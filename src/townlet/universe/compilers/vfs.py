"""VFS-domain compiler boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pyparsing import ParseBaseException

from townlet.config.items_config import ItemsAppearanceConfig
from townlet.config.variables_config import VariableDeclaration, VariablesConfig
from townlet.items.manager import SpawnPredicateReads
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.source_map import SourceMap, locate
from townlet.vfs.namespace import ExpressionSource, Namespace, SpellingError, inline_expression_reads
from townlet.vfs.profiles import VFSProfileCompiler
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

_ENGINE_TICK_ID = "tick"


class _SpawnPredicateRefusedError(Exception):
    """One spawn predicate the runtime could not evaluate; the message says why."""


_DETERMINISTIC_TENSOR_INITIALIZERS = frozenset({"zeros", "ones", "eye"})


def _literal_tensor_default(mode: str, shape: list[int], *, var_id: str) -> list[Any]:
    """Lower one deterministic tensor initializer to its exact row-major literal."""
    if mode == "eye":
        if len(shape) != 2 or shape[0] != shape[1]:
            raise ValueError(f"Exposed VFS variable '{var_id}' initial_value_mode 'eye' requires a square 2D shape; got {shape}")
        return [[1.0 if row == column else 0.0 for column in range(shape[1])] for row in range(shape[0])]

    fill = 0.0 if mode == "zeros" else 1.0

    def filled(axis: int) -> list[Any]:
        if axis == len(shape) - 1:
            return [fill for _ in range(shape[axis])]
        return [filled(axis + 1) for _ in range(shape[axis])]

    return filled(0)


def _engine_tick_variable_def() -> VariableDef:
    return VariableDef(
        id=_ENGINE_TICK_ID,
        scope=VariableScope.GLOBAL,
        type="scalar",
        default=0.0,
        lifetime="episode",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        # float32 storage is integer-exact to 2^24; persistent-lifetime counters are
        # hamlet-0268336cd1's question, not this variable's contract.
        description="Engine-written step counter — the one temporal primitive (token-obs design ruling 6).",
    )


class VFSCompiler:
    """Compile VFS profiles, schemas, and spawn predicates."""

    def compile_profiles(
        self,
        config: VariablesConfig,
        bar_schema: dict[str, str],
    ) -> CompiledVFSProfiles:
        """Lower one canonical roster into internal expression and item products."""
        compiler = VFSProfileCompiler()
        globals_ = config.for_scope(VariableScope.GLOBAL)
        agents = config.for_scope(VariableScope.AGENT)
        # Each scope compiles against the other's roster: agent expressions read globals
        # by bare name (the runtime evaluates the global profile first); global
        # expressions refuse agent ids as scope widening.
        return CompiledVFSProfiles(
            global_profile=(compiler.compile_profile(globals_, bar_schema, cross_scope=agents) if globals_ else None),
            agent_profile=(compiler.compile_profile(agents, bar_schema, cross_scope=globals_) if agents else None),
            item_profiles={
                name: compiler.compile_item_profile(name, config.for_item_profile(name), bar_schema) for name in config.item_profiles
            },
        )

    def build_runtime_variables(self, config: VariablesConfig) -> tuple[VariableDef, ...]:
        """Lower each authored registry variable exactly once, with its declared static access policy."""
        return (
            _engine_tick_variable_def(),
            *(self._variable_to_definition(variable) for variable in config.declarations if variable.scope != VariableScope.ITEM),
        )

    def _variable_to_definition(self, variable: VariableDeclaration) -> VariableDef:
        mode = variable.initial_value_mode
        params = variable.initial_value_params
        default = variable.initial_value
        if variable.exposed_to and mode in _DETERMINISTIC_TENSOR_INITIALIZERS:
            assert variable.shape is not None
            default = _literal_tensor_default(mode, variable.shape, var_id=variable.id)
            mode, params = None, None
        return VariableDef(
            id=variable.id,
            scope=variable.scope,
            type=variable.type,
            lifetime=variable.lifetime,
            readable_by=list(variable.readable_by),
            writable_by=list(variable.writable_by),
            default=default,
            shape=variable.shape,
            dims=variable.dims,
            initial_value_mode=mode,
            initial_value_params=params,
            normalization=variable.normalization,
            exposed_to=list(variable.exposed_to),
            semantic_type=variable.semantic_type,
            description=variable.description,
        )

    def derive_evaluation_marks(self, config: VariablesConfig) -> dict[str, set[str]]:
        """Expressions are state; evaluate them irrespective of observation exposure."""
        return {
            scope.value: {variable.id for variable in config.for_scope(scope) if variable.expression is not None}
            for scope in (VariableScope.GLOBAL, VariableScope.AGENT)
            if any(variable.expression is not None for variable in config.for_scope(scope))
        }

    def compile_item_spawn_conditions(
        self,
        appearance: ItemsAppearanceConfig | None,
        *,
        bar_schema: dict[str, str],
        variables: VariablesConfig,
        expressions: Mapping[str, ExpressionSource],
        source_map: SourceMap | None,
        level_name: str,
    ) -> None:
        """Resolve, type-check and inline each spawn predicate; store its AST.

        The readable names come from `SpawnPredicateReads.namespace`, fed the same
        registry roster the runtime registry is built from, so a predicate that compiles
        is one the spawn context can evaluate. A spelling the resolver refuses, a call to
        a function whose context a spawn does not carry (temporal history, the step,
        positions), a non-bool result, or a read of a context-bound tick-lifetime
        expression variable is refused here with the rule's `file:line`. Every pure
        expression variable a predicate reads is inlined (S4 follow-up): spawns run after
        tick state resets, so a stored value would be stale or a literal.
        """
        if appearance is None:
            return
        namespace = SpawnPredicateReads.namespace(meter_names=bar_schema, variables=self.build_runtime_variables(variables))
        parser = ExpressionParser()
        type_checker = TypeChecker(namespace.schema(SpawnPredicateReads.CONTEXT))
        declaration = f"levels/{level_name}/items_appearance"
        issues: list[CompilationMessage] = []
        for index, rule in enumerate(appearance.items):
            rule.when_ast = None
            if rule.when is None:
                continue
            try:
                rule.when_ast = self._check_spawn_predicate(rule.when, namespace, expressions, parser, type_checker)
            except _SpawnPredicateRefusedError as refusal:
                issues.append(
                    CompilationMessage(
                        code=ErrorCode.ITEM_SPAWN_CONDITION,
                        message=f"Spawn condition for item '{rule.item_type}': {rule.when!r} {refusal}",
                        location=locate(source_map, f"{declaration}:items[{index}].when", declaration),
                    )
                )
        if issues:
            raise CompilationError("Item spawn conditions", issues)

    @staticmethod
    def _check_spawn_predicate(
        when: str,
        namespace: Namespace,
        expressions: Mapping[str, ExpressionSource],
        parser: ExpressionParser,
        type_checker: TypeChecker,
    ) -> Any:
        """Return the parsed, inlined predicate, or raise `_SpawnPredicateRefusedError` saying why not."""
        try:
            ast = parser.parse(when)
        except (ParseBaseException, ValueError) as exc:
            raise _SpawnPredicateRefusedError(f"does not parse: {exc}") from exc
        refusals = namespace.refusals(ast, SpawnPredicateReads.CONTEXT)
        if refusals:
            raise _SpawnPredicateRefusedError(f"is refused: {' '.join(refusals)}")
        try:
            result_type = type_checker.check(ast)
        except TypeCheckError as exc:
            raise _SpawnPredicateRefusedError(f"does not type-check: {exc}") from exc
        if result_type != "bool":
            raise _SpawnPredicateRefusedError(f"must return bool, got {result_type}")
        try:
            return inline_expression_reads(ast, expressions, consumer="an item spawn")
        except SpellingError as exc:
            raise _SpawnPredicateRefusedError(f"is refused: {exc}") from exc
