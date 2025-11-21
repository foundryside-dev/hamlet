"""Tests for using compiled effect catalog at runtime."""

from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler


def test_env_uses_compiled_effect_catalog():
    """VectorizedHamletEnv should use compiled effect catalog from CompiledUniverse."""
    # Setup: Compile universe with effects
    config_dir = Path(__file__).parent.parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Compiled catalog exists
    assert compiled.compiled_effect_catalog is not None
    assert len(compiled.compiled_effect_catalog.effects) > 0

    # Exercise: Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_effects",
        device=torch.device("cpu"),
    )

    # Verify: Environment uses compiled catalog (not rebuilt from YAML)
    assert env.effect_manager is not None
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog
    # Same object reference = using compiled artifact
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog


def test_env_fails_if_effects_required_but_not_compiled():
    """Environment should fail gracefully if effects required but catalog missing."""
    # Setup: Config with affordances but no effects.yaml (would fail at compile time)
    # This test documents expected behavior: compilation should fail, not runtime

    # Note: If effects.yaml is missing and affordances exist, compiler should fail
    # This is already tested in test_effects_catalog_compilation.py
    pass  # Documented behavior only
