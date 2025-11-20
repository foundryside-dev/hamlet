"""Unit tests for items configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import (
    ItemAppearanceRuleConfig,
    ItemInteractionsConfig,
    ItemsAppearanceConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
)


def test_item_type_minimal():
    """ItemTypeConfig requires id, vfs_profile, interactions."""
    item = ItemTypeConfig(
        id="apple",
        vfs_profile="food",
        interactions=ItemInteractionsConfig(
            on_pickup=[],
            on_use=[],
            on_drop=[],
        ),
    )

    assert item.id == "apple"
    assert item.vfs_profile == "food"
    assert item.interactions.on_pickup == []


def test_item_type_with_lifecycle():
    """ItemTypeConfig supports duration and cooldown."""
    item = ItemTypeConfig(
        id="mushroom",
        vfs_profile="food",
        interactions=ItemInteractionsConfig(
            on_pickup=[],
            on_use=[{"modify": "target.bar.health", "value": "0.5"}],
            on_drop=[],
        ),
        duration=100,  # Despawns after 100 ticks
        cooldown=50,  # Can't spawn again for 50 ticks
    )

    assert item.duration == 100
    assert item.cooldown == 50


def test_item_interactions_use_effects_syntax():
    """Item interactions use Effects command syntax."""
    interactions = ItemInteractionsConfig(
        on_pickup=[{"modify": "target.vfs.has_food", "value": "true"}],
        on_use=[
            {"modify": "target.bar.energy", "value": "target.bar.energy + 0.3"},
            {"spawn_effect": "ate_food", "target": "self", "duration": 10},
        ],
        on_drop=[{"modify": "target.vfs.has_food", "value": "false"}],
    )

    assert len(interactions.on_use) == 2
    assert interactions.on_use[0]["modify"] == "target.bar.energy"


def test_item_type_rejects_custom_commands():
    """Phase 1-3: Custom item commands are NOT supported."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemTypeConfig(
            id="umbrella",
            vfs_profile="tool",
            interactions=ItemInteractionsConfig(
                on_pickup=[],
                on_use=[],
                on_drop=[],
                local_commands=[{"name": "OPEN_UMBRELLA"}],  # REJECTED
            ),
        )


def test_items_catalog_minimal():
    """ItemsCatalogConfig requires item_types list."""
    catalog = ItemsCatalogConfig(
        item_types=[
            ItemTypeConfig(
                id="apple",
                vfs_profile="food",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[{"modify": "target.bar.energy", "value": "0.3"}],
                    on_drop=[],
                ),
            ),
        ],
    )

    assert len(catalog.item_types) == 1
    assert catalog.max_items_per_agent == 3  # Default
    assert catalog.max_items_in_world == 10  # Default


def test_items_catalog_rejects_duplicate_ids():
    """ItemsCatalogConfig validates unique item type IDs."""
    with pytest.raises(ValidationError, match="Duplicate item type IDs"):
        ItemsCatalogConfig(
            item_types=[
                ItemTypeConfig(id="apple", vfs_profile="food", interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[])),
                ItemTypeConfig(
                    id="apple", vfs_profile="food", interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[])
                ),  # Duplicate
            ],
        )


def test_items_appearance_minimal():
    """ItemsAppearanceConfig defines level-specific spawn rules."""
    appearance = ItemsAppearanceConfig(
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=3,
                spawn_interval=100,
            ),
        ],
    )

    assert len(appearance.items) == 1
    assert appearance.items[0].item_type == "apple"
    assert appearance.items[0].spawn_count == 3


def test_items_appearance_empty_allowed():
    """Level can have no items (appearance.items = [])."""
    appearance = ItemsAppearanceConfig(items=[])
    assert appearance.items == []


def test_items_catalog_from_yaml():
    """Load items catalog from YAML file."""
    from pathlib import Path

    import yaml

    catalog_path = Path("/home/john/hamlet/configs/test/items_smoke/items.yaml")
    with open(catalog_path) as f:
        data = yaml.safe_load(f)

    catalog = ItemsCatalogConfig(**data["items"])

    assert len(catalog.item_types) == 3
    assert catalog.item_types[0].id == "apple"
    assert catalog.item_types[0].duration is None  # Permanent
    assert catalog.item_types[1].id == "medkit"
    assert catalog.item_types[1].duration == 100  # Despawns after 100 ticks
    assert catalog.item_types[2].id == "coin"


def test_items_appearance_from_yaml():
    """Load items appearance from YAML file."""
    from pathlib import Path

    import yaml

    appearance_path = Path("/home/john/hamlet/configs/test/items_smoke/levels/L0_smoke/items.yaml")
    with open(appearance_path) as f:
        data = yaml.safe_load(f)

    appearance = ItemsAppearanceConfig(**data)

    assert len(appearance.items) == 3
    assert appearance.items[0].item_type == "apple"
    assert appearance.items[0].spawn_count == 3
    assert appearance.items[0].spawn_interval == 100
