"""Observation-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig as EnvConfigV21
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.effects.catalog import EffectCatalog
from townlet.universe.compiled import CompiledVFSProfiles
from townlet.universe.dto import ObservationActivity, ObservationSpec
from townlet.vfs.schema import ObservationField as VFSObservationField
from townlet.vfs.schema import VariableDef


class _ObservationDelegate(Protocol):
    config_pack_path: Path

    def _build_observation_spec(
        self,
        stratum: StratumConfig,
        environment: EnvConfigV21,
        curriculum: CurriculumConfig,
        compiled_vfs_profiles: CompiledVFSProfiles | None = None,
        items_catalog: ItemsCatalogConfig | None = None,
        compiled_effect_catalog: EffectCatalog | None = None,
    ) -> ObservationSpec: ...

    def _build_observation_activity(self, obs_spec: ObservationSpec) -> ObservationActivity: ...

    def _build_vfs_observation_fields(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VFSObservationField, ...]: ...

    def _build_vfs_variables(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VariableDef, ...]: ...


class ObservationCompiler:
    """Compile observation specs and their VFS-facing artifacts."""

    def __init__(self, delegate: _ObservationDelegate) -> None:
        self._delegate = delegate

    def build_spec(
        self,
        stratum: StratumConfig,
        environment: EnvConfigV21,
        curriculum: CurriculumConfig,
        compiled_vfs_profiles: CompiledVFSProfiles | None = None,
        items_catalog: ItemsCatalogConfig | None = None,
        compiled_effect_catalog: EffectCatalog | None = None,
    ) -> ObservationSpec:
        return self._delegate._build_observation_spec(
            stratum,
            environment,
            curriculum,
            compiled_vfs_profiles,
            items_catalog,
            compiled_effect_catalog,
        )

    def build_activity(self, obs_spec: ObservationSpec) -> ObservationActivity:
        return self._delegate._build_observation_activity(obs_spec)

    def build_vfs_observation_fields(
        self,
        obs_spec: ObservationSpec,
        environment: EnvConfigV21,
    ) -> tuple[VFSObservationField, ...]:
        return self._delegate._build_vfs_observation_fields(obs_spec, environment)

    def build_vfs_variables(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VariableDef, ...]:
        return self._delegate._build_vfs_variables(obs_spec, environment)
