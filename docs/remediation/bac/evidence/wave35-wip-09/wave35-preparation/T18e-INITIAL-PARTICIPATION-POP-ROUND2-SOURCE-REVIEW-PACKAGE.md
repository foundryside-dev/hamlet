 src/townlet/population/vectorized.py               | 46 ++++++++++++++++++----
 .../bac/test_initial_participation_population.py   | 43 ++++++++++++++++++--
 2 files changed, 79 insertions(+), 10 deletions(-)
diff --git a/src/townlet/population/vectorized.py b/src/townlet/population/vectorized.py
index 0028be1b..e0c6d486 100644
--- a/src/townlet/population/vectorized.py
+++ b/src/townlet/population/vectorized.py
@@ -908,23 +908,23 @@ class VectorizedPopulation(PopulationManager):
         decision, prior = self._initial_decision, self._prior_reading
         if (
             decision is None
             or prior is None
             or self._accepted is not decision.accepted
             or self._reset_record is not decision.reset
             or prior.accepted is not decision.accepted
             or prior.vector_tick != self.total_steps
             or prior.action_masks is None
         ):
-            error = RuntimeError("Owned episode lacks its genuine sealed population reading")
-            self._quarantine_participation(error)
-            raise error
+            missing = RuntimeError("Owned episode lacks its genuine sealed population reading")
+            self._quarantine_participation(missing)
+            raise missing
         retired_rows = torch.nonzero(decision.retired, as_tuple=False).flatten().tolist()
         healthy = (
             self._parent_reading_matches(prior)
             and self._same_reading(self.env.dones, prior.env_dones)
             and self._same_reading(self.env.step_counts, prior.env_counts)
             and all(
                 bool(self.episode_completed[row])
                 and int(self.episode_step_counts[row]) == 0
                 and self.episode_completions[row] is None
                 and row not in self._episode_participants
@@ -965,22 +965,21 @@ class VectorizedPopulation(PopulationManager):
             if self.env.world_phase == "quarantined":
                 self._failed_step, self._activation = True, None
             raise
         self._check_owned_state()
         return prior
 
     def _begin_selection(self) -> _SelectionFrame:
         self._require_operation_idle()
         if self._failed_step or self._pending_batch_commit is not None or self._vector_steps or self._owned_reset_pending:
             raise RuntimeError("Pending or failed population work cannot select actions")
-        owned = self._accepted is not None or self._initial_decision is not None or self._reset_record is not None
-        if owned:
+        if self._accepted is not None or self._initial_decision is not None or self._reset_record is not None:
             self._check_owned_state()
         frame = _SelectionFrame(
             self._accepted,
             self._reset_record,
             self._initial_decision,
             self._prior_reading,
             self._checkpoint_revision,
             self.current_obs.detach().clone(),
             self.episode_completed.detach().clone(),
             self.episode_step_counts.detach().clone(),
@@ -1015,20 +1014,28 @@ class VectorizedPopulation(PopulationManager):
         )
 
     def _revalidate_selection(self, frame: _SelectionFrame) -> None:
         if not self._selection_changed(frame) and frame.decision is not None:
             self._validate_owned_reading()
         if self._selection_changed(frame):
             error = ValueError("Selection callback changed retained population custody")
             self._quarantine_participation(error)
             raise error
 
+    def _check_selection_exception(self, frame: _SelectionFrame, error: Exception) -> None:
+        try:
+            self._revalidate_selection(frame)
+        except Exception as invalid:
+            error.add_note(f"Selection failure could not certify retained owner state: {invalid!r}")
+            if not self._failed_step:
+                self._quarantine_participation(error)
+
     def _prepare_initial_participation(self, work: _InitialReset) -> None:
         if self._initial_reset is not work or self._checkpoint_revision != work.revision:
             raise RuntimeError("Stale private reset preparation")
         work.intent = self._population_issuer.issue(
             kind="initial_participation_intent",
             payload=dict(
                 accepted=work.record.accepted,
                 world_ids=work.record.accepted.world_ids,
                 retired_world_ids=work.retired_world_ids,
                 population_revision=work.revision,
@@ -1194,27 +1201,44 @@ class VectorizedPopulation(PopulationManager):
             self._prepare_initial_participation(work)
             self._publish_initial_participation(work)
             activation = self._population_issuer.issue(kind="activation", payload={"accepted": record.accepted})
             if (
                 work.candidate is None
                 or self._prior_reading is not work.candidate
                 or self._initial_decision is not work.decision
                 or self._reset_record is not record
                 or self._checkpoint_revision != work.next_revision
                 or self._failed_step
+                or self._initial_reset is not None
+                or self._reset_stage != "finalizing"
+                or not self._step_active
                 or not self._parent_reading_matches(work.candidate)
             ):
                 raise ValueError("Activation finalization changed the paired population publication")
             assert work.decision is not None
             self.env.validate_initial_participation_reading(
                 accepted=record.accepted, participation=work.decision.participation, predecessor=work.candidate.observation
             )
+            if (
+                work.candidate is None
+                or work.decision is None
+                or self._prior_reading is not work.candidate
+                or self._initial_decision is not work.decision
+                or self._reset_record is not record
+                or self._checkpoint_revision != work.next_revision
+                or self._failed_step
+                or self._initial_reset is not None
+                or self._reset_stage != "finalizing"
+                or not self._step_active
+                or not self._parent_reading_matches(work.candidate)
+            ):
+                raise ValueError("Final activation reading changed retained population publication")
             self._accepted, self._activation = record.accepted, activation
             self._reset_stage = "completed"
             return record, activation
         except Exception as error:
             self._reset_stage, self._failed_step, self._activation = "failed", True, None
             if record is not None:
                 try:
                     self.env.abandon_episode(accepted=record.accepted, reason="runtime_failure")
                 except Exception as quarantine_error:
                     error.add_note(f"Reset quarantine failed: {quarantine_error!r}")
@@ -2003,20 +2027,23 @@ class VectorizedPopulation(PopulationManager):
         try:
             with torch.no_grad():
                 eligible = ~env.dones & ~self.episode_completed
                 q_values = self._rollout_q(eligible)
                 action_masks = env.get_action_masks()
                 self._revalidate_selection(frame)
                 self._validate_selection(q_values, action_masks, eligible)
                 actions = q_values.argmax(dim=1)
                 actions[eligible] = q_values[eligible].masked_fill(~action_masks[eligible], -torch.inf).argmax(dim=1)
                 return actions
+        except Exception as error:
+            self._check_selection_exception(frame, error)
+            raise
         finally:
             if self._selection_frame is frame:
                 self._selection_frame = None
 
     def select_epsilon_greedy_actions(self, env: VectorizedHamletEnv, epsilon: float) -> torch.Tensor:
         """
         Select epsilon-greedy actions with action masking.
 
         With probability epsilon, select random valid action.
         With probability (1-epsilon), select greedy action.
@@ -2035,20 +2062,23 @@ class VectorizedPopulation(PopulationManager):
                 q_values = self._rollout_q(eligible)
                 action_masks = env.get_action_masks()
                 self._revalidate_selection(frame)
                 epsilons = torch.full((self.num_agents,), epsilon, device=self.device, dtype=torch.float32)
                 return epsilon_greedy_action_selection_eligible(
                     q_values=q_values,
                     epsilons=epsilons,
                     action_masks=action_masks,
                     eligible=eligible,
                 )
+        except Exception as error:
+            self._check_selection_exception(frame, error)
+            raise
         finally:
             if self._selection_frame is frame:
                 self._selection_frame = None
 
     def step_population(self, envs: VectorizedHamletEnv) -> BatchedAgentState:
         """Execute once; retain truthful progress and quarantine irreversible failures."""
         self._require_operation_idle()
         if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
             raise RuntimeError("Reentrant or quarantined population step")
         if envs is not self.env or self._accepted is None or self._clock_ledger_restore_unavailable:
@@ -2487,26 +2517,28 @@ class VectorizedPopulation(PopulationManager):
             "training_step_counter": self.training_step_counter,
             # All buffer types implement serialize(), but mypy doesn't infer it for unions.
             "replay_buffer": self.replay_buffer.serialize(),  # type: ignore[union-attr]
         }
 
     def _has_failed_step_diagnostic(self) -> bool:
         progress = self._vector_step_progress
         if not self._failed_step or not self._vector_steps or progress is None:
             return False
         record = next(iter(self._vector_steps.values()))
-        return (
+        if (
             progress["status"] == "failed"
             and progress["last_reached_stage"] == self._vector_stage
             and progress["vector_tick"] == record.vector_tick
             and progress["accepted_identity"] == self._accepted_identity(record.accepted)
-        )
+        ):
+            return True
+        return False
 
     @staticmethod
     def _require_exact_mapping(label: str, incoming_state: object, expected_keys: frozenset[str]) -> Mapping[str, object]:
         if not isinstance(incoming_state, Mapping):
             raise ValueError(f"Population checkpoint {label} must be a mapping; got {type(incoming_state).__name__}.")
         incoming_keys = set(incoming_state)
         if incoming_keys != expected_keys:
             missing = sorted(expected_keys - incoming_keys)
             unknown = sorted(incoming_keys - expected_keys)
             raise ValueError(f"Population checkpoint {label} key mismatch: missing={missing}, unknown={unknown}.")
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
# CPP cumulative Round2 actual repairs

BaseR31 3db908c4915c0b3f6666064bdc74a80dfbadb8a6 -> R33f0f1b79b7df95402269d8e306330f6b38a233a27
R32fouractualnegativewitnessesbeforeproductionfix; currentPOP31636c4f7ca0/focused7739186,parent7916cea unchanged.

