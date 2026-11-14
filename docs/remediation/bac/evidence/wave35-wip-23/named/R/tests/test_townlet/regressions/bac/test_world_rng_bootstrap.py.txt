"""Real selected-provider witnesses for pure shared bootstrap and explicit lineage.

The controls deliberately exercise only existing APIs. Feature cases then require
the approved reserve/bootstrap/activate_under producer seams. BANK/CP publication
and ENV acceptance remain their real owners' separate integration obligations.
"""

from __future__ import annotations

import gc
import hashlib
import importlib
import json
import multiprocessing
import os
import random
import threading
import weakref
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from queue import Empty
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration.curiosity_checkpoint import attach_gradients, capture_gradients, gradient_modules, validate_native
from townlet.exploration.provider_factory import make_backend
from townlet.exploration.rng_custody import RNGOperation, process_rng_domain
from townlet.exploration.world_curiosity_state import (
    OwnedWorldBackend,
    ServiceClock,
    SharedWorldBackend,
    WorldCuriosityDescriptor,
    WorldRNGState,
)
from townlet.universe.compiler import UniverseCompiler

FAMILIES = ("none", "count_based", "rnd", "adaptive_rnd", "icm")
TRAINABLE = ("rnd", "adaptive_rnd", "icm")
QUALIFICATION_KEYS = ("BAC_QUAL_ROOT", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_MANIFEST", "BAC_QUAL_OUTPUT")


def _equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, torch.Tensor):
        return left.shape == right.shape and left.dtype == right.dtype and left.device == right.device and torch.equal(left, right)
    if isinstance(left, np.ndarray):
        return left.dtype == right.dtype and left.shape == right.shape and np.array_equal(left, right)
    if isinstance(left, Mapping):
        return left.keys() == right.keys() and all(_equal(value, right[key]) for key, value in left.items())
    if isinstance(left, (tuple, list)):
        return len(left) == len(right) and all(_equal(value, other) for value, other in zip(left, right, strict=True))
    return bool(left == right)


def _ambient() -> tuple[Any, Any, torch.Tensor]:
    return deepcopy(random.getstate()), deepcopy(np.random.get_state()), torch.get_rng_state().clone()


def _next(state: tuple[Any, Any, torch.Tensor]) -> tuple[float, float, torch.Tensor]:
    python = random.Random(0)
    python.setstate(state[0])
    numpy = np.random.RandomState(0)
    numpy.set_state(state[1])
    generator = torch.Generator(device="cpu")
    generator.set_state(state[2])
    return python.random(), float(numpy.random_sample()), torch.rand(5, generator=generator)


def _assert_ambient(state: tuple[Any, Any, torch.Tensor]) -> None:
    observed = _ambient()
    assert _equal(observed, state)
    assert _equal(_next(observed), _next(state))


def _draw() -> None:
    random.random()
    np.random.random_sample()
    torch.rand(3)


@contextmanager
def _no_rng_or_native_effects() -> Iterator[None]:
    """Observe actual calls only at cuts that must reject before any such work."""
    observed: list[str] = []
    observing_thread = threading.get_ident()

    def observe(original: Callable[..., Any], label: str) -> Callable[..., Any]:
        def invoke(*args: Any, **kwargs: Any) -> Any:
            if threading.get_ident() == observing_thread:
                observed.append(label)
            return original(*args, **kwargs)

        return invoke

    targets = (
        (random, ("getstate", "setstate", "random", "seed", "getrandbits", "uniform", "randrange", "randint")),
        (np.random, ("get_state", "set_state", "random", "random_sample", "rand", "randn", "randint", "seed")),
        (torch, ("get_rng_state", "set_rng_state", "rand", "randn", "randint", "manual_seed", "seed")),
        (torch.nn.Linear, ("__init__",)),
        (torch.optim.Adam, ("__init__",)),
    )
    with pytest.MonkeyPatch.context() as patch:
        for owner, names in targets:
            for name in names:
                patch.setattr(owner, name, observe(getattr(owner, name), f"{owner.__name__}.{name}"))
        try:
            yield
        finally:
            assert observed == [], f"forbidden effects before admission/refusal: {observed}"


@pytest.fixture(scope="module")
def compiled() -> Any:
    return UniverseCompiler().compile(
        experiment_dir=Path(__file__).resolve().parents[4] / "configs/test/token_set_smoke",
        primary_level="L0_test",
        use_cache=False,
    )


def _selection(compiled: Any, family: str, scope: str) -> tuple[Any, WorldCuriosityDescriptor]:
    level = compiled.get_level("L0_test")
    drive = level.drive.intrinsic.model_dump()
    drive["strategy"] = family
    training = deepcopy(level.training.model_dump())
    training["replay_buffer"]["batch_size"] = 2
    training["intrinsic"]["rnd"].update(feature_dim=4, learning_rate=0.001)
    training["intrinsic"].update(initial_weight=0.4, survival_window=10, min_survival_fraction=0.01)
    training["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    training["training_loop"]["max_steps_per_episode"] = 20
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
            "provider_parameter_source": "training",
            "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
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
    policy = resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), options)
    descriptor = WorldCuriosityDescriptor.from_policy(
        policy,
        world_ids=("target-z", "target-a"),
        observation_dim=level.token_spec.total_dims,
        action_dim=level.action_metadata.total_actions,
        training_seed=731,
    )
    return policy, descriptor


