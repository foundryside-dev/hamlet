"""V7 (review-2026-10-24 F8, probe2 A `expr_agent_reads_global`): agent expressions read globals.

The runtime evaluates the global profile before the agent profile and hands the agent
profile the registry state, so a global is an input of an agent expression by bare name.
The reverse direction is scope widening and refuses at compile.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet.helpers.config_builder import copy_config_pack
from townlet.config.variables_config import VariablesConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.vfs import VFSCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.evaluator import VFSEvaluator

PACK = Path("configs/static_epistemic_access")
LEVEL = "L0_simple"


def _declaration(identifier: str, *, scope: str, expression: str | None = None, writable: bool = True, **extra) -> dict:
    payload = {
        "id": identifier,
        "scope": scope,
        "type": extra.pop("type", "scalar"),
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"] if writable else [],
        "exposed_to": [],
        "initial_value": extra.pop("initial_value", 0.0),
        **extra,
    }
    if expression is not None:
        payload["expression"] = expression
    return payload


def _pack_with(tmp_path: Path, declarations: list[dict]) -> Path:
    pack = copy_config_pack(PACK, tmp_path)
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"].extend(declarations)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return pack


def _env(pack: Path, num_agents: int = 2):
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    env.reset()
    return universe, env


def _advance(env) -> None:
    ids = env.universe.get_level(LEVEL).runtime_action_space.action_ids
    env.step(torch.full((env.num_agents,), ids["ADVANCE"], dtype=torch.long))


def test_agent_expression_compiles_against_a_global_and_tracks_engine_writes(tmp_path: Path):
    """probe2 A `expr_agent_reads_global`, plus the tracking half over an engine-writable global."""
    pack = _pack_with(
        tmp_path,
        [
            _declaration("scale", scope="global", initial_value=0.5),
            _declaration("scaled", scope="agent", expression="public_state * scale"),
            _declaration("scaled_immutable", scope="agent", expression="public_state * immutable_scale"),
        ],
    )
    universe, env = _env(pack)
    assert {"scaled", "scaled_immutable"} <= universe.vfs_evaluation_marks["agent"]

    _advance(env)  # public_state 0 -> 1 per agent
    assert torch.equal(env.vfs_registry.get("scaled", reader="engine"), torch.tensor([0.5, 0.5]))
    assert torch.equal(env.vfs_registry.get("scaled_immutable", reader="engine"), torch.tensor([0.5, 0.5]))

    env.vfs_registry.set_engine_value("scale", torch.tensor([2.0, 3.0]))  # one value per world (S1)
    _advance(env)  # public_state 1 -> 2 per agent, each read against its own world's global
    assert torch.equal(env.vfs_registry.get("scaled", reader="engine"), torch.tensor([4.0, 6.0]))
    assert torch.equal(env.vfs_registry.get("scaled_immutable", reader="engine"), torch.tensor([1.0, 1.0]))


def test_global_expression_reading_an_agent_variable_refuses_at_compile(tmp_path: Path):
    """probe2 A `expr_global_reads_agent`: scope widening refuses by name, not as 'not found'."""
    pack = _pack_with(tmp_path, [_declaration("gb", scope="global", expression="public_state * 2.0")])
    with pytest.raises(
        CompilationError, match=r"'gb' is global-scope but its expression reads agent-scope variable\(s\) \['public_state'\]"
    ):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_agent_expression_over_a_global_expression_reads_the_same_tick_value(tmp_path: Path):
    """The motivating case: `is_night: day_phase > 0.5` where the clock is itself a global expression."""
    pack = _pack_with(
        tmp_path,
        [
            _declaration("clock", scope="global", expression="tick * 1.0"),
            _declaration("clock_seen", scope="agent", expression="clock + 0.0 * public_state"),
        ],
    )
    _, env = _env(pack)
    for _ in range(3):
        _advance(env)
        clock = env.vfs_registry.get("clock", reader="engine")
        assert torch.equal(env.vfs_registry.get("clock_seen", reader="engine"), clock.expand(env.num_agents))


def test_evaluator_feeds_global_outputs_to_the_agent_profile_in_order():
    """The evaluator needs no change: globals ride in `vfs_state`, so evaluating the global
    profile first and handing its outputs on makes the agent profile read this tick's value."""
    config = VariablesConfig(
        version="1.0",
        item_profiles=[],
        declarations=[
            _declaration("clock", scope="global", expression="tick * 1.0"),
            _declaration("is_night", scope="agent", type="bool", initial_value=False, expression="clock > 0.5 and bar.energy >= 0.0"),
        ],
    )
    compiler = VFSCompiler()
    profiles = compiler.compile_profiles(config, {"energy": "float"})
    marks = compiler.derive_evaluation_marks(config)
    assert marks == {"global": {"clock"}, "agent": {"is_night"}}
    assert profiles.global_profile is not None and profiles.agent_profile is not None

    evaluator = VFSEvaluator(history_spec=None)
    bars = {"energy": torch.tensor([1.0, 1.0])}
    for tick, expected in ((0.0, False), (1.0, True)):
        state = {"tick": torch.tensor(tick), "clock": torch.tensor(-1.0), "is_night": torch.tensor([False, False])}
        state.update(evaluator.evaluate_global_profile(profiles.global_profile, bars, state, marks=marks["global"]))
        assert state["clock"].item() == tick
        agent_values = evaluator.evaluate_global_profile(profiles.agent_profile, bars, state, marks=marks["agent"])
        assert torch.equal(agent_values["is_night"], torch.tensor([expected, expected]))
