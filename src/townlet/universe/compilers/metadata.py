"""Metadata-domain compiler boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.environment_config import EnvironmentConfig as EnvConfigV21
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.dto import AffordanceMetadata, MeterMetadata, UniverseMetadata
from townlet.universe.raw_configs_v21 import RawConfigsV21


class _MetadataDelegate(Protocol):
    def _build_meter_metadata(self, environment: EnvConfigV21, bars: BarsV2Config) -> MeterMetadata: ...

    def _build_affordance_metadata(self, affordances: AffordancesV2Config) -> AffordanceMetadata: ...

    def _build_universe_metadata(
        self,
        raw: RawConfigsV21,
        primary_meta: CompiledUniverse.LevelMetadata,
        *,
        experiment_dir: Path,
        config_hash: str | None,
        config_mtime: float | None,
    ) -> UniverseMetadata: ...


class MetadataCompiler:
    """Compile public metadata DTOs for the compiled universe."""

    def __init__(self, delegate: _MetadataDelegate) -> None:
        self._delegate = delegate

    def build_meter_metadata(self, environment: EnvConfigV21, bars: BarsV2Config) -> MeterMetadata:
        return self._delegate._build_meter_metadata(environment, bars)

    def build_affordance_metadata(self, affordances: AffordancesV2Config) -> AffordanceMetadata:
        return self._delegate._build_affordance_metadata(affordances)

    def build_universe_metadata(
        self,
        raw: RawConfigsV21,
        primary_meta: CompiledUniverse.LevelMetadata,
        *,
        experiment_dir: Path,
        config_hash: str | None,
        config_mtime: float | None,
    ) -> UniverseMetadata:
        return self._delegate._build_universe_metadata(
            raw,
            primary_meta,
            experiment_dir=experiment_dir,
            config_hash=config_hash,
            config_mtime=config_mtime,
        )
