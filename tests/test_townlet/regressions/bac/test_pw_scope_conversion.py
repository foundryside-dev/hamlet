"""PW07: reject fabricated private past, lost learning, aliases and active archives.

Real BANK/providers/ENV/HC/replay; local other-role receipts qualify only interfaces.
Synthetic 3D curiosity inputs do not claim actual runner or sampler integration.
"""

from collections import OrderedDict
from collections.abc import Mapping
from copy import copy, deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.world_roster import WorldRosterDeclaration
from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
from townlet.exploration import curiosity_checkpoint as cp
from townlet.exploration.provider_factory import make_policy_selector
from townlet.exploration.scoped_curiosity import CuriosityBank
from townlet.exploration.world_curiosity_state import OwnedWorldBackend, ServiceClock, WorldCuriosityDescriptor, WorldRNGState
from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.state import RewardTensor
from townlet.universe.compiler import UniverseCompiler

FAMILIES = ("none", "count_based", "rnd", "adaptive_rnd", "icm")
TRAINABLE = ("rnd", "adaptive_rnd", "icm")
CHOICES = ("fresh_private", "clone_learned_archive_pending")
MODES = ("paced_fifo", "occupancy_fifo")
IDS = ("A", "B")


def equal(left, right):
    """Independent value witness; never call the production checkpoint comparator."""
    assert type(left) is type(right), (type(left), type(right))
    if isinstance(left, torch.Tensor):
        assert (left.dtype, left.shape, left.device, left.layout) == (right.dtype, right.shape, right.device, right.layout)
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, Mapping):
        assert left.keys() == right.keys()
        if isinstance(left, OrderedDict):
            assert list(left) == list(right)
        for key in left:
            equal(left[key], right[key])
        if hasattr(left, "_metadata"):
            equal(left._metadata, right._metadata)
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            equal(a, b)
    else:
        assert left == right


def storages(value):
    if isinstance(value, torch.Tensor):
        return {value.untyped_storage().data_ptr()} if value.numel() else set()
    if isinstance(value, Mapping):
        return set().union(*(storages(item) for item in value.values()))
    if isinstance(value, (tuple, list)):
        return set().union(*(storages(item) for item in value))
    return set()


@pytest.fixture(scope="module")
def compiled():
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


def policy(compiled, family, scope, mode):
    level = compiled.get_level("L0_test")
    drive = IntrinsicStrategyConfig.model_validate(dict(level.drive.intrinsic.model_dump(), strategy=family))
    data = deepcopy(level.training.model_dump())
    data["replay_buffer"]["batch_size"] = 2
    data["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
    data["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.01)
    data["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    data["training_loop"]["max_steps_per_episode"] = 20
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
            "provider_parameter_source": "training",
            "rnd": {"service_mode": mode, "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
            "providers": {
                "count_based": {"quantization_width": 0.125, "max_entries": 4},
                "icm": {
                    "feature_dim": 4,
                    "hidden_dim": 8,
                    "learning_rate": 0.001,
                    "inverse_weight": 0.8,
                    "forward_weight": 0.2,
                    "training_batch_size": 2,
                    "max_pending_transitions": 4,
                },
            },
        }
    )
    return resolve_exploration_policy(drive, TrainingV2Config.model_validate(data), options)


class Rig:
    """Actual ENV authority; other roles are explicitly local receipt interfaces."""

    def __init__(self, compiled, selected, ids=IDS, *, width=3, seed=701, membership=IDS):
        self.roster = WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(membership)})
        self.env = VectorizedHamletEnv(
            universe=compiled,
            level_name="L0_test",
            num_agents=len(ids),
            device="cpu",
            world_roster=self.roster,
            training_seed=seed,
            lane_world_ids=ids,
        )
        self.reports = []
        descriptor = WorldCuriosityDescriptor.from_policy(
            selected,
            world_ids=ids,
            observation_dim=width,
            action_dim=2,
            training_seed=seed,
        )
        self.bank = CuriosityBank(
            policy=selected,
            descriptor=descriptor,
            device="cpu",
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=lambda owner: WorldReceiptIssuer(owner=owner),
            report_allocation=self.reports.append,
        )
        self.issuer = WorldReceiptIssuer(owner=self)
        roles = {
            name: self for name in ("population", "curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")
        }
        roles["curiosity"] = self.bank
        self.authority = self.env.bind_boundary_authority(owner=self, role_owners=roles)
        self.release = None
        self.accepted = None
        self.batches = []

    def begin(self, batch):
        if self.release is None:
            self.release = self.env.install_boundary_release(self.authority.bootstrap(first_batch_episode=batch))
        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
        self.env.validate_episode_reservation(reservation)
        self.accepted = self.env.reset(reservation=reservation).accepted
        self.env.activate_episode(
            accepted=self.accepted,
            population_receipt=self.issuer.issue(kind="activation", payload={"accepted": self.accepted}),
            curiosity_receipt=self.bank.begin_episode(accepted=self.accepted),
        )
        self.batches.append(batch)

    def step(self, tick, active=(True, True)):
        # Actual ENV supplies participation and authority; curiosity uses explicit synthetic geometry.
        for index, eligible in enumerate(active):
            if not eligible:
                self.env.dones[index] = True
        actions = self.env.get_action_masks().to(torch.int64).argmax(dim=1)
        self.env.step(actions, depletion_multiplier=1.0)
        return service(self.bank, self.accepted, tick, active)

    def close(self):
        token = self.accepted
        participants = tuple(world for world in token.world_ids if self.bank._cursor[world]["participated"])
        outcomes = tuple(
            LaneOutcome(
                outcome=EpisodeCompletion(
                    agent_idx=token.world_ids.index(world),
                    reason="cap",
                    survival_time=int(self.env.step_counts[token.world_ids.index(world)].item()),
                    final_observation=torch.zeros(3),
                    final_meters=self.env.meters[token.world_ids.index(world)].detach().cpu().clone(),
                ),
                batch_episode=token.batch_episode,
                planned_horizon=20,
                reward_total=1.0,
                reward_extrinsic=0.5,
                reward_intrinsic=0.5,
                reward_shaping=0.0,
                policy_entropy=0.0,
                world_id=world,
                world_episode_seq=token.world_episode_seqs[token.world_ids.index(world)],
            )
            for world in participants
        )
        content = tuple((value.payload.hex(), value.fingerprint) for value in map(freeze_lane_outcome, outcomes))
        prepared = self.bank.prepare_completion(
            accepted=token,
            boundary_key=token.batch_episode,
            completion_content=content,
            outcomes=outcomes,
            participated_world_ids=participants,
        )
        closing = self.env.prepare_episode_close(
            accepted=token,
            boundary_key=token.batch_episode,
            completion_content=content,
            participated_world_ids=participants,
            dispositions=prepared.prepared_receipt,
        )
        self.env.freeze_episode_close(closing)
        dispositions = self.bank.commit_completion(prepared=prepared)
        closure = self.env.close_episode(closing, dispositions=dispositions)
        fields = dict(accepted=token, boundary_key=token.batch_episode, completion_content=content)
        children = {
            name: self.issuer.issue(kind=name, payload=fields)
            for name in (
                "curriculum_receipt",
                "exploration_receipt",
                "epsilon_install_receipt",
                "population_commit_receipt",
                "selection_sync_receipt",
            )
        }
        effects = self.issuer.issue(
            kind="boundary_effects",
            payload=dict(
                batch_episode=token.batch_episode,
                accepted_identity=token,
                completion_content=content,
                retirement_receipt=dispositions,
                **children,
            ),
        )
        self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))

    def world_state(self):
        return self.env.checkpoint_world_state(
            kind="COMPLETED",
            release=self.release,
            retained_binding_batches=tuple(self.batches),
            initial=None,
        )

    def prepare_parent(self, source):
        world_state = source.world_state()
        self.parent = self.env.prepare_world_restore(
            kind="COMPLETED",
            state=world_state,
            world_roster=self.roster,
            destination_world_ids=self.env.world_ids,
            semantic_execution_identity=self.env.semantic_execution_identity,
        )
        self.views = []

        def validate(*, prepared, curiosity_state):
            # Real ENV authority authenticates the retained record and native parent state.
            boundary = self.issuer.issue(
                kind="restored_boundary", payload={"kind": "COMPLETED", "state": world_state, "prepared": prepared}
            )
            self.restored_release = self.authority.restored(restore=prepared, boundary=boundary)
            assert prepared is self.parent
            self.views.append(curiosity_state)

        self.validate_parent = validate
        return self.parent, validate

    def install_parent(self):
        self.release = self.env.install_world_restore(prepared=self.parent, release=self.restored_release)


