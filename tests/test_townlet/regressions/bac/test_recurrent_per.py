"""T14 public storage contracts; synthetic rows are transport, not learner evidence."""

import copy
import hashlib
import itertools
import math
import random
from pathlib import Path

import numpy as np
import pytest
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.training.replay_contract import ReplayBatch, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer

SUCCESSIVE = "successive_without_replacement"
INDEPENDENT = "independent_with_replacement"
EPS = 1e-6
DEVICE = torch.device("cpu")
DATA = Path(__file__).resolve().parents[2] / "fixtures" / "bac_sequence_current6"


def _same(actual, expected):
    if isinstance(expected, torch.Tensor):
        torch.testing.assert_close(actual, expected, rtol=0, atol=0, equal_nan=True)
    elif isinstance(expected, np.ndarray):
        np.testing.assert_array_equal(actual, expected)
    elif isinstance(expected, dict):
        assert actual.keys() == expected.keys()
        for key in expected:
            _same(actual[key], expected[key])
    elif isinstance(expected, (tuple, list)):
        assert type(actual) is type(expected) and len(actual) == len(expected)
        for left, right in zip(actual, expected, strict=True):
            _same(left, right)
    else:
        assert actual == expected or (isinstance(expected, float) and math.isnan(expected) and math.isnan(actual))


def _globals():
    return copy.deepcopy((np.random.get_state(), random.getstate(), torch.random.get_rng_state()))


def _options(mode=SUCCESSIVE, sequence="adaptive_prefix", objective="window_mean", retention="transition_tail", reducer="max_abs"):
    return ReplayOptions(
        sampling_mode=mode,
        uniform_sequence_adapter="legacy_episode_length_with_replacement",
        sequence_mode=sequence,
        retention_mode=retention,
        sequence_objective=objective,
        priority_reduction=reducer,
    )


def _per(
    *, options=None, capacity=32, rng=None, alpha=1.0, beta=1.0, annealing=False, horizon=10, tick=0, action_dim=3, origin="T14-explicit"
):
    factory = getattr(SequentialReplayBuffer, "for_prioritized_replay", None)
    assert callable(factory), "T14 requires the additive public for_prioritized_replay factory"
    return factory(
        capacity,
        DEVICE,
        options=_options() if options is None else options,
        action_dim=action_dim,
        legality_mode="captured",
        alpha=alpha,
        beta=beta,
        beta_annealing=annealing,
        beta_vector_tick_horizon=horizon,
        current_vector_tick=tick,
        rng=np.random.Generator(np.random.PCG64(19)) if rng is None else rng,
        origin=origin,
    )


def _request(buffer, length, batch=1, minimum=0):
    options = buffer.replay_options
    return ReplayRequest(batch, length, minimum, options.sampling_mode, options.sequence_mode, options.sequence_objective)


def _rows(count, start=0, width=2, action_dim=3, terminal=False, component=None):
    observations = torch.arange(count * width, dtype=torch.float32).reshape(count, width) / 10 + start
    rows = dict(
        observations=observations,
        actions=torch.arange(count, dtype=torch.int64) % action_dim,
        rewards=torch.arange(count, dtype=torch.float32) + start,
        next_observations=observations + 0.25,
        dones=torch.zeros(count, dtype=torch.bool),
    )
    rows["dones"][-1] = terminal
    if component is not None:
        rows[component] = torch.arange(count, dtype=torch.float32) + 0.5
    return rows


def _store(buffer, count, start=0, terminal=False, component=None):
    rows = _rows(count, start, action_dim=buffer.action_dim, terminal=terminal, component=component)
    masks = torch.ones((count, buffer.action_dim), dtype=torch.bool)
    masks[rows["dones"]] = False
    buffer.store_captured_episode(rows, next_action_masks=masks, legality_recorded=torch.ones(count, dtype=torch.bool))
    return rows


def _domain(buffer, length):
    return next(item for item in buffer.serialize()["priority_state"]["domains"] if item["sequence_length"] == length)


