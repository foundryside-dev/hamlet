"""Tests for VFS standard variable validation in UniverseCompiler.

BUG-37: No compile-time validation ensures required standard VFS variables exist
with correct scopes/types. This test suite verifies that the compiler catches
misconfigured variables_reference.yaml files at compile time.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def test_vfs_validation_missing_position_variable(tmp_path: Path) -> None:
    """Compiler rejects config with missing position variable."""
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "vfs_missing_position"

    compiler = UniverseCompiler()

    with pytest.raises(CompilationError) as excinfo:
        compiler.compile(config_dir, use_cache=False)

    error_msg = str(excinfo.value)
    assert "VFS_MISSING_REQUIRED_VARIABLE" in error_msg or "position" in error_msg.lower()
    assert "variables_reference.yaml" in error_msg


def test_vfs_validation_wrong_position_scope(tmp_path: Path) -> None:
    """Compiler rejects config with position having wrong scope."""
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "vfs_wrong_position_scope"

    compiler = UniverseCompiler()

    with pytest.raises(CompilationError) as excinfo:
        compiler.compile(config_dir, use_cache=False)

    error_msg = str(excinfo.value)
    assert "VFS_VARIABLE_SCOPE_MISMATCH" in error_msg or "scope" in error_msg.lower()
    assert "position" in error_msg.lower()


def test_vfs_validation_accepts_valid_config(tmp_path: Path) -> None:
    """Compiler accepts config with correctly configured VFS variables."""
    # Use a known good config
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()

    # Should not raise
    compiled = compiler.compile(config_dir, use_cache=False)
    assert compiled is not None
