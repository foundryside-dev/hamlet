"""ICM regressions: real transition objectives, bounded service, and atomic state."""

import json
from copy import deepcopy
from importlib import import_module, util
from pathlib import Path

import pytest
import torch
import torch.nn.functional as functional

from townlet.config.bac_options import BaCOptions
from townlet.config.drive_as_code import IntrinsicStrategyConfig
from townlet.config.exploration_policy import IntrinsicTransitionContext, resolve_exploration_policy
from townlet.config.training_v2_config import TrainingV2Config

PARAMETERS = {
    "feature_dim": 2,
    "hidden_dim": 5,
    "learning_rate": 0.03,
    "inverse_weight": 0.7,
    "forward_weight": 0.3,
    "training_batch_size": 3,
    "max_pending_transitions": 6,
}


def _policy(parameters, service_mode, overflow_policy):
    path = Path(__file__).resolve().parents[2] / "fixtures/bac_curiosity_pre_scope/manifest.json"
    effective = json.loads(path.read_text())["artifacts"][0]["effective_run"]
    training = deepcopy(effective["training"])
    training["population"]["size"] = 3
    training["replay_buffer"].update(batch_size=2, min_size=2, capacity=64)
    training["intrinsic"]["rnd"]["feature_dim"] = 4
    options = {
        "providers": {"icm": dict(parameters)},
        "rnd": {"service_mode": service_mode, "max_updates_per_tick": 1, "overflow_policy": overflow_policy},
    }
    training["bac_options"] = deepcopy(options)
    drive = deepcopy(effective["exploration"]["authored_parameters"]["drive_intrinsic"])
    drive.update(strategy="icm", icm_config={"feature_dim": 9, "hidden_dim": 11, "learning_rate": 0.001})
    return resolve_exploration_policy(
        IntrinsicStrategyConfig.model_validate(drive), TrainingV2Config.model_validate(training), BaCOptions.model_validate(options)
    )


def _provider(parameters, service_mode, overflow_policy):
    assert util.find_spec("townlet.exploration.icm") is not None, "transition-based ICM provider is missing"
    provider_type = import_module("townlet.exploration.icm").ICMExploration
    policy = _policy(parameters, service_mode, overflow_policy)
    provider = provider_type(policy, obs_dim=3, action_dim=2, **parameters, device=torch.device("cpu"))
    with torch.no_grad():
        for module in (provider.encoder, provider.inverse_model, provider.forward_model):
            for index, parameter in enumerate(module.parameters()):
                parameter.copy_(
                    0.02 + (torch.arange(parameter.numel()).reshape(parameter.shape) + 1) / (10 * parameter.numel()) + index / 100
                )
    return provider


def _context(predecessor, actions, successor, active, tick):
    return IntrinsicTransitionContext(
        predecessor=torch.tensor(predecessor, dtype=torch.float32),
        actions=torch.tensor(actions, dtype=torch.long),
        successor=torch.tensor(successor, dtype=torch.float32),
        active_on_entry=torch.tensor(active, dtype=torch.bool),
        vector_tick=tick,
    )


def _rows(count, tick):
    return _context(
        [[0.2 + row, 0.5, 0.9] for row in range(count)],
        [row % 2 for row in range(count)],
        [[1.1, 0.3 + row, 1.7] for row in range(count)],
        [True] * count,
        tick,
    )


def _weights(provider):
    return [
        [value.detach().clone() for value in module.parameters()]
        for module in (provider.encoder, provider.inverse_model, provider.forward_model)
    ]


def _objective(provider, context, parameters):
    predecessor = provider.encoder(context.predecessor)
    successor = provider.encoder(context.successor)
    actions = context.actions
    prediction = provider.forward_model(torch.cat((predecessor, functional.one_hot(actions, 2).to(predecessor)), dim=1))
    logits = provider.inverse_model(torch.cat((predecessor, successor), dim=1))
    squared = (prediction - successor.detach()).square()
    loss = parameters["inverse_weight"] * functional.cross_entropy(logits, actions) + parameters["forward_weight"] * squared.mean()
    return loss, 0.5 * squared.mean(dim=1)


def _equal(actual, expected):
    if isinstance(expected, torch.Tensor):
        torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for name in expected:
            _equal(actual[name], expected[name])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for first, second in zip(actual, expected, strict=True):
            _equal(first, second)
    else:
        assert actual == expected


