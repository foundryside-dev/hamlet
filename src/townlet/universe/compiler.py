"""UniverseCompiler implementation (Stage 1 scaffolding)."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from collections import defaultdict
from numbers import Number
from pathlib import Path
from typing import Any

import torch
import yaml

from townlet.config.affordance import AffordanceConfig
from townlet.universe.compiled_v21 import CompiledUniverseV21
from townlet.universe.dto import (
    ObservationField,
    ObservationSpec,
)

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


class UniverseCompiler:
    """Entry point for compiling config packs into CompiledUniverse artifacts."""

    def __init__(self) -> None:
        pass

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
        from townlet.config.agent_config import AgentConfig
        from townlet.config.bars_v2_config import load_bars_v2_config
        from townlet.config.curriculum_config import CurriculumConfig
        from townlet.config.environment_config import EnvironmentConfig
        from townlet.config.experiment_config import ExperimentConfig
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
                f"No curriculum levels found in {levels_dir}\n"
                f"Expected at least one level directory (e.g., levels/L1_full_observability/)"
            )

        return (experiment, stratum, environment, actions, agent, levels_dict)

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

    def _build_observation_spec(
        self,
        stratum,
        environment,
        curriculum,
        agent,
    ) -> ObservationSpec:
        """
        Build observation spec using Support/Active pattern.

        Support (stratum): Which observation fields CAN exist (declared at experiment level)
        Active (curriculum): Which fields ARE active vs masked (varies per curriculum level)

        This enables:
        - Transfer learning: All levels have same obs_dim (masked fields = zeros)
        - Power user optimization: Future enhancement can exclude unsupported fields

        Args:
            stratum: Stratum config with vision/temporal support declarations
            environment: Environment config with meter/affordance vocabulary
            curriculum: Curriculum config with active vision/temporal settings
            agent: Agent config with perception settings

        Returns:
            ObservationSpec with all fields, marked as active or masked via description
        """
        fields = []
        offset = 0

        # ===== Vision Fields (Support/Active pattern) =====

        # Global vision (grid encoding)
        if stratum.stratum.vision_support in ["both", "global"]:
            is_active = curriculum.curriculum.active_vision == "global"

            # Compute grid encoding dimensions
            if stratum.stratum.substrate.type == "grid":
                grid_width = stratum.stratum.substrate.grid.width
                grid_height = stratum.stratum.substrate.grid.height
                grid_encoding_dims = grid_width * grid_height  # e.g., 8*8 = 64
            else:
                grid_encoding_dims = 0  # Non-grid substrates don't have grid encoding

            if grid_encoding_dims > 0:
                desc = f"{grid_width}x{grid_height} grid encoding" if is_active else "MASKED (partial obs active)"
                fields.append(
                    ObservationField(
                        uuid=None,  # Auto-computed
                        name="obs_grid_encoding",
                        type="spatial_grid",
                        dims=grid_encoding_dims,
                        start_index=offset,
                        end_index=offset + grid_encoding_dims,
                        scope="agent",
                        description=desc,
                        semantic_type="spatial",
                    )
                )
                offset += grid_encoding_dims

        # Partial vision (local window)
        if stratum.stratum.vision_support in ["both", "partial"]:
            is_active = curriculum.curriculum.active_vision in ["partial", "local"]

            # Compute local window dimensions from normalized vision_range
            if stratum.stratum.substrate.type == "grid":
                grid_width = stratum.stratum.substrate.grid.width
                # vision_range is 0.0-1.0, represents fraction of grid
                # e.g., 0.625 on 8x8 grid = 5-cell window → 5x5 = 25 dims
                window_size = max(3, int(curriculum.curriculum.vision_range * grid_width))
                # Force odd size (agent at center)
                if window_size % 2 == 0:
                    window_size += 1
                # Clamp to grid size
                window_size = min(window_size, grid_width)

                local_window_dims = window_size**2  # e.g., 5^2 = 25
            else:
                local_window_dims = 0

            if local_window_dims > 0:
                desc = f"{window_size}x{window_size} local window" if is_active else "MASKED (global obs active)"
                fields.append(
                    ObservationField(
                        uuid=None,
                        name="obs_local_window",
                        type="spatial_grid",
                        dims=local_window_dims,
                        start_index=offset,
                        end_index=offset + local_window_dims,
                        scope="agent",
                        description=desc,
                        semantic_type="spatial",
                    )
                )
                offset += local_window_dims

        # ===== Position and Velocity (always active) =====

        position_dims = 2  # 2D grid (width, height)

        fields.append(
            ObservationField(
                uuid=None,
                name="obs_position",
                type="vector",
                dims=position_dims,
                start_index=offset,
                end_index=offset + position_dims,
                scope="agent",
                description=f"Agent position ({position_dims}D coordinates)",
                semantic_type="spatial",
            )
        )
        offset += position_dims

        fields.append(
            ObservationField(
                uuid=None,
                name="obs_velocity",
                type="vector",
                dims=position_dims,
                start_index=offset,
                end_index=offset + position_dims,
                scope="agent",
                description=f"Agent velocity ({position_dims}D vector)",
                semantic_type="spatial",
            )
        )
        offset += position_dims

        # ===== Meters (always active, fixed vocabulary) =====

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
                description=f"{meter_count} meter values (normalized 0-1)",
                semantic_type="bars",
            )
        )
        offset += meter_count

        # ===== Affordances (always active, fixed vocabulary) =====

        affordance_count = len(environment.environment.affordances)

        fields.append(
            ObservationField(
                uuid=None,
                name="obs_affordances",
                type="vector",
                dims=affordance_count,
                start_index=offset,
                end_index=offset + affordance_count,
                scope="agent",
                description=f"{affordance_count} affordance distances (normalized)",
                semantic_type="affordance",
            )
        )
        offset += affordance_count

        # ===== Temporal Features (Support/Active pattern) =====

        if stratum.stratum.temporal_support == "enabled":
            is_active = curriculum.curriculum.active_temporal

            # Temporal features: (time_of_day_sin, time_of_day_cos, day_progress, is_night)
            temporal_dims = 4

            desc = "Temporal features (day/night cycle)" if is_active else "MASKED (temporal inactive)"
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

        # ===== Build ObservationSpec =====

        obs_spec = ObservationSpec.from_fields(fields=fields)

        active_dims = sum(f.dims for f in fields if "MASKED" not in f.description)
        masked_dims = sum(f.dims for f in fields if "MASKED" in f.description)

        logger.info("  Observation spec built:")
        logger.info("    Total dims: %d (active: %d, masked: %d)", obs_spec.total_dims, active_dims, masked_dims)
        for field in fields:
            status = "ACTIVE" if "MASKED" not in field.description else "MASKED"
            logger.info("      [%3d:%3d] %-25s (%3d dims) %s", field.start_index, field.end_index, field.name, field.dims, status)

        return obs_spec

    def _compile_v21_hierarchical(self, experiment_dir: Path, use_cache: bool = True) -> CompiledUniverseV21:
        """
        Compile v2.1 hierarchical config structure into CompiledUniverseV21.

        This is a parallel implementation path for v2.1 configs, separate from legacy flat configs.

        Args:
            experiment_dir: Path to experiment root with experiment.yaml
            use_cache: Whether to use cache (currently stubbed for v2.1)

        Returns:
            CompiledUniverseV21

        Raises:
            NotImplementedError: Stages 3-7 not yet implemented
        """
        logger.info("Compiling v2.1 experiment: %s", experiment_dir)

        # Stage 1: Load hierarchical structure
        logger.info("=== Stage 1: Loading hierarchical config structure ===")
        (experiment, stratum, environment, actions, agent, levels_dict) = self._load_experiment_structure(experiment_dir)

        logger.info("Loaded experiment: '%s'", experiment.experiment.metadata.name)
        logger.info("  Description: %s", experiment.experiment.metadata.description)
        logger.info("  Stratum: %s", stratum.stratum.substrate.type)
        logger.info("  Curriculum levels: %s", list(levels_dict.keys()))

        # Stage 2: Cross-curriculum vocabulary validation
        logger.info("=== Stage 2: Validating vocabulary consistency ===")
        self._validate_vocabulary_consistency(environment, levels_dict)

        # Stage 3-4: Symbol table and resolution
        # TODO: Implement if needed for your system
        # For now, skip these stages (legacy may not need them)
        logger.info("=== Stage 3-4: Symbol table and resolution (skipped) ===")

        # Stage 5: Build observation specs for all curriculum levels
        logger.info("=== Stage 5: Building observation specs ===")
        observation_specs = {}
        for level_name, (curriculum, bars, affordances, training) in levels_dict.items():
            logger.info("Building obs spec for %s:", level_name)
            obs_spec = self._build_observation_spec(stratum, environment, curriculum, agent)
            observation_specs[level_name] = obs_spec

        # Stage 6-7: Optimization and emit
        logger.info("=== Stage 6-7: Optimization and emit ===")
        logger.info("Creating CompiledUniverseV21...")

        compiled = CompiledUniverseV21(
            experiment=experiment,
            stratum=stratum,
            environment=environment,
            actions=actions,
            agent=agent,
            curriculum_levels=levels_dict,
            observation_specs=observation_specs,
            experiment_dir=experiment_dir,
        )

        logger.info("✓ Compilation complete for '%s'", experiment.experiment.metadata.name)
        logger.info("  %d curriculum levels loaded", len(compiled.curriculum_levels))
        logger.info("  %d observation specs generated", len(compiled.observation_specs))

        return compiled

    def compile(self, config_dir: Path, use_cache: bool = True) -> CompiledUniverseV21:
        """
        Compile a v2.1 hierarchical config pack into a CompiledUniverseV21.

        BREAKING CHANGE (v2.1): Flat config structure NO LONGER SUPPORTED.
        Only v2.1 hierarchical structure is supported. Old flat configs will raise CompilationError.

        For v2.1 hierarchical structure:
            config_dir/
            ├── experiment.yaml       # Metadata
            ├── stratum.yaml          # World shape (substrate, grid, temporal)
            ├── environment.yaml      # Vocabulary (bars, affordances, VFS)
            ├── actions.yaml          # Action space configuration
            ├── agent.yaml            # Perception + Drive + Brain
            └── levels/
                ├── L1_full_observability/
                │   ├── curriculum.yaml   # Vision/temporal activation
                │   ├── bars.yaml         # Bar parameters + cascades
                │   ├── affordances.yaml  # Affordance parameters
                │   └── training.yaml     # Runtime orchestration
                └── [other levels]/

        Compilation stages (v2.1):
        - Stage 1: Load hierarchical structure (5 shared + N curriculum levels)
        - Stage 2: Cross-curriculum vocabulary validation (WHAT vs HOW enforcement)
        - Stage 3: Build symbol table from environment.yaml
        - Stage 4: Resolve references and dependencies
        - Stage 5: Generate observation spec with Support/Active pattern
        - Stage 6: Optimize and cache
        - Stage 7: Emit CompiledUniverse

        Args:
            config_dir: Path to experiment root (v2.1 hierarchical structure)
            use_cache: Whether to use compiled universe cache

        Returns:
            CompiledUniverseV21 with validated, cross-curriculum consistent configuration

        Raises:
            CompilationError: If experiment.yaml missing (not a v2.1 config)
            ValueError: If vocabulary inconsistent across curriculum levels
            FileNotFoundError: If required config files missing
        """

        config_dir = Path(config_dir).resolve()  # Resolve to absolute path
        self._validate_config_dir(config_dir)

        # BREAKING CHANGE: Only v2.1 hierarchical structure supported
        is_v21 = (config_dir / "experiment.yaml").exists()

        if not is_v21:
            raise CompilationError(
                stage="Config Structure Validation",
                errors=[
                    f"Legacy flat config structure no longer supported: {config_dir}",
                    "Config directory must contain experiment.yaml (v2.1 hierarchical structure)",
                ],
                hints=[
                    "Migrate to v2.1 hierarchical structure (see docs/guides/v2.1-migration.md)",
                    "All curriculum levels must be in levels/ subdirectory",
                ],
            )

        # V2.1 HIERARCHICAL STRUCTURE PATH
        logger.info("Compiling v2.1 hierarchical config structure")
        return self._compile_v21_hierarchical(config_dir, use_cache)

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

        # Required config files (consolidated structure)
        # Note: training.yaml contains training/environment/population/curriculum/exploration sections
        required_files = [
            "training.yaml",
            "bars.yaml",
            "cascades.yaml",
            "affordances.yaml",
            "substrate.yaml",
            "cues.yaml",
            "variables_reference.yaml",  # Required file, but variables list can be empty
        ]

        # Optional files
        optional_files = ["action_labels.yaml"]

        # Also check global actions (outside config_dir)
        global_actions_path = Path("configs") / "global_actions.yaml"
        all_files_to_check = [(config_dir / f, f, True) for f in required_files]
        all_files_to_check.extend([(config_dir / f, f, False) for f in optional_files])
        all_files_to_check.append((global_actions_path, "global_actions.yaml", True))

        for file_path, file_name, is_required in all_files_to_check:
            if not file_path.exists():
                if is_required:
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
                error_msg = str(exc)
                if hasattr(exc, "problem_mark"):
                    mark = exc.problem_mark
                    problem = getattr(exc, "problem", None) or "syntax error"
                    error_msg = f"line {mark.line + 1}, column {mark.column + 1}: {problem}"
                    if hasattr(exc, "context") and exc.context:
                        error_msg = f"{exc.context}\n  {error_msg}"

                errors.add(
                    error_msg,
                    code="YAML_SYNTAX_ERROR",
                    location=file_name,
                )

        if errors.errors:
            errors.add_hint("Check YAML indentation (use spaces, not tabs)")
            errors.add_hint("Ensure lists use proper '- item' syntax")
            errors.add_hint("Validate YAML syntax at yamllint.com or with 'yamllint <file>'")
            errors.check_and_raise()

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
        yaml_files = sorted(config_dir.glob("*.yaml"))
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

        pipeline = affordance.effect_pipeline
        if pipeline is not None:
            _add_entries(pipeline.on_start)
            _add_entries(pipeline.per_tick)
            _add_entries(pipeline.on_completion)
            _add_entries(pipeline.on_early_exit)
            _add_entries(pipeline.on_failure)
        else:
            _add_entries(getattr(affordance, "effects", []))
            _add_entries(getattr(affordance, "effects_per_tick", []))
            _add_entries(getattr(affordance, "completion_bonus", []))

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
