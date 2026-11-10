Base265a36ac152a4419d22a3b5753ea6d151d112f19
Candidate5d866cc7fe7af528fcbc2119b1ba9ddefb03062e
Exactly5whole4250cap, singlefixturefilediff; no productionchange.
diff --git a/tests/test_townlet/regressions/bac/test_pw_rng_domains.py b/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
index e2eda2f5..414308e6 100644
--- a/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
+++ b/tests/test_townlet/regressions/bac/test_pw_rng_domains.py
@@ -11,16 +11,17 @@ import sys
 import threading
 from collections.abc import Mapping
 from pathlib import Path
 
 import numpy as np
 import pytest
 import torch
 
+from townlet.config.bac_options import RNDOptions
 from townlet.exploration import world_curiosity_state as ws
 from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
 from townlet.exploration.icm import ICMExploration
 from townlet.exploration.rnd import RNDExploration
 
 KINDS = ("rnd", "icm", "adaptive_rnd")
 
 
@@ -143,43 +144,61 @@ def _icm_context(observations, tick):
         predecessor=observations,
         actions=torch.arange(len(observations), dtype=torch.long) % 2,
         successor=observations + torch.tensor([0.9, -0.2, 0.8]),
         active_on_entry=torch.ones(len(observations), dtype=torch.bool),
         vector_tick=tick,
     )
 
 
-def _factory(kind):
-    def create(rng):
+def _factory(kind, *, service_clock_unit):
+    def create(candidate_rng):
         if kind == "rnd":
-            return RNDExploration(**_parameters(kind))
-        if kind == "adaptive_rnd":
-            return AdaptiveIntrinsicExploration(**_parameters(kind))
-        policy = _icm_policy()
-        return ICMExploration(policy, obs_dim=3, action_dim=2, device="cpu", **dict(policy.provider_parameters))
+            backend = RNDExploration(**_parameters(kind), rng=candidate_rng, service_clock_unit=service_clock_unit)
+        elif kind == "adaptive_rnd":
+            backend = AdaptiveIntrinsicExploration(**_parameters(kind), rng=candidate_rng, service_clock_unit=service_clock_unit)
+        else:
+            policy = _icm_policy()
+            return ICMExploration(
+                policy,
+                obs_dim=3,
+                action_dim=2,
+                device="cpu",
+                **dict(policy.provider_parameters),
+                rng=candidate_rng,
+                service_clock_unit=service_clock_unit,
+            )
+        backend.configure_service(
+            RNDOptions(
+                service_mode="paced_fifo",
+                max_updates_per_tick=1,
+                max_pending_rows=4,
+                overflow_policy="service_before_admit",
+            )
+        )
+        return backend
 
     return create
 
 
 def _draw(sources):
     # Current networks train deterministically: this transparent wrapper exercises RNG consumption.
     return (torch.rand(3), random.gauss(0, 1), sources.python.random(), np.random.normal(size=3), sources.numpy.normal(size=3))
 
 
-def _exercise(backend, sources, rows, tick):
+def _exercise(backend, sources, rows, tick, *, clock: ws.ServiceClock):
     draws = _draw(sources)
     observations = torch.tensor([[0.2, -0.7, 1.1], [1.3, 0.4, -0.2]])[:rows]
     if isinstance(backend, ICMExploration):
         context = _icm_context(observations, tick)
         reward = backend.compute_transition_novelty(context, update_stats=True)
-        backend.admit_and_service(context)
+        backend.admit_and_service_at(context, clock=clock)
     else:
         reward = backend.compute_intrinsic_rewards(observations, update_stats=True)
-        backend.update({"observations": observations})
+        backend.admit_and_service_at(observations, clock=clock)
         if isinstance(backend, AdaptiveIntrinsicExploration):
             backend.update_on_episode_end(200.0 + tick)
     return draws, reward, backend.checkpoint_state()
 
 
 def _rnd_state(state, kind):
     return state["rnd_state"] if kind == "adaptive_rnd" else state
 
