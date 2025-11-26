"""Tests for item lifecycle and persistence."""

from pathlib import Path

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.manager import ItemManager


def test_item_preserves_identity_when_lifted_and_placed():
    """Items retain instance_id and VFS state when lifted/placed."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn apple at (2, 2)
    item = manager.spawn_item("apple", position=(2, 2), current_tick=0)
    assert item is not None
    original_id = item.instance_id

    # Lift item (pickup) - moves to held_items
    manager.lift_item(original_id)

    # Verify NOT in active_items
    assert original_id not in manager.active_items

    # Verify IN held_items
    assert original_id in manager.held_items
    held_item = manager.held_items[original_id]
    assert held_item.instance_id == original_id
    assert held_item.item_type == "apple"

    # Place item back at (5, 5) (drop)
    manager.place_item(original_id, position=(5, 5))

    # Verify back in active_items with SAME ID
    assert original_id in manager.active_items
    placed_item = manager.active_items[original_id]
    assert placed_item.instance_id == original_id
    assert placed_item.position == (5, 5)

    # Verify NOT in held_items
    assert original_id not in manager.held_items


def test_held_items_continue_ticking():
    """Items in inventory continue to age/spoil."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn medkit with duration=100 (unlike apple which is permanent)
    item = manager.spawn_item("medkit", position=(0, 0), current_tick=0)
    initial_duration = item.duration_remaining
    manager.lift_item(item.instance_id)

    # Tick 50 times
    for tick in range(1, 51):
        manager.tick(tick)

    # Verify item aged (duration_remaining decreased)
    held_item = manager.held_items[item.instance_id]
    assert held_item.duration_remaining == initial_duration - 50, "Held items must age"
