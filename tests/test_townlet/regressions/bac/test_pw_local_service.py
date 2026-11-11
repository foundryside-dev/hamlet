"""PW04 producer contracts; actual POP/ordinary-runner qualification is separate.

All learning witnesses use the real providers and Adam with positive learning
rates. Current fixtures are constructed before assertions on the adopted ABI,
so the initial RED identifies a missing backend guarantee, not an import error.
"""

from __future__ import annotations

import inspect
import random
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import torch.nn.functional as functional
import yaml

from townlet.config.bac_options import BaCOptions, RNDOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.world_curiosity_state import OwnedWorldBackend, ServiceClock, WorldCuriosityDescriptor, WorldRNGState

PROVIDERS = ("rnd", "icm", "adaptive")
OVERFLOW = ("service_before_admit", "drop_oldest", "drop_newest")
PRIVATE = "world_eligible_admission"
SHARED = "vector_tick"


def _equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert left.device == right.device
        torch.testing.assert_close(left, right, rtol=0, atol=0, equal_nan=True)
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray)
        assert left.dtype == right.dtype
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict) and left.keys() == right.keys()
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _equal(a, b)
    else:
        assert left == right


def _ambient() -> tuple[Any, ...]:
    return torch.get_rng_state().clone(), random.getstate(), deepcopy(np.random.get_state())


def _rows(count: int, start: int = 0) -> torch.Tensor:
    values = torch.arange(start * 3, (start + count) * 3, dtype=torch.float32).reshape(count, 3)
    return values / 19 + torch.tensor([0.3, -0.7, 1.1])


def _rnd(backend: Any) -> RNDExploration:
    return backend.rnd if isinstance(backend, AdaptiveIntrinsicExploration) else backend


def _native(backend: Any) -> dict[str, Any]:
    return backend.checkpoint_state()


def _inner(state: dict[str, Any]) -> dict[str, Any]:
    return state["rnd_state"] if "rnd_state" in state else state


def _service_state(state: dict[str, Any]) -> dict[str, Any]:
    state = _inner(state)
    return state["predictor_service"] if "predictor_service" in state else state


def _position(backend: Any) -> int:
    value = _service_state(_native(backend))["service_position"]
    return 0 if value is None else value


def _parameters(state: dict[str, Any]) -> dict[str, torch.Tensor]:
    state = _inner(state)
    if "predictor_network" in state:
        return state["predictor_network"]
    return {f"{module}/{key}": value for module in ("encoder", "inverse_model", "forward_model") for key, value in state[module].items()}


def _learned(before: dict[str, Any], after: dict[str, Any]) -> None:
    old, new = _parameters(before), _parameters(after)
    assert any(not torch.equal(old[key], new[key]) for key in old)
    optimizer = _inner(after)["optimizer"]
    assert optimizer["state"]
    assert all(float(group["lr"]) > 0 for group in optimizer["param_groups"])
    assert all(float(value["step"]) > 0 for value in optimizer["state"].values())
    assert any(torch.count_nonzero(value["exp_avg"]).item() for value in optimizer["state"].values())
    if "fixed_network" in _inner(before):
        _equal(_inner(before)["fixed_network"], _inner(after)["fixed_network"])


def _conserved(backend: Any) -> None:
    state = _inner(_native(backend))
    service = _service_state(state)
    if "predictor_service" in state:
        pending = len(service["pending_observations"])
        counters = service
    else:
        pending = len(state["pending"])
        counters = state["counters"]
    assert counters["admitted_rows"] == counters["consumed_rows"] + counters["dropped_rows"] + pending
    assert counters["consumed_rows"] == counters["optimizer_updates"] * 2
    if service["service_clock_unit"] == PRIVATE:
        assert service["service_position"] == counters["admitted_rows"]


def _require_api(backend: Any) -> None:
    # The caller has already constructed/configured the actual current provider.
    assert isinstance(backend.checkpoint_state(), dict)
    for name in ("admit_and_service_at", "validate_state", "prepare_state", "install_state"):
        assert callable(getattr(backend, name, None)), f"PW04 missing backend ABI: {type(backend).__name__}.{name}"
    parameters = inspect.signature(type(backend)).parameters
    for name in ("rng", "service_clock_unit"):
        assert name in parameters, f"PW04 missing constructor ABI: {type(backend).__name__}.{name}"


# Fixture construction uses the root-supplied finite public type receipt.
@cache
def _policy(kind: str, overflow: str, unit: str) -> ResolvedExplorationPolicy:
    level = Path("/workspace/hamlet/configs/test/token_set_smoke/levels/L0_test")
    raw_training = yaml.safe_load((level / "training.yaml").read_text())["training"]
    raw_training["population"]["size"] = 2
    raw_training["replay_buffer"]["batch_size"] = 2
    raw_training["intrinsic"]["rnd"]["feature_dim"] = 3
    raw_training["intrinsic"]["rnd"]["learning_rate"] = 0.01
    training = TrainingV2Config.model_validate(raw_training)
    raw_drive = yaml.safe_load((level / "drive.yaml").read_text())["drive"]["intrinsic"]
    raw_drive["strategy"] = "adaptive_rnd" if kind == "adaptive" else kind
    private = unit == PRIVATE
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {
                "scope": "per_world" if private else "shared",
                "seed_policy": "world_id_derived_v1" if private else "legacy_shared_v1",
            },
            "rnd": {
                "service_mode": "paced_fifo",
                "max_updates_per_tick": 1,
                "max_pending_rows": 4,
                "overflow_policy": overflow,
            },
            "providers": {
                "icm": {
                    "feature_dim": 3,
                    "hidden_dim": 7,
                    "learning_rate": 0.01,
                    "inverse_weight": 0.8,
                    "forward_weight": 0.2,
                    "training_batch_size": 2,
                    "max_pending_transitions": 4,
                }
            },
        }
    )
    return resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(raw_drive), training, options)


def _build(kind: str, overflow: str, unit: str, **extra: Any) -> Any:
    inputs = {"rng": None, "service_clock_unit": unit, **extra}
    if kind == "icm":
        return ICMExploration(
            _policy(kind, overflow, unit),
            obs_dim=3,
            action_dim=3,
            feature_dim=3,
            hidden_dim=7,
            learning_rate=0.01,
            inverse_weight=0.8,
            forward_weight=0.2,
            training_batch_size=2,
            max_pending_transitions=4,
            device=torch.device("cpu"),
            **inputs,
        )
    if kind == "adaptive":
        backend = AdaptiveIntrinsicExploration(
            obs_dim=3,
            embed_dim=3,
            rnd_learning_rate=0.01,
            rnd_training_batch_size=2,
            initial_intrinsic_weight=1.0,
            min_intrinsic_weight=0.1,
            variance_threshold=100.0,
            min_survival_fraction=0.2,
            max_episode_length=100,
            survival_window=12,
            decay_rate=0.9,
            **inputs,
        )
    else:
        backend = RNDExploration(obs_dim=3, embed_dim=3, learning_rate=0.01, training_batch_size=2, **inputs)
    options = RNDOptions(
        service_mode="paced_fifo",
        max_updates_per_tick=1,
        max_pending_rows=4,
        overflow_policy=overflow,
    )
    # Retain the original nested configuration fixture while transporting the
    # required constructor inputs; the preflight and behavioral assertions stay intact.
    _rnd(backend).configure_service(options)
    return backend


