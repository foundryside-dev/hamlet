# Owner-fixture actual delta ONLY R2 -> R3

 .../regressions/bac/test_world_episode_identity.py |  28 ++-
 .../unit/vfs/test_random_expressions.py            | 155 ++++++++++++---
 .../unit/vfs/test_verify_r3_repairs.py             | 218 ++++++++++++++++++---
 .../unit/vfs/test_vtc_bounds_clamps.py             |   6 +-
 4 files changed, 349 insertions(+), 58 deletions(-)

diff --git a/tests/test_townlet/regressions/bac/test_world_episode_identity.py b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
index 29b99211..d8da6c2b 100644
--- a/tests/test_townlet/regressions/bac/test_world_episode_identity.py
+++ b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
@@ -489,17 +489,24 @@ def test_participating_episode_cannot_claim_empty_abandon(compiled):
 
 
 def test_initial_snapshot_repeat_restore_and_first_real_reset(compiled):
     run = _Run(_env(compiled))
     before = _state(run.env)
     state = run.initial()
     _same(state, run.initial())
     _same(before, _state(run.env))
-    assert state["schema"] == "world-lifecycle-v3" and state["kind"] == "INITIAL"
+    assert state["schema"] == "world-lifecycle-v4" and state["kind"] == "INITIAL"
+    assert state["vfs_random_context"] == {
+        "schema": "vfs-world-random-v1",
+        "domain": "townlet.simulator.vfs.world-draw.v1",
+        "training_seed": SEED,
+        "world_ids": list(IDS),
+        "world_episode_seqs": [0, 0],
+    }
     assert state["accepted_bindings"] == []
     assert state["last_closed_episode"] is None and state["completed_boundary_key"] is None
     assert state["saved_lane_binding"] is None
     assert state["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
     restored = _restore(compiled, state, tuple(reversed(IDS)))
     assert restored.env.world_phase == "bootstrap-ready"
     assert restored.reset(1)[1].accepted.world_episode_seqs == (1, 1)
     with pytest.raises(ValueError):
@@ -530,16 +537,27 @@ def test_malformed_initial_restore_is_pure(compiled, field, value):
         target.env.prepare_world_restore(
             kind="INITIAL",
             state=state,
             world_roster=_roster(),
             destination_world_ids=IDS,
             semantic_execution_identity=target.env.semantic_execution_identity,
         )
     _same(before, _state(target.env))
+    if field == "schema":
+        state["schema"] = "world-lifecycle-v3"
+        with pytest.raises((TypeError, ValueError)):
+            target.env.prepare_world_restore(
+                kind="INITIAL",
+                state=state,
+                world_roster=_roster(),
+                destination_world_ids=IDS,
+                semantic_execution_identity=target.env.semantic_execution_identity,
+            )
+        _same(before, _state(target.env))
 
 
 def test_initial_restore_over_live_boundary_refuses(compiled):
     run = _Run(_env(compiled))
     state = run.initial()
     run.reset(1)
     before = _state(run.env)
     with pytest.raises(ValueError):
@@ -563,16 +581,19 @@ def test_two_boundaries_two_reorders_keep_historical_binding_verbatim(compiled):
     old_content = deepcopy(first.events[1])
     second = _restore(compiled, saved1, tuple(reversed(IDS)))
     assert dict(second.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
     assert second.reset(2)[1].accepted.world_ids == tuple(reversed(IDS))
     second.step((IDS[0],))
     _, closure, dispositions = second.close(2, (IDS[0],))
     second.release_closed(2, closure, dispositions)
     saved2 = second.completed((1, 2))
+    assert saved2["vfs_random_context"]["training_seed"] == SEED
+    assert saved2["vfs_random_context"]["world_ids"] == list(reversed(IDS))
+    assert saved2["vfs_random_context"]["world_episode_seqs"] == [2, 2]
     assert saved2["accepted_bindings"] == [
         {"batch_episode": 1, "world_ids": list(IDS), "world_episode_seqs": [1, 1]},
         {"batch_episode": 2, "world_ids": list(reversed(IDS)), "world_episode_seqs": [2, 2]},
     ]
     third = _restore(compiled, saved2, IDS)
     restored_bindings = third.completed((1, 2))["accepted_bindings"]
     _same(saved2["accepted_bindings"], restored_bindings)
     by_batch = {binding["batch_episode"]: binding for binding in restored_bindings}
@@ -657,21 +678,26 @@ def test_initial_schema_exact_and_snapshot_isolation(compiled):
         "training_seed",
         "execution_identity",
         "saved_lane_binding",
         "destination_lane_binding",
         "accepted_episode_seqs",
         "last_closed_episode",
         "completed_boundary_key",
         "accepted_bindings",
+        "vfs_random_context",
     }
     state["world_roster"]["world_ids"].clear()
     state["accepted_episode_seqs"][IDS[0]] = 99
+    state["vfs_random_context"]["world_ids"].clear()
+    state["vfs_random_context"]["world_episode_seqs"][0] = 99
     assert run.initial()["world_roster"]["world_ids"] == list(IDS)
     assert run.initial()["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
+    assert run.initial()["vfs_random_context"]["world_ids"] == list(IDS)
+    assert run.initial()["vfs_random_context"]["world_episode_seqs"] == [0, 0]
 
 
 @pytest.mark.parametrize("mode", ["wrong_kind", "extra_key", "changed_manifest", "wrong_seed", "unknown_member"])
 def test_restore_identity_and_kind_mismatch_refuse(compiled, mode):
     state = _Run(_env(compiled)).initial()
     target = _Run(_env(compiled), bootstrap=False)
     kind, order = "INITIAL", IDS
     if mode == "wrong_kind":
diff --git a/tests/test_townlet/unit/vfs/test_random_expressions.py b/tests/test_townlet/unit/vfs/test_random_expressions.py
index 64063141..d1dcad0c 100644
--- a/tests/test_townlet/unit/vfs/test_random_expressions.py
+++ b/tests/test_townlet/unit/vfs/test_random_expressions.py
@@ -12,36 +12,139 @@ from __future__ import annotations
 import shutil
 from pathlib import Path
 from typing import Any
 
 import pytest
 import torch
 import yaml
 
+from townlet.config.world_roster import WorldRosterDeclaration
 from townlet.determinism import seed_all
+from townlet.environment.vectorized_env import WorldReceiptIssuer
 from townlet.items.manager import SpawnPredicateReads
 from townlet.universe.compiler import UniverseCompiler
 from townlet.universe.errors import CompilationError
 from townlet.vfs.evaluator import VFSEvaluator
 from townlet.vfs.namespace import SPAWN_PREDICATE
 from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
-from townlet.vfs.random_draws import VFSRandomness, reference_uniform
+from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext, reference_uniform
 from townlet.vfs.schema import VariableDef, VariableScope
 from townlet.vfs.vtc import VTCTransitionRuleProgram, VTCWriteTarget, compile_vtc_transition_rules
 from townlet.world.expression import ExpressionParser
 
 REPO = Path(__file__).resolve().parents[4]
 WITNESS = REPO / "configs" / "static_epistemic_access"
 LEVEL = "L0_simple"
 N = 4
 STEPS = 64
 MINMAX = {"kind": "minmax", "min": 0.0, "max": 3.0, "clip": True}
 
 
+def _environment(universe, num_agents: int = N, seed: int = 7):
+    ids = tuple(f"expression-world-{index}" for index in range(num_agents))
+    roster = WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)})
+    return universe.create_environment(
+        num_agents=num_agents,
+        level_name=LEVEL,
+        device="cpu",
+        world_roster=roster,
+        training_seed=seed,
+        lane_world_ids=ids,
+    )
+
+
+class _EpisodeDriver:
+    """Local sealed producer-test owners, not real population/bank/learning owners."""
+
+    def __init__(self, env):
+        self.env = env
+        self.issuer = WorldReceiptIssuer(owner=self)
+        roles = dict.fromkeys("population curiosity curriculum exploration network optimizer scheduler replay selection".split(), self)
+        self.authority = env.bind_boundary_authority(owner=self, role_owners=roles)
+        self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))
+        self.batch = 0
+        self.accepted = None
+        self.participants = set()
+
+    def receipt(self, receipt_kind, **payload):
+        return self.issuer.issue(kind=receipt_kind, payload=payload)
+
+    def reset(self):
+        reservation = self.env.prepare_episode(batch_episode=self.batch + 1, release=self.release)
+        self.env.validate_episode_reservation(reservation)
+        result = self.env.reset(reservation=reservation)
+        self.accepted = result.accepted
+        self.env.activate_episode(
+            accepted=self.accepted,
+            population_receipt=self.receipt("activation", accepted=self.accepted),
+            curiosity_receipt=self.receipt("activation", accepted=self.accepted),
+        )
+        self.batch += 1
+        self.participants.clear()
+        return result.observation
+
+    def step(self, actions):
+        self.participants.update(world_id for index, world_id in enumerate(self.env.world_ids) if not self.env.dones[index])
+        return self.env.step(actions)
+
+    def complete(self):
+        participants = tuple(world_id for world_id in self.accepted.world_ids if world_id in self.participants)
+        assert participants, "completion requires a real participating step"
+        content = tuple(
+            (self.batch, index, world_id, self.accepted.world_episode_seqs[index], "local-interface-outcome")
+            for index, world_id in enumerate(self.accepted.world_ids)
+            if world_id in participants
+        )
+        payload = dict(
+            accepted=self.accepted,
+            boundary_key=self.batch,
+            completion_content=content,
+            participated_world_ids=participants,
+            dispositions=tuple(
+                (world_id, "completed" if world_id in participants else "retired_nonparticipating") for world_id in self.accepted.world_ids
+            ),
+        )
+        prepared = self.env.prepare_episode_close(
+            accepted=self.accepted,
+            boundary_key=self.batch,
+            completion_content=content,
+            participated_world_ids=participants,
+            dispositions=self.receipt("prepared_dispositions", **payload),
+        )
+        self.env.freeze_episode_close(prepared)
+        dispositions = self.receipt("dispositions", **payload)
+        closure = self.env.close_episode(prepared, dispositions=dispositions)
+        children = {
+            name: self.receipt(name, accepted=self.accepted, boundary_key=self.batch, completion_content=content)
+            for name in (
+                "curriculum_receipt",
+                "exploration_receipt",
+                "population_commit_receipt",
+                "epsilon_install_receipt",
+                "selection_sync_receipt",
+            )
+        }
+        effects = self.receipt(
+            "boundary_effects",
+            batch_episode=self.batch,
+            accepted_identity=self.accepted,
+            completion_content=content,
+            retirement_receipt=dispositions,
+            **children,
+        )
+        self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
+
+
+def _started(universe, num_agents: int = N, seed: int = 7):
+    driver = _EpisodeDriver(_environment(universe, num_agents, seed))
+    driver.reset()
+    return driver.env
+
+
 # --- pack helpers ---------------------------------------------------------------------------
 
 
 def _decl(var_id: str, *, scope: str = "agent", type_: str = "scalar", lifetime: str = "episode", **extra: object) -> dict:
     declaration: dict[str, object] = {
         "id": var_id,
         "scope": scope,
         "type": type_,
@@ -162,19 +265,20 @@ def _snapshot(env, world: int, obs: torch.Tensor) -> dict[str, Any]:
         "position": env.positions[world].clone(),
         "registry": {var_id: _reg(env, var_id)[world].clone() for var_id in env.vfs_registry.variables},
     }
 
 
 def _run(universe, actions: list[torch.Tensor], *, num_agents: int = N, seed: int = 7) -> list[list[dict[str, Any]]]:
     """Per step (reset first), every world's snapshot."""
     seed_all(seed)
