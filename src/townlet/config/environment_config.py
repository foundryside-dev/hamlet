"""Environment-level configuration DTO.

This module defines the Pydantic DTO for environment.yaml files in the v2.1
configuration system. An environment defines meters, cascades, modulations,
affordances, VFS variables, and UI cues.

Example:
    >>> config = EnvironmentConfig.from_yaml(Path("configs/default_curriculum/environment.yaml"))
    >>> print(len(config.meters))
    8
    >>> print(config.meters[0].name)
    'energy'
"""

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Discriminator, Field, model_validator

from townlet.vfs.semantic_type import SemanticType


class _MeterRangeBase(BaseModel):
    """Shared base for the `range_type` members. Each member forbids extras, so a
    parameter belonging to a DIFFERENT member is a parse error naming the meter,
    not a silently ignored key."""

    model_config = ConfigDict(extra="forbid")


class MeterRangeNone(_MeterRangeBase):
    """Observe the meter's raw value. An explicit author choice, never an absence of one."""

    kind: Literal["none"]


class MeterRangeMinMax(_MeterRangeBase):
    """Linear rescale of the meter's declared bar bounds onto [0, 1]."""

    kind: Literal["minmax"]
    clip: bool = Field(
        ...,
        description=(
            "Clamp into the declared bounds before rescaling. Required: a bar whose bounds are "
            "enforced at runtime does not need it, an expression-driven one does, and the "
            "compiler must not guess which this is."
        ),
    )


class MeterRangeLogScaled(_MeterRangeBase):
    """Logarithmic rescale of the declared bar bounds onto [0, 1].

    The member `hamlet-3d3039f340` exists for: with bounds `[1, 1e6]`, minmax crushes the
    whole operating range 1..100,000 into `[0, 0.0999]` and the agent is effectively blind
    to the meter. This gives it back its dynamic range.
    """

    kind: Literal["log_scaled"]
    clip: bool = Field(..., description="Clamp into the declared bounds before log-scaling.")


class MeterRangeZScore(_MeterRangeBase):
    """Standardize against a declared mean and standard deviation."""

    kind: Literal["zscore"]
    mean: float = Field(..., description="Distribution mean. Declared, never inferred from bounds.")
    std: float = Field(..., description="Distribution standard deviation. Must be non-zero.")


class MeterRangeCyclicalSinCos(_MeterRangeBase):
    """Encode a wrapping quantity as a (sin, cos) pair. Observes TWO dimensions, not one."""

    kind: Literal["cyclical_sin_cos"]
    period: float = Field(..., gt=0.0, description="The value at which the quantity wraps (e.g. 24 for hours).")


class MeterRangeOneHot(_MeterRangeBase):
    """Expand an integer-valued meter into a one-hot vector. Observes `categories` dimensions."""

    kind: Literal["one_hot"]
    categories: int = Field(..., ge=2, description="Number of categories; the meter's value indexes into them.")


class MeterRangeBinary(_MeterRangeBase):
    """Threshold the meter into 0/1."""

    kind: Literal["binary"]
    threshold: float = Field(..., description="Values strictly above this observe as 1.0.")


class MeterRangeRankScaled(_MeterRangeBase):
    """Scale the meter to its rank within the batch. Note this makes the observation
    depend on the other agents, which is a deliberate choice and rarely the right one."""

    kind: Literal["rank_scaled"]


class MeterRangeMaskedValue(_MeterRangeBase):
    """Replace a sentinel value with a fill value, passing everything else through."""

    kind: Literal["masked_value"]
    mask_value: float = Field(..., description="The sentinel to replace.")
    fill_value: float = Field(..., description="What to replace it with.")