def _factory(policy: Any, descriptor: WorldCuriosityDescriptor, rng: WorldRNGState | None) -> Any:
    return make_backend(
        policy,
        world_id=None if rng is None else "target-a",
        obs_dim=descriptor.observation_dim,
        action_dim=descriptor.action_dim,
        device=torch.device("cpu"),
        rng=rng,
        descriptor=None if rng is None else descriptor,
    )


def _restore_factory(policy: Any, descriptor: WorldCuriosityDescriptor, payload: dict[str, Any]) -> Callable[[], Any]:
    def construct() -> Any:
        candidate = _factory(policy, descriptor, None)
        return candidate.with_restore_configuration(payload) if policy.strategy in TRAINABLE else candidate

    return construct


def _validator(policy: Any, descriptor: WorldCuriosityDescriptor) -> Callable[[Any, Any], None]:
    def validate(candidate: Any, payload: Any) -> None:
        validate_native(candidate, payload, policy=policy, descriptor=descriptor)

    return validate


def _mixed_gradients(provider: Any, family: str) -> dict[str, Any]:
    index = 0
    for module in gradient_modules(provider, family).values():
        for parameter in module.parameters():
            parameter.grad = None if index % 3 == 0 else torch.full_like(parameter, 0.0 if index % 3 == 1 else 0.125)
            index += 1
    return capture_gradients(provider, family)


def _pairing(provider: Any, family: str) -> tuple[bool, dict[str, Any]]:
    modules = gradient_modules(provider, family)
    if not modules:
        return True, capture_gradients(provider, family)
    optimizer = provider.rnd.optimizer if family == "adaptive_rnd" else provider.optimizer
    parameters = [parameter for module in modules.values() for parameter in module.parameters()]
    actual = [parameter for group in optimizer.param_groups for parameter in group["params"]]
    return len(actual) == len(parameters) and {id(value) for value in actual} == {id(value) for value in parameters}, capture_gradients(
        provider, family
    )


def _service(provider: Any, family: str, descriptor: WorldCuriosityDescriptor) -> dict[str, Any]:
    native = provider.checkpoint_state()
    selected = native["rnd_state"] if family == "adaptive_rnd" else native
    previous = selected["service_position"] if family == "icm" else selected.get("predictor_service", {}).get("service_position")
    unit = descriptor.service_clock_unit
    position = (0 if previous is None else previous) + (3 if unit == "world_eligible_admission" else 1)
    rows = torch.arange(3 * descriptor.observation_dim, dtype=torch.float32).reshape(3, descriptor.observation_dim) / 113.0
    context = IntrinsicTransitionContext(
        predecessor=rows,
        actions=torch.arange(3, dtype=torch.int64) % descriptor.action_dim,
        successor=rows + 0.125,
        active_on_entry=torch.ones(3, dtype=torch.bool),
        vector_tick=position,
    )
    if family == "icm":
        novelty = provider.compute_transition_novelty(context, update_stats=True)
        receipt = provider.admit_and_service_at(context, clock=ServiceClock(unit, position))
    elif family == "count_based":
        novelty = provider.compute_intrinsic_rewards(context.successor, update_stats=True)
        receipt = provider.admit_and_service(context)
    else:
        novelty = provider.compute_intrinsic_rewards(rows, update_stats=True)
        receipt = None if family == "none" else provider.admit_and_service_at(rows, clock=ServiceClock(unit, position))
    assert novelty.shape == (3,) and torch.isfinite(novelty).all()
    if family == "none":
        assert torch.count_nonzero(novelty) == 0 and receipt is None
    if family in TRAINABLE:
        assert receipt.optimizer_updates >= 1
    return provider.checkpoint_state()


def _source(compiled: Any, family: str) -> tuple[Any, WorldCuriosityDescriptor, SharedWorldBackend, dict[str, Any], dict[str, Any]]:
    policy, descriptor = _selection(compiled, family, "shared")
    owner = SharedWorldBackend.construct(factory=lambda: _factory(policy, descriptor, None), cuda_devices=())
    owner.call(lambda provider: _service(provider, family, descriptor), lineage=None)
    gradients = owner.call(lambda provider: _mixed_gradients(provider, family), lineage=None)
    return policy, descriptor, owner, owner.snapshot(lineage=None), gradients


def _install(
    reservation: SharedWorldBackend,
    policy: Any,
    descriptor: WorldCuriosityDescriptor,
    payload: dict[str, Any],
    gradients: dict[str, Any],
    lineage: RNGOperation,
) -> None:
    handle = reservation.prepare_restore(
        payload,
        factory=_restore_factory(policy, descriptor, payload["backend"]),
        validate_backend=_validator(policy, descriptor),
        lineage=lineage,
    )
    reservation.validate_prepared(handle, lineage=lineage)
    reservation.install(handle, lineage=lineage)
    reservation.call(lambda provider: attach_gradients(provider, gradients, policy.strategy), lineage=lineage)


