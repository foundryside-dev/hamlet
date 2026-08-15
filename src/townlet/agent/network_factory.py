"""Network factory for building Q-networks from configuration.

Builds neural networks from BrainConfig specifications.
Forward-compatible with future SDA (Software Defined Agent) architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch.nn as nn

from townlet.agent.networks import DuelingQNetwork, RecurrentSpatialQNetwork, SetEncoderQNetwork
from townlet.config.brain_config import DuelingConfig, FeedforwardConfig, RecurrentConfig, SetEncoderConfig

if TYPE_CHECKING:
    from townlet.universe.dto import ObservationActivity, ObservationSpec


class NetworkFactory:
    """Factory for building Q-networks from declarative configuration."""

    @staticmethod
    def build_feedforward(
        config: FeedforwardConfig,
        obs_dim: int,
        action_dim: int,
    ) -> nn.Module:
        """Build feedforward MLP Q-network from configuration.

        Args:
            config: Feedforward architecture configuration
            obs_dim: Observation dimension
            action_dim: Action dimension

        Returns:
            PyTorch module (feedforward Q-network)

        Example:
            >>> config = FeedforwardConfig(
            ...     hidden_layers=[256, 128],
            ...     activation="relu",
            ...     dropout=0.0,
            ...     layer_norm=True,
            ... )
            >>> network = NetworkFactory.build_feedforward(config, 29, 8)
            >>> network(torch.randn(4, 29)).shape
            torch.Size([4, 8])
        """
        layers: list[nn.Module] = []
        in_features = obs_dim

        # Build hidden layers
        for hidden_size in config.hidden_layers:
            layers.append(nn.Linear(in_features, hidden_size))

            if config.layer_norm:
                layers.append(nn.LayerNorm(hidden_size))

            layers.append(NetworkFactory._get_activation(config.activation))

            if config.dropout > 0.0:
                layers.append(nn.Dropout(config.dropout))

            in_features = hidden_size

        # Output layer (Q-values)
        layers.append(nn.Linear(in_features, action_dim))

        return nn.Sequential(*layers)

    @staticmethod
    def build_recurrent(
        config: RecurrentConfig,
        action_dim: int,
        window_size: int,
        position_dim: int,
        bars_dim: int,
        num_affordance_types: int,
        observation_spec: ObservationSpec | None = None,
        observation_activity: ObservationActivity | None = None,
    ) -> RecurrentSpatialQNetwork:
        """Build recurrent LSTM Q-network from configuration.

        Args:
            config: Recurrent architecture configuration
            action_dim: Number of actions
            window_size: Vision window size (5 for 5×5)
            position_dim: Position dimensionality (2 for Grid2D, 3 for Grid3D, 0 for Aspatial)
            bars_dim: OBSERVED width of the meter block, from
                observation_activity.group_slices["bars"] — NOT the meter count, which
                diverges as soon as a meter declares a widening normalization
            num_affordance_types: Number of affordance types
            observation_activity: Carries group_slices, which is how the meter block is
                located without knowing any field's name

        Returns:
            RecurrentSpatialQNetwork

        Note:
            This builds a RecurrentSpatialQNetwork with configurable dimensions
            instead of hardcoded values. The network structure matches the original
            RecurrentSpatialQNetwork but dimensions come from config.

            Currently, the config's vision_encoder, position_encoder, meter_encoder,
            affordance_encoder, and q_head parameters are not used because
            RecurrentSpatialQNetwork has a fixed internal architecture. This is
            acceptable for Phase 2 (TASK-005). Future phases may make the network
            architecture fully configurable.

        Example:
            >>> config = RecurrentConfig(...)
            >>> network = NetworkFactory.build_recurrent(
            ...     config=config,
            ...     action_dim=8,
            ...     window_size=5,
            ...     position_dim=2,
            ...     bars_dim=8,
            ...     num_affordance_types=14,
            ... )
        """
        # Extract LSTM hidden size from config
        lstm_hidden_size = config.lstm.hidden_size

        # Create RecurrentSpatialQNetwork with config-driven LSTM dimension
        # Note: The existing RecurrentSpatialQNetwork class has hardcoded encoder
        # architectures (CNN, MLPs). For Phase 2, we only make LSTM hidden_size
        # configurable via the hidden_dim parameter.
        # Future phases may make the entire architecture fully configurable.
        network = RecurrentSpatialQNetwork(
            action_dim=action_dim,
            window_size=window_size,
            position_dim=position_dim,
            bars_dim=bars_dim,
            num_affordance_types=num_affordance_types,
            enable_temporal_features=False,  # Will be determined by environment
            hidden_dim=lstm_hidden_size,  # From config instead of hardcoded!
            observation_spec=observation_spec,
            observation_activity=observation_activity,
        )

        return network

    @staticmethod
    def build_dueling(
        config: DuelingConfig,
        obs_dim: int,
        action_dim: int,
    ) -> DuelingQNetwork:
        """Build Dueling Q-network from configuration.

        Args:
            config: Dueling architecture configuration
            obs_dim: Observation dimension
            action_dim: Action dimension

        Returns:
            DuelingQNetwork

        Example:
            >>> config = DuelingConfig(
            ...     shared_layers=[256, 128],
            ...     value_stream=DuelingStreamConfig(...),
            ...     advantage_stream=DuelingStreamConfig(...),
            ...     activation="relu",
            ...     dropout=0.0,
            ...     layer_norm=True,
            ... )
            >>> network = NetworkFactory.build_dueling(config, 29, 8)
        """
        network = DuelingQNetwork(
            obs_dim=obs_dim,
            action_dim=action_dim,
            shared_dims=config.shared_layers,
            value_dims=config.value_stream.hidden_layers,
            advantage_dims=config.advantage_stream.hidden_layers,
            activation=config.activation,
            value_activation=config.value_stream.activation,
            advantage_activation=config.advantage_stream.activation,
            dropout=config.dropout,
            layer_norm=config.layer_norm,
        )

        return network

    @staticmethod
    def build_set_encoder(
        config: SetEncoderConfig,
        obs_dim: int,
        action_dim: int,
        observation_spec: ObservationSpec,
    ) -> SetEncoderQNetwork:
        """Build a set-aware Q-network from a flattened token observation field."""
        token_field = observation_spec.get_field_by_name(config.token_field_name)
        expected_dims = config.max_tokens * config.token_dim
        if token_field.dims != expected_dims:
            raise ValueError(
                f"Set encoder token field {config.token_field_name!r} has dims={token_field.dims}, "
                f"expected max_tokens * token_dim = {expected_dims}"
            )
        if observation_spec.total_dims != obs_dim:
            raise ValueError(f"ObservationSpec total_dims={observation_spec.total_dims} does not match obs_dim={obs_dim}")

        return SetEncoderQNetwork(
            obs_dim=obs_dim,
            action_dim=action_dim,
            token_slice=slice(token_field.start_index, token_field.end_index),
            token_shape=(config.max_tokens, config.token_dim),
            token_embed_dim=config.token_embed_dim,
            base_hidden_dim=config.base_hidden_dim,
            q_head_hidden_dim=config.q_head_hidden_dim,
        )

    @staticmethod
    def _get_activation(activation: str) -> nn.Module:
        """Get activation function module from config string.

        Args:
            activation: Activation function name

        Returns:
            PyTorch activation module
        """
        activations = {
            "relu": nn.ReLU(),
            "gelu": nn.GELU(),
            "swish": nn.SiLU(),  # Swish = SiLU in PyTorch
            "tanh": nn.Tanh(),
            "elu": nn.ELU(),
        }
        return activations[activation]
