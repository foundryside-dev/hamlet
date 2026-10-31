"""Tests for Items + Effects System integration."""

from pathlib import Path

from tests.test_townlet.utils.builders import make_grid2d_substrate
from townlet.config.items_config import ItemsCatalogConfig
from townlet.effects.schema import CommandType
from townlet.items.manager import ItemManager
from townlet.vfs.namespace import CommandSymbols, Namespace


def test_item_interactions_are_compiled():
    """ItemManager compiles interaction commands using CommandCompiler."""
    # Load items_smoke config
    config_path = Path("configs/test/items_smoke/items.yaml")
    catalog = ItemsCatalogConfig.from_yaml(config_path)

    # The namespace by item profile, as Namespace.of_registry builds it from the compiled roster
    namespace = Namespace(
        variables=[("has_food", "agent", "bool")],
        meters=["energy", "health", "money"],
        item_profiles={"food": {"freshness": "scalar"}, "medical": {"durability": "scalar"}, "currency": {}},
    )

    # Create manager with schema
    manager = ItemManager(
        catalog=catalog,
        num_worlds=1,
        substrate=make_grid2d_substrate(),
        items_per_world=10,
        device="cpu",
        symbols=CommandSymbols(namespace=namespace, expressions={}, time_enabled=True),
    )

    # Verify coin interactions are compiled (coin has on_pickup effect)
    coin_type = next(t for t in manager.compiled_item_types if t.id == "coin")
    assert coin_type.compiled_on_pickup is not None, "on_pickup not compiled"
    assert len(coin_type.compiled_on_pickup) == 1
    assert coin_type.compiled_on_pickup[0].type == CommandType.MODIFY
    assert coin_type.compiled_on_pickup[0].path == "bar.money"
    assert coin_type.compiled_on_pickup[0].value_ast is not None, "AST not compiled"

    # Verify apple on_use commands compiled
    apple_type = next(t for t in manager.compiled_item_types if t.id == "apple")
    assert apple_type.compiled_on_use is not None
    assert len(apple_type.compiled_on_use) == 1
    assert apple_type.compiled_on_use[0].path == "bar.energy"
    assert apple_type.compiled_on_use[0].value_ast is not None
