"""Tests for set-aware Q-network support."""

import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import SetEncoderQNetwork
from townlet.config.brain_config import SetEncoderConfig
from townlet.universe.dto import ObservationField, ObservationSpec


def _dynamic_need_observation_spec() -> ObservationSpec:
    return ObservationSpec.from_fields(
        [
            ObservationField(
                uuid=None,
                name="obs_base",
                type="vector",
                dims=2,
                start_index=0,
                end_index=2,
                scope="agent",
                description="Base non-token features",
                semantic_type="custom",
                feature="variable",
            ),
            ObservationField(
                uuid=None,
                name="dynamic_need_tokens",
                type="vector",
                dims=12,
                start_index=2,
                end_index=14,
                scope="agent",
                description="Flattened dynamic-need token set",
                semantic_type="custom",
                feature="variable",
            ),
        ]
    )


def test_set_encoder_qnetwork_outputs_q_values_for_flattened_token_observations() -> None:
    network = SetEncoderQNetwork(
        obs_dim=14,
        action_dim=5,
        token_slice=slice(2, 14),
        token_shape=(3, 4),
        token_embed_dim=8,
        base_hidden_dim=6,
        q_head_hidden_dim=10,
    )

    q_values = network(torch.randn(7, 14))

    assert q_values.shape == torch.Size([7, 5])


def test_set_encoder_qnetwork_is_permutation_invariant_over_non_empty_tokens() -> None:
    torch.manual_seed(0)
    network = SetEncoderQNetwork(
        obs_dim=14,
        action_dim=5,
        token_slice=slice(2, 14),
        token_shape=(3, 4),
        token_embed_dim=8,
        base_hidden_dim=6,
        q_head_hidden_dim=10,
    )

    base = torch.tensor([[0.25, 0.75]])
    token_a = torch.tensor([[1.0, 0.0, 0.5, 0.0]])
    token_b = torch.tensor([[0.0, 1.0, 0.25, 0.75]])
    empty = torch.zeros(1, 4)

    obs_one = torch.cat((base, torch.cat((token_a, token_b, empty), dim=1)), dim=1)
    obs_two = torch.cat((base, torch.cat((empty, token_b, token_a), dim=1)), dim=1)

    assert torch.allclose(network(obs_one), network(obs_two), atol=1e-6)


def test_network_factory_builds_set_encoder_from_observation_spec() -> None:
    config = SetEncoderConfig(
        token_field_name="dynamic_need_tokens",
        max_tokens=3,
        token_dim=4,
        token_embed_dim=8,
        base_hidden_dim=6,
        q_head_hidden_dim=10,
    )

    network = NetworkFactory.build_set_encoder(
        config=config,
        obs_dim=14,
        action_dim=5,
        observation_spec=_dynamic_need_observation_spec(),
    )

    q_values = network(torch.randn(2, 14))

    assert isinstance(network, SetEncoderQNetwork)
    assert q_values.shape == torch.Size([2, 5])
