"""Configuration DTOs for VFS profiles."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "GlobalVFSVariableConfig",
    "GlobalVFSProfileConfig",
    "AgentVFSVariableConfig",
    "AgentVFSProfileConfig",
    "ItemVFSVariableConfig",
    "ItemVFSProfileConfig",
    "VFSProfilesConfig",
]


class GlobalVFSVariableConfig(BaseModel):
    """Configuration for a single global VFS variable.

    Global variables are shared across all agents (e.g., day_count, is_night).
    """

    # Metadata
    id: str | None = None
    exposed_to: list[str] = Field(default_factory=list)

    name: str
    type: Literal[
        "int",
        "float",
        "bool",
        "vec2i",
        "vec3i",
        "vecNi",
        "vecNf",
        "agent_ref",
        "item_ref",
        "tensor1d",
        "tensor2d",
        "tensor3d",
        "tensorNd",
    ]
    dims: int | None = None
    shape: list[int] | None = None
    initial_value: int | float | bool | list | None = None
    initial_value_mode: Literal["zeros", "ones", "eye", "random_normal", "random_uniform"] | None = None
    initial_value_params: dict | None = None
    expression: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one init source (initial_value or initial_value_mode) or expression must be set."""
        has_value = self.initial_value is not None
        has_mode = self.initial_value_mode is not None
        has_expr = self.expression is not None

        provided = int(has_value) + int(has_mode) + int(has_expr)
        if provided == 0:
            raise ValueError(f"Variable '{self.name}' must provide exactly one of initial_value, initial_value_mode, or expression")
        if provided > 1:
            raise ValueError(f"Variable '{self.name}' must choose exactly one of initial_value, initial_value_mode, or expression")

        return self

    @model_validator(mode="after")
    def validate_tensor_shape(self):
        """Tensor types require shape metadata."""
        if self.type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
            if not self.shape:
                raise ValueError(f"Variable '{self.name}' with type '{self.type}' requires a non-empty shape list")
            rank = len(self.shape)
            if self.type == "tensor1d" and rank != 1:
                raise ValueError(f"Variable '{self.name}' with type 'tensor1d' must have 1D shape")
            if self.type == "tensor2d" and rank != 2:
                raise ValueError(f"Variable '{self.name}' with type 'tensor2d' must have 2D shape")
            if self.type == "tensor3d" and rank != 3:
                raise ValueError(f"Variable '{self.name}' with type 'tensor3d' must have 3D shape")
            if self.type == "tensorNd" and rank < 1:
                raise ValueError(f"Variable '{self.name}' with type 'tensorNd' must have shape of rank ≥1")
        if self.type in {"vecNi", "vecNf"}:
            if self.dims is None or self.dims < 1:
                raise ValueError(f"Variable '{self.name}' with type '{self.type}' requires a positive dims value")
        elif self.dims is not None:
            raise ValueError(f"Variable '{self.name}' should not set 'dims' when type is '{self.type}'")
        return self

    model_config = ConfigDict(extra="forbid")


