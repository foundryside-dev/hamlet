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

import numpy as np
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.training import historical_checkpoint as history
from townlet.training.replay_contract import (
    HistoricalLegalityUnavailable,
    ReplayBatch,
    ReplayReadiness,
    ReplayRequest,
    SamplingReceipt,
    validate_successor_masks,
)

Episode = dict[str, Any]

SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION = 6
SEQUENTIAL_REPLAY_BUFFER_KIND = "sequential"
_LEGACY_VERSION = 5
_LEGACY_STATE_KEYS = frozenset({"replay_kind", "format_version", "capacity", "num_transitions", "episodes"})
_INSPECTION_KEYS = frozenset({"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"})
_INSPECTION_MARKERS = frozenset({"inspection_kind", "inspection_version", "legacy_transport"})
_INSPECTION_KIND = "sequential_replay_inspection"
SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS = _LEGACY_STATE_KEYS | {
    "action_dim",
    "legality_mode",
    "replay_options",
    "next_episode_id",
    "next_transition_id",
    "historical_archives",
}
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
_CURRENT_EPISODE_KEYS = SEQUENTIAL_EPISODE_KEYS | {
    "next_action_masks",
    "legality_recorded",
    "episode_id",
    "start_offset",
    "original_length",
    "transition_ids",
}
_MAX_ID = 2**63 - 1


@dataclass(frozen=True, slots=True)
class SequentialReplayBatch(ReplayBatch):
    """Component values are recorded only under true real-row presence bits."""

    rewards_extrinsic_present: torch.Tensor
    rewards_intrinsic_present: torch.Tensor
    rewards_shaping_present: torch.Tensor

    def __post_init__(self) -> None:
        ReplayBatch.__post_init__(self)
        if self.observations.ndim != 3:
            raise ValueError("sequential batches require [B,L,D] observations")
        real = torch.arange(self.actions.shape[1], device=self.actions.device)[None, :] < self.lengths[:, None]
        for name in _COMPONENT_EPISODE_KEYS:
            present, value = getattr(self, f"{name}_present"), getattr(self, name)
            if not isinstance(present, torch.Tensor) or present.dtype != torch.bool:
                raise ValueError(f"{name}_present must be a bool tensor")
            if present.shape != self.rewards.shape or present.device != self.rewards.device or bool((present & ~real).any()):
                raise ValueError(f"{name}_present must match real reward rows without padded presence")
            if value is None:
                if bool(present.any()):
                    raise ValueError(f"{name} omits recorded component values")
            elif not bool(present.any()) or bool((value[~present] != 0).any()):
                raise ValueError(f"{name} requires None when absent and zero unrecorded placeholders")
            object.__setattr__(self, f"{name}_present", present.detach().clone())


@dataclass(frozen=True)
class _SequentialRestoreCandidate:
    num_transitions: int
    episodes: deque[Episode]


@dataclass(frozen=True)
class _ValidatedSequentialState:
    num_transitions: int
    episodes: tuple[Episode, ...]


@dataclass(frozen=True)
class _ValidatedLegacyState(_ValidatedSequentialState):
    original_state: Mapping[str, Any]


@dataclass(frozen=True)
class _ValidatedInspectionState(_ValidatedSequentialState):
    archives: tuple[history.HistoricalReplayArchive, ...]


@dataclass(frozen=True)
class _ValidatedCapturedState(_ValidatedSequentialState):
    action_dim: int
    legality_mode: str
    replay_options: ReplayOptions
    next_episode_id: int
    next_transition_id: int
    archives: tuple[history.HistoricalReplayArchive, ...]


