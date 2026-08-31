"""
Sequential Replay Buffer for LSTM Training.

CRIT-07: Updated to use single 'rewards' field for DAC-composed totals.
Episodes store pre-composed total rewards with optional component breakdown.

The current exact artifact carries compact observation rows and the successor
of the last sampled index required for the boundary bootstrap.

Unlike standard replay buffers that sample individual transitions,
this buffer stores complete episodes and samples sequences of consecutive
transitions to maintain temporal structure for recurrent networks.
"""

from __future__ import annotations

import random
from collections import deque  # MED-02: Use deque for O(1) popleft
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch

Episode = dict[str, torch.Tensor]

SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION = 5
SEQUENTIAL_REPLAY_BUFFER_KIND = "sequential"
SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS = frozenset({"replay_kind", "format_version", "capacity", "num_transitions", "episodes"})
SEQUENTIAL_EPISODE_KEYS = frozenset(
    {
        "observations",
        "actions",
        "rewards",
        "dones",
        "next_observations",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
    }
)
_REQUIRED_EPISODE_KEYS = frozenset({"observations", "actions", "rewards", "dones", "next_observations"})
_COMPONENT_EPISODE_KEYS = frozenset({"rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"})


@dataclass(frozen=True)
class _SequentialRestoreCandidate:
    num_transitions: int
    episodes: deque[Episode]


@dataclass(frozen=True)
class _ValidatedSequentialState:
    num_transitions: int
    episodes: tuple[Episode, ...]


