"""Native Adam configuration transport; standalone clocks, not owner authority.

All histories below come from real Adam steps or native service.  The independent
oracle keys live optimizer state by model Parameter identity, never archive IDs.
Root runs this file under source custody; importing it does not run a compiler.
"""

from __future__ import annotations

import random
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.provider_factory import make_backend
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.world_curiosity_state import ServiceClock, WorldCuriosityDescriptor, WorldRNGState
from townlet.universe.compiler import UniverseCompiler

FAMILIES = ("rnd", "adaptive_rnd", "icm")
SCOPES = ("shared", "per_world")
RND_FAMILIES = ("rnd", "adaptive_rnd")


@pytest.fixture(scope="session")
def compiled_native_level() -> Any:
    repository = Path(__file__).resolve().parents[4]
    compiled = UniverseCompiler().compile(repository / "configs/test/token_set_smoke", primary_level="L0_test", use_cache=False)
    return compiled.get_level("L0_test")


@dataclass
class NativeRig:
    backend: Any
    policy: Any
    obs_dim: int
    action_dim: int
    rng: Any
    descriptor: Any


@dataclass(eq=False)
class IdentityObservation:
    """Pin original objects; compare with ``is`` only within one live graph."""

    references: dict[str, object]


def _factory(level: Any, family: str, scope: str, *, feature_dim: int = 128) -> NativeRig:
    drive_data = level.drive.intrinsic.model_dump()
    drive_data["strategy"] = family
    drive = IntrinsicStrategyConfig.model_validate(drive_data)
    training_data = deepcopy(level.training.model_dump())
    training_data["replay_buffer"]["batch_size"] = 2
    training_data["intrinsic"]["rnd"]["feature_dim"] = feature_dim
    training_data["intrinsic"]["rnd"]["learning_rate"] = 0.001
    training_data["intrinsic"]["initial_weight"] = 0.4
    training_data["intrinsic"]["survival_window"] = 10
    training_data["intrinsic"]["min_survival_fraction"] = 0.01
    training_data["intrinsic"]["annealing"].update(min_weight=0.01, threshold=100.0, decay_rate=0.9)
    training_data["training_loop"]["max_steps_per_episode"] = 20
    training = TrainingV2Config.model_validate(training_data)
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
    policy = resolve_exploration_policy(drive, training, options)
    obs_dim, action_dim = level.token_spec.total_dims, level.action_metadata.total_actions
    rng = descriptor = world_id = None
    if scope == "per_world":
        world_id = "native-restore-world"
        descriptor = WorldCuriosityDescriptor.from_policy(
            policy, world_ids=(world_id,), observation_dim=obs_dim, action_dim=action_dim, training_seed=7301
        )
        rng = WorldRNGState.create(descriptor=descriptor, world_id=world_id, cuda_devices=())
    backend = make_backend(policy, world_id=world_id, obs_dim=obs_dim, action_dim=action_dim, device="cpu", rng=rng, descriptor=descriptor)
    return NativeRig(backend, policy, obs_dim, action_dim, rng, descriptor)


def _equal(left: Any, right: Any) -> None:
    """Exact owned-tree oracle, including option scalar/container types."""
    assert type(left) is type(right), (type(left), type(right))
    if isinstance(left, IdentityObservation):
        assert left.references.keys() == right.references.keys()
        for name, reference in left.references.items():
            assert reference is right.references[name], f"live identity changed: {name}"
    elif isinstance(left, torch.Tensor):
        assert left.shape == right.shape
        assert left.dtype == right.dtype
        assert left.device == right.device
        assert torch.all((left == right) | (torch.isnan(left) & torch.isnan(right))).item()
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert len(left) == len(right)
        for item, other in zip(left, right, strict=True):
            _equal(item, other)
    elif isinstance(left, np.ndarray):
        assert left.dtype == right.dtype
        assert np.array_equal(left, right)
    else:
        assert left == right


def _native(backend: Any) -> Any:
    return backend.rnd if isinstance(backend, AdaptiveIntrinsicExploration) else backend


def _record(state: dict[str, Any]) -> dict[str, Any]:
    return state["rnd_state"] if "rnd_state" in state else state


def _named(backend: Any) -> dict[str, torch.nn.Parameter]:
    native = _native(backend)
    modules = (
        (("encoder", native.encoder), ("inverse_model", native.inverse_model), ("forward_model", native.forward_model))
        if isinstance(native, ICMExploration)
        else (("predictor_network", native.predictor_network),)
    )
    return {f"{prefix}.{name}": parameter for prefix, module in modules for name, parameter in module.named_parameters()}


def _association(backend: Any) -> list[list[str]]:
    names = {id(parameter): name for name, parameter in _named(backend).items()}
    groups = [[names[id(parameter)] for parameter in group["params"]] for group in _native(backend).optimizer.param_groups]
    flat = [name for group in groups for name in group]
    assert len(flat) == len(set(flat)) == len(names)
    assert set(flat) == set(names.values())
    return groups


def _moments(backend: Any) -> dict[str, Any]:
    optimizer = _native(backend).optimizer
    return {name: deepcopy(optimizer.state.get(parameter, {})) for name, parameter in _named(backend).items()}


def _weights(backend: Any) -> dict[str, torch.Tensor]:
    return {name: parameter.detach().clone() for name, parameter in _named(backend).items()}


def _gradients(backend: Any) -> dict[str, Any]:
    return {name: None if parameter.grad is None else parameter.grad.detach().clone() for name, parameter in _named(backend).items()}


def _modules(backend: Any) -> dict[str, torch.nn.Module]:
    native = _native(backend)
    if isinstance(native, ICMExploration):
        return {"encoder": native.encoder, "inverse_model": native.inverse_model, "forward_model": native.forward_model}
    return {"fixed_network": native.fixed_network, "predictor_network": native.predictor_network}


