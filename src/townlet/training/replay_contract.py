"""Owned replay transport, independent of storage and sampling implementations.

Constructors detach/clone tensors and copy receipt arrays; producer mutations
cannot rewrite history. Frozen fields prevent rebinding, not tensor mutation:
consumers own their transport and must not mutate it while a learner uses it.
No missing-mask inference is performed here. Explicitly unconstrained adapters
must supply their declared all-legal mask; constrained old history is archival.
"""

from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, fields, replace
from functools import wraps
from threading import RLock, current_thread
from typing import Concatenate, Literal, NoReturn
from weakref import WeakKeyDictionary

import numpy as np
import numpy.typing as npt
import torch
from torch import Tensor

from townlet.exploration import rng_custody
from townlet.exploration.rng_custody import RNGCurrentToken, RNGOperation, RNGParticipant, process_rng_domain


class HistoricalLegalityUnavailable(ValueError):  # noqa: N818 - approved public interface
    """Unknown historical legality belongs in the approved archive, not replay."""


class PreparedReplay:
    """Identity-only publication capability; material stays with its issuer."""

    __slots__ = ("__weakref__",)

    def __new__(cls) -> NoReturn:
        raise TypeError("Prepared replay capabilities are issued by their owner")

    def __init__(self) -> None:
        raise TypeError("Prepared replay capabilities cannot be reinitialized")

    def __reduce__(self) -> NoReturn:
        raise TypeError("Prepared replay capabilities cannot be copied or serialized")


