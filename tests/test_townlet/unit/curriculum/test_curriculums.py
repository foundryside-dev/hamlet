"""Current curriculum consumer contracts, using owned completed-lane outcomes.

Historical test identities remain to document the replacement of tracker/Q-value
ownership by the completion protocol. Reward windows are supplied by the episode
owner; curriculum retains them and derives progress only from survival fractions.
"""

from copy import deepcopy
from dataclasses import replace

import pytest
import torch

from townlet.curriculum.adversarial import AdversarialCurriculum
from townlet.curriculum.static import StaticCurriculum
from townlet.training.episode import EpisodeCompletion, LaneOutcome, lane_outcome_state


@pytest.fixture
def adversarial_policy(cpu_device):
    return {
        "commit_mode": "completion",
        "difficulty_mode": "stage_band",
        "adaptation_rate": 0.1,
        "min_difficulty": 0.0,
        "max_difficulty": 1.0,
        "survival_advance_threshold": 0.7,
        "survival_retreat_threshold": 0.3,
        "entropy_gate": 0.5,
        "min_steps_at_stage": 100,
        "device": cpu_device,
    }


@pytest.fixture
def static_policy():
    return {
        "commit_mode": "completion",
        "difficulty_level": 0.7,
        "reward_mode": "sparse",
        "active_meters": ["energy", "hygiene"],
        "depletion_multiplier": 2.0,
    }


def adaptive(policy, population):
    curriculum = AdversarialCurriculum(**policy)
    curriculum.initialize_population(population)
    return curriculum


def fixed(policy, population):
    curriculum = StaticCurriculum(**policy)
    curriculum.initialize_population(population)
    return curriculum


def completion(lane, batch, steps, horizon, entropy, reward):
    """Declare a genuine consumer event; world labels are test identities only."""
    return LaneOutcome(
        outcome=EpisodeCompletion(
            agent_idx=lane,
            reason="cap",
            survival_time=steps,
            final_observation=torch.tensor([float(lane), float(batch)], dtype=torch.float64),
            final_meters=torch.tensor([float(steps), float(horizon)], dtype=torch.float32),
        ),
        batch_episode=batch,
        planned_horizon=horizon,
        reward_total=reward,
        reward_extrinsic=reward - 3.0,
        reward_intrinsic=1.0,
        reward_shaping=2.0,
        policy_entropy=entropy,
        world_id=f"world-{lane}",
        world_episode_seq=batch,
    )