def _identities(backend: Any) -> IdentityObservation:
    native = _native(backend)
    optimizer = native.optimizer
    references = {
        "backend": backend,
        "native": native,
        "optimizer": optimizer,
        "groups": optimizer.param_groups,
        "state": optimizer.state,
        "defaults": optimizer.defaults,
    }
    for prefix, module in _modules(backend).items():
        for index, submodule in enumerate(module.modules()):
            references[f"{prefix}.module.{index}"] = submodule
        for name, parameter in module.named_parameters(remove_duplicate=False):
            references[f"{prefix}.parameter.{name}"] = parameter
            if parameter.grad is not None:
                references[f"{prefix}.gradient.{name}"] = parameter.grad
    for index, group in enumerate(optimizer.param_groups):
        references[f"group.{index}"] = group
        references[f"group.{index}.params"] = group["params"]
        for position, parameter in enumerate(group["params"]):
            references[f"group.{index}.parameter.{position}"] = parameter
            if parameter.grad is not None:
                references[f"group.{index}.gradient.{position}"] = parameter.grad
    for index, (parameter, moments) in enumerate(optimizer.state.items()):
        references[f"state.{index}.parameter"] = parameter
        references[f"state.{index}.moments"] = moments
    for index, tensor in enumerate(_tensors((optimizer.param_groups, optimizer.state, optimizer.defaults))):
        references[f"optimizer.tensor.{index}"] = tensor
    if isinstance(native, ICMExploration):
        references.update(policy=native.policy, pending=native._pending, counters=native._counters)
        for index, row in enumerate(native._pending):
            references[f"pending.row.{index}"] = row
            for key in ("predecessor", "successor"):
                references[f"pending.row.{index}.{key}"] = row[key]
    else:
        references.update(buffer=native.obs_buffer, reward_rms=native.reward_rms, service_options=native.service_options)
        for index, row in enumerate(native.obs_buffer):
            references[f"buffer.row.{index}"] = row
    if isinstance(backend, AdaptiveIntrinsicExploration):
        references["survival_history"] = backend.survival_history
    return IdentityObservation(references)


def _direct_observe(backend: Any) -> tuple[Any, ...]:
    """No native checkpoint: observe even an intentionally invalid live graph."""
    native = _native(backend)
    optimizer = native.optimizer
    values = {
        "models": {name: module.state_dict() for name, module in _modules(backend).items()},
        "module_training_flags": {
            name: [submodule.training for submodule in module.modules()] for name, module in _modules(backend).items()
        },
        "model_parameter_flags_gradients": {
            prefix: [(name, parameter.requires_grad, parameter.grad) for name, parameter in module.named_parameters(remove_duplicate=False)]
            for prefix, module in _modules(backend).items()
        },
        "optimizer_groups": [
            {key: [id(parameter) for parameter in value] if key == "params" else value for key, value in group.items()}
            for group in optimizer.param_groups
        ],
        "optimizer_state": [(id(parameter), moments) for parameter, moments in optimizer.state.items()],
        "optimizer_defaults": optimizer.defaults,
        "optimizer_parameters": [
            [(id(parameter), parameter.detach(), parameter.requires_grad, parameter.grad) for parameter in group["params"]]
            for group in optimizer.param_groups
        ],
        "common": (
            native.obs_dim,
            native.training_batch_size,
            native.device,
            native.epsilon,
            native.epsilon_min,
            native.epsilon_decay,
            native._service_clock_unit,
            native._service_position,
            native._ordinary_updates_at_position,
            native._optimizer_epoch_origin,
        ),
    }
    if isinstance(native, ICMExploration):
        values["icm"] = (
            native.action_dim,
            native.feature_dim,
            native.hidden_dim,
            native.learning_rate,
            native.inverse_weight,
            native.forward_weight,
            native.max_pending_transitions,
            native._source_device,
            native.policy.to_dict(),
            list(native._pending),
            native._counters,
            native._last_loss,
        )
    else:
        values["rnd"] = (
            native.embed_dim,
            native.obs_buffer,
            native.step_counter,
            None if native.service_options is None else native.service_options.model_dump(),
            native._admitted_rows,
            native._consumed_rows,
            native._dropped_rows,
            native._optimizer_updates,
            native.reward_rms.mean,
            native.reward_rms.var,
            native.reward_rms.count,
        )
    if isinstance(backend, AdaptiveIntrinsicExploration):
        values["adaptive"] = (
            backend.initial_intrinsic_weight,
            backend.current_intrinsic_weight,
            backend.min_intrinsic_weight,
            backend.variance_threshold,
            backend.min_survival_fraction,
            backend.max_episode_length,
            backend.min_survival_for_annealing,
            backend.survival_window,
            backend.decay_rate,
            backend.device,
            backend.survival_history,
        )
    return deepcopy(values), _identities(backend)


def _observe(backend: Any) -> tuple[Any, ...]:
    native = _native(backend)
    if isinstance(native, RNDExploration):
        assert all(not parameter.requires_grad and parameter.grad is None for parameter in native.fixed_network.parameters())
    # Observe before invoking the capture under test; checkpoint_state itself
    # must not be allowed to replace or repair the baseline we intend to retain.
    return _direct_observe(backend), _association(backend)


def _preload_gradients_are_absent(backend: Any) -> None:
    for module in _modules(backend).values():
        assert all(parameter.grad is None for parameter in module.parameters())
    native = _native(backend)
    if isinstance(native, RNDExploration):
        assert all(not parameter.requires_grad for parameter in native.fixed_network.parameters())


def _ambient() -> tuple[Any, ...]:
    return (torch.random.get_rng_state().clone(), random.getstate(), deepcopy(np.random.get_state()))


def _rng_continuation(rig: NativeRig) -> Any:
    return None if rig.rng is None else rig.rng.snapshot()


def _rows(rig: NativeRig, count: int = 3, offset: float = 0.0) -> torch.Tensor:
    return torch.arange(count * rig.obs_dim, dtype=torch.float32).reshape(count, rig.obs_dim).remainder(19).div(19).add(offset)


def _service(rig: NativeRig, *, count: int = 3, offset: float = 0.0) -> Any:
    backend = rig.backend
    state = _record(backend.checkpoint_state())
    clock_state = state if isinstance(backend, ICMExploration) else state["predictor_service"]
    previous = clock_state["service_position"]
    unit = backend.service_clock_unit
    position = (0 if previous is None else previous) + (count if unit == "world_eligible_admission" else 1)
    rows = _rows(rig, count, offset)
    if isinstance(backend, ICMExploration):
        context = IntrinsicTransitionContext(
            predecessor=rows,
            actions=torch.arange(count, dtype=torch.long).remainder(rig.action_dim),
            successor=rows.add(0.125),
            active_on_entry=torch.ones(count, dtype=torch.bool),
            vector_tick=position,
        )
        return backend.admit_and_service_at(context, clock=ServiceClock(unit, position))
    return backend.admit_and_service_at(rows, clock=ServiceClock(unit, position))