class ReplayCustody:
    """One process lease before one replay owner's mutation exclusion."""

    device: torch.device
    capacity: int
    action_dim: int | None
    actions: Tensor | None
    observations: Tensor | None
    legality_recorded: Tensor | None
    _local_cuda_contracts: Mapping[str, str]

    def _init_custody(self, device: torch.device) -> None:
        # Current full-member consumers migrate in their own producer packets.
        if not isinstance(device, torch.device) or device.type not in ("cpu", "cuda"):
            raise ValueError("replay custody requires an explicit CPU or CUDA torch.device")
        devices: tuple[int, ...] = ()
        if device.type == "cuda":
            index = device.index
            if type(index) is not int or index < 0:
                raise ValueError("CUDA replay custody requires an explicit initialized device index")
            devices = (index,)
        self._initialize_custody(device, devices)

    def _init_device_custody(self, device: torch.device) -> None:
        self._initialize_custody(device, ())

    def _initialize_custody(self, device: torch.device, cuda_devices: tuple[int, ...]) -> None:
        if not isinstance(device, torch.device) or device.type not in ("cpu", "cuda"):
            raise ValueError("replay custody requires an explicit CPU or CUDA torch.device")
        self._replay_lock = RLock()
        self._replay_revision = 0
        self._replay_healthy = True
        self._replay_scope: tuple[object, torch.device | None, str] | None = None
        self._replay_prepared: WeakKeyDictionary[PreparedReplay, tuple[int, RNGCurrentToken, object]] = WeakKeyDictionary()
        self._replay_participant = process_rng_domain().register(
            owner=self, cuda_devices=cuda_devices, entrypoints=frozenset({"sample", "prepare", "install"})
        )

    @property
    def rng_participant(self) -> RNGParticipant:
        return self._replay_participant

    def _check_custody(self) -> None:
        if not self._replay_healthy:
            raise RuntimeError("Replay owner is quarantined after uncertain publication")

    @contextmanager
    def _owner_operation(self, *, mutation: bool) -> Iterator[None]:
        with self._replay_lock:
            self._check_custody()
            if self._replay_scope is not None:
                raise RuntimeError("Unrelated replay lifecycle reentry")
            if mutation:
                self._replay_revision += 1
            yield

    @contextmanager
    def _domain_operation(self, kind: str, lineage: RNGOperation | None) -> Iterator[RNGOperation]:
        with process_rng_domain().operation(participant=self._replay_participant, operation_kind=kind, lineage=lineage) as lease:
            yield lease

    @property
    def _effective_replay_device(self) -> torch.device:
        if self._replay_scope is None or self._replay_scope[0] is not current_thread() or self._replay_scope[1] is None:
            raise RuntimeError("Replay allocation was not included in this invocation plan")
        return self._replay_scope[1]

    def _replay_inventory(
        self, route: str, args: tuple[object, ...], kwargs: Mapping[str, object]
    ) -> tuple[torch.device | None, tuple[object, ...]]:
        raise NotImplementedError("Device producer must supply its source-owned inventory")

    def _replay_children(self, value: object) -> tuple[object, ...]:
        if isinstance(value, Mapping):
            return tuple(item for pair in value.items() for item in pair)
        if type(value) in (tuple, list) and isinstance(value, (tuple, list)):
            return tuple(value)
        return ()

    @staticmethod
    def _replay_argument(args: tuple[object, ...], kwargs: Mapping[str, object], index: int, name: str) -> object:
        if len(args) > index:
            return args[index]
        return kwargs.get(name)

    def _push_inventory(
        self, route: str, args: tuple[object, ...], kwargs: Mapping[str, object], retained: tuple[object, ...]
    ) -> tuple[torch.device | None, tuple[object, ...]]:
        observations = self._replay_argument(args, kwargs, 0, "observations")
        prefix: tuple[object, ...] = ()
        if route == "push_recorded":
            prefix = (self._replay_argument(args, kwargs, 4, "dones"), self._replay_argument(args, kwargs, 5, "next_action_masks"))
        elif self.action_dim is not None:
            prefix = (self._replay_argument(args, kwargs, 4, "dones"),)
        if not isinstance(observations, Tensor) or observations.ndim != 2 or observations.dtype != torch.float32:
            return None, prefix
        if observations.shape[1] < 1 or observations.shape[0] > self.capacity:
            return None, prefix
        rewards = self._replay_argument(args, kwargs, 2, "rewards")
        values = (
            *args,
            *(kwargs.get(name) for name in ("observations", "actions", "next_observations", "dones", "next_action_masks")),
            *(getattr(rewards, name, None) for name in ("total", "extrinsic", "intrinsic", "shaping")),
        )
        if observations.shape[0]:
            return self.device, (*values, *retained)
        if route == "push_recorded" or self.action_dim is not None:
            return None, (*values, self.actions)
        return None, values

    def _transport_target(self, state: Mapping[str, object], size_field: str, *, strict: bool) -> torch.device | None:
        capacity = state.get("capacity")
        if strict and type(capacity) is not int:
            return None
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity != self.capacity:
            return None
        count = state.get(size_field)
        if strict and type(count) is not int:
            return None
        if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
            return None
        return self.device

    def _sample_inventory(
        self,
        route: str,
        args: tuple[object, ...],
        kwargs: Mapping[str, object],
        retained: tuple[object, ...],
        *,
        size: int,
        mode: str,
        with_replacement: bool,
        strict: bool,
    ) -> tuple[torch.device | None, tuple[object, ...]]:
        count: object
        if route == "sample_batch":
            request = self._replay_argument(args, kwargs, 0, "request")
            if not isinstance(request, ReplayRequest):
                return None, ()
            if (request.sequence_mode, request.sequence_objective, request.sequence_length) != (
                "feedforward",
                "transition",
                1,
            ) or request.sampling_mode != mode:
                return None, ()
            if self.action_dim is None or self.legality_recorded is None:
                return None, ()
            count = request.batch_size
            if size < request.min_transitions or size == 0 or (not with_replacement and count > size):
                return None, (self.legality_recorded,)
        else:
            count = self._replay_argument(args, kwargs, 0, "batch_size")
        if strict:
            if type(count) is not int or count < 0:
                return None, ()
        elif not isinstance(count, (int, np.integer)) or isinstance(count, (bool, np.bool_)) or count <= 0:
            return None, ()
        if self.observations is None or (not with_replacement and count > size):
            return None, ()
        return self.device, retained

    def _completion_devices(self, sources: tuple[int, ...], device: torch.device | None) -> tuple[int, ...]:
        if device is not None and device.type == "cuda":
            index = device.index
            if type(index) is not int:
                raise ValueError("Replay effective CUDA device is not concrete")
            return tuple(sorted({*sources, index}))
        return sources

    def _replay_cuda_devices(self, values: tuple[object, ...]) -> tuple[int, ...]:
        result: set[int] = set()

        def visit(value: object) -> None:
            if isinstance(value, Tensor):
                if value.device.type == "cuda":
                    index = value.device.index
                    if type(index) is not int or index < 0:
                        raise ValueError("Retained replay CUDA tensors require concrete device metadata")
                    result.add(index)
            else:
                for child in self._replay_children(value):
                    visit(child)

        for value in values:
            visit(value)
        return tuple(sorted(result))

    def _device_plan(
        self, route: str, args: tuple[object, ...], kwargs: Mapping[str, object], *, admitted: bool
    ) -> tuple[torch.device | None, tuple[int, ...]]:
        device, values = self._replay_inventory(route, args, kwargs)
        if admitted:
            values = (*values, *(record[2] for record in self._replay_prepared.values()))
        return device, self._replay_cuda_devices(values)

    def _quarantine_replay(self) -> None:
        self._replay_healthy = False
        self._replay_revision += 1

    @contextmanager
    def _local_operation(self, route: str, args: tuple[object, ...], kwargs: Mapping[str, object], *, mutation: bool) -> Iterator[None]:
        effective: torch.device | None
        if self._replay_scope is not None and self._replay_scope[0] is current_thread():
            raise RuntimeError("Unrelated replay lifecycle reentry")
        while True:
            with self._owner_operation(mutation=False):
                device, sources = self._device_plan(route, args, kwargs, admitted=False)
                if not sources and (device is None or device.type == "cpu"):
                    if mutation:
                        self._replay_revision += 1
                    self._replay_scope = (current_thread(), device, route)
                    try:
                        yield
                    finally:
                        self._replay_scope = None
                    return
            contract = getattr(rng_custody, self._local_cuda_contracts[route])
            with process_rng_domain().local_cuda_access(participant=self._replay_participant, contract=contract) as gate:
                if device is not None and device.type == "cuda":
                    effective = torch.device("cuda", gate.resolve_cuda(device=device))
                else:
                    effective = device
                for index in sources:
                    gate.resolve_cuda(device=torch.device("cuda", index))
                with self._owner_operation(mutation=False):
                    selected, actual = self._device_plan(route, args, kwargs, admitted=False)
                    if selected != device:
                        continue
                    devices = self._completion_devices(actual, effective)
                    self._replay_scope = (current_thread(), effective, route)
                    try:
                        with gate.complete(cuda_devices=devices):
                            if mutation:
                                self._replay_revision += 1
                            yield
                    finally:
                        if gate.completion_failed():
                            self._quarantine_replay()
                        self._replay_scope = None
                    return

    @contextmanager
    def _device_operation(
        self, kind: str, lineage: RNGOperation | None, route: str, args: tuple[object, ...], kwargs: Mapping[str, object], *, mutation: bool
    ) -> Iterator[RNGOperation]:
        effective: torch.device | None
        if self._replay_scope is not None and self._replay_scope[0] is current_thread():
            raise RuntimeError("Unrelated replay lifecycle reentry")
        domain = process_rng_domain()
        with domain.admission(lineage=lineage) as gate:
            while True:
                with self._owner_operation(mutation=False):
                    device, sources = self._device_plan(route, args, kwargs, admitted=True)
                if device is not None and device.type == "cuda":
                    effective = torch.device("cuda", gate.resolve_cuda(device=device))
                else:
                    effective = device
                for index in sources:
                    gate.resolve_cuda(device=torch.device("cuda", index))
                with self._owner_operation(mutation=False):
                    selected, actual = self._device_plan(route, args, kwargs, admitted=True)
                    if selected != device:
                        continue
                    devices = self._completion_devices(actual, effective)
                    if lineage is None:
                        gate.enroll(participant=self._replay_participant, cuda_devices=devices)
                    invocation = domain.device_invocation(
                        participant=self._replay_participant, operation_kind=kind, lineage=lineage, cuda_devices=devices
                    )
                    entered = False
                    try:
                        with ExitStack() as work:
                            try:
                                lease = work.enter_context(invocation)
                            except ValueError as error:
                                if lineage is not None:
                                    raise RuntimeError("CUDA replay requires idle preflight for its requested inventory") from error
                                raise
                            entered = True
                            self._replay_scope = (current_thread(), effective, route)
                            if mutation:
                                self._replay_revision += 1
                            yield lease
                    finally:
                        if entered and invocation.completion_failed():
                            self._quarantine_replay()
                        self._replay_scope = None
                    return

    @contextmanager
    def cuda_preflight(self, *, anticipated_devices: tuple[torch.device, ...]) -> Iterator[None]:
        with replay_cuda_preflight(owners=(self,), anticipated_devices=anticipated_devices):
            yield

    def _issue_replay(self, payload: object, lease: RNGOperation) -> PreparedReplay:
        handle = object.__new__(PreparedReplay)
        token = process_rng_domain().current_token(participant=self._replay_participant, operation=lease)
        self._replay_prepared[handle] = (self._replay_revision, token, payload)
        return handle

    def _prepared_payload(self, handle: object) -> object:
        if not isinstance(handle, PreparedReplay) or handle not in self._replay_prepared:
            raise ValueError("Prepared replay is foreign, fabricated or already consumed")
        return self._replay_prepared[handle][2]

    def _validate_replay(self, handle: PreparedReplay, lease: RNGOperation) -> None:
        recorded = self._replay_prepared.get(handle)
        if recorded is None:
            raise ValueError("Prepared replay is foreign, fabricated or already consumed")
        revision, token, _ = recorded
        if revision != self._replay_revision:
            raise ValueError("Prepared replay destination changed")
        process_rng_domain().validate_current(token=token, operation=lease)

    def _publish_replay(self, handle: PreparedReplay, publish: Callable[[], None]) -> None:
        try:
            publish()
        except BaseException:
            self._replay_healthy = False
            self._replay_revision += 1
            raise
        del self._replay_prepared[handle]
        self._replay_revision += 1


