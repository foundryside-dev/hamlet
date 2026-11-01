"""P3 estimator, finite-update and PER4/5/6 preservation regressions.

All oracles and RNG spies live here. New interfaces are resolved inside test
bodies so the pre-T13 implementation still collects these causal regressions.
"""

from __future__ import annotations

import copy
import importlib
import itertools
import math
from collections import Counter
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as functional

SUCCESSIVE = "successive_without_replacement"
INDEPENDENT = "independent_with_replacement"
RULES = {SUCCESSIVE: "successive_conditional_residual_v1", INDEPENDENT: "independent_inverse_probability_v1"}
COMPONENTS = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
ROW_FIELDS = ("observations", "actions", "rewards", *COMPONENTS, "next_observations", "dones")
OLD_KEYS = {
    "replay_kind",
    "format_version",
    "capacity",
    "alpha",
    "beta",
    "beta_initial",
    "beta_annealing",
    "priorities",
    "max_priority",
    "position",
    "size_current",
    *ROW_FIELDS,
}
CAPTURED_KEYS = OLD_KEYS | {
    "action_dim",
    "legality_mode",
    "historical_archives",
    "next_action_masks",
    "legality_recorded",
    *(f"{name}_present" for name in COMPONENTS),
}
NEW_KEYS = {
    "unit_ids",
    "next_unit_id",
    "sampling_mode",
    "sampling_origin",
    "sampling_objective_unit",
    "sampling_weight_rule",
    "sampling_rng",
}
FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "bac_per_current5"


def _pb():
    return importlib.import_module("townlet.training.prioritized_replay_buffer")


def _ps():
    return importlib.import_module("townlet.training.per_sampling")


def _history():
    return importlib.import_module("townlet.training.historical_checkpoint")


