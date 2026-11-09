"""Owned completion metrics, lane clocks, and explicit difficulty modes (T20)."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest
import torch

from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.static import StaticCurriculum
from townlet.training.episode import EpisodeCompletion, LaneOutcome


def curriculum(*, lanes=1, dwell=1000, mode="stage_band", rate=0.01, low=0.0, high=1.0, commitment="completion"):
    manager = AdversarialCurriculum(max_steps_per_episode=500)
    manager.configure_from_training(
        SimpleNamespace(
            commit_mode=commitment,
            difficulty_mode=mode,
            adaptation_rate=rate,
            min_difficulty=low,
            max_difficulty=high,
            min_steps_at_stage=dwell,
        )
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
    assert manager.tracker.steps_at_stage.tolist() == [10.0]
    assert manager.tracker.episodes_at_stage.tolist() == [1]


def test_duplicate_completion_does_not_mutate_metrics_dwell_or_stage():
    manager = curriculum(dwell=10)
    event = outcome()
    commit(manager, event)
    before = deepcopy(manager.get_stage_info())
    transitions = deepcopy(manager.transition_events)
    dwell = manager.tracker.steps_at_stage.clone()
    commit(manager, event, event)
    assert manager.get_stage_info() == before
    assert manager.transition_events == transitions
    assert torch.equal(manager.tracker.steps_at_stage, dwell)
    assert manager.tracker.agent_stages.tolist() == [2]


def test_distinct_lanes_and_reordered_duplicates_are_independent():
    manager = curriculum(lanes=2)
    first = outcome(lane=0, steps=10)
    second = outcome(lane=1, steps=4, reason="authored_terminal")
    commit(manager, second, first)
    commit(manager, first, second)
    assert manager.tracker.steps_at_stage.tolist() == [10.0, 4.0]
    assert manager.tracker.episodes_at_stage.tolist() == [1, 1]
    assert manager.get_stage_info(0)["survival_rate"] == pytest.approx(1.0)
    assert manager.get_stage_info(1)["survival_rate"] == pytest.approx(0.4)
    assert manager.get_stage_info(1)["completion_reason"] == "authored_terminal"
    commit(manager, outcome(lane=1, batch=2, steps=3, reason="budget"))
    assert manager.tracker.steps_at_stage.tolist() == [10.0, 7.0]
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
    assert manager.tracker.agent_stages.tolist() == [1]


@pytest.mark.parametrize("entropy,steps,want", [(0.9, 10, 1), (0.1, 9, 1), (0.1, 10, 2)])
def test_advance_requires_completion_entropy_and_eligible_dwell(entropy, steps, want):
    manager = curriculum(dwell=10)
    commit(manager, outcome(steps=steps, entropy=entropy))
    assert manager.tracker.agent_stages.tolist() == [want]
    assert manager.tracker.steps_at_stage.tolist() == ([0.0] if want == 2 else [float(steps)])
    decisions(manager)
    decisions(manager)
    assert manager.tracker.agent_stages.tolist() == [want]
    assert len(manager.transition_events) == (1 if want == 2 else 0)


def test_retreat_uses_negative_fraction_progress_and_ignores_entropy_gate():
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    assert manager.tracker.agent_stages.tolist() == [2]
    commit(manager, outcome(batch=2, steps=10, horizon=20, entropy=0.99))
    assert manager.tracker.agent_stages.tolist() == [1]
    assert [event["reason"] for event in manager.transition_events] == ["advance", "retreat"]
    assert manager.transition_events[-1]["learning_progress"] == pytest.approx(-0.5)


def test_low_survival_retreats_even_with_positive_learning_progress():
    manager = curriculum(dwell=2)
    manager.tracker.agent_stages[0] = 2
    commit(manager, outcome(steps=2, entropy=0.99))
    assert manager.get_stage_info()["learning_progress"] == pytest.approx(0.2)
    assert manager.tracker.agent_stages.tolist() == [1]
    assert manager.transition_events[-1]["reason"] == "retreat"


def test_checkpoint_resume_preserves_completion_identity_and_completed_metrics():
    manager = curriculum()
    event = outcome()
    commit(manager, event)
    restored = curriculum()
    restored.load_state(deepcopy(manager.checkpoint_state()))
    commit(restored, event)
    assert restored.get_stage_info() == manager.get_stage_info()
    assert restored.tracker.steps_at_stage.tolist() == [10.0]
    assert restored.tracker.episodes_at_stage.tolist() == [1]


def test_decision_reads_do_not_commit_stage_or_dwell():
    manager = curriculum(dwell=10)
    commit(manager, outcome())
    before = deepcopy(manager.get_stage_info())
    dwell = manager.tracker.steps_at_stage.clone()
    for _ in range(3):
        decisions(manager)
    assert manager.get_stage_info() == before
    assert torch.equal(manager.tracker.steps_at_stage, dwell)
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
    manager.tracker.agent_stages.copy_(torch.tensor([1, 2, 3, 4, 5]))
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
    manager = StaticCurriculum(difficulty_level=0.6, depletion_multiplier=0.8)
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
    return deepcopy({
        "state": manager.checkpoint_state(),
        "events": manager.transition_events,
        "info": [manager.get_stage_info(i) for i in range(lanes)],
        "decisions": [vars(item) for item in decisions(manager, lanes)],
        "rng": torch.random.get_rng_state(),
    })


@pytest.mark.parametrize("field,value", [
    ("survival_baseline", 0.0), ("learning_progress", 2.0),
    ("learning_progress", -2.0), ("learning_progress", 1e300),
])
def test_checkpoint_contradiction_or_impossible_progress_refuses_atomically(field, value):
    # Keep this on R1's reachable public API: no missing new constructor/preflight
    # can hide the reviewer's concrete malformed-restore acceptance witness.
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
        assert target.tracker.agent_stages.tolist() == [2]
    assert_same(snapshot(restored), snapshot(manager))


@pytest.mark.parametrize("change", ["lane", "zero", "excess", "reason"])
def test_malformed_later_completion_refuses_whole_batch(change):
    manager = curriculum(lanes=2, dwell=10, mode="rate_limited")
    invalid = outcome(lane=1)
    alteration = {
        "lane": {"agent_idx": 2}, "zero": {"survival_time": 0},
        "excess": {"survival_time": 11}, "reason": {"reason": "undeclared"},
    }[change]
    invalid = replace(invalid, outcome=replace(invalid.outcome, **alteration))
    before = snapshot(manager, 2)
    with pytest.raises(ValueError):
        commit(manager, outcome(), invalid)
    assert_same(snapshot(manager, 2), before)


@pytest.mark.parametrize("change", [
    "reward_total", "reward_extrinsic", "reward_intrinsic", "reward_shaping",
    "policy_entropy", "world_id", "world_episode_seq", "planned_horizon",
    "survival_time", "reason", "final_observation", "final_meters", "observation_dtype", "observation_shape",
])
def test_changed_content_duplicate_refuses_without_any_effect(change):
    manager = curriculum(dwell=10, mode="rate_limited")
    event = outcome()
    commit(manager, event)
    if change in ("survival_time", "reason", "final_observation", "final_meters", "observation_dtype", "observation_shape"):
        value = {
            "survival_time": 9, "reason": "budget",
            "final_observation": torch.tensor([0.5, 0.5]),
            "final_meters": torch.tensor([70.0, 70.0, 60.0, 50.0, 40.0, 30.0]),
            "observation_dtype": torch.tensor([0.25, 0.75], dtype=torch.float64),
            "observation_shape": torch.tensor([[0.25, 0.75]]),
        }[change]
        field = "final_observation" if change.startswith("observation_") else change
        changed = replace(event, outcome=replace(event.outcome, **{field: value}))
    else:
        value = {"world_id": "other-declared-town", "world_episode_seq": 2,
                 "planned_horizon": 20}.get(change, 0.5)
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
    assert manager.tracker.agent_stages.tolist() == [2]
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
    assert manager.tracker.steps_at_stage.tolist() == [20.0]


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
    for event in (outcome(batch=2, steps=10, horizon=20),
                  outcome(batch=3, steps=10), outcome(batch=4, steps=10)):
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


@pytest.mark.parametrize("change", [
    "config", "missing_nested", "unknown_nested", "stage_low", "stage_high",
    "negative_dwell", "negative_episodes", "bad_rate", "duplicate_event",
    "bad_identity", "missing_metrics", "prior_low", "prior_high", "prior_infinite",
    "event_content", "event_fingerprint", "negative_generation",
])
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
            "prior_low": -0.1, "prior_high": 1.1, "prior_infinite": float("inf"),
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
    manager = StaticCurriculum(difficulty_level=0.6, depletion_multiplier=0.8)
    manager.initialize_population(1)
    before = snapshot(manager, 0)
    receipt = prepare(manager, outcome())
    assert_same(snapshot(manager, 0), before)
    accept(manager, receipt)
    once = snapshot(manager, 0)
    accept(manager, receipt)
    assert_same(snapshot(manager, 0), once)
    with pytest.raises(ValueError):
        commit(manager, replace(outcome(), reward_total=11.0))
    assert_same(snapshot(manager, 0), once)
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
