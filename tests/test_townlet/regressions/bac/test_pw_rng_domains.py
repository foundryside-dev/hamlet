"""PW02 primitive proof; native provider validation/hooks and bank wiring remain later gates."""

from __future__ import annotations

import copy
import hashlib
import json
import random
import subprocess
import sys
import threading
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pytest
import torch

from townlet.config.bac_options import RNDOptions
from townlet.exploration import world_curiosity_state as ws
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration

KINDS = ("rnd", "icm", "adaptive_rnd")


def _equal(left, right):
    assert type(left) is type(right)
    if isinstance(left, torch.Tensor):
        assert left.dtype == right.dtype and left.shape == right.shape and left.device == right.device
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype and np.array_equal(left, right)
    elif isinstance(left, Mapping):
        assert left.keys() == right.keys()
        for key in left:
            _equal(left[key], right[key])
        if isinstance(left, OrderedDict):
            assert list(left) == list(right)
            assert hasattr(left, "_metadata") == hasattr(right, "_metadata")
            if hasattr(left, "_metadata"):
                _equal(left._metadata, right._metadata)
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _equal(a, b)
    else:
        assert left == right


def _globals(devices):
    return copy.deepcopy(
        (torch.get_rng_state(), random.getstate(), np.random.get_state(), {i: torch.cuda.get_rng_state(i) for i in devices})
    )


@pytest.fixture(autouse=True)
def preserve_test_rng():
    saved = _globals(())
    yield
    torch.set_rng_state(saved[0])
    random.setstate(saved[1])
    np.random.set_state(saved[2])


def _api():
    assert hasattr(ws, "WorldRNGState"), "PW02 missing private WorldRNGState domain"
    assert hasattr(ws, "OwnedWorldBackend"), "PW02 missing OwnedWorldBackend lifecycle"
    return ws.WorldRNGState, ws.OwnedWorldBackend


def _descriptor(kind, ids):
    seeds = {
        world: {
            component: ws.derive_world_seed(training_seed=29, world_id=world, provider_kind=kind, component=component)
            for component in ws.WORLD_SEED_COMPONENTS
        }
        for world in ids
    }
    return ws.WorldCuriosityDescriptor(
        schema_version=1,
        scope="per_world",
        provider_kind=kind,
        provider_parameter_hash=hashlib.sha256(json.dumps(_parameters(kind), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        observation_dim=3,
        action_dim=2,
        world_ids=ids,
        seed_policy="world_id_derived_v1",
        service_clock_unit="world_eligible_admission",
        origin="authored",
        guarantee="world_id_owned_state",
        training_seed=29,
        seeds=seeds,
    )


def _rng(kind, world, ids):
    rng_type, _ = _api()
    return rng_type.create(descriptor=_descriptor(kind, ids), world_id=world, cuda_devices=())


def _parameters(kind):
    if kind == "icm":
        return dict(
            feature_dim=2,
            hidden_dim=5,
            learning_rate=0.03,
            inverse_weight=0.7,
            forward_weight=0.3,
            training_batch_size=2,
            max_pending_transitions=6,
        )
    if kind == "rnd":
        return dict(obs_dim=3, embed_dim=4, training_batch_size=2, learning_rate=0.01)
    return dict(obs_dim=3, embed_dim=4, rnd_training_batch_size=2, rnd_learning_rate=0.01)


def _icm_policy():
    # Root's accepted fixture receipt supplies this genuine authored DATA recipe.
    from townlet.config.bac_options import BaCOptions
    from townlet.config.drive_as_code import IntrinsicStrategyConfig
    from townlet.config.exploration_policy import resolve_exploration_policy
    from townlet.config.training_v2_config import TrainingV2Config

    path = Path(__file__).resolve().parents[2] / "fixtures/bac_curiosity_pre_scope/manifest.json"
    effective = json.loads(path.read_text())["artifacts"][0]["effective_run"]
    training = copy.deepcopy(effective["training"])
    training["population"]["size"] = 3
    training["replay_buffer"].update(batch_size=2, min_size=2, capacity=64)
    training["intrinsic"]["rnd"]["feature_dim"] = 4
    options = {
        "providers": {"icm": _parameters("icm")},
        "rnd": {"service_mode": "paced_fifo", "max_updates_per_tick": 1, "overflow_policy": "service_before_admit"},
        "curiosity_scope": {"scope": "per_world", "seed_policy": "world_id_derived_v1"},
    }
    training["bac_options"] = copy.deepcopy(options)
    drive = copy.deepcopy(effective["exploration"]["authored_parameters"]["drive_intrinsic"])
    drive.update(strategy="icm", icm_config={"feature_dim": 9, "hidden_dim": 11, "learning_rate": 0.001})
    return resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), BaCOptions.model_validate(options)
    )


