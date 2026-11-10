# PW06 actualproductionfixround1
9f27d612ad3527b1309bfc60219e58d45d03c834 -> e52234ed9e775355ef3fbc2704ce46b13c78c6bb
Source/tests combined delta includes approved4newregressions, CP/BANK3fixes.

diff --git a/src/townlet/exploration/curiosity_checkpoint.py b/src/townlet/exploration/curiosity_checkpoint.py
index 194ae93d..6f03ea3c 100644
--- a/src/townlet/exploration/curiosity_checkpoint.py
+++ b/src/townlet/exploration/curiosity_checkpoint.py
@@ -1,19 +1,20 @@
 """Strict current BANK transport and off-side runtime codecs.
 
 Portable values carry evidence, never ENV acceptance or closing authority.
 Provider algorithms and native validation belong to their actual producers.
 """
 
 from __future__ import annotations
 
 import math
+from collections import OrderedDict
 from collections.abc import Mapping
 from copy import deepcopy
 from typing import Any, cast
 
 import numpy as np
 import torch
 
 from townlet.config.exploration_policy import ResolvedExplorationPolicy
 from townlet.config.world_roster import WorldAcceptedEpisode, WorldRecord, WorldRosterDeclaration, validate_world_snapshot, world_binding
 from townlet.exploration.world_curiosity_state import CuriosityEventId, CuriosityStepStamp, ServiceClock, WorldCuriosityDescriptor
@@ -77,70 +78,92 @@ def number(value: Any, name: str) -> None:
 
 def same(left: Any, right: Any) -> bool:
     if type(left) is not type(right):
         return False
     if isinstance(left, torch.Tensor):
         return (left.shape, left.dtype, left.device, left.layout) == (right.shape, right.dtype, right.device, right.layout) and torch.equal(
             left, right
         )
     if isinstance(left, np.ndarray):
         return left.dtype == right.dtype and left.shape == right.shape and bool(np.array_equal(left, right))
+    if type(left) is OrderedDict:
+        if tuple(left) != tuple(right) or hasattr(left, "_metadata") != hasattr(right, "_metadata"):
+            return False
+        if hasattr(left, "_metadata") and not same(left._metadata, right._metadata):
+            return False
+        return all(same(left[key], right[key]) for key in left)
     if isinstance(left, Mapping):
         return left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
     if isinstance(left, (list, tuple)):
         return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right, strict=True))
     return bool(left == right)
 
 
 def owned(value: Any) -> Any:
     """Closed portable data only; reject unsupported storage before cloning."""
     if isinstance(value, torch.Tensor):
         require(value.layout == torch.strided and value.device.type in ("cpu", "cuda"), "portable dense CPU/CUDA tensor required")
         require(bool(torch.isfinite(value).all()), "nonfinite transported tensor")
         return value.detach().clone()
     if isinstance(value, np.ndarray):
         require(not value.dtype.hasobject, "object arrays are not portable")
         return value.copy()
+    if isinstance(value, np.floating):
+        require(bool(np.isfinite(value)), "nonfinite native NumPy scalar")
+        return value.copy()
+    if type(value) is OrderedDict:
+        # Current Torch state_dict carries ordered entries and module metadata.
+        result = OrderedDict((owned(key), owned(item)) for key, item in value.items())
+        if hasattr(value, "_metadata"):
+            setattr(result, "_metadata", owned(value._metadata))
+        return result
     if type(value) is dict:
         return {owned(key): owned(item) for key, item in value.items()}
     if type(value) is list:
         return [owned(item) for item in value]
     if type(value) is tuple:
         return tuple(owned(item) for item in value)
     require(value is None or type(value) in (str, int, float, bool), "nonportable checkpoint object")
     if type(value) is float:
         require(math.isfinite(value), "nonfinite scalar")
     return value
 
 
 def tensor_bytes(value: Any) -> int:
     """Metadata-only input inventory, before admission or tensor cloning."""
     if isinstance(value, torch.Tensor):
         return value.numel() * value.element_size()
     if isinstance(value, np.ndarray):
         return value.nbytes
