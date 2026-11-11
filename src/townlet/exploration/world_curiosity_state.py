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
import weakref
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from contextlib import AbstractContextManager, contextmanager
from copy import copy, deepcopy
from dataclasses import dataclass, fields, is_dataclass
from types import MappingProxyType
from typing import Any, Literal, cast

import numpy as np
import torch

from townlet.config.exploration_policy import STRATEGIES, ResolvedExplorationPolicy, Strategy
from townlet.exploration.rng_custody import RNGCurrentToken, RNGOperation, RNGParticipant, process_rng_domain

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
class ServiceClock:
    """Typed service position; live scheduling authority belongs to its owner."""

    unit: Literal["vector_tick", "world_eligible_admission"]
    position: int

    def __post_init__(self) -> None:
        if type(self.unit) is not str or self.unit not in ("vector_tick", "world_eligible_admission"):
            raise ValueError("service clock unit must be an exact supported string")
        _integer(self.position, "position", 0)


@dataclass(frozen=True)
class CuriosityEventId:
    """Exact accepted-episode identity; eligible_seq zero marks no admission yet.

    This value does not authenticate ENV acceptance or allocate live cursors.
    An inactive row may retain the ID of its latest eligible admission.
    """

    curiosity_epoch: int
    world_id: str
    world_episode_seq: int
    eligible_seq: int

    def __post_init__(self) -> None:
        _integer(self.curiosity_epoch, "curiosity_epoch", 0)
        if type(self.world_id) is not str or not self.world_id:
            raise ValueError("world_id must be an exact nonempty string")
        _integer(self.world_episode_seq, "world_episode_seq", 1)
        _integer(self.eligible_seq, "eligible_seq", 0)


@dataclass(frozen=True, init=False, eq=False)
class CuriosityStepStamp:
    """Owned all-row identity snapshot, with identity equality and no hashing.

    Tensor access returns detached independent copies. Acceptance, actual-context
    correlation, phase ordering and retry receipts remain live-owner duties.
    Inputs must be quiescent while this cooperative snapshot is constructed.
    """

    # Intentionally disable object's hash protocol for this identity-equal stamp.
    __hash__ = None  # type: ignore[assignment]

    event_ids: tuple[CuriosityEventId, ...]
    world_ids: tuple[str, ...]
    _world_episode_seqs: torch.Tensor
    _eligible_seqs: torch.Tensor
    _eligible: torch.Tensor

    def __init__(
        self,
        *,
        event_ids: tuple[CuriosityEventId, ...],
        world_ids: tuple[str, ...],
        world_episode_seqs: torch.Tensor,
        eligible_seqs: torch.Tensor,
        eligible: torch.Tensor,
    ) -> None:
        if type(world_ids) is not tuple or not world_ids or any(type(item) is not str or not item for item in world_ids):
            raise ValueError("stamp world_ids must be an exact nonempty tuple of exact nonempty strings")
        if len(set(world_ids)) != len(world_ids):
            raise ValueError("stamp world_ids must be unique")
        rows = len(world_ids)
        if type(event_ids) is not tuple or len(event_ids) != rows or any(type(item) is not CuriosityEventId for item in event_ids):
            raise ValueError("stamp event_ids must be an exact tuple of CuriosityEventId values matching all rows")
        if len({item.curiosity_epoch for item in event_ids}) != 1:
            raise ValueError("stamp rows must share one curiosity epoch")
        inputs = (world_episode_seqs, eligible_seqs, eligible)
        for value, dtype in zip(inputs, (torch.int64, torch.int64, torch.bool), strict=True):
            if (
                not isinstance(value, torch.Tensor)
                or value.layout != torch.strided
                or value.device.type not in ("cpu", "cuda")
                or value.shape != (rows,)
                or value.dtype != dtype
            ):
                raise ValueError("stamp tensors require dense CPU/CUDA [N] vectors with int64/int64/bool dtypes")
        if any(value.device != world_episode_seqs.device for value in inputs):
            raise ValueError("stamp tensors must share exactly one device")
        episodes_owned, sequences_owned, eligible_owned = (value.detach().clone() for value in inputs)
        if bool((episodes_owned < 1).any()) or bool((sequences_owned < 0).any()) or bool((eligible_owned & (sequences_owned < 1)).any()):
            raise ValueError("stamp episodes must be positive and eligible admissions require a positive local sequence")
        episodes = episodes_owned.tolist()
        sequences = sequences_owned.tolist()
        for index, event_id in enumerate(event_ids):
            if (
                event_id.world_id != world_ids[index]
                or event_id.world_episode_seq != episodes[index]
                or event_id.eligible_seq != sequences[index]
            ):
                raise ValueError("stamp event IDs must match exact ordered world/episode/eligible content")
        object.__setattr__(self, "event_ids", event_ids)
        object.__setattr__(self, "world_ids", world_ids)
        object.__setattr__(self, "_world_episode_seqs", episodes_owned)
        object.__setattr__(self, "_eligible_seqs", sequences_owned)
        object.__setattr__(self, "_eligible", eligible_owned)

    @property
    def world_episode_seqs(self) -> torch.Tensor:
        return self._world_episode_seqs.detach().clone()

    @property
    def eligible_seqs(self) -> torch.Tensor:
        return self._eligible_seqs.detach().clone()

    @property
    def eligible(self) -> torch.Tensor:
        return self._eligible.detach().clone()


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


