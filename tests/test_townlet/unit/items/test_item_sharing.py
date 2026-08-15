import torch

from townlet.config.items_config import ItemInteractionsConfig, ItemsCatalogConfig, ItemTypeConfig
from townlet.effects.executor import CommandExecutor
from townlet.items.action_handlers import ItemActionHandler
from townlet.items.inventory import InventoryState
from townlet.items.manager import ItemManager


def _make_catalog(*, exclusive: bool) -> ItemsCatalogConfig:
    interactions = ItemInteractionsConfig(
        on_pickup=[],
        on_use=[],
        on_drop=[],
        local_commands=[],
        inventory_commands=[],
    )
    item_type = ItemTypeConfig(
        name="Test Item",
        icon="*",
        tags=["test"],
        id="test_item",
        vfs_profile="test_profile",
        interactions=interactions,
        exclusive=exclusive,
    )
    return ItemsCatalogConfig(
        version="1.0",
        item_types=[item_type],
        max_items_per_agent=2,
        max_items_in_world=5,
    )


def _make_handler(*, exclusive: bool) -> tuple[ItemManager, InventoryState, ItemActionHandler]:
    catalog = _make_catalog(exclusive=exclusive)
    manager = ItemManager(catalog=catalog, max_items=5, device="cpu", schema=None, vfs_registry=None)
    inventory = InventoryState(batch_size=2, max_items_per_agent=2, device="cpu")
    handler = ItemActionHandler(
        manager=manager,
        inventory=inventory,
        command_executor=CommandExecutor(),
        vfs_registry=None,  # Not used because interactions are empty
        meter_name_to_index={},
        effect_manager=None,
        affordance_overrides=None,
    )
    return manager, inventory, handler


def test_exclusive_item_single_holder() -> None:
    manager, inventory, handler = _make_handler(exclusive=True)

    item = manager.spawn_item(item_type="test_item", position=(0, 0), current_tick=0, initial_state=None)
    assert item is not None

    meters = torch.zeros((1, 0))
    pos = torch.tensor([0, 0], dtype=torch.float32)

    # First agent picks up successfully; item leaves the world
    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=0, meters=meters) is True
    assert inventory.has_item(0, item.instance_id)
    assert manager.active_items == {}
    assert item.holder_agent_ids == {0}

    # Second agent cannot pick up (item no longer on grid)
    assert handler.handle_get_action(agent_idx=1, agent_position=pos, current_tick=1, meters=meters) is False
    assert not inventory.has_item(1, item.instance_id)

    # Dropping returns item to the grid and clears holders
    drop_pos = torch.tensor([1, 0], dtype=torch.float32)
    assert handler.handle_drop_slot_action(agent_idx=0, slot_idx=0, agent_position=drop_pos, current_tick=2) is True
    assert manager.active_items[item.instance_id].position == (1, 0)
    assert item.holder_agent_ids == set()
    assert manager.held_items == {}


def test_shared_item_multiple_holders() -> None:
    manager, inventory, handler = _make_handler(exclusive=False)

    item = manager.spawn_item(item_type="test_item", position=(0, 0), current_tick=0, initial_state=None)
    assert item is not None

    meters = torch.zeros((1, 0))
    pos = torch.tensor([0, 0], dtype=torch.float32)

    # First agent picks up; item stays in world and tracks holder
    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=0, meters=meters) is True
    assert inventory.has_item(0, item.instance_id)
    assert len(manager.active_items) == 1
    assert item.holder_agent_ids == {0}

    # Second agent can also pick up the same item
    assert handler.handle_get_action(agent_idx=1, agent_position=pos, current_tick=1, meters=meters) is True
    assert inventory.has_item(1, item.instance_id)
    assert item.holder_agent_ids == {0, 1}
    assert len(manager.active_items) == 1  # Shared item never left the grid

    # Dropping from one agent only removes that holder; item stays put
    assert handler.handle_drop_slot_action(agent_idx=0, slot_idx=0, agent_position=pos, current_tick=2) is True
    assert item.holder_agent_ids == {1}
    assert len(manager.active_items) == 1
    assert manager.active_items[item.instance_id].position == (0, 0)

    # Final drop clears holders but item remains active
    assert handler.handle_drop_slot_action(agent_idx=1, slot_idx=0, agent_position=pos, current_tick=3) is True
    assert item.holder_agent_ids == set()
    assert len(manager.active_items) == 1