def _updates(buffer, length, values, ids=None, width=None):
    state, domain = buffer.serialize(), _domain(buffer, length)
    lookup = {int(handle): key.tolist() for handle, key in zip(domain["unit_ids"], domain["window_keys"], strict=True)}
    handles = domain["unit_ids"].clone() if ids is None else torch.tensor(ids, dtype=torch.int64)
    errors = torch.full((len(handles), length if width is None else width), float("nan"), dtype=torch.float64)
    mask = torch.zeros_like(errors, dtype=torch.bool)
    for row, (handle, value) in enumerate(zip(handles.tolist(), values, strict=True)):
        episode_id, first, end = lookup[handle]
        episode = next(item for item in state["episodes"] if item["episode_id"] == episode_id)
        retained_ids = episode["transition_ids"].tolist()
        size = retained_ids.index(end) - retained_ids.index(first) + 1
        mask[row, :size] = True
        if buffer.replay_options.sequence_objective == "anchor_transition":
            mask[row, : size - 1] = False
        errors[row, mask[row]] = value
    return handles, errors, mask


def _put(buffer, length, priorities):
    ids, errors, mask = _updates(buffer, length, np.asarray(priorities) - EPS)
    buffer.update_priorities(ids, errors, loss_mask=mask)


def _atomic(buffer, action, match=None):
    before, external = copy.deepcopy(buffer.serialize()), _globals()
    with pytest.raises(ValueError, match=match):
        action()
    _same(buffer.serialize(), before)
    _same(_globals(), external)


def _tape(draws):
    """Public MT19937 state supplies exact finite choice uniforms, without rare draws."""

    def undo(value, shift, mask, left):
        result = value
        for _ in range(33):
            result = value ^ (((result << shift) & mask) if left else (result >> shift))
        return result & 0xFFFFFFFF

    words = []
    for uniform in draws:
        integer = int(uniform * (1 << 53))
        for value in ((integer >> 26) << 5, (integer & ((1 << 26) - 1)) << 6):
            value = undo(value, 18, 0, False)
            value = undo(value, 15, 0xEFC60000, True)
            value = undo(value, 7, 0x9D2C5680, True)
            words.append(undo(value, 11, 0, False))
    bit_generator = np.random.MT19937(0)
    state = bit_generator.state
    state["state"]["key"] = np.asarray(words + [0] * (624 - len(words)), dtype=np.uint32)
    state["state"]["pos"] = 0
    bit_generator.state = state
    rng = np.random.Generator(bit_generator)
    np.testing.assert_allclose(copy.deepcopy(rng).random(len(draws)), draws, atol=2**-52, rtol=0)
    return rng


def _model():
    with torch.random.fork_rng(devices=[]):
        model = torch.nn.LSTM(2, 2, batch_first=True)
    with torch.no_grad():
        for name, parameter in model.named_parameters():
            parameter.fill_(0.17 if "weight" in name else 0.03)
    return model


def _objectives(batch, model):
    result = []
    for index, length in enumerate(batch.lengths.tolist()):
        output, _ = model(batch.observations[index : index + 1, :length])
        losses = output[0].square().mean(-1)
        result.append(float(losses[batch.loss_mask[index, :length]].mean().detach()))
    return np.asarray(result)


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
@pytest.mark.parametrize("sequence", ["fixed_full", "adaptive_prefix"])
@pytest.mark.parametrize("objective", ["window_mean", "anchor_transition"])
@pytest.mark.parametrize("reducer", ["max_abs", "mean_abs"])
def test_recurrent_per_window_objective(mode, sequence, objective, reducer):
    """Wrong actual draw order/q or duplicated timestep weights biases the LSTM objective."""
    priorities, model = np.asarray([1.0, 2.0, 4.0]), _model()
    orders = list(itertools.permutations(range(3), 2) if mode == SUCCESSIVE else itertools.product(range(3), repeat=2))
    expectation = wrong_expectation = 0.0
    losses_by_unit = None
    for order in orders:
        support, uniforms, conditional = list(range(3)), [], []
        for selected in order:
            probabilities = priorities[support] / priorities[support].sum()
            position = support.index(selected)
            uniforms.append(float(probabilities[:position].sum() + probabilities[position] / 2))
            conditional.append(float(probabilities[position]))
            if mode == SUCCESSIVE:
                support.remove(selected)
        buffer = _per(options=_options(mode, sequence, objective, reducer=reducer), rng=_tape([0.5, *uniforms]))
        rows = _store(buffer, 4 if sequence == "fixed_full" else 3)
        buffer.sample_batch(_request(buffer, 2))
        domain = _domain(buffer, 2)
        expected_keys = [[0, 0, 1], [0, 1, 2], [0, 2, 3]] if sequence == "fixed_full" else [[0, 0, 0], [0, 0, 1], [0, 1, 2]]
        assert domain["window_keys"].tolist() == expected_keys
        _put(buffer, 2, priorities)
        batch = buffer.sample_batch(_request(buffer, 2, 2))
        assert tuple(batch.sampling.indices) == order
        assert batch.unit_ids.tolist() == domain["unit_ids"][list(order)].tolist()
        np.testing.assert_allclose(batch.sampling.conditional_draw_probabilities, conditional, rtol=1e-13)
        q = np.asarray(conditional)
        expected_weights = (np.asarray([1, 0]) + 1 / q) / 3 if mode == SUCCESSIVE else 1 / (3 * q)
        np.testing.assert_allclose(batch.weights.numpy(), expected_weights, rtol=1e-13)
        assert batch.sampling.population_size == 3 and batch.sampling.mode == mode
        assert batch.sampling.objective_unit == ("window" if objective == "window_mean" else "anchor_transition")
        assert batch.sampling.weight_rule == (
            "successive_conditional_residual_v1" if mode == SUCCESSIVE else "independent_inverse_probability_v1"
        )
        bounds = [(0, 2), (1, 3), (2, 4)] if sequence == "fixed_full" else [(0, 1), (0, 2), (1, 3)]
        expected_losses = []
        for start, end in bounds:
            output, _ = model(rows["observations"][None, start:end])
            losses = output[0].square().mean(-1)
            expected_losses.append(float((losses.mean() if objective == "window_mean" else losses[-1]).detach()))
        losses_by_unit = np.asarray(expected_losses)
        actual_losses = _objectives(batch, model)
        np.testing.assert_allclose(actual_losses, losses_by_unit[list(order)], rtol=1e-6)
        probability = math.prod(conditional)
        expectation += probability * np.mean(batch.weights.numpy() * actual_losses)
        wrong = 1 / (3 * (priorities / priorities.sum())[list(order)])
        wrong_expectation += probability * np.mean((wrong / wrong.max()) * actual_losses)
    assert expectation == pytest.approx(losses_by_unit.mean(), abs=1e-10)
    assert abs(wrong_expectation - losses_by_unit.mean()) > 1e-6


