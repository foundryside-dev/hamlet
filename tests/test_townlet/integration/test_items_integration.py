"""Integration tests for Items system in VectorizedHamletEnv."""

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler


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


def test_env_with_items_initializes():
    """Environment with ItemManager and InventoryState initializes correctly."""
    compiler = UniverseCompiler()
    universe = compiler.compile(Path("configs/test/items_smoke"))

    env = VectorizedHamletEnv(
        universe=universe,
        level_name="L0_smoke",
        num_agents=4,
        device="cpu",
    )

    # Verify Items components exist
    assert env.item_manager is not None, "ItemManager not initialized"
    assert env.item_inventory is not None, "InventoryState not initialized"
    assert env.item_handler is not None, "ItemActionHandler not initialized"

    # Verify inventory shape
    assert env.item_inventory.slots.shape == (4, 3), f"Expected (4, 3), got {env.item_inventory.slots.shape}"
    assert torch.all(env.item_inventory.slots == -1), "Inventory should start empty"