@pytest.mark.parametrize("family", FAMILIES)
def test_control_real_compiled_selected_factory_native_roundtrip(compiled: Any, family: str) -> None:
    policy, descriptor, owner, payload, gradients = _source(compiled, family)
    level = compiled.get_level("L0_test")
    assert descriptor.observation_dim == level.token_spec.total_dims > 0
    assert descriptor.action_dim == level.action_metadata.total_actions > 0
    assert policy.strategy == family
    candidate = _restore_factory(policy, descriptor, payload["backend"])()
    before = candidate.checkpoint_state()
    transported = deepcopy(payload["backend"])
    assert validate_native(candidate, transported, policy=policy, descriptor=descriptor) is None
    assert _equal(candidate.checkpoint_state(), before)
    assert _equal(transported, payload["backend"])
    candidate.load_state(transported)
    assert _equal(candidate.checkpoint_state(), payload["backend"])
    attach_gradients(candidate, gradients, family)
    paired, observed = _pairing(candidate, family)
    assert paired and _equal(observed, gradients)
    assert _equal(owner.snapshot(lineage=None)["backend"], payload["backend"])


@pytest.mark.parametrize("family", FAMILIES)
def test_control_real_private_factory_uses_actual_candidate_rng(compiled: Any, family: str) -> None:
    policy, descriptor = _selection(compiled, family, "per_world")
    rng = WorldRNGState.create(descriptor=descriptor, world_id="target-a", cuda_devices=())
    before = _ambient()
    owner = OwnedWorldBackend.construct(rng=rng, factory=lambda candidate_rng: _factory(policy, descriptor, candidate_rng))
    state = owner.snapshot(lineage=None)
    assert state["healthy"] is True
    assert state["rng"]["world_id"] == "target-a"
    assert state["rng"]["components"]["model_init"]["seed"] == descriptor.seed_for("target-a", "model_init")
    assert owner.call(lambda provider, sources: _pairing(provider, family)[0], lineage=None)
    _assert_ambient(before)


@pytest.mark.parametrize("family", FAMILIES)
def test_control_genuine_native_learning_and_next_service(compiled: Any, family: str) -> None:
    policy, descriptor, original, payload, _ = _source(compiled, family)
    candidate = _restore_factory(policy, descriptor, payload["backend"])()
    validate_native(candidate, payload["backend"], policy=policy, descriptor=descriptor)
    candidate.load_state(payload["backend"])
    expected = original.call(lambda provider: _service(provider, family, descriptor), lineage=None)
    actual = _service(candidate, family, descriptor)
    assert _equal(actual, expected)
    if family in TRAINABLE:
        native = actual["rnd_state"] if family == "adaptive_rnd" else actual
        assert native["optimizer"]["state"]


@pytest.mark.parametrize("family", TRAINABLE)
def test_control_shared_constructor_retains_real_torch_advancement(compiled: Any, family: str) -> None:
    policy, descriptor = _selection(compiled, family, "shared")
    before = _ambient()
    owner = SharedWorldBackend.construct(factory=lambda: _factory(policy, descriptor, None), cuda_devices=())
    assert owner.snapshot(lineage=None)["healthy"] is True
    assert not torch.equal(_ambient()[2], before[2])
    assert _equal(_ambient()[:2], before[:2])


@pytest.mark.parametrize("family", FAMILIES)
def test_bootstrap_real_native_roundtrip_final_parameters_and_ambient(compiled: Any, family: str) -> None:
    policy, descriptor, original, payload, gradients = _source(compiled, family)
    before = _ambient()
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    with reservation.bootstrap(lineage=None) as lineage:
        assert type(lineage) is RNGOperation
        _draw()
        _install(reservation, policy, descriptor, payload, gradients, lineage)
        paired, actual_gradients = reservation.call(lambda provider: _pairing(provider, family), lineage=lineage)
        assert paired and _equal(actual_gradients, gradients)
        assert _equal(reservation.snapshot(lineage=lineage)["backend"], payload["backend"])
    _assert_ambient(before)
    paired, actual_gradients = reservation.call(lambda provider: _pairing(provider, family), lineage=None)
    assert paired and _equal(actual_gradients, gradients)
    assert _equal(reservation.snapshot(lineage=None)["backend"], payload["backend"])
    assert _equal(original.snapshot(lineage=None), payload)
    with pytest.raises((RuntimeError, ValueError)):
        with reservation.bootstrap(lineage=None):
            pytest.fail("a published reservation reentered bootstrap")


