"""One source-owned BANK/world restore, with truthful failure and no rollback."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import current_thread
from typing import TYPE_CHECKING, Any, Never, SupportsIndex
from weakref import WeakKeyDictionary, ref

from townlet.config.world_roster import WorldRecord
from townlet.exploration.rng_custody import process_rng_domain

if TYPE_CHECKING:
    from townlet.environment.parent_custody import EnvParentCustody


@dataclass(slots=True)
class _Escrow:
    # Weak registry values must never retain their preparation key or attempt.
    status: str


@dataclass(frozen=True, slots=True)
class RuntimeRestoreContext:
    scope: EnvParentCustody
    prepared: WorldRecord
    operation: str


class _Attempt:
    def __init__(
        self, authority: Any, prepared: WorldRecord, child: Any, profile: str, compare: Callable[..., Any], finalize: Callable[..., Any]
    ) -> None:
        self.pid = os.getpid()
        self.thread: Any = current_thread()
        self.env, self.authority = authority._env, authority
        self.prepared: Any = prepared
        self.child, self.profile = child, profile
        self.compare: Any = compare
        self.finalize: Any = finalize
        self.pins = self.env._env_custody.binding()
        self.live, self.stage = True, "ACQUIRED"
        self.escrow = _Escrow("active")
        self.scope: EnvParentCustody | None = None
        self.parent_adapter: Callable[..., Any] | None = None
        self.child_prepared: Any = None
        self.observation: Any = None
        self.release: WorldRecord | None = None
        self.installed: WorldRecord | None = None
        self.preparation_entered = self.preparation_completed = False
        self.install_entered = self.world_entered = False
        self.overlay_permission: str | None = None
        self.overlay_active = False
        self.release_permit, self.world_permit, self.finalizer_permit = object(), object(), object()
        self.permit: object | None = None


_ATTEMPTS: WeakKeyDictionary[WorldRestoreAttempt, _Attempt] = WeakKeyDictionary()


def _record(attempt: Any) -> _Attempt:
    if type(attempt) is not WorldRestoreAttempt:
        raise ValueError("restore attempt is foreign or unissued")
    record = _ATTEMPTS.get(attempt)
    if (
        record is None
        or not record.live
        or record.pid != os.getpid()
        or record.thread is not current_thread()
        or record.env._world_restore_attempt is not attempt
    ):
        raise ValueError("restore attempt is expired, foreign or belongs to another thread/process")
    return record


def _bindings(record: _Attempt) -> None:
    actual = record.env._env_custody.binding()
    if len(actual) != len(record.pins) or any(a is not b for a, b in zip(actual, record.pins)):
        raise ValueError("restore attempt owner bindings changed")


def _result(record: _Attempt) -> Any:
    from townlet.exploration.parent_custody import RestoreInstallationOutcome, RestoreInstallationResult

    if type(record.observation) is not RestoreInstallationOutcome:
        raise ValueError("restore requires its genuine installation observation")
    result = record.observation.read()
    if type(result) is not RestoreInstallationResult:
        raise ValueError("restore installation result was not source-issued")
    return result


def _uncertain(record: _Attempt) -> bool:
    if record.world_entered:
        return True
    if not record.install_entered:
        return record.preparation_entered and not record.preparation_completed
    try:
        result = _result(record)
    except BaseException:
        return True
    return not (
        result.status == "sealed"
        and result.bank_publication == "none"
        and result.runtime_publication in ("none", "not_applicable")
        and result.completion in ("not_entered", "succeeded")
    )


def finish_restore_failure(*, env: Any, attempt: Any) -> None:
    """ENV's private failure entry; never enter another admission after poison."""
    record = _record(attempt)
    if record.env is not env:
        raise ValueError("restore failure belongs to another receiver")
    with env._env_custody.lock:
        if record.stage in ("COMPLETE", "FAILED_NO_PUBLICATION", "FAILED_PARTIAL_OR_UNCERTAIN"):
            return
        terminal = _uncertain(record)
        record.escrow.status = "failed"
        if terminal:
            env._world_restore_terminal = True
        if terminal:
            record.stage = "FAILED_PARTIAL_OR_UNCERTAIN"
        else:
            record.stage = "FAILED_NO_PUBLICATION"
        record.permit = record.overlay_permission = None


