Previousreviewed2f5a63a58a728af624be0262a22d9fdd6ac48833
Fixed5028604b97fa241f00e4bae758125b4aeb2e8755
Onlyquarantinefixture changed, ENVproductionhashunchanged; same4whole3841cap4450.
diff --git a/tests/test_townlet/regressions/bac/test_env_accepted_auth.py b/tests/test_townlet/regressions/bac/test_env_accepted_auth.py
index e001cd40..230a9105 100644
--- a/tests/test_townlet/regressions/bac/test_env_accepted_auth.py
+++ b/tests/test_townlet/regressions/bac/test_env_accepted_auth.py
@@ -35,16 +35,35 @@ def _snapshot(env):
     return {
         "env": _state(env),
         "semantic_identity": env.semantic_execution_identity,
         "python_rng": random.getstate(),
         "numpy_rng": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
     }
 
 
+def _quarantined_snapshot(env):
+    """Observable witnesses; quarantine deliberately forbids native VFS export."""
+    numpy_state = np.random.get_state()
+    return {
+        "phase": env.world_phase,
+        "ids": env.world_ids,
+        "cursors": dict(env.accepted_episode_seqs),
+        "positions": env.positions.clone(),
+        "meters": env.meters.clone(),
+        "dones": env.dones.clone(),
+        "steps": env.step_counts.clone(),
+        "tick": env.global_tick,
+        "semantic_identity": env.semantic_execution_identity,
+        "torch_rng": torch.get_rng_state().clone(),
+        "python_rng": random.getstate(),
+        "numpy_rng": (numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
+    }
+
+
 def _validator(env):
     method = getattr(env, "validate_accepted_episode", None)
     assert callable(method), "actual ENV must expose public validate_accepted_episode"
     return method
 
 
 def _pure_validation(env, accepted):
     method = _validator(env)
@@ -225,15 +244,27 @@ def test_identity_authentication_does_not_activate_or_release_phase_permissions(
     _pure_validation(run.env, accepted)
 
 
 def test_identity_authentication_keeps_quarantine_and_physics_refusal(compiled):
     run = _Run(_env(compiled))
     accepted = run.reset(1)[1].accepted
     run.env.abandon_episode(accepted=accepted, reason="runtime_failure")
     assert run.env.world_phase == "quarantined"
-    _pure_validation(run.env, accepted)
-    before = _snapshot(run.env)
+    method = _validator(run.env)
+    before = _quarantined_snapshot(run.env)
+    for _ in range(2):
+        with pytest.raises(ValueError):
+            run.env.vfs_random_state()
+        with pytest.raises(ValueError):
+            run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
+        with pytest.raises(ValueError):
+            run.initial()
+        _same(before, _quarantined_snapshot(run.env))
+        assert method(accepted=accepted) is None
+        _same(before, _quarantined_snapshot(run.env))
+    with pytest.raises(ValueError):
+        run.env.vfs_random_state()
     with pytest.raises(ValueError):
         run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
     with pytest.raises(ValueError):
         run.initial()
-    _same(before, _snapshot(run.env))
+    _same(before, _quarantined_snapshot(run.env))
