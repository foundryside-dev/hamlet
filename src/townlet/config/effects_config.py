"""Configuration DTOs for Effects system."""

from __future__ import annotations

import enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "CommandConfig",
    "EffectDefinitionConfig",
    "EffectScope",
    "EffectsConfig",
    "ReapplyPolicy",
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
    def _missing_(cls, value: object) -> ReapplyPolicy | None:
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
    def _missing_(cls, value: object) -> EffectScope | None:
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

    # switch command: Multi-branch equality dispatch
    switch: str | None = None  # Expression evaluated once
    cases: list[dict[str, Any]] = []  # List of {when: expr, do: [...]} mappings
    default: list[CommandConfig] = []  # Default branch commands

    # reduce command: Fixed-size reduction into accumulator
    reduce: str | None = None  # collection expression
    reduce_as: str | None = Field(None, alias="reduce_as")  # iterator name
    reduce_init: str | None = None  # accumulator init expr
    reduce_body: str | None = None  # accumulator update expr (uses acc + iterator)
    reduce_into: str | None = None  # target path to store result

    # parallel command: disjoint branch execution
    parallel: list[CommandConfig] | None = None

    # delay command: schedule commands after N ticks
    delay: str | None = None  # ticks expression
    delay_do: list[CommandConfig] = Field(default=[], alias="do")

    @model_validator(mode="after")
    def validate_exactly_one_command(self) -> CommandConfig:
        """Exactly one command type must be set."""
        fields = ["modify", "spawn_effect", "spawn_item", "if_condition", "for_each", "switch", "reduce", "parallel", "delay"]
        set_fields = [f for f in fields if getattr(self, f) is not None]

        if len(set_fields) != 1:
            allowed = "modify/spawn_effect/spawn_item/if/for_each/switch/reduce/parallel/delay"
            raise ValueError(f"Exactly one command type required ({allowed}), got {len(set_fields)}: {set_fields}")

        # Also validate that modify command has value field
        if self.modify and not self.value:
            raise ValueError("modify command requires 'value' field")

        if self.switch is not None and not self.cases and not self.default:
            raise ValueError("switch command requires at least one case or default block")

        if self.reduce is not None:
            missing = [
                name
                for name, val in {
                    "reduce_as": self.reduce_as,
                    "reduce_init": self.reduce_init,
                    "reduce_body": self.reduce_body,
                    "reduce_into": self.reduce_into,
                }.items()
                if val is None
            ]
            if missing:
                raise ValueError(f"reduce command missing fields: {missing}")

        if self.parallel is not None and not self.parallel:
            raise ValueError("parallel command requires at least one branch")

        if self.delay is not None and not self.delay_do:
            raise ValueError("delay command requires a 'do' block")

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
    def parse_command_dicts(cls, v: list[dict[str, Any]] | list[CommandConfig] | None) -> list[CommandConfig]:
        """Convert list of dicts to list of CommandConfig."""
        if v is None:
            return []
        if isinstance(v, list):
            return [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in v]
        return v


class EffectsConfig(BaseModel):
    """Top-level Effects configuration from effects.yaml."""

    version: Literal["1.0"] = Field(default="1.0", description="Config schema version")
    effect_definitions: list[EffectDefinitionConfig] = Field(default=[], description="Catalog of reusable effect definitions")

    @field_validator("effect_definitions")
    @classmethod
    def validate_unique_ids(cls, definitions: list[EffectDefinitionConfig]) -> list[EffectDefinitionConfig]:
        """Effect IDs must be unique."""
        ids = [d.id for d in definitions]
        duplicates = {effect_id for effect_id in ids if ids.count(effect_id) > 1}

        if duplicates:
            msg = f"Duplicate effect IDs: {duplicates}"
            raise ValueError(msg)

        return definitions
