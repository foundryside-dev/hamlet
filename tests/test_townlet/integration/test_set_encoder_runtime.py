"""`token_set`, config-in/behaviour-out, over the LIVE token observation.

An unexercised code path in this codebase is not presumptively working. This file DRIVES
`architecture.type: token_set` from an authored pack through a real environment.

It was the `set_encoder` exerciser until the unit-3 token cut. `set_encoder` sliced one
flattened token FIELD out of the compiled `ObservationSpec` — the spec is gone, and the
whole observation is a token set now, so `configs/test/set_encoder_smoke` declares
`token_set` and this file follows it. What is pinned is unchanged in substance: the
declared aggregator reaches the built network, tokens reach the network and change its
output, rows pool as a SET rather than a sequence, and gradients reach the encoders.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

from townlet.agent.networks import TokenSetQNetwork
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/set_encoder_smoke")
LEVEL = "L0_test"
NUM_AGENTS = 2


def _build(level: str):
    universe = UniverseCompiler().compile(PACK, primary_level=level, use_cache=False)
    device = torch.device("cpu")
    env = VectorizedHamletEnv(universe=universe, level_name=level, num_agents=NUM_AGENTS, device=device)
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
        vision_window_size=1,
    )
    population.reset()
    return env, population


@pytest.fixture
def setup():
    return _build(LEVEL)


@pytest.fixture
def attention_setup():
    return _build("L1_attention")


def _element_type_slice(env) -> slice:
    """Serialization slice of the `variable_element` block — this pack's exposed vars."""
    from townlet.agent.network_factory import NetworkFactory

    return NetworkFactory.token_block_slices(env.token_spec)["variable_element"]


def test_config_builds_a_token_set_network(setup) -> None:
    env, population = setup
    net = population.q_network
    assert isinstance(net, TokenSetQNetwork)
    # The roster is COMPILED: one encoder per token type with capacity, keyed by NAME
    # (an nn.ModuleDict, never a list indexed by roster position).
    assert set(net.token_type_names) <= {t.type_name for t in env.token_spec.types}
    assert net.obs_dim == env.token_spec.total_dims == env.observation_dim
    assert net.aggregator_type == "mean"


def test_tokens_reach_the_network_and_change_its_output(setup) -> None:
    env, population = setup
    net = population.q_network
    element_slice = _element_type_slice(env)

    obs_zero = env._get_observations()
    q_zero = net(obs_zero)

    # Write through the REGISTRY, the authored surface: the exposed agent-profile
    # variable's elements must reach the `variable_element` token block.
    tokens = torch.rand(NUM_AGENTS, 4, 3) + 0.1
    env.vfs_registry.set("need_tokens", tokens, writer="engine")

    obs_tokens = env._get_observations()
    assert torch.any(obs_tokens[:, element_slice] != obs_zero[:, element_slice]), "a registry write must reach the observation"
    q_tokens = net(obs_tokens)
    assert not torch.allclose(q_zero, q_tokens), "token values must change Q-values"


def test_token_rows_pool_as_a_set_not_a_sequence(setup) -> None:
    env, population = setup
    net = population.q_network
    element_type = env.token_spec.get_type("variable_element")
    element_slice = _element_type_slice(env)

    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, element_slice].reshape(NUM_AGENTS, element_type.capacity, element_type.row_width)
    order = torch.randperm(element_type.capacity, generator=torch.Generator().manual_seed(7))
    permuted[:, element_slice] = rows[:, order, :].reshape(NUM_AGENTS, -1)

    assert torch.allclose(net(obs), net(permuted), atol=1e-6), (
        "mean-pooled token rows must be permutation-invariant; if this fails the block is "
        "being consumed as a flat vector, not a token set"
    )


def test_gradients_flow_into_the_per_type_encoders(setup) -> None:
    env, population = setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    grads = {name: encoder.weight.grad for name, encoder in net.encoders.items()}
    assert any(g is not None and torch.any(g != 0.0) for g in grads.values()), "loss must reach the token encoders"


def test_declared_attention_reaches_the_built_network(attention_setup) -> None:
    """The aggregator declaration is config-in/behaviour-out, not declared-but-inert."""
    _env, population = attention_setup
    net = population.q_network
    assert isinstance(net, TokenSetQNetwork)
    assert net.aggregator_type == "attention"
    assert net.num_heads == 4
    assert net.q_proj is not None and net.out_proj is not None


def test_attention_level_stays_permutation_invariant_end_to_end(attention_setup) -> None:
    env, population = attention_setup
    net = population.q_network
    element_type = env.token_spec.get_type("variable_element")
    element_slice = _element_type_slice(env)

    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, element_slice].reshape(NUM_AGENTS, element_type.capacity, element_type.row_width)
    order = torch.randperm(element_type.capacity, generator=torch.Generator().manual_seed(11))
    permuted[:, element_slice] = rows[:, order, :].reshape(NUM_AGENTS, -1)

    assert torch.allclose(net(obs), net(permuted), atol=1e-5), (
        "explicit-QKV attention without positional encoding plus masked mean-pool must stay "
        "permutation-invariant; a failure here means the aggregator sees row order"
    )


def test_attention_level_gradients_reach_the_attention_weights(attention_setup) -> None:
    env, population = attention_setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    assert net.q_proj is not None
    grad = net.q_proj.weight.grad
    assert grad is not None and torch.any(grad != 0.0), "loss must reach the attention weights"
