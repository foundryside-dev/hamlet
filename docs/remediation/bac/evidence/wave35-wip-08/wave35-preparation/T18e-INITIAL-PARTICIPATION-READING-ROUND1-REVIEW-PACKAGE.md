 .../bac/test_initial_participation_env.py          | 46 +++++++++++++++++++++-
 1 file changed, 45 insertions(+), 1 deletion(-)
diff --git a/tests/test_townlet/regressions/bac/test_initial_participation_env.py b/tests/test_townlet/regressions/bac/test_initial_participation_env.py
index 4aa49ce9..4661e682 100644
--- a/tests/test_townlet/regressions/bac/test_initial_participation_env.py
+++ b/tests/test_townlet/regressions/bac/test_initial_participation_env.py
@@ -110,20 +110,21 @@ class ComponentPopulation:
         self.curriculum = build_curriculum(
             training, curriculum_options=effective.options.curriculum, static_policy=effective.static_policy, device=self.device
         )
         self.curriculum.initialize_population(len(IDS))
         self.curriculum_issuer = WorldReceiptIssuer(owner=self.curriculum)
         policy = resolve_exploration_policy(
             drive_intrinsic=IntrinsicStrategyConfig(strategy="none", base_weight=0.0, apply_modifiers=[]),
             training=training,
             options=options,
         )
+        self.policy = policy
         descriptor = WorldCuriosityDescriptor.from_policy(
             policy,
             world_ids=IDS,
             observation_dim=self.env.observation_dim,
             action_dim=self.env.action_dim,
             training_seed=SEED,
         )
         self.reports: list[Any] = []
         self.bank: Any = None
         self.bank_issuer: Any = None
@@ -1063,39 +1064,68 @@ def reading_phase(compiled: Any, phase: str) -> ComponentPopulation:
         reward_extrinsic=float(info["reward_components"]["extrinsic"][0]),
         reward_intrinsic=float(info["reward_components"]["intrinsic"][0]),
         reward_shaping=float(info["reward_components"]["shaping"][0]),
         policy_entropy=0.0,  # The real component control always chooses WAIT, not a Q policy.
         world_id=IDS[0],
         world_episode_seq=rig.accepted.world_episode_seqs[0],
     )
     outcomes = (event,)
     content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
     key = rig.accepted.batch_episode
+    rig.completion_before = owned(rig.runtime.checkpoint_state())
     curriculum = rig.curriculum.prepare_episode_outcomes(outcomes)
     bank = rig.runtime.prepare_completion(
         accepted=rig.accepted, boundary_key=key, completion_content=content, outcomes=outcomes, participated_world_ids=(IDS[0],)
     )
     close = rig.env.prepare_episode_close(
         accepted=rig.accepted,
         boundary_key=key,
         completion_content=content,
         participated_world_ids=(IDS[0],),
         dispositions=bank.prepared_receipt,
     )
     rig.env.freeze_episode_close(close)
-    rig.close_context = (curriculum, bank, close)
+    rig.close_context = (curriculum, bank, close, outcomes, content, key)
     if phase == "boundary-pending":
         return rig
+    return finish_reading_close(rig, phase)
+
+
+def finish_reading_close(rig: ComponentPopulation, phase: str) -> ComponentPopulation:
+    curriculum, bank, close, outcomes, content, key = rig.close_context
     rig.curriculum.commit_prepared_episode_outcomes(curriculum)
     retirement = rig.runtime.commit_completion(prepared=bank)
     rig.completion_request = (rig.accepted, key, content)
     rig.runtime.commit_batch_episode(batch_episode=key, outcomes=outcomes)
+    original_before = rig.completion_before["selector"]["epsilon"]
+    expected_after = max(rig.policy.epsilon_end, original_before * rig.policy.epsilon_decay)
+    published = rig.runtime.checkpoint_state()  # BANK completion is committed; no pending export.
+    assert rig.runtime.epsilon == expected_after
+    equal(
+        published["selector"],
+        {
+            "epsilon": expected_after,
+            "epsilon_min": rig.policy.epsilon_end,
+            "epsilon_decay": rig.policy.epsilon_decay,
+        },
+    )
+    equal(
+        published["cadence"]["last_committed"],
+        {
+            "batch_episode": key,
+            "completion_content": content,
+            "epsilon_before": original_before,
+            "epsilon_after": expected_after,
+        },
+    )
+    rig.runtime.commit_batch_episode(batch_episode=key, outcomes=outcomes)  # Exact supported retry, not another completion.
+    equal(rig.runtime.checkpoint_state(), published)
     rig.committed_batches[key] = content
     rig.completed = torch.ones_like(rig.completed)  # Genuine declared component cap finalized A; B was already retired.
     rig.ledger = rig.ledger.advance(completed_batch_episodes=1)
     rig.current_epsilons = rig.runtime.epsilon_tensor(batch_size=len(IDS), device=rig.device)
     equal(rig.current_epsilons, torch.full((len(IDS),), rig.runtime.epsilon, dtype=torch.float32))
     closure = rig.env.close_episode(close, dispositions=retirement)
     assert dict(retirement.dispositions)[IDS[1]] == "retired_nonparticipating"
     if phase == "closed-awaiting-release":
         return rig
     fields = {"accepted": rig.accepted, "boundary_key": key, "completion_content": content}
