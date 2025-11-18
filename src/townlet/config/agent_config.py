"""Agent-level configuration DTO.

This module defines the Pydantic DTO for agent.yaml files in the v2.1
configuration system. An agent config defines perception, drive (reward function),
and brain (neural network architecture and training).

Example:
    >>> config = AgentConfig.from_yaml(Path("configs/default_curriculum/agent.yaml"))
    >>> print(config.brain.architecture)
    'feedforward'
    >>> print(config.drive.extrinsic.type)
    'constant_base_with_shaped_bonus'
"""

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PerceptionConfig(BaseModel):
    """Perception configuration (currently empty placeholder)."""

    model_config = ConfigDict(extra="allow")  # Allow empty dict or future fields


class RangeMultiplierRange(BaseModel):
    """Range definition for range_multiplier modifier."""

    min: float = Field(..., description="Minimum value (inclusive)")
    max: float = Field(..., description="Maximum value (exclusive)")
    multiplier: float = Field(..., description="Multiplier to apply in this range")

    model_config = ConfigDict(extra="forbid")


class RangeMultiplierModifier(BaseModel):
    """Range-based multiplier modifier."""

    type: Literal["range_multiplier"] = Field(..., description="Modifier type")
    source: str = Field(..., description="Source meter/variable name")
    ranges: list[RangeMultiplierRange] = Field(..., description="Range definitions")

    model_config = ConfigDict(extra="forbid")


class ExtrinsicBonus(BaseModel):
    """Bonus term for extrinsic reward."""

    bar: str = Field(..., description="Meter name")
    weight: float = Field(..., description="Bonus weight")
    transform: Literal["linear", "quadratic", "exponential"] = Field(..., description="Transform function")

    model_config = ConfigDict(extra="forbid")


class ExtrinsicConfig(BaseModel):
    """Extrinsic reward configuration."""

    type: str = Field(..., description="Extrinsic strategy type")
    base: float = Field(..., description="Base reward value")
    bonuses: list[ExtrinsicBonus] | None = Field(None, description="Bonus terms (for constant_base_with_shaped_bonus)")

    model_config = ConfigDict(extra="forbid")


class AnnealingConfig(BaseModel):
    """Intrinsic weight annealing configuration."""

    enabled: bool = Field(..., description="Whether annealing is enabled")
    threshold: float = Field(..., description="Performance threshold to trigger annealing")
    decay_rate: float = Field(..., description="Decay rate per step")
    min_weight: float = Field(..., description="Minimum weight floor")

    model_config = ConfigDict(extra="forbid")


class IntrinsicConfig(BaseModel):
    """Intrinsic reward configuration."""

    strategy: Literal["rnd", "icm", "count_based", "adaptive_rnd", "none"] = Field(..., description="Intrinsic strategy type")
    base_weight: float = Field(..., description="Base intrinsic weight")
    apply_modifiers: list[str] = Field(..., description="Modifiers to apply")
    annealing: AnnealingConfig | None = Field(None, description="Annealing configuration")

    model_config = ConfigDict(extra="forbid")


class ShapingConfig(BaseModel):
    """Reward shaping configuration."""

    type: str = Field(..., description="Shaping bonus type")

    model_config = ConfigDict(extra="allow")  # Allow arbitrary fields for different shaping types


class CompositionConfig(BaseModel):
    """Reward composition configuration."""

    normalize: bool = Field(..., description="Whether to normalize total reward")
    clip: float | None = Field(None, description="Clip value (null = no clipping)")
    log_components: bool = Field(..., description="Whether to log reward components")
    log_modifiers: bool = Field(..., description="Whether to log modifier values")

    model_config = ConfigDict(extra="forbid")


class DriveConfig(BaseModel):
    """Drive (reward function) configuration."""

    version: str = Field(..., description="Drive config version")
    modifiers: dict[str, RangeMultiplierModifier] = Field(..., description="Reward modifiers")
    extrinsic: ExtrinsicConfig = Field(..., description="Extrinsic reward configuration")
    intrinsic: IntrinsicConfig = Field(..., description="Intrinsic reward configuration")
    shaping: list[ShapingConfig] = Field(..., description="Reward shaping configurations")
    composition: CompositionConfig = Field(..., description="Composition configuration")

    model_config = ConfigDict(extra="forbid")


class FeedforwardConfig(BaseModel):
    """Feedforward network configuration."""

    hidden_sizes: list[int] = Field(..., description="Hidden layer sizes")
    activation: Literal["relu", "tanh", "elu"] = Field(..., description="Activation function")

    model_config = ConfigDict(extra="forbid")


class VisionEncoderConfig(BaseModel):
    """Vision encoder configuration for recurrent networks."""

    conv_channels: list[int] = Field(..., description="Convolutional channel sizes")
    kernel_size: int = Field(..., description="Convolution kernel size", gt=0)
    stride: int = Field(..., description="Convolution stride", gt=0)
    output_dim: int = Field(..., description="Output dimension", gt=0)

    model_config = ConfigDict(extra="forbid")


class PositionEncoderConfig(BaseModel):
    """Position encoder configuration for recurrent networks."""

    hidden_size: int = Field(..., description="Hidden layer size", gt=0)

    model_config = ConfigDict(extra="forbid")


class MeterEncoderConfig(BaseModel):
    """Meter encoder configuration for recurrent networks."""

    hidden_size: int = Field(..., description="Hidden layer size", gt=0)

    model_config = ConfigDict(extra="forbid")


class LSTMConfig(BaseModel):
    """LSTM configuration for recurrent networks."""

    hidden_size: int = Field(..., description="LSTM hidden size", gt=0)
    num_layers: int = Field(..., description="Number of LSTM layers", gt=0)

    model_config = ConfigDict(extra="forbid")


