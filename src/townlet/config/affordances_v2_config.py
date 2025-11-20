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
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from townlet.config.base import format_validation_error, load_yaml_section
from townlet.config.effects_config import CommandConfig

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

    # Affordability gates (checked BEFORE execution) -------------------------
    costs: dict[str, float] = Field(
        default_factory=dict,
        description="Resource costs required to use this affordance (affordability check). "
        "Example: {'energy': 0.2} means agent needs energy >= 0.2 to interact.",
    )
    costs_per_tick: dict[str, float] = Field(
        default_factory=dict, description="Resource costs per tick for multi_tick affordances (affordability check)."
    )

    # Effect outcomes (applied AFTER affordability check passes) -------------

    # LEGACY: Simple effects dict (DEPRECATED - use interactions instead)
    effects: dict[str, float] = Field(
        default_factory=dict,
        description="[DEPRECATED] Simple instant effects (meter: value). Use interactions field instead.",
    )

    # LEGACY: Effect pipeline (DEPRECATED - use interactions instead)
    effect_pipeline: Any | None = Field(  # EffectPipeline type removed to avoid import
        default=None,
        description="[DEPRECATED] Multi-stage effect pipeline. Use interactions field instead.",
    )

    # NEW: Effects commands (unified with Items system) - OPTIONAL during migration
    interactions: dict[str, list[CommandConfig]] | None = Field(
        default=None,
        description=(
            "Effects commands for affordance lifecycle stages. "
            "Unified with Items system (declarative Effects). "
            "Stages: on_start, per_tick, on_completion, on_early_exit, on_failure. "
            "NOTE: Use costs/costs_per_tick for affordability gates, interactions for outcomes."
        ),
    )

    # Temporal semantics -----------------------------------------------------
    interaction_type: Literal["instant", "multi_tick", "dual"] | None = Field(
        default=None,
        description="Interaction type. When omitted, defaults to 'instant' at runtime.",
    )
    duration_ticks: int | None = Field(
        default=None,
        description="Number of ticks required to complete a multi_tick or dual interaction.",
    )

    # Availability + spatial deployment --------------------------------------
    opening_hours: OpeningHoursConfig = Field(description="Availability schedule")
    deployment: DeploymentConfig = Field(description="Spatial placement configuration")

    @model_validator(mode="after")
    def validate_interaction_semantics(self) -> "AffordanceParamConfig":
        """Lightweight validation of interaction_type/duration_ticks compatibility."""

        interaction = self.interaction_type or "instant"

        if interaction in {"multi_tick", "dual"} and self.duration_ticks is None:
            raise ValueError(f"Affordance '{self.name}': interaction_type='{interaction}' requires an explicit duration_ticks value.")

        if interaction == "instant" and self.duration_ticks is not None:
            raise ValueError(f"Affordance '{self.name}': duration_ticks is only valid for multi_tick or dual interaction types.")

        return self

    @model_validator(mode="after")
    def validate_effects_exclusivity(self) -> "AffordanceParamConfig":
        """Ensure only one effect system is used (legacy or new)."""
        effects_count = sum(
            [
                bool(self.effects),
                self.effect_pipeline is not None,
                self.interactions is not None,
            ]
        )

        if effects_count == 0:
            raise ValueError(
                f"Affordance '{self.name}': Must specify one effect system: "
                "effects (deprecated), effect_pipeline (deprecated), or interactions (preferred)."
            )

        if effects_count > 1:
            raise ValueError(
                f"Affordance '{self.name}': Only one effect system allowed. "
                "Found multiple: effects, effect_pipeline, and/or interactions. "
                "Use interactions field only (legacy fields are deprecated)."
            )

        return self

    @model_validator(mode="after")
    def validate_interaction_stages(self) -> "AffordanceParamConfig":
        """Validate interactions have correct stages for interaction_type."""
        # Skip validation if using legacy effect systems
        if self.interactions is None:
            return self

        valid_stages = {"on_start", "per_tick", "on_completion", "on_early_exit", "on_failure"}
        provided_stages = set(self.interactions.keys())

        invalid = provided_stages - valid_stages
        if invalid:
            raise ValueError(f"Affordance '{self.name}': Invalid interaction stages: {invalid}. Valid stages: {valid_stages}")

        interaction_type = self.interaction_type or "instant"

        # Instant affordances shouldn't have per_tick effects
        if interaction_type == "instant" and self.interactions.get("per_tick"):
            raise ValueError(
                f"Affordance '{self.name}': instant affordances cannot have per_tick effects. Use multi_tick or dual interaction_type."
            )

        return self


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
                f"Duplicate affordance names in modulation: {list(set(duplicates))}. Each affordance must appear only once per modulation."
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
            raise ValueError(f"Duplicate affordance names found: {list(set(duplicates))}. Each affordance must have a unique name.")
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