def service(bank, accepted, tick, active):
    rows = len(accepted.world_ids)
    predecessor = torch.arange(rows * 3, dtype=torch.float32).reshape(rows, 3) * 0.07 + tick * 0.2
    context = IntrinsicTransitionContext(
        predecessor=predecessor,
        successor=predecessor + 0.11,
        actions=torch.tensor([index % 2 for index in range(rows)]),
        active_on_entry=torch.tensor(active),
        vector_tick=tick,
    )
    stamp = bank.prepare_step_stamp(
        accepted=accepted, world_ids=accepted.world_ids, active_on_entry=context.active_on_entry, vector_tick=tick
    )
    reward = bank.reward(context=context, stamp=stamp, accepted=accepted, update_stats=True)
    receipts = bank.admit_and_service(context=context, stamp=stamp, accepted=accepted)
    return context, stamp, reward, receipts


def backend(bank, world="A"):
    """Shared-only test seam; private providers never escape an owned callback."""
    assert bank.scope == "shared", "inspect private state inside on_backend callback"
    return bank._shared


def on_backend(bank, operation, world="A"):
    if bank.scope == "shared":
        return operation(bank._shared)
    return bank._owners[world].call(lambda provider, sources: operation(provider))


def validate_live(bank, state, world="A"):
    on_backend(bank, lambda provider: provider.validate_state(state), world)


def observe_training(bank, family, world="A"):
    batches, handles = [], []

    def observe(module, inputs):
        if torch.is_grad_enabled():
            batches.append(inputs[0].detach().clone())

    def install(provider):
        model = provider.encoder if family == "icm" else (provider.rnd if family == "adaptive_rnd" else provider).predictor_network
        handles.append(model.register_forward_pre_hook(observe))

    def remove(provider):
        for handle in handles:
            handle.remove()

    on_backend(bank, install, world)
    return batches, lambda: on_backend(bank, remove, world)


def modules(provider, family):
    if family == "adaptive_rnd":
        return {"rnd.predictor_network": provider.rnd.predictor_network}
    if family == "rnd":
        return {"predictor_network": provider.predictor_network}
    if family == "icm":
        return {key: getattr(provider, key) for key in ("encoder", "inverse_model", "forward_model")}
    return {}


def native_ledger(native, family):
    if family == "adaptive_rnd":
        native = native["rnd_state"]
    if family in ("rnd", "adaptive_rnd"):
        values = native["predictor_service"]
        return values, values["pending_observations"]
    return native["counters"], native["pending"]


def snapshot_native(snapshot):
    return snapshot["backend"]["backend"]


def learned(native, family):
    if family == "adaptive_rnd":
        return {key: learned(value, "rnd") if key == "rnd_state" else value for key, value in native.items()}
    if family == "rnd":
        return {
            key: native[key]
            for key in (
                "fixed_network",
                "predictor_network",
                "optimizer",
                "reward_rms_mean",
                "reward_rms_var",
                "reward_rms_count",
            )
        }
    if family == "icm":
        return {key: native[key] for key in ("encoder", "inverse_model", "forward_model", "optimizer", "last_loss")}
    if family == "count_based":
        return {key: native[key] for key in ("counts", "lru", "eviction_count")}
    return native


def live(bank, world="A"):
    return on_backend(bank, lambda provider: live_provider(provider, bank.policy.strategy), world)


def live_provider(provider, family):
    params = [p for module in modules(provider, family).values() for p in module.parameters()]
    gradients = {
        key: {name: None if p.grad is None else p.grad.detach().clone() for name, p in module.named_parameters()}
        for key, module in modules(provider, family).items()
    }
    refs = tuple((id(p), p.data_ptr(), None if p.grad is None else p.grad.data_ptr()) for p in params)
    storage_ids = {p.data_ptr() for p in params} | {p.grad.data_ptr() for p in params if p.grad is not None}
    if family in ("rnd", "adaptive_rnd"):
        rnd = provider.rnd if family == "adaptive_rnd" else provider
        assert all(p.grad is None for p in rnd.fixed_network.parameters())
        storage_ids.update(p.data_ptr() for p in rnd.fixed_network.parameters())
    adam = provider.rnd.optimizer if family == "adaptive_rnd" else getattr(provider, "optimizer", None)
    if adam is not None:
        grouped = [p for group in adam.param_groups for p in group["params"]]
        assert {id(p) for p in grouped} == {id(p) for p in params}
        assert {id(p) for p in adam.state}.issubset({id(p) for p in params})
        refs += tuple(
            (id(p), tuple(v.data_ptr() for v in state.values() if isinstance(v, torch.Tensor))) for p, state in adam.state.items()
        )
        storage_ids.update(v.data_ptr() for state in adam.state.values() for v in state.values() if isinstance(v, torch.Tensor))
    return {
        "provider_id": id(provider),
        "native": provider.checkpoint_state(),
        "gradients": gradients,
        "refs": refs,
        "storage_ids": tuple(sorted(storage_ids)),
    }


def set_gradients(bank):
    def assign(provider):
        parameters = (p for module in modules(provider, bank.policy.strategy).values() for p in module.parameters())
        for index, parameter in enumerate(parameters):
            parameter.grad = None if index % 3 == 0 else torch.full_like(parameter, 0.0 if index % 3 == 1 else 0.125)

    on_backend(bank, assign)


def trained_source(compiled, family, mode):
    source = Rig(compiled, policy(compiled, family, "shared", mode))
    original = live(source.bank)
    episodes = 5 if family == "adaptive_rnd" else 1
    for batch in range(episodes):
        source.begin(batch)
        for step in range(1, 6):
            source.step(batch * 10 + step, (True, step < 5))
        source.close()
    set_gradients(source.bank)
    state = source.bank.checkpoint_state()
    source.original = original
    source.saved = state
    return source


def destination(compiled, source, ids=IDS):
    target = Rig(compiled, policy(compiled, source.bank.policy.strategy, "per_world", source.bank.policy.service_mode), ids)
    target.prepare_parent(source)
    return target


def prepare(target, state, choice):
    return target.bank.prepare_private_initialization(
        state=state,
        initialization=choice,
        parent_restore=target.parent,
        validate_parent_restore=target.validate_parent,
    )


def convert(target, state, choice):
    token = prepare(target, state, choice)
    target.bank.install_restore(prepared=token)
    target.install_parent()
    return token


def assert_source(source, before, state):
    equal(live(source.bank), before)
    equal(source.bank.checkpoint_state(), state)


def assert_future(snapshot, family, admissions, updates):
    assert snapshot["cursor"]["cumulative_service_position"] == admissions
    counters = snapshot["future_service_counters"]
    if family not in TRAINABLE:
        assert counters is None
        return
    assert counters["admitted_rows"] == admissions
    assert counters["optimizer_updates"] == updates
    assert counters["consumed_rows"] == updates * 2
    assert counters["dropped_rows"] == 0
    assert counters["pending_rows"] == admissions - updates * 2
    assert counters["mandatory_service_updates"] == (0 if family == "icm" else None)


