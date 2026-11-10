# Actual ownedgreedyfixturedelta only

R0 04d822c62185771e689b38f5d84804ec0ef9b5a8→R1 4c0cec9a4cd8893910a0abb64c396eb7011f5787. Onlythisownedtest sourcebelow; globalfixturecodeexcludedfromthisreviewer5filecontext andseparatelyreviewed. Exactepsilon_min0 keepsgreedypositiveunderactualconstructorinvariant; noassertionremoval.

```diff
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
