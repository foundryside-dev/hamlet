"""Filesystem, scoping, and YAML syntax preflight checks."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from townlet.universe.errors import CompilationError, CompilationErrorCollector

logger = logging.getLogger(__name__)


def validate_config_dir(config_dir: Path) -> None:
    """Validate config_dir for security and sanity before parsing configs."""
    if not config_dir.exists():
        raise CompilationError(
            stage="Config Directory Validation",
            errors=[f"Config directory does not exist: {config_dir}"],
        )

    if not config_dir.is_dir():
        raise CompilationError(
            stage="Config Directory Validation",
            errors=[f"Config path is not a directory: {config_dir}"],
        )

    path_str = str(config_dir)
    if ".." in path_str:
        logger.warning(
            "Config directory path contains '..' after resolution: %s. This may indicate a path traversal attempt.",
            config_dir,
        )


def validate_scoping(experiment_dir: Path) -> None:
    """Enforce experiment-vs-level scoping for shared catalogs."""
    errors = CompilationErrorCollector(stage="Stage 0: Scoping Validation")

    has_curriculum = (experiment_dir / "curriculum.yaml").exists()
    has_experiment = (experiment_dir / "experiment.yaml").exists()
    has_environment = (experiment_dir / "environment.yaml").exists()

    if has_curriculum and not has_experiment and not has_environment:
        parent_experiment = experiment_dir.parent.parent
        errors.add(
            f"Cannot validate level directory directly. Please validate from the experiment root: {parent_experiment}",
            code="SCOPING_LEVEL_DIRECTORY",
            location=str(experiment_dir),
        )
        errors.check_and_raise()

    required_experiment_files: list[str] = ["vfs_profiles.yaml", "items.yaml"]
    forbidden_level_files = ["vfs_profiles.yaml", "effects.yaml"]

    for filename in required_experiment_files:
        root_path = experiment_dir / filename
        if not root_path.exists():
            errors.add(
                f"Missing required experiment-level file: {filename}",
                code="SCOPING_MISSING_EXPERIMENT_FILE",
                location=str(root_path),
            )

    levels_root = experiment_dir / "levels"
    if levels_root.exists():
        for level_dir in sorted(levels_root.iterdir()):
            if not level_dir.is_dir():
                continue
            for forbidden in forbidden_level_files:
                forbidden_path = level_dir / forbidden
                if forbidden_path.exists():
                    errors.add(
                        f"Found {forbidden} at level scope ({forbidden_path}). This file must live at the experiment root only.",
                        code="SCOPING_FORBIDDEN_LEVEL_FILE",
                        location=str(forbidden_path),
                    )
            level_items = level_dir / "items.yaml"
            if level_items.exists():
                level_version: str | None = None
                try:
                    with level_items.open() as handle:
                        data = yaml.safe_load(handle) or {}
                    if isinstance(data, dict):
                        level_version = data.get("version")
                except yaml.YAMLError:
                    level_version = None

                if level_version != "1.0":
                    errors.add(
                        f"Found items.yaml at level scope ({level_items}). "
                        "Level item spawns must use the v1.0 ItemsAppearance schema; "
                        "shared item catalogs belong at the experiment root.",
                        code="SCOPING_FORBIDDEN_LEVEL_FILE",
                        location=str(level_items),
                    )

    errors.check_and_raise()


def validate_yaml_syntax(config_dir: Path) -> None:
    """Validate all config YAML files can be parsed before compilation begins."""
    errors = CompilationErrorCollector(stage="Phase 0: YAML Syntax Validation")

    shared_files = [
        "experiment.yaml",
        "stratum.yaml",
        "environment.yaml",
        "actions.yaml",
        "brain.yaml",
        "vfs_profiles.yaml",
        "items.yaml",
    ]
    optional_shared_files = [
        "effects.yaml",
        "action_labels.yaml",
        "variables_reference.yaml",
    ]

    for file_name in shared_files:
        file_path = config_dir / file_name
        if not file_path.exists():
            if file_name == "items.yaml":
                continue
            errors.add(f"{file_name}: File not found", code="MISSING_FILE", location=str(file_path))
            continue
        try:
            with file_path.open() as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            errors.add(str(exc), code="YAML_SYNTAX_ERROR", location=str(file_path))

    for file_name in optional_shared_files:
        file_path = config_dir / file_name
        if not file_path.exists():
            continue
        try:
            with file_path.open() as handle:
                yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            errors.add(str(exc), code="YAML_SYNTAX_ERROR", location=str(file_path))

    levels_dir = config_dir / "levels"
    if not levels_dir.exists():
        errors.add("levels/ directory missing", code="MISSING_LEVELS_DIR", location=str(levels_dir))
    else:
        for level_dir in sorted(p for p in levels_dir.iterdir() if p.is_dir()):
            for file_name in ("curriculum.yaml", "bars.yaml", "affordances.yaml", "training.yaml", "drive.yaml"):
                file_path = level_dir / file_name
                if not file_path.exists():
                    errors.add(
                        f"{file_name}: File not found",
                        code="MISSING_FILE",
                        location=str(file_path),
                    )
                    continue
                try:
                    with file_path.open() as handle:
                        yaml.safe_load(handle)
                except yaml.YAMLError as exc:
                    errors.add(str(exc), code="YAML_SYNTAX_ERROR", location=str(file_path))

    if errors.errors:
        errors.add_hint("Check YAML indentation (use spaces, not tabs)")
        errors.add_hint("Ensure lists use proper '- item' syntax")
        errors.add_hint("Validate YAML syntax at yamllint.com or with 'yamllint <file>'")
        errors.check_and_raise()