@@ -193,61 +212,67 @@ def _learning_snapshot(value):
         return [_learning_snapshot(child) for child in value]
     if isinstance(value, tuple):
         return tuple(_learning_snapshot(child) for child in value)
     return copy.deepcopy(value)
 
 
 def _assert_learning(before, after, kind, updates, pending):
     old, new = _rnd_state(_learning_snapshot(before), kind), _rnd_state(_learning_snapshot(after), kind)
+    assert new["schema"] == ("icm-state-v2" if kind == "icm" else "rnd-state-v2")
+    if kind == "adaptive_rnd":
+        assert after["schema"] == "adaptive-intrinsic-state-v2"
     model = "encoder" if kind == "icm" else "predictor_network"
     assert any(not torch.equal(old[model][key], value) for key, value in new[model].items())
     moments = new["optimizer"]["state"]
     assert moments and all(float(item["step"]) == updates for item in moments.values())
     assert any(torch.count_nonzero(item["exp_avg"]) > 0 for item in moments.values())
     assert any(torch.count_nonzero(item["exp_avg_sq"]) > 0 for item in moments.values())
     if kind == "icm":
         assert new["counters"]["optimizer_updates"] == updates
         assert new["counters"]["consumed_rows"] == updates * 2
         assert len(new["pending"]) == pending
         assert new["counters"]["admitted_rows"] == updates * 2 + pending + new["counters"]["dropped_rows"]
+        service = new
+        admitted = new["counters"]["admitted_rows"]
+        assert new["counters"]["dropped_rows"] == 0
     else:
         _equal(old["fixed_network"], new["fixed_network"])
         service = new["predictor_service"]
         assert service["optimizer_updates"] == updates and service["consumed_rows"] == updates * 2
         assert len(service["pending_observations"]) == pending
         assert service["admitted_rows"] == updates * 2 + pending + service["dropped_rows"]
+        assert service["version"] == 2 and service["optimizer_step_offset"] == 0
+        assert service["dropped_rows"] == 0
+        assert new["reward_rms_count"] > old["reward_rms_count"]
+        admitted = service["admitted_rows"]
+    assert 0 <= service["ordinary_updates_at_position"] <= 1
+    if service["service_clock_unit"] == "world_eligible_admission":
+        assert service["service_position"] == admitted
+        if kind != "icm":
+            assert service["step_counter"] == 0
 
 
 def _owner(kind, world, ids):
     _, owned_type = _api()
-    return owned_type.construct(rng=_rng(kind, world, ids), factory=_factory(kind))
+    return owned_type.construct(rng=_rng(kind, world, ids), factory=_factory(kind, service_clock_unit="world_eligible_admission"))
 
 
 def _validate_backend(candidate, payload):
-    # Counted test validation adapter, not PW04 native complete semantic validation.
+    # Validate the complete current native schema without installing candidate state.
     before, transported = copy.deepcopy(candidate.checkpoint_state()), copy.deepcopy(payload)
-    if isinstance(candidate, AdaptiveIntrinsicExploration):
-        assert set(payload) == set(before)
-        assert isinstance(payload["survival_history"], list)
-        assert all(isinstance(x, (int, float)) and np.isfinite(x) and x >= 0 for x in payload["survival_history"])
-        assert all(np.isfinite(payload[key]) for key in before if key not in ("rnd_state", "survival_history"))
-        candidate.rnd.validate_state(payload["rnd_state"])
-    elif isinstance(candidate, RNDExploration):
-        candidate.validate_state(payload)
-    else:
-        policy = candidate.policy
-        owned_policy = type(policy).from_dict(copy.deepcopy(policy.to_dict()))
-        copy.deepcopy(candidate, {id(policy): owned_policy}).load_state(copy.deepcopy(payload))
+    candidate.validate_state(payload)
     _equal(before, candidate.checkpoint_state())
     _equal(transported, payload)
 
 
 def _restore(owner, payload, kind):
-    prepared = owner.prepare_restore(payload, factory=_factory(kind), validate_backend=_validate_backend)
+    prepared = owner.prepare_restore(
+        payload, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
+    )
     owner.install(prepared)
     return prepared
 
 
 def _find(value, key):
     if isinstance(value, Mapping):
         if key in value:
             return value[key]
