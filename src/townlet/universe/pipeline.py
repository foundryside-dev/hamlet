"""Typed stage boundaries for universe compiler orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from townlet.effects.catalog import EffectCatalog
from townlet.universe.compiled import CompiledUniverse, CompiledVFSProfiles
from townlet.universe.dto import UniverseMetadata
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.vfs.observation_builder import VFSObservationSpec


@dataclass(frozen=True)
class LoadedConfigBundle:
    """Configs loaded from a v2.1 experiment pack."""

    raw: RawConfigsV21


@dataclass(frozen=True)
class ResolvedConfigBundle:
    """Loaded configs after symbol registration and reference validation."""

    raw: RawConfigsV21
    symbol_table: UniverseSymbolTable


@dataclass(frozen=True)
class SharedCompilerArtifacts:
    """Shared artifacts reused while compiling every curriculum level."""

    bar_schema: dict[str, str]
    compiled_vfs_profiles: CompiledVFSProfiles | None
    effects_schema: dict[str, str]
    compiled_effect_catalog: EffectCatalog | None
    vfs_history_spec: dict[str, int]
    vfs_observation_spec: VFSObservationSpec | None


@dataclass(frozen=True)
class CompiledLevelBundle:
    """Per-level compiled metadata plus primary-level derived schemas."""

    all_levels: dict[str, CompiledUniverse.LevelMetadata]
    primary_meta: CompiledUniverse.LevelMetadata
    universe_metadata: UniverseMetadata
    vfs_expression_schema: dict[str, str]
    vfs_observation_marks: dict[str, set[str]] | None


@dataclass(frozen=True)
class CompiledArtifactBundle:
    """Final compiled artifact and its cache target."""

    compiled: CompiledUniverse
    cache_path: Path
