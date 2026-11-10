# Fixround1 actual staged-tree delta R1 -> R3

 src/townlet/config/world_roster.py                 |  14 +-
 src/townlet/environment/vectorized_env.py          |  94 ++++++++++---
 .../regressions/bac/test_world_episode_identity.py | 149 +++++++++++++++++++--
 3 files changed, 229 insertions(+), 28 deletions(-)

diff --git a/src/townlet/config/world_roster.py b/src/townlet/config/world_roster.py
index 8c11a337..2bf889af 100644
--- a/src/townlet/config/world_roster.py
+++ b/src/townlet/config/world_roster.py
@@ -104,17 +104,17 @@ class WorldRecord:
             raise AttributeError(name)
         payload = object.__getattribute__(self, "_payload")
         if name not in payload:
             raise AttributeError(name)
         return owned_value(payload[name])
 
     @property
     def payload(self) -> dict[str, Any]:
-        return owned_value(self._payload)
+        return {key: owned_value(value) for key, value in self._payload.items()}
 
 
 @dataclass(frozen=True, eq=False)
 class WorldOwnerReceipt(WorldRecord):
     _issuer: object
 
     @property
     def owner(self) -> object:
@@ -242,17 +242,17 @@ def validate_world_snapshot(
         if (
             any(cursors.values())
             or history
             or state["last_closed_episode"] is not None
             or state["completed_boundary_key"] is not None
             or state["saved_lane_binding"] is not None
         ):
             raise ValueError("INITIAL cannot contain accepted or completed history")
-        return owned_value(state)
+        return {key: owned_value(value) for key, value in state.items()}
     batch = exact_integer(state["completed_boundary_key"], 0, "completed boundary")
     if next_batch != batch + 1 or not all(cursors.values()):
         raise ValueError("completed next batch or accepted cursors disagree")
     saved_ids = binding(state["saved_lane_binding"])
     previous_batch, previous_sequence = None, None
     for item in history:
         if not isinstance(item, Mapping) or set(item) != {"batch_episode", "world_ids", "world_episode_seqs"}:
             raise ValueError("accepted binding requires exact fields")
@@ -274,18 +274,26 @@ def validate_world_snapshot(
     if not isinstance(last, Mapping) or set(last) != {
         "batch_episode",
         "world_ids",
         "world_episode_seqs",
         "completion_content",
         "participated_world_ids",
     }:
         raise ValueError("completed snapshot requires exact last closure")
+    exact_integer(last["batch_episode"], 0, "last closure batch")
+    if not isinstance(last["world_ids"], list) or not isinstance(last["world_episode_seqs"], list):
+        raise ValueError("last closure identities require serialized lists")
+    exact_world_ids(last["world_ids"])
+    if len(last["world_episode_seqs"]) != len(last["world_ids"]):
+        raise ValueError("last closure sequence shape disagrees")
+    for sequence in last["world_episode_seqs"]:
+        exact_integer(sequence, 1, "last closure sequence")
     if not history or history[-1]["batch_episode"] != batch or last["batch_episode"] != batch:
         raise ValueError("missing last accepted binding provenance")
     for name in ("world_ids", "world_episode_seqs"):
         if last[name] != history[-1][name]:
             raise ValueError("last closure contradicts accepted provenance")
     if tuple(last["world_ids"]) != saved_ids or dict(zip(saved_ids, last["world_episode_seqs"], strict=True)) != cursors:
         raise ValueError("last saved binding contradicts current cursors")
     if not set(exact_world_ids(last["participated_world_ids"])).issubset(membership):
         raise ValueError("last closure participants are not declared worlds")
-    return owned_value(state)
+    return {key: owned_value(value) for key, value in state.items()}
diff --git a/src/townlet/environment/vectorized_env.py b/src/townlet/environment/vectorized_env.py
index 1bb6796d..5a8f77c0 100644
--- a/src/townlet/environment/vectorized_env.py
+++ b/src/townlet/environment/vectorized_env.py
@@ -73,16 +73,25 @@ if TYPE_CHECKING:
     from townlet.population.runtime_registry import AgentRuntimeRegistry
     from townlet.universe.compiled import CompiledUniverse
     from townlet.vfs.schema import VariableDef
 
 
 # Import consolidated NullItemManager (ENV-009)
 from townlet.environment.null_managers import NullItemManager
 
+_WORLD_ROLES = {"population", "curiosity", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection"}
+_EFFECT_ROLES = {
+    "curriculum_receipt": "curriculum",
+    "exploration_receipt": "exploration",
+    "population_commit_receipt": "population",
+    "epsilon_install_receipt": "exploration",
+    "selection_sync_receipt": "selection",
+}
+
 
 class WorldReceiptIssuer:
     """Cooperative owner custody; copied or duck-typed evidence is never issued."""
 
     def __init__(self, *, owner: object):
         self._owner = owner
         self._issued: WeakValueDictionary[int, WorldOwnerReceipt] = WeakValueDictionary()
 
@@ -152,19 +161,25 @@ class WorldBoundaryAuthority:
             raise ValueError("effects require the exact accepted boundary")
         exact_integer(fields["batch_episode"], 0, "effects batch")
         if fields["batch_episode"] != closure.boundary_key or not same_value(fields["completion_content"], closure.completion_content):
             raise ValueError("effects disagree with closure content")
         if fields["retirement_receipt"] is not closure.dispositions:
             raise ValueError("retirement evidence disagrees")
         for name in required - {"batch_episode", "accepted_identity", "completion_content", "retirement_receipt"}:
             child = fields[name]
-            WorldReceiptIssuer.validate(child, name, child.owner if isinstance(child, WorldOwnerReceipt) else None)
+            WorldReceiptIssuer.validate(child, name, env._world_role_owners[_EFFECT_ROLES[name]])
+            if set(child.payload) != {"accepted", "boundary_key", "completion_content"}:
+                raise ValueError("effect receipt requires exact correlation fields")
             exact_integer(child.boundary_key, 0, "effect boundary")
-            if child.accepted is not env._world_accepted or child.boundary_key != closure.boundary_key:
+            if (
+                child.accepted is not env._world_accepted
+                or child.boundary_key != closure.boundary_key
+                or not same_value(child.completion_content, closure.completion_content)
+            ):
                 raise ValueError("effect receipt belongs to another boundary")
         return env._equal_record(
             "completed_release",
             "release",
             {
                 "release_kind": "completed",
                 "next_batch_episode": closure.boundary_key + 1,
                 "closure": closure,
@@ -172,31 +187,40 @@ class WorldBoundaryAuthority:
             },
         )
 
     def prepare_initial_snapshot(self, *, release: WorldRecord, owners: WorldOwnerReceipt) -> WorldRecord:
         env = self._bound_env()
         env._require_phase("bootstrap-ready")
         env._require_release(release)
         proof = WorldReceiptIssuer.validate(owners, "initial_owners", self._owner)
+        exact_integer(proof.bootstrap_first_batch, 0, "initial bootstrap batch")
         fields = proof.payload
         names = {"population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection"}
         if set(fields) != names | {"semantic_execution_identity", "bootstrap_first_batch", "world_binding"}:
             raise ValueError("initial preparation requires every current owner")
         if (
             proof.semantic_execution_identity != env.semantic_execution_identity
             or proof.bootstrap_first_batch != release.next_batch_episode
             or tuple(proof.world_binding) != env.world_ids
         ):
             raise ValueError("initial owner identity disagrees")
         for name in names:
             child = fields[name]
-            WorldReceiptIssuer.validate(child, "initial_owner", child.owner if isinstance(child, WorldOwnerReceipt) else None)
-            if set(child.payload) != {"state"}:
+            WorldReceiptIssuer.validate(child, "initial_owner", env._world_role_owners[name])
+            if set(child.payload) != {"role", "state", "semantic_execution_identity", "bootstrap_first_batch", "world_binding"}:
                 raise ValueError("initial owner must provide its prepared current state")
+            if (
+                child.role != name
+                or child.semantic_execution_identity != env.semantic_execution_identity
+                or type(child.bootstrap_first_batch) is not int
+                or child.bootstrap_first_batch != release.next_batch_episode
+                or tuple(child.world_binding) != env.world_ids
+            ):
+                raise ValueError("initial owner role or correlation disagrees")
         return env._record("initial_snapshot", {"release": release, "owners": owners})
 
     def restored(self, *, restore: WorldRecord, boundary: WorldOwnerReceipt) -> WorldRecord:
         env = self._bound_env()
         env._require_phase("fresh-bound")
         env._valid_record(restore, "prepared_restore")
         proof = WorldReceiptIssuer.validate(boundary, "restored_boundary", self._owner)
         if set(proof.payload) != {"kind", "state", "prepared"} or proof.prepared is not restore:
@@ -214,16 +238,33 @@ class VectorizedHamletEnv:
 
     Batches multiple independent environments for parallel execution.
     All state is stored as PyTorch tensors on specified device.
     """
 
     EFFECT_OBS_SLOTS = 8  # Fixed number of observable effect slots per agent
 
     runtime_registry: AgentRuntimeRegistry | None
+    positions: torch.Tensor
+    _velocity: torch.Tensor
+    meters: torch.Tensor
+    dones: torch.Tensor
+    step_counts: torch.Tensor
+    intrinsic_weights: torch.Tensor
+    _movement_deltas: torch.Tensor
+    meter_bounds_min: torch.Tensor
+    meter_bounds_max: torch.Tensor
+    interaction_progress: torch.Tensor
+    last_interaction_position: torch.Tensor
+    time_of_day: int
+    vtc_reward_program: VTCRewardProgram
+    action_space: ComposedActionSpace
+    action_ids: dict[str, int]
+    affordances: dict[str, torch.Tensor]
+    affordance_engine: AffordanceEngine
 
     def __init__(
         self,
         *,
         universe: CompiledUniverse,
         level_name: str,
         num_agents: int,
         device: torch.device | str,
@@ -1241,16 +1282,17 @@ class VectorizedHamletEnv:
             observations: [num_agents, observation_dim]
             rewards: [num_agents]
             dones: [num_agents] bool
             info: dict with metadata and owned bool [num_agents, action_dim]
                 successor_action_masks for this same committed observation/status
         """
         if self._world_phase != "active":
             raise ValueError("world episode must be accepted and activated before stepping")
+        self._world_revision += 1
         prev_dones = self.dones.clone()
         active_on_entry = ~prev_dones
         self.vfs_registry.reset_tick_scoped()
         refusals_before = 0
         if self.effect_manager is not None:
             refusals_before = len(self.effect_manager.spawn_refusals)
         # 1. Execute actions and track successful interactions
         successful_interactions = self._action_executor._execute_actions(actions)
@@ -1881,16 +1923,19 @@ class VectorizedHamletEnv:
         ids = exact_world_ids(lane_ids)
         exact_integer(count, 1, "world count")
         exact_integer(seed, 0, "training seed")
         if len(ids) != count or set(ids) != set(roster.world_ids):
             raise ValueError("lane binding must contain the exact declared roster")
         self._world_roster, self._world_seed, self._world_ids = roster, seed, ids
         self._world_identity = canonical_hash({"execution": execution_identity, "membership": roster.semantic_identity, "seed": seed})
         self._world_phase, self._world_generation = "fresh-unbound", 0
+        self._world_revision = 0
+        self._world_role_owners: Mapping[str, object] = {}
+        self._world_frozen: WorldRecord | None = None
         self._world_cursors = dict.fromkeys(ids, 0)
         self._world_records: WeakValueDictionary[int, WorldRecord] = WeakValueDictionary()
         self._world_equal: dict[str, WorldRecord] = {}
         self._world_bindings: dict[int, dict[str, Any]] = {}
         self._world_authority: WorldBoundaryAuthority | None = None
         self._world_bootstrap: WorldRecord | None = None
         self._world_release: WorldRecord | None = None
         self._world_accepted: WorldAcceptedEpisode | None = None
@@ -1947,23 +1992,28 @@ class VectorizedHamletEnv:
         self._world_equal[key] = result
         return result
 
     def _require_release(self, release: WorldRecord) -> None:
         self._valid_record(release, "release")
         if release is not self._world_release:
             raise ValueError("world operation requires the installed release")
 
-    def bind_boundary_authority(self, *, owner: object) -> WorldBoundaryAuthority:
+    def bind_boundary_authority(self, *, owner: object, role_owners: Mapping[str, object]) -> WorldBoundaryAuthority:
+        if not isinstance(role_owners, Mapping) or set(role_owners) != _WORLD_ROLES or any(value is None for value in role_owners.values()):
+            raise ValueError("boundary authority requires every actual role owner")
         if self._world_authority is not None:
-            if self._world_authority._owner is not owner:
+            if self._world_authority._owner is not owner or any(
+                role_owners[key] is not self._world_role_owners[key] for key in _WORLD_ROLES
+            ):
                 raise ValueError("world boundary authority is already bound")
             return self._world_authority
         self._require_phase("fresh-unbound")
         self._world_authority = WorldBoundaryAuthority(self, owner)
+        self._world_role_owners = MappingProxyType(dict(role_owners))
         self._world_phase = "fresh-bound"
         return self._world_authority
 
     def install_boundary_release(self, release: WorldRecord) -> WorldRecord:
         self._valid_record(release, "release")
         if release is self._world_release:
             self._require_phase("bootstrap-ready", "released-completed")
             return release
@@ -2046,16 +2096,17 @@ class VectorizedHamletEnv:
                 "world_episode_seqs": list(accepted.world_episode_seqs),
             }
             self._world_generation = generation
             receipt = self._record("reset", {"accepted": accepted, "observation": observation})
             self._world_cursors = dict(zip(accepted.world_ids, accepted.world_episode_seqs, strict=True))
             self._world_bindings[accepted.batch_episode] = binding
             self._world_accepted, self._world_reset, self._world_reservation = accepted, receipt, reservation
             self._world_restored = None
+            self._world_frozen = None
             self._world_equal = {}
             self._world_closure, self._world_release = None, None
             self._world_phase = "active-awaiting-activation"
             return receipt
         except BaseException:
             self._world_phase = "quarantined"
             raise
 
@@ -2063,19 +2114,18 @@ class VectorizedHamletEnv:
         if accepted is not self._world_accepted or accepted is None:
             raise ValueError("accepted episode must be this ENV's current token")
 
     def activate_episode(
         self, *, accepted: WorldAcceptedEpisode, population_receipt: WorldOwnerReceipt, curiosity_receipt: WorldOwnerReceipt
     ) -> WorldRecord:
         self._require_phase("active-awaiting-activation", "active")
         self._accepted(accepted)
-        receipts = (population_receipt, curiosity_receipt)
-        for receipt in receipts:
-            WorldReceiptIssuer.validate(receipt, "activation", receipt.owner if isinstance(receipt, WorldOwnerReceipt) else None)
+        for role, receipt in (("population", population_receipt), ("curiosity", curiosity_receipt)):
+            WorldReceiptIssuer.validate(receipt, "activation", self._world_role_owners[role])
             if set(receipt.payload) != {"accepted"} or receipt.accepted is not accepted:
                 raise ValueError("activation receipt identity disagrees")
         owners = (population_receipt.owner, curiosity_receipt.owner)
         if self._world_consumers is not None and any(a is not b for a, b in zip(owners, self._world_consumers, strict=True)):
             raise ValueError("episode consumers cannot change inside an ENV")
         result = self._equal_record(
             "activation", "activation", {"accepted": accepted, "population": population_receipt, "curiosity": curiosity_receipt}
         )
@@ -2095,17 +2145,17 @@ class VectorizedHamletEnv:
         self._accepted(accepted)
         exact_integer(boundary_key, 0, "boundary key")
         participants = exact_world_ids(participated_world_ids)
         actual = {key for index, key in enumerate(self.world_ids) if int(self.step_counts[index]) > 0}
         if boundary_key != accepted.batch_episode or set(participants) != actual:
             raise ValueError("closure requires exactly the genuinely participated worlds")
         if self._world_consumers is None:
             raise ValueError("closure requires activated consumers")
-        proof = WorldReceiptIssuer.validate(dispositions, "dispositions", self._world_consumers[1])
+        proof = WorldReceiptIssuer.validate(dispositions, "prepared_dispositions", self._world_consumers[1])
         if set(proof.payload) != {"accepted", "boundary_key", "completion_content", "participated_world_ids", "dispositions"}:
             raise ValueError("disposition receipt requires complete fields")
         exact_integer(proof.boundary_key, 0, "disposition boundary")
         expected = tuple((key, "completed" if key in actual else "retired_nonparticipating") for key in self.world_ids)
         if (
             proof.accepted is not accepted
             or proof.boundary_key != boundary_key
             or tuple(proof.participated_world_ids) != participants
@@ -2114,26 +2164,40 @@ class VectorizedHamletEnv:
         ):
             raise ValueError("committed dispositions disagree with the accepted episode")
         payload = {
             "accepted": accepted,
             "boundary_key": boundary_key,
             "completion_content": completion_content,
             "participated_world_ids": participants,
             "dispositions": dispositions,
+            "revision": self._world_revision,
         }
-        if self._world_closure is not None and not same_value(self._world_closure.payload, payload):
-            raise ValueError("changed duplicate closure")
         return self._record("prepared_close", payload)
 
-    def close_episode(self, prepared: WorldRecord) -> WorldRecord:
-        self._require_phase("active", "closed-awaiting-release", "released-completed")
+    def freeze_episode_close(self, prepared: WorldRecord) -> WorldRecord:
+        self._require_phase("active", "boundary-pending", "closed-awaiting-release", "released-completed")
         self._valid_record(prepared, "prepared_close")
         self._accepted(prepared.accepted)
-        closure = self._equal_record("closure", "closure", prepared.payload)
+        if prepared.revision != self._world_revision or (self._world_frozen is not None and self._world_frozen is not prepared):
+            raise ValueError("closure preparation is stale or another boundary is frozen")
+        if self._world_frozen is prepared:
+            return prepared
+        self._world_frozen, self._world_phase = prepared, "boundary-pending"
+        return prepared
+
+    def close_episode(self, prepared: WorldRecord, *, dispositions: WorldOwnerReceipt) -> WorldRecord:
+        self._require_phase("boundary-pending", "closed-awaiting-release", "released-completed")
+        self._valid_record(prepared, "prepared_close")
+        if prepared is not self._world_frozen or prepared.revision != self._world_revision:
+            raise ValueError("closure requires the frozen current preparation")
+        WorldReceiptIssuer.validate(dispositions, "dispositions", self._world_role_owners["curiosity"])
+        if not same_value(dispositions.payload, prepared.dispositions.payload):
+            raise ValueError("committed bank disposition disagrees with prepared content")
+        closure = self._equal_record("closure", "closure", {**prepared.payload, "dispositions": dispositions})
         if self._world_closure is not None:
             return closure
         accepted = prepared.accepted
         last = {
             "batch_episode": accepted.batch_episode,
             "world_ids": list(accepted.world_ids),
             "world_episode_seqs": list(accepted.world_episode_seqs),
             "completion_content": owned_value(prepared.completion_content),
diff --git a/tests/test_townlet/regressions/bac/test_world_episode_identity.py b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
index ac69b687..29b99211 100644
--- a/tests/test_townlet/regressions/bac/test_world_episode_identity.py
+++ b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
@@ -115,17 +115,21 @@ class _Sink:
 
 
 class _Run:
     def __init__(self, env, bootstrap=True):
         self.env = env
         self.boundary = _Sink()
         self.population = _Sink()
         self.bank = _Sink()
-        self.authority = env.bind_boundary_authority(owner=self.boundary)
+        self.roles = dict.fromkeys(
+            "population curiosity curriculum exploration network optimizer scheduler replay selection".split(), self.boundary
+        )
+        self.roles.update(population=self.population, curiosity=self.bank)
+        self.authority = env.bind_boundary_authority(owner=self.boundary, role_owners=self.roles)
         self.release = None
         self.accepted = None
         self.events = {}
         if bootstrap:
             self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))
 
     def reset(self, batch):
         reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
@@ -156,37 +160,41 @@ class _Run:
             for index, world_id in enumerate(self.accepted.world_ids)
             if world_id in participants
         )
         self.events[batch] = content
         dispositions = tuple(
             (world_id, "completed" if world_id in participants else "retired_nonparticipating") for world_id in self.accepted.world_ids
         )
         receipt = self.bank.receipt(
-            "dispositions",
+            "prepared_dispositions",
             accepted=self.accepted,
             boundary_key=batch,
             completion_content=content,
             participated_world_ids=tuple(participants),
             dispositions=dispositions,
         )
         prepared = self.env.prepare_episode_close(
             accepted=self.accepted,
             boundary_key=batch,
             completion_content=content,
             participated_world_ids=tuple(participants),
             dispositions=receipt,
         )
