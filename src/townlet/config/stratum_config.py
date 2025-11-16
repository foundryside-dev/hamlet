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
from pydantic import BaseModel, Field, model_validator


class GridConfig(BaseModel):
    """Grid substrate configuration."""

    topology: Literal["square", "cubic"] = Field(..., description="Grid cell topology (square=2D, cubic=3D)")
    width: int = Field(..., description="Grid width in cells", gt=0)
    height: int = Field(..., description="Grid height in cells", gt=0)
    depth: int | None = Field(None, description="Grid depth in cells (required for cubic topology)", gt=0)
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior when agent reaches edge")
    distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = Field(..., description="Distance calculation method")
    observation_encoding: Literal["relative", "scaled", "absolute"] = Field(..., description="Coordinate encoding mode for observations")

    class Config:
        extra = "forbid"

    @model_validator(mode="after")
    def validate_cubic_depth(self) -> "GridConfig":
        """Ensure cubic topology includes depth and square topology omits it."""
        if self.topology == "cubic":
            if self.depth is None:
                raise ValueError(
                    "Grid topology 'cubic' requires a 'depth' field.\n"
                    "Example:\n"
                    "  grid:\n"
                    "    topology: cubic\n"
                    "    width: 8\n"
                    "    height: 8\n"
                    "    depth: 3\n"
                )
        else:
            # square topology should not specify depth
            if self.depth is not None:
                raise ValueError("Grid topology 'square' must not specify 'depth'. Remove depth or use topology: cubic.")
        return self


class GridNDConfig(BaseModel):
    """N-dimensional grid substrate configuration (4D+ discrete grids)."""

    dimension_sizes: list[int] = Field(..., description="Size of each dimension [d0, d1, ..., dN] (N>=4 recommended)")
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior at edges")
    distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = Field(..., description="Distance calculation method")
    observation_encoding: Literal["relative", "scaled", "absolute"] = Field(..., description="Coordinate encoding mode for observations")

    class Config:
        extra = "forbid"

    @model_validator(mode="after")
    def validate_dimensions(self) -> "GridNDConfig":
        if not self.dimension_sizes:
            raise ValueError("GridNDConfig.dimension_sizes must contain at least one dimension size.")
        if any(size <= 0 for size in self.dimension_sizes):
            raise ValueError("All GridNDConfig.dimension_sizes entries must be positive integers.")
        return self


class SubstrateConfig(BaseModel):
    """Substrate configuration (spatial or aspatial)."""

    type: Literal["grid", "grid3d", "gridnd", "continuous", "continuousnd", "aspatial"] = Field(..., description="Substrate type")
    grid: GridConfig | None = Field(None, description="Grid substrate parameters (2D or 3D)")
    gridnd: GridNDConfig | None = Field(None, description="GridND substrate parameters (4D+)")

    class Config:
        extra = "forbid"


class StratumConfigRoot(BaseModel):
    """Root structure for stratum.yaml file."""

    version: str = Field(..., description="Config schema version")
    substrate: SubstrateConfig = Field(..., description="Substrate configuration")
    vision_support: Literal["global", "partial", "both", "none"] = Field(..., description="Vision modes supported by this stratum")
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
