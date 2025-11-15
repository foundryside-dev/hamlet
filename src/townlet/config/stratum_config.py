"""Stratum-level configuration DTO.

This module defines the Pydantic DTO for stratum.yaml files in the v2.1
configuration system. A stratum defines the substrate (spatial/aspatial),
vision support, and temporal mechanics capabilities.

Example:
    >>> config = StratumConfig.from_yaml(Path("configs/default_curriculum/stratum.yaml"))
    >>> print(config.substrate.type)
    'grid'
    >>> print(config.substrate.grid.width)
    8
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class GridConfig(BaseModel):
    """Grid substrate configuration."""

    topology: Literal["square", "hexagonal", "triangular"] = Field(..., description="Grid cell topology")
    width: int = Field(..., description="Grid width in cells", gt=0)
    height: int = Field(..., description="Grid height in cells", gt=0)
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior when agent reaches edge")
    distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = Field(..., description="Distance calculation method")
    observation_encoding: Literal["relative", "scaled", "absolute"] = Field(..., description="Coordinate encoding mode for observations")

    class Config:
        extra = "forbid"


class SubstrateConfig(BaseModel):
    """Substrate configuration (spatial or aspatial)."""

    type: Literal["grid", "grid3d", "gridnd", "continuous", "continuousnd", "aspatial"] = Field(..., description="Substrate type")
    grid: GridConfig | None = Field(None, description="Grid substrate parameters")

    class Config:
        extra = "forbid"


class StratumConfigRoot(BaseModel):
    """Root structure for stratum.yaml file."""

    version: str = Field(..., description="Config schema version")
    substrate: SubstrateConfig = Field(..., description="Substrate configuration")
    vision_support: Literal["global_only", "local_only", "both"] = Field(..., description="Vision modes supported by this stratum")
    temporal_support: Literal["enabled", "disabled"] = Field(..., description="Whether temporal mechanics are supported")

    class Config:
        extra = "forbid"


class StratumConfig(BaseModel):
    """Top-level stratum configuration.

    This DTO wraps the 'stratum' key from stratum.yaml.
    """

    stratum: StratumConfigRoot = Field(..., description="Stratum configuration")

    class Config:
        extra = "forbid"

    @classmethod
    def from_yaml(cls, path: Path) -> "StratumConfig":
        """Load stratum configuration from YAML file.

        Args:
            path: Path to stratum.yaml file

        Returns:
            StratumConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