def assert_baseline(bank, source, choice, world, local_admitted, local_updates):
    """Derive the native ledger independently of the production diagnostic deltas."""
    snapshot, family = bank.snapshot_world(world_id=world), bank.policy.strategy
    origin = snapshot["initialization_origin"]
    if family not in TRAINABLE:
        assert origin["inherited_baseline"] is None
        return
    old, _ = native_ledger(source["shared_backend"]["native"], family)
    expected = {name: old[name] if choice == CHOICES[1] else 0 for name in ("consumed_rows", "dropped_rows", "optimizer_updates")}
    expected["admitted_rows"] = expected["consumed_rows"] + expected["dropped_rows"]
    expected["mandatory_service_updates"] = old["mandatory_service_updates"] if family == "icm" and choice == CHOICES[1] else 0
    if family != "icm":
        expected["mandatory_service_updates"] = None
    equal(origin["inherited_baseline"], expected)
    native = snapshot_native(snapshot)
    actual, pending = native_ledger(native, family)
    for key, delta in (("admitted_rows", local_admitted), ("consumed_rows", local_updates * 2), ("optimizer_updates", local_updates)):
        assert actual[key] == expected[key] + delta
    assert actual["dropped_rows"] == expected["dropped_rows"]
    assert len(pending) == local_admitted - local_updates * 2
    clock = native if family == "icm" else actual
    assert clock["service_position"] == expected["admitted_rows"] + local_admitted
    assert clock["service_clock_unit"] == "world_eligible_admission"


def poison_shared_numeric(state, family):
    """Mutate real transport storage, including each learned/pending ownership class."""
    payload = state["shared_backend"]
    native = payload["native"]
    if family == "adaptive_rnd":
        native["survival_history"][0] += 3
        native = native["rnd_state"]
    if family in TRAINABLE:
        key = "encoder" if family == "icm" else "predictor_network"
        next(iter(native[key].values())).add_(10)
        if family != "icm":
            next(iter(native["fixed_network"].values())).add_(12)
        next(iter(native["optimizer"]["state"].values()))["exp_avg"].add_(2)
        next(value for group in payload["gradients"].values() for value in group.values() if value is not None).add_(4)
        tail = native["pending"] if family == "icm" else native["predictor_service"]["pending_observations"]
        (tail[0]["predecessor"] if family == "icm" else tail[0]).add_(6)
    elif family == "count_based":
        native["counts"][next(iter(native["counts"]))] += 11
        native["lru"].reverse()
    else:
        native["epsilon"] *= 0.5


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("mode", MODES)
def test_fixture_actual_shared_learning_and_completed_parent(compiled, family, mode):
    """Prerequisite: wrong fixture or fake learning must fail before conversion RED."""
    source = trained_source(compiled, family, mode)
    native = source.saved["shared_backend"]["native"]
    if family in TRAINABLE:
        counters, pending = native_ledger(native, family)
        assert counters["optimizer_updates"] >= 2
        assert len(pending) == 1
        assert counters["admitted_rows"] == counters["consumed_rows"] + counters["dropped_rows"] + 1
        provider = backend(source.bank)
        provider.validate_state(native)
        actual = learned(native, family)
        assert storages(actual).isdisjoint(storages(source.original["native"]))
        first_module = next(iter(modules(provider, family).values()))
        initial_native = source.original["native"]
        if family == "adaptive_rnd":
            initial_native = initial_native["rnd_state"]
            assert len(native["survival_history"]) == 10
            assert native["current_intrinsic_weight"] < native["initial_intrinsic_weight"]
        key = "encoder" if family == "icm" else "predictor_network"
        assert any(not torch.equal(value, initial_native[key][name]) for name, value in first_module.state_dict().items())
        adam = provider.rnd.optimizer if family == "adaptive_rnd" else provider.optimizer
        assert adam.state and any(bool(state["exp_avg"].abs().sum() > 0) for state in adam.state.values())
        gradients = live(source.bank)["gradients"]
        values = [value for group in gradients.values() for value in group.values()]
        assert any(value is None for value in values)
        assert any(value is not None and not bool(value.any()) for value in values)
        assert any(value is not None and bool(value.any()) for value in values)
    elif family == "count_based":
        assert native["counts"] and native["eviction_count"] > 0 and len(native["lru"]) == 4
    target = destination(compiled, source)
    target.validate_parent(prepared=target.parent, curiosity_state=deepcopy(source.saved))
    assert target.restored_release.next_batch_episode == source.accepted.batch_episode + 1


