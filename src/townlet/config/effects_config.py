"""Configuration DTOs for Effects system."""

from __future__ import annotations

import enum
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    SerializerFunctionWrapHandler,
    field_validator,
    model_serializer,
    model_validator,
)

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


# Each command kind is the exact set of YAML keys a node of that kind authors. The
# first key names the kind; every key in `required` must be authored (no command field
# has a behavioural default), and a key outside `required | optional` is refused, so a
# node is one command kind and nothing else (compiler remediation C12). `do` is one YAML
# key shared by `for_each` and `delay`.
_COMMAND_KINDS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "modify": (frozenset({"modify", "value"}), frozenset()),
    "spawn_effect": (frozenset({"spawn_effect", "target", "intensity"}), frozenset()),
    "spawn_item": (frozenset({"spawn_item", "position", "quantity"}), frozenset()),
    "if": (frozenset({"if", "then", "else"}), frozenset()),
    # `as` is accepted and not yet bound (effects remediation WP7 decides bind or delete).
    "for_each": (frozenset({"for_each", "do"}), frozenset({"as"})),
    "switch": (frozenset({"switch", "cases", "default"}), frozenset()),
    "parallel": (frozenset({"parallel"}), frozenset()),
    "delay": (frozenset({"delay", "do"}), frozenset()),
    "sample": (frozenset({"sample", "params", "store_in"}), frozenset()),
}


