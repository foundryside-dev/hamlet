"""An authored ``switch`` with case and default bodies compiles and runs; a bad nested command cites its own line.

``CommandConfig.cases`` used to be ``list[dict]``: the parser handed each raw ``do`` mapping to
``parse_command`` and any non-empty case body died with ``AttributeError: 'MarkedMapping' object
has no attribute 'modify'`` at stage 6, after static write authorization had walked it fine. A
case is now a typed ``SwitchCaseConfig`` (``when``, ``do``), so parsing, static authorization and
pipeline compilation walk one grammar and the ``cases[k].do[m]`` / ``default[i]`` citations reach YAML.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
from pydantic import ValidationError

from tests.test_townlet.unit.effects.test_bare_vfs_write import LEVEL, _effect, _env, _pack
from townlet.config.effects_config import CommandConfig, SwitchCaseConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

SWITCH = {
    "switch": "public_state",
    "cases": [{"when": "0.0", "do": [{"modify": "public_state", "value": "public_state + 1.0"}]}],
    "default": [{"modify": "public_state", "value": "public_state + 10.0"}],
}
BAD_IN_CASE = {
    "switch": "public_state",
    "cases": [{"when": "0.0", "do": [{"modify": "public_state", "value": "0.0"}, {"modify": "nope", "value": "1.0"}]}],
    "default": [],
}
BAD_IN_DEFAULT = {
    "switch": "public_state",
    "cases": [{"when": "0.0", "do": []}],
    "default": [{"modify": "public_state", "value": "0.0"}, {"modify": "nope", "value": "1.0"}],
}


def _public_state(env) -> list[float]:
    return env.vfs_registry.get("public_state", reader="engine").tolist()


def _line_of(path: Path, needle: str) -> int:
    return next(number for number, text in enumerate(path.read_text().splitlines(), 1) if needle in text)


def test_switch_case_is_a_typed_node() -> None:
    command = CommandConfig.model_validate(SWITCH)
    (case,) = command.cases
    assert isinstance(case, SwitchCaseConfig)
    assert case.when == "0.0" and case.do[0].modify == "public_state"
    assert CommandConfig.model_validate(command.model_dump(by_alias=True)) == command


@pytest.mark.parametrize(
    ("case", "match"),
    [
        ({"do": []}, "when"),
        ({"when": "0.0"}, "do"),
        ({"when": "0.0", "do": [], "then": []}, "Extra inputs are not permitted"),
        ({"when": "0.0", "do": [{"modify": "public_state"}]}, r"modify command requires \['value'\]"),
    ],
)
def test_switch_case_refuses_a_malformed_body_at_the_dto(case: dict, match: str) -> None:
    with pytest.raises(ValidationError, match=match):
        CommandConfig.model_validate({"switch": "public_state", "cases": [case], "default": []})


def test_switch_bodies_run_in_an_interaction(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=[SWITCH]), num_agents=2)
    env.step(torch.full((2,), env.action_ids["INTERACT"]))
    assert _public_state(env) == [1.0, 1.0]  # case `0.0`
    env.step(torch.full((2,), env.action_ids["INTERACT"]))
    assert _public_state(env) == [11.0, 11.0]  # default


def test_switch_bodies_run_in_an_effect(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, effects=[_effect("agent", [SWITCH])]), num_agents=2)
    bars = {name: env.meters[:, index] for name, index in env.meter_name_to_index.items()}
    env.effect_manager.spawn_effect(
        "agent_probe", 0, 1.0, env.global_tick, bars=bars, vfs_registry=env.vfs_registry, item_manager=env.item_manager, world=0
    )
    env.step(torch.full((2,), env.action_ids["WAIT"]))
    assert _public_state(env) == [1.0, 0.0]
    env.step(torch.full((2,), env.action_ids["WAIT"]))
    assert _public_state(env) == [11.0, 0.0]


@pytest.mark.parametrize(("command", "path"), [(BAD_IN_CASE, "cases[0].do[1]"), (BAD_IN_DEFAULT, "default[1]")])
def test_a_bad_command_in_a_switch_body_of_an_interaction_cites_its_own_line(tmp_path: Path, command: dict, path: str) -> None:
    pack = _pack(tmp_path, sleep_on_start=[command])
    affordances = pack / "levels" / LEVEL / "affordances.yaml"
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    (issue,) = refusal.value.issues
    assert issue.code == "EFFECT-COMPILE"
    assert f"SLEEP:on_start[0].{path}: MODIFY target 'nope'" in issue.message
    assert issue.location == f"{affordances}:{_line_of(affordances, 'modify: nope')}"
    assert _line_of(affordances, "modify: nope") != _line_of(affordances, "- switch:")


@pytest.mark.parametrize(("command", "path"), [(BAD_IN_CASE, "cases[0].do[1]"), (BAD_IN_DEFAULT, "default[1]")])
def test_a_bad_command_in_a_switch_body_of_an_effect_cites_its_own_line(tmp_path: Path, command: dict, path: str) -> None:
    pack = _pack(tmp_path, effects=[_effect("agent", [command])])
    effects = pack / "effects.yaml"
    with pytest.raises(CompilationError) as refusal:
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    (issue,) = refusal.value.issues
    assert issue.code == "EFFECT-COMPILE"
    assert f"on_tick[0].{path}: MODIFY target 'nope'" in issue.message
    assert issue.location == f"{effects}:{_line_of(effects, 'modify: nope')}"
    assert _line_of(effects, "modify: nope") != _line_of(effects, "- switch:")
