"""CPU protocol controls; instrumented CUDA calls are not hardware qualification."""

from __future__ import annotations

import copy
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
import threading
import time
import weakref
from pathlib import Path
from types import MappingProxyType
from typing import Any

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
    record = custody._LocalCUDARecord(
        owner_type=Owner,
        route="test_cuda_leaf",
        input_type=tuple,
        rationale="finite CPU seam, no production purity qualification",
        healthy=True,
        post_poison=post_poison,
    )
    monkeypatch.setattr(custody, "_LOCAL_CUDA_CONTRACTS", MappingProxyType({contract: record}))
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


def test_public_required_signatures_and_empty_manifest() -> None:
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
    assert not custody._LOCAL_CUDA_CONTRACTS


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
)


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


def poison_case(case: str, domain: Any, cuda: CUDASeam, monkeypatch: pytest.MonkeyPatch) -> None:
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


def cuda_core_child(queue: Any, case: str) -> None:
    role = f"cuda_core_{case}"
    qualified = child_identity(role)
    domain = custody.process_rng_domain()
    assert domain.status()[2] is False
    with pytest.MonkeyPatch.context() as monkeypatch:
        cuda = CUDASeam(True)
        monkeypatch.setattr(custody.torch, "cuda", cuda)
        poison_case(case, domain, cuda, monkeypatch)
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
    else:
        assert trial == "local"
        actions = {
            "resolve_cuda": lambda: gate.resolve_cuda(device=device),
            "complete": lambda: enter(gate.complete(cuda_devices=())),
            "completion_failed": gate.completion_failed,
            "report_failure": lambda: gate.report_failure(error=sentinel),
            "domain_local_cuda_access": lambda: enter(domain.local_cuda_access(participant=participant, contract=contract)),
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
                run_fork_trial(trial, gate, domain, participant, contract, domain_lock, owner_lock, cuda_calls, metadata, modules, output)
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