+    if isinstance(value, np.floating):
+        return value.dtype.itemsize
+    if type(value) is OrderedDict:
+        size = sum(tensor_bytes(key) + tensor_bytes(item) for key, item in value.items())
+        if hasattr(value, "_metadata"):
+            size += tensor_bytes(value._metadata)
+        return size
     if isinstance(value, Mapping):
         return sum(tensor_bytes(key) + tensor_bytes(item) for key, item in value.items())
     if isinstance(value, (tuple, list)):
         return sum(tensor_bytes(item) for item in value)
     return 0
 
 
 def accepted_identity(accepted: WorldAcceptedEpisode) -> dict[str, Any]:
     return dict(
         batch_episode=accepted.batch_episode, world_ids=list(accepted.world_ids), world_episode_seqs=list(accepted.world_episode_seqs)
     )
 
 
 def identity(value: Any, worlds: tuple[str, ...]) -> dict[str, int]:
     keys(value, {"batch_episode", "world_ids", "world_episode_seqs"}, "accepted value identity")
-    integer(value["batch_episode"], 1, "batch episode")
+    integer(value["batch_episode"], 0, "batch episode")
     ids, episodes = value["world_ids"], value["world_episode_seqs"]
     require(type(ids) is list and type(episodes) is list and len(ids) == len(episodes) == len(worlds), "identity row geometry")
     require(all(type(world) is str and bool(world) for world in ids), "exact identity IDs")
     require(len(set(ids)) == len(ids) and set(ids) == set(worlds), "identity exact membership")
     for episode in episodes:
         integer(episode, 1, "accepted sequence")
     return dict(zip(ids, episodes, strict=True))
 
 
 def preflight(
@@ -467,21 +490,21 @@ def validate_cache(record: dict[str, Any], *, descriptor: WorldCuriosityDescript
 
 
 def validate_completion(state: dict[str, Any], *, descriptor: WorldCuriosityDescriptor) -> None:
     completion = state["completion"]
     if completion is None:
         return
     keys(completion, COMPLETION, "historical completion")
     require(completion["status"] == "committed", "historical status")
     binding = completion["original_accepted_identity"]
     episodes = identity(binding, descriptor.world_ids)
-    integer(completion["boundary_key"], 1, "completion boundary")
+    integer(completion["boundary_key"], 0, "completion boundary")
     require(completion["boundary_key"] == binding["batch_episode"], "completion boundary identity")
     records = {record["world_id"]: record for record in state["worlds"]}
     participants = tuple(world for world in binding["world_ids"] if records[world]["cursor"]["participated"])
     require(
         bool(participants) and type(completion["participated_world_ids"]) is tuple and completion["participated_world_ids"] == participants,
         "completion participation/order",
     )
     dispositions = []
     for world in binding["world_ids"]:
         cursor = records[world]["cursor"]
diff --git a/src/townlet/exploration/scoped_curiosity.py b/src/townlet/exploration/scoped_curiosity.py
index b26f177f..2a40c9dd 100644
--- a/src/townlet/exploration/scoped_curiosity.py
+++ b/src/townlet/exploration/scoped_curiosity.py
@@ -1006,45 +1006,53 @@ class CuriosityBank:
     ) -> Any:
         """Prepare every owner and runtime value without observing live owners."""
         from townlet.exploration import curiosity_checkpoint as checkpoint
 
         _require(self._prepared is None, "completion transaction pending")
         revision = self.mutation_revision
         checkpoint.preflight(state, policy=self.policy, descriptor=self.descriptor, device=self.device, mode=mode)
         checkpoint.check_mode(mode=mode, accepted=accepted, parent=parent_restore, validate=validate_parent_restore)
         size = checkpoint.tensor_bytes(state)
         reserve = self._allocation("restore", len(self.world_ids), 0)
-        components = reserve.components + (("owned_input_candidate_workspace", 5 * size),)
+        callback_bytes = 0
+        if parent_restore is not None:
+            callback_bytes = 2 * size
+        components = reserve.components + (
+            ("owned_input_candidate_workspace", 5 * size),
+            ("two_retained_parent_callback_views", callback_bytes),
+        )
         self._report(
             replace(
                 reserve,
                 known_tensor_bytes=sum(value for _, value in components),
                 components=components,
                 assumptions=reserve.assumptions
                 + (
                     "old resident plus new owners, gradients/Adam/tails, owned transport and sequential validation workspace",
                     "five input tensor inventories reserve transport, gradients, RNG, caches, outcomes and transient copies",
+                    "both independently owned parent callback views may be retained; earlier preparations/external copies excluded",
                 ),
+                unknown_components=reserve.unknown_components + ("parent callback copies and retention from earlier preparations",),
             )
         )
         saved = checkpoint.owned(state)
 
         def correlate() -> None:
             if mode == "live_episode":
                 assert accepted is not None
                 self._validate(accepted=accepted)
                 checkpoint.match_live(saved, accepted=accepted, descriptor=self.descriptor)
             elif parent_restore is not None:
                 checkpoint.match_parent(saved, parent=parent_restore, descriptor=self.descriptor)
-                before = checkpoint.owned(saved)
-                _require(validate_parent_restore(prepared=parent_restore, curiosity_state=saved) is None, "parent validator return")
-                _require(checkpoint.same(saved, before), "parent callback changed curiosity state")
+                view = checkpoint.owned(saved)
+                _require(validate_parent_restore(prepared=parent_restore, curiosity_state=view) is None, "parent validator return")
+                _require(checkpoint.same(saved, view), "parent callback changed curiosity state")
 
         correlate()
         checkpoint.validate_records(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
         owners: dict[str, OwnedWorldBackend] = {}
         shared = None
         devices: tuple[int, ...] = ()
         if self.device.type == "cuda":
             devices = (cast(int, self.device.index),)
         records = {item["world_id"]: item for item in saved["worlds"]}
         validator = partial(checkpoint.validate_native, policy=self.policy, descriptor=self.descriptor)
diff --git a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
index e1584e5c..6c5380e2 100644
--- a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
+++ b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
@@ -258,20 +258,21 @@ class Rig:
             device="cpu",
             validate_accepted_episode=self.env.validate_accepted_episode,
             issuer_factory=lambda owner: RecordedIssuer(owner, self.issued),
             report_allocation=self.report_allocation,
         )
         self.other, self.population = LocalRole(), LocalRole()
         roles = {key: self.other for key in ("curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")}
         roles.update(population=self.population, curiosity=self.bank)
         self.authority = self.env.bind_boundary_authority(owner=self.other, role_owners=roles)
         self.release, self.accepted, self.observation = None, None, None
+        self.retained_batches = (1,)
 
     def report_allocation(self, estimate):
         self.reports.append(estimate)
         if self.reject_restore_allocation and estimate.operation == "restore":
             raise MemoryError("admitted restore allocation refused")
 
     def begin(self, batch):
         if self.release is None:
             self.release = self.env.install_boundary_release(self.authority.bootstrap(first_batch_episode=batch))
         reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
@@ -398,21 +399,23 @@ class Rig:
             accepted_identity=self.accepted,
             completion_content=arguments["completion_content"],
             retirement_receipt=committed,
             **children,
         )
         self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
         self.source_prepared, self.source_committed = prepared, committed
         return self.world_checkpoint(), arguments
 
     def world_checkpoint(self):