@@ -255,74 +280,109 @@ def _find(value, key):
             result = _find(child, key)
             if result is not None:
                 return result
     return None
 
 
 @pytest.mark.parametrize("kind", KINDS)
 def test_private_rng_restores_global_streams(kind):
-    # Fixture positive and real learning precede the intended absent-ABI RED.
-    native = _factory(kind)(None)
+    # Genuine shared and private learning use their explicitly selected clocks.
+    native = _factory(kind, service_clock_unit="vector_tick")(None)
     before = copy.deepcopy(native.checkpoint_state())
     native_sources = type("Sources", (), {"python": random, "numpy": np.random.default_rng(13)})()
-    _, reward, after = _exercise(native, native_sources, 2, 0)
+    _, reward, after = _exercise(native, native_sources, 2, 0, clock=ws.ServiceClock("vector_tick", 0))
     assert torch.isfinite(reward).all()
     _assert_learning(before, after, kind, 1, 0)
     random.seed(17)
     random.gauss(0, 1)  # Keep a cached Gaussian in the exact global state.
     np.random.seed(19)
     np.random.normal()
     global_before = _globals(())
-    owner = _owner(kind, "world1", ("world0", "world1"))
+    rng = _rng(kind, "world1", ("world0", "world1"))
+    original_rng = rng.snapshot()
+    _, owned_type = _api()
+    owner = owned_type.construct(rng=rng, factory=_factory(kind, service_clock_unit="world_eligible_admission"))
+    _equal(original_rng, rng.snapshot())
+    constructed_rng = owner.snapshot()["rng"]
+    used = {"model_init", "predictor"} if kind == "icm" else {"target", "predictor"}
+    for component in ws.WORLD_SEED_COMPONENTS:
+        before_component = original_rng["components"][component]
+        after_component = constructed_rng["components"][component]
+        if component in used:
+            assert not torch.equal(before_component["torch_cpu"], after_component["torch_cpu"])
+            for field in before_component.keys() - {"torch_cpu"}:
+                _equal(before_component[field], after_component[field])
+        else:
+            _equal(before_component, after_component)
     _equal(global_before, _globals(()))
     initial = owner.call(lambda backend, sources: backend.checkpoint_state())
-    _, _, tail = owner.call(lambda backend, sources: _exercise(backend, sources, 1, 0))
+    _, _, tail = owner.call(
+        lambda backend, sources: _exercise(backend, sources, 1, 0, clock=ws.ServiceClock("world_eligible_admission", 1))
+    )
     tail_state = _rnd_state(tail, kind)
     assert not tail_state["optimizer"]["state"]
-    _, _, trained = owner.call(lambda backend, sources: _exercise(backend, sources, 1, 1))
+    _, _, trained = owner.call(
+        lambda backend, sources: _exercise(backend, sources, 1, 1, clock=ws.ServiceClock("world_eligible_admission", 2))
+    )
     _assert_learning(initial, trained, kind, 1, 0)
     _equal(global_before, _globals(()))
     saved = owner.snapshot()
-    continuation = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 2))
+    continuation = owner.call(
+        lambda backend, sources: _exercise(backend, sources, 2, 2, clock=ws.ServiceClock("world_eligible_admission", 4))
+    )
     _restore(owner, saved, kind)
     _equal(global_before, _globals(()))
-    replayed = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 2))
+    replayed = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 2, clock=ws.ServiceClock("world_eligible_admission", 4)))
     _equal(continuation, replayed)
     _assert_learning(initial, replayed[2], kind, 2, 0)
     _equal(global_before, _globals(()))
 
 
 @pytest.mark.parametrize("kind", KINDS)
 def test_world1_rng_independent_of_world0_calls(kind):
     global_before = _globals(())
     baseline = _owner(kind, "world1", ("world1",))
     interleaved = _owner(kind, "world1", ("spectator", "world1", "world0"))
     other = _owner(kind, "world0", ("world0", "world1"))
     _equal(baseline.snapshot(), interleaved.snapshot())
     other_before = other.snapshot()
+    admitted_position = 0
     for tick in range(3):
