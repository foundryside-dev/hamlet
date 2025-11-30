"""Random Network Distillation (RND) for intrinsic motivation."""

from __future__ import annotations

import warnings
from typing import Any, cast

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812

from townlet.exploration.action_selection import epsilon_greedy_action_selection
from townlet.exploration.base import ExplorationStrategy
from townlet.training.state import BatchedAgentState


class RunningMeanStd:
    """Running mean and standard deviation tracker.

    Uses Welford's online algorithm for numerical stability.
    Adapted from OpenAI's RND implementation and CleanRL.

    EXP-01: Fixed variance collapse bug. Original initialization with count=epsilon
    caused variance to collapse when early batches had small values, leading to
    exploding normalized intrinsic rewards (10-100x inflation).
    """

    def __init__(self, initial_count: int = 100, min_variance: float = 0.01):
        """Initialize running statistics.

        Args:
            initial_count: Initial pseudo-count for numerical stability.
                Higher values make early statistics more stable but slower
                to adapt. Default 100 provides good balance.
            min_variance: Variance floor to prevent reward explosion.
                Default 0.01 per EXP-01 fix.

        EXP-01: Changed from epsilon=1e-4 to initial_count=100 to prevent
        variance collapse in early training when prediction errors are small.
        """
        self.mean = 0.0
        self.var = 1.0
        self.count = float(initial_count)
        self.min_variance = min_variance

    def update(self, x: np.ndarray) -> None:
        """Update running statistics with new batch.

        Args:
            x: Array of shape [batch_size] or [batch_size, ...]
        """
        batch_mean = np.mean(x)
        batch_var = np.var(x)
        batch_count = x.size if isinstance(x.size, int) else np.prod(x.shape)

        self.update_from_moments(batch_mean, batch_var, batch_count)

    def update_from_moments(self, batch_mean: float, batch_var: float, batch_count: int) -> None:
        """Update from pre-computed batch statistics.

        Args:
            batch_mean: Mean of batch
            batch_var: Variance of batch
            batch_count: Number of samples in batch
        """
        delta = batch_mean - self.mean
        total_count = self.count + batch_count

        new_mean = self.mean + delta * batch_count / total_count
        m_a = self.var * self.count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta**2 * self.count * batch_count / total_count
        new_var = m2 / total_count

        self.mean = new_mean
        self.var = new_var
        self.count = total_count


