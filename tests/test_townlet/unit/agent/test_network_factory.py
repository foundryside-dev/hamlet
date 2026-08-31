"""Tests for network factory."""

import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.config.brain_config import (
    DuelingConfig,
    DuelingStreamConfig,
    FeedforwardConfig,
)
from townlet.universe.dto.token_spec import PAYLOAD_SCHEMAS, TOKEN_TRANSPORT_VERSION, SlotBinding, TokenSpec, build_token_type


def test_token_block_slices_use_compact_row_width():
    self_type = build_token_type(
        "self",
        (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self"),),
        slot_context_payloads=((0.0,) * len(PAYLOAD_SCHEMAS["self"]),),
        effect_catalog_contexts=(),
    )
    meter_type = build_token_type(
        "meter",
        tuple(SlotBinding(slot_index=index, filler_kind="static", filler_ref=f"meter:{index}") for index in range(2)),
        slot_context_payloads=tuple((0.0,) * len(PAYLOAD_SCHEMAS["meter"]) for _ in range(2)),
        effect_catalog_contexts=(),
    )
    spec = TokenSpec(
        types=(self_type, meter_type),
        position_rank=2,
        transport_version=TOKEN_TRANSPORT_VERSION,
    )

    slices = NetworkFactory.token_block_slices(spec)

    layout = spec.compact_layout()
    self_layout = layout.get_type("self")
    meter_layout = layout.get_type("meter")
    assert self_layout is not None and meter_layout is not None
    assert slices == {
        "self": slice(self_layout.start, self_layout.end),
        "meter": slice(meter_layout.start, meter_layout.end),
    }


def test_build_feedforward_basic():
    """NetworkFactory builds SimpleQNetwork from FeedforwardConfig."""
    config = FeedforwardConfig(
        hidden_layers=[128, 64],
        activation="relu",
        dropout=0.0,
        layer_norm=True,
    )

    network = NetworkFactory.build_feedforward(
        config=config,
        obs_dim=29,
        action_dim=8,
    )

    # Check output shape
    obs = torch.randn(4, 29)
    q_values = network(obs)
    assert q_values.shape == (4, 8)


def test_build_feedforward_multiple_layers():
    """NetworkFactory handles multiple hidden layers."""
    config = FeedforwardConfig(
        hidden_layers=[256, 128, 64],
        activation="gelu",
        dropout=0.1,
        layer_norm=False,
    )

    network = NetworkFactory.build_feedforward(
        config=config,
        obs_dim=54,
        action_dim=10,
    )

    obs = torch.randn(2, 54)
    q_values = network(obs)
    assert q_values.shape == (2, 10)


def test_build_feedforward_parameter_count():
    """NetworkFactory creates network with expected parameter count."""
    config = FeedforwardConfig(
        hidden_layers=[128],
        activation="relu",
        dropout=0.0,
        layer_norm=True,
    )

    network = NetworkFactory.build_feedforward(
        config=config,
        obs_dim=29,
        action_dim=8,
    )

    total_params = sum(p.numel() for p in network.parameters())
    # Rough sanity check (not exact)
    assert 1000 < total_params < 20000


def test_build_dueling_basic():
    """NetworkFactory builds DuelingQNetwork from DuelingConfig."""
    config = DuelingConfig(
        shared_layers=[256, 128],
        value_stream=DuelingStreamConfig(
            hidden_layers=[128],
            activation="relu",
        ),
        advantage_stream=DuelingStreamConfig(
            hidden_layers=[128],
            activation="relu",
        ),
        activation="relu",
        dropout=0.0,
        layer_norm=True,
    )

    network = NetworkFactory.build_dueling(
        config=config,
        obs_dim=29,
        action_dim=8,
    )

    # Test forward pass
    obs = torch.randn(4, 29)
    q_values = network(obs)
    assert q_values.shape == (4, 8)


def test_build_dueling_with_dropout():
    """NetworkFactory handles dropout in dueling networks."""
    config = DuelingConfig(
        shared_layers=[128],
        value_stream=DuelingStreamConfig(
            hidden_layers=[64],
            activation="gelu",
        ),
        advantage_stream=DuelingStreamConfig(
            hidden_layers=[64],
            activation="gelu",
        ),
        activation="gelu",
        dropout=0.1,
        layer_norm=False,
    )

    network = NetworkFactory.build_dueling(
        config=config,
        obs_dim=54,
        action_dim=10,
    )

    obs = torch.randn(2, 54)
    q_values = network(obs)
    assert q_values.shape == (2, 10)
