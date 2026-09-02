"""Unit tests for agent inventory system."""

import torch

from townlet.items.instance import ItemInstance
from townlet.items.inventory import InventoryState


def test_item_instance_has_no_single_holder_compatibility_property():
    assert "holder_agent_id" not in ItemInstance.__dict__


def test_inventory_initialization():
    """InventoryState initializes empty inventory slots."""
    inventory = InventoryState(
        batch_size=4,
        max_items_per_agent=3,
        device="cpu",
    )

    assert inventory.slots.shape == (4, 3)  # [batch, max_items]
    assert inventory.slots.dtype == torch.long
    assert torch.all(inventory.slots == -1)  # -1 = empty slot


def test_add_item_to_inventory():
    """add_item() stores item instance_id in first empty slot."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=3, device="cpu")

    item1 = ItemInstance(
        name="Apple",
        icon="🍎",
        tags=("food",),
        item_type="apple",
        instance_id=42,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="food_stats",
        spawn_tick=100,
        duration_total=200,
        duration_remaining=200,
    )
    item2 = ItemInstance(
        name="Medkit",
        icon="💊",
        tags=("medical",),
        item_type="medkit",
        instance_id=43,
        position=(0, 0),
        vfs_index=1,
        vfs_profile="consumable_stats",
        spawn_tick=100,
        duration_total=None,
        duration_remaining=None,
    )

    success1 = inventory.add_item(agent_idx=0, item=item1)
    assert success1 is True
    assert inventory.slots[0, 0].item() == 42
    assert item1.holder_agent_ids == {0}

    success2 = inventory.add_item(agent_idx=0, item=item2)
    assert success2 is True
    assert inventory.slots[0, 1].item() == 43
    assert item2.holder_agent_ids == {0}


def test_add_item_overflow_deny():
    """DENY_PICKUP: add_item() returns False when inventory full."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=2, device="cpu")

    item1 = ItemInstance(
        name="a",
        icon="a",
        tags=("t",),
        item_type="a",
        instance_id=1,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    item2 = ItemInstance(
        name="b",
        icon="b",
        tags=("t",),
        item_type="b",
        instance_id=2,
        position=(0, 0),
        vfs_index=1,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    item3 = ItemInstance(
        name="c",
        icon="c",
        tags=("t",),
        item_type="c",
        instance_id=3,
        position=(0, 0),
        vfs_index=2,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )

    inventory.add_item(0, item1)
    inventory.add_item(0, item2)

    # Inventory full (2/2)
    success = inventory.add_item(0, item3)
    assert success is False  # DENY_PICKUP
    assert inventory.slots[0, 0].item() == 1
    assert inventory.slots[0, 1].item() == 2


def test_remove_item_from_slot():
    """remove_item() clears slot and returns instance_id."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=3, device="cpu")

    item = ItemInstance(
        name="Apple",
        icon="🍎",
        tags=("food",),
        item_type="apple",
        instance_id=42,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="food_stats",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item)

    # Remove from slot 0
    instance_id = inventory.remove_item(agent_idx=0, slot_idx=0)
    assert instance_id == 42
    assert inventory.slots[0, 0].item() == -1  # Slot now empty
    assert item.holder_agent_ids == set()


def test_remove_from_empty_slot_returns_none():
    """remove_item() on empty slot returns None."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=3, device="cpu")

    instance_id = inventory.remove_item(agent_idx=0, slot_idx=0)
    assert instance_id is None


def test_get_item_from_slot():
    """get_item() returns instance_id without removing."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=3, device="cpu")

    item = ItemInstance(
        name="Medkit",
        icon="💊",
        tags=("medical",),
        item_type="medkit",
        instance_id=99,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="consumable_stats",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item)

    instance_id = inventory.get_item(agent_idx=0, slot_idx=0)
    assert instance_id == 99
    assert inventory.slots[0, 0].item() == 99  # Still in slot


def test_is_full():
    """is_full() checks if all slots occupied."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=2, device="cpu")

    assert not inventory.is_full(0)

    item1 = ItemInstance(
        name="a",
        icon="a",
        tags=("t",),
        item_type="a",
        instance_id=1,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item1)
    assert not inventory.is_full(0)

    item2 = ItemInstance(
        name="b",
        icon="b",
        tags=("t",),
        item_type="b",
        instance_id=2,
        position=(0, 0),
        vfs_index=1,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item2)
    assert inventory.is_full(0)


def test_count_items():
    """count_items() returns number of non-empty slots."""
    inventory = InventoryState(batch_size=1, max_items_per_agent=3, device="cpu")

    assert inventory.count_items(0) == 0

    item1 = ItemInstance(
        name="a",
        icon="a",
        tags=("t",),
        item_type="a",
        instance_id=1,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item1)
    assert inventory.count_items(0) == 1

    item2 = ItemInstance(
        name="b",
        icon="b",
        tags=("t",),
        item_type="b",
        instance_id=2,
        position=(0, 0),
        vfs_index=1,
        vfs_profile="default",
        spawn_tick=0,
        duration_total=None,
        duration_remaining=None,
    )
    inventory.add_item(0, item2)
    assert inventory.count_items(0) == 2