def _icm_context(observations, tick):
    from townlet.config.exploration_policy import IntrinsicTransitionContext

    return IntrinsicTransitionContext(
        predecessor=observations,
        actions=torch.arange(len(observations), dtype=torch.long) % 2,
        successor=observations + torch.tensor([0.9, -0.2, 0.8]),
        active_on_entry=torch.ones(len(observations), dtype=torch.bool),
        vector_tick=tick,
    )


def _factory(kind, *, service_clock_unit):
    def create(candidate_rng):
        if kind == "rnd":
            backend = RNDExploration(**_parameters(kind), rng=candidate_rng, service_clock_unit=service_clock_unit)
        elif kind == "adaptive_rnd":
            backend = AdaptiveIntrinsicExploration(**_parameters(kind), rng=candidate_rng, service_clock_unit=service_clock_unit)
        else:
            policy = _icm_policy()
            return ICMExploration(
                policy,
                obs_dim=3,
                action_dim=2,
                device="cpu",
                **dict(policy.provider_parameters),
                rng=candidate_rng,
                service_clock_unit=service_clock_unit,
            )
        backend.configure_service(
            RNDOptions(
                service_mode="paced_fifo",
                max_updates_per_tick=1,
                max_pending_rows=4,
                overflow_policy="service_before_admit",
            )
        )
        return backend

    return create


def _draw(sources):
    # Current networks train deterministically: this transparent wrapper exercises RNG consumption.
    return (torch.rand(3), random.gauss(0, 1), sources.python.random(), np.random.normal(size=3), sources.numpy.normal(size=3))


def _exercise(backend, sources, rows, tick, *, clock: ws.ServiceClock):
    draws = _draw(sources)
    observations = torch.tensor([[0.2, -0.7, 1.1], [1.3, 0.4, -0.2]])[:rows]
    if isinstance(backend, ICMExploration):
        context = _icm_context(observations, tick)
        reward = backend.compute_transition_novelty(context, update_stats=True)
        backend.admit_and_service_at(context, clock=clock)
    else:
        reward = backend.compute_intrinsic_rewards(observations, update_stats=True)
        backend.admit_and_service_at(observations, clock=clock)
        if isinstance(backend, AdaptiveIntrinsicExploration):
            backend.update_on_episode_end(200.0 + tick)
    return draws, reward, backend.checkpoint_state()


def _rnd_state(state, kind):
    return state["rnd_state"] if kind == "adaptive_rnd" else state


def _learning_snapshot(value):
    # Preserve native mapping kinds, entry order and recursive Torch metadata,
    # while independently owning the reference snapshot and its leaves.
    return copy.deepcopy(value)


def _assert_learning(before, after, kind, updates, pending):
    old, new = _rnd_state(_learning_snapshot(before), kind), _rnd_state(_learning_snapshot(after), kind)
    assert new["schema"] == ("icm-state-v2" if kind == "icm" else "rnd-state-v2")
    if kind == "adaptive_rnd":
        assert after["schema"] == "adaptive-intrinsic-state-v2"
    model = "encoder" if kind == "icm" else "predictor_network"
    assert any(not torch.equal(old[model][key], value) for key, value in new[model].items())
    moments = new["optimizer"]["state"]
    assert moments and all(float(item["step"]) == updates for item in moments.values())
    assert any(torch.count_nonzero(item["exp_avg"]) > 0 for item in moments.values())
    assert any(torch.count_nonzero(item["exp_avg_sq"]) > 0 for item in moments.values())
    if kind == "icm":
        assert new["counters"]["optimizer_updates"] == updates
        assert new["counters"]["consumed_rows"] == updates * 2
        assert len(new["pending"]) == pending
        assert new["counters"]["admitted_rows"] == updates * 2 + pending + new["counters"]["dropped_rows"]
        service = new
        admitted = new["counters"]["admitted_rows"]
        assert new["counters"]["dropped_rows"] == 0
    else:
        _equal(old["fixed_network"], new["fixed_network"])
        service = new["predictor_service"]
        assert service["optimizer_updates"] == updates and service["consumed_rows"] == updates * 2
        assert len(service["pending_observations"]) == pending
        assert service["admitted_rows"] == updates * 2 + pending + service["dropped_rows"]
        assert service["version"] == 2 and service["optimizer_step_offset"] == 0
        assert service["dropped_rows"] == 0
        assert new["reward_rms_count"] > old["reward_rms_count"]
        admitted = service["admitted_rows"]
    assert 0 <= service["ordinary_updates_at_position"] <= 1
    if service["service_clock_unit"] == "world_eligible_admission":
        assert service["service_position"] == admitted
        if kind != "icm":
            assert service["step_counter"] == 0