def _required_lineage(arguments: Mapping[str, object]) -> RNGOperation | None:
    try:
        lineage = arguments["lineage"]
    except KeyError:
        raise TypeError("Missing required keyword-only argument: 'lineage'") from None
    if lineage is not None and not isinstance(lineage, RNGOperation):
        raise ValueError("RNG operation lineage is foreign or expired")
    return lineage


@contextmanager
def replay_cuda_preflight(*, owners: tuple[ReplayCustody, ...], anticipated_devices: tuple[torch.device, ...]) -> Iterator[None]:
    if type(owners) is not tuple or not all(isinstance(owner, ReplayCustody) for owner in owners):
        raise ValueError("Replay preflight requires a tuple of replay owners")
    if type(anticipated_devices) is not tuple or not all(
        isinstance(device, torch.device) and device.type in ("cpu", "cuda") for device in anticipated_devices
    ):
        raise ValueError("Replay preflight requires explicit CPU/CUDA device metadata")
    pinned = tuple(sorted({id(owner): owner for owner in owners}.values(), key=id))
    with process_rng_domain().admission(lineage=None) as gate:
        for owner in pinned:
            gate.enroll(participant=owner.rng_participant, cuda_devices=())
        resolved = {
            gate.resolve_cuda(device=device)
            for device in (*anticipated_devices, *(owner.device for owner in pinned))
            if device.type == "cuda"
        }
        with ExitStack() as locks:
            for owner in pinned:
                locks.enter_context(owner._owner_operation(mutation=False))
            for owner in pinned:
                _, sources = owner._device_plan("preflight", (), {}, admitted=True)
                gate.enroll(participant=owner.rng_participant, cuda_devices=tuple(sorted({*resolved, *sources})))
            yield


