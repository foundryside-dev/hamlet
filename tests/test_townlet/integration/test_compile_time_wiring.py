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

    # Verify: Effects catalog has effects that can reference VFS
    energy_regen = compiled.compiled_effect_catalog.get("energy_regen")
    assert energy_regen is not None
    assert len(energy_regen.on_tick) > 0


def test_compiler_handles_explicit_empty_variable_catalog():
    """UniverseCompiler should handle an explicit empty variable catalog."""
    # Setup: Minimal config with no variable declarations
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "action_masking"

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_masking", use_cache=False)

    # Verify: Minimal profiles compile (no globals/agent vars)
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is None
    assert compiled.compiled_vfs_profiles.agent_profile is None
    # Effects catalog should still compile (no VFS dependencies required)
    assert compiled.compiled_effect_catalog is not None


def test_command_namespace_includes_bars_and_globals():
    """The environment's command namespace reads meters as bar.<m> and globals by bare id (VFS round-2 S5)."""
    from townlet.vfs.namespace import EFFECT_PIPELINE

    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"
    compiled = UniverseCompiler().compile(config_dir, primary_level="L0_effects", use_cache=False)
    env = compiled.create_environment(num_agents=1, level_name="L0_effects", device="cpu")
    schema = env.command_symbols.namespace.schema(EFFECT_PIPELINE)
    assert schema["bar.energy"] == "float"
    assert schema["bar.health"] == "float"
    assert schema["day_count"] == "float"
