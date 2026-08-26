"""Network factory for building Q-networks from configuration.

Builds neural networks from BrainConfig specifications.
Forward-compatible with future SDA (Software Defined Agent) architecture.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch.nn as nn

from townlet.agent.networks import DuelingQNetwork, RecurrentSpatialQNetwork, TokenSetQNetwork
from townlet.config.brain_config import DuelingConfig, FeedforwardConfig, RecurrentConfig, TokenSetConfig

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
    def token_block_slices(spec: TokenSpec) -> dict[str, slice]:
        """Serialization slice of each token type, by type name.

        The TokenSpec's serialization is contiguous per-type blocks in roster order —
        the same walk :meth:`TokenObservationEncoder.encode` performs. A block-reading
        network addresses its inputs through these, never through a dim literal.
        """
        slices: dict[str, slice] = {}
        offset = 0
        for token_type in spec.types:
            width = token_type.capacity * token_type.row_width
            slices[token_type.type_name] = slice(offset, offset + width)
            offset += width
        return slices

    @staticmethod
    def build_recurrent(
        config: RecurrentConfig,
        action_dim: int,
        substrate_position_dim: int,
        token_spec: TokenSpec,
    ) -> RecurrentSpatialQNetwork:
        """Build the LSTM Q-network over the compiled token serialization.

        The network's three real input blocks map onto token types: `self` carries the
        observer's position features, `meter` the meter block, `affordance` the
        affordance block. There is no spatial window in a token observation, so
        `grid_slice` is None and the vision encoder reads zeros at `window_size` 1 —
        the same "no window" case every full-observability universe produced before the
        unit-3 cut, when the window side was read off a spec that had no window field.

        This is a BLOCK reader, not a token-aware one: it flattens each type's rows into
        one Linear. A genuinely token-native recurrent/attention brain is unit 4, and
        `architecture.type='token_set'` is the shipped token-native option today. No
        shipped pack declares `recurrent`; POMDP levels run feedforward.
        """
        blocks = NetworkFactory.token_block_slices(token_spec)
        for required in ("self", "meter", "affordance"):
            if required not in blocks:
                raise ValueError(
                    f"architecture.type='recurrent' reads the {required!r} token block, which this "
                    f"compiled TokenSpec does not carry (types: {[t.type_name for t in token_spec.types]})."
                )
        meter_block = blocks["meter"]
        affordance_block = blocks["affordance"]
        self_block = blocks["self"]
        bars_dim = meter_block.stop - meter_block.start
        affordance_dims = affordance_block.stop - affordance_block.start
        if bars_dim == 0 or affordance_dims == 0:
            raise ValueError(
                "architecture.type='recurrent' requires non-empty meter and affordance token blocks; "
                f"got meter width {bars_dim}, affordance width {affordance_dims}. Declare meters and "
                "affordances, or use `feedforward` / `token_set`."
            )
        # `position_dim` sizes the position encoder, so it is the WIDTH of the block it
        # reads (the whole `self` token row), not the substrate's coordinate rank. An
        # aspatial universe has no observer position and passes 0, which is the
        # network's own "no position encoder" case.
        position_dim = (self_block.stop - self_block.start) if substrate_position_dim > 0 else 0
        return RecurrentSpatialQNetwork(
            action_dim=action_dim,
            # No spatial window exists in a token observation; 1 is the API's own
            # long-standing "no window" value and keeps the Conv2d well-formed.
            window_size=1,
            position_dim=position_dim,
            bars_dim=bars_dim,
            # The affordance encoder is sized `num_affordance_types + 1`; the block width
            # is what it must consume.
            num_affordance_types=affordance_dims - 1,
            enable_temporal_features=False,
            hidden_dim=config.lstm.hidden_size,
            meters_slice=meter_block,
            affordance_slice=affordance_block,
            grid_slice=None,
            position_slice=self_block if position_dim > 0 else None,
        )

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
