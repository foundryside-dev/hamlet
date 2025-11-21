"""Tests for ItemManager VFS profile assignment."""

import torch

from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.items.manager import ItemManager
from townlet.vfs.registry import VariableRegistry


def test_item_manager_assigns_vfs_profile_on_spawn():
    """ItemManager should assign vfs_profile from item type on spawn."""
    # Setup: Catalog with item types that have vfs_profile
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="apple",
                vfs_profile="food_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
            ItemTypeConfig(
                id="sword",
                vfs_profile="weapon_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
        ],
        max_items_per_agent=3,
        max_items_in_world=10,
    )

    # Create minimal registry (no VFS variables needed for this test)
    registry = VariableRegistry(
        variables=[],
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device=torch.device("cpu"),
        schema=None,
        vfs_registry=registry,
    )

    # Exercise: Spawn an apple
    apple_instance = manager.spawn_item(
        item_type="apple",
        position=(0, 0),
        current_tick=0,
    )

    # Verify: Instance has vfs_profile assigned
    assert apple_instance is not None
    assert hasattr(apple_instance, "vfs_profile")
    assert apple_instance.vfs_profile == "food_stats"

    # Exercise: Spawn a sword
    sword_instance = manager.spawn_item(
        item_type="sword",
        position=(1, 1),
        current_tick=0,
    )

    # Verify: Different profile assigned
    assert sword_instance is not None
    assert hasattr(sword_instance, "vfs_profile")
    assert sword_instance.vfs_profile == "weapon_stats"


def test_item_manager_preserves_vfs_profile_across_operations():
    """VFS profile should be preserved when item is lifted/placed."""
    # Setup
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="potion",
                vfs_profile="consumable_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ],
        max_items_per_agent=3,
        max_items_in_world=10,
    )

    registry = VariableRegistry(
        variables=[],
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device=torch.device("cpu"),
        schema=None,
        vfs_registry=registry,
    )

    # Spawn item
    item = manager.spawn_item(
        item_type="potion",
        position=(2, 3),
        current_tick=0,
    )

    assert item is not None
    original_profile = item.vfs_profile
    assert original_profile == "consumable_stats"

    # Lift item (pickup)
    lifted = manager.lift_item(item.instance_id)
    assert lifted is not None
    assert lifted.vfs_profile == original_profile

    # Place item (drop)
    placed = manager.place_item(item.instance_id, position=(4, 5))
    assert placed is not None
    assert placed.vfs_profile == original_profile
