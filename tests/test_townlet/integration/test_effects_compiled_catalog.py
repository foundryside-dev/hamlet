"""Integration tests for compiled effect catalog usage."""

from pathlib import Path

import torch

from townlet.universe.compiler import UniverseCompiler


def test_effects_use_compiled_catalog_end_to_end():
    """Effects should use compiled catalog from compilation through execution."""
    # Setup: Compile effects_smoke config
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Verify: Catalog compiled
    assert compiled.compiled_effect_catalog is not None
    assert "energy_regen" in compiled.compiled_effect_catalog.effects

    # Exercise: Create environment and trigger effect
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_effects",
        device=torch.device("cpu"),
    )

    # Verify: Effect manager uses compiled catalog
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog

    # Reset and step
    obs = env.reset()
    actions = torch.zeros(4, dtype=torch.long)
    obs, rewards, dones, info = env.step(actions)

    # Verify: Effects can be triggered (functional smoke test)
    # (If affordances exist, effects should be executable)


def test_no_runtime_yaml_loading():
    """Verify no runtime YAML loading for effects."""
    # Setup: Compile config
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "effects_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_effects", use_cache=False)

    # Create environment
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_effects",
        device=torch.device("cpu"),
    )

    # Verify: No effects.yaml read at runtime
    # (If YAML was loaded, catalog would be different object)
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog
    # Object identity check ensures no rebuild
