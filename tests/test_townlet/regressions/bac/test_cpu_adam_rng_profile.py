"""Serial CPU optimizer-path qualification; no training, reset, CUDA or constructor-purity claim.

Run family nodes in fresh processes for first-use observations. Never run concurrent
RNG users in this process. The first actual optimizer step is always measured.
A stochastic public step hook must defeat the no-consumption detector.
"""

import hashlib
import os
import random
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.optim.optimizer as optimizer_module

from townlet.agent.optimizer_factory import OptimizerFactory
from townlet.config.bac_options import BaCOptions, resolve_bac_options
from townlet.config.brain_config import apply_training_overrides
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import resolve_exploration_policy
from townlet.exploration.adaptive_intrinsic import AdaptiveIntrinsicExploration
from townlet.exploration.icm import ICMExploration
from townlet.exploration.rnd import RNDExploration
from townlet.universe.compiler import UniverseCompiler

_SOURCE_SEALS = {
    "optimizer.py": (1193, "ea3497233845529a212f81d4d325828eadc20f387ab94b1c21b96057f0001536"),
    "adam.py": (991, "7e5c8482c91b88e355a8bdf1d4b1930e8d961fb99f00c2179946b164a03652b6"),
}


def _capture_rng():
    numpy_state = np.random.get_state()
    return random.getstate(), (numpy_state[0], numpy_state[1].copy(), *numpy_state[2:]), torch.get_rng_state().clone()


def _restore_rng(state):
    random.setstate(state[0])
    np.random.set_state(state[1])
    torch.set_rng_state(state[2])


def _same_rng(left, right):
    a, b = left[1], right[1]
    numpy_equal = a[0] == b[0] and np.array_equal(a[1], b[1]) and a[2:] == b[2:]
    return left[0] == right[0], bool(numpy_equal), torch.equal(left[2], right[2])


def _draw():
    return random.random(), np.random.random_sample(4), torch.rand(4, device="cpu")


def _assert_continuation(before, after):
    try:
        actual = _draw()
        _restore_rng(before)
        reference = _draw()
        assert actual[0] == reference[0]
        np.testing.assert_array_equal(actual[1], reference[1])
        assert torch.equal(actual[2], reference[2])
    finally:
        _restore_rng(after)


def _assert_no_hooks(optimizer):
    assert not optimizer_module._global_optimizer_pre_hooks
    assert not optimizer_module._global_optimizer_post_hooks
    assert not optimizer._optimizer_step_pre_hooks
    assert not optimizer._optimizer_step_post_hooks


@pytest.fixture(autouse=True)
def ambient_custody():
    original = _capture_rng()
    try:
        assert "PYTEST_XDIST_WORKER" not in os.environ, "Use serial fresh-process qualification, without xdist"
        assert sys.getprofile() is None, "Custom Python profiling is outside the admitted profile"
        print(f"CPU_ADAM environment torch={torch.__version__} dynamo_before_setup={'torch._dynamo' in sys.modules}")
        assert torch.__version__ == "2.11.0+cu130"
        for name, expected in _SOURCE_SEALS.items():
            path = Path(torch.__file__).resolve().parent / "optim" / name
            payload = path.read_bytes()
            observed = (len(payload.splitlines()), hashlib.sha256(payload).hexdigest())
            print(f"CPU_ADAM source={path} lines={observed[0]} sha256={observed[1]}")
            assert observed == expected, "Installed source differs from qualified source facts"
        yield
    finally:
        _restore_rng(original)
        assert _same_rng(original, _capture_rng()) == (True, True, True)


@pytest.fixture
def compiled(ambient_custody):
    return UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)