def _manual_step(backend: Any) -> None:
    """Distinct dense real gradients make equal-shaped biases distinguishable."""
    optimizer = _native(backend).optimizer
    optimizer.zero_grad(set_to_none=True)
    for index, parameter in enumerate(_named(backend).values()):
        parameter.grad = torch.full_like(parameter, (index + 1) / 100)
    optimizer.step()


def _reordered_names(backend: Any) -> list[str]:
    named = _named(backend)
    names = list(named)
    pair = next(
        (left, right)
        for left in range(len(names))
        for right in range(left + 1, len(names))
        if named[names[left]].shape == named[names[right]].shape
    )
    left, right = pair
    names[left], names[right] = names[right], names[left]
    return names


def _replace_optimizer(backend: Any, *, topology: str = "two", inert: bool = False) -> None:
    native = _native(backend)
    named = _named(backend)
    names = _reordered_names(backend)
    if isinstance(native, ICMExploration):
        groups = [{"params": [named[name] for name in names], "lr": 0.002}]
    elif topology == "empty_first":
        groups = [{"params": [], "lr": 0.0007}, {"params": [named[name] for name in names], "lr": 0.002}]
    elif topology == "empty_last":
        groups = [{"params": [named[name] for name in names], "lr": 0.002}, {"params": [], "lr": 0.0007}]
    elif topology == "one":
        groups = [{"params": [named[name] for name in names], "lr": 0.001}]
    else:
        # Equal-shaped biases cross group boundaries; remaining membership also
        # differs from canonical traversal, not merely the group lengths.
        groups = [
            {"params": [named[name] for name in reversed(names[:4])], "lr": 0.002},
            {"params": [named[name] for name in reversed(names[4:])], "lr": 0.0007},
        ]
    native.optimizer = torch.optim.Adam(groups, lr=0.001)
    if inert:
        for index, group in enumerate(native.optimizer.param_groups):
            group["native_inert_flag"] = index % 2 == 0


def _assert_recipe(backend: Any, state: dict[str, Any]) -> None:
    record = _record(state)
    recipe = record["adam_restore_recipe"]
    assert set(recipe) == {"version", "algorithm", "groups"}
    assert type(recipe["version"]) is int and recipe["version"] == 1
    assert type(recipe["algorithm"]) is str and recipe["algorithm"] == "torch.optim.Adam"
    assert type(recipe["groups"]) is list and recipe["groups"]
    expected_names = _association(backend)
    assert len(recipe["groups"]) == len(expected_names)
    for group, names, payload in zip(recipe["groups"], expected_names, record["optimizer"]["param_groups"], strict=True):
        assert set(group) == {"parameter_names", "options"}
        assert type(group["parameter_names"]) is list
        assert all(type(name) is str for name in group["parameter_names"])
        assert group["parameter_names"] == names
        _equal(group["options"], {key: value for key, value in payload.items() if key != "params"})
    if isinstance(backend, AdaptiveIntrinsicExploration):
        assert "adam_restore_recipe" not in state
        assert state["schema"] == "adaptive-intrinsic-state-v4"
    assert record["schema"] == ("icm-state-v4" if isinstance(backend, ICMExploration) else "rnd-state-v4")
    if not isinstance(backend, ICMExploration):
        assert record["predictor_service"]["version"] == 3


def _restore(source: NativeRig, receiver: NativeRig) -> NativeRig:
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    before_source, before_receiver = _observe(source.backend), _observe(receiver.backend)
    before_rng = _ambient(), _rng_continuation(source), _rng_continuation(receiver)
    receiver_weights = _weights(receiver.backend)
    configured = receiver.backend.with_restore_configuration(state)
    assert configured is not receiver.backend
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
    _equal(_weights(configured), receiver_weights)
    assert not _native(configured).optimizer.state
    _preload_gradients_are_absent(configured)
    configured.validate_state(state)
    configured.load_state(state)
    _equal(configured.checkpoint_state(), state)
    _equal(_moments(configured), _moments(source.backend))
    _equal(_weights(configured), _weights(source.backend))
    assert _association(configured) == _association(source.backend)
    _assert_recipe(configured, configured.checkpoint_state())
    for name, parameter in _named(configured).items():
        assert parameter is not _named(source.backend)[name]
        assert parameter is not _named(receiver.backend)[name]
        assert parameter.data_ptr() != _named(source.backend)[name].data_ptr()
        assert parameter.data_ptr() != _named(receiver.backend)[name].data_ptr()
    return NativeRig(configured, receiver.policy, receiver.obs_dim, receiver.action_dim, receiver.rng, receiver.descriptor)


def _next_equivalent(source: NativeRig, restored: NativeRig) -> None:
    _equal(_moments(source.backend), _moments(restored.backend))
    _equal(_weights(source.backend), _weights(restored.backend))
    _equal(_service(source, count=2, offset=0.375), _service(restored, count=2, offset=0.375))
    _equal(_moments(source.backend), _moments(restored.backend))
    _equal(_weights(source.backend), _weights(restored.backend))
    _equal(source.backend.checkpoint_state(), restored.backend.checkpoint_state())
    if isinstance(source.backend, ICMExploration):
        rows = _rows(source, 2, 0.25)
        context = IntrinsicTransitionContext(
            predecessor=rows,
            actions=torch.zeros(2, dtype=torch.long),
            successor=rows.add(0.125),
            active_on_entry=torch.ones(2, dtype=torch.bool),
            vector_tick=100,
        )
        _equal(
            source.backend.compute_transition_novelty(context, update_stats=False),
            restored.backend.compute_transition_novelty(context, update_stats=False),
        )
    else:
        _equal(
            source.backend.compute_intrinsic_rewards(_rows(source, 2), update_stats=False),
            restored.backend.compute_intrinsic_rewards(_rows(source, 2), update_stats=False),
        )


