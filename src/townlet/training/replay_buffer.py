"""Replay buffer for off-policy learning with DAC-composed rewards.

CRIT-07: Updated to use RewardTensor DTO for explicit composition semantics.
Stores pre-composed total rewards from DAC, eliminating the misleading
'extrinsic/intrinsic' split pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.training.state import RewardTensor


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
        """
        Serialize buffer contents for checkpointing (P1.1).

        Version 3: Stores reward components (extrinsic, intrinsic, shaping) from DAC.

        Returns:
            Dictionary with all buffer state on CPU for saving
        """
        if self.observations is None:
            # Empty buffer
            return {
                "size": 0,
                "position": 0,
                "capacity": self.capacity,
                "format_version": 3,  # Version 3: reward components support
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
            "size": self.size,
            "position": self.size,  # Reset position to size since data is now contiguous
            "capacity": self.capacity,
            "format_version": 3,  # Version 3: reward components support
            "observations": observations,
            "actions": actions,
            "rewards": rewards,
            "rewards_extrinsic": rewards_extrinsic,
            "rewards_intrinsic": rewards_intrinsic,
            "rewards_shaping": rewards_shaping,
            "next_observations": next_observations,
            "dones": dones,
        }

    def load_from_serialized(self, state: dict[str, Any]) -> None:
        """
        Restore buffer from serialized state (P1.1).

        Version 3 required: Loads reward components (extrinsic, intrinsic, shaping).

        Args:
            state: Dictionary from serialize()

        Raises:
            ValueError: If the checkpoint format version or capacity does not match exactly
        """
        # Only the exact current checkpoint format is executable.
        format_version = state.get("format_version")
        if format_version != 3:
            raise ValueError(
                f"Cannot load replay buffer checkpoint with format_version {format_version!r}; "
                "the exact current format_version is 3. Regenerate the checkpoint."
            )

        if state["observations"] is None:
            # Empty buffer
            self.size = 0
            self.position = 0
            self.has_wrapped = False  # HIGH-04: Reset wrap flag
            return

        # HIGH-02: Validate that loaded size doesn't exceed current buffer capacity
        loaded_size = state["size"]
        if loaded_size > self.capacity:
            raise ValueError(
                f"Cannot load buffer: loaded size ({loaded_size}) exceeds buffer capacity ({self.capacity}). "
                f"Either increase buffer capacity in config or regenerate checkpoint with smaller buffer."
            )

        self.size = loaded_size
        self.position = state["position"]
        # HIGH-04: Set has_wrapped if buffer is full, since next push will overwrite oldest
        # Note: Serialized data is contiguous, but position=size means next push wraps to 0
        self.has_wrapped = loaded_size == self.capacity

        # Initialize storage if needed
        obs_dim = state["observations"].shape[1]

        # MED-05: Validate obs_dim consistency when buffer already has data
        if self.observations is not None and self.observations.shape[1] != obs_dim:
            raise ValueError(
                f"Cannot load buffer: loaded obs_dim ({obs_dim}) != current buffer obs_dim ({self.observations.shape[1]}). "
                f"Buffer dimension mismatch may indicate incompatible checkpoint or environment config."
            )

        if self.observations is None:
            self.observations = torch.zeros(self.capacity, obs_dim, device=self.device)
            self.actions = torch.zeros(self.capacity, dtype=torch.long, device=self.device)
            self.rewards = torch.zeros(self.capacity, device=self.device)
            self.rewards_extrinsic = torch.zeros(self.capacity, device=self.device)
            self.rewards_intrinsic = torch.zeros(self.capacity, device=self.device)
            self.rewards_shaping = torch.zeros(self.capacity, device=self.device)
            self.next_observations = torch.zeros(self.capacity, obs_dim, device=self.device)
            self.dones = torch.zeros(self.capacity, dtype=torch.bool, device=self.device)

        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.rewards_extrinsic is not None
        assert self.rewards_intrinsic is not None
        assert self.rewards_shaping is not None
        assert self.next_observations is not None
        assert self.dones is not None

        # Restore data
        self.observations[: self.size] = state["observations"].to(self.device)
        self.actions[: self.size] = state["actions"].to(self.device)
        self.rewards[: self.size] = state["rewards"].to(self.device)
        self.rewards_extrinsic[: self.size] = state["rewards_extrinsic"].to(self.device)
        self.rewards_intrinsic[: self.size] = state["rewards_intrinsic"].to(self.device)
        self.rewards_shaping[: self.size] = state["rewards_shaping"].to(self.device)
        self.next_observations[: self.size] = state["next_observations"].to(self.device)
        self.dones[: self.size] = state["dones"].to(self.device)
