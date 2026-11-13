"""Atomic native/gradient/private-RNG capture through the real managed owner.

The genuine compiled-provider supplier is reused without copying its source.
These are producer-contract witnesses, not BANK or full-parent qualification.
"""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import random
import threading
from collections.abc import Iterator, Mapping
from copy import deepcopy
from pathlib import Path
from queue import Empty
from typing import Any

import numpy as np
import pytest
import test_world_rng_bootstrap as bootstrap
import torch

from townlet.exploration.curiosity_checkpoint import capture_gradients, gradient_modules
from townlet.exploration.rng_custody import RNGOperation, process_rng_domain
from townlet.exploration.world_curiosity_state import OwnedWorldBackend, SharedWorldBackend, WorldRNGState

# Expose the supplier's actual fixture; do not compile a replacement universe.
compiled = bootstrap.compiled


def _private(compiled: Any, family: str) -> tuple[Any, Any, OwnedWorldBackend, WorldRNGState]:
    policy, descriptor = bootstrap._selection(compiled, family, "per_world")
    initial = WorldRNGState.create(descriptor=descriptor, world_id="target-a", cuda_devices=())
    actual: list[WorldRNGState] = []

    def factory(rng: WorldRNGState) -> Any:
        actual.append(rng)
        return bootstrap._factory(policy, descriptor, rng)

    owner = OwnedWorldBackend.construct(rng=initial, factory=factory)
    assert len(actual) == 1
    return policy, descriptor, owner, actual[0]


def _parameters(provider: Any, family: str) -> tuple[torch.nn.Parameter, ...]:
    return tuple(parameter for module in gradient_modules(provider, family).values() for parameter in module.parameters())


def _raw(owner: OwnedWorldBackend) -> Any:
    retained: list[Any] = []
    owner.call(lambda backend, sources: retained.append(backend), lineage=None)
    assert len(retained) == 1
    return retained[0]


def _tensors(value: Any) -> Iterator[torch.Tensor]:
    if isinstance(value, torch.Tensor):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _tensors(item)
    elif isinstance(value, (tuple, list)):
        for item in value:
            yield from _tensors(item)


