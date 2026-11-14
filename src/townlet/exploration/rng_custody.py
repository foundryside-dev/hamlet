"""One process admission domain for cooperating ambient RNG consumers.

This coordinates supported enrolled entrypoints, not arbitrary raw library calls.
Same-object mutation exclusion and real parent boundary authority remain separate.
"""

from __future__ import annotations

import os
import queue
import threading
import weakref
from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from types import MappingProxyType, TracebackType
from typing import Any, Literal, Protocol, cast

import torch


class _OwnedRLock(Protocol):
    """Ownership extension of the actual process RLock and its forwarding probe."""

    def _is_owned(self) -> bool: ...


class _Opaque:
    __slots__ = ("__weakref__",)

    def __new__(cls) -> Any:
        raise TypeError("RNG capabilities are issued by their process domain")

    def __init__(self) -> None:
        raise TypeError("RNG capabilities cannot be reinitialized")

    def __copy__(self) -> Any:
        raise TypeError("RNG capabilities cannot be copied")

    def __reduce__(self) -> Any:
        raise TypeError("RNG capabilities are nonportable")

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        raise TypeError("RNG capabilities cannot be copied")


class RNGParticipant(_Opaque):
    """Identity-bound process membership, never serialized authority."""

    __slots__ = ()


class RNGOperation(_Opaque):
    """Synchronous issuing-thread operation lineage."""

    __slots__ = ()


class RNGDeviceInvocation(_Opaque):
    """Single-use operation context with an immutable own-phase exit outcome."""

    __slots__ = ()

    def __enter__(self) -> RNGOperation:
        return _PROCESS_DOMAIN._enter_invocation(self)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        return _PROCESS_DOMAIN._exit_invocation(self, exc_type, exc_value, traceback)

    def completion_failed(self) -> bool:
        record = _PROCESS_DOMAIN._invocation_record(self)
        if record.state != "exited":
            raise RuntimeError("RNG invocation has no completed outcome")
        return record.failed_completion


class RNGCurrentToken(_Opaque):
    """Producer-issued generation/revision evidence for a prepared candidate."""

    __slots__ = ()


class LocalCUDAContract(_Opaque):
    """Source-issued classification of one concrete owner's finite local route."""

    __slots__ = ()


class RNGAdmission(_Opaque):
    """Open same-domain exclusion, without draw or operation authority."""

    __slots__ = ()

    def resolve_cuda(self, device: torch.device) -> int:
        return _PROCESS_DOMAIN._resolve_cuda(gate=self, device=device)

    def enroll(self, *, participant: RNGParticipant, cuda_devices: tuple[int, ...]) -> None:
        _PROCESS_DOMAIN._enroll(gate=self, participant=participant, cuda_devices=cuda_devices)

    def report_failure(self, *, error: BaseException) -> None:
        _PROCESS_DOMAIN._gate_report_failure(gate=self, error=error)


class LocalCUDAGate(_Opaque):
    """Owner/route-bound exclusion for source-classified ambient-free work."""

    __slots__ = ()

    def resolve_cuda(self, *, device: torch.device) -> int:
        return _PROCESS_DOMAIN._resolve_cuda(gate=self, device=device)

    @contextmanager
    def complete(self, *, cuda_devices: tuple[int, ...]) -> Iterator[None]:
        with _PROCESS_DOMAIN._local_completion(gate=self, cuda_devices=cuda_devices):
            yield

    def completion_failed(self) -> bool:
        return _PROCESS_DOMAIN._gate_record(self).failed_completion

    def report_failure(self, *, error: BaseException) -> None:
        _PROCESS_DOMAIN._gate_report_failure(gate=self, error=error)


@dataclass(frozen=True)
class _LocalCUDARecord:
    owner_type: type[object]
    route: str
    input_type: type[object]
    rationale: str
    healthy: bool
    post_poison: bool


@dataclass(frozen=True)
class _LocalCUDADescriptor:
    owner_kind: Literal["flat", "per"]
    route: str
    input_kind: Literal["tensor", "request", "mapping", "archive", "none", "integer", "indices"]
    rationale: str
    healthy: bool
    post_poison: bool


# Fixed source-issued identities. Canonical classes resolve only under actual
# custody after their producer modules initialize; importing core is CUDA-free.
REPLAY_BUFFER_PUSH_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_PUSH_RECORDED_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_READINESS_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_SERIALIZE_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA = object.__new__(LocalCUDAContract)
REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA = object.__new__(LocalCUDAContract)
PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA = object.__new__(LocalCUDAContract)

