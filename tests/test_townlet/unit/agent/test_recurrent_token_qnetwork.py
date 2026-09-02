"""Canonical token-native recurrent Q-network contracts."""

from __future__ import annotations

import pytest
import torch

from tests.test_townlet.unit.agent.test_token_set_qnetwork import make_obs, make_spec, present_rows
from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import RecurrentTokenQNetwork, TokenSetEncoder
from townlet.config.brain_config import LSTMConfig, RecurrentConfig, SetAggregatorConfig


def _config(*, aggregator: str = "mean", num_heads: int | None = None) -> RecurrentConfig:
    return RecurrentConfig(
        token_embed_dim=16,
        aggregator=SetAggregatorConfig(type=aggregator, num_heads=num_heads),
        lstm=LSTMConfig(hidden_size=24, num_layers=2, dropout=0.0),
        q_head_hidden_dim=32,
    )


def test_recurrent_schema_is_only_the_token_native_contract() -> None:
    assert set(RecurrentConfig.model_fields) == {"token_embed_dim", "aggregator", "lstm", "q_head_hidden_dim"}


def test_single_layer_lstm_rejects_inert_dropout() -> None:
    with pytest.raises(ValueError, match="dropout.*num_layers"):
        LSTMConfig(hidden_size=24, num_layers=1, dropout=0.1)


@pytest.mark.parametrize(("aggregator", "num_heads"), [("mean", None), ("attention", 4)])
def test_sequence_forward_uses_one_lstm_call(aggregator: str, num_heads: int | None) -> None:
    spec = make_spec()
    network = NetworkFactory.build_recurrent(
        config=_config(aggregator=aggregator, num_heads=num_heads),
        action_dim=5,
        token_spec=spec,
    )
    assert isinstance(network, RecurrentTokenQNetwork)
    assert isinstance(network.encoder, TokenSetEncoder)

    batch_size = 256
    sequence_length = 8
    step = make_obs(spec, batch_size, present=present_rows(spec))
    observations = step.unsqueeze(1).expand(-1, sequence_length, -1).contiguous()
    hidden = network.initial_hidden(batch_size, torch.device("cpu"))
    calls = 0

    def count_call(_module, _args) -> None:
        nonlocal calls
        calls += 1

    handle = network.lstm.register_forward_pre_hook(count_call)
    try:
        q_values, new_hidden = network(observations, hidden)
    finally:
        handle.remove()

    assert calls == 1
    assert q_values.shape == (batch_size, sequence_length, 5)
    assert new_hidden[0].shape == (2, batch_size, 24)
    assert new_hidden[1].shape == (2, batch_size, 24)


def test_recurrent_forward_rejects_single_step_rank_two_input() -> None:
    spec = make_spec()
    network = NetworkFactory.build_recurrent(config=_config(), action_dim=5, token_spec=spec)
    observation = make_obs(spec, 2, present=present_rows(spec))
    hidden = network.initial_hidden(2, torch.device("cpu"))
    with pytest.raises(ValueError, match=r"\[batch, sequence, observation\]"):
        network(observation, hidden)