class RNDNetwork(nn.Module):
    """3-layer MLP for RND embeddings.

    Architecture: [obs_dim → 256 → 128 → embed_dim]
    Matches SimpleQNetwork architecture for consistency.
    """

    def __init__(self, obs_dim: int = 70, embed_dim: int = 128, active_mask: tuple[bool, ...] | None = None):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, embed_dim),
        )

        # Register active_mask as buffer (moves with model to device)
        if active_mask is not None:
            mask_tensor = torch.tensor(active_mask, dtype=torch.float32)
        else:
            # No masking: all dimensions active
            mask_tensor = torch.ones(obs_dim, dtype=torch.float32)
        self.register_buffer("active_mask", mask_tensor)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Transform observations to embeddings.

        Args:
            x: [batch, obs_dim] observations

        Returns:
            [batch, embed_dim] embeddings
        """
        # Apply mask to zero out padding dimensions
        # Cast needed because register_buffer doesn't provide proper typing to mypy
        active_mask = cast(torch.Tensor, self.active_mask)
        masked_x = x * active_mask
        return cast(torch.Tensor, self.net(masked_x))


class RNDExploration(ExplorationStrategy):
    """Random Network Distillation for novelty-based intrinsic rewards.

    Uses prediction error as intrinsic reward signal:
    - High error = novel state = high intrinsic reward
    - Low error = familiar state = low intrinsic reward
    """

    def __init__(
        self,
        obs_dim: int = 70,
        embed_dim: int = 128,
        learning_rate: float = 1e-4,
        training_batch_size: int = 128,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        device: torch.device = torch.device("cpu"),
        active_mask: tuple[bool, ...] | None = None,
        # Normalization parameters (configurable per DRL expert review)
        normalization_initial_count: int = 100,
        normalization_min_variance: float = 0.01,
        reward_clip_max: float = 5.0,
    ):
        """Initialize RND with fixed and predictor networks.

        Args:
            obs_dim: Observation dimension
            embed_dim: Embedding dimension
            learning_rate: Learning rate for predictor network
            training_batch_size: Batch size for predictor training
            epsilon_start: Initial epsilon for epsilon-greedy
            epsilon_min: Minimum epsilon
            epsilon_decay: Epsilon decay rate
            device: Device for tensors
            active_mask: Optional mask for active observation dimensions (padding dimensions will be zeroed)
            normalization_initial_count: Initial pseudo-count for running mean/std (EXP-01 fix)
            normalization_min_variance: Variance floor for normalization (EXP-01 fix)
            reward_clip_max: Maximum intrinsic reward after normalization (Burda et al. 2018)
        """
        self.obs_dim = obs_dim
        self.embed_dim = embed_dim
        self.training_batch_size = training_batch_size
        self.device = device

        # Normalization parameters (stored for checkpoint serialization)
        self.normalization_initial_count = normalization_initial_count
        self.normalization_min_variance = normalization_min_variance
        self.reward_clip_max = reward_clip_max

        # Epsilon parameters
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # EXP-09: Validate active_mask for transfer learning concerns
        # Masking too many dimensions may destroy spatial information needed for
        # curriculum progression (e.g., position coordinates in Grid2D)
        if active_mask is not None:
            if len(active_mask) != obs_dim:
                raise ValueError(f"active_mask length ({len(active_mask)}) must match obs_dim ({obs_dim})")
            active_count = sum(active_mask)
            masked_ratio = 1.0 - (active_count / obs_dim)
            if masked_ratio > 0.5:
                warnings.warn(
                    f"RND active_mask has {masked_ratio:.0%} of dimensions masked "
                    f"({obs_dim - active_count}/{obs_dim}). This may harm transfer learning "
                    f"by destroying spatial information needed for curriculum progression.",
                    UserWarning,
                    stacklevel=2,
                )

        # Fixed network (random, frozen)
        self.fixed_network = RNDNetwork(obs_dim, embed_dim, active_mask=active_mask).to(device)
        for param in self.fixed_network.parameters():
            param.requires_grad = False

        # Predictor network (trained to match fixed)
        self.predictor_network = RNDNetwork(obs_dim, embed_dim, active_mask=active_mask).to(device)

        # Optimizer for predictor
        self.optimizer = torch.optim.Adam(self.predictor_network.parameters(), lr=learning_rate)

        # Observation buffer for mini-batch training
        self.obs_buffer: list[torch.Tensor] = []
        self.step_counter = 0

        # Running statistics for intrinsic reward normalization
        self.reward_rms = RunningMeanStd(
            initial_count=normalization_initial_count,
            min_variance=normalization_min_variance,
        )

    def select_actions(
        self,
        q_values: torch.Tensor,
        agent_states: BatchedAgentState,
        action_masks: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Select actions using epsilon-greedy with action masking.

        Args:
            q_values: Q-values for each action [batch, num_actions]
            agent_states: Current state (contains per-agent epsilons)
            action_masks: Optional action validity masks [batch, num_actions] bool

        Returns:
            actions: [batch] selected actions
        """
        return epsilon_greedy_action_selection(
            q_values=q_values,
            epsilons=agent_states.epsilons,
            action_masks=action_masks,
        )

    def compute_intrinsic_rewards(
        self,
        observations: torch.Tensor,  # [batch, obs_dim]
        update_stats: bool = False,
    ) -> torch.Tensor:
        """Compute normalized RND novelty signal (prediction error).

        Args:
            observations: [batch, obs_dim] state observations
            update_stats: If True, update running mean/std statistics (use during training rollouts)

        Returns:
            [batch] normalized intrinsic rewards
        """
        with torch.no_grad():
            target_features: torch.Tensor = self.fixed_network(observations)
            predicted_features: torch.Tensor = self.predictor_network(observations)
            # MSE per sample (high error = novel = high reward)
            mse_per_sample = ((target_features - predicted_features) ** 2).mean(dim=1)

            # Optionally update running statistics (only during training rollouts)
            if update_stats:
                mse_numpy = mse_per_sample.cpu().numpy()
                self.reward_rms.update(mse_numpy)

            # Normalize by running standard deviation
            # This brings intrinsic rewards to comparable magnitude with extrinsic rewards
            # EXP-01: Use variance floor to prevent reward explosion when variance is small
            effective_var = max(self.reward_rms.var, self.reward_rms.min_variance)
            normalized = mse_per_sample / (np.sqrt(effective_var) + 1e-8)

            # Clip rewards per Burda et al. (2018) - prevents extreme outliers
            # Intrinsic rewards are always >= 0 (MSE), clip to [0, reward_clip_max]
            clipped = torch.clamp(normalized, min=0.0, max=self.reward_clip_max)

        return cast(torch.Tensor, clipped)

    def update(self, batch: dict[str, torch.Tensor]) -> None:
        """Update predictor network from experience batch.

        Args:
            batch: Experience batch with 'observations' key
        """
        if "observations" not in batch:
            return

        observations = batch["observations"]

        # Add to buffer
        for i in range(observations.shape[0]):
            self.obs_buffer.append(observations[i].detach())

        # Train if buffer is full
        if len(self.obs_buffer) >= self.training_batch_size:
            self.update_predictor()

    def update_predictor(self) -> float:
        """Train predictor network on accumulated observations.

        Called every training_batch_size steps.

        Returns:
            Prediction loss (for logging)
        """
        if len(self.obs_buffer) < self.training_batch_size:
            return 0.0

        # Stack observations into batch
        obs_batch = torch.stack(self.obs_buffer[: self.training_batch_size]).to(self.device)

        # Clear buffer
        self.obs_buffer = self.obs_buffer[self.training_batch_size :]

        # Compute loss
        target = self.fixed_network(obs_batch).detach()
        predicted = self.predictor_network(obs_batch)
        loss = F.mse_loss(predicted, target)

        # Gradient step
        # EXP-02: Add gradient clipping for training stability with novel states
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.predictor_network.parameters(), max_norm=10.0)
        self.optimizer.step()

        return loss.item()

    # get_novelty_map() was removed (BUG-24 fix)
    # Reason: Unused debug visualization code with hardcoded observation assumptions.
    # It assumed 70-dim obs with meters at indices 64:70 and one-hot grid encoding,
    # which breaks with VFS-based observation layouts and different curriculum levels.
    # Per CLAUDE.md pre-release policy: delete unused code rather than maintaining it.

    def decay_epsilon(self) -> None:
        """Decay epsilon (call once per episode)."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def checkpoint_state(self) -> dict[str, Any]:
        """Return serializable state for checkpoint saving.

        Returns:
            Dict with network weights, optimizer state, epsilon, and normalization stats

        EXP-03: Now includes obs_buffer for checkpoint reproducibility.
        """
        return {
            "fixed_network": self.fixed_network.state_dict(),
            "predictor_network": self.predictor_network.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epsilon": self.epsilon,
            "epsilon_min": self.epsilon_min,
            "epsilon_decay": self.epsilon_decay,
            "obs_dim": self.obs_dim,
            "embed_dim": self.embed_dim,
            # Normalization parameters (configurable)
            "normalization_initial_count": self.normalization_initial_count,
            "normalization_min_variance": self.normalization_min_variance,
            "reward_clip_max": self.reward_clip_max,
            # Normalization statistics
            "reward_rms_mean": self.reward_rms.mean,
            "reward_rms_var": self.reward_rms.var,
            "reward_rms_count": self.reward_rms.count,
            # EXP-03: Save observation buffer for reproducibility
            "obs_buffer": [obs.cpu() for obs in self.obs_buffer],
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Restore from checkpoint.

        Args:
            state: Dict from checkpoint_state()

        Raises:
            ValueError: If checkpoint obs_dim doesn't match current configuration

        EXP-03: Added obs_dim validation and obs_buffer restoration.
        """
        # EXP-04: Validate obs_dim before loading to prevent cryptic errors
        checkpoint_obs_dim = state.get("obs_dim")
        if checkpoint_obs_dim is not None and checkpoint_obs_dim != self.obs_dim:
            raise ValueError(
                f"Checkpoint obs_dim mismatch: checkpoint has {checkpoint_obs_dim}, "
                f"current environment has {self.obs_dim}. "
                "This usually means loading a checkpoint from a different curriculum level."
            )

        self.fixed_network.load_state_dict(state["fixed_network"])
        self.predictor_network.load_state_dict(state["predictor_network"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.epsilon = state["epsilon"]
        self.epsilon_min = state["epsilon_min"]
        self.epsilon_decay = state["epsilon_decay"]

        # Restore normalization parameters (required - no backwards compatibility for pre-release)
        self.normalization_initial_count = state["normalization_initial_count"]
        self.normalization_min_variance = state["normalization_min_variance"]
        self.reward_clip_max = state["reward_clip_max"]

        # Restore normalization statistics
        self.reward_rms.mean = state["reward_rms_mean"]
        self.reward_rms.var = state["reward_rms_var"]
        self.reward_rms.count = state["reward_rms_count"]
        # Also restore min_variance on the RunningMeanStd instance
        self.reward_rms.min_variance = self.normalization_min_variance

        # EXP-03: Restore observation buffer for reproducibility (required)
        self.obs_buffer = [obs.to(self.device) for obs in state["obs_buffer"]]
