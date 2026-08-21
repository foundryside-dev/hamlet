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

from townlet.vfs.semantic_type import SemanticType

__all__ = [
    "NormalizationSpec",
    "WriteSpec",
    "ObservationField",
    "VariableDef",
    "VariableScope",
    "VFSScopeExtents",
    "VariablesReferenceData",
    "load_variables_reference_config",
]


class VariableScope(StrEnum):
    """Variable scope determines storage layout and access patterns."""

    GLOBAL = "global"  # Shared across all agents (world state)
    AGENT = "agent"  # Per-agent state ([batch, ...])
    AGENT_PRIVATE = "agent_private"  # Hidden from agent observations
    ITEM = "item"  # Per-item state ([max_items, ...])
    PAIR = "pair"  # Directed agent-agent state ([num_agents, num_agents, ...])
    GROUP = "group"  # Group/faction/team state ([num_groups, ...])
    AFFORDANCE = "affordance"  # Per-affordance-instance state ([num_affordances, ...])
    ZONE = "zone"  # Per-zone state ([num_zones, ...])
    MESSAGE = "message"  # Recent communication buffer state ([num_agents, num_message_slots, ...])


class NormalizationSpec(BaseModel):
    """Observation normalization specification.

    Supports normalization kinds from the VFS v1.1 observation ABI:
    - none: Pass-through
    - minmax: Linear scaling to [min, max] range
    - zscore: Z-score normalization (value - mean) / std
    - cyclical_sin_cos: Encode cyclical scalar values as sin/cos pairs
    - binary: Threshold values into 0/1
    - one_hot: Expand categorical integer ids into one-hot vectors
    - log_scaled: Scale non-negative values logarithmically
    - rank_scaled: Scale batch ranks to [0, 1]
    - masked_value: Replace sentinel values with a configured fill value

    Clamping is a PARAMETER (`clip`), not a kind. It is required on the two
    range-based kinds (`minmax`, `log_scaled`) and forbidden on the rest, which
    have no range to clamp against (hamlet-fba56feca5, PDR-0054 ruling 3).

    `clipped_log_scaled` was DELETED in the same change. It was the only clamping
    member, so an author who wanted a plain clamp had to accept a log curve with
    it. Once `clip` exists as a parameter, `log_scaled` + `clip=True` is exactly
    what `clipped_log_scaled` did, and keeping both would be PDR-0053 taxonomy
    shape #3 — two members, one behaviour — authored deliberately while cleaning
    up that very shape. `docs/architecture/vfs.md` §9.2's own example
    (`kind: clipped_log_scaled ... clip: true`) carried the redundancy already.

    Examples:
        # Scalar minmax, pure affine rescaling — out-of-range input stays out of range
        NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False)

        # Vector minmax, clamped into the declared range first
        NormalizationSpec(kind="minmax", min=[0.0, 0.0], max=[7.0, 7.0], clip=True)

        # Scalar z-score (no range, so no clip)
        NormalizationSpec(kind="zscore", mean=0.5, std=0.2)
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal[
        "none",
        "minmax",
        "zscore",
        "cyclical_sin_cos",
        "one_hot",
        "binary",
        "log_scaled",
        "rank_scaled",
        "masked_value",
    ] = Field(description="Normalization method from the VFS v1.1 vocabulary")

    # MinMax parameters (can be scalar or list)
    min: float | list[float] | None = Field(
        default=None,
        description="Minimum value(s) for minmax/log-scaled normalization",
    )
    max: float | list[float] | None = Field(
        default=None,
        description="Maximum value(s) for minmax/log-scaled normalization",
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

    period: float | None = Field(
        default=None,
        description="Positive period for cyclical_sin_cos normalization",
    )

    categories: int | None = Field(
        default=None,
        description="Category count for one_hot normalization",
    )

    threshold: float | None = Field(
        default=None,
        description="Threshold for binary normalization",
    )

    mask_value: float | None = Field(
        default=None,
        description="Sentinel value replaced by masked_value normalization",
    )

    fill_value: float | None = Field(
        default=None,
        description="Replacement value for masked_value normalization",
    )

    clip: bool | None = Field(
        default=None,
        description=(
            "Clamp the value into [min, max] before scaling. REQUIRED on the range-based "
            "kinds (minmax, log_scaled) and forbidden on the rest. `None` is not a default: "
            "the validator rejects it wherever the parameter applies (No-Defaults Principle)."
        ),
    )

    @model_validator(mode="after")
    def validate_normalization_params(self) -> "NormalizationSpec":
        """Validate that required parameters are present for each kind."""
        range_based = self.kind in {"minmax", "log_scaled"}
        if range_based and self.clip is None:
            raise ValueError(
                f"{self.kind} normalization requires an explicit 'clip' parameter (true or false).\n"
                "  Rule: clamping is a declared choice, never inferred. Declare clip: false for pure\n"
                "  scaling, or clip: true to clamp into [min, max] first."
            )
        if not range_based and self.clip is not None:
            raise ValueError(
                f"{self.kind} normalization does not accept a 'clip' parameter — it has no range to clamp against.\n"
                "  Rule: clip applies only to minmax and log_scaled."
            )

        if self.kind == "minmax":
            if self.min is None:
                raise ValueError("minmax normalization requires 'min' parameter")
            if self.max is None:
                raise ValueError("minmax normalization requires 'max' parameter")
            if not self._bounds_are_ordered():
                raise ValueError("minmax normalization requires 'min' < 'max'")
        elif self.kind == "zscore":
            if self.mean is None:
                raise ValueError("zscore normalization requires 'mean' parameter")
            if self.std is None:
                raise ValueError("zscore normalization requires 'std' parameter")
            if self._contains_zero(self.std):
                raise ValueError("zscore normalization requires non-zero 'std'")
        elif self.kind == "cyclical_sin_cos":
            if self.period is None or self.period <= 0:
                raise ValueError("cyclical_sin_cos normalization requires positive 'period'")
        elif self.kind == "one_hot":
            if self.categories is None or self.categories < 2:
                raise ValueError("one_hot normalization requires at least 2 categories")
        elif self.kind == "binary":
            if self.threshold is None:
                raise ValueError("binary normalization requires 'threshold'")
        elif self.kind == "log_scaled":
            if self.min is None or self.max is None:
                raise ValueError(f"{self.kind} normalization requires 'min' and 'max' parameters")
            if not self._bounds_are_ordered():
                raise ValueError(f"{self.kind} normalization requires 'min' < 'max'")
        elif self.kind == "masked_value":
            if self.mask_value is None:
                raise ValueError("masked_value normalization requires 'mask_value'")
            if self.fill_value is None:
                raise ValueError("masked_value normalization requires 'fill_value'")
        return self

    def _bounds_are_ordered(self) -> bool:
        """Return whether min/max parameters are broadcast-compatible and ordered."""
        if self.min is None or self.max is None:
            return False
        min_values = self.min if isinstance(self.min, list) else [self.min]
        max_values = self.max if isinstance(self.max, list) else [self.max]
        if len(min_values) == 1 and len(max_values) > 1:
            min_values = min_values * len(max_values)
        if len(max_values) == 1 and len(min_values) > 1:
            max_values = max_values * len(min_values)
        if len(min_values) != len(max_values):
            return False
        return all(min_value < max_value for min_value, max_value in zip(min_values, max_values, strict=True))

    @staticmethod
    def _contains_zero(value: float | list[float]) -> bool:
        values = value if isinstance(value, list) else [value]
        return any(item == 0 for item in values)


class WriteSpec(BaseModel):
    """Action write specification (variable update).

    Defines how an action modifies a variable's value and how the transition
    compiler should schedule, compose, clamp, and audit the write.

    Expressions are parsed into ASTs during profile/effect compilation before
    runtime execution.

    Examples:
        # Simple constant
        WriteSpec(
            variable_id="energy",
            expression="-0.005",
            condition=None,
            composition="additive_delta",
            phase="action_costs",
            priority=10,
            clamp=(0.0, 1.0),
            telemetry_label="movement_energy_cost",
        )

        # Complex expression
        WriteSpec(
            variable_id="money",
            expression="money + 10.0",
            condition=None,
            composition="overwrite",
            phase="action_effects",
            priority=0,
            clamp=None,
            telemetry_label="wage_credit",
        )
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

    condition: str | None = Field(
        description="Optional mask or predicate expression that gates this write. Pass None for unconditional writes.",
    )

    composition: Literal[
        "overwrite",
        "additive_delta",
        "multiplicative_modifier",
        "min",
        "max",
        "clamp",
        "priority_write",
        "last_write_wins",
        "claim_if_free",
        "capacity_claim",
        "append_event",
    ] = Field(
        description="How to compose this write with other writes targeting the same variable in the same phase",
    )

    phase: str = Field(
        min_length=1,
        description="Transition phase where this write is scheduled",
    )

    priority: int = Field(
        ge=0,
        description="Non-negative ordering key within the transition phase",
    )

    clamp: tuple[float, float] | None = Field(
        description="Optional inclusive post-write bounds. Pass None when no clamp applies.",
    )

    telemetry_label: str = Field(
        min_length=1,
        description="Human-readable audit label emitted with write telemetry",
    )

    @model_validator(mode="after")
    def validate_write_metadata(self) -> "WriteSpec":
        """Validate explicit VFS v1.1 transition metadata."""
        if self.condition is not None and not self.condition.strip():
            raise ValueError("condition must be None or a non-empty expression")
        if not self.phase.strip():
            raise ValueError("phase must be a non-empty transition phase")
        if not self.telemetry_label.strip():
            raise ValueError("telemetry_label must be non-empty")
        if self.clamp is not None:
            low, high = self.clamp
            if low > high:
                raise ValueError("clamp lower bound must be <= upper bound")
        return self


