"""Unit tests for ItemManager and ItemInstance."""

import pytest

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.instance import ItemInstance
from townlet.items.manager import ItemManager


def test_item_instance_initialization():
    """ItemInstance stores runtime state."""
    item = ItemInstance(
        name="Apple",
        icon="🍎",
        tags=("food",),
        item_type="apple",
        instance_id=42,
        position=(3, 5),  # Grid position
        vfs_index=7,  # Index into item_vfs tensor
        vfs_profile="food_stats",
        spawn_tick=1000,
        duration_total=200,
        duration_remaining=200,
    )

    assert item.item_type == "apple"
    assert item.instance_id == 42
    assert item.position == (3, 5)
    assert item.vfs_index == 7
    assert item.duration_remaining == 200


def test_item_instance_tracks_age():
    """ItemInstance calculates age from spawn_tick."""
    item = ItemInstance(
        name="Medkit",
        icon="💊",
        tags=("medical",),
        item_type="medkit",
        instance_id=1,
        position=(0, 0),
        vfs_index=0,
        vfs_profile="consumable_stats",
        spawn_tick=500,
        duration_total=None,  # Permanent
        duration_remaining=None,
    )

    current_tick = 550
    age = current_tick - item.spawn_tick
    assert age == 50


@pytest.fixture
def items_catalog():
    """Minimal items catalog for testing."""
    from townlet.config.items_config import ItemInteractionsConfig, ItemTypeConfig

    return ItemsCatalogConfig(
        version="1.0",
        max_items_per_agent=3,
        max_items_in_world=10,
        item_types=[
            ItemTypeConfig(
                name="Apple",
                icon="🍎",
                tags=["food"],
                id="apple",
                vfs_profile="food",
                duration=200,
                cooldown=50,
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            ),
            ItemTypeConfig(
                name="Medkit",
                icon="💊",
                tags=["medical"],
                id="medkit",
                vfs_profile="medical",
                duration=None,  # Permanent
                cooldown=None,
                interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
            ),
        ],
    )


def test_item_manager_initialization(items_catalog):
    """ItemManager initializes with catalog and device."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
    )

    assert manager.catalog == items_catalog
    assert manager.max_items == 10
    assert manager.next_instance_id == 0
    assert len(manager.active_items) == 0


def test_spawn_item_creates_instance(items_catalog):
    """spawn_item() creates ItemInstance and allocates VFS slot."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
    )

    item = manager.spawn_item(
        item_type="apple",
        position=(3, 5),
        current_tick=1000,
    )

    assert item.item_type == "apple"
    assert item.instance_id == 0  # First item
    assert item.position == (3, 5)
    assert item.vfs_index >= 0  # Allocated VFS slot
    assert item.duration_total == 200
    assert item.duration_remaining == 200
    assert item.spawn_tick == 1000

    # Verify stored in active_items
    assert item.instance_id in manager.active_items
    assert manager.active_items[item.instance_id] == item


def test_spawn_item_respects_max_items(items_catalog):
    """spawn_item() enforces max_items limit."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=2,  # Only 2 items allowed
        device="cpu",
    )

    _ = manager.spawn_item("apple", (0, 0), 100)
    _ = manager.spawn_item("medkit", (1, 1), 100)

    # Third spawn should return None (at capacity)
    item3 = manager.spawn_item("apple", (2, 2), 100)
    assert item3 is None
    assert len(manager.active_items) == 2


def test_lifecycle_despawn_on_expiration(items_catalog):
    """Items despawn when duration expires."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn apple with 200 tick duration
    item = manager.spawn_item("apple", (0, 0), current_tick=1000)
    assert item.duration_remaining == 200

    # Tick 199 times (not expired yet)
    for tick in range(1001, 1200):
        manager.tick(tick)

    assert item.instance_id in manager.active_items
    assert item.duration_remaining == 1

    # Tick once more (ticks to 0 but doesn't despawn yet - not expired at start of tick)
    manager.tick(1200)
    assert item.instance_id in manager.active_items  # Still alive
    assert item.duration_remaining == 0

    # Next tick despawns (expired at start of tick)
    manager.tick(1201)
    assert item.instance_id not in manager.active_items  # Now despawned
    assert len(manager.active_items) == 0


def test_permanent_items_never_expire(items_catalog):
    """Items with duration=None never despawn."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn medkit (duration=None, permanent)
    item = manager.spawn_item("medkit", (0, 0), current_tick=1000)
    assert item.duration_total is None
    assert item.duration_remaining is None

    # Tick 1000 times
    for tick in range(1001, 2001):
        manager.tick(tick)

    # Item still exists
    assert item.instance_id in manager.active_items


def test_cooldown_prevents_immediate_respawn(items_catalog):
    """Despawned items respect cooldown period."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=10,
        device="cpu",
    )

    # Spawn apple
    item1 = manager.spawn_item("apple", (0, 0), current_tick=1000)
    assert item1 is not None

    # Manually despawn (triggers cooldown=50)
    manager.despawn_item(item1.instance_id, current_tick=1050)

    # Immediate respawn should fail (on cooldown)
    item2 = manager.spawn_item("apple", (1, 1), current_tick=1051)
    assert item2 is None

    # Respawn at tick 1099 should still fail
    item3 = manager.spawn_item("apple", (1, 1), current_tick=1099)
    assert item3 is None

    # Respawn at tick 1100 (cooldown expired) should succeed
    item4 = manager.spawn_item("apple", (1, 1), current_tick=1100)
    assert item4 is not None
    assert item4.item_type == "apple"


def test_vfs_slot_reuse_after_despawn(items_catalog):
    """VFS slots are freed and reused after despawn."""
    manager = ItemManager(
        catalog=items_catalog,
        max_items=3,
        device="cpu",
    )

    # Spawn 3 items
    _ = manager.spawn_item("apple", (0, 0), 100)
    item2 = manager.spawn_item("apple", (1, 1), 100)
    _ = manager.spawn_item("apple", (2, 2), 100)

    assert len(manager.vfs_free_slots) == 0  # All slots used
    assert len(manager.active_items) == 3

    # Despawn item2
    vfs_index_2 = item2.vfs_index
    manager.despawn_item(item2.instance_id, current_tick=200)

    assert len(manager.vfs_free_slots) == 1
    assert vfs_index_2 in manager.vfs_free_slots  # Slot freed

    # Spawn new item (should reuse slot)
    item4 = manager.spawn_item("medkit", (3, 3), current_tick=250)
    assert item4.vfs_index == vfs_index_2  # Reused slot