MeterRangeType = Annotated[
    MeterRangeNone
    | MeterRangeMinMax
    | MeterRangeLogScaled
    | MeterRangeZScore
    | MeterRangeCyclicalSinCos
    | MeterRangeOneHot
    | MeterRangeBinary
    | MeterRangeRankScaled
    | MeterRangeMaskedValue,
    Discriminator("kind"),
]
"""A meter's COMPLETE observation type (PDR-0053 ruling (a), PDR-0054 ruling 2).

Nine members, one per VFS normalization kind, **tagged by the kind's own name** — there is
no translation layer, because a translation layer is where a member learns to lie
(`PDR-0047` rule 1; `hamlet-1dba1910c0` was exactly that defect). Each member carries its
own required parameters and omitting one is a compile error (`PDR-0052`).

The `minmax` and `log_scaled` members take their `min`/`max` from the meter's declared
`bars.yaml` bounds rather than restating them — `PDR-0016` made bounds and normalization one
feature, so the declaration that ceilings the runtime also scales the observation. Every
other member's parameters are declared inline, because no other member's parameters are
implied by anything already written down.

Two members change the OBSERVED WIDTH: `cyclical_sin_cos` observes 2 dims and `one_hot`
observes `categories`. That is why the compiled observation field's width and its VFS source
variable's width are two different numbers (`PDR-0054` W4).

This REPLACES `Literal["normalized", "unbounded", "integer"]`, which was accepted, hashed
into `environment_hash`, and drove nothing (`PDR-0051` measured it, `hamlet-365e996511`
tracked it). The old members are deleted, not mapped: translating `unbounded` to a log
family would be a hidden default of exactly the kind this work removes.
"""