def _profile(source: NativeRig, fresh: NativeRig, profile: str, *, topology: str = "two", inert: bool = False) -> None:
    if profile == "retained_origin":
        _service(source)
        source.backend.install_state(source.backend.prepare_learning_reset(fresh=fresh.backend))
        service = _record(source.backend.checkpoint_state())["predictor_service"]
        assert service["optimizer_epoch_origin"] == service["optimizer_updates"] > 0
    if profile == "negative_delta":
        _service(source)
    _replace_optimizer(source.backend, topology=topology, inert=inert)
    if profile == "positive_delta":
        _manual_step(source.backend)
    if profile != "empty":
        _service(source)
    if isinstance(source.backend, AdaptiveIntrinsicExploration):
        for _ in range(10):
            source.backend.update_on_episode_end(8.0)
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    service = _record(state)["predictor_service"]
    expected_delta = {"empty": 0, "learned": 0, "positive_delta": 1, "negative_delta": -1, "retained_origin": 0}[profile]
    assert service["optimizer_step_offset"] == expected_delta


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_native_factory_learning_baseline(compiled_native_level: Any, scope: str, family: str) -> None:
    """Healthy current-v3 control: real resolved factory and actual native work."""
    rig = _factory(compiled_native_level, family, scope, feature_dim=4)
    rig.backend.validate_state(rig.backend.checkpoint_state())
    receipt = _service(rig)
    assert receipt.optimizer_updates == 1
    assert any(_moments(rig.backend).values())
    state = rig.backend.checkpoint_state()
    rig.backend.validate_state(state)
    copy = deepcopy(rig.backend)
    copy.load_state(state)
    _equal(copy.checkpoint_state(), state)
    _equal(_moments(copy), _moments(rig.backend))


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("profile", ("empty", "learned", "positive_delta", "negative_delta", "retained_origin"))
def test_rnd_two_group_restore_configuration(compiled_native_level: Any, scope: str, profile: str) -> None:
    source, receiver, fresh = [_factory(compiled_native_level, "rnd", scope) for _ in range(3)]
    _profile(source, fresh, profile)
    with pytest.raises(ValueError):
        receiver.backend.validate_state(source.backend.checkpoint_state())
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("profile", ("empty", "learned", "positive_delta", "negative_delta", "retained_origin"))
def test_adaptive_two_group_restore_configuration(compiled_native_level: Any, scope: str, profile: str) -> None:
    source, receiver, fresh = [_factory(compiled_native_level, "adaptive_rnd", scope) for _ in range(3)]
    _profile(source, fresh, profile)
    with pytest.raises(ValueError):
        receiver.backend.validate_state(source.backend.checkpoint_state())
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("learned", (False, True))
@pytest.mark.parametrize("reordered", (False, True))
def test_icm_changed_lr_restore_configuration(compiled_native_level: Any, scope: str, learned: bool, reordered: bool) -> None:
    source, receiver = [_factory(compiled_native_level, "icm", scope) for _ in range(2)]
    if reordered:
        _replace_optimizer(source.backend)
    else:
        source.backend.optimizer.param_groups[0]["lr"] = 0.002
    if learned:
        _service(source)
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    assert state["config"]["learning_rate"] == 0.001
    assert state["optimizer"]["param_groups"][0]["lr"] == 0.002
    with pytest.raises(ValueError):
        receiver.backend.validate_state(state)
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
def test_existing_decoder_refuses_same_shape_association_mismatch(compiled_native_level: Any, scope: str) -> None:
    """Causal RED on existing API: v3 silently accepts swapped bias moments.

    No new method or schema assertion precedes the discriminator.  Both graphs
    have one group, identical serialized IDs/options and equal-shaped swapped
    biases, while dense real gradients give each bias a distinct moment history.
    """
    source, receiver = [_factory(compiled_native_level, "rnd", scope) for _ in range(2)]
    _replace_optimizer(source.backend, topology="one")
    _manual_step(source.backend)
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    assert _association(source.backend) != _association(receiver.backend)
    assert state["optimizer"]["param_groups"] == receiver.backend.checkpoint_state()["optimizer"]["param_groups"]
    # Correct direct load must refuse before touching a differently paired graph.
    before = _observe(receiver.backend)
    with pytest.raises(ValueError):
        receiver.backend.load_state(state)
    _equal(_observe(receiver.backend), before)


