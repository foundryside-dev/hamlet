"""Neural network architectures for townlet agents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple, cast

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812
from torch.nn.attention import SDPBackend, sdpa_kernel

from townlet.agent.token_input import TokenInputAssembler as _TokenInputAssembler

if TYPE_CHECKING:
    from townlet.universe.dto.token_spec import TokenSpec


class SimpleQNetwork(nn.Module):
    """Simple MLP Q-network with LayerNorm."""

    def __init__(self, obs_dim: int, action_dim: int, hidden_dim: int):
        """
        Initialize simple MLP Q-network.

        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            hidden_dim: Hidden layer dimension (typically 128-256)

        Note (PDR-002):
            All network architecture parameters must be explicitly specified.
            No BAC (BRAIN_AS_CODE) defaults allowed.
        """
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: [batch, obs_dim] observations

        Returns:
            q_values: [batch, action_dim]
        """
        return cast(torch.Tensor, self.net(x))


class DuelingQNetwork(nn.Module):
    """Dueling Q-Network with value and advantage streams.

    Architecture (Wang et al. 2016):
    - Shared layers: obs → feature representation
    - Value stream: feature → V(s) [scalar]
    - Advantage stream: feature → A(s,a) [action_dim]
    - Aggregation: Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))

    The mean subtraction ensures identifiability: V(s) represents
    state value, A(s,a) represents relative action advantage.
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        shared_dims: list[int],
        value_dims: list[int],
        advantage_dims: list[int],
        activation: str = "relu",
        value_activation: str | None = None,
        advantage_activation: str | None = None,
        dropout: float = 0.0,
        layer_norm: bool = True,
    ):
        """Initialize Dueling Q-Network.

        Args:
            obs_dim: Observation dimension
            action_dim: Number of actions
            shared_dims: Shared layer sizes (e.g., [256, 128])
            value_dims: Value stream layer sizes (e.g., [128])
            advantage_dims: Advantage stream layer sizes (e.g., [128])
            activation: Activation function for shared layers
            value_activation: Activation for value stream (defaults to activation)
            advantage_activation: Activation for advantage stream (defaults to activation)
            dropout: Dropout probability for shared layers (0.0 = no dropout)
            layer_norm: Apply LayerNorm after shared/stream layers
        """
        super().__init__()

        # Default per-stream activations to shared activation
        value_activation = value_activation or activation
        advantage_activation = advantage_activation or activation

        # Shared layers
        shared_layers: list[nn.Module] = []
        in_features = obs_dim
        for dim in shared_dims:
            shared_layers.append(nn.Linear(in_features, dim))
            if layer_norm:
                shared_layers.append(nn.LayerNorm(dim))
            shared_layers.append(self._get_activation(activation))
            if dropout > 0.0:
                shared_layers.append(nn.Dropout(dropout))
            in_features = dim
        self.shared = nn.Sequential(*shared_layers)

        # Value stream: feature → V(s)
        value_layers: list[nn.Module] = []
        in_features = shared_dims[-1]
        for dim in value_dims:
            value_layers.append(nn.Linear(in_features, dim))
            if layer_norm:
                value_layers.append(nn.LayerNorm(dim))
            value_layers.append(self._get_activation(value_activation))
            in_features = dim
        value_layers.append(nn.Linear(in_features, 1))  # Scalar value
        self.value_stream = nn.Sequential(*value_layers)

        # Advantage stream: feature → A(s,a)
        advantage_layers: list[nn.Module] = []
        in_features = shared_dims[-1]
        for dim in advantage_dims:
            advantage_layers.append(nn.Linear(in_features, dim))
            if layer_norm:
                advantage_layers.append(nn.LayerNorm(dim))
            advantage_layers.append(self._get_activation(advantage_activation))
            in_features = dim
        advantage_layers.append(nn.Linear(in_features, action_dim))
        self.advantage_stream = nn.Sequential(*advantage_layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with dueling decomposition.

        Args:
            x: [batch, obs_dim] observations

        Returns:
            q_values: [batch, action_dim]
                Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
        """
        # Shared feature extraction
        features = self.shared(x)  # [batch, shared_dims[-1]]

        # Value stream: V(s)
        value = self.value_stream(features)  # [batch, 1]

        # Advantage stream: A(s,a)
        advantage = self.advantage_stream(features)  # [batch, action_dim]

        # Dueling aggregation: Q(s,a) = V(s) + (A(s,a) - mean(A(s,:)))
        # Mean subtraction ensures identifiability
        advantage_mean = advantage.mean(dim=1, keepdim=True)  # [batch, 1]
        q_values: torch.Tensor = value + (advantage - advantage_mean)  # [batch, action_dim]

        return q_values

    @staticmethod
    def _get_activation(activation: str) -> nn.Module:
        """Get activation function module."""
        activations = {
            "relu": nn.ReLU(),
            "gelu": nn.GELU(),
            "swish": nn.SiLU(),
            "tanh": nn.Tanh(),
            "elu": nn.ELU(),
        }
        return activations[activation]


