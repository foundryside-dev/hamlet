 src/townlet/population/vectorized.py               | 587 +++++++++++++++++++--
 .../bac/test_parent_intrinsic_handoff.py           |  24 +-
 2 files changed, 572 insertions(+), 39 deletions(-)
diff --git a/src/townlet/population/vectorized.py b/src/townlet/population/vectorized.py
index dc24f275..0028be1b 100644
--- a/src/townlet/population/vectorized.py
+++ b/src/townlet/population/vectorized.py
@@ -82,20 +82,70 @@ ReplayStorage = ReplayBuffer | SequentialReplayBuffer | PrioritizedReplayBuffer
 @dataclass(frozen=True)
 class _VectorStep:
     vector_tick: int
     accepted: Any
     world_ids: tuple[str, ...]
     predecessor: torch.Tensor
     actions: torch.Tensor
     active_on_entry: torch.Tensor
 
 
+@dataclass(frozen=True, slots=True)
+class _PopulationReading:
+    accepted: Any
+    vector_tick: int
+    observation: torch.Tensor
+    env_dones: torch.Tensor
+    env_counts: torch.Tensor
+    completed: torch.Tensor
+    counts: torch.Tensor
+    action_masks: torch.Tensor | None
+
+
+@dataclass(slots=True)
+class _InitialDecision:
+    accepted: Any
+    reset: Any
+    retired_world_ids: tuple[str, ...]
+    retired: torch.Tensor
+    participation: Any
+
+
+@dataclass(slots=True)
+class _InitialReset:
+    record: Any
+    retired_world_ids: tuple[str, ...]
+    revision: int
+    before: _PopulationReading
+    intent: Any
+    prepared: Any
+    ready: Any
+    decision: _InitialDecision | None
+    candidate: _PopulationReading | None
+    observation: torch.Tensor
+    completed: torch.Tensor
+    next_revision: int
+
+
+@dataclass(frozen=True, slots=True)
+class _SelectionFrame:
+    accepted: Any
+    reset: Any
+    decision: _InitialDecision | None
+    prior: _PopulationReading | None
+    revision: int
+    observation: torch.Tensor
+    completed: torch.Tensor
+    counts: torch.Tensor
+    env_phase: str
+
+
 @dataclass(frozen=True)
 class _ReplaySetup:
     options: ReplayOptions
     min_transitions: int
     rng: np.random.Generator
     origin: str
     horizon: int
     horizon_origin: str
     tick: int
     preserve_global: bool
@@ -418,20 +468,25 @@ class VectorizedPopulation(PopulationManager):
         # Lane survival and completion state are cleared only by an explicit batch reset.
         self.episode_step_counts = torch.zeros(self.num_agents, dtype=torch.long, device=device)
         self.episode_completed = torch.zeros(self.num_agents, dtype=torch.bool, device=self.device)
         self.episode_completions: list[EpisodeCompletion | None] = [None for _ in range(self.num_agents)]
         self._clock_ledger = ClockLedger(vector_ticks=self.total_steps)
         self._clock_ledger_restore_unavailable = self.total_steps != 0
         self._accepted: Any = None
         self._activation: Any = None
         self._reset_stage: str | None = None
         self._reset_record: Any = None
+        self._initial_reset: _InitialReset | None = None
+        self._initial_decision: _InitialDecision | None = None
+        self._prior_reading: _PopulationReading | None = None
+        self._selection_frame: _SelectionFrame | None = None
+        self._step_inspection: object | None = None
         self._population_issuer: Any = None
         self._empty_evidence: Any = None
         self._vector_steps: dict[PreparedVectorStep, _VectorStep] = {}
         self._vector_stage: str | None = None
         self._vector_step_progress: dict[str, Any] | None = None
         self._step_active = False
         self._failed_step = False
         self._returned_step: dict[str, Any] | None = None
         self._service_receipts: tuple[Any, ...] = ()
         self._checkpoint_revision = 0
@@ -790,49 +845,320 @@ class VectorizedPopulation(PopulationManager):
         self.last_td_error, self.last_loss, self.last_q_values_mean = td_mean, loss.item(), q_mean
         self.last_training_step = self.total_steps
         if self.use_per:
             if self.is_recurrent:
                 cast(SequentialReplayBuffer, self.replay_buffer).update_priorities(batch.unit_ids, errors, loss_mask=batch.loss_mask)
             else:
                 handles = batch.unit_ids.detach().cpu().numpy().astype(np.int64, copy=True)
                 cast(PrioritizedReplayBuffer, self.replay_buffer).update_unit_priorities(handles, errors)
         self._log_network_histograms()
 