def assert_owned_equal(actual, expected):
    """Compare complete native snapshots, including genuine tensor readings."""
    assert type(actual) is type(expected)
    if isinstance(actual, torch.Tensor):
        assert actual.dtype == expected.dtype
        assert actual.shape == expected.shape
        assert torch.equal(actual, expected)
    elif isinstance(actual, dict):
        assert actual.keys() == expected.keys()
        for key in actual:
            assert_owned_equal(actual[key], expected[key])
    elif isinstance(actual, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            assert_owned_equal(left, right)
    else:
        assert actual == expected


def reach_stage(curriculum, lane, target):
    """Reach stages through improving completions, never inject stage history."""
    for batch in range(1, target):
        curriculum.commit_episode_outcomes([completion(lane, batch, 350 + 25 * batch, 500, 0.1, float(batch))])
    assert curriculum.get_stage_info(lane)["current_stage"] == target


class TestStaticCurriculum:
    def test_returns_same_decision_for_all_agents(self, static_policy):
        curriculum = fixed(static_policy, 3)
        decisions = curriculum.get_batch_decisions(None, ["agent_0", "agent_1", "agent_2"])
        assert len(decisions) == 3
        for decision in decisions:
            assert decision.difficulty_level == 0.7
            assert decision.reward_mode == "sparse"
            assert decision.active_meters == ["energy", "hygiene"]
            assert decision.depletion_multiplier == 2.0
            assert "Static curriculum" in decision.reason
            assert "0.7" in decision.reason

    def test_respects_different_difficulty_levels(self, static_policy):
        easy = fixed({**static_policy, "difficulty_level": 0.2}, 1)
        hard = fixed({**static_policy, "difficulty_level": 0.9}, 1)
        assert easy.get_batch_decisions(None, ["agent_0"])[0].difficulty_level == 0.2
        assert hard.get_batch_decisions(None, ["agent_0"])[0].difficulty_level == 0.9

    def test_checkpoint_state_returns_all_config(self, static_policy):
        curriculum = fixed(static_policy, 1)
        state = curriculum.checkpoint_state()
        assert set(state) == {"version", "strategy", "completion"}
        assert state["version"] == 2
        assert state["strategy"] == "static"
        assert state["completion"]["config"] == static_policy
        assert state["completion"]["lanes"] == [{"stage": 0, "dwell": 0, "episodes_at_stage": 0, "difficulty": 0.7}]

    def test_load_state_restores_configuration(self, static_policy):
        """Native load restores the same policy; reconfiguration is refused."""
        original = fixed(static_policy, 1)
        original.commit_episode_outcomes([completion(0, 1, 8, 10, 0.4, 15.0)])
        state = original.checkpoint_state()
        restored = fixed(static_policy, 1)
        restored.load_state(state)
        assert_owned_equal(restored.checkpoint_state(), state)
        incompatible = fixed({**static_policy, "difficulty_level": 0.3}, 1)
        before = incompatible.checkpoint_state()
        with pytest.raises(ValueError, match="configuration mismatch"):
            incompatible.load_state(state)
        assert_owned_equal(incompatible.checkpoint_state(), before)

    def test_checkpoint_restore_roundtrip(self, static_policy):
        original = fixed(static_policy, 2)
        original.commit_episode_outcomes([completion(0, 1, 10, 10, 0.4, 8.0), completion(1, 1, 4, 10, 0.8, 2.0)])
        restored = fixed(static_policy, 2)
        restored.load_state(original.checkpoint_state())
        assert_owned_equal(restored.checkpoint_state(), original.checkpoint_state())
        assert restored.get_batch_decisions(None, ["a", "b"]) == original.get_batch_decisions(None, ["a", "b"])
        assert restored.get_stage_info(0) == original.get_stage_info(0)
        assert restored.get_stage_info(1) == original.get_stage_info(1)


class TestPerformanceTracker:
    """Historical tracker identities now exercise actual completion consumers."""

    def test_update_step_accumulates_rewards_and_steps(self, static_policy):
        """Consume real completed reward windows and count eligible transitions."""
        curriculum = fixed(static_policy, 2)
        curriculum.commit_episode_outcomes([completion(0, 1, 2, 10, 0.2, 2.5), completion(1, 1, 3, 10, 0.8, 4.5)])
        for lane, steps, reward in [(0, 2, 2.5), (1, 3, 4.5)]:
            info = curriculum.get_stage_info(lane)
            assert info["steps_at_stage"] == steps
            assert info["episodes_at_stage"] == 1
            assert info["reward_total"] == reward
            assert info["reward_extrinsic"] == reward - 3.0
            assert info["reward_intrinsic"] == 1.0
            assert info["reward_shaping"] == 2.0

    def test_update_step_resets_on_done(self, static_policy):
        """A new completed window replaces metrics without resetting other lanes."""
        curriculum = fixed(static_policy, 2)
        curriculum.commit_episode_outcomes([completion(0, 1, 3, 10, 0.2, 10.0), completion(1, 1, 3, 10, 0.8, 23.0)])
        other = curriculum.get_stage_info(1)
        event = completion(0, 2, 2, 10, 0.4, 5.0)
        curriculum.commit_episode_outcomes([event])
        assert curriculum.get_stage_info(0)["reward_total"] == 5.0
        assert curriculum.get_stage_info(0)["steps_at_stage"] == 5
        assert curriculum.get_stage_info(0)["episodes_at_stage"] == 2
        assert curriculum.get_stage_info(1) == other
        before = curriculum.checkpoint_state()
        curriculum.commit_episode_outcomes([event])
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_get_survival_rate_calculation(self, static_policy):
        curriculum = fixed(static_policy, 3)
        curriculum.commit_episode_outcomes([completion(lane, 1, steps, 500, 0.4, 0.0) for lane, steps in enumerate([50, 100, 250])])
        assert [curriculum.get_stage_info(lane)["survival_rate"] for lane in range(3)] == [0.1, 0.2, 0.5]

    def test_get_learning_progress_positive(self, static_policy):
        curriculum = fixed(static_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 2, 10, 0.4, 100.0), completion(0, 2, 5, 10, 0.4, -100.0)])
        assert curriculum.get_stage_info(0)["learning_progress"] == pytest.approx(0.3)
        assert curriculum.get_stage_info(0)["survival_baseline"] == 0.5

    def test_get_learning_progress_negative(self, static_policy):
        curriculum = fixed(static_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 5, 10, 0.4, -100.0), completion(0, 2, 2, 10, 0.4, 100.0)])
        assert curriculum.get_stage_info(0)["learning_progress"] == pytest.approx(-0.3)

    def test_update_baseline_stores_current_average(self, static_policy):
        """Baseline is the completed fraction in the same units as progress."""
        curriculum = fixed(static_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 3, 10, 0.4, 15.0)])
        info = curriculum.get_stage_info(0)
        assert info["survival_baseline"] == 0.3
        assert info["learning_progress"] == 0.3
        curriculum.commit_episode_outcomes([completion(0, 2, 6, 10, 0.4, 0.0)])
        assert curriculum.get_stage_info(0)["survival_baseline"] == 0.6
        assert curriculum.get_stage_info(0)["learning_progress"] == 0.3


