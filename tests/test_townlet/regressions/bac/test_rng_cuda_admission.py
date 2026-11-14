"""CPU protocol controls; instrumented CUDA calls are not hardware qualification."""

from __future__ import annotations

import copy
import gc
import hashlib
import importlib
import inspect
import json
import multiprocessing
import os
import pickle
import random
import select
import signal
import subprocess
import threading
import time
import weakref
from collections.abc import Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from types import MappingProxyType, TracebackType
from typing import Any, Literal, get_type_hints

import numpy as np
import pytest
import test_world_rng_bootstrap as bootstrap
import torch

from townlet.exploration import rng_custody as custody


class Owner:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.revision = 0
        self.quarantined = False


class OtherOwner:
    pass


class ChildOwner(Owner):
    pass


class CUDASeam:
    """Finite state/query seam, with no tensor operations or GPU claims."""

    def __init__(self, initialized: bool) -> None:
        self.initialized = initialized
        self.selected = 0
        self.count = 3
        self.calls: list[Any] = []
        self.init_error: BaseException | None = None
        self.query_error: BaseException | None = None
        self.sync_errors: dict[int, BaseException] = {}
        self.init_hook: Any = None
        self.sync_hook: Any = None

    def is_initialized(self) -> bool:
        self.calls.append("is_initialized")
        if self.query_error is not None:
            raise self.query_error
        return self.initialized

    def init(self) -> None:
        self.calls.append("init")
        if self.init_hook is not None:
            self.init_hook()
        if self.init_error is not None:
            raise self.init_error
        self.initialized = True

    def device_count(self) -> int:
        self.calls.append("device_count")
        return self.count

    def current_device(self) -> int:
        self.calls.append("current_device")
        return self.selected

    def synchronize(self, index: int) -> None:
        self.calls.append(("synchronize", index))
        if self.sync_hook is not None:
            self.sync_hook(index)
        if index in self.sync_errors:
            raise self.sync_errors[index]


class NoCUDA:
    def __getattribute__(self, name: str) -> Any:
        if name == "__class__":
            return object.__getattribute__(self, name)
        raise AssertionError(f"CPU protocol queried CUDA attribute {name}")


@pytest.fixture
def domain() -> Any:
    actual = custody.process_rng_domain()
    assert actual.status()[2] is False
    yield actual
    assert actual.status()[2] is False


@pytest.fixture
def cuda(monkeypatch: pytest.MonkeyPatch) -> CUDASeam:
    seam = CUDASeam(True)
    monkeypatch.setattr(custody.torch, "cuda", seam)
    # Each seam represents a fresh simulated runtime; never reset real CUDA.
    monkeypatch.setattr(custody.process_rng_domain(), "_cuda_ready", False, raising=False)
    return seam


def register(domain: Any, owner: object, devices: tuple[int, ...]) -> Any:
    return domain.register(
        owner=owner,
        cuda_devices=devices,
        entrypoints=frozenset({"parent", "ordinary", "prepare", "validate", "install"}),
    )


def contract_fixture(monkeypatch: pytest.MonkeyPatch, post_poison: bool) -> Any:
    """Private finite manifest fixture, never a production issuer/constant."""
    contract = object.__new__(custody.LocalCUDAContract)
    descriptor = custody._LocalCUDADescriptor(
        owner_kind="flat",
        route="test_cuda_leaf",
        input_kind="none",
        rationale="finite CPU seam, no production purity qualification",
        healthy=True,
        post_poison=post_poison,
    )
    record = custody._LocalCUDARecord(
        owner_type=Owner,
        route="test_cuda_leaf",
        input_type=type(None),
        rationale="finite CPU seam, no production purity qualification",
        healthy=True,
        post_poison=post_poison,
    )
    domain = custody.process_rng_domain()
    production = custody._LOCAL_CUDA_CONTRACTS
    real_resolver = domain._resolve_local_cuda_record

    def resolve(*, descriptor: Any) -> Any:
        if descriptor is fixture_descriptor:
            return record
        if any(descriptor is item for item in production.values()):
            return real_resolver(descriptor=descriptor)
        raise ValueError("unexpected finite fixture descriptor")

    fixture_descriptor = descriptor
    monkeypatch.setattr(domain, "_local_cuda_policies", {})
    monkeypatch.setattr(domain, "_resolve_local_cuda_record", resolve)
    monkeypatch.setattr(custody, "_LOCAL_CUDA_CONTRACTS", MappingProxyType({**production, contract: descriptor}))
    return contract


def prepare_token(domain: Any, participant: Any) -> Any:
    with domain.operation(participant=participant, operation_kind="prepare", lineage=None) as operation:
        return domain.current_token(participant=participant, operation=operation)


def validate_token(domain: Any, participant: Any, token: Any) -> None:
    with domain.operation(participant=participant, operation_kind="install", lineage=None) as operation:
        domain.validate_current(token=token, operation=operation)


def syncs(cuda: CUDASeam) -> list[int]:
    return [call[1] for call in cuda.calls if isinstance(call, tuple) and call[0] == "synchronize"]


def test_existing_cpu_registration_and_completion_query_no_cuda(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = Owner()
    participant = register(domain, owner, ())
    try:
        with domain.operation(participant=participant, operation_kind="ordinary", lineage=None):
            assert owner.revision == 0
    finally:
        domain.unregister(participant=participant)


def test_existing_released_prepare_install_currentness(domain: Any) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    token = prepare_token(domain, participant)
    validate_token(domain, participant, token)
    domain.unregister(participant=participant)


def test_existing_nested_currency_distinguishes_sibling_from_open_prepare(domain: Any) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    with domain.operation(participant=participant, operation_kind="parent", lineage=None) as parent:
        with domain.operation(participant=participant, operation_kind="prepare", lineage=parent):
            inside = domain.current_token(participant=participant, operation=parent)
            with domain.operation(participant=participant, operation_kind="ordinary", lineage=parent):
                pass
            # This is the existing source rule: ordinary inside open prepare is
            # not detected by core currency. Producer owner revision is separate.
            domain.validate_current(token=inside, operation=parent)
        with domain.operation(participant=participant, operation_kind="ordinary", lineage=parent):
            pass
        with pytest.raises(ValueError, match="stale"):
            domain.validate_current(token=inside, operation=parent)
    domain.unregister(participant=participant)


def test_public_required_signatures_and_empty_manifest(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    expected = {
        "operation": ("participant", "operation_kind", "lineage"),
        "device_operation": ("participant", "operation_kind", "lineage", "cuda_devices"),
        "admission": ("lineage",),
        "local_cuda_access": ("participant", "contract"),
    }
    for name, names in expected.items():
        parameters = list(inspect.signature(getattr(custody.AmbientRNGDomain, name)).parameters.values())[1:]
        assert tuple(parameter.name for parameter in parameters) == names
        assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters)
        assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    for name, names in {"resolve_cuda": ("device",), "complete": ("cuda_devices",), "report_failure": ("error",)}.items():
        parameters = list(inspect.signature(getattr(custody.LocalCUDAGate, name)).parameters.values())[1:]
        assert tuple(parameter.name for parameter in parameters) == names
        assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
        assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters)
    assert len(inspect.signature(custody.LocalCUDAGate.completion_failed).parameters) == 1
    admission_methods = {"resolve_cuda": ("device",), "enroll": ("participant", "cuda_devices"), "report_failure": ("error",)}
    for name, names in admission_methods.items():
        parameters = list(inspect.signature(getattr(custody.RNGAdmission, name)).parameters.values())[1:]
        assert tuple(parameter.name for parameter in parameters) == names
        assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
        expected_kind = inspect.Parameter.POSITIONAL_OR_KEYWORD if name == "resolve_cuda" else inspect.Parameter.KEYWORD_ONLY
        assert all(parameter.kind is expected_kind for parameter in parameters)
    assert isinstance(custody._LOCAL_CUDA_CONTRACTS, MappingProxyType)
    # Preserve the historical node ID while replacing its stage-specific oracle.
    descriptor_type = custody._LocalCUDADescriptor
    policies = {
        "REPLAY_BUFFER_PUSH_CUDA": ("flat", "push", "tensor"),
        "REPLAY_BUFFER_PUSH_RECORDED_CUDA": ("flat", "push_recorded", "tensor"),
        "REPLAY_BUFFER_READINESS_CUDA": ("flat", "readiness", "request"),
        "REPLAY_BUFFER_SERIALIZE_CUDA": ("flat", "serialize", "none"),
        "REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA": ("flat", "validate_serialized", "mapping"),
        "REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA": ("flat", "load_for_mode", "mapping"),
        "REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA": ("flat", "historical_archives", "none"),
        "REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA": ("flat", "install_historical_archive", "archive"),
        "PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA": ("per", "push", "tensor"),
        "PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA": ("per", "push_recorded", "tensor"),
        "PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA": ("per", "declare_unconstrained_action_dim", "integer"),
        "PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA": ("per", "readiness", "request"),
        "PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA": ("per", "serialize", "none"),
        "PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA": ("per", "validate_serialized", "mapping"),
        "PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA": ("per", "historical_archives", "none"),
        "PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA": ("per", "install_historical_archive", "archive"),
        "PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA": ("per", "update_priorities", "indices"),
        "PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA": ("per", "update_unit_priorities", "indices"),
    }
    contracts = [getattr(custody, name) for name in policies]
    assert len({id(contract) for contract in contracts}) == 18
    assert set(custody._LOCAL_CUDA_CONTRACTS) == set(contracts)
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    from townlet.training.historical_checkpoint import HistoricalReplayArchive
    from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
    from townlet.training.replay_buffer import ReplayBuffer
    from townlet.training.replay_contract import ReplayRequest

    owners = {"flat": ReplayBuffer, "per": PrioritizedReplayBuffer}
    inputs = {
        "tensor": torch.Tensor,
        "request": ReplayRequest,
        "mapping": Mapping,
        "archive": HistoricalReplayArchive,
        "none": type(None),
        "integer": int,
        "indices": np.ndarray,
    }
    monkeypatch.setattr(domain, "_local_cuda_policies", {})
    real_resolver = domain._resolve_local_cuda_record
    resolutions: list[int] = []

    def count_resolution(*, descriptor: Any) -> Any:
        resolutions.append(id(descriptor))
        return real_resolver(descriptor=descriptor)

    monkeypatch.setattr(domain, "_resolve_local_cuda_record", count_resolution)
    before = (domain.status(), domain._currency, domain._cuda_ready)
    resolved = []
    with domain._lock:
        for name, (owner_kind, route, input_kind) in policies.items():
            contract = getattr(custody, name)
            assert type(contract) is custody.LocalCUDAContract
            descriptor = custody._LOCAL_CUDA_CONTRACTS[contract]
            assert type(descriptor) is descriptor_type
            assert (descriptor.owner_kind, descriptor.route, descriptor.input_kind) == (owner_kind, route, input_kind)
            assert type(descriptor.rationale) is str and descriptor.rationale
            assert descriptor.healthy is True and descriptor.post_poison is False
            with pytest.raises(AttributeError):
                descriptor.route = "forged"
            policy = domain._local_cuda_policy(contract=contract)
            assert type(policy) is custody._LocalCUDARecord and policy.owner_type is owners[owner_kind]
            assert policy.input_type is inputs[input_kind] and policy.route == route and policy.rationale == descriptor.rationale
            assert policy.healthy is True and policy.post_poison is False
            assert domain._local_cuda_policies[contract] == (descriptor, policy)
            assert domain._local_cuda_policies[contract][0] is descriptor
            assert domain._local_cuda_policies[contract][1] is policy
            assert domain._local_cuda_policy(contract=contract) is policy
            resolved.append(policy)
        assert len(domain._local_cuda_policies) == len({id(policy) for policy in resolved}) == 18
        assert len(resolutions) == len(set(resolutions)) == 18
    assert (domain.status(), domain._currency, domain._cuda_ready) == before


