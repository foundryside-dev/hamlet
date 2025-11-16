"""Curriculum-level configuration DTO.

This module defines the Pydantic DTO for curriculum.yaml files in the v2.1
configuration system. A curriculum config defines vision mode, temporal settings,
and level-specific overrides.

Example:
    >>> config = CurriculumConfig.from_yaml(
    ...     Path("configs/default_curriculum/levels/L1_full_observability/curriculum.yaml")
    ... )
    >>> print(config.active_vision)
    'global'
    >>> print(config.active_temporal)
    False
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class CurriculumConfigRoot(BaseModel):
    """Root structure for curriculum.yaml file."""

    version: str = Field(..., description="Config schema version")
    active_vision: Literal["global", "partial"] = Field(..., description="Vision mode (global=full observability, partial=POMDP)")
    vision_range: float = Field(..., description="Vision range (0.0-1.0 for local, ignored for global)", ge=0.0, le=1.0)
    active_temporal: bool = Field(..., description="Whether temporal mechanics are active")
    day_length: int | None = Field(None, description="Day length in ticks (required if active_temporal=true)")

    class Config:
        extra = "forbid"

    @model_validator(mode="after")
    def validate_day_length(self):
        """Validate day_length based on active_temporal.

        Rules:
        - If active_temporal=true, day_length must be a positive integer
        - If active_temporal=false, day_length must be null
        """
        if self.active_temporal:
            if self.day_length is None:
                raise ValueError("day_length is required when active_temporal=true")
            if not isinstance(self.day_length, int) or self.day_length <= 0:
                raise ValueError(f"day_length must be a positive integer, got {self.day_length}")
        else:
            if self.day_length is not None:
                raise ValueError("day_length must be null when active_temporal=false")

        return self


class CurriculumConfig(BaseModel):
    """Top-level curriculum configuration.

    This DTO wraps the 'curriculum' key from curriculum.yaml.
    """

    curriculum: CurriculumConfigRoot = Field(..., description="Curriculum configuration")

    class Config:
        extra = "forbid"

    @classmethod
    def from_yaml(cls, path: Path) -> "CurriculumConfig":
        """Load curriculum configuration from YAML file.

        Args:
            path: Path to curriculum.yaml file

        Returns:
            CurriculumConfig instance

        Raises:
            ValidationError: If YAML structure doesn't match schema
            FileNotFoundError: If path doesn't exist
        """
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