def _make(kind: str, *, overflow: str = "service_before_admit", unit: str = PRIVATE, rng: Any = None) -> Any:
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(314)
        current = _build(kind, overflow, unit)
        _require_api(current)
        if kind == "adaptive":
            for name in ("configure_service", "predictor_service_counters", "admit_and_service"):
                assert callable(getattr(current, name, None)), f"PW04 missing adaptive delegation: {name}"
        torch.manual_seed(314)
        backend = _build(kind, overflow, unit, service_clock_unit=unit, rng=rng)
    assert backend.service_clock_unit == unit
    return backend


def _rng(kind: str, world: str = "world-a") -> Any:
    descriptor = WorldCuriosityDescriptor.from_policy(
        _policy(kind, "service_before_admit", PRIVATE),
        world_ids=("world-a", "world-b"),
        observation_dim=3,
        action_dim=3,
        training_seed=17,
    )
    return WorldRNGState.create(descriptor=descriptor, world_id=world, cuda_devices=())


def _owned(kind: str) -> Any:
    # Check the actual current provider fixture before invoking the new hooks.
    _make(kind)
    return OwnedWorldBackend.construct(
        rng=_rng(kind),
        factory=lambda candidate_rng: _build(
            kind,
            "service_before_admit",
            PRIVATE,
            service_clock_unit=PRIVATE,
            rng=candidate_rng,
        ),
    )


def _context(rows: torch.Tensor, tick: int, *, active: torch.Tensor | None = None) -> IntrinsicTransitionContext:
    count = len(rows)
    if active is None:
        active = torch.ones(count, dtype=torch.bool)
    return IntrinsicTransitionContext(
        predecessor=rows,
        actions=torch.round((rows[:, 0] - 0.3) * 19 / 3).to(torch.int64) % 3,
        successor=rows * 0.7 + torch.tensor([0.2, 0.1, -0.3]),
        active_on_entry=active,
        vector_tick=tick,
    )


def _serve(
    backend: Any,
    rows: torch.Tensor,
    *,
    tick: int = 1,
    position: int | None = None,
    active: torch.Tensor | None = None,
) -> Any:
    unit = backend.service_clock_unit
    count = len(rows) if active is None else int(active.sum().item())
    if position is None:
        position = _position(backend) + count if unit == PRIVATE else tick
    clock = ServiceClock(unit, position)
    if isinstance(backend, ICMExploration):
        return backend.admit_and_service_at(_context(rows, tick, active=active), clock=clock)
    assert active is None
    return backend.admit_and_service_at(rows, clock=clock)


def _traced(backend: Any, rows: torch.Tensor, **kwargs: Any) -> tuple[Any, list[dict[str, Any]]]:
    """Observe real network forwards and Adam steps without replacing either."""
    provider = _rnd(backend)
    current: dict[str, Any] = {}
    updates: list[dict[str, Any]] = []
    handles = []

    def remember(name: str) -> Any:
        def hook(module: Any, inputs: Any, output: torch.Tensor) -> None:
            current[name] = (inputs[0].detach().clone(), output.detach().clone())

        return hook

    if isinstance(provider, ICMExploration):
        encoded: list[tuple[torch.Tensor, torch.Tensor]] = []

        def encoder_hook(module: Any, inputs: Any, output: torch.Tensor) -> None:
            encoded.append((inputs[0].detach().clone(), output.detach().clone()))

        handles.append(provider.encoder.register_forward_hook(encoder_hook))
        handles.append(provider.inverse_model.register_forward_hook(remember("inverse")))
        handles.append(provider.forward_model.register_forward_hook(remember("forward")))

        def before_step(optimizer: Any, args: Any, kwargs: Any) -> None:
            assert len(encoded) == 2
            predecessor, target = encoded[0][0], encoded[1][1]
            forward_inputs, predicted = current["forward"]
            actions = forward_inputs[:, -provider.action_dim :].argmax(dim=1)
            loss = provider.inverse_weight * functional.cross_entropy(current["inverse"][1], actions)
            loss = loss + provider.forward_weight * (predicted - target).square().mean()
            updates.append({"rows": predecessor, "actions": actions.clone(), "successor": encoded[1][0], "loss": float(loss)})
            encoded.clear()

    else:
        handles.append(provider.fixed_network.register_forward_hook(remember("target")))
        handles.append(provider.predictor_network.register_forward_hook(remember("predictor")))

        def before_step(optimizer: Any, args: Any, kwargs: Any) -> None:
            observations, prediction = current["predictor"]
            loss = functional.mse_loss(prediction, current["target"][1])
            updates.append({"rows": observations, "loss": float(loss)})

    handles.append(provider.optimizer.register_step_pre_hook(before_step))
    try:
        receipt = _serve(backend, rows, **kwargs)
    finally:
        for handle in handles:
            handle.remove()
    assert receipt.optimizer_updates == len(updates)
    if updates:
        assert receipt.last_loss == updates[-1]["loss"]
    _conserved(backend)
    return receipt, updates


def _reward(backend: Any, rows: torch.Tensor, tick: int) -> torch.Tensor:
    if isinstance(backend, ICMExploration):
        return backend.compute_transition_novelty(_context(rows, tick), update_stats=True)
    return backend.compute_intrinsic_rewards(rows, update_stats=True)


def _warm(backend: Any) -> None:
    initial = _native(backend)
    _serve(backend, _rows(5))
    _reward(backend, _rows(3, 9), 1)
    if isinstance(backend, AdaptiveIntrinsicExploration):
        for _ in range(12):
            backend.update_on_episode_end(40.0)
        assert backend.current_intrinsic_weight < backend.initial_intrinsic_weight
    _learned(initial, _native(backend))
    _conserved(backend)


def _full_tail(backend: Any) -> torch.Tensor:
    """Import a legal full tail; do not pretend fresh private pacing creates it."""
    _warm(backend)
    state = _native(backend)
    inner = _inner(state)
    service = _service_state(state)
    rows = _rows(4, 30)
    if isinstance(backend, ICMExploration):
        context = _context(rows, 1)
        inner["pending"] = [
            {"predecessor": context.predecessor[i].clone(), "action": int(context.actions[i]), "successor": context.successor[i].clone()}
            for i in range(4)
        ]
        counters = inner["counters"]
    else:
        service["pending_observations"] = rows.clone()
        counters = service
    counters["admitted_rows"] = counters["consumed_rows"] + counters["dropped_rows"] + 4
    service["service_position"] = counters["admitted_rows"]
    backend.validate_state(state)
    backend.load_state(state)
    _equal(state, _native(backend))
    return rows