def test_local_descriptor_cache_keeps_active_gate_binding(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = contract_fixture(monkeypatch, False)
    canonical_contract = custody.REPLAY_BUFFER_SERIALIZE_CUDA
    descriptor = custody._LOCAL_CUDA_CONTRACTS[canonical_contract]
    raw_resolver = custody.AmbientRNGDomain._resolve_local_cuda_record
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    before = local_policy_state(domain)
    for action in (lambda: domain._local_cuda_policy(contract=canonical_contract), lambda: raw_resolver(domain, descriptor=descriptor)):
        with pytest.raises(RuntimeError):
            action()
    assert local_policy_state(domain) == before
    owner = Owner()
    participant = register(domain, owner, ())
    try:
        with domain.local_cuda_access(participant=participant, contract=contract) as gate:
            cached = domain._local_cuda_policies[contract]
            active = domain._gates[gate]
            with pytest.raises(RuntimeError):
                with domain.local_cuda_access(participant=participant, contract=contract):
                    pytest.fail("nested public local gate admitted")
            canonical = domain._local_cuda_policy(contract=canonical_contract)
            assert canonical is domain._local_cuda_policies[canonical_contract][1] and canonical is not cached[1]
            assert domain._local_cuda_policies[contract] is cached and active.policy is cached[1] and active.owner is owner

            def no_resolution(*, descriptor: Any) -> Any:
                raise AssertionError("live gate authentication resolved a policy")

            with monkeypatch.context() as patch:
                patch.setattr(domain, "_resolve_local_cuda_record", no_resolution)
                for corruption in ("removed_descriptor", "replaced_descriptor", "replaced_policy"):
                    with monkeypatch.context() as altered:
                        if corruption == "replaced_policy":
                            altered.setattr(
                                domain, "_local_cuda_policies", {**domain._local_cuda_policies, contract: (cached[0], copy.copy(cached[1]))}
                            )
                        else:
                            manifest = dict(custody._LOCAL_CUDA_CONTRACTS)
                            if corruption == "removed_descriptor":
                                del manifest[contract]
                            else:
                                manifest[contract] = copy.copy(cached[0])
                            altered.setattr(custody, "_LOCAL_CUDA_CONTRACTS", MappingProxyType(manifest))
                        with pytest.raises(ValueError):
                            gate.completion_failed()
                    assert gate.completion_failed() is False and active.policy is cached[1]
                with gate.complete(cuda_devices=()):
                    pass
                assert gate.completion_failed() is False
    finally:
        domain.unregister(participant=participant)


@pytest.mark.parametrize("name", ["RNGAdmission", "LocalCUDAGate", "LocalCUDAContract"])
def test_new_capabilities_have_no_public_constructor(name: str) -> None:
    capability_type = getattr(custody, name)
    with pytest.raises(TypeError):
        capability_type()


def test_idle_admission_is_not_lineage_and_escaped_gate_refuses(domain: Any) -> None:
    with domain.admission(lineage=None) as gate:
        assert not isinstance(gate, custody.RNGOperation)
        for copier in (copy.copy, copy.deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                copier(gate)
    with pytest.raises((ValueError, RuntimeError)):
        gate.resolve_cuda(torch.device("cuda"))
    with pytest.raises((ValueError, RuntimeError)):
        gate.report_failure(error=RuntimeError("expired must not poison"))


@pytest.mark.parametrize("lineage", [object(), False, "operation"])
def test_admission_rejects_fabricated_lineage(domain: Any, lineage: object) -> None:
    with pytest.raises((ValueError, RuntimeError)):
        with domain.admission(lineage=lineage):
            pytest.fail("foreign lineage yielded")


def test_gate_lineage_and_active_enrollment_bootstrap_rules(domain: Any, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    cuda.initialized = False
    with domain.operation(participant=participant, operation_kind="parent", lineage=None) as parent:
        with pytest.raises((ValueError, RuntimeError)):
            with domain.admission(lineage=None):
                pytest.fail("missing lineage laundered")
        with domain.admission(lineage=parent) as gate:
            with pytest.raises(RuntimeError):
                gate.resolve_cuda(torch.device("cuda"))
            with pytest.raises(RuntimeError):
                gate.enroll(participant=participant, cuda_devices=())
        assert "init" not in cuda.calls
    with pytest.raises((ValueError, RuntimeError)):
        with domain.admission(lineage=parent):
            pytest.fail("expired lineage yielded")
    domain.unregister(participant=participant)


def test_initialized_resolve_and_noop_enroll_preserve_real_token(domain: Any, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, (1,))
    token = prepare_token(domain, participant)
    generation, revision, _ = domain.status()
    with domain.admission(lineage=None) as gate:
        assert gate.resolve_cuda(torch.device("cuda:1")) == 1
        gate.enroll(participant=participant, cuda_devices=(1,))
    assert domain.status()[:2] == (generation, revision)
    assert "init" not in cuda.calls
    validate_token(domain, participant, token)
    domain.unregister(participant=participant)


def test_actual_expansion_keeps_participant_owner_and_invalidates_token(domain: Any, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, (0,))
    token = prepare_token(domain, participant)
    original = domain._members[participant]
    generation, revision, _ = domain.status()
    with domain.admission(lineage=None) as gate:
        gate.enroll(participant=participant, cuda_devices=(1,))
        assert domain._members[participant].cuda_devices == (0, 1)
        assert domain._members[participant].owner is original.owner
        assert domain._members[participant].entrypoints is original.entrypoints
    assert domain.status()[:2] == (generation + 1, revision)
    with pytest.raises(ValueError, match="membership"):
        validate_token(domain, participant, token)
    domain.unregister(participant=participant)


@pytest.mark.parametrize("devices", [(1, 0), (0, 0), (-1,), (True,), [0], (3,)])
def test_invalid_enrollment_is_atomic(domain: Any, cuda: CUDASeam, devices: Any) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    before = domain.status()
    with domain.admission(lineage=None) as gate:
        with pytest.raises(ValueError):
            gate.enroll(participant=participant, cuda_devices=devices)
    assert domain.status() == before
    assert domain._members[participant].cuda_devices == ()
    domain.unregister(participant=participant)


@pytest.mark.parametrize("device", [torch.device("cpu"), "cuda", object()])
def test_structurally_invalid_resolve_precedes_cuda_queries(domain: Any, monkeypatch: pytest.MonkeyPatch, device: Any) -> None:
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    with domain.admission(lineage=None) as gate:
        with pytest.raises((ValueError, TypeError)):
            gate.resolve_cuda(device)


@pytest.mark.parametrize("initialized", [False, True])
def test_invalid_index_before_or_after_init_keeps_exact_phase(domain: Any, cuda: CUDASeam, initialized: bool) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    token = prepare_token(domain, participant)
    cuda.initialized = initialized
    revision = domain.status()[1]
    with domain.admission(lineage=None) as gate:
        with pytest.raises(ValueError):
            gate.resolve_cuda(torch.device("cuda:9"))
    assert cuda.calls.count("init") == int(not initialized)
    assert domain.status()[1] == revision
    assert domain.status()[2] is False
    assert domain._members[participant].cuda_devices == ()
    if initialized:
        validate_token(domain, participant, token)
    else:
        with pytest.raises(ValueError, match="stale"):
            validate_token(domain, participant, token)
        assert domain._cuda_ready is True
    domain.unregister(participant=participant)


def test_first_init_invalidates_without_operation_revision_and_dynamic_selection(domain: Any, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    token = prepare_token(domain, participant)
    cuda.initialized = False
    revision = domain.status()[1]
    currency = domain._currency
    with domain.admission(lineage=None) as gate:
        assert gate.resolve_cuda(torch.device("cuda")) == 0
        assert domain._currency == currency + 1
        assert domain.status()[1] == revision
        gate.enroll(participant=participant, cuda_devices=(0,))
    cuda.selected = 2
    with domain.admission(lineage=None) as gate:
        assert gate.resolve_cuda(torch.device("cuda")) == 2
        gate.enroll(participant=participant, cuda_devices=(2,))
    assert cuda.calls.count("init") == 1
    assert cuda.calls.count("current_device") == 2
    assert domain._members[participant].cuda_devices == (0, 2)
    with pytest.raises(ValueError):
        validate_token(domain, participant, token)
    domain.unregister(participant=participant)


def test_bootstrap_reentry_refused_before_callbacks(domain: Any, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    cuda.initialized = False
    refused: list[str] = []

    def reenter() -> None:
        with pytest.raises(RuntimeError):
            register(domain, OtherOwner(), ())
        refused.append("register")
        with pytest.raises(RuntimeError):
            with domain.operation(participant=participant, operation_kind="ordinary", lineage=None):
                pytest.fail("bootstrap operation reentry")
        refused.append("operation")
        with pytest.raises(RuntimeError):
            with domain.admission(lineage=None) as unrelated:
                unrelated.resolve_cuda(torch.device("cuda"))
        refused.append("resolve")

    cuda.init_hook = reenter
    with domain.admission(lineage=None) as gate:
        gate.resolve_cuda(torch.device("cuda"))
    assert refused == ["register", "operation", "resolve"]
    assert cuda.calls.count("init") == 1
    domain.unregister(participant=participant)


@pytest.mark.parametrize("outer_subset", [False, True])
def test_mixed_operation_completion_union(domain: Any, cuda: CUDASeam, outer_subset: bool) -> None:
    first, second = Owner(), Owner()
    parent_member = register(domain, first, (0, 1))
    child_member = register(domain, second, (1, 2))
    outer = (
        domain.device_operation(participant=parent_member, operation_kind="parent", lineage=None, cuda_devices=(0,))
        if outer_subset
        else domain.operation(participant=parent_member, operation_kind="parent", lineage=None)
    )
    with outer as parent:
        child = (
            domain.operation(participant=child_member, operation_kind="prepare", lineage=parent)
            if outer_subset
            else domain.device_operation(participant=child_member, operation_kind="prepare", lineage=parent, cuda_devices=(2,))
        )
        with child:
            pass
        assert syncs(cuda) == ([1, 2] if outer_subset else [2])
    assert syncs(cuda) == ([1, 2, 0, 1, 2] if outer_subset else [2, 0, 1, 2])
    domain.unregister(participant=parent_member)
    domain.unregister(participant=child_member)


@pytest.mark.parametrize("devices", [(2,), (1, 0), (0, 0), (False,), [0]])
def test_device_operation_rejects_invalid_subset_before_body(domain: Any, cuda: CUDASeam, devices: Any) -> None:
    owner = Owner()
    participant = register(domain, owner, (0, 1))
    with pytest.raises(ValueError):
        with domain.device_operation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=devices):
            pytest.fail("invalid subset reached body")
    assert syncs(cuda) == []
    domain.unregister(participant=participant)


def test_subset_cpu_path_never_queries_cuda(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = Owner()
    participant = register(domain, owner, ())
    with domain.device_operation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=()):
        pass
    domain.unregister(participant=participant)


def test_device_invocation_required_api() -> None:
    # Catches a missing/optional factory input or a context exposing new lineage.
    invocation_type = getattr(custody, "RNGDeviceInvocation")
    factory = getattr(custody.AmbientRNGDomain, "device_invocation")
    parameters = list(inspect.signature(factory).parameters.values())[1:]
    assert tuple(parameter.name for parameter in parameters) == ("participant", "operation_kind", "lineage", "cuda_devices")
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in parameters)
    assert get_type_hints(factory) == {
        "participant": custody.RNGParticipant,
        "operation_kind": str,
        "lineage": custody.RNGOperation | None,
        "cuda_devices": tuple[int, ...],
        "return": invocation_type,
    }
    assert issubclass(invocation_type, AbstractContextManager)
    for name in ("__enter__", "completion_failed"):
        assert tuple(inspect.signature(getattr(invocation_type, name)).parameters) == ("self",)
    assert get_type_hints(invocation_type.__enter__) == {"return": custody.RNGOperation}
    assert get_type_hints(invocation_type.completion_failed) == {"return": bool}
    exit_parameters = list(inspect.signature(invocation_type.__exit__).parameters.values())[1:]
    assert tuple(parameter.name for parameter in exit_parameters) == ("exc_type", "exc_value", "traceback")
    assert all(parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for parameter in exit_parameters)
    assert all(parameter.default is inspect.Parameter.empty for parameter in exit_parameters)
    assert get_type_hints(invocation_type.__exit__) == {
        "exc_type": type[BaseException] | None,
        "exc_value": BaseException | None,
        "traceback": TracebackType | None,
        "return": Literal[False],
    }
    with pytest.raises(TypeError):
        invocation_type()


def test_device_invocation_historical_result_preserves_real_token_and_retirement(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches receipt reads depending on a live operation/member or taking locks.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    participant = register(domain, owner, ())
    try:
        before = (domain.status(), domain._currency)
        invocation = factory(participant=participant, operation_kind="prepare", lineage=None, cuda_devices=())
        assert (domain.status(), domain._currency) == before
        with owner.lock:
            operation = invocation.__enter__()
            try:
                assert type(operation) is custody.RNGOperation
                token = domain.current_token(participant=participant, operation=operation)
                domain.validate_current(token=token, operation=operation)
            finally:
                exit_result = invocation.__exit__(None, None, None)
            assert exit_result is False
            assert invocation.completion_failed() is False
        with pytest.raises(ValueError, match="expired"):
            domain.current_token(participant=participant, operation=operation)
        validate_token(domain, participant, token)
        assert invocation.completion_failed() is False
    finally:
        domain.unregister(participant=participant)
    probe = LockProbe(domain._lock)
    monkeypatch.setattr(domain, "_lock", probe)
    with owner.lock:
        assert invocation.completion_failed() is False
        assert invocation.completion_failed() is False
    assert probe.calls == [0]


def test_device_invocation_lifecycle_refusals_leave_completed_result_stable(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches premature False, reuse, suppression, or a refusal mutating the state.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    participant = register(domain, owner, ())
    try:
        invocation = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
        with pytest.raises(RuntimeError):
            invocation.completion_failed()
        with pytest.raises(RuntimeError):
            invocation.__exit__(None, None, None)
        with invocation:
            with pytest.raises(RuntimeError):
                invocation.completion_failed()
            with pytest.raises(RuntimeError):
                invocation.__enter__()
        for action in (invocation.__enter__, lambda: invocation.__exit__(None, None, None)):
            with pytest.raises(RuntimeError):
                action()
        assert invocation.completion_failed() is False
    finally:
        domain.unregister(participant=participant)


def test_device_invocation_entry_failure_has_no_outcome_or_reuse(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches admission at issuance only, or entry refusal publishing False.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    participant = register(domain, owner, ())
    invocation = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
    domain.unregister(participant=participant)
    with pytest.raises(ValueError):
        with invocation:
            pytest.fail("retired participant reached invocation body")
    with pytest.raises(RuntimeError):
        invocation.completion_failed()
    with pytest.raises(RuntimeError):
        invocation.__enter__()
    with pytest.raises(RuntimeError):
        invocation.__exit__(None, None, None)


def test_device_invocation_issuance_rejects_forged_arguments_without_cuda(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches issuance accepting unissued identities or mutable/malformed inputs.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    participant = register(domain, owner, ())
    try:
        valid = {"participant": participant, "operation_kind": "ordinary", "lineage": None, "cuda_devices": ()}
        bad_arguments = (
            ("participant", object.__new__(custody.RNGParticipant)),
            ("participant", object()),
            ("operation_kind", ""),
            ("operation_kind", 1),
            ("lineage", object.__new__(custody.RNGOperation)),
            ("cuda_devices", []),
            ("cuda_devices", (True,)),
            ("cuda_devices", (-1,)),
            ("cuda_devices", (1, 0)),
            ("cuda_devices", (0, 0)),
        )
        before = (domain.status(), domain._currency)
        for name, value in bad_arguments:
            arguments = {**valid, name: value}
            with pytest.raises(ValueError):
                factory(**arguments)
        assert (domain.status(), domain._currency) == before
    finally:
        domain.unregister(participant=participant)


def test_device_invocation_unissued_subclass_and_copy_refuse(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches lookalike/copy authority and public attributes forging a receipt.
    invocation_type = getattr(custody, "RNGDeviceInvocation")
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = Owner()
    participant = register(domain, owner, ())

    class InvocationSubclass(invocation_type):
        pass

    try:
        invocation = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
        for copier in (copy.copy, copy.deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                copier(invocation)
        with pytest.raises(TypeError):
            invocation.__init__()
        with pytest.raises(AttributeError):
            invocation.result = False
        for forged in (object.__new__(invocation_type), object.__new__(InvocationSubclass)):
            for action in (forged.__enter__, lambda: forged.__exit__(None, None, None), forged.completion_failed):
                with pytest.raises(ValueError):
                    action()
        with invocation:
            pass
        assert invocation.completion_failed() is False
    finally:
        domain.unregister(participant=participant)


def test_device_invocation_wrong_thread_refuses_before_held_locks(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches authentic methods waiting for exclusion before thread authentication.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    participant = register(domain, owner, ())
    threads: list[threading.Thread] = []
    errors: list[BaseException] = []
    refusals: list[bool] = []
    try:
        invocation = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())

        def check_wrong_thread() -> None:
            done = threading.Event()

            def call_methods() -> None:
                try:
                    for action in (invocation.__enter__, lambda: invocation.__exit__(None, None, None), invocation.completion_failed):
                        with pytest.raises(ValueError):
                            action()
                except BaseException as error:
                    errors.append(error)
                finally:
                    done.set()

            thread = threading.Thread(target=call_methods)
            threads.append(thread)
            thread.start()
            refusals.append(done.wait(2))

        with domain._lock, owner.lock:
            check_wrong_thread()
            with invocation:
                check_wrong_thread()
            check_wrong_thread()
        assert invocation.completion_failed() is False
    finally:
        for thread in threads:
            thread.join(5)
        domain.unregister(participant=participant)
    assert all(not thread.is_alive() for thread in threads)
    assert refusals == [True, True, True]
    assert not errors


def test_device_invocation_unused_handle_does_not_pin_owner(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches eager admission/owner pinning at handle construction.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation
    owner = Owner()
    reference = weakref.ref(owner)
    participant = register(domain, owner, ())
    invocation = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
    del owner
    gc.collect()
    assert reference() is None
    domain.status()
    with pytest.raises(ValueError):
        invocation.__enter__()
    with pytest.raises(RuntimeError):
        invocation.completion_failed()


def test_device_invocation_completed_handle_releases_execution_references(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    # Catches a completed handle retaining its generator, owner, lineage or error.
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    factory = domain.device_invocation

    class BodyError(RuntimeError):
        pass

    def complete() -> tuple[Any, Any, Any, Any]:
        owner = Owner()
        participant = register(domain, owner, ())
        invocation = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
        error = BodyError("body-only failure is not a completion failure")
        try:
            with invocation as operation:
                raise error
        except BodyError as outward:
            assert outward is error
        else:
            pytest.fail("invocation suppressed body exception")
        domain.unregister(participant=participant)
        return invocation, weakref.ref(owner), weakref.ref(operation), weakref.ref(error)

    invocation, owner_reference, operation_reference, error_reference = complete()
    gc.collect()
    assert invocation.completion_failed() is False
    assert owner_reference() is None
    assert operation_reference() is None
    assert error_reference() is None
    invocation_reference = weakref.ref(invocation)
    del invocation
    gc.collect()
    assert invocation_reference() is None


def test_device_invocation_nonempty_completion_matches_existing_operation(
    domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam
) -> None:
    owner = Owner()
    participant = register(domain, owner, (0, 1, 2))
    probe = LockProbe(domain._lock)
    monkeypatch.setattr(domain, "_lock", probe)
    try:
        observed: list[list[int]] = []
        acquisitions: list[int] = []
        for factory in (domain.device_operation, domain.device_invocation):
            cuda.calls.clear()
            context = factory(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=(0, 1, 2))
            before = probe.calls[0]
            with context as operation:
                assert type(operation) is custody.RNGOperation
            observed.append(syncs(cuda))
            acquisitions.append(probe.calls[0] - before)
            if type(context) is custody.RNGDeviceInvocation:
                assert context.completion_failed() is False
        assert observed == [[0, 1, 2], [0, 1, 2]]
        assert acquisitions[0] == acquisitions[1] and acquisitions[0] > 0
    finally:
        domain.unregister(participant=participant)


def test_device_invocation_nested_siblings_keep_lineage_and_receipts(domain: Any, cuda: CUDASeam) -> None:
    owners = [Owner(), Owner(), Owner()]
    members = [register(domain, owner, (0, 1, 2)) for owner in owners]
    try:
        parent = domain.device_invocation(participant=members[0], operation_kind="parent", lineage=None, cuda_devices=(0,))
        with parent as operation:
            children = []
            for member, device in zip(members[1:], (1, 2)):
                child = domain.device_invocation(participant=member, operation_kind="prepare", lineage=operation, cuda_devices=(device,))
                with child as joined:
                    assert joined is operation
                    token = domain.current_token(participant=member, operation=joined)
                    domain.validate_current(token=token, operation=operation)
                assert child.completion_failed() is False
                children.append(child)
            assert len({id(parent), *(id(child) for child in children)}) == 3
            assert syncs(cuda) == [1, 2]
        assert syncs(cuda) == [1, 2, 0, 1, 2]
        with domain.operation(participant=members[0], operation_kind="ordinary", lineage=None):
            pass
        for member in members:
            domain.unregister(participant=member)
        members.clear()
        assert all(child.completion_failed() is False for child in [parent, *children])
    finally:
        for member in members:
            domain.unregister(participant=member)


@pytest.mark.parametrize("route", ["device_operation", "device_invocation"])
def test_device_invocation_nested_currency_preserves_currentness_rules(domain: Any, monkeypatch: pytest.MonkeyPatch, route: str) -> None:
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = Owner()
    participant = register(domain, owner, ())
    contexts = []

    def scope(kind: str, lineage: Any) -> Any:
        context = getattr(domain, route)(participant=participant, operation_kind=kind, lineage=lineage, cuda_devices=())
        contexts.append(context)
        return context

    try:
        with scope("parent", None) as parent:
            with scope("prepare", parent):
                token = domain.current_token(participant=participant, operation=parent)
                with scope("ordinary", parent):
                    pass
                domain.validate_current(token=token, operation=parent)
            with scope("ordinary", parent):
                pass
            with pytest.raises(ValueError, match="stale"):
                domain.validate_current(token=token, operation=parent)
        if route == "device_invocation":
            assert all(context.completion_failed() is False for context in contexts)
    finally:
        domain.unregister(participant=participant)


def test_device_invocation_thread_object_rejects_numeric_alias(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = Owner()
    participant = register(domain, owner, ())
    domain_probe, owner_probe = LockProbe(domain._lock), LockProbe(owner.lock)
    monkeypatch.setattr(domain, "_lock", domain_probe)
    monkeypatch.setattr(owner, "lock", owner_probe)
    handles: list[Any] = []
    errors: list[BaseException] = []

    def issue() -> None:
        try:
            invocation = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
            with invocation:
                pass
            handles.append(invocation)
        except BaseException as error:
            errors.append(error)

    issuer = threading.Thread(target=issue)
    issuer.start()
    issuer.join(5)
    assert not issuer.is_alive() and not errors
    assert issuer.ident is not None and len(handles) == 1

    class NumericAlias:
        def get_ident(self) -> int:
            assert issuer.ident is not None
            return issuer.ident

        def __getattr__(self, name: str) -> Any:
            return getattr(threading, name)

    done = threading.Event()

    def refuse() -> None:
        try:
            assert threading.current_thread() is not issuer
            assert custody.threading.current_thread() is threading.current_thread()
            assert custody.threading.get_ident() == issuer.ident
            for action in (handles[0].__enter__, lambda: handles[0].__exit__(None, None, None), handles[0].completion_failed):
                with pytest.raises(ValueError):
                    action()
        except BaseException as error:
            errors.append(error)
        finally:
            done.set()

    receiver = threading.Thread(target=refuse)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(custody, "threading", NumericAlias())
            with domain._lock, owner.lock:
                domain_probe.calls[0] = owner_probe.calls[0] = 0
                receiver.start()
                refused_before_unlock = done.wait(2)
                assert domain_probe.calls == owner_probe.calls == [0]
            receiver.join(5)
        assert refused_before_unlock and not receiver.is_alive() and not errors
    finally:
        if receiver.ident is not None:
            receiver.join(5)
        domain.unregister(participant=participant)


def test_device_invocation_registry_lifetime_and_lock_paths(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam) -> None:
    owner = Owner()
    participant = register(domain, owner, (0,))
    domain_probe, owner_probe = LockProbe(domain._lock), LockProbe(owner.lock)
    monkeypatch.setattr(domain, "_lock", domain_probe)
    monkeypatch.setattr(owner, "lock", owner_probe)
    phases: list[str] = []
    invocation = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=(0,))
    identity, reference = id(invocation), weakref.ref(invocation)
    record = domain._invocations[invocation]
    assert domain_probe.calls == owner_probe.calls == [0]
    assert record.thread is threading.current_thread() and record.state == "issued"
    assert record.participant is participant and record.operation_kind == "ordinary" and record.lineage is None
    assert record.cuda_devices == (0,) and record.context is None and record.failed_completion is True
    original_query = cuda.is_initialized

    def entering() -> bool:
        assert record.state == "entering" and record.context is not None
        snapshot = invocation_state(domain)
        row = next(row for row in snapshot if row[0] == identity)
        assert row[10][2] == id(record)
        counts = (domain_probe.calls[0], owner_probe.calls[0])
        with pytest.raises(RuntimeError):
            reference().completion_failed()
        assert invocation_state(domain) == snapshot and counts == (domain_probe.calls[0], owner_probe.calls[0])
        phases.append("entering")
        return original_query()

    def exiting(index: int) -> None:
        assert index == 0 and record.state == "active" and record.context is None
        before = invocation_state(domain)
        counts = (domain_probe.calls[0], owner_probe.calls[0])
        with pytest.raises(RuntimeError):
            reference().completion_failed()
        assert invocation_state(domain) == before and counts == (domain_probe.calls[0], owner_probe.calls[0])
        phases.append("exiting")

    monkeypatch.setattr(cuda, "is_initialized", entering)
    cuda.sync_hook = exiting
    try:
        with owner.lock:
            with invocation:
                assert record.state == "active" and record.context is not None
                phases.append("active")
                before = invocation_state(domain)
                counts = (domain_probe.calls[0], owner_probe.calls[0])
                with pytest.raises(RuntimeError):
                    invocation.completion_failed()
                assert invocation_state(domain) == before and counts == (domain_probe.calls[0], owner_probe.calls[0])
            domain_probe.calls[0] = owner_probe.calls[0] = 0
            assert invocation.completion_failed() is False
            assert invocation.completion_failed() is False
            assert domain_probe.calls == owner_probe.calls == [0]
        assert phases == ["entering", "active", "exiting"]
        assert record.failed_completion is False
        assert (record.state, record.participant, record.operation_kind, record.lineage, record.cuda_devices, record.context) == (
            "exited",
            None,
            None,
            None,
            (),
            None,
        )
        failed = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=(1,))
        with pytest.raises(ValueError):
            failed.__enter__()
        failed_record = domain._invocations[failed]
        assert failed_record.state == "entry_failed" and failed_record.failed_completion is True
        assert (
            failed_record.participant,
            failed_record.operation_kind,
            failed_record.lineage,
            failed_record.cuda_devices,
            failed_record.context,
        ) == (None, None, None, (), None)
        domain_probe.calls[0] = owner_probe.calls[0] = 0
        before = invocation_state(domain)
        for action in (invocation.__enter__, lambda: reference().__exit__(None, None, None), failed.completion_failed):
            with pytest.raises(RuntimeError):
                action()
        del action
        assert invocation_state(domain) == before and domain_probe.calls == owner_probe.calls == [0]
        failed_reference = weakref.ref(failed)
        ids = {id(invocation), id(failed)}
        del invocation, failed
        gc.collect()
        assert reference() is failed_reference() is None
        assert all(row[0] not in ids for row in invocation_state(domain))
    finally:
        domain.unregister(participant=participant)


def test_actual_gate_blocks_other_thread_and_cross_thread_capability(domain: Any) -> None:
    started, entered = threading.Event(), threading.Event()
    errors: list[BaseException] = []
    with domain.admission(lineage=None) as gate:

        def competitor() -> None:
            started.set()
            try:
                with pytest.raises((ValueError, RuntimeError)):
                    gate.resolve_cuda(torch.device("cuda"))
                with domain.admission(lineage=None):
                    entered.set()
            except BaseException as error:
                errors.append(error)

        thread = threading.Thread(target=competitor)
        thread.start()
        assert started.wait(2)
        assert not entered.wait(0.05)
    thread.join(5)
    assert not thread.is_alive()
    assert not errors
    assert entered.is_set()


@pytest.mark.parametrize("owner_type", [OtherOwner, ChildOwner, type("Owner", (), {"__module__": __name__})])
def test_local_contract_rejects_unrelated_subclass_and_name_spoof(domain: Any, monkeypatch: pytest.MonkeyPatch, owner_type: type) -> None:
    contract = contract_fixture(monkeypatch, False)
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    owner = owner_type()
    participant = register(domain, owner, ())
    with pytest.raises((ValueError, RuntimeError)):
        with domain.local_cuda_access(participant=participant, contract=contract):
            pytest.fail("wrong exact owner class yielded")
    domain.unregister(participant=participant)


@pytest.mark.parametrize("contract", [object(), "test_cuda_leaf", True])
def test_local_contract_cannot_be_caller_declared(domain: Any, contract: Any) -> None:
    owner = Owner()
    participant = register(domain, owner, ())
    with pytest.raises((ValueError, RuntimeError, TypeError)):
        with domain.local_cuda_access(participant=participant, contract=contract):
            pytest.fail("unissued contract yielded")
    domain.unregister(participant=participant)


def test_local_unissued_identity_and_unknown_participant_refuse_before_cuda(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    issued = contract_fixture(monkeypatch, False)
    unissued = object.__new__(custody.LocalCUDAContract)
    owner = Owner()
    participant = register(domain, owner, ())
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    for member, contract in ((participant, unissued), (object(), issued)):
        with pytest.raises((ValueError, RuntimeError)):
            with domain.local_cuda_access(participant=member, contract=contract):
                pytest.fail("unissued identity or member yielded")
    domain.unregister(participant=participant)


def test_local_gate_live_thread_copy_unissued_and_expired_authentication(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    body_calls: list[str] = []

    def methods_refuse(gate: Any) -> None:
        with pytest.raises((ValueError, RuntimeError)):
            gate.resolve_cuda(device=torch.device("cuda"))
        with pytest.raises((ValueError, RuntimeError)):
            with gate.complete(cuda_devices=()):
                body_calls.append("invalid completion")
        with pytest.raises((ValueError, RuntimeError)):
            gate.report_failure(error=RuntimeError("invalid reporter must not poison"))
        with pytest.raises((ValueError, RuntimeError)):
            gate.completion_failed()

    done = threading.Event()
    errors: list[BaseException] = []
    with domain.local_cuda_access(participant=participant, contract=contract) as live:
        for copier in (copy.copy, copy.deepcopy, pickle.dumps):
            with pytest.raises(TypeError):
                copier(live)

        def another_thread() -> None:
            try:
                methods_refuse(live)
            except BaseException as error:
                errors.append(error)
            finally:
                done.set()

        thread = threading.Thread(target=another_thread)
        thread.start()
        refused_while_live = done.wait(2)
    thread.join(5)
    assert not thread.is_alive()
    assert refused_while_live, "wrong-thread local methods blocked on held domain instead of refusing"
    assert not errors
    methods_refuse(live)
    methods_refuse(object.__new__(custody.LocalCUDAGate))
    assert not body_calls
    assert not domain.status()[2]
    domain.unregister(participant=participant)


def test_local_empty_completion_queries_no_cuda(domain: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    monkeypatch.setattr(custody.torch, "cuda", NoCUDA())
    with domain.local_cuda_access(participant=participant, contract=contract) as gate:
        with gate.complete(cuda_devices=()):
            pass
        assert not gate.completion_failed()
    domain.unregister(participant=participant)


def test_local_active_parent_refuses_bootstrap(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    cuda.initialized = False
    with domain.operation(participant=participant, operation_kind="parent", lineage=None):
        with domain.local_cuda_access(participant=participant, contract=contract) as gate:
            assert not isinstance(gate, custody.RNGOperation)
            with pytest.raises(RuntimeError):
                gate.resolve_cuda(device=torch.device("cuda"))
    assert "init" not in cuda.calls
    domain.unregister(participant=participant)


def test_local_exact_owner_instances_and_noncopyable_contract(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam) -> None:
    contract = contract_fixture(monkeypatch, False)
    for copier in (copy.copy, copy.deepcopy, pickle.dumps):
        with pytest.raises(TypeError):
            copier(contract)
    for owner in (Owner(), Owner()):
        participant = register(domain, owner, ())
        with domain.local_cuda_access(participant=participant, contract=contract) as gate:
            assert gate.resolve_cuda(device=torch.device("cuda:1")) == 1
            with gate.complete(cuda_devices=(1,)):
                pass
            assert gate.completion_failed() is False
        domain.unregister(participant=participant)
    assert syncs(cuda) == [1, 1]


def test_local_completion_body_error_identity_and_no_currency_change(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    token = prepare_token(domain, participant)
    before = (domain.status(), domain._currency)
    error = RuntimeError("body only")
    with domain.local_cuda_access(participant=participant, contract=contract) as gate:
        gate.resolve_cuda(device=torch.device("cuda:2"))
        with owner.lock:
            with pytest.raises(RuntimeError) as raised:
                with gate.complete(cuda_devices=(0, 2)):
                    raise error
            assert raised.value is error
            assert not gate.completion_failed()
    assert syncs(cuda) == [0, 2]
    assert (domain.status(), domain._currency) == before
    validate_token(domain, participant, token)
    domain.unregister(participant=participant)


@pytest.mark.parametrize("devices", [(1, 0), (0, 0), (-1,), (True,), [0], (3,)])
def test_local_completion_validates_before_body(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam, devices: Any) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    with domain.local_cuda_access(participant=participant, contract=contract) as gate:
        gate.resolve_cuda(device=torch.device("cuda:0"))
        with pytest.raises(ValueError):
            with gate.complete(cuda_devices=devices):
                pytest.fail("invalid completion reached body")
    assert syncs(cuda) == []
    domain.unregister(participant=participant)


def test_local_completion_scope_reentry_expiry_and_no_retroactive_device(
    domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam
) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    with domain.local_cuda_access(participant=participant, contract=contract) as gate:
        gate.resolve_cuda(device=torch.device("cuda:0"))
        with gate.complete(cuda_devices=(0,)):
            with pytest.raises((RuntimeError, ValueError)):
                with gate.complete(cuda_devices=(1,)):
                    pytest.fail("overlapping completion yielded")
            with pytest.raises((RuntimeError, ValueError)):
                gate.resolve_cuda(device=torch.device("cuda:1"))
        with pytest.raises((RuntimeError, ValueError)):
            with gate.complete(cuda_devices=(0,)):
                pytest.fail("repeated completion yielded")
    for action in (gate.completion_failed, lambda: gate.resolve_cuda(device=torch.device("cuda:0"))):
        with pytest.raises((RuntimeError, ValueError)):
            action()
    assert syncs(cuda) == [0]
    domain.unregister(participant=participant)


def test_local_parent_token_owner_revision_and_no_enrollment_authority(
    domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam
) -> None:
    contract = contract_fixture(monkeypatch, False)
    owner = Owner()
    participant = register(domain, owner, ())
    with domain.operation(participant=participant, operation_kind="parent", lineage=None) as parent:
        with domain.operation(participant=participant, operation_kind="prepare", lineage=parent):
            token = domain.current_token(participant=participant, operation=parent)
        expected_revision = owner.revision
        before = (domain.status(), domain._currency)
        with domain.local_cuda_access(participant=participant, contract=contract) as gate:
            gate.resolve_cuda(device=torch.device("cuda:0"))
            assert not hasattr(gate, "enroll")
            with owner.lock:
                with gate.complete(cuda_devices=(0,)):
                    owner.revision += 1
        assert (domain.status(), domain._currency) == before
        domain.validate_current(token=token, operation=parent)
        assert owner.revision != expected_revision
    domain.unregister(participant=participant)


def test_local_pin_and_owner_exclusion_through_completion(domain: Any, monkeypatch: pytest.MonkeyPatch, cuda: CUDASeam) -> None:
    contract = contract_fixture(monkeypatch, False)
    holder = [Owner()]
    reference = weakref.ref(holder[0])
    owner_lock = holder[0].lock
    participant = register(domain, holder[0], ())
    attempted, mutated = threading.Event(), threading.Event()

    def mutate() -> None:
        attempted.set()
        with owner_lock:
            mutated.set()

    def check_completion(index: int) -> None:
        assert index == 1
        assert reference() is not None
        assert attempted.wait(2)
        assert not mutated.wait(0.05)

    cuda.sync_hook = check_completion
    with domain.local_cuda_access(participant=participant, contract=contract) as gate:
        gate.resolve_cuda(device=torch.device("cuda:1"))
        with owner_lock:
            holder.clear()
            assert reference() is not None
            with gate.complete(cuda_devices=(1,)):
                thread = threading.Thread(target=mutate)
                thread.start()
        thread.join(5)
        assert not thread.is_alive()
        assert mutated.is_set()
        assert reference() is not None
    assert reference() is None
    domain.status()  # idle retirement of the now unpinned real weak owner


def ambient_snapshot() -> tuple[Any, Any, torch.Tensor]:
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone()


def assert_ambient_unchanged(before: tuple[Any, Any, torch.Tensor]) -> None:
    python, numpy, cpu = before
    assert random.getstate() == python
    actual = np.random.get_state()
    assert actual[0] == numpy[0]
    assert np.array_equal(actual[1], numpy[1])
    assert actual[2:] == numpy[2:]
    assert torch.equal(torch.get_rng_state(), cpu)


INVOCATION_CASES = (
    "invocation_same_error",
    "invocation_child_failure",
    "invocation_parent_failure",
    "invocation_reported_failure",
    "invocation_phase_reference",
    "invocation_phase_failure",
)
PHASE_CASES = ("invocation_phase_reference", "invocation_phase_failure")

CHILD_CASES = (
    "bootstrap_failure",
    "runtime_query_failure",
    "local_completion_single",
    "local_completion_multiple_body",
    "local_completion_duplicate_parent",
    "poison_unknown_ready",
    "poison_ready_qualified",
    "poison_ready_healthy_only",
    "operation_body_completion",
) + INVOCATION_CASES


def child_identity(role: str) -> bool:
    qualified = bootstrap._child_identity(role)
    if qualified:
        output = Path(os.environ["BAC_QUAL_OUTPUT"])
        identity_path = output / f"spawn-identity-{role}.json"
        record = json.loads(identity_path.read_text())
        record["ppid"] = os.getppid()
        record["cuda_core_imports"] = {
            name: str(Path(importlib.import_module(name).__file__).resolve())
            for name in ("townlet.exploration.rng_custody", "test_rng_cuda_admission")
        }
        record["cuda_core_test_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        identity_path.write_text(json.dumps(record, sort_keys=True))
    return qualified


def invocation_case(case: str, domain: Any, cuda: CUDASeam) -> dict[str, Any] | None:
    owners = [Owner(), Owner(), Owner()]
    members = [register(domain, owner, (0, 1, 2)) for owner in owners]
    primary, cleanup = RuntimeError(f"{case} body"), RuntimeError(f"{case} synchronization")
    factory = domain.device_invocation
    phase = None
    if case == "invocation_same_error":
        receipts = []
        for failing in (False, True):
            invocation = factory(participant=members[0], operation_kind="ordinary", lineage=None, cuda_devices=(0,))
            if failing:
                cuda.sync_errors[0] = primary
            with owners[0].lock:
                with pytest.raises(RuntimeError) as raised:
                    with invocation:
                        raise primary
                assert raised.value is primary and invocation.completion_failed() is failing
                assert domain.status()[2] is failing
                receipts.append(invocation)
        assert syncs(cuda) == [0, 0]
        assert [receipt.completion_failed() for receipt in receipts] == [False, True]
    elif case == "invocation_child_failure":
        failures = [0]

        def fail_once(index: int) -> None:
            if index == 1 and failures[0] == 0:
                failures[0] += 1
                raise cleanup

        cuda.sync_hook = fail_once
        parent = factory(participant=members[0], operation_kind="parent", lineage=None, cuda_devices=(0,))
        with pytest.raises(RuntimeError) as raised:
            with parent as lineage:
                child = factory(participant=members[1], operation_kind="prepare", lineage=lineage, cuda_devices=(1,))
                try:
                    with child as joined:
                        assert joined is lineage
                except RuntimeError as error:
                    assert error is cleanup and child.completion_failed() is True
                    sibling = factory(participant=members[2], operation_kind="prepare", lineage=lineage, cuda_devices=(2,))
                    with pytest.raises(RuntimeError, match="poisoned"):
                        with sibling:
                            pytest.fail("poisoned sibling reached body")
                    with pytest.raises(RuntimeError):
                        sibling.completion_failed()
                    assert domain._invocations[sibling].state == "entry_failed"
                    raise
        assert raised.value is cleanup and failures == [1]
        assert child is not parent and child.completion_failed() is True and parent.completion_failed() is False
        assert syncs(cuda) == [1, 0, 1]
    elif case == "invocation_parent_failure":
        attempted, mutated = threading.Event(), threading.Event()
        events: list[str] = []
        errors: list[BaseException] = []
        seen = [0]

        def contend() -> None:
            try:
                attempted.set()
                with owners[0].lock:
                    events.append("competitor")
                    mutated.set()
            except BaseException as error:
                errors.append(error)

        def fail_parent(index: int) -> None:
            if index == 2:
                seen[0] += 1
                if seen[0] == 2:
                    assert attempted.wait(2) and not mutated.is_set()
                    events.append("completion")
                    raise cleanup

        cuda.sync_hook = fail_parent
        parent = factory(participant=members[0], operation_kind="parent", lineage=None, cuda_devices=(0,))
        thread = threading.Thread(target=contend)
        children = []
        try:
            with owners[0].lock:
                with pytest.raises(RuntimeError) as raised:
                    with parent as lineage:
                        for member, index in zip(members[1:], (1, 2)):
                            child = factory(participant=member, operation_kind="prepare", lineage=lineage, cuda_devices=(index,))
                            with child as joined:
                                assert joined is lineage
                            assert child.completion_failed() is False
                            children.append(child)
                        thread.start()
                        assert attempted.wait(2)
                assert raised.value is cleanup and parent.completion_failed() is True
                assert all(child.completion_failed() is False for child in children)
                assert not mutated.is_set()
                events.append("read")
        finally:
            if thread.ident is not None:
                thread.join(5)
        assert not thread.is_alive() and not errors and mutated.is_set()
        assert events == ["completion", "read", "competitor"] and syncs(cuda) == [1, 2, 0, 1, 2]
    elif case == "invocation_reported_failure":
        invalid = factory(participant=members[0], operation_kind="ordinary", lineage=None, cuda_devices=(3,))
        with pytest.raises(ValueError):
            with invalid:
                pytest.fail("out-of-subset invocation entered")
        with pytest.raises(RuntimeError):
            invalid.completion_failed()
        assert syncs(cuda) == [] and domain._invocations[invalid].state == "entry_failed"
        invocation = factory(participant=members[0], operation_kind="ordinary", lineage=None, cuda_devices=(0,))
        with pytest.raises(RuntimeError) as raised:
            with invocation as lineage:
                with domain.admission(lineage=lineage) as gate:
                    gate.report_failure(error=primary)
                raise primary
        assert raised.value is primary and invocation.completion_failed() is False and syncs(cuda) == [0]
        refused = factory(participant=members[0], operation_kind="ordinary", lineage=None, cuda_devices=())
        with pytest.raises(RuntimeError, match="poisoned"):
            refused.__enter__()
        with pytest.raises(RuntimeError):
            refused.completion_failed()
    else:
        assert case in PHASE_CASES
        cuda.sync_errors[1] = cleanup
        factory = domain.device_operation if case == "invocation_phase_reference" else domain.device_invocation
        invocation = factory(participant=members[0], operation_kind="ordinary", lineage=None, cuda_devices=(0, 1, 2))
        with pytest.raises(BaseExceptionGroup) as raised:
            with invocation:
                raise primary
        assert len(raised.value.exceptions) == 2
        assert raised.value.exceptions[0] is primary and raised.value.exceptions[1] is cleanup
        outcome = invocation.completion_failed() if case == "invocation_phase_failure" else None
        assert outcome is (True if case == "invocation_phase_failure" else None)
        phase = {
            "devices": [0, 1, 2],
            "synchronize_events": syncs(cuda),
            "exception_labels": ["body", "synchronization"],
            "completion_failed": outcome,
        }
    assert domain.status()[2] is True
    with pytest.raises(RuntimeError, match="poisoned"):
        with domain.admission(lineage=None):
            pytest.fail("poisoned invocation child admitted work")
    with pytest.raises(RuntimeError, match="poisoned"):
        with domain.operation(participant=members[0], operation_kind="ordinary", lineage=None):
            pytest.fail("poisoned invocation child entered operation")
    return phase


def poison_case(case: str, domain: Any, cuda: CUDASeam, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any] | None:
    if case in INVOCATION_CASES:
        return invocation_case(case, domain, cuda)
    owner = Owner()
    participant = register(domain, owner, ())
    primary = RuntimeError(f"{case} primary")
    cleanup = RuntimeError(f"{case} cleanup")
    second = RuntimeError(f"{case} second cleanup")
    if case in {"bootstrap_failure", "runtime_query_failure"}:
        token = prepare_token(domain, participant)
        before_revision, before_currency = domain._revision, domain._currency
        cuda.initialized = False
        if case == "bootstrap_failure":
            cuda.init_error = primary
        else:
            cuda.query_error = primary
        with pytest.raises(RuntimeError) as raised:
            with domain.admission(lineage=None) as gate:
                gate.resolve_cuda(torch.device("cuda"))
        assert raised.value is primary
        assert domain._poison is primary
        assert domain._revision == before_revision
        assert domain._currency == before_currency + int(case == "bootstrap_failure")
        assert domain._tokens[token].currency == before_currency
        assert domain._cuda_ready is False
    elif case == "operation_body_completion":
        with domain.admission(lineage=None) as gate:
            gate.resolve_cuda(torch.device("cuda:0"))
            gate.enroll(participant=participant, cuda_devices=(0,))
        cuda.sync_errors[0] = cleanup
        with pytest.raises(BaseExceptionGroup) as raised:
            with domain.device_operation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=(0,)):
                raise primary
        assert raised.value.exceptions == (primary, cleanup)
        assert domain._poison is cleanup
    elif case == "local_completion_duplicate_parent":
        contract = contract_fixture(monkeypatch, True)
        with domain.admission(lineage=None) as gate:
            gate.resolve_cuda(torch.device("cuda:0"))
            gate.enroll(participant=participant, cuda_devices=(0, 1, 2))
        cuda.sync_errors = {0: primary, 1: primary, 2: second}
        local_calls: list[int] = []
        with pytest.raises(BaseException) as raised:
            with domain.operation(participant=participant, operation_kind="parent", lineage=None):
                with domain.local_cuda_access(participant=participant, contract=contract) as local:
                    with owner.lock:
                        try:
                            with local.complete(cuda_devices=(0, 1, 2)):
                                raise primary
                        finally:
                            owner.quarantined = local.completion_failed()
                            local_calls.extend(syncs(cuda))
        leaves: list[BaseException] = []

        def flatten(error: BaseException) -> None:
            if isinstance(error, BaseExceptionGroup):
                for child in error.exceptions:
                    flatten(child)
            else:
                leaves.append(error)

        flatten(raised.value)
        assert leaves == [primary, second]
        assert domain._poison is primary
        assert owner.quarantined
        assert local_calls == [0, 1, 2]
        assert syncs(cuda)[3:4] == [0]  # authentic parent cleanup also ran; its remaining policy is unchanged
    else:
        contract = contract_fixture(monkeypatch, case != "poison_ready_healthy_only")
        if case.startswith("poison_"):
            if case != "poison_unknown_ready":
                with domain.local_cuda_access(participant=participant, contract=contract) as gate:
                    gate.resolve_cuda(device=torch.device("cuda:0"))
            with domain.admission(lineage=None) as gate:
                gate.report_failure(error=primary)
            before_calls = list(cuda.calls)
            if case == "poison_ready_qualified":
                cuda.selected = 2
                with domain.local_cuda_access(participant=participant, contract=contract) as gate:
                    assert gate.resolve_cuda(device=torch.device("cuda")) == 2
                    with gate.complete(cuda_devices=(2,)):
                        owner.revision += 1
                    gate.report_failure(error=cleanup)
                assert syncs(cuda) == [2]
            else:
                with pytest.raises(RuntimeError):
                    with domain.local_cuda_access(participant=participant, contract=contract):
                        pytest.fail("unqualified poisoned local path admitted")
                assert cuda.calls == before_calls
            assert domain._poison is primary
        else:
            cuda.sync_errors[0] = cleanup
            if case == "local_completion_multiple_body":
                cuda.sync_errors[2] = second
            sync_started, attempted, release_sync, mutated = (threading.Event() for _ in range(4))
            observations: list[bool] = []
            thread_errors: list[BaseException] = []

            def contender() -> None:
                try:
                    assert sync_started.wait(3)
                    attempted.set()
                    with owner.lock:
                        observations.append(owner.quarantined)
                        mutated.set()
                except BaseException as error:
                    thread_errors.append(error)

            def observe_barrier() -> None:
                try:
                    assert sync_started.wait(3)
                    assert attempted.wait(3)
                    assert not mutated.wait(0.05)
                except BaseException as error:
                    thread_errors.append(error)
                finally:
                    release_sync.set()

            def hold_failed_completion(index: int) -> None:
                if index == 0:
                    sync_started.set()
                    assert release_sync.wait(3)
                    assert not mutated.is_set()

            cuda.sync_hook = hold_failed_completion
            mutation_thread = threading.Thread(target=contender)
            observer_thread = threading.Thread(target=observe_barrier)
            with domain.local_cuda_access(participant=participant, contract=contract) as gate:
                gate.resolve_cuda(device=torch.device("cuda:0"))
                with owner.lock:
                    try:
                        with gate.complete(cuda_devices=(0, 1, 2)):
                            mutation_thread.start()
                            observer_thread.start()
                            if case == "local_completion_multiple_body":
                                raise primary
                    except BaseException as error:
                        if case == "local_completion_multiple_body":
                            assert isinstance(error, BaseExceptionGroup)
                            assert error.exceptions == (primary, cleanup, second)
                        else:
                            assert error is cleanup
                    else:
                        pytest.fail("completion failure returned success")
                    finally:
                        assert gate.completion_failed()
                        assert attempted.is_set()
                        assert not mutated.is_set()
                        owner.quarantined = True
                assert owner.quarantined
                assert domain._poison is cleanup
                assert syncs(cuda) == [0, 1, 2]
            mutation_thread.join(5)
            observer_thread.join(5)
            assert not mutation_thread.is_alive()
            assert not observer_thread.is_alive()
            assert not thread_errors
            assert observations == [True]
    assert domain.status()[2]
    with pytest.raises(RuntimeError):
        with domain.admission(lineage=None):
            pytest.fail("poisoned admission yielded")
    with pytest.raises(RuntimeError):
        with domain.operation(participant=participant, operation_kind="ordinary", lineage=None):
            pytest.fail("poisoned operation yielded")
    # CPU local work remains owner-only and does not heal common poison.
    with owner.lock:
        owner.revision += 1
    assert domain.status()[2]
    return None


def cuda_core_child(queue: Any, case: str) -> None:
    role = f"cuda_core_{case}"
    qualified = child_identity(role)
    domain = custody.process_rng_domain()
    assert domain.status()[2] is False
    with pytest.MonkeyPatch.context() as monkeypatch:
        cuda = CUDASeam(True)
        monkeypatch.setattr(custody.torch, "cuda", cuda)
        phase = poison_case(case, domain, cuda, monkeypatch)
        if phase is not None and qualified:
            manifest_bytes = Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()
            manifest = json.loads(manifest_bytes)
            assert manifest["base_commit"] == os.environ["BAC_QUAL_SHA"]
            assert manifest["candidate_tree"] == os.environ["BAC_QUAL_TREE"]
            record = {
                "schema": "cuda-core-invocation-phase-v1",
                "role": role,
                "case": case,
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "base_commit": manifest["base_commit"],
                "candidate_tree": manifest["candidate_tree"],
                "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                "source_sha256": {
                    "townlet.exploration.rng_custody": hashlib.sha256(Path(custody.__file__).read_bytes()).hexdigest(),
                    "test_rng_cuda_admission": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                },
                **phase,
            }
            with (Path(os.environ["BAC_QUAL_OUTPUT"]) / f"invocation-phase-{role}.json").open("x") as stream:
                json.dump(record, stream, sort_keys=True)
    queue.put((f"cuda core {case} fail closed", os.getpid(), os.getppid(), qualified))


@pytest.mark.parametrize("case", CHILD_CASES)
def test_isolated_poison_protocol(case: str) -> None:
    before = ambient_snapshot()
    parent_pid = os.getpid()
    qualified = bootstrap._qualification_active()
    role = f"cuda_core_{case}"
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=cuda_core_child, args=(queue, case), name=role)
    try:
        process.start()
        process.join(90)
        assert not process.is_alive()
        assert process.exitcode == 0
        message, queued_pid, queued_ppid, child_qualified = queue.get(timeout=5)
        assert message == f"cuda core {case} fail closed"
        assert queued_pid == process.pid
        assert queued_ppid == parent_pid
        assert child_qualified is qualified
        if qualified:
            output = Path(os.environ["BAC_QUAL_OUTPUT"])
            manifest_hash = hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest()
            phase_binding = {}
            if case in PHASE_CASES:
                phase_binding["invocation_phase_sha256"] = hashlib.sha256(
                    (output / f"invocation-phase-{role}.json").read_bytes()
                ).hexdigest()
            with (output / f"spawn-observation-{role}.json").open("x") as stream:
                json.dump(
                    {
                        "process_pid": process.pid,
                        "queued_pid": queued_pid,
                        "parent_pid": parent_pid,
                        "queued_ppid": queued_ppid,
                        "exitcode": process.exitcode,
                        "qualified": qualified,
                        "message": message,
                        "manifest_sha256": manifest_hash,
                        **phase_binding,
                    },
                    stream,
                    sort_keys=True,
                )
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        assert not process.is_alive()
        queue.close()
        queue.join_thread()
        process.close()
    assert custody.process_rng_domain().status()[2] is False
    assert_ambient_unchanged(before)


class LockProbe:
    """Forward every observed acquisition to the same genuine RLock."""

    def __init__(self, actual: Any) -> None:
        self.actual = actual
        self.calls = [0]

    def acquire(self, *args: Any, **kwargs: Any) -> Any:
        self.calls[0] += 1
        return self.actual.acquire(*args, **kwargs)

    def release(self) -> None:
        self.actual.release()

    def __enter__(self) -> LockProbe:
        self.acquire()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.release()

    def _is_owned(self) -> bool:
        return self.actual._is_owned()

    def _acquire_restore(self, state: Any) -> Any:
        self.calls[0] += 1
        return self.actual._acquire_restore(state)

    def _release_save(self) -> Any:
        return self.actual._release_save()


class ForbiddenCUDA:
    def __init__(self, counter: list[int]) -> None:
        self.counter = counter

    def __getattribute__(self, name: str) -> Any:
        if name == "__class__":
            return object.__getattribute__(self, name)
        counter = object.__getattribute__(self, "counter")
        counter[0] += 1
        raise AssertionError(f"fork guard reached forbidden CUDA accessor {name}")


def invocation_state(domain: Any) -> tuple[Any, ...]:
    rows = []
    for key, record in domain._invocations.items():
        generator = getattr(record.context, "gen", None)
        frame = getattr(generator, "gi_frame", None)
        execution = (id(generator), id(frame), id(frame.f_locals.get("completion")) if frame is not None else id(None))
        rows.append(
            (
                id(key),
                id(record),
                id(record.thread),
                record.state,
                id(record.participant),
                record.operation_kind,
                id(record.lineage),
                record.cuda_devices,
                id(record.context),
                record.failed_completion,
                execution,
            )
        )
    return tuple(rows)


def local_policy_state(domain: Any) -> tuple[Any, ...]:
    manifest = custody._LOCAL_CUDA_CONTRACTS
    return (
        tuple(
            (
                id(contract),
                id(descriptor),
                descriptor.owner_kind,
                descriptor.route,
                descriptor.input_kind,
                descriptor.rationale,
                descriptor.healthy,
                descriptor.post_poison,
            )
            for contract, descriptor in manifest.items()
        ),
        tuple(
            (
                id(contract),
                id(descriptor),
                id(policy),
                id(policy.owner_type),
                policy.route,
                id(policy.input_type),
                policy.rationale,
                policy.healthy,
                policy.post_poison,
                descriptor is manifest.get(contract),
            )
            for contract, (descriptor, policy) in domain._local_cuda_policies.items()
        ),
        tuple(id(contract) for contract in manifest if contract not in domain._local_cuda_policies),
    )


def guard_state(domain: Any) -> tuple[Any, ...]:
    return (
        domain._pid,
        domain._generation,
        domain._revision,
        domain._currency,
        domain._ambient_revision,
        id(domain._poison),
        tuple(
            (id(key), id(member), id(member.owner), member.cuda_devices, id(member.entrypoints)) for key, member in domain._members.items()
        ),
        tuple(
            (
                id(key),
                id(operation),
                operation.thread,
                operation.generation,
                operation.revision,
                tuple(sorted(id(participant) for participant in operation.participants)),
                tuple(operation.kinds),
                tuple(id(pin) for pin in operation.pins),
                tuple(sorted(operation.devices)),
                tuple(id(token) for token in operation.issued),
                tuple(id(error) for error in operation.reported),
            )
            for key, operation in domain._operations.items()
        ),
        tuple(
            (
                id(key),
                id(current),
                id(current.participant),
                id(current.operation),
                current.generation,
                current.revision,
                current.currency,
            )
            for key, current in domain._tokens.items()
        ),
        domain._cuda_ready,
        domain._cuda_busy,
        id(domain._local.__dict__.get("operation")),
        tuple(
            (
                id(key),
                id(gate),
                gate.thread,
                id(gate.lineage),
                id(gate.participant),
                id(gate.owner),
                id(gate.contract),
                id(gate.policy),
                tuple(id(pin) for pin in gate.pins),
                gate.completion,
                gate.failed_completion,
            )
            for key, gate in domain._gates.items()
        ),
        invocation_state(domain),
        local_policy_state(domain),
    )


def fork_guard_grandchild(
    trial: str,
    actions: dict[str, Any],
    domain: Any,
    domain_lock: LockProbe,
    owner_lock: LockProbe,
    cuda_calls: list[int],
    body_calls: list[int],
    metadata: dict[str, Any],
    modules: dict[str, Any],
    identity_path: Path,
    read_fd: int,
    write_fd: int,
) -> None:
    """No imports, Torch/NumPy calls, queue use or inherited-scope unwind here."""
    os.close(read_fd)
    try:
        assert os.getpid() != domain._pid
        assert os.getppid() == domain._pid
        os_threads = len(os.listdir("/proc/self/task"))
        assert os_threads == 1
        results: dict[str, Any] = {}
        for name, action in actions.items():
            domain_lock.calls[0] = owner_lock.calls[0] = cuda_calls[0] = body_calls[0] = 0
            before = guard_state(domain)
            try:
                action()
            except BaseException as error:
                assert type(error) is RuntimeError
                assert str(error) == "RNG custody cannot be inherited by another process"
                exception_class = "builtins.RuntimeError"
                diagnostic = str(error)
            else:
                raise AssertionError(f"inherited {trial}/{name} did not refuse")
            unchanged = guard_state(domain) == before
            assert unchanged
            assert domain_lock.calls[0] == owner_lock.calls[0] == cuda_calls[0] == body_calls[0] == 0
            results[name] = {
                "exception_class": exception_class,
                "diagnostic": diagnostic,
                "lock_acquire_calls": domain_lock.calls[0],
                "owner_lock_acquire_calls": owner_lock.calls[0],
                "cuda_touch_calls": cuda_calls[0],
                "body_calls": body_calls[0],
                "state_unchanged": unchanged,
            }
        imports = {name: str(Path(module.__file__).resolve()) for name, module in modules.items()}
        source_hashes = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in imports.items()}
        identity = {
            "schema": "cuda-core-fork-guard-identity-v1",
            "profile": "linux-fork-inherited-guard-only-v1",
            "role": "cuda_core_inherited_pid_guard",
            "trial": trial,
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "inherited_domain_pid": domain._pid,
            **metadata,
            "cuda_core_imports": imports,
            "module_origin": "inherited-loaded-module-objects",
            "source_sha256": source_hashes,
            "os_threads": os_threads,
            "torch_profile": None,
            "torch_profile_unavailable_reason": "no Torch calls permitted in fork guard-only process",
            "guard_results": results,
        }
        with identity_path.open("x") as stream:
            json.dump(identity, stream, sort_keys=True)
        acknowledgement = {
            "trial": trial,
            "pid": os.getpid(),
            "ppid": os.getppid(),
            "identity_sha256": hashlib.sha256(identity_path.read_bytes()).hexdigest(),
            "message": f"cuda core inherited pid {trial} fail closed",
        }
        payload = json.dumps(acknowledgement, sort_keys=True).encode("utf-8")
        assert len(payload) <= 4096
        position = 0
        while position < len(payload):
            written = os.write(write_fd, payload[position:])
            assert written > 0
            position += written
    except BaseException as error:
        try:
            os.write(write_fd, repr(error).encode("utf-8")[:1024])
        finally:
            os._exit(1)
    os.close(write_fd)
    os._exit(0)


def await_owned_fork(pid: int, read_fd: int) -> tuple[int, int, bytes]:
    deadline = time.monotonic() + 10
    payload = bytearray()
    reaped = False
    eof = False
    wait_pid, status = 0, 0
    try:
        os.set_blocking(read_fd, False)
        while not (reaped and eof):
            remaining = deadline - time.monotonic()
            assert remaining > 0, "inherited guard exceeded owned ten-second deadline"
            ready, _, _ = select.select([] if eof else [read_fd], [], [], min(remaining, 0.05))
            if ready:
                data = os.read(read_fd, 4097)
                if data:
                    payload.extend(data)
                    assert len(payload) <= 4096
                else:
                    eof = True
            if not reaped:
                wait_pid, status = os.waitpid(pid, os.WNOHANG)
                reaped = wait_pid == pid
        return wait_pid, status, bytes(payload)
    finally:
        if not reaped:
            wait_pid, _ = os.waitpid(pid, os.WNOHANG)
            reaped = wait_pid == pid
        if not reaped:
            # Only our still-unreaped child can receive these signals.
            os.kill(pid, signal.SIGTERM)
            cleanup_deadline = time.monotonic() + 1
            while time.monotonic() < cleanup_deadline:
                wait_pid, _ = os.waitpid(pid, os.WNOHANG)
                if wait_pid == pid:
                    reaped = True
                    break
                select.select([], [], [], 0.01)
            if not reaped:
                wait_pid, _ = os.waitpid(pid, os.WNOHANG)
                reaped = wait_pid == pid
            if not reaped:
                os.kill(pid, signal.SIGKILL)
                cleanup_deadline = time.monotonic() + 1
                while time.monotonic() < cleanup_deadline:
                    wait_pid, _ = os.waitpid(pid, os.WNOHANG)
                    if wait_pid == pid:
                        reaped = True
                        break
                    select.select([], [], [], 0.01)
            assert reaped, "owned fork child could not be reaped"


def run_fork_trial(
    trial: str,
    gate: Any,
    domain: Any,
    participant: Any,
    contract: Any,
    domain_lock: LockProbe,
    owner_lock: LockProbe,
    cuda_calls: list[int],
    metadata: dict[str, Any],
    modules: dict[str, Any],
    output: Path,
) -> None:
    device = torch.device("cuda")
    sentinel = RuntimeError("inherited reporter must not mutate poison")
    body_calls = [0]

    def enter(context: Any) -> None:
        with context:
            body_calls[0] += 1

    if trial == "admission":
        actions = {
            "resolve_cuda": lambda: gate.resolve_cuda(device),
            "enroll": lambda: gate.enroll(participant=participant, cuda_devices=()),
            "report_failure": lambda: gate.report_failure(error=sentinel),
            "domain_admission": lambda: enter(domain.admission(lineage=None)),
        }
    elif trial == "local":
        descriptor = custody._LOCAL_CUDA_CONTRACTS[contract]
        raw_resolver = custody.AmbientRNGDomain._resolve_local_cuda_record
        actions = {
            "resolve_cuda": lambda: gate.resolve_cuda(device=device),
            "complete": lambda: enter(gate.complete(cuda_devices=())),
            "completion_failed": gate.completion_failed,
            "report_failure": lambda: gate.report_failure(error=sentinel),
            "domain_local_cuda_access": lambda: enter(domain.local_cuda_access(participant=participant, contract=contract)),
            "domain_local_cuda_policy": lambda: domain._local_cuda_policy(contract=contract),
            "domain_resolve_local_cuda_record": lambda: raw_resolver(domain, descriptor=descriptor),
        }
    else:
        assert trial == "invocation"
        active, completed = gate
        actions = {
            "active_enter": active.__enter__,
            "active_exit": lambda: active.__exit__(None, None, None),
            "active_completion_failed": active.completion_failed,
            "completed_completion_failed": completed.completion_failed,
            "domain_device_invocation": lambda: domain.device_invocation(
                participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=()
            ),
        }
    identity_path = output / f"fork-identity-cuda_core_inherited_pid-{trial}.json"
    observation_path = output / f"fork-observation-cuda_core_inherited_pid-{trial}.json"
    parent_pid = os.getpid()
    read_fd, write_fd = os.pipe()
    try:
        parent_threads = len(os.listdir("/proc/self/task"))
        assert parent_threads == 1, "fork guard requires exactly one actual OS task before fork"
        pid = os.fork()
        if pid == 0:
            fork_guard_grandchild(
                trial, actions, domain, domain_lock, owner_lock, cuda_calls, body_calls, metadata, modules, identity_path, read_fd, write_fd
            )
            os._exit(1)
        os.close(write_fd)
        write_fd = -1
        wait_pid, status, payload = await_owned_fork(pid, read_fd)
        assert os.WIFEXITED(status)
        assert os.WEXITSTATUS(status) == 0, payload.decode("utf-8", errors="replace")
        acknowledgement = json.loads(payload)
        assert set(acknowledgement) == {"trial", "pid", "ppid", "identity_sha256", "message"}
        assert acknowledgement["trial"] == trial
        assert wait_pid == pid == acknowledgement["pid"]
        assert acknowledgement["ppid"] == parent_pid
        assert acknowledgement["message"] == f"cuda core inherited pid {trial} fail closed"
        identity_hash = hashlib.sha256(identity_path.read_bytes()).hexdigest()
        assert acknowledgement["identity_sha256"] == identity_hash
        identity = json.loads(identity_path.read_text())
        assert identity["pid"] == pid
        assert identity["ppid"] == identity["inherited_domain_pid"] == parent_pid
        with observation_path.open("x") as stream:
            json.dump(
                {
                    "schema": "cuda-core-fork-guard-observation-v1",
                    "trial": trial,
                    "role": "cuda_core_inherited_pid_guard",
                    "parent_pid": parent_pid,
                    "fork_pid": pid,
                    "waitpid_pid": wait_pid,
                    "wait_status": status,
                    "exit_code": os.WEXITSTATUS(status),
                    "queued_pid": acknowledgement["pid"],
                    "queued_ppid": acknowledgement["ppid"],
                    "identity_sha256": identity_hash,
                    "message": acknowledgement["message"],
                    "parent_os_threads_before_fork": parent_threads,
                    "manifest_sha256": metadata["manifest_sha256"],
                },
                stream,
                sort_keys=True,
            )
    finally:
        os.close(read_fd)
        if write_fd != -1:
            os.close(write_fd)


def inherited_pid_child(queue: Any, ordinary_output: str) -> None:
    role = "cuda_core_inherited_pid"
    qualified = child_identity(role)
    before = ambient_snapshot()
    domain = custody.process_rng_domain()
    assert not domain.status()[2]
    metadata: dict[str, Any] = {"qualified": qualified, "base_commit": None, "candidate_tree": None, "manifest_sha256": None}
    if qualified:
        output = Path(os.environ["BAC_QUAL_OUTPUT"])
        manifest_bytes = Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()
        manifest = json.loads(manifest_bytes)
        outer_identity = json.loads((output / f"spawn-identity-{role}.json").read_text())
        assert manifest["base_commit"] == outer_identity["sha"] == os.environ["BAC_QUAL_SHA"]
        assert manifest["candidate_tree"] == outer_identity["candidate_tree"] == os.environ["BAC_QUAL_TREE"]
        metadata.update(
            base_commit=manifest["base_commit"],
            candidate_tree=manifest["candidate_tree"],
            manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        )
        assert metadata["manifest_sha256"] == outer_identity["manifest_sha256"]
    else:
        output = Path(ordinary_output)
    modules = {
        "townlet.exploration.rng_custody": custody,
        "test_rng_cuda_admission": importlib.import_module("test_rng_cuda_admission"),
    }
    owner = Owner()
    participant = register(domain, owner, ())
    with pytest.MonkeyPatch.context() as monkeypatch:
        contract = contract_fixture(monkeypatch, False)
        domain_lock, owner_lock = LockProbe(domain._lock), LockProbe(owner.lock)
        monkeypatch.setattr(domain, "_lock", domain_lock)
        monkeypatch.setattr(owner, "lock", owner_lock)
        cuda_calls = [0]
        monkeypatch.setattr(custody.torch, "cuda", ForbiddenCUDA(cuda_calls))
        for trial in ("admission", "local"):
            context = (
                domain.admission(lineage=None)
                if trial == "admission"
                else domain.local_cuda_access(participant=participant, contract=contract)
            )
            with context as gate:
                if trial == "admission":
                    canonical_contract = custody.REPLAY_BUFFER_SERIALIZE_CUDA
                    canonical = domain._local_cuda_policy(contract=canonical_contract)
                    assert domain._local_cuda_policies[canonical_contract][1] is canonical
                    assert any(item not in domain._local_cuda_policies for item in custody._LOCAL_CUDA_CONTRACTS)
                run_fork_trial(trial, gate, domain, participant, contract, domain_lock, owner_lock, cuda_calls, metadata, modules, output)
            assert not domain.status()[2]
            assert_ambient_unchanged(before)
        completed = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
        with completed:
            pass
        active = domain.device_invocation(participant=participant, operation_kind="ordinary", lineage=None, cuda_devices=())
        with owner.lock, active:
            run_fork_trial(
                "invocation",
                (active, completed),
                domain,
                participant,
                contract,
                domain_lock,
                owner_lock,
                cuda_calls,
                metadata,
                modules,
                output,
            )
        assert completed.completion_failed() is False and active.completion_failed() is False
        assert not domain.status()[2]
        assert_ambient_unchanged(before)
    domain.unregister(participant=participant)
    assert not domain.status()[2]
    assert_ambient_unchanged(before)
    queue.put(("cuda core inherited pid gates fail closed", os.getpid(), os.getppid(), qualified))


def test_isolated_inherited_pid_gate_refusal(tmp_path: Path) -> None:
    assert hasattr(os, "fork") and Path("/proc/self/task").is_dir(), "Linux fork guard prerequisite unavailable; UNRUN"
    before = ambient_snapshot()
    parent_pid = os.getpid()
    qualified = bootstrap._qualification_active()
    role = "cuda_core_inherited_pid"
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=inherited_pid_child, args=(queue, str(tmp_path)), name=role)
    try:
        process.start()
        process.join(90)
        assert not process.is_alive()
        assert process.exitcode == 0
        message, queued_pid, queued_ppid, child_qualified = queue.get(timeout=5)
        assert message == "cuda core inherited pid gates fail closed"
        assert queued_pid == process.pid
        assert queued_ppid == parent_pid
        assert child_qualified is qualified
        if qualified:
            output = Path(os.environ["BAC_QUAL_OUTPUT"])
            with (output / f"spawn-observation-{role}.json").open("x") as stream:
                json.dump(
                    {
                        "process_pid": process.pid,
                        "queued_pid": queued_pid,
                        "parent_pid": parent_pid,
                        "queued_ppid": queued_ppid,
                        "exitcode": process.exitcode,
                        "qualified": qualified,
                        "message": message,
                        "manifest_sha256": hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
                    },
                    stream,
                    sort_keys=True,
                )
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        assert not process.is_alive()
        queue.close()
        queue.join_thread()
        process.close()
    assert not custody.process_rng_domain().status()[2]
    assert_ambient_unchanged(before)


_COLD_IMPORT_PROBE = r"""import ast
import builtins
import hashlib
import importlib.util
import json
import os
import pickle
import random
import sys
import threading
from pathlib import Path

def digest(data):
    return hashlib.sha256(data).hexdigest()

def reference(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": digest(data)}

def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            assert key not in result, "duplicate JSON key"
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs)

def verify_reference(ref):
    assert reference(ref["path"]) == ref
    return read(ref["path"])

argv = sys.orig_argv
proc_argv = Path("/proc/self/cmdline").read_bytes().split(b"\0")
assert proc_argv.pop() == b""
proc_argv = [value.decode("utf-8") for value in proc_argv]
assert argv == proc_argv and len(argv) == 9 and argv[1:3] == ["-I", "-c"]
mode, entry, root_text, output_text, nonce = sys.argv[1:]
root, output = Path(root_text).resolve(), Path(output_text).resolve()
assert str(root) == root_text and str(output) == output_text and Path.cwd() == root
assert mode in ("qualify", "preflight_preloaded", "preflight_cuda_touch") and entry in ("core", "flat", "per")
assert len(nonce) == 32 and all(c in "0123456789abcdef" for c in nonce)
launch_python = str(root / ".venv/bin/python")
assert argv[0] == sys.executable == launch_python and sys.flags.isolated == 1
binary = str(Path("/proc/self/exe").resolve())
binary_hash = digest(Path(binary).read_bytes())
script_hash = digest(argv[3].encode("utf-8"))
command_hash = digest(json.dumps(argv, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
manifest_ref = reference(os.environ["BAC_QUAL_MANIFEST"])
manifest = read(manifest_ref["path"])
assert manifest["base_commit"] == os.environ["BAC_QUAL_SHA"]
assert manifest["candidate_tree"] == os.environ["BAC_QUAL_TREE"]
assert os.environ["BAC_QUAL_ROOT"] == str(root) and os.environ["BAC_QUAL_OUTPUT"] == str(output)
test_ref = reference(root / "tests/test_townlet/regressions/bac/test_rng_cuda_admission.py")
assert manifest["source_files"][str(Path(test_ref["path"]).relative_to(root))] == test_ref["sha256"]
worker_ref = reference(output / "cold-import-worker.json")
worker = read(worker_ref["path"])
assert worker["pid"] == os.getppid() and worker["root"] == str(root)
role = "cuda_core_cold_import_" + entry if mode == "qualify" else "cuda_core_cold_" + mode
assert worker["role"] == role
runtime_seal = None
if "BAC_COLD_SPEC" in os.environ:
    spec = read(os.environ["BAC_COLD_SPEC"])
    assert spec["root"] == str(root) and spec["manifest_ref"] == manifest_ref
    tool_seal = verify_reference(spec["tool_seal_ref"])
    runtime_seal = tool_seal["runtime"]
allowed = {}
for relative, sha in manifest["source_files"].items():
    if relative.startswith("src/townlet/") and relative.endswith(".py"):
        parts = Path(relative).parts[1:]
        name = ".".join(parts[:-1] if parts[-1] == "__init__.py" else (*parts[:-1], parts[-1][:-3]))
        path = (root / relative).resolve()
        assert name not in allowed and path.is_relative_to(root / "src")
        allowed[name] = {"path": str(path), "sha256": sha}

def modules():
    return sorted(name for name in sys.modules if name == "townlet" or name.startswith("townlet."))

def sources(names):
    result = {}
    for name in names:
        path = Path(sys.modules[name].__file__).resolve()
        row = {"path": str(path), "sha256": digest(path.read_bytes())}
        assert name in allowed and row == allowed[name]
        result[name] = row
    return result

checkpoints = {"before_torch": modules()}
assert checkpoints["before_torch"] == []
sys.path.insert(0, str(root / "src"))
import torch
import numpy as np
checkpoints["after_torch"] = modules()
assert checkpoints["after_torch"] == []
thread_keys = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS",
               "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS")
environment = {key: os.environ[key] for key in thread_keys}
assert set(environment.values()) == {"1"}
torch.set_num_threads(1)
torch.set_num_interop_threads(1)
runtime = {"torch_version": str(torch.__version__), "torch_path": str(Path(torch.__file__).resolve()),
           "numpy_version": np.__version__, "numpy_path": str(Path(np.__file__).resolve())}
if runtime_seal is not None:
    assert all(runtime[key] == runtime_seal[key] for key in runtime)
    assert runtime_seal["launch_python"] == launch_python and runtime_seal["binary"] == binary
    assert runtime_seal["binary_sha256"] == binary_hash and runtime_seal["python_version"] == sys.version

def threads():
    actual = [{"name": t.name, "ident": t.ident, "native_id": t.native_id} for t in threading.enumerate()]
    tasks = os.listdir("/proc/self/task")
    assert len(actual) == len(tasks) == 1 and actual[0]["name"] == "MainThread"
    assert actual[0]["native_id"] == int(tasks[0])
    intra, inter = torch.get_num_threads(), torch.get_num_interop_threads()
    assert intra == inter == 1
    return {"python": actual, "os": len(tasks), "torch_intraop": intra, "torch_interop": inter}

threads_before = threads()
tree = ast.parse(argv[3])
boundary_site = next(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Assert)
                     and isinstance(n.msg, ast.Constant) and n.msg.value == "cold import precondition violated")
sentinel_site = next(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Raise)
                    and isinstance(n.exc, ast.Call) and n.exc.args
                    and isinstance(n.exc.args[0], ast.Constant) and n.exc.args[0].value == "cold import CUDA sentinel touched")
preload_branch = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                      and any(isinstance(v, ast.Constant) and v.value == "preflight_preloaded" for v in ast.walk(n.test)))
preload_caller = next(n.lineno for n in ast.walk(preload_branch) if isinstance(n, ast.Call)
                      and isinstance(n.func, ast.Name) and n.func.id == "_cold_boundary")
touch_caller = next(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                    and n.attr == "is_initialized" and isinstance(n.value, ast.Attribute) and n.value.attr == "cuda")

def common(schema):
    assert sys.orig_argv == argv and reference(worker_ref["path"]) == worker_ref
    return {"schema": schema, "profile": "linux-exec-cold-import-v2", "role": role, "mode": mode, "entry": entry,
            "nonce": nonce, "pid": os.getpid(), "ppid": os.getppid(), "worker_ref": worker_ref, "root": str(root),
            "cwd": str(Path.cwd()), "launch_python": launch_python, "binary": binary, "binary_sha256": binary_hash,
            "python_version": sys.version, "orig_argv": argv, "proc_argv": proc_argv, "command_sha256": command_hash,
            "script_sha256": script_hash, "manifest_ref": manifest_ref, "test_ref": test_ref,
            "base_commit": manifest["base_commit"], "candidate_tree": manifest["candidate_tree"]}

def emit(filename, value):
    with (output / filename).open("x") as stream:
        json.dump(value, stream, sort_keys=True, allow_nan=False)

cuda_calls = [0]
def witness(phase, function, line, caller):
    names = modules()
    emit("cold-import-fault-witness.json", {**common("cuda-core-cold-import-fault-witness-v2"),
         "phase": phase, "modules": names, "source_modules": sources(names), "cuda_calls": cuda_calls[0],
         "site_function": function, "site_line": line, "caller_function": "<module>", "caller_line": caller,
         "threads": threads(), "environment": environment})

class NoCUDA:
    def __getattribute__(self, name):
        cuda_calls[0] += 1
        if mode == "preflight_cuda_touch":
            witness("before_sentinel_raise", "__getattribute__", sentinel_site, touch_caller)
        raise RuntimeError("cold import CUDA sentinel touched")

sentinel = NoCUDA()
torch.cuda = sentinel
checkpoints["before_selected"] = modules()
assert checkpoints["before_selected"] == []
core_name = "townlet.exploration.rng_custody"
flat_name = "townlet.training.replay_buffer"
per_name = "townlet.training.prioritized_replay_buffer"
core_path = str((root / "src/townlet/exploration/rng_custody.py").resolve())
eager_calls, custody_imports = [], []
old_profile, old_import = sys.getprofile(), builtins.__import__

def profile(frame, event, arg):
    if event == "call" and frame.f_code.co_name in ("_local_cuda_policy", "_resolve_local_cuda_record"):
        if str(Path(frame.f_code.co_filename).resolve()) == core_path:
            eager_calls.append(frame.f_code.co_name)
            raise AssertionError("eager canonical policy lookup")

def observe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if globals and globals.get("__name__") == core_name:
        if type(name) is not str or type(level) is not int or not isinstance(fromlist, (tuple, list, type(None))):
            return old_import(name, globals, locals, fromlist, level)
        try:
            base = importlib.util.resolve_name("." * level + name, globals.get("__package__")) if level else name
            targets = {base, *(base + "." + item for item in (fromlist or ()) if isinstance(item, str))}
        except (AttributeError, ImportError, TypeError, ValueError):
            return old_import(name, globals, locals, fromlist, level)
        if targets.intersection((flat_name, per_name)):
            custody_imports.append(base)
            raise AssertionError("custody eagerly imported canonical producer")
    return old_import(name, globals, locals, fromlist, level)

def _cold_boundary():
    assert modules() == [], "cold import precondition violated"

sys.setprofile(profile)
builtins.__import__ = observe_import
try:
    if mode == "preflight_preloaded":
        importlib.import_module(core_name)
        witness("before_preentry_assert", "_cold_boundary", boundary_site, preload_caller)
        _cold_boundary()
    if mode == "preflight_cuda_touch":
        torch.cuda.is_initialized
    _cold_boundary()
    importlib.import_module({"core": core_name, "flat": flat_name, "per": per_name}[entry])
finally:
    builtins.__import__ = old_import
    sys.setprofile(old_profile)
assert eager_calls == custody_imports == [] and cuda_calls == [0] and torch.cuda is sentinel
checkpoints["after_selected"] = modules()
assert {"townlet", core_name, {"core": core_name, "flat": flat_name, "per": per_name}[entry]} <= set(modules())
if entry == "core":
    assert flat_name not in sys.modules and per_name not in sys.modules
custody = importlib.import_module(core_name)
domain = custody.process_rng_domain()
assert domain._pid == os.getpid() and domain._local_cuda_policies == {}
rows = [
    ("REPLAY_BUFFER_PUSH_CUDA", "flat", "push", "tensor"),
    ("REPLAY_BUFFER_PUSH_RECORDED_CUDA", "flat", "push_recorded", "tensor"),
    ("REPLAY_BUFFER_READINESS_CUDA", "flat", "readiness", "request"),
    ("REPLAY_BUFFER_SERIALIZE_CUDA", "flat", "serialize", "none"),
    ("REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA", "flat", "validate_serialized", "mapping"),
    ("REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA", "flat", "load_for_mode", "mapping"),
    ("REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA", "flat", "historical_archives", "none"),
    ("REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA", "flat", "install_historical_archive", "archive"),
    ("PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA", "per", "push", "tensor"),
    ("PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA", "per", "push_recorded", "tensor"),
    ("PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA", "per", "declare_unconstrained_action_dim", "integer"),
    ("PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA", "per", "readiness", "request"),
    ("PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA", "per", "serialize", "none"),
    ("PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA", "per", "validate_serialized", "mapping"),
    ("PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA", "per", "historical_archives", "none"),
    ("PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA", "per", "install_historical_archive", "archive"),
    ("PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA", "per", "update_priorities", "indices"),
    ("PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA", "per", "update_unit_priorities", "indices"),
]
from types import MappingProxyType
contracts = {name: getattr(custody, name) for name, *_ in rows}
assert type(custody._LOCAL_CUDA_CONTRACTS) is MappingProxyType
assert len(set(contracts.values())) == 18 and set(custody._LOCAL_CUDA_CONTRACTS) == set(contracts.values())
inventory = []
for name, kind, route, input_kind in rows:
    contract = contracts[name]
    descriptor = custody._LOCAL_CUDA_CONTRACTS[contract]
    assert type(contract) is custody.LocalCUDAContract and type(descriptor) is custody._LocalCUDADescriptor
    assert (descriptor.owner_kind, descriptor.route, descriptor.input_kind) == (kind, route, input_kind)
    assert descriptor.healthy is True and descriptor.post_poison is False and descriptor.rationale
    inventory.append({"name": name, "contract_id": id(contract), "descriptor_id": id(descriptor), "owner_kind": kind,
                      "route": route, "input_kind": input_kind, "rationale": descriptor.rationale,
                      "healthy": descriptor.healthy, "post_poison": descriptor.post_poison})
assert len({row["descriptor_id"] for row in inventory}) == 18
flat, per = importlib.import_module(flat_name), importlib.import_module(per_name)
checkpoints["after_producers"] = modules()
owners = []
missing, gates, resolutions = [], [], []
real_resolver = domain._resolve_local_cuda_record
def resolve(*, descriptor):
    resolutions.append(id(descriptor))
    return real_resolver(descriptor=descriptor)
domain._resolve_local_cuda_record = resolve
names = ["REPLAY_BUFFER_SERIALIZE_CUDA", "PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA"]

def cache():
    return [name for name, *_ in rows if contracts[name] in domain._local_cuda_policies]

def state():
    with domain._lock:
        return {"generation": domain._generation, "revision": domain._revision, "currency": domain._currency,
                "ambient_revision": domain._ambient_revision, "poisoned": domain._poison is not None,
                "ready": domain._cuda_ready, "gates": len(domain._gates), "operations": len(domain._operations),
                "members": len(domain._members)}

def rng():
    return {"python": digest(pickle.dumps(random.getstate(), protocol=5)),
            "numpy": digest(pickle.dumps(np.random.get_state(), protocol=5)),
            "torch": digest(torch.get_rng_state().numpy().tobytes())}

try:
    owners.append(flat.ReplayBuffer(4, torch.device("cpu")))
    owners.append(per.PrioritizedReplayBuffer(4, 1.0, 0.0, False, torch.device("cpu")))
    assert cache() == [] and cuda_calls == [0]
    for owner, module, class_name in zip(owners, (flat, per), ("ReplayBuffer", "PrioritizedReplayBuffer")):
        assert type(owner) is getattr(module, class_name)
        assert domain._members[owner.rng_participant].owner() is owner
    rng_before = rng()
    for owner, module, class_name, name in zip(owners, (flat, per), ("ReplayBuffer", "PrioritizedReplayBuffer"), names):
        before, before_cache = state(), cache()
        canonical = module.__dict__.pop(class_name)
        body_calls = 0
        try:
            try:
                with domain.local_cuda_access(participant=owner.rng_participant, contract=contracts[name]):
                    body_calls += 1
            except ImportError:
                pass
            else:
                raise AssertionError("missing canonical export admitted")
        finally:
            module.__dict__[class_name] = canonical
        after = state()
        assert before == after and cache() == before_cache == [] and body_calls == 0 and cuda_calls == [0]
        missing.append({"contract": name, "exception_class": "ImportError", "export_restored": getattr(module, class_name) is canonical,
                        "body_calls": body_calls, "cuda_calls": cuda_calls[0], "cache_before": before_cache, "cache_after": cache(),
                        "state_before": before, "state_after": after})
    assert len(resolutions) == 2
    retained = {}
    for pass_name in ("first", "repeat"):
        for owner, name in zip(owners, names):
            before, before_cache, count = state(), cache(), len(resolutions)
            contract = contracts[name]
            with domain.local_cuda_access(participant=owner.rng_participant, contract=contract) as gate:
                cached = domain._local_cuda_policies[contract]
                descriptor, policy = cached
                live = domain._gate_record(gate)
                assert live.participant is owner.rng_participant and live.owner is owner and live.contract is contract
                assert descriptor is custody._LOCAL_CUDA_CONTRACTS[contract] and live.policy is policy
                assert policy.owner_type is type(owner) and policy.input_type is type(None)
                assert policy.route == descriptor.route == "serialize" and policy.rationale == descriptor.rationale
                assert policy.healthy is True and policy.post_poison is False
                for previous_name, previous in retained.items():
                    assert domain._local_cuda_policies[contracts[previous_name]] is previous
                if pass_name == "repeat":
                    assert retained[name] is cached and len(resolutions) == count
                else:
                    assert len(resolutions) == count + 1
                    retained[name] = cached
                with owner._owner_operation(mutation=False):
                    assert owner._replay_lock._is_owned()
                    with gate.complete(cuda_devices=()):
                        assert domain._gate_record(gate) is live and live.policy is policy
                    assert gate.completion_failed() is False and domain._gate_record(gate).policy is policy
            after = state()
            assert before == after and domain._local_cuda_policies[contract] is cached
            gates.append({"pass": pass_name, "contract": name, "owner_id": id(owner), "participant_id": id(owner.rng_participant),
                          "descriptor_id": id(descriptor), "policy_id": id(policy), "cache_tuple_id": id(cached),
                          "owner_class": type(owner).__module__ + "." + type(owner).__qualname__, "input_class": "builtins.NoneType",
                          "route": policy.route, "rationale": policy.rationale, "healthy": policy.healthy,
                          "post_poison": policy.post_poison, "exact_binding": True, "completion_failed": False,
                          "cache_before": before_cache, "cache_after": cache(), "resolver_before": count,
                          "resolver_after": len(resolutions), "state_before": before, "state_after": after})
    rng_after = rng()
    assert rng_before == rng_after and len(resolutions) == 4 and cache() == names
finally:
    domain._resolve_local_cuda_record = real_resolver
    for owner in owners:
        domain.unregister(participant=owner.rng_participant)
unresolved = [name for name, *_ in rows if name not in cache()]
cleanup_state = state()
assert cleanup_state["members"] == cleanup_state["gates"] == cleanup_state["operations"] == 0
assert cleanup_state["poisoned"] is cleanup_state["ready"] is False and len(unresolved) == 16
assert cuda_calls == [0] and torch.cuda is sentinel
checkpoints["final"] = modules()
threads_after = threads()
all_modules = sorted(set().union(*map(set, checkpoints.values())))
emit("cold-import-identity.json", {**common("cuda-core-cold-import-identity-v2"), "runtime": runtime,
     "checkpoints": checkpoints, "source_modules": sources(all_modules), "threads_before": threads_before,
     "threads_after": threads_after, "environment": environment, "eager_policy_calls": eager_calls,
     "custody_producer_imports": custody_imports, "manifest_contracts": inventory, "missing_exports": missing,
     "gates": gates, "unresolved": unresolved, "rng_before": rng_before, "rng_after": rng_after,
     "cleanup": {"unregistered": ["flat", "per"], "state": cleanup_state, "cache": cache(), "unresolved": unresolved,
                 "cuda_calls": cuda_calls[0], "sentinel_identity": torch.cuda is sentinel}})
"""


def _run_cold_import_probe(tmp_path: Path, mode: str, entry: str) -> None:
    """Launch exact source-issued code without importing this warmed module in its child."""
    root = Path(custody.__file__).resolve().parents[3]
    qualified = bootstrap._qualification_active()
    qualification_keys = ("BAC_QUAL_ROOT", "BAC_QUAL_OUTPUT", "BAC_QUAL_MANIFEST", "BAC_QUAL_SHA", "BAC_QUAL_TREE")
    if any(key in os.environ for key in qualification_keys):
        assert qualified and all(key in os.environ for key in qualification_keys), "partial qualification environment"
    output = Path(os.environ["BAC_QUAL_OUTPUT"]).resolve() if qualified else tmp_path.resolve()
    role = f"cuda_core_cold_import_{entry}" if mode == "qualify" else f"cuda_core_cold_{mode}"
    nonce = os.urandom(16).hex()

    def reference(path: Path) -> dict[str, Any]:
        data = path.read_bytes()
        return {"path": str(path.resolve()), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

    def write(filename: str, value: dict[str, Any]) -> None:
        with (output / filename).open("x") as stream:
            json.dump(value, stream, sort_keys=True, allow_nan=False)

    process = None
    timed_out, termination, started, phase = False, "none", time.monotonic(), "setup"

    def stop_child(sig: signal.Signals) -> None:
        assert process is not None
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    try:
        worker_path = output / "cold-import-worker.json"
        child_env = dict(os.environ)
        if qualified:
            assert Path(os.environ["BAC_QUAL_ROOT"]).resolve() == root and "BAC_COLD_SPEC" in os.environ
            worker = json.loads(worker_path.read_bytes())
            assert worker["pid"] == os.getpid() and worker["role"] == role
        else:
            manifest_path = output / "local-manifest.json"
            source_files = {str(path.relative_to(root)): reference(path)["sha256"] for path in (root / "src/townlet").rglob("*.py")}
            source_files[str(Path(__file__).resolve().relative_to(root))] = reference(Path(__file__))["sha256"]
            manifest_path.write_text(
                json.dumps({"base_commit": "unqualified", "candidate_tree": "unqualified", "source_files": source_files})
            )
            child_env.update(
                BAC_QUAL_ROOT=str(root),
                BAC_QUAL_OUTPUT=str(output),
                BAC_QUAL_MANIFEST=str(manifest_path),
                BAC_QUAL_SHA="unqualified",
                BAC_QUAL_TREE="unqualified",
            )
            child_env.pop("BAC_COLD_SPEC", None)
            write("cold-import-worker.json", {"pid": os.getpid(), "role": role, "root": str(root)})
        worker_ref = reference(worker_path)
        ticks = int(Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19])
        if qualified:
            assert worker["start_ticks"] == ticks
        for key in (
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "BLIS_NUM_THREADS",
        ):
            child_env[key] = "1"
        argv = [str(root / ".venv/bin/python"), "-I", "-c", _COLD_IMPORT_PROBE, mode, entry, str(root), str(output), nonce]
        command_hash = hashlib.sha256(json.dumps(argv, ensure_ascii=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        script_hash = hashlib.sha256(_COLD_IMPORT_PROBE.encode("utf-8")).hexdigest()
        with (output / "cold-import-stdout.log").open("xb") as stdout, (output / "cold-import-stderr.log").open("xb") as stderr:
            process = subprocess.Popen(argv, cwd=root, env=child_env, stdout=stdout, stderr=stderr, start_new_session=True)
            assert process.poll() is None
            assert int(Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19]) == ticks
            phase = "import"
            try:
                process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                timed_out, termination = True, "terminate"
                stop_child(signal.SIGTERM)
                if process.poll() is None:
                    termination = "kill"
                    stop_child(signal.SIGKILL)
        assert not timed_out and process.returncode == (0 if mode == "qualify" else 1)
        phase = "validate"
        subject = output / ("cold-import-identity.json" if mode == "qualify" else "cold-import-fault-witness.json")
        record = json.loads(subject.read_bytes())
        assert record["pid"] == process.pid and record["ppid"] == os.getpid() and record["nonce"] == nonce
        assert record["orig_argv"] == record["proc_argv"] == argv and record["worker_ref"] == worker_ref
        assert record["script_sha256"] == script_hash and record["command_sha256"] == command_hash
        if mode != "qualify":
            assert not (output / "cold-import-identity.json").exists()
            expected = (
                "AssertionError: cold import precondition violated"
                if mode == "preflight_preloaded"
                else "RuntimeError: cold import CUDA sentinel touched"
            )
            assert (output / "cold-import-stderr.log").read_text().rstrip().splitlines()[-1] == expected
            assert record["cuda_calls"] == (0 if mode == "preflight_preloaded" else 1)
        write(
            "cold-import-observation.json",
            {
                "schema": "cuda-core-cold-import-observation-v2",
                "role": role,
                "mode": mode,
                "entry": entry,
                "nonce": nonce,
                "parent_pid": os.getpid(),
                "child_pid": process.pid,
                "worker_start_ticks": ticks,
                "worker_ref": worker_ref,
                "launch_argv": argv,
                "command_sha256": command_hash,
                "script_sha256": script_hash,
                "subject_ref": reference(subject),
                "stdout_ref": reference(output / "cold-import-stdout.log"),
                "stderr_ref": reference(output / "cold-import-stderr.log"),
                "exitcode": process.returncode,
                "timed_out": timed_out,
                "termination": termination,
                "reaped": process.poll() is not None,
                "seconds": float(time.monotonic() - started),
            },
        )
    except BaseException as error:
        if process is not None and process.poll() is None:
            termination = "kill"
            stop_child(signal.SIGKILL)
        write(
            "cold-import-failure.json",
            {
                "schema": "cuda-core-cold-import-failure-v2",
                "role": role,
                "phase": phase,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "elapsed_seconds": float(time.monotonic() - started),
                "timeout": timed_out,
                "termination": termination,
                "returncode": None if process is None else process.returncode,
                "reaped": process is not None and process.poll() is not None,
                "files": [reference(path) for path in sorted(output.iterdir()) if path.is_file()],
            },
        )
        raise


@pytest.mark.parametrize("entry", ["core", "flat", "per"])
def test_fresh_process_canonical_import_order(tmp_path: Path, entry: str) -> None:
    _run_cold_import_probe(tmp_path, "qualify", entry)


@pytest.mark.parametrize("fault", ["preloaded", "cuda_touch"])
def test_cold_import_probe_faults(tmp_path: Path, fault: str) -> None:
    _run_cold_import_probe(tmp_path, "preflight_" + fault, "core")
