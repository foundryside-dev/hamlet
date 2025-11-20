"""Integration test for observing item VFS state."""

from pathlib import Path

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.schema import VariableScope


def test_agent_observes_item_durability():
    """Agent should see item durability in observations."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"), use_cache=False)

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=1,
        device="cpu",
    )

    env.reset()

    # Spawn item and modify durability
    item = env.item_manager.spawn_item("medkit", (3, 4), current_tick=0)
    env.vfs_registry.write(
        "durability",
        75.0,
        context_index=item.vfs_index,
        scope=VariableScope.ITEM,
    )

    # Agent should see item durability in observation
    # (Exact observation index depends on observation_builder layout)
    # For now, verify via VFS registry directly

    durability = env.vfs_registry.read(
        "durability",
        context_index=item.vfs_index,
        scope=VariableScope.ITEM,
    )

    assert durability == 75.0

    # TODO: Once observation builder supports item VFS,
    # verify durability appears in obs tensor at correct index

    # NOTE: Full observation integration (item VFS in obs tensor) requires:
    # 1. ObservationBuilder to handle scope: item in exposed_observations
    # 2. Logic to select which item's properties to include (nearest? held?)
    # 3. Padding for cases where no item is present
    #
    # This is deferred as it requires significant ObservationBuilder changes.
    # Current test validates that item VFS state is stored correctly and
    # can be accessed programmatically.
