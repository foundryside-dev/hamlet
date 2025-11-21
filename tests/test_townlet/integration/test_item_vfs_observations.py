"""Integration tests for item VFS in agent observations."""

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

# NOTE: These tests are designed to fail loudly until Task 3 of the Runtime VFS+Effects
# Integration Plan is complete (see docs/plans/vfs_uplift/2025-11-23-runtime-vfs-effects-integration.md).
# Task 3 will implement profile-driven item VFS observations.
# The tests verify test isolation and registry cleanup even when skipped.


def spawn_and_pickup_item(
    env: VectorizedHamletEnv,
    agent_idx: int,
    item_type: str,
    initial_state: dict[str, float] | None = None,
) -> int:
    """Helper to spawn item and assign to agent inventory.

    Args:
        env: Environment instance
        agent_idx: Which agent should pick up the item
        item_type: Type of item to spawn (e.g., "apple", "medkit")
        initial_state: Optional custom VFS state for the item

    Returns:
        instance_id: The item instance ID
    """
    # Get agent's current position
    agent_pos = tuple(env.positions[agent_idx].tolist())

    # Spawn item at agent's position
    item = env.item_manager.spawn_item(
        item_type=item_type,
        position=agent_pos,
        current_tick=env.step_counts[0].item() if env.step_counts.numel() > 0 else 0,
        initial_state=initial_state,
    )

    if item is None:
        raise RuntimeError(f"Failed to spawn {item_type} at {agent_pos}")

    # Execute GET action to pick up item
    get_action = env.action_space.get_action_by_name("GET")
    actions = torch.full((env.num_agents,), get_action.id, dtype=torch.long)
    env.step(actions)

    return item.instance_id


@pytest.mark.xfail(
    reason="Item VFS observations not yet implemented (Task 3 of Runtime VFS+Effects Integration Plan)",
    strict=True,
)
def test_item_vfs_observations_include_held_items():
    """Agent observations should include VFS state of held items.

    This test verifies that:
    1. Test isolation is correct (VFS registry clean at start)
    2. Item VFS field exists in observations
    3. Item VFS values are correctly exposed in observations
    4. Masking works for empty slots and zero-variable profiles
    """
    # Setup: Compile items_smoke config
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=4,
        device=torch.device("cpu"),
    )

    # Verify test isolation: VFS registry should be clean
    if env.vfs_registry is not None and env.vfs_registry.item_vfs is not None:
        assert torch.all(
            env.vfs_registry.item_vfs == 0.0
        ), f"VFS registry not clean at test start! Non-zero values found: {env.vfs_registry.item_vfs[env.vfs_registry.item_vfs != 0.0]}"

    # Reset to initialize state
    obs = env.reset()
    initial_obs_dim = obs.shape[1]

    # Calculate expected item VFS dimensions
    # Item VFS dim = max_items_per_agent × max_vars_per_profile
    # For items_smoke: 3 slots × 1 var (food=freshness, medical=durability, currency=none)
    max_items_per_agent = compiled.items_catalog.max_items_per_agent
    max_vars_per_profile = max(len(p.variables) for p in compiled.compiled_vfs_profiles.item_profiles.values())
    item_vfs_dim = max_items_per_agent * max_vars_per_profile
    assert item_vfs_dim == 3, f"Expected 3 item VFS dims (3 slots × 1 var), got {item_vfs_dim}"

    # Exercise: Setup different item holdings
    # Agent 0: holds 2 items (slots 0, 1 filled)
    spawn_and_pickup_item(env, 0, "apple")  # freshness=100.0
    spawn_and_pickup_item(env, 0, "medkit")  # durability=100.0

    # Agent 1: holds 1 item (slot 0 filled, slots 1-2 empty)
    spawn_and_pickup_item(env, 1, "apple")

    # Agent 2: holds 0 items (all slots empty)
    # (no pickup)

    # Agent 3: holds coin (profile with 0 variables)
    spawn_and_pickup_item(env, 3, "coin")

    # Get observations after pickups
    obs = env._get_observations()

    # Verify: Observations include item VFS with proper dimensions
    assert obs.shape[1] == initial_obs_dim, f"Observation dimensions changed: {initial_obs_dim} -> {obs.shape[1]}"

    # Calculate item VFS slice indices from observation spec
    # Find the item VFS field by iterating through observation fields
    item_vfs_field = None
    for field in env.observation_spec.fields:
        if "item" in field.name.lower() and "vfs" in field.name.lower():
            item_vfs_field = field
            break

    assert (
        item_vfs_field is not None
    ), f"Item VFS field not found in observations! Available fields: {[f.name for f in env.observation_spec.fields]}"

    # Extract item VFS slice from observations
    start_idx = item_vfs_field.start_index
    end_idx = item_vfs_field.end_index
    item_vfs_obs = obs[:, start_idx:end_idx]

    # Verify shape: [batch, item_vfs_dim]
    assert item_vfs_obs.shape == (4, item_vfs_dim), f"Expected (4, {item_vfs_dim}), got {item_vfs_obs.shape}"

    # Agent 0: Should have non-zero values in slots 0 and 1
    agent0_item_vfs = item_vfs_obs[0]
    assert agent0_item_vfs[0] > 0.0, "Agent 0 slot 0 should be non-zero (apple freshness)"
    assert agent0_item_vfs[1] > 0.0, "Agent 0 slot 1 should be non-zero (medkit durability)"
    assert agent0_item_vfs[2] == 0.0, "Agent 0 slot 2 should be masked (empty)"

    # Agent 1: Should have non-zero value in slot 0 only
    agent1_item_vfs = item_vfs_obs[1]
    assert agent1_item_vfs[0] > 0.0, "Agent 1 slot 0 should be non-zero (apple freshness)"
    assert agent1_item_vfs[1] == 0.0, "Agent 1 slot 1 should be masked (empty)"
    assert agent1_item_vfs[2] == 0.0, "Agent 1 slot 2 should be masked (empty)"

    # Agent 2: All slots should be masked (no items)
    agent2_item_vfs = item_vfs_obs[2]
    assert torch.all(agent2_item_vfs == 0.0), "Agent 2 all slots should be masked (no items held)"

    # Agent 3: Coin has 0 variables, so slot 0 should be 0.0 (masked profile, not empty slot)
    agent3_item_vfs = item_vfs_obs[3]
    # Note: Currency profile has 0 variables, so it still gets masked in the obs
    assert agent3_item_vfs[0] == 0.0, "Agent 3 slot 0 should be 0.0 (coin has no VFS vars)"


