"""Actions-level configuration DTO.

PARSE-TIME DTO: This module validates actions from training.yaml during compilation.
For runtime action configuration used by the environment, see:
    townlet.environment.action_config

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
from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Base model that forbids extra fields (pydantic v2 style)."""

    model_config = ConfigDict(extra="forbid")


class SubstrateActionsConfig(StrictBaseModel):
    """Substrate actions configuration."""

    inherit: bool = Field(..., description="Whether to inherit default substrate actions (movement, etc.)")


class CustomActionConfig(StrictBaseModel):
    """Custom action definition."""

    name: str = Field(..., description="Action name (e.g., 'INTERACT', 'WAIT')")
    description: str = Field(..., description="Human-readable description")
    enabled_by_default: bool = Field(..., description="Whether this action is enabled by default")


class ActionLabelsConfig(StrictBaseModel):
    """Action label preset configuration."""

    preset: Literal["gaming", "6dof", "cardinal", "math"] = Field(..., description="Label preset for action names")


class ActionsConfigRoot(StrictBaseModel):
    """Root structure for actions.yaml file."""

    version: str = Field(..., description="Config schema version")
    substrate_actions: SubstrateActionsConfig = Field(..., description="Substrate actions configuration")
    custom_actions: list[CustomActionConfig] = Field(..., description="Custom action definitions")
    labels: ActionLabelsConfig = Field(..., description="Action label configuration")


class ActionsConfig(StrictBaseModel):
    """Top-level actions configuration.

    This DTO wraps the 'actions' key from actions.yaml.
    """

    actions: ActionsConfigRoot = Field(..., description="Actions configuration")

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