-    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
+    driver = _EpisodeDriver(_environment(universe, num_agents, seed))
+    env = driver.env
     seed_all(seed)
-    obs = env.reset()
+    obs = driver.reset()
     trace = [[_snapshot(env, world, obs) for world in range(num_agents)]]
     for step_actions in actions:
         obs, _, _, _ = env.step(step_actions)
         trace.append([_snapshot(env, world, obs) for world in range(num_agents)])
     return trace
 
 
 def _assert_equal(a: Any, b: Any, where: str) -> None:
@@ -202,39 +306,36 @@ def _quiet(env_like_num_agents: int, wait: int, steps: int) -> list[torch.Tensor
 def test_random_draws_compile_in_expressions_rules_and_action_writes(random_universe) -> None:
     schedule = random_universe.get_level(LEVEL).transition_schedule
     assert {rule.variable_id for rule in schedule.transition_rule_program.rules} == {"roll"}
     assert "luck" in {write.variable_id for write in schedule.action_write_program.writes}
 
 
 def test_a_literal_argument_draw_in_an_agent_expression_is_one_draw_per_row(random_universe) -> None:
     seed_all(3)
-    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    env = _started(random_universe, seed=3)
     noise = _reg(env, "noise")
     assert noise.shape == (N,)
     assert len(set(noise.tolist())) == N
     assert torch.all((noise >= 0.0) & (noise < 1.0))
 
 
 def test_a_global_draw_differs_across_worlds_and_a_rule_rolls_per_world(random_universe) -> None:
     seed_all(3)
-    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    env = _started(random_universe, seed=3)
     wait = _action(env, "WAIT")
     env.step(torch.full((N,), wait, dtype=torch.long))
     assert len(set(_reg(env, "weather").tolist())) == N
     assert len(set(_reg(env, "roll").tolist())) == N
     assert torch.all((_reg(env, "weather") >= 0.0) & (_reg(env, "weather") < 3.0))
 
 
 def test_weather_holds_for_k_ticks_and_lag_of_a_random_variable_reads_its_history(random_universe) -> None:
     seed_all(5)
-    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    env = _started(random_universe, seed=5)
     wait = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
     weather = [_reg(env, "weather").clone()]
     yesterday = [_reg(env, "yesterday").clone()]
     for _ in range(9):
         env.step(wait)
         weather.append(_reg(env, "weather").clone())
         yesterday.append(_reg(env, "yesterday").clone())
     # Ticks 0..3 hold the tick-0 roll, 4..7 the tick-4 roll, 8.. the tick-8 roll.
@@ -247,43 +348,42 @@ def test_weather_holds_for_k_ticks_and_lag_of_a_random_variable_reads_its_histor
     # `yesterday` is the committed weather of the previous instant (the declared 0.0 at tick 0).
     assert torch.equal(yesterday[0], torch.zeros(N))
     for tick in range(1, 10):
         assert torch.equal(yesterday[tick], weather[tick - 1]), tick
 
 
 def test_an_action_write_draw_lands_on_the_acting_agents_row_only(random_universe) -> None:
     seed_all(5)
-    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    env = _started(random_universe, seed=5)
     actions = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
     actions[1] = _action(env, "ADVANCE")
     env.step(actions)
     luck = _reg(env, "luck")
     assert luck[1] != 0.0
     assert torch.equal(luck[[0, 2, 3]], torch.zeros(3))
 
 
 # --- S1: isolation, reproducibility, batch-size independence --------------------------------
 
 
 def test_same_seed_runs_are_bitwise_identical(random_universe) -> None:
     seed_all(7)
-    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
+    probe = _environment(random_universe)
     wait, advance = _action(probe, "WAIT"), _action(probe, "ADVANCE")
     actions = _quiet(N, wait, STEPS)
     for step in range(0, STEPS, 3):
         actions[step] = actions[step].clone()
         actions[step][step % N] = advance
     _assert_equal(_run(random_universe, actions), _run(random_universe, actions), "A/A")
 
 
 def test_world0s_actions_leave_every_other_worlds_draws_identical(random_universe) -> None:
     seed_all(7)
-    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
+    probe = _environment(random_universe)
     wait, advance = _action(probe, "WAIT"), _action(probe, "ADVANCE")
     movement = [index for index, action in enumerate(probe.action_space.actions) if action.name not in {"WAIT", "ADVANCE", "INTERACT"}]
     quiet = _quiet(N, wait, STEPS)
     busy = [row.clone() for row in quiet]
     for step in range(STEPS):
         busy[step][0] = advance if step % 2 else movement[step % len(movement)]
 
     trace_a = _run(random_universe, quiet)
@@ -294,49 +394,51 @@ def test_world0s_actions_leave_every_other_worlds_draws_identical(random_univers
             _assert_equal(snap_a[world], snap_b[world], f"step {step} world {world}")
     # World 0 did act: its action-write draw and its public state moved.
     assert trace_b[-1][0]["registry"]["luck"] != 0.0
     assert trace_b[-1][0]["registry"]["public_state"] > 0.0
 
 
 def test_a_worlds_draws_do_not_depend_on_the_batch_size(random_universe) -> None:
     seed_all(7)
-    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
+    probe = _environment(random_universe)
     wait = _action(probe, "WAIT")
     small = _run(random_universe, _quiet(N, wait, 16), num_agents=N)
     large = _run(random_universe, _quiet(2 * N, wait, 16), num_agents=2 * N)
     for step, (snap_small, snap_large) in enumerate(zip(small, large, strict=True)):
         for world in range(N):
             for var_id in ("weather", "noise", "roll", "yesterday"):
                 assert torch.equal(snap_small[world]["registry"][var_id], snap_large[world]["registry"][var_id]), (step, world, var_id)
 
 
 def test_a_new_episode_re_derives_every_worlds_stream(random_universe) -> None:
     seed_all(11)
-    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    driver = _EpisodeDriver(_environment(random_universe, seed=11))
+    env = driver.env
+    driver.reset()
     first = _reg(env, "noise").clone()
-    env.reset()
+    driver.step(env.get_action_masks().to(torch.int64).argmax(dim=1))
+    driver.complete()
+    driver.reset()
     assert not torch.equal(_reg(env, "noise"), first)
 
 
 # --- lifetimes and consumers -----------------------------------------------------------------
 
 
 def test_a_random_expression_is_stored_not_inlined_so_a_rule_reads_the_observed_draw(tmp_path: Path) -> None:
     """Inlining `coin` into the rule would draw again; the rule must see the value the observation showed."""
     pack = _pack(
         tmp_path,
         [_decl("coin", scope="global", expression="uniform(0.0, 1.0)"), _decl("copy", scope="global")],
         rules=[_rule("copy_rule", "copy", "coin")],
     )
     universe = _compile(pack)
     seed_all(2)
-    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
-    env.reset()
+    env = _started(universe, seed=2)
     wait = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
     for _ in range(3):
         shown = _reg(env, "coin").clone()
         env.step(wait)
         # The rule ran at instant k on the draw the instant-k observation carried; `coin`
         # then re-rolled for instant k+1.
         assert torch.equal(_reg(env, "copy"), shown)
         assert not torch.equal(_reg(env, "coin"), shown)
@@ -387,37 +489,42 @@ def _profile(expression: str) -> CompiledGlobalProfile:
     )
     return CompiledGlobalProfile(variables=[variable], dependencies={"x": ()})
 
 
 def test_the_profile_evaluator_refuses_to_sample_without_the_world_streams() -> None:
     evaluator = VFSEvaluator(history_spec=None)
     with pytest.raises(RuntimeError, match=r"Engine defect: expression variable\(s\) \['x'\] sample"):
         evaluator.evaluate_global_profile(_profile("uniform(0.0, 1.0)"), bars={}, vfs_state={}, marks={"x"}, device=torch.device("cpu"))
-    randomness = VFSRandomness(7)
-    randomness.reset()
+    ids = ("profile-west", "profile-center", "profile-east")
+    randomness = VFSRandomness(context=VFSWorldContext(training_seed=7, world_ids=ids, world_episode_seqs=(1, 1, 1)))
     drawn = evaluator.evaluate_global_profile(
         _profile("uniform(0.0, 1.0)"),
         bars={},
         vfs_state={},
         marks={"x"},
         device=torch.device("cpu"),
-        draws=randomness.instant(tick=5, worlds=3, device=torch.device("cpu")),
+        draws=randomness.instant(tick=5, device=torch.device("cpu")),
     )["x"]
     assert drawn.shape == (3,)
-    expected = [reference_uniform(seed=7, episode=1, tick=5, site="var:x", ordinal=0, world=world, element=0) for world in range(3)]
+    expected = [
+        reference_uniform(training_seed=7, world_id=world_id, world_episode_seq=1, tick=5, site="var:x", ordinal=0, element=0)
+        for world_id in ids
+    ]
     assert drawn.tolist() == pytest.approx(expected, abs=0.0)
 
 
 def test_a_rule_program_refuses_to_sample_without_the_world_streams() -> None:
     targets = {"g": VTCWriteTarget(VariableScope.GLOBAL, "scalar", meter=False, expression=None)}
     program = compile_vtc_transition_rules([_rule("r", "g", "uniform(0.0, 1.0)")], targets)
     with pytest.raises(RuntimeError, match="Engine defect: VTC transition rules ran without the instant's draws"):
         VTCTransitionRuleProgram(program.rules).apply(
             vfs_state={"g": torch.zeros(2)}, active_mask=torch.tensor([True, True]), device=torch.device("cpu"), draws=None
         )
     with pytest.raises(RuntimeError, match="draws for 3 worlds, not 2"):
         VTCTransitionRuleProgram(program.rules).apply(
             vfs_state={"g": torch.zeros(2)},
             active_mask=torch.tensor([True, True]),
             device=torch.device("cpu"),
-            draws=VFSRandomness(0).instant(tick=0, worlds=3, device=torch.device("cpu")),
+            draws=VFSRandomness(
+                context=VFSWorldContext(training_seed=0, world_ids=("rule-west", "rule-center", "rule-east"), world_episode_seqs=(0, 0, 0))
+            ).instant(tick=0, device=torch.device("cpu")),
         )
diff --git a/tests/test_townlet/unit/vfs/test_verify_r3_repairs.py b/tests/test_townlet/unit/vfs/test_verify_r3_repairs.py
index 42c1ff88..4e0c9219 100644
--- a/tests/test_townlet/unit/vfs/test_verify_r3_repairs.py
+++ b/tests/test_townlet/unit/vfs/test_verify_r3_repairs.py
@@ -1,34 +1,154 @@
 """Repairs for the adversarial verification of 636192e0 (R3 verifier, V1-V7).
 
 VFS draws are counter-based (`townlet.vfs.random_draws`): every value is a pure function of
-(seed, episode, tick, site, world, element). Each case compiles a scratch pack and steps it.
+(training seed, exact world ID, world episode sequence, tick, site, ordinal, element).
+Each case compiles a scratch pack and steps it through current world authority gates.
 """
 
 from __future__ import annotations
 
 import shutil
 from pathlib import Path
 from typing import Any
 
 import pytest
 import torch
 import yaml
 
+from townlet.config.world_roster import WorldRosterDeclaration
 from townlet.determinism import seed_all
+from townlet.environment.vectorized_env import WorldReceiptIssuer
 from townlet.universe.compiler import UniverseCompiler
 from townlet.universe.errors import CompilationError
 
 REPO = Path(__file__).resolve().parents[4]
 WITNESS = REPO / "configs" / "static_epistemic_access"
 LEVEL = "L0_simple"
 MINMAX = {"kind": "minmax", "min": 0.0, "max": 3.0, "clip": True}
 
 
+def _environment(universe, num_agents: int, seed: int):
+    ids = tuple(f"repair-world-{index}" for index in range(num_agents))
+    roster = WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)})
+    return universe.create_environment(
+        num_agents=num_agents,
+        level_name=LEVEL,
+        device="cpu",
+        world_roster=roster,
+        training_seed=seed,
+        lane_world_ids=ids,
+    )
+
+
+class _EpisodeDriver:
+    """Explicit local receipt owners exercise ENV, not actual runner/bank/learning."""
+
+    def __init__(self, env, *, bootstrap=True):
+        self.env = env
+        self.issuer = WorldReceiptIssuer(owner=self)
+        roles = dict.fromkeys("population curiosity curriculum exploration network optimizer scheduler replay selection".split(), self)
+        self.authority = env.bind_boundary_authority(owner=self, role_owners=roles)
+        self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1)) if bootstrap else None
+        self.batch = 0
+        self.accepted = None
+        self.participants = set()
+
+    def receipt(self, receipt_kind, **payload):
+        return self.issuer.issue(kind=receipt_kind, payload=payload)
+
+    def reset(self):
+        reservation = self.env.prepare_episode(batch_episode=self.batch + 1, release=self.release)
+        self.env.validate_episode_reservation(reservation)
+        result = self.env.reset(reservation=reservation)
+        self.accepted = result.accepted
+        self.env.activate_episode(
+            accepted=self.accepted,
+            population_receipt=self.receipt("activation", accepted=self.accepted),
+            curiosity_receipt=self.receipt("activation", accepted=self.accepted),
+        )
+        self.batch += 1
+        self.participants.clear()
+        return result.observation
+
+    def step(self, actions):
+        self.participants.update(world_id for index, world_id in enumerate(self.env.world_ids) if not self.env.dones[index])
+        return self.env.step(actions)
+
+    def complete(self):
+        participants = tuple(world_id for world_id in self.accepted.world_ids if world_id in self.participants)
+        assert participants, "completion requires a real participating step"
+        content = tuple(
+            (self.batch, index, world_id, self.accepted.world_episode_seqs[index], "local-interface-outcome")
+            for index, world_id in enumerate(self.accepted.world_ids)
+            if world_id in participants
+        )
+        payload = dict(
+            accepted=self.accepted,
+            boundary_key=self.batch,
+            completion_content=content,
+            participated_world_ids=participants,
+            dispositions=tuple(
+                (world_id, "completed" if world_id in participants else "retired_nonparticipating") for world_id in self.accepted.world_ids
+            ),
+        )
+        prepared = self.env.prepare_episode_close(
+            accepted=self.accepted,
+            boundary_key=self.batch,
+            completion_content=content,
+            participated_world_ids=participants,
+            dispositions=self.receipt("prepared_dispositions", **payload),
+        )
+        self.env.freeze_episode_close(prepared)
+        dispositions = self.receipt("dispositions", **payload)
+        closure = self.env.close_episode(prepared, dispositions=dispositions)
+        children = {
+            name: self.receipt(name, accepted=self.accepted, boundary_key=self.batch, completion_content=content)
+            for name in (
+                "curriculum_receipt",
+                "exploration_receipt",
+                "population_commit_receipt",
+                "epsilon_install_receipt",
+                "selection_sync_receipt",
+            )
+        }
+        effects = self.receipt(
+            "boundary_effects",
+            batch_episode=self.batch,
+            accepted_identity=self.accepted,
+            completion_content=content,
+            retirement_receipt=dispositions,
+            **children,
+        )
+        self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
+
+    def checkpoint(self):
+        return self.env.checkpoint_world_state(
+            kind="COMPLETED",
+            release=self.release,
+            retained_binding_batches=tuple(range(1, self.batch + 1)),
+            initial=None,
+        )
+
+    def restore(self, state):
+        roster = WorldRosterDeclaration.from_dict(state["world_roster"])
+        prepared = self.env.prepare_world_restore(
+            kind="COMPLETED",
+            state=state,
+            world_roster=roster,
+            destination_world_ids=self.env.world_ids,
+            semantic_execution_identity=self.env.semantic_execution_identity,
+        )
+        boundary = self.receipt("restored_boundary", kind="COMPLETED", state=state, prepared=prepared)
+        release = self.authority.restored(restore=prepared, boundary=boundary)
+        self.release = self.env.install_world_restore(prepared=prepared, release=release)
+        self.batch = state["next_batch_episode"] - 1
+
+
 def _decl(var_id: str, *, scope: str = "agent", type_: str = "scalar", lifetime: str = "episode", **extra: object) -> dict:
     declaration: dict[str, object] = {
         "id": var_id,
         "scope": scope,
         "type": type_,
         "lifetime": lifetime,
         "semantic_type": "custom",
         "readable_by": ["engine", "agent"],
@@ -74,19 +194,19 @@ def _compile(pack: Path):
 def _refusal(pack: Path) -> str:
     with pytest.raises(CompilationError) as caught:
         _compile(pack)
     return str(caught.value)
 
 
 def _env(universe, num_agents: int, seed: int = 7):
     seed_all(seed)
-    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
-    env.reset()
-    return env
+    driver = _EpisodeDriver(_environment(universe, num_agents, seed))
+    driver.reset()
+    return driver.env
 
 
 def _wait(env) -> int:
     return next(index for index, action in enumerate(env.action_space.actions) if action.name == "WAIT")
 
 
 def _reg(env, var_id: str) -> torch.Tensor:
     return env.vfs_registry.get(var_id, reader="engine").clone()
@@ -265,37 +385,46 @@ def test_v3_world0_differential(tmp_path: Path, num_agents: int) -> None:
 
     quiet, perturbed = run(False), run(True)
     for left, right in zip(quiet, perturbed, strict=True):
         for key in left:
             assert torch.equal(left[key], right[key]), key
 
 
 def test_v3_resume_from_a_checkpoint_reproduces_the_draws(tmp_path: Path) -> None:
-    """The draw state is (seed, episode). Checkpointed between episodes (as the runner does) and
-    restored into a fresh env in a differently seeded process, every later draw is the original's,
-    tick for tick: a value is a pure function of seed, episode, tick, site, world and element."""
+    """Direct ENV boundary restore reproduces the next reset plus five ticks.
+
+    Local sealed owners exercise the real world checkpoint gates. This does not run
+    actual runner save/load or qualify the still-open outer checkpoint integration.
+    """
     universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))