@pytest.mark.parametrize("retention", ["whole_episode", "transition_tail"])
@pytest.mark.parametrize("sequence", ["fixed_full", "adaptive_prefix"])
def test_recurrent_priority_restore_and_eviction(retention, sequence):
    """Tail-context replacement, stale handles and clear must not alias another unit."""
    buffer = _per(capacity=4, options=_options(sequence=sequence, retention=retention))
    _store(buffer, 4)
    for length in (1, 2):
        buffer.sample_batch(_request(buffer, length))
        _put(buffer, length, np.arange(len(_domain(buffer, length)["unit_ids"])) + 2 + length)
    before = buffer.serialize()
    old = {
        (d["sequence_length"], *key.tolist()): (int(handle), float(priority))
        for d in before["priority_state"]["domains"]
        for key, handle, priority in zip(d["window_keys"], d["unit_ids"], d["priorities"], strict=True)
    }
    _store(buffer, 2, start=10)
    after = buffer.serialize()
    current = {
        (d["sequence_length"], *key.tolist()): (int(handle), float(priority))
        for d in after["priority_state"]["domains"]
        for key, handle, priority in zip(d["window_keys"], d["unit_ids"], d["priorities"], strict=True)
    }
    for key, value in current.items():
        if key in old:
            assert value == old[key]
        else:
            assert value[0] >= before["priority_state"]["next_unit_id"]
            assert value[1] == before["priority_state"]["max_priority"]
    if retention == "transition_tail":
        assert current[(2, 0, 2, 3)] == old[(2, 0, 2, 3)]
        if sequence == "adaptive_prefix":
            assert (2, 0, 2, 2) in current and (2, 0, 1, 2) not in current
    retired = set(value[0] for value in old.values()) - set(value[0] for value in current.values())
    assert retired
    handle = _domain(buffer, 1)["unit_ids"][0].item()
    ids, errors, mask = _updates(buffer, 1, [99.0], [handle])
    _atomic(
        buffer, lambda: buffer.update_priorities(torch.tensor([handle, min(retired)]), errors.repeat(2, 1), loss_mask=mask.repeat(2, 1))
    )
    restored = _per(capacity=4, options=buffer.replay_options)
    validated = restored.validate_serialized(after, expected_obs_dim=2)
    restored.load_prepared(restored.materialize_validated(validated))
    _same(restored.serialize(), after)
    high, maximum = after["priority_state"]["next_unit_id"], after["priority_state"]["max_priority"]
    restored.clear()
    assert all(not len(d["unit_ids"]) for d in restored.serialize()["priority_state"]["domains"])
    _store(restored, 1, start=20)
    restored.sample_batch(_request(restored, 1))
    assert min(_domain(restored, 1)["unit_ids"]).item() >= high
    assert _domain(restored, 1)["priorities"].tolist() == [maximum]


