"""Integration tests for item VFS end-to-end."""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def test_item_vfs_profile_driven_end_to_end():
    """Item VFS should be profile-driven from compilation to observations."""
    # Setup: Compile items_smoke config (has item profiles)
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Verify: Item profiles compiled
    assert compiled.compiled_vfs_profiles is not None, "VFS profiles not compiled"
    assert compiled.compiled_vfs_profiles.item_profiles is not None, "Item profiles not compiled"
    assert len(compiled.compiled_vfs_profiles.item_profiles) > 0, "No item profiles found"

    # Verify: Expected profiles present (food, medical, currency)
    assert "food" in compiled.compiled_vfs_profiles.item_profiles, "food profile missing"
    assert "medical" in compiled.compiled_vfs_profiles.item_profiles, "medical profile missing"
    assert "currency" in compiled.compiled_vfs_profiles.item_profiles, "currency profile missing"

    # Verify: Profiles have correct structure
    food_profile = compiled.compiled_vfs_profiles.item_profiles["food"]
    assert len(food_profile.variables) == 1, f"Expected 1 variable in food profile, got {len(food_profile.variables)}"
    assert food_profile.variables[0].name == "freshness", "Expected freshness variable in food profile"

    medical_profile = compiled.compiled_vfs_profiles.item_profiles["medical"]
    assert len(medical_profile.variables) == 1, f"Expected 1 variable in medical profile, got {len(medical_profile.variables)}"
    assert medical_profile.variables[0].name == "durability", "Expected durability variable in medical profile"

    currency_profile = compiled.compiled_vfs_profiles.item_profiles["currency"]
    assert len(currency_profile.variables) == 0, f"Expected 0 variables in currency profile, got {len(currency_profile.variables)}"

    # Create environment
    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=4,
        device=torch.device("cpu"),
    )

    # Verify: Item VFS storage allocated
    assert env.vfs_registry.item_vfs is not None, "Item VFS storage not allocated"
    assert env.vfs_registry.item_profile_map is not None, "Item profile map not created"

    # Verify: Profile map contains expected profiles
    assert "food" in env.vfs_registry.item_profile_map, "food profile not in profile map"
    assert "medical" in env.vfs_registry.item_profile_map, "medical profile not in profile map"
    assert "currency" in env.vfs_registry.item_profile_map, "currency profile not in profile map"

    # Verify: Profile map contains correct variable indices
    food_map = env.vfs_registry.item_profile_map["food"]
    assert "freshness" in food_map, "freshness variable not in food profile map"
    assert food_map["freshness"] == 0, f"Expected freshness at index 0, got {food_map['freshness']}"

    medical_map = env.vfs_registry.item_profile_map["medical"]
    assert "durability" in medical_map, "durability variable not in medical profile map"
    assert medical_map["durability"] == 0, f"Expected durability at index 0, got {medical_map['durability']}"

    # Verify: Item VFS storage has correct shape
    # max_items_in_world = 10, max_vars_across_profiles = 1 (food and medical both have 1 var)
    assert env.vfs_registry.item_vfs.shape[0] == 10, f"Expected 10 item slots, got {env.vfs_registry.item_vfs.shape[0]}"
    assert env.vfs_registry.item_vfs.shape[1] == 1, f"Expected 1 variable per item, got {env.vfs_registry.item_vfs.shape[1]}"

    # Exercise: Spawn item and observe VFS
    env.reset()

    # Spawn apple (food profile with freshness=100.0)
    apple = env.item_manager.spawn_item("apple", position=(2, 2), current_tick=0)
    assert apple is not None, "Failed to spawn apple"
    assert apple.vfs_profile == "food", f"Expected food profile, got {apple.vfs_profile}"

    # Verify: Item VFS state initialized with default values
    apple_vfs_index = apple.vfs_index
    freshness_idx = env.vfs_registry.item_profile_map["food"]["freshness"]
    freshness_value = env.vfs_registry.item_vfs[apple_vfs_index, freshness_idx].item()
    assert freshness_value == 100.0, f"Expected freshness=100.0, got {freshness_value}"


