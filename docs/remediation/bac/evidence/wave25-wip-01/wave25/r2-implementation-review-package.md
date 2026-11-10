# PW05 actual BANK candidate review
Base 6f451471c2fa865633dd93658991b2253fb68a10
Candidate fee0eac4e8e3944296fa4e22a8ad9f4a8f17f684
Full five-source inventory in wave25/r2-candidate.json. Teststrength delta included for context; exactT2reviewapproved.

 src/townlet/exploration/scoped_curiosity.py        | 717 +++++++++++++++++++++
 .../regressions/bac/test_pw_private_bank.py        | 260 +++++++-
 2 files changed, 973 insertions(+), 4 deletions(-)
diff --git a/src/townlet/exploration/scoped_curiosity.py b/src/townlet/exploration/scoped_curiosity.py
new file mode 100644
index 00000000..6ad68caa
--- /dev/null
+++ b/src/townlet/exploration/scoped_curiosity.py
@@ -0,0 +1,717 @@
+"""Exact-ID curiosity ownership; ENV supplies identity, BANK owns local phases.
+
+Snapshots are owned diagnostic values, not a parent restore format. Global
+completion capabilities remain live and never enter world-local snapshots.
+"""
+
+from __future__ import annotations
+
+from collections.abc import Callable, Mapping
+from copy import copy, deepcopy
+from dataclasses import dataclass
+from functools import partial, wraps
+from threading import RLock
+from typing import Any, Protocol, cast
+
+import torch
+
+from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy
+from townlet.config.world_roster import WorldAcceptedEpisode, WorldOwnerReceipt
+from townlet.exploration.provider_factory import make_backend
+from townlet.exploration.world_curiosity_state import (
+    CuriosityEventId,
+    CuriosityStepStamp,
+    OwnedWorldBackend,
+    ServiceClock,
+    WorldCuriosityDescriptor,
+    WorldRNGState,
+)
+from townlet.training.episode import LaneOutcome, freeze_lane_outcome, lane_outcome_state
+
+
+class AcceptedEpisodeValidator(Protocol):
+    def __call__(self, *, accepted: WorldAcceptedEpisode) -> None: ...
+
+
+class ReceiptIssuer(Protocol):
+    @property
+    def owner(self) -> object: ...
+
+    def issue(self, *, kind: str, payload: Mapping[str, Any]) -> WorldOwnerReceipt: ...
+
+
+@dataclass(frozen=True)
+class AllocationEstimate:
+    schema: str
+    operation: str
+    scope: str
+    device: str
+    model_dtype: str
+    observation_dtype: str
+    world_count: int
+    participant_count: int
+    instance_count: int
+    known_tensor_bytes: int
+    components: tuple[tuple[str, int], ...]
+    assumptions: tuple[str, ...]
+    unknown_components: tuple[str, ...]
+
+
+@dataclass(frozen=True)
+class WorldServiceReceipt:
+    scope: str
+    world_id: str | None
+    event_ids: tuple[CuriosityEventId, ...]
+    eligible: bool
+    clock: ServiceClock | None
+    admitted_rows: int
+    consumed_rows: int
+    dropped_rows: int
+    pending_rows: int
+    optimizer_updates: int
+    mandatory_service_updates: int
+    last_loss: float
+
+
+class CuriosityReward:
+    def __init__(
+        self, raw: torch.Tensor, scales: torch.Tensor, eligible: torch.Tensor, event_ids: tuple[CuriosityEventId, ...], scope: str
+    ):
+        self._raw, self._scales, self._eligible = (value.detach().clone() for value in (raw, scales, eligible))
+        self.event_ids, self.scope = event_ids, scope
+
+    @property
+    def raw(self) -> torch.Tensor:
+        return self._raw.clone()
+
+    @property
+    def scales(self) -> torch.Tensor:
+        return self._scales.clone()
+
+    @property
+    def eligible(self) -> torch.Tensor:
+        return self._eligible.clone()
+
+
+@dataclass
+class PreparedBankCompletion:
+    destination: object
+    revision: int
+    accepted: WorldAcceptedEpisode
+    boundary_key: int
+    completion_content: Any
+    participated_world_ids: tuple[str, ...]
+    dispositions: tuple[tuple[str, str], ...]
+    values: dict[str, tuple[list[float], float]]
+    prepared_receipt: WorldOwnerReceipt
+    used: bool
+
+
+def _same(left: Any, right: Any) -> bool:
+    if type(left) is not type(right):
+        return False
+    if isinstance(left, torch.Tensor):
+        return left.shape == right.shape and left.dtype == right.dtype and left.device == right.device and torch.equal(left, right)
+    if isinstance(left, dict):
+        return left.keys() == right.keys() and all(_same(left[key], right[key]) for key in left)
+    if isinstance(left, (tuple, list)):
+        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right, strict=True))
+    return bool(left == right)
+
+
+def _require(condition: bool, message: str) -> None:
+    if not condition:
+        raise ValueError(message)
+
+
+def _serialized(method: Callable[..., Any]) -> Callable[..., Any]:
+    @wraps(method)
+    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
+        with self._lock:
+            return method(self, *args, **kwargs)
+
+    return invoke
+
+
+def _allocation_estimate(
+    policy: ResolvedExplorationPolicy,
+    descriptor: WorldCuriosityDescriptor,
+    device: torch.device,
+    operation: str,
+    participants: int,
+    outcome_bytes: int,
+) -> AllocationEstimate:
+    d, a = descriptor.observation_dim, descriptor.action_dim
+    k = len(descriptor.world_ids) if policy.curiosity_scope == "per_world" else 1
+    model = gradients = queue = 0
+    if policy.strategy in ("rnd", "adaptive_rnd"):
+        e = policy.rnd_feature_dim
+        p = d * 256 + 256 + 256 * 128 + 128 + 128 * e + e
+        model, gradients, queue = 8 * p, 12 * p + 24, 4 * d * policy.max_pending_rows
+    elif policy.strategy == "icm":
+        h, f = policy.provider_parameters["hidden_dim"], policy.provider_parameters["feature_dim"]
+        p = sum(x * y + y for x, y in ((d, h), (h, f), (2 * f, h), (h, a), (f + a, h), (h, f)))
+        model, gradients, queue = 4 * p, 12 * p + 48, policy.max_pending_rows * (8 * d + 8)
+    components: tuple[tuple[str, int], ...] = (
+        ("eager_model_copy_peak", (k + 1) * model + k * queue),
+        ("trained_reserve", k * (model + gradients + queue)),
+    )
+    if operation == "complete":
+        history = 16 * (policy.survival_window + 1) if policy.strategy == "adaptive_rnd" else 0
+        components = (("outcome_transport", 2 * outcome_bytes), ("history_workspace", history), ("model_copies", 0))
+    return AllocationEstimate(
+        "curiosity-allocation-estimate-v1",
+        operation,
+        policy.curiosity_scope,
+        str(device),
+        str(torch.float32),
+        str(torch.float32),
+        len(descriptor.world_ids),
+        participants,
+        k,
+        max(value for _, value in components) if operation == "construct" else sum(value for _, value in components),
+        components,
+        (
+            "float32 models; lazy Adam and gradients reserved",
+            "sequential completion candidates; retained Python histories <= participants*window",
+        ),
+        ("Python containers/count integer keys", "RNG tensors", "allocator/activation/library workspace"),
+    )
+
+
+def allocation_estimate(
+    *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, device: torch.device | str
+) -> AllocationEstimate:
+    """Pure known-tensor estimate; unknown resident/workspace costs stay labeled."""
+    return _allocation_estimate(policy, descriptor, torch.device(device), "construct", 0, 0)
+
+
+class CuriosityBank:
+    def __init__(
+        self,
+        *,
+        policy: ResolvedExplorationPolicy,
+        descriptor: WorldCuriosityDescriptor,
+        device: torch.device | str,
+        validate_accepted_episode: AcceptedEpisodeValidator,
+        issuer_factory: Callable[[object], ReceiptIssuer],
+        report_allocation: Callable[[AllocationEstimate], None],
+    ):
+        _require(isinstance(policy, ResolvedExplorationPolicy), "actual resolved policy required")
+        self._lock = RLock()
+        self.policy = ResolvedExplorationPolicy.from_dict(policy.to_dict())
+        self.descriptor = WorldCuriosityDescriptor.from_dict(descriptor.to_dict())
+        ids = self.descriptor.world_ids
+        _require(
+            bool(ids) and len(set(ids)) == len(ids) and all(type(world) is str and bool(world) for world in ids),
+            "exact declared IDs required",
+        )
+        expected = WorldCuriosityDescriptor.from_policy(
+            self.policy,
+            world_ids=ids,
+            observation_dim=descriptor.observation_dim,
+            action_dim=descriptor.action_dim,
+            training_seed=descriptor.training_seed,
+        )
+        _require(expected.to_dict() == self.descriptor.to_dict(), "policy/descriptor mismatch")
+        self.device = torch.device(device)
+        _require(
+            self.device.type in ("cpu", "cuda") and (self.device.type != "cuda" or self.device.index is not None),
+            "explicit CPU/CUDA device required",
+        )
+        _require(torch.get_default_dtype() == torch.float32, "bank requires declared float32 model profile")
+        _require(self.policy.strategy == "none" or descriptor.observation_dim > 0, "selected provider requires positive width")
+        _require(
+            callable(validate_accepted_episode) and callable(issuer_factory) and callable(report_allocation), "required owner callbacks"
+        )
+        self._validate, self._report = validate_accepted_episode, report_allocation
+        self._issuer = issuer_factory(self)
+        _require(self._issuer.owner is self, "issuer must belong to actual bank")
+        self.scope, self.world_ids = self.policy.curiosity_scope, ids
+        self.mutation_revision = 0
+        self._failed = False
+        self._quarantine: tuple[WorldAcceptedEpisode, str] | None = None
+        self._accepted: WorldAcceptedEpisode | None = None
+        self._activation: WorldOwnerReceipt | None = None
+        self._pending: dict[str, Any] | None = None
+        self._prepared: PreparedBankCompletion | None = None
+        self._committed: tuple[PreparedBankCompletion, WorldOwnerReceipt] | None = None
+        self._owners: dict[str, OwnedWorldBackend] = {}
+        self._shared: Any = None
+        self._cursor: dict[str, dict[str, Any]] = {
+            world: dict(accepted_episode_seq=0, eligible_seq=0, cumulative_service_position=0, participated=False, disposition=None)
+            for world in ids
+        }
+        self._cache: dict[str, dict[str, Any]] = {world: {} for world in ids}
+        self._estimate = self._allocation("construct", 0, 0)
+        self._report(self._estimate)
+        devices = () if self.device.type == "cpu" else (self.device.index,)
+        for world in sorted(ids) if self.scope == "per_world" else ():
+            rng = WorldRNGState.create(descriptor=self.descriptor, world_id=world, cuda_devices=devices)
+            self._owners[world] = OwnedWorldBackend.construct(rng=rng, factory=partial(self._factory, world))
+        if self.scope == "shared":
+            self._shared = self._factory(None, None)
+
+    def _factory(self, world: str | None, rng: WorldRNGState | None) -> Any:
+        return make_backend(
+            self.policy,
+            world_id=world,
+            obs_dim=self.descriptor.observation_dim,
+            action_dim=self.descriptor.action_dim,
+            device=self.device,
+            rng=rng,
+            descriptor=self.descriptor if world is not None else None,
+        )
+
+    def _allocation(self, operation: str, participants: int, outcome_bytes: int) -> AllocationEstimate:
+        return _allocation_estimate(self.policy, self.descriptor, self.device, operation, participants, outcome_bytes)
+
+    def _healthy(self) -> None:
+        if self._failed:
+            raise RuntimeError("curiosity bank quarantined")
+
+    def _auth(self, accepted: WorldAcceptedEpisode) -> None:
+        self._validate(accepted=accepted)
+        _require(accepted is self._accepted, "bank accepted identity mismatch")
+
+    def _available(self) -> None:
+        self._healthy()
+        _require(self._prepared is None, "completion transaction pending")
+
+    def _call(self, world: str, operation: Callable[[Any], Any]) -> Any:
+        try:
+            if self.scope == "per_world":
+                return self._owners[world].call(lambda backend, sources: operation(backend))
+            return operation(self._shared)
+        except BaseException:
+            self._failed = True
+            raise
+
+    @_serialized
+    def begin_episode(self, *, accepted: WorldAcceptedEpisode) -> WorldOwnerReceipt:
+        self._available()
+        self._validate(accepted=accepted)
+        if accepted is self._accepted:
+            assert self._activation is not None
+            return self._activation
+        _require(
+            set(accepted.world_ids) == set(self.world_ids) and len(accepted.world_ids) == len(self.world_ids),
+            "accepted declaration mismatch",
+        )
+        _require(self._pending is None or self._pending["serviced"], "unfinished step")
+        for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
+            cursor = self._cursor[world]
+            _require(type(episode) is int and episode == cursor["accepted_episode_seq"] + 1, "accepted episode must advance once")
+            _require(cursor["accepted_episode_seq"] == 0 or cursor["disposition"] is not None, "unfinished accepted episode")
+        receipt = self._issuer.issue(kind="activation", payload={"accepted": accepted})
+        for world, episode in zip(accepted.world_ids, accepted.world_episode_seqs, strict=True):
+            self._cursor[world].update(accepted_episode_seq=episode, eligible_seq=0, participated=False, disposition=None)
+            self._cache[world] = {}
+        self._accepted, self._activation, self._pending, self._committed = accepted, receipt, None, None
+        self.mutation_revision += 1
+        return receipt
+
+    @_serialized
+    def prepare_step_stamp(
+        self, *, accepted: WorldAcceptedEpisode, world_ids: tuple[str, ...], active_on_entry: torch.Tensor, vector_tick: int
+    ) -> CuriosityStepStamp:
+        self._available()
+        self._auth(accepted)
+        _require(world_ids == accepted.world_ids, "row binding mismatch")
+        _require(type(vector_tick) is int and vector_tick >= 0, "invalid vector tick")
+        _require(
+            isinstance(active_on_entry, torch.Tensor)
+            and active_on_entry.shape == (len(world_ids),)
+            and active_on_entry.dtype == torch.bool
+            and active_on_entry.layout == torch.strided
+            and active_on_entry.device == self.device,
+            "eligibility geometry mismatch",
+        )
+        _require(all(self._cursor[world]["disposition"] is None for world in world_ids), "episode disposed")
+        if self._pending is not None:
+            pending = self._pending
+            if pending["tick"] == vector_tick and _same(pending["active"], active_on_entry):
+                return cast(CuriosityStepStamp, pending["stamp"])
+            _require(pending["serviced"] and vector_tick > pending["tick"], "unfinished or regressing preparation")
+        sequences = tuple(self._cursor[world]["eligible_seq"] + int(active_on_entry[i]) for i, world in enumerate(world_ids))
+        events = tuple(
+            CuriosityEventId(0, world, episode, seq)
+            for world, episode, seq in zip(world_ids, accepted.world_episode_seqs, sequences, strict=True)
+        )
+        stamp = CuriosityStepStamp(
+            event_ids=events,
+            world_ids=world_ids,
+            world_episode_seqs=torch.tensor(accepted.world_episode_seqs, dtype=torch.int64, device=self.device),
+            eligible_seqs=torch.tensor(sequences, dtype=torch.int64, device=self.device),
+            eligible=active_on_entry,
+        )
+        self._pending = dict(
+            stamp=stamp,
+            tick=vector_tick,
+            active=active_on_entry.clone(),
+            context=None,
+            update_stats=None,
+            reward=None,
+            receipts=None,
+            serviced=False,
+        )
+        self.mutation_revision += 1
+        return stamp
+
+    def _context(self, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode) -> dict[str, Any]:
+        self._available()
+        self._auth(accepted)
+        _require(isinstance(context, IntrinsicTransitionContext) and isinstance(stamp, CuriosityStepStamp), "actual context/stamp required")
+        pending = self._pending
+        _require(pending is not None, "missing reservation")
+        assert pending is not None
+        expected = pending["stamp"]
+        _require(
+            stamp.world_ids == expected.world_ids and stamp.event_ids == expected.event_ids and _same(stamp.eligible, expected.eligible),
+            "stamp reservation mismatch",
+        )
+        _require(
+            context.vector_tick == pending["tick"] and _same(context.active_on_entry, pending["active"]), "context provenance mismatch"
+        )
+        predecessor, successor, actions = context.predecessor, context.successor, context.actions
+        _require(predecessor.shape == (len(self.world_ids), self.descriptor.observation_dim), "provider observation width mismatch")
+        _require(
+            predecessor.dtype == successor.dtype == torch.float32 and predecessor.device == self.device,
+            "selected observation profile mismatch",
+        )
+        _require(bool(((actions >= 0) & (actions < self.descriptor.action_dim)).all()), "action bounds mismatch")
+        content = dict(
+            predecessor=predecessor, successor=successor, actions=actions, active=context.active_on_entry, vector_tick=context.vector_tick
+        )
+        if pending["context"] is not None:
+            _require(_same(content, pending["context"]), "changed event content")
+        return content
+
+    def _row_context(self, content: dict[str, Any], indexes: list[int]) -> IntrinsicTransitionContext:
+        return IntrinsicTransitionContext(
+            predecessor=content["predecessor"][indexes],
+            actions=content["actions"][indexes],
+            successor=content["successor"][indexes],
+            active_on_entry=content["active"][indexes],
+            vector_tick=content["vector_tick"],
+        )
+
+    def _local_content(self, content: dict[str, Any], index: int) -> dict[str, Any]:
+        return {key: value if key == "vector_tick" else value[index].clone() for key, value in content.items()}
+
+    @_serialized
+    def reward(
+        self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode, update_stats: bool
+    ) -> CuriosityReward:
+        content = self._context(context, stamp, accepted)
+        _require(type(update_stats) is bool, "update_stats must be bool")
+        pending = self._pending
+        assert pending is not None
+        if pending["reward"] is not None:
+            _require(update_stats == pending["update_stats"], "changed reward mode")
+            return cast(CuriosityReward, deepcopy(pending["reward"]))
+        raw = torch.zeros(len(self.world_ids), device=self.device)
+        scales = torch.zeros_like(raw)
+        indexes = content["active"].nonzero().flatten().tolist()
+        groups = [[index] for index in indexes] if self.scope == "per_world" else ([indexes] if indexes else [])
+        for group in groups:
+
+            def compute(backend: Any) -> tuple[torch.Tensor, float]:
+                novelty = (
+                    backend.compute_transition_novelty(self._row_context(content, group), update_stats=update_stats)
+                    if self.policy.strategy == "icm"
+                    else backend.compute_intrinsic_rewards(content["successor"][group], update_stats=update_stats)
+                )
+                scale = backend.get_intrinsic_weight() if self.policy.strategy == "adaptive_rnd" else self.policy.initial_intrinsic_weight
+                if (
+                    novelty.shape != (len(group),)
+                    or not bool(torch.isfinite(novelty).all())
+                    or not bool(torch.isfinite(torch.tensor(scale)))
+                ):
+                    raise RuntimeError("provider returned invalid reward")
+                return novelty, scale
+
+            values, weight = self._call(accepted.world_ids[group[0]], compute)
+            raw[group], scales[group] = values, weight
+        result = CuriosityReward(raw, scales, content["active"], stamp.event_ids, self.scope)
+        pending.update(context=content, update_stats=update_stats, reward=result)
+        for index in indexes:
+            world = accepted.world_ids[index]
+            self._cache[world]["reward"] = dict(
+                event_id=stamp.event_ids[index],
+                content=self._local_content(content, index),
+                update_stats=update_stats,
+                raw=raw[index].clone(),
+                scale=scales[index].clone(),
+            )
+        self.mutation_revision += 1
+        return deepcopy(result)
+
+    @_serialized
+    def admit_and_service(
+        self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode
+    ) -> tuple[WorldServiceReceipt, ...]:
+        content = self._context(context, stamp, accepted)
+        pending = self._pending
+        assert pending is not None
+        _require(pending["reward"] is not None, "reward must precede service")
+        if pending["serviced"]:
+            return cast(tuple[WorldServiceReceipt, ...], pending["receipts"])
+        indexes = content["active"].nonzero().flatten().tolist()
+        groups = [[i] for i in range(len(self.world_ids))] if self.scope == "per_world" else ([indexes] if indexes else [])
+        receipts = []
+        for group in groups:
+            world = accepted.world_ids[group[0]]
+            active = bool(content["active"][group[0]])
+            clock = None
+            values: dict[str, Any] = dict(
+                admitted_rows=0,
+                consumed_rows=0,
+                dropped_rows=0,
+                pending_rows=0,
+                optimizer_updates=0,
+                mandatory_service_updates=0,
+                last_loss=0.0,
+            )
+            if active and self.policy.strategy in ("rnd", "adaptive_rnd", "icm"):
+                clock = ServiceClock(
+                    self.policy.service_clock_unit,
+                    self._cursor[world]["cumulative_service_position"] + 1 if self.scope == "per_world" else context.vector_tick,
+                )
+
+                def service(backend: Any) -> Any:
+                    payload = self._row_context(content, group) if self.policy.strategy == "icm" else content["predecessor"][group]
+                    if self.scope == "per_world":
+                        return backend.admit_and_service_at(payload, clock=clock)
+                    if self.policy.strategy == "icm":
+                        return backend.admit_and_service(payload)
+                    return backend.admit_and_service(payload, vector_tick=context.vector_tick)
+
+                receipt = self._call(world, service)
+                if self.policy.strategy == "icm":
+                    values = {key: getattr(receipt, key) for key in values}
+                else:
+                    values = {key: getattr(receipt, key) for key in values if key not in ("mandatory_service_updates", "last_loss")}
+                    values.update(
+                        mandatory_service_updates=receipt.overflow_optimizer_updates,
+                        last_loss=0.0 if receipt.last_loss is None else receipt.last_loss,
+                    )
+            item = WorldServiceReceipt(
+                self.scope, world if self.scope == "per_world" else None, tuple(stamp.event_ids[i] for i in group), active, clock, **values
+            )
+            receipts.append(item)
+            if active:
+                for index in group:
+                    local = accepted.world_ids[index]
+                    self._cursor[local].update(eligible_seq=stamp.event_ids[index].eligible_seq, participated=True)
+                    self._cursor[local]["cumulative_service_position"] += 1
+                    self._cache[local]["service"] = dict(
+                        event_id=stamp.event_ids[index], content=self._local_content(content, index), receipt=item
+                    )
+        pending.update(receipts=tuple(receipts), serviced=True)
+        self.mutation_revision += 1
+        return tuple(receipts)
+
+    @_serialized
+    def prepare_completion(
+        self,
+        *,
+        accepted: WorldAcceptedEpisode,
+        boundary_key: int,
+        completion_content: Any,
+        outcomes: tuple[LaneOutcome, ...],
+        participated_world_ids: tuple[str, ...],
+    ) -> PreparedBankCompletion:
+        self._healthy()
+        self._auth(accepted)
+        _require(type(boundary_key) is int and boundary_key == accepted.batch_episode, "completion boundary mismatch")
+        _require(type(outcomes) is tuple and all(isinstance(event, LaneOutcome) for event in outcomes), "actual lane outcomes required")
+        participants = tuple(world for world in accepted.world_ids if self._cursor[world]["participated"])
+        _require(bool(participants) and participated_world_ids == participants, "completion participation mismatch")
+        _require(tuple(event.world_id for event in outcomes) == participants, "outcome order/membership mismatch")
+        _require(self._pending is None or self._pending["serviced"], "unfinished phase at completion")
+        for event in outcomes:
+            index = accepted.world_ids.index(event.world_id)
+            _require(
+                event.world_episode_seq == accepted.world_episode_seqs[index]
+                and event.batch_episode == accepted.batch_episode
+                and event.outcome.agent_idx == index,
+                "outcome accepted identity mismatch",
+            )
+        # Metadata-only size pass; admission precedes outcome cloning/candidates.
+        outcome_bytes = sum(
+            value.numel() * value.element_size()
+            for event in outcomes
+            for value in (event.outcome.final_observation, event.outcome.final_meters)
+        )
+        if self._prepared is not None:
+            prepared = self._prepared
+            canonical = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in (freeze_lane_outcome(event) for event in outcomes))
+            _require(
+                prepared.accepted is accepted
+                and prepared.boundary_key == boundary_key
+                and _same(prepared.completion_content, completion_content)
+                and _same(canonical, completion_content),
+                "changed pending completion",
+            )
+            return prepared
+        _require(all(self._cursor[world]["disposition"] is None for world in self.world_ids), "episode already disposed")
+        self._report(self._allocation("complete", len(participants), outcome_bytes))
+        for event in outcomes:
+            lane_outcome_state(event)
+        canonical = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in (freeze_lane_outcome(event) for event in outcomes))
+        _require(_same(canonical, completion_content), "completion content must contain exact full canonical payload and fingerprint")
+        values: dict[str, tuple[list[float], float]] = {}
+        observed = False
+        try:
+            if self.policy.strategy == "adaptive_rnd":
+                groups = [(event.world_id, (event,)) for event in outcomes] if self.scope == "per_world" else [(participants[0], outcomes)]
+                for world, events in groups:
+
+                    def candidate(backend: Any) -> Any:
+                        offside = copy(backend)
+                        offside.survival_history = list(backend.survival_history)
+                        try:
+                            for event in events:
+                                offside.update_on_episode_end(event.outcome.survival_time)
+                        except ValueError as error:
+                            return (False, str(error))
+                        return (True, (list(offside.survival_history), offside.current_intrinsic_weight))
+
+                    observed = True
+                    result = self._call(world, candidate)
+                    _require(result[0], result[1] if not result[0] else "")
+                    values[world] = result[1]
+        except BaseException:
+            if observed:
+                self.mutation_revision += 1
+            raise
+        dispositions = tuple((world, "completed" if world in participants else "retired_nonparticipating") for world in accepted.world_ids)
+        payload = dict(
+            accepted=accepted,
+            boundary_key=boundary_key,
+            completion_content=canonical,
+            participated_world_ids=participants,
+            dispositions=dispositions,
+        )
+        receipt = self._issuer.issue(kind="prepared_dispositions", payload=payload)
+        self.mutation_revision += 1
+        prepared = PreparedBankCompletion(
+            self, self.mutation_revision, accepted, boundary_key, canonical, participants, dispositions, deepcopy(values), receipt, False
+        )
+        self._prepared = prepared
+        # Publication data is bank-owned, separate from the returned opaque token.
+        self._completion_values, self._completion_payload = values, payload
+        return prepared
+
+    @_serialized
+    def commit_completion(self, *, prepared: PreparedBankCompletion) -> WorldOwnerReceipt:
+        self._healthy()
+        _require(isinstance(prepared, PreparedBankCompletion) and prepared.destination is self, "foreign completion token")
+        self._auth(prepared.accepted)
+        if self._committed is not None and self._committed[0] is prepared:
+            return self._committed[1]
+        _require(self._prepared is prepared and not prepared.used and prepared.revision == self.mutation_revision, "stale completion token")
+        payload = self._completion_payload
+        _require(
+            prepared.boundary_key == payload["boundary_key"]
+            and _same(prepared.completion_content, payload["completion_content"])
+            and prepared.participated_world_ids == payload["participated_world_ids"]
+            and prepared.dispositions == payload["dispositions"],
+            "changed completion token",
+        )
+        try:
+            for world, (history, weight) in self._completion_values.items():
+
+                def publish(backend: Any) -> None:
+                    backend.survival_history = history
+                    backend.current_intrinsic_weight = weight
+
+                self._call(world, publish)
+            receipt = self._issuer.issue(kind="dispositions", payload=payload)
+            for world, disposition in prepared.dispositions:
+                self._cursor[world]["disposition"] = disposition
+                index = prepared.participated_world_ids.index(world) if world in prepared.participated_world_ids else None
+                self._cache[world]["completion"] = dict(
+                    episode=self._cursor[world]["accepted_episode_seq"],
+                    disposition=disposition,
+                    content=None if index is None else prepared.completion_content[index],
+                )
+        except BaseException:
+            self._failed = True
+            raise
+        prepared.used = True
+        self._prepared = None
+        self._committed = (prepared, receipt)
+        self._completion_values = {}
+        self.mutation_revision += 1
+        return receipt
+
+    @_serialized
+    def prepare_empty_episode_evidence(self, *, accepted: WorldAcceptedEpisode) -> WorldOwnerReceipt:
+        self._available()
+        self._auth(accepted)
+        _require(
+            not any(
+                cursor["participated"] or cursor["eligible_seq"] or cursor["disposition"] is not None for cursor in self._cursor.values()
+            ),
+            "episode is not empty",
+        )
+        _require(self._pending is None or self._pending["serviced"], "pending empty phase")
+        return self._issuer.issue(kind="empty_episode", payload=dict(accepted=accepted, participated_world_ids=(), events=()))
+
+    @_serialized
+    def quarantine_episode(self, *, accepted: WorldAcceptedEpisode, reason: str) -> None:
+        self._auth(accepted)
+        _require(type(reason) is str and reason in ("empty_participation", "runtime_failure"), "unsupported quarantine reason")
+        if self._quarantine is not None:
+            _require(self._quarantine[0] is accepted and self._quarantine[1] == reason, "changed quarantine notification")
+            return
+        self._quarantine = (accepted, reason)
+        self._failed = True
+        self.mutation_revision += 1
+
+    @_serialized
+    def snapshot_world(self, *, world_id: str) -> dict[str, Any]:
+        self._available()
+        _require(type(world_id) is str and world_id in self._cursor, "unknown exact world ID")
+        try:
+            backend = self._owners[world_id].snapshot() if self.scope == "per_world" else deepcopy(self._shared.checkpoint_state())
+        except BaseException:
+            self._failed = True
+            raise
+        finally:
+            self.mutation_revision += 1
+        accepted = self._accepted
+        identity = (
+            None
+            if accepted is None
+            else dict(
+                batch_episode=accepted.batch_episode,
+                world_ids=list(accepted.world_ids),
+                world_episode_seqs=list(accepted.world_episode_seqs),
+            )
+        )
+        pending = None
+        if self._pending is not None and not self._pending["serviced"]:
+            assert accepted is not None
+            index = accepted.world_ids.index(world_id)
+            if bool(self._pending["active"][index]):
+                pending = dict(
+                    event_id=self._pending["stamp"].event_ids[index],
+                    vector_tick=self._pending["tick"],
+                    context=None if self._pending["context"] is None else self._local_content(self._pending["context"], index),
+                )
+        return dict(
+            schema="curiosity-bank-world-v1",
+            scope=self.scope,
+            world_id=world_id,
+            policy_identity=self.policy.policy_identity,
+            descriptor=self.descriptor.to_dict(),
+            backend=backend,
+            curiosity_epoch=0,
+            accepted_identity=identity,
+            cursor=deepcopy(self._cursor[world_id]),
+            phase_cache=deepcopy(self._cache[world_id]),
+            pending_step=pending,
+        )
diff --git a/tests/test_townlet/regressions/bac/test_pw_private_bank.py b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
index 78c9a137..f78bbda6 100644
--- a/tests/test_townlet/regressions/bac/test_pw_private_bank.py
+++ b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
@@ -146,34 +146,37 @@ def _updates(state: dict[str, Any], family: str) -> int:
     if family == "icm":
         return state["counters"]["optimizer_updates"]
     return _rnd_native(state, family)["predictor_service"]["optimizer_updates"]
 
 
 def _ownership(backend: Any, family: str) -> dict[str, Any]:
     """Read actual published provider objects; return scalars/data, never live objects."""
     result: dict[str, Any] = {"backend": id(backend)}
     if family not in TRAINABLE:
         result["native"] = backend.checkpoint_state()
