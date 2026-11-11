 .../bac/test_initial_participation_population.py   | 90 ++++++++++++++++++----
 1 file changed, 74 insertions(+), 16 deletions(-)
diff --git a/tests/test_townlet/regressions/bac/test_initial_participation_population.py b/tests/test_townlet/regressions/bac/test_initial_participation_population.py
index e3fd53c6..aa7ddc01 100644
--- a/tests/test_townlet/regressions/bac/test_initial_participation_population.py
+++ b/tests/test_townlet/regressions/bac/test_initial_participation_population.py
@@ -94,26 +94,28 @@ def reading(rig: ParentFixture) -> dict[str, Any]:
             replay=pop.replay_buffer.serialize(),
             curriculum=pop.curriculum.checkpoint_state(),
             runtime=rig.runtime.checkpoint_state(),
             torch_rng=torch.get_rng_state(),
             numpy_rng=(numpy_state[0], numpy_state[1].tolist(), *numpy_state[2:]),
             python_rng=random.getstate(),
         )
     )
 
 
-def capture_participation(monkeypatch: Any, rig: ParentFixture) -> list[Any]:
+def capture_participation(monkeypatch: Any, rig: ParentFixture, ready: list[Any] | None = None) -> list[Any]:
     committed, original = [], rig.env.commit_initial_participation
 
     def commit(**kwargs: Any) -> Any:
         result = original(**kwargs)
         committed.append(result)
+        if ready is not None:
+            ready.append(kwargs["population_ready"])
         return result
 
     monkeypatch.setattr(rig.env, "commit_initial_participation", commit)
     return committed
 
 
 def prepare_close(rig: ParentFixture) -> tuple[Any, Any, Any, tuple[Any, ...], tuple[Any, ...]]:
     """Actual positive events and sink preparations; no synthetic nonparticipant event."""
     pop, accepted = rig.population, rig.record.accepted
     for lane in range(len(IDS)):
