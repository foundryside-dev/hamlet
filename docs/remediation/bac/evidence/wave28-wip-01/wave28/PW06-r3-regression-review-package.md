# PW06 implementation fixround1 newregressions only
9f27d612ad3527b1309bfc60219e58d45d03c834 -> 2453754fabb4833e7488b44e12bf8c3d8e3bc718

diff --git a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
index e1584e5c..6c5380e2 100644
--- a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
+++ b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
@@ -258,20 +258,21 @@ class Rig:
             device="cpu",
             validate_accepted_episode=self.env.validate_accepted_episode,
             issuer_factory=lambda owner: RecordedIssuer(owner, self.issued),
             report_allocation=self.report_allocation,
         )
         self.other, self.population = LocalRole(), LocalRole()
         roles = {key: self.other for key in ("curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")}
         roles.update(population=self.population, curiosity=self.bank)
         self.authority = self.env.bind_boundary_authority(owner=self.other, role_owners=roles)
         self.release, self.accepted, self.observation = None, None, None
+        self.retained_batches = (1,)
 
     def report_allocation(self, estimate):
         self.reports.append(estimate)
         if self.reject_restore_allocation and estimate.operation == "restore":
             raise MemoryError("admitted restore allocation refused")
 
     def begin(self, batch):
         if self.release is None:
             self.release = self.env.install_boundary_release(self.authority.bootstrap(first_batch_episode=batch))
         reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
@@ -398,21 +399,23 @@ class Rig:
             accepted_identity=self.accepted,
             completion_content=arguments["completion_content"],
             retirement_receipt=committed,
             **children,
         )
         self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
         self.source_prepared, self.source_committed = prepared, committed
         return self.world_checkpoint(), arguments
 
     def world_checkpoint(self):
-        return self.env.checkpoint_world_state(kind="COMPLETED", release=self.release, retained_binding_batches=(1,), initial=None)
+        return self.env.checkpoint_world_state(
+            kind="COMPLETED", release=self.release, retained_binding_batches=self.retained_batches, initial=None
+        )
 
 
 class Correlation:
     """Local parent custody control using genuine ENV preparation, never True."""
 
     def __init__(self, rig, world_state):
         self.rig, self.world_state = rig, deepcopy(world_state)
         self.prepared = rig.env.prepare_world_restore(
             kind="COMPLETED",
             state=world_state,
@@ -1392,10 +1395,104 @@ def test_current_hc_preserves_captured_rows_and_private_counters(compiled):
         pytest.fail("current captured replay must not take the historical branch")
 
     prepared = prepare_historical_envelope(payload, requested_mode="recorded_full_resume", validate_legacy=forbidden_legacy)
     decoded = decode_historical_envelope(encode_historical_envelope(prepared))
     retained = decoded.available_learned_state
     independent(retained, payload)
     assert decoded.policy.active_retained_transitions == 2
     rig.bank.install_restore(prepared=prepare(rig, retained["pw06_test_owned_bank"], "live_episode", None))
     same(rig.bank.checkpoint_state(), state)
     rig.event(6, IDS)
+
+
+@pytest.mark.parametrize("mode", ("live_episode", "completed_boundary"))
+def test_batch_zero_current_bank_resume(compiled, mode):
+    """Actual batch zero is distinct from each world's positive first sequence."""
+    source = Rig(compiled, "count_based", "per_world", IDS)
+    source.retained_batches = (0,)
+    source.begin(0)
+    assert source.accepted.batch_episode == 0
+    assert tuple(source.accepted.world_episode_seqs) == (1, 1)
+    source.actual_step()
+    source.train()
+    world_state = None
+    if mode == "completed_boundary":
+        world_state, _ = source.complete()
+        assert world_state["completed_boundary_key"] == 0 and world_state["next_batch_episode"] == 1
+    saved = source.bank.checkpoint_state()
+    destination = Rig(compiled, "count_based", "per_world", IDS[::-1])
+    destination.retained_batches = (0,)
+    parent = None
+    if mode == "live_episode":
+        destination.begin(0)
+    else:
+        parent = Correlation(destination, world_state)
+    before_rng = ambient()
+    prepared = prepare(destination, saved, mode, parent)
+    same(ambient(), before_rng)
+    destination.bank.install_restore(prepared=prepared)
+    restored = destination.bank.checkpoint_state()
+    for world in IDS:
+        independent(by_id(saved)[world], by_id(restored)[world])
+    if parent is not None:
+        same(restored["completion"], saved["completion"])
+        assert restored["completion"]["boundary_key"] == 0
+        assert "prepared_dispositions" not in destination.issued and "dispositions" not in destination.issued
+        parent.install_env()
+        destination.begin(1)
+        source.begin(1)
+        assert tuple(destination.accepted.world_episode_seqs) == (2, 2)
+    else:
+        assert restored["dispatch_identity"]["batch_episode"] == 0
+    destination.event(6, IDS)
+    source.event(6, IDS)
+    for world in IDS:
+        same(by_id(destination.bank.checkpoint_state())[world], by_id(source.bank.checkpoint_state())[world])
+
+
+@pytest.mark.parametrize("retained_view", (0, -1), ids=("first_callback", "final_callback"))
+def test_parent_retained_callback_view_cannot_mutate_prepared_history(compiled, retained_view):
+    source = Rig(compiled, "count_based", "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    world_state, _ = source.complete()
+    saved = source.bank.checkpoint_state()
+    expected = deepcopy(saved)
+    destination = Rig(compiled, "count_based", "per_world", IDS[::-1])
+    parent = Correlation(destination, world_state)
+    retained = []
+
+    def validate(*, prepared, curiosity_state):
+        parent.validate(prepared=prepared, curiosity_state=curiosity_state)
+        retained.append(curiosity_state)
+
+    prepared = destination.bank.prepare_restore(
+        state=saved,
+        mode="completed_boundary",
+        accepted=None,
+        parent_restore=parent.prepared,
+        validate_parent_restore=validate,
+    )
+    assert len(retained) >= 2 and destination.env.world_phase == "fresh-bound"
+    view = retained[retained_view]
+    view["completion"]["original_accepted_identity"]["world_ids"].reverse()
+    view["completion"]["original_accepted_identity"]["batch_episode"] = 41
+    view["completion"]["outcomes"][0]["outcome"]["final_observation"].fill_(712.0)
+    view["step"]["original_binding"]["world_ids"].reverse()
+    view["step"]["stamp"]["eligible_seqs"].fill_(713)
+    view["step"]["context"]["predecessor"].fill_(714.0)
+    same(saved, expected)
+    destination.bank.install_restore(prepared=prepared)
+    restored = destination.bank.checkpoint_state()
+    independent(restored["completion"], expected["completion"])
+    independent(restored["step"], expected["step"])
+    for world in IDS:
+        independent(by_id(restored)[world], by_id(expected)[world])
+    assert restored["dispatch_identity"] is None
+    assert "prepared_dispositions" not in destination.issued and "dispositions" not in destination.issued
+    with pytest.raises(REFUSAL):
+        destination.bank.commit_completion(prepared=source.source_prepared)
+    parent.install_env()
+    destination.begin(2)
+    assert tuple(destination.accepted.world_episode_seqs) == (2, 2)
+    destination.event(6, IDS)