# Shared consumers and private swaps use this same actual process admission.
# Supported direct producers still need enrollment; raw library calls bypass it.
_rng_domain = process_rng_domain()
_rng_local = threading.local()


def _owned(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            return deepcopy(value)
        return value.copy()
    if isinstance(value, OrderedDict):
        ordered = OrderedDict((_owned(key), _owned(item)) for key, item in value.items())
        if hasattr(value, "_metadata"):
            cast(Any, ordered)._metadata = _owned(value._metadata)
        return ordered
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
    if isinstance(left, OrderedDict):
        if list(left) != list(right) or hasattr(left, "_metadata") != hasattr(right, "_metadata"):
            return False
        if hasattr(left, "_metadata") and not _same(left._metadata, right._metadata):
            return False
        return all(_same(left[key], right[key]) for key in left)
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
    _rng_domain._usable()


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


def _restore_checked(state: dict[str, Any], operation: RNGOperation) -> list[BaseException]:
    failures = _restore_globals(state)
    try:
        expected = {name: state[name] for name in ("torch_cpu", "cuda", "python", "numpy_legacy")}
        if not _same(expected, _globals(tuple(state["cuda"]))):
            raise RuntimeError("Ambient RNG restoration did not retain the selected continuation")
    except BaseException as error:
        failures.append(error)
    if failures:
        _rng_domain.poison(operation=operation, error=BaseExceptionGroup("Ambient RNG restoration failed", failures))
    return failures


@contextmanager
def _preserve_ambient(devices: tuple[int, ...], operation: RNGOperation) -> Iterator[dict[str, Any]]:
    entry = _globals(devices)
    failures: list[BaseException] = []
    try:
        yield entry
    except BaseException as error:
        failures.append(error)
    finally:
        failures.extend(_restore_checked(entry, operation))
    _raise_failures(failures)


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
    def __init__(
        self, owner: WorldRNGState, component: str, generator: np.random.Generator, ambient: dict[str, Any], operation: RNGOperation
    ):
        self.owner, self.component = owner, component
        self.sources = WorldRandomSources(PythonRandomSource(self), generator)
        self.ambient = ambient
        self.operation = operation


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
        self._lifetime_owner: object | None = None
        self._participant = _rng_domain.register(owner=self, cuda_devices=cuda_devices, entrypoints=frozenset({"rng"}))

    @property
    def rng_participant(self) -> RNGParticipant:
        return self._participant

    def _operation(self) -> AbstractContextManager[RNGOperation]:
        return _rng_domain.operation(participant=self._participant, operation_kind="rng", lineage=None)

    @contextmanager
    def _initializing(self) -> Iterator[RNGOperation]:
        try:
            with self._operation() as operation:
                yield operation
        except BaseException:
            if not _rng_domain.status()[2]:
                _rng_domain.unregister(participant=self._participant)
            raise

    def _fork(self) -> WorldRNGState:
        """Internal current copy while its producer already owns domain custody."""
        _quiescent()
        if self._broken:
            raise RuntimeError("Private RNG state failed to capture and cannot resume")
        result = object.__new__(WorldRNGState)
        result._descriptor, result._world_id, result._cuda_devices = self._descriptor, self._world_id, self._cuda_devices
        result._components = _owned(self._components)
        result._broken = False
        result._participant = self._participant
        if self._lifetime_owner is not None:
            result._lifetime_owner = self._lifetime_owner
        else:
            result._lifetime_owner = self
        return result

    def _restore(self, payload: Any) -> WorldRNGState:
        result = object.__new__(WorldRNGState)
        result._descriptor, result._world_id, result._cuda_devices = self._descriptor, self._world_id, self._cuda_devices
        result._components = self._decode_snapshot(
            payload, descriptor=self._descriptor, world_id=self._world_id, cuda_devices=self._cuda_devices
        )
        result._broken = False
        result._participant = self._participant
        if self._lifetime_owner is not None:
            result._lifetime_owner = self._lifetime_owner
        else:
            result._lifetime_owner = self
        return result

    @classmethod
    def create(cls, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> WorldRNGState:
        result = cls(descriptor, world_id, cuda_devices, {})
        with result._initializing():
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
            result._components = _owned(components)
            return result

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
        result = cls(descriptor, world_id, cuda_devices, {})
        with result._initializing():
            result._components = cls._decode_snapshot(payload, descriptor=descriptor, world_id=world_id, cuda_devices=cuda_devices)
            return result

    @classmethod
    def _decode_snapshot(
        cls, payload: Any, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]
    ) -> dict[str, Any]:
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
        return cast(dict[str, Any], state["components"])

    def snapshot(self) -> dict[str, Any]:
        with self._operation():
            return self._snapshot()

    def _snapshot(self) -> dict[str, Any]:
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

    def validate_binding(self, *, descriptor: WorldCuriosityDescriptor, world_id: str, cuda_devices: tuple[int, ...]) -> None:
        """Check actual ownership without draws, including inside this owner's callback.

        Roster order and spectators are not stream identity. Snapshot and restore
        remain quiescent lifecycle operations; this read never captures streams.
        """
        stack = _stack()
        lineage: RNGOperation | None
        if stack and stack[-1].owner is self:
            lineage = stack[-1].operation
        else:
            lineage = None
        with _rng_domain.operation(participant=self._participant, operation_kind="rng", lineage=lineage):
            _usable()
            if self._broken:
                raise RuntimeError("Private RNG state is unusable after failed capture")
            stack = _stack()
            if stack and stack[-1].owner is not self:
                raise RuntimeError("Cross-owner nested RNG binding validation is forbidden")
            _domain_arguments(descriptor, world_id, cuda_devices)
            _domain_arguments(self._descriptor, self._world_id, self._cuda_devices)
            # Validate both descriptors, including fields outside stable identity
            # and frozen-dataclass instances forged around their constructor.
            WorldCuriosityDescriptor.from_dict(descriptor.to_dict())
            WorldCuriosityDescriptor.from_dict(self._descriptor.to_dict())
            if not _same(_identity(self._descriptor), _identity(descriptor)):
                raise ValueError("Private RNG descriptor identity disagrees")
            if not _same(self._world_id, world_id) or not _same(self._cuda_devices, cuda_devices):
                raise ValueError("Private RNG world/device binding disagrees")

    @contextmanager
    def activate(self, component: str) -> Iterator[WorldRandomSources]:
        stack = _stack()
        lineage: RNGOperation | None
        if stack and stack[-1].owner is self:
            lineage = stack[-1].operation
        else:
            lineage = None
        with self._activate(component, lineage) as sources:
            yield sources

    @contextmanager
    def _activate(self, component: str, lineage: RNGOperation | None) -> Iterator[WorldRandomSources]:
        with _rng_domain.operation(participant=self._participant, operation_kind="rng", lineage=lineage) as operation:
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
                frame = _Activation(self, component, generator, _owned(entry), operation)
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
                restoration = _restore_checked(stack[-1].ambient if stack else saved, operation)
                if restoration:
                    self._broken = True
                    failures.extend(restoration)
            _raise_failures(failures)


class PreparedWorldBackend:
    """Opaque nonportable identity; all candidate material stays with its issuer."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> PreparedWorldBackend:
        raise TypeError("Prepared backends are issued by their destination owner")

    def __reduce__(self) -> Any:
        raise TypeError("Prepared backends are nonportable")

    def __deepcopy__(self, memo: dict[int, Any]) -> Any:
        raise TypeError("Prepared backends cannot be copied")


@dataclass
class _PreparedBackend:
    revision: int
    current: RNGCurrentToken
    backend: Any
    rng: WorldRNGState | None
    ambient: dict[str, Any] | None
    ambient_revision: int | None


class _BackendOwner:
    """Common admission-before-owner exclusion and opaque candidate issuance."""

    def __init__(self, backend: Any, cuda_devices: tuple[int, ...], previous_rng: WorldRNGState | None):
        self._backend = backend
        self._token = object()
        self._revision = 0
        self._failed = False
        self._lock = threading.RLock()
        self._active = False
        self._prepared: weakref.WeakKeyDictionary[PreparedWorldBackend, _PreparedBackend] = weakref.WeakKeyDictionary()
        entrypoints = frozenset({"rng", "call", "snapshot", "prepare", "install", "validate"})
        if previous_rng is None:
            self._participant = _rng_domain.register(owner=self, cuda_devices=cuda_devices, entrypoints=entrypoints)
        else:
            self._participant = _rng_domain._adopt(
                participant=previous_rng._participant,
                previous_owner=previous_rng,
                owner=self,
                cuda_devices=cuda_devices,
                entrypoints=entrypoints,
            )

    @property
    def rng_participant(self) -> RNGParticipant:
        return self._participant

    @contextmanager
    def _scope(self, kind: str, lineage: RNGOperation | None) -> Iterator[RNGOperation]:
        # Admission always precedes mutable-owner exclusion.
        try:
            with _rng_domain.operation(participant=self._participant, operation_kind=kind, lineage=lineage) as operation:
                with self._lock:
                    _quiescent()
                    if self._active:
                        raise RuntimeError("Reentrant backend lifecycle mutation is forbidden")
                    self._active = True
                    try:
                        yield operation
                    finally:
                        self._active = False
        except BaseException:
            if _rng_domain.status()[2]:
                self._failed = True
            raise

    def _issue(
        self, backend: Any, rng: WorldRNGState | None, ambient: dict[str, Any] | None, operation: RNGOperation, ambient_revision: int | None
    ) -> PreparedWorldBackend:
        handle = object.__new__(PreparedWorldBackend)
        self._prepared[handle] = _PreparedBackend(
            self._revision,
            _rng_domain.current_token(participant=self._participant, operation=operation),
            backend,
            rng,
            ambient,
            ambient_revision,
        )
        return handle

    def _validate_prepared(self, prepared: PreparedWorldBackend, operation: RNGOperation) -> _PreparedBackend:
        if type(prepared) is not PreparedWorldBackend or prepared not in self._prepared:
            raise ValueError("Prepared backend is foreign, fabricated or already consumed")
        state = self._prepared[prepared]
        if state.revision != self._revision:
            raise ValueError("Prepared backend destination changed")
        _rng_domain.validate_current(token=state.current, operation=operation)
        if state.ambient is not None and state.ambient_revision != _rng_domain._ambient_revision:
            raise ValueError("Shared reset continuation predecessor changed; prepare again from current continuation")
        return state

    def validate_prepared(self, prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None:
        with self._scope("validate", lineage) as operation:
            state = self._validate_prepared(prepared, operation)
            replacement = _rng_domain.current_token(participant=self._participant, operation=operation)
            _rng_domain._consume_token(state.current)
            state.current = replacement

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


class OwnedWorldBackend(_BackendOwner):
    """Serialized private lifecycle; failed live callbacks quarantine.

    Provider adapters own semantic qualification. Raw retained references preserve
    their caller-owned quiescence obligation; the domain does not intercept them.
    """

    def __init__(self, backend: Any, rng: WorldRNGState):
        super().__init__(backend, rng._cuda_devices, rng)
        self._rng = rng
        rng._participant = self._participant
        rng._lifetime_owner = self

    @classmethod
    def construct(cls, *, rng: WorldRNGState, factory: Callable[[WorldRNGState], Any]) -> OwnedWorldBackend:
        if not isinstance(rng, WorldRNGState) or not callable(factory):
            raise ValueError("Owned construction requires an RNG owner and factory")
        with rng._operation() as operation:
            _quiescent()
            candidate_rng = rng._fork()
            with candidate_rng._activate("model_init", operation):
                backend = cls._clone_backend(factory(candidate_rng))
                cls._backend_contract(backend)
        return cls(backend, candidate_rng)

    def call(self, operation: Callable[[Any, WorldRandomSources], Any], *, lineage: RNGOperation | None) -> Any:
        """Managed mutation; retained raw aliases still require caller quiescence."""
        with self._scope("call", lineage) as custody:
            if self._failed:
                raise RuntimeError("Owned backend is quarantined after a failed callback; prepare an explicit restore")
            if not callable(operation):
                raise ValueError("Owned operation must be callable")
            try:
                with self._rng._activate("service", custody) as sources:
                    return _owned(operation(self._backend, sources))
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def snapshot(self, *, lineage: RNGOperation | None) -> dict[str, Any]:
        with self._scope("snapshot", lineage) as operation:
            try:
                with self._rng._activate("service", operation):
                    backend_state = _owned(self._backend.checkpoint_state())
                return {
                    "schema": "owned-world-backend-v1",
                    "healthy": not self._failed,
                    "backend": backend_state,
                    "rng": self._rng._snapshot(),
                }
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def prepare_restore(
        self,
        payload: Any,
        *,
        factory: Callable[[WorldRNGState], Any],
        validate_backend: Callable[[Any, Any], object],
        lineage: RNGOperation | None,
    ) -> PreparedWorldBackend:
        with self._scope("prepare", lineage) as operation:
            if not callable(factory) or not callable(validate_backend):
                raise ValueError("Prepared restore requires factory and pure backend validation")
            state = _owned(payload)
            _keys(state, {"schema", "healthy", "backend", "rng"}, "Owned backend snapshot")
            if state["schema"] != "owned-world-backend-v1" or state["healthy"] is not True:
                raise ValueError("Only a healthy owned backend snapshot can be restored")
            with _preserve_ambient(self._rng._cuda_devices, operation):
                saved_rng = self._rng._restore(state["rng"])
                work_rng = saved_rng._fork()
                with work_rng._activate("model_init", operation):
                    candidate = self._clone_backend(factory(work_rng))
                    self._backend_contract(candidate)
                with work_rng._activate("service", operation):
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
            return self._issue(candidate, saved_rng, None, operation, None)

    def prepare_learning_reset(
        self,
        *,
        factory: Callable[[WorldRNGState], Any],
        prepare_native: Callable[[Any, Any], object],
        lineage: RNGOperation | None,
    ) -> PreparedWorldBackend:
        """Pure current fork; candidate-only native work cannot mutate the live owner."""
        with self._scope("prepare", lineage) as operation:
            if self._failed:
                raise RuntimeError("Learning reset requires a healthy owned backend")
            if not callable(factory) or not callable(prepare_native):
                raise ValueError("Learning reset requires real factory and candidate-only native adapter")
            with _preserve_ambient(self._rng._cuda_devices, operation):
                candidate = self._clone_backend(self._backend)
                candidate_rng = self._rng._fork()
                with candidate_rng._activate("model_init", operation):
                    fresh = self._clone_backend(factory(candidate_rng))
                    self._backend_contract(fresh)
                # Validation/reconstruction draws are disposable, unlike actual
                # selected fresh construction. Preserve the entire candidate fork.
                work_rng = candidate_rng._fork()
                with work_rng._activate("service", operation):
                    if prepare_native(candidate, fresh) is not None:
                        raise ValueError("Native reset adapter must install candidate work and return None")
                    self._backend_contract(candidate)
                    candidate = self._clone_backend(candidate)
            return self._issue(candidate, candidate_rng, None, operation, None)

    def install(self, prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None:
        with self._scope("install", lineage) as operation:
            state = self._validate_prepared(prepared, operation)
            if state.rng is None:
                raise ValueError("Prepared backend has no owned RNG state")
            try:
                self._backend, self._rng = state.backend, state.rng
                self._failed = False
                self._revision += 1
                del self._prepared[prepared]
                _rng_domain._consume_token(state.current)
            except BaseException:
                self._failed = True
                raise


def _stage_ambient(state: dict[str, Any], entry: dict[str, Any], operation: RNGOperation) -> None:
    failures: list[BaseException] = []
    try:
        _install_globals(state)
        if not _same(state, _globals(tuple(state["cuda"]))):
            raise RuntimeError("Candidate ambient RNG installation did not verify")
    except BaseException as error:
        failures.append(error)
        failures.extend(_restore_checked(entry, operation))
    _raise_failures(failures)


class SharedWorldBackend(_BackendOwner):
    """Admitted real shared native lifecycle using the existing ambient stream.

    Shared callbacks receive the actual native backend. A returned value is copied;
    references retained through side effects remain caller-quiescent raw aliases.
    No parent boundary or all-child publication authority is created here.
    """

    def __init__(self, backend: Any, cuda_devices: tuple[int, ...]):
        super().__init__(backend, cuda_devices, None)
        self._cuda_devices = cuda_devices

    @classmethod
    def construct(cls, *, factory: Callable[[], Any], cuda_devices: tuple[int, ...]) -> SharedWorldBackend:
        if not callable(factory):
            raise ValueError("Shared construction requires an actual factory")
        owner = cls(None, cuda_devices)
        try:
            with owner._scope("prepare", None) as operation:
                if cuda_devices and (not torch.cuda.is_initialized() or any(index >= torch.cuda.device_count() for index in cuda_devices)):
                    raise ValueError("Initialize explicitly declared shared CUDA devices before construction")
                with _preserve_ambient(cuda_devices, operation) as entry:
                    backend = factory()
                    continuation = _globals(cuda_devices)
                    candidate = cls._clone_backend(backend)
                    cls._backend_contract(candidate)
                _stage_ambient(continuation, entry, operation)
                _rng_domain._commit_ambient(operation)
                owner._backend = candidate
            return owner
        except BaseException:
            if not _rng_domain.status()[2]:
                _rng_domain.unregister(participant=owner._participant)
            raise

    def call(self, operation: Callable[[Any], Any], *, lineage: RNGOperation | None) -> Any:
        with self._scope("call", lineage):
            if self._failed:
                raise RuntimeError("Shared backend is quarantined; prepare an explicit restore")
            if not callable(operation):
                raise ValueError("Shared operation must be callable")
            try:
                return _owned(operation(self._backend))
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def snapshot(self, *, lineage: RNGOperation | None) -> dict[str, Any]:
        with self._scope("snapshot", lineage):
            try:
                return {
                    "schema": "shared-world-backend-v1",
                    "healthy": not self._failed,
                    "backend": _owned(self._backend.checkpoint_state()),
                }
            except BaseException:
                self._failed = True
                raise
            finally:
                self._revision += 1

    def prepare_restore(
        self,
        payload: Any,
        *,
        factory: Callable[[], Any],
        validate_backend: Callable[[Any, Any], object],
        lineage: RNGOperation | None,
    ) -> PreparedWorldBackend:
        with self._scope("prepare", lineage) as operation:
            if not callable(factory) or not callable(validate_backend):
                raise ValueError("Shared restore requires factory and complete pure native validator")
            state = _owned(payload)
            _keys(state, {"schema", "healthy", "backend"}, "Shared backend snapshot")
            if state["schema"] != "shared-world-backend-v1" or state["healthy"] is not True:
                raise ValueError("Only a healthy shared backend snapshot can be restored")
            with _preserve_ambient(self._cuda_devices, operation):
                candidate = self._clone_backend(factory())
                self._backend_contract(candidate)
                before = _owned(candidate.checkpoint_state())
                transported = _owned(state["backend"])
                if validate_backend(candidate, transported) is not None:
                    raise ValueError("Native validator must return None on success")
                if not _same(before, candidate.checkpoint_state()) or not _same(state["backend"], transported):
                    raise ValueError("Shared native validator mutated candidate or transport")
                candidate.load_state(_owned(state["backend"]))
                if not _same(state["backend"], candidate.checkpoint_state()):
                    raise ValueError("Shared native restore did not retain exact transport")
                candidate = self._clone_backend(candidate)
            # Ordinary restore has no saved process RNG field and never rewinds a peer.
            return self._issue(candidate, None, None, operation, None)

    def prepare_learning_reset(
        self,
        *,
        factory: Callable[[], Any],
        prepare_native: Callable[[Any, Any], object],
        lineage: RNGOperation | None,
    ) -> PreparedWorldBackend:
        with self._scope("prepare", lineage) as operation:
            if self._failed:
                raise RuntimeError("Learning reset requires a healthy shared backend")
            if not callable(factory) or not callable(prepare_native):
                raise ValueError("Shared reset requires real factory and candidate-only native adapter")
            predecessor = _rng_domain._ambient_revision
            with _preserve_ambient(self._cuda_devices, operation):
                candidate = self._clone_backend(self._backend)
                fresh = factory()
                continuation = _globals(self._cuda_devices)
                fresh = self._clone_backend(fresh)
                self._backend_contract(fresh)
                if prepare_native(candidate, fresh) is not None:
                    raise ValueError("Native reset adapter must install candidate work and return None")
                self._backend_contract(candidate)
                candidate = self._clone_backend(candidate)
            return self._issue(candidate, None, continuation, operation, predecessor)

    def install(self, prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None:
        with self._scope("install", lineage) as operation:
            state = self._validate_prepared(prepared, operation)
            if state.rng is not None:
                raise ValueError("A shared backend cannot install private RNG ownership")
            if state.ambient is not None:
                entry = _globals(self._cuda_devices)
                _stage_ambient(state.ambient, entry, operation)
                _rng_domain._commit_ambient(operation)
            # Fallible RNG staging precedes the first child assignment. Actual
            # later joint publication failures require the parent's quarantine.
            try:
                self._backend = state.backend
                self._failed = False
                self._revision += 1
                del self._prepared[prepared]
                _rng_domain._consume_token(state.current)
            except BaseException:
                self._failed = True
                raise
