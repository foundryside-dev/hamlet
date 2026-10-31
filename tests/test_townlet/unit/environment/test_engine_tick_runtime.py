"""Runtime tick: zeroed on reset, advanced once per step, engine-only."""

from __future__ import annotations

import pytest
import torch

from tests.test_townlet.helpers.config_builder import PRIMARY_LEVEL_NAME, prepare_config_dir
from townlet.universe.compiler import UniverseCompiler


def _make_env(tmp_path, num_agents=2):
    u = UniverseCompiler().compile(prepare_config_dir(tmp_path), primary_level=PRIMARY_LEVEL_NAME)
    env = u.create_environment(num_agents=num_agents, level_name=PRIMARY_LEVEL_NAME, device="cpu")
    env.reset()
    return env


def _tick_value(env) -> float:
    return float(env.vfs_registry.get("tick", reader="engine").reshape(-1)[0])


def test_tick_counts_steps_and_resets(tmp_path):
    env = _make_env(tmp_path)
    assert _tick_value(env) == 0.0
    for k in range(3):
        env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    # The registry tick advances with global_tick at one point in step(), after the
    # transition phases: the observation step() returns describes the instant the next
    # action is taken in, so the two agree whenever step() is not running.
    assert _tick_value(env) == float(env.global_tick) == 3.0
    env.reset()
    assert _tick_value(env) == 0.0


def test_tick_matches_value_seen_within_step(tmp_path, monkeypatch):
    """Every consumer of THIS step's action sees the same tick value.

    Capturing on the SECOND step discriminates: after one step the clock has advanced to
    1, so the action executor must see registry tick 1 alongside current_step
    (global_tick) 1. A clock advance that skipped the registry write, or wrote it before
    the transitions of the previous step committed, would leave the two apart.
    """
    env = _make_env(tmp_path)
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))

    seen: dict[str, float] = {}
    original_execute = env._action_executor._execute_actions

    def _record_and_execute(actions):
        seen["tick"] = _tick_value(env)
        seen["current_step"] = float(env.global_tick)
        return original_execute(actions)

    monkeypatch.setattr(env._action_executor, "_execute_actions", _record_and_execute)
    env.step(torch.zeros(env.num_agents, dtype=torch.long, device=env.device))
    assert seen["tick"] == seen["current_step"] == 1.0


def test_tick_is_engine_writable_only(tmp_path):
    env = _make_env(tmp_path)
    with pytest.raises(PermissionError):
        env.vfs_registry.set("tick", torch.tensor(99.0), writer="agent")
