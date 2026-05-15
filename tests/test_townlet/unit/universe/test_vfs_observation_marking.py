"""Tests for VFS observation marking in UniverseCompiler."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_marks_vfs_variables_used_in_observations(tmp_path: Path):
    """Compiler should mark which VFS variables appear in observation fields."""
    # Setup: Create config with VFS profiles and observations
    config_dir = prepare_config_dir(tmp_path, name="test_vfs_marks")

    # Add VFS profiles with global variables
    vfs_profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {
            "variables": [
                {"name": "day_count", "type": "int", "initial_value": 0},
                {"name": "unused_var", "type": "int", "initial_value": 0},
            ]
        },
    }
    (config_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Create variables_reference with observation markings
    variables_ref = {
        "version": "1.0",
        "variables": [
            {
                "id": "day_count",
                "scope": "global",
                "type": "scalar",
                "default": 0,
                "lifetime": "episode",
                "readable_by": ["agent"],
                "writable_by": ["engine"],
                "observable": True,  # This marks it for observation
            },
            {
                "id": "unused_var",
                "scope": "global",
                "type": "scalar",
                "default": 0,
                "lifetime": "episode",
                "readable_by": ["agent"],
                "writable_by": ["engine"],
                "observable": False,  # NOT in observations
            },
        ],
    }
    (config_dir / "variables_reference.yaml").write_text(yaml.dump(variables_ref))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: day_count is marked, unused_var is not
    assert compiled.vfs_observation_marks is not None
    assert "day_count" in compiled.vfs_observation_marks["global"]
    assert "unused_var" not in compiled.vfs_observation_marks["global"]


def test_compiler_marks_empty_when_no_vfs_observations(tmp_path: Path):
    """Compiler should handle configs without VFS observations."""
    # Setup: Config with NO VFS variables in observations
    config_dir = prepare_config_dir(tmp_path, name="test_no_vfs")

    # Add VFS profiles
    vfs_profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {
            "variables": [
                {"name": "some_var", "type": "int", "initial_value": 0},
            ]
        },
    }
    (config_dir / "vfs_profiles.yaml").write_text(yaml.dump(vfs_profiles))

    # Create variables_reference with NO observable variables
    variables_ref = {
        "version": "1.0",
        "variables": [
            {
                "id": "some_var",
                "scope": "global",
                "type": "scalar",
                "default": 0,
                "lifetime": "episode",
                "readable_by": ["agent"],
                "writable_by": ["engine"],
                "observable": False,  # NOT observable
            },
        ],
    }
    (config_dir / "variables_reference.yaml").write_text(yaml.dump(variables_ref))

    # Exercise
    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: marks are empty or None
    assert compiled.vfs_observation_marks is None or len(compiled.vfs_observation_marks.get("global", set())) == 0