def test_context_is_not_an_endpoint_or_a_row_coverage_count():
    buffer, model = _per(), _model()
    _store(buffer, 3)
    batches = [buffer.sample_batch(_request(buffer, length, 3)) for length in (1, 2)]
    domains = [_domain(buffer, length) for length in (1, 2)]
    assert set(domains[0]["unit_ids"].tolist()).isdisjoint(domains[1]["unit_ids"].tolist())
    losses = []
    for batch in batches:
        row = next(index for index, observation in enumerate(batch.observations) if observation[int(batch.lengths[index]) - 1, 0] == 0.4)
        output, _ = model(batch.observations[row : row + 1, : batch.lengths[row]])
        losses.append(output[0, -1].detach())
    assert not torch.allclose(*losses)


@pytest.mark.parametrize("objective", ["window_mean", "anchor_transition"])
@pytest.mark.parametrize("reducer,expected", [("max_abs", 8.0), ("mean_abs", 5.0)])
def test_priority_reduction_ignores_padding_and_merges_duplicates(objective, reducer, expected):
    buffer = _per(options=_options(objective=objective, reducer=reducer))
    _store(buffer, 2)
    buffer.sample_batch(_request(buffer, 4))
    domain = _domain(buffer, 4)
    ids, errors, mask = _updates(buffer, 4, [2.0, 2.0])
    errors[1, 1] = -8.0
    buffer.update_priorities(ids, errors, loss_mask=mask)
    want = 8.0 if objective == "anchor_transition" else expected
    np.testing.assert_allclose(_domain(buffer, 4)["priorities"], [2 + EPS, want + EPS])
    ids, errors, mask = _updates(buffer, 4, [3.0, 9.0], [int(domain["unit_ids"][1])] * 2)
    buffer.update_priorities(ids, errors, loss_mask=mask)
    np.testing.assert_allclose(_domain(buffer, 4)["priorities"][1], 9 + EPS)
    before = buffer.serialize()
    buffer.update_priorities(ids.flip(0), errors.flip(0), loss_mask=mask.flip(0))
    _same(buffer.serialize(), before)
    errors[0, mask[0]] = float("inf")
    _atomic(buffer, lambda: buffer.update_priorities(ids, errors, loss_mask=mask))
    bad = mask.clone()
    bad[0, -1] = True
    _atomic(buffer, lambda: buffer.update_priorities(ids, torch.ones_like(errors), loss_mask=bad))


def test_multiple_domain_priority_update_is_one_atomic_operation():
    buffer = _per(options=_options(reducer="mean_abs"))
    _store(buffer, 2)
    for length in (1, 2):
        buffer.sample_batch(_request(buffer, length))
    first = _updates(buffer, 1, [123.0], [_domain(buffer, 1)["unit_ids"][0].item()], width=2)
    second = _updates(buffer, 2, [float("inf")], [_domain(buffer, 2)["unit_ids"][-1].item()])
    ids, errors, mask = (torch.cat(items) for items in zip(first, second, strict=True))
    _atomic(buffer, lambda: buffer.update_priorities(ids, errors, loss_mask=mask))
    errors[1, mask[1]] = 1e308  # Stable mean must not overflow its intermediate sum.
    buffer.update_priorities(ids, errors, loss_mask=mask)
    assert _domain(buffer, 1)["priorities"][0].item() == pytest.approx(123 + EPS)
    assert _domain(buffer, 2)["priorities"][-1].item() == 1e308
    assert buffer.serialize()["priority_state"]["max_priority"] == 1e308