-    def reset(self, *, reservation: Any) -> tuple[Any, Any]:
+    def _require_operation_idle(self) -> None:
+        if (
+            self._step_active
+            or self._selection_frame is not None
+            or self._initial_reset is not None
+            or self._step_inspection is not None
+            or self._preparing_checkpoint is not None
+            or self._batch_commit_active
+        ):
+            raise RuntimeError("Reentrant population operation")
+
+    def _quarantine_participation(self, error: Exception) -> None:
+        self._failed_step, self._activation = True, None
+        if self._accepted is not None:
+            try:
+                self.env.abandon_episode(accepted=self._accepted, reason="runtime_failure")
+            except Exception as cleanup:
+                error.add_note(f"Population integrity quarantine: {cleanup!r}")
+
+    @staticmethod
+    def _same_reading(value: Any, owned: torch.Tensor) -> bool:
+        return (
+            isinstance(value, torch.Tensor)
+            and value.layout == torch.strided
+            and value.dtype == owned.dtype
+            and value.device == owned.device
+            and value.shape == owned.shape
+            and torch.equal(value, owned)
+        )
+
+    def _copy_reading(self, *, accepted: Any, observation: torch.Tensor, action_masks: torch.Tensor | None) -> _PopulationReading:
+        return _PopulationReading(
+            accepted,
+            self.total_steps,
+            observation.detach().clone(),
+            self.env.dones.detach().clone(),
+            self.env.step_counts.detach().clone(),
+            self.episode_completed.detach().clone(),
+            self.episode_step_counts.detach().clone(),
+            None if action_masks is None else action_masks.detach().clone(),
+        )
+
+    def _parent_reading_matches(self, reading: _PopulationReading) -> bool:
+        return all(
+            self._same_reading(value, owned)
+            for value, owned in (
+                (self.current_obs, reading.observation),
+                (self.episode_completed, reading.completed),
+                (self.episode_step_counts, reading.counts),
+            )
+        )
+
+    def _check_owned_state(self) -> _PopulationReading:
+        decision, prior = self._initial_decision, self._prior_reading
+        if (
+            decision is None
+            or prior is None
+            or self._accepted is not decision.accepted
+            or self._reset_record is not decision.reset
+            or prior.accepted is not decision.accepted
+            or prior.vector_tick != self.total_steps
+            or prior.action_masks is None
+        ):
+            error = RuntimeError("Owned episode lacks its genuine sealed population reading")
+            self._quarantine_participation(error)
+            raise error
+        retired_rows = torch.nonzero(decision.retired, as_tuple=False).flatten().tolist()
+        healthy = (
+            self._parent_reading_matches(prior)
+            and self._same_reading(self.env.dones, prior.env_dones)
+            and self._same_reading(self.env.step_counts, prior.env_counts)
+            and all(
+                bool(self.episode_completed[row])
+                and int(self.episode_step_counts[row]) == 0
+                and self.episode_completions[row] is None
+                and row not in self._episode_participants
+                and not bool(self._episode_entropy_present[row])
+                and not bool(self._episode_reward_totals[row].any())
+                and (not self.is_recurrent or not self.current_episodes[row]["observations"])
+                for row in retired_rows
+            )
+        )
+        if not healthy:
+            error = ValueError("Population state changed outside its owned transition boundary")
+            self._quarantine_participation(error)
+            raise error
+        return prior
+
+    def _validate_owned_training(self) -> _PopulationReading:
+        prior = self._check_owned_state()
+        assert self._initial_decision is not None
+        try:
+            self.env.validate_initial_participation(
+                accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
+            )
+        except Exception:
+            if self.env.world_phase == "quarantined":
+                self._failed_step, self._activation = True, None
+            raise
+        self._check_owned_state()
+        return prior
+
+    def _validate_owned_reading(self) -> _PopulationReading:
+        prior = self._check_owned_state()
+        assert self._initial_decision is not None
+        try:
+            self.env.validate_initial_participation_reading(
+                accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
+            )
+        except Exception:
+            if self.env.world_phase == "quarantined":
+                self._failed_step, self._activation = True, None
+            raise
+        self._check_owned_state()
+        return prior
+
+    def _begin_selection(self) -> _SelectionFrame:
+        self._require_operation_idle()
+        if self._failed_step or self._pending_batch_commit is not None or self._vector_steps or self._owned_reset_pending:
+            raise RuntimeError("Pending or failed population work cannot select actions")
+        owned = self._accepted is not None or self._initial_decision is not None or self._reset_record is not None
+        if owned:
+            self._check_owned_state()
+        frame = _SelectionFrame(
+            self._accepted,
+            self._reset_record,
+            self._initial_decision,
+            self._prior_reading,
+            self._checkpoint_revision,
+            self.current_obs.detach().clone(),
+            self.episode_completed.detach().clone(),
+            self.episode_step_counts.detach().clone(),
+            self.env.world_phase,
+        )
+        self._selection_frame = frame
+        try:
+            self._revalidate_selection(frame)
+            frame = replace(frame, revision=frame.revision + 1)
+            self._checkpoint_revision = frame.revision
+            self._selection_frame = frame
+            return frame
+        except Exception:
+            if self._selection_frame is frame:
+                self._selection_frame = None
+            raise
+
+    def _selection_changed(self, frame: _SelectionFrame) -> bool:
+        return (
+            self._selection_frame is not frame
+            or self._checkpoint_revision != frame.revision
+            or self._accepted is not frame.accepted
+            or self._reset_record is not frame.reset
+            or self._initial_decision is not frame.decision
+            or self._prior_reading is not frame.prior
+            or self._owned_reset_pending
+            or self._failed_step
+            or self.env.world_phase != frame.env_phase
+            or not self._same_reading(self.current_obs, frame.observation)
+            or not self._same_reading(self.episode_completed, frame.completed)
+            or not self._same_reading(self.episode_step_counts, frame.counts)
+        )
+
+    def _revalidate_selection(self, frame: _SelectionFrame) -> None:
+        if not self._selection_changed(frame) and frame.decision is not None:
+            self._validate_owned_reading()
+        if self._selection_changed(frame):
+            error = ValueError("Selection callback changed retained population custody")
+            self._quarantine_participation(error)
+            raise error
+
+    def _prepare_initial_participation(self, work: _InitialReset) -> None:
+        if self._initial_reset is not work or self._checkpoint_revision != work.revision:
+            raise RuntimeError("Stale private reset preparation")
+        work.intent = self._population_issuer.issue(
+            kind="initial_participation_intent",
+            payload=dict(
+                accepted=work.record.accepted,
+                world_ids=work.record.accepted.world_ids,
+                retired_world_ids=work.retired_world_ids,
+                population_revision=work.revision,
+            ),
+        )
+        work.prepared = self.env.prepare_initial_participation(accepted=work.record.accepted, intent=work.intent)
+        observation, masks = work.prepared.observation, work.prepared.action_masks
+        if (
+            not self._same_reading(observation, work.before.observation)
+            or not self._parent_reading_matches(work.before)
+            or masks.layout != torch.strided
+            or masks.shape != (self.num_agents, self.action_dim)
+            or masks.dtype != torch.bool
+            or masks.device != self.device
+            or work.prepared.retired_world_ids != work.retired_world_ids
+        ):
+            raise ValueError("Prepared initial participation changed reset readings or selected geometry")
+        retired = torch.tensor(
+            [world in work.retired_world_ids for world in work.record.accepted.world_ids], dtype=torch.bool, device=self.device
+        )
+        if bool(masks[retired].any()) or bool((~retired & ~masks.any(dim=1)).any()):
+            raise ValueError("Prepared masks disagree with the initial participation decision")
+        work.observation, work.completed = observation, retired.clone()
+        work.decision = _InitialDecision(work.record.accepted, work.record, work.retired_world_ids, retired.clone(), None)
+        work.candidate = _PopulationReading(
+            work.record.accepted,
+            self.total_steps,
+            observation.detach().clone(),
+            retired.clone(),
+            work.before.env_counts.clone(),
+            retired.clone(),
+            work.before.counts.clone(),
+            masks.detach().clone(),
+        )
+        work.ready = self._population_issuer.issue(
+            kind="initial_participation_ready",
+            payload=dict(accepted=work.record.accepted, intent=work.intent, prepared=work.prepared, population_revision=work.revision),
+        )
+
+    def _publish_initial_participation(self, work: _InitialReset) -> None:
+        decision, candidate = work.decision, work.candidate
+        if (
+            self._initial_reset is not work
+            or decision is None
+            or candidate is None
+            or self._checkpoint_revision != work.revision
+            or not self._parent_reading_matches(work.before)
+            or not self._same_reading(self.env.dones, work.before.env_dones)
+            or not self._same_reading(self.env.step_counts, work.before.env_counts)
+            or self._vector_steps
+            or self._completed_outcomes
+            or self._episode_participants
+            or any(value is not None for value in self.episode_completions)
+            or bool(self._episode_reward_totals.any())
+            or bool(self._episode_entropy_present.any())
+            or any(episode["observations"] for episode in self.current_episodes)
+        ):
+            raise ValueError("Population reset changed before initial participation publication")
+        result = self.env.commit_initial_participation(prepared=work.prepared, population_ready=work.ready)
+        # Assignment-only paired suffix: no clone, callback, receipt, validation or allocation.
+        decision.participation = result
+        self.current_obs = work.observation
+        self.episode_completed = work.completed
+        self._initial_decision = decision
+        self._prior_reading = candidate
+        self._checkpoint_revision = work.next_revision
+        self._initial_reset = None
+        self._reset_stage = "finalizing"
+
+    def reset(self, *, reservation: Any, retired_world_ids: tuple[str, ...]) -> tuple[Any, Any]:
         """Reset all environments and state."""
         from townlet.environment.vectorized_env import WorldReceiptIssuer
 
+        self._require_operation_idle()
         if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
             raise RuntimeError("A running or failed population attempt requires healthy boundary recovery")