def test_fixture_icm_rejects_erased_updates_with_inherited_adam(compiled):
    """Control: fake counter reset cannot pass the unchanged real ICM validator."""
    source = trained_source(compiled, "icm", "paced_fifo")
    native = deepcopy(source.saved["shared_backend"]["native"])
    native["counters"].update(admitted_rows=0, consumed_rows=0, dropped_rows=0, optimizer_updates=0, mandatory_service_updates=0)
    native.update(pending=[], last_loss=0.0, ordinary_updates_at_position=0)
    before = live(source.bank)
    with pytest.raises(ValueError):
        backend(source.bank).validate_state(native)
    equal(live(source.bank), before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("choice", CHOICES)
@pytest.mark.parametrize("mode", MODES)
def test_fresh_private_and_clone_learned_origins(compiled, family, choice, mode):
    """Catches erased Adam/gradients, fake private past, aliases and lost baseline on resume."""
    source = trained_source(compiled, family, mode)
    source_live = live(source.bank)
    target = destination(compiled, source)
    fresh = {world: live(target.bank, world) for world in IDS}
    fresh_rng = {world: target.bank.snapshot_world(world_id=world)["backend"]["rng"] for world in IDS}
    selector = make_policy_selector(target.bank.policy)
    selector_before = selector.checkpoint_state()
    convert(target, source.saved, choice)
    exported = target.bank.checkpoint_state()
    assert exported["schema"] == "curiosity-bank-state-v2"
    assert exported["curiosity_epoch"] == 1 and exported["bank_phase"] == "private_initialized"
    assert exported["completion"] is None and exported["step"] is None and exported["dispatch_identity"] is None
    origin = exported["initialization_origin"]
    assert origin["initialization"] == choice
    assert origin["native_counter_basis"] == "inherited_settled_plus_future_local"
    equal(origin["source_checkpoint"], source.saved)
    for world in IDS:
        snapshot = target.bank.snapshot_world(world_id=world)
        assert_future(snapshot, family, 0, 0)
        assert_baseline(target.bank, source.saved, choice, world, 0, 0)
        equal(snapshot["backend"]["rng"], fresh_rng[world])
        cursor = snapshot["cursor"]
        assert cursor["accepted_episode_seq"] == source.accepted.world_episode_seqs[IDS.index(world)]
        assert cursor["eligible_seq"] == 0 and cursor["participated"] is False and cursor["disposition"] is None
        assert snapshot["phase_cache"] == {} and snapshot["accepted_identity"] is None
        actual = live(target.bank, world)
        expected = source_live if choice == CHOICES[1] else fresh[world]
        equal(learned(actual["native"], family), learned(expected["native"], family))
        equal(actual["gradients"], expected["gradients"])
        assert storages(actual).isdisjoint(storages(source_live))
        assert set(actual["storage_ids"]).isdisjoint(source_live["storage_ids"])
        if family in TRAINABLE:
            validate_live(target.bank, actual["native"], world)
            counters, queue = native_ledger(actual["native"], family)
            assert len(queue) == 0
            assert counters["admitted_rows"] == counters["consumed_rows"] + counters["dropped_rows"]
    a, b = live(target.bank, "A"), live(target.bank, "B")
    assert storages(a).isdisjoint(storages(b))
    assert set(a["storage_ids"]).isdisjoint(b["storage_ids"])
    b_rng = target.bank.snapshot_world(world_id="B")["backend"]["rng"]
    assert_source(source, source_live, source.saved)
    # Ordinary resume must understand the new origin phase without manufacturing close authority.
    resumed = destination(compiled, source, ("B", "A"))
    handle = resumed.bank.prepare_restore(
        state=exported,
        mode="private_initialized",
        accepted=None,
        parent_restore=resumed.parent,
        validate_parent_restore=resumed.validate_parent,
    )
    resumed.bank.install_restore(prepared=handle)
    resumed.install_parent()
    for world in IDS:
        equal(learned(live(resumed.bank, world)["native"], family), learned(live(target.bank, world)["native"], family))
        equal(live(resumed.bank, world)["gradients"], live(target.bank, world)["gradients"])
    target.begin(source.accepted.batch_episode + 1)
    context, stamp, _, receipts = target.step(101, (True, False))
    assert stamp.event_ids[0].curiosity_epoch == 1 and stamp.event_ids[0].eligible_seq == 1
    if family in TRAINABLE:
        assert receipts[0].clock.position == 1
    settled = live(target.bank, "A")
    retry = target.bank.admit_and_service(context=context, stamp=stamp, accepted=target.accepted)
    assert retry == receipts
    equal(live(target.bank, "A"), settled)
    obsolete = type(stamp)(
        event_ids=tuple(type(event)(0, event.world_id, event.world_episode_seq, event.eligible_seq) for event in stamp.event_ids),
        world_ids=stamp.world_ids,
        world_episode_seqs=stamp.world_episode_seqs,
        eligible_seqs=stamp.eligible_seqs,
        eligible=stamp.eligible,
    )
    with pytest.raises(ValueError):
        target.bank.admit_and_service(context=context, stamp=obsolete, accepted=target.accepted)
    equal(live(target.bank, "A"), settled)
    target.step(102, (True, False))
    assert_future(target.bank.snapshot_world(world_id="A"), family, 2, 1)
    assert_baseline(target.bank, source.saved, choice, "A", 2, 1)
    if family in TRAINABLE:
        after = live(target.bank, "A")["native"]
        previous = native_ledger(a["native"], family)[0]["optimizer_updates"]
        assert native_ledger(after, family)[0]["optimizer_updates"] == previous + 1
        inner = after["rnd_state"] if family == "adaptive_rnd" else after
        old_inner = a["native"]["rnd_state"] if family == "adaptive_rnd" else a["native"]
        model_key = "encoder" if family == "icm" else "predictor_network"
        assert any(not torch.equal(value, old_inner[model_key][name]) for name, value in inner[model_key].items())
    equal(live(target.bank, "B"), b)
    equal(target.bank.snapshot_world(world_id="B")["backend"]["rng"], b_rng)
    assert_source(source, source_live, source.saved)
    equal(selector.checkpoint_state(), selector_before)
    # Actual private completion/resume retains the baseline into the next genuine update.
    target.close()
    completed = target.bank.checkpoint_state()
    restored = Rig(compiled, target.bank.policy)
    restored.prepare_parent(target)
    token = restored.bank.prepare_restore(
        state=completed,
        mode="completed_boundary",
        accepted=None,
        parent_restore=restored.parent,
        validate_parent_restore=restored.validate_parent,
    )
    restored.bank.install_restore(prepared=token)
    restored.install_parent()
    restored.begin(target.accepted.batch_episode + 1)
    restored.step(201, (True, False))
    restored.step(202, (True, False))
    assert_future(restored.bank.snapshot_world(world_id="A"), family, 4, 2)
    assert restored.bank.checkpoint_state()["curiosity_epoch"] == 1
    equal(selector.checkpoint_state(), selector_before)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("choice", CHOICES)
@pytest.mark.parametrize("mode", MODES)
def test_shared_pending_is_archived_not_falsely_attributed(compiled, family, choice, mode):
    """Catches dropped/reordered archives and any archive-to-active service route."""
    source = trained_source(compiled, family, mode)
    source_live = live(source.bank)
    target = destination(compiled, source)
    caller_state = deepcopy(source.saved)
    fresh = {world: live(target.bank, world) for world in IDS}
    ambient = torch.get_rng_state().clone()
    token = prepare(target, caller_state, choice)
    equal(torch.get_rng_state(), ambient)
    caller_state["worlds"][0]["cursor"]["eligible_seq"] = 999
    poison_shared_numeric(caller_state, family)
    for retained in target.views:
        retained.clear()
    target.bank.install_restore(prepared=token)
    target.install_parent()
    snapshot = target.bank.snapshot_world(world_id="A")
    equal(snapshot["initialization_origin"]["source_checkpoint"], source.saved)
    snapshot["initialization_origin"]["source_checkpoint"]["worlds"][0]["cursor"]["eligible_seq"] = 888
    poison_shared_numeric(snapshot["initialization_origin"]["source_checkpoint"], family)
    equal(target.bank.checkpoint_state()["initialization_origin"]["source_checkpoint"], source.saved)
    for world in IDS:
        expected = source_live if choice == CHOICES[1] else fresh[world]
        equal(learned(live(target.bank, world)["native"], family), learned(expected["native"], family))
        equal(live(target.bank, world)["gradients"], expected["gradients"])
    if family in TRAINABLE:
        native, pending = native_ledger(live(target.bank)["native"], family)
        assert len(pending) == 0
        trained_batches, remove_hook = observe_training(target.bank, family)
    before_b = live(target.bank, "B")
    target.begin(source.accepted.batch_episode + 1)
    first, _, _, _ = target.step(301, (True, False))
    second, _, _, _ = target.step(302, (True, False))
    if family in TRAINABLE:
        remove_hook()
        equal(trained_batches[0], torch.cat((first.predecessor[:1], second.predecessor[:1])))
        actual, pending = native_ledger(live(target.bank)["native"], family)
        baseline = native["optimizer_updates"]
        assert actual["optimizer_updates"] == baseline + 1 and len(pending) == 0
        # Complete local B2 batch consists only of these new A rows; no source tail can be consumed.
        source_tail = native_ledger(source.saved["shared_backend"]["native"], family)[1]
        assert len(source_tail) == 1
        validate_live(target.bank, live(target.bank)["native"])
    equal(live(target.bank, "B"), before_b)
    assert_future(target.bank.snapshot_world(world_id="A"), family, 2, 1)
    equal(target.bank.checkpoint_state()["initialization_origin"]["source_checkpoint"], source.saved)
    assert_source(source, source_live, source.saved)


def recorded_replay():
    replay = ReplayBuffer(capacity=4, device=torch.device("cpu"))
    observations = torch.tensor([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    replay.push_recorded(
        observations=observations,
        actions=torch.tensor([0, 1]),
        rewards=RewardTensor(
            torch.tensor([1.0, 2.0]), extrinsic=torch.tensor([0.5, 1.0]), intrinsic=torch.tensor([0.5, 1.0]), shaping=None, is_composed=True
        ),
        next_observations=observations + 0.1,
        dones=torch.tensor([False, True]),
        next_action_masks=torch.tensor([[True, False], [False, False]]),
    )
    return replay


def replay_roundtrip(replay):
    from townlet.training import historical_checkpoint as hc

    saved = replay.serialize()
    payload = dict(
        version=10,
        action_dim=2,
        episode=3,
        completed_live_agent_steps=7,
        population_state=dict(version=7, total_steps=9, training_step_counter=2, replay_buffer=saved),
    )

    def no_legacy(_):
        raise AssertionError("current captured replay entered obsolete-format validation")

    access = hc.resolve_historical_access(payload, requested_mode="recorded_full_resume")
    assert access.effective_mode == "recorded_full_resume" and access.active_retained_transitions == 2
    assert access.archived_row_count == 0
    envelope = hc.prepare_historical_envelope(payload, requested_mode="recorded_full_resume", validate_legacy=no_legacy)
    decoded = hc.decode_historical_envelope(hc.encode_historical_envelope(envelope))
    equal(decoded.available_learned_state, payload)
    assert decoded.archives == ()
    restored = ReplayBuffer(capacity=4, device=torch.device("cpu"))
    restored.load_prepared(
        restored.prepare_serialized(decoded.available_learned_state["population_state"]["replay_buffer"], expected_obs_dim=3)
    )
    equal(restored.serialize(), saved)
    assert len(restored) == restored.retained_transitions == 2
    assert bool(saved["legality_recorded"].all()) and bool(saved["rewards_intrinsic_present"].all())
    assert not bool(saved["rewards_shaping_present"].any())
    equal(saved["next_action_masks"], torch.tensor([[True, False], [False, False]]))
    with pytest.raises(ValueError):
        hc.resolve_historical_access(payload, requested_mode="archived_history_fresh_episode")
    with pytest.raises(ValueError):
        restored.load_for_mode(saved, requested_mode="archived_history_fresh_episode")
    equal(restored.serialize(), saved)
    return restored, payload, decoded


def test_fixture_current_hc_and_active_replay_roundtrip():
    """Prerequisite: real captured replay must survive real HC and replay loaders."""
    replay_roundtrip(recorded_replay())


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("choice", CHOICES)
@pytest.mark.parametrize("mode", MODES)
def test_current_captured_replay_is_preserved(compiled, family, choice, mode):
    """Catches confusing curiosity's inactive tail archive with active captured REPLAY."""
    source = trained_source(compiled, family, mode)
    replay = recorded_replay()
    saved = replay.serialize()
    restored, payload, envelope = replay_roundtrip(replay)
    target = destination(compiled, source)
    convert(target, source.saved, choice)
    equal(replay.serialize(), saved)
    equal(restored.serialize(), saved)
    equal(envelope.available_learned_state, payload)
    assert len(restored) == 2 and len(restored.historical_archives) == 0
    # Mutate the actual receiving replay via its public producer, not a returned copy.
    extra = recorded_replay().serialize()
    restored.push_recorded(
        observations=extra["observations"],
        actions=extra["actions"],
        rewards=RewardTensor(
            extra["rewards"],
            extrinsic=extra["rewards_extrinsic"],
            intrinsic=extra["rewards_intrinsic"],
            shaping=None,
            is_composed=True,
        ),
        next_observations=extra["next_observations"],
        dones=extra["dones"],
        next_action_masks=extra["next_action_masks"],
    )
    assert len(restored) == 4
    equal(replay.serialize(), saved)
    equal(envelope.available_learned_state, payload)


@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("choice", CHOICES)
def test_initial_conversion_has_no_episode_or_closing_history(compiled, family, choice):
    """Catches an INITIAL template inventing an accepted episode or completed history."""
    source = Rig(compiled, policy(compiled, family, "shared", "paced_fifo"))
    state = source.bank.checkpoint_state()
    target = Rig(compiled, policy(compiled, family, "per_world", "paced_fifo"))
    token = target.bank.prepare_private_initialization(
        state=state,
        initialization=choice,
        parent_restore=None,
        validate_parent_restore=None,
    )
    target.bank.install_restore(prepared=token)
    saved = target.bank.checkpoint_state()
    assert saved["bank_phase"] == "initial" and saved["curiosity_epoch"] == 1
    assert saved["completion"] is None and saved["dispatch_identity"] is None
    for world in IDS:
        snapshot = target.bank.snapshot_world(world_id=world)
        assert snapshot["cursor"]["accepted_episode_seq"] == 0
        assert snapshot["accepted_identity"] is None and snapshot["phase_cache"] == {}
        assert_future(snapshot, family, 0, 0)
    target.begin(0)
    _, stamp, _, _ = target.step(1)
    assert all(event.world_episode_seq == 1 and event.curiosity_epoch == 1 for event in stamp.event_ids)


@pytest.mark.parametrize("family", FAMILIES)
def test_source_shared_and_live_same_scope_restore_remain_real(compiled, family):
    """Positive countercontrol: explicit conversion must not damage ordinary restore."""
    source = trained_source(compiled, family, "paced_fifo")
    restored = Rig(compiled, source.bank.policy)
    restored.prepare_parent(source)
    token = restored.bank.prepare_restore(
        state=source.saved,
        mode="completed_boundary",
        accepted=None,
        parent_restore=restored.parent,
        validate_parent_restore=restored.validate_parent,
    )
    restored.bank.install_restore(prepared=token)
    restored.install_parent()
    equal(live(restored.bank)["native"], live(source.bank)["native"])
    restored.begin(source.accepted.batch_episode + 1)
    restored.step(100)
    active = restored.bank.checkpoint_state()
    before = live(restored.bank)
    token = restored.bank.prepare_restore(
        state=active,
        mode="live_episode",
        accepted=restored.accepted,
        parent_restore=None,
        validate_parent_restore=None,
    )
    restored.bank.install_restore(prepared=token)
    equal(live(restored.bank)["native"], before["native"])
    restored.step(101)
    if family in TRAINABLE:
        counters, _ = native_ledger(live(restored.bank)["native"], family)
        previous, _ = native_ledger(before["native"], family)
        assert counters["optimizer_updates"] > previous["optimizer_updates"]
    assert restored.bank.checkpoint_state()["curiosity_epoch"] == 0


@pytest.mark.parametrize("mutation", ("epoch", "membership", "policy", "gradient", "adam", "pending", "choice", "ordinary", "parent"))
def test_invalid_conversion_refuses_without_live_effects(compiled, mutation):
    """Catches conversion using malformed source data, implicit fallback or false custody."""
    source = trained_source(compiled, "icm", "paced_fifo")
    target = destination(compiled, source)
    state = deepcopy(source.saved)
    before = {world: live(target.bank, world) for world in IDS}
    source_before = live(source.bank)
    revision = target.bank.mutation_revision
    choice = CHOICES[1]
    if mutation == "epoch":
        state["curiosity_epoch"] = True
    elif mutation == "membership":
        state["worlds"][-1]["world_id"] = "A"
    elif mutation == "policy":
        state["policy"]["provider_parameters"]["learning_rate"] = 0.2
    elif mutation == "gradient":
        values = state["shared_backend"]["gradients"]["encoder"]
        values[next(iter(values))] = torch.zeros(1)
    elif mutation == "adam":
        values = state["shared_backend"]["native"]["optimizer"]["state"]
        values[next(iter(values))]["exp_avg_sq"].fill_(-1)
    elif mutation == "pending":
        state["shared_backend"]["native"]["pending"][-1]["action"] = 2
    elif mutation == "choice":
        choice = "automatic"
    elif mutation == "parent":
        target.parent = copy(target.parent)
    with pytest.raises(ValueError):
        if mutation == "ordinary":
            target.bank.prepare_restore(
                state=state,
                mode="completed_boundary",
                accepted=None,
                parent_restore=target.parent,
                validate_parent_restore=target.validate_parent,
            )
        else:
            prepare(target, state, choice)
    assert target.bank.mutation_revision == revision
    for world in IDS:
        equal(live(target.bank, world), before[world])
    equal(live(source.bank), source_before)
    # Fresh genuine input remains usable after refusal (foreign preparation case needs a new target).
    if mutation == "parent":
        target = destination(compiled, source)
    convert(target, source.saved, CHOICES[1])


@pytest.mark.parametrize("failure", ("report", "late_allocation"))
def test_allocation_refusal_is_before_publication_and_retryable(compiled, monkeypatch, failure):
    """Catches partial destination publication and late allocations after the live swap."""
    source = trained_source(compiled, "icm", "paced_fifo")
    target = destination(compiled, source)
    before = {world: live(target.bank, world) for world in IDS}
    rng_before = {world: target.bank.snapshot_world(world_id=world)["backend"]["rng"] for world in IDS}
    ambient = torch.get_rng_state().clone()
    source_before, revision = live(source.bank), target.bank.mutation_revision
    attached = []
    boundaries = []
    original_attach, original_allocate = cp.attach_gradients, cp._allocate_runtime_data

    def attach(provider, values, family):
        original_attach(provider, values, family)
        attached.append(provider.checkpoint_state())

    def allocation(*, section, value):
        if sum(item["service_clock_unit"] == "world_eligible_admission" for item in attached) >= 2:
            raise MemoryError("actual late runtime allocation")
        return original_allocate(section=section, value=value)

    def refuse(_):
        raise MemoryError("allocation admission refused")

    with monkeypatch.context() as patch:
        patch.setattr(cp, "attach_gradients", attach)
        if failure == "report":
            patch.setattr(target.bank, "_report", refuse)

            def boundary(name, operation):
                def record(*args, **kwargs):
                    boundaries.append(name)
                    return operation(*args, **kwargs)

                return record

            patch.setattr(cp, "owned", boundary("owned_input", cp.owned))
            patch.setattr(cp, "clone_provider", boundary("provider_copy", cp.clone_provider))
            patch.setattr(cp, "validate_native", boundary("native_validation", cp.validate_native))
            patch.setattr(target.bank, "_factory", boundary("candidate_factory", target.bank._factory))
            create = boundary("rng_create", WorldRNGState.create)
            construct = boundary("owner_construct", OwnedWorldBackend.construct)
            patch.setattr(WorldRNGState, "create", classmethod(lambda cls, **kwargs: create(**kwargs)))
            patch.setattr(OwnedWorldBackend, "construct", classmethod(lambda cls, **kwargs: construct(**kwargs)))
            patch.setattr(OwnedWorldBackend, "prepare_restore", boundary("native_prepare", OwnedWorldBackend.prepare_restore))
        else:
            patch.setattr(cp, "_allocate_runtime_data", allocation)
        with pytest.raises(MemoryError):
            prepare(target, source.saved, CHOICES[1])
    if failure == "report":
        assert not attached and not boundaries
    else:
        assert len(attached) >= 2
        assert sum(item["service_clock_unit"] == "world_eligible_admission" for item in attached) == 2
    assert target.bank.mutation_revision == revision
    for world in IDS:
        equal(live(target.bank, world), before[world])
        equal(target.bank.snapshot_world(world_id=world)["backend"]["rng"], rng_before[world])
    equal(torch.get_rng_state(), ambient)
    equal(live(source.bank), source_before)
    convert(target, source.saved, CHOICES[1])


@pytest.mark.parametrize("failure", ("stale", "foreign", "copied", "used"))
def test_prepared_initialization_custody(compiled, failure):
    """Catches foreign, copied, stale or repeated publication of a prepared runtime."""
    source = trained_source(compiled, "count_based", "paced_fifo")
    target = destination(compiled, source)
    token = prepare(target, source.saved, CHOICES[1])
    if failure == "stale":
        target.bank.snapshot_world(world_id="A")
    elif failure == "foreign":
        target = destination(compiled, source)
    elif failure == "copied":
        token = copy(token)
    else:
        target.bank.install_restore(prepared=token)
    before = {world: live(target.bank, world) for world in IDS}
    with pytest.raises(ValueError):
        target.bank.install_restore(prepared=token)
    for world in IDS:
        equal(live(target.bank, world), before[world])


@pytest.mark.parametrize("mutation", ("baseline", "epoch", "archive", "callback"))
def test_origin_and_callback_corruption_cannot_publish(compiled, mutation):
    """Catches forged inherited totals and callback aliases corrupting a prepared origin."""
    source = trained_source(compiled, "icm", "paced_fifo")
    target = destination(compiled, source)
    if mutation == "callback":
        validate = target.validate_parent

        def corrupt(*, prepared, curiosity_state):
            validate(prepared=prepared, curiosity_state=curiosity_state)
            curiosity_state.clear()

        target.validate_parent = corrupt
        before = live(target.bank)
        with pytest.raises(ValueError):
            prepare(target, source.saved, CHOICES[1])
        equal(live(target.bank), before)
        return
    convert(target, source.saved, CHOICES[1])
    state = target.bank.checkpoint_state()
    if mutation == "baseline":
        state["initialization_origin"]["inherited_baseline"]["admitted_rows"] += 1
    elif mutation == "epoch":
        state["curiosity_epoch"] = 0
    else:
        state["initialization_origin"]["source_checkpoint"]["shared_backend"]["native"]["pending"][0]["action"] = 2
    receiver = destination(compiled, source)
    before = {world: live(receiver.bank, world) for world in IDS}
    with pytest.raises(ValueError):
        receiver.bank.prepare_restore(
            state=state,
            mode="private_initialized",
            accepted=None,
            parent_restore=receiver.parent,
            validate_parent_restore=receiver.validate_parent,
        )
    for world in IDS:
        equal(live(receiver.bank, world), before[world])


def incompatible_target(compiled, mismatch):
    selected = policy(compiled, "icm", "per_world", "paced_fifo")
    if mismatch == "family":
        selected = policy(compiled, "rnd", "per_world", "paced_fifo")
    elif mismatch in ("learning_rate", "batch", "capacity"):
        authored = selected.to_dict()["authored_parameters"]
        options = authored["bac_options"]
        key, value = {
            "learning_rate": ("learning_rate", 0.002),
            "batch": ("training_batch_size", 3),
            "capacity": ("max_pending_transitions", 6),
        }[mismatch]
        options["providers"]["icm"][key] = value
        selected = resolve_exploration_policy(
            IntrinsicStrategyConfig.model_validate(authored["drive_intrinsic"]),
            TrainingV2Config.model_validate(authored["training"]),
            BaCOptions.model_validate(options),
        )
    options = {"width": 4} if mismatch == "geometry" else {"seed": 702} if mismatch == "seed" else {}
    if mismatch == "membership":
        options.update(ids=("A", "C"), membership=("A", "C"))
    return Rig(compiled, selected, **options)


@pytest.mark.parametrize("mismatch", ("family", "learning_rate", "batch", "capacity", "geometry", "seed", "membership"))
def test_fixture_coherent_incompatible_targets(compiled, mismatch):
    """Each mismatch is a real independently valid target, not corrupt source metadata."""
    target = incompatible_target(compiled, mismatch)
    for world in target.env.world_ids:
        validate_live(target.bank, live(target.bank, world)["native"], world)
    assert target.bank.checkpoint_state()["bank_phase"] == "initial"


@pytest.mark.parametrize("mismatch", ("family", "learning_rate", "batch", "capacity", "geometry", "seed", "membership"))
def test_coherent_incompatible_target_refuses(compiled, mismatch):
    """Source validation alone cannot reject these separately valid target configurations."""
    source = Rig(compiled, policy(compiled, "icm", "shared", "paced_fifo"))
    state = source.bank.checkpoint_state()
    backend(source.bank).validate_state(state["shared_backend"]["native"])
    target = incompatible_target(compiled, mismatch)
    before = {world: live(target.bank, world) for world in target.env.world_ids}
    for world in target.env.world_ids:
        validate_live(target.bank, before[world]["native"], world)
    with pytest.raises(ValueError):
        target.bank.prepare_private_initialization(
            state=state, initialization=CHOICES[1], parent_restore=None, validate_parent_restore=None
        )
    for world in target.env.world_ids:
        equal(live(target.bank, world), before[world])
    equal(source.bank.checkpoint_state(), state)
    # A genuinely compatible current target accepts the exact same source.
    compatible = Rig(compiled, policy(compiled, "icm", "per_world", "paced_fifo"))
    token = compatible.bank.prepare_private_initialization(
        state=state, initialization=CHOICES[1], parent_restore=None, validate_parent_restore=None
    )
    compatible.bank.install_restore(prepared=token)


@pytest.mark.parametrize("fault", ("omitted_choice", "declared_profile", "foreign_parent", "stale_parent"))
def test_explicit_choice_profile_and_parent_custody(compiled, fault):
    """Catches a guessed choice, ignored profile, or unauthenticated real parent record."""
    source = trained_source(compiled, "icm", "paced_fifo")
    target = destination(compiled, source)
    state = deepcopy(source.saved)
    backend(source.bank).validate_state(state["shared_backend"]["native"])
    for world in IDS:
        validate_live(target.bank, live(target.bank, world)["native"], world)
    parent = target.parent
    if fault == "declared_profile":
        # CPU-host test of saved device provenance; native source itself stays validated/current.
        state["source_device"] = "cuda:0"
    elif fault == "foreign_parent":
        parent = destination(compiled, source).parent
    elif fault == "stale_parent":
        target.validate_parent(prepared=parent, curiosity_state=deepcopy(state))
        target.install_parent()
        reservation = target.env.prepare_episode(batch_episode=source.accepted.batch_episode + 1, release=target.release)
        target.env.validate_episode_reservation(reservation)
        target.env.reset(reservation=reservation)
    before = {world: live(target.bank, world) for world in IDS}
    with pytest.raises(TypeError if fault == "omitted_choice" else ValueError):
        if fault == "omitted_choice":
            target.bank.prepare_private_initialization(state=state, parent_restore=parent, validate_parent_restore=target.validate_parent)
        else:
            target.bank.prepare_private_initialization(
                state=state, initialization=CHOICES[1], parent_restore=parent, validate_parent_restore=target.validate_parent
            )
    for world in IDS:
        equal(live(target.bank, world), before[world])
    retry = destination(compiled, source)
    convert(retry, source.saved, CHOICES[1])


@pytest.mark.parametrize("origin", ("ordinary", "fresh_private", "clone_learned_archive_pending"))
@pytest.mark.parametrize("family", TRAINABLE)
def test_initial_and_live_private_continuation(compiled, family, origin):
    """Catches converted INITIAL/live decoder gaps, lost RNG/gradients and foreign cached epochs."""
    selected = policy(compiled, family, "per_world", "paced_fifo")
    target = Rig(compiled, selected)
    if origin != "ordinary":
        source = Rig(compiled, policy(compiled, family, "shared", "paced_fifo"))
        token = target.bank.prepare_private_initialization(
            state=source.bank.checkpoint_state(), initialization=origin, parent_restore=None, validate_parent_restore=None
        )
        target.bank.install_restore(prepared=token)
    initial = target.bank.checkpoint_state()
    if origin == "ordinary":
        assert initial["initialization_origin"] is None and initial["curiosity_epoch"] == 0
    receiving = Rig(compiled, selected)
    token = receiving.bank.prepare_restore(state=initial, mode="initial", accepted=None, parent_restore=None, validate_parent_restore=None)
    receiving.bank.install_restore(prepared=token)
    equal(receiving.bank.checkpoint_state(), initial)
    receiving.begin(0)
    receiving.step(1, (True, False))
    receiving.step(2, (True, False))
    context, stamp, _, receipts = receiving.step(3, (True, False))
    live_state = receiving.bank.checkpoint_state()
    before = {world: live(receiving.bank, world) for world in IDS}
    rng = {world: receiving.bank.snapshot_world(world_id=world)["backend"]["rng"] for world in IDS}
    corrupt = deepcopy(live_state)
    corrupt["worlds"][0]["phase_cache"]["service"]["receipt"]["event_ids"][0]["curiosity_epoch"] += 1
    with pytest.raises(ValueError):
        receiving.bank.prepare_restore(
            state=corrupt, mode="live_episode", accepted=receiving.accepted, parent_restore=None, validate_parent_restore=None
        )
    token = receiving.bank.prepare_restore(
        state=live_state, mode="live_episode", accepted=receiving.accepted, parent_restore=None, validate_parent_restore=None
    )
    receiving.bank.install_restore(prepared=token)
    for world in IDS:
        equal(live(receiving.bank, world)["native"], before[world]["native"])
        equal(live(receiving.bank, world)["gradients"], before[world]["gradients"])
        equal(receiving.bank.snapshot_world(world_id=world)["backend"]["rng"], rng[world])
    assert receiving.bank.admit_and_service(context=context, stamp=stamp, accepted=receiving.accepted) == receipts
    receiving.step(4, (True, False))
    assert receiving.bank.checkpoint_state()["curiosity_epoch"] == (0 if origin == "ordinary" else 1)
    counters, pending = native_ledger(live(receiving.bank)["native"], family)
    assert counters["optimizer_updates"] == 2 and len(pending) == 0


@pytest.mark.parametrize("choice", CHOICES)
def test_private_rng_is_owned_and_starts_at_same_id_factory_continuation(compiled, choice):
    """Catches shared RNG ownership even if snapshot tensors themselves are copied."""
    source = trained_source(compiled, "rnd", "paced_fifo")
    target = destination(compiled, source)
    independent = Rig(compiled, target.bank.policy)
    convert(target, source.saved, choice)
    b_before = target.bank.snapshot_world(world_id="B")["backend"]["rng"]
    ambient = torch.get_rng_state().clone()

    def draw(provider, sources):
        return torch.rand(13)

    first = target.bank._owners["A"].call(draw)
    equal(first, independent.bank._owners["A"].call(draw))
    equal(target.bank.snapshot_world(world_id="A")["backend"]["rng"], independent.bank.snapshot_world(world_id="A")["backend"]["rng"])
    equal(target.bank.snapshot_world(world_id="B")["backend"]["rng"], b_before)
    equal(torch.get_rng_state(), ambient)
    assert not torch.equal(first, target.bank._owners["A"].call(draw))
    equal(target.bank.snapshot_world(world_id="B")["backend"]["rng"], b_before)


def offset_source(compiled, sign):
    source = Rig(compiled, policy(compiled, "rnd", "shared", "paced_fifo"))
    source.begin(0)
    source.step(1)
    source.step(2)
    provider = backend(source.bank)
    earlier = deepcopy(provider.optimizer.state_dict())
    source.step(3)
    source.step(4)
    source.step(5, (True, False))
    if sign == "positive":
        # Genuine manual Adam update using the last real backward's residual gradients.
        provider.optimizer.step()
    else:
        # Deliberate public Adam rewind: real earlier moments/steps, current learned model.
        provider.optimizer.load_state_dict(earlier)
    source.close()
    source.saved = source.bank.checkpoint_state()
    native = source.saved["shared_backend"]["native"]
    provider.validate_state(native)
    steps = {int(item["step"].item()) for item in provider.optimizer.state.values()}
    assert len(steps) == 1
    offset = next(iter(steps)) - native["predictor_service"]["optimizer_updates"]
    assert offset == (1 if sign == "positive" else -2)
    assert native["predictor_service"]["optimizer_step_offset"] == offset
    return source


def dropped_source(compiled, family):
    ids = ("A", "B", "C", "D", "E")
    source = Rig(compiled, policy(compiled, family, "shared", "paced_fifo"), ids, membership=ids)
    source.begin(0)
    for tick in range(1, 4):
        source.step(tick, (True,) * 5)
    source.close()
    source.saved = source.bank.checkpoint_state()
    native = source.saved["shared_backend"]["native"]
    backend(source.bank).validate_state(native)
    counters, tail = native_ledger(native, family)
    assert counters["admitted_rows"] == 15 and counters["optimizer_updates"] >= 2
    assert counters["dropped_rows"] > 0 and len(tail) >= 2
    return source


@pytest.mark.parametrize("sign", ("positive", "negative"))
def test_fixture_real_signed_rnd_offset(compiled, sign):
    """Prerequisite: signed-offset sources are accepted by the unchanged native validator."""
    offset_source(compiled, sign)


@pytest.mark.parametrize("family", ("rnd", "icm"))
def test_fixture_genuine_drops_and_multirow_tail(compiled, family):
    """Prerequisite: five real shared rows per tick genuinely overflow selected capacity."""
    dropped_source(compiled, family)


@pytest.mark.parametrize("sign", ("positive", "negative"))
def test_signed_rnd_offset_survives_clone_and_next_real_update(compiled, sign):
    """Catches reset/coercion of a valid signed offset while inherited Adam is retained."""
    source = offset_source(compiled, sign)
    target = destination(compiled, source)
    before = live(source.bank)
    convert(target, source.saved, CHOICES[1])
    native = live(target.bank)["native"]
    equal(native["optimizer"], before["native"]["optimizer"])
    expected = 1 if sign == "positive" else -2
    assert native["predictor_service"]["optimizer_step_offset"] == expected
    assert_baseline(target.bank, source.saved, CHOICES[1], "A", 0, 0)
    state = target.bank.checkpoint_state()
    restored = destination(compiled, source)
    token = restored.bank.prepare_restore(
        state=state,
        mode="private_initialized",
        accepted=None,
        parent_restore=restored.parent,
        validate_parent_restore=restored.validate_parent,
    )
    restored.bank.install_restore(prepared=token)
    restored.install_parent()
    equal(live(restored.bank)["native"], live(target.bank)["native"])
    equal(live(restored.bank)["gradients"], live(target.bank)["gradients"])
    target = restored
    target.begin(1)
    target.step(51, (True, False))
    target.step(52, (True, False))
    actual = live(target.bank)["native"]
    validate_live(target.bank, actual)
    assert actual["predictor_service"]["optimizer_step_offset"] == expected
    assert_baseline(target.bank, source.saved, CHOICES[1], "A", 2, 1)
    for key, value in actual["optimizer"]["state"].items():
        assert value["step"].item() == native["optimizer"]["state"][key]["step"].item() + 1
    assert_source(source, before, source.saved)


@pytest.mark.parametrize("family", ("rnd", "icm"))
@pytest.mark.parametrize("choice", CHOICES)
def test_nonzero_drop_baseline_and_multirow_archive_exclusion(compiled, family, choice):
    """Catches invented drop work, dropped inherited totals, and archived rows in a trained batch."""
    source = dropped_source(compiled, family)
    ids = source.env.world_ids
    target = Rig(compiled, policy(compiled, family, "per_world", "paced_fifo"), ids, membership=ids)
    target.prepare_parent(source)
    before = live(source.bank)
    convert(target, source.saved, choice)
    assert_baseline(target.bank, source.saved, choice, "A", 0, 0)
    b = live(target.bank, "B")
    trained, remove_hook = observe_training(target.bank, family)
    target.begin(1)
    first, _, _, receipts = target.step(71, (True, False, False, False, False))
    assert receipts[0].clock == ServiceClock("world_eligible_admission", 1)
    second, _, _, receipts = target.step(72, (True, False, False, False, False))
    remove_hook()
    equal(trained[0], torch.cat((first.predecessor[:1], second.predecessor[:1])))
    assert receipts[0].clock == ServiceClock("world_eligible_admission", 2)
    assert_baseline(target.bank, source.saved, choice, "A", 2, 1)
    equal(live(target.bank, "B"), b)
    equal(target.bank.checkpoint_state()["initialization_origin"]["source_checkpoint"], source.saved)
    assert_source(source, before, source.saved)


@pytest.mark.parametrize("family", FAMILIES)
def test_fixture_actual_private_callback_witnesses(compiled, family):
    """Reject copied-provider evidence: stable installed addresses and real service hooks."""
    rig = Rig(compiled, policy(compiled, family, "per_world", "paced_fifo"))
    before = live(rig.bank)
    equal(live(rig.bank), before)
    other = live(rig.bank, "B")
    assert before["provider_id"] != other["provider_id"]
    assert set(before["storage_ids"]).isdisjoint(other["storage_ids"])
    rng = rig.bank.snapshot_world(world_id="B")["backend"]["rng"]
    if family in TRAINABLE:
        assert before["storage_ids"]
        batches, remove_hook = observe_training(rig.bank, family)
    rig.begin(0)
    first, _, _, _ = rig.step(1, (True, False))
    second, _, _, _ = rig.step(2, (True, False))
    if family in TRAINABLE:
        remove_hook()
        equal(batches[0], torch.cat((first.predecessor[:1], second.predecessor[:1])))
    after = live(rig.bank)
    assert after["provider_id"] == before["provider_id"]
    equal(live(rig.bank), after)
    equal(live(rig.bank, "B"), other)
    equal(rig.bank.snapshot_world(world_id="B")["backend"]["rng"], rng)
    if family in TRAINABLE:
        counter, tail = native_ledger(after["native"], family)
        assert counter["optimizer_updates"] == 1 and len(tail) == 0
        assert tuple(row[:2] for row in before["refs"]) == tuple(row[:2] for row in after["refs"][: len(before["refs"])])
        gradients = [value for group in after["gradients"].values() for value in group.values()]
        assert any(value is not None and bool(value.abs().sum() > 0) for value in gradients)
        set_gradients(rig.bank)
        sentinel = live(rig.bank)
        equal(live(rig.bank), sentinel)
        gradients = [value for group in sentinel["gradients"].values() for value in group.values()]
        assert any(value is None for value in gradients)
        assert any(value is not None and not bool(value.any()) for value in gradients)
        assert any(value is not None and bool(value.any()) for value in gradients)
        validate_live(rig.bank, sentinel["native"])
        equal(live(rig.bank), sentinel)
    elif family == "count_based":
        assert not before["native"]["counts"] and len(after["native"]["counts"]) == 2
    else:
        equal(after["native"], before["native"])
    # A third actual operation proves witness calls did not quarantine the owner.
    rig.step(3, (True, False))
    assert rig.bank.snapshot_world(world_id="A")["cursor"]["cumulative_service_position"] == 3


@pytest.mark.parametrize("mutation", ("choice", "archive_counts", "target_counts"))
def test_unstarted_count_origin_requires_selected_template(compiled, mutation):
    """Reject valid native Count state that contradicts its unstarted origin claim."""
    source = trained_source(compiled, "count_based", "paced_fifo")
    source_before = live(source.bank)
    target = destination(compiled, source)
    convert(target, source.saved, CHOICES[1])
    original = target.bank.checkpoint_state()
    assert original["bank_phase"] == "private_initialized"
    assert original["initialization_origin"]["inherited_baseline"] is None
    assert all(record["cursor"]["cumulative_service_position"] == 0 for record in original["worlds"])
    changed = deepcopy(original)
    if mutation == "choice":
        changed["initialization_origin"]["initialization"] = CHOICES[0]
        assert changed["worlds"][0]["backend"]["backend"]["counts"]
    else:
        if mutation == "archive_counts":
            native = changed["initialization_origin"]["source_checkpoint"]["shared_backend"]["native"]
            validator = Rig(compiled, source.bank.policy)
        else:
            native = changed["worlds"][0]["backend"]["backend"]
            validator = Rig(compiled, target.bank.policy)
        native["counts"][next(iter(native["counts"]))] += 1
        # Actual Count's complete loader accepts this independently valid learned state.
        on_backend(validator.bank, lambda provider: provider.load_state(deepcopy(native)))
        equal(live(validator.bank)["native"], native)
    receiver = destination(compiled, source)
    before = {world: live(receiver.bank, world) for world in IDS}
    rng = {world: receiver.bank.snapshot_world(world_id=world)["backend"]["rng"] for world in IDS}
    revision = receiver.bank.mutation_revision
    ambient = torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        receiver.bank.prepare_restore(
            state=changed,
            mode="private_initialized",
            accepted=None,
            parent_restore=receiver.parent,
            validate_parent_restore=receiver.validate_parent,
        )
    assert receiver.bank.mutation_revision == revision
    for world in IDS:
        equal(live(receiver.bank, world), before[world])
        equal(receiver.bank.snapshot_world(world_id=world)["backend"]["rng"], rng[world])
    equal(torch.get_rng_state(), ambient)
    assert_source(source, source_before, source.saved)
    token = receiver.bank.prepare_restore(
        state=original,
        mode="private_initialized",
        accepted=None,
        parent_restore=receiver.parent,
        validate_parent_restore=receiver.validate_parent,
    )
    receiver.bank.install_restore(prepared=token)
    receiver.install_parent()
    equal(learned(live(receiver.bank)["native"], "count_based"), learned(source_before["native"], "count_based"))
    receiver.begin(source.accepted.batch_episode + 1)
    receiver.step(401, (True, False))
    assert receiver.bank.snapshot_world(world_id="A")["cursor"]["cumulative_service_position"] == 1
    assert_source(source, source_before, source.saved)