@pytest.mark.parametrize("scope", SCOPES)
def test_existing_decoder_next_update_cannot_use_misassociated_moments(compiled_native_level: Any, scope: str) -> None:
    """Execute the v3 silent-load failure through a real next native update.

    The strict loader can refuse the inconsistent candidate.  If it accepts, this
    witness executes service before asserting by-name moments and weights, so RED
    reports the actual numerical consequence rather than only a missing refusal.
    """
    source, receiver = [_factory(compiled_native_level, "rnd", scope) for _ in range(2)]
    _replace_optimizer(source.backend, topology="one")
    _manual_step(source.backend)
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    before = _observe(receiver.backend)
    try:
        receiver.backend.load_state(state)
    except ValueError:
        _equal(_observe(receiver.backend), before)
        return
    before_source_moments, before_receiver_moments = _moments(source.backend), _moments(receiver.backend)
    _service(source, count=2, offset=0.375)
    _service(receiver, count=2, offset=0.375)
    _equal(_moments(source.backend), _moments(receiver.backend))
    _equal(_weights(source.backend), _weights(receiver.backend))
    _equal(before_source_moments, before_receiver_moments)
    pytest.fail("ordinary native load accepted a differently paired candidate; explicit configuration is required")


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_named_same_shape_reorder_preserves_adam_association(compiled_native_level: Any, scope: str, family: str) -> None:
    source, receiver = [_factory(compiled_native_level, family, scope) for _ in range(2)]
    _replace_optimizer(source.backend, topology="one")
    if family != "icm":
        _manual_step(source.backend)
    _service(source)
    named = _named(source.backend)
    same_shape = [(left, right) for left in named for right in named if left != right and named[left].shape == named[right].shape]
    assert same_shape
    moments = _moments(source.backend)
    assert any(not torch.equal(moments[left]["exp_avg"], moments[right]["exp_avg"]) for left, right in same_shape)
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", RND_FAMILIES)
@pytest.mark.parametrize("position", ("empty_first", "empty_last"))
def test_rnd_adaptive_empty_group_preserved(compiled_native_level: Any, scope: str, family: str, position: str) -> None:
    source, receiver, fresh = [_factory(compiled_native_level, family, scope) for _ in range(3)]
    _profile(source, fresh, "learned", topology=position)
    restored = _restore(source, receiver)
    assert [len(group["params"]) for group in _native(restored.backend).optimizer.param_groups] == (
        [0, len(_named(source.backend))] if position == "empty_first" else [len(_named(source.backend)), 0]
    )
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", RND_FAMILIES)
def test_rnd_adaptive_extra_boolean_group_field_preserved(compiled_native_level: Any, scope: str, family: str) -> None:
    source, receiver, fresh = [_factory(compiled_native_level, family, scope) for _ in range(3)]
    _profile(source, fresh, "learned", inert=True)
    restored = _restore(source, receiver)
    assert [group["native_inert_flag"] for group in _native(restored.backend).optimizer.param_groups] == [True, False]
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", RND_FAMILIES)
@pytest.mark.parametrize("settings", ("amsgrad", "tensor_scalars", "numeric_forms", "execution_flags"))
def test_rnd_supported_adam_settings_preserved(compiled_native_level: Any, scope: str, family: str, settings: str) -> None:
    source, receiver = [_factory(compiled_native_level, family, scope) for _ in range(2)]
    _replace_optimizer(source.backend)
    for group in _native(source.backend).optimizer.param_groups:
        if settings == "amsgrad":
            group["amsgrad"] = True
        elif settings == "tensor_scalars":
            group["lr"] = torch.tensor(group["lr"])
            group["eps"] = torch.tensor(1e-8)
            group["weight_decay"] = torch.tensor(0.0)
        elif settings == "numeric_forms":
            group["lr"] = np.float64(group["lr"])
            group["betas"] = [0.8, 0.95]
        else:
            group.update(foreach=False, fused=False, capturable=False, differentiable=False, maximize=True)
    _service(source)
    source.backend.validate_state(source.backend.checkpoint_state())
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
def test_icm_real_optimizer_replacement_keeps_epoch_history(compiled_native_level: Any, scope: str) -> None:
    source, receiver = [_factory(compiled_native_level, "icm", scope) for _ in range(2)]
    _service(source)
    actual_state = source.backend.optimizer.state_dict()
    source.backend.optimizer = torch.optim.Adam(list(_named(source.backend).values()), lr=0.003)
    source.backend.optimizer.load_state_dict(actual_state)
    source.backend.optimizer.param_groups[0]["lr"] = 0.003
    _service(source, offset=0.25)
    source.backend.validate_state(source.backend.checkpoint_state())
    restored = _restore(source, receiver)
    _next_equivalent(source, restored)


MALFORMED = (
    "missing_recipe",
    "old_schema",
    "wrong_algorithm",
    "wrong_version",
    "bool_version",
    "extra_recipe_key",
    "extra_group_key",
    "missing_name",
    "duplicate_name",
    "foreign_name",
    "name_type",
    "names_tuple",
    "duplicate_id",
    "omitted_id",
    "id_type",
    "group_count",
    "name_order",
    "options_value",
    "options_type",
    "options_keys",
    "payload_config_only",
    "payload_option_type",
    "wrong_dimensions",
    "wrong_clock",
    "wrong_origin",
    "incomplete_moments",
    "bad_moment_shape",
    "bad_moment_dtype",
    "negative_variance",
    "nonfinite_moment",
)


def _corrupt(state: dict[str, Any], case: str) -> None:
    record = _record(state)
    recipe = record["adam_restore_recipe"]
    groups = recipe["groups"]
    group = groups[0]
    payload = record["optimizer"]["param_groups"]
    ids = payload[0]["params"]
    history = record["optimizer"]["state"]
    first = ids[0]
    if case == "missing_recipe":
        record.pop("adam_restore_recipe")
    elif case == "old_schema":
        record["schema"] = "icm-state-v3" if record["schema"].startswith("icm") else "rnd-state-v3"
    elif case == "wrong_algorithm":
        recipe["algorithm"] = "torch.optim.AdamW"
    elif case == "wrong_version":
        recipe["version"] = 2
    elif case == "bool_version":
        recipe["version"] = True
    elif case == "extra_recipe_key":
        recipe["defaults"] = {}
    elif case == "extra_group_key":
        group["unexpected"] = True
    elif case == "missing_name":
        group["parameter_names"].pop()
    elif case == "duplicate_name":
        group["parameter_names"][1] = group["parameter_names"][0]
    elif case == "foreign_name":
        group["parameter_names"][0] = "fixed_network.foreign"
    elif case == "name_type":
        group["parameter_names"][0] = 0
    elif case == "names_tuple":
        group["parameter_names"] = tuple(group["parameter_names"])
    elif case == "duplicate_id":
        ids[1] = ids[0]
    elif case == "omitted_id":
        ids.pop()
    elif case == "id_type":
        ids[0] = False
    elif case == "group_count":
        groups.append(deepcopy(group))
    elif case == "name_order":
        group["parameter_names"].reverse()
    elif case == "options_value":
        group["options"]["lr"] *= 2
    elif case == "options_type":
        group["options"]["betas"] = list(group["options"]["betas"])
    elif case == "options_keys":
        group["options"].pop("eps")
    elif case == "payload_config_only":
        payload[0]["lr"] *= 2
    elif case == "payload_option_type":
        payload[0]["betas"] = list(payload[0]["betas"])
    elif case == "wrong_dimensions":
        if "config" in record:
            record["config"]["obs_dim"] += 1
        else:
            record["obs_dim"] += 1
    elif case == "wrong_clock":
        service = record if "config" in record else record["predictor_service"]
        service["service_clock_unit"] = "vector_tick" if service["service_clock_unit"] != "vector_tick" else "world_eligible_admission"
    elif case == "wrong_origin":
        service = record if "config" in record else record["predictor_service"]
        service["optimizer_epoch_origin"] = -1
    elif case == "incomplete_moments":
        history.pop(first)
    elif case == "bad_moment_shape":
        history[first]["exp_avg"] = torch.zeros(1)
    elif case == "bad_moment_dtype":
        history[first]["exp_avg"] = history[first]["exp_avg"].double()
    elif case == "negative_variance":
        history[first]["exp_avg_sq"].fill_(-1)
    elif case == "nonfinite_moment":
        history[first]["exp_avg"].fill_(float("nan"))
    else:
        raise AssertionError(case)


