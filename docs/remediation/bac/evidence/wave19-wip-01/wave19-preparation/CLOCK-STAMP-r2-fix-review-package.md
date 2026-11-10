# Sourcefixround1 exactdelta

PreviousR1tree fc9be745ab293003ab8f69a8ad7dd52c23a48f2a; fixedR2tree 808e9975155d089dd4c62996dbb996359d774fc6. Onlytargeted documentedtypingignore andBlackformat. RootASTequivalencePASS bothpaths, whole4fileinventory/hash inR2manifest. Rootrerunsjoint+sixguards, coveringhashassertionincluded.

```diff
diff --git a/src/townlet/exploration/world_curiosity_state.py b/src/townlet/exploration/world_curiosity_state.py
index e54acc27..29ee821d 100644
--- a/src/townlet/exploration/world_curiosity_state.py
+++ b/src/townlet/exploration/world_curiosity_state.py
@@ -102,7 +102,8 @@ class CuriosityStepStamp:
     Inputs must be quiescent while this cooperative snapshot is constructed.
     """
 
-    __hash__ = None
+    # Intentionally disable object's hash protocol for this identity-equal stamp.
+    __hash__ = None  # type: ignore[assignment]
 
     event_ids: tuple[CuriosityEventId, ...]
     world_ids: tuple[str, ...]
diff --git a/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py b/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py
index d5bae7c7..c9415b46 100644
--- a/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py
+++ b/tests/test_townlet/regressions/bac/test_pw_clock_stamp.py
@@ -160,6 +160,7 @@ def test_step_stamp_all_row_identity_refusals(case):
     elif case == "not_id":
         values["event_ids"] = (first, (0, "world-b", 2, 0))
     elif case == "id_alias":
+
         class EventAlias(event_id):
             pass
 
@@ -201,9 +202,7 @@ def test_step_stamp_all_row_order_and_geometry():
 
 
 @pytest.mark.parametrize("field", ["world_episode_seqs", "eligible_seqs", "eligible"])
-@pytest.mark.parametrize(
-    "kind", ["rank0", "rank2", "short", "long", "list", "none", "float", "int32", "wrong_bool", "meta", "sparse"]
-)
+@pytest.mark.parametrize("kind", ["rank0", "rank2", "short", "long", "list", "none", "float", "int32", "wrong_bool", "meta", "sparse"])
 def test_step_stamp_tensor_shape_dtype_layout_device(field, kind):
     values = _inputs()
     source = values[field]

```