class CommandConfig(BaseModel):
    """Single command in an effect pipeline.

    Exactly one command kind per node, and every field of that kind authored:

    - modify/value: Mutate VFS/bar variable
    - spawn_effect/target/intensity: Trigger another effect
    - spawn_item/position/quantity: Create items in the world
    - if/then/else: Conditional execution (per-agent mask)
    - for_each/do (+ as): Iterate over collection
    - switch/cases/default: Multi-branch dispatch
    - parallel: Disjoint branch execution
    - delay/do: Schedule commands after N ticks
    - sample/params/store_in: Draw from distribution

    Fields that belong to another kind keep an inert empty value; the validator refuses
    them if authored, so they never carry behaviour.
    """

    model_config = ConfigDict(extra="forbid")

    # modify command: Mutate VFS/bar variable
    modify: str | None = None
    value: str | None = None  # Expression to evaluate

    # spawn_effect command: Trigger another effect
    spawn_effect: str | None = None  # Effect ID
    target: str | None = None  # Expression: "self", "target", or path
    intensity: float | None = Field(default=None, allow_inf_nan=False)  # Strength multiplier

    # spawn_item command: Create items in the world
    spawn_item: str | None = None  # Item type ID
    position: str | None = None  # "self", "target" or "random"
    quantity: int | None = Field(default=None, ge=1)  # Number of items placed by one execution
    # No authored `initial_state`: static write authorization cannot see an override map,
    # so an authored one is refused here as an extra field (items remediation).

    # if command: Conditional execution
    if_condition: str | None = Field(None, alias="if")  # Expression (must eval to bool)
    then: list[CommandConfig] = []
    else_: list[CommandConfig] = Field(default=[], alias="else")

    # for_each command: Iterate over collection
    for_each: str | None = None  # Collection name or expression
    as_: str | None = Field(None, alias="as")  # Iterator variable name (not yet bound; WP7)
    do: list[CommandConfig] = []

    # switch command: Multi-branch equality dispatch
    switch: str | None = None  # Expression evaluated once
    cases: list[SwitchCaseConfig] = []  # Typed {when, do} branches
    default: list[CommandConfig] = []  # Default branch commands

    # parallel command: disjoint branch execution
    parallel: list[CommandConfig] | None = None

    # delay command: schedule commands after N ticks
    delay: str | None = None  # ticks expression
    delay_do: list[CommandConfig] = Field(default=[], alias="do")

    # sample command: draw from distribution into path
    sample: str | None = None  # distribution name (e.g., "uniform")
    params: dict[str, Any] | None = None
    store_in: str | None = None

    @field_validator("intensity")
    @classmethod
    def validate_spawn_intensity_float32(cls, intensity: float | None) -> float | None:
        """Canonicalize authored spawn intensity at the float32 runtime boundary."""
        if intensity is None:
            return None
        return require_float32(intensity, field="spawn_effect intensity")

    def _authored_keys(self) -> set[str]:
        """The YAML keys this node authored (aliases, so `do` is one key for two fields)."""
        fields = type(self).model_fields
        return {fields[name].alias or name for name in self.model_fields_set}

    @model_serializer(mode="wrap")
    def _serialize_own_kind(self, handler: SerializerFunctionWrapHandler, info: SerializationInfo) -> dict[str, Any]:
        """Serialize exactly the authored keys, so a dump re-validates as the same command.

        The inert values of other kinds' fields are not part of the command; emitting them
        would make a round trip (`model_dump` then `model_validate`) read as a node that
        authored every kind at once.
        """
        authored = self._authored_keys()
        fields = type(self).model_fields
        # `do` is one YAML key for two fields; the node's kind owns exactly one of them.
        disowned = "do"
        if self.delay is None:
            disowned = "delay_do"
        keep = {name for name, field in fields.items() if (field.alias or name) in authored and name != disowned}
        keys = set(keep)
        if info.by_alias:
            keys = {fields[name].alias or name for name in keep}
        return {key: value for key, value in handler(self).items() if key in keys}

    @model_validator(mode="after")
    def validate_exactly_one_command(self) -> CommandConfig:
        """One command kind per node; every key of that kind authored, no key of another."""
        authored = self._authored_keys()
        kinds = [kind for kind in _COMMAND_KINDS if kind in authored]
        if len(kinds) != 1:
            allowed = "/".join(_COMMAND_KINDS)
            raise ValueError(f"Exactly one command type required ({allowed}), got {len(kinds)}: {kinds}")
        kind = kinds[0]
        required, optional = _COMMAND_KINDS[kind]
        missing = sorted(required - authored)
        if missing:
            raise ValueError(f"{kind} command requires {missing}; every field of a command is authored explicitly")
        foreign = sorted(authored - required - optional)
        if foreign:
            raise ValueError(f"{kind} command does not take {foreign}; a command node is exactly one command kind")
        values = {name: getattr(self, name) for name in self.model_fields_set}
        null = sorted(type(self).model_fields[name].alias or name for name, value in values.items() if value is None)
        if null:
            raise ValueError(f"{kind} command fields {null} must not be null")

        if self.switch is not None and not self.cases and not self.default:
            raise ValueError("switch command requires at least one case or default block")

        if self.parallel is not None and not self.parallel:
            raise ValueError("parallel command requires at least one branch")

        if self.delay is not None and not self.delay_do:
            raise ValueError("delay command requires a non-empty 'do' block")

        if self.sample is not None:
            assert self.params is not None
            dist = self.sample.lower()
            required_params: dict[str, tuple[str, ...]] = {
                "uniform": ("min", "max"),
                "normal": ("mean", "std"),
                "lognormal": ("mean", "std"),
                "exponential": ("rate",),
                "bernoulli": ("p",),
                "categorical": ("probs",),
            }
            if dist not in required_params:
                raise ValueError(f"Unsupported sample distribution '{self.sample}'")
            missing_params = [k for k in required_params[dist] if k not in self.params]
            if missing_params:
                raise ValueError(f"sample '{dist}' missing params: {missing_params}")

        return self


class SwitchCaseConfig(BaseModel):
    """One branch of a ``switch`` command: ``when`` is the equality expression, ``do`` its body.

    Both keys are authored (an empty ``do`` is an authored empty body). The body is typed
    command nodes, so parsing, static write authorization and pipeline compilation walk
    one grammar, and a refusal inside it is located at the nested command.
    """

    model_config = ConfigDict(extra="forbid")

    when: str
    do: list[CommandConfig]


CommandConfig.model_rebuild()


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

    version: Literal["1.0"] = Field(..., description="Config schema version")
    effect_definitions: list[EffectDefinitionConfig] = Field(..., description="Catalog of reusable effect definitions")
    # Per-scope budget of concurrently active effects (token-obs spec §2 capacity table;
    # hamlet-88578e629e): the instances ONE scope entity (a world's agent, an item row, a
    # world's affordance, the world itself) may carry at once. REQUIRED (No-Defaults)
    # whenever any effect is declared — `effect` token capacity is Σ scope budget × scope
    # denominator — and forbidden when the catalog is empty (a declaration that reaches
    # nothing). A spawn that would add an instance beyond the budget is not admitted, in
    # that world only, and is recorded in `EffectManager.spawn_refusals` (step `info`
    # `effect_spawn_refusals`); the publisher's overflow refusal is a backstop, never the
    # enforcement.
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
