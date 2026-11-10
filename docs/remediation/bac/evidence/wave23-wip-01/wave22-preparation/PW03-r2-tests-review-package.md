Previous2912e724e5bec3349e8b065b7a6e4aee6fe372ed
Test-onlycurrented02906633ded82430fb3af20c6c8f154fe40d61
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
