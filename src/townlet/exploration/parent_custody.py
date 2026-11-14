"""Finite runtime/BANK custody. Execution authority never enters restore dictionaries."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import current_thread
from typing import Any
from weakref import WeakKeyDictionary, ref

from townlet.exploration.rng_custody import RNGOperation, process_rng_domain

_scopes: WeakKeyDictionary[Any, Any] = WeakKeyDictionary()
_records: WeakKeyDictionary[_Custody, _Record] = WeakKeyDictionary()
_PID = os.getpid()
_COHORT = frozenset({"prepare_restore", "prepare_private_initialization", "install_restore", "validate_restore_data"})


@dataclass(frozen=True, slots=True)
class RestoreInstallationResult:
    """An observation of one actual install attempt, never installation authority."""

    status: str
    call_entered: bool
    operation_entered: bool
    handle_consumed: bool
    bank_publication: str
    runtime_publication: str
    completion: str
    returned_normally: bool
    runtime_handle_consumed: bool


_INSTALLATION_FIELDS = (
    ("pending", "in_progress", "sealed"),
    (False, True),
    (False, True),
    (False, True),
    ("none", "complete", "uncertain"),
    ("not_applicable", "none", "complete", "uncertain"),
    ("not_entered", "succeeded", "failed", "uncertified"),
    (False, True),
    (False, True),
)


def _installation_results(depth: int, values: tuple[Any, ...]) -> Any:
    if depth == len(_INSTALLATION_FIELDS):
        return RestoreInstallationResult(*values)
    return tuple(_installation_results(depth + 1, values + (value,)) for value in _INSTALLATION_FIELDS[depth])


# Immutable variants are allocated before any native token exists. Recording a
# publication/completion cut only selects an existing value; it calls no loader,
# allocator, serializer, RNG operation, exporter or user callback.
_INSTALLATION_RESULTS = _installation_results(0, ())


class _InstallationCell:
    def __init__(self, owner: Any, handle: Any, runtime: bool):
        self.owner, self.handle_id = ref(owner), id(handle)
        self.status = 0
        self.call_entered = self.operation_entered = self.handle_consumed = False
        self.bank_publication, self.runtime_publication = 0, 1 if runtime else 0
        self.completion = 0
        self.returned_normally = self.runtime_handle_consumed = False
        self.current: RestoreInstallationResult
        self.refresh()

    def refresh(self) -> None:
        self.current = _INSTALLATION_RESULTS[self.status][self.call_entered][self.operation_entered][self.handle_consumed][
            self.bank_publication
        ][self.runtime_publication][self.completion][self.returned_normally][self.runtime_handle_consumed]


_installation_records: WeakKeyDictionary[RestoreInstallationOutcome, _InstallationCell] = WeakKeyDictionary()


class RestoreInstallationOutcome:
    """Producer-issued first-attempt observation, readable after consumption/poison.

    A refused, unconsumed handle can still be retried through the standalone API.
    Such a retry never rewrites this immutable first-attempt result.
    """

    __slots__ = ("_owner", "_handle", "_pid", "_thread", "__weakref__")
    _owner: Any
    _handle: Any
    _pid: int
    _thread: Any

    def __new__(cls) -> Any:
        raise TypeError("installation outcomes are producer-issued")

    def __copy__(self) -> Any:
        raise TypeError("installation outcomes cannot be copied")

    def __deepcopy__(self, memo: Any) -> Any:
        raise TypeError("installation outcomes cannot be copied")

    def __reduce__(self) -> Any:
        raise TypeError("installation outcomes cannot be serialized")

    def read(self) -> RestoreInstallationResult:
        if type(self) is not RestoreInstallationOutcome or self not in _installation_records:
            raise ValueError("unissued installation observation")
        cell = _installation_cell(self, self._owner)
        if self._thread is not current_thread():
            raise ValueError("foreign installation observation thread")
        return cell.current


def _new_installation_outcome(owner: Any, handle: Any, *, runtime: bool) -> RestoreInstallationOutcome:
    outcome = object.__new__(RestoreInstallationOutcome)
    outcome._owner, outcome._handle = owner, handle
    outcome._pid, outcome._thread = os.getpid(), current_thread()
    _installation_records[outcome] = _InstallationCell(owner, handle, runtime)
    return outcome


def _installation_cell(outcome: RestoreInstallationOutcome, owner: Any) -> _InstallationCell:
    if type(outcome) is not RestoreInstallationOutcome:
        raise ValueError("foreign installation observation")
    cell = _installation_records.get(outcome)
    if (
        cell is None
        or _PID != os.getpid()
        or outcome._pid != _PID
        or cell.owner() is not owner
        or outcome._owner is not owner
        or id(outcome._handle) != cell.handle_id
    ):
        raise ValueError("unissued or foreign installation observation")
    return cell


def _check_installation_lookup(owner: Any, *, busy: bool) -> None:
    if _PID != os.getpid() or busy:
        raise RuntimeError("installation observation unavailable during an incompatible call")
    scope = _local(owner)
    if scope is not None:
        record = _record(scope)
        if record.public is not None or record.permit is not None:
            raise RuntimeError("installation observation cannot reenter a public call")


def _validate_installation_outcome(outcome: RestoreInstallationOutcome, owner: Any) -> None:
    _installation_cell(outcome, owner)
    if outcome._thread is not current_thread():
        raise ValueError("foreign installation observation thread")


def _begin_installation(outcome: RestoreInstallationOutcome | None, owner: Any) -> _InstallationCell | None:
    if outcome is None:
        return None
    cell = _installation_cell(outcome, owner)
    if cell.status != 0:
        return None  # Preserve standalone retries without changing the first result.
    cell.status, cell.call_entered = 1, True
    cell.refresh()
    return cell


def _finish_installation(cell: _InstallationCell | None) -> None:
    if cell is not None:
        cell.status = 2
        cell.refresh()


def _incorporate_bank_result(cell: _InstallationCell, outcome: RestoreInstallationOutcome, bank: Any) -> None:
    result = _installation_cell(outcome, bank).current
    cell.operation_entered, cell.handle_consumed = result.operation_entered, result.handle_consumed
    cell.bank_publication = _INSTALLATION_FIELDS[4].index(result.bank_publication)
    cell.completion = _INSTALLATION_FIELDS[6].index(result.completion)
    cell.refresh()


@dataclass
class _Record:
    owner: Any
    thread: Any
    operation: RNGOperation | None
    retained: bool
    delegator: Any
    bank: Any
    call: object | None
    permit: Any
    public: object | None


class _Custody:
    __slots__ = ("__weakref__",)

    def __new__(cls) -> Any:
        raise TypeError("custody is producer-issued")

    def __copy__(self) -> Any:
        raise TypeError("custody cannot be copied")

    def __deepcopy__(self, memo: Any) -> Any:
        raise TypeError("custody cannot be copied")

    def __reduce__(self) -> Any:
        raise TypeError("custody cannot be serialized")


class BankParentCustody(_Custody):
    __slots__ = ()

    @contextmanager
    def bind_operation(self, *, operation: RNGOperation) -> Iterator[None]:
        if _record(self).delegator is not None:
            raise RuntimeError("delegated BANK binding belongs to runtime")
        with _binding(self, operation):
            yield


class RuntimeParentCustody(_Custody):
    __slots__ = ()

    @contextmanager
    def bind_operation(self, *, operation: RNGOperation) -> Iterator[None]:
        record = _record(self)
        with _binding(self, operation), _binding(record.bank, operation):
            yield


def _lookup(owner: Any) -> Any:
    issued = _scopes.get(owner)
    return None if issued is None else issued()


def _record(scope: Any) -> _Record:
    if _PID != os.getpid():
        raise RuntimeError("foreign process custody")
    record = _records.get(scope)
    if record is None or _lookup(record.owner) is not scope:
        raise RuntimeError("expired or unissued custody")
    if record.thread is not current_thread():
        raise RuntimeError("foreign custody thread")
    return record


def _issue(owner: Any, cls: Any, retained: bool, delegator: Any) -> Any:
    if _lookup(owner) is not None:
        raise RuntimeError("owner custody already retained")
    scope = object.__new__(cls)
    _records[scope] = _Record(owner, current_thread(), None, retained, delegator, None, None, None, None)
    _scopes[owner] = ref(scope)
    return scope


def _expire(scope: Any) -> None:
    record = _records.pop(scope)
    del _scopes[record.owner]
    record.owner = record.operation = record.delegator = record.bank = None
    record.call = record.permit = record.public = record.thread = None


def _local(owner: Any) -> Any:
    if _PID != os.getpid():
        raise RuntimeError("foreign process custody")
    scope = _lookup(owner)
    if scope is not None:
        record = _records.get(scope)
        if record is not None and record.thread is current_thread():
            _record(scope)
            return scope
    return None


def _lineage(owner: Any) -> RNGOperation | None:
    scope = _local(owner)
    if scope is None:
        return None
    record = _record(scope)
    if record.retained and record.operation is None:
        raise RuntimeError("retained custody requires explicit operation binding")
    return record.operation


@contextmanager
def _binding(scope: Any, operation: RNGOperation) -> Iterator[None]:
    record = _record(scope)
    if operation is None or record.operation is not None or record.call is not None or record.public is not None:
        raise RuntimeError("invalid or reentered operation binding")
    with process_rng_domain().admission(lineage=operation):
        record.operation = operation
        try:
            yield
        finally:
            record.operation = None


@contextmanager
def _bank_custody(bank: Any, runtime: Any, retained: bool) -> Iterator[BankParentCustody]:
    with bank._lock:
        if bank._entered:
            raise RuntimeError("BANK operation already active")
        scope = _issue(bank, BankParentCustody, retained, runtime)
        try:
            yield scope
        finally:
            _expire(scope)


@contextmanager
def _retain_bank(bank: Any) -> Iterator[BankParentCustody]:
    with process_rng_domain().admission(lineage=None), _bank_custody(bank, None, True) as scope:
        yield scope


@contextmanager
def _retain_runtime(runtime: Any) -> Iterator[RuntimeParentCustody]:
    with process_rng_domain().admission(lineage=None), runtime._lock:
        if runtime._operation_active:
            raise RuntimeError("runtime operation already active")
        scope = _issue(runtime, RuntimeParentCustody, True, None)
        try:
            with _bank_custody(runtime._bank, runtime, True) as bank:
                _record(scope).bank = bank
                yield scope
        finally:
            _expire(scope)


@contextmanager
def _delegated_call(scope: Any, runtime: Any) -> Iterator[None]:
    record = _record(scope)
    if record.delegator is not runtime or record.call is not None:
        raise RuntimeError("reentrant or foreign runtime forwarding")
    record.call = object()
    try:
        yield
    finally:
        record.call = record.permit = None


@contextmanager
def _runtime_call(runtime: Any, method: str) -> Iterator[None]:
    lineage = _lineage(runtime)
    if lineage is not None and method in _COHORT:
        raise RuntimeError("bound cohort preparation/publication is not enabled")
    with process_rng_domain().admission(lineage=lineage), runtime._lock:
        if runtime._operation_active:
            raise RuntimeError("reentrant runtime operation")
        scope = _local(runtime)
        if scope is not None:
            with _delegated_call(_record(scope).bank, runtime):
                yield
        else:
            with _bank_custody(runtime._bank, runtime, False) as bank, _delegated_call(bank, runtime):
                yield


def _forward_bank(runtime: Any, method: str, kwargs: dict[str, Any]) -> Any:
    scope = _local(runtime._bank)
    if scope is None:
        record = None
    else:
        record = _record(scope)
    if record is None or record.delegator is not runtime or record.call is None or record.permit is not None or record.public is not None:
        raise RuntimeError("BANK forwarding requires its current runtime call")
    record.permit = (runtime, record.call, method, record.operation)
    try:
        return getattr(runtime._bank, method)(**kwargs)
    finally:
        record.permit = None


@contextmanager
def _bank_call(bank: Any, method: str) -> Iterator[None]:
    scope = _local(bank)
    if scope is not None:
        record = _record(scope)
        if record.public is not None:
            raise RuntimeError("reentrant BANK public call")
        if record.delegator is not None:
            permit, record.permit = record.permit, None
            if permit is None or permit != (record.delegator, record.call, method, record.operation) or record.call is None:
                raise RuntimeError("direct BANK callback cannot borrow runtime forwarding")
    lineage = _lineage(bank)
    if lineage is not None and method in _COHORT:
        raise RuntimeError("bound BANK cohort preparation/publication is not enabled")
    with process_rng_domain().admission(lineage=lineage), bank._lock:
        temporary = scope is None
        if temporary:
            scope = _issue(bank, BankParentCustody, False, None)
        record = _record(scope)
        record.public = object()
        try:
            yield
        finally:
            record.public = None
            if temporary:
                _expire(scope)
