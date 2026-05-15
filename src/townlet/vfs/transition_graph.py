"""Configured transition phase graph for VFS transition execution."""

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
    "apply_modulations",
    "apply_threshold_cascades",
    "apply_social_residue_effects",
    "clamp_and_validate",
    "evaluate_terminal_conditions",
    "compute_rewards",
    "emit_observation_features",
    "emit_telemetry",
)


@dataclass(frozen=True)
class TransitionPhaseGraph:
    """Explicit phase order used by transition schedulers."""

    ordered_phases: tuple[str, ...]

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

    @classmethod
    def default(cls) -> TransitionPhaseGraph:
        """Return the default VFS v1.1 transition phase graph."""
        return cls(DEFAULT_TRANSITION_PHASES)

    @property
    def edges(self) -> tuple[tuple[str, str], ...]:
        """Return adjacent phase ordering edges."""
        return tuple((before, after) for before, after in zip(self.ordered_phases, self.ordered_phases[1:]))

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
        }
