# PW05 implementation fix round1, whole owned diff
Base fee0eac4e8e3944296fa4e22a8ad9f4a8f17f684 -> d0c26b6f52139e680f7fd96644713eeb3d17b9e8

 src/townlet/exploration/scoped_curiosity.py        | 286 +++++++++++++++++----
 .../regressions/bac/test_pw_private_bank.py        | 197 +++++++++++++-
 2 files changed, 431 insertions(+), 52 deletions(-)
diff --git a/src/townlet/exploration/scoped_curiosity.py b/src/townlet/exploration/scoped_curiosity.py
index 6ad68caa..87406664 100644
--- a/src/townlet/exploration/scoped_curiosity.py
+++ b/src/townlet/exploration/scoped_curiosity.py
@@ -135,64 +135,115 @@ def _serialized(method: Callable[..., Any]) -> Callable[..., Any]:
 
 def _allocation_estimate(
     policy: ResolvedExplorationPolicy,
     descriptor: WorldCuriosityDescriptor,
     device: torch.device,
     operation: str,
     participants: int,
     outcome_bytes: int,
 ) -> AllocationEstimate:
     d, a = descriptor.observation_dim, descriptor.action_dim
-    k = len(descriptor.world_ids) if policy.curiosity_scope == "per_world" else 1
+    if policy.curiosity_scope == "per_world":
+        k = len(descriptor.world_ids)
+    else:
+        k = 1
     model = gradients = queue = 0
     if policy.strategy in ("rnd", "adaptive_rnd"):
         e = policy.rnd_feature_dim
         p = d * 256 + 256 + 256 * 128 + 128 + 128 * e + e
         model, gradients, queue = 8 * p, 12 * p + 24, 4 * d * policy.max_pending_rows
     elif policy.strategy == "icm":
         h, f = policy.provider_parameters["hidden_dim"], policy.provider_parameters["feature_dim"]
         p = sum(x * y + y for x, y in ((d, h), (h, f), (2 * f, h), (h, a), (f + a, h), (h, f)))
         model, gradients, queue = 4 * p, 12 * p + 48, policy.max_pending_rows * (8 * d + 8)
     components: tuple[tuple[str, int], ...] = (
         ("eager_model_copy_peak", (k + 1) * model + k * queue),
         ("trained_reserve", k * (model + gradients + queue)),
     )
     if operation == "complete":
-        history = 16 * (policy.survival_window + 1) if policy.strategy == "adaptive_rnd" else 0
+        if policy.strategy == "adaptive_rnd":
+            history = 16 * (policy.survival_window + 1)
+        else:
+            history = 0
         components = (("outcome_transport", 2 * outcome_bytes), ("history_workspace", history), ("model_copies", 0))
+    if operation == "construct":
+        known_bytes = max(value for _, value in components)
+    else:
+        known_bytes = sum(value for _, value in components)
     return AllocationEstimate(
         "curiosity-allocation-estimate-v1",
         operation,
         policy.curiosity_scope,
         str(device),
         str(torch.float32),
         str(torch.float32),
         len(descriptor.world_ids),
         participants,
         k,
-        max(value for _, value in components) if operation == "construct" else sum(value for _, value in components),
+        known_bytes,
         components,
         (
             "float32 models; lazy Adam and gradients reserved",
             "sequential completion candidates; retained Python histories <= participants*window",
         ),
         ("Python containers/count integer keys", "RNG tensors", "allocator/activation/library workspace"),
     )
 
 
 def allocation_estimate(
     *, policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, device: torch.device | str
 ) -> AllocationEstimate:
     """Pure known-tensor estimate; unknown resident/workspace costs stay labeled."""
     return _allocation_estimate(policy, descriptor, torch.device(device), "construct", 0, 0)
 
 