@pytest.mark.parametrize("family", FAMILIES)
def test_bootstrap_restores_actual_next_service_and_learning(compiled: Any, family: str) -> None:
    policy, descriptor, original, payload, gradients = _source(compiled, family)
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    with reservation.bootstrap(lineage=None) as lineage:
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    _assert_ambient(before)
    expected = original.call(lambda provider: _service(provider, family, descriptor), lineage=None)
    actual = reservation.call(lambda provider: _service(provider, family, descriptor), lineage=None)
    assert _equal(actual, expected)


@pytest.mark.parametrize("family", FAMILIES)
def test_bootstrap_discards_actual_factory_validator_and_attachment_draws(compiled: Any, family: str) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, family)
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    real_factory = _restore_factory(policy, descriptor, payload["backend"])
    real_validator = _validator(policy, descriptor)
    stages: list[str] = []
    before = _ambient()

    def factory() -> Any:
        candidate = real_factory()
        _draw()
        stages.append("factory")
        return candidate

    def validator(candidate: Any, saved: Any) -> None:
        real_validator(candidate, saved)
        _draw()
        stages.append("validator")

    def attachment(candidate: Any) -> None:
        attach_gradients(candidate, gradients, family)
        _draw()
        stages.append("attachment")

    with reservation.bootstrap(lineage=None) as lineage:
        handle = reservation.prepare_restore(payload, factory=factory, validate_backend=validator, lineage=lineage)
        reservation.install(handle, lineage=lineage)
        reservation.call(attachment, lineage=lineage)
    assert stages == ["factory", "validator", "attachment"]
    _assert_ambient(before)
    assert _equal(reservation.snapshot(lineage=None)["backend"], payload["backend"])
    assert _equal(reservation.call(lambda provider: capture_gradients(provider, family), lineage=None), gradients)


@pytest.mark.parametrize("family", TRAINABLE)
def test_bootstrap_preserves_supported_saved_optimizer_configuration(compiled: Any, family: str) -> None:
    policy, descriptor, original, _, _ = _source(compiled, family)

    def configure(provider: Any) -> None:
        if family == "icm":
            provider.optimizer.param_groups[0]["lr"] = 0.0007
        else:
            native = provider.rnd if family == "adaptive_rnd" else provider
            parameters = list(native.predictor_network.parameters())
            native.optimizer = torch.optim.Adam(
                [
                    {"params": list(reversed(parameters[::2])), "lr": 0.0007, "amsgrad": True},
                    {"params": [], "lr": 0.0009},
                    {"params": list(reversed(parameters[1::2])), "lr": 0.0013},
                ]
            )
        _service(provider, family, descriptor)

    original.call(configure, lineage=None)
    gradients = original.call(lambda provider: _mixed_gradients(provider, family), lineage=None)
    payload = original.snapshot(lineage=None)
    native = payload["backend"]["rnd_state"] if family == "adaptive_rnd" else payload["backend"]
    if family != "icm":
        assert len(native["adam_restore_recipe"]["groups"]) == 3
        assert native["adam_restore_recipe"]["groups"][1]["parameter_names"] == []
        assert native["predictor_service"]["optimizer_step_offset"] < 0
    else:
        assert native["optimizer"]["param_groups"][0]["lr"] == 0.0007
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    with reservation.bootstrap(lineage=None) as lineage:
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    _assert_ambient(before)
    assert _equal(reservation.snapshot(lineage=None)["backend"], payload["backend"])
    assert _equal(
        reservation.call(lambda provider: _service(provider, family, descriptor), lineage=None),
        original.call(lambda provider: _service(provider, family, descriptor), lineage=None),
    )


def test_empty_reservation_refuses_ordinary_work_without_native_effects(compiled: Any) -> None:
    policy, descriptor, _, payload, _ = _source(compiled, "rnd")
    before = _ambient()
    with _no_rng_or_native_effects():
        reservation = SharedWorldBackend.reserve(cuda_devices=())
    effects: list[str] = []

    def callback(provider: Any) -> None:
        effects.append("call")

    def factory() -> Any:
        effects.append("factory")
        return _factory(policy, descriptor, None)

    operations = (
        lambda: reservation.call(callback, lineage=None),
        lambda: reservation.snapshot(lineage=None),
        lambda: reservation.prepare_restore(payload, factory=factory, validate_backend=_validator(policy, descriptor), lineage=None),
        lambda: reservation.prepare_learning_reset(factory=factory, prepare_native=lambda candidate, fresh: None, lineage=None),
        lambda: reservation.install(object(), lineage=None),
        lambda: reservation.validate_prepared(object(), lineage=None),
    )
    for operation in operations:
        with _no_rng_or_native_effects():
            with pytest.raises((RuntimeError, ValueError)):
                operation()
        assert effects == []
        _assert_ambient(before)
    with pytest.raises((RuntimeError, ValueError)):
        with reservation.bootstrap(lineage=None):
            _draw()
    _assert_ambient(before)


