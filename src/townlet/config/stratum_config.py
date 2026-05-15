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
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ObservationModeConfig(BaseModel):
    """Observation mode selection for runtime observation layout."""

    mode: Literal["full_auto", "max_compact", "full_manual"] = Field(
        ...,
        description="Observation layout strategy: full_auto (include all), max_compact (drop masked), or full_manual (explicit list).",
    )
    include_fields: list[str] | None = Field(
        default=None,
        description="Field names to include when mode=full_manual. Must be non-empty and match observation field names.",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_manual(self) -> "ObservationModeConfig":
        if self.mode == "full_manual":
            if not self.include_fields:
                raise ValueError("full_manual observation_mode requires include_fields to be provided and non-empty.")
        return self


class GridConfig(BaseModel):
    """Grid substrate configuration."""

    topology: Literal["square", "cubic"] = Field(..., description="Grid cell topology (square=2D, cubic=3D)")
    width: int = Field(..., description="Grid width in cells", gt=0)
    height: int = Field(..., description="Grid height in cells", gt=0)
    depth: int | None = Field(None, description="Grid depth in cells (required for cubic topology)", gt=0)
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior when agent reaches edge")
    distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = Field(..., description="Distance calculation method")
    observation_encoding: Literal["relative", "scaled", "absolute"] = Field(..., description="Coordinate encoding mode for observations")
    diagonals: bool = Field(..., description="Whether diagonal movement actions are enabled for grid substrates")

    model_config = ConfigDict(extra="forbid")

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
    topology: Literal["hypercube"] = Field(..., description="Grid topology (explicit to avoid hidden defaults)")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dimensions(self) -> "GridNDConfig":
        if not self.dimension_sizes:
            raise ValueError("GridNDConfig.dimension_sizes must contain at least one dimension size.")
        if any(size <= 0 for size in self.dimension_sizes):
            raise ValueError("All GridNDConfig.dimension_sizes entries must be positive integers.")
        return self


class ActionDiscretizationConfig(BaseModel):
    """Discretized action configuration for continuous substrates.

    All fields required (no implicit defaults). This controls how many
    discrete directions and magnitude bins are generated for movement.
    """

    num_directions: int = Field(
        ...,
        ge=8,
        le=32,
        description="Number of discrete directions (e.g., 8 for 45° steps, up to 32)",
    )
    num_magnitudes: int = Field(
        ...,
        ge=3,
        le=7,
        description="Number of magnitude bins (>=3). Magnitudes span [0.0, 1.0] inclusively.",
    )

    model_config = ConfigDict(extra="forbid")


class ContinuousConfig(BaseModel):
    """Continuous substrate configuration (1D-100D)."""

    dimensions: int = Field(..., ge=1, le=100, description="Number of continuous dimensions")
    bounds: list[tuple[float, float]] = Field(..., description="Bounds for each dimension [(min, max), ...]")
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior at edges")
    movement_delta: float = Field(..., gt=0, description="Discrete movement step for navigation")
    interaction_radius: float = Field(..., gt=0, description="Distance threshold for affordance interaction")
    distance_metric: Literal["euclidean", "manhattan", "chebyshev"] = Field(..., description="Distance calculation method")
    observation_encoding: Literal["relative", "scaled", "absolute"] = Field(..., description="Position encoding strategy")
    action_discretization: ActionDiscretizationConfig = Field(
        ...,
        description=(
            "Discretization of continuous actions. All fields required; no implicit defaults are applied. "
            "{'num_directions': 8-32, 'num_magnitudes': 3-7}"
        ),
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_bounds(self) -> "ContinuousConfig":
        """Ensure bounds match dimensions and are strictly ordered."""
        if len(self.bounds) != self.dimensions:
            raise ValueError(
                f"Number of bounds ({len(self.bounds)}) must match dimensions ({self.dimensions}). "
                "Example for 2D: bounds: [[0.0, 10.0], [0.0, 10.0]]"
            )

        for i, (min_val, max_val) in enumerate(self.bounds):
            if min_val >= max_val:
                raise ValueError(f"bounds[{i}] invalid: min ({min_val}) must be < max ({max_val})")

        return self


class AspatialConfig(BaseModel):
    """Aspatial substrate marker (no positional fields)."""

    model_config = ConfigDict(extra="forbid")


class SubstrateConfig(BaseModel):
    """Substrate configuration (spatial or aspatial)."""

    type: Literal["grid", "grid3d", "gridnd", "continuous", "continuousnd", "aspatial"] = Field(..., description="Substrate type")
    grid: GridConfig | None = Field(None, description="Grid substrate parameters (2D or 3D)")
    gridnd: GridNDConfig | None = Field(None, description="GridND substrate parameters (4D+)")
    continuous: ContinuousConfig | None = Field(None, description="Continuous substrate parameters (required for continuous/continuousnd)")
    aspatial: AspatialConfig | None = Field(None, description="Aspatial substrate parameters (required for aspatial)")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_substrate(self) -> "SubstrateConfig":
        """Enforce type-specific config presence (no silent defaults)."""
        if self.type == "grid" and self.grid is None:
            raise ValueError("type='grid' requires a grid block.")
        if self.type == "gridnd" and self.gridnd is None:
            raise ValueError("type='gridnd' requires a gridnd block.")
        if self.type in {"continuous", "continuousnd"} and self.continuous is None:
            raise ValueError(f"type='{self.type}' requires a continuous block.")
        if self.type == "aspatial" and self.aspatial is None:
            raise ValueError("type='aspatial' requires an aspatial block.")

        provided = [
            cfg is not None
            for cfg in (
                self.grid,
                self.gridnd,
                self.continuous,
                self.aspatial,
            )
        ]
        if sum(provided) > 1:
            raise ValueError("Only one substrate configuration block may be specified.")

        return self


class StratumConfigRoot(BaseModel):
    """Root structure for stratum.yaml file."""

    version: str = Field(..., description="Config schema version")
    substrate: SubstrateConfig = Field(..., description="Substrate configuration")
    vision_support: Literal["global", "partial", "both", "none"] = Field(..., description="Vision modes supported by this stratum")
    temporal_support: Literal["enabled", "disabled"] = Field(..., description="Whether temporal mechanics are supported")
    observation_mode: ObservationModeConfig = Field(
        ...,
        description="Observation layout mode: full_auto | max_compact | full_manual (requires include_fields).",
    )

    model_config = ConfigDict(extra="forbid")


class StratumConfig(BaseModel):
    """Top-level stratum configuration.

    This DTO wraps the 'stratum' key from stratum.yaml.
    """

    stratum: StratumConfigRoot = Field(..., description="Stratum configuration")

    model_config = ConfigDict(extra="forbid")

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
