"""Tests for item profile compilation in UniverseCompiler."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_item_profiles(tmp_path: Path):
    """UniverseCompiler should compile item_profiles from vfs_profiles.yaml."""
    # Setup: Create config with item profiles
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    vfs_profiles = {
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
        ]
    }

    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

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


def test_compiler_handles_missing_item_profiles(tmp_path: Path):
    """UniverseCompiler should handle configs without item_profiles."""
    # Setup: Config without item_profiles
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Create vfs_profiles.yaml without item_profiles
    vfs_profiles = {"global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]}}

    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    # Verify: No error, item_profiles is empty dict
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.item_profiles == {}
