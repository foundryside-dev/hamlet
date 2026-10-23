"""Configured transition phase graph for VFS transition execution.

The graph is the schedule: ``VectorizedHamletEnv.step()`` executes every phase it
declares, in order, and nothing outside it. Action writes are admitted only at the
phases the env runs with the tick's actions in hand (``action_phases``); the
compiler refuses an action write scheduled anywhere later.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_TRANSITION_PHASES = (
    "ingest_actions",
    "advance_global_time",
    "compute_action_legality_masks",
    "apply_movement_and_wait_costs",
    "resolve_affordance_access_and_occupancy",
    "apply_action_costs",
    "advance_interaction_progress",
    "apply_action_effects",
    "apply_completion_bonuses",
    "apply_passive_depletion",
    "apply_threshold_cascades",
    "apply_social_residue_effects",
    "clamp_and_validate",
    "evaluate_terminal_conditions",
)

DEFAULT_LAST_ACTION_PHASE = "apply_completion_bonuses"


@dataclass(frozen=True)
class TransitionPhaseGraph:
    """Explicit phase order used by transition schedulers.

    ``last_action_phase`` closes the prefix of phases that run with the tick's
    actions; every later phase runs without them, so action writes there refuse.
    """

    ordered_phases: tuple[str, ...]
    last_action_phase: str

    def __post_init__(self) -> None:
        if len(self.ordered_phases) == 0:
            raise ValueError("transition phase graph must contain at least one phase")

        seen: set[str] = set()
        for phase in self.ordered_phases:
            if not phase.strip():
                raise ValueError("transition phase names must be non-empty")
            if phase in seen:
                raise ValueError(f"Duplicate transition phase '{phase}'")
            seen.add(phase)
        if self.last_action_phase not in seen:
            raise ValueError(f"last_action_phase '{self.last_action_phase}' is not a phase of the graph")

    @classmethod
    def default(cls) -> TransitionPhaseGraph:
        """Return the default VFS transition phase graph."""
        return cls(DEFAULT_TRANSITION_PHASES, DEFAULT_LAST_ACTION_PHASE)

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        """Return adjacent phase ordering edges."""
        return tuple((before, after) for before, after in zip(self.ordered_phases, self.ordered_phases[1:]))

    @property
    def action_phases(self) -> tuple[str, ...]:
        """Phases that run with the tick's actions — the only phases admitting action writes."""
        return self.ordered_phases[: self.sort_key(self.last_action_phase) + 1]

    def sort_key(self, phase: str) -> int:
        """Return the configured order index for a phase, failing loudly for unknown phases."""
        index_by_phase = {known_phase: index for index, known_phase in enumerate(self.ordered_phases)}
        try:
            return index_by_phase[phase]
        except KeyError as exc:
            raise ValueError(f"Unknown transition phase '{phase}'") from exc

    def to_canonical_payload(self) -> dict[str, object]:
        """Return the deterministic phase graph payload used by provenance hashing."""
        return {
            "phases": list(self.ordered_phases),
            "edges": [{"before": before, "after": after} for before, after in self.edges],
            "last_action_phase": self.last_action_phase,
        }