# Ordinary dense tensors, builtin data containers and numeric NumPy values are
# source-classified here. Input tags describe the primary argument, not a
# runtime purity detector. GPU post-poison qualification remains separate.
_LOCAL_CUDA_CONTRACTS: Mapping[LocalCUDAContract, _LocalCUDADescriptor] = MappingProxyType(
    {
        REPLAY_BUFFER_PUSH_CUDA: _LocalCUDADescriptor(
            "flat",
            "push",
            "tensor",
            "Ordinary tensor/RewardTensor inputs and retained rows: validation, allocation and owned copies.",
            True,
            False,
        ),
        REPLAY_BUFFER_PUSH_RECORDED_CUDA: _LocalCUDADescriptor(
            "flat",
            "push_recorded",
            "tensor",
            "Ordinary transition inputs, masks and retained rows: legality validation and owned copies.",
            True,
            False,
        ),
        REPLAY_BUFFER_READINESS_CUDA: _LocalCUDADescriptor(
            "flat",
            "readiness",
            "request",
            "ReplayRequest and retained legality tensor: deterministic readiness reduction without draws.",
            True,
            False,
        ),
        REPLAY_BUFFER_SERIALIZE_CUDA: _LocalCUDADescriptor(
            "flat",
            "serialize",
            "none",
            "Retained rows and ordinary canonical archives: chronological CPU copies and archive records.",
            True,
            False,
        ),
        REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA: _LocalCUDADescriptor(
            "flat",
            "validate_serialized",
            "mapping",
            "Ordinary transport and expected width: reached tensor/archive validation and ownership copies.",
            True,
            False,
        ),
        REPLAY_BUFFER_LOAD_FOR_MODE_VALIDATION_CUDA: _LocalCUDADescriptor(
            "flat",
            "load_for_mode",
            "mapping",
            "Ordinary transport validation prelude only; materialization and publication require admission.",
            True,
            False,
        ),
        REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA: _LocalCUDADescriptor(
            "flat",
            "historical_archives",
            "none",
            "Retained canonical archives with ordinary payloads: owned copies, validation and digest.",
            True,
            False,
        ),
        REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA: _LocalCUDADescriptor(
            "flat",
            "install_historical_archive",
            "archive",
            "Incoming and retained ordinary canonical archives: owned validation, digest and merge.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_PUSH_CUDA: _LocalCUDADescriptor(
            "per",
            "push",
            "tensor",
            "Ordinary transition/RewardTensor inputs and rows: copies plus deterministic priority and stable-ID staging.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_PUSH_RECORDED_CUDA: _LocalCUDADescriptor(
            "per",
            "push_recorded",
            "tensor",
            "Ordinary transition inputs, masks and rows: legality checks, copies and priority/ID staging.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_DECLARE_UNCONSTRAINED_ACTION_DIM_CUDA: _LocalCUDADescriptor(
            "per",
            "declare_unconstrained_action_dim",
            "integer",
            "Integer width and retained actions: deterministic legality checks and mask allocation.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_READINESS_CUDA: _LocalCUDADescriptor(
            "per",
            "readiness",
            "request",
            "ReplayRequest, configured mode and retained legality tensor: readiness reduction without draws.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA: _LocalCUDADescriptor(
            "per",
            "serialize",
            "none",
            "Ordinary rows, archives, numeric priorities/IDs and sampler metadata: copies without RNG advancement.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_VALIDATE_SERIALIZED_CUDA: _LocalCUDADescriptor(
            "per",
            "validate_serialized",
            "mapping",
            "Ordinary transport: tensor/archive/priority/ID checks and offside deterministic engine restore.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_HISTORICAL_ARCHIVES_CUDA: _LocalCUDADescriptor(
            "per",
            "historical_archives",
            "none",
            "Ordinary canonical archives: owned copies/digest and detached PER validation without enrollment.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_INSTALL_HISTORICAL_ARCHIVE_CUDA: _LocalCUDADescriptor(
            "per",
            "install_historical_archive",
            "archive",
            "Ordinary incoming/retained archives: owned digest/merge and detached PER validation.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_UPDATE_PRIORITIES_CUDA: _LocalCUDADescriptor(
            "per",
            "update_priorities",
            "indices",
            "Numeric NumPy physical indices and td_errors tensor: CPU conversion and staged duplicate-max updates.",
            True,
            False,
        ),
        PRIORITIZED_REPLAY_BUFFER_UPDATE_UNIT_PRIORITIES_CUDA: _LocalCUDADescriptor(
            "per",
            "update_unit_priorities",
            "indices",
            "Numeric stable IDs, current ID map and td_errors tensor: CPU conversion and staged duplicate-max updates.",
            True,
            False,
        ),
    }
)


@dataclass
class _Gate:
    thread: int
    lineage: RNGOperation | None
    participant: RNGParticipant | None
    owner: object | None
    contract: LocalCUDAContract | None
    policy: _LocalCUDARecord | None
    pins: list[object]
    completion: str
    failed_completion: bool


@dataclass(frozen=True)
class _Member:
    owner: weakref.ReferenceType[object]
    cuda_devices: tuple[int, ...]
    entrypoints: frozenset[str]


@dataclass
class _Operation:
    thread: int
    generation: int
    revision: int
    participants: set[RNGParticipant]
    kinds: list[str]
    pins: list[object]
    devices: set[int]
    issued: list[RNGCurrentToken]
    reported: list[BaseException]


@dataclass
class _Current:
    participant: RNGParticipant
    operation: RNGOperation
    generation: int
    revision: int
    currency: int