+        if self._vector_steps:
+            raise RuntimeError("Resolve the pending vector step before reset")
         pending = (self.episode_step_counts > 0) & ~self.episode_completed
         if bool(pending.any()):
             raise RuntimeError("Complete pending lanes with an explicit stop reason before reset")
         binding = self._owned_episode
         if binding is None or (reservation.batch_episode, reservation.world_ids, reservation.world_episode_seqs) != (
             binding[0],
             binding[2],
             binding[3],
         ):
             raise ValueError("Reset reservation must match the explicitly begun population episode")
+        if (
+            type(retired_world_ids) is not tuple
+            or any(type(world) is not str or not world for world in retired_world_ids)
+            or len(set(retired_world_ids)) != len(retired_world_ids)
+            or tuple(world for world in binding[2] if world in retired_world_ids) != retired_world_ids
+        ):
+            raise ValueError("Retired world IDs must be an exact ordered unique subset of the bound roster")
+        if (
+            self._reset_record is not None
+            and self._reset_record.accepted is self._accepted
+            and (self._accepted.batch_episode, self._accepted.world_ids, self._accepted.world_episode_seqs)
+            == (binding[0], binding[2], binding[3])
+        ):
+            self._validate_owned_reading()
+            if self._initial_decision is None or retired_world_ids != self._initial_decision.retired_world_ids:
+                raise ValueError("An accepted reset cannot change its sealed initial decision")
         previous_stage = self._reset_stage
         self._reset_stage, self._step_active = "preparing", True
         record = None
         try:
             record = self.env.reset(reservation=reservation)
             self._reset_record = record
             if record.accepted is self._accepted:
                 if previous_stage != "completed" or self._activation is None:
                     raise RuntimeError("Accepted reset has no completed population preparation")
                 self._reset_stage = "completed"
                 return record, self._activation
             observation = record.observation
-            if observation.shape != self.current_obs.shape or observation.dtype != torch.float32 or observation.device != self.device:
+            if (
+                observation.layout != torch.strided
+                or observation.shape != self.current_obs.shape
+                or observation.dtype != torch.float32
+                or observation.device != self.device
+                or not bool(torch.isfinite(observation).all())
+            ):
                 raise ValueError("Reset observation disagrees with the selected population geometry")
             if self._population_issuer is None:
                 self._population_issuer = WorldReceiptIssuer(owner=self)
             self.current_obs = observation.detach().clone()
             self._empty_evidence, self._vector_steps, self._vector_stage = None, {}, None
             self._episode_participants = set()
             self._checkpoint_revision += 1
             self.episode_step_counts.zero_()
             self.episode_completed.zero_()
             self.episode_completions = [None for _ in range(self.num_agents)]
@@ -840,39 +1166,74 @@ class VectorizedPopulation(PopulationManager):
             self._completed_outcomes = ()
             self._episode_reward_totals.zero_()
             self._episode_entropies.zero_()
             self._episode_entropy_present.zero_()
             if self.is_recurrent:
                 recurrent_network = cast(RecurrentTokenQNetwork, self.q_network)
                 self.rollout_hidden = recurrent_network.initial_hidden(self.num_agents, self.device)
                 self.current_episodes = [self._new_episode_container() for _ in range(self.num_agents)]
             for agent_idx in range(self.num_agents):
                 self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=0)
-            self.sync_exploration_metrics()
+            self._publish_exploration_metrics()
             self._sync_curriculum_metrics()
+            before = self._copy_reading(accepted=record.accepted, observation=self.current_obs, action_masks=None)
+            work = _InitialReset(
+                record,
+                retired_world_ids,
+                self._checkpoint_revision,
+                before,
+                None,
+                None,
+                None,
+                None,
+                None,
+                self.current_obs,
+                self.episode_completed,
+                self._checkpoint_revision + 1,
+            )
+            self._initial_reset = work
+            self._prepare_initial_participation(work)
+            self._publish_initial_participation(work)
             activation = self._population_issuer.issue(kind="activation", payload={"accepted": record.accepted})
+            if (
+                work.candidate is None
+                or self._prior_reading is not work.candidate
+                or self._initial_decision is not work.decision
+                or self._reset_record is not record
+                or self._checkpoint_revision != work.next_revision
+                or self._failed_step
+                or not self._parent_reading_matches(work.candidate)
+            ):
+                raise ValueError("Activation finalization changed the paired population publication")
+            assert work.decision is not None
+            self.env.validate_initial_participation_reading(
+                accepted=record.accepted, participation=work.decision.participation, predecessor=work.candidate.observation
+            )
             self._accepted, self._activation = record.accepted, activation
             self._reset_stage = "completed"
             return record, activation
         except Exception as error:
             self._reset_stage, self._failed_step, self._activation = "failed", True, None
             if record is not None:
                 try:
                     self.env.abandon_episode(accepted=record.accepted, reason="runtime_failure")
                 except Exception as quarantine_error:
                     error.add_note(f"Reset quarantine failed: {quarantine_error!r}")
             raise
         finally:
+            self._initial_reset = None
             self._step_active = False
 
     def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
         """Attest actual zero participation without completing or clearing any work."""
+        self._require_operation_idle()
+        self._check_owned_state()
         self.env.validate_accepted_episode(accepted=accepted)
         if self._pending_batch_commit is not None:
             raise RuntimeError("Resolve the pending batch commitment before another transition")
         if accepted is None or accepted is not self._accepted or self._population_issuer is None:
             raise ValueError("Empty evidence requires this population's actual activated acceptance")
         if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._vector_steps:
             raise RuntimeError("Running, failed or pending population work cannot attest an empty episode")
         if self._owned_reset_pending or bool((self.episode_step_counts != 0).any()) or bool((self.env.step_counts != 0).any()):
             raise RuntimeError("A participating or unprepared episode is not empty")
         if self._completed_outcomes or any(episode["observations"] for episode in self.current_episodes):
@@ -894,27 +1255,30 @@ class VectorizedPopulation(PopulationManager):
     def _accepted_identity(accepted: Any) -> dict[str, Any]:
         return dict(
             batch_episode=accepted.batch_episode, world_ids=list(accepted.world_ids), world_episode_seqs=list(accepted.world_episode_seqs)
         )
 
     def _step_record(
         self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
     ) -> _VectorStep:
         if (
             self._preparing_checkpoint is not None
+            or self._selection_frame is not None
+            or self._initial_reset is not None
             or self._failed_step
             or self._owned_reset_pending
             or accepted is not self._accepted
             or accepted is None
         ):
             raise RuntimeError("Step requires this population's healthy accepted reset")
         self.env.validate_accepted_episode(accepted=accepted)
+        self._validate_owned_training()
         if self._pending_batch_commit is not None:
             raise RuntimeError("Resolve the pending batch commitment before another transition")
         if (
             type(self.total_steps) is not int
             or self._clock_ledger_restore_unavailable
             or self._clock_ledger.vector_ticks != self.total_steps
         ):
             raise ValueError("Next step requires the authoritative complete parent vector position")
         if type(world_ids) is not tuple or world_ids != accepted.world_ids:
             raise ValueError("Step world order must equal the actual accepted binding")
