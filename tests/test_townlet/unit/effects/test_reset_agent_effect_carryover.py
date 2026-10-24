"""hamlet-d76684f549, agent scope: an agent effect must not survive ``env.reset()``.

Recipe from ``review-2026-10-24/effects/repro_d766_agent.py``: spawn ``energy_regen`` on
agent 1 of ``configs/test/effects_smoke``, step once, reset. Before ``EffectManager.reset()``
existed the instance stayed in the agent store with ``elapsed_ticks=1`` and kept regenerating
agent 1's energy in the next episode, so the two agents' energy deltas diverged.
"""

from __future__ import annotations

from pathlib import Path

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path(__file__).resolve().parents[4] / "configs" / "test" / "effects_smoke"
LEVEL = "L0_effects"
NUM_AGENTS = 2


def test_agent_effect_does_not_survive_reset() -> None:
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=NUM_AGENTS, device="cpu")
    manager = env.effect_manager
    assert manager is not None
    energy = env.meter_name_to_index["energy"]
    wait = torch.full((NUM_AGENTS,), env.action_dim - 1, dtype=torch.long)

    env.reset()
    bars = {name: env.meters[:, index] for name, index in env.meter_name_to_index.items()}
    manager.spawn_effect("energy_regen", target_entity_id=1, intensity=1.0, current_step=0, bars=bars, vfs_registry=env.vfs_registry)
    env.step(wait)
    # Control: the agent store really holds a ticked instance on agent 1.
    assert [(e.effect_id, e.target_entity_id, e.elapsed_ticks) for e in manager.get_all_active_effects()] == [("energy_regen", 1, 1)]

    env.reset()
    assert manager.agent_effects == {}
    assert manager.get_all_active_effects() == []

    before = env.meters[:, energy].clone()
    env.step(wait)
    delta = env.meters[:, energy] - before
    assert manager.get_all_active_effects() == []
    torch.testing.assert_close(delta[0], delta[1])
