"""
Epsilon-greedy exploration strategy (vectorized).

Simple baseline: epsilon probability of random action, 1-epsilon probability
of greedy action. No intrinsic motivation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import torch

from townlet.exploration.action_selection import epsilon_greedy_action_selection
from townlet.exploration.base import ExplorationStrategy
from townlet.training.state import BatchedAgentState


@dataclass(slots=True)
class _PreparedEpsilon:
    owner: NoneExploration
    epsilon: float
    decay: float
    minimum: float
    used: bool


def _diagnostics(state: dict[str, Any]) -> tuple[float, float, float]:
    if not isinstance(state, Mapping) or set(state) != {"epsilon", "epsilon_decay", "epsilon_min"}:
        raise ValueError("epsilon checkpoint requires exactly its three diagnostic fields")
    values = []
    for name in ("epsilon", "epsilon_decay", "epsilon_min"):
        value = state[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} requires a finite number")
        try:
            finite = math.isfinite(value)
        except OverflowError as error:
            raise ValueError(f"{name} requires a finite number") from error
        if not finite:
            raise ValueError(f"{name} requires a finite number")
        values.append(value)
    # Preserve ordinary finite numeric transport; reset has separate policy bounds.
    return values[0], values[1], values[2]


class EpsilonGreedyExploration(ExplorationStrategy):
    """
    Vectorized epsilon-greedy exploration.

    No intrinsic motivation - just simple epsilon-greedy action selection.
    Epsilon decays over time with exponential schedule.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        epsilon_decay: float = 0.995,
        epsilon_min: float = 0.01,
    ):
        """
        Initialize epsilon-greedy exploration.

        Args:
            epsilon: Initial exploration rate (1.0 = full random)
            epsilon_decay: Decay per episode (0.995 = ~1% decay)
            epsilon_min: Minimum epsilon (prevents pure greedy)
        """
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

    def select_actions(
        self,
        q_values: torch.Tensor,  # [batch, num_actions]
        agent_states: BatchedAgentState,
        action_masks: torch.Tensor | None = None,  # [batch, num_actions] bool
    ) -> torch.Tensor:
        """
        Select actions with epsilon-greedy strategy and action masking.

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
        """
        Compute intrinsic rewards (none for epsilon-greedy).

        Args:
            observations: Current observations

        Returns:
            intrinsic_rewards: [batch] all zeros
        """
        batch_size = observations.shape[0]
        return torch.zeros(batch_size, device=observations.device)

    def update(self, batch: dict[str, torch.Tensor]) -> None:
        """
        Update exploration networks (no-op for epsilon-greedy).

        Args:
            batch: Experience batch (ignored)
        """
        pass  # No networks to update

    def decay_epsilon(self) -> None:
        """Decay epsilon (call once per episode)."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def checkpoint_state(self) -> dict[str, Any]:
        """
        Return serializable state.

        Returns:
            Dict with epsilon state
        """
        return {
            "epsilon": self.epsilon,
            "epsilon_decay": self.epsilon_decay,
            "epsilon_min": self.epsilon_min,
        }

    def load_state(self, state: dict[str, Any]) -> None:
        """Restore the diagnostic triple, including explicit base-class callers."""
        epsilon, decay, minimum = _diagnostics(state)
        self.epsilon = epsilon
        self.epsilon_decay = decay
        self.epsilon_min = minimum


class NoneExploration(EpsilonGreedyExploration):
    """Concrete no-novelty backend with its own native preparation contract.

    Global selectors and other diagnostic subclasses share EPS behavior without
    inheriting this family's opaque prepared-state or reset signatures.
    """

    def prepare_state(self, state: dict[str, Any]) -> _PreparedEpsilon:
        """Validate finite diagnostic transport off-side, without policy bounds."""
        epsilon, decay, minimum = _diagnostics(state)
        return _PreparedEpsilon(self, epsilon, decay, minimum, used=False)

    def install_state(self, prepared: _PreparedEpsilon) -> None:
        """Publish an already-qualified, destination-bound diagnostic candidate."""
        if type(prepared) is not _PreparedEpsilon or prepared.owner is not self or prepared.used:
            raise ValueError("epsilon preparation is foreign, invalid or already consumed")
        self.epsilon = prepared.epsilon
        self.epsilon_decay = prepared.decay
        self.epsilon_min = prepared.minimum
        prepared.used = True

    def prepare_learning_reset(self, *, fresh: NoneExploration) -> _PreparedEpsilon:
        """Retain diagnostics for genuine none; the outer owner qualifies freshness."""
        if type(self) is not NoneExploration or type(fresh) is not NoneExploration or fresh is self:
            raise ValueError("none reset requires distinct exact none family owners")
        epsilon, decay, minimum = _diagnostics(self.checkpoint_state())
        start, fresh_decay, fresh_minimum = _diagnostics(fresh.checkpoint_state())
        if decay != fresh_decay or minimum != fresh_minimum or not minimum <= epsilon <= start:
            raise ValueError("none reset diagnostics disagree with the selected fresh constructor")
        return _PreparedEpsilon(self, epsilon, decay, minimum, used=False)
