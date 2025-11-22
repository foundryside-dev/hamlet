"""UniverseCompiler implementation (Stage 1 scaffolding)."""

from __future__ import annotations

import difflib
import hashlib
import logging
import math
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from numbers import Number
from pathlib import Path
from typing import Any

import torch
import yaml

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordanceParamConfig, AffordancesV2Config
from townlet.config.agent_config import AgentConfig
from townlet.config.bars_v2_config import BarsV2Config, MeterConfig
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.config.effects_config import EffectsConfig
from townlet.config.environment_config import CascadeConfig
from townlet.config.environment_config import EnvironmentConfig as EnvConfigV21
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsCatalogConfig, build_item_command_action_name
from townlet.config.stratum_config import ObservationModeConfig, StratumConfig, SubstrateConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.effects.catalog import EffectCatalog
from townlet.effects.schema import CommandType
from townlet.environment.action_config import ActionConfig, ActionSpaceConfig
from townlet.environment.action_labels import get_labels
from townlet.environment.affordance_config import AffordanceConfig  # Runtime representation
from townlet.environment.substrate_action_validator import SubstrateActionValidator
from townlet.environment.temporal_utils import is_affordance_open
from townlet.substrate.factory import SubstrateFactory
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.dto import (
    ActionMetadata,
    ActionSpaceMetadata,
    AffordanceInfo,
    AffordanceMetadata,
    MeterInfo,
    MeterMetadata,
    ObservationActivity,
    ObservationField,
    ObservationSpec,
    UniverseMetadata,
)
from townlet.universe.optimization import OptimizationData
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.symbol_table import UniverseSymbolTable
from townlet.vfs.profiles import CompiledItemProfile, VFSProfileCompiler
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope
from townlet.vfs.schema import ObservationField as VFSObservationField
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError

from .compiled import CompiledVFSProfiles
from .cues_compiler import CuesCompiler
from .errors import CompilationError, CompilationErrorCollector, CompilationMessage

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
COMPILER_VERSION = "0.1.0"

