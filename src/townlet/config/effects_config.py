"""Configuration DTOs for Effects system."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "ReapplyPolicy",
    "EffectScope",
    "CommandConfig",
    "EffectDefinitionConfig",
]


class ReapplyPolicy(str, enum.Enum):
    """Policy for handling multiple spawns of the same effect.

    - stack: Create independent instances (multiple timers)
    - renew: Refresh duration (single instance, timer resets)
    - merge: Increase intensity (single instance, intensity stacks)
    - replace: Clear old, spawn new (single instance, new replaces old)
    """

    STACK = "stack"
    RENEW = "renew"
    MERGE = "merge"
    REPLACE = "replace"

    @classmethod
    def _missing_(cls, value):
        """Case-insensitive lookup."""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class EffectScope(str, enum.Enum):
    """Scope where effect can attach.

    - global: Single instance shared across all agents
    - agent: Per-agent effects (typical use case)
    - item: Per-item effects (e.g., "spoiled", "poisoned")
    - affordance: Per-affordance effects (e.g., "depleted", "locked")
    """

    GLOBAL = "global"
    AGENT = "agent"
    ITEM = "item"
    AFFORDANCE = "affordance"

    @classmethod
    def _missing_(cls, value):
        """Case-insensitive lookup."""
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.lower():
                    return member
        return None


class CommandConfig(BaseModel):
    """Single command in an effect pipeline.

    Exactly one of: modify, spawn_effect, spawn_item, if, for_each must be set.
    """

    model_config = ConfigDict(populate_by_name=True)  # Allow both "if" and "if_condition"

    # modify command: Mutate VFS/bar variable
    modify: str | None = None
    value: str | None = None  # Expression to evaluate

    # spawn_effect command: Trigger another effect
    spawn_effect: str | None = None  # Effect ID
    target: str | None = "self"  # Expression: "self", "target", or path
    intensity: float | None = 1.0  # Strength multiplier

    # spawn_item command: Create item in world (Phase 4)
    spawn_item: str | None = None  # Item type ID
    position: str | None = None  # Expression for position

    # if command: Conditional execution
    if_condition: str | None = Field(None, alias="if")  # Expression (must eval to bool)
    then: list[CommandConfig] = []
    else_: list[CommandConfig] = Field(default=[], alias="else")

    # for_each command: Iterate over collection
    for_each: str | None = None  # Expression (must eval to list/tensor)
    as_: str | None = Field(None, alias="as")  # Iterator variable name
    do: list[CommandConfig] = []

    @model_validator(mode="after")
    def validate_exactly_one_command(self) -> CommandConfig:
        """Exactly one command type must be set."""
        fields = ["modify", "spawn_effect", "spawn_item", "if_condition", "for_each"]
        set_fields = [f for f in fields if getattr(self, f) is not None]

        if len(set_fields) != 1:
            raise ValueError(
                f"Exactly one command type required (modify/spawn_effect/spawn_item/if/for_each), got {len(set_fields)}: {set_fields}"
            )

        # Also validate that modify command has value field
        if self.modify and not self.value:
            raise ValueError("modify command requires 'value' field")

        return self


class EffectDefinitionConfig(BaseModel):
    """Definition of a single effect in the catalog.

    Effects are reusable simulation behaviors with lifecycle hooks.
    """

    id: str = Field(..., description="Unique effect identifier")
    scope: EffectScope = Field(..., description="Where effect can attach")

    # Lifecycle parameters (REQUIRED - no defaults to prevent surprises)
    duration: int = Field(..., description="Ticks until auto-despawn", gt=0)
    intensity: float = Field(default=1.0, description="Default strength multiplier")

    # Stacking policy (REQUIRED - must be explicit)
    reapply_policy: ReapplyPolicy = Field(..., description="Policy for multiple spawns")

    # Visibility
    observable: bool = Field(default=True, description="Visible in agent observations")

    # Lifecycle command pipelines
    on_spawn: list[CommandConfig] = Field(default=[], description="Commands on spawn")
    on_tick: list[CommandConfig] = Field(default=[], description="Commands each tick")
    on_despawn: list[CommandConfig] = Field(default=[], description="Commands on despawn")
    on_interrupt: list[CommandConfig] = Field(default=[], description="Commands on forced removal")

    @field_validator("on_spawn", "on_tick", "on_despawn", "on_interrupt", mode="before")
    @classmethod
    def parse_command_dicts(cls, v):
        """Convert list of dicts to list of CommandConfig."""
        if v is None:
            return []
        if isinstance(v, list):
            return [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in v]
        return v
