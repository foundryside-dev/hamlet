"""Tests for effect observations exposed to agents."""

import pytest
import torch

from townlet.config.effects_config import EffectScope
from townlet.effects.manager import ActiveEffect
from townlet.environment.vectorized_env import VectorizedHamletEnv


class _StubEffectManager:
    def __init__(self, effect_map):
        self._effect_map = effect_map

    def get_observable_agent_effects(self, agent_id: int):
        return [eff for eff in self._effect_map.get(agent_id, []) if getattr(eff, "observable", False)]


def _make_env_stub(effect_manager, effect_slots: int, num_agents: int = 2):
    env = VectorizedHamletEnv.__new__(VectorizedHamletEnv)
    env.device = torch.device("cpu")
    env.num_agents = num_agents
    env.effect_manager = effect_manager
    env.effect_observation_slots = effect_slots
    return env


def test_effect_observation_encodes_observable_effects():
    """Observable effects should populate fixed slots with id, remaining ratio, and active flag."""
    effect_a = ActiveEffect(
        effect_id="shield",
        instance_id=1,
        target_entity_id=0,
        scope=EffectScope.AGENT,
        intensity=1.0,
        duration_total=10,
        duration_remaining=5,
        elapsed_ticks=0,
        spawn_step=0,
        observable=True,
        effect_index=3,
    )
    effect_hidden = ActiveEffect(
        effect_id="invisible",
        instance_id=2,
        target_entity_id=0,
        scope=EffectScope.AGENT,
        intensity=1.0,
        duration_total=10,
        duration_remaining=8,
        elapsed_ticks=0,
        spawn_step=0,
        observable=False,
        effect_index=4,
    )

    manager = _StubEffectManager({0: [effect_a, effect_hidden], 1: []})
    env = _make_env_stub(manager, effect_slots=2, num_agents=2)

    obs = env._build_effects_observation(dims=6)  # 2 slots × 3 dims
    assert obs.shape == (2, 6)

    # First agent gets the observable effect in slot 0
    assert obs[0, 0].item() == pytest.approx(3)  # effect_index
    assert obs[0, 1].item() == pytest.approx(0.5)  # remaining normalized
    assert obs[0, 2].item() == pytest.approx(1.0)  # active flag
    # Hidden effect should be filtered out; slot 1 remains zero
    assert torch.all(obs[0, 3:] == 0)

    # Second agent has no effects; all zeros
    assert torch.all(obs[1] == 0)


def test_effect_observation_handles_missing_manager():
    env = _make_env_stub(effect_manager=None, effect_slots=2, num_agents=1)
    obs = env._build_effects_observation(dims=6)
    assert torch.all(obs == 0)