+class _CandidateRefusalError(ValueError):
+    """Expected off-side algorithm refusal, with no live candidate publication."""
+
+
+def _observation_boundary(method: Callable[..., Any]) -> Callable[..., Any]:
+    @wraps(method)
+    def invoke(self: Any, *args: Any, **kwargs: Any) -> Any:
+        observations, revision, publication = self._observations, self.mutation_revision, self._publications
+        try:
+            return method(self, *args, **kwargs)
+        except BaseException as error:
+            if self._observations != observations or self._publications != publication:
+                if self.mutation_revision == revision:
+                    self.mutation_revision += 1
+                if not isinstance(error, _CandidateRefusalError):
+                    self._failed = True
+            raise
+
+    return invoke
+
+
+def _same_outcome(left: LaneOutcome, right: LaneOutcome) -> bool:
+    for field in (
+        "batch_episode",
+        "planned_horizon",
+        "reward_total",
+        "reward_extrinsic",
+        "reward_intrinsic",
+        "reward_shaping",
+        "policy_entropy",
+        "world_id",
+        "world_episode_seq",
+    ):
+        if not _same(getattr(left, field), getattr(right, field)):
+            return False
+    for field in ("agent_idx", "reason", "survival_time", "final_observation", "final_meters"):
+        if not _same(getattr(left.outcome, field), getattr(right.outcome, field)):
+            return False
+    return True
+
+
 class CuriosityBank:
     def __init__(
         self,
         *,
         policy: ResolvedExplorationPolicy,
         descriptor: WorldCuriosityDescriptor,
         device: torch.device | str,
         validate_accepted_episode: AcceptedEpisodeValidator,
         issuer_factory: Callable[[object], ReceiptIssuer],
         report_allocation: Callable[[AllocationEstimate], None],
@@ -222,70 +273,86 @@ class CuriosityBank:
         _require(torch.get_default_dtype() == torch.float32, "bank requires declared float32 model profile")
         _require(self.policy.strategy == "none" or descriptor.observation_dim > 0, "selected provider requires positive width")
         _require(
             callable(validate_accepted_episode) and callable(issuer_factory) and callable(report_allocation), "required owner callbacks"
         )
         self._validate, self._report = validate_accepted_episode, report_allocation
         self._issuer = issuer_factory(self)
         _require(self._issuer.owner is self, "issuer must belong to actual bank")
         self.scope, self.world_ids = self.policy.curiosity_scope, ids
         self.mutation_revision = 0
+        self._observations = 0
+        self._publications = 0
+        self._completion_payload: dict[str, Any] = {}
+        self._completion_outcomes: tuple[LaneOutcome, ...] = ()
+        self._completion_values: dict[str, tuple[list[float], float]] = {}
         self._failed = False
         self._quarantine: tuple[WorldAcceptedEpisode, str] | None = None
         self._accepted: WorldAcceptedEpisode | None = None
         self._activation: WorldOwnerReceipt | None = None
         self._pending: dict[str, Any] | None = None
         self._prepared: PreparedBankCompletion | None = None
         self._committed: tuple[PreparedBankCompletion, WorldOwnerReceipt] | None = None
         self._owners: dict[str, OwnedWorldBackend] = {}
         self._shared: Any = None
         self._cursor: dict[str, dict[str, Any]] = {
             world: dict(accepted_episode_seq=0, eligible_seq=0, cumulative_service_position=0, participated=False, disposition=None)
             for world in ids
         }
         self._cache: dict[str, dict[str, Any]] = {world: {} for world in ids}
         self._estimate = self._allocation("construct", 0, 0)
         self._report(self._estimate)
-        devices = () if self.device.type == "cpu" else (self.device.index,)
-        for world in sorted(ids) if self.scope == "per_world" else ():
+        devices: tuple[int, ...]
+        if self.device.type == "cpu":
+            devices = ()
+        else:
+            devices = (cast(int, self.device.index),)
+        private_ids: tuple[str, ...] = ()
+        if self.scope == "per_world":
+            private_ids = tuple(sorted(ids))
+        for world in private_ids:
             rng = WorldRNGState.create(descriptor=self.descriptor, world_id=world, cuda_devices=devices)
             self._owners[world] = OwnedWorldBackend.construct(rng=rng, factory=partial(self._factory, world))
         if self.scope == "shared":
             self._shared = self._factory(None, None)
 
     def _factory(self, world: str | None, rng: WorldRNGState | None) -> Any:
+        descriptor = None
+        if world is not None:
+            descriptor = self.descriptor
         return make_backend(
             self.policy,
             world_id=world,
             obs_dim=self.descriptor.observation_dim,
             action_dim=self.descriptor.action_dim,
             device=self.device,
             rng=rng,
-            descriptor=self.descriptor if world is not None else None,
+            descriptor=descriptor,
         )
 
     def _allocation(self, operation: str, participants: int, outcome_bytes: int) -> AllocationEstimate:
         return _allocation_estimate(self.policy, self.descriptor, self.device, operation, participants, outcome_bytes)
 
     def _healthy(self) -> None:
         if self._failed:
             raise RuntimeError("curiosity bank quarantined")
 
     def _auth(self, accepted: WorldAcceptedEpisode) -> None:
         self._validate(accepted=accepted)
         _require(accepted is self._accepted, "bank accepted identity mismatch")
 
     def _available(self) -> None:
         self._healthy()
         _require(self._prepared is None, "completion transaction pending")
 
     def _call(self, world: str, operation: Callable[[Any], Any]) -> Any:
+        self._observations += 1
         try:
             if self.scope == "per_world":
                 return self._owners[world].call(lambda backend, sources: operation(backend))
             return operation(self._shared)
         except BaseException:
             self._failed = True
             raise
 
     @_serialized
     def begin_episode(self, *, accepted: WorldAcceptedEpisode) -> WorldOwnerReceipt:
@@ -358,168 +425,257 @@ class CuriosityBank:
         self.mutation_revision += 1
         return stamp
 
     def _context(self, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode) -> dict[str, Any]:
         self._available()
         self._auth(accepted)
         _require(isinstance(context, IntrinsicTransitionContext) and isinstance(stamp, CuriosityStepStamp), "actual context/stamp required")
         pending = self._pending
         _require(pending is not None, "missing reservation")
         assert pending is not None
-        expected = pending["stamp"]
-        _require(
-            stamp.world_ids == expected.world_ids and stamp.event_ids == expected.event_ids and _same(stamp.eligible, expected.eligible),
-            "stamp reservation mismatch",
-        )
-        _require(
-            context.vector_tick == pending["tick"] and _same(context.active_on_entry, pending["active"]), "context provenance mismatch"
-        )
+        _require(stamp.world_ids == accepted.world_ids and _same(stamp.eligible, context.active_on_entry), "stamp row/eligibility mismatch")
+        for i, event in enumerate(stamp.event_ids):
+            _require(event.curiosity_epoch == 0 and event.world_episode_seq == accepted.world_episode_seqs[i], "stamp episode mismatch")
+            if not bool(stamp.eligible[i]):
+                _require(event.eligible_seq <= self._cursor[event.world_id]["eligible_seq"], "inactive cursor is in the future")
+        current = self._current(context, stamp)
+        if self.scope == "shared":
+            _require(current, "stamp reservation mismatch")
+        elif not current:
+            _require(bool(stamp.eligible.any()), "expired inactive reservation")
+            for i, world in enumerate(accepted.world_ids):
+                if bool(stamp.eligible[i]):
+                    _require(
+                        "reward" in self._cache[world] and self._cache[world]["reward"]["event_id"] == stamp.event_ids[i],
+                        "expired local event",
+                    )
         predecessor, successor, actions = context.predecessor, context.successor, context.actions
         _require(predecessor.shape == (len(self.world_ids), self.descriptor.observation_dim), "provider observation width mismatch")
         _require(
             predecessor.dtype == successor.dtype == torch.float32 and predecessor.device == self.device,
             "selected observation profile mismatch",
         )
         _require(bool(((actions >= 0) & (actions < self.descriptor.action_dim)).all()), "action bounds mismatch")
         content = dict(
             predecessor=predecessor, successor=successor, actions=actions, active=context.active_on_entry, vector_tick=context.vector_tick
         )
-        if pending["context"] is not None:
+        if self.scope == "shared" and pending["context"] is not None:
             _require(_same(content, pending["context"]), "changed event content")
+        if self.scope == "per_world" and not current:
+            for i, world in enumerate(accepted.world_ids):
+                if bool(stamp.eligible[i]):
+                    _require(
+                        _same(self._local_content(content, i), self._cache[world]["reward"]["content"]), "changed local event/provenance"
+                    )
         return content
 
+    def _current(self, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp) -> bool:
+        assert self._pending is not None
+        return (
+            stamp.event_ids == self._pending["stamp"].event_ids
+            and _same(stamp.eligible, self._pending["active"])
+            and context.vector_tick == self._pending["tick"]
+        )
+
+    def _replay(self, content: dict[str, Any], stamp: CuriosityStepStamp, phase: str) -> bool:
+        indexes = stamp.eligible.nonzero().flatten().tolist()
+        if self.scope != "per_world" or not indexes:
+            return False
+        for i in indexes:
+            cache = self._cache[stamp.world_ids[i]]
+            if phase not in cache or cache[phase]["event_id"] != stamp.event_ids[i]:
+                return False
+        for i in indexes:
+            _require(
+                _same(self._local_content(content, i), self._cache[stamp.world_ids[i]][phase]["content"]), "changed local event/provenance"
+            )
+        return True
+
+    def _inactive_receipt(self, event: CuriosityEventId) -> WorldServiceReceipt:
+        return WorldServiceReceipt(self.scope, event.world_id, (event,), False, None, 0, 0, 0, 0, 0, 0, 0.0)
+
     def _row_context(self, content: dict[str, Any], indexes: list[int]) -> IntrinsicTransitionContext:
         return IntrinsicTransitionContext(
             predecessor=content["predecessor"][indexes],
             actions=content["actions"][indexes],
             successor=content["successor"][indexes],
             active_on_entry=content["active"][indexes],
             vector_tick=content["vector_tick"],
         )
 
     def _local_content(self, content: dict[str, Any], index: int) -> dict[str, Any]:
-        return {key: value if key == "vector_tick" else value[index].clone() for key, value in content.items()}
+        local = {}
+        for key, value in content.items():
+            if key == "vector_tick":
+                local[key] = value
+            else:
+                local[key] = value[index].clone()
+        return local
 
     @_serialized
+    @_observation_boundary
     def reward(
         self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode, update_stats: bool
     ) -> CuriosityReward:
         content = self._context(context, stamp, accepted)
         _require(type(update_stats) is bool, "update_stats must be bool")
         pending = self._pending
         assert pending is not None
+        if self._replay(content, stamp, "reward"):
+            raw = torch.zeros(len(stamp.world_ids), device=self.device)
+            scales = torch.zeros_like(raw)
+            for i, world in enumerate(stamp.world_ids):
+                if bool(stamp.eligible[i]):
+                    cached = self._cache[world]["reward"]
+                    _require(cached["update_stats"] == update_stats, "changed reward mode")
+                    raw[i], scales[i] = cached["raw"], cached["scale"]
+            return CuriosityReward(raw, scales, stamp.eligible, stamp.event_ids, self.scope)
+        _require(self._current(context, stamp), "expired reward event")
         if pending["reward"] is not None:
             _require(update_stats == pending["update_stats"], "changed reward mode")
             return cast(CuriosityReward, deepcopy(pending["reward"]))
         raw = torch.zeros(len(self.world_ids), device=self.device)
         scales = torch.zeros_like(raw)
         indexes = content["active"].nonzero().flatten().tolist()
-        groups = [[index] for index in indexes] if self.scope == "per_world" else ([indexes] if indexes else [])
+        if self.scope == "per_world":
+            groups = [[index] for index in indexes]
+        else:
+            if indexes:
+                groups = [indexes]
+            else:
+                groups = []
         for group in groups:
 
             def compute(backend: Any) -> tuple[torch.Tensor, float]:
-                novelty = (
-                    backend.compute_transition_novelty(self._row_context(content, group), update_stats=update_stats)
-                    if self.policy.strategy == "icm"
-                    else backend.compute_intrinsic_rewards(content["successor"][group], update_stats=update_stats)
-                )
-                scale = backend.get_intrinsic_weight() if self.policy.strategy == "adaptive_rnd" else self.policy.initial_intrinsic_weight
+                if self.policy.strategy == "icm":
+                    novelty = backend.compute_transition_novelty(self._row_context(content, group), update_stats=update_stats)
+                else:
+                    novelty = backend.compute_intrinsic_rewards(content["successor"][group], update_stats=update_stats)
+                if self.policy.strategy == "adaptive_rnd":
+                    scale = backend.get_intrinsic_weight()
+                else:
+                    scale = self.policy.initial_intrinsic_weight
                 if (
                     novelty.shape != (len(group),)
                     or not bool(torch.isfinite(novelty).all())
                     or not bool(torch.isfinite(torch.tensor(scale)))
                 ):
                     raise RuntimeError("provider returned invalid reward")
                 return novelty, scale
 
             values, weight = self._call(accepted.world_ids[group[0]], compute)
             raw[group], scales[group] = values, weight
+        self._publications += 1
         result = CuriosityReward(raw, scales, content["active"], stamp.event_ids, self.scope)
         pending.update(context=content, update_stats=update_stats, reward=result)
         for index in indexes:
             world = accepted.world_ids[index]
             self._cache[world]["reward"] = dict(
                 event_id=stamp.event_ids[index],
                 content=self._local_content(content, index),
                 update_stats=update_stats,
                 raw=raw[index].clone(),
                 scale=scales[index].clone(),
             )
         self.mutation_revision += 1
         return deepcopy(result)
 
     @_serialized
+    @_observation_boundary
     def admit_and_service(
         self, *, context: IntrinsicTransitionContext, stamp: CuriosityStepStamp, accepted: WorldAcceptedEpisode
     ) -> tuple[WorldServiceReceipt, ...]:
         content = self._context(context, stamp, accepted)
         pending = self._pending
         assert pending is not None
+        if self._replay(content, stamp, "service"):
+            cached_receipts = []
+            for i, world in enumerate(stamp.world_ids):
+                if bool(stamp.eligible[i]):
+                    cached_receipts.append(self._cache[world]["service"]["receipt"])
+                else:
+                    cached_receipts.append(self._inactive_receipt(stamp.event_ids[i]))
+            return tuple(cached_receipts)
+        _require(self._current(context, stamp), "expired service event")
         _require(pending["reward"] is not None, "reward must precede service")
+        if self.scope == "per_world":
+            _require(self._replay(content, stamp, "reward") or not bool(stamp.eligible.any()), "reward source mismatch")
         if pending["serviced"]:
             return cast(tuple[WorldServiceReceipt, ...], pending["receipts"])
         indexes = content["active"].nonzero().flatten().tolist()
-        groups = [[i] for i in range(len(self.world_ids))] if self.scope == "per_world" else ([indexes] if indexes else [])
+        if self.scope == "per_world":
+            groups = [[i] for i in range(len(self.world_ids))]
+        else:
+            if indexes:
+                groups = [indexes]
+            else:
+                groups = []
         receipts = []
+        self._publications += 1
         for group in groups:
             world = accepted.world_ids[group[0]]
             active = bool(content["active"][group[0]])
             clock = None
             values: dict[str, Any] = dict(
                 admitted_rows=0,
                 consumed_rows=0,
                 dropped_rows=0,
                 pending_rows=0,
                 optimizer_updates=0,
                 mandatory_service_updates=0,
                 last_loss=0.0,
             )
             if active and self.policy.strategy in ("rnd", "adaptive_rnd", "icm"):
-                clock = ServiceClock(
-                    self.policy.service_clock_unit,
-                    self._cursor[world]["cumulative_service_position"] + 1 if self.scope == "per_world" else context.vector_tick,
-                )
+                position = context.vector_tick
+                if self.scope == "per_world":
+                    position = self._cursor[world]["cumulative_service_position"] + 1
+                clock = ServiceClock(self.policy.service_clock_unit, position)
 
                 def service(backend: Any) -> Any:
-                    payload = self._row_context(content, group) if self.policy.strategy == "icm" else content["predecessor"][group]
+                    if self.policy.strategy == "icm":
+                        payload = self._row_context(content, group)
+                    else:
+                        payload = content["predecessor"][group]
                     if self.scope == "per_world":
                         return backend.admit_and_service_at(payload, clock=clock)
                     if self.policy.strategy == "icm":
                         return backend.admit_and_service(payload)
                     return backend.admit_and_service(payload, vector_tick=context.vector_tick)
 
                 receipt = self._call(world, service)
                 if self.policy.strategy == "icm":
                     values = {key: getattr(receipt, key) for key in values}
                 else:
                     values = {key: getattr(receipt, key) for key in values if key not in ("mandatory_service_updates", "last_loss")}
-                    values.update(
-                        mandatory_service_updates=receipt.overflow_optimizer_updates,
-                        last_loss=0.0 if receipt.last_loss is None else receipt.last_loss,
-                    )
-            item = WorldServiceReceipt(
-                self.scope, world if self.scope == "per_world" else None, tuple(stamp.event_ids[i] for i in group), active, clock, **values
-            )
+                    loss = receipt.last_loss
+                    if loss is None:
+                        loss = 0.0
+                    values.update(mandatory_service_updates=receipt.overflow_optimizer_updates, last_loss=loss)
+            receipt_world = None
+            if self.scope == "per_world":
+                receipt_world = world
+            item = WorldServiceReceipt(self.scope, receipt_world, tuple(stamp.event_ids[i] for i in group), active, clock, **values)
             receipts.append(item)
             if active:
                 for index in group:
                     local = accepted.world_ids[index]
                     self._cursor[local].update(eligible_seq=stamp.event_ids[index].eligible_seq, participated=True)
                     self._cursor[local]["cumulative_service_position"] += 1
                     self._cache[local]["service"] = dict(
                         event_id=stamp.event_ids[index], content=self._local_content(content, index), receipt=item
                     )
         pending.update(receipts=tuple(receipts), serviced=True)
         self.mutation_revision += 1
         return tuple(receipts)
 
     @_serialized
+    @_observation_boundary
     def prepare_completion(
         self,
         *,
         accepted: WorldAcceptedEpisode,
         boundary_key: int,
         completion_content: Any,
         outcomes: tuple[LaneOutcome, ...],
         participated_world_ids: tuple[str, ...],
     ) -> PreparedBankCompletion:
         self._healthy()
@@ -539,76 +695,93 @@ class CuriosityBank:
                 "outcome accepted identity mismatch",
             )
         # Metadata-only size pass; admission precedes outcome cloning/candidates.
         outcome_bytes = sum(
             value.numel() * value.element_size()
             for event in outcomes
             for value in (event.outcome.final_observation, event.outcome.final_meters)
         )
         if self._prepared is not None:
             prepared = self._prepared
