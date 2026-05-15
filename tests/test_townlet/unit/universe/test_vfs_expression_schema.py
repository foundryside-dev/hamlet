"""Tests for VFS expression schema in CompiledUniverse."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_generates_vfs_expression_schema(tmp_path: Path):
    """UniverseCompiler should generate type schema for runtime expression checking."""
    # Setup: Create minimal config pack using the helper
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Add vfs_profiles.yaml at experiment root with global variables
    vfs_profiles_yaml = experiment_dir / "vfs_profiles.yaml"
    vfs_profiles = {
        "version": "1.0",
        "global_profile": {
            "variables": [
                {
                    "name": "day_count",
                    "type": "int",
                    "initial_value": 0,
                    "description": "Number of days elapsed",
                },
                {
                    "name": "is_night",
                    "type": "bool",
                    "initial_value": False,
                    "description": "Whether it is currently night time",
                },
                {
                    "name": "ambient_temperature",
                    "type": "float",
                    "initial_value": 20.0,
                    "description": "Ambient temperature in celsius",
                },
            ],
        },
    }
    vfs_profiles_yaml.write_text(yaml.dump(vfs_profiles, sort_keys=False))

    # Exercise: Compile universe
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: Schema includes bars (from template) and VFS variables
    assert compiled.vfs_expression_schema is not None

    # Check bar paths (bars come from L0_0_minimal template)
    assert "bar.energy" in compiled.vfs_expression_schema
    assert compiled.vfs_expression_schema["bar.energy"] == "float"

    # Check VFS variable paths and types
    assert "vfs.day_count" in compiled.vfs_expression_schema
    assert "vfs.is_night" in compiled.vfs_expression_schema
    assert "vfs.ambient_temperature" in compiled.vfs_expression_schema

    assert compiled.vfs_expression_schema["vfs.day_count"] == "int"
    assert compiled.vfs_expression_schema["vfs.is_night"] == "bool"
    assert compiled.vfs_expression_schema["vfs.ambient_temperature"] == "float"


def test_vfs_expression_schema_without_vfs_profiles(tmp_path: Path):
    """VFS expression schema should work even without VFS profiles (bars only)."""
    # Setup: Create minimal config pack WITHOUT vfs_profiles.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Exercise: Compile universe (no vfs_profiles.yaml created)
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: Schema includes bars but no VFS variables
    assert compiled.vfs_expression_schema is not None
    assert "bar.energy" in compiled.vfs_expression_schema
    assert compiled.vfs_expression_schema["bar.energy"] == "float"

    # No VFS variables present
    assert not any(key.startswith("vfs.") for key in compiled.vfs_expression_schema.keys())
