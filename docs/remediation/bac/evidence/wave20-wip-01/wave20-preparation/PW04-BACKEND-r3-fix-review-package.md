# Actual source fixround1 delta R1→R3

PreviousactualreviewedR1tree 82b428748d2de3f46caca601893cb3308cdbb91a; currentfixedtree ee8d22825ab3b28fd72d9e00fc7a869bbb8d4ba6. Same4wholefiles/3042actual<=4050; newtest includes48newadversarial andexplicitstaletokenfixturecorrection. Remainingproductioncaller/schema/fullrunner gapsrequiredOPEN; no integrationrelease. Rootfixqualificationactualresultsfollowafterfreeze.

```diff
diff --git a/src/townlet/exploration/icm.py b/src/townlet/exploration/icm.py
index 66e68605..54626ae4 100644
--- a/src/townlet/exploration/icm.py
+++ b/src/townlet/exploration/icm.py
@@ -118,9 +118,22 @@ class ICMExploration(EpsilonGreedyExploration):
         self._pending: deque[dict[str, Any]] = deque()
         self._counters = dict.fromkeys(_COUNTERS, 0)
         self._last_loss = 0.0
-        self._service_position: int | None = 0 if service_clock_unit == "world_eligible_admission" else None
+        self._service_position: int | None
+        if service_clock_unit == "world_eligible_admission":
+            self._service_position = 0
+        else:
+            self._service_position = None
         self._ordinary_updates_at_position = 0
 
+    def __deepcopy__(self, memo: dict[int, Any]) -> ICMExploration:
+        """Copy real learned state without pickling frozen policy mappings."""
+        candidate = object.__new__(type(self))
+        memo[id(self)] = candidate
+        if id(self.policy) not in memo:
+            memo[id(self.policy)] = type(self.policy).from_dict(self.policy.to_dict())
+        candidate.__dict__ = deepcopy(self.__dict__, memo)
+        return candidate
+
     @property
     def service_clock_unit(self) -> Literal["vector_tick", "world_eligible_admission"]:
         return self._service_clock_unit
@@ -450,7 +463,7 @@ class ICMExploration(EpsilonGreedyExploration):
             owned_pending = deque(_owned(pending))
         except (KeyError, TypeError, RuntimeError, AttributeError, OverflowError) as error:
             raise ValueError("ICM checkpoint is malformed") from error
-        candidate = deepcopy(self)
+        candidate = deepcopy(self, {id(self.policy): policy})
         candidate.encoder, candidate.inverse_model, candidate.forward_model, candidate.optimizer = encoder, inverse, forward, optimizer
         candidate.policy, candidate._source_device = policy, config["device"]
         candidate.epsilon, candidate.epsilon_decay, candidate.epsilon_min = state["epsilon"], state["epsilon_decay"], state["epsilon_min"]
diff --git a/src/townlet/exploration/rnd.py b/src/townlet/exploration/rnd.py
index eca3bead..e9080f63 100644
--- a/src/townlet/exploration/rnd.py
+++ b/src/townlet/exploration/rnd.py
@@ -81,7 +81,7 @@ class RunningMeanStd:
         """
         batch_mean = np.mean(x)
         batch_var = np.var(x)
-        batch_count = x.size if isinstance(x.size, int) else np.prod(x.shape)
+        batch_count = int(x.size)
 
         self.update_from_moments(batch_mean, batch_var, batch_count)
 
@@ -180,14 +180,14 @@ class RNDExploration(ExplorationStrategy):
         for name, value in (("obs_dim", obs_dim), ("embed_dim", embed_dim), ("training_batch_size", training_batch_size)):
             if type(value) is not int or value <= 0:
                 raise ValueError(f"RND {name} must be a positive integer")
-        for name, value in (
+        for scalar_name, scalar_value in (
             ("learning_rate", learning_rate),
             ("epsilon_start", epsilon_start),
             ("epsilon_min", epsilon_min),
             ("epsilon_decay", epsilon_decay),
         ):
-            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
-                raise ValueError(f"RND {name} must be finite numeric configuration")
+            if isinstance(scalar_value, bool) or not isinstance(scalar_value, (int, float)) or not math.isfinite(scalar_value):
+                raise ValueError(f"RND {scalar_name} must be finite numeric configuration")
         if learning_rate < 0 or not 0 <= epsilon_min <= epsilon_start <= 1 or not 0 <= epsilon_decay <= 1:
             raise ValueError("RND learning rate/epsilon configuration is invalid")
         device = torch.device(device)
@@ -225,7 +225,11 @@ class RNDExploration(ExplorationStrategy):
         self._consumed_rows = 0
         self._dropped_rows = 0
         self._optimizer_updates = 0
-        self._service_position: int | None = 0 if service_clock_unit == "world_eligible_admission" else None
+        self._service_position: int | None
+        if service_clock_unit == "world_eligible_admission":
+            self._service_position = 0
+        else:
+            self._service_position = None
         self._ordinary_updates_at_position = 0
 
         # Running statistics for intrinsic reward normalization
@@ -392,7 +396,10 @@ class RNDExploration(ExplorationStrategy):
         self._validate_buffer()
         if self.service_options is None:
             raise ValueError("Configure resolved RND service options before admission")
-        self._validated_options(self.service_options)
+        options = self._validated_options(self.service_options)
+        assert options.max_pending_rows is not None
+        if len(self.obs_buffer) > options.max_pending_rows:
+            raise ValueError("RND existing buffer exceeds bounded service capacity")
         if type(clock) is not ServiceClock:
             raise ValueError("RND service requires ServiceClock")
         ServiceClock(clock.unit, clock.position)
@@ -657,40 +664,46 @@ class RNDExploration(ExplorationStrategy):
         if not isinstance(optimizer_state, dict) or set(optimizer_state) != {"state", "param_groups"}:
             raise ValueError("RND checkpoint optimizer fields mismatch")
         self._validate_optimizer_groups(optimizer_state["param_groups"])
-        if not isinstance(optimizer_state["state"], dict):
-            raise ValueError("RND checkpoint optimizer moments must be a mapping")
+        states = optimizer_state["state"]
+        if not isinstance(states, dict) or any(type(identifier) is not int for identifier in states):
+            raise ValueError("RND checkpoint optimizer moments require exact integer parameter IDs")
         parameter_ids = [index for group in optimizer_state["param_groups"] for index in group["params"]]
-        if len(set(parameter_ids)) != len(parameter_ids) or not set(optimizer_state["state"]).issubset(parameter_ids):
+        if len(set(parameter_ids)) != len(parameter_ids) or not set(states).issubset(parameter_ids):
             raise ValueError("RND checkpoint optimizer parameter identity mismatch")
-        if optimizer_state["state"] and set(optimizer_state["state"]) != set(parameter_ids):
+        if states and set(states) != set(parameter_ids):
             raise ValueError("RND dense predictor requires complete Adam history for every parameter")
-        optimizer.load_state_dict(deepcopy(optimizer_state))
+        # Inspect original transported tensors before Adam can cast moments to
+        # parameter dtype, losing invalid dtype/negative-underflow information.
         steps: set[int] = set()
-        for group in optimizer.param_groups:
+        for group, destination in zip(optimizer_state["param_groups"], optimizer.param_groups, strict=True):
             if group["lr"] < 0 or group["eps"] < 0 or group["weight_decay"] < 0 or any(not 0 <= beta < 1 for beta in group["betas"]):
                 raise ValueError("RND checkpoint optimizer settings invalid")
-            for parameter in group["params"]:
-                if parameter not in optimizer.state:
+            for identifier, parameter in zip(group["params"], destination["params"], strict=True):
+                if identifier not in states:
                     continue
-                moments = optimizer.state[parameter]
+                moments = states[identifier]
                 required = {"step", "exp_avg", "exp_avg_sq"}
                 if group["amsgrad"]:
                     required.add("max_exp_avg_sq")
-                if set(moments) != required:
+                if not isinstance(moments, dict) or set(moments) != required:
                     raise ValueError("RND checkpoint optimizer moment fields mismatch")
                 for name, tensor in moments.items():
-                    if not isinstance(tensor, torch.Tensor):
-                        raise ValueError("RND checkpoint optimizer moments must be tensors")
+                    if not isinstance(tensor, torch.Tensor) or tensor.layout != torch.strided or tensor.device.type not in {"cpu", "cuda"}:
+                        raise ValueError("RND checkpoint optimizer moments require concrete dense tensors")
+                    if not torch.isfinite(tensor).all().item():
+                        raise ValueError("RND checkpoint optimizer moments must be finite")
                     if name == "step":
                         if tensor.shape != () or not tensor.is_floating_point() or tensor.item() < 0 or tensor.item() != int(tensor.item()):
                             raise ValueError("RND checkpoint optimizer step invalid")
                         steps.add(int(tensor.item()))
                     elif tensor.shape != parameter.shape or tensor.dtype != parameter.dtype:
-                        raise ValueError("RND checkpoint optimizer moment geometry mismatch")
+                        raise ValueError("RND raw optimizer moment geometry/dtype mismatch")
                     elif name in {"exp_avg_sq", "max_exp_avg_sq"} and (tensor < 0).any().item():
-                        raise ValueError("RND checkpoint optimizer squared moments must be nonnegative")
+                        raise ValueError("RND raw optimizer squared moments must be nonnegative")
         if len(steps) > 1:
             raise ValueError("RND dense predictor Adam parameter steps must agree")
+        optimizer.load_state_dict(deepcopy(optimizer_state))
+        self._finite_tree(optimizer.state_dict())
         # Exercise destination execution on disposable copies, including flags
         # whose device/version compatibility is enforced only during Adam.step.
         probe = deepcopy(optimizer)
@@ -699,6 +712,11 @@ class RNDExploration(ExplorationStrategy):
                 parameter.grad = torch.zeros_like(parameter)
         try:
             probe.step()
+            self._finite_tree(probe.state_dict())
+            for group in probe.param_groups:
+                for parameter in group["params"]:
+                    if not torch.isfinite(parameter).all().item():
+                        raise ValueError("RND checkpoint optimizer produces nonfinite destination parameters")
         except (AssertionError, RuntimeError, TypeError, ValueError) as exc:
             raise ValueError("RND checkpoint optimizer cannot execute on this destination") from exc
         return fixed, predictor, optimizer
@@ -733,7 +751,9 @@ class RNDExploration(ExplorationStrategy):
             raise ValueError("RND predictor service version/minibatch mismatch")
         options = None
         if service["options"] is not None:
-            expected_options = self.service_options.model_dump() if self.service_options is not None else {}
+            if self.service_options is None:
+                raise ValueError("RND checkpoint service options differ from unconfigured destination")
+            expected_options = self.service_options.model_dump()
             raw_options = service["options"]
             if (
                 not isinstance(raw_options, dict)
diff --git a/tests/test_townlet/regressions/bac/test_pw_local_service.py b/tests/test_townlet/regressions/bac/test_pw_local_service.py
index 072a58ce..9520718f 100644
--- a/tests/test_townlet/regressions/bac/test_pw_local_service.py
+++ b/tests/test_townlet/regressions/bac/test_pw_local_service.py
@@ -602,6 +602,17 @@ def test_owned_native_real_learning_and_rng_continuation(kind: str) -> None:
     )
     _equal(before, destination.snapshot())
     _equal(ambient, _ambient())
+    # Observing the live destination advances its revision. The earlier token
+    # must refuse, preserving the checked state; prepare again after observation.
+    with pytest.raises(ValueError, match="already installed or its destination changed"):
+        destination.install(prepared)
+    _equal(before, destination.snapshot())
+    _equal(ambient, _ambient())
+    prepared = destination.prepare_restore(
+        saved,
+        factory=factory,
+        validate_backend=lambda candidate, payload: candidate.validate_state(payload),
+    )
     destination.install(prepared)
     _equal(saved, destination.snapshot())
 
@@ -1287,3 +1298,115 @@ def test_current_provider_fixture_preflight(kind: str, overflow: str, unit: str)
         assert set(snapshot["components"]) == {"model_init", "target", "predictor", "service"}
         assert all(component["torch_cpu"].dtype == torch.uint8 for component in snapshot["components"].values())
         _equal(ambient, _ambient())
+
+
+@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
+@pytest.mark.parametrize("overflow", OVERFLOW)
+@pytest.mark.parametrize("entrypoint", ("admit_and_service", "update"))
+def test_overcapacity_shared_buffer_refuses_before_service(kind: str, overflow: str, entrypoint: str) -> None:
+    backend = _make(kind, overflow=overflow, unit=SHARED)
+    provider = _rnd(backend)
+    provider.obs_buffer.extend(row.clone() for row in _rows(8, 500))
+    before, counters, ambient = _native(backend), provider.predictor_service_counters(), _ambient()
+    callbacks: list[str] = []
+
+    def forbidden_callback(*args: Any, **kwargs: Any) -> None:
+        callbacks.append("service-before-capacity-refusal")
+        pytest.fail("over-capacity admission invoked learning before preflight; stopped before its possible unbounded loop")
+
+    handles = [
+        provider.fixed_network.register_forward_pre_hook(forbidden_callback),
+        provider.predictor_network.register_forward_pre_hook(forbidden_callback),
+        provider.optimizer.register_step_pre_hook(forbidden_callback),
+    ]
+    try:
+        with pytest.raises(ValueError):
+            if entrypoint == "admit_and_service":
+                backend.admit_and_service(_rows(1, 520), vector_tick=7)
+            else:
+                backend.update({"observations": _rows(1, 520)})
+        assert not callbacks
+        assert provider.predictor_service_counters() == counters
+        _equal(before, _native(backend))
+        _equal(ambient, _ambient())
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+def _warm_native_validation_fixture(kind: str) -> tuple[Any, dict[str, Any]]:
+    backend = _make(kind)
+    _warm(backend)
+    pristine = _native(backend)
+    # Establish complete lawful preparation before the malformed-state witness.
+    # In particular, a current ICM MappingProxy clone error is a prerequisite
+    # failure here, outside every expected-refusal assertion; it is not Adam RED.
+    backend.validate_state(pristine)
+    _equal(pristine, _native(backend))
+    moments = _inner(pristine)["optimizer"]["state"]
+    assert moments and all(type(key) is int for key in moments)
+    for state in moments.values():
+        assert state["exp_avg"].dtype == state["exp_avg_sq"].dtype == torch.float32
+    return backend, pristine
+
+
+RAW_MOMENT_CASES = (
+    ("exp_avg", "float64"),
+    ("exp_avg", "int64"),
+    ("exp_avg", "bool"),
+    ("exp_avg_sq", "float64"),
+    ("exp_avg_sq", "int64"),
+    ("exp_avg_sq", "bool"),
+    ("exp_avg", "finite_overflow"),
+    ("exp_avg_sq", "negative_underflow"),
+)
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("field,case", RAW_MOMENT_CASES)
+def test_raw_adam_moment_dtype_refuses_before_loader_coercion(kind: str, field: str, case: str) -> None:
+    backend, pristine = _warm_native_validation_fixture(kind)
+    damaged = deepcopy(pristine)
+    moments = list(_inner(damaged)["optimizer"]["state"].values())[-1]
+    original = moments[field]
+    if case == "finite_overflow":
+        moments[field] = torch.full_like(original, 1e300, dtype=torch.float64)
+        assert bool(torch.isfinite(moments[field]).all())
+        assert bool(torch.isinf(moments[field].to(torch.float32)).all())
+    elif case == "negative_underflow":
+        moments[field] = torch.full_like(original, -1e-300, dtype=torch.float64)
+        assert bool((moments[field] < 0).all())
+        assert bool((moments[field].to(torch.float32) == 0).all())
+    else:
+        dtype = {"float64": torch.float64, "int64": torch.int64, "bool": torch.bool}[case]
+        moments[field] = original.to(dtype)
+    input_before = deepcopy(damaged)
+    callbacks: list[Any] = []
+    handles = _watch_forwards(backend, callbacks)
+    try:
+        for method in (backend.validate_state, backend.prepare_state, backend.load_state):
+            _must_refuse_unchanged(backend, lambda: method(damaged))
+            _equal(pristine, _native(backend))
+            _equal(input_before, damaged)
+            assert not callbacks
+    finally:
+        for handle in handles:
+            handle.remove()
+
+
+@pytest.mark.parametrize("kind", PROVIDERS)
+@pytest.mark.parametrize("identifier,alias", ((0, False), (0, 0.0), (1, True), (1, 1.0)))
+def test_native_optimizer_state_ids_refuse_bool_and_float_aliases(kind: str, identifier: int, alias: Any) -> None:
+    backend, pristine = _warm_native_validation_fixture(kind)
+    damaged = deepcopy(pristine)
+    optimizer = _inner(damaged)["optimizer"]
+    assert identifier in optimizer["state"]
+    optimizer["state"] = {alias if key == identifier else key: value for key, value in optimizer["state"].items()}
+    keys_before = [(type(key), key) for key in optimizer["state"]]
+    assert (type(alias), alias) in keys_before
+    input_before = deepcopy(damaged)
+    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
+        _must_refuse_unchanged(backend, lambda: method(damaged))
+        _equal(pristine, _native(backend))
+        _equal(input_before, damaged)
+        assert [(type(key), key) for key in optimizer["state"]] == keys_before

```
