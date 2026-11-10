"""Owned completion metrics, lane clocks, and explicit difficulty modes (T20)."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace

import pytest
import torch

from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.static import StaticCurriculum
from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome, lane_outcome_fingerprint, lane_outcome_state


def curriculum(*, lanes=1, dwell=1000, mode="stage_band", rate=0.01, low=0.0, high=1.0, commitment="completion"):
    manager = AdversarialCurriculum(
        commit_mode=commitment,
        difficulty_mode=mode,
        adaptation_rate=rate,
        min_difficulty=low,
        max_difficulty=high,
        min_steps_at_stage=dwell,
        survival_advance_threshold=0.7,
        survival_retreat_threshold=0.3,
        entropy_gate=0.5,
        device=torch.device("cpu"),
    )
    manager.initialize_population(lanes)
    return manager


def outcome(*, lane=0, batch=1, steps=10, horizon=10, entropy=0.1, reason="cap", extrinsic=6.0, intrinsic=3.0, shaping=1.0):
    return LaneOutcome(
        outcome=EpisodeCompletion(
            agent_idx=lane,
            reason=reason,
            survival_time=steps,
            final_observation=torch.tensor([0.25, 0.75]),
            final_meters=torch.tensor([80.0, 70.0, 60.0, 50.0, 40.0, 30.0]),
        ),
        batch_episode=batch,
        planned_horizon=horizon,
        reward_total=extrinsic + intrinsic + shaping,
        reward_extrinsic=extrinsic,
        reward_intrinsic=intrinsic,
        reward_shaping=shaping,
        policy_entropy=entropy,
        world_id=f"town-world-{lane}",
        world_episode_seq=batch,
    )


def commit(manager, *events):
    consumer = getattr(manager, "commit_episode_outcomes", None)
    assert callable(consumer), "Curriculum must consume owned LaneOutcome completions"
    consumer(events)


def decisions(manager, lanes=1):
    # Both implementations ignore state; no extra state/fixture source is read.
    return manager.get_batch_decisions(None, [f"agent-{i}" for i in range(lanes)])


def lane_values(manager, key):
    return [manager.get_stage_info(index)[key] for index in range(manager.num_agents)]


def advance_to_stages(manager, stages):
    """Produce heterogeneous stages using real improving completed episodes."""
    for lane, stage in enumerate(stages):
        for batch, steps in enumerate((3000, 3200, 3600, 4000)[: stage - 1], start=1):
            commit(manager, outcome(lane=lane, batch=batch, steps=steps, horizon=4000))


def fixed_curriculum():
    return StaticCurriculum(
        commit_mode="completion",
        difficulty_level=0.6,
        reward_mode="shaped",
        active_meters=["energy", "hygiene", "satiation", "money", "mood", "social"],
        depletion_multiplier=0.8,
    )


def test_full_survival_survives_reset():
    manager = curriculum()
    commit(manager, outcome())
    # A read for the next episode must retain the owned completed snapshot.
    decisions(manager)
    decisions(manager)
    assert manager.get_stage_info()["survival_rate"] == pytest.approx(1.0)
    assert manager.get_stage_info()["completion_reason"] == "cap"


def test_dwell_counts_ten_transitions():
    manager = curriculum()
    commit(manager, outcome())
    assert lane_values(manager, "steps_at_stage") == [10.0]
    assert lane_values(manager, "episodes_at_stage") == [1]


def test_duplicate_completion_does_not_mutate_metrics_dwell_or_stage():
    manager = curriculum(dwell=10)
    event = outcome()
    commit(manager, event)
    before = deepcopy(manager.get_stage_info())
    transitions = deepcopy(manager.transition_events)
    dwell = lane_values(manager, "steps_at_stage")
    commit(manager, event, event)
    assert manager.get_stage_info() == before
    assert manager.transition_events == transitions
    assert lane_values(manager, "steps_at_stage") == dwell
    assert lane_values(manager, "current_stage") == [2]


def test_distinct_lanes_and_reordered_duplicates_are_independent():
    manager = curriculum(lanes=2)
    first = outcome(lane=0, steps=10)
    second = outcome(lane=1, steps=4, reason="authored_terminal")
    commit(manager, second, first)
    commit(manager, first, second)
    assert lane_values(manager, "steps_at_stage") == [10.0, 4.0]
    assert lane_values(manager, "episodes_at_stage") == [1, 1]
    assert manager.get_stage_info(0)["survival_rate"] == pytest.approx(1.0)
    assert manager.get_stage_info(1)["survival_rate"] == pytest.approx(0.4)
    assert manager.get_stage_info(1)["completion_reason"] == "authored_terminal"
    commit(manager, outcome(lane=1, batch=2, steps=3, reason="budget"))
    assert lane_values(manager, "steps_at_stage") == [10.0, 7.0]
    assert manager.get_stage_info(0)["completion_reason"] == "cap"
    assert manager.get_stage_info(1)["completion_reason"] == "budget"


def test_learning_progress_compares_completed_fractions_before_baseline_update():
    manager = curriculum()
    commit(manager, outcome(steps=4, horizon=10, extrinsic=1000.0))
    assert manager.get_stage_info()["learning_progress"] == pytest.approx(0.4)
    assert manager.get_stage_info()["survival_baseline"] == pytest.approx(0.4)
    commit(manager, outcome(batch=2, steps=12, horizon=20, extrinsic=-1000.0))
    info = manager.get_stage_info()
    assert info["survival_rate"] == pytest.approx(0.6)
    assert info["learning_progress"] == pytest.approx(0.2)
    assert info["survival_baseline"] == pytest.approx(0.6)
    assert info["reward_total"] == pytest.approx(-996.0)
    assert info["reward_extrinsic"] == pytest.approx(-1000.0)
    assert info["reward_intrinsic"] == pytest.approx(3.0)
    assert info["reward_shaping"] == pytest.approx(1.0)
    assert info["policy_entropy"] == pytest.approx(0.1)


def test_equal_fraction_is_not_positive_learning_despite_more_steps_and_reward():
    manager = curriculum(dwell=10)
    commit(manager, outcome(steps=8, horizon=10, entropy=0.9))
    commit(manager, outcome(batch=2, steps=16, horizon=20, extrinsic=10000.0))
    assert manager.get_stage_info()["learning_progress"] == pytest.approx(0.0)
    assert lane_values(manager, "current_stage") == [1]


@pytest.mark.parametrize("entropy,steps,want", [(0.9, 10, 1), (0.1, 9, 1), (0.1, 10, 2)])
def test_advance_requires_completion_entropy_and_eligible_dwell(entropy, steps, want):
    manager = curriculum(dwell=10)
    commit(manager, outcome(steps=steps, entropy=entropy))
    assert lane_values(manager, "current_stage") == [want]
    assert lane_values(manager, "steps_at_stage") == ([0.0] if want == 2 else [float(steps)])
    decisions(manager)
    decisions(manager)
    assert lane_values(manager, "current_stage") == [want]
    assert len(manager.transition_events) == (1 if want == 2 else 0)


def test_retreat_uses_negative_fraction_progress_and_ignores_entropy_gate():
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    assert lane_values(manager, "current_stage") == [2]
    commit(manager, outcome(batch=2, steps=10, horizon=20, entropy=0.99))
    assert lane_values(manager, "current_stage") == [1]
    assert [event["reason"] for event in manager.transition_events] == ["advance", "retreat"]
    assert manager.transition_events[-1]["learning_progress"] == pytest.approx(-0.5)


def test_low_survival_retreats_even_with_positive_learning_progress():
    manager = curriculum(dwell=2)
    commit(manager, outcome(steps=8), outcome(batch=2))
    commit(manager, outcome(batch=3, steps=2, horizon=40, entropy=0.99))
    assert lane_values(manager, "current_stage") == [2]
    commit(manager, outcome(batch=4, steps=5, horizon=20, entropy=0.99))
    assert manager.get_stage_info()["learning_progress"] == pytest.approx(0.2)
    assert lane_values(manager, "current_stage") == [1]
    assert manager.transition_events[-1]["reason"] == "retreat"


def test_checkpoint_resume_preserves_completion_identity_and_completed_metrics():
    manager = curriculum()
    event = outcome()
    commit(manager, event)
    restored = curriculum()
    restored.load_state(deepcopy(manager.checkpoint_state()))
    commit(restored, event)
    assert restored.get_stage_info() == manager.get_stage_info()
    assert lane_values(restored, "steps_at_stage") == [10.0]
    assert lane_values(restored, "episodes_at_stage") == [1]


def test_decision_reads_do_not_commit_stage_or_dwell():
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    before = deepcopy(manager.get_stage_info())
    dwell = lane_values(manager, "steps_at_stage")
    for _ in range(3):
        decisions(manager)
    assert manager.get_stage_info() == before
    assert lane_values(manager, "steps_at_stage") == dwell
    assert len(manager.transition_events) == 1


@pytest.mark.parametrize("mode", ["stage_band", "rate_limited"])
def test_singleton_band(mode):
    manager = curriculum(mode=mode, low=0.6, high=0.6)
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.6)
    commit(manager, outcome())
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.6)


@pytest.mark.parametrize("rate,want", [(0.01, 0.1), (0.1, 0.25)])
def test_rate_has_declared_effect(rate, want):
    manager = curriculum(dwell=10, mode="rate_limited", rate=rate)
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.0)
    commit(manager, outcome())
    # Stage 2 target is .25; ten transitions permit .1 or 1.0 movement.
    assert decisions(manager)[0].difficulty_level == pytest.approx(want)
    assert manager.get_stage_info()["adaptation_rate_active"] is True
    assert manager.get_stage_info()["adaptation_rate_units"] == "difficulty_per_eligible_transition"


def test_rate_limited_moves_back_toward_retreat_target_and_clamps_to_band():
    manager = curriculum(dwell=10, mode="rate_limited", rate=0.01, low=0.2, high=0.6)
    commit(manager, outcome())
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.3)
    commit(manager, outcome(batch=2, steps=10, horizon=20))
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.2)


@pytest.mark.parametrize("rate", [0.01, 0.1])
def test_stage_band_preserves_mapping_and_truthfully_reports_inactive_rate(rate):
    manager = curriculum(lanes=5, rate=rate, low=0.2, high=0.6)
    advance_to_stages(manager, [1, 2, 3, 4, 5])
    result = decisions(manager, 5)
    assert [d.difficulty_level for d in result] == pytest.approx([0.2, 0.3, 0.4, 0.5, 0.6])
    assert [d.depletion_multiplier for d in result] == pytest.approx([0.2, 0.5, 0.8, 1.0, 1.0])
    assert [d.reward_mode for d in result] == ["shaped", "shaped", "shaped", "shaped", "sparse"]
    assert result[0].active_meters == ["energy", "hygiene"]
    info = manager.get_stage_info()
    assert info["commit_mode"] == "completion"
    assert info["difficulty_mode"] == "stage_band"
    assert info["adaptation_rate"] == pytest.approx(rate)
    assert info["adaptation_rate_active"] is False


def test_obsolete_commit_mode_is_refused():
    with pytest.raises(ValueError):
        curriculum(commitment="legacy_step")


def test_static_curriculum_accepts_completion_without_changing_decisions():
    manager = fixed_curriculum()
    manager.initialize_population(1)
    before = decisions(manager)[0]
    event = outcome()
    commit(manager, event, event)
    after = decisions(manager)[0]
    assert after.difficulty_level == before.difficulty_level == 0.6
    assert after.depletion_multiplier == before.depletion_multiplier == 0.8
    assert manager.transition_events == []


def assert_same(actual, expected):
    """Compare owned complete snapshots, including tensor dtype and contents."""
    assert type(actual) is type(expected)
    if isinstance(actual, torch.Tensor):
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        assert torch.equal(actual, expected)
    elif isinstance(actual, dict):
        assert actual.keys() == expected.keys()
        for key in actual:
            assert_same(actual[key], expected[key])
    elif isinstance(actual, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            assert_same(left, right)
    else:
        assert actual == expected


def snapshot(manager, lanes=1):
    return deepcopy(
        {
            "state": manager.checkpoint_state(),
            "events": manager.transition_events,
            "info": [manager.get_stage_info(i) for i in range(lanes)],
            "decisions": [vars(item) for item in decisions(manager, lanes)],
            "rng": torch.random.get_rng_state(),
        }
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("survival_baseline", 0.0),
        ("learning_progress", 2.0),
        ("learning_progress", -2.0),
        ("learning_progress", 1e300),
    ],
)
def test_checkpoint_contradiction_or_impossible_progress_refuses_atomically(field, value):
    # Root captured this exact R1 corruption cause before migrating initialization.
    # Redundant fraction/progress fields are forbidden in the canonical metric row.
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    damaged = deepcopy(manager.checkpoint_state())
    damaged["completion"]["metrics"][0][field] = value
    before = snapshot(manager)
    with pytest.raises(ValueError):
        manager.load_state(damaged)
    assert_same(snapshot(manager), before)


def test_valid_point_eight_native_restore_preserves_equal_fraction_future():
    manager = curriculum(dwell=8)
    commit(manager, outcome(steps=8))
    manager.transition_events.clear()  # Model the boundary telemetry drain before save.
    restored = curriculum(dwell=8)
    restored.load_state(deepcopy(manager.checkpoint_state()))
    assert restored.get_stage_info()["survival_rate"] == pytest.approx(0.8)
    assert restored.get_stage_info()["survival_baseline"] == pytest.approx(0.8)
    for target in (manager, restored):
        commit(target, outcome(batch=2, steps=16, horizon=20))
        assert target.get_stage_info()["learning_progress"] == pytest.approx(0.0)
        assert lane_values(target, "current_stage") == [2]
    assert_same(snapshot(restored), snapshot(manager))


@pytest.mark.parametrize("change", ["lane", "zero", "excess", "reason"])
def test_malformed_later_completion_refuses_whole_batch(change):
    manager = curriculum(lanes=2, dwell=10, mode="rate_limited")
    invalid = outcome(lane=1)
    alteration = {
        "lane": {"agent_idx": 2},
        "zero": {"survival_time": 0},
        "excess": {"survival_time": 11},
        "reason": {"reason": "undeclared"},
    }[change]
    invalid = replace(invalid, outcome=replace(invalid.outcome, **alteration))
    before = snapshot(manager, 2)
    with pytest.raises(ValueError):
        commit(manager, outcome(), invalid)
    assert_same(snapshot(manager, 2), before)


@pytest.mark.parametrize(
    "change",
    [
        "reward_total",
        "reward_extrinsic",
        "reward_intrinsic",
        "reward_shaping",
        "policy_entropy",
        "world_id",
        "world_episode_seq",
        "planned_horizon",
        "survival_time",
        "reason",
        "final_observation",
        "final_meters",
        "observation_dtype",
        "observation_shape",
    ],
)
def test_changed_content_duplicate_refuses_without_any_effect(change):
    manager = curriculum(dwell=10, mode="rate_limited")
    event = outcome()
    commit(manager, event)
    if change in ("survival_time", "reason", "final_observation", "final_meters", "observation_dtype", "observation_shape"):
        value = {
            "survival_time": 9,
            "reason": "budget",
            "final_observation": torch.tensor([0.5, 0.5]),
            "final_meters": torch.tensor([70.0, 70.0, 60.0, 50.0, 40.0, 30.0]),
            "observation_dtype": torch.tensor([0.25, 0.75], dtype=torch.float64),
            "observation_shape": torch.tensor([[0.25, 0.75]]),
        }[change]
        field = "final_observation" if change.startswith("observation_") else change
        changed = replace(event, outcome=replace(event.outcome, **{field: value}))
    else:
        value = {"world_id": "other-declared-town", "world_episode_seq": 2, "planned_horizon": 20}.get(change, 0.5)
        changed = replace(event, **{change: value})
    before = snapshot(manager)
    with pytest.raises(ValueError):
        commit(manager, changed)
    assert_same(snapshot(manager), before)


def test_equal_content_duplicate_uses_owned_content_not_object_identity():
    manager = curriculum(dwell=10, mode="rate_limited")
    commit(manager, outcome())
    before = snapshot(manager)
    commit(manager, outcome(), deepcopy(outcome()))
    assert_same(snapshot(manager), before)


def prepare(manager, *events):
    method = getattr(manager, "prepare_episode_outcomes", None)
    assert callable(method), "Curriculum needs pure whole-batch preparation"
    return method(events)


def accept(manager, receipt):
    method = getattr(manager, "commit_prepared_episode_outcomes", None)
    assert callable(method), "Curriculum needs pinned prepared-batch commit"
    return method(receipt)


def test_prepare_is_pure_and_prepared_retry_commits_once():
    manager = curriculum(dwell=10, mode="rate_limited")
    before = snapshot(manager)
    receipt = prepare(manager, outcome())
    assert_same(snapshot(manager), before)
    with pytest.raises((AttributeError, TypeError)):
        receipt.generation = 99
    accept(manager, receipt)
    once = snapshot(manager)
    accept(manager, receipt)
    assert_same(snapshot(manager), once)
    assert lane_values(manager, "current_stage") == [2]
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.1)


def test_prepare_rejects_later_invalid_lane_without_mutation():
    manager = curriculum(lanes=2, mode="rate_limited")
    before = snapshot(manager, 2)
    method = getattr(manager, "prepare_episode_outcomes", None)
    assert callable(method), "Pure preparation must exist before sink mutation"
    with pytest.raises(ValueError):
        method((outcome(), outcome(lane=2)))
    assert_same(snapshot(manager, 2), before)


def test_prepared_receipt_owns_content_and_refuses_stale_generation():
    manager = curriculum(mode="rate_limited")
    original = outcome()
    first = prepare(manager, original)
    second = prepare(manager, outcome(batch=2))
    original.outcome.final_observation.fill_(999)
    accept(manager, first)
    # Accepted content must be the immutable prepared snapshot, not this mutation.
    commit(manager, outcome())
    before = snapshot(manager)
    with pytest.raises(ValueError):
        accept(manager, second)
    assert_same(snapshot(manager), before)
    commit(manager, outcome(batch=2))
    assert lane_values(manager, "steps_at_stage") == [20.0]


def test_prepared_receipt_from_other_owner_refuses_atomically():
    manager = curriculum()
    other = curriculum()
    foreign = prepare(other, outcome())
    before = snapshot(manager)
    with pytest.raises(ValueError):
        accept(manager, foreign)
    assert_same(snapshot(manager), before)


def test_changed_duplicate_inside_single_preflight_refuses_atomically():
    manager = curriculum()
    event = outcome()
    before = snapshot(manager)
    method = getattr(manager, "prepare_episode_outcomes", None)
    assert callable(method), "Preflight must compare duplicate content within a batch"
    with pytest.raises(ValueError):
        method((event, replace(event, reward_total=11.0)))
    assert_same(snapshot(manager), before)


def test_current_schema_has_one_canonical_completed_state_and_no_tracker_protocol():
    manager = curriculum()
    commit(manager, outcome())
    state = manager.checkpoint_state()
    assert set(state) == {"version", "strategy", "completion"}
    assert state["version"] == 2
    assert state["strategy"] == "adversarial"
    assert set(state["completion"]) == {"config", "generation", "lanes", "events", "metrics"}
    assert not hasattr(manager, "tracker"), "Remove obsolete reward-as-step tracker protocol"
    assert not hasattr(manager, "get_batch_decisions_with_qvalues")
    assert not hasattr(manager, "configure_from_training")
    assert manager.get_stage_info()["survival_rate"] == pytest.approx(1.0)


@pytest.mark.parametrize("change", ["version", "missing", "unknown", "strategy", "obsolete"])
def test_current_checkpoint_schema_refuses_obsolete_or_malformed_state(change):
    manager = curriculum()
    commit(manager, outcome())
    damaged = deepcopy(manager.checkpoint_state())
    if change == "version":
        damaged["version"] = -1
    elif change == "missing":
        damaged.pop("completion")
    elif change == "unknown":
        damaged["unknown"] = 1
    elif change == "strategy":
        damaged["strategy"] = "undeclared"
    else:
        damaged = {"version": 1, "completion": damaged["completion"]}
    before = snapshot(manager)
    with pytest.raises(ValueError):
        manager.load_state(damaged)
    assert_same(snapshot(manager), before)


def test_rate_limited_resume_matches_uninterrupted_future_and_duplicate_retry():
    manager = curriculum(dwell=10, mode="rate_limited", rate=0.01)
    commit(manager, outcome())
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.1)
    manager.transition_events.clear()  # Compare newly emitted future telemetry only.
    restored = curriculum(dwell=10, mode="rate_limited", rate=0.01)
    restored.load_state(deepcopy(manager.checkpoint_state()))
    commit(restored, outcome())
    assert decisions(restored)[0].difficulty_level == pytest.approx(0.1)
    for event in (outcome(batch=2, steps=10, horizon=20), outcome(batch=3, steps=10), outcome(batch=4, steps=10)):
        commit(manager, event)
        commit(restored, deepcopy(event))
        assert_same(snapshot(restored), snapshot(manager))
    assert decisions(restored)[0].difficulty_level == pytest.approx(0.2)


def test_checkpoint_snapshot_and_loaded_input_do_not_alias_live_state():
    manager = curriculum()
    commit(manager, outcome())
    state = deepcopy(manager.checkpoint_state())
    restored = curriculum()
    restored.load_state(state)
    expected = snapshot(restored)
    state["completion"]["metrics"][0].clear()
    assert_same(snapshot(restored), expected)
    saved = manager.checkpoint_state()
    before = snapshot(manager)
    saved["completion"]["metrics"][0].clear()
    assert_same(snapshot(manager), before)


def test_completion_transition_uses_canonical_identity_without_legacy_alias():
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    transition = manager.transition_events[0]
    assert transition["agent_idx"] == 0
    assert transition["world_id"] == "town-world-0"
    assert transition["world_episode_seq"] == 1
    assert transition["batch_episode"] == 1
    assert transition["from_stage"] == 1
    assert transition["to_stage"] == 2
    assert "agent_id" not in transition


def current_state(manager):
    state = deepcopy(manager.checkpoint_state())
    assert set(state) == {"version", "strategy", "completion"}, "Current native state is required"
    assert state["version"] == 2
    return state


@pytest.mark.parametrize(
    "change",
    [
        "config",
        "missing_nested",
        "unknown_nested",
        "stage_low",
        "stage_high",
        "negative_dwell",
        "negative_episodes",
        "bad_rate",
        "duplicate_event",
        "bad_identity",
        "missing_metrics",
        "prior_low",
        "prior_high",
        "prior_infinite",
        "event_content",
        "event_fingerprint",
        "negative_generation",
    ],
)
def test_current_nested_corruption_refuses_before_installation(change):
    manager = curriculum(dwell=10, mode="rate_limited")
    commit(manager, outcome())
    damaged = current_state(manager)
    body = damaged["completion"]
    if change == "config":
        body["config"]["adaptation_rate"] = 0.2
    elif change == "missing_nested":
        body.pop("events")
    elif change == "unknown_nested":
        body["unknown"] = []
    elif change in ("stage_low", "stage_high"):
        body["lanes"][0]["stage"] = 0 if change == "stage_low" else 6
    elif change == "negative_dwell":
        body["lanes"][0]["dwell"] = -1
    elif change == "negative_episodes":
        body["lanes"][0]["episodes_at_stage"] = -1
    elif change == "bad_rate":
        body["lanes"][0]["difficulty"] = float("nan")
    elif change == "duplicate_event":
        body["events"].append(deepcopy(body["events"][0]))
    elif change == "bad_identity":
        body["events"][0]["identity"] = (1, 9)
    elif change == "missing_metrics":
        body["metrics"][0] = None
    elif change in ("prior_low", "prior_high", "prior_infinite"):
        body["metrics"][0]["previous_fraction"] = {
            "prior_low": -0.1,
            "prior_high": 1.1,
            "prior_infinite": float("inf"),
        }[change]
    elif change == "event_content":
        body["metrics"][0]["event"]["reward_total"] = 123.0
    elif change == "event_fingerprint":
        body["events"][0]["fingerprint"] = "0" * 64
    else:
        body["generation"] = -1
    before = snapshot(manager)
    with pytest.raises(ValueError):
        manager.load_state(damaged)
    assert_same(snapshot(manager), before)


def test_current_valid_restore_installs_one_authoritative_fraction_and_progress():
    manager = curriculum()
    commit(manager, outcome(steps=8))
    state = current_state(manager)
    assert set(state["completion"]["metrics"][0]) == {"event", "previous_fraction"}
    restored = curriculum()
    restored.load_state(state)
    assert restored.get_stage_info()["survival_rate"] == pytest.approx(0.8)
    assert restored.get_stage_info()["learning_progress"] == pytest.approx(0.8)
    commit(restored, outcome(batch=2, steps=8))
    assert restored.get_stage_info()["survival_rate"] == pytest.approx(0.8)
    assert restored.get_stage_info()["learning_progress"] == pytest.approx(0.0)


def test_static_preparation_is_pure_and_changed_duplicate_is_still_refused():
    manager = fixed_curriculum()
    manager.initialize_population(1)
    before = snapshot(manager)
    receipt = prepare(manager, outcome())
    assert_same(snapshot(manager), before)
    accept(manager, receipt)
    once = snapshot(manager)
    accept(manager, receipt)
    assert_same(snapshot(manager), once)
    with pytest.raises(ValueError):
        commit(manager, replace(outcome(), reward_total=11.0))
    assert_same(snapshot(manager), once)
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.6)


def test_current_event_tensor_snapshots_are_owned_on_save_and_load():
    manager = curriculum()
    commit(manager, outcome())
    state = current_state(manager)
    restored = curriculum()
    restored.load_state(state)
    expected = snapshot(restored)
    state["completion"]["metrics"][0]["event"]["outcome"]["final_observation"].zero_()
    assert_same(snapshot(restored), expected)
    saved = manager.checkpoint_state()
    before = snapshot(manager)
    saved["completion"]["metrics"][0]["event"]["outcome"]["final_meters"].zero_()
    assert_same(snapshot(manager), before)


@pytest.mark.parametrize(
    "dtype",
    [
        torch.bool,
        torch.uint8,
        torch.int8,
        torch.int16,
        torch.int32,
        torch.int64,
        torch.float16,
        torch.bfloat16,
        torch.float32,
        torch.float64,
        torch.complex64,
        torch.complex128,
    ],
)
@pytest.mark.parametrize("shape", [(0,), (2, 0), (0, 3), (2,)])
def test_shared_fingerprint_preserves_empty_shapes_dtype_contents_and_ownership(dtype, shape):
    event = replace(
        outcome(),
        outcome=replace(outcome().outcome, final_observation=torch.zeros(shape, dtype=dtype), final_meters=torch.zeros(shape, dtype=dtype)),
    )
    expected = lane_outcome_state(event)
    frozen = freeze_lane_outcome(event)
    assert frozen.fingerprint == lane_outcome_fingerprint(event)
    event.outcome.final_observation.fill_(1)
    assert_same(lane_outcome_state(frozen.to_outcome()), expected)
    if event.outcome.final_observation.numel():
        assert frozen.fingerprint != lane_outcome_fingerprint(event)


@pytest.mark.parametrize("change", ["world", "sequence", "batch"])
def test_preflight_refuses_new_event_with_wrong_established_lane_cursor(change):
    manager = curriculum()
    commit(manager, outcome())
    event = outcome(batch=2)
    event = replace(
        event,
        **{
            "world": {"world_id": "other-declared-town"},
            "sequence": {"world_episode_seq": 1},
            "batch": {"batch_episode": 0},
        }[change],
    )
    before = snapshot(manager)
    with pytest.raises(ValueError):
        prepare(manager, event)
    assert_same(snapshot(manager), before)


def test_current_load_invalidates_prepared_owner_even_at_equal_generation():
    manager = curriculum()
    commit(manager, outcome())
    pending = prepare(manager, outcome(batch=2))
    manager.load_state(manager.checkpoint_state())
    before = snapshot(manager)
    with pytest.raises(ValueError):
        accept(manager, pending)
    assert_same(snapshot(manager), before)


def logical_fixture(kind):
    manager = fixed_curriculum() if "static" in kind else curriculum(dwell=10, mode="rate_limited") if kind == "rate" else curriculum()
    if "static" in kind:
        manager.initialize_population(1)
    events = (
        (outcome(steps=4), outcome(batch=2, steps=8))
        if kind.startswith("multi")
        else (outcome() if "static" in kind or kind == "rate" else outcome(steps=4),)
    )
    commit(manager, *events)
    return manager, outcome(batch=len(events) + 1, steps=8)


@pytest.mark.parametrize(
    "kind",
    [
        "dwell",
        "stage",
        "rate",
        "static_count",
        "static_zero",
        "multi_latest_dwell",
        "multi_zero_count",
        "multi_stage",
        "multi_static_count",
    ],
)
def test_logically_impossible_native_effects_refuse_without_invalidating_prepared_owner(kind):
    manager, future = logical_fixture(kind)
    control, _ = logical_fixture(kind)
    pending = prepare(manager, future)
    damaged = current_state(manager)
    lane = damaged["completion"]["lanes"][0]
    if kind == "dwell":
        lane["dwell"] = 1000
    elif kind == "stage":
        lane.update(stage=5, difficulty=1.0)
    elif kind == "rate":
        lane["difficulty"] = 0.9
    elif kind == "static_count" or kind == "multi_static_count":
        lane["episodes_at_stage"] = 0 if kind == "static_count" else 1
    elif kind == "static_zero":
        lane.update(episodes_at_stage=0, dwell=0)
    elif kind == "multi_latest_dwell":
        lane["dwell"] = 7
    elif kind == "multi_zero_count":
        lane["episodes_at_stage"] = 0
    else:
        lane.update(stage=4, difficulty=0.75)
    before = snapshot(manager)
    with pytest.raises(ValueError):
        manager.load_state(damaged)
    assert_same(snapshot(manager), before)
    accept(manager, pending)
    commit(control, future)
    assert_same(snapshot(manager), snapshot(control))


@pytest.mark.parametrize(
    "kind,stage,dwell,count,difficulty",
    [
        ("dwell", 1, 4, 1, 0.0),
        ("rate", 2, 0, 0, 0.1),
        ("static_count", 0, 10, 1, 0.6),
    ],
)
def test_genuine_first_event_native_effects_restore_exactly(kind, stage, dwell, count, difficulty):
    manager, _ = logical_fixture(kind)
    manager.transition_events.clear()
    restored, _ = logical_fixture(kind)
    restored.load_state(manager.checkpoint_state())
    assert_same(snapshot(restored), snapshot(manager))
    assert lane_values(restored, "current_stage") == [stage]
    assert lane_values(restored, "steps_at_stage") == [dwell]
    assert lane_values(restored, "episodes_at_stage") == [count]
    assert decisions(restored)[0].difficulty_level == pytest.approx(difficulty)


def test_static_multi_event_resume_keeps_exact_clocks_and_old_equal_retry():
    manager, _ = logical_fixture("multi_static_count")
    restored = fixed_curriculum()
    restored.initialize_population(1)
    restored.load_state(manager.checkpoint_state())
    commit(restored, outcome(steps=4))
    assert lane_values(restored, "steps_at_stage") == [12]
    assert lane_values(restored, "episodes_at_stage") == [2]
    for target in (manager, restored):
        commit(target, outcome(batch=3, steps=3, reason="budget"))
        assert lane_values(target, "steps_at_stage") == [15]
        assert lane_values(target, "episodes_at_stage") == [3]
        assert decisions(target)[0].difficulty_level == pytest.approx(0.6)
    assert_same(snapshot(restored), snapshot(manager))


def test_future_generation_equal_receipt_refuses_but_older_equal_retry_survives():
    manager = curriculum()
    original = prepare(manager, outcome())
    accept(manager, original)
    commit(manager, outcome(batch=2))
    before = snapshot(manager)
    with pytest.raises(ValueError):
        accept(manager, replace(original, generation=99))
    assert_same(snapshot(manager), before)
    accept(manager, original)
    assert_same(snapshot(manager), before)


@pytest.mark.parametrize(
    "reading",
    [
        torch.tensor(3.25, dtype=torch.float64),
        torch.tensor(1 + 2j, dtype=torch.complex64),
        torch.tensor([[1 + 2j, 3 - 4j], [5 + 6j, 7 - 8j]], dtype=torch.complex128).t(),
        torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]).t(),
    ],
)
def test_codec_preserves_nonzero_complex_scalar_and_noncontiguous_logical_readings(reading):
    event = replace(outcome(), outcome=replace(outcome().outcome, final_observation=reading, final_meters=reading))
    expected = lane_outcome_state(event)
    frozen = freeze_lane_outcome(event)
    assert_same(lane_outcome_state(frozen.to_outcome()), expected)
    contiguous = replace(event, outcome=replace(event.outcome, final_observation=reading.contiguous(), final_meters=reading.contiguous()))
    assert lane_outcome_fingerprint(contiguous) == frozen.fingerprint
    event.outcome.final_observation.zero_()
    assert_same(lane_outcome_state(frozen.to_outcome()), expected)


@pytest.mark.parametrize(
    "change",
    ["fingerprint", "dtype", "negative_shape", "boolean_shape", "wrong_shape", "bad_hex", "byte_length", "unknown_field", "nonfinite"],
)
def test_codec_malformed_metadata_bytes_and_content_refuse(change):
    frozen = freeze_lane_outcome(outcome())
    data = json.loads(frozen.payload)
    reading = data["outcome"]["final_observation"]
    if change == "fingerprint":
        damaged = replace(frozen, fingerprint="0" * 64)
    else:
        if change == "dtype":
            reading["dtype"] = "undeclared"
        elif change in ("negative_shape", "boolean_shape", "wrong_shape"):
            reading["shape"] = {"negative_shape": [-1], "boolean_shape": [True], "wrong_shape": [3]}[change]
        elif change in ("bad_hex", "byte_length"):
            reading["data"] = "zz" if change == "bad_hex" else "00"
        elif change == "unknown_field":
            data["unknown"] = 1
        else:
            reading["data"] = torch.tensor([float("inf"), 0.75]).numpy().tobytes().hex()
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        damaged = replace(frozen, payload=payload, fingerprint=hashlib.sha256(payload).hexdigest())
    with pytest.raises(ValueError):
        damaged.to_outcome()


def rate_history(kind):
    rate = 1.0 if kind in ("saturated", "advance") else 0.0 if kind == "zero" else 0.01
    low, high = (0.2, 0.8) if kind == "zero" else (0.6, 0.6) if kind == "singleton" else (0.0, 1.0)
    manager = curriculum(dwell=8 if kind == "advance" else 10, mode="rate_limited", rate=rate, low=low, high=high)
    steps_horizons = [(10, 10), (10, 10)]
    if kind == "interior":
        steps_horizons = [(10, 10), (2, 2)]
    elif kind == "advance":
        steps_horizons = [(8, 10), (10, 10)]
    elif kind == "lower":
        steps_horizons = [(10, 10), (10, 20), (10, 10)]
    elif kind == "upper":
        steps_horizons = [(30, 40), (32, 40), (36, 40), (40, 40), (10, 20)]
    for batch, (steps, horizon) in enumerate(steps_horizons, start=1):
        commit(manager, outcome(batch=batch, steps=steps, horizon=horizon))
    return manager, outcome(batch=len(steps_horizons) + 1)


@pytest.mark.parametrize(
    "kind,damaged_difficulty",
    [
        ("saturated", 0.0),
        ("saturated", 0.9),
        ("interior", 0.01),
        ("interior", 0.99),
        ("advance", 0.25),
        ("advance", 0.9),
        ("zero", 0.3),
        ("zero", 0.79),
    ],
)
def test_latest_rate_interval_or_zero_rate_corruption_refuses_with_prepared_owner_intact(kind, damaged_difficulty):
    manager, future = rate_history(kind)
    control, _ = rate_history(kind)
    pending = prepare(manager, future)
    damaged = current_state(manager)
    damaged["completion"]["lanes"][0]["difficulty"] = damaged_difficulty
    before = snapshot(manager)
    with pytest.raises(ValueError):
        manager.load_state(damaged)
    assert_same(snapshot(manager), before)
    accept(manager, pending)
    commit(control, future)
    assert_same(snapshot(manager), snapshot(control))


@pytest.mark.parametrize(
    "kind,stage,difficulty",
    [
        ("saturated", 2, 0.25),
        ("interior", 2, 0.12),
        ("advance", 3, 0.5),
        ("lower", 2, 0.1),
        ("upper", 4, 0.9),
        ("zero", 2, 0.2),
        ("singleton", 2, 0.6),
    ],
)
def test_genuine_latest_rate_endpoint_interior_and_new_stage_native_future(kind, stage, difficulty):
    manager, future = rate_history(kind)
    manager.transition_events.clear()
    restored, _ = rate_history(kind)
    restored.load_state(manager.checkpoint_state())
    assert lane_values(restored, "current_stage") == [stage]
    assert decisions(restored)[0].difficulty_level == pytest.approx(difficulty)
    assert_same(snapshot(restored), snapshot(manager))
    commit(manager, future)
    commit(restored, future)
    assert_same(snapshot(restored), snapshot(manager))


def test_genuine_seven_event_latest_rate_cancellation_native_roundtrip_and_future():
    manager = curriculum(dwell=1, mode="rate_limited", rate=0.01, low=0.0, high=0.4)
    advance_to_stages(manager, [5])
    for event in (outcome(batch=5, steps=1, horizon=2), outcome(batch=6, steps=1, horizon=4), outcome(batch=7, steps=40, horizon=400)):
        commit(manager, event)
    assert lane_values(manager, "current_stage") == [2]
    assert decisions(manager)[0].difficulty_level == pytest.approx(0.1)
    manager.transition_events.clear()
    restored = curriculum(dwell=1, mode="rate_limited", rate=0.01, low=0.0, high=0.4)
    restored.load_state(manager.checkpoint_state())
    assert_same(snapshot(restored), snapshot(manager))
    for target in (manager, restored):
        commit(target, outcome(batch=8))
        assert lane_values(target, "current_stage") == [3]
        assert decisions(target)[0].difficulty_level == pytest.approx(0.2)
    assert_same(snapshot(restored), snapshot(manager))
