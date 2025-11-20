"""Tests for periodic item respawning."""

from pathlib import Path

from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
from townlet.items.manager import ItemManager


def test_respawn_timer_initialized_on_despawn():
    """When item despawns with spawn_interval configured, respawn timer is set."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    # Load appearance config (has spawn_interval)
    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 100,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    # Set appearance config
    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn apple
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    assert item is not None

    # Despawn it (item expires)
    manager.despawn_item(item.instance_id, current_tick=50)

    # Verify respawn timer set
    assert "apple" in manager.respawn_timers
    assert manager.respawn_timers["apple"] == 50 + 100  # current_tick + spawn_interval


def test_respawn_timer_not_set_without_spawn_interval():
    """Items without spawn_interval don't get respawn timers."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": None,  # No periodic respawn
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn and despawn
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    manager.despawn_item(item.instance_id, current_tick=50)

    # No respawn timer
    assert "apple" not in manager.respawn_timers


def test_process_respawns_spawns_item_when_timer_expires():
    """process_respawns spawns item when timer expires."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 100,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Spawn and despawn apple at tick 0
    item = manager.spawn_item("apple", position=(0, 0), current_tick=0)
    manager.despawn_item(item.instance_id, current_tick=0)

    # Timer should be at tick 100
    assert manager.respawn_timers["apple"] == 100

    # Process respawns at tick 99 (not yet)
    manager.process_respawns(current_tick=99)
    assert len(manager.active_items) == 0

    # Process respawns at tick 100 (timer expires)
    manager.process_respawns(current_tick=100)
    assert len(manager.active_items) == 1

    # Verify apple spawned
    spawned_items = list(manager.active_items.values())
    assert spawned_items[0].item_type == "apple"

    # Timer should be cleared
    assert "apple" not in manager.respawn_timers


def test_process_respawns_respects_max_items_capacity():
    """process_respawns doesn't spawn if at max capacity."""
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    appearance_config = ItemsAppearanceConfig(
        version="1.0",
        items=[
            {
                "item_type": "apple",
                "spawn_count": 1,
                "spawn_interval": 10,
                "spawn_position": "random",
            }
        ],
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=2,  # Small capacity
        device="cpu",
    )

    manager.set_appearance_config(appearance_config, grid_size=(7, 7))

    # Fill manager to capacity with coins
    manager.spawn_item("coin", position=(0, 0), current_tick=0)
    manager.spawn_item("coin", position=(1, 1), current_tick=0)
    assert len(manager.active_items) == 2

    # Set respawn timer for apple
    manager.respawn_timers["apple"] = 10

    # Try to respawn apple
    manager.process_respawns(current_tick=10)

    # Apple should NOT spawn (at capacity)
    assert len(manager.active_items) == 2  # Still just 2 coins

    # Timer should remain (will retry next tick)
    assert "apple" in manager.respawn_timers
