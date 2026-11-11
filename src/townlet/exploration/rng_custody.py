"""One process admission domain for cooperating ambient RNG consumers.

This coordinates supported enrolled entrypoints, not arbitrary raw library calls.
Same-object mutation exclusion and real parent boundary authority remain separate.
"""

from __future__ import annotations

import os
import queue
import threading
import weakref
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import torch


class _Opaque:
    __slots__ = ("__weakref__",)

    def __new__(cls) -> Any:
        raise TypeError("RNG capabilities are issued by their process domain")

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


class RNGCurrentToken(_Opaque):
    """Producer-issued generation/revision evidence for a prepared candidate."""

    __slots__ = ()


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


@dataclass
class _Current:
    participant: RNGParticipant
    operation: RNGOperation
    generation: int
    revision: int
    currency: int


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
        self._retired: queue.SimpleQueue[RNGParticipant] = queue.SimpleQueue()
        self._generation = 0
        self._revision = 0
        self._currency = 0
        self._ambient_revision = 0
        self._poison: BaseException | None = None
        self._pid = os.getpid()

    def _usable(self) -> None:
        if self._pid != os.getpid():
            raise RuntimeError("RNG custody cannot be inherited by another process")
        if self._poison is not None:
            raise RuntimeError("Ambient RNG domain is poisoned after failed restoration") from self._poison

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
        with self._lock:
            self._usable()
            if self._active() is not None:
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
        with self._lock:
            self._usable()
            if self._active() is not None:
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
        with self._lock:
            self._usable()
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

    def _finish(self, operation: RNGOperation, devices: tuple[int, ...], failures: list[BaseException]) -> None:
        try:
            self._complete(devices)
        except BaseException as error:
            self.poison(operation=operation, error=error)
            failures.append(error)

    @staticmethod
    def _raise(failures: list[BaseException]) -> None:
        if len(failures) == 1:
            raise failures[0]
        if failures:
            raise BaseExceptionGroup("RNG operation and device completion failed", failures)

    def _commit_ambient(self, operation: RNGOperation) -> None:
        self._authenticate(operation)
        self._ambient_revision += 1

    @contextmanager
    def operation(self, *, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation | None) -> Iterator[RNGOperation]:
        # Another thread waits at this actual lock before any enrolled work.
        with self._lock:
            self._usable()
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
                record = self._authenticate(lineage)
                if participant not in record.participants:
                    record.pins.append(owner)
                record.participants.add(participant)
                record.devices.update(member.cuda_devices)
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
                    yield lineage
                except BaseException as error:
                    failures.append(error)
                finally:
                    self._finish(lineage, member.cuda_devices, failures)
                    if ordinary or failures:
                        self._currency += 1
                    record.kinds.pop()
                self._raise(failures)
                return
            if lineage is not None:
                raise ValueError("RNG operation lineage is foreign or expired")
            operation = object.__new__(RNGOperation)
            record = _Operation(
                threading.get_ident(),
                self._generation,
                self._revision,
                {participant},
                [operation_kind],
                [owner],
                set(member.cuda_devices),
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
                self._finish(operation, tuple(sorted(record.devices)), failures)
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
        with self._lock:
            self._usable()
            self._member(participant)
            record = self._authenticate(operation)
            if participant not in record.participants:
                raise ValueError("RNG owner did not enter this operation")
            token = object.__new__(RNGCurrentToken)
            self._tokens[token] = _Current(participant, operation, self._generation, self._revision, self._currency)
            record.issued.append(token)
            return token

    def validate_current(self, *, token: RNGCurrentToken, operation: RNGOperation) -> None:
        with self._lock:
            self._usable()
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
