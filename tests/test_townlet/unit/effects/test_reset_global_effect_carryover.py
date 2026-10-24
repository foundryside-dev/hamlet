"""hamlet-d76684f549: a global effect spawned in episode N must not tick in episode N+1.

Recipe from ``review-2026-10-24/effects/repro_d766.py``: on ``trial002_money_log_gdp`` the WORK
interaction spawns the global ``business_cycle`` effect, whose ``on_tick`` rewrites
``bar.money``. Before ``EffectManager.reset()`` existed the instance survived ``env.reset()``
with its counters intact and pushed money from 1000 to ~2258 on the first WAIT of the next
episode.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.effects.manager import EffectManager
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path(__file__).resolve().parents[4] / "configs" / "trial002_money_log_gdp"
LEVEL = "L0_simple"
NUM_AGENTS = 2


@pytest.fixture(scope="module")
def universe():
    return UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)


def _env(universe) -> tuple[VectorizedHamletEnv, EffectManager]:
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=NUM_AGENTS, device="cpu")
    assert env.effect_manager is not None
    return env, env.effect_manager


def _work_then_wait(env: VectorizedHamletEnv) -> torch.Tensor:
    """Agent 0 interacts at WORK (spawning business_cycle); agent 1 waits."""
    env.positions[0] = env.affordances["WORK"]
    actions = torch.full((NUM_AGENTS,), env.action_dim - 1, dtype=torch.long)
    actions[0] = env.action_dim - 2
    return actions


def test_global_effect_does_not_survive_reset(universe) -> None:
    env, manager = _env(universe)
    money = env.meter_name_to_index["money"]
    wait = torch.full((NUM_AGENTS,), env.action_dim - 1, dtype=torch.long)

    env.reset()
    initial_money = env.meters[:, money].clone()
    env.step(_work_then_wait(env))
    live = manager.get_all_active_effects()
    # Control: the episode-N path really spawned and ticked the global effect.
    assert [(e.effect_id, e.scope.value, e.elapsed_ticks) for e in live] == [("business_cycle", "global", 1)]
    assert not torch.equal(env.meters[:, money], initial_money)

    env.reset()
    assert manager.get_all_active_effects() == []
    torch.testing.assert_close(env.meters[:, money], initial_money)

    env.step(wait)
    assert manager.get_all_active_effects() == []
    torch.testing.assert_close(env.meters[:, money], initial_money)
    assert initial_money.tolist() == [1000.0, 1000.0]


def test_respawn_in_new_episode_starts_fresh(universe) -> None:
    """Re-creation by an in-episode spawn path is legitimate and starts from zero."""
    env, manager = _env(universe)
    env.reset()
    env.step(_work_then_wait(env))
    for _ in range(3):
        env.step(torch.full((NUM_AGENTS,), env.action_dim - 1, dtype=torch.long))
    (before,) = manager.get_all_active_effects()
    assert before.elapsed_ticks == 4

    env.reset()
    env.step(_work_then_wait(env))

    (after,) = manager.get_all_active_effects()
    assert after is not before
    assert after.instance_id == 0
    assert after.elapsed_ticks == 1
    assert after.duration_remaining == after.duration_total - 1
