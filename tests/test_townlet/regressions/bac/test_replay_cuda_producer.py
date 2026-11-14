"""Flat/PER producer controls; CUDA hardware qualification is separate.

The constructor sentinel catches eager CUDA access. CPU controls exercise real
storage, sampling and issuer-owned preparation without enabling local policies.
"""

import copy
import hashlib
import json
import multiprocessing
import os
import random
import sys
from collections import OrderedDict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from threading import Event, Thread
from types import MappingProxyType
from typing import Any

import numpy as np
import pytest
import torch

from townlet.exploration.rng_custody import LocalCUDAGate, process_rng_domain
from townlet.training import historical_checkpoint as history
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.replay_contract import PreparedReplay, ReplayPrefix, ReplayRequest, _ReplayPrefixStopError
from townlet.training.state import RewardTensor


class _NoCUDA:
    """Fail on CUDA access, while allowing ordinary object introspection."""

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        raise AssertionError(f"Replay unexpectedly accessed torch.cuda.{name}")


@pytest.fixture(autouse=True)
def preserve_cpu_rng() -> Iterator[None]:
    python_state = random.getstate()
    numpy_state = np.random.get_state()
    torch_state = torch.get_rng_state().clone()
    try:
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        torch.set_rng_state(torch_state)


def _owner(family: str, device: torch.device) -> ReplayBuffer | PrioritizedReplayBuffer:
    if family == "flat":
        return ReplayBuffer(capacity=4, device=device)
    assert family == "per"
    return PrioritizedReplayBuffer(capacity=4, alpha=1.0, beta=0.0, beta_annealing=False, device=device)


def _rows() -> dict[str, torch.Tensor]:
    return {
        "observations": torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]], dtype=torch.float32),
        "actions": torch.tensor([0, 1, 0, 1], dtype=torch.int64),
        "rewards": torch.tensor([10.0, 20.0, 30.0, 40.0], dtype=torch.float32),
        "rewards_extrinsic": torch.tensor([1.0, 2.0, 3.0, 4.0], dtype=torch.float32),
        "rewards_shaping": torch.tensor([0.5, 0.5, 0.5, 0.5], dtype=torch.float32),
        "next_observations": torch.tensor([[1.5, 2.5], [3.5, 4.5], [5.5, 6.5], [7.5, 8.5]], dtype=torch.float32),
        "dones": torch.tensor([False, False, False, True], dtype=torch.bool),
        "next_action_masks": torch.tensor([[True, False], [False, True], [True, True], [False, False]], dtype=torch.bool),
    }


def _push(owner: ReplayBuffer | PrioritizedReplayBuffer, rows: dict[str, torch.Tensor], *, recorded: bool) -> None:
    rewards = RewardTensor(
        rows["rewards"],
        extrinsic=rows["rewards_extrinsic"],
        intrinsic=None,
        shaping=rows["rewards_shaping"],
        is_composed=False,
    )
    arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], rows["dones"])
    if recorded:
        owner.push_recorded(*arguments, rows["next_action_masks"])
    else:
        owner.push(*arguments)


def _request(family: str) -> ReplayRequest:
    mode = "uniform_without_replacement" if family == "flat" else "successive_without_replacement"
    return ReplayRequest(
        batch_size=2,
        sequence_length=1,
        min_transitions=0,
        sampling_mode=mode,
        sequence_mode="feedforward",
        sequence_objective="transition",
    )


def _assert_numpy_state(actual: tuple, expected: tuple) -> None:
    assert actual[0] == expected[0]
    assert np.array_equal(actual[1], expected[1])
    assert actual[2:] == expected[2:]


def _assert_tree_equal(actual: Any, expected: Any) -> None:
    if isinstance(expected, torch.Tensor):
        assert isinstance(actual, torch.Tensor)
        assert actual.dtype == expected.dtype
        assert actual.device == expected.device
        assert torch.equal(actual, expected)
    elif isinstance(expected, np.ndarray):
        assert isinstance(actual, np.ndarray)
        assert actual.dtype == expected.dtype
        assert np.array_equal(actual, expected)
    elif isinstance(expected, dict):
        assert isinstance(actual, dict)
        assert actual.keys() == expected.keys()
        for key, value in expected.items():
            _assert_tree_equal(actual[key], value)
    elif isinstance(expected, (list, tuple)):
        assert type(actual) is type(expected)
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _assert_tree_equal(left, right)
    else:
        assert actual == expected