@@ -959,20 +1323,34 @@ class VectorizedPopulation(PopulationManager):
                     (left.actions, right.actions),
                     (left.active_on_entry, right.active_on_entry),
                 )
             )
         )
 
     def prepare_vector_step(
         self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
     ) -> PreparedVectorStep:
         """Own a pure candidate; equal pending preparation retains its issued identity."""
+        self._require_operation_idle()
+        inspection = object()
+        self._step_inspection = inspection
+        try:
+            return self._prepare_vector_step(
+                accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
+            )
+        finally:
+            if self._step_inspection is inspection:
+                self._step_inspection = None
+
+    def _prepare_vector_step(
+        self, *, accepted: Any, world_ids: tuple[str, ...], predecessor: torch.Tensor, actions: torch.Tensor, active_on_entry: torch.Tensor
+    ) -> PreparedVectorStep:
         record = self._step_record(
             accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
         )
         if self._vector_steps:
             handle, pending = next(iter(self._vector_steps.items()))
             if self._vector_stage != "prepared" or not self._same_step(pending, record):
                 raise ValueError("Pending step cannot be replaced or executed twice")
             return handle
         handle = PreparedVectorStep()
         self._vector_steps = {handle: record}
@@ -983,20 +1361,47 @@ class VectorizedPopulation(PopulationManager):
         self,
         *,
         prepared: PreparedVectorStep,
         accepted: Any,
         world_ids: tuple[str, ...],
         predecessor: torch.Tensor,
         actions: torch.Tensor,
         active_on_entry: torch.Tensor,
     ) -> int:
         """Authenticate exactly one prephysics execution of an issued candidate."""
+        if self._step_inspection is not None:
+            raise RuntimeError("Reentrant population step inspection")
+        inspection = object()
+        self._step_inspection = inspection
+        try:
+            return self._claim_vector_step(
+                prepared=prepared,
+                accepted=accepted,
+                world_ids=world_ids,
+                predecessor=predecessor,
+                actions=actions,
+                active_on_entry=active_on_entry,
+            )
+        finally:
+            if self._step_inspection is inspection:
+                self._step_inspection = None
+
+    def _claim_vector_step(
+        self,
+        *,
+        prepared: PreparedVectorStep,
+        accepted: Any,
+        world_ids: tuple[str, ...],
+        predecessor: torch.Tensor,
+        actions: torch.Tensor,
+        active_on_entry: torch.Tensor,
+    ) -> int:
         if type(prepared) is not PreparedVectorStep or prepared not in self._vector_steps or self._vector_stage != "prepared":
             raise ValueError("Foreign, consumed or already executing vector step")
         candidate = self._step_record(
             accepted=accepted, world_ids=world_ids, predecessor=predecessor, actions=actions, active_on_entry=active_on_entry
         )
         record = self._vector_steps[prepared]
         if not self._same_step(record, candidate):
             raise ValueError("Claim changed the owned vector step")
         participants = self._episode_participants | set(torch.nonzero(record.active_on_entry, as_tuple=False).flatten().tolist())
         self._episode_participants = participants
@@ -1015,36 +1420,42 @@ class VectorizedPopulation(PopulationManager):
 
     @property
     def completed_outcomes(self) -> tuple[LaneOutcome, ...]:
         """Independent owned readings of this explicitly begun episode's events."""
         # LaneOutcome construction clones its embedded DTO tensors. Each sink
         # receives its own readings and cannot mutate POP's canonical authority.
         return tuple(replace(event) for event in self._completed_outcomes)
 
     def bind_episode_worlds(self, *, world_ids: Sequence[str], world_episode_seqs: Sequence[int]) -> None:
         """Own actual caller identities, never infer them from row, batch or tick."""
+        self._require_operation_idle()
+        if self._failed_step or self._vector_steps:
+            raise RuntimeError("Failed or pending population work cannot change world binding")
         if self._preparing_checkpoint is not None or self._step_active or self._pending_batch_commit is not None:
             raise RuntimeError("Reentrant population binding")
         ids, sequences = tuple(world_ids), tuple(world_episode_seqs)
         if len(ids) != self.num_agents or len(sequences) != self.num_agents:
             raise ValueError("World identity binding must contain exactly one entry per lane")
         if any(not isinstance(world, str) or not world.strip() for world in ids) or len(set(ids)) != len(ids):
             raise ValueError("World IDs must be unique concrete nonempty strings")
         if any(type(sequence) is not int or sequence < 0 for sequence in sequences):
             raise ValueError("World episode sequences must be explicit nonnegative integers")
         if self._owned_reset_pending or bool(((self.episode_step_counts > 0) & ~self.episode_completed).any()):
             raise RuntimeError("Complete the current episode before binding another episode")
         self._next_world_binding = ids, sequences
         self._checkpoint_revision += 1
 
     def begin_batch_episode(self, index: int, planned_horizon: int) -> None:
         """Pin fresh caller binding before the next population reset and rollout."""
+        self._require_operation_idle()
+        if self._failed_step or self._vector_steps:
+            raise RuntimeError("Failed or pending population work cannot begin an episode")
         if self._preparing_checkpoint is not None or self._step_active or self._pending_batch_commit is not None:
             raise RuntimeError("Reentrant population episode entry")
         if type(index) is not int or index < 0 or type(planned_horizon) is not int or planned_horizon < 1:
             raise ValueError("Batch index/horizon must be nonnegative/positive integers")
         if self._next_world_binding is None:
             raise RuntimeError("Bind concrete world IDs and episode sequences before beginning each owned episode")
         if self._owned_reset_pending or bool(((self.episode_step_counts > 0) & ~self.episode_completed).any()):
             raise RuntimeError("Complete the current episode before beginning another episode")
         if index in self._begun_batch_ids:
             raise ValueError("A batch episode identity cannot be reused")
@@ -1090,20 +1501,21 @@ class VectorizedPopulation(PopulationManager):
         if (
             participants
             and set(participants) == self._episode_participants
             and all(bool(self.episode_completed[lane]) for lane in participants)
             and all(bool(self.env.dones[lane]) for lane in range(self.num_agents) if lane not in participants)
         ):
             self._batch_participants[self._owned_episode[0]] = participants
 
     def commit_episode_outcomes(self, outcomes: Sequence[LaneOutcome]) -> None:
         """Retain exact child retry custody; publish parent completion only after its return."""
+        self._require_operation_idle()
         if (
             self._step_active
             or self._failed_step
             or self._preparing_checkpoint is not None
             or self._batch_commit_active
             or self._vector_steps
         ):
             raise RuntimeError("Cannot commit outcomes during running, pending or failed population work")
         incoming = tuple(outcomes)
         prepared: dict[tuple[int, int], str] = {}
@@ -1468,22 +1880,26 @@ class VectorizedPopulation(PopulationManager):
         """Convert curriculum difficulty (0.0-1.0) to discrete stage (1-5)."""
         stage = int(round(difficulty_level * 4.0)) + 1
         return max(1, min(5, stage))
 
     def sync_exploration_metrics(self) -> None:
         """
         Synchronise exploration parameters (epsilon, intrinsic weight) to registry.
 
         Also refreshes current_epsilons to keep action selection in sync with telemetry.
         """
-        if self._preparing_checkpoint is not None:
+        self._require_operation_idle()
+        if self._failed_step or self._pending_batch_commit is not None or self._vector_steps or self._owned_reset_pending:
             raise RuntimeError("Reentrant population telemetry publication")
