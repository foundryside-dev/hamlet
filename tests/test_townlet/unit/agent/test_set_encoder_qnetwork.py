"""Tests for set-aware Q-network support."""

import torch

from townlet.agent.networks import SetEncoderQNetwork


def test_set_encoder_qnetwork_outputs_q_values_for_flattened_token_observations() -> None:
    network = SetEncoderQNetwork(
        obs_dim=14,
        action_dim=5,
        token_slice=slice(2, 14),
        token_shape=(3, 4),
        token_embed_dim=8,
        base_hidden_dim=6,
        q_head_hidden_dim=10,
        aggregator_type="mean",
        num_heads=None,
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
        aggregator_type="mean",
        num_heads=None,
    )

    base = torch.tensor([[0.25, 0.75]])
    token_a = torch.tensor([[1.0, 0.0, 0.5, 0.0]])
    token_b = torch.tensor([[0.0, 1.0, 0.25, 0.75]])
    empty = torch.zeros(1, 4)

    obs_one = torch.cat((base, torch.cat((token_a, token_b, empty), dim=1)), dim=1)
    obs_two = torch.cat((base, torch.cat((empty, token_b, token_a), dim=1)), dim=1)

    assert torch.allclose(network(obs_one), network(obs_two), atol=1e-6)


