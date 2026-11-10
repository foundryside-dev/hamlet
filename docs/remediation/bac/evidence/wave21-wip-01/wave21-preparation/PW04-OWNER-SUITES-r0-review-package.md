# Actual fiveowner-testmigration delta

Base 7e702ab885c2bc1bba37652273cfb89742624f08; currenttree 04d822c62185771e689b38f5d84804ec0ef9b5a8. Exactly5wholefiles/2595actual<=3200, no6thprovider/helper/source. All151oldcases+actualcurrentnative/negative/refusal coveragepreserved; explicitconstructorinputs. Coreproductionbyteunchanged; allsource/tests/index/trackeddocsfrozen.

```diff
diff --git a/tests/test_townlet/regressions/bac/test_icm_provider.py b/tests/test_townlet/regressions/bac/test_icm_provider.py
index 07d9a411..1accff94 100644
--- a/tests/test_townlet/regressions/bac/test_icm_provider.py
+++ b/tests/test_townlet/regressions/bac/test_icm_provider.py
@@ -48,7 +48,9 @@ def _provider(parameters, service_mode, overflow_policy):
     assert util.find_spec("townlet.exploration.icm") is not None, "transition-based ICM provider is missing"
     provider_type = import_module("townlet.exploration.icm").ICMExploration
     policy = _policy(parameters, service_mode, overflow_policy)
-    provider = provider_type(policy, obs_dim=3, action_dim=2, **parameters, device=torch.device("cpu"))
+    provider = provider_type(
+        policy, rng=None, service_clock_unit="vector_tick", obs_dim=3, action_dim=2, **parameters, device=torch.device("cpu")
+    )
     with torch.no_grad():
         for module in (provider.encoder, provider.inverse_model, provider.forward_model):
             for index, parameter in enumerate(module.parameters()):
@@ -116,6 +118,8 @@ def test_icm_uses_action_and_successor():
     provider = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
     context = _rows(2, 0)
     before = deepcopy(provider.checkpoint_state())
+    assert before["schema"] == "icm-state-v2"
+    assert before["service_clock_unit"] == "vector_tick"
     reward = provider.compute_transition_novelty(context, update_stats=False)
     _, expected = _objective(provider, context, PARAMETERS)
     torch.testing.assert_close(reward, expected.detach())
@@ -294,7 +298,15 @@ def test_icm_constructor_cannot_override_selected_policy(name, value):
     provider_type = type(_provider(PARAMETERS, "paced_fifo", "service_before_admit"))
     policy = _policy(PARAMETERS, "paced_fifo", "service_before_admit")
     with pytest.raises((TypeError, ValueError)):
-        provider_type(policy, obs_dim=3, action_dim=2, **{**PARAMETERS, name: value}, device=torch.device("cpu"))
+        provider_type(
+            policy,
+            rng=None,
+            service_clock_unit="vector_tick",
+            obs_dim=3,
+            action_dim=2,
+            **{**PARAMETERS, name: value},
+            device=torch.device("cpu"),
+        )
 
 
 @pytest.mark.parametrize(
diff --git a/tests/test_townlet/regressions/bac/test_rnd_service.py b/tests/test_townlet/regressions/bac/test_rnd_service.py
index 0bf86ae9..500b2556 100644
--- a/tests/test_townlet/regressions/bac/test_rnd_service.py
+++ b/tests/test_townlet/regressions/bac/test_rnd_service.py
@@ -10,7 +10,7 @@ from townlet.exploration.rnd import RNDExploration
 
 
 def provider(batch, capacity, mode, overflow):
-    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=batch)
+    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=batch)
     assert hasattr(rnd, "configure_service"), "bounded RND service interface missing"
     rnd.configure_service(RNDOptions(service_mode=mode, max_updates_per_tick=1, max_pending_rows=capacity, overflow_policy=overflow))
     return rnd
@@ -144,7 +144,7 @@ def test_malformed_state_is_atomic(damage):
     elif damage == "count":
         service["admitted_rows"] += 1
     elif damage == "clock":
-        service["paced_updates_this_tick"] = 2
+        service["ordinary_updates_at_position"] = 2
     elif damage == "normalizer":
         bad["reward_rms_var"] = -1
     elif damage == "network":
@@ -157,7 +157,7 @@ def test_malformed_state_is_atomic(damage):
 
 
 def test_service_options_are_explicit_and_buffer_admission_validated():
-    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     assert hasattr(rnd, "configure_service"), "bounded RND service interface missing"
     with pytest.raises(ValueError):
         rnd.configure_service(RNDOptions(service_mode="paced_fifo"))
@@ -171,31 +171,42 @@ def test_service_options_are_explicit_and_buffer_admission_validated():
         equal(before, rnd.checkpoint_state())
 
 
-def test_direct_minibatch_and_explicit_legacy_available_state():
-    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+def test_direct_minibatch_and_current_native_state_refuse_diagnostic_import():
+    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     rnd.update({"observations": rows(7)})
-    assert len(rnd.obs_buffer) == 4  # Preserve working legacy one-minibatch update API.
+    assert len(rnd.obs_buffer) == 4  # Preserve current one-minibatch direct update API.
     assert rnd.update_predictor() > 0
     assert len(rnd.obs_buffer) == 1
     assert hasattr(rnd, "available_state"), "explicit available-state export missing"
-    legacy = rnd.available_state()
-    assert "predictor_service" not in legacy
-    restored = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
-    restored.load_available_state(legacy)
-    equal(legacy, restored.available_state())
-    assert restored.obs_buffer == []
-    restored.load_state(legacy)  # Exact historical schema remains a supported public API.
-    equal(legacy, restored.available_state())
-    rnd.load_state(legacy)
-    equal(torch.stack(rnd.obs_buffer), rows(7)[6:])  # Historical import never invents or discards destination tails.
+    diagnostic = rnd.available_state()
+    assert "predictor_service" not in diagnostic
+    restored = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
+    assert not hasattr(restored, "load_available_state")
+    for current in (rnd, restored):
+        before = current.checkpoint_state()
+        for operation in (current.validate_state, current.prepare_state, current.load_state):
+            with pytest.raises(ValueError):
+                operation(diagnostic)
+            equal(before, current.checkpoint_state())
+    native = rnd.checkpoint_state()
+    assert native["schema"] == "rnd-state-v2"
+    assert native["predictor_service"]["version"] == 2
+    assert native["predictor_service"]["service_clock_unit"] == "vector_tick"
+    restored.load_state(native)
+    equal(native, restored.checkpoint_state())
+    equal(diagnostic, restored.available_state())
+    equal(torch.stack(restored.obs_buffer), rows(7)[6:])
+    for current in (rnd, restored):
+        current.update({"observations": rows(2)})
+    equal(rnd.checkpoint_state(), restored.checkpoint_state())
     with pytest.raises(ValueError):
-        restored.load_state({**legacy, "misspelled_service": {}})
+        restored.load_state({**native, "misspelled_service": {}})
 
 
 def test_invalid_minibatch_refuses_before_allocation():
     for batch in (0, -1, True, 1.5):
         with pytest.raises(ValueError):
-            RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=batch)
+            RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=batch)
 
 
 @pytest.mark.parametrize("damage", ["negative_moment", "orphan_moment", "fractional_batch", "false_clock_count"])
@@ -211,11 +222,11 @@ def test_corrupt_optimizer_and_service_metadata_are_atomic(damage):
     elif damage == "fractional_batch":
         bad["predictor_service"]["training_batch_size"] = 3.0
     else:
-        bad["predictor_service"]["paced_updates_this_tick"] = 1
+        bad["predictor_service"]["ordinary_updates_at_position"] = 1
         bad["predictor_service"]["optimizer_updates"] = 0
         bad["predictor_service"]["consumed_rows"] = 0
         bad["predictor_service"]["admitted_rows"] = 2
-        bad["predictor_service"]["vector_tick"] = 2
+        bad["predictor_service"]["service_position"] = 2
     with pytest.raises(ValueError):
         rnd.load_state(bad)
     equal(before, rnd.checkpoint_state())
@@ -374,15 +385,28 @@ def test_optimizer_continuation_refuses_corruption_before_install(damage):
 
 
 @pytest.mark.parametrize("historical_updates", [0, 3])
-def test_historical_optimizer_history_aligns_with_existing_service_counts(historical_updates):
+def test_current_native_manual_optimizer_history_replaces_existing_service_counts(historical_updates):
     source = provider(3, 9, "occupancy_fifo", "service_before_admit")
-    for tick in range(historical_updates):
-        source.admit_and_service(rows(3), vector_tick=tick)
+    for _ in range(historical_updates):
+        loss = (source.predictor_network(rows(3)) - source.fixed_network(rows(3))).square().mean()
+        source.optimizer.zero_grad()
+        loss.backward()
+        source.optimizer.step()
+    source.obs_buffer.extend(rows(2).unbind())
+    assert source.update_predictor() == 0.0
     destination = provider(3, 9, "occupancy_fifo", "service_before_admit")
     destination.admit_and_service(rows(8), vector_tick=3)
-    destination.load_state(source.available_state())
+    before = destination.checkpoint_state()
+    for operation in (destination.validate_state, destination.prepare_state, destination.load_state):
+        with pytest.raises(ValueError):
+            operation(source.available_state())
+        equal(before, destination.checkpoint_state())
+    destination.load_state(source.checkpoint_state())
     state = destination.checkpoint_state()
-    assert state["predictor_service"]["optimizer_updates"] == 2
+    equal(source.checkpoint_state(), state)
+    assert before["predictor_service"]["optimizer_updates"] == 2
+    assert state["predictor_service"]["optimizer_updates"] == 0
+    assert state["predictor_service"]["optimizer_step_offset"] == historical_updates
     restored = provider(3, 9, "occupancy_fifo", "service_before_admit")
     restored.load_state(state)
     equal(state, restored.checkpoint_state())
@@ -433,7 +457,7 @@ def service_counter_values(snapshot):
 
 
 def test_public_predictor_counters_follow_genuine_legacy_optimizer_work():
-    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     before = copy.deepcopy(rnd.predictor_network.state_dict())
     steps = []
     handle = rnd.optimizer.register_step_post_hook(lambda *_: steps.append(1))
@@ -450,7 +474,7 @@ def test_public_predictor_counters_follow_genuine_legacy_optimizer_work():
 
 
 def test_public_predictor_counters_bracket_legacy_partial_and_full_direct_updates():
-    rnd = RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+    rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     rnd.obs_buffer.extend(rows(2).unbind())
     assert rnd.update_predictor() == 0.0
     assert rnd.optimizer.state == {}
@@ -480,7 +504,7 @@ def test_public_predictor_counters_count_real_zero_loss_steps(configured):
     rnd = (
         provider(3, 9, "paced_fifo", "service_before_admit")
         if configured
-        else RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+        else RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     )
     rnd.predictor_network.load_state_dict(rnd.fixed_network.state_dict())
     steps = []
@@ -544,7 +568,7 @@ def test_public_predictor_counters_are_frozen_owned_primitives_and_observational
     rnd = (
         provider(3, 9, "paced_fifo", "service_before_admit")
         if configured
-        else RNDExploration(obs_dim=2, embed_dim=3, training_batch_size=3)
+        else RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=2, embed_dim=3, training_batch_size=3)
     )
     rnd.update({"observations": rows(5)})
     before = rnd.checkpoint_state()  # One test oracle, never the per-step accounting path.
diff --git a/tests/test_townlet/unit/exploration/test_exploration_strategies.py b/tests/test_townlet/unit/exploration/test_exploration_strategies.py
index 774cbbdc..d7c14de0 100644
--- a/tests/test_townlet/unit/exploration/test_exploration_strategies.py
+++ b/tests/test_townlet/unit/exploration/test_exploration_strategies.py
@@ -273,7 +273,7 @@ class TestRNDNetworkInitialization:
 
     def test_fixed_network_is_frozen(self):
         """Fixed network should have requires_grad=False for all parameters."""
-        rnd = RNDExploration(obs_dim=10, embed_dim=8, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, embed_dim=8, device=torch.device("cpu"))
 
         # Check all fixed network parameters are frozen
         for param in rnd.fixed_network.parameters():
@@ -281,7 +281,7 @@ class TestRNDNetworkInitialization:
 
     def test_predictor_network_is_trainable(self):
         """Predictor network should have requires_grad=True."""
-        rnd = RNDExploration(obs_dim=10, embed_dim=8, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, embed_dim=8, device=torch.device("cpu"))
 
         # Check predictor network parameters are trainable
         trainable_params = [p for p in rnd.predictor_network.parameters() if p.requires_grad]
@@ -289,7 +289,7 @@ class TestRNDNetworkInitialization:
 
     def test_networks_have_different_weights(self):
         """Fixed and predictor should start with different random weights."""
-        rnd = RNDExploration(obs_dim=10, embed_dim=8, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, embed_dim=8, device=torch.device("cpu"))
 
         # Get first layer weights
         fixed_weight = list(rnd.fixed_network.parameters())[0]
@@ -305,7 +305,9 @@ class TestRNDIntrinsicRewardComputation:
     @pytest.fixture
     def rnd(self):
         """Create RND exploration with small networks."""
-        return RNDExploration(obs_dim=10, embed_dim=8, learning_rate=0.01, device=torch.device("cpu"))
+        return RNDExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=10, embed_dim=8, learning_rate=0.01, device=torch.device("cpu")
+        )
 
     def test_intrinsic_rewards_are_nonnegative(self, rnd):
         """Prediction errors (MSE) should always be non-negative."""
@@ -351,12 +353,12 @@ class TestRNDBufferAccumulation:
 
     def test_buffer_starts_empty(self):
         """Buffer should be empty on initialization."""
-        rnd = RNDExploration(obs_dim=10, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, device=torch.device("cpu"))
         assert len(rnd.obs_buffer) == 0
 
     def test_update_adds_to_buffer(self):
         """update() should add observations to buffer."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
 
         batch = {"observations": torch.randn(3, 10)}
         rnd.update(batch)
@@ -366,7 +368,7 @@ class TestRNDBufferAccumulation:
 
     def test_update_without_observations_key(self):
         """update() should handle missing 'observations' gracefully."""
-        rnd = RNDExploration(obs_dim=10, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, device=torch.device("cpu"))
 
         batch = {"actions": torch.randint(0, 6, (3,))}
         rnd.update(batch)  # Should not crash
@@ -376,7 +378,7 @@ class TestRNDBufferAccumulation:
 
     def test_buffer_accumulates_across_updates(self):
         """Multiple update() calls should accumulate observations."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=20, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=20, device=torch.device("cpu"))
 
         # Add observations in batches
         rnd.update({"observations": torch.randn(5, 10)})
@@ -394,7 +396,7 @@ class TestRNDPredictorTraining:
 
     def test_update_predictor_requires_minimum_buffer_size(self):
         """Should return 0.0 when buffer is too small."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
 
         # Add only 5 observations (less than batch size of 10)
         rnd.update({"observations": torch.randn(5, 10)})
@@ -405,7 +407,7 @@ class TestRNDPredictorTraining:
 
     def test_update_predictor_clears_buffer(self):
         """After training, buffer should be cleared."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=10, device=torch.device("cpu"))
 
         # Manually add to buffer (bypass update() auto-training)
         for _ in range(10):
@@ -421,7 +423,7 @@ class TestRNDPredictorTraining:
 
     def test_update_predictor_keeps_excess_observations(self):
         """Observations beyond batch size should remain in buffer."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=5, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=5, device=torch.device("cpu"))
 
         # Manually add 8 observations (bypass update() auto-training)
         for _ in range(8):
@@ -440,6 +442,8 @@ class TestRNDPredictorTraining:
         torch.manual_seed(123)
 
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             embed_dim=8,
             learning_rate=0.01,
@@ -469,7 +473,7 @@ class TestRNDPredictorTraining:
 
     def test_update_triggers_training_automatically(self):
         """update() should automatically call update_predictor when buffer full."""
-        rnd = RNDExploration(obs_dim=10, training_batch_size=5, device=torch.device("cpu"))
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=10, training_batch_size=5, device=torch.device("cpu"))
 
         # Add exactly batch_size observations
         observations = torch.randn(5, 10)
@@ -492,6 +496,8 @@ class TestRNDLearningBehavior:
         torch.manual_seed(123)
 
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             embed_dim=8,
             learning_rate=0.1,
@@ -521,6 +527,8 @@ class TestRNDLearningBehavior:
         torch.manual_seed(456)
 
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             embed_dim=8,
             learning_rate=0.1,
@@ -551,6 +559,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_should_not_anneal_with_insufficient_data(self):
         """Should not anneal before survival_window filled."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             survival_window=100,
             variance_threshold=100.0,
@@ -568,6 +578,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_should_not_anneal_with_high_variance(self):
         """Should not anneal when survival variance is high."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             survival_window=100,
             variance_threshold=100.0,
@@ -585,6 +597,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_should_not_anneal_consistent_failure(self):
         """Should NOT anneal when consistently failing (low variance, low survival)."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             survival_window=100,
             variance_threshold=100.0,
@@ -603,6 +617,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_should_anneal_consistent_success(self):
         """Should anneal when consistently succeeding (low variance, high survival)."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             survival_window=100,
             variance_threshold=100.0,
@@ -624,6 +640,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_anneal_weight_exponential_decay(self):
         """anneal_weight should apply exponential decay."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             initial_intrinsic_weight=1.0,
             decay_rate=0.9,
@@ -646,6 +664,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_anneal_weight_respects_minimum(self):
         """anneal_weight should not go below minimum."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             initial_intrinsic_weight=0.15,
             decay_rate=0.5,
@@ -664,6 +684,8 @@ class TestAdaptiveIntrinsicAnnealingLogic:
     def test_update_on_episode_end_maintains_window(self):
         """update_on_episode_end should maintain sliding window."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             survival_window=10,
             device=torch.device("cpu"),
@@ -685,6 +707,8 @@ class TestAdaptiveIntrinsicActionSelection:
     def test_select_actions_delegates_to_rnd(self):
         """select_actions should delegate to RND."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             epsilon_start=0.0,  # Greedy for deterministic test
             device=torch.device("cpu"),
@@ -722,6 +746,8 @@ class TestAdaptiveIntrinsicRNDUpdate:
     def test_update_delegates_to_rnd(self):
         """update should delegate to RND predictor."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             rnd_training_batch_size=4,
             device=torch.device("cpu"),
@@ -745,6 +771,8 @@ class TestAdaptiveIntrinsicEpsilonDecay:
     def test_decay_epsilon_delegates_to_rnd(self):
         """decay_epsilon should delegate to RND."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             epsilon_start=1.0,
             epsilon_decay=0.9,
@@ -770,6 +798,8 @@ class TestAdaptiveIntrinsicStatePersistence:
     def test_checkpoint_state_includes_all_config(self):
         """checkpoint_state should include RND state and annealing config."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             initial_intrinsic_weight=0.7,
             min_intrinsic_weight=0.05,
@@ -797,27 +827,67 @@ class TestAdaptiveIntrinsicStatePersistence:
         assert abs(state["survival_history"][1] - 110.0) < 0.1
 
     def test_load_state_restores_all_config(self):
-        """load_state should restore RND and annealing config."""
+        """Current native state restores into matching selected configuration."""
+
+        def assert_native_equal(actual, expected):
+            if isinstance(expected, torch.Tensor):
+                torch.testing.assert_close(actual, expected, rtol=0, atol=0)
+            elif isinstance(expected, dict):
+                assert actual.keys() == expected.keys()
+                for key in expected:
+                    assert_native_equal(actual[key], expected[key])
+            elif isinstance(expected, (list, tuple)):
+                assert len(actual) == len(expected)
+                for first, second in zip(actual, expected, strict=True):
+                    assert_native_equal(first, second)
+            else:
+                assert actual == expected
+
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             device=torch.device("cpu"),
         )
 
-        # Create state to load
-        rnd_state = exploration.rnd.checkpoint_state()
-        new_state = {
-            "rnd_state": rnd_state,
-            "current_intrinsic_weight": 0.3,
+        selected = {
             "min_intrinsic_weight": 0.01,
             "variance_threshold": 25.0,
             "survival_window": 150,
             "decay_rate": 0.97,
             "min_survival_fraction": 0.5,
             "max_episode_length": 1000,
-            "survival_history": [50.0, 60.0, 70.0],
         }
-
+        source = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=10, device=torch.device("cpu"), **selected
+        )
+        for survival in (50.0, 60.0, 70.0):
+            source.update_on_episode_end(survival)
+        source.current_intrinsic_weight = 0.3
+        source.update({"observations": torch.randn(128, 10)})
+        new_state = source.checkpoint_state()
+        assert new_state["schema"] == "adaptive-intrinsic-state-v2"
+        assert new_state["rnd_state"]["schema"] == "rnd-state-v2"
+        before = exploration.checkpoint_state()
+        for operation in (exploration.validate_state, exploration.prepare_state, exploration.load_state):
+            with pytest.raises(ValueError, match="configuration differs from destination"):
+                operation(new_state)
+            assert_native_equal(exploration.checkpoint_state(), before)
+        exploration = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=10, device=torch.device("cpu"), **selected
+        )
+        incomplete = {
+            key: value
+            for key, value in new_state.items()
+            if key not in {"schema", "initial_intrinsic_weight", "min_survival_for_annealing"}
+        }
+        before = exploration.checkpoint_state()
+        for operation in (exploration.validate_state, exploration.prepare_state, exploration.load_state):
+            with pytest.raises(ValueError, match="complete current native state"):
+                operation(incomplete)
+            assert_native_equal(exploration.checkpoint_state(), before)
         exploration.load_state(new_state)
+        assert_native_equal(exploration.checkpoint_state(), new_state)
 
         # Should have updated all fields
         assert abs(exploration.current_intrinsic_weight - 0.3) < 1e-6
@@ -828,10 +898,16 @@ class TestAdaptiveIntrinsicStatePersistence:
         assert abs(exploration.min_survival_fraction - 0.5) < 1e-6
         assert exploration.max_episode_length == 1000
         assert exploration.survival_history == [50.0, 60.0, 70.0]
+        continuation = {"observations": torch.randn(128, 10)}
+        source.update(continuation)
+        exploration.update(continuation)
+        assert_native_equal(exploration.checkpoint_state(), source.checkpoint_state())
 
     def test_checkpoint_restore_roundtrip(self):
         """Checkpoint and restore should preserve exact state."""
         original = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             initial_intrinsic_weight=0.42,
             min_intrinsic_weight=0.08,
@@ -851,7 +927,18 @@ class TestAdaptiveIntrinsicStatePersistence:
         state = original.checkpoint_state()
 
         # Create new exploration and restore
-        restored = AdaptiveIntrinsicExploration(obs_dim=10, device=torch.device("cpu"))
+        restored = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
+            obs_dim=10,
+            initial_intrinsic_weight=0.42,
+            min_intrinsic_weight=0.08,
+            variance_threshold=75.0,
+            survival_window=80,
+            decay_rate=0.88,
+            epsilon_start=0.8,
+            device=torch.device("cpu"),
+        )
         restored.load_state(state)
 
         # Should match original
@@ -872,6 +959,8 @@ class TestAdaptiveIntrinsicWeightGetter:
     def test_get_intrinsic_weight_returns_current_value(self):
         """get_intrinsic_weight should return current weight."""
         exploration = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=10,
             initial_intrinsic_weight=0.65,
             device=torch.device("cpu"),
@@ -896,6 +985,8 @@ class TestRNDCheckpointCompleteness:
     def test_rnd_saves_predictor_optimizer(self, cpu_device, basic_env):
         """RND should save predictor optimizer state."""
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             embed_dim=128,
             learning_rate=1e-4,
@@ -909,6 +1000,8 @@ class TestRNDCheckpointCompleteness:
     def test_rnd_saves_epsilon(self, cpu_device, basic_env):
         """RND should save epsilon decay parameters."""
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             epsilon_start=0.8,
             epsilon_min=0.05,
@@ -927,6 +1020,8 @@ class TestRNDCheckpointCompleteness:
     def test_rnd_saves_network_architecture_params(self, cpu_device, basic_env):
         """RND should save architecture parameters for reconstruction."""
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             embed_dim=256,
             device=cpu_device,
@@ -940,7 +1035,7 @@ class TestRNDCheckpointCompleteness:
 
     def test_rnd_saves_network_weights(self, cpu_device, basic_env):
         """RND should save both fixed and predictor network weights."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
 
         state = rnd.checkpoint_state()
         assert "fixed_network" in state, "RND checkpoint must include fixed_network"
@@ -952,7 +1047,9 @@ class TestRNDCheckpointCompleteness:
 
     def test_rnd_restores_epsilon(self, cpu_device, basic_env):
         """RND should restore epsilon from checkpoint."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, epsilon_start=1.0, device=cpu_device)
+        rnd = RNDExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, epsilon_start=1.0, device=cpu_device
+        )
 
         # Decay epsilon
         for _ in range(10):
@@ -962,14 +1059,16 @@ class TestRNDCheckpointCompleteness:
         state = rnd.checkpoint_state()
 
         # Create new RND and restore
-        rnd2 = RNDExploration(obs_dim=basic_env.observation_dim, epsilon_start=1.0, device=cpu_device)
+        rnd2 = RNDExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, epsilon_start=1.0, device=cpu_device
+        )
         rnd2.load_state(state)
 
         assert abs(rnd2.epsilon - decayed_epsilon) < 1e-6, "Epsilon should be restored"
 
     def test_rnd_restores_network_weights(self, cpu_device, basic_env):
         """RND should restore network weights from checkpoint."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
 
         # Train predictor on some data
         obs = torch.randn(128, basic_env.observation_dim, device=cpu_device)
@@ -984,7 +1083,7 @@ class TestRNDCheckpointCompleteness:
         state = rnd.checkpoint_state()
 
         # Create new RND and restore
-        rnd2 = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd2 = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
         rnd2.load_state(state)
 
         # Networks should produce same output
@@ -996,7 +1095,9 @@ class TestRNDCheckpointCompleteness:
 
     def test_rnd_restores_optimizer_state(self, cpu_device, basic_env):
         """RND should restore optimizer state from checkpoint."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, learning_rate=1e-3, device=cpu_device)
+        rnd = RNDExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, learning_rate=1e-3, device=cpu_device
+        )
 
         # Train for a few steps to build optimizer state
         for _ in range(5):
@@ -1013,7 +1114,9 @@ class TestRNDCheckpointCompleteness:
         optimizer_state_keys = set(state["optimizer"]["state"].keys())
 
         # Create new RND and restore
-        rnd2 = RNDExploration(obs_dim=basic_env.observation_dim, learning_rate=1e-3, device=cpu_device)
+        rnd2 = RNDExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, learning_rate=1e-3, device=cpu_device
+        )
         rnd2.load_state(state)
 
         # Optimizer should have same state
@@ -1027,6 +1130,8 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
     def test_adaptive_saves_intrinsic_weight(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should save current intrinsic weight."""
         adaptive = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             initial_intrinsic_weight=0.5,
             device=cpu_device,
@@ -1039,6 +1144,8 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
     def test_adaptive_saves_annealing_params(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should save all annealing parameters."""
         adaptive = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             variance_threshold=50.0,
             survival_window=200,
@@ -1059,7 +1166,9 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
 
     def test_adaptive_saves_survival_history(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should save survival history for annealing."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         # Simulate some survival times
         adaptive.survival_history = [10.0, 20.0, 30.0, 40.0, 50.0]
@@ -1070,7 +1179,9 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
 
     def test_adaptive_saves_rnd_state(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should save underlying RND state."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         state = adaptive.checkpoint_state()
         assert "rnd_state" in state
@@ -1084,6 +1195,8 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
     def test_adaptive_restores_intrinsic_weight(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should restore intrinsic weight from checkpoint."""
         adaptive = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=basic_env.observation_dim,
             initial_intrinsic_weight=1.0,
             device=cpu_device,
@@ -1095,14 +1208,18 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
         state = adaptive.checkpoint_state()
 
         # Create new instance and restore
-        adaptive2 = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive2 = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
         adaptive2.load_state(state)
 
         assert abs(adaptive2.current_intrinsic_weight - 0.3) < 1e-6
 
     def test_adaptive_restores_survival_history(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should restore survival history from checkpoint."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         # Set survival history
         adaptive.survival_history = [15.0, 25.0, 35.0]
@@ -1110,14 +1227,18 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
         state = adaptive.checkpoint_state()
 
         # Create new instance and restore
-        adaptive2 = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive2 = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
         adaptive2.load_state(state)
 
         assert adaptive2.survival_history == [15.0, 25.0, 35.0]
 
     def test_adaptive_restores_rnd_state(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should restore RND state from checkpoint."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         # Train RND predictor
         obs = torch.randn(128, basic_env.observation_dim, device=cpu_device)
@@ -1130,7 +1251,9 @@ class TestAdaptiveIntrinsicCheckpointCompleteness:
 
         # Save and restore
         state = adaptive.checkpoint_state()
-        adaptive2 = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive2 = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
         adaptive2.load_state(state)
 
         # Predictor should produce same output
@@ -1143,7 +1266,7 @@ class TestCheckpointRoundTrip:
 
     def test_rnd_roundtrip_preserves_behavior(self, cpu_device, basic_env):
         """RND should have identical behavior after save/restore."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
 
         # Train predictor
         for _ in range(5):
@@ -1157,7 +1280,7 @@ class TestCheckpointRoundTrip:
 
         # Save and restore
         state = rnd.checkpoint_state()
-        rnd2 = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd2 = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
         rnd2.load_state(state)
 
         # Compute intrinsic rewards after restore
@@ -1168,7 +1291,9 @@ class TestCheckpointRoundTrip:
 
     def test_adaptive_roundtrip_preserves_behavior(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should have identical behavior after save/restore."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         # Train and anneal
         for _ in range(3):
@@ -1185,7 +1310,9 @@ class TestCheckpointRoundTrip:
 
         # Save and restore
         state = adaptive.checkpoint_state()
-        adaptive2 = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive2 = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
         adaptive2.load_state(state)
 
         # Compute intrinsic rewards after restore
@@ -1201,26 +1328,30 @@ class TestCheckpointStrictValidation:
 
     def test_rnd_rejects_missing_optimizer(self, cpu_device, basic_env):
         """RND should reject checkpoints without optimizer state."""
-        rnd = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
 
         state = rnd.checkpoint_state()
         # Simulate legacy checkpoint without optimizer
         del state["optimizer"]
 
-        # Should raise KeyError (strict validation)
-        rnd2 = RNDExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
-        with pytest.raises(KeyError):
+        # Current exact-key validation refuses missing optimizer state.
+        rnd2 = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device)
+        with pytest.raises(ValueError, match="complete current rnd-state-v2 checkpoint"):
             rnd2.load_state(state)
 
     def test_adaptive_rejects_missing_survival_history(self, cpu_device, basic_env):
         """AdaptiveIntrinsic should reject checkpoints without survival history."""
-        adaptive = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
+        adaptive = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
 
         state = adaptive.checkpoint_state()
         # Simulate legacy checkpoint without survival history
         del state["survival_history"]
 
-        # Should raise KeyError (strict validation)
-        adaptive2 = AdaptiveIntrinsicExploration(obs_dim=basic_env.observation_dim, device=cpu_device)
-        with pytest.raises(KeyError):
+        # Current exact-key validation refuses missing history.
+        adaptive2 = AdaptiveIntrinsicExploration(
+            rng=None, service_clock_unit="vector_tick", obs_dim=basic_env.observation_dim, device=cpu_device
+        )
+        with pytest.raises(ValueError, match="complete current native state"):
             adaptive2.load_state(state)
diff --git a/tests/test_townlet/unit/exploration/test_rnd_normalization.py b/tests/test_townlet/unit/exploration/test_rnd_normalization.py
index 41a490c0..f5a64bba 100644
--- a/tests/test_townlet/unit/exploration/test_rnd_normalization.py
+++ b/tests/test_townlet/unit/exploration/test_rnd_normalization.py
@@ -23,6 +23,8 @@ class TestRNDNormalization:
         device = torch.device("cpu")
 
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=obs_dim,
             embed_dim=embed_dim,
             device=device,
@@ -69,6 +71,8 @@ class TestRNDNormalization:
         device = torch.device("cpu")
 
         rnd = RNDExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=obs_dim,
             embed_dim=embed_dim,
             device=device,
@@ -105,7 +109,7 @@ class TestRNDNormalization:
         device = torch.device("cpu")
 
         # Create RND and warmup
-        rnd1 = RNDExploration(obs_dim=obs_dim, embed_dim=embed_dim, device=device)
+        rnd1 = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=obs_dim, embed_dim=embed_dim, device=device)
 
         for _ in range(5):
             observations = torch.randn(100, obs_dim, device=device)
@@ -116,7 +120,7 @@ class TestRNDNormalization:
         checkpoint = rnd1.checkpoint_state()
 
         # Create new RND and load checkpoint
-        rnd2 = RNDExploration(obs_dim=obs_dim, embed_dim=embed_dim, device=device)
+        rnd2 = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=obs_dim, embed_dim=embed_dim, device=device)
         rnd2.load_state(checkpoint)
 
         # Compute rewards on same observations
@@ -145,6 +149,8 @@ class TestAdaptiveIntrinsicDoubleWeighting:
         device = torch.device("cpu")
 
         adaptive = AdaptiveIntrinsicExploration(
+            rng=None,
+            service_clock_unit="vector_tick",
             obs_dim=obs_dim,
             embed_dim=embed_dim,
             initial_intrinsic_weight=0.7,
diff --git a/tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py b/tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py
index a35dd428..f5b37905 100644
--- a/tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py
+++ b/tests/test_townlet/unit/exploration/test_rnd_stats_update_timing.py
@@ -22,7 +22,7 @@ class TestRNDStatsUpdateTiming:
         """
         device = torch.device("cpu")
         obs_dim = 29
-        rnd = RNDExploration(obs_dim=obs_dim, device=device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=obs_dim, device=device)
 
         # Record initial variance
         initial_var = rnd.reward_rms.var
@@ -45,7 +45,7 @@ class TestRNDStatsUpdateTiming:
         """Test that RND stats don't update when update_stats=False (eval mode)."""
         device = torch.device("cpu")
         obs_dim = 29
-        rnd = RNDExploration(obs_dim=obs_dim, device=device)
+        rnd = RNDExploration(rng=None, service_clock_unit="vector_tick", obs_dim=obs_dim, device=device)
 
         # Warmup: establish some statistics
         warmup_obs = torch.randn(100, obs_dim, device=device)

```
