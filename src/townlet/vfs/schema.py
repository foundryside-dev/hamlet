"""VFS schema definitions using Pydantic.

Variable & Feature System (VFS) schemas for defining variables, observations,
and action effects. These schemas enable declarative configuration of the
environment's state space.

Supports typed variables, derivation graphs, complex types, and expression parsing
for the runtime VFS profile pipeline.
"""

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

__all__ = [
    "NormalizationSpec",
    "WriteSpec",
    "ObservationField",
    "VariableDef",
    "VariableScope",
    "load_variables_reference_config",
]


class VariableScope(StrEnum):
    """Variable scope determines storage layout and access patterns."""

    GLOBAL = "global"  # Shared across all agents (world state)
    AGENT = "agent"  # Per-agent state ([batch, ...])
    AGENT_PRIVATE = "agent_private"  # Hidden from agent observations
    ITEM = "item"  # Per-item state ([max_items, ...])


class NormalizationSpec(BaseModel):
    """Observation normalization specification.

    Supports two normalization kinds:
    - minmax: Linear scaling to [min, max] range
    - zscore: Z-score normalization (value - mean) / std

    Examples:
        # Scalar minmax
        NormalizationSpec(kind="minmax", min=0.0, max=1.0)

        # Vector minmax
        NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[7.0, 7.0])

        # Scalar z-score
        NormalizationSpec(kind="zscore", mean=0.5, std=0.2)
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["minmax", "zscore"] = Field(description="Normalization method: minmax or zscore")

    # MinMax parameters (can be scalar or list)
    min: float | list[float] | None = Field(
        default=None,
        description="Minimum value(s) for minmax normalization",
    )
    max: float | list[float] | None = Field(
        default=None,
        description="Maximum value(s) for minmax normalization",
    )

    # Z-score parameters (can be scalar or list)
    mean: float | list[float] | None = Field(
        default=None,
        description="Mean value(s) for zscore normalization",
    )
    std: float | list[float] | None = Field(
        default=None,
        description="Standard deviation(s) for zscore normalization",
    )

    @model_validator(mode="after")
    def validate_normalization_params(self) -> "NormalizationSpec":
        """Validate that required parameters are present for each kind."""
        if self.kind == "minmax":
            if self.min is None:
                raise ValueError("minmax normalization requires 'min' parameter")
            if self.max is None:
                raise ValueError("minmax normalization requires 'max' parameter")
        elif self.kind == "zscore":
            if self.mean is None:
                raise ValueError("zscore normalization requires 'mean' parameter")
            if self.std is None:
                raise ValueError("zscore normalization requires 'std' parameter")
        return self


class WriteSpec(BaseModel):
    """Action write specification (variable update).

    Defines how an action modifies a variable's value.

    Expressions are parsed into ASTs during profile/effect compilation before
    runtime execution.

    Examples:
        # Simple constant
        WriteSpec(variable_id="energy", expression="-0.005")

        # Complex expression
        WriteSpec(variable_id="money", expression="money + 10.0")
    """

    model_config = ConfigDict(extra="forbid")

    variable_id: str = Field(
        min_length=1,
        description="ID of the variable to write to",
    )

    expression: str = Field(
        min_length=1,
        description="Expression to parse, type-check, and evaluate through the expression runtime",
    )


class ObservationField(BaseModel):
    """Observation field specification.

    Maps a variable to an observation field that will be exposed to agents
    or other systems (like the BAC compiler).

    Examples:
        # Scalar observation
        ObservationField(
            id="obs_energy",
            source_variable="energy",
            exposed_to=["agent"],
            shape=[],
        )

        # Vector observation with normalization
        ObservationField(
            id="obs_position",
            source_variable="position",
            exposed_to=["agent"],
            shape=[2],
            normalization=NormalizationSpec(kind="minmax", min=[0,0], max=[7,7]),
        )
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        min_length=1,
        description="Unique identifier for this observation field",
    )

    source_variable: str = Field(
        min_length=1,
        description="ID of the variable this observation reads from",
    )

    exposed_to: list[str] = Field(
        min_length=1,
        description="Who can observe this field (e.g., ['agent', 'acs', 'bac'])",
    )

    shape: list[int] = Field(
        description="Shape of observation ([] for scalar, [N] for vector)",
    )

    normalization: NormalizationSpec | None = Field(
        default=None,
        description="Optional normalization to apply before exposing",
    )

    # NEW FIELDS for QUICK-05: Structured Observation Masking
    semantic_type: Literal["bars", "spatial", "affordance", "temporal", "custom"] = Field(
        default="custom",
        description=(
            "Semantic grouping for structured encoders. "
            "bars: meter values, spatial: position/grid, affordance: affordance state, "
            "temporal: time/progress, custom: user-defined variables"
        ),
    )

    curriculum_active: bool = Field(
        default=True,
        description=(
            "Whether this field is active in current curriculum level. "
            "False indicates padding dimensions that should be masked out during training. "
            "Used by structured encoders and RND to ignore inactive affordances/meters."
        ),
    )


