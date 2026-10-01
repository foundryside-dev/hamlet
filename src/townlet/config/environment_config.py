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
from pydantic import BaseModel, ConfigDict, Discriminator, Field

from townlet.vfs.schema import NormalizationSpec


class _MeterRangeBase(BaseModel):
    """Shared base for the `range_type` members. Each member forbids extras, so a
    parameter belonging to a DIFFERENT member is a parse error naming the meter,
    not a silently ignored key."""

    model_config = ConfigDict(extra="forbid")


class MeterRangeMinMax(_MeterRangeBase):
    """Clamped linear rescale of the meter's declared bar bounds onto [0, 1]."""

    kind: Literal["minmax"]
    clip: Literal[True] = Field(
        ...,
        description="Must be true: meter values entering tokens are bounded by declaration.",
    )


class MeterRangeLogScaled(_MeterRangeBase):
    """Logarithmic rescale of the declared bar bounds onto [0, 1].

    The member `hamlet-3d3039f340` exists for: with bounds `[1, 1e6]`, minmax crushes the
    whole operating range 1..100,000 into `[0, 0.0999]` and the agent is effectively blind
    to the meter. This gives it back its dynamic range.
    """

    kind: Literal["log_scaled"]
    clip: Literal[True] = Field(..., description="Must be true: meter values entering tokens are bounded by declaration.")


class MeterRangeCyclicalSinCos(_MeterRangeBase):
    """Encode a wrapping quantity as a (sin, cos) pair. Observes TWO dimensions, not one."""

    kind: Literal["cyclical_sin_cos"]
    period: float = Field(
        ...,
        gt=0.0,
        allow_inf_nan=False,
        description="The finite value at which the quantity wraps (e.g. 24 for hours).",
    )


class MeterRangeBinary(_MeterRangeBase):
    """Threshold the meter into 0/1."""

    kind: Literal["binary"]
    threshold: float = Field(..., allow_inf_nan=False, description="Values strictly above this finite threshold observe as 1.0.")


MeterRangeType = Annotated[
    MeterRangeMinMax | MeterRangeLogScaled | MeterRangeCyclicalSinCos | MeterRangeBinary,
    Discriminator("kind"),
]
"""A meter token's complete bounded two-lane observation type (PDR-0134).

Four members, tagged by the normalization kind's own name. Each member carries its own
required parameters and omitting one is a compile error (`PDR-0052`).

The `minmax` and `log_scaled` members take their `min`/`max` from the meter's declared
`bars.yaml` bounds rather than restating them — `PDR-0016` made bounds and normalization one
feature, so the declaration that ceilings the runtime also scales the observation. Every
other member's parameters are declared inline, because no other member's parameters are
implied by anything already written down.

`cyclical_sin_cos` uses both fixed value lanes; the other members use lane 0. Kinds that
are unbounded, batch-coupled, or require more than two lanes are deleted from the meter
surface rather than accepted and translated (`PDR-0134`).
"""


class MeterConfig(BaseModel):
    """Meter (bar) definition."""

    name: str = Field(..., description="Meter name (e.g., 'energy', 'health')")
    description: str = Field(..., description="Human-readable description")
    range_type: MeterRangeType = Field(
        ...,
        description=(
            "The meter's complete observation type: a closed, parameterized vocabulary tagged "
            "by the VFS normalization kind. Determines how the meter fills its fixed two-lane "
            "token value block."
        ),
    )

    model_config = ConfigDict(extra="forbid")

    def token_normalization(self, *, minimum: float, maximum: float) -> NormalizationSpec:
        """Materialize this same-kind declaration for the canonical token normalizer.

        Range kinds take their bounds from bars.yaml; authors never restate them. No
        member is renamed or mapped to another behavior.
        """
        parameters = self.range_type.model_dump()
        if self.range_type.kind in {"minmax", "log_scaled"}:
            parameters["min"] = minimum
            parameters["max"] = maximum
        return NormalizationSpec(**parameters)


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
