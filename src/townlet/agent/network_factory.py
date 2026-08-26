"""Network factory for building Q-networks from configuration.

Builds neural networks from BrainConfig specifications.
Forward-compatible with future SDA (Software Defined Agent) architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch.nn as nn

from townlet.agent.networks import DuelingQNetwork, TokenSetQNetwork
from townlet.config.brain_config import DuelingConfig, FeedforwardConfig, TokenSetConfig

if TYPE_CHECKING:
    from townlet.universe.dto.token_spec import TokenSpec


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
    def build_token_set(
        config: TokenSetConfig,
        action_dim: int,
        token_spec: TokenSpec,
    ) -> TokenSetQNetwork:
        """Build a token-native Q-network over a compiled TokenSpec (token-obs spec §4).

        The roster is compiled, never authored: capacities, payload widths and the
        serialization layout come from the TokenSpec; ``config`` declares only the
        embedding width, aggregator (PDR-0112 block verbatim), and Q-head size.
        """
        return TokenSetQNetwork(
            token_spec=token_spec,
            action_dim=action_dim,
            token_embed_dim=config.token_embed_dim,
            q_head_hidden_dim=config.q_head_hidden_dim,
            aggregator_type=config.aggregator.type,
            num_heads=config.aggregator.num_heads,
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
