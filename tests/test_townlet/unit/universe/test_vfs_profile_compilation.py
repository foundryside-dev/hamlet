"""Tests for VFS profile compilation in UniverseCompiler."""

from pathlib import Path

import pytest
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
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0}]},
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
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {"variables": [{"semantic_type": "custom", "name": "day_count", "type": "int", "initial_value": 0}]},
        "agent_profile": {"variables": [{"semantic_type": "custom", "name": "motivation", "type": "float", "initial_value": 0.5}]},
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    variables_by_id = {var.id: var for var in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables}
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


def test_compiler_refuses_exposed_expression_before_runtime_identity_is_erased(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    # The model_config fixture used by prepare_config_dir declares deficit_energy /
    # time_since_last_eat under environment.yaml, and declaration there IS exposure
    # (observation.py:67) — unrelated to this test's expression/initial_value question.
    # Clear it so the slot_bindings assertion below reflects only what this test declares.
    env_path = experiment_dir / "environment.yaml"
    env_doc = yaml.safe_load(env_path.read_text())
    env_doc["environment"]["variables"] = []
    env_path.write_text(yaml.safe_dump(env_doc))
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "global_profile": {
            "variables": [
                {
                    "semantic_type": "temporal",
                    "name": "phase",
                    "type": "float",
                    "expression": "tick",
                    "exposed_to": ["agent"],
                    "normalization": {"kind": "cyclical_sin_cos", "period": 24},
                }
            ]
        },
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profiles))

    with pytest.raises(ValueError, match=r"phase.*expression.*without a declared initial_value"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    profiles["global_profile"]["variables"][0]["initial_value"] = 0.0
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profiles))
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    spec = compiled.get_level(PRIMARY_LEVEL_NAME).token_spec
    assert [b.filler_ref for b in spec.get_type("variable_element").slot_bindings] == ["phase"]
    declared = {v.id: v for v in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables}["phase"]
    assert declared.default == 0.0


@pytest.mark.parametrize(
    ("mode", "shape", "expected_default"),
    (
        ("zeros", [2, 3], [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
        ("ones", [2, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]),
        ("eye", [2, 2], [[1.0, 0.0], [0.0, 1.0]]),
    ),
)
def test_compiler_lowers_exposed_deterministic_tensor_mode_to_only_literal_default(
    tmp_path: Path,
    mode: str,
    shape: list[int],
    expected_default: list[list[float]],
):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "agent_profile": {
            "variables": [
                {
                    "semantic_type": "custom",
                    "name": "tensor",
                    "type": "tensor2d",
                    "shape": shape,
                    "initial_value_mode": mode,
                    "exposed_to": ["agent"],
                    "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True},
                }
            ]
        },
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profiles))

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    tensor = next(variable for variable in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables if variable.id == "tensor")

    assert tensor.default == expected_default
    assert tensor.initial_value_mode is None
    assert tensor.initial_value_params is None


@pytest.mark.parametrize("mode", ("random_normal", "random_uniform"))
def test_compiler_refuses_exposed_random_tensor_mode(tmp_path: Path, mode: str):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    profiles = {
        "version": "1.0",
        "evaluation_mode": "mark_and_sweep",
        "debug_logging": False,
        "agent_profile": {
            "variables": [
                {
                    "semantic_type": "custom",
                    "name": "random_tensor",
                    "type": "tensor2d",
                    "shape": [2, 2],
                    "initial_value_mode": mode,
                    "exposed_to": ["agent"],
                    "normalization": {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True},
                }
            ]
        },
    }
    (experiment_dir / "vfs_profiles.yaml").write_text(yaml.safe_dump(profiles))

    with pytest.raises(ValueError, match=rf"random_tensor.*{mode}.*cannot be exposed"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