+        self._publish_exploration_metrics()
+
+    def _publish_exploration_metrics(self) -> None:
         epsilon_tensor = torch.full(
             (self.num_agents,),
             self._get_current_epsilon_value(),
             dtype=torch.float32,
             device=self.device,
         )
         self.current_epsilons = epsilon_tensor
 
         for idx in range(self.num_agents):
             self.runtime_registry.set_epsilon(agent_idx=idx, epsilon=epsilon_tensor[idx])
@@ -1526,95 +1942,130 @@ class VectorizedPopulation(PopulationManager):
         self.episode_completions[agent_idx] = completion
         if envelope is not None:
             # Pin authoritative content at publication, before any public read.
             # Fingerprints survive accepted resets so delayed/partial commits
             # retain authority without retaining every episode's tensor payloads.
             identity = envelope.batch_episode, envelope.outcome.agent_idx
             self._published_outcome_fingerprints[identity] = self._outcome_fingerprint(envelope)
             self._published_events[identity] = replace(envelope)
             self._completed_outcomes = (*self._completed_outcomes, envelope)
         self.runtime_registry.record_survival_time(agent_idx=agent_idx, steps=survival_time)
-        self.sync_exploration_metrics()
+        self._publish_exploration_metrics()
         self._reset_hidden_state(agent_idx)
         self._retain_participant_roster()
         return completion
 
     def flush_episode(self, agent_idx: int, reason: RunnerCompletionReason) -> EpisodeCompletion | None:
         """Complete a surviving lane for an explicit external stop without changing replay done."""
+        self._require_operation_idle()
         if self._preparing_checkpoint is not None or self._step_active or self._failed_step or self._pending_batch_commit is not None:
             raise RuntimeError("Cannot flush during running, restoring or failed population work")
-        self._checkpoint_revision += 1
-        return self._finalize_episode(agent_idx, reason)
+        if self._vector_steps or self._owned_reset_pending:
+            raise RuntimeError("Complete pending population work before flushing")
+        self._step_active = True
+        try:
+            prior = self._validate_owned_training()
+            completed = prior.completed.clone()
+            if int(prior.counts[agent_idx]) > 0:
+                completed[agent_idx] = True
+            candidate = replace(prior, completed=completed)
+            self._checkpoint_revision += 1
+            try:
+                result = self._finalize_episode(agent_idx, reason)
+                assert self._initial_decision is not None
+                self.env.validate_initial_participation(
+                    accepted=prior.accepted, participation=self._initial_decision.participation, predecessor=prior.observation
+                )
+                if not self._parent_reading_matches(candidate):
+                    raise ValueError("Flush callback changed the owned population reading")
+                self._prior_reading = candidate
+                self._check_owned_state()
+                return result
+            except Exception as error:
+                self._quarantine_participation(error)
+                raise
+        finally:
+            self._step_active = False
 
     def select_greedy_actions(self, env: VectorizedHamletEnv) -> torch.Tensor:
         """
         Select greedy actions with action masking for inference.
 
         This is the canonical way to select actions during inference.
         Uses the same action masking logic as training to prevent boundary violations.
 
         Args:
             env: Environment to get action masks from
 
         Returns:
             actions: [num_agents] tensor of selected actions
         """
-        if self._preparing_checkpoint is not None or self._step_active or self._failed_step or self._pending_batch_commit is not None:
-            raise RuntimeError("Reentrant or failed population selection")
-        self._checkpoint_revision += 1
-        with torch.no_grad():
-            eligible = ~env.dones & ~self.episode_completed
-            q_values = self._rollout_q(eligible)
-            action_masks = env.get_action_masks()
-            self._validate_selection(q_values, action_masks, eligible)
-            actions = q_values.argmax(dim=1)
-            actions[eligible] = q_values[eligible].masked_fill(~action_masks[eligible], -torch.inf).argmax(dim=1)
-            return actions
+        frame = self._begin_selection()
+        try:
+            with torch.no_grad():
+                eligible = ~env.dones & ~self.episode_completed
+                q_values = self._rollout_q(eligible)
+                action_masks = env.get_action_masks()
+                self._revalidate_selection(frame)
+                self._validate_selection(q_values, action_masks, eligible)
+                actions = q_values.argmax(dim=1)
+                actions[eligible] = q_values[eligible].masked_fill(~action_masks[eligible], -torch.inf).argmax(dim=1)
+                return actions
+        finally:
+            if self._selection_frame is frame:
+                self._selection_frame = None
 
     def select_epsilon_greedy_actions(self, env: VectorizedHamletEnv, epsilon: float) -> torch.Tensor:
         """
         Select epsilon-greedy actions with action masking.
 
         With probability epsilon, select random valid action.
         With probability (1-epsilon), select greedy action.
 
         Args:
             env: Environment to get action masks from
             epsilon: Exploration rate [0, 1]
 
         Returns:
             actions: [num_agents] tensor of selected actions
         """
-        if self._preparing_checkpoint is not None or self._step_active or self._failed_step or self._pending_batch_commit is not None:
-            raise RuntimeError("Reentrant or failed population selection")
-        self._checkpoint_revision += 1
-        with torch.no_grad():
-            eligible = ~env.dones & ~self.episode_completed
-            q_values = self._rollout_q(eligible)
-            action_masks = env.get_action_masks()
-            epsilons = torch.full((self.num_agents,), epsilon, device=self.device, dtype=torch.float32)
-            return epsilon_greedy_action_selection_eligible(
-                q_values=q_values,
-                epsilons=epsilons,
-                action_masks=action_masks,
-                eligible=eligible,
-            )
+        frame = self._begin_selection()
+        try:
+            with torch.no_grad():
+                eligible = ~env.dones & ~self.episode_completed
+                q_values = self._rollout_q(eligible)
+                action_masks = env.get_action_masks()
+                self._revalidate_selection(frame)
+                epsilons = torch.full((self.num_agents,), epsilon, device=self.device, dtype=torch.float32)
+                return epsilon_greedy_action_selection_eligible(
+                    q_values=q_values,
+                    epsilons=epsilons,
+                    action_masks=action_masks,
+                    eligible=eligible,
+                )
+        finally:
+            if self._selection_frame is frame:
+                self._selection_frame = None
 
     def step_population(self, envs: VectorizedHamletEnv) -> BatchedAgentState:
         """Execute once; retain truthful progress and quarantine irreversible failures."""
+        self._require_operation_idle()
         if self._step_active or self._failed_step or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
             raise RuntimeError("Reentrant or quarantined population step")
         if envs is not self.env or self._accepted is None or self._clock_ledger_restore_unavailable:
             raise ValueError("Step requires this population's bound current ENV and complete clocks")
+        if self._vector_steps:
+            raise RuntimeError("Resolve the pending vector step before another population step")
         self._step_active = True
-        self._checkpoint_revision += 1
         try:
+            self._validate_owned_training()
+            self._checkpoint_revision += 1
             state = self._execute_population_step(envs)
             record = next(iter(self._vector_steps.values()))
             self._vector_step_progress = dict(
                 vector_tick=record.vector_tick,
                 status="completed",
                 last_reached_stage="completed",
                 accepted_identity=self._accepted_identity(record.accepted),
             )
             self._vector_stage = "completed"
             self._vector_steps = {}
