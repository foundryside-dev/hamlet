"""Tests for Items + Effects System integration."""

from pathlib import Path

from townlet.config.items_config import ItemsCatalogConfig
from townlet.effects.schema import CommandType
from townlet.items.manager import ItemManager


def test_item_interactions_are_compiled():
    """ItemManager compiles interaction commands using CommandCompiler."""
    # Load items_smoke config
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    # Build schema (same pattern as VectorizedHamletEnv)
    schema = {
        "target.bar.energy": "float",
        "target.bar.health": "float",
        "target.bar.money": "float",
        "target.vfs.has_food": "bool",
    }

    # Create manager with schema
    manager = ItemManager(
        catalog=catalog,
        max_items=10,
        device="cpu",
        schema=schema,  # NEW PARAMETER
    )

    # Verify apple interactions are compiled
    apple_type = next(t for t in manager.compiled_item_types if t.id == "apple")
    assert apple_type.compiled_on_pickup is not None, "on_pickup not compiled"
    assert len(apple_type.compiled_on_pickup) == 1
    assert apple_type.compiled_on_pickup[0].type == CommandType.MODIFY
    assert apple_type.compiled_on_pickup[0].path == "target.vfs.has_food"
    assert apple_type.compiled_on_pickup[0].value_ast is not None, "AST not compiled"

    # Verify on_use commands compiled
    assert apple_type.compiled_on_use is not None
    assert len(apple_type.compiled_on_use) == 1
    assert apple_type.compiled_on_use[0].path == "target.bar.energy"
    assert apple_type.compiled_on_use[0].value_ast is not None
