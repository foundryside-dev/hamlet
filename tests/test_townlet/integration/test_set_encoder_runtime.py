"""set_encoder, config-in/behaviour-out (PDR-0017 first unit, hamlet-fa6bb6da4a).

An unexercised code path in this codebase is not presumptively working. This file is the
first thing that ever DRIVES architecture.type: set_encoder from an authored pack.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.agent.networks import SetEncoderQNetwork
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"
NUM_AGENTS = 2


@pytest.fixture
def setup():
    universe = UniverseCompiler().compile(PACK, primary_level=LEVEL, use_cache=False)
    device = torch.device("cpu")
    env = VectorizedHamletEnv(universe=universe, level_name=LEVEL, num_agents=NUM_AGENTS, device=device)
    population = VectorizedPopulation(
        env=env,
        curriculum=StaticCurriculum(difficulty_level=0.5),
        exploration=EpsilonGreedyExploration(epsilon=0.1, epsilon_min=0.1, epsilon_decay=1.0),
        agent_ids=[f"agent_{i}" for i in range(NUM_AGENTS)],
        device=device,
        obs_dim=env.observation_dim,
        brain_config=universe.brain,
        action_dim=env.action_dim,
        train_frequency=1,
        batch_size=16,
        sequence_length=1,
        max_grad_norm=1.0,
        vision_window_size=5,
    )
    population.reset()
    return universe, env, population


def _token_slice(universe) -> slice:
    field = universe.observation_spec.get_field_by_name("need_tokens")
    return slice(field.start_index, field.end_index)


def test_config_builds_a_set_encoder_network(setup) -> None:
    universe, env, population = setup
    assert isinstance(population.q_network, SetEncoderQNetwork)
    assert population.is_set_encoder is True
    net = population.q_network
    assert (net.max_tokens, net.token_dim) == (4, 3)
    assert net.token_slice == _token_slice(universe)


def test_tokens_reach_the_network_and_change_its_output(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    sl = _token_slice(universe)

    obs_zero = env._get_observations()
    assert torch.all(obs_zero[:, sl] == 0.0), "token field should initialize to zeros"
    q_zero = net(obs_zero)

    tokens = torch.rand(NUM_AGENTS, 4, 3) + 0.1  # strictly nonzero: every row is non-empty
    env.vfs_registry.set("need_tokens", tokens, writer="engine")

    obs_tokens = env._get_observations()
    assert torch.any(obs_tokens[:, sl] != 0.0), "registry write must reach the observation"
    q_tokens = net(obs_tokens)
    assert not torch.allclose(q_zero, q_tokens), "token values must change Q-values"


def test_token_rows_are_a_set_not_a_sequence(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    sl = _token_slice(universe)

    tokens = torch.rand(NUM_AGENTS, 4, 3) + 0.1
    env.vfs_registry.set("need_tokens", tokens, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, sl].reshape(NUM_AGENTS, 4, 3)
    permuted[:, sl] = rows[:, [2, 0, 3, 1], :].reshape(NUM_AGENTS, 12)

    assert torch.allclose(net(obs), net(permuted), atol=1e-6), (
        "mean-pooled token rows must be permutation-invariant; if this fails the slice is "
        "being consumed as a flat vector, not a token set"
    )


def test_gradients_flow_into_the_token_encoder(setup) -> None:
    universe, env, population = setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    grad = net.token_encoder[0].weight.grad
    assert grad is not None and torch.any(grad != 0.0), "loss must reach the token encoder"
