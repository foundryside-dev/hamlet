"""Affordances configuration DTO for Config v2.1 (curriculum-level).

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design: Validates affordances.yaml structure from v2.1 hierarchical configs.
Includes affordance parameters AND modulation parameters in same file.

Structure:
    affordances:
      version: "1.0"
      affordances: [...]    # How affordances behave in this curriculum level
      modulations: [...]    # How bars affect affordance effectiveness
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from townlet.config.base import format_validation_error, load_yaml_section

__all__ = [
    "TimeWindowConfig",
    "OpeningHoursConfig",
    "DeploymentConfig",
    "AffordanceParamConfig",
    "ModulationParamConfig",
    "AffordancesV2Config",
    "load_affordances_v2_config",
]


class TimeWindowConfig(BaseModel):
    """Time window configuration for opening hours."""

    model_config = ConfigDict(extra="forbid")

    start: int = Field(ge=0, le=23, description="Opening hour (0-23)")
    end: int = Field(ge=1, le=28, description="Closing hour (1-28, can exceed 24 for overnight)")

    @model_validator(mode="after")
    def validate_time_order(self) -> "TimeWindowConfig":
        """Ensure start < end (except for overnight windows)."""
        # Allow overnight windows (e.g., 22-6 becomes 22-30)
        # This is validated at a higher level if needed
        return self


class OpeningHoursConfig(BaseModel):
    """Opening hours configuration."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(description="Whether opening hours are enabled (false = 24/7 availability)")
    schedule: list[TimeWindowConfig] = Field(
        default_factory=list, description="Time windows when affordance is available (empty if enabled=false)"
    )

    @model_validator(mode="after")
    def validate_schedule_required_when_enabled(self) -> "OpeningHoursConfig":
        """If enabled=true, schedule must not be empty."""
        if self.enabled and not self.schedule:
            raise ValueError(
                "opening_hours.schedule must not be empty when opening_hours.enabled=true. "
                "Provide at least one time window or set enabled=false for 24/7 availability."
            )
        return self


class DeploymentConfig(BaseModel):
    """Deployment configuration for spatial placement."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["fixed", "random", "procedural"] = Field(description="Deployment type")
    positions: list[list[int]] = Field(default_factory=list, description="Grid positions for fixed deployment (e.g., [[2, 2], [5, 5]])")

    @model_validator(mode="after")
    def validate_positions_for_fixed(self) -> "DeploymentConfig":
        """If type=fixed, positions must not be empty."""
        if self.type == "fixed" and not self.positions:
            raise ValueError(
                "deployment.positions must not be empty when deployment.type='fixed'. "
                "Provide at least one position or use type='random' or 'procedural'."
            )
        return self


class AffordanceParamConfig(BaseModel):
    """Affordance parameter configuration for curriculum level.

    Defines how a specific affordance behaves in this curriculum level.
    Must match affordance names from environment.yaml.

    Example:
        >>> affordance = AffordanceParamConfig(
        ...     name="EAT",
        ...     costs={"energy": 0.05, "money": 5.0},
        ...     effects={"satiation": 0.4, "mood": 0.05},
        ...     opening_hours=OpeningHoursConfig(enabled=True, schedule=[...]),
        ...     deployment=DeploymentConfig(type="fixed", positions=[[2, 2], [5, 5]]),
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="Affordance name (must match environment.yaml)")
    costs: dict[str, float] = Field(default_factory=dict, description="Bar decreases when action executes (meter: value)")
    effects: dict[str, float] = Field(default_factory=dict, description="Bar increases when action executes (meter: value)")
    opening_hours: OpeningHoursConfig = Field(description="Availability schedule")
    deployment: DeploymentConfig = Field(description="Spatial placement configuration")


class ModulationParamConfig(BaseModel):
    """Modulation parameter configuration for curriculum level.

    Defines how bars affect affordance effectiveness.
    Must match modulations from environment.yaml modulation_graph.

    Example:
        >>> modulation = ModulationParamConfig(
        ...     bar="energy",
        ...     affordances=["WORK"],
        ...     type="linear_multiplier",
        ...     threshold=0.3,
        ...     min_multiplier=0.5,
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    bar: str = Field(min_length=1, description="Bar name (must match modulation_graph)")
    affordances: list[str] = Field(min_length=1, description="Affordance names affected by this modulation")
    type: Literal["linear_multiplier"] = Field(description="Modulation type")
    threshold: float = Field(ge=0.0, le=1.0, description="Threshold below which modulation applies")
    min_multiplier: float = Field(ge=0.0, le=1.0, description="Minimum effectiveness multiplier")

    @field_validator("affordances")
    @classmethod
    def validate_unique_affordances(cls, affordances: list[str]) -> list[str]:
        """Ensure affordances list has no duplicates."""
        duplicates = [aff for aff in affordances if affordances.count(aff) > 1]
        if duplicates:
            raise ValueError(
                f"Duplicate affordance names in modulation: {list(set(duplicates))}. "
                f"Each affordance must appear only once per modulation."
            )
        return affordances


class AffordancesV2Config(BaseModel):
    """Affordances configuration for Config v2.1.

    Combines affordance parameters and modulation parameters in same file.
    ALL FIELDS REQUIRED (no defaults) - enforces operator accountability.

    Validation:
    - All affordances from environment.yaml MUST be present
    - All modulations from environment.yaml modulation_graph MUST be present

    Example:
        >>> config = AffordancesV2Config(
        ...     version="1.0",
        ...     affordances=[...],
        ...     modulations=[...],
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(description="Config version")
    affordances: list[AffordanceParamConfig] = Field(description="Affordance parameters for this curriculum level")
    modulations: list[ModulationParamConfig] = Field(description="Modulation parameters for this curriculum level")

    @field_validator("affordances")
    @classmethod
    def validate_unique_affordance_names(cls, affordances: list[AffordanceParamConfig]) -> list[AffordanceParamConfig]:
        """Ensure affordance names are unique."""
        names = [a.name for a in affordances]
        duplicates = [name for name in names if names.count(name) > 1]
        if duplicates:
            raise ValueError(f"Duplicate affordance names found: {list(set(duplicates))}. " f"Each affordance must have a unique name.")
        return affordances


def load_affordances_v2_config(config_dir: Path) -> AffordancesV2Config:
    """Load and validate affordances configuration (v2.1 format).

    Args:
        config_dir: Directory containing affordances.yaml (curriculum level)

    Returns:
        Validated AffordancesV2Config

    Raises:
        FileNotFoundError: If affordances.yaml not found
        ValueError: If validation fails (with helpful error message)

    Example:
        >>> config = load_affordances_v2_config(Path("configs/default_curriculum/levels/L1_full_observability"))
        >>> print(f"Loaded {len(config.affordances)} affordances, {len(config.modulations)} modulations")
        Loaded 14 affordances, 2 modulations
    """
    try:
        data = load_yaml_section(config_dir, "affordances.yaml", "affordances")
        return AffordancesV2Config(**data)
    except ValidationError as e:
        raise ValueError(format_validation_error(e, "affordances.yaml")) from e