@pytest.mark.parametrize("family", ["PCG64", "PCG64DXSM", "MT19937", "Philox", "SFC64"])
def test_rng_codec_owned_roundtrip_and_failed_sample(family, tmp_path, monkeypatch):
    caller = np.random.Generator(getattr(np.random, family)(81))
    caller_before, external = copy.deepcopy(caller.bit_generator.state), _globals()
    buffer = _per(rng=caller, beta=0.4, annealing=True, tick=3)
    _store(buffer, 3, component="rewards_intrinsic")
    before = copy.deepcopy(buffer.serialize())
    with monkeypatch.context() as patch:

        def fail_batch(_self):
            raise ValueError("injected late batch validation")

        patch.setattr(ReplayBatch, "__post_init__", fail_batch)
        _atomic(buffer, lambda: buffer.sample_batch(_request(buffer, 2, 2)), "injected late")
    _same(buffer.serialize(), before)
    buffer.sample_batch(_request(buffer, 2, 2))
    _put(buffer, 2, [2, 3, 4])
    buffer.set_vector_tick(8)
    saved = copy.deepcopy(buffer.serialize())
    assert saved["format_version"] == 7 and saved["priority_state"]["rng"]["bit_generator"] == family
    assert set(saved) == set(
        "replay_kind format_version capacity num_transitions episodes action_dim legality_mode replay_options "
        "next_episode_id next_transition_id historical_archives priority_state".split()
    )
    assert set(saved["priority_state"]) == set(
        "priority_state_version alpha beta_initial beta beta_annealing beta_vector_tick_horizon current_vector_tick origin "
        "sampling_mode objective_unit weight_rule weight_normalization unit_identity_rule new_unit_priority_rule initial_priority "
        "priority_epsilon max_priority next_unit_id initialization rng domains".split()
    )
    source, destination = tmp_path / "source.pt", tmp_path / "relocated.pt"
    torch.save(saved, source)
    source.rename(destination)
    target = _per(beta=0.4, annealing=True)
    target.load_from_serialized(torch.load(destination, weights_only=False))
    _same(target.serialize(), saved)
    for _ in range(2):
        left, right = buffer.sample_batch(_request(buffer, 2, 3)), target.sample_batch(_request(target, 2, 3))
        _same(left.unit_ids, right.unit_ids)
        _same(left.weights, right.weights)
    owned = target.serialize()
    owned["priority_state"]["domains"][0]["priorities"].fill_(999)
    assert not bool((_domain(target, 2)["priorities"] == 999).any())
    _same(caller.bit_generator.state, caller_before)
    _same(_globals(), external)


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
@pytest.mark.parametrize("alpha,beta", [(1.0, 0.0), (1.0, 0.5), (0.5, 1.0)])
def test_extreme_support_and_tempered_actual_weights(mode, alpha, beta):
    buffer = _per(options=_options(mode), alpha=alpha, beta=beta, rng=_tape([0.0] * 16))
    _store(buffer, 2)
    buffer.sample_batch(_request(buffer, 1))
    _put(buffer, 1, [EPS, 1e308])
    before = copy.deepcopy(buffer.serialize())
    restored = _per(options=_options(mode), alpha=alpha, beta=beta)
    restored.load_from_serialized(before)
    _same(restored.serialize(), before)
    batch = restored.sample_batch(_request(restored, 1))
    assert batch.sampling.indices.tolist() == [0]
    assert 0 < batch.sampling.conditional_draw_probabilities[0] < 1e-100
    log_weight = -beta * (math.log(2) + math.log(batch.sampling.conditional_draw_probabilities[0]))
    assert batch.weights.item() == pytest.approx(math.exp(log_weight), rel=1e-12)
    assert torch.isfinite(batch.weights).all()


def test_extreme_full_population_roundtrip_survives_actual_b1_refusal_and_clock():
    buffer = _per(beta=0.0, annealing=True, rng=_tape([0.0] * 24))
    _store(buffer, 2)
    buffer.sample_batch(_request(buffer, 1))
    _put(buffer, 1, [EPS, 1e308])
    buffer.set_vector_tick(10)
    assert buffer.serialize()["priority_state"]["beta"] == 1.0
    saved = copy.deepcopy(buffer.serialize())
    target = _per(beta=0.0, annealing=True)
    target.load_from_serialized(saved)
    _same(target.serialize(), saved)
    _atomic(target, lambda: target.sample_batch(_request(target, 1)), "weight")
    full = target.sample_batch(_request(target, 1, 2))
    assert len(set(full.unit_ids.tolist())) == 2 and full.weights.tolist() == [1.0, 1.0]
    target.load_from_serialized(target.serialize())
    replacement = _per(options=_options(INDEPENDENT), rng=_tape([0.0] * 12))
    _store(replacement, 2)
    replacement.sample_batch(_request(replacement, 1))
    _put(replacement, 1, [EPS, 1e308])
    _atomic(replacement, lambda: replacement.sample_batch(_request(replacement, 1)), "weight")