def consume_restore_route(*, env: Any, prepared: WorldRecord, route: str) -> None:
    """Ordinary ENV methods consume only a source-entered escrow permit."""
    if type(prepared) is not WorldRecord:
        raise ValueError("restore requires a genuine prepared world record")
    if prepared in env._world_restore_revoked:
        raise ValueError("prepared restore was revoked")
    escrow = env._world_restore_escrows.get(prepared)
    if escrow is None or escrow.status == "complete":
        return
    if escrow.status != "active":
        raise ValueError("prepared restore belongs to a failed attempt")
    record = _record(env._world_restore_attempt)
    if route == "release":
        expected = record.release_permit
        stage = "ISSUING_RELEASE"
    else:
        expected = record.world_permit
        stage = "INSTALLING_WORLD"
    if (
        route not in ("release", "world")
        or record.prepared is not prepared
        or record.escrow is not escrow
        or record.stage != stage
        or record.permit is not expected
    ):
        raise ValueError("escrowed restore requires its exact source-owned call")
    record.permit = None


@contextmanager
def runtime_restore_context(*, attempt: Any, runtime: Any) -> Iterator[RuntimeRestoreContext]:
    """Authenticate exactly one runtime overlay inside the genuine C stage."""
    record = _record(attempt)
    operation = record.overlay_permission
    scope = record.scope
    if (
        record.profile != "runtime"
        or record.child is not runtime
        or record.overlay_active
        or operation not in ("prepare", "install")
        or scope is None
        or record.stage != ("PREPARING" if operation == "prepare" else "INSTALLING_CHILD")
    ):
        raise ValueError("runtime correlation requires its genuine selected restore stage")
    _bindings(record)
    custody = scope._check()
    if scope._operation is not None or custody.active is not None or custody.reverse is not None:
        raise ValueError("runtime correlation requires actual idle unbound ENV exclusion")
    record.overlay_permission, record.overlay_active = None, True
    assert operation is not None
    try:
        yield RuntimeRestoreContext(scope, record.prepared, operation)
    except BaseException:
        record.env._finish_restore_attempt_failure(attempt)
        raise
    finally:
        record.overlay_active = False


def validate_restore_finalizer(*, attempt: Any, owner: Any, restored: object) -> None:
    """Borrow the actual fixed-finalizer call; this is no portable install token."""
    record = _record(attempt)
    if record.stage != "FINALIZING" or record.permit is not record.finalizer_permit:
        raise ValueError("native publication requires the actual fixed restore finalizer")
    _bindings(record)
    env = record.env
    pair = env._world_restored
    if (
        restored is not record.installed
        or env._world_release is not restored
        or pair is None
        or pair[0] is not record.prepared
        or pair[1] is not record.release
        or env._world_restore_terminal
        or (owner is not env and not any(owner is value for value in env._world_role_owners.values()))
    ):
        raise ValueError("native finalizer owner or installed world pair is no longer current")