def test_icm_uses_action_and_successor():
    """An observation-only reward or implicit reward-phase training must fail."""
    provider = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    context = _rows(2, 0)
    before = deepcopy(provider.checkpoint_state())
    reward = provider.compute_transition_novelty(context, update_stats=False)
    _, expected = _objective(provider, context, PARAMETERS)
    torch.testing.assert_close(reward, expected.detach())
    assert reward.shape == (2,) and torch.isfinite(reward).all() and not reward.requires_grad
    _equal(provider.checkpoint_state(), before)
    changed_action = _context(context.predecessor.tolist(), [1, 0], context.successor.tolist(), [True, True], 0)
    changed_successor = _context(context.predecessor.tolist(), [0, 1], [[2.2, 1.1, 0.4], [3.1, 0.7, 2.8]], [True, True], 0)
    assert not torch.allclose(reward, provider.compute_transition_novelty(changed_action, update_stats=False))
    assert not torch.allclose(reward, provider.compute_transition_novelty(changed_successor, update_stats=False))
    provider.compute_transition_novelty(context, update_stats=True)
    _equal(_weights(provider), _weights(_provider(PARAMETERS, "paced_fifo", "service_before_admit")))
    assert provider.checkpoint_state()["pending"] == []  # Reward diagnostics never admit predictor work.
    mixed = _context([[0.2, 0.5, 0.9]] * 4, [0, 1, 1, 0], [[1.1, 0.3, 1.7]] * 4, [True, False, True, False], 0)
    receipt = provider.admit_and_service(mixed)
    assert (receipt.admitted_rows, receipt.consumed_rows, receipt.pending_rows, receipt.optimizer_updates) == (2, 0, 2, 0)
    # A terminal-causing row is eligible on entry; next tick's completed/padding rows are not.
    completed = _context([[1.1, 0.3, 1.7]] * 2, [0, 1], [[1.1, 0.3, 1.7]] * 2, [False, False], 1)
    assert provider.admit_and_service(completed).admitted_rows == 0
    assert len(provider.checkpoint_state()["pending"]) == 2
    for invalid in (
        _context([[1.0, 2.0]], [0], [[2.0, 3.0]], [True], 2),
        _context([[1.0, 2.0, 3.0]], [2], [[2.0, 3.0, 4.0]], [True], 2),
        _context([[1.0, 2.0, 3.0]], [-1], [[2.0, 3.0, 4.0]], [True], 2),
    ):
        snapshot = deepcopy(provider.checkpoint_state())
        with pytest.raises((TypeError, ValueError)):
            provider.compute_transition_novelty(invalid, update_stats=False)
        with pytest.raises((TypeError, ValueError)):
            provider.admit_and_service(invalid)
        _equal(provider.checkpoint_state(), snapshot)
    with pytest.raises((TypeError, ValueError)):
        provider.compute_transition_novelty(context.predecessor, update_stats=False)


def test_icm_objective_gradients_and_tail():
    """Wrong loss scaling, an attached target, or a lost partial FIFO must fail."""
    provider = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    context = _rows(3, 0)
    expected_loss, expected_reward = _objective(provider, context, PARAMETERS)
    encoder_parameters = list(provider.encoder.parameters())
    expected_gradients = torch.autograd.grad(expected_loss, encoder_parameters)
    assert any(torch.count_nonzero(gradient) for gradient in expected_gradients)
    captured = [[] for _ in encoder_parameters]
    handles = [parameter.register_hook(values.append) for parameter, values in zip(encoder_parameters, captured, strict=True)]
    before = _weights(provider)
    torch.testing.assert_close(provider.compute_transition_novelty(context, update_stats=False), expected_reward.detach())
    receipt = provider.admit_and_service(context)
    for handle in handles:
        handle.remove()
    assert (receipt.consumed_rows, receipt.optimizer_updates, receipt.pending_rows) == (3, 1, 0)
    assert receipt.last_loss == pytest.approx(expected_loss.detach().item(), rel=1e-6)
    for expected, actual in zip(expected_gradients, captured, strict=True):
        assert len(actual) == 1
        torch.testing.assert_close(actual[0], expected, rtol=1e-5, atol=1e-7)
    for original, updated in zip(before, _weights(provider), strict=True):
        assert any(not torch.equal(first, second) for first, second in zip(original, updated, strict=True))

    uninterrupted = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    assert uninterrupted.admit_and_service(_rows(2, 0)).pending_rows == 2
    saved = deepcopy(uninterrupted.checkpoint_state())
    pending = saved["pending"]
    assert [row["action"] for row in pending] == [0, 1]
    torch.testing.assert_close(pending[0]["predecessor"], torch.tensor([0.2, 0.5, 0.9]))
    torch.testing.assert_close(pending[1]["successor"], torch.tensor([1.1, 1.3, 1.7]))
    restored = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    restored.load_state(saved)
    _equal(restored.checkpoint_state(), saved)
    exposed = uninterrupted.checkpoint_state()
    exposed["pending"][0]["predecessor"].fill_(99)
    _equal(uninterrupted.checkpoint_state(), saved)
    third = _context([[2.2, 0.5, 0.9]], [0], [[1.1, 2.3, 1.7]], [True], 1)
    assert uninterrupted.admit_and_service(third) == restored.admit_and_service(third)
    _equal(restored.checkpoint_state(), uninterrupted.checkpoint_state())
    external = restored.checkpoint_state()
    next(iter(external["encoder"].values())).fill_(99)
    _equal(restored.checkpoint_state(), uninterrupted.checkpoint_state())