@@ -1672,25 +2123,28 @@ class VectorizedPopulation(PopulationManager):
         if not _same_device(self.current_obs.device, self.device):
             raise RuntimeError(
                 f"Observation tensor on {self.current_obs.device} but population on {self.device}. "
                 f"Ensure environment and population use the same device."
             )
 
         if bool(self.episode_completed.all()):
             raise RuntimeError("Population episode is complete; call reset before stepping.")
         if self._owned_reset_pending:
             raise RuntimeError("Reset the explicitly begun batch before stepping")
+        prior = self._validate_owned_training()
         active_on_entry = ~envs.dones.clone()
         if bool((active_on_entry & self.episode_completed).any()):
             raise RuntimeError("A completed population lane cannot enter another transition.")
         self._bind_training()
+        self._validate_owned_training()
         q_values = self._rollout_q(active_on_entry)
+        self._validate_owned_training()
         if self._owned_episode is not None:
             if not bool(torch.isfinite(q_values[active_on_entry]).all()):
                 raise ValueError("Owned policy Q-values must be finite at the eligible predecessor")
             if q_values.shape[-1] == 1:
                 # A finite deterministic vocabulary has zero entropy. Validate
                 # Q first: this is not a fallback for NaN or infinite inputs.
                 entropy = torch.zeros_like(q_values[:, 0])
             else:
                 probabilities = torch.softmax(q_values, dim=-1)
                 entropy = -(probabilities * torch.log(probabilities + 1e-10)).sum(dim=-1) / torch.log(
@@ -1723,37 +2177,40 @@ class VectorizedPopulation(PopulationManager):
                 q_values,
             )
         else:
             # StaticCurriculum or other curricula - no Q-values needed
             self.current_curriculum_decisions = self.curriculum.get_batch_decisions(
                 temp_state,
                 self.agent_ids,
             )
 
         # 3.5 Sync curriculum metrics to registry
+        self._validate_owned_training()
         self._sync_curriculum_metrics()
+        self._validate_owned_training()
 
         # 4. Get action masks from environment
         action_masks = envs.get_action_masks()
+        self._validate_owned_training()
 
         # 5. Select actions via exploration strategy (with action masking)
         actions = self._select_eligible(q_values, temp_state, action_masks, active_on_entry)
 
         # 6. Extract curriculum difficulty multiplier
         depletion_multiplier = 1.0
         if self.current_curriculum_decisions:
             depletion_multiplier = self.current_curriculum_decisions[0].depletion_multiplier
 
         # 7. Step environment with curriculum difficulty
         # Note: rewards from environment already contain full DAC composition:
         #   rewards = extrinsic + (intrinsic * base_weight * modifiers) + shaping
-        prepared = self.prepare_vector_step(
+        prepared = self._prepare_vector_step(
             accepted=self._accepted,
             world_ids=self._accepted.world_ids,
             predecessor=self.current_obs,
             actions=actions,
             active_on_entry=active_on_entry,
         )
         next_obs, rewards, dones, info = envs.step(actions, depletion_multiplier, vector_step=prepared)
 
         active_on_entry = info["active_on_entry"]
         newly_terminal = info["newly_terminal"]
@@ -1780,20 +2237,40 @@ class VectorizedPopulation(PopulationManager):
                 (context.predecessor, record.predecessor),
                 (context.actions, record.actions),
                 (context.active_on_entry, record.active_on_entry),
                 (context.successor, next_obs),
                 (active_on_entry, record.active_on_entry),
                 (handoff.stamp.eligible, record.active_on_entry),
             )
         ):
             raise ValueError("ENV handoff changed the owned canonical transition")
         self._vector_stage = "env_returned"
+        next_counts = prior.counts + active_on_entry.long()
+        if (
+            not self._same_reading(info["step_counts"], next_counts)
+            or not self._same_reading(envs.step_counts, next_counts)
+            or not bool(torch.isfinite(next_obs).all())
+            or info["successor_action_masks"].shape != (self.num_agents, self.action_dim)
+            or info["successor_action_masks"].dtype != torch.bool
+            or info["successor_action_masks"].device != self.device
+        ):
+            raise ValueError("ENV return disagrees with the owned next population cut")
+        successor = _PopulationReading(
+            self._accepted,
+            record.vector_tick,
+            next_obs.detach().clone(),
+            dones.detach().clone(),
+            next_counts.detach().clone(),
+            prior.completed | newly_terminal,
+            next_counts.detach().clone(),
+            info["successor_action_masks"].detach().clone(),
+        )
         self._returned_step = copy.deepcopy(
             dict(
                 observations=next_obs,
                 rewards=rewards,
                 dones=dones,
                 components=components,
                 successor_action_masks=info["successor_action_masks"],
             )
         )
         intrinsic_rewards = components["provider_intrinsic_raw"].detach().clone()
@@ -1849,30 +2326,42 @@ class VectorizedPopulation(PopulationManager):
         # Preserve the existing advancement cut; allocate/validate before either publication.
         replacement = self._clock_ledger.advance(vector_ticks=1, eligible_transitions=int(active_on_entry.sum().item()))
         self.total_steps = record.vector_tick
         self._clock_ledger = replacement
         self._vector_stage = "advanced"
         self._pace_replay()
         if self.total_steps % self.train_frequency == 0:
             self._learn()
 
         # 10. Update current state
+        if not self._parent_reading_matches(prior) or self._prior_reading is not prior:
+            raise ValueError("A child callback changed the population predecessor")
+        assert self._initial_decision is not None
+        envs.validate_initial_participation(
+            accepted=self._accepted, participation=self._initial_decision.participation, predecessor=successor.observation
+        )
         self.current_obs = next_obs
 
         self.episode_step_counts += active_on_entry.long()
         new_completions = []
         for agent_idx in torch.nonzero(newly_terminal, as_tuple=False).flatten().tolist():
             reason: CompletionReason = "retirement" if bool(newly_retired[agent_idx]) else "authored_terminal"
             completion = self._finalize_episode(agent_idx, reason)
             if completion is not None:
                 new_completions.append(completion)
         info["episode_completions"] = tuple(new_completions)
+        envs.validate_initial_participation(
+            accepted=self._accepted, participation=self._initial_decision.participation, predecessor=successor.observation
+        )
+        if not self._parent_reading_matches(successor):
+            raise ValueError("Population finalization changed the actual successor reading")
+        self._prior_reading = successor
 
         # 12. Construct BatchedAgentState
         # Note: rewards from environment already contain full DAC composition including intrinsic.
         # We do NOT add intrinsic_rewards again to avoid double-counting.
         # intrinsic_rewards is kept for logging/tracking purposes only.
         total_rewards = rewards  # Already contains: extrinsic + intrinsic + shaping from DAC
 
         # 10. Construct and return batched agent state
         # Add Q-values to info for recording (clone to CPU to avoid GPU memory issues)
         info["q_values"] = [q_values[i].cpu().tolist() for i in range(self.num_agents)]
@@ -1904,20 +2393,23 @@ class VectorizedPopulation(PopulationManager):
         agents = [self.runtime_registry.get_snapshot_for_agent(i).to_dict() for i in range(self.num_agents)]
         payload = {
             "schema_version": "1.0.0",
             "episode_index": int(episode_index) if episode_index is not None else None,
             "agents": agents,
         }
         return payload
 
     def update_curriculum_tracker(self, rewards: torch.Tensor, dones: torch.Tensor) -> None:
         """Update curriculum tracker with episode rewards/dones."""