def _refuse_purely(receiver: NativeRig, state: dict[str, Any]) -> None:
    before, before_rng, owned_state = _observe(receiver.backend), (_ambient(), _rng_continuation(receiver)), deepcopy(state)
    with pytest.raises(ValueError):
        receiver.backend.with_restore_configuration(state)
    _equal(_observe(receiver.backend), before)
    _equal((_ambient(), _rng_continuation(receiver)), before_rng)
    _equal(state, owned_state)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("case", MALFORMED)
def test_malformed_restore_configuration_refused(compiled_native_level: Any, scope: str, family: str, case: str) -> None:
    source, receiver = [_factory(compiled_native_level, family, scope) for _ in range(2)]
    _service(source)
    source.backend.validate_state(source.backend.checkpoint_state())
    state = source.backend.checkpoint_state()
    _corrupt(state, case)
    _mixed_gradients(receiver.backend)
    before_source = _observe(source.backend)
    _refuse_purely(receiver, state)
    _equal(_observe(source.backend), before_source)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", RND_FAMILIES)
@pytest.mark.parametrize(
    "case", ("recipe_group_order", "payload_group_order", "nonbool_option", "numeric_initial_lr", "bad_offset", "service_policy")
)
def test_rnd_invalid_group_configuration_refused(compiled_native_level: Any, scope: str, family: str, case: str) -> None:
    source, receiver, fresh = [_factory(compiled_native_level, family, scope) for _ in range(3)]
    _profile(source, fresh, "learned")
    state = source.backend.checkpoint_state()
    record = _record(state)
    if case == "recipe_group_order":
        record["adam_restore_recipe"]["groups"].reverse()
    elif case == "payload_group_order":
        record["optimizer"]["param_groups"].reverse()
    elif case in {"nonbool_option", "numeric_initial_lr"}:
        key = "initial_lr" if case == "numeric_initial_lr" else "native_inert_flag"
        record["optimizer"]["param_groups"][0][key] = 0.1
        record["adam_restore_recipe"]["groups"][0]["options"][key] = 0.1
    elif case == "bad_offset":
        record["predictor_service"]["optimizer_step_offset"] += 1
    else:
        record["predictor_service"]["options"]["max_updates_per_tick"] += 1
    _refuse_purely(receiver, state)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("case", ("extra_group", "empty_history", "manual_displacement", "amsgrad_history", "policy", "loss_without_epoch"))
def test_icm_unsupported_configuration_history_refused(compiled_native_level: Any, scope: str, case: str) -> None:
    source, receiver = [_factory(compiled_native_level, "icm", scope) for _ in range(2)]
    if case == "amsgrad_history":
        source.backend.optimizer.param_groups[0]["amsgrad"] = True
    _service(source)
    if case == "manual_displacement":
        _manual_step(source.backend)
    # A nonportable live history may be refused by capture itself.  Otherwise its
    # exported record must be refused by configuration, without receiver mutation.
    before_source, before_receiver = _direct_observe(source.backend), _direct_observe(receiver.backend)
    before_rng = _ambient(), _rng_continuation(source), _rng_continuation(receiver)
    try:
        state = source.backend.checkpoint_state()
    except ValueError:
        assert case in {"manual_displacement", "amsgrad_history"}
        _equal(_direct_observe(source.backend), before_source)
        _equal(_direct_observe(receiver.backend), before_receiver)
        _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
        return
    if case == "extra_group":
        payload = state["optimizer"]["param_groups"]
        recipe = state["adam_restore_recipe"]["groups"]
        extra, extra_recipe = deepcopy(payload[0]), deepcopy(recipe[0])
        extra["params"] = payload[0]["params"][1:]
        payload[0]["params"] = payload[0]["params"][:1]
        extra_recipe["parameter_names"] = recipe[0]["parameter_names"][1:]
        recipe[0]["parameter_names"] = recipe[0]["parameter_names"][:1]
        payload.append(extra)
        recipe.append(extra_recipe)
    elif case == "empty_history":
        state["optimizer"]["state"] = {}
    elif case == "policy":
        state["policy_identity"] = "unselected-policy"
    elif case == "loss_without_epoch":
        state["optimizer_epoch_origin"] = state["counters"]["optimizer_updates"]
        state["optimizer"]["state"] = {}
        state["last_loss"] = 1.0
    _refuse_purely(receiver, state)


def _tensors(value: Any) -> list[torch.Tensor]:
    if isinstance(value, torch.Tensor):
        return [value]
    if isinstance(value, dict):
        return [tensor for item in value.values() for tensor in _tensors(item)]
    if isinstance(value, (list, tuple)):
        return [tensor for item in value for tensor in _tensors(item)]
    return []