-    original = _env(universe, 3, seed=11)
+    seed_all(11)
+    driver = _EpisodeDriver(_environment(universe, 3, 11))
+    original = driver.env
+    driver.reset()
     wait = _wait(original)
-    for _ in range(2):
+    for episode in range(3):
         for _ in range(3):
-            original.step(torch.full((3,), wait, dtype=torch.long))
-        original.reset()
-    checkpoint = original.vfs_random_state()
-    original.reset()
+            driver.step(torch.full((3,), wait, dtype=torch.long))
+        driver.complete()
+        if episode < 2:
+            driver.reset()
+    checkpoint = driver.checkpoint()
+    assert checkpoint["vfs_random_context"]["world_episode_seqs"] == [3, 3, 3]
+    driver.reset()
     original_ticks = [{name: _reg(original, name) for name in V3_VARS}]
     for _ in range(5):
         original.step(torch.full((3,), wait, dtype=torch.long))
         original_ticks.append({name: _reg(original, name) for name in V3_VARS})
 
     seed_all(999)
-    resumed = universe.create_environment(num_agents=3, level_name=LEVEL, device="cpu")
-    resumed.restore_vfs_random_state(checkpoint)
-    resumed.reset()
+    restored = _EpisodeDriver(_environment(universe, 3, 11), bootstrap=False)
+    restored.restore(checkpoint)
+    restored.reset()
+    resumed = restored.env
     for tick, expected in enumerate(original_ticks):
         if tick:
             resumed.step(torch.full((3,), wait, dtype=torch.long))
         for name in V3_VARS:
             assert torch.equal(_reg(resumed, name), expected[name]), (tick, name)
 
 
 def test_v3_the_runner_checkpoint_carries_the_draw_state() -> None:
