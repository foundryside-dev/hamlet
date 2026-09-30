"""Canonical item declarations compile to persistent internal item products."""

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler


def _item_variable(profile: str, identifier: str, initial: float) -> dict:
    return {
        "id": identifier,
        "scope": "item",
        "profile": profile,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": initial,
    }


def _write_variables(pack: Path, profiles: list[str], declarations: list[dict]) -> None:
    (pack / "variables.yaml").write_text(
        yaml.safe_dump(
            {
                "variables": {
                    "version": "1.0",
                    "evaluation_mode": "mark_and_sweep",
                    "debug_logging": False,
                    "extents": {},
                    "item_profiles": profiles,
                    "declarations": declarations,
                }
            },
            sort_keys=False,
        )
    )


def _item(identifier: str, profile: str) -> dict:
    return {
        "id": identifier,
        "name": identifier,
        "icon": "item",
        "tags": ["test"],
        "vfs_profile": profile,
        "duration": None,
        "cooldown": None,
        "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
    }


def _write_items(pack: Path, items: list[dict]) -> None:
    (pack / "items.yaml").write_text(
        yaml.safe_dump({"items": {"version": "1.0", "max_items_per_agent": 3, "max_items_in_world": 10, "item_types": items}})
    )


@pytest.mark.parametrize("cached", [False, True])
def test_compiler_compiles_item_profiles(tmp_path: Path, cached: bool) -> None:
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _write_variables(
        experiment_dir,
        ["food_stats", "weapon_stats"],
        [
            _item_variable("food_stats", "calories", 100.0),
            _item_variable("food_stats", "freshness", 1.0),
            _item_variable("weapon_stats", "damage", 50.0),
            _item_variable("weapon_stats", "durability", 1.0),
        ],
    )
    _write_items(experiment_dir, [_item("apple", "food_stats")])
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    if cached:
        artifact = tmp_path / "world.msgpack"
        compiled.save_to_cache(artifact)
        compiled = CompiledUniverse.load_from_cache(artifact)
    assert compiled.compiled_vfs_profiles is not None
    profiles = compiled.compiled_vfs_profiles.item_profiles
    assert set(profiles) == {"food_stats", "weapon_stats"}
    assert [(var.name, var.initial_value) for var in profiles["food_stats"].variables] == [("calories", 100.0), ("freshness", 1.0)]
    assert [(var.name, var.initial_value) for var in profiles["weapon_stats"].variables] == [("damage", 50.0), ("durability", 1.0)]
    assert all(var.lifetime == "episode" and var.semantic_type == "custom" for profile in profiles.values() for var in profile.variables)


def test_compiler_rejects_unknown_item_vfs_profile(tmp_path: Path) -> None:
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _write_variables(experiment_dir, ["food_stats"], [_item_variable("food_stats", "calories", 100.0)])
    _write_items(experiment_dir, [_item("apple", "food_stats"), _item("ghost_item", "missing_profile")])
    with pytest.raises(ValueError, match="missing_profile"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_compiler_handles_empty_item_profile_inventory(tmp_path: Path) -> None:
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _write_variables(
        experiment_dir,
        [],
        [
            {
                "id": "day_count",
                "scope": "global",
                "type": "scalar",
                "lifetime": "persistent",
                "semantic_type": "custom",
                "exposed_to": [],
                "initial_value": 0.0,
            }
        ],
    )
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles == {}