def _same(actual, expected):
    assert type(actual) is type(expected)
    if isinstance(actual, torch.Tensor):
        assert actual.dtype == expected.dtype and actual.device == expected.device
        assert torch.equal(actual, expected)
    elif isinstance(actual, np.ndarray):
        assert actual.dtype == expected.dtype
        np.testing.assert_array_equal(actual, expected)
    elif isinstance(actual, Mapping):
        assert actual.keys() == expected.keys()
        for key in actual:
            _same(actual[key], expected[key])
    elif isinstance(actual, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _same(left, right)
    elif isinstance(actual, float) and math.isnan(actual):
        assert math.isnan(expected)
    else:
        assert actual == expected


def _buffer(capacity=4, *, alpha=0.6, beta=0.4, annealing=True):
    return _pb().PrioritizedReplayBuffer(capacity, alpha, beta, annealing, torch.device("cpu"))


def _push(buffer, rows, *, present=(True, False, True), recorded=True):
    reward_type = importlib.import_module("townlet.training.state").RewardTensor
    values = torch.tensor(rows, dtype=torch.float32)
    observations = torch.stack((values, values + 0.25), dim=1)
    actions = values.to(torch.int64) % 3
    dones = actions == 1
    masks = torch.zeros((len(rows), 3), dtype=torch.bool)
    masks[~dones, 0] = True
    masks[~dones, 2] = True
    components = [values + offset if exists else None for offset, exists in zip((10, 20, 30), present, strict=True)]
    rewards = reward_type(values + 100, extrinsic=components[0], intrinsic=components[1], shaping=components[2], is_composed=True)
    args = (observations, actions, rewards, observations + 1, dones)
    if recorded:
        buffer.push_recorded(*args, masks)
    else:
        buffer.push(*args)
    return observations, rewards, masks


def _request(batch, mode=SUCCESSIVE, minimum=1):
    return _pb().ReplayRequest(batch, 1, minimum, mode, "feedforward", "transition")


def _configure(buffer, mode=INDEPENDENT, *, seed=702, origin="authored"):
    buffer.configure_sampling(sampling_mode=mode, rng=np.random.default_rng(seed), origin=origin)


def _captured(archived=False):
    filename = "per5-captured-with-per4-archive.pt" if archived else "per5-captured.pt"
    state = torch.load(FIXTURES / filename, map_location="cpu", weights_only=False)
    assert set(state) == CAPTURED_KEYS and state["format_version"] == 5
    return state


def _oracle(priorities, order, alpha, beta, mode):
    """Small ordinary-value oracle; never uses production scoring/weight helpers."""
    scores = np.array([float(value) ** alpha for value in priorities], dtype=np.float64)
    remaining = list(range(len(scores)))
    q = []
    for index in order:
        support = remaining if mode == SUCCESSIVE else list(range(len(scores)))
        q.append(float(scores[index]) / math.fsum(float(scores[item]) for item in support))
        if mode == SUCCESSIVE:
            remaining.remove(index)
    if mode == SUCCESSIVE:
        weights = [
            1.0 if len(order) == len(scores) else ((len(order) - k - 1 + 1 / value) / len(scores)) ** beta for k, value in enumerate(q)
        ]
    else:
        weights = [(len(scores) * value) ** (-beta) for value in q]
    return np.array(q), np.array(weights), math.prod(q)


class _ForcedRng(np.random.Generator):
    """A real Generator subtype spying only at the actual choice boundary."""

    def __init__(self, priorities, order, alpha, mode):
        super().__init__(np.random.PCG64(192))
        self.scores = np.array([float(value) ** alpha for value in priorities])
        self.order, self.mode, self.offset, self.calls = tuple(order), mode, 0, []

    def choice(self, a, size=None, replace=True, p=None, axis=0, shuffle=True):
        pool = np.arange(a) if np.isscalar(a) else np.asarray(a)
        count = 1 if size is None else int(np.prod(size))
        assert axis == 0
        if count > 1:
            assert bool(replace) == (self.mode == INDEPENDENT)
        assert self.offset + count <= len(self.order)
        active = self.scores.copy()
        if self.mode == SUCCESSIVE:
            active[list(self.order[: self.offset])] = 0
        expected = active[pool] / math.fsum(float(value) for value in active)
        if p is None:
            np.testing.assert_allclose(expected, np.full(len(pool), 1 / len(pool)), rtol=1e-13, atol=0)
        else:
            np.testing.assert_allclose(p, expected, rtol=1e-13, atol=0)
        selected = np.array(self.order[self.offset : self.offset + count], dtype=np.int64)
        assert all(index in pool for index in selected)
        assert all(active[index] > 0 for index in selected)
        self.calls.append((pool.copy(), np.asarray(p).copy(), bool(replace)))
        self.offset += count
        return int(selected[0]) if size is None else selected.reshape(size)


def _forced_receipt(priorities, order, *, alpha=0.6, beta=1.0, mode=SUCCESSIVE):
    priorities = np.array(priorities, dtype=np.float64)
    original = priorities.copy()
    rng = _ForcedRng(priorities, order, alpha, mode)
    receipt = _ps().sample_units(priorities, alpha=alpha, beta=beta, batch_size=len(order), mode=mode, rng=rng)
    assert rng.offset == len(order) and rng.calls
    np.testing.assert_array_equal(priorities, original)
    _check_receipt(receipt, len(priorities), mode)
    np.testing.assert_array_equal(receipt.indices, order)
    q, weights, probability = _oracle(priorities, order, alpha, beta, mode)
    np.testing.assert_allclose(receipt.conditional_draw_probabilities, q, rtol=1e-13, atol=0)
    np.testing.assert_allclose(receipt.weights, weights, rtol=1e-13, atol=0)
    assert math.prod(receipt.conditional_draw_probabilities) == pytest.approx(probability, rel=1e-13, abs=0)
    return receipt, probability


def _check_receipt(receipt, population, mode):
    assert isinstance(receipt, _pb().SamplingReceipt)
    assert receipt.indices.dtype == np.int64 and receipt.indices.ndim == 1
    assert receipt.weights.dtype == np.float64 and receipt.weights.shape == receipt.indices.shape
    assert receipt.conditional_draw_probabilities.dtype == np.float64
    assert receipt.conditional_draw_probabilities.shape == receipt.indices.shape
    assert receipt.population_size == population and receipt.mode == mode
    assert receipt.objective_unit == "transition" and receipt.weight_rule == RULES[mode]
    assert np.all(np.isfinite(receipt.weights)) and np.all(receipt.weights > 0)
    assert np.all(np.isfinite(receipt.conditional_draw_probabilities))
    assert np.all((receipt.conditional_draw_probabilities > 0) & (receipt.conditional_draw_probabilities <= 1))


def test_full_buffer_huber_gradient_zero():
    """Catches the existing consumer's sampled-max normalization at B=N."""
    buffer = _buffer(2, alpha=1.0, beta=1.0, annealing=False)
    _push(buffer, [0, 1])
    buffer.update_priorities(np.array([0, 1]), torch.tensor([1.0, -9.0]))
    batch = buffer.sample(2)
    errors = torch.tensor([1.0, -9.0])[batch["indices"]]
    theta = torch.tensor(0.0, requires_grad=True)
    loss = (functional.smooth_l1_loss(theta.expand(2), -errors, reduction="none") * batch["weights"].detach()).mean()
    loss.backward()
    assert theta.grad.item() == pytest.approx(0.0, abs=1e-12)
    torch.testing.assert_close(batch["weights"], torch.ones(2), rtol=0, atol=0)
    assert batch["weights"].dtype == torch.float32 and not batch["weights"].requires_grad


def test_old_initial_probability_sample_max_is_a_deterministic_negative():
    """Independent literal negative control: neither a missing API nor a lucky draw."""
    priorities = np.array([1.0, 9.0])
    coefficients = np.zeros(2)
    for order in itertools.permutations(range(2)):
        _, _, probability = _oracle(priorities, order, 1.0, 1.0, SUCCESSIVE)
        old_weights = 1 / (2 * (priorities / priorities.sum())[list(order)])
        old_weights /= old_weights.max()
        for index, weight in zip(order, old_weights, strict=True):
            coefficients[index] += probability * weight / 2
    np.testing.assert_allclose(coefficients, [0.5, 1 / 18], rtol=0, atol=1e-15)
    assert abs(float(coefficients @ np.array([1.0, -1.0]))) > 0.4
    assert not np.allclose(coefficients, [0.5, 0.5], rtol=0, atol=1e-12)


def test_ordered_estimator_exact_expectation():
    """Every actual forced ordered receipt contributes exactly 1/N at beta1."""
    for population in range(2, 5):
        priorities = np.array([1.0, 3.0, 7.0, 13.0][:population])
        for batch in range(1, population + 1):
            coefficients, total_probability = np.zeros(population), 0.0
            for order in itertools.permutations(range(population), batch):
                receipt, probability = _forced_receipt(priorities, order)
                total_probability += probability
                np.add.at(coefficients, receipt.indices, probability * receipt.weights / batch)
                if batch == population:
                    np.testing.assert_array_equal(receipt.weights, np.ones(batch))
            assert total_probability == pytest.approx(1, abs=1e-12)
            np.testing.assert_allclose(coefficients, np.full(population, 1 / population), rtol=0, atol=1e-12)


def test_actual_sampler_ordered_law():
    """Forced branches spy proposal arguments; seeded frequencies catch routing changes."""
    priorities = np.array([1.0, 3.0, 8.0], dtype=np.float64)
    exact = {}
    for order in itertools.permutations(range(3), 2):
        receipt, probability = _forced_receipt(priorities, order, alpha=1.0)
        assert len(set(receipt.indices)) == 2
        exact[order] = probability
    # Predeclared seed/count/bounds: each tuple must lie inside 6 sigma + 3 draws.
    draws, rng, counts = 12000, np.random.default_rng(20261101), Counter()
    for _ in range(draws):
        receipt = _ps().sample_units(priorities, alpha=1.0, beta=1.0, batch_size=2, mode=SUCCESSIVE, rng=rng)
        counts[tuple(receipt.indices)] += 1
    assert set(counts) == set(exact)
    for order, probability in exact.items():
        bound = 6 * math.sqrt(draws * probability * (1 - probability)) + 3
        assert abs(counts[order] - draws * probability) <= bound, (order, counts, probability, bound)


def test_independent_estimator_exact_expectation():
    """Cartesian enumeration includes repeated handles and replacement batches B>N."""
    for population in range(2, 5):
        priorities = np.array([1.0, 3.0, 7.0, 13.0][:population])
        for batch in range(1, population + 2):
            coefficients, total_probability = np.zeros(population), 0.0
            for order in itertools.product(range(population), repeat=batch):
                receipt, probability = _forced_receipt(priorities, order, mode=INDEPENDENT)
                total_probability += probability
                np.add.at(coefficients, receipt.indices, probability * receipt.weights / batch)
            assert total_probability == pytest.approx(1, abs=1e-12)
            np.testing.assert_allclose(coefficients, np.full(population, 1 / population), rtol=0, atol=1e-12)


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_alpha_zero_uniform_proposals_have_exact_expected_coefficients(mode):
    coefficients = np.zeros(3)
    orders = itertools.permutations(range(3), 2) if mode == SUCCESSIVE else itertools.product(range(3), repeat=2)
    for order in orders:
        receipt, probability = _forced_receipt([1, 17, 301], order, alpha=0.0, mode=mode)
        np.add.at(coefficients, receipt.indices, probability * receipt.weights / 2)
    np.testing.assert_allclose(coefficients, np.full(3, 1 / 3), rtol=0, atol=1e-12)


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_beta_zero_leaves_each_sample_weight_one(mode):
    receipt, _ = _forced_receipt([1, 3, 19], (2, 0), beta=0.0, mode=mode)
    np.testing.assert_array_equal(receipt.weights, np.ones(2))


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_intermediate_beta_uses_declared_power_without_sample_max(mode):
    receipt, _ = _forced_receipt([1, 3, 19], (0, 2), beta=0.37, mode=mode)
    _, beta_one, _ = _oracle([1, 3, 19], (0, 2), 0.6, 1.0, mode)
    np.testing.assert_allclose(receipt.weights, beta_one**0.37, rtol=1e-13, atol=0)
    assert receipt.weights.max() > 1.0


def test_large_finite_priorities():
    """Existing physical API first: float32 score sums must not overflow."""
    buffer = _buffer(2, alpha=1.0, beta=1.0, annealing=False)
    _push(buffer, [0, 1])
    buffer.update_priorities(np.array([0, 1]), torch.tensor([3e38, 3e38]))
    legacy = buffer.sample(1)
    assert bool(torch.isfinite(legacy["weights"]).all())
    torch.testing.assert_close(legacy["weights"], torch.ones(1), rtol=0, atol=0)
    for mode in (SUCCESSIVE, INDEPENDENT):
        for magnitude in (3e38, 1e308):
            receipt = _ps().sample_units(
                np.full(2, magnitude), alpha=1.0, beta=1.0, batch_size=1, mode=mode, rng=np.random.default_rng(193)
            )
            _check_receipt(receipt, 2, mode)
            np.testing.assert_array_equal(receipt.conditional_draw_probabilities, [0.5])
            np.testing.assert_array_equal(receipt.weights, [1.0])


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_score_scaling_preserves_the_draw_law_and_weights(mode):
    ordinary, _ = _forced_receipt([1, 3, 7], (2, 0), alpha=0.7, mode=mode)
    scaled, _ = _forced_receipt([1e200, 3e200, 7e200], (2, 0), alpha=0.7, mode=mode)
    np.testing.assert_allclose(scaled.conditional_draw_probabilities, ordinary.conditional_draw_probabilities, rtol=1e-12, atol=0)
    np.testing.assert_allclose(scaled.weights, ordinary.weights, rtol=1e-12, atol=0)


def test_residual_support_is_recomputed_after_a_dominating_draw():
    receipt, _ = _forced_receipt([1e-200, 1.0, 1e200], (2, 0), alpha=0.5)
    assert receipt.conditional_draw_probabilities[1] == pytest.approx(1e-100, rel=1e-13, abs=0)
    assert np.isfinite(receipt.weights).all() and receipt.weights[1] > 1e99


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
@pytest.mark.parametrize("beta", [0.0, 0.1])
def test_tiny_positive_q_accepts_representable_final_beta_weight(mode, beta):
    priorities = np.array([1e-310, 1.0])
    rng = _ForcedRng(priorities, (0,), 1.0, mode)
    receipt = _ps().sample_units(priorities, alpha=1.0, beta=beta, batch_size=1, mode=mode, rng=rng)
    expected = math.exp(beta * (-math.log(2) - math.log(1e-310)))
    _check_receipt(receipt, 2, mode)
    assert receipt.conditional_draw_probabilities[0] == pytest.approx(1e-310, rel=1e-13, abs=0)
    assert receipt.weights[0] == pytest.approx(expected, rel=1e-12, abs=0)


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_unrepresentable_positive_support_refuses_with_location_before_rng(mode):
    priorities = np.array([np.nextafter(0.0, 1.0), np.finfo(np.float64).max])
    rng = np.random.default_rng(930)
    before = copy.deepcopy(rng.bit_generator.state)
    with pytest.raises(ValueError, match=r"(?i)(priorit.*0|support.*0|represent.*0|probabilit.*0)"):
        _ps().sample_units(priorities, alpha=1.0, beta=1.0, batch_size=1, mode=mode, rng=rng)
    _same(rng.bit_generator.state, before)


@pytest.mark.parametrize(
    "change",
    [
        {"priorities": np.array([], dtype=np.float64)},
        {"priorities": np.array([[1.0]])},
        {"priorities": np.array([1.0, 0.0])},
        {"priorities": np.array([1.0, -1.0])},
        {"priorities": np.array([1.0, np.nan])},
        {"priorities": np.array([1.0, np.inf])},
        {"alpha": -0.1},
        {"alpha": 1.1},
        {"alpha": np.nan},
        {"alpha": True},
        {"beta": -0.1},
        {"beta": 1.1},
        {"beta": np.inf},
        {"beta": True},
        {"batch_size": 0},
        {"batch_size": -1},
        {"batch_size": 3},
        {"batch_size": 1.5},
        {"batch_size": True},
        {"mode": "unregistered"},
        {"rng": None},
    ],
)
def test_malformed_sampling_request_is_owned_and_consumes_no_rng(change):
    rng = np.random.default_rng(604)
    args = dict(priorities=np.array([1.0, 3.0]), alpha=0.6, beta=1.0, batch_size=1, mode=SUCCESSIVE, rng=rng)
    args.update(change)
    original = copy.deepcopy(args["priorities"])
    before = copy.deepcopy(rng.bit_generator.state)
    with pytest.raises((ValueError, TypeError)):
        _ps().sample_units(**args)
    _same(args["priorities"], original)
    _same(rng.bit_generator.state, before)


def test_receipts_and_priority_input_do_not_alias():
    priorities = np.array([1.0, 4.0, 9.0])
    original = priorities.copy()
    rng = _ForcedRng(priorities, (0, 2), 0.6, SUCCESSIVE)
    receipt = _ps().sample_units(priorities, alpha=0.6, beta=1.0, batch_size=2, mode=SUCCESSIVE, rng=rng)
    np.testing.assert_array_equal(priorities, original)
    saved = (receipt.indices.copy(), receipt.weights.copy(), receipt.conditional_draw_probabilities.copy())
    priorities.fill(8)
    for value, expected in zip((receipt.indices, receipt.weights, receipt.conditional_draw_probabilities), saved, strict=True):
        np.testing.assert_array_equal(value, expected)
    again, _ = _forced_receipt(original, (0, 2))
    np.testing.assert_array_equal(again.weights, saved[1])


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_actual_global_adapter_retains_seed_control_and_correct_weights(mode):
    """Configured sample_batch must never commandeer legacy sample/global state."""
    saved_global = np.random.get_state()
    try:
        buffer = _buffer(4, beta=1.0, annealing=False)
        _push(buffer, [0, 1, 2, 3])
        buffer.update_priorities(np.arange(4), torch.tensor([1.0, 2.0, 5.0, 11.0]))
        _configure(buffer, mode)
        np.random.seed(843)
        scores = buffer.priorities.astype(np.float64) ** 0.6
        wanted_indices = np.random.choice(4, 2, p=scores / scores.sum(), replace=False)
        wanted_global = np.random.get_state()
        np.random.seed(843)
        expected = _ps().sample_legacy_units(buffer.priorities.astype(np.float64), alpha=0.6, beta=1.0, batch_size=2)
        np.testing.assert_array_equal(expected.indices, wanted_indices)
        _same(np.random.get_state(), wanted_global)
        expected_global = np.random.get_state()
        np.random.seed(843)
        actual = buffer.sample(2)
        np.testing.assert_array_equal(actual["indices"], expected.indices)
        torch.testing.assert_close(actual["weights"], torch.tensor(expected.weights, dtype=torch.float32), rtol=0, atol=0)
        _same(np.random.get_state(), expected_global)
        assert len(set(actual["indices"])) == 2
        _check_receipt(expected, 4, SUCCESSIVE)
        q, weights, _ = _oracle(buffer.priorities, expected.indices, 0.6, 1.0, SUCCESSIVE)
        np.testing.assert_allclose(expected.conditional_draw_probabilities, q, rtol=1e-12, atol=0)
        np.testing.assert_allclose(expected.weights, weights, rtol=1e-12, atol=0)
    finally:
        np.random.set_state(saved_global)


@pytest.mark.parametrize(
    "indices,errors",
    [
        (np.array([0, 1]), torch.tensor([2.0])),
        (np.array([0]), torch.tensor([2.0, 3.0])),
        (np.array([0.0, 1.0]), torch.tensor([2.0, 3.0])),
        (np.array([True, False]), torch.tensor([2.0, 3.0])),
        (np.array([[0, 1]]), torch.tensor([2.0, 3.0])),
        (np.array([0, -1]), torch.tensor([2.0, 3.0])),
        (np.array([0, 3]), torch.tensor([2.0, 3.0])),
        (np.array([0, 1]), torch.tensor([2.0, np.nan])),
        (np.array([0, 1]), torch.tensor([2.0, np.inf])),
        (np.array([0, 1]), torch.tensor([[2.0, 3.0]])),
        (np.array([0, 1]), torch.tensor([2.0, 7e38], dtype=torch.float64)),
    ],
)
def test_legacy_priority_updates_validate_whole_request_before_any_write(indices, errors):
    """Existing API causal failures include truncation, final NaN and partial writes."""
    buffer = _buffer(4)
    _push(buffer, [0, 1, 2])
    before, original_indices, original_errors = buffer.serialize(), indices.copy(), errors.clone()
    with pytest.raises((ValueError, TypeError, OverflowError), match=r"(?i)(index|indices|td|priorit|finite|shape|length|represent)"):
        buffer.update_priorities(indices, errors)
    _same(buffer.serialize(), before)
    _same(indices, original_indices)
    torch.testing.assert_close(errors, original_errors, rtol=0, atol=0, equal_nan=True)


@pytest.mark.parametrize("permutation", [(0, 1, 2), (1, 2, 0), (2, 0, 1)])
def test_legacy_duplicate_physical_updates_use_order_independent_max_abs(permutation):
    buffer = _buffer(3)
    _push(buffer, [0, 1, 2])
    before = buffer.serialize()
    indices, errors = np.array([0, 0, 1]), torch.tensor([7.0, -2.0, 3.0])
    buffer.update_priorities(indices[list(permutation)], errors[list(permutation)])
    np.testing.assert_allclose(buffer.priorities[:2], np.array([7 + 1e-6, 3 + 1e-6], dtype=np.float32), rtol=0, atol=0)
    after = buffer.serialize()
    for key in CAPTURED_KEYS - {"priorities", "max_priority"}:
        _same(after[key], before[key])
    assert buffer.max_priority == float(buffer.priorities[0])


def test_qualified_replacement_readiness_mode_and_stable_mapping():
    buffer = _buffer(2)
    _push(buffer, [0, 1])
    with pytest.raises(ValueError):
        buffer.sample_batch(_request(3, INDEPENDENT))
    _configure(buffer)
    ready = buffer.readiness(_request(5, INDEPENDENT))
    assert ready.ready and ready.retained_transitions == ready.sampleable_units == 2
    assert buffer.readiness(_request(5, INDEPENDENT, minimum=3)).reason == "warmup"
    before = buffer.serialize()
    batch = buffer.sample_batch(_request(5, INDEPENDENT))
    _check_receipt(batch.sampling, 2, INDEPENDENT)
    assert len(batch.unit_ids) == 5 and len(set(batch.unit_ids.tolist())) <= 2
    np.testing.assert_array_equal(batch.unit_ids.numpy(), before["unit_ids"][batch.sampling.indices])
    torch.testing.assert_close(batch.observations, buffer.observations[batch.sampling.indices])
    torch.testing.assert_close(batch.weights, torch.from_numpy(batch.sampling.weights), rtol=0, atol=0)
    assert batch.weights.dtype == torch.float64 and not batch.weights.requires_grad
    with pytest.raises(ValueError):
        buffer.sample_batch(_request(1, SUCCESSIVE))
    persisted = buffer.serialize()
    _configure(buffer, SUCCESSIVE)
    reconfigured = buffer.serialize()
    for key in set(persisted) - {"sampling_mode", "sampling_origin", "sampling_weight_rule", "sampling_rng"}:
        _same(reconfigured[key], persisted[key])
    assert not buffer.readiness(_request(3)).ready


def test_unconstrained_public_adapter_still_requires_explicit_legality_declaration():
    buffer = _buffer(3, beta=1.0, annealing=False)
    _push(buffer, [0, 1], recorded=False)
    assert not buffer.readiness(_request(1)).ready
    buffer.declare_unconstrained_action_dim(action_dim=3)
    assert buffer.readiness(_request(2)).ready
    batch = buffer.sample_batch(_request(2))
    assert bool(batch.next_action_masks.all()) and bool(batch.legality_recorded.all())
    torch.testing.assert_close(batch.weights, torch.ones(2, dtype=torch.float64), rtol=0, atol=0)


@pytest.mark.parametrize("permutation", [(0, 1, 2), (1, 2, 0), (2, 0, 1)])
def test_duplicate_stable_ids_reduce_max_abs_and_preserve_rows(permutation):
    buffer = _buffer(3)
    _push(buffer, [0, 1, 2])
    _configure(buffer)
    state = buffer.serialize()
    ids = state["unit_ids"][[0, 0, 1]]
    errors = torch.tensor([8.0, -2.0, 3.0])
    buffer.update_unit_priorities(ids[list(permutation)], errors[list(permutation)])
    after = buffer.serialize()
    np.testing.assert_array_equal(after["priorities"][:2], np.array([8 + 1e-6, 3 + 1e-6], dtype=np.float32))
    for key in set(after) - {"priorities", "max_priority"}:
        _same(after[key], state[key])


@pytest.mark.parametrize("case", ["length", "dtype", "negative", "unknown", "nan", "overflow", "rank"])
def test_stable_update_validates_entire_request_atomically(case):
    buffer = _buffer(3)
    _push(buffer, [0, 1, 2])
    state = buffer.serialize()
    ids, errors = state["unit_ids"][:2].copy(), torch.tensor([4.0, 6.0])
    if case == "length":
        errors = errors[:1]
    elif case == "dtype":
        ids = ids.astype(np.int32)
    elif case == "negative":
        ids[1] = -1
    elif case == "unknown":
        ids[1] = state["next_unit_id"]
    elif case == "nan":
        errors[1] = np.nan
    elif case == "overflow":
        errors = torch.tensor([4.0, 7e38], dtype=torch.float64)
    else:
        ids = ids.reshape(1, 2)
    with pytest.raises((ValueError, TypeError, OverflowError)):
        buffer.update_unit_priorities(ids, errors)
    _same(buffer.serialize(), state)


def test_stale_ids_after_overwrite_and_clear_never_address_a_new_occupant():
    buffer = _buffer(2)
    _push(buffer, [0, 1])
    original = buffer.serialize()
    _push(buffer, [2])
    wrapped = buffer.serialize()
    assert wrapped["unit_ids"][0] > original["unit_ids"].max()
    with pytest.raises(ValueError):
        buffer.update_unit_priorities(original["unit_ids"], torch.tensor([4.0, 5.0]))
    _same(buffer.serialize(), wrapped)
    buffer.update_priorities(np.array([0]), torch.tensor([6.0]))
    assert float(buffer.priorities[0]) == float(np.float32(6 + 1e-6))
    counter = buffer.serialize()["next_unit_id"]
    buffer.clear()
    assert buffer.serialize()["next_unit_id"] == counter
    _push(buffer, [3])
    cleared = buffer.serialize()
    assert cleared["unit_ids"][0] >= counter
    with pytest.raises(ValueError):
        buffer.update_unit_priorities(wrapped["unit_ids"], torch.tensor([4.0, 5.0]))
    _same(buffer.serialize(), cleared)


def test_id_exhaustion_refuses_push_before_any_storage_or_counter_write():
    buffer = _buffer(3)
    _push(buffer, [0, 1])
    state = buffer.serialize()
    state["next_unit_id"] = int(np.iinfo(np.int64).max)
    buffer.load_from_serialized(state)
    before = buffer.serialize()
    with pytest.raises((ValueError, OverflowError), match=r"(?i)(id|counter|exhaust|overflow)"):
        _push(buffer, [2, 3])
    _same(buffer.serialize(), before)


@pytest.mark.parametrize("engine_name", ["PCG64", "PCG64DXSM", "MT19937", "Philox", "SFC64"])
def test_owned_generator_configuration_roundtrip_continues_without_aliasing(engine_name):
    supplied = np.random.Generator(getattr(np.random, engine_name)(811))
    supplied_before = copy.deepcopy(supplied.bit_generator.state)
    buffer, control = _buffer(3), _buffer(3)
    for target in (buffer, control):
        _push(target, [0, 1, 2])
        target.configure_sampling(sampling_mode=INDEPENDENT, rng=supplied, origin="bac-options-v1")
    _same(supplied.bit_generator.state, supplied_before)
    supplied.random(41)
    first = buffer.sample_batch(_request(7, INDEPENDENT))
    counterpart = control.sample_batch(_request(7, INDEPENDENT))
    np.testing.assert_array_equal(first.sampling.indices, counterpart.sampling.indices)
    saved = buffer.serialize()
    descriptor = saved["sampling_rng"]
    assert set(descriptor) == {"ownership", "bit_generator", "state"}
    assert descriptor["ownership"] == "owned_numpy_generator" and descriptor["bit_generator"] == engine_name
    restored = _buffer(3)
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    restored.load_from_serialized(saved)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)
    for _ in range(4):
        left, right = buffer.sample_batch(_request(7, INDEPENDENT)), restored.sample_batch(_request(7, INDEPENDENT))
        np.testing.assert_array_equal(left.sampling.indices, right.sampling.indices)
        torch.testing.assert_close(left.weights, right.weights, rtol=0, atol=0)
    before = restored.serialize()
    saved["sampling_rng"]["state"].clear()
    _same(restored.serialize(), before)


