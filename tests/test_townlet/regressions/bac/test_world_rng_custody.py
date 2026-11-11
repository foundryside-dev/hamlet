"""R0 core owner controls; actual downstream stochastic enrollment remains owed.

R40 qualified the existing genuine-learning control and missing-reset-API RED.
These source-owned cases exercise actual private/shared owners, not a test gate.
"""

from __future__ import annotations

import gc
import hashlib
import json
import multiprocessing
import os
import pickle
import random
import threading
import weakref
from collections import OrderedDict
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration import rnd as rnd_module
from townlet.exploration import rng_custody as custody_module
from townlet.exploration import world_curiosity_state as world_state
from townlet.exploration.provider_factory import make_backend
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.rng_custody import RNGOperation, RNGParticipant, process_rng_domain
from townlet.exploration.world_curiosity_state import (
    WORLD_SEED_COMPONENTS,
    OwnedWorldBackend,
    PreparedWorldBackend,
    ServiceClock,
    SharedWorldBackend,
    WorldCuriosityDescriptor,
    WorldRandomSources,
    WorldRNGState,
)
from townlet.universe.compiler import UniverseCompiler


def _equal(left: Any, right: Any) -> None:
    """Independent exact evidence comparison, including complete RNG payloads."""
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert (left.layout, left.dtype, left.device, left.shape) == (right.layout, right.dtype, right.device, right.shape)
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert (left.dtype, left.shape) == (right.dtype, right.shape)
        np.testing.assert_array_equal(left, right)
    elif isinstance(left, Mapping):
        assert left.keys() == right.keys()
        if isinstance(left, OrderedDict):
            assert list(left) == list(right)
            assert hasattr(left, "_metadata") == hasattr(right, "_metadata")
            if hasattr(left, "_metadata"):
                _equal(left._metadata, right._metadata)
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for item, reference in zip(left, right, strict=True):
            _equal(item, reference)
    else:
        assert left == right


def _ambient() -> dict[str, Any]:
    # CPU only. In particular, no availability/initialization query is needed.
    return {
        "python": deepcopy(random.getstate()),
        "numpy_legacy": deepcopy(np.random.get_state()),
        "torch_cpu": torch.get_rng_state().clone(),
    }


def _restore_ambient(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy_legacy"])
    torch.set_rng_state(state["torch_cpu"])


@pytest.fixture(autouse=True)
def preserve_cpu_ambient() -> Iterator[None]:
    # Complete prior tests' real weak-owner lifetimes before this case's timeline.
    # This performs ordinary reclamation; it neither clears nor heals domain poison.
    gc.collect()
    process_rng_domain().status()
    original = _ambient()
    try:
        yield
    finally:
        _restore_ambient(original)


def _ambient_next(state: dict[str, Any]) -> dict[str, Any]:
    """Next values from independent local generators, without ambient installation."""
    python = random.Random(0)
    python.setstate(state["python"])
    legacy = np.random.RandomState(0)
    legacy.set_state(state["numpy_legacy"])
    cpu = torch.Generator(device="cpu")
    cpu.set_state(state["torch_cpu"])
    return {
        "python": (python.random(), python.gauss(0.0, 1.0)),
        "numpy_legacy": (legacy.random_sample(3), legacy.normal(size=3)),
        "torch_cpu": torch.rand(3, generator=cpu),
    }


def _draw_sources(sources: WorldRandomSources) -> dict[str, Any]:
    return {
        "python": (sources.python.random(), sources.python.gauss(0.0, 1.0)),
        "numpy_pcg64": (sources.numpy.random(3), sources.numpy.integers(0, 101, size=3)),
        "numpy_legacy": (np.random.random_sample(3), np.random.normal(size=3)),
        "torch_cpu": torch.rand(3),
    }


def _native_evidence(backend: RNDExploration) -> dict[str, Any]:
    modules = {"target": backend.fixed_network, "predictor": backend.predictor_network}
    return {
        "native": backend.checkpoint_state(),
        "gradients": {
            role: {
                name: None if parameter.grad is None else parameter.grad.detach().clone() for name, parameter in module.named_parameters()
            }
            for role, module in modules.items()
        },
        "identity": {
            "backend": id(backend),
            "optimizer": id(backend.optimizer),
            "modules": {role: id(module) for role, module in modules.items()},
            "parameters": {
                role: tuple((name, id(parameter), parameter.data_ptr()) for name, parameter in module.named_parameters())
                for role, module in modules.items()
            },
            "optimizer_parameters": tuple(id(parameter) for group in backend.optimizer.param_groups for parameter in group["params"]),
            "buffer": id(backend.obs_buffer),
            "pending_rows": tuple((id(row), row.data_ptr()) for row in backend.obs_buffer),
        },
    }


def _live_evidence(owner: OwnedWorldBackend) -> dict[str, Any]:
    """White-box observation while the test owns caller quiescence.

    No owner.call/snapshot or RNG.snapshot runs between prepare and install: those
    public observations can themselves invalidate a released preparation. Raw reads
    here grant no concurrency guarantee for independently retained mutable aliases.
    """
    backend = owner._backend
    assert type(backend) is RNDExploration
    rng = owner._rng
    return {
        **_native_evidence(backend),
        "rng_identity": id(rng),
        "rng_components": deepcopy(rng._components),
        "rng_descriptor": rng._descriptor.to_dict(),
        "rng_world_id": rng._world_id,
        "rng_devices": rng._cuda_devices,
        "rng_broken": rng._broken,
        "owner_token": id(owner._token),
        "owner_revision": owner._revision,
        "owner_failed": owner._failed,
    }


def _rows(count: int, width: int, start: int) -> torch.Tensor:
    # Deterministic real observations; gradients are produced by actual backward.
    return torch.arange(start, start + count * width, dtype=torch.float32).reshape(count, width) / float(width + count)


def _service(backend: RNDExploration, sources: WorldRandomSources, observations: torch.Tensor, position: int) -> dict[str, Any]:
    draws = _draw_sources(sources)
    rewards = backend.compute_intrinsic_rewards(observations, update_stats=True)
    receipt = backend.admit_and_service_at(observations, clock=ServiceClock("world_eligible_admission", position))
    return {"draws": draws, "rewards": rewards, "receipt": receipt}


@dataclass
class PrivateRND:
    owner: OwnedWorldBackend
    factory: Callable[[WorldRNGState], RNDExploration]
    descriptor: WorldCuriosityDescriptor
    initial: dict[str, Any]
    learned: dict[str, Any]
    batch_size: int
    width: int


@pytest.fixture(scope="module")
def compiled() -> Any:
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


def _resolved_rnd(selected: Any, scope: str) -> ResolvedExplorationPolicy:
    """Assemble genuine DTOs from the published current resolver recipe."""
    drive_data = selected.drive.intrinsic.model_dump()
    drive_data["strategy"] = "rnd"
    training_data = deepcopy(selected.training.model_dump())
    training_data["replay_buffer"]["batch_size"] = 2
    intrinsic = training_data["intrinsic"]
    intrinsic["rnd"]["feature_dim"] = 4
    intrinsic["rnd"]["learning_rate"] = 0.001
    intrinsic["initial_weight"] = 0.4
    intrinsic["survival_window"] = 10
    intrinsic["min_survival_fraction"] = 0.01
    intrinsic["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    training_data["training_loop"]["max_steps_per_episode"] = 20
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
            "provider_parameter_source": "training",
            "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "max_pending_rows": 4, "overflow_policy": "drop_oldest"},
            "providers": {
                "count_based": {"quantization_width": 0.125, "max_entries": 4},
                "icm": {
                    "feature_dim": 4,
                    "hidden_dim": 8,
                    "learning_rate": 0.001,
                    "inverse_weight": 0.8,
                    "forward_weight": 0.2,
                    "training_batch_size": 2,
                    "max_pending_transitions": 4,
                },
            },
        }
    )
    return resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive_data), TrainingV2Config.model_validate(training_data), options
    )


