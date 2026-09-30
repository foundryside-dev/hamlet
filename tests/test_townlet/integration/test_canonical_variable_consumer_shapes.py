"""Authored variable consumers honor actual evaluator and reward tensor shapes."""

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

LEVEL = "L0_simple"


def _pack(tmp_path: Path, declaration: dict) -> Path:
    pack = tmp_path / "world"
    shutil.copytree(Path("configs/simple"), pack)
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"] = [declaration]
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return pack


def _declaration(scope: str, variable_type: str, initial: float | bool, expression: str | None = None) -> dict:
    declaration = {
        "id": "signal",
        "scope": scope,
        "type": variable_type,
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
        "initial_value": initial,
    }
    if expression is not None:
        declaration["expression"] = expression
    return declaration


@pytest.mark.parametrize(
    ("scope", "variable_type", "expression", "expected"),
    [
        ("global", "scalar", "sum(2.0, 4.0)", 6.0),
        ("global", "scalar", "argmin(2.0, 4.0)", 0.0),
        ("global", "bool", "any(true, false)", True),
        ("agent", "scalar", "mean(bar.energy, bar.health)", 0.9925),
        ("agent", "scalar", "argmax(bar.energy, bar.health)", 1.0),
        ("agent", "bool", "all(bar.energy > 0.5, bar.health > 0.5)", True),
        ("agent", "scalar", "count_where(bar.energy > 0.5, bar.health > 0.5)", 2.0),
        ("agent", "bool", "threshold(0.5, bar.energy, 0.9)", False),
        ("agent", "scalar", "where(bar.energy > 0.5, 1.0, 0.0)", 1.0),
    ],
)
def test_expression_functions_produce_declared_state_shape(
    tmp_path: Path, scope: str, variable_type: str, expression: str, expected: float | bool
) -> None:
    initial = False if variable_type == "bool" else 0.0
    pack = _pack(tmp_path, _declaration(scope, variable_type, initial, expression))
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    wait = universe.get_level(LEVEL).runtime_action_space.action_ids["WAIT"]
    env.step(torch.full((2,), wait, dtype=torch.long))
    actual = env.vfs_registry.get("signal", reader="engine")
    assert actual.shape == (() if scope == "global" else (2,))
    assert torch.allclose(actual, torch.full_like(actual, expected))


@pytest.mark.parametrize(
    ("scope", "variable_type", "expression"),
    [
        ("global", "scalar", "bar.energy"),
        ("global", "scalar", "mean(bar.energy, bar.health)"),
        ("global", "scalar", "argmin(bar.energy, bar.health)"),
        ("agent", "scalar", "3.0"),
        ("agent", "scalar", "mean(bar.energy, 3.0)"),
        ("agent", "scalar", "argmax(bar.energy, 3.0)"),
        ("agent", "bool", "all(bar.energy > 0.5, true)"),
    ],
)
def test_incompatible_function_shapes_refuse_before_execution(tmp_path: Path, scope: str, variable_type: str, expression: str) -> None:
    initial = False if variable_type == "bool" else 0.0
    pack = _pack(tmp_path, _declaration(scope, variable_type, initial, expression))
    with pytest.raises(CompilationError, match="shape") as error:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert "variables.yaml:" in str(error.value)


@pytest.mark.parametrize("scope", ["global", "agent"])
@pytest.mark.parametrize("value", [False, True])
@pytest.mark.parametrize("consumer", ["modifier", "variable_bonus", "shaping"])
def test_boolean_state_has_numeric_reward_consumer_semantics(tmp_path: Path, scope: str, value: bool, consumer: str) -> None:
    pack = _pack(tmp_path, _declaration(scope, "bool", value))
    path = pack / "levels" / LEVEL / "drive.yaml"
    payload = yaml.safe_load(path.read_text())
    drive = payload["drive"]
    drive["intrinsic"]["base_weight"] = 0.0
    drive["intrinsic"]["apply_modifiers"] = []
    drive["shaping"] = []
    drive["modifiers"] = {}
    if consumer == "modifier":
        drive["extrinsic"] = {"type": "multiplicative", "base": 1.0, "bars": [], "apply_modifiers": ["signal_modifier"]}
        drive["modifiers"] = {
            "signal_modifier": {
                "variable": "signal",
                "ranges": [
                    {"name": "false", "min": 0.0, "max": 0.5, "multiplier": 0.25},
                    {"name": "true", "min": 0.5, "max": 1.0, "multiplier": 2.0},
                ],
            }
        }
        expected = 2.0 if value else 0.25
    else:
        drive["extrinsic"] = {
            "type": "vfs_variable",
            "base": 0.0,
            "bar_bonuses": [],
            "variable_bonuses": [{"variable": "signal", "weight": 0.5}] if consumer == "variable_bonus" else [],
            "apply_modifiers": [],
        }
        if consumer == "shaping":
            drive["shaping"] = [{"type": "vfs_variable", "variable": "signal", "weight": 0.5}]
        expected = 0.5 if value else 0.0
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    wait = universe.get_level(LEVEL).runtime_action_space.action_ids["WAIT"]
    _, rewards, _, info = env.step(torch.full((2,), wait, dtype=torch.long))
    assert rewards.shape == (2,)
    assert rewards.dtype == torch.float32
    assert torch.allclose(rewards, torch.full((2,), expected))
    component = "shaping" if consumer == "shaping" else "extrinsic"
    assert torch.allclose(info["reward_components"][component], rewards)
