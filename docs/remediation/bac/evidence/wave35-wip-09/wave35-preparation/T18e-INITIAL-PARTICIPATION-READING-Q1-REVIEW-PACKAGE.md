 .../bac/test_initial_participation_env.py          | 302 ++++++++++++++++++++-
 1 file changed, 295 insertions(+), 7 deletions(-)
diff --git a/tests/test_townlet/regressions/bac/test_initial_participation_env.py b/tests/test_townlet/regressions/bac/test_initial_participation_env.py
index 38a24874..4aa49ce9 100644
--- a/tests/test_townlet/regressions/bac/test_initial_participation_env.py
+++ b/tests/test_townlet/regressions/bac/test_initial_participation_env.py
@@ -1,16 +1,16 @@
 """ENV component proofs; cooperative population custody is not actual POP learning.
 
 Breaks targeted: publishing before ready, accepting lookalike capabilities, reopening
 retired lanes, performing physics/provider work during retirement, and leaking a
-partly published decision. Real Q/Adam/replay/curriculum owners are constructed,
-but no learner, replay admission or curriculum completion is claimed here.
+partly published decision. Real Q/Adam/replay/curriculum owners are constructed;
+declared component closure uses real sinks, without claiming POP learning/replay.
 """
 
 from __future__ import annotations
 
 import copy
 import random
 from collections.abc import Mapping
 from dataclasses import replace
 from pathlib import Path
 from typing import Any
@@ -24,20 +24,21 @@ from townlet.agent.optimizer_factory import OptimizerFactory
 from townlet.config.bac_options import resolve_bac_options
 from townlet.config.brain_config import apply_training_overrides
 from townlet.config.drive_as_code import IntrinsicStrategyConfig
 from townlet.config.exploration_policy import build_exploration, resolve_exploration_policy
 from townlet.config.training_v2_config import TrainingV2Config
 from townlet.config.world_roster import WorldRosterDeclaration
 from townlet.curriculum.factory import build_curriculum
 from townlet.environment.vectorized_env import WorldReceiptIssuer
 from townlet.exploration.world_curiosity_state import WorldCuriosityDescriptor
 from townlet.training.clock_ledger import ClockLedger, PreparedVectorStep
+from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
 from townlet.training.replay_buffer import ReplayBuffer
 from townlet.universe.compiler import UniverseCompiler
 
 IDS = ("component-A", "component-B")
 SEED = 42
 
 
 def equal(left: Any, right: Any) -> None:
     """Exact owned witness comparison; never recompute an expected production value."""
     if isinstance(left, torch.Tensor):
@@ -71,22 +72,22 @@ def owned(value: Any) -> Any:
 
 
 @pytest.fixture(scope="module")
 def compiled() -> Any:
     return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)
 
 
 class ComponentPopulation:
     """Actual registered component owner with retained issued decision/step custody.
 
-    Unsupported parent-global commit/native requests fail closed. This controller
-    owns a component ClockLedger, not a reconstructed production POP history.
+    Unsupported commit/native requests fail closed. Canonical component boundary
+    commitments own a component ClockLedger, not production POP history.
     """
 
     def __init__(self, compiled: Any):
         self.device = torch.device("cpu")
         selected = compiled.get_level(compiled.metadata.primary_level)
         authored = selected.training.model_dump()
         authored["population"]["size"] = len(IDS)
         authored["seed"] = SEED
         training = TrainingV2Config.model_validate(authored)
         options = resolve_bac_options(training.bac_options, training=training).options
@@ -103,20 +104,21 @@ class ComponentPopulation:
         self.q = NetworkFactory.build_token_set(
             config=brain.architecture.token_set, action_dim=self.env.action_dim, token_spec=self.env.token_spec
         ).to(self.device)
         self.optimizer, self.scheduler = OptimizerFactory.build(config=brain.optimizer, parameters=self.q.parameters())
         self.replay = ReplayBuffer(capacity=brain.replay.capacity, device=self.device)
         effective = compiled.effective_run
         self.curriculum = build_curriculum(
             training, curriculum_options=effective.options.curriculum, static_policy=effective.static_policy, device=self.device
         )
         self.curriculum.initialize_population(len(IDS))