@pytest.mark.parametrize(
    "change",
    [
        {"sampling_mode": "missing"},
        {"sampling_mode": None},
        {"origin": "guessed"},
        {"origin": None},
        {"rng": None},
        {"rng": 123},
    ],
)
def test_invalid_reconfiguration_does_not_mutate_storage_or_rng(change):
    buffer = _buffer(3)
    _push(buffer, [0, 1, 2])
    _configure(buffer)
    before = buffer.serialize()
    supplied = np.random.default_rng(400)
    rng_before = copy.deepcopy(supplied.bit_generator.state)
    args = dict(sampling_mode=SUCCESSIVE, rng=supplied, origin="authored")
    args.update(change)
    with pytest.raises((ValueError, TypeError)):
        buffer.configure_sampling(**args)
    _same(buffer.serialize(), before)
    _same(supplied.bit_generator.state, rng_before)


def test_legacy_persistence_labels_external_global_ownership_without_restoring_it():
    buffer = _buffer(3)
    _push(buffer, [0, 1])
    state = buffer.serialize()
    assert state["format_version"] == 6 and set(state) == CAPTURED_KEYS | NEW_KEYS
    assert state["unit_ids"].dtype == np.int64 and state["unit_ids"].shape == (3,)
    np.testing.assert_array_equal(state["unit_ids"], [0, 1, -1])
    assert state["next_unit_id"] == 2
    assert state["sampling_mode"] == SUCCESSIVE and state["sampling_origin"] == "legacy-constructor"
    assert state["sampling_objective_unit"] == "transition" and state["sampling_weight_rule"] == RULES[SUCCESSIVE]
    assert state["sampling_rng"] == {"ownership": "numpy_global_legacy", "bit_generator": None, "state": None}
    target = _buffer(3)
    before = np.random.get_state()
    target.load_from_serialized(state)
    _same(np.random.get_state(), before)
    _same(target.serialize(), state)