def test_atomic_capture_one_serializer_same_parameters_and_detached_gradients(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeating serialization or cloning before capture loses this identity/state."""
    _, _, owner, _ = _private(compiled, "rnd")
    expected_gradients = owner.call(lambda backend, sources: bootstrap._mixed_gradients(backend, "rnd"), lineage=None)
    backend = _raw(owner)
    parameters = _parameters(backend, "rnd")
    assert parameters and any(parameter.grad is None for parameter in parameters)
    assert any(parameter.grad is not None and bool(torch.count_nonzero(parameter.grad)) for parameter in parameters)
    expected_native = owner.snapshot(lineage=None)["backend"]
    real_checkpoint = type(backend).checkpoint_state
    native_calls: list[tuple[int, tuple[int, ...]]] = []
    capture_calls: list[tuple[int, tuple[int, ...]]] = []

    def checkpoint(candidate: Any) -> Any:
        assert candidate is backend
        native_calls.append((id(candidate), tuple(map(id, _parameters(candidate, "rnd")))))
        # An equal native payload would hide this nonserialized side effect if
        # an implementation called checkpoint_state a second time for RNG.
        if len(native_calls) > 1:
            for parameter in _parameters(candidate, "rnd"):
                parameter.grad = torch.full_like(parameter, 19.0)
        return real_checkpoint(candidate)

    def capture(candidate: Any) -> dict[str, Any]:
        assert candidate is backend and len(native_calls) == 1
        capture_calls.append((id(candidate), tuple(map(id, _parameters(candidate, "rnd")))))
        paired, gradients = bootstrap._pairing(candidate, "rnd")
        assert paired
        # Return actual Parameters and borrowed gradients inside value transport;
        # the public result must contain only detached independent tensors.
        return {"gradients": gradients, "borrowed": [parameter.grad for parameter in parameters], "weights": parameters}

    before = bootstrap._ambient()
    with monkeypatch.context() as patch:
        patch.setattr(type(backend), "checkpoint_state", checkpoint)
        envelope, auxiliary = owner.snapshot_with_capture(capture, lineage=None)
        assert len(native_calls) == len(capture_calls) == 1
    assert native_calls == capture_calls == [(id(backend), tuple(map(id, parameters)))]
    assert set(envelope) == {"schema", "healthy", "backend", "rng"}
    assert envelope["schema"] == "owned-world-backend-v1" and envelope["healthy"] is True
    assert bootstrap._equal(envelope["backend"], expected_native)
    assert bootstrap._equal(auxiliary["gradients"], expected_gradients)
    for original, owned in zip(parameters, auxiliary["weights"], strict=True):
        assert type(owned) is torch.Tensor and not owned.requires_grad and owned.grad_fn is None
        assert owned.data_ptr() != original.data_ptr() and torch.equal(owned, original)
    for original, owned in zip(parameters, auxiliary["borrowed"], strict=True):
        if original.grad is None:
            assert owned is None
        else:
            assert owned.data_ptr() != original.grad.data_ptr() and torch.equal(owned, original.grad)
    for tensor in _tensors((envelope, auxiliary)):
        assert type(tensor) is torch.Tensor and not tensor.requires_grad and tensor.grad_fn is None
    for tensor in _tensors(auxiliary):
        tensor.zero_()
    native_tensors = list(_tensors(envelope["backend"]))
    assert native_tensors
    for tensor in native_tensors:
        tensor.zero_()
    assert bootstrap._equal(owner.snapshot(lineage=None)["backend"], expected_native)
    assert bootstrap._equal(owner.call(lambda provider, sources: capture_gradients(provider, "rnd"), lineage=None), expected_gradients)
    bootstrap._assert_ambient(before)


class _DrawOnCopy(dict[str, Any]):
    """Portable mapping whose ownership traversal has visible RNG side effects."""

    def __init__(self, payload: dict[str, Any], events: list[str], label: str):
        super().__init__(payload)
        self.events = events
        self.label = label

    def items(self) -> Any:
        self.events.append(self.label)
        bootstrap._draw()
        return super().items()


def _advance_expected(component: dict[str, Any], draws: int) -> tuple[dict[str, Any], tuple[Any, ...]]:
    """Derive expected continuation with independent local standard generators."""
    expected = deepcopy(component)
    python = random.Random(0)
    python.setstate(component["python"])
    numpy = np.random.RandomState(0)
    numpy.set_state(component["numpy_legacy"])
    torch_generator = torch.Generator(device="cpu")
    torch_generator.set_state(component["torch_cpu"])
    for _ in range(draws):
        python.random()
        numpy.random_sample()
        torch.rand(3, generator=torch_generator)
    expected.update(python=python.getstate(), numpy_legacy=numpy.get_state(), torch_cpu=torch_generator.get_state())
    return expected, (python.random(), float(numpy.random_sample()), torch.rand(3, generator=torch_generator))


def test_atomic_capture_rng_follows_callback_copies_and_activation_completion(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Early RNG capture misses native/callback/ownership-traversal draws."""
    _, _, owner, actual_rng = _private(compiled, "rnd")
    backend = _raw(owner)
    entry = owner.snapshot(lineage=None)
    before = bootstrap._ambient()
    expected_service, expected_next = _advance_expected(entry["rng"]["components"]["service"], 4)
    events: list[str] = []
    real_checkpoint = type(backend).checkpoint_state
    real_snapshot = WorldRNGState._snapshot
    domain = process_rng_domain()
    real_complete = domain._complete

    def checkpoint(candidate: Any) -> Any:
        assert candidate is backend
        assert "native" not in events
        events.append("native")
        bootstrap._draw()
        return _DrawOnCopy(real_checkpoint(candidate), events, "native-copy")

    def capture(candidate: Any) -> Any:
        assert candidate is backend and events.count("native") == 1
        events.append("capture")
        bootstrap._draw()
        return _DrawOnCopy({"gradient": torch.tensor([0.125])}, events, "auxiliary-copy")

    def complete(devices: tuple[int, ...]) -> None:
        real_complete(devices)
        events.append("complete")

    def snapshot(rng: WorldRNGState) -> Any:
        assert rng is actual_rng
        assert all(events.count(label) == 1 for label in ("native", "native-copy", "capture", "auxiliary-copy"))
        assert events[-1] == "complete", "activation completion must precede quiescent RNG snapshot"
        events.append("rng")
        return real_snapshot(rng)

    with monkeypatch.context() as patch:
        patch.setattr(type(backend), "checkpoint_state", checkpoint)
        patch.setattr(WorldRNGState, "_snapshot", snapshot)
        patch.setattr(domain, "_complete", complete)
        envelope, auxiliary = owner.snapshot_with_capture(capture, lineage=None)
    assert events.count("rng") == 1
    assert bootstrap._equal(envelope["backend"], entry["backend"])
    assert torch.equal(auxiliary["gradient"], torch.tensor([0.125]))
    assert bootstrap._equal(envelope["rng"]["components"]["service"], expected_service)
    for component in ("model_init", "target", "predictor"):
        assert bootstrap._equal(envelope["rng"]["components"][component], entry["rng"]["components"][component])
    # Independent generator replay establishes that returned bytes describe the
    # actual next managed draws, rather than merely agreeing with another copy.
    observed_next = owner.call(
        lambda provider, sources: (sources.python.random(), float(np.random.random_sample()), torch.rand(3)), lineage=None
    )
    assert bootstrap._equal(observed_next, expected_next)
    bootstrap._assert_ambient(before)


def test_atomic_capture_preserves_snapshot_transport_and_explicit_lineage(compiled: Any) -> None:
    """The additive operation accepts authentic parent custody, with the old ABI."""
    _, _, owner, _ = _private(compiled, "rnd")
    owner.call(lambda provider, sources: bootstrap._mixed_gradients(provider, "rnd"), lineage=None)
    expected = owner.snapshot(lineage=None)
    before = bootstrap._ambient()
    domain = process_rng_domain()
    with domain.operation(participant=owner.rng_participant, operation_kind="snapshot", lineage=None) as lineage:
        assert type(lineage) is RNGOperation
        envelope, gradients = owner.snapshot_with_capture(lambda provider: capture_gradients(provider, "rnd"), lineage=lineage)
    assert bootstrap._equal(envelope, expected)
    assert bootstrap._equal(owner.snapshot(lineage=None), expected)
    assert bootstrap._equal(owner.call(lambda provider, sources: capture_gradients(provider, "rnd"), lineage=None), gradients)
    effects: list[str] = []
    for invalid in (lineage, object()):
        with bootstrap._no_rng_or_native_effects():
            with pytest.raises(ValueError):
                owner.snapshot_with_capture(lambda provider: effects.append("capture"), lineage=invalid)
    assert effects == []
    bootstrap._assert_ambient(before)


def test_atomic_capture_reentry_refuses_during_native_and_gradient_intervals(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both capture halves retain real owner/domain admission and RNG quiescence."""
    _, _, owner, actual_rng = _private(compiled, "rnd")
    _, _, peer, _ = _private(compiled, "none")
    backend = _raw(owner)
    real_checkpoint = type(backend).checkpoint_state
    phases: list[str] = []
    callbacks: list[str] = []
    before = bootstrap._ambient()
    domain = process_rng_domain()

    with domain.operation(participant=owner.rng_participant, operation_kind="snapshot", lineage=None) as lineage:

        def refuse(phase: str) -> None:
            phases.append(phase)
            for nested in (
                lambda: owner.snapshot(lineage=None),
                lambda: owner.snapshot(lineage=lineage),
                lambda: owner.snapshot_with_capture(lambda provider: callbacks.append("same"), lineage=lineage),
                lambda: owner.call(lambda provider, sources: callbacks.append("same-call"), lineage=lineage),
                lambda: peer.snapshot(lineage=None),
                lambda: peer.snapshot(lineage=lineage),
                lambda: peer.call(lambda provider, sources: callbacks.append("peer-call"), lineage=lineage),
                actual_rng.snapshot,
            ):
                with bootstrap._no_rng_or_native_effects():
                    with pytest.raises(RuntimeError):
                        nested()
            assert callbacks == []

        def checkpoint(candidate: Any) -> Any:
            assert candidate is backend
            refuse("native")
            return real_checkpoint(candidate)

        def capture(candidate: Any) -> Any:
            assert candidate is backend
            refuse("gradient")
            return capture_gradients(candidate, "rnd")

        with monkeypatch.context() as patch:
            patch.setattr(type(backend), "checkpoint_state", checkpoint)
            envelope, _ = owner.snapshot_with_capture(capture, lineage=lineage)
    assert phases == ["native", "gradient"] and envelope["healthy"] is True
    assert peer.snapshot(lineage=None)["healthy"] is True
    bootstrap._assert_ambient(before)


def test_atomic_capture_excludes_actual_peer_admission_through_cleanup(compiled: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """A split/unlocked capture exposes actual nonblocking admission at a cut."""
    _, _, owner, _ = _private(compiled, "rnd")
    _, _, peer, _ = _private(compiled, "none")
    backend = _raw(owner)
    domain = process_rng_domain()
    real_lock = domain._lock
    real_checkpoint = type(backend).checkpoint_state
    real_set = torch.set_rng_state
    phases = ("native", "gradient", "cleanup")
    reached = {phase: threading.Event() for phase in phases}
    release = {phase: threading.Event() for phase in phases}
    attempted = {phase: threading.Event() for phase in phases}
    entered = {phase: threading.Event() for phase in phases}
    acquired: dict[str, bool] = {}
    failures: list[BaseException] = []
    results: list[Any] = []
    body_done = threading.Event()
    before = bootstrap._ambient()

    class ObservedAdmission:
        def __enter__(self) -> ObservedAdmission:
            phase = threading.current_thread().name.removeprefix("atomic-peer-")
            if phase in attempted and not attempted[phase].is_set():
                immediate = real_lock.acquire(blocking=False)
                if immediate:
                    real_lock.release()
                acquired[phase] = immediate
                attempted[phase].set()
            real_lock.acquire()
            return self

        def __exit__(self, error_type: Any, error: Any, traceback: Any) -> None:
            real_lock.release()

    def pause(phase: str) -> None:
        reached[phase].set()
        assert release[phase].wait(10)

    def checkpoint(candidate: Any) -> Any:
        assert candidate is backend
        pause("native")
        return real_checkpoint(candidate)

    def capture(candidate: Any) -> Any:
        assert candidate is backend
        pause("gradient")
        value = capture_gradients(candidate, "rnd")
        body_done.set()
        return value

    def setter(value: torch.Tensor) -> None:
        if threading.current_thread().name == "atomic-producer" and body_done.is_set() and not reached["cleanup"].is_set():
            pause("cleanup")
        real_set(value)

    def produce() -> None:
        try:
            results.append(owner.snapshot_with_capture(capture, lineage=None))
        except BaseException as error:
            failures.append(error)

    def consume(phase: str) -> None:
        try:
            peer.call(lambda provider, sources: entered[phase].set(), lineage=None)
        except BaseException as error:
            failures.append(error)

    monkeypatch.setattr(domain, "_lock", ObservedAdmission())
    monkeypatch.setattr(type(backend), "checkpoint_state", checkpoint)
    monkeypatch.setattr(torch, "set_rng_state", setter)
    producer = threading.Thread(target=produce, name="atomic-producer")
    consumers = {phase: threading.Thread(target=consume, args=(phase,), name=f"atomic-peer-{phase}") for phase in phases}
    producer.start()
    try:
        for phase in phases:
            assert reached[phase].wait(10)
            consumers[phase].start()
            assert attempted[phase].wait(5)
            assert acquired[phase] is False
            assert not any(event.is_set() for event in entered.values())
            release[phase].set()
    finally:
        for event in release.values():
            event.set()
        producer.join(15)
        for consumer in consumers.values():
            if consumer.ident is not None:
                consumer.join(15)
    assert not producer.is_alive() and not any(consumer.is_alive() for consumer in consumers.values())
    assert failures == [] and len(results) == 1
    assert all(event.is_set() for event in entered.values())
    bootstrap._assert_ambient(before)


@pytest.mark.parametrize("stage", ("native", "capture", "auxiliary-copy"))
def test_atomic_capture_failure_quarantines_without_poisoning_healthy_peers(
    compiled: Any, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    """No failed native/callback/result-copy operation can report healthy success."""
    _, _, owner, _ = _private(compiled, "rnd")
    _, _, peer, _ = _private(compiled, "none")
    backend = _raw(owner)
    real_checkpoint = type(backend).checkpoint_state
    calls: list[str] = []
    before = bootstrap._ambient()

    def checkpoint(candidate: Any) -> Any:
        calls.append("native")
        result = real_checkpoint(candidate)
        if stage == "native":
            bootstrap._draw()
            raise ValueError("primary atomic native failure")
        return result

    class Uncopyable(dict[str, Any]):
        def items(self) -> Any:
            calls.append("auxiliary-copy")
            bootstrap._draw()
            raise ValueError("primary atomic auxiliary-copy failure")

    def capture(candidate: Any) -> Any:
        calls.append("capture")
        if stage == "capture":
            bootstrap._draw()
            raise ValueError("primary atomic capture failure")
        return Uncopyable(gradients=capture_gradients(candidate, "rnd"))

    with monkeypatch.context() as patch:
        patch.setattr(type(backend), "checkpoint_state", checkpoint)
        with pytest.raises(ValueError, match=f"primary atomic {stage} failure"):
            owner.snapshot_with_capture(capture, lineage=None)
    assert (
        calls == {"native": ["native"], "capture": ["native", "capture"], "auxiliary-copy": ["native", "capture", "auxiliary-copy"]}[stage]
    )
    assert owner.snapshot(lineage=None)["healthy"] is False
    effects: list[str] = []
    with pytest.raises(RuntimeError, match="quarantin"):
        owner.call(lambda provider, sources: effects.append("resumed"), lineage=None)
    assert effects == []
    assert peer.snapshot(lineage=None)["healthy"] is True
    assert process_rng_domain().status()[2] is False
    bootstrap._assert_ambient(before)


@pytest.mark.parametrize("invalid", (None, 17, "capture", {}))
def test_atomic_capture_noncallable_refuses_before_native_work_and_keeps_owner_usable(compiled: Any, invalid: Any) -> None:
    """Malformed capture input is admission refusal rather than a live callback."""
    _, _, owner, _ = _private(compiled, "none")
    backend = _raw(owner)
    before = bootstrap._ambient()
    with pytest.MonkeyPatch.context() as patch:

        def forbidden(candidate: Any) -> Any:
            raise AssertionError("noncallable capture reached native serialization")

        patch.setattr(type(backend), "checkpoint_state", forbidden)
        with bootstrap._no_rng_or_native_effects():
            with pytest.raises(ValueError, match="callable"):
                owner.snapshot_with_capture(invalid, lineage=None)
    assert owner.call(lambda provider, sources: True, lineage=None) is True
    assert owner.snapshot(lineage=None)["healthy"] is True
    bootstrap._assert_ambient(before)


def test_atomic_capture_invalidates_prepared_destination_revision(compiled: Any) -> None:
    """New snapshots must not leave an earlier prepared handle current."""
    policy, descriptor, owner, _ = _private(compiled, "none")
    payload = owner.snapshot(lineage=None)
    handle = owner.prepare_restore(
        payload,
        factory=lambda rng: bootstrap._factory(policy, descriptor, rng),
        validate_backend=bootstrap._validator(policy, descriptor),
        lineage=None,
    )
    owner.snapshot_with_capture(lambda provider: {"observed": True}, lineage=None)
    with pytest.raises(ValueError):
        owner.install(handle, lineage=None)
    assert owner.snapshot(lineage=None)["healthy"] is True


def _capture_poison_child(queue: Any, kind: str) -> None:
    role = f"owner_capture_poison_{kind}"
    qualified = bootstrap._child_identity(role)
    # Invoke the supplier fixture's genuine compilation function, rather than
    # substituting a synthetic descriptor or copying its provider source.
    compiled_universe = bootstrap.compiled.__wrapped__()
    _, _, owner, actual_rng = _private(compiled_universe, "rnd")
    _, _, peer, _ = _private(compiled_universe, "none")
    backend = _raw(owner)
    original_parameters = _parameters(backend, "rnd")
    original_native = owner.snapshot(lineage=None)["backend"]
    domain = process_rng_domain()
    patch = pytest.MonkeyPatch()
    real_python_set = random.setstate
    real_torch_set = torch.set_rng_state
    real_complete = domain._complete
    setter_calls = 0
    captures: list[str] = []

    def broken_python(value: Any) -> None:
        real_python_set(value)
        raise RuntimeError("atomic partial private setter failure")

    def broken_torch(value: torch.Tensor) -> None:
        nonlocal setter_calls
        setter_calls += 1
        real_torch_set(value)
        if kind == "cleanup" or setter_calls > 1:
            raise RuntimeError("atomic ambient cleanup setter failure")

    def broken_complete(devices: tuple[int, ...]) -> None:
        real_complete(devices)
        raise RuntimeError("atomic declared device completion failure")

    def capture(candidate: Any) -> Any:
        assert candidate is backend
        captures.append("capture")
        if kind == "cleanup":
            bootstrap._draw()
            patch.setattr(torch, "set_rng_state", broken_torch)
            raise ValueError("primary atomic capture body failure")
        return capture_gradients(candidate, "rnd")

    try:
        if kind == "setter":
            patch.setattr(random, "setstate", broken_python)
            patch.setattr(torch, "set_rng_state", broken_torch)
        elif kind == "completion":
            assert kind == "completion"
            patch.setattr(domain, "_complete", broken_complete)
        else:
            assert kind == "cleanup"
        try:
            owner.snapshot_with_capture(capture, lineage=None)
        except BaseException as error:
            messages = bootstrap._exception_messages(error)
            expected = {
                "setter": ("atomic partial private setter failure", "atomic ambient cleanup setter failure"),
                "cleanup": ("primary atomic capture body failure", "atomic ambient cleanup setter failure"),
                "completion": ("atomic declared device completion failure",),
            }[kind]
            assert all(any(fragment in message for message in messages) for fragment in expected), messages
        else:
            raise AssertionError("uncertain atomic capture returned successful data")
    finally:
        patch.undo()
    assert captures == ([] if kind == "setter" else ["capture"])
    assert tuple(map(id, _parameters(backend, "rnd"))) == tuple(map(id, original_parameters))
    assert bootstrap._equal(backend.checkpoint_state(), original_native)
    assert domain.status()[2] is True
    effects: list[str] = []
    for operation in (
        lambda: owner.snapshot_with_capture(lambda candidate: effects.append("resumed"), lineage=None),
        lambda: owner.snapshot(lineage=None),
        lambda: owner.call(lambda candidate, sources: effects.append("resumed-call"), lineage=None),
        lambda: peer.snapshot(lineage=None),
        actual_rng.snapshot,
        lambda: SharedWorldBackend.reserve(cuda_devices=()),
    ):
        with pytest.raises(RuntimeError, match="poison"):
            operation()
    assert effects == []
    queue.put((f"owner capture poison {kind} fail closed", os.getpid(), qualified))


@pytest.mark.parametrize("kind", ("setter", "cleanup", "completion"))
def test_fresh_child_atomic_capture_poison_fails_common_domain_closed(kind: str) -> None:
    """Uncertain restoration/completion fails every enrolled owner in a child."""
    qualified = bootstrap._qualification_active()
    role = f"owner_capture_poison_{kind}"
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_capture_poison_child, args=(queue, kind), name=role)
    before = bootstrap._ambient()
    process.start()
    try:
        process.join(90)
        assert not process.is_alive(), f"{role} child timed out"
        assert process.exitcode == 0
        try:
            message, queued_pid, child_qualified = queue.get(timeout=5)
        except Empty:
            pytest.fail(f"{role} child emitted no successful poison receipt")
        assert message == f"owner capture poison {kind} fail closed" and queued_pid == process.pid
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
    bootstrap._assert_ambient(before)
