"""Public curriculum DTO loading from discovered v2.1 declarations."""

from pathlib import Path

from townlet.config.curriculum_config import CurriculumConfig

__all__ = ["CurriculumConfig", "load_curriculum_config"]


def load_curriculum_config(config_dir: Path):
    """Load a local/direct/sole-level curriculum with authored clocks resolved.

    Numeric standalone curriculum needs no variables declaration. A period_of
    reference requires its actual pack clock; multiple pack levels are ambiguous
    unless the input names a direct level or contains a local curriculum target.
    """
    from townlet.config.resolved_launch import resolve_config_section

    section = resolve_config_section(Path(config_dir), family="curriculum")
    return CurriculumConfig.model_validate({"curriculum": dict(section.payload)})
