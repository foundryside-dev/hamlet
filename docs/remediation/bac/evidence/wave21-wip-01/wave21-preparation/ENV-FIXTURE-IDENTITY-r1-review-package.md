# Actual R0→R1 fixture prerequisite repair

PreviousR0 04d822c62185771e689b38f5d84804ec0ef9b5a8; fixedR1 4c0cec9a4cd8893910a0abb64c396eb7011f5787. Deltatwo testfilesonly, underlyingENV/roster/productionreadonlyunchanged. Wholeglobalworkercontext4/4535<=4800; unitowner5context2596<=3200. Exactepsilonfloor transportpreservesgreedypositive; actualbasic_envmetadata-onlydeclarationno activation/fakeowners. RealrunnercaseunchangedandstillrequiredOPEN.

```diff
diff --git a/tests/test_townlet/_fixtures/environment.py b/tests/test_townlet/_fixtures/environment.py
index dc9fd404..639da8e6 100644
--- a/tests/test_townlet/_fixtures/environment.py
+++ b/tests/test_townlet/_fixtures/environment.py
@@ -14,6 +14,7 @@ import yaml
 
 from tests.test_townlet._fixtures.config import _apply_config_overrides
 from tests.test_townlet.helpers.config_builder import _get_primary_level_dir, mutate_training_yaml
+from townlet.config.world_roster import WorldRosterDeclaration
 from townlet.environment.vectorized_env import VectorizedHamletEnv
 from townlet.universe.compiled import CompiledUniverse
 
@@ -41,11 +42,16 @@ def basic_env(
         VectorizedHamletEnv instance
     """
     universe = compile_universe(test_config_pack_path)
+    # Authored test identity; construction leaves episode activation to the caller.
+    world_roster = WorldRosterDeclaration(world_ids=("basic-env-world",))
     return VectorizedHamletEnv.from_universe(
         universe,
         level_name="L0_test",
         num_agents=1,
         device=device,
+        world_roster=world_roster,
+        training_seed=universe.get_level("L0_test").training.seed,
+        lane_world_ids=world_roster.world_ids,
     )
 
 
diff --git a/tests/test_townlet/unit/exploration/test_exploration_strategies.py b/tests/test_townlet/unit/exploration/test_exploration_strategies.py
index d7c14de0..4f72e0a8 100644
--- a/tests/test_townlet/unit/exploration/test_exploration_strategies.py
+++ b/tests/test_townlet/unit/exploration/test_exploration_strategies.py
@@ -711,6 +711,7 @@ class TestAdaptiveIntrinsicActionSelection:
             service_clock_unit="vector_tick",
             obs_dim=10,
             epsilon_start=0.0,  # Greedy for deterministic test
+            epsilon_min=0.0,
             device=torch.device("cpu"),
         )
 

```
