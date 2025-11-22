"""Tests for ItemManager VFS profile assignment."""

import torch

from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def _catalog(item_types):
    return ItemsCatalogConfig(
        version="1.0",
        item_types=item_types,
        max_items_per_agent=3,
        max_items_in_world=10,
    )


def test_item_manager_assigns_vfs_profile_on_spawn():
    """ItemManager should assign vfs_profile from item type on spawn."""
    # Setup: Catalog with item types that have vfs_profile
    catalog = _catalog(
        [
            ItemTypeConfig(
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                vfs_profile="food_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
            ItemTypeConfig(
                id="sword",
                name="Sword",
                icon="🗡️",
                tags=["weapon"],
                vfs_profile="weapon_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            ),
        ]
    )

    # Create compiled item profiles
    food_profile = CompiledItemProfile(
        profile_name="food_stats",
        variables=[
            CompiledVariable(name="calories", type="int", ast=None, initial_value=100, result_type="int"),
            CompiledVariable(name="freshness", type="float", ast=None, initial_value=1.0, result_type="float"),
        ],
    )

    weapon_profile = CompiledItemProfile(
        profile_name="weapon_stats",
        variables=[
            CompiledVariable(name="damage", type="int", ast=None, initial_value=50, result_type="int"),
            CompiledVariable(name="durability", type="float", ast=None, initial_value=1.0, result_type="float"),
        ],
    )

    item_profiles = {"food_stats": food_profile, "weapon_stats": weapon_profile}

    # Create registry with item profiles
    registry = VariableRegistry(
        variables=[],
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles=item_profiles,
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
    catalog = _catalog(
        [
            ItemTypeConfig(
                id="potion",
                name="Potion",
                icon="🧪",
                tags=["consumable"],
                vfs_profile="consumable_stats",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    # Create compiled item profiles
    consumable_profile = CompiledItemProfile(
        profile_name="consumable_stats",
        variables=[
            CompiledVariable(name="charges", type="int", ast=None, initial_value=3, result_type="int"),
            CompiledVariable(name="potency", type="float", ast=None, initial_value=1.0, result_type="float"),
        ],
    )

    item_profiles = {"consumable_stats": consumable_profile}

    registry = VariableRegistry(
        variables=[],
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles=item_profiles,
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