-            canonical = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in (freeze_lane_outcome(event) for event in outcomes))
             _require(
                 prepared.accepted is accepted
                 and prepared.boundary_key == boundary_key
-                and _same(prepared.completion_content, completion_content)
-                and _same(canonical, completion_content),
+                and _same(self._completion_payload["completion_content"], completion_content)
+                and len(outcomes) == len(self._completion_outcomes),
                 "changed pending completion",
             )
+            _require(
+                all(_same_outcome(event, owned) for event, owned in zip(outcomes, self._completion_outcomes, strict=True)),
+                "changed pending outcome",
+            )
             return prepared
         _require(all(self._cursor[world]["disposition"] is None for world in self.world_ids), "episode already disposed")
         self._report(self._allocation("complete", len(participants), outcome_bytes))
         for event in outcomes:
             lane_outcome_state(event)
         canonical = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in (freeze_lane_outcome(event) for event in outcomes))
         _require(_same(canonical, completion_content), "completion content must contain exact full canonical payload and fingerprint")
+        owned_outcomes = deepcopy(outcomes)
         values: dict[str, tuple[list[float], float]] = {}
         observed = False
         try:
             if self.policy.strategy == "adaptive_rnd":
-                groups = [(event.world_id, (event,)) for event in outcomes] if self.scope == "per_world" else [(participants[0], outcomes)]
+                groups: list[tuple[str, tuple[LaneOutcome, ...]]]
+                if self.scope == "per_world":
+                    groups = [(event.world_id, (event,)) for event in outcomes]
+                else:
+                    groups = [(participants[0], outcomes)]
                 for world, events in groups:
 
                     def candidate(backend: Any) -> Any:
                         offside = copy(backend)
                         offside.survival_history = list(backend.survival_history)
                         try:
                             for event in events:
                                 offside.update_on_episode_end(event.outcome.survival_time)
                         except ValueError as error:
                             return (False, str(error))
                         return (True, (list(offside.survival_history), offside.current_intrinsic_weight))
 
                     observed = True
                     result = self._call(world, candidate)