+        self.curriculum_issuer = WorldReceiptIssuer(owner=self.curriculum)
         policy = resolve_exploration_policy(
             drive_intrinsic=IntrinsicStrategyConfig(strategy="none", base_weight=0.0, apply_modifiers=[]),
             training=training,
             options=options,
         )
         descriptor = WorldCuriosityDescriptor.from_policy(
             policy,
             world_ids=IDS,
             observation_dim=self.env.observation_dim,
             action_dim=self.env.action_dim,
@@ -130,61 +132,67 @@ class ComponentPopulation:
             descriptor=descriptor,
             device=self.device,
             validate_accepted_episode=self.env.validate_accepted_episode,
             issuer_factory=self.capture_bank,
             report_allocation=self.reports.append,
             validate_committed_batch=self.validate_committed_batch,
             validate_parent_cadence=self.validate_parent_cadence,
         )
         assert self.bank is not None and self.bank is not self.runtime
         self.issuer = WorldReceiptIssuer(owner=self)
+        self.completion_request: Any = None
+        self.committed_batches: dict[int, Any] = {}
+        self.current_epsilons = self.runtime.epsilon_tensor(batch_size=len(IDS), device=self.device)
         self.ledger = ClockLedger()
         self.revision = 0
         self.intent: Any = None
         self.ready: Any = None
         self.participation: Any = None
         self.activation: Any = None
         self.retired: tuple[str, ...] | None = None
         self.current_obs: Any = None
         self.completed = torch.zeros(len(IDS), dtype=torch.bool)
         self.step_registry: dict[int, dict[str, Any]] = {}
         self.step_started = False
         self.env.set_exploration_runtime(exploration=self.runtime, claim_vector_step=self.claim_vector_step)
         self.roles = {
             "population": self,
             "curiosity": self.bank,
             "curriculum": self.curriculum,
-            "exploration": self.runtime,
+            "exploration": self,  # Real component coordinator owns its child commit journal.
             "network": self.q,
             "optimizer": self.optimizer,
             "scheduler": self if self.scheduler is None else self.scheduler,
             "replay": self.replay,
-            "selection": self.runtime,
+            "selection": self,  # Owns actual diagnostic epsilon telemetry supplied below.
         }
         self.authority = self.env.bind_boundary_authority(owner=self, role_owners=self.roles)
         release = self.authority.bootstrap(first_batch_episode=0)
         self.env.install_boundary_release(release)
         self.reservation = self.env.prepare_episode(batch_episode=0, release=release)
         self.env.validate_episode_reservation(self.reservation)
         self.reset = self.env.reset(reservation=self.reservation)
         self.accepted = self.reset.accepted
         self.current_obs = self.reset.observation
 
     def capture_bank(self, bank: Any) -> Any:
         if self.bank is not None:
             raise ValueError("component permits exactly one actual BANK construction")
         self.bank = bank
         self.bank_issuer = WorldReceiptIssuer(owner=bank)
         return self.bank_issuer
 
     def validate_committed_batch(self, *, batch_episode: Any, outcomes: Any) -> None:
-        raise ValueError("ENV component does not own a committed parent-global batch")
+        request = self.completion_request
+        content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
+        if request is None or request != (self.accepted, batch_episode, content):
+            raise ValueError("ENV component does not own this canonical completion request")
 
     def validate_parent_cadence(self, *, cadence: Any, mode: Any, accepted: Any, parent_restore: Any) -> None:
         raise ValueError("ENV component does not install parent-native cadence")
 
     def request(self, retired: tuple[str, ...]) -> Any:
         if self.activation is not None or self.step_started:
             raise ValueError("component decision window is closed")
         if self.intent is not None:
             if retired != self.retired:
                 raise ValueError("component decision request changed")
@@ -284,20 +292,21 @@ class ComponentPopulation:
 
     def step(self) -> Any:
         actions = torch.full((len(IDS),), self.env.action_ids["WAIT"], dtype=torch.long)
         prepared = self.prepare_step(actions)
         observations, rewards, dones, info = self.env.step(actions, vector_step=prepared)
         handoff = info["intrinsic_transition"]
         receipts = self.runtime.admit_and_service(context=handoff.context, stamp=handoff.stamp, accepted=handoff.accepted)
         self.ledger = self.ledger.advance(vector_ticks=1, eligible_transitions=int(info["active_on_entry"].sum()))
         self.current_obs = observations.detach().clone()
         self.completed = dones.detach().clone()
