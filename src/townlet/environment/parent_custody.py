"""ENV exclusion and finite reverse calls; these confer no completion authority."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from threading import RLock, Thread, current_thread
from typing import TYPE_CHECKING, Any, SupportsIndex
from weakref import WeakKeyDictionary

from townlet.config.world_roster import WorldRecord
from townlet.environment.manual_physical import ManualPhysicalSession
from townlet.exploration.rng_custody import RNGOperation, process_rng_domain

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


@dataclass(frozen=True, slots=True)
class _PreparedRestoreSeal:
    """Issuer metadata only; never retain the weak registry's record key."""

    payload: Any
    kind: str
    generation: int
    revision: int
    authority: Any
    boundary_owner: Any
    binding: tuple[Any, ...]
    roster: Any
    seed: int
    world_ids: tuple[str, ...]
    identity: str
    exploration_bound: bool
    manual: ManualPhysicalSession | None


def env_guard[**P, R](method: Callable[P, R]) -> Callable[P, R]:
    """Guard the complete public method, including boundary-authority work."""

    @wraps(method)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> R:
        self: Any
        if args:
            self = args[0]
        else:
            self = kwargs["self"]
        if method.__qualname__.startswith("WorldBoundaryAuthority."):
            env = self._env
        else:
            env = self
        with env._env_custody.call(method.__name__, kwargs):
            return method(*args, **kwargs)

    return guarded


class EnvParentCustody:
    """Issuer-retained execution binding, never transferable publication authority."""

    def __init__(self, custody: EnvCustody):
        self._pid = custody.pid
        self._thread: Thread | None = current_thread()
        self._custody: EnvCustody | None = custody
        self._pins = custody.binding()
        self._operation: RNGOperation | None = None

    def __copy__(self) -> Any:
        raise TypeError("ENV custody cannot be copied")

    def __deepcopy__(self, memo: Any) -> Any:
        raise TypeError("ENV custody cannot be copied")

    def __reduce_ex__(self, protocol: SupportsIndex) -> Any:
        raise TypeError("ENV custody cannot be serialized")

    def _check(self) -> EnvCustody:
        # Inherited/forged handles refuse before admission or any owner-lock wait.
        if os.getpid() != getattr(self, "_pid", None):
            raise ValueError("ENV custody belongs to another process or issuer")
        custody = self._custody
        if custody is None or self._thread is not current_thread() or custody.scope is not self:
            raise ValueError("ENV custody is expired, foreign or unissued")
        if any(left is not right for left, right in zip(self._pins, custody.binding(), strict=True)):
            raise ValueError("ENV retained bindings changed")
        return custody

    def validate_prepared_restore(self, *, prepared: WorldRecord) -> None:
        """Pure currentness under already-retained, unbound ENV exclusion."""
        custody = self._check()
        if self._operation is not None or custody.active is not None or custody.reverse is not None:
            raise ValueError("prepared restore validation requires idle unbound ENV custody")
        custody._validate_prepared_restore(prepared)

    @contextmanager
    def bind_operation(self, *, operation: RNGOperation) -> Iterator[None]:
        custody = self._check()
        if self._operation is not None or custody.active is not None:
            raise ValueError("ENV operation binding cannot reenter active work")
        if not isinstance(operation, RNGOperation):
            raise ValueError("ENV binding requires an authentic operation")
        with process_rng_domain().admission(lineage=operation):
            self._operation = operation
            try:
                yield
            finally:
                self._operation = None

    def _expire(self) -> None:
        self._custody = None
        self._thread = None
        self._pins = ()
        self._operation = None