+        if family == "count_based":
+            result["counts_container"] = id(backend._counts)  # Root-published actual OrderedDict.
         return result
     actual = backend.rnd if family == "adaptive_rnd" else backend
     models = (
         (actual.encoder, actual.inverse_model, actual.forward_model)
         if family == "icm"
         else (
             actual.fixed_network,
             actual.predictor_network,
         )
     )
     parameters = [parameter for model in models for parameter in model.parameters()]
     result.update(
         models=tuple(id(model) for model in models),
         parameters=tuple(id(parameter) for parameter in parameters),
+        trainable_parameters=tuple(id(parameter) for parameter in parameters if parameter.requires_grad),
         storage=tuple(_storage(parameter) for parameter in parameters),
         optimizer=id(actual.optimizer),
         optimizer_parameters=tuple(id(parameter) for group in actual.optimizer.param_groups for parameter in group["params"]),
         gradient_storage=tuple(_storage(parameter.grad) for parameter in parameters if parameter.grad is not None),
         gradients=tuple(None if parameter.grad is None else parameter.grad.detach().clone() for parameter in parameters),
         moment_storage=tuple(_storage(tensor) for tensor in _tensors(actual.optimizer.state)),
         native=backend.checkpoint_state(),
     )
     if family in ("rnd", "adaptive_rnd"):
         result["queue"] = id(actual.obs_buffer)