@pytest.mark.parametrize("archived", [False, True])
def test_authentic_captured5_adapter_preserves_all_original_fields_and_full_resume(archived):
    state, target = _captured(archived), _buffer(3)
    original, before = copy.deepcopy(state), target.serialize()
    validated = target.validate_serialized(state, expected_obs_dim=2)
    _same(state, original)
    _same(target.serialize(), before)
    target.load_prepared(target.materialize_validated(validated))
    adapted = target.serialize()
    assert adapted["format_version"] == 6 and set(adapted) == CAPTURED_KEYS | NEW_KEYS
    for key in CAPTURED_KEYS - {"format_version"}:
        _same(adapted[key], original[key])
    np.testing.assert_array_equal(adapted["unit_ids"], np.arange(3, dtype=np.int64))
    assert adapted["next_unit_id"] == 3 and adapted["sampling_origin"] == "captured5-physical-slot-adapter"
    assert adapted["sampling_mode"] == SUCCESSIVE and adapted["sampling_weight_rule"] == RULES[SUCCESSIVE]
    assert adapted["sampling_rng"] == {"ownership": "numpy_global_legacy", "bit_generator": None, "state": None}
    assert target.retained_transitions == 3 and target.position == 2 and target.beta == 0.7 and target.beta_initial == 0.4
    assert target.readiness(_request(3)).ready
    batch = target.sample_batch(_request(3))
    assert sorted(batch.observations[:, 0].tolist()) == [2.0, 3.0, 4.0]
    assert bool((~batch.next_action_masks[batch.dones]).all())
    full = _buffer(3)
    full.load_for_mode(state, requested_mode="recorded_full_resume")
    assert full.retained_transitions == 3
    with pytest.raises(ValueError):
        target.load_for_mode(state, requested_mode="archived_history_fresh_episode")
    _same(state, original)
    restored = _buffer(3)
    restored.load_from_serialized(adapted)
    _same(restored.serialize(), adapted)
    state["observations"].fill_(-100)
    _same(target.serialize(), adapted)


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("case", ["missing", "unknown", "new_key_under_5", "mask", "presence", "priority"])
def test_original_closed5_schema_is_validated_before_adaptation(archived, case):
    state, target = _captured(archived), _buffer(3)
    _push(target, [8])
    if case == "missing":
        state.pop("beta_initial")
    elif case == "unknown":
        state["surprise"] = 1
    elif case == "new_key_under_5":
        state["unit_ids"] = np.arange(3)
    elif case == "mask":
        state["next_action_masks"][0].fill_(False)
    elif case == "presence":
        state["rewards_extrinsic_present"][0] = True
        state["rewards_extrinsic"] = None
    else:
        state["priorities"][-1] = np.inf
    original, before = copy.deepcopy(state), target.serialize()
    with pytest.raises(ValueError):
        target.load_from_serialized(state)
    _same(target.serialize(), before)
    _same(state, original)


