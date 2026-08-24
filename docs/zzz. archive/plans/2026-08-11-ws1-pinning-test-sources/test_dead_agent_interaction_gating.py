"""Pinning test candidate for hamlet-88acec4bb5 (dead-agent interaction filter)."""

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/default_curriculum")
LEVEL = "L1_full_observability"


@pytest.fixture(scope="module")
def universe():
    return UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)


def _env_with_one_dead_agent(universe):
    env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=2, device="cpu")
    env.reset()
    health = env.meter_name_to_index["health"]
    env.meters[1, health] = 0.0
    env.step(torch.full((2,), env.action_ids["WAIT"], dtype=torch.long))
    assert env.dones.tolist() == [False, True], "vacuity: terminal condition did not kill agent 1"
    return env


def test_a_dead_agent_is_not_charged_the_interaction_cost(universe):
    env = _env_with_one_dead_agent(universe)
    energy = env.meter_name_to_index["energy"]
    occupied = {tuple(v.tolist()) for v in env.affordances.values()}
    free = next((x, y) for x in range(8) for y in range(8) if (x, y) not in occupied)
    env.positions[0] = torch.tensor(free)
    env.positions[1] = torch.tensor(free)
    env.meters[:, energy] = 0.5
    before = env.meters[:, energy].clone()
    env._action_executor._execute_actions(torch.full((2,), env.action_ids["INTERACT"], dtype=torch.long))
    after = env.meters[:, energy]
    assert after[0].item() < before[0].item(), "vacuity: live agent was not charged"
    assert after[1].item() == pytest.approx(before[1].item()), "dead agent was charged the interaction cost"


def test_a_dead_agent_does_not_complete_an_instant_interaction(universe):
    env = _env_with_one_dead_agent(universe)
    energy = env.meter_name_to_index["energy"]
    money = env.meter_name_to_index["money"]
    work = env.affordances["WORK"]
    env.positions[0] = work.clone()
    env.positions[1] = work.clone()
    env.meters[:, energy] = 0.5
    env.meters[:, money] = 0.0
    _, _, _, info = env.step(torch.full((2,), env.action_ids["INTERACT"], dtype=torch.long))
    assert info["successful_interactions"].get(0) == "WORK", "vacuity: live agent did not interact"
    assert 1 not in info["successful_interactions"], "dead agent completed an interaction"
    assert env.meters[1, money].item() == pytest.approx(0.0), "dead agent was paid"
    assert env._last_affordances[1] is None, "dead agent polluted affordance tracking"
    assert env._affordance_streaks["WORK"][1].item() == 0, "dead agent polluted streaks"
