"""Integration test for items modifying their own VFS state."""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema import VariableScope


def test_item_use_modifies_item_durability():
    """Using an item should decrease its durability via Effects."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    # Modify medkit to have on_use that decreases durability
    # (Requires updating items.yaml before test)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Spawn medkit at known location and pick it up
    medkit_instance = env.item_manager.spawn_item("medkit", position=(2, 2), current_tick=0)
    assert medkit_instance is not None

    # Move agent to medkit position
    env.positions[0] = torch.tensor([2, 2], dtype=torch.long)

    # Pick up the medkit (GET action)
    get_action = env.action_space.get_action_by_name("GET")
    obs, reward, done, truncated = env.step(torch.tensor([get_action.id]))

    # Check initial durability
    initial_durability = env.vfs_registry.read(
        "durability",
        context_index=medkit_instance.vfs_index,
        scope=VariableScope.ITEM,
    )
    assert initial_durability == 100.0

    # Use item (USE_SLOT_0 action)
    use_action = env.action_space.get_action_by_name("USE_SLOT_0")
    obs, reward, done, truncated = env.step(torch.tensor([use_action.id]))

    # Durability should decrease
    final_durability = env.vfs_registry.read(
        "durability",
        context_index=medkit_instance.vfs_index,
        scope=VariableScope.ITEM,
    )
    assert final_durability < initial_durability
    assert final_durability == 90.0  # Expect -10 per use
