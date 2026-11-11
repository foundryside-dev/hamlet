 .../regressions/bac/test_intrinsic_composition.py  | 79 ++++++++++++----------
 1 file changed, 44 insertions(+), 35 deletions(-)
diff --git a/tests/test_townlet/regressions/bac/test_intrinsic_composition.py b/tests/test_townlet/regressions/bac/test_intrinsic_composition.py
index a330e263..e1d2d9f5 100644
--- a/tests/test_townlet/regressions/bac/test_intrinsic_composition.py
+++ b/tests/test_townlet/regressions/bac/test_intrinsic_composition.py
@@ -105,25 +105,24 @@ def wait_control(monkeypatch: Any, rig: Any) -> None:
 
 @pytest.mark.parametrize("scope", ("shared", "per_world"))
 @pytest.mark.parametrize(
     "scale,base,intrinsic,total", ((0.5, 0.25, 0.5, 1.6), (0.0, 0.25, 0.0, 1.1), (1.0, 0.25, 1.0, 2.1), (0.5, 0.5, 1.0, 2.1))
 )
 def test_real_composer_applies_runtime_scale_once(
     compiled: Any, monkeypatch: Any, scope: str, scale: float, base: float, intrinsic: float, total: float
 ) -> None:
     rig = make_parent(compiled, "icm", scope, selected_policy=controlled_policy(compiled, scope, scale))
     install_raw_two(rig.runtime, scope)
+    # Component initial-data control, consumed by genuine reset before either owner seals.
+    rig.env.initial_meter_values[rig.env.meter_name_to_index["energy"]] = 0.8
     rig.enter()
     real_composer(rig.env, base)