class WorldRestoreAttempt:
    """Opaque, one-use execution authority issued by an ENV boundary owner."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> WorldRestoreAttempt:
        raise TypeError("restore attempts are issued by the bound ENV authority")

    def __copy__(self) -> Never:
        raise TypeError("restore attempts cannot be copied")

    def __deepcopy__(self, memo: dict[int, Any]) -> Never:
        raise TypeError("restore attempts cannot be copied")

    def __reduce_ex__(self, protocol: SupportsIndex) -> Never:
        raise TypeError("restore attempts cannot be serialized")

    @contextmanager
    def _stage(self, before: str, during: str, after: str) -> Iterator[_Attempt]:
        record = _record(self)
        try:
            if record.stage != before:
                raise ValueError("restore stage cannot be skipped, repeated or resumed after failure")
            _bindings(record)
            record.stage = during
            yield record
            if record.stage != during:
                raise ValueError("restore stage failed during its child call")
            record.stage = after
            if after == "COMPLETE":
                record.escrow.status = "complete"
        except BaseException:
            record.env._finish_restore_attempt_failure(self)
            raise

    @contextmanager
    def _retained(self, record: _Attempt, operation: str) -> Iterator[None]:
        with record.env.retain_parent_custody() as scope:
            record.scope = scope
            try:
                # Source authentication at a stage boundary is distinct from the
                # mandated public pure checks surrounding real child comparisons.
                scope._check()._validate_prepared_restore(record.prepared)
                if record.profile == "runtime":
                    record.overlay_permission = operation
                    with record.child.correlate_world_restore(attempt=self):
                        yield
                else:
                    yield
            finally:
                record.scope = None
                record.overlay_permission = None

    def _compare(self, *, prepared: Any, curiosity_state: Any) -> None:
        record = _record(self)
        scope = record.scope
        if record.stage not in ("PREPARING", "INSTALLING_CHILD") or scope is None or prepared is not record.prepared:
            raise ValueError("parent comparison requires this actual retained restore")
        scope.validate_prepared_restore(prepared=prepared)
        result = record.compare(prepared=prepared, curiosity_state=curiosity_state)
        if result is not None:
            raise ValueError("parent comparison must return None")
        scope.validate_prepared_restore(prepared=prepared)

    def _prepare(self, state: Any, mode: str | None, initialization: str | None) -> None:
        with self._stage("ACQUIRED", "PREPARING", "PREPARED") as record:
            if mode is None and initialization is None:
                raise ValueError("restore mode or private initialization must be explicit")
            with self._retained(record, "prepare"):
                record.preparation_entered = True
                if initialization is None:
                    handle = record.child.prepare_restore(
                        state=state,
                        mode=mode,
                        accepted=None,
                        parent_restore=record.prepared,
                        validate_parent_restore=record.parent_adapter,
                    )
                else:
                    handle = record.child.prepare_private_initialization(
                        state=state,
                        initialization=initialization,
                        parent_restore=record.prepared,
                        validate_parent_restore=record.parent_adapter,
                    )
                record.child_prepared = handle
                record.preparation_completed = True
                record.observation = record.child.restore_installation_outcome(prepared=handle)
                if _result(record).status != "pending":
                    raise ValueError("restore preparation supplied an already-attempted installation")

    def prepare_child(self, *, state: Any, mode: str) -> None:
        self._prepare(state, mode, None)

    def prepare_private_initialization(self, *, state: Any, initialization: str) -> None:
        self._prepare(state, None, initialization)

    def issue_release(self, *, boundary: Any) -> None:
        with self._stage("PREPARED", "ISSUING_RELEASE", "RELEASED") as record:
            record.permit = record.release_permit
            try:
                record.release = record.authority.restored(restore=record.prepared, boundary=boundary)
            finally:
                record.permit = None

    def install_child(self) -> None:
        with self._stage("RELEASED", "INSTALLING_CHILD", "CHILD_INSTALLED") as record:
            with self._retained(record, "install"):
                if _result(record).status != "pending":
                    raise ValueError("composed install cannot reuse an already-attempted handle")
                record.install_entered = True
                record.child.install_restore(prepared=record.child_prepared)
                result = _result(record)
                if record.profile == "runtime":
                    expected = "complete"
                else:
                    expected = "not_applicable"
                if (
                    result.status != "sealed"
                    or not result.returned_normally
                    or result.bank_publication != "complete"
                    or result.runtime_publication != expected
                    or result.completion != "succeeded"
                ):
                    raise ValueError("child installation did not earn a complete source outcome")

    def install_world(self) -> None:
        with self._stage("CHILD_INSTALLED", "INSTALLING_WORLD", "WORLD_INSTALLED") as record:
            record.world_entered, record.permit = True, record.world_permit
            try:
                record.installed = record.env.install_world_restore(prepared=record.prepared, release=record.release)
            finally:
                record.permit = None

    def finish(self) -> WorldRecord:
        with self._stage("WORLD_INSTALLED", "FINALIZING", "COMPLETE") as record:
            assert record.installed is not None
            record.permit = record.finalizer_permit
            try:
                result = record.finalize(restored=record.installed)
                if result is not None:
                    raise ValueError("restore finalizer must return None")
                validate_restore_finalizer(attempt=self, owner=record.env._world_role_owners["population"], restored=record.installed)
            finally:
                record.permit = None
            return record.installed

    def abort(self) -> None:
        record = _record(self)
        record.env._finish_restore_attempt_failure(self)


def _expire(record: _Attempt) -> None:
    # In particular break a value -> prepared runtime handle -> attempt cycle.
    record.live = False
    record.authority = record.env = record.prepared = record.child = None
    record.compare = record.finalize = record.parent_adapter = None
    record.child_prepared = record.observation = record.release = record.installed = None
    record.scope = record.thread = record.permit = record.overlay_permission = None
    record.pins = ()


@contextmanager
def restore_attempt(
    *,
    authority: Any,
    prepared: WorldRecord,
    child: Any,
    profile: str,
    validate_parent_restore: Callable[..., Any],
    finalize_component: Callable[..., Any],
) -> Iterator[WorldRestoreAttempt]:
    from townlet.config.exploration_policy import ExplorationRuntime
    from townlet.environment.vectorized_env import WorldBoundaryAuthority
    from townlet.exploration.scoped_curiosity import CuriosityBank

    if type(authority) is not WorldBoundaryAuthority or profile not in ("bank", "runtime"):
        raise ValueError("restore attempt requires an actual boundary authority and explicit child profile")
    if not callable(validate_parent_restore) or not callable(finalize_component):
        raise ValueError("restore attempt requires fixed real comparison and finalization callbacks")
    env = authority._env
    if env._world_restore_terminal:
        raise ValueError("receiver is terminal after failed restore composition")
    with process_rng_domain().admission(lineage=None):
        with env.retain_parent_custody() as scope:
            if env._world_authority is not authority or env._world_restore_attempt is not None:
                raise ValueError("restore authority is foreign or another attempt is active")
            scope._check()._validate_prepared_restore(prepared)
            curiosity = env._world_role_owners["curiosity"]
            if profile == "bank":
                if type(child) is not CuriosityBank or curiosity is not child or child._issuer.owner is not child:
                    raise ValueError("direct restore requires the actual receiving BANK owner")
            else:
                if type(child) is not ExplorationRuntime or env._world_role_owners["exploration"] is not child:
                    raise ValueError("runtime restore requires the actual receiving runtime owner")
                child.validate_restore_receiver(curiosity_owner=curiosity)
            attempt = object.__new__(WorldRestoreAttempt)
            record = _Attempt(authority, prepared, child, profile, validate_parent_restore, finalize_component)
            reference = ref(attempt)

            def compare(*, prepared: Any, curiosity_state: Any) -> None:
                actual = reference()
                if actual is None:
                    raise ValueError("restore attempt comparison has expired")
                actual._compare(prepared=prepared, curiosity_state=curiosity_state)

            record.parent_adapter = compare
            _ATTEMPTS[attempt] = record
            env._world_restore_escrows[prepared] = record.escrow
            env._world_restore_attempt = attempt
        try:
            yield attempt
        finally:
            try:
                env._finish_restore_attempt_failure(attempt)
            finally:
                with env._env_custody.lock:
                    if env._world_restore_attempt is attempt:
                        env._world_restore_attempt = None
                    _expire(record)
