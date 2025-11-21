"""Test ItemManager spawn_item with initial_state parameter."""

import torch

from townlet.config.items_config import (
    ItemInteractionsConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)
from townlet.items.manager import ItemManager
from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable
from townlet.vfs.registry import VariableRegistry


def test_spawn_item_with_initial_state():
    """spawn_item should accept initial_state parameter (profile-driven path)."""
    # NOTE: initial_state only works with deprecated variable-based system
    # Profile-driven system doesn't have per-instance initialization yet
    # This test verifies that spawn_item accepts the parameter without crashing

    # Create item profile with durability and quality variables
    weapon_profile = CompiledItemProfile(
        profile_name="weapon",
        variables=[
            CompiledVariable(
                name="durability",
                type="scalar",
                ast=None,
                initial_value=100.0,
                result_type="scalar",
            ),
            CompiledVariable(
                name="quality",
                type="scalar",
                ast=None,
                initial_value=1.0,
                result_type="scalar",
            ),
        ],
    )

    # Create VFS registry with item profiles
    vfs_registry = VariableRegistry(
        variables=[],  # No agent-scoped variables
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles={"weapon": weapon_profile},
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

    # Spawn with empty initial_state (profile-driven path doesn't use it yet)
    item = manager.spawn_item(
        item_type="sword",
        position=(3, 4),
        current_tick=0,
        initial_state={},  # Empty - profile system doesn't support per-instance init yet
    )

    assert item is not None
    assert item.vfs_profile == "weapon"  # Profile assigned from config
    assert item.vfs_index == 0  # First VFS slot allocated

    # Verify profile mapping was created during initialization
    assert "weapon" in vfs_registry.item_profile_map
    assert "durability" in vfs_registry.item_profile_map["weapon"]
    assert "quality" in vfs_registry.item_profile_map["weapon"]

    # Verify VFS tensor was allocated (unified storage)
    assert vfs_registry.item_vfs is not None
    assert vfs_registry.item_vfs.shape == (10, 2)  # (max_items, max_vars_across_profiles)


def test_spawn_item_without_initial_state_uses_defaults():
    """spawn_item without initial_state should allocate VFS profile storage."""
    # Create item profile with durability variable
    weapon_profile = CompiledItemProfile(
        profile_name="weapon",
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
        variables=[],
        num_agents=1,
        max_items=10,
        device=torch.device("cpu"),
        item_profiles={"weapon": weapon_profile},
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
    assert item.vfs_profile == "weapon"  # Profile assigned
    assert item.vfs_index == 0  # First VFS slot

    # Verify profile mapping exists
    assert "weapon" in vfs_registry.item_profile_map
    assert "durability" in vfs_registry.item_profile_map["weapon"]

    # Verify VFS tensor was allocated (unified storage)
    assert vfs_registry.item_vfs is not None
    assert vfs_registry.item_vfs.shape == (10, 1)  # (max_items, max_vars_across_profiles)