-        return self.env.checkpoint_world_state(kind="COMPLETED", release=self.release, retained_binding_batches=(1,), initial=None)
+        return self.env.checkpoint_world_state(
+            kind="COMPLETED", release=self.release, retained_binding_batches=self.retained_batches, initial=None
+        )
 
 
 class Correlation:
     """Local parent custody control using genuine ENV preparation, never True."""
 
     def __init__(self, rig, world_state):
         self.rig, self.world_state = rig, deepcopy(world_state)
         self.prepared = rig.env.prepare_world_restore(
             kind="COMPLETED",
             state=world_state,
@@ -1392,10 +1395,104 @@ def test_current_hc_preserves_captured_rows_and_private_counters(compiled):
         pytest.fail("current captured replay must not take the historical branch")
 
     prepared = prepare_historical_envelope(payload, requested_mode="recorded_full_resume", validate_legacy=forbidden_legacy)
     decoded = decode_historical_envelope(encode_historical_envelope(prepared))
     retained = decoded.available_learned_state
     independent(retained, payload)
     assert decoded.policy.active_retained_transitions == 2
     rig.bank.install_restore(prepared=prepare(rig, retained["pw06_test_owned_bank"], "live_episode", None))
     same(rig.bank.checkpoint_state(), state)
     rig.event(6, IDS)
+
+
+@pytest.mark.parametrize("mode", ("live_episode", "completed_boundary"))
+def test_batch_zero_current_bank_resume(compiled, mode):
+    """Actual batch zero is distinct from each world's positive first sequence."""
+    source = Rig(compiled, "count_based", "per_world", IDS)
+    source.retained_batches = (0,)
+    source.begin(0)
+    assert source.accepted.batch_episode == 0
+    assert tuple(source.accepted.world_episode_seqs) == (1, 1)
+    source.actual_step()
+    source.train()
+    world_state = None
+    if mode == "completed_boundary":
+        world_state, _ = source.complete()
+        assert world_state["completed_boundary_key"] == 0 and world_state["next_batch_episode"] == 1
+    saved = source.bank.checkpoint_state()
+    destination = Rig(compiled, "count_based", "per_world", IDS[::-1])
+    destination.retained_batches = (0,)
+    parent = None
+    if mode == "live_episode":
+        destination.begin(0)
+    else:
+        parent = Correlation(destination, world_state)
+    before_rng = ambient()
+    prepared = prepare(destination, saved, mode, parent)
+    same(ambient(), before_rng)
+    destination.bank.install_restore(prepared=prepared)
+    restored = destination.bank.checkpoint_state()
+    for world in IDS:
+        independent(by_id(saved)[world], by_id(restored)[world])
+    if parent is not None:
+        same(restored["completion"], saved["completion"])
+        assert restored["completion"]["boundary_key"] == 0
+        assert "prepared_dispositions" not in destination.issued and "dispositions" not in destination.issued
+        parent.install_env()
+        destination.begin(1)
+        source.begin(1)
+        assert tuple(destination.accepted.world_episode_seqs) == (2, 2)
+    else:
+        assert restored["dispatch_identity"]["batch_episode"] == 0
+    destination.event(6, IDS)
+    source.event(6, IDS)
+    for world in IDS:
+        same(by_id(destination.bank.checkpoint_state())[world], by_id(source.bank.checkpoint_state())[world])
+
+
+@pytest.mark.parametrize("retained_view", (0, -1), ids=("first_callback", "final_callback"))
+def test_parent_retained_callback_view_cannot_mutate_prepared_history(compiled, retained_view):
+    source = Rig(compiled, "count_based", "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    world_state, _ = source.complete()
+    saved = source.bank.checkpoint_state()
+    expected = deepcopy(saved)
+    destination = Rig(compiled, "count_based", "per_world", IDS[::-1])
+    parent = Correlation(destination, world_state)
+    retained = []
+
+    def validate(*, prepared, curiosity_state):
+        parent.validate(prepared=prepared, curiosity_state=curiosity_state)
+        retained.append(curiosity_state)
+
+    prepared = destination.bank.prepare_restore(
+        state=saved,
+        mode="completed_boundary",
+        accepted=None,
+        parent_restore=parent.prepared,
+        validate_parent_restore=validate,
+    )
+    assert len(retained) >= 2 and destination.env.world_phase == "fresh-bound"
+    view = retained[retained_view]
+    view["completion"]["original_accepted_identity"]["world_ids"].reverse()
+    view["completion"]["original_accepted_identity"]["batch_episode"] = 41
+    view["completion"]["outcomes"][0]["outcome"]["final_observation"].fill_(712.0)
+    view["step"]["original_binding"]["world_ids"].reverse()
+    view["step"]["stamp"]["eligible_seqs"].fill_(713)
+    view["step"]["context"]["predecessor"].fill_(714.0)
+    same(saved, expected)
+    destination.bank.install_restore(prepared=prepared)
+    restored = destination.bank.checkpoint_state()
+    independent(restored["completion"], expected["completion"])
+    independent(restored["step"], expected["step"])
+    for world in IDS:
+        independent(by_id(restored)[world], by_id(expected)[world])
+    assert restored["dispatch_identity"] is None
+    assert "prepared_dispositions" not in destination.issued and "dispositions" not in destination.issued
+    with pytest.raises(REFUSAL):
+        destination.bank.commit_completion(prepared=source.source_prepared)
+    parent.install_env()
+    destination.begin(2)
+    assert tuple(destination.accepted.world_episode_seqs) == (2, 2)
+    destination.event(6, IDS)
