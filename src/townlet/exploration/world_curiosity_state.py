"""Exact-WorldId seeds and serialized private RNG/backend ownership primitives.

Private seed inputs deliberately exclude lane order, population, model parameters
and all clocks. World routing and shared-policy quiescence belong to the bank.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import threading
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Literal, cast

import numpy as np
import torch

from townlet.config.exploration_policy import STRATEGIES, ResolvedExplorationPolicy, Strategy

WORLD_SEED_COMPONENTS = ("model_init", "target", "predictor", "service")


def _hash(record: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _integer(value: Any, name: str, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: expected integer >= {minimum}")


def _nonempty(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name}: expected exact nonempty string")


def derive_world_seed(*, training_seed: int, world_id: str, provider_kind: str, component: str) -> int:
    """Versioned canonical KDF over only the four declared ownership inputs."""
    _integer(training_seed, "training_seed", 0)
    _nonempty(world_id, "world_id")
    _nonempty(component, "component")
    if provider_kind not in STRATEGIES:
        raise ValueError("provider_kind: unsupported curiosity provider")
    digest = _hash(
        {
            "schema": "world-curiosity-seed-v1",
            "training_seed": training_seed,
            "world_id": world_id,
            "provider_kind": provider_kind,
            "component": component,
        }
    )
    return int(digest[:16], 16) & (2**63 - 1)


@dataclass(frozen=True)
class WorldCuriosityDescriptor:
    """Immutable declared geometry, ID binding and canonical ID-keyed streams.

    Equal descriptors never own shared mutable storage. Shared mode records its
    legacy stream ownership; it does not pretend to derive private world seeds.
    """

    schema_version: Literal[1]
    scope: Literal["shared", "per_world"]
    provider_kind: Strategy
    provider_parameter_hash: str
    observation_dim: int
    action_dim: int
    world_ids: tuple[str, ...]
    seed_policy: Literal["legacy_shared_v1", "world_id_derived_v1"]
    service_clock_unit: Literal["vector_tick", "world_eligible_admission"]
    origin: Literal["authored", "bac-options-v1"]
    guarantee: Literal["shared_population_state", "world_id_owned_state"]
    training_seed: int
    seeds: Mapping[str, Mapping[str, int]]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported world curiosity descriptor schema")
        if self.scope not in ("shared", "per_world") or self.provider_kind not in STRATEGIES:
            raise ValueError("invalid world curiosity scope/provider")
        expected = ("legacy_shared_v1", "vector_tick", "shared_population_state")
        if self.scope == "per_world":
            expected = ("world_id_derived_v1", "world_eligible_admission", "world_id_owned_state")
        if (self.seed_policy, self.service_clock_unit, self.guarantee) != expected:
            raise ValueError("world curiosity descriptor ownership/seed/clock guarantee disagrees")
        if self.origin not in ("authored", "bac-options-v1"):
            raise ValueError("invalid world curiosity origin")
        if self.scope == "per_world" and self.origin != "authored":
            raise ValueError("private curiosity requires an explicit declaration")
        if (
            not isinstance(self.provider_parameter_hash, str)
            or len(self.provider_parameter_hash) != 64
            or any(char not in "0123456789abcdef" for char in self.provider_parameter_hash)
        ):
            raise ValueError("provider_parameter_hash must be a canonical SHA256")
        _integer(self.observation_dim, "observation_dim", 0)
        _integer(self.action_dim, "action_dim", 1)
        _integer(self.training_seed, "training_seed", 0)
        if not isinstance(self.world_ids, (tuple, list)) or any(not isinstance(item, str) for item in self.world_ids):
            raise ValueError("world_ids must contain exact strings")
        world_ids = tuple(self.world_ids)
        if self.scope == "per_world":
            if not world_ids or any(not item for item in world_ids):
                raise ValueError("strict world IDs must be nonempty")
            if len(set(world_ids)) != len(world_ids):
                raise ValueError("duplicate strict world IDs")
        object.__setattr__(self, "world_ids", world_ids)
        if not isinstance(self.seeds, Mapping):
            raise ValueError("seeds must be an ID-keyed mapping")
        if self.scope == "per_world":
            required = set(world_ids)
        else:
            required = set()
        if set(self.seeds) != required:
            raise ValueError("seeds must match the exact private world IDs")
        owned: dict[str, Mapping[str, int]] = {}
        for world_id in sorted(required):
            streams = self.seeds[world_id]
            if not isinstance(streams, Mapping) or set(streams) != set(WORLD_SEED_COMPONENTS):
                raise ValueError("seeds must persist every named private stream")
            for component, seed in streams.items():
                _integer(seed, f"seeds.{world_id}.{component}", 0)
                if seed != derive_world_seed(
                    training_seed=self.training_seed, world_id=world_id, provider_kind=self.provider_kind, component=component
                ):
                    raise ValueError("persisted world seed disagrees with versioned derivation")
            owned[world_id] = MappingProxyType(dict(streams))
        object.__setattr__(self, "seeds", MappingProxyType(owned))

    @property
    def canonical_world_ids(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.world_ids)))

    @property
    def world_binding_hash(self) -> str:
        """Runtime row binding, kept separate from compiled policy identity."""
        return _hash({"schema": "world-curiosity-binding-v1", "world_ids": list(self.world_ids)})

    def seed_for(self, world_id: str, component: str) -> int:
        if self.scope != "per_world":
            raise ValueError("shared curiosity retains its legacy shared RNG ownership")
        if world_id not in self.seeds or component not in self.seeds[world_id]:
            raise ValueError("unknown exact world ID or private seed component")
        return self.seeds[world_id][component]

    @classmethod
    def from_policy(
        cls,
        policy: ResolvedExplorationPolicy,
        *,
        world_ids: tuple[str, ...],
        observation_dim: int,
        action_dim: int,
        training_seed: int,
    ) -> WorldCuriosityDescriptor:
        seeds = {}
        if policy.curiosity_scope == "per_world":
            # Validate before constructing a map so duplicate IDs cannot vanish.
            if not isinstance(world_ids, (tuple, list)):
                raise ValueError("strict world IDs require an ordered sequence")
            for world_id in world_ids:
                _nonempty(world_id, "world_id")
            if len(set(world_ids)) != len(world_ids):
                raise ValueError("duplicate strict world IDs")
            seeds = {
                world_id: {
                    component: derive_world_seed(
                        training_seed=training_seed, world_id=world_id, provider_kind=policy.strategy, component=component
                    )
                    for component in WORLD_SEED_COMPONENTS
                }
                for world_id in world_ids
            }
        return cls(
            schema_version=1,
            scope=policy.curiosity_scope,
            provider_kind=policy.strategy,
            provider_parameter_hash=_hash(dict(policy.provider_parameters)),
            observation_dim=observation_dim,
            action_dim=action_dim,
            world_ids=world_ids,
            seed_policy=policy.seed_policy,
            service_clock_unit=policy.service_clock_unit,
            origin=policy.scope_origin,
            guarantee=policy.scope_guarantee,
            training_seed=training_seed,
            seeds=seeds,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope,
            "provider_kind": self.provider_kind,
            "provider_parameter_hash": self.provider_parameter_hash,
            "observation_dim": self.observation_dim,
            "action_dim": self.action_dim,
            "world_ids": list(self.world_ids),
            "canonical_world_ids": list(self.canonical_world_ids),
            "world_binding_hash": self.world_binding_hash,
            "seed_policy": self.seed_policy,
            "service_clock_unit": self.service_clock_unit,
            "origin": self.origin,
            "guarantee": self.guarantee,
            "training_seed": self.training_seed,
            "seeds": {world_id: dict(streams) for world_id, streams in self.seeds.items()},
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WorldCuriosityDescriptor:
        required = set(
            "schema_version scope provider_kind provider_parameter_hash observation_dim action_dim world_ids canonical_world_ids "
            "world_binding_hash seed_policy service_clock_unit origin guarantee training_seed seeds".split()
        )
        if set(payload) != required:
            raise ValueError("world curiosity descriptor requires a complete versioned field set")
        values = dict(payload)
        binding = values.pop("world_binding_hash")
        canonical = values.pop("canonical_world_ids")
        result = cls(**values)
        if canonical != list(result.canonical_world_ids) or binding != result.world_binding_hash:
            raise ValueError("world curiosity descriptor ID binding disagrees")
        return result


# A runtime owner must also exclude unrelated shared RNG users. This lock only
# coordinates participating lifecycle operations, not arbitrary process code.
_rng_guard = threading.RLock()
_rng_local = threading.local()
_rng_unusable: BaseException | None = None


def _owned(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            return deepcopy(value)
        return value.copy()
    if isinstance(value, Mapping):
        return {_owned(key): _owned(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_owned(item) for item in value]
    if isinstance(value, tuple):
        if hasattr(value, "_fields"):
            return type(value)(*(_owned(item) for item in value))
        return tuple(_owned(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        result = copy(value)
        for field in fields(value):
            object.__setattr__(result, field.name, _owned(getattr(value, field.name)))
        return result
    return deepcopy(value)


def _same(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, torch.Tensor):
        return left.dtype == right.dtype and left.device == right.device and left.shape == right.shape and torch.equal(left, right)
    if isinstance(left, np.ndarray):
        return left.dtype == right.dtype and left.shape == right.shape and bool(np.array_equal(left, right))
    if isinstance(left, Mapping):
        return left.keys() == right.keys() and all(_same(left[key], right[key]) for key in left)
    if isinstance(left, (tuple, list)):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right, strict=True))
    return bool(left == right)


def _stack() -> list[_Activation]:
    if not hasattr(_rng_local, "stack"):
        _rng_local.stack = []
    return cast(list[_Activation], _rng_local.stack)


def _usable() -> None:
    if _rng_unusable is not None:
        raise RuntimeError("Private RNG coordinator is unusable after restoration failure") from _rng_unusable


def _quiescent() -> None:
    _usable()
    if _stack():
        raise RuntimeError("Owned lifecycle operation requires a quiescent RNG domain")


def _keys(value: Any, required: set[str], name: str) -> None:
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError(f"{name} requires its exact versioned fields")


def _identity(descriptor: WorldCuriosityDescriptor) -> dict[str, Any]:
    return {
        name: getattr(descriptor, name)
        for name in ("scope", "provider_kind", "provider_parameter_hash", "observation_dim", "action_dim", "seed_policy", "training_seed")
    }


def _domain_arguments(descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> None:
    if not isinstance(descriptor, WorldCuriosityDescriptor) or descriptor.scope != "per_world":
        raise ValueError("Private RNG requires an explicitly private descriptor")
    _nonempty(world_id, "world_id")
    if world_id not in descriptor.world_ids:
        raise ValueError("Private RNG requires an exact descriptor world ID")
    if not isinstance(cuda_devices, tuple) or any(type(index) is not int or index < 0 for index in cuda_devices):
        raise ValueError("cuda_devices must be a tuple of nonnegative device indices")
    if tuple(sorted(set(cuda_devices))) != cuda_devices:
        raise ValueError("cuda_devices must be unique and canonically ordered")
    if cuda_devices:
        # Explicit quiescent CUDA setup belongs to the runtime. CPU owners never
        # query or initialize CUDA; uninitialized device domains fail closed.
        if not torch.cuda.is_initialized():
            raise ValueError("Initialize used CUDA devices at the quiescent runtime setup boundary first")
        if any(index >= torch.cuda.device_count() for index in cuda_devices):
            raise ValueError("Private RNG references an unavailable CUDA device")


def _synchronize(devices: tuple[int, ...]) -> None:
    for index in devices:
        torch.cuda.synchronize(index)


def _globals(devices: tuple[int, ...]) -> dict[str, Any]:
    _synchronize(devices)
    return {
        "torch_cpu": torch.get_rng_state().clone(),
        "cuda": {index: torch.cuda.get_rng_state(index).clone() for index in devices},
        "python": deepcopy(random.getstate()),
        "numpy_legacy": _owned(np.random.get_state()),
    }


def _install_globals(state: dict[str, Any]) -> None:
    torch.set_rng_state(state["torch_cpu"])
    random.setstate(state["python"])
    np.random.set_state(state["numpy_legacy"])
    for index, value in state["cuda"].items():
        torch.cuda.set_rng_state(value, index)


def _restore_globals(state: dict[str, Any]) -> list[BaseException]:
    failures: list[BaseException] = []
    operations: list[tuple[Callable[..., Any], tuple[Any, ...]]] = [
        (torch.set_rng_state, (state["torch_cpu"],)),
        (random.setstate, (state["python"],)),
        (np.random.set_state, (state["numpy_legacy"],)),
        *((torch.cuda.set_rng_state, (value, index)) for index, value in state["cuda"].items()),
    ]
    for setter, arguments in operations:
        try:
            setter(*arguments)
        except BaseException as error:
            failures.append(error)
    return failures


def _raise_failures(failures: list[BaseException]) -> None:
    if len(failures) == 1:
        raise failures[0]
    if failures:
        raise BaseExceptionGroup("Private RNG operation and cleanup failed", failures)


class PythonRandomSource:
    """Activation-bound facade over the installed module-global Python stream."""

    def __init__(self, frame: Any):
        self._frame = frame

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_") or not callable(getattr(random.Random, name, None)):
            raise AttributeError(name)

        def invoke(*args: Any, **kwargs: Any) -> Any:
            if not _stack() or _stack()[-1] is not self._frame:
                raise RuntimeError("Python random source is outside its active RNG component")
            return getattr(random, name)(*args, **kwargs)

        return invoke


@dataclass(frozen=True)
class WorldRandomSources:
    python: PythonRandomSource
    numpy: np.random.Generator


class _Activation:
    def __init__(self, owner: WorldRNGState, component: str, generator: np.random.Generator, ambient: dict[str, Any]):
        self.owner, self.component = owner, component
        self.sources = WorldRandomSources(PythonRandomSource(self), generator)
        self.ambient = ambient


class WorldRNGState:
    """Owned named streams; scoped ambient swapping restores all captured globals.

    Schema v1 uses each primary seed for CPU Torch, plus KDF component suffixes
    /python, /numpy-pcg64, /numpy-legacy (modulo 2**32), and /cuda/<index>.
    Mutable identity is instance-owned; spectator roster/order is not identity.
    """

    def __init__(self, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...], components: dict[str, Any]):
        self._descriptor, self._world_id, self._cuda_devices = descriptor, world_id, cuda_devices
        self._components = _owned(components)
        self._broken = False

    @classmethod
    def create(cls, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> WorldRNGState:
        with _rng_guard:
            _quiescent()
            _domain_arguments(descriptor, world_id, cuda_devices)
            components = {}
            for component in WORLD_SEED_COMPONENTS:

                def seed(suffix: str) -> int:
                    return derive_world_seed(
                        training_seed=descriptor.training_seed,
                        world_id=world_id,
                        provider_kind=descriptor.provider_kind,
                        component=f"{component}/{suffix}",
                    )

                primary = descriptor.seed_for(world_id, component)
                components[component] = {
                    "seed": primary,
                    "torch_cpu": torch.Generator(device="cpu").manual_seed(primary).get_state(),
                    "cuda": {
                        index: torch.Generator(device=f"cuda:{index}").manual_seed(seed(f"cuda/{index}")).get_state()
                        for index in cuda_devices
                    },
                    "python": random.Random(seed("python")).getstate(),
                    "numpy_pcg64": np.random.PCG64(seed("numpy-pcg64")).state,
                    "numpy_legacy": np.random.RandomState(seed("numpy-legacy") % 2**32).get_state(),
                }
            return cls(descriptor, world_id, cuda_devices, components)

    @staticmethod
    def _torch_state(value: Any, device: str) -> None:
        if not isinstance(value, torch.Tensor) or value.dtype != torch.uint8 or value.device.type != "cpu" or value.ndim != 1:
            raise ValueError("Torch RNG state must be a CPU byte vector")
        generator = torch.Generator(device=device)
        generator.set_state(value.clone())
        if not _same(value, generator.get_state()):
            raise ValueError("Torch RNG state is not canonical for this device")

    @classmethod
    def from_snapshot(
        cls, payload: Any, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]
    ) -> WorldRNGState:
        with _rng_guard:
            _quiescent()
            _domain_arguments(descriptor, world_id, cuda_devices)
            state = _owned(payload)
            _keys(state, {"schema", "descriptor", "world_id", "cuda_devices", "components"}, "RNG snapshot")
            if (
                type(state["schema"]) is not str
                or state["schema"] != "world-curiosity-rng-v1"
                or not _same(state["descriptor"], _identity(descriptor))
            ):
                raise ValueError("RNG snapshot schema/descriptor identity disagrees")
            if state["world_id"] != world_id or not _same(state["cuda_devices"], cuda_devices):
                raise ValueError("RNG snapshot world/device inventory disagrees")
            _keys(state["components"], set(WORLD_SEED_COMPONENTS), "RNG components")
            try:
                for component, entry in state["components"].items():
                    _keys(entry, {"seed", "torch_cpu", "cuda", "python", "numpy_pcg64", "numpy_legacy"}, "RNG component")
                    if type(entry["seed"]) is not int or entry["seed"] != descriptor.seed_for(world_id, component):
                        raise ValueError("RNG component seed disagrees with the versioned KDF")
                    cls._torch_state(entry["torch_cpu"], "cpu")
                    cuda = entry["cuda"]
                    if not isinstance(cuda, dict) or any(type(index) is not int for index in cuda) or set(cuda) != set(cuda_devices):
                        raise ValueError("RNG component CUDA inventory disagrees")
                    for index, value in cuda.items():
                        cls._torch_state(value, f"cuda:{index}")
                    python = random.Random(0)
                    python.setstate(entry["python"])
                    if not _same(entry["python"], python.getstate()):
                        raise ValueError("Python RNG snapshot must use canonical current state")
                    gaussian = entry["python"][2]
                    if gaussian is not None and (type(gaussian) is not float or not math.isfinite(gaussian)):
                        raise ValueError("Python RNG Gaussian cache must be finite")
                    pcg = entry["numpy_pcg64"]
                    _keys(pcg, {"bit_generator", "state", "has_uint32", "uinteger"}, "PCG64 state")
                    _keys(pcg["state"], {"state", "inc"}, "PCG64 internal state")
                    if pcg["bit_generator"] != "PCG64":
                        raise ValueError("Private NumPy generator must be PCG64")
                    for key, maximum in (("has_uint32", 1), ("uinteger", 2**32 - 1)):
                        if type(pcg[key]) is not int or not 0 <= pcg[key] <= maximum:
                            raise ValueError("PCG64 cache is malformed")
                    for value in pcg["state"].values():
                        if type(value) is not int or not 0 <= value < 2**128:
                            raise ValueError("PCG64 state must contain unsigned 128-bit integers")
                    if pcg["state"]["inc"] % 2 != 1:
                        raise ValueError("PCG64 increment must be odd")
                    generator = np.random.PCG64(0)
                    generator.state = pcg
                    legacy = np.random.RandomState(0)
                    legacy.set_state(entry["numpy_legacy"])
                    if not _same(entry["numpy_legacy"], legacy.get_state()) or not math.isfinite(legacy.get_state()[4]):
                        raise ValueError("Legacy NumPy RNG state must be canonical and finite")
            except (TypeError, KeyError, IndexError, RuntimeError, OverflowError) as error:
                raise ValueError("Malformed private RNG continuation state") from error
            return cls(descriptor, world_id, cuda_devices, state["components"])

    def snapshot(self) -> dict[str, Any]:
        with _rng_guard:
            _quiescent()
            if self._broken:
                raise RuntimeError("Private RNG state failed to capture and cannot resume")
            return cast(
                dict[str, Any],
                _owned(
                    {
                        "schema": "world-curiosity-rng-v1",
                        "descriptor": _identity(self._descriptor),
                        "world_id": self._world_id,
                        "cuda_devices": self._cuda_devices,
                        "components": self._components,
                    }
                ),
            )

    @contextmanager
    def activate(self, component: str) -> Iterator[WorldRandomSources]:
        global _rng_unusable
        with _rng_guard:
            _usable()
            if self._broken:
                raise RuntimeError("Private RNG state is unusable after failed capture")
            if type(component) is not str or component not in self._components:
                raise ValueError("Unknown named private RNG component")
            stack = _stack()
            if stack and stack[-1].owner is not self:
                raise RuntimeError("Cross-owner nested RNG activation is forbidden")
            if stack and stack[-1].component == component:
                yield stack[-1].sources
                return
            entry = self._components[component]
            frame = next((active for active in reversed(stack) if active.component == component), None)
            if frame is None:
                generator = np.random.Generator(np.random.PCG64(0))
                generator.bit_generator.state = deepcopy(entry["numpy_pcg64"])
                frame = _Activation(self, component, generator, _owned(entry))
            try:
                saved = _globals(self._cuda_devices)
            except BaseException:
                self._broken = True
                raise
            if stack:
                stack[-1].ambient = saved
            failures: list[BaseException] = []
            entered = False
            try:
                _install_globals(frame.ambient)
                stack.append(frame)
                entered = True
                yield frame.sources
            except BaseException as error:
                failures.append(error)
            finally:
                if entered:
                    try:
                        advanced = _globals(self._cuda_devices)
                        advanced["seed"] = entry["seed"]
                        advanced["numpy_pcg64"] = deepcopy(frame.sources.numpy.bit_generator.state)
                        self._components[component] = advanced
                        frame.ambient = advanced
                    except BaseException as error:
                        self._broken = True
                        failures.append(error)
                    finally:
                        stack.pop()
                # A -> B -> A nesting resumes the advanced suspended A frame,
                # not the older ambient copy originally saved by B.
                restoration = _restore_globals(stack[-1].ambient if stack else saved)
                if restoration:
                    self._broken = True
                    _rng_unusable = BaseExceptionGroup("Private RNG global restoration failed", restoration)
                    failures.extend(restoration)
            _raise_failures(failures)


class PreparedWorldBackend:
    """Opaque destination-bound single-use transfer; provider work precedes install."""

    def __init__(self, destination: object, revision: int, backend: Any, rng: WorldRNGState):
        self._destination, self._revision = destination, revision
        self._backend = backend
        self._rng: WorldRNGState | None = rng
        self._used = False


class OwnedWorldBackend:
    """Serialized private lifecycle; failed live callbacks quarantine, never retry.

    Provider owners must supply complete pure validation. PW02 owns the envelope,
    copies and off-side installation, not backend-specific semantic qualification.
    """

    def __init__(self, backend: Any, rng: WorldRNGState):
        self._backend, self._rng = backend, rng
        self._token = object()
        self._revision = 0
        self._failed = False

    @staticmethod
    def _backend_contract(backend: Any) -> None:
        if not callable(getattr(backend, "checkpoint_state", None)) or not callable(getattr(backend, "load_state", None)):
            raise ValueError("Owned backend requires checkpoint_state and load_state")

    @staticmethod
    def _clone_backend(backend: Any) -> Any:
        # Resolved policies contain MappingProxyType values. Reconstruct through
        # their validated portable ABI rather than sharing or pickling proxies.
        memo: dict[int, Any] = {}
        policy = getattr(backend, "policy", None)
        if isinstance(policy, ResolvedExplorationPolicy):
            memo[id(policy)] = type(policy).from_dict(deepcopy(policy.to_dict()))
        return deepcopy(backend, memo)

    @classmethod
    def construct(cls, *, rng: WorldRNGState, factory: Callable[[WorldRNGState], Any]) -> OwnedWorldBackend:
        with _rng_guard:
            _quiescent()
            if not isinstance(rng, WorldRNGState) or not callable(factory):
                raise ValueError("Owned construction requires an RNG owner and factory")
            candidate_rng = WorldRNGState.from_snapshot(
                rng.snapshot(),
                descriptor=rng._descriptor,
                world_id=rng._world_id,
                cuda_devices=rng._cuda_devices,
            )
            with candidate_rng.activate("model_init"):
                backend = cls._clone_backend(factory(candidate_rng))
                cls._backend_contract(backend)
            return cls(backend, candidate_rng)

    def call(self, operation: Callable[[Any, WorldRandomSources], Any]) -> Any:
        with _rng_guard:
            _quiescent()
            if self._failed:
                raise RuntimeError("Owned backend is quarantined after a failed callback; prepare an explicit restore")
            if not callable(operation):
                raise ValueError("Owned operation must be callable")
            try:
                with self._rng.activate("service") as sources:
                    return _owned(operation(self._backend, sources))
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def snapshot(self) -> dict[str, Any]:
        with _rng_guard:
            _quiescent()
            try:
                with self._rng.activate("service"):
                    backend_state = _owned(self._backend.checkpoint_state())
                return {
                    "schema": "owned-world-backend-v1",
                    "healthy": not self._failed,
                    "backend": backend_state,
                    "rng": self._rng.snapshot(),
                }
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def prepare_restore(
        self, payload: Any, *, factory: Callable[[WorldRNGState], Any], validate_backend: Callable[[Any, Any], object]
    ) -> PreparedWorldBackend:
        with _rng_guard:
            _quiescent()
            if not callable(factory) or not callable(validate_backend):
                raise ValueError("Prepared restore requires factory and pure backend validation")
            state = _owned(payload)
            _keys(state, {"schema", "healthy", "backend", "rng"}, "Owned backend snapshot")
            if state["schema"] != "owned-world-backend-v1" or state["healthy"] is not True:
                raise ValueError("Only a healthy owned backend snapshot can be restored")
            saved_rng = WorldRNGState.from_snapshot(
                state["rng"],
                descriptor=self._rng._descriptor,
                world_id=self._rng._world_id,
                cuda_devices=self._rng._cuda_devices,
            )
            work_rng = WorldRNGState.from_snapshot(
                state["rng"],
                descriptor=self._rng._descriptor,
                world_id=self._rng._world_id,
                cuda_devices=self._rng._cuda_devices,
            )
            with work_rng.activate("model_init"):
                candidate = self._clone_backend(factory(work_rng))
                self._backend_contract(candidate)
            with work_rng.activate("service"):
                before = _owned(candidate.checkpoint_state())
                transported = _owned(state["backend"])
                if validate_backend(candidate, transported) is not None:
                    raise ValueError("Backend validator must raise on invalid data and return None on success")
                if not _same(before, _owned(candidate.checkpoint_state())) or not _same(state["backend"], transported):
                    raise ValueError("Backend validation mutated candidate or transported state")
                candidate.load_state(_owned(state["backend"]))
                if not _same(state["backend"], _owned(candidate.checkpoint_state())):
                    raise ValueError("Loaded backend does not exactly retain transported state")
                candidate = self._clone_backend(candidate)
            return PreparedWorldBackend(self._token, self._revision, candidate, saved_rng)

    def install(self, prepared: PreparedWorldBackend) -> None:
        with _rng_guard:
            _quiescent()
            if not isinstance(prepared, PreparedWorldBackend) or prepared._destination is not self._token:
                raise ValueError("Prepared backend belongs to a different destination")
            if prepared._used or prepared._revision != self._revision:
                raise ValueError("Prepared backend is already installed or its destination changed")
            if prepared._rng is None:
                raise ValueError("Prepared backend has no owned RNG state")
            self._backend, self._rng = prepared._backend, prepared._rng
            self._failed = False
            self._revision += 1
            prepared._used = True
            prepared._backend = None
            prepared._rng = None