def _must_refuse_unchanged(backend: Any, operation: Any) -> None:
    before, ambient = _native(backend), _ambient()
    with pytest.raises(ValueError):
        operation()
    _equal(before, _native(backend))
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("full_tail", (False, True))
def test_local_clock_ignores_idle_vector_ticks(kind: str, full_tail: bool) -> None:
    backend = _make(kind)
    if full_tail:
        _full_tail(backend)
    else:
        _warm(backend)
    before = _native(backend)
    position = _position(backend)
    for tick in (2, 73, 10000, 10000):
        rows = _rows(3) if kind == "icm" else _rows(0)
        active = torch.zeros(3, dtype=torch.bool) if kind == "icm" else None
        receipt, updates = _traced(backend, rows, tick=tick, position=position, active=active)
        assert receipt.admitted_rows == receipt.consumed_rows == receipt.dropped_rows == receipt.optimizer_updates == 0
        assert updates == []
        _equal(before, _native(backend))
    _must_refuse_unchanged(backend, lambda: _serve(backend, _rows(0), position=position + 1))
    _must_refuse_unchanged(backend, lambda: _serve(backend, _rows(1), position=position))
    receipt, updates = _traced(backend, _rows(1, 50), tick=10001)
    assert receipt.admitted_rows == 1
    assert updates
    assert _position(backend) == position + 1
    _learned(before, _native(backend))


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("overflow", OVERFLOW)
def test_backend_losses_and_quotas_are_world_local(kind: str, overflow: str) -> None:
    world1 = _make(kind, overflow=overflow)
    _warm(world1)
    initial = _native(world1)
    other_schedule = _make(kind, overflow=overflow)
    other_schedule.load_state(initial)
    world0 = _make(kind, overflow=overflow)
    before0 = _native(world0)
    before1 = _native(world1)
    first_trace, second_trace = [], []
    for step, count in enumerate((1, 3, 2, 1), start=1):
        local = _rows(count, 60 + step * 7)
        receipt, trace = _traced(world1, local, tick=step)
        first_trace.extend(trace)
        for pressure in range(step + 1):
            pressure_receipt, _ = _traced(world0, _rows(7, 150 + pressure * 11), tick=step * 100 + pressure)
            assert pressure_receipt.optimizer_updates > 0
            assert pressure_receipt.dropped_rows == 0
            _reward(world0, _rows(3, 20 + pressure), step)
            if kind == "adaptive":
                for _ in range(12):
                    world0.update_on_episode_end(40.0)
        for idle in range(3):
            empty_receipt, empty_trace = _traced(other_schedule, _rows(0), tick=step * 1000 + idle)
            assert empty_receipt.optimizer_updates == 0 and not empty_trace
        other_receipt, other_trace = _traced(other_schedule, local, tick=step * 1000 + 99)
        second_trace.extend(other_trace)
        assert receipt == other_receipt
        _equal(_reward(world1, local, step), _reward(other_schedule, local, step * 1000 + 99))
        if kind == "adaptive":
            world1.update_on_episode_end(40.0)
            other_schedule.update_on_episode_end(40.0)
        _equal(_native(world1), _native(other_schedule))
    _equal(first_trace, second_trace)
    _learned(before0, _native(world0))
    _learned(before1, _native(world1))
    assert first_trace


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("overflow", OVERFLOW)
@pytest.mark.parametrize("full_tail", (False, True))
def test_private_admission_partition_invariance(kind: str, overflow: str, full_tail: bool) -> None:
    whole = _make(kind, overflow=overflow)
    if full_tail:
        _full_tail(whole)
    split = _make(kind, overflow=overflow)
    split.load_state(_native(whole))
    rows = _rows(7, 80)
    full_receipt, full_trace = _traced(whole, rows)
    split_trace = []
    totals = {key: 0 for key in ("admitted_rows", "consumed_rows", "dropped_rows", "optimizer_updates")}
    offset = 0
    # Observation-derived actions preserve the exact transition across partitions.
    for tick, count in enumerate((1, 3, 0, 2, 1), start=1):
        receipt, trace = _traced(split, rows[offset : offset + count], tick=tick * 19)
        split_trace.extend(trace)
        offset += count
        for key in totals:
            totals[key] += getattr(receipt, key)
    assert offset == len(rows)
    for key, value in totals.items():
        assert value == getattr(full_receipt, key)
    _equal(full_trace, split_trace)
    _equal(_native(whole), _native(split))
    if kind != "icm":
        assert full_receipt.dropped_rows == full_receipt.overflow_optimizer_updates == 0


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
@pytest.mark.parametrize("overflow", OVERFLOW)
def test_shared_same_tick_overflow_really_learns(kind: str, overflow: str) -> None:
    backend = _make(kind, overflow=overflow, unit=SHARED)
    before = _native(backend)
    rows = _rows(10, 10)
    receipt, trace = _traced(backend, rows, tick=7)
    assert receipt.admitted_rows == 10
    assert receipt.paced_optimizer_updates == 1
    _equal(trace[0]["rows"], rows[:2])
    state = _service_state(_native(backend))
    if overflow == "service_before_admit":
        assert receipt.overflow_optimizer_updates == 2 and receipt.dropped_rows == 0
        _equal(torch.cat([update["rows"] for update in trace]), rows[:6])
        _equal(state["pending_observations"], rows[6:])
    else:
        assert receipt.overflow_optimizer_updates == 0 and receipt.dropped_rows == 4
        _equal(state["pending_observations"], rows[6:] if overflow == "drop_oldest" else rows[2:6])
    assert state["service_position"] == 7
    same, same_trace = _traced(backend, _rows(0), tick=7)
    assert same.optimizer_updates == 0 and not same_trace
    newer, newer_trace = _traced(backend, _rows(0), tick=8)
    assert newer.optimizer_updates == 1 and len(newer_trace) == 1
    _learned(before, _native(backend))


@pytest.mark.parametrize("overflow", OVERFLOW)
def test_private_icm_full_imported_tail_overflow(overflow: str) -> None:
    backend = _make("icm", overflow=overflow)
    tail = _full_tail(backend)
    before = _native(backend)
    new = _rows(1, 90)
    receipt, trace = _traced(backend, new)
    assert receipt.admitted_rows == 1
    if overflow == "service_before_admit":
        assert receipt.mandatory_service_updates == 1 and receipt.dropped_rows == 0
        assert len(trace) == 2
        _equal(torch.cat([item["rows"] for item in trace]), tail)
        _equal(_native(backend)["pending"][0]["predecessor"], new[0])
    else:
        assert receipt.mandatory_service_updates == 0 and receipt.dropped_rows == 1
        assert len(trace) == 1
        expected = tail[1:3] if overflow == "drop_oldest" else tail[:2]
        _equal(trace[0]["rows"], expected)
        expected_pending = torch.cat((tail[3:], new)) if overflow == "drop_oldest" else tail[2:]
        _equal(torch.stack([row["predecessor"] for row in _native(backend)["pending"]]), expected_pending)
    _learned(before, _native(backend))


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("unit", (PRIVATE, SHARED))
def test_current_native_warm_adam_tail_and_next_update(kind: str, unit: str) -> None:
    source = _make(kind, unit=unit)
    _warm(source)
    saved = _native(source)
    inner = _inner(saved)
    service = _service_state(saved)
    assert inner["schema"] == ("icm-state-v4" if kind == "icm" else "rnd-state-v4")
    if kind == "adaptive":
        assert saved["schema"] == "adaptive-intrinsic-state-v4"
    assert service["service_clock_unit"] == unit
    assert "vector_tick" not in service and "service_tick" not in service
    pending = inner["pending"] if kind == "icm" else service["pending_observations"]
    assert len(pending) > 0
    destination = _make(kind, unit=unit)
    before, ambient = _native(destination), _ambient()
    destination.validate_state(saved)
    prepared = destination.prepare_state(saved)
    _equal(before, _native(destination))
    _equal(ambient, _ambient())
    destination.install_state(prepared)
    _equal(saved, _native(destination))
    rows = _rows(3, 110)
    receipt, trace = _traced(source, rows, tick=2)
    resumed_receipt, resumed_trace = _traced(destination, rows, tick=2)
    assert receipt == resumed_receipt
    _equal(trace, resumed_trace)
    _equal(_native(source), _native(destination))
    _learned(saved, _native(destination))