+        self._require_operation_idle()
+        if self._failed_step or self._owned_reset_pending or self._vector_steps or self._pending_batch_commit is not None:
+            raise RuntimeError("Pending population work cannot update curriculum telemetry")
         if hasattr(self.curriculum, "tracker") and self.curriculum.tracker is not None:
             self.curriculum.tracker.update_step(rewards, dones)
 
     def get_training_metrics(self) -> dict:
         """Get recent training metrics for logging.
 
         Returns:
             Dictionary with TD error, loss, Q-values mean, and training step.
             Returns None values if no training has occurred yet.
         """
@@ -1928,20 +2420,23 @@ class VectorizedPopulation(PopulationManager):
             "training_step": self.last_training_step,
         }
 
     def get_checkpoint(self) -> PopulationCheckpoint:
         """
         Return Pydantic checkpoint.
 
         Returns:
             PopulationCheckpoint DTO
         """
+        self._require_operation_idle()
+        if self._failed_step or self._vector_steps or self._owned_reset_pending or self._pending_batch_commit is not None:
+            raise RuntimeError("Pending population work cannot export a checkpoint")
         return PopulationCheckpoint(
             generation=0,
             num_agents=self.num_agents,
             agent_ids=self.agent_ids,
             curriculum_states={"global": self.curriculum.checkpoint_state()},
             exploration_states={"global": self.exploration.checkpoint_state()},
             pareto_frontier=[],
             metrics_summary={},
         )
 