-                    _require(result[0], result[1] if not result[0] else "")
+                    if not result[0]:
+                        raise _CandidateRefusalError(result[1])
                     values[world] = result[1]
         except BaseException:
             if observed:
                 self.mutation_revision += 1
             raise
-        dispositions = tuple((world, "completed" if world in participants else "retired_nonparticipating") for world in accepted.world_ids)
+        disposition_rows = []
+        for world in accepted.world_ids:
+            disposition = "retired_nonparticipating"
+            if world in participants:
+                disposition = "completed"
+            disposition_rows.append((world, disposition))
+        dispositions = tuple(disposition_rows)
         payload = dict(
             accepted=accepted,
             boundary_key=boundary_key,
             completion_content=canonical,
             participated_world_ids=participants,
             dispositions=dispositions,
         )
+        self._publications += 1
         receipt = self._issuer.issue(kind="prepared_dispositions", payload=payload)
         self.mutation_revision += 1
         prepared = PreparedBankCompletion(
             self, self.mutation_revision, accepted, boundary_key, canonical, participants, dispositions, deepcopy(values), receipt, False
         )
         self._prepared = prepared
         # Publication data is bank-owned, separate from the returned opaque token.
         self._completion_values, self._completion_payload = values, payload
+        self._completion_outcomes = owned_outcomes
         return prepared
 
     @_serialized
     def commit_completion(self, *, prepared: PreparedBankCompletion) -> WorldOwnerReceipt:
         self._healthy()
         _require(isinstance(prepared, PreparedBankCompletion) and prepared.destination is self, "foreign completion token")
         self._auth(prepared.accepted)
         if self._committed is not None and self._committed[0] is prepared:
             return self._committed[1]
         _require(self._prepared is prepared and not prepared.used and prepared.revision == self.mutation_revision, "stale completion token")