-        closure = self.env.close_episode(prepared)
+        self.env.freeze_episode_close(prepared)
+        receipt = self.bank.receipt("dispositions", **receipt.payload)
+        closure = self.env.close_episode(prepared, dispositions=receipt)
         self.bank.records[batch] = dispositions
         return prepared, closure, receipt
 
     def release_closed(self, batch, closure, dispositions):
         fields = {
-            name: self.boundary.receipt(name, accepted=self.accepted, boundary_key=batch)
+            name: (self.population if name == "population_commit_receipt" else self.boundary).receipt(
+                name, accepted=self.accepted, boundary_key=batch, completion_content=self.events[batch]
+            )
             for name in (
                 "curriculum_receipt",
                 "exploration_receipt",
                 "population_commit_receipt",
                 "epsilon_install_receipt",
                 "selection_sync_receipt",
             )
         }
@@ -199,17 +207,24 @@ class _Run:
             **fields,
         )
         release = self.authority.completed(closure=closure, effects=effects)
         self.release = self.env.install_boundary_release(release)
         return effects
 
     def initial(self):
         owner_fields = {
-            name: self.boundary.receipt("initial_owner", state={"weights": self.boundary.initial_weight.clone()})
+            name: self.roles[name].receipt(
+                "initial_owner",
+                state={"weights": self.boundary.initial_weight.clone()},
+                role=name,
+                semantic_execution_identity=self.env.semantic_execution_identity,
+                bootstrap_first_batch=1,
+                world_binding=self.env.world_ids,
+            )
             for name in ("population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
         }
         owners = self.boundary.receipt(
             "initial_owners",
             semantic_execution_identity=self.env.semantic_execution_identity,
             bootstrap_first_batch=1,
             world_binding=self.env.world_ids,
             **owner_fields,
@@ -323,20 +338,20 @@ def test_reservation_and_failed_preflight_are_pure(compiled):
         run.env.validate_episode_reservation(foreign_reservation)
     _same(before, _state(run.env))
     run.env.validate_episode_reservation(first)
     _same(before, _state(run.env))
 
 
 def test_authority_bootstrap_binding_and_consumption(compiled):
     run = _Run(_env(compiled))
-    assert run.env.bind_boundary_authority(owner=run.boundary) is run.authority
+    assert run.env.bind_boundary_authority(owner=run.boundary, role_owners=run.roles) is run.authority
     before = _state(run.env)
     with pytest.raises(ValueError):
-        run.env.bind_boundary_authority(owner=_Sink())
+        run.env.bind_boundary_authority(owner=_Sink(), role_owners=run.roles)
     _same(before, _state(run.env))
     reservation, reset = run.reset(1)
     assert reset.accepted.world_episode_seqs == (1, 1)
     with pytest.raises(ValueError):
         run.authority.bootstrap(first_batch_episode=1)
     with pytest.raises(ValueError):
         run.env.prepare_episode(batch_episode=2, release=run.release)
     assert run.env.reset(reservation=reservation) is reset
@@ -407,17 +422,17 @@ def test_late_reset_failure_quarantines_without_false_rollback(compiled, monkeyp
 
 
 def test_close_alone_blocks_save_next_release_is_save_independent(compiled):
     run = _Run(_env(compiled))
     run.reset(1)
     run.step()
     prepared, closure, dispositions = run.close(1)
     before = _state(run.env)
-    assert run.env.close_episode(prepared) is closure
+    assert run.env.close_episode(prepared, dispositions=dispositions) is closure
     _same(before, _state(run.env))
     with pytest.raises(ValueError):
         run.completed((1,))
     with pytest.raises(ValueError):
         run.env.prepare_episode(batch_episode=2, release=run.release)
     run.release_closed(1, closure, dispositions)
     assert run.env.install_boundary_release(run.release) is run.release
     # No checkpoint call between release and the next successful reset.
@@ -430,27 +445,27 @@ def test_wrong_release_and_changed_disposition_are_pure(compiled):
     before = _state(run.env)
     with pytest.raises(ValueError):
         run.env.install_boundary_release(foreign.release)
     _same(before, _state(run.env))
     run.reset(1)
     run.step((IDS[0],))
     prepared, closure, dispositions = run.close(1, (IDS[0],))
     before = _state(run.env)
-    forged = replace(dispositions)
+    forged = replace(run.bank.receipt("prepared_dispositions", **dispositions.payload))
     with pytest.raises((TypeError, ValueError)):
         run.env.prepare_episode_close(
             accepted=run.accepted,
             boundary_key=1,
             completion_content=run.events[1],
             participated_world_ids=(IDS[0],),
             dispositions=forged,
         )
     _same(before, _state(run.env))
-    assert run.env.close_episode(prepared) is closure
+    assert run.env.close_episode(prepared, dispositions=dispositions) is closure
 
 
 def test_empty_abandon_is_not_completion_or_initial(compiled):
     run = _Run(_env(compiled))
     run.reset(1)
     abandoned = run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
     assert run.env.abandon_episode(accepted=run.accepted, reason="empty_participation") is abandoned
     assert run.env.world_phase == "quarantined"
@@ -694,8 +709,122 @@ def test_foreign_boundary_effect_receipt_cannot_release(compiled):
         retirement_receipt=dispositions,
     )
     before = _state(run.env)
     with pytest.raises((ValueError, TypeError)):
         run.authority.completed(closure=closure, effects=foreign)
     with pytest.raises(ValueError):
         run.initial()
     _same(before, _state(run.env))
+
+
+@pytest.mark.parametrize(
+    "field,value", [("batch_episode", True), ("batch_episode", 1.0), ("world_episode_seqs", [True, 1]), ("world_episode_seqs", [1.0, 1])]
+)
+def test_last_closure_numeric_alias_refuses(compiled, field, value):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step()
+    _, closure, dispositions = run.close(1)
+    run.release_closed(1, closure, dispositions)
+    state = run.completed((1,))
+    state["last_closed_episode"][field] = value
+    target = _Run(_env(compiled), bootstrap=False)
+    before = _state(target.env)
+    with pytest.raises(ValueError):
+        target.env.prepare_world_restore(
+            kind="COMPLETED",
+            state=state,
+            world_roster=_roster(),
+            destination_world_ids=IDS,
+            semantic_execution_identity=target.env.semantic_execution_identity,
+        )
+    _same(before, _state(target.env))
+
+
+@pytest.mark.parametrize("damage", ["foreign_effect", "wrong_content", "foreign_initial"])
+def test_bound_outer_proof_rejects_wrong_child(compiled, monkeypatch, damage):
+    run = _Run(_env(compiled))
+    issuer = run.boundary if damage == "foreign_initial" else run.population
+    original = issuer.receipt
+    foreign = _Sink()
+
+    def altered(kind, **payload):
+        if kind == "population_commit_receipt":
+            if damage == "foreign_effect":
+                return foreign.receipt(kind, **payload)
+            if damage == "wrong_content":
+                payload["completion_content"] = (("changed-same-boundary",),)
+        if kind == "initial_owner" and damage == "foreign_initial":
+            return foreign.receipt(kind, **payload)
+        return original(kind, **payload)
+
+    monkeypatch.setattr(issuer, "receipt", altered)
+    if damage == "foreign_initial":
+        before = _state(run.env)
+        with pytest.raises(ValueError):
+            run.initial()
+    else:
+        run.reset(1)
+        run.step()
+        _, closure, dispositions = run.close(1)
+        before = _state(run.env)
+        with pytest.raises(ValueError):
+            run.release_closed(1, closure, dispositions)
+    _same(before, _state(run.env))
+
+
+def test_prepared_close_refuses_intervening_rollout(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step((IDS[0],))
+    content = ((1, 0, IDS[0], 1, "interface-outcome"),)
+    dispositions = run.bank.receipt(
+        "prepared_dispositions",
+        accepted=run.accepted,
+        boundary_key=1,
+        completion_content=content,
+        participated_world_ids=(IDS[0],),
+        dispositions=((IDS[0], "completed"), (IDS[1], "retired_nonparticipating")),
+    )
+    prepared = run.env.prepare_episode_close(
+        accepted=run.accepted,
+        boundary_key=1,
+        completion_content=content,
+        participated_world_ids=(IDS[0],),
+        dispositions=dispositions,
+    )
+    run.step(IDS)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.freeze_episode_close(prepared)
+    _same(before, _state(run.env))
+
+
+def test_closure_installed_before_acknowledgement_retries_once(compiled, monkeypatch):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step()
+    original = run.env.close_episode
+    captured = []
+
+    def interrupted(prepared, **kwargs):
+        assert run.env.world_phase == "boundary-pending"
+        frozen = _state(run.env)
+        with pytest.raises(ValueError):
+            run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
+        assert run.env.freeze_episode_close(prepared) is prepared
+        _same(frozen, _state(run.env))
+        closure = original(prepared, **kwargs)
+        captured.append((prepared, kwargs, closure))
+        raise RuntimeError("after closure installation")
+
+    monkeypatch.setattr(run.env, "close_episode", interrupted)
+    with pytest.raises(RuntimeError, match="after closure installation"):
+        run.close(1)
+    prepared, kwargs, closure = captured[0]
+    before = _state(run.env)
+    assert run.env.freeze_episode_close(prepared) is prepared
+    assert original(prepared, **kwargs) is closure
+    _same(before, _state(run.env))
+    assert run.env.world_phase == "closed-awaiting-release"
+    run.release_closed(1, closure, closure.dispositions)
+    assert run.reset(2)[1].accepted.world_episode_seqs == (2, 2)
