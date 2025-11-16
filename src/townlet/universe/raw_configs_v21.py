"""Raw config loader for Config v2.1 hierarchical structure."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config, load_affordances_v2_config
from townlet.config.agent_config import AgentConfig
from townlet.config.bars_v2_config import BarsV2Config, load_bars_v2_config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config, load_training_v2_config
from townlet.universe.errors import CompilationErrorCollector


@dataclass(frozen=True)
class CurriculumLevel:
    """All curriculum-level configs for a single level."""

    name: str
    curriculum: CurriculumConfig
    bars: BarsV2Config
    affordances: AffordancesV2Config
    training: TrainingV2Config

    @property
    def level_dir(self) -> str:
        """Directory name for this level."""
        return self.name


@dataclass(frozen=True)
class RawConfigsV21:
    """Container for all v2.1 hierarchical config DTOs."""

    # Experiment-level configs (shared vocabulary and metadata)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    agent: AgentConfig

    # Curriculum levels (per-level parameters)
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path

    def __post_init__(self) -> None:
        """Validate vocabulary consistency across all curriculum levels."""
        if not self.levels:
            raise ValueError(f"No curriculum levels found in {self.experiment_dir}")

        env_meter_names = {meter.name for meter in self.environment.environment.meters}
        env_affordance_names = {aff.name for aff in self.environment.environment.affordances}

        for level_name, level in self.levels.items():
            level_meter_names = {meter.name for meter in level.bars.meters}
            level_affordance_names = {aff.name for aff in level.affordances.affordances}

            if level_meter_names != env_meter_names:
                missing = env_meter_names - level_meter_names
                extra = level_meter_names - env_meter_names
                raise ValueError(
                    "Meter vocabulary mismatch in "
                    f"{self.experiment_dir}/levels/{level_name}/bars.yaml\n"
                    f"  Expected (from environment.yaml): {sorted(env_meter_names)}\n"
                    f"  Actual: {sorted(level_meter_names)}\n"
                    f"  Missing: {sorted(missing) if missing else 'none'}\n"
                    f"  Extra: {sorted(extra) if extra else 'none'}\n"
                    "\nAll levels must have identical meter vocabulary to environment.yaml."
                )

            if level_affordance_names != env_affordance_names:
                missing = env_affordance_names - level_affordance_names
                extra = level_affordance_names - env_affordance_names
                raise ValueError(
                    "Affordance vocabulary mismatch in "
                    f"{self.experiment_dir}/levels/{level_name}/affordances.yaml\n"
                    f"  Expected (from environment.yaml): {sorted(env_affordance_names)}\n"
                    f"  Actual: {sorted(level_affordance_names)}\n"
                    f"  Missing: {sorted(missing) if missing else 'none'}\n"
                    f"  Extra: {sorted(extra) if extra else 'none'}\n"
                    "\nAll levels must have identical affordance vocabulary to environment.yaml."
                )

    @classmethod
    def from_experiment_dir(cls, experiment_dir: Path) -> RawConfigsV21:
        """
        Load all configs from a v2.1 experiment directory.

        Expected structure:
            experiment_dir/
              experiment.yaml
              stratum.yaml
              environment.yaml
              actions.yaml
              agent.yaml
              levels/
                <level_name>/
                  curriculum.yaml
                  bars.yaml
                  affordances.yaml
                  training.yaml
        """

        experiment_dir = Path(experiment_dir).resolve()
        errors = CompilationErrorCollector(stage="Stage 1: Load v2.1 Configs")

        # Shared experiment-level configs
        experiment = stratum = environment = actions = agent = None
        shared_specs = [
            ("experiment.yaml", ExperimentConfig, "experiment"),
            ("stratum.yaml", StratumConfig, "stratum"),
            ("environment.yaml", EnvironmentConfig, "environment"),
            ("actions.yaml", ActionsConfig, "actions"),
            ("agent.yaml", AgentConfig, "agent"),
        ]

        for filename, loader_cls, label in shared_specs:
            path = experiment_dir / filename
            try:
                loaded = loader_cls.from_yaml(path)  # type: ignore[attr-defined]
            except Exception as exc:  # noqa: BLE001 - we want to aggregate anything
                errors.add(
                    f"Failed to load {label} from {filename}: {exc}",
                    code="LOAD_ERROR",
                    location=str(path),
                )
                continue

            if label == "experiment":
                experiment = loaded
            elif label == "stratum":
                stratum = loaded
            elif label == "environment":
                environment = loaded
            elif label == "actions":
                actions = loaded
            elif label == "agent":
                agent = loaded

        # If any shared config failed, surface now.
        if errors.errors:
            errors.check_and_raise()

        # Curriculum levels
        levels_dir = experiment_dir / "levels"
        if not levels_dir.exists():
            errors.add(
                f"Missing levels/ directory under {experiment_dir}",
                code="MISSING_LEVELS_DIR",
                location=str(levels_dir),
            )
            errors.check_and_raise()

        levels: dict[str, CurriculumLevel] = {}
        for level_dir in sorted(levels_dir.iterdir()):
            if not level_dir.is_dir():
                continue

            level_name = level_dir.name
            try:
                curriculum = CurriculumConfig.from_yaml(level_dir / "curriculum.yaml")
                bars = load_bars_v2_config(level_dir)
                affordances = load_affordances_v2_config(level_dir)
                training = load_training_v2_config(level_dir)
                levels[level_name] = CurriculumLevel(
                    name=level_name,
                    curriculum=curriculum,
                    bars=bars,
                    affordances=affordances,
                    training=training,
                )
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load level '{level_name}': {exc}",
                    code="LEVEL_LOAD_ERROR",
                    location=str(level_dir),
                )

        if not levels:
            errors.add(
                f"No curriculum levels found in {levels_dir}",
                code="NO_CURRICULUM_LEVELS",
                location=str(levels_dir),
            )

        errors.check_and_raise()

        return cls(
            experiment=experiment,  # type: ignore[arg-type]
            stratum=stratum,  # type: ignore[arg-type]
            environment=environment,  # type: ignore[arg-type]
            actions=actions,  # type: ignore[arg-type]
            agent=agent,  # type: ignore[arg-type]
            levels=levels,
            experiment_dir=experiment_dir,
        )
