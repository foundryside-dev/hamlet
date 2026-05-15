"""Tests for VFS profile compilation in UniverseCompiler."""

from pathlib import Path

import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def test_compiler_loads_vfs_profiles_if_present(tmp_path: Path):
    """UniverseCompiler should load vfs_profiles.yaml from experiment root if present."""
    # Setup: Create minimal config pack using the helper
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Create vfs_profiles.yaml with a simple global variable
    profiles = {
        "version": "1.0",
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    # Exercise: Compile universe
    compiler = UniverseCompiler()
    # This will fail until we implement profile loading
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: CompiledUniverse has compiled profiles
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is not None
    assert len(compiled.compiled_vfs_profiles.global_profile.variables) == 1
    assert compiled.compiled_vfs_profiles.global_profile.variables[0].name == "day_count"


def test_compiler_emits_runtime_vfs_variables_from_profiles(tmp_path: Path):
    """CompiledUniverse should carry registry-ready global and agent VFS variables."""
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "global_profile": {"variables": [{"name": "day_count", "type": "int", "initial_value": 0}]},
        "agent_profile": {"variables": [{"name": "motivation", "type": "float", "initial_value": 0.5}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    variables_by_id = {var.id: var for var in compiled.vfs_variables}
    assert variables_by_id["day_count"].scope == "global"
    assert variables_by_id["day_count"].type == "scalar"
    assert variables_by_id["day_count"].default == 0
    assert variables_by_id["day_count"].lifetime == "persistent"
    assert variables_by_id["motivation"].scope == "agent"
    assert variables_by_id["motivation"].type == "scalar"
    assert variables_by_id["motivation"].default == 0.5
    assert variables_by_id["motivation"].lifetime == "episode"


def test_compiler_allows_missing_vfs_profiles(tmp_path: Path):
    """UniverseCompiler should allow missing vfs_profiles.yaml (not all configs use VFS)."""
    # Setup: Create minimal config pack WITHOUT vfs_profiles.yaml
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")

    # Exercise: Compile universe (no vfs_profiles.yaml created)
    compiler = UniverseCompiler()
    # This should succeed with empty/None profiles
    compiled = compiler.compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    # Verify: No error, profiles are None or empty
    assert compiled.compiled_vfs_profiles is None or compiled.compiled_vfs_profiles.global_profile is None
