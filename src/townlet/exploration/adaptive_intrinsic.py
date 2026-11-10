"""Adaptive intrinsic exploration with variance-based annealing."""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Literal

import torch

from townlet.config.bac_options import RNDOptions
from townlet.exploration.base import ExplorationStrategy
from townlet.exploration.rnd import PredictorServiceCounters, PredictorServiceReceipt, RNDExploration
from townlet.exploration.world_curiosity_state import ServiceClock, WorldRNGState
from townlet.training.state import BatchedAgentState


@dataclass
class _PreparedAdaptive:
    owner: object
    attributes: dict[str, Any]
    consumed: bool


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
        variance_threshold: float = 100.0,  # Increased from 10.0 to prevent premature annealing
        min_survival_fraction: float = 0.4,  # Fraction of max_episode_length (e.g., 0.4 = 40%)
        max_episode_length: int = 500,  # From curriculum config - used to compute absolute threshold
        survival_window: int = 100,
        decay_rate: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        device: torch.device = torch.device("cpu"),
        *,
        rng: WorldRNGState | None,
        service_clock_unit: Literal["vector_tick", "world_eligible_admission"],
    ):
        """Initialize adaptive intrinsic exploration.

        Args:
            obs_dim: Observation dimension
            embed_dim: RND embedding dimension
            rnd_learning_rate: Learning rate for RND predictor
            rnd_training_batch_size: Batch size for RND training
            initial_intrinsic_weight: Starting intrinsic weight
            min_intrinsic_weight: Minimum intrinsic weight (floor)
            variance_threshold: Variance threshold for annealing trigger
            min_survival_fraction: Fraction of max_episode_length before allowing annealing (prevents "stable failure")
            max_episode_length: Maximum steps per episode (from curriculum config)
            survival_window: Number of episodes to track for variance
            decay_rate: Exponential decay rate (weight *= decay_rate)
            epsilon_start: Initial epsilon for epsilon-greedy
            epsilon_min: Minimum epsilon
            epsilon_decay: Epsilon decay rate
            device: Device for tensors
        """
        self._validate_config(
            {
                "initial_intrinsic_weight": initial_intrinsic_weight,
                "min_intrinsic_weight": min_intrinsic_weight,
                "variance_threshold": variance_threshold,
                "min_survival_fraction": min_survival_fraction,
                "max_episode_length": max_episode_length,
                "survival_window": survival_window,
                "decay_rate": decay_rate,
            }
        )
        # RND instance (composition)
        self.rnd = RNDExploration(
            obs_dim=obs_dim,
            embed_dim=embed_dim,
            learning_rate=rnd_learning_rate,
            training_batch_size=rnd_training_batch_size,
            epsilon_start=epsilon_start,
            epsilon_min=epsilon_min,
            epsilon_decay=epsilon_decay,
            device=device,
            rng=rng,
            service_clock_unit=service_clock_unit,
        )

        # Annealing parameters
        self.initial_intrinsic_weight = initial_intrinsic_weight
        self.current_intrinsic_weight = initial_intrinsic_weight
        self.min_intrinsic_weight = min_intrinsic_weight
        self.variance_threshold = variance_threshold
        self.min_survival_fraction = min_survival_fraction
        self.max_episode_length = max_episode_length
        self.min_survival_for_annealing = int(min_survival_fraction * max_episode_length)  # Compute absolute threshold
        self.survival_window = survival_window
        self.decay_rate = decay_rate
        self.device = device

        # Survival tracking
        self.survival_history: list[float] = []

    @staticmethod
    def _validate_config(config: dict[str, Any]) -> None:
        for name, value in config.items():
            if name in {"max_episode_length", "survival_window"}:
                if type(value) is not int or value <= 0:
                    raise ValueError(f"Adaptive {name} must be a positive exact integer")
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Adaptive {name} must be a finite nonnegative scalar")
        if config["min_intrinsic_weight"] > config["initial_intrinsic_weight"]:
            raise ValueError("Adaptive minimum weight exceeds initial weight")
        if config["min_survival_fraction"] > 1 or config["decay_rate"] > 1:
            raise ValueError("Adaptive survival fraction and decay rate must be in [0,1]")
        try:
            int(config["min_survival_fraction"] * config["max_episode_length"])
        except (OverflowError, ValueError) as error:
            raise ValueError("Adaptive derived survival threshold is not representable") from error

    def _config(self) -> dict[str, Any]:
        return {
            "initial_intrinsic_weight": self.initial_intrinsic_weight,
            "min_intrinsic_weight": self.min_intrinsic_weight,
            "variance_threshold": self.variance_threshold,
            "min_survival_fraction": self.min_survival_fraction,
            "max_episode_length": self.max_episode_length,
            "survival_window": self.survival_window,
            "decay_rate": self.decay_rate,
        }

    @property
    def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
        return self.rnd.service_clock_unit

    def configure_service(self, options: RNDOptions) -> None:
        self.rnd.configure_service(options)

    def predictor_service_counters(self) -> PredictorServiceCounters:
        return self.rnd.predictor_service_counters()

    def admit_and_service_at(self, observations: torch.Tensor, *, clock: ServiceClock) -> PredictorServiceReceipt:
        return self.rnd.admit_and_service_at(observations, clock=clock)

    def admit_and_service(self, observations: torch.Tensor, *, vector_tick: int) -> PredictorServiceReceipt:
        return self.rnd.admit_and_service(observations, vector_tick=vector_tick)

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

    def update_on_episode_end(self, survival_time: float) -> None:
        """Update survival history and check for annealing trigger.

        Call after each episode completes.

        Args:
            survival_time: Number of steps agent survived this episode
        """
        self._history_decision(self.survival_history)
        prospective = [*self.survival_history, survival_time][-self.survival_window :]
        anneal = self._history_decision(prospective)
        weight = (
            max(self.current_intrinsic_weight * self.decay_rate, self.min_intrinsic_weight) if anneal else self.current_intrinsic_weight
        )
        self.survival_history, self.current_intrinsic_weight = prospective, weight

    def _history_decision(self, history: list[float]) -> bool:
        if type(history) is not list or len(history) > self.survival_window:
            raise ValueError("Adaptive history must be an owned list within the selected window")
        for value in history:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError("Adaptive survival history requires finite nonnegative scalars")
        try:
            values = torch.tensor(history, dtype=torch.float32)
        except (RuntimeError, OverflowError) as error:
            raise ValueError("Adaptive history cannot be represented for variance computation") from error
        if not torch.isfinite(values).all().item():
            raise ValueError("Adaptive history is not finite in float32")
        if len(history) < 10:
            return False
        variance, mean = torch.var(values).item(), torch.mean(values).item()
        if not math.isfinite(variance) or not math.isfinite(mean):
            raise ValueError("Adaptive history variance/mean is nonfinite")
        return variance < self.variance_threshold and mean > self.min_survival_for_annealing

    def should_anneal(self) -> bool:
        """Preserve the variance estimator, threshold and minimum ten survivals."""
        return self._history_decision(self.survival_history)

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
        """Current native snapshot with independent nested tensors and history."""
        return deepcopy(
            {
                "schema": "adaptive-intrinsic-state-v3",
                "rnd_state": self.rnd.checkpoint_state(),
                **self._config(),
                "current_intrinsic_weight": self.current_intrinsic_weight,
                "min_survival_for_annealing": self.min_survival_for_annealing,
                "survival_history": self.survival_history,
            }
        )

    def validate_state(self, state: dict[str, Any]) -> None:
        self.prepare_state(state)

    def prepare_state(self, state: dict[str, Any]) -> _PreparedAdaptive:
        """Validate all outer semantics before preparing nested learned state."""
        try:
            state = deepcopy(state)
            if (
                not isinstance(state, dict)
                or state.keys() != self.checkpoint_state().keys()
                or state["schema"] != "adaptive-intrinsic-state-v3"
            ):
                raise ValueError("Adaptive requires complete current native state")
            config = {name: state[name] for name in self._config()}
            self._validate_config(config)
            if config != self._config():
                raise ValueError("Adaptive checkpoint configuration differs from destination")
            threshold = state["min_survival_for_annealing"]
            if type(threshold) is not int or threshold != int(config["min_survival_fraction"] * config["max_episode_length"]):
                raise ValueError("Adaptive derived survival threshold is inconsistent")
            weight = state["current_intrinsic_weight"]
            if (
                isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or not math.isfinite(weight)
                or not self.min_intrinsic_weight <= weight <= self.initial_intrinsic_weight
            ):
                raise ValueError("Adaptive current weight is outside configured bounds")
            self._history_decision(state["survival_history"])
            candidate = deepcopy(self)
            candidate.rnd.load_state(state["rnd_state"])
            candidate.current_intrinsic_weight = weight
            candidate.survival_history = state["survival_history"]
            return _PreparedAdaptive(self, candidate.__dict__, False)
        except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
            raise ValueError("Adaptive checkpoint is malformed") from error

    def prepare_learning_reset(self, *, fresh: AdaptiveIntrinsicExploration) -> _PreparedAdaptive:
        """Reset owned adaptive learning while retaining the inner service lifetime."""
        if type(fresh) is not AdaptiveIntrinsicExploration or fresh is self:
            raise ValueError("Adaptive reset requires a distinct actual adaptive factory candidate")
        self.validate_state(self.checkpoint_state())
        fresh.validate_state(fresh.checkpoint_state())
        if self._config() != fresh._config() or self.device != fresh.device:
            raise ValueError("Adaptive reset candidate differs from retained authored configuration")
        if fresh.survival_history or fresh.current_intrinsic_weight != fresh.initial_intrinsic_weight:
            raise ValueError("Adaptive reset candidate must have fresh history and initial weight")
        prepared_rnd = self.rnd.prepare_learning_reset(fresh=fresh.rnd)
        candidate = deepcopy(self)
        # The nested handle is bound to the old inner owner. Its already-owned
        # attributes become the off-side inner candidate without touching live state.
        candidate.rnd.__dict__ = prepared_rnd.attributes
        prepared_rnd.consumed = True
        candidate.survival_history = []
        candidate.current_intrinsic_weight = self.initial_intrinsic_weight
        return _PreparedAdaptive(self, candidate.__dict__, False)

    def install_state(self, prepared: _PreparedAdaptive) -> None:
        if type(prepared) is not _PreparedAdaptive or prepared.owner is not self or prepared.consumed:
            raise ValueError("Adaptive prepared state belongs to another destination or was consumed")
        prepared.consumed = True
        self.__dict__ = prepared.attributes

    def load_state(self, state: dict[str, Any]) -> None:
        self.install_state(self.prepare_state(state))