-    rig.env.meters[:, rig.env.meter_name_to_index["energy"]] = 0.8
-    # Real test setup changes predecessor state; keep actual parent observation synchronized.
-    rig.population.current_obs = rig.env._get_observations()
     wait_control(monkeypatch, rig)
     calls = observe_runtime(monkeypatch, rig)
     state = rig.population.step_population(rig.env)
     assert not bool(state.dones.any())  # These are pre-retirement arithmetic cases.
     assert len(calls["reward"]) == len(calls["service"]) == 1
     arguments, reward = calls["reward"][0]
     assert arguments["update_stats"] is True
     components = state.info["reward_components"]
     for actual, expected in (
         (reward.raw, 2.0),
@@ -207,53 +206,64 @@ def test_claim_refusal_precedes_first_physical_write(compiled: Any) -> None:
 
 
 @pytest.fixture(scope="module")
 def temporal_compiled() -> Any:
     return UniverseCompiler().compile(Path("configs/reference/model_pack"), primary_level="L0_demo", use_cache=False)
 
 
 @pytest.mark.parametrize("terminal", (False, True))
 def test_real_effect_pending_cancellation_preserves_successor(temporal_compiled: Any, monkeypatch: Any, terminal: bool) -> None:
     rig = make_parent(temporal_compiled)
-    rig.enter()
     env = rig.env
     manager = env.effect_manager
     effect_layout = env.token_spec.compact_layout().get_type("effect")
     assert effect_layout.capacity > 0
     assert env.token_spec.get_type("item").capacity > 0
-    bars = {name: env.meters[:, col] for name, col in env.meter_name_to_index.items()}
-    active = manager.spawn_effect(
-        effect_id="ate_food",
-        target_entity_id=0,
-        world=0,
-        intensity=1.0,
-        current_step=manager.current_step,
-        bars=bars,
-        vfs_registry=env.vfs_registry,
-        item_manager=env.item_manager,
-    )
-    assert active is not None and active.observable
-    manager.scheduler.schedule(
-        commands=manager.catalog.effects["ate_food"].on_tick,
-        delay_ticks=10,
-        base_tick=manager.current_step,
-        scope="agent",
-        entity_id=0,
-        context_overrides={"effect": active},
-        effect_instance=active.instance_id,
-    )
-    due = manager.current_step + 10
-    pending = tuple(manager.scheduler.pending[due])
-    assert pending
-    if terminal:
-        env.meters[0, env.meter_name_to_index["health"]] = 0.001
-    rig.population.current_obs = env._get_observations()
+    original_reset = env._reset_world_state
+    initialized: list[tuple[Any, int, tuple[Any, ...]]] = []
+
+    def initialize_effect_state() -> Any:
+        original_reset()  # Real base physics/VFS/items initialization, exactly once.
+        assert env.world_phase == "resetting"
+        bars = {name: env.meters[:, col] for name, col in env.meter_name_to_index.items()}
+        active = manager.spawn_effect(
+            effect_id="ate_food",
+            target_entity_id=0,
+            world=0,
+            intensity=1.0,
+            current_step=manager.current_step,
+            bars=bars,
+            vfs_registry=env.vfs_registry,
+            item_manager=env.item_manager,
+        )
+        assert active is not None and active.observable
+        manager.scheduler.schedule(
+            commands=manager.catalog.effects["ate_food"].on_tick,
+            delay_ticks=10,
+            base_tick=manager.current_step,
+            scope="agent",
+            entity_id=0,
+            context_overrides={"effect": active},
+            effect_instance=active.instance_id,
+        )
+        due = manager.current_step + 10
+        pending = tuple(manager.scheduler.pending[due])
+        assert pending
+        if terminal:
+            env.meters[0, env.meter_name_to_index["health"]] = 0.001
+        initialized.append((active, due, pending))
+        return env._get_observations()  # Final genuine reading BEFORE reset record/private snapshot.
+
+    with monkeypatch.context() as setup:
+        setup.setattr(env, "_reset_world_state", initialize_effect_state)
+        rig.enter()
+    [(active, due, pending)] = initialized
     wait_control(monkeypatch, rig)
     calculate = env._reward_calculator._calculate_shaped_rewards
     boundary: list[torch.Tensor] = []
 
     def capture(**kwargs: Any) -> Any:
         assert all(item in manager.scheduler.pending[due] for item in pending)
         assert active in manager.effects_in_world(0)
         boundary.append(env._get_observations().clone())
         return calculate(**kwargs)
 
@@ -274,26 +284,25 @@ def test_real_effect_pending_cancellation_preserves_successor(temporal_compiled:
         monkeypatch.setattr(env._reward_calculator, "_calculate_shaped_rewards", calculate)
         later = rig.population.step_population(env)
         assert not bool(later.info["active_on_entry"][0])
         assert float(later.rewards[0]) == float(later.info["intrinsic_weight"][0]) == 0.0
         assert all(float(component[0]) == 0.0 for component in later.info["reward_components"].values())
 
 
 def test_retirement_preserves_live_composition_then_adds_bonus(compiled: Any, monkeypatch: Any) -> None:
     rig = make_parent(compiled, "icm", selected_policy=controlled_policy(compiled, "shared", 0.5))
     install_raw_two(rig.runtime, "shared")
-    rig.enter()
-    real_composer(rig.env, 0.25)
     # Explicit actual ENV lifespan control; all rows retire on their first eligible transition.
     rig.env.agent_lifespan = 1
-    rig.env.meters[:, rig.env.meter_name_to_index["energy"]] = 0.8
-    rig.population.current_obs = rig.env._get_observations()
+    rig.env.initial_meter_values[rig.env.meter_name_to_index["energy"]] = 0.8
+    rig.enter()
+    real_composer(rig.env, 0.25)
     wait_control(monkeypatch, rig)
     state = rig.population.step_population(rig.env)
     assert bool(state.info["newly_retired"].all())
     assert bool(state.info["active_on_entry"].all())
     components = state.info["reward_components"]
     torch.testing.assert_close(components["intrinsic"], torch.full_like(state.rewards, 0.5))
     torch.testing.assert_close(components["extrinsic"], torch.full_like(state.rewards, 2.0))
     torch.testing.assert_close(state.rewards, torch.full_like(state.rewards, 2.6))
     equal(state.info["intrinsic_transition"].context.successor, state.observations)
     request = ReplayRequest(len(IDS), 1, 2, "uniform_without_replacement", "feedforward", "transition")
# Composer fixture causal initialization repair

R33basef0f1b79b7df95402269d8e306330f6b38a233a27 -> R3424258ffe10cbb423276fa324295cef24440c2c89
Onlyonefixturechanged350/a16c2a52, allproductionandotherfivebodyhashesunchanged.

