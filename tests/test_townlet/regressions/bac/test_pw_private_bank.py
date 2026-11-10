"""PW05 real private-bank controls; local other-role owners are NOT parent integration.

All helper code lives here. No fixture-source imports, introspection or copied
provider algorithms. The independent prerequisite must pass before missing-bank
failures count as RED. Actual ENV acceptance and actual issuer capabilities are
required even though the non-curiosity role owners below are cooperative doubles.
"""

from __future__ import annotations

import importlib
import importlib.util
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.config.world_roster import WorldRosterDeclaration
from townlet.environment.vectorized_env import VectorizedHamletEnv, WorldReceiptIssuer
from townlet.exploration.provider_factory import make_backend, make_policy_selector
from townlet.exploration.world_curiosity_state import OwnedWorldBackend, WorldCuriosityDescriptor, WorldRNGState
from townlet.training.episode import EpisodeCompletion, LaneOutcome, freeze_lane_outcome
from townlet.universe.compiler import UniverseCompiler

FAMILIES = ("none", "count_based", "rnd", "adaptive_rnd", "icm")
TRAINABLE = ("rnd", "adaptive_rnd", "icm")
WORLD_IDS = ("world0", "world1")
BANK_MODULE = "townlet.exploration.scoped_curiosity"


def _bank_type() -> type:
    # Explicit intended RED, after fixture construction, not an import error.
    assert importlib.util.find_spec(BANK_MODULE) is not None, "PW05 missing CuriosityBank implementation"
    module = importlib.import_module(BANK_MODULE)
    assert hasattr(module, "CuriosityBank"), "PW05 missing CuriosityBank public ABI"
    return module.CuriosityBank


def _equal(left: Any, right: Any) -> None:
    """Exact values including gradients/RNG/native trees, never approximate loss."""
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert (left.shape, left.dtype, left.device) == (right.shape, right.dtype, right.device)
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype and np.array_equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _equal(a, b)
    else:
        assert left == right


def _tensors(value: Any) -> list[torch.Tensor]:
    if isinstance(value, torch.Tensor):
        return [value]
    if isinstance(value, dict):
        return [tensor for item in value.values() for tensor in _tensors(item)]
    if isinstance(value, (list, tuple)):
        return [tensor for item in value for tensor in _tensors(item)]
    return []


def _storage(tensor: torch.Tensor) -> int:
    return tensor.untyped_storage().data_ptr()


def _descriptor(policy: ResolvedExplorationPolicy, ids: tuple[str, ...], width: int) -> WorldCuriosityDescriptor:
    return WorldCuriosityDescriptor.from_policy(policy, world_ids=ids, observation_dim=width, action_dim=2, training_seed=421)


def _owned(policy: ResolvedExplorationPolicy, descriptor: WorldCuriosityDescriptor, world_id: str) -> OwnedWorldBackend:
    rng = WorldRNGState.create(descriptor=descriptor, world_id=world_id, cuda_devices=())
    return OwnedWorldBackend.construct(
        rng=rng,
        factory=lambda candidate: make_backend(
            policy,
            world_id=world_id,
            obs_dim=descriptor.observation_dim,
            action_dim=descriptor.action_dim,
            device="cpu",
            rng=candidate,
            descriptor=descriptor,
        ),
    )


def _context(tick: int, active: tuple[bool, ...], width: int, other: float) -> IntrinsicTransitionContext:
    rows = len(active)
    predecessor = torch.arange(rows * width, dtype=torch.float32).reshape(rows, width) / 17 + tick / 11
    if width:
        predecessor[0] += other
    return IntrinsicTransitionContext(
        predecessor=predecessor,
        actions=torch.tensor([tick % 2] * rows, dtype=torch.int64),
        successor=predecessor + 0.125,
        active_on_entry=torch.tensor(active, dtype=torch.bool),
        vector_tick=tick,
    )


def _step(bank: Any, accepted: Any, context: IntrinsicTransitionContext) -> tuple[Any, Any, Any]:
    stamp = bank.prepare_step_stamp(
        accepted=accepted,
        world_ids=accepted.world_ids,
        active_on_entry=context.active_on_entry,
        vector_tick=context.vector_tick,
    )
    reward = bank.reward(context=context, stamp=stamp, accepted=accepted, update_stats=True)
    receipts = bank.admit_and_service(context=context, stamp=stamp, accepted=accepted)
    return stamp, reward, receipts


def _native(snapshot: dict[str, Any]) -> dict[str, Any]:
    return snapshot["backend"]["backend"] if snapshot["scope"] == "per_world" else snapshot["backend"]