def _construct(family, compiled):
    selected = compiled.get_level(compiled.metadata.primary_level)
    width, actions = selected.token_spec.total_dims, selected.action_metadata.total_actions
    print(f"CPU_ADAM family={family} dynamo_before_constructor={'torch._dynamo' in sys.modules}")
    common = dict(obs_dim=width, device=torch.device("cpu"), rng=None, service_clock_unit="vector_tick")
    if family == "rnd":
        owner = RNDExploration(
            **common,
            embed_dim=8,
            learning_rate=0.001,
            training_batch_size=2,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
        )
        parameters, optimizer = list(owner.predictor_network.parameters()), owner.optimizer
    elif family == "adaptive":
        owner = AdaptiveIntrinsicExploration(
            **common,
            embed_dim=8,
            rnd_learning_rate=0.001,
            rnd_training_batch_size=2,
            initial_intrinsic_weight=1.0,
            min_intrinsic_weight=0.0,
            variance_threshold=100.0,
            min_survival_fraction=0.4,
            max_episode_length=500,
            survival_window=100,
            decay_rate=0.99,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
        )
        parameters, optimizer = list(owner.rnd.predictor_network.parameters()), owner.rnd.optimizer
    elif family == "icm":
        data = resolve_bac_options(selected.training.bac_options, training=selected.training).options.model_dump(exclude_none=True)
        data["curiosity_scope"] = {"scope": "shared", "seed_policy": "legacy_shared_v1"}
        policy = resolve_exploration_policy(
            drive_intrinsic=IntrinsicStrategyConfig(strategy="icm", base_weight=1.0, apply_modifiers=[]),
            training=selected.training,
            options=BaCOptions.model_validate(data),
        )
        provider = dict(policy.provider_parameters)
        assert set(provider) == {
            "feature_dim",
            "hidden_dim",
            "learning_rate",
            "inverse_weight",
            "forward_weight",
            "training_batch_size",
            "max_pending_transitions",
        }
        owner = ICMExploration(policy, **common, action_dim=actions, **provider)
        parameters = [p for module in (owner.encoder, owner.inverse_model, owner.forward_model) for p in module.parameters()]
        optimizer = owner.optimizer
    else:
        assert family == "q_factory"
        brain = apply_training_overrides(compiled.brain, selected.training)
        assert brain.optimizer.type == "adam" and brain.optimizer.schedule.type == "constant"
        assert brain.optimizer.learning_rate == 0.0001 and brain.optimizer.weight_decay == 0.0
        owner = torch.nn.Linear(width, actions, device=torch.device("cpu"))
        parameters = list(owner.parameters())
        optimizer, scheduler = OptimizerFactory.build(config=brain.optimizer, parameters=owner.parameters())
        assert scheduler is None
    print(f"CPU_ADAM family={family} dynamo_after_constructor={'torch._dynamo' in sys.modules}")
    return owner, parameters, optimizer


def _counters(owner):
    if type(owner) in (RNDExploration, AdaptiveIntrinsicExploration):
        return deepcopy(owner.predictor_service_counters())
    if type(owner) is ICMExploration:
        return deepcopy(owner._counters)
    return None  # The Q factory component has no native service counters.


def _profile(parameters, optimizer):
    assert type(optimizer) is torch.optim.Adam
    _assert_no_hooks(optimizer)
    actual = [p for group in optimizer.param_groups for p in group["params"]]
    assert parameters and len(actual) == len(parameters) and len({id(p) for p in actual}) == len(actual)
    assert all(p is q for p, q in zip(actual, parameters, strict=True))
    for p in parameters:
        assert type(p) is torch.nn.Parameter and p.requires_grad
        assert p.device.type == "cpu" and p.dtype == torch.float32 and p.layout == torch.strided and p.numel() > 0
    for group in optimizer.param_groups:
        assert type(group["lr"]) is float and group["lr"] > 0
        assert np.isfinite(group["lr"]) and group["betas"] == (0.9, 0.999) and group["eps"] == 1e-8
        assert group["weight_decay"] == 0.0 and group["foreach"] is None and group["fused"] is None
        for key in ("amsgrad", "maximize", "capturable", "differentiable", "decoupled_weight_decay"):
            assert group[key] is False and optimizer.defaults[key] is False
        print(f"CPU_ADAM actual_group={ {k: v for k, v in group.items() if k != 'params'} }")


def _gradients(parameters, value):
    for p in parameters:
        p.grad = torch.full_like(p, value)
        assert type(p.grad) is torch.Tensor and p.grad.layout == torch.strided and torch.count_nonzero(p.grad) == p.numel()


def _progress(parameters, optimizer, old_parameters, old_moments, step):
    assert len(optimizer.state) == len(parameters)
    for p, previous in zip(parameters, old_parameters, strict=True):
        assert not torch.equal(p, previous) and torch.isfinite(p).all()
        state = optimizer.state[p]
        assert state["step"].shape == () and state["step"].item() == step
        for key in ("exp_avg", "exp_avg_sq"):
            moment = state[key]
            assert moment.shape == p.shape and moment.dtype == p.dtype and moment.device == p.device
            assert torch.isfinite(moment).all() and torch.count_nonzero(moment) > 0
            if old_moments:
                assert not torch.equal(moment, old_moments[p][key])