-        expected = baseline.call(lambda backend, sources: _exercise(backend, sources, 2, tick))
-        other.call(lambda backend, sources: _exercise(backend, sources, 2, tick))
+        admitted_position += 2
+        expected = baseline.call(
+            lambda backend, sources: _exercise(
+                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
+            )
+        )
+        other.call(
+            lambda backend, sources: _exercise(
+                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
+            )
+        )
         saved_other = other.snapshot()
         _restore(other, saved_other, kind)
-        actual = interleaved.call(lambda backend, sources: _exercise(backend, sources, 2, tick))
+        actual = interleaved.call(
+            lambda backend, sources: _exercise(
+                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
+            )
+        )
         _equal(expected, actual)
         _equal(baseline.snapshot(), interleaved.snapshot())
     with pytest.raises(AssertionError):
         _equal(other_before, other.snapshot())
     _equal(global_before, _globals(()))
 
 
 def test_native_global_rng_counterexample_and_private_continuation():
     torch.manual_seed(123)
     state = torch.get_rng_state().clone()
-    first = _factory("rnd")(None)
+    first = _factory("rnd", service_clock_unit="vector_tick")(None)
     assert not torch.equal(state, torch.get_rng_state())
-    second = _factory("rnd")(None)
+    second = _factory("rnd", service_clock_unit="vector_tick")(None)
     assert any(
         not torch.equal(a, b) for a, b in zip(first.predictor_network.parameters(), second.predictor_network.parameters(), strict=True)
     )
     rng = _rng("rnd", "world1", ("world1",))
     with rng.activate("service") as sources:
         first_draw = _draw(sources)
     saved = rng.snapshot()
     with rng.activate("service") as sources:
@@ -337,33 +397,33 @@ def test_native_global_rng_counterexample_and_private_continuation():
 @pytest.mark.parametrize("kind", KINDS)
 @pytest.mark.parametrize("after_update", [False, True])
 def test_constructor_compute_failure_restoration_and_quarantine(kind, after_update):
     rng = _rng(kind, "world1", ("world1",))
     _, owned_type = _api()
     global_before = _globals(())
 
     def broken_factory(private):
-        _factory(kind)(private)
+        _factory(kind, service_clock_unit="world_eligible_admission")(private)
         with private.activate("model_init") as sources:
             _draw(sources)
         raise KeyboardInterrupt("constructor cancellation")
 
     with pytest.raises(KeyboardInterrupt, match="constructor cancellation"):
         owned_type.construct(rng=rng, factory=broken_factory)
     _equal(global_before, _globals(()))
     owner = _owner(kind, "world1", ("world1",))
     other = _owner(kind, "world0", ("world0",))
     healthy, unaffected = owner.snapshot(), other.snapshot()
     learner_before = owner.call(lambda backend, sources: backend.checkpoint_state())
     observed = []
 
     def fail_after_update(backend, sources):
         if after_update:
-            observed.append(_learning_snapshot(_exercise(backend, sources, 2, 0)[2]))
+            observed.append(_learning_snapshot(_exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2))[2]))
         else:
             _draw(sources)
         raise RuntimeError("live callback failure")
 
     with pytest.raises(RuntimeError, match="live callback failure"):
         owner.call(fail_after_update)
     _equal(global_before, _globals(()))
     _equal(unaffected, other.snapshot())
