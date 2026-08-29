"""Typed stage boundaries for universe compiler orchestration."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.effects.catalog import EffectCatalog
from townlet.universe.compiled import CompiledUniverse, CompiledVFSProfiles
from townlet.universe.dto import UniverseMetadata


@dataclass(frozen=True)
class SharedCompilerArtifacts:
    """Shared artifacts reused while compiling every curriculum level."""

    bar_schema: dict[str, str]
    compiled_vfs_profiles: CompiledVFSProfiles | None
    effects_schema: dict[str, str]
    compiled_effect_catalog: EffectCatalog | None
    vfs_history_spec: dict[str, int]


@dataclass(frozen=True)
class CompiledLevelBundle:
    """Per-level compiled metadata plus primary-level derived schemas."""

    all_levels: dict[str, CompiledUniverse.LevelMetadata]
    primary_meta: CompiledUniverse.LevelMetadata
    universe_metadata: UniverseMetadata
    vfs_expression_schema: dict[str, str]
    vfs_evaluation_marks: dict[str, set[str]] | None