def _measured_step(parameters, optimizer, step):
    _assert_no_hooks(optimizer)
    _gradients(parameters, float(step))
    old_parameters = [p.detach().clone() for p in parameters]
    old_moments = {p: {k: v.clone() for k, v in state.items()} for p, state in optimizer.state.items()}
    print(
        f"CPU_ADAM step={step} dynamo_before_step={'torch._dynamo' in sys.modules} "
        "coldness=observed-module-presence-only no_optimizer_warmup=true"
    )
    before = _capture_rng()
    optimizer.step()
    after = _capture_rng()
    equality = _same_rng(before, after)
    print(f"CPU_ADAM step={step} rng_equal_python_numpy_torch={equality} dynamo_after_step={'torch._dynamo' in sys.modules}")
    assert equality == (True, True, True)
    _progress(parameters, optimizer, old_parameters, old_moments, step)
    _assert_continuation(before, after)
    _assert_no_hooks(optimizer)


@pytest.mark.parametrize("family", ["rnd", "adaptive", "icm", "q_factory"])
def test_cpu_adam_public_steps_preserve_global_rng(compiled, family):
    """A real dense public update consuming any ambient stream defeats qualification."""
    owner, parameters, optimizer = _construct(family, compiled)
    _profile(parameters, optimizer)
    assert not optimizer.state
    counters = _counters(owner)
    _measured_step(parameters, optimizer, 1)
    assert _counters(owner) == counters
    _measured_step(parameters, optimizer, 2)
    assert _counters(owner) == counters
    # ICM was manually advanced: deliberately do not claim native checkpoint validity.


def test_stochastic_instance_hook_is_detected_and_removed(compiled):
    """The same detector must observe actual callback RNG work, then a clean bare step."""
    _, parameters, optimizer = _construct("q_factory", compiled)
    _profile(parameters, optimizer)
    _measured_step(parameters, optimizer, 1)
    entry = _capture_rng()
    calls = []

    def consuming_hook(actual_optimizer, args, kwargs):
        assert actual_optimizer is optimizer and args == (optimizer,) and kwargs == {}
        calls.append(True)
        random.random()
        np.random.random_sample()
        torch.rand(1, device="cpu")

    handle = optimizer.register_step_pre_hook(consuming_hook)
    try:
        _gradients(parameters, 2.0)
        previous = [p.detach().clone() for p in parameters]
        moments = {p: {k: v.clone() for k, v in state.items()} for p, state in optimizer.state.items()}
        before = _capture_rng()
        optimizer.step()
        after = _capture_rng()
        equality = _same_rng(before, after)
        print(f"CPU_ADAM stochastic_hook rng_equal_python_numpy_torch={equality} calls={len(calls)}")
        assert calls == [True] and equality == (False, False, False)
        _progress(parameters, optimizer, previous, moments, 2)
    finally:
        handle.remove()
        _restore_rng(entry)
    _assert_no_hooks(optimizer)
    _measured_step(parameters, optimizer, 3)


def test_sparse_cpu_adam_refusal_preserves_global_rng(compiled):
    """A first sparse-gradient refusal is neither an update nor a rollback guarantee."""
    _, parameters, optimizer = _construct("q_factory", compiled)
    _profile(parameters, optimizer)
    assert not optimizer.state
    for p in parameters:
        p.grad = None
    first = parameters[0]
    first.grad = torch.sparse_coo_tensor(
        torch.zeros((first.ndim, 1), dtype=torch.long),
        torch.ones(1, dtype=first.dtype),
        size=first.shape,
        device="cpu",
    )
    previous = [p.detach().clone() for p in parameters]
    before = _capture_rng()
    with pytest.raises(RuntimeError, match="sparse gradients"):
        optimizer.step()
    after = _capture_rng()
    equality = _same_rng(before, after)
    print(f"CPU_ADAM sparse_refusal rng_equal_python_numpy_torch={equality}")
    assert equality == (True, True, True) and not optimizer.state
    assert all(torch.equal(p, old) for p, old in zip(parameters, previous, strict=True))
    _assert_continuation(before, after)
    _assert_no_hooks(optimizer)
