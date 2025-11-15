"""Bars configuration DTO for Config v2.1 (curriculum-level).

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design: Validates bars.yaml structure from v2.1 hierarchical configs.
Includes meter parameters AND cascade parameters in same file.

Structure:
    bars:
      version: "1.0"
      meters: [...]      # How meters behave in this curriculum level
      cascades: [...]    # How meter relationships behave
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from townlet.config.base import format_validation_error, load_yaml_section

__all__ = [
    "MeterDepletionConfig",
    "MeterRecoveryConfig",
    "MeterBoundsConfig",
    "MeterConfig",
    "CascadeParamConfig",
    "BarsV2Config",
    "load_bars_v2_config",
]


class MeterDepletionConfig(BaseModel):
    """Meter depletion rates configuration."""

    model_config = ConfigDict(extra="forbid")

    passive: float = Field(description="Passive drain per timestep")
    move: float = Field(description="Drain per movement action")
    interact: float = Field(description="Drain per INTERACT action")


class MeterRecoveryConfig(BaseModel):
    """Meter recovery rates configuration."""

    model_config = ConfigDict(extra="forbid")

    natural: float = Field(description="Natural recovery per timestep (usually 0)")


class MeterBoundsConfig(BaseModel):
    """Meter bounds configuration."""

    model_config = ConfigDict(extra="forbid")

    min: float = Field(description="Minimum value")
    max: float = Field(description="Maximum value")
    lethal_min: bool = Field(description="Death if reaches min")
    lethal_max: bool = Field(description="Death if reaches max")

    @model_validator(mode="after")
    def validate_bounds_order(self) -> "MeterBoundsConfig":
        """Ensure min < max."""
        if self.min >= self.max:
            raise ValueError(f"bounds.min ({self.min}) must be < bounds.max ({self.max}). " f"Got reversed or equal bounds.")
        return self


class MeterConfig(BaseModel):
    """Meter (bar) configuration for curriculum level.

    Defines how a specific meter behaves in this curriculum level.
    Must match meter names from environment.yaml.

    Example:
        >>> meter = MeterConfig(
        ...     name="energy",
        ...     initial=1.0,
        ...     depletion=MeterDepletionConfig(passive=0.01, move=0.02, interact=0.05),
        ...     recovery=MeterRecoveryConfig(natural=0.0),
        ...     bounds=MeterBoundsConfig(min=0.0, max=1.0, lethal_min=True, lethal_max=False),
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="Meter name (must match environment.yaml)")
    initial: float = Field(description="Starting value [0.0, 1.0]")
    depletion: MeterDepletionConfig = Field(description="Depletion rates")
    recovery: MeterRecoveryConfig = Field(description="Recovery rates")
    bounds: MeterBoundsConfig = Field(description="Value bounds and lethality")

    @model_validator(mode="after")
    def validate_initial_in_bounds(self) -> "MeterConfig":
        """Ensure initial value is within [min, max]."""
        if not (self.bounds.min <= self.initial <= self.bounds.max):
            raise ValueError(
                f"initial value ({self.initial}) must be within bounds "
                f"[{self.bounds.min}, {self.bounds.max}]. "
                f"Got: initial={self.initial}"
            )
        return self


class CascadeParamConfig(BaseModel):
    """Cascade parameter configuration for curriculum level.

    Defines how a cascade behaves in this curriculum level.
    Must match cascades from environment.yaml cascade_graph.

    Example:
        >>> cascade = CascadeParamConfig(
        ...     source="satiation",
        ...     target="health",
        ...     threshold=0.3,
        ...     strength=0.004,
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, description="Source meter name (must match cascade_graph)")
    target: str = Field(min_length=1, description="Target meter name (must match cascade_graph)")
    threshold: float = Field(ge=0.0, le=1.0, description="Trigger when source < threshold")
    strength: float = Field(description="Damage rate (0.0 = explicit disable)")

    @model_validator(mode="after")
    def validate_not_self_cascade(self) -> "CascadeParamConfig":
        """Source and target must be different meters."""
        if self.source == self.target:
            raise ValueError(
                f"Cascade source and target cannot be the same meter. "
                f"Got: source='{self.source}', target='{self.target}'. "
                f"Self-cascades are not allowed."
            )
        return self


class BarsV2Config(BaseModel):
    """Bars configuration for Config v2.1.

    Combines meter parameters and cascade parameters in same file.
    ALL FIELDS REQUIRED (no defaults) - enforces operator accountability.

    Validation:
    - All meters from environment.yaml MUST be present
    - All cascades from environment.yaml cascade_graph MUST be present
    - To disable a cascade: Set strength: 0.0 (explicit disable, not omission)

    Example:
        >>> config = BarsV2Config(
        ...     version="1.0",
        ...     meters=[...],
        ...     cascades=[...],
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(description="Config version")
    meters: list[MeterConfig] = Field(description="Meter parameters for this curriculum level")
    cascades: list[CascadeParamConfig] = Field(description="Cascade parameters for this curriculum level")

    @field_validator("meters")
    @classmethod
    def validate_unique_meter_names(cls, meters: list[MeterConfig]) -> list[MeterConfig]:
        """Ensure meter names are unique."""
        names = [m.name for m in meters]
        duplicates = [name for name in names if names.count(name) > 1]
        if duplicates:
            raise ValueError(f"Duplicate meter names found: {list(set(duplicates))}. " f"Each meter must have a unique name.")
        return meters

    @field_validator("cascades")
    @classmethod
    def validate_unique_cascades(cls, cascades: list[CascadeParamConfig]) -> list[CascadeParamConfig]:
        """Ensure cascade pairs are unique."""
        pairs = [(c.source, c.target) for c in cascades]
        duplicates = [pair for pair in pairs if pairs.count(pair) > 1]
        if duplicates:
            raise ValueError(f"Duplicate cascade pairs found: {list(set(duplicates))}. " f"Each (source, target) pair must be unique.")
        return cascades


def load_bars_v2_config(config_dir: Path) -> BarsV2Config:
    """Load and validate bars configuration (v2.1 format).

    Args:
        config_dir: Directory containing bars.yaml (curriculum level)

    Returns:
        Validated BarsV2Config

    Raises:
        FileNotFoundError: If bars.yaml not found
        ValueError: If validation fails (with helpful error message)

    Example:
        >>> config = load_bars_v2_config(Path("configs/default_curriculum/levels/L1_full_observability"))
        >>> print(f"Loaded {len(config.meters)} meters, {len(config.cascades)} cascades")
        Loaded 8 meters, 5 cascades
    """
    try:
        data = load_yaml_section(config_dir, "bars.yaml", "bars")
        return BarsV2Config(**data)
    except ValidationError as e:
        raise ValueError(format_validation_error(e, "bars.yaml")) from e
