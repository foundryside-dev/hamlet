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

if False:  # TYPE_CHECKING
    from townlet.universe.dto.runtime import RuntimeUniverse


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

    def as_single_level(self, level_name: str) -> dict:
        """Extract single curriculum level as flat dict for backwards compatibility.

        This is NOT an adapter - it's a convenience for accessing one level's config.

        Args:
            level_name: Curriculum level to extract

        Returns:
            Dict with all configs for that level
        """
        curriculum, bars, affordances, training = self.get_level(level_name)

        return {
            "experiment": self.experiment,
            "stratum": self.stratum,
            "environment": self.environment,
            "actions": self.actions,
            "agent": self.agent,
            "curriculum": curriculum,
            "bars": bars,
            "affordances": affordances,
            "training": training,
            "observation_spec": self.get_obs_spec(level_name),
        }

    def to_runtime(self, level_name: str) -> "RuntimeUniverse":
        """Convert to RuntimeUniverse for specified curriculum level.

        Args:
            level_name: Which curriculum level to create runtime for (e.g., "L0_0_minimal")

        Returns:
            RuntimeUniverse with configs for specified level

        Raises:
            ValueError: If level_name not found in curriculum_levels
            NotImplementedError: to_runtime() not yet implemented for v2.1 hierarchical configs

        NOTE: This method is currently NOT IMPLEMENTED because RuntimeUniverse expects:
            - HamletConfig (flat legacy structure)
            - EnvironmentConfig (cascade config from environment/cascade_config.py)

        But CompiledUniverseV21 contains:
            - Hierarchical v2.1 configs (experiment/stratum/environment/actions/agent)
            - EnvironmentConfig (from config/environment_config.py - different type!)

        To implement this method, we need ONE of:
        1. Create adapter that converts v2.1 hierarchical -> legacy flat HamletConfig
        2. Refactor RuntimeUniverse to accept v2.1 hierarchical structure directly
        3. Create RuntimeUniverseV21 that mirrors v2.1 structure

        Until then, this method raises NotImplementedError.
        """
        # Validate level exists
        if level_name not in self.curriculum_levels:
            available = list(self.curriculum_levels.keys())
            raise ValueError(f"Level '{level_name}' not found. Available: {available}")

        raise NotImplementedError(
            "to_runtime() not yet implemented for CompiledUniverseV21.\n"
            "\n"
            "RuntimeUniverse expects legacy flat configs (HamletConfig + cascade EnvironmentConfig).\n"
            "CompiledUniverseV21 contains v2.1 hierarchical configs (experiment/stratum/environment/actions/agent).\n"
            "\n"
            "Options to fix:\n"
            "  1. Create adapter: v2.1 hierarchical -> legacy flat HamletConfig\n"
            "  2. Refactor RuntimeUniverse to accept v2.1 structure\n"
            "  3. Create RuntimeUniverseV21 for v2.1 configs\n"
            "\n"
            "For now, use as_single_level() to extract configs manually."
        )