@pytest.mark.parametrize("mode,consumed,pending,updates", [("occupancy_fifo", 6, 0, 2), ("paced_fifo", 3, 3, 1)])
def test_icm_service_modes_and_tick_budget(mode, consumed, pending, updates):
    provider = _provider({**PARAMETERS, "max_pending_transitions": 9}, mode, "service_before_admit")
    first = provider.admit_and_service(_rows(6, 7))
    assert (first.admitted_rows, first.consumed_rows, first.pending_rows, first.optimizer_updates) == (6, consumed, pending, updates)
    if mode == "paced_fifo":
        reference = _provider({**PARAMETERS, "max_pending_transitions": 9}, mode, "service_before_admit")
        reference.admit_and_service(_rows(3, 7))
        _equal(_weights(provider), _weights(reference))  # First minibatch uses the oldest complete transitions.
    inactive = _context([[0.0, 0.0, 0.0]], [0], [[0.0, 0.0, 0.0]], [False], 7)
    repeated = provider.admit_and_service(inactive)
    assert (repeated.admitted_rows, repeated.consumed_rows, repeated.optimizer_updates, repeated.pending_rows) == (0, 0, 0, pending)
    inactive = _context([[0.0, 0.0, 0.0]], [0], [[0.0, 0.0, 0.0]], [False], 8)
    later = provider.admit_and_service(inactive)
    assert later.consumed_rows == pending and later.pending_rows == 0


@pytest.mark.parametrize(
    "overflow,drops,updates,mandatory", [("service_before_admit", 0, 3, 2), ("drop_oldest", 6, 1, 0), ("drop_newest", 6, 1, 0)]
)
def test_icm_bounded_overflow_accounting(overflow, drops, updates, mandatory):
    provider = _provider({**PARAMETERS, "max_pending_transitions": 3}, "paced_fifo", overflow)
    receipt = provider.admit_and_service(_rows(9, 0))
    assert receipt.provider == "icm"
    assert (receipt.admitted_rows, receipt.dropped_rows, receipt.pending_rows) == (9, drops, 0)
    assert (receipt.optimizer_updates, receipt.mandatory_service_updates) == (updates, mandatory)
    assert receipt.consumed_rows + receipt.dropped_rows + receipt.pending_rows == receipt.admitted_rows
    assert len(provider.checkpoint_state()["pending"]) <= 3
    if drops:
        reference = _provider({**PARAMETERS, "max_pending_transitions": 3}, "paced_fifo", overflow)
        selected = _rows(9, 0)
        indices = slice(6, 9) if overflow == "drop_oldest" else slice(0, 3)
        retained = _context(
            selected.predecessor[indices].tolist(), selected.actions[indices].tolist(), selected.successor[indices].tolist(), [True] * 3, 0
        )
        reference.admit_and_service(retained)
        _equal(_weights(provider), _weights(reference))


