# World identity actual R1 review package

Base28830be0f794be3514ddcde751d58f47478cdabb; staged candidate2ab1dfdc105a9ae3e559c829096c1e50ca3860a7.

 src/townlet/config/world_roster.py                 | 291 +++++++++
 src/townlet/environment/vectorized_env.py          | 572 ++++++++++++++++-
 .../regressions/bac/test_world_episode_identity.py | 701 +++++++++++++++++++++
 3 files changed, 1560 insertions(+), 4 deletions(-)

diff --git a/src/townlet/config/world_roster.py b/src/townlet/config/world_roster.py
new file mode 100644
index 00000000..8c11a337
--- /dev/null
+++ b/src/townlet/config/world_roster.py
@@ -0,0 +1,291 @@
+"""Current authored world declarations and immutable lifecycle value records.
+
+This module owns data only. ENV owns issuance, acceptance and all live cursors.
+"""
+
+from __future__ import annotations
+
+import hashlib
+import json
+from collections.abc import Mapping
+from dataclasses import dataclass
+from types import MappingProxyType
+from typing import Any
+
+import torch
+
+
+def canonical_hash(value: Any) -> str:
+    return hashlib.sha256(canonical_bytes(value)).hexdigest()
+
+
+def canonical_bytes(value: Any) -> bytes:
+    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
+
+
+def exact_integer(value: Any, minimum: int, name: str) -> int:
+    if type(value) is not int or value < minimum:
+        raise ValueError(f"{name} requires an integer >= {minimum}")
+    return value
+
+
+def exact_world_ids(value: Any) -> tuple[str, ...]:
+    if not isinstance(value, (tuple, list)) or not value:
+        raise ValueError("world IDs require a nonempty ordered sequence")
+    if any(not isinstance(item, str) or not item for item in value):
+        raise ValueError("world IDs require exact nonempty strings")
+    if len(set(value)) != len(value):
+        raise ValueError("world IDs must be unique")
+    return tuple(value)
+
+
+def world_binding(world_ids: tuple[str, ...]) -> dict[str, Any]:
+    values = {"schema": "world-binding-v1", "world_ids": list(exact_world_ids(world_ids))}
+    return {**values, "hash": canonical_hash(values)}
+
+
+@dataclass(frozen=True)
+class WorldRosterDeclaration:
+    world_ids: tuple[str, ...]
+
+    def __post_init__(self) -> None:
+        object.__setattr__(self, "world_ids", exact_world_ids(self.world_ids))
+
+    @classmethod
+    def from_dict(cls, payload: Mapping[str, Any]) -> WorldRosterDeclaration:
+        if not isinstance(payload, Mapping) or set(payload) != {"schema", "world_ids"}:
+            raise ValueError("world roster requires exact current fields")
+        if payload["schema"] != "world-roster-v1" or not isinstance(payload["world_ids"], list):
+            raise ValueError("world roster requires current schema and serialized ID list")
+        return cls(exact_world_ids(payload["world_ids"]))
+
+    def to_dict(self) -> dict[str, Any]:
+        return {"schema": "world-roster-v1", "world_ids": list(self.world_ids)}
+
+    @property
+    def semantic_identity(self) -> str:
+        return canonical_hash({"schema": "world-membership-v1", "world_ids": sorted(self.world_ids)})
+
+    @property
+    def manifest_digest(self) -> str:
+        return hashlib.sha256(canonical_bytes(self.to_dict()) + b"\n").hexdigest()
+
+
+@dataclass(frozen=True, eq=False)
+class WorldEpisodeReservation:
+    world_ids: tuple[str, ...]
+    world_episode_seqs: tuple[int, ...]
+    batch_episode: int
+    _owner: object
+    _generation: int
+    _release: WorldRecord
+
+
+@dataclass(frozen=True, eq=False)
+class WorldAcceptedEpisode:
+    world_ids: tuple[str, ...]
+    world_episode_seqs: tuple[int, ...]
+    batch_episode: int
+    _owner: object
+    _generation: int
+
+
+@dataclass(frozen=True, eq=False)
+class WorldRecord:
+    """Owned data with in-process capability identity; never serialize the owner."""
+
+    kind: str
+    _owner: object
+    _generation: int
+    _payload: Mapping[str, Any]
+
+    def __getattr__(self, name: str) -> Any:
+        if name.startswith("_"):
+            raise AttributeError(name)
+        payload = object.__getattribute__(self, "_payload")
+        if name not in payload:
+            raise AttributeError(name)
+        return owned_value(payload[name])
+
+    @property
+    def payload(self) -> dict[str, Any]:
+        return owned_value(self._payload)
+
+
+@dataclass(frozen=True, eq=False)
+class WorldOwnerReceipt(WorldRecord):
+    _issuer: object
+
+    @property
+    def owner(self) -> object:
+        return self._owner
+
+
+class _FrozenList(tuple):
+    """Preserve portable list shape while owning immutable internal storage."""
+
+
+def owned_value(value: Any) -> Any:
+    """Copy mutable values while preserving already-issued opaque capabilities."""
+    if isinstance(value, (WorldRecord, WorldEpisodeReservation, WorldAcceptedEpisode)):
+        return value
+    if isinstance(value, torch.Tensor):
+        return value.detach().clone()
+    if isinstance(value, Mapping):
+        return {key: owned_value(item) for key, item in value.items()}
+    if isinstance(value, _FrozenList):
+        return [owned_value(item) for item in value]
+    if isinstance(value, tuple):
+        return tuple(owned_value(item) for item in value)
+    if isinstance(value, list):
+        return [owned_value(item) for item in value]
+    if value is None or type(value) in (str, int, float, bool):
+        return value
+    raise ValueError(f"unsupported world receipt value: {type(value).__name__}")
+
+
+def frozen_value(value: Any) -> Any:
+    if isinstance(value, Mapping):
+        if any(not isinstance(key, str) for key in value):
+            raise ValueError("receipt mappings require string keys")
+        return MappingProxyType({key: frozen_value(item) for key, item in value.items()})
+    if isinstance(value, list):
+        return _FrozenList(frozen_value(item) for item in value)
+    if isinstance(value, tuple):
+        return tuple(frozen_value(item) for item in value)
+    return owned_value(value)
+
+
+def same_value(left: Any, right: Any) -> bool:
+    if isinstance(left, torch.Tensor):
+        return (
+            isinstance(right, torch.Tensor)
+            and left.dtype == right.dtype
+            and left.device == right.device
+            and left.shape == right.shape
+            and torch.equal(left, right)
+        )
+    if isinstance(left, Mapping):
+        return isinstance(right, Mapping) and left.keys() == right.keys() and all(same_value(left[key], right[key]) for key in left)
+    if isinstance(left, (tuple, list)):
+        return (
+            isinstance(right, (tuple, list)) and len(left) == len(right) and all(same_value(a, b) for a, b in zip(left, right, strict=True))
+        )
+    if isinstance(left, WorldOwnerReceipt):
+        return (
+            isinstance(right, WorldOwnerReceipt)
+            and left.owner is right.owner
+            and left.kind == right.kind
+            and same_value(left.payload, right.payload)
+        )
+    if isinstance(left, (WorldRecord, WorldEpisodeReservation, WorldAcceptedEpisode)):
+        return left is right
+    return type(left) is type(right) and left == right
+
+
+def validate_world_snapshot(
+    state: Mapping[str, Any], kind: str, roster: WorldRosterDeclaration, seed: int, semantic_identity: str
+) -> dict[str, Any]:
+    """Pure current-native structure and available accepted-history validation."""
+    keys = {
+        "schema",
+        "kind",
+        "next_batch_episode",
+        "world_roster",
+        "manifest_digest",
+        "roster_semantic_identity",
+        "training_seed",
+        "execution_identity",
+        "saved_lane_binding",
+        "destination_lane_binding",
+        "accepted_episode_seqs",
+        "last_closed_episode",
+        "completed_boundary_key",
+        "accepted_bindings",
+    }
+    if not isinstance(state, Mapping) or set(state) != keys or state["schema"] != "world-lifecycle-v3":
+        raise ValueError("world snapshot requires exact current schema")
+    if kind not in ("INITIAL", "COMPLETED") or state["kind"] != kind:
+        raise ValueError("world snapshot requires matching explicit kind")
+    if (
+        state["world_roster"] != roster.to_dict()
+        or state["manifest_digest"] != roster.manifest_digest
+        or state["roster_semantic_identity"] != roster.semantic_identity
+        or state["execution_identity"] != semantic_identity
+    ):
+        raise ValueError("world snapshot declaration or semantic identity disagrees")
+    if exact_integer(state["training_seed"], 0, "training seed") != seed:
+        raise ValueError("world snapshot training seed disagrees")
+    next_batch = exact_integer(state["next_batch_episode"], 0, "next batch")
+    membership = set(roster.world_ids)
+
+    def binding(value: Any) -> tuple[str, ...]:
+        if not isinstance(value, Mapping) or set(value) != {"schema", "world_ids", "hash"}:
+            raise ValueError("world binding requires exact fields")
+        ids = exact_world_ids(value["world_ids"])
+        if set(ids) != membership or value != world_binding(ids):
+            raise ValueError("world binding integrity disagrees")
+        return ids
+
+    binding(state["destination_lane_binding"])
+    cursors = state["accepted_episode_seqs"]
+    if not isinstance(cursors, Mapping) or set(cursors) != membership:
+        raise ValueError("accepted cursors must cover declared membership")
+    for sequence in cursors.values():
+        exact_integer(sequence, 0, "accepted sequence")
+    if len(set(cursors.values())) != 1:
+        raise ValueError("current full-roster histories cannot create unequal accepted cursors")
+    history = state["accepted_bindings"]
+    if not isinstance(history, list):
+        raise ValueError("accepted binding history requires a list")
+    if kind == "INITIAL":
+        if (
+            any(cursors.values())
+            or history
+            or state["last_closed_episode"] is not None
+            or state["completed_boundary_key"] is not None
+            or state["saved_lane_binding"] is not None
+        ):
+            raise ValueError("INITIAL cannot contain accepted or completed history")
+        return owned_value(state)
+    batch = exact_integer(state["completed_boundary_key"], 0, "completed boundary")
+    if next_batch != batch + 1 or not all(cursors.values()):
+        raise ValueError("completed next batch or accepted cursors disagree")
+    saved_ids = binding(state["saved_lane_binding"])
+    previous_batch, previous_sequence = None, None
+    for item in history:
+        if not isinstance(item, Mapping) or set(item) != {"batch_episode", "world_ids", "world_episode_seqs"}:
+            raise ValueError("accepted binding requires exact fields")
+        item_batch = exact_integer(item["batch_episode"], 0, "historical batch")
+        ids = exact_world_ids(item["world_ids"])
+        sequences = item["world_episode_seqs"]
+        if set(ids) != membership or not isinstance(sequences, list) or len(sequences) != len(ids):
+            raise ValueError("historical binding membership or sequence shape disagrees")
+        for sequence in sequences:
+            exact_integer(sequence, 1, "historical sequence")
+        if len(set(sequences)) != 1 or item_batch > batch or sequences[0] > item_batch + 1:
+            raise ValueError("unsupported historical cursor provenance")
+        if previous_batch is not None:
+            assert previous_sequence is not None
+            if item_batch <= previous_batch or sequences[0] - previous_sequence != item_batch - previous_batch:
+                raise ValueError("historical accepted sequence progression disagrees")
+        previous_batch, previous_sequence = item_batch, sequences[0]
+    last = state["last_closed_episode"]
+    if not isinstance(last, Mapping) or set(last) != {
+        "batch_episode",
+        "world_ids",
+        "world_episode_seqs",
+        "completion_content",
+        "participated_world_ids",
+    }:
+        raise ValueError("completed snapshot requires exact last closure")
+    if not history or history[-1]["batch_episode"] != batch or last["batch_episode"] != batch:
+        raise ValueError("missing last accepted binding provenance")
+    for name in ("world_ids", "world_episode_seqs"):
+        if last[name] != history[-1][name]:
+            raise ValueError("last closure contradicts accepted provenance")
+    if tuple(last["world_ids"]) != saved_ids or dict(zip(saved_ids, last["world_episode_seqs"], strict=True)) != cursors:
+        raise ValueError("last saved binding contradicts current cursors")
+    if not set(exact_world_ids(last["participated_world_ids"])).issubset(membership):
+        raise ValueError("last closure participants are not declared worlds")
+    return owned_value(state)
diff --git a/src/townlet/environment/vectorized_env.py b/src/townlet/environment/vectorized_env.py
index 4bb8b9d6..1bb6796d 100644
--- a/src/townlet/environment/vectorized_env.py
+++ b/src/townlet/environment/vectorized_env.py
@@ -3,22 +3,40 @@ Vectorized Hamlet environment for GPU-native training.
 
 Batches multiple independent Hamlet environments into a single vectorized
 environment with tensor operations [num_agents, ...].
 """
 
 from __future__ import annotations
 
 import math
+from collections.abc import Mapping
 from numbers import Number, Real
 from pathlib import Path
+from types import MappingProxyType
 from typing import TYPE_CHECKING, Any, cast
+from weakref import WeakValueDictionary
 
 import torch
 
+from townlet.config.world_roster import (
+    WorldAcceptedEpisode,
+    WorldEpisodeReservation,
+    WorldOwnerReceipt,
+    WorldRecord,
+    WorldRosterDeclaration,
+    canonical_hash,
+    exact_integer,
+    exact_world_ids,
+    frozen_value,
+    owned_value,
+    same_value,
+    validate_world_snapshot,
+    world_binding,
+)
 from townlet.environment import env_factory
 from townlet.environment.action_builder import ComposedActionSpace
 from townlet.environment.action_config import ActionConfig
 from townlet.environment.action_executor import ActionExecutor
 from townlet.environment.action_labels import ActionLabels
 from townlet.environment.action_mask_builder import ActionMaskBuilder
 from townlet.environment.affordance_engine import AffordanceEngine
 from townlet.environment.dac_engine import DACEngine
@@ -56,16 +74,145 @@ if TYPE_CHECKING:
     from townlet.universe.compiled import CompiledUniverse
     from townlet.vfs.schema import VariableDef
 
 
 # Import consolidated NullItemManager (ENV-009)
 from townlet.environment.null_managers import NullItemManager
 
 
+class WorldReceiptIssuer:
+    """Cooperative owner custody; copied or duck-typed evidence is never issued."""
+
+    def __init__(self, *, owner: object):
+        self._owner = owner
+        self._issued: WeakValueDictionary[int, WorldOwnerReceipt] = WeakValueDictionary()
+
+    @property
+    def owner(self) -> object:
+        return self._owner
+
+    def issue(self, *, kind: str, payload: Mapping[str, Any]) -> WorldOwnerReceipt:
+        if not isinstance(kind, str) or not kind or not isinstance(payload, Mapping):
+            raise ValueError("owner receipts require a kind and owned field mapping")
+        receipt = WorldOwnerReceipt(kind, self.owner, 0, frozen_value(payload), self)
+        self._issued[id(receipt)] = receipt
+        return receipt
+
+    @staticmethod
+    def validate(receipt: Any, kind: str, owner: object) -> WorldOwnerReceipt:
+        if not isinstance(receipt, WorldOwnerReceipt) or not isinstance(receipt._issuer, WorldReceiptIssuer):
+            raise ValueError("committed evidence requires an issued owner receipt")
+        issuer = receipt._issuer
+        if issuer._issued.get(id(receipt)) is not receipt or receipt.kind != kind or receipt.owner is not owner:
+            raise ValueError("wrong receipt kind, issuer or copied evidence")
+        return receipt
+
+
+class WorldBoundaryAuthority:
+    """T26's bound release capability; saving is never a release side effect."""
+
+    def __init__(self, env: VectorizedHamletEnv, owner: object):
+        self._env, self._owner = env, owner
+
+    def _bound_env(self) -> VectorizedHamletEnv:
+        if self._env._world_authority is not self:
+            raise ValueError("boundary capability was not bound by this ENV")
+        return self._env
+
+    def bootstrap(self, *, first_batch_episode: int) -> WorldRecord:
+        env = self._bound_env()
+        exact_integer(first_batch_episode, 0, "first batch")
+        env._require_phase("fresh-bound", "bootstrap-ready")
+        if env._world_bootstrap is not None:
+            if env._world_bootstrap.next_batch_episode != first_batch_episode:
+                raise ValueError("bootstrap batch cannot change")
+            return env._world_bootstrap
+        env._world_bootstrap = env._record("release", {"release_kind": "bootstrap", "next_batch_episode": first_batch_episode})
+        return env._world_bootstrap
+
+    def completed(self, *, closure: WorldRecord, effects: WorldOwnerReceipt) -> WorldRecord:
+        env = self._bound_env()
+        env._require_phase("closed-awaiting-release", "released-completed")
+        env._valid_record(closure, "closure")
+        if closure is not env._world_closure:
+            raise ValueError("release must name the current closure")
+        proof = WorldReceiptIssuer.validate(effects, "boundary_effects", self._owner)
+        fields = proof.payload
+        required = {
+            "batch_episode",
+            "accepted_identity",
+            "completion_content",
+            "retirement_receipt",
+            "curriculum_receipt",
+            "exploration_receipt",
+            "population_commit_receipt",
+            "epsilon_install_receipt",
+            "selection_sync_receipt",
+        }
+        if set(fields) != required or fields["accepted_identity"] is not env._world_accepted:
+            raise ValueError("effects require the exact accepted boundary")
+        exact_integer(fields["batch_episode"], 0, "effects batch")
+        if fields["batch_episode"] != closure.boundary_key or not same_value(fields["completion_content"], closure.completion_content):
+            raise ValueError("effects disagree with closure content")
+        if fields["retirement_receipt"] is not closure.dispositions:
+            raise ValueError("retirement evidence disagrees")
+        for name in required - {"batch_episode", "accepted_identity", "completion_content", "retirement_receipt"}:
+            child = fields[name]
+            WorldReceiptIssuer.validate(child, name, child.owner if isinstance(child, WorldOwnerReceipt) else None)
+            exact_integer(child.boundary_key, 0, "effect boundary")
+            if child.accepted is not env._world_accepted or child.boundary_key != closure.boundary_key:
+                raise ValueError("effect receipt belongs to another boundary")
+        return env._equal_record(
+            "completed_release",
+            "release",
+            {
+                "release_kind": "completed",
+                "next_batch_episode": closure.boundary_key + 1,
+                "closure": closure,
+                "effects": effects,
+            },
+        )
+
+    def prepare_initial_snapshot(self, *, release: WorldRecord, owners: WorldOwnerReceipt) -> WorldRecord:
+        env = self._bound_env()
+        env._require_phase("bootstrap-ready")
+        env._require_release(release)
+        proof = WorldReceiptIssuer.validate(owners, "initial_owners", self._owner)
+        fields = proof.payload
+        names = {"population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection"}
+        if set(fields) != names | {"semantic_execution_identity", "bootstrap_first_batch", "world_binding"}:
+            raise ValueError("initial preparation requires every current owner")
+        if (
+            proof.semantic_execution_identity != env.semantic_execution_identity
+            or proof.bootstrap_first_batch != release.next_batch_episode
+            or tuple(proof.world_binding) != env.world_ids
+        ):
+            raise ValueError("initial owner identity disagrees")
+        for name in names:
+            child = fields[name]
+            WorldReceiptIssuer.validate(child, "initial_owner", child.owner if isinstance(child, WorldOwnerReceipt) else None)
+            if set(child.payload) != {"state"}:
+                raise ValueError("initial owner must provide its prepared current state")
+        return env._record("initial_snapshot", {"release": release, "owners": owners})
+
+    def restored(self, *, restore: WorldRecord, boundary: WorldOwnerReceipt) -> WorldRecord:
+        env = self._bound_env()
+        env._require_phase("fresh-bound")
+        env._valid_record(restore, "prepared_restore")
+        proof = WorldReceiptIssuer.validate(boundary, "restored_boundary", self._owner)
+        if set(proof.payload) != {"kind", "state", "prepared"} or proof.prepared is not restore:
+            raise ValueError("restore requires matching joint prepared evidence")
+        if proof.payload["kind"] != restore.state["kind"] or not same_value(proof.state, restore.state):
+            raise ValueError("joint restore evidence disagrees")
+        return env._record(
+            "release", {"release_kind": "restored", "next_batch_episode": restore.state["next_batch_episode"], "restore": restore}
+        )
+
+
 class VectorizedHamletEnv:
     """
     GPU-native vectorized Hamlet environment.
 
     Batches multiple independent environments for parallel execution.
     All state is stored as PyTorch tensors on specified device.
     """
 