@dataclass(frozen=True)
class _PreparedSequenceState(_SequentialRestoreCandidate):
    capacity: int
    device: torch.device
    configured: bool
    action_dim: int | None
    legality_mode: str
    replay_options: ReplayOptions | None
    next_episode_id: int
    next_transition_id: int
    archives: tuple[history.HistoricalReplayArchive, ...]


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
        self._configured = False
        self.action_dim: int | None = None
        self.legality_mode = "legacy"
        self.replay_options: ReplayOptions | None = None
        self.next_episode_id = self.next_transition_id = 0
        self._historical_archives: tuple[history.HistoricalReplayArchive, ...] = ()

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
                if isinstance(tensor, torch.Tensor):
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
            "retained_transitions": self.retained_transitions,
            "legacy_transport_transitions": self.legacy_transport_transitions,
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
        if self._configured:
            if self.legality_mode != "unconstrained":
                raise HistoricalLegalityUnavailable("captured replay requires store_captured_episode with actual successor legality")
            assert self.action_dim is not None
            if not isinstance(episode, Mapping):
                raise ValueError("unconstrained episode must be a mapping with bool dones")
            dones = episode.get("dones")
            if not isinstance(dones, torch.Tensor) or dones.dtype != torch.bool or dones.ndim != 1:
                raise ValueError("unconstrained episode requires bool[rows] dones")
            masks = torch.ones((*dones.shape, self.action_dim), dtype=torch.bool, device=dones.device)
            recorded = torch.ones_like(dones, dtype=torch.bool)
            self.store_captured_episode(episode, next_action_masks=masks, legality_recorded=recorded)
            return
        # Validate the preserved newly-authored legacy transport domain.
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
        episode_on_device: Episode = {key: tensor.detach().to(self.device).clone() for key, tensor in episode.items()}

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
        """Own exact5 inspection, archive-bearing inspection, or qualified6 state."""
        if self._configured:
            return self._serialize_current()
        transport = self._serialize_legacy_transport()
        if self._historical_archives:
            return {
                "inspection_kind": _INSPECTION_KIND,
                "inspection_version": 1,
                "legacy_transport": transport,
                "historical_archives": [history._record(archive) for archive in self._historical_archives],
            }
        return transport

    def _serialize_legacy_transport(self) -> dict[str, Any]:
        """Preserve the closed history-free legacy5 row representation."""
        if len(self.episodes) == 0:
            return {
                "replay_kind": SEQUENTIAL_REPLAY_BUFFER_KIND,
                "format_version": _LEGACY_VERSION,
                "capacity": self.capacity,
                "num_transitions": 0,
                "episodes": [],
            }

        serialized_episodes: list[dict[str, torch.Tensor | None]] = []
        for episode in self.episodes:
            serialized_episode: dict[str, torch.Tensor | None] = {
                "observations": episode["observations"].detach().cpu().clone(),
                "actions": episode["actions"].detach().cpu().clone(),
                "rewards": episode["rewards"].detach().cpu().clone(),
                "dones": episode["dones"].detach().cpu().clone(),
                "next_observations": episode["next_observations"].detach().cpu().clone(),
                "rewards_extrinsic": None,
                "rewards_intrinsic": None,
                "rewards_shaping": None,
            }
            for key in _COMPONENT_EPISODE_KEYS:
                if key in episode:
                    serialized_episode[key] = episode[key].detach().cpu().clone()
            serialized_episodes.append(serialized_episode)

        return {
            "replay_kind": SEQUENTIAL_REPLAY_BUFFER_KIND,
            "format_version": _LEGACY_VERSION,
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

    def _validate_legacy_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _ValidatedSequentialState:
        if not isinstance(state, Mapping):
            raise ValueError(f"Sequential replay checkpoint payload must be a mapping; got {type(state).__name__}.")
        format_version = state.get("format_version")
        if type(format_version) is not int or format_version != _LEGACY_VERSION:
            raise ValueError(
                f"Cannot load sequential buffer checkpoint with format_version {format_version!r}; "
                f"the exact legacy format_version is {_LEGACY_VERSION}. Regenerate the checkpoint."
            )
        replay_kind = state.get("replay_kind")
        if replay_kind != SEQUENTIAL_REPLAY_BUFFER_KIND:
            raise ValueError(
                f"Sequential checkpoint replay_kind is {replay_kind!r}; expected {SEQUENTIAL_REPLAY_BUFFER_KIND!r}. "
                "Regenerate the checkpoint."
            )
        state_keys = set(state)
        if state_keys != _LEGACY_STATE_KEYS:
            missing = sorted(_LEGACY_STATE_KEYS - state_keys)
            unknown = sorted(state_keys - _LEGACY_STATE_KEYS)
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
        return _ValidatedLegacyState(num_transitions, tuple(validated_episodes), history._clone(state))

    def _materialize_serialized(self, state: _ValidatedSequentialState) -> _SequentialRestoreCandidate:
        if isinstance(state, _ValidatedLegacyState):
            archive = history.archive_standalone_replay(state.original_state)
            return self._empty_prepared(self._merge_archives((archive,), expected_obs_dim=None))
        if isinstance(state, _ValidatedInspectionState):
            if self._configured:
                raise HistoricalLegalityUnavailable("inspection transport requires the unconfigured two-argument inspection route")
            transport = deque(self._own_fragment(episode, device=self.device) for episode in state.episodes)
            width = None
            if transport:
                width = transport[0]["observations"].shape[1]
            archives = self._merge_archives(state.archives, expected_obs_dim=width)
            return _PreparedSequenceState(
                state.num_transitions,
                transport,
                self.capacity,
                self.device,
                False,
                None,
                "legacy",
                None,
                self.next_episode_id,
                self.next_transition_id,
                archives,
            )
        if not isinstance(state, _ValidatedCapturedState):
            raise ValueError("Sequential materialization requires validated replay state")
        episodes: deque[Episode] = deque()
        for episode in state.episodes:
            episodes.append(self._own_fragment(episode, device=self.device))
        width = None
        if episodes:
            width = episodes[0]["observations"].shape[1]
        archives = self._merge_archives(state.archives, expected_obs_dim=width)
        return _PreparedSequenceState(
            state.num_transitions,
            episodes,
            self.capacity,
            self.device,
            True,
            state.action_dim,
            state.legality_mode,
            state.replay_options.model_copy(deep=True),
            state.next_episode_id,
            state.next_transition_id,
            archives,
        )

    def _prepare_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _SequentialRestoreCandidate:
        validated = self._validate_serialized(state, expected_obs_dim=expected_obs_dim)
        return self._materialize_serialized(validated)

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedSequentialState:
        """Pure structural inspection of exact old5/current6; no materialization or installation."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedSequentialState) -> _SequentialRestoreCandidate:
        """Materialize one restore candidate from already validated structure."""
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _SequentialRestoreCandidate:
        """Validate and materialize the one candidate that will be installed."""
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _SequentialRestoreCandidate) -> None:
        """Install a fully validated, already materialized restore candidate."""
        if not isinstance(candidate, _PreparedSequenceState) or candidate.capacity != self.capacity or candidate.device != self.device:
            raise ValueError("Sequential installation requires a compatible prepared replay candidate")
        if self._configured and (
            not candidate.configured
            or candidate.action_dim != self.action_dim
            or candidate.legality_mode != self.legality_mode
            or candidate.replay_options != self.replay_options
        ):
            raise ValueError("prepared replay cannot downgrade or replace the target's configured geometry/options")
        for archive in self._historical_archives:
            if not any(item.source_digest == archive.source_digest for item in candidate.archives):
                raise ValueError("prepared replay cannot discard retained target history; prepare again against the current target")
        self.num_transitions = candidate.num_transitions
        self.episodes = candidate.episodes
        self._configured, self.action_dim, self.legality_mode = candidate.configured, candidate.action_dim, candidate.legality_mode
        self.replay_options = candidate.replay_options
        self.next_episode_id, self.next_transition_id = candidate.next_episode_id, candidate.next_transition_id
        self._historical_archives = candidate.archives

    def load_from_serialized(self, state: Mapping[str, Any]) -> None:
        """Restore only after the complete exact-current artifact validates."""
        self.load_prepared(self.prepare_serialized(state, expected_obs_dim=None))

    @staticmethod
    def _resolved_options(value: object) -> ReplayOptions:
        if isinstance(value, ReplayOptions):
            result = value.model_copy(deep=True)
        elif isinstance(value, Mapping):
            if set(value) != set(ReplayOptions.model_fields):
                raise ValueError("replay_options must contain every resolved replay field exactly")
            result = ReplayOptions.model_validate(dict(value))
        else:
            raise ValueError("replay_options must be fully resolved ReplayOptions or its exact mapping")
        if any(item is None for item in result.model_dump().values()):
            raise ValueError("qualified replay requires fully resolved replay_options; resolve omissions before construction")
        return result

    @classmethod
    def for_replay(
        cls, capacity: int, device: torch.device, *, options: ReplayOptions, action_dim: int, legality_mode: str
    ) -> SequentialReplayBuffer:
        if type(capacity) is not int or type(action_dim) is not int:
            raise ValueError("qualified capacity and action_dim must be exact integers")
        cls._require_int(capacity, "capacity", minimum=1, maximum=_MAX_ID)
        cls._require_int(action_dim, "action_dim", minimum=1, maximum=_MAX_ID)
        if type(legality_mode) is not str or legality_mode not in ("captured", "unconstrained"):
            raise ValueError("qualified legality_mode must be captured or explicitly unconstrained")
        policy = cls._resolved_options(options)
        result = cls(capacity, device)
        result._configured, result.action_dim, result.legality_mode = True, action_dim, legality_mode
        result.replay_options = policy
        return result

    @property
    def retained_transitions(self) -> int:
        if self._configured:
            return self.num_transitions
        return 0

    @property
    def legacy_transport_transitions(self) -> int:
        if self._configured:
            return 0
        return self.num_transitions

    def _configuration(self) -> tuple[ReplayOptions, int]:
        if not self._configured or self.replay_options is None or self.action_dim is None:
            raise HistoricalLegalityUnavailable(
                "qualified sequence replay needs for_replay with resolved options and declared action_dim; legacy transport has no masks"
            )
        return self.replay_options, self.action_dim

    def _observation_width(self) -> int | None:
        if self.episodes:
            return int(self.episodes[0]["observations"].shape[1])
        for archive in self._historical_archives:
            episodes = archive.original_state["episodes"]
            if isinstance(episodes, list) and episodes:
                return int(episodes[0]["observations"].shape[1])
        return None

    @staticmethod
    def _own_fragment(episode: Episode, *, device: torch.device) -> Episode:
        result: Episode = {}
        for key, value in episode.items():
            if isinstance(value, torch.Tensor):
                result[key] = value.detach().to(device).clone()
            else:
                result[key] = history._clone(value)
        return result

    @classmethod
    def _captured_rows(
        cls,
        episode: Mapping[str, Any],
        masks: torch.Tensor,
        recorded: torch.Tensor,
        *,
        action_dim: int,
        legality_mode: str,
        expected_obs_dim: int | None,
    ) -> Episode:
        if not isinstance(episode, Mapping) or not _REQUIRED_EPISODE_KEYS <= set(episode) or set(episode) - SEQUENTIAL_EPISODE_KEYS:
            raise ValueError("captured episode requires the existing row fields and only supported optional components")
        observations = episode["observations"]
        if not isinstance(observations, torch.Tensor) or observations.ndim != 2:
            raise ValueError("captured observations must be float32 [rows, obs_dim]")
        count, width = observations.shape
        if count < 1 or width < 1:
            raise ValueError("captured episodes require positive real row count and observation width")
        if expected_obs_dim is not None and width != expected_obs_dim:
            raise ValueError("captured observation width differs from configured/current replay geometry")
        rows: Episode = {}
        for name in SEQUENTIAL_EPISODE_KEYS:
            if name in _COMPONENT_EPISODE_KEYS and (name not in episode or episode[name] is None):
                rows[name] = None
                continue
            shape: tuple[int, ...] = (count,)
            dtype = torch.float32
            if name in ("observations", "next_observations"):
                shape = (count, width)
            elif name == "actions":
                dtype = torch.int64
            elif name == "dones":
                dtype = torch.bool
            value = cls._require_tensor(episode, name, dtype=dtype, shape=shape)
            if value.device != observations.device:
                raise ValueError("captured row tensors must have one device")
            rows[name] = value
        actions, dones = rows["actions"], rows["dones"]
        if bool(((actions < 0) | (actions >= action_dim)).any()):
            raise ValueError("captured actions are outside the declared action vocabulary")
        if bool(dones[:-1].any()):
            raise ValueError("captured real episode rows cannot continue after a terminal")
        validate_successor_masks(masks, dones, action_dim=action_dim)
        if not isinstance(recorded, torch.Tensor) or recorded.dtype != torch.bool or recorded.shape != (count,):
            raise ValueError("legality_recorded must be bool[real_rows]")
        if recorded.device != observations.device or not bool(recorded.all()):
            raise HistoricalLegalityUnavailable("every captured real successor needs owned recorded legality on its row device")
        if legality_mode == "unconstrained" and not bool(masks.all()):
            raise ValueError("explicit unconstrained replay declares every action legal")
        rows["next_action_masks"], rows["legality_recorded"] = masks, recorded
        return rows

    def store_captured_episode(
        self, episode: Mapping[str, Any], *, next_action_masks: torch.Tensor, legality_recorded: torch.Tensor
    ) -> None:
        policy, action_dim = self._configuration()
        width = self._observation_width()
        rows = self._captured_rows(
            episode,
            next_action_masks,
            legality_recorded,
            action_dim=action_dim,
            legality_mode=self.legality_mode,
            expected_obs_dim=width,
        )
        count = len(rows["actions"])
        if self.next_episode_id >= _MAX_ID or self.next_transition_id + count > _MAX_ID:
            raise ValueError("qualified replay stable identity range exhausted before admission")
        owned = self._own_fragment(rows, device=self.device)
        owned.update(
            episode_id=self.next_episode_id,
            start_offset=0,
            original_length=count,
            transition_ids=torch.arange(self.next_transition_id, self.next_transition_id + count, dtype=torch.int64, device=self.device),
        )
        retained = deque(self.episodes)
        retained.append(owned)
        total = self.num_transitions + count
        while total > self.capacity:
            first = retained[0]
            length = len(first["actions"])
            excess = total - self.capacity
            if policy.retention_mode == "whole_episode" or excess >= length:
                retained.popleft()
                total -= length
            else:
                tail = {}
                for key, value in first.items():
                    if isinstance(value, torch.Tensor):
                        tail[key] = value[excess:].detach().clone()
                    else:
                        tail[key] = value
                tail["start_offset"] = first["start_offset"] + excess
                retained[0] = tail
                total -= excess
        self.episodes, self.num_transitions = retained, total
        self.next_episode_id += 1
        self.next_transition_id += count

    def _check_request(self, request: ReplayRequest) -> ReplayOptions:
        policy, _ = self._configuration()
        if not isinstance(request, ReplayRequest):
            raise ValueError("sequence replay requires ReplayRequest")
        if (request.sequence_mode, request.sequence_objective, request.sampling_mode) != (
            policy.sequence_mode,
            policy.sequence_objective,
            policy.sampling_mode,
        ):
            raise ValueError("sequence request modes must match the persisted resolved replay_options")
        return policy

    def _sampleable(self, request: ReplayRequest) -> tuple[list[Episode], int]:
        valid = []
        count = 0
        for episode in self.episodes:
            length = len(episode["actions"])
            if request.sequence_mode == "adaptive_prefix":
                valid.append(episode)
                count += length
            elif length >= request.sequence_length:
                valid.append(episode)
                count += length - request.sequence_length + 1
        return valid, count

    def readiness(self, request: ReplayRequest) -> ReplayReadiness:
        self._check_request(request)
        _, population = self._sampleable(request)
        if request.sequence_mode == "fixed_full" and request.sequence_length > self.capacity:
            return ReplayReadiness(False, self.retained_transitions, population, "capacity_window_impossible")
        if self.retained_transitions < request.min_transitions:
            return ReplayReadiness(False, self.retained_transitions, population, "warmup")
        if not population:
            return ReplayReadiness(False, self.retained_transitions, 0, "window_unavailable")
        return ReplayReadiness(True, self.retained_transitions, population, "ready")

    def sample_batch(self, request: ReplayRequest) -> SequentialReplayBatch:
        ready = self.readiness(request)
        if not ready.ready:
            raise ValueError(
                f"sequence replay unavailable: {ready.reason}; retained={ready.retained_transitions}, sampleable={ready.sampleable_units}"
            )
        policy, action_dim = self._configuration()
        valid, population = self._sampleable(request)
        lengths = [len(episode["actions"]) for episode in valid]
        total = sum(lengths)
        windows: list[tuple[Episode, int, int]] = []
        legacy = policy.uniform_sequence_adapter == "legacy_episode_length_with_replacement"
        if not legacy:
            for episode in valid:
                for endpoint in range(len(episode["actions"])):
                    if request.sequence_mode == "fixed_full" and endpoint + 1 < request.sequence_length:
                        continue
                    windows.append((episode, max(0, endpoint + 1 - request.sequence_length), endpoint + 1))
        selected: list[tuple[Episode, int, int]] = []
        proposals = np.empty(request.batch_size, dtype=np.float64)
        weights = np.ones(request.batch_size, dtype=np.float64)
        nonuniform = legacy and request.sequence_mode == "fixed_full" and request.sequence_length != 1 and len(set(lengths)) > 1
        for index in range(request.batch_size):
            if legacy:
                episode = random.choices(valid, weights=lengths, k=1)[0]
                length = len(episode["actions"])
                if request.sequence_mode == "fixed_full":
                    start = random.randint(0, length - request.sequence_length)
                    end = start + request.sequence_length
                    probability = length / (total * (length - request.sequence_length + 1))
                else:
                    end = random.randint(0, length - 1) + 1
                    start = max(0, end - request.sequence_length)
                    probability = 1.0 / population
            else:
                episode, start, end = random.choice(windows)
                probability = 1.0 / population
            selected.append((episode, start, end))
            proposals[index] = probability
            if nonuniform:
                weights[index] = 1.0 / (population * probability)
        batch, length = request.batch_size, request.sequence_length
        width = valid[0]["observations"].shape[1]
        tensors: dict[str, Any] = {}
        for name in _REQUIRED_EPISODE_KEYS:
            shape: tuple[int, ...] = (batch, length)
            dtype = torch.float32
            if name in ("observations", "next_observations"):
                shape = (batch, length, width)
            elif name == "actions":
                dtype = torch.int64
            elif name == "dones":
                dtype = torch.bool
            tensors[name] = torch.zeros(shape, dtype=dtype, device=self.device)
        tensors["next_action_masks"] = torch.zeros((batch, length, action_dim), dtype=torch.bool, device=self.device)
        tensors["legality_recorded"] = torch.zeros((batch, length), dtype=torch.bool, device=self.device)
        tensors["loss_mask"] = torch.zeros((batch, length), dtype=torch.bool, device=self.device)
        for name in _COMPONENT_EPISODE_KEYS:
            tensors[name] = None
            if any(episode[name] is not None for episode, _, _ in selected):
                tensors[name] = torch.zeros((batch, length), dtype=torch.float32, device=self.device)
            tensors[f"{name}_present"] = torch.zeros((batch, length), dtype=torch.bool, device=self.device)
        real_lengths = torch.empty(batch, dtype=torch.int64, device=self.device)
        ids = np.empty(batch, dtype=np.int64)
        for index, (episode, start, end) in enumerate(selected):
            size = end - start
            real_lengths[index] = size
            ids[index] = int(episode["transition_ids"][end - 1])
            for name in (*_REQUIRED_EPISODE_KEYS, "next_action_masks", "legality_recorded"):
                tensors[name][index, :size].copy_(episode[name][start:end])
            if request.sequence_objective == "window_mean":
                tensors["loss_mask"][index, :size].fill_(True)
            else:
                tensors["loss_mask"][index, size - 1] = True
            for name in _COMPONENT_EPISODE_KEYS:
                if episode[name] is not None:
                    tensors[name][index, :size].copy_(episode[name][start:end])
                    tensors[f"{name}_present"][index, :size].fill_(True)
        rule = "uniform"
        if nonuniform:
            rule = "inverse_population_proposal"
        objective = "window"
        if request.sequence_objective == "anchor_transition":
            objective = "anchor_transition"
        assert policy.uniform_sequence_adapter is not None
        receipt = SamplingReceipt(ids, weights, population, proposals, policy.uniform_sequence_adapter, objective, rule)
        return SequentialReplayBatch(
            **tensors,
            lengths=real_lengths,
            unit_ids=torch.from_numpy(ids.copy()).to(self.device),
            weights=torch.from_numpy(weights.copy()).to(self.device),
            sampling=receipt,
        )

    def _serialize_current(self) -> dict[str, Any]:
        policy, action_dim = self._configuration()
        return {
            "replay_kind": SEQUENTIAL_REPLAY_BUFFER_KIND,
            "format_version": SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION,
            "capacity": self.capacity,
            "num_transitions": self.num_transitions,
            "action_dim": action_dim,
            "legality_mode": self.legality_mode,
            "replay_options": policy.model_dump(),
            "next_episode_id": self.next_episode_id,
            "next_transition_id": self.next_transition_id,
            "episodes": [self._own_fragment(episode, device=torch.device("cpu")) for episode in self.episodes],
            "historical_archives": [history._record(archive) for archive in self._historical_archives],
        }

    def _own_archive(self, archive: history.HistoricalReplayArchive, *, expected_obs_dim: int | None) -> history.HistoricalReplayArchive:
        if not isinstance(archive, history.HistoricalReplayArchive):
            raise ValueError("sequence archive must be a HistoricalReplayArchive")
        owned = history._archive_from_state(history._record(archive))
        if owned.source_formats["replay_kind"] != SEQUENTIAL_REPLAY_BUFFER_KIND:
            raise ValueError("historical archive replay kind differs from sequential storage")
        original = owned.original_state
        capacity = self._require_int(original["capacity"], "archive.capacity", minimum=1, maximum=_MAX_ID)
        validator = SequentialReplayBuffer(capacity, torch.device("cpu"))
        validator.validate_serialized(original, expected_obs_dim=expected_obs_dim)
        return owned

    @property
    def historical_archives(self) -> tuple[history.HistoricalReplayArchive, ...]:
        return tuple(self._own_archive(archive, expected_obs_dim=None) for archive in self._historical_archives)

    def _merge_archives(
        self, incoming: tuple[history.HistoricalReplayArchive, ...], *, expected_obs_dim: int | None
    ) -> tuple[history.HistoricalReplayArchive, ...]:
        width = expected_obs_dim
        if self.episodes:
            current = self.episodes[0]["observations"].shape[1]
            if width is not None and width != current:
                raise ValueError("archive observation width differs from current storage")
            width = current
        result = []
        identities: dict[str, bytes] = {}
        for archive in (*self._historical_archives, *incoming):
            owned = self._own_archive(archive, expected_obs_dim=width)
            if width is None:
                archived_episodes = owned.original_state["episodes"]
                if isinstance(archived_episodes, list) and archived_episodes:
                    width = int(archived_episodes[0]["observations"].shape[1])
            content = history._canonical((owned.source_formats, owned.original_state))
            if owned.source_digest in identities:
                if identities[owned.source_digest] != content:
                    raise ValueError("contradictory archive content under one domain-aware identity")
            else:
                identities[owned.source_digest] = content
                result.append(owned)
        return tuple(result)

    def _empty_prepared(self, archives: tuple[history.HistoricalReplayArchive, ...]) -> _PreparedSequenceState:
        policy = self.replay_options
        if policy is not None:
            policy = policy.model_copy(deep=True)
        return _PreparedSequenceState(
            0,
            deque(),
            self.capacity,
            self.device,
            self._configured,
            self.action_dim,
            self.legality_mode,
            policy,
            self.next_episode_id,
            self.next_transition_id,
            archives,
        )

    def prepare_archived_import(
        self, archives: tuple[history.HistoricalReplayArchive, ...], *, expected_obs_dim: int | None
    ) -> _SequentialRestoreCandidate:
        self._configuration()
        if not isinstance(archives, tuple):
            raise ValueError("prepare_archived_import requires an immutable tuple of archive records")
        if expected_obs_dim is not None:
            self._require_int(expected_obs_dim, "expected_obs_dim", minimum=1, maximum=_MAX_ID)
        return self._empty_prepared(self._merge_archives(archives, expected_obs_dim=expected_obs_dim))

    def _validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedSequentialState:
        if not isinstance(state, Mapping):
            raise ValueError("Sequential replay checkpoint payload must be a mapping")
        if set(state) & _INSPECTION_MARKERS:
            return self._validate_inspection(state, expected_obs_dim=expected_obs_dim)
        version = state.get("format_version")
        if type(version) is not int or version not in (_LEGACY_VERSION, SEQUENTIAL_REPLAY_BUFFER_FORMAT_VERSION):
            raise ValueError(
                f"Cannot load sequential checkpoint with format_version {version!r}; supported format_version values are 5 and 6"
            )
        if version == _LEGACY_VERSION:
            return self._validate_legacy_serialized(state, expected_obs_dim=expected_obs_dim)
        if state.get("replay_kind") != SEQUENTIAL_REPLAY_BUFFER_KIND:
            raise ValueError("Sequential checkpoint replay_kind must be sequential")
        if set(state) != SEQUENTIAL_REPLAY_BUFFER_STATE_KEYS:
            raise ValueError("Sequential checkpoint key set mismatch for captured format6")
        integer_fields = ("capacity", "num_transitions", "action_dim", "next_episode_id", "next_transition_id")
        if any(type(state[name]) is not int for name in integer_fields):
            raise ValueError("Sequential captured counts, geometry and identity counters require exact integers")
        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=_MAX_ID)
        if capacity != self.capacity:
            raise ValueError("Sequential checkpoint capacity differs from current capacity")
        count = self._require_int(state["num_transitions"], "num_transitions", minimum=0, maximum=capacity)
        action_dim = self._require_int(state["action_dim"], "action_dim", minimum=1, maximum=_MAX_ID)
        mode = state["legality_mode"]
        if type(mode) is not str or mode not in ("captured", "unconstrained"):
            raise ValueError("Sequential checkpoint legality_mode is unsupported")
        policy = self._resolved_options(state["replay_options"])
        if self._configured and (action_dim != self.action_dim or mode != self.legality_mode or policy != self.replay_options):
            raise ValueError("Sequential checkpoint action/legality/replay_options differ from configured storage")
        next_episode = self._require_int(state["next_episode_id"], "next_episode_id", minimum=0, maximum=_MAX_ID)
        next_transition = self._require_int(state["next_transition_id"], "next_transition_id", minimum=0, maximum=_MAX_ID)
        if not isinstance(state["episodes"], list):
            raise ValueError("Sequential checkpoint episodes must be a list")
        width = expected_obs_dim
        if self.episodes:
            current = self.episodes[0]["observations"].shape[1]
            if width is not None and width != current:
                raise ValueError("Sequential checkpoint expected observation width differs from current storage")
            width = current
        episodes = []
        total, last_episode, last_transition = 0, -1, -1
        for record in state["episodes"]:
            if not isinstance(record, Mapping) or set(record) != _CURRENT_EPISODE_KEYS:
                raise ValueError("Sequential captured fragment key set mismatch")
            if any(type(record[name]) is not int for name in ("episode_id", "original_length", "start_offset")):
                raise ValueError("Sequential captured fragment metadata requires exact integers")
            rows = self._captured_rows(
                {name: record[name] for name in SEQUENTIAL_EPISODE_KEYS},
                record["next_action_masks"],
                record["legality_recorded"],
                action_dim=action_dim,
                legality_mode=mode,
                expected_obs_dim=width,
            )
            length = len(rows["actions"])
            width = rows["observations"].shape[1]
            episode_id = self._require_int(record["episode_id"], "episode_id", minimum=0, maximum=_MAX_ID)
            original_length = self._require_int(record["original_length"], "original_length", minimum=1, maximum=_MAX_ID)
            offset = self._require_int(record["start_offset"], "start_offset", minimum=0, maximum=_MAX_ID)
            if offset + length > original_length or episode_id <= last_episode or episode_id >= next_episode:
                raise ValueError("Sequential fragment bounds or episode identity ordering are inconsistent")
            if policy.retention_mode == "whole_episode" and (offset != 0 or length != original_length):
                raise ValueError("whole_episode retention cannot claim partial fragments")
            ids = self._require_tensor(record, "transition_ids", dtype=torch.int64, shape=(length,))
            if ids.device != rows["observations"].device or bool((ids < 0).any()) or bool((ids[1:] <= ids[:-1]).any()):
                raise ValueError("Sequential transition_ids must be ordered nonnegative int64 real-row IDs")
            first, last = int(ids[0]), int(ids[-1])
            if first <= last_transition or last >= next_transition:
                raise ValueError("Sequential transition IDs overlap or exceed their persisted next-ID counter")
            rows.update(episode_id=episode_id, start_offset=offset, original_length=original_length, transition_ids=ids)
            episodes.append(self._own_fragment(rows, device=rows["observations"].device))
            total += length
            last_episode, last_transition = episode_id, last
        if total != count:
            raise ValueError("Sequential checkpoint num_transitions differs from real fragment row total")
        if not isinstance(state["historical_archives"], list):
            raise ValueError("Sequential checkpoint historical_archives must be a list")
        archives = tuple(
            self._own_archive(history._archive_from_state(record), expected_obs_dim=width) for record in state["historical_archives"]
        )
        return _ValidatedCapturedState(count, tuple(episodes), action_dim, mode, policy, next_episode, next_transition, archives)

    def _validate_inspection(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ValidatedInspectionState:
        if set(state) != _INSPECTION_KEYS:
            raise ValueError("Sequential inspection envelope key set mismatch")
        if type(state["inspection_kind"]) is not str or state["inspection_kind"] != _INSPECTION_KIND:
            raise ValueError("Sequential inspection_kind is unsupported")
        if type(state["inspection_version"]) is not int or state["inspection_version"] != 1:
            raise ValueError("Sequential inspection_version must be exact integer1")
        if self._configured:
            raise HistoricalLegalityUnavailable(
                "inspection envelope cannot downgrade captured replay; use the two-argument inspection route"
            )
        legacy = self._validate_legacy_serialized(state["legacy_transport"], expected_obs_dim=expected_obs_dim)
        if not isinstance(state["historical_archives"], list):
            raise ValueError("Sequential inspection historical_archives must be a list")
        width = expected_obs_dim
        if legacy.episodes:
            width = legacy.episodes[0]["observations"].shape[1]
        incoming = tuple(history._archive_from_state(record) for record in state["historical_archives"])
        archives = self._merge_archives(incoming, expected_obs_dim=width)
        episodes = tuple(self._own_fragment(episode, device=episode["observations"].device) for episode in legacy.episodes)
        return _ValidatedInspectionState(legacy.num_transitions, episodes, archives)

    def prepare_for_mode(
        self, state: Mapping[str, Any], *, expected_obs_dim: int | None, requested_mode: history.AccessMode
    ) -> _SequentialRestoreCandidate:
        if requested_mode not in ("auto", "recorded_full_resume", "archived_history_fresh_episode", "inference"):
            raise ValueError("requested_mode is unsupported")
        validated = self._validate_serialized(state, expected_obs_dim=expected_obs_dim)
        if isinstance(validated, _ValidatedLegacyState) and requested_mode == "recorded_full_resume":
            raise HistoricalLegalityUnavailable("missing historical successor masks; use approved archived_history_fresh_episode")
        if isinstance(validated, _ValidatedInspectionState) and requested_mode == "recorded_full_resume":
            raise HistoricalLegalityUnavailable("unqualified inspection transport has no captured replay identity for recorded_full_resume")
        if isinstance(validated, _ValidatedCapturedState) and requested_mode == "archived_history_fresh_episode":
            raise ValueError("current captured6 cannot discard qualified rows/history through archival reset")
        return self._materialize_serialized(validated)

    def load_for_mode(self, state: Mapping[str, Any], *, requested_mode: history.AccessMode) -> None:
        candidate = self.prepare_for_mode(state, expected_obs_dim=None, requested_mode=requested_mode)
        self.load_prepared(candidate)