@pytest.mark.parametrize("refusal", ("factory", "validator"))
def test_early_refusal_discards_draws_and_all_handles_then_corrected_retry(compiled: Any, refusal: str) -> None:
    policy, descriptor, original, payload, gradients = _source(compiled, "rnd")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    handles: list[Any] = []

    def fail_factory() -> Any:
        _draw()
        raise ValueError("early selected factory refusal")

    def fail_validator(candidate: Any, saved: Any) -> None:
        _draw()
        raise ValueError("early pure validator refusal")

    with pytest.raises(ValueError, match="early"):
        with reservation.bootstrap(lineage=None) as lineage:
            handles.append(
                reservation.prepare_restore(
                    payload,
                    factory=_restore_factory(policy, descriptor, payload["backend"]),
                    validate_backend=_validator(policy, descriptor),
                    lineage=lineage,
                )
            )
            reservation.prepare_restore(
                payload,
                factory=fail_factory if refusal == "factory" else _restore_factory(policy, descriptor, payload["backend"]),
                validate_backend=fail_validator if refusal == "validator" else _validator(policy, descriptor),
                lineage=lineage,
            )
    _assert_ambient(before)
    assert process_rng_domain().status()[2] is False
    with reservation.bootstrap(lineage=None) as lineage:
        with pytest.raises((RuntimeError, ValueError)):
            reservation.install(handles[0], lineage=lineage)
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    _assert_ambient(before)
    assert _equal(original.snapshot(lineage=None), payload)


def test_installed_attachment_failure_quarantines_only_offside_reservation(compiled: Any) -> None:
    policy, descriptor, original, payload, gradients = _source(compiled, "rnd")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()

    def attachment(provider: Any) -> None:
        attach_gradients(provider, gradients, "rnd")
        _draw()
        raise ValueError("late final attachment refusal")

    with pytest.raises(ValueError, match="late final attachment"):
        with reservation.bootstrap(lineage=None) as lineage:
            handle = reservation.prepare_restore(
                payload,
                factory=_restore_factory(policy, descriptor, payload["backend"]),
                validate_backend=_validator(policy, descriptor),
                lineage=lineage,
            )
            reservation.install(handle, lineage=lineage)
            reservation.call(attachment, lineage=lineage)
    _assert_ambient(before)
    assert process_rng_domain().status()[2] is False
    assert _equal(original.snapshot(lineage=None), payload)
    with pytest.raises((RuntimeError, ValueError)):
        reservation.call(lambda provider: provider.checkpoint_state(), lineage=None)
    with pytest.raises((RuntimeError, ValueError)):
        with reservation.bootstrap(lineage=None):
            pytest.fail("installed failure was publicly healed")


def test_bootstrap_handle_destination_consumption_and_same_owner_reentry(compiled: Any) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, "rnd")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    foreign = SharedWorldBackend.reserve(cuda_devices=())
    with reservation.bootstrap(lineage=None) as lineage:
        handle = reservation.prepare_restore(
            payload,
            factory=_restore_factory(policy, descriptor, payload["backend"]),
            validate_backend=_validator(policy, descriptor),
            lineage=lineage,
        )
        with pytest.raises((RuntimeError, ValueError)):
            foreign.install(handle, lineage=lineage)
        handle = reservation.prepare_restore(
            payload,
            factory=_restore_factory(policy, descriptor, payload["backend"]),
            validate_backend=_validator(policy, descriptor),
            lineage=lineage,
        )
        reservation.install(handle, lineage=lineage)
        with pytest.raises((RuntimeError, ValueError)):
            reservation.install(handle, lineage=lineage)

        def nested(provider: Any) -> None:
            with pytest.raises(RuntimeError):
                reservation.snapshot(lineage=lineage)
            attach_gradients(provider, gradients, "rnd")

        reservation.call(nested, lineage=lineage)
    assert reservation.call(lambda provider: _pairing(provider, "rnd")[0], lineage=None)


def test_bootstrap_inner_ordinary_work_invalidates_earlier_handle(compiled: Any) -> None:
    policy, descriptor, peer, payload, gradients = _source(compiled, "rnd")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    with reservation.bootstrap(lineage=None) as lineage:
        stale = reservation.prepare_restore(
            payload,
            factory=_restore_factory(policy, descriptor, payload["backend"]),
            validate_backend=_validator(policy, descriptor),
            lineage=lineage,
        )
        peer.call(lambda provider: provider.checkpoint_state(), lineage=lineage)
        with pytest.raises(ValueError):
            reservation.install(stale, lineage=lineage)
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    assert reservation.snapshot(lineage=None)["healthy"] is True


def test_bootstrap_registration_requires_idle_and_active_owner_is_pinned(compiled: Any) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, "none")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    reference = weakref.ref(reservation)
    context = reservation.bootstrap(lineage=None)
    with context as lineage:
        with _no_rng_or_native_effects():
            with pytest.raises(RuntimeError):
                SharedWorldBackend.reserve(cuda_devices=())
        with pytest.raises(RuntimeError):
            with reservation.bootstrap(lineage=lineage):
                pytest.fail("aggregate bootstrap reentered itself")
        _install(reservation, policy, descriptor, payload, gradients, lineage)
        del reservation
        gc.collect()
        assert reference() is not None
    del context
    gc.collect()
    assert reference() is None


