"""`token_set`, config-in/behaviour-out, over the live token observation.

An unexercised code path in this codebase is not presumptively working. This file DRIVES
`architecture.type: token_set` from an authored pack through a real environment.

The declared aggregator reaches the built network, tokens reach the network and change
its output, rows pool as a set rather than a sequence, and gradients reach the encoders.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import torch

from townlet.agent.networks import TokenSetQNetwork
from townlet.curriculum.static import StaticCurriculum
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.universe.compiler import UniverseCompiler

PACK = Path("configs/test/token_set_smoke")
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
    layout = env.token_spec.compact_layout().get_type("variable_element")
    assert layout is not None
    return slice(layout.start, layout.end)


def _network_with_permuted_element_contexts(
    env: VectorizedHamletEnv,
    net: TokenSetQNetwork,
    order: torch.Tensor,
) -> TokenSetQNetwork:
    """Build the equivalent ABI whose compiled slot contexts follow ``order``.

    Compact rows carry only live fields. A meaningful token permutation therefore
    permutes each row together with the positional compiled context that the input
    assembler attaches at the network boundary.
    """
    element_type = env.token_spec.get_type("variable_element")
    assert element_type is not None
    indices = tuple(int(index) for index in order.tolist())
    permuted_element_type = replace(
        element_type,
        slot_bindings=tuple(
            replace(element_type.slot_bindings[old_index], slot_index=new_index) for new_index, old_index in enumerate(indices)
        ),
        slot_context_payloads=tuple(element_type.slot_context_payloads[index] for index in indices),
    )
    permuted_spec = replace(
        env.token_spec,
        types=tuple(
            permuted_element_type if token_type.type_name == "variable_element" else token_type for token_type in env.token_spec.types
        ),
    )
    first_head_layer = net.q_head[0]
    assert isinstance(first_head_layer, torch.nn.Linear)
    permuted_net = TokenSetQNetwork(
        token_spec=permuted_spec,
        action_dim=net.action_dim,
        token_embed_dim=net.token_embed_dim,
        q_head_hidden_dim=first_head_layer.out_features,
        aggregator_type=net.encoder.aggregator_type,
        num_heads=net.encoder.num_heads,
    )
    permuted_net.load_state_dict(net.state_dict())
    return permuted_net


def test_config_builds_a_token_set_network(setup) -> None:
    env, population = setup
    net = population.q_network
    assert isinstance(net, TokenSetQNetwork)
    # The roster is COMPILED: one encoder per token type with capacity, keyed by NAME
    # (an nn.ModuleDict, never a list indexed by roster position).
    assert set(net.token_type_names) <= {t.type_name for t in env.token_spec.types}
    assert net.obs_dim == env.token_spec.total_dims == env.observation_dim
    assert net.encoder.aggregator_type == "mean"


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
    element_layout = env.token_spec.compact_layout().get_type("variable_element")
    assert element_type is not None and element_layout is not None
    element_slice = _element_type_slice(env)

    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, element_slice].reshape(NUM_AGENTS, element_type.capacity, element_layout.compact_row_width)
    order = torch.randperm(element_type.capacity, generator=torch.Generator().manual_seed(7))
    permuted[:, element_slice] = rows[:, order, :].reshape(NUM_AGENTS, -1)
    permuted_net = _network_with_permuted_element_contexts(env, net, order)

    assert torch.allclose(net(obs), permuted_net(permuted), atol=1e-6), (
        "mean-pooled tokens must be invariant when compact rows and their compiled " "slot contexts are permuted together"
    )


def test_gradients_flow_into_the_per_type_encoders(setup) -> None:
    env, population = setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    grads = {name: encoder.weight.grad for name, encoder in net.encoder.encoders.items()}
    assert any(g is not None and torch.any(g != 0.0) for g in grads.values()), "loss must reach the token encoders"


def test_declared_attention_reaches_the_built_network(attention_setup) -> None:
    """The aggregator declaration is config-in/behaviour-out, not declared-but-inert."""
    _env, population = attention_setup
    net = population.q_network
    assert isinstance(net, TokenSetQNetwork)
    assert net.encoder.aggregator_type == "attention"
    assert net.encoder.num_heads == 4
    assert net.encoder.q_proj is not None and net.encoder.out_proj is not None


def test_attention_level_stays_permutation_invariant_end_to_end(attention_setup) -> None:
    env, population = attention_setup
    net = population.q_network
    element_type = env.token_spec.get_type("variable_element")
    element_layout = env.token_spec.compact_layout().get_type("variable_element")
    assert element_type is not None and element_layout is not None
    element_slice = _element_type_slice(env)

    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    permuted = obs.clone()
    rows = permuted[:, element_slice].reshape(NUM_AGENTS, element_type.capacity, element_layout.compact_row_width)
    order = torch.randperm(element_type.capacity, generator=torch.Generator().manual_seed(11))
    permuted[:, element_slice] = rows[:, order, :].reshape(NUM_AGENTS, -1)
    permuted_net = _network_with_permuted_element_contexts(env, net, order)

    assert torch.allclose(net(obs), permuted_net(permuted), atol=1e-5), (
        "explicit-QKV attention without positional encoding plus masked mean-pool must stay "
        "invariant when compact rows and their compiled slot contexts are permuted together"
    )


def test_attention_level_gradients_reach_the_attention_weights(attention_setup) -> None:
    env, population = attention_setup
    net = population.q_network
    env.vfs_registry.set("need_tokens", torch.rand(NUM_AGENTS, 4, 3) + 0.1, writer="engine")
    obs = env._get_observations()

    net.zero_grad()
    net(obs).sum().backward()
    assert net.encoder.q_proj is not None
    grad = net.encoder.q_proj.weight.grad
    assert grad is not None and torch.any(grad != 0.0), "loss must reach the attention weights"
