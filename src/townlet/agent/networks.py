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


class RecurrentSpatialQNetwork(nn.Module):
    """
    Recurrent Spatial Q-Network for partial observability (Level 2 POMDP).

    Architecture:
    - Vision Encoder: CNN for local window → 128 features
    - Position Encoder: (x, y) → 32 features
    - Meter Encoder: 8 meters → 32 features
    - Affordance Encoder: 15 affordance types → 32 features
    - LSTM: 224 input → 256 hidden
    - Q-Head: 256 → 128 → action_dim

    Handles partial observations:
    - Grid: [batch, window_size²] flattened local window (25 for 5×5)
    - Position: [batch, 2] normalized (x, y)
    - Meters: [batch, 8] normalized meter values
    - Affordance: [batch, 15] one-hot affordance type (14 types + "none")
    """

    def __init__(
        self,
        action_dim: int,
        window_size: int,
        position_dim: int,
        bars_dim: int,
        num_affordance_types: int,
        enable_temporal_features: bool,
        hidden_dim: int,
        meters_slice: slice,
        affordance_slice: slice,
        grid_slice: slice | None = None,
        position_slice: slice | None = None,
        temporal_slice: slice | None = None,
        temporal_embed_dim: int = 16,
    ):
        """
        Initialize recurrent spatial Q-network.

        Args:
            action_dim: Number of actions
            window_size: Size of local vision window (5 for 5×5)
            position_dim: Dimensionality of position (2 for Grid2D, 3 for Grid3D, 0 for Aspatial)
            bars_dim: OBSERVED width of the meter block. Not the meter COUNT — the two differ
                whenever a meter declares a widening normalization (cyclical_sin_cos observes 2
                dims, one_hot observes its category count). Read it from
                the caller's bars group slice, never from a meter count.
            num_affordance_types: Number of affordance types
            enable_temporal_features: Whether to expect temporal features
            hidden_dim: LSTM hidden dimension (typically 256)
            meters_slice: Meter (bars) block slice. REQUIRED.
            grid_slice: Local spatial-window block slice, or None when the universe has
                no spatial window. `None` is the long-standing "no window" case — it was
                what a full-observability universe produced before the unit-3 cut too —
                and the vision encoder then reads zeros at `window_size` 1.
            affordance_slice: Affordance block slice. REQUIRED.
            position_slice: Position block slice, or None when the substrate is aspatial.
            temporal_slice: Temporal block slice, or None when temporal is inactive.

        Note (PDR-002):
            All network architecture parameters must be explicitly specified.
            No BAC (BRAIN_AS_CODE) defaults allowed.

        Future (BRAIN_AS_CODE):
            These parameters should come from network config YAML.
        """
        super().__init__()
        self.action_dim = action_dim
        self.window_size = window_size
        self.position_dim = position_dim
        self.bars_dim = bars_dim
        self.num_affordance_types = num_affordance_types
        self.enable_temporal_features = enable_temporal_features
        self.temporal_dims = 4  # Fixed v2.1 temporal feature count
        self.hidden_dim = hidden_dim

        # Calculate affordance encoding dimension (types + 1 for "none")
        self.num_affordance_dims = num_affordance_types + 1

        # Vision Encoder: CNN for local window → 128 features
        self.vision_encoder = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),  # 16×window_size×window_size
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),  # 32×window_size×window_size
            nn.ReLU(),
            nn.Flatten(),  # 32 * window_size * window_size
            nn.Linear(32 * window_size * window_size, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
        )

        # Position Encoder: position_dim → 32 features (conditional on position_dim > 0)
        self.position_encoder: nn.Sequential | None
        if position_dim > 0:
            self.position_encoder = nn.Sequential(
                nn.Linear(position_dim, 32),
                nn.ReLU(),
            )
            position_features = 32
        else:
            # Aspatial: no position encoding
            self.position_encoder = None
            position_features = 0

        # Meter Encoder: the OBSERVED bars width → 32 features. This took `num_meters`, a
        # STATE count threaded in from env.meter_count — an observation-side layer sized by a
        # state-side quantity, which held only while every meter observed exactly one dim.
        self.meter_encoder = nn.Sequential(
            nn.Linear(bars_dim, 32),
            nn.ReLU(),
        )

        # Temporal Encoder: 4 temporal features → temporal_embed_dim
        self.temporal_encoder = nn.Sequential(
            nn.Linear(self.temporal_dims, temporal_embed_dim),
            nn.ReLU(),
        )

        # Affordance Encoder: dynamic size based on num_affordance_dims
        self.affordance_encoder = nn.Sequential(
            nn.Linear(self.num_affordance_dims, 32),
            nn.ReLU(),
        )

        # LSTM: variable input → hidden_dim
        # Input size: 128 (vision) + position_features (0 or 32) + 32 (meters) + 32 (affordance) + temporal_embed_dim
        self.lstm_input_dim = 128 + position_features + 32 + 32 + temporal_embed_dim
        self.lstm = nn.LSTM(input_size=self.lstm_input_dim, hidden_size=hidden_dim, num_layers=1, batch_first=True)

        # LayerNorm for LSTM output
        self.lstm_norm = nn.LayerNorm(hidden_dim)

        # Q-Head: hidden_dim → 128 → action_dim
        self.q_head = nn.Sequential(
            nn.Linear(hidden_dim, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
        )

        # Input-block slicing, given EXPLICITLY by the caller.
        #
        # These used to be derived from the compiled `ObservationSpec` /
        # `ObservationActivity`, which the unit-3 token cut deleted. The caller now names
        # them, and `NetworkFactory.build_recurrent` derives them from the compiled
        # TokenSpec's contiguous per-type serialization blocks: `self` -> position,
        # `meter` -> meters, `affordance` -> affordance. There is no spatial window in a
        # token observation, so `grid_slice` is None and the vision encoder reads zeros —
        # the same "no window" case every full-observability universe produced before the
        # cut. A token-aware recurrent/attention brain is unit 4.
        self._grid_slice: slice | None = grid_slice
        self._position_slice: slice | None = position_slice
        self._meters_slice: slice = meters_slice
        self._affordance_slice: slice = affordance_slice
        self._temporal_slice: slice | None = temporal_slice

    def forward(
        self,
        obs: torch.Tensor,
        hidden: tuple[torch.Tensor, torch.Tensor],
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass with LSTM memory.

        The network owns no hidden state: callers thread it explicitly. Use
        `initial_hidden(batch_size, device)` at episode/sequence start.

        Args:
            obs: [batch, obs_dim] observations where:
                - obs[:, :window_size²] = local grid
                - obs[:, window_size²:window_size²+position_dim] = position (position_dim)
                - obs[:, window_size²+position_dim:window_size²+position_dim+num_meters] = meters
                - obs[:, window_size²+position_dim+num_meters:window_size²+position_dim+num_meters+num_affordance_dims] = affordance
                - obs[:, window_size²+position_dim+num_meters+num_affordance_dims:] = temporal (if enabled)
            hidden: LSTM hidden state (h, c), each [num_layers, batch, hidden_dim] (required)

        Returns:
            q_values: [batch, action_dim]
            new_hidden: Tuple of (h, c) hidden states
        """
        batch_size = obs.shape[0]

        grid = obs[:, self._grid_slice] if self._grid_slice is not None else obs.new_zeros((batch_size, self.window_size**2))
        position = obs[:, self._position_slice] if (self._position_slice is not None and self.position_dim > 0) else None
        meters = obs[:, self._meters_slice]
        affordance = (
            obs[:, self._affordance_slice] if self._affordance_slice is not None else obs.new_zeros((batch_size, self.num_affordance_dims))
        )
        temporal = (
            obs[:, self._temporal_slice]
            if self._temporal_slice is not None
            else obs.new_zeros((batch_size, self.temporal_dims if hasattr(self, "temporal_dims") else 0))
        )

        # Reshape grid for CNN: [batch, 1, window_size, window_size]
        grid_2d = grid.view(batch_size, 1, self.window_size, self.window_size)

        # Encode components
        vision_features = self.vision_encoder(grid_2d)  # [batch, 128]

        if self.position_encoder is not None:
            position_features = self.position_encoder(position)  # [batch, 32]
        else:
            # Aspatial: no position features
            position_features = None

        meter_features = self.meter_encoder(meters)  # [batch, 32]
        affordance_features = self.affordance_encoder(affordance)  # [batch, 32]
        temporal_features = self.temporal_encoder(temporal) if temporal.numel() > 0 else None

        # Concatenate features (conditionally include position)
        parts = [vision_features, meter_features, affordance_features]
        if position_features is not None:
            parts.insert(1, position_features)
        if temporal_features is not None:
            parts.append(temporal_features)
        combined = torch.cat(parts, dim=1)

        # LSTM expects [batch, seq_len, input_dim]
        combined = combined.unsqueeze(1)  # [batch, 1, lstm_input_dim]

        # LSTM forward
        lstm_out, new_hidden = self.lstm(combined, hidden)  # lstm_out: [batch, 1, hidden_dim]
        lstm_out = lstm_out.squeeze(1)  # [batch, hidden_dim]

        # Apply LayerNorm to LSTM output
        lstm_out = self.lstm_norm(lstm_out)  # [batch, hidden_dim]

        # Q-values
        q_values = self.q_head(lstm_out)  # [batch, action_dim]

        return q_values, new_hidden

    def initial_hidden(self, batch_size: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
        """Fresh all-zero LSTM hidden state for a new episode or sampled sequence.

        The network owns no mutable hidden state; callers hold and thread it.

        Args:
            batch_size: Batch size for the hidden state
            device: Device for the tensors (required)

        Returns:
            (h, c), each [num_layers, batch_size, hidden_dim], all zeros
        """
        h = torch.zeros(self.lstm.num_layers, batch_size, self.hidden_dim, device=device)
        c = torch.zeros(self.lstm.num_layers, batch_size, self.hidden_dim, device=device)
        return (h, c)


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


class TokenSetQNetwork(nn.Module):
    """Q-network over the TokenSpec serialization (token-obs spec §4; unit 3 Task 9).

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
    5. Q-head over the pooled embedding.

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
        action_dim: int,
        token_embed_dim: int,
        q_head_hidden_dim: int,
        aggregator_type: str,
        num_heads: int | None,
    ):
        """Initialize a token-native Q-network from a compiled TokenSpec.

        Args:
            token_spec: The compiled token artifact. The roster is compiled, never
                authored — capacities, payload widths and the serialization layout
                all come from here.
            action_dim: Number of actions.
            token_embed_dim: Embedding width every live type projects into.
            q_head_hidden_dim: Hidden size of the Q-value head.
            aggregator_type: ``"mean"`` or ``"attention"`` — declared, never defaulted.
            num_heads: Attention heads; required for ``"attention"``, must be None
                for ``"mean"`` (the PDR-0112 aggregator contract).
        """
        super().__init__()
        if action_dim <= 0:
            raise ValueError("action_dim must be positive")
        if token_embed_dim <= 0:
            raise ValueError("token_embed_dim must be positive")
        if q_head_hidden_dim <= 0:
            raise ValueError("q_head_hidden_dim must be positive")

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
        self.action_dim = action_dim
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

        self.q_head = nn.Sequential(
            nn.Linear(token_embed_dim, q_head_hidden_dim),
            nn.LayerNorm(q_head_hidden_dim),
            nn.ReLU(),
            nn.Linear(q_head_hidden_dim, action_dim),
        )

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
        """Encode the token set into Q-values, [batch, action_dim]."""
        return cast(torch.Tensor, self.q_head(self.pooled_embedding(obs)))


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
