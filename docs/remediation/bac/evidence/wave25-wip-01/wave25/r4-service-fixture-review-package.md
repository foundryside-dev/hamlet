# Single causal service fixture repair
diff --git a/tests/test_townlet/regressions/bac/test_pw_private_bank.py b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
index 7f1f30a0..7be710f7 100644
--- a/tests/test_townlet/regressions/bac/test_pw_private_bank.py
+++ b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
@@ -1149,27 +1149,38 @@ def test_quarantine_refuses_cached_completion_success(harness_factory: Any) -> N
     receipt = h.bank.commit_completion(prepared=prepared)
     assert h.bank.commit_completion(prepared=prepared) is receipt
     h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
     with pytest.raises((RuntimeError, ValueError)):
         h.bank.commit_completion(prepared=prepared)
 
 
 @pytest.mark.parametrize("phase", ("reward", "service"))
 def test_post_provider_publication_failure_quarantines_real_effect(harness_factory: Any, monkeypatch: Any, phase: str) -> None:
     h = harness_factory("rnd")
-    for tick in (1, 2):
+    prefix = (1, 2, 3) if phase == "service" else (1, 2)
+    for tick in prefix:
         _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
-    context = _context(3, (True, True), 3, 0.0)
-    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=3)
+    next_tick = len(prefix) + 1
+    context = _context(next_tick, (True, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(
+        accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=next_tick
+    )
     if phase == "service":
         h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
     before = h.bank._owners["world0"].snapshot()["backend"]
+    if phase == "service":
+        # Actual B2 cadence: admissions1/2 already produced update1; admission3
+        # leaves one row. Admission4 must consume that tail in update2.
+        service = before["predictor_service"]
+        assert service["optimizer_updates"] == 1
+        assert service["pending_observations"].shape[0] == 1
+        assert h.policy.predictor_batch_size == 2
     calls: list[str] = []
 
     def publication_fault(*args: Any, **kwargs: Any) -> None:
         calls.append(phase)
         raise RuntimeError("injected post-provider publication allocation failure")
 
     module = importlib.import_module(BANK_MODULE)
     target = "CuriosityReward" if phase == "reward" else "WorldServiceReceipt"
     with monkeypatch.context() as patch:
         patch.setattr(module, target, publication_fault)
@@ -1178,20 +1189,23 @@ def test_post_provider_publication_failure_quarantines_real_effect(harness_facto
                 h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
             else:
                 h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted)
     assert calls == [phase]
     after = h.bank._owners["world0"].snapshot()["backend"]
     if phase == "reward":
         assert after["reward_rms_count"] > before["reward_rms_count"]
     else:
         assert after["predictor_service"]["optimizer_updates"] > before["predictor_service"]["optimizer_updates"]
         assert any(not torch.equal(a, b) for a, b in zip(_learned(before, "rnd"), _learned(after, "rnd"), strict=True))
+        old_moments, new_moments = before["optimizer"]["state"], after["optimizer"]["state"]
+        assert any(not torch.equal(old_moments[key]["exp_avg"], value["exp_avg"]) for key, value in new_moments.items())
+        assert any(bool(value["exp_avg"].ne(0).any()) for value in new_moments.values())
     for retry in (
         lambda: h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True),
         lambda: h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted),
     ):
         with pytest.raises((ValueError, RuntimeError), match="quarantin"):
             retry()
 
 
 def test_completion_receipt_failure_after_observation_tracks_revision(harness_factory: Any, monkeypatch: Any) -> None:
     h = harness_factory("adaptive_rnd")
