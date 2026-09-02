"""Replay buffer for off-policy learning with DAC-composed rewards.

CRIT-07: Updated to use RewardTensor DTO for explicit composition semantics.
Stores pre-composed total rewards from DAC, eliminating the misleading
'extrinsic/intrinsic' split pattern.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.training.state import RewardTensor


REPLAY_BUFFER_FORMAT_VERSION = 4
REPLAY_BUFFER_KIND = "standard"
REPLAY_BUFFER_STATE_KEYS = frozenset(
    {
        "replay_kind",
        "format_version",
        "capacity",
        "size",
        "position",
        "observations",
        "actions",
        "rewards",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
        "next_observations",
        "dones",
    }
)
_REPLAY_TENSOR_FIELDS = (
    "observations",
    "actions",
    "rewards",
    "rewards_extrinsic",
    "rewards_intrinsic",
    "rewards_shaping",
    "next_observations",
    "dones",
)


@dataclass(frozen=True)
class _ReplayRestoreCandidate:
    size: int
    position: int
    has_wrapped: bool
    observations: torch.Tensor | None
    actions: torch.Tensor | None
    rewards: torch.Tensor | None
    rewards_extrinsic: torch.Tensor | None
    rewards_intrinsic: torch.Tensor | None
    rewards_shaping: torch.Tensor | None
    next_observations: torch.Tensor | None
    dones: torch.Tensor | None


@dataclass(frozen=True)
class _ValidatedReplayState:
    size: int
    position: int
    obs_dim: int | None
    observations: torch.Tensor | None
    actions: torch.Tensor | None
    rewards: torch.Tensor | None
    rewards_extrinsic: torch.Tensor | None
    rewards_intrinsic: torch.Tensor | None
    rewards_shaping: torch.Tensor | None
    next_observations: torch.Tensor | None
    dones: torch.Tensor | None


class ReplayBuffer:
    """Circular buffer storing transitions with DAC-composed rewards.

    CRIT-07: Stores total rewards from RewardTensor, not separate components.

    Stores: (obs, action, reward_total, next_obs, done)
    Samples: Random mini-batches with pre-composed rewards
    """

    def __init__(self, capacity: int, device: torch.device):
        """Initialize replay buffer.

        Args:
            capacity: Maximum number of transitions to store
            device: Device for tensor storage (CPU or CUDA)
        """
        self.capacity = capacity
        self.device = device
        self.position = 0
        self.size = 0
        self.has_wrapped = False  # HIGH-04: Track if buffer has wrapped for serialization

        # Storage tensors (initialized on first push)
        self.observations: torch.Tensor | None = None
        self.actions: torch.Tensor | None = None
        self.rewards: torch.Tensor | None = None  # Total reward
        self.rewards_extrinsic: torch.Tensor | None = None  # DAC extrinsic component
        self.rewards_intrinsic: torch.Tensor | None = None  # DAC intrinsic component (after modifiers)
        self.rewards_shaping: torch.Tensor | None = None  # DAC shaping component
        self.next_observations: torch.Tensor | None = None
        self.dones: torch.Tensor | None = None

    def push(
        self,
        observations: torch.Tensor,  # [batch, obs_dim]
        actions: torch.Tensor,  # [batch]
        rewards: RewardTensor,  # [batch] - DAC-composed rewards
        next_observations: torch.Tensor,  # [batch, obs_dim]
        dones: torch.Tensor,  # [batch]
    ) -> None:
        """Add batch of transitions to buffer.

        CRIT-07: Now accepts RewardTensor instead of separate extrinsic/intrinsic.

        Uses FIFO eviction when buffer is full.

        Raises:
            ValueError: If batch_size > capacity (would corrupt buffer state)
            ValueError: If tensor shapes are inconsistent (MED-04)
        """
        if observations.ndim != 2:
            raise ValueError(f"observations must be 2D [batch, obs_dim], got shape {tuple(observations.shape)}")
        if observations.dtype is not torch.float32:
            raise ValueError(f"observations must use dtype torch.float32, got {observations.dtype}")
        if next_observations.ndim != 2:
            raise ValueError(f"next_observations must be 2D [batch, obs_dim], got shape {tuple(next_observations.shape)}")
        if next_observations.dtype is not torch.float32:
            raise ValueError(f"next_observations must use dtype torch.float32, got {next_observations.dtype}")
        if actions.ndim != 1 or actions.dtype is not torch.int64:
            raise ValueError(f"actions must be 1D with dtype torch.int64, got shape {tuple(actions.shape)} and dtype {actions.dtype}")
        if rewards.total.ndim != 1 or rewards.total.dtype is not torch.float32:
            raise ValueError(
                f"rewards.total must be 1D with dtype torch.float32, got shape {tuple(rewards.total.shape)} and dtype {rewards.total.dtype}"
            )
        if dones.ndim != 1 or dones.dtype is not torch.bool:
            raise ValueError(f"dones must be 1D with dtype torch.bool, got shape {tuple(dones.shape)} and dtype {dones.dtype}")

        batch_size = observations.shape[0]
        obs_dim = observations.shape[1]

        # CRIT-01: Prevent buffer corruption from oversized batches
        if batch_size > self.capacity:
            raise ValueError(
                f"batch_size ({batch_size}) exceeds buffer capacity ({self.capacity}). "
                f"This would corrupt the circular buffer. Either increase capacity or reduce batch_size."
            )

        # MED-04: Validate tensor shapes for consistency
        if actions.shape[0] != batch_size:
            raise ValueError(f"actions batch size ({actions.shape[0]}) != observations batch size ({batch_size})")
        if rewards.total.shape[0] != batch_size:
            raise ValueError(f"rewards batch size ({rewards.total.shape[0]}) != observations batch size ({batch_size})")
        if next_observations.shape[0] != batch_size:
            raise ValueError(f"next_observations batch size ({next_observations.shape[0]}) != observations batch size ({batch_size})")
        if next_observations.shape[1] != obs_dim:
            raise ValueError(f"next_observations obs_dim ({next_observations.shape[1]}) != observations obs_dim ({obs_dim})")
        if dones.shape[0] != batch_size:
            raise ValueError(f"dones batch size ({dones.shape[0]}) != observations batch size ({batch_size})")
        if self.observations is not None and obs_dim != self.observations.shape[1]:
            raise ValueError(f"observations obs_dim ({obs_dim}) != current buffer obs_dim ({self.observations.shape[1]})")
        for field, tensor in (
            ("observations", observations),
            ("rewards.total", rewards.total),
            ("next_observations", next_observations),
        ):
            if not bool(torch.isfinite(tensor).all()):
                raise ValueError(f"{field} must contain only finite values")
        for field, component in (
            ("rewards.extrinsic", rewards.extrinsic),
            ("rewards.intrinsic", rewards.intrinsic),
            ("rewards.shaping", rewards.shaping),
        ):
            if component is None:
                continue
            if component.ndim != 1 or component.shape[0] != batch_size or component.dtype is not torch.float32:
                raise ValueError(f"{field} must have shape ({batch_size},) and dtype torch.float32")
            if not bool(torch.isfinite(component).all()):
                raise ValueError(f"{field} must contain only finite values")

        # Initialize storage on first push
        if self.observations is None:
            self.observations = torch.zeros(self.capacity, obs_dim, device=self.device)
            self.actions = torch.zeros(self.capacity, dtype=torch.long, device=self.device)
            self.rewards = torch.zeros(self.capacity, device=self.device)
            self.rewards_extrinsic = torch.zeros(self.capacity, device=self.device)
            self.rewards_intrinsic = torch.zeros(self.capacity, device=self.device)
            self.rewards_shaping = torch.zeros(self.capacity, device=self.device)
            self.next_observations = torch.zeros(self.capacity, obs_dim, device=self.device)
            self.dones = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)

        # Mypy: guard attributes after allocation
        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.rewards_extrinsic is not None
        assert self.rewards_intrinsic is not None
        assert self.rewards_shaping is not None
        assert self.next_observations is not None
        assert self.dones is not None

        # Move tensors to device
        observations = observations.to(self.device)
        actions = actions.to(self.device)
        reward_totals = rewards.total.to(self.device)  # CRIT-07: Use total from RewardTensor
        next_observations = next_observations.to(self.device)
        dones = dones.to(self.device)

        # MED-01: Vectorized circular buffer push using tensor slicing
        # Compute indices for batch insertion (handles wrap-around correctly)
        start_pos = self.position
        end_pos = start_pos + batch_size

        if end_pos <= self.capacity:
            # Simple case: batch fits without wrapping
            indices = slice(start_pos, end_pos)
            self.observations[indices] = observations
            self.actions[indices] = actions
            self.rewards[indices] = reward_totals
            self.next_observations[indices] = next_observations
            self.dones[indices] = dones

            # Store components if available
            if rewards.extrinsic is not None:
                self.rewards_extrinsic[indices] = rewards.extrinsic.to(self.device)
            if rewards.intrinsic is not None:
                self.rewards_intrinsic[indices] = rewards.intrinsic.to(self.device)
            if rewards.shaping is not None:
                self.rewards_shaping[indices] = rewards.shaping.to(self.device)
        else:
            # Wrap-around case: split batch into two chunks
            first_chunk_size = self.capacity - start_pos
            second_chunk_size = batch_size - first_chunk_size

            # First chunk: from start_pos to capacity
            self.observations[start_pos : self.capacity] = observations[:first_chunk_size]
            self.actions[start_pos : self.capacity] = actions[:first_chunk_size]
            self.rewards[start_pos : self.capacity] = reward_totals[:first_chunk_size]
            self.next_observations[start_pos : self.capacity] = next_observations[:first_chunk_size]
            self.dones[start_pos : self.capacity] = dones[:first_chunk_size]

            # Second chunk: from 0 to wrap point
            self.observations[:second_chunk_size] = observations[first_chunk_size:]
            self.actions[:second_chunk_size] = actions[first_chunk_size:]
            self.rewards[:second_chunk_size] = reward_totals[first_chunk_size:]
            self.next_observations[:second_chunk_size] = next_observations[first_chunk_size:]
            self.dones[:second_chunk_size] = dones[first_chunk_size:]

            # Store components if available (both chunks)
            if rewards.extrinsic is not None:
                extrinsic = rewards.extrinsic.to(self.device)
                self.rewards_extrinsic[start_pos : self.capacity] = extrinsic[:first_chunk_size]
                self.rewards_extrinsic[:second_chunk_size] = extrinsic[first_chunk_size:]
            if rewards.intrinsic is not None:
                intrinsic = rewards.intrinsic.to(self.device)
                self.rewards_intrinsic[start_pos : self.capacity] = intrinsic[:first_chunk_size]
                self.rewards_intrinsic[:second_chunk_size] = intrinsic[first_chunk_size:]
            if rewards.shaping is not None:
                shaping = rewards.shaping.to(self.device)
                self.rewards_shaping[start_pos : self.capacity] = shaping[:first_chunk_size]
                self.rewards_shaping[:second_chunk_size] = shaping[first_chunk_size:]

        # Update position and size (HIGH-04: Use modulo to prevent unbounded growth)
        self.position = (self.position + batch_size) % self.capacity
        old_size = self.size
        self.size = min(self.size + batch_size, self.capacity)

        # Track if we've wrapped around for serialization (CRIT-02)
        if old_size < self.capacity and self.size == self.capacity:
            self.has_wrapped = True

    def sample(self, batch_size: int) -> dict[str, torch.Tensor]:
        """Sample random mini-batch with pre-composed rewards.

        CRIT-07: Rewards are already composed by DAC before storage.
        MED-13: Removed dead intrinsic_weight parameter (always 1.0 post-DAC).

        Args:
            batch_size: Number of transitions to sample

        Returns:
            Dictionary with keys: observations, actions, rewards, next_observations, dones, mask
            'rewards' contains DAC-composed totals
            'mask' = bool tensor [batch_size] (all True for feed-forward training)
        """
        if self.size < batch_size:
            raise ValueError(f"Buffer size ({self.size}) < batch_size ({batch_size})")

        # MED-15: Sample without replacement for better training diversity
        # Use torch.randperm and select first batch_size indices (more efficient than randint with duplicates)
        indices = torch.randperm(self.size, device=self.device)[:batch_size]

        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.next_observations is not None
        assert self.dones is not None

        # CRIT-07: Return pre-composed rewards directly (no intrinsic_weight multiplication)
        # MED-16: mask is all True for feedforward buffer (no temporal context).
        # Post-terminal masking only applies to sequential buffers (LSTM training).
        return {
            "observations": self.observations[indices],
            "actions": self.actions[indices],
            "rewards": self.rewards[indices],
            "next_observations": self.next_observations[indices],
            "dones": self.dones[indices],
            "mask": torch.ones(batch_size, dtype=torch.bool, device=self.device),
        }

    def __len__(self) -> int:
        """Return current buffer size."""
        return self.size

    def clear(self) -> None:
        """Reset buffer to empty state and deallocate storage.

        Resets size and position to 0 and sets all storage tensors to None,
        allowing garbage collection to reclaim memory. Buffer can be reused
        after clearing.
        """
        self.size = 0
        self.position = 0
        self.has_wrapped = False  # HIGH-04: Reset wrap flag
        self.observations = None
        self.actions = None
        self.rewards = None
        self.rewards_extrinsic = None
        self.rewards_intrinsic = None
        self.rewards_shaping = None
        self.next_observations = None
        self.dones = None

    def stats(self) -> dict[str, Any]:
        """Return buffer statistics for introspection.

        Returns:
            Dictionary with keys:
                - size: Current number of transitions stored
                - capacity: Maximum buffer capacity
                - occupancy_ratio: size / capacity (0.0 to 1.0)
                - memory_bytes: Approximate memory usage in bytes
                - device: Device string (e.g., 'cpu', 'cuda:0')
        """
        # Calculate memory usage
        memory_bytes = 0
        if self.observations is not None:
            # All tensors are preallocated to capacity
            assert self.actions is not None
            assert self.rewards is not None
            assert self.rewards_extrinsic is not None
            assert self.rewards_intrinsic is not None
            assert self.rewards_shaping is not None
            assert self.next_observations is not None
            assert self.dones is not None

            memory_bytes = (
                self.observations.element_size() * self.observations.numel()
                + self.actions.element_size() * self.actions.numel()
                + self.rewards.element_size() * self.rewards.numel()
                + self.rewards_extrinsic.element_size() * self.rewards_extrinsic.numel()
                + self.rewards_intrinsic.element_size() * self.rewards_intrinsic.numel()
                + self.rewards_shaping.element_size() * self.rewards_shaping.numel()
                + self.next_observations.element_size() * self.next_observations.numel()
                + self.dones.element_size() * self.dones.numel()
            )

        # Calculate occupancy ratio
        occupancy_ratio = self.size / self.capacity if self.capacity > 0 else 0.0

        return {
            "size": self.size,
            "capacity": self.capacity,
            "occupancy_ratio": occupancy_ratio,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
        }

    def serialize(self) -> dict[str, Any]:
        """Serialize the exact current standard replay artifact."""
        if self.observations is None:
            return {
                "replay_kind": REPLAY_BUFFER_KIND,
                "format_version": REPLAY_BUFFER_FORMAT_VERSION,
                "capacity": self.capacity,
                "size": 0,
                "position": 0,
                "observations": None,
                "actions": None,
                "rewards": None,
                "rewards_extrinsic": None,
                "rewards_intrinsic": None,
                "rewards_shaping": None,
                "next_observations": None,
                "dones": None,
            }

        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.rewards_extrinsic is not None
        assert self.rewards_intrinsic is not None
        assert self.rewards_shaping is not None
        assert self.next_observations is not None
        assert self.dones is not None

        # CRIT-02: Handle wrap-around correctly to preserve temporal order
        # When buffer has wrapped, data is not contiguous from index 0.
        # Oldest data is at index (position % capacity), newest at ((position-1) % capacity).
        # HIGH-04: Use has_wrapped flag instead of position > capacity check
        if self.has_wrapped:
            # Buffer has wrapped - reorder to temporal sequence (oldest first)
            wrap_point = self.position  # Position already points to oldest after modulo
            observations = torch.cat([self.observations[wrap_point:], self.observations[:wrap_point]], dim=0).cpu().clone()
            actions = torch.cat([self.actions[wrap_point:], self.actions[:wrap_point]], dim=0).cpu().clone()
            rewards = torch.cat([self.rewards[wrap_point:], self.rewards[:wrap_point]], dim=0).cpu().clone()
            rewards_extrinsic = torch.cat([self.rewards_extrinsic[wrap_point:], self.rewards_extrinsic[:wrap_point]], dim=0).cpu().clone()
            rewards_intrinsic = torch.cat([self.rewards_intrinsic[wrap_point:], self.rewards_intrinsic[:wrap_point]], dim=0).cpu().clone()
            rewards_shaping = torch.cat([self.rewards_shaping[wrap_point:], self.rewards_shaping[:wrap_point]], dim=0).cpu().clone()
            next_observations = torch.cat([self.next_observations[wrap_point:], self.next_observations[:wrap_point]], dim=0).cpu().clone()
            dones = torch.cat([self.dones[wrap_point:], self.dones[:wrap_point]], dim=0).cpu().clone()
        else:
            # Buffer hasn't wrapped - data is already in temporal order
            observations = self.observations[: self.size].cpu().clone()
            actions = self.actions[: self.size].cpu().clone()
            rewards = self.rewards[: self.size].cpu().clone()
            rewards_extrinsic = self.rewards_extrinsic[: self.size].cpu().clone()
            rewards_intrinsic = self.rewards_intrinsic[: self.size].cpu().clone()
            rewards_shaping = self.rewards_shaping[: self.size].cpu().clone()
            next_observations = self.next_observations[: self.size].cpu().clone()
            dones = self.dones[: self.size].cpu().clone()

        return {
            "replay_kind": REPLAY_BUFFER_KIND,
            "format_version": REPLAY_BUFFER_FORMAT_VERSION,
            "capacity": self.capacity,
            "size": self.size,
            "position": self.size % self.capacity,
            "observations": observations,
            "actions": actions,
            "rewards": rewards,
            "rewards_extrinsic": rewards_extrinsic,
            "rewards_intrinsic": rewards_intrinsic,
            "rewards_shaping": rewards_shaping,
            "next_observations": next_observations,
            "dones": dones,
        }

    @staticmethod
    def _require_tensor(
        state: Mapping[str, Any],
        field: str,
        *,
        dtype: torch.dtype,
        shape: tuple[int, ...],
    ) -> torch.Tensor:
        value = state[field]
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"Replay checkpoint {field} must be a tensor; got {type(value).__name__}. Regenerate the checkpoint.")
        if value.dtype is not dtype:
            raise ValueError(f"Replay checkpoint {field} dtype is {value.dtype}; expected {dtype}. Regenerate the checkpoint.")
        if tuple(value.shape) != shape:
            raise ValueError(f"Replay checkpoint {field} shape is {tuple(value.shape)}; expected {shape}. Regenerate the checkpoint.")
        if dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"Replay checkpoint {field} must contain only finite values. Regenerate the checkpoint.")
        return value

    @staticmethod
    def _require_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Replay checkpoint {field} must be an integer; got {value!r}. Regenerate the checkpoint.")
        if not minimum <= value <= maximum:
            raise ValueError(f"Replay checkpoint {field}={value} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return value

    def _validate_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _ValidatedReplayState:
        if not isinstance(state, Mapping):
            raise ValueError(f"Replay buffer checkpoint payload must be a mapping; got {type(state).__name__}.")
        format_version = state.get("format_version")
        if type(format_version) is not int or format_version != REPLAY_BUFFER_FORMAT_VERSION:
            raise ValueError(
                f"Cannot load replay buffer checkpoint with format_version {format_version!r}; "
                f"the exact current format_version is {REPLAY_BUFFER_FORMAT_VERSION}. Regenerate the checkpoint."
            )

        replay_kind = state.get("replay_kind")
        if replay_kind != REPLAY_BUFFER_KIND:
            raise ValueError(
                f"Replay checkpoint replay_kind is {replay_kind!r}; expected {REPLAY_BUFFER_KIND!r}. Regenerate the checkpoint."
            )

        state_keys = set(state)
        if state_keys != REPLAY_BUFFER_STATE_KEYS:
            missing = sorted(REPLAY_BUFFER_STATE_KEYS - state_keys)
            unknown = sorted(state_keys - REPLAY_BUFFER_STATE_KEYS)
            raise ValueError(f"Replay checkpoint key set mismatch: missing={missing}, unknown={unknown}. Regenerate the checkpoint.")

        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        if capacity != self.capacity:
            raise ValueError(
                f"Replay checkpoint capacity is {capacity}; current capacity is {self.capacity}. "
                "Regenerate the checkpoint for this configuration."
            )
        size = self._require_int(state["size"], "size", minimum=0, maximum=self.capacity)
        position = self._require_int(state["position"], "position", minimum=0, maximum=self.capacity - 1)
        expected_position = size % self.capacity
        if position != expected_position:
            raise ValueError(
                f"Replay checkpoint position is {position}; expected {expected_position} for size {size}. Regenerate the checkpoint."
            )

        if size == 0:
            non_null = [field for field in _REPLAY_TENSOR_FIELDS if state[field] is not None]
            if non_null:
                raise ValueError(f"Empty replay checkpoint tensor fields must be null; non-null={non_null}. Regenerate the checkpoint.")
            return _ValidatedReplayState(0, 0, None, None, None, None, None, None, None, None, None)

        observations = state["observations"]
        if not isinstance(observations, torch.Tensor) or observations.ndim != 2:
            raise ValueError("Replay checkpoint observations must be a 2D tensor. Regenerate the checkpoint.")
        obs_dim = observations.shape[1]
        if obs_dim <= 0:
            raise ValueError("Replay checkpoint observations obs_dim must be positive. Regenerate the checkpoint.")
        if expected_obs_dim is not None and obs_dim != expected_obs_dim:
            raise ValueError(
                f"Replay checkpoint obs_dim is {obs_dim}; expected current obs_dim {expected_obs_dim}. Regenerate the checkpoint."
            )
        if self.observations is not None and obs_dim != self.observations.shape[1]:
            raise ValueError(
                f"Replay checkpoint obs_dim is {obs_dim}; current buffer obs_dim is {self.observations.shape[1]}. "
                "Regenerate the checkpoint."
            )

        observations = self._require_tensor(state, "observations", dtype=torch.float32, shape=(size, obs_dim))
        actions = self._require_tensor(state, "actions", dtype=torch.int64, shape=(size,))
        rewards = self._require_tensor(state, "rewards", dtype=torch.float32, shape=(size,))
        rewards_extrinsic = self._require_tensor(state, "rewards_extrinsic", dtype=torch.float32, shape=(size,))
        rewards_intrinsic = self._require_tensor(state, "rewards_intrinsic", dtype=torch.float32, shape=(size,))
        rewards_shaping = self._require_tensor(state, "rewards_shaping", dtype=torch.float32, shape=(size,))
        next_observations = self._require_tensor(state, "next_observations", dtype=torch.float32, shape=(size, obs_dim))
        dones = self._require_tensor(state, "dones", dtype=torch.bool, shape=(size,))

        return _ValidatedReplayState(
            size,
            position,
            obs_dim,
            observations,
            actions,
            rewards,
            rewards_extrinsic,
            rewards_intrinsic,
            rewards_shaping,
            next_observations,
            dones,
        )

    def _materialize_serialized(self, state: _ValidatedReplayState) -> _ReplayRestoreCandidate:
        if state.size == 0:
            return _ReplayRestoreCandidate(0, 0, False, None, None, None, None, None, None, None, None)

        assert state.obs_dim is not None
        assert state.observations is not None
        assert state.actions is not None
        assert state.rewards is not None
        assert state.rewards_extrinsic is not None
        assert state.rewards_intrinsic is not None
        assert state.rewards_shaping is not None
        assert state.next_observations is not None
        assert state.dones is not None
        candidate_observations = torch.zeros((self.capacity, state.obs_dim), dtype=torch.float32, device=self.device)
        candidate_actions = torch.zeros(self.capacity, dtype=torch.int64, device=self.device)
        candidate_rewards = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
        candidate_rewards_extrinsic = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
        candidate_rewards_intrinsic = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
        candidate_rewards_shaping = torch.zeros(self.capacity, dtype=torch.float32, device=self.device)
        candidate_next_observations = torch.zeros((self.capacity, state.obs_dim), dtype=torch.float32, device=self.device)
        candidate_dones = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)
        candidate_observations[: state.size].copy_(state.observations.to(self.device))
        candidate_actions[: state.size].copy_(state.actions.to(self.device))
        candidate_rewards[: state.size].copy_(state.rewards.to(self.device))
        candidate_rewards_extrinsic[: state.size].copy_(state.rewards_extrinsic.to(self.device))
        candidate_rewards_intrinsic[: state.size].copy_(state.rewards_intrinsic.to(self.device))
        candidate_rewards_shaping[: state.size].copy_(state.rewards_shaping.to(self.device))
        candidate_next_observations[: state.size].copy_(state.next_observations.to(self.device))
        candidate_dones[: state.size].copy_(state.dones.to(self.device))
        return _ReplayRestoreCandidate(
            state.size,
            state.position,
            state.size == self.capacity,
            candidate_observations,
            candidate_actions,
            candidate_rewards,
            candidate_rewards_extrinsic,
            candidate_rewards_intrinsic,
            candidate_rewards_shaping,
            candidate_next_observations,
            candidate_dones,
        )

    def _prepare_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _ReplayRestoreCandidate:
        validated = self._validate_serialized(state, expected_obs_dim=expected_obs_dim)
        return self._materialize_serialized(validated)

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int) -> _ValidatedReplayState:
        """Validate exact structure without allocating restore storage or mutating this buffer."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedReplayState) -> _ReplayRestoreCandidate:
        """Materialize one restore candidate from already validated structure."""
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _ReplayRestoreCandidate:
        """Validate and materialize the one candidate that will be installed."""
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _ReplayRestoreCandidate) -> None:
        """Install a fully validated, already materialized restore candidate."""
        self.size = candidate.size
        self.position = candidate.position
        self.has_wrapped = candidate.has_wrapped
        self.observations = candidate.observations
        self.actions = candidate.actions
        self.rewards = candidate.rewards
        self.rewards_extrinsic = candidate.rewards_extrinsic
        self.rewards_intrinsic = candidate.rewards_intrinsic
        self.rewards_shaping = candidate.rewards_shaping
        self.next_observations = candidate.next_observations
        self.dones = candidate.dones

    def load_from_serialized(self, state: Mapping[str, Any]) -> None:
        """Restore only after the complete exact-current artifact validates."""
        self.load_prepared(self.prepare_serialized(state, expected_obs_dim=None))