@@ -303,45 +432,72 @@ def test_v3_the_runner_checkpoint_carries_the_draw_state() -> None:
 
     assert "vfs_random_state" in DEMO_CHECKPOINT_KEYS and CHECKPOINT_FORMAT_VERSION == 9
 
 
 def test_v7_the_seed_is_captured_at_construction(tmp_path: Path) -> None:
     """Another environment's seed_all after construction never shifts this environment's draws."""
     universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))
     seed_all(1)
-    solo = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
-    solo.reset()
-    solo.reset()
+    solo_driver = _EpisodeDriver(_environment(universe, 2, 1))
+    solo = solo_driver.env
+    solo_driver.reset()
+    solo_driver.step(solo.get_action_masks().to(torch.int64).argmax(dim=1))
+    solo_driver.complete()
+    solo_driver.reset()
     expected = _reg(solo, "g_rand")
 
     seed_all(1)
-    shared = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
-    shared.reset()
+    shared_driver = _EpisodeDriver(_environment(universe, 2, 1))
+    shared = shared_driver.env
+    shared_driver.reset()
+    shared_driver.step(shared.get_action_masks().to(torch.int64).argmax(dim=1))
+    shared_driver.complete()
     seed_all(2)
-    universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu").reset()
-    shared.reset()
+    other = _EpisodeDriver(_environment(universe, 2, 2))
+    other.reset()
+    shared_driver.reset()
     assert torch.equal(_reg(shared, "g_rand"), expected)
 
 
 def test_draw_kernel_matches_the_reference_specification() -> None:
