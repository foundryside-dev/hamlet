"""UniverseCompiler implementation (Stage 1 scaffolding)."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Any

import torch
import yaml

from townlet.effects.catalog import EffectCatalog
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
from townlet.vfs.observation_builder import VFSObservationSpec
from townlet.vfs.profiles import CircularDependencyError
from townlet.vfs.schema_hashes import (
    compute_action_schema_hash,
    compute_observation_schema_hash,
    compute_transition_graph_hash,
    compute_variable_schema_hash,
    compute_vfs_hash,
)
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.vfs.vtc import (
    compile_vtc_action_writes_with_phase_graph,
    compile_vtc_affordance_gates_with_phase_graph,
    compile_vtc_interaction_progress_with_phase_graph,
    compile_vtc_modulations_with_phase_graph,
    compile_vtc_passive_depletions_with_phase_graph,
    compile_vtc_reward_components_with_phase_graph,
    compile_vtc_terminal_conditions_with_phase_graph,
    compile_vtc_threshold_cascades_with_phase_graph,
)
from townlet.world.expression.type_checker import TypeCheckError

from .compiled import CompiledVFSProfiles
from .compilers.actions import ActionCompiler
from .compilers.effects import EffectsCompiler
from .compilers.metadata import MetadataCompiler
from .compilers.observation import ObservationCompiler
from .compilers.optimization import OptimizationCompiler
from .compilers.vfs import VFSCompiler
from .cues_compiler import CuesCompiler
from .errors import CompilationError, CompilationMessage
from .loaders.preflight import validate_config_dir, validate_scoping, validate_yaml_syntax
from .loaders.v21 import load_v21_configs
from .pipeline import CompiledLevelBundle, SharedCompilerArtifacts
from .validation.limits import (
    EFFECT_OBSERVATION_SLOTS,
    MAX_CACHE_FILE_SIZE,
    validate_v21_limits,
)
from .validation.references import build_symbol_table, resolve_references
from .validation.semantics import select_primary_level, validate_v21_semantics

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

        # Stage 1b: enforce safety limits over loaded DTOs
        self._log_stage(2, "Enforce safety limits")
        validate_v21_limits(raw, experiment_dir)

        # Stage 1c: cross-validate semantics over loaded DTOs
        self._log_stage(3, "Cross-validate semantics")
        validate_v21_semantics(raw, experiment_dir)

        # Stage 2: symbol table
        self._log_stage(4, "Build symbol table")
        symbol_table = build_symbol_table(raw)

        # Stage 3: resolve references
        self._log_stage(5, "Resolve references")
        resolve_references(raw, symbol_table, experiment_dir)

        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"

        # Select primary level
        primary_level = select_primary_level(raw.levels, primary_level)

        # Stage 5: shared artifact enrichment
        self._log_stage(6, "Enrich shared schemas and effects")
        try:
            shared_artifacts = self._stage_5_prepare_shared_artifacts(
                raw,
                experiment_dir,
                primary_level=primary_level,
                temporal_supported=temporal_supported,
            )
        except (CircularDependencyError, TypeCheckError) as exc:
            raise self._vfs_domain_compilation_error(
                "Stage 6: Enrich shared schemas and effects",
                "VFS-PROFILE-COMPILE",
                experiment_dir / "vfs_profiles.yaml",
                exc,
            ) from exc

        # Stage 6: level compilation + optimization
        self._log_stage(7, "Compile levels and optimization data")
        # Stage 6: Compile levels (per-level artifacts)
        # Compute config hashes for provenance
        brain_hash = self._compute_pydantic_hash(raw.brain)
        experiment_hash = self._compute_pydantic_hash(raw.experiment)
        stratum_hash = self._compute_pydantic_hash(raw.stratum)
        environment_hash = self._compute_pydantic_hash(raw.environment)
        actions_hash = self._compute_pydantic_hash(raw.actions)
        items_hash = self._compute_pydantic_hash(raw.items) if raw.items else None

        try:
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
        except (CircularDependencyError, TypeCheckError) as exc:
            raise self._vfs_domain_compilation_error(
                "Stage 7: Compile levels and optimization data",
                "VFS-LEVEL-COMPILE",
                experiment_dir / "levels",
                exc,
            ) from exc

        # Stage 7: emit artifact + cache
        self._log_stage(8, "Emit compiled universe")
        effect_observation_slots = (
            EFFECT_OBSERVATION_SLOTS if shared_artifacts.compiled_effect_catalog and shared_artifacts.compiled_effect_catalog.effects else 0
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
            shared_artifacts.effects_schema,
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

    def _vfs_domain_compilation_error(
        self,
        stage: str,
        code: str,
        location: Path,
        exc: Exception,
    ) -> CompilationError:
        """Convert VFS/domain exceptions into compiler diagnostics."""
        return CompilationError(
            stage,
            [
                CompilationMessage(
                    code=code,
                    message=str(exc),
                    location=str(location),
                )
            ],
        )

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

        compiled_vfs_profiles = self._vfs_compiler.compile_profiles(raw.vfs_profiles, experiment_dir, bar_schema)
        self._vfs_compiler.validate_item_profile_bindings(raw.items, compiled_vfs_profiles)

        from townlet.vfs.history import collect_history_requirements

        vfs_history_spec = collect_history_requirements(compiled_vfs_profiles.global_profile if compiled_vfs_profiles else None)

        effects_schema = self._effects_compiler.build_schema(
            bar_names=tuple(meter.name for meter in primary_level_config.bars.meters),
            environment_variables=tuple(getattr(raw.environment.environment, "variables", ()) or ()),
            compiled_vfs_profiles=compiled_vfs_profiles,
        )

        compiled_effect_catalog = self._effects_compiler.compile_catalog(
            raw.effects,
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
                raw.action_label_overrides,
            )
            runtime_action_space = self._action_compiler.build_runtime_action_space(action_metadata)
            action_schema_hash = compute_action_schema_hash(runtime_action_space.actions)
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
            optimization_data = self._optimization_compiler.build_optimization_data(
                level.bars,
                level.affordances,
                meter_metadata,
                affordance_metadata,
                action_metadata,
            )
            vfs_fields = self._observation_compiler.build_vfs_observation_fields(obs_spec, raw.environment)
            base_vfs_variables = self._observation_compiler.build_vfs_variables(obs_spec, raw.environment)
            vfs_variables = self._vfs_compiler.build_runtime_variables(base_vfs_variables, compiled_vfs_profiles)
            observation_schema_hash = compute_observation_schema_hash(vfs_fields)
            variable_schema_hash = compute_variable_schema_hash(vfs_variables)
            transition_phase_graph = TransitionPhaseGraph.default()
            transition_action_writes = compile_vtc_action_writes_with_phase_graph(runtime_action_space.actions, transition_phase_graph)
            transition_affordance_gates = compile_vtc_affordance_gates_with_phase_graph(
                level.affordances.affordances,
                transition_phase_graph,
            )
            transition_interaction_progress = compile_vtc_interaction_progress_with_phase_graph(
                level.affordances.affordances,
                transition_phase_graph,
            )
            transition_terminal_conditions = compile_vtc_terminal_conditions_with_phase_graph(level.bars.meters, transition_phase_graph)
            transition_passive_depletions = compile_vtc_passive_depletions_with_phase_graph(level.bars.meters, transition_phase_graph)
            transition_modulations = compile_vtc_modulations_with_phase_graph(level.affordances.modulations, transition_phase_graph)
            transition_threshold_cascades = compile_vtc_threshold_cascades_with_phase_graph(level.bars.cascades, transition_phase_graph)
            transition_reward_components = compile_vtc_reward_components_with_phase_graph(level.drive, transition_phase_graph)
            transition_graph_hash = compute_transition_graph_hash(
                transition_phase_graph,
                transition_action_writes,
                affordance_gate_program=transition_affordance_gates,
                interaction_progress_program=transition_interaction_progress,
                terminal_condition_program=transition_terminal_conditions,
                threshold_cascade_program=transition_threshold_cascades,
                modulation_program=transition_modulations,
                passive_depletion_program=transition_passive_depletions,
                reward_component_program=transition_reward_components,
            )
            vfs_hash = compute_vfs_hash(variable_schema_hash, observation_schema_hash, action_schema_hash, transition_graph_hash)

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
                runtime_action_space=runtime_action_space,
                action_schema_hash=action_schema_hash,
                transition_graph_hash=transition_graph_hash,
                vfs_hash=vfs_hash,
                meter_metadata=meter_metadata,
                affordance_metadata=affordance_metadata,
                optimization_data=optimization_data,
                drive_hash=drive_hash,
                curriculum_hash=curriculum_hash,
                bars_hash=bars_hash,
                affordances_hash=affordances_hash,
                training_hash=training_hash,
                vfs_observation_fields=vfs_fields,
                observation_schema_hash=observation_schema_hash,
                vfs_variables=vfs_variables,
                variable_schema_hash=variable_schema_hash,
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

        vfs_observation_marks: dict[str, set[str]] | None = None
        if raw.variables_reference is not None:
            vfs_observation_marks = self._vfs_compiler.extract_observation_marks(raw.variables_reference)

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
        effects_schema: dict[str, str],
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
            observation_schema_hash=primary_meta.observation_schema_hash,
            vfs_variables=primary_meta.vfs_variables,
            variable_schema_hash=primary_meta.variable_schema_hash,
            action_space_metadata=primary_meta.action_metadata,
            runtime_action_space=primary_meta.runtime_action_space,
            action_schema_hash=primary_meta.action_schema_hash,
            transition_graph_hash=primary_meta.transition_graph_hash,
            vfs_hash=primary_meta.vfs_hash,
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
            effects_schema=effects_schema,
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