class _TokenTypeLayout(NamedTuple):
    """One live token type's compact slice and fixed network-boundary width."""

    type_name: str
    capacity: int
    payload_width: int
    compact_row_width: int
    start: int
    end: int


class TokenSetEncoder(nn.Module):
    """Permutation-invariant encoder over the compiled TokenSpec serialization.

    Consumes the flat token observation (`[batch, total_dims]`, rows in canonical
    type-then-slot order, presence leading each row) and reads it as a token set:

    1. per-type projection encoders — ``Linear(W_t → token_embed_dim)`` in an
       ``nn.ModuleDict`` keyed by token type NAME (a list indexed by roster position
       would re-bind weights silently on roster differences — spec §4);
    2. a learned per-type embedding added post-projection (type-keyed, transfers);
    3. all tokens pooled into ONE mixed set;
    4. the declared aggregator — ``mean`` (masked mean-pool) or ``attention``
       (explicit QKV + ``F.scaled_dot_product_attention`` per the unit-3 Global
       Constraints — deliberately NOT ``nn.MultiheadAttention``, whose fused path
       cannot be pinned for byte-exact training replay), then the same masked
       mean-pool;

    Masking is OUTPUT-SIDE (spec §4, load-bearing): an absent token's zero row still
    embeds to the projection bias + type embedding, so its embedded row is multiplied
    by the bool presence mask AFTER encoding — exact-zero contribution AND exact-zero
    gradient for absent tokens, per aggregator type, pinned by test. Absent tokens are
    additionally excluded as attention KEYS; the all-empty unmask guard keeps softmax
    finite for a row with no present token (its pooled vector is forced to exact zero
    by the output-side mask + count clamp).

    Only types with capacity > 0 get an encoder: a structurally-absent type (capacity
    0 — e.g. `agent` in every shipped pack) contributes no parameters, so the
    ModuleDict key set IS the universe's live roster, which is what the cross-universe
    intersection load keys on. No LayerNorm/Linear ever sees the concatenated set
    width (Global Constraints); the token path is per-token-row only.
    """

    def __init__(
        self,
        token_spec: TokenSpec,
        token_embed_dim: int,
        aggregator_type: str,
        num_heads: int | None,
    ):
        """Initialize a token-native Q-network from a compiled TokenSpec.

        Args:
            token_spec: The compiled token artifact. The roster is compiled, never
                authored — capacities, payload widths and the serialization layout
                all come from here.
            token_embed_dim: Embedding width every live type projects into.
            aggregator_type: ``"mean"`` or ``"attention"`` — declared, never defaulted.
            num_heads: Attention heads; required for ``"attention"``, must be None
                for ``"mean"`` (the PDR-0112 aggregator contract).
        """
        super().__init__()
        if token_embed_dim <= 0:
            raise ValueError("token_embed_dim must be positive")

        layouts: list[_TokenTypeLayout] = []
        compact_layout = token_spec.compact_layout()
        for token_type in token_spec.types:
            if token_type.capacity > 0:
                type_layout = compact_layout.get_type(token_type.type_name)
                assert type_layout is not None
                layouts.append(
                    _TokenTypeLayout(
                        type_name=token_type.type_name,
                        capacity=token_type.capacity,
                        payload_width=token_type.payload_width,
                        compact_row_width=type_layout.compact_row_width,
                        start=type_layout.start,
                        end=type_layout.end,
                    )
                )
        if not layouts:
            raise ValueError(
                "TokenSpec has no token type with capacity > 0; a token-set network over an " "empty roster cannot observe anything."
            )
        self._layouts: tuple[_TokenTypeLayout, ...] = tuple(layouts)
        self.obs_dim = token_spec.total_dims
        self.token_embed_dim = token_embed_dim
        self.input_assembler = _TokenInputAssembler(token_spec)

        # Per-type projection encoders, keyed by type NAME (the transfer contract).
        self.encoders = nn.ModuleDict({layout.type_name: nn.Linear(layout.payload_width, token_embed_dim) for layout in self._layouts})
        # Learned per-type embedding, added post-projection. Zero-init: deterministic,
        # and the per-type projection weights already break type symmetry at step 0.
        self.type_embeddings = nn.ParameterDict({layout.type_name: nn.Parameter(torch.zeros(token_embed_dim)) for layout in self._layouts})

        self.aggregator_type = aggregator_type
        if aggregator_type == "attention":
            if num_heads is None:
                raise ValueError("aggregator_type='attention' requires num_heads")
            if token_embed_dim % num_heads != 0:
                raise ValueError(f"token_embed_dim ({token_embed_dim}) must be divisible by num_heads ({num_heads})")
            self.num_heads: int | None = num_heads
            # Explicit QKV + output projection (Global Constraints: never nn.MultiheadAttention).
            self.q_proj: nn.Linear | None = nn.Linear(token_embed_dim, token_embed_dim)
            self.k_proj: nn.Linear | None = nn.Linear(token_embed_dim, token_embed_dim)
            self.v_proj: nn.Linear | None = nn.Linear(token_embed_dim, token_embed_dim)
            self.out_proj: nn.Linear | None = nn.Linear(token_embed_dim, token_embed_dim)
        elif aggregator_type == "mean":
            if num_heads is not None:
                raise ValueError("aggregator_type='mean' takes no num_heads")
            self.num_heads = None
            self.q_proj = None
            self.k_proj = None
            self.v_proj = None
            self.out_proj = None
        else:
            raise ValueError(f"Unknown aggregator_type: {aggregator_type!r}. Supported: mean, attention")

    @property
    def token_type_names(self) -> tuple[str, ...]:
        """The live roster this network was built for, in engine-canonical order."""
        return tuple(layout.type_name for layout in self._layouts)

    def _embed_tokens(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Slice the flat vector per type, embed, and concatenate the mixed set.

        Returns:
            tokens: [batch, N_total, token_embed_dim] embedded rows (unmasked)
            presence: [batch, N_total] bool presence mask (spec §6: masks are bool)
        """
        if obs.dim() != 2 or obs.shape[1] != self.obs_dim:
            raise ValueError(f"Expected observations with shape [batch, {self.obs_dim}], got {tuple(obs.shape)}")
        batch_size = obs.shape[0]
        embedded_parts: list[torch.Tensor] = []
        presence_parts: list[torch.Tensor] = []
        for layout in self._layouts:
            # `.view()` raises on copy (Global Constraints) — the flat slice of a
            # contiguous [batch, obs_dim] tensor reshapes without one.
            dynamic_rows = obs[:, layout.start : layout.end].view(batch_size, layout.capacity, layout.compact_row_width)
            rows = self.input_assembler.expand_type(layout.type_name, dynamic_rows)
            presence_parts.append(rows[:, :, 0] > 0.5)
            embedded = self.encoders[layout.type_name](rows[:, :, 1:]) + self.type_embeddings[layout.type_name]
            embedded_parts.append(embedded)
            del rows
        return torch.cat(embedded_parts, dim=1), torch.cat(presence_parts, dim=1)

    def pooled_embedding(self, obs: torch.Tensor) -> torch.Tensor:
        """The permutation-invariant pooled set embedding, [batch, token_embed_dim].

        Exposed separately from :meth:`forward` for the §3b training-dynamical
        diagnostics (pooled-embedding norm, online-vs-target cosine drift).
        """
        tokens, presence = self._embed_tokens(obs)
        if self.aggregator_type == "attention":
            assert self.q_proj is not None and self.k_proj is not None and self.v_proj is not None and self.out_proj is not None
            assert self.num_heads is not None
            batch_size, n_tokens, _ = tokens.shape
            head_dim = self.token_embed_dim // self.num_heads
            # A row with no present token would mask every key and make softmax NaN;
            # unmask its keys and rely on the output-side zeroing below, which already
            # forces all-empty sets to an exact-zero pooled vector.
            all_empty = ~presence.any(dim=1, keepdim=True)
            key_mask = presence | all_empty
            query = self.q_proj(tokens).view(batch_size, n_tokens, self.num_heads, head_dim).transpose(1, 2)
            key = self.k_proj(tokens).view(batch_size, n_tokens, self.num_heads, head_dim).transpose(1, 2)
            value = self.v_proj(tokens).view(batch_size, n_tokens, self.num_heads, head_dim).transpose(1, 2)
            # Bool attn_mask: True = may attend. Broadcasts over heads and queries.
            # MATH backend pinned: spec §6 demands byte-exact replay from the token
            # path (the reason for explicit QKV over nn.MultiheadAttention); fused
            # backends may vary bitwise across runs/devices (task-9 review I2).
            with sdpa_kernel([SDPBackend.MATH]):
                attended = F.scaled_dot_product_attention(query, key, value, attn_mask=key_mask[:, None, None, :])
            tokens = self.out_proj(attended.transpose(1, 2).reshape(batch_size, n_tokens, self.token_embed_dim))
        # Output-side masking: exact-zero contribution AND exact-zero gradient for
        # absent tokens (spec §4) — the multiply-by-zero cuts the autograd path.
        tokens = tokens * presence.unsqueeze(-1).to(dtype=tokens.dtype)
        counts = presence.sum(dim=1).clamp(min=1).to(dtype=tokens.dtype)
        return tokens.sum(dim=1) / counts.unsqueeze(-1)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """Encode observations into pooled token embeddings."""
        return self.pooled_embedding(obs)


class TokenSetQNetwork(nn.Module):
    """Q-network composed from a shared token-set encoder and a Q-head."""

    def __init__(
        self,
        token_spec: TokenSpec,
        action_dim: int,
        token_embed_dim: int,
        q_head_hidden_dim: int,
        aggregator_type: str,
        num_heads: int | None,
    ):
        super().__init__()
        if action_dim <= 0:
            raise ValueError("action_dim must be positive")
        if q_head_hidden_dim <= 0:
            raise ValueError("q_head_hidden_dim must be positive")
        self.action_dim = action_dim
        self.encoder = TokenSetEncoder(
            token_spec=token_spec,
            token_embed_dim=token_embed_dim,
            aggregator_type=aggregator_type,
            num_heads=num_heads,
        )
        self.obs_dim = self.encoder.obs_dim
        self.token_embed_dim = self.encoder.token_embed_dim
        self.q_head = nn.Sequential(
            nn.Linear(token_embed_dim, q_head_hidden_dim),
            nn.LayerNorm(q_head_hidden_dim),
            nn.ReLU(),
            nn.Linear(q_head_hidden_dim, action_dim),
        )

    @property
    def token_type_names(self) -> tuple[str, ...]:
        return self.encoder.token_type_names

    def pooled_embedding(self, obs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.encoder(obs))

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.q_head(self.encoder(obs)))


class RecurrentTokenQNetwork(nn.Module):
    """Token-set encoder followed by one sequence-level LSTM call and a Q-head."""

    def __init__(
        self,
        token_spec: TokenSpec,
        action_dim: int,
        token_embed_dim: int,
        q_head_hidden_dim: int,
        aggregator_type: str,
        num_heads: int | None,
        lstm_hidden_size: int,
        lstm_num_layers: int,
        lstm_dropout: float,
    ):
        super().__init__()
        if action_dim <= 0:
            raise ValueError("action_dim must be positive")
        if q_head_hidden_dim <= 0:
            raise ValueError("q_head_hidden_dim must be positive")
        self.action_dim = action_dim
        self.hidden_dim = lstm_hidden_size
        self.encoder = TokenSetEncoder(
            token_spec=token_spec,
            token_embed_dim=token_embed_dim,
            aggregator_type=aggregator_type,
            num_heads=num_heads,
        )
        self.obs_dim = self.encoder.obs_dim
        self.token_embed_dim = self.encoder.token_embed_dim
        self.lstm = nn.LSTM(
            input_size=token_embed_dim,
            hidden_size=lstm_hidden_size,
            num_layers=lstm_num_layers,
            dropout=lstm_dropout,
            batch_first=True,
        )
        self.q_head = nn.Sequential(
            nn.Linear(lstm_hidden_size, q_head_hidden_dim),
            nn.LayerNorm(q_head_hidden_dim),
            nn.ReLU(),
            nn.Linear(q_head_hidden_dim, action_dim),
        )

    @property
    def token_type_names(self) -> tuple[str, ...]:
        return self.encoder.token_type_names

    def initial_hidden(self, batch_size: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
        shape = (self.lstm.num_layers, batch_size, self.lstm.hidden_size)
        return torch.zeros(shape, device=device), torch.zeros(shape, device=device)

    def forward(
        self,
        observations: torch.Tensor,
        hidden: tuple[torch.Tensor, torch.Tensor],
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        if observations.dim() != 3 or observations.shape[2] != self.encoder.obs_dim:
            raise ValueError(
                f"Expected observations with shape [batch, sequence, observation] where observation={self.encoder.obs_dim}, "
                f"got {tuple(observations.shape)}"
            )
        batch_size, sequence_length, observation_dim = observations.shape
        flat_observations = observations.reshape(batch_size * sequence_length, observation_dim)
        encoded = self.encoder(flat_observations).reshape(batch_size, sequence_length, -1)
        recurrent, new_hidden = self.lstm(encoded, hidden)
        return cast(torch.Tensor, self.q_head(recurrent)), new_hidden


class StructuredQNetwork(nn.Module):
    """
    Structured Q-Network with group encoders for semantic observation groups.

    Uses caller-given group slices for semantic groups (spatial, bars, affordances, temporal, custom)
    and processes each group with its own encoder MLP before combining for Q-value prediction.

    Architecture:
    - Group Encoders: Each semantic group → embedding_dim features (default 32)
    - Concatenation: All group embeddings → combined_dim
    - Q-Head: combined_dim → hidden_dim → action_dim

    This architecture leverages observation structure for better inductive bias compared to
    SimpleQNetwork which treats all observation dimensions uniformly.
    """

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        group_slices: Mapping[str, slice],
        group_embed_dim: int = 32,
        q_head_hidden_dim: int = 128,
    ):
        """
        Initialize structured Q-network with group encoders.

        Args:
            obs_dim: Total observation dimension
            action_dim: Number of actions
            group_slices: Semantic group name -> slice into the observation
            group_embed_dim: Embedding dimension for each group encoder (default 32)
            q_head_hidden_dim: Hidden dimension for final Q-head MLP (default 128)

        Note (PDR-002):
            Architecture parameters explicitly specified, no BAC defaults.
        """
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.group_slices = dict(group_slices)
        self.group_embed_dim = group_embed_dim

        # Create encoder for each semantic group
        self.group_encoders = nn.ModuleDict()
        total_embed_dim = 0

        for group_name, group_slice in self.group_slices.items():
            group_size = group_slice.stop - group_slice.start

            # Skip empty groups
            if group_size <= 0:
                continue

            # Create encoder: group_size → group_embed_dim
            encoder = nn.Sequential(
                nn.Linear(group_size, group_embed_dim),
                nn.LayerNorm(group_embed_dim),
                nn.ReLU(),
            )
            self.group_encoders[group_name] = encoder
            total_embed_dim += group_embed_dim

        # Q-head: combined embeddings → hidden → action_dim
        self.q_head = nn.Sequential(
            nn.Linear(total_embed_dim, q_head_hidden_dim),
            nn.LayerNorm(q_head_hidden_dim),
            nn.ReLU(),
            nn.Linear(q_head_hidden_dim, action_dim),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """
        Forward pass with structured group processing.

        Args:
            obs: [batch, obs_dim] observations

        Returns:
            q_values: [batch, action_dim]
        """
        # Extract and encode each group
        group_embeddings = []

        for group_name, encoder in self.group_encoders.items():
            group_slice = self.group_slices[group_name]
            group_obs = obs[:, group_slice]
            group_embed = encoder(group_obs)
            group_embeddings.append(group_embed)

        # Concatenate all group embeddings
        combined = torch.cat(group_embeddings, dim=1)  # [batch, total_embed_dim]

        # Q-values
        q_values = self.q_head(combined)  # [batch, action_dim]

        return cast(torch.Tensor, q_values)