@pytest.fixture
def private_rnd(compiled: Any) -> PrivateRND:
    selected = compiled.get_level(compiled.metadata.primary_level)
    width = selected.token_spec.total_dims
    actions = selected.action_metadata.total_actions
    assert width > 0 and actions > 0
    resolved = _resolved_rnd(selected, "per_world")
    assert resolved.predictor_batch_size == 2
    descriptor = WorldCuriosityDescriptor.from_policy(
        resolved, world_ids=("R0-current",), observation_dim=width, action_dim=actions, training_seed=701
    )

    def factory(candidate_rng: WorldRNGState) -> RNDExploration:
        backend = make_backend(
            resolved,
            world_id="R0-current",
            obs_dim=width,
            action_dim=actions,
            device=torch.device("cpu"),
            rng=candidate_rng,
            descriptor=descriptor,
        )
        assert type(backend) is RNDExploration
        return backend

    rng = WorldRNGState.create(descriptor=descriptor, world_id="R0-current", cuda_devices=())
    owner = OwnedWorldBackend.construct(rng=rng, factory=factory)
    initial = _live_evidence(owner)
    for component in WORLD_SEED_COMPONENTS:
        # Actual named-stream draws establish a current continuation in every
        # component before preparation. No stored seed/state/counter is fabricated.
        with owner._rng.activate(component) as sources:
            _draw_sources(sources)
    observations = _rows(3, width, 1)
    result = owner.call(lambda backend, sources: _service(backend, sources, observations, 3), lineage=None)
    assert result["receipt"].optimizer_updates == 1
    assert result["receipt"].pending_rows == 1
    owner.call(lambda backend, sources: backend.decay_epsilon(), lineage=None)
    learned = _live_evidence(owner)
    _assert_learned(initial, learned)
    return PrivateRND(owner, factory, descriptor, initial, learned, resolved.predictor_batch_size, width)


def _assert_learned(initial: dict[str, Any], learned: dict[str, Any]) -> None:
    native = learned["native"]
    service = native["predictor_service"]
    assert (service["admitted_rows"], service["consumed_rows"], service["dropped_rows"], service["optimizer_updates"]) == (3, 2, 0, 1)
    assert service["optimizer_epoch_origin"] == 0
    assert service["optimizer_step_offset"] == 0
    assert service["service_position"] == 3
    assert service["pending_observations"].shape == (1, native["obs_dim"])
    assert native["reward_rms_count"] > initial["native"]["reward_rms_count"]
    assert native["epsilon"] < initial["native"]["epsilon"]
    _equal(initial["native"]["fixed_network"], native["fixed_network"])
    assert any(not torch.equal(value, native["predictor_network"][name]) for name, value in initial["native"]["predictor_network"].items())
    optimizer_states = native["optimizer"]["state"]
    assert optimizer_states
    assert len(optimizer_states) == len(learned["identity"]["optimizer_parameters"])
    assert all(state["step"].item() == 1 for state in optimizer_states.values())
    assert any(bool((state["exp_avg"] != 0).any()) for state in optimizer_states.values())
    assert any(bool((state["exp_avg_sq"] > 0).any()) for state in optimizer_states.values())
    assert any(value is not None and bool((value != 0).any()) for value in learned["gradients"]["predictor"].values())
    assert all(value is None for value in learned["gradients"]["target"].values())
    assert learned["identity"]["optimizer_parameters"] == tuple(item[1] for item in learned["identity"]["parameters"]["predictor"])
    assert learned["owner_failed"] is False and learned["rng_broken"] is False
    assert learned["rng_devices"] == ()
    for component in WORLD_SEED_COMPONENTS:
        assert not torch.equal(initial["rng_components"][component]["torch_cpu"], learned["rng_components"][component]["torch_cpu"])


@contextmanager
def _forbid_live_preparation_work(monkeypatch: pytest.MonkeyPatch, owner: OwnedWorldBackend) -> Iterator[None]:
    live_backend = owner._backend
    original_checkpoint = RNDExploration.checkpoint_state
    original_call = OwnedWorldBackend.call
    original_snapshot = OwnedWorldBackend.snapshot

    def checkpoint(backend: RNDExploration) -> dict[str, Any]:
        assert backend is not live_backend, "reset preparation captured the live native backend"
        return original_checkpoint(backend)

    def call(destination: OwnedWorldBackend, operation: Callable[..., Any], *, lineage: RNGOperation | None) -> Any:
        assert destination is not owner, "reset preparation invoked live owner.call"
        return original_call(destination, operation, lineage=lineage)

    def snapshot(destination: OwnedWorldBackend, *, lineage: RNGOperation | None) -> dict[str, Any]:
        assert destination is not owner, "reset preparation invoked live owner.snapshot"
        return original_snapshot(destination, lineage=lineage)

    def create(cls: type[WorldRNGState], **kwargs: Any) -> WorldRNGState:
        raise AssertionError("reset preparation reseeded instead of forking the current continuation")

    with monkeypatch.context() as patch:
        # Class-level identity discrimination lets genuine offside RND clones run
        # their real checkpoint/validation work. No native work is stubbed out.
        patch.setattr(RNDExploration, "checkpoint_state", checkpoint)
        patch.setattr(OwnedWorldBackend, "call", call)
        patch.setattr(OwnedWorldBackend, "snapshot", snapshot)
        patch.setattr(WorldRNGState, "create", classmethod(create))
        yield


def _reset_rnd(current_candidate: RNDExploration, fresh_candidate: RNDExploration) -> None:
    assert type(current_candidate) is RNDExploration and type(fresh_candidate) is RNDExploration
    current_candidate.install_state(current_candidate.prepare_learning_reset(fresh=fresh_candidate))


def test_current_private_owner_has_genuine_learned_continuation(private_rnd: PrivateRND) -> None:
    """Fixture control: real factory/backward/Adam/FIFO establish the RED prerequisite."""
    _assert_learned(private_rnd.initial, private_rnd.learned)
    _equal(private_rnd.learned, _live_evidence(private_rnd.owner))


