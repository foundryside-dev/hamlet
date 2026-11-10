"""Actual factory producer contract; no bank/update isolation claim is made here."""

from __future__ import annotations

import importlib
import random
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, ResolvedExplorationPolicy, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.count_based import CountExploration
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.exploration.world_curiosity_state import OwnedWorldBackend, WorldCuriosityDescriptor, WorldRNGState

FAMILIES = ("none", "rnd", "adaptive_rnd", "count_based", "icm")
CLASSES = (EpsilonGreedyExploration, RNDExploration, AdaptiveIntrinsicExploration, CountExploration, ICMExploration)
OBS_DIM = 7
ACTION_DIM = 3
SEED = 42


def _factory() -> Any:
    try:
        module = importlib.import_module("townlet.exploration.provider_factory")
    except ModuleNotFoundError as error:
        if error.name != "townlet.exploration.provider_factory":
            raise
        pytest.fail("PW03 requires the actual backend factory module")
    assert callable(getattr(module, "make_backend", None)), "PW03 requires make_backend"
    assert callable(getattr(module, "make_policy_selector", None)), "PW03 requires independent make_policy_selector"
    return module


def _policy(strategy: str, scope: str, *, feature_dim: int = 5) -> ResolvedExplorationPolicy:
    level = Path("configs/test/token_set_smoke/levels/L0_test")
    training_payload = yaml.safe_load((level / "training.yaml").read_text())["training"]
    training_payload["replay_buffer"]["batch_size"] = 2
    training_payload["intrinsic"]["rnd"]["feature_dim"] = feature_dim
    training_payload["intrinsic"]["rnd"]["learning_rate"] = 0.003
    drive_payload = yaml.safe_load((level / "drive.yaml").read_text())["drive"]["intrinsic"]
    drive_payload["strategy"] = strategy
    options = BaCOptions.model_validate(
        {
            "curiosity_scope": {"scope": scope, "seed_policy": "world_id_derived_v1" if scope == "per_world" else "legacy_shared_v1"},
            "rnd": {
                "service_mode": "paced_fifo",
                "max_updates_per_tick": 1,
                "max_pending_rows": 4,
                "overflow_policy": "service_before_admit",
            },
            "providers": {
                "icm": {
                    "feature_dim": feature_dim,
                    "hidden_dim": 9,
                    "learning_rate": 0.004,
                    "inverse_weight": 0.6,
                    "forward_weight": 0.4,
                    "training_batch_size": 2,
                    "max_pending_transitions": 4,
                },
                "count_based": {"quantization_width": 0.125, "max_entries": 3},
            },
        }
    )
    return resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive_payload), TrainingV2Config.model_validate(training_payload), options
    )


def _descriptor(
    policy: ResolvedExplorationPolicy, *, world_ids: tuple[str, ...] = ("alpha", "beta"), obs_dim: int = OBS_DIM, training_seed: int = SEED
) -> WorldCuriosityDescriptor:
    return WorldCuriosityDescriptor.from_policy(
        policy, world_ids=world_ids, observation_dim=obs_dim, action_dim=ACTION_DIM, training_seed=training_seed
    )


def _rng(descriptor: WorldCuriosityDescriptor, world_id: str) -> WorldRNGState:
    return WorldRNGState.create(descriptor=descriptor, world_id=world_id, cuda_devices=())


def _arguments(policy: ResolvedExplorationPolicy, *, world_id: str = "alpha") -> dict[str, Any]:
    descriptor = None
    rng = None
    selected_id = None
    if policy.curiosity_scope == "per_world":
        descriptor = _descriptor(policy)
        rng = _rng(descriptor, world_id)
        selected_id = world_id
    return {"world_id": selected_id, "obs_dim": OBS_DIM, "action_dim": ACTION_DIM, "device": "cpu", "rng": rng, "descriptor": descriptor}


