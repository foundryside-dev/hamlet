"""VFS-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.environment_config import VariableConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.vfs_profiles_config import GlobalVFSProfileConfig, VFSProfilesConfig
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.validation.limits import MAX_VFS_PROFILES
from townlet.vfs.profiles import CompiledItemProfile, VFSProfileCompiler
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class VFSCompiler:
    """Compile VFS profiles, schemas, and spawn predicates."""

    def compile_profiles(self, experiment_dir: Path, bar_schema: dict[str, str]) -> CompiledVFSProfiles | None:
        """Load and compile VFS profiles from experiment directory."""
        profiles_path = experiment_dir / "vfs_profiles.yaml"

        if not profiles_path.exists():
            return None

        profiles_data = yaml.safe_load(profiles_path.read_text())
        profiles_config = VFSProfilesConfig(**profiles_data)

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
            global_profile=compiled_global,
            agent_profile=compiled_agent,
            item_profiles=compiled_item_profiles,
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

    def extract_observation_marks(self, variables: tuple[VariableDef, ...]) -> dict[str, set[str]]:
        """Extract which VFS variables are marked for observation."""
        marks: dict[str, set[str]] = {
            "global": set(),
            "agent": set(),
            "item": set(),
        }

        for var in variables:
            if var.observable:
                if isinstance(var.scope, VariableScope):
                    scope_key = var.scope.value
                else:
                    scope_key = str(var.scope)

                if scope_key == "global":
                    marks["global"].add(var.id)
                elif scope_key in ("agent", "agent_private"):
                    marks["agent"].add(var.id)

        return {k: v for k, v in marks.items() if v}

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