class GlobalVFSProfileConfig(BaseModel):
    """Configuration for global VFS profile.

    Global VFS contains variables shared across all agents.
    """

    variables: list[GlobalVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[GlobalVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables

    @model_validator(mode="after")
    def default_metadata(self):
        """Populate optional metadata defaults to align with VFS-REQ-006."""
        for var in self.variables:
            if var.id is None:
                var.id = var.name
            if not var.exposed_to:
                var.exposed_to = ["agent"]
        return self

    model_config = ConfigDict(extra="forbid")


class AgentVFSVariableConfig(BaseModel):
    """Configuration for a single agent VFS variable.

    Agent variables are per-agent state (e.g., motivation, is_crisis).
    """

    # Metadata
    id: str | None = None
    exposed_to: list[str] = Field(default_factory=list)

    name: str
    type: Literal[
        "int",
        "float",
        "bool",
        "vec2i",
        "vec3i",
        "vecNi",
        "vecNf",
        "agent_ref",
        "item_ref",
        "affordance_ref",
        "effect_ref",
        "tensor1d",
        "tensor2d",
        "tensor3d",
        "tensorNd",
    ]
    dims: int | None = None
    initial_value: int | float | bool | list | None = None
    shape: list[int] | None = None
    initial_value_mode: Literal["zeros", "ones", "eye", "random_normal", "random_uniform"] | None = None
    initial_value_params: dict | None = None
    expression: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one init source (initial_value or initial_value_mode) or expression must be set."""
        has_value = self.initial_value is not None
        has_mode = self.initial_value_mode is not None
        has_expr = self.expression is not None

        provided = int(has_value) + int(has_mode) + int(has_expr)
        if provided == 0:
            raise ValueError(f"Variable '{self.name}' must provide exactly one of initial_value, initial_value_mode, or expression")
        if provided > 1:
            raise ValueError(f"Variable '{self.name}' must choose exactly one of initial_value, initial_value_mode, or expression")

        return self

    @model_validator(mode="after")
    def validate_tensor_shape(self):
        """Tensor types require shape metadata."""
        if self.type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
            if not self.shape:
                raise ValueError(f"Variable '{self.name}' with type '{self.type}' requires a non-empty shape list")
            rank = len(self.shape)
            if self.type == "tensor1d" and rank != 1:
                raise ValueError(f"Variable '{self.name}' with type 'tensor1d' must have 1D shape")
            if self.type == "tensor2d" and rank != 2:
                raise ValueError(f"Variable '{self.name}' with type 'tensor2d' must have 2D shape")
            if self.type == "tensor3d" and rank != 3:
                raise ValueError(f"Variable '{self.name}' with type 'tensor3d' must have 3D shape")
            if self.type == "tensorNd" and rank < 1:
                raise ValueError(f"Variable '{self.name}' with type 'tensorNd' must have shape of rank ≥1")
        if self.type in {"vecNi", "vecNf"}:
            if self.dims is None or self.dims < 1:
                raise ValueError(f"Variable '{self.name}' with type '{self.type}' requires a positive dims value")
        elif self.dims is not None:
            raise ValueError(f"Variable '{self.name}' should not set 'dims' when type is '{self.type}'")
        return self

    model_config = ConfigDict(extra="forbid")


class AgentVFSProfileConfig(BaseModel):
    """Configuration for agent VFS profile.

    Agent VFS contains per-agent state (motivation, crisis flags, etc.).
    """

    variables: list[AgentVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[AgentVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables

    @model_validator(mode="after")
    def default_metadata(self):
        """Populate optional metadata defaults to align with VFS-REQ-006."""
        for var in self.variables:
            if var.id is None:
                var.id = var.name
            if not var.exposed_to:
                var.exposed_to = ["agent"]
        return self

    model_config = ConfigDict(extra="forbid")


class ItemVFSVariableConfig(BaseModel):
    """Configuration for a single item VFS variable.

    Item variables are per-item-instance state (e.g., nutrition, age, is_spoiled).
    """

    # Metadata
    id: str | None = None
    exposed_to: list[str] = Field(default_factory=list)

    name: str
    type: Literal[
        "int",
        "float",
        "bool",
        "vec2i",
        "vec3i",
        "agent_ref",
        "item_ref",
        "affordance_ref",
        "effect_ref",
    ]
    initial_value: int | float | bool | list | None = None
    expression: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one of initial_value or expression must be set."""
        has_value = self.initial_value is not None
        has_expr = self.expression is not None

        if has_value == has_expr:
            raise ValueError(f"Variable '{self.name}' must have exactly one of initial_value or expression (not both, not neither)")

        return self

    @model_validator(mode="after")
    def validate_tensor_disallowed(self):
        """Reject tensor types for item profiles until storage/layout is supported."""
        if self.type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
            raise ValueError(f"Tensor VFS variables are not supported for item profiles yet (variable '{self.name}').")
        return self

    model_config = ConfigDict(extra="forbid")


class ItemVFSProfileConfig(BaseModel):
    """Configuration for item VFS profile.

    Item VFS profiles define reusable state schemas for item types
    (e.g., 'food_stats', 'weapon_stats').
    """

    profile_name: str
    variables: list[ItemVFSVariableConfig]

    @field_validator("variables")
    @classmethod
    def validate_unique_names(cls, variables: list[ItemVFSVariableConfig]):
        """Variable names must be unique within profile."""
        names = [v.name for v in variables]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate variable names: {duplicates}")

        return variables

    @model_validator(mode="after")
    def default_metadata(self):
        """Populate optional metadata defaults to align with VFS-REQ-006."""
        for var in self.variables:
            if var.id is None:
                var.id = var.name
            if not var.exposed_to:
                var.exposed_to = ["agent"]
        return self

    model_config = ConfigDict(extra="forbid")


class VFSProfilesConfig(BaseModel):
    """Top-level configuration for VFS profiles.

    Loaded from vfs_profiles.yaml. Contains:
    - global_profile: Shared variables (day_count, is_night)
    - agent_profile: Per-agent variables (motivation, is_crisis)
    - item_profiles: Named profiles for item types (food_stats, weapon_stats)
    """

    version: Literal["1.0"]
    evaluation_mode: Literal["mark_and_sweep", "eager"]
    debug_logging: bool
    global_profile: GlobalVFSProfileConfig | None = None
    agent_profile: AgentVFSProfileConfig | None = None
    item_profiles: list[ItemVFSProfileConfig] = []

    @field_validator("item_profiles")
    @classmethod
    def validate_unique_profile_names(cls, profiles: list[ItemVFSProfileConfig]):
        """Item profile names must be unique."""
        names = [p.profile_name for p in profiles]
        duplicates = {name for name in names if names.count(name) > 1}

        if duplicates:
            raise ValueError(f"Duplicate item profile names: {duplicates}")

        return profiles

    model_config = ConfigDict(extra="forbid")
