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
from pydantic import BaseModel, Field


class PerceptionConfig(BaseModel):
    """Perception configuration (currently empty placeholder)."""

    class Config:
        extra = "allow"  # Allow empty dict or future fields


class RangeMultiplierRange(BaseModel):
    """Range definition for range_multiplier modifier."""

    min: float = Field(..., description="Minimum value (inclusive)")
    max: float = Field(..., description="Maximum value (exclusive)")
    multiplier: float = Field(..., description="Multiplier to apply in this range")

    class Config:
        extra = "forbid"


class RangeMultiplierModifier(BaseModel):
    """Range-based multiplier modifier."""

    type: Literal["range_multiplier"] = Field(..., description="Modifier type")
    source: str = Field(..., description="Source meter/variable name")
    ranges: list[RangeMultiplierRange] = Field(..., description="Range definitions")

    class Config:
        extra = "forbid"


class ExtrinsicBonus(BaseModel):
    """Bonus term for extrinsic reward."""

    bar: str = Field(..., description="Meter name")
    weight: float = Field(..., description="Bonus weight")
    transform: Literal["linear", "quadratic", "exponential"] = Field(..., description="Transform function")

    class Config:
        extra = "forbid"


class ExtrinsicConfig(BaseModel):
    """Extrinsic reward configuration."""

    type: str = Field(..., description="Extrinsic strategy type")
    base: float = Field(..., description="Base reward value")
    bonuses: list[ExtrinsicBonus] | None = Field(None, description="Bonus terms (for constant_base_with_shaped_bonus)")

    class Config:
        extra = "forbid"


class AnnealingConfig(BaseModel):
    """Intrinsic weight annealing configuration."""

    enabled: bool = Field(..., description="Whether annealing is enabled")
    threshold: float = Field(..., description="Performance threshold to trigger annealing")
    decay_rate: float = Field(..., description="Decay rate per step")
    min_weight: float = Field(..., description="Minimum weight floor")

    class Config:
        extra = "forbid"


class IntrinsicConfig(BaseModel):
    """Intrinsic reward configuration."""

    strategy: Literal["rnd", "icm", "count_based", "adaptive_rnd", "none"] = Field(..., description="Intrinsic strategy type")
    base_weight: float = Field(..., description="Base intrinsic weight")
    apply_modifiers: list[str] = Field(..., description="Modifiers to apply")
    annealing: AnnealingConfig | None = Field(None, description="Annealing configuration")

    class Config:
        extra = "forbid"


class ShapingConfig(BaseModel):
    """Reward shaping configuration."""

    type: str = Field(..., description="Shaping bonus type")

    class Config:
        extra = "allow"  # Allow arbitrary fields for different shaping types


class CompositionConfig(BaseModel):
    """Reward composition configuration."""

    normalize: bool = Field(..., description="Whether to normalize total reward")
    clip: float | None = Field(None, description="Clip value (null = no clipping)")
    log_components: bool = Field(..., description="Whether to log reward components")
    log_modifiers: bool = Field(..., description="Whether to log modifier values")

    class Config:
        extra = "forbid"


class DriveConfig(BaseModel):
    """Drive (reward function) configuration."""

    version: str = Field(..., description="Drive config version")
    modifiers: dict[str, RangeMultiplierModifier] = Field(..., description="Reward modifiers")
    extrinsic: ExtrinsicConfig = Field(..., description="Extrinsic reward configuration")
    intrinsic: IntrinsicConfig = Field(..., description="Intrinsic reward configuration")
    shaping: list[ShapingConfig] = Field(..., description="Reward shaping configurations")
    composition: CompositionConfig = Field(..., description="Composition configuration")

    class Config:
        extra = "forbid"


class FeedforwardConfig(BaseModel):
    """Feedforward network configuration."""

    hidden_sizes: list[int] = Field(..., description="Hidden layer sizes")
    activation: Literal["relu", "tanh", "elu"] = Field(..., description="Activation function")

    class Config:
        extra = "forbid"