class VariableDef(BaseModel):
    """Variable definition for VFS.

    Defines a single variable in the VFS state space with its type, scope,
    lifetime, and access control.

    Scope semantics:
    - global: Single value shared by all agents (e.g., time_of_day)
    - agent: Per-agent value, observable by all agents (e.g., energy, position)
    - agent_private: Per-agent value, observable only by owner (e.g., home_position)

    Type system (Phase 1):
    - scalar: Single float value
    - vec2i, vec3i: Fixed 2D/3D integer vectors
    - vecNi: N-dimensional integer vector (requires dims field)
    - vecNf: N-dimensional float vector (requires dims field)
    - bool: Boolean value

    Examples:
        # Scalar variable
        VariableDef(
    model_config = ConfigDict(extra="forbid")

    id="energy",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=1.0,
        )

        # Vector variable
        VariableDef(
            id="position",
            scope="agent",
            type="vecNf",
            dims=2,
            lifetime="episode",
            readable_by=["agent"],
            writable_by=["engine"],
            default=[0.0, 0.0],
        )
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        min_length=1,
        description="Unique identifier for this variable",
    )

    exposed_to: list[str] = Field(
        default_factory=list,
        description="Who can observe this variable (e.g., ['agent', 'engine'])",
    )

    semantic_type: Literal["bars", "spatial", "affordance", "temporal", "custom"] = Field(
        default="custom",
        description="Semantic grouping for structured encoders (bars, spatial, affordance, temporal, custom)",
    )

    scope: VariableScope | Literal["global", "agent", "agent_private", "item"] = Field(
        description="Scope: global (shared), agent (per-agent public), agent_private (per-agent private), item (per-item)",
    )

    type: Literal[
        "scalar",
        "vec2i",
        "vec3i",
        "vec2f",
        "vec3f",
        "vecNi",
        "vecNf",
        "bool",
        "agent_ref",
        "item_ref",
        "affordance_ref",
        "effect_ref",
        "tensor1d",
        "tensor2d",
        "tensor3d",
        "tensorNd",
    ] = Field(description="Variable type (scalar, vector, bool, reference, or tensor)")

    dims: int | None = Field(
        default=None,
        ge=1,
        description="Number of dimensions for vecNi/vecNf types (required for those types)",
    )

    lifetime: Literal["tick", "episode", "persistent"] = Field(
        description="Lifetime: tick (recomputed each step), episode (persistent within episode), or persistent (survives episodes)",
    )

    readable_by: list[str] = Field(
        min_length=1,
        description="Who can read this variable (e.g., ['agent', 'engine', 'acs'])",
    )

    writable_by: list[str] = Field(
        min_length=1,
        description="Who can write this variable (e.g., ['engine', 'actions'])",
    )

    default: Any = Field(
        description="Default value (type depends on 'type' field)",
    )

    shape: list[int] | None = Field(
        default=None,
        description="Shape for tensor types (e.g., [10] for tensor1d, [4,4] for tensor2d)",
    )

    initial_value_mode: Literal["zeros", "ones", "eye", "random_normal", "random_uniform"] | None = Field(
        default=None,
        description="Initialization mode for tensor types (defaults to zeros when omitted)",
    )

    initial_value_params: dict[str, Any] | None = Field(
        default=None,
        description="Optional parameters for initialization (mean/std for random_normal, low/high for random_uniform)",
    )

    normalization: NormalizationSpec | None = Field(
        default=None,
        description="Normalization specification applied when exposing this variable",
    )

    description: str | None = Field(
        default=None,
        description="Human-readable description of this variable",
    )

    observable: bool = Field(
        default=False,
        description="Whether this variable should be included in agent observations (for mark-and-sweep evaluation)",
    )

    @model_validator(mode="after")
    def validate_vector_types(self) -> "VariableDef":
        """Validate that vecNi/vecNf have dims field, scalar/bool do not."""
        if self.type in ("vecNi", "vecNf"):
            if self.dims is None:
                raise ValueError(f"Variable '{self.id}' with type '{self.type}' requires 'dims' field")
        elif self.type in ("scalar", "bool"):
            if self.dims is not None:
                raise ValueError(f"Variable '{self.id}' with type '{self.type}' should not have 'dims' field")
        # vec2i, vec3i, vec2f, vec3f have implicit dims (2, 3) - no dims field needed

        # Tensor types require explicit shape and do not use dims
        if self.type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
            if not self.shape:
                raise ValueError(f"Variable '{self.id}' with type '{self.type}' requires a non-empty 'shape' list")
            if self.dims is not None:
                raise ValueError(f"Variable '{self.id}' with type '{self.type}' should not set 'dims'; use 'shape' instead")

            rank = len(self.shape)
            if self.type == "tensor1d" and rank != 1:
                raise ValueError(f"Variable '{self.id}' with type 'tensor1d' must have 1D shape, got rank {rank}")
            if self.type == "tensor2d" and rank != 2:
                raise ValueError(f"Variable '{self.id}' with type 'tensor2d' must have 2D shape, got rank {rank}")
            if self.type == "tensor3d" and rank != 3:
                raise ValueError(f"Variable '{self.id}' with type 'tensor3d' must have 3D shape, got rank {rank}")
            if self.type == "tensorNd" and rank < 1:
                raise ValueError(f"Variable '{self.id}' with type 'tensorNd' must have shape of rank ≥1")

        return self


def load_variables_reference_config(config_dir: Path) -> list[VariableDef]:
    """Load and validate variables_reference.yaml."""

    config_dir = Path(config_dir)
    yaml_path = config_dir / "variables_reference.yaml"

    if not yaml_path.exists():
        raise FileNotFoundError(f"variables_reference.yaml is required but not found in {config_dir}.")

    try:
        with yaml_path.open() as handle:
            data = yaml.safe_load(handle) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse {yaml_path}: {exc}") from exc

    variables_block = data.get("variables")
    if variables_block is None:
        raise ValueError(f"{yaml_path} must include a top-level 'variables' list.")

    # variables_reference.yaml remains a static registry input; expression DSL
    # belongs to vfs_profiles.yaml and effect specs.
    for raw_var in variables_block:
        if "expression" in raw_var:
            raise ValueError(
                "variables_reference.yaml must define static variables only; expressions belong in vfs_profiles.yaml or effects specs.\n"
                f"  Variable: {raw_var.get('name') or raw_var.get('id')}\n"
                "  Action: remove expression and provide static defaults, or move the derived variable into vfs_profiles.yaml."
            )
        if raw_var.get("scope") == "item":
            raise ValueError("variables_reference.yaml cannot define item-scoped variables; use vfs_profiles.yaml item_profiles.")

    try:
        return [VariableDef(**raw_var) for raw_var in variables_block]
    except ValidationError as exc:
        raise ValueError(f"Invalid variables_reference.yaml: {exc}") from exc
