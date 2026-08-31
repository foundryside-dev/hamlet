"""Configuration DTOs for Effects system."""

from __future__ import annotations

import enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from townlet.numeric import require_float32

__all__ = [
    "CommandConfig",
    "EffectDefinitionConfig",
    "EffectScope",
    "EffectsConfig",
    "ReapplyPolicy",
]


class ReapplyPolicy(enum.StrEnum):
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


class EffectScope(enum.StrEnum):
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

    Exactly one command type must be set. Valid command types:

    - modify/value: Mutate VFS/bar variable
    - spawn_effect: Trigger another effect
    - spawn_item: Create item in world
    - if/then/else: Conditional execution
    - for_each/as/do: Iterate over collection
    - switch/cases/default: Multi-branch dispatch
    - reduce: Fixed-size reduction into accumulator
    - parallel: Disjoint branch execution
    - delay/do: Schedule commands after N ticks
    - sample/store_in: Draw from distribution
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # modify command: Mutate VFS/bar variable
    modify: str | None = None
    value: str | None = None  # Expression to evaluate

    # spawn_effect command: Trigger another effect
    spawn_effect: str | None = None  # Effect ID
    target: str | None = None  # Expression: "self", "target", or path
    intensity: float | None = Field(default=None, allow_inf_nan=False)  # Strength multiplier

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

    # sample command: draw from distribution into path
    sample: str | None = None  # distribution name (e.g., "uniform")
    params: dict[str, Any] = Field(default_factory=dict)
    store_in: str | None = None

    @field_validator("intensity")
    @classmethod
    def validate_spawn_intensity_float32(cls, intensity: float | None) -> float | None:
        """Canonicalize authored spawn intensity at the float32 runtime boundary."""
        if intensity is None:
            return None
        return require_float32(intensity, field="spawn_effect intensity")

    @model_validator(mode="after")
    def validate_exactly_one_command(self) -> CommandConfig:
        """Exactly one command type must be set."""
        fields = [
            "modify",
            "spawn_effect",
            "spawn_item",
            "if_condition",
            "for_each",
            "switch",
            "reduce",
            "parallel",
            "delay",
            "sample",
        ]
        set_fields = [f for f in fields if getattr(self, f) is not None]

        if len(set_fields) != 1:
            allowed = "modify/spawn_effect/spawn_item/if/for_each/switch/reduce/parallel/delay/sample"
            raise ValueError(f"Exactly one command type required ({allowed}), got {len(set_fields)}: {set_fields}")

        # Also validate that modify command has value field
        if self.modify and not self.value:
            raise ValueError("modify command requires 'value' field")

        if self.spawn_effect is not None:
            if self.target is None:
                raise ValueError("spawn_effect command requires 'target'")
            if self.intensity is None:
                raise ValueError("spawn_effect command requires 'intensity'")

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

        sample_set = self.sample is not None
        if sample_set:
            if not self.store_in:
                raise ValueError("sample command requires 'store_in'")
            if not self.sample:
                raise ValueError("sample command requires 'sample' distribution name")
            if not isinstance(self.params, dict):
                raise ValueError("sample command params must be a mapping")

            dist = self.sample.lower()
            required: dict[str, tuple[str, ...]] = {
                "uniform": ("min", "max"),
                "normal": ("mean", "std"),
                "lognormal": ("mean", "std"),
                "exponential": ("rate",),
                "bernoulli": ("p",),
                "categorical": ("probs",),
            }
            if dist not in required:
                raise ValueError(f"Unsupported sample distribution '{self.sample}'")
            missing = [k for k in required[dist] if k not in self.params]
            if missing:
                raise ValueError(f"sample '{dist}' missing params: {missing}")

        return self


class EffectDefinitionConfig(BaseModel):
    """Definition of a single effect in the catalog.

    Effects are reusable simulation behaviors with lifecycle hooks.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique effect identifier")
    scope: EffectScope = Field(..., description="Where effect can attach")

    # Lifecycle parameters (REQUIRED - no defaults to prevent surprises)
    duration: int = Field(..., description="Ticks until auto-despawn", gt=0)

    # Stacking policy (REQUIRED - must be explicit)
    reapply_policy: ReapplyPolicy = Field(..., description="Policy for multiple spawns")

    # Visibility
    observable: bool = Field(..., description="Visible in agent observations")

    # Authoring metadata only — never read at runtime. Same pattern as
    # ItemTypeConfig.description (items_config.py) — a sibling per-definition DTO.
    description: str | None = Field(default=None, description="Human-readable description (metadata only)")

    # Lifecycle command pipelines
    on_spawn: list[CommandConfig] = Field(..., description="Commands on spawn")
    on_tick: list[CommandConfig] = Field(..., description="Commands each tick")
    on_despawn: list[CommandConfig] = Field(..., description="Commands on despawn")
    on_interrupt: list[CommandConfig] = Field(..., description="Commands on forced removal")

    @field_validator("on_spawn", "on_tick", "on_despawn", "on_interrupt", mode="before")
    @classmethod
    def parse_command_dicts(cls, v: list[dict[str, Any]] | list[CommandConfig]) -> list[CommandConfig]:
        """Convert list of dicts to list of CommandConfig."""
        if isinstance(v, list):
            return [CommandConfig(**cmd) if isinstance(cmd, dict) else cmd for cmd in v]
        return v


class EffectsConfig(BaseModel):
    """Top-level Effects configuration from effects.yaml."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(default="1.0", description="Config schema version")
    effect_definitions: list[EffectDefinitionConfig] = Field(default=[], description="Catalog of reusable effect definitions")
    # Per-scope budget of concurrently active effects (token-obs spec §2 capacity table;
    # hamlet-88578e629e). REQUIRED (No-Defaults) whenever any effect is declared —
    # `effect` token capacity is Σ scope budget × scope denominator — and forbidden when
    # the catalog is empty (a declaration that reaches nothing). Exceeding a scope's
    # budget at runtime raises at publish time (overflow is loud, never truncated).
    max_active_effects: dict[str, int] | None = Field(
        default=None,
        description="Per-EffectScope budget of concurrently active effects, e.g. {global: 0, agent: 4, item: 0, affordance: 0}",
    )

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

    @model_validator(mode="after")
    def validate_max_active_effects(self):
        """`max_active_effects` is required iff any effects are declared (No-Defaults)."""
        scope_values = tuple(member.value for member in EffectScope)
        if self.effect_definitions:
            if self.max_active_effects is None:
                raise ValueError(
                    f"effects.yaml declares {len(self.effect_definitions)} effect(s) but no `max_active_effects` budget.\n"
                    "  Rule: effect token capacity derives from a per-scope declared budget "
                    f"(max_active_effects: {{{', '.join(f'{s}: N' for s in scope_values)}}}), "
                    "required if any effects are declared (token-obs spec §2 capacity table, No-Defaults)."
                )
            missing = [s for s in scope_values if s not in self.max_active_effects]
            unknown = [s for s in self.max_active_effects if s not in scope_values]
            if missing or unknown:
                raise ValueError(
                    f"max_active_effects must declare exactly the EffectScope members {scope_values}; "
                    f"missing {missing}, unknown {unknown}"
                )
            negative = {s: n for s, n in self.max_active_effects.items() if n < 0}
            if negative:
                raise ValueError(f"max_active_effects budgets must be >= 0; got {negative}")
        elif self.max_active_effects is not None:
            raise ValueError(
                "effects.yaml declares `max_active_effects` but no effects, so the declaration reaches nothing.\n"
                "  Rule: a declaration that can reach nothing is removed rather than defaulted (PDR-0066)."
            )
        return self