class ObservationField(BaseModel):
    """Observation field specification.

    Maps a variable to an observation field that will be exposed to agents
    or other systems (like the VTC or brain compiler).

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
            normalization=NormalizationSpec(kind="minmax", min=[0,0], max=[7,7], clip=False),
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

    semantic_type: SemanticType = Field(
        description=(
            "Semantic group of this field in the observation vector — one member of the closed "
            "vocabulary in townlet.vfs.semantic_type (PDR-0047). Required: it is part of the "
            "field's identity (observation_schema_hash) and names its group slice, so it is never "
            "defaulted."
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

    scope: VariableScope | Literal["global", "agent", "agent_private", "item", "pair", "group", "affordance", "zone", "message"] = Field(
        description=(
            "Scope: global (shared), agent (per-agent public), agent_private (per-agent private), item (per-item), "
            "pair (directed agent-agent), group, affordance, zone, or message"
        ),
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
        "message_token",
    ] = Field(description="Variable type (scalar, vector, bool, reference, tensor, or message token)")

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
        if self.type in ("vecNi", "vecNf", "message_token"):
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

        if self.type == "message_token" and self.shape is not None:
            raise ValueError(f"Variable '{self.id}' with type 'message_token' should not set 'shape'; use 'dims' instead")

        return self


class VFSScopeExtents(BaseModel):
    """Storage extents for the zone/group/message variable scopes.

    Declared in the optional top-level ``extents:`` block of
    variables_reference.yaml — the only file that can declare variables with
    these scopes. An extent is required exactly when a variable of the matching
    scope is declared; the loader rejects the pack otherwise, so the failure is
    a compile error and never a green compile that crashes at env construction
    (hamlet-9e1ae3b7a2).
    """

    model_config = ConfigDict(extra="forbid")

    num_zones: int | None = Field(default=None, ge=1, description="Number of zone-scope storage rows")
    num_groups: int | None = Field(default=None, ge=1, description="Number of group-scope storage rows")
    num_message_slots: int | None = Field(default=None, ge=1, description="Recent-message buffer slots per agent")


class VariablesReferenceData(BaseModel):
    """Parsed contents of variables_reference.yaml the compiler consumes."""

    model_config = ConfigDict(frozen=True)

    variables: tuple[VariableDef, ...]
    extents: VFSScopeExtents | None


_SCOPE_EXTENT_FIELD: dict[VariableScope, str] = {
    VariableScope.ZONE: "num_zones",
    VariableScope.GROUP: "num_groups",
    VariableScope.MESSAGE: "num_message_slots",
}


def load_variables_reference_config(config_dir: Path) -> VariablesReferenceData:
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
        variables = tuple(VariableDef(**raw_var) for raw_var in variables_block)
    except ValidationError as exc:
        raise ValueError(f"Invalid variables_reference.yaml: {exc}") from exc

    extents_block = data.get("extents")
    try:
        extents = VFSScopeExtents(**extents_block) if extents_block is not None else None
    except ValidationError as exc:
        raise ValueError(f"Invalid extents block in {yaml_path}: {exc}") from exc

    # A zone/group/message-scoped variable sizes its storage by the matching
    # extent; without one the registry cannot allocate. Reject HERE, so the
    # author gets a compile error, not a crash at env construction.
    for variable in variables:
        extent_field = _SCOPE_EXTENT_FIELD.get(VariableScope(variable.scope))
        if extent_field is None:
            continue
        declared = getattr(extents, extent_field) if extents is not None else None
        if declared is None:
            raise ValueError(
                f"Variable '{variable.id}' uses {VariableScope(variable.scope).value} scope "
                f"but the pack declares no '{extent_field}' extent.\n"
                f"  File: {yaml_path}\n"
                f"  Action: add a top-level extents block:\n"
                f"    extents:\n"
                f"      {extent_field}: <positive int>"
            )

    return VariablesReferenceData(variables=variables, extents=extents)
