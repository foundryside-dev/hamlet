"""Fixtures for universe compiler tests."""

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


@pytest.fixture
def minimal_compiled_universe_with_profiles(tmp_path: Path):
    """Create a minimal CompiledUniverse with VFS profiles."""
    # Setup: Create minimal config pack with VFS profiles
    experiment_dir = prepare_config_dir(tmp_path, name="test_profiles")

    # Add VFS profiles with global variables
    profiles = {
        "global_profile": {
            "variables": [
                {"name": "day_count", "type": "int", "initial_value": 0},
                {"name": "total_earnings", "type": "float", "initial_value": 0.0},
            ]
        }
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Compile
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    return compiled


@pytest.fixture
def minimal_compiled_universe_with_effects(tmp_path: Path):
    """Create a minimal CompiledUniverse with effects catalog."""
    # Setup: Create minimal config pack with effects
    experiment_dir = prepare_config_dir(tmp_path, name="test_effects")

    # Add VFS profiles (required for effects)
    profiles = {"global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]}}
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Add effects.yaml
    effects = {
        "version": "1.0",
        "effect_definitions": [
            {
                "id": "energy_regen",
                "scope": "agent",
                "duration": 1,
                "intensity": 1.0,
                "reapply_policy": "stack",
                "observable": True,
                "on_spawn": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.2"}],
                "on_tick": [],
                "on_despawn": [],
            },
            {
                "id": "speed_boost",
                "scope": "agent",
                "duration": 5,
                "intensity": 2.0,
                "reapply_policy": "replace",
                "observable": True,
                "on_spawn": [],
                "on_tick": [],
                "on_despawn": [],
            },
        ],
    }
    (experiment_dir / "effects.yaml").write_text(yaml.dump(effects))

    # Compile
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    return compiled
