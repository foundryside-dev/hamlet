"""Training configuration DTO for Config v2.1 (curriculum-level).

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design: Validates training.yaml structure from v2.1 hierarchical configs.
Includes runtime orchestration settings for this curriculum level.

Structure:
    training:
      version: "1.0"
      population: {...}
      enabled_actions: {...}    # Optional curriculum-level action control
      q_learning: {...}         # Curriculum-level overrides
      replay_buffer: {...}
      exploration: {...}
      intrinsic: {...}
      training_loop: {...}
      curriculum: {...}
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from townlet.config.base import format_validation_error, load_yaml_section

__all__ = [
    "PopulationConfig",
    "EnabledActionsConfig",
    "QLearningConfig",
    "ReplayBufferConfig",
    "ExplorationConfig",
    "RNDConfig",
    "AnnealingConfig",
    "IntrinsicConfig",
    "EvaluationConfig",
    "CheckpointingConfig",
    "TrainingLoopConfig",
    "AdversarialCurriculumConfig",
    "CurriculumStrategyConfig",
    "TrainingV2Config",
    "load_training_v2_config",
]


class PopulationConfig(BaseModel):
    """Population settings configuration."""

    model_config = ConfigDict(extra="forbid")

    size: int = Field(gt=0, description="Number of parallel agents")


class EnabledActionsConfig(BaseModel):
    """Curriculum-level action control configuration.

    Enables actions that have enabled_by_default: false in actions.yaml.
    Cannot disable actions that have enabled_by_default: true.
    """

    model_config = ConfigDict(extra="forbid")

    custom: list[str] = Field(default_factory=list, description="Custom actions to enable for this level")

    @field_validator("custom")
    @classmethod
    def validate_unique_actions(cls, actions: list[str]) -> list[str]:
        """Ensure action names are unique."""
        duplicates = [action for action in actions if actions.count(action) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate action names in enabled_actions.custom: {list(set(duplicates))}. " f"Each action must appear only once."
            )
        return actions


class QLearningConfig(BaseModel):
    """Q-learning hyperparameters configuration (curriculum-level overrides).

    These override agent.yaml brain settings for this curriculum level.
    """

    model_config = ConfigDict(extra="forbid")

    use_double_dqn: bool = Field(description="Enable Double DQN for this level")
    gamma: float = Field(gt=0.0, le=1.0, description="Discount factor")
    learning_rate: float = Field(gt=0.0, description="Adam learning rate")
    target_update_frequency: int = Field(gt=0, description="Update target network every N steps")


class ReplayBufferConfig(BaseModel):
    """Replay buffer configuration."""

    model_config = ConfigDict(extra="forbid")

    capacity: int = Field(gt=0, description="Replay buffer capacity")
    batch_size: int = Field(gt=0, description="Training batch size")
    min_size: int = Field(gt=0, description="Start training after N transitions")

    @model_validator(mode="after")
    def validate_min_size_le_capacity(self) -> "ReplayBufferConfig":
        """Ensure min_size <= capacity."""
        if self.min_size > self.capacity:
            raise ValueError(
                f"replay_buffer.min_size ({self.min_size}) must be <= capacity ({self.capacity}). "
                f"Cannot start training before buffer has enough capacity."
            )
        return self

    @model_validator(mode="after")
    def validate_batch_size_le_min_size(self) -> "ReplayBufferConfig":
        """Ensure batch_size <= min_size."""
        if self.batch_size > self.min_size:
            raise ValueError(
                f"replay_buffer.batch_size ({self.batch_size}) must be <= min_size ({self.min_size}). "
                f"Cannot sample more transitions than minimum buffer size."
            )
        return self


class ExplorationConfig(BaseModel):
    """Epsilon-greedy exploration configuration."""

    model_config = ConfigDict(extra="forbid")

    epsilon_start: float = Field(ge=0.0, le=1.0, description="Initial exploration rate (1.0 = 100% random)")
    epsilon_end: float = Field(ge=0.0, le=1.0, description="Minimum exploration rate (floor)")
    epsilon_decay: float = Field(gt=0.0, lt=1.0, description="Decay per episode (< 1.0)")

    @model_validator(mode="after")
    def validate_epsilon_start_ge_end(self) -> "ExplorationConfig":
        """Ensure epsilon_start >= epsilon_end."""
        if self.epsilon_start < self.epsilon_end:
            raise ValueError(
                f"exploration.epsilon_start ({self.epsilon_start}) must be >= "
                f"epsilon_end ({self.epsilon_end}). "
                f"Exploration cannot start below the minimum threshold."
            )
        return self


class RNDConfig(BaseModel):
    """Random Network Distillation configuration."""

    model_config = ConfigDict(extra="forbid")

    feature_dim: int = Field(gt=0, description="RND feature dimension")
    learning_rate: float = Field(gt=0.0, description="RND learning rate")


class AnnealingConfig(BaseModel):
    """Intrinsic reward annealing configuration."""

    model_config = ConfigDict(extra="forbid")

    threshold: float = Field(gt=0.0, description="Survivors metric threshold")
    decay_rate: float = Field(gt=0.0, lt=1.0, description="Annealing decay rate")
    min_weight: float = Field(ge=0.0, le=1.0, description="Minimum intrinsic weight")


class IntrinsicConfig(BaseModel):
    """Intrinsic exploration configuration."""

    model_config = ConfigDict(extra="forbid")

    rnd: RNDConfig = Field(description="RND configuration")
    annealing: AnnealingConfig = Field(description="Annealing configuration")
    initial_weight: float = Field(
        default=1.0,
        ge=0.0,
        description=("Initial intrinsic reward weight (vs extrinsic). " "For inference runs, set to 0.0 for near-greedy behavior."),
    )
    min_survival_fraction: float = Field(
        default=0.4,
        gt=0.0,
        lt=1.0,
        description=(
            "Minimum mean survival as fraction of max_episode_length before allowing annealing "
            "(prevents 'stable failure' from triggering annealing)."
        ),
    )
    survival_window: int = Field(
        default=100,
        gt=0,
        description="Window size (episodes) for tracking survival consistency when annealing intrinsic weight.",
    )


class EvaluationConfig(BaseModel):
    """Evaluation configuration."""

    model_config = ConfigDict(extra="forbid")

    interval: int = Field(gt=0, description="Evaluate every N episodes")
    num_episodes: int = Field(gt=0, description="Number of episodes per evaluation")


class CheckpointingConfig(BaseModel):
    """Checkpointing configuration."""

    model_config = ConfigDict(extra="forbid")

    interval: int = Field(gt=0, description="Save checkpoint every N episodes")
    keep_last: int = Field(gt=0, description="Keep last N checkpoints")


class TrainingLoopConfig(BaseModel):
    """Training loop configuration."""

    model_config = ConfigDict(extra="forbid")

    max_episodes: int = Field(gt=0, description="Total episodes to train")
    max_steps_per_episode: int = Field(gt=0, description="Maximum steps per episode")
    evaluation: EvaluationConfig = Field(description="Evaluation configuration")
    checkpointing: CheckpointingConfig = Field(description="Checkpointing configuration")
    train_frequency: int = Field(
        default=4,
        gt=0,
        description="Train Q-network every N environment steps (default 4).",
    )
    sequence_length: int = Field(
        default=8,
        gt=0,
        description="Sequence length for recurrent agents when using sequential replay (default 8).",
    )
    max_grad_norm: float = Field(
        default=10.0,
        gt=0.0,
        description="Gradient clipping threshold for Q-network updates (default 10.0).",
    )


class AdversarialCurriculumConfig(BaseModel):
    """Adversarial curriculum configuration."""

    model_config = ConfigDict(extra="forbid")

    difficulty_metric: Literal["survival_rate"] = Field(description="Difficulty metric to track")
    adaptation_rate: float = Field(gt=0.0, le=1.0, description="Difficulty adaptation rate")
    min_difficulty: float = Field(ge=0.0, le=1.0, description="Minimum difficulty")
    max_difficulty: float = Field(ge=0.0, le=1.0, description="Maximum difficulty")

    @model_validator(mode="after")
    def validate_min_le_max(self) -> "AdversarialCurriculumConfig":
        """Ensure min_difficulty <= max_difficulty."""
        if self.min_difficulty > self.max_difficulty:
            raise ValueError(
                f"curriculum.adversarial.min_difficulty ({self.min_difficulty}) must be <= " f"max_difficulty ({self.max_difficulty})."
            )
        return self


class CurriculumStrategyConfig(BaseModel):
    """Curriculum progression strategy configuration."""

    model_config = ConfigDict(extra="forbid")

    strategy: Literal["static", "adversarial"] = Field(description="Curriculum strategy")
    adversarial: AdversarialCurriculumConfig | None = Field(
        default=None, description="Adversarial curriculum settings (required when strategy='adversarial')"
    )

    @model_validator(mode="after")
    def validate_adversarial_required_when_strategy_adversarial(self) -> "CurriculumStrategyConfig":
        """If strategy='adversarial', adversarial config must be present."""
        if self.strategy == "adversarial" and self.adversarial is None:
            raise ValueError(
                "curriculum.adversarial is required when curriculum.strategy='adversarial'. "
                "Provide adversarial configuration or set strategy='static'."
            )
        return self


class TrainingV2Config(BaseModel):
    """Training configuration for Config v2.1.

    Controls training process and runtime behavior for this curriculum level.
    ALL FIELDS REQUIRED (no defaults) - enforces operator accountability.

    Example:
        >>> config = TrainingV2Config(
        ...     version="1.0",
        ...     population=PopulationConfig(size=512),
        ...     enabled_actions=EnabledActionsConfig(custom=["REST", "MEDITATE"]),
        ...     q_learning=QLearningConfig(...),
        ...     replay_buffer=ReplayBufferConfig(...),
        ...     exploration=ExplorationConfig(...),
        ...     intrinsic=IntrinsicConfig(...),
        ...     training_loop=TrainingLoopConfig(...),
        ...     curriculum=CurriculumStrategyConfig(...),
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(description="Config version")
    population: PopulationConfig = Field(description="Population settings")
    enabled_affordances: list[str] | None = Field(
        description=("Subset of affordances to deploy for this curriculum level " "(null = deploy all affordances from environment.yaml).")
    )
    randomize_affordances: bool = Field(
        description=(
            "true = randomize affordance positions each episode, " "false = use configured positions from affordances.yaml/optimization."
        )
    )
    enabled_actions: EnabledActionsConfig | None = Field(
        default=None, description="Optional curriculum-level action control (null = use defaults from actions.yaml)"
    )
    q_learning: QLearningConfig = Field(description="Q-learning hyperparameters (curriculum-level overrides)")
    replay_buffer: ReplayBufferConfig = Field(description="Replay buffer configuration")
    exploration: ExplorationConfig = Field(description="Epsilon-greedy exploration configuration")
    intrinsic: IntrinsicConfig = Field(description="Intrinsic exploration configuration")
    training_loop: TrainingLoopConfig = Field(description="Training loop configuration")
    curriculum: CurriculumStrategyConfig = Field(description="Curriculum progression strategy")


def load_training_v2_config(config_dir: Path) -> TrainingV2Config:
    """Load and validate training configuration (v2.1 format).

    Args:
        config_dir: Directory containing training.yaml (curriculum level)

    Returns:
        Validated TrainingV2Config

    Raises:
        FileNotFoundError: If training.yaml not found
        ValueError: If validation fails (with helpful error message)

    Example:
        >>> config = load_training_v2_config(Path("configs/default_curriculum/levels/L1_full_observability"))
        >>> print(f"Population size: {config.population.size}")
        Population size: 512
    """
    try:
        data = load_yaml_section(config_dir, "training.yaml", "training")
        return TrainingV2Config(**data)
    except ValidationError as e:
        raise ValueError(format_validation_error(e, "training.yaml")) from e
