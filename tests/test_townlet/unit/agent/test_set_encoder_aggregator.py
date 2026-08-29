"""The set-encoder aggregator is a DECLARED choice, not an engine fact (hamlet-fa6bb6da4a).

Phase B unit 1 (PDR-0109): `SetEncoderConfig` carries a required `aggregator` block —
`{type: mean}` (the proven DeepSets pool) or `{type: attention, num_heads: N}`
(self-attention over embedded token rows, then the same masked mean-pool). Both are
permutation-invariant; the declaration must change the built module.
"""

from __future__ import annotations

import pytest
import torch
from pydantic import ValidationError

from townlet.agent.networks import SetEncoderQNetwork
from townlet.config.brain_config import SetAggregatorConfig, SetEncoderConfig

# --- config surface -------------------------------------------------------


def _encoder_config_kwargs() -> dict:
    return {
        "token_field_name": "need_tokens",
        "max_tokens": 3,
        "token_dim": 4,
        "token_embed_dim": 8,
        "base_hidden_dim": 6,
        "q_head_hidden_dim": 10,
    }


def test_set_encoder_config_requires_an_aggregator_declaration() -> None:
    with pytest.raises(ValidationError, match="aggregator"):
        SetEncoderConfig(**_encoder_config_kwargs())


def test_attention_aggregator_requires_num_heads() -> None:
    with pytest.raises(ValidationError, match="num_heads"):
        SetAggregatorConfig(type="attention")


def test_mean_aggregator_refuses_num_heads() -> None:
    with pytest.raises(ValidationError, match="num_heads"):
        SetAggregatorConfig(type="mean", num_heads=2)


def test_token_embed_dim_must_be_divisible_by_num_heads() -> None:
    with pytest.raises(ValidationError, match="divisible"):
        SetEncoderConfig(
            **{**_encoder_config_kwargs(), "token_embed_dim": 10},
            aggregator=SetAggregatorConfig(type="attention", num_heads=4),
        )


# --- network behaviour ----------------------------------------------------


def _network(aggregator_type: str, num_heads: int | None) -> SetEncoderQNetwork:
    torch.manual_seed(0)
    return SetEncoderQNetwork(
        obs_dim=14,
        action_dim=5,
        token_slice=slice(2, 14),
        token_shape=(3, 4),
        token_embed_dim=8,
        base_hidden_dim=6,
        q_head_hidden_dim=10,
        aggregator_type=aggregator_type,
        num_heads=num_heads,
    )


def _observations() -> tuple[torch.Tensor, torch.Tensor]:
    base = torch.tensor([[0.25, 0.75]])
    token_a = torch.tensor([[1.0, 0.0, 0.5, 0.0]])
    token_b = torch.tensor([[0.0, 1.0, 0.25, 0.75]])
    empty = torch.zeros(1, 4)
    obs_one = torch.cat((base, torch.cat((token_a, token_b, empty), dim=1)), dim=1)
    obs_two = torch.cat((base, torch.cat((empty, token_b, token_a), dim=1)), dim=1)
    return obs_one, obs_two


def test_declaring_attention_builds_an_attention_module_with_declared_heads() -> None:
    attention_net = _network("attention", num_heads=2)
    mean_net = _network("mean", num_heads=None)

    assert isinstance(attention_net.aggregator, torch.nn.MultiheadAttention)
    assert attention_net.aggregator.num_heads == 2
    assert mean_net.aggregator is None


def test_attention_aggregation_is_permutation_invariant_over_non_empty_tokens() -> None:
    network = _network("attention", num_heads=2)
    obs_one, obs_two = _observations()
    assert torch.allclose(network(obs_one), network(obs_two), atol=1e-6)


def test_gradients_reach_the_attention_weights() -> None:
    network = _network("attention", num_heads=2)
    obs_one, _ = _observations()
    network.zero_grad()
    network(obs_one).sum().backward()
    grad = network.aggregator.in_proj_weight.grad
    assert grad is not None and torch.any(grad != 0.0)


@pytest.mark.parametrize("aggregator_type,num_heads", [("mean", None), ("attention", 2)])
def test_all_empty_token_set_yields_finite_q_values(aggregator_type: str, num_heads: int | None) -> None:
    network = _network(aggregator_type, num_heads)
    obs = torch.cat((torch.tensor([[0.25, 0.75]]), torch.zeros(1, 12)), dim=1)
    q_values = network(obs)
    assert torch.all(torch.isfinite(q_values))


# --- factory wiring -------------------------------------------------------