+        info["component_selection_epsilons"] = self.current_epsilons
         return observations, rewards, dones, info, receipts
 
     def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
         if accepted is not self.accepted or self.activation is None or self.step_started:
             raise ValueError("component empty proof needs actual activated zero-event custody")
         if not bool(self.completed.all()) or bool(self.env.step_counts.any()) or self.ledger.vector_ticks:
             raise ValueError("component has genuine participating work")
         return self.issuer.issue(kind="empty_episode", payload={"accepted": accepted, "participated_world_ids": (), "events": ()})
 
 
@@ -900,10 +909,289 @@ def test_observation_cleanup_cannot_activate_quarantined_episode(compiled: Any,
         return observation
 
     monkeypatch.setattr(rig.env, "_encode_observations", encode_then_abandon)
     before, revision = witness(rig), rig.env._world_revision
     with pytest.raises(ValueError):
         rig.activate()
     assert len(abandonments) == 1 and abandonments[0].accepted is rig.accepted
     assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
     assert rig.activation is None
     assert_unchanged(rig, before)
+
+
+def test_reading_validator_accepts_genuine_committed_preactivation(compiled: Any) -> None:
+    """Q1 causal RED reaches the absent reading API after genuine reset/decision commit."""
+    rig = ComponentPopulation(compiled)
+    rig.publish(prepare(rig))
+    assert rig.env.world_phase == "active-awaiting-activation" and rig.activation is None
+    before, revision = witness(rig), rig.env._world_revision
+    assert (
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+        is None
+    )
+    assert rig.env.world_phase == "active-awaiting-activation" and rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    with pytest.raises(ValueError):
+        rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
+
+
+@pytest.mark.parametrize("damage", ["copy_result", "foreign_result", "copy_token", "mutated_record", "predecessor"])
+def test_reading_validator_authenticates_current_private_reading(compiled: Any, damage: str) -> None:
+    rig = activated(compiled)
+    participation, accepted, predecessor = rig.participation, rig.accepted, rig.current_obs.clone()
+    if damage == "copy_result":
+        participation = replace(participation)
+    elif damage == "foreign_result":
+        participation = activated(compiled).participation
+    elif damage == "copy_token":
+        accepted = replace(accepted)
+    elif damage == "mutated_record":
+        fields = participation.payload
+        fields["observation"].add_(1)
+        participation = replace(participation, _payload=fields)
+    else:
+        predecessor.add_(0.25)
+    before, revision = witness(rig), rig.env._world_revision
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=accepted, participation=participation, predecessor=predecessor)
+    assert rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+
+
+@pytest.mark.parametrize("field", ["positions", "meters", "dones", "step_counts"])
+def test_reading_validator_rejects_public_physical_tamper(compiled: Any, field: str) -> None:
+    rig = activated(compiled)
+    value = getattr(rig.env, field)
+    if field == "dones":
+        value[1] = False
+    else:
+        value.reshape(-1)[0] += 1
+    before, revision = witness(rig), rig.env._world_revision
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+
+
+def test_reading_validator_cleanup_is_durable(compiled: Any, monkeypatch: Any) -> None:
+    rig = activated(compiled)
+    encode = rig.env._encode_observations
+    abandonments: list[Any] = []
+
+    def encode_then_abandon() -> Any:
+        observation = encode()
+        abandonments.append(rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure"))
+        return observation
+
+    monkeypatch.setattr(rig.env, "_encode_observations", encode_then_abandon)
+    before, revision = witness(rig), rig.env._world_revision
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    assert len(abandonments) == 1 and abandonments[0].accepted is rig.accepted
+    assert rig.env.world_phase == "quarantined" and rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+
+
+def test_pending_decision_cannot_be_used_as_reading_authority(compiled: Any) -> None:
+    rig = ComponentPopulation(compiled)
+    prepared = prepare(rig)
+    before = witness(rig)
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=prepared, predecessor=rig.current_obs)
+    assert_unchanged(rig, before)
+    rig.publish(prepared)  # A pure refused query must not consume the actual pending decision.
+    equal(rig.env.dones, torch.tensor([False, True]))
+
+
+def test_failed_episode_cannot_use_retained_reading_authority(compiled: Any) -> None:
+    rig = activated(compiled)
+    rig.env.abandon_episode(accepted=rig.accepted, reason="runtime_failure")
+    before = witness(rig)
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    assert rig.env.world_phase == "quarantined"
+    assert_unchanged(rig, before)
+
+
+def test_activation_in_progress_refuses_recursive_reading(compiled: Any, monkeypatch: Any) -> None:
+    """The readable preactivation phase must not bypass actual activation's busy fence."""
+    rig = ComponentPopulation(compiled)
+    rig.publish(prepare(rig))
+    encode = rig.env._encode_observations
+    refused: list[bool] = []
+
+    def encode_with_query() -> Any:
+        observation = encode()
+        with pytest.raises(ValueError):
+            rig.env.validate_initial_participation_reading(
+                accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs
+            )
+        refused.append(True)
+        return observation
+
+    monkeypatch.setattr(rig.env, "_encode_observations", encode_with_query)
+    before, revision = witness(rig), rig.env._world_revision
+    rig.activate()
+    assert refused == [True] and rig.env.world_phase == "active"
+    assert rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+
+
+def reading_phase(compiled: Any, phase: str) -> ComponentPopulation:
+    """Earn completed phases through a declared one-step component cap and real sinks."""
+    rig = ComponentPopulation(compiled)
+    rig.publish(prepare(rig))
+    if phase == "active-awaiting-activation":
+        return rig
+    rig.activate()
+    if phase == "active":
+        return rig
+    observations, rewards, _, info, _ = rig.step()
+    equal(rig.env.step_counts, torch.tensor([1, 0]))
+    event = LaneOutcome(
+        outcome=EpisodeCompletion(
+            agent_idx=0,
+            reason="cap",
+            survival_time=1,
+            final_observation=observations[0].detach().cpu().clone(),
+            final_meters=rig.env.meters[0].detach().cpu().clone(),
+        ),
+        batch_episode=rig.accepted.batch_episode,
+        planned_horizon=1,
+        reward_total=float(rewards[0]),
+        reward_extrinsic=float(info["reward_components"]["extrinsic"][0]),
+        reward_intrinsic=float(info["reward_components"]["intrinsic"][0]),
+        reward_shaping=float(info["reward_components"]["shaping"][0]),
+        policy_entropy=0.0,  # The real component control always chooses WAIT, not a Q policy.
+        world_id=IDS[0],
+        world_episode_seq=rig.accepted.world_episode_seqs[0],
+    )
+    outcomes = (event,)
+    content = tuple((item.payload.hex(), item.fingerprint) for item in map(freeze_lane_outcome, outcomes))
+    key = rig.accepted.batch_episode
+    curriculum = rig.curriculum.prepare_episode_outcomes(outcomes)
+    bank = rig.runtime.prepare_completion(
+        accepted=rig.accepted, boundary_key=key, completion_content=content, outcomes=outcomes, participated_world_ids=(IDS[0],)
+    )
+    close = rig.env.prepare_episode_close(
+        accepted=rig.accepted,
+        boundary_key=key,
+        completion_content=content,
+        participated_world_ids=(IDS[0],),
+        dispositions=bank.prepared_receipt,
+    )
+    rig.env.freeze_episode_close(close)
+    rig.close_context = (curriculum, bank, close)
+    if phase == "boundary-pending":
+        return rig
+    rig.curriculum.commit_prepared_episode_outcomes(curriculum)
+    retirement = rig.runtime.commit_completion(prepared=bank)
+    rig.completion_request = (rig.accepted, key, content)
+    rig.runtime.commit_batch_episode(batch_episode=key, outcomes=outcomes)
+    rig.committed_batches[key] = content
+    rig.completed = torch.ones_like(rig.completed)  # Genuine declared component cap finalized A; B was already retired.
+    rig.ledger = rig.ledger.advance(completed_batch_episodes=1)
+    rig.current_epsilons = rig.runtime.epsilon_tensor(batch_size=len(IDS), device=rig.device)
+    equal(rig.current_epsilons, torch.full((len(IDS),), rig.runtime.epsilon, dtype=torch.float32))
+    closure = rig.env.close_episode(close, dispositions=retirement)
+    assert dict(retirement.dispositions)[IDS[1]] == "retired_nonparticipating"
+    if phase == "closed-awaiting-release":
+        return rig
+    fields = {"accepted": rig.accepted, "boundary_key": key, "completion_content": content}
+    effects = rig.issuer.issue(
+        kind="boundary_effects",
+        payload={
+            "batch_episode": key,
+            "accepted_identity": rig.accepted,
+            "completion_content": content,
+            "retirement_receipt": retirement,
+            "curriculum_receipt": rig.curriculum_issuer.issue(kind="curriculum_receipt", payload=fields),
+            **{
+                name: rig.issuer.issue(kind=name, payload=fields)
+                for name in ("exploration_receipt", "population_commit_receipt", "epsilon_install_receipt", "selection_sync_receipt")
+            },
+        },
+    )
+    rig.release = rig.authority.completed(closure=closure, effects=effects)
+    rig.env.install_boundary_release(rig.release)
+    assert phase == "released-completed"
+    return rig
+
+
+@pytest.mark.parametrize("phase", ["active-awaiting-activation", "active", "closed-awaiting-release", "released-completed"])
+def test_reading_validator_preserves_each_genuine_healthy_phase(compiled: Any, monkeypatch: Any, phase: str) -> None:
+    rig = reading_phase(compiled, phase)
+    assert rig.env.world_phase == phase
+    components_before, runtime_before = component_state(rig), rig.runtime.checkpoint_state()
+    before, revision = witness(rig), rig.env._world_revision
+
+    def forbidden_mask(**kwargs: Any) -> Any:
+        raise AssertionError("a pure reading must not recompute action masks")
+
+    monkeypatch.setattr(rig.env.action_mask_builder, "build", forbidden_mask)
+    rig.participation.observation.add_(100)
+    rig.participation.action_masks.fill_(True)
+    for _ in range(2):
+        assert (
+            rig.env.validate_initial_participation_reading(
+                accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs
+            )
+            is None
+        )
+    assert rig.env.world_phase == phase and rig.env._world_revision == revision
+    assert_unchanged(rig, before)
+    equal(component_state(rig), components_before)
+    equal(rig.runtime.checkpoint_state(), runtime_before)
+    if phase != "active":
+        with pytest.raises(ValueError):
+            rig.env.validate_initial_participation(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+        with pytest.raises(ValueError):
+            rig.env.step(torch.zeros(len(IDS), dtype=torch.long), vector_step=PreparedVectorStep())
+
+
+def test_frozen_close_refuses_reading_without_consuming_sink_handles(compiled: Any) -> None:
+    rig = reading_phase(compiled, "boundary-pending")
+    before = witness(rig)
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    assert rig.env.world_phase == "boundary-pending"
+    assert_unchanged(rig, before)
+
+
+def test_new_genuine_reset_invalidates_prior_reading_identity(compiled: Any) -> None:
+    rig = reading_phase(compiled, "released-completed")
+    old_participation, old_accepted = rig.participation, rig.accepted
+    reservation = rig.env.prepare_episode(batch_episode=rig.release.next_batch_episode, release=rig.release)
+    reset = rig.env.reset(reservation=reservation)
+    rig.reservation, rig.reset, rig.accepted, rig.current_obs = reservation, reset, reset.accepted, reset.observation
+    rig.participation = rig.activation = None
+    rig.retired = None
+    rig.step_started = False
+    rig.publish(prepare(rig))
+    assert rig.accepted is not old_accepted and rig.accepted.world_episode_seqs == (2, 2)
+    before = witness(rig)
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=old_participation, predecessor=rig.current_obs)
+    rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=rig.current_obs)
+    assert_unchanged(rig, before)
+    rig.activate()
+    _, _, _, info, _ = rig.step()
+    equal(info["component_selection_epsilons"], rig.runtime.epsilon_tensor(batch_size=len(IDS), device=rig.device))
+
+
+@pytest.mark.parametrize("damage", ["dtype", "width", "nonfinite"])
+def test_reading_validator_requires_actual_finite_observation_geometry(compiled: Any, damage: str) -> None:
+    rig = activated(compiled)
+    predecessor = rig.current_obs.clone()
+    if damage == "dtype":
+        predecessor = predecessor.to(torch.float64)
+    elif damage == "width":
+        predecessor = predecessor[:, :-1]
+    else:
+        predecessor[0, 0] = float("nan")
+    before, revision = witness(rig), rig.env._world_revision
+    with pytest.raises(ValueError):
+        rig.env.validate_initial_participation_reading(accepted=rig.accepted, participation=rig.participation, predecessor=predecessor)
+    assert rig.env._world_revision == revision and rig.env.world_phase == "active"
+    assert_unchanged(rig, before)
# ENV query authored-test review

Base7a96f86dd3706edae99f92dba7191bd9b1ca85cc
Candidate8d909f5d7c2b6f94e8b13eb62eb65b737e1101d5

