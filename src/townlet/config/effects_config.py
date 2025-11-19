"""Configuration DTOs for Effects system."""

from __future__ import annotations

import enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = [
    "ReapplyPolicy",
    "EffectScope",
    "CommandConfig",
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
