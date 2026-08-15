"""Integration test for items modifying their own VFS state."""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def test_item_use_modifies_item_durability():
    """Using an item should decrease its durability via Effects."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)

    # Modify medkit to have on_use that decreases durability
    # (Requires updating items.yaml before test)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Clear any items at target position to avoid collision with random spawns
    target_pos = (2, 2)
    for instance_id, item in list(env.item_manager.active_items.items()):
        if item.position == target_pos:
            env.item_manager.despawn_item(instance_id, current_tick=0)
    # Clear cooldowns that may have been set by despawning
    env.item_manager.cooldown_until.clear()

    # Spawn medkit at known location and pick it up
    medkit_instance = env.item_manager.spawn_item("medkit", position=target_pos, current_tick=0)
    assert medkit_instance is not None

    # Move agent to medkit position
    env.positions[0] = torch.tensor([2, 2], dtype=torch.long)

    # Pick up the medkit (GET action)
    get_action = env.action_space.get_action_by_name("GET")
    obs, reward, done, truncated = env.step(torch.tensor([get_action.id]))

    # Check initial durability
    initial_durability = env.vfs_registry.read_item(
        profile_name=medkit_instance.vfs_profile,
        var_name="durability",
        vfs_index=medkit_instance.vfs_index,
    )
    assert initial_durability == 100.0

    # Use item (USE_SLOT_0 action)
    use_action = env.action_space.get_action_by_name("USE_SLOT_0")
    obs, reward, done, truncated = env.step(torch.tensor([use_action.id]))

    # Durability should decrease
    final_durability = env.vfs_registry.read_item(
        profile_name=medkit_instance.vfs_profile,
        var_name="durability",
        vfs_index=medkit_instance.vfs_index,
    )
    assert final_durability < initial_durability
    assert final_durability == 90.0  # Expect -10 per use