def _owner(kind, world, ids):
    _, owned_type = _api()
    return owned_type.construct(rng=_rng(kind, world, ids), factory=_factory(kind, service_clock_unit="world_eligible_admission"))


def _validate_backend(candidate, payload):
    # Validate the complete current native schema without installing candidate state.
    before, transported = copy.deepcopy(candidate.checkpoint_state()), copy.deepcopy(payload)
    candidate.validate_state(payload)
    _equal(before, candidate.checkpoint_state())
    _equal(transported, payload)


def _restore(owner, payload, kind):
    prepared = owner.prepare_restore(
        payload, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
    )
    owner.install(prepared)
    return prepared


def _find(value, key):
    if isinstance(value, Mapping):
        if key in value:
            return value[key]
        for child in value.values():
            result = _find(child, key)
            if result is not None:
                return result
    return None


@pytest.mark.parametrize("kind", KINDS)
def test_private_rng_restores_global_streams(kind):
    # Genuine shared and private learning use their explicitly selected clocks.
    native = _factory(kind, service_clock_unit="vector_tick")(None)
    before = copy.deepcopy(native.checkpoint_state())
    native_sources = type("Sources", (), {"python": random, "numpy": np.random.default_rng(13)})()
    _, reward, after = _exercise(native, native_sources, 2, 0, clock=ws.ServiceClock("vector_tick", 0))
    assert torch.isfinite(reward).all()
    _assert_learning(before, after, kind, 1, 0)
    random.seed(17)
    random.gauss(0, 1)  # Keep a cached Gaussian in the exact global state.
    np.random.seed(19)
    np.random.normal()
    global_before = _globals(())
    rng = _rng(kind, "world1", ("world0", "world1"))
    original_rng = rng.snapshot()
    _, owned_type = _api()
    owner = owned_type.construct(rng=rng, factory=_factory(kind, service_clock_unit="world_eligible_admission"))
    _equal(original_rng, rng.snapshot())
    constructed_rng = owner.snapshot()["rng"]
    used = {"model_init", "predictor"} if kind == "icm" else {"target", "predictor"}
    for component in ws.WORLD_SEED_COMPONENTS:
        before_component = original_rng["components"][component]
        after_component = constructed_rng["components"][component]
        if component in used:
            assert not torch.equal(before_component["torch_cpu"], after_component["torch_cpu"])
            for field in before_component.keys() - {"torch_cpu"}:
                _equal(before_component[field], after_component[field])
        else:
            _equal(before_component, after_component)
    _equal(global_before, _globals(()))
    initial = owner.call(lambda backend, sources: backend.checkpoint_state())
    _, _, tail = owner.call(
        lambda backend, sources: _exercise(backend, sources, 1, 0, clock=ws.ServiceClock("world_eligible_admission", 1))
    )
    tail_state = _rnd_state(tail, kind)
    assert not tail_state["optimizer"]["state"]
    _, _, trained = owner.call(
        lambda backend, sources: _exercise(backend, sources, 1, 1, clock=ws.ServiceClock("world_eligible_admission", 2))
    )
    _assert_learning(initial, trained, kind, 1, 0)
    _equal(global_before, _globals(()))
    saved = owner.snapshot()
    continuation = owner.call(
        lambda backend, sources: _exercise(backend, sources, 2, 2, clock=ws.ServiceClock("world_eligible_admission", 4))
    )
    _restore(owner, saved, kind)
    _equal(global_before, _globals(()))
    replayed = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 2, clock=ws.ServiceClock("world_eligible_admission", 4)))
    _equal(continuation, replayed)
    _assert_learning(initial, replayed[2], kind, 2, 0)
    _equal(global_before, _globals(()))


@pytest.mark.parametrize("kind", KINDS)
def test_world1_rng_independent_of_world0_calls(kind):
    global_before = _globals(())
    baseline = _owner(kind, "world1", ("world1",))
    interleaved = _owner(kind, "world1", ("spectator", "world1", "world0"))
    other = _owner(kind, "world0", ("world0", "world1"))
    _equal(baseline.snapshot(), interleaved.snapshot())
    other_before = other.snapshot()
    admitted_position = 0
    for tick in range(3):
        admitted_position += 2
        expected = baseline.call(
            lambda backend, sources: _exercise(
                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
            )
        )
        other.call(
            lambda backend, sources: _exercise(
                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
            )
        )
        saved_other = other.snapshot()
        _restore(other, saved_other, kind)
        actual = interleaved.call(
            lambda backend, sources: _exercise(
                backend, sources, 2, tick, clock=ws.ServiceClock("world_eligible_admission", admitted_position)
            )
        )
        _equal(expected, actual)
        _equal(baseline.snapshot(), interleaved.snapshot())
    with pytest.raises(AssertionError):
        _equal(other_before, other.snapshot())
    _equal(global_before, _globals(()))


