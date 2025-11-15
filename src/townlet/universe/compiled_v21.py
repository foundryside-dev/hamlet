"""CompiledUniverse for v2.1 hierarchical config structure."""

from dataclasses import dataclass
from pathlib import Path

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.agent_config import AgentConfig
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config
from townlet.universe.dto.observation_spec import ObservationSpec


@dataclass
class CompiledUniverseV21:
    """
    Compiled universe for v2.1 hierarchical config structure.

    Contains all loaded and validated configuration plus derived metadata.
    This is a v2.1-specific class that stores hierarchical configs directly
    without conversion to legacy flat structure.
    """

    # Shared configs (experiment-level)
    experiment: ExperimentConfig
    stratum: StratumConfig
    environment: EnvironmentConfig
    actions: ActionsConfig
    agent: AgentConfig

    # Curriculum levels: {level_name: (curriculum, bars, affordances, training)}
    curriculum_levels: dict[str, tuple[CurriculumConfig, BarsV2Config, AffordancesV2Config, TrainingV2Config]]

    # Derived metadata (per level)
    observation_specs: dict[str, ObservationSpec]  # {level_name: obs_spec}

    # Provenance
    experiment_dir: Path

    def get_level(self, level_name: str) -> tuple[CurriculumConfig, BarsV2Config, AffordancesV2Config, TrainingV2Config]:
        """Get curriculum level configs by name."""
        if level_name not in self.curriculum_levels:
            available = list(self.curriculum_levels.keys())
            raise ValueError(f"Level '{level_name}' not found. Available: {available}")
        return self.curriculum_levels[level_name]

    def get_obs_spec(self, level_name: str) -> ObservationSpec:
        """Get observation spec for curriculum level."""
        if level_name not in self.observation_specs:
            available = list(self.observation_specs.keys())
            raise ValueError(f"Obs spec for '{level_name}' not found. Available: {available}")
        return self.observation_specs[level_name]
