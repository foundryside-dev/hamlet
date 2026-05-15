"""Transition phase graph scheduling tests."""

import pytest

from townlet.vfs.transition_graph import DEFAULT_TRANSITION_PHASES, TransitionPhaseGraph


def test_default_transition_phase_graph_matches_vfs_spec_order() -> None:
    """The default scheduler should follow the VFS spec's explicit tick order."""
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
        "apply_modulations",
        "apply_threshold_cascades",
        "apply_social_residue_effects",
        "clamp_and_validate",
        "evaluate_terminal_conditions",
        "compute_rewards",
        "emit_observation_features",
        "emit_telemetry",
    )
    assert TransitionPhaseGraph.default().ordered_phases == DEFAULT_TRANSITION_PHASES


def test_transition_phase_graph_rejects_duplicate_phase_names() -> None:
    """Duplicate phase names make ordering ambiguous and should fail at construction."""
    with pytest.raises(ValueError, match="Duplicate transition phase"):
        TransitionPhaseGraph(("ingest_actions", "ingest_actions"))


def test_transition_phase_graph_rejects_empty_phase_names() -> None:
    """Phase names must be explicit non-empty identifiers."""
    with pytest.raises(ValueError, match="non-empty"):
        TransitionPhaseGraph(("ingest_actions", " "))


def test_transition_phase_graph_exposes_canonical_edges() -> None:
    """The configured order should be representable as a deterministic graph payload."""
    graph = TransitionPhaseGraph(("phase_b", "phase_a", "phase_c"))

    assert graph.edges == (("phase_b", "phase_a"), ("phase_a", "phase_c"))
    assert graph.to_canonical_payload() == {
        "phases": ["phase_b", "phase_a", "phase_c"],
        "edges": [
            {"before": "phase_b", "after": "phase_a"},
            {"before": "phase_a", "after": "phase_c"},
        ],
    }


def test_transition_phase_graph_rejects_unknown_phase_lookup() -> None:
    """Schedulers should fail loudly when a rule references an unconfigured phase."""
    graph = TransitionPhaseGraph(("ingest_actions", "advance_global_time"))

    with pytest.raises(ValueError, match="Unknown transition phase"):
        graph.sort_key("apply_action_effects")
