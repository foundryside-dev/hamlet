Previous reviewed tree 3be954f130ee8a19a03013f68d8c897ba11c2dba
Fixed tree efb8c926252e7aff6366978fc38b4b8f09561146
Formatting only, WS production unchanged.
diff --git a/tests/test_townlet/regressions/bac/test_pw_rng_binding.py b/tests/test_townlet/regressions/bac/test_pw_rng_binding.py
index 6cf61633..dc1d5558 100644
--- a/tests/test_townlet/regressions/bac/test_pw_rng_binding.py
+++ b/tests/test_townlet/regressions/bac/test_pw_rng_binding.py
@@ -15,28 +15,32 @@ import torch
 import yaml
 
 from townlet.config.bac_options import BaCOptions
 from townlet.config.drive_as_code import IntrinsicStrategyConfig
 from townlet.config.exploration_policy import ResolvedExplorationPolicy, resolve_exploration_policy
 from townlet.config.training_v2_config import TrainingV2Config
 from townlet.exploration import world_curiosity_state as world_state
 from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
-from townlet.exploration.world_curiosity_state import WORLD_SEED_COMPONENTS, OwnedWorldBackend, WorldCuriosityDescriptor, WorldRNGState, derive_world_seed
+from townlet.exploration.world_curiosity_state import (
+    WORLD_SEED_COMPONENTS,
+    OwnedWorldBackend,
+    WorldCuriosityDescriptor,
+    WorldRNGState,
+    derive_world_seed,
+)
 
 
 def _policy() -> ResolvedExplorationPolicy:
     root = Path(__file__).resolve().parents[4]
     directory = root / "configs/test/token_set_smoke/levels/L0_test"
     training = yaml.safe_load((directory / "training.yaml").read_text())["training"]
     drive = yaml.safe_load((directory / "drive.yaml").read_text())["drive"]["intrinsic"]
     drive["strategy"] = "none"
-    options = BaCOptions.model_validate(
-        {"curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"}}
-    )
+    options = BaCOptions.model_validate({"curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"}})
     return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), options)
 
 
 def _descriptor(policy: ResolvedExplorationPolicy, ids: tuple[str, ...]) -> WorldCuriosityDescriptor:
     return WorldCuriosityDescriptor.from_policy(policy, world_ids=ids, observation_dim=3, action_dim=2, training_seed=173)
 
 
 def _backend(policy: ResolvedExplorationPolicy) -> EpsilonGreedyExploration:
@@ -201,18 +205,36 @@ def test_binding_rejects_other_owner_inside_activation(binding: tuple[Any, ...])
             with other.activate("service"):
                 pytest.fail("different owner was activated")
         _same(_ambient(()), installed)
     _same(other.snapshot(), before)
 
 
 @pytest.mark.parametrize(
     "probe",
-    ["id", "empty-id", "typed-id", "missing-id", "provider", "config", "observation", "action", "seed", "scope",
-     "malformed-descriptor", "malformed-seeds", "malformed-clock", "device-list", "device-bool", "device-negative", "device-duplicate", "device-order"],
+    [
+        "id",
+        "empty-id",
+        "typed-id",
+        "missing-id",
+        "provider",
+        "config",
+        "observation",
+        "action",
+        "seed",
+        "scope",
+        "malformed-descriptor",
+        "malformed-seeds",
+        "malformed-clock",
+        "device-list",
+        "device-bool",
+        "device-negative",
+        "device-duplicate",
+        "device-order",
+    ],
 )
 @pytest.mark.parametrize("active", [False, True])
 def test_binding_refuses_mismatch_before_draws(binding: tuple[Any, ...], probe: str, active: bool) -> None:
     policy, descriptor, rng = binding
     expected: Any = descriptor
     world_id: Any = "world-A"
     devices: Any = ()
     if probe == "id":