@@ -75,31 +222,35 @@ class VectorizedHamletEnv:
 
     def __init__(
         self,
         *,
         universe: CompiledUniverse,
         level_name: str,
         num_agents: int,
         device: torch.device | str,
+        world_roster: WorldRosterDeclaration,
+        training_seed: int,
+        lane_world_ids: tuple[str, ...],
     ):
         """
         Initialize vectorized environment.
 
         Args:
             universe: CompiledUniverse artifact produced by UniverseCompiler (v2.1 hierarchical configs)
             level_name: Which curriculum level to instantiate (e.g., "L0_0_minimal")
             num_agents: Number of parallel agents to simulate
             device: PyTorch device or device string (must be provided explicitly)
 
         Note (PDR-002 Compliance):
             - device retains an infrastructure default (exempted from no-defaults principle)
             - Behavioral parameters (grid size, observability, energy costs, affordance selection)
               now flow exclusively from the compiled universe
         """
+        self._initialize_world_identity(world_roster, training_seed, lane_world_ids, num_agents, universe.execution_hash)
         if device is None:
             raise ValueError("VectorizedHamletEnv requires an explicit device; cannot default to CPU/GPU.")
         torch_device = torch.device(device) if isinstance(device, str) else device
 
         level = universe.get_level(level_name)
         self.level_name = level_name
         self.level = level
         self.universe = universe