def _rnd_native(state: dict[str, Any], family: str) -> dict[str, Any]:
    return state["rnd_state"] if family == "adaptive_rnd" else state


def _learned(state: dict[str, Any], family: str) -> list[torch.Tensor]:
    if family == "icm":
        return _tensors({key: state[key] for key in ("encoder", "inverse_model", "forward_model")})
    return _tensors(_rnd_native(state, family)["predictor_network"])


def _optimizer(state: dict[str, Any], family: str) -> dict[str, Any]:
    return _rnd_native(state, family)["optimizer"]


def _updates(state: dict[str, Any], family: str) -> int:
    if family == "icm":
        return state["counters"]["optimizer_updates"]
    return _rnd_native(state, family)["predictor_service"]["optimizer_updates"]


def _ownership(backend: Any, family: str) -> dict[str, Any]:
    """Read actual published provider objects; return scalars/data, never live objects."""
    result: dict[str, Any] = {"backend": id(backend)}
    if family not in TRAINABLE:
        result["native"] = backend.checkpoint_state()
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
        result["rms"] = id(actual.reward_rms)
    if family == "adaptive_rnd":
        result["history"] = id(backend.survival_history)
    return result


def _inspect(bank: Any, world_id: str, family: str) -> dict[str, Any]:
    # Owned callback is required: accessing live model objects outside custody is
    # deliberately avoided. _owners is the bank's test-visible private ID registry.
    return bank._owners[world_id].call(lambda backend, sources: _ownership(backend, family))


def _outcomes(accepted: Any, ids: tuple[str, ...], steps: int) -> tuple[LaneOutcome, ...]:
    return tuple(
        LaneOutcome(
            outcome=EpisodeCompletion(
                agent_idx=accepted.world_ids.index(world_id),
                reason="cap",
                survival_time=steps,
                final_observation=torch.ones(3),
                final_meters=torch.ones(2),
            ),
            batch_episode=accepted.batch_episode,
            planned_horizon=20,
            reward_total=1.0,
            reward_extrinsic=0.5,
            reward_intrinsic=0.5,
            reward_shaping=0.0,
            policy_entropy=0.2,
            world_id=world_id,
            world_episode_seq=accepted.world_episode_seqs[accepted.world_ids.index(world_id)],
        )
        for world_id in ids
    )


def _completion(bank: Any, accepted: Any, ids: tuple[str, ...], steps: int) -> Any:
    outcomes = _outcomes(accepted, ids, steps)
    return bank.prepare_completion(
        accepted=accepted,
        boundary_key=accepted.batch_episode,
        completion_content=_content(outcomes),
        outcomes=outcomes,
        participated_world_ids=ids,
    )


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
            if family in TRAINABLE:
                for field in ("models", "parameters", "storage", "gradient_storage", "moment_storage"):
                    assert set(left[field]).isdisjoint(right[field]), field
                assert left["optimizer"] != right["optimizer"]
                assert set(left["optimizer_parameters"]) <= set(left["parameters"])
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
        assert "optimizer" not in _native(before)


@pytest.mark.parametrize("family", FAMILIES)
def test_world1_updates_match_when_world0_activity_changes(harness_factory: Any, family: str) -> None:
    first, second = harness_factory(family), harness_factory(family)
    before = _native(first.bank.snapshot_world(world_id="world1"))
    for tick in range(1, 10):
        _, left, _ = _step(first.bank, first.accepted, _context(tick, (True, True), 3, 100.0))
        _, right, _ = _step(second.bank, second.accepted, _context(tick, (False, True), 3, -100.0))
        _equal(left.raw[1], right.raw[1])
        _equal(left.scales[1], right.scales[1])
        _equal(first.bank.snapshot_world(world_id="world1"), second.bank.snapshot_world(world_id="world1"))
        if family in TRAINABLE:
            _equal(_inspect(first.bank, "world1", family)["gradients"], _inspect(second.bank, "world1", family)["gradients"])
    after = _native(first.bank.snapshot_world(world_id="world1"))
    if family in TRAINABLE:
        assert _updates(after, family) >= 2
        assert any(not torch.equal(a, b) for a, b in zip(_learned(before, family), _learned(after, family), strict=True))
        moments = _optimizer(after, family)["state"]
        assert moments and any(bool(value["exp_avg"].ne(0).any()) for value in moments.values())
        assert all(float(value["step"]) >= 2 for value in moments.values())


