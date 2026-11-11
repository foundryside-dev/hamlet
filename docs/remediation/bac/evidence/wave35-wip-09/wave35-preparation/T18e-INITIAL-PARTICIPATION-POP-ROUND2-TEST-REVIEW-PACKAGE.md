diff --git a/tests/test_townlet/regressions/bac/test_initial_participation_population.py b/tests/test_townlet/regressions/bac/test_initial_participation_population.py
index aa7ddc01..aca1d453 100644
--- a/tests/test_townlet/regressions/bac/test_initial_participation_population.py
+++ b/tests/test_townlet/regressions/bac/test_initial_participation_population.py
@@ -537,43 +537,80 @@ def test_postpublication_activation_failure_quarantines_without_reusable_reset(c
     monkeypatch.setattr(WorldReceiptIssuer, "issue", fail_activation)
     with pytest.raises(MemoryError, match="after paired publication"):
         rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
     assert rig.env.world_phase == "quarantined"
     with pytest.raises(REFUSAL):
         rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
     assert len(committed) == 1 and rig.population.total_steps == 0
 
 
 @pytest.mark.parametrize("kind", ("greedy", "0.5"))
-def test_mutating_foreign_mask_callback_stops_selection_after_its_real_q_effects(compiled: Any, monkeypatch: Any, kind: str) -> None:
+@pytest.mark.parametrize("raises", (False, True))
+def test_mutating_foreign_mask_callback_stops_selection_after_its_real_q_effects(
+    compiled: Any, monkeypatch: Any, kind: str, raises: bool
+) -> None:
     rig, foreign = make_parent(compiled), unowned(compiled)
     begin(rig)
-    masks, q_calls = foreign.env.get_action_masks(), []
+    mask_read, q_calls = foreign.env.get_action_masks, []
+    fault = ValueError("foreign mask callback failed after mutation")
     rollout = rig.population._rollout_q
 
     def observe(eligible: Any) -> Any:
         q_calls.append(None)
         return rollout(eligible)
 
     def mutate() -> Any:
+        masks = mask_read()
         rig.population.current_obs.add_(1)
+        if raises:
+            raise fault
         return masks
 
     monkeypatch.setattr(rig.population, "_rollout_q", observe)
     monkeypatch.setattr(foreign.env, "get_action_masks", mutate)
     rng = torch.get_rng_state().clone()
-    with pytest.raises(REFUSAL):
+    with pytest.raises(REFUSAL) as error:
         select(rig.population, foreign.env, kind)
+    if raises:
+        assert error.value is fault
     assert q_calls == [None]
     equal(torch.get_rng_state(), rng)
     assert rig.population.total_steps == 0
     assert rig.env.world_phase == "quarantined"
+    assert rig.population._failed_step and rig.population._activation is None
+    with pytest.raises(REFUSAL):
+        rig.population.get_checkpoint_state()
+
+
+@pytest.mark.parametrize("damage", ("observation", "status"))
+def test_finalization_read_cannot_publish_activation_after_mutating_pop_state(compiled: Any, monkeypatch: Any, damage: str) -> None:
+    rig = make_parent(compiled)
+    reservation = reserve(rig)
+    reading, visits = rig.env.validate_initial_participation_reading, []
+
+    def mutate(**kwargs: Any) -> Any:
+        result = reading(**kwargs)
+        visits.append(None)
+        if damage == "observation":
+            rig.population.current_obs.add_(1)
+        else:
+            rig.population.episode_completed[1] = False
+        return result
+
+    monkeypatch.setattr(rig.env, "validate_initial_participation_reading", mutate)
+    with pytest.raises(REFUSAL):
+        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
+    assert visits == [None] and rig.env.world_phase == "quarantined"
+    assert rig.population._failed_step and rig.population._activation is None
+    with pytest.raises(REFUSAL):
+        rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
+    assert visits == [None] and rig.population.total_steps == rig.env.global_tick == 0
 
 
 def test_current_initial_boundary_restore_does_not_import_live_decision_authority(compiled: Any) -> None:
     source, target = make_parent(compiled), make_parent(compiled)
     state = copy.deepcopy(source.population.get_checkpoint_state())
     target.population.load_checkpoint_state(state)
     begin(target)
     equal(target.env.dones, ~LIVE)
     with pytest.raises(REFUSAL):
         target.population.load_checkpoint_state(state)
# CPP Round2 causal regressions before source repairs

BaseR31 3db908c4915c0b3f6666064bdc74a80dfbadb8a6 -> R3286fae3c974e87e1ccbfa4d6f15fe695c851c767d
Source3131244e/parent7916cea unchanged; focused7739186a953.