@pytest.mark.parametrize("kind", PROVIDERS)
def test_owned_native_real_learning_and_rng_continuation(kind: str) -> None:
    source = _owned(kind)

    def warm_and_draw(backend: Any, sources: Any) -> None:
        _warm(backend)
        torch.rand(5)
        random.random()
        np.random.random(3)
        sources.numpy.random(4)

    ambient = _ambient()
    source.call(warm_and_draw, lineage=None)
    _equal(ambient, _ambient())
    saved = source.snapshot(lineage=None)
    destination = _owned(kind)

    def factory(rng: Any) -> Any:
        return _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng)

    prepared = destination.prepare_restore(
        saved, factory=factory, validate_backend=lambda candidate, payload: candidate.validate_state(payload), lineage=None
    )
    destination.install(prepared, lineage=None)
    _equal(saved, destination.snapshot(lineage=None))

    def next_work(backend: Any, sources: Any) -> Any:
        draws = (torch.rand(3), random.random(), np.random.random(2), sources.numpy.random(3))
        receipt, trace = _traced(backend, _rows(3, 140))
        return draws, receipt, trace, _native(backend)

    _equal(source.call(next_work, lineage=None), destination.call(next_work, lineage=None))
    _equal(source.snapshot(lineage=None), destination.snapshot(lineage=None))
    _equal(ambient, _ambient())

    before = destination.snapshot(lineage=None)
    prepared = destination.prepare_restore(
        saved,
        factory=factory,
        validate_backend=lambda candidate, payload: candidate.validate_state(payload),
        lineage=None,
    )
    _equal(before, destination.snapshot(lineage=None))
    _equal(ambient, _ambient())
    # After successful restore and next learning, independently show that an
    # observation stales a new handle without changing the destination's state.
    with pytest.raises(ValueError, match="destination changed"):
        destination.install(prepared, lineage=None)
    _equal(before, destination.snapshot(lineage=None))
    _equal(ambient, _ambient())


def _corrupt(state: dict[str, Any], case: str) -> None:
    inner, service = _inner(state), _service_state(state)
    icm = "pending" in inner
    counters = inner["counters"] if icm else service
    optimizer = inner["optimizer"]
    moments = next(iter(optimizer["state"].values()))
    if case == "moment_nan":
        list(optimizer["state"].values())[-1]["exp_avg"].flatten()[-1] = float("nan")
    elif case == "missing_moment":
        del optimizer["state"][next(iter(optimizer["state"]))]
    elif case == "negative_variance":
        moments["exp_avg_sq"].flatten()[-1] = -1
    elif case == "step":
        moments["step"] += 1
    elif case == "lr":
        optimizer["param_groups"][0]["lr"] = -0.01
    elif case == "flags":
        optimizer["param_groups"][0]["amsgrad"] = "false"
    elif case == "tail_nan":
        tail = inner["pending"][-1]["successor"] if icm else service["pending_observations"][-1]
        tail[-1] = float("nan")
    elif case == "tail_shape":
        if icm:
            inner["pending"][-1]["predecessor"] = torch.zeros(4)
        else:
            service["pending_observations"] = torch.zeros((1, 4))
    elif case == "conservation":
        counters["admitted_rows"] += 1
    elif case == "position":
        service["service_position"] += 1
    elif case == "unit":
        service["service_clock_unit"] = SHARED
    elif case == "budget":
        service["ordinary_updates_at_position"] = 2
    elif case == "schema":
        inner["schema"] = "icm-state-v1" if icm else "rnd-state-v1"
    elif case == "unknown":
        inner["unexpected"] = 0
    elif case == "offset":
        service["optimizer_step_offset"] += 1
    elif case == "capacity":
        if icm:
            inner["pending"] = inner["pending"] * 5
        else:
            service["pending_observations"] = service["pending_observations"].repeat(5, 1)
        counters["admitted_rows"] = counters["consumed_rows"] + counters["dropped_rows"] + 5
        service["service_position"] = counters["admitted_rows"]
    elif case == "policy":
        inner["policy_identity"] = "wrong-policy"
    elif case == "config":
        inner["config"]["inverse_weight"] = 0.3
    else:
        raise AssertionError(case)


INVALID_NATIVE = (
    "moment_nan",
    "missing_moment",
    "negative_variance",
    "step",
    "lr",
    "flags",
    "tail_nan",
    "tail_shape",
    "conservation",
    "position",
    "unit",
    "budget",
    "schema",
    "unknown",
    "capacity",
)


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("case", INVALID_NATIVE)
def test_deep_native_refuses_before_any_live_install(kind: str, case: str) -> None:
    backend = _make(kind)
    _warm(backend)
    saved = _native(backend)
    damaged = deepcopy(saved)
    _corrupt(damaged, case)
    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
        _must_refuse_unchanged(backend, lambda: method(damaged))
        _equal(saved, _native(backend))


@pytest.mark.parametrize("kind,case", (("rnd", "offset"), ("adaptive", "offset"), ("icm", "policy"), ("icm", "config")))
def test_provider_specific_native_refusal(kind: str, case: str) -> None:
    backend = _make(kind)
    _warm(backend)
    damaged = _native(backend)
    _corrupt(damaged, case)
    _must_refuse_unchanged(backend, lambda: backend.validate_state(damaged))
    _must_refuse_unchanged(backend, lambda: backend.load_state(damaged))