def test_shared_mode_retains_coupled_control(harness_factory: Any) -> None:
    first, second = harness_factory("count_based", scope="shared"), harness_factory("count_based", scope="shared")

    # Same successor bin for both worlds: active world0 must increment the same
    # actual shared Count dictionary before world1 is evaluated.
    def context(active: tuple[bool, bool]) -> IntrinsicTransitionContext:
        return IntrinsicTransitionContext(
            predecessor=torch.zeros(2, 3),
            actions=torch.zeros(2, dtype=torch.int64),
            successor=torch.ones(2, 3),
            active_on_entry=torch.tensor(active),
            vector_tick=1,
        )

    _, both, _ = _step(first.bank, first.accepted, context((True, True)))
    _, one, _ = _step(second.bank, second.accepted, context((False, True)))
    assert both.raw[1] < one.raw[1]
    assert both.raw[1] > 0
    assert both.scope == one.scope == "shared"


@pytest.mark.parametrize("family", FAMILIES)
def test_phase_retry_inactive_and_terminal_once(harness_factory: Any, family: str) -> None:
    harness = harness_factory(family)
    bank, accepted = harness.bank, harness.accepted
    context = _context(1, (True, False), 3, 0.0)
    stamp = bank.prepare_step_stamp(accepted=accepted, world_ids=WORLD_IDS, active_on_entry=context.active_on_entry, vector_tick=1)
    before = bank.snapshot_world(world_id="world0")
    with pytest.raises(ValueError):
        bank.admit_and_service(context=context, stamp=stamp, accepted=accepted)
    _equal(before, bank.snapshot_world(world_id="world0"))
    reward = bank.reward(context=context, stamp=stamp, accepted=accepted, update_stats=True)
    after_reward = bank.snapshot_world(world_id="world0")
    again = bank.reward(context=context, stamp=stamp, accepted=accepted, update_stats=True)
    _equal(reward.raw, again.raw)
    _equal(after_reward, bank.snapshot_world(world_id="world0"))
    changed = IntrinsicTransitionContext(
        predecessor=context.predecessor,
        actions=context.actions,
        successor=context.successor + 1,
        active_on_entry=context.active_on_entry,
        vector_tick=1,
    )
    with pytest.raises(ValueError):
        bank.reward(context=changed, stamp=stamp, accepted=accepted, update_stats=True)
    _equal(after_reward, bank.snapshot_world(world_id="world0"))
    bank.admit_and_service(context=context, stamp=stamp, accepted=accepted)
    settled = bank.snapshot_world(world_id="world0")
    bank.admit_and_service(context=context, stamp=stamp, accepted=accepted)
    _equal(settled, bank.snapshot_world(world_id="world0"))
    assert settled["cursor"]["eligible_seq"] == 1
    assert settled["cursor"]["cumulative_service_position"] == 1
    idle_before = bank.snapshot_world(world_id="world0")
    _, idle_reward, _ = _step(bank, accepted, _context(2, (False, False), 3, 0.0))
    idle_after = bank.snapshot_world(world_id="world0")
    _equal(idle_before["backend"], idle_after["backend"])
    _equal(idle_before["cursor"], idle_after["cursor"])
    assert torch.count_nonzero(idle_reward.raw) == 0
    assert torch.count_nonzero(idle_reward.scales) == 0
    assert reward.raw.shape == reward.scales.shape == (2,)
    assert torch.isfinite(reward.raw).all() and torch.isfinite(reward.scales).all()


@pytest.mark.parametrize("corruption", ("action", "width", "dtype", "tick", "eligibility", "token"))
def test_complete_batch_preflight_precedes_any_world_effect(harness_factory: Any, corruption: str) -> None:
    h = harness_factory("icm")
    good = _context(1, (True, True), 3, 0.0)
    stamp = h.bank.prepare_step_stamp(accepted=h.accepted, world_ids=WORLD_IDS, active_on_entry=good.active_on_entry, vector_tick=1)
    predecessor, actions, successor, active = good.predecessor, good.actions, good.successor, good.active_on_entry
    tick, accepted = 1, h.accepted
    if corruption == "action":
        actions[1] = 2
    elif corruption == "width":
        predecessor, successor = predecessor[:, :2], successor[:, :2]
    elif corruption == "dtype":
        predecessor, successor = predecessor.double(), successor.double()
    elif corruption == "tick":
        tick = 2
    elif corruption == "eligibility":
        active[1] = False
    else:
        accepted = replace(accepted)
    context = IntrinsicTransitionContext(
        predecessor=predecessor, actions=actions, successor=successor, active_on_entry=active, vector_tick=tick
    )
    before = tuple(h.bank.snapshot_world(world_id=world) for world in WORLD_IDS)
    with pytest.raises(ValueError):
        h.bank.reward(context=context, stamp=stamp, accepted=accepted, update_stats=True)
    for world, state in zip(WORLD_IDS, before, strict=True):
        _equal(state, h.bank.snapshot_world(world_id=world))