def _mixed_gradients(backend: Any) -> None:
    for index, parameter in enumerate(_named(backend).values()):
        parameter.grad = None if index % 3 == 0 else torch.full_like(parameter, 0.0 if index % 3 == 1 else 0.25)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_capture_and_configuration_are_owned_and_pure(compiled_native_level: Any, scope: str, family: str) -> None:
    source, receiver = [_factory(compiled_native_level, family, scope) for _ in range(2)]
    if family != "icm":
        _native(source.backend).optimizer.param_groups[0]["lr"] = torch.tensor(0.001)
    _service(source)
    _service(receiver, offset=0.5)
    _mixed_gradients(source.backend)
    _mixed_gradients(receiver.backend)
    before_source, before_receiver = _observe(source.backend), _observe(receiver.backend)
    before_rng = _ambient(), _rng_continuation(source), _rng_continuation(receiver)
    exported = source.backend.checkpoint_state()
    record = _record(exported)
    recipe_pointers = {tensor.data_ptr() for tensor in _tensors(record["adam_restore_recipe"]) if tensor.numel()}
    payload_pointers = {tensor.data_ptr() for tensor in _tensors(record["optimizer"]) if tensor.numel()}
    assert not recipe_pointers.intersection(payload_pointers)
    _equal(_observe(source.backend), before_source)
    _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
    configured = receiver.backend.with_restore_configuration(exported)
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _preload_gradients_are_absent(configured)
    second = receiver.backend.with_restore_configuration(exported)
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
    _equal(_weights(configured), _weights(receiver.backend))
    assert not _native(configured).optimizer.state
    _preload_gradients_are_absent(second)
    assert not _native(second).optimizer.state
    configured.load_state(exported)
    second.load_state(exported)
    _equal(configured.checkpoint_state(), exported)
    actual_storages = []
    for backend in (source.backend, receiver.backend, configured, second):
        native = _native(backend)
        tensors = [*_named(backend).values(), *_tensors(native.optimizer.state), *_tensors(native.optimizer.param_groups)]
        if isinstance(native, RNDExploration):
            tensors.extend(native.fixed_network.parameters())
        actual_storages.append({tensor.data_ptr() for tensor in tensors if tensor.numel()})
    for index, storage in enumerate(actual_storages):
        assert all(not storage.intersection(other) for other in actual_storages[index + 1 :])
    snapshots = (exported, source.backend.checkpoint_state(), configured.checkpoint_state(), second.checkpoint_state())
    pointers = [{tensor.data_ptr() for tensor in _tensors(snapshot) if tensor.numel()} for snapshot in snapshots]
    for index, storage in enumerate(pointers):
        assert all(not storage.intersection(other) for other in pointers[index + 1 :])
    # Mutating exported tensors/options cannot mutate the source or either load.
    configured_before, second_before = configured.checkpoint_state(), second.checkpoint_state()
    for tensor in _tensors(exported):
        if tensor.is_floating_point():
            tensor.add_(1)
    _record(exported)["adam_restore_recipe"]["groups"][0]["options"]["lr"] = 99.0
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _equal(configured.checkpoint_state(), configured_before)
    _equal(second.checkpoint_state(), second_before)
    with torch.no_grad():
        next(iter(_named(configured).values())).add_(0.125)
        first_parameter = next(iter(_named(configured).values()))
        _native(configured).optimizer.state[first_parameter]["exp_avg"].add_(0.125)
    _native(configured).optimizer.param_groups[0]["lr"] = 0.009
    _equal(second.checkpoint_state(), second_before)
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_gradients_attach_after_final_copy_to_final_named_parameters(compiled_native_level: Any, scope: str, family: str) -> None:
    source, receiver = [_factory(compiled_native_level, family, scope) for _ in range(2)]
    _replace_optimizer(source.backend)
    _service(source)
    restored = _restore(source, receiver)
    # The final ownership copy precedes all attachment.  No load or copy follows.
    final = deepcopy(restored.backend)
    _mixed_gradients(source.backend)
    gradients = _gradients(source.backend)
    for name, parameter in _named(final).items():
        gradient = gradients[name]
        parameter.grad = None if gradient is None else gradient.clone()
    _equal(_gradients(final), gradients)
    for group in _native(final).optimizer.param_groups:
        for parameter in group["params"]:
            assert any(parameter is named for named in _named(final).values())
    if isinstance(_native(final), RNDExploration):
        assert all(parameter.grad is None for parameter in _native(final).fixed_network.parameters())
    final_rig = NativeRig(final, restored.policy, restored.obs_dim, restored.action_dim, restored.rng, restored.descriptor)
    _next_equivalent(source, final_rig)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
@pytest.mark.parametrize("graph", ("foreign", "missing", "duplicate", "alias", "subclass"))
def test_capture_refuses_nonportable_parameter_graph(compiled_native_level: Any, scope: str, family: str, graph: str) -> None:
    rig = _factory(compiled_native_level, family, scope)
    _service(rig)
    if isinstance(rig.backend, AdaptiveIntrinsicExploration):
        rig.backend.update_on_episode_end(8.0)
    _mixed_gradients(rig.backend)
    native = _native(rig.backend)
    original_optimizer = native.optimizer
    parameters = list(_named(rig.backend).values())
    if graph == "foreign":
        foreign = torch.nn.Parameter(torch.zeros_like(parameters[-1]))
        native.optimizer = torch.optim.Adam([*parameters[:-1], foreign], lr=0.001)
    elif graph == "missing":
        native.optimizer = torch.optim.Adam(parameters[:-1], lr=0.001)
    elif graph == "duplicate":
        # Alter an actual already-constructed Adam group, avoiding upstream
        # constructor warnings as the expected failure mechanism.
        native.optimizer.param_groups[0]["params"].append(parameters[-1])
    elif graph == "alias":
        module = native.encoder if isinstance(native, ICMExploration) else native.predictor_network
        module.register_parameter("duplicate_parameter_alias", parameters[0])
    else:

        class AdamSubclass(torch.optim.Adam):
            pass

        native.optimizer = AdamSubclass(parameters, lr=0.001)
    if native.optimizer is not original_optimizer:
        # Retain actual earned history for surviving Parameters; foreign/missing
        # coverage remains intentionally invalid. No history or clock is invented.
        for group in native.optimizer.param_groups:
            for parameter in group["params"]:
                if parameter in original_optimizer.state:
                    native.optimizer.state[parameter] = deepcopy(original_optimizer.state[parameter])
    before_source, before_rng = _direct_observe(rig.backend), (_ambient(), _rng_continuation(rig))
    with pytest.raises(ValueError):
        rig.backend.checkpoint_state()
    _equal(_direct_observe(rig.backend), before_source)
    _equal((_ambient(), _rng_continuation(rig)), before_rng)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("family", FAMILIES)
def test_direct_validation_requires_exact_paired_name_order(compiled_native_level: Any, scope: str, family: str) -> None:
    rig = _factory(compiled_native_level, family, scope)
    _service(rig)
    rig.backend.validate_state(rig.backend.checkpoint_state())
    state = rig.backend.checkpoint_state()
    record = _record(state)
    record["adam_restore_recipe"]["groups"][0]["parameter_names"] = _reordered_names(rig.backend)
    before = _observe(rig.backend)
    for operation in (rig.backend.validate_state, rig.backend.load_state):
        with pytest.raises(ValueError):
            operation(state)
        _equal(_observe(rig.backend), before)


@pytest.mark.parametrize("scope", SCOPES)
def test_adaptive_authored_outer_configuration_stays_selected(compiled_native_level: Any, scope: str) -> None:
    source, receiver = [_factory(compiled_native_level, "adaptive_rnd", scope) for _ in range(2)]
    _service(source)
    state = source.backend.checkpoint_state()
    state["initial_intrinsic_weight"] += 0.1
    _refuse_purely(receiver, state)


class _WireList(list[Any]):
    """Ordinary values with a concrete wire type that must not be erased."""


class _WireTuple(tuple[float, ...]):
    """Beta values remain valid; only the paired container type differs."""