class TestAdversarialCurriculumStageAdvancement:
    def test_should_not_advance_without_minimum_steps(self, adversarial_policy):
        curriculum = adaptive({**adversarial_policy, "min_steps_at_stage": 1000}, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 500, 500, 0.0, 100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.get_stage_info(0)["steps_at_stage"] == 500
        assert curriculum.transition_events == []

    def test_should_not_advance_from_stage_5(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 5)
        curriculum.transition_events.clear()
        curriculum.commit_episode_outcomes([completion(0, 5, 500, 500, 0.0, 100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 5
        assert curriculum.transition_events == []

    def test_should_advance_with_all_conditions_met(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 2)
        curriculum.commit_episode_outcomes([completion(0, 2, 400, 500, 0.3, -100.0)])
        info = curriculum.get_stage_info(0)
        assert info["current_stage"] == 3
        assert info["survival_rate"] == 0.8
        assert info["learning_progress"] == pytest.approx(0.05)
        assert info["steps_at_stage"] == 0
        assert info["episodes_at_stage"] == 0

    def test_should_not_advance_with_low_survival(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 100, 500, 0.3, 100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.get_stage_info(0)["learning_progress"] == 0.2

    def test_should_not_advance_with_negative_learning(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 2)
        curriculum.commit_episode_outcomes([completion(0, 2, 360, 500, 0.3, 1000.0)])
        assert curriculum.get_stage_info(0)["learning_progress"] == pytest.approx(-0.03)
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.transition_events[-1]["reason"] == "retreat"

    def test_should_not_advance_with_high_entropy(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 400, 500, 0.8, 100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.get_stage_info(0)["policy_entropy"] == 0.8
        assert curriculum.get_stage_info(0)["steps_at_stage"] == 400

    def test_stage_transition_logs_reason(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        event = completion(0, 1, 450, 500, 0.3, 90.0)
        curriculum.commit_episode_outcomes([event])
        assert curriculum.transition_events == [
            {
                "agent_idx": 0,
                "world_id": "world-0",
                "world_episode_seq": 1,
                "batch_episode": 1,
                "from_stage": 1,
                "to_stage": 2,
                "reason": "advance",
                "survival_rate": 0.9,
                "learning_progress": 0.9,
                "entropy": 0.3,
                "steps_at_stage": 450,
            }
        ]
        curriculum.commit_episode_outcomes([event])
        assert len(curriculum.transition_events) == 1


class TestAdversarialCurriculumStageRetreat:
    def test_should_not_retreat_from_stage_1(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 10, 500, 1.0, -100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.transition_events == []

    def test_should_not_retreat_without_minimum_steps(self, adversarial_policy):
        curriculum = adaptive({**adversarial_policy, "min_steps_at_stage": 500}, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 500, 500, 0.0, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        curriculum.transition_events.clear()
        curriculum.commit_episode_outcomes([completion(0, 2, 100, 500, 1.0, -100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        assert curriculum.get_stage_info(0)["steps_at_stage"] == 100
        assert curriculum.transition_events == []

    def test_should_retreat_with_low_survival(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 4)
        curriculum.commit_episode_outcomes([completion(0, 4, 100, 1000, 1.0, 100.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 3
        assert curriculum.get_stage_info(0)["survival_rate"] == 0.1
        assert curriculum.get_stage_info(0)["steps_at_stage"] == 0
        assert curriculum.get_stage_info(0)["episodes_at_stage"] == 0
        curriculum.commit_episode_outcomes([completion(0, 5, 200, 1000, 1.0, 100.0)])
        info = curriculum.get_stage_info(0)
        assert info["current_stage"] == 2
        assert info["survival_rate"] == 0.2
        assert info["learning_progress"] == pytest.approx(0.1)
        assert info["policy_entropy"] == 1.0
        assert info["steps_at_stage"] == 0
        assert info["episodes_at_stage"] == 0
        transition = curriculum.transition_events[-1]
        assert transition["from_stage"] == 3
        assert transition["to_stage"] == 2
        assert transition["reason"] == "retreat"
        assert transition["survival_rate"] == 0.2
        assert transition["learning_progress"] == pytest.approx(0.1)
        assert transition["steps_at_stage"] == 200

    def test_should_retreat_with_negative_learning(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 3)
        curriculum.commit_episode_outcomes([completion(0, 3, 390, 500, 1.0, 1000.0)])
        assert curriculum.get_stage_info(0)["survival_rate"] == 0.78
        assert curriculum.get_stage_info(0)["learning_progress"] == pytest.approx(-0.02)
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        assert curriculum.transition_events[-1]["reason"] == "retreat"


class TestAdversarialCurriculumEntropyCalculation:
    """Entropy calculation belongs to the producer; consume its actual readings."""

    def test_entropy_zero_for_deterministic_policy(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 450, 500, 0.0, 0.0)])
        assert curriculum.get_stage_info(0)["policy_entropy"] == 0.0
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        assert curriculum.transition_events[0]["entropy"] == 0.0

    def test_entropy_high_for_uniform_policy(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        curriculum.commit_episode_outcomes([completion(0, 1, 450, 500, 1.0, 0.0)])
        assert curriculum.get_stage_info(0)["policy_entropy"] == 1.0
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        assert curriculum.transition_events == []

    def test_entropy_batch_processing(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 2)
        curriculum.commit_episode_outcomes([completion(0, 1, 450, 500, 0.0, 0.0), completion(1, 1, 450, 500, 1.0, 0.0)])
        assert [curriculum.get_stage_info(lane)["policy_entropy"] for lane in range(2)] == [0.0, 1.0]
        assert [curriculum.get_stage_info(lane)["current_stage"] for lane in range(2)] == [2, 1]


class TestAdversarialCurriculumBatchDecisions:
    def test_get_batch_decisions_advances_stage(self, adversarial_policy):
        """Commit advances; repeated decision reads preserve that committed stage."""
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 2)
        curriculum.commit_episode_outcomes([completion(0, 2, 400, 500, 0.0, 100.0)])
        before = curriculum.checkpoint_state()
        for _ in range(3):
            decision = curriculum.get_batch_decisions(None, ["agent_0"])[0]
            assert decision.reward_mode == "shaped"
            assert "Stage 3" in decision.reason
            assert decision.difficulty_level == 0.5
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_get_batch_decisions_retreats_stage(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 3)
        curriculum.commit_episode_outcomes([completion(0, 3, 100, 500, 1.0, -10.0)])
        before = curriculum.checkpoint_state()
        decision = curriculum.get_batch_decisions(None, ["agent_0"])[0]
        assert "Stage 2" in decision.reason
        assert decision.difficulty_level == 0.25
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_get_batch_decisions_maps_stage_to_difficulty(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 5)
        for lane, stage in enumerate(range(1, 6)):
            reach_stage(curriculum, lane, stage)
        decisions = curriculum.get_batch_decisions(None, ["a0", "a1", "a2", "a3", "a4"])
        assert [decision.difficulty_level for decision in decisions] == [0.0, 0.25, 0.5, 0.75, 1.0]
        assert [decision.depletion_multiplier for decision in decisions] == [0.2, 0.5, 0.8, 1.0, 1.0]
        assert [decision.active_meters for decision in decisions] == [
            ["energy", "hygiene"],
            ["energy", "hygiene", "satiation"],
            ["energy", "hygiene", "satiation", "money"],
            ["energy", "hygiene", "satiation", "money", "mood", "social"],
            ["energy", "hygiene", "satiation", "money", "mood", "social"],
        ]
        assert [decision.reward_mode for decision in decisions] == ["shaped", "shaped", "shaped", "shaped", "sparse"]

    def test_stage_5_is_sparse_rewards(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        reach_stage(curriculum, 0, 5)
        decision = curriculum.get_batch_decisions(None, ["agent_0"])[0]
        assert decision.reward_mode == "sparse"
        assert "SPARSE" in decision.reason
        info = curriculum.get_stage_info(0)
        assert info["active_meters_status"] == "unqualified"
        assert info["reward_mode_status"] == "unqualified"
        assert info["difficulty_calibrated"] is False

    def test_adversarial_curriculum_thresholds_from_config(self, adversarial_policy):
        """Resolved constructor policy replaces removed configure_from_training."""
        policy = {
            **adversarial_policy,
            "survival_advance_threshold": 0.75,
            "survival_retreat_threshold": 0.25,
            "entropy_gate": 0.4,
            "min_steps_at_stage": 200,
        }
        curriculum = adaptive(policy, 1)
        expected = {key: value for key, value in policy.items() if key != "device"}
        assert curriculum.checkpoint_state()["completion"]["config"] == expected
        curriculum.commit_episode_outcomes([completion(0, 1, 150, 200, 0.3, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        curriculum.commit_episode_outcomes([completion(0, 2, 160, 200, 0.4, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1
        curriculum.commit_episode_outcomes([completion(0, 3, 170, 200, 0.3, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        curriculum.commit_episode_outcomes([completion(0, 4, 200, 200, 0.4, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        curriculum.commit_episode_outcomes([completion(0, 5, 50, 200, 0.8, 0.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 1

        # Sufficient dwell isolates the authored .75 threshold from default .7.
        advance = adaptive(policy, 1)
        advance.commit_episode_outcomes([completion(0, 1, 720, 1000, 0.3, 0.0)])
        assert advance.get_stage_info(0)["current_stage"] == 1
        assert advance.get_stage_info(0)["survival_rate"] == 0.72
        assert advance.get_stage_info(0)["learning_progress"] == 0.72
        assert advance.get_stage_info(0)["steps_at_stage"] == 720
        assert advance.transition_events == []
        advance.commit_episode_outcomes([completion(0, 2, 800, 1000, 0.3, 0.0)])
        assert advance.get_stage_info(0)["current_stage"] == 2
        assert advance.transition_events[-1]["reason"] == "advance"

        # High survival and low entropy isolate dwell200 from default100.
        dwell = adaptive(policy, 1)
        dwell.commit_episode_outcomes([completion(0, 1, 150, 160, 0.3, 0.0)])
        assert dwell.get_stage_info(0)["current_stage"] == 1
        assert dwell.get_stage_info(0)["survival_rate"] == 0.9375
        assert dwell.get_stage_info(0)["learning_progress"] == 0.9375
        assert dwell.get_stage_info(0)["steps_at_stage"] == 150
        assert dwell.transition_events == []
        dwell.commit_episode_outcomes([completion(0, 2, 160, 160, 0.3, 0.0)])
        assert dwell.get_stage_info(0)["current_stage"] == 2
        assert dwell.transition_events[-1]["reason"] == "advance"
        assert dwell.transition_events[-1]["steps_at_stage"] == 310

        # Positive progress on either side isolates configured retreat .25.
        retreat = adaptive(policy, 1)
        for batch, steps in [(1, 400), (2, 425), (3, 450)]:
            retreat.commit_episode_outcomes([completion(0, batch, steps, 500, 0.3, 0.0)])
        assert retreat.get_stage_info(0)["current_stage"] == 4
        retreat.commit_episode_outcomes([completion(0, 4, 200, 2000, 1.0, 0.0)])
        assert retreat.get_stage_info(0)["current_stage"] == 3
        retreat.transition_events.clear()
        retreat.commit_episode_outcomes([completion(0, 5, 540, 2000, 1.0, 0.0)])
        assert retreat.get_stage_info(0)["survival_rate"] == 0.27
        assert retreat.get_stage_info(0)["learning_progress"] == pytest.approx(0.17)
        assert retreat.get_stage_info(0)["current_stage"] == 3
        assert retreat.get_stage_info(0)["steps_at_stage"] == 540
        assert retreat.get_stage_info(0)["episodes_at_stage"] == 1
        assert retreat.transition_events == []
        retreat.commit_episode_outcomes([completion(0, 6, 200, 2000, 1.0, 0.0)])
        assert retreat.get_stage_info(0)["current_stage"] == 2
        retreat.commit_episode_outcomes([completion(0, 7, 480, 2000, 1.0, 0.0)])
        assert retreat.get_stage_info(0)["survival_rate"] == 0.24
        assert retreat.get_stage_info(0)["learning_progress"] == pytest.approx(0.14)
        assert retreat.get_stage_info(0)["current_stage"] == 1
        assert retreat.get_stage_info(0)["steps_at_stage"] == 0
        assert retreat.get_stage_info(0)["episodes_at_stage"] == 0
        assert retreat.transition_events[-1]["from_stage"] == 2
        assert retreat.transition_events[-1]["to_stage"] == 1
        assert retreat.transition_events[-1]["reason"] == "retreat"
        assert retreat.transition_events[-1]["steps_at_stage"] == 480

    def test_adversarial_curriculum_difficulty_mapping_from_config(self, adversarial_policy):
        curriculum = adaptive({**adversarial_policy, "min_difficulty": 0.2, "max_difficulty": 0.6}, 5)
        for lane, stage in enumerate(range(1, 6)):
            reach_stage(curriculum, lane, stage)
        decisions = curriculum.get_batch_decisions(None, ["a0", "a1", "a2", "a3", "a4"])
        assert [decision.difficulty_level for decision in decisions] == pytest.approx([0.2, 0.3, 0.4, 0.5, 0.6])
        assert curriculum.get_stage_info(0)["adaptation_rate_active"] is False
        assert curriculum.get_stage_info(0)["adaptation_rate_units"] == "inactive"


def populated(policy):
    curriculum = adaptive(policy, 3)
    reach_stage(curriculum, 0, 3)
    reach_stage(curriculum, 1, 2)
    reach_stage(curriculum, 2, 4)
    curriculum.commit_episode_outcomes(
        [
            completion(0, 4, 400, 500, 1.0, 12.0),
            completion(1, 4, 400, 500, 1.0, 3.5),
            completion(2, 4, 450, 500, 1.0, 0.0),
        ]
    )
    return curriculum


class TestAdversarialCurriculumStatePersistence:
    def test_checkpoint_state_includes_all_tracker_state(self, adversarial_policy):
        """Persist every current lane, metric and identity receipt, with ownership."""
        curriculum = populated(adversarial_policy)
        state = curriculum.checkpoint_state()
        body = state["completion"]
        assert set(body) == {"config", "generation", "lanes", "events", "metrics"}
        assert [lane["stage"] for lane in body["lanes"]] == [3, 2, 4]
        assert [lane["dwell"] for lane in body["lanes"]] == [400, 400, 450]
        assert [lane["episodes_at_stage"] for lane in body["lanes"]] == [1, 1, 1]
        assert [row["event"]["reward_total"] for row in body["metrics"]] == [12.0, 3.5, 0.0]
        assert [row["previous_fraction"] for row in body["metrics"]] == [0.8, 0.75, 0.85]
        assert len(body["events"]) == 9
        before = curriculum.checkpoint_state()
        body["lanes"][0]["dwell"] = 0
        body["metrics"][0]["event"]["reward_total"] = -999.0
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_load_state_restores_all_state(self, adversarial_policy):
        original = populated(adversarial_policy)
        state = original.checkpoint_state()
        restored = adaptive(adversarial_policy, 3)
        restored.load_state(state)
        assert_owned_equal(restored.checkpoint_state(), state)
        for lane in range(3):
            assert restored.get_stage_info(lane) == original.get_stage_info(lane)
        state["completion"]["lanes"][0]["dwell"] = 0
        assert_owned_equal(restored.checkpoint_state(), original.checkpoint_state())


class TestCurriculumSignalPurity:
    def test_curriculum_has_canonical_checkpoint_methods(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        event = completion(0, 1, 10, 10, 0.8, 1000.0)
        curriculum.commit_episode_outcomes([event])
        state = curriculum.checkpoint_state()
        curriculum.validate_checkpoint_state(state)
        assert set(state) == {"version", "strategy", "completion"}
        assert state["completion"]["metrics"][0]["previous_fraction"] == 0.0
        assert curriculum.get_stage_info(0)["survival_rate"] == 1.0
        assert curriculum.get_stage_info(0)["learning_progress"] == 1.0
        for _ in range(3):
            curriculum.get_batch_decisions(None, ["agent_0"])
        assert curriculum.get_stage_info(0)["survival_rate"] == 1.0
        assert_owned_equal(curriculum.checkpoint_state(), state)

    def test_curriculum_state_preserves_agent_stages(self, adversarial_policy):
        original = adaptive(adversarial_policy, 1)
        reach_stage(original, 0, 3)
        original.commit_episode_outcomes([completion(0, 3, 400, 500, 1.0, 1000.0)])
        restored = adaptive(adversarial_policy, 1)
        assert restored.get_stage_info(0)["current_stage"] == 1
        restored.load_state(original.checkpoint_state())
        assert restored.get_stage_info(0)["current_stage"] == 3
        assert restored.get_stage_info(0)["steps_at_stage"] == 400
        assert restored.get_stage_info(0) == original.get_stage_info(0)


class TestAdversarialCurriculumFullStateRoundtrip:
    def test_checkpoint_state_includes_all_tracker_tensors(self, adversarial_policy):
        """Current schema preserves all real completion scalar/tensor readings."""
        curriculum = populated(adversarial_policy)
        state = curriculum.checkpoint_state()
        assert state["version"] == 2
        assert state["strategy"] == "adversarial"
        assert set(state["completion"]["lanes"][0]) == {"stage", "dwell", "episodes_at_stage", "difficulty"}
        assert set(state["completion"]["metrics"][0]) == {"event", "previous_fraction"}
        assert_owned_equal(state["completion"]["metrics"][0]["event"], lane_outcome_state(completion(0, 4, 400, 500, 1.0, 12.0)))
        curriculum.validate_checkpoint_state(state)

    def test_load_state_restores_every_tensor_exactly(self, adversarial_policy):
        original = populated(adversarial_policy)
        state = original.checkpoint_state()
        restored = adaptive(adversarial_policy, 3)
        restored.load_state(state)
        assert_owned_equal(restored.checkpoint_state(), state)
        before = restored.checkpoint_state()
        for row in state["completion"]["metrics"]:
            for reading in row["event"]["outcome"].values():
                if isinstance(reading, torch.Tensor):
                    reading.add_(99)
        assert_owned_equal(restored.checkpoint_state(), before)

    def test_resume_continues_episode_counter(self, adversarial_policy):
        original = populated(adversarial_policy)
        state = original.checkpoint_state()
        restored = adaptive(adversarial_policy, 3)
        restored.load_state(state)
        others = [restored.get_stage_info(lane) for lane in [1, 2]]
        event = completion(0, 5, 400, 500, 1.0, 100.0)
        restored.commit_episode_outcomes([event])
        assert restored.get_stage_info(0)["episodes_at_stage"] == 2
        assert restored.get_stage_info(0)["steps_at_stage"] == 800
        assert [restored.get_stage_info(lane) for lane in [1, 2]] == others
        before = restored.checkpoint_state()
        restored.commit_episode_outcomes([event])
        assert_owned_equal(restored.checkpoint_state(), before)


class TestAdversarialCurriculumLoadStateStrictness:
    @pytest.mark.parametrize("missing", ["version", "strategy", "completion"])
    def test_load_state_raises_on_missing_key(self, adversarial_policy, missing):
        curriculum = adaptive(adversarial_policy, 1)
        before = curriculum.checkpoint_state()
        partial = deepcopy(before)
        del partial[missing]
        with pytest.raises(ValueError, match="exact current curriculum schema"):
            curriculum.load_state(partial)
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_load_state_raises_on_num_agents_mismatch(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 2)
        before = curriculum.checkpoint_state()
        state = populated(adversarial_policy).checkpoint_state()
        with pytest.raises(ValueError, match="population mismatch"):
            curriculum.load_state(state)
        assert_owned_equal(curriculum.checkpoint_state(), before)


class TestCurriculumCheckpointValidators:
    def test_static_validator_requires_exact_typed_schema_without_mutation(self, static_policy):
        curriculum = fixed(static_policy, 1)
        before = curriculum.checkpoint_state()
        unknown = deepcopy(before)
        unknown["removed_field"] = True
        with pytest.raises(ValueError, match="exact current curriculum schema"):
            curriculum.validate_checkpoint_state(unknown)
        malformed = deepcopy(before)
        malformed["completion"]["config"]["active_meters"] = ["energy", 1]
        with pytest.raises(ValueError, match="configuration mismatch"):
            curriculum.validate_checkpoint_state(malformed)
        malformed = deepcopy(before)
        malformed["completion"]["lanes"][0]["dwell"] = True
        with pytest.raises(ValueError, match="dwell/completion count"):
            curriculum.validate_checkpoint_state(malformed)
        assert_owned_equal(curriculum.checkpoint_state(), before)

    def test_adversarial_validator_requires_exact_tensor_contract_without_mutation(self, adversarial_policy):
        """Exact current typed schema replaces the obsolete seven-tensor schema."""
        curriculum = populated(adversarial_policy)
        before = curriculum.checkpoint_state()
        unknown = deepcopy(before)
        unknown["removed_field"] = torch.zeros(3)
        with pytest.raises(ValueError, match="exact current curriculum schema"):
            curriculum.validate_checkpoint_state(unknown)
        malformed = deepcopy(before)
        malformed["completion"]["lanes"][0]["stage"] = 3.0
        with pytest.raises(ValueError, match="curriculum stage"):
            curriculum.validate_checkpoint_state(malformed)
        malformed = deepcopy(before)
        malformed["completion"]["metrics"][0]["previous_fraction"] = 2.0
        with pytest.raises(ValueError, match="Previous fraction"):
            curriculum.validate_checkpoint_state(malformed)
        assert_owned_equal(curriculum.checkpoint_state(), before)


class TestCurrentCompletionControls:
    @pytest.mark.parametrize("rate, expected", [(0.01, 0.1), (0.1, 0.25)])
    def test_rate_has_declared_effect(self, adversarial_policy, rate, expected):
        curriculum = adaptive(
            {**adversarial_policy, "difficulty_mode": "rate_limited", "adaptation_rate": rate, "min_steps_at_stage": 10}, 1
        )
        event = completion(0, 1, 10, 10, 0.0, 0.0)
        curriculum.commit_episode_outcomes([event])
        assert curriculum.get_stage_info(0)["current_stage"] == 2
        assert curriculum.get_stage_info(0)["adaptation_rate_active"] is True
        assert curriculum.get_stage_info(0)["adaptation_rate_units"] == "difficulty_per_eligible_transition"
        assert curriculum.get_batch_decisions(None, ["a"])[0].difficulty_level == pytest.approx(expected)
        before = curriculum.checkpoint_state()
        curriculum.commit_episode_outcomes([event])
        assert_owned_equal(curriculum.checkpoint_state(), before)

    @pytest.mark.parametrize("mode", ["stage_band", "rate_limited"])
    def test_singleton_band(self, adversarial_policy, mode):
        curriculum = adaptive({**adversarial_policy, "difficulty_mode": mode, "min_difficulty": 0.6, "max_difficulty": 0.6}, 1)
        assert curriculum.get_batch_decisions(None, ["a"])[0].difficulty_level == 0.6
        reach_stage(curriculum, 0, 5)
        assert curriculum.get_batch_decisions(None, ["a"])[0].difficulty_level == 0.6
        curriculum.commit_episode_outcomes([completion(0, 5, 100, 500, 1.0, -999.0)])
        assert curriculum.get_stage_info(0)["current_stage"] == 4
        assert curriculum.get_batch_decisions(None, ["a"])[0].difficulty_level == 0.6

    def test_prepare_is_pure_and_commits_owned_content_once(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        event = completion(0, 1, 450, 500, 0.0, 10.0)
        expected = lane_outcome_state(event)
        before = curriculum.checkpoint_state()
        prepared = curriculum.prepare_episode_outcomes([event])
        assert_owned_equal(curriculum.checkpoint_state(), before)
        assert curriculum.transition_events == []
        event.outcome.final_observation.add_(99)
        event.outcome.final_meters.add_(99)
        curriculum.commit_prepared_episode_outcomes(prepared)
        after = curriculum.checkpoint_state()
        assert_owned_equal(after["completion"]["metrics"][0]["event"], expected)
        curriculum.commit_prepared_episode_outcomes(prepared)
        assert_owned_equal(curriculum.checkpoint_state(), after)
        assert len(curriculum.transition_events) == 1
        with pytest.raises(ValueError, match="changed content"):
            curriculum.commit_episode_outcomes([replace(event, reward_total=11.0, reward_extrinsic=8.0)])
        assert_owned_equal(curriculum.checkpoint_state(), after)

    def test_later_invalid_lane_refuses_entire_batch(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        before = curriculum.checkpoint_state()
        with pytest.raises(ValueError, match="outside initialized population"):
            curriculum.commit_episode_outcomes([completion(0, 1, 450, 500, 0.0, 10.0), completion(1, 1, 450, 500, 0.0, 10.0)])
        assert_owned_equal(curriculum.checkpoint_state(), before)
        assert curriculum.transition_events == []

    def test_dwell_counts_ten_transitions_and_retains_completed_fraction(self, adversarial_policy):
        curriculum = adaptive(adversarial_policy, 1)
        event = completion(0, 1, 10, 10, 1.0, 1000.0)
        curriculum.commit_episode_outcomes([event])
        for _ in range(3):
            curriculum.get_batch_decisions(None, ["a"])
        info = curriculum.get_stage_info(0)
        assert info["steps_at_stage"] == 10
        assert info["episodes_at_stage"] == 1
        assert info["survival_rate"] == 1.0
        assert info["survival_baseline"] == 1.0
        assert info["completion_reason"] == event.outcome.reason

    def test_reward_components_cannot_contaminate_stage_or_progress(self, adversarial_policy):
        pure = adaptive(adversarial_policy, 1)
        augmented = adaptive(adversarial_policy, 1)
        first = completion(0, 1, 400, 500, 0.1, 0.0)
        second = completion(0, 2, 450, 500, 0.1, -1000.0)
        for event in [first, second]:
            pure.commit_episode_outcomes([event])
            augmented.commit_episode_outcomes(
                [replace(event, reward_total=99999.0, reward_extrinsic=-1.0, reward_intrinsic=100000.0, reward_shaping=0.0)]
            )
        for key in ["current_stage", "steps_at_stage", "episodes_at_stage", "survival_rate", "survival_baseline", "learning_progress"]:
            assert pure.get_stage_info(0)[key] == augmented.get_stage_info(0)[key]
        assert pure.get_stage_info(0)["current_stage"] == 3
        assert pure.get_stage_info(0)["learning_progress"] == pytest.approx(0.1)
        assert pure.get_batch_decisions(None, ["a"]) == augmented.get_batch_decisions(None, ["a"])