@pytest.mark.xfail(
    reason="Item VFS observations not yet implemented (Task 3 of Runtime VFS+Effects Integration Plan)",
    strict=True,
)
def test_item_vfs_masking_with_different_profiles():
    """Items with different VFS profiles should mask correctly.

    This test verifies that:
    1. Test isolation is correct (VFS registry clean at start)
    2. initial_state parameter works correctly
    3. Different profiles with different variable counts mask correctly
    4. VFS values persist correctly in the registry
    """
    # Setup: items_smoke has 3 profiles:
    # - food: 1 var (freshness)
    # - medical: 1 var (durability)
    # - currency: 0 vars
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=1,
        device=torch.device("cpu"),
    )

    # Verify test isolation: VFS registry should be clean
    if env.vfs_registry is not None and env.vfs_registry.item_vfs is not None:
        assert torch.all(
            env.vfs_registry.item_vfs == 0.0
        ), f"VFS registry not clean at test start! Non-zero values found: {env.vfs_registry.item_vfs[env.vfs_registry.item_vfs != 0.0]}"

    env.reset()

    # Exercise: Agent holds items from different profiles
    # Slot 0: apple (food profile, 1 var)
    spawn_and_pickup_item(env, 0, "apple", initial_state={"freshness": 75.0})

    # Slot 1: medkit (medical profile, 1 var)
    spawn_and_pickup_item(env, 0, "medkit", initial_state={"durability": 50.0})

    # Slot 2: coin (currency profile, 0 vars)
    spawn_and_pickup_item(env, 0, "coin")

    # Verify: VFS registry has correct values
    # Find item instance IDs in inventory
    apple_slot = env.item_inventory.slots[0, 0].item()
    medkit_slot = env.item_inventory.slots[0, 1].item()
    coin_slot = env.item_inventory.slots[0, 2].item()

    assert apple_slot != -1, "Apple should be in slot 0"
    assert medkit_slot != -1, "Medkit should be in slot 1"
    assert coin_slot != -1, "Coin should be in slot 2"

    # Verify VFS values in registry with detailed diagnostics
    food_profile_map = env.vfs_registry.item_profile_map["food"]
    freshness_idx = food_profile_map["freshness"]
    apple_freshness = env.vfs_registry.item_vfs[apple_slot, freshness_idx].item()

    # DEBUG: Print full VFS state for diagnosis
    if apple_freshness != 75.0:
        print("\n=== VFS State Dump (Apple) ===")
        print(f"Apple slot: {apple_slot}")
        print(f"Freshness index: {freshness_idx}")
        print(f"Full item_vfs tensor:\n{env.vfs_registry.item_vfs}")
        print(f"Apple VFS row: {env.vfs_registry.item_vfs[apple_slot]}")
        print("===========================\n")

    assert apple_freshness == 75.0, (
        f"Expected freshness=75.0, got {apple_freshness}. "
        f"Apple slot={apple_slot}, freshness_idx={freshness_idx}, "
        f"VFS row={env.vfs_registry.item_vfs[apple_slot]}"
    )

    medical_profile_map = env.vfs_registry.item_profile_map["medical"]
    durability_idx = medical_profile_map["durability"]
    medkit_durability = env.vfs_registry.item_vfs[medkit_slot, durability_idx].item()
    assert medkit_durability == 50.0, (
        f"Expected durability=50.0, got {medkit_durability}. "
        f"Medkit slot={medkit_slot}, durability_idx={durability_idx}, "
        f"VFS row={env.vfs_registry.item_vfs[medkit_slot]}"
    )

    # Currency profile has 0 variables, so no VFS state to check

    # Get observations and verify masking
    obs = env._get_observations()

    # Try to find item VFS field in observations
    item_vfs_field = None
    for field in env.observation_spec.fields:
        if "item" in field.name.lower() and "vfs" in field.name.lower():
            item_vfs_field = field
            break

    assert (
        item_vfs_field is not None
    ), f"Item VFS field not found in observations! Available fields: {[f.name for f in env.observation_spec.fields]}"

    # Extract item VFS slice
    start_idx = item_vfs_field.start_index
    end_idx = item_vfs_field.end_index
    item_vfs_obs = obs[0, start_idx:end_idx]

    # Verify: Each slot has correct VFS values
    # max_vars_across_profiles = 1 (food and medical both have 1 var)
    # So each slot contributes 1 dimension
    assert item_vfs_obs[0] == 75.0, (
        f"Slot 0 should have freshness=75.0, got {item_vfs_obs[0]}. "
        f"Full obs slice: {item_vfs_obs}, registry values: {env.vfs_registry.item_vfs[apple_slot]}"
    )
    assert item_vfs_obs[1] == 50.0, (
        f"Slot 1 should have durability=50.0, got {item_vfs_obs[1]}. "
        f"Full obs slice: {item_vfs_obs}, registry values: {env.vfs_registry.item_vfs[medkit_slot]}"
    )
    assert item_vfs_obs[2] == 0.0, f"Slot 2 should be 0.0 (coin has no vars), got {item_vfs_obs[2]}. Full obs slice: {item_vfs_obs}"