@@ -1956,20 +2451,25 @@ class VectorizedPopulation(PopulationManager):
         - Optimizer state
         - Scheduler state or explicit null when no scheduler is configured
         - Training counters
         - Replay buffer contents
         - Exploration strategy state
         - Exact universe metadata for identity validation
 
         Returns:
             Complete checkpoint state dictionary
         """
+        self._require_operation_idle()
+        if self._owned_reset_pending:
+            raise RuntimeError("An outstanding owned reset cannot export a checkpoint")
+        if self._failed_step and not self._has_failed_step_diagnostic():
+            raise RuntimeError("Failed reset or unclassified work cannot export a healthy checkpoint")
         if self._step_active or self._pending_batch_commit is not None or (self._vector_steps and not self._failed_step):
             raise RuntimeError("In-progress vector work cannot masquerade as a healthy checkpoint")
         bars_config = self.env.bars_config
         return {
             "version": POPULATION_CHECKPOINT_FORMAT_VERSION,
             "clock_ledger": asdict(self.clock_ledger),
             "vector_step_progress": self.vector_step_progress,
             "q_network": self.q_network.state_dict(),
             "optimizer": self.optimizer.state_dict(),
             "scheduler": self.scheduler.state_dict() if self.scheduler is not None else None,
@@ -1982,20 +2482,32 @@ class VectorizedPopulation(PopulationManager):
                 "obs_dim": self.env.observation_dim,
                 "observation_schema_hash": self.env.level.observation_schema_hash,
                 "action_dim": self.action_dim,
             },
             "target_network": self.target_network.state_dict(),
             "training_step_counter": self.training_step_counter,
             # All buffer types implement serialize(), but mypy doesn't infer it for unions.
             "replay_buffer": self.replay_buffer.serialize(),  # type: ignore[union-attr]
         }
 
+    def _has_failed_step_diagnostic(self) -> bool:
+        progress = self._vector_step_progress
+        if not self._failed_step or not self._vector_steps or progress is None:
+            return False
+        record = next(iter(self._vector_steps.values()))
+        return (
+            progress["status"] == "failed"
+            and progress["last_reached_stage"] == self._vector_stage
+            and progress["vector_tick"] == record.vector_tick
+            and progress["accepted_identity"] == self._accepted_identity(record.accepted)
+        )
+
     @staticmethod
     def _require_exact_mapping(label: str, incoming_state: object, expected_keys: frozenset[str]) -> Mapping[str, object]:
         if not isinstance(incoming_state, Mapping):
             raise ValueError(f"Population checkpoint {label} must be a mapping; got {type(incoming_state).__name__}.")
         incoming_keys = set(incoming_state)
         if incoming_keys != expected_keys:
             missing = sorted(expected_keys - incoming_keys)
             unknown = sorted(incoming_keys - expected_keys)
             raise ValueError(f"Population checkpoint {label} key mismatch: missing={missing}, unknown={unknown}.")
         return incoming_state
@@ -2490,20 +3002,23 @@ class VectorizedPopulation(PopulationManager):
         ):
             raise ValueError("Progress requires actual portable world membership")
         if type(seqs) is not list or len(seqs) != self.num_agents or any(type(item) is not int or item < 1 for item in seqs):
             raise ValueError("Progress requires actual positive accepted world sequences")
         return ledger, progress
 
     def prepare_checkpoint_state(
         self, checkpoint: Mapping[str, Any], *, mode: str, parent_restore: Any, validate_parent_restore: Any, initialization: str | None
     ) -> PreparedPopulationRestore:
         """Prepare every owned child offside; external boundary authentication stays genuine."""
+        self._require_operation_idle()
+        if self._failed_step or self._owned_reset_pending or self._vector_steps:
+            raise RuntimeError("A failed population cannot install boundary state")
         if self._step_active or self._preparing_checkpoint is not None or self._pending_batch_commit is not None:
             raise RuntimeError("Reentrant population restore")
         if self._accepted is not None:
             raise ValueError("Boundary restore requires a fresh receiving population")
         if self.env.world_phase != "fresh-unbound":
             raise ValueError("Bound component replacement requires the genuine outer stable-owner installation protocol")
         revision = self._checkpoint_revision
         owned = copy.deepcopy(checkpoint)
         replay_target, validated_replay = self._validate_checkpoint_state(owned)
         ledger, progress = self._checkpoint_clocks(owned)
@@ -2554,20 +3069,23 @@ class VectorizedPopulation(PopulationManager):
             scheduler,
             replay_target,
             ledger,
             progress,
             correlation,
             cadence,
         )
         return handle
 
     def install_checkpoint_state(self, *, prepared: PreparedPopulationRestore) -> None:
+        self._require_operation_idle()
+        if self._failed_step or self._owned_reset_pending or self._vector_steps:
+            raise RuntimeError("A failed population cannot install boundary state")
         if type(prepared) is not PreparedPopulationRestore or prepared not in self._population_restores or self._step_active:
             raise ValueError("Foreign, consumed or reentrant population restore")
         if self.env.world_phase != "fresh-unbound":
             raise ValueError("Bound component replacement requires the genuine outer stable-owner installation protocol")
         revision, runtime, q, target, optimizer, scheduler, replay, ledger, progress, correlation, cadence = self._population_restores[
             prepared
         ]
         if revision != self._checkpoint_revision:
             raise ValueError("Stale population restore")
         # Preallocate all post-child publication state before the final runtime/BANK check.
@@ -2578,20 +3096,21 @@ class VectorizedPopulation(PopulationManager):
         try:
             self.exploration.install_restore(prepared=runtime)
             self.q_network, self.target_network, self.optimizer, self.scheduler = q, target, optimizer, scheduler
             self.replay_buffer = replay
             self.total_steps, self._clock_ledger = ledger.vector_ticks, ledger
             self.training_step_counter = ledger.optimizer_updates
             self._vector_step_progress, self._parent_cadence = progress, cadence
             self._vector_steps, self._population_restores = empty_steps, empty_restores
             self._failed_step, self._clock_ledger_restore_unavailable = False, False
             self._vector_stage, self._returned_step, self._service_receipts = None, None, ()
+            self._initial_decision, self._prior_reading, self._initial_reset, self._selection_frame = None, None, None, None
             self._checkpoint_revision, self._last_beta_tick = next_revision, ledger.vector_ticks
             self._bound_replay, self._replay_was_loaded = replay, True
             self._constructor_replay, self._constructor_replay_state, self._last_readiness = None, None, None
         finally:
             self._preparing_checkpoint, self._step_active = None, False
 
     def validate_checkpoint_state(self, checkpoint: Mapping[str, object]) -> None:
         """Structure/native-child INITIAL validation without publishing any child."""
         self.prepare_checkpoint_state(checkpoint, mode="initial", parent_restore=None, validate_parent_restore=None, initialization=None)
 
diff --git a/tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py b/tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py
index 6c88b482..a0bf1ee8 100644
--- a/tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py
+++ b/tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py
@@ -73,43 +73,48 @@ class ParentFixture:
     def enter(self, batch: int = 0) -> None:
         pop = self.population
         if self.boundary is None:
             self.bind()
             self.release = self.boundary.bootstrap(first_batch_episode=batch)
             self.env.install_boundary_release(self.release)
         reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
         self.env.validate_episode_reservation(reservation)
         pop.bind_episode_worlds(world_ids=IDS, world_episode_seqs=reservation.world_episode_seqs)
         pop.begin_batch_episode(batch, planned_horizon=20)
-        self.record, activation = pop.reset(reservation=reservation)
+        self.record, activation = pop.reset(reservation=reservation, retired_world_ids=())
         assert activation.owner is pop
         curiosity = self.runtime.begin_episode(accepted=self.record.accepted)
         self.env.activate_episode(
             accepted=self.record.accepted,
             population_receipt=activation,
             curiosity_receipt=curiosity,
         )
         equal(pop.current_obs, self.record.observation)
 
     def complete(self) -> tuple[Any, ...]:
         """Real component effects under a local controller; no HC/T26 native attestation."""
         pop, accepted = self.population, self.record.accepted
         for lane in range(len(IDS)):
             pop.flush_episode(lane, reason="budget")
         outcomes, key = pop.completed_outcomes, accepted.batch_episode
+        participants = tuple(world for world in accepted.world_ids if any(event.world_id == world for event in outcomes))
         content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
         curriculum = pop.curriculum.prepare_episode_outcomes(outcomes)
         bank = self.runtime.prepare_completion(
-            accepted=accepted, boundary_key=key, completion_content=content, outcomes=outcomes, participated_world_ids=IDS
+            accepted=accepted, boundary_key=key, completion_content=content, outcomes=outcomes, participated_world_ids=participants
         )
         closing = self.env.prepare_episode_close(
-            accepted=accepted, boundary_key=key, completion_content=content, participated_world_ids=IDS, dispositions=bank.prepared_receipt
+            accepted=accepted,
+            boundary_key=key,
+            completion_content=content,
+            participated_world_ids=participants,
+            dispositions=bank.prepared_receipt,
         )
         self.env.freeze_episode_close(closing)
         pop.curriculum.commit_prepared_episode_outcomes(curriculum)
         retirement = self.runtime.commit_completion(prepared=bank)
         pop.commit_episode_outcomes(outcomes)
         pop.sync_exploration_metrics()
         equal(pop.current_epsilons, self.runtime.epsilon_tensor(batch_size=len(IDS), device="cpu"))
         kinds = (
             "curriculum_receipt",
             "exploration_receipt",
@@ -527,20 +532,29 @@ def test_partial_failure_records_reached_cut_and_refuses_reexecution(
     with pytest.raises(RuntimeError, match="injected"):
         rig.population.step_population(rig.env)
     assert_failed(rig, stage, advanced)
     assert rig.env.global_tick == 1
     if seam != "env":
         assert rig.population.replay_buffer.retained_transitions == len(IDS)
     with pytest.raises(RuntimeError):
         rig.population.step_population(rig.env)
     assert len(physical_calls) == 1
     assert_failed(rig, stage, advanced)
+    if seam == "pace":
+        diagnostic = copy.deepcopy(rig.population.get_checkpoint_state())
+        equal(diagnostic["vector_step_progress"], rig.population.vector_step_progress)
+        assert diagnostic["vector_step_progress"]["status"] == "failed"
+        receiver = make_parent(compiled, "rnd")
+        with pytest.raises(ValueError, match="Failed or in-progress"):
+            receiver.population.prepare_checkpoint_state(
+                diagnostic, mode="completed_boundary", parent_restore=None, validate_parent_restore=None, initialization=None
+            )
 
 
 def test_current_initial_transport_has_complete_exact_ledger(compiled: Any) -> None:
     rig = make_parent(compiled)
     checkpoint = rig.population.get_checkpoint_state()
     assert checkpoint["version"] == 7
     assert set(checkpoint) == {
         "version",
         "q_network",
         "optimizer",
@@ -692,29 +706,29 @@ def test_post_env_reset_failure_never_issues_reusable_activation(compiled: Any,
         receipt = issue(issuer, kind=kind, payload=payload)
         if issuer.owner is rig.population and kind == "activation":
             activations.append(receipt)
         return receipt
 
     def refuse_telemetry() -> None:
         raise RuntimeError("post-ENV-reset telemetry failure")
 
     monkeypatch.setattr(rig.env, "reset", observe_reset)
     monkeypatch.setattr(WorldReceiptIssuer, "issue", observe_issue)
-    monkeypatch.setattr(rig.population, "sync_exploration_metrics", refuse_telemetry)
+    monkeypatch.setattr(rig.population, "_publish_exploration_metrics", refuse_telemetry)
     with pytest.raises(RuntimeError, match="post-ENV-reset"):
         rig.enter()
     assert len(resets) == 1
     assert resets[0][1].accepted.world_episode_seqs == (1,) * len(IDS)
     assert not activations
     assert rig.env.world_phase == "quarantined"
     with pytest.raises(RuntimeError):
-        rig.population.reset(reservation=resets[0][0])
+        rig.population.reset(reservation=resets[0][0], retired_world_ids=())
     assert len(resets) == 1
     assert rig.population.total_steps == rig.population.clock_ledger.vector_ticks == 0
 
 
 @pytest.mark.parametrize("after_child", (False, True))
 def test_identical_multi_batch_commit_request_retries_pending_child(compiled: Any, monkeypatch: Any, after_child: bool) -> None:
     rig = make_parent(compiled)
     rig.enter()
     rig.population.step_population(rig.env)
     settled = rig.complete()
# Actual POP initial participation implementation

Base00889036f1e00f9f864d126dd46f8c0cc9519459
Candidate3db908c4915c0b3f6666064bdc74a80dfbadb8a6
POP3131244e7f9e; parent7916cea1235; other3ownedbodiesunchanged.

