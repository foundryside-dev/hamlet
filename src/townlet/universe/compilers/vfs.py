"""VFS-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.environment_config import VariableConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.universe.compiled import CompiledVFSProfiles


class _VFSDelegate(Protocol):
    def _compile_vfs_profiles(self, experiment_dir: Path, bar_schema: dict[str, str]) -> CompiledVFSProfiles | None: ...

    def _build_vfs_expression_schema(
        self,
        bars: BarsV2Config,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> dict[str, str]: ...

    def _extract_vfs_observation_marks(self, variables) -> dict[str, set[str]]: ...

    def _validate_item_profile_bindings(
        self,
        items: ItemsCatalogConfig | None,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> None: ...

    def _compile_item_spawn_conditions(
        self,
        appearance: ItemsAppearanceConfig | None,
        *,
        bar_schema: dict[str, str],
        env_vars: list[VariableConfig],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> None: ...


class VFSCompiler:
    """Compile VFS profiles, schemas, and spawn predicates."""

    def __init__(self, delegate: _VFSDelegate) -> None:
        self._delegate = delegate

    def compile_profiles(self, experiment_dir: Path, bar_schema: dict[str, str]) -> CompiledVFSProfiles | None:
        return self._delegate._compile_vfs_profiles(experiment_dir, bar_schema)

    def build_expression_schema(self, bars: BarsV2Config, compiled_vfs_profiles: CompiledVFSProfiles | None) -> dict[str, str]:
        return self._delegate._build_vfs_expression_schema(bars, compiled_vfs_profiles)

    def extract_observation_marks(self, variables) -> dict[str, set[str]]:
        return self._delegate._extract_vfs_observation_marks(variables)

    def validate_item_profile_bindings(
        self,
        items: ItemsCatalogConfig | None,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> None:
        self._delegate._validate_item_profile_bindings(items, compiled_vfs_profiles)

    def compile_item_spawn_conditions(
        self,
        appearance: ItemsAppearanceConfig | None,
        *,
        bar_schema: dict[str, str],
        env_vars: list[VariableConfig],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> None:
        self._delegate._compile_item_spawn_conditions(
            appearance,
            bar_schema=bar_schema,
            env_vars=env_vars,
            compiled_vfs_profiles=compiled_vfs_profiles,
            temporal_supported=temporal_supported,
        )
