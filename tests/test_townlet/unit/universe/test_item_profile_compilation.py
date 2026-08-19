"""Tests for item profile compilation in UniverseCompiler."""

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_item_profiles(tmp_path: Path):
    """UniverseCompiler should compile item_profiles from vfs_profiles.yaml."""
    # Setup: Create config with item profiles
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    vfs_profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "item_profiles": [
            {
                "profile_name": "food_stats",
                "variables": [
                    {"name": "calories", "type": "int", "initial_value": 100},
                    {"name": "freshness", "type": "float", "expression": "1.0"},
                ],
            },
            {
                "profile_name": "weapon_stats",
                "variables": [
                    {"name": "damage", "type": "int", "initial_value": 50},
                    {"name": "durability", "type": "float", "initial_value": 1.0},
                ],
            },
        ],
    }

    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Enable item system so item VFS dims are valid
    items_catalog = {
        "items": {
            "version": "1.0",
            "max_items_per_agent": 3,
            "max_items_in_world": 10,
            "item_types": [
                {
                    "id": "apple",
                    "name": "Apple",
                    "icon": "apple",
                    "tags": ["food"],
                    "vfs_profile": "food_stats",
                    "duration": None,
                    "cooldown": None,
                    "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
                }
            ],
        }
    }
    (experiment_dir / "items.yaml").write_text(yaml.dump(items_catalog))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: Item profiles are compiled
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles is not None
    assert "food_stats" in compiled.compiled_vfs_profiles.item_profiles
    assert "weapon_stats" in compiled.compiled_vfs_profiles.item_profiles

    # Verify: Profiles have correct structure
    food_profile = compiled.compiled_vfs_profiles.item_profiles["food_stats"]
    assert len(food_profile.variables) == 2
    assert food_profile.variables[0].name == "calories"
    assert food_profile.variables[1].name == "freshness"


def test_compiler_rejects_unknown_item_vfs_profile(tmp_path: Path):
    """Compiler should fail when an item references a missing vfs_profile."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    vfs_profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "item_profiles": [
            {
                "profile_name": "food_stats",
                "variables": [
                    {"name": "calories", "type": "int", "initial_value": 100},
                ],
            }
        ],
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    items_catalog = {
        "items": {
            "version": "1.0",
            "max_items_per_agent": 3,
            "max_items_in_world": 10,
            "item_types": [
                {
                    "id": "apple",
                    "name": "Apple",
                    "icon": "apple",
                    "tags": ["food"],
                    "vfs_profile": "food_stats",
                    "duration": None,
                    "cooldown": None,
                    "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
                },
                {
                    "id": "ghost_item",
                    "name": "Ghost",
                    "icon": "ghost",
                    "tags": ["spectral"],
                    "vfs_profile": "missing_profile",
                    "duration": None,
                    "cooldown": None,
                    "interactions": {"on_pickup": [], "on_use": [], "on_drop": []},
                },
            ],
        }
    }
    (experiment_dir / "items.yaml").write_text(yaml.dump(items_catalog))

    compiler = UniverseCompiler()
    with pytest.raises(ValueError):
        compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_compiler_handles_missing_item_profiles(tmp_path: Path):
    """UniverseCompiler should handle configs without item_profiles."""
    # Setup: Config without item_profiles
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Create vfs_profiles.yaml without item_profiles
    vfs_profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0}]},
    }

    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: No error, item_profiles is empty dict
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles == {}
