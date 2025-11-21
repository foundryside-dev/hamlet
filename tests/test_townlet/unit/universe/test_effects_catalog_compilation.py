"""Tests for Effects catalog compilation in UniverseCompiler."""

from pathlib import Path

import pytest
import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_effects_catalog_per_level(tmp_path: Path):
    """UniverseCompiler should compile effects.yaml into catalog artifact."""
    # Setup: Create minimal config pack with effects.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="test_experiment")

    # Add VFS profiles with a global variable
    profiles = {"global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]}}
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Get the primary level directory
    level_dir = experiment_dir / "levels" / "L0_test"

    # Create effects.yaml with a simple effect
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
            }
        ],
    }
    (level_dir / "effects.yaml").write_text(yaml.dump(effects))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    # Verify: CompiledUniverse has compiled effect catalog
    assert compiled.compiled_effect_catalog is not None
    assert len(compiled.compiled_effect_catalog.effects) > 0
    assert "energy_regen" in compiled.compiled_effect_catalog.effects


def test_compiler_fails_if_effects_yaml_missing(tmp_path: Path):
    """UniverseCompiler should fail if effects.yaml required but missing."""
    # Setup: Config pack with valid configs but missing level effects.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="test_experiment")

    # The skeleton already has valid affordances.yaml
    # Don't create effects.yaml - we want to test that it fails when missing

    # Exercise & Verify
    compiler = UniverseCompiler()
    with pytest.raises(FileNotFoundError, match="effects.yaml is required"):
        compiler.compile(experiment_dir, use_cache=False)
