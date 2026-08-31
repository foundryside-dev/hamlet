"""Integration test for observing item VFS state."""

from pathlib import Path

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


def test_item_durability_roundtrips_through_vfs_registry():
    """Item durability should round-trip through the item VFS registry."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Spawn item and modify durability
    item = env.item_manager.spawn_item("medkit", (3, 4), current_tick=0)
    env.vfs_registry.write_item(
        profile_name=item.vfs_profile,
        var_name="durability",
        value=75.0,
        vfs_index=item.vfs_index,
    )

    durability = env.vfs_registry.read_item(
        profile_name=item.vfs_profile,
        var_name="durability",
        vfs_index=item.vfs_index,
    )

    assert durability == 75.0