@pytest.mark.parametrize(
    "inverse,forward,changed", [(1.0, 0.0, (True, True, False)), (0.0, 1.0, (True, False, True)), (0.0, 0.0, (False, False, False))]
)
def test_icm_selected_weights_and_instance_ownership(inverse, forward, changed):
    parameters = {
        **PARAMETERS,
        "inverse_weight": inverse,
        "forward_weight": forward,
        "feature_dim": 3,
        "hidden_dim": 7,
        "learning_rate": 0.017,
    }
    first = _provider(parameters, "paced_fifo", "service_before_admit")
    second = _provider(parameters, "paced_fifo", "service_before_admit")
    second_before = deepcopy(second.checkpoint_state())
    before = _weights(first)
    assert first.encoder(_rows(3, 0).predecessor).shape == (3, 3)
    assert first.optimizer.param_groups[0]["lr"] == 0.017
    assert (first.compute_transition_novelty(_rows(3, 0), update_stats=False) > 0).all()
    for left, right in zip(
        (first.encoder, first.inverse_model, first.forward_model), (second.encoder, second.inverse_model, second.forward_model), strict=True
    ):
        assert all(a.data_ptr() != b.data_ptr() for a, b in zip(left.parameters(), right.parameters(), strict=True))
    first.admit_and_service(_rows(3, 0))
    actual = tuple(
        any(not torch.equal(a, b) for a, b in zip(old, new, strict=True)) for old, new in zip(before, _weights(first), strict=True)
    )
    assert actual == changed
    _equal(second.checkpoint_state(), second_before)


@pytest.mark.parametrize("defect", ["actions_shape", "actions_dtype", "successor", "device", "eligibility"])
def test_icm_requires_a_complete_typed_transition(defect):
    _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    context = _rows(2, 0)
    values = {
        "predecessor": context.predecessor,
        "actions": context.actions,
        "successor": context.successor,
        "active_on_entry": context.active_on_entry,
        "vector_tick": 0,
    }
    if defect == "actions_shape":
        values["actions"] = torch.tensor([0])
    elif defect == "actions_dtype":
        values["actions"] = torch.zeros(2)
    elif defect == "successor":
        values["successor"] = torch.ones(2, 4)
    elif defect == "device":
        values["actions"] = torch.zeros(2, dtype=torch.long, device="meta")
    else:
        values["active_on_entry"] = torch.ones(2)
    with pytest.raises((TypeError, ValueError)):
        IntrinsicTransitionContext(**values)


@pytest.mark.parametrize("name,value", [("feature_dim", 3), ("hidden_dim", 7), ("learning_rate", 0.001), ("training_batch_size", 2)])
def test_icm_constructor_cannot_override_selected_policy(name, value):
    provider_type = type(_provider(PARAMETERS, "paced_fifo", "service_before_admit"))
    policy = _policy(PARAMETERS, "paced_fifo", "service_before_admit")
    with pytest.raises((TypeError, ValueError)):
        provider_type(policy, obs_dim=3, action_dim=2, **{**PARAMETERS, name: value}, device=torch.device("cpu"))


@pytest.mark.parametrize(
    "defect",
    [
        "nan_pending",
        "pending_shape",
        "pending_action",
        "too_many_pending",
        "optimizer_nan",
        "optimizer_rate",
        "model_nan",
        "config_nan",
        "config",
    ],
)
def test_icm_malformed_restore_is_atomic(defect):
    provider = _provider(PARAMETERS, "paced_fifo", "service_before_admit")
    provider.admit_and_service(_rows(3, 0))  # Establish real Adam moments before malformed optimizer restore.
    provider.admit_and_service(_rows(2, 1))
    before = deepcopy(provider.checkpoint_state())
    bad = deepcopy(before)
    if defect == "nan_pending":
        bad["pending"][0]["successor"][0] = float("nan")
    elif defect == "pending_shape":
        bad["pending"][1]["predecessor"] = torch.ones(4)
    elif defect == "pending_action":
        bad["pending"][1]["action"] = 2
    elif defect == "too_many_pending":
        bad["pending"] *= 4
    elif defect == "optimizer_nan":
        next(iter(bad["optimizer"]["state"].values()))["exp_avg"].fill_(float("nan"))
    elif defect == "optimizer_rate":
        bad["optimizer"]["param_groups"][0]["lr"] = 0.001
    elif defect == "model_nan":
        next(iter(bad["encoder"].values())).fill_(float("nan"))
    elif defect == "config_nan":
        bad["config"]["learning_rate"] = float("nan")
    else:
        bad["config"]["feature_dim"] += 1
    with pytest.raises((TypeError, ValueError)):
        provider.load_state(bad)
    _equal(provider.checkpoint_state(), before)
