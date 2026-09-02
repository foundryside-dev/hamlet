"""Prioritized Experience Replay buffer (Schaul et al. 2016).

CRIT-07: Updated to use RewardTensor DTO for explicit composition semantics.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import torch

if TYPE_CHECKING:
    from townlet.training.state import RewardTensor


PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION = 4
PRIORITIZED_REPLAY_BUFFER_KIND = "prioritized"
PRIORITIZED_REPLAY_BUFFER_STATE_KEYS = frozenset(
    {
        "replay_kind",
        "format_version",
        "capacity",
        "alpha",
        "beta",
        "beta_initial",
        "beta_annealing",
        "observations",
        "actions",
        "rewards",
        "rewards_extrinsic",
        "rewards_intrinsic",
        "rewards_shaping",
        "next_observations",
        "dones",
        "priorities",
        "max_priority",
        "position",
        "size_current",
    }
)
_PER_TENSOR_FIELDS = (
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
class _PrioritizedRestoreCandidate:
    beta: float
    priorities: np.ndarray
    max_priority: float
    position: int
    size_current: int
    observations: torch.Tensor | None
    actions: torch.Tensor | None
    rewards: torch.Tensor | None
    rewards_extrinsic: torch.Tensor | None
    rewards_intrinsic: torch.Tensor | None
    rewards_shaping: torch.Tensor | None
    next_observations: torch.Tensor | None
    dones: torch.Tensor | None


@dataclass(frozen=True)
class _ValidatedPrioritizedState:
    beta: float
    priorities: np.ndarray
    max_priority: float
    position: int
    size_current: int
    obs_dim: int | None
    observations: torch.Tensor | None
    actions: torch.Tensor | None
    rewards: torch.Tensor | None
    rewards_extrinsic: torch.Tensor | None
    rewards_intrinsic: torch.Tensor | None
    rewards_shaping: torch.Tensor | None
    next_observations: torch.Tensor | None
    dones: torch.Tensor | None


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
        if observations.ndim != 2 or observations.dtype is not torch.float32:
            raise ValueError(
                f"observations must be 2D with dtype torch.float32, got shape {tuple(observations.shape)} and dtype {observations.dtype}"
            )
        if next_observations.ndim != 2 or next_observations.dtype is not torch.float32:
            raise ValueError(
                "next_observations must be 2D with dtype torch.float32, "
                f"got shape {tuple(next_observations.shape)} and dtype {next_observations.dtype}"
            )
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
        if batch_size > self.capacity:
            raise ValueError(f"batch_size ({batch_size}) exceeds buffer capacity ({self.capacity})")
        if actions.shape[0] != batch_size or rewards.total.shape[0] != batch_size or dones.shape[0] != batch_size:
            raise ValueError("PER transition batch tensors must have the same leading dimension.")
        if next_observations.shape != observations.shape:
            raise ValueError(
                f"next_observations shape {tuple(next_observations.shape)} must equal observations shape {tuple(observations.shape)}"
            )
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
        """Serialize the exact current prioritized replay artifact."""
        if self.observations is None:
            return {
                "replay_kind": PRIORITIZED_REPLAY_BUFFER_KIND,
                "format_version": PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION,
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
            "replay_kind": PRIORITIZED_REPLAY_BUFFER_KIND,
            "format_version": PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION,
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

    @staticmethod
    def _require_int(value: object, field: str, *, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"PER checkpoint {field} must be an integer; got {value!r}. Regenerate the checkpoint.")
        if not minimum <= value <= maximum:
            raise ValueError(f"PER checkpoint {field}={value} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return value

    @staticmethod
    def _require_float(value: object, field: str, *, minimum: float, maximum: float) -> float:
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
            raise ValueError(f"PER checkpoint {field} must be a finite number; got {value!r}. Regenerate the checkpoint.")
        result = float(value)
        if not minimum <= result <= maximum:
            raise ValueError(f"PER checkpoint {field}={result} is outside [{minimum}, {maximum}]. Regenerate the checkpoint.")
        return result

    @staticmethod
    def _require_tensor(state: Mapping[str, Any], field: str, *, dtype: torch.dtype, shape: tuple[int, ...]) -> torch.Tensor:
        value = state[field]
        if not isinstance(value, torch.Tensor):
            raise ValueError(f"PER checkpoint {field} must be a tensor; got {type(value).__name__}. Regenerate the checkpoint.")
        if value.dtype is not dtype:
            raise ValueError(f"PER checkpoint {field} dtype is {value.dtype}; expected {dtype}. Regenerate the checkpoint.")
        if tuple(value.shape) != shape:
            raise ValueError(f"PER checkpoint {field} shape is {tuple(value.shape)}; expected {shape}. Regenerate the checkpoint.")
        if dtype.is_floating_point and not bool(torch.isfinite(value).all()):
            raise ValueError(f"PER checkpoint {field} must contain only finite values. Regenerate the checkpoint.")
        return value

    def _validate_serialized(
        self,
        state: Mapping[str, Any],
        *,
        expected_obs_dim: int | None,
    ) -> _ValidatedPrioritizedState:
        if not isinstance(state, Mapping):
            raise ValueError(f"Prioritized replay checkpoint payload must be a mapping; got {type(state).__name__}.")
        format_version = state.get("format_version")
        if type(format_version) is not int or format_version != PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION:
            raise ValueError(
                f"Cannot load PER checkpoint with format_version {format_version!r}; "
                f"the exact current format_version is {PRIORITIZED_REPLAY_BUFFER_FORMAT_VERSION}. Regenerate the checkpoint."
            )
        replay_kind = state.get("replay_kind")
        if replay_kind != PRIORITIZED_REPLAY_BUFFER_KIND:
            raise ValueError(
                f"PER checkpoint replay_kind is {replay_kind!r}; expected {PRIORITIZED_REPLAY_BUFFER_KIND!r}. Regenerate the checkpoint."
            )
        state_keys = set(state)
        if state_keys != PRIORITIZED_REPLAY_BUFFER_STATE_KEYS:
            missing = sorted(PRIORITIZED_REPLAY_BUFFER_STATE_KEYS - state_keys)
            unknown = sorted(state_keys - PRIORITIZED_REPLAY_BUFFER_STATE_KEYS)
            raise ValueError(f"PER checkpoint key set mismatch: missing={missing}, unknown={unknown}. Regenerate the checkpoint.")

        capacity = self._require_int(state["capacity"], "capacity", minimum=1, maximum=2**63 - 1)
        if capacity != self.capacity:
            raise ValueError(
                f"PER checkpoint capacity is {capacity}; current capacity is {self.capacity}. "
                "Regenerate the checkpoint for this configuration."
            )
        alpha = self._require_float(state["alpha"], "alpha", minimum=0.0, maximum=1.0)
        if alpha != self.alpha:
            raise ValueError(f"PER checkpoint alpha is {alpha}; current alpha is {self.alpha}. Regenerate the checkpoint.")
        beta_initial = self._require_float(state["beta_initial"], "beta_initial", minimum=0.0, maximum=1.0)
        if beta_initial != self.beta_initial:
            raise ValueError(
                f"PER checkpoint beta_initial is {beta_initial}; current beta_initial is {self.beta_initial}. Regenerate the checkpoint."
            )
        beta_annealing = state["beta_annealing"]
        if type(beta_annealing) is not bool:
            raise ValueError("PER checkpoint beta_annealing must be a boolean. Regenerate the checkpoint.")
        if beta_annealing != self.beta_annealing:
            raise ValueError(
                f"PER checkpoint beta_annealing is {beta_annealing}; current beta_annealing is {self.beta_annealing}. "
                "Regenerate the checkpoint."
            )
        beta = self._require_float(state["beta"], "beta", minimum=beta_initial, maximum=1.0)
        if not beta_annealing and beta != beta_initial:
            raise ValueError("PER checkpoint beta must equal beta_initial when beta annealing is disabled. Regenerate the checkpoint.")
        size_current = self._require_int(state["size_current"], "size_current", minimum=0, maximum=self.capacity)
        position = self._require_int(state["position"], "position", minimum=0, maximum=self.capacity - 1)
        if size_current < self.capacity and position != size_current:
            raise ValueError(f"PER checkpoint position is {position}; expected {size_current} before wrap. Regenerate the checkpoint.")
        priorities = state["priorities"]
        if not isinstance(priorities, np.ndarray):
            raise ValueError(
                f"PER checkpoint priorities must be a numpy array; got {type(priorities).__name__}. Regenerate the checkpoint."
            )
        if priorities.dtype != np.dtype(np.float32):
            raise ValueError(f"PER checkpoint priorities dtype is {priorities.dtype}; expected float32. Regenerate the checkpoint.")
        if priorities.shape != (self.capacity,):
            raise ValueError(
                f"PER checkpoint priorities shape is {priorities.shape}; expected {(self.capacity,)}. Regenerate the checkpoint."
            )
        if not bool(np.isfinite(priorities).all()):
            raise ValueError("PER checkpoint priorities must contain only finite values. Regenerate the checkpoint.")
        if np.any(priorities[:size_current] <= 0.0) or np.any(priorities[size_current:] < 0.0):
            raise ValueError("PER checkpoint priorities are outside the valid positive/zero ranges. Regenerate the checkpoint.")
        max_priority = self._require_float(state["max_priority"], "max_priority", minimum=0.0, maximum=float("inf"))
        if max_priority <= 0.0:
            raise ValueError("PER checkpoint max_priority must be positive. Regenerate the checkpoint.")
        if size_current and max_priority < float(priorities[:size_current].max()):
            raise ValueError("PER checkpoint max_priority is below an active priority. Regenerate the checkpoint.")

        if size_current == 0:
            non_null = [field for field in _PER_TENSOR_FIELDS if state[field] is not None]
            if non_null:
                raise ValueError(f"Empty PER checkpoint tensor fields must be null; non-null={non_null}. Regenerate the checkpoint.")
            return _ValidatedPrioritizedState(
                beta,
                priorities,
                max_priority,
                0,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

        observations = state["observations"]
        if not isinstance(observations, torch.Tensor) or observations.ndim != 2:
            raise ValueError("PER checkpoint observations must be a 2D tensor. Regenerate the checkpoint.")
        obs_dim = observations.shape[1]
        if obs_dim <= 0:
            raise ValueError("PER checkpoint observations obs_dim must be positive. Regenerate the checkpoint.")
        if expected_obs_dim is not None and obs_dim != expected_obs_dim:
            raise ValueError(
                f"PER checkpoint obs_dim is {obs_dim}; expected current obs_dim {expected_obs_dim}. Regenerate the checkpoint."
            )
        if self.observations is not None and obs_dim != self.observations.shape[1]:
            raise ValueError(
                f"PER checkpoint obs_dim is {obs_dim}; current buffer obs_dim is {self.observations.shape[1]}. "
                "Regenerate the checkpoint."
            )
        observations = self._require_tensor(state, "observations", dtype=torch.float32, shape=(size_current, obs_dim))
        actions = self._require_tensor(state, "actions", dtype=torch.int64, shape=(size_current,))
        rewards = self._require_tensor(state, "rewards", dtype=torch.float32, shape=(size_current,))
        rewards_extrinsic = self._require_tensor(state, "rewards_extrinsic", dtype=torch.float32, shape=(size_current,))
        rewards_intrinsic = self._require_tensor(state, "rewards_intrinsic", dtype=torch.float32, shape=(size_current,))
        rewards_shaping = self._require_tensor(state, "rewards_shaping", dtype=torch.float32, shape=(size_current,))
        next_observations = self._require_tensor(state, "next_observations", dtype=torch.float32, shape=(size_current, obs_dim))
        dones = self._require_tensor(state, "dones", dtype=torch.bool, shape=(size_current,))

        return _ValidatedPrioritizedState(
            beta,
            priorities,
            max_priority,
            position,
            size_current,
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

    def _materialize_serialized(self, state: _ValidatedPrioritizedState) -> _PrioritizedRestoreCandidate:
        if state.size_current == 0:
            return _PrioritizedRestoreCandidate(
                state.beta,
                state.priorities.copy(),
                state.max_priority,
                0,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )

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
        candidate_observations[: state.size_current].copy_(state.observations.to(self.device))
        candidate_actions[: state.size_current].copy_(state.actions.to(self.device))
        candidate_rewards[: state.size_current].copy_(state.rewards.to(self.device))
        candidate_rewards_extrinsic[: state.size_current].copy_(state.rewards_extrinsic.to(self.device))
        candidate_rewards_intrinsic[: state.size_current].copy_(state.rewards_intrinsic.to(self.device))
        candidate_rewards_shaping[: state.size_current].copy_(state.rewards_shaping.to(self.device))
        candidate_next_observations[: state.size_current].copy_(state.next_observations.to(self.device))
        candidate_dones[: state.size_current].copy_(state.dones.to(self.device))
        return _PrioritizedRestoreCandidate(
            state.beta,
            state.priorities.copy(),
            state.max_priority,
            state.position,
            state.size_current,
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
    ) -> _PrioritizedRestoreCandidate:
        validated = self._validate_serialized(state, expected_obs_dim=expected_obs_dim)
        return self._materialize_serialized(validated)

    def validate_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int) -> _ValidatedPrioritizedState:
        """Validate exact structure without allocating restore storage or mutating this buffer."""
        return self._validate_serialized(state, expected_obs_dim=expected_obs_dim)

    def materialize_validated(self, state: _ValidatedPrioritizedState) -> _PrioritizedRestoreCandidate:
        """Materialize one restore candidate from already validated structure."""
        return self._materialize_serialized(state)

    def prepare_serialized(self, state: Mapping[str, Any], *, expected_obs_dim: int | None) -> _PrioritizedRestoreCandidate:
        """Validate and materialize the one candidate that will be installed."""
        return self._prepare_serialized(state, expected_obs_dim=expected_obs_dim)

    def load_prepared(self, candidate: _PrioritizedRestoreCandidate) -> None:
        """Install a fully validated, already materialized restore candidate."""
        self.beta = candidate.beta
        self.priorities = candidate.priorities
        self.max_priority = candidate.max_priority
        self.position = candidate.position
        self.size_current = candidate.size_current
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