@@ -222,43 +244,64 @@ def test_binding_refuses_mismatch_before_draws(binding: tuple[Any, ...], probe:
     elif probe == "typed-id":
         world_id = 1
     elif probe == "missing-id":
         expected = _descriptor(policy, ("world-B",))
     elif probe in ("provider", "seed"):
         payload = policy.to_dict()
         if probe == "provider":
             # Valid same-schema descriptor with a different current provider.
-            expected = replace(descriptor, provider_kind="rnd", seeds={
-                wid: {component: derive_world_seed(
-                    training_seed=descriptor.training_seed, world_id=wid, provider_kind="rnd", component=component
-                ) for component in WORLD_SEED_COMPONENTS} for wid in descriptor.world_ids
-            })
+            expected = replace(
+                descriptor,
+                provider_kind="rnd",
+                seeds={
+                    wid: {
+                        component: derive_world_seed(
+                            training_seed=descriptor.training_seed, world_id=wid, provider_kind="rnd", component=component
+                        )
+                        for component in WORLD_SEED_COMPONENTS
+                    }
+                    for wid in descriptor.world_ids
+                },
+            )
         else:
             expected = WorldCuriosityDescriptor.from_policy(
-                ResolvedExplorationPolicy.from_dict(payload), world_ids=descriptor.world_ids,
-                observation_dim=3, action_dim=2, training_seed=174,
+                ResolvedExplorationPolicy.from_dict(payload),
+                world_ids=descriptor.world_ids,
+                observation_dim=3,
+                action_dim=2,
+                training_seed=174,
             )
     elif probe == "config":
         expected = replace(descriptor, provider_parameter_hash="0" * 64)
     elif probe == "observation":
         expected = replace(descriptor, observation_dim=4)
     elif probe == "action":
         expected = replace(descriptor, action_dim=3)
     elif probe == "scope":
-        expected = replace(descriptor, scope="shared", seed_policy="legacy_shared_v1", service_clock_unit="vector_tick",
-                           guarantee="shared_population_state", seeds={})
+        expected = replace(
+            descriptor,
+            scope="shared",
+            seed_policy="legacy_shared_v1",
+            service_clock_unit="vector_tick",
+            guarantee="shared_population_state",
+            seeds={},
+        )
     elif probe == "malformed-descriptor":
         expected = descriptor.to_dict()
     elif probe in ("malformed-seeds", "malformed-clock"):
         expected = copy(descriptor)
         # Adversarial frozen-dataclass bypass must still be refused by preflight.
-        object.__setattr__(expected, "seeds" if probe == "malformed-seeds" else "service_clock_unit", {} if probe == "malformed-seeds" else "vector_tick")
+        object.__setattr__(
+            expected, "seeds" if probe == "malformed-seeds" else "service_clock_unit", {} if probe == "malformed-seeds" else "vector_tick"
+        )
     else:
-        devices = {"device-list": [], "device-bool": (True,), "device-negative": (-1,), "device-duplicate": (0, 0), "device-order": (1, 0)}[probe]
+        devices = {"device-list": [], "device-bool": (True,), "device-negative": (-1,), "device-duplicate": (0, 0), "device-order": (1, 0)}[
+            probe
+        ]
     before = rng.snapshot()
     ambient = _ambient(())
 
     def refuse() -> None:
         installed = _ambient(())
         with pytest.raises(ValueError):
             _validate(rng, expected, world_id, devices)
         _same(_ambient(()), installed)
@@ -313,17 +356,19 @@ def test_binding_cuda_domain(binding: tuple[Any, ...]) -> None:
     with rng.activate("model_init"):
         _validate(rng, descriptor, "world-A", devices)
         with pytest.raises(ValueError):
             _validate(rng, descriptor, "world-A", ())
     with pytest.raises(ValueError):
         _validate(cpu, descriptor, "world-A", devices)
     with pytest.raises(ValueError):
         _validate(rng, descriptor, "world-A", (torch.cuda.device_count(),))
-    owner = OwnedWorldBackend.construct(rng=rng, factory=lambda candidate: (_validate(candidate, descriptor, "world-A", devices), _backend(policy))[1])
+    owner = OwnedWorldBackend.construct(
+        rng=rng, factory=lambda candidate: (_validate(candidate, descriptor, "world-A", devices), _backend(policy))[1]
+    )
     _same(owner.snapshot()["rng"], before)
     _same(rng.snapshot(), before)
     _same(_ambient(devices), ambient)
 
 
 def test_binding_validates_actual_owned_descriptor(binding: tuple[Any, ...]) -> None:
     _, descriptor, rng = binding
     malformed = copy(descriptor)