class MeterConfig(BaseModel):
    """Meter (bar) definition."""

    name: str = Field(..., description="Meter name (e.g., 'energy', 'health')")
    description: str = Field(..., description="Human-readable description")
    range_type: MeterRangeType = Field(
        ...,
        description=(
            "The meter's complete observation type: a closed, parameterized vocabulary tagged "
            "by the VFS normalization kind. Determines how the meter is observed AND how wide "
            "its observation is."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class CascadeConfig(BaseModel):
    """Cascade edge in the cascade graph."""

    source: str = Field(..., description="Source meter name")
    target: str = Field(..., description="Target meter name")
    description: str = Field(..., description="Cascade relationship description")

    model_config = ConfigDict(extra="forbid")


class ModulationConfig(BaseModel):
    """Modulation relationship between meter and affordances."""

    bar: str = Field(..., description="Meter name that modulates affordances")
    affordances: list[str] = Field(..., description="Affordances affected by this meter")
    description: str = Field(..., description="Modulation effect description")

    model_config = ConfigDict(extra="forbid")


class AffordanceDefinition(BaseModel):
    """Global affordance registry entry (environment.yaml).

    Defines the canonical name, description, and category for an affordance.
    Curriculum-level parameters (costs, effects, deployment) are defined in
    levels/*/affordances.yaml using AffordanceParamConfig.
    """

    name: str = Field(..., description="Affordance name (e.g., 'EAT', 'SLEEP')")
    description: str = Field(..., description="Human-readable description")
    category: str = Field(..., description="Affordance category (e.g., 'sustenance', 'hygiene')")

    model_config = ConfigDict(extra="forbid")


class NormalizationConfig(BaseModel):
    """Variable normalization configuration."""

    method: Literal["normalize", "standardize"] = Field(
        ...,
        description=(
            "Normalization method: normalize (scale to [0,1] against `range`) or "
            "standardize (mean/std). Every member is distinct and does what its name says "
            "(PDR-0047 rule 1)."
        ),
    )
    range: list[float] = Field(..., description="Value range [min, max]", min_length=2, max_length=2)
    clip: bool | None = Field(
        default=None,
        description=(
            "Clamp the value into `range` before scaling. REQUIRED when method=normalize, "
            "forbidden when method=standardize (which has no range to clamp against). "
            "`None` is not a default — the validator rejects it where the parameter applies."
        ),
    )
    mean: float | list[float] | None = Field(
        default=None,
        description="Mean value(s) for standardize normalization (optional; required when method=standardize).",
    )
    std: float | list[float] | None = Field(
        default=None,
        description="Standard deviation value(s) for standardize normalization (optional; required when method=standardize).",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_clip_is_declared_where_it_applies(self) -> "NormalizationConfig":
        """`clip` is required for `normalize` and forbidden for `standardize`.

        Removing the false `clip` *member* (hamlet-1dba1910c0) did not give authors
        clamping — they never had it, because `minmax` is pure affine rescaling.
        This is the real thing (hamlet-fba56feca5), as a parameter rather than a
        member, so it composes with `log_scaled` instead of multiplying members.
        """
        if self.method == "normalize" and self.clip is None:
            raise ValueError(
                "normalization method 'normalize' requires an explicit 'clip' (true or false).\n"
                "  Rule: clamping is a declared choice, never inferred (No-Defaults Principle).\n"
                "  clip: false — rescale only; an input outside `range` stays outside [0, 1].\n"
                "  clip: true  — clamp into `range` first, so the observation is bounded."
            )
        if self.method == "standardize" and self.clip is not None:
            raise ValueError("normalization method 'standardize' does not accept 'clip' — it has no range to clamp against.")
        return self


class VariableConfig(BaseModel):
    """An environment variable — and, today, its exposure declaration.

    Each of these becomes exactly ONE compiled observation field, so the observation-side
    properties (`normalization`, `semantic_type`) are declared here beside the state. When a
    per-variable exposure surface exists (vfs.md §4.3 / §8.1) both move to it together.
    """

    name: str = Field(..., description="Variable name")
    type: Literal["scalar", "vector"] = Field(..., description="Variable data type")
    dims: int = Field(..., description="Number of dimensions", gt=0)
    scope: Literal["global", "agent", "agent_private"] = Field(..., description="Variable visibility scope")
    description: str = Field(..., description="Human-readable description")
    normalization: NormalizationConfig = Field(..., description="Normalization configuration")
    semantic_type: SemanticType = Field(
        ...,
        description=(
            "Semantic group of this variable's observation field — one member of the closed vocabulary "
            "in townlet.vfs.semantic_type (PDR-0047). The declaration is authoritative: the compiler emits "
            "exactly this value and lays the field out with its group. `bars` is the meter block and is "
            "not declarable here. Required, no default: it is part of the field's provenance."
        ),
    )

    model_config = ConfigDict(extra="forbid")


class CueTriggerConfig(BaseModel):
    """Cue trigger condition."""

    bar: str = Field(..., description="Meter name to monitor")
    threshold: float = Field(..., description="Threshold value")
    direction: Literal["above", "below"] = Field(..., description="Trigger direction")

    model_config = ConfigDict(extra="forbid")


class CueDisplayConfig(BaseModel):
    """Cue display properties."""

    icon: str = Field(..., description="Display icon (emoji or text)")
    color: str = Field(..., description="Display color (hex code)")
    message: str = Field(..., description="Message to display")

    model_config = ConfigDict(extra="forbid")


class CueConfig(BaseModel):
    """UI cue definition."""

    name: str = Field(..., description="Cue name")
    trigger: CueTriggerConfig = Field(..., description="Trigger condition")
    display: CueDisplayConfig = Field(..., description="Display properties")

    model_config = ConfigDict(extra="forbid")


class EnvironmentConfigRoot(BaseModel):
    """Root structure for environment.yaml file."""

    version: str = Field(..., description="Config schema version")
    meters: list[MeterConfig] = Field(..., description="Meter definitions")
    cascade_graph: list[CascadeConfig] = Field(..., description="Cascade relationships")
    modulation_graph: list[ModulationConfig] = Field(..., description="Modulation relationships")
    affordances: list[AffordanceDefinition] = Field(..., description="Affordance definitions")
    variables: list[VariableConfig] = Field(..., description="VFS variable definitions")
    cues: list[CueConfig] = Field(..., description="UI cue definitions")

    model_config = ConfigDict(extra="forbid")


class EnvironmentConfig(BaseModel):
    """Top-level environment configuration.

    This DTO wraps the 'environment' key from environment.yaml.
    """

    environment: EnvironmentConfigRoot = Field(..., description="Environment configuration")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_yaml(cls, path: Path) -> "EnvironmentConfig":
        """Load environment configuration from YAML file.

        Args:
            path: Path to environment.yaml file

        Returns:
            EnvironmentConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
