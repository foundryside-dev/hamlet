"""Experiment-level configuration DTO.

This module defines the Pydantic DTO for experiment.yaml files in the v2.1
configuration system. An experiment defines metadata and the list of curriculum
levels to train through.

Example:
    >>> config = ExperimentConfig.from_yaml(Path("configs/default_curriculum/experiment.yaml"))
    >>> print(config.experiment.experiment_name)
    'Default Curriculum'
    >>> print(config.experiment.curriculum_levels)
    ['L0_0_minimal', 'L0_5_dual_resource', ...]
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ExperimentMetadata(BaseModel):
    """Metadata about the experiment."""

    name: str = Field(..., description="Human-readable experiment name")
    description: str = Field(..., description="Experiment purpose and scope")
    author: str = Field(..., description="Creator of this experiment")
    created: str = Field(..., description="Creation date (YYYY-MM-DD)")
    tags: list[str] = Field(..., description="Classification tags")

    model_config = ConfigDict(extra="forbid")


class ExperimentConfigRoot(BaseModel):
    """Root structure for experiment.yaml file."""

    version: str = Field(..., description="Config schema version")
    experiment_name: str = Field(
        ...,
        description=(
            "Canonical experiment name used for runtime batch labeling and telemetry. " "Must be explicitly set in experiment.yaml."
        ),
    )
    metadata: ExperimentMetadata = Field(..., description="Experiment metadata")
    curriculum_levels: list[str] = Field(..., description="Ordered list of curriculum level names")

    model_config = ConfigDict(extra="forbid")


class ExperimentConfig(BaseModel):
    """Top-level experiment configuration.

    This DTO wraps the 'experiment' key from experiment.yaml.
    """

    experiment: ExperimentConfigRoot = Field(..., description="Experiment configuration")

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def from_yaml(cls, path: Path) -> "ExperimentConfig":
        """Load experiment configuration from YAML file.

        Args:
            path: Path to experiment.yaml file

        Returns:
            ExperimentConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