def test_reserved_tick_order_and_expired_events_refuse(harness_factory: Any) -> None:
    h = harness_factory("rnd")
    old_context = _context(1, (True, True), 3, 0.0)
    old_stamp, _, _ = _step(h.bank, h.accepted, old_context)
    _step(h.bank, h.accepted, _context(2, (True, True), 3, 0.0))
    before = h.bank.snapshot_world(world_id="world1")
    with pytest.raises(ValueError):
        h.bank.reward(context=old_context, stamp=old_stamp, accepted=h.accepted, update_stats=True)
    _equal(before, h.bank.snapshot_world(world_id="world1"))
    with pytest.raises(ValueError):
        h.bank.prepare_step_stamp(
            accepted=h.accepted, world_ids=tuple(reversed(WORLD_IDS)), active_on_entry=torch.ones(2, dtype=torch.bool), vector_tick=3
        )
    _equal(before, h.bank.snapshot_world(world_id="world1"))


@pytest.mark.parametrize("family", TRAINABLE)
def test_all_inactive_shared_call_does_not_service_pending_tail(harness_factory: Any, family: str) -> None:
    h = harness_factory(family, scope="shared")
    _step(h.bank, h.accepted, _context(1, (True, False), 3, 0.0))
    before = h.bank.snapshot_world(world_id="world1")
    native = _native(before)
    pending = native["pending"] if family == "icm" else _rnd_native(native, family)["predictor_service"]["pending_observations"]
    assert len(pending) == 1
    _, reward, receipts = _step(h.bank, h.accepted, _context(100, (False, False), 3, 100.0))
    assert receipts == ()
    assert not reward.raw.any()
    _equal(before["backend"], h.bank.snapshot_world(world_id="world1")["backend"])


def test_completion_preserves_nonempty_gradients_and_tail(harness_factory: Any) -> None:
    h = harness_factory("adaptive_rnd")
    for tick in range(1, 8):
        _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
    before = {world: _inspect(h.bank, world, "adaptive_rnd") for world in WORLD_IDS}
    for value in before.values():
        assert any(gradient is not None and bool(gradient.ne(0).any()) for gradient in value["gradients"])
        assert value["native"]["rnd_state"]["predictor_service"]["pending_observations"]
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
    for world in WORLD_IDS:
        after = _inspect(h.bank, world, "adaptive_rnd")
        for field in (
            "models",
            "parameters",
            "storage",
            "optimizer",
            "optimizer_parameters",
            "gradient_storage",
            "gradients",
            "queue",
            "rms",
        ):
            _equal(before[world][field], after[field])
        _equal(before[world]["native"]["rnd_state"], after["native"]["rnd_state"])
        assert after["native"]["survival_history"] == [7]


def test_completion_malformed_last_outcome_and_wrong_destination_refuse(harness_factory: Any) -> None:
    h, foreign = harness_factory("adaptive_rnd"), harness_factory("adaptive_rnd")
    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
    good = _outcomes(h.accepted, WORLD_IDS, 1)
    malformed = (good[0], replace(good[1], world_episode_seq=2))
    before = tuple(h.bank.snapshot_world(world_id=world) for world in WORLD_IDS)
    with pytest.raises(ValueError):
        h.bank.prepare_completion(
            accepted=h.accepted,
            boundary_key=h.accepted.batch_episode,
            completion_content=_content(malformed),
            outcomes=malformed,
            participated_world_ids=WORLD_IDS,
        )
    for world, state in zip(WORLD_IDS, before, strict=True):
        _equal(state, h.bank.snapshot_world(world_id=world))
    prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
    with pytest.raises(ValueError):
        foreign.bank.commit_completion(prepared=prepared)
    h.bank.commit_completion(prepared=prepared)


def test_nonparticipant_retirement_does_not_invent_adaptive_history(harness_factory: Any) -> None:
    h = harness_factory("adaptive_rnd")
    _step(h.bank, h.accepted, _context(1, (False, True), 3, 0.0))
    receipt = h.bank.commit_completion(prepared=_completion(h.bank, h.accepted, ("world1",), 1))
    assert receipt.payload["dispositions"] == (("world0", "retired_nonparticipating"), ("world1", "completed"))
    assert _native(h.bank.snapshot_world(world_id="world0"))["survival_history"] == []
    assert _native(h.bank.snapshot_world(world_id="world1"))["survival_history"] == [1]