@pytest.mark.parametrize("mode", [SUCCESSIVE, INDEPENDENT])
def test_alpha_zero_keeps_the_actual_law_specific_estimator(mode):
    buffer = _per(options=_options(mode), alpha=0.0, rng=_tape([0.5, 1 / 6, 0.75]))
    _store(buffer, 3)
    buffer.sample_batch(_request(buffer, 1))
    _put(buffer, 1, [EPS, 1e308, 4])
    sampled = buffer.sample_batch(_request(buffer, 1, 2))
    assert sampled.sampling.indices.tolist() == [0, 2]
    q, weights = ([1 / 3, 1 / 2], [4 / 3, 2 / 3]) if mode == SUCCESSIVE else ([1 / 3, 1 / 3], [1, 1])
    np.testing.assert_allclose(sampled.sampling.conditional_draw_probabilities, q, rtol=1e-13)
    np.testing.assert_allclose(sampled.weights, weights, rtol=1e-13)


@pytest.mark.parametrize("sequence,mode", [("adaptive_prefix", SUCCESSIVE), ("adaptive_prefix", INDEPENDENT), ("fixed_full", SUCCESSIVE)])
def test_readiness_and_absolute_beta_clock_are_observational(sequence, mode):
    buffer = _per(capacity=1, options=_options(mode, sequence), beta=0.2, annealing=True)
    _store(buffer, 1)
    before, external = copy.deepcopy(buffer.serialize()), _globals()
    ready = buffer.readiness(_request(buffer, 8, 2, 2))
    assert ready.reason == ("capacity_window_impossible" if sequence == "fixed_full" else "warmup")
    _same(buffer.serialize(), before)
    ready = buffer.readiness(_request(buffer, 8, 2))
    expected = "capacity_window_impossible" if sequence == "fixed_full" else ("batch_unavailable" if mode == SUCCESSIVE else "ready")
    assert ready.reason == expected and ready.retained_transitions == 1
    _same(buffer.serialize(), before)
    for tick, beta in [(0, 0.2), (5, 0.6), (5, 0.6), (10, 1.0), (30, 1.0)]:
        buffer.set_vector_tick(tick)
        state = buffer.serialize()["priority_state"]
        assert state["beta"] == pytest.approx(beta) and state["current_vector_tick"] == tick
        assert state["domains"] == []
    for invalid in (29, -1, True, 1.5):
        _atomic(buffer, lambda value=invalid: buffer.set_vector_tick(value))
    if mode == INDEPENDENT:
        sample = buffer.sample_batch(_request(buffer, 8, 2))
        assert sample.lengths.tolist() == [1, 1] and sample.loss_mask.sum().item() == 2
    _same(_globals(), external)


@pytest.mark.parametrize(
    "damage", ["version", "keys", "top_keys", "domain", "ids", "context", "priority", "epsilon", "max", "beta", "rng", "rng_state"]
)
def test_malformed_restore_refuses_before_any_target_install(damage, monkeypatch):
    source, target = _per(), _per()
    _store(source, 3)
    source.sample_batch(_request(source, 2))
    _store(target, 2, start=50)
    payload = copy.deepcopy(source.serialize())
    priority, domain = payload["priority_state"], payload["priority_state"]["domains"][0]
    if damage == "version":
        payload["format_version"] = True
    elif damage == "keys":
        priority["unknown"] = 1
    elif damage == "top_keys":
        payload["unknown"] = 1
    elif damage == "domain":
        domain["priorities"] = domain["priorities"][:-1]
    elif damage == "ids":
        domain["unit_ids"][1] = domain["unit_ids"][0]
    elif damage == "context":
        domain["window_keys"][0, 1] = 999
    elif damage == "priority":
        domain["priorities"][0] = float("inf")
    elif damage == "epsilon":
        domain["priorities"][0] = 1e-320  # Semantic-floor refusal, not a claimed PS support-path witness.
    elif damage == "max":
        priority["max_priority"] = 0.5
    elif damage == "beta":
        priority["beta"] = 0.25
    elif damage == "rng":
        priority["rng"]["bit_generator"] = "UnsupportedGenerator"
    else:
        priority["rng"]["state"]["state"]["state"] = -1
    original = copy.deepcopy(payload)
    _atomic(target, lambda: target.load_from_serialized(payload))
    _same(payload, original)
    good = source.serialize()
    before, external, original_good = copy.deepcopy(target.serialize()), _globals(), copy.deepcopy(good)
    validated = target.validate_serialized(good, expected_obs_dim=2)
    _same(target.serialize(), before)
    _same(good, original_good)
    with monkeypatch.context() as patch:

        def allocation_failure(*_args, **_kwargs):
            raise MemoryError("injected replay allocation")

        patch.setattr(torch.Tensor, "to", allocation_failure)
        with pytest.raises(MemoryError, match="injected replay"):
            target.materialize_validated(validated)
    _same(target.serialize(), before)
    _same(good, original_good)
    _same(source.serialize(), original_good)
    _same(_globals(), external)


