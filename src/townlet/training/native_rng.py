"""Owned outer Python and Torch RNG state for the native runner boundary.

Portable generator bytes are data, never current operation authority. Native
installation additionally requires the actual POP plan and C finalizer.
"""

from __future__ import annotations

import math
import os
import random
import threading
import weakref
from dataclasses import dataclass
from typing import Any

import torch

from townlet.exploration.rng_custody import RNGDeviceInvocation, process_rng_domain


def _validate_devices(cuda_devices: tuple[int, ...]) -> None:
    if (
        type(cuda_devices) is not tuple
        or any(type(index) is not int or index < 0 for index in cuda_devices)
        or tuple(sorted(set(cuda_devices))) != cuda_devices
    ):
        raise ValueError("Native RNG requires an explicit sorted unique CUDA inventory")


def _validate_state_tensor(value: Any) -> None:
    if type(value) is not torch.Tensor:
        raise ValueError("Native RNG state requires an ordinary contiguous CPU uint8 vector")
    # Exact Tensor type alone does not exclude per-instance method overrides.
    # Refuse attached behavior before invoking any tensor method, including the
    # ostensibly observational contiguity check used by the pure schema gate.
    attributes = object.__getattribute__(value, "__dict__")
    if type(attributes) is not dict or attributes:
        raise ValueError("Native RNG state cannot carry per-instance attributes or callbacks")
    if (
        value.device.type != "cpu"
        or value.dtype != torch.uint8
        or value.layout != torch.strided
        or value.ndim != 1
        or value.numel() == 0
        or not torch.Tensor.is_contiguous(value)
    ):
        raise ValueError("Native RNG state requires an ordinary contiguous CPU uint8 vector")


def _validate_python_state(value: Any) -> None:
    """Reject behavior-bearing objects before detached generator validation."""
    if type(value) is not tuple or len(value) != 3:
        raise ValueError("Native Python RNG state requires an exact three-item tuple")
    version, words, gaussian = value
    if type(version) is not int or version != 3:
        raise ValueError("Native Python RNG state requires version 3")
    if type(words) is not tuple or len(words) != 625:
        raise ValueError("Native Python RNG state requires 624 MT words and a cursor")
    if any(type(word) is not int or not 0 <= word < 2**32 for word in words[:-1]):
        raise ValueError("Native Python RNG words must be exact uint32 integers")
    if type(words[-1]) is not int or not 0 <= words[-1] <= 624:
        raise ValueError("Native Python RNG cursor must be an exact integer in [0, 624]")
    if gaussian is not None and (type(gaussian) is not float or not math.isfinite(gaussian)):
        raise ValueError("Native Python RNG Gaussian cache must be None or a finite float")


def validate_native_rng_payload(payload: Any, *, cuda_devices: tuple[int, ...]) -> None:
    """Check the portable schema without admission, CUDA or generator mutation.

    Actual generator state compatibility is checked by the receiving owner's
    ``validate_payload`` or ``prepare`` before any live child publication.
    """
    _validate_devices(cuda_devices)
    if type(payload) is not dict or set(payload) != {"schema", "python", "torch_cpu", "torch_cuda"}:
        raise ValueError("Native RNG payload requires the exact current fields")
    if type(payload["schema"]) is not str or payload["schema"] != "native-rng-v2":
        raise ValueError("Native RNG payload requires native-rng-v2")
    _validate_python_state(payload["python"])
    _validate_state_tensor(payload["torch_cpu"])
    states = payload["torch_cuda"]
    if type(states) is not dict or any(type(index) is not int for index in states) or set(states) != set(cuda_devices):
        raise ValueError("Native RNG CUDA state does not match the explicit receiving inventory")
    for state in states.values():
        _validate_state_tensor(state)