-    from townlet.vfs.random_draws import VFSRandomness, reference_uniform
+    from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext, reference_uniform
 
-    randomness = VFSRandomness(2**63 + 12345)
-    randomness.reset()
-    randomness.reset()
-    stream = randomness.instant(tick=9, worlds=3, device=torch.device("cpu")).stream("var:x", (3, 5))
+    ids = ("kernel-west", "kernel-center", "kernel-east")
+    randomness = VFSRandomness(context=VFSWorldContext(training_seed=2**63 + 12345, world_ids=ids, world_episode_seqs=(2, 2, 2)))
+    stream = randomness.instant(tick=9, device=torch.device("cpu")).stream("var:x", (3, 5))
     stream.uniform("uniform", torch.zeros(()))
     second = stream.uniform("uniform", torch.zeros(()))
     expected = [
-        [reference_uniform(seed=2**63 + 12345, episode=2, tick=9, site="var:x", ordinal=1, world=w, element=e) for e in range(5)]
-        for w in range(3)
+        [
+            reference_uniform(
+                training_seed=2**63 + 12345,
+                world_id=world_id,
+                world_episode_seq=2,
+                tick=9,
+                site="var:x",
+                ordinal=1,
+                element=element,
+            )
+            for element in range(5)
+        ]
+        for world_id in ids
     ]
     assert torch.equal(second, torch.tensor(expected, dtype=torch.float32))
