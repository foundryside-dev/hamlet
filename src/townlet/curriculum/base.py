"""Current completion-driven curriculum interfaces."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from townlet.training.episode import FrozenLaneOutcome, LaneOutcome
from townlet.training.state import BatchedAgentState, CurriculumDecision


@dataclass(frozen=True)
class PreparedCurriculumOutcomes:
    """An owner-bound, generation-pinned immutable completion handoff."""

    owner_token: object
    generation: int
    outcomes: tuple[FrozenLaneOutcome, ...]


class PreparedNativeCurriculum:
    """Source-issued data for one genuine native restore finalizer."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> Any:
        raise TypeError("Native curriculum state must be prepared by its receiving owner")

    def __reduce__(self) -> Any:
        raise TypeError("Native curriculum preparations cannot be copied or serialized")


class CurriculumManager(ABC):
    """One completion protocol; decisions only read previously committed state."""

    @abstractmethod
    def initialize_population(self, num_agents: int) -> None:
        """Start a new population with no invented completion history."""
        raise NotImplementedError

    @abstractmethod
    def prepare_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> PreparedCurriculumOutcomes:
        """Validate and own the whole sequence without mutation or RNG use."""
        raise NotImplementedError

    @abstractmethod
    def commit_prepared_episode_outcomes(self, prepared: PreparedCurriculumOutcomes) -> None:
        """Install prepared effects and identity receipts once, including retries."""
        raise NotImplementedError

    def commit_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> None:
        """Prepare and install an owned sequence through the one current protocol."""
        self.commit_prepared_episode_outcomes(self.prepare_episode_outcomes(outcomes))

    @abstractmethod
    def get_batch_decisions(self, agent_states: BatchedAgentState | None, agent_ids: list[str]) -> list[CurriculumDecision]:
        """Read committed decisions in lane order without changing state."""
        raise NotImplementedError

    @abstractmethod
    def get_stage_info(self, agent_idx: int) -> dict[str, Any]:
        """Read current stage, completion metrics and truthful feature status."""
        raise NotImplementedError

    @abstractmethod
    def checkpoint_state(self) -> dict[str, Any]:
        """Return independently owned current-native state."""
        raise NotImplementedError

    @abstractmethod
    def validate_checkpoint_state(self, state: dict[str, Any]) -> None:
        """Validate the exact current schema before any installation."""
        raise NotImplementedError

    @abstractmethod
    def load_state(self, state: dict[str, Any]) -> None:
        """Install validated current state and invalidate prior prepared owners."""
        raise NotImplementedError

    @abstractmethod
    def prepare_native_state(self, state: dict[str, Any], *, parent_plan: Any) -> PreparedNativeCurriculum:
        """Own all publication data before the native BANK preparation cut."""
        raise NotImplementedError

    @abstractmethod
    def install_native_state(self, *, prepared: PreparedNativeCurriculum, parent_plan: Any, attempt: Any, restored: Any) -> None:
        """Publish once in the actual native restore finalizer."""
        raise NotImplementedError