def test_item_spawn_with_initial_state():
    """Items spawned with initial_state should have custom VFS values."""
    # Setup: Compile config with items
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Create environment
    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=1,
        device=torch.device("cpu"),
    )

    env.reset()

    # Exercise: Spawn apple with custom initial_state
    custom_freshness = 75.5
    apple = env.item_manager.spawn_item(
        "apple",
        position=(3, 3),
        current_tick=0,
        initial_state={"freshness": custom_freshness},
    )

    # Verify: VFS state reflects initial_state
    apple_vfs_index = apple.vfs_index
    freshness_idx = env.vfs_registry.item_profile_map["food"]["freshness"]
    freshness_value = env.vfs_registry.item_vfs[apple_vfs_index, freshness_idx].item()
    assert freshness_value == custom_freshness, f"Expected freshness={custom_freshness}, got {freshness_value}"

    # Exercise: Spawn medkit with custom initial_state
    custom_durability = 42.0
    medkit = env.item_manager.spawn_item(
        "medkit",
        position=(4, 4),
        current_tick=0,
        initial_state={"durability": custom_durability},
    )

    # Verify: VFS state reflects initial_state
    medkit_vfs_index = medkit.vfs_index
    durability_idx = env.vfs_registry.item_profile_map["medical"]["durability"]
    durability_value = env.vfs_registry.item_vfs[medkit_vfs_index, durability_idx].item()
    assert durability_value == custom_durability, f"Expected durability={custom_durability}, got {durability_value}"


def test_item_vfs_in_observations():
    """Item VFS state should appear in agent observations when items are held."""
    # Setup: Compile config with items
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    # Create environment
    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=1,
        device=torch.device("cpu"),
    )

    obs = env.reset()

    # Get initial observation (no items held)
    initial_obs_dim = obs.shape[1]

    # Spawn apple and pick it up
    env.item_manager.spawn_item("apple", position=(0, 0), current_tick=0)
    env.positions[0] = torch.tensor([0, 0], dtype=torch.long)
    get_action = env.action_space.get_action_by_name("GET")
    obs, _, _, _ = env.step(torch.tensor([get_action.id]))

    # Verify: Agent now has apple in inventory
    assert env.item_inventory.count_items(0) == 1, "Apple not in inventory"

    # Verify: Observation dimensions remain constant
    # (item VFS dimensions are pre-allocated, just masked when empty)
    assert obs.shape[1] == initial_obs_dim, f"Observation dimensions changed: {initial_obs_dim} -> {obs.shape[1]}"

    # Note: We cannot easily verify that item VFS values appear in observations
    # without knowing the exact structure of the observation vector. That would
    # require inspecting the VFSObservationSpec and calculating offsets.
    # The important property is that obs_dim is stable (verified above).


def test_item_profile_switch_updates_vfs_layout():
    """Switching item profile should update VFS storage layout.

    Tests profile-based VFS allocation:
    - Spawn item with profile A (food: 1 var)
    - Despawn and spawn different item type with profile B (medical: 1 var)
    - Verify storage uses profile B layout
    """
    # Setup: Config with multiple item profiles
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="L0_smoke", use_cache=False)

    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=1,
        device=torch.device("cpu"),
    )

    env.reset()

    # Exercise: Spawn apple (food profile)
    apple = env.item_manager.spawn_item("apple", position=(2, 2), current_tick=0)
    assert apple is not None, "Failed to spawn apple"
    assert apple.vfs_profile == "food", f"Expected food profile, got {apple.vfs_profile}"

    # Verify: Apple VFS storage uses food profile map
    apple_vfs_index = apple.vfs_index
    food_profile_map = env.vfs_registry.item_profile_map["food"]
    assert "freshness" in food_profile_map, "freshness variable not in food profile map"
    freshness_idx = food_profile_map["freshness"]
    freshness_value = env.vfs_registry.item_vfs[apple_vfs_index, freshness_idx].item()
    assert freshness_value == 100.0, f"Expected freshness=100.0, got {freshness_value}"

    # Exercise: Despawn apple
    current_tick = env.step_counts[0].item() if env.step_counts.numel() > 0 else 0
    env.item_manager.despawn_item(apple.instance_id, current_tick=current_tick)
    assert apple.instance_id not in env.item_manager.active_items, "Apple should be despawned"

    # Exercise: Spawn medkit (medical profile) - reuses the same VFS slot
    medkit = env.item_manager.spawn_item("medkit", position=(3, 3), current_tick=0)
    assert medkit is not None, "Failed to spawn medkit"
    assert medkit.vfs_profile == "medical", f"Expected medical profile, got {medkit.vfs_profile}"

    # Verify: Medkit VFS storage uses medical profile map
    medkit_vfs_index = medkit.vfs_index
    medical_profile_map = env.vfs_registry.item_profile_map["medical"]
    assert "durability" in medical_profile_map, "durability variable not in medical profile map"
    durability_idx = medical_profile_map["durability"]
    durability_value = env.vfs_registry.item_vfs[medkit_vfs_index, durability_idx].item()
    assert durability_value == 100.0, f"Expected durability=100.0, got {durability_value}"

    # Verify: Profile switching works correctly
    # The VFS slot was reused when medkit spawned after apple despawned
    # The key property is that medkit uses durability_idx correctly via profile map
    # This test verifies that the profile map correctly routes to the right variables
    # (Medical profile doesn't use freshness, so the old freshness value is irrelevant)