@@ -375,19 +435,21 @@ def test_constructor_compute_failure_restoration_and_quarantine(kind, after_upda
         _equal(_rnd_state(observed[0], kind)["optimizer"], _find(diagnostic, "optimizer"))
     with pytest.raises(AssertionError):
         _equal(_find(healthy, "components"), _find(diagnostic, "components"))
     with pytest.raises(AssertionError):
         _equal(healthy, diagnostic)
     with pytest.raises((RuntimeError, ValueError), match="quarantin|failed"):
         owner.call(lambda backend, sources: backend.checkpoint_state())
     with pytest.raises((RuntimeError, ValueError)):
-        owner.prepare_restore(diagnostic, factory=_factory(kind), validate_backend=_validate_backend)
+        owner.prepare_restore(
+            diagnostic, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
+        )
     _restore(owner, healthy, kind)
-    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
     _equal(global_before, _globals(()))
 
 
 def _mutate_arrays(value):
     if isinstance(value, torch.Tensor):
         value.fill_(0)
     elif isinstance(value, np.ndarray):
         value.fill(0)
@@ -397,64 +459,68 @@ def _mutate_arrays(value):
     elif isinstance(value, (list, tuple)):
         for child in value:
             _mutate_arrays(child)
 
 
 @pytest.mark.parametrize("kind", KINDS)
 def test_owned_snapshot_restore_aliases_and_late_load_failure(kind):
     owner = _owner(kind, "world1", ("world1",))
-    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
-    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 1))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 1, clock=ws.ServiceClock("world_eligible_admission", 3)))
     saved = owner.snapshot()
     pristine = copy.deepcopy(saved)
     original_payload = copy.deepcopy(pristine)
     exposed = owner.call(lambda backend, sources: backend.checkpoint_state())
     _mutate_arrays(exposed)
     if kind == "adaptive_rnd":
         exposed["survival_history"].append(9999)
     _equal(pristine, owner.snapshot())
     _mutate_arrays(saved)
     _equal(pristine, owner.snapshot())
     second = _owner(kind, "world1", ("world1", "spectator"))
-    prepared = owner.prepare_restore(pristine, factory=_factory(kind), validate_backend=_validate_backend)
+    prepared = owner.prepare_restore(
+        pristine, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
+    )
     with pytest.raises((ValueError, RuntimeError)):
         second.install(prepared)
     owner.install(prepared)
     with pytest.raises((ValueError, RuntimeError)):
         owner.install(prepared)
     _restore(second, pristine, kind)
     stable = second.snapshot()
-    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 2))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 2, clock=ws.ServiceClock("world_eligible_admission", 4)))
     _equal(stable, second.snapshot())
     _equal(original_payload, pristine)
     before, globals_before = owner.snapshot(), _globals(())
     invalid = copy.deepcopy(pristine)
     invalid["unexpected"] = 1
     with pytest.raises((ValueError, TypeError)):
-        owner.prepare_restore(invalid, factory=_factory(kind), validate_backend=_validate_backend)
+        owner.prepare_restore(
+            invalid, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
+        )
     _equal(before, owner.snapshot())
 
     def late_factory(rng):
-        candidate = _factory(kind)(rng)
+        candidate = _factory(kind, service_clock_unit="world_eligible_admission")(rng)
         real_load = candidate.load_state
 
         def fail_load(payload):
             real_load(payload)
             torch.rand(2)
             random.gauss(0, 1)
             np.random.normal()
             raise RuntimeError("late candidate load")
 
         candidate.load_state = fail_load
         return candidate
 
     def validate_late(candidate, payload):
         # Validate genuine provider data before the intentionally late failing load.
-        _validate_backend(_factory(kind)(None), payload)
+        _validate_backend(candidate, payload)
 
     with pytest.raises(RuntimeError, match="late candidate load"):
         owner.prepare_restore(pristine, factory=late_factory, validate_backend=validate_late)
     _equal(before, owner.snapshot())
     _equal(globals_before, _globals(()))
     _equal(stable, second.snapshot())
 
 
@@ -493,17 +559,17 @@ def test_snapshot_callback_failure_restores_and_quarantines():
 
     owner.call(install_failure)
     with pytest.raises(RuntimeError, match="snapshot callback failure"):
         owner.snapshot()
     _equal(before, _globals(()))
     with pytest.raises((RuntimeError, ValueError), match="quarantin|failed"):
         owner.call(lambda backend, sources: 1)
     _restore(owner, healthy, "rnd")
-    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
     _equal(before, _globals(()))
 
 
 def test_invalid_rng_snapshot_is_pure_and_nested_components_resume():
     rng = _rng("rnd", "world1", ("world1",))
     other = _rng("rnd", "world0", ("world0",))
     saved, global_before = rng.snapshot(), _globals(())
     for field, value in (("unexpected", 1), ("world_id", "wrong"), ("components", {}), ("cuda_devices", (0,))):
