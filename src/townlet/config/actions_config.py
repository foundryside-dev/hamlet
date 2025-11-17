"""Actions-level configuration DTO.

This module defines the Pydantic DTO for actions.yaml files in the v2.1
configuration system. An actions config defines substrate actions, custom
actions, and action label presets.

Example:
    >>> config = ActionsConfig.from_yaml(Path("configs/default_curriculum/actions.yaml"))
    >>> print(config.substrate_actions.inherit)
    True
    >>> print(len(config.custom_actions))
    4
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class SubstrateActionsConfig(BaseModel):
    """Substrate actions configuration."""

    inherit: bool = Field(..., description="Whether to inherit default substrate actions (movement, etc.)")

    class Config:
        extra = "forbid"


class CustomActionConfig(BaseModel):
    """Custom action definition."""

    name: str = Field(..., description="Action name (e.g., 'INTERACT', 'WAIT')")
    description: str = Field(..., description="Human-readable description")
    enabled_by_default: bool = Field(..., description="Whether this action is enabled by default")
    costs: dict[str, float] | None = Field(
        default=None,
        description="Optional per-step meter costs (meter: value).",
    )
    effects: dict[str, float] | None = Field(
        default=None,
        description="Optional per-step meter effects (meter: value).",
    )

    class Config:
        extra = "forbid"


class ActionLabelsConfig(BaseModel):
    """Action label preset configuration."""

    preset: Literal["gaming", "6dof", "cardinal", "math"] = Field(..., description="Label preset for action names")

    class Config:
        extra = "forbid"


class ActionsConfigRoot(BaseModel):
    """Root structure for actions.yaml file."""

    version: str = Field(..., description="Config schema version")
    substrate_actions: SubstrateActionsConfig = Field(..., description="Substrate actions configuration")
    custom_actions: list[CustomActionConfig] = Field(..., description="Custom action definitions")
    labels: ActionLabelsConfig = Field(..., description="Action label configuration")

    class Config:
        extra = "forbid"


class ActionsConfig(BaseModel):
    """Top-level actions configuration.

    This DTO wraps the 'actions' key from actions.yaml.
    """

    actions: ActionsConfigRoot = Field(..., description="Actions configuration")

    class Config:
        extra = "forbid"

    @classmethod
    def from_yaml(cls, path: Path) -> "ActionsConfig":
        """Load actions configuration from YAML file.

        Args:
            path: Path to actions.yaml file

        Returns:
            ActionsConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