def test_initial_snapshot_has_no_fabricated_event(harness_factory: Any) -> None:
    h = harness_factory("none", begin=False)
    state = h.bank.snapshot_world(world_id="world0")
    assert state["accepted_identity"] is None
    assert state["phase_cache"] == {}
    assert state["pending_step"] is None
    assert state["cursor"] == {
        "accepted_episode_seq": 0,
        "eligible_seq": 0,
        "cumulative_service_position": 0,
        "participated": False,
        "disposition": None,
    }


def test_empty_evidence_and_conservative_quarantine(harness_factory: Any) -> None:
    h = harness_factory("adaptive_rnd")
    before = tuple(h.bank.snapshot_world(world_id=world) for world in WORLD_IDS)
    for _ in range(2):
        receipt = h.bank.prepare_empty_episode_evidence(accepted=h.accepted)
        WorldReceiptIssuer.validate(receipt, "empty_episode", h.bank)
        assert set(receipt.payload) == {"accepted", "participated_world_ids", "events"}
        assert receipt.payload["accepted"] is h.accepted
        assert receipt.payload["participated_world_ids"] == receipt.payload["events"] == ()
        for world, state in zip(WORLD_IDS, before, strict=True):
            _equal(state, h.bank.snapshot_world(world_id=world))
    abandonment = h.env.abandon_episode(accepted=h.accepted, reason="empty_participation")
    assert abandonment.kind == "abandonment"
    h.bank.quarantine_episode(accepted=h.accepted, reason="empty_participation")
    h.bank.quarantine_episode(accepted=h.accepted, reason="empty_participation")
    with pytest.raises(ValueError):
        h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
    with pytest.raises((ValueError, RuntimeError)):
        h.bank.snapshot_world(world_id="world0")
    with pytest.raises((ValueError, RuntimeError)):
        _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))


def test_quarantine_prevents_pending_completion_publication(harness_factory: Any) -> None:
    h = harness_factory("adaptive_rnd")
    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
    prepared = _completion(h.bank, h.accepted, WORLD_IDS, 1)
    h.bank.quarantine_episode(accepted=h.accepted, reason="runtime_failure")
    with pytest.raises((ValueError, RuntimeError)):
        h.bank.commit_completion(prepared=prepared)


def test_allocation_report_can_refuse_before_constructor(harness_factory: Any, monkeypatch: Any) -> None:
    cls = _bank_type()
    h = harness_factory("rnd", begin=False)
    reports: list[Any] = []

    def refuse(report: Any) -> None:
        reports.append(report)
        raise ValueError("allocation admission refused")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("provider allocated before allocation admission")

    monkeypatch.setattr(importlib.import_module(BANK_MODULE), "make_backend", forbidden)
    with pytest.raises(ValueError, match="allocation admission refused"):
        cls(
            policy=h.policy,
            descriptor=h.descriptor,
            device="cpu",
            validate_accepted_episode=h.env.validate_accepted_episode,
            issuer_factory=lambda owner: WorldReceiptIssuer(owner=owner),
            report_allocation=refuse,
        )
    assert len(reports) == 1
    report = reports[0]
    assert report.operation == "construct" and report.scope == "per_world"
    assert report.world_count == report.instance_count == 2
    assert report.known_tensor_bytes > 0
    assert report.unknown_components and report.assumptions


def test_completion_allocation_refusal_leaves_provider_untouched(harness_factory: Any) -> None:
    reports: list[Any] = []

    def admission(report: Any) -> None:
        reports.append(report)
        if report.operation == "complete":
            raise ValueError("completion allocation refused")

    h = harness_factory("adaptive_rnd", report_allocation=admission)
    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
    before = tuple(h.bank.snapshot_world(world_id=world) for world in WORLD_IDS)
    with pytest.raises(ValueError, match="completion allocation refused"):
        _completion(h.bank, h.accepted, WORLD_IDS, 1)
    assert reports[-1].operation == "complete"
    for world, state in zip(WORLD_IDS, before, strict=True):
        _equal(state, h.bank.snapshot_world(world_id=world))


def _content(outcomes: tuple[LaneOutcome, ...]) -> tuple[tuple[str, str], ...]:
    frozen = tuple(freeze_lane_outcome(outcome) for outcome in outcomes)
    return tuple((item.payload.hex(), item.fingerprint) for item in frozen)