@@ -227,25 +230,28 @@ def _completion(bank: Any, accepted: Any, ids: tuple[str, ...], steps: int) -> A
 @pytest.mark.parametrize("family", FAMILIES)
 def test_private_models_moments_and_queues_do_not_alias(harness_factory: Any, family: str) -> None:
     first, second = harness_factory(family), harness_factory(family)
     for harness in (first, second):
         for tick in range(1, 8):
             _step(harness.bank, harness.accepted, _context(tick, (True, True), 3, 0.7))
     views = [_inspect(h.bank, world, family) for h in (first, second) for world in WORLD_IDS]
     for index, left in enumerate(views):
         for right in views[index + 1 :]:
             assert left["backend"] != right["backend"]
+            if family == "count_based":
+                assert left["counts_container"] != right["counts_container"]
             if family in TRAINABLE:
                 for field in ("models", "parameters", "storage", "gradient_storage", "moment_storage"):
                     assert set(left[field]).isdisjoint(right[field]), field
                 assert left["optimizer"] != right["optimizer"]
-                assert set(left["optimizer_parameters"]) <= set(left["parameters"])
+                assert len(left["optimizer_parameters"]) == len(left["trainable_parameters"])
+                assert set(left["optimizer_parameters"]) == set(left["trainable_parameters"])
                 for field in ("queue", "rms", "history"):
                     if field in left:
                         assert left[field] != right[field]
     snapshot = first.bank.snapshot_world(world_id="world1")
     before = deepcopy(snapshot)
     for tensor in _tensors(snapshot):
         if tensor.numel():
             tensor.zero_()
     _equal(first.bank.snapshot_world(world_id="world1"), before)
     if family not in TRAINABLE:
@@ -415,20 +421,21 @@ def test_completion_preserves_nonempty_gradients_and_tail(harness_factory: Any)
     assert committed.payload["dispositions"] == tuple((world, "completed") for world in WORLD_IDS)
     for world in WORLD_IDS:
         after = _inspect(h.bank, world, "adaptive_rnd")
         for field in (
             "models",
             "parameters",
             "storage",
             "optimizer",
             "optimizer_parameters",
             "gradient_storage",
+            "moment_storage",
             "gradients",
             "queue",
             "rms",
         ):
             _equal(before[world][field], after[field])
         _equal(before[world]["native"]["rnd_state"], after["native"]["rnd_state"])
         assert after["native"]["survival_history"] == [7]
 
 
 def test_completion_malformed_last_outcome_and_wrong_destination_refuse(harness_factory: Any) -> None:
@@ -712,20 +719,23 @@ class _Harness:
             )
         }
         effects = self.boundary.receipt(
             "boundary_effects",
             batch_episode=self.accepted.batch_episode,
             accepted_identity=self.accepted,
             completion_content=content,
             retirement_receipt=committed,
             **children,
         )
+        self.last_completion_content = content
+        self.last_completion_receipt = committed
+        _equal(committed.payload["completion_content"], content)
         self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
         self.begin(self.accepted.batch_episode + 1)
 
 
 @pytest.fixture
 def harness_factory(compiled: Any) -> Any:
     def make(
         family: str,
         *,
         scope: str = "per_world",
@@ -846,32 +856,37 @@ def test_exact_id_not_row_or_spectator_controls_private_state(harness_factory: A
                 actions=torch.full((rows,), tick % 2, dtype=torch.int64),
                 successor=predecessor + 0.125,
                 active_on_entry=active,
                 vector_tick=tick,
             )
             _, reward, _ = _step(h.bank, h.accepted, context)
             outputs.append((reward.raw[index], reward.scales[index], h.bank.snapshot_world(world_id="world1")))
         for raw, scale, snapshot in outputs[1:]:
             _equal(outputs[0][0], raw)
             _equal(outputs[0][1], scale)
-            _equal(outputs[0][2]["backend"], snapshot["backend"])
-            _equal(outputs[0][2]["cursor"], snapshot["cursor"])
+            _equal(_private_domain(outputs[0][2], allowed_ticks=None), _private_domain(snapshot, allowed_ticks=None))
 
 
 def test_adaptive_real_history_weight_and_per_row_scale(harness_factory: Any) -> None:
     first, second = harness_factory("adaptive_rnd"), harness_factory("adaptive_rnd")
     for episode in range(10):
         for h, other_survival in ((first, 1), (second, 12)):
             _step(h.bank, h.accepted, _context(episode + 1, (True, True), 3, float(other_survival)))
             h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
             h.close_and_begin(7, world0_steps=other_survival)
-        _equal(first.bank.snapshot_world(world_id="world1"), second.bank.snapshot_world(world_id="world1"))
+        _equal(
+            _private_domain(first.bank.snapshot_world(world_id="world1"), allowed_ticks=None),
+            _private_domain(second.bank.snapshot_world(world_id="world1"), allowed_ticks=None),
+        )
+        assert first.last_completion_content != second.last_completion_content
+        _equal(first.last_completion_receipt.payload["completion_content"], first.last_completion_content)
+        _equal(second.last_completion_receipt.payload["completion_content"], second.last_completion_content)
     snapshots = {world: _native(first.bank.snapshot_world(world_id=world)) for world in WORLD_IDS}
     assert snapshots["world1"]["survival_history"] == [7] * 10
     assert snapshots["world0"]["survival_history"] == [1] * 10
     assert snapshots["world1"]["current_intrinsic_weight"] < snapshots["world1"]["initial_intrinsic_weight"]
     _, reward, _ = _step(first.bank, first.accepted, _context(100, (True, True), 3, 0.0))
     assert reward.scales[1].item() == pytest.approx(snapshots["world1"]["current_intrinsic_weight"])
     assert reward.scales[0] > reward.scales[1]
     assert reward.scales.shape == (2,)
 
 
@@ -892,10 +907,247 @@ def test_completion_content_is_full_canonical_outcome_not_just_hash(harness_fact
     with pytest.raises(ValueError):
         h.bank.prepare_completion(
             accepted=h.accepted,
             boundary_key=h.accepted.batch_episode,
             completion_content=tuple(content),
             outcomes=outcomes,
             participated_world_ids=WORLD_IDS,
         )
     for world, state in zip(WORLD_IDS, before, strict=True):
         _equal(state, h.bank.snapshot_world(world_id=world))
+
+
+def _private_domain(snapshot: dict[str, Any], *, allowed_ticks: set[int] | None) -> dict[str, Any]:
+    """Compare EVERY world-local field; check separate roster/binding provenance.
+
+    Snapshot caches are explicitly world-local. Whole-bank completion correlation
+    is asserted on actual receipts, never hidden in a local learned-state cache.
+    Only reserved global ticks in cache/pending metadata may be normalized, and
+    only for the deliberately different-tick differential.
+    """
+    result = deepcopy(snapshot)
+    descriptor = WorldCuriosityDescriptor.from_dict(result.pop("descriptor"))
+    world = result["world_id"]
+    assert world in descriptor.world_ids
+    result["stable_descriptor"] = {
+        key: value
+        for key, value in descriptor.to_dict().items()
+        if key not in ("world_ids", "canonical_world_ids", "world_binding_hash", "seeds")
+    }
+    result["world_seeds"] = dict(descriptor.seeds[world])
+    binding = result.pop("accepted_identity")
+    if binding is None:
+        result["accepted_world_identity"] = None
+    else:
+        assert len(binding["world_ids"]) == len(binding["world_episode_seqs"])
+        assert len(set(binding["world_ids"])) == len(binding["world_ids"])
+        index = binding["world_ids"].index(world)
+        assert binding["world_episode_seqs"][index] == result["cursor"]["accepted_episode_seq"]
+        result["accepted_world_identity"] = (binding["batch_episode"], world, binding["world_episode_seqs"][index])
+
+    def provenance(value: Any) -> Any:
+        if isinstance(value, dict):
+            owned = {}
+            for key, item in value.items():
+                if key == "vector_tick" and allowed_ticks is not None:
+                    assert type(item) is int and item in allowed_ticks
+                    owned[key] = "explicit-global-provenance"
+                else:
+                    owned[key] = provenance(item)
+            return owned
+        if isinstance(value, tuple):
+            return tuple(provenance(item) for item in value)
+        if isinstance(value, list):
+            return [provenance(item) for item in value]
+        return value
+
+    # Do not omit absent, pending, completion or retry data: all keys remain.
+    result["phase_cache"] = provenance(result["phase_cache"])
+    result["pending_step"] = provenance(result["pending_step"])
+    return result
+
+
+def test_private_count_same_bin_and_owned_container_mutation(harness_factory: Any) -> None:
+    first, second = harness_factory("count_based"), harness_factory("count_based")
+    context = IntrinsicTransitionContext(
+        predecessor=torch.zeros(2, 3),
+        actions=torch.zeros(2, dtype=torch.int64),
+        successor=torch.ones(2, 3),
+        active_on_entry=torch.ones(2, dtype=torch.bool),
+        vector_tick=1,
+    )
+    _, reward, _ = _step(first.bank, first.accepted, context)
+    assert reward.raw.tolist() == [1.0, 1.0]  # Same bins, distinct real dictionaries.
+    untouched = second.bank.snapshot_world(world_id="world1")
+    before = {world: first.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    modified = first.bank.snapshot_world(world_id="world0")
+    native = _native(modified)
+    assert native["counts"] and native["lru"]
+    native["counts"].clear()
+    native["lru"].clear()
+    for world in WORLD_IDS:
+        _equal(before[world], first.bank.snapshot_world(world_id=world))
+    _equal(untouched, second.bank.snapshot_world(world_id="world1"))
+    _, next_reward, _ = _step(
+        first.bank,
+        first.accepted,
+        IntrinsicTransitionContext(
+            predecessor=context.predecessor,
+            actions=context.actions,
+            successor=context.successor,
+            active_on_entry=torch.tensor([False, True]),
+            vector_tick=2,
+        ),
+    )
+    assert next_reward.raw[1].item() == pytest.approx(2**-0.5)
+    _equal(before["world0"]["backend"], first.bank.snapshot_world(world_id="world0")["backend"])
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+def test_private_idle_ticks_do_not_change_local_updates_or_retry_cache(harness_factory: Any, family: str) -> None:
+    first, second = harness_factory(family), harness_factory(family)
+    initial = _native(first.bank.snapshot_world(world_id="world1"))
+    for local in range(1, 10):
+        for offset, active in ((-2, (True, False)), (-1, (False, False))):
+            _step(second.bank, second.accepted, _context(local * 10 + offset, active, 3, 99.0))
+        results = []
+        for h, tick in ((first, local), (second, local * 10)):
+            predecessor = torch.full((2, 3), local / 13, dtype=torch.float32)
+            context = IntrinsicTransitionContext(
+                predecessor=predecessor,
+                actions=torch.full((2,), local % 2, dtype=torch.int64),
+                successor=predecessor + 0.2,
+                active_on_entry=torch.tensor([False, True]),
+                vector_tick=tick,
+            )
+            stamp, reward, _ = _step(h.bank, h.accepted, context)
+            before_retry = h.bank.snapshot_world(world_id="world1")
+            replay = h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+            h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted)
+            _equal(reward.raw, replay.raw)
+            _equal(before_retry, h.bank.snapshot_world(world_id="world1"))
+            results.append((reward, _private_domain(before_retry, allowed_ticks={tick})))
+        _equal(results[0][0].raw[1], results[1][0].raw[1])
+        _equal(results[0][0].scales[1], results[1][0].scales[1])
+        _equal(results[0][1], results[1][1])
+    final = _native(first.bank.snapshot_world(world_id="world1"))
+    if family in TRAINABLE:
+        assert _updates(final, family) >= 2
+        assert any(not torch.equal(a, b) for a, b in zip(_learned(initial, family), _learned(final, family), strict=True))
+        assert any(bool(item["exp_avg"].ne(0).any()) for item in _optimizer(final, family)["state"].values())
+
+
+def _seed_numeric_prefix(backend: Any, sources: Any) -> None:
+    # Synthetic VALID learned prefix via real algorithm; not nine ENV episodes.
+    for _ in range(9):
+        backend.update_on_episode_end(10**20)
+
+
+def test_pristine_adaptive_numeric_refusal_control(compiled: Any) -> None:
+    policy = _policy(compiled, "adaptive_rnd", "per_world")
+    owner = _owned(policy, _descriptor(policy, WORLD_IDS, 3), "world1")
+    owner.call(_seed_numeric_prefix)
+    state = owner.snapshot()
+    owner.call(lambda backend, sources: backend.validate_state(state["backend"]))
+
+    def candidate(backend: Any, sources: Any) -> bool:
+        from copy import copy
+
+        other = copy(backend)
+        other.survival_history = list(backend.survival_history)
+        with pytest.raises(ValueError):
+            other.update_on_episode_end(1)
+        return True
+
+    assert owner.call(candidate) is True
+    _equal(state, owner.snapshot())
+
+
+def test_expected_numeric_completion_refusal_only_advances_observation_revision(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    h.bank._owners["world1"].call(_seed_numeric_prefix)
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    with pytest.raises(ValueError):
+        _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    assert h.bank.mutation_revision == revision + 1
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    # A genuine subsequent local operation proves neither owner nor bank was
+    # falsely quarantined by expected off-side arithmetic refusal.
+    _step(h.bank, h.accepted, _context(2, (True, True), 3, 0.0))
+
+
+def test_unexpected_callback_failure_quarantines_earlier_success_and_replay(harness_factory: Any) -> None:
+    h = harness_factory("rnd")
+    old_context = _context(1, (True, True), 3, 0.0)
+    old_stamp, _, _ = _step(h.bank, h.accepted, old_context)
+    calls: list[str] = []
+
+    def inject(backend: Any, sources: Any) -> None:
+        def fail(*args: Any, **kwargs: Any) -> None:
+            calls.append("world1")
+            raise RuntimeError("injected real owned reward operation failure")
+
+        backend.compute_intrinsic_rewards = fail
+
+    h.bank._owners["world1"].call(inject)
+    before = h.bank.snapshot_world(world_id="world0")
+    context = _context(2, (True, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=2)
+    with pytest.raises(RuntimeError, match="injected real owned"):
+        h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+    assert calls == ["world1"]
+    # Direct WS diagnostic of the earlier healthy owner proves a real preceding
+    # effect occurred; no attempt to roll that effect back is permitted.
+    state = h.bank._owners["world0"].snapshot()["backend"]
+    assert state["reward_rms_count"] > _native(before)["reward_rms_count"]
+    for operation in (
+        lambda: h.bank.reward(context=old_context, stamp=old_stamp, accepted=h.accepted, update_stats=True),
+        lambda: h.bank.admit_and_service(context=old_context, stamp=old_stamp, accepted=h.accepted),
+        lambda: h.bank.snapshot_world(world_id="world0"),
+    ):
+        with pytest.raises((RuntimeError, ValueError)):
+            operation()
+
+
+@pytest.mark.parametrize("pending", ("step", "completion"))
+def test_conservative_quarantine_after_actual_env_abandon_refusal(harness_factory: Any, pending: str) -> None:
+    h = harness_factory("adaptive_rnd")
+    h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
+    context = _context(1, (True, True), 3, 0.0)
+    if pending == "completion":
+        _step(h.bank, h.accepted, context)
+        prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    else:
+        stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=1)
+    with pytest.raises(ValueError):
+        h.env.abandon_episode(accepted=h.accepted, reason="empty_participation")
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    with pytest.raises((RuntimeError, ValueError)):
+        if pending == "completion":
+            h.bank.commit_completion(prepared=prepared)
+        else:
+            h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+
+
+def test_exact_whitespace_world_id_survives_real_completion(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd", ids=(" ", "world1"))
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    prepared = _completion(h.bank, h.accepted, h.accepted.world_ids, 1)
+    receipt = h.bank.commit_completion(prepared=prepared)
+    assert receipt.payload["dispositions"][0] == (" ", "completed")
+    state = h.bank.snapshot_world(world_id=" ")
+    assert state["world_id"] == " " and _native(state)["survival_history"] == [1]
+
+
+def test_quarantine_refuses_cached_completion_success(harness_factory: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    receipt = h.bank.commit_completion(prepared=prepared)
+    assert h.bank.commit_completion(prepared=prepared) is receipt
+    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
+    with pytest.raises((RuntimeError, ValueError)):
+        h.bank.commit_completion(prepared=prepared)
