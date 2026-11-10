Previousreviewed2912e724e5bec3349e8b065b7a6e4aee6fe372ed
Finalfix32108b7f6a869c02e0547e6297315cc2aaabfcba
Exact5scope unchanged, Countsource nottouched.
diff --git a/src/townlet/exploration/provider_factory.py b/src/townlet/exploration/provider_factory.py
index e6c5ee98..c7355c68 100644
--- a/src/townlet/exploration/provider_factory.py
+++ b/src/townlet/exploration/provider_factory.py
@@ -42,18 +42,18 @@ def make_backend(
     Private callers pass the actual candidate received by OwnedWorldBackend.construct.
     Binding validation supports that candidate's active model_init custody; lifecycle
     snapshot/restore operations remain outside this callback. Shared ownership inputs
     must all be explicit None. The factory never selects a seed or services a queue.
     """
     policy = _validated_policy(policy)
     if type(obs_dim) is not int or obs_dim < 0:
         raise ValueError("factory observation dimension must be a nonnegative exact integer")
-    if policy.strategy in ("rnd", "adaptive_rnd", "icm") and obs_dim == 0:
-        raise ValueError("trainable curiosity requires a positive observation dimension")
+    if policy.strategy != "none" and obs_dim == 0:
+        raise ValueError("selected curiosity provider requires a positive observation dimension")
     if type(action_dim) is not int or action_dim <= 0:
         raise ValueError("factory action dimension must be a positive exact integer")
     selected_device = torch.device(device)
     if selected_device.type not in {"cpu", "cuda"}:
         raise ValueError("factory requires a CPU or CUDA destination")
     if selected_device.type == "cuda" and selected_device.index is None:
         raise ValueError("factory CUDA destination requires an explicit device index")
     cuda_devices: tuple[int, ...] = ()
diff --git a/tests/test_townlet/regressions/bac/test_pw_backend_factory.py b/tests/test_townlet/regressions/bac/test_pw_backend_factory.py
index e40a5032..8fa1d2bd 100644
--- a/tests/test_townlet/regressions/bac/test_pw_backend_factory.py
+++ b/tests/test_townlet/regressions/bac/test_pw_backend_factory.py
@@ -441,17 +441,17 @@ def test_global_policy_selector_is_independent_of_private_epsilon(strategy: str)
     assert initial == {"epsilon": policy.epsilon_start, "epsilon_decay": policy.epsilon_decay, "epsilon_min": policy.epsilon_end}
     private.decay_epsilon()
     _equal(selector.checkpoint_state(), initial)
     selector.decay_epsilon()
     assert selector.checkpoint_state()["epsilon"] < initial["epsilon"]
     _equal(another_selector.checkpoint_state(), initial)
 
 
-@pytest.mark.parametrize("strategy", ("none", "count_based"))
+@pytest.mark.parametrize("strategy", ("none",))
 @pytest.mark.parametrize("scope", ("shared", "per_world"))
 def test_nonrandom_zero_column_geometry_remains_supported(strategy: str, scope: str) -> None:
     policy = _policy(strategy, scope)
     arguments = _arguments(policy)
     arguments["obs_dim"] = 0
     if scope == "per_world":
         arguments["descriptor"] = _descriptor(policy, obs_dim=0)
         arguments["rng"] = _rng(arguments["descriptor"], "alpha")
@@ -498,8 +498,33 @@ def test_active_different_owner_refuses_even_with_identical_binding(strategy: st
     another_before = another.snapshot()
     ambient_before = _ambient()
     with another.activate("model_init"):
         with pytest.raises(RuntimeError):
             factory.make_backend(policy, **arguments)
     _equal(arguments["rng"].snapshot(), before)
     _equal(another.snapshot(), another_before)
     _equal(_ambient(), ambient_before)
+
+
+@pytest.mark.parametrize("scope", ("shared", "per_world"))
+def test_count_zero_width_refuses_before_allocation_or_draws(scope: str, monkeypatch: pytest.MonkeyPatch) -> None:
+    policy = _policy("count_based", scope)
+    arguments = _arguments(policy)
+    arguments["obs_dim"] = 0
+    if scope == "per_world":
+        arguments["descriptor"] = _descriptor(policy, obs_dim=0)
+        arguments["rng"] = _rng(arguments["descriptor"], "alpha")
+    before = arguments["rng"].snapshot() if arguments["rng"] is not None else None
+    ambient_before = _ambient()
+    constructor_calls = []
+
+    def forbidden_constructor(*args: Any, **kwargs: Any) -> None:
+        constructor_calls.append(True)
+        raise AssertionError("zero-width Count must refuse before provider allocation")
+
+    monkeypatch.setattr(CountExploration, "__init__", forbidden_constructor)
+    with pytest.raises(ValueError):
+        _factory().make_backend(policy, **arguments)
+    assert constructor_calls == []
+    if arguments["rng"] is not None:
+        _equal(arguments["rng"].snapshot(), before)
+    _equal(_ambient(), ambient_before)
