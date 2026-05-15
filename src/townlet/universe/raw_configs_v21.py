"""Raw config loader for Config v2.1 hierarchical structure."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import yaml

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config, load_affordances_v2_config
from townlet.config.bars_v2_config import BarsV2Config, load_bars_v2_config
from townlet.config.brain_config import BrainConfig, load_brain_config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.drive_as_code import DriveAsCodeConfig
from townlet.config.effects_config import EffectsConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config, load_training_v2_config
from townlet.config.vfs_profiles_config import VFSProfilesConfig
from townlet.universe.errors import CompilationErrorCollector
from townlet.vfs.schema import VariableDef, load_variables_reference_config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurriculumLevel:
    """All curriculum-level configs for a single level."""

    name: str
    curriculum: CurriculumConfig
    bars: BarsV2Config
    affordances: AffordancesV2Config
    drive: DriveAsCodeConfig
    training: TrainingV2Config
    items_appearance: ItemsAppearanceConfig | None = None

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
    brain: BrainConfig

    # Curriculum levels (per-level parameters)
    levels: dict[str, CurriculumLevel]

    # Provenance
    experiment_dir: Path

    # Optional experiment-level configs
    items: ItemsCatalogConfig | None = None
    vfs_profiles: VFSProfilesConfig | None = None
    effects: EffectsConfig | None = None
    action_label_overrides: dict[int, str] | None = None
    variables_reference: tuple[VariableDef, ...] | None = None

    def __post_init__(self) -> None:
        """Validate local DTO construction invariants."""
        if not self.levels:
            raise ValueError(f"No curriculum levels found in {self.experiment_dir}")

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
        experiment = stratum = environment = actions = brain = items = vfs_profiles = effects = None
        action_label_overrides: dict[int, str] | None = None
        variables_reference: tuple[VariableDef, ...] | None = None
        shared_specs = [
            ("experiment.yaml", ExperimentConfig, "experiment"),
            ("stratum.yaml", StratumConfig, "stratum"),
            ("environment.yaml", EnvironmentConfig, "environment"),
            ("actions.yaml", ActionsConfig, "actions"),
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

        # Load brain.yaml
        brain_path = experiment_dir / "brain.yaml"
        try:
            brain = load_brain_config(experiment_dir)
        except Exception as exc:
            errors.add(
                f"Failed to load brain from brain.yaml: {exc}",
                code="LOAD_ERROR",
                location=str(brain_path),
            )

        # Load items.yaml (optional)
        items_path = experiment_dir / "items.yaml"
        if items_path.exists():
            try:
                loaded_items = ItemsCatalogConfig.from_yaml(items_path)
                # Treat zero-capacity catalogs as disabled to remove item actions/obs.
                if loaded_items.max_items_in_world == 0 or loaded_items.max_items_per_agent == 0:
                    items = None
                else:
                    items = loaded_items
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load items from items.yaml: {exc}",
                    code="LOAD_ERROR",
                    location=str(items_path),
                )

        # Load vfs_profiles.yaml (required experiment-level artifact)
        vfs_profiles_path = experiment_dir / "vfs_profiles.yaml"
        try:
            vfs_profiles_data = yaml.safe_load(vfs_profiles_path.read_text()) or {}
            vfs_profiles = VFSProfilesConfig(**vfs_profiles_data)
        except Exception as exc:  # noqa: BLE001
            errors.add(
                f"Failed to load VFS profiles from vfs_profiles.yaml: {exc}",
                code="LOAD_ERROR",
                location=str(vfs_profiles_path),
            )

        # Load effects.yaml (optional experiment-level artifact)
        effects_path = experiment_dir / "effects.yaml"
        if effects_path.exists():
            try:
                effects_data = yaml.safe_load(effects_path.read_text()) or {}
                effects = EffectsConfig(**effects_data)
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load effects from effects.yaml: {exc}",
                    code="LOAD_ERROR",
                    location=str(effects_path),
                )

        # Load action_labels.yaml (optional experiment-level metadata)
        action_labels_path = experiment_dir / "action_labels.yaml"
        if action_labels_path.exists():
            try:
                labels_data = yaml.safe_load(action_labels_path.read_text()) or {}
                raw_custom = labels_data.get("custom")
                if raw_custom is not None:
                    if not isinstance(raw_custom, dict):
                        raise ValueError("action_labels.yaml custom field must be a mapping from action id to label")
                    action_label_overrides = {int(k): str(v) for k, v in raw_custom.items()}
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load action labels from action_labels.yaml: {exc}",
                    code="LOAD_ERROR",
                    location=str(action_labels_path),
                )

        # Load variables_reference.yaml (optional experiment-level VFS observation metadata)
        variables_reference_path = experiment_dir / "variables_reference.yaml"
        if variables_reference_path.exists():
            try:
                variables_reference = tuple(load_variables_reference_config(experiment_dir))
            except Exception as exc:  # noqa: BLE001
                errors.add(
                    f"Failed to load variables reference from variables_reference.yaml: {exc}",
                    code="LOAD_ERROR",
                    location=str(variables_reference_path),
                )

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

                drive_path = level_dir / "drive.yaml"
                with drive_path.open() as f:
                    drive_data = yaml.safe_load(f)
                drive = DriveAsCodeConfig(**drive_data["drive"])

                # Load level-specific items.yaml if exists
                items_appearance = None
                level_items_path = level_dir / "items.yaml"
                if level_items_path.exists():
                    with level_items_path.open() as f:
                        items_data = yaml.safe_load(f)
                    items_appearance = ItemsAppearanceConfig(**items_data)

                levels[level_name] = CurriculumLevel(
                    name=level_name,
                    curriculum=curriculum,
                    bars=bars,
                    affordances=affordances,
                    drive=drive,
                    training=training,
                    items_appearance=items_appearance,
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
            brain=brain,  # type: ignore[arg-type]
            items=items,
            vfs_profiles=vfs_profiles,
            effects=effects,
            action_label_overrides=action_label_overrides,
            variables_reference=variables_reference,
            levels=levels,
            experiment_dir=experiment_dir,
        )
