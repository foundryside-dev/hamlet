Basecfef2979e70f0cc9a850c9928386e2e243a0b21b
Candidate2558d794476a4e7a1878b3c334b62d1733d62bb9
Only1literalpredicatealigned+171testlines;3whole659<=1050, otherstagedBanktest901excludedfromyourreadinventory.
diff --git a/src/townlet/training/episode.py b/src/townlet/training/episode.py
index 1749d2fe..2807d75e 100644
--- a/src/townlet/training/episode.py
+++ b/src/townlet/training/episode.py
@@ -45,17 +45,17 @@ class LaneOutcome:
 
     def __post_init__(self) -> None:
         if not isinstance(self.outcome, EpisodeCompletion):
             raise ValueError("outcome must be an EpisodeCompletion")
         for name, minimum in (("batch_episode", 0), ("planned_horizon", 1), ("world_episode_seq", 0)):
             value = getattr(self, name)
             if type(value) is not int or value < minimum:
                 raise ValueError(f"{name} must be an integer >= {minimum}")
-        if not isinstance(self.world_id, str) or not self.world_id.strip():
+        if not isinstance(self.world_id, str) or not self.world_id:
             raise ValueError("world_id must be a concrete nonempty string")
         for name in ("reward_total", "reward_extrinsic", "reward_intrinsic", "reward_shaping", "policy_entropy"):
             value = getattr(self, name)
             if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(float(value)):
                 raise ValueError(f"{name} must be a finite real value")
             object.__setattr__(self, name, float(value))
         object.__setattr__(
             self,
diff --git a/tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py b/tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py
new file mode 100644
index 00000000..bc9c9778
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py
@@ -0,0 +1,171 @@
+"""Keep completion-envelope world identities aligned with exact roster IDs."""
+
+import hashlib
+from typing import Any
+
+import pytest
+import torch
+
+from townlet.config.world_roster import WorldRosterDeclaration
+from townlet.training.episode import (
+    EpisodeCompletion,
+    LaneOutcome,
+    freeze_lane_outcome,
+    lane_outcome_from_state,
+    lane_outcome_state,
+)
+
+WHITESPACE_IDS = pytest.mark.parametrize("world_id", [" ", "\t", "\r"], ids=["space", "tab", "carriage-return"])
+EXACT_IDS = (
+    "world-A",
+    " world-A",
+    "world-A ",
+    "World-A",
+    "é",
+    "e\u0301",
+    "world\rA",
+    "world\tA",
+    "world A",
+)
+EXACT_NAMES = (
+    "ordinary",
+    "leading-space",
+    "trailing-space",
+    "case-distinct",
+    "unicode-composed",
+    "unicode-decomposed",
+    "embedded-carriage-return",
+    "embedded-tab",
+    "embedded-space",
+)
+
+
+def _outcome(world_id: Any) -> LaneOutcome:
+    return LaneOutcome(
+        outcome=EpisodeCompletion(
+            agent_idx=0,
+            reason="cap",
+            survival_time=1,
+            final_observation=torch.tensor([[1.0, -2.0]], dtype=torch.float32, device="cpu"),
+            final_meters=torch.tensor([3.0, 4.0], dtype=torch.float64, device="cpu"),
+        ),
+        batch_episode=0,
+        planned_horizon=2,
+        reward_total=1.5,
+        reward_extrinsic=1.0,
+        reward_intrinsic=0.25,
+        reward_shaping=0.25,
+        policy_entropy=0.5,
+        world_id=world_id,
+        world_episode_seq=1,
+    )
+
+
+def _assert_envelope(actual: LaneOutcome, expected: LaneOutcome) -> None:
+    assert actual.world_id == expected.world_id
+    assert actual.batch_episode == expected.batch_episode
+    assert actual.planned_horizon == expected.planned_horizon
+    assert actual.world_episode_seq == expected.world_episode_seq
+    assert actual.reward_total == expected.reward_total
+    assert actual.reward_extrinsic == expected.reward_extrinsic
+    assert actual.reward_intrinsic == expected.reward_intrinsic
+    assert actual.reward_shaping == expected.reward_shaping
+    assert actual.policy_entropy == expected.policy_entropy
+    assert actual.outcome.agent_idx == expected.outcome.agent_idx
+    assert actual.outcome.reason == expected.outcome.reason
+    assert actual.outcome.survival_time == expected.outcome.survival_time
+    for name in ("final_observation", "final_meters"):
+        actual_reading = getattr(actual.outcome, name)
+        expected_reading = getattr(expected.outcome, name)
+        assert actual_reading.device.type == "cpu"
+        assert actual_reading.layout == torch.strided
+        assert actual_reading.dtype == expected_reading.dtype
+        assert actual_reading.shape == expected_reading.shape
+        assert torch.equal(actual_reading, expected_reading)
+
+
+def test_valid_ordinary_completion_control() -> None:
+    event = _outcome("world-A")
+    assert event.outcome.survival_time > 0
+    assert event.planned_horizon >= event.outcome.survival_time
+    for reading in (event.outcome.final_observation, event.outcome.final_meters):
+        assert reading.device.type == "cpu"
+        assert reading.layout == torch.strided
+        assert torch.isfinite(reading).all().item()
+    _assert_envelope(lane_outcome_from_state(lane_outcome_state(event)), event)
+    frozen = freeze_lane_outcome(event)
+    assert frozen.fingerprint == hashlib.sha256(frozen.payload).hexdigest()
+    _assert_envelope(frozen.to_outcome(), event)
+
+
+def test_roster_accepts_exact_whitespace_ids_control() -> None:
+    world_ids = (" ", "\t", "\r")
+    roster = WorldRosterDeclaration(world_ids=world_ids)
+    assert roster.world_ids == world_ids
+    assert roster.to_dict() == {"schema": "world-roster-v1", "world_ids": list(world_ids)}
+    assert WorldRosterDeclaration.from_dict(roster.to_dict()).world_ids == world_ids
+
+
+@WHITESPACE_IDS
+def test_declared_whitespace_id_constructs_outcome(world_id: str) -> None:
+    roster = WorldRosterDeclaration(world_ids=(world_id,))
+    event = _outcome(roster.world_ids[0])
+    assert event.world_id == world_id
+
+
+@WHITESPACE_IDS
+def test_declared_whitespace_id_current_state_roundtrip(world_id: str) -> None:
+    roster = WorldRosterDeclaration(world_ids=(world_id,))
+    event = _outcome(roster.world_ids[0])
+    state = lane_outcome_state(event)
+    assert state["world_id"] == world_id
+    restored = lane_outcome_from_state(state)
+    _assert_envelope(restored, event)
+    assert restored.world_id == world_id
+
+
+@WHITESPACE_IDS
+def test_declared_whitespace_id_frozen_roundtrip(world_id: str) -> None:
+    roster = WorldRosterDeclaration(world_ids=(world_id,))
+    event = _outcome(roster.world_ids[0])
+    frozen = freeze_lane_outcome(event)
+    assert frozen.fingerprint == hashlib.sha256(frozen.payload).hexdigest()
+    restored = frozen.to_outcome()
+    _assert_envelope(restored, event)
+    assert restored.world_id == world_id
+
+
+@pytest.mark.parametrize("world_id", EXACT_IDS, ids=EXACT_NAMES)
+def test_existing_exact_id_preservation(world_id: str) -> None:
+    roster = WorldRosterDeclaration(world_ids=(world_id,))
+    assert roster.world_ids == (world_id,)
+    event = _outcome(roster.world_ids[0])
+    assert event.world_id == world_id
+    state = lane_outcome_state(event)
+    assert state["world_id"] == world_id
+    _assert_envelope(lane_outcome_from_state(state), event)
+    _assert_envelope(freeze_lane_outcome(event).to_outcome(), event)
+
+
+@pytest.mark.parametrize("world_id", ["", None, 0, False, b"world-A"], ids=["empty", "none", "integer", "boolean", "bytes"])
+def test_empty_or_nonstring_id_still_refused(world_id: Any) -> None:
+    with pytest.raises(ValueError, match="world_id"):
+        _outcome(world_id)
+    state = lane_outcome_state(_outcome("world-A"))
+    state["world_id"] = world_id
+    with pytest.raises(ValueError, match="world_id"):
+        lane_outcome_from_state(state)
+
+
+def test_existing_distinct_exact_ids_have_distinct_fingerprints() -> None:
+    assert len(set(EXACT_IDS)) == len(EXACT_IDS)
+    fingerprints = [freeze_lane_outcome(_outcome(world_id)).fingerprint for world_id in EXACT_IDS]
+    assert len(set(fingerprints)) == len(EXACT_IDS)
+
+
+def test_whitespace_and_existing_exact_ids_have_distinct_fingerprints() -> None:
+    world_ids = (*EXACT_IDS, " ", "\t", "\r")
+    roster = WorldRosterDeclaration(world_ids=world_ids)
+    assert roster.world_ids == world_ids
+    fingerprints = [freeze_lane_outcome(_outcome(world_id)).fingerprint for world_id in roster.world_ids]
+    assert len(set(fingerprints)) == len(world_ids)
