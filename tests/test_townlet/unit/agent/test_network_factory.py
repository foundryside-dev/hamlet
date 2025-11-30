"""Tests for network factory."""

import torch

from townlet.agent.network_factory import NetworkFactory
from townlet.agent.networks import RecurrentSpatialQNetwork
from townlet.config.brain_config import (
    CNNEncoderConfig,
    DuelingConfig,
    DuelingStreamConfig,
    FeedforwardConfig,
    LSTMConfig,
    MLPEncoderConfig,
    RecurrentConfig,
)
from townlet.universe.dto import ObservationField, ObservationSpec


def _make_observation_spec(
    *,
    window_size: int,
    position_dim: int,
    num_meters: int,
    num_affordance_types: int,
) -> ObservationSpec:
    """Construct an ObservationSpec matching RecurrentSpatialQNetwork expectations."""
    fields: list[ObservationField] = []
    start = 0

    grid_dims = window_size * window_size
    fields.append(
        ObservationField(
            uuid=None,
            name="obs_local_window",
            type="spatial_grid",
            dims=grid_dims,
            start_index=start,
            end_index=start + grid_dims,
            scope="agent",
            description="Local vision window grid encoding",
            semantic_type="spatial",
        )
    )
    start += grid_dims

    if position_dim > 0:
        fields.append(
            ObservationField(
                uuid=None,
                name="obs_position",
                type="vector",
                dims=position_dim,
                start_index=start,
                end_index=start + position_dim,
                scope="agent",
                description="Agent position",
                semantic_type="spatial",
            )
        )
        start += position_dim

    fields.append(
        ObservationField(
            uuid=None,
            name="obs_meters",
            type="vector",
            dims=num_meters,
            start_index=start,
            end_index=start + num_meters,
            scope="agent",
            description="Meter values",
            semantic_type="meters",
        )
    )
    start += num_meters

    affordance_dims = num_affordance_types + 1  # network expects +1 for "none"
    fields.append(
        ObservationField(
            uuid=None,
            name="obs_affordances",
            type="vector",
            dims=affordance_dims,
            start_index=start,
            end_index=start + affordance_dims,
            scope="agent",
            description="Affordance activations",
            semantic_type="affordance",
        )
    )
    start += affordance_dims

    return ObservationSpec.from_fields(fields)


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


def test_build_recurrent_basic():
    """NetworkFactory builds RecurrentSpatialQNetwork from RecurrentConfig."""
    config = RecurrentConfig(
        vision_encoder=CNNEncoderConfig(
            channels=[16, 32],
            kernel_sizes=[3, 3],
            strides=[1, 1],
            padding=[1, 1],
            activation="relu",
        ),
        position_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        meter_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        affordance_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        lstm=LSTMConfig(
            hidden_size=256,
            num_layers=1,
            dropout=0.0,
        ),
        q_head=MLPEncoderConfig(
            hidden_sizes=[128],
            activation="relu",
        ),
    )

    obs_spec = _make_observation_spec(
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
    )

    network = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec,
    )

    # Verify network type
    assert isinstance(network, RecurrentSpatialQNetwork)

    # Test forward pass with dummy observation
    batch_size = 4
    obs = torch.randn(batch_size, obs_spec.total_dims)

    q_values, hidden = network(obs)

    assert q_values.shape == (batch_size, 8)
    assert isinstance(hidden, tuple)
    assert len(hidden) == 2
    assert hidden[0].shape == (1, batch_size, 256)  # h
    assert hidden[1].shape == (1, batch_size, 256)  # c


def test_build_recurrent_parameter_count():
    """NetworkFactory creates recurrent network with expected parameter count."""
    config = RecurrentConfig(
        vision_encoder=CNNEncoderConfig(
            channels=[16, 32],
            kernel_sizes=[3, 3],
            strides=[1, 1],
            padding=[1, 1],
            activation="relu",
        ),
        position_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        meter_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        affordance_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        lstm=LSTMConfig(
            hidden_size=256,
            num_layers=1,
            dropout=0.0,
        ),
        q_head=MLPEncoderConfig(
            hidden_sizes=[128],
            activation="relu",
        ),
    )

    obs_spec = _make_observation_spec(
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
    )

    network = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec,
    )

    total_params = sum(p.numel() for p in network.parameters())
    # Recurrent networks are larger (~500K-700K params)
    assert 400_000 < total_params < 1_000_000


def test_build_recurrent_custom_lstm_size():
    """NetworkFactory respects custom LSTM hidden_size from config."""
    config = RecurrentConfig(
        vision_encoder=CNNEncoderConfig(
            channels=[16, 32],
            kernel_sizes=[3, 3],
            strides=[1, 1],
            padding=[1, 1],
            activation="relu",
        ),
        position_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        meter_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        affordance_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        lstm=LSTMConfig(
            hidden_size=128,  # Smaller LSTM
            num_layers=1,
            dropout=0.0,
        ),
        q_head=MLPEncoderConfig(
            hidden_sizes=[64],
            activation="relu",
        ),
    )

    obs_spec = _make_observation_spec(
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
    )

    network = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec,
    )

    # Verify LSTM hidden size is 128 (not default 256)
    assert network.hidden_dim == 128

    # Test forward pass
    batch_size = 2
    obs = torch.randn(batch_size, obs_spec.total_dims)

    q_values, hidden = network(obs)

    assert q_values.shape == (batch_size, 8)
    assert hidden[0].shape == (1, batch_size, 128)  # h with custom size
    assert hidden[1].shape == (1, batch_size, 128)  # c with custom size


