"""VFS-domain compiler boundary."""

from __future__ import annotations

from typing import Any

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.variables_config import VariableDeclaration, VariablesConfig
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.vfs.profiles import VFSProfileCompiler
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

_ENGINE_TICK_ID = "tick"

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
        scope="global",
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
        return CompiledVFSProfiles(
            evaluation_mode=config.evaluation_mode,
            debug_logging=config.debug_logging,
            global_profile=compiler.compile_profile(globals_, bar_schema, evaluation_mode=config.evaluation_mode) if globals_ else None,
            agent_profile=compiler.compile_profile(agents, bar_schema, evaluation_mode=config.evaluation_mode) if agents else None,
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
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> None:
        """Compile item spawn predicates into parsed ASTs for runtime reuse."""
        if appearance is None:
            return
        schema = self._build_spawn_condition_schema(
            bar_schema=bar_schema,
            variables=variables,
            compiled_vfs_profiles=compiled_vfs_profiles,
            temporal_supported=temporal_supported,
        )
        parser = ExpressionParser()
        type_checker = TypeChecker(schema)
        for rule in appearance.items:
            rule.when_ast = None
            if rule.when is None:
                continue

            ast = parser.parse(rule.when)

            if not temporal_supported and self._ast_uses_temporal(ast):
                raise TypeCheckError("Spawn condition references temporal.* but temporal mechanics are disabled for this level")

            result_type = type_checker.check(ast)
            if result_type != "bool":
                raise TypeCheckError(f"Spawn condition must return bool, got {result_type}")

            rule.when_ast = ast

    def _build_spawn_condition_schema(
        self,
        *,
        bar_schema: dict[str, str],
        variables: VariablesConfig,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> dict[str, str]:
        """Build expression schema for item spawn conditions."""
        schema: dict[str, str] = {**bar_schema}
        for var in variables.declarations:
            if var.scope in {VariableScope.GLOBAL, VariableScope.AGENT}:
                schema[f"env.{var.id}"] = "float" if var.type == "scalar" else var.type
        if temporal_supported:
            schema["temporal.time_of_day"] = "float"
            schema["temporal.day_progress"] = "float"
            schema["temporal.is_night"] = "bool"

        if compiled_vfs_profiles is not None:
            if compiled_vfs_profiles.global_profile is not None:
                for compiled_var in compiled_vfs_profiles.global_profile.variables:
                    schema[f"vfs.{compiled_var.name}"] = compiled_var.type
            if compiled_vfs_profiles.agent_profile is not None:
                for compiled_var in compiled_vfs_profiles.agent_profile.variables:
                    schema[f"agent.vfs.{compiled_var.name}"] = compiled_var.type

        return schema

    def _ast_uses_temporal(self, ast: Any) -> bool:
        """Return True if parsed expression AST references temporal.* paths."""
        if isinstance(ast, dict):
            if ast.get("type") == "path":
                path = ast.get("path")
                if isinstance(path, str) and path.startswith("temporal."):
                    return True
            return any(self._ast_uses_temporal(value) for value in ast.values())
        if isinstance(ast, list):
            return any(self._ast_uses_temporal(item) for item in ast)
        if hasattr(ast, "__dict__"):
            return self._ast_uses_temporal(vars(ast))
        return False