class PreparedNativeRNG:
    """Source-issued, nonportable owned data; no ambient installation authority."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> Any:
        raise TypeError("Native RNG data is issued by its actual receiving owner")

    def __copy__(self) -> Any:
        raise TypeError("Native RNG prepared data cannot be copied")

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        raise TypeError("Native RNG prepared data cannot be copied")

    def __reduce__(self) -> Any:
        raise TypeError("Native RNG prepared data is nonportable")


@dataclass
class _PreparedData:
    parent: Any
    parent_plan: Any
    payload: dict[str, Any]
    revision: int
    thread: threading.Thread
    pid: int
    consumed: bool


def _validate_parent(*, parent: Any, parent_plan: Any) -> None:
    # Import the actual implementation, never a caller-supplied validator.
    from townlet.population.vectorized import VectorizedPopulation, validate_native_population_data

    if not isinstance(parent, VectorizedPopulation):
        raise ValueError("Native RNG restoration requires the actual receiving population")
    validate_native_population_data(plan=parent_plan, owner=parent)


class NativeRNGState:
    """Own capture/staging and genuine final native RNG publication.

    Construct before BANK/runtime preparation. CUDA indices describe the actual
    selected execution profile, not every device available on the host.
    """

    def __init__(self, *, cuda_devices: tuple[int, ...]):
        _validate_devices(cuda_devices)
        self._pid = os.getpid()
        self._cuda_devices = cuda_devices
        self._revision = 0
        self._prepared: weakref.WeakKeyDictionary[PreparedNativeRNG, _PreparedData] = weakref.WeakKeyDictionary()
        domain = process_rng_domain()
        with domain.admission(lineage=None) as gate:
            for index in cuda_devices:
                if gate.resolve_cuda(torch.device("cuda", index)) != index:
                    raise ValueError("Native RNG CUDA resolution changed the explicit device")
            self._participant = domain.register(
                owner=self, cuda_devices=cuda_devices, entrypoints=frozenset({"capture", "prepare", "validate", "install"})
            )

    def _check_pid(self) -> None:
        if self._pid != os.getpid():
            raise RuntimeError("Native RNG owner cannot be inherited by another process")

    def _invocation(self, kind: str) -> RNGDeviceInvocation:
        self._check_pid()
        return process_rng_domain().device_invocation(
            participant=self._participant, operation_kind=kind, lineage=None, cuda_devices=self._cuda_devices
        )

    def capture(self) -> dict[str, Any]:
        """Return independent generator bytes without advancing any stream."""
        with self._invocation("capture"):
            payload = {
                "schema": "native-rng-v2",
                "python": random.getstate(),
                "torch_cpu": torch.get_rng_state().clone(),
                "torch_cuda": {index: torch.cuda.get_rng_state(index).clone() for index in self._cuda_devices},
            }
            validate_native_rng_payload(payload, cuda_devices=self._cuda_devices)
        return payload

    def _owned_payload(self, payload: Any) -> dict[str, Any]:
        validate_native_rng_payload(payload, cuda_devices=self._cuda_devices)
        owned: dict[str, Any] = {
            "schema": "native-rng-v2",
            # Strictly validated tuples contain only immutable built-in values.
            "python": payload["python"],
            "torch_cpu": torch.Tensor.clone(payload["torch_cpu"]),
            "torch_cuda": {index: torch.Tensor.clone(payload["torch_cuda"][index]) for index in self._cuda_devices},
        }
        try:
            random.Random(0).setstate(owned["python"])
            torch.Generator(device="cpu").set_state(owned["torch_cpu"])
            for index in self._cuda_devices:
                torch.Generator(device=torch.device("cuda", index)).set_state(owned["torch_cuda"][index])
        except (RuntimeError, TypeError, ValueError) as error:
            raise ValueError("Native RNG generator state is incompatible with the receiving profile") from error
        return owned

    def validate_payload(self, payload: Any) -> dict[str, Any]:
        """Validate detached generators and own all bytes without live mutation."""
        with self._invocation("validate"):
            owned = self._owned_payload(payload)
        return owned

    def prepare(self, payload: Any, *, parent: Any, parent_plan: Any) -> PreparedNativeRNG:
        """Stage data before the BANK cut, bound to a real receiving POP plan."""
        self._check_pid()
        _validate_parent(parent=parent, parent_plan=parent_plan)
        with self._invocation("prepare"):
            _validate_parent(parent=parent, parent_plan=parent_plan)
            owned = self._owned_payload(payload)
            prepared = object.__new__(PreparedNativeRNG)
            self._prepared[prepared] = _PreparedData(
                parent, parent_plan, owned, self._revision, threading.current_thread(), os.getpid(), False
            )
        return prepared

    def _record(self, prepared: PreparedNativeRNG, parent_plan: Any) -> _PreparedData:
        self._check_pid()
        if type(prepared) is not PreparedNativeRNG or prepared not in self._prepared:
            raise ValueError("Native RNG prepared data is foreign or expired")
        record = self._prepared[prepared]
        if record.pid != os.getpid() or record.thread is not threading.current_thread():
            raise ValueError("Native RNG prepared data belongs to another process or thread")
        if record.consumed or record.revision != self._revision or record.parent_plan is not parent_plan:
            raise ValueError("Native RNG prepared data is consumed, stale or associated with another parent plan")
        _validate_parent(parent=record.parent, parent_plan=parent_plan)
        return record

    def install(self, *, prepared: PreparedNativeRNG, parent_plan: Any, attempt: Any, restored: Any) -> None:
        """Publish last in the genuine fixed native finalizer, without rollback."""
        from townlet.environment.restore_attempt import validate_restore_finalizer

        record = self._record(prepared, parent_plan)
        validate_restore_finalizer(attempt=attempt, owner=record.parent, restored=restored)
        domain = process_rng_domain()
        with domain.admission(lineage=None):
            record = self._record(prepared, parent_plan)
            validate_restore_finalizer(attempt=attempt, owner=record.parent, restored=restored)
            with self._invocation("install") as operation:
                record = self._record(prepared, parent_plan)
                validate_restore_finalizer(attempt=attempt, owner=record.parent, restored=restored)
                record.consumed = True
                self._revision += 1
                try:
                    random.setstate(record.payload["python"])
                    torch.set_rng_state(record.payload["torch_cpu"])
                    for index in self._cuda_devices:
                        torch.cuda.set_rng_state(record.payload["torch_cuda"][index], index)
                    domain._commit_ambient(operation)
                except BaseException as error:
                    # A setter may have mutated before raising. Preserve the
                    # original cause and refuse all further admitted RNG work.
                    domain.poison(operation=operation, error=error)
                    raise
