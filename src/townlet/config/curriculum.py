"""Curriculum configuration loader (v2.1 curriculum.yaml)."""

from pathlib import Path

from townlet.config.curriculum_config import CurriculumConfig

__all__ = ["CurriculumConfig", "load_curriculum_config"]


def load_curriculum_config(config_dir: Path):
    """Load curriculum.yaml using the v2.1 CurriculumConfig DTO."""
    path = Path(config_dir) / "curriculum.yaml"
    return CurriculumConfig.from_yaml(path)
