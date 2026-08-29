"""Runtime tick: written at the top of step, zeroed on reset, engine-only."""

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
    # The pinned write happens at the TOP of step(), before global_tick's end-of-step
    # increment — the same pre-increment value effects consume via
    # current_step=self.global_tick (vectorized_env.py step()). So after N step() calls
    # the registry cell holds the index of the step just executed (N-1), one behind the
    # post-increment step-count attribute. See test_tick_matches_value_seen_within_step
    # below for the property this write point actually guarantees.
    assert _tick_value(env) == float(env.global_tick - 1)
    env.reset()
    assert _tick_value(env) == 0.0


def test_tick_matches_value_seen_within_step(tmp_path, monkeypatch):
    """Pinned write point: every consumer of THIS step sees the same tick value.

    Fix round 1, Finding 2: a fresh reset() already writes tick=0, so capturing on the
    FIRST step() call doesn't discriminate — seen["tick"] would read 0 from reset's
    write and seen["current_step"] would read 0 (pre-increment global_tick) even if the
    step()-level write were deleted entirely or moved after action execution. Stepping
    once, unmonitored, first advances global_tick past 0; capturing on the SECOND step
    means only a write correctly placed at the top of step() (before the action
    executor consumes current_step=self.global_tick) can match — a deleted or
    misplaced write would leave the registry holding step 1's stale value (0) against
    step 2's current_step (1).
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
