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

import math
from pathlib import Path
from typing import Final, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

# Every substrate rule the factory's constructors enforce (`substrate/grid2d.py`,
# `grid3d.py`, `gridnd.py`, `continuous.py`, `continuousnd.py`) is stated here too, so a pack
# that breaks one refuses at parse, located at its declaration, instead of as a bare
# ValueError from inside the compiler.
GRIDND_MIN_RANK = 4
CONTINUOUSND_MIN_RANK = 4
CONTINUOUS_MAX_RANK = 3

MAX_POSITION_RANK: Final[int] = 8
"""The widest position a token carries (`universe/dto/token_spec.py` pads every position to
it, and the transfer contract `token_type_schema_hash` covers that width). A substrate's rank
cannot exceed it, so it is also the upper rank bound of `gridnd` and `continuousnd`."""


class GridConfig(BaseModel):
    """Grid substrate configuration."""

    topology: Literal["square", "cubic"] = Field(..., description="Grid cell topology (square=2D, cubic=3D)")
    width: int = Field(..., description="Grid width in cells", gt=0)
    height: int = Field(..., description="Grid height in cells", gt=0)
    depth: int | None = Field(None, description="Grid depth in cells (required for cubic topology)", gt=0)
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior when agent reaches edge")
    distance_metric: Literal["manhattan", "euclidean", "chebyshev"] = Field(..., description="Distance calculation method")
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
    topology: Literal["hypercube"] = Field(..., description="Grid topology (explicit to avoid hidden defaults)")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dimensions(self) -> "GridNDConfig":
        """The rank rule GridNDSubstrate enforces, refused here so it is located at the declaration."""
        rank = len(self.dimension_sizes)
        if rank < GRIDND_MIN_RANK or rank > MAX_POSITION_RANK:
            raise ValueError(
                f"gridnd.dimension_sizes declares {rank} dimension(s); a gridnd substrate has "
                f"{GRIDND_MIN_RANK} to {MAX_POSITION_RANK} (MAX_POSITION_RANK, the widest position a token "
                "carries). For 2 or 3 dimensions use type: grid (topology: square or cubic)."
            )
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
    """Continuous substrate configuration (1 to MAX_POSITION_RANK dimensions)."""

    dimensions: int = Field(..., ge=1, le=MAX_POSITION_RANK, description="Number of continuous dimensions")
    bounds: list[tuple[float, float]] = Field(..., description="Bounds for each dimension [(min, max), ...]")
    boundary: Literal["clamp", "wrap", "bounce", "sticky"] = Field(..., description="Boundary behavior at edges")
    movement_delta: float = Field(..., gt=0, description="Discrete movement step for navigation")
    interaction_radius: float = Field(..., gt=0, description="Distance threshold for affordance interaction")
    distance_metric: Literal["euclidean", "manhattan", "chebyshev"] = Field(..., description="Distance calculation method")
    action_discretization: ActionDiscretizationConfig = Field(
        ...,
        description=(
            "Discretization of continuous actions. All fields required; no implicit defaults are applied. "
            "{'num_directions': 8-32, 'num_magnitudes': 3-7}"
        ),
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("interaction_radius")
    @classmethod
    def validate_interaction_radius_fits_bounds(cls, value: float, info: ValidationInfo) -> float:
        """The substrate refuses a space too small to interact in; refused here at its own key."""
        for index, bound in enumerate(info.data.get("bounds") or ()):
            low, high = bound
            # An unordered or infinite bound is refused by validate_bounds, by its own message.
            if math.isfinite(low) and math.isfinite(high) and low < high and high - low < value:
                raise ValueError(
                    f"interaction_radius ({value}) exceeds the span of bounds[{index}] ({high - low}): the space is "
                    "too small for affordance interaction. Widen the bounds or shrink interaction_radius."
                )
        return value

    @model_validator(mode="after")
    def validate_bounds(self) -> "ContinuousConfig":
        """Ensure bounds match dimensions and are strictly ordered."""
        if len(self.bounds) != self.dimensions:
            raise ValueError(
                f"Number of bounds ({len(self.bounds)}) must match dimensions ({self.dimensions}). "
                "Example for 2D: bounds: [[0.0, 10.0], [0.0, 10.0]]"
            )

        for i, (min_val, max_val) in enumerate(self.bounds):
            # An infinite bound compiles and then every position and observation is NaN
            # (normalization divides by the span): refuse it where it is authored.
            if not (math.isfinite(min_val) and math.isfinite(max_val)):
                raise ValueError(f"bounds[{i}] invalid: both bounds must be finite numbers, got [{min_val}, {max_val}]")
            if min_val >= max_val:
                raise ValueError(f"bounds[{i}] invalid: min ({min_val}) must be < max ({max_val})")
        if not math.isfinite(self.movement_delta):
            raise ValueError(f"movement_delta must be a finite number, got {self.movement_delta}")
        if not math.isfinite(self.interaction_radius):
            raise ValueError(f"interaction_radius must be a finite number, got {self.interaction_radius}")

        return self


class AspatialConfig(BaseModel):
    """Aspatial substrate marker (no positional fields)."""

    model_config = ConfigDict(extra="forbid")


class SubstrateConfig(BaseModel):
    """Substrate configuration (spatial or aspatial)."""

    # "grid3d" was deleted from this Literal (WS-7 first knockdown): it never
    # had a SubstrateFactory branch, so it could only compile toward a
    # guaranteed factory crash. The working 3-D path is type: grid with
    # topology: cubic (Grid3DSubstrate).
    type: Literal["grid", "gridnd", "continuous", "continuousnd", "aspatial"] = Field(..., description="Substrate type")
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
        # The rank each continuous family serves (`substrate/factory.py` dispatches on it).
        if self.type == "continuous" and self.continuous is not None and self.continuous.dimensions > CONTINUOUS_MAX_RANK:
            raise ValueError(
                f"type='continuous' serves 1 to {CONTINUOUS_MAX_RANK} dimensions, got continuous.dimensions="
                f"{self.continuous.dimensions}. Use type: continuousnd for {CONTINUOUSND_MIN_RANK} or more."
            )
        if self.type == "continuousnd" and self.continuous is not None and self.continuous.dimensions < CONTINUOUSND_MIN_RANK:
            raise ValueError(
                f"type='continuousnd' serves {CONTINUOUSND_MIN_RANK} to {MAX_POSITION_RANK} dimensions, got "
                f"continuous.dimensions={self.continuous.dimensions}. Use type: continuous for 1 to {CONTINUOUS_MAX_RANK}."
            )

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