@@ -683,17 +749,17 @@ print("isolated restoration custody and coordinator refusal verified")
     )
     assert result.returncode == 0, result.stdout + result.stderr
     assert "isolated restoration custody and coordinator refusal verified" in result.stdout
 
 
 @pytest.mark.parametrize("array_kind", ["plain", "structured"])
 def test_object_array_result_does_not_alias_live_adaptive_history(array_kind):
     owner = _owner("adaptive_rnd", "world1", ("world1",))
-    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
 
     def history_array(backend, sources):
         if array_kind == "plain":
             result = np.empty(1, dtype=object)
             result[0] = backend.survival_history
         else:
             result = np.empty(1, dtype=[("history", object)])
             result["history"][0] = backend.survival_history
@@ -713,18 +779,21 @@ def test_object_array_result_does_not_alias_live_adaptive_history(array_kind):
 @pytest.mark.parametrize("kind", KINDS)
 @pytest.mark.parametrize("composite_key", [False, True], ids=["native", "tuple"])
 def test_learned_adam_mapping_keys_and_values_are_owned(kind, composite_key):
     globals_before = _globals(())
     owner = _owner(kind, "world1", ("world1",))
     control = _owner(kind, "world1", ("world1",))
     initial = owner.call(lambda backend, sources: backend.checkpoint_state())
     _equal(initial, control.call(lambda backend, sources: backend.checkpoint_state()))
-    trained = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
-    _equal(trained, control.call(lambda backend, sources: _exercise(backend, sources, 2, 0)))
+    trained = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
+    _equal(
+        trained,
+        control.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2))),
+    )
     _assert_learning(initial, trained[2], kind, 1, 0)
 
     def native_adam_state(backend, sources):
         learner = backend.rnd if kind == "adaptive_rnd" else backend
         state = learner.optimizer.state
         return {("parameter", key): value for key, value in state.items()} if composite_key else state
 
     exported = owner.call(native_adam_state)
@@ -746,18 +815,20 @@ def test_learned_adam_mapping_keys_and_values_are_owned(kind, composite_key):
         moments["exp_avg"].add_(12345)
     assert not torch.equal(parameter_before, parameter)
     assert not torch.equal(moment_before, moments["exp_avg"])
     # No callback or snapshot occurs between this revision capture and comparison.
     assert owner._revision == revision_before
     _equal(before, owner.snapshot())
     _equal(globals_before, _globals(()))
     assert not parameter.requires_grad and parameter.grad_fn is None
-    continued = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 1))
-    expected = control.call(lambda backend, sources: _exercise(backend, sources, 2, 1))
+    continued = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4)))
+    expected = control.call(
+        lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4))
+    )
     _equal(expected, continued)
     _assert_learning(initial, continued[2], kind, 2, 0)
     _equal(owner.snapshot(), control.snapshot())
     _equal(globals_before, _globals(()))
 
 
 def test_true_a_b_a_nested_activation_preserves_both_streams():
     rng = _rng("rnd", "world1", ("world1",))
@@ -781,18 +852,22 @@ def test_true_a_b_a_nested_activation_preserves_both_streams():
         _equal(b2, _draw(b))
     _equal(control.snapshot(), rng.snapshot())
     _equal(globals_before, _globals(()))
 
 
 def test_stale_prepared_restore_refuses_after_real_owner_update():
     owner = _owner("rnd", "world1", ("world1",))
     initial = owner.call(lambda backend, sources: backend.checkpoint_state())
-    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0))
-    prepared = owner.prepare_restore(owner.snapshot(), factory=_factory("rnd"), validate_backend=_validate_backend)
-    _, _, updated = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 1))
+    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
+    prepared = owner.prepare_restore(
+        owner.snapshot(), factory=_factory("rnd", service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
+    )
+    _, _, updated = owner.call(
+        lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4))
+    )
     _assert_learning(initial, updated, "rnd", 2, 0)
     before, globals_before = owner.snapshot(), _globals(())
     with pytest.raises(ValueError, match="destination changed"):
         owner.install(prepared)
     _equal(updated, owner.call(lambda backend, sources: backend.checkpoint_state()))
     _equal(before, owner.snapshot())
     _equal(globals_before, _globals(()))