def _bad6(state, case):
    if case == "version_bool":
        state["format_version"] = True
    elif case == "future":
        state["format_version"] = 7
    elif case == "missing":
        state.pop("sampling_rng")
    elif case == "unknown":
        state["surprise"] = 0
    elif case == "ids_duplicate":
        state["unit_ids"][1] = state["unit_ids"][0]
    elif case == "ids_dtype":
        state["unit_ids"] = state["unit_ids"].astype(np.int32)
    elif case == "ids_shape":
        state["unit_ids"] = state["unit_ids"][:-1]
    elif case == "ids_negative":
        state["unit_ids"][1] = -1
    elif case == "ids_inactive":
        state["size_current"], state["position"] = 2, 2
        for key in (*ROW_FIELDS, "next_action_masks", "legality_recorded", *(f"{name}_present" for name in COMPONENTS)):
            if state[key] is not None:
                state[key] = state[key][:2].clone()
    elif case == "counter":
        state["next_unit_id"] = int(state["unit_ids"].max())
    elif case == "counter_bool":
        state["next_unit_id"] = True
    elif case == "counter_overflow":
        state["next_unit_id"] = 2**63
    elif case == "mode":
        state["sampling_mode"] = "unregistered"
    elif case == "origin":
        state["sampling_origin"] = "legacy-constructor"
    elif case == "objective":
        state["sampling_objective_unit"] = "window"
    elif case == "rule":
        state["sampling_weight_rule"] = RULES[SUCCESSIVE]
    elif case == "rng_unknown":
        state["sampling_rng"]["surprise"] = 1
    elif case == "rng_missing":
        state["sampling_rng"].pop("state")
    elif case == "rng_kind":
        state["sampling_rng"]["bit_generator"] = "arbitrary.module.Class"
    elif case == "rng_mismatch":
        state["sampling_rng"]["state"]["bit_generator"] = "Philox"
    elif case == "rng_late":
        state["sampling_rng"]["state"]["state"]["state"] = -1
    else:
        archive = _captured(True)["historical_archives"][0]
        state["historical_archives"] = [archive, copy.deepcopy(archive)]
        state["historical_archives"][-1]["archived_row_count"] += 1


