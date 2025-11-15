"""HamletConfig - Master configuration DTO for complete training setup.

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design: Composes all section DTOs (training, environment, population, curriculum,
exploration) and performs cross-config validation to ensure internal consistency.

This is the single entry point for loading complete training configurations.
"""

import logging
from pathlib import Path

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from townlet.config.affordance import AffordanceConfig
from townlet.config.bar import BarConfig
from townlet.config.cascade import CascadeConfig
from townlet.config.cues import CuesConfig
from townlet.config.curriculum import CurriculumConfig
from townlet.config.environment import TrainingEnvironmentConfig
from townlet.config.exploration import ExplorationConfig
from townlet.config.population import PopulationConfig
from townlet.config.training import TrainingConfig
from townlet.substrate.config import SubstrateConfig

logger = logging.getLogger(__name__)


class HamletConfig(BaseModel):
    """Complete HAMLET training configuration (master DTO).

    Composes all section configs and validates cross-config consistency.
    This is the single source of truth for a training run.

    ALL FIELDS REQUIRED (no defaults) - enforces operator accountability.

    Philosophy: If it affects the universe, it's in the config. No exceptions.

    Example:
        # v2.1: Use UniverseCompiler for hierarchical configs
        >>> from townlet.universe.compiler import UniverseCompiler
        >>> compiler = UniverseCompiler()
        >>> compiled = compiler.compile(Path("configs/default_curriculum"))
        >>> level_config = compiled.as_single_level("L0_0_minimal")
        >>> # Access configs: level_config["training"], level_config["bars"], etc.
    """

    # Section configs (ALL REQUIRED)
    training: TrainingConfig = Field(description="Training hyperparameters (device, episodes, epsilon, batch size)")
    environment: TrainingEnvironmentConfig = Field(description="Environment parameters (grid, observability, affordances, energy costs)")
    population: PopulationConfig = Field(description="Population parameters (agents, learning rate, replay buffer, network type)")
    curriculum: CurriculumConfig = Field(description="Curriculum parameters (episode length, advancement thresholds)")
    exploration: ExplorationConfig = Field(description="Exploration parameters (RND, intrinsic motivation, annealing)")
    bars: tuple[BarConfig, ...] = Field(description="Meter definitions loaded from bars.yaml")
    cascades: tuple[CascadeConfig, ...] = Field(description="Cascade relationships loaded from cascades.yaml")
    affordances: tuple[AffordanceConfig, ...] = Field(description="Affordance definitions loaded from affordances.yaml")
    substrate: SubstrateConfig = Field(description="Spatial substrate configuration (grid, continuous, aspatial)")
    cues: CuesConfig = Field(description="Cues configuration (cues.yaml) – required for Stage 5 cues pipeline")

    # Private attributes (not part of config, used for validation context)
    _config_dir: Path | None = PrivateAttr(default=None)

    def _validate_batch_size_vs_buffer(self) -> None:
        """Private method to perform batch_size vs buffer validation.

        Extracted from model_validator to allow manual invocation after setting _config_dir.
        """
        # Load brain.yaml to get replay_buffer_capacity (if we have _config_dir context)
        # In normal usage via UniverseCompiler, _config_dir is set
        # In direct construction (tests), _config_dir may not be set
        if self._config_dir is None:
            # Direct construction without _config_dir - skip validation
            # (Tests that directly construct HamletConfig won't have brain.yaml context)
            return

        from townlet.agent.brain_config import load_brain_config

        brain_yaml_path = self._config_dir / "brain.yaml"

        if not brain_yaml_path.exists():
            # brain.yaml missing - will be caught by PopulationConfig/TrainingConfig validators
            return

        brain_config = load_brain_config(self._config_dir)
        replay_capacity = brain_config.replay.capacity

        if self.training.batch_size > replay_capacity:
            raise ValueError(
                f"training.batch_size ({self.training.batch_size}) cannot exceed "
                f"brain.yaml:replay.capacity ({replay_capacity}). "
                f"Cannot sample {self.training.batch_size} transitions from buffer "
                f"that only holds {replay_capacity} transitions.\n\n"
                f"Fix: Either reduce batch_size in training.yaml or increase replay.capacity in brain.yaml."
            )

    @model_validator(mode="after")
    def validate_batch_size_vs_buffer(self) -> "HamletConfig":
        """Ensure batch_size <= replay_buffer_capacity.

        Can't sample more transitions than buffer holds.

        Note: replay_buffer_capacity is managed by brain.yaml (not training.yaml).
        This validator loads brain.yaml to access the capacity value for validation.
        """
        self._validate_batch_size_vs_buffer()
        return self

    @model_validator(mode="after")
    def validate_grid_capacity(self) -> "HamletConfig":
        """Warn if grid may be too small for agents + affordances.

        NOTE: This is a HINT for operator convenience, not strict enforcement.
        Operators may intentionally create crowded grids for challenge.

        NOTE: Grid dimensions are now read from substrate.yaml (single source of truth).
        For non-grid substrates (aspatial, continuous), this validation is skipped.
        """
        # Calculate grid cells from substrate (not environment config)
        grid_cells: int | None = None
        dimensions_str = ""

        if self.substrate.type == "grid" and self.substrate.grid is not None:
            if self.substrate.grid.topology == "square":
                grid_cells = self.substrate.grid.width * self.substrate.grid.height
                dimensions_str = f"{self.substrate.grid.width}×{self.substrate.grid.height}"
            elif self.substrate.grid.topology == "cubic":
                if self.substrate.grid.depth is not None:
                    grid_cells = self.substrate.grid.width * self.substrate.grid.height * self.substrate.grid.depth
                    dimensions_str = f"{self.substrate.grid.width}×{self.substrate.grid.height}×{self.substrate.grid.depth}"
        elif self.substrate.type == "gridnd" and self.substrate.gridnd is not None:
            grid_cells = 1
            for dim_size in self.substrate.gridnd.dimension_sizes:
                grid_cells *= dim_size
            dimensions_str = "×".join(str(d) for d in self.substrate.gridnd.dimension_sizes)
        else:
            # Continuous, aspatial - skip spatial capacity check
            return self

        if grid_cells is None:
            return self

        num_agents = self.population.num_agents

        # Estimate affordance count
        if self.environment.enabled_affordances is None:
            num_affordances = len(self.affordances)
        else:
            num_affordances = len(self.environment.enabled_affordances)

        total_entities = num_agents + num_affordances

        if total_entities > grid_cells:
            logger.warning(
                f"Grid capacity warning: {dimensions_str} grid "
                f"({grid_cells} cells) may not fit {num_agents} agents + "
                f"{num_affordances} affordances ({total_entities} entities total). "
                f"Entities may overlap or fail to place. "
                f"This may be intentional for high-density experiments."
            )
        elif total_entities > grid_cells * 0.8:
            logger.warning(
                f"Grid capacity warning: {dimensions_str} grid "
                f"is {total_entities}/{grid_cells} ({total_entities / grid_cells * 100:.0f}%) full. "
                f"High density may reduce agent mobility. "
                f"This may be intentional for your experiment."
            )

        return self
