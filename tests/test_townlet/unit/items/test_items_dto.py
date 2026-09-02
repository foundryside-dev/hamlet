"""Unit tests for items configuration DTOs."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import (
    ItemAppearanceRuleConfig,
    ItemCustomCommand,
    ItemInteractionsConfig,
    ItemsAppearanceConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
    build_item_command_action_name,
)


def test_item_type_minimal():
    """ItemTypeConfig requires id, vfs_profile, interactions."""
    item = ItemTypeConfig(
        id="apple",
        name="Apple",
        icon="🍎",
        tags=["food"],
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
        name="Mushroom",
        icon="🍄",
        tags=["food"],
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
            {"spawn_effect": "ate_food", "target": "self", "intensity": 1.0},
        ],
        on_drop=[{"modify": "target.vfs.has_food", "value": "false"}],
    )

    assert len(interactions.on_use) == 2
    assert interactions.on_use[0]["modify"] == "target.bar.energy"


def test_item_type_rejects_custom_commands():
    """Custom item commands are supported via ItemCustomCommand."""
    cfg = ItemTypeConfig(
        id="umbrella",
        name="Umbrella",
        icon="☂️",
        tags=["tool"],
        vfs_profile="tool",
        interactions=ItemInteractionsConfig(
            on_pickup=[],
            on_use=[],
            on_drop=[],
            local_commands=[
                ItemCustomCommand(name="OPEN_UMBRELLA", description=None, effects=[{"modify": "target.bar.energy", "value": "1.0"}])
            ],
        ),
    )
    assert cfg.interactions.local_commands[0].name == "OPEN_UMBRELLA"


def test_items_catalog_minimal():
    """ItemsCatalogConfig requires item_types list and explicit limits/version."""
    catalog = ItemsCatalogConfig(
        version="1.0",
        item_types=[
            ItemTypeConfig(
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                vfs_profile="food",
                interactions=ItemInteractionsConfig(
                    on_pickup=[],
                    on_use=[{"modify": "target.bar.energy", "value": "0.3"}],
                    on_drop=[],
                ),
            ),
        ],
        max_items_per_agent=3,
        max_items_in_world=10,
    )

    assert len(catalog.item_types) == 1
    assert catalog.max_items_per_agent == 3
    assert catalog.max_items_in_world == 10


def test_items_catalog_rejects_duplicate_ids():
    """ItemsCatalogConfig validates unique item type IDs."""
    with pytest.raises(ValidationError, match="Duplicate item type IDs"):
        ItemsCatalogConfig(
            version="1.0",
            item_types=[
                ItemTypeConfig(
                    id="apple",
                    name="Apple",
                    icon="🍎",
                    tags=["food"],
                    vfs_profile="food",
                    interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
                ),
                ItemTypeConfig(
                    id="apple",
                    name="Apple2",
                    icon="🍏",
                    tags=["food"],
                    vfs_profile="food",
                    interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
                ),  # Duplicate
            ],
            max_items_per_agent=3,
            max_items_in_world=10,
        )


def test_items_appearance_minimal():
    """ItemsAppearanceConfig defines level-specific spawn rules."""
    appearance = ItemsAppearanceConfig(
        version="1.0",
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=3,
                placement={"mode": "random"},
                schedule={"type": "periodic", "period": 100},
                when=None,
            ),
        ],
    )

    assert len(appearance.items) == 1
    assert appearance.items[0].item_type == "apple"
    assert appearance.items[0].spawn_count == 3


def test_items_appearance_accepts_when():
    """Spawn conditions can be declared on appearance rules."""
    appearance = ItemsAppearanceConfig(
        version="1.0",
        items=[
            ItemAppearanceRuleConfig(
                item_type="apple",
                spawn_count=1,
                schedule=None,
                when="bar.energy > 0.5",
            ),
        ],
    )

    assert appearance.items[0].when == "bar.energy > 0.5"
    assert appearance.items[0].when_ast is None


def test_items_appearance_empty_allowed():
    """Level can have no items (appearance.items = [])."""
    appearance = ItemsAppearanceConfig(version="1.0", items=[])
    assert appearance.items == []


def test_items_catalog_from_yaml():
    """Load items catalog from YAML file."""
    from pathlib import Path

    import yaml

    catalog_path = Path("configs/test/items_smoke/items.yaml")
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

    appearance_path = Path("configs/test/items_smoke/levels/L0_smoke/items.yaml")
    with open(appearance_path) as f:
        data = yaml.safe_load(f)

    appearance = ItemsAppearanceConfig(**data)

    assert len(appearance.items) == 3
    assert appearance.items[0].item_type == "apple"
    assert appearance.items[0].spawn_count == 3
    assert appearance.items[0].schedule is not None
    assert appearance.items[0].schedule.type == "periodic"
    assert appearance.items[0].schedule.period == 100


def test_items_catalog_requires_version_and_limits():
    """Missing version or limits should fail validation."""
    with pytest.raises(ValidationError):
        ItemsCatalogConfig(
            item_types=[
                ItemTypeConfig(
                    id="apple",
                    name="Apple",
                    icon="🍎",
                    tags=["food"],
                    vfs_profile="food",
                    interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
                )
            ],
            max_items_in_world=10,
        )
    with pytest.raises(ValidationError):
        ItemsCatalogConfig(
            version="1.0",
            item_types=[
                ItemTypeConfig(
                    id="apple",
                    name="Apple",
                    icon="🍎",
                    tags=["food"],
                    vfs_profile="food",
                    interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
                )
            ],
            max_items_per_agent=3,
        )


def test_items_catalog_rejects_unknown_fields():
    """Unknown fields are forbidden on ItemsCatalogConfig."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemsCatalogConfig(
            version="1.0",
            item_types=[],
            max_items_per_agent=1,
            max_items_in_world=1,
            unknown_field=123,  # type: ignore[arg-type]
        )


def test_item_custom_commands_schema_and_naming():
    """Custom commands accept effects and generate stable action names."""
    cmd = ItemCustomCommand(
        name="OPEN_UMBRELLA",
        description="Open it",
        effects=[{"modify": "target.bar.energy", "value": "1.0"}],
    )
    interactions = ItemInteractionsConfig(
        on_pickup=[],
        on_use=[],
        on_drop=[],
        local_commands=[cmd],
        inventory_commands=[],
    )
    assert interactions.local_commands[0].name == "OPEN_UMBRELLA"
    assert build_item_command_action_name("umbrella", "OPEN_UMBRELLA", "local") == "ITEM_LOCAL_UMBRELLA_OPEN_UMBRELLA"


def test_item_interactions_reject_distribution_alias():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemInteractionsConfig(on_pickup=[{"distribution": "uniform"}], on_use=[], on_drop=[])


def test_item_custom_commands_reject_distribution_alias():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ItemCustomCommand(name="ROLL", effects=[{"distribution": "uniform"}])
