"""VFS-domain compiler boundary."""

from __future__ import annotations

from typing import Any

from pyparsing import ParseBaseException

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.variables_config import VariableDeclaration, VariablesConfig
from townlet.items.manager import SpawnPredicateReads
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.source_map import SourceMap, locate
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

    def build_expression_schema(self, bars: BarsV2Config, compiled_vfs_profiles: CompiledVFSProfiles | None) -> dict[str, str]:
        """Build type schema for VFS expression runtime validation."""
        schema = {}

        for meter in bars.meters:
            schema[f"bar.{meter.name}"] = "float"

        if compiled_vfs_profiles and compiled_vfs_profiles.global_profile:
            for var in compiled_vfs_profiles.global_profile.variables:
                schema[f"vfs.{var.name}"] = var.type

        if compiled_vfs_profiles and compiled_vfs_profiles.item_profiles:
            for profile in compiled_vfs_profiles.item_profiles.values():
                for var in profile.variables:
                    schema[f"self.vfs.{var.name}"] = var.type
                    schema[f"target.vfs.{var.name}"] = var.type

        return schema

    def derive_evaluation_marks(self, config: VariablesConfig) -> dict[str, set[str]]:
        """Expressions are state; evaluate them irrespective of observation exposure."""
        return {
            scope.value: {variable.id for variable in config.for_scope(scope) if variable.expression is not None}
            for scope in (VariableScope.GLOBAL, VariableScope.AGENT)
            if any(variable.expression is not None for variable in config.for_scope(scope))
        }

    def validate_item_profile_bindings(
        self,
        items: ItemsCatalogConfig | None,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> None:
        """Validate item profile references from items.yaml against compiled VFS profiles."""
        if items is None:
            return
        item_profiles = compiled_vfs_profiles.item_profiles if compiled_vfs_profiles is not None else None
        available_profiles = set(item_profiles.keys()) if item_profiles is not None else set()
        for item in items.item_types:
            profile_name = item.vfs_profile
            if profile_name is None:
                continue
            if profile_name not in available_profiles:
                raise ValueError(
                    "Invalid item VFS profile binding.\n"
                    f"  Item: {item.id}\n"
                    f"  vfs_profile: {profile_name!r}\n"
                    f"  Available item profiles: {sorted(available_profiles)}\n"
                    "Define the profile in the pack-scope item_profiles declaration or update the item catalog binding."
                )

    def compile_item_spawn_conditions(
        self,
        appearance: ItemsAppearanceConfig | None,
        *,
        bar_schema: dict[str, str],
        variables: VariablesConfig,
        source_map: SourceMap | None,
        level_name: str,
    ) -> None:
        """Type-check each spawn predicate against what the runtime serves; store its AST.

        The readable names come from `SpawnPredicateReads.schema`, fed the same registry
        roster the runtime registry is built from, so a predicate that compiles is one the
        spawn context can evaluate. A read outside that schema, or a non-bool result, is
        refused here with the rule's `file:line`.
        """
        if appearance is None:
            return
        schema = SpawnPredicateReads.schema(meter_names=bar_schema, variables=self.build_runtime_variables(variables))
        parser = ExpressionParser()
        type_checker = TypeChecker(schema)
        declaration = f"levels/{level_name}/items_appearance"
        issues: list[CompilationMessage] = []
        for index, rule in enumerate(appearance.items):
            rule.when_ast = None
            if rule.when is None:
                continue
            try:
                rule.when_ast = self._check_spawn_predicate(rule.when, schema, parser, type_checker)
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
    def _check_spawn_predicate(when: str, schema: dict[str, str], parser: ExpressionParser, type_checker: TypeChecker) -> Any:
        """Return the parsed predicate, or raise `_SpawnPredicateRefusedError` saying why not."""
        try:
            ast = parser.parse(when)
        except (ParseBaseException, ValueError) as exc:
            raise _SpawnPredicateRefusedError(f"does not parse: {exc}") from exc
        unserved = [name for name in dict.fromkeys(SpawnPredicateReads.reads(ast)) if name not in schema]
        if unserved:
            raise _SpawnPredicateRefusedError(
                f"reads {unserved}, which the spawn context does not serve. A spawn predicate reads "
                f"'{SpawnPredicateReads.VARIABLE_ROOT}.<id>' for a global- or agent-scope variable (the engine clock "
                f"is '{SpawnPredicateReads.variable_path(_ENGINE_TICK_ID)}') and '{SpawnPredicateReads.BAR_ROOT}.<meter>' "
                "for a meter; derive anything else (an hour, a season) as a declared global expression variable."
            )
        try:
            result_type = type_checker.check(ast)
        except TypeCheckError as exc:
            raise _SpawnPredicateRefusedError(f"does not type-check: {exc}") from exc
        if result_type != "bool":
            raise _SpawnPredicateRefusedError(f"must return bool, got {result_type}")
        return ast