def test_native_global_rng_counterexample_and_private_continuation():
    torch.manual_seed(123)
    state = torch.get_rng_state().clone()
    first = _factory("rnd", service_clock_unit="vector_tick")(None)
    assert not torch.equal(state, torch.get_rng_state())
    second = _factory("rnd", service_clock_unit="vector_tick")(None)
    assert any(
        not torch.equal(a, b) for a, b in zip(first.predictor_network.parameters(), second.predictor_network.parameters(), strict=True)
    )
    rng = _rng("rnd", "world1", ("world1",))
    with rng.activate("service") as sources:
        first_draw = _draw(sources)
    saved = rng.snapshot()
    with rng.activate("service") as sources:
        next_draw = _draw(sources)
    restored = type(rng).from_snapshot(saved, descriptor=_descriptor("rnd", ("world1",)), world_id="world1", cuda_devices=())
    with restored.activate("service") as sources:
        _equal(next_draw, _draw(sources))
    with pytest.raises(AssertionError):
        _equal(first_draw, next_draw)


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("after_update", [False, True])
def test_constructor_compute_failure_restoration_and_quarantine(kind, after_update):
    rng = _rng(kind, "world1", ("world1",))
    _, owned_type = _api()
    global_before = _globals(())

    def broken_factory(private):
        _factory(kind, service_clock_unit="world_eligible_admission")(private)
        with private.activate("model_init") as sources:
            _draw(sources)
        raise KeyboardInterrupt("constructor cancellation")

    with pytest.raises(KeyboardInterrupt, match="constructor cancellation"):
        owned_type.construct(rng=rng, factory=broken_factory)
    _equal(global_before, _globals(()))
    owner = _owner(kind, "world1", ("world1",))
    other = _owner(kind, "world0", ("world0",))
    healthy, unaffected = owner.snapshot(), other.snapshot()
    learner_before = owner.call(lambda backend, sources: backend.checkpoint_state())
    observed = []

    def fail_after_update(backend, sources):
        if after_update:
            observed.append(_learning_snapshot(_exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2))[2]))
        else:
            _draw(sources)
        raise RuntimeError("live callback failure")

    with pytest.raises(RuntimeError, match="live callback failure"):
        owner.call(fail_after_update)
    _equal(global_before, _globals(()))
    _equal(unaffected, other.snapshot())
    diagnostic = owner.snapshot()
    if after_update:
        _assert_learning(learner_before, observed[0], kind, 1, 0)
        model = "encoder" if kind == "icm" else "predictor_network"
        _equal(_rnd_state(observed[0], kind)[model], _find(diagnostic, model))
        _equal(_rnd_state(observed[0], kind)["optimizer"], _find(diagnostic, "optimizer"))
    with pytest.raises(AssertionError):
        _equal(_find(healthy, "components"), _find(diagnostic, "components"))
    with pytest.raises(AssertionError):
        _equal(healthy, diagnostic)
    with pytest.raises((RuntimeError, ValueError), match="quarantin|failed"):
        owner.call(lambda backend, sources: backend.checkpoint_state())
    with pytest.raises((RuntimeError, ValueError)):
        owner.prepare_restore(
            diagnostic, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
        )
    _restore(owner, healthy, kind)
    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
    _equal(global_before, _globals(()))