class SequentialReplayBuffer:
    """
    Replay buffer that maintains temporal structure for LSTM training.

    Episodes store single 'rewards' field with DAC-composed totals, plus optional
    component breakdown (rewards_extrinsic, rewards_intrinsic, rewards_shaping).

    Stores complete episodes and samples sequences of consecutive transitions.
    This is essential for training recurrent networks which need temporal context.

    Attributes:
        capacity: Maximum number of transitions to store
        device: Device to store tensors on
        episodes: List of stored episodes (each is a dict of tensors)
        num_transitions: Total number of transitions stored
    """

    def __init__(self, capacity: int, device: torch.device):
        """
        Initialize sequential replay buffer.

        Args:
            capacity: Maximum number of transitions to store
            device: Device to store tensors on (CPU or CUDA)

        Raises:
            ValueError: If capacity <= 0
        """
        # LOW-02: Validate positive capacity
        if capacity <= 0:
            raise ValueError(f"Buffer capacity must be positive, got {capacity}")

        self.capacity = capacity
        self.device = device
        self.episodes: deque[Episode] = deque()  # MED-02: deque for O(1) popleft
        self.num_transitions = 0

    def __len__(self) -> int:
        """Return number of episodes stored."""
        return len(self.episodes)

    def clear(self) -> None:
        """Reset buffer to empty state and deallocate all episode storage.

        Clears the episode deque and resets transition count to 0.
        Buffer can be reused after clearing.
        """
        self.episodes = deque()  # MED-02: Reset to empty deque
        self.num_transitions = 0

    def stats(self) -> dict[str, Any]:
        """Return buffer statistics for introspection.

        Returns:
            Dictionary with keys:
                - size: Total number of transitions stored (same as num_transitions)
                - capacity: Maximum buffer capacity in transitions
                - occupancy_ratio: num_transitions / capacity (0.0 to 1.0)
                - memory_bytes: Approximate memory usage in bytes
                - device: Device string (e.g., 'cpu', 'cuda:0')
                - num_episodes: Number of episodes stored
                - num_transitions: Total transitions across all episodes
        """
        # Calculate memory usage across all episodes
        memory_bytes = 0
        for episode in self.episodes:
            for tensor in episode.values():
                memory_bytes += tensor.element_size() * tensor.numel()

        # Calculate occupancy ratio
        occupancy_ratio = self.num_transitions / self.capacity if self.capacity > 0 else 0.0

        return {
            "size": self.num_transitions,
            "capacity": self.capacity,
            "occupancy_ratio": occupancy_ratio,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
            "num_episodes": len(self.episodes),
            "num_transitions": self.num_transitions,
        }

    def store_episode(self, episode: Episode) -> None:
        """
        Store a complete episode.

        CRIT-07: Now requires 'rewards' key with pre-composed totals.
        WS-1(c): 'next_observations' is REQUIRED - the boundary bootstrap needs the
        successor of every timestep, and a missing key must fail loudly, not default.
        Component keys (rewards_extrinsic, rewards_intrinsic, rewards_shaping) are optional.

        Args:
            episode: Dict with keys:
                - 'observations': [seq_len, obs_dim]
                - 'actions': [seq_len]
                - 'rewards': [seq_len] - DAC-composed total rewards
                - 'dones': [seq_len]
                - 'next_observations': [seq_len, obs_dim] - successor observations
                - 'rewards_extrinsic': [seq_len] (optional) - extrinsic component
                - 'rewards_intrinsic': [seq_len] (optional) - intrinsic component
                - 'rewards_shaping': [seq_len] (optional) - shaping component

        Raises:
            ValueError: If episode structure is invalid
        """
        # Validate episode structure
        episode_keys = set(episode)
        missing_keys = _REQUIRED_EPISODE_KEYS - episode_keys
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        unknown_keys = episode_keys - SEQUENTIAL_EPISODE_KEYS
        if unknown_keys:
            raise ValueError(f"Unknown episode keys: {unknown_keys}")

        # LOW-01: Validate episode has positive length
        seq_len = len(episode["observations"])
        if seq_len == 0:
            raise ValueError("Cannot store zero-length episode (no transitions)")

        # LOW-15: Validate tensor shapes for consistency
        for key, tensor in episode.items():
            if len(tensor) != seq_len:
                raise ValueError(f"Episode tensor length mismatch: observations has {seq_len} steps, but {key} has {len(tensor)} steps")

        # LOW-15: Validate tensor dimensionality
        if episode["observations"].ndim != 2:
            raise ValueError(f"observations must be 2D [seq_len, obs_dim], got shape {episode['observations'].shape}")
        if episode["observations"].dtype is not torch.float32:
            raise ValueError(f"observations must use dtype torch.float32, got {episode['observations'].dtype}")
        if episode["actions"].ndim != 1:
            raise ValueError(f"actions must be 1D [seq_len], got shape {episode['actions'].shape}")
        if episode["actions"].dtype is not torch.int64:
            raise ValueError(f"actions must use dtype torch.int64, got {episode['actions'].dtype}")
        if episode["rewards"].ndim != 1:
            raise ValueError(f"rewards must be 1D [seq_len], got shape {episode['rewards'].shape}")
        if episode["rewards"].dtype is not torch.float32:
            raise ValueError(f"rewards must use dtype torch.float32, got {episode['rewards'].dtype}")
        if episode["dones"].ndim != 1:
            raise ValueError(f"dones must be 1D [seq_len], got shape {episode['dones'].shape}")
        if episode["dones"].dtype is not torch.bool:
            raise ValueError(f"dones must use dtype torch.bool, got {episode['dones'].dtype}")
        if episode["next_observations"].ndim != 2:
            raise ValueError(f"next_observations must be 2D [seq_len, obs_dim], got shape {episode['next_observations'].shape}")
        if episode["next_observations"].dtype is not torch.float32:
            raise ValueError(f"next_observations must use dtype torch.float32, got {episode['next_observations'].dtype}")
        if episode["next_observations"].shape != episode["observations"].shape:
            raise ValueError(
                f"next_observations shape {tuple(episode['next_observations'].shape)} must equal "
                f"observations shape {tuple(episode['observations'].shape)}"
            )
        if self.episodes and episode["observations"].shape[1] != self.episodes[0]["observations"].shape[1]:
            raise ValueError(
                f"observations obs_dim ({episode['observations'].shape[1]}) != current buffer obs_dim "
                f"({self.episodes[0]['observations'].shape[1]})"
            )

        # Validate optional component keys if present
        for component_key in _COMPONENT_EPISODE_KEYS:
            if component_key in episode:
                if episode[component_key].ndim != 1:
                    raise ValueError(f"{component_key} must be 1D [seq_len], got shape {episode[component_key].shape}")
                if len(episode[component_key]) != seq_len:
                    comp_len = len(episode[component_key])
                    raise ValueError(
                        f"Episode tensor length mismatch: observations has {seq_len} steps, " f"but {component_key} has {comp_len} steps"
                    )
                if episode[component_key].dtype is not torch.float32:
                    raise ValueError(f"{component_key} must use dtype torch.float32, got {episode[component_key].dtype}")

        for field, tensor in episode.items():
            if tensor.dtype.is_floating_point and not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"{field} must contain only finite values")

        # Move episode to correct device
        episode_on_device: Episode = {key: tensor.to(self.device) for key, tensor in episode.items()}

        # Add episode
        self.episodes.append(episode_on_device)
        self.num_transitions += seq_len

        # MED-02: Evict oldest episodes if over capacity (O(1) popleft with deque)
        while self.num_transitions > self.capacity and len(self.episodes) > 0:
            oldest_episode = self.episodes.popleft()  # O(1) instead of O(n) pop(0)
            self.num_transitions -= len(oldest_episode["observations"])

    def sample_sequences(self, batch_size: int, seq_len: int) -> dict[str, torch.Tensor]:
        """
        Sample a batch of sequential transitions.

        CRIT-07: Rewards are already composed by DAC before storage.
        MED-13: Removed dead intrinsic_weight parameter (always 1.0 post-DAC).

        Args:
            batch_size: Number of sequences to sample
            seq_len: Length of each sequence

        Returns:
            Dict with keys:
                - 'observations': [batch_size, seq_len, obs_dim]
                - 'actions': [batch_size, seq_len]
                - 'rewards': [batch_size, seq_len]
                - 'dones': [batch_size, seq_len]
                - 'next_observations': [batch_size, seq_len, obs_dim] - successors
                  (WS-1(c): [:, -1] is the window-boundary bootstrap target)
                - 'mask': [batch_size, seq_len] bool - True for valid timesteps,
                          False after terminal (for post-terminal masking in loss)

        Raises:
            ValueError: If not enough data to sample
        """
        # Check if we have enough data
        if len(self.episodes) == 0:
            raise ValueError("Cannot sample: buffer is empty (not enough data)")

        # Find episodes long enough for the requested sequence length
        valid_episodes = [ep for ep in self.episodes if len(ep["observations"]) >= seq_len]

        if not valid_episodes:
            # Provide detailed error message for debugging
            episode_lengths = [len(ep["observations"]) for ep in self.episodes]
            max_length = max(episode_lengths) if episode_lengths else 0
            raise ValueError(
                f"Cannot sample: no episodes long enough for seq_len={seq_len}. "
                f"Buffer has {len(self.episodes)} episodes with lengths: {episode_lengths[:10]}"
                f"{' (showing first 10)' if len(episode_lengths) > 10 else ''}. "
                f"Max episode length: {max_length}. "
                f"Hint: If this occurs in tests that don't intend to test training, "
                f"disable training with train_frequency=10000 or use the "
                f"non_training_recurrent_population fixture."
            )

        # Sample batch_size sequences
        sampled_sequences = []

        # LOW-14: Weight episode selection by length for uniform transition sampling
        # Without weighting, short episodes are oversampled relative to their contribution
        episode_lengths = [len(ep["observations"]) for ep in valid_episodes]

        for _ in range(batch_size):
            # Randomly select an episode weighted by length (uniform transition sampling)
            episode = random.choices(valid_episodes, weights=episode_lengths, k=1)[0]

            # Randomly select a starting position (ensuring we can get seq_len transitions)
            ep_len = episode["observations"].shape[0]
            max_start = ep_len - seq_len
            start_idx = random.randint(0, max_start)
            end_idx = start_idx + seq_len

            # Extract sequence
            sequence = {
                "observations": episode["observations"][start_idx:end_idx],
                "actions": episode["actions"][start_idx:end_idx],
                "rewards": episode["rewards"][start_idx:end_idx],  # CRIT-07: Use pre-composed rewards
                "dones": episode["dones"][start_idx:end_idx],
                "next_observations": episode["next_observations"][start_idx:end_idx],
            }

            # Create validity mask (P2.2: Post-terminal masking)
            # Mask is True up to and including terminal, False after
            dones_seq = episode["dones"][start_idx:end_idx]
            mask = torch.ones(seq_len, dtype=torch.bool, device=self.device)

            # Find first terminal in sequence
            terminal_positions = torch.nonzero(dones_seq, as_tuple=False)
            if terminal_positions.numel() > 0:
                terminal_idx = int(terminal_positions[0].item())
                # Mask out everything AFTER terminal (terminal itself is valid)
                if terminal_idx < seq_len - 1:
                    mask[terminal_idx + 1 :] = False

            sequence["mask"] = mask

            sampled_sequences.append(sequence)

        # Stack sequences into batch
        batch = {
            "observations": torch.stack([s["observations"] for s in sampled_sequences]),
            "actions": torch.stack([s["actions"] for s in sampled_sequences]),
            "rewards": torch.stack([s["rewards"] for s in sampled_sequences]),
            "dones": torch.stack([s["dones"] for s in sampled_sequences]),
            "next_observations": torch.stack([s["next_observations"] for s in sampled_sequences]),
            "mask": torch.stack([s["mask"] for s in sampled_sequences]),
        }

        return batch

    def serialize(self) -> dict[str, Any]:
        """Serialize the exact current sequential replay artifact."""
        if len(self.episodes) == 0:
            return {
                "replay_kind": SEQUENTIAL_REPLAY_BUFFER_KIND,
                "format_version": SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION,
                "capacity": self.capacity,
                "num_transitions": 0,
                "episodes": [],
            }

        serialized_episodes: list[dict[str, torch.Tensor | None]] = []
        for episode in self.episodes:
            serialized_episode: dict[str, torch.Tensor | None] = {
                "observations": episode["observations"].cpu(),
                "actions": episode["actions"].cpu(),
                "rewards": episode["rewards"].cpu(),
                "dones": episode["dones"].cpu(),
                "next_observations": episode["next_observations"].cpu(),
                "rewards_extrinsic": None,
                "rewards_intrinsic": None,
                "rewards_shaping": None,
            }
            for key in _COMPONENT_EPISODE_KEYS:
                if key in episode:
                    serialized_episode[key] = episode[key].cpu()
            serialized_episodes.append(serialized_episode)

        return {
            "replay_kind": SEQUENTIAL_REPLAY_BUFFER_KIND,
            "format_version": SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION,
            "capacity": self.capacity,
            "num_transitions": self.num_transitions,
            "episodes": serialized_episodes,
        }

    @staticmethod
    def _require_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Sequential checkpoint {field} must be an integer; got {value!r}. Regenerate the checkpoint.")
        if not minimum <= value <= maximum:
            raise ValueError(f"Sequential checkpoint {field}={value} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return value

    @staticmethod
    def _require_tensor(episode: Mapping[str, Any], field: str, *, dtype: torch.dtype, shape: tuple[int, ...]) -> torch.Tensor:
        value = episode[field]
        if not isinstance(value, torch.Tensor):
            raise ValueError(
                f"Sequential checkpoint episode {field} must be a tensor; got {type(value).__name__}. Regenerate the checkpoint."
            )
        if value.dtype is not dtype:
            raise ValueError(f"Sequential checkpoint episode {field} dtype is {value.dtype}; expected {dtype}. Regenerate the checkpoint.")
        if tuple(value.shape) != shape:
            raise ValueError(
                f"Sequential checkpoint episode {field} shape is {tuple(value.shape)}; expected {shape}. Regenerate the checkpoint."
            )
        if dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"Sequential checkpoint episode {field} must contain only finite values. Regenerate the checkpoint.")
        return value

    def _validate_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _ValidatedSequentialState:
        if not isinstance(state, Mapping):
            raise ValueError(f"Sequential replay checkpoint payload must be a mapping; got {type(state).__name__}.")
        format_version = state.get("format_version")
        if type(format_version) is not int or format_version != SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION:
            raise ValueError(
                f"Cannot load sequential buffer checkpoint with format_version {format_version!r}; "
                f"the exact current format_version is {SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION}. Regenerate the checkpoint."
            )
        replay_kind = state.get("replay_kind")
        if replay_kind != SEQUENTIAL_REPLAY_BUFFER_KIND:
            raise ValueError(
                f"Sequential checkpoint replay_kind is {replay_kind!r}; expected {SEQUENTIAL_REPLAY_BUFFER_KIND!r}. "
                "Regenerate the checkpoint."
            )
        state_keys = set(state)
        if state_keys != SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS:
            missing = sorted(SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS - state_keys)
            unknown = sorted(state_keys - SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS)
            raise ValueError(f"Sequential checkpoint key set mismatch: missing={missing}, unknown={unknown}. Regenerate the checkpoint.")
        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        if capacity != self.capacity:
            raise ValueError(
                f"Sequential checkpoint capacity is {capacity}; current capacity is {self.capacity}. Regenerate the checkpoint."
            )
        num_transitions = self._require_int(state["num_transitions"], "num_transitions", minimum=0, maximum=self.capacity)
        serialized_episodes = state["episodes"]
        if not isinstance(serialized_episodes, list):
            raise ValueError("Sequential checkpoint episodes must be a list. Regenerate the checkpoint.")
        if num_transitions == 0 and serialized_episodes:
            raise ValueError("Empty sequential checkpoint must contain no episodes. Regenerate the checkpoint.")

        current_obs_dim = self.episodes[0]["observations"].shape[1] if self.episodes else None
        validated_episodes: list[Episode] = []
        observed_transitions = 0
        observed_obs_dim: int | None = None
        for episode_index, episode_state in enumerate(serialized_episodes):
            if not isinstance(episode_state, Mapping):
                raise ValueError(f"Sequential checkpoint episode {episode_index} must be a mapping. Regenerate the checkpoint.")
            episode_keys = set(episode_state)
            if episode_keys != SEQUENTIAL_EPISODE_KEYS:
                missing = sorted(SEQUENTIAL_EPISODE_KEYS - episode_keys)
                unknown = sorted(episode_keys - SEQUENTIAL_EPISODE_KEYS)
                raise ValueError(
                    f"Sequential checkpoint episode {episode_index} key set mismatch: missing={missing}, unknown={unknown}. "
                    "Regenerate the checkpoint."
                )
            observations_value = episode_state["observations"]
            if not isinstance(observations_value, torch.Tensor) or observations_value.ndim != 2:
                raise ValueError(
                    f"Sequential checkpoint episode {episode_index} observations must be a 2D tensor. Regenerate the checkpoint."
                )
            seq_len, obs_dim = observations_value.shape
            if seq_len <= 0 or obs_dim <= 0:
                raise ValueError("Sequential checkpoint episodes require positive sequence and observation dimensions.")
            if observed_obs_dim is None:
                observed_obs_dim = obs_dim
            if obs_dim != observed_obs_dim:
                raise ValueError(
                    f"Sequential checkpoint episode {episode_index} obs_dim is {obs_dim}; expected {observed_obs_dim}. "
                    "Regenerate the checkpoint."
                )
            if current_obs_dim is not None and obs_dim != current_obs_dim:
                raise ValueError(
                    f"Sequential checkpoint obs_dim is {obs_dim}; expected current obs_dim {current_obs_dim}. " "Regenerate the checkpoint."
                )
            if expected_obs_dim is not None and obs_dim != expected_obs_dim:
                raise ValueError(
                    f"Sequential checkpoint obs_dim is {obs_dim}; expected environment obs_dim {expected_obs_dim}. "
                    "Regenerate the checkpoint."
                )

            observations = self._require_tensor(episode_state, "observations", dtype=torch.float32, shape=(seq_len, obs_dim))
            actions = self._require_tensor(episode_state, "actions", dtype=torch.int64, shape=(seq_len,))
            rewards = self._require_tensor(episode_state, "rewards", dtype=torch.float32, shape=(seq_len,))
            dones = self._require_tensor(episode_state, "dones", dtype=torch.bool, shape=(seq_len,))
            next_observations = self._require_tensor(episode_state, "next_observations", dtype=torch.float32, shape=(seq_len, obs_dim))
            episode: Episode = {
                "observations": observations,
                "actions": actions,
                "rewards": rewards,
                "dones": dones,
                "next_observations": next_observations,
            }
            for component_key in _COMPONENT_EPISODE_KEYS:
                component = episode_state[component_key]
                if component is not None:
                    component_tensor = self._require_tensor(episode_state, component_key, dtype=torch.float32, shape=(seq_len,))
                    episode[component_key] = component_tensor
            validated_episodes.append(episode)
            observed_transitions += seq_len

        if observed_transitions != num_transitions:
            raise ValueError(
                f"Sequential checkpoint num_transitions is {num_transitions}; episode lengths total {observed_transitions}. "
                "Regenerate the checkpoint."
            )
        return _ValidatedSequentialState(num_transitions, tuple(validated_episodes))

    def _materialize_serialized(self, state: _ValidatedSequentialState) -> _SequentialRestoreCandidate:
        episodes: deque[Episode] = deque()
        for episode in state.episodes:
            episodes.append({key: tensor.to(self.device).clone() for key, tensor in episode.items()})
        return _SequentialRestoreCandidate(state.num_transitions, episodes)

    def _prepare_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _SequentialRestoreCandidate:
        validated = self._validate_serialized(state, expected_obs_dim=expected_obs_dim)
        return self._materialize_serialized(validated)

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int) -> _ValidatedSequentialState:
        """Validate exact structure without cloning episode tensors or mutating this buffer."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedSequentialState) -> _SequentialRestoreCandidate:
        """Materialize one restore candidate from already validated structure."""
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _SequentialRestoreCandidate:
        """Validate and materialize the one candidate that will be installed."""
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _SequentialRestoreCandidate) -> None:
        """Install a fully validated, already materialized restore candidate."""
        self.num_transitions = candidate.num_transitions
        self.episodes = candidate.episodes

    def load_from_serialized(self, state: Mapping[str, Any]) -> None:
        """Restore only after the complete exact-current artifact validates."""
        self.load_prepared(self.prepare_serialized(state, expected_obs_dim=None))