def _equal(left: Any, right: Any) -> None:
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor)
        assert left.dtype == right.dtype and left.shape == right.shape and left.device == right.device
        assert torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray)
        assert left.dtype == right.dtype and np.array_equal(left, right)
    elif isinstance(left, dict):
        assert isinstance(right, dict) and left.keys() == right.keys()
        for key in left:
            _equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert type(left) is type(right) and len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            _equal(a, b)
    else:
        assert left == right


def _ambient() -> dict[str, Any]:
    return {"torch": torch.get_rng_state().clone(), "python": random.getstate(), "numpy": deepcopy(np.random.get_state())}


def _models(backend: Any, strategy: str) -> tuple[torch.nn.Module, ...]:
    if strategy == "adaptive_rnd":
        return backend.rnd.fixed_network, backend.rnd.predictor_network
    if strategy == "rnd":
        return backend.fixed_network, backend.predictor_network
    if strategy == "icm":
        return backend.encoder, backend.inverse_model, backend.forward_model
    return ()


def _optimizer(backend: Any, strategy: str) -> Any:
    return backend.rnd.optimizer if strategy == "adaptive_rnd" else backend.optimizer


def test_factory_fixture_prerequisites() -> None:
    """Root runs this before RED so resolver/YAML failures cannot masquerade as RED."""
    for strategy in FAMILIES:
        for scope in ("shared", "per_world"):
            policy = _policy(strategy, scope)
            assert policy.strategy == strategy and policy.curiosity_scope == scope
            if scope == "per_world":
                descriptor = _descriptor(policy)
                rng = _rng(descriptor, "alpha")
                restored = WorldRNGState.from_snapshot(rng.snapshot(), descriptor=descriptor, world_id="alpha", cuda_devices=())
                _equal(restored.snapshot(), rng.snapshot())


@pytest.mark.parametrize("strategy,expected_class", zip(FAMILIES, CLASSES, strict=True))
@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_factory_reuses_all_five_backends(strategy: str, expected_class: type, scope: str) -> None:
    policy = _policy(strategy, scope)
    backend = _factory().make_backend(policy, **_arguments(policy))
    assert type(backend) is expected_class
    state = backend.checkpoint_state()
    epsilon_state = state
    if strategy == "adaptive_rnd":
        epsilon_state = state["rnd_state"]
        for key in (
            "initial_intrinsic_weight",
            "min_intrinsic_weight",
            "variance_threshold",
            "min_survival_fraction",
            "max_episode_length",
            "survival_window",
            "decay_rate",
        ):
            assert state[key] == getattr(policy, key)
    assert epsilon_state["epsilon"] == policy.epsilon_start
    assert epsilon_state["epsilon_min"] == policy.epsilon_end
    assert epsilon_state["epsilon_decay"] == policy.epsilon_decay
    if strategy in ("rnd", "adaptive_rnd"):
        rnd = backend.rnd if strategy == "adaptive_rnd" else backend
        assert rnd.obs_dim == OBS_DIM and rnd.embed_dim == policy.rnd_feature_dim
        assert rnd.training_batch_size == policy.predictor_batch_size
        assert rnd.optimizer.param_groups[0]["lr"] == policy.rnd_learning_rate
        assert rnd.service_options.model_dump() == {
            key: getattr(policy, key) for key in ("service_mode", "max_updates_per_tick", "max_pending_rows", "overflow_policy")
        }
        assert rnd.fixed_network(torch.ones(2, OBS_DIM)).shape == (2, policy.rnd_feature_dim)
        assert rnd.predictor_network(torch.ones(2, OBS_DIM)).shape == (2, policy.rnd_feature_dim)
        assert all(not parameter.requires_grad for parameter in rnd.fixed_network.parameters())
        assert all(parameter.requires_grad for parameter in rnd.predictor_network.parameters())
    if strategy == "icm":
        assert state["policy_identity"] == policy.policy_identity
        assert state["config"] == {"obs_dim": OBS_DIM, "action_dim": ACTION_DIM, **dict(policy.provider_parameters), "device": "cpu"}
        assert backend.optimizer.param_groups[0]["lr"] == policy.provider_parameters["learning_rate"]
    if strategy == "count_based":
        reference = CountExploration(policy, **dict(policy.provider_parameters), device="cpu")
        _equal(state, reference.checkpoint_state())
        # Actual selected quantization/LRU effect, without guessing native key names.
        backend.compute_intrinsic_rewards(torch.tensor([[0.01] * OBS_DIM, [0.02] * OBS_DIM]), update_stats=True)
        repeated = backend.compute_intrinsic_rewards(torch.tensor([[0.01] * OBS_DIM]), update_stats=False)
        fresh = backend.compute_intrinsic_rewards(torch.tensor([[1.01] * OBS_DIM]), update_stats=False)
        assert repeated.item() < fresh.item()
    if strategy in ("rnd", "adaptive_rnd", "icm"):
        assert backend.service_clock_unit == policy.service_clock_unit
    if strategy == "icm":
        context = IntrinsicTransitionContext(
            predecessor=torch.ones(2, OBS_DIM),
            actions=torch.tensor([0, ACTION_DIM - 1], dtype=torch.long),
            successor=torch.full((2, OBS_DIM), 0.5),
            active_on_entry=torch.tensor([True, True]),
            vector_tick=0,
        )
        before = backend.checkpoint_state()
        rewards = backend.compute_transition_novelty(context, update_stats=False)
        assert rewards.shape == (2,) and torch.isfinite(rewards).all()
        _equal(backend.checkpoint_state(), before)
    else:
        assert backend.compute_intrinsic_rewards(torch.ones(2, OBS_DIM), update_stats=False).shape == (2,)


