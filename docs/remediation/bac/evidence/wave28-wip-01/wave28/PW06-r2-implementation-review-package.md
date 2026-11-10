# PW06 actual CP/BANK implementation
Base41e5742307ad170bc9871e0b5354b00599084da6
Candidate9f27d612ad3527b1309bfc60219e58d45d03c834
Test1401/ad1491f5 frozen, whole4source inventory inmanifest.

 src/townlet/exploration/curiosity_checkpoint.py | 878 ++++++++++++++++++++++++
 src/townlet/exploration/scoped_curiosity.py     | 215 +++++-
 2 files changed, 1092 insertions(+), 1 deletion(-)
diff --git a/src/townlet/exploration/curiosity_checkpoint.py b/src/townlet/exploration/curiosity_checkpoint.py
new file mode 100644
index 00000000..194ae93d
--- /dev/null
+++ b/src/townlet/exploration/curiosity_checkpoint.py
@@ -0,0 +1,878 @@
+"""Strict current BANK transport and off-side runtime codecs.
+
+Portable values carry evidence, never ENV acceptance or closing authority.
+Provider algorithms and native validation belong to their actual producers.
+"""
+
+from __future__ import annotations
+
+import math
+from collections.abc import Mapping
+from copy import deepcopy
+from typing import Any, cast
+
+import numpy as np
+import torch
+
+from townlet.config.exploration_policy import ResolvedExplorationPolicy
+from townlet.config.world_roster import WorldAcceptedEpisode, WorldRecord, WorldRosterDeclaration, validate_world_snapshot, world_binding
+from townlet.exploration.world_curiosity_state import CuriosityEventId, CuriosityStepStamp, ServiceClock, WorldCuriosityDescriptor
+from townlet.training.episode import freeze_lane_outcome, lane_outcome_from_state
+from townlet.vfs.random_draws import VFSRandomness, VFSWorldContext
+
+ENVELOPE = set(
+    (
+        "schema policy policy_identity descriptor source_device curiosity_epoch bank_phase "
+        "dispatch_identity worlds shared_backend step completion"
+    ).split()
+)
+CURSOR = set("accepted_episode_seq eligible_seq cumulative_service_position participated disposition".split())
+CONTENT = set("predecessor successor actions active vector_tick".split())
+RECEIPT = (
+    "scope",
+    "world_id",
+    "event_ids",
+    "eligible",
+    "clock",
+    "admitted_rows",
+    "consumed_rows",
+    "dropped_rows",
+    "pending_rows",
+    "optimizer_updates",
+    "mandatory_service_updates",
+    "last_loss",
+)
+STEP = set("original_binding stamp tick active context update_stats reward receipts serviced".split())
+STAMP = set("event_ids world_ids world_episode_seqs eligible_seqs eligible".split())
+EVENT = set("curiosity_epoch world_id world_episode_seq eligible_seq".split())
+COMPLETION = set("status original_accepted_identity boundary_key completion_content participated_world_ids dispositions outcomes".split())
+
+
+class PreparedCuriosityRestore:
+    """Identity-only handle; BANK retains the complete private publication data."""
+
+    __slots__ = ()
+
+
+def require(condition: bool, message: str) -> None:
+    if not condition:
+        raise ValueError(message)
+
+
+def keys(value: Any, required: set[str], name: str) -> None:
+    require(type(value) is dict and set(value) == required, f"{name}: exact current fields required")
+
+
+def integer(value: Any, minimum: int, name: str) -> None:
+    require(type(value) is int and value >= minimum, f"{name}: exact integer required")
+
+
+def boolean(value: Any, name: str) -> None:
+    require(type(value) is bool, f"{name}: exact bool required")
+
+
+def number(value: Any, name: str) -> None:
+    require(type(value) in (int, float) and math.isfinite(value), f"{name}: finite number required")
+
+
+def same(left: Any, right: Any) -> bool:
+    if type(left) is not type(right):
+        return False
+    if isinstance(left, torch.Tensor):
+        return (left.shape, left.dtype, left.device, left.layout) == (right.shape, right.dtype, right.device, right.layout) and torch.equal(
+            left, right
+        )
+    if isinstance(left, np.ndarray):
+        return left.dtype == right.dtype and left.shape == right.shape and bool(np.array_equal(left, right))
+    if isinstance(left, Mapping):
+        return left.keys() == right.keys() and all(same(left[key], right[key]) for key in left)
+    if isinstance(left, (list, tuple)):
+        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right, strict=True))
+    return bool(left == right)
+
+
+def owned(value: Any) -> Any:
+    """Closed portable data only; reject unsupported storage before cloning."""
+    if isinstance(value, torch.Tensor):
+        require(value.layout == torch.strided and value.device.type in ("cpu", "cuda"), "portable dense CPU/CUDA tensor required")
+        require(bool(torch.isfinite(value).all()), "nonfinite transported tensor")
+        return value.detach().clone()
+    if isinstance(value, np.ndarray):
+        require(not value.dtype.hasobject, "object arrays are not portable")
+        return value.copy()
+    if type(value) is dict:
+        return {owned(key): owned(item) for key, item in value.items()}
+    if type(value) is list:
+        return [owned(item) for item in value]
+    if type(value) is tuple:
+        return tuple(owned(item) for item in value)
+    require(value is None or type(value) in (str, int, float, bool), "nonportable checkpoint object")
+    if type(value) is float:
+        require(math.isfinite(value), "nonfinite scalar")
+    return value
+
+
+def tensor_bytes(value: Any) -> int:
+    """Metadata-only input inventory, before admission or tensor cloning."""
+    if isinstance(value, torch.Tensor):
+        return value.numel() * value.element_size()
+    if isinstance(value, np.ndarray):
+        return value.nbytes
+    if isinstance(value, Mapping):
+        return sum(tensor_bytes(key) + tensor_bytes(item) for key, item in value.items())
+    if isinstance(value, (tuple, list)):
+        return sum(tensor_bytes(item) for item in value)
+    return 0
+
+
+def accepted_identity(accepted: WorldAcceptedEpisode) -> dict[str, Any]:
+    return dict(
+        batch_episode=accepted.batch_episode, world_ids=list(accepted.world_ids), world_episode_seqs=list(accepted.world_episode_seqs)
+    )
+
+
+def identity(value: Any, worlds: tuple[str, ...]) -> dict[str, int]:
+    keys(value, {"batch_episode", "world_ids", "world_episode_seqs"}, "accepted value identity")
+    integer(value["batch_episode"], 1, "batch episode")
+    ids, episodes = value["world_ids"], value["world_episode_seqs"]
+    require(type(ids) is list and type(episodes) is list and len(ids) == len(episodes) == len(worlds), "identity row geometry")
+    require(all(type(world) is str and bool(world) for world in ids), "exact identity IDs")
+    require(len(set(ids)) == len(ids) and set(ids) == set(worlds), "identity exact membership")
+    for episode in episodes:
+        integer(episode, 1, "accepted sequence")
+    return dict(zip(ids, episodes, strict=True))
+
+
+def preflight(
+    state: Any, *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, device: torch.device, mode: str
+) -> None:
+    keys(state, ENVELOPE, "bank checkpoint")
+    require(type(state["schema"]) is str and state["schema"] == "curiosity-bank-state-v1", "bank schema")
+    require(
+        type(mode) is str and mode in ("initial", "live_episode", "completed_boundary") and state["bank_phase"] == mode,
+        "bank phase mismatch",
+    )
+    integer(state["curiosity_epoch"], 0, "curiosity epoch")
+    require(state["curiosity_epoch"] == 0, "ordinary resume requires epoch zero")
+    restored_policy = ResolvedExplorationPolicy.from_dict(state["policy"])
+    require(
+        restored_policy.to_dict() == policy.to_dict() and state["policy_identity"] == policy.policy_identity, "complete policy mismatch"
+    )
+    source = WorldCuriosityDescriptor.from_dict(state["descriptor"])
+    require(
+        set(source.world_ids) == set(descriptor.world_ids) and len(source.world_ids) == len(descriptor.world_ids), "descriptor membership"
+    )
+    expected = WorldCuriosityDescriptor.from_policy(
+        policy,
+        world_ids=source.world_ids,
+        observation_dim=descriptor.observation_dim,
+        action_dim=descriptor.action_dim,
+        training_seed=descriptor.training_seed,
+    )
+    require(source.to_dict() == expected.to_dict(), "complete source descriptor mismatch")
+    require(type(state["source_device"]) is str and state["source_device"] == str(device), "same declared device profile required")
+    require(torch.get_default_dtype() == torch.float32, "declared float32 profile required")
+    records = state["worlds"]
+    require(type(records) is list and len(records) == len(descriptor.world_ids), "world record cardinality")
+    ids = []
+    for record in records:
+        keys(record, {"world_id", "backend", "gradients", "cursor", "phase_cache"}, "world record")
+        require(type(record["world_id"]) is str and bool(record["world_id"]), "world record exact ID")
+        ids.append(record["world_id"])
+    require(len(set(ids)) == len(ids) and set(ids) == set(descriptor.world_ids), "missing/extra/duplicate world IDs")
+    if descriptor.scope == "shared":
+        keys(state["shared_backend"], {"native", "gradients"}, "shared native")
+        require(all(record["backend"] is None and record["gradients"] is None for record in records), "shared world backend must be absent")
+    else:
+        require(state["shared_backend"] is None, "private state has shared provider")
+    if mode == "completed_boundary":
+        keys(state["completion"], COMPLETION, "completion")
+        require(state["completion"]["status"] == "committed", "only committed history is portable")
+        require(state["dispatch_identity"] is None, "history cannot be live dispatch")
+    else:
+        require(state["completion"] is None, "live/initial state cannot import completion")
+    if mode == "initial":
+        require(state["dispatch_identity"] is None and state["step"] is None, "INITIAL has no dispatch/step")
+
+
+def check_mode(*, mode: str, accepted: Any, parent: Any, validate: Any) -> None:
+    if mode == "live_episode":
+        require(isinstance(accepted, WorldAcceptedEpisode) and parent is None and validate is None, "live restore needs actual token only")
+    elif mode == "completed_boundary":
+        require(
+            accepted is None and isinstance(parent, WorldRecord) and callable(validate), "completed restore needs actual parent preparation"
+        )
+    else:
+        require(
+            accepted is None and ((parent is None and validate is None) or (isinstance(parent, WorldRecord) and callable(validate))),
+            "INITIAL parent pair",
+        )
+
+
+def match_live(state: dict[str, Any], *, accepted: WorldAcceptedEpisode, descriptor: WorldCuriosityDescriptor) -> None:
+    saved = identity(state["dispatch_identity"], descriptor.world_ids)
+    current = accepted_identity(accepted)
+    actual = identity(current, descriptor.world_ids)
+    require(saved == actual and current["batch_episode"] == state["dispatch_identity"]["batch_episode"], "live accepted values mismatch")
+    require(tuple(accepted.world_ids) == descriptor.world_ids, "receiving live dispatch order")
+    if descriptor.scope == "shared":
+        require(state["dispatch_identity"]["world_ids"] == current["world_ids"], "shared grouped dispatch cannot permute")
+
+
+def match_parent(state: dict[str, Any], *, parent: WorldRecord, descriptor: WorldCuriosityDescriptor) -> None:
+    require(parent.kind == "prepared_restore", "actual parent preparation kind")
+    data = parent.payload
+    keys(data, {"state", "destination_world_ids", "destination_vfs_context"}, "parent preparation payload")
+    require(tuple(data["destination_world_ids"]) == descriptor.world_ids, "parent receiving binding mismatch")
+    world_state = data["state"]
+    require(world_state["training_seed"] == descriptor.training_seed, "parent training seed mismatch")
+    roster = WorldRosterDeclaration.from_dict(world_state["world_roster"])
+    # The producer validates manifest order/digest; the bank requires exact ID membership.
+    require(set(world_state["world_roster"]["world_ids"]) == set(descriptor.world_ids), "parent declared world membership")
+    validate_world_snapshot(
+        world_state,
+        kind=world_state["kind"],
+        roster=roster,
+        seed=descriptor.training_seed,
+        semantic_identity=world_state["execution_identity"],
+    )
+    require(
+        same(world_state["destination_lane_binding"], world_binding(tuple(state["descriptor"]["world_ids"]))),
+        "parent snapshot-producer binding mismatch",
+    )
+    sequences = {record["world_id"]: record["cursor"]["accepted_episode_seq"] for record in state["worlds"]}
+    require(same(world_state["accepted_episode_seqs"], sequences), "parent cursor mismatch")
+    VFSRandomness.validate_state(
+        data["destination_vfs_context"],
+        expected=VFSWorldContext(
+            training_seed=descriptor.training_seed,
+            world_ids=descriptor.world_ids,
+            world_episode_seqs=tuple(sequences[world] for world in descriptor.world_ids),
+        ),
+    )
+    if state["bank_phase"] == "initial":
+        require(world_state["kind"] == "INITIAL" and world_state["last_closed_episode"] is None, "INITIAL parent history")
+        require(all(value == 0 for value in sequences.values()), "INITIAL parent cursor")
+        return
+    completion = state["completion"]
+    binding = completion["original_accepted_identity"]
+    require(world_state["kind"] == "COMPLETED", "completed parent kind")
+    require(world_state["completed_boundary_key"] == completion["boundary_key"], "parent boundary mismatch")
+    closed = world_state["last_closed_episode"]
+    for key in ("batch_episode", "world_ids", "world_episode_seqs"):
+        require(same(list_value(closed[key]), list_value(binding[key])), "parent original closure binding mismatch")
+    require(same(world_state["saved_lane_binding"], world_binding(tuple(binding["world_ids"]))), "parent original lane binding")
+    require(any(same(entry, binding) for entry in world_state["accepted_bindings"]), "parent retained original accepted binding")
+    require(same(closed["completion_content"], completion["completion_content"]), "parent full completion mismatch")
+    require(tuple(closed["participated_world_ids"]) == completion["participated_world_ids"], "parent participants mismatch")
+
+
+def list_value(value: Any) -> Any:
+    if isinstance(value, (tuple, list)):
+        return list(value)
+    return value
+
+
+def event_state(event: CuriosityEventId) -> dict[str, Any]:
+    return dict(
+        curiosity_epoch=event.curiosity_epoch,
+        world_id=event.world_id,
+        world_episode_seq=event.world_episode_seq,
+        eligible_seq=event.eligible_seq,
+    )
+
+
+def event_value(value: Any) -> CuriosityEventId:
+    keys(value, EVENT, "event")
+    result = CuriosityEventId(**value)
+    require(result.curiosity_epoch == 0, "ordinary event epoch")
+    return result
+
+
+def receipt_state(receipt: Any) -> dict[str, Any]:
+    result = {name: getattr(receipt, name) for name in RECEIPT}
+    result["event_ids"] = tuple(event_state(event) for event in receipt.event_ids)
+    result["clock"] = None
+    if receipt.clock is not None:
+        result["clock"] = dict(unit=receipt.clock.unit, position=receipt.clock.position)
+    return result
+
+
+def receipt_value(value: Any, *, descriptor: WorldCuriosityDescriptor) -> Any:
+    from townlet.exploration.scoped_curiosity import WorldServiceReceipt
+
+    keys(value, set(RECEIPT), "service receipt")
+    require(value["scope"] == descriptor.scope, "receipt scope mismatch")
+    boolean(value["eligible"], "receipt eligibility")
+    events = value["event_ids"]
+    require(type(events) is tuple and bool(events), "receipt events")
+    events = tuple(event_value(event) for event in events)
+    ids = tuple(event.world_id for event in events)
+    require(len(set(ids)) == len(ids) and set(ids).issubset(set(descriptor.world_ids)), "receipt event membership")
+    if descriptor.scope == "per_world":
+        require(len(ids) == 1 and value["world_id"] == ids[0], "private receipt identity")
+    else:
+        require(value["world_id"] is None and value["eligible"], "shared aggregate receipt identity")
+    for name in RECEIPT[5:-1]:
+        integer(value[name], 0, name)
+    require(value["mandatory_service_updates"] <= value["optimizer_updates"], "receipt mandatory budget")
+    number(value["last_loss"], "receipt loss")
+    require(value["last_loss"] >= 0, "receipt negative loss")
+    clock = None
+    if value["clock"] is not None:
+        keys(value["clock"], {"unit", "position"}, "service clock")
+        clock = ServiceClock(**value["clock"])
+        require(clock.unit == descriptor.service_clock_unit, "receipt clock unit")
+    trainable = descriptor.provider_kind in ("rnd", "adaptive_rnd", "icm")
+    if value["eligible"] and trainable:
+        require(clock is not None and value["admitted_rows"] == len(events), "active trainable receipt")
+    else:
+        require(clock is None and all(value[name] == 0 for name in RECEIPT[5:]), "nonpredictor/inactive receipt effects")
+    return WorldServiceReceipt(**dict(value, event_ids=events, clock=clock))
+
+
+def encode_cache(cache: dict[str, Any]) -> dict[str, Any]:
+    result = {}
+    for phase, entry in cache.items():
+        item = dict(entry)
+        if phase in ("reward", "service"):
+            item["event_id"] = event_state(entry["event_id"])
+        if phase == "service":
+            item["receipt"] = receipt_state(entry["receipt"])
+        result[phase] = owned(item)
+    return result
+
+
+def stamp_state(stamp: CuriosityStepStamp) -> dict[str, Any]:
+    return dict(
+        event_ids=tuple(event_state(event) for event in stamp.event_ids),
+        world_ids=stamp.world_ids,
+        world_episode_seqs=stamp.world_episode_seqs,
+        eligible_seqs=stamp.eligible_seqs,
+        eligible=stamp.eligible,
+    )
+
+
+def reward_state(reward: Any) -> dict[str, Any]:
+    return dict(
+        raw=reward.raw,
+        scales=reward.scales,
+        eligible=reward.eligible,
+        event_ids=tuple(event_state(event) for event in reward.event_ids),
+        scope=reward.scope,
+    )
+
+
+def encode_step(pending: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
+    result = dict(pending, original_binding=binding, stamp=stamp_state(pending["stamp"]))
+    if pending["reward"] is not None:
+        result["reward"] = reward_state(pending["reward"])
+    if pending["receipts"] is not None:
+        result["receipts"] = tuple(receipt_state(receipt) for receipt in pending["receipts"])
+    return cast(dict[str, Any], owned(result))
+
+
+def tensor(value: Any, shape: tuple[int, ...], dtype: torch.dtype, device: torch.device, name: str) -> None:
+    require(
+        isinstance(value, torch.Tensor)
+        and value.layout == torch.strided
+        and value.shape == shape
+        and value.dtype == dtype
+        and value.device == device
+        and bool(torch.isfinite(value).all()),
+        f"{name}: tensor profile mismatch",
+    )
+
+
+def validate_content(value: Any, *, descriptor: WorldCuriosityDescriptor, device: torch.device, rows: tuple[int, ...]) -> None:
+    keys(value, CONTENT, "transition content")
+    integer(value["vector_tick"], 0, "content tick")
+    tensor(value["predecessor"], rows + (descriptor.observation_dim,), torch.float32, device, "predecessor")
+    tensor(value["successor"], rows + (descriptor.observation_dim,), torch.float32, device, "successor")
+    tensor(value["actions"], rows, torch.int64, device, "actions")
+    tensor(value["active"], rows, torch.bool, device, "active")
+    require(bool(((value["actions"] >= 0) & (value["actions"] < descriptor.action_dim)).all()), "action bounds")
+
+
+def local_content(value: dict[str, Any], index: int) -> dict[str, Any]:
+    result = {}
+    for key, item in value.items():
+        if key == "vector_tick":
+            result[key] = item
+        else:
+            result[key] = item[index]
+    return result
+
+
+def validate_cache(record: dict[str, Any], *, descriptor: WorldCuriosityDescriptor, device: torch.device, mode: str) -> None:
+    cursor, cache, world = record["cursor"], record["phase_cache"], record["world_id"]
+    keys(cursor, CURSOR, "world cursor")
+    for name in ("accepted_episode_seq", "eligible_seq", "cumulative_service_position"):
+        integer(cursor[name], 0, name)
+    boolean(cursor["participated"], "participated")
+    require(cursor["eligible_seq"] <= cursor["cumulative_service_position"], "eligible/cumulative cursor")
+    require(cursor["participated"] == (cursor["eligible_seq"] > 0), "participation cursor")
+    require(type(cache) is dict and set(cache).issubset({"reward", "service", "completion"}), "cache phases")
+    if mode == "initial":
+        require(
+            not cache and all(cursor[name] == 0 for name in ("accepted_episode_seq", "eligible_seq", "cumulative_service_position")),
+            "INITIAL cursors/cache",
+        )
+        require(cursor["disposition"] is None and not cursor["participated"], "INITIAL disposition")
+        return
+    integer(cursor["accepted_episode_seq"], 1, "accepted cursor")
+    if mode == "live_episode":
+        require(cursor["disposition"] is None and "completion" not in cache, "live disposition/history")
+    else:
+        require(cursor["disposition"] in ("completed", "retired_nonparticipating") and "completion" in cache, "completed disposition/cache")
+        require((cursor["disposition"] == "completed") == cursor["participated"], "disposition participation")
+    for phase in ("reward", "service"):
+        if phase not in cache:
+            continue
+        entry = cache[phase]
+        required = {"event_id", "content", "receipt"}
+        if phase == "reward":
+            required = {"event_id", "content", "update_stats", "raw", "scale"}
+        keys(entry, required, f"{phase} cache")
+        event = event_value(entry["event_id"])
+        require(event.world_id == world and event.world_episode_seq == cursor["accepted_episode_seq"], "cache event binding")
+        integer(event.eligible_seq, 1, "cache eligible event")
+        validate_content(entry["content"], descriptor=descriptor, device=device, rows=())
+        require(bool(entry["content"]["active"]), "active local cache required")
+        if phase == "reward":
+            boolean(entry["update_stats"], "cached update_stats")
+            tensor(entry["raw"], (), torch.float32, device, "cached reward")
+            tensor(entry["scale"], (), torch.float32, device, "cached scale")
+            require(bool(entry["scale"] >= 0) and bool(entry["raw"] >= 0), "negative reward/scale")
+            require(event.eligible_seq in (cursor["eligible_seq"], cursor["eligible_seq"] + 1), "reward cursor")
+            if mode == "completed_boundary":
+                require(event.eligible_seq == cursor["eligible_seq"], "completed reward must be settled")
+        else:
+            require(event.eligible_seq == cursor["eligible_seq"] and cursor["participated"], "service cursor")
+            receipt = receipt_value(entry["receipt"], descriptor=descriptor)
+            require(receipt.eligible and event in receipt.event_ids, "cache receipt event")
+            if receipt.clock is not None:
+                position = entry["content"]["vector_tick"]
+                if descriptor.scope == "per_world":
+                    position = cursor["cumulative_service_position"]
+                require(receipt.clock.position == position, "local service clock")
+    if "service" in cache:
+        require("reward" in cache, "service without reward cache")
+        reward_event = event_value(cache["reward"]["event_id"])
+        service_event = event_value(cache["service"]["event_id"])
+        require(reward_event.eligible_seq >= service_event.eligible_seq, "cache phase order")
+        if reward_event == service_event:
+            require(same(cache["reward"]["content"], cache["service"]["content"]), "cache phase content mismatch")
+    require(cursor["eligible_seq"] == 0 or "service" in cache, "settled cursor without service cache")
+
+
+def validate_completion(state: dict[str, Any], *, descriptor: WorldCuriosityDescriptor) -> None:
+    completion = state["completion"]
+    if completion is None:
+        return
+    keys(completion, COMPLETION, "historical completion")
+    require(completion["status"] == "committed", "historical status")
+    binding = completion["original_accepted_identity"]
+    episodes = identity(binding, descriptor.world_ids)
+    integer(completion["boundary_key"], 1, "completion boundary")
+    require(completion["boundary_key"] == binding["batch_episode"], "completion boundary identity")
+    records = {record["world_id"]: record for record in state["worlds"]}
+    participants = tuple(world for world in binding["world_ids"] if records[world]["cursor"]["participated"])
+    require(
+        bool(participants) and type(completion["participated_world_ids"]) is tuple and completion["participated_world_ids"] == participants,
+        "completion participation/order",
+    )
+    dispositions = []
+    for world in binding["world_ids"]:
+        cursor = records[world]["cursor"]
+        require(cursor["accepted_episode_seq"] == episodes[world], "historical cursor binding")
+        dispositions.append((world, cursor["disposition"]))
+    require(same(completion["dispositions"], tuple(dispositions)), "historical dispositions/order")
+    values = completion["outcomes"]
+    require(type(values) is tuple and len(values) == len(participants), "complete outcomes cardinality")
+    canonical = []
+    for world, value in zip(participants, values, strict=True):
+        event = lane_outcome_from_state(value)
+        require(
+            event.world_id == world and event.world_episode_seq == episodes[world] and event.batch_episode == binding["batch_episode"],
+            "outcome original identity",
+        )
+        require(event.outcome.agent_idx == binding["world_ids"].index(world), "outcome original row provenance")
+        frozen = freeze_lane_outcome(event)
+        canonical.append((frozen.payload.hex(), frozen.fingerprint))
+    require(same(tuple(canonical), completion["completion_content"]), "complete canonical outcomes mismatch")
+    for world, disposition in dispositions:
+        cached = records[world]["phase_cache"]["completion"]
+        keys(cached, {"episode", "disposition", "content"}, "completion cache")
+        expected = None
+        if world in participants:
+            expected = canonical[participants.index(world)]
+        require(
+            type(cached["episode"]) is int and cached["episode"] == episodes[world] and cached["disposition"] == disposition,
+            "local completion binding",
+        )
+        require(same(cached["content"], expected), "local completion content")
+
+
+def stamp_value(value: Any, *, device: torch.device) -> CuriosityStepStamp:
+    keys(value, STAMP, "step stamp")
+    require(type(value["event_ids"]) is tuple, "stamp events tuple")
+    require(value["world_episode_seqs"].device == device, "stamp selected device")
+    return CuriosityStepStamp(**dict(value, event_ids=tuple(event_value(event) for event in value["event_ids"])))
+
+
+def validate_step(state: dict[str, Any], *, descriptor: WorldCuriosityDescriptor, device: torch.device) -> None:
+    step = state["step"]
+    if step is None:
+        return
+    keys(step, STEP, "current step")
+    binding = step["original_binding"]
+    episodes = identity(binding, descriptor.world_ids)
+    if state["bank_phase"] == "completed_boundary":
+        require(
+            same(binding, state["completion"]["original_accepted_identity"]) and step["serviced"] is True, "historical settled step binding"
+        )
+    else:
+        require(same(binding, state["dispatch_identity"]), "step/dispatch binding")
+    stamp = stamp_value(step["stamp"], device=device)
+    require(
+        list(stamp.world_ids) == binding["world_ids"] and stamp.world_episode_seqs.tolist() == binding["world_episode_seqs"],
+        "step stamp binding",
+    )
+    integer(step["tick"], 0, "step tick")
+    n = len(stamp.world_ids)
+    tensor(step["active"], (n,), torch.bool, device, "step eligibility")
+    require(same(step["active"], stamp.eligible), "step eligibility stamp mismatch")
+    boolean(step["serviced"], "step serviced")
+    context, reward = step["context"], step["reward"]
+    if reward is None:
+        require(context is None and step["update_stats"] is None and step["receipts"] is None and not step["serviced"], "reserved phase")
+    else:
+        validate_content(context, descriptor=descriptor, device=device, rows=(n,))
+        require(context["vector_tick"] == step["tick"] and same(context["active"], stamp.eligible), "step context provenance")
+        boolean(step["update_stats"], "step update_stats")
+        keys(reward, {"raw", "scales", "eligible", "event_ids", "scope"}, "step reward")
+        require(reward["scope"] == descriptor.scope and same(reward["event_ids"], step["stamp"]["event_ids"]), "reward event/scope")
+        tensor(reward["raw"], (n,), torch.float32, device, "step reward raw")
+        tensor(reward["scales"], (n,), torch.float32, device, "step reward scales")
+        tensor(reward["eligible"], (n,), torch.bool, device, "step reward eligibility")
+        require(same(reward["eligible"], stamp.eligible) and bool((reward["scales"] >= 0).all()), "reward eligibility/scale")
+        require(bool((reward["raw"] >= 0).all()), "negative raw novelty")
+        require(
+            bool((reward["raw"][~stamp.eligible] == 0).all()) and bool((reward["scales"][~stamp.eligible] == 0).all()),
+            "inactive reward effects",
+        )
+    receipts = step["receipts"]
+    if step["serviced"]:
+        require(reward is not None and type(receipts) is tuple, "settled step needs reward/receipts")
+        decoded = tuple(receipt_value(receipt, descriptor=descriptor) for receipt in receipts)
+        if descriptor.scope == "per_world":
+            require(len(decoded) == n, "private receipt rows")
+            require(
+                all(
+                    receipt.event_ids == (event,) and receipt.eligible == bool(stamp.eligible[i])
+                    for i, (receipt, event) in enumerate(zip(decoded, stamp.event_ids, strict=True))
+                ),
+                "private step receipts",
+            )
+        else:
+            active_events = tuple(event for i, event in enumerate(stamp.event_ids) if bool(stamp.eligible[i]))
+            if active_events:
+                require(len(decoded) == 1 and decoded[0].event_ids == active_events, "shared grouped receipt")
+            else:
+                require(not decoded, "shared inactive receipts")
+    else:
+        require(receipts is None, "unsettled step has receipts")
+    records = {record["world_id"]: record for record in state["worlds"]}
+    for index, event in enumerate(stamp.event_ids):
+        record = records[event.world_id]
+        cursor, cache = record["cursor"], record["phase_cache"]
+        require(cursor["accepted_episode_seq"] == episodes[event.world_id], "step cursor episode")
+        expected = cursor["eligible_seq"]
+        if bool(stamp.eligible[index]) and not step["serviced"]:
+            expected += 1
+        require(event.eligible_seq == expected, "step cursor sequence")
+        if bool(stamp.eligible[index]) and reward is not None:
+            cached = cache["reward"]
+            require(
+                same(cached["event_id"], event_state(event)) and same(cached["content"], local_content(context, index)),
+                "step local reward cache",
+            )
+            require(
+                cached["update_stats"] == step["update_stats"]
+                and same(cached["raw"], reward["raw"][index])
+                and same(cached["scale"], reward["scales"][index]),
+                "step cached reward values",
+            )
+            if step["serviced"]:
+                require(same(cache["service"]["event_id"], event_state(event)), "step settled cache event")
+                receipt_index = 0
+                if descriptor.scope == "per_world":
+                    receipt_index = index
+                require(same(cache["service"]["receipt"], receipts[receipt_index]), "step/local receipt mismatch")
+
+
+def validate_records(
+    state: dict[str, Any], *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, device: torch.device
+) -> None:
+    mode = state["bank_phase"]
+    episodes = None
+    if mode == "live_episode":
+        episodes = identity(state["dispatch_identity"], descriptor.world_ids)
+    for record in state["worlds"]:
+        validate_cache(record, descriptor=descriptor, device=device, mode=mode)
+        cursor = record["cursor"]
+        if episodes is not None:
+            require(cursor["accepted_episode_seq"] == episodes[record["world_id"]], "live cursor accepted identity")
+        if descriptor.scope == "per_world":
+            envelope = record["backend"]
+            keys(envelope, {"schema", "healthy", "backend", "rng"}, "owned provider envelope")
+            require(envelope["schema"] == "owned-world-backend-v1" and envelope["healthy"] is True, "healthy owned provider required")
+            native = envelope["backend"]
+            if policy.strategy in ("rnd", "adaptive_rnd", "icm"):
+                if policy.strategy == "adaptive_rnd":
+                    native = native["rnd_state"]
+                if policy.strategy != "icm":
+                    native = native["predictor_service"]
+                    admitted = native["admitted_rows"]
+                else:
+                    admitted = native["counters"]["admitted_rows"]
+                require(
+                    type(admitted) is int and admitted == cursor["cumulative_service_position"],
+                    "provider/BANK cumulative admission mismatch",
+                )
+                position = native["service_position"]
+                if position is None:
+                    require(admitted == 0, "unstarted provider position")
+                else:
+                    require(type(position) is int and position == admitted, "private provider service position")
+    validate_completion(state, descriptor=descriptor)
+    validate_step(state, descriptor=descriptor, device=device)
+    binding = state["dispatch_identity"]
+    if mode == "completed_boundary":
+        binding = state["completion"]["original_accepted_identity"]
+    records = {record["world_id"]: record for record in state["worlds"]}
+    for record in state["worlds"]:
+        cache, cursor = record["phase_cache"], record["cursor"]
+        if "reward" in cache:
+            scale = cache["reward"]["scale"]
+            if policy.strategy != "adaptive_rnd":
+                expected_scale = torch.tensor(policy.initial_intrinsic_weight, dtype=torch.float32, device=device)
+                require(same(scale, expected_scale), "cached selected reward scale")
+            else:
+                require(
+                    bool(scale >= policy.min_intrinsic_weight) and bool(scale <= policy.initial_intrinsic_weight),
+                    "cached adaptive scale bounds",
+                )
+            if policy.strategy == "none":
+                require(bool(cache["reward"]["raw"] == 0), "none reward effect")
+        if "service" in cache and descriptor.scope == "shared":
+            require(binding is not None, "shared receipt needs accepted provenance")
+            events = cache["service"]["receipt"]["event_ids"]
+            ids = tuple(event["world_id"] for event in events)
+            require(ids == tuple(world for world in binding["world_ids"] if world in ids), "shared receipt original group order")
+            for event in events:
+                other = records[event["world_id"]]["cursor"]
+                require(
+                    event["world_episode_seq"] == other["accepted_episode_seq"] and 1 <= event["eligible_seq"] <= other["eligible_seq"],
+                    "shared grouped event cursor",
+                )
+        if "reward" in cache and cache["reward"]["event_id"]["eligible_seq"] == cursor["eligible_seq"] + 1:
+            step = state["step"]
+            require(mode == "live_episode" and step is not None and not step["serviced"], "unserviced reward needs live reservation")
+            index = step["original_binding"]["world_ids"].index(record["world_id"])
+            require(
+                bool(step["active"][index]) and same(step["stamp"]["event_ids"][index], cache["reward"]["event_id"]),
+                "unserviced local reward reservation",
+            )
+
+
+def clone_provider(provider: Any, *, family: str) -> Any:
+    memo = {}
+    if family in ("count_based", "icm"):
+        policy = provider.policy
+        memo[id(policy)] = ResolvedExplorationPolicy.from_dict(policy.to_dict())
+    return deepcopy(provider, memo)
+
+
+def validate_native(provider: Any, payload: Any, *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor) -> None:
+    family = policy.strategy
+    if family == "none":
+        keys(payload, {"epsilon", "epsilon_decay", "epsilon_min"}, "epsilon native")
+        for name in payload:
+            number(payload[name], name)
+        require(
+            payload["epsilon_decay"] == policy.epsilon_decay and payload["epsilon_min"] == policy.epsilon_end, "epsilon policy schedule"
+        )
+        require(policy.epsilon_end <= payload["epsilon"] <= policy.epsilon_start, "epsilon selected bounds")
+    elif family == "count_based":
+        for key in payload["counts"]:
+            require(type(key) is tuple and len(key) == descriptor.observation_dim, "Count bin bank geometry")
+        for key in payload["lru"]:
+            require(type(key) is tuple and len(key) == descriptor.observation_dim, "Count LRU bank geometry")
+        disposable = clone_provider(provider, family=family)
+        disposable.load_state(owned(payload))
+    else:
+        require(provider.validate_state(payload) is None, "native validator return")
+
+
+def gradient_modules(provider: Any, family: str) -> dict[str, Any]:
+    if family == "rnd":
+        require(all(parameter.grad is None for parameter in provider.fixed_network.parameters()), "fixed target gradient is not lawful")
+        return {"predictor_network": provider.predictor_network}
+    if family == "adaptive_rnd":
+        require(all(parameter.grad is None for parameter in provider.rnd.fixed_network.parameters()), "fixed target gradient is not lawful")
+        return {"rnd.predictor_network": provider.rnd.predictor_network}
+    if family == "icm":
+        return dict(encoder=provider.encoder, inverse_model=provider.inverse_model, forward_model=provider.forward_model)
+    return {}
+
+
+def check_pairing(provider: Any, family: str, modules: dict[str, Any]) -> None:
+    if not modules:
+        return
+    if family == "adaptive_rnd":
+        adam = provider.rnd.optimizer
+    else:
+        adam = provider.optimizer
+    parameters = [parameter for module in modules.values() for parameter in module.parameters()]
+    ids = [id(parameter) for parameter in parameters]
+    grouped = [id(parameter) for group in adam.param_groups for parameter in group["params"]]
+    require(len(set(ids)) == len(ids) and len(grouped) == len(ids) and set(grouped) == set(ids), "actual Adam/Parameter pairing")
+    require({id(parameter) for parameter in adam.state}.issubset(set(ids)), "Adam state pairing")
+
+
+def capture_gradients(provider: Any, family: str) -> dict[str, Any]:
+    modules = gradient_modules(provider, family)
+    check_pairing(provider, family, modules)
+    result = {}
+    for label, module in modules.items():
+        parameters = dict(module.named_parameters())
+        values = {}
+        for name, parameter in parameters.items():
+            gradient = parameter.grad
+            if gradient is not None:
+                tensor(gradient, tuple(parameter.shape), parameter.dtype, parameter.device, "live gradient")
+                gradient = gradient.detach().clone()
+            values[name] = gradient
+        result[label] = values
+    return result
+
+
+def attach_gradients(provider: Any, values: Any, family: str) -> None:
+    modules = gradient_modules(provider, family)
+    check_pairing(provider, family, modules)
+    keys(values, set(modules), "gradient modules")
+    prepared = []
+    for label, module in modules.items():
+        parameters = dict(module.named_parameters())
+        keys(values[label], set(parameters), "gradient parameter names")
+        for name, parameter in parameters.items():
+            gradient = values[label][name]
+            if gradient is not None:
+                tensor(gradient, tuple(parameter.shape), parameter.dtype, parameter.device, "saved gradient")
+                gradient = gradient.detach().clone()
+            prepared.append((parameter, gradient))
+    for parameter, gradient in prepared:
+        parameter.grad = gradient
+
+
+def _allocate_runtime_data(*, section: str, value: Any) -> Any:
+    """Actual late ownership allocation; returned values feed installed runtime."""
+    require(section in ("cache", "receipt", "outcome"), "runtime allocation section")
+    return owned(value)
+
+
+def decode_cache(values: dict[str, Any], *, descriptor: WorldCuriosityDescriptor) -> dict[str, Any]:
+    result = {}
+    for world, cache in values.items():
+        phases = {}
+        for phase, entry in cache.items():
+            item = dict(entry)
+            if phase in ("reward", "service"):
+                item["event_id"] = event_value(entry["event_id"])
+            if phase == "service":
+                item["receipt"] = receipt_value(entry["receipt"], descriptor=descriptor)
+            phases[phase] = item
+        result[world] = phases
+    return result
+
+
+def project_step(step: dict[str, Any], *, order: tuple[str, ...]) -> dict[str, Any]:
+    """Only live private current work changes row order; local provenance stays."""
+    source = step["original_binding"]["world_ids"]
+    indexes = [source.index(world) for world in order]
+    result = dict(step)
+    binding = step["original_binding"]
+    result["original_binding"] = dict(
+        binding, world_ids=list(order), world_episode_seqs=[binding["world_episode_seqs"][i] for i in indexes]
+    )
+    stamp = step["stamp"]
+    result["stamp"] = dict(
+        event_ids=tuple(stamp["event_ids"][i] for i in indexes),
+        world_ids=order,
+        world_episode_seqs=stamp["world_episode_seqs"][indexes],
+        eligible_seqs=stamp["eligible_seqs"][indexes],
+        eligible=stamp["eligible"][indexes],
+    )
+    result["active"] = step["active"][indexes]
+    if step["context"] is not None:
+        result["context"] = {"vector_tick": step["context"]["vector_tick"]}
+        for key in CONTENT - {"vector_tick"}:
+            result["context"][key] = step["context"][key][indexes]
+    if step["reward"] is not None:
+        reward = step["reward"]
+        result["reward"] = dict(
+            reward,
+            raw=reward["raw"][indexes],
+            scales=reward["scales"][indexes],
+            eligible=reward["eligible"][indexes],
+            event_ids=result["stamp"]["event_ids"],
+        )
+    if step["receipts"] is not None:
+        result["receipts"] = tuple(step["receipts"][i] for i in indexes)
+    return result
+
+
+def decode_step(step: dict[str, Any], *, descriptor: WorldCuriosityDescriptor, device: torch.device) -> dict[str, Any]:
+    from townlet.exploration.scoped_curiosity import CuriosityReward
+
+    result = dict(step)
+    result.pop("original_binding")
+    result["stamp"] = stamp_value(step["stamp"], device=device)
+    if step["reward"] is not None:
+        reward = step["reward"]
+        result["reward"] = CuriosityReward(reward["raw"], reward["scales"], reward["eligible"], result["stamp"].event_ids, reward["scope"])
+    if step["receipts"] is not None:
+        result["receipts"] = tuple(receipt_value(value, descriptor=descriptor) for value in step["receipts"])
+    return result
+
+
+def runtime_data(state: dict[str, Any], *, descriptor: WorldCuriosityDescriptor, device: torch.device) -> dict[str, Any]:
+    caches = _allocate_runtime_data(section="cache", value={record["world_id"]: record["phase_cache"] for record in state["worlds"]})
+    history, historical_step, pending = None, None, None
+    step = state["step"]
+    receipts = None
+    if step is not None and step["receipts"] is not None:
+        receipts = _allocate_runtime_data(section="receipt", value=step["receipts"])
+    if state["bank_phase"] == "completed_boundary":
+        history = dict(state["completion"])
+        outcomes = _allocate_runtime_data(section="outcome", value=history["outcomes"])
+        # Keep complete owned historical codecs; no live receipt or outcome effect.
+        history["outcomes"] = outcomes
+        for value in outcomes:
+            lane_outcome_from_state(value)
+        if step is not None:
+            historical_step = dict(step, receipts=receipts)
+    elif step is not None:
+        projected = dict(step, receipts=receipts)
+        if descriptor.scope == "per_world":
+            projected = project_step(projected, order=descriptor.world_ids)
+        pending = decode_step(projected, descriptor=descriptor, device=device)
+    return dict(
+        cursor={record["world_id"]: owned(record["cursor"]) for record in state["worlds"]},
+        cache=decode_cache(caches, descriptor=descriptor),
+        pending=pending,
+        history=history,
+        historical_step=historical_step,
+    )
diff --git a/src/townlet/exploration/scoped_curiosity.py b/src/townlet/exploration/scoped_curiosity.py
index 87406664..b26f177f 100644
--- a/src/townlet/exploration/scoped_curiosity.py
+++ b/src/townlet/exploration/scoped_curiosity.py
@@ -1,21 +1,21 @@
 """Exact-ID curiosity ownership; ENV supplies identity, BANK owns local phases.
 
 Snapshots are owned diagnostic values, not a parent restore format. Global
 completion capabilities remain live and never enter world-local snapshots.
 """
 
 from __future__ import annotations
 
 from collections.abc import Callable, Mapping
 from copy import copy, deepcopy
-from dataclasses import dataclass
+from dataclasses import dataclass, replace
 from functools import partial, wraps
 from threading import RLock
 from typing import Any, Protocol, cast
 
 import torch
 
 from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy
 from townlet.config.world_roster import WorldAcceptedEpisode, WorldOwnerReceipt
 from townlet.exploration.provider_factory import make_backend
 from townlet.exploration.world_curiosity_state import (
@@ -285,20 +285,23 @@ class CuriosityBank:
         self._completion_payload: dict[str, Any] = {}
         self._completion_outcomes: tuple[LaneOutcome, ...] = ()
         self._completion_values: dict[str, tuple[list[float], float]] = {}
         self._failed = False
         self._quarantine: tuple[WorldAcceptedEpisode, str] | None = None
         self._accepted: WorldAcceptedEpisode | None = None
         self._activation: WorldOwnerReceipt | None = None
         self._pending: dict[str, Any] | None = None
         self._prepared: PreparedBankCompletion | None = None
         self._committed: tuple[PreparedBankCompletion, WorldOwnerReceipt] | None = None
+        self._history: dict[str, Any] | None = None
+        self._historical_step: dict[str, Any] | None = None
+        self._restore_tokens: dict[object, Any] = {}
         self._owners: dict[str, OwnedWorldBackend] = {}
         self._shared: Any = None
         self._cursor: dict[str, dict[str, Any]] = {
             world: dict(accepted_episode_seq=0, eligible_seq=0, cumulative_service_position=0, participated=False, disposition=None)
             for world in ids
         }
         self._cache: dict[str, dict[str, Any]] = {world: {} for world in ids}
         self._estimate = self._allocation("construct", 0, 0)
         self._report(self._estimate)
         devices: tuple[int, ...]
@@ -368,20 +371,22 @@ class CuriosityBank:
         _require(self._pending is None or self._pending["serviced"], "unfinished step")
         for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
             cursor = self._cursor[world]
             _require(type(episode) is int and episode == cursor["accepted_episode_seq"] + 1, "accepted episode must advance once")
             _require(cursor["accepted_episode_seq"] == 0 or cursor["disposition"] is not None, "unfinished accepted episode")
         receipt = self._issuer.issue(kind="activation", payload={"accepted": accepted})
         for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
             self._cursor[world].update(accepted_episode_seq=episode, eligible_seq=0, participated=False, disposition=None)
             self._cache[world] = {}
         self._accepted, self._activation, self._pending, self._committed = accepted, receipt, None, None
+        self._history, self._historical_step = None, None
+        self._completion_payload, self._completion_outcomes, self._completion_values = {}, (), {}
         self.mutation_revision += 1
         return receipt
 
     @_serialized
     def prepare_step_stamp(
         self, *, accepted: WorldAcceptedEpisode, world_ids: tuple[str, ...], active_on_entry: torch.Tensor, vector_tick: int
     ) -> CuriosityStepStamp:
         self._available()
         self._auth(accepted)
         _require(world_ids == accepted.world_ids, "row binding mismatch")
@@ -891,11 +896,219 @@ class CuriosityBank:
             scope=self.scope,
             world_id=world_id,
             policy_identity=self.policy.policy_identity,
             descriptor=self.descriptor.to_dict(),
             backend=backend,
             curiosity_epoch=0,
             accepted_identity=identity,
             cursor=deepcopy(self._cursor[world_id]),
             phase_cache=deepcopy(self._cache[world_id]),
             pending_step=pending,
+            bank_phase=self._checkpoint_phase(),
+            historical_identity=self._historical_identity(),
         )
+
+    def _checkpoint_phase(self) -> str:
+        if self._history is not None or self._committed is not None:
+            return "completed_boundary"
+        if self._accepted is not None:
+            return "live_episode"
+        return "initial"
+
+    def _historical_identity(self) -> dict[str, Any] | None:
+        from townlet.exploration import curiosity_checkpoint as checkpoint
+
+        if self._history is not None:
+            return cast(dict[str, Any], deepcopy(self._history["original_accepted_identity"]))
+        if self._committed is not None:
+            return checkpoint.accepted_identity(self._committed[0].accepted)
+        return None
+
+    @_serialized
+    @_observation_boundary
+    def checkpoint_state(self) -> dict[str, Any]:
+        """Owned current transport; historical completion never transports authority."""
+        from townlet.exploration import curiosity_checkpoint as checkpoint
+
+        self._available()
+        phase = self._checkpoint_phase()
+        worlds = []
+        shared = None
+        try:
+            if self.scope == "shared":
+                self._observations += 1
+                shared = dict(
+                    native=checkpoint.owned(self._shared.checkpoint_state()),
+                    gradients=checkpoint.capture_gradients(self._shared, self.policy.strategy),
+                )
+            for world in self.world_ids:
+                backend = gradients = None
+                if self.scope == "per_world":
+                    self._observations += 1
+                    gradients = self._owners[world].call(
+                        lambda provider, sources: checkpoint.capture_gradients(provider, self.policy.strategy)
+                    )
+                    backend = self._owners[world].snapshot()
+                worlds.append(
+                    dict(
+                        world_id=world,
+                        backend=backend,
+                        gradients=gradients,
+                        cursor=deepcopy(self._cursor[world]),
+                        phase_cache=checkpoint.encode_cache(self._cache[world]),
+                    )
+                )
+            completion = deepcopy(self._history)
+            if self._committed is not None:
+                payload = self._completion_payload
+                completion = dict(
+                    status="committed",
+                    original_accepted_identity=checkpoint.accepted_identity(self._committed[0].accepted),
+                    boundary_key=payload["boundary_key"],
+                    completion_content=deepcopy(payload["completion_content"]),
+                    participated_world_ids=payload["participated_world_ids"],
+                    dispositions=payload["dispositions"],
+                    outcomes=tuple(lane_outcome_state(event) for event in self._completion_outcomes),
+                )
+            step = deepcopy(self._historical_step)
+            if self._pending is not None:
+                assert self._accepted is not None
+                step = checkpoint.encode_step(self._pending, checkpoint.accepted_identity(self._accepted))
+            dispatch = None
+            if phase == "live_episode":
+                assert self._accepted is not None
+                dispatch = checkpoint.accepted_identity(self._accepted)
+            return dict(
+                schema="curiosity-bank-state-v1",
+                policy=self.policy.to_dict(),
+                policy_identity=self.policy.policy_identity,
+                descriptor=self.descriptor.to_dict(),
+                source_device=str(self.device),
+                curiosity_epoch=0,
+                bank_phase=phase,
+                dispatch_identity=dispatch,
+                worlds=worlds,
+                shared_backend=shared,
+                step=step,
+                completion=completion,
+            )
+        finally:
+            self.mutation_revision += 1
+
+    @_serialized
+    def prepare_restore(
+        self,
+        *,
+        state: Any,
+        mode: str,
+        accepted: WorldAcceptedEpisode | None,
+        parent_restore: Any,
+        validate_parent_restore: Any,
+    ) -> Any:
+        """Prepare every owner and runtime value without observing live owners."""
+        from townlet.exploration import curiosity_checkpoint as checkpoint
+
+        _require(self._prepared is None, "completion transaction pending")
+        revision = self.mutation_revision
+        checkpoint.preflight(state, policy=self.policy, descriptor=self.descriptor, device=self.device, mode=mode)
+        checkpoint.check_mode(mode=mode, accepted=accepted, parent=parent_restore, validate=validate_parent_restore)
+        size = checkpoint.tensor_bytes(state)
+        reserve = self._allocation("restore", len(self.world_ids), 0)
+        components = reserve.components + (("owned_input_candidate_workspace", 5 * size),)
+        self._report(
+            replace(
+                reserve,
+                known_tensor_bytes=sum(value for _, value in components),
+                components=components,
+                assumptions=reserve.assumptions
+                + (
+                    "old resident plus new owners, gradients/Adam/tails, owned transport and sequential validation workspace",
+                    "five input tensor inventories reserve transport, gradients, RNG, caches, outcomes and transient copies",
+                ),
+            )
+        )
+        saved = checkpoint.owned(state)
+
+        def correlate() -> None:
+            if mode == "live_episode":
+                assert accepted is not None
+                self._validate(accepted=accepted)
+                checkpoint.match_live(saved, accepted=accepted, descriptor=self.descriptor)
+            elif parent_restore is not None:
+                checkpoint.match_parent(saved, parent=parent_restore, descriptor=self.descriptor)
+                before = checkpoint.owned(saved)
+                _require(validate_parent_restore(prepared=parent_restore, curiosity_state=saved) is None, "parent validator return")
+                _require(checkpoint.same(saved, before), "parent callback changed curiosity state")
+
+        correlate()
+        checkpoint.validate_records(saved, policy=self.policy, descriptor=self.descriptor, device=self.device)
+        owners: dict[str, OwnedWorldBackend] = {}
+        shared = None
+        devices: tuple[int, ...] = ()
+        if self.device.type == "cuda":
+            devices = (cast(int, self.device.index),)
+        records = {item["world_id"]: item for item in saved["worlds"]}
+        validator = partial(checkpoint.validate_native, policy=self.policy, descriptor=self.descriptor)
+        if self.scope == "per_world":
+            for world in sorted(self.world_ids):
+                rng = WorldRNGState.create(descriptor=self.descriptor, world_id=world, cuda_devices=devices)
+                factory = partial(self._factory, world)
+                owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
+                native = owner.prepare_restore(records[world]["backend"], factory=factory, validate_backend=validator)
+                owner.install(native)
+                owner.call(
+                    lambda provider, sources: checkpoint.attach_gradients(provider, records[world]["gradients"], self.policy.strategy)
+                )
+                owners[world] = owner
+        else:
+            shared = checkpoint.clone_provider(self._shared, family=self.policy.strategy)
+            payload = saved["shared_backend"]
+            validator(shared, payload["native"])
+            shared.load_state(checkpoint.owned(payload["native"]))
+            _require(checkpoint.same(shared.checkpoint_state(), payload["native"]), "shared native transport changed")
+            checkpoint.attach_gradients(shared, payload["gradients"], self.policy.strategy)
+        runtime_values = checkpoint.runtime_data(saved, descriptor=self.descriptor, device=self.device)
+        activation = None
+        if mode == "live_episode":
+            activation = self._issuer.issue(kind="activation", payload={"accepted": accepted})
+        token = checkpoint.PreparedCuriosityRestore()
+        runtime = dict(self.__dict__)
+        runtime.update(
+            _owners=owners,
+            _shared=shared,
+            _cursor=runtime_values["cursor"],
+            _cache=runtime_values["cache"],
+            _pending=runtime_values["pending"],
+            _history=runtime_values["history"],
+            _historical_step=runtime_values["historical_step"],
+            _accepted=accepted,
+            _activation=activation,
+            _prepared=None,
+            _committed=None,
+            _failed=False,
+            _quarantine=None,
+            _completion_payload={},
+            _completion_outcomes=(),
+            _completion_values={},
+            _restore_tokens={},
+            mutation_revision=revision + 1,
+        )
+        correlate()
+        _require(self.mutation_revision == revision, "destination changed during restore preparation")
+        self._restore_tokens[token] = (revision, runtime, accepted)
+        return token
+
+    @_serialized
+    def install_restore(self, *, prepared: Any) -> None:
+        from townlet.exploration.curiosity_checkpoint import PreparedCuriosityRestore
+
+        _require(type(prepared) is PreparedCuriosityRestore and prepared in self._restore_tokens, "foreign or consumed restore token")
+        revision, runtime, accepted = self._restore_tokens[prepared]
+        _require(revision == self.mutation_revision and self._prepared is None, "stale restore token")
+        if accepted is not None:
+            self._validate(accepted=accepted)
+        _require(revision == self.mutation_revision, "destination changed during final authentication")
+        try:
+            self.__dict__ = runtime
+        except BaseException:
+            self._failed = True
+            raise
