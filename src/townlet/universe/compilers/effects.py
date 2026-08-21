"""Effects-domain compiler boundary."""

from __future__ import annotations

from typing import Any

from townlet.config.effects_config import EffectsConfig
from townlet.effects.catalog import EffectCatalog
from townlet.universe.compiled import CompiledVFSProfiles

_EFFECT_SCHEMA_REFERENCE_TYPES = frozenset({"agent_ref", "item_ref", "affordance_ref", "effect_ref"})


class EffectsCompiler:
    """Compile effects catalogs against the active schema."""

    def build_schema(
        self,
        *,
        bar_names: tuple[str, ...],
        environment_variables: tuple[Any, ...],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> dict[str, str]:
        """Build the runtime effect expression schema from compiler-owned artifacts."""
        schema: dict[str, str] = {
            "intensity": "float",
            "elapsed_ticks": "float",
            "duration_remaining": "float",
        }

        for bar_name in bar_names:
            schema[f"bar.{bar_name}"] = "float"
            schema[f"target.bar.{bar_name}"] = "float"

        for var in environment_variables:
            if str(getattr(var, "scope", "")) == "global":
                self._add_global_vfs_paths(schema, str(var.name), getattr(var, "type", None))
            else:
                self._add_target_vfs_paths(schema, str(var.name), getattr(var, "type", None))

        if compiled_vfs_profiles is not None:
            if compiled_vfs_profiles.global_profile is not None:
                # Global-profile variables are global by construction: no per-agent
                # axis exists, so no target.vfs path is registered (hamlet-cf16cdb6c4).
                for var in compiled_vfs_profiles.global_profile.variables:
                    self._add_global_vfs_paths(schema, str(var.name), getattr(var, "type", None))
            if compiled_vfs_profiles.agent_profile is not None:
                for var in compiled_vfs_profiles.agent_profile.variables:
                    self._add_target_vfs_paths(schema, str(var.name), getattr(var, "type", None))
            if compiled_vfs_profiles.item_profiles:
                for profile in compiled_vfs_profiles.item_profiles.values():
                    for var in profile.variables:
                        schema[f"self.vfs.{var.name}"] = self._normalize_effect_schema_type(getattr(var, "type", None))

        return schema

    def compile_catalog(
        self,
        effects_config: EffectsConfig | None,
        schema: dict[str, str],
        *,
        time_enabled: bool,
    ) -> EffectCatalog | None:
        """Compile Stage 1 effects DTOs."""
        if effects_config is None:
            return None

        return EffectCatalog.from_config(effects_config, schema=schema, time_enabled=time_enabled)

    @staticmethod
    def _add_target_vfs_paths(schema: dict[str, str], name: str, raw_type: Any) -> None:
        schema_type = EffectsCompiler._normalize_effect_schema_type(raw_type)
        schema[f"vfs.{name}"] = schema_type
        schema[f"target.vfs.{name}"] = schema_type

    @staticmethod
    def _add_global_vfs_paths(schema: dict[str, str], name: str, raw_type: Any) -> None:
        """Register a global-scoped variable: plain and explicit-global roots, no target path."""
        schema_type = EffectsCompiler._normalize_effect_schema_type(raw_type)
        schema[f"vfs.{name}"] = schema_type
        schema[f"global.vfs.{name}"] = schema_type

    @staticmethod
    def _normalize_effect_schema_type(raw_type: Any) -> str:
        if raw_type in _EFFECT_SCHEMA_REFERENCE_TYPES:
            return str(raw_type)
        if raw_type == "bool":
            return "bool"
        return "float"
