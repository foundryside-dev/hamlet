"""Config DTO entrypoints for v2.1 hierarchical packs.

This module intentionally exposes ONLY the v2.1 configuration
data models used by the UniverseCompiler. Legacy training.yaml
and flat bars/cascades/affordances loaders are not re-exported.

Philosophy:
    - All behavioral parameters must be explicitly specified.
    - No hidden defaults in the configuration pipeline.
    - Config packs are the single source of truth.
"""

from townlet.config.actions_config import ActionsConfig
from townlet.config.affordances_v2_config import AffordancesV2Config, load_affordances_v2_config
from townlet.config.agent_config import AgentConfig
from townlet.config.bars_v2_config import BarsV2Config, load_bars_v2_config
from townlet.config.curriculum import load_curriculum_config
from townlet.config.curriculum_config import CurriculumConfig
from townlet.config.environment_config import EnvironmentConfig
from townlet.config.experiment_config import ExperimentConfig
from townlet.config.stratum_config import StratumConfig
from townlet.config.training_v2_config import TrainingV2Config, load_training_v2_config

# Version tracking for v2.1 schema evolution
CONFIG_SCHEMA_VERSION = "2.1.0"

__all__ = [
    "CONFIG_SCHEMA_VERSION",
    "ExperimentConfig",
    "StratumConfig",
    "EnvironmentConfig",
    "ActionsConfig",
    "AgentConfig",
    "BarsV2Config",
    "load_bars_v2_config",
    "AffordancesV2Config",
    "load_affordances_v2_config",
    "CurriculumConfig",
    "load_curriculum_config",
    "TrainingV2Config",
    "load_training_v2_config",
]
