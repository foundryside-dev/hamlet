"""UniverseCompiler implementation (see stages.CompilationStage for the pipeline order)."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Any

import torch
import yaml

from townlet.config.brain_config import apply_training_overrides, compute_brain_hash
from townlet.effects.catalog import EffectCatalog, EffectCompileError
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.declarations import DeclarationStore, config_documents
from townlet.universe.dto import UniverseMetadata
from townlet.universe.error_codes import ErrorCode
from townlet.universe.raw_configs_v21 import RawConfigsV21
from townlet.universe.token_hashes import (
    compute_observation_schema_hash,
    compute_token_layout_hash,
    compute_token_type_schema_hash,
)
from townlet.vfs.history import collect_history_requirements
from townlet.vfs.profiles import CircularDependencyError
from townlet.vfs.schema_hashes import (
    compute_action_schema_hash,
    compute_actions_hash,
    compute_expression_schema_hash,
    compute_transition_graph_hash,
    compute_variable_schema_hash,
    compute_variables_hash,
    compute_vfs_hash,
)
from townlet.vfs.transition_schedule import build_vtc_transition_schedule
from townlet.vfs.vtc import VTCWriteRefusalError
from townlet.world.expression.type_checker import TypeCheckError

from .compiled import CompiledVFSProfiles
from .compilers.actions import ActionCompiler
from .compilers.effects import EffectsCompiler
from .compilers.metadata import MetadataCompiler
from .compilers.observation import ObservationCompiler
from .compilers.optimization import OptimizationCompiler
from .compilers.vfs import VFSCompiler
from .errors import CompilationError, CompilationErrorCollector, CompilationMessage
from .loaders.preflight import validate_config_dir
from .pipeline import CompiledLevelBundle, SharedCompilerArtifacts
from .source_map import SourceMap, locate
from .stages import CompilationStage
from .validation.limits import (
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

    def _log_stage(self, stage: CompilationStage) -> None:
        """Emit a concise stage marker for pipeline tracing."""
        logger.info("%s", stage.label)

    def compile(self, experiment_dir: Path, primary_level: str | None = None, use_cache: bool = True) -> CompiledUniverse:
        """Compile v2.1 hierarchical configs into a multi-level CompiledUniverse."""
        if primary_level is None:
            raise ValueError("UniverseCompiler.compile requires an explicit primary_level; implicit level selection is not allowed.")
        experiment_dir = Path(experiment_dir).resolve()
        self.config_pack_path = experiment_dir

        validate_config_dir(experiment_dir)

        # Stage 0 preflight: scoping (no YAML parsing yet)
        declarations = DeclarationStore.discover(experiment_dir)

        # The cache path is derived from primary_level, so an unknown level must be
        # rejected BEFORE it can name an artifact. Exact-name membership against the
        # directory listing — not is_dir(), which admits "." and "..".
        self._validate_primary_level_exists(experiment_dir, primary_level)

        # Optional cache fast-path
        cache_path = self._cache_artifact_path(experiment_dir, primary_level)
        config_hash: str | None = None
        config_mtime: float | None = None

        if use_cache and cache_path.exists():
            cached = self._read_cache_artifact(cache_path)
            if cached is not None:
                # OUTSIDE the defensive read above, deliberately. A raise left inside
                # that broad `except Exception` is downgraded to a warning and compile()
                # returns normally — verified by execution — so a mislabelled artifact
                # would silently recompile instead of failing loudly.
                if cached.metadata.primary_level != primary_level:
                    raise CompilationError(
                        CompilationStage.PREFLIGHT.label,
                        [
                            CompilationMessage(
                                code=ErrorCode.ARTIFACT_LOAD_REFUSED,
                                message=(
                                    f"Compiled artifact declares primary_level '{cached.metadata.primary_level}' "
                                    f"but was loaded for '{primary_level}'. The cache is mislabelled; "
                                    "delete .compiled/ and recompile."
                                ),
                                location=f"{cache_path}:1",
                            )
                        ],
                    )

                staleness = self.cache_staleness(cached, experiment_dir)
                if not staleness:
                    logger.info("Loading compiled universe from cache: %s", cache_path)
                    return cached
                logger.info("Cache stale for %s (%s); recompiling.", cache_path, "; ".join(staleness))

        # Stage 0 preflight: YAML syntax validation (lightweight)

        self._log_stage(CompilationStage.PARSE)
        raw = RawConfigsV21.from_declarations(declarations)
        # Discovery retains source marks outside authored mapping keys;
        # the typed declaration products never receive metadata fields.
        source_map = declarations.source_map

        self._log_stage(CompilationStage.LIMITS)
        validate_v21_limits(raw, experiment_dir, source_map)

        self._log_stage(CompilationStage.SEMANTICS)
        validate_v21_semantics(raw, experiment_dir, source_map)

        self._log_stage(CompilationStage.SYMBOLS)
        symbol_table = build_symbol_table(raw, source_map)

        self._log_stage(CompilationStage.RESOLVE)
        resolve_references(raw, symbol_table, experiment_dir, source_map)
        self._resolve_presentation(raw, source_map)

        from townlet.universe.validation.static_access import validate_static_write_targets

        validate_static_write_targets(raw, source_map)

        temporal_supported = raw.stratum.stratum.temporal_support == "enabled"

        # Select primary level
        primary_level = select_primary_level(raw.levels, primary_level)

        self._log_stage(CompilationStage.SHARED)
        try:
            shared_artifacts = self._stage_6_prepare_shared_artifacts(
                raw,
                experiment_dir,
                primary_level=primary_level,
                temporal_supported=temporal_supported,
            )
        except EffectCompileError as exc:
            raise CompilationError(
                CompilationStage.SHARED.label,
                [
                    CompilationMessage(
                        code=ErrorCode.EFFECT_COMPILE,
                        message=str(exc),
                        location=locate(source_map, f"effects:{exc.effect_id}"),
                    )
                ],
            ) from exc.__cause__
        except (CircularDependencyError, TypeCheckError) as exc:
            raise self._vfs_domain_compilation_error(
                CompilationStage.SHARED.label,
                ErrorCode.VFS_PROFILE_COMPILE,
                Path(source_map.lookup("variables") or f"{experiment_dir}:1"),
                exc,
            ) from exc

        self._log_stage(CompilationStage.LEVELS)
        # Compute config hashes for provenance
        # brain_hash covers the EFFECTIVE brain config: brain.yaml merged with the primary
        # level's training.yaml overrides. Two deliberate changes from the sibling lines
        # below, both load-bearing:
        #   1. the INPUT is the effective config, not raw.brain — a training.yaml q_learning
        #      edit changes the network that trains, and must move the hash;
        #   2. the FUNCTION is compute_brain_hash, not _compute_pydantic_hash — it is what
        #      docs/config-schemas/brain.md documents and what every other brain-hash
        #      producer uses. Do NOT "match local style" and revert this to
        #      _compute_pydantic_hash; that silently diverges from every other producer.
        # This makes brain_hash level-scoped, exactly as drive_hash already is.
        # PDR-0027: a level's complete brain.yaml replaces the pack brain as the effective
        # base. brain_hash stays what it was: the EFFECTIVE config for the primary level.
        base_brain = raw.levels[primary_level].brain or raw.brain
        brain_hash = compute_brain_hash(apply_training_overrides(base_brain, raw.levels[primary_level].training))
        # PDR-0027 half 2: the pack baseline under the SAME level training overrides, so a
        # pack_brain_hash != brain_hash difference isolates exactly one cause — the level
        # declared its own brain.
        pack_brain_hash = compute_brain_hash(apply_training_overrides(raw.brain, raw.levels[primary_level].training))
        experiment_hash = self._compute_pydantic_hash(raw.experiment)
        stratum_hash = self._compute_pydantic_hash(raw.stratum)
        environment_hash = self._compute_pydantic_hash(raw.environment)
        # Canonical, not a pydantic dump: action-write expression text is hashed as its AST,
        # so a respelling that parses identically does not refuse resume.
        actions_hash = compute_actions_hash(raw.actions)
        items_hash = self._compute_pydantic_hash(raw.items) if raw.items else None
        # The sixth pack hash is canonical content, not `_compute_pydantic_hash`: `variables`
        # is a collection family whose fragments merge in sorted-path order, so a pydantic
        # dump would move on a file move while no variable changed (VFS round-2 F5).
        variables_hash = compute_variables_hash(raw.variables)

        try:
            level_bundle = self._stage_7_compile_levels(
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
                CompilationStage.LEVELS.label,
                ErrorCode.VFS_LEVEL_COMPILE,
                experiment_dir / "levels",
                exc,
            ) from exc

        self._log_stage(CompilationStage.EMIT)
        compiled = self._stage_8_emit_artifact(
            raw,
            experiment_dir,
            cache_path,
            use_cache,
            level_bundle.universe_metadata,
            level_bundle.all_levels,
            shared_artifacts.compiled_vfs_profiles,
            shared_artifacts.compiled_effect_catalog,
            shared_artifacts.effects_schema,
            level_bundle.vfs_expression_schema,
            level_bundle.vfs_evaluation_marks,
            shared_artifacts.vfs_history_spec,
            brain_hash=brain_hash,
            pack_brain_hash=pack_brain_hash,
            experiment_hash=experiment_hash,
            stratum_hash=stratum_hash,
            environment_hash=environment_hash,
            actions_hash=actions_hash,
            items_hash=items_hash,
            variables_hash=variables_hash,
        )
        return compiled

    def _resolve_presentation(self, raw: RawConfigsV21, source_map: SourceMap) -> None:
        """Stage 5 – a presentation entry must name a meter or affordance the pack declares.

        Presentation is observer-only (PDR-0025): it rides on the artifact so the observer reads
        one vocabulary, but it enters no semantic hash. Resolving its references here is what
        makes a declaration for something the universe lacks a located compile refusal rather
        than a key the frontend silently ignores.
        """
        presentation = raw.presentation
        if presentation is None:
            return
        env = raw.environment.environment
        meter_names = {meter.name for meter in env.meters}
        affordance_names = {affordance.name for affordance in env.affordances}
        errors = CompilationErrorCollector(stage=CompilationStage.RESOLVE.label)
        for name in presentation.meters:
            if name not in meter_names:
                errors.add(
                    f"Presentation declares meter '{name}', which the pack does not declare (declared meters: {sorted(meter_names)}).",
                    code=ErrorCode.UAC_RES_PRESENTATION,
                    location=locate(source_map, f"presentation:meters.{name}"),
                )
        for name in presentation.affordances:
            if name not in affordance_names:
                errors.add(
                    f"Presentation declares affordance '{name}', which the pack does not declare "
                    f"(declared affordances: {sorted(affordance_names)}).",
                    code=ErrorCode.UAC_RES_PRESENTATION,
                    location=locate(source_map, f"presentation:affordances.{name}"),
                )
        errors.check_and_raise()

    def _vfs_domain_compilation_error(
        self,
        stage: str,
        code: ErrorCode,
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

    def _stage_6_prepare_shared_artifacts(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        *,
        primary_level: str,
        temporal_supported: bool,
    ) -> SharedCompilerArtifacts:
        """Stage 6 – build shared schemas (bars/VFS) and compile effects catalog."""
        primary_level_config = raw.levels[primary_level]
        bar_schema: dict[str, str] = {meter.name: "float" for meter in primary_level_config.bars.meters}

        compiled_vfs_profiles = self._vfs_compiler.compile_profiles(raw.variables, bar_schema)
        self._vfs_compiler.validate_item_profile_bindings(raw.items, compiled_vfs_profiles)

        # Every history ring either profile reads, at its deepest lag (WP14). The profile
        # compile above has already refused any temporal call the runtime cannot serve.
        vfs_history_spec = collect_history_requirements(compiled_vfs_profiles.global_profile, compiled_vfs_profiles.agent_profile)

        effects_schema = self._effects_compiler.build_schema(
            bar_names=tuple(meter.name for meter in primary_level_config.bars.meters),
            variables=raw.variables,
            compiled_vfs_profiles=compiled_vfs_profiles,
        )

        compiled_effect_catalog = self._effects_compiler.compile_catalog(
            raw.effects,
            effects_schema,
            time_enabled=temporal_supported,
        )
        return SharedCompilerArtifacts(
            bar_schema=bar_schema,
            compiled_vfs_profiles=compiled_vfs_profiles,
            effects_schema=effects_schema,
            compiled_effect_catalog=compiled_effect_catalog,
            vfs_history_spec=vfs_history_spec,
        )

    def _stage_7_compile_levels(
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
        """Stage 7 – compile level metadata, optimization data, and derived schemas."""
        all_levels: dict[str, CompiledUniverse.LevelMetadata] = {}
        for level_name, level in raw.levels.items():
            logger.info("Compiling level: %s", level_name)
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
                variables=raw.variables,
                source_map=raw.source_map,
                level_name=level_name,
            )
            optimization_data = self._optimization_compiler.build_optimization_data(
                level.bars,
                level.affordances,
                meter_metadata,
                affordance_metadata,
                action_metadata,
                source_map=raw.source_map,
                level_name=level_name,
            )
            vfs_variables = self._vfs_compiler.build_runtime_variables(raw.variables)

            # The token observation artifact IS the compiler's observation product
            # (unit-3 Task-10 cut). It is built BEFORE `observation_schema_hash`, which
            # is now computed over it (token-obs spec §5) and enters slot 2 of the
            # structurally-unchanged four-term `compute_vfs_hash` composition.
            # Token-spec refusals (exposure, capacity, identity) leave the observation
            # compiler as located LEVELS-stage CompilationErrors with their error code.
            meter_declarations = self._observation_compiler.compile_meter_declarations(
                raw.environment,
                level.bars,
                level_name=level_name,
                source_map=raw.source_map,
            )
            token_spec, token_advisories = self._observation_compiler.build_token_spec(
                raw.stratum,
                meter_declarations,
                level.affordances,
                raw.items,
                compiled_effect_catalog,
                compiled_vfs_profiles,
                vfs_variables,
                # The EFFECTIVE brain for this level (PDR-0027 selection, same as stage 8);
                # it also decides whether the indistinguishability check applies.
                level.brain or raw.brain,
                enabled_affordances=level.training.enabled_affordances,
                level_name=level_name,
                source_map=raw.source_map,
            )
            token_type_schema_hash = compute_token_type_schema_hash(token_spec)
            layout_hash = compute_token_layout_hash(token_spec)
            for advisory in token_advisories:
                logger.warning("[%s] %s", level_name, advisory)

            observation_schema_hash = compute_observation_schema_hash(token_spec)
            assert compiled_vfs_profiles is not None and compiled_vfs_profiles.item_profiles is not None
            variable_schema_hash = compute_variable_schema_hash(vfs_variables, compiled_vfs_profiles.item_profiles)
            try:
                transition_schedule = build_vtc_transition_schedule(
                    runtime_action_space=runtime_action_space,
                    level=level,
                    transition_rules=raw.transition_rules,
                    vfs_variables=vfs_variables,
                    expression_profiles=(compiled_vfs_profiles.global_profile, compiled_vfs_profiles.agent_profile),
                )
            except VTCWriteRefusalError as exc:
                raise CompilationError(
                    CompilationStage.LEVELS.label,
                    [
                        CompilationMessage(
                            code=ErrorCode.VTC_WRITE_TYPE if refusal.kind == "type" else ErrorCode.UAC_STATIC_WRITE,
                            message=refusal.message,
                            location=locate(raw.source_map, refusal.origin_key),
                        )
                        for refusal in exc.refusals
                    ],
                ) from exc
            transition_graph_hash = compute_transition_graph_hash(
                transition_schedule.phase_graph,
                transition_schedule.action_write_program,
                affordance_gate_program=transition_schedule.affordance_gate_program,
                interaction_progress_program=transition_schedule.interaction_progress_program,
                terminal_condition_program=transition_schedule.terminal_condition_program,
                threshold_cascade_program=transition_schedule.threshold_cascade_program,
                modulation_program=transition_schedule.modulation_program,
                passive_depletion_program=transition_schedule.passive_depletion_program,
                transition_rule_program=transition_schedule.transition_rule_program,
                bounds_clamp_program=transition_schedule.bounds_clamp_program,
            )
            expression_schema_hash = compute_expression_schema_hash(
                global_profile=compiled_vfs_profiles.global_profile,
                agent_profile=compiled_vfs_profiles.agent_profile,
            )
            vfs_hash = compute_vfs_hash(
                variable_schema_hash, observation_schema_hash, action_schema_hash, transition_graph_hash, expression_schema_hash
            )

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
                observation_schema_hash=observation_schema_hash,
                vfs_variables=vfs_variables,
                variable_schema_hash=variable_schema_hash,
                transition_schedule=transition_schedule,
                items_appearance=level.items_appearance,
                meter_declarations=meter_declarations,
                token_spec=token_spec,
                token_type_schema_hash=token_type_schema_hash,
                layout_hash=layout_hash,
                token_advisories=token_advisories,
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

        vfs_evaluation_marks = self._vfs_compiler.derive_evaluation_marks(raw.variables)

        return CompiledLevelBundle(
            all_levels=all_levels,
            primary_meta=primary_meta,
            universe_metadata=universe_metadata,
            vfs_expression_schema=vfs_expression_schema,
            vfs_evaluation_marks=vfs_evaluation_marks,
        )

    def _stage_8_emit_artifact(
        self,
        raw: RawConfigsV21,
        experiment_dir: Path,
        cache_path: Path,
        use_cache: bool,
        universe_metadata: UniverseMetadata,
        all_levels: dict[str, CompiledUniverse.LevelMetadata],
        compiled_vfs_profiles: CompiledVFSProfiles | None,
        compiled_effect_catalog: EffectCatalog | None,
        effects_schema: dict[str, str],
        vfs_expression_schema: dict[str, str],
        vfs_evaluation_marks: dict[str, set[str]] | None,
        vfs_history_spec: dict[str, int],
        brain_hash: str | None,
        pack_brain_hash: str | None,
        experiment_hash: str,
        stratum_hash: str,
        environment_hash: str,
        actions_hash: str,
        items_hash: str | None,
        variables_hash: str,
    ) -> CompiledUniverse:
        """Stage 8 – emit the compiled artifact and persist cache."""
        compiled = CompiledUniverse(
            metadata=universe_metadata,
            experiment=raw.experiment,
            stratum=raw.stratum,
            environment=raw.environment,
            actions=raw.actions,
            # PDR-0027: the EFFECTIVE base brain for the compiled level — a level's own
            # complete brain.yaml replaces the pack brain. brain_hash above is computed
            # from the same selection; the two must never diverge.
            brain=raw.levels[universe_metadata.primary_level].brain or raw.brain,
            items_catalog=raw.items,
            presentation=raw.presentation,
            compiled_vfs_profiles=compiled_vfs_profiles,
            compiled_effect_catalog=compiled_effect_catalog,
            effects_schema=effects_schema,
            vfs_expression_schema=vfs_expression_schema,
            vfs_history_spec=vfs_history_spec or None,
            vfs_evaluation_marks=vfs_evaluation_marks,
            experiment_dir=experiment_dir,
            brain_hash=brain_hash,
            pack_brain_hash=pack_brain_hash,
            experiment_hash=experiment_hash,
            stratum_hash=stratum_hash,
            environment_hash=environment_hash,
            actions_hash=actions_hash,
            items_hash=items_hash,
            variables_hash=variables_hash,
            all_levels=all_levels,
        )

        if use_cache:
            # A failed cache write fails the compile. The user asked for an artifact;
            # reporting success while writing nothing is how hamlet-a141ab5db3 stayed
            # invisible (a downgraded logger.warning the CLI never displayed).
            try:
                cache_dir = self._cache_directory_for(experiment_dir)
                self._prepare_cache_directory(cache_dir)
                compiled.save_to_cache(cache_path)
            except Exception as exc:
                raise CompilationError(
                    stage="Cache Write",
                    errors=[f"Failed to write cache artifact to {cache_path}: {exc}"],
                    hints=["Pass --no-cache to compile without persisting an artifact."],
                ) from exc
            logger.info("Saved compiled universe cache to %s", cache_path)

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
                documents = list(yaml.safe_load_all(handle))
            if len(documents) == 1:
                return yaml.dump(documents[0] or {}, sort_keys=True)
            return yaml.safe_dump_all(documents, sort_keys=True)
        except yaml.YAMLError as exc:
            # Transform raw YAML errors into friendly syntax errors
            error_msg = str(exc)
            if hasattr(exc, "problem_mark"):
                mark = exc.problem_mark
                error_msg = f"line {mark.line + 1}, column {mark.column + 1}: {getattr(exc, 'problem', None) or 'syntax error'}"
                if hasattr(exc, "context"):
                    error_msg = f"{exc.context}\n  {error_msg}"

            raise CompilationError(
                stage=CompilationStage.PREFLIGHT.label,
                errors=[
                    CompilationMessage(
                        code=ErrorCode.YAML_SYNTAX_ERROR,
                        message=error_msg,
                        location=f"{file_path}:{getattr(getattr(exc, 'problem_mark', None), 'line', 0) + 1}",
                    )
                ],
                hints=[
                    "Check YAML indentation (use spaces, not tabs)",
                    "Ensure lists use proper '- item' syntax",
                    "Validate YAML syntax at yamllint.com or with 'yamllint <file>'",
                ],
            ) from exc

    def _build_cache_fingerprint(self, config_dir: Path) -> tuple[str, str]:
        """Return ``(config_hash, provenance_id)`` for the pack at ``config_dir``.

        ``config_hash`` is the pack's content (two identical packs share it). The
        provenance carries everything else an artifact depends on: the resolved pack
        path (an artifact copied with its pack belongs to the source, not the copy), the
        bytes of the townlet source tree (an uncommitted compiler edit moves it; a commit
        that touches no source does not), and the interpreter/dependency versions.
        """
        config_hash = self._compute_config_hash(config_dir)
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        from pydantic import __version__ as pydantic_version  # lazy import to avoid startup penalty

        provenance = self._compute_provenance_id(
            config_hash=config_hash,
            experiment_dir=str(Path(config_dir).resolve()),
            compiler_version=COMPILER_VERSION,
            source_digest=self._compute_package_source_digest(),
            python_version=python_version,
            torch_version=torch.__version__,
            pydantic_version=pydantic_version,
        )
        return config_hash, provenance

    def cache_staleness(self, compiled: CompiledUniverse, config_dir: Path) -> list[str]:
        """Say why ``compiled`` no longer matches the pack at ``config_dir``; empty when fresh.

        The single freshness rule, shared by the compile cache fast-path and ``inspect``:
        the artifact must have been compiled from this pack path, with this pack content
        and executable provenance, and no pack file may be newer than the compile.
        """
        config_dir = Path(config_dir).resolve()
        meta = compiled.metadata
        reasons: list[str] = []
        if compiled.experiment_dir is None or Path(compiled.experiment_dir).resolve() != config_dir:
            reasons.append(f"compiled from {compiled.experiment_dir}, not {config_dir}")
        if not config_dir.is_dir():
            reasons.append(f"source pack {config_dir} does not exist")
            return reasons
        config_hash, provenance_id = self._build_cache_fingerprint(config_dir)
        if meta.config_hash != config_hash:
            reasons.append("pack content changed since compile (config_hash differs)")
        elif meta.provenance_id != provenance_id:
            # provenance_id folds in config_hash, so it is only informative when the content matches.
            reasons.append("compiler provenance changed (pack path, townlet source, or python/torch/pydantic version)")
        if meta.config_mtime < self._compute_config_mtime(config_dir):
            reasons.append("a pack file was modified after compile")
        return reasons

    def _cache_directory_for(self, config_dir: Path) -> Path:
        """Return the cache directory path for a config pack."""

        return config_dir / ".compiled"

    def _validate_primary_level_exists(self, config_dir: Path, primary_level: str) -> None:
        """Reject an unknown primary level before it can name a cache artifact.

        Mirrors ``select_primary_level``'s message, which runs much later (after
        YAML load). Without this, an unknown level names a cache path nothing will
        ever hit and the failure surfaces far from its cause.
        """

        levels_dir = config_dir / "levels"
        # Directories only: a stray file in levels/ (README.md) is not a level.
        # Exact-name membership, not (levels_dir / name).is_dir(), which would admit
        # "." and ".." and nested paths.
        available = sorted(entry.name for entry in levels_dir.iterdir() if entry.is_dir()) if levels_dir.is_dir() else []
        if primary_level not in available:
            raise CompilationError(
                CompilationStage.PREFLIGHT.label,
                [
                    CompilationMessage(
                        code=ErrorCode.PRIMARY_LEVEL_UNKNOWN,
                        message=f"Primary level '{primary_level}' not found. Available: {available}",
                        location=f"{levels_dir}:1",
                    )
                ],
            )

    def _read_cache_artifact(self, cache_path: Path) -> CompiledUniverse | None:
        """Load a cached artifact, or return None if it is unusable.

        Defensive by design: a corrupt or oversized artifact is a cache miss, not a
        crash. The level-identity guard deliberately lives at the CALL SITE, outside
        this try — a mislabelled artifact is a provenance failure, not a miss.
        """

        try:
            cache_size = cache_path.stat().st_size
            if cache_size > MAX_CACHE_FILE_SIZE:
                logger.warning(
                    "Cache file exceeds size limit (%d bytes > %d bytes)",
                    cache_size,
                    MAX_CACHE_FILE_SIZE,
                )
                return None
            return CompiledUniverse.load_from_cache(cache_path)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load cached universe from %s: %s", cache_path, exc)
            return None

    def _cache_artifact_path(self, config_dir: Path, primary_level: str) -> Path:
        """Return the cache artifact path for a pack compiled at ``primary_level``.

        One artifact per level. There is deliberately no default for
        ``primary_level``: a pack-wide ``universe.msgpack`` is what let a request
        for one level be served another level's projection, and a default would
        quietly reintroduce it.
        """

        return self._cache_directory_for(config_dir) / f"universe-{primary_level}.msgpack"

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
        yaml_files = config_documents(config_dir)

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
        yaml_files = config_documents(config_dir)

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
        experiment_dir: str,
        compiler_version: str,
        source_digest: str,
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
                experiment_dir,
                compiler_version,
                source_digest,
                python_version,
                torch_version,
                pydantic_version,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _package_root() -> Path:
        """The directory holding the townlet source this compiler was imported from."""
        import townlet

        return Path(townlet.__file__).resolve().parent

    def _compute_package_source_digest(self) -> str:
        """SHA-256 over every ``.py`` file of the townlet package (relative path + bytes).

        Robust where a git sha is not: it moves on an uncommitted edit, stays put on a
        commit that touches no source, and works for an installed (non-git) package.
        The whole package, not only ``universe/``: the artifact embeds the products of
        config DTOs, VFS, effects and substrate code. Measured at ~7 ms for the tree.
        """
        root = self._package_root()
        digest = hashlib.sha256()
        for source in sorted(root.rglob("*.py")):
            digest.update(source.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(source.read_bytes())
        return digest.hexdigest()

    def _get_git_sha(self) -> str:
        """HEAD of the repository holding the townlet source, independent of the cwd.

        Recorded on the artifact as ``compiler_git_sha``; it is not a cache input (the
        source digest is), so a non-git install records "unknown" without thrashing.
        """
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self._package_root(),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "unknown"