def test_held_bootstrap_excludes_peer_through_capture_and_cleanup(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    policy, descriptor, peer, payload, gradients = _source(compiled, "rnd")
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    capture = threading.Event()
    release_capture = threading.Event()
    body_done = threading.Event()
    cleanup = threading.Event()
    release_cleanup = threading.Event()
    attempted = {phase: threading.Event() for phase in ("capture", "cleanup")}
    entered = {phase: threading.Event() for phase in ("capture", "cleanup")}
    acquired_immediately: dict[str, bool] = {}
    failures: list[BaseException] = []
    real_get = torch.get_rng_state
    real_set = torch.set_rng_state
    domain = process_rng_domain()
    real_lock = domain._lock

    class ObservedAdmission:
        """Delegate custody to the real RLock and report its actual acquire result."""

        def __enter__(self) -> ObservedAdmission:
            name = threading.current_thread().name
            phase = name.removeprefix("bootstrap-peer-")
            if phase in attempted and not attempted[phase].is_set():
                acquired = real_lock.acquire(blocking=False)
                if acquired:
                    real_lock.release()
                acquired_immediately[phase] = acquired
                attempted[phase].set()
            real_lock.acquire()
            return self

        def __exit__(self, error_type: Any, error: Any, traceback: Any) -> None:
            real_lock.release()

    def guarded_get() -> torch.Tensor:
        if threading.current_thread().name == "bootstrap-capture" and not capture.is_set():
            capture.set()
            assert release_capture.wait(10)
        return real_get()

    def guarded_set(value: torch.Tensor) -> None:
        if threading.current_thread().name == "bootstrap-capture" and body_done.is_set() and not cleanup.is_set():
            cleanup.set()
            assert release_cleanup.wait(10)
        real_set(value)

    monkeypatch.setattr(torch, "get_rng_state", guarded_get)
    monkeypatch.setattr(torch, "set_rng_state", guarded_set)
    monkeypatch.setattr(domain, "_lock", ObservedAdmission())

    def prepare() -> None:
        try:
            with reservation.bootstrap(lineage=None) as lineage:
                _install(reservation, policy, descriptor, payload, gradients, lineage)
                body_done.set()
        except BaseException as error:
            failures.append(error)

    def peer_operation(phase: str) -> None:
        try:
            peer.call(lambda provider: entered[phase].set(), lineage=None)
        except BaseException as error:
            failures.append(error)

    producer = threading.Thread(target=prepare, name="bootstrap-capture")
    consumers = {
        phase: threading.Thread(target=peer_operation, args=(phase,), name=f"bootstrap-peer-{phase}") for phase in ("capture", "cleanup")
    }
    producer.start()
    try:
        assert capture.wait(10)
        consumers["capture"].start()
        assert attempted["capture"].wait(5)
        assert acquired_immediately["capture"] is False and not entered["capture"].is_set()
        release_capture.set()
        assert cleanup.wait(10)
        consumers["cleanup"].start()
        assert attempted["cleanup"].wait(5)
        assert acquired_immediately["cleanup"] is False
        assert not any(event.is_set() for event in entered.values())
        release_cleanup.set()
    finally:
        release_capture.set()
        release_cleanup.set()
        producer.join(15)
        for consumer in consumers.values():
            if consumer.ident is not None:
                consumer.join(15)
    assert not producer.is_alive() and not any(consumer.is_alive() for consumer in consumers.values())
    assert failures == [] and all(event.is_set() for event in entered.values())
    _assert_ambient(before)


def test_explicit_lineage_archive_validation_uses_target_seed_and_source_policy(compiled: Any) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, "rnd")
    target_policy, target_descriptor = _selection(compiled, "icm", "per_world")
    assert target_policy.strategy != policy.strategy
    assert target_descriptor.scope != descriptor.scope
    world_id = sorted(target_descriptor.world_ids)[0]
    validation_rng = WorldRNGState.create(descriptor=target_descriptor, world_id=world_id, cuda_devices=())
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    expected_generator = torch.Generator(device="cpu").manual_seed(target_descriptor.seed_for(world_id, "model_init"))
    expected_draw = torch.rand(5, generator=expected_generator)
    with reservation.bootstrap(lineage=None) as lineage:
        with validation_rng.activate_under("model_init", lineage=lineage):
            assert torch.equal(torch.rand(5), expected_draw)
            candidate = _restore_factory(policy, descriptor, payload["backend"])()
            assert validate_native(candidate, payload["backend"], policy=policy, descriptor=descriptor) is None
            candidate.load_state(payload["backend"])
            assert _equal(candidate.checkpoint_state(), payload["backend"])
            attach_gradients(candidate, gradients, "rnd")
            assert _equal(capture_gradients(candidate, "rnd"), gradients)
            with _no_rng_or_native_effects():
                with pytest.raises(RuntimeError):
                    reservation.snapshot(lineage=lineage)
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    _assert_ambient(before)