class QHeadConfig(BaseModel):
    """Q-value head configuration for recurrent networks."""

    hidden_sizes: list[int] = Field(..., description="Hidden layer sizes")

    model_config = ConfigDict(extra="forbid")


class RecurrentConfig(BaseModel):
    """Recurrent network configuration."""

    vision_encoder: VisionEncoderConfig = Field(..., description="Vision encoder config")
    position_encoder: PositionEncoderConfig = Field(..., description="Position encoder config")
    meter_encoder: MeterEncoderConfig = Field(..., description="Meter encoder config")
    lstm: LSTMConfig = Field(..., description="LSTM config")
    q_head: QHeadConfig = Field(..., description="Q-value head config")

    model_config = ConfigDict(extra="forbid")


class OptimizerScheduleConfig(BaseModel):
    """Learning rate schedule configuration for agent.yaml.

    Mirrors the BrainConfig ScheduleConfig options at a schema level so
    schedule behavior is fully configuration-driven.
    """

    type: Literal["constant", "step_decay", "cosine", "exponential"] = Field(..., description="Learning rate schedule type")
    step_size: int | None = Field(
        default=None,
        gt=0,
        description="Step size for step_decay schedule (required when type='step_decay')",
    )
    gamma: float | None = Field(
        default=None,
        gt=0.0,
        lt=1.0,
        description="Multiplicative factor for step_decay/exponential schedules (required for those types)",
    )
    t_max: int | None = Field(
        default=None,
        gt=0,
        description="Maximum iterations for cosine schedule (required when type='cosine')",
    )
    eta_min: float | None = Field(
        default=None,
        ge=0.0,
        description="Minimum learning rate for cosine schedule (required when type='cosine')",
    )

    model_config = ConfigDict(extra="forbid")


class OptimizerConfig(BaseModel):
    """Optimizer configuration."""

    type: Literal["adam", "rmsprop", "sgd"] = Field(..., description="Optimizer type")
    learning_rate: float = Field(..., description="Learning rate", gt=0)

    # Optional optimizer-specific parameters. These are required for certain
    # optimizer types and validated when constructing the runtime BrainConfig.
    adam_beta1: float | None = Field(
        default=None,
        ge=0.0,
        lt=1.0,
        description="Adam beta1 parameter (required when type='adam')",
    )
    adam_beta2: float | None = Field(
        default=None,
        ge=0.0,
        lt=1.0,
        description="Adam beta2 parameter (required when type='adam')",
    )
    adam_eps: float | None = Field(
        default=None,
        gt=0.0,
        description="Adam epsilon parameter (required when type='adam')",
    )

    sgd_momentum: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="SGD momentum (required when type='sgd')",
    )
    sgd_nesterov: bool | None = Field(
        default=None,
        description="Use Nesterov momentum (required when type='sgd')",
    )

    rmsprop_alpha: float | None = Field(
        default=None,
        ge=0.0,
        lt=1.0,
        description="RMSprop alpha/decay (required when type='rmsprop')",
    )
    rmsprop_eps: float | None = Field(
        default=None,
        gt=0.0,
        description="RMSprop epsilon (required when type='rmsprop')",
    )

    weight_decay: float = Field(..., ge=0.0, description="L2 weight decay")
    schedule: OptimizerScheduleConfig = Field(..., description="Learning rate schedule configuration")

    model_config = ConfigDict(extra="forbid")


class QLearningConfig(BaseModel):
    """Q-learning algorithm configuration."""

    algorithm: Literal["dqn", "double_dqn"] = Field(..., description="Q-learning algorithm")
    gamma: float = Field(..., description="Discount factor", ge=0, le=1)
    target_update_frequency: int = Field(..., description="Target network update frequency (steps)", gt=0)

    model_config = ConfigDict(extra="forbid")


class BrainConfig(BaseModel):
    """Brain (neural network) configuration."""

    architecture: Literal["feedforward", "recurrent"] = Field(..., description="Network architecture type")
    feedforward: FeedforwardConfig = Field(..., description="Feedforward network config")
    recurrent: RecurrentConfig = Field(..., description="Recurrent network config")
    optimizer: OptimizerConfig = Field(..., description="Optimizer config")
    q_learning: QLearningConfig = Field(..., description="Q-learning config")
    loss: "LossConfig" = Field(..., description="Loss function configuration")

    model_config = ConfigDict(extra="forbid")


class LossConfig(BaseModel):
    """Loss function configuration."""

    type: Literal["mse", "huber", "smooth_l1"] = Field(..., description="Loss function type")
    huber_delta: float = Field(..., gt=0.0, description="Delta parameter for Huber/smooth_l1")

    model_config = ConfigDict(extra="forbid")


class AgentConfigRoot(BaseModel):
    """Root structure for agent.yaml file."""

    version: str = Field(..., description="Config schema version")
    perception: PerceptionConfig | dict[str, Any] | None = Field(
        None, description="Perception configuration (placeholder, can be null or empty dict)"
    )
    drive: DriveConfig = Field(..., description="Drive (reward) configuration")
    brain: BrainConfig = Field(..., description="Brain (network) configuration")

    model_config = ConfigDict(extra="forbid")


class AgentConfig(BaseModel):
    """Top-level agent configuration.

    This DTO wraps the 'agent' key from agent.yaml.
    """

    agent: AgentConfigRoot = Field(..., description="Agent configuration")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentConfig":
        """Load agent configuration from YAML file.

        Args:
            path: Path to agent.yaml file

        Returns:
            AgentConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