@@ -217,57 +219,73 @@ def test_decision_preserves_state_and_equal_reset_cannot_reopen_it(compiled: Any
     prepare = rig.env.prepare_initial_participation
 
     def observe(**kwargs: Any) -> Any:
         before.update(reading(rig))
         result = prepare(**kwargs)
         prepared.append(result)
         assert not bool(rig.env.dones.any())
         return result
 
     monkeypatch.setattr(rig.env, "prepare_initial_participation", observe)
-    committed = capture_participation(monkeypatch, rig)
+    ready: list[Any] = []
+    committed = capture_participation(monkeypatch, rig, ready)
     reservation, activation = begin(rig, active=False)
     equal(reading(rig), before)
     equal(prepared[0].action_masks[1:], torch.zeros((7, rig.env.action_dim), dtype=torch.bool))
     damaged = committed[0].observation
     damaged.add_(50)
     equal(rig.population.current_obs, before["observation"])
     masks = committed[0].action_masks
     masks.fill_(True)
     assert not bool(committed[0].action_masks[1:].any())
+    with pytest.raises(REFUSAL):
+        rig.env.commit_initial_participation(prepared=prepared[0], population_ready=ready[0])
     record, retry = rig.population.reset(reservation=reservation, retired_world_ids=RETIRED)
     assert record is rig.record and retry is activation and len(committed) == 1
     with pytest.raises(REFUSAL):
         rig.population.reset(reservation=reservation, retired_world_ids=())
     equal(rig.env.dones, ~LIVE)
     activate(rig, activation)
     with pytest.raises(REFUSAL):
         rig.env.commit_initial_participation(prepared=prepared[0], population_ready=activation)
 
 
 def test_actual_a_learning_replay_private_b_and_next_cycle(compiled: Any, monkeypatch: Any) -> None:
     rig = make_parent(compiled, "rnd", "per_world")
     begin(rig)
     calls = observe_runtime(monkeypatch, rig)
     initial = rig.runtime.checkpoint_state()
     b_before = next(world for world in initial["bank"]["worlds"] if world["world_id"] == IDS[1])
     q_before = copy.deepcopy(rig.population.q_network.state_dict())
-    selected, original_select = [], rig.runtime.select_actions
+    selected, expected, original_select = [], [], rig.runtime.select_actions
 
     def selector(values: Any, state: Any, masks: Any) -> Any:
         selected.append((values.shape, state.observations.shape, masks.shape))
         return original_select(values, state, masks)
 
     monkeypatch.setattr(rig.runtime, "select_actions", selector)
     for tick in (1, 2):
         previous = rig.population.current_obs.clone()
         state = rig.population.step_population(rig.env)
+        expected.append(
+            copy.deepcopy(
+                dict(
+                    observations=previous[0],
+                    actions=state.actions[0],
+                    next_observations=state.observations[0],
+                    dones=state.dones[0],
+                    rewards=state.rewards[0],
+                    next_action_masks=state.info["successor_action_masks"][0],
+                    **{f"rewards_{name}": state.info["reward_components"][name][0] for name in ("extrinsic", "intrinsic", "shaping")},
+                )
+            )
+        )
         handoff = state.info["intrinsic_transition"]
         equal(handoff.context.predecessor, previous)
         equal(handoff.context.active_on_entry, LIVE)
         equal(handoff.stamp.eligible, LIVE)
         assert handoff.context.vector_tick == tick
         assert rig.population.replay_buffer.retained_transitions == tick
         assert len(calls["reward"]) == len(calls["service"]) == tick
         reward_args, _ = calls["reward"][-1]
         service_args, _ = calls["service"][-1]
         for args in (reward_args, service_args):
@@ -277,20 +295,26 @@ def test_actual_a_learning_replay_private_b_and_next_cycle(compiled: Any, monkey
             equal(state.info["reward_components"][component][1:], torch.zeros(7))
     assert selected == [((1, rig.env.action_dim), (1, rig.env.observation_dim), (1, rig.env.action_dim))] * 2
     ledger = rig.population.clock_ledger
     assert ledger.vector_ticks == ledger.eligible_transitions == 2
     assert ledger.optimizer_updates == rig.population.training_step_counter == 1
     assert any(not torch.equal(value, q_before[key]) for key, value in rig.population.q_network.state_dict().items())
     batch = rig.population.replay_buffer.sample_batch(ReplayRequest(2, 1, 2, "uniform_without_replacement", "feedforward", "transition"))
     assert batch.observations.shape == (2, rig.env.observation_dim)
     assert batch.next_action_masks.shape == (2, rig.env.action_dim)
     assert bool(batch.rewards_extrinsic_present.all()) and bool(batch.rewards_intrinsic_present.all())
+    assert set(batch.unit_ids.tolist()) == {0, 1}
+    for field in expected[0]:
+        equal(getattr(batch, field), torch.stack([row[field] for row in expected])[batch.unit_ids])
+    for name in ("extrinsic", "intrinsic", "shaping"):
+        assert bool(getattr(batch, f"rewards_{name}_present").all())
+    assert bool(batch.legality_recorded.all()) and bool(batch.loss_mask.all())
     after = rig.runtime.checkpoint_state()
     b_after = next(world for world in after["bank"]["worlds"] if world["world_id"] == IDS[1])
     equal(b_after["backend"], b_before["backend"])
     equal(b_after["gradients"], b_before["gradients"])
     assert b_after["cursor"]["eligible_seq"] == 0 and b_after["cursor"]["participated"] is False
     equal(rig.population.episode_step_counts, torch.tensor([2, 0, 0, 0, 0, 0, 0, 0]))
     assert rig.population.episode_completions[1] is None
     assert not bool(rig.population._episode_entropy_present[1:].any())
     equal(rig.population._episode_reward_totals[1:], torch.zeros((7, 4), dtype=torch.float64))
     prepared = prepare_close(rig)
@@ -355,69 +379,103 @@ def test_unowned_inference_preserves_legal_actions_q_display_and_lifetime(compil
         assert actions.shape == (len(IDS),) and actions.dtype == torch.int64
         assert bool(masks.gather(1, actions[:, None]).all())
         assert rig.population.last_selected_q_values.shape == masks.shape
     assert rig.population.max_episodes is None and rig.population.max_steps_per_episode is None
     assert (rig.population.total_steps, asdict(rig.population.clock_ledger), rig.population.replay_buffer.retained_transitions) == before
     assert rig.env.world_phase == "active-awaiting-activation"
 
 
 @pytest.mark.parametrize("owned", (False, True))
 @pytest.mark.parametrize("kind", ("greedy", "0.0", "1.0", "0.5"))
+@pytest.mark.parametrize("invalid", ("geometry", "empty"))
 def test_compatible_foreign_masks_keep_their_effect_without_changing_episode_authority(
-    compiled: Any, monkeypatch: Any, owned: bool, kind: str
+    compiled: Any, monkeypatch: Any, owned: bool, kind: str, invalid: str
 ) -> None:
     rig, foreign = make_parent(compiled) if owned else unowned(compiled), unowned(compiled)
     if owned:
         begin(rig)
     masks = foreign.env.get_action_masks()
-    chosen = masks.long().argmax(dim=1)
+    own = rig.population.select_greedy_actions(rig.env)
+    alternatives = masks.clone().scatter_(1, own[:, None], False)
+    assert bool(alternatives.any(dim=1).all())
+    chosen = alternatives.long().argmax(dim=1)
     forced = torch.zeros_like(masks).scatter_(1, chosen[:, None], True)
     monkeypatch.setattr(foreign.env, "get_action_masks", lambda: forced.clone())
     actions = select(rig.population, foreign.env, kind)
     eligible = LIVE if owned else torch.ones(len(IDS), dtype=torch.bool)
+    assert bool((chosen[eligible] != own[eligible]).all())
     equal(actions[eligible], chosen[eligible])
     if owned:
         equal(rig.population.episode_completed, ~LIVE)
     assert rig.population.total_steps == 0
-    bad = forced[:-1]
+    bad = forced[:-1] if invalid == "geometry" else torch.zeros_like(forced)
     monkeypatch.setattr(foreign.env, "get_action_masks", lambda: bad)
-    with pytest.raises((ValueError, RuntimeError, IndexError)):
-        select(rig.population, foreign.env, kind)
-    monkeypatch.setattr(foreign.env, "get_action_masks", lambda: torch.zeros_like(forced))
-    with pytest.raises(REFUSAL):
+    errors = (ValueError, RuntimeError, IndexError) if invalid == "geometry" else REFUSAL
+    with pytest.raises(errors):
         select(rig.population, foreign.env, kind)
 
 
 @pytest.mark.parametrize("kind", ("greedy", "0.5"))
 def test_owned_reading_survives_healthy_phases_without_granting_physics(compiled: Any, monkeypatch: Any, kind: str) -> None:
     rig = make_parent(compiled)
     committed = capture_participation(monkeypatch, rig)
+
+    def refuse_physics() -> None:
+        candidate = rig.candidate()
+        before = rig.population.total_steps, rig.env.global_tick
+        with monkeypatch.context() as observers:
+            calls = forbid_effects(observers, rig)
+            operations = (
+                lambda: rig.env.validate_initial_participation(
+                    accepted=rig.record.accepted, participation=committed[0], predecessor=rig.population.current_obs
+                ),
+                lambda: rig.population.step_population(rig.env),
+                lambda: rig.population.prepare_vector_step(**candidate),
+            )
+            for operation in operations:
+                rng = torch.get_rng_state().clone()
+                with pytest.raises(REFUSAL):
+                    operation()
+                assert calls == []
+                equal(torch.get_rng_state(), rng)
+                assert (rig.population.total_steps, rig.env.global_tick) == before
+
     _, activation = begin(rig, active=False)
     select(rig.population, rig.env, kind)
+    refuse_physics()
     activate(rig, activation)
     rig.population.step_population(rig.env)
     select(rig.population, rig.env, kind)
     prepared = prepare_close(rig)
     close(rig, prepared, release=False)
     assert rig.env.world_phase == "closed-awaiting-release"
     for install in (False, True):
         if install:
             rig.env.install_boundary_release(rig.release)
             assert rig.env.world_phase == "released-completed"
         actions = select(rig.population, rig.env, kind)
         assert actions.shape == (len(IDS),)
-        with pytest.raises(REFUSAL):
-            rig.env.validate_initial_participation(
-                accepted=rig.record.accepted, participation=committed[0], predecessor=rig.population.current_obs
-            )
-        with pytest.raises(REFUSAL):
-            rig.population.step_population(rig.env)
+        refuse_physics()
+    assert rig.population.total_steps == rig.env.global_tick == 1
+
+
+def test_pending_genuine_step_blocks_the_completion_needed_to_change_reading_phase(compiled: Any) -> None:
+    rig = make_parent(compiled)
+    begin(rig)
+    rig.population.step_population(rig.env)
+    candidate = rig.candidate()
+    prepared = rig.population.prepare_vector_step(**candidate)
+    with pytest.raises(REFUSAL):
+        rig.population.flush_episode(0, reason="budget")
+    assert rig.population.episode_completions[0] is None
+    assert not bool(rig.population.episode_completed[0]) and rig.env.world_phase == "active"
+    assert rig.population.claim_vector_step(prepared=prepared, **candidate) == 2
     assert rig.population.total_steps == rig.env.global_tick == 1
 
 
 @pytest.mark.parametrize("where", ("reset", "finalization", "prepared_step", "close_frozen", "failed"))
 def test_pending_and_failed_custody_cannot_use_unowned_inference(compiled: Any, monkeypatch: Any, where: str) -> None:
     rig, foreign = make_parent(compiled), unowned(compiled)
     hits: list[str] = []
 
     def refuse_selection() -> None:
         previous_q = rig.population.last_selected_q_values
# CPP authored assertion repair Round1

Base candidate tree8d909f5d7c2b6f94e8b13eb62eb65b737e1101d5/newtest678bae10c26.
New sealed test736 SHA256bfa42a957753efea826ec37eae904be7c199d503ef9295bd214d65f13afa841a. Four other owned bodies unchanged. ENV query test undergoing separate unrelated repair; no final global-tree claim.