@pytest.mark.parametrize(
    "case", ("missing", "history_nan", "history_negative", "history_bool", "history_long", "derived", "config", "weight", "outer_schema")
)
def test_adaptive_outer_failure_cannot_install_valid_changed_rnd(case: str) -> None:
    backend = _make("adaptive")
    _warm(backend)
    changed = _make("adaptive")
    changed.load_state(_native(backend))
    _serve(changed, _rows(3, 210))
    candidate = _native(changed)
    assert any(
        not torch.equal(a, candidate["rnd_state"]["predictor_network"][key])
        for key, a in _native(backend)["rnd_state"]["predictor_network"].items()
    )
    if case == "missing":
        del candidate["survival_history"]
    elif case == "history_nan":
        candidate["survival_history"][-1] = float("nan")
    elif case == "history_negative":
        candidate["survival_history"][-1] = -1
    elif case == "history_bool":
        candidate["survival_history"][-1] = True
    elif case == "history_long":
        candidate["survival_history"].append(40.0)
    elif case == "derived":
        candidate["min_survival_for_annealing"] += 1
    elif case == "config":
        candidate["decay_rate"] = 0.7
    elif case == "weight":
        candidate["current_intrinsic_weight"] = 2.0
    else:
        candidate["schema"] = "adaptive-intrinsic-state-v1"
    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
        _must_refuse_unchanged(backend, lambda: method(candidate))


def _mutate_owned_tree(value: Any) -> None:
    if isinstance(value, torch.Tensor):
        value.add_(1)
    elif isinstance(value, np.ndarray):
        value[...] = 0
    elif isinstance(value, dict):
        for nested in value.values():
            _mutate_owned_tree(nested)
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _mutate_owned_tree(nested)
            if isinstance(value, list) and isinstance(nested, (int, float)):
                value[index] = nested + 1


@pytest.mark.parametrize("kind", PROVIDERS)
def test_native_snapshot_preparation_and_two_restores_own_every_leaf(kind: str) -> None:
    source = _make(kind)
    _warm(source)
    payload = _native(source)
    pristine = deepcopy(payload)
    first, second = _make(kind), _make(kind)
    prepared = first.prepare_state(payload)
    second.load_state(payload)
    _mutate_owned_tree(payload)
    if kind == "adaptive":
        payload["survival_history"].append(999.0)
    _equal(pristine, _native(source))
    _equal(pristine, _native(second))
    first.install_state(prepared)
    _equal(pristine, _native(first))
    _serve(first, _rows(3, 240))
    if kind == "adaptive":
        first.update_on_episode_end(55.0)
    _equal(pristine, _native(second))
    _equal(pristine, _native(source))
    snapshot = _native(second)
    _mutate_owned_tree(snapshot)
    _equal(pristine, _native(second))


@pytest.mark.parametrize("kind", PROVIDERS)
def test_prepared_candidate_is_destination_bound_and_single_install(kind: str) -> None:
    source = _make(kind)
    _warm(source)
    first, second = _make(kind), _make(kind)
    prepared = first.prepare_state(_native(source))
    _must_refuse_unchanged(second, lambda: second.install_state(prepared))
    first.install_state(prepared)
    _equal(_native(source), _native(first))
    _must_refuse_unchanged(first, lambda: first.install_state(prepared))


def _watch_forwards(backend: Any, calls: list[Any]) -> list[Any]:
    provider = _rnd(backend)
    modules = (
        (provider.encoder, provider.inverse_model, provider.forward_model)
        if isinstance(provider, ICMExploration)
        else (provider.fixed_network, provider.predictor_network)
    )

    def observe(module: Any, inputs: Any) -> None:
        calls.append(module)

    return [module.register_forward_pre_hook(observe) for module in modules]


@pytest.mark.parametrize(
    "kind,case",
    [
        (kind, case)
        for kind in PROVIDERS
        for case in ("late_nan", "shape", "dtype", "clock_unit", "clock_gap", "clock_regress", "clock_type", "clock_forged_bool")
        if (kind, case) != ("icm", "late_nan")
    ],
)
def test_entire_batch_and_clock_preflight_precedes_callbacks(kind: str, case: str) -> None:
    backend = _make(kind)
    _warm(backend)
    rows = _rows(3, 260)
    clock: Any = ServiceClock(PRIVATE, _position(backend) + 3)
    if case == "late_nan":
        rows[-1, -1] = float("nan")
    elif case == "shape":
        rows = torch.ones((3, 4), dtype=torch.float32)
    elif case == "dtype":
        rows = rows.to(torch.float64)
    elif case == "clock_unit":
        clock = ServiceClock(SHARED, _position(backend) + 3)
    elif case == "clock_gap":
        clock = ServiceClock(PRIVATE, _position(backend) + 4)
    elif case == "clock_regress":
        clock = ServiceClock(PRIVATE, _position(backend) - 1)
    elif case == "clock_type":
        clock = {"unit": PRIVATE, "position": _position(backend) + 3}
    else:
        if case == "clock_forged_bool":
            clock = object.__new__(ServiceClock)
            object.__setattr__(clock, "unit", PRIVATE)
            object.__setattr__(clock, "position", True)
    # Actual RP refuses nonfinite contexts itself, hence the ICM NaN pair is
    # excluded above and covered separately with explicit context-boundary credit.
    context = None
    if kind == "icm":
        context = IntrinsicTransitionContext(
            predecessor=rows,
            successor=rows * 0.7,
            actions=torch.tensor([0, 1, 2]),
            active_on_entry=torch.ones(3, dtype=torch.bool),
            vector_tick=1,
        )
    calls: list[Any] = []
    handles = _watch_forwards(backend, calls)
    before, ambient = _native(backend), _ambient()
    try:
        with pytest.raises(ValueError):
            if kind == "icm":
                backend.admit_and_service_at(context, clock=clock)
            else:
                backend.admit_and_service_at(rows, clock=clock)
        assert not calls
        _equal(before, _native(backend))
        _equal(ambient, _ambient())
    finally:
        for handle in handles:
            handle.remove()


