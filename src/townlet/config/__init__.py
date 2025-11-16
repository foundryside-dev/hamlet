"""Configuration DTOs for UNIVERSE_AS_CODE validation.

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design Decision (TASK-003):
- Created 8 core DTOs: Training, Environment, Population, Curriculum, Exploration, Bar, Cascade, Affordance
- TrainingEnvironmentConfig (not EnvironmentConfig) - avoids conflict with cascade_config.EnvironmentConfig
- BarConfig, CascadeConfig, AffordanceConfig - BASIC structural validation (TASK-003)
  - Cross-file validation (meter references) deferred to TASK-004A
  - Advanced features (capabilities, effect pipelines) deferred to TASK-004B
- Added ExplorationConfig - found in all config packs but missing from original plan

Naming Strategy:
- Training-specific configs use "Training" prefix to distinguish from game mechanics
- Example: TrainingEnvironmentConfig vs cascade_config.EnvironmentConfig
- Prevents import conflicts and clarifies purpose
"""

# Import DTOs for convenient access
from townlet.config.affordance import (
    AffordanceConfig,
    AffordanceConfigCollection,
    load_affordances_config,
)
from townlet.config.bar import BarConfig, BarsConfig, load_bars_config
from townlet.config.cascade import CascadeConfig, CascadesConfig, load_cascades_config
from townlet.config.cues import CuesConfig, load_cues_config
from townlet.config.curriculum import CurriculumConfig, load_curriculum_config
from townlet.config.environment import (
    TrainingEnvironmentConfig,
    load_environment_config,
)
from townlet.config.exploration import ExplorationConfig, load_exploration_config

# Version tracking for schema evolution
CONFIG_SCHEMA_VERSION = "1.0.0"

__all__ = [
    "CONFIG_SCHEMA_VERSION",
    "TrainingEnvironmentConfig",
    "load_environment_config",
    "CurriculumConfig",
    "load_curriculum_config",
    "ExplorationConfig",
    "load_exploration_config",
    "BarConfig",
    "BarsConfig",
    "load_bars_config",
    "CascadeConfig",
    "CascadesConfig",
    "load_cascades_config",
    "AffordanceConfig",
    "AffordanceConfigCollection",
    "load_affordances_config",
    "CuesConfig",
    "load_cues_config",
]
