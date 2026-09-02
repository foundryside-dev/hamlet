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

    Bypasses the GET action and adds the freshly-spawned item to the agent's
    inventory directly, then lifts it from the world if exclusive. This
    sidesteps GET's position-arbitration (which picks the oldest item at the
    cell by insertion order) so a co-located initial-spawned item cannot
    shadow the helper's spawn. Side effects of GET that this helper does NOT
    reproduce: `on_pickup` interaction commands, env tick advancement, and
    bar depletion. None of the tests in this file depend on those.

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

    current_tick = env.step_counts[0].item() if env.step_counts.numel() > 0 else 0

    # Spawn item at agent's position
    item = env.item_manager.spawn_item(
        item_type=item_type,
        position=agent_pos,
        current_tick=current_tick,
        initial_state=initial_state,
    )

    if item is None:
        raise RuntimeError(f"Failed to spawn {item_type} at {agent_pos}")

    # Add directly to inventory rather than firing GET. GET picks the first
    # item it finds at the agent's cell by insertion order, so an
    # initial-spawned item from `spawn_initial_items` co-located with the
    # agent would shadow this helper's spawn — silently turning every
    # `initial_state` override into the profile default. Direct insertion
    # guarantees the test sees the item it asked for.
    if not env.item_inventory.add_item(agent_idx, item):
        raise RuntimeError(f"Inventory full; could not add {item_type} for agent {agent_idx}")

    # Exclusive items leave the world on pickup (matches GET semantics).
    if item.exclusive:
        env.item_manager.lift_item(item.instance_id)

    return item.instance_id


def test_spawn_and_pickup_helper_is_robust_to_colocated_items():
    """Regression: spawn_and_pickup_item must pick up its own spawn, not a co-located pre-existing item.

    The items_smoke level spawns 3 apples + 1 medkit at random positions via
    ``spawn_initial_items``. When one of those happens to land on agent 0's
    starting cell, the GET action picks the older item (insertion order),
    so the test's freshly-spawned apple with a custom ``initial_state`` is
    silently shadowed. This caused `test_item_vfs_masking_with_different_profiles`
    to flake (~10-20% of full-suite runs).
    """
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

    # Force the collision: spawn a default apple at agent 0's exact cell BEFORE
    # the helper runs. Without the despawn-co-located fix, the helper's GET
    # would pick this one (freshness=100) rather than the helper's spawn.
    agent_pos = tuple(env.positions[0].tolist())
    preexisting = env.item_manager.spawn_item(item_type="apple", position=agent_pos, current_tick=0)
    assert preexisting is not None, "Pre-existing apple must spawn successfully"
    preexisting_id = preexisting.instance_id

    helper_id = spawn_and_pickup_item(env, 0, "apple", initial_state={"freshness": 42.0})

    held_id = env.item_inventory.slots[0, 0].item()
    assert held_id == helper_id, (
        f"Helper's spawn (instance_id={helper_id}) should be in slot 0; " f"got instance_id={held_id} (pre-existing was {preexisting_id})."
    )

    held_instance = env.item_inventory.items[held_id]
    freshness_idx = env.vfs_registry.item_profile_map["food"]["freshness"]
    held_freshness = env.vfs_registry.item_vfs[held_instance.vfs_index, freshness_idx].item()
    assert held_freshness == 42.0, (
        f"Held apple's freshness should be the helper's custom value 42.0, got {held_freshness}. "
        "This indicates the pre-existing co-located apple was picked up instead."
    )


def test_exposed_item_variable_publishes_through_the_item_arena():
    """Config-in/behaviour-out for the item-arena `variable_element` scope: `durability` is
    declared exposed on the `medical` profile, so a world-resident medkit's row carries its
    normalized value and toggles absent when the item leaves the world.

    Two deviations from the brief's literal test, both measured rather than assumed:

    1. `items_smoke`'s `L0_smoke` level auto-spawns one medkit (and three apples) at reset
       (`levels/L0_smoke/items.yaml`), so the medical-profile `durability` row is already
       present before any test-driven spawn — the brief's "absent until spawn" assumption
       doesn't hold for the committed pack. Asserted instead, by the same principle the
       effects-smoke test above applies: the present-row count increases by exactly one
       after a spawn, and the newly-present row carries the spawned item's own value.
    2. The item-arena `variable_element` scope is fed by the SAME live-item batch as the
       `item` token type (`VectorizedHamletEnv._item_slot_batch`), which is world-resident
       items only (`ItemManager.get_all_items()` — `active_items`, not `held_items`). A
       picked-up EXCLUSIVE item (medkit defaults `exclusive: true`) is lifted out of that
       batch entirely on pickup (`ItemManager.lift_item`), so `spawn_and_pickup_item`'s own
       pickup step makes its medkit disappear from every item-token-shaped observation, not
       just this one — a pre-existing gap in the `item` token type's coverage of held
       inventory, not something this task's item-arena wiring introduces or should paper
       over. Demonstrated below (the row goes from present back to absent) rather than
       worked around, so the gap is visible in-tree, not only in the task report. Filed as
       hamlet-4b931faaf4.
    """
    universe = UniverseCompiler().compile(Path("configs/test/items_smoke"), primary_level="L0_smoke", use_cache=False)
    env = VectorizedHamletEnv(universe=universe, level_name="L0_smoke", num_agents=1, device=torch.device("cpu"))
    env.reset()
    layout = env.token_spec.compact_layout().get_type("variable_element")
    assert layout is not None and layout.capacity > 0
    v0 = layout.dynamic_features.index("value_0")

    def rows():
        obs = env._get_observations()
        return obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(
            layout.capacity, layout.compact_row_width
        )

    def present_count(r: torch.Tensor) -> int:
        return int((r[:, 0] == 1.0).sum().item())

    before = rows()
    baseline = present_count(before)

    # World-resident spawn (no pickup): proves presence toggling, per-instance value, and
    # normalization for the item-arena scope on its own terms.
    agent_pos = tuple(env.positions[0].tolist())
    spawned = env.item_manager.spawn_item(item_type="medkit", position=agent_pos, current_tick=0, initial_state={"durability": 50.0})
    assert spawned is not None
    after_spawn = rows()
    after_spawn_present = after_spawn[:, 0] == 1.0
    assert present_count(after_spawn) == baseline + 1
    newly_present = after_spawn_present & ~(before[:, 0] == 1.0)
    assert newly_present.sum().item() == 1
    assert after_spawn[newly_present][0, v0].item() == pytest.approx(0.5)  # minmax 0..100

    # Documents the held-item gap named above (filed as hamlet-4b931faaf4): lifting the
    # same instance (matching GET's exclusive-pickup semantics) removes it from
    # `ItemManager.get_all_items()`, so its durability row goes back to absent even though
    # the item and its VFS state still exist.
    env.item_manager.lift_item(spawned.instance_id)
    after_lift = rows()
    assert present_count(after_lift) == baseline