@@ -1114,21 +1144,29 @@ def reading_phase(compiled: Any, phase: str) -> ComponentPopulation:
         },
     )
     rig.release = rig.authority.completed(closure=closure, effects=effects)
     rig.env.install_boundary_release(rig.release)
     assert phase == "released-completed"
     return rig
 
 
 @pytest.mark.parametrize("phase", ["active-awaiting-activation", "active", "closed-awaiting-release", "released-completed"])
 def test_reading_validator_preserves_each_genuine_healthy_phase(compiled: Any, monkeypatch: Any, phase: str) -> None:
+    claim, claim_calls = ComponentPopulation.claim_vector_step, []
+
+    def observed_claim(owner: ComponentPopulation, *, prepared: Any, **candidate: Any) -> int:
+        claim_calls.append(prepared)
+        return claim(owner, prepared=prepared, **candidate)
+
+    monkeypatch.setattr(ComponentPopulation, "claim_vector_step", observed_claim)
     rig = reading_phase(compiled, phase)
+    claim_calls.clear()  # Earned closed phases used their genuine claim before this reading boundary.
     assert rig.env.world_phase == phase
     components_before, runtime_before = component_state(rig), rig.runtime.checkpoint_state()
     before, revision = witness(rig), rig.env._world_revision
 
     def forbidden_mask(**kwargs: Any) -> Any:
         raise AssertionError("a pure reading must not recompute action masks")
 
     monkeypatch.setattr(rig.env.action_mask_builder, "build", forbidden_mask)
     rig.participation.observation.add_(100)
     rig.participation.action_masks.fill_(True)
@@ -1141,29 +1179,35 @@ def test_reading_validator_preserves_each_genuine_healthy_phase(compiled: Any, m
         )
     assert rig.env.world_phase == phase and rig.env._world_revision == revision
     assert_unchanged(rig, before)
     equal(component_state(rig), components_before)
     equal(rig.runtime.checkpoint_state(), runtime_before)
     if phase != "active":
         with pytest.raises(ValueError):
             rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
         with pytest.raises(ValueError):
             rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
+    assert claim_calls == []
 
 
 def test_frozen_close_refuses_reading_without_consuming_sink_handles(compiled: Any) -> None:
     rig = reading_phase(compiled, "boundary-pending")
+    original_context = rig.close_context
     before = witness(rig)
     with pytest.raises(ValueError):
         rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
     assert rig.env.world_phase == "boundary-pending"
     assert_unchanged(rig, before)
+    finish_reading_close(rig, "released-completed")
+    assert rig.close_context is original_context and rig.env.world_phase == "released-completed"
+    assert rig.ledger.completed_batch_episodes == 1
+    assert rig.committed_batches == {original_context[5]: original_context[4]}
 
 
 def test_new_genuine_reset_invalidates_prior_reading_identity(compiled: Any) -> None:
     rig = reading_phase(compiled, "released-completed")
     old_participation, old_accepted = rig.participation, rig.accepted
     reservation = rig.env.prepare_episode(batch_episode=rig.release.next_batch_episode, release=rig.release)
     reset = rig.env.reset(reservation=reservation)
     rig.reservation, rig.reset, rig.accepted, rig.current_obs = reservation, reset, reset.accepted, reset.observation
     rig.participation = rig.activation = None
     rig.retired = None
# ENV Q1 authored assertion repair Round1

Base candidate tree8d909f5d7c2b6f94e8b13eb62eb65b737e1101d5/test1197d47a9387.
New candidated5481fce58bf63de8071ba24ba26dc6dfe0b18ad/test1241 SHA2560a90bb7e57956ce714b8bc4f663cbdb3aa237448dd1437d733f98c04ec913f11. Four other owned bodies unchanged.