@pytest.mark.parametrize(
    "case",
    [
        "version_bool",
        "future",
        "missing",
        "unknown",
        "ids_duplicate",
        "ids_dtype",
        "ids_shape",
        "ids_negative",
        "ids_inactive",
        "counter",
        "counter_bool",
        "counter_overflow",
        "mode",
        "origin",
        "objective",
        "rule",
        "rng_unknown",
        "rng_missing",
        "rng_kind",
        "rng_mismatch",
        "rng_late",
        "late_archive",
    ],
)
def test_closed6_malformed_restore_is_pure_and_atomic_against_populated_target(case):
    source, target = _buffer(3), _buffer(3)
    for buffer, rows in ((source, [0, 1, 2]), (target, [6, 7, 8])):
        _push(buffer, rows)
        _configure(buffer)
    source.sample_batch(_request(4, INDEPENDENT))
    state = source.serialize()
    assert state["format_version"] == 6
    _bad6(state, case)
    original, before = copy.deepcopy(state), target.serialize()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    for operation in (lambda: target.validate_serialized(state, expected_obs_dim=2), lambda: target.load_from_serialized(state)):
        with pytest.raises((ValueError, TypeError, OverflowError)):
            operation()
        _same(target.serialize(), before)
        _same(state, original)
        _same(np.random.get_state(), global_before)
        torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