def test_activate_under_rejects_wrong_expired_foreign_thread_and_foreign_frame(compiled: Any) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, "none")
    _, private_descriptor = _selection(compiled, "rnd", "per_world")
    rng = WorldRNGState.create(descriptor=private_descriptor, world_id="target-a", cuda_devices=())
    other = WorldRNGState.create(descriptor=private_descriptor, world_id="target-z", cuda_devices=())
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    before = _ambient()
    generator = torch.Generator(device="cpu").manual_seed(private_descriptor.seed_for("target-a", "model_init"))
    expected_a = torch.rand(3, generator=generator)
    expected_next_a = torch.rand(3, generator=generator)
    for invalid_lineage in (None, object()):
        with _no_rng_or_native_effects():
            with pytest.raises((TypeError, ValueError)):
                with rng.activate_under("model_init", lineage=invalid_lineage):
                    pytest.fail("absent/fabricated lineage activated")
    with reservation.bootstrap(lineage=None) as lineage:
        with _no_rng_or_native_effects():
            with pytest.raises(ValueError):
                with rng.activate_under("wrong", lineage=lineage):
                    pytest.fail("unknown named stream activated")
        with rng.activate_under("model_init", lineage=lineage) as sources:
            assert torch.equal(torch.rand(3), expected_a)
            with rng.activate_under("model_init", lineage=lineage) as same:
                assert same is sources
            with rng.activate_under("service", lineage=lineage):
                torch.rand(4)
                with rng.activate_under("model_init", lineage=lineage) as resumed:
                    assert resumed is sources
                    assert torch.equal(torch.rand(3), expected_next_a)
            with _no_rng_or_native_effects():
                with pytest.raises(RuntimeError):
                    with other.activate_under("model_init", lineage=lineage):
                        pytest.fail("foreign private frame activated")
            with _no_rng_or_native_effects():
                with pytest.raises(ValueError):
                    rng.validate_binding(descriptor=private_descriptor, world_id="target-z", cuda_devices=())
        failures: list[BaseException] = []
        started = threading.Event()

        def foreign_thread() -> None:
            started.set()
            try:
                with _no_rng_or_native_effects():
                    with rng.activate_under("model_init", lineage=lineage):
                        failures.append(AssertionError("foreign thread activated"))
            except BaseException as error:
                failures.append(error)

        thread = threading.Thread(target=foreign_thread)
        thread.start()
        assert started.wait(5)
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    thread.join(10)
    assert not thread.is_alive()
    assert len(failures) == 1 and isinstance(failures[0], (RuntimeError, ValueError))
    with _no_rng_or_native_effects():
        with pytest.raises(ValueError):
            with rng.activate_under("model_init", lineage=lineage):
                pytest.fail("expired lineage activated")
    _assert_ambient(before)


