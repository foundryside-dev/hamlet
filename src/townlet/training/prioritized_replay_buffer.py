"""Prioritized Experience Replay buffer (Schaul et al. 2016).

CRIT-07: Updated to use RewardTensor DTO for explicit composition semantics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import torch

if TYPE_CHECKING:
    from townlet.training.state import RewardTensor


class PrioritizedReplayBuffer:
    """Prioritized Experience Replay buffer with TD-error-based sampling.

    Samples transitions proportional to their TD error (priority).
    High TD-error transitions are sampled more frequently.

    Reference: Schaul et al. 2016 - "Prioritized Experience Replay"
    """

    def __init__(
        self,
        capacity: int,
        alpha: float,
        beta: float,
        beta_annealing: bool,
        device: torch.device,
    ):
        """Initialize prioritized replay buffer.

        Args:
            capacity: Maximum number of transitions
            alpha: Prioritization exponent (0=uniform, 1=full prioritization)
            beta: Importance sampling exponent (anneals to 1.0)
            beta_annealing: Whether to anneal beta to 1.0 over training
            device: PyTorch device
        """
        self.capacity = capacity
        self.alpha = alpha
        self.beta = beta
        self.beta_initial = beta  # CRIT-04: Store initial beta for annealing
        self.beta_annealing = beta_annealing
        self.device = device

        # Storage tensors (initialized on first push)
        self.observations: torch.Tensor | None = None
        self.actions: torch.Tensor | None = None
        self.rewards: torch.Tensor | None = None  # Total reward
        self.rewards_extrinsic: torch.Tensor | None = None  # DAC extrinsic component
        self.rewards_intrinsic: torch.Tensor | None = None  # DAC intrinsic component (after modifiers)
        self.rewards_shaping: torch.Tensor | None = None  # DAC shaping component
        self.next_observations: torch.Tensor | None = None
        self.dones: torch.Tensor | None = None

        # Priorities (TD errors)
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.max_priority = 1.0  # Initial priority for new transitions
        self.position = 0
        self.size_current = 0

    def push(
        self,
        observations: torch.Tensor,
        actions: torch.Tensor,
        rewards: RewardTensor,  # CRIT-07: Now accepts RewardTensor
        next_observations: torch.Tensor,
        dones: torch.Tensor,
    ) -> None:
        """Add batch of transitions to buffer with max priority.

        CRIT-07: Now accepts RewardTensor instead of separate extrinsic/intrinsic.
        MED-14: PER stores pre-composed rewards by design (from DAC). This is intentional,
        not a limitation. Alternative design (storing components) would require per-sample
        recomposition at training time, adding unnecessary overhead.

        Args:
            observations: [batch, obs_dim] observations
            actions: [batch] actions
            rewards: RewardTensor with pre-composed total rewards
            next_observations: [batch, obs_dim] next observations
            dones: [batch] done flags
        """
        batch_size = observations.shape[0]
        obs_dim = observations.shape[1]

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
        next_observations = next_observations.to(self.device)
        dones = dones.to(self.device)

        # CRIT-07: Use pre-composed total from RewardTensor
        reward_totals = rewards.total.to(self.device)

        # Loop over batch and store each transition
        for i in range(batch_size):
            idx = self.position % self.capacity

            # Direct tensor indexing (no list operations, no device churn)
            self.observations[idx] = observations[i]
            self.actions[idx] = actions[i]
            self.rewards[idx] = reward_totals[i]  # CRIT-07: Use total from RewardTensor
            self.next_observations[idx] = next_observations[i]
            self.dones[idx] = dones[i]

            # Store components if available
            if rewards.extrinsic is not None:
                self.rewards_extrinsic[idx] = rewards.extrinsic[i].to(self.device)
            if rewards.intrinsic is not None:
                self.rewards_intrinsic[idx] = rewards.intrinsic[i].to(self.device)
            if rewards.shaping is not None:
                self.rewards_shaping[idx] = rewards.shaping[i].to(self.device)

            # Assign max priority to new transition
            self.priorities[idx] = self.max_priority

            self.position = (self.position + 1) % self.capacity
            self.size_current = min(self.size_current + 1, self.capacity)

    def sample(self, batch_size: int) -> dict:
        """Sample batch with priority-based sampling.

        MED-03: Current implementation uses O(n) np.random.choice sampling.
        Future optimization: Use segment tree (sum-tree) for O(log n) sampling.
        Reference: Schaul et al. 2016 Appendix B.2.1

        Returns:
            Batch dict with keys: observations, actions, rewards,
            next_observations, dones, weights, indices

        Raises:
            ValueError: If batch_size exceeds buffer size or capacity
        """
        # LOW-16: Validate batch_size constraints
        if batch_size <= 0:
            raise ValueError(f"batch_size must be positive, got {batch_size}")
        if batch_size > self.capacity:
            raise ValueError(f"batch_size ({batch_size}) exceeds buffer capacity ({self.capacity})")

        # Guard: buffer must have enough transitions
        if self.size_current < batch_size:
            raise ValueError(f"Buffer size ({self.size_current}) < batch_size ({batch_size})")

        # MED-03: O(n) sampling - acceptable for buffer sizes < 1M, but could use segment tree for scale
        # Compute sampling probabilities from priorities
        priorities = self.priorities[: self.size_current]
        probs = priorities**self.alpha
        probs /= probs.sum()

        # Sample indices
        indices = np.random.choice(self.size_current, batch_size, p=probs, replace=False)

        # Compute importance sampling weights
        weights = (self.size_current * probs[indices]) ** (-self.beta)
        weights /= weights.max()  # Normalize by max weight

        # Mypy: guard attributes
        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.next_observations is not None
        assert self.dones is not None

        # Convert indices to tensor for vectorized gathering
        indices_tensor = torch.tensor(indices, dtype=torch.long, device=self.device)

        # Gather batch (direct tensor indexing, no stacking or device transfer)
        batch = {
            "observations": self.observations[indices_tensor],
            "actions": self.actions[indices_tensor],
            "rewards": self.rewards[indices_tensor],
            "next_observations": self.next_observations[indices_tensor],
            "dones": self.dones[indices_tensor],
            "weights": torch.tensor(weights, dtype=torch.float32, device=self.device),
            "indices": indices,
        }

        return batch

    def update_priorities(self, indices: np.ndarray, td_errors: torch.Tensor) -> None:
        """Update priorities for sampled transitions.

        MED-08: The abs() call ensures priorities are positive even if callers
        accidentally pass signed TD errors. This is defensive programming, not a bug.
        Callers should pass absolute TD errors, but this guarantees correctness.

        Args:
            indices: Indices of sampled transitions
            td_errors: TD errors (should be absolute values, but abs() ensures it)
        """
        td_errors_np = td_errors.detach().cpu().numpy()

        for idx, td_error in zip(indices, td_errors_np):
            # MED-08: abs() is defensive - ensures positive priorities even if caller forgets
            self.priorities[idx] = abs(td_error) + 1e-6  # Small epsilon to avoid zero priority

        # float() is required, not cosmetic: ndarray.max() returns np.floating, and
        # max(float, np.floating) widens to SupportsDunderLT | SupportsDunderGT.
        self.max_priority = max(self.max_priority, float(self.priorities[: self.size_current].max()))

    def anneal_beta(self, total_steps: int, current_step: int) -> None:
        """Anneal beta toward 1.0 over training.

        Args:
            total_steps: Total training steps
            current_step: Current training step
        """
        if self.beta_annealing:
            # CRIT-03: Guard against zero division
            if total_steps <= 0:
                return
            progress = min(current_step / total_steps, 1.0)
            # CRIT-04: Use stored initial beta instead of hardcoded 0.4
            self.beta = self.beta_initial + (1.0 - self.beta_initial) * progress

    def size(self) -> int:
        """Return current buffer size."""
        return self.size_current

    def __len__(self) -> int:
        """Return current buffer size (required by VectorizedPopulation)."""
        return self.size_current

    def clear(self) -> None:
        """Reset buffer to empty state and deallocate storage.

        Resets size and position to 0, sets all storage tensors to None,
        resets priorities array to zeros, and resets max_priority to 1.0.
        Buffer can be reused after clearing.
        """
        self.size_current = 0
        self.position = 0
        self.observations = None
        self.actions = None
        self.rewards = None
        self.rewards_extrinsic = None
        self.rewards_intrinsic = None
        self.rewards_shaping = None
        self.next_observations = None
        self.dones = None
        self.priorities = np.zeros(self.capacity, dtype=np.float32)
        self.max_priority = 1.0

    def stats(self) -> dict[str, Any]:
        """Return buffer statistics for introspection.

        Returns:
            Dictionary with keys:
                - size: Current number of transitions stored
                - capacity: Maximum buffer capacity
                - occupancy_ratio: size / capacity (0.0 to 1.0)
                - memory_bytes: Approximate memory usage in bytes (includes priorities)
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
                + self.priorities.nbytes  # NumPy array
            )

        # Calculate occupancy ratio
        occupancy_ratio = self.size_current / self.capacity if self.capacity > 0 else 0.0

        return {
            "size": self.size_current,
            "capacity": self.capacity,
            "occupancy_ratio": occupancy_ratio,
            "memory_bytes": memory_bytes,
            "device": str(self.device),
        }

    def serialize(self) -> dict:
        """Serialize buffer contents for checkpointing.

        Version 3: Stores reward components (extrinsic, intrinsic, shaping) from DAC.

        Returns:
            Dictionary containing buffer state (observations, priorities, metadata)
        """
        if self.observations is None:
            # Empty buffer
            return {
                "format_version": 3,  # Version 3: reward components support
                "capacity": self.capacity,
                "alpha": self.alpha,
                "beta": self.beta,
                "beta_initial": self.beta_initial,
                "beta_annealing": self.beta_annealing,
                "observations": None,
                "actions": None,
                "rewards": None,
                "rewards_extrinsic": None,
                "rewards_intrinsic": None,
                "rewards_shaping": None,
                "next_observations": None,
                "dones": None,
                "priorities": self.priorities.copy(),
                "max_priority": self.max_priority,
                "position": self.position,
                "size_current": self.size_current,
            }

        assert self.observations is not None
        assert self.actions is not None
        assert self.rewards is not None
        assert self.rewards_extrinsic is not None
        assert self.rewards_intrinsic is not None
        assert self.rewards_shaping is not None
        assert self.next_observations is not None
        assert self.dones is not None

        return {
            "format_version": 3,  # Version 3: reward components support
            "capacity": self.capacity,
            "alpha": self.alpha,
            "beta": self.beta,
            "beta_initial": self.beta_initial,
            "beta_annealing": self.beta_annealing,
            "observations": self.observations[: self.size_current].cpu().clone(),
            "actions": self.actions[: self.size_current].cpu().clone(),
            "rewards": self.rewards[: self.size_current].cpu().clone(),
            "rewards_extrinsic": self.rewards_extrinsic[: self.size_current].cpu().clone(),
            "rewards_intrinsic": self.rewards_intrinsic[: self.size_current].cpu().clone(),
            "rewards_shaping": self.rewards_shaping[: self.size_current].cpu().clone(),
            "next_observations": self.next_observations[: self.size_current].cpu().clone(),
            "dones": self.dones[: self.size_current].cpu().clone(),
            "priorities": self.priorities.copy(),
            "max_priority": self.max_priority,
            "position": self.position,
            "size_current": self.size_current,
        }

    def load_from_serialized(self, state: dict) -> None:
        """Restore buffer from serialized state.

        Version 3 required: Loads reward components (extrinsic, intrinsic, shaping).

        Args:
            state: Dictionary from serialize()

        Raises:
            ValueError: If the checkpoint format version does not match exactly
        """
        # Only the exact current checkpoint format is executable.
        format_version = state.get("format_version")
        if format_version != 3:
            raise ValueError(
                f"Cannot load PER checkpoint with format_version {format_version!r}; "
                "the exact current format_version is 3. Regenerate the checkpoint."
            )

        self.capacity = state["capacity"]
        self.alpha = state["alpha"]
        self.beta = state["beta"]
        self.beta_initial = state["beta_initial"]
        self.beta_annealing = state["beta_annealing"]
        self.priorities = state["priorities"].copy()
        self.max_priority = state["max_priority"]
        self.position = state["position"]
        self.size_current = state["size_current"]

        if state["observations"] is None:
            # Empty buffer
            self.observations = None
            self.actions = None
            self.rewards = None
            self.rewards_extrinsic = None
            self.rewards_intrinsic = None
            self.rewards_shaping = None
            self.next_observations = None
            self.dones = None
            return

        # Initialize storage if needed
        obs_dim = state["observations"].shape[1]
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
        self.observations[: self.size_current] = state["observations"].to(self.device)
        self.actions[: self.size_current] = state["actions"].to(self.device)
        self.rewards[: self.size_current] = state["rewards"].to(self.device)
        self.rewards_extrinsic[: self.size_current] = state["rewards_extrinsic"].to(self.device)
        self.rewards_intrinsic[: self.size_current] = state["rewards_intrinsic"].to(self.device)
        self.rewards_shaping[: self.size_current] = state["rewards_shaping"].to(self.device)
        self.next_observations[: self.size_current] = state["next_observations"].to(self.device)
        self.dones[: self.size_current] = state["dones"].to(self.device)
