"""Adaptive intrinsic exploration with variance-based annealing."""

from typing import Any

import torch

from townlet.exploration.base import ExplorationStrategy
from townlet.exploration.rnd import RNDExploration
from townlet.training.state import BatchedAgentState


class AdaptiveIntrinsicExploration(ExplorationStrategy):
    """RND with adaptive annealing based on survival variance.

    Automatically reduces intrinsic weight when agent demonstrates
    consistent performance (low survival time variance).

    Composition: Contains RNDExploration instance for novelty computation.
    """

    def __init__(
        self,
        obs_dim: int = 70,
        embed_dim: int = 128,
        rnd_learning_rate: float = 1e-4,
        rnd_training_batch_size: int = 128,
        initial_intrinsic_weight: float = 1.0,
        min_intrinsic_weight: float = 0.0,
        variance_threshold: float = 100.0,  # When use_coefficient_of_variation=false: absolute variance
        use_coefficient_of_variation: bool = True,  # NEW: Use CV instead of variance
        min_survival_fraction: float = 0.4,  # Fraction of max_episode_length (e.g., 0.4 = 40%)
        max_episode_length: int = 500,  # From curriculum config - used to compute absolute threshold
        survival_window: int = 100,
        decay_rate: float = 0.99,
        hysteresis_cooldown: int = 0,  # NEW: Episodes between annealing triggers
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        device: torch.device = torch.device("cpu"),
        active_mask: tuple[bool, ...] | None = None,
        # RND normalization parameters (passed through to RNDExploration)
        normalization_initial_count: int = 100,
        normalization_min_variance: float = 0.01,
        reward_clip_max: float = 5.0,
    ):
        """Initialize adaptive intrinsic exploration.

        Args:
            obs_dim: Observation dimension
            embed_dim: RND embedding dimension
            rnd_learning_rate: Learning rate for RND predictor
            rnd_training_batch_size: Batch size for RND training
            initial_intrinsic_weight: Starting intrinsic weight
            min_intrinsic_weight: Minimum intrinsic weight (floor)
            variance_threshold: Threshold for annealing trigger (variance or CV depending on mode)
            use_coefficient_of_variation: If True, use CV (std/mean) instead of raw variance
            min_survival_fraction: Fraction of max_episode_length before allowing annealing (prevents "stable failure")
            max_episode_length: Maximum steps per episode (from curriculum config)
            survival_window: Number of episodes to track for variance
            decay_rate: Exponential decay rate (weight *= decay_rate)
            hysteresis_cooldown: Minimum episodes between annealing triggers (prevents feedback loop)
            epsilon_start: Initial epsilon for epsilon-greedy
            epsilon_min: Minimum epsilon
            epsilon_decay: Epsilon decay rate
            device: Device for tensors
            active_mask: Optional mask for active observation dimensions (padding dimensions will be zeroed)
            normalization_initial_count: Initial pseudo-count for running mean/std (EXP-01 fix)
            normalization_min_variance: Variance floor for normalization (EXP-01 fix)
            reward_clip_max: Maximum intrinsic reward after normalization (Burda et al. 2018)

        Raises:
            ValueError: If parameters are out of valid range

        EXP-05: Added parameter validation to catch catastrophic misconfigurations.
        """
        # EXP-05: Validate parameters to prevent silent failures
        if not 0.0 < decay_rate < 1.0:
            raise ValueError(
                f"decay_rate must be in (0, 1), got {decay_rate}. "
                f"Values >= 1 would increase exploration weight over time (opposite of intended)."
            )
        if variance_threshold <= 0:
            raise ValueError(f"variance_threshold must be > 0, got {variance_threshold}")
        if not 0.0 <= min_survival_fraction <= 1.0:
            raise ValueError(f"min_survival_fraction must be in [0, 1], got {min_survival_fraction}")
        if max_episode_length <= 0:
            raise ValueError(f"max_episode_length must be > 0, got {max_episode_length}")
        if survival_window <= 0:
            raise ValueError(f"survival_window must be > 0, got {survival_window}")
        if initial_intrinsic_weight < 0:
            raise ValueError(f"initial_intrinsic_weight cannot be negative, got {initial_intrinsic_weight}")
        if min_intrinsic_weight < 0:
            raise ValueError(f"min_intrinsic_weight cannot be negative, got {min_intrinsic_weight}")
        if hysteresis_cooldown < 0:
            raise ValueError(f"hysteresis_cooldown cannot be negative, got {hysteresis_cooldown}")

        # RND instance (composition) with configurable normalization
        self.rnd = RNDExploration(
            obs_dim=obs_dim,
            embed_dim=embed_dim,
            learning_rate=rnd_learning_rate,
            training_batch_size=rnd_training_batch_size,
            epsilon_start=epsilon_start,
            epsilon_min=epsilon_min,
            epsilon_decay=epsilon_decay,
            device=device,
            active_mask=active_mask,
            normalization_initial_count=normalization_initial_count,
            normalization_min_variance=normalization_min_variance,
            reward_clip_max=reward_clip_max,
        )

        # Annealing parameters
        self.current_intrinsic_weight = initial_intrinsic_weight
        self.min_intrinsic_weight = min_intrinsic_weight
        self.variance_threshold = variance_threshold
        self.use_coefficient_of_variation = use_coefficient_of_variation
        self.min_survival_fraction = min_survival_fraction
        self.max_episode_length = max_episode_length
        self.min_survival_for_annealing = int(min_survival_fraction * max_episode_length)  # Compute absolute threshold
        self.survival_window = survival_window
        self.decay_rate = decay_rate
        self.hysteresis_cooldown = hysteresis_cooldown
        self.episodes_since_last_anneal = hysteresis_cooldown  # Start ready to anneal
        # EXP-06: Removed unused self.device field (RND handles device internally)

        # Survival tracking
        # EXP-07: Changed type from list[float] to list[int] - survival times are discrete steps
        self.survival_history: list[int] = []

    def select_actions(
        self,
        q_values: torch.Tensor,
        agent_states: BatchedAgentState,
        action_masks: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Select actions using epsilon-greedy with action masking (delegates to RND).

        Args:
            q_values: Q-values for each action [batch, num_actions]
            agent_states: Current state (contains per-agent epsilons)
            action_masks: Optional action validity masks [batch, num_actions] bool

        Returns:
            actions: [batch] selected actions
        """
        return self.rnd.select_actions(q_values, agent_states, action_masks)

    def compute_intrinsic_rewards(
        self,
        observations: torch.Tensor,
        update_stats: bool = False,
    ) -> torch.Tensor:
        """Compute intrinsic rewards (normalized RND novelty).

        Note: Weight is applied in replay buffer sampling, NOT here.
        This prevents double-weighting bug.

        Args:
            observations: [batch, obs_dim] state observations
            update_stats: If True, update running mean/std statistics (use during training rollouts)

        Returns:
            [batch] normalized intrinsic rewards (unweighted)
        """
        # Get RND novelty (already normalized)
        # Weight will be applied once in replay buffer sampling
        return self.rnd.compute_intrinsic_rewards(observations, update_stats=update_stats)

    def update(self, batch: dict[str, torch.Tensor]) -> None:
        """Update RND predictor network from experience batch.

        Args:
            batch: Experience batch with 'observations' key
        """
        self.rnd.update(batch)

    def update_on_episode_end(self, survival_time: int) -> None:
        """Update survival history and check for annealing trigger.

        Call after each episode completes.

        Args:
            survival_time: Number of steps agent survived this episode (discrete count)

        EXP-07: Changed type from float to int - survival times are discrete step counts.
        """
        self.survival_history.append(survival_time)
        self.episodes_since_last_anneal += 1

        # Keep only recent window
        if len(self.survival_history) > self.survival_window:
            self.survival_history = self.survival_history[-self.survival_window :]

        # Check for annealing (includes hysteresis check)
        if self.should_anneal():
            self.anneal_weight()
            self.episodes_since_last_anneal = 0  # Reset hysteresis counter

    def should_anneal(self) -> bool:
        """Check if variability is below threshold AND performance is good.

        Supports two modes:
        - Variance mode (legacy): threshold is absolute variance of survival times
        - CV mode (recommended): threshold is coefficient of variation (std/mean)

        CV mode is curriculum-agnostic because it normalizes by mean, so the same
        threshold works across L0 (500 max steps) and L3 (1000 max steps).

        Returns:
            True if agent performance is consistent enough to reduce exploration

        Note:
            Uses incremental window checking to avoid abrupt behavior changes
            when hitting full window size. For small windows (< 10), waits for
            the full window. For large windows, starts checking at 10 episodes.
            Always requires at least 2 samples for variance calculation.
        """
        # Need minimum data for reliable variance/CV calculation
        # Respect small windows instead of enforcing a hidden minimum
        min_required = min(self.survival_window, 10)
        if len(self.survival_history) < min_required:
            return False

        # Hysteresis check: don't anneal too frequently
        if self.episodes_since_last_anneal < self.hysteresis_cooldown:
            return False

        # Use whatever recent data we have (up to window size)
        # This allows incremental checking instead of waiting for full window
        window_size = min(self.survival_window, len(self.survival_history))
        recent_survivals = torch.tensor(
            self.survival_history[-window_size:],
            dtype=torch.float32,
        )
        mean_survival = torch.mean(recent_survivals).item()
        std_survival = torch.std(recent_survivals, unbiased=False).item()

        # Compute variability metric based on mode
        if self.use_coefficient_of_variation:
            # CV = std / mean (curriculum-agnostic)
            # Add small epsilon to prevent division by zero
            variability = std_survival / (mean_survival + 1e-8)
        else:
            # Legacy mode: absolute variance
            variability = std_survival**2  # variance = std^2

        # DEFENSIVE: Only anneal if BOTH low variability AND good performance
        # Low variability + low survival = "consistently failing" (NOT ready to anneal)
        # Low variability + high survival = "consistently succeeding" (ready to anneal)
        return variability < self.variance_threshold and mean_survival > self.min_survival_for_annealing

    def anneal_weight(self) -> None:
        """Reduce intrinsic weight via exponential decay."""
        new_weight = self.current_intrinsic_weight * self.decay_rate
        self.current_intrinsic_weight = max(new_weight, self.min_intrinsic_weight)

    def get_intrinsic_weight(self) -> float:
        """Get current intrinsic weight (for logging/visualization)."""
        return self.current_intrinsic_weight

    def decay_epsilon(self) -> None:
        """Decay epsilon (delegates to RND)."""
        self.rnd.decay_epsilon()

    def checkpoint_state(self) -> dict[str, Any]:
        """Return serializable state for checkpoint saving.

        Returns:
            Dict with RND state, intrinsic weight, and survival history
        """
        return {
            "rnd_state": self.rnd.checkpoint_state(),
            "current_intrinsic_weight": self.current_intrinsic_weight,
            "min_intrinsic_weight": self.min_intrinsic_weight,
            "variance_threshold": self.variance_threshold,
            "use_coefficient_of_variation": self.use_coefficient_of_variation,
            "min_survival_fraction": self.min_survival_fraction,
            "max_episode_length": self.max_episode_length,
            "survival_window": self.survival_window,
            "decay_rate": self.decay_rate,
            "hysteresis_cooldown": self.hysteresis_cooldown,
            "episodes_since_last_anneal": self.episodes_since_last_anneal,
            "survival_history": self.survival_history,
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Restore from checkpoint.

        Args:
            state: Dict from checkpoint_state()
        """
        self.rnd.load_state(state["rnd_state"])
        self.current_intrinsic_weight = state["current_intrinsic_weight"]
        self.min_intrinsic_weight = state["min_intrinsic_weight"]
        self.variance_threshold = state["variance_threshold"]
        self.survival_window = state["survival_window"]
        self.decay_rate = state["decay_rate"]
        self.min_survival_fraction = state["min_survival_fraction"]
        self.max_episode_length = state["max_episode_length"]
        self.min_survival_for_annealing = int(self.min_survival_fraction * self.max_episode_length)
        self.survival_history = state["survival_history"]
        # Restore annealing fields (required - no backwards compatibility for pre-release)
        self.use_coefficient_of_variation = state["use_coefficient_of_variation"]
        self.hysteresis_cooldown = state["hysteresis_cooldown"]
        self.episodes_since_last_anneal = state["episodes_since_last_anneal"]
