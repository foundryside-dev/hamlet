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
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class MeterConfig(BaseModel):
    """Meter (bar) definition."""

    name: str = Field(..., description="Meter name (e.g., 'energy', 'health')")
    description: str = Field(..., description="Human-readable description")
    range_type: Literal["normalized", "unbounded", "integer"] = Field(
        ...,
        description=(
            "Value range type (normalized=[0,1], unbounded=any float, integer=discrete points). "
            "Metadata only for UI; does not affect obs_dim."
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
    mean: float | list[float] | None = Field(
        default=None,
        description="Mean value(s) for standardize normalization (optional; required when method=standardize).",
    )
    std: float | list[float] | None = Field(
        default=None,
        description="Standard deviation value(s) for standardize normalization (optional; required when method=standardize).",
    )

    model_config = ConfigDict(extra="forbid")


class VariableConfig(BaseModel):
    """VFS variable definition."""

    name: str = Field(..., description="Variable name")
    type: Literal["scalar", "vector"] = Field(..., description="Variable data type")
    dims: int = Field(..., description="Number of dimensions", gt=0)
    scope: Literal["global", "agent", "agent_private"] = Field(..., description="Variable visibility scope")
    description: str = Field(..., description="Human-readable description")
    normalization: NormalizationConfig = Field(..., description="Normalization configuration")

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
