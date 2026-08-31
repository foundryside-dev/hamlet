"""
Static curriculum manager (trivial implementation).

Always returns the same curriculum decision. Used for baseline testing
and to validate the curriculum interface works.
"""

from __future__ import annotations

import math
from typing import Any

import torch

from townlet.curriculum.base import CurriculumManager
from townlet.training.state import BatchedAgentState, CurriculumDecision


class StaticCurriculum(CurriculumManager):
    """
    Static curriculum - no adaptation.

    Returns the same curriculum decision for all agents at all times.
    Useful for baseline experiments and interface validation.
    """

    _CHECKPOINT_KEYS = frozenset({"difficulty_level", "reward_mode", "active_meters", "depletion_multiplier"})

    def __init__(
        self,
        difficulty_level: float = 0.5,
        reward_mode: str = "shaped",
        active_meters: list[str] | None = None,
        depletion_multiplier: float = 1.0,
    ):
        """
        Initialize static curriculum.

        Args:
            difficulty_level: Fixed difficulty (0.0-1.0)
            reward_mode: 'shaped' or 'sparse'
            active_meters: Which meters are active (default: all 6)
            depletion_multiplier: Depletion rate multiplier
        """
        self.difficulty_level = difficulty_level
        self.reward_mode = reward_mode
        self.active_meters = active_meters or ["energy", "hygiene", "satiation", "money", "mood", "social"]
        self.depletion_multiplier = depletion_multiplier
        self.transition_events: list[dict[str, Any]] = []
        self.num_agents: int | None = None
        self.tracker: _StaticTracker | None = None

    def initialize_population(self, num_agents: int) -> None:
        """Static curriculum has no per-agent state; record agent count and reset events."""
        self.num_agents = num_agents
        self.transition_events.clear()
        self.tracker = _StaticTracker(num_agents)

    def get_batch_decisions(
        self,
        agent_states: BatchedAgentState,
        agent_ids: list[str],
    ) -> list[CurriculumDecision]:
        """
        Get curriculum decisions (same for all agents).

        Args:
            agent_states: Current agent state (ignored)
            agent_ids: List of agent IDs

        Returns:
            List of identical CurriculumDecisions
        """
        decision = CurriculumDecision(
            difficulty_level=self.difficulty_level,
            active_meters=self.active_meters,
            depletion_multiplier=self.depletion_multiplier,
            reward_mode=self.reward_mode,
            reason=f"Static curriculum (difficulty={self.difficulty_level})",
        )

        # Return same decision for all agents
        return [decision] * len(agent_ids)

    def checkpoint_state(self) -> dict[str, Any]:
        """
        Return serializable state.

        Returns:
            Dict with all configuration
        """
        return {
            "difficulty_level": self.difficulty_level,
            "reward_mode": self.reward_mode,
            "active_meters": self.active_meters,
            "depletion_multiplier": self.depletion_multiplier,
        }

    def validate_checkpoint_state(self, state: dict[str, Any]) -> None:
        """Validate the exact static-curriculum state without mutation."""
        if not isinstance(state, dict):
            raise ValueError(f"Static curriculum checkpoint must be a dictionary; got {type(state).__name__}.")

        state_keys = set(state)
        if state_keys != self._CHECKPOINT_KEYS:
            missing = sorted(self._CHECKPOINT_KEYS - state_keys)
            unknown = sorted(state_keys - self._CHECKPOINT_KEYS)
            raise ValueError(f"Static curriculum checkpoint key set mismatch: missing={missing}, unknown={unknown}.")

        for field in ("difficulty_level", "depletion_multiplier"):
            value = state[field]
            if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(float(value)):
                raise ValueError(f"Static curriculum checkpoint {field} must be a finite number.")
        if not isinstance(state["reward_mode"], str):
            raise ValueError("Static curriculum checkpoint reward_mode must be a string.")
        active_meters = state["active_meters"]
        if not isinstance(active_meters, list) or any(not isinstance(name, str) for name in active_meters):
            raise ValueError("Static curriculum checkpoint active_meters must be a list of strings.")

    def load_state(self, state: dict[str, Any]) -> None:
        """
        Restore from checkpoint.

        Args:
            state: Dict from checkpoint_state()
        """
        self.validate_checkpoint_state(state)
        self.difficulty_level = state["difficulty_level"]
        self.reward_mode = state["reward_mode"]
        self.active_meters = state["active_meters"]
        self.depletion_multiplier = state["depletion_multiplier"]


class _StaticTracker:
    """Minimal tracker so logging paths can read curriculum stage tensors."""

    def __init__(self, num_agents: int):
        self.num_agents = num_agents
        self.agent_stages = torch.zeros(num_agents, dtype=torch.long)

    def update_step(self, rewards: torch.Tensor, dones: torch.Tensor) -> None:  # noqa: ARG002
        # Static curriculum does not change stage; no-op
        return None
