"""Canonical flat/PER contract activation; CPU protocol evidence only.

These controls use real producer membership and source-issued constants. No
production manifest is replaced. Import/fork/poison children and the existing
producer completion matrix belong to their separately qualified packets.
"""

import gc
import weakref
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import FrozenInstanceError
from types import MappingProxyType
from typing import Any

import numpy as np
import pytest
import torch

from townlet.exploration import rng_custody as custody
from townlet.training import prioritized_replay_buffer, replay_buffer
from townlet.training.historical_checkpoint import HistoricalReplayArchive, archive_standalone_replay
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import ReplayRequest
from townlet.training.state import RewardTensor

# Each row names one actual source route, including flat's distinct validation
# prelude. PER load_for_mode calls its existing validate_serialized route.
_ROUTES = (
    ("flat", "push", "REPLAY_BUFFER_PUSH_CUDA", "tensor", torch.Tensor),
    ("flat", "push_recorded", "REPLAY_BUFFER_PUSH_RECORDED_CUDA", "tensor", torch.Tensor),
    ("flat", "readiness", "REPLAY_BUFFER_READINESS_CUDA", "request", ReplayRequest),
    ("flat", "serialize", "REPLAY_BUFFER_SERIALIZE_CUDA", "none", type(None)),
    ("flat", "validate_serialized", "REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA", "mapping", Mapping),
    ("flat", "load_for_mode", "REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA", "mapping", Mapping),
    ("flat", "historical_archives", "REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA", "none", type(None)),
    ("flat", "install_historical_archive", "REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA", "archive", HistoricalReplayArchive),
    ("per", "push", "PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA", "tensor", torch.Tensor),
    ("per", "push_recorded", "PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA", "tensor", torch.Tensor),
    ("per", "declare_unconstrained_action_dim", "PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA", "integer", int),
    ("per", "readiness", "PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA", "request", ReplayRequest),
    ("per", "serialize", "PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA", "none", type(None)),
    ("per", "validate_serialized", "PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA", "mapping", Mapping),
    ("per", "historical_archives", "PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA", "none", type(None)),
    ("per", "install_historical_archive", "PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA", "archive", HistoricalReplayArchive),
    ("per", "update_priorities", "PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA", "indices", np.ndarray),
    ("per", "update_unit_priorities", "PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA", "indices", np.ndarray),
)
_ROUTE_IDS = tuple(f"{row[0]}-{row[1]}" for row in _ROUTES)
_CLASSES = {"flat": ReplayBuffer, "per": PrioritizedReplayBuffer}


def _contract(name: str) -> custody.LocalCUDAContract:
    assert hasattr(custody, name), f"B activation missing source-issued constant: {name}"
    contract = getattr(custody, name)
    assert type(contract) is custody.LocalCUDAContract
    return contract


def _name(family: str, route: str) -> str:
    return next(row[2] for row in _ROUTES if row[:2] == (family, route))


class _NoCUDA:
    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"activation binding unexpectedly accessed CUDA: {name}")


@pytest.fixture
def owners() -> Iterator[Any]:
    domain = custody.process_rng_domain()
    retained: list[object] = []
    participants: list[custody.RNGParticipant] = []

    def make(family: str, *, owner_type: type | None = None) -> Any:
        cls = _CLASSES[family] if owner_type is None else owner_type
        if family == "flat":
            owner = cls(4, torch.device("cpu"))
        else:
            owner = cls(4, 1.0, 0.0, False, torch.device("cpu"))
        retained.append(owner)
        participants.append(owner.rng_participant)
        return owner

    def unrelated(cls: type) -> tuple[object, custody.RNGParticipant]:
        owner = cls()
        participant = domain.register(owner=owner, cuda_devices=(), entrypoints=frozenset({"sample"}))
        retained.append(owner)
        participants.append(participant)
        return owner, participant

    yield make, unrelated
    for participant in reversed(participants):
        domain.unregister(participant=participant)


