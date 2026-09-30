"""Pack-directory preflight; declarations own content and scope validation."""

from __future__ import annotations

import logging
from pathlib import Path

from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError, CompilationMessage
from townlet.universe.stages import CompilationStage

logger = logging.getLogger(__name__)


def validate_config_dir(config_dir: Path) -> None:
    """Validate config_dir for security and sanity before parsing configs."""
    if not config_dir.exists():
        raise CompilationError(
            stage=CompilationStage.PREFLIGHT.label,
            errors=[
                CompilationMessage(
                    code=ErrorCode.CONFIG_PATH_INVALID, message="Config directory does not exist", location=f"{config_dir}:1"
                )
            ],
        )

    if not config_dir.is_dir():
        raise CompilationError(
            stage=CompilationStage.PREFLIGHT.label,
            errors=[
                CompilationMessage(code=ErrorCode.CONFIG_PATH_INVALID, message="Config path is not a directory", location=f"{config_dir}:1")
            ],
        )

    path_str = str(config_dir)
    if ".." in path_str:
        logger.warning(
            "Config directory path contains '..' after resolution: %s. This may indicate a path traversal attempt.",
            config_dir,
        )