def _assert_selected_rows(result: dict[str, torch.Tensor], rows: dict[str, torch.Tensor], selected: torch.Tensor) -> None:
    for field in ("observations", "actions", "rewards", "next_observations", "dones", "next_action_masks"):
        assert torch.equal(result[field], rows[field][selected])
    assert torch.equal(result["legality_recorded"], torch.ones(len(selected), dtype=torch.bool))


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("selector", ["cpu", "cuda", "cuda:3"])
def test_empty_constructor_has_no_cuda_access(family: str, selector: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Eager initialization/index validation breaks metadata-only construction."""
    device = torch.device(selector)
    domain = process_rng_domain()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = _owner(family, device)
        assert owner.device is device
        assert len(owner) == 0
        participant = owner.rng_participant
        assert owner.rng_participant is participant
        # The actual domain authenticates this lifetime registration; no fake
        # participant or replacement domain stands in for constructor behavior.
        with domain.device_operation(participant=participant, operation_kind="sample", lineage=None, cuda_devices=()):
            assert owner.device is device


@pytest.mark.parametrize("family", ["flat", "per"])
def test_cpu_local_and_admitted_routes_stay_cuda_free(family: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """CPU storage, actual sampling and current prepare/install need no CUDA."""
    rows = _rows()
    request = _request(family)
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = _owner(family, torch.device("cpu"))
        _push(owner, rows, recorded=True)
        assert len(owner) == owner.retained_transitions == 4
        assert owner.readiness(request).ready
        assert owner.stats()["device"] == "cpu"
        assert owner.historical_archives == ()
        state = owner.serialize()
        for field, expected in rows.items():
            assert torch.equal(state[field], expected)
        assert state["rewards_intrinsic"] is None
        assert torch.equal(state["rewards_extrinsic_present"], torch.ones(4, dtype=torch.bool))
        assert torch.equal(state["rewards_intrinsic_present"], torch.zeros(4, dtype=torch.bool))
        assert torch.equal(state["rewards_shaping_present"], torch.ones(4, dtype=torch.bool))

        validated = owner.validate_serialized(state, expected_obs_dim=2)
        candidate = owner.materialize_validated(validated, lineage=None)
        assert isinstance(candidate, PreparedReplay)
        owner.load_prepared(candidate, lineage=None)
        _assert_tree_equal(owner.serialize(), state)
        candidate = owner.prepare_serialized(state, expected_obs_dim=2, lineage=None)
        owner.load_prepared(candidate, lineage=None)
        _assert_tree_equal(owner.serialize(), state)
        owner.load_for_mode(state, requested_mode="auto", lineage=None)
        _assert_tree_equal(owner.serialize(), state)
        owner.load_from_serialized(state, lineage=None)
        _assert_tree_equal(owner.serialize(), state)

        direct = owner.sample(2, lineage=None)
        selected = ((direct["observations"][:, 0] - 1) / 2).to(torch.int64)
        assert len(torch.unique(selected)) == 2
        _assert_selected_rows(direct, rows, selected)
        batch = owner.sample_batch(request, lineage=None)
        selected = torch.from_numpy(batch.sampling.indices.copy())
        assert len(torch.unique(selected)) == 2
        assert torch.equal(batch.observations, rows["observations"][selected])
        assert torch.equal(batch.rewards, rows["rewards"][selected])
        assert torch.equal(batch.rewards_extrinsic, rows["rewards_extrinsic"][selected])
        assert batch.rewards_intrinsic is None
        assert torch.equal(batch.rewards_shaping, rows["rewards_shaping"][selected])
        assert torch.equal(batch.next_action_masks, rows["next_action_masks"][selected])
        assert torch.equal(batch.loss_mask, torch.ones(2, dtype=torch.bool))
        assert torch.equal(batch.lengths, torch.ones(2, dtype=torch.int64))
        assert torch.equal(batch.weights, torch.ones(2, dtype=torch.float64))

        if isinstance(owner, PrioritizedReplayBuffer):
            configured = np.random.default_rng(812)
            original_generator_state = copy.deepcopy(configured.bit_generator.state)
            owner.configure_sampling(sampling_mode="successive_without_replacement", rng=configured, origin="authored")
            _assert_tree_equal(configured.bit_generator.state, original_generator_state)
            owner.update_priorities(np.array([0, 1], dtype=np.int64), torch.tensor([0.5, 1.5]))
            owner.update_unit_priorities(np.array([0], dtype=np.int64), torch.tensor([0.25]))
            assert owner.serialize()["priorities"][0] == np.float32(0.250001)
            assert owner.serialize()["priorities"][1] == np.float32(1.500001)
            owner.anneal_beta(total_steps=10, current_step=5)
            assert owner.size() == 4

        owner.clear()
        assert len(owner) == 0
        assert not owner.readiness(request).ready
        _push(owner, rows, recorded=False)
        assert len(owner) == 4
        if isinstance(owner, PrioritizedReplayBuffer):
            owner.declare_unconstrained_action_dim(action_dim=2)
            assert owner.readiness(request).ready
            assert torch.equal(owner.serialize()["next_action_masks"], torch.ones((4, 2), dtype=torch.bool))
        else:
            assert not owner.readiness(request).ready
        direct = owner.sample(2, lineage=None)
        assert direct["observations"].shape == (2, 2)
        owner.clear()
        assert len(owner) == 0


@pytest.mark.parametrize("adapter", ["direct", "batch"])
def test_flat_sampling_preserves_selected_cpu_torch_stream(adapter: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A NumPy law or a private/reseeded Torch draw changes rows/continuation."""
    rows = _rows()
    torch.random.default_generator.manual_seed(29)
    oracle = torch.Generator(device="cpu")
    oracle.set_state(torch.get_rng_state())
    expected_indices = torch.randperm(4, generator=oracle)[:2]
    numpy_before = np.random.get_state()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = _owner("flat", torch.device("cpu"))
        _push(owner, rows, recorded=True)
        if adapter == "direct":
            result = owner.sample(2, lineage=None)
            _assert_selected_rows(result, rows, expected_indices)
        else:
            batch = owner.sample_batch(_request("flat"), lineage=None)
            assert torch.equal(batch.observations, rows["observations"][expected_indices])
            assert np.array_equal(batch.sampling.indices, expected_indices.numpy())
            assert np.array_equal(batch.sampling.conditional_draw_probabilities, np.array([0.25, 1.0 / 3.0]))
        assert torch.equal(torch.get_rng_state(), oracle.get_state())
        _assert_numpy_state(np.random.get_state(), numpy_before)


def test_per_direct_retains_vectorized_global_law_with_owned_sampler(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configuring owned sampling must not reroute the public direct adapter."""
    rows = _rows()
    np.random.seed(113)
    oracle = np.random.RandomState()
    oracle.set_state(np.random.get_state())
    expected_indices = oracle.choice(4, 2, p=np.array([0.25, 0.25, 0.25, 0.25]), replace=False)
    torch_before = torch.get_rng_state().clone()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = PrioritizedReplayBuffer(capacity=4, alpha=1.0, beta=0.0, beta_annealing=False, device=torch.device("cpu"))
        _push(owner, rows, recorded=True)
        owner.configure_sampling(sampling_mode="successive_without_replacement", rng=np.random.default_rng(81), origin="authored")
        sampler_before = owner.serialize()["sampling_rng"]
        result = owner.sample(2, lineage=None)
        assert np.array_equal(result["indices"], expected_indices)
        assert torch.equal(result["weights"], torch.ones(2, dtype=torch.float32))
        _assert_selected_rows(result, rows, torch.from_numpy(expected_indices))
        _assert_tree_equal(owner.serialize()["sampling_rng"], sampler_before)
        _assert_numpy_state(np.random.get_state(), oracle.get_state())
        assert torch.equal(torch.get_rng_state(), torch_before)


def test_per_batch_external_sampler_retains_vectorized_global_law(monkeypatch: pytest.MonkeyPatch) -> None:
    """The qualified external sampler keeps the actual vectorized NumPy law."""
    rows = _rows()
    np.random.seed(307)
    oracle = np.random.RandomState()
    oracle.set_state(np.random.get_state())
    expected_indices = oracle.choice(4, 2, p=np.array([0.25, 0.25, 0.25, 0.25]), replace=False)
    torch_before = torch.get_rng_state().clone()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = _owner("per", torch.device("cpu"))
        _push(owner, rows, recorded=True)
        batch = owner.sample_batch(_request("per"), lineage=None)
        assert np.array_equal(batch.sampling.indices, expected_indices)
        assert torch.equal(batch.observations, rows["observations"][torch.from_numpy(expected_indices)])
        assert torch.equal(batch.weights, torch.ones(2, dtype=torch.float64))
        _assert_numpy_state(np.random.get_state(), oracle.get_state())
        assert torch.equal(torch.get_rng_state(), torch_before)


def test_per_batch_owned_sampler_retains_residual_draw_law(monkeypatch: pytest.MonkeyPatch) -> None:
    """Qualified owned successive sampling draws once per residual support."""
    rows = _rows()
    configured = np.random.default_rng(919)
    configured_before = copy.deepcopy(configured.bit_generator.state)
    oracle = np.random.default_rng(919)
    first = int(oracle.choice(np.array([0, 1, 2, 3]), p=np.array([0.25, 0.25, 0.25, 0.25]), replace=False))
    remaining = np.array([index for index in (0, 1, 2, 3) if index != first])
    second = int(oracle.choice(remaining, p=np.array([1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]), replace=False))
    expected_indices = np.array([first, second], dtype=np.int64)
    numpy_before = np.random.get_state()
    torch_before = torch.get_rng_state().clone()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        owner = PrioritizedReplayBuffer(capacity=4, alpha=1.0, beta=0.0, beta_annealing=False, device=torch.device("cpu"))
        _push(owner, rows, recorded=True)
        owner.configure_sampling(sampling_mode="successive_without_replacement", rng=configured, origin="authored")
        batch = owner.sample_batch(_request("per"), lineage=None)
        assert np.array_equal(batch.sampling.indices, expected_indices)
        assert np.array_equal(batch.sampling.conditional_draw_probabilities, np.array([0.25, 1.0 / 3.0]))
        assert torch.equal(batch.unit_ids, torch.from_numpy(expected_indices))
        assert torch.equal(batch.observations, rows["observations"][torch.from_numpy(expected_indices)])
        assert torch.equal(batch.weights, torch.ones(2, dtype=torch.float64))
        _assert_tree_equal(owner.serialize()["sampling_rng"]["state"], oracle.bit_generator.state)
        _assert_tree_equal(configured.bit_generator.state, configured_before)
        _assert_numpy_state(np.random.get_state(), numpy_before)
        assert torch.equal(torch.get_rng_state(), torch_before)


class _SimCUDA:
    """Initialized finite CPU protocol stand-in; never GPU qualification."""

    def __init__(self) -> None:
        self.selected = 0
        self.events: list[tuple] = []
        self.depth = 0
        self.on_sync: Callable[[int], None] = lambda index: None
        self.after_tensor: Callable[[str, tuple[int, ...], Any], None] = lambda name, devices, result: None

    def is_initialized(self) -> bool:
        self.events.append(("initialized",))
        return True

    def device_count(self) -> int:
        self.events.append(("count",))
        return 5

    def init(self) -> None:
        raise AssertionError("Initialized protocol fixture must not bootstrap")

    def current_device(self) -> int:
        self.events.append(("current", self.selected))
        return self.selected

    def synchronize(self, index: int) -> None:
        self.events.append(("sync", index))
        self.on_sync(index)

    def work(self, name: str, devices: tuple[int, ...]) -> None:
        self.events.append(("work", name, devices, self.depth > 0))


def _map_values(value: Any, transform: Callable[[torch.Tensor], Any]) -> Any:
    if isinstance(value, torch.Tensor):
        return transform(value)
    if isinstance(value, tuple):
        return tuple(_map_values(item, transform) for item in value)
    if isinstance(value, list):
        return [_map_values(item, transform) for item in value]
    if isinstance(value, dict):
        return {key: _map_values(item, transform) for key, item in value.items()}
    return value


class _CUDAData(torch.Tensor):
    """Real CPU tensor storage with explicit simulated CUDA device metadata."""

    runtime: _SimCUDA | None = None

    @staticmethod
    def __new__(cls, value: torch.Tensor, index: int) -> "_CUDAData":
        with torch._C.DisableTorchFunctionSubclass():
            result = torch.Tensor._make_subclass(cls, value, False)
        result.index = index
        return result

    def plain(self) -> torch.Tensor:
        with torch._C.DisableTorchFunctionSubclass():
            return self.as_subclass(torch.Tensor)

    @property
    def device(self) -> torch.device:
        return torch.device("cuda", self.index)

    def cpu(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        assert self.runtime is not None
        self.runtime.work("cpu", (self.index,))
        return self.plain().cpu(*args, **kwargs)

    @classmethod
    def __torch_function__(cls, func: Any, types: Any, args: tuple = (), kwargs: Any = None) -> Any:
        # Torch's callback convention omits kwargs for some C Tensor methods.
        # These required upstream hook defaults are test-only; production's
        # no-defaults gate targets src/townlet, not this protocol adapter.
        arguments = {} if kwargs is None else kwargs
        devices: set[int] = set()

        def unwrap(value: torch.Tensor) -> torch.Tensor:
            if isinstance(value, _CUDAData):
                devices.add(value.index)
                return value.plain()
            return value

        plain_args = _map_values(args, unwrap)
        plain_kwargs = _map_values(arguments, unwrap)
        assert cls.runtime is not None
        name = func.__name__
        if name != "__get__":
            cls.runtime.work(name, tuple(sorted(devices)))
        with torch._C.DisableTorchFunctionSubclass():
            result = func(*plain_args, **plain_kwargs)
        if name != "__get__":
            cls.runtime.events.append(("finished", name, tuple(sorted(devices))))
            cls.runtime.after_tensor(name, tuple(sorted(devices)), result)
        if not devices:
            return result
        index = min(devices)
        return _map_values(result, lambda value: _CUDAData(value, index))


@contextmanager
def _cuda_simulation(monkeypatch: pytest.MonkeyPatch) -> Iterator[_SimCUDA]:
    """Redirect allocation/movement only; actual producer algorithms remain."""
    runtime = _SimCUDA()
    _CUDAData.runtime = runtime
    real_to = torch.Tensor.to
    real_complete = LocalCUDAGate.complete

    def transfer(value: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        positional = list(args)
        target = kwargs.get("device")
        if positional and isinstance(positional[0], (str, torch.device)):
            target = positional[0]
        device = None if target is None else torch.device(target)
        original_index = value.index if isinstance(value, _CUDAData) else None
        plain = value.plain() if isinstance(value, _CUDAData) else value
        if original_index is not None:
            runtime.work("to", (original_index,))
        if device is not None:
            if positional and isinstance(positional[0], (str, torch.device)):
                positional[0] = torch.device("cpu")
            else:
                kwargs["device"] = torch.device("cpu")
        result = real_to(plain, *positional, **kwargs)
        if device is not None and device.type == "cuda":
            index = runtime.selected if device.index is None else device.index
            runtime.work("to_destination", (index,))
            return _CUDAData(result, index)
        return _CUDAData(result, original_index) if device is None and original_index is not None else result

    def allocator(name: str, original: Callable[..., torch.Tensor]) -> Callable[..., torch.Tensor]:
        def allocate(*args: Any, **kwargs: Any) -> torch.Tensor:
            device = torch.device(kwargs["device"]) if "device" in kwargs else None
            if device is None or device.type != "cuda":
                return original(*args, **kwargs)
            index = runtime.selected if device.index is None else device.index
            runtime.work(name, (index,))
            return _CUDAData(original(*args, **{**kwargs, "device": torch.device("cpu")}), index)

        return allocate

    @contextmanager
    def complete(gate: LocalCUDAGate, *, cuda_devices: tuple[int, ...]) -> Iterator[None]:
        # Observe the real public method; no manifest, permission or gate issuer
        # is replaced. The arm event follows authentic tuple validation.
        with real_complete(gate, cuda_devices=cuda_devices):
            runtime.events.append(("arm", cuda_devices))
            runtime.depth += 1
            try:
                yield
            finally:
                runtime.depth -= 1

    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", runtime)
        scoped.setattr(torch.Tensor, "to", transfer)
        scoped.setattr(LocalCUDAGate, "complete", complete)
        for name in ("zeros", "ones", "full", "arange", "tensor", "randperm"):
            scoped.setattr(torch, name, allocator(name, getattr(torch, name)))
        try:
            yield runtime
        finally:
            _CUDAData.runtime = None


@pytest.fixture
def simulated_cuda(monkeypatch: pytest.MonkeyPatch) -> Iterator[_SimCUDA]:
    with _cuda_simulation(monkeypatch) as runtime:
        yield runtime


def _syncs(events: list[tuple]) -> tuple[int, ...]:
    return tuple(event[1] for event in events if event[0] == "sync")


def _assert_local(events: list[tuple], devices: tuple[int, ...]) -> None:
    assert [event[1] for event in events if event[0] == "arm"] == [devices]
    assert _syncs(events) == devices
    assert all(event[3] for event in events if event[0] == "work"), "Tensor work began before authentic completion arming"


@pytest.mark.parametrize("family", ["flat", "per"])
def test_simulated_fixture_runs_real_producer_values(family: str, simulated_cuda: _SimCUDA) -> None:
    """Positive prerequisite: initialized indexed setup reaches real algorithms."""
    rows = _rows()
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, rows, recorded=True)
    assert owner.observations is not None and owner.observations.device == torch.device("cuda:0")
    assert torch.equal(owner.observations.cpu(), rows["observations"])
    assert owner.readiness(_request(family)).ready
    result = owner.sample(2, lineage=None)
    positions = ((result["observations"].cpu()[:, 0] - 1) / 2).to(torch.int64)
    assert len(torch.unique(positions)) == 2
    assert torch.equal(result["rewards"].cpu(), rows["rewards"][positions])
    state = owner.serialize()
    validated = owner.validate_serialized(state, expected_obs_dim=2)
    candidate = owner.materialize_validated(validated, lineage=None)
    owner.load_prepared(candidate, lineage=None)
    _assert_tree_equal(owner.serialize(), state)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_dynamic_selector_resolves_each_real_push(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    selector = torch.device("cuda")
    owner.device = selector
    for index in (0, 1):
        owner.clear()
        simulated_cuda.selected = index
        simulated_cuda.events.clear()
        _push(owner, _rows(), recorded=True)
        events = list(simulated_cuda.events)
        assert owner.device is selector
        assert owner.observations is not None and owner.observations.device == torch.device("cuda", index)
        assert torch.equal(owner.observations.cpu(), _rows()["observations"])
        assert [event for event in events if event[0] == "current"] == [("current", index)]
        _assert_local(events, (index,))


@pytest.mark.parametrize("family", ["flat", "per"])
def test_push_inventories_retained_secondary_source_and_destination(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    owner.device = torch.device("cuda:1")
    rows = _rows()
    rows["observations"] += 10
    rows["next_observations"] += 10
    rows["rewards_shaping"] = _CUDAData(rows["rewards_shaping"], 2)
    simulated_cuda.events.clear()
    _push(owner, rows, recorded=True)
    events = list(simulated_cuda.events)
    assert owner.observations is not None and owner.observations.device == torch.device("cuda:0")
    assert torch.equal(owner.observations.cpu(), rows["observations"])
    _assert_local(events, (0, 1, 2))


@pytest.mark.parametrize("family", ["flat", "per"])
def test_install_inventories_issuer_material_without_selector_migration(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    state = owner.serialize()
    owner.device = torch.device("cuda:1")
    with owner.cuda_preflight(anticipated_devices=(torch.device("cuda:0"), torch.device("cuda:1"))):
        candidate = owner.prepare_serialized(state, expected_obs_dim=2, lineage=None)
        owner.device = torch.device("cuda:2")
        simulated_cuda.events.clear()
        owner.load_prepared(candidate, lineage=None)
        events = list(simulated_cuda.events)
    assert owner.observations is not None and owner.observations.device == torch.device("cuda:1")
    _assert_tree_equal(owner.serialize(), state)
    assert _syncs(events) == (0, 1)
    assert not any(event[0] == "current" for event in events)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_released_preparation_refuses_late_membership_enrollment(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    live_observations = owner.observations
    owner.device = torch.device("cuda:1")
    candidate = owner.prepare_serialized(before, expected_obs_dim=2, lineage=None)
    # Local push/read did not enroll live0; prepare enrolled only candidate1.
    # Expand real idle membership after issuance without changing owner revision
    # or performing ordinary work that could mask the original-token diagnosis.
    with process_rng_domain().admission(lineage=None) as gate:
        gate.enroll(participant=owner.rng_participant, cuda_devices=(0,))
    owner.device = torch.device("cuda:2")
    simulated_cuda.events.clear()
    with pytest.raises(ValueError, match="^RNG preparation membership changed$"):
        owner.load_prepared(candidate, lineage=None)
    events = list(simulated_cuda.events)
    assert owner.observations is live_observations
    assert owner.observations is not None and owner.observations.device == torch.device("cuda:0")
    _assert_tree_equal(owner.serialize(), before)
    assert _syncs(events) == (0, 1)
    clones = [position for position, event in enumerate(events) if event[:3] == ("finished", "clone", (1,))]
    assert clones and max(clones) < next(position for position, event in enumerate(events) if event[0] == "sync")
    assert not any(event[0] == "current" for event in events)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_empty_prepare_install_ignores_unused_cuda_selector(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    state = owner.serialize()
    owner.device = torch.device("cuda:3")
    simulated_cuda.events.clear()
    candidate = owner.prepare_serialized(state, expected_obs_dim=None, lineage=None)
    owner.load_prepared(candidate, lineage=None)
    assert simulated_cuda.events == []
    assert len(owner) == 0


def _legacy_transport(family: str) -> dict[str, Any]:
    rows = _rows()
    fields = {name: value for name, value in rows.items() if name != "next_action_masks"}
    fields["rewards_intrinsic"] = torch.zeros(4, dtype=torch.float32)
    if family == "flat":
        legacy = {"replay_kind": "standard", "format_version": 4, "capacity": 4, "size": 4, "position": 0, **fields}
    else:
        legacy = {
            "replay_kind": "prioritized",
            "format_version": 4,
            "capacity": 4,
            "alpha": 1.0,
            "beta": 0.0,
            "beta_initial": 0.0,
            "beta_annealing": False,
            "priorities": np.ones(4, dtype=np.float32),
            "max_priority": 1.0,
            "position": 0,
            "size_current": 4,
            **fields,
        }
    return legacy


@pytest.mark.parametrize("family", ["flat", "per"])
def test_archive_only_prepare_install_keeps_unused_target_lazy(family: str, simulated_cuda: _SimCUDA) -> None:
    legacy = _legacy_transport(family)
    owner = _owner(family, torch.device("cuda:0"))
    owner.device = torch.device("cuda:3")
    simulated_cuda.events.clear()
    candidate = owner.prepare_serialized(legacy, expected_obs_dim=2, lineage=None)
    owner.load_prepared(candidate, lineage=None)
    assert simulated_cuda.events == []
    assert len(owner) == 0
    assert owner.historical_archives[0].archived_row_count == 4


@pytest.mark.parametrize("matching", [False, True])
def test_per_declaration_distinguishes_allocating_and_noop_branches(matching: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner("per", torch.device("cuda:0"))
    assert isinstance(owner, PrioritizedReplayBuffer)
    if matching:
        owner.declare_unconstrained_action_dim(action_dim=2)
        owner.device = torch.device("cuda:3")
    simulated_cuda.events.clear()
    owner.declare_unconstrained_action_dim(action_dim=2)
    events = list(simulated_cuda.events)
    assert owner.action_dim == 2
    if matching:
        assert events == []
    else:
        assert owner.next_action_masks is not None and tuple(owner.next_action_masks.shape) == (4, 2)
        _assert_local(events, (0,))


@pytest.mark.parametrize("family", ["flat", "per"])
def test_zero_push_inventories_secondary_validation_without_target_allocation(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    owner.device = torch.device("cuda:3")
    rows = {name: value[:0] for name, value in _rows().items()}
    rows["rewards_shaping"] = _CUDAData(rows["rewards_shaping"], 2)
    simulated_cuda.events.clear()
    _push(owner, rows, recorded=True)
    events = list(simulated_cuda.events)
    assert len(owner) == 0 and owner.observations is None
    _assert_local(events, (2,))
    assert not any(event[0] == "current" for event in events)


@pytest.mark.parametrize("stable", [False, True])
@pytest.mark.parametrize("cuda_input", [False, True])
def test_priority_update_uses_actual_error_source(stable: bool, cuda_input: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner("per", torch.device("cpu") if cuda_input else torch.device("cuda:0"))
    assert isinstance(owner, PrioritizedReplayBuffer)
    _push(owner, _rows(), recorded=True)
    errors = torch.tensor([0.5])
    if cuda_input:
        errors = _CUDAData(errors, 2)
    update = owner.update_unit_priorities if stable else owner.update_priorities
    simulated_cuda.events.clear()
    update(np.array([0], dtype=np.int64), errors)
    events = list(simulated_cuda.events)
    assert owner.priorities[0] == np.float32(0.500001)
    if cuda_input:
        _assert_local(events, (2,))
    else:
        assert events == []
    before = owner.priorities.copy()
    with pytest.raises(ValueError):
        update(np.array([999], dtype=np.int64), torch.tensor([0.5]))
    assert np.array_equal(owner.priorities, before)
    with pytest.raises(ValueError):
        update(np.array([0], dtype=np.int64), torch.tensor([0.5, 0.75]))
    owner.clear()  # Clean validation failures do not quarantine this owner.


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("route", ["readiness", "serialize"])
def test_read_routes_inventory_accessed_fields_not_selector(family: str, route: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    owner.legality_recorded = _CUDAData(torch.ones(4, dtype=torch.bool), 2)
    owner.device = torch.device("cuda:3")
    simulated_cuda.events.clear()
    result = owner.readiness(_request(family)) if route == "readiness" else owner.serialize()
    events = list(simulated_cuda.events)
    assert result.ready if route == "readiness" else torch.equal(result["observations"], _rows()["observations"])
    _assert_local(events, (2,) if route == "readiness" else (0, 2))
    assert not any(event[0] == "current" for event in events)


def _archive_on(index: int) -> history.HistoricalReplayArchive:
    return _family_archive("flat", index)


def _family_archive(family: str, index: int) -> history.HistoricalReplayArchive:
    legacy = _legacy_transport(family)
    values = {name: _CUDAData(value, index) if isinstance(value, torch.Tensor) else value for name, value in legacy.items()}
    return history.archive_standalone_replay(values)


def test_archive_fixture_owns_real_rows_before_observation(simulated_cuda: _SimCUDA) -> None:
    archive = _archive_on(3)
    assert archive.archived_row_count == 4
    assert torch.equal(archive.query_rows(offset=0, limit=4)["observations"].cpu(), _rows()["observations"])
    assert archive.original_state["observations"].device == torch.device("cuda:3")


def test_archive_inventory_precedes_clone_on_read(simulated_cuda: _SimCUDA) -> None:
    archive = _archive_on(3)  # Legitimate owning construction before observation.
    owner = _owner("flat", torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    owner.device = torch.device("cuda:1")
    simulated_cuda.events.clear()
    owner.install_historical_archive(archive)
    events = list(simulated_cuda.events)
    assert owner.historical_archives[0].source_digest == archive.source_digest
    _assert_local(events, (3,))


def _competing_clear(owner: ReplayBuffer | PrioritizedReplayBuffer) -> tuple[Thread, Event, Event, list[BaseException]]:
    attempted, finished = Event(), Event()
    errors: list[BaseException] = []

    def mutate() -> None:
        attempted.set()
        try:
            owner.clear()
        except BaseException as error:
            errors.append(error)
        finally:
            finished.set()

    return Thread(target=mutate), attempted, finished, errors


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("body_error", [False, True])
def test_completion_keeps_actual_mutation_excluded(family: str, local: bool, body_error: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    reached, release = Event(), Event()
    started_work = Event()
    outcomes: list[BaseException] = []
    primary = ValueError("controlled failure after a real selected-row tensor operation")

    def synchronize(index: int) -> None:
        reached.set()
        release.wait(5)

    simulated_cuda.on_sync = synchronize

    def after_tensor(name: str, devices: tuple[int, ...], result: Any) -> None:
        if name == "__getitem__" and devices == (0,) and isinstance(result, torch.Tensor) and result.shape == (2, 2):
            started_work.set()
            raise primary

    if body_error and not local:
        simulated_cuda.after_tensor = after_tensor

    def run() -> None:
        try:
            if local:
                if body_error:
                    rows = _rows()
                    rows["next_action_masks"][0].fill_(False)
                    rows["next_action_masks"] = _CUDAData(rows["next_action_masks"], 0)
                    rows["dones"] = _CUDAData(rows["dones"], 0)
                    _push(owner, rows, recorded=True)
                else:
                    owner.serialize()
            else:
                owner.sample(2, lineage=None)
        except BaseException as error:
            outcomes.append(error)

    worker = Thread(target=run)
    competitor, attempted, finished, competitor_errors = _competing_clear(owner)
    worker.start()
    try:
        assert reached.wait(2), "Actual producer never reached CUDA completion"
        if body_error and not local:
            assert started_work.is_set(), "Body failure preceded the genuine selected-row tensor operation"
        competitor.start()
        assert attempted.wait(2), "Competitor did not attempt its actual clear"
        assert not finished.wait(0.1), "Owner was released before completion"
    finally:
        release.set()
        worker.join(5)
        if competitor.ident is not None:
            competitor.join(5)
    assert not worker.is_alive() and not competitor.is_alive()
    assert not competitor_errors
    assert len(outcomes) == int(body_error)
    if body_error:
        assert isinstance(outcomes[0], ValueError)
        if not local:
            assert outcomes[0] is primary
    owner.clear()  # Successful completion preserves usability after body errors.


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("local", [False, True])
def test_clean_body_error_keeps_identity_and_owner_health(
    family: str, local: bool, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    primary = ValueError("controlled external tensor/sampler body failure")

    def fail(*args: Any, **kwargs: Any) -> Any:
        raise primary

    with monkeypatch.context() as scoped:
        if local:
            scoped.setattr(torch, "isfinite", fail)
        elif family == "flat":
            scoped.setattr(torch, "randperm", fail)
        else:
            scoped.setattr(np.random, "choice", fail)
        simulated_cuda.events.clear()
        with pytest.raises(ValueError) as caught:
            if local:
                rows = _rows()
                rows["observations"] = _CUDAData(rows["observations"], 0)
                _push(owner, rows, recorded=True)
            else:
                owner.sample(2, lineage=None)
        events = list(simulated_cuda.events)
    assert caught.value is primary
    _assert_tree_equal(owner.serialize(), before)
    owner.clear()
    if local:
        _assert_local(events, (0,))
    else:
        assert _syncs(events) == (0,)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("changed_destination", [False, True])
def test_failed_preparation_keeps_live_data_and_original_streams(family: str, changed_destination: bool) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    validated = owner.validate_serialized(owner.serialize(), expected_obs_dim=2)
    if changed_destination:
        owner.clear()
        rows = _rows()
        rows["observations"] = torch.cat((rows["observations"], torch.ones((4, 1))), dim=1)
        rows["next_observations"] = torch.cat((rows["next_observations"], torch.ones((4, 1))), dim=1)
        _push(owner, rows, recorded=True)
    else:
        validated.next_action_masks[0].fill_(False)
    before = owner.serialize()
    python_before, numpy_before, torch_before = random.getstate(), np.random.get_state(), torch.get_rng_state().clone()
    with pytest.raises(ValueError):
        owner.materialize_validated(validated, lineage=None)
    _assert_tree_equal(owner.serialize(), before)
    assert random.getstate() == python_before
    _assert_numpy_state(np.random.get_state(), numpy_before)
    assert torch.equal(torch.get_rng_state(), torch_before)
    fresh = owner.prepare_serialized(before, expected_obs_dim=3 if changed_destination else 2, lineage=None)
    owner.load_prepared(fresh, lineage=None)
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("mutate", [False, True])
def test_same_parent_owner_revision_is_independent_of_core_currentness(family: str, mutate: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    state = owner.serialize()
    domain = process_rng_domain()
    with domain.operation(participant=owner.rng_participant, operation_kind="prepare", lineage=None) as parent:
        candidate = owner.prepare_serialized(state, expected_obs_dim=2, lineage=parent)
        probe = domain.current_token(participant=owner.rng_participant, operation=parent)
        with domain.admission(lineage=parent) as gate:
            assert gate.resolve_cuda(torch.device("cuda:0")) == 0
        owner.stats()
        if mutate:
            owner.clear()
        domain.validate_current(token=probe, operation=parent)
        if mutate:
            with pytest.raises(ValueError, match="destination changed"):
                owner.load_prepared(candidate, lineage=parent)
        else:
            owner.load_prepared(candidate, lineage=parent)
            _assert_tree_equal(owner.serialize(), state)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_preflight_retains_exclusion_through_parent_completion(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    competitor, attempted, finished, errors = _competing_clear(owner)
    observed: list[tuple[int, bool]] = []
    try:
        with owner.cuda_preflight(anticipated_devices=(torch.device("cuda:0"), torch.device("cuda:1"))):
            with process_rng_domain().operation(participant=owner.rng_participant, operation_kind="sample", lineage=None) as parent:
                owner.device = torch.device("cuda")
                simulated_cuda.selected = 1
                simulated_cuda.events.clear()
                result = owner.sample(2, lineage=parent)
                nested = list(simulated_cuda.events)
                assert result["observations"].shape == (2, 2)
                assert owner.observations is not None and owner.observations.device == torch.device("cuda:0")
                selected_output = result["mask"] if family == "flat" else result["weights"]
                assert selected_output.device == torch.device("cuda:1")
                assert [event for event in nested if event[0] == "current"] == [("current", 1)]
                assert any(event[:3] == ("work", "randperm" if family == "flat" else "tensor", (1,)) for event in nested)
                assert _syncs(nested) == (0, 1)
                competitor.start()
                assert attempted.wait(2)
                assert not finished.wait(0.1)
                simulated_cuda.on_sync = lambda index: observed.append((index, finished.is_set()))
                simulated_cuda.events.clear()
            outer = list(simulated_cuda.events)
            assert _syncs(outer) == (0, 1)
            assert not finished.is_set()
    finally:
        if competitor.ident is not None:
            competitor.join(5)
    assert not competitor.is_alive() and not errors
    assert finished.is_set()
    assert observed and all(not was_finished for _, was_finished in observed)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_sibling_sampling_stales_core_currency_without_target_mutation(family: str) -> None:
    owner = _owner(family, torch.device("cpu"))
    sibling = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    _push(sibling, _rows(), recorded=True)
    state = owner.serialize()
    with process_rng_domain().operation(participant=owner.rng_participant, operation_kind="install", lineage=None) as parent:
        candidate = owner.prepare_serialized(state, expected_obs_dim=2, lineage=parent)
        sibling.sample(2, lineage=parent)
        with pytest.raises((ValueError, RuntimeError)):
            owner.load_prepared(candidate, lineage=parent)
        _assert_tree_equal(owner.serialize(), state)
        fresh = owner.prepare_serialized(state, expected_obs_dim=2, lineage=parent)
        owner.load_prepared(fresh, lineage=parent)
    _assert_tree_equal(owner.serialize(), state)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_preflight_undeclared_target_refuses_before_draw_or_data_effect(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    with owner.cuda_preflight(anticipated_devices=(torch.device("cuda:0"),)):
        with process_rng_domain().operation(participant=owner.rng_participant, operation_kind="sample", lineage=None) as parent:
            owner.device = torch.device("cuda:4")
            numpy_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
            with pytest.raises(RuntimeError, match="preflight"):
                owner.sample(2, lineage=parent)
            _assert_numpy_state(np.random.get_state(), numpy_before)
            assert torch.equal(torch.get_rng_state(), torch_before)
    _assert_tree_equal(owner.serialize(), before)


def _assert_cloned_then_completed(events: list[tuple], devices: tuple[int, ...]) -> None:
    for index in devices:
        assert any(event[:2] == ("finished", "clone") and index in event[2] for event in events)
    assert _syncs(events) == devices
    first_completion = next(position for position, event in enumerate(events) if event[0] == "sync")
    assert all(
        position < first_completion
        for position, event in enumerate(events)
        if event[:2] == ("finished", "clone") and any(index in event[2] for index in devices)
    )


def test_per_archive_fixture_preserves_real_legacy_rows(simulated_cuda: _SimCUDA) -> None:
    archive = _family_archive("per", 3)
    assert archive.archived_row_count == 4
    assert archive.source_formats["replay_kind"] == "prioritized"
    assert torch.equal(archive.query_rows(offset=0, limit=4)["observations"].cpu(), _rows()["observations"])


@pytest.mark.parametrize("family", ["flat", "per"])
def test_mutated_legacy_dto_clones_extra_gpu_value_before_schema_refusal(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    validated = owner.validate_serialized(_legacy_transport(family), expected_obs_dim=2)
    assert isinstance(validated.legacy_state, dict)
    validated.legacy_state["malformed_extra"] = _CUDAData(torch.tensor([7.0]), 3)
    before = owner.serialize()
    python_before, numpy_before, torch_before = random.getstate(), np.random.get_state(), torch.get_rng_state().clone()
    simulated_cuda.events.clear()
    with pytest.raises(ValueError, match="key set mismatch"):
        owner.materialize_validated(validated, lineage=None)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    assert random.getstate() == python_before
    _assert_numpy_state(np.random.get_state(), numpy_before)
    assert torch.equal(torch.get_rng_state(), torch_before)
    _assert_cloned_then_completed(events, (3,))


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("prepare", [False, True])
def test_direct_extra_transport_key_refuses_without_touching_gpu_value(family: str, prepare: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    transport = {**before, "malformed_extra": _CUDAData(torch.tensor([7.0]), 3)}
    owner.device = torch.device("cuda:4")  # Unused destination must remain lazy.
    simulated_cuda.events.clear()
    with pytest.raises(ValueError, match="key set mismatch"):
        if prepare:
            owner.prepare_serialized(transport, expected_obs_dim=2, lineage=None)
        else:
            owner.validate_serialized(transport, expected_obs_dim=2)
    assert simulated_cuda.events == []
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("with_archive", [False, True])
def test_stale_gpu_candidate_stages_sources_before_currentness_refusal(family: str, with_archive: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cuda:0"))
    _push(owner, _rows(), recorded=True)
    transport = owner.serialize()
    if with_archive:
        transport["historical_archives"] = [history._record(_family_archive(family, 3))]
    owner.device = torch.device("cuda:1")
    candidate = owner.prepare_serialized(transport, expected_obs_dim=2, lineage=None)
    owner.clear()  # Invalidates owner revision; issuer-held GPU material survives.
    owner.device = torch.device("cuda:4")
    before = owner.serialize()
    simulated_cuda.events.clear()
    with pytest.raises(ValueError, match="destination changed"):
        owner.load_prepared(candidate, lineage=None)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    _assert_cloned_then_completed(events, (1, 3) if with_archive else (1,))


@pytest.mark.parametrize("family", ["flat", "per"])
def test_archive_original_state_clone_precedes_nested_content_refusal(family: str, simulated_cuda: _SimCUDA) -> None:
    record = history._record(_family_archive(family, 3))
    assert set(record) == {
        "source_formats",
        "original_state",
        "source_digest",
        "archived_row_count",
        "reward_semantics",
        "approval_reference",
    }
    record["original_state"]["malformed_extra"] = _CUDAData(torch.tensor([7.0]), 4)
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    transport = {**before, "historical_archives": [record]}
    simulated_cuda.events.clear()
    with pytest.raises(ValueError):
        owner.validate_serialized(transport, expected_obs_dim=2)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    _assert_local(events, (3, 4))
    _assert_cloned_then_completed(events, (3, 4))


_PRODUCER_ROLE = "cuda_producer_poison"
_PRODUCER_CASES = tuple(
    f"{family}_{schedule}"
    for family in ("flat", "per")
    for schedule in ("local_single", "local_distinct", "local_same", "admitted_single", "admitted_same")
)


def _poison_json(stem: str, record: dict[str, Any]) -> None:
    if "BAC_QUAL_OUTPUT" in os.environ:
        with (Path(os.environ["BAC_QUAL_OUTPUT"]) / f"{stem}-{_PRODUCER_ROLE}.json").open("x") as stream:
            json.dump(record, stream, sort_keys=True, allow_nan=False)


def _error_record(error: BaseException) -> dict[str, Any]:
    return {
        "type": type(error).__name__,
        "message": str(error),
        "id": id(error),
        "children": [_error_record(item) for item in error.exceptions] if isinstance(error, BaseExceptionGroup) else [],
    }


def _producer_child_identity(case: str) -> bool:
    import test_world_rng_bootstrap as bootstrap

    qualified = bootstrap._child_identity(_PRODUCER_ROLE)
    if qualified:
        location = Path(os.environ["BAC_QUAL_OUTPUT"]) / f"spawn-identity-{_PRODUCER_ROLE}.json"
        record = json.loads(location.read_text())
        names = (
            "townlet.exploration.rng_custody",
            "townlet.training.replay_contract",
            "townlet.training.replay_buffer",
            "townlet.training.prioritized_replay_buffer",
            "test_replay_cuda_producer",
        )
        imports = {name: str(Path(sys.modules[name].__file__).resolve()) for name in names}
        record.update(
            ppid=os.getppid(),
            producer_case=case,
            cuda_producer_imports=imports,
            cuda_producer_sha256={name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for name, path in imports.items()},
        )
        location.write_text(json.dumps(record, sort_keys=True, allow_nan=False))
    return qualified


def _producer_poison_child(case: str, queue: Any) -> None:
    qualified = _producer_child_identity(case)
    assert case in _PRODUCER_CASES
    family, schedule = case.split("_", 1)
    local, body_error = schedule.startswith("local"), schedule.endswith(("distinct", "same"))
    body = ValueError(f"{case}: body") if body_error else None
    first = body if schedule.endswith("same") else RuntimeError(f"{case}: completion0")
    second = OSError(f"{case}: completion1") if schedule == "local_distinct" else None
    domain = process_rng_domain()
    identity = {"case": case, "pid": os.getpid(), "ppid": os.getppid(), "qualified": qualified}
    before = {
        "domain": list(domain.status()),
        "devices": [0, 1],
        "error_ids": [id(body) if body else None, id(first), id(second) if second else None],
    }
    _poison_json("spawn-preflight", {**identity, "before": before})
    phase, success = "preflight", False
    observations: dict[str, Any] = {}
    failure = None
    try:
        core = sys.modules["townlet.exploration.rng_custody"]
        getattr(core, "REPLAY_BUFFER_SERIALIZE_CUDA" if family == "flat" else "PRIORITIZED_REPLAY_BUFFER_SERIALIZE_CUDA")
        if not local:
            getattr(domain, "device_invocation")  # Availability is not an authentic outcome or a successful poisoning assertion.
        with pytest.MonkeyPatch.context() as patch, _cuda_simulation(patch) as runtime:
            owner, control = _owner(family, torch.device("cuda:0")), _owner(family, torch.device("cpu"))
            _push(owner, _rows(), recorded=True)
            _push(control, _rows(), recorded=True)
            owner.legality_recorded = _CUDAData(torch.ones(4, dtype=torch.bool), 1)
            runtime.events.clear()
            serialized = owner.serialize()
            assert torch.equal(serialized["observations"], _rows()["observations"])
            _assert_local(list(runtime.events), (0, 1))
            runtime.events.clear()
            sampled = owner.sample(2, lineage=None)
            assert sampled["observations"].shape == (2, 2) and _syncs(runtime.events) == (0, 1)
            observations["healthy_controls"] = True
            phase = "fault"
            reached, release, started = Event(), Event(), Event()
            outcomes: list[BaseException] = []
            markers: list[bool] = []
            outcome_errors: list[BaseException] = []
            invocations: list[Any] = []
            if local:
                real_failed = LocalCUDAGate.completion_failed

                def failed(gate: LocalCUDAGate) -> bool:
                    actual = real_failed(gate)
                    markers.append(actual)
                    return actual

                patch.setattr(LocalCUDAGate, "completion_failed", failed)
            else:
                real_invocation = domain.device_invocation

                def invocation(*, participant: Any, operation_kind: str, lineage: Any, cuda_devices: tuple[int, ...]) -> Any:
                    actual = real_invocation(
                        participant=participant, operation_kind=operation_kind, lineage=lineage, cuda_devices=cuda_devices
                    )
                    invocations.append(actual)
                    return actual

                patch.setattr(domain, "device_invocation", invocation)

            def after_tensor(name: str, devices: tuple[int, ...], result: Any) -> None:
                if body is not None and name == "__getitem__" and devices == (0,) and isinstance(result, torch.Tensor):
                    if result.shape == (4 if local else 2, 2):
                        started.set()
                        raise body

            def synchronize(index: int) -> None:
                reached.set()
                release.wait(5)
                if index == 0:
                    raise first
                if index == 1 and second is not None:
                    raise second

            def invoke() -> None:
                try:
                    owner.serialize() if local else owner.sample(2, lineage=None)
                except BaseException as error:
                    outcomes.append(error)
                finally:
                    if not local:
                        try:
                            assert len(invocations) == 1
                            markers.append(invocations[0].completion_failed())  # Same issuing worker, historical outcome only.
                        except BaseException as error:
                            outcome_errors.append(error)

            runtime.after_tensor, runtime.on_sync = after_tensor, synchronize
            before_unlock: list[bool] = []
            real_owner_operation = owner._owner_operation

            @contextmanager
            def owner_operation(*, mutation: bool) -> Iterator[None]:
                with real_owner_operation(mutation=mutation):
                    try:
                        yield
                    finally:
                        if reached.is_set():
                            try:
                                owner._check_custody()
                            except RuntimeError:
                                before_unlock.append(True)
                            else:
                                before_unlock.append(False)

            patch.setattr(owner, "_owner_operation", owner_operation)
            runtime.events.clear()
            worker = Thread(target=invoke)
            peer, attempted, finished, peer_errors = _competing_clear(owner)
            blocked = None
            worker.start()
            try:
                did_reach = reached.wait(2)
                if did_reach:
                    peer.start()
                    assert attempted.wait(2)
                    blocked = not finished.wait(0.1)
            finally:
                release.set()
                worker.join(5)
                if peer.ident is not None:
                    peer.join(5)
            observations.update(
                reached=did_reach,
                started_work=started.is_set(),
                syncs=list(_syncs(runtime.events)),
                peer_blocked=blocked,
                worker_errors=[_error_record(error) for error in outcomes],
                peer_errors=[_error_record(error) for error in peer_errors],
                completion_failed=markers,
                outcome_errors=[_error_record(error) for error in outcome_errors],
                quarantine_before_unlock=before_unlock,
            )
            assert not worker.is_alive() and not peer.is_alive() and did_reach and blocked is True
            assert markers and all(marker is True for marker in markers) and not outcome_errors
            assert before_unlock == [True]
            assert len(outcomes) == len(peer_errors) == 1 and isinstance(peer_errors[0], RuntimeError)
            assert "quarantined" in str(peer_errors[0])
            expected = [body, first, second] if schedule == "local_distinct" else [first]
            if schedule == "local_distinct":
                assert isinstance(outcomes[0], BaseExceptionGroup)
                assert len(outcomes[0].exceptions) == 3
                assert all(actual is wanted for actual, wanted in zip(outcomes[0].exceptions, expected, strict=True))
            else:
                assert outcomes[0] is first
            if body_error:
                assert started.is_set()
            if local:
                assert observations["syncs"] == [0, 1]
            else:
                assert observations["syncs"] and observations["syncs"][0] == 0
                assert set(observations["syncs"]) <= {0, 1}  # No permanent generic cleanup-tail promise.
            with pytest.raises(RuntimeError, match="quarantined"):
                owner.clear()
            assert domain.status()[2] is True
            control.clear()
            _push(control, _rows(), recorded=True)
            assert len(control) == 4
            with pytest.raises(RuntimeError):
                control.sample(2, lineage=None)
            assert domain.status()[2] is True
            observations.update(owner_quarantined=True, cpu_local_available=True, ambient_refused=True, domain_after=list(domain.status()))
            success, phase = True, "complete"
    except BaseException as error:
        failure = _error_record(error)
        raise
    finally:
        _poison_json("spawn-after", {**identity, "phase": phase, "success": success, "observations": observations, "failure": failure})
    queue.put((f"cuda producer {case} poison quarantines under owner custody", os.getpid(), os.getppid(), qualified))


class _ParentBaselineOwner:
    pass


def _parent_rng_snapshot() -> tuple:
    cuda = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    return random.getstate(), np.random.get_state(), torch.get_rng_state().clone(), cuda


def _parent_baseline_record(state: tuple, status: tuple[int, int, bool]) -> dict[str, Any]:
    return {
        "domain": list(status),
        "python": hashlib.sha256(repr(state[0]).encode()).hexdigest(),
        "numpy": [state[1][0], hashlib.sha256(state[1][1].tobytes()).hexdigest(), *state[1][2:]],
        "torch": hashlib.sha256(state[2].numpy().tobytes()).hexdigest(),
        "cuda": None if state[3] is None else [hashlib.sha256(item.cpu().numpy().tobytes()).hexdigest() for item in state[3]],
    }


@pytest.mark.parametrize("case", _PRODUCER_CASES)
def test_isolated_producer_poison(case: str) -> None:
    import test_world_rng_bootstrap as bootstrap

    qualified = bootstrap._qualification_active()
    domain, baseline_owner = process_rng_domain(), _ParentBaselineOwner()
    devices = tuple(range(torch.cuda.device_count())) if torch.cuda.is_initialized() else ()
    participant = domain.register(owner=baseline_owner, cuda_devices=devices, entrypoints=frozenset({"baseline"}))
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_producer_poison_child, args=(case, queue), name=_PRODUCER_ROLE)
    before_record = after_record = None
    result = None
    before = None
    success = paired = False
    parent_pid = os.getpid()
    try:
        with domain.operation(participant=participant, operation_kind="baseline", lineage=None):
            before = _parent_rng_snapshot()
        assert domain.status()[2] is False
        before_record = _parent_baseline_record(before, domain.status())
        _poison_json("spawn-parent-before", {"case": case, "parent_pid": parent_pid, "qualified": qualified, "before": before_record})
        process.start()
        process.join(90)
        assert not process.is_alive() and process.exitcode == 0
        result = queue.get(timeout=5)
        assert result == (f"cuda producer {case} poison quarantines under owner custody", process.pid, parent_pid, qualified)
        paired = True
    finally:
        if process.pid is not None and process.is_alive():
            process.terminate()
            process.join(5)
        try:
            with domain.operation(participant=participant, operation_kind="baseline", lineage=None):
                after = _parent_rng_snapshot()
            after_record = _parent_baseline_record(after, domain.status())
            if before is not None:
                _assert_tree_equal(after, before)
            assert domain.status()[2] is False
            success = paired
        finally:
            domain.unregister(participant=participant)
            _poison_json(
                "spawn-observation",
                {
                    "case": case,
                    "process_pid": process.pid,
                    "queued_pid": None if result is None else result[1],
                    "parent_pid": parent_pid,
                    "queued_ppid": None if result is None else result[2],
                    "exitcode": process.exitcode,
                    "qualified": None if result is None else result[3],
                    "message": None if result is None else result[0],
                    "manifest_sha256": (
                        hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest() if qualified else None
                    ),
                    "before": before_record,
                    "after": after_record,
                    "success": success,
                },
            )
            queue.close()
            queue.join_thread()
            process.close()


def _metadata_plan(owner: ReplayBuffer | PrioritizedReplayBuffer, route: str, args: tuple, admitted: bool, runtime: _SimCUDA) -> tuple:
    runtime.events.clear()
    with owner._owner_operation(mutation=False):
        result = owner._device_plan(route, args, {}, admitted=admitted)
    assert runtime.events == [], "Metadata planning executed Tensor/runtime work before arming"
    return result


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("archive_only", [False, True])
def test_raw_prepare_includes_installed_archive_sources(family: str, archive_only: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    incoming = _legacy_transport(family) if archive_only else owner.serialize()
    owner.install_historical_archive(_family_archive(family, 3))  # Authentic B activation prerequisite.
    before = owner.serialize()
    simulated_cuda.events.clear()
    prepared = owner.prepare_serialized(incoming, expected_obs_dim=2, lineage=None)
    events = list(simulated_cuda.events)
    assert isinstance(prepared, PreparedReplay)
    _assert_tree_equal(owner.serialize(), before)
    _assert_cloned_then_completed(events, (3,))


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("prepare", [False, True])
def test_mapping_view_inventory_preserves_accepted_transport(family: str, prepare: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    mapping = MappingProxyType({name: _CUDAData(value, 2) if isinstance(value, torch.Tensor) else value for name, value in before.items()})
    simulated_cuda.events.clear()
    if prepare:
        result = owner.prepare_serialized(mapping, expected_obs_dim=2, lineage=None)
        assert isinstance(result, PreparedReplay)
    else:
        result = owner.validate_serialized(mapping, expected_obs_dim=2)
    events = list(simulated_cuda.events)
    if not prepare:
        assert torch.equal(result.observations.cpu(), _rows()["observations"])
    _assert_tree_equal(owner.serialize(), before)
    if not prepare:
        _assert_local(events, (2,))
    _assert_cloned_then_completed(events, (2,))


@pytest.mark.parametrize(
    "family,field", [("flat", "position"), ("flat", "size"), ("per", "position"), ("per", "size_current"), ("per", "priorities")]
)
def test_dto_metadata_copy_inventory_is_pure_and_complete(family: str, field: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    dto = owner.validate_serialized(before, expected_obs_dim=2)
    malformed = replace(dto, **{field: _CUDAData(torch.tensor(1, dtype=torch.int64), 2)})
    _, devices = _metadata_plan(owner, "materialize_validated", (malformed,), True, simulated_cuda)
    assert devices == (2,), "Owned DTO reconstruction clones this malformed metadata before refusing it"
    simulated_cuda.events.clear()
    with pytest.raises(ValueError):
        owner.materialize_validated(malformed, lineage=None)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    _assert_cloned_then_completed(events, (2,))


@pytest.mark.parametrize("family", ["flat", "per"])
def test_tensor_version_refuses_without_metadata_tensor_effects(family: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    malformed = {**before, "format_version": _CUDAData(torch.tensor(5, dtype=torch.int64), 2)}
    selected, devices = _metadata_plan(owner, "validate_serialized", (malformed,), False, simulated_cuda)
    assert selected is None and devices == (2,)
    with pytest.raises(ValueError, match="format_version") as error:
        owner.validate_serialized(malformed, expected_obs_dim=2)
    events = list(simulated_cuda.events)
    assert "5" in str(error.value)
    assert any(event[:3] == ("work", "__repr__", (2,)) for event in events)
    _assert_local(events, (2,))
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("branch", ["capacity", "rank", "unready"])
def test_early_cpu_refusal_does_not_plan_unused_cuda_target(
    family: str, branch: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner(family, torch.device("cpu"))
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        if branch == "capacity":
            _push(owner, _rows(), recorded=True)
            incoming = owner.serialize()
            if family == "flat":
                owner = ReplayBuffer(capacity=5, device=torch.device("cpu"))
            else:
                owner = PrioritizedReplayBuffer(capacity=5, alpha=1.0, beta=0.0, beta_annealing=False, device=torch.device("cpu"))
            owner.device = torch.device("cuda:3")
            with pytest.raises(ValueError, match="capacity"):
                owner.validate_serialized(incoming, expected_obs_dim=2)
            selected, devices = _metadata_plan(owner, "prepare_serialized", (incoming,), True, simulated_cuda)
        elif branch == "rank":
            rows = _rows()
            rows["observations"] = torch.ones(4, dtype=torch.float32)
            revision = owner._replay_revision
            with pytest.raises(ValueError, match="observations"):
                _push(owner, rows, recorded=True)
            assert owner._replay_revision > revision and len(owner) == 0
            rewards = RewardTensor(
                rows["rewards"], extrinsic=rows["rewards_extrinsic"], intrinsic=None, shaping=rows["rewards_shaping"], is_composed=False
            )
            arguments = (
                rows["observations"],
                rows["actions"],
                rewards,
                rows["next_observations"],
                rows["dones"],
                rows["next_action_masks"],
            )
            owner.device = torch.device("cuda:3")
            selected, devices = _metadata_plan(owner, "push_recorded", arguments, False, simulated_cuda)
        else:
            _push(owner, _rows(), recorded=False)
            request = _request(family)
            assert not owner.readiness(request).ready and len(owner) == 4
            owner.device = torch.device("cuda:3")
            selected, devices = _metadata_plan(owner, "sample_batch", (request,), True, simulated_cuda)
        assert selected is None and devices == ()
        if branch == "capacity":
            with pytest.raises(ValueError, match="capacity"):
                owner.prepare_serialized(incoming, expected_obs_dim=2, lineage=None)
        elif branch == "rank":
            revision = owner._replay_revision
            with pytest.raises(ValueError, match="observations"):
                _push(owner, rows, recorded=True)
            assert owner._replay_revision > revision
        else:
            with pytest.raises(ValueError, match="unavailable"):
                owner.sample_batch(request, lineage=None)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("callback", ["sample", "prepare"])
def test_local_callback_reentry_refuses_before_requesting_admission(family: str, callback: str, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    state = owner.serialize()
    domain = process_rng_domain()
    real_admission, real_clone = domain.admission, torch.Tensor.clone
    requested, refused = [], []
    entered = False

    def admission(actual: Any, *, lineage: Any) -> Any:
        requested.append(lineage)
        return real_admission(lineage=lineage)  # Observe the request; retain real authentication/exclusion.

    def clone(value: torch.Tensor, *args: Any, **kwargs: Any) -> torch.Tensor:
        nonlocal entered
        result = real_clone(value, *args, **kwargs)
        if not entered:
            entered = True
            with pytest.raises(RuntimeError, match="reentry") as error:
                owner.sample(2, lineage=None) if callback == "sample" else owner.prepare_serialized(state, expected_obs_dim=2, lineage=None)
            refused.append(error.value)
        return result

    with monkeypatch.context() as scoped:
        scoped.setattr(type(domain), "admission", admission)
        scoped.setattr(torch.Tensor, "clone", clone)
        actual = owner.serialize()
    assert entered and len(refused) == 1
    _assert_tree_equal(actual, state)
    assert requested == [], "Same-owner callback requested domain while holding owner custody"


def _capacity_refusal_fixture(family: str) -> tuple:
    source = _owner(family, torch.device("cpu"))
    _push(source, _rows(), recorded=True)
    incoming = source.serialize()
    if family == "flat":
        target = ReplayBuffer(capacity=5, device=torch.device("cpu"))
    else:
        target = PrioritizedReplayBuffer(capacity=5, alpha=1.0, beta=0.0, beta_annealing=False, device=torch.device("cpu"))
    target.device = torch.device("cuda:3")
    return target, incoming


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("route", ["validate", "prepare"])
def test_capacity_refusal_does_not_inventory_unused_gpu_rows(
    family: str, route: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, incoming = _capacity_refusal_fixture(family)
    incoming["observations"] = _CUDAData(incoming["observations"], 2)
    before = owner.serialize()
    method = "validate_serialized" if route == "validate" else "prepare_serialized"
    selected, devices = _metadata_plan(owner, method, (incoming,), route == "prepare", simulated_cuda)
    assert selected is None and devices == (), "Capacity refuses before any row source or destination is touched"
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError, match="capacity"):
            if route == "validate":
                owner.validate_serialized(incoming, expected_obs_dim=2)
            else:
                owner.prepare_serialized(incoming, expected_obs_dim=2, lineage=None)
    assert simulated_cuda.events == []
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_capacity_refusal_does_not_merge_installed_gpu_archive(
    family: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, incoming = _capacity_refusal_fixture(family)
    owner.install_historical_archive(_family_archive(family, 3))  # Genuine B-dependent installed-archive fixture.
    before = owner.serialize()
    selected, devices = _metadata_plan(owner, "prepare_serialized", (incoming,), True, simulated_cuda)
    assert selected is None and devices == ()
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError, match="capacity"):
            owner.prepare_serialized(incoming, expected_obs_dim=2, lineage=None)
    assert simulated_cuda.events == []
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
def test_bad_plain_push_refuses_before_unused_gpu_dones(family: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = _owner(family, torch.device("cpu"))
    before = owner.serialize()
    rows = _rows()
    rows["observations"] = torch.ones(4, dtype=torch.float32)
    rows["dones"] = _CUDAData(rows["dones"], 2)
    rewards = RewardTensor(rows["rewards"], extrinsic=None, intrinsic=None, shaping=None, is_composed=False)
    arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], rows["dones"])
    owner.device = torch.device("cuda:3")
    assert owner.action_dim is None
    selected, devices = _metadata_plan(owner, "push", arguments, False, simulated_cuda)
    assert selected is None and devices == (), "Plain no-vocabulary push rejects observations before reading dones"
    revision = owner._replay_revision
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError, match="observations"):
            owner.push(*arguments)
    assert simulated_cuda.events == [] and owner._replay_revision > revision
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("prefix", ["recorded", "known"])
@pytest.mark.parametrize("public", [False, True])
def test_bad_observation_prefix_keeps_necessary_gpu_sources(family: str, prefix: str, public: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    if prefix == "known":
        _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    rows = _rows()
    rows["observations"] = torch.ones(4, dtype=torch.float32)
    rows["dones"] = _CUDAData(rows["dones"], 2)
    rewards = RewardTensor(rows["rewards"], extrinsic=None, intrinsic=None, shaping=None, is_composed=False)
    arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], rows["dones"])
    if prefix == "recorded":
        arguments = (*arguments, _CUDAData(rows["next_action_masks"], 2))
    method = "push_recorded" if prefix == "recorded" else "push"
    owner.device = torch.device("cuda:3")
    selected, devices = _metadata_plan(owner, method, arguments, False, simulated_cuda)
    assert selected is None and devices == (2,)
    if public:
        revision = owner._replay_revision
        with pytest.raises(ValueError, match="observations"):
            getattr(owner, method)(*arguments)
        events = list(simulated_cuda.events)
        assert owner._replay_revision > revision
        _assert_tree_equal(owner.serialize(), before)
        _assert_local(events, (2,))


_RAW_PREFIX_CASES = [
    (family, field, value, message)
    for family in ("flat", "per")
    for field, value, message in (
        ("replay_kind", "wrong", "replay_kind"),
        ("capacity", False, "capacity"),
        ("capacity", 0, "capacity"),
        ("count", False, "size"),
        ("count", -1, "size"),
        ("position", False, "position"),
        ("ring", 0, "position"),
        ("legality_mode", "wrong", "legality_mode"),
        ("action_dim", False, "action_dim"),
        ("action_dim", 3, "action_dim"),
        ("historical_archives", (), "historical_archives"),
        ("observations", "rank", "observations"),
        ("observations", "dtype", "observations"),
        ("observations", "shape", "observations"),
        ("actions", "dtype", "actions"),
        ("empty", None, "Empty"),
        ("precedence", "wrong", "key set mismatch" if family == "flat" else "replay_kind"),
    )
] + [
    ("per", field, value, message)
    for field, value, message in (
        ("alpha", False, "alpha"),
        ("alpha", 0.5, "alpha"),
        ("beta_initial", float("nan"), "beta_initial"),
        ("beta_annealing", 0, "beta_annealing"),
        ("beta", 0.5, "beta"),
        ("priorities", "type", "priorities"),
        ("priorities", "dtype", "priorities"),
        ("priorities", "shape", "priorities"),
        ("max_priority", 0, "max_priority"),
    )
]


@pytest.mark.parametrize(
    "family,field,value,message", _RAW_PREFIX_CASES, ids=[f"{family}-{field}-{value}" for family, field, value, _ in _RAW_PREFIX_CASES]
)
@pytest.mark.parametrize("route", ["validate-plan", "validate", "prepare-plan", "prepare"])
def test_raw_prefix_matrix(
    family: str, field: str, value: Any, message: str, route: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    incoming = copy.deepcopy(before)
    count = "size" if family == "flat" else "size_current"
    incoming["dones"] = _CUDAData(incoming["dones"], 3)
    if field == "empty":
        incoming = _owner(family, torch.device("cpu")).serialize()
        incoming["observations"] = _CUDAData(torch.ones((4, 2)), 3)
    elif field == "ring":
        incoming[count], incoming["position"] = 3, value
    elif field == "precedence":
        incoming["replay_kind"], incoming["extra"] = value, _CUDAData(torch.ones(1), 3)
    elif field in ("observations", "actions", "priorities"):
        original = incoming[field]
        replacements = {
            "rank": torch.ones(4),
            "dtype": original.double() if isinstance(original, torch.Tensor) else original.astype(np.float64),
            "shape": original[:3],
            "type": _CUDAData(torch.ones(4), 3),
        }
        incoming[field] = replacements[value]
    else:
        incoming[count if field == "count" else field] = value
    owner.device = torch.device("cuda:4")
    prepare = route.startswith("prepare")
    method = "prepare_serialized" if prepare else "validate_serialized"
    selected, devices = _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda)
    assert selected is None and devices == (), "Ordinary refusal must exclude all later row/archive/destination work"
    if route.endswith("-plan"):
        return
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError, match=message):
            if prepare:  # Real invocation authority remains a B prerequisite.
                owner.prepare_serialized(incoming, expected_obs_dim=2, lineage=None)
            else:
                owner.validate_serialized(incoming, expected_obs_dim=2)
    assert simulated_cuda.events == []
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize(
    "field,shape,dtype",
    [
        ("observations", (4,), torch.float32),
        ("observations", (4, 2), torch.float64),
        ("observations", (4, 0), torch.float32),
        ("observations", (5, 2), torch.float32),
        ("next_observations", (4,), torch.float32),
        ("next_observations", (4, 2), torch.float64),
        ("next_observations", (3, 2), torch.float32),
        ("actions", (4, 1), torch.int64),
        ("actions", (4,), torch.float32),
        ("actions", (3,), torch.int64),
        ("rewards", (4, 1), torch.float32),
        ("rewards", (4,), torch.float64),
        ("rewards", (3,), torch.float32),
        ("dones", (4, 1), torch.bool),
        ("dones", (4,), torch.float32),
        ("dones", (3,), torch.bool),
    ],
    ids=str,
)
def test_plain_push_metadata_prefix_matrix(
    family: str, field: str, shape: tuple, dtype: torch.dtype, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner(family, torch.device("cpu"))
    before, rows = owner.serialize(), _rows()
    rows[field] = torch.zeros(shape, dtype=dtype)
    rows["rewards_shaping"] = _CUDAData(rows["rewards_shaping"], 3)
    owner.device = torch.device("cuda:4")
    rewards = RewardTensor(rows["rewards"], extrinsic=None, intrinsic=None, shaping=rows["rewards_shaping"], is_composed=False)
    arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], rows["dones"])
    assert _metadata_plan(owner, "push", arguments, False, simulated_cuda) == (None, ())
    revision = owner._replay_revision
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError):
            owner.push(*arguments)
    assert simulated_cuda.events == [] and owner._replay_revision > revision
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("guard", ["type", "rank", "width", "dtype", "dones", "shape", "device"])
def test_recorded_mask_metadata_precedes_tensor_effects(
    family: str, guard: str, simulated_cuda: _SimCUDA, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, rows = _owner(family, torch.device("cpu")), _rows()
    masks = _CUDAData(rows["next_action_masks"], 2)
    dones = _CUDAData(rows["dones"], 2)
    masks = {
        "type": None,
        "rank": _CUDAData(torch.ones(4, dtype=torch.bool), 2),
        "width": _CUDAData(torch.ones((4, 0), dtype=torch.bool), 2),
        "dtype": _CUDAData(torch.ones((4, 2)), 2),
        "shape": _CUDAData(torch.ones((3, 2), dtype=torch.bool), 2),
    }.get(guard, masks)
    if guard == "dones":
        dones = _CUDAData(torch.ones(4), 2)
    elif guard == "device":
        dones = _CUDAData(rows["dones"], 3)
    rewards = RewardTensor(rows["rewards"], extrinsic=None, intrinsic=None, shaping=None, is_composed=False)
    arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], dones, masks)
    owner.device = torch.device("cuda:4")
    assert _metadata_plan(owner, "push_recorded", arguments, False, simulated_cuda) == (None, ())
    revision = owner._replay_revision
    with monkeypatch.context() as scoped:
        scoped.setattr(torch, "cuda", _NoCUDA())
        with pytest.raises(ValueError):
            owner.push_recorded(*arguments)
    assert simulated_cuda.events == [] and owner._replay_revision > revision and len(owner) == 0


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("route", ["raw", "component", "recorded", "known", "retained-width"])
@pytest.mark.parametrize("public", [False, True])
def test_later_metadata_refusal_retains_only_earlier_effects(family: str, route: str, public: bool, simulated_cuda: _SimCUDA) -> None:
    owner, rows = _owner(family, torch.device("cpu")), _rows()
    if route in ("raw", "known", "retained-width"):
        _push(owner, rows, recorded=route != "retained-width")
    before = owner.serialize()
    if route == "raw":
        incoming = {
            **before,
            "observations": _CUDAData(before["observations"], 2),
            "actions": before["actions"].float(),
            "next_observations": _CUDAData(before["next_observations"], 3),
        }
        method, arguments = "validate_serialized", (incoming,)
    else:
        rows["rewards_shaping"] = _CUDAData(rows["rewards_shaping"], 3)
        if route == "component":
            rows["observations"], rows["rewards_extrinsic"] = _CUDAData(rows["observations"], 2), torch.ones(3)
        elif route == "retained-width":
            rows["observations"], rows["next_observations"] = torch.ones((4, 3)), torch.ones((4, 3))
            rows["actions"] = _CUDAData(rows["actions"], 2)
        else:
            rows["dones"], rows["next_action_masks"] = _CUDAData(rows["dones"], 2), _CUDAData(rows["next_action_masks"], 2)
            rows["next_observations"] = torch.ones(4)
        rewards = RewardTensor(
            rows["rewards"], extrinsic=rows["rewards_extrinsic"], intrinsic=None, shaping=rows["rewards_shaping"], is_composed=False
        )
        arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], rows["dones"])
        method = "push_recorded" if route == "recorded" else "push"
        if route == "recorded":
            arguments = (*arguments, rows["next_action_masks"])
    owner.device = torch.device("cuda:4")
    devices = () if route == "retained-width" and family == "per" else (2,)
    assert _metadata_plan(owner, method, arguments, False, simulated_cuda) == (None, devices)
    if not public:
        return
    revision = owner._replay_revision
    message = {
        "raw": "actions",
        "component": "rewards.extrinsic",
        "recorded": "next_observations",
        "known": "next_observations",
        "retained-width": "obs_dim",
    }[route]
    with pytest.raises(ValueError, match=message):
        if route == "raw":
            owner.validate_serialized(*arguments, expected_obs_dim=2)
        else:
            getattr(owner, method)(*arguments)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    assert owner._replay_revision > revision if route != "raw" else owner._replay_revision == revision
    if devices:
        assert any(event[0] == "work" and event[2] == (2,) for event in events)
        _assert_local(events, devices)
    else:
        assert events == []


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("route", ["validate_serialized", "prepare_serialized", "push", "push_recorded", "known"])
def test_prefix_first_effect_inventory_controls(family: str, route: str, simulated_cuda: _SimCUDA) -> None:
    owner, rows = _owner(family, torch.device("cpu")), _rows()
    _push(owner, rows, recorded=True)
    state = owner.serialize()
    assert torch.equal(state["observations"], rows["observations"])
    assert torch.equal(owner.validate_serialized(state, expected_obs_dim=2).rewards, rows["rewards"])
    if route.endswith("serialized"):
        arguments = ({name: _CUDAData(value, 2) if isinstance(value, torch.Tensor) else value for name, value in state.items()},)
    else:
        if route != "known":
            owner.clear()
        rewards = RewardTensor(rows["rewards"], extrinsic=None, intrinsic=None, shaping=None, is_composed=False)
        arguments = (rows["observations"], rows["actions"], rewards, rows["next_observations"], _CUDAData(rows["dones"], 2))
        if route == "push_recorded":
            arguments = (*arguments, _CUDAData(rows["next_action_masks"], 2))
    owner.device = torch.device("cuda:4")
    method = "push" if route == "known" else route
    selected = None if route == "validate_serialized" else owner.device
    assert _metadata_plan(owner, method, arguments, route == "prepare_serialized", simulated_cuda) == (selected, (2,))


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("case", ["type", "keys", "semantics", "later-record"])
@pytest.mark.parametrize("public", [False, True])
def test_archive_record_prefix_matrix(family: str, case: str, public: bool, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    before = owner.serialize()
    record = history._record(_family_archive(family, 2))  # Genuine owned/digest-qualified fixture before observation.
    if case == "type":
        records = [None, record]
    elif case == "keys":
        records = [{**record, "unused": _CUDAData(torch.ones(1), 3)}]
    elif case == "semantics":
        records = [{**record, "reward_semantics": "wrong"}]
    else:
        records = [record, None]
    incoming = {**before, "historical_archives": records, "observations": _CUDAData(torch.ones((4, 2)), 3)}
    owner.device = torch.device("cuda:4")
    devices = () if case in ("type", "keys") else (2, 3)  # Subclass clones can change subsequent validation.
    assert _metadata_plan(owner, "validate_serialized", (incoming,), False, simulated_cuda) == (None, devices)
    if not public:
        return
    with pytest.raises(ValueError, match="embedded archive|reward_semantics|reward semantics"):
        owner.validate_serialized(incoming, expected_obs_dim=2)
    events = list(simulated_cuda.events)
    _assert_tree_equal(owner.serialize(), before)
    if devices:
        clones = [index for index, event in enumerate(events) if event[:3] == ("finished", "clone", (2,))]
        assert clones and max(clones) < next(index for index, event in enumerate(events) if event[0] == "sync")
        assert not any(event[0] == "work" and 3 in event[2] for event in events)
        _assert_local(events, devices)
    else:
        assert events == []


class _ArchiveComparison(_CUDAData):
    """Supported nonplain semantic operand with observable real Tensor work."""

    @classmethod
    def __torch_function__(cls, func: Any, types: Any, args: tuple = (), kwargs: Any = None) -> Any:
        result = super().__torch_function__(func, types, args, kwargs)
        if func.__name__ in ("detach", "clone"):
            return _map_values(result, lambda value: cls(value, value.index) if isinstance(value, _CUDAData) else value)
        # Reduction/arithmetic results stay base tensors: preserving this class
        # for sum would recursively re-enter its intentionally unusual __ne__.
        return result

    def __ne__(self, other: object) -> torch.Tensor:
        return self.sum() != 0


@pytest.mark.parametrize("family", ["flat", "per"])
def test_archive_digest_operator_clone_preserves_rejection(family: str, simulated_cuda: _SimCUDA) -> None:
    record = history._record(_family_archive(family, 2))
    original = _ArchiveComparison(torch.tensor(1), 1)
    record["source_digest"] = original
    simulated_cuda.events.clear()
    cloned = history._clone(record)
    clone_events = list(simulated_cuda.events)
    digest = cloned["source_digest"]
    assert type(digest) is _ArchiveComparison and digest.device == torch.device("cuda:1")
    assert torch.equal(digest.plain(), torch.tensor(1)) and torch.equal(original.plain(), torch.tensor(1))
    assert digest.plain().data_ptr() != original.plain().data_ptr()
    assert any(event[:3] == ("finished", "clone", (1,)) for event in clone_events)
    simulated_cuda.events.clear()
    with pytest.raises(ValueError, match="^archive source digest mismatch after owned cloning$"):
        history._archive_from_state(cloned)
    restore_events = list(simulated_cuda.events)
    assert any(event[:3] == ("finished", "clone", (2,)) for event in restore_events)
    assert any(event[:3] == ("work", "sum", (1,)) for event in restore_events)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("field", ["reward_semantics", "approval_reference", "source_digest", "archived_row_count"])
@pytest.mark.parametrize("reject", [False, True])
def test_archive_semantic_operator_fixture(family: str, field: str, reject: bool, simulated_cuda: _SimCUDA) -> None:
    record = history._record(_family_archive(family, 2))
    record[field] = _ArchiveComparison(torch.tensor(int(reject)), 1)
    simulated_cuda.events.clear()
    if reject or field == "archived_row_count":
        with pytest.raises(ValueError, match="reward|digest|archived_row_count"):
            history._archive_from_state(record)
    else:
        assert history._archive_from_state(record).archived_row_count == 4
    events = simulated_cuda.events
    assert any(event[:2] == ("finished", "clone") and event[2] == (2,) for event in events)
    operators = [event for event in events if event[0] == "work" and event[2] == (1,)]
    assert bool(operators) is (field != "archived_row_count")
    assert not operators or any(event[1] == "sum" for event in operators)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize(
    "case",
    [
        "top-key",
        "archive-key",
        "later-key",
        "reward",
        "approval",
        "later-reward",
        "count",
        "reward_semantics",
        "approval_reference",
        "source_digest",
        "success",
    ],
)
@pytest.mark.parametrize("route", ["validate-plan", "prepare-plan", "validate", "prepare"])
def test_archive_semantic_and_schema_boundaries(family: str, case: str, route: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    incoming = {name: _CUDAData(value, 3) if isinstance(value, torch.Tensor) else value for name, value in before.items()}
    record = history._record(_family_archive(family, 2))
    records, devices, continuation = [record], (2,), False
    if case == "top-key":
        incoming[_CUDAData(torch.tensor(1), 2)] = _CUDAData(torch.ones(1), 3)
    elif case in ("archive-key", "later-key"):
        record = history._record(_family_archive(family, 3))
        record[_CUDAData(torch.tensor(1), 2)] = _CUDAData(torch.ones(1), 3)
        records = [record] if case == "archive-key" else [history._record(_family_archive(family, 1)), record]
        devices = (2,) if case == "archive-key" else (1, 2)
    elif case in ("reward", "approval", "later-reward"):
        record["source_digest"] = _ArchiveComparison(torch.tensor(1), 1)
        if case != "approval":
            record["approval_reference"] = _ArchiveComparison(torch.tensor(1), 1)
        record["approval_reference" if case == "approval" else "reward_semantics"] = "wrong"
        if case == "later-reward":
            records = [history._record(_family_archive(family, 0)), record, history._record(_family_archive(family, 3))]
            devices = (0, 2)
    elif case == "count":
        record["archived_row_count"] = _ArchiveComparison(torch.tensor(4), 1)
        record["source_digest"] = _ArchiveComparison(torch.tensor(1), 1)
    else:
        continuation = True
        devices = (2, 3) if case == "success" else (1, 2, 3)
        if case != "success":
            record[case] = _ArchiveComparison(torch.tensor(1), 1)
    opaque_clones = {
        "later-key": (1, 2, 3),
        "reward": (1, 2, 3),
        "approval": (1, 2, 3),
        "later-reward": (0, 1, 2, 3),
        "count": (1, 2, 3),
    }
    if case in opaque_clones:
        devices, continuation = opaque_clones[case], True
    incoming["historical_archives"] = records
    owner.device = torch.device("cuda:4")
    prepare = route.startswith("prepare")
    method = "prepare_serialized" if prepare else "validate_serialized"
    selected = owner.device if prepare and continuation else None
    assert _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda) == (selected, devices)
    if route.endswith("-plan"):
        return
    arguments = {"expected_obs_dim": 2, **({"lineage": None} if prepare else {})}
    if case == "success":
        getattr(owner, method)(incoming, **arguments)
    else:
        with pytest.raises(ValueError, match="key set mismatch|schema key mismatch|reward|digest|archived_row_count"):
            getattr(owner, method)(incoming, **arguments)
    events = list(simulated_cuda.events)
    assert _syncs(events) == (*devices, 4) if selected is not None else _syncs(events) == devices
    assert any(event[0] == "work" and event[2] == (2,) for event in events)
    copies = {"top-key": (), "archive-key": (), "later-key": (1,), "later-reward": (0, 2)}.get(case, (2,))
    assert all(any(event[:3] == ("finished", "clone", (index,)) for event in events) for index in copies)
    if case in ("reward_semantics", "approval_reference", "source_digest"):
        assert any(event[:3] == ("work", "sum", (1,)) for event in events)
    if case in ("reward", "approval", "later-reward", "count"):
        assert not any(event[0] == "work" and 1 in event[2] for event in events)
    if case not in ("success", "reward_semantics", "approval_reference", "source_digest"):
        assert not any(event[0] == "work" and (3 in event[2] or 4 in event[2]) for event in events)
    _assert_tree_equal(owner.serialize(), before)


class _OpaqueSchemaKey(str):
    """Accepted nonplain key: equality can succeed without a new key policy."""


class _ArchiveCountOnClone(int):
    """A raw nonplain count can become valid exact metadata during ownership."""

    def __deepcopy__(self, memo: dict) -> int:
        return int(self) - 1


def _fix5_archive_record(kind: str, count: int, case: str) -> dict[str, Any]:
    legacy = _legacy_transport("per" if kind == "prioritized" else "flat")
    rows = {key: _CUDAData(value[:count], 2) for key, value in legacy.items() if isinstance(value, torch.Tensor)}
    if kind == "sequential":
        state = {"replay_kind": kind, "format_version": 5, "capacity": 4, "num_transitions": count, "episodes": [rows] if count else []}
    else:
        state = {**legacy, **rows, "position": count % 4, "size_current" if kind == "prioritized" else "size": count}
    record = history._record(history.archive_standalone_replay(state))
    if case == "clone":
        field = {"standard": "size", "prioritized": "size_current", "sequential": "num_transitions"}[kind]
        record["original_state"][field] = _ArchiveCountOnClone(count + 1)
    elif case == "mapping":
        record["original_state"] = MappingProxyType(record["original_state"])
    elif case in ("above", "zero", "digest", "later"):
        record["archived_row_count"] = count + 1
    elif case == "below":
        record["archived_row_count"] = count - 1
    return record


@pytest.mark.parametrize("kind", ["standard", "prioritized", "sequential"])
@pytest.mark.parametrize("case", ["above", "below", "zero", "digest", "later", "match", "clone", "mapping"])
def test_archive_declared_count_fixture(kind: str, case: str, simulated_cuda: _SimCUDA) -> None:
    count = 0 if case == "zero" else 2 if case == "above" else 4
    record = _fix5_archive_record(kind, count, case)
    record["source_digest"] = _ArchiveComparison(torch.tensor(0), 1)
    simulated_cuda.events.clear()
    if case in ("match", "clone", "mapping"):
        assert history._archive_from_state(record).archived_row_count == count
        assert any(event[:3] == ("work", "sum", (1,)) for event in simulated_cuda.events)
    else:
        with pytest.raises(ValueError, match="archive row count differs from original state"):
            history._archive_from_state(record)
        assert not any(event[0] == "work" and (event[1] == "cpu" or event[2] == (1,)) for event in simulated_cuda.events)
    if count:
        assert any(event[:3] == ("finished", "clone", (2,)) for event in simulated_cuda.events)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("kind", ["standard", "prioritized", "sequential"])
@pytest.mark.parametrize("case", ["above", "below", "zero", "digest", "later", "match", "clone", "mapping"])
@pytest.mark.parametrize("route", ["validate-plan", "prepare-plan", "validate", "prepare"])
def test_archive_declared_count_boundaries(family: str, kind: str, case: str, route: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    incoming = {name: _CUDAData(value, 3) if isinstance(value, torch.Tensor) else value for name, value in before.items()}
    count = 0 if case == "zero" else 2 if case == "above" else 4
    record = _fix5_archive_record(kind, count, case)
    count_accepted = case in ("match", "clone", "mapping")
    compatible = kind == ("standard" if family == "flat" else "prioritized")
    continuation = not (kind == "sequential" and count == 0)  # Only this graph has no subclass rows.
    devices = (2, 3) if continuation else ()
    records = [record]
    if case == "digest":
        record["source_digest"] = _ArchiveComparison(torch.tensor(1), 1)
        devices = (1, 2, 3)
    if case == "later":
        records = [history._record(_family_archive(family, 0)), record, history._record(_family_archive(family, 3))]
        devices = (0, 2, 3)
    incoming["historical_archives"] = records
    owner.device = torch.device("cuda:4")
    prepare = route.startswith("prepare")
    method = "prepare_serialized" if prepare else "validate_serialized"
    selected = owner.device if prepare and continuation else None
    assert _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda) == (selected, devices)
    if route.endswith("-plan"):
        return
    arguments = {"expected_obs_dim": 2, **({"lineage": None} if prepare else {})}
    if not count_accepted:
        with pytest.raises(ValueError, match="archive row count differs from original state"):
            getattr(owner, method)(incoming, **arguments)
    elif not compatible:
        message = (
            "^historical archive replay kind differs from uniform storage$"
            if family == "flat"
            else "^historical archive replay kind differs from prioritized storage$"
        )
        with pytest.raises(ValueError, match=message):
            getattr(owner, method)(incoming, **arguments)
    else:
        getattr(owner, method)(incoming, **arguments)
    events = list(simulated_cuda.events)
    assert _syncs(events) == ((*devices, 4) if selected is not None else devices)
    if count:
        assert any(event[:3] == ("finished", "clone", (2,)) for event in events)
    if case == "later":
        assert any(event[:3] == ("finished", "clone", (0,)) for event in events)
    if not count_accepted:
        assert not any(event[0] == "work" and any(index in event[2] for index in (1, 3, 4)) for event in events)
    elif not compatible:
        assert not any(event[0] == "work" and any(index in event[2] for index in (3, 4)) for event in events)
    _assert_tree_equal(owner.serialize(), before)


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("location", ["top", "archive"])
def test_equal_cardinality_opaque_key_fixture(family: str, location: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    incoming = owner.serialize()
    record = history._record(history.archive_standalone_replay(_legacy_transport(family)))
    incoming["historical_archives"] = [record]
    target, field = (incoming, "rewards") if location == "top" else (record, "source_digest")
    target[_OpaqueSchemaKey(field)] = target.pop(field)
    simulated_cuda.events.clear()
    owner.validate_serialized(incoming, expected_obs_dim=2)
    assert simulated_cuda.events == []


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("case", ["top", "archive", "later", "opaque-top", "opaque-archive"])
@pytest.mark.parametrize("route", ["validate-plan", "prepare-plan", "validate", "prepare"])
def test_equal_cardinality_key_boundaries(family: str, case: str, route: str, simulated_cuda: _SimCUDA) -> None:
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    incoming = {name: _CUDAData(value, 3) if isinstance(value, torch.Tensor) else value for name, value in before.items()}
    record = history._record(_family_archive(family, 3 if case in ("archive", "later") else 2))
    incoming["historical_archives"] = [record]
    top = case in ("top", "opaque-top")
    target = incoming if top else record
    fields = ("rewards", "dones") if top else ("source_digest", "approval_reference")
    continuation = case.startswith("opaque-")
    if continuation:
        target[_OpaqueSchemaKey(fields[0])] = target.pop(fields[0])
        devices = (2, 3)
    else:
        cardinality = len(target)
        for field in fields:
            target.pop(field)
        target["unexpected"] = None
        target[_CUDAData(torch.tensor(1), 2)] = None
        assert len(target) == cardinality
        devices = (2,)
        if case == "later":
            incoming["historical_archives"].insert(0, history._record(_family_archive(family, 1)))
            devices, continuation = (1, 2, 3), True  # Earlier opaque clone may change the later schema.
    owner.device = torch.device("cuda:4")
    prepare = route.startswith("prepare")
    method = "prepare_serialized" if prepare else "validate_serialized"
    selected = owner.device if prepare and continuation else None
    assert _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda) == (selected, devices)
    if route.endswith("-plan"):
        return
    arguments = {"expected_obs_dim": 2, **({"lineage": None} if prepare else {})}
    if case.startswith("opaque-"):
        getattr(owner, method)(incoming, **arguments)
    else:
        # Mixed-key sorting can raise TypeError before the ordinary diagnostic.
        with pytest.raises((ValueError, TypeError)):
            getattr(owner, method)(incoming, **arguments)
    events = list(simulated_cuda.events)
    assert _syncs(events) == ((*devices, 4) if selected is not None else devices)
    if case == "later":
        assert any(event[:3] == ("finished", "clone", (1,)) for event in events)
    if not case.startswith("opaque-"):
        assert not any(event[0] == "work" and (3 in event[2] or 4 in event[2]) for event in events)
    _assert_tree_equal(owner.serialize(), before)


def _native_archive_record(kind: str, count: int) -> dict[str, Any]:
    legacy = _legacy_transport("per" if kind == "prioritized" else "flat")
    rows = {key: value[:count] for key, value in legacy.items() if type(value) is torch.Tensor}
    if kind == "sequential":
        state = {"replay_kind": kind, "format_version": 5, "capacity": 4, "num_transitions": count, "episodes": [rows] if count else []}
    else:
        state = {**legacy, **rows, "position": count % 4, "size_current" if kind == "prioritized" else "size": count}
    return history._record(history.archive_standalone_replay(state))


def _clone_repair_record(family: str, location: str, *, operator: bool) -> tuple[dict[str, Any], list[str], str]:
    record = history._record(_family_archive(family, 2))
    state = record["original_state"]
    field = "size" if family == "flat" else "size_current"
    state[field] = 3
    calls: list[str] = []

    class RepairCount(int):
        def __deepcopy__(self, memo: dict) -> int:
            calls.append(location)
            state[field] = 4
            return int(self)

    target, key = (record["source_formats"], "replay") if location == "formats" else (state, "capacity")
    target[key] = RepairCount(target[key])
    if operator:
        record["source_digest"] = _ArchiveComparison(torch.tensor(0), 1)
    return record, calls, field


@pytest.mark.parametrize("family", ["flat", "per"])
@pytest.mark.parametrize("location", ["formats", "sibling"])
@pytest.mark.parametrize("stage", ["fixture", "canonical-fixture", "validate-plan", "prepare-plan", "validate", "prepare"])
def test_archive_clone_repairs_later_count(family: str, location: str, stage: str, simulated_cuda: _SimCUDA) -> None:
    # Both digest forms must survive real recording/revalidation ownership;
    # public preparation also retains its genuine canonical digest control.
    operator = stage not in ("canonical-fixture", "prepare")
    record, calls, field = _clone_repair_record(family, location, operator=operator)
    state = record["original_state"]
    assert type(state[field]) is int and state[field] == 3 and record["archived_row_count"] == 4
    if stage in ("fixture", "canonical-fixture"):
        simulated_cuda.events.clear()
        restored = history._archive_from_state(record)
        assert restored.archived_row_count == 4
        assert calls and state[field] == 4
        assert any(event[:3] == ("finished", "clone", (2,)) for event in simulated_cuda.events)
        assert any(event[:3] == ("work", "sum", (1,)) for event in simulated_cuda.events) is operator
        if not operator:
            assert type(record["source_digest"]) is str and restored.source_digest == record["source_digest"]
        simulated_cuda.events.clear()
        owned_record = history._record(restored)
        recording_events = list(simulated_cuda.events)
        simulated_cuda.events.clear()
        reowned = history._archive_from_state(owned_record)
        second_restore_events = list(simulated_cuda.events)
        assert reowned.archived_row_count == 4 and reowned.original_state[field] == 4
        assert any(event[:3] == ("finished", "clone", (2,)) for event in second_restore_events)
        assert any(event[:3] == ("work", "sum", (1,)) for event in second_restore_events) is operator
        if operator:
            assert any(event[:3] == ("finished", "clone", (1,)) for event in recording_events)
            digest = reowned.source_digest
            original_digest = restored.source_digest
            assert type(digest) is type(original_digest) is _ArchiveComparison
            assert digest.device == original_digest.device == torch.device("cuda:1")
            plain_digest, plain_original = digest.plain(), original_digest.plain()
            assert plain_digest.dtype == plain_original.dtype == torch.int64
            assert plain_digest.shape == plain_original.shape == torch.Size([])
            assert torch.equal(plain_digest, torch.tensor(0)) and torch.equal(plain_original, torch.tensor(0))
            assert plain_digest.data_ptr() != plain_original.data_ptr()
        else:
            assert type(reowned.source_digest) is str and reowned.source_digest == record["source_digest"]
        return
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    before = owner.serialize()
    incoming = {key: _CUDAData(value, 3) if isinstance(value, torch.Tensor) else value for key, value in before.items()}
    incoming["historical_archives"] = [record]
    owner.device = torch.device("cuda:4")
    prepare = stage.startswith("prepare")
    method = "prepare_serialized" if prepare else "validate_serialized"
    plan = _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda)
    assert calls == [] and state[field] == 3
    devices = (1, 2, 3) if operator else (2, 3)
    assert plan == (owner.device if prepare else None, devices)
    if stage.endswith("-plan"):
        return
    arguments = {"expected_obs_dim": 2, **({"lineage": None} if prepare else {})}
    getattr(owner, method)(incoming, **arguments)
    events = list(simulated_cuda.events)
    assert calls and state[field] == 4
    assert any(event[:3] == ("work", "sum", (1,)) for event in events) is operator
    assert _syncs(events) == ((*devices, 4) if prepare else devices)
    assert any(event[:3] == ("finished", "clone", (2,)) for event in events)
    _assert_tree_equal(owner.serialize(), before)


_NATIVE_CLONE_CASES = [
    (family, kind, case)
    for family, kind in (("flat", "standard"), ("per", "prioritized"), ("flat", "sequential"))
    for case in ("above", "below", "empty", "match")
] + [("flat", "standard", case) for case in ("reward", "approval", "count-type", "later", "later-key")]


@pytest.mark.parametrize("family,kind,case", _NATIVE_CLONE_CASES, ids=["-".join(item) for item in _NATIVE_CLONE_CASES])
@pytest.mark.parametrize("prepare", [False, True])
def test_native_archive_clone_boundaries(family: str, kind: str, case: str, prepare: bool, simulated_cuda: _SimCUDA) -> None:
    count = 0 if case == "empty" else 2 if case == "above" else 4
    record = _native_archive_record(kind, count)
    record["source_digest"] = _ArchiveComparison(torch.tensor(0), 1)
    records = [record]
    if case in ("above", "empty", "later"):
        record["archived_row_count"] = count + 1
    elif case == "below":
        record["archived_row_count"] = count - 1
    elif case in ("reward", "approval"):
        record["approval_reference" if case == "approval" else "reward_semantics"] = "wrong"
        if case == "reward":
            record["approval_reference"] = _ArchiveComparison(torch.tensor(0), 1)
    elif case == "count-type":
        record["archived_row_count"] = _ArchiveComparison(torch.tensor(count), 1)
    elif case == "later-key":
        record = history._record(_family_archive("flat", 2))
        record.pop("source_digest")
        record.pop("approval_reference")
        record["unexpected"] = None
        record[_CUDAData(torch.tensor(1), 1)] = None
    if case in ("later", "later-key"):
        records = [_native_archive_record(kind, 4), record, history._record(_family_archive("flat", 2))]
    # Real helper prerequisites distinguish schema/semantic/count refusal from
    # fixture setup errors; an accepting digest operator is reached only at match.
    simulated_cuda.events.clear()
    if case == "match":
        assert history._archive_from_state(record).archived_row_count == count
        assert any(event[:3] == ("work", "sum", (1,)) for event in simulated_cuda.events)
    else:
        with pytest.raises(ValueError, match="row count|reward semantics|archived_row_count|schema key mismatch"):
            history._archive_from_state(record)
        assert not any(event[:3] == ("work", "sum", (1,)) for event in simulated_cuda.events)
    owner = _owner(family, torch.device("cpu"))
    _push(owner, _rows(), recorded=True)
    incoming = {key: _CUDAData(value, 3) if isinstance(value, torch.Tensor) else value for key, value in owner.serialize().items()}
    incoming["historical_archives"] = records
    owner.device = torch.device("cuda:4")
    method = "prepare_serialized" if prepare else "validate_serialized"
    devices = (1, 3) if case == "match" else (1,) if case == "later-key" else ()
    assert _metadata_plan(owner, method, (incoming,), prepare, simulated_cuda) == (
        owner.device if prepare and case == "match" else None,
        devices,
    )
    # CPU clones still belong to the reached prefix even when no CUDA device
    # describes them. Inspect recorded identities without Tensor equality.
    prefix = ReplayPrefix(planning=True)
    try:
        for item in records:
            prefix.archive(item, lambda: pytest.fail("planning invoked archive restoration"))
    except _ReplayPrefixStopError:
        pass
    reached = records[:1] if case == "later-key" else records[:2] if case == "later" else records
    for item in reached:
        assert any(value is item["source_formats"] for value in prefix.values)
        assert any(value is item["original_state"] for value in prefix.values)
    assert simulated_cuda.events == []


@pytest.mark.parametrize(
    "case",
    [
        "native",
        "primitives",
        "alias",
        "numpy-numeric",
        "numpy-bool",
        "scalar",
        "tensor-subclass",
        "mapping",
        "list-subclass",
        "key",
        "kind",
        "count",
        "proxy",
        "numpy-object",
        "numpy-structured",
        "numpy-subclass",
        "numpy-scalar",
        "cycle",
        "ordered-items",
        "tensor-detach",
        "tensor-attribute",
    ],
)
def test_archive_clone_graph_classification(case: str, simulated_cuda: _SimCUDA) -> None:
    record = _native_archive_record("standard", 4)
    state = record["original_state"]
    calls: list[str] = []

    def unexpected(*args: Any, **kwargs: Any) -> Any:
        calls.append(case)
        raise AssertionError("Clone classification invoked an opaque protocol")

    class CloneScalar(int):
        __deepcopy__ = unexpected

    class ProtocolMapping(dict):
        items = unexpected

    class ProtocolList(list):
        __iter__ = unexpected

    class ProtocolArray(np.ndarray):
        __deepcopy__ = unexpected

    if case == "primitives":
        state["leaves"] = (None, True, 1, 1.0, "value", b"value")
    elif case == "alias":
        leaf = [1, {"value": torch.ones(1)}]
        state["aliases"] = [leaf, leaf]
    elif case in ("numpy-numeric", "numpy-bool", "numpy-object", "numpy-structured", "numpy-subclass", "numpy-scalar"):
        values = {
            "numpy-numeric": np.ones(2, dtype=np.float32),
            "numpy-bool": np.ones(2, dtype=np.bool_),
            "numpy-object": np.array([CloneScalar(1)], dtype=object),
            "numpy-structured": np.zeros(2, dtype=[("value", np.float32)]),
            "numpy-subclass": np.ones(2).view(ProtocolArray),
            "numpy-scalar": np.int64(1),
        }
        state["array"] = values[case]
    elif case == "scalar":
        record["source_formats"]["replay"] = CloneScalar(4)
    elif case == "tensor-subclass":
        state["observations"] = _CUDAData(state["observations"], 2)
    elif case == "mapping":
        record["original_state"] = ProtocolMapping(state)
    elif case == "list-subclass":
        state["nested"] = ProtocolList([1])
    elif case == "key":
        state[_OpaqueSchemaKey("capacity")] = state.pop("capacity")
    elif case == "kind":
        state["replay_kind"] = _OpaqueSchemaKey(state["replay_kind"])
    elif case == "count":
        state["size"] = _ArchiveCountOnClone(5)
    elif case == "proxy":
        record["original_state"] = MappingProxyType(state)
    elif case == "cycle":
        state["cycle"] = state
    elif case == "ordered-items":
        ordered = OrderedDict(state)
        ordered.items = unexpected
        assert type(ordered) is OrderedDict
        record["original_state"] = ordered
    elif case in ("tensor-detach", "tensor-attribute"):
        tensor = state["observations"]
        assert type(tensor) is torch.Tensor and object.__getattribute__(tensor, "__dict__") == {}
        if case == "tensor-detach":
            tensor.detach = unexpected
        else:
            tensor.harmless = 1
    record["reward_semantics"] = "wrong"
    prefix = ReplayPrefix(planning=True)
    simulated_cuda.events.clear()
    with pytest.raises(_ReplayPrefixStopError):
        prefix.archive(record, lambda: pytest.fail("planning invoked archive restoration"))
    assert calls == [] and simulated_cuda.events == []
    assert prefix.unknown is (case not in ("native", "primitives", "alias", "numpy-numeric", "numpy-bool"))
    assert len(prefix.values) == 2
    assert prefix.values[0] is record["source_formats"] and prefix.values[1] is record["original_state"]
    # Deliberately classifier-only: inventory may invoke Mapping protocols and
    # does not promise cycle traversal. No cyclic real constructor is executed.
