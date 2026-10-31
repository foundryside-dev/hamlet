import torch

from tests.test_townlet.utils.builders import make_grid2d_substrate
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
    # S1: two independent single-agent worlds; agent i lives in world i.
    manager = ItemManager(
        catalog=catalog, num_worlds=2, substrate=make_grid2d_substrate(), items_per_world=7, device="cpu", symbols=None, vfs_registry=None
    )
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=CommandExecutor(),
        vfs_registry=None,  # Not used because interactions are empty
        meter_name_to_index={},
        effect_manager=None,
        affordance_overrides=None,
    )
    return manager, inventory, handler


def test_exclusive_item_leaves_its_world_on_pickup_and_returns_on_drop() -> None:
    manager, inventory, handler = _make_handler(exclusive=True)

    item = manager.spawn_item(0, item_type="test_item", position=(0, 0), current_tick=0, initial_state=None)
    assert item is not None

    meters = torch.zeros((2, 0))
    pos = torch.tensor([0, 0], dtype=torch.float32)

    # World 0's agent picks it up; the item leaves world 0's ground into held state
    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=0, meters=meters) is True
    assert inventory.has_item(0, item.instance_id)
    assert manager.worlds[0].active == {}
    assert manager.worlds[0].held == {item.instance_id: item}
    assert item.holder_agent_ids == {0}

    # A second GET at the same cell finds nothing
    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=1, meters=meters) is False

    # Dropping returns item to world 0's ground and clears holders
    drop_pos = torch.tensor([1, 0], dtype=torch.float32)
    assert handler.handle_drop_slot_action(agent_idx=0, slot_idx=0, agent_position=drop_pos, current_tick=2) is True
    assert manager.worlds[0].active[item.instance_id].position == (1, 0)
    assert item.holder_agent_ids == set()
    assert manager.worlds[0].held == {}


def test_shared_item_stays_on_the_ground_while_held() -> None:
    manager, inventory, handler = _make_handler(exclusive=False)

    item = manager.spawn_item(0, item_type="test_item", position=(0, 0), current_tick=0, initial_state=None)
    assert item is not None

    meters = torch.zeros((2, 0))
    pos = torch.tensor([0, 0], dtype=torch.float32)

    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=0, meters=meters) is True
    assert inventory.has_item(0, item.instance_id)
    assert item.holder_agent_ids == {0}
    assert manager.worlds[0].active[item.instance_id] is item  # Shared item never left the ground

    # The same agent cannot hold a second copy
    assert handler.handle_get_action(agent_idx=0, agent_position=pos, current_tick=1, meters=meters) is False

    # Dropping clears the holder; the item stays put
    assert handler.handle_drop_slot_action(agent_idx=0, slot_idx=0, agent_position=pos, current_tick=2) is True
    assert item.holder_agent_ids == set()
    assert manager.worlds[0].active[item.instance_id].position == (0, 0)


def test_an_agent_cannot_pick_up_another_worlds_item() -> None:
    """Agent 1 standing on world 0's item's cell is in world 1, where no item exists (S1)."""
    for exclusive in (True, False):
        manager, inventory, handler = _make_handler(exclusive=exclusive)
        item = manager.spawn_item(0, item_type="test_item", position=(0, 0), current_tick=0, initial_state=None)
        assert item is not None
        pos = torch.tensor([0, 0], dtype=torch.float32)
        assert handler.handle_get_action(agent_idx=1, agent_position=pos, current_tick=0, meters=torch.zeros((2, 0))) is False
        assert not inventory.has_item(1, item.instance_id)
        assert manager.worlds[0].active == {item.instance_id: item}
