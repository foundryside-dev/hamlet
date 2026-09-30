"""Tests for VFS expression schema in CompiledUniverse."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_generates_vfs_expression_schema(tmp_path: Path):
    """UniverseCompiler should generate type schema for runtime expression checking."""
    # Setup: Create minimal config pack using the helper
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Author global variables through the canonical pack declaration
    variables_yaml = experiment_dir / "variables.yaml"
    variables_document = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": [],
            "declarations": [
                {
                    "id": "day_count",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "persistent",
                    "semantic_type": "custom",
                    "exposed_to": [],
                    "initial_value": 0,
                    "description": "Number of days elapsed",
                },
                {
                    "id": "is_night",
                    "scope": "global",
                    "type": "bool",
                    "lifetime": "persistent",
                    "semantic_type": "custom",
                    "exposed_to": [],
                    "initial_value": False,
                    "description": "Whether it is currently night time",
                },
                {
                    "id": "ambient_temperature",
                    "scope": "global",
                    "type": "scalar",
                    "lifetime": "persistent",
                    "semantic_type": "custom",
                    "exposed_to": [],
                    "initial_value": 20.0,
                    "description": "Ambient temperature in celsius",
                },
            ],
        }
    }
    variables_yaml.write_text(yaml.dump(variables_document, sort_keys=False))

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

    assert compiled.vfs_expression_schema["vfs.day_count"] == "float"
    assert compiled.vfs_expression_schema["vfs.is_night"] == "bool"
    assert compiled.vfs_expression_schema["vfs.ambient_temperature"] == "float"


def test_vfs_expression_schema_with_empty_variable_roster(tmp_path: Path):
    """An explicitly empty variable roster yields the bar-only schema."""
    # Setup: Create a pack with an explicitly empty canonical roster
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    data = yaml.safe_load((experiment_dir / "variables.yaml").read_text())
    data["variables"]["declarations"] = []
    (experiment_dir / "variables.yaml").write_text(yaml.safe_dump(data))

    # Exercise: Compile the bar-only expression schema
    compiler = UniverseCompiler()
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: Schema includes bars but no VFS variables
    assert compiled.vfs_expression_schema is not None
    assert "bar.energy" in compiled.vfs_expression_schema
    assert compiled.vfs_expression_schema["bar.energy"] == "float"

    # No VFS variables present
    assert not any(key.startswith("vfs.") for key in compiled.vfs_expression_schema.keys())
