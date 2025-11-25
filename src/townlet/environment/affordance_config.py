"""Affordance configuration models for runtime.

RUNTIME DTO: This module defines runtime affordance objects used by the environment
stack during simulation. For parse-time YAML validation DTOs, see:
    townlet.config.affordances_v2_config

Config v2.1 compiles affordance metadata from hierarchical YAML packs;
this module does not perform any YAML loading.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class AffordanceEffect(BaseModel):
    """Single meter effect from an affordance interaction."""

    meter: str  # Meter name (e.g., "energy", "hygiene")
    amount: float  # Change amount (normalized, positive or negative)
    type: str | None = None  # "linear" for distributed effects, None for instant

    # Note: Meter name validation historically happened at collection level.


class AffordanceCost(BaseModel):
    """Resource cost for an affordance interaction."""

    meter: str  # Meter name (usually "money" or "energy")
    amount: float = Field(ge=0.0)  # Cost amount (must be non-negative)

    # Note: Meter name validation historically happened at collection level.


class AffordanceConfig(BaseModel):
    """Complete configuration for a single affordance."""

    # Identity
    id: str  # Unique identifier (e.g., "Bed", "Shower")
    name: str  # Human-readable name
    category: str  # Category (e.g., "energy_restoration", "income")

    # Interaction type
    interaction_type: Literal["instant", "multi_tick", "continuous", "dual"]

    # Multi-tick specific
    duration_ticks: int | None = None  # Number of ticks to complete

    # Costs (instant or per-tick)
    costs: list[AffordanceCost] = Field(default_factory=list)
    costs_per_tick: list[AffordanceCost] = Field(default_factory=list)

    # Effects (instant or per-tick)
    effects: list[AffordanceEffect] = Field(default_factory=list)
    effects_per_tick: list[AffordanceEffect] = Field(default_factory=list)

    # Completion bonus (only for multi_tick)
    completion_bonus: list[AffordanceEffect] = Field(default_factory=list)

    # Operating hours [open_hour, close_hour]
    # Example: [8, 18] = 8am-6pm, [18, 28] = 6pm-4am (wraps midnight)
    operating_hours: list[int]

    # Optional metadata
    teaching_note: str | None = None
    design_intent: str | None = None
    position: list[int] | dict[str, int] | int | None = None

    @model_validator(mode="after")
    def validate_multi_tick_requirements(self) -> AffordanceConfig:
        """Ensure multi_tick and dual affordances have duration_ticks set."""
        if self.interaction_type == "multi_tick" and self.duration_ticks is None:
            raise ValueError(f"Affordance '{self.id}': multi_tick type requires 'duration_ticks' field")

        if self.interaction_type == "dual" and self.duration_ticks is None:
            raise ValueError(f"Affordance '{self.id}': dual type requires 'duration_ticks' field")

        if self.interaction_type not in ["multi_tick", "dual"] and self.duration_ticks is not None:
            raise ValueError(f"Affordance '{self.id}': 'duration_ticks' only valid for multi_tick or dual types")

        return self

    @model_validator(mode="after")
    def validate_operating_hours(self) -> AffordanceConfig:
        """Ensure operating hours are valid."""
        if len(self.operating_hours) != 2:
            raise ValueError(f"Affordance '{self.id}': operating_hours must be [open, close]")

        open_hour, close_hour = self.operating_hours

        if not (0 <= open_hour < 24):
            raise ValueError(f"Affordance '{self.id}': open_hour must be 0-23, got {open_hour}")

        if not (0 < close_hour <= 28):
            raise ValueError(f"Affordance '{self.id}': close_hour must be 1-28, got {close_hour}")

        return self

    @field_validator("position")
    @classmethod
    def validate_position_format(cls, value):
        """Validate multi-format positioning across substrates."""
        if value is None:
            return value

        if isinstance(value, list):
            if not value or not all(isinstance(coord, int) for coord in value):
                raise ValueError("List position must contain integer coordinates")
            # Lists represent explicit spatial coordinates; allow any dimensionality >=1.
            return value

        if isinstance(value, dict):
            if set(value.keys()) != {"q", "r"}:
                raise ValueError("Dict position must contain 'q' and 'r' keys for axial coordinates")
            if not all(isinstance(coord, int) for coord in value.values()):
                raise ValueError("Dict position values must be integers")
            return value

        if isinstance(value, int):
            if value < 0:
                raise ValueError("Integer position (graph node id) must be >= 0")
            return value

        raise ValueError(f"Invalid position format ({type(value)}). Expected list[int], dict[str,int], int, or None.")


class AffordanceConfigCollection(BaseModel):
    """Collection of all affordance configurations."""

    version: str
    description: str
    status: str  # e.g., "TEMPLATE", "PRODUCTION"
    affordances: list[AffordanceConfig]

    # Optional metadata
    teaching_insights: dict[str, str] | None = None
    implementation_notes: dict[str, str] | None = None

    def get_affordance(self, affordance_id: str) -> AffordanceConfig | None:
        """Look up affordance by ID."""
        for affordance in self.affordances:
            if affordance.id == affordance_id:
                return affordance
        return None

    def get_affordances_by_category(self, category: str) -> list[AffordanceConfig]:
        """Get all affordances in a category."""
        return [aff for aff in self.affordances if aff.category == category]

    def get_affordances_by_type(self, interaction_type: str) -> list[AffordanceConfig]:
        """Get all affordances of a given type."""
        return [aff for aff in self.affordances if aff.interaction_type == interaction_type]


# ============================================================================
# DELETED: is_affordance_open() moved to temporal_utils.py (JANK-09 fix)
# If you get an ImportError, update your import to:
#   from townlet.environment.temporal_utils import is_affordance_open
# ============================================================================