class _LocalRole:
    """Cooperative interface fixture, not a production parent/population owner."""

    def __init__(self) -> None:
        self.issuer = WorldReceiptIssuer(owner=self)
        self.accepted: Any = None
        self.participants: tuple[str, ...] = ()

    def receipt(self, kind: str, **payload: Any) -> Any:
        return self.issuer.issue(kind=kind, payload=payload)

    def activation(self, accepted: Any) -> Any:
        self.accepted, self.participants = accepted, ()
        return self.receipt("activation", accepted=accepted)

    def prepare_empty_episode_evidence(self, *, accepted: Any) -> Any:
        assert accepted is self.accepted and self.participants == ()
        return self.receipt("empty_episode", accepted=accepted, participated_world_ids=(), events=())


@pytest.fixture(scope="module")
def compiled() -> Any:
    result = UniverseCompiler().compile(Path("/workspace/hamlet/configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)
    assert result.to_dict()["compiled_schema_version"] == "1.42"
    assert isinstance(result.effective_run.exploration, ResolvedExplorationPolicy)
    return result


def _policy(compiled: Any, family: str, scope: str) -> ResolvedExplorationPolicy:
    level = compiled.get_level("L0_test")
    drive = IntrinsicStrategyConfig.model_validate(dict(level.drive.intrinsic.model_dump(), strategy=family))
    training_data = deepcopy(level.training.model_dump())
    training_data["replay_buffer"]["batch_size"] = 2
    training_data["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
    training_data["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.1)
    training_data["training_loop"]["max_steps_per_episode"] = 20
    training_data["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    training = TrainingV2Config.model_validate(training_data)
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
            "provider_parameter_source": "training",
            "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
            "providers": {
                "count_based": {"quantization_width": 0.125, "max_entries": 16},
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
    return resolve_exploration_policy(drive, training, options)


def _env(compiled: Any, ids: tuple[str, ...]) -> Any:
    return VectorizedHamletEnv(
        universe=compiled,
        level_name="L0_test",
        num_agents=len(ids),
        device="cpu",
        world_roster=WorldRosterDeclaration.from_dict({"schema": "world-roster-v1", "world_ids": list(ids)}),
        training_seed=421,
        lane_world_ids=ids,
    )


def _bind(env: Any, curiosity: Any, population: Any, boundary: Any) -> Any:
    roles = {role: boundary for role in ("curriculum", "exploration", "network", "optimizer", "scheduler", "replay", "selection")}
    roles.update(curiosity=curiosity, population=population)
    return env.bind_boundary_authority(owner=boundary, role_owners=roles)


class _Harness:
    def __init__(self, compiled: Any, family: str, scope: str, begin: bool, report: Any, ids: tuple[str, ...], width: int):
        self.env = _env(compiled, ids)
        self.policy = _policy(compiled, family, scope)
        self.descriptor = _descriptor(self.policy, ids, width)
        self.reports: list[Any] = []
        self.bank = _bank_type()(
            policy=self.policy,
            descriptor=self.descriptor,
            device="cpu",
            validate_accepted_episode=self.env.validate_accepted_episode,
            issuer_factory=lambda owner: WorldReceiptIssuer(owner=owner),
            report_allocation=self.reports.append if report is None else report,
        )
        self.population, self.boundary = _LocalRole(), _LocalRole()
        self.authority = _bind(self.env, self.bank, self.population, self.boundary)
        self.release = self.env.install_boundary_release(self.authority.bootstrap(first_batch_episode=1))
        self.accepted: Any = None
        if begin:
            self.begin(1)

    def begin(self, batch: int) -> None:
        reservation = self.env.prepare_episode(batch_episode=batch, release=self.release)
        self.env.validate_episode_reservation(reservation)
        record = self.env.reset(reservation=reservation)
        self.accepted = record.accepted
        self.env.validate_accepted_episode(accepted=self.accepted)
        activation = self.bank.begin_episode(accepted=self.accepted)
        WorldReceiptIssuer.validate(activation, "activation", self.bank)
        self.env.activate_episode(
            accepted=self.accepted, population_receipt=self.population.activation(self.accepted), curiosity_receipt=activation
        )

    def close_and_begin(self, steps: int, world0_steps: int | None = None) -> None:
        participants = tuple(world for world, count in zip(self.env.world_ids, self.env.step_counts.tolist(), strict=True) if count > 0)
        self.population.participants = participants
        outcomes = _outcomes(self.accepted, participants, steps)
        if world0_steps is not None:
            outcomes = tuple(
                replace(event, outcome=replace(event.outcome, survival_time=world0_steps)) if event.world_id == "world0" else event
                for event in outcomes
            )
        content = _content(outcomes)
        prepared = self.bank.prepare_completion(
            accepted=self.accepted,
            boundary_key=self.accepted.batch_episode,
            completion_content=content,
            outcomes=outcomes,
            participated_world_ids=participants,
        )
        closing = self.env.prepare_episode_close(
            accepted=self.accepted,
            boundary_key=self.accepted.batch_episode,
            completion_content=content,
            participated_world_ids=participants,
            dispositions=prepared.prepared_receipt,
        )
        self.env.freeze_episode_close(closing)
        committed = self.bank.commit_completion(prepared=prepared)
        closure = self.env.close_episode(closing, dispositions=committed)
        fields = dict(accepted=self.accepted, boundary_key=self.accepted.batch_episode, completion_content=content)
        children = {
            kind: (self.population if kind == "population_commit_receipt" else self.boundary).receipt(kind, **fields)
            for kind in (
                "curriculum_receipt",
                "exploration_receipt",
                "epsilon_install_receipt",
                "population_commit_receipt",
                "selection_sync_receipt",
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
        self.release = self.env.install_boundary_release(self.authority.completed(closure=closure, effects=effects))
        self.begin(self.accepted.batch_episode + 1)


@pytest.fixture
def harness_factory(compiled: Any) -> Any:
    def make(
        family: str,
        *,
        scope: str = "per_world",
        begin: bool = True,
        report_allocation: Any = None,
        ids: tuple[str, ...] = WORLD_IDS,
        width: int = 3,
    ) -> _Harness:
        return _Harness(compiled, family, scope, begin, report_allocation, ids, width)

    return make


@pytest.mark.parametrize("family", FAMILIES)
def test_pristine_current_producer_and_env_fixture_control(compiled: Any, family: str) -> None:
    """Independent positive: no BANK import or _bank_type lookup whatsoever."""
    policy = _policy(compiled, family, "per_world")
    descriptor = _descriptor(policy, WORLD_IDS, 3)
    owner = _owned(policy, descriptor, "world1")
    snapshot = owner.snapshot()
    assert snapshot["healthy"] is True and snapshot["rng"]["world_id"] == "world1"
    selector = make_policy_selector(policy)
    assert owner.call(lambda backend, sources: id(backend)) != id(selector)
    env = _env(compiled, WORLD_IDS)
    curiosity, population, boundary = _LocalRole(), _LocalRole(), _LocalRole()
    authority = _bind(env, curiosity, population, boundary)
    release = env.install_boundary_release(authority.bootstrap(first_batch_episode=1))
    reservation = env.prepare_episode(batch_episode=1, release=release)
    env.validate_episode_reservation(reservation)
    reset = env.reset(reservation=reservation)
    accepted = reset.accepted
    assert accepted.world_ids == WORLD_IDS and accepted.world_episode_seqs == (1, 1)
    assert env.validate_accepted_episode(accepted=accepted) is None
    with pytest.raises(ValueError):
        env.validate_accepted_episode(accepted=replace(accepted))
    activation = curiosity.activation(accepted)
    WorldReceiptIssuer.validate(activation, "activation", curiosity)
    env.activate_episode(accepted=accepted, population_receipt=population.activation(accepted), curiosity_receipt=activation)
    actions = env.get_action_masks().to(torch.int64).argmax(dim=1)
    observation, rewards, dones, info = env.step(actions, depletion_multiplier=1.0)
    assert observation.shape[0] == rewards.shape[0] == dones.shape[0] == 2
    assert bool((env.step_counts > 0).all())
    assert isinstance(info, dict)


@pytest.mark.parametrize("family", TRAINABLE)
def test_ordinary_episode_preserves_learning_rng_and_cumulative_clock(harness_factory: Any, family: str) -> None:
    h = harness_factory(family)
    for tick in range(1, 8):
        _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
    # Real ENV participation is required for its close permission; these legal
    # actions are a lifecycle control, not a claim of synthetic context routing.
    h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
    previous = h.accepted
    before = h.bank.snapshot_world(world_id="world1")
    h.close_and_begin(7)
    after = h.bank.snapshot_world(world_id="world1")
    assert after["cursor"]["eligible_seq"] == 0
    assert after["cursor"]["cumulative_service_position"] == before["cursor"]["cumulative_service_position"]
    _equal(before["backend"]["rng"], after["backend"]["rng"])
    _equal(_rnd_native(_native(before), family), _rnd_native(_native(after), family))
    with pytest.raises(ValueError):
        h.env.validate_accepted_episode(accepted=previous)
    _step(h.bank, h.accepted, _context(100, (False, True), 3, 0.0))
    assert h.bank.snapshot_world(world_id="world1")["cursor"]["cumulative_service_position"] == 8


@pytest.mark.parametrize("family,width", (("none", 0), ("count_based", 3)))
def test_supported_geometry_positive(harness_factory: Any, family: str, width: int) -> None:
    h = harness_factory(family, width=width)
    _, reward, _ = _step(h.bank, h.accepted, _context(1, (True, True), width, 0.0))
    assert reward.raw.shape == (2,) and torch.isfinite(reward.raw).all()


def test_count_zero_width_refuses_before_any_provider_call(harness_factory: Any, monkeypatch: Any) -> None:
    _bank_type()
    called: list[bool] = []

    def forbidden(*args: Any, **kwargs: Any) -> None:
        called.append(True)
        pytest.fail("Count D0 reached provider allocation")

    monkeypatch.setattr(importlib.import_module(BANK_MODULE), "make_backend", forbidden)
    with pytest.raises(ValueError):
        harness_factory("count_based", width=0)
    assert called == []


@pytest.mark.parametrize("family", FAMILIES)
def test_shared_real_family_and_aggregate_receipt(harness_factory: Any, family: str) -> None:
    h = harness_factory(family, scope="shared")
    for tick in range(1, 5):
        _, reward, receipts = _step(h.bank, h.accepted, _context(tick, (True, True), 3, 0.0))
        assert len(receipts) == 1 and receipts[0].world_id is None
        assert receipts[0].scope == reward.scope == "shared"
    state = _native(h.bank.snapshot_world(world_id="world1"))
    if family in TRAINABLE:
        assert _updates(state, family) >= 2
        assert any(bool(item["exp_avg"].ne(0).any()) for item in _optimizer(state, family)["state"].values())


@pytest.mark.parametrize("family", FAMILIES)
def test_exact_id_not_row_or_spectator_controls_private_state(harness_factory: Any, family: str) -> None:
    first = harness_factory(family)
    second = harness_factory(family, ids=("spectator", "world1", "world0"))
    third = harness_factory(family, ids=("world1", "world0"))
    for tick in range(1, 8):
        outputs = []
        for h in (first, second, third):
            rows = len(h.accepted.world_ids)
            predecessor = torch.full((rows, 3), 99.0)
            index = h.accepted.world_ids.index("world1")
            predecessor[index] = torch.tensor([0.1, 0.2, 0.3]) + tick / 11
            active = torch.zeros(rows, dtype=torch.bool)
            active[index] = True
            context = IntrinsicTransitionContext(
                predecessor=predecessor,
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
            _equal(outputs[0][2]["backend"], snapshot["backend"])
            _equal(outputs[0][2]["cursor"], snapshot["cursor"])


def test_adaptive_real_history_weight_and_per_row_scale(harness_factory: Any) -> None:
    first, second = harness_factory("adaptive_rnd"), harness_factory("adaptive_rnd")
    for episode in range(10):
        for h, other_survival in ((first, 1), (second, 12)):
            _step(h.bank, h.accepted, _context(episode + 1, (True, True), 3, float(other_survival)))
            h.env.step(h.env.get_action_masks().to(torch.int64).argmax(dim=1), depletion_multiplier=1.0)
            h.close_and_begin(7, world0_steps=other_survival)
        _equal(first.bank.snapshot_world(world_id="world1"), second.bank.snapshot_world(world_id="world1"))
    snapshots = {world: _native(first.bank.snapshot_world(world_id=world)) for world in WORLD_IDS}
    assert snapshots["world1"]["survival_history"] == [7] * 10
    assert snapshots["world0"]["survival_history"] == [1] * 10
    assert snapshots["world1"]["current_intrinsic_weight"] < snapshots["world1"]["initial_intrinsic_weight"]
    _, reward, _ = _step(first.bank, first.accepted, _context(100, (True, True), 3, 0.0))
    assert reward.scales[1].item() == pytest.approx(snapshots["world1"]["current_intrinsic_weight"])
    assert reward.scales[0] > reward.scales[1]
    assert reward.scales.shape == (2,)


@pytest.mark.parametrize("mutation", ("payload", "fingerprint", "order"))
def test_completion_content_is_full_canonical_outcome_not_just_hash(harness_factory: Any, mutation: str) -> None:
    h = harness_factory("adaptive_rnd")
    _step(h.bank, h.accepted, _context(1, (True, True), 3, 0.0))
    outcomes = _outcomes(h.accepted, WORLD_IDS, 1)
    content = list(_content(outcomes))
    if mutation == "payload":
        altered = replace(outcomes[-1], reward_total=9.0)
        content[-1] = (_content((altered,))[0][0], content[-1][1])
    elif mutation == "fingerprint":
        content[-1] = (content[-1][0], "0" * 64)
    else:
        content.reverse()
    before = tuple(h.bank.snapshot_world(world_id=world) for world in WORLD_IDS)
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
