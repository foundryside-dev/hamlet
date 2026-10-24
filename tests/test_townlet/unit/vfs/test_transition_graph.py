"""Transition phase graph scheduling tests."""

import pytest

from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES, TransitionPhaseGraph


def test_default_transition_phase_graph_is_the_executed_schedule() -> None:
    """The default graph declares exactly the fourteen phases step() executes, in order."""
    assert DEFAULT_TRANSITION_PHASES == (
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
    graph = TransitionPhaseGraph.default()
    assert graph.ordered_phases == DEFAULT_TRANSITION_PHASES
    assert graph.last_action_phase == "apply_completion_bonuses"
    assert graph.action_phases == DEFAULT_TRANSITION_PHASES[:9]


def test_transition_phase_graph_rejects_unknown_last_action_phase() -> None:
    with pytest.raises(ValueError, match="last_action_phase 'missing'"):
        TransitionPhaseGraph(("ingest_actions",), "missing")


def test_transition_phase_graph_rejects_duplicate_phase_names() -> None:
    """Duplicate phase names make ordering ambiguous and should fail at construction."""
    with pytest.raises(ValueError, match="Duplicate transition phase"):
        TransitionPhaseGraph(("ingest_actions", "ingest_actions"), "ingest_actions")


def test_transition_phase_graph_rejects_empty_phase_names() -> None:
    """Phase names must be explicit non-empty identifiers."""
    with pytest.raises(ValueError, match="non-empty"):
        TransitionPhaseGraph(("ingest_actions", " "), "ingest_actions")


def test_transition_phase_graph_exposes_canonical_edges() -> None:
    """The configured order should be representable as a deterministic graph payload."""
    graph = TransitionPhaseGraph(("phase_b", "phase_a", "phase_c"), "phase_a")

    assert graph.edges == (("phase_b", "phase_a"), ("phase_a", "phase_c"))
    assert graph.to_canonical_payload() == {
        "phases": ["phase_b", "phase_a", "phase_c"],
        "edges": [
            {"before": "phase_b", "after": "phase_a"},
            {"before": "phase_a", "after": "phase_c"},
        ],
        "last_action_phase": "phase_a",
    }
    assert graph.action_phases == ("phase_b", "phase_a")


def test_transition_phase_graph_rejects_unknown_phase_lookup() -> None:
    """Schedulers should fail loudly when a rule references an unconfigured phase."""
    graph = TransitionPhaseGraph(("ingest_actions", "advance_global_time"), "advance_global_time")

    with pytest.raises(ValueError, match="Unknown transition phase"):
        graph.sort_key("apply_action_effects")