@pytest.mark.xfail(
    reason="Item VFS observations not yet implemented (Task 3 of Runtime VFS+Effects Integration Plan)",
    strict=True,
)
def test_item_vfs_updates_in_observations():
    """Item VFS state changes should appear in observations.

    This test verifies that:
    1. Test isolation is correct (VFS registry clean at start)
    2. VFS state changes are reflected in subsequent observations
    3. Manual registry updates propagate to observations correctly
    """
    # Setup: Compile config with items
    config_dir = Path("configs/test/items_smoke")

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, use_cache=False)

    env = VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_smoke",
        num_agents=1,
        device=torch.device("cpu"),
    )

    # Verify test isolation: VFS registry should be clean
    if env.vfs_registry is not None and env.vfs_registry.item_vfs is not None:
        assert torch.all(
            env.vfs_registry.item_vfs == 0.0
        ), f"VFS registry not clean at test start! Non-zero values found: {env.vfs_registry.item_vfs[env.vfs_registry.item_vfs != 0.0]}"

    env.reset()

    # Exercise: Agent holds medkit with durability=100
    spawn_and_pickup_item(env, 0, "medkit", initial_state={"durability": 100.0})

    # Get initial observation
    obs_before = env._get_observations()

    # Verify medkit is in inventory
    assert env.item_inventory.count_items(0) == 1, "Medkit should be in inventory"

    # Find medkit instance ID
    medkit_slot = env.item_inventory.slots[0, 0].item()
    assert medkit_slot != -1, "Medkit should be in slot 0"

    # Manually modify medkit durability via VFS registry (simulates effect execution)
    medical_profile_map = env.vfs_registry.item_profile_map["medical"]
    durability_idx = medical_profile_map["durability"]
    env.vfs_registry.item_vfs[medkit_slot, durability_idx] = 50.0

    # Get observation after VFS update
    obs_after = env._get_observations()

    # Try to find item VFS field in observations
    item_vfs_field = None
    for field in env.observation_spec.fields:
        if "item" in field.name.lower() and "vfs" in field.name.lower():
            item_vfs_field = field
            break

    assert (
        item_vfs_field is not None
    ), f"Item VFS field not found in observations! Available fields: {[f.name for f in env.observation_spec.fields]}"

    # Extract item VFS slice from both observations
    start_idx = item_vfs_field.start_index
    end_idx = item_vfs_field.end_index

    item_vfs_before = obs_before[0, start_idx:end_idx]
    item_vfs_after = obs_after[0, start_idx:end_idx]

    # Verify: Observation reflects updated VFS state
    # Slot 0 should show durability change from 100.0 -> 50.0
    assert (
        item_vfs_before[0] == 100.0
    ), f"Initial durability should be 100.0, got {item_vfs_before[0]}. Medkit slot={medkit_slot}, full obs before: {item_vfs_before}"
    assert item_vfs_after[0] == 50.0, (
        f"Updated durability should be 50.0, got {item_vfs_after[0]}. "
        f"Medkit slot={medkit_slot}, full obs after: {item_vfs_after}, "
        f"registry value: {env.vfs_registry.item_vfs[medkit_slot, durability_idx]}"
    )
