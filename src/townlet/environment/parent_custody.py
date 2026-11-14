"""ENV exclusion and finite reverse calls; these confer no completion authority."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from threading import RLock, Thread, current_thread
from typing import Any, SupportsIndex

from townlet.exploration.rng_custody import RNGOperation, process_rng_domain


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
        )

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