@pytest.mark.parametrize("strategy", FAMILIES)
def test_private_factory_returns_disjoint_mutable_instances(strategy: str) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    first = factory.make_backend(policy, **_arguments(policy, world_id="alpha"))
    second = factory.make_backend(policy, **_arguments(policy, world_id="beta"))
    assert first is not second
    before_second = second.checkpoint_state()
    first.decay_epsilon()
    _equal(second.checkpoint_state(), before_second)
    for left, right in zip(_models(first, strategy), _models(second, strategy), strict=True):
        assert left is not right
        for a, b in zip(left.parameters(), right.parameters(), strict=True):
            assert a is not b and a.data_ptr() != b.data_ptr()
        assert any(not torch.equal(a, b) for a, b in zip(left.parameters(), right.parameters(), strict=True))
    if strategy in ("rnd", "adaptive_rnd", "icm"):
        left_opt, right_opt = _optimizer(first, strategy), _optimizer(second, strategy)
        assert left_opt is not right_opt and left_opt.state is not right_opt.state
        assert left_opt.param_groups is not right_opt.param_groups
        assert left_opt.param_groups[0] is not right_opt.param_groups[0]
        assert left_opt.param_groups[0]["params"] is not right_opt.param_groups[0]["params"]
    if strategy in ("rnd", "adaptive_rnd"):
        left = first.rnd if strategy == "adaptive_rnd" else first
        right = second.rnd if strategy == "adaptive_rnd" else second
        assert left.obs_buffer is not right.obs_buffer and left.reward_rms is not right.reward_rms
        left.compute_intrinsic_rewards(torch.ones(1, OBS_DIM), update_stats=True)
    elif strategy == "count_based":
        first.compute_intrinsic_rewards(torch.ones(1, OBS_DIM), update_stats=True)
    if strategy == "adaptive_rnd":
        assert first.survival_history is not second.survival_history
        first.update_on_episode_end(123.0)
    _equal(second.checkpoint_state(), before_second)