@@ -580,17 +731,17 @@ class VectorizedHamletEnv:
             items_per_world=self.items_per_world,
             num_affordances=self.metadata.affordance_count,
             item_profiles=item_profiles,
         )
 
         # Counter-based VFS draws (expressions, action writes, transition rules), separate
         # from the effects engine's streams (S1). The run seed is captured here, once: a
         # later seed_all elsewhere in the process never shifts this environment's draws.
-        self.vfs_randomness = VFSRandomness(torch.initial_seed())
+        self.vfs_randomness = VFSRandomness(self._world_seed)
         self.vfs_evaluator: VFSEvaluator | None = None
         if universe.compiled_vfs_profiles is not None:
             self.vfs_evaluator = VFSEvaluator(history_spec=universe.vfs_history_spec)
             self.vfs_evaluation_marks = universe.vfs_evaluation_marks
         else:
             self.vfs_evaluation_marks = None
 
         meter_name_to_index = dict(self.metadata.meter_name_to_index)
@@ -748,17 +899,17 @@ class VectorizedHamletEnv:
         Returns:
             Dictionary mapping bar names to meter tensors [num_agents]
         """
         bars_dict = {}
         for bar_name, idx in self.meter_name_to_index.items():
             bars_dict[bar_name] = self.meters[:, idx]
         return bars_dict
 
-    def reset(self) -> torch.Tensor:
+    def _reset_world_state(self) -> torch.Tensor:
         """Reset all environments and return the first observation of the episode.
 
         The observation describes the state the first action is taken in, exactly as
         `step()`'s observation describes the state the next action is taken in. Reset runs
         the tail of `step()`'s phase order from an empty world, at instant 0:
 
         1. world state: affordance layout, positions, velocity, meters, dones, step counts;
         2. clock: `global_tick = 0`, registry `tick` written after `reset_episode_scoped`
@@ -847,35 +998,42 @@ class VectorizedHamletEnv:
     @classmethod
     def from_universe(
         cls,
         universe: CompiledUniverse,
         *,
         level_name: str,
         num_agents: int,
         device: torch.device | str,
+        world_roster: WorldRosterDeclaration,
+        training_seed: int,
+        lane_world_ids: tuple[str, ...],
     ) -> VectorizedHamletEnv:
         """Instantiate environment using metadata from a compiled universe.
 
         Args:
             universe: CompiledUniverse with hierarchical configs
             level_name: Curriculum level to instantiate (e.g., \"L0_0_minimal\").
                 Must be provided explicitly; no default level selection is performed.
             num_agents: Number of parallel agents
             device: PyTorch device (explicit)
 
         Returns:
             VectorizedHamletEnv instance
         """
