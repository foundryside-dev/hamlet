"""Tests for Effects catalog compilation in UniverseCompiler."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_compiles_effects_catalog_per_level(tmp_path: Path):
    """UniverseCompiler should compile effects.yaml into catalog artifact."""
    # Setup: Create minimal config pack with effects.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="test_experiment")

    # Add VFS profiles with a global variable
    profiles = {
        "version": "1.0",
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Create effects.yaml at EXPERIMENT ROOT (not in level directory)
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
    (experiment_dir / "effects.yaml").write_text(yaml.dump(effects))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    # Verify: CompiledUniverse has compiled effect catalog
    assert compiled.compiled_effect_catalog is not None
    assert len(compiled.compiled_effect_catalog.effects) > 0
    assert "energy_regen" in compiled.compiled_effect_catalog.effects


def test_compiler_allows_missing_effects_yaml(tmp_path: Path):
    """UniverseCompiler should allow missing effects.yaml (optional)."""
    # Setup: Config pack with valid configs but missing effects.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="test_experiment")

    # Add VFS profiles with a global variable
    profiles = {
        "version": "1.0",
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Remove effects.yaml (prepare_config_dir copies it from skeleton)
    effects_yaml = experiment_dir / "effects.yaml"
    if effects_yaml.exists():
        effects_yaml.unlink()

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, use_cache=False)

    # Verify: compiled_effect_catalog should be None when file missing
    assert compiled.compiled_effect_catalog is None
