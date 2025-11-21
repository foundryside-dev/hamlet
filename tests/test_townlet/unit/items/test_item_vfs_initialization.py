"""Tests for item VFS state initialization."""

import torch

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def test_spawn_item_initializes_vfs_state():
    """Spawning item should allocate VFS profile storage (profile-driven)."""
    # Create item profile with durability variable
    food_profile = CompiledItemProfile(
        profile_name="food",
        variables=[
            CompiledVariable(
                name="durability",
                type="scalar",
                ast=None,
                initial_value=100.0,
                result_type="scalar",
            ),
        ],
    )

    # Create VFS registry with item profiles
    vfs_registry = VariableRegistry(
        variables=[],  # No agent-scoped variables
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles={"food": food_profile},
    )

    # Create ItemManager with VFS registry
    catalog = ItemsCatalogConfig.from_yaml("configs/test/items_smoke/items.yaml")
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,  # Skip compilation - we're only testing VFS initialization
        vfs_registry=vfs_registry,
    )

    # Spawn item
    item = manager.spawn_item("apple", (3, 4), current_tick=0)

    assert item is not None
    assert item.vfs_index == 0  # First VFS slot
    assert item.vfs_profile == "food"  # Profile from config

    # Verify VFS profile mapping was created during initialization
    assert "food" in vfs_registry.item_profile_map
    assert "durability" in vfs_registry.item_profile_map["food"]

    # Verify VFS tensor was allocated (unified storage)
    assert vfs_registry.item_vfs is not None
    assert vfs_registry.item_vfs.shape == (10, 1)  # (max_items, max_vars_across_profiles)


def test_despawn_item_does_not_clear_vfs_state():
    """Despawning item should free VFS slot but not clear profile storage."""
    # Create item profile with durability variable
    food_profile = CompiledItemProfile(
        profile_name="food",
        variables=[
            CompiledVariable(
                name="durability",
                type="scalar",
                ast=None,
                initial_value=100.0,
                result_type="scalar",
            ),
        ],
    )

    # Create VFS registry with item profiles
    vfs_registry = VariableRegistry(
        variables=[],  # No agent-scoped variables
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles={"food": food_profile},
    )

    catalog = ItemsCatalogConfig.from_yaml("configs/test/items_smoke/items.yaml")
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,  # Skip compilation - we're only testing VFS state persistence
        vfs_registry=vfs_registry,
    )

    # Spawn item
    item = manager.spawn_item("apple", (3, 4), current_tick=0)
    assert item is not None
    vfs_index = item.vfs_index

    # Despawn
    manager.despawn_item(item.instance_id, current_tick=10)

    # VFS slot should be freed for reuse
    assert vfs_index in manager.vfs_free_slots

    # VFS profile mapping should still exist (not cleared on despawn)
    assert "food" in vfs_registry.item_profile_map
    assert "durability" in vfs_registry.item_profile_map["food"]

    # VFS tensor should still be allocated (batch storage persists)
    assert vfs_registry.item_vfs is not None
    assert vfs_registry.item_vfs.shape == (10, 1)  # (max_items, max_vars_across_profiles), unchanged
