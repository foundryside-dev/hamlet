"""Integration tests for compile-time VFS profiles + effects catalog."""

from pathlib import Path

from townlet.universe.compiler import UniverseCompiler


def test_compiler_wires_vfs_and_effects_together():
    """UniverseCompiler should compile VFS profiles and effects together."""
    # Setup: Use effects_smoke test config (has both VFS global profiles and effects)
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Both artifacts present
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_effect_catalog is not None
    assert compiled.vfs_expression_schema is not None

    # Verify: Effects schema includes VFS global variables
    # effects_smoke has day_count in global profile
    assert "vfs.day_count" in compiled.vfs_expression_schema
    assert compiled.vfs_expression_schema["vfs.day_count"] == "int"

    # Verify: Effects catalog has effects that can reference VFS
    energy_regen = compiled.compiled_effect_catalog.get("energy_regen")
    assert energy_regen is not None
    assert len(energy_regen.on_tick) > 0


def test_compiler_handles_minimal_config_without_vfs():
    """UniverseCompiler should handle configs without VFS profiles."""
    # Setup: Minimal config without vfs_profiles.yaml
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "action_masking"

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_masking", use_cache=False)

    # Verify: No profiles, but compilation succeeds
    assert compiled.compiled_vfs_profiles is None
    # Effects catalog should still compile (no VFS dependencies)
    assert compiled.compiled_effect_catalog is not None


def test_vfs_expression_schema_includes_bars():
    """VFS expression schema should include bar paths for effects."""
    # Setup: Use effects_smoke config
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Schema includes both bars and VFS
    assert "bar.energy" in compiled.vfs_expression_schema
    assert "bar.health" in compiled.vfs_expression_schema
    assert "vfs.day_count" in compiled.vfs_expression_schema

    # Verify: Types are correct
    assert compiled.vfs_expression_schema["bar.energy"] == "float"
    assert compiled.vfs_expression_schema["bar.health"] == "float"
    assert compiled.vfs_expression_schema["vfs.day_count"] == "int"