@pytest.mark.parametrize("strategy", FAMILIES)
def test_private_same_id_ignores_ambient_order_and_spectators(strategy: str) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    original_arguments = _arguments(policy)
    ambient_before = _ambient()
    original = factory.make_backend(policy, **original_arguments)
    _equal(_ambient(), ambient_before)
    # All ambient generators really move; private construction must ignore them.
    torch.rand(19)
    random.random()
    np.random.random(17)
    for ids in (("beta", "alpha"), ("spectator", "alpha", "beta")):
        descriptor = _descriptor(policy, world_ids=ids)
        factory.make_backend(
            policy,
            world_id="beta",
            obs_dim=OBS_DIM,
            action_dim=ACTION_DIM,
            device="cpu",
            rng=_rng(descriptor, "beta"),
            descriptor=descriptor,
        )
        # Actual owner retains original roster: stable binding must allow caller spectator changes.
        rng = _rng(_descriptor(policy), "alpha")
        ambient_before = _ambient()
        repeated = factory.make_backend(
            policy, world_id="alpha", obs_dim=OBS_DIM, action_dim=ACTION_DIM, device="cpu", rng=rng, descriptor=descriptor
        )
        _equal(_ambient(), ambient_before)
        _equal(original.checkpoint_state(), repeated.checkpoint_state())
        _equal(original_arguments["rng"].snapshot()["components"], rng.snapshot()["components"])