@dataclass
class _Invocation:
    thread: threading.Thread
    state: str
    participant: RNGParticipant | None
    operation_kind: str | None
    lineage: RNGOperation | None
    cuda_devices: tuple[int, ...]
    context: AbstractContextManager[RNGOperation] | None
    failed_completion: bool


_CONSTRUCTION = object()


class AmbientRNGDomain:
    """Actual common exclusion, membership, operation identity and poison owner.

    Use process_rng_domain(); independently usable domain instances are refused.
    No operation or installed private stream may be held across await/yield.
    """

    def __init__(self, authority: object):
        if authority is not _CONSTRUCTION:
            raise TypeError("Use the sole process_rng_domain")
        self._lock = threading.RLock()
        self._local = threading.local()
        self._members: dict[RNGParticipant, _Member] = {}
        self._tokens: weakref.WeakKeyDictionary[RNGCurrentToken, _Current] = weakref.WeakKeyDictionary()
        self._operations: dict[RNGOperation, _Operation] = {}
        self._invocations: weakref.WeakKeyDictionary[RNGDeviceInvocation, _Invocation] = weakref.WeakKeyDictionary()
        self._gates: dict[RNGAdmission | LocalCUDAGate, _Gate] = {}
        self._local_cuda_policies: dict[LocalCUDAContract, tuple[_LocalCUDADescriptor, _LocalCUDARecord]] = {}
        self._retired: queue.SimpleQueue[RNGParticipant] = queue.SimpleQueue()
        self._generation = 0
        self._revision = 0
        self._currency = 0
        self._ambient_revision = 0
        self._poison: BaseException | None = None
        self._pid = os.getpid()
        self._cuda_ready = False
        self._cuda_busy: int | None = None

    def _check_pid(self) -> None:
        if self._pid != os.getpid():
            raise RuntimeError("RNG custody cannot be inherited by another process")

    def _usable(self) -> None:
        self._check_pid()
        if self._poison is not None:
            raise RuntimeError("Ambient RNG domain is poisoned after failed restoration") from self._poison

    def _not_busy(self) -> None:
        if self._cuda_busy == threading.get_ident():
            raise RuntimeError("Unrelated RNG reentry during a CUDA transaction is forbidden")

    def _has_local_gate(self) -> bool:
        return any(type(gate) is LocalCUDAGate and record.thread == threading.get_ident() for gate, record in self._gates.items())

    def _active(self) -> RNGOperation | None:
        return getattr(self._local, "operation", None)

    def _collect_retired(self) -> None:
        """Drain weak callbacks only under exclusive idle custody."""
        if self._active() is not None:
            return
        while True:
            try:
                participant = self._retired.get_nowait()
            except queue.Empty:
                return
            member = self._members.get(participant)
            if member is not None and member.owner() is None:
                del self._members[participant]
                self._generation += 1

    def _member(self, participant: RNGParticipant) -> _Member:
        if type(participant) is not RNGParticipant or participant not in self._members:
            raise ValueError("RNG participant is foreign or no longer registered")
        member = self._members[participant]
        if member.owner() is None:
            raise ValueError("RNG participant owner is no longer alive")
        return member

    def register(self, *, owner: object, cuda_devices: tuple[int, ...], entrypoints: frozenset[str]) -> RNGParticipant:
        self._check_pid()
        with self._lock:
            self._usable()
            self._not_busy()
            if self._active() is not None or self._has_local_gate():
                raise RuntimeError("RNG membership requires exclusive idle custody")
            self._collect_retired()
            if (
                type(cuda_devices) is not tuple
                or any(type(index) is not int or index < 0 for index in cuda_devices)
                or tuple(sorted(set(cuda_devices))) != cuda_devices
            ):
                raise ValueError("RNG CUDA inventory must be explicit, sorted and unique")
            if cuda_devices and (not torch.cuda.is_initialized() or any(index >= torch.cuda.device_count() for index in cuda_devices)):
                raise ValueError("Initialize explicitly declared RNG devices before registration")
            if type(entrypoints) is not frozenset or not entrypoints or any(type(name) is not str or not name for name in entrypoints):
                raise ValueError("RNG registration requires explicit nonempty entrypoints")
            if any(member.owner() is owner for member in self._members.values()):
                raise ValueError("RNG owner already has a registration")
            participant = object.__new__(RNGParticipant)

            def retired(reference: weakref.ReferenceType[object]) -> None:
                self._retired.put(participant)

            try:
                reference = weakref.ref(owner, retired)
            except TypeError as error:
                raise ValueError("RNG registration requires a weak-referenceable lifetime owner") from error
            self._members[participant] = _Member(reference, cuda_devices, entrypoints)
            self._generation += 1
            return participant

    def unregister(self, *, participant: RNGParticipant) -> None:
        self._check_pid()
        with self._lock:
            self._usable()
            self._not_busy()
            if self._active() is not None or self._has_local_gate():
                raise RuntimeError("RNG membership requires exclusive idle custody")
            self._collect_retired()
            self._member(participant)
            del self._members[participant]
            self._generation += 1

    def _adopt(
        self,
        *,
        participant: RNGParticipant,
        previous_owner: object,
        owner: object,
        cuda_devices: tuple[int, ...],
        entrypoints: frozenset[str],
    ) -> RNGParticipant:
        self._check_pid()
        with self._lock:
            self._usable()
            self._not_busy()
            if self._active() is not None:
                raise RuntimeError("RNG ownership adoption requires exclusive idle custody")
            self._collect_retired()
            retire_previous = self._member(participant).owner() is previous_owner
            replacement = self.register(owner=owner, cuda_devices=cuda_devices, entrypoints=entrypoints)
            if retire_previous:
                self.unregister(participant=participant)
            return replacement

    def _authenticate(self, operation: RNGOperation) -> _Operation:
        if type(operation) is not RNGOperation or operation is not self._active() or operation not in self._operations:
            raise ValueError("RNG operation lineage is foreign or expired")
        record = self._operations[operation]
        if record.thread != threading.get_ident() or record.generation != self._generation:
            raise ValueError("RNG operation lineage belongs to another thread or membership")
        return record

    @staticmethod
    def _complete(devices: tuple[int, ...]) -> None:
        # Empty CPU inventory never accesses a CUDA attribute or availability API.
        for index in devices:
            torch.cuda.synchronize(index)

    def _finish(
        self, operation: RNGOperation, devices: tuple[int, ...], failures: list[BaseException], completion: _Invocation | None
    ) -> None:
        try:
            self._complete(devices)
        except BaseException as error:
            self.poison(operation=operation, error=error)
            failures.append(error)
        else:
            if completion is not None:
                completion.failed_completion = False
        failures.extend(self._authenticate(operation).reported)

    @staticmethod
    def _raise(failures: list[BaseException]) -> None:
        if len(failures) == 1:
            raise failures[0]
        if failures:
            distinct: list[BaseException] = []
            seen: list[BaseException] = []

            def retain(error: BaseException) -> BaseException | None:
                if isinstance(error, BaseExceptionGroup):
                    children: list[BaseException] = []
                    for child in error.exceptions:
                        kept = retain(child)
                        if kept is not None:
                            children.append(kept)
                    if not children:
                        return None
                    if len(children) == len(error.exceptions) and all(
                        child is original for child, original in zip(children, error.exceptions)
                    ):
                        return error
                    return error.derive(children)
                if all(error is not previous for previous in seen):
                    seen.append(error)
                    return error
                return None

            for error in failures:
                kept = retain(error)
                if kept is not None:
                    distinct.append(kept)
            if len(distinct) == 1:
                raise distinct[0]
            raise BaseExceptionGroup("RNG operation and device completion failed", distinct)

    @staticmethod
    def _device_tuple(cuda_devices: tuple[int, ...]) -> None:
        if (
            type(cuda_devices) is not tuple
            or any(type(index) is not int or index < 0 for index in cuda_devices)
            or tuple(sorted(set(cuda_devices))) != cuda_devices
        ):
            raise ValueError("RNG CUDA inventory must be explicit, sorted and unique")

    def _resolve_local_cuda_record(self, *, descriptor: _LocalCUDADescriptor) -> _LocalCUDARecord:
        self._check_pid()
        if not cast(_OwnedRLock, self._lock)._is_owned():
            raise RuntimeError("Local CUDA policy resolution requires its actual domain exclusion")
        self._not_busy()
        if type(descriptor) is not _LocalCUDADescriptor:
            raise ValueError("Local CUDA contract has no immutable source descriptor")
        owner_type: type[object]
        if descriptor.owner_kind == "flat":
            from townlet.training.replay_buffer import ReplayBuffer

            owner_type = ReplayBuffer
        elif descriptor.owner_kind == "per":
            from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer

            owner_type = PrioritizedReplayBuffer
        else:
            raise ValueError("Local CUDA descriptor has no canonical owner")
        input_type: type[object]
        if descriptor.input_kind == "tensor":
            input_type = torch.Tensor
        elif descriptor.input_kind == "request":
            from townlet.training.replay_contract import ReplayRequest

            input_type = ReplayRequest
        elif descriptor.input_kind == "mapping":
            input_type = Mapping
        elif descriptor.input_kind == "archive":
            from townlet.training.historical_checkpoint import HistoricalReplayArchive

            input_type = HistoricalReplayArchive
        elif descriptor.input_kind == "none":
            input_type = type(None)
        elif descriptor.input_kind == "integer":
            input_type = int
        elif descriptor.input_kind == "indices":
            from numpy import ndarray

            input_type = ndarray
        else:
            raise ValueError("Local CUDA descriptor has no canonical input type")
        if not isinstance(owner_type, type) or not isinstance(input_type, type):
            raise ValueError("Local CUDA canonical classes are unavailable")
        return _LocalCUDARecord(owner_type, descriptor.route, input_type, descriptor.rationale, descriptor.healthy, descriptor.post_poison)

    def _local_cuda_policy(self, *, contract: LocalCUDAContract) -> _LocalCUDARecord:
        self._check_pid()
        if not cast(_OwnedRLock, self._lock)._is_owned():
            raise RuntimeError("Local CUDA policy resolution requires its actual domain exclusion")
        self._not_busy()
        if type(contract) is not LocalCUDAContract or contract not in _LOCAL_CUDA_CONTRACTS:
            raise ValueError("Local CUDA contract is not source-issued")
        descriptor = _LOCAL_CUDA_CONTRACTS[contract]
        if type(descriptor) is not _LocalCUDADescriptor:
            raise ValueError("Local CUDA contract has no immutable source descriptor")
        cached = self._local_cuda_policies.get(contract)
        if cached is not None:
            if cached[0] is not descriptor or type(cached[1]) is not _LocalCUDARecord:
                raise ValueError("Local CUDA contract source policy changed")
            return cached[1]
        policy = self._resolve_local_cuda_record(descriptor=descriptor)
        if type(policy) is not _LocalCUDARecord:
            raise ValueError("Local CUDA contract has no immutable source policy")
        self._local_cuda_policies[contract] = (descriptor, policy)
        return policy

    def _gate_record(self, gate: RNGAdmission | LocalCUDAGate) -> _Gate:
        # Methods already hold the issuing scope's real lock. Authenticate before
        # any lock/owner/CUDA work, including wrong-thread and inherited callers.
        self._check_pid()
        if type(gate) not in {RNGAdmission, LocalCUDAGate} or gate not in self._gates:
            raise ValueError("RNG gate is foreign or expired")
        record = self._gates[gate]
        if record.thread != threading.get_ident():
            raise ValueError("RNG gate belongs to another thread")
        if not cast(_OwnedRLock, self._lock)._is_owned():
            raise RuntimeError("RNG gate requires its actual domain exclusion")
        if record.lineage is not None:
            self._authenticate(record.lineage)
        if type(gate) is LocalCUDAGate:
            if record.participant is None or record.contract is None or record.policy is None:
                raise ValueError("Local CUDA gate has no authentic binding")
            member = self._member(record.participant)
            cached = self._local_cuda_policies.get(record.contract)
            if (
                member.owner() is not record.owner
                or cached is None
                or cached[0] is not _LOCAL_CUDA_CONTRACTS.get(record.contract)
                or cached[1] is not record.policy
                or type(record.owner) is not record.policy.owner_type
            ):
                raise ValueError("Local CUDA gate owner/route binding changed")
        return record

    def _local_permission(self, record: _Gate) -> None:
        policy = record.policy
        if policy is None or not policy.healthy:
            raise RuntimeError("Local CUDA route is not admitted by source policy")
        if self._poison is not None and (not policy.post_poison or not self._cuda_ready):
            raise RuntimeError("Poisoned local CUDA access requires a previously READY qualified route") from self._poison

    def _close_gate(self, gate: RNGAdmission | LocalCUDAGate) -> None:
        record = self._gate_record(gate)
        self._not_busy()
        unfinished = record.completion == "active"
        if unfinished:
            error = RuntimeError("Local CUDA gate cannot exit with unfinished completion")
            record.failed_completion = True
            self._gate_report_failure(gate=gate, error=error)
        del self._gates[gate]
        record.pins.clear()
        record.owner = None
        if unfinished:
            raise error

    @contextmanager
    def admission(self, *, lineage: RNGOperation | None) -> Iterator[RNGAdmission]:
        self._check_pid()
        self._not_busy()
        with self._lock:
            self._usable()
            self._not_busy()
            if self._has_local_gate():
                raise RuntimeError("Local CUDA scope cannot admit unrelated RNG work")
            active = self._active()
            if active is None:
                if lineage is not None:
                    raise ValueError("RNG operation lineage is foreign or expired")
            elif lineage is None:
                raise RuntimeError("Unrelated same-thread RNG reentry is forbidden")
            else:
                self._authenticate(lineage)
            self._collect_retired()
            gate = object.__new__(RNGAdmission)
            self._gates[gate] = _Gate(threading.get_ident(), lineage, None, None, None, None, [], "unused", False)
            try:
                yield gate
            finally:
                self._close_gate(gate)

    @contextmanager
    def local_cuda_access(self, *, participant: RNGParticipant, contract: LocalCUDAContract) -> Iterator[LocalCUDAGate]:
        self._check_pid()
        self._not_busy()
        with self._lock:
            self._not_busy()
            if self._has_local_gate():
                raise RuntimeError("Local CUDA helpers must reuse their producer's existing scope")
            self._collect_retired()
            if type(contract) is not LocalCUDAContract or contract not in _LOCAL_CUDA_CONTRACTS:
                raise ValueError("Local CUDA contract is not source-issued")
            member = self._member(participant)
            owner = member.owner()
            policy = self._local_cuda_policy(contract=contract)
            if owner is None or type(owner) is not policy.owner_type:
                raise ValueError("Local CUDA contract does not authorize this exact owner class")
            record = _Gate(threading.get_ident(), self._active(), participant, owner, contract, policy, [owner], "unused", False)
            self._local_permission(record)
            gate = object.__new__(LocalCUDAGate)
            self._gates[gate] = record
            try:
                yield gate
            finally:
                self._close_gate(gate)

    def _gate_report_failure(self, *, gate: RNGAdmission | LocalCUDAGate, error: BaseException) -> None:
        self._gate_record(gate)
        if not isinstance(error, BaseException):
            raise TypeError("RNG gate failure must be an exception")
        self._record_failure(error)

    def _record_failure(self, error: BaseException) -> None:
        """Internal first cause/reporting under already authenticated custody."""
        if self._poison is None:
            self._poison = error
        active = self._active()
        if active is not None:
            reported = self._authenticate(active).reported
            if all(error is not previous for previous in reported):
                reported.append(error)

    def _runtime_snapshot(self, gate: RNGAdmission | LocalCUDAGate) -> tuple[bool, int]:
        try:
            initialized = torch.cuda.is_initialized()
            if initialized:
                count = torch.cuda.device_count()
            else:
                count = 0
            if type(initialized) is not bool or type(count) is not int or (initialized and count <= 0):
                raise RuntimeError("CUDA runtime returned invalid initialized device inventory")
            if not initialized or self._poison is None:
                self._cuda_ready = initialized
            return initialized, count
        except BaseException as error:
            self._cuda_ready = False
            self._gate_report_failure(gate=gate, error=error)
            raise

    def _resolve_cuda(self, *, gate: RNGAdmission | LocalCUDAGate, device: torch.device) -> int:
        record = self._gate_record(gate)
        self._not_busy()
        if type(device) is not torch.device or device.type != "cuda":
            raise ValueError("CUDA resolution requires a torch.device CUDA selector")
        if record.completion != "unused":
            raise RuntimeError("CUDA selection must precede local completion work")
        if type(gate) is LocalCUDAGate:
            self._local_permission(record)
        else:
            self._usable()
        self._cuda_busy = threading.get_ident()
        try:
            initialized, count = self._runtime_snapshot(gate)
            if not initialized:
                if self._active() is not None:
                    raise RuntimeError("CUDA initialization requires idle preflight before the parent operation")
                if self._poison is not None:
                    raise RuntimeError("Poisoned local CUDA access cannot initialize a runtime") from self._poison
                self._cuda_ready = False
                self._currency += 1
                try:
                    torch.cuda.init()
                    initialized, count = self._runtime_snapshot(gate)
                    if not initialized:
                        raise RuntimeError("CUDA initialization did not establish an initialized runtime")
                except BaseException as error:
                    self._cuda_ready = False
                    self._gate_report_failure(gate=gate, error=error)
                    raise
            self._cuda_ready = True
            if device.index is not None:
                if not 0 <= device.index < count:
                    raise ValueError("CUDA device index is outside initialized runtime inventory")
                return device.index
            try:
                selected = torch.cuda.current_device()
                if type(selected) is not int or not 0 <= selected < count:
                    raise RuntimeError("CUDA runtime returned an invalid current device")
                return selected
            except BaseException as error:
                self._cuda_ready = False
                self._gate_report_failure(gate=gate, error=error)
                raise
        finally:
            self._cuda_busy = None

    def _enroll(self, *, gate: RNGAdmission, participant: RNGParticipant, cuda_devices: tuple[int, ...]) -> None:
        record = self._gate_record(gate)
        self._not_busy()
        self._usable()
        if self._active() is not None or self._has_local_gate():
            raise RuntimeError("RNG membership requires exclusive idle custody")
        self._device_tuple(cuda_devices)
        member = self._member(participant)
        owner = member.owner()
        if owner is None:
            raise ValueError("RNG participant owner is no longer alive")
        if cuda_devices:
            self._cuda_busy = threading.get_ident()
            try:
                initialized, count = self._runtime_snapshot(gate)
                if not initialized or any(index >= count for index in cuda_devices):
                    raise ValueError("Enroll only explicitly initialized CUDA device indices")
            finally:
                self._cuda_busy = None
        union = tuple(sorted(set(member.cuda_devices).union(cuda_devices)))
        if union != member.cuda_devices:
            self._members[participant] = _Member(member.owner, union, member.entrypoints)
            self._generation += 1
        if all(owner is not pinned for pinned in record.pins):
            record.pins.append(owner)

    @contextmanager
    def _local_completion(self, *, gate: LocalCUDAGate, cuda_devices: tuple[int, ...]) -> Iterator[None]:
        record = self._gate_record(gate)
        self._not_busy()
        self._local_permission(record)
        if record.completion != "unused":
            raise RuntimeError("Local CUDA gate permits exactly one completion scope")
        self._device_tuple(cuda_devices)
        if cuda_devices:
            self._cuda_busy = threading.get_ident()
            try:
                initialized, count = self._runtime_snapshot(gate)
                if not initialized or any(index >= count for index in cuda_devices):
                    raise ValueError("Local completion requires initialized CUDA indices")
                self._cuda_ready = True
            finally:
                self._cuda_busy = None
        record.completion = "active"
        failures: list[BaseException] = []
        try:
            yield
        except BaseException as error:
            failures.append(error)
        finally:
            self._gate_record(gate)
            self._cuda_busy = threading.get_ident()
            try:
                for index in cuda_devices:
                    try:
                        torch.cuda.synchronize(index)
                    except BaseException as error:
                        record.failed_completion = True
                        self._gate_report_failure(gate=gate, error=error)
                        failures.append(error)
            finally:
                self._cuda_busy = None
                record.completion = "done"
        self._raise(failures)

    def _commit_ambient(self, operation: RNGOperation) -> None:
        self._authenticate(operation)
        self._ambient_revision += 1

    @contextmanager
    def operation(self, *, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation | None) -> Iterator[RNGOperation]:
        with self._operation(
            participant=participant, operation_kind=operation_kind, lineage=lineage, full_member=True, cuda_devices=(), completion=None
        ) as operation:
            yield operation

    @contextmanager
    def device_operation(
        self, *, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation | None, cuda_devices: tuple[int, ...]
    ) -> Iterator[RNGOperation]:
        with self._operation(
            participant=participant,
            operation_kind=operation_kind,
            lineage=lineage,
            full_member=False,
            cuda_devices=cuda_devices,
            completion=None,
        ) as operation:
            yield operation

    def device_invocation(
        self, *, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation | None, cuda_devices: tuple[int, ...]
    ) -> RNGDeviceInvocation:
        self._check_pid()
        self._member(participant)
        if type(operation_kind) is not str or not operation_kind:
            raise ValueError("RNG invocation requires an explicit nonempty operation kind")
        if lineage is not None and (type(lineage) is not RNGOperation or lineage not in self._operations):
            raise ValueError("RNG operation lineage is foreign or expired")
        self._device_tuple(cuda_devices)
        invocation = object.__new__(RNGDeviceInvocation)
        self._invocations[invocation] = _Invocation(
            threading.current_thread(), "issued", participant, operation_kind, lineage, cuda_devices, None, True
        )
        return invocation

    def _invocation_record(self, invocation: RNGDeviceInvocation) -> _Invocation:
        # Refuse inherited/forged/wrong-thread calls before any exclusion or CUDA.
        self._check_pid()
        if type(invocation) is not RNGDeviceInvocation or invocation not in self._invocations:
            raise ValueError("RNG invocation is foreign or unissued")
        record = self._invocations[invocation]
        if record.thread is not threading.current_thread():
            raise ValueError("RNG invocation belongs to another thread")
        return record

    @staticmethod
    def _release_invocation(record: _Invocation) -> None:
        record.participant = None
        record.operation_kind = None
        record.lineage = None
        record.cuda_devices = ()
        record.context = None

    def _enter_invocation(self, invocation: RNGDeviceInvocation) -> RNGOperation:
        record = self._invocation_record(invocation)
        if record.state != "issued":
            raise RuntimeError("RNG invocation permits exactly one entry")
        record.state = "entering"
        try:
            if record.participant is None or record.operation_kind is None:
                raise RuntimeError("RNG invocation has no execution binding")
            context = self._operation(
                participant=record.participant,
                operation_kind=record.operation_kind,
                lineage=record.lineage,
                full_member=False,
                cuda_devices=record.cuda_devices,
                completion=record,
            )
            record.context = context
            operation = context.__enter__()
        except BaseException:
            record.state = "entry_failed"
            self._release_invocation(record)
            raise
        record.state = "active"
        return operation

    def _exit_invocation(
        self,
        invocation: RNGDeviceInvocation,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        record = self._invocation_record(invocation)
        if record.state != "active" or record.context is None:
            raise RuntimeError("RNG invocation requires one active exit")
        context = record.context
        # Taking the execution reference also refuses recursive exit while the
        # phase is running; the outcome stays unreadable until finally seals it.
        record.context = None
        try:
            context.__exit__(exc_type, exc_value, traceback)
        finally:
            self._release_invocation(record)
            record.state = "exited"
        return False

    def _operation_inventory(self, *, member: _Member, cuda_devices: tuple[int, ...]) -> None:
        self._device_tuple(cuda_devices)
        if not set(cuda_devices).issubset(member.cuda_devices):
            raise ValueError("RNG operation device inventory is outside enrolled membership; idle preflight is required")
        if not cuda_devices:
            return
        self._cuda_busy = threading.get_ident()
        try:
            try:
                initialized = torch.cuda.is_initialized()
                if initialized:
                    count = torch.cuda.device_count()
                else:
                    count = 0
                if type(initialized) is not bool or type(count) is not int or (initialized and count <= 0):
                    raise RuntimeError("CUDA runtime returned invalid initialized device inventory")
            except BaseException as error:
                self._cuda_ready = False
                self._record_failure(error)
                raise
            self._cuda_ready = initialized
            if not initialized or any(index >= count for index in cuda_devices):
                raise ValueError("RNG operation requires initialized enrolled CUDA indices")
        finally:
            self._cuda_busy = None

    @contextmanager
    def _operation(
        self,
        *,
        participant: RNGParticipant,
        operation_kind: str,
        lineage: RNGOperation | None,
        full_member: bool,
        cuda_devices: tuple[int, ...],
        completion: _Invocation | None,
    ) -> Iterator[RNGOperation]:
        # Another thread waits at this actual lock before any enrolled work.
        self._check_pid()
        self._not_busy()
        with self._lock:
            self._usable()
            self._not_busy()
            if self._has_local_gate():
                raise RuntimeError("Local CUDA scope cannot admit unrelated RNG work")
            self._collect_retired()
            member = self._member(participant)
            owner = member.owner()
            if owner is None:
                raise ValueError("RNG participant owner is no longer alive")
            if operation_kind not in member.entrypoints:
                raise ValueError("RNG entrypoint is not registered for this owner")
            active = self._active()
            if active is not None:
                if lineage is None:
                    raise RuntimeError("Unrelated same-thread RNG reentry is forbidden")
                self._authenticate(lineage)
            elif lineage is not None:
                raise ValueError("RNG operation lineage is foreign or expired")
            if full_member:
                devices = member.cuda_devices
            else:
                self._operation_inventory(member=member, cuda_devices=cuda_devices)
                devices = cuda_devices
            if active is not None:
                record = self._authenticate(active)
                if participant not in record.participants:
                    record.pins.append(owner)
                record.participants.add(participant)
                record.devices.update(devices)
                # Offside preparation, validation and child publication compose
                # within one held parent lease. Actual nested ordinary work still
                # invalidates candidates, even when it consumes no RNG bytes.
                ordinary = operation_kind not in {"prepare", "validate", "install"} and not any(
                    kind not in {"validate", "install"} for kind in record.kinds[1:]
                )
                if ordinary:
                    self._currency += 1
                record.kinds.append(operation_kind)
                failures: list[BaseException] = []
                try:
                    yield active
                except BaseException as error:
                    failures.append(error)
                finally:
                    self._finish(active, devices, failures, completion)
                    if ordinary or failures:
                        self._currency += 1
                    record.kinds.pop()
                self._raise(failures)
                return
            operation = object.__new__(RNGOperation)
            record = _Operation(
                threading.get_ident(),
                self._generation,
                self._revision,
                {participant},
                [operation_kind],
                [owner],
                set(devices),
                [],
                [],
            )
            self._operations[operation] = record
            self._local.operation = operation
            ordinary = operation_kind not in {"prepare", "validate", "install"}
            if ordinary:
                self._currency += 1
            failures = []
            try:
                yield operation
            except BaseException as error:
                failures.append(error)
            finally:
                self._finish(operation, tuple(sorted(record.devices)), failures, completion)
                if ordinary or failures:
                    self._currency += 1
                # Even unchanged bytes or an exception invalidate released work.
                self._revision += 1
                del self._operations[operation]
                self._local.operation = None
                record.pins.clear()
                before_retirement = self._generation
                self._collect_retired()
                if not failures:
                    for token in record.issued:
                        issued = self._tokens.get(token)
                        if (
                            issued is not None
                            and issued.operation is operation
                            and issued.currency == self._currency
                            and issued.generation == before_retirement
                        ):
                            # Finalize only this operation's still-current work
                            # after its own idle weak-membership bookkeeping.
                            issued.generation = self._generation
            self._raise(failures)

    def current_token(self, *, participant: RNGParticipant, operation: RNGOperation) -> RNGCurrentToken:
        self._check_pid()
        with self._lock:
            self._usable()
            self._not_busy()
            self._member(participant)
            record = self._authenticate(operation)
            if participant not in record.participants:
                raise ValueError("RNG owner did not enter this operation")
            token = object.__new__(RNGCurrentToken)
            self._tokens[token] = _Current(participant, operation, self._generation, self._revision, self._currency)
            record.issued.append(token)
            return token

    def validate_current(self, *, token: RNGCurrentToken, operation: RNGOperation) -> None:
        self._check_pid()
        with self._lock:
            self._usable()
            self._not_busy()
            record = self._authenticate(operation)
            if type(token) is not RNGCurrentToken or token not in self._tokens:
                raise ValueError("RNG current token is foreign or consumed")
            expected = self._tokens[token]
            self._member(expected.participant)
            if expected.participant not in record.participants or expected.generation != self._generation:
                raise ValueError("RNG preparation membership changed")
            if expected.operation is operation:
                revision = expected.revision
            else:
                revision = expected.revision + 1
            if self._revision != revision:
                raise ValueError("RNG preparation is stale after an intervening operation")
            if self._currency != expected.currency:
                raise ValueError("RNG preparation is stale after intervening nested work")

    def _consume_token(self, token: RNGCurrentToken) -> None:
        self._tokens.pop(token)

    def poison(self, *, operation: RNGOperation, error: BaseException) -> None:
        with self._lock:
            self._authenticate(operation)
            if self._poison is None:
                self._poison = error

    def status(self) -> tuple[int, int, bool]:
        """Pure diagnostics; these values never grant publication authority."""
        with self._lock:
            self._collect_retired()
            return self._generation, self._revision, self._poison is not None


_PROCESS_DOMAIN = AmbientRNGDomain(_CONSTRUCTION)


def process_rng_domain() -> AmbientRNGDomain:
    return _PROCESS_DOMAIN