def test_exact_source_manifest_and_immutable_descriptors() -> None:
    constants = [_contract(row[2]) for row in _ROUTES]
    assert len(constants) == len(set(constants)) == 18
    manifest = custody._LOCAL_CUDA_CONTRACTS
    assert type(manifest) is MappingProxyType
    assert set(manifest) == set(constants)
    descriptor_type = getattr(custody, "_LocalCUDADescriptor")
    for row, contract in zip(_ROUTES, constants, strict=True):
        family, route, _, input_kind, _ = row
        descriptor = manifest[contract]
        assert type(descriptor) is descriptor_type
        assert (descriptor.owner_kind, descriptor.route, descriptor.input_kind) == (family, route, input_kind)
        assert descriptor.healthy is True and descriptor.post_poison is False
        assert type(descriptor.rationale) is str and descriptor.rationale.strip()
        with pytest.raises(FrozenInstanceError):
            descriptor.route = "unreviewed"
    with pytest.raises(TypeError):
        manifest[constants[0]] = manifest[constants[0]]


@pytest.mark.parametrize("family,route,name,input_kind,input_type", _ROUTES, ids=_ROUTE_IDS)
def test_every_contract_binds_real_canonical_owner(
    family: str, route: str, name: str, input_kind: str, input_type: type, owners: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _contract(name)
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, _ = owners
    owner = make(family)
    domain = custody.process_rng_domain()
    before = domain.status()
    with domain.local_cuda_access(participant=owner.rng_participant, contract=contract) as gate:
        descriptor, policy = domain._local_cuda_policies[contract]
        assert descriptor is custody._LOCAL_CUDA_CONTRACTS[contract]
        assert descriptor.input_kind == input_kind
        assert type(policy) is custody._LocalCUDARecord
        assert policy.owner_type is type(owner) is _CLASSES[family]
        assert policy.input_type is input_type
        assert policy.route == route
        assert policy.healthy is True and policy.post_poison is False
        with gate.complete(cuda_devices=()):
            pass
        assert gate.completion_failed() is False
    assert domain.status() == before
    with pytest.raises(ValueError, match="foreign or expired"):
        gate.completion_failed()


@pytest.mark.parametrize("family,route,name,input_kind,input_type", _ROUTES, ids=_ROUTE_IDS)
def test_every_contract_refuses_other_real_family(
    family: str, route: str, name: str, input_kind: str, input_type: type, owners: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _contract(name)
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, _ = owners
    owner = make("per" if family == "flat" else "flat")
    domain = custody.process_rng_domain()
    before = domain.status()
    with pytest.raises(ValueError, match="exact owner class"):
        with domain.local_cuda_access(participant=owner.rng_participant, contract=contract):
            pytest.fail("wrong-family producer entered a local gate")
    assert domain.status() == before


@pytest.mark.parametrize("family", ("flat", "per"))
@pytest.mark.parametrize("case", ("subclass", "name_spoof", "unknown_participant", "unknown_contract"))
def test_unlisted_identity_refuses_before_cuda(family: str, case: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _contract(_name(family, "serialize"))
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, unrelated = owners
    canonical = _CLASSES[family]
    if case == "subclass":
        owner = make(family, owner_type=type("Unlisted", (canonical,), {}))
        participant = owner.rng_participant
    elif case == "name_spoof":
        spoof = type(canonical.__name__, (), {"__module__": canonical.__module__})
        _, participant = unrelated(spoof)
    else:
        owner = make(family)
        participant = owner.rng_participant
        if case == "unknown_participant":
            participant = object()
        else:
            contract = object()
    with pytest.raises(ValueError):
        with custody.process_rng_domain().local_cuda_access(participant=participant, contract=contract):
            pytest.fail("unlisted identity entered a local gate")


@pytest.mark.parametrize("family", ("flat", "per"))
def test_second_public_local_gate_still_refuses(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    first = _contract(_name(family, "serialize"))
    second = _contract(_name(family, "readiness"))
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, _ = owners
    owner = make(family)
    domain = custody.process_rng_domain()
    with domain.local_cuda_access(participant=owner.rng_participant, contract=first) as gate:
        before = dict(domain._local_cuda_policies)
        with pytest.raises(RuntimeError, match="reuse their producer's existing scope"):
            with domain.local_cuda_access(participant=owner.rng_participant, contract=second):
                pytest.fail("nested public local gate was admitted")
        assert domain._local_cuda_policies == before
        with gate.complete(cuda_devices=()):
            pass
        assert gate.completion_failed() is False


@pytest.mark.parametrize("family", ("flat", "per"))
def test_resolved_policy_identity_survives_sequential_instances(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _contract(_name(family, "serialize"))
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, _ = owners
    first, second = make(family), make(family)
    domain = custody.process_rng_domain()
    records = []
    for owner in (first, second, first):
        with domain.local_cuda_access(participant=owner.rng_participant, contract=contract) as gate:
            records.append(domain._local_cuda_policies[contract])
            with gate.complete(cuda_devices=()):
                pass
    assert all(record is records[0] for record in records)
    assert records[0][1].owner_type is _CLASSES[family]
    assert first.rng_participant is not second.rng_participant


@pytest.mark.parametrize("family", ("flat", "per"))
def test_resolved_policy_does_not_pin_retired_canonical_owner(family: str, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _contract(_name(family, "serialize"))
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    if family == "flat":
        owner = ReplayBuffer(4, torch.device("cpu"))
    else:
        owner = PrioritizedReplayBuffer(4, 1.0, 0.0, False, torch.device("cpu"))
    domain = custody.process_rng_domain()
    participant = owner.rng_participant
    reference = weakref.ref(owner)
    try:
        with domain.local_cuda_access(participant=participant, contract=contract) as gate:
            resolved = domain._local_cuda_policies[contract]
            with gate.complete(cuda_devices=()):
                pass
    finally:
        domain.unregister(participant=participant)
    del owner
    gc.collect()
    assert reference() is None
    assert domain._local_cuda_policies[contract] is resolved


@pytest.mark.parametrize("family", ("flat", "per"))
def test_failed_canonical_lookup_does_not_cache_success(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _contract(_name(family, "serialize"))
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    make, _ = owners
    owner = make(family)
    domain = custody.process_rng_domain()
    module = replay_buffer if family == "flat" else prioritized_replay_buffer
    canonical = _CLASSES[family]
    # Establish a cold entry without altering any descriptor or authority. All
    # fixture changes occur under real idle exclusion, with no live local gate.
    with domain.admission(lineage=None):
        cache = dict(domain._local_cuda_policies)
        cache.pop(contract, None)
        monkeypatch.setattr(domain, "_local_cuda_policies", cache)
    before = domain.status()
    with monkeypatch.context() as missing:
        missing.delattr(module, canonical.__name__)
        with pytest.raises((ImportError, AttributeError, ValueError, RuntimeError)):
            with domain.local_cuda_access(participant=owner.rng_participant, contract=contract):
                pytest.fail("missing canonical class was admitted")
        assert contract not in cache
    with domain.local_cuda_access(participant=owner.rng_participant, contract=contract) as gate:
        assert cache[contract][1].owner_type is canonical
        with gate.complete(cuda_devices=()):
            pass
    assert domain.status() == before


class _SourceOnCUDA(torch.Tensor):
    """CPU-backed source metadata seam; real numeric/copy work remains CPU."""

    events: list[object]

    @staticmethod
    def __new__(cls: type, value: torch.Tensor) -> "_SourceOnCUDA":
        return torch.Tensor._make_subclass(cls, value, False)

    @property
    def device(self) -> torch.device:
        return torch.device("cuda", 1)

    def cpu(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        self.events.append("copy-to-cpu")
        return self.as_subclass(torch.Tensor).cpu(*args, **kwargs)

    def to(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        self.events.append("convert-to-cpu")
        destination = args[0] if args else kwargs.get("device")
        assert torch.device(destination).type == "cpu", "source seam must retain the actual CPU destination"
        return self.as_subclass(torch.Tensor).to(*args, **kwargs)

    def clone(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        self.events.append("clone-source")
        return torch.Tensor.clone(self, *args, **kwargs)


def test_cpu_backed_source_fixture_preserves_real_values(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[object] = []
    monkeypatch.setattr(_SourceOnCUDA, "events", events, raising=False)
    ordinary = torch.tensor([-2.0, 4.0], dtype=torch.float32)
    source = _SourceOnCUDA(ordinary)
    assert source.device == torch.device("cuda", 1)
    copied = source[:1].detach().cpu().clone()
    converted = source.detach().to(device="cpu", dtype=torch.float64)
    assert type(copied) is type(converted) is torch.Tensor
    assert copied.device.type == converted.device.type == "cpu"
    assert torch.equal(copied, ordinary[:1])
    assert np.array_equal(converted.numpy(), np.array([-2.0, 4.0], dtype=np.float64))
    copied.fill_(99)
    assert torch.equal(ordinary, torch.tensor([-2.0, 4.0], dtype=torch.float32))
    assert torch.equal(source.as_subclass(torch.Tensor), ordinary)
    assert events == ["copy-to-cpu", "convert-to-cpu"]


def _rows(owner: Any) -> None:
    observations = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float32)
    owner.push_recorded(
        observations,
        torch.tensor([0, 1], dtype=torch.int64),
        RewardTensor(torch.tensor([1.0, 2.0], dtype=torch.float32)),
        observations + 1,
        torch.tensor([False, True]),
        torch.tensor([[True, False], [False, False]]),
    )


def _observe_real_local_route(monkeypatch: pytest.MonkeyPatch, owner: Any, name: str, events: list[object]) -> None:
    expected = _contract(name)
    domain = custody.process_rng_domain()
    original = domain.local_cuda_access

    @contextmanager
    def observe(*, participant: custody.RNGParticipant, contract: custody.LocalCUDAContract) -> Iterator[custody.LocalCUDAGate]:
        assert participant is owner.rng_participant and contract is expected
        with original(participant=participant, contract=contract) as gate:
            events.append("gate-enter")
            yield gate
        events.append("gate-exit")

    def no_init() -> None:
        pytest.fail("already initialized source-only operation attempted CUDA initialization")

    def no_current() -> int:
        pytest.fail("source-only operation queried an unused allocation selector")

    monkeypatch.setattr(domain, "local_cuda_access", observe)
    monkeypatch.setattr(torch.cuda, "is_initialized", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 3)
    monkeypatch.setattr(torch.cuda, "init", no_init)
    monkeypatch.setattr(torch.cuda, "current_device", no_current)
    monkeypatch.setattr(torch.cuda, "synchronize", lambda index: events.append(("complete", index)))
    monkeypatch.setattr(_SourceOnCUDA, "events", events, raising=False)


@pytest.mark.parametrize("family", ("flat", "per"))
def test_real_serialize_dispatch_owns_rows_and_completes_only_source(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _contract(_name(family, "serialize"))
    make, _ = owners
    owner = make(family)
    _rows(owner)
    expected = owner.serialize()
    owner.observations = _SourceOnCUDA(owner.observations)
    events: list[object] = []
    _observe_real_local_route(monkeypatch, owner, _name(family, "serialize"), events)
    result = owner.serialize()
    assert events == ["gate-enter", "copy-to-cpu", ("complete", 1), "gate-exit"]
    assert set(result) == set(expected)
    for key, value in expected.items():
        if isinstance(value, torch.Tensor):
            assert type(result[key]) is torch.Tensor and result[key].device.type == "cpu"
            assert torch.equal(result[key], value)
        elif isinstance(value, np.ndarray):
            assert np.array_equal(result[key], value)
        else:
            assert result[key] == value
    result["observations"].fill_(99)
    assert torch.equal(owner.observations.as_subclass(torch.Tensor)[:2], expected["observations"])
    assert owner.device == torch.device("cpu")


@pytest.mark.parametrize("stable", (False, True), ids=("physical", "stable"))
def test_real_priority_dispatch_preserves_algorithm_and_source_completion(
    stable: bool, owners: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    route = "update_unit_priorities" if stable else "update_priorities"
    _contract(_name("per", route))
    make, _ = owners
    owner = make("per")
    _rows(owner)
    if stable:
        _rows(owner)
        _rows(owner)
        assert np.array_equal(owner.unit_ids, np.array([4, 5, 2, 3], dtype=np.int64))
    before_revision = owner._replay_revision
    expected = owner.priorities.copy()
    if stable:
        errors = _SourceOnCUDA(torch.tensor([-3.0, 4.0, 2.0], dtype=torch.float32))
        indices = np.array([4, 2, 4], dtype=np.int64)
        expected[[0, 2]] = np.array([3.0 + 1e-6, 4.0 + 1e-6], dtype=np.float32)
    else:
        errors = _SourceOnCUDA(torch.tensor([-2.0, 4.0], dtype=torch.float32))
        indices = np.array([0, 1], dtype=np.int64)
        expected[:2] = np.array([2.0 + 1e-6, 4.0 + 1e-6], dtype=np.float32)
    events: list[object] = []
    _observe_real_local_route(monkeypatch, owner, _name("per", route), events)
    getattr(owner, route)(indices, errors)
    assert events == ["gate-enter", "convert-to-cpu", ("complete", 1), "gate-exit"]
    assert np.array_equal(owner.priorities, expected)
    assert owner.max_priority == float(expected.max())
    assert owner._replay_revision == before_revision + 1
    assert owner.device == torch.device("cpu")


@pytest.mark.parametrize("family", ("flat", "per"))
def test_cpu_local_data_work_does_not_resolve_cuda_contracts(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    make, _ = owners
    owner = make(family)
    monkeypatch.setattr(torch, "cuda", _NoCUDA())

    def forbidden_gate(*, participant: object, contract: object) -> Any:
        pytest.fail("CPU-only local data work attempted a CUDA contract gate")

    monkeypatch.setattr(custody.process_rng_domain(), "local_cuda_access", forbidden_gate)
    _rows(owner)
    state = owner.serialize()
    assert state["observations"].shape == (2, 2)
    assert state["observations"].device.type == "cpu"
    owner.clear()
    assert len(owner) == 0


@pytest.mark.parametrize("family", ("flat", "per"))
def test_real_plain_push_owns_numeric_rows_and_declares_legal_masks(family: str, owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _contract(_name(family, "push"))
    make, _ = owners
    owner = make(family)
    _rows(owner)
    incoming = torch.tensor([[5.0, 6.0], [7.0, 8.0]], dtype=torch.float32)
    source = _SourceOnCUDA(incoming)
    events: list[object] = []
    _observe_real_local_route(monkeypatch, owner, _name(family, "push"), events)
    owner.push(
        source,
        torch.tensor([1, 0], dtype=torch.int64),
        RewardTensor(torch.tensor([9.0, 10.0]), extrinsic=torch.tensor([3.0, 4.0])),
        incoming + 1,
        torch.tensor([False, True]),
    )
    assert events == ["gate-enter", "convert-to-cpu", ("complete", 1), "gate-exit"]
    source.fill_(99)
    result = owner.serialize()
    assert len(owner) == 4 and owner.device == torch.device("cpu")
    assert torch.equal(result["observations"][2:], torch.tensor([[5.0, 6.0], [7.0, 8.0]]))
    assert torch.equal(result["next_observations"][2:], torch.tensor([[6.0, 7.0], [8.0, 9.0]]))
    assert torch.equal(result["actions"][2:], torch.tensor([1, 0], dtype=torch.int64))
    assert torch.equal(result["rewards"][2:], torch.tensor([9.0, 10.0]))
    assert torch.equal(result["rewards_extrinsic"][2:], torch.tensor([3.0, 4.0]))
    assert torch.equal(result["rewards_extrinsic_present"], torch.tensor([False, False, True, True]))
    assert torch.equal(result["next_action_masks"][2:], torch.ones((2, 2), dtype=torch.bool))
    assert bool(result["legality_recorded"].all())


def test_real_flat_load_for_mode_completes_validation_before_install(owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _contract(_name("flat", "load_for_mode"))
    make, _ = owners
    source, target = make("flat"), make("flat")
    _rows(source)
    expected = source.serialize()
    supplied = {key: _SourceOnCUDA(value) if isinstance(value, torch.Tensor) else value for key, value in expected.items()}
    events: list[object] = []
    _observe_real_local_route(monkeypatch, target, _name("flat", "load_for_mode"), events)
    target.load_for_mode(supplied, requested_mode="auto", lineage=None)
    first_completion = events.index(("complete", 1))
    assert events[0] == "gate-enter" and events[first_completion + 1] == "gate-exit"
    tensor_count = sum(isinstance(value, torch.Tensor) for value in expected.values())
    assert events[1:first_completion].count("clone-source") >= tensor_count
    assert events.count("gate-enter") == events.count("gate-exit") == 1
    assert [event for event in events if isinstance(event, tuple)] == [("complete", 1), ("complete", 1)]
    assert "convert-to-cpu" in events[first_completion + 2 :]
    result = target.serialize()
    for key, value in expected.items():
        if isinstance(value, torch.Tensor):
            assert type(result[key]) is torch.Tensor and result[key].device.type == "cpu"
            assert torch.equal(result[key], value)
        else:
            assert result[key] == value
    supplied["observations"].fill_(99)
    assert torch.equal(target.observations[:2], torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    assert len(target) == 2 and target.device == torch.device("cpu")


def _nonempty_per_archive(owner: PrioritizedReplayBuffer, *, cuda_source: bool) -> HistoricalReplayArchive:
    state = owner.serialize()
    legacy = {key: state[key] for key in prioritized_replay_buffer._LEGACY_STATE_KEYS}
    legacy["format_version"] = 4
    for field in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
        if legacy[field] is None:
            legacy[field] = torch.zeros_like(legacy["rewards"])
    if cuda_source:
        legacy = {key: _SourceOnCUDA(value) if isinstance(value, torch.Tensor) else value for key, value in legacy.items()}
    return archive_standalone_replay(legacy)


def test_cpu_archive_fixture_preserves_nonempty_per_rows(owners: Any) -> None:
    make, _ = owners
    source, target = make("per"), make("per")
    _rows(source)
    archive = _nonempty_per_archive(source, cuda_source=False)
    target.install_historical_archive(archive)
    returned = target.historical_archives
    assert len(returned) == 1 and returned[0].archived_row_count == 2 and len(target) == 0
    rows = returned[0].original_state
    assert torch.equal(rows["observations"], torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    rows["observations"].fill_(99)
    assert torch.equal(target.historical_archives[0].original_state["observations"], torch.tensor([[1.0, 2.0], [3.0, 4.0]]))


def test_cpu_backed_cuda_archive_fixture_has_verified_owned_rows(owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    make, _ = owners
    source = make("per")
    _rows(source)
    monkeypatch.setattr(torch, "cuda", _NoCUDA())
    monkeypatch.setattr(_SourceOnCUDA, "events", [], raising=False)
    archive = _nonempty_per_archive(source, cuda_source=True)
    assert type(archive) is HistoricalReplayArchive and archive.archived_row_count == 2
    rows = archive.original_state
    assert rows["observations"].device == torch.device("cuda", 1)
    assert torch.equal(rows["observations"].as_subclass(torch.Tensor), torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    rows["observations"].fill_(99)
    assert torch.equal(archive.original_state["observations"].as_subclass(torch.Tensor), torch.tensor([[1.0, 2.0], [3.0, 4.0]]))


def test_real_per_historical_property_clones_nonempty_cuda_archive(owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _contract(_name("per", "historical_archives"))
    _contract(_name("per", "install_historical_archive"))
    make, _ = owners
    source, target = make("per"), make("per")
    _rows(source)
    monkeypatch.setattr(_SourceOnCUDA, "events", [], raising=False)
    # Public archive construction computes and validates the real digest over
    # the CPU-backed source; no digest or canonical archive is fabricated.
    archive = _nonempty_per_archive(source, cuda_source=True)
    install_events: list[object] = []
    with monkeypatch.context() as installing:
        _observe_real_local_route(installing, target, _name("per", "install_historical_archive"), install_events)
        target.install_historical_archive(archive)
    assert install_events[0] == "gate-enter" and install_events[-2:] == [("complete", 1), "gate-exit"]
    assert [event for event in install_events if isinstance(event, tuple)] == [("complete", 1)]
    assert "clone-source" in install_events[1:-2] and "copy-to-cpu" in install_events[1:-2]
    installed = target._historical_archives[0]
    assert installed is not archive and installed.source_digest == archive.source_digest
    retained = object.__getattribute__(installed, "original_state")
    incoming = object.__getattribute__(archive, "original_state")
    incoming["observations"].fill_(77)
    assert torch.equal(retained["observations"].as_subclass(torch.Tensor), torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    events: list[object] = []
    _observe_real_local_route(monkeypatch, target, _name("per", "historical_archives"), events)
    returned = target.historical_archives
    assert events[0] == "gate-enter" and events[-2:] == [("complete", 1), "gate-exit"]
    assert events.count("gate-enter") == events.count("gate-exit") == 1
    assert [event for event in events if isinstance(event, tuple)] == [("complete", 1)]
    assert "clone-source" in events[1:-2] and "copy-to-cpu" in events[1:-2]
    assert len(returned) == 1 and type(returned[0]) is HistoricalReplayArchive
    assert returned[0] is not installed and returned[0].source_digest == archive.source_digest
    assert returned[0].archived_row_count == 2 and len(target) == 0
    owned = object.__getattribute__(returned[0], "original_state")
    assert torch.equal(owned["observations"].as_subclass(torch.Tensor), torch.tensor([[1.0, 2.0], [3.0, 4.0]]))
    owned["observations"].fill_(99)
    assert torch.equal(retained["observations"].as_subclass(torch.Tensor), torch.tensor([[1.0, 2.0], [3.0, 4.0]]))


def test_real_stale_unit_priority_refusal_preserves_numeric_state(owners: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _contract(_name("per", "update_unit_priorities"))
    make, _ = owners
    owner = make("per")
    for _ in range(3):
        _rows(owner)
    assert np.array_equal(owner.unit_ids, np.array([4, 5, 2, 3], dtype=np.int64))
    priorities, ids = owner.priorities.copy(), owner.unit_ids.copy()
    maximum, revision = owner.max_priority, owner._replay_revision
    before = custody.process_rng_domain().status()
    events: list[object] = []
    _observe_real_local_route(monkeypatch, owner, _name("per", "update_unit_priorities"), events)
    with pytest.raises(ValueError, match="stale or unknown unit ID 0"):
        owner.update_unit_priorities(np.array([4, 0], dtype=np.int64), _SourceOnCUDA(torch.tensor([8.0, 9.0])))
    assert events == ["gate-enter", "convert-to-cpu", ("complete", 1)]
    assert np.array_equal(owner.priorities, priorities) and np.array_equal(owner.unit_ids, ids)
    assert owner.max_priority == maximum and owner._replay_revision == revision + 1
    assert custody.process_rng_domain().status() == before
    owner._check_custody()
