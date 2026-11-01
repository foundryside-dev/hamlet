"""Public exploration DTO loading from discovered v2.1 training declarations."""

from pathlib import Path

from townlet.config.training_v2_config import ExplorationConfig

__all__ = ["ExplorationConfig", "load_exploration_config"]


def load_exploration_config(config_dir: Path) -> ExplorationConfig:
    """Load the local target, a direct level or the sole level in a pack.

    A local wrapped training section needs only its exploration DTO fields.
    Packs without a local target must select an unambiguous level.
    """
    from pydantic import ValidationError

    from townlet.config.base import format_validation_error
    from townlet.config.resolved_launch import resolve_config_section

    section = resolve_config_section(Path(config_dir), family="training")
    exploration_block = section.payload.get("exploration")
    if exploration_block is None:
        raise ValueError(f"Missing exploration section under {section.origin}:training")
    try:
        return ExplorationConfig(**exploration_block)
    except ValidationError as exc:
        raise ValueError(format_validation_error(exc, f"exploration section ({section.origin})")) from exc
