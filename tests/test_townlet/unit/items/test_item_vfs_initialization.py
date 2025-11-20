"""Tests for item VFS state initialization."""

import torch

from townlet.config.items_config import ItemsCatalogConfig
from townlet.items.manager import ItemManager
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def test_spawn_item_initializes_vfs_state():
    """Spawning item should initialize its VFS variables to defaults."""
    # Create VFS registry with item variables
    variables = [
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
    ]

    vfs_registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
    )

    # Create ItemManager with VFS registry
    catalog = ItemsCatalogConfig.from_yaml("configs/test/items_smoke/items.yaml")
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,  # Skip compilation - we're only testing VFS initialization
        vfs_registry=vfs_registry,  # NEW parameter
    )

    # Spawn item
    item = manager.spawn_item("apple", (3, 4), current_tick=0)

    assert item is not None
    assert item.vfs_index == 0  # First VFS slot

    # VFS state should be initialized to defaults
    durability = vfs_registry.read("durability", context_index=0, scope=VariableScope.ITEM)
    assert durability == 100.0


def test_despawn_item_does_not_clear_vfs_state():
    """Despawning item should NOT clear VFS state (for potential respawn)."""
    variables = [
        VariableDef(
            id="durability",
            scope=VariableScope.ITEM,
            type="scalar",
            default=100.0,
            lifetime="persistent",
            readable_by=["agent", "engine"],
            writable_by=["actions", "engine"],
            description="Item durability",
        ),
    ]

    vfs_registry = VariableRegistry(
        variables=variables,
        num_agents=4,
        max_items=10,
        device=torch.device("cpu"),
    )

    catalog = ItemsCatalogConfig.from_yaml("configs/test/items_smoke/items.yaml")
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,  # Skip compilation - we're only testing VFS initialization
        vfs_registry=vfs_registry,
    )

    # Spawn and modify item
    item = manager.spawn_item("apple", (3, 4), current_tick=0)
    vfs_registry.write("durability", 75.0, context_index=item.vfs_index, scope=VariableScope.ITEM)

    # Despawn
    manager.despawn_item(item.instance_id, current_tick=10)

    # VFS state should remain (slot freed but data intact for debugging/respawn)
    durability = vfs_registry.read("durability", context_index=0, scope=VariableScope.ITEM)
    assert durability == 75.0  # Modified value persists