-    normal = randomness.instant(tick=0, worlds=8192, device=torch.device("cpu")).stream("var:n", (8192,)).normal("n", torch.zeros(()))
+    normal_context = VFSWorldContext(
+        training_seed=2**63 + 12345,
+        world_ids=tuple(f"normal-world-{index}" for index in range(8192)),
+        world_episode_seqs=(2,) * 8192,
+    )
+    normal = (
+        VFSRandomness(context=normal_context)
+        .instant(tick=0, device=torch.device("cpu"))
+        .stream("var:n", (8192,))
+        .normal("n", torch.zeros(()))
+    )
     assert abs(float(normal.mean())) < 0.05 and abs(float(normal.std()) - 1.0) < 0.05
 
 
 # --- V4: a static initialised by initial_value_mode is read at its runtime value ---------
 
 
 def test_v4_an_expression_over_a_mode_initialised_tensor_compiles_resets_and_steps(tmp_path: Path) -> None:
     tensor = _decl("t1", type_="tensor1d", shape=[3], initial_value_mode="ones")
diff --git a/tests/test_townlet/unit/vfs/test_vtc_bounds_clamps.py b/tests/test_townlet/unit/vfs/test_vtc_bounds_clamps.py
index 91bcf18b..de931744 100644
--- a/tests/test_townlet/unit/vfs/test_vtc_bounds_clamps.py
+++ b/tests/test_townlet/unit/vfs/test_vtc_bounds_clamps.py
@@ -14,17 +14,17 @@ PDR-0014 B3 / PDR-0015) are NOT replaced by this phase — they are mid-tick wri
 contracts with different semantics (a ceiling applied before the passive tick reads
 back 0.49, not 0.5). This phase is the end-of-transition invariant net.
 """
 
 import pytest
 import torch
 
 from townlet.vfs import vtc
-from townlet.vfs.random_draws import VFSRandomness
+from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext
 from townlet.vfs.transition_graph import TransitionPhaseGraph
 from townlet.vfs.transition_schedule import (
     VTCTransitionContext,
     VTCTransitionRunner,
     VTCTransitionSchedule,
 )
 
 
@@ -101,17 +101,19 @@ def test_transition_runner_executes_bounds_clamps_in_clamp_and_validate_phase()
         TransitionPhaseGraph.default(),
     )
     runner = VTCTransitionRunner(_empty_schedule_with_bounds(program))
     context = VTCTransitionContext(
         vfs_state={},
         bars_state={"energy": torch.tensor([1.7, -0.3], dtype=torch.float32)},
         active_mask=torch.tensor([True, False]),
         device=torch.device("cpu"),
-        draws=VFSRandomness(0).instant(tick=0, worlds=2, device=torch.device("cpu")),
+        draws=VFSRandomness(
+            context=VFSWorldContext(training_seed=0, world_ids=("bounds-west", "bounds-east"), world_episode_seqs=(0, 0))
+        ).instant(tick=0, device=torch.device("cpu")),
     )
 
     # A phase the rules are not scheduled for leaves the out-of-bounds value alone.
     untouched = runner.run_phases(("apply_passive_depletion",), context)
     assert untouched.bars_state["energy"].tolist() == pytest.approx([1.7, -0.3])
 
     clamped = runner.run_phases(("clamp_and_validate",), context)
     # Bounds are invariants: they apply to every agent, active or not.
