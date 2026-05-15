"""Neural network architectures for townlet agents."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import torch
import torch.nn as nn

if TYPE_CHECKING:
    from townlet.universe.dto import ObservationActivity, ObservationSpec


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
        num_meters: int,
        num_affordance_types: int,
        enable_temporal_features: bool,
        hidden_dim: int,
        observation_spec: ObservationSpec | None = None,
        temporal_embed_dim: int = 16,
    ):
        """
        Initialize recurrent spatial Q-network.

        Args:
            action_dim: Number of actions
            window_size: Size of local vision window (5 for 5×5)
            position_dim: Dimensionality of position (2 for Grid2D, 3 for Grid3D, 0 for Aspatial)
            num_meters: Number of meter values
            num_affordance_types: Number of affordance types
            enable_temporal_features: Whether to expect temporal features
            hidden_dim: LSTM hidden dimension (typically 256)

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
        self.num_meters = num_meters
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

        # Meter Encoder: num_meters → 32 features
        self.meter_encoder = nn.Sequential(
            nn.Linear(num_meters, 32),
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

        # Hidden state (initialized per episode)
        self.hidden_state: tuple[torch.Tensor, torch.Tensor] | None = None

        # Optional observation-spec-driven slicing (v2.1 pipeline).
        self._use_observation_spec = observation_spec is not None
        self._grid_slice: slice | None = None
        self._position_slice: slice | None = None
        self._meters_slice: slice | None = None
        self._affordance_slice: slice | None = None
        self._temporal_slice: slice | None = None

        if observation_spec is not None:
            try:
                fields = observation_spec.fields
                for field in fields:
                    if field.name == "obs_local_window":
                        self._grid_slice = slice(field.start_index, field.end_index)
                    elif field.name == "obs_position":
                        self._position_slice = slice(field.start_index, field.end_index)
                    elif field.name == "obs_meters":
                        self._meters_slice = slice(field.start_index, field.end_index)
                    elif field.name in {"obs_affordance_at_position", "obs_affordances"}:
                        self._affordance_slice = slice(field.start_index, field.end_index)
                    elif field.name == "obs_temporal":
                        self._temporal_slice = slice(field.start_index, field.end_index)

                # Enable spec-driven slicing only if we have the critical fields.
                if self._grid_slice is None or self._meters_slice is None or self._affordance_slice is None:
                    self._use_observation_spec = False
            except Exception:  # pragma: no cover - defensive
                self._use_observation_spec = False

    def forward(
        self, obs: torch.Tensor, hidden: tuple[torch.Tensor, torch.Tensor] | None = None
    ) -> tuple[torch.Tensor, tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass with LSTM memory.

        Args:
            obs: [batch, obs_dim] observations where:
                - obs[:, :window_size²] = local grid
                - obs[:, window_size²:window_size²+position_dim] = position (position_dim)
                - obs[:, window_size²+position_dim:window_size²+position_dim+num_meters] = meters
                - obs[:, window_size²+position_dim+num_meters:window_size²+position_dim+num_meters+num_affordance_dims] = affordance
                - obs[:, window_size²+position_dim+num_meters+num_affordance_dims:] = temporal (if enabled)
            hidden: Optional LSTM hidden state (h, c), each [1, batch, hidden_dim]

        Returns:
            q_values: [batch, action_dim]
            new_hidden: Tuple of (h, c) hidden states
        """
        batch_size = obs.shape[0]

        if not self._use_observation_spec or self._grid_slice is None:
            raise ValueError("ObservationSpec-driven slicing is required in v2.1; legacy positional layout is no longer supported.")

        grid = obs[:, self._grid_slice]
        position = obs[:, self._position_slice] if (self._position_slice is not None and self.position_dim > 0) else None
        meters = obs[:, self._meters_slice] if self._meters_slice is not None else obs.new_zeros((batch_size, self.num_meters))
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

        # Use provided hidden state or self.hidden_state
        if hidden is None:
            hidden = self.hidden_state

        # If still None, initialize with zeros
        if hidden is None:
            h = torch.zeros(1, batch_size, self.hidden_dim, device=obs.device)
            c = torch.zeros(1, batch_size, self.hidden_dim, device=obs.device)
            hidden = (h, c)

        # LSTM forward
        lstm_out, new_hidden = self.lstm(combined, hidden)  # lstm_out: [batch, 1, hidden_dim]
        lstm_out = lstm_out.squeeze(1)  # [batch, hidden_dim]

        # Apply LayerNorm to LSTM output
        lstm_out = self.lstm_norm(lstm_out)  # [batch, hidden_dim]

        # Q-values
        q_values = self.q_head(lstm_out)  # [batch, action_dim]

        return q_values, new_hidden

    def reset_hidden_state(self, batch_size: int, device: torch.device | None = None) -> None:
        """
        Reset LSTM hidden state (call at episode start).

        Args:
            batch_size: Batch size for hidden state
            device: Device for tensors (default: cpu). Infrastructure default - PDR-002 exemption.
        """
        if device is None:
            device = torch.device("cpu")

        h = torch.zeros(1, batch_size, self.hidden_dim, device=device)
        c = torch.zeros(1, batch_size, self.hidden_dim, device=device)
        self.hidden_state = (h, c)

    def set_hidden_state(self, hidden: tuple[torch.Tensor, torch.Tensor]) -> None:
        """
        Set LSTM hidden state (for episode rollouts).

        Args:
            hidden: Tuple of (h, c) hidden states
        """
        self.hidden_state = hidden

    def get_hidden_state(self) -> tuple[torch.Tensor, torch.Tensor] | None:
        """Get current LSTM hidden state."""
        return self.hidden_state


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


class SetEncoderQNetwork(nn.Module):
    """Q-network that pools a fixed-capacity token set with permutation-invariant mean aggregation."""

    def __init__(
        self,
        obs_dim: int,
        action_dim: int,
        token_slice: slice,
        token_shape: tuple[int, int],
        token_embed_dim: int,
        base_hidden_dim: int,
        q_head_hidden_dim: int,
    ):
        """Initialize a set-aware Q-network.

        Args:
            obs_dim: Total flattened observation dimension.
            action_dim: Number of actions.
            token_slice: Slice of the flattened observation that contains token rows.
            token_shape: ``(max_tokens, token_dim)`` for reshaping the token slice.
            token_embed_dim: Embedding size for pooled token features.
            base_hidden_dim: Embedding size for non-token observation features.
            q_head_hidden_dim: Hidden size for the Q-value head.
        """
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.token_slice = self._validate_token_slice(obs_dim, token_slice)
        self.max_tokens, self.token_dim = self._validate_token_shape(token_shape)
        self.token_embed_dim = token_embed_dim
        self.base_hidden_dim = base_hidden_dim

        expected_token_dims = self.max_tokens * self.token_dim
        if self.token_slice.stop - self.token_slice.start != expected_token_dims:
            raise ValueError(
                "token_slice length must equal max_tokens * token_dim "
                f"({expected_token_dims}), got {self.token_slice.stop - self.token_slice.start}"
            )
        if token_embed_dim <= 0:
            raise ValueError("token_embed_dim must be positive")
        if base_hidden_dim <= 0:
            raise ValueError("base_hidden_dim must be positive")
        if q_head_hidden_dim <= 0:
            raise ValueError("q_head_hidden_dim must be positive")

        self.base_dim = obs_dim - expected_token_dims
        if self.base_dim < 0:
            raise ValueError("token dimensions cannot exceed obs_dim")

        self.token_encoder = nn.Sequential(
            nn.Linear(self.token_dim, token_embed_dim),
            nn.LayerNorm(token_embed_dim),
            nn.ReLU(),
        )
        self.base_encoder: nn.Sequential | None
        if self.base_dim > 0:
            self.base_encoder = nn.Sequential(
                nn.Linear(self.base_dim, base_hidden_dim),
                nn.LayerNorm(base_hidden_dim),
                nn.ReLU(),
            )
            q_head_input_dim = token_embed_dim + base_hidden_dim
        else:
            self.base_encoder = None
            q_head_input_dim = token_embed_dim

        self.q_head = nn.Sequential(
            nn.Linear(q_head_input_dim, q_head_hidden_dim),
            nn.LayerNorm(q_head_hidden_dim),
            nn.ReLU(),
            nn.Linear(q_head_hidden_dim, action_dim),
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        """Encode non-token observations and a token set into Q-values."""
        if obs.dim() != 2 or obs.shape[1] != self.obs_dim:
            raise ValueError(f"Expected observations with shape [batch, {self.obs_dim}], got {tuple(obs.shape)}")

        token_flat = obs[:, self.token_slice]
        tokens = token_flat.reshape(obs.shape[0], self.max_tokens, self.token_dim)
        non_empty_mask = tokens.abs().sum(dim=-1, keepdim=True) > 0

        token_embeddings = self.token_encoder(tokens)
        token_embeddings = token_embeddings * non_empty_mask.to(dtype=token_embeddings.dtype)
        token_counts = non_empty_mask.sum(dim=1).clamp(min=1).to(dtype=token_embeddings.dtype)
        pooled_tokens = token_embeddings.sum(dim=1) / token_counts

        parts = []
        if self.base_encoder is not None:
            base_obs = torch.cat((obs[:, : self.token_slice.start], obs[:, self.token_slice.stop :]), dim=1)
            parts.append(self.base_encoder(base_obs))
        parts.append(pooled_tokens)

        return cast(torch.Tensor, self.q_head(torch.cat(parts, dim=1)))

    @staticmethod
    def _validate_token_slice(obs_dim: int, token_slice: slice) -> slice:
        if token_slice.step not in (None, 1):
            raise ValueError("token_slice step must be None or 1")
        if token_slice.start is None or token_slice.stop is None:
            raise ValueError("token_slice must have explicit start and stop")
        if token_slice.start < 0 or token_slice.stop > obs_dim or token_slice.stop <= token_slice.start:
            raise ValueError(f"token_slice must be within observation bounds 0..{obs_dim}")
        return slice(token_slice.start, token_slice.stop)

    @staticmethod
    def _validate_token_shape(token_shape: tuple[int, int]) -> tuple[int, int]:
        max_tokens, token_dim = token_shape
        if max_tokens <= 0:
            raise ValueError("token_shape max_tokens must be positive")
        if token_dim <= 0:
            raise ValueError("token_shape token_dim must be positive")
        return max_tokens, token_dim


class StructuredQNetwork(nn.Module):
    """
    Structured Q-Network with group encoders for semantic observation groups.

    Uses ObservationActivity to identify semantic groups (spatial, bars, affordances, temporal, custom)
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
        observation_activity: ObservationActivity,
        group_embed_dim: int = 32,
        q_head_hidden_dim: int = 128,
    ):
        """
        Initialize structured Q-network with group encoders.

        Args:
            obs_dim: Total observation dimension
            action_dim: Number of actions
            observation_activity: ObservationActivity with group_slices
            group_embed_dim: Embedding dimension for each group encoder (default 32)
            q_head_hidden_dim: Hidden dimension for final Q-head MLP (default 128)

        Note (PDR-002):
            Architecture parameters explicitly specified, no BAC defaults.
        """
        super().__init__()
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.observation_activity = observation_activity
        self.group_embed_dim = group_embed_dim

        # Create encoder for each semantic group
        self.group_encoders = nn.ModuleDict()
        total_embed_dim = 0

        for group_name, group_slice in observation_activity.group_slices.items():
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
            group_slice = self.observation_activity.group_slices[group_name]
            group_obs = obs[:, group_slice]
            group_embed = encoder(group_obs)
            group_embeddings.append(group_embed)

        # Concatenate all group embeddings
        combined = torch.cat(group_embeddings, dim=1)  # [batch, total_embed_dim]

        # Q-values
        q_values = self.q_head(combined)  # [batch, action_dim]

        return cast(torch.Tensor, q_values)
