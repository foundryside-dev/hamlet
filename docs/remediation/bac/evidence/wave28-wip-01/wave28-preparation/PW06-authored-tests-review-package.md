# PW06 approvedABI testsfirst actualcandidate
Base 41e5742307ad170bc9871e0b5354b00599084da6
Candidate 7b29ea746c91e539e24ccd674566f143c1200d61
New owned test1192/40b0e27a, unchanged BANK901/WS871/HC675; CPabsent.

 .../regressions/bac/test_pw_scope_restore.py       | 1192 ++++++++++++++++++++
 1 file changed, 1192 insertions(+)
diff --git a/tests/test_townlet/regressions/bac/test_pw_scope_restore.py b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
new file mode 100644
index 00000000..2a2dd4df
--- /dev/null
+++ b/tests/test_townlet/regressions/bac/test_pw_scope_restore.py
@@ -0,0 +1,1192 @@
+"""PW06 CPU bank-owner units, with genuine ENV identity/lifecycle and providers.
+
+The three-dimensional transitions below are deliberately test-owned learning
+inputs, not the compiled ENV observation pipeline. Other boundary roles are
+explicit local interface owners. These cases do not qualify production POP,
+T26 effects, replay sampling, ordinary runner, or deferred simulator continuation.
+No checkpoint module or missing BANK method is imported/looked up at collection.
+"""
+
+from __future__ import annotations
+
+import random
+from collections.abc import Mapping
+from copy import copy, deepcopy
+from pathlib import Path
+
+import numpy as np
+import pytest
+import torch
+
+from townlet.config.bac_options import BaCOptions
+from townlet.config.drive_as_code import IntrinsicStrategyConfig
+from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
+from townlet.config.training_v2_config import TrainingV2Config
+from townlet.config.world_roster import WorldRosterDeclaration
+from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
+from townlet.exploration.provider_factory import make_backend
+from townlet.exploration.scoped_curiosity import CuriosityBank
+from townlet.exploration.world_curiosity_state import OwnedWorldBackend, ServiceClock, WorldCuriosityDescriptor, WorldRNGState
+from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
+from townlet.training.historical_checkpoint import (
+    decode_historical_envelope,
+    encode_historical_envelope,
+    prepare_historical_envelope,
+    resolve_historical_access,
+)
+from townlet.training.replay_buffer import ReplayBuffer
+from townlet.training.state import RewardTensor
+from townlet.universe.compiler import UniverseCompiler
+
+FAMILIES = ("none", "count_based", "rnd", "adaptive_rnd", "icm")
+TRAINABLE = ("rnd", "adaptive_rnd", "icm")
+IDS = ("PW06/A", "PW06/B")
+SEED = 10291
+REFUSAL = (ValueError, TypeError, RuntimeError, KeyError)
+
+
+def policy_for(compiled_universe, family, scope):
+    level = compiled_universe.get_level("L0_test")
+    drive = IntrinsicStrategyConfig.model_validate(dict(level.drive.intrinsic.model_dump(), strategy=family))
+    training = level.training.model_dump()
+    training["replay_buffer"]["batch_size"] = 2
+    training["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
+    training["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.1)
+    training["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
+    training["training_loop"]["max_steps_per_episode"] = 20
+    options = BaCOptions.model_validate(
+        {
+            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
+            "provider_parameter_source": "training",
+            "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
+            "providers": {
+                "count_based": {"quantization_width": 0.125, "max_entries": 16},
+                "icm": {
+                    "feature_dim": 4,
+                    "hidden_dim": 8,
+                    "learning_rate": 0.001,
+                    "inverse_weight": 0.8,
+                    "forward_weight": 0.2,
+                    "training_batch_size": 2,
+                    "max_pending_transitions": 4,
+                },
+            },
+        }
+    )
+    return resolve_exploration_policy(drive, TrainingV2Config.model_validate(training), options)
+
+
+def captured_payload():
+    replay = ReplayBuffer(capacity=4, device=torch.device("cpu"))
+    observations = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
+    rewards = RewardTensor(
+        torch.tensor([1.0, 2.0]),
+        extrinsic=torch.tensor([0.5, 1.0]),
+        intrinsic=torch.tensor([0.5, 1.0]),
+        shaping=None,
+        is_composed=True,
+    )
+    replay.push_recorded(
+        observations=observations,
+        actions=torch.tensor([0, 1], dtype=torch.int64),
+        rewards=rewards,
+        next_observations=observations + 0.25,
+        dones=torch.tensor([False, True]),
+        next_action_masks=torch.tensor([[True, False], [False, False]]),
+    )
+    return {
+        "version": 10,
+        "action_dim": 2,
+        "episode": 3,
+        "completed_live_agent_steps": 7,
+        "population_state": {"version": 7, "total_steps": 9, "training_step_counter": 2, "replay_buffer": replay.serialize()},
+    }
+
+
+def same(left, right):
+    """Independent typed equality; never delegates to a future CP codec."""
+    assert type(left) is type(right)
+    if isinstance(left, torch.Tensor):
+        assert (left.shape, left.dtype, left.device, left.layout) == (right.shape, right.dtype, right.device, right.layout)
+        assert torch.equal(left, right)
+    elif isinstance(left, np.ndarray):
+        assert left.dtype == right.dtype and left.shape == right.shape
+        assert np.array_equal(left, right)
+    elif isinstance(left, Mapping):
+        assert left.keys() == right.keys()
+        for key in left:
+            same(left[key], right[key])
+    elif isinstance(left, (tuple, list)):
+        assert len(left) == len(right)
+        for a, b in zip(left, right, strict=True):
+            same(a, b)
+    else:
+        assert left == right
+
+
+def tensors(value):
+    if isinstance(value, torch.Tensor):
+        yield value
+    elif isinstance(value, Mapping):
+        for item in value.values():
+            yield from tensors(item)
+    elif isinstance(value, (tuple, list)):
+        for item in value:
+            yield from tensors(item)
+
+
+def independent(left, right):
+    same(left, right)
+    a, b = list(tensors(left)), list(tensors(right))
+    assert len(a) == len(b)
+    for source, destination in zip(a, b, strict=True):
+        if source.numel():
+            assert source.untyped_storage().data_ptr() != destination.untyped_storage().data_ptr()
+
+
+def ambient():
+    return (torch.get_rng_state().clone(), deepcopy(random.getstate()), deepcopy(np.random.get_state()))
+
+
+def native(world):
+    return world["backend"]["backend"]
+
+
+def rnd_native(state, family):
+    if family == "adaptive_rnd":
+        return state["rnd_state"]
+    return state
+
+
+def service_native(state, family):
+    if family == "icm":
+        return state
+    return rnd_native(state, family)["predictor_service"]
+
+
+def learned(state, family):
+    if family == "icm":
+        return state["encoder"]
+    return rnd_native(state, family)["predictor_network"]
+
+
+def optimizer(state, family):
+    return rnd_native(state, family)["optimizer"]
+
+
+def assert_real_learning(before, after, family):
+    if family not in TRAINABLE:
+        return
+    old, new = learned(before, family), learned(after, family)
+    assert any(not torch.equal(old[key], new[key]) for key in old)
+    adam = optimizer(after, family)["state"]
+    assert adam and all(type(key) is int for key in adam)
+    assert all(float(value["step"]) >= 2 for value in adam.values())
+    assert any(bool(value["exp_avg"].abs().sum() > 0) for value in adam.values())
+    assert any(bool(value["exp_avg_sq"].sum() > 0) for value in adam.values())
+    service = service_native(after, family)
+    if family == "icm":
+        assert service["counters"]["optimizer_updates"] >= 2
+        assert service["pending"]
+    else:
+        assert service["optimizer_updates"] >= 2
+        assert len(service["pending_observations"]) > 0
+
+
+class LocalRole:
+    """Real issued interfaces, without claiming production owner effects."""
+
+    def __init__(self):
+        self.issuer = WorldReceiptIssuer(owner=self)
+
+    def receipt(self, receipt_kind, **payload):
+        return self.issuer.issue(kind=receipt_kind, payload=payload)
+
+
+class RecordedIssuer:
+    def __init__(self, owner, kinds):
+        self.actual = WorldReceiptIssuer(owner=owner)
+        self.kinds = kinds
+
+    @property
+    def owner(self):
+        return self.actual.owner
+
+    def issue(self, *, kind, payload):
+        self.kinds.append(kind)
+        return self.actual.issue(kind=kind, payload=payload)
+
+
+@pytest.fixture(scope="module")
+def compiled():
+    result = UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)
+    assert result.to_dict()["compiled_schema_version"] == "1.42"
+    return result
+
+
+class Rig:
+    """Actual BANK + ENV; explicit small provider geometry/local other roles."""
+
+    def __init__(self, compiled_universe, family, scope, order):
+        self.family, self.scope, self.order = family, scope, order
+        self.policy = policy_for(compiled_universe, family, scope)
+        self.roster = WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(IDS)})
+        self.env = VectorizedHamletEnv(
+            universe=compiled_universe,
+            level_name="L0_test",
+            num_agents=2,
+            device="cpu",
+            world_roster=self.roster,
+            training_seed=SEED,
+            lane_world_ids=order,
+        )
+        self.descriptor = WorldCuriosityDescriptor.from_policy(
+            self.policy, world_ids=order, observation_dim=3, action_dim=2, training_seed=SEED
+        )
+        self.reports, self.issued = [], []
+        self.reject_restore_allocation = False
+        self.bank = CuriosityBank(
+            policy=self.policy,
+            descriptor=self.descriptor,
+            device="cpu",
+            validate_accepted_episode=self.env.validate_accepted_episode,
+            issuer_factory=lambda owner: RecordedIssuer(owner, self.issued),
+            report_allocation=self.report_allocation,
+        )
+        self.other, self.population = LocalRole(), LocalRole()
+        roles = {key: self.other for key in ("curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")}
+        roles.update(population=self.population, curiosity=self.bank)
+        self.authority = self.env.bind_boundary_authority(owner=self.other, role_owners=roles)
+        self.release, self.accepted, self.observation = None, None, None
+
+    def report_allocation(self, estimate):
+        self.reports.append(estimate)
+        if self.reject_restore_allocation and estimate.operation == "restore":
+            raise MemoryError("admitted restore allocation refused")
+
+    def begin(self, batch):
+        if self.release is None:
+            self.release = self.env.install_boundary_release(self.authority.bootstrap(first_batch_episode=batch))
+        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
+        self.env.validate_episode_reservation(reservation)
+        reset = self.env.reset(reservation=reservation)
+        self.accepted, self.observation = reset.accepted, reset.observation
+        receipt = self.bank.begin_episode(accepted=self.accepted)
+        self.env.activate_episode(
+            accepted=self.accepted,
+            population_receipt=self.population.receipt("activation", accepted=self.accepted),
+            curiosity_receipt=receipt,
+        )
+        return receipt
+
+    def actual_step(self):
+        actions = self.env.get_action_masks().to(torch.int64).argmax(dim=1)
+        result = self.env.step(actions, depletion_multiplier=1.0)
+        assert bool((self.env.step_counts > 0).all())
+        return result
+
+    def context(self, tick, active):
+        rows = []
+        for world in self.order:
+            offset = 1.0 if world == IDS[0] else 8.0
+            rows.append([offset + tick / 10, offset * 0.2 - tick / 20, -offset - tick / 7])
+        predecessor = torch.tensor(rows, dtype=torch.float32)
+        return IntrinsicTransitionContext(
+            predecessor=predecessor,
+            actions=torch.tensor([0 if world == IDS[0] else 1 for world in self.order], dtype=torch.int64),
+            successor=predecessor + torch.tensor([0.2, -0.1, 0.3]),
+            active_on_entry=torch.tensor([world in active for world in self.order], dtype=torch.bool),
+            vector_tick=tick,
+        )
+
+    def reserve(self, context):
+        return self.bank.prepare_step_stamp(
+            accepted=self.accepted, world_ids=self.order, active_on_entry=context.active_on_entry, vector_tick=context.vector_tick
+        )
+
+    def event(self, tick, active):
+        context = self.context(tick, active)
+        stamp = self.reserve(context)
+        reward = self.bank.reward(context=context, stamp=stamp, accepted=self.accepted, update_stats=True)
+        receipt = self.bank.admit_and_service(context=context, stamp=stamp, accepted=self.accepted)
+        return context, stamp, reward, receipt
+
+    def train(self):
+        before = {world: self.bank.snapshot_world(world_id=world)["backend"] for world in self.order}
+        last = None
+        for tick in range(1, 6):
+            last = self.event(tick, IDS)
+        for world in self.order:
+            saved = self.bank.snapshot_world(world_id=world)["backend"]
+            if self.scope == "per_world":
+                assert_real_learning(before[world]["backend"], saved["backend"], self.family)
+            else:
+                assert_real_learning(before[world], saved, self.family)
+        return last
+
+    def completion_arguments(self):
+        outcomes = tuple(
+            LaneOutcome(
+                outcome=EpisodeCompletion(
+                    agent_idx=index,
+                    reason="checkpoint",
+                    survival_time=int(self.env.step_counts[index]),
+                    final_observation=self.observation[index],
+                    final_meters=self.env.meters[index],
+                ),
+                batch_episode=self.accepted.batch_episode,
+                planned_horizon=100,
+                reward_total=float(index + 1),
+                reward_extrinsic=float(index + 1),
+                reward_intrinsic=0.0,
+                reward_shaping=0.0,
+                policy_entropy=0.5,
+                world_id=world,
+                world_episode_seq=self.accepted.world_episode_seqs[index],
+            )
+            for index, world in enumerate(self.order)
+        )
+        content = tuple((frozen.payload.hex(), frozen.fingerprint) for frozen in map(freeze_lane_outcome, outcomes))
+        return dict(
+            accepted=self.accepted,
+            boundary_key=self.accepted.batch_episode,
+            completion_content=content,
+            outcomes=outcomes,
+            participated_world_ids=self.order,
+        )
+
+    def complete(self):
+        arguments = self.completion_arguments()
+        prepared = self.bank.prepare_completion(**arguments)
+        closing = self.env.prepare_episode_close(
+            accepted=self.accepted,
+            boundary_key=self.accepted.batch_episode,
+            completion_content=arguments["completion_content"],
+            participated_world_ids=self.order,
+            dispositions=prepared.prepared_receipt,
+        )
+        self.env.freeze_episode_close(closing)
+        committed = self.bank.commit_completion(prepared=prepared)
+        assert self.bank.commit_completion(prepared=prepared) is committed
+        closure = self.env.close_episode(closing, dispositions=committed)
+        child_payload = dict(
+            accepted=self.accepted, boundary_key=self.accepted.batch_episode, completion_content=arguments["completion_content"]
+        )
+        children = {
+            name: owner.receipt(name, **child_payload)
+            for name, owner in (
+                ("curriculum_receipt", self.other),
+                ("exploration_receipt", self.other),
+                ("epsilon_install_receipt", self.other),
+                ("population_commit_receipt", self.population),
+                ("selection_sync_receipt", self.other),
+            )
+        }
+        effects = self.other.receipt(
+            "boundary_effects",
+            batch_episode=self.accepted.batch_episode,
+            accepted_identity=self.accepted,
+            completion_content=arguments["completion_content"],
+            retirement_receipt=committed,
+            **children,
+        )
+        self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
+        self.source_prepared, self.source_committed = prepared, committed
+        return self.world_checkpoint(), arguments
+
+    def world_checkpoint(self):
+        return self.env.checkpoint_world_state(kind="COMPLETED", release=self.release, retained_binding_batches=(1,), initial=None)
+
+
+class Correlation:
+    """Local parent custody control using genuine ENV preparation, never True."""
+
+    def __init__(self, rig, world_state):
+        self.rig, self.world_state = rig, deepcopy(world_state)
+        self.prepared = rig.env.prepare_world_restore(
+            kind="COMPLETED",
+            state=world_state,
+            world_roster=rig.roster,
+            destination_world_ids=rig.order,
+            semantic_execution_identity=rig.env.semantic_execution_identity,
+        )
+        self.calls = 0
+
+    def validate(self, *, prepared, curiosity_state):
+        assert prepared is self.prepared
+        assert self.rig.env.world_phase == "fresh-bound"
+        assert self.rig.env.world_ids == self.rig.order
+        boundary = self.rig.other.receipt("restored_boundary", kind="COMPLETED", state=self.world_state, prepared=self.prepared)
+        self.rig.authority.restored(restore=prepared, boundary=boundary)
+        data = prepared.payload
+        assert set(data) == {"state", "destination_world_ids", "destination_vfs_context"}
+        same(data["state"], self.world_state)
+        assert tuple(data["destination_world_ids"]) == self.rig.order
+        assert self.rig.env.semantic_execution_identity == self.world_state["execution_identity"]
+        completion = curiosity_state["completion"]
+        closed = self.world_state["last_closed_episode"]
+        identity = completion["original_accepted_identity"]
+        assert identity["batch_episode"] == closed["batch_episode"]
+        assert tuple(identity["world_ids"]) == tuple(closed["world_ids"])
+        assert tuple(identity["world_episode_seqs"]) == tuple(closed["world_episode_seqs"])
+        same(completion["completion_content"], closed["completion_content"])
+        assert tuple(completion["participated_world_ids"]) == tuple(closed["participated_world_ids"])
+        for world in curiosity_state["worlds"]:
+            assert world["cursor"]["accepted_episode_seq"] == self.world_state["accepted_episode_seqs"][world["world_id"]]
+        self.calls += 1
+
+    def install_env(self):
+        boundary = self.rig.other.receipt("restored_boundary", kind="COMPLETED", state=self.world_state, prepared=self.prepared)
+        release = self.rig.authority.restored(restore=self.prepared, boundary=boundary)
+        self.rig.release = self.rig.env.install_world_restore(prepared=self.prepared, release=release)
+
+
+def prepare(rig, state, mode, correlation):
+    return rig.bank.prepare_restore(
+        state=state,
+        mode=mode,
+        accepted=rig.accepted if mode == "live_episode" else None,
+        parent_restore=None if correlation is None else correlation.prepared,
+        validate_parent_restore=None if correlation is None else correlation.validate,
+    )
+
+
+def by_id(state):
+    return {world["world_id"]: world for world in state["worlds"]}
+
+
+def no_live_change(rig, state, operation):
+    revision, globals_before = rig.bank.mutation_revision, ambient()
+    with pytest.raises(REFUSAL):
+        operation()
+    assert rig.bank.mutation_revision == revision
+    same(ambient(), globals_before)
+    same(rig.bank.checkpoint_state(), state)
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+@pytest.mark.parametrize("scope", ("per_world", "shared"))
+def test_pristine_real_bank_env_producer_control(compiled, family, scope):
+    """No CP lookup: root runs this genuine fixture/learning control first."""
+    rig = Rig(compiled, family, scope, IDS)
+    activation = rig.begin(1)
+    WorldReceiptIssuer.validate(activation, kind="activation", owner=rig.bank)
+    rig.env.validate_accepted_episode(accepted=rig.accepted)
+    with pytest.raises(REFUSAL):
+        rig.env.validate_accepted_episode(accepted=copy(rig.accepted))
+    rig.actual_step()
+    context, stamp, reward, receipts = rig.train()
+    assert reward.raw.shape == (2,) and bool(torch.isfinite(reward.raw).all())
+    revision = rig.bank.mutation_revision
+    replay = rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
+    assert replay == receipts and rig.bank.mutation_revision == revision
+    snapshots = [rig.bank.snapshot_world(world_id=world) for world in IDS]
+    if scope == "per_world":
+        a, b = snapshots[0]["backend"], snapshots[1]["backend"]
+        assert a["rng"]["world_id"] == IDS[0] and b["rng"]["world_id"] == IDS[1]
+    if family == "count_based":
+        counts = snapshots[0]["backend"]
+        if scope == "per_world":
+            counts = counts["backend"]
+        assert len(counts["counts"]) > 0 and set(counts["lru"]) == set(counts["counts"])
+        assert sum(counts["counts"].values()) == (5 if scope == "per_world" else 10)
+    if family in TRAINABLE:
+        assert any(item.optimizer_updates > 0 for item in receipts) or any(
+            service_native(snapshots[0]["backend"]["backend"] if scope == "per_world" else snapshots[0]["backend"], family)[key]
+            for key in (("counters",) if family == "icm" else ("optimizer_updates",))
+        )
+
+
+@pytest.mark.parametrize("family", TRAINABLE)
+def test_pristine_owned_provider_gradient_pairing_control(compiled, family):
+    """Actual owner public callbacks; no BANK checkpoint or CP import."""
+    policy = policy_for(compiled, family, "per_world")
+    descriptor = WorldCuriosityDescriptor.from_policy(policy, world_ids=IDS, observation_dim=3, action_dim=2, training_seed=SEED)
+    rng = WorldRNGState.create(descriptor=descriptor, world_id=IDS[0], cuda_devices=())
+    owner = OwnedWorldBackend.construct(
+        rng=rng,
+        factory=lambda candidate: make_backend(
+            policy, world_id=IDS[0], obs_dim=3, action_dim=2, device="cpu", rng=candidate, descriptor=descriptor
+        ),
+    )
+
+    def witness(backend, sources):
+        del sources
+        if family == "icm":
+            parameters = (
+                list(backend.encoder.parameters()) + list(backend.inverse_model.parameters()) + list(backend.forward_model.parameters())
+            )
+            adam = backend.optimizer
+        else:
+            provider = backend.rnd if family == "adaptive_rnd" else backend
+            parameters, adam = list(provider.predictor_network.parameters()), provider.optimizer
+            assert all(parameter.grad is None for parameter in provider.fixed_network.parameters())
+        assert {id(parameter) for group in adam.param_groups for parameter in group["params"]} == {id(p) for p in parameters}
+        assert all(parameter.grad is None for parameter in parameters)
+        return backend.checkpoint_state()
+
+    before = ambient()
+    snapshot = owner.call(witness)
+    same(ambient(), before)
+    independent(snapshot, owner.snapshot()["backend"])
+
+    def admit(backend, sources, position):
+        del sources
+        observations = torch.tensor([[position / 10, 0.3, -0.8]], dtype=torch.float32)
+        if family == "icm":
+            data = IntrinsicTransitionContext(
+                predecessor=observations,
+                actions=torch.tensor([position % 2]),
+                successor=observations + 0.2,
+                active_on_entry=torch.tensor([True]),
+                vector_tick=position,
+            )
+        else:
+            data = observations
+        return backend.admit_and_service_at(data, clock=ServiceClock("world_eligible_admission", position))
+
+    for position in range(1, 6):
+        owner.call(lambda backend, sources: admit(backend, sources, position))
+
+    def trained_witness(backend, sources):
+        del sources
+        if family == "icm":
+            parameters = (
+                list(backend.encoder.parameters()) + list(backend.inverse_model.parameters()) + list(backend.forward_model.parameters())
+            )
+            adam = backend.optimizer
+        else:
+            provider = backend.rnd if family == "adaptive_rnd" else backend
+            parameters, adam = list(provider.predictor_network.parameters()), provider.optimizer
+            assert all(parameter.grad is None for parameter in provider.fixed_network.parameters())
+        assert {id(parameter) for group in adam.param_groups for parameter in group["params"]} == {id(p) for p in parameters}
+        assert all(parameter.grad is not None for parameter in parameters)
+        assert any(bool(parameter.grad.abs().sum() > 0) for parameter in parameters)
+        assert len({parameter.data_ptr() for parameter in parameters}) == len(parameters)
+        assert all(parameter.grad.data_ptr() != parameter.data_ptr() for parameter in parameters)
+        assert all(float(state["step"]) >= 2 for state in adam.state.values())
+        return dict(native=backend.checkpoint_state(), gradients=[parameter.grad for parameter in parameters])
+
+    learned_state = owner.call(trained_witness)
+    independent(learned_state, owner.call(trained_witness))
+
+
+def test_pristine_historical_current_captured_replay_control():
+    payload = captured_payload()
+    before = deepcopy(payload)
+    policy = resolve_historical_access(payload, requested_mode="recorded_full_resume")
+    assert policy.active_retained_transitions == 2 and policy.effective_mode == "recorded_full_resume"
+
+    def forbidden_legacy(_):
+        pytest.fail("current captured input must not invoke historical source validation")
+
+    prepared = prepare_historical_envelope(payload, requested_mode="recorded_full_resume", validate_legacy=forbidden_legacy)
+    independent(prepared.available_learned_state, before)
+    same(payload, before)
+    same(prepared.policy.restored_clocks, {"episode": 3, "completed_live_agent_steps": 7, "total_steps": 9, "training_step_counter": 2})
+    decoded = decode_historical_envelope(encode_historical_envelope(prepared))
+    independent(decoded.available_learned_state, before)
+    captured = decoded.available_learned_state["population_state"]["replay_buffer"]
+    assert captured["format_version"] == 5 and captured["size"] == 2
+    assert bool(captured["legality_recorded"].all())
+    assert bool(captured["rewards_extrinsic_present"].all()) and bool(captured["rewards_intrinsic_present"].all())
+    assert not bool(captured["rewards_shaping_present"].any()) and captured["rewards_shaping"] is None
+    with pytest.raises(ValueError):
+        resolve_historical_access(payload, requested_mode="archived_history_fresh_episode")
+
+
+def test_pristine_completed_env_preinstall_parent_control(compiled):
+    """Genuine completed ENV lifecycle/preparation, independent of missing CP."""
+    source = Rig(compiled, "none", "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    world_state, arguments = source.complete()
+    destination = Rig(compiled, "none", "per_world", IDS[::-1])
+    parent = Correlation(destination, world_state)
+    assert destination.env.world_phase == "fresh-bound"
+    assert dict(destination.env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)
+    with pytest.raises(REFUSAL):
+        destination.env.validate_accepted_episode(accepted=source.accepted)
+    same(parent.prepared.payload["state"]["last_closed_episode"]["completion_content"], arguments["completion_content"])
+    foreign = Correlation(Rig(compiled, "none", "per_world", IDS), world_state).prepared
+    for invalid in (copy(parent.prepared), foreign):
+        boundary = destination.other.receipt("restored_boundary", kind="COMPLETED", state=world_state, prepared=parent.prepared)
+        with pytest.raises(REFUSAL):
+            destination.authority.restored(restore=invalid, boundary=boundary)
+    parent.install_env()
+    assert dict(destination.env.accepted_episode_seqs) == dict.fromkeys(IDS, 1)
+    same(destination.world_checkpoint()["last_closed_episode"], world_state["last_closed_episode"])
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+def test_private_restore_matches_by_world_id(compiled, family):
+    source = Rig(compiled, family, "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    world_state, _ = source.complete()
+    saved = source.bank.checkpoint_state()
+    assert saved["bank_phase"] == "completed_boundary" and saved["dispatch_identity"] is None
+    original = deepcopy(saved["completion"])
+    for order in (IDS[::-1], IDS):
+        destination = Rig(compiled, family, "per_world", order)
+        parent = Correlation(destination, world_state)
+        globals_before = ambient()
+        prepared = prepare(destination, saved, "completed_boundary", parent)
+        same(ambient(), globals_before)
+        assert parent.calls >= 2 and destination.env.world_phase == "fresh-bound"
+        assert dict(destination.env.accepted_episode_seqs) == dict.fromkeys(IDS, 0)
+        assert "prepared_dispositions" not in destination.issued and "dispositions" not in destination.issued
+        destination.bank.install_restore(prepared=prepared)
+        parent.install_env()
+        exported = destination.bank.checkpoint_state()
+        same(exported["completion"], original)
+        assert exported["descriptor"]["world_ids"] == list(order)
+        for world in IDS:
+            independent(by_id(saved)[world], by_id(exported)[world])
+        assert exported["dispatch_identity"] is None
+        saved, world_state = exported, destination.world_checkpoint()
+    destination.begin(2)
+    assert dict(destination.env.accepted_episode_seqs) == dict.fromkeys(IDS, 2)
+    revision = destination.bank.mutation_revision
+    destination.bank.begin_episode(accepted=destination.accepted)
+    assert destination.bank.mutation_revision == revision
+    after_begin = destination.bank.checkpoint_state()
+    assert after_begin["completion"] is None
+    for world in after_begin["worlds"]:
+        assert world["cursor"]["eligible_seq"] == 0 and not world["phase_cache"]
+    destination.event(6, IDS)
+    source.begin(2)
+    source.event(6, IDS)
+    for world in IDS:
+        same(by_id(destination.bank.checkpoint_state())[world], by_id(source.bank.checkpoint_state())[world])
+
+
+BAD_METADATA = ("missing_id", "extra_id", "duplicate_id", "wrong_id", "scope", "provider", "policy", "geometry", "cursor", "cache")
+
+
+def corrupt(state, defect, family):
+    last = state["worlds"][-1]
+    if defect == "missing_id":
+        state["worlds"].pop()
+    elif defect == "extra_id":
+        state["worlds"].append(dict(deepcopy(last), world_id="unlisted"))
+    elif defect == "duplicate_id":
+        last["world_id"] = state["worlds"][0]["world_id"]
+    elif defect == "wrong_id":
+        last["world_id"] = "different-exact-ID"
+    elif defect == "scope":
+        state["descriptor"]["scope"] = "shared"
+    elif defect == "provider":
+        state["descriptor"]["provider_kind"] = "none"
+    elif defect == "policy":
+        state["policy_identity"] = "0" * 64
+    elif defect == "geometry":
+        state["descriptor"]["observation_dim"] = 4
+    elif defect == "cursor":
+        last["cursor"]["cumulative_service_position"] = True
+    elif defect == "cache":
+        last["phase_cache"]["reward"]["raw"] = torch.tensor(float("nan"))
+    elif defect == "rng":
+        last["backend"]["rng"]["components"]["service"]["torch_cpu"] = torch.zeros(2, dtype=torch.uint8)
+    elif defect.startswith("gradient"):
+        gradients = last["gradients"]
+        if defect == "gradient_target":
+            target = rnd_native(native(last), family)["fixed_network"]
+            gradients["fixed_network"] = {name: torch.ones_like(value) for name, value in target.items()}
+        elif defect == "gradient_extra":
+            gradients["invented"] = {"weight": torch.ones(1)}
+        else:
+            module = gradients[next(iter(gradients))]
+            key = next(iter(module))
+            if defect == "gradient_missing":
+                module.pop(key)
+            elif defect == "gradient_shape":
+                module[key] = torch.zeros(1)
+            elif defect == "gradient_dtype":
+                module[key] = module[key].to(torch.float64)
+            elif defect == "gradient_sparse":
+                module[key] = module[key].to_sparse()
+            elif defect == "gradient_device":
+                module[key] = torch.empty_like(module[key], device="meta")
+            else:
+                module[key].flatten()[0] = float("nan")
+    elif defect in ("epsilon", "epsilon_missing", "epsilon_bool", "epsilon_decay", "epsilon_nan", "epsilon_min"):
+        values = native(last)
+        if defect == "epsilon_missing":
+            values.pop("epsilon_min")
+        elif defect == "epsilon_bool":
+            values["epsilon"] = True
+        elif defect == "epsilon_decay":
+            values["epsilon_decay"] *= 0.5
+        elif defect == "epsilon_nan":
+            values["epsilon"] = float("nan")
+        elif defect == "epsilon_min":
+            values["epsilon_min"] = -0.5
+        else:
+            values["epsilon"] = 1.5
+    elif defect in ("lru", "count_width_short", "count_width_long"):
+        values = native(last)
+        if defect == "lru":
+            values["lru"].pop()
+        else:
+            key = next(iter(values["counts"]))
+            replacement = key[:-1] if defect.endswith("short") else (*key, 0)
+            count = values["counts"].pop(key)
+            values["counts"][replacement] = count
+            values["lru"] = [replacement if item == key else item for item in values["lru"]]
+    elif defect == "model":
+        next(iter(learned(native(last), family).values())).flatten()[0] = float("nan")
+    elif defect == "model_dtype":
+        model = learned(native(last), family)
+        key = next(iter(model))
+        model[key] = model[key].to(torch.float64)
+    elif defect == "adam_id_alias":
+        states = optimizer(native(last), family)["state"]
+        key = next(iter(states))
+        states[float(key)] = states.pop(key)
+    elif defect == "adam_step":
+        moment = next(iter(optimizer(native(last), family)["state"].values()))
+        moment["step"] = torch.tensor(999.0)
+    elif defect == "moment_dtype":
+        moment = next(iter(optimizer(native(last), family)["state"].values()))
+        moment["exp_avg"] = moment["exp_avg"].to(torch.float64)
+    elif defect == "moment":
+        moment = next(iter(optimizer(native(last), family)["state"].values()))
+        moment["exp_avg_sq"].flatten()[0] = -1
+    elif defect == "queue":
+        values = service_native(native(last), family)
+        if family == "icm":
+            values["pending"].append(torch.tensor([float("nan")]))
+        else:
+            queue = values["pending_observations"]
+            queue[-1] = torch.full_like(queue[-1], float("nan"))
+    else:
+        raise AssertionError(defect)
+
+
+INVALID_CASES = [("rnd", defect) for defect in BAD_METADATA]
+INVALID_CASES += [(family, defect) for family in TRAINABLE for defect in ("rng", "model", "moment", "queue", "gradient_nan")]
+INVALID_CASES += [(family, defect) for family in TRAINABLE for defect in ("model_dtype", "adam_id_alias", "adam_step", "moment_dtype")]
+INVALID_CASES += [
+    ("rnd", defect)
+    for defect in (
+        "gradient_missing",
+        "gradient_extra",
+        "gradient_shape",
+        "gradient_dtype",
+        "gradient_sparse",
+        "gradient_device",
+        "gradient_target",
+    )
+]
+INVALID_CASES += [
+    ("none", defect)
+    for defect in ("epsilon", "epsilon_missing", "epsilon_bool", "epsilon_decay", "epsilon_nan", "epsilon_min", "gradient_extra")
+]
+INVALID_CASES += [("count_based", defect) for defect in ("lru", "count_width_short", "count_width_long", "gradient_extra")]
+
+
+@pytest.mark.parametrize("family,defect", INVALID_CASES, ids=[f"{family}-{defect}" for family, defect in INVALID_CASES])
+def test_invalid_last_world_leaves_all_runtime_state_unchanged(compiled, family, defect):
+    rig = Rig(compiled, family, "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    before = rig.bank.checkpoint_state()
+    malformed = deepcopy(before)
+    corrupt(malformed, defect, family)
+    no_live_change(rig, before, lambda: prepare(rig, malformed, "live_episode", None))
+    good = prepare(rig, before, "live_episode", None)
+    rig.bank.install_restore(prepared=good)
+    rig.event(6, IDS)
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+@pytest.mark.parametrize("scope", ("shared", "per_world"))
+def test_initial_and_live_scope_roundtrip(compiled, family, scope):
+    rig = Rig(compiled, family, scope, IDS)
+    initial = rig.bank.checkpoint_state()
+    assert initial["bank_phase"] == "initial"
+    prepared = prepare(rig, initial, "initial", None)
+    rig.bank.install_restore(prepared=prepared)
+    independent(initial, rig.bank.checkpoint_state())
+    rig.begin(1)
+    context, stamp, reward, receipts = rig.train()
+    saved = rig.bank.checkpoint_state()
+    before_rng = ambient()
+    prepared = prepare(rig, saved, "live_episode", None)
+    same(ambient(), before_rng)
+    rig.bank.install_restore(prepared=prepared)
+    revision = rig.bank.mutation_revision
+    replay = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
+    same(replay.raw, reward.raw)
+    same(replay.scales, reward.scales)
+    assert rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted) == receipts
+    assert rig.bank.mutation_revision == revision
+    independent(saved, rig.bank.checkpoint_state())
+    rig.event(6, IDS)
+    expected_next = rig.bank.checkpoint_state()
+    prepared = prepare(rig, saved, "live_episode", None)
+    rig.bank.install_restore(prepared=prepared)
+    rig.event(6, IDS)
+    same(rig.bank.checkpoint_state(), expected_next)
+
+
+@pytest.mark.parametrize("family", FAMILIES)
+@pytest.mark.parametrize("phase", ("reserved", "rewarded", "settled", "inactive", "stale_private"))
+def test_live_phase_dedup_resume(compiled, family, phase):
+    rig = Rig(compiled, family, "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    active = () if phase == "inactive" else (IDS[0],)
+    context = rig.context(6, active)
+    stamp = rig.reserve(context)
+    reward, receipts = None, None
+    if phase != "reserved":
+        reward = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
+    if phase in ("settled", "inactive", "stale_private"):
+        receipts = rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
+    if phase == "stale_private":
+        rig.event(7, (IDS[1],))
+    saved = rig.bank.checkpoint_state()
+    prepared = prepare(rig, saved, "live_episode", None)
+    rig.bank.install_restore(prepared=prepared)
+    revision = rig.bank.mutation_revision
+    replay = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
+    if reward is not None:
+        same(replay.raw, reward.raw)
+        same(replay.scales, reward.scales)
+        assert rig.bank.mutation_revision == revision
+    served = rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
+    if receipts is not None:
+        assert served == receipts and rig.bank.mutation_revision == revision
+    if active:
+        stable = rig.bank.checkpoint_state()
+        no_live_change(rig, stable, lambda: rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=False))
+        changed = IntrinsicTransitionContext(
+            predecessor=context.predecessor + 1,
+            actions=context.actions,
+            successor=context.successor,
+            active_on_entry=context.active_on_entry,
+            vector_tick=context.vector_tick,
+        )
+        no_live_change(rig, stable, lambda: rig.bank.reward(context=changed, stamp=stamp, accepted=rig.accepted, update_stats=True))
+
+
+@pytest.mark.parametrize("family", TRAINABLE)
+def test_native_gradients_are_owned_before_next_update(compiled, family):
+    rig = Rig(compiled, family, "per_world", IDS)
+    initial = rig.bank.checkpoint_state()
+    assert all(value is None for world in initial["worlds"] for module in world["gradients"].values() for value in module.values())
+    rig.begin(1)
+    rig.train()
+    saved = rig.bank.checkpoint_state()
+    for world in saved["worlds"]:
+        values = [value for module in world["gradients"].values() for value in module.values()]
+        assert values and all(isinstance(value, torch.Tensor) for value in values)
+        assert any(bool(value.abs().sum() > 0) for value in values)
+    # Optional residual values are transport state, not reconstructed by Adam.
+    mixed = deepcopy(saved)
+    module = next(iter(mixed["worlds"][0]["gradients"].values()))
+    names = list(module)
+    assert len(names) >= 2
+    module[names[0]], module[names[1]] = None, torch.zeros_like(module[names[1]])
+    mixed_prepared = prepare(rig, mixed, "live_episode", None)
+    rig.bank.install_restore(prepared=mixed_prepared)
+    independent(mixed, rig.bank.checkpoint_state())
+    prepared = prepare(rig, saved, "live_episode", None)
+    rig.bank.install_restore(prepared=prepared)
+    independent(saved, rig.bank.checkpoint_state())
+    # Mutating caller-owned gradients after preparation cannot alter the candidate.
+    prepared = prepare(rig, saved, "live_episode", None)
+    for world in saved["worlds"]:
+        for module in world["gradients"].values():
+            for value in module.values():
+                value.fill_(291.0)
+    rig.bank.install_restore(prepared=prepared)
+    restored = rig.bank.checkpoint_state()
+    assert all(not bool((value == 291).all()) for world in restored["worlds"] for value in tensors(world["gradients"]))
+
+
+@pytest.mark.parametrize("defect", ("foreign", "copy", "consumed", "snapshot", "real_mutation", "caller_mutation"))
+def test_restore_token_and_input_custody(compiled, defect):
+    rig = Rig(compiled, "rnd", "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    saved = rig.bank.checkpoint_state()
+    prepared = prepare(rig, saved, "live_episode", None)
+    if defect == "caller_mutation":
+        expected = deepcopy(saved)
+        next(tensors(saved["worlds"][0]["backend"]["backend"])).fill_(713.0)
+        rig.bank.install_restore(prepared=prepared)
+        same(rig.bank.checkpoint_state(), expected)
+        return
+    if defect == "consumed":
+        rig.bank.install_restore(prepared=prepared)
+    elif defect == "snapshot":
+        rig.bank.snapshot_world(world_id=IDS[0])
+    elif defect == "real_mutation":
+        rig.event(6, IDS)
+    elif defect == "copy":
+        prepared = copy(prepared)
+    if defect == "foreign":
+        other = Rig(compiled, "rnd", "per_world", IDS)
+        before = other.bank.checkpoint_state()
+        no_live_change(other, before, lambda: other.bank.install_restore(prepared=prepared))
+    else:
+        before = rig.bank.checkpoint_state() if defect in ("snapshot", "real_mutation") else deepcopy(saved)
+        no_live_change(rig, before, lambda: rig.bank.install_restore(prepared=prepared))
+
+
+@pytest.mark.parametrize("allocation", ("report", "last_owner", "last_clone"))
+def test_restore_allocation_refusal_is_atomic(compiled, monkeypatch, allocation):
+    rig = Rig(compiled, "rnd", "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    before = rig.bank.checkpoint_state()
+    revision, globals_before = rig.bank.mutation_revision, ambient()
+    if allocation == "report":
+        rig.reject_restore_allocation = True
+        with pytest.raises(MemoryError, match="admitted restore"):
+            prepare(rig, before, "live_episode", None)
+        assert rig.reports[-1].operation == "restore"
+        rig.reject_restore_allocation = False
+    elif allocation == "last_owner":
+        original = OwnedWorldBackend.construct
+        calls = []
+
+        def fail_last(cls, *, rng, factory):
+            calls.append(rng.snapshot()["world_id"])
+            if len(calls) == 2:
+                raise MemoryError("last actual owner allocation")
+            return original(rng=rng, factory=factory)
+
+        with monkeypatch.context() as patch:
+            patch.setattr(OwnedWorldBackend, "construct", classmethod(fail_last))
+            with pytest.raises(MemoryError, match="last actual owner"):
+                prepare(rig, before, "live_episode", None)
+        assert calls == list(IDS)
+    else:
+        original = torch.Tensor.clone
+        calls = []
+
+        def count_clone(value, *args, **kwargs):
+            calls.append(value.numel())
+            return original(value, *args, **kwargs)
+
+        with monkeypatch.context() as patch:
+            patch.setattr(torch.Tensor, "clone", count_clone)
+            prepare(rig, before, "live_episode", None)
+        last, count = len(calls), 0
+        assert last > 20
+
+        def fail_final_clone(value, *args, **kwargs):
+            nonlocal count
+            count += 1
+            if count == last:
+                raise MemoryError("last real tensor allocation")
+            return original(value, *args, **kwargs)
+
+        with monkeypatch.context() as patch:
+            patch.setattr(torch.Tensor, "clone", fail_final_clone)
+            with pytest.raises(MemoryError, match="last real tensor"):
+                prepare(rig, before, "live_episode", None)
+        assert count == last
+    assert rig.bank.mutation_revision == revision
+    same(ambient(), globals_before)
+    same(rig.bank.checkpoint_state(), before)
+    prepared = prepare(rig, before, "live_episode", None)
+    rig.bank.install_restore(prepared=prepared)
+    rig.event(6, IDS)
+
+
+def test_pending_completion_export_refuses_purely(compiled):
+    rig = Rig(compiled, "adaptive_rnd", "per_world", IDS)
+    rig.begin(1)
+    rig.actual_step()
+    rig.train()
+    arguments = rig.completion_arguments()
+    prepared = rig.bank.prepare_completion(**arguments)
+    revision, globals_before = rig.bank.mutation_revision, ambient()
+    report_count, issues = len(rig.reports), list(rig.issued)
+    with pytest.raises(REFUSAL):
+        rig.bank.checkpoint_state()
+    assert rig.bank.mutation_revision == revision and len(rig.reports) == report_count
+    same(rig.issued, issues)
+    same(ambient(), globals_before)
+    assert rig.bank.prepare_completion(**arguments) is prepared
+    receipt = rig.bank.commit_completion(prepared=prepared)
+    assert rig.bank.commit_completion(prepared=prepared) is receipt
+
+
+@pytest.mark.parametrize("order", (IDS, IDS[::-1]), ids=("same", "reversed"))
+def test_historical_completion_cannot_authorize_receiving_live_close(compiled, order):
+    source = Rig(compiled, "none", "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    _, arguments = source.complete()
+    history = source.bank.checkpoint_state()
+    receiving = Rig(compiled, "none", "per_world", order)
+    receiving.begin(1)
+    receiving.actual_step()
+    receiving.train()
+    before = receiving.bank.checkpoint_state()
+    no_live_change(receiving, before, lambda: prepare(receiving, history, "live_episode", None))
+    for evidence in (history["completion"], source.source_prepared.prepared_receipt, source.source_committed):
+        with pytest.raises(REFUSAL):
+            receiving.env.prepare_episode_close(
+                accepted=receiving.accepted,
+                boundary_key=1,
+                completion_content=arguments["completion_content"],
+                participated_world_ids=order,
+                dispositions=evidence,
+            )
+    with pytest.raises(REFUSAL):
+        receiving.bank.commit_completion(prepared=source.source_prepared)
+    assert receiving.env.world_phase == "active"
+
+
+@pytest.mark.parametrize("defect", ("parent_copy", "closure", "binding", "content", "prepared_status", "callback_late"))
+def test_completed_parent_correlation_refuses_before_install(compiled, defect):
+    source = Rig(compiled, "rnd", "per_world", IDS)
+    source.begin(1)
+    source.actual_step()
+    source.train()
+    world_state, _ = source.complete()
+    history = source.bank.checkpoint_state()
+    receiving = Rig(compiled, "rnd", "per_world", IDS[::-1])
+    parent = Correlation(receiving, world_state)
+    before = receiving.bank.checkpoint_state()
+    if defect == "closure":
+        history["completion"]["boundary_key"] += 1
+    elif defect == "binding":
+        history["completion"]["original_accepted_identity"]["world_ids"].reverse()
+    elif defect == "content":
+        history["completion"]["completion_content"] = (("00", "0" * 64),)
+    elif defect == "prepared_status":
+        history["completion"]["status"] = "prepared"
+    original = parent.validate
+
+    def validate(*, prepared, curiosity_state):
+        if defect == "parent_copy":
+            assert prepared is not parent.prepared
+        original(prepared=prepared, curiosity_state=curiosity_state)
+        if defect == "callback_late" and parent.calls == 2:
+            raise ValueError("late genuine correlation refusal")
+
+    revision, globals_before = receiving.bank.mutation_revision, ambient()
+    with pytest.raises((*REFUSAL, AssertionError)):
+        receiving.bank.prepare_restore(
+            state=history,
+            mode="completed_boundary",
+            accepted=None,
+            parent_restore=copy(parent.prepared) if defect == "parent_copy" else parent.prepared,
+            validate_parent_restore=validate,
+        )
+    assert receiving.bank.mutation_revision == revision
+    same(ambient(), globals_before)
+    same(receiving.bank.checkpoint_state(), before)
+    assert receiving.env.world_phase == "fresh-bound"
+    assert "prepared_dispositions" not in receiving.issued and "dispositions" not in receiving.issued
+
+
+def test_quarantine_requires_healthy_restore_not_native_export(compiled):
+    rig = Rig(compiled, "rnd", "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    saved = rig.bank.checkpoint_state()
+    rig.bank.quarantine_episode(accepted=rig.accepted, reason="runtime_failure")
+    revision = rig.bank.mutation_revision
+    with pytest.raises(RuntimeError):
+        rig.bank.checkpoint_state()
+    assert rig.bank.mutation_revision == revision
+    prepared = prepare(rig, saved, "live_episode", None)
+    rig.bank.install_restore(prepared=prepared)
+    same(rig.bank.checkpoint_state(), saved)
+    rig.event(6, IDS)
+
+
+@pytest.mark.parametrize("scope", ("shared", "per_world"))
+def test_count_scope_coupling_positive(compiled, scope):
+    rig = Rig(compiled, "count_based", scope, IDS)
+    rig.begin(1)
+    observations = torch.full((2, 3), 0.375)
+    context = IntrinsicTransitionContext(
+        predecessor=observations,
+        actions=torch.tensor([0, 0]),
+        successor=observations,
+        active_on_entry=torch.tensor([True, True]),
+        vector_tick=1,
+    )
+    stamp = rig.reserve(context)
+    reward = rig.bank.reward(context=context, stamp=stamp, accepted=rig.accepted, update_stats=True)
+    expected = torch.tensor([1.0, 2**-0.5 if scope == "shared" else 1.0])
+    torch.testing.assert_close(reward.raw, expected, rtol=1e-6, atol=0)
+    rig.bank.admit_and_service(context=context, stamp=stamp, accepted=rig.accepted)
+    saved = rig.bank.checkpoint_state()
+    rig.bank.install_restore(prepared=prepare(rig, saved, "live_episode", None))
+    same(rig.bank.checkpoint_state(), saved)
+
+
+@pytest.mark.parametrize("family", ("none", "count_based"))
+def test_zero_width_selected_family_control(compiled, family):
+    rig = Rig(compiled, family, "per_world", IDS)
+    descriptor = WorldCuriosityDescriptor.from_policy(rig.policy, world_ids=IDS, observation_dim=0, action_dim=2, training_seed=SEED)
+    reports = []
+
+    def construct():
+        return CuriosityBank(
+            policy=rig.policy,
+            descriptor=descriptor,
+            device="cpu",
+            validate_accepted_episode=rig.env.validate_accepted_episode,
+            issuer_factory=lambda owner: WorldReceiptIssuer(owner=owner),
+            report_allocation=reports.append,
+        )
+
+    if family == "count_based":
+        with pytest.raises(ValueError):
+            construct()
+        assert not reports
+    else:
+        bank = construct()
+        assert reports and bank.snapshot_world(world_id=IDS[0])["backend"]["backend"]["epsilon"] == rig.policy.epsilon_start
+
+
+def test_bank_entry_terminal_once_then_inactive(compiled):
+    rig = Rig(compiled, "rnd", "per_world", IDS)
+    rig.begin(1)
+    rig.event(1, IDS)
+    saved = rig.bank.checkpoint_state()
+    rig.bank.install_restore(prepared=prepare(rig, saved, "live_episode", None))
+    rig.event(2, (IDS[1],))
+    after = by_id(rig.bank.checkpoint_state())
+    assert after[IDS[0]]["cursor"]["cumulative_service_position"] == 1
+    assert after[IDS[1]]["cursor"]["cumulative_service_position"] == 2
+    same(after[IDS[0]]["backend"], by_id(saved)[IDS[0]]["backend"])
+
+
+def test_current_hc_preserves_captured_rows_and_private_counters(compiled):
+    """Actual HC owned-envelope unit; not an invented full DQN parent schema."""
+    rig = Rig(compiled, "icm", "per_world", IDS)
+    rig.begin(1)
+    rig.train()
+    state = rig.bank.checkpoint_state()
+    payload = captured_payload()
+    # HC preserves arbitrary supplied learned-state data; this fixture key is
+    # expressly test-owned and does not claim a production parent field name.
+    payload["pw06_test_owned_bank"] = state
+
+    def forbidden_legacy(_):
+        pytest.fail("current captured replay must not take the historical branch")
+
+    prepared = prepare_historical_envelope(payload, requested_mode="recorded_full_resume", validate_legacy=forbidden_legacy)
+    decoded = decode_historical_envelope(encode_historical_envelope(prepared))
+    retained = decoded.available_learned_state
+    independent(retained, payload)
+    assert decoded.policy.active_retained_transitions == 2
+    rig.bank.install_restore(prepared=prepare(rig, retained["pw06_test_owned_bank"], "live_episode", None))
+    same(rig.bank.checkpoint_state(), state)
+    rig.event(6, IDS)