-        return env_factory.from_universe(
-            cls,
+        if level_name is None:
+            raise ValueError("level_name must be explicit")
+        return cls(
             universe=universe,
             level_name=level_name,
             num_agents=num_agents,
             device=device,
+            world_roster=world_roster,
+            training_seed=training_seed,
+            lane_world_ids=lane_world_ids,
         )
 
     def _get_observations(self) -> torch.Tensor:
         """Serialize this tick's compiled token observation, `[num_agents, total_dims]`."""
         return self._observation_encoder.encode(self.num_agents, self._build_token_publish_context())
 
     def _item_slot_batch(self) -> ItemSlotBatch | None:
         """Every world's live items keyed by compiled `item` token slot.
@@ -1081,16 +1239,18 @@ class VectorizedHamletEnv:
 
         Returns:
             observations: [num_agents, observation_dim]
             rewards: [num_agents]
             dones: [num_agents] bool
             info: dict with metadata and owned bool [num_agents, action_dim]
                 successor_action_masks for this same committed observation/status
         """
+        if self._world_phase != "active":
+            raise ValueError("world episode must be accepted and activated before stepping")
         prev_dones = self.dones.clone()
         active_on_entry = ~prev_dones
         self.vfs_registry.reset_tick_scoped()
         refusals_before = 0
         if self.effect_manager is not None:
             refusals_before = len(self.effect_manager.spawn_refusals)
         # 1. Execute actions and track successful interactions
         successful_interactions = self._action_executor._execute_actions(actions)
@@ -1707,8 +1867,412 @@ class VectorizedHamletEnv:
                 return sampled
             sampled[clashes] = self.substrate.initialize_positions(len(clashes), self.device, generator=None)
         clashes = [index for index, row in enumerate(sampled.tolist()) if tuple(row) in taken]
         if clashes:
             free = [position for position in self.substrate.get_all_positions() if tuple(position) not in taken]
             picks = torch.randint(0, len(free), (len(clashes),))
             sampled[clashes] = torch.tensor([free[int(pick)] for pick in picks], dtype=self.substrate.position_dtype, device=self.device)
         return sampled
+
+    def _initialize_world_identity(
+        self, roster: WorldRosterDeclaration, seed: int, lane_ids: tuple[str, ...], count: int, execution_identity: str
+    ) -> None:
+        if not isinstance(roster, WorldRosterDeclaration):
+            raise ValueError("ENV requires an authored WorldRosterDeclaration")
+        ids = exact_world_ids(lane_ids)
+        exact_integer(count, 1, "world count")
+        exact_integer(seed, 0, "training seed")
+        if len(ids) != count or set(ids) != set(roster.world_ids):
+            raise ValueError("lane binding must contain the exact declared roster")
+        self._world_roster, self._world_seed, self._world_ids = roster, seed, ids
+        self._world_identity = canonical_hash({"execution": execution_identity, "membership": roster.semantic_identity, "seed": seed})
+        self._world_phase, self._world_generation = "fresh-unbound", 0
+        self._world_cursors = dict.fromkeys(ids, 0)
+        self._world_records: WeakValueDictionary[int, WorldRecord] = WeakValueDictionary()
+        self._world_equal: dict[str, WorldRecord] = {}
+        self._world_bindings: dict[int, dict[str, Any]] = {}
+        self._world_authority: WorldBoundaryAuthority | None = None
+        self._world_bootstrap: WorldRecord | None = None
+        self._world_release: WorldRecord | None = None
+        self._world_accepted: WorldAcceptedEpisode | None = None
+        self._world_reset: WorldRecord | None = None
+        self._world_reservation: WorldEpisodeReservation | None = None
+        self._world_closure: WorldRecord | None = None
+        self._world_last_closed: dict[str, Any] | None = None
+        self._world_consumers: tuple[object, object] | None = None
+        self._world_saved_binding: dict[str, Any] | None = None
+        self._world_restored: tuple[WorldRecord, WorldRecord] | None = None
+
+    @property
+    def world_ids(self) -> tuple[str, ...]:
+        return self._world_ids
+
+    @property
+    def accepted_episode_seqs(self) -> Mapping[str, int]:
+        return MappingProxyType(dict(self._world_cursors))
+
+    @property
+    def world_phase(self) -> str:
+        return self._world_phase
+
+    @property
+    def semantic_execution_identity(self) -> str:
+        return self._world_identity
+
+    def _require_phase(self, *phases: str) -> None:
+        if self._world_phase not in phases:
+            raise ValueError(f"operation is unavailable in world phase {self._world_phase}")
+
+    def _record(self, kind: str, payload: Mapping[str, Any]) -> WorldRecord:
+        result = WorldRecord(kind, self, self._world_generation, frozen_value(payload))
+        self._world_records[id(result)] = result
+        return result
+
+    def _valid_record(self, record: Any, kind: str) -> None:
+        if (
+            not isinstance(record, WorldRecord)
+            or record.kind != kind
+            or record._owner is not self
+            or record._generation != self._world_generation
+            or self._world_records.get(id(record)) is not record
+        ):
+            raise ValueError("foreign, stale, changed or unissued world capability")
+
+    def _equal_record(self, key: str, kind: str, payload: Mapping[str, Any]) -> WorldRecord:
+        previous = self._world_equal.get(key)
+        if previous is not None:
+            if not same_value(previous.payload, payload):
+                raise ValueError("changed content on a world operation retry")
+            return previous
+        result = self._record(kind, payload)
+        self._world_equal[key] = result
+        return result
+
+    def _require_release(self, release: WorldRecord) -> None:
+        self._valid_record(release, "release")
+        if release is not self._world_release:
+            raise ValueError("world operation requires the installed release")
+
+    def bind_boundary_authority(self, *, owner: object) -> WorldBoundaryAuthority:
+        if self._world_authority is not None:
+            if self._world_authority._owner is not owner:
+                raise ValueError("world boundary authority is already bound")
+            return self._world_authority
+        self._require_phase("fresh-unbound")
+        self._world_authority = WorldBoundaryAuthority(self, owner)
+        self._world_phase = "fresh-bound"
+        return self._world_authority
+
+    def install_boundary_release(self, release: WorldRecord) -> WorldRecord:
+        self._valid_record(release, "release")
+        if release is self._world_release:
+            self._require_phase("bootstrap-ready", "released-completed")
+            return release
+        if release.release_kind == "bootstrap":
+            self._require_phase("fresh-bound")
+            if release is not self._world_bootstrap:
+                raise ValueError("unissued bootstrap")
+            phase = "bootstrap-ready"
+        elif release.release_kind == "completed":
+            self._require_phase("closed-awaiting-release")
+            if release.closure is not self._world_closure:
+                raise ValueError("release does not match current closure")
+            phase = "released-completed"
+        else:
+            raise ValueError("restored releases install only with their prepared restore")
+        self._world_release, self._world_phase = release, phase
+        return release
+
+    def prepare_episode(self, *, batch_episode: int, release: WorldRecord) -> WorldEpisodeReservation:
+        self._require_phase("bootstrap-ready", "released-completed")
+        self._require_release(release)
+        exact_integer(batch_episode, 0, "batch episode")
+        if batch_episode != release.next_batch_episode:
+            raise ValueError("batch identity must be the released next batch")
+        return WorldEpisodeReservation(
+            self.world_ids,
+            tuple(self._world_cursors[key] + 1 for key in self.world_ids),
+            batch_episode,
+            self,
+            self._world_generation,
+            release,
+        )
+
+    def validate_episode_reservation(self, reservation: WorldEpisodeReservation) -> None:
+        self._require_phase("bootstrap-ready", "released-completed")
+        if not isinstance(reservation, WorldEpisodeReservation) or reservation._owner is not self:
+            raise ValueError("reservation belongs to another world authority")
+        if not isinstance(reservation.world_episode_seqs, tuple):
+            raise ValueError("reservation sequences must be immutable")
+        for sequence in reservation.world_episode_seqs:
+            exact_integer(sequence, 1, "reserved sequence")
+        self._require_release(reservation._release)
+        expected = self.prepare_episode(batch_episode=reservation.batch_episode, release=reservation._release)
+        if (
+            reservation._generation != expected._generation
+            or reservation.world_ids != expected.world_ids
+            or reservation.world_episode_seqs != expected.world_episode_seqs
+        ):
+            raise ValueError("reservation identity or cursor disagrees")
+
+    def reset(self, *, reservation: WorldEpisodeReservation) -> WorldRecord:
+        previous = self._world_reservation
+        duplicate = (
+            isinstance(reservation, WorldEpisodeReservation)
+            and previous is not None
+            and type(reservation.batch_episode) is int
+            and isinstance(reservation.world_episode_seqs, tuple)
+            and all(type(sequence) is int for sequence in reservation.world_episode_seqs)
+            and reservation._owner is previous._owner
+            and reservation._generation == previous._generation
+            and reservation._release is previous._release
+            and reservation.batch_episode == previous.batch_episode
+            and reservation.world_ids == previous.world_ids
+            and reservation.world_episode_seqs == previous.world_episode_seqs
+        )
+        if self._world_reset is not None and duplicate:
+            self._require_phase("active-awaiting-activation", "active", "closed-awaiting-release", "released-completed")
+            return self._world_reset
+        self.validate_episode_reservation(reservation)
+        self._world_phase = "resetting"
+        try:
+            observation = self._reset_world_state()
+            generation = self._world_generation + 1
+            accepted = WorldAcceptedEpisode(
+                reservation.world_ids, reservation.world_episode_seqs, reservation.batch_episode, self, generation
+            )
+            binding = {
+                "batch_episode": accepted.batch_episode,
+                "world_ids": list(accepted.world_ids),
+                "world_episode_seqs": list(accepted.world_episode_seqs),
+            }
+            self._world_generation = generation
+            receipt = self._record("reset", {"accepted": accepted, "observation": observation})
+            self._world_cursors = dict(zip(accepted.world_ids, accepted.world_episode_seqs, strict=True))
+            self._world_bindings[accepted.batch_episode] = binding
+            self._world_accepted, self._world_reset, self._world_reservation = accepted, receipt, reservation
+            self._world_restored = None
+            self._world_equal = {}
+            self._world_closure, self._world_release = None, None
+            self._world_phase = "active-awaiting-activation"
+            return receipt
+        except BaseException:
+            self._world_phase = "quarantined"
+            raise
+
+    def _accepted(self, accepted: WorldAcceptedEpisode) -> None:
+        if accepted is not self._world_accepted or accepted is None:
+            raise ValueError("accepted episode must be this ENV's current token")
+
+    def activate_episode(
+        self, *, accepted: WorldAcceptedEpisode, population_receipt: WorldOwnerReceipt, curiosity_receipt: WorldOwnerReceipt
+    ) -> WorldRecord:
+        self._require_phase("active-awaiting-activation", "active")
+        self._accepted(accepted)
+        receipts = (population_receipt, curiosity_receipt)
+        for receipt in receipts:
+            WorldReceiptIssuer.validate(receipt, "activation", receipt.owner if isinstance(receipt, WorldOwnerReceipt) else None)
+            if set(receipt.payload) != {"accepted"} or receipt.accepted is not accepted:
+                raise ValueError("activation receipt identity disagrees")
+        owners = (population_receipt.owner, curiosity_receipt.owner)
+        if self._world_consumers is not None and any(a is not b for a, b in zip(owners, self._world_consumers, strict=True)):
+            raise ValueError("episode consumers cannot change inside an ENV")
+        result = self._equal_record(
+            "activation", "activation", {"accepted": accepted, "population": population_receipt, "curiosity": curiosity_receipt}
+        )
+        self._world_consumers, self._world_phase = owners, "active"
+        return result
+
+    def prepare_episode_close(
+        self,
+        *,
+        accepted: WorldAcceptedEpisode,
+        boundary_key: int,
+        completion_content: Any,
+        participated_world_ids: tuple[str, ...],
+        dispositions: WorldOwnerReceipt,
+    ) -> WorldRecord:
+        self._require_phase("active", "closed-awaiting-release", "released-completed")
+        self._accepted(accepted)
+        exact_integer(boundary_key, 0, "boundary key")
+        participants = exact_world_ids(participated_world_ids)
+        actual = {key for index, key in enumerate(self.world_ids) if int(self.step_counts[index]) > 0}
+        if boundary_key != accepted.batch_episode or set(participants) != actual:
+            raise ValueError("closure requires exactly the genuinely participated worlds")
+        if self._world_consumers is None:
+            raise ValueError("closure requires activated consumers")
+        proof = WorldReceiptIssuer.validate(dispositions, "dispositions", self._world_consumers[1])
+        if set(proof.payload) != {"accepted", "boundary_key", "completion_content", "participated_world_ids", "dispositions"}:
+            raise ValueError("disposition receipt requires complete fields")
+        exact_integer(proof.boundary_key, 0, "disposition boundary")
+        expected = tuple((key, "completed" if key in actual else "retired_nonparticipating") for key in self.world_ids)
+        if (
+            proof.accepted is not accepted
+            or proof.boundary_key != boundary_key
+            or tuple(proof.participated_world_ids) != participants
+            or not same_value(proof.completion_content, completion_content)
+            or proof.dispositions != expected
+        ):
+            raise ValueError("committed dispositions disagree with the accepted episode")
+        payload = {
+            "accepted": accepted,
+            "boundary_key": boundary_key,
+            "completion_content": completion_content,
+            "participated_world_ids": participants,
+            "dispositions": dispositions,
+        }
+        if self._world_closure is not None and not same_value(self._world_closure.payload, payload):
+            raise ValueError("changed duplicate closure")
+        return self._record("prepared_close", payload)
+
+    def close_episode(self, prepared: WorldRecord) -> WorldRecord:
+        self._require_phase("active", "closed-awaiting-release", "released-completed")
+        self._valid_record(prepared, "prepared_close")
+        self._accepted(prepared.accepted)
+        closure = self._equal_record("closure", "closure", prepared.payload)
+        if self._world_closure is not None:
+            return closure
+        accepted = prepared.accepted
+        last = {
+            "batch_episode": accepted.batch_episode,
+            "world_ids": list(accepted.world_ids),
+            "world_episode_seqs": list(accepted.world_episode_seqs),
+            "completion_content": owned_value(prepared.completion_content),
+            "participated_world_ids": list(prepared.participated_world_ids),
+        }
+        self._world_last_closed, self._world_saved_binding = last, world_binding(accepted.world_ids)
+        self._world_closure, self._world_phase = closure, "closed-awaiting-release"
+        return closure
+
+    def abandon_episode(self, *, accepted: WorldAcceptedEpisode, reason: str) -> WorldRecord:
+        self._accepted(accepted)
+        if reason not in ("empty_participation", "runtime_failure"):
+            raise ValueError("unknown episode abandonment reason")
+        if self._world_phase == "quarantined":
+            previous = self._world_equal.get("abandonment")
+            if previous is None or previous.reason != reason:
+                raise ValueError("different failed attempt cannot be retried")
+            return previous
+        self._require_phase("active", "active-awaiting-activation")
+        if reason == "empty_participation":
+            if bool((self.step_counts > 0).any()) or self._world_consumers is None:
+                raise ValueError("empty abandonment requires activated empty owners")
+            for owner in self._world_consumers:
+                method = getattr(owner, "prepare_empty_episode_evidence", None)
+                if not callable(method):
+                    raise ValueError("owner lacks the required empty-episode proof")
+                evidence = WorldReceiptIssuer.validate(method(accepted=accepted), "empty_episode", owner)
+                if set(evidence.payload) != {"accepted", "participated_world_ids", "events"} or evidence.accepted is not accepted:
+                    raise ValueError("empty-episode proof identity disagrees")
+                if evidence.participated_world_ids or evidence.events:
+                    raise ValueError("episode has participating owner state")
+        result = self._equal_record("abandonment", "abandonment", {"accepted": accepted, "reason": reason})
+        self._world_phase = "quarantined"
+        return result
+
+    def checkpoint_world_state(
+        self, *, kind: str, release: WorldRecord, retained_binding_batches: tuple[int, ...], initial: WorldRecord | None
+    ) -> dict[str, Any]:
+        self._require_release(release)
+        if not isinstance(retained_binding_batches, tuple):
+            raise ValueError("retained history references require a tuple")
+        for batch in retained_binding_batches:
+            exact_integer(batch, 0, "retained batch")
+        if tuple(sorted(set(retained_binding_batches))) != retained_binding_batches:
+            raise ValueError("retained batch references must be sorted and unique")
+        if kind == "INITIAL":
+            self._require_phase("bootstrap-ready")
+            self._valid_record(initial, "initial_snapshot")
+            assert isinstance(initial, WorldRecord)
+            if initial.release is not release or retained_binding_batches or any(self._world_cursors.values()) or self._world_bindings:
+                raise ValueError("INITIAL requires pristine bootstrap and no accepted history")
+        elif kind == "COMPLETED":
+            self._require_phase("released-completed")
+            if (
+                initial is not None
+                or self._world_last_closed is None
+                or self._world_last_closed["batch_episode"] not in retained_binding_batches
+            ):
+                raise ValueError("completed snapshots require current closure provenance")
+        else:
+            raise ValueError("snapshot kind must be explicit INITIAL or COMPLETED")
+        if any(batch not in self._world_bindings for batch in retained_binding_batches):
+            raise ValueError("missing retained accepted-binding provenance")
+        return {
+            "schema": "world-lifecycle-v3",
+            "kind": kind,
+            "next_batch_episode": release.next_batch_episode,
+            "world_roster": self._world_roster.to_dict(),
+            "manifest_digest": self._world_roster.manifest_digest,
+            "roster_semantic_identity": self._world_roster.semantic_identity,
+            "training_seed": self._world_seed,
+            "execution_identity": self.semantic_execution_identity,
+            "saved_lane_binding": owned_value(self._world_saved_binding),
+            "destination_lane_binding": world_binding(self.world_ids),
+            "accepted_episode_seqs": dict(self._world_cursors),
+            "last_closed_episode": owned_value(self._world_last_closed),
+            "completed_boundary_key": None if self._world_last_closed is None else self._world_last_closed["batch_episode"],
+            "accepted_bindings": [owned_value(self._world_bindings[batch]) for batch in retained_binding_batches],
+        }
+
+    def prepare_world_restore(
+        self,
+        *,
+        kind: str,
+        state: Mapping[str, Any],
+        world_roster: WorldRosterDeclaration,
+        destination_world_ids: tuple[str, ...],
+        semantic_execution_identity: str,
+    ) -> WorldRecord:
+        self._require_phase("fresh-bound")
+        if not isinstance(world_roster, WorldRosterDeclaration) or world_roster.to_dict() != self._world_roster.to_dict():
+            raise ValueError("restore must preserve the original authored roster manifest")
+        destination = exact_world_ids(destination_world_ids)
+        if set(destination) != set(self.world_ids) or destination != self.world_ids:
+            raise ValueError("restore destination must be the fresh ENV's actual binding")
+        if semantic_execution_identity != self.semantic_execution_identity:
+            raise ValueError("restore destination semantic identity disagrees")
+        prepared = validate_world_snapshot(state, kind, world_roster, self._world_seed, semantic_execution_identity)
+        return self._record("prepared_restore", {"state": prepared, "destination_world_ids": destination})
+
+    def install_world_restore(self, *, prepared: WorldRecord, release: WorldRecord) -> WorldRecord:
+        if self._world_restored is not None and self._world_restored == (prepared, release):
+            self._require_phase("bootstrap-ready", "released-completed")
+            assert self._world_release is not None
+            return self._world_release
+        self._require_phase("fresh-bound")
+        self._valid_record(prepared, "prepared_restore")
+        self._valid_record(release, "release")
+        if release.release_kind != "restored" or release.restore is not prepared:
+            raise ValueError("restore release does not name this preparation")
+        state = prepared.state
+        self._world_phase = "restoring"
+        try:
+            self._world_generation += 1
+            self._world_cursors = dict(state["accepted_episode_seqs"])
+            self._world_bindings = {item["batch_episode"]: owned_value(item) for item in state["accepted_bindings"]}
+            self._world_last_closed = owned_value(state["last_closed_episode"])
+            self._world_saved_binding = owned_value(state["saved_lane_binding"])
+            if state["kind"] == "INITIAL":
+                installed = self._record("release", {"release_kind": "bootstrap", "next_batch_episode": state["next_batch_episode"]})
+                self._world_bootstrap = installed
+                phase = "bootstrap-ready"
+            else:
+                last = self._world_last_closed
+                assert last is not None
+                self._world_accepted = WorldAcceptedEpisode(
+                    tuple(last["world_ids"]),
+                    tuple(last["world_episode_seqs"]),
+                    last["batch_episode"],
+                    self,
+                    self._world_generation,
+                )
+                self._world_closure = self._record("restored_closure", {"semantic_state": last})
+                installed = self._record("release", {"release_kind": "completed", "next_batch_episode": state["next_batch_episode"]})
+                phase = "released-completed"
+            self._world_release = installed
+            self._world_restored = (prepared, release)
+            self._world_phase = phase
+            return installed
+        except BaseException:
+            self._world_phase = "quarantined"
+            raise
diff --git a/tests/test_townlet/regressions/bac/test_world_episode_identity.py b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
new file mode 100644
index 00000000..ac69b687
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_world_episode_identity.py
@@ -0,0 +1,701 @@
+"""Real ENV producer tests; sealed local sink receipts are interface evidence only.
+
+Compilation uses the accepted current1.42 public receipt. The sinks below do not
+qualify real POP/PW05/T25/T26, provider learning, VFS or simulator independence.
+New production imports stay inside helpers so the preimplementation RED collects.
+"""
+
+from __future__ import annotations
+
+from copy import deepcopy
+from dataclasses import replace
+from pathlib import Path
+from types import SimpleNamespace
+
+import pytest
+import torch
+
+IDS = ("orchard-west", "river-house")
+SEED = 479
+
+
+@pytest.fixture(scope="module")
+def compiled():
+    from townlet.universe.compiler import UniverseCompiler
+
+    result = UniverseCompiler().compile(
+        Path(__file__).resolve().parents[4] / "configs/test/token_set_smoke",
+        primary_level="L0_test",
+        use_cache=False,
+    )
+    assert result.to_dict()["compiled_schema_version"] == "1.42"
+    return result
+
+
+def _roster(ids=IDS):
+    from townlet.config.world_roster import WorldRosterDeclaration
+
+    return WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)})
+
+
+def _env(compiled, order=IDS):
+    from townlet.environment.vectorized_env import VectorizedHamletEnv
+
+    return VectorizedHamletEnv(
+        universe=compiled,
+        level_name="L0_test",
+        num_agents=2,
+        device="cpu",
+        world_roster=_roster(),
+        training_seed=SEED,
+        lane_world_ids=order,
+    )
+
+
+def _same(left, right):
+    if isinstance(left, torch.Tensor):
+        assert isinstance(right, torch.Tensor)
+        assert left.dtype == right.dtype and left.device == right.device
+        assert left.shape == right.shape and torch.equal(left, right)
+    elif isinstance(left, dict):
+        assert left.keys() == right.keys()
+        for key in left:
+            _same(left[key], right[key])
+    elif isinstance(left, (tuple, list)):
+        assert type(left) is type(right) and len(left) == len(right)
+        for first, second in zip(left, right, strict=True):
+            _same(first, second)
+    else:
+        assert type(left) is type(right) and left == right
+
+
+def _state(env):
+    """Observable identity plus real mutable simulator/RNG witnesses."""
+    return {
+        "phase": env.world_phase,
+        "ids": env.world_ids,
+        "cursors": dict(env.accepted_episode_seqs),
+        "positions": env.positions.clone(),
+        "meters": env.meters.clone(),
+        "dones": env.dones.clone(),
+        "steps": env.step_counts.clone(),
+        "tick": env.global_tick,
+        "vfs": deepcopy(env.vfs_random_state()),
+        "rng": torch.get_rng_state().clone(),
+    }
+
+
+class _Sink:
+    """Cooperative local owner; only issuer-sealed evidence is accepted by ENV.
+
+    This is not a fake implementation of POP canonical outcome validation.
+    Its event content is deliberately an opaque interface fixture.
+    """
+
+    def __init__(self):
+        from townlet.environment.vectorized_env import WorldReceiptIssuer
+
+        self.issuer = WorldReceiptIssuer(owner=self)
+        self.accepted = None
+        self.participants = ()
+        self.records = {}
+        self.initial_weight = torch.tensor([0.25, -0.75])
+
+    def receipt(self, receipt_kind, **payload):
+        return self.issuer.issue(kind=receipt_kind, payload=payload)
+
+    def prepare_empty_episode_evidence(self, *, accepted):
+        if accepted is not self.accepted or self.participants:
+            raise ValueError("not an empty accepted episode")
+        return self.receipt("empty_episode", accepted=accepted, participated_world_ids=(), events=())
+
+    def activation(self, accepted):
+        self.accepted = accepted
+        return self.receipt("activation", accepted=accepted)
+
+
+class _Run:
+    def __init__(self, env, bootstrap=True):
+        self.env = env
+        self.boundary = _Sink()
+        self.population = _Sink()
+        self.bank = _Sink()
+        self.authority = env.bind_boundary_authority(owner=self.boundary)
+        self.release = None
+        self.accepted = None
+        self.events = {}
+        if bootstrap:
+            self.release = env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))
+
+    def reset(self, batch):
+        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
+        self.env.validate_episode_reservation(reservation)
+        reset = self.env.reset(reservation=reservation)
+        self.accepted = reset.accepted
+        self.env.activate_episode(
+            accepted=reset.accepted,
+            population_receipt=self.population.activation(reset.accepted),
+            curiosity_receipt=self.bank.activation(reset.accepted),
+        )
+        return reservation, reset
+
+    def step(self, participants=IDS):
+        # Control actual active-on-entry lanes; no fabricated simulator steps.
+        for index, world_id in enumerate(self.env.world_ids):
+            self.env.dones[index] = world_id not in participants
+        masks = self.env.get_action_masks()
+        actions = masks.to(torch.int64).argmax(dim=1)
+        self.env.step(actions, depletion_multiplier=1.0)
+        self.population.participants = tuple(participants)
+        self.bank.participants = tuple(participants)
+
+    def close(self, batch, participants=IDS):
+        # Actual ENV participation; opaque fixture content is not an EP envelope.
+        content = tuple(
+            (batch, index, world_id, self.accepted.world_episode_seqs[index], "interface-outcome")
+            for index, world_id in enumerate(self.accepted.world_ids)
+            if world_id in participants
+        )
+        self.events[batch] = content
+        dispositions = tuple(
+            (world_id, "completed" if world_id in participants else "retired_nonparticipating") for world_id in self.accepted.world_ids
+        )
+        receipt = self.bank.receipt(
+            "dispositions",
+            accepted=self.accepted,
+            boundary_key=batch,
+            completion_content=content,
+            participated_world_ids=tuple(participants),
+            dispositions=dispositions,
+        )
+        prepared = self.env.prepare_episode_close(
+            accepted=self.accepted,
+            boundary_key=batch,
+            completion_content=content,
+            participated_world_ids=tuple(participants),
+            dispositions=receipt,
+        )
+        closure = self.env.close_episode(prepared)
+        self.bank.records[batch] = dispositions
+        return prepared, closure, receipt
+
+    def release_closed(self, batch, closure, dispositions):
+        fields = {
+            name: self.boundary.receipt(name, accepted=self.accepted, boundary_key=batch)
+            for name in (
+                "curriculum_receipt",
+                "exploration_receipt",
+                "population_commit_receipt",
+                "epsilon_install_receipt",
+                "selection_sync_receipt",
+            )
+        }
+        effects = self.boundary.receipt(
+            "boundary_effects",
+            batch_episode=batch,
+            accepted_identity=self.accepted,
+            completion_content=self.events[batch],
+            retirement_receipt=dispositions,
+            **fields,
+        )
+        release = self.authority.completed(closure=closure, effects=effects)
+        self.release = self.env.install_boundary_release(release)
+        return effects
+
+    def initial(self):
+        owner_fields = {
+            name: self.boundary.receipt("initial_owner", state={"weights": self.boundary.initial_weight.clone()})
+            for name in ("population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
+        }
+        owners = self.boundary.receipt(
+            "initial_owners",
+            semantic_execution_identity=self.env.semantic_execution_identity,
+            bootstrap_first_batch=1,
+            world_binding=self.env.world_ids,
+            **owner_fields,
+        )
+        proof = self.authority.prepare_initial_snapshot(release=self.release, owners=owners)
+        return self.env.checkpoint_world_state(
+            kind="INITIAL",
+            release=self.release,
+            retained_binding_batches=(),
+            initial=proof,
+        )
+
+    def completed(self, references):
+        return self.env.checkpoint_world_state(
+            kind="COMPLETED",
+            release=self.release,
+            retained_binding_batches=references,
+            initial=None,
+        )
+
+
+def _restore(compiled, state, order):
+    run = _Run(_env(compiled, order), bootstrap=False)
+    prepared = run.env.prepare_world_restore(
+        kind=state["kind"],
+        state=state,
+        world_roster=_roster(),
+        destination_world_ids=order,
+        semantic_execution_identity=run.env.semantic_execution_identity,
+    )
+    # T25/T26 joint validation is a labeled sealed interface attestation here.
+    boundary = run.boundary.receipt("restored_boundary", kind=state["kind"], state=deepcopy(state), prepared=prepared)
+    release = run.authority.restored(restore=prepared, boundary=boundary)
+    run.release = run.env.install_world_restore(prepared=prepared, release=release)
+    assert run.env.install_world_restore(prepared=prepared, release=release) is run.release
+    return run
+
+
+def test_declared_roster_owned_exact_serialization():
+    from townlet.config.world_roster import WorldRosterDeclaration
+
+    payload = {"schema": "world-roster-v1", "world_ids": list(IDS)}
+    roster = WorldRosterDeclaration.from_dict(payload)
+    payload["world_ids"].reverse()
+    assert roster.world_ids == IDS
+    exported = roster.to_dict()
+    exported["world_ids"].clear()
+    assert roster.to_dict() == {"schema": "world-roster-v1", "world_ids": list(IDS)}
+    with pytest.raises((AttributeError, TypeError)):
+        roster.world_ids = tuple(reversed(IDS))
+
+
+@pytest.mark.parametrize("ids", [[], [""], ["x", "x"], [True, "x"], "not-an-array"])
+def test_roster_invalid_ids_refuse(ids):
+    from townlet.config.world_roster import WorldRosterDeclaration
+
+    with pytest.raises((TypeError, ValueError)):
+        WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": ids})
+
+
+@pytest.mark.parametrize("change", ["missing", "old_schema", "extra"])
+def test_roster_exact_schema(change):
+    from townlet.config.world_roster import WorldRosterDeclaration
+
+    payload = {"schema": "world-roster-v1", "world_ids": list(IDS)}
+    if change == "missing":
+        del payload["world_ids"]
+    elif change == "old_schema":
+        payload["schema"] = "world-roster-v0"
+    else:
+        payload["row_names"] = list(IDS)
+    with pytest.raises((TypeError, ValueError)):
+        WorldRosterDeclaration.from_dict(payload)
+
+
+@pytest.mark.parametrize("order", [(IDS[0],), (IDS[0], IDS[0]), (IDS[0], "foreign")])
+def test_invalid_binding_precedes_constructor_randomness(compiled, monkeypatch, order):
+    from townlet.environment.vectorized_env import VectorizedHamletEnv
+
+    def forbidden(*args, **kwargs):
+        pytest.fail("invalid constructor binding reached random layout")
+
+    monkeypatch.setattr(VectorizedHamletEnv, "randomize_affordance_positions", forbidden)
+    before = torch.get_rng_state().clone()
+    with pytest.raises((TypeError, ValueError)):
+        _env(compiled, order)
+    assert torch.equal(before, torch.get_rng_state())
+
+
+def test_real_env_requires_explicit_roster_seed_binding(compiled):
+    from townlet.environment.vectorized_env import VectorizedHamletEnv
+
+    with pytest.raises(TypeError):
+        VectorizedHamletEnv(universe=compiled, level_name="L0_test", num_agents=2, device="cpu")
+    env = _env(compiled)
+    assert env.world_ids == IDS
+    assert dict(env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)
+
+
+def test_reservation_and_failed_preflight_are_pure(compiled):
+    run = _Run(_env(compiled))
+    before = _state(run.env)
+    first = run.env.prepare_episode(batch_episode=1, release=run.release)
+    second = run.env.prepare_episode(batch_episode=1, release=run.release)
+    assert first.world_ids == second.world_ids == IDS
+    assert first.world_episode_seqs == second.world_episode_seqs == (1, 1)
+    foreign = _Run(_env(compiled))
+    foreign_reservation = foreign.env.prepare_episode(batch_episode=1, release=foreign.release)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.validate_episode_reservation(foreign_reservation)
+    _same(before, _state(run.env))
+    run.env.validate_episode_reservation(first)
+    _same(before, _state(run.env))
+
+
+def test_authority_bootstrap_binding_and_consumption(compiled):
+    run = _Run(_env(compiled))
+    assert run.env.bind_boundary_authority(owner=run.boundary) is run.authority
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.bind_boundary_authority(owner=_Sink())
+    _same(before, _state(run.env))
+    reservation, reset = run.reset(1)
+    assert reset.accepted.world_episode_seqs == (1, 1)
+    with pytest.raises(ValueError):
+        run.authority.bootstrap(first_batch_episode=1)
+    with pytest.raises(ValueError):
+        run.env.prepare_episode(batch_episode=2, release=run.release)
+    assert run.env.reset(reservation=reservation) is reset
+
+
+def test_reset_retry_after_rollout_owns_original_observation(compiled, monkeypatch):
+    run = _Run(_env(compiled))
+    calls = []
+    original = run.env._get_observations
+
+    def observed():
+        calls.append(1)
+        return original()
+
+    monkeypatch.setattr(run.env, "_get_observations", observed)
+    reservation, receipt = run.reset(1)
+    initial = receipt.observation.clone()
+    receipt.observation.fill_(1234)
+    _same(initial, receipt.observation)
+    run.step()
+    before = _state(run.env)
+    count = len(calls)
+    assert run.env.reset(reservation=reservation) is receipt
+    assert len(calls) == count
+    _same(before, _state(run.env))
+    _same(initial, receipt.observation)
+
+
+def test_activation_requires_owned_matching_receipts(compiled):
+    run = _Run(_env(compiled))
+    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
+    accepted = run.env.reset(reservation=reservation).accepted
+    before = _state(run.env)
+    with pytest.raises((TypeError, ValueError)):
+        run.env.activate_episode(
+            accepted=accepted,
+            population_receipt=SimpleNamespace(accepted=accepted),
+            curiosity_receipt=run.bank.activation(accepted),
+        )
+    _same(before, _state(run.env))
+    population = run.population.activation(accepted)
+    curiosity = run.bank.activation(accepted)
+    activation = run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity)
+    assert run.env.activate_episode(accepted=accepted, population_receipt=population, curiosity_receipt=curiosity) is activation
+
+
+def test_late_reset_failure_quarantines_without_false_rollback(compiled, monkeypatch):
+    run = _Run(_env(compiled))
+    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
+
+    def fail_late():
+        raise RuntimeError("injected late encoding failure")
+
+    monkeypatch.setattr(run.env, "_get_observations", fail_late)
+    with pytest.raises(RuntimeError, match="late encoding"):
+        run.env.reset(reservation=reservation)
+    assert run.env.world_phase == "quarantined"
+    assert dict(run.env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)
+    with pytest.raises((ValueError, RuntimeError)):
+        run.env.reset(reservation=reservation)
+    with pytest.raises((ValueError, RuntimeError)):
+        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
+    with pytest.raises((ValueError, RuntimeError)):
+        run.initial()
+    # No assertion of simulator or RNG rollback: reconstruction is the recovery.
+    fresh = _Run(_env(compiled))
+    assert fresh.reset(1)[1].accepted.world_episode_seqs == (1, 1)
+
+
+def test_close_alone_blocks_save_next_release_is_save_independent(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step()
+    prepared, closure, dispositions = run.close(1)
+    before = _state(run.env)
+    assert run.env.close_episode(prepared) is closure
+    _same(before, _state(run.env))
+    with pytest.raises(ValueError):
+        run.completed((1,))
+    with pytest.raises(ValueError):
+        run.env.prepare_episode(batch_episode=2, release=run.release)
+    run.release_closed(1, closure, dispositions)
+    assert run.env.install_boundary_release(run.release) is run.release
+    # No checkpoint call between release and the next successful reset.
+    assert run.reset(2)[1].accepted.world_episode_seqs == (2, 2)
+
+
+def test_wrong_release_and_changed_disposition_are_pure(compiled):
+    run = _Run(_env(compiled))
+    foreign = _Run(_env(compiled))
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.install_boundary_release(foreign.release)
+    _same(before, _state(run.env))
+    run.reset(1)
+    run.step((IDS[0],))
+    prepared, closure, dispositions = run.close(1, (IDS[0],))
+    before = _state(run.env)
+    forged = replace(dispositions)
+    with pytest.raises((TypeError, ValueError)):
+        run.env.prepare_episode_close(
+            accepted=run.accepted,
+            boundary_key=1,
+            completion_content=run.events[1],
+            participated_world_ids=(IDS[0],),
+            dispositions=forged,
+        )
+    _same(before, _state(run.env))
+    assert run.env.close_episode(prepared) is closure
+
+
+def test_empty_abandon_is_not_completion_or_initial(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    abandoned = run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
+    assert run.env.abandon_episode(accepted=run.accepted, reason="empty_participation") is abandoned
+    assert run.env.world_phase == "quarantined"
+    assert dict(run.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
+    with pytest.raises(ValueError):
+        run.completed(())
+    with pytest.raises(ValueError):
+        run.initial()
+    with pytest.raises(ValueError):
+        run.env.prepare_episode(batch_episode=2, release=run.release)
+
+
+def test_participating_episode_cannot_claim_empty_abandon(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step((IDS[0],))
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.abandon_episode(accepted=run.accepted, reason="empty_participation")
+    _same(before, _state(run.env))
+
+
+def test_initial_snapshot_repeat_restore_and_first_real_reset(compiled):
+    run = _Run(_env(compiled))
+    before = _state(run.env)
+    state = run.initial()
+    _same(state, run.initial())
+    _same(before, _state(run.env))
+    assert state["schema"] == "world-lifecycle-v3" and state["kind"] == "INITIAL"
+    assert state["accepted_bindings"] == []
+    assert state["last_closed_episode"] is None and state["completed_boundary_key"] is None
+    assert state["saved_lane_binding"] is None
+    assert state["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
+    restored = _restore(compiled, state, tuple(reversed(IDS)))
+    assert restored.env.world_phase == "bootstrap-ready"
+    assert restored.reset(1)[1].accepted.world_episode_seqs == (1, 1)
+    with pytest.raises(ValueError):
+        restored.initial()
+    restored.step()
+    _, closure, dispositions = restored.close(1)
+    restored.release_closed(1, closure, dispositions)
+    assert restored.completed((1,))["kind"] == "COMPLETED"
+
+
+@pytest.mark.parametrize(
+    "field,value",
+    [
+        ("kind", "UNKNOWN"),
+        ("schema", "world-lifecycle-v2"),
+        ("completed_boundary_key", 0),
+        ("last_closed_episode", {}),
+        ("accepted_episode_seqs", {IDS[0]: 0, IDS[1]: 1}),
+        ("next_batch_episode", True),
+    ],
+)
+def test_malformed_initial_restore_is_pure(compiled, field, value):
+    state = _Run(_env(compiled)).initial()
+    state[field] = value
+    target = _Run(_env(compiled), bootstrap=False)
+    before = _state(target.env)
+    with pytest.raises((TypeError, ValueError)):
+        target.env.prepare_world_restore(
+            kind="INITIAL",
+            state=state,
+            world_roster=_roster(),
+            destination_world_ids=IDS,
+            semantic_execution_identity=target.env.semantic_execution_identity,
+        )
+    _same(before, _state(target.env))
+
+
+def test_initial_restore_over_live_boundary_refuses(compiled):
+    run = _Run(_env(compiled))
+    state = run.initial()
+    run.reset(1)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.prepare_world_restore(
+            kind="INITIAL",
+            state=state,
+            world_roster=_roster(),
+            destination_world_ids=IDS,
+            semantic_execution_identity=run.env.semantic_execution_identity,
+        )
+    _same(before, _state(run.env))
+
+
+def test_two_boundaries_two_reorders_keep_historical_binding_verbatim(compiled):
+    first = _Run(_env(compiled))
+    first.reset(1)
+    first.step()
+    _, closure, dispositions = first.close(1)
+    first.release_closed(1, closure, dispositions)
+    saved1 = first.completed((1,))
+    old_content = deepcopy(first.events[1])
+    second = _restore(compiled, saved1, tuple(reversed(IDS)))
+    assert dict(second.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
+    assert second.reset(2)[1].accepted.world_ids == tuple(reversed(IDS))
+    second.step((IDS[0],))
+    _, closure, dispositions = second.close(2, (IDS[0],))
+    second.release_closed(2, closure, dispositions)
+    saved2 = second.completed((1, 2))
+    assert saved2["accepted_bindings"] == [
+        {"batch_episode": 1, "world_ids": list(IDS), "world_episode_seqs": [1, 1]},
+        {"batch_episode": 2, "world_ids": list(reversed(IDS)), "world_episode_seqs": [2, 2]},
+    ]
+    third = _restore(compiled, saved2, IDS)
+    restored_bindings = third.completed((1, 2))["accepted_bindings"]
+    _same(saved2["accepted_bindings"], restored_bindings)
+    by_batch = {binding["batch_episode"]: binding for binding in restored_bindings}
+    for batch, index, world_id, sequence, _ in old_content + second.events[2]:
+        assert by_batch[batch]["world_ids"][index] == world_id
+        assert by_batch[batch]["world_episode_seqs"][index] == sequence
+    next_receipt = third.reset(3)[1].accepted
+    assert next_receipt.world_ids == IDS and next_receipt.world_episode_seqs == (3, 3)
+    # No unequal-cursor fixture is passed off as reachable native history.
+
+
+@pytest.mark.parametrize("damage", ["missing_latest", "duplicate_batch", "wrong_latest", "foreign_world", "bool_sequence"])
+def test_completed_binding_corruption_refuses_before_install(compiled, damage):
+    run = _Run(_env(compiled))
+    for batch in (1, 2):
+        run.reset(batch)
+        run.step()
+        _, closure, dispositions = run.close(batch)
+        run.release_closed(batch, closure, dispositions)
+    state = run.completed((1, 2))
+    if damage == "missing_latest":
+        state["accepted_bindings"].pop()
+    elif damage == "duplicate_batch":
+        state["accepted_bindings"].append(deepcopy(state["accepted_bindings"][0]))
+    elif damage == "wrong_latest":
+        state["accepted_bindings"][-1]["world_ids"].reverse()
+    elif damage == "foreign_world":
+        state["accepted_bindings"][0]["world_ids"][0] = "foreign"
+    else:
+        state["accepted_bindings"][0]["world_episode_seqs"][1] = True
+    target = _Run(_env(compiled), bootstrap=False)
+    before = _state(target.env)
+    with pytest.raises((ValueError, TypeError)):
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
+def test_step_before_activation_and_changed_reservation_refuse(compiled):
+    run = _Run(_env(compiled))
+    reservation = run.env.prepare_episode(batch_episode=1, release=run.release)
+    run.env.reset(reservation=reservation)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.env.step(torch.zeros(2, dtype=torch.long), depletion_multiplier=1.0)
+    with pytest.raises(ValueError):
+        run.env.reset(reservation=replace(reservation, world_episode_seqs=(2, 2)))
+    _same(before, _state(run.env))
+
+
+def test_empty_close_and_unknown_history_reference_refuse(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.close(1, ())
+    _same(before, _state(run.env))
+    run.step()
+    _, closure, dispositions = run.close(1)
+    run.release_closed(1, closure, dispositions)
+    before = _state(run.env)
+    with pytest.raises(ValueError):
+        run.completed((1, 12))
+    _same(before, _state(run.env))
+
+
+def test_initial_schema_exact_and_snapshot_isolation(compiled):
+    run = _Run(_env(compiled))
+    state = run.initial()
+    assert set(state) == {
+        "schema",
+        "kind",
+        "next_batch_episode",
+        "world_roster",
+        "manifest_digest",
+        "roster_semantic_identity",
+        "training_seed",
+        "execution_identity",
+        "saved_lane_binding",
+        "destination_lane_binding",
+        "accepted_episode_seqs",
+        "last_closed_episode",
+        "completed_boundary_key",
+        "accepted_bindings",
+    }
+    state["world_roster"]["world_ids"].clear()
+    state["accepted_episode_seqs"][IDS[0]] = 99
+    assert run.initial()["world_roster"]["world_ids"] == list(IDS)
+    assert run.initial()["accepted_episode_seqs"] == dict.fromkeys(IDS, 0)
+
+
+@pytest.mark.parametrize("mode", ["wrong_kind", "extra_key", "changed_manifest", "wrong_seed", "unknown_member"])
+def test_restore_identity_and_kind_mismatch_refuse(compiled, mode):
+    state = _Run(_env(compiled)).initial()
+    target = _Run(_env(compiled), bootstrap=False)
+    kind, order = "INITIAL", IDS
+    if mode == "wrong_kind":
+        kind = "COMPLETED"
+    elif mode == "extra_key":
+        state["legacy_episode"] = 0
+    elif mode == "changed_manifest":
+        state["world_roster"]["world_ids"].reverse()
+    elif mode == "wrong_seed":
+        state["training_seed"] += 1
+    else:
+        order = (IDS[0], "foreign")
+    before = _state(target.env)
+    with pytest.raises((ValueError, TypeError)):
+        target.env.prepare_world_restore(
+            kind=kind,
+            state=state,
+            world_roster=_roster(),
+            destination_world_ids=order,
+            semantic_execution_identity=target.env.semantic_execution_identity,
+        )
+    _same(before, _state(target.env))
+
+
+def test_foreign_boundary_effect_receipt_cannot_release(compiled):
+    run = _Run(_env(compiled))
+    run.reset(1)
+    run.step()
+    _, closure, dispositions = run.close(1)
+    foreign = _Sink().receipt(
+        "boundary_effects",
+        batch_episode=1,
+        accepted_identity=run.accepted,
+        completion_content=run.events[1],
+        retirement_receipt=dispositions,
+    )
+    before = _state(run.env)
+    with pytest.raises((ValueError, TypeError)):
+        run.authority.completed(closure=closure, effects=foreign)
+    with pytest.raises(ValueError):
+        run.initial()
+    _same(before, _state(run.env))