def test_icm_inactive_rows_and_late_active_action_are_validated() -> None:
    backend = _make("icm")
    _warm(backend)
    rows = _rows(3, 280)
    bad = IntrinsicTransitionContext(
        predecessor=rows,
        successor=rows * 0.7,
        actions=torch.tensor([0, 1, 3]),
        active_on_entry=torch.ones(3, dtype=torch.bool),
        vector_tick=10,
    )
    calls: list[Any] = []
    handles = _watch_forwards(backend, calls)
    try:
        _must_refuse_unchanged(backend, lambda: backend.admit_and_service_at(bad, clock=ServiceClock(PRIVATE, _position(backend) + 3)))
        assert not calls
    finally:
        for handle in handles:
            handle.remove()
    active = torch.tensor([True, False, True])
    position = _position(backend)
    receipt, trace = _traced(backend, rows, active=active, tick=99)
    assert receipt.admitted_rows == 2 and _position(backend) == position + 2
    assert trace
    _conserved(backend)


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
@pytest.mark.parametrize("incomplete", (False, True))
def test_shared_direct_buffer_validates_every_row_before_reconciliation(kind: str, incomplete: bool) -> None:
    # Existing API: reach the actual current preflight defect independently of
    # new-clock ABI absence, with a valid configured real provider fixture.
    backend = _build(kind, "service_before_admit", SHARED)
    provider = _rnd(backend)
    provider.obs_buffer.extend(row.clone() for row in _rows(1 if incomplete else 3, 300))
    provider.obs_buffer[-1][-1] = float("nan")
    # External edits precede this baseline; rejection must preserve them as-is.
    before = _native(backend)
    counters = provider.predictor_service_counters()
    clock = provider.step_counter
    calls: list[Any] = []
    handles = _watch_forwards(backend, calls)
    try:
        with pytest.raises(ValueError):
            provider.update_predictor()
        assert not calls
        assert provider.predictor_service_counters() == counters
        assert provider.step_counter == clock
        _equal(before, _native(backend))
    finally:
        for handle in handles:
            handle.remove()


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
def test_configured_shared_update_preflights_before_step_counter_change(kind: str) -> None:
    backend = _build(kind, "service_before_admit", SHARED)
    provider = _rnd(backend)
    provider.admit_and_service(_rows(3), vector_tick=50)
    clock, before = provider.step_counter, _native(backend)
    calls: list[Any] = []
    handles = _watch_forwards(backend, calls)
    rows = _rows(3, 320)
    rows[-1, -1] = float("nan")
    try:
        with pytest.raises(ValueError):
            backend.update({"observations": rows})
        assert not calls and provider.step_counter == clock
        _equal(before, _native(backend))
    finally:
        for handle in handles:
            handle.remove()


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
def test_shared_direct_training_and_native_lr_offset_remain_real(kind: str) -> None:
    backend = _make(kind, unit=SHARED)
    before = _native(backend)
    backend.update({"observations": _rows(5)})
    _learned(before, _native(backend))
    provider = _rnd(backend)
    provider.optimizer.param_groups[0]["lr"] = 0.007
    provider.optimizer.zero_grad()
    loss = sum(parameter.square().mean() for parameter in provider.predictor_network.parameters())
    loss.backward()
    provider.optimizer.step()
    saved = _native(backend)
    assert _service_state(saved)["optimizer_step_offset"] == 1
    destination = _make(kind, unit=SHARED)
    destination.load_state(saved)
    _equal(saved, _native(destination))
    backend.update({"observations": _rows(3, 340)})
    destination.update({"observations": _rows(3, 340)})
    _equal(_native(backend), _native(destination))
    # Unconfigured direct training remains a current substantive operation.
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(19)
        direct = (
            AdaptiveIntrinsicExploration(
                obs_dim=3, embed_dim=3, rnd_learning_rate=0.01, rnd_training_batch_size=2, rng=None, service_clock_unit=SHARED
            )
            if kind == "adaptive"
            else RNDExploration(obs_dim=3, embed_dim=3, learning_rate=0.01, training_batch_size=2, rng=None, service_clock_unit=SHARED)
        )
    _require_api(direct)
    start = _native(direct)
    direct.update({"observations": _rows(5)})
    _learned(start, _native(direct))
    assert len(_rnd(direct).obs_buffer) == 3
    _rnd(direct).update_predictor()
    assert len(_rnd(direct).obs_buffer) == 1
    _conserved(direct)


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
def test_private_direct_training_and_old_native_import_refuse(kind: str) -> None:
    backend = _make(kind)
    _warm(backend)
    _must_refuse_unchanged(backend, lambda: backend.update({"observations": _rows(3)}))
    _must_refuse_unchanged(backend, lambda: _rnd(backend).update_predictor())
    _must_refuse_unchanged(backend, lambda: _rnd(backend).admit_and_service(_rows(1), vector_tick=99))
    old = _native(backend)
    del _inner(old)["predictor_service"]
    _must_refuse_unchanged(backend, lambda: backend.validate_state(old))
    _must_refuse_unchanged(backend, lambda: backend.load_state(old))


@pytest.mark.parametrize("kind", PROVIDERS)
def test_selected_unit_is_immutable_and_shared_calls_are_explicit(kind: str) -> None:
    backend = _make(kind)
    before = _native(backend)
    with pytest.raises((AttributeError, ValueError)):
        backend.service_clock_unit = SHARED
    _equal(before, _native(backend))
    if kind == "icm":
        _must_refuse_unchanged(backend, lambda: backend.admit_and_service(_context(_rows(1), 99)))
    shared = _make(kind, unit=SHARED)
    if kind == "icm":
        context = _context(_rows(3), 4)
        _must_refuse_unchanged(shared, lambda: shared.admit_and_service_at(context, clock=ServiceClock(SHARED, 5)))
        receipt = shared.admit_and_service(context)
    else:
        receipt = shared.admit_and_service(_rows(3), vector_tick=4)
    assert receipt.admitted_rows == 3 and receipt.optimizer_updates == 1
    _conserved(shared)


@pytest.mark.parametrize("bad", (float("nan"), float("inf"), -1.0, True, 1e100))
def test_adaptive_completion_preflights_history_before_append(bad: Any) -> None:
    backend = _make("adaptive")
    _warm(backend)
    _must_refuse_unchanged(backend, lambda: backend.update_on_episode_end(bad))


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
def test_rnd_reward_input_and_empty_statistics_are_preflighted(kind: str) -> None:
    backend = _make(kind)
    _warm(backend)
    before = _native(backend)
    assert backend.compute_intrinsic_rewards(_rows(0), update_stats=True).shape == (0,)
    _equal(before, _native(backend))
    rows = _rows(3)
    rows[-1, -1] = float("nan")
    calls: list[Any] = []
    handles = _watch_forwards(backend, calls)
    try:
        _must_refuse_unchanged(backend, lambda: backend.compute_intrinsic_rewards(rows, update_stats=True))
        _must_refuse_unchanged(backend, lambda: backend.compute_intrinsic_rewards(_rows(3), update_stats=1))
        assert not calls
    finally:
        for handle in handles:
            handle.remove()


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("component", ("model_init", "target", "predictor", "service"))
def test_real_constructor_component_hooks_and_unused_streams(kind: str, component: str) -> None:
    first_rng, second_rng = _rng(kind), _rng(kind)
    ambient = _ambient()
    with second_rng.activate(component):
        torch.rand(7)
    _equal(ambient, _ambient())
    original_rng = first_rng.snapshot()
    first = _make(kind, rng=first_rng)
    second = _make(kind, rng=second_rng)
    _equal(ambient, _ambient())
    first_state, second_state = _inner(_native(first)), _inner(_native(second))
    modules = ("encoder", "inverse_model", "forward_model") if kind == "icm" else ("fixed_network", "predictor_network")
    expected_changes = {
        "model_init": {"encoder", "inverse_model"} if kind == "icm" else set(),
        "target": set() if kind == "icm" else {"fixed_network"},
        "predictor": {"forward_model"} if kind == "icm" else {"predictor_network"},
        "service": set(),
    }[component]
    for module in modules:
        changed = any(not torch.equal(value, second_state[module][key]) for key, value in first_state[module].items())
        assert changed == (module in expected_changes), (kind, component, module)
    after_rng = first_rng.snapshot()
    unused = ("target", "service") if kind == "icm" else ("model_init", "service")
    for name in unused:
        _equal(original_rng["components"][name], after_rng["components"][name])
    used = ("model_init", "predictor") if kind == "icm" else ("target", "predictor")
    for name in used:
        assert not torch.equal(original_rng["components"][name]["torch_cpu"], after_rng["components"][name]["torch_cpu"])