class EnvCustody:
    """One ENV's domain-first exclusion and source-owned lexical outcall state."""

    def __init__(self, owner: Any):
        self.owner = owner
        self.pid = os.getpid()
        self.lock = RLock()
        self.active: tuple[object, Any] | None = None
        self.reverse: dict[str, Any] | None = None
        self.scope: EnvParentCustody | None = None
        self._restore_seals: WeakKeyDictionary[WorldRecord, _PreparedRestoreSeal] = WeakKeyDictionary()

    def check_process(self) -> None:
        if os.getpid() != self.pid:
            raise ValueError("ENV custody belongs to another process")

    def binding(self) -> tuple[Any, ...]:
        env = self.owner
        return (
            env._world_role_owners,
            *env._world_role_owners.values(),
            getattr(env, "_exploration_runtime", None),
            getattr(env, "_claim_vector_step", None),
            env._world_authority,
            getattr(env, "_manual_session", None),
        )

    def _seal_prepared_restore(self, record: WorldRecord) -> None:
        """Called only at ENV's genuine prepared-world issuance cut."""
        env: VectorizedHamletEnv = self.owner
        authority = env._world_authority
        if (
            self.active is None
            or self.active[1] is not current_thread()
            or type(record) is not WorldRecord
            or record._owner is not env
            or env._world_records.get(id(record)) is not record
            or authority is None
        ):
            raise ValueError("prepared world seal requires genuine ENV issuance")
        self._restore_seals[record] = _PreparedRestoreSeal(
            record._payload,
            record.kind,
            record._generation,
            env._world_revision,
            authority,
            authority._owner,
            self.binding(),
            env._world_roster,
            env._world_seed,
            env._world_ids,
            env._world_identity,
            env._exploration_bound,
            env._manual_session,
        )

    def _validate_prepared_restore(self, prepared: WorldRecord) -> None:
        # Scope/PID/thread authentication has already run. Authenticate exact
        # registry identity before reading record fields, never public payloads.
        env = self.owner
        if type(prepared) is not WorldRecord or env._world_records.get(id(prepared)) is not prepared:
            raise ValueError("prepared world restore is foreign, copied or unissued")
        seal = self._restore_seals.get(prepared)
        if (
            seal is None
            or prepared in env._world_restore_revoked
            or env._world_restore_terminal is not False
            or type(prepared.kind) is not str
            or prepared.kind != "prepared_restore"
            or prepared.kind != seal.kind
            or prepared._owner is not env
            or type(prepared._generation) is not int
            or prepared._generation != seal.generation
            or prepared._payload is not seal.payload
        ):
            raise ValueError("prepared world restore has no current issuer seal")
        authority = env._world_authority
        if (
            type(env._world_phase) is not str
            or env._world_phase != "fresh-bound"
            or type(env._world_generation) is not int
            or env._world_generation != 0
            or env._world_generation != seal.generation
            or type(env._world_revision) is not int
            or env._world_revision != 0
            or env._world_revision != seal.revision
            or authority is not seal.authority
            or authority._env is not env
            or authority._owner is not seal.boundary_owner
            or any(left is not right for left, right in zip(self.binding(), seal.binding, strict=True))
            or env._world_roster is not seal.roster
            or type(env._world_seed) is not int
            or env._world_seed != seal.seed
            or type(env._world_ids) is not tuple
            or any(type(value) is not str for value in env._world_ids)
            or env._world_ids != seal.world_ids
            or type(env._world_identity) is not str
            or env._world_identity != seal.identity
            or env._exploration_bound is not seal.exploration_bound
            or env._participation_busy is not False
            or env._participation_failed is not False
        ):
            raise ValueError("prepared world receiving identity is no longer fresh and current")
        if any(
            getattr(env, name) is not None
            for name in (
                "_world_accepted",
                "_world_reset",
                "_world_reservation",
                "_world_release",
                "_world_closure",
                "_world_frozen",
                "_world_consumers",
                "_world_restored",
                "_world_vfs_pending",
                "_world_last_closed",
                "_world_saved_binding",
                "_participation_pending",
                "_participation_committed",
                "_participation_reset_state",
                "_manual_close_prepared",
            )
        ):
            raise ValueError("prepared world receiver contains accepted or pending effects")
        cursors = env._world_cursors
        if (
            type(cursors) is not dict
            or len(cursors) != len(seal.world_ids)
            or any(
                type(key) is not str or key not in seal.world_ids or type(value) is not int or value != 0 for key, value in cursors.items()
            )
            or type(env._world_bindings) is not dict
            or env._world_bindings
            or type(env._world_equal) is not dict
            or env._world_equal
        ):
            raise ValueError("prepared world receiver contains accepted history")
        manual = env._manual_session
        if manual is not seal.manual:
            raise ValueError("prepared world manual binding changed")
        if manual is not None and (
            type(manual) is not ManualPhysicalSession
            or manual._env is not env
            or manual._owner is not env._world_role_owners["population"]
            or manual._binding is not env._world_role_owners
            or manual._authority is not authority
            or manual._pid != self.pid
            or manual._thread is not current_thread()
            or type(manual._tick) is not int
            or manual._tick != 0
            or manual._busy is not False
            or manual._failed is not False
            or manual._pending is not None
            or manual._accepted is not None
            or manual._state is not None
            or type(manual._stage) is not str
            or manual._stage != "idle"
            or manual._failure is not None
        ):
            raise ValueError("prepared world manual receiver is not genuinely quiescent")

    @contextmanager
    def retain(self) -> Iterator[EnvParentCustody]:
        self.check_process()
        thread = current_thread()
        if (self.active is not None and self.active[1] is thread) or (self.scope is not None and self.scope._thread is thread):
            raise ValueError("ENV retained custody cannot reenter")
        with process_rng_domain().admission(lineage=None), self.lock:
            if self.active is not None or self.scope is not None:
                raise ValueError("ENV custody is already retained")
            scope = EnvParentCustody(self)
            self.scope = scope
            try:
                yield scope
            finally:
                scope._expire()
                self.scope = None

    @contextmanager
    def call(self, name: str, arguments: dict[str, Any]) -> Iterator[None]:
        self.check_process()
        thread = current_thread()
        if self.active is not None and self.active[1] is thread:
            if name in ("world_phase", "accepted_episode_seqs"):
                # Phase and copied cursor diagnostics reuse the original call's
                # exclusion. Neither grants export, mutation or reverse-call rights.
                yield
                return
            with self._reverse_entry(name, arguments):
                yield
            return
        lineage = None
        scope = self.scope
        if scope is not None and scope._thread is thread:
            scope._check()
            lineage = scope._operation
            if lineage is None:
                raise ValueError("ENV retained custody requires explicit operation binding")
            # Binding mutation cannot replace owners pinned by this lexical scope.
            if name == "set_exploration_runtime" or (name == "bind_boundary_authority" and self.owner._world_authority is None):
                raise ValueError("ENV binding must precede retained custody")
        with process_rng_domain().admission(lineage=lineage), self.lock:
            if self.active is not None:
                raise ValueError("ENV method custody is already active")
            self.active = (object(), thread)
            try:
                yield
            finally:
                self.active = None

    def _current(self, record: dict[str, Any]) -> None:
        env = self.owner
        if (
            self.reverse is not record
            or self.active is not record["call"]
            or current_thread() is not record["thread"]
            or env._world_accepted is not record["accepted"]
            or env._world_generation != record["generation"]
            or env._world_revision != record["revision"]
            or env._participation_committed is not record["committed"]
            or self.scope is not record["scope"]
            or (self.scope is not None and self.scope._operation is not record["operation"])
            or any(left is not right for left, right in zip(self.binding(), record["binding"], strict=True))
        ):
            raise ValueError("ENV reverse-call identity is no longer current")

    @contextmanager
    def _reverse_entry(self, name: str, arguments: dict[str, Any]) -> Iterator[None]:
        record = self.reverse
        if record is None:
            raise ValueError("ENV public methods cannot reenter active work")
        state = record["state"]
        if name == "validate_initial_participation" and state == "CLAIM_READY" and record["committed"] is not None:
            # Consume before identity validation as well as before any tensor work.
            record["state"] = "VALIDATING"
            try:
                self._current(record)
                if arguments.get("accepted") is not record["accepted"] or arguments.get("participation") is not record["participation"]:
                    raise ValueError("ENV reverse validation requires the exact current decision")
                yield
            except BaseException as error:
                record["failure"] = error
                record["denied"] = True
                record["state"] = "CHECK_FAILED"
                raise
            else:
                record["state"] = "CHECKED"
            return
        if name == "abandon_episode" and state in ("CLAIM_READY", "CHECKED", "CHECK_FAILED", "EMPTY_READY"):
            self._current(record)
            if (
                arguments.get("accepted") is not record["accepted"]
                or type(arguments.get("reason")) is not str
                or arguments["reason"] != "runtime_failure"
            ):
                raise ValueError("ENV reverse cleanup requires exact current runtime failure")
            record["denied"], record["state"] = True, "CLEANING"
            try:
                yield
            finally:
                record["state"] = "DENIED"
            return
        raise ValueError("ENV callback has no permission for this public entry")

    def outcall(self, edge: str, callback: Callable[..., Any], *, owner: Any, **arguments: Any) -> Any:
        """Issue one private continuation immediately around an actual producer call."""
        self.check_process()
        if self.active is None or self.active[1] is not current_thread() or self.reverse is not None:
            raise ValueError("ENV outcall requires its original method custody")
        env = self.owner
        committed = env._participation_committed
        record = {
            "call": self.active,
            "thread": current_thread(),
            "callback": callback,
            "owner": owner,
            "binding": self.binding(),
            "scope": self.scope,
            "operation": None if self.scope is None else self.scope._operation,
            "accepted": env._world_accepted,
            "generation": env._world_generation,
            "revision": env._world_revision,
            "committed": committed,
            "participation": None if committed is None else committed["result"],
            "reading": None if committed is None else committed["observation"],
            "prepared": arguments.get("prepared"),
            "state": "CLAIM_READY" if edge == "claim" else "EMPTY_READY",
            "denied": False,
            "failure": None,
        }
        self.reverse = record
        try:
            result = callback(**arguments)
            # No permission survives into result/receipt validation or ENV helpers.
            self.reverse = None
            if record["failure"] is not None:
                raise record["failure"]
            if record["denied"] or (edge == "claim" and committed is not None and record["state"] != "CHECKED"):
                raise ValueError("ENV continuation refused after producer callback")
            return result
        finally:
            self.reverse = None
            record.clear()