@pytest.mark.parametrize(
    "strategy,case",
    [
        (strategy, case)
        for strategy in FAMILIES
        for case in (
            "missing_rng",
            "missing_descriptor",
            "wrong_id",
            "wrong_rng_id",
            "wrong_provider",
            "wrong_obs",
            "wrong_action",
            "wrong_seed",
            "wrong_devices",
        )
    ]
    + [(strategy, "wrong_config") for strategy in FAMILIES if strategy != "none"],
)
def test_private_binding_refuses_before_draws(strategy: str, case: str, monkeypatch: pytest.MonkeyPatch) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    arguments = _arguments(policy)
    real_rng = arguments["rng"]
    if case == "missing_rng":
        arguments["rng"] = None
    elif case == "missing_descriptor":
        arguments["descriptor"] = None
    elif case == "wrong_id":
        arguments["world_id"] = "unregistered"
    elif case == "wrong_rng_id":
        arguments["rng"] = _rng(arguments["descriptor"], "beta")
    elif case == "wrong_provider":
        other = "icm" if strategy != "icm" else "rnd"
        arguments["descriptor"] = _descriptor(_policy(other, "per_world"))
    elif case == "wrong_config":
        payload = policy.to_dict()
        if strategy in ("rnd", "adaptive_rnd"):
            payload["rnd_learning_rate"] = 0.007
            payload["provider_parameters"]["learning_rate"] = 0.007
        elif strategy == "icm":
            payload["provider_parameters"]["hidden_dim"] = 13
        else:
            payload["provider_parameters"]["max_entries"] = 5
        policy = ResolvedExplorationPolicy.from_dict(payload)
    elif case == "wrong_obs":
        arguments["obs_dim"] = OBS_DIM + 1
    elif case == "wrong_action":
        arguments["action_dim"] = ACTION_DIM + 1
    elif case == "wrong_seed":
        arguments["descriptor"] = _descriptor(policy, training_seed=SEED + 1)
    elif case == "wrong_devices":
        arguments["device"] = "cuda:0"

    def forbidden_constructor(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("binding must refuse before any selected provider constructor")

    monkeypatch.setattr(CLASSES[FAMILIES.index(strategy)], "__init__", forbidden_constructor)
    rng_before = deepcopy(real_rng.snapshot())
    other_before = arguments["rng"].snapshot() if arguments["rng"] is not None else None
    ambient_before = _ambient()
    with pytest.raises(ValueError):
        factory.make_backend(policy, **arguments)
    _equal(_ambient(), ambient_before)
    _equal(real_rng.snapshot(), rng_before)
    if arguments["rng"] is not None:
        _equal(arguments["rng"].snapshot(), other_before)


@pytest.mark.parametrize("strategy", FAMILIES)
@pytest.mark.parametrize("field,value", (("world_id", "alpha"), ("descriptor", "private"), ("rng", "private")))
def test_shared_requires_explicit_absent_ownership(strategy: str, field: str, value: Any) -> None:
    factory = _factory()
    policy = _policy(strategy, "shared")
    arguments = _arguments(policy)
    private = _arguments(_policy(strategy, "per_world"))
    arguments[field] = private[field] if value == "private" else value
    before = _ambient()
    with pytest.raises(ValueError):
        factory.make_backend(policy, **arguments)
    _equal(_ambient(), before)


@pytest.mark.parametrize("strategy", FAMILIES)
@pytest.mark.parametrize(
    "field,value", (("obs_dim", -1), ("obs_dim", True), ("action_dim", 1.5), ("action_dim", -1), ("device", "meta"), ("device", "cuda"))
)
def test_invalid_geometry_device_refuses_before_draws(strategy: str, field: str, value: Any) -> None:
    policy = _policy(strategy, "per_world")
    arguments = _arguments(policy)
    arguments[field] = value
    before = arguments["rng"].snapshot()
    ambient_before = _ambient()
    with pytest.raises(ValueError):
        _factory().make_backend(policy, **arguments)
    _equal(arguments["rng"].snapshot(), before)
    _equal(_ambient(), ambient_before)


@pytest.mark.parametrize("strategy", FAMILIES)
def test_owned_construction_uses_actual_candidate_rng(strategy: str) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    descriptor = _descriptor(policy)
    original_rng = _rng(descriptor, "alpha")
    original_before = original_rng.snapshot()
    expected_rng = WorldRNGState.from_snapshot(original_before, descriptor=descriptor, world_id="alpha", cuda_devices=())
    expected = factory.make_backend(
        policy, world_id="alpha", obs_dim=OBS_DIM, action_dim=ACTION_DIM, device="cpu", rng=expected_rng, descriptor=descriptor
    )
    observed = []

    def construct(candidate_rng: WorldRNGState) -> Any:
        assert candidate_rng is not original_rng
        backend = factory.make_backend(
            policy, world_id="alpha", obs_dim=OBS_DIM, action_dim=ACTION_DIM, device="cpu", rng=candidate_rng, descriptor=descriptor
        )
        observed.append((candidate_rng, backend))
        return backend

    ambient_before = _ambient()
    owner = OwnedWorldBackend.construct(rng=original_rng, factory=construct)
    assert len(observed) == 1
    _equal(_ambient(), ambient_before)
    _equal(original_rng.snapshot(), original_before)
    _equal(observed[0][1].checkpoint_state(), expected.checkpoint_state())
    envelope = owner.snapshot()
    _equal(envelope["rng"], expected_rng.snapshot())
    _equal(envelope["backend"], expected.checkpoint_state())
    components_before = original_before["components"]
    components_after = expected_rng.snapshot()["components"]
    used = {"rnd": {"target", "predictor"}, "adaptive_rnd": {"target", "predictor"}, "icm": {"model_init", "predictor"}}.get(
        strategy, set()
    )
    for component in components_before:
        if component in used:
            with pytest.raises(AssertionError):
                _equal(components_before[component], components_after[component])
        else:
            _equal(components_before[component], components_after[component])


@pytest.mark.parametrize("strategy", FAMILIES)
def test_global_policy_selector_is_independent_of_private_epsilon(strategy: str) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    selector = factory.make_policy_selector(policy)
    another_selector = factory.make_policy_selector(policy)
    private = factory.make_backend(policy, **_arguments(policy))
    assert type(selector) is EpsilonGreedyExploration
    assert selector is not another_selector and selector is not private
    initial = selector.checkpoint_state()
    assert initial == {"epsilon": policy.epsilon_start, "epsilon_decay": policy.epsilon_decay, "epsilon_min": policy.epsilon_end}
    private.decay_epsilon()
    _equal(selector.checkpoint_state(), initial)
    selector.decay_epsilon()
    assert selector.checkpoint_state()["epsilon"] < initial["epsilon"]
    _equal(another_selector.checkpoint_state(), initial)


@pytest.mark.parametrize("strategy", ("none",))
@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_nonrandom_zero_column_geometry_remains_supported(strategy: str, scope: str) -> None:
    policy = _policy(strategy, scope)
    arguments = _arguments(policy)
    arguments["obs_dim"] = 0
    if scope == "per_world":
        arguments["descriptor"] = _descriptor(policy, obs_dim=0)
        arguments["rng"] = _rng(arguments["descriptor"], "alpha")
    backend = _factory().make_backend(policy, **arguments)
    assert type(backend) is CLASSES[FAMILIES.index(strategy)]
    rewards = backend.compute_intrinsic_rewards(torch.empty(2, 0), update_stats=True)
    assert rewards.shape == (2,) and torch.isfinite(rewards).all()


@pytest.mark.parametrize("strategy", ("rnd", "adaptive_rnd", "icm"))
def test_trainable_zero_width_refuses_before_draws(strategy: str) -> None:
    policy = _policy(strategy, "per_world")
    arguments = _arguments(policy)
    arguments["obs_dim"] = 0
    arguments["descriptor"] = _descriptor(policy, obs_dim=0)
    arguments["rng"] = _rng(arguments["descriptor"], "alpha")
    before = arguments["rng"].snapshot()
    ambient_before = _ambient()
    with pytest.raises(ValueError):
        _factory().make_backend(policy, **arguments)
    _equal(arguments["rng"].snapshot(), before)
    _equal(_ambient(), ambient_before)


@pytest.mark.parametrize("strategy", FAMILIES)
def test_diagnostic_epsilon_does_not_invent_rng_provider_identity(strategy: str) -> None:
    policy = _policy(strategy, "per_world")
    arguments = _arguments(policy)
    payload = policy.to_dict()
    payload["epsilon_decay"] = 0.97
    changed = ResolvedExplorationPolicy.from_dict(payload)
    backend = _factory().make_backend(changed, **arguments)
    state = backend.rnd.checkpoint_state() if strategy == "adaptive_rnd" else backend.checkpoint_state()
    assert state["epsilon_decay"] == 0.97


@pytest.mark.parametrize("strategy", FAMILIES)
def test_active_different_owner_refuses_even_with_identical_binding(strategy: str) -> None:
    factory = _factory()
    policy = _policy(strategy, "per_world")
    arguments = _arguments(policy)
    another = _rng(arguments["descriptor"], "alpha")
    before = arguments["rng"].snapshot()
    another_before = another.snapshot()
    ambient_before = _ambient()
    with another.activate("model_init"):
        with pytest.raises(RuntimeError):
            factory.make_backend(policy, **arguments)
    _equal(arguments["rng"].snapshot(), before)
    _equal(another.snapshot(), another_before)
    _equal(_ambient(), ambient_before)


@pytest.mark.parametrize("scope", ("shared", "per_world"))
def test_count_zero_width_refuses_before_allocation_or_draws(scope: str, monkeypatch: pytest.MonkeyPatch) -> None:
    policy = _policy("count_based", scope)
    arguments = _arguments(policy)
    arguments["obs_dim"] = 0
    if scope == "per_world":
        arguments["descriptor"] = _descriptor(policy, obs_dim=0)
        arguments["rng"] = _rng(arguments["descriptor"], "alpha")
    before = arguments["rng"].snapshot() if arguments["rng"] is not None else None
    ambient_before = _ambient()
    constructor_calls = []

    def forbidden_constructor(*args: Any, **kwargs: Any) -> None:
        constructor_calls.append(True)
        raise AssertionError("zero-width Count must refuse before provider allocation")

    monkeypatch.setattr(CountExploration, "__init__", forbidden_constructor)
    with pytest.raises(ValueError):
        _factory().make_backend(policy, **arguments)
    assert constructor_calls == []
    if arguments["rng"] is not None:
        _equal(arguments["rng"].snapshot(), before)
    _equal(_ambient(), ambient_before)
