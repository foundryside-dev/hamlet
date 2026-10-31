"""Unit tests for item action handlers."""

import torch

from tests.test_townlet.utils.builders import make_grid2d_substrate
from townlet.config.items_config import ItemInteractionsConfig, ItemsCatalogConfig, ItemTypeConfig
from townlet.items.action_handlers import ItemActionHandler
from townlet.items.manager import ItemManager


def _catalog(item_types):
    """Helper to build ItemsCatalogConfig with required fields."""
    return ItemsCatalogConfig(
        version="1.0",
        item_types=item_types,
        max_items_per_agent=3,
        max_items_in_world=10,
    )


# Stubs for testing
class MockCommandExecutor:
    """Mock CommandExecutor for testing."""

    def execute(self, *args, **kwargs):
        """No-op execute."""
        pass


class MockVariableRegistry:
    """Mock VariableRegistry for testing."""

    def __init__(self):
        self.variables = {}

    def get(self, key, default=None):
        """Mock get."""
        return self.variables.get(key, default)


class MockEffectManager:
    """Mock EffectManager for satisfying ExecutionContext."""

    def spawn_effect(self, *args, **kwargs):
        """No-op or raise to indicate misuse."""
        raise RuntimeError("spawn_effect called unexpectedly in MockEffectManager")


def test_get_action_picks_up_item():
    """GET action: picks up item at agent position."""
    # Setup
    catalog = _catalog(
        [
            ItemTypeConfig(
                exclusive=True,
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                vfs_profile="food",
                interactions=ItemInteractionsConfig(
                    on_pickup=[{"modify": "target.vfs.has_food", "value": "true"}],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    # Spawn item at agent's position
    item = manager.spawn_item(0, "apple", position=(3, 5), current_tick=100)
    assert item is not None

    # Agent at same position tries to pick up
    agent_idx = 0
    agent_position = torch.tensor([[3, 5]], dtype=torch.long)
    meters = torch.zeros((1, 2), dtype=torch.float32)  # [batch, num_meters]

    success = handler.handle_get_action(
        agent_idx=agent_idx,
        agent_position=agent_position[agent_idx],
        current_tick=100,
        meters=meters,
    )

    assert success is True
    assert inventory.count_items(agent_idx) == 1
    assert inventory.get_item(agent_idx, slot_idx=0) == item.instance_id
    assert item.instance_id not in manager.worlds[0].active  # Removed from world


def test_get_action_fails_when_inventory_full():
    """GET action: DENY_PICKUP when inventory full."""
    catalog = _catalog(
        [
            ItemTypeConfig(
                exclusive=True,
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                vfs_profile="food",
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            )
        ]
    )

    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    # Fill inventory (the catalog's max_items_per_agent is 3)
    for _ in range(3):
        inventory.add_item(0, manager.spawn_item(0, "apple", (0, 0), 100))

    # Try to pick up third item
    item3 = manager.spawn_item(0, "apple", (3, 5), 100)
    agent_position = torch.tensor([3, 5], dtype=torch.long)
    meters = torch.zeros((1, 2), dtype=torch.float32)  # [batch, num_meters]

    success = handler.handle_get_action(
        agent_idx=0,
        agent_position=agent_position,
        current_tick=100,
        meters=meters,
    )

    assert success is False  # DENY_PICKUP
    assert inventory.count_items(0) == 3
    assert item3.instance_id in manager.worlds[0].active  # Still in world


def test_get_action_fails_when_no_item_at_position():
    """GET action: fails when no item at agent position."""
    catalog = _catalog([])
    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    # No item spawned at (3, 5)
    agent_position = torch.tensor([3, 5], dtype=torch.long)
    meters = torch.zeros((1, 2), dtype=torch.float32)  # [batch, num_meters]

    success = handler.handle_get_action(
        agent_idx=0,
        agent_position=agent_position,
        current_tick=100,
        meters=meters,
    )

    assert success is False
    assert inventory.count_items(0) == 0


def test_use_slot_action_succeeds_when_slot_occupied():
    """USE_SLOT_N: succeeds when slot has item."""
    catalog = _catalog(
        [
            ItemTypeConfig(
                exclusive=True,
                id="medkit",
                name="Medkit",
                icon="💊",
                tags=["medical"],
                vfs_profile="medical",
                interactions=ItemInteractionsConfig(
                    on_use=[{"modify": "target.bar.health", "value": "0.5"}],
                    on_pickup=[],
                    on_drop=[],
                ),
            )
        ]
    )

    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    # Add item to inventory
    item = manager.spawn_item(0, "medkit", (0, 0), 100)
    inventory.add_item(0, item)
    meters = torch.zeros((1, 2), dtype=torch.float32)  # [batch, num_meters]

    success = handler.handle_use_slot_action(
        agent_idx=0,
        slot_idx=0,
        current_tick=100,
        meters=meters,
    )

    assert success is True
    # Item remains in inventory after use (not consumed)
    assert inventory.get_item(0, 0) == item.instance_id


def test_use_slot_action_fails_when_slot_empty():
    """USE_SLOT_N: fails when slot is empty."""
    catalog = _catalog([])
    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )
    meters = torch.zeros((1, 2), dtype=torch.float32)  # [batch, num_meters]

    success = handler.handle_use_slot_action(
        agent_idx=0,
        slot_idx=0,
        current_tick=100,
        meters=meters,
    )

    assert success is False


def test_drop_slot_action_removes_from_inventory():
    """DROP_SLOT_N: removes item from inventory."""
    catalog = _catalog(
        [
            ItemTypeConfig(
                exclusive=True,
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                vfs_profile="food",
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            )
        ]
    )

    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    inventory = manager.inventory
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    # Add item to inventory
    item = manager.spawn_item(0, "apple", (0, 0), 100)
    manager.despawn_item(item.instance_id, 100)  # Remove from world first
    inventory.slots[0, 0] = item.instance_id  # Manually add to inventory
    inventory.items[item.instance_id] = item  # Add to metadata dict

    agent_position = torch.tensor([5, 5], dtype=torch.long)

    success = handler.handle_drop_slot_action(
        agent_idx=0,
        slot_idx=0,
        agent_position=agent_position,
        current_tick=100,
    )

    assert success is True
    assert inventory.get_item(0, 0) is None  # Removed from inventory


def test_drop_slot_action_fails_when_slot_empty():
    """DROP_SLOT_N: fails when slot is empty."""
    catalog = _catalog([])
    manager = ItemManager(catalog=catalog, num_worlds=1, substrate=make_grid2d_substrate(), items_per_world=10, device="cpu")
    handler = ItemActionHandler(
        manager=manager,
        command_executor=MockCommandExecutor(),
        vfs_registry=MockVariableRegistry(),
        meter_name_to_index={"energy": 0, "health": 1},
        effect_manager=MockEffectManager(),
    )

    agent_position = torch.tensor([5, 5], dtype=torch.long)

    success = handler.handle_drop_slot_action(
        agent_idx=0,
        slot_idx=0,
        agent_position=agent_position,
        current_tick=100,
    )

    assert success is False