def test_cpu_empty_inventory_performs_no_cuda_query(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    policy, descriptor, _, payload, gradients = _source(compiled, "none")

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("CPU bootstrap queried CUDA")

    for name in ("is_available", "is_initialized", "device_count", "synchronize", "get_rng_state", "set_rng_state"):
        monkeypatch.setattr(torch.cuda, name, forbidden)
    before = _ambient()
    with _no_rng_or_native_effects():
        reservation = SharedWorldBackend.reserve(cuda_devices=())
    with reservation.bootstrap(lineage=None) as lineage:
        _install(reservation, policy, descriptor, payload, gradients, lineage)
    assert reservation.snapshot(lineage=None)["healthy"] is True
    _assert_ambient(before)


@pytest.mark.parametrize("devices", (None, [], (True,), (-1,), (1, 0), (0, 0)))
def test_reservation_authenticates_exact_device_inventory_without_draws(devices: Any) -> None:
    before = _ambient()
    with _no_rng_or_native_effects():
        with pytest.raises((TypeError, ValueError)):
            SharedWorldBackend.reserve(cuda_devices=devices)
    _assert_ambient(before)


def _qualification_active() -> bool:
    present = tuple(key in os.environ for key in QUALIFICATION_KEYS)
    assert not any(present) or all(present), "partial qualification environment must refuse"
    return all(present)


def _child_identity(role: str) -> bool:
    qualified = _qualification_active()
    if not qualified:
        return False
    import bac_source_identity

    bac_source_identity.pytest_configure(SimpleNamespace(workerinput={"workerid": role}))
    output = Path(os.environ["BAC_QUAL_OUTPUT"])
    emitted = output / f"identity-{role}.json"
    destination = output / f"spawn-identity-{role}.json"
    assert emitted.is_file() and not destination.exists()
    record = json.loads(emitted.read_text())
    record.update(
        pid=os.getpid(),
        manifest_sha256=hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
        debug=__debug__,
        interop_threads=torch.get_num_interop_threads(),
        imports={
            name: str(Path(importlib.import_module(f"townlet.exploration.{name}").__file__).resolve())
            for name in ("world_curiosity_state", "rng_custody", "rnd")
        },
    )
    assert record["debug"] is True
    assert torch.get_num_threads() == 1 and record["interop_threads"] == 5
    emitted.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
    emitted.rename(destination)
    return True


def _exception_messages(error: BaseException) -> list[str]:
    if isinstance(error, BaseExceptionGroup):
        return [message for child in error.exceptions for message in _exception_messages(child)]
    return [str(error)]


def _poison_child(queue: Any, kind: str) -> None:
    role = f"bootstrap_poison_{kind}"
    qualified = _child_identity(role)
    compiled = UniverseCompiler().compile(
        experiment_dir=Path(__file__).resolve().parents[4] / "configs/test/token_set_smoke",
        primary_level="L0_test",
        use_cache=False,
    )
    policy, descriptor, original, payload, gradients = _source(compiled, "none")
    _, private_descriptor = _selection(compiled, "rnd", "per_world")
    validation_rng = WorldRNGState.create(descriptor=private_descriptor, world_id="target-a", cuda_devices=())
    reservation = SharedWorldBackend.reserve(cuda_devices=())
    raw_original: list[Any] = []
    original.call(lambda provider: raw_original.append(provider), lineage=None)
    domain = process_rng_domain()
    patch = pytest.MonkeyPatch()
    real_torch_set = torch.set_rng_state
    real_python_set = random.setstate
    real_complete = domain._complete
    setter_calls = 0

    def broken_python(value: Any) -> None:
        real_python_set(value)
        raise RuntimeError("partial private setter failure")

    def broken_torch(value: torch.Tensor) -> None:
        nonlocal setter_calls
        setter_calls += 1
        real_torch_set(value)
        if kind == "cleanup" or setter_calls > 1:
            raise RuntimeError("ambient cleanup setter failure")

    def broken_complete(devices: tuple[int, ...]) -> None:
        real_complete(devices)
        raise RuntimeError("declared device completion failure")

    try:
        try:
            with reservation.bootstrap(lineage=None) as lineage:
                _install(reservation, policy, descriptor, payload, gradients, lineage)
                if kind == "setter":
                    patch.setattr(torch, "set_rng_state", broken_torch)
                    patch.setattr(random, "setstate", broken_python)
                    with validation_rng.activate_under("model_init", lineage=lineage):
                        raise AssertionError("partial setter unexpectedly entered body")
                elif kind == "cleanup":
                    patch.setattr(torch, "set_rng_state", broken_torch)
                    _draw()
                    raise ValueError("primary bootstrap body failure")
                else:
                    assert kind == "completion"
                    patch.setattr(domain, "_complete", broken_complete)
        except BaseException as error:
            messages = _exception_messages(error)
            if kind == "setter":
                assert any("partial private setter" in message for message in messages)
                assert any("ambient cleanup setter" in message for message in messages)
            elif kind == "cleanup":
                assert any("primary bootstrap body" in message for message in messages)
                assert any("ambient cleanup setter" in message for message in messages)
            else:
                assert any("declared device completion" in message for message in messages)
        else:
            raise AssertionError("uncertain bootstrap cleanup/completion returned success")
    finally:
        patch.undo()
    assert domain.status()[2] is True
    assert _equal(raw_original[0].checkpoint_state(), payload["backend"])
    for operation in (
        lambda: original.snapshot(lineage=None),
        lambda: reservation.snapshot(lineage=None),
        lambda: validation_rng.snapshot(),
        lambda: SharedWorldBackend.reserve(cuda_devices=()),
    ):
        try:
            operation()
        except RuntimeError as error:
            assert "poison" in str(error).lower()
        else:
            raise AssertionError("participating operation resumed after common-domain poison")
    queue.put((f"bootstrap poison {kind} fail closed", os.getpid(), qualified))


@pytest.mark.parametrize("kind", ("setter", "cleanup", "completion"))
def test_fresh_child_bootstrap_poison_fails_common_domain_closed(kind: str) -> None:
    qualified = _qualification_active()
    role = f"bootstrap_poison_{kind}"
    expected_message = f"bootstrap poison {kind} fail closed"
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_poison_child, args=(queue, kind), name=role)
    before = _ambient()
    process.start()
    try:
        process.join(90)
        assert not process.is_alive(), f"{role} child timed out"
        assert process.exitcode == 0
        try:
            message, queued_pid, child_qualified = queue.get(timeout=5)
        except Empty:
            pytest.fail(f"{role} child emitted no successful poison receipt")
        assert message == expected_message and queued_pid == process.pid
        assert child_qualified is qualified
        if qualified:
            destination = Path(os.environ["BAC_QUAL_OUTPUT"]) / f"spawn-observation-{role}.json"
            record = {
                "process_pid": process.pid,
                "queued_pid": queued_pid,
                "exitcode": process.exitcode,
                "qualified": child_qualified,
                "message": message,
                "manifest_sha256": hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
            }
            with destination.open("x") as stream:
                stream.write(json.dumps(record, sort_keys=True, indent=2) + "\n")
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        assert not process.is_alive()
        queue.close()
        queue.join_thread()
        process.close()
    assert process_rng_domain().status()[2] is False
    _assert_ambient(before)
