"""Held items expire cleanly, and a done world's items are frozen (owner ruling S1; verify_B2c L2, L7).

L2: `ItemManager.inventory` was never assigned (the manager was built before the
inventory), so `despawn_item` never purged: an item that expired while held left its id
in the slot and its metadata, and USE_SLOT on that slot ran the dead item's `on_use`,
which raised in `_entity_position` and killed the whole batch. The manager now owns its
worlds' inventory from construction and purges a despawned item in the same call.

L7: item aging and periodic respawn ran over every world, so a done world's items kept
expiring and respawning while its effects and VTC rules were frozen. Both now take the
live mask.
"""

from __future__ import annotations

from pathlib import Path

import torch

from tests.test_townlet.utils.builders import make_vectorized_env_from_pack
from townlet.determinism import seed_all

ITEMS_SMOKE = Path(__file__).resolve().parents[4] / "configs" / "test" / "items_smoke"
LEVEL = "L0_smoke"


def _env(num_agents: int):
    seed_all(5)
    env = make_vectorized_env_from_pack(ITEMS_SMOKE, level_name=LEVEL, num_agents=num_agents, device=torch.device("cpu"))
    seed_all(5)
    env.reset()
    return env


def _free_cell(env, world: int) -> tuple[int, int]:
    occupied = {tuple(item.position) for item in env.item_manager.items_in_world(world)}
    return next((x, y) for x in range(5) for y in range(5) if (x, y) not in occupied)


def _carry(env, item_type: str, world: int):
    position = _free_cell(env, world)
    item = env.item_manager.spawn_item(world, item_type, position, current_tick=0)
    assert item is not None
    env.positions[world] = torch.tensor(position, dtype=env.positions.dtype)
    assert env.item_handler.handle_get_action(agent_idx=world, agent_position=env.positions[world], current_tick=0, meters=env.meters)
    return item


def _action(env, name: str) -> int:
    return env.action_space.get_action_by_name(name).id


def test_the_manager_owns_the_inventory_the_env_and_handler_use() -> None:
    env = _env(2)
    assert env.item_inventory is env.item_manager.inventory is env.item_handler.inventory


def test_an_item_that_expires_while_held_leaves_its_slot_and_using_the_slot_is_harmless() -> None:
    env = _env(2)
    medkit = _carry(env, "medkit", world=1)
    slot = int((env.item_inventory.slots[1] == medkit.instance_id).nonzero()[0])
    medkit.duration_remaining = 0  # expires at the next item tick

    wait = _action(env, "WAIT")
    env.step(torch.tensor([wait, wait]))
    assert medkit.instance_id not in env.item_manager.live_items
    assert int(env.item_inventory.slots[1, slot]) == -1
    assert medkit.instance_id not in env.item_inventory.items

    # The emptied slot is a no-op to use, not a crash of every world.
    env.step(torch.tensor([wait, _action(env, f"USE_SLOT_{slot}")]))


def test_a_done_worlds_items_neither_age_nor_expire() -> None:
    env = _env(2)
    frozen = _carry(env, "medkit", world=0)
    ticking = _carry(env, "medkit", world=1)
    frozen.duration_remaining = ticking.duration_remaining = 2
    env.dones[0] = True

    wait = _action(env, "WAIT")
    for _ in range(3):
        env.step(torch.tensor([wait, wait]))

    assert frozen.instance_id in env.item_manager.live_items and frozen.duration_remaining == 2
    assert ticking.instance_id not in env.item_manager.live_items


def test_a_done_worlds_respawn_timers_do_not_fire() -> None:
    env = _env(2)
    live = torch.tensor([False, True])
    manager = env.item_manager
    for world in (0, 1):
        for item in list(manager.items_in_world(world)):
            manager.despawn_item(item.instance_id, current_tick=0)
    timers = {world: dict(manager.worlds[world].respawn_timers) for world in (0, 1)}
    assert timers[0] and timers[0] == timers[1]  # the pack's periodic rules armed both worlds alike

    due = max(timers[0].values())
    manager.process_respawns(due, bars=env.bars, live=live)
    assert manager.worlds[0].respawn_timers == timers[0]
    assert list(manager.items_in_world(0)) == []
    assert manager.worlds[1].respawn_timers != timers[1]