def test_private_learning_reset_prepares_current_streams_without_live_effects(
    private_rnd: PrivateRND, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Catch reseeding, live-capture preparation, dropped factory draws and wrong next service."""
    rig = private_rnd
    owner = rig.owner
    current_rng = owner._rng.snapshot()
    reference_rng = WorldRNGState.from_snapshot(current_rng, descriptor=rig.descriptor, world_id="R0-current", cuda_devices=())
    with reference_rng.activate("model_init"):
        fresh = rig.factory(reference_rng)
    fresh_native = fresh.checkpoint_state()
    expected_components = deepcopy(reference_rng._components)
    reference_native = deepcopy(owner._backend)
    _reset_rnd(reference_native, fresh)
    before = _live_evidence(owner)
    ambient_before = _ambient()
    next_before = _ambient_next(ambient_before)

    with _forbid_live_preparation_work(monkeypatch, owner):
        # R40 observed the genuine missing-API RED here after the learned fixture;
        # the production implementation must now satisfy the complete witness.
        prepared = owner.prepare_learning_reset(factory=rig.factory, prepare_native=_reset_rnd, lineage=None)

    _equal(before, _live_evidence(owner))
    _equal(ambient_before, _ambient())
    _equal(next_before, _ambient_next(_ambient()))
    owner.install(prepared, lineage=None)
    installed = _live_evidence(owner)
    _equal(expected_components, installed["rng_components"])
    _equal(reference_native.checkpoint_state(), installed["native"])
    for key in ("fixed_network", "predictor_network", "optimizer", "reward_rms_mean", "reward_rms_var", "reward_rms_count"):
        _equal(fresh_native[key], installed["native"][key])
    retained = before["native"]["predictor_service"]
    actual = installed["native"]["predictor_service"]
    for key in retained:
        if key not in {"optimizer_epoch_origin", "optimizer_step_offset"}:
            _equal(retained[key], actual[key])
    assert actual["optimizer_epoch_origin"] == 1
    assert actual["optimizer_step_offset"] == 0
    assert installed["native"]["optimizer"]["state"] == {}
    assert installed["native"]["epsilon"] == before["native"]["epsilon"]
    assert installed["owner_token"] == before["owner_token"]
    assert installed["owner_revision"] == before["owner_revision"] + 1
    assert installed["identity"]["optimizer_parameters"] == tuple(item[1] for item in installed["identity"]["parameters"]["predictor"])
    assert all(value is None for role in installed["gradients"].values() for value in role.values())
    assert installed["owner_failed"] is False and installed["rng_broken"] is False
    for component in ("model_init", "service"):
        _equal(before["rng_components"][component], installed["rng_components"][component])
    for component in ("target", "predictor"):
        assert not torch.equal(before["rng_components"][component]["torch_cpu"], installed["rng_components"][component]["torch_cpu"])
    _equal(ambient_before, _ambient())

    observations = _rows(1, rig.width, 101)
    with reference_rng.activate("service") as sources:
        expected = _service(reference_native, sources, observations, 4)
    actual_result = owner.call(lambda backend, sources: _service(backend, sources, observations, 4), lineage=None)
    _equal(expected["draws"], actual_result["draws"])
    _equal(expected["rewards"], actual_result["rewards"])
    assert actual_result["receipt"] == expected["receipt"]
    resumed = _live_evidence(owner)
    _equal(reference_native.checkpoint_state(), resumed["native"])
    _equal(reference_rng._components, resumed["rng_components"])
    service = resumed["native"]["predictor_service"]
    assert (service["admitted_rows"], service["consumed_rows"], service["optimizer_updates"], len(service["pending_observations"])) == (
        4,
        4,
        2,
        0,
    )
    assert service["optimizer_epoch_origin"] == 1
    assert all(state["step"].item() == 1 for state in resumed["native"]["optimizer"]["state"].values())
    _equal(ambient_before, _ambient())


@pytest.fixture
def shared_rnd(compiled: Any) -> tuple[SharedWorldBackend, Callable[[], RNDExploration]]:
    selected = compiled.get_level(compiled.metadata.primary_level)
    resolved = _resolved_rnd(selected, "shared")

    def factory() -> RNDExploration:
        backend = make_backend(
            resolved,
            world_id=None,
            obs_dim=selected.token_spec.total_dims,
            action_dim=selected.action_metadata.total_actions,
            device="cpu",
            rng=None,
            descriptor=None,
        )
        assert type(backend) is RNDExploration
        return backend

    return SharedWorldBackend.construct(factory=factory, cuda_devices=()), factory


class _ObservedLock:
    """Observe contention at the real production RLock; supply no second lock."""

    def __init__(self, actual: Any, contended: threading.Event):
        self.actual, self.contended = actual, contended

    def __enter__(self) -> _ObservedLock:
        if threading.current_thread().name == "r0-contender":
            if not self.actual.acquire(blocking=False):
                self.contended.set()
                self.actual.acquire()
        else:
            self.actual.acquire()
        return self

    def __exit__(self, *errors: Any) -> None:
        self.actual.release()


@pytest.mark.parametrize("route", ["shared_call", "shared_constructor", "private_call", "shared_reset"])
def test_actual_shared_private_entrypoints_wait_at_common_domain(
    private_rnd: PrivateRND,
    shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]],
    monkeypatch: pytest.MonkeyPatch,
    route: str,
) -> None:
    shared, factory = shared_rnd
    contended, entered = threading.Event(), threading.Event()
    errors: list[BaseException] = []
    domain = process_rng_domain()
    monkeypatch.setattr(domain, "_lock", _ObservedLock(domain._lock, contended))

    def actual_factory() -> RNDExploration:
        entered.set()
        return factory()

    def consuming(backend: RNDExploration) -> torch.Tensor:
        # A real supported module hook consumes ambient RNG during actual forward.
        def prehook(module: Any, arguments: Any) -> None:
            entered.set()
            torch.rand(1)

        handle = backend.predictor_network.register_forward_pre_hook(prehook)
        try:
            return backend.compute_intrinsic_rewards(_rows(1, private_rnd.width, 11), update_stats=False)
        finally:
            handle.remove()

    def contender() -> None:
        try:
            if route == "shared_constructor":
                SharedWorldBackend.construct(factory=actual_factory, cuda_devices=())
            elif route == "shared_call":
                shared.call(consuming, lineage=None)
            else:
                private_rnd.owner.call(lambda backend, sources: consuming(backend), lineage=None)
        except BaseException as error:
            errors.append(error)

    thread = threading.Thread(target=contender, name="r0-contender")

    def holding(*args: Any) -> None:
        before = _ambient()
        thread.start()
        assert contended.wait(10), "the actual consuming route never reached the real admission lock"
        assert not entered.is_set()
        _equal(before, _ambient())

    try:
        if route == "private_call":
            shared.call(holding, lineage=None)
        elif route == "shared_reset":

            def reset_factory() -> RNDExploration:
                holding()
                return factory()

            with domain.operation(participant=shared.rng_participant, operation_kind="prepare", lineage=None) as operation:
                prepared = shared.prepare_learning_reset(factory=reset_factory, prepare_native=_reset_rnd, lineage=operation)
                assert not entered.is_set()
                shared.install(prepared, lineage=operation)
                assert not entered.is_set()
        else:
            private_rnd.owner.call(holding, lineage=None)
    finally:
        if thread.ident is not None:
            thread.join(30)
    assert not thread.is_alive()
    assert not errors
    assert entered.is_set()


def test_domain_opaque_lineage_and_named_nesting(private_rnd: PrivateRND) -> None:
    domain = process_rng_domain()
    owner = private_rnd.owner
    participant = owner.rng_participant
    before = _ambient()
    with pytest.raises(TypeError):
        RNGParticipant()
    with pytest.raises(TypeError):
        deepcopy(participant)
    with pytest.raises(TypeError):
        pickle.dumps(participant)
    with domain.operation(participant=participant, operation_kind="call", lineage=None) as operation:
        token = domain.current_token(participant=participant, operation=operation)
        with pytest.raises(RuntimeError, match="reentry"):
            owner.call(lambda backend, sources: torch.rand(1), lineage=None)
        with pytest.raises(ValueError):
            owner.call(lambda backend, sources: torch.rand(1), lineage=object.__new__(RNGOperation))
        # Exact lineage permits genuine nested managed work.
        owner.call(lambda backend, sources: backend.predictor_service_counters(), lineage=operation)
        with pytest.raises(ValueError, match="nested"):
            domain.validate_current(token=token, operation=operation)
    with pytest.raises(ValueError):
        owner.call(lambda backend, sources: torch.rand(1), lineage=operation)
    _equal(before, _ambient())
    snapshot = owner._rng.snapshot()
    reference_a = WorldRNGState.from_snapshot(snapshot, descriptor=private_rnd.descriptor, world_id="R0-current", cuda_devices=())
    reference_b = WorldRNGState.from_snapshot(snapshot, descriptor=private_rnd.descriptor, world_id="R0-current", cuda_devices=())
    # Independent nonnested streams: B cannot influence A's resumed position.
    with reference_a.activate("target") as sources:
        first, third, fourth = (_draw_sources(sources) for _ in range(3))
    with reference_b.activate("predictor") as sources:
        second = _draw_sources(sources)
    expected_components = deepcopy(snapshot["components"])
    expected_components["target"] = deepcopy(reference_a._components["target"])
    expected_components["predictor"] = deepcopy(reference_b._components["predictor"])

    def nested(rng: WorldRNGState) -> list[dict[str, Any]]:
        with rng.activate("target") as a:
            first = _draw_sources(a)
            with rng.activate("predictor") as b:
                second = _draw_sources(b)
                with rng.activate("target") as resumed:
                    third = _draw_sources(resumed)
            fourth = _draw_sources(a)
        return [first, second, third, fourth]

    _equal([first, second, third, fourth], nested(owner._rng))
    _equal(expected_components, owner._rng._components)
    _equal(before, _ambient())


@pytest.mark.parametrize("mutation", ["service", "manual", "replacement", "ambient", "membership", "fabricated", "foreign", "used"])
def test_prepared_identity_freshness_and_one_use(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], mutation: str
) -> None:
    owner = private_rnd.owner
    shared, _ = shared_rnd
    prepared = owner.prepare_learning_reset(factory=private_rnd.factory, prepare_native=_reset_rnd, lineage=None)
    if mutation == "service":
        owner.call(lambda backend, sources: _service(backend, sources, _rows(1, private_rnd.width, 61), 4), lineage=None)
    elif mutation == "manual":
        owner.call(lambda backend, sources: backend.optimizer.step(), lineage=None)  # genuine retained backward gradients
    elif mutation == "replacement":

        def replace(backend: RNDExploration, sources: WorldRandomSources) -> None:
            backend.optimizer = torch.optim.Adam(backend.predictor_network.parameters(), lr=0.001)

        owner.call(replace, lineage=None)
    elif mutation == "ambient":
        shared.call(lambda backend: None, lineage=None)  # unchanged RNG bytes still invalidate domain freshness
    elif mutation == "membership":

        class RegistrationOwner:
            pass

        membership_owner = RegistrationOwner()
        member = process_rng_domain().register(owner=membership_owner, cuda_devices=(), entrypoints=frozenset({"probe"}))
        process_rng_domain().unregister(participant=member)
    elif mutation == "fabricated":
        prepared = object.__new__(PreparedWorldBackend)
    elif mutation == "foreign":
        with pytest.raises(ValueError):
            shared.install(prepared, lineage=None)
    elif mutation == "used":
        owner.validate_prepared(prepared, lineage=None)
        owner.install(prepared, lineage=None)
    after_mutation = _live_evidence(owner)
    ambient = _ambient()
    with pytest.raises(ValueError):
        owner.install(prepared, lineage=None)
    _equal(after_mutation, _live_evidence(owner))
    _equal(ambient, _ambient())


def test_successive_current_resets_and_exact_private_restore(private_rnd: PrivateRND) -> None:
    rig, owner = private_rnd, private_rnd.owner
    saved = owner.snapshot(lineage=None)
    position = 3
    for count in (1, 2):
        current = owner._rng.snapshot()
        reference = WorldRNGState.from_snapshot(current, descriptor=rig.descriptor, world_id="R0-current", cuda_devices=())
        with reference.activate("model_init"):
            rig.factory(reference)
        prepared = owner.prepare_learning_reset(factory=rig.factory, prepare_native=_reset_rnd, lineage=None)
        owner.install(prepared, lineage=None)
        _equal(reference._components, owner._rng._components)
        position += count
        owner.call(lambda backend, sources: _service(backend, sources, _rows(count, rig.width, position * 7), position), lineage=None)
    ambient = _ambient()
    prepared = owner.prepare_restore(
        saved, factory=rig.factory, validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
    )
    owner.install(prepared, lineage=None)
    restored = _live_evidence(owner)
    _equal(saved["backend"], restored["native"])
    _equal(saved["rng"]["components"], restored["rng_components"])
    _equal(ambient, _ambient())


def test_shared_reset_retains_factory_draws_restore_preserves_peer_current(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]]
) -> None:
    shared, factory = shared_rnd
    shared.call(lambda backend: backend.admit_and_service(_rows(3, private_rnd.width, 1), vector_tick=0), lineage=None)
    saved = shared.snapshot(lineage=None)
    before_native = _native_evidence(shared._backend)
    entry = _ambient()
    fresh = factory()  # independent sole-thread reference; this direct route remains unenrolled
    expected_rng = _ambient()
    fresh_native = fresh.checkpoint_state()
    _restore_ambient(entry)
    domain = process_rng_domain()
    with domain.operation(participant=shared.rng_participant, operation_kind="prepare", lineage=None) as operation:
        private_prepared = private_rnd.owner.prepare_learning_reset(
            factory=private_rnd.factory, prepare_native=_reset_rnd, lineage=operation
        )
        prepared = shared.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=operation)
        _equal(entry, _ambient())
        _equal(before_native, _native_evidence(shared._backend))
        private_rnd.owner.install(private_prepared, lineage=operation)
        shared.install(prepared, lineage=operation)
    _equal(expected_rng, _ambient())
    reset = shared._backend.checkpoint_state()
    _equal(fresh_native["predictor_network"], reset["predictor_network"])
    _equal(saved["backend"]["predictor_service"]["pending_observations"], reset["predictor_service"]["pending_observations"])
    assert reset["predictor_service"]["optimizer_epoch_origin"] == 1
    shared.call(lambda backend: (random.random(), np.random.random(), torch.rand(3)), lineage=None)
    peer_current = _ambient()
    prepared = shared.prepare_restore(
        saved, factory=factory, validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
    )
    shared.install(prepared, lineage=None)
    _equal(peer_current, _ambient())
    _equal(_ambient_next(peer_current), _ambient_next(_ambient()))
    _equal(saved["backend"], shared._backend.checkpoint_state())


@pytest.mark.parametrize("boundary", ["factory", "native", "capture", "stage", "post_constructor_capture", "partial_stage", "verify"])
def test_shared_prepublication_refusal_preserves_live_owner(
    shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], monkeypatch: pytest.MonkeyPatch, boundary: str
) -> None:
    shared, factory = shared_rnd
    before, ambient, revision = _native_evidence(shared._backend), _ambient(), shared._revision

    def refuse(*args: Any) -> Any:
        raise RuntimeError("injected owned boundary refusal")

    original_globals, original_install = world_state._globals, world_state._install_globals
    constructed: list[RNDExploration] = []
    injected: list[str] = []

    def actual_factory() -> RNDExploration:
        result = factory()
        constructed.append(result)
        return result

    def capture(devices: tuple[int, ...]) -> dict[str, Any]:
        state = original_globals(devices)
        if constructed and not injected:
            injected.append(boundary)
            raise RuntimeError("injected post-constructor capture refusal")
        return state

    def partial_install(state: dict[str, Any]) -> None:
        torch.set_rng_state(state["torch_cpu"])
        random.setstate(state["python"])
        assert not torch.equal(ambient["torch_cpu"], torch.get_rng_state())
        injected.append(boundary)
        raise RuntimeError("injected partial setter refusal")

    def installed(state: dict[str, Any]) -> None:
        original_install(state)
        injected.append("installed")

    def verify(devices: tuple[int, ...]) -> dict[str, Any]:
        state = original_globals(devices)
        if injected == ["installed"]:
            injected.append("verification")
            state["python"] = random.Random(991).getstate()
        return state

    with monkeypatch.context() as patch:
        if boundary == "capture":
            patch.setattr(world_state, "_globals", refuse)
        elif boundary == "post_constructor_capture":
            patch.setattr(world_state, "_globals", capture)
        with pytest.raises(RuntimeError, match="verify" if boundary == "verify" else "injected"):
            prepared = shared.prepare_learning_reset(
                factory=refuse if boundary == "factory" else actual_factory,
                prepare_native=refuse if boundary == "native" else _reset_rnd,
                lineage=None,
            )
            if boundary == "stage":
                patch.setattr(world_state, "_install_globals", refuse)
            elif boundary == "partial_stage":
                patch.setattr(world_state, "_install_globals", partial_install)
            elif boundary == "verify":
                patch.setattr(world_state, "_install_globals", installed)
                patch.setattr(world_state, "_globals", verify)
            if boundary in {"stage", "partial_stage", "verify"}:
                shared.install(prepared, lineage=None)
    if boundary in {"post_constructor_capture", "partial_stage", "verify"}:
        assert len(constructed) == 1 and injected
    _equal(before, _native_evidence(shared._backend))
    _equal(ambient, _ambient())
    assert shared._revision == revision and shared._failed is False
    assert process_rng_domain().status()[2] is False


def test_independent_real_cpu_adam_step_completes_during_private_activation(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]]
) -> None:
    independent, _ = shared_rnd
    independent.call(lambda backend: backend.admit_and_service(_rows(2, private_rnd.width, 5), vector_tick=0), lineage=None)
    backend = independent._backend  # caller quiescence for this separately owned raw reference
    before = backend.checkpoint_state()
    errors: list[BaseException] = []

    def step() -> None:
        try:
            backend.optimizer.step()  # no global gate: exact already-qualified CPU profile
        except BaseException as error:
            errors.append(error)

    def holding(native: RNDExploration, sources: WorldRandomSources) -> None:
        ambient = _ambient()
        worker = threading.Thread(target=step)
        worker.start()
        worker.join(20)
        assert not worker.is_alive(), "qualified independent Adam core was incorrectly globally gated"
        assert not errors
        _equal(ambient, _ambient())

    private_rnd.owner.call(holding, lineage=None)
    after = backend.checkpoint_state()
    assert all(state["step"].item() == 2 for state in after["optimizer"]["state"].values())
    assert any(not torch.equal(value, after["predictor_network"][name]) for name, value in before["predictor_network"].items())
    assert after["predictor_service"]["optimizer_updates"] == 1
    assert after["predictor_service"]["optimizer_step_offset"] == 1


def _record_spawn_identity() -> bool:
    names = ("BAC_QUAL_ROOT", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_MANIFEST", "BAC_QUAL_OUTPUT")
    if not any(name in os.environ for name in names):
        return False
    assert all(name in os.environ for name in names)
    from bac_source_identity import pytest_configure

    pytest_configure(SimpleNamespace(workerinput={"workerid": "poison"}))
    receipt = Path(os.environ["BAC_QUAL_OUTPUT"]) / "identity-poison.json"
    destination = receipt.with_name("spawn-identity-poison.json")
    if destination.exists():
        raise FileExistsError(destination)
    identity = json.loads(receipt.read_text())
    identity.update(
        pid=os.getpid(),
        manifest_sha256=hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
        debug=__debug__,
        interop_threads=torch.get_num_interop_threads(),
        imports={
            name: str(Path(module.__file__).resolve())
            for name, module in {"world_curiosity_state": world_state, "rng_custody": custody_module, "rnd": rnd_module}.items()
        },
    )
    receipt.write_text(json.dumps(identity, sort_keys=True, indent=2) + "\n")
    receipt.rename(destination)
    return True


def _poison_worker(
    policy: dict[str, Any],
    private_policy: dict[str, Any],
    descriptor: dict[str, Any],
    rng: dict[str, Any],
    width: int,
    actions: int,
    output: Any,
) -> None:
    try:
        qualified = _record_spawn_identity()
        resolved = ResolvedExplorationPolicy.from_dict(policy)
        private_resolved = ResolvedExplorationPolicy.from_dict(private_policy)
        private_descriptor = WorldCuriosityDescriptor.from_dict(descriptor)

        def factory() -> RNDExploration:
            return make_backend(resolved, world_id=None, obs_dim=width, action_dim=actions, device="cpu", rng=None, descriptor=None)

        shared = SharedWorldBackend.construct(factory=factory, cuda_devices=())
        private_rng = WorldRNGState.from_snapshot(rng, descriptor=private_descriptor, world_id="R0-current", cuda_devices=())

        def private_factory(candidate: WorldRNGState) -> Any:
            return make_backend(
                private_resolved,
                world_id="R0-current",
                obs_dim=width,
                action_dim=actions,
                device="cpu",
                rng=candidate,
                descriptor=private_descriptor,
            )

        private = OwnedWorldBackend.construct(rng=private_rng, factory=private_factory)
        private.call(lambda backend, sources: _service(backend, sources, _rows(3, width, 1), 3), lineage=None)
        prepared = shared.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=None)

        def failed_install(state: Any) -> None:
            raise RuntimeError("candidate staging failed")

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(world_state, "_install_globals", failed_install)
            patch.setattr(world_state, "_restore_globals", lambda state: [RuntimeError("entry cleanup failed")])
            with pytest.raises(BaseExceptionGroup):
                shared.install(prepared, lineage=None)
        assert process_rng_domain().status()[2] is True
        with pytest.raises(RuntimeError, match="poisoned"):
            shared.call(lambda backend: torch.rand(1), lineage=None)
        with pytest.raises(RuntimeError, match="poisoned"):
            private.call(lambda backend, sources: _service(backend, sources, _rows(1, width, 11), 4), lineage=None)
        with pytest.raises(RuntimeError, match="poisoned"):
            with private._rng.activate("service"):
                torch.rand(1)
        with pytest.raises(RuntimeError, match="poisoned"):
            WorldRNGState.from_snapshot(
                rng, descriptor=WorldCuriosityDescriptor.from_dict(descriptor), world_id="R0-current", cuda_devices=()
            )
        output.put(("poisoned shared/private fail closed", os.getpid(), qualified))
    except BaseException as error:
        output.put(repr(error))
        raise


def test_cleanup_poison_isolated_in_fresh_process(private_rnd: PrivateRND, compiled: Any) -> None:
    selected = compiled.get_level(compiled.metadata.primary_level)
    context = multiprocessing.get_context("spawn")
    output = context.Queue()
    process = context.Process(
        target=_poison_worker,
        args=(
            _resolved_rnd(selected, "shared").to_dict(),
            _resolved_rnd(selected, "per_world").to_dict(),
            private_rnd.descriptor.to_dict(),
            private_rnd.owner._rng.snapshot(),
            private_rnd.width,
            selected.action_metadata.total_actions,
            output,
        ),
    )
    process.start()
    try:
        process.join(90)
        assert not process.is_alive(), "fresh poison control did not finish"
        assert process.exitcode == 0
        receipt = output.get(timeout=5)
        assert receipt[:2] == ("poisoned shared/private fail closed", process.pid)
        assert receipt[2] is ("BAC_QUAL_ROOT" in os.environ)
        assert process.pid is not None and process.pid > 0 and receipt[1] > 0
        if "BAC_QUAL_ROOT" in os.environ:
            assert receipt[2] is True
            observation = Path(os.environ["BAC_QUAL_OUTPUT"]) / "spawn-observation-poison.json"
            if observation.exists():
                raise FileExistsError(observation)
            observation.write_text(
                json.dumps(
                    {
                        "process_pid": process.pid,
                        "queued_pid": receipt[1],
                        "exitcode": process.exitcode,
                        "qualified": receipt[2],
                        "message": receipt[0],
                        "manifest_sha256": hashlib.sha256(Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()).hexdigest(),
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n"
            )
    finally:
        if process.is_alive():
            process.terminate()
            process.join(10)
        output.close()
        output.join_thread()
    assert process_rng_domain().status()[2] is False


def _same_owner_exclusion(private_rnd: PrivateRND, monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    owner = private_rnd.owner
    contended, mutated = threading.Event(), threading.Event()
    domain = process_rng_domain()
    monkeypatch.setattr(domain, "_lock", _ObservedLock(domain._lock, contended))
    errors: list[BaseException] = []

    def mutate() -> None:
        try:
            if mutation == "manual":
                owner.call(lambda backend, sources: backend.optimizer.step(), lineage=None)
            elif mutation == "service":
                owner.call(lambda backend, sources: _service(backend, sources, _rows(1, private_rnd.width, 13), 4), lineage=None)
            else:

                def replace(backend: RNDExploration, sources: WorldRandomSources) -> None:
                    backend.optimizer = torch.optim.Adam(backend.predictor_network.parameters(), lr=0.001)

                owner.call(replace, lineage=None)
            mutated.set()
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=mutate, name="r0-contender")

    def prepare(current: RNDExploration, fresh: RNDExploration) -> None:
        worker.start()
        assert contended.wait(10)
        assert not mutated.is_set()
        _reset_rnd(current, fresh)

    try:
        prepared = owner.prepare_learning_reset(factory=private_rnd.factory, prepare_native=prepare, lineage=None)
    finally:
        if worker.ident is not None:
            worker.join(30)
    assert not worker.is_alive() and not errors and mutated.is_set()
    changed = _live_evidence(owner)
    if mutation == "manual":
        assert changed["native"]["predictor_service"]["optimizer_step_offset"] == 1
    elif mutation == "service":
        assert changed["native"]["predictor_service"]["optimizer_updates"] == 2
    else:
        assert changed["identity"]["optimizer"] != private_rnd.learned["identity"]["optimizer"]
        assert changed["native"]["predictor_service"]["optimizer_step_offset"] == -1
    with pytest.raises(ValueError):
        owner.install(prepared, lineage=None)
    _equal(changed, _live_evidence(owner))


@pytest.mark.parametrize("boundary", ["factory", "native"])
def test_private_candidate_refusal_is_pure(private_rnd: PrivateRND, boundary: str) -> None:
    owner = private_rnd.owner
    before, ambient = _live_evidence(owner), _ambient()

    def refuse(*args: Any) -> Any:
        raise RuntimeError("private candidate refused")

    with pytest.raises(RuntimeError, match="private candidate"):
        owner.prepare_learning_reset(
            factory=refuse if boundary == "factory" else private_rnd.factory,
            prepare_native=refuse if boundary == "native" else _reset_rnd,
            lineage=None,
        )
    _equal(before, _live_evidence(owner))
    _equal(ambient, _ambient())


@pytest.mark.parametrize("binding", ["world_id", "descriptor", "cuda_devices"])
def test_private_restore_refuses_foreign_binding_without_live_effects(private_rnd: PrivateRND, binding: str) -> None:
    owner = private_rnd.owner
    saved = owner.snapshot(lineage=None)
    if binding == "world_id":
        saved["rng"][binding] = "foreign-world"
    elif binding == "descriptor":
        saved["rng"][binding]["training_seed"] += 1
    else:
        saved["rng"][binding] = (0,)
    before, ambient = _live_evidence(owner), _ambient()
    with pytest.raises(ValueError):
        owner.prepare_restore(
            saved, factory=private_rnd.factory, validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
        )
    _equal(before, _live_evidence(owner))
    _equal(ambient, _ambient())


@pytest.mark.parametrize("kind", ["private", "shared"])
def test_failed_live_callback_quarantines_until_explicit_restore(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], kind: str
) -> None:
    owner, factory = (private_rnd.owner, private_rnd.factory) if kind == "private" else shared_rnd
    saved, ambient = owner.snapshot(lineage=None), _ambient()

    def fail(*args: Any) -> None:
        args[0].decay_epsilon()
        torch.rand(3)
        raise RuntimeError("failed actual live callback")

    with pytest.raises(RuntimeError, match="actual live"):
        owner.call(fail, lineage=None)
    assert owner._failed is True
    current_ambient = _ambient()
    if kind == "private":
        _equal(ambient, current_ambient)
    with pytest.raises(RuntimeError, match="quarantined"):
        owner.call(lambda *args: None, lineage=None)
    prepared = owner.prepare_restore(
        saved, factory=factory, validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
    )
    owner.install(prepared, lineage=None)
    assert owner._failed is False
    _equal(saved["backend"], owner._backend.checkpoint_state())
    _equal(current_ambient, _ambient())


def test_same_owner_real_manual_mutation_waits_for_reset_copy_then_stales_preparation(
    private_rnd: PrivateRND, monkeypatch: pytest.MonkeyPatch
) -> None:
    _same_owner_exclusion(private_rnd, monkeypatch, "manual")


@pytest.mark.parametrize("mutation", ["service", "replacement"])
def test_same_owner_service_and_replacement_wait_for_reset_copy(
    private_rnd: PrivateRND, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    _same_owner_exclusion(private_rnd, monkeypatch, mutation)


def _train_shared(owner: SharedWorldBackend, width: int) -> None:
    receipt = owner.call(lambda backend: backend.admit_and_service(_rows(3, width, 3), vector_tick=0), lineage=None)
    assert receipt.optimizer_updates == 1 and receipt.pending_rows == 1


def _shared_live(owner: SharedWorldBackend) -> dict[str, Any]:
    return {**_native_evidence(owner._backend), "revision": owner._revision, "failed": owner._failed, "token": id(owner._token)}


@contextmanager
def _observe_shared_publication(monkeypatch: pytest.MonkeyPatch, owner: SharedWorldBackend) -> Iterator[list[str]]:
    """Observe only the attempted owner's call window; delegate all real work.

    Ambient state is process-wide, so every staging/setter in this otherwise idle
    window matters. Native publication is additionally scoped by owner identity.
    """
    events: list[str] = []
    original_stage, original_install = world_state._stage_ambient, world_state._install_globals
    original_restore = world_state._restore_globals
    original_setattr = SharedWorldBackend.__setattr__

    def stage(state: dict[str, Any], entry: dict[str, Any], operation: RNGOperation) -> None:
        events.append("ambient stage")
        original_stage(state, entry, operation)

    def install(state: dict[str, Any]) -> None:
        events.append("ambient setter")
        original_install(state)

    def restore(state: dict[str, Any]) -> list[BaseException]:
        events.append("ambient restoration setter")
        return original_restore(state)

    def publish(destination: SharedWorldBackend, name: str, value: Any) -> None:
        if destination is owner and name == "_backend":
            events.append("actual destination backend assignment")
        original_setattr(destination, name, value)

    with monkeypatch.context() as patch:
        patch.setattr(world_state, "_stage_ambient", stage)
        patch.setattr(world_state, "_install_globals", install)
        patch.setattr(world_state, "_restore_globals", restore)
        patch.setattr(SharedWorldBackend, "__setattr__", publish)
        yield events


@pytest.mark.parametrize("schedule", ["before_release", "next_lease"])
@pytest.mark.parametrize("draws", [True, False])
@pytest.mark.parametrize("entrypoint", ["install", "validate_prepared"])
def test_shared_peer_nested_work_stales_across_lease_boundaries(
    private_rnd: PrivateRND,
    shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]],
    schedule: str,
    draws: bool,
    entrypoint: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner, factory = shared_rnd
    peer = SharedWorldBackend.construct(factory=factory, cuda_devices=())
    for current in (owner, peer):
        _train_shared(current, private_rnd.width)
    domain = process_rng_domain()

    def peer_work(backend: RNDExploration) -> None:
        backend.compute_intrinsic_rewards(_rows(1, private_rnd.width, 17), update_stats=False)
        if draws:
            random.random()
            np.random.normal(size=3)
            torch.rand(3)

    def must_refuse(prepared: PreparedWorldBackend, lineage: RNGOperation | None) -> None:
        live = (_shared_live(owner), _shared_live(peer))
        ambient = _ambient()
        method = owner.install if entrypoint == "install" else owner.validate_prepared
        with _observe_shared_publication(monkeypatch, owner) as effects:
            with pytest.raises(ValueError, match="stale|changed|intervening|current|continuation"):
                method(prepared, lineage=lineage)
        assert effects == [], "a stale handle reached ambient staging/setters or actual backend publication before refusal"
        _equal(live, (_shared_live(owner), _shared_live(peer)))
        _equal(ambient, _ambient())
        _equal(_ambient_next(ambient), _ambient_next(_ambient()))

    if schedule == "before_release":
        with domain.operation(participant=owner.rng_participant, operation_kind="prepare", lineage=None) as operation:
            prepared = owner.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=operation)
            before_peer = _ambient()
            peer.call(peer_work, lineage=operation)
            if not draws:
                _equal(before_peer, _ambient())
        must_refuse(prepared, None)
    else:
        prepared = owner.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=None)
        with domain.operation(participant=owner.rng_participant, operation_kind="prepare", lineage=None) as operation:
            before_peer = _ambient()
            peer.call(peer_work, lineage=operation)
            if not draws:
                _equal(before_peer, _ambient())
            must_refuse(prepared, operation)


def test_two_shared_resets_under_held_lease_match_real_sequential_reference(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], monkeypatch: pytest.MonkeyPatch
) -> None:
    first, factory = shared_rnd
    second = SharedWorldBackend.construct(factory=factory, cuda_devices=())
    for owner in (first, second):
        _train_shared(owner, private_rnd.width)
    references = [deepcopy(first._backend), deepcopy(second._backend)]
    entry = _ambient()
    try:
        for reference in references:
            _reset_rnd(reference, factory())  # second real construction starts after the first's actual draws
        expected_ambient = _ambient()
        expected_native = [reference.checkpoint_state() for reference in references]
    finally:
        _restore_ambient(entry)
    assert any(
        not torch.equal(value, expected_native[1]["predictor_network"][name])
        for name, value in expected_native[0]["predictor_network"].items()
    )
    domain = process_rng_domain()
    with domain.operation(participant=first.rng_participant, operation_kind="prepare", lineage=None) as operation:
        prepared_first = first.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=operation)
        prepared_second = second.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=operation)
        first.install(prepared_first, lineage=operation)
        committed = _ambient()
        second_before = _shared_live(second)
        dependency_refused = False
        with _observe_shared_publication(monkeypatch, second) as effects:
            try:
                second.install(prepared_second, lineage=operation)
            except ValueError as error:
                assert any(word in str(error).lower() for word in ("stale", "dependency", "predecessor", "continuation"))
                assert effects == [], "dependency refusal occurred after ambient staging/setters or actual backend publication"
                _equal(committed, _ambient())
                _equal(second_before, _shared_live(second))
                dependency_refused = True
        if dependency_refused:
            prepared_second = second.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=operation)
            second.install(prepared_second, lineage=operation)
    _equal(expected_native, [first._backend.checkpoint_state(), second._backend.checkpoint_state()])
    _equal(expected_ambient, _ambient())
    _equal(_ambient_next(expected_ambient), _ambient_next(_ambient()))


@pytest.mark.parametrize("kind", ["standalone", "private", "raw_private", "shared"])
def test_real_registration_and_native_objects_are_reclaimed_after_drop(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], kind: str
) -> None:
    domain = process_rng_domain()
    for _ in range(2):
        if kind == "shared":
            owner = SharedWorldBackend.construct(factory=shared_rnd[1], cuda_devices=())
            _train_shared(owner, private_rnd.width)
        else:
            rng = WorldRNGState.from_snapshot(
                private_rnd.owner._rng.snapshot(), descriptor=private_rnd.descriptor, world_id="R0-current", cuda_devices=()
            )
            input_reference = weakref.ref(rng)
            if kind == "standalone":
                owner = rng
            else:
                if kind == "raw_private":
                    with rng.activate("model_init"):
                        native = private_rnd.factory(rng)
                    owner = OwnedWorldBackend(native, rng)
                    del native
                else:
                    owner = OwnedWorldBackend.construct(rng=rng, factory=private_rnd.factory)
                owner.call(lambda backend, sources: _service(backend, sources, _rows(3, private_rnd.width, 1), 3), lineage=None)
            del rng
        participant = owner.rng_participant
        references = [weakref.ref(owner)]
        if kind != "shared":
            references.append(input_reference)
        if kind != "standalone":
            references.extend(weakref.ref(item) for item in (owner._backend, owner._backend.predictor_network, owner._backend.optimizer))
            if kind in {"private", "raw_private"}:
                references.append(weakref.ref(owner._rng))
        generation = domain.status()[0]
        del owner
        gc.collect()
        assert all(reference() is None for reference in references), "the process registration retained discarded real owner/native state"
        with pytest.raises(ValueError):
            with domain.operation(participant=participant, operation_kind="rng" if kind == "standalone" else "call", lineage=None):
                pytest.fail("discarded owner membership remained usable")
        assert domain.status()[0] > generation


def test_active_operation_pins_real_owner_and_forbids_early_retirement(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]]
) -> None:
    owner = SharedWorldBackend.construct(factory=shared_rnd[1], cuda_devices=())
    participant, reference = owner.rng_participant, weakref.ref(owner)
    domain = process_rng_domain()
    with domain.operation(participant=participant, operation_kind="call", lineage=None) as operation:
        del owner
        gc.collect()
        assert reference() is not None
        with pytest.raises(RuntimeError, match="idle"):
            domain.unregister(participant=participant)
        result = reference().call(
            lambda backend: backend.compute_intrinsic_rewards(_rows(1, private_rnd.width, 5), update_stats=False), lineage=operation
        )
        assert result.shape == (1,)
    del result
    gc.collect()
    assert reference() is None


def test_real_shared_constructor_blocks_private_service_and_preserves_serialized_continuation(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = shared_rnd[1]
    reference_native = deepcopy(private_rnd.owner._backend)
    reference_rng = WorldRNGState.from_snapshot(
        private_rnd.owner._rng.snapshot(), descriptor=private_rnd.descriptor, world_id="R0-current", cuda_devices=()
    )
    entry = _ambient()
    try:
        expected_shared = factory().checkpoint_state()
        expected_ambient = _ambient()
        with reference_rng.activate("service") as sources:
            expected_service = _service(reference_native, sources, _rows(1, private_rnd.width, 41), 4)
    finally:
        _restore_ambient(entry)
    contended, serviced = threading.Event(), threading.Event()
    actual_service: list[dict[str, Any]] = []
    errors: list[BaseException] = []
    domain = process_rng_domain()
    monkeypatch.setattr(domain, "_lock", _ObservedLock(domain._lock, contended))

    def private_work() -> None:
        try:
            actual_service.append(
                private_rnd.owner.call(
                    lambda backend, sources: _service(backend, sources, _rows(1, private_rnd.width, 41), 4), lineage=None
                )
            )
            serviced.set()
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=private_work, name="r0-contender")

    def held_factory() -> RNDExploration:
        actual = factory()  # real constructor consumption precedes the contention witness
        worker.start()
        assert contended.wait(10)
        assert not serviced.is_set()
        _equal(expected_ambient, _ambient())
        return actual

    try:
        actual_shared = SharedWorldBackend.construct(factory=held_factory, cuda_devices=())
    finally:
        if worker.ident is not None:
            worker.join(30)
    assert not worker.is_alive() and not errors and serviced.is_set()
    _equal(expected_shared, actual_shared._backend.checkpoint_state())
    _equal(expected_service, actual_service[0])
    _equal(reference_native.checkpoint_state(), private_rnd.owner._backend.checkpoint_state())
    _equal(reference_rng._components, private_rnd.owner._rng._components)
    _equal(expected_ambient, _ambient())
    _equal(_ambient_next(expected_ambient), _ambient_next(_ambient()))


def test_cpu_core_does_not_query_cuda_while_library_health_check_remains_available(
    private_rnd: PrivateRND, shared_rnd: tuple[SharedWorldBackend, Callable[[], RNDExploration]], monkeypatch: pytest.MonkeyPatch
) -> None:
    class NoProjectCUDA:
        def __getattr__(self, name: str) -> Any:
            raise AssertionError(f"CPU project core accessed CUDA.{name}")

    class ProjectTorch:
        cuda = NoProjectCUDA()

        def __getattr__(self, name: str) -> Any:
            return getattr(torch, name)

    # Replace only WS's module binding. Installed Torch keeps its real CUDA object,
    # so the pinned public Adam health check is neither removed nor misattributed.
    monkeypatch.setattr(world_state, "torch", ProjectTorch())
    monkeypatch.setattr(custody_module, "torch", ProjectTorch())
    rig = private_rnd
    rng = WorldRNGState.from_snapshot(rig.owner._rng.snapshot(), descriptor=rig.descriptor, world_id="R0-current", cuda_devices=())
    owner = OwnedWorldBackend.construct(rng=rng, factory=rig.factory)
    owner.call(lambda backend, sources: _service(backend, sources, _rows(3, rig.width, 9), 3), lineage=None)
    prepared = owner.prepare_learning_reset(factory=rig.factory, prepare_native=_reset_rnd, lineage=None)
    owner.install(prepared, lineage=None)
    saved = owner.snapshot(lineage=None)
    prepared = owner.prepare_restore(
        saved, factory=rig.factory, validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
    )
    owner.install(prepared, lineage=None)
    shared = SharedWorldBackend.construct(factory=shared_rnd[1], cuda_devices=())
    _train_shared(shared, rig.width)
    saved_shared = shared.snapshot(lineage=None)
    prepared = shared.prepare_learning_reset(factory=shared_rnd[1], prepare_native=_reset_rnd, lineage=None)
    shared.install(prepared, lineage=None)
    prepared = shared.prepare_restore(
        saved_shared, factory=shared_rnd[1], validate_backend=lambda backend, state: backend.validate_state(state), lineage=None
    )
    shared.install(prepared, lineage=None)


def test_private_post_factory_capture_refusal_keeps_current_owner_healthy(private_rnd: PrivateRND, monkeypatch: pytest.MonkeyPatch) -> None:
    owner = private_rnd.owner
    before, ambient = _live_evidence(owner), _ambient()
    original = world_state._globals
    constructed: list[RNDExploration] = []
    captures: list[str] = []

    def factory(candidate: WorldRNGState) -> RNDExploration:
        backend = private_rnd.factory(candidate)
        constructed.append(backend)
        return backend

    def capture(devices: tuple[int, ...]) -> dict[str, Any]:
        if constructed and not captures:
            captures.append("after genuine private factory")
            raise RuntimeError("injected private candidate capture refusal")
        return original(devices)

    with monkeypatch.context() as patch:
        patch.setattr(world_state, "_globals", capture)
        with pytest.raises(RuntimeError, match="private candidate capture"):
            owner.prepare_learning_reset(factory=factory, prepare_native=_reset_rnd, lineage=None)
    assert len(constructed) == 1 and captures == ["after genuine private factory"]
    _equal(before, _live_evidence(owner))
    _equal(ambient, _ambient())
    assert process_rng_domain().status()[2] is False
