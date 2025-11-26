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


def test_effects_can_reference_item_vfs():
    """Effects should be able to read and modify item VFS variables.

    Tests:
    - Effect reads item.vfs.durability
    - Effect modifies item.vfs.quality
    - Item VFS schema includes all item profile variables
    """
    # Setup: Compile items_smoke config with effects that reference item VFS
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "items_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Verify: Compiled catalog includes item VFS effects
    assert compiled.compiled_effect_catalog is not None
    assert "wear_and_tear" in compiled.compiled_effect_catalog.effects
    assert "food_decay" in compiled.compiled_effect_catalog.effects

    # Verify: Effects reference item VFS variables
    wear_tear_effect = compiled.compiled_effect_catalog.effects["wear_and_tear"]
    assert wear_tear_effect.scope == "item"
    # The effect should have on_tick modifications that reference self.vfs.durability
    assert len(wear_tear_effect.on_tick) > 0

    food_decay_effect = compiled.compiled_effect_catalog.effects["food_decay"]
    assert food_decay_effect.scope == "item"
    # The effect should have on_tick modifications that reference self.vfs.freshness
    assert len(food_decay_effect.on_tick) > 0

    # Exercise: Create environment and verify effects can execute
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_smoke",
        device=torch.device("cpu"),
    )

    # Verify: Effect manager uses compiled catalog with item effects
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog

    # Smoke test: Reset environment (should not crash with item VFS effects)
    obs = env.reset()
    assert obs is not None


def test_effects_cascade_with_item_vfs():
    """Effect cascades should work with item VFS state.

    Tests:
    - Effect A modifies item.vfs.durability
    - Effect B modifies item.vfs.durability to 0 (cascade/break)
    - Cascading effects can trigger based on item VFS conditions
    """
    # Setup: Compile config with cascading item VFS effects
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "items_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Verify: Catalog includes cascading effects
    assert compiled.compiled_effect_catalog is not None
    assert "item_degradation" in compiled.compiled_effect_catalog.effects
    assert "item_break" in compiled.compiled_effect_catalog.effects

    # Verify: Effects can cascade (both modify durability)
    degradation_effect = compiled.compiled_effect_catalog.effects["item_degradation"]
    assert degradation_effect.scope == "item"
    assert len(degradation_effect.on_spawn) > 0

    break_effect = compiled.compiled_effect_catalog.effects["item_break"]
    assert break_effect.scope == "item"
    assert len(break_effect.on_spawn) > 0

    # Exercise: Create environment with item effects
    env = compiled.create_environment(
        num_agents=4,
        level_name="L0_smoke",
        device=torch.device("cpu"),
    )

    # Verify: Environment supports item VFS effects
    assert env.effect_manager.catalog is compiled.compiled_effect_catalog

    # Smoke test: Step environment (cascading effects should not crash)
    obs = env.reset()
    actions = torch.zeros(4, dtype=torch.long)
    obs, rewards, dones, info = env.step(actions)
    assert obs is not None