def replay_local[Owner: ReplayCustody, Result, **Arguments](
    *, mutation: bool
) -> Callable[[Callable[Concatenate[Owner, Arguments], Result]], Callable[Concatenate[Owner, Arguments], Result]]:
    def decorate(method: Callable[Concatenate[Owner, Arguments], Result]) -> Callable[Concatenate[Owner, Arguments], Result]:
        @wraps(method)
        def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> Result:
            with self._local_operation(method.__name__, args, kwargs, mutation=mutation):
                return method(self, *args, **kwargs)

        return guarded

    return decorate


def replay_device_sample[Owner: ReplayCustody, Result, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], Result],
) -> Callable[Concatenate[Owner, Arguments], Result]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> Result:
        with self._device_operation("sample", _required_lineage(kwargs), method.__name__, args, kwargs, mutation=True):
            return method(self, *args, **kwargs)

    return guarded


def replay_device_prepare[Owner: ReplayCustody, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], object],
) -> Callable[Concatenate[Owner, Arguments], PreparedReplay]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> PreparedReplay:
        with self._device_operation("prepare", _required_lineage(kwargs), method.__name__, args, kwargs, mutation=False) as lease:
            return self._issue_replay(method(self, *args, **kwargs), lease)

    return guarded


def replay_read[Owner: ReplayCustody, Result, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], Result],
) -> Callable[Concatenate[Owner, Arguments], Result]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> Result:
        with self._owner_operation(mutation=False):
            return method(self, *args, **kwargs)

    return guarded


