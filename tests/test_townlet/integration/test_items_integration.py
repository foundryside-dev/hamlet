"""Integration tests for Items system in VectorizedHamletEnv.

NOTE: Full environment integration requires HamletConfig schema changes
to support items_catalog field. These tests verify config existence only.
"""

from pathlib import Path


def test_items_smoke_config_pack_exists():
    """items_smoke config pack has all required files."""
    config_dir = Path("configs/test/items_smoke")

    # Core config files
    assert (config_dir / "items.yaml").exists(), "items.yaml missing"
    assert (config_dir / "substrate.yaml").exists(), "substrate.yaml missing"
    assert (config_dir / "bars.yaml").exists(), "bars.yaml missing"
    assert (config_dir / "affordances.yaml").exists(), "affordances.yaml missing"
    assert (config_dir / "training.yaml").exists(), "training.yaml missing"


def test_items_catalog_has_three_item_types():
    """items.yaml defines apple, medkit, coin."""
    import yaml

    config_path = Path("configs/test/items_smoke/items.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    item_types = data["items"]["item_types"]
    item_ids = [item["id"] for item in item_types]

    assert len(item_ids) == 3, f"Expected 3 item types, got {len(item_ids)}"
    assert "apple" in item_ids, "apple item type missing"
    assert "medkit" in item_ids, "medkit item type missing"
    assert "coin" in item_ids, "coin item type missing"


def test_items_catalog_validates_with_schema():
    """items.yaml validates against ItemsCatalogConfig schema."""
    import yaml

    from townlet.config.items_config import ItemsCatalogConfig

    config_path = Path("configs/test/items_smoke/items.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Should not raise ValidationError
    catalog = ItemsCatalogConfig(**data["items"])

    assert catalog.max_items_per_agent == 3
    assert catalog.max_items_in_world == 10
    assert len(catalog.item_types) == 3


def test_item_actions_defined_in_global_actions():
    """default_curriculum/actions.yaml has GET/USE_SLOT/DROP_SLOT actions."""
    import yaml

    config_path = Path("configs/default_curriculum/actions.yaml")
    with open(config_path) as f:
        data = yaml.safe_load(f)

    action_names = [a["name"] for a in data["actions"]["custom_actions"]]

    # Item actions
    assert "GET" in action_names, "GET action missing"
    assert "USE_SLOT_0" in action_names, "USE_SLOT_0 action missing"
    assert "USE_SLOT_1" in action_names, "USE_SLOT_1 action missing"
    assert "USE_SLOT_2" in action_names, "USE_SLOT_2 action missing"
    assert "DROP_SLOT_0" in action_names, "DROP_SLOT_0 action missing"
    assert "DROP_SLOT_1" in action_names, "DROP_SLOT_1 action missing"
    assert "DROP_SLOT_2" in action_names, "DROP_SLOT_2 action missing"


# ============================================================================
# DEFERRED TO PHASE 5: Environment Integration Tests
# ============================================================================
# The following tests require HamletConfig schema changes to support
# items_catalog field. They are placeholders for Phase 5 implementation.
# ============================================================================


def test_env_with_items_initializes_deferred():
    """DEFERRED: Environment with ItemManager and InventoryState initializes correctly.

    Requires:
    - HamletConfig.items_catalog field
    - VectorizedHamletEnv Items integration
    - ItemManager initialization in reset()
    """
    # TODO: Setup config pack with items enabled
    # TODO: Create env with items
    # TODO: Verify env.item_manager exists
    # TODO: Verify env.item_inventory exists
    # TODO: Verify item actions in action space

    assert True  # Placeholder


def test_get_action_picks_up_item_deferred():
    """DEFERRED: GET action picks up item from world into inventory.

    Requires:
    - Items environment integration
    - ItemManager.spawn_item() in reset()
    - GET action dispatch wiring
    """
    # TODO: Setup env with items_smoke config
    # TODO: Spawn item at position (3, 5)
    # TODO: Move agent to (3, 5)
    # TODO: Execute GET action
    # TODO: Verify item in inventory
    # TODO: Verify item removed from world

    assert True  # Placeholder


def test_use_slot_action_executes_effects_deferred():
    """DEFERRED: USE_SLOT_N action executes on_use Effects commands.

    Requires:
    - Items environment integration
    - Effects execution in ItemActionHandler
    - VFS integration for item state
    """
    # TODO: Setup env with items_smoke config
    # TODO: Give agent apple (on_use: energy +0.3)
    # TODO: Record initial energy
    # TODO: Execute USE_SLOT_0 action
    # TODO: Verify energy increased by 0.3

    assert True  # Placeholder


def test_drop_slot_action_spawns_item_in_world_deferred():
    """DEFERRED: DROP_SLOT_N action places item back in world.

    Requires:
    - Items environment integration
    - ItemInstance item_type tracking for respawn
    - DROP action spawn logic
    """
    # TODO: Setup env with items_smoke config
    # TODO: Give agent apple in slot 0
    # TODO: Agent at position (5, 5)
    # TODO: Execute DROP_SLOT_0 action
    # TODO: Verify item removed from inventory
    # TODO: Verify item spawned at (5, 5)

    assert True  # Placeholder