def _wire_observe(state: dict[str, Any]) -> tuple[Any, ...]:
    references: dict[str, object] = {}

    def retain(value: Any, path: str) -> None:
        references[path] = value
        if isinstance(value, dict):
            for index, (key, item) in enumerate(value.items()):
                references[f"{path}.key.{index}"] = key
                retain(item, f"{path}.value.{index}")
        elif isinstance(value, (tuple, list)):
            for index, item in enumerate(value):
                retain(item, f"{path}.item.{index}")
        elif isinstance(value, torch.Tensor) and value.grad is not None:
            references[f"{path}.gradient"] = value.grad

    retain(state, "input")
    flags_and_gradients = []
    for tensor in _tensors(state):
        gradient = None
        if tensor.grad is not None:
            gradient = tensor.grad.detach().clone()
        flags_and_gradients.append((tensor.requires_grad, gradient))
    return deepcopy(state), flags_and_gradients, IdentityObservation(references)


def _ordered_icm_models(state: dict[str, Any]) -> dict[str, Any]:
    owned = deepcopy(state)
    for name in ("encoder", "inverse_model", "forward_model"):
        owned[name] = OrderedDict(owned[name].items())
    return owned


@pytest.mark.parametrize("scope", SCOPES)
def test_icm_plain_tensor_lr_restore_configuration(compiled_native_level: Any, scope: str) -> None:
    """A supported plain Tensor LR must survive raw validation and next work.

    Ordered model mappings are legitimate input, independently of strict recipe
    containers. The selected policy LR remains separate from mutable Adam LR.
    """
    source, receiver = [_factory(compiled_native_level, "icm", scope) for _ in range(2)]
    for rig in (source, receiver):
        rig.backend.optimizer.param_groups[0]["lr"] = torch.tensor(0.002)
    _service(source)
    state = source.backend.checkpoint_state()
    assert state["config"]["learning_rate"] == 0.001
    assert source.policy.provider_parameters["learning_rate"] == 0.001
    assert type(state["optimizer"]["param_groups"][0]["lr"]) is torch.Tensor
    assert type(state["adam_restore_recipe"]["groups"][0]["options"]["lr"]) is torch.Tensor
    ordered = _ordered_icm_models(state)
    source.backend.validate_state(ordered)
    receiver.backend.validate_state(ordered)
    receiver.backend.load_state(ordered)
    _equal(receiver.backend.checkpoint_state(), state)
    _equal(_moments(source.backend), _moments(receiver.backend))
    _next_equivalent(source, receiver)

    state = source.backend.checkpoint_state()
    ordered = _ordered_icm_models(state)
    _mixed_gradients(source.backend)
    _mixed_gradients(receiver.backend)
    before_source, before_receiver, before_input = _observe(source.backend), _observe(receiver.backend), _wire_observe(ordered)
    before_rng = _ambient(), _rng_continuation(source), _rng_continuation(receiver)
    configured = receiver.backend.with_restore_configuration(ordered)
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _equal(_wire_observe(ordered), before_input)
    _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
    _preload_gradients_are_absent(configured)
    assert not configured.optimizer.state
    configured.validate_state(ordered)
    configured.load_state(ordered)
    _equal(configured.checkpoint_state(), state)
    _equal(_moments(configured), _moments(source.backend))
    restored = NativeRig(configured, receiver.policy, receiver.obs_dim, receiver.action_dim, receiver.rng, receiver.descriptor)
    _next_equivalent(source, restored)


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("operation", ("configuration", "validate", "load"))
@pytest.mark.parametrize("case", ("parameter_lr", "recipe_dict", "groups_list", "group_dict", "options_dict", "betas_tuple"))
def test_icm_raw_restore_wire_types_refused(compiled_native_level: Any, scope: str, operation: str, case: str) -> None:
    """Raw types must be rejected before CPU ownership can normalize them."""
    source, receiver = [_factory(compiled_native_level, "icm", scope) for _ in range(2)]
    for rig in (source, receiver):
        if case == "parameter_lr":
            rig.backend.optimizer.param_groups[0]["lr"] = torch.tensor(0.002)
        else:
            rig.backend.optimizer.param_groups[0]["lr"] = 0.002
    _service(source)
    state = source.backend.checkpoint_state()
    source.backend.validate_state(state)
    receiver.backend.validate_state(state)
    operations = {
        "configuration": receiver.backend.with_restore_configuration,
        "validate": receiver.backend.validate_state,
        "load": receiver.backend.load_state,
    }
    # Prove this exact operation accepts the genuine compatible baseline before
    # changing only the raw wire type. A fixture/LR rejection is not the RED.
    accepted = operations[operation](state)
    if operation == "configuration":
        _preload_gradients_are_absent(accepted)
        assert not accepted.optimizer.state
        accepted.validate_state(state)
    elif operation == "load":
        _equal(receiver.backend.checkpoint_state(), state)
    group = state["adam_restore_recipe"]["groups"][0]
    if case == "parameter_lr":
        payload_lr = state["optimizer"]["param_groups"][0]["lr"]
        assert type(payload_lr) is torch.Tensor
        group["options"]["lr"] = torch.nn.Parameter(payload_lr.detach().clone(), requires_grad=False)
    elif case == "recipe_dict":
        state["adam_restore_recipe"] = OrderedDict(state["adam_restore_recipe"].items())
    elif case == "groups_list":
        state["adam_restore_recipe"]["groups"] = _WireList(state["adam_restore_recipe"]["groups"])
    elif case == "group_dict":
        state["adam_restore_recipe"]["groups"][0] = OrderedDict(group.items())
    elif case == "options_dict":
        group["options"] = OrderedDict(group["options"].items())
    else:
        group["options"]["betas"] = _WireTuple(group["options"]["betas"])
        assert type(state["optimizer"]["param_groups"][0]["betas"]) is tuple
    _mixed_gradients(source.backend)
    _mixed_gradients(receiver.backend)
    before_source, before_receiver, before_input = _observe(source.backend), _observe(receiver.backend), _wire_observe(state)
    before_rng = _ambient(), _rng_continuation(source), _rng_continuation(receiver)
    with pytest.raises(ValueError):
        operations[operation](state)
    _equal(_observe(source.backend), before_source)
    _equal(_observe(receiver.backend), before_receiver)
    _equal(_wire_observe(state), before_input)
    _equal((_ambient(), _rng_continuation(source), _rng_continuation(receiver)), before_rng)
