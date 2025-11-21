"""Edge case tests for VFS expression evaluation."""

from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.profiles import CircularDependencyError
from townlet.world.expression.type_checker import TypeCheckError


def test_circular_dependency_detected_at_compile_time():
    """Circular VFS dependencies should fail at compile time, not runtime."""
    # Setup: Create config with circular dependency
    # a = b + 1
    # b = a + 1
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_circular_dependency"

    # Exercise & Verify: Compilation should fail with clear error
    with pytest.raises(CircularDependencyError, match="[Cc]ircular"):
        compiler = UniverseCompiler()
        compiler.compile(config_dir, primary_level="L0_circular", use_cache=False)


def test_missing_vfs_variable_reference():
    """VFS expression referencing undefined variable should fail at compile time."""
    # Setup: Config with VFS var referencing nonexistent var
    # my_var = undefined_var + 1
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_undefined_var"

    # Exercise & Verify: Compilation should fail
    with pytest.raises(TypeCheckError, match="not found"):
        compiler = UniverseCompiler()
        compiler.compile(config_dir, primary_level="L0_undefined", use_cache=False)


def test_type_mismatch_in_vfs_expression():
    """VFS expression with type mismatch should fail at compile time."""
    # Setup: Config with int var assigned bool expression
    # my_int_var = 10 < 5  # Returns bool, not int
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "vfs_type_mismatch"

    # Exercise & Verify: Compilation should fail with type error
    with pytest.raises(TypeCheckError, match="declared as int but expression returns bool"):
        compiler = UniverseCompiler()
        compiler.compile(config_dir, primary_level="L0_type_mismatch", use_cache=False)