class VisionEncoderConfig(BaseModel):
    """Vision encoder configuration for recurrent networks."""

    conv_channels: list[int] = Field(..., description="Convolutional channel sizes")
    kernel_size: int = Field(..., description="Convolution kernel size", gt=0)
    stride: int = Field(..., description="Convolution stride", gt=0)
    output_dim: int = Field(..., description="Output dimension", gt=0)

    class Config:
        extra = "forbid"


class PositionEncoderConfig(BaseModel):
    """Position encoder configuration for recurrent networks."""

    hidden_size: int = Field(..., description="Hidden layer size", gt=0)

    class Config:
        extra = "forbid"


class MeterEncoderConfig(BaseModel):
    """Meter encoder configuration for recurrent networks."""

    hidden_size: int = Field(..., description="Hidden layer size", gt=0)

    class Config:
        extra = "forbid"


class LSTMConfig(BaseModel):
    """LSTM configuration for recurrent networks."""

    hidden_size: int = Field(..., description="LSTM hidden size", gt=0)
    num_layers: int = Field(..., description="Number of LSTM layers", gt=0)

    class Config:
        extra = "forbid"


class QHeadConfig(BaseModel):
    """Q-value head configuration for recurrent networks."""

    hidden_sizes: list[int] = Field(..., description="Hidden layer sizes")

    class Config:
        extra = "forbid"


class RecurrentConfig(BaseModel):
    """Recurrent network configuration."""

    vision_encoder: VisionEncoderConfig = Field(..., description="Vision encoder config")
    position_encoder: PositionEncoderConfig = Field(..., description="Position encoder config")
    meter_encoder: MeterEncoderConfig = Field(..., description="Meter encoder config")
    lstm: LSTMConfig = Field(..., description="LSTM config")
    q_head: QHeadConfig = Field(..., description="Q-value head config")

    class Config:
        extra = "forbid"


class OptimizerConfig(BaseModel):
    """Optimizer configuration."""

    type: Literal["adam", "rmsprop", "sgd"] = Field(..., description="Optimizer type")
    learning_rate: float = Field(..., description="Learning rate", gt=0)

    class Config:
        extra = "forbid"


class QLearningConfig(BaseModel):
    """Q-learning algorithm configuration."""

    algorithm: Literal["dqn", "double_dqn"] = Field(..., description="Q-learning algorithm")
    gamma: float = Field(..., description="Discount factor", ge=0, le=1)
    target_update_frequency: int = Field(..., description="Target network update frequency (steps)", gt=0)

    class Config:
        extra = "forbid"


class BrainConfig(BaseModel):
    """Brain (neural network) configuration."""

    architecture: Literal["feedforward", "recurrent"] = Field(..., description="Network architecture type")
    feedforward: FeedforwardConfig = Field(..., description="Feedforward network config")
    recurrent: RecurrentConfig = Field(..., description="Recurrent network config")
    optimizer: OptimizerConfig = Field(..., description="Optimizer config")
    q_learning: QLearningConfig = Field(..., description="Q-learning config")

    class Config:
        extra = "forbid"


class AgentConfigRoot(BaseModel):
    """Root structure for agent.yaml file."""

    version: str = Field(..., description="Config schema version")
    perception: PerceptionConfig | dict[str, Any] | None = Field(
        None, description="Perception configuration (placeholder, can be null or empty dict)"
    )
    drive: DriveConfig = Field(..., description="Drive (reward) configuration")
    brain: BrainConfig = Field(..., description="Brain (network) configuration")

    class Config:
        extra = "forbid"


class AgentConfig(BaseModel):
    """Top-level agent configuration.

    This DTO wraps the 'agent' key from agent.yaml.
    """

    agent: AgentConfigRoot = Field(..., description="Agent configuration")

    class Config:
        extra = "forbid"

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
