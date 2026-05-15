"""UniverseCompiler implementation (Stage 1 scaffolding)."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from numbers import Number
from pathlib import Path
from typing import Any

import torch
import yaml

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordanceParamConfig
from townlet.config.bars_v2_config import MeterConfig
from townlet.config.brain_config import load_brain_config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig, load_drive_as_code_config
from townlet.config.environment_config import CascadeConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig, SubstrateConfig
from townlet.effects.catalog import EffectCatalog
from townlet.environment.action_config import ActionConfig, ActionSpaceConfig
from townlet.environment.affordance_config import AffordanceConfig  # Runtime representation
from townlet.environment.substrate_action_validator import SubstrateActionValidator
from townlet.environment.temporal_utils import is_affordance_open
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.dto import (
    ActionSpaceMetadata,
    AffordanceMetadata,
    MeterMetadata,
    ObservationSpec,
    UniverseMetadata,
)
from townlet.universe.optimization import OptimizationData
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.vfs.observation_builder import VFSObservationSpec

from .compiled import CompiledVFSProfiles
from .compilers.actions import ActionCompiler
from .compilers.effects import EffectsCompiler
from .compilers.metadata import MetadataCompiler
from .compilers.observation import ObservationCompiler
from .compilers.optimization import OptimizationCompiler
from .compilers.vfs import VFSCompiler
from .cues_compiler import CuesCompiler
from .errors import CompilationError, CompilationErrorCollector, CompilationMessage
from .loaders.preflight import validate_config_dir, validate_scoping, validate_yaml_syntax
from .loaders.v21 import load_v21_configs
from .pipeline import CompiledLevelBundle, SharedCompilerArtifacts
from .validation.feasibility import grid_capacity_for_substrate
from .validation.limits import (
    EFFECT_OBSERVATION_SLOTS,
    MAX_ACTIONS,
    MAX_AFFORDANCES,
    MAX_CACHE_FILE_SIZE,
    MAX_CASCADES,
    MAX_GRID_CELLS,
    MAX_ITEM_TYPES,
    MAX_METERS,
    MAX_VARIABLES,
    MAX_VFS_PROFILES,
)
from .validation.references import build_symbol_table, resolve_references
from .validation.semantics import select_primary_level

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
COMPILER_VERSION = "0.1.0"

class UniverseCompiler:
    """Entry point for compiling config packs into CompiledUniverse artifacts."""

    def __init__(self) -> None:
        self._cues_compiler = CuesCompiler()
        self._metadata: UniverseMetadata | None = None
        self._observation_spec: ObservationSpec | None = None
        self._action_metadata: ActionSpaceMetadata | None = None
        self._meter_metadata: MeterMetadata | None = None
        self._affordance_metadata: AffordanceMetadata | None = None
        self._optimization_data: OptimizationData | None = None
        self._observation_compiler = ObservationCompiler()
        self._action_compiler = ActionCompiler()
        self._effects_compiler = EffectsCompiler()
        self._metadata_compiler = MetadataCompiler(
            schema_version=SCHEMA_VERSION,
            compiler_version=COMPILER_VERSION,
            compute_config_mtime=self._compute_config_mtime,
            build_cache_fingerprint=self._build_cache_fingerprint,
            get_git_sha=self._get_git_sha,
        )
        self._optimization_compiler = OptimizationCompiler()
        self._vfs_compiler = VFSCompiler()

    def _log_stage(self, number: int, description: str) -> None:
        """Emit a concise stage marker for pipeline tracing."""
        logger.info("Stage %d: %s", number, description)

    def _load_experiment_structure(self, experiment_dir: Path) -> tuple:
        """
        Load all config files from hierarchical v2.1 structure.

        This implements Stage 1 of the v2.1 compiler pipeline: hierarchical config loading.

        Returns:
            (experiment, stratum, environment, actions, agent, levels_dict)
            where levels_dict = {
                "L1_full_observability": (curriculum, bars, affordances, training),
                ...
            }

        Raises:
            FileNotFoundError: If required files or directories missing
            ValueError: If no curriculum levels found
        """
        from townlet.config.affordances_v2_config import load_affordances_v2_config
        from townlet.config.bars_v2_config import load_bars_v2_config
        from townlet.config.environment_config import EnvironmentConfig
        from townlet.config.training_v2_config import load_training_v2_config

        # Load shared configs (experiment-level)
        experiment = ExperimentConfig.from_yaml(experiment_dir / "experiment.yaml")
        stratum = StratumConfig.from_yaml(experiment_dir / "stratum.yaml")
        environment = EnvironmentConfig.from_yaml(experiment_dir / "environment.yaml")
        actions = ActionsConfig.from_yaml(experiment_dir / "actions.yaml")

        # Load brain config (expects directory, not file path)
        brain = load_brain_config(experiment_dir)

        # Load items.yaml (optional)
        items: ItemsCatalogConfig | None = None
        items_path = experiment_dir / "items.yaml"
        if items_path.exists():
            items = ItemsCatalogConfig.from_yaml(items_path)

        levels_dir = experiment_dir / "levels"
        if not levels_dir.exists():
            raise FileNotFoundError(
                f"Missing levels/ directory in {experiment_dir}\n"
                f"Expected structure: {experiment_dir}/levels/L*/{{curriculum,bars,affordances,training,drive}}.yaml"
            )

        levels_dict = {}
        for level_dir in sorted(levels_dir.iterdir()):
            if not level_dir.is_dir():
                continue

            level_name = level_dir.name

            # Load all 5 curriculum-level configs
            curriculum = CurriculumConfig.from_yaml(level_dir / "curriculum.yaml")
            bars = load_bars_v2_config(level_dir)
            affordances = load_affordances_v2_config(level_dir)
            training = load_training_v2_config(level_dir)
            drive = load_drive_as_code_config(level_dir)

            levels_dict[level_name] = (curriculum, bars, affordances, training, drive)

        if not levels_dict:
            raise ValueError(
                f"No curriculum levels found in {levels_dir}\nExpected at least one level directory (e.g., levels/L1_full_observability/)"
            )

        return (experiment, stratum, environment, actions, brain, items, levels_dict)





    def _validate_vocabulary_consistency(self, environment, levels_dict: dict) -> None:
        """
        Validate that all curriculum levels use the same vocabulary as environment.yaml.

        This implements Stage 2 of the v2.1 compiler pipeline: cross-curriculum validation.

        Enforces the WHAT vs HOW split:
        - environment.yaml defines WHAT exists (vocabulary - breaks checkpoints)
        - levels/*/bars.yaml defines HOW bars behave (parameters - doesn't break)
        - levels/*/affordances.yaml defines HOW affordances behave (parameters - doesn't break)

        This ensures checkpoint portability across curriculum levels.

        Args:
            environment: Loaded EnvironmentConfig with canonical vocabulary
            levels_dict: Dict of {level_name: (curriculum, bars, affordances, training, drive)}

        Raises:
            ValueError: If any level has different meter or affordance vocabulary
        """
        # Get canonical vocabulary from environment.yaml
        env_meters = set(m.name for m in environment.environment.meters)
        env_affordances = set(a.name for a in environment.environment.affordances)

        # Validate each curriculum level
        for level_name, (curriculum, bars, affordances, training, drive) in levels_dict.items():
            # Check meter vocabulary matches
            level_meters = set(m.name for m in bars.meters)
            if level_meters != env_meters:
                missing = env_meters - level_meters
                extra = level_meters - env_meters

                msg_parts = [f"Meter vocabulary mismatch in {level_name}/bars.yaml:"]
                if missing:
                    msg_parts.append(f"  Missing meters: {sorted(missing)}")
                if extra:
                    msg_parts.append(f"  Extra meters: {sorted(extra)}")
                msg_parts.append(f"  Expected (from environment.yaml): {sorted(env_meters)}")
                msg_parts.append(f"  Actual (from bars.yaml): {sorted(level_meters)}")
                msg_parts.append("")
                msg_parts.append("All curriculum levels must have same meter vocabulary as environment.yaml")
                msg_parts.append("This ensures checkpoint portability across curriculum.")

                raise ValueError("\n".join(msg_parts))

            # Check affordance vocabulary matches
            level_affordances = set(a.name for a in affordances.affordances)
            if level_affordances != env_affordances:
                missing = env_affordances - level_affordances
                extra = level_affordances - env_affordances

                msg_parts = [f"Affordance vocabulary mismatch in {level_name}/affordances.yaml:"]
                if missing:
                    msg_parts.append(f"  Missing affordances: {sorted(missing)}")
                if extra:
                    msg_parts.append(f"  Extra affordances: {sorted(extra)}")
                msg_parts.append(f"  Expected (from environment.yaml): {sorted(env_affordances)}")
                msg_parts.append(f"  Actual (from affordances.yaml): {sorted(level_affordances)}")
                msg_parts.append("")
                msg_parts.append("All curriculum levels must have same affordance vocabulary as environment.yaml")
                msg_parts.append("This ensures checkpoint portability across curriculum.")

                raise ValueError("\n".join(msg_parts))

        # All levels validated - log confirmation
        logger.info(
            "✓ Vocabulary consistent across %d curriculum levels: %d meters, %d affordances",
            len(levels_dict),
            len(env_meters),
            len(env_affordances),
        )

    def compile(self, experiment_dir: Path, primary_level: str | None = None, use_cache: bool = True) -> CompiledUniverse:
        """Compile v2.1 hierarchical configs into a multi-level CompiledUniverse."""
        if primary_level is None:
            raise ValueError("UniverseCompiler.compile requires an explicit primary_level; implicit level selection is not allowed.")
        experiment_dir = Path(experiment_dir).resolve()
        self.config_pack_path = experiment_dir

        validate_config_dir(experiment_dir)

        # Stage 0: scoping preflight (no YAML parsing yet)
        validate_scoping(experiment_dir)

        # Optional cache fast-path
        cache_path = self._cache_artifact_path(experiment_dir)
        config_hash: str | None = None
        config_mtime: float | None = None

        if use_cache and cache_path.exists():
            try:
                cache_size = cache_path.stat().st_size
                if cache_size > MAX_CACHE_FILE_SIZE:
                    logger.warning(
                        "Cache file exceeds size limit (%d bytes > %d bytes)",
                        cache_size,
                        MAX_CACHE_FILE_SIZE,
                    )
                else:
                    # Compute fingerprint once for comparison
                    config_hash, provenance_id = self._build_cache_fingerprint(experiment_dir)
                    config_mtime = self._compute_config_mtime(experiment_dir)

                    cached = CompiledUniverse.load_from_cache(cache_path)
                    cached_meta = cached.metadata

                    # Treat missing fingerprint fields as stale cache
                    if cached_meta.config_hash and cached_meta.config_mtime and cached_meta.provenance_id:
                        if (
                            cached_meta.config_hash == config_hash
                            and cached_meta.provenance_id == provenance_id
                            and cached_meta.config_mtime >= config_mtime
                        ):
                            logger.info("Loading compiled universe from cache: %s", cache_path)
                            return cached
                        logger.info(
                            "Cache stale for %s (hash/provenance/mtime mismatch); recompiling.",
                            experiment_dir,
                        )
                    else:
                        logger.info("Cached universe at %s missing fingerprint/provenance fields; recompiling.", cache_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load cached universe from %s: %s", cache_path, exc)

        # Stage 0: YAML syntax validation (lightweight)
        validate_yaml_syntax(experiment_dir)

        # Stage 1: load v2.1 configs
        self._log_stage(1, "Parse v2.1 configs")
        loaded = load_v21_configs(experiment_dir)
        raw = loaded.raw

        # Stage 2: symbol table
        self._log_stage(2, "Build symbol table")
        symbol_table = build_symbol_table(raw)

        # Stage 3: resolve references
        self._log_stage(3, "Resolve references")
        resolve_references(raw, symbol_table, experiment_dir, validate_dac_references=self._validate_dac_references)

        # Stage 4: cross-validate semantics
        self._log_stage(4, "Cross-validate semantics")
        self._validate_v21_semantics(raw, experiment_dir)
        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"

        # Select primary level
        primary_level = select_primary_level(raw.levels, primary_level)

        # Stage 5: shared artifact enrichment
        self._log_stage(5, "Enrich shared schemas and effects")
        shared_artifacts = self._stage_5_prepare_shared_artifacts(
            raw,
            experiment_dir,
            primary_level=primary_level,
            temporal_supported=temporal_supported,
        )

        # Stage 6: level compilation + optimization
        self._log_stage(6, "Compile levels and optimization data")
        # Stage 6: Compile levels (per-level artifacts)
        # Compute config hashes for provenance
        brain_hash = self._compute_pydantic_hash(raw.brain)
        experiment_hash = self._compute_pydantic_hash(raw.experiment)
        stratum_hash = self._compute_pydantic_hash(raw.stratum)
        environment_hash = self._compute_pydantic_hash(raw.environment)
        actions_hash = self._compute_pydantic_hash(raw.actions)
        items_hash = self._compute_pydantic_hash(raw.items) if raw.items else None

        level_bundle = self._stage_6_compile_levels(
            raw,
            experiment_dir,
            primary_level=primary_level,
            compiled_vfs_profiles=shared_artifacts.compiled_vfs_profiles,
            compiled_effect_catalog=shared_artifacts.compiled_effect_catalog,
            config_hash=config_hash,
            config_mtime=config_mtime,
            temporal_supported=temporal_supported,
        )

        # Stage 7: emit artifact + cache
        self._log_stage(7, "Emit compiled universe")
        effect_observation_slots = (
            EFFECT_OBSERVATION_SLOTS
            if shared_artifacts.compiled_effect_catalog and shared_artifacts.compiled_effect_catalog.effects
            else 0
        )
        compiled = self._stage_7_emit_artifact(
            raw,
            experiment_dir,
            cache_path,
            use_cache,
            level_bundle.universe_metadata,
            level_bundle.primary_meta,
            level_bundle.all_levels,
            shared_artifacts.compiled_vfs_profiles,
            shared_artifacts.compiled_effect_catalog,
            level_bundle.vfs_expression_schema,
            level_bundle.vfs_observation_marks,
            effect_observation_slots,
            shared_artifacts.vfs_history_spec,
            shared_artifacts.vfs_observation_spec,
            brain_hash=brain_hash,
            experiment_hash=experiment_hash,
            stratum_hash=stratum_hash,
            environment_hash=environment_hash,
            actions_hash=actions_hash,
            items_hash=items_hash,
        )
        return compiled

    def _validate_v21_semantics(self, raw: RawConfigsV21, experiment_dir: Path) -> None:
        """Validate v2.1 semantic constraints (no defaults, no BC)."""

        errors = CompilationErrorCollector(stage="Stage 1b: v2.1 Semantic Validation")

        # 0) Scoping: enforce experiment-level shared catalogs and forbid level overrides
        required_experiment_files = ["vfs_profiles.yaml", "items.yaml"]
        for filename in required_experiment_files:
            path = experiment_dir / filename
            if not path.exists():
                errors.add(
                    f"Missing required experiment-level file: {filename}",
                    code="SCOPING_MISSING_EXPERIMENT_FILE",
                    location=str(path),
                )

        levels_root = experiment_dir / "levels"
        if levels_root.exists():
            for level_dir in sorted(levels_root.iterdir()):
                if not level_dir.is_dir():
                    continue
                for forbidden in ("vfs_profiles.yaml", "effects.yaml"):
                    forbidden_path = level_dir / forbidden
                    if forbidden_path.exists():
                        errors.add(
                            f"Found {forbidden} at level scope ({forbidden_path}). This file must live at the experiment root only.",
                            code="SCOPING_FORBIDDEN_LEVEL_FILE",
                            location=str(forbidden_path),
                        )

        # 1) Temporal requirements
        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"
        for level_name, level in raw.levels.items():
            day_length = level.curriculum.curriculum.day_length
            if temporal_supported and level.curriculum.curriculum.active_temporal:
                if day_length is None or day_length <= 0:
                    errors.add(
                        "curriculum.day_length must be >0 when temporal_support is enabled and active_temporal=true.",
                        code="TEMPORAL_DAY_LENGTH_MISSING",
                        location=str(experiment_dir / "levels" / level_name / "curriculum.yaml"),
                    )

        # 2) Vision compatibility (active vs supported)
        vision_support = raw.stratum.stratum.vision_support
        for level_name, level in raw.levels.items():
            active = level.curriculum.curriculum.active_vision
            active_canon = "partial" if active in {"local", "partial"} else "global"
            if active_canon == "global" and vision_support not in {"global", "both"}:
                errors.add(
                    "Invalid vision configuration: curriculum.active_vision='global' requires stratum.vision_support in ['global','both'].",
                    code="VISION_INCOMPATIBLE",
                    location=str(experiment_dir / "levels" / level_name / "curriculum.yaml"),
                )
            if active_canon == "partial" and vision_support not in {"partial", "both"}:
                errors.add(
                    (
                        "Invalid vision configuration: curriculum.active_vision=partial/local "
                        "requires stratum.vision_support in ['partial','both']."
                    ),
                    code="VISION_INCOMPATIBLE",
                    location=str(experiment_dir / "levels" / level_name / "curriculum.yaml"),
                )

        substrate = raw.stratum.stratum.substrate

        # 3) Action/substrate compatibility: treat warnings as errors to enforce explicit action sets
        validator = SubstrateActionValidator(substrate, raw.actions)
        validation_result = validator.validate()
        for err in validation_result.errors:
            errors.add(
                err,
                code="SUBSTRATE_ACTION_INCOMPATIBLE",
                location=str(experiment_dir / "actions.yaml"),
            )
        for warn in validation_result.warnings:
            errors.add(
                warn,
                code="SUBSTRATE_ACTION_WARNING_AS_ERROR",
                location=str(experiment_dir / "actions.yaml"),
            )

        # 3b) Continuous substrates must declare an explicit interaction_radius
        if substrate.type in {"continuous", "continuousnd"}:
            continuous_cfg = getattr(substrate, "continuous", None)
            if continuous_cfg is None or getattr(continuous_cfg, "interaction_radius", None) is None:
                errors.add(
                    "Continuous substrates require an explicit interaction_radius; no defaults are applied.",
                    code="INTERACTION_RADIUS_MISSING",
                    location=str(experiment_dir / "stratum.yaml"),
                )

        # 4) Environment↔level vocabulary alignment and cascades/modulations coverage
        env_meter_names = {m.name for m in raw.environment.environment.meters}
        env_affordance_names = {a.name for a in raw.environment.environment.affordances}
        env_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in raw.environment.environment.modulation_graph}
        env_edges = {(c.source, c.target) for c in raw.environment.environment.cascade_graph}

        # Cascade edges must reference valid meters
        for edge in env_edges:
            if edge[0] not in env_meter_names or edge[1] not in env_meter_names:
                errors.add(
                    f"environment.yaml cascade_graph references unknown meters: {edge}",
                    code="CASCADE_INVALID_METER",
                    location=str(experiment_dir / "environment.yaml"),
                )

        # 4b) Action meter validation (JANK-02) against environment meter vocabulary.
        # Validate any custom action costs/effects in actions.yaml.
        for action in raw.actions.actions.custom_actions:
            for field_name in ("costs", "effects"):
                payload = getattr(action, field_name, None) or {}
                if not payload:
                    continue
                invalid_meters = [meter for meter in payload.keys() if meter not in env_meter_names]
                if invalid_meters:
                    for meter in invalid_meters:
                        errors.add(
                            (
                                f"Action '{action.name}' references unknown meter '{meter}' in {field_name}. "
                                "Ensure all meters are defined in environment.yaml/bars.yaml."
                            ),
                            code="UAC-ACT-002",
                            location=f"{experiment_dir / 'actions.yaml'}:{action.name}",
                        )

        # Grid capacity (hard error)
        grid_capacity = grid_capacity_for_substrate(substrate)

        for level_name, level in raw.levels.items():
            level_dir = experiment_dir / "levels" / level_name

            level_meter_names = {meter.name for meter in level.bars.meters}
            level_affordance_names = {aff.name for aff in level.affordances.affordances}

            if level_meter_names != env_meter_names:
                missing = env_meter_names - level_meter_names
                extra = level_meter_names - env_meter_names
                errors.add(
                    "Meter vocabulary mismatch between environment.yaml and levels/bars.yaml.",
                    code="METER_VOCAB_MISMATCH",
                    location=str(level_dir / "bars.yaml"),
                )
                if missing:
                    errors.add_hint(f"Missing meters: {sorted(missing)}")
                if extra:
                    errors.add_hint(f"Unexpected meters: {sorted(extra)}")

            if level_affordance_names != env_affordance_names:
                missing = env_affordance_names - level_affordance_names
                extra = level_affordance_names - env_affordance_names
                errors.add(
                    "Affordance vocabulary mismatch between environment.yaml and levels/affordances.yaml.",
                    code="AFFORDANCE_VOCAB_MISMATCH",
                    location=str(level_dir / "affordances.yaml"),
                )
                if missing:
                    errors.add_hint(f"Missing affordances: {sorted(missing)}")
                if extra:
                    errors.add_hint(f"Unexpected affordances: {sorted(extra)}")

            # Cascade coverage per level
            level_edges = {(c.source, c.target) for c in level.bars.cascades}
            missing_edges = env_edges - level_edges
            extra_edges = level_edges - env_edges
            if missing_edges:
                errors.add(
                    f"Missing cascades (must match environment.yaml cascade_graph): {sorted(missing_edges)}",
                    code="CASCADE_MISSING",
                    location=str(level_dir / "bars.yaml"),
                )
            if extra_edges:
                errors.add(
                    f"Extra cascades not declared in environment.yaml cascade_graph: {sorted(extra_edges)}",
                    code="CASCADE_EXTRA",
                    location=str(level_dir / "bars.yaml"),
                )

            # Modulation coverage per level
            level_mod_pairs = {(m.bar, tuple(sorted(m.affordances))) for m in level.affordances.modulations}
            missing_mods = env_mod_pairs - level_mod_pairs
            extra_mods = level_mod_pairs - env_mod_pairs
            if missing_mods:
                errors.add(
                    f"Missing modulations (must match environment.yaml modulation_graph): {sorted(missing_mods)}",
                    code="MODULATION_MISSING",
                    location=str(level_dir / "affordances.yaml"),
                )
            if extra_mods:
                errors.add(
                    f"Extra modulations not declared in environment.yaml modulation_graph: {sorted(extra_mods)}",
                    code="MODULATION_EXTRA",
                    location=str(level_dir / "affordances.yaml"),
                )

            # Affordance field checks
            for aff in level.affordances.affordances:
                if getattr(aff, "opening_hours", None) is None:
                    errors.add(
                        f"Affordance '{aff.name}' missing opening_hours.",
                        code="AFFORDANCE_OPENING_HOURS_MISSING",
                        location=str(level_dir / "affordances.yaml"),
                    )
                deployment = getattr(aff, "deployment", None)
                if deployment is not None and getattr(deployment, "type", None) == "fixed" and not deployment.positions:
                    errors.add(
                        f"Affordance '{aff.name}' has deployment.type='fixed' but no positions specified.",
                        code="AFFORDANCE_DEPLOYMENT_POSITIONS_MISSING",
                        location=str(level_dir / "affordances.yaml"),
                    )
                invalid_cost_meters = [name for name in aff.costs.keys() if name not in env_meter_names]

                # Extract meter names from interactions (Effects commands)
                invalid_interaction_meters = []
                for stage_commands in aff.interactions.values():
                    for cmd in stage_commands:
                        modify = getattr(cmd, "modify", None)
                        if isinstance(modify, str) and modify.startswith("target.bar."):
                            meter_name = modify.split(".")[-1]
                            if meter_name not in env_meter_names:
                                invalid_interaction_meters.append(meter_name)

                if invalid_cost_meters or invalid_interaction_meters:
                    errors.add(
                        f"Affordance '{aff.name}' references unknown meters in costs/interactions.",
                        code="AFFORDANCE_INVALID_METER",
                        location=str(level_dir / "affordances.yaml"),
                    )

            # enabled_affordances must be subset of environment affordances
            enabled_affordances = getattr(level.training, "enabled_affordances", None)
            normalized_enabled = env_affordance_names if enabled_affordances is None else {str(name) for name in enabled_affordances}
            invalid_enabled = normalized_enabled - env_affordance_names
            if invalid_enabled:
                errors.add(
                    f"training.enabled_affordances contains unknown entries: {sorted(invalid_enabled)}",
                    code="ENABLED_AFFORDANCES_INVALID",
                    location=str(level_dir / "training.yaml"),
                )

            # Grid capacity (hard error)
            if grid_capacity is not None:
                deployed_count = len(normalized_enabled)
                population_size = getattr(level.training.population, "size", 0)
                required_slots = deployed_count + population_size
                if required_slots > grid_capacity:
                    errors.add(
                        f"Grid capacity exceeded: {required_slots} entities (agents + affordances) vs grid capacity {grid_capacity}.",
                        code="GRID_CAPACITY_EXCEEDED",
                        location=str(level_dir / "training.yaml"),
                    )

        # 6) DAC must be present per level and non-empty
        meters = env_meter_names
        variables_set = (
            set(var.name for var in raw.environment.environment.variables) if hasattr(raw.environment.environment, "variables") else set()
        )

        for level_name, level in raw.levels.items():
            level_path = experiment_dir / "levels" / level_name / "drive.yaml"
            drive = getattr(level, "drive", None)

            if drive is None:
                errors.add(f"drive.yaml is required for level {level_name}.", code="LEVEL_DRIVE_MISSING", location=str(level_path))
                continue

            # Modifiers must exist and reference known bars/variables
            modifiers = getattr(drive, "modifiers", {}) or {}
            # Modifiers can be empty if no contextual adjustment needed, but usually we want some.
            # Let's not enforce non-empty modifiers strictly unless required by design.

            for mod_name, mod_cfg in modifiers.items():
                source = getattr(mod_cfg, "source", None)
                if source and source not in meters and source not in variables_set:
                    # Check if it's a VFS variable (might be implicitly defined or explicit)
                    # For now, we check against env variables.
                    pass
                    # Note: _validate_dac_references in Stage 3 does more thorough checking.
                    # Here we just do basic structural checks if needed.

            # Extrinsic bonuses
            extrinsic = getattr(drive, "extrinsic", None)
            if extrinsic is None:
                errors.add(
                    f"drive.extrinsic is required for level {level_name}.", code="LEVEL_DRIVE_EXTRINSIC_MISSING", location=str(level_path)
                )

            # Intrinsic
            intrinsic = getattr(drive, "intrinsic", None)
            if intrinsic is None:
                errors.add(
                    f"drive.intrinsic is required for level {level_name}.", code="LEVEL_DRIVE_INTRINSIC_MISSING", location=str(level_path)
                )

        errors.check_and_raise()

    def _stage_5_prepare_shared_artifacts(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        *,
        primary_level: str,
        temporal_supported: bool,
    ) -> SharedCompilerArtifacts:
        """Stage 5 – build shared schemas (bars/VFS) and compile effects catalog."""
        primary_level_config = raw.levels[primary_level]
        bar_schema: dict[str, str] = {meter.name: "float" for meter in primary_level_config.bars.meters}

        compiled_vfs_profiles = self._vfs_compiler.compile_profiles(experiment_dir, bar_schema)
        self._vfs_compiler.validate_item_profile_bindings(raw.items, compiled_vfs_profiles)

        from townlet.vfs.history import collect_history_requirements

        vfs_history_spec = collect_history_requirements(compiled_vfs_profiles.global_profile if compiled_vfs_profiles else None)

        effects_schema: dict[str, str] = {
            "intensity": "float",
            "elapsed_ticks": "float",
            "duration_remaining": "float",
        }

        for meter in primary_level_config.bars.meters:
            effects_schema[f"bar.{meter.name}"] = "float"
            effects_schema[f"target.bar.{meter.name}"] = "float"

        for var in getattr(raw.environment.environment, "variables", []) or []:
            var_type = getattr(var, "type", None)
            if var_type in ("agent_ref", "item_ref"):
                effects_schema[f"vfs.{var.name}"] = var_type
                effects_schema[f"target.vfs.{var.name}"] = var_type
            else:
                vfs_type = "bool" if var_type == "bool" else "float"
                effects_schema[f"vfs.{var.name}"] = vfs_type
                effects_schema[f"target.vfs.{var.name}"] = vfs_type

        if compiled_vfs_profiles and compiled_vfs_profiles.item_profiles:
            for compiled_profile in compiled_vfs_profiles.item_profiles.values():
                for var in compiled_profile.variables:
                    var_type = getattr(var, "type", None)
                    if var_type in ("agent_ref", "item_ref"):
                        effects_schema[f"self.vfs.{var.name}"] = var_type
                    else:
                        vfs_type = "bool" if var_type == "bool" else "float"
                        effects_schema[f"self.vfs.{var.name}"] = vfs_type

        compiled_effect_catalog = self._effects_compiler.compile_catalog(
            experiment_dir,
            effects_schema,
            time_enabled=temporal_supported,
        )
        max_items_per_agent = raw.items.max_items_per_agent if raw.items is not None else VFSObservationSpec.max_items_per_agent
        vfs_observation_spec = VFSObservationSpec.from_compiled_profiles(
            compiled_vfs_profiles,
            max_items_per_agent=max_items_per_agent,
        )

        return SharedCompilerArtifacts(
            bar_schema=bar_schema,
            compiled_vfs_profiles=compiled_vfs_profiles,
            effects_schema=effects_schema,
            compiled_effect_catalog=compiled_effect_catalog,
            vfs_history_spec=vfs_history_spec,
            vfs_observation_spec=vfs_observation_spec,
        )

    def _stage_6_compile_levels(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        *,
        primary_level: str,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        compiled_effect_catalog: EffectCatalog | None,
        config_hash: str | None,
        config_mtime: float | None,
        temporal_supported: bool,
    ) -> CompiledLevelBundle:
        """Stage 6 – compile level metadata, optimization data, and derived schemas."""
        all_levels: dict[str, CompiledUniverse.LevelMetadata] = {}
        for level_name, level in raw.levels.items():
            logger.info("Compiling level: %s", level_name)
            obs_spec = self._observation_compiler.build_spec(
                raw.stratum,
                raw.environment,
                level.curriculum,
                compiled_vfs_profiles,
                raw.items,
                compiled_effect_catalog,
            )
            obs_activity = self._observation_compiler.build_activity(obs_spec)
            bar_schema = {meter.name: "float" for meter in level.bars.meters}
            action_metadata = self._action_compiler.build_action_space_metadata(
                raw.stratum,
                raw.actions,
                level.training,
                level.affordances,
                raw.items,
                self.config_pack_path,
            )
            meter_metadata = self._metadata_compiler.build_meter_metadata(raw.environment, level.bars)
            affordance_metadata = self._metadata_compiler.build_affordance_metadata(level.affordances)

            # Compile item spawn predicates (type-check and store AST on rules)
            self._vfs_compiler.compile_item_spawn_conditions(
                level.items_appearance,
                bar_schema=bar_schema,
                env_vars=getattr(raw.environment.environment, "variables", []) or [],
                compiled_vfs_profiles=compiled_vfs_profiles,
                temporal_supported=temporal_supported and level.curriculum.curriculum.active_temporal,
            )
            day_length = level.curriculum.curriculum.day_length
            if temporal_supported and level.curriculum.curriculum.active_temporal:
                if day_length is None or day_length <= 0:
                    raise ValueError(
                        "curriculum.day_length is required when temporal mechanics are declared in stratum.temporal_support.\n"
                        f"  Experiment: {experiment_dir}\n"
                        f"  Level: {level_name}\n"
                        "Provide an explicit positive day_length; no defaults are applied."
                    )
            else:
                day_length = 0

            optimization_data = self._optimization_compiler.build_optimization_data(
                level.bars,
                level.affordances,
                meter_metadata,
                affordance_metadata,
                action_metadata,
                day_length=day_length,
            )
            if compiled_effect_catalog is not None:
                self._optimization_compiler.validate_trigger_cascade_ids(compiled_effect_catalog, optimization_data, level_name=level_name)
            vfs_fields = self._observation_compiler.build_vfs_observation_fields(obs_spec, raw.environment)
            vfs_variables = self._observation_compiler.build_vfs_variables(obs_spec, raw.environment)

            # Compute hashes for level-specific configs
            drive_hash = self._compute_pydantic_hash(level.drive)
            curriculum_hash = self._compute_pydantic_hash(level.curriculum)
            bars_hash = self._compute_pydantic_hash(level.bars)
            affordances_hash = self._compute_pydantic_hash(level.affordances)
            training_hash = self._compute_pydantic_hash(level.training)

            all_levels[level_name] = CompiledUniverse.LevelMetadata(
                level_name=level_name,
                bars=level.bars,
                affordances=level.affordances,
                drive=level.drive,
                curriculum=level.curriculum,
                training=level.training,
                observation_spec=obs_spec,
                observation_activity=obs_activity,
                action_metadata=action_metadata,
                meter_metadata=meter_metadata,
                affordance_metadata=affordance_metadata,
                optimization_data=optimization_data,
                drive_hash=drive_hash,
                curriculum_hash=curriculum_hash,
                bars_hash=bars_hash,
                affordances_hash=affordances_hash,
                training_hash=training_hash,
                vfs_observation_fields=vfs_fields,
                vfs_variables=vfs_variables,
                items_appearance=level.items_appearance,
            )

        primary_meta = all_levels[primary_level]
        primary_level_config = raw.levels[primary_level]

        universe_metadata = self._metadata_compiler.build_universe_metadata(
            raw,
            primary_meta,
            experiment_dir=experiment_dir,
            config_hash=config_hash,
            config_mtime=config_mtime,
        )

        vfs_expression_schema = self._vfs_compiler.build_expression_schema(primary_level_config.bars, compiled_vfs_profiles)

        variables_reference_path = experiment_dir / "variables_reference.yaml"
        vfs_observation_marks: dict[str, set[str]] | None = None
        if variables_reference_path.exists():
            from townlet.vfs.schema import load_variables_reference_config

            variables_from_yaml = tuple(load_variables_reference_config(experiment_dir))
            vfs_observation_marks = self._vfs_compiler.extract_observation_marks(variables_from_yaml)

        return CompiledLevelBundle(
            all_levels=all_levels,
            primary_meta=primary_meta,
            universe_metadata=universe_metadata,
            vfs_expression_schema=vfs_expression_schema,
            vfs_observation_marks=vfs_observation_marks,
        )

    def _stage_7_emit_artifact(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        cache_path: Path,
        use_cache: bool,
        universe_metadata: UniverseMetadata,
        primary_meta: CompiledUniverse.LevelMetadata,
        all_levels: dict[str, CompiledUniverse.LevelMetadata],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        compiled_effect_catalog: EffectCatalog | None,
        vfs_expression_schema: dict[str, str],
        vfs_observation_marks: dict[str, set[str]] | None,
        effect_observation_slots: int,
        vfs_history_spec: dict[str, int],
        vfs_observation_spec: VFSObservationSpec | None,
        brain_hash: str | None,
        experiment_hash: str,
        stratum_hash: str,
        environment_hash: str,
        actions_hash: str,
        items_hash: str | None,
    ) -> CompiledUniverse:
        """Stage 7 – emit the compiled artifact and persist cache."""
        compiled = CompiledUniverse(
            metadata=universe_metadata,
            observation_spec=primary_meta.observation_spec,
            observation_activity=primary_meta.observation_activity,
            vfs_observation_fields=primary_meta.vfs_observation_fields,
            vfs_variables=primary_meta.vfs_variables,
            action_space_metadata=primary_meta.action_metadata,
            meter_metadata=primary_meta.meter_metadata,
            affordance_metadata=primary_meta.affordance_metadata,
            optimization_data=primary_meta.optimization_data,
            experiment=raw.experiment,
            stratum=raw.stratum,
            environment=raw.environment,
            actions=raw.actions,
            brain=raw.brain,  # Changed from agent to brain
            items_catalog=raw.items,
            compiled_vfs_profiles=compiled_vfs_profiles,
            compiled_effect_catalog=compiled_effect_catalog,
            effect_observation_slots=effect_observation_slots,
            vfs_expression_schema=vfs_expression_schema,
            vfs_history_spec=vfs_history_spec or None,
            vfs_observation_marks=vfs_observation_marks,
            vfs_observation_spec=vfs_observation_spec,
            experiment_dir=experiment_dir,
            drive_hash=primary_meta.drive_hash,
            brain_hash=brain_hash,
            experiment_hash=experiment_hash,
            stratum_hash=stratum_hash,
            environment_hash=environment_hash,
            actions_hash=actions_hash,
            items_hash=items_hash,
            all_levels=all_levels,
        )

        if use_cache:
            try:
                cache_dir = self._cache_directory_for(experiment_dir)
                self._prepare_cache_directory(cache_dir)
                compiled.save_to_cache(cache_path)
                logger.info("Saved compiled universe cache to %s", cache_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to write cache artifact to %s: %s", cache_path, exc)

        return compiled

    def _compute_pydantic_hash(self, config: Any) -> str:
        """Compute SHA256 hash of a Pydantic config."""
        if config is None:
            return ""
        # Use JSON dump to get consistent representation
        json_str = config.model_dump_json()
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------




    # ------------------------------------------------------------------
    # v2.1 helpers
    # ------------------------------------------------------------------


    @staticmethod







    @staticmethod



    def _validate_drive_references_v21(
        self,
        raw: RawConfigsV21,
        primary_meta: CompiledUniverse.LevelMetadata,
        compiled: CompiledUniverse,
    ) -> None:
        """Validate v2.1 agent.drive references against meters and VFS variables.

        This is a minimal v2.1 analogue of DAC reference validation. It ensures:
        - RangeMultiplierModifier.source points to an existing meter or VFS variable.
        - Extrinsic bonuses reference valid meters.

        ShapingConfig is intentionally left free-form for now; its internal fields are not validated here.

        Note: This function is currently unused (dead code) and needs refactoring for v2.1 schema.
        """
        drive = raw.agent.agent.drive  # type: ignore[attr-defined]  # TODO: Fix for v2.1 schema (function is unused)

        meter_names = {m.name for m in primary_meta.meter_metadata.meters}
        vfs_var_ids = {var.id for var in compiled.vfs_variables}

        # Validate modifiers: source must be either a meter or a VFS variable
        for mod_name, modifier in drive.modifiers.items():
            source = modifier.source
            if source in meter_names or source in vfs_var_ids:
                continue
            raise ValueError(
                "Invalid drive.modifiers entry in agent.yaml.\n"
                f"  Experiment: {compiled.experiment_dir}\n"
                f"  Modifier: {mod_name}\n"
                f"  Source: {source!r}\n"
                f"  Valid meters: {sorted(meter_names)}\n"
                f"  Valid VFS variables: {sorted(vfs_var_ids)}\n"
                "\nEach modifier.source must reference a meter or VFS variable."
            )

        # Validate extrinsic bonus bar references
        extrinsic = drive.extrinsic
        if extrinsic.bonuses:
            for bonus in extrinsic.bonuses:
                if bonus.bar not in meter_names:
                    raise ValueError(
                        "Invalid extrinsic bonus bar in agent.yaml.\n"
                        f"  Experiment: {compiled.experiment_dir}\n"
                        f"  Bonus bar: {bonus.bar!r}\n"
                        f"  Valid meters: {sorted(meter_names)}\n"
                        "\nAll extrinsic.bonuses[*].bar values must match meters declared in environment.yaml."
                    )

        # Validate substrate ↔ action compatibility for v2.1 actions
        # Build a temporary ActionSpaceConfig from substrate defaults + custom actions.
        try:
            substrate = SubstrateFactory.build(raw.stratum.stratum.substrate, torch.device("cpu"))
            substrate_actions = substrate.get_default_actions()
        except Exception as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"Failed to derive substrate default actions for v2.1 validation.\n  Experiment: {compiled.experiment_dir}\n  Error: {exc}"
            ) from exc

        custom_actions_cfg = raw.actions.actions.custom_actions
        actions: list[ActionConfig] = []

        # Normalize substrate actions into ActionConfig
        for act in substrate_actions:
            actions.append(
                ActionConfig(
                    id=act.id,
                    name=act.name,
                    type=act.type,
                    costs={},
                    effects={},
                    delta=act.delta,
                    teleport_to=act.teleport_to,
                    enabled=True,
                    description=None,
                    icon=None,
                    source="substrate",
                    source_affordance=None,
                )
            )

        # Normalize custom actions into ActionConfig; IDs assigned sequentially after substrate actions
        next_id = len(actions)
        for custom in custom_actions_cfg:
            actions.append(
                ActionConfig(
                    id=next_id,
                    name=custom.name,
                    type="interaction" if custom.name != "WAIT" else "passive",
                    costs={},
                    effects={},
                    delta=None,
                    teleport_to=None,
                    enabled=custom.enabled_by_default,
                    description=custom.description or None,
                    icon=None,
                    source="custom",
                    source_affordance=None,
                )
            )
            next_id += 1

        action_space = ActionSpaceConfig(actions=actions)
        validator = SubstrateActionValidator(raw.stratum.stratum.substrate, action_space)
        validation_result = validator.validate()
        if validation_result.errors:
            messages = "\n  - " + "\n  - ".join(validation_result.errors)
            raise ValueError(
                "Substrate/action incompatibility detected for v2.1 actions.\n"
                f"  Experiment: {compiled.experiment_dir}\n"
                f"{messages}\n"
                "\nUpdate actions.yaml or stratum.yaml so movement actions are compatible with the substrate."
            )
        for warning in validation_result.warnings:
            logger.warning(
                "Substrate/action compatibility warning (v2.1).\n  Experiment: %s\n  Warning: %s",
                compiled.experiment_dir,
                warning,
            )

    def _validate_economic_balance_v21(self, raw: RawConfigsV21) -> None:
        """Emit economic balance warnings for v2.1 configs."""
        _ = raw.environment.environment  # TODO: Decide if we need this.
        affordances_cfg = next(iter(raw.levels.values())).affordances

        total_income = self._compute_max_income(affordances_cfg.affordances)
        total_costs = self._compute_total_costs(affordances_cfg.affordances)

        if total_income <= 0.0 and total_costs > 0.0:
            logger.warning(
                "Economic imbalance (v2.1): No income-generating affordances available while costs accrue.\n"
                "  Experiment: %s\n"
                "  File: environment.yaml / affordances.yaml\n",
                raw.experiment_dir,
            )
        elif total_income < total_costs:
            logger.warning(
                "Economic imbalance (v2.1): Total income (%.2f) < total costs (%.2f).\n"
                "  Experiment: %s\n"
                "  File: environment.yaml / affordances.yaml\n",
                total_income,
                total_costs,
                raw.experiment_dir,
            )

        # Check whether income affordances ever open during the curriculum day.
        income_affordances = [aff for aff in affordances_cfg.affordances if self._affordance_positive_amount_for_meter(aff, "money") > 0.0]
        if not income_affordances:
            return

        hours_with_income = 0
        for hour in range(24):
            if any(self._affordance_open_for_hour(aff, hour) for aff in income_affordances):
                hours_with_income += 1

        if hours_with_income == 0:
            logger.warning(
                "Economic imbalance (v2.1): Income-generating affordances exist but none are available during the day.\n"
                "  Experiment: %s\n"
                "  File: affordances.yaml\n",
                raw.experiment_dir,
            )
        elif 0 < hours_with_income < 12:
            logger.warning(
                "Economic stress (v2.1): Jobs only available %.0fh/day while costs accrue 24h/day.\n"
                "  Experiment: %s\n"
                "  File: affordances.yaml\n",
                float(hours_with_income),
                raw.experiment_dir,
            )


    def _validate_dac_references(
        self,
        dac_config: DriveAsCodeConfig,
        symbol_table: UniverseSymbolTable,
        errors: CompilationErrorCollector,
    ) -> None:
        """Validate DAC references to bars, variables, and affordances.

        Stage 3 validation: Ensures DAC configurations reference valid entities.

        Checks:
        - Modifiers reference valid bars or VFS variables
        - Extrinsic strategies reference valid bars/variables
        - Shaping bonuses reference valid affordances
        """
        # Validate modifier sources
        for mod_name, mod_config in dac_config.modifiers.items():
            bar_ref = getattr(mod_config, "bar", None)
            variable_ref = getattr(mod_config, "variable", None)
            if bar_ref:
                if bar_ref not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-001",
                            message=f"Modifier '{mod_name}' references undefined bar: {bar_ref}",
                            location=f"drive_as_code.yaml:modifiers.{mod_name}",
                        )
                    )
            elif variable_ref:
                if variable_ref not in symbol_table.vfs_variables:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-002",
                            message=f"Modifier '{mod_name}' references undefined VFS variable: {variable_ref}",
                            location=f"drive_as_code.yaml:modifiers.{mod_name}",
                        )
                    )

        # Validate extrinsic strategy bar references
        extrinsic_bars = getattr(dac_config.extrinsic, "bars", None)
        if extrinsic_bars:
            for bar in extrinsic_bars:
                if bar not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-003",
                            message=f"Extrinsic strategy references undefined bar: {bar}",
                            location="drive_as_code.yaml:extrinsic.bars",
                        )
                    )

        # Validate extrinsic bar_bonuses (if present)
        for idx, bonus in enumerate(getattr(dac_config.extrinsic, "bar_bonuses", []) or []):
            bonus_bar = getattr(bonus, "bar", None)
            if bonus_bar and bonus_bar not in symbol_table.meters:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-004",
                        message=f"Extrinsic bar bonus references undefined bar: {bonus_bar}",
                        location=f"drive_as_code.yaml:extrinsic.bar_bonuses[{idx}]",
                    )
                )

        # Validate extrinsic variable_bonuses (if present)
        for idx, var_bonus in enumerate(getattr(dac_config.extrinsic, "variable_bonuses", []) or []):
            var_ref = getattr(var_bonus, "variable", None)
            if var_ref and var_ref not in symbol_table.vfs_variables:
                errors.add(
                    CompilationMessage(
                        code="DAC-REF-005",
                        message=f"Extrinsic variable bonus references undefined VFS variable: {var_ref}",
                        location=f"drive_as_code.yaml:extrinsic.variable_bonuses[{idx}]",
                    )
                )

        # Validate shaping bonus bar/affordance/variable references
        for idx, shaping in enumerate(dac_config.shaping):
            # Validate affordance references
            if shaping.type == "approach_reward":
                target_aff = getattr(shaping, "target_affordance", None) or getattr(shaping, "target", None)
                if target_aff and target_aff not in symbol_table.affordances:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-006",
                            message=f"Shaping bonus references undefined affordance: {target_aff}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "completion_bonus":
                aff_ref = getattr(shaping, "affordance", None)
                if aff_ref and aff_ref not in symbol_table.affordances:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-007",
                            message=f"Shaping bonus (completion_bonus) references undefined affordance: {aff_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "streak_bonus":
                aff_ref = getattr(shaping, "affordance", None)
                if aff_ref and aff_ref not in symbol_table.affordances:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-008",
                            message=f"Shaping bonus (streak_bonus) references undefined affordance: {aff_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "timing_bonus":
                for time_range_idx, time_range in enumerate(shaping.time_ranges):
                    aff_ref = getattr(time_range, "affordance", None)
                    if aff_ref and aff_ref not in symbol_table.affordances:
                        errors.add(
                            CompilationMessage(
                                code="DAC-REF-009",
                                message=f"Shaping bonus (timing_bonus) references undefined affordance: {aff_ref}",
                                location=f"drive_as_code.yaml:shaping[{idx}].time_ranges[{time_range_idx}]",
                            )
                        )

            # Validate bar references
            elif shaping.type == "efficiency_bonus":
                bar_ref = getattr(shaping, "bar", None)
                if bar_ref and bar_ref not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-010",
                            message=f"Shaping bonus (efficiency_bonus) references undefined bar: {bar_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "crisis_avoidance":
                bar_ref = getattr(shaping, "bar", None)
                if bar_ref and bar_ref not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-011",
                            message=f"Shaping bonus (crisis_avoidance) references undefined bar: {bar_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "economic_efficiency":
                money_bar = getattr(shaping, "money_bar", None)
                if money_bar and money_bar not in symbol_table.meters:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-012",
                            message=f"Shaping bonus (economic_efficiency) references undefined bar: {money_bar}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )
            elif shaping.type == "balance_bonus":
                for bar in getattr(shaping, "bars", []) or []:
                    if bar and bar not in symbol_table.meters:
                        errors.add(
                            CompilationMessage(
                                code="DAC-REF-013",
                                message=f"Shaping bonus (balance_bonus) references undefined bar: {bar}",
                                location=f"drive_as_code.yaml:shaping[{idx}]",
                            )
                        )
            elif shaping.type == "state_achievement":
                for condition_idx, condition in enumerate(getattr(shaping, "conditions", []) or []):
                    condition_bar = getattr(condition, "bar", None)
                    if condition_bar and condition_bar not in symbol_table.meters:
                        errors.add(
                            CompilationMessage(
                                code="DAC-REF-014",
                                message=f"Shaping bonus (state_achievement) references undefined bar: {condition_bar}",
                                location=f"drive_as_code.yaml:shaping[{idx}].conditions[{condition_idx}]",
                            )
                        )

            # Validate VFS variable references
            elif shaping.type == "vfs_variable":
                var_ref = getattr(shaping, "variable", None)
                if var_ref and var_ref not in symbol_table.vfs_variables:
                    errors.add(
                        CompilationMessage(
                            code="DAC-REF-015",
                            message=f"Shaping bonus (vfs_variable) references undefined VFS variable: {var_ref}",
                            location=f"drive_as_code.yaml:shaping[{idx}]",
                        )
                    )

    def _compute_dac_hash(self, dac_config: DriveAsCodeConfig) -> str:
        """Compute SHA256 content hash of DAC configuration for provenance.

        Args:
            dac_config: DAC configuration to hash

        Returns:
            SHA256 hex digest (64 character string)

        Purpose:
            - Checkpoint validation (detect DAC changes)
            - Provenance tracking (which drive functions were used)
            - Reproducibility (verify exact reward configuration)

        Example:
            >>> dac = DriveAsCodeConfig(...)
            >>> hash_val = self._compute_dac_hash(dac)
            >>> len(hash_val)
            64
        """
        import hashlib
        import json

        # Convert to dict for stable JSON serialization
        dac_dict = dac_config.model_dump(mode="json")

        # Compute SHA256 hash with sorted keys for determinism
        json_str = json.dumps(dac_dict, sort_keys=True)
        hash_digest = hashlib.sha256(json_str.encode()).hexdigest()

        return hash_digest

    def _validate_spatial_feasibility(self, raw_configs: Any, errors: CompilationErrorCollector, formatter) -> None:
        """Validate that substrate has enough space for all affordances + agents.

        Reads spatial dimensions from substrate.yaml (single source of truth).
        Accounts for population.num_agents from training.yaml.
        Only applies to discrete grid substrates (grid, gridnd).
        """
        substrate = raw_configs.substrate

        # Calculate grid cells based on substrate type
        grid_cells: int | None = None
        dimensions_str = ""

        if substrate.type == "grid" and substrate.grid is not None:
            # Grid2D (square) or Grid3D (cubic)
            if substrate.grid.topology == "square":
                grid_cells = substrate.grid.width * substrate.grid.height
                dimensions_str = f"{substrate.grid.width}×{substrate.grid.height}"
            elif substrate.grid.topology == "cubic":
                if substrate.grid.depth is not None:
                    grid_cells = substrate.grid.width * substrate.grid.height * substrate.grid.depth
                    dimensions_str = f"{substrate.grid.width}×{substrate.grid.height}×{substrate.grid.depth}"
        elif substrate.type == "gridnd" and substrate.gridnd is not None:
            # GridND (N-dimensional discrete grid)
            grid_cells = 1
            for dim_size in substrate.gridnd.dimension_sizes:
                grid_cells *= dim_size
            dimensions_str = "×".join(str(d) for d in substrate.gridnd.dimension_sizes)
        else:
            # Continuous, aspatial - no spatial feasibility check
            return

        if grid_cells is None or grid_cells <= 0:
            return

        # Enforce upper bound for DoS protection
        if grid_cells > MAX_GRID_CELLS:
            errors.add(
                formatter(
                    "UAC-VAL-001",
                    f"Grid size exceeds safety limit: {grid_cells} cells (max {MAX_GRID_CELLS})",
                    "substrate.yaml:grid",
                )
            )
            return

        enabled_affordances = raw_configs.environment.enabled_affordances
        required = len(enabled_affordances)

        num_agents = raw_configs.population.num_agents
        required_cells = required + num_agents
        if required_cells > grid_cells:
            agent_label = "agent" if num_agents == 1 else "agents"
            message = (
                f"Spatial impossibility: Grid has {grid_cells} cells ({dimensions_str}) but need {required_cells} "
                f"({required} affordances + {num_agents} {agent_label})."
            )
            errors.add(formatter("UAC-VAL-001", message, "substrate.yaml:grid"))

    def _enforce_security_limits(self, raw_configs: Any, errors: CompilationErrorCollector) -> None:
        checks = (
            (len(raw_configs.bars), MAX_METERS, "bars.yaml", "meters"),
            (len(raw_configs.affordances), MAX_AFFORDANCES, "affordances.yaml", "affordances"),
            (len(raw_configs.cascades), MAX_CASCADES, "cascades.yaml", "cascades"),
            (len(raw_configs.global_actions.actions), MAX_ACTIONS, "configs/global_actions.yaml", "actions"),
            (len(raw_configs.variables_reference), MAX_VARIABLES, "variables_reference.yaml", "variables"),
            (len(getattr(raw_configs, "item_types", []) or []), MAX_ITEM_TYPES, "items.yaml", "item types"),
            (len(getattr(raw_configs, "compiled_vfs_profiles", []) or []), MAX_VFS_PROFILES, "vfs_profiles.yaml", "vfs profiles"),
        )

        for count, limit, location, label in checks:
            if count > limit:
                errors.add(
                    f"Too many {label}: found {count} (max {limit}). This may indicate config injection or duplication.",
                    code="UAC-VAL-006",
                    location=location,
                )

    def _validate_economic_balance(
        self,
        raw_configs: Any,
        errors: CompilationErrorCollector,
        formatter,
        allow_unfeasible: bool,
    ) -> None:
        enabled_lookup = self._build_enabled_affordance_lookup(raw_configs.environment.enabled_affordances)

        total_income = self._compute_max_income(raw_configs.affordances)
        total_costs = self._compute_total_costs(raw_configs.affordances)

        if total_income <= 0.0 and total_costs > 0.0:
            self._record_feasibility_issue(
                errors,
                formatter,
                allow_unfeasible,
                "UAC-VAL-002",
                "No income-generating affordances available while costs accrue. Universe is unwinnable.",
                "affordances.yaml",
            )
        elif total_income < total_costs:
            errors.add_warning(
                formatter(
                    "UAC-VAL-002",
                    f"Economic imbalance: Total income ({total_income:.2f}) < total costs ({total_costs:.2f}).",
                    "affordances.yaml",
                )
            )

        income_hours = self._count_income_hours(raw_configs, enabled_lookup)
        if total_income > 0.0 and income_hours == 0:
            self._record_feasibility_issue(
                errors,
                formatter,
                allow_unfeasible,
                "UAC-VAL-002",
                (
                    "Income-generating affordances exist but none are available during the day. "
                    "Adjust operating_hours or enable additional jobs."
                ),
                "affordances.yaml",
            )
        elif 0 < income_hours < 12:
            errors.add_warning(
                formatter(
                    "UAC-VAL-002",
                    f"Income stress: jobs only available {income_hours:.0f}h/day. Costs accrue 24h/day.",
                    "affordances.yaml",
                )
            )

    def _validate_cascade_cycles(self, raw_configs: Any, errors: CompilationErrorCollector, formatter) -> None:
        graph = self._build_cascade_graph(raw_configs.cascades)
        cycles = self._detect_cycles(graph)
        if not cycles:
            return
        for cycle in cycles:
            cycle_str = " → ".join(cycle + [cycle[0]])
            errors.add(formatter("UAC-VAL-003", f"Cascade circularity detected: {cycle_str}.", "cascades.yaml"))

    def _validate_operating_hours(self, raw_configs: Any, errors: CompilationErrorCollector, formatter) -> None:
        for affordance in raw_configs.affordances:
            operating_hours = affordance.operating_hours
            # operating_hours is now required by schema - no None check needed
            if len(operating_hours) != 2:
                errors.add(
                    formatter(
                        "UAC-VAL-004",
                        "operating_hours must contain exactly two entries [open_hour, close_hour]",
                        f"affordances.yaml:{affordance.id}:operating_hours",
                    )
                )
                continue
            open_hour, close_hour = operating_hours
            if open_hour < 0 or open_hour > 23:
                errors.add(
                    formatter(
                        "UAC-VAL-004",
                        f"open_hour must be 0-23, got {open_hour}",
                        f"affordances.yaml:{affordance.id}:operating_hours",
                    )
                )
            if close_hour < 1 or close_hour > 28:
                errors.add(
                    formatter(
                        "UAC-VAL-004",
                        f"close_hour must be 1-28, got {close_hour}",
                        f"affordances.yaml:{affordance.id}:operating_hours",
                    )
                )

    def _validate_availability_and_modes(
        self,
        raw_configs: Any,
        symbol_table: UniverseSymbolTable,
        errors: CompilationErrorCollector,
        formatter,
    ) -> None:
        for affordance in raw_configs.affordances:
            for idx, constraint in enumerate(getattr(affordance, "availability", []) or []):
                location = f"affordances.yaml:{affordance.id}:availability[{idx}]"
                meter = self._get_attr_value(constraint, "meter")
                if meter not in symbol_table.meters:
                    errors.add(
                        formatter(
                            "UAC-VAL-007",
                            f"Availability constraint references unknown meter '{meter}'",
                            location,
                        )
                    )
                for bound_name in ("min", "max"):
                    bound_value = self._get_attr_value(constraint, bound_name)
                    if bound_value is None:
                        continue
                    if bound_value < 0.0 or bound_value > 1.0:
                        errors.add(
                            formatter(
                                "UAC-VAL-007",
                                f"Availability {bound_name} must be within [0.0, 1.0], got {bound_value}",
                                location,
                            )
                        )
                min_value = self._get_attr_value(constraint, "min")
                max_value = self._get_attr_value(constraint, "max")
                if min_value is not None and max_value is not None and min_value >= max_value:
                    errors.add(
                        formatter(
                            "UAC-VAL-007",
                            f"Availability min ({min_value}) must be < max ({max_value}).",
                            location,
                        )
                    )

            modes = getattr(affordance, "modes", {}) or {}
            for mode_name, mode in modes.items():
                hours = self._get_attr_value(mode, "hours")
                if not hours:
                    continue
                start, end = hours
                if not (0 <= start <= 23 and 0 <= end <= 23):
                    errors.add(
                        formatter(
                            "UAC-VAL-007",
                            f"Mode '{mode_name}' hours must be within 0-23, got {hours}",
                            f"affordances.yaml:{affordance.id}:modes:{mode_name}",
                        )
                    )

    def _validate_capabilities_and_effect_pipelines(
        self,
        raw_configs: Any,
        errors: CompilationErrorCollector,
        formatter,
    ) -> None:
        # Build affordance ID set for prerequisite validation
        affordance_ids = {aff.id for aff in raw_configs.affordances}
        # Build meter name set for skill_scaling validation
        meter_names = {bar.name for bar in raw_configs.bars}

        for affordance in raw_configs.affordances:
            capabilities = getattr(affordance, "capabilities", []) or []
            types = [self._get_attr_value(cap, "type") for cap in capabilities]
            multi_tick_caps = [cap for cap, cap_type in zip(capabilities, types) if cap_type == "multi_tick"]
            has_resumable_flag = any(bool(self._get_attr_value(cap, "resumable")) for cap in capabilities)

            if affordance.interaction_type and affordance.interaction_type.lower() == "instant" and multi_tick_caps:
                errors.add(
                    formatter(
                        "UAC-VAL-008",
                        "Instant affordances cannot declare multi_tick capabilities.",
                        f"affordances.yaml:{affordance.id}",
                    )
                )

            # Validate interactions field (Effects commands)
            interactions = getattr(affordance, "interactions", {})
            if multi_tick_caps:
                has_per_tick = bool(interactions.get("per_tick"))
                has_on_completion = bool(interactions.get("on_completion"))
                if not has_per_tick and not has_on_completion:
                    errors.add(
                        formatter(
                            "UAC-VAL-008",
                            "multi_tick capability requires per_tick or on_completion effects.",
                            f"affordances.yaml:{affordance.id}",
                        )
                    )
                else:
                    cap = multi_tick_caps[0]
                    early_exit_allowed = bool(self._get_attr_value(cap, "early_exit_allowed"))
                    if interactions.get("on_early_exit") and not early_exit_allowed:
                        errors.add_warning(
                            formatter(
                                "UAC-VAL-008",
                                "on_early_exit effects defined but early_exit_allowed is False.",
                                f"affordances.yaml:{affordance.id}",
                            )
                        )
            elif interactions.get("per_tick"):
                errors.add_warning(
                    formatter(
                        "UAC-VAL-008",
                        "Per-tick effects defined without multi_tick capability.",
                        f"affordances.yaml:{affordance.id}",
                    )
                )

            if "cooldown" in types and affordance.interaction_type and affordance.interaction_type.lower() == "instant":
                # Instant affordances with cooldowns are permitted, but highlight to operators.
                errors.add_warning(
                    formatter(
                        "UAC-VAL-008",
                        "Instant affordance declares a cooldown capability; ensure this is intentional.",
                        f"affordances.yaml:{affordance.id}",
                    )
                )

            if has_resumable_flag and not multi_tick_caps:
                errors.add(
                    formatter(
                        "UAC-VAL-008",
                        "'resumable' flag requires a multi_tick capability.",
                        f"affordances.yaml:{affordance.id}:capabilities",
                    )
                )

            # Validate capability-specific references (combined loop for efficiency)
            for idx, capability in enumerate(capabilities):
                cap_type = self._get_attr_value(capability, "type")

                # UAC-VAL-010: Validate prerequisite affordance references
                if cap_type == "prerequisite":
                    required = self._get_attr_value(capability, "required_affordances") or []
                    for req_id in required:
                        if req_id not in affordance_ids:
                            errors.add(
                                formatter(
                                    "UAC-VAL-010",
                                    f"Prerequisite affordance '{req_id}' does not exist in affordances.yaml",
                                    f"affordances.yaml:{affordance.id}:capabilities[{idx}]",
                                )
                            )

                # UAC-VAL-012: Validate skill_scaling meter references
                elif cap_type == "skill_scaling":
                    skill_meter = self._get_attr_value(capability, "skill")
                    if skill_meter and skill_meter not in meter_names:
                        errors.add(
                            formatter(
                                "UAC-VAL-012",
                                f"Skill scaling capability references non-existent meter '{skill_meter}'. "
                                f"Valid meters: {sorted(meter_names)}",
                                f"affordances.yaml:{affordance.id}:capabilities[{idx}]",
                            )
                        )

            # UAC-VAL-011: Validate probabilistic interactions completeness
            has_probabilistic = any(self._get_attr_value(cap, "type") == "probabilistic" for cap in capabilities)

            if has_probabilistic:
                # interactions is already defined earlier in this method
                has_on_completion = bool(interactions.get("on_completion"))
                has_on_failure = bool(interactions.get("on_failure"))

                missing_stages = []
                if not has_on_completion:
                    missing_stages.append("on_completion (success path)")
                if not has_on_failure:
                    missing_stages.append("on_failure (failure path)")

                if missing_stages:
                    errors.add(
                        formatter(
                            "UAC-VAL-011",
                            f"Probabilistic affordance '{affordance.id}' should define both success and failure effects. "
                            f"Missing: {', '.join(missing_stages)}",
                            f"affordances.yaml:{affordance.id}:interactions",
                        )
                    )

    def _validate_affordance_positions(
        self,
        raw_configs: Any,
        errors: CompilationErrorCollector,
        formatter,
    ) -> None:
        for affordance in raw_configs.affordances:
            position = getattr(affordance, "position", None)
            if position is None:
                continue
            in_bounds, message = self._position_in_bounds(position, raw_configs.substrate)
            if not in_bounds:
                errors.add(
                    formatter(
                        "UAC-VAL-010",
                        message,
                        f"affordances.yaml:{affordance.id}:position",
                    )
                )

    def _validate_capacity_and_sustainability(
        self,
        raw_configs: Any,
        errors: CompilationErrorCollector,
        formatter,
        allow_unfeasible: bool,
    ) -> None:
        enabled_lookup = self._build_enabled_affordance_lookup(raw_configs.environment.enabled_affordances)
        self._validate_meter_sustainability(raw_configs, enabled_lookup, errors, formatter, allow_unfeasible)
        self._validate_capacity_constraints(raw_configs, enabled_lookup, errors, formatter)

    def _position_in_bounds(self, position: object, substrate: SubstrateConfig) -> tuple[bool, str]:
        if substrate.type == "grid" and substrate.grid is not None:
            grid = substrate.grid
            width, height = grid.width, grid.height
            depth = grid.depth or 1
            if isinstance(position, list):
                if len(position) == 2:
                    x, y = position
                    if 0 <= x < width and 0 <= y < height:
                        return True, ""
                    return False, f"Position {position} outside grid bounds 0-{width - 1}, 0-{height - 1}."
                if len(position) == 3:
                    if grid.depth is None:
                        return False, "Position includes depth but substrate is 2D."
                    x, y, z = position
                    if 0 <= x < width and 0 <= y < height and 0 <= z < depth:
                        return True, ""
                    return False, f"Position {position} outside 3D grid bounds."
                return False, f"Grid positions must be length 2 or 3. Got {len(position)} elements."
            if isinstance(position, int):
                total_nodes = width * height * depth
                if 0 <= position < total_nodes:
                    return True, ""
                return False, f"Graph node id {position} outside 0-{total_nodes - 1}."
            if isinstance(position, dict):
                # Hex/axial grids do not currently expose explicit bounds; assume valid.
                return True, ""
            return False, f"Unsupported position format '{type(position).__name__}'."
        return True, ""

    @staticmethod
    def _get_attr_value(obj: object, key: str):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _validate_substrate_action_compatibility(
        self,
        raw_configs: Any,
        errors: CompilationErrorCollector,
        formatter,
        add_hint,
    ) -> None:
        validator = SubstrateActionValidator(raw_configs.substrate, raw_configs.global_actions)
        result = validator.validate()
        for message in result.errors:
            errors.add(formatter("UAC-VAL-006", message, "configs/global_actions.yaml"))
        for warning in result.warnings:
            errors.add_warning(formatter("UAC-VAL-006", warning, "configs/global_actions.yaml"))

    def _compute_total_costs(self, affordances: list[AffordanceParamConfig]) -> float:
        total = 0.0
        for affordance in affordances:
            total += self._sum_amounts(getattr(affordance, "costs", []))
            total += self._sum_amounts(getattr(affordance, "costs_per_tick", []))
        return total

    def _compute_max_income(self, affordances: list[AffordanceParamConfig]) -> float:
        total = 0.0
        for affordance in affordances:
            # Extract from interactions field (Effects commands)
            interactions = getattr(affordance, "interactions", {})
            total += self._sum_money_entries(interactions.get("on_start", []), positive_only=True)
            total += self._sum_money_entries(interactions.get("per_tick", []), positive_only=True)
            total += self._sum_money_entries(interactions.get("on_completion", []), positive_only=True)
            total += self._sum_money_entries(interactions.get("on_early_exit", []), positive_only=True)
            total += self._sum_money_entries(interactions.get("on_failure", []), positive_only=True)
        return total

    def _sum_money_entries(self, entries: object | None, *, positive_only: bool) -> float:
        total = 0.0
        for entry in self._iter_entries(entries):
            if self._get_meter(entry) != "money":
                continue
            amount = self._get_amount(entry)
            if amount is None:
                continue
            if positive_only and amount <= 0:
                continue
            total += amount
        return total

    def _sum_amounts(self, entries: object | None) -> float:
        total = 0.0
        for entry in self._iter_entries(entries):
            amount = self._get_amount(entry)
            if amount is not None:
                total += amount
        return total

    def _sum_positive_meter_entries(self, entries: object | None, meter_name: str) -> float:
        total = 0.0
        for entry in self._iter_entries(entries):
            if self._get_meter(entry) != meter_name:
                continue
            amount = self._get_amount(entry)
            if amount is None or amount <= 0:
                continue
            total += amount
        return total

    def _build_enabled_affordance_lookup(self, enabled_affordances: list[str] | None) -> set[str]:
        if enabled_affordances is None:
            raise ValueError(
                "enabled_affordances must be explicitly provided (empty list allowed to disable all affordances); null is not allowed."
            )
        return {str(name) for name in enabled_affordances}

    def _is_affordance_enabled(self, affordance: AffordanceConfig, enabled_lookup: set[str] | None) -> bool:
        if enabled_lookup is None:
            return True
        return affordance.name in enabled_lookup or affordance.id in enabled_lookup

    def _count_income_hours(self, raw_configs: Any, enabled_lookup: set[str] | None) -> float:
        income_affordances = [
            aff
            for aff in raw_configs.affordances
            if self._is_affordance_enabled(aff, enabled_lookup) and self._affordance_positive_amount_for_meter(aff, "money") > 0
        ]
        if not income_affordances:
            return 0.0

        # If temporal mechanics are disabled, operating_hours are ignored (all affordances available 24/7)
        if not raw_configs.environment.enable_temporal_mechanics:
            return 24.0

        # operating_hours is now required by schema - no None check needed
        hours_with_income = 0
        for hour in range(24):
            if any(self._affordance_open_for_hour(aff, hour) for aff in income_affordances):
                hours_with_income += 1
        return float(hours_with_income)

    def _affordance_open_for_hour(self, affordance: AffordanceParamConfig, hour: int) -> bool:
        """Return True if an affordance is open for the given hour.

        v2.1 semantics: availability is defined via opening_hours on
        curriculum-level affordances (AffordanceParamConfig from AffordancesV2Config).
        The compiler converts opening_hours config to operating_hours runtime tuples
        for use with temporal_utils.is_affordance_open().
        """
        opening_hours = getattr(affordance, "opening_hours", None)
        if opening_hours is None:
            raise ValueError("Affordance missing opening_hours in v2.1 config. All affordances must declare opening_hours.")

        # opening_hours.enabled == False → 24/7 availability.
        if not opening_hours.enabled:
            return True

        windows = getattr(opening_hours, "schedule", []) or []
        for window in windows:
            start = getattr(window, "start", None)
            end = getattr(window, "end", None)
            if start is None or end is None:
                continue
            if is_affordance_open(hour, (start, end)):
                return True
        return False

    def _affordance_positive_amount_for_meter(self, affordance: AffordanceParamConfig | AffordanceConfig, meter_name: str) -> float:
        # Extract from interactions field (Effects commands)
        interactions = getattr(affordance, "interactions", {})
        total = 0.0

        total += self._sum_positive_meter_entries(interactions.get("on_start", []), meter_name)
        total += self._sum_positive_meter_entries(interactions.get("per_tick", []), meter_name)
        total += self._sum_positive_meter_entries(interactions.get("on_completion", []), meter_name)
        total += self._sum_positive_meter_entries(interactions.get("on_early_exit", []), meter_name)
        total += self._sum_positive_meter_entries(interactions.get("on_failure", []), meter_name)

        return total

    def _compute_max_restoration_for_meter(
        self,
        meter_name: str,
        affordances: tuple[AffordanceConfig, ...],
        enabled_lookup: set[str] | None,
    ) -> float:
        max_restoration = 0.0
        for affordance in affordances:
            if not self._is_affordance_enabled(affordance, enabled_lookup):
                continue
            restoration = self._affordance_positive_amount_for_meter(affordance, meter_name)
            if restoration > max_restoration:
                max_restoration = restoration
        return max_restoration

    def _validate_meter_sustainability(
        self,
        raw_configs: Any,
        enabled_lookup: set[str] | None,
        errors: CompilationErrorCollector,
        formatter,
        allow_unfeasible: bool,
    ) -> None:
        critical_meter_names = self._collect_critical_meter_names(raw_configs)
        if not critical_meter_names:
            return

        for bar in raw_configs.bars:
            if bar.name not in critical_meter_names:
                continue
            depletion = float(getattr(bar, "base_depletion", 0.0))
            if depletion <= 0.0:
                continue
            restoration = self._compute_max_restoration_for_meter(bar.name, raw_configs.affordances, enabled_lookup)
            if restoration <= 0.0:
                self._record_feasibility_issue(
                    errors,
                    formatter,
                    allow_unfeasible,
                    "UAC-VAL-005",
                    f"Meter {bar.name} unsustainable: passive depletion {depletion:.4f}/tick but no restoring affordances are enabled.",
                    f"bars.yaml:{bar.name}",
                )
            elif restoration < depletion:
                self._record_feasibility_issue(
                    errors,
                    formatter,
                    allow_unfeasible,
                    "UAC-VAL-005",
                    f"Meter {bar.name} unsustainable: depletion ({depletion:.4f}/tick) > max restoration ({restoration:.4f}/tick).",
                    f"bars.yaml:{bar.name}",
                )

    def _collect_critical_meter_names(self, raw_configs: Any) -> set[str]:
        names: set[str] = set()
        for bar in raw_configs.bars:
            if self._is_meter_critical(bar):
                names.add(bar.name)
        return names

    def _is_meter_critical(self, bar: MeterConfig) -> bool:
        if getattr(bar, "critical", False):
            return True
        tier = getattr(bar, "tier", None)
        return isinstance(tier, str) and tier.lower() == "pivotal"

    def _validate_capacity_constraints(
        self,
        raw_configs: Any,
        enabled_lookup: set[str] | None,
        errors: CompilationErrorCollector,
        formatter,
    ) -> None:
        num_agents = getattr(raw_configs.population, "num_agents", 1)
        if num_agents <= 1:
            return

        critical_affordances = self._find_critical_path_affordances(raw_configs, enabled_lookup)
        for affordance in critical_affordances:
            capacity = getattr(affordance, "capacity", None)
            if capacity is None:
                continue
            if capacity < num_agents:
                errors.add_warning(
                    formatter(
                        "UAC-VAL-005",
                        f"Affordance {affordance.name} capacity {capacity} < num_agents ({num_agents}). Contentions may cause starvation.",
                        f"affordances.yaml:{affordance.id}",
                    )
                )

    def _find_critical_path_affordances(
        self,
        raw_configs: Any,
        enabled_lookup: set[str] | None,
    ) -> list[AffordanceConfig]:
        critical_meters = self._collect_critical_meter_names(raw_configs)
        if not critical_meters:
            return []

        critical_affordances: list[AffordanceConfig] = []
        for affordance in raw_configs.affordances:
            if not self._is_affordance_enabled(affordance, enabled_lookup):
                continue
            if any(self._affordance_positive_amount_for_meter(affordance, meter) > 0.0 for meter in critical_meters):
                critical_affordances.append(affordance)
        return critical_affordances

    def _record_feasibility_issue(
        self,
        errors: CompilationErrorCollector,
        formatter,
        allow_unfeasible: bool,
        code: str,
        message: str,
        location: str,
    ) -> None:
        issue = formatter(code, message, location)
        if allow_unfeasible:
            errors.add_warning(f"{issue.format()} (allow_unfeasible_universe=true)")
        else:
            errors.add(issue)

    def _get_meter(self, entry: object | None) -> str | None:
        """Extract meter name from Effects command."""
        if entry is None:
            return None
        if isinstance(entry, dict):
            # Effects command: extract from "modify" field
            if "modify" in entry:
                modify = entry["modify"]
                if isinstance(modify, str) and modify.startswith("target.bar."):
                    return modify.split(".")[-1]
            return None
        return None

    def _get_amount(self, entry: object | None) -> float | None:
        """Extract meter delta from Effects command."""
        if entry is None:
            return None

        # Effects command: parse simple addition from "value" expression
        if isinstance(entry, dict) and "value" in entry:
            value_expr = entry["value"]
            if isinstance(value_expr, str):
                # Parse simple pattern: "target.bar.X + Y" or "target.bar.X - Y"
                # For more complex expressions, return None (heuristic validation only)
                if " + " in value_expr:
                    parts = value_expr.split(" + ")
                    if len(parts) == 2:
                        try:
                            return float(parts[1].strip())
                        except ValueError:
                            return None
                elif " - " in value_expr:
                    parts = value_expr.split(" - ")
                    if len(parts) == 2:
                        try:
                            return -float(parts[1].strip())
                        except ValueError:
                            return None
        return None

    @staticmethod
    def _iter_entries(entries: object | None) -> Iterable[object]:
        if entries is None:
            return ()
        if isinstance(entries, Iterable) and not isinstance(entries, str | bytes):
            return entries
        return ()

    def _build_cascade_graph(self, cascades: tuple[CascadeConfig, ...]) -> dict[str, list[str]]:
        graph: dict[str, list[str]] = {}
        for cascade in cascades:
            graph.setdefault(cascade.source, []).append(cascade.target)
        return graph

    def _detect_cycles(self, graph: dict[str, list[str]]) -> list[list[str]]:
        """Detect cycles in cascade dependency graph using depth-first search.

        Algorithm: DFS with path tracking to identify back edges (cycles).
        Time Complexity: O(V + E) where V=number of meters, E=number of cascades
        Space Complexity: O(V) for visited set and recursion stack

        Args:
            graph: Adjacency list mapping source meter -> list of target meters

        Returns:
            List of cycles, where each cycle is a list of meter names forming a loop
        """
        cycles: list[list[str]] = []
        visited: set[str] = set()
        stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in stack:
                    try:
                        start_index = path.index(neighbor)
                        cycles.append(path[start_index:])
                    except ValueError:
                        cycles.append([neighbor])
            stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _normalize_yaml(self, file_path: Path) -> str:
        try:
            with file_path.open() as handle:
                data = yaml.safe_load(handle) or {}
            return yaml.dump(data, sort_keys=True)
        except yaml.YAMLError as exc:
            # Transform raw YAML errors into friendly syntax errors
            error_msg = str(exc)
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                error_msg = f"line {mark.line + 1}, column {mark.column + 1}: {getattr(exc, 'problem', None) or 'syntax error'}"
                if hasattr(exc, "context"):
                    error_msg = f"{exc.context}\n  {error_msg}"

            raise CompilationError(
                stage="Config Validation",
                errors=[
                    CompilationMessage(
                        code="YAML_SYNTAX_ERROR",
                        message=error_msg,
                        location=str(file_path),
                    )
                ],
                hints=[
                    "Check YAML indentation (use spaces, not tabs)",
                    "Ensure lists use proper '- item' syntax",
                    "Validate YAML syntax at yamllint.com or with 'yamllint <file>'",
                ],
            ) from exc

    def _build_cache_fingerprint(self, config_dir: Path) -> tuple[str, str]:
        config_hash = self._compute_config_hash(config_dir)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        from pydantic import __version__ as pydantic_version  # lazy import to avoid startup penalty

        provenance = self._compute_provenance_id(
            config_hash=config_hash,
            compiler_version=COMPILER_VERSION,
            git_sha=self._get_git_sha(),
            python_version=python_version,
            torch_version=torch.__version__,
            pydantic_version=pydantic_version,
        )
        return config_hash, provenance

    def _cache_directory_for(self, config_dir: Path) -> Path:
        """Return the cache directory path for a config pack."""

        return config_dir / ".compiled"

    def _cache_artifact_path(self, config_dir: Path) -> Path:
        """Return the expected cache artifact path for a config pack."""

        return self._cache_directory_for(config_dir) / "universe.msgpack"

    def _prepare_cache_directory(self, cache_dir: Path) -> None:
        """Ensure the cache directory exists and is writable."""

        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:  # pragma: no cover - defensive
            raise RuntimeError(f"Unable to create cache directory at {cache_dir}: {exc}") from exc

        if not cache_dir.is_dir():
            raise RuntimeError(f"Cache path {cache_dir} exists but is not a directory")

        if not os.access(cache_dir, os.W_OK):
            raise RuntimeError(f"Cache directory {cache_dir} is not writable")

    def _compute_config_hash(self, config_dir: Path) -> str:
        # Include root YAML files and any hierarchical level YAMLs.
        yaml_files = sorted(config_dir.glob("*.yaml"))

        levels_dir = config_dir / "levels"
        if levels_dir.exists():
            yaml_files.extend(sorted(levels_dir.rglob("*.yaml")))

        # v2.1 actions are per-experiment via actions.yaml or embedded in training.yaml.

        digest = hashlib.sha256()
        for file_path in yaml_files:
            if not file_path.exists():
                continue
            normalized = self._normalize_yaml(file_path)
            digest.update(str(file_path.relative_to(config_dir)).encode("utf-8"))
            digest.update(normalized.encode("utf-8"))
        return digest.hexdigest()

    def _compute_config_mtime(self, config_dir: Path) -> float:
        """Compute maximum modification time of all config files.

        Returns the latest mtime across all YAML files in the config directory.
        This ensures cache is invalidated when ANY config file changes
        (including comment/whitespace-only changes).
        """
        yaml_files = sorted(config_dir.glob("*.yaml"))

        levels_dir = config_dir / "levels"
        if levels_dir.exists():
            yaml_files.extend(sorted(levels_dir.rglob("*.yaml")))

        max_mtime = 0.0
        for file_path in yaml_files:
            if not file_path.exists():
                continue
            mtime = file_path.stat().st_mtime
            if mtime > max_mtime:
                max_mtime = mtime
        return max_mtime

    def _compute_provenance_id(
        self,
        *,
        config_hash: str,
        compiler_version: str,
        git_sha: str,
        python_version: str,
        torch_version: str,
        pydantic_version: str,
    ) -> str:
        """Compute full provenance ID including all dependencies.

        Cache validity includes this ID so compiler and dependency changes cannot
        reuse an artifact compiled under different executable provenance.
        """
        payload = "|".join(
            [
                config_hash,
                compiler_version,
                git_sha,
                python_version,
                torch_version,
                pydantic_version,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _get_git_sha(self) -> str:
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def _summarize_affordance_effects(self, affordance: AffordanceConfig) -> dict[str, float]:
        totals: defaultdict[str, float] = defaultdict(float)

        def _add_entries(entries: object | None) -> None:
            for entry in self._iter_entries(entries):
                meter = self._get_meter(entry)
                amount = self._get_amount(entry)
                if meter and amount is not None:
                    totals[meter] += amount

        # Extract from interactions field (Effects commands)
        interactions = getattr(affordance, "interactions", {})
        _add_entries(interactions.get("on_start", []))
        _add_entries(interactions.get("per_tick", []))
        _add_entries(interactions.get("on_completion", []))
        _add_entries(interactions.get("on_early_exit", []))
        _add_entries(interactions.get("on_failure", []))

        return dict(totals)

    def _extract_money_cost(self, affordance: AffordanceConfig) -> float:
        total = 0.0
        total += self._sum_money_entries(getattr(affordance, "costs", []), positive_only=True)
        total += self._sum_money_entries(getattr(affordance, "costs_per_tick", []), positive_only=True)
        return total

    def _normalize_affordance_position_metadata(self, position: Any) -> Any:
        if position is None:
            return None
        if isinstance(position, list):
            return tuple(position)
        if isinstance(position, dict):
            return dict(position)
        return position

    def _tensorize_affordance_position(self, position: Any, device: torch.device) -> torch.Tensor | None:
        if position is None:
            return None
        if isinstance(position, torch.Tensor):
            return position.to(device=device, dtype=torch.float32)

        if isinstance(position, dict):
            if set(position.keys()) == {"q", "r"}:
                coords = [position["q"], position["r"]]
            else:
                return None
            return torch.tensor(coords, dtype=torch.float32, device=device)

        if isinstance(position, list | tuple):
            return torch.tensor(list(position), dtype=torch.float32, device=device)

        if isinstance(position, Number):
            return torch.tensor([position], dtype=torch.float32, device=device)

        return None


# DELETED: _is_open() wrapper - now using temporal_utils.is_affordance_open() directly (JANK-09 fix)
