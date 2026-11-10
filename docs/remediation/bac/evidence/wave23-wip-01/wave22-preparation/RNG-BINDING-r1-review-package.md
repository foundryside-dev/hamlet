Base 50210cfec4fdccf304d4a6bfb00ae179563a5846
Candidate 3be954f130ee8a19a03013f68d8c897ba11c2dba
Exactly3source inventory in brief, only WS+bindingtest changed. Factory test staged draft is unreviewed and outside this review; do not open it.

diff --git a/src/townlet/exploration/world_curiosity_state.py b/src/townlet/exploration/world_curiosity_state.py
index 29ee821d..abfa7a78 100644
--- a/src/townlet/exploration/world_curiosity_state.py
+++ b/src/townlet/exploration/world_curiosity_state.py
@@ -637,16 +637,40 @@ class WorldRNGState:
                         "descriptor": _identity(self._descriptor),
                         "world_id": self._world_id,
                         "cuda_devices": self._cuda_devices,
                         "components": self._components,
                     }
                 ),
             )
 
+    def validate_binding(self, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> None:
+        """Check actual ownership without draws, including inside this owner's callback.
+
+        Roster order and spectators are not stream identity. Snapshot and restore
+        remain quiescent lifecycle operations; this read never captures streams.
+        """
+        with _rng_guard:
+            _usable()
+            if self._broken:
+                raise RuntimeError("Private RNG state is unusable after failed capture")
+            stack = _stack()
+            if stack and stack[-1].owner is not self:
+                raise RuntimeError("Cross-owner nested RNG binding validation is forbidden")
+            _domain_arguments(descriptor, world_id, cuda_devices)
+            _domain_arguments(self._descriptor, self._world_id, self._cuda_devices)
+            # Validate both descriptors, including fields outside stable identity
+            # and frozen-dataclass instances forged around their constructor.
+            WorldCuriosityDescriptor.from_dict(descriptor.to_dict())
+            WorldCuriosityDescriptor.from_dict(self._descriptor.to_dict())
+            if not _same(_identity(self._descriptor), _identity(descriptor)):
+                raise ValueError("Private RNG descriptor identity disagrees")
+            if not _same(self._world_id, world_id) or not _same(self._cuda_devices, cuda_devices):
+                raise ValueError("Private RNG world/device binding disagrees")
+
     @contextmanager
     def activate(self, component: str) -> Iterator[WorldRandomSources]:
         global _rng_unusable
         with _rng_guard:
             _usable()
             if self._broken:
                 raise RuntimeError("Private RNG state is unusable after failed capture")
             if type(component) is not str or component not in self._components:
diff --git a/tests/test_townlet/regressions/bac/test_pw_rng_binding.py b/tests/test_townlet/regressions/bac/test_pw_rng_binding.py
new file mode 100644
index 00000000..6cf61633
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_pw_rng_binding.py
@@ -0,0 +1,374 @@
+"""Public binding preflight must compose with real owned construction without draws."""
+
+from __future__ import annotations
+
+import random
+from collections.abc import Mapping
+from copy import copy, deepcopy
+from dataclasses import replace
+from pathlib import Path
+from typing import Any
+
+import numpy as np
+import pytest
+import torch
+import yaml
+
+from townlet.config.bac_options import BaCOptions
+from townlet.config.drive_as_code import IntrinsicStrategyConfig
+from townlet.config.exploration_policy import ResolvedExplorationPolicy, resolve_exploration_policy
+from townlet.config.training_v2_config import TrainingV2Config
+from townlet.exploration import world_curiosity_state as world_state
+from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
+from townlet.exploration.world_curiosity_state import WORLD_SEED_COMPONENTS, OwnedWorldBackend, WorldCuriosityDescriptor, WorldRNGState, derive_world_seed
+
+
+def _policy() -> ResolvedExplorationPolicy:
+    root = Path(__file__).resolve().parents[4]
+    directory = root / "configs/test/token_set_smoke/levels/L0_test"
+    training = yaml.safe_load((directory / "training.yaml").read_text())["training"]
+    drive = yaml.safe_load((directory / "drive.yaml").read_text())["drive"]["intrinsic"]
+    drive["strategy"] = "none"
+    options = BaCOptions.model_validate(
+        {"curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"}}
+    )
+    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), options)
+
+
+def _descriptor(policy: ResolvedExplorationPolicy, ids: tuple[str, ...]) -> WorldCuriosityDescriptor:
+    return WorldCuriosityDescriptor.from_policy(policy, world_ids=ids, observation_dim=3, action_dim=2, training_seed=173)
+
+
+def _backend(policy: ResolvedExplorationPolicy) -> EpsilonGreedyExploration:
+    return EpsilonGreedyExploration(epsilon=policy.epsilon_start, epsilon_decay=policy.epsilon_decay, epsilon_min=policy.epsilon_end)
+
+
+def _same(left: Any, right: Any) -> None:
+    assert type(left) is type(right)
+    if isinstance(left, torch.Tensor):
+        assert left.device == right.device and left.dtype == right.dtype
+        assert torch.equal(left, right)
+    elif isinstance(left, np.ndarray):
+        assert left.dtype == right.dtype
+        np.testing.assert_array_equal(left, right)
+    elif isinstance(left, Mapping):
+        assert left.keys() == right.keys()
+        for key in left:
+            _same(left[key], right[key])
+    elif isinstance(left, (tuple, list)):
+        assert len(left) == len(right)
+        for a, b in zip(left, right, strict=True):
+            _same(a, b)
+    else:
+        assert left == right
+
+
+def _ambient(devices: tuple[int, ...]) -> dict[str, Any]:
+    return {
+        "torch": torch.get_rng_state().clone(),
+        "python": random.getstate(),
+        "numpy": deepcopy(np.random.get_state()),
+        "cuda": {index: torch.cuda.get_rng_state(index).clone() for index in devices},
+    }
+
+
+def _validate(rng: WorldRNGState, descriptor: Any, world_id: Any, devices: Any) -> None:
+    method = getattr(rng, "validate_binding", None)
+    assert callable(method), "WorldRNGState lacks public activation-safe validate_binding"
+    assert method(descriptor=descriptor, world_id=world_id, cuda_devices=devices) is None
+
+
+@pytest.fixture
+def binding() -> tuple[ResolvedExplorationPolicy, WorldCuriosityDescriptor, WorldRNGState]:
+    policy = _policy()
+    descriptor = _descriptor(policy, ("world-A", "world-B"))
+    rng = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
+    return policy, descriptor, rng
+
+
+def test_binding_fixture_prerequisite(binding: tuple[Any, ...]) -> None:
+    """All real fixtures and lifecycle succeed independently of the new method."""
+    policy, descriptor, rng = binding
+    assert policy.strategy == "none" and policy.curiosity_scope == "per_world"
+    assert WorldCuriosityDescriptor.from_dict(descriptor.to_dict()) == descriptor
+    before = rng.snapshot()
+    ambient = _ambient(())
+    candidates = []
+
+    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
+        assert candidate is not rng
+        candidates.append(candidate)
+        with pytest.raises(RuntimeError, match="quiescent"):
+            candidate.snapshot()
+        with pytest.raises(RuntimeError, match="quiescent"):
+            WorldRNGState.from_snapshot(before, descriptor=descriptor, world_id="world-A", cuda_devices=())
+        return _backend(policy)
+
+    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
+    assert len(candidates) == 1
+    _same(owner.snapshot()["rng"], before)
+    _same(rng.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+def test_binding_inside_actual_owned_constructor(binding: tuple[Any, ...]) -> None:
+    policy, descriptor, rng = binding
+    before = rng.snapshot()
+    ambient = _ambient(())
+    candidates = []
+
+    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
+        assert candidate is not rng
+        candidates.append(candidate)
+        installed = _ambient(())
+        _validate(candidate, descriptor, "world-A", ())
+        _same(_ambient(()), installed)
+        return _backend(policy)
+
+    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
+    assert len(candidates) == 1
+    _same(owner.snapshot()["rng"], before)
+    _same(rng.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+@pytest.mark.parametrize("component", WORLD_SEED_COMPONENTS)
+def test_binding_read_preserves_every_stream(binding: tuple[Any, ...], component: str) -> None:
+    _, descriptor, rng = binding
+    before = rng.snapshot()
+    ambient = _ambient(())
+    _validate(rng, descriptor, "world-A", ())
+    with rng.activate(component) as sources:
+        installed = _ambient(())
+        pcg = deepcopy(sources.numpy.bit_generator.state)
+        _validate(rng, descriptor, "world-A", ())
+        _same(sources.numpy.bit_generator.state, pcg)
+        _same(_ambient(()), installed)
+        with pytest.raises(RuntimeError, match="quiescent"):
+            rng.snapshot()
+    _same(rng.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+def test_binding_preserves_actual_candidate_domain_draws(binding: tuple[Any, ...]) -> None:
+    policy, descriptor, rng = binding
+    before = rng.snapshot()
+    ambient = _ambient(())
+    seen = []
+
+    def factory(candidate: WorldRNGState) -> EpsilonGreedyExploration:
+        seen.append(candidate)
+        _validate(candidate, descriptor, "world-A", ())
+        for component in WORLD_SEED_COMPONENTS:
+            with candidate.activate(component) as sources:
+                _validate(candidate, descriptor, "world-A", ())
+                torch.rand(2)
+                sources.python.random()
+                sources.numpy.random()
+                np.random.random()
+        return _backend(policy)
+
+    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
+    after = owner.snapshot()["rng"]
+    _same(after, seen[0].snapshot())
+    for component in WORLD_SEED_COMPONENTS:
+        assert not torch.equal(after["components"][component]["torch_cpu"], before["components"][component]["torch_cpu"])
+    _same(rng.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+@pytest.mark.parametrize("ids", [("world-B", "world-A"), ("spectator", "world-A"), ("world-A",)])
+def test_binding_ignores_spectator_roster_and_order(binding: tuple[Any, ...], ids: tuple[str, ...]) -> None:
+    policy, _, rng = binding
+    descriptor = _descriptor(policy, ids)
+    before = rng.snapshot()
+    _validate(rng, descriptor, "world-A", ())
+    with rng.activate("model_init"):
+        _validate(rng, descriptor, "world-A", ())
+    _same(rng.snapshot(), before)
+
+
+def test_binding_rejects_other_owner_inside_activation(binding: tuple[Any, ...]) -> None:
+    _, descriptor, rng = binding
+    other = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
+    before = other.snapshot()
+    with rng.activate("model_init"):
+        _validate(rng, descriptor, "world-A", ())
+        installed = _ambient(())
+        with pytest.raises(RuntimeError, match="[Cc]ross-owner"):
+            _validate(other, descriptor, "world-A", ())
+        with pytest.raises(RuntimeError, match="[Cc]ross-owner"):
+            with other.activate("service"):
+                pytest.fail("different owner was activated")
+        _same(_ambient(()), installed)
+    _same(other.snapshot(), before)
+
+
+@pytest.mark.parametrize(
+    "probe",
+    ["id", "empty-id", "typed-id", "missing-id", "provider", "config", "observation", "action", "seed", "scope",
+     "malformed-descriptor", "malformed-seeds", "malformed-clock", "device-list", "device-bool", "device-negative", "device-duplicate", "device-order"],
+)
+@pytest.mark.parametrize("active", [False, True])
+def test_binding_refuses_mismatch_before_draws(binding: tuple[Any, ...], probe: str, active: bool) -> None:
+    policy, descriptor, rng = binding
+    expected: Any = descriptor
+    world_id: Any = "world-A"
+    devices: Any = ()
+    if probe == "id":
+        world_id = "world-B"
+    elif probe == "empty-id":
+        world_id = ""
+    elif probe == "typed-id":
+        world_id = 1
+    elif probe == "missing-id":
+        expected = _descriptor(policy, ("world-B",))
+    elif probe in ("provider", "seed"):
+        payload = policy.to_dict()
+        if probe == "provider":
+            # Valid same-schema descriptor with a different current provider.
+            expected = replace(descriptor, provider_kind="rnd", seeds={
+                wid: {component: derive_world_seed(
+                    training_seed=descriptor.training_seed, world_id=wid, provider_kind="rnd", component=component
+                ) for component in WORLD_SEED_COMPONENTS} for wid in descriptor.world_ids
+            })
+        else:
+            expected = WorldCuriosityDescriptor.from_policy(
+                ResolvedExplorationPolicy.from_dict(payload), world_ids=descriptor.world_ids,
+                observation_dim=3, action_dim=2, training_seed=174,
+            )
+    elif probe == "config":
+        expected = replace(descriptor, provider_parameter_hash="0" * 64)
+    elif probe == "observation":
+        expected = replace(descriptor, observation_dim=4)
+    elif probe == "action":
+        expected = replace(descriptor, action_dim=3)
+    elif probe == "scope":
+        expected = replace(descriptor, scope="shared", seed_policy="legacy_shared_v1", service_clock_unit="vector_tick",
+                           guarantee="shared_population_state", seeds={})
+    elif probe == "malformed-descriptor":
+        expected = descriptor.to_dict()
+    elif probe in ("malformed-seeds", "malformed-clock"):
+        expected = copy(descriptor)
+        # Adversarial frozen-dataclass bypass must still be refused by preflight.
+        object.__setattr__(expected, "seeds" if probe == "malformed-seeds" else "service_clock_unit", {} if probe == "malformed-seeds" else "vector_tick")
+    else:
+        devices = {"device-list": [], "device-bool": (True,), "device-negative": (-1,), "device-duplicate": (0, 0), "device-order": (1, 0)}[probe]
+    before = rng.snapshot()
+    ambient = _ambient(())
+
+    def refuse() -> None:
+        installed = _ambient(())
+        with pytest.raises(ValueError):
+            _validate(rng, expected, world_id, devices)
+        _same(_ambient(()), installed)
+
+    if active:
+        with rng.activate("model_init"):
+            refuse()
+    else:
+        refuse()
+    _same(rng.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+def test_binding_refuses_broken_owner(binding: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch) -> None:
+    _, descriptor, rng = binding
+    _validate(rng, descriptor, "world-A", ())
+    ambient = _ambient(())
+
+    def fail_capture() -> Any:
+        raise RuntimeError("injected capture failure")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(torch, "get_rng_state", fail_capture)
+        with pytest.raises(RuntimeError, match="injected capture failure"):
+            with rng.activate("model_init"):
+                pytest.fail("capture unexpectedly succeeded")
+    with pytest.raises(RuntimeError, match="[Uu]sable|capture|resume"):
+        _validate(rng, descriptor, "world-A", ())
+    _same(_ambient(()), ambient)
+
+
+def test_binding_cpu_never_queries_cuda(binding: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch) -> None:
+    _, descriptor, rng = binding
+
+    def forbidden() -> Any:
+        pytest.fail("CPU binding queried CUDA")
+
+    monkeypatch.setattr(torch.cuda, "is_initialized", forbidden)
+    monkeypatch.setattr(torch.cuda, "device_count", forbidden)
+    _validate(rng, descriptor, "world-A", ())
+
+
+@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA binding requires available hardware")
+def test_binding_cuda_domain(binding: tuple[Any, ...]) -> None:
+    policy, descriptor, cpu = binding
+    torch.cuda.init()
+    devices = (0,)
+    rng = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=devices)
+    before = rng.snapshot()
+    ambient = _ambient(devices)
+    _validate(rng, descriptor, "world-A", devices)
+    with rng.activate("model_init"):
+        _validate(rng, descriptor, "world-A", devices)
+        with pytest.raises(ValueError):
+            _validate(rng, descriptor, "world-A", ())
+    with pytest.raises(ValueError):
+        _validate(cpu, descriptor, "world-A", devices)
+    with pytest.raises(ValueError):
+        _validate(rng, descriptor, "world-A", (torch.cuda.device_count(),))
+    owner = OwnedWorldBackend.construct(rng=rng, factory=lambda candidate: (_validate(candidate, descriptor, "world-A", devices), _backend(policy))[1])
+    _same(owner.snapshot()["rng"], before)
+    _same(rng.snapshot(), before)
+    _same(_ambient(devices), ambient)
+
+
+def test_binding_validates_actual_owned_descriptor(binding: tuple[Any, ...]) -> None:
+    _, descriptor, rng = binding
+    malformed = copy(descriptor)
+    object.__setattr__(malformed, "seeds", {})
+    state = rng.snapshot()
+    # The existing public constructor can receive an unvalidated descriptor.
+    owner = WorldRNGState(malformed, "world-A", (), state["components"])
+    before = owner.snapshot()
+    ambient = _ambient(())
+    with pytest.raises(ValueError):
+        _validate(owner, descriptor, "world-A", ())
+    _same(owner.snapshot(), before)
+    _same(_ambient(()), ambient)
+
+
+def test_binding_refuses_quarantined_coordinator(binding: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch) -> None:
+    _, descriptor, rng = binding
+    other = WorldRNGState.create(descriptor=descriptor, world_id="world-A", cuda_devices=())
+    _validate(rng, descriptor, "world-A", ())
+    ambient = _ambient(())
+    original_set = torch.set_rng_state
+    calls = 0
+
+    def fail_restoration(state: torch.Tensor) -> None:
+        nonlocal calls
+        calls += 1
+        if calls == 2:
+            raise RuntimeError("injected restoration failure")
+        original_set(state)
+
+    try:
+        with monkeypatch.context() as patch:
+            # Preserve coordinator quarantine isolation across tests; the failure
+            # itself comes from the real activation restoration path.
+            patch.setattr(world_state, "_rng_unusable", None)
+            patch.setattr(torch, "set_rng_state", fail_restoration)
+            with pytest.raises(RuntimeError, match="injected restoration failure"):
+                with rng.activate("model_init"):
+                    pass
+            installed = _ambient(())
+            with pytest.raises(RuntimeError, match="unusable"):
+                _validate(other, descriptor, "world-A", ())
+            _same(_ambient(()), installed)
+    finally:
+        original_set(ambient["torch"])
+        random.setstate(ambient["python"])
+        np.random.set_state(ambient["numpy"])
+    _same(_ambient(()), ambient)
