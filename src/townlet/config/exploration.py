"""Exploration configuration loader for v2.1 training.yaml."""

from pathlib import Path

from townlet.config.training_v2_config import ExplorationConfig

__all__ = ["ExplorationConfig", "load_exploration_config"]


def load_exploration_config(config_dir: Path) -> ExplorationConfig:
    """Load exploration config from training.yaml (v2.1)."""
    from pydantic import ValidationError

    from townlet.config.base import format_validation_error, load_yaml_section

    training = load_yaml_section(Path(config_dir), "training.yaml", "training")
    exploration_block = training.get("exploration")
    if exploration_block is None:
        raise ValueError("Missing exploration section under training.yaml:training")
    try:
        return ExplorationConfig(**exploration_block)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc, "exploration section (training.yaml)")) from exc
