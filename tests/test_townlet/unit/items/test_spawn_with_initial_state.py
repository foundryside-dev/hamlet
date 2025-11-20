"""Test ItemManager spawn_item with initial_state parameter."""

import torch

from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.items.manager import ItemManager
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def test_spawn_item_with_initial_state():
    """spawn_item should accept initial_state and apply to VFS."""
    # Create VFS registry with item-scoped variables
    variables = [
        VariableDef(
            id="durability",
            type="scalar",
            scope=VariableScope.ITEM,
            default=100.0,
            lifetime="persistent",
            readable_by=["agent"],
            writable_by=["actions"],
            description="Item durability",
        ),
        VariableDef(
            id="quality",
            type="scalar",
            scope=VariableScope.ITEM,
            default=1.0,
            lifetime="persistent",
            readable_by=["agent"],
            writable_by=["actions"],
            description="Item quality",
        ),
    ]

    vfs_registry = VariableRegistry(
        variables=variables,
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
    )

    # Create minimal catalog
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="sword",
                vfs_profile="weapon",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,  # No Effects compilation needed
        vfs_registry=vfs_registry,
    )

    # Spawn with custom initial_state
    item = manager.spawn_item(
        item_type="sword",
        position=(3, 4),
        current_tick=0,
        initial_state={"durability": 50.0, "quality": 0.5},
    )

    assert item is not None

    # Verify initial_state was applied
    durability = vfs_registry.read("durability", context_index=item.vfs_index, scope=VariableScope.ITEM)
    quality = vfs_registry.read("quality", context_index=item.vfs_index, scope=VariableScope.ITEM)

    assert durability == 50.0
    assert quality == 0.5


def test_spawn_item_without_initial_state_uses_defaults():
    """spawn_item without initial_state should use VFS defaults."""
    # Same setup as above
    variables = [
        VariableDef(
            id="durability",
            type="scalar",
            scope=VariableScope.ITEM,
            default=100.0,
            lifetime="persistent",
            readable_by=["agent"],
            writable_by=["actions"],
            description="Item durability",
        ),
    ]

    vfs_registry = VariableRegistry(
        variables=variables,
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
    )

    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="sword",
                vfs_profile="weapon",
                duration=None,
                cooldown=None,
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[],
                    on_drop=[],
                ),
            )
        ]
    )

    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=None,
        vfs_registry=vfs_registry,
    )

    # Spawn WITHOUT initial_state
    item = manager.spawn_item(
        item_type="sword",
        position=(3, 4),
        current_tick=0,
    )

    assert item is not None

    # Verify defaults were used
    durability = vfs_registry.read("durability", context_index=item.vfs_index, scope=VariableScope.ITEM)
    assert durability == 100.0  # Default value
