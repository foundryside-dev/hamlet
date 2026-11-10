"""Fixed decisions with the same current completion and retry protocol."""

from typing import Any

from townlet.curriculum.adversarial import CompletionCurriculum, finite_number
from townlet.training.episode import LaneOutcome
from townlet.training.state import BatchedAgentState, CurriculumDecision


class StaticCurriculum(CompletionCurriculum):
    """Retain completion ownership while keeping every authored decision fixed."""

    def __init__(
        self, *, commit_mode: str, difficulty_level: float, reward_mode: str, active_meters: list[str], depletion_multiplier: float
    ):
        if commit_mode != "completion":
            raise ValueError("Only the current completion protocol is supported")
        if not finite_number(difficulty_level) or not 0 <= difficulty_level <= 1:
            raise ValueError("Static difficulty must be within [0, 1]")
        if not finite_number(depletion_multiplier) or depletion_multiplier < 0:
            raise ValueError("Static depletion multiplier must be finite and nonnegative")
        if not isinstance(reward_mode, str) or not reward_mode:
            raise ValueError("Static reward mode must be a nonempty label")
        if not isinstance(active_meters, list) or any(not isinstance(name, str) or not name for name in active_meters):
            raise ValueError("Static meter labels must be a list of nonempty strings")
        super().__init__(
            "static",
            {
                "commit_mode": commit_mode,
                "difficulty_level": float(difficulty_level),
                "reward_mode": reward_mode,
                "active_meters": active_meters.copy(),
                "depletion_multiplier": float(depletion_multiplier),
            },
        )

    def _initial_lane(self) -> dict[str, Any]:
        return {"stage": 0, "dwell": 0, "episodes_at_stage": 0, "difficulty": self._config["difficulty_level"]}

    def _advance_lane(self, lane: dict[str, Any], event: LaneOutcome, previous_fraction: float) -> None:
        """Record the lane clock without changing its fixed decision or stage."""
        lane["dwell"] += event.outcome.survival_time
        lane["episodes_at_stage"] += 1
        return None

    def get_batch_decisions(self, agent_states: BatchedAgentState | None, agent_ids: list[str]) -> list[CurriculumDecision]:
        self._body()
        if len(agent_ids) != self.num_agents:
            raise ValueError("Decision identities must cover initialized lanes")
        return [
            CurriculumDecision(
                difficulty_level=self._config["difficulty_level"],
                active_meters=self._config["active_meters"].copy(),
                depletion_multiplier=self._config["depletion_multiplier"],
                reward_mode=self._config["reward_mode"],
                reason=f"Static curriculum (difficulty={self._config['difficulty_level']})",
            )
            for _ in agent_ids
        ]

    def get_stage_info(self, agent_idx: int) -> dict[str, Any]:
        info = self._stage_info(agent_idx)
        info.update(difficulty_mode="fixed", adaptation_rate=None, adaptation_rate_active=False, adaptation_rate_units="inactive")
        return info
