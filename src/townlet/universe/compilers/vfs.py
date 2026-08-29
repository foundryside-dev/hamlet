"""VFS-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.environment_config import VariableConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.vfs_profiles_config import GlobalVFSProfileConfig, VFSProfilesConfig
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.validation.limits import MAX_VFS_PROFILES
from townlet.vfs.profiles import CompiledItemProfile, VFSProfileCompiler
from townlet.vfs.schema import VariableDef
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

_RUNTIME_VFS_TYPES = frozenset(
    {"scalar", "bool", "tensor1d", "tensor2d", "tensor3d", "tensorNd", "agent_ref", "item_ref", "affordance_ref", "effect_ref"}
)

_ENGINE_TICK_ID = "tick"


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
        profiles_config: VFSProfilesConfig | None,
        experiment_dir: Path,
        bar_schema: dict[str, str],
    ) -> CompiledVFSProfiles | None:
        """Compile Stage 1 VFS profile DTOs."""
        if profiles_config is None:
            return None

        profile_count = (
            int(profiles_config.global_profile is not None)
            + int(profiles_config.agent_profile is not None)
            + len(profiles_config.item_profiles or [])
        )
        if profile_count > MAX_VFS_PROFILES:
            raise ValueError(
                "vfs_profiles.yaml exceeds safety limit for profile count.\n"
                f"  Experiment: {experiment_dir}\n"
                f"  Profiles: {profile_count} (max {MAX_VFS_PROFILES})\n"
                "Reduce VFS profile count to keep config size within guardrails."
            )

        compiler = VFSProfileCompiler()
        compiler.validate_version(profiles_config.version)

        compiled_global = None
        if profiles_config.global_profile is not None:
            compiled_global = compiler.compile_global_profile(profiles_config.global_profile, bar_schema=bar_schema)

        compiled_agent = None
        if profiles_config.agent_profile is not None:
            agent_profile = cast(GlobalVFSProfileConfig, profiles_config.agent_profile)
            compiled_agent = compiler.compile_global_profile(agent_profile, bar_schema=bar_schema)

        compiled_item_profiles: dict[str, CompiledItemProfile] = {}
        if profiles_config.item_profiles:
            for item_profile_config in profiles_config.item_profiles:
                compiled_profile = compiler.compile_item_profile(item_profile_config, bar_schema=bar_schema)
                compiled_item_profiles[compiled_profile.profile_name] = compiled_profile

        return CompiledVFSProfiles(
            evaluation_mode=profiles_config.evaluation_mode,
            debug_logging=profiles_config.debug_logging,
            global_profile=compiled_global,
            agent_profile=compiled_agent,
            item_profiles=compiled_item_profiles,
        )

    def build_runtime_variables(
        self,
        base_variables: tuple[VariableDef, ...],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        static_variables: tuple[VariableDef, ...] | None = None,
    ) -> tuple[VariableDef, ...]:
        """Emit registry-ready VFS variables from observation/environment variables and profiles."""
        variables: list[VariableDef] = [_engine_tick_variable_def(), *base_variables]

        if compiled_vfs_profiles is not None:
            if compiled_vfs_profiles.global_profile is not None:
                for compiled_var in compiled_vfs_profiles.global_profile.variables:
                    variables.append(self._compiled_profile_var_to_variable_def(compiled_var, scope="global", lifetime="persistent"))

            if compiled_vfs_profiles.agent_profile is not None:
                for compiled_var in compiled_vfs_profiles.agent_profile.variables:
                    variables.append(self._compiled_profile_var_to_variable_def(compiled_var, scope="agent", lifetime="episode"))

            existing_ids = {variable.id for variable in variables}
            for variable in static_variables or ():
                # Refuse explicitly BEFORE the dedup skip below: existing_ids already
                # contains the engine's own prepended 'tick' (index 0), so an authored
                # static variable (variables_reference.yaml) named 'tick' would otherwise
                # match that dedup check and be silently dropped instead of refused.
                if variable.id == _ENGINE_TICK_ID:
                    raise ValueError(
                        "Variable id 'tick' is reserved for the engine-written step counter "
                        "(token-obs design ruling 6). Rename the authored variable."
                    )
                if variable.id in existing_ids:
                    continue
                variables.append(variable)
                existing_ids.add(variable.id)

        clashes = [v.id for v in variables[1:] if v.id == _ENGINE_TICK_ID]
        if clashes:
            raise ValueError(
                "Variable id 'tick' is reserved for the engine-written step counter "
                "(token-obs design ruling 6). Rename the authored variable."
            )

        return tuple(variables)

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

    def derive_evaluation_marks(
        self,
        profiles_config: VFSProfilesConfig | None,
        overlay_variables: tuple[VariableDef, ...] | None,
    ) -> dict[str, set[str]] | None:
        """Marks = every profile EXPRESSION variable. Statics are never marked.

        An expression variable's value is WORLD STATE: a VTC rule, a DAC reward
        component, another expression or a terminal condition may read it, and none of
        those care whether anyone observes it. So evaluation is marked by declaration —
        having an expression — never by exposure.

        It used to be marked by exposure ("only evaluate observed variables"), which
        looked harmless only because `exposed_to` failed open to `["agent"]`: every
        profile expression variable was exposed, so every one was evaluated. Deleting
        that fail-open at the unit-3 cut (hamlet-d97b4d6b4a) turned an OBSERVATION
        decision into a STATE decision — unexposed expression variables silently stopped
        being computed and sat at their defaults, which is a world-evolution change, not
        an observation change, and would have broken the cut's own adjudication criterion
        (spec §5: only `obs` may diverge). Marking every expression reproduces the
        pre-cut evaluation set exactly on every pack.

        Statics stay unmarked: they are storage, and re-emitting their initial value
        would clobber runtime writes (hamlet-df3a96bbac). They still reach the evaluator
        by its other two doors — the dependency chase and the compiled `history_spec` —
        and are REPORTED at their current value there, never re-initialized
        (vfs/evaluator.py's static branch, comment-242 item 4).
        """
        if profiles_config is None:
            return None
        marks: dict[str, set[str]] = {}
        for scope_key, profile in (("global", profiles_config.global_profile), ("agent", profiles_config.agent_profile)):
            if profile is None:
                continue
            expression_vars = {v.name for v in profile.variables if v.expression is not None}
            if expression_vars:
                marks[scope_key] = expression_vars
        return marks or {}

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
                    "Define the profile in vfs_profiles.yaml:item_profiles or update items.yaml."
                )

    def compile_item_spawn_conditions(
        self,
        appearance: ItemsAppearanceConfig | None,
        *,
        bar_schema: dict[str, str],
        env_vars: list[VariableConfig],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> None:
        """Compile item spawn predicates into parsed ASTs for runtime reuse."""
        if appearance is None:
            return
        schema = self._build_spawn_condition_schema(
            bar_schema=bar_schema,
            env_vars=env_vars,
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
        env_vars: list[VariableConfig],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> dict[str, str]:
        """Build expression schema for item spawn conditions."""
        schema: dict[str, str] = {**bar_schema}
        for var in env_vars:
            schema[f"env.{var.name}"] = getattr(var, "type", "float")
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

    def _compiled_profile_var_to_variable_def(
        self,
        compiled_var: Any,
        *,
        scope: Literal["global", "agent", "agent_private", "item", "pair", "group", "affordance", "zone", "message"],
        lifetime: Literal["persistent", "episode"],
    ) -> VariableDef:
        raw_type = str(compiled_var.type)
        if raw_type in ("agent_ref", "item_ref", "affordance_ref", "effect_ref"):
            default_value = compiled_var.initial_value
        else:
            default_value = (
                compiled_var.initial_value if compiled_var.initial_value is not None else (0.0 if raw_type in ("int", "float") else False)
            )

        normalized_type = self._normalize_runtime_vfs_type(raw_type, str(compiled_var.name))
        variable_type = cast(
            Literal[
                "scalar",
                "bool",
                "tensor1d",
                "tensor2d",
                "tensor3d",
                "tensorNd",
                "agent_ref",
                "item_ref",
                "affordance_ref",
                "effect_ref",
            ],
            normalized_type,
        )
        return VariableDef(
            id=str(compiled_var.name),
            scope=scope,
            type=variable_type,
            default=default_value,
            lifetime=lifetime,
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            description=f"{scope.title()} VFS variable from vfs_profiles.yaml",
            shape=getattr(compiled_var, "shape", None),
            dims=getattr(compiled_var, "dims", None),
            initial_value_mode=getattr(compiled_var, "initial_value_mode", None),
            initial_value_params=getattr(compiled_var, "initial_value_params", None),
            # The declared normalization rides onto the runtime declaration so the token
            # publishers read exactly what the author declared (spec §2).
            normalization=getattr(compiled_var, "normalization", None),
        )

    @staticmethod
    def _normalize_runtime_vfs_type(raw_type: str, var_id: str) -> str:
        if raw_type in ("int", "float"):
            return "scalar"
        if raw_type in _RUNTIME_VFS_TYPES:
            return raw_type
        raise ValueError(f"Unsupported VFS variable type '{raw_type}' for variable '{var_id}'. Valid types: {sorted(_RUNTIME_VFS_TYPES)}")
