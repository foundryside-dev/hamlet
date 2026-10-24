"""Experiment-level configuration DTO.

This module defines the Pydantic DTO for experiment.yaml files in the v2.1
configuration system. An experiment names the pack and carries its schema version and
human-readable metadata. Curriculum levels are discovered from ``levels/``; the experiment
declaration does not list them.

Example:
    >>> config = ExperimentConfig.from_yaml(Path("configs/default_curriculum/experiment.yaml"))
    >>> print(config.experiment.experiment_name)
    'Default Curriculum'
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ExperimentMetadata(BaseModel):
    """Metadata about the experiment."""

    name: str = Field(..., description="Human-readable experiment name")
    description: str = Field(..., description="Experiment purpose and scope")

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
