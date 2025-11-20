import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


class MockItemManager:
    """Mock ItemManager for testing spawn_item command."""

    def __init__(self):
        self.spawned_items = []
        self.current_step = 0

    def spawn_item(self, item_id, position_hint, initial_state=None):
        """Mock spawn_item that records calls."""
        from townlet.items.instance import ItemInstance

        instance = ItemInstance(
            item_type=item_id,
            instance_id=len(self.spawned_items),
            position=(0, 0),  # Dummy position
            vfs_index=0,
            spawn_tick=self.current_step,
            duration_total=None,
            duration_remaining=None,
        )
        self.spawned_items.append(
            {
                "item_id": item_id,
                "position_hint": position_hint,
                "initial_state": initial_state,
                "instance": instance,
            }
        )
        return instance

    def get_active_items(self):
        """Return spawned items."""
        return [item["instance"] for item in self.spawned_items]


def test_spawn_item_at_self_position():
    """Test spawn_item command creates item at self position."""
    item_manager = MockItemManager()
    executor = CommandExecutor()

    # Create spawn_item command
    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="apple",
        position="self",
        quantity=1,
    )

    # Create context with item_manager
    bars = {"health": torch.tensor([1.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        item_manager=item_manager,
    )

    # Execute command
    executor.execute(command, context)

    # Verify item spawned
    assert len(item_manager.spawned_items) == 1
    assert item_manager.spawned_items[0]["item_id"] == "apple"
    assert item_manager.spawned_items[0]["position_hint"] == ("agent", 0)


def test_spawn_item_with_initial_state():
    """Test spawn_item passes initial_state to ItemManager."""
    item_manager = MockItemManager()
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_ITEM,
        item_id="sword",
        position="self",
        quantity=1,
        initial_state={"durability": 0.5},  # Damaged sword
    )

    bars = {"health": torch.tensor([1.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        item_manager=item_manager,
    )

    executor.execute(command, context)

    # Verify initial_state passed to spawn_item
    assert len(item_manager.spawned_items) == 1
    assert item_manager.spawned_items[0]["initial_state"] == {"durability": 0.5}
