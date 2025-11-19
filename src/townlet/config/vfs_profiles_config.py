"""Configuration DTOs for VFS profiles."""

from typing import Literal

from pydantic import BaseModel, field_validator, model_validator


class GlobalVFSVariableConfig(BaseModel):
    """Configuration for a single global VFS variable.

    Global variables are shared across all agents (e.g., day_count, is_night).
    """

    name: str
    type: Literal["int", "float", "bool", "vec2i", "vec3i", "agent_ref", "item_ref"]
    initial_value: int | float | bool | list | None = None
    expression: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_value_xor_expression(self):
        """Exactly one of initial_value or expression must be set."""
        has_value = self.initial_value is not None
        has_expr = self.expression is not None

        if has_value == has_expr:  # Both true or both false
            raise ValueError(f"Variable '{self.name}' must have exactly one of initial_value or expression (not both, not neither)")

        return self


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


class AgentVFSVariableConfig(BaseModel):
    """Configuration for a single agent VFS variable.

    Agent variables are per-agent state (e.g., motivation, is_crisis).
    """

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