MAX_METERS = 100
MAX_AFFORDANCES = 100
MAX_CASCADES = 500
MAX_ACTIONS = 300  # Increased for discretized continuous actions (32×7 = 195+)
MAX_VARIABLES = 200
MAX_GRID_CELLS = 10000  # 100×100 maximum (DoS protection)
MAX_CACHE_FILE_SIZE = 10 * 1024 * 1024  # 10MB (cache bomb protection)
EFFECT_OBSERVATION_SLOTS = 8  # Fixed slots per agent for observable effects
MAX_ITEM_TYPES = 200
MAX_VFS_PROFILES = 200
MAX_SPAWN_RULES_PER_ITEM = 200


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
        from townlet.config.actions_config import ActionsConfig
        from townlet.config.affordances_v2_config import load_affordances_v2_config
        from townlet.config.bars_v2_config import load_bars_v2_config
        from townlet.config.curriculum_config import CurriculumConfig
        from townlet.config.environment_config import EnvironmentConfig
        from townlet.config.stratum_config import StratumConfig
        from townlet.config.training_v2_config import load_training_v2_config

        # Load shared configs (experiment-level)
        experiment = ExperimentConfig.from_yaml(experiment_dir / "experiment.yaml")
        stratum = StratumConfig.from_yaml(experiment_dir / "stratum.yaml")
        environment = EnvironmentConfig.from_yaml(experiment_dir / "environment.yaml")
        actions = ActionsConfig.from_yaml(experiment_dir / "actions.yaml")
        agent = AgentConfig.from_yaml(experiment_dir / "agent.yaml")

        # Load all curriculum levels
        levels_dir = experiment_dir / "levels"
        if not levels_dir.exists():
            raise FileNotFoundError(
                f"Missing levels/ directory in {experiment_dir}\n"
                f"Expected structure: {experiment_dir}/levels/L*/{{curriculum,bars,affordances,training}}.yaml"
            )

        levels_dict = {}
        for level_dir in sorted(levels_dir.iterdir()):
            if not level_dir.is_dir():
                continue

            level_name = level_dir.name

            # Load all 4 curriculum-level configs
            curriculum = CurriculumConfig.from_yaml(level_dir / "curriculum.yaml")
            bars = load_bars_v2_config(level_dir)
            affordances = load_affordances_v2_config(level_dir)
            training = load_training_v2_config(level_dir)

            levels_dict[level_name] = (curriculum, bars, affordances, training)

        if not levels_dict:
            raise ValueError(
                f"No curriculum levels found in {levels_dir}\nExpected at least one level directory (e.g., levels/L1_full_observability/)"
            )

        return (experiment, stratum, environment, actions, agent, levels_dict)

    def _compile_vfs_profiles(self, experiment_dir: Path, bar_schema: dict[str, str]) -> CompiledVFSProfiles | None:
        """Load and compile VFS profiles from experiment directory.

        Args:
            experiment_dir: Experiment root directory
            bar_schema: Type schema for bars (for expression type checking)

        Returns:
            Compiled profiles or None if vfs_profiles.yaml not present
        """
        profiles_path = experiment_dir / "vfs_profiles.yaml"

        if not profiles_path.exists():
            logger.debug("vfs_profiles.yaml not found, skipping VFS profile compilation")
            return None

        # Load YAML
        profiles_data = yaml.safe_load(profiles_path.read_text())

        # Validate with Pydantic
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

        # Compile profiles
        compiler = VFSProfileCompiler()
        compiler.validate_version(profiles_config.version)

        compiled_global = None
        if profiles_config.global_profile is not None:
            compiled_global = compiler.compile_global_profile(profiles_config.global_profile, bar_schema=bar_schema)

        # Compile item profiles
        compiled_item_profiles: dict[str, CompiledItemProfile] = {}
        if profiles_config.item_profiles:
            for item_profile_config in profiles_config.item_profiles:
                compiled_profile = compiler.compile_item_profile(
                    item_profile_config,
                    bar_schema=bar_schema,
                )
                compiled_item_profiles[compiled_profile.profile_name] = compiled_profile

        return CompiledVFSProfiles(
            global_profile=compiled_global,
            agent_profile=None,  # TODO: Task 4 or later
            item_profiles=compiled_item_profiles,
        )

    def _compile_effects_catalog(
        self, experiment_dir: Path, effects_schema: dict[str, str], *, time_enabled: bool = True
    ) -> EffectCatalog | None:
        """Load and compile effects catalog from experiment directory.

        Args:
            experiment_dir: Experiment config directory containing effects.yaml
            effects_schema: Type schema for effect command validation

        Returns:
            Compiled effects catalog, or None if effects.yaml not found

        Raises:
            None - effects.yaml is optional
        """
        effects_path = experiment_dir / "effects.yaml"

        if not effects_path.exists():
            return None

        # Load YAML
        effects_data = yaml.safe_load(effects_path.read_text())

        # Validate with Pydantic
        effects_config = EffectsConfig(**effects_data)

        # Compile catalog with schema validation
        catalog = EffectCatalog.from_config(effects_config, schema=effects_schema, time_enabled=time_enabled)

        return catalog

    def _build_vfs_expression_schema(self, bars: BarsV2Config, compiled_vfs_profiles: CompiledVFSProfiles | None) -> dict[str, str]:
        """Build type schema for VFS expression runtime validation.

        Args:
            bars: Bars configuration (for bar paths)
            compiled_vfs_profiles: Compiled VFS profiles (for vfs paths)

        Returns:
            Type schema mapping path -> type
        """
        schema = {}

        # Add bar paths
        for meter in bars.meters:
            schema[f"bar.{meter.name}"] = "float"

        # Add VFS paths from global profile
        if compiled_vfs_profiles and compiled_vfs_profiles.global_profile:
            for var in compiled_vfs_profiles.global_profile.variables:
                schema[f"vfs.{var.name}"] = var.type

        # Add item VFS paths from all item profiles
        if compiled_vfs_profiles and compiled_vfs_profiles.item_profiles:
            for profile_name, profile in compiled_vfs_profiles.item_profiles.items():
                for var in profile.variables:
                    # Items use self.vfs.* and target.vfs.* paths in effects
                    # Profile name is implicit (instance determines profile at runtime)
                    schema[f"self.vfs.{var.name}"] = var.type
                    schema[f"target.vfs.{var.name}"] = var.type

        # TODO: Add agent profile paths (Task 2)

        return schema

    def _extract_vfs_observation_marks(self, variables: tuple[VariableDef, ...]) -> dict[str, set[str]]:
        """Extract which VFS variables are marked for observation.

        Args:
            variables: VFS variables from variables_reference.yaml

        Returns:
            Dict mapping scope to set of observed variable names
            Example: {"global": {"day_count"}, "agent": {"motivation"}}
        """
        marks: dict[str, set[str]] = {
            "global": set(),
            "agent": set(),
            "item": set(),
        }

        for var in variables:
            # Variables with observable=True are included in observations
            if var.observable:
                if isinstance(var.scope, VariableScope):
                    scope_key = var.scope.value
                else:
                    scope_key = str(var.scope)

                # Map VariableScope to mark keys
                if scope_key == "global":
                    marks["global"].add(var.id)
                elif scope_key in ("agent", "agent_private"):
                    marks["agent"].add(var.id)
                # TODO: Handle item-scoped variables (Task 3)

        # Remove empty scopes
        return {k: v for k, v in marks.items() if v}

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
            levels_dict: Dict of {level_name: (curriculum, bars, affordances, training)}

        Raises:
            ValueError: If any level has different meter or affordance vocabulary
        """
        # Get canonical vocabulary from environment.yaml
        env_meters = set(m.name for m in environment.environment.meters)
        env_affordances = set(a.name for a in environment.environment.affordances)

        # Validate each curriculum level
        for level_name, (curriculum, bars, affordances, training) in levels_dict.items():
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
        experiment_dir = Path(experiment_dir).resolve()
        self.config_pack_path = experiment_dir

        self._validate_config_dir(experiment_dir)

        # Stage 0: scoping preflight (no YAML parsing yet)
        self._validate_scoping(experiment_dir)

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
                    config_hash = self._compute_config_hash(experiment_dir)
                    config_mtime = self._compute_config_mtime(experiment_dir)

                    cached = CompiledUniverse.load_from_cache(cache_path)
                    cached_meta = cached.metadata

                    # Treat missing fingerprint fields as stale cache
                    if cached_meta.config_hash and cached_meta.config_mtime:
                        if cached_meta.config_hash == config_hash and cached_meta.config_mtime >= config_mtime:
                            logger.info("Loading compiled universe from cache: %s", cache_path)
                            return cached
                        logger.info(
                            "Cache stale for %s (hash/mtime mismatch); recompiling.",
                            experiment_dir,
                        )
                    else:
                        logger.info("Cached universe at %s missing fingerprint fields; recompiling.", cache_path)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to load cached universe from %s: %s", cache_path, exc)

        # Stage 0: YAML syntax validation (lightweight)
        self._phase_0_validate_yaml_syntax(experiment_dir)

        # Stage 1: load v2.1 configs
        self._log_stage(1, "Parse v2.1 configs")
        raw = self._stage_1_load_v21_configs(experiment_dir)

        # Stage 2: symbol table
        self._log_stage(2, "Build symbol table")
        symbol_table = self._stage_2_build_symbol_table(raw)

        # Stage 3: resolve references
        self._log_stage(3, "Resolve references")
        self._stage_3_resolve_references(raw, symbol_table, experiment_dir)

        # Stage 4: cross-validate semantics
        self._log_stage(4, "Cross-validate semantics")
        self._validate_v21_semantics(raw, experiment_dir)
        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"

        # Select primary level
        if primary_level is None:
            primary_level = sorted(raw.levels.keys())[0]
            logger.info("No primary_level specified; defaulting to %s", primary_level)
        if primary_level not in raw.levels:
            raise ValueError(f"Primary level '{primary_level}' not found. Available: {list(raw.levels.keys())}")

        # Stage 5: shared artifact enrichment
        self._log_stage(5, "Enrich shared schemas and effects")
        (
            _bar_schema,
            compiled_vfs_profiles,
            _effects_schema,
            compiled_effect_catalog,
        ) = self._stage_5_prepare_shared_artifacts(
            raw,
            experiment_dir,
            primary_level=primary_level,
            temporal_supported=temporal_supported,
        )

        # Stage 6: level compilation + optimization
        self._log_stage(6, "Compile levels and optimization data")
        (
            all_levels,
            primary_meta,
            universe_metadata,
            vfs_expression_schema,
            vfs_observation_marks,
        ) = self._stage_6_compile_levels(
            raw,
            experiment_dir,
            primary_level=primary_level,
            compiled_vfs_profiles=compiled_vfs_profiles,
            compiled_effect_catalog=compiled_effect_catalog,
            config_hash=config_hash,
            config_mtime=config_mtime,
            temporal_supported=temporal_supported,
        )

        # Stage 7: emit artifact + cache
        self._log_stage(7, "Emit compiled universe")
        effect_observation_slots = EFFECT_OBSERVATION_SLOTS if compiled_effect_catalog and compiled_effect_catalog.effects else 0
        compiled = self._stage_7_emit_artifact(
            raw,
            experiment_dir,
            cache_path,
            use_cache,
            universe_metadata,
            primary_meta,
            all_levels,
            compiled_vfs_profiles,
            compiled_effect_catalog,
            vfs_expression_schema,
            vfs_observation_marks,
            effect_observation_slots,
        )
        return compiled

    def _validate_scoping(self, experiment_dir: Path) -> None:
        """Enforce experiment-vs-level scoping for shared catalogs (effects/VFS/items)."""
        from townlet.universe.errors import CompilationErrorCollector

        errors = CompilationErrorCollector(stage="Stage 0: Scoping Validation")
        # Shared catalogs required at experiment root (effects remain optional)
        required_experiment_files: list[str] = ["vfs_profiles.yaml", "items.yaml"]
        forbidden_level_files = ["vfs_profiles.yaml", "effects.yaml"]

        for filename in required_experiment_files:
            root_path = experiment_dir / filename
            if not root_path.exists():
                errors.add(
                    f"Missing required experiment-level file: {filename}",
                    code="SCOPING_MISSING_EXPERIMENT_FILE",
                    location=str(root_path),
                )

        levels_root = experiment_dir / "levels"
        if levels_root.exists():
            for level_dir in sorted(levels_root.iterdir()):
                if not level_dir.is_dir():
                    continue
                for forbidden in forbidden_level_files:
                    forbidden_path = level_dir / forbidden
                    if forbidden_path.exists():
                        errors.add(
                            f"Found {forbidden} at level scope ({forbidden_path}). " "This file must live at the experiment root only.",
                            code="SCOPING_FORBIDDEN_LEVEL_FILE",
                            location=str(forbidden_path),
                        )
                # Allow level items.yaml only when using the ItemsAppearance (v1.0) schema
                level_items = level_dir / "items.yaml"
                if level_items.exists():
                    level_version: str | None = None
                    try:
                        with level_items.open() as handle:
                            data = yaml.safe_load(handle) or {}
                        if isinstance(data, dict):
                            level_version = data.get("version")
                    except yaml.YAMLError:
                        level_version = None

                    if level_version != "1.0":
                        errors.add(
                            f"Found items.yaml at level scope ({level_items}). "
                            "Level item spawns must use the v1.0 ItemsAppearance schema; "
                            "shared item catalogs belong at the experiment root.",
                            code="SCOPING_FORBIDDEN_LEVEL_FILE",
                            location=str(level_items),
                        )

        errors.check_and_raise()

    def _validate_config_dir(self, config_dir: Path) -> None:
        """Validate config_dir for security and sanity.

        Ensures:
        - Path is a directory
        - Path doesn't contain suspicious traversal patterns
        - Path exists

        Raises:
            CompilationError: If validation fails
        """
        if not config_dir.exists():
            raise CompilationError(
                stage="Config Directory Validation",
                errors=[f"Config directory does not exist: {config_dir}"],
            )

        if not config_dir.is_dir():
            raise CompilationError(
                stage="Config Directory Validation",
                errors=[f"Config path is not a directory: {config_dir}"],
            )

        # Warn about suspicious patterns (though resolve() already normalized them)
        path_str = str(config_dir)
        if ".." in path_str:
            logger.warning(
                "Config directory path contains '..' after resolution: %s. This may indicate a path traversal attempt.",
                config_dir,
            )

    def _phase_0_validate_yaml_syntax(self, config_dir: Path) -> None:
        """Phase 0 – validate all YAML files can be parsed before compilation begins."""
        errors = CompilationErrorCollector(stage="Phase 0: YAML Syntax Validation")

        shared_files = [
            "experiment.yaml",
            "stratum.yaml",
            "environment.yaml",
            "actions.yaml",
            "agent.yaml",
        ]

        for file_name in shared_files:
            file_path = config_dir / file_name
            if not file_path.exists():
                errors.add(f"{file_name}: File not found", code="MISSING_FILE", location=str(file_path))
                continue
            try:
                with file_path.open() as handle:
                    yaml.safe_load(handle)
            except yaml.YAMLError as exc:
                errors.add(str(exc), code="YAML_SYNTAX_ERROR", location=str(file_path))

        levels_dir = config_dir / "levels"
        if not levels_dir.exists():
            errors.add("levels/ directory missing", code="MISSING_LEVELS_DIR", location=str(levels_dir))
        else:
            for level_dir in sorted(p for p in levels_dir.iterdir() if p.is_dir()):
                for file_name in ("curriculum.yaml", "bars.yaml", "affordances.yaml", "training.yaml"):
                    file_path = level_dir / file_name
                    if not file_path.exists():
                        errors.add(
                            f"{file_name}: File not found",
                            code="MISSING_FILE",
                            location=str(file_path),
                        )
                        continue
                    try:
                        with file_path.open() as handle:
                            yaml.safe_load(handle)
                    except yaml.YAMLError as exc:
                        errors.add(str(exc), code="YAML_SYNTAX_ERROR", location=str(file_path))

        if errors.errors:
            errors.add_hint("Check YAML indentation (use spaces, not tabs)")
            errors.add_hint("Ensure lists use proper '- item' syntax")
            errors.add_hint("Validate YAML syntax at yamllint.com or with 'yamllint <file>'")
            errors.check_and_raise()

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
                            f"Found {forbidden} at level scope ({forbidden_path}). " "This file must live at the experiment root only.",
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
        grid_capacity: int | None = None
        grid_config = getattr(substrate, "grid", None)
        if getattr(substrate, "type", None) == "grid" and grid_config is not None:
            width = grid_config.width
            height = grid_config.height
            depth = getattr(grid_config, "depth", None)
            grid_capacity = width * height if depth is None else width * height * depth
        gridnd_config = getattr(substrate, "gridnd", None)
        if getattr(substrate, "type", None) == "gridnd" and gridnd_config is not None:
            grid_capacity = 1
            for size in gridnd_config.dimension_sizes:
                grid_capacity *= size

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

        # 6) DAC must be present under agent.yaml (agent.drive) and non-empty, with valid references
        meters = env_meter_names
        affordances = env_affordance_names
        variables_set = (
            set(var.name for var in raw.environment.environment.variables) if hasattr(raw.environment.environment, "variables") else set()
        )

        agent_drive = getattr(raw.agent.agent, "drive", None)
        agent_path = experiment_dir / "agent.yaml"
        if agent_drive is None:
            errors.add("agent.drive is required and must not be empty.", code="AGENT_DRIVE_MISSING", location=str(agent_path))
        else:
            # Modifiers must exist and reference known bars/variables
            modifiers = getattr(agent_drive, "modifiers", {}) or {}
            if not modifiers:
                errors.add("agent.drive.modifiers must not be empty.", code="AGENT_DRIVE_MODIFIERS_EMPTY", location=str(agent_path))
            for mod_name, mod_cfg in modifiers.items():
                source = getattr(mod_cfg, "source", None)
                if source and source not in meters and source not in variables_set:
                    errors.add(
                        f"Modifier '{mod_name}' references unknown meter/variable: {source}",
                        code="AGENT_DRIVE_MODIFIER_INVALID_SOURCE",
                        location=str(agent_path),
                    )

            # Extrinsic bonuses
            extrinsic = getattr(agent_drive, "extrinsic", None)
            if extrinsic is None:
                errors.add("agent.drive.extrinsic is required.", code="AGENT_DRIVE_EXTRINSIC_MISSING", location=str(agent_path))
            else:
                for bonus in getattr(extrinsic, "bonuses", []) or []:
                    bar = getattr(bonus, "bar", None)
                    if bar and bar not in meters:
                        errors.add(
                            f"Extrinsic bonus references unknown bar: {bar}",
                            code="AGENT_DRIVE_EXTRINSIC_INVALID_BAR",
                            location=str(agent_path),
                        )

            # Intrinsic
            intrinsic = getattr(agent_drive, "intrinsic", None)
            if intrinsic is None:
                errors.add("agent.drive.intrinsic is required.", code="AGENT_DRIVE_INTRINSIC_MISSING", location=str(agent_path))

            # Shaping
            shaping = getattr(agent_drive, "shaping", None)
            if not shaping:
                errors.add("agent.drive.shaping must not be empty.", code="AGENT_DRIVE_SHAPING_EMPTY", location=str(agent_path))
            else:
                for idx, shape_cfg in enumerate(shaping):
                    loc = f"{agent_path}:drive.shaping[{idx}]"
                    # Handle known keys from reference-config (approach_reward, completion_bonus, etc.)
                    target = getattr(shape_cfg, "target", None) or getattr(shape_cfg, "affordance", None)
                    if target and target not in affordances:
                        errors.add(
                            f"Shaping entry references unknown affordance: {target}",
                            code="AGENT_DRIVE_SHAPING_INVALID_AFFORDANCE",
                            location=loc,
                        )
                    bar = getattr(shape_cfg, "bar", None)
                    if bar and bar not in meters:
                        errors.add(
                            f"Shaping entry references unknown bar: {bar}",
                            code="AGENT_DRIVE_SHAPING_INVALID_BAR",
                            location=loc,
                        )
                    money_bar = getattr(shape_cfg, "money_bar", None)
                    if money_bar and money_bar not in meters:
                        errors.add(
                            f"Shaping entry references unknown bar: {money_bar}",
                            code="AGENT_DRIVE_SHAPING_INVALID_BAR",
                            location=loc,
                        )
                    condition_bar = getattr(shape_cfg, "bar", None)
                    if condition_bar and condition_bar not in meters:
                        errors.add(
                            f"Shaping condition references unknown bar: {condition_bar}",
                            code="AGENT_DRIVE_SHAPING_INVALID_BAR",
                            location=loc,
                        )

        errors.check_and_raise()

    def _stage_1_load_v21_configs(self, experiment_dir: Path) -> RawConfigsV21:
        """Stage 1 – load v2.1 hierarchical configs."""
        return RawConfigsV21.from_experiment_dir(experiment_dir)

    def _stage_2_build_symbol_table(self, raw: RawConfigsV21) -> UniverseSymbolTable:
        """Stage 2 – collect all named entities into a symbol table."""
        errors = CompilationErrorCollector(stage="Stage 2: Symbol Table")
        table = UniverseSymbolTable()

        def _register(register_fn, payload) -> None:
            try:
                register_fn(payload)
            except CompilationError as exc:
                errors.extend(exc.issues)

        env = raw.environment.environment
        for meter in getattr(env, "meters", []) or []:
            _register(table.register_meter, meter)

        for cascade in getattr(env, "cascade_graph", []) or []:
            _register(table.register_cascade, cascade)

        for affordance in getattr(env, "affordances", []) or []:
            _register(table.register_affordance, affordance)

        for variable in getattr(env, "variables", []) or []:
            _register(table.register_variable, variable)

        for action in getattr(raw.actions.actions, "custom_actions", []) or []:
            _register(table.register_action, action)

        if raw.items is not None:
            for item in getattr(raw.items, "item_types", []) or []:
                _register(table.register_item, item)

        errors.check_and_raise(stage_label="Stage 2: Symbol Table")
        return table

    def _stage_3_resolve_references(
        self,
        raw: RawConfigsV21,
        symbol_table: UniverseSymbolTable,
        experiment_dir: Path,
    ) -> None:
        """Stage 3 – resolve and validate symbolic references."""
        errors = CompilationErrorCollector(stage="Stage 3: Reference Resolution")

        meter_names = set(symbol_table.meters.keys())
        affordance_names = set(symbol_table.affordances_by_name.keys())
        variable_ids = set(symbol_table.variables.keys())
        item_ids = set(symbol_table.items.keys())

        for level_name, level in raw.levels.items():
            level_dir = experiment_dir / "levels" / level_name

            # Cascades reference valid meters
            for cascade in getattr(level.bars, "cascades", []) or []:
                if cascade.source not in meter_names:
                    errors.add(
                        CompilationMessage(
                            code="UAC-RES-CASCADE",
                            message=f"Cascade references unknown source meter '{cascade.source}'.",
                            location=str(level_dir / "bars.yaml"),
                        )
                    )
                if cascade.target not in meter_names:
                    errors.add(
                        CompilationMessage(
                            code="UAC-RES-CASCADE",
                            message=f"Cascade references unknown target meter '{cascade.target}'.",
                            location=str(level_dir / "bars.yaml"),
                        )
                    )

            # Enabled affordances reference known affordance names
            enabled_affordances = getattr(level.training, "enabled_affordances", None)
            if enabled_affordances is not None:
                requested = {str(name) for name in enabled_affordances}
                unknown = requested - affordance_names
                if unknown:
                    errors.add(
                        CompilationMessage(
                            code="UAC-RES-AFF",
                            message=f"training.enabled_affordances contains unknown entries: {sorted(unknown)}",
                            location=str(level_dir / "training.yaml"),
                        )
                    )

            # Affordance costs and interaction references
            for affordance in getattr(level.affordances, "affordances", []) or []:
                invalid_costs = [meter for meter in affordance.costs.keys() if meter not in meter_names]
                if invalid_costs:
                    errors.add(
                        CompilationMessage(
                            code="UAC-RES-AFF",
                            message=f"Affordance '{affordance.name}' references unknown meters in costs: {sorted(invalid_costs)}",
                            location=str(level_dir / "affordances.yaml"),
                        )
                    )

                for stage_commands in (affordance.interactions or {}).values():
                    for cmd in stage_commands:
                        modify_target = getattr(cmd, "modify", None)
                        if isinstance(modify_target, str) and modify_target.startswith("target.bar."):
                            meter_name = modify_target.split(".")[-1]
                            if meter_name not in meter_names:
                                errors.add(
                                    CompilationMessage(
                                        code="UAC-RES-AFF",
                                        message=f"Affordance '{affordance.name}' interaction references unknown meter '{meter_name}'.",
                                        location=str(level_dir / "affordances.yaml"),
                                    )
                                )
                        if isinstance(modify_target, str):
                            vfs_prefixes = ("vfs.", "target.vfs.", "self.vfs.")
                            if modify_target.startswith(vfs_prefixes):
                                var_name = modify_target.split(".")[-1]
                                if var_name not in variable_ids:
                                    errors.add(
                                        CompilationMessage(
                                            code="UAC-RES-VFS",
                                            message=(f"Affordance '{affordance.name}' interaction uses unknown VFS variable '{var_name}'."),
                                            location=str(level_dir / "affordances.yaml"),
                                        )
                                    )

            # Item appearance rules reference known items
            if level.items_appearance is not None:
                for rule in level.items_appearance.items:
                    if rule.item_type not in item_ids:
                        errors.add(
                            CompilationMessage(
                                code="UAC-RES-ITEM",
                                message=f"Item appearance references unknown item_type '{rule.item_type}'.",
                                location=str(level_dir / "items.yaml"),
                            )
                        )

        # Agent drive references
        if getattr(raw.agent, "agent", None) and getattr(raw.agent.agent, "drive", None):
            # DriveConfig and DriveAsCodeConfig have identical structure
            from typing import cast

            drive_config = cast(DriveAsCodeConfig, raw.agent.agent.drive)
            self._validate_dac_references(drive_config, symbol_table, errors)

        errors.check_and_raise(stage_label="Stage 3: Reference Resolution")

    def _stage_5_prepare_shared_artifacts(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        *,
        primary_level: str,
        temporal_supported: bool,
    ) -> tuple[dict[str, str], CompiledVFSProfiles | None, dict[str, str], EffectCatalog | None]:
        """Stage 5 – build shared schemas (bars/VFS) and compile effects catalog."""
        primary_level_config = raw.levels[primary_level]
        bar_schema: dict[str, str] = {meter.name: "float" for meter in primary_level_config.bars.meters}

        compiled_vfs_profiles = self._compile_vfs_profiles(experiment_dir, bar_schema)
        self._validate_item_profile_bindings(raw.items, compiled_vfs_profiles)

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

        compiled_effect_catalog = self._compile_effects_catalog(
            experiment_dir,
            effects_schema,
            time_enabled=temporal_supported,
        )

        return bar_schema, compiled_vfs_profiles, effects_schema, compiled_effect_catalog

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
    ) -> tuple[
        dict[str, CompiledUniverse.LevelMetadata],
        CompiledUniverse.LevelMetadata,
        UniverseMetadata,
        dict[str, str],
        dict[str, set[str]] | None,
    ]:
        """Stage 6 – compile level metadata, optimization data, and derived schemas."""
        all_levels: dict[str, CompiledUniverse.LevelMetadata] = {}
        for level_name, level in raw.levels.items():
            logger.info("Compiling level: %s", level_name)
            obs_spec = self._build_observation_spec(
                raw.stratum,
                raw.environment,
                level.curriculum,
                compiled_vfs_profiles,
                raw.items,
                compiled_effect_catalog,
            )
            obs_activity = self._build_observation_activity(obs_spec)
            bar_schema = {meter.name: "float" for meter in level.bars.meters}
            action_metadata = self._build_action_space_metadata(
                raw.stratum,
                raw.actions,
                level.training,
                level.affordances,
                raw.items,
                self.config_pack_path,
            )
            meter_metadata = self._build_meter_metadata(raw.environment, level.bars)
            affordance_metadata = self._build_affordance_metadata(level.affordances)

            # Compile item spawn predicates (type-check and store AST on rules)
            self._compile_item_spawn_conditions(
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

            optimization_data = self._build_optimization_data(
                level.bars,
                level.affordances,
                meter_metadata,
                affordance_metadata,
                action_metadata,
                day_length=day_length,
            )
            if compiled_effect_catalog is not None:
                self._validate_trigger_cascade_ids(compiled_effect_catalog, optimization_data, level_name=level_name)
            vfs_fields = self._build_vfs_observation_fields(obs_spec, raw.environment)
            vfs_variables = self._build_vfs_variables(obs_spec, raw.environment)

            all_levels[level_name] = CompiledUniverse.LevelMetadata(
                level_name=level_name,
                bars=level.bars,
                affordances=level.affordances,
                curriculum=level.curriculum,
                training=level.training,
                observation_spec=obs_spec,
                observation_activity=obs_activity,
                action_metadata=action_metadata,
                meter_metadata=meter_metadata,
                affordance_metadata=affordance_metadata,
                optimization_data=optimization_data,
                vfs_observation_fields=vfs_fields,
                vfs_variables=vfs_variables,
                items_appearance=level.items_appearance,
            )

        primary_meta = all_levels[primary_level]
        primary_level_config = raw.levels[primary_level]

        universe_metadata = self._build_universe_metadata(
            raw,
            primary_meta,
            experiment_dir=experiment_dir,
            config_hash=config_hash,
            config_mtime=config_mtime,
        )

        vfs_expression_schema = self._build_vfs_expression_schema(primary_level_config.bars, compiled_vfs_profiles)

        variables_reference_path = experiment_dir / "variables_reference.yaml"
        vfs_observation_marks: dict[str, set[str]] | None = None
        if variables_reference_path.exists():
            from townlet.vfs.schema import load_variables_reference_config

            variables_from_yaml = tuple(load_variables_reference_config(experiment_dir))
            vfs_observation_marks = self._extract_vfs_observation_marks(variables_from_yaml)

        return all_levels, primary_meta, universe_metadata, vfs_expression_schema, vfs_observation_marks

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
            agent=raw.agent,
            items_catalog=raw.items,
            compiled_vfs_profiles=compiled_vfs_profiles,
            compiled_effect_catalog=compiled_effect_catalog,
            effect_observation_slots=effect_observation_slots,
            vfs_expression_schema=vfs_expression_schema,
            vfs_observation_marks=vfs_observation_marks,
            experiment_dir=experiment_dir,
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

        self._validate_drive_references_v21(raw, primary_meta, compiled)
        self._validate_economic_balance_v21(raw)
        return compiled

    # ------------------------------------------------------------------
    def _validate_item_profile_bindings(
        self,
        items_catalog: ItemsCatalogConfig | None,
        compiled_vfs_profiles: CompiledVFSProfiles | None,
    ) -> None:
        """Ensure every item vfs_profile exists in compiled VFS item profiles."""
        if items_catalog is None:
            return
        if compiled_vfs_profiles is None or not compiled_vfs_profiles.item_profiles:
            if any(item.vfs_profile for item in items_catalog.item_types):
                raise ValueError(
                    "Items catalog specifies vfs_profile entries, but no item_profiles were compiled from vfs_profiles.yaml. "
                    "Add item_profiles or remove vfs_profile references."
                )
            return

        available_profiles = set(compiled_vfs_profiles.item_profiles.keys())

        for item_def in items_catalog.item_types:
            if item_def.vfs_profile and item_def.vfs_profile not in available_profiles:
                close = difflib.get_close_matches(item_def.vfs_profile, available_profiles, n=1)
                suggestion = f" Did you mean '{close[0]}'?" if close else ""
                raise ValueError(
                    f"Item '{item_def.id}' references undefined vfs_profile '{item_def.vfs_profile}'. "
                    f"Available profiles: {sorted(available_profiles)}.{suggestion}"
                )

    def _build_spawn_condition_schema(
        self,
        *,
        bar_schema: dict[str, str],
        env_vars: list[Any],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> dict[str, str]:
        """Construct type schema for spawn condition expressions."""

        schema: dict[str, str] = {}

        for bar_name in bar_schema:
            schema[f"bar.{bar_name}"] = "float"

        for var in env_vars:
            vfs_type = "bool" if getattr(var, "type", None) == "bool" else "float"
            schema[f"vfs.{var.name}"] = vfs_type

        if compiled_vfs_profiles and compiled_vfs_profiles.global_profile:
            for var in compiled_vfs_profiles.global_profile.variables:
                vfs_type = "bool" if getattr(var, "type", None) == "bool" else "float"
                schema.setdefault(f"vfs.{var.name}", vfs_type)

        if temporal_supported:
            schema["temporal.tick"] = "int"

        return schema

    def _ast_uses_temporal(self, node: Any) -> bool:
        """Detect whether an AST references temporal.* paths."""

        from townlet.world.expression.ast_nodes import PathAccess

        if isinstance(node, PathAccess) and node.segments and node.segments[0] == "temporal":
            return True

        for attr in ("left", "right", "operand", "condition", "true_branch", "false_branch", "base", "index"):
            child = getattr(node, attr, None)
            if child is not None and self._ast_uses_temporal(child):
                return True

        if hasattr(node, "arguments") and node.arguments:
            for arg in node.arguments:
                if self._ast_uses_temporal(arg):
                    return True

        return False

    def _compile_item_spawn_conditions(
        self,
        items_appearance: Any | None,
        *,
        bar_schema: dict[str, str],
        env_vars: list[Any],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        temporal_supported: bool,
    ) -> None:
        """Parse and type-check spawn conditions, storing AST on each rule."""

        if items_appearance is None:
            return

        condition_schema = self._build_spawn_condition_schema(
            bar_schema=bar_schema,
            env_vars=env_vars,
            compiled_vfs_profiles=compiled_vfs_profiles,
            temporal_supported=temporal_supported,
        )

        parser = ExpressionParser()
        type_checker = TypeChecker(schema=condition_schema)

        for rule in items_appearance.items:
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

    # ------------------------------------------------------------------
    # v2.1 helpers
    # ------------------------------------------------------------------

    def _build_observation_activity(self, obs_spec: ObservationSpec) -> ObservationActivity:
        """Build ObservationActivity grouping dims by semantic_type and honoring masking.

        - active_mask: one bool per obs dim, False where description contains 'MASKED'
        - group_slices: contiguous slices per semantic_type (e.g., 'spatial', 'bars')
        - active_field_uuids: UUIDs for fields that are not masked
        """

        if not obs_spec.fields:
            return ObservationActivity(active_mask=(), group_slices={}, active_field_uuids=())

        active_mask_list: list[bool] = []
        active_uuids_list: list[str] = []

        group_boundaries: dict[str, int] = {}
        group_end_indices: dict[str, int] = {}
        current_idx = 0

        for field in obs_spec.fields:
            is_masked = "MASKED" in (field.description or "")
            dims = field.dims

            group_name = field.semantic_type or "custom"
            if group_name not in group_boundaries:
                group_boundaries[group_name] = current_idx

            # Expand mask and UUIDs
            for _ in range(dims):
                active_mask_list.append(not is_masked)
                if not is_masked:
                    active_uuids_list.append(field.uuid or "")

            current_idx += dims
            group_end_indices[group_name] = current_idx

        group_slices = {name: slice(group_boundaries[name], group_end_indices[name]) for name in group_boundaries.keys()}

        return ObservationActivity(
            active_mask=tuple(active_mask_list),
            group_slices=group_slices,
            active_field_uuids=tuple(active_uuids_list),
        )

    @staticmethod
    def _apply_observation_mode(
        fields: list[ObservationField],
        mode_cfg: ObservationModeConfig,
    ) -> list[ObservationField]:
        """Filter observation fields based on observation_mode selection."""

        if mode_cfg.mode == "full_auto":
            return fields

        if mode_cfg.mode == "max_compact":
            return [f for f in fields if "MASKED" not in (f.description or "")]

        if mode_cfg.mode == "full_manual":
            includes = mode_cfg.include_fields or []
            field_lookup = {field.name: field for field in fields}
            missing = [name for name in includes if name not in field_lookup]
            if missing:
                raise ValueError(
                    f"full_manual observation_mode requested unknown fields: {sorted(missing)}. "
                    "Check names against ObservationSpec fields."
                )
            if not includes:
                raise ValueError("full_manual observation_mode produced an empty field set; include_fields must match existing fields.")
            return [field_lookup[name] for name in includes]

        raise ValueError(f"Unsupported observation_mode '{mode_cfg.mode}'.")

    def _build_observation_spec(
        self,
        stratum: StratumConfig,
        environment: EnvConfigV21,
        curriculum: CurriculumConfig,
        compiled_vfs_profiles: CompiledVFSProfiles | None = None,
        items_catalog: ItemsCatalogConfig | None = None,
        compiled_effect_catalog: EffectCatalog | None = None,
    ) -> ObservationSpec:
        """Build observation spec using Support/Active pattern for v2.1."""

        fields: list[ObservationField] = []
        offset = 0

        substrate = stratum.stratum.substrate
        vision_support = stratum.stratum.vision_support  # canonical: global/partial/both/none
        temporal_support = stratum.stratum.temporal_support
        active_vision = curriculum.curriculum.active_vision
        vision_range = curriculum.curriculum.vision_range
        active_temporal = curriculum.curriculum.active_temporal

        # Normalize curriculum active vision: local → partial (POMDP)
        canon_active_vision = "partial" if active_vision in {"local", "partial"} else "global"

        # Compatibility validation: curriculum cannot request modes not supported by stratum
        if canon_active_vision == "global" and vision_support not in {"global", "both"}:
            raise ValueError(
                "Invalid vision configuration: curriculum.active_vision='global' but "
                f"stratum.vision_support='{vision_support}'. "
                "active_vision='global' requires vision_support to be 'global' or 'both'."
            )
        if canon_active_vision == "partial" and vision_support not in {"partial", "both"}:
            raise ValueError(
                "Invalid vision configuration: curriculum.active_vision indicates partial/local vision but "
                f"stratum.vision_support='{vision_support}'. "
                "Partial observability requires vision_support to be 'partial' or 'both'."
            )

        # Grid dimensions (for grid-based substrates)
        grid_width = grid_height = 0
        grid_cells = 0
        if substrate.type in {"grid", "grid3d"} and substrate.grid is not None:
            grid_width = substrate.grid.width
            grid_height = substrate.grid.height
            depth = getattr(substrate.grid, "depth", None)
            if depth is not None:
                grid_cells = grid_width * grid_height * depth
            else:
                grid_cells = grid_width * grid_height
        elif substrate.type == "gridnd" and substrate.gridnd is not None:
            grid_cells = 1
            for size in substrate.gridnd.dimension_sizes:
                grid_cells *= size

        # Vision: global
        if vision_support in {"both", "global"}:
            # Global vision only defined for grid substrates; gridnd uses flattened cells.
            if grid_cells:
                dims = grid_cells
                is_active = canon_active_vision == "global"
                if substrate.type == "gridnd":
                    desc = f"{dims}‑cell gridnd encoding" if is_active else "MASKED (local vision active)"
                elif grid_width and grid_height:
                    desc = f"{grid_width}x{grid_height} grid encoding" if is_active else "MASKED (local vision active)"
                else:
                    desc = "Global grid encoding" if is_active else "MASKED (local vision active)"
                fields.append(
                    ObservationField(
                        uuid=None,
                        name="obs_grid_encoding",
                        type="spatial_grid",
                        dims=dims,
                        start_index=offset,
                        end_index=offset + dims,
                        scope="agent",
                        description=desc,
                        semantic_type="spatial",
                    )
                )
                offset += dims

        # Vision: local / partial
        if vision_support in {"both", "partial"}:
            # Partial observability is only supported for low-dimensional grids.
            if substrate.type == "gridnd" and canon_active_vision == "partial":
                raise ValueError(
                    "Partial observability (local vision) is not supported for gridnd substrates. "
                    "Use active_vision='global' or vision_support='global'/'both' with grid substrates."
                )

            if substrate.type in {"grid", "grid3d"} and grid_width and grid_height:
                # Derive window size from normalized vision_range [0, 1] using the
                # v2.1 reference formula:
                #   radius = ceil(vision_range * (grid_size / 2))
                #   window_size = 2 * radius + 1
                # This keeps obs_dim stable across curricula while allowing intuitive
                # scaling with grid size.
                radius = max(1, int(math.ceil(vision_range * (grid_width / 2.0))))
                window_size = min((2 * radius) + 1, grid_width)

                # For grid substrates we always treat the local window as a 2D footprint.
                dims = window_size * window_size
                is_active = canon_active_vision == "partial"
                desc = f"{window_size}x{window_size} local window" if is_active else "MASKED (global vision active)"
                fields.append(
                    ObservationField(
                        uuid=None,
                        name="obs_local_window",
                        type="spatial_grid",
                        dims=dims,
                        start_index=offset,
                        end_index=offset + dims,
                        scope="agent",
                        description=desc,
                        semantic_type="spatial",
                    )
                )
                offset += dims

        # Position / velocity (all spatial substrates)
        #
        # Position dimensions depend on substrate type and observation encoding:
        # - Grid2D/Grid3D: 2D or 3D (fixed)
        # - GridND: N dimensions (N=4 to 100)
        # - Continuous/ContinuousND: N or 2N depending on observation_encoding
        #   - relative: N dims (normalized [0,1])
        #   - scaled: 2N dims (normalized + range sizes)
        #   - absolute: N dims (raw coordinates)
        # - Aspatial: 0 dims (no position)
        #
        # For continuous substrates, we build a temporary instance to query
        # get_observation_dim() for accurate dimensions based on encoding mode.

        position_dim = 0
        velocity_dim = 0  # May differ from position_dim for scaled encoding

        if substrate.type == "aspatial":
            # Aspatial substrates have no position
            position_dim = 0
            velocity_dim = 0

        elif substrate.type in {"grid", "grid3d"}:
            # Discrete grid substrates: position_dim = spatial dimensions
            if substrate.grid is not None:
                if substrate.grid.topology == "cubic":
                    position_dim = 3
                else:
                    position_dim = 2
            velocity_dim = position_dim  # Velocity matches position dims

        elif substrate.type == "gridnd":
            # High-dimensional discrete grids
            if substrate.gridnd is not None:
                position_dim = len(substrate.gridnd.dimension_sizes)
            velocity_dim = position_dim

        elif substrate.type in {"continuous", "continuousnd"}:
            # Continuous substrates: observation dims depend on encoding mode
            # Build temporary instance to query actual observation dimensions
            try:
                substrate_instance = SubstrateFactory.build(substrate, torch.device("cpu"))
                position_dim = substrate_instance.get_observation_dim()

                # Velocity always uses substrate's native dimensionality (not encoding)
                # e.g., 2D continuous with scaled encoding: position=4, velocity=2
                velocity_dim = substrate_instance.position_dim

            except Exception as exc:
                # Fallback: use position_dim from config (may be inaccurate for scaled)
                import warnings

                if substrate.type == "continuous" and substrate.continuous is not None:
                    position_dim = substrate.continuous.dimensions
                    velocity_dim = substrate.continuous.dimensions
                elif substrate.type == "continuousnd" and substrate.continuous is not None:
                    position_dim = len(substrate.continuous.bounds)
                    velocity_dim = len(substrate.continuous.bounds)

                warnings.warn(
                    f"Failed to build substrate instance for observation dim calculation: {exc}. "
                    f"Using fallback dims (may be inaccurate for scaled encoding).",
                    UserWarning,
                )

        # Add position observation field
        if position_dim:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_position",
                    type="vector",
                    dims=position_dim,
                    start_index=offset,
                    end_index=offset + position_dim,
                    scope="agent",
                    description=f"Agent position ({position_dim}D)",
                    semantic_type="spatial",
                )
            )
            offset += position_dim

        # Add velocity observation field (use velocity_dim, not position_dim)
        if velocity_dim:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_velocity",
                    type="vector",
                    dims=velocity_dim,
                    start_index=offset,
                    end_index=offset + velocity_dim,
                    scope="agent",
                    description=f"Agent velocity ({velocity_dim}D)",
                    semantic_type="spatial",
                )
            )
            offset += velocity_dim

        # Meters
        meter_count = len(environment.environment.meters)
        fields.append(
            ObservationField(
                uuid=None,
                name="obs_meters",
                type="vector",
                dims=meter_count,
                start_index=offset,
                end_index=offset + meter_count,
                scope="agent",
                description=f"{meter_count} meter values (normalized)",
                semantic_type="bars",
            )
        )
        offset += meter_count

        # Affordances: one-hot over full vocabulary + explicit "none" slot.
        affordance_count = len(environment.environment.affordances)
        affordance_dim = affordance_count + 1
        fields.append(
            ObservationField(
                uuid=None,
                name="obs_affordance_at_position",
                type="vector",
                dims=affordance_dim,
                start_index=offset,
                end_index=offset + affordance_dim,
                scope="agent",
                description=f"{affordance_dim}‑way one-hot affordance_at_position (including 'none')",
                semantic_type="affordance",
            )
        )
        offset += affordance_dim

        # Observable effects (fixed slots; filtered by observable flag)
        if compiled_effect_catalog is not None and compiled_effect_catalog.effects:
            effect_slots = EFFECT_OBSERVATION_SLOTS
            effect_dims = effect_slots * 3  # [effect_id, remaining_norm, active_flag]
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_effects",
                    type="vector",
                    dims=effect_dims,
                    start_index=offset,
                    end_index=offset + effect_dims,
                    scope="agent",
                    description=f"Observable effects (up to {effect_slots} slots)",
                    semantic_type="effects",
                )
            )
            offset += effect_dims

        # VFS variables (environment-declared)
        for var in environment.environment.variables:
            dims = getattr(var, "dims", 1)
            fields.append(
                ObservationField(
                    uuid=None,
                    name=var.name,
                    type="vector" if dims > 1 else "scalar",
                    dims=dims,
                    start_index=offset,
                    end_index=offset + dims,
                    scope=var.scope,
                    description=var.description,
                    semantic_type="custom",
                )
            )
            offset += dims

        # VFS observations (global + agent + item VFS)
        # Compute total VFS dimensions from VFS profiles (flatten tensors/vectors).
        vfs_dim = 0
        item_vfs_dim = 0

        def _var_flat_dim(var: Any) -> int:
            """Flattened observation width for a compiled VFS variable."""
            vtype = getattr(var, "type", None)
            if vtype in {"int", "float", "bool", "agent_ref", "item_ref", "affordance_ref", "effect_ref"}:
                return 1
            if vtype in {"vec2i", "vec2f"}:
                return 2
            if vtype in {"vec3i", "vec3f"}:
                return 3
            if vtype in {"vecNi", "vecNf"}:
                dims_val = getattr(var, "dims", None)
                if dims_val is None:
                    raise ValueError(f"Vector VFS variable '{getattr(var, 'name', '')}' is missing dims for obs_dim calculation.")
                return int(dims_val)
            if vtype in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
                shape = getattr(var, "shape", None)
                if not shape:
                    raise ValueError(f"Tensor VFS variable '{getattr(var, 'name', '')}' is missing shape for obs_dim calculation.")
                prod = 1
                for dim in shape:
                    prod *= dim
                return prod
            # Default: treat as scalar
            return 1

        if compiled_vfs_profiles is not None:
            if compiled_vfs_profiles.global_profile is not None:
                for compiled_var in compiled_vfs_profiles.global_profile.variables:
                    vfs_dim += _var_flat_dim(compiled_var)

            if compiled_vfs_profiles.agent_profile is not None:
                for compiled_var in getattr(compiled_vfs_profiles.agent_profile, "variables", []):
                    vfs_dim += _var_flat_dim(compiled_var)

            # Item VFS: max_items_per_agent × max(flat_dim across profiles)
            if compiled_vfs_profiles.item_profiles:
                item_profiles_dict = compiled_vfs_profiles.item_profiles
                if item_profiles_dict:
                    max_profile_dim = 0
                    for profile in item_profiles_dict.values():
                        profile_vars = getattr(profile, "variables", [])
                        profile_dim = 0
                        for item_profile_var in profile_vars:
                            profile_dim += _var_flat_dim(item_profile_var)
                        max_profile_dim = max(max_profile_dim, profile_dim)

                    max_items_per_agent: int | None = 3
                    if items_catalog is not None:
                        max_items_per_agent = items_catalog.max_items_per_agent
                    else:
                        max_items_per_agent = None

                    if max_items_per_agent is None:
                        raise ValueError(
                            "VFS observation includes item variables but no items catalog is configured. "
                            "Provide items.yaml with item profiles enabled or remove item VFS profiles."
                        )

                    item_vfs_dim = max_items_per_agent * max_profile_dim
                    vfs_dim += item_vfs_dim

        # Fail fast if item VFS dims are requested without an active item system
        if item_vfs_dim > 0 and items_catalog is None:
            raise ValueError(
                "Observation spec includes item VFS dimensions, but items are disabled (no items catalog). "
                "Enable items or remove item VFS profiles."
            )

        if vfs_dim > 0:
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_vfs",
                    type="vector",
                    dims=vfs_dim,
                    start_index=offset,
                    end_index=offset + vfs_dim,
                    scope="agent",
                    description=f"VFS observations (global + agent + item, {vfs_dim} dims)",
                    semantic_type="custom",
                )
            )
            offset += vfs_dim

        # Temporal fields
        if temporal_support == "enabled":
            # Rich temporal encoding: four dimensions
            #   [0] time_of_day_sin
            #   [1] time_of_day_cos
            #   [2] day_progress (0.0–1.0 over 24h)
            #   [3] is_night (0.0/1.0 indicator)
            # Masking is handled via curriculum (active_temporal).
            temporal_dims = 4
            desc = "Temporal features (sin, cos, day_progress, is_night)" if active_temporal else "MASKED (temporal inactive)"
            fields.append(
                ObservationField(
                    uuid=None,
                    name="obs_temporal",
                    type="vector",
                    dims=temporal_dims,
                    start_index=offset,
                    end_index=offset + temporal_dims,
                    scope="agent",
                    description=desc,
                    semantic_type="temporal",
                )
            )
            offset += temporal_dims

        mode_cfg: ObservationModeConfig = getattr(stratum.stratum, "observation_mode", ObservationModeConfig())
        filtered_fields = self._apply_observation_mode(fields, mode_cfg)

        # Re-index fields after filtering to keep contiguous start/end spans
        reindexed: list[ObservationField] = []
        offset = 0
        for field in filtered_fields:
            reindexed.append(
                ObservationField(
                    uuid=field.uuid,
                    name=field.name,
                    type=field.type,
                    dims=field.dims,
                    start_index=offset,
                    end_index=offset + field.dims,
                    scope=field.scope,
                    description=field.description,
                    semantic_type=field.semantic_type,
                    categorical_labels=field.categorical_labels,
                )
            )
            offset += field.dims

        return ObservationSpec.from_fields(fields=reindexed)

    def _build_action_space_metadata(
        self,
        stratum: StratumConfig,
        actions: ActionsConfig,
        training: TrainingV2Config,
        affordances: AffordancesV2Config,
        items: ItemsCatalogConfig | None,
        config_pack_path: Path,
    ) -> ActionSpaceMetadata:
        """Build action space metadata using substrate actions + custom actions."""
        entries: list[ActionMetadata] = []
        next_id = 0

        def _add(name: str, action_type: str, source: str, enabled: bool, movement_delta: tuple[float, ...] | None = None) -> None:
            nonlocal next_id
            entries.append(
                ActionMetadata(
                    id=next_id,
                    name=name,
                    type=action_type,  # type: ignore[arg-type]
                    enabled=enabled,
                    source=source,  # type: ignore[arg-type]
                    costs={},
                    description="",
                    movement_delta=movement_delta,
                )
            )
            next_id += 1

        substrate_actions_cfg = actions.actions.substrate_actions
        allow_interact = len(affordances.affordances) > 0
        substrate_actions: list[ActionConfig] = []
        substrate_names: set[str] = set()

        if substrate_actions_cfg.inherit:
            # Build substrate instance using validated stratum config to derive canonical actions.
            substrate = SubstrateFactory.build(stratum.stratum.substrate, torch.device("cpu"))
            substrate_actions = substrate.get_default_actions()
            substrate_names = {a.name for a in substrate_actions}
            for action in substrate_actions:
                enabled = True
                if action.name == "INTERACT" and not allow_interact:
                    enabled = False
                movement_delta: tuple[float, ...] | None = None
                if action.type == "movement" and action.delta is not None:
                    movement_delta = tuple(float(d) for d in action.delta)
                _add(action.name, action.type, "substrate", enabled, movement_delta=movement_delta)

        reserved_names: set[str] = {"INTERACT"}
        if items is not None:
            reserved_names.add("GET")
            for slot_idx in range(items.max_items_per_agent):
                reserved_names.add(f"USE_SLOT_{slot_idx}")
                reserved_names.add(f"DROP_SLOT_{slot_idx}")
            for item in items.item_types:
                for custom in item.interactions.local_commands:
                    reserved_names.add(build_item_command_action_name(item.id, custom.name, "local"))
                for custom in item.interactions.inventory_commands:
                    reserved_names.add(build_item_command_action_name(item.id, custom.name, "inventory"))

        enabled_custom = set(training.enabled_actions.custom) if training.enabled_actions else set()
        for custom in actions.actions.custom_actions:
            if custom.name in reserved_names:
                raise ValueError(f"Action name '{custom.name}' is reserved for system actions and cannot be overridden")
            if custom.name in substrate_names:
                continue
            action_type = "passive" if custom.name == "WAIT" else "interaction"
            enabled = custom.enabled_by_default or custom.name in enabled_custom
            _add(custom.name, action_type, "custom", enabled)

        if items is not None:
            _add("GET", "interaction", "item", True)
            for slot_idx in range(items.max_items_per_agent):
                _add(f"USE_SLOT_{slot_idx}", "interaction", "item", True)
                _add(f"DROP_SLOT_{slot_idx}", "interaction", "item", True)
            for item in items.item_types:
                for custom in item.interactions.local_commands:
                    _add(
                        build_item_command_action_name(item.id, custom.name, "local"),
                        "interaction",
                        "item",
                        True,
                    )
                for custom in item.interactions.inventory_commands:
                    _add(
                        build_item_command_action_name(item.id, custom.name, "inventory"),
                        "interaction",
                        "item",
                        True,
                    )

        # Build action labels (compiler is the single source of truth)
        labels_path = config_pack_path / "action_labels.yaml"
        custom_labels: dict[int, str] | None = None
        if labels_path.exists():
            import yaml

            data = yaml.safe_load(labels_path.read_text()) or {}
            raw_custom = data.get("custom")
            if isinstance(raw_custom, dict):
                custom_labels = {int(k): str(v) for k, v in raw_custom.items()}

        label_config = actions.actions.labels
        label_preset = label_config.preset
        action_labels = get_labels(
            preset=label_preset if custom_labels is None else None,
            custom_labels=custom_labels,
            substrate_position_dim=self._infer_position_dim(stratum.stratum.substrate),
        )

        return ActionSpaceMetadata(
            total_actions=len(entries),
            actions=tuple(entries),
            labels=action_labels.get_all_labels(),
            label_description=action_labels.description,
            label_domain=action_labels.domain,
        )

    def _build_meter_metadata(
        self,
        environment: EnvConfigV21,
        bars: BarsV2Config,
    ) -> MeterMetadata:
        """Meters: use environment vocabulary, initial from bars."""
        meter_lookup = {meter.name: meter for meter in bars.meters}
        meter_infos: list[MeterInfo] = []
        for idx, meter in enumerate(environment.environment.meters):
            bar_cfg = meter_lookup.get(meter.name)
            initial = bar_cfg.initial if bar_cfg else 0.0
            meter_infos.append(
                MeterInfo(
                    name=meter.name,
                    index=idx,
                    critical=False,
                    initial_value=initial,
                    observable=True,
                    description=meter.description,
                )
            )
        return MeterMetadata(meters=tuple(meter_infos))

    def _build_affordance_metadata(self, affordances: AffordancesV2Config) -> AffordanceMetadata:
        """Affordance metadata derived from per-level affordances.yaml."""
        infos: list[AffordanceInfo] = []
        for aff in affordances.affordances:
            # Extract effects from interactions (on_start stage for metadata)
            # This is for visualization/UI purposes - the actual Effects execution uses compiled commands
            effects_dict = {}
            if aff.interactions and "on_start" in aff.interactions:
                for cmd in aff.interactions["on_start"]:
                    modify = getattr(cmd, "modify", None)
                    if isinstance(modify, str) and modify.startswith("target.bar."):
                        meter_name = modify.split(".")[-1]
                        # Simple extraction - just parse basic addition (e.g., "target.bar.energy + 0.5")
                        # This is best-effort for metadata; actual execution uses compiled Effects
                        value_field = getattr(cmd, "value", None)
                        if isinstance(value_field, str) and "+" in value_field:
                            try:
                                value_part = value_field.split("+")[-1].strip()
                                effects_dict[meter_name] = float(value_part)
                            except (ValueError, IndexError):
                                pass  # Skip if not a simple addition

            infos.append(
                AffordanceInfo(
                    id=aff.name,
                    name=aff.name,
                    enabled=True,
                    effects=effects_dict,
                    cost=float(aff.costs.get("money", 0.0)) if hasattr(aff, "costs") else 0.0,
                    category=None,
                    description="",
                    position=None,
                )
            )
        return AffordanceMetadata(affordances=tuple(infos))

    def _build_optimization_data(
        self,
        bars: BarsV2Config,
        affordances: AffordancesV2Config,
        meter_metadata: MeterMetadata,
        affordance_metadata: AffordanceMetadata,
        action_metadata: ActionSpaceMetadata,
        *,
        day_length: int,
    ) -> OptimizationData:
        """Precompute tensors from v2.1 DTOs (depletions, cascades, modulations, temporal masks)."""
        meter_lookup = {m.name: m.index for m in meter_metadata.meters}
        base_depletions = torch.zeros(len(meter_metadata.meters), dtype=torch.float32)
        for bar in bars.meters:
            idx = meter_lookup.get(bar.name)
            if idx is not None:
                base_depletions[idx] = float(bar.depletion.passive)

        cascade_entries: list[dict[str, Any]] = []
        cascade_by_id: dict[str, list[dict[str, Any]]] = {}
        for cascade in bars.cascades:
            source_idx = meter_lookup.get(cascade.source)
            target_idx = meter_lookup.get(cascade.target)
            if source_idx is None or target_idx is None:
                missing_source = cascade.source not in meter_lookup
                missing_target = cascade.target not in meter_lookup
                parts = ["Invalid cascade entry in bars.yaml."]
                if missing_source:
                    parts.append(f"  Unknown source meter: {cascade.source!r}")
                if missing_target:
                    parts.append(f"  Unknown target meter: {cascade.target!r}")
                parts.append("  Valid meters: " + ", ".join(sorted(meter_lookup.keys())))
                raise ValueError("\n".join(parts))
            entry = {
                "source_idx": source_idx,
                "target_idx": target_idx,
                "threshold": float(cascade.threshold),
                "strength": float(cascade.strength),
            }
            cascade_entries.append(entry)
            pair_id = f"{cascade.source}->{cascade.target}"
            cascade_by_id[pair_id] = cascade_by_id.get(pair_id, []) + [entry]

        modulation_entries: list[dict[str, Any]] = []
        for modulation in affordances.modulations:
            bar_idx = meter_lookup.get(modulation.bar)
            if bar_idx is None:
                raise ValueError(
                    "Invalid modulation entry in affordances.yaml.\n"
                    f"  Unknown bar: {modulation.bar!r}\n"
                    "  Valid meters: " + ", ".join(sorted(meter_lookup.keys()))
                )
            for aff_name in modulation.affordances:
                target_idx = next((i for i, a in enumerate(affordance_metadata.affordances) if a.name == aff_name), None)
                if target_idx is None:
                    valid_affordances = [a.name for a in affordance_metadata.affordances]
                    raise ValueError(
                        "Invalid modulation entry in affordances.yaml.\n"
                        f"  Unknown affordance in modulation.affordances: {aff_name!r}\n"
                        "  Valid affordances: " + ", ".join(sorted(valid_affordances))
                    )
                modulation_entries.append(
                    {
                        "bar_idx": bar_idx,
                        "affordance_idx": target_idx,
                        "threshold": float(modulation.threshold),
                        "min_multiplier": float(modulation.min_multiplier),
                    }
                )

        # Build action mask table [day_length, num_affordances] from per-affordance opening hours.
        # Rows correspond to discrete hours in the curriculum's day; columns align with
        # affordance indices in AffordanceMetadata. This is consumed by the runtime
        # via metadata.affordance_id_to_index and _is_affordance_open().
        num_hours = max(day_length, 1)
        num_affordances = len(affordance_metadata.affordances)
        action_mask_table = torch.ones((num_hours, num_affordances), dtype=torch.bool)

        # Build lookup from affordance name to its metadata index.
        affordance_index: dict[str, int] = {info.name: idx for idx, info in enumerate(affordance_metadata.affordances)}

        # For each affordance, compute its availability across the configured day_length.
        for aff_cfg in affordances.affordances:
            aff_idx = affordance_index.get(aff_cfg.name)
            if aff_idx is None:
                # Should not happen due to earlier vocabulary validation, but guard defensively.
                continue

            # Default: 24/7 availability when opening_hours.enabled is False.
            hours_enabled = torch.ones(num_hours, dtype=torch.bool)
            opening = aff_cfg.opening_hours
            if opening.enabled and opening.schedule:
                hours_enabled[:] = False
                for window in opening.schedule:
                    # Windows are expressed in 0-23 (start) and 1-28 (end, may exceed 24 for overnight).
                    start = int(window.start)
                    end = int(window.end)
                    for hour in range(start, end):
                        hours_enabled[hour % num_hours] = True

            # Apply affordance-specific availability to the corresponding column.
            action_mask_table[:, aff_idx] &= hours_enabled

        return OptimizationData(
            base_depletions=base_depletions,
            # v2.1: BarsV2Config does not classify cascades by tier; all
            # meter-to-meter cascades are exposed under a single category
            # consumed by MeterDynamics.apply_secondary_to_primary_effects.
            cascade_data={"primary_to_pivotal": cascade_entries, **cascade_by_id},
            modulation_data=modulation_entries,
            action_mask_table=action_mask_table,
            affordance_position_map={aff.name: None for aff in affordance_metadata.affordances},
        )

    def _validate_trigger_cascade_ids(
        self,
        compiled_effect_catalog: EffectCatalog,
        optimization_data: OptimizationData,
        *,
        level_name: str,
    ) -> None:
        """Ensure trigger_cascade commands reference cascades compiled for this level."""
        valid_ids = set(optimization_data.cascade_data.keys())
        if not valid_ids:
            for effect in compiled_effect_catalog.effects.values():
                for cmd in self._walk_commands(effect):
                    if cmd.type == CommandType.TRIGGER_CASCADE:
                        raise ValueError(
                            "trigger_cascade referenced but no cascades are defined in bars.yaml.\n"
                            f"  Level: {level_name}\n"
                            f"  Effect: {effect.id}\n"
                            "  Define cascades in bars.cascades before using trigger_cascade."
                        )
            return

        for effect in compiled_effect_catalog.effects.values():
            for cmd in self._walk_commands(effect):
                if cmd.type == CommandType.TRIGGER_CASCADE:
                    cascade_id = cmd.cascade_id
                    if not cascade_id or cascade_id not in valid_ids:
                        raise ValueError(
                            "trigger_cascade references unknown cascade_id.\n"
                            f"  Level: {level_name}\n"
                            f"  Effect: {effect.id}\n"
                            f"  cascade_id: {cascade_id!r}\n"
                            f"  Valid cascade ids: {sorted(valid_ids)}"
                        )

    @staticmethod
    def _walk_commands(effect: Any):
        """Yield all CommandNodes from a compiled effect (recursively)."""

        def walk(cmd):
            yield cmd
            if cmd.type == CommandType.IF:
                for child in cmd.then_commands or []:
                    yield from walk(child)
                for child in cmd.else_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.FOR_EACH:
                for child in cmd.body or cmd.do_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.SWITCH:
                for _, body in cmd.cases or []:
                    for child in body:
                        yield from walk(child)
                for child in cmd.default_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.REDUCE:
                # reduce has no nested commands; accumulator logic uses expressions only
                pass
            elif cmd.type == CommandType.PARALLEL:
                for child in cmd.parallel_commands or []:
                    yield from walk(child)
            elif cmd.type == CommandType.DELAY:
                for child in cmd.delay_commands or []:
                    yield from walk(child)

        pipelines = list(effect.on_spawn) + list(effect.on_tick) + list(effect.on_despawn) + list(getattr(effect, "on_interrupt", []) or [])
        for command in pipelines:
            yield from walk(command)

    def _build_vfs_observation_fields(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VFSObservationField, ...]:
        """Mirror ObservationSpec fields into VFS observation fields for runtime consumption."""

        def _convert_normalization(var_name: str, norm_cfg: Any) -> NormalizationSpec:
            """Map environment.yaml normalization into VFS NormalizationSpec."""
            if norm_cfg is None:
                raise ValueError(
                    "Missing normalization for variable declared in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Rule: All variables must declare normalization (clip/normalize/standardize); method 'none' is not allowed."
                )

            method = getattr(norm_cfg, "method", None)
            range_values = getattr(norm_cfg, "range", None)
            mean = getattr(norm_cfg, "mean", None)
            std = getattr(norm_cfg, "std", None)

            if method is None:
                raise ValueError(
                    "Normalization entry missing 'method' in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Provide method: clip | normalize | standardize."
                )

            if method == "none":
                raise ValueError(
                    "Normalization method 'none' is not permitted (no defaults). "
                    "Specify clip/normalize/standardize with explicit parameters.\n"
                    f"  Variable: {var_name}"
                )

            if method in {"clip", "normalize"}:
                if not range_values or len(range_values) != 2:
                    raise ValueError(
                        f"Normalization range must provide exactly two values [min, max].\n  Variable: {var_name}\n  Got: {range_values}"
                    )
                return NormalizationSpec(kind="minmax", min=range_values[0], max=range_values[1])
            if method == "standardize":
                if mean is None or std is None:
                    raise ValueError(
                        "Normalization method 'standardize' requires 'mean' and 'std' parameters in environment.yaml.\n"
                        f"  Variable: {var_name}\n"
                        "  Action: add mean/std fields to normalization or use clip/normalize with explicit ranges."
                    )
                return NormalizationSpec(kind="zscore", mean=mean, std=std)

            raise ValueError(f"Unsupported normalization method '{method}' for variable '{var_name}'. Use clip | normalize | standardize.")

        env_norm_by_name: dict[str, NormalizationSpec] = {}
        for var in environment.environment.variables:
            env_norm_by_name[var.name] = _convert_normalization(var.name, getattr(var, "normalization", None))

        fields: list[VFSObservationField] = []
        allowed_semantic = {"bars", "spatial", "affordance", "temporal", "custom"}
        for field in obs_spec.fields:
            norm = env_norm_by_name.get(field.name)
            semantic = field.semantic_type if field.semantic_type in allowed_semantic else "custom"
            fields.append(
                VFSObservationField(
                    id=field.name,
                    source_variable=field.name,
                    exposed_to=["agent"],
                    shape=[field.dims],
                    normalization=norm,
                    semantic_type=semantic,  # type: ignore[arg-type]  # semantic_type is Literal type
                    curriculum_active="MASKED" not in (field.description or ""),
                )
            )
        return tuple(fields)

    def _build_vfs_variables(self, obs_spec: ObservationSpec, environment: EnvConfigV21) -> tuple[VariableDef, ...]:
        """Build VFS variables from observation fields + environment variables.

        Creates VariableDefs for:
        1. System observation primitives (obs_position, obs_meters, etc.) from obs_spec
        2. User-defined variables from environment.environment.variables

        This ensures every VFSObservationField.source_variable has a backing VariableDef.
        """
        vars_out: list[VariableDef] = []

        def _convert_normalization(var_name: str, norm_cfg: Any) -> NormalizationSpec:
            """Map environment.yaml normalization into VFS NormalizationSpec."""
            if norm_cfg is None:
                raise ValueError(
                    "Missing normalization for variable declared in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Rule: All variables must declare normalization (clip/normalize/standardize); method 'none' is not allowed."
                )

            method = getattr(norm_cfg, "method", None)
            range_values = getattr(norm_cfg, "range", None)
            mean = getattr(norm_cfg, "mean", None)
            std = getattr(norm_cfg, "std", None)

            if method is None:
                raise ValueError(
                    "Normalization entry missing 'method' in environment.yaml.\n"
                    f"  Variable: {var_name}\n"
                    "  Provide method: clip | normalize | standardize."
                )

            if method == "none":
                raise ValueError(
                    "Normalization method 'none' is not permitted (no defaults). "
                    "Specify clip/normalize/standardize with explicit parameters.\n"
                    f"  Variable: {var_name}"
                )

            if method in {"clip", "normalize"}:
                if not range_values or len(range_values) != 2:
                    raise ValueError(
                        f"Normalization range must provide exactly two values [min, max].\n  Variable: {var_name}\n  Got: {range_values}"
                    )
                return NormalizationSpec(kind="minmax", min=range_values[0], max=range_values[1])
            if method == "standardize":
                if mean is None or std is None:
                    raise ValueError(
                        "Normalization method 'standardize' requires 'mean' and 'std' parameters in environment.yaml.\n"
                        f"  Variable: {var_name}\n"
                        "  Action: add mean/std fields to normalization or use clip/normalize with explicit ranges."
                    )
                return NormalizationSpec(kind="zscore", mean=mean, std=std)

            raise ValueError(f"Unsupported normalization method '{method}' for variable '{var_name}'. Use clip | normalize | standardize.")

        # Build lookup of user-defined variable names
        user_var_names = {var.name for var in environment.environment.variables}

        # System observation primitives (obs_position, obs_meters, obs_grid_encoding, etc.)
        # These are compiler-generated fields from obs_spec that need backing VariableDefs
        for field in obs_spec.fields:
            # Skip user-defined variables - they're handled below with full metadata from environment.yaml
            if field.name in user_var_names:
                continue

            # Create VariableDef for system primitives
            is_vector = field.dims > 1
            default = [0.0] * field.dims if is_vector else 0.0

            vars_out.append(
                VariableDef(
                    id=field.name,
                    scope="agent",  # All observation primitives are agent-scoped
                    type="vecNf" if is_vector else "scalar",
                    dims=field.dims if is_vector else None,
                    lifetime="tick",  # Refreshed every step
                    readable_by=["agent", "engine"],
                    writable_by=["engine"],  # Only engine writes observation primitives
                    default=default,
                    description=field.description or f"System observation primitive: {field.name}",
                    normalization=None,  # System primitives are pre-normalized by environment
                )
            )

        # User-defined variables (explicit declaration from environment.yaml)
        for var in environment.environment.variables:
            raw_dims = getattr(var, "dims", None)
            # Tensor support: expect shape metadata on var.shape when present
            shape = getattr(var, "shape", None)
            var_type = getattr(var, "type", None)

            is_tensor = var_type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}
            is_vector = bool(raw_dims and raw_dims > 1 and not is_tensor)

            dims = raw_dims if is_vector else None
            user_var_default: list[float] | float | None = 0.0
            if is_tensor:
                # For tensors, allow shape-backed default broadcasting; use zeros placeholder here.
                user_var_default = None
            elif is_vector and raw_dims is not None:
                user_var_default = [0.0] * raw_dims

            normalization = _convert_normalization(var.name, getattr(var, "normalization", None))

            # Determine final type for VariableDef
            # Use cast to narrow str to the Literal type expected by VariableDef
            from typing import Literal as LiteralType
            from typing import cast

            if var_type is None:
                final_type = cast(
                    LiteralType[
                        "scalar",
                        "vec2i",
                        "vec3i",
                        "vec2f",
                        "vec3f",
                        "vecNi",
                        "vecNf",
                        "bool",
                        "agent_ref",
                        "item_ref",
                        "tensor1d",
                        "tensor2d",
                        "tensor3d",
                        "tensorNd",
                    ],
                    "vecNf" if is_vector else "scalar",
                )
            elif is_tensor:
                final_type = cast(
                    LiteralType[
                        "scalar",
                        "vec2i",
                        "vec3i",
                        "vec2f",
                        "vec3f",
                        "vecNi",
                        "vecNf",
                        "bool",
                        "agent_ref",
                        "item_ref",
                        "tensor1d",
                        "tensor2d",
                        "tensor3d",
                        "tensorNd",
                    ],
                    var_type,
                )
            else:
                final_type = cast(
                    LiteralType[
                        "scalar",
                        "vec2i",
                        "vec3i",
                        "vec2f",
                        "vec3f",
                        "vecNi",
                        "vecNf",
                        "bool",
                        "agent_ref",
                        "item_ref",
                        "tensor1d",
                        "tensor2d",
                        "tensor3d",
                        "tensorNd",
                    ],
                    "vecNf" if is_vector else "scalar",
                )

            vars_out.append(
                VariableDef(
                    id=var.name,
                    scope=var.scope,
                    type=final_type,
                    dims=dims,
                    lifetime="tick",
                    readable_by=["agent", "engine"],
                    writable_by=["engine"],
                    default=user_var_default,
                    description=var.description,
                    normalization=normalization,
                    shape=shape,
                    initial_value_mode=getattr(var, "initial_value_mode", None),
                    initial_value_params=getattr(var, "initial_value_params", None),
                )
            )
        return tuple(vars_out)

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
        """
        drive = raw.agent.agent.drive

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

    def _build_universe_metadata(
        self,
        raw: RawConfigsV21,
        primary_meta: CompiledUniverse.LevelMetadata,
        *,
        experiment_dir: Path,
        config_hash: str | None = None,
        config_mtime: float | None = None,
    ) -> UniverseMetadata:
        """Construct UniverseMetadata summary."""
        meter_names = tuple(m.name for m in primary_meta.meter_metadata.meters)
        meter_name_to_index = {m.name: m.index for m in primary_meta.meter_metadata.meters}
        affordance_ids = tuple(a.id for a in primary_meta.affordance_metadata.affordances)
        affordance_id_to_index = {a.id: idx for idx, a in enumerate(primary_meta.affordance_metadata.affordances)}

        grid_size = None
        grid_cells = None
        position_dim = 0
        substrate_cfg = raw.stratum.stratum.substrate
        substrate_type = substrate_cfg.type
        if substrate_type in {"grid", "grid3d"} and substrate_cfg.grid is not None:
            width = substrate_cfg.grid.width
            height = substrate_cfg.grid.height
            grid_size = width
            depth = getattr(substrate_cfg.grid, "depth", None)
            if depth is not None:
                grid_cells = width * height * depth
                position_dim = 3
            else:
                grid_cells = width * height
                position_dim = 2
        elif substrate_type == "gridnd" and substrate_cfg.gridnd is not None:
            # GridND: product of all dimension sizes, position dim = number of axes
            grid_cells = 1
            for size in substrate_cfg.gridnd.dimension_sizes:
                grid_cells *= size
            position_dim = len(substrate_cfg.gridnd.dimension_sizes)

            # Temporal metadata: require explicit ticks_per_day when temporal support is enabled.
            ticks_per_day: int | None = None
        curriculum_day_length = primary_meta.curriculum.curriculum.day_length
        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"
        temporal_active = primary_meta.curriculum.curriculum.active_temporal
        if temporal_supported and temporal_active:
            if curriculum_day_length is None or curriculum_day_length <= 0:
                raise ValueError(
                    "Missing curriculum.day_length for temporal-enabled stratum.\n"
                    f"  Experiment: {experiment_dir}\n"
                    f"  Level: {primary_meta.level_name}\n"
                    "Provide an explicit positive day_length; no defaults are applied."
                )
            ticks_per_day = curriculum_day_length
        else:
            # Temporal support disabled; mark as zero ticks per day (no temporal mechanics).
            ticks_per_day = 0

        # Compute fingerprint if not provided by caller.
        if config_hash is None:
            config_hash = self._compute_config_hash(experiment_dir)
        if config_mtime is None:
            config_mtime = self._compute_config_mtime(experiment_dir)

        # v2.1: experiment.version is mandatory (no legacy fallback)
        try:
            config_version = raw.experiment.experiment.version
        except AttributeError as exc:
            raise ValueError(
                "experiment.version is required in experiment.yaml (no defaults allowed). Provide an explicit semantic version string."
            ) from exc
        if not config_version:
            raise ValueError("experiment.version is required in experiment.yaml and cannot be empty.")

        return UniverseMetadata(
            universe_name=raw.experiment.experiment.metadata.name,
            schema_version=SCHEMA_VERSION,
            substrate_type=substrate_type,
            position_dim=position_dim,
            meter_count=len(meter_names),
            meter_names=meter_names,
            meter_name_to_index=meter_name_to_index,
            affordance_count=len(affordance_ids),
            affordance_ids=affordance_ids,
            affordance_id_to_index=affordance_id_to_index,
            action_count=primary_meta.action_metadata.total_actions,
            observation_dim=primary_meta.observation_spec.total_dims,
            grid_size=grid_size,
            grid_cells=grid_cells,
            max_sustainable_income=0.0,
            total_affordance_costs=0.0,
            economic_balance=0.0,
            ticks_per_day=ticks_per_day,
            config_version=config_version,
            compiler_version=COMPILER_VERSION,
            compiled_at=datetime.now(UTC).isoformat(),
            config_hash=config_hash,
            config_mtime=config_mtime,
            provenance_id=str(experiment_dir),
            compiler_git_sha="",
            python_version=sys.version.split()[0],
            torch_version=torch.__version__,
            pydantic_version="",
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

    def _stage_4_cross_validate(
        self,
        raw_configs: Any,
        symbol_table: UniverseSymbolTable,
        errors: CompilationErrorCollector,
    ) -> None:
        """Stage 4 – enforce cross-config semantic constraints (subset of spec for TASK-004A)."""

        raise RuntimeError("Legacy flat config pipeline removed; use v2.1 hierarchical configs.")

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

        v2.1 semantics: availability is defined *only* via opening_hours on
        curriculum-level affordances (AffordanceParamConfig from AffordancesV2Config).
        Legacy operating_hours fields are no longer supported.
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
        """Extract meter name from Effects command or legacy effect entry."""
        if entry is None:
            return None
        if isinstance(entry, dict):
            # Effects command: extract from "modify" field
            if "modify" in entry:
                modify = entry["modify"]
                if isinstance(modify, str) and modify.startswith("target.bar."):
                    return modify.split(".")[-1]
                return None
            # Legacy effect entry
            return entry.get("meter")
        return getattr(entry, "meter", None)

    def _get_amount(self, entry: object | None) -> float | None:
        """Extract meter delta from Effects command or legacy effect entry."""
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
            return None

        # Legacy effect entry
        value = entry.get("amount") if isinstance(entry, dict) else getattr(entry, "amount", None)
        if isinstance(value, int | float):
            return float(value)
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

    def _stage_5_compute_metadata(
        self,
        config_dir: Path,
        raw_configs: Any,
        symbol_table: UniverseSymbolTable,
        *,
        precomputed_config_hash: str | None = None,
    ) -> tuple[UniverseMetadata, ObservationSpec, tuple[VFSObservationField, ...]]:
        """Stage 5 – compute derived metadata and observation specification."""

        raise RuntimeError("Legacy flat config pipeline removed; use v2.1 hierarchical configs.")

    def _stage_5_build_rich_metadata(
        self,
        raw_configs: Any,
    ) -> tuple[ActionSpaceMetadata, MeterMetadata, AffordanceMetadata]:
        """Stage 5 – build training-facing metadata structures."""

        raise RuntimeError("Legacy flat config pipeline removed; use v2.1 hierarchical configs.")

    def _stage_6_optimize(
        self,
        raw_configs: Any,
        metadata: UniverseMetadata,
        *,
        device: torch.device | None = None,
    ) -> OptimizationData:
        """Stage 6 – pre-compute optimization tensors and lookup tables."""

        torch_device = device or torch.device("cpu")
        meter_lookup = metadata.meter_name_to_index

        base_depletions = torch.zeros(metadata.meter_count, dtype=torch.float32, device=torch_device)
        for bar in raw_configs.bars:
            index = meter_lookup.get(bar.name, bar.index)
            base_depletions[index] = float(getattr(bar, "base_depletion", 0.0))

        cascade_data: dict[str, list[dict[str, float]]] = defaultdict(list)
        cascade_by_id: dict[str, list[dict[str, float]]] = defaultdict(list)
        for cascade in raw_configs.cascades:
            source_idx = meter_lookup.get(cascade.source)
            target_idx = meter_lookup.get(cascade.target)
            if source_idx is None or target_idx is None:
                continue
            category_key = cascade.category or "uncategorized"
            entry = {
                "source_idx": source_idx,
                "target_idx": target_idx,
                "threshold": cascade.threshold,
                "strength": cascade.strength,
            }
            cascade_data[category_key].append(entry)
            pair_id = f"{cascade.source}->{cascade.target}"
            cascade_by_id[pair_id].append(entry)

        for category, entries in cascade_data.items():
            entries.sort(key=lambda entry: entry["target_idx"])

        modulation_data: list[dict[str, float]] = []

        affordance_count = metadata.affordance_count
        action_mask_table = torch.zeros((24, affordance_count), dtype=torch.bool, device=torch_device)

        if affordance_count > 0:
            for hour in range(24):
                for affordance_idx, affordance in enumerate(raw_configs.affordances):
                    # operating_hours is now required by schema - no None check needed
                    # Convert list[int] to tuple[int, int] for is_affordance_open
                    # Pydantic ensures exactly 2 elements (Field(min_length=2, max_length=2))
                    open_hour, close_hour = affordance.operating_hours
                    action_mask_table[hour, affordance_idx] = is_affordance_open(hour, (open_hour, close_hour))

        affordance_position_map = {
            aff.id: self._tensorize_affordance_position(getattr(aff, "position", None), torch_device) for aff in raw_configs.affordances
        }

        cascade_payload = dict(cascade_data)
        cascade_payload.update(cascade_by_id)

        return OptimizationData(
            base_depletions=base_depletions,
            cascade_data=cascade_payload,
            modulation_data=modulation_data,
            action_mask_table=action_mask_table,
            affordance_position_map=affordance_position_map,
        )

    def _derive_grid_dimensions(self, substrate: SubstrateConfig) -> tuple[int | None, int | None]:
        """Calculate grid dimensions for metadata.

        Returns:
            (grid_size, grid_cells): For square grids, grid_size=width.
                                     For non-square or non-grid substrates, returns (None, None).
        """
        if substrate.type == "grid" and substrate.grid is not None:
            width = substrate.grid.width
            height = substrate.grid.height

            # Handle 3D grids
            depth = getattr(substrate.grid, "depth", None)
            if depth is not None:
                # For 3D, grid_size is ambiguous (use width as representative)
                grid_cells = width * height * depth
                return width, grid_cells

            # 2D grid
            grid_cells = width * height

            # Only return grid_size if square (for backward compatibility)
            if width == height:
                return width, grid_cells
            else:
                # Non-square grids: grid_size concept doesn't apply
                return None, grid_cells

        # Continuous, aspatial, gridnd: no grid_size concept
        return None, None

    def _label_substrate_type(self, substrate: SubstrateConfig) -> str:
        if substrate.type != "grid":
            return substrate.type
        if substrate.grid is None:
            return "grid"
        return f"grid_{substrate.grid.topology}"

    def _infer_position_dim(self, substrate: SubstrateConfig) -> int:
        if substrate.type == "aspatial":
            return 0
        if substrate.type == "grid":
            if substrate.grid and substrate.grid.topology == "cubic":
                return 3
            return 2
        if substrate.type == "gridnd" and substrate.gridnd is not None:
            return len(substrate.gridnd.dimension_sizes)
        if substrate.type == "continuous" and substrate.continuous is not None:
            return substrate.continuous.dimensions
        if substrate.type == "continuousnd" and substrate.continuous is not None:
            return len(substrate.continuous.bounds)
        return 0

    def _auto_generate_standard_exposures(self, symbol_table: UniverseSymbolTable) -> list[dict[str, Any]]:
        """Auto-generate standard observation exposures for all system variables.

        Creates exposures for:
        - Spatial variables (grid_encoding/local_window, position)
        - All meters
        - Affordance encoding
        - Temporal variables

        Returns:
            List of exposure dictionaries matching the expected schema
        """
        exposures: list[dict[str, Any]] = []

        # Get all variables from symbol table
        for var_id, var in symbol_table.variables.items():
            # Determine observation shape
            if var.type == "scalar":
                shape: list[int] = []
            elif var.type == "vecNf" and var.dims:
                shape = [var.dims]
            else:
                continue  # Skip unsupported types

            # Create exposure with obs_ prefix
            exposures.append(
                {
                    "id": f"obs_{var_id}",
                    "source_variable": var_id,
                    "exposed_to": ["agent"],
                    "shape": shape,
                }
            )

        return exposures

    def _load_observation_exposures(self, raw_configs: Any, symbol_table: UniverseSymbolTable) -> list[dict[str, Any]]:
        """Legacy observation exposure generator."""
        raise RuntimeError("Legacy flat config pipeline removed; use v2.1 hierarchical configs.")

        # Auto-generate exposures for ALL variables (standard system + custom computed)
        exposures = self._auto_generate_standard_exposures(symbol_table)

        # Mark spatial observation fields with curriculum_active based on partial_observability
        # This creates a superset observation contract where obs_dim stays constant across levels
        # Also set semantic_type for proper group_slices organization
        partial_obs = raw_configs.environment.partial_observability

        # Get meter names for semantic_type inference
        meter_names = {bar.name for bar in raw_configs.bars}

        for exposure in exposures:
            source_var = exposure.get("source_variable")

            if source_var == "grid_encoding":
                # grid_encoding active in full obs, inactive in partial obs
                exposure["curriculum_active"] = not partial_obs
                exposure["semantic_type"] = "spatial"  # BUG-43: Mark as spatial for group_slices
            elif source_var == "local_window":
                # local_window active in partial obs, inactive in full obs
                exposure["curriculum_active"] = partial_obs
                exposure["semantic_type"] = "spatial"  # BUG-43: Mark as spatial for group_slices
            else:
                # All other fields are always active
                exposure["curriculum_active"] = True

                # Infer semantic_type from source_variable name (same logic as _semantic_from_name)
                # Add None check to avoid AttributeError
                if source_var is not None:
                    if "position" in source_var.lower():
                        exposure["semantic_type"] = "spatial"
                    elif source_var in meter_names:
                        exposure["semantic_type"] = "bars"
                    elif "affordance" in source_var.lower():
                        exposure["semantic_type"] = "affordance"
                    elif "time" in source_var.lower() or "temporal" in source_var.lower() or "lifetime" in source_var.lower():
                        exposure["semantic_type"] = "temporal"
                    # else: default to "custom" (handled by ObservationField schema default)

        return exposures

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

        yaml_files.append(Path("configs") / "global_actions.yaml")

        digest = hashlib.sha256()
        for file_path in yaml_files:
            if not file_path.exists():
                continue
            normalized = self._normalize_yaml(file_path)
            digest.update(file_path.name.encode("utf-8"))
            digest.update(normalized.encode("utf-8"))
        return digest.hexdigest()

    def _compute_config_mtime(self, config_dir: Path) -> float:
        """Compute maximum modification time of all config files.

        Returns the latest mtime across all YAML files in the config directory
        and global_actions.yaml. This ensures cache is invalidated when ANY
        config file changes (including comment/whitespace-only changes).
        """
        yaml_files = sorted(config_dir.glob("*.yaml"))

        levels_dir = config_dir / "levels"
        if levels_dir.exists():
            yaml_files.extend(sorted(levels_dir.rglob("*.yaml")))

        yaml_files.append(Path("configs") / "global_actions.yaml")

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

        Note: This is for debugging/reproducibility only. Cache invalidation uses
        config_mtime + config_hash, NOT provenance_id, so dependency version changes
        don't trigger unnecessary recompilation. This is intentional - the compiler
        logic is version-stable, and dependency updates don't affect compiled output.
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