def test_preparation_allocation_failure_does_not_mutate_populated_target(monkeypatch):
    source, target = _buffer(3), _buffer(3)
    _push(source, [0, 1, 2])
    _push(target, [6, 7, 8])
    _configure(source)
    state, before = source.serialize(), target.serialize()
    original, real_zeros, calls = copy.deepcopy(state), torch.zeros, 0

    def fail_late(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("injected materialization allocation failure")
        return real_zeros(*args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(torch, "zeros", fail_late)
        with pytest.raises(RuntimeError, match="injected materialization"):
            target.prepare_serialized(state, expected_obs_dim=2)
    assert calls == 3
    _same(target.serialize(), before)
    _same(state, original)


def test_wrap_component_presence_owned_inputs_and_new6_roundtrip():
    buffer = _buffer(3)
    observations, rewards, masks = _push(buffer, [0, 1, 2])
    before = buffer.serialize()
    observations.fill_(-1)
    rewards.total.fill_(-1)
    masks.fill_(False)
    _same(buffer.serialize(), before)
    _push(buffer, [3, 4], present=(False, True, False))
    _configure(buffer, SUCCESSIVE)
    state = buffer.serialize()
    assert state["format_version"] == 6 and state["position"] == 2
    np.testing.assert_array_equal(state["unit_ids"], [3, 4, 2])
    assert state["next_unit_id"] == 5
    torch.testing.assert_close(state["observations"][:, 0], torch.tensor([3.0, 4.0, 2.0]))
    for name, expected in zip(COMPONENTS, ([False, False, True], [True, True, False], [False, False, True]), strict=True):
        torch.testing.assert_close(state[f"{name}_present"], torch.tensor(expected))
    restored = _buffer(3)
    restored.load_from_serialized(state)
    _same(restored.serialize(), state)
    _push(restored, [5])
    assert restored.serialize()["unit_ids"][2] == 5
    assert restored.serialize()["next_unit_id"] == 6


def test_archive_union_clear_and_optional_component_absence_survive_current_restore():
    target = _buffer(3)
    target.load_from_serialized(_captured(True))
    retained = target.historical_archives
    target.load_from_serialized(_captured(False))
    assert len(target.historical_archives) == 1
    assert target.historical_archives[0].source_digest == retained[0].source_digest
    before = target.serialize()
    target.clear()
    assert target.retained_transitions == 0 and target.serialize()["next_unit_id"] == before["next_unit_id"]
    assert len(target.historical_archives) == 1
    _push(target, [9], present=(False, False, False))
    batch = target.sample_batch(_request(1))
    for name in COMPONENTS:
        assert getattr(batch, name) is None and not bool(getattr(batch, f"{name}_present").any())


def test_genuine_per4_stays_strict_archival_fresh_zero_and_exportable(tmp_path):
    old = _captured(True)["historical_archives"][0]["original_state"]
    assert old["format_version"] == 4 and set(old) == OLD_KEYS and len(old) == 19
    original = copy.deepcopy(old)
    target = _buffer(old["capacity"], alpha=old["alpha"], beta=old["beta_initial"], annealing=old["beta_annealing"])
    reward_type = importlib.import_module("townlet.training.state").RewardTensor
    rewards = reward_type(torch.tensor([108.0]), extrinsic=None, intrinsic=None, shaping=None, is_composed=True)
    observations = torch.full((1, old["observations"].shape[1]), 8.0)
    target.push_recorded(
        observations, torch.tensor([2]), rewards, observations + 1, torch.tensor([False]), torch.tensor([[True, False, True]])
    )
    before = target.serialize()
    target.validate_serialized(old, expected_obs_dim=None)
    _same(target.serialize(), before)
    with pytest.raises(_pb().HistoricalLegalityUnavailable):
        target.load_for_mode(old, requested_mode="recorded_full_resume")
    _same(target.serialize(), before)
    target.load_from_serialized(old)
    assert target.retained_transitions == 0 and not target.priorities.any()
    assert not target.readiness(_request(1)).ready
    (archive,) = target.historical_archives
    assert archive.archived_row_count == old["size_current"] == 4
    queried = archive.query_rows(offset=0, limit=4)
    torch.testing.assert_close(queried["observations"], old["observations"])
    destination = tmp_path / "preserved-per4.pt"
    archive.export(destination)
    _same(torch.load(destination, weights_only=False), original)
    target.clear()
    assert len(target.historical_archives) == 1
    _same(old, original)


@pytest.mark.parametrize("version", [5, 6])
def test_hc_explicit_current_per_classification_policy_and_codec(version):
    history = _history()
    replay = _captured(False)
    if version == 6:
        buffer = _buffer(3)
        buffer.load_from_serialized(replay)
        replay = buffer.serialize()
        assert replay["format_version"] == 6
    payload = {"version": 10, "action_dim": 3, "population_state": {"version": 7, "replay_buffer": replay}}
    original = copy.deepcopy(payload)
    policy = history.resolve_historical_access(payload, requested_mode="recorded_full_resume")
    assert policy.source_formats == {"demo": 10, "population": 7, "replay": version, "replay_kind": "prioritized"}
    assert policy.effective_mode == "recorded_full_resume" and policy.active_retained_transitions == 3
    envelope = history.HistoricalPreparedEnvelope(policy, (), payload)
    encoded = history.encode_historical_envelope(envelope)
    decoded = history.decode_historical_envelope(encoded)
    _same(decoded.policy.source_formats, policy.source_formats)
    _same(history.encode_historical_envelope(decoded), encoded)
    for bad in (4, 7, True):
        malformed = copy.deepcopy(encoded)
        malformed["policy"]["source_formats"]["replay"] = bad
        with pytest.raises(ValueError):
            history.decode_historical_envelope(malformed)
        malformed_payload = copy.deepcopy(payload)
        malformed_payload["population_state"]["replay_buffer"]["format_version"] = bad
        with pytest.raises(ValueError):
            history.resolve_historical_access(malformed_payload, requested_mode="auto")
    _same(payload, original)


def test_hc_historical_per4_domain_and_standard_sequence_policy_versions_stay_distinct():
    history = _history()
    old = _captured(True)["historical_archives"][0]["original_state"]
    payload = {"version": 9, "population_state": {"version": 6, "replay_buffer": old}}
    policy = history.resolve_historical_access(payload, requested_mode="auto")
    assert policy.source_formats["replay"] == 4 and policy.effective_mode == "archived_history_fresh_episode"
    assert policy.active_retained_transitions == 0 and policy.archived_row_count == 4
    with pytest.raises(_pb().HistoricalLegalityUnavailable):
        history.resolve_historical_access(payload, requested_mode="recorded_full_resume")
    for kind, current in (("standard", 5), ("sequential", 6)):
        for version in (current, current + 1):
            kwargs = dict(
                source_formats={"demo": 10, "population": 7, "replay": version, "replay_kind": kind},
                requested_mode="auto",
                effective_mode="recorded_full_resume",
                approval_reference=None,
                archived_row_count=0,
                active_retained_transitions=0,
                restored_clocks={},
                guarantees=(),
                legacy_identity_recipe="current-captured",
            )
            if version == current:
                assert history.HistoricalAccessPolicy(**kwargs).source_formats["replay"] == current
            else:
                with pytest.raises(ValueError):
                    history.HistoricalAccessPolicy(**kwargs)


def test_legacy_float32_weight_refuses_before_global_choice_or_rng_consumption(monkeypatch):
    """Positive-support float64 correction must be checked at the legacy dtype boundary."""
    buffer = _buffer(2, alpha=1.0, beta=1.0, annealing=False)
    _push(buffer, [0, 1])
    indices, errors = np.array([0, 1], dtype=np.int64), torch.tensor([0.0, 3e38])
    buffer.update_priorities(indices, errors)
    before, supplied_indices, supplied_errors = buffer.serialize(), indices.copy(), errors.clone()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    real_choice, calls = np.random.choice, []

    def force_low(a, size=None, replace=True, p=None):
        calls.append((a, size, replace))
        assert a == 2 and size == 1 and replace is False
        expected = buffer.priorities.astype(np.float64)
        expected /= expected.sum()
        np.testing.assert_allclose(p, expected, rtol=1e-13, atol=0)
        # Preserve real global-RNG consumption, then force the rare positive
        # support branch. The required preflight must never enter this choice.
        real_choice(a, size=size, replace=replace, p=p)
        return np.array([0], dtype=np.int64)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(np.random, "choice", force_low)
            with pytest.raises(ValueError, match=r"(?i)(?=.*(?:index|unit).*0)(?=.*(?:represent|float32))"):
                buffer.sample(1)
        global_after = np.random.get_state()
    finally:
        np.random.set_state(global_before)
    assert not calls, "legacy float32 representability was checked after calling global choice"
    _same(global_after, global_before)
    _same(buffer.serialize(), before)
    _same(indices, supplied_indices)
    torch.testing.assert_close(errors, supplied_errors, rtol=0, atol=0)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


@pytest.mark.parametrize("beta,batch_size", [(0.1, 1), (0.0, 1), (1.0, 2)])
def test_legacy_float32_representable_beta_and_full_population_positives(monkeypatch, beta, batch_size):
    buffer = _buffer(2, alpha=1.0, beta=beta, annealing=False)
    _push(buffer, [0, 1])
    buffer.update_priorities(np.array([0, 1]), torch.tensor([0.0, 3e38]))
    before, order = buffer.serialize(), tuple(range(batch_size))

    def force_order(a, size=None, replace=True, p=None):
        assert a == 2 and size == batch_size and replace is False
        assert p is not None and p[0] > 0 and p[1] > 0
        return np.array(order, dtype=np.int64)

    monkeypatch.setattr(np.random, "choice", force_order)
    batch = buffer.sample(batch_size)
    _, expected, _ = _oracle(buffer.priorities, order, 1.0, beta, SUCCESSIVE)
    assert batch["weights"].dtype == torch.float32 and bool(torch.isfinite(batch["weights"]).all())
    torch.testing.assert_close(batch["weights"], torch.tensor(expected, dtype=torch.float32), rtol=1e-6, atol=0)
    _same(buffer.serialize(), before)


def test_qualified_float64_retains_positive_support_above_legacy_weight_range(monkeypatch):
    buffer = _buffer(2, alpha=1.0, beta=1.0, annealing=False)
    _push(buffer, [0, 1])
    buffer.update_priorities(np.array([0, 1]), torch.tensor([0.0, 3e38]))
    before = buffer.serialize()

    def force_low(a, size=None, replace=True, p=None):
        assert a == 2 and size == 1 and replace is False
        assert p is not None and p[0] > 0
        return np.array([0], dtype=np.int64)

    monkeypatch.setattr(np.random, "choice", force_low)
    batch = buffer.sample_batch(_request(1))
    _, expected, _ = _oracle(buffer.priorities, (0,), 1.0, 1.0, SUCCESSIVE)
    assert batch.weights.dtype == torch.float64 and bool(torch.isfinite(batch.weights).all())
    assert float(batch.weights[0]) > float(np.finfo(np.float32).max)
    torch.testing.assert_close(batch.weights, torch.from_numpy(expected), rtol=1e-12, atol=0)
    np.testing.assert_array_equal(batch.sampling.indices, [0])
    _same(buffer.serialize(), before)


@pytest.mark.parametrize("operation", ["validate", "load"])
def test_new6_unrepresentable_insertion_max_refuses_purely_before_install(operation):
    source, target = _buffer(3), _buffer(3)
    for buffer, rows in ((source, [0, 1]), (target, [6, 7])):
        _push(buffer, rows)
        _configure(buffer)
    state = source.serialize()
    assert state["format_version"] == 6 and set(state) == CAPTURED_KEYS | NEW_KEYS
    state["max_priority"] = 1e300
    original, before = copy.deepcopy(state), target.serialize()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    with pytest.raises(ValueError, match=r"(?i)max_priority"):
        if operation == "validate":
            target.validate_serialized(state, expected_obs_dim=2)
        else:
            target.load_from_serialized(state)
    _same(target.serialize(), before)
    _same(state, original)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


def test_legacy_dictionary_indices_are_owned_writable_int64():
    buffer = _buffer(2, alpha=1.0, beta=1.0, annealing=False)
    _push(buffer, [0, 1])
    before = buffer.serialize()
    qualified = buffer.sample_batch(_request(2))
    assert not qualified.sampling.indices.flags.writeable
    with pytest.raises(ValueError):
        qualified.sampling.indices[0] = 0
    legacy = buffer.sample(2)
    indices = legacy["indices"]
    assert isinstance(indices, np.ndarray) and indices.dtype == np.int64 and indices.flags.owndata
    assert indices.flags.writeable, "legacy indices must retain the writable np.random.choice result contract"
    indices[:] = 0
    assert np.all(indices == 0)
    _same(buffer.serialize(), before)


@pytest.mark.parametrize("operation", ["validate", "load"])
def test_max_invariant_empty6_underflow_refuses_atomically(operation):
    source, target = _buffer(3), _buffer(3)
    _configure(source, SUCCESSIVE)
    _push(target, [6, 7])
    _configure(target, SUCCESSIVE, seed=91)
    state = source.serialize()
    assert state["format_version"] == 6 and state["size_current"] == 0
    state["max_priority"] = 1e-300
    original, before = copy.deepcopy(state), target.serialize()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    with pytest.raises(ValueError, match=r"(?i)max_priority"):
        if operation == "validate":
            target.validate_serialized(state, expected_obs_dim=None)
        else:
            target.load_from_serialized(state)
    _same(target.serialize(), before)
    _same(state, original)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


def test_max_invariant_malformed_live_underflow_refuses_before_insertion_mutation():
    """Malformed live public metadata robustness only; no authored reachability claim."""
    buffer = _buffer(3)
    _configure(buffer, SUCCESSIVE)
    buffer.max_priority = 1e-300
    before = buffer.serialize()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    with pytest.raises(ValueError, match=r"(?i)max_priority"):
        _push(buffer, [0])
    _same(buffer.serialize(), before)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


@pytest.mark.parametrize("operation", ["validate", "load"])
def test_max_invariant_captured5_adapter_refuses_unloadable_latest_state(operation):
    state, target = _captured(False), _buffer(3)
    assert state["format_version"] == 5 and set(state) == CAPTURED_KEYS
    # A schema-valid semantic-malformation control, not a historical producer claim.
    state["max_priority"] = 1e300
    _push(target, [6, 7])
    _configure(target)
    original, before = copy.deepcopy(state), target.serialize()
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    with pytest.raises(ValueError, match=r"(?i)max_priority"):
        if operation == "validate":
            target.validate_serialized(state, expected_obs_dim=2)
        else:
            target.load_from_serialized(state)
    _same(target.serialize(), before)
    _same(state, original)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)


@pytest.mark.parametrize("version", [5, 6])
def test_max_invariant_ordinary_round_up_preserves_restore_then_serves_and_reloads(version):
    if version == 5:
        state = _captured(False)
        state["max_priority"] = 8.0000006  # Above all captured active priorities; rounds upward in float32.
    else:
        state = _buffer(3).serialize()
        state["max_priority"] = 1.00000007
    original, buffer = copy.deepcopy(state), _buffer(3)
    global_before, torch_before = np.random.get_state(), torch.get_rng_state().clone()
    buffer.load_from_serialized(state)
    restored = buffer.serialize()
    for key in set(state) - {"format_version"}:
        _same(restored[key], state[key])
    _same(state, original)
    _same(np.random.get_state(), global_before)
    torch.testing.assert_close(torch.get_rng_state(), torch_before, rtol=0, atol=0)
    _push(buffer, [9])
    after = buffer.serialize()
    active = after["priorities"][: after["size_current"]]
    assert np.isfinite(active).all() and np.all(active > 0)
    assert after["max_priority"] >= float(active.max()), "insertion rounded an active priority above its cached maximum"
    continuation = _buffer(3)
    continuation.load_from_serialized(after)
    _same(continuation.serialize(), after)
    batch = continuation.sample_batch(_request(continuation.retained_transitions))
    assert bool(torch.isfinite(batch.weights).all()) and bool(batch.legality_recorded.all())
    _push(continuation, [10])
    assert continuation.max_priority >= float(continuation.priorities.max())


@pytest.mark.parametrize("maximum", [float(np.nextafter(np.float32(0), np.float32(1))), float(np.finfo(np.float32).max)])
def test_max_invariant_positive_float32_subnormal_and_upper_boundary_remain_supported(maximum):
    state, buffer = _buffer(3).serialize(), _buffer(3)
    state["max_priority"] = maximum
    original = copy.deepcopy(state)
    buffer.load_from_serialized(state)
    _same(buffer.serialize(), state)
    _same(state, original)
    _push(buffer, [0])
    assert buffer.priorities[0] == np.float32(maximum) and buffer.priorities[0] > 0
    after, continuation = buffer.serialize(), _buffer(3)
    continuation.load_from_serialized(after)
    _same(continuation.serialize(), after)
    torch.testing.assert_close(continuation.sample_batch(_request(1)).weights, torch.ones(1, dtype=torch.float64), rtol=0, atol=0)


def test_max_invariant_old4_archive_maximum_does_not_become_an_active_bound():
    old = _captured(True)["historical_archives"][0]["original_state"]
    assert old["format_version"] == 4 and set(old) == OLD_KEYS
    # Explicit archival-domain control; this is not an authentic producer-value claim.
    old["max_priority"] = 1e300
    original = copy.deepcopy(old)
    target = _buffer(old["capacity"], alpha=old["alpha"], beta=old["beta_initial"], annealing=old["beta_annealing"])
    target.validate_serialized(old, expected_obs_dim=None)
    target.load_from_serialized(old)
    assert target.retained_transitions == 0 and not target.priorities.any()
    (archive,) = target.historical_archives
    assert archive.original_state["max_priority"] == 1e300
    assert archive.archived_row_count == old["size_current"] and archive.source_formats["replay"] == 4
    _same(archive.original_state, original)
    _same(old, original)