def replay_mutation[Owner: ReplayCustody, Result, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], Result],
) -> Callable[Concatenate[Owner, Arguments], Result]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> Result:
        with self._owner_operation(mutation=True):
            return method(self, *args, **kwargs)

    return guarded


def replay_sample[Owner: ReplayCustody, Result, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], Result],
) -> Callable[Concatenate[Owner, Arguments], Result]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> Result:
        with self._domain_operation("sample", _required_lineage(kwargs)):
            with self._owner_operation(mutation=True):
                return method(self, *args, **kwargs)

    return guarded


def replay_prepare[Owner: ReplayCustody, **Arguments](
    method: Callable[Concatenate[Owner, Arguments], object],
) -> Callable[Concatenate[Owner, Arguments], PreparedReplay]:
    @wraps(method)
    def guarded(self: Owner, /, *args: Arguments.args, **kwargs: Arguments.kwargs) -> PreparedReplay:
        with self._domain_operation("prepare", _required_lineage(kwargs)) as lease:
            with self._owner_operation(mutation=False):
                return self._issue_replay(method(self, *args, **kwargs), lease)

    return guarded


def _integer(name: str, value: int, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def validate_successor_masks(masks: Tensor, dones: Tensor, *, action_dim: int) -> None:
    """Validate actual successor sets; only terminal rows may have no action."""
    _integer("action_dim", action_dim, 1)
    if not isinstance(masks, Tensor) or masks.dtype != torch.bool:
        raise ValueError("next_action_masks/legal must be a bool tensor")
    if not isinstance(dones, Tensor) or dones.dtype != torch.bool:
        raise ValueError("dones must be a bool tensor")
    if masks.shape != (*dones.shape, action_dim) or masks.device != dones.device:
        raise ValueError("successor masks shape/device must match dones and action_dim")
    if ((~dones) & ~masks.any(dim=-1)).any():
        raise ValueError("nonterminal successor has no legal action")


@dataclass(frozen=True, slots=True)
class ReplayRequest:
    batch_size: int
    sequence_length: int
    min_transitions: int
    sampling_mode: str
    sequence_mode: str
    sequence_objective: str

    def __post_init__(self) -> None:
        _integer("batch_size", self.batch_size, 1)
        _integer("sequence_length", self.sequence_length, 1)
        _integer("min_transitions", self.min_transitions, 0)
        for name in ("sampling_mode", "sequence_mode", "sequence_objective"):
            _text(name, getattr(self, name))


ReadinessReason = Literal["ready", "warmup", "batch_unavailable", "window_unavailable", "capacity_window_impossible"]


@dataclass(frozen=True, slots=True)
class ReplayReadiness:
    ready: bool
    retained_transitions: int
    sampleable_units: int
    reason: ReadinessReason

    def __post_init__(self) -> None:
        _integer("retained_transitions", self.retained_transitions, 0)
        _integer("sampleable_units", self.sampleable_units, 0)
        if type(self.ready) is not bool or self.reason not in (
            "ready",
            "warmup",
            "batch_unavailable",
            "window_unavailable",
            "capacity_window_impossible",
        ):
            raise ValueError("ready/reason must describe a recognized readiness result")
        if self.ready != (self.reason == "ready") or (self.ready and self.sampleable_units == 0):
            raise ValueError("ready must agree with reason and a nonempty sampleable population")


@dataclass(frozen=True, slots=True)
class SamplingReceipt:
    """Ordered proposal evidence; weights are not renormalized by this DTO.

    Indices identify sampler units, not necessarily contiguous storage slots.
    Sampling laws and objective-specific weight validation belong to samplers.
    """

    indices: npt.NDArray[np.int64]
    weights: npt.NDArray[np.float64]
    population_size: int
    conditional_draw_probabilities: npt.NDArray[np.float64]
    mode: str
    objective_unit: str
    weight_rule: str

    def __post_init__(self) -> None:
        _integer("population_size", self.population_size, 1)
        for name in ("mode", "objective_unit", "weight_rule"):
            _text(name, getattr(self, name))
        size = None
        for name, dtype in (("indices", np.int64), ("weights", np.float64), ("conditional_draw_probabilities", np.float64)):
            value = getattr(self, name)
            if not isinstance(value, np.ndarray) or value.dtype != dtype or value.ndim != 1 or value.size == 0:
                raise ValueError(f"{name} must be a nonempty 1D ndarray[{np.dtype(dtype)}]")
            if size is not None and value.size != size:
                raise ValueError(f"{name} shape must match receipt indices")
            size = value.size
            if not np.isfinite(value).all() or (value < 0).any():
                raise ValueError(f"{name} must be finite and nonnegative")
            if name != "indices" and (value <= 0).any():
                raise ValueError(f"{name} must be positive")
            if name == "conditional_draw_probabilities" and (value > 1).any():
                raise ValueError("conditional_draw_probabilities must be <= 1")
            owned = value.copy()
            owned.setflags(write=False)
            object.__setattr__(self, name, owned)


@dataclass(frozen=True, slots=True)
class ReplayBatch:
    """Real rows are the prefix defined by lengths; loss_mask may select anchors.

    Optional reward components stay independent and never recompose rewards.
    Padded rows carry transport only and are not validated as experience.
    """

    legality_recorded: Tensor
    observations: Tensor
    actions: Tensor
    rewards: Tensor
    rewards_extrinsic: Tensor | None
    rewards_intrinsic: Tensor | None
    rewards_shaping: Tensor | None
    next_observations: Tensor
    dones: Tensor
    next_action_masks: Tensor
    loss_mask: Tensor
    lengths: Tensor
    unit_ids: Tensor
    weights: Tensor
    sampling: SamplingReceipt

    def __post_init__(self) -> None:
        obs = self.observations
        if not isinstance(obs, Tensor) or obs.ndim not in (2, 3) or any(d <= 0 for d in obs.shape):
            raise ValueError("observations shape must be nonempty [B,D] or [B,L,D]")
        shape, device = obs.shape[:-1], obs.device
        b, length = shape[0], shape[1] if obs.ndim == 3 else 1
        for name in ("lengths", "unit_ids", "weights"):
            value = getattr(self, name)
            if not isinstance(value, Tensor) or value.shape != (b,) or value.device != device:
                raise ValueError(f"{name} shape/device must be [B] on observations device")
            if name == "weights":
                if value.dtype != torch.float64 or not torch.isfinite(value).all() or (value <= 0).any():
                    raise ValueError("weights must be finite positive float64 values")
            elif value.dtype != torch.int64 or (value < (1 if name == "lengths" else 0)).any():
                raise ValueError(f"{name} must be int64 with valid nonnegative indices/positive lengths")
        if (self.lengths > length).any():
            raise ValueError("lengths exceed real transport capacity")
        real = torch.arange(length, device=device)[None, :] < self.lengths[:, None]
        if obs.ndim == 2:
            real = real[:, 0]
        for name in (
            "actions",
            "rewards",
            "rewards_extrinsic",
            "rewards_intrinsic",
            "rewards_shaping",
            "dones",
            "legality_recorded",
            "loss_mask",
        ):
            value = getattr(self, name)
            if value is None and name in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
                continue
            if not isinstance(value, Tensor) or value.shape != shape or value.device != device:
                raise ValueError(f"{name} shape/device must match transition rows")
            expected = torch.bool
            if name == "actions":
                expected = torch.int64
            if name.startswith("rewards"):
                if value.dtype != torch.float32 or not torch.isfinite(value[real]).all():
                    raise ValueError(f"{name} must have finite real float32 values")
            elif value.dtype != expected:
                raise ValueError(f"{name} must have dtype {expected}")
        for name in ("observations", "next_observations"):
            value = getattr(self, name)
            if not isinstance(value, Tensor) or value.shape != obs.shape or value.device != device or value.dtype != obs.dtype:
                raise ValueError(f"{name} shape/dtype/device must match observations")
            if value.dtype != torch.float32 or not torch.isfinite(value[real]).all():
                raise ValueError(f"{name} must contain finite real float32 observations")
        masks = self.next_action_masks
        if not isinstance(masks, Tensor) or masks.ndim != len(shape) + 1 or masks.shape[:-1] != shape or masks.shape[-1] < 1:
            raise ValueError("next_action_masks shape must be [*transition_rows,A] with A>0")
        if masks.dtype != torch.bool or masks.device != device:
            raise ValueError("next_action_masks must be bool on observations device")
        if not self.legality_recorded[real].all():
            raise HistoricalLegalityUnavailable("unrecorded real successor legality: preserve in approved historical archive")
        if (self.loss_mask & ~real).any() or not self.loss_mask.reshape(b, -1).any(dim=1).all():
            raise ValueError("loss_mask must select real rows and at least one row per unit")
        if obs.ndim == 3 and (self.dones[:, :-1] & real[:, 1:]).any():
            raise ValueError("real recurrent rows cannot continue after a terminal")
        if ((self.actions[real] < 0) | (self.actions[real] >= masks.shape[-1])).any():
            raise ValueError("actions outside action vocabulary")
        validate_successor_masks(masks[real], self.dones[real], action_dim=masks.shape[-1])
        if not isinstance(self.sampling, SamplingReceipt) or len(self.sampling.indices) != b:
            raise ValueError("sampling receipt shape must match [B]")
        if not np.array_equal(self.weights.detach().cpu().numpy(), self.sampling.weights):
            raise ValueError("weights must agree with sampling receipt")
        object.__setattr__(self, "sampling", replace(self.sampling))
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Tensor):
                object.__setattr__(self, field.name, value.detach().clone())