@pytest.mark.parametrize("archive", [False, True])
def test_authentic_captured6_active_adapter_preserves_every_owned_row(archive):
    name = "sequence6-captured-with-sequence5-archive.pt" if archive else "sequence6-captured.pt"
    digest = (
        "0a40c2dbba0d64f804f91f1a5600994385777a660d4a40c851e7aa3111fa239b"
        if archive
        else "02e19371fc3131db51a9569fc6d5175de5a11416e2d6cea075d441ebd8bc8434"
    )
    assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest
    payload = torch.load(DATA / name, map_location="cpu", weights_only=False)
    original = copy.deepcopy(payload)
    options = _options(objective="anchor_transition", reducer="mean_abs")
    target = _per(capacity=3, action_dim=12, options=options, tick=37)
    rows = _rows(1, width=118, action_dim=12)
    target.store_captured_episode(
        rows, next_action_masks=torch.ones((1, 12), dtype=torch.bool), legality_recorded=torch.ones(1, dtype=torch.bool)
    )
    target.sample_batch(_request(target, 1))
    _put(target, 1, [99.0])
    high = target.serialize()["priority_state"]["next_unit_id"]
    target.load_for_mode(payload, requested_mode="recorded_full_resume")
    restored = target.serialize()
    assert restored["format_version"] == 7
    _same(
        {key: value for key, value in restored.items() if key not in ("format_version", "priority_state")},
        {key: value for key, value in payload.items() if key != "format_version"},
    )
    assert restored["priority_state"]["initialization"] == {
        "kind": "captured6_active_adapter",
        "source_replay_kind": "sequential",
        "source_format_version": 6,
    }
    assert restored["priority_state"]["domains"] == [] and restored["priority_state"]["current_vector_tick"] == 37
    assert restored["priority_state"]["max_priority"] == 1.0 and restored["priority_state"]["next_unit_id"] >= high
    assert target.retained_transitions == 3 and len(target.historical_archives) == int(archive)
    batch = target.sample_batch(_request(target, 8, 3))
    assert sorted(batch.lengths.tolist()) == [1, 1, 2]
    assert batch.weights.tolist() == [1.0] * 3 and batch.loss_mask.sum().item() == 3
    assert batch.legality_recorded[torch.arange(8)[None, :] < batch.lengths[:, None]].all()
    keys = dict(zip(_domain(target, 8)["unit_ids"].tolist(), _domain(target, 8)["window_keys"].tolist(), strict=True))
    for row, handle in enumerate(batch.unit_ids.tolist()):
        episode_id, first, end = keys[handle]
        episode = next(item for item in payload["episodes"] if item["episode_id"] == episode_id)
        positions = episode["transition_ids"].tolist()
        start, stop = positions.index(first), positions.index(end) + 1
        size = stop - start
        for field in ("observations", "next_observations", "actions", "dones", "next_action_masks"):
            _same(getattr(batch, field)[row, :size], episode[field][start:stop])
        for component in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
            presence = getattr(batch, f"{component}_present")[row]
            assert presence[:size].tolist() == [episode[component] is not None] * size and not presence[size:].any()
            if episode[component] is not None:
                _same(getattr(batch, component)[row, :size], episode[component][start:stop])
    uniform = SequentialReplayBuffer.for_replay(3, DEVICE, options=options, action_dim=12, legality_mode="captured")
    uniform.load_from_serialized(payload)
    _same(uniform.serialize(), original)
    adopting = SequentialReplayBuffer(3, DEVICE)
    adopting.load_from_serialized(target.serialize())
    _same(adopting.serialize(), target.serialize())
    _same(payload, original)
    assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest


def test_historical5_inspection_and_uniform_adapters_remain_distinct(tmp_path):
    old = SequentialReplayBuffer(8, DEVICE)
    old.store_episode(_rows(2, component="rewards_shaping"))
    payload = old.serialize()
    qualified = _per(capacity=8)
    qualified.load_from_serialized(payload)
    assert qualified.retained_transitions == 0 and qualified.serialize()["priority_state"]["domains"] == []
    assert qualified.readiness(_request(qualified, 2, minimum=1)).reason == "warmup"
    archive = qualified.historical_archives[0]
    _same(archive.original_state, payload)
    _same(archive.query_rows(offset=0, limit=2)["observations"], payload["episodes"][0]["observations"])
    exported = tmp_path / "archive.pt"
    receipt = archive.export(exported)
    assert receipt.row_count == 2 and receipt.source_digest == archive.source_digest and exported.is_file()
    _atomic(qualified, lambda: qualified.load_for_mode(payload, requested_mode="recorded_full_resume"))
    _store(qualified, 1, start=77)
    assert qualified.sample_batch(_request(qualified, 8)).observations[0, 0, 0].item() == 77
    inspection = SequentialReplayBuffer(8, DEVICE)
    inspection.load_from_serialized(payload)
    inspection.store_episode(_rows(1, start=99))
    envelope = inspection.serialize()
    assert set(envelope) == {"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"}
    restored = SequentialReplayBuffer(8, DEVICE)
    restored.load_from_serialized(envelope)
    assert restored.retained_transitions == 0 and len(restored.historical_archives) == 1
    assert restored.sample_sequences(2, 1)["observations"][:, :, 0].tolist() == [[99.0], [99.0]]
    _same(restored.serialize(), envelope)
    _atomic(qualified, lambda: qualified.load_from_serialized(envelope))
    for adapter in ("legacy_episode_length_with_replacement", "uniform_windows_with_replacement"):
        options = _options(sequence="fixed_full").model_copy(update={"uniform_sequence_adapter": adapter})
        uniform = SequentialReplayBuffer.for_replay(8, DEVICE, options=options, action_dim=3, legality_mode="captured")
        _store(uniform, 2)
        _store(uniform, 4, start=5)
        sampled = uniform.sample_batch(_request(uniform, 2, 8))
        assert sampled.sampling.mode == adapter and uniform.serialize()["format_version"] == 6
        want = 1 / (sampled.sampling.population_size * sampled.sampling.conditional_draw_probabilities)
        np.testing.assert_allclose(sampled.weights, want, rtol=1e-13)
        assert "priority_state" not in uniform.serialize()
    unconstrained = SequentialReplayBuffer.for_replay(8, DEVICE, options=_options(), action_dim=3, legality_mode="unconstrained")
    unconstrained.store_episode(_rows(1))
    assert unconstrained.sample_batch(_request(unconstrained, 8)).next_action_masks[0, 0].all()


@pytest.mark.parametrize(
    "arguments",
    [
        {"alpha": True},
        {"alpha": -0.1},
        {"beta": float("nan")},
        {"beta": 1.1},
        {"horizon": 0},
        {"tick": True},
        {"annealing": 1},
        {"origin": ""},
        {"capacity": True},
        {"options": ReplayOptions()},
    ],
)
def test_invalid_factory_arguments_do_not_mutate_caller_rng(arguments):
    rng = np.random.Generator(np.random.PCG64(44))
    before, external = copy.deepcopy(rng.bit_generator.state), _globals()
    with pytest.raises(ValueError):
        _per(rng=rng, **arguments)
    _same(rng.bit_generator.state, before)
    _same(_globals(), external)


def test_explicit_inactive_horizon_unsupported_codec_and_early_target_refusal():
    buffer = _per(beta=0.3, horizon=7, tick=100)
    buffer.set_vector_tick(101)
    state = buffer.serialize()["priority_state"]
    assert state["beta"] == 0.3 and state["beta_vector_tick_horizon"] == 7

    class Unsupported(np.random.PCG64):
        pass

    with pytest.raises(ValueError, match="codec|generator|Generator"):
        _per(rng=np.random.Generator(Unsupported(1)))
    _store(buffer, 2)
    buffer.sample_batch(_request(buffer, 2))
    uniform = SequentialReplayBuffer.for_replay(32, DEVICE, options=_options(), action_dim=3, legality_mode="captured")
    _store(uniform, 1, start=9)
    _atomic(uniform, lambda: uniform.validate_serialized(buffer.serialize(), expected_obs_dim=2))
    incompatible = _per(alpha=0.5, beta=0.3, horizon=7)
    _store(incompatible, 1, start=8)
    _atomic(incompatible, lambda: incompatible.validate_serialized(buffer.serialize(), expected_obs_dim=2))