def test_build_recurrent_aspatial():
    """NetworkFactory builds recurrent network for aspatial substrate (position_dim=0)."""
    config = RecurrentConfig(
        vision_encoder=CNNEncoderConfig(
            channels=[16, 32],
            kernel_sizes=[3, 3],
            strides=[1, 1],
            padding=[1, 1],
            activation="relu",
        ),
        position_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        meter_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        affordance_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        lstm=LSTMConfig(
            hidden_size=256,
            num_layers=1,
            dropout=0.0,
        ),
        q_head=MLPEncoderConfig(
            hidden_sizes=[128],
            activation="relu",
        ),
    )

    obs_spec = _make_observation_spec(
        window_size=5,
        position_dim=0,
        num_meters=8,
        num_affordance_types=14,
    )

    network = NetworkFactory.build_recurrent(
        config=config,
        action_dim=4,
        window_size=5,
        position_dim=0,  # Aspatial (no position)
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec,
    )

    # Test forward pass without position component
    batch_size = 2
    obs = torch.randn(batch_size, obs_spec.total_dims)

    q_values, hidden = network(obs)

    assert q_values.shape == (batch_size, 4)
    assert hidden[0].shape == (1, batch_size, 256)
    assert hidden[1].shape == (1, batch_size, 256)


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


def test_build_recurrent_temporal_features_detection():
    """NetworkFactory detects temporal features from observation_spec."""
    config = RecurrentConfig(
        vision_encoder=CNNEncoderConfig(
            channels=[16, 32],
            kernel_sizes=[3, 3],
            strides=[1, 1],
            padding=[1, 1],
            activation="relu",
        ),
        position_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        meter_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        affordance_encoder=MLPEncoderConfig(
            hidden_sizes=[32],
            activation="relu",
        ),
        lstm=LSTMConfig(
            hidden_size=256,
            num_layers=1,
            dropout=0.0,
        ),
        q_head=MLPEncoderConfig(
            hidden_sizes=[128],
            activation="relu",
        ),
    )

    # Create observation spec WITH temporal features
    fields_with_temporal: list[ObservationField] = []
    start = 0

    # Local window
    grid_dims = 25
    fields_with_temporal.append(
        ObservationField(
            uuid=None,
            name="obs_local_window",
            type="spatial_grid",
            dims=grid_dims,
            start_index=start,
            end_index=start + grid_dims,
            scope="agent",
            description="Local vision window",
            semantic_type="spatial",
        )
    )
    start += grid_dims

    # Position
    fields_with_temporal.append(
        ObservationField(
            uuid=None,
            name="obs_position",
            type="vector",
            dims=2,
            start_index=start,
            end_index=start + 2,
            scope="agent",
            description="Agent position",
            semantic_type="spatial",
        )
    )
    start += 2

    # Meters
    fields_with_temporal.append(
        ObservationField(
            uuid=None,
            name="obs_meters",
            type="vector",
            dims=8,
            start_index=start,
            end_index=start + 8,
            scope="agent",
            description="Meter values",
            semantic_type="meters",
        )
    )
    start += 8

    # Affordances
    fields_with_temporal.append(
        ObservationField(
            uuid=None,
            name="obs_affordances",
            type="vector",
            dims=15,
            start_index=start,
            end_index=start + 15,
            scope="agent",
            description="Affordance activations",
            semantic_type="affordance",
        )
    )
    start += 15

    # Temporal features (the key field to detect)
    fields_with_temporal.append(
        ObservationField(
            uuid=None,
            name="obs_temporal",
            type="vector",
            dims=4,
            start_index=start,
            end_index=start + 4,
            scope="global",
            description="Temporal features (time_sin, time_cos, day, progress)",
            semantic_type="temporal",
        )
    )
    start += 4

    obs_spec_with_temporal = ObservationSpec.from_fields(fields_with_temporal)

    # Build network WITH temporal features
    network_with_temporal = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec_with_temporal,
    )

    # Verify temporal features are enabled
    assert network_with_temporal.enable_temporal_features is True

    # Build network WITHOUT temporal features (using existing helper)
    obs_spec_without_temporal = _make_observation_spec(
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
    )

    network_without_temporal = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=obs_spec_without_temporal,
    )

    # Verify temporal features are disabled
    assert network_without_temporal.enable_temporal_features is False

    # Build network with None observation_spec
    network_none_spec = NetworkFactory.build_recurrent(
        config=config,
        action_dim=8,
        window_size=5,
        position_dim=2,
        num_meters=8,
        num_affordance_types=14,
        observation_spec=None,
    )

    # Verify temporal features default to False
    assert network_none_spec.enable_temporal_features is False