@@ -624,25 +797,31 @@ class CuriosityBank:
             for world, (history, weight) in self._completion_values.items():
 
                 def publish(backend: Any) -> None:
                     backend.survival_history = history
                     backend.current_intrinsic_weight = weight
 
                 self._call(world, publish)
             receipt = self._issuer.issue(kind="dispositions", payload=payload)
             for world, disposition in prepared.dispositions:
                 self._cursor[world]["disposition"] = disposition
-                index = prepared.participated_world_ids.index(world) if world in prepared.participated_world_ids else None
+                if world in prepared.participated_world_ids:
+                    index = prepared.participated_world_ids.index(world)
+                else:
+                    index = None
+                local_completion = None
+                if index is not None:
+                    local_completion = prepared.completion_content[index]
                 self._cache[world]["completion"] = dict(
                     episode=self._cursor[world]["accepted_episode_seq"],
                     disposition=disposition,
-                    content=None if index is None else prepared.completion_content[index],
+                    content=local_completion,
                 )
         except BaseException:
             self._failed = True
             raise
         prepared.used = True
         self._prepared = None
         self._committed = (prepared, receipt)
         self._completion_values = {}
         self.mutation_revision += 1
         return receipt
@@ -669,45 +848,50 @@ class CuriosityBank:
             return
         self._quarantine = (accepted, reason)
         self._failed = True
         self.mutation_revision += 1
 
     @_serialized
     def snapshot_world(self, *, world_id: str) -> dict[str, Any]:
         self._available()
         _require(type(world_id) is str and world_id in self._cursor, "unknown exact world ID")
         try:
-            backend = self._owners[world_id].snapshot() if self.scope == "per_world" else deepcopy(self._shared.checkpoint_state())
+            if self.scope == "per_world":
+                backend = self._owners[world_id].snapshot()
+            else:
+                backend = deepcopy(self._shared.checkpoint_state())
         except BaseException:
             self._failed = True
             raise
         finally:
             self.mutation_revision += 1
         accepted = self._accepted
-        identity = (
-            None
-            if accepted is None
-            else dict(
+        if accepted is None:
+            identity = None
+        else:
+            identity = dict(
                 batch_episode=accepted.batch_episode,
                 world_ids=list(accepted.world_ids),
                 world_episode_seqs=list(accepted.world_episode_seqs),
             )
-        )
         pending = None
         if self._pending is not None and not self._pending["serviced"]:
             assert accepted is not None
             index = accepted.world_ids.index(world_id)
             if bool(self._pending["active"][index]):
+                local_context = None
+                if self._pending["context"] is not None:
+                    local_context = self._local_content(self._pending["context"], index)
                 pending = dict(
                     event_id=self._pending["stamp"].event_ids[index],
                     vector_tick=self._pending["tick"],
-                    context=None if self._pending["context"] is None else self._local_content(self._pending["context"], index),
+                    context=local_context,
                 )
         return dict(
             schema="curiosity-bank-world-v1",
             scope=self.scope,
             world_id=world_id,
             policy_identity=self.policy.policy_identity,
             descriptor=self.descriptor.to_dict(),
             backend=backend,
             curiosity_epoch=0,
             accepted_identity=identity,
diff --git a/tests/test_townlet/regressions/bac/test_pw_private_bank.py b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
index f78bbda6..7be710f7 100644
--- a/tests/test_townlet/regressions/bac/test_pw_private_bank.py
+++ b/tests/test_townlet/regressions/bac/test_pw_private_bank.py
@@ -401,21 +401,21 @@ def test_all_inactive_shared_call_does_not_service_pending_tail(harness_factory:
     _equal(before["backend"], h.bank.snapshot_world(world_id="world1")["backend"])
 
 
 def test_completion_preserves_nonempty_gradients_and_tail(harness_factory: Any) -> None:
     h = harness_factory("adaptive_rnd")
     for tick in range(1, 8):
         _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
     before = {world: _inspect(h.bank, world, "adaptive_rnd") for world in WORLD_IDS}
     for value in before.values():
         assert any(gradient is not None and bool(gradient.ne(0).any()) for gradient in value["gradients"])
-        assert value["native"]["rnd_state"]["predictor_service"]["pending_observations"]
+        assert value["native"]["rnd_state"]["predictor_service"]["pending_observations"].shape[0] > 0
     prepared = _completion(h.bank, h.accepted, WORLD_IDS, 7)
     assert _completion(h.bank, h.accepted, WORLD_IDS, 7) is prepared
     with pytest.raises(ValueError):
         _completion(h.bank, h.accepted, WORLD_IDS, 6)
     with pytest.raises((ValueError, RuntimeError)):
         h.bank.snapshot_world(world_id="world0")
     committed = h.bank.commit_completion(prepared=prepared)
     assert h.bank.commit_completion(prepared=prepared) is committed
     WorldReceiptIssuer.validate(committed, "dispositions", h.bank)
     assert committed.payload["dispositions"] == tuple((world, "completed") for world in WORLD_IDS)
@@ -1144,10 +1144,205 @@ def test_exact_whitespace_world_id_survives_real_completion(harness_factory: Any
 
 def test_quarantine_refuses_cached_completion_success(harness_factory: Any) -> None:
     h = harness_factory("adaptive_rnd")
     _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
     prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
     receipt = h.bank.commit_completion(prepared=prepared)
     assert h.bank.commit_completion(prepared=prepared) is receipt
     h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
     with pytest.raises((RuntimeError, ValueError)):
         h.bank.commit_completion(prepared=prepared)
+
+
+@pytest.mark.parametrize("phase", ("reward", "service"))
+def test_post_provider_publication_failure_quarantines_real_effect(harness_factory: Any, monkeypatch: Any, phase: str) -> None:
+    h = harness_factory("rnd")
+    prefix = (1, 2, 3) if phase == "service" else (1, 2)
+    for tick in prefix:
+        _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
+    next_tick = len(prefix) + 1
+    context = _context(next_tick, (True, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(
+        accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=next_tick
+    )
+    if phase == "service":
+        h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+    before = h.bank._owners["world0"].snapshot()["backend"]
+    if phase == "service":
+        # Actual B2 cadence: admissions1/2 already produced update1; admission3
+        # leaves one row. Admission4 must consume that tail in update2.
+        service = before["predictor_service"]
+        assert service["optimizer_updates"] == 1
+        assert service["pending_observations"].shape[0] == 1
+        assert h.policy.predictor_batch_size == 2
+    calls: list[str] = []
+
+    def publication_fault(*args: Any, **kwargs: Any) -> None:
+        calls.append(phase)
+        raise RuntimeError("injected post-provider publication allocation failure")
+
+    module = importlib.import_module(BANK_MODULE)
+    target = "CuriosityReward" if phase == "reward" else "WorldServiceReceipt"
+    with monkeypatch.context() as patch:
+        patch.setattr(module, target, publication_fault)
+        with pytest.raises(RuntimeError, match="injected post-provider"):
+            if phase == "reward":
+                h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True)
+            else:
+                h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted)
+    assert calls == [phase]
+    after = h.bank._owners["world0"].snapshot()["backend"]
+    if phase == "reward":
+        assert after["reward_rms_count"] > before["reward_rms_count"]
+    else:
+        assert after["predictor_service"]["optimizer_updates"] > before["predictor_service"]["optimizer_updates"]
+        assert any(not torch.equal(a, b) for a, b in zip(_learned(before, "rnd"), _learned(after, "rnd"), strict=True))
+        old_moments, new_moments = before["optimizer"]["state"], after["optimizer"]["state"]
+        assert any(not torch.equal(old_moments[key]["exp_avg"], value["exp_avg"]) for key, value in new_moments.items())
+        assert any(bool(value["exp_avg"].ne(0).any()) for value in new_moments.values())
+    for retry in (
+        lambda: h.bank.reward(context=context, stamp=stamp, accepted=h.accepted, update_stats=True),
+        lambda: h.bank.admit_and_service(context=context, stamp=stamp, accepted=h.accepted),
+    ):
+        with pytest.raises((ValueError, RuntimeError), match="quarantin"):
+            retry()
+
+
+def test_completion_receipt_failure_after_observation_tracks_revision(harness_factory: Any, monkeypatch: Any) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    before = {world: h.bank._owners[world].snapshot() for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+
+    def fail_issue(*, kind: str, payload: Any) -> Any:
+        assert kind == "prepared_dispositions"
+        raise RuntimeError("injected completion receipt allocation failure")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(h.bank._issuer, "issue", fail_issue)
+        with pytest.raises(RuntimeError, match="injected completion receipt"):
+            _completion(h.bank, h.accepted, WORLD_IDS, 1)
+    assert h.bank.mutation_revision == revision + 1
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank._owners[world].snapshot())
+    assert h.bank._prepared is None
+
+
+@pytest.mark.parametrize("retry", ("equal", "changed_content", "changed_outcome", "changed_tensor"))
+def test_pending_completion_refuses_or_replays_before_codec_allocation(harness_factory: Any, monkeypatch: Any, retry: str) -> None:
+    h = harness_factory("adaptive_rnd")
+    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
+    outcomes = _outcomes(h.accepted, WORLD_IDS, 1)
+    content = _content(outcomes)
+    prepared = h.bank.prepare_completion(
+        accepted=h.accepted,
+        boundary_key=h.accepted.batch_episode,
+        completion_content=content,
+        outcomes=outcomes,
+        participated_world_ids=WORLD_IDS,
+    )
+    assert prepared.completion_content == content
+    assert all(bytes.fromhex(payload).hex() == payload and len(fingerprint) == 64 for payload, fingerprint in content)
+    if retry == "changed_content":
+        content = ((content[0][0], "0" * 64), content[1])
+    elif retry == "changed_outcome":
+        outcomes = (outcomes[0], replace(outcomes[1], reward_total=9.0))
+    elif retry == "changed_tensor":
+        outcomes[1].outcome.final_observation.add_(1)
+    revision = h.bank.mutation_revision
+    effects: list[str] = []
+
+    def forbidden(*args: Any, **kwargs: Any) -> Any:
+        effects.append("unexpected allocation/owner observation")
+        raise RuntimeError("pending preparation performed new codec/report/owner work")
+
+    with monkeypatch.context() as patch:
+        patch.setattr(importlib.import_module(BANK_MODULE), "freeze_lane_outcome", forbidden)
+        patch.setattr(importlib.import_module(BANK_MODULE), "lane_outcome_state", forbidden)
+        patch.setattr(h.bank, "_report", forbidden)
+        for world in WORLD_IDS:
+            patch.setattr(h.bank._owners[world], "call", forbidden)
+        if retry == "equal":
+            assert (
+                h.bank.prepare_completion(
+                    accepted=h.accepted,
+                    boundary_key=h.accepted.batch_episode,
+                    completion_content=content,
+                    outcomes=outcomes,
+                    participated_world_ids=WORLD_IDS,
+                )
+                is prepared
+            )
+        else:
+            with pytest.raises(ValueError):
+                h.bank.prepare_completion(
+                    accepted=h.accepted,
+                    boundary_key=h.accepted.batch_episode,
+                    completion_content=content,
+                    outcomes=outcomes,
+                    participated_world_ids=WORLD_IDS,
+                )
+    assert effects == []
+    assert h.bank.mutation_revision == revision
+    h.bank.commit_completion(prepared=prepared)
+
+
+def _spectator_variant(context: IntrinsicTransitionContext, *, own: bool, tick: int) -> IntrinsicTransitionContext:
+    predecessor, successor, actions = context.predecessor, context.successor, context.actions
+    row = 1 if own else 0
+    predecessor[row] += 100
+    successor[row] -= 50
+    actions[row] = 1 - actions[row]
+    return IntrinsicTransitionContext(
+        predecessor=predecessor, actions=actions, successor=successor, active_on_entry=context.active_on_entry, vector_tick=tick
+    )
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+def test_private_last_local_replay_survives_inactive_source_and_other_world_activity(
+    harness_factory: Any, monkeypatch: Any, family: str
+) -> None:
+    h = harness_factory(family)
+    original = _context(1, (False, True), 3, 0.0)
+    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=original.active_on_entry, vector_tick=1)
+    reward = h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+    changed_spectator = _spectator_variant(original, own=False, tick=1)
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    replay = h.bank.reward(context=changed_spectator, stamp=stamp, accepted=h.accepted, update_stats=True)
+    _equal(reward.raw, replay.raw)
+    assert h.bank.mutation_revision == revision
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    h.bank.admit_and_service(context=changed_spectator, stamp=stamp, accepted=h.accepted)
+    _step(h.bank, h.accepted, _context(2, (True, False), 3, 10.0))
+    before = {world: h.bank.snapshot_world(world_id=world) for world in WORLD_IDS}
+    revision = h.bank.mutation_revision
+    effects: list[str] = []
+
+    def forbidden(*args: Any, **kwargs: Any) -> Any:
+        effects.append("provider call")
+        raise RuntimeError("cached local replay invoked a provider")
+
+    with monkeypatch.context() as patch:
+        for world in WORLD_IDS:
+            patch.setattr(h.bank._owners[world], "call", forbidden)
+        replay = h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+        receipts = h.bank.admit_and_service(context=original, stamp=stamp, accepted=h.accepted)
+        _equal(reward.raw, replay.raw)
+        assert replay.raw[0] == 0 and not receipts[0].eligible
+        assert receipts[0].admitted_rows == receipts[0].optimizer_updates == 0
+        for bad, mode in (
+            (_spectator_variant(original, own=True, tick=1), True),
+            (original, False),
+            (_spectator_variant(original, own=False, tick=2), True),
+        ):
+            with pytest.raises(ValueError):
+                h.bank.reward(context=bad, stamp=stamp, accepted=h.accepted, update_stats=mode)
+    assert effects == [] and h.bank.mutation_revision == revision
+    for world in WORLD_IDS:
+        _equal(before[world], h.bank.snapshot_world(world_id=world))
+    _step(h.bank, h.accepted, _context(3, (False, True), 3, 0.0))
+    before = h.bank.snapshot_world(world_id="world1")
+    with pytest.raises(ValueError):
+        h.bank.reward(context=original, stamp=stamp, accepted=h.accepted, update_stats=True)
+    _equal(before, h.bank.snapshot_world(world_id="world1"))