def _mutate_arrays(value):
    if isinstance(value, torch.Tensor):
        value.fill_(0)
    elif isinstance(value, np.ndarray):
        value.fill(0)
    elif isinstance(value, Mapping):
        for child in value.values():
            _mutate_arrays(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _mutate_arrays(child)


@pytest.mark.parametrize("kind", KINDS)
def test_owned_snapshot_restore_aliases_and_late_load_failure(kind):
    owner = _owner(kind, "world1", ("world1",))
    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 1, clock=ws.ServiceClock("world_eligible_admission", 3)))
    saved = owner.snapshot()
    pristine = copy.deepcopy(saved)
    original_payload = copy.deepcopy(pristine)
    exposed = owner.call(lambda backend, sources: backend.checkpoint_state())
    _mutate_arrays(exposed)
    if kind == "adaptive_rnd":
        exposed["survival_history"].append(9999)
    _equal(pristine, owner.snapshot())
    _mutate_arrays(saved)
    _equal(pristine, owner.snapshot())
    second = _owner(kind, "world1", ("world1", "spectator"))
    prepared = owner.prepare_restore(
        pristine, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
    )
    with pytest.raises((ValueError, RuntimeError)):
        second.install(prepared)
    owner.install(prepared)
    with pytest.raises((ValueError, RuntimeError)):
        owner.install(prepared)
    _restore(second, pristine, kind)
    stable = second.snapshot()
    owner.call(lambda backend, sources: _exercise(backend, sources, 1, 2, clock=ws.ServiceClock("world_eligible_admission", 4)))
    _equal(stable, second.snapshot())
    _equal(original_payload, pristine)
    before, globals_before = owner.snapshot(), _globals(())
    invalid = copy.deepcopy(pristine)
    invalid["unexpected"] = 1
    with pytest.raises((ValueError, TypeError)):
        owner.prepare_restore(
            invalid, factory=_factory(kind, service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
        )
    _equal(before, owner.snapshot())

    def late_factory(rng):
        candidate = _factory(kind, service_clock_unit="world_eligible_admission")(rng)
        real_load = candidate.load_state

        def fail_load(payload):
            real_load(payload)
            torch.rand(2)
            random.gauss(0, 1)
            np.random.normal()
            raise RuntimeError("late candidate load")

        candidate.load_state = fail_load
        return candidate

    def validate_late(candidate, payload):
        # Validate genuine provider data before the intentionally late failing load.
        _validate_backend(candidate, payload)

    with pytest.raises(RuntimeError, match="late candidate load"):
        owner.prepare_restore(pristine, factory=late_factory, validate_backend=validate_late)
    _equal(before, owner.snapshot())
    _equal(globals_before, _globals(()))
    _equal(stable, second.snapshot())


def test_named_substream_recipe_and_activation_bound_python_facade():
    rng = _rng("rnd", "world1", ("world1",))
    descriptor = _descriptor("rnd", ("world1",))

    def derived(suffix):
        return ws.derive_world_seed(training_seed=29, world_id="world1", provider_kind="rnd", component=f"service/{suffix}")

    python = random.Random(derived("python"))
    numpy = np.random.Generator(np.random.PCG64(derived("numpy-pcg64")))
    legacy = np.random.RandomState(derived("numpy-legacy") % 2**32)
    torch_generator = torch.Generator().manual_seed(descriptor.seed_for("world1", "service"))
    expected = (torch.rand(3, generator=torch_generator), python.gauss(0, 1), python.random(), legacy.normal(size=3), numpy.normal(size=3))
    before = _globals(())
    with rng.activate("service") as sources:
        _equal(expected, _draw(sources))
    _equal(before, _globals(()))
    with pytest.raises((RuntimeError, ValueError)):
        sources.python.random()


def test_snapshot_callback_failure_restores_and_quarantines():
    owner = _owner("rnd", "world1", ("world1",))
    healthy, before = owner.snapshot(), _globals(())

    def install_failure(backend, sources):
        def broken_snapshot():
            torch.rand(2)
            random.gauss(0, 1)
            np.random.normal()
            raise RuntimeError("snapshot callback failure")

        backend.checkpoint_state = broken_snapshot

    owner.call(install_failure)
    with pytest.raises(RuntimeError, match="snapshot callback failure"):
        owner.snapshot()
    _equal(before, _globals(()))
    with pytest.raises((RuntimeError, ValueError), match="quarantin|failed"):
        owner.call(lambda backend, sources: 1)
    _restore(owner, healthy, "rnd")
    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
    _equal(before, _globals(()))


def test_invalid_rng_snapshot_is_pure_and_nested_components_resume():
    rng = _rng("rnd", "world1", ("world1",))
    other = _rng("rnd", "world0", ("world0",))
    saved, global_before = rng.snapshot(), _globals(())
    for field, value in (("unexpected", 1), ("world_id", "wrong"), ("components", {}), ("cuda_devices", (0,))):
        malformed = copy.deepcopy(saved)
        malformed[field] = value
        with pytest.raises((ValueError, TypeError)):
            type(rng).from_snapshot(malformed, descriptor=_descriptor("rnd", ("world1",)), world_id="world1", cuda_devices=())
        _equal(saved, rng.snapshot())
        _equal(global_before, _globals(()))
    with rng.activate("service") as sources:
        first = _draw(sources)
        with rng.activate("service") as nested:
            second = _draw(nested)
        with rng.activate("target") as target:
            _draw(target)
        with pytest.raises((ValueError, RuntimeError)):
            with other.activate("service"):
                pytest.fail("cross-owner nested activation entered")
        third = _draw(sources)
    control = type(rng).from_snapshot(saved, descriptor=_descriptor("rnd", ("world1",)), world_id="world1", cuda_devices=())
    with control.activate("service") as sources:
        _equal(first, _draw(sources))
        _equal(second, _draw(sources))
        _equal(third, _draw(sources))
    _equal(global_before, _globals(()))


def test_thread_ownership_serializes_and_releases_after_error():
    first, second = _rng("rnd", "world1", ("world1",)), _rng("rnd", "world0", ("world0",))
    entered, attempting, release, second_entered = (threading.Event() for _ in range(4))
    events, failures = [], []
    global_before = _globals(())

    def a():
        try:
            with first.activate("service"):
                events.append("a-enter")
                entered.set()
                assert release.wait(5)
                events.append("a-exit")
                raise RuntimeError("release test")
        except RuntimeError as error:
            assert str(error) == "release test"
        except BaseException as error:
            failures.append(error)

    def b():
        try:
            assert entered.wait(5)
            attempting.set()
            with second.activate("service") as sources:
                events.append("b-enter")
                second_entered.set()
                _draw(sources)
        except BaseException as error:
            failures.append(error)

    workers = [threading.Thread(target=a, daemon=True), threading.Thread(target=b, daemon=True)]
    for worker in workers:
        worker.start()
    try:
        assert attempting.wait(5)
        assert not second_entered.is_set()
    finally:
        release.set()
        for worker in workers:
            worker.join(5)
    assert not any(worker.is_alive() for worker in workers)
    assert not failures and events == ["a-enter", "a-exit", "b-enter"]
    _equal(global_before, _globals(()))


def test_used_cuda_domain_restoration_when_hardware_available():
    if not torch.cuda.is_available():
        pytest.skip("CUDA private RNG qualification unrun: no supported hardware")
    rng_type, _ = _api()
    torch.cuda.init()
    devices = (torch.cuda.current_device(),)
    before = _globals(devices)
    try:
        rng = rng_type.create(descriptor=_descriptor("rnd", ("world1",)), world_id="world1", cuda_devices=devices)
        with pytest.raises(RuntimeError, match="device callback"):
            with rng.activate("service"):
                torch.rand(3, device=f"cuda:{devices[0]}")
                raise RuntimeError("device callback")
        _equal(before, _globals(devices))
    finally:
        for device, state in before[3].items():
            torch.cuda.set_rng_state(state, device)


def test_restoration_failure_poisoning_isolated_from_pytest():
    _api()
    source = Path(ws.__file__).resolve()
    root = source.parents[3]
    expected_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    expected_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    parent_profile = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "torch_version": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
    }
    script = r"""
import hashlib
import json
import os
import fcntl
import random
import subprocess
import sys
from pathlib import Path
import numpy as np
import torch

source, expected_hash, expected_head, root, encoded_profile = sys.argv[1:]
expected_profile = json.loads(encoded_profile)
torch.set_num_threads(expected_profile["torch_threads"])
torch.set_num_interop_threads(expected_profile["torch_interop_threads"])
actual_profile = {
    "python_executable": sys.executable,
    "python_version": sys.version,
    "torch_version": torch.__version__,
    "torch_threads": torch.get_num_threads(),
    "torch_interop_threads": torch.get_num_interop_threads(),
}
assert actual_profile == expected_profile
sys.path.insert(0, str(Path(root) / "src"))
from townlet.exploration import world_curiosity_state as ws
assert Path(ws.__file__).resolve() == Path(source)
assert hashlib.sha256(Path(ws.__file__).read_bytes()).hexdigest() == expected_hash
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == expected_head
qualification_names = ("BAC_QUAL_MANIFEST", "BAC_QUAL_SHA", "BAC_QUAL_TREE", "BAC_QUAL_ROOT", "BAC_QUAL_OUTPUT")
qualified = any(name in os.environ for name in qualification_names)
def custody():
    assert all(os.environ.get(name) for name in qualification_names), "incomplete qualification environment"
    assert Path(os.environ["BAC_QUAL_ROOT"]).resolve() == Path(root).resolve()
    assert actual_profile["torch_threads"] == 1
    manifest_bytes = Path(os.environ["BAC_QUAL_MANIFEST"]).read_bytes()
    manifest = json.loads(manifest_bytes)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    assert sha == expected_head == os.environ["BAC_QUAL_SHA"] == manifest["base_commit"]
    with (Path(root) / ".superpowers/bac-qualification-index.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            tree = subprocess.check_output(["git", "write-tree"], cwd=root, text=True).strip()
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
    assert tree == os.environ["BAC_QUAL_TREE"] == manifest["candidate_tree"]
    source_hashes = {}
    for relative, expected in manifest["source_files"].items():
        path = Path(root) / relative
        assert path.resolve() == path and path.is_file(), relative
        source_hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        assert source_hashes[relative] == expected, relative
    import_paths = {}
    for name, module in list(sys.modules.items()):
        if name == "townlet" or name.startswith("townlet."):
            filename = getattr(module, "__file__", None)
            if filename is not None:
                path = Path(filename).resolve()
                relative = str(path.relative_to(Path(root)))
                assert relative in source_hashes, (name, relative)
                assert path == Path(root) / "src" / Path(*name.split(".")).with_suffix(".py") or (
                    path == Path(root) / "src" / Path(*name.split(".")) / "__init__.py"
                ), (name, path)
                import_paths[name] = str(path)
    assert import_paths["townlet.exploration.world_curiosity_state"] == source
    return {"pid": os.getpid(), "sha": sha, "candidate_tree": tree, **actual_profile,
            "import_path": str(Path(ws.__file__).resolve()), "import_paths": import_paths,
            "source_hashes": source_hashes, "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest()}
if qualified:
    initial_custody = custody()
seeds = {world: {component: ws.derive_world_seed(training_seed=29, world_id=world, provider_kind="rnd", component=component)
                 for component in ws.WORLD_SEED_COMPONENTS} for world in ("a", "b")}
descriptor = ws.WorldCuriosityDescriptor(
    schema_version=1, scope="per_world", provider_kind="rnd", provider_parameter_hash="a" * 64,
    observation_dim=3, action_dim=2, world_ids=("a", "b"), seed_policy="world_id_derived_v1",
    service_clock_unit="world_eligible_admission", origin="authored", guarantee="world_id_owned_state",
    training_seed=29, seeds=seeds)
first = ws.WorldRNGState.create(descriptor=descriptor, world_id="a", cuda_devices=())
second = ws.WorldRNGState.create(descriptor=descriptor, world_id="b", cuda_devices=())
random.seed(41)
random.gauss(0, 1)
np.random.seed(43)
np.random.normal()
saved_torch, saved_python, saved_numpy = torch.get_rng_state().clone(), random.getstate(), np.random.get_state()
real_torch, real_python, real_numpy = torch.set_rng_state, random.setstate, np.random.set_state
drawn, swaps = [], []
def torch_setter(state):
    swaps.append("torch")
    if drawn and torch.equal(state, saved_torch):
        raise RuntimeError("injected captured Torch restoration failure")
    return real_torch(state)
def python_setter(state):
    swaps.append("python")
    return real_python(state)
def numpy_setter(state):
    swaps.append("numpy")
    return real_numpy(state)
torch.set_rng_state, random.setstate, np.random.set_state = torch_setter, python_setter, numpy_setter
def retains_injected_error(error):
    if "injected captured Torch restoration failure" in str(error):
        return True
    return any(retains_injected_error(item) for item in getattr(error, "exceptions", ())) or (
        error.__cause__ is not None and retains_injected_error(error.__cause__))
try:
    with first.activate("service") as sources:
        torch.rand(3)
        random.gauss(0, 1)
        sources.python.random()
        np.random.normal(size=3)
        sources.numpy.normal(size=3)
        drawn.append(True)
except BaseException as error:
    assert retains_injected_error(error), repr(error)
else:
    raise AssertionError("restoration failure was swallowed")
assert drawn and random.getstate() == saved_python
actual_numpy = np.random.get_state()
assert actual_numpy[0] == saved_numpy[0] and np.array_equal(actual_numpy[1], saved_numpy[1])
assert actual_numpy[2:] == saved_numpy[2:]
before_refusal = list(swaps)
try:
    with second.activate("service"):
        raise AssertionError("unusable coordinator permitted activation")
except (RuntimeError, ValueError) as error:
    assert any(word in str(error).lower() for word in ("unusable", "poison", "failed", "restoration")), str(error)
assert swaps == before_refusal, "refused activation still swapped global streams"
if qualified:
    final_custody = custody()
    assert final_custody == initial_custody
    output = Path(os.environ["BAC_QUAL_OUTPUT"])
    assert output.is_absolute() and output.is_dir()
    receipt = output / f"subprocess-custody-poisoning-{os.getpid()}.json"
    with receipt.open("x") as stream:
        json.dump({**final_custody, "poisoning_assertions_passed": True}, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
print("isolated restoration custody and coordinator refusal verified")
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(source), expected_hash, expected_head, str(root), json.dumps(parent_profile)],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "isolated restoration custody and coordinator refusal verified" in result.stdout


@pytest.mark.parametrize("array_kind", ["plain", "structured"])
def test_object_array_result_does_not_alias_live_adaptive_history(array_kind):
    owner = _owner("adaptive_rnd", "world1", ("world1",))
    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))

    def history_array(backend, sources):
        if array_kind == "plain":
            result = np.empty(1, dtype=object)
            result[0] = backend.survival_history
        else:
            result = np.empty(1, dtype=[("history", object)])
            result["history"][0] = backend.survival_history
        return result

    exported = owner.call(history_array)
    # Compare native history AFTER the callback: wrapper revision changes are irrelevant.
    before_history = owner.call(lambda backend, sources: backend.checkpoint_state())["survival_history"]
    assert before_history and exported.dtype.hasobject
    returned_history = exported[0] if array_kind == "plain" else exported["history"][0]
    returned_history.append(12345.0)
    after_history = owner.call(lambda backend, sources: backend.checkpoint_state())["survival_history"]
    _equal(before_history, after_history)
    assert returned_history == [*before_history, 12345.0]


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("composite_key", [False, True], ids=["native", "tuple"])
def test_learned_adam_mapping_keys_and_values_are_owned(kind, composite_key):
    globals_before = _globals(())
    owner = _owner(kind, "world1", ("world1",))
    control = _owner(kind, "world1", ("world1",))
    initial = owner.call(lambda backend, sources: backend.checkpoint_state())
    _equal(initial, control.call(lambda backend, sources: backend.checkpoint_state()))
    trained = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
    _equal(
        trained,
        control.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2))),
    )
    _assert_learning(initial, trained[2], kind, 1, 0)

    def native_adam_state(backend, sources):
        learner = backend.rnd if kind == "adaptive_rnd" else backend
        state = learner.optimizer.state
        return {("parameter", key): value for key, value in state.items()} if composite_key else state

    exported = owner.call(native_adam_state)
    control.call(native_adam_state)
    assert exported
    key = next(iter(exported))
    parameter = key[1] if composite_key else key
    moments = exported[key]
    assert isinstance(parameter, torch.Tensor)
    assert float(moments["step"]) == 1
    assert torch.count_nonzero(moments["exp_avg"]) > 0
    parameter_before = parameter.detach().clone()
    moment_before = moments["exp_avg"].clone()
    before = owner.snapshot()
    _equal(before, control.snapshot())
    revision_before = owner._revision
    with torch.no_grad():
        parameter.add_(12345)
        moments["exp_avg"].add_(12345)
    assert not torch.equal(parameter_before, parameter)
    assert not torch.equal(moment_before, moments["exp_avg"])
    # No callback or snapshot occurs between this revision capture and comparison.
    assert owner._revision == revision_before
    _equal(before, owner.snapshot())
    _equal(globals_before, _globals(()))
    assert not parameter.requires_grad and parameter.grad_fn is None
    continued = owner.call(lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4)))
    expected = control.call(
        lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4))
    )
    _equal(expected, continued)
    _assert_learning(initial, continued[2], kind, 2, 0)
    _equal(owner.snapshot(), control.snapshot())
    _equal(globals_before, _globals(()))


def test_true_a_b_a_nested_activation_preserves_both_streams():
    rng = _rng("rnd", "world1", ("world1",))
    saved, globals_before = rng.snapshot(), _globals(())
    with rng.activate("service") as a:
        a1 = _draw(a)
        with rng.activate("target") as b:
            b1 = _draw(b)
            with rng.activate("service") as nested_a:
                a2 = _draw(nested_a)
            b2 = _draw(b)
        a3 = _draw(a)
    _equal(globals_before, _globals(()))
    control = type(rng).from_snapshot(saved, descriptor=_descriptor("rnd", ("world1",)), world_id="world1", cuda_devices=())
    with control.activate("service") as a:
        _equal(a1, _draw(a))
        _equal(a2, _draw(a))
        _equal(a3, _draw(a))
    with control.activate("target") as b:
        _equal(b1, _draw(b))
        _equal(b2, _draw(b))
    _equal(control.snapshot(), rng.snapshot())
    _equal(globals_before, _globals(()))


def test_stale_prepared_restore_refuses_after_real_owner_update():
    owner = _owner("rnd", "world1", ("world1",))
    initial = owner.call(lambda backend, sources: backend.checkpoint_state())
    owner.call(lambda backend, sources: _exercise(backend, sources, 2, 0, clock=ws.ServiceClock("world_eligible_admission", 2)))
    prepared = owner.prepare_restore(
        owner.snapshot(), factory=_factory("rnd", service_clock_unit="world_eligible_admission"), validate_backend=_validate_backend
    )
    _, _, updated = owner.call(
        lambda backend, sources: _exercise(backend, sources, 2, 1, clock=ws.ServiceClock("world_eligible_admission", 4))
    )
    _assert_learning(initial, updated, "rnd", 2, 0)
    before, globals_before = owner.snapshot(), _globals(())
    with pytest.raises(ValueError, match="destination changed"):
        owner.install(prepared)
    _equal(updated, owner.call(lambda backend, sources: backend.checkpoint_state()))
    _equal(before, owner.snapshot())
    _equal(globals_before, _globals(()))
