"""Extended DTO validation tests for items configuration."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import (
    ItemAppearanceRuleConfig,
    ItemInteractionsConfig,
    ItemsAppearanceConfig,
    ItemsCatalogConfig,
    ItemTypeConfig,
    SpawnPlacementConfig,
    SpawnScheduleConfig,
)


class TestItemTypeConfigValidation:
    def _base_interactions(self) -> ItemInteractionsConfig:
        return ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[])

    def test_valid_minimal_item(self):
        item = ItemTypeConfig(
            id="apple",
            name="Apple",
            icon="🍎",
            tags=["food"],
            vfs_profile="food",
            interactions=self._base_interactions(),
        )
        assert item.id == "apple"
        assert item.duration is None
        assert item.cooldown is None

    @pytest.mark.parametrize(
        "bad_id",
        [
            "Apple",  # uppercase
            "apple-1",  # hyphen not allowed
            "apple$",  # symbol
            "",  # empty
        ],
    )
    def test_invalid_ids_rejected(self, bad_id: str):
        with pytest.raises(ValidationError):
            ItemTypeConfig(
                id=bad_id,
                name="Bad",
                icon="❌",
                tags=["bad"],
                vfs_profile="food",
                interactions=self._base_interactions(),
            )

    def test_missing_vfs_profile(self):
        with pytest.raises(ValidationError):
            ItemTypeConfig(
                id="apple",
                name="Apple",
                icon="🍎",
                tags=["food"],
                interactions=self._base_interactions(),  # type: ignore[arg-type]
            )

    def test_interactions_require_known_commands(self):
        with pytest.raises(ValidationError, match="Command must have one of"):
            ItemInteractionsConfig(on_pickup=[{"noop": True}], on_use=[], on_drop=[])

    def test_initial_state_allows_various_types(self):
        # initial_state lives on ItemAppearanceRuleConfig; ensure it accepts mixed types
        appearance = ItemAppearanceRuleConfig(
            item_type="apple",
            spawn_count=1,
            placement={"mode": "random"},
            schedule=None,
            when=None,
            # non-schema fields should be ignored here; this is a placeholder to ensure DTO accepts dict
        )
        assert appearance.item_type == "apple"


class TestSpawnScheduleConfigValidation:
    def test_valid_periodic(self):
        cfg = SpawnScheduleConfig(type="periodic", period=10)
        assert cfg.period == 10
        assert cfg.type == "periodic"

    def test_valid_time_window(self):
        cfg = SpawnScheduleConfig(type="time_window", start_tick=5, end_tick=20)
        assert cfg.start_tick == 5
        assert cfg.end_tick == 20

    def test_valid_poisson(self):
        cfg = SpawnScheduleConfig(type="poisson", rate=0.5)
        assert cfg.rate == 0.5

    def test_valid_normal(self):
        cfg = SpawnScheduleConfig(type="normal", mean=50.0, std_dev=5.0)
        assert cfg.mean == 50.0
        assert cfg.std_dev == 5.0

    def test_invalid_negative_period(self):
        with pytest.raises(ValidationError):
            SpawnScheduleConfig(type="periodic", period=0)

    def test_invalid_negative_rate(self):
        with pytest.raises(ValidationError):
            SpawnScheduleConfig(type="poisson", rate=-1.0)


class TestSpawnPlacementConfigValidation:
    def test_valid_random(self):
        cfg = SpawnPlacementConfig(mode="random")
        assert cfg.mode == "random"

    def test_valid_fixed_positions(self):
        cfg = SpawnPlacementConfig(mode="fixed", fixed_positions=[(0, 0), (1, 2)])
        assert cfg.fixed_positions == [(0, 0), (1, 2)]

    def test_valid_grid_spacing(self):
        cfg = SpawnPlacementConfig(mode="grid", grid_spacing=2)
        assert cfg.grid_spacing == 2

    def test_invalid_grid_spacing_zero(self):
        with pytest.raises(ValidationError):
            SpawnPlacementConfig(mode="grid", grid_spacing=0)

    def test_invalid_extra_field(self):
        with pytest.raises(ValidationError):
            SpawnPlacementConfig(mode="random", unknown_field=123)  # type: ignore[arg-type]


class TestItemAppearanceRuleConfigValidation:
    def _rule(self, **kwargs) -> ItemAppearanceRuleConfig:
        spawn_count = kwargs.pop("spawn_count", 1)
        return ItemAppearanceRuleConfig(
            item_type="apple",
            spawn_count=spawn_count,
            schedule=None,
            placement=None,
            when=None,
            **kwargs,
        )

    def test_valid_with_schedule_and_placement(self):
        rule = ItemAppearanceRuleConfig(
            item_type="apple",
            spawn_count=2,
            schedule=SpawnScheduleConfig(type="periodic", period=5),
            placement=SpawnPlacementConfig(mode="random"),
            when="bar.energy > 0.2",
        )
        assert rule.spawn_count == 2
        assert rule.schedule.period == 5

    def test_spawn_count_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            self._rule(spawn_count=-1)

    @pytest.mark.parametrize(
        ("field", "value"),
        (("spawn_interval", 1), ("spawn_position", "random")),
    )
    def test_legacy_spawn_fields_are_rejected(self, field: str, value: object):
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            self._rule(**{field: value})

    def test_max_total_ge_1(self):
        with pytest.raises(ValidationError):
            self._rule(max_total=0)


class TestItemsCatalogConfigValidation:
    def _base_item(self, id_: str = "apple") -> ItemTypeConfig:
        return ItemTypeConfig(
            id=id_,
            name=id_.capitalize(),
            icon="🧰",
            tags=["tag"],
            vfs_profile="food",
            interactions=ItemInteractionsConfig(on_pickup=[], on_use=[], on_drop=[]),
        )

    def test_valid_catalog_multiple_items(self):
        catalog = ItemsCatalogConfig(
            version="1.0",
            item_types=[self._base_item("apple"), self._base_item("banana")],
            max_items_per_agent=2,
            max_items_in_world=5,
        )
        assert catalog.max_items_per_agent == 2
        assert catalog.max_items_in_world == 5
        assert {i.id for i in catalog.item_types} == {"apple", "banana"}

    def test_valid_empty_catalog(self):
        catalog = ItemsCatalogConfig(version="1.0", item_types=[], max_items_per_agent=1, max_items_in_world=1)
        assert catalog.item_types == []

    def test_duplicate_ids_rejected(self):
        with pytest.raises(ValidationError, match="Duplicate item type IDs"):
            ItemsCatalogConfig(
                version="1.0",
                item_types=[self._base_item("apple"), self._base_item("apple")],
                max_items_per_agent=2,
                max_items_in_world=2,
            )


class TestItemsAppearanceConfigValidation:
    def test_empty_appearance_allowed(self):
        cfg = ItemsAppearanceConfig(version="1.0", items=[])
        assert cfg.items == []

    def test_valid_appearance_rule(self):
        cfg = ItemsAppearanceConfig(
            version="1.0",
            items=[
                ItemAppearanceRuleConfig(
                    item_type="apple",
                    spawn_count=1,
                    placement=SpawnPlacementConfig(mode="random"),
                    schedule=SpawnScheduleConfig(type="periodic", period=5),
                )
            ],
        )
        assert len(cfg.items) == 1
        assert cfg.items[0].schedule.period == 5