@pytest.mark.parametrize("kind", PROVIDERS)
def test_shared_constructor_preserves_original_ambient_draw_order(kind: str) -> None:
    # Reference allocations only: these objects never implement provider learning.
    # Use the actual RNDNetwork, and the exact declared ICM Linear/ReLU sequence.
    from townlet.exploration.rnd import RNDNetwork

    _make(kind, unit=SHARED)
    ambient = _ambient()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(812)
        if kind == "icm":
            expected = {
                "encoder": torch.nn.Sequential(torch.nn.Linear(3, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
                "inverse_model": torch.nn.Sequential(torch.nn.Linear(6, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
                "forward_model": torch.nn.Sequential(torch.nn.Linear(6, 7), torch.nn.ReLU(), torch.nn.Linear(7, 3)),
            }
        else:
            expected = {"fixed_network": RNDNetwork(3, 3), "predictor_network": RNDNetwork(3, 3)}
        expected_state = {name: module.state_dict() for name, module in expected.items()}
        expected_rng = torch.get_rng_state().clone()
        torch.manual_seed(812)
        backend = _build(kind, "service_before_admit", SHARED, service_clock_unit=SHARED, rng=None)
        actual = _inner(_native(backend))
        for name in expected_state:
            _equal(expected_state[name], actual[name])
        _equal(expected_rng, torch.get_rng_state())
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", PROVIDERS)
def test_owned_malformed_backend_refuses_before_rng_or_live_install(kind: str) -> None:
    owner = _owned(kind)
    owner.call(lambda backend, sources: _warm(backend), lineage=None)
    saved = owner.snapshot(lineage=None)
    damaged = deepcopy(saved)
    _corrupt(damaged["backend"], "moment_nan")
    if kind == "adaptive":
        damaged["backend"]["survival_history"][-1] = float("nan")
    ambient = _ambient()
    with pytest.raises(ValueError):
        owner.prepare_restore(
            damaged,
            factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
            validate_backend=lambda candidate, payload: candidate.validate_state(payload),
            lineage=None,
        )
    _equal(saved, owner.snapshot(lineage=None))
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", PROVIDERS)
def test_private_world_construction_and_owned_pressure_preserve_world1(kind: str) -> None:
    world1 = _owned(kind)
    world1.call(lambda backend, sources: _warm(backend), lineage=None)
    saved = world1.snapshot(lineage=None)
    replay = _owned(kind)
    prepared = replay.prepare_restore(
        saved,
        factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
        validate_backend=lambda candidate, payload: candidate.validate_state(payload),
        lineage=None,
    )
    replay.install(prepared, lineage=None)
    world0 = OwnedWorldBackend.construct(
        rng=_rng(kind, "world-b"),
        factory=lambda rng: _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=rng),
    )
    before0 = world0.snapshot(lineage=None)
    ambient = _ambient()

    def work(backend: Any, sources: Any) -> Any:
        # Transparent extra domain draws cover the currently deterministic backend.
        draws = (torch.rand(2), random.random(), np.random.random(), sources.numpy.random())
        receipt, trace = _traced(backend, _rows(3, 370))
        return draws, receipt, trace, _native(backend)

    expected = world1.call(work, lineage=None)
    for _ in range(4):
        world0.call(work, lineage=None)
    actual = replay.call(work, lineage=None)
    _equal(expected, actual)
    _equal(world1.snapshot(lineage=None), replay.snapshot(lineage=None))
    _learned(before0["backend"], world0.snapshot(lineage=None)["backend"])
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("unit", ("wrong-unit", None, True))
def test_constructor_unit_refusal_precedes_rng_or_model_allocation(kind: str, unit: Any) -> None:
    _make(kind)
    rng = _rng(kind)
    before_rng, ambient = rng.snapshot(), _ambient()
    with pytest.raises(ValueError):
        _build(kind, "service_before_admit", PRIVATE, service_clock_unit=unit, rng=rng)
    _equal(before_rng, rng.snapshot())
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", PROVIDERS)
def test_constructor_rng_refusal_precedes_model_allocation(kind: str) -> None:
    _make(kind)
    ambient = _ambient()
    with pytest.raises(ValueError):
        _build(kind, "service_before_admit", PRIVATE, service_clock_unit=PRIVATE, rng=object())
    _equal(ambient, _ambient())


def _current_adaptive_with_learning() -> AdaptiveIntrinsicExploration:
    """Valid current API fixture, deliberately independent of missing new APIs."""
    backend = _build("adaptive", "service_before_admit", SHARED)
    initial = deepcopy(backend.checkpoint_state())
    backend.update({"observations": _rows(3)})
    _learned(initial, backend.checkpoint_state())
    for _ in range(12):
        backend.update_on_episode_end(40.0)
    return backend


def test_current_adaptive_snapshot_history_is_not_a_live_alias() -> None:
    backend = _current_adaptive_with_learning()
    pristine = deepcopy(backend.checkpoint_state())
    snapshot = backend.checkpoint_state()
    snapshot["survival_history"][-1] = 999.0
    snapshot["survival_history"].append(888.0)
    _equal(pristine, backend.checkpoint_state())


def test_current_adaptive_restore_history_does_not_alias_payload() -> None:
    source = _current_adaptive_with_learning()
    payload = source.checkpoint_state()
    pristine = deepcopy(payload)
    destination = _build("adaptive", "service_before_admit", SHARED)
    destination.load_state(payload)
    payload["survival_history"][-1] = 777.0
    payload["survival_history"].append(666.0)
    _equal(pristine, destination.checkpoint_state())


def test_current_adaptive_late_outer_refusal_preserves_nested_learning() -> None:
    backend = _current_adaptive_with_learning()
    before = deepcopy(backend.checkpoint_state())
    donor = _build("adaptive", "service_before_admit", SHARED)
    donor.load_state(deepcopy(before))
    donor.update({"observations": _rows(3, 420)})
    candidate = donor.checkpoint_state()
    _learned(before, candidate)
    del candidate["survival_history"]
    with pytest.raises((KeyError, ValueError)):
        backend.load_state(candidate)
    _equal(before, backend.checkpoint_state())


def test_icm_nonfinite_context_refusal_is_context_boundary_only() -> None:
    backend = _build("icm", "service_before_admit", PRIVATE)
    before = backend.checkpoint_state()
    rows = _rows(3)
    rows[-1, -1] = float("nan")
    with pytest.raises(ValueError):
        _context(rows, 1)
    # This deliberately makes no claim of executing ICM's provider preflight.
    _equal(before, backend.checkpoint_state())


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("overflow", OVERFLOW)
@pytest.mark.parametrize("unit", (PRIVATE, SHARED))
def test_current_provider_fixture_preflight(kind: str, overflow: str, unit: str) -> None:
    """Positive current-interface preflight, not private-clock qualification."""
    backend = _build(kind, overflow, unit)
    state = backend.checkpoint_state()
    assert isinstance(state, dict) and state
    inner = _inner(state)
    assert isinstance(inner["optimizer"], dict)
    assert not inner["optimizer"]["state"]
    assert all(float(group["lr"]) > 0 for group in inner["optimizer"]["param_groups"])
    rows = _rows(3)
    context = _context(rows, 7)
    _equal(context.predecessor, rows)
    assert context.vector_tick == 7
    assert context.actions.tolist() == [0, 1, 2]
    assert context.active_on_entry.tolist() == [True, True, True]
    if kind == "icm":
        assert backend.policy.policy_identity == _policy(kind, overflow, unit).policy_identity
        rewards = backend.compute_transition_novelty(context, update_stats=False)
    else:
        options = _rnd(backend).service_options
        assert options is not None and options.overflow_policy == overflow
        assert options.max_pending_rows == 4 and options.max_updates_per_tick == 1
        rewards = backend.compute_intrinsic_rewards(rows, update_stats=False)
    assert rewards.shape == (3,) and bool(torch.isfinite(rewards).all())
    _equal(state, backend.checkpoint_state())
    if unit == PRIVATE:
        descriptor = WorldCuriosityDescriptor.from_policy(
            _policy(kind, overflow, unit),
            world_ids=("world-a", "world-b"),
            observation_dim=3,
            action_dim=3,
            training_seed=17,
        )
        ambient = _ambient()
        rng = WorldRNGState.create(descriptor=descriptor, world_id="world-a", cuda_devices=())
        snapshot = rng.snapshot()
        assert snapshot["schema"] == "world-curiosity-rng-v1"
        assert snapshot["world_id"] == "world-a" and len(snapshot["cuda_devices"]) == 0
        assert set(snapshot["components"]) == {"model_init", "target", "predictor", "service"}
        assert all(component["torch_cpu"].dtype == torch.uint8 for component in snapshot["components"].values())
        _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", ("rnd", "adaptive"))
@pytest.mark.parametrize("overflow", OVERFLOW)
@pytest.mark.parametrize("entrypoint", ("admit_and_service", "update"))
def test_overcapacity_shared_buffer_refuses_before_service(kind: str, overflow: str, entrypoint: str) -> None:
    backend = _make(kind, overflow=overflow, unit=SHARED)
    provider = _rnd(backend)
    provider.obs_buffer.extend(row.clone() for row in _rows(8, 500))
    before, counters, ambient = _native(backend), provider.predictor_service_counters(), _ambient()
    callbacks: list[str] = []

    def forbidden_callback(*args: Any, **kwargs: Any) -> None:
        callbacks.append("service-before-capacity-refusal")
        pytest.fail("over-capacity admission invoked learning before preflight; stopped before its possible unbounded loop")

    handles = [
        provider.fixed_network.register_forward_pre_hook(forbidden_callback),
        provider.predictor_network.register_forward_pre_hook(forbidden_callback),
        provider.optimizer.register_step_pre_hook(forbidden_callback),
    ]
    try:
        with pytest.raises(ValueError):
            if entrypoint == "admit_and_service":
                backend.admit_and_service(_rows(1, 520), vector_tick=7)
            else:
                backend.update({"observations": _rows(1, 520)})
        assert not callbacks
        assert provider.predictor_service_counters() == counters
        _equal(before, _native(backend))
        _equal(ambient, _ambient())
    finally:
        for handle in handles:
            handle.remove()


def _warm_native_validation_fixture(kind: str) -> tuple[Any, dict[str, Any]]:
    backend = _make(kind)
    _warm(backend)
    pristine = _native(backend)
    # Establish complete lawful preparation before the malformed-state witness.
    # In particular, a current ICM MappingProxy clone error is a prerequisite
    # failure here, outside every expected-refusal assertion; it is not Adam RED.
    backend.validate_state(pristine)
    _equal(pristine, _native(backend))
    moments = _inner(pristine)["optimizer"]["state"]
    assert moments and all(type(key) is int for key in moments)
    for state in moments.values():
        assert state["exp_avg"].dtype == state["exp_avg_sq"].dtype == torch.float32
    return backend, pristine


RAW_MOMENT_CASES = (
    ("exp_avg", "float64"),
    ("exp_avg", "int64"),
    ("exp_avg", "bool"),
    ("exp_avg_sq", "float64"),
    ("exp_avg_sq", "int64"),
    ("exp_avg_sq", "bool"),
    ("exp_avg", "finite_overflow"),
    ("exp_avg_sq", "negative_underflow"),
)


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("field,case", RAW_MOMENT_CASES)
def test_raw_adam_moment_dtype_refuses_before_loader_coercion(kind: str, field: str, case: str) -> None:
    backend, pristine = _warm_native_validation_fixture(kind)
    damaged = deepcopy(pristine)
    moments = list(_inner(damaged)["optimizer"]["state"].values())[-1]
    original = moments[field]
    if case == "finite_overflow":
        moments[field] = torch.full_like(original, 1e300, dtype=torch.float64)
        assert bool(torch.isfinite(moments[field]).all())
        assert bool(torch.isinf(moments[field].to(torch.float32)).all())
    elif case == "negative_underflow":
        moments[field] = torch.full_like(original, -1e-300, dtype=torch.float64)
        assert bool((moments[field] < 0).all())
        assert bool((moments[field].to(torch.float32) == 0).all())
    else:
        dtype = {"float64": torch.float64, "int64": torch.int64, "bool": torch.bool}[case]
        moments[field] = original.to(dtype)
    input_before = deepcopy(damaged)
    callbacks: list[Any] = []
    handles = _watch_forwards(backend, callbacks)
    try:
        for method in (backend.validate_state, backend.prepare_state, backend.load_state):
            _must_refuse_unchanged(backend, lambda: method(damaged))
            _equal(pristine, _native(backend))
            _equal(input_before, damaged)
            assert not callbacks
    finally:
        for handle in handles:
            handle.remove()


@pytest.mark.parametrize("kind", PROVIDERS)
@pytest.mark.parametrize("identifier,alias", ((0, False), (0, 0.0), (1, True), (1, 1.0)))
def test_native_optimizer_state_ids_refuse_bool_and_float_aliases(kind: str, identifier: int, alias: Any) -> None:
    backend, pristine = _warm_native_validation_fixture(kind)
    damaged = deepcopy(pristine)
    optimizer = _inner(damaged)["optimizer"]
    assert identifier in optimizer["state"]
    optimizer["state"] = {alias if key == identifier else key: value for key, value in optimizer["state"].items()}
    keys_before = [(type(key), key) for key in optimizer["state"]]
    assert (type(alias), alias) in keys_before
    input_before = deepcopy(damaged)
    for method in (backend.validate_state, backend.prepare_state, backend.load_state):
        _must_refuse_unchanged(backend, lambda: method(damaged))
        _equal(pristine, _native(backend))
        _equal(input_before, damaged)
        assert [(type(key), key) for key in optimizer["state"]] == keys_before
