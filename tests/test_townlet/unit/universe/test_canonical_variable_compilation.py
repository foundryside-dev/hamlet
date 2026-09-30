"""Canonical variable declarations compile to concrete runtime and observation products."""

from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _declare(experiment_dir: Path, declarations: list[dict]) -> None:
    payload = {
        "variables": {
            "version": "1.0",
            "evaluation_mode": "mark_and_sweep",
            "debug_logging": False,
            "extents": {},
            "item_profiles": ["default_item"],
            "declarations": declarations,
        }
    }
    (experiment_dir / "variables.yaml").write_text(yaml.safe_dump(payload))


def _variable(identifier: str, scope: str, lifetime: str, dtype: str, **fields) -> dict:
    return {
        "id": identifier,
        "scope": scope,
        "type": dtype,
        "lifetime": lifetime,
        "semantic_type": "custom",
        "exposed_to": [],
        **fields,
    }


def test_compiler_lowers_authored_global_state_to_internal_expression_product(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _declare(experiment_dir, [_variable("day_count", "global", "persistent", "scalar", initial_value=0)])

    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is not None
    variables = compiled.compiled_vfs_profiles.global_profile.variables
    assert len(variables) == 1
    assert variables[0].name == "day_count"
    assert variables[0].type == "float"
    assert variables[0].lifetime == "persistent"


def test_compiler_emits_registry_variables_from_the_same_canonical_roster(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _declare(
        experiment_dir,
        [
            _variable("day_count", "global", "persistent", "scalar", initial_value=0),
            _variable("motivation", "agent", "episode", "scalar", initial_value=0.5),
        ],
    )

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


def test_explicit_empty_catalog_compiles_without_authored_registry_state(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _declare(experiment_dir, [])
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    assert compiled.compiled_vfs_profiles is not None
    assert compiled.compiled_vfs_profiles.global_profile is None
    assert compiled.compiled_vfs_profiles.agent_profile is None
    assert [var.id for var in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables] == ["tick"]


def test_missing_canonical_catalog_refuses_instead_of_inserting_empty_state(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    (experiment_dir / "variables.yaml").unlink()
    with pytest.raises(CompilationError, match="variables"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)


def test_exposed_expression_keeps_its_declared_reset_value_and_identity(tmp_path: Path):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    phase = _variable(
        "phase",
        "global",
        "persistent",
        "scalar",
        semantic_type="temporal",
        expression="tick",
        exposed_to=["agent"],
        normalization={"kind": "cyclical_sin_cos", "period": 24},
    )
    _declare(experiment_dir, [phase])
    with pytest.raises(CompilationError, match=r"phase.*initial_value"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)

    phase["initial_value"] = 0.0
    _declare(experiment_dir, [phase])
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    spec = compiled.get_level(PRIMARY_LEVEL_NAME).token_spec
    assert [binding.filler_ref for binding in spec.get_type("variable_element").slot_bindings] == ["phase"]
    declared = next(var for var in compiled.get_level(PRIMARY_LEVEL_NAME).vfs_variables if var.id == "phase")
    assert declared.default == 0.0
    assert declared.semantic_type == "temporal"
    assert declared.exposed_to == ["agent"]


@pytest.mark.parametrize(
    ("mode", "shape", "expected_default"),
    [
        ("zeros", [2, 3], [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]),
        ("ones", [2, 3], [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]),
        ("eye", [2, 2], [[1.0, 0.0], [0.0, 1.0]]),
    ],
)
def test_exposed_deterministic_tensor_lowers_to_one_literal_default(tmp_path: Path, mode: str, shape: list[int], expected_default):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _declare(
        experiment_dir,
        [
            _variable(
                "tensor",
                "agent",
                "episode",
                "tensor2d",
                shape=shape,
                initial_value_mode=mode,
                exposed_to=["agent"],
                normalization={"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True},
            )
        ],
    )
    compiled = UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
    for universe in [compiled, CompiledUniverse.from_dict(compiled.to_dict())]:
        tensor = next(variable for variable in universe.get_level(PRIMARY_LEVEL_NAME).vfs_variables if variable.id == "tensor")
        assert tensor.default == expected_default
        assert tensor.initial_value_mode is None
        assert tensor.initial_value_params is None
        env = universe.create_environment(num_agents=2, level_name=PRIMARY_LEVEL_NAME, device="cpu")
        env.reset()
        expected = torch.tensor(expected_default).unsqueeze(0).expand(2, *shape)
        assert torch.equal(env.vfs_registry.get("tensor", reader="engine"), expected)


@pytest.mark.parametrize("mode,params", [("random_normal", {"mean": 0.0, "std": 1.0}), ("random_uniform", {"low": 0.0, "high": 1.0})])
def test_exposed_random_tensor_refuses_before_runtime_allocation(tmp_path: Path, mode: str, params: dict):
    experiment_dir = prepare_config_dir(tmp_path, name="experiment")
    _declare(
        experiment_dir,
        [
            _variable(
                "random_tensor",
                "agent",
                "episode",
                "tensor2d",
                shape=[2, 2],
                initial_value_mode=mode,
                initial_value_params=params,
                exposed_to=["agent"],
                normalization={"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True},
            )
        ],
    )
    with pytest.raises(CompilationError, match=r"random_tensor.*random initialization.*exposed"):
        UniverseCompiler().compile(experiment_dir, primary_level=PRIMARY_LEVEL_NAME, use_cache=False)
