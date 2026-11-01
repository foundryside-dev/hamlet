"""Sequence storage: real windows, owned legality and preserved old inspection."""

import copy
import hashlib
import random

import numpy as np
import pytest
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.training import historical_checkpoint as history
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer

DEVICE = torch.device("cpu")
COMPONENTS = ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping")
OLD_KEYS = {"replay_kind", "format_version", "capacity", "num_transitions", "episodes"}
CURRENT_KEYS = OLD_KEYS | {"action_dim", "legality_mode", "replay_options", "next_episode_id", "next_transition_id", "historical_archives"}


def api(owner, name):
    method = getattr(owner, name, None)
    assert callable(method), f"T12 missing qualified sequence API: {name}"
    return method


def options(window, retention, objective, adapter, sampling):
    return ReplayOptions(
        sampling_mode=sampling,
        uniform_sequence_adapter=adapter,
        sequence_mode=window,
        retention_mode=retention,
        sequence_objective=objective,
        priority_reduction="max_abs",
    )


def qualified(capacity, policy, legality):
    return api(SequentialReplayBuffer, "for_replay")(capacity, DEVICE, options=policy, action_dim=3, legality_mode=legality)


def request(policy, batch, length, minimum):
    return ReplayRequest(batch, length, minimum, policy.sampling_mode, policy.sequence_mode, policy.sequence_objective)


def episode(numbers, components, terminal):
    values = torch.tensor(numbers, dtype=torch.float32)
    obs = torch.stack((values, values + 100), dim=1)
    done = torch.zeros(len(numbers), dtype=torch.bool)
    done[-1] = terminal
    result = {
        "observations": obs,
        "actions": values.to(torch.int64) % 3,
        "rewards": values + 0.25,
        "next_observations": obs + 1000,
        "dones": done,
    }
    if components:
        result["rewards_extrinsic"] = values * 10 + 7
    masks = torch.zeros((len(numbers), 3), dtype=torch.bool)
    for index, number in enumerate(numbers):
        if not done[index]:
            masks[index, (number + 1) % 3] = True
    return result, masks


def store(owner, numbers, components, terminal):
    data, masks = episode(numbers, components, terminal)
    api(owner, "store_captured_episode")(data, next_action_masks=masks, legality_recorded=torch.ones(len(numbers), dtype=torch.bool))
    return data, masks


def equal(left, right):
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and left.dtype == right.dtype and torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray) and left.dtype == right.dtype and np.array_equal(left, right)
    elif isinstance(left, dict):
        assert set(left) == set(right)
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (tuple, list)):
        assert type(left) is type(right) and len(left) == len(right)
        for one, two in zip(left, right, strict=True):
            equal(one, two)
    else:
        assert left == right


def catalog(*inputs):
    result = {}
    for data, masks in inputs:
        for index, number in enumerate(data["observations"][:, 0].tolist()):
            result[int(number)] = ({key: value[index].clone() for key, value in data.items()}, masks[index].clone())
    return result


def check_batch(batch, allowed, rows, objective):
    selected_presence = {name: False for name in COMPONENTS}
    for index, length in enumerate(batch.lengths.tolist()):
        codes = tuple(int(value) for value in batch.observations[index, :length, 0].tolist())
        assert codes in allowed
        expected_loss = [True] * length if objective == "window_mean" else [False] * (length - 1) + [True]
        assert batch.loss_mask[index].tolist() == expected_loss + [False] * (batch.loss_mask.shape[1] - length)
        assert batch.legality_recorded[index, :length].all()
        for step, code in enumerate(codes):
            data, masks = rows[code]
            for name in ("observations", "actions", "rewards", "next_observations", "dones"):
                equal(getattr(batch, name)[index, step], data[name])
            equal(batch.next_action_masks[index, step], masks)
            for name in COMPONENTS:
                present = name in data
                assert getattr(batch, f"{name}_present")[index, step].item() == present
                selected_presence[name] |= present
                value = getattr(batch, name)
                if present:
                    equal(value[index, step], data[name])
                elif value is not None:
                    assert value[index, step].item() == 0
        for name in COMPONENTS:
            assert not getattr(batch, f"{name}_present")[index, length:].any()
            value = getattr(batch, name)
            if value is not None:
                assert not value[index, length:].any()
    for name, present in selected_presence.items():
        assert (getattr(batch, name) is not None) == present
    assert batch.weights.dtype == torch.float64
    equal(batch.weights.cpu().numpy(), batch.sampling.weights)
    equal(batch.unit_ids.cpu().numpy(), batch.sampling.indices)


def old_state(interior):
    owner = SequentialReplayBuffer(10, DEVICE)
    data, _ = episode([30, 31, 32], True, False)
    if interior:
        data["dones"][1] = True
    owner.store_episode(data)
    state = owner.serialize()
    assert state["format_version"] == 5 and state["replay_kind"] == "sequential" and set(state) == OLD_KEYS
    assert set(state["episodes"][0]) == {"observations", "actions", "rewards", "next_observations", "dones", *COMPONENTS}
    return owner, state


def load_mode(owner, state, mode):
    return api(owner, "load_for_mode")(state, requested_mode=mode)


def test_legacy_postterminal_sampling_and_strict5_inspection_remain_callable(monkeypatch):
    owner, state = old_state(True)
    before = copy.deepcopy(state)
    rng = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    owner.validate_serialized(state, expected_obs_dim=2)
    equal(state, before)
    equal((random.getstate(), np.random.get_state(), torch.get_rng_state()), rng)
    monkeypatch.setattr(random, "choices", lambda population, weights, k: [population[0]])
    monkeypatch.setattr(random, "randint", lambda lower, upper: 0)
    batch = owner.sample_sequences(4, 3)
    assert batch["mask"].tolist() == [[True, True, False]] * 4
    assert batch["observations"][:, :, 0].tolist() == [[30, 31, 32]] * 4
    equal(batch["next_observations"][0], before["episodes"][0]["next_observations"])
    damaged = copy.deepcopy(before)
    damaged["episodes"][0]["actions"][0] = -1
    owner.validate_serialized(damaged, expected_obs_dim=2)  # Structural inspection, not valid-action learning.
    equal(owner.serialize(), before)
    assert len(owner) == 1 and owner.num_transitions == 3


def test_legacy_input_and_serialized_tensors_are_owned(monkeypatch):
    owner = SequentialReplayBuffer(10, DEVICE)
    data, _ = episode([0, 1], True, False)
    owner.store_episode(data)
    expected = copy.deepcopy(owner.serialize())
    for value in data.values():
        value.fill_(0)
    equal(owner.serialize(), expected)
    output = owner.serialize()
    output["episodes"][0]["next_observations"].fill_(-99)
    equal(owner.serialize(), expected)
    monkeypatch.setattr(random, "choices", lambda population, weights, k: [population[0]])
    monkeypatch.setattr(random, "randint", lambda lower, upper: 0)
    assert owner.sample_sequences(1, 2)["observations"][0, :, 0].tolist() == [0, 1]


def test_sixteen_short_episodes_do_not_crash():
    for mode in ("fixed_full", "adaptive_prefix"):
        policy = options(mode, "whole_episode", "window_mean", "legacy_episode_length_with_replacement", "successive_without_replacement")
        owner = qualified(40, policy, "captured")
        inputs = [store(owner, [10 * number, 10 * number + 1], True, False) for number in range(16)]
        asked = request(policy, 16, 3, 32)
        ready = api(owner, "readiness")(asked)
        assert ready.retained_transitions == owner.retained_transitions == 32
        if mode == "fixed_full":
            assert not ready.ready and ready.sampleable_units == 0 and ready.reason == "window_unavailable"
            with pytest.raises(ValueError):
                api(owner, "sample_batch")(asked)
        else:
            assert ready.ready and ready.sampleable_units == 32
            allowed = {(10 * number,) for number in range(16)} | {(10 * number, 10 * number + 1) for number in range(16)}
            batch = api(owner, "sample_batch")(asked)
            assert batch.observations.shape == (16, 3, 2)
            check_batch(batch, allowed, catalog(*inputs), "window_mean")


@pytest.mark.parametrize("adapter", ["legacy_episode_length_with_replacement", "uniform_windows_with_replacement"])
def test_capacity15_has_viable_two_step_windows(adapter):
    policy = options("fixed_full", "whole_episode", "window_mean", adapter, "successive_without_replacement")
    owner = qualified(15, policy, "captured")
    inputs = [store(owner, [10 * number, 10 * number + 1], False, False) for number in range(16)]
    asked = request(policy, 16, 2, 14)
    ready = api(owner, "readiness")(asked)
    assert ready.ready and ready.retained_transitions == 14 and ready.sampleable_units == 7
    allowed = {(10 * number, 10 * number + 1) for number in range(9, 16)}
    batch = api(owner, "sample_batch")(asked)
    check_batch(batch, allowed, catalog(*inputs), "window_mean")
    assert len(set(batch.unit_ids.tolist())) < 16  # B>M necessarily repeats actual units.
    assert batch.sampling.mode == adapter and batch.sampling.population_size == 7


def test_capacity1_adaptive_retains_one_real_row():
    policy = options(
        "adaptive_prefix", "transition_tail", "anchor_transition", "legacy_episode_length_with_replacement", "independent_with_replacement"
    )
    owner = qualified(1, policy, "captured")
    source = store(owner, [0, 1, 2], True, True)
    asked = request(policy, 4, 8, 1)
    ready = api(owner, "readiness")(asked)
    assert ready.ready and ready.retained_transitions == ready.sampleable_units == 1
    batch = api(owner, "sample_batch")(asked)
    assert batch.observations.shape == (4, 8, 2)
    check_batch(batch, {(2,)}, catalog(source), "anchor_transition")
    state = owner.serialize()
    assert state["episodes"][0]["start_offset"] == 2 and state["episodes"][0]["original_length"] == 3
    fixed = options("fixed_full", "transition_tail", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement")
    target = qualified(1, fixed, "captured")
    store(target, [3], False, False)
    impossible = api(target, "readiness")(request(fixed, 1, 8, 1000))
    assert not impossible.ready and impossible.reason == "capacity_window_impossible" and impossible.retained_transitions == 1
    whole = options("adaptive_prefix", "whole_episode", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement")
    complete = qualified(1, whole, "captured")
    store(complete, [4, 5], False, False)
    assert complete.retained_transitions == 0  # Complete-episode selection remains available.


@pytest.mark.parametrize("objective", ["window_mean", "anchor_transition"])
def test_fragment_masks_stable_ids_and_current6_resume(objective):
    policy = options("adaptive_prefix", "transition_tail", objective, "uniform_windows_with_replacement", "successive_without_replacement")
    owner = qualified(4, policy, "captured")
    first = store(owner, [0, 1, 2], True, False)
    original_ids = owner.serialize()["episodes"][0]["transition_ids"].clone()
    second = store(owner, [10, 11, 12], False, True)
    state = owner.serialize()
    assert set(state) == CURRENT_KEYS and state["format_version"] == 6
    assert state["num_transitions"] == 4 and state["action_dim"] == 3 and state["legality_mode"] == "captured"
    fragment = state["episodes"][0]
    assert fragment["start_offset"] == 2 and fragment["original_length"] == 3
    equal(fragment["transition_ids"], original_ids[-1:])
    assert state["episodes"][1]["episode_id"] > fragment["episode_id"]
    assert state["episodes"][1]["transition_ids"].min() > original_ids.max()
    before = copy.deepcopy(state)
    for data, masks in (first, second):
        for value in data.values():
            value.fill_(0)
        masks.fill_(True)
    equal(owner.serialize(), before)
    target = qualified(4, policy, "captured")
    store(target, [99], True, False)
    load_mode(target, state, "recorded_full_resume")
    equal(target.serialize(), before)
    state["episodes"][0]["next_action_masks"].fill_(False)
    equal(target.serialize(), before)
    allowed = {(2,), (10,), (10, 11), (10, 11, 12)}
    expected = catalog(episode([0, 1, 2], True, False), episode([10, 11, 12], False, True))
    batch = api(target, "sample_batch")(request(policy, 32, 3, 4))
    check_batch(batch, allowed, expected, objective)
    endpoints = {
        int(code): int(unit) for ep in before["episodes"] for code, unit in zip(ep["observations"][:, 0], ep["transition_ids"], strict=True)
    }
    for index, length in enumerate(batch.lengths.tolist()):
        assert batch.unit_ids[index].item() == endpoints[int(batch.observations[index, length - 1, 0])]
    batch.next_action_masks.fill_(False)
    equal(target.serialize(), before)
    store(target, [20], True, False)
    after = target.serialize()
    assert after["next_transition_id"] > before["next_transition_id"]
    assert after["episodes"][-1]["transition_ids"].min() >= before["next_transition_id"]


@pytest.mark.parametrize("mode", ["fixed_full", "adaptive_prefix"])
@pytest.mark.parametrize("adapter", ["legacy_episode_length_with_replacement", "uniform_windows_with_replacement"])
@pytest.mark.parametrize("sampling", ["successive_without_replacement", "independent_with_replacement"])
def test_actual_sequence_proposals_and_receipt_weights(mode, adapter, sampling):
    policy = options(mode, "whole_episode", "window_mean", adapter, sampling)
    owner = qualified(10, policy, "captured")
    store(owner, [0, 1, 2], True, False)
    store(owner, [10, 11, 12, 13, 14], False, False)
    previous_rng = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    random.seed(20261101)
    np.random.seed(20261101)
    torch.manual_seed(20261101)
    try:
        batch = api(owner, "sample_batch")(request(policy, 4096, 3, 8))
    finally:
        random.setstate(previous_rng[0])
        np.random.set_state(previous_rng[1])
        torch.set_rng_state(previous_rng[2])
    endpoints = batch.observations[torch.arange(4096), batch.lengths - 1, 0].to(torch.int64).numpy()
    assert batch.observations.shape == (4096, 3, 2)
    windows = {0: (0,), 1: (0, 1), 2: (0, 1, 2), 10: (10,), 11: (10, 11), 12: (10, 11, 12), 13: (11, 12, 13), 14: (12, 13, 14)}
    for index, length in enumerate(batch.lengths.tolist()):
        assert tuple(batch.observations[index, :length, 0].tolist()) == windows[int(endpoints[index])]
    if mode == "fixed_full":
        assert set(endpoints.tolist()) == {2, 12, 13, 14}
        expected_p = np.full(4096, 0.25, dtype=np.float64)
        if adapter == "legacy_episode_length_with_replacement":
            expected_p = np.where(endpoints == 2, 3 / 8, 5 / 24)
        population = 4
    else:
        assert set(endpoints.tolist()) == {0, 1, 2, 10, 11, 12, 13, 14}
        expected_p = np.full(4096, 1 / 8, dtype=np.float64)
        population = 8
    np.testing.assert_allclose(batch.sampling.conditional_draw_probabilities, expected_p, rtol=0, atol=1e-12)
    np.testing.assert_allclose(batch.sampling.weights, 1 / (population * expected_p), rtol=0, atol=1e-12)
    for endpoint in set(endpoints.tolist()):
        frequency = float(np.mean(endpoints == endpoint))
        proposal = float(expected_p[np.flatnonzero(endpoints == endpoint)[0]])
        assert abs(frequency - proposal) < 0.04
    assert batch.sampling.mode == adapter and batch.sampling.objective_unit == "window"
    assert batch.sampling.population_size == population
    nonuniform = mode == "fixed_full" and adapter == "legacy_episode_length_with_replacement"
    assert batch.sampling.weight_rule == ("inverse_population_proposal" if nonuniform else "uniform")
    equal(batch.weights.cpu().numpy(), batch.sampling.weights)
    assert len(set(batch.unit_ids.tolist())) == population


def test_component_presence_and_unconstrained_adapter(monkeypatch):
    policy = options(
        "fixed_full", "whole_episode", "anchor_transition", "legacy_episode_length_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    first = store(owner, [0, 1], True, False)
    second = store(owner, [10, 11], False, False)
    choices = iter([0, 1, 0, 1])
    monkeypatch.setattr(random, "choices", lambda population, weights, k: [population[next(choices)]])
    monkeypatch.setattr(random, "randint", lambda lower, upper: 0)
    batch = api(owner, "sample_batch")(request(policy, 4, 2, 4))
    check_batch(batch, {(0, 1), (10, 11)}, catalog(first, second), "anchor_transition")
    assert batch.rewards_extrinsic_present.tolist() == [[True, True], [False, False]] * 2
    assert batch.sampling.objective_unit == "anchor_transition"
    choices = iter([0])
    all_present = api(owner, "sample_batch")(request(policy, 1, 2, 0))
    assert all_present.rewards_extrinsic_present.all()
    equal(all_present.rewards_extrinsic[0], first[0]["rewards_extrinsic"])
    unconstrained = qualified(10, policy, "unconstrained")
    unconstrained.store_episode(episode([20, 21], False, False)[0])
    choices = iter([0])
    assert api(unconstrained, "sample_batch")(request(policy, 1, 2, 0)).next_action_masks.all()
    with pytest.raises(HistoricalLegalityUnavailable):
        owner.store_episode(episode([30], False, False)[0])
    legacy = SequentialReplayBuffer(10, DEVICE)
    legacy.store_episode(episode([40], False, False)[0])
    with pytest.raises(ValueError):
        api(legacy, "readiness")(request(policy, 1, 1, 0))
    assert legacy.retained_transitions == 0 and legacy.num_transitions == 1


@pytest.mark.parametrize(
    "defect", ["mask_dtype", "mask_width", "mask_count", "unrecorded", "empty_live", "negative_action", "action", "interior", "nan"]
)
def test_captured_admission_refuses_atomically(defect):
    policy = options(
        "adaptive_prefix", "transition_tail", "anchor_transition", "uniform_windows_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    store(owner, [20, 21], True, False)
    before = owner.serialize()
    data, masks = episode([0, 1, 2], True, True)
    recorded = torch.ones(3, dtype=torch.bool)
    if defect == "mask_dtype":
        masks = masks.float()
    elif defect == "mask_width":
        masks = torch.ones((3, 4), dtype=torch.bool)
    elif defect == "mask_count":
        masks = masks[:-1]
    elif defect == "unrecorded":
        recorded[0] = False
    elif defect == "empty_live":
        masks[0].fill_(False)
    elif defect == "negative_action":
        data["actions"][0] = -1
    elif defect == "action":
        data["actions"][0] = 3
    elif defect == "interior":
        data["dones"][0] = True
    else:
        data["rewards_extrinsic"][0] = float("nan")
    source = copy.deepcopy((data, masks, recorded))
    with pytest.raises(ValueError):
        api(owner, "store_captured_episode")(data, next_action_masks=masks, legality_recorded=recorded)
    equal(owner.serialize(), before)
    if defect != "nan":
        equal((data, masks, recorded), source)
    else:
        for name, value in data.items():
            torch.testing.assert_close(value, source[0][name], rtol=0, atol=0, equal_nan=True)
        equal(masks, source[1])
        equal(recorded, source[2])


def test_sequence5_interior_terminal_archive_fidelity(tmp_path, monkeypatch):
    legacy, state = old_state(True)
    before = copy.deepcopy(state)
    legacy.validate_serialized(state, expected_obs_dim=2)
    monkeypatch.setattr(random, "choices", lambda population, weights, k: [population[0]])
    monkeypatch.setattr(random, "randint", lambda lower, upper: 0)
    assert legacy.sample_sequences(1, 3)["mask"].tolist() == [[True, True, False]]
    source = tmp_path / "original-sequential5.pt"
    torch.save(state, source)
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    loaded = torch.load(source, weights_only=False)
    archive = history.archive_standalone_replay(loaded)
    assert archive.archived_row_count == 3
    assert archive.source_formats == {"scope": "standalone_replay", "replay": 5, "replay_kind": "sequential"}
    assert archive.reward_semantics == "historical_recorded_pre_fix" and archive.approval_reference == history.APPROVAL_REFERENCE
    equal(archive.original_state, before)
    queried = archive.query_rows(offset=0, limit=3)
    for name in ("observations", "actions", "rewards", "next_observations", "dones", "rewards_extrinsic"):
        equal(queried[name], before["episodes"][0][name])
    assert queried["episode_ids"].tolist() == [0, 0, 0]
    receipt = archive.export(tmp_path / "export.pt")
    equal(torch.load(receipt.destination, weights_only=False), before)
    assert receipt.row_count == 3 and receipt.source_digest == archive.source_digest
    loaded["episodes"][0]["observations"].fill_(-99)
    queried["next_observations"].fill_(-99)
    equal(archive.original_state, before)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_digest


def test_old5_auto_import_archives_instead_of_activating_rows():
    _, state = old_state(False)
    owner = SequentialReplayBuffer(10, DEVICE)
    owner.load_from_serialized(state)
    assert owner.num_transitions == 0 and len(owner) == 0, "approved old5 import must archive and start fresh"
    assert owner.retained_transitions == 0
    equal(owner.historical_archives[0].original_state, state)
    with pytest.raises(ValueError):
        owner.sample_sequences(1, 1)
    second = SequentialReplayBuffer(10, DEVICE)
    validated = second.validate_serialized(state, expected_obs_dim=2)
    second.load_prepared(second.materialize_validated(validated))
    assert second.num_transitions == 0 and second.retained_transitions == 0
    equal(second.historical_archives[0].original_state, state)


def test_old5_modes_fresh_readiness_and_current6_with_history_resume():
    policy = options(
        "adaptive_prefix", "transition_tail", "anchor_transition", "uniform_windows_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    store(owner, [90], True, False)
    before = owner.serialize()
    _, old = old_state(True)
    frozen_old = copy.deepcopy(old)
    with pytest.raises(HistoricalLegalityUnavailable):
        load_mode(owner, old, "recorded_full_resume")
    equal(owner.serialize(), before)
    equal(old, frozen_old)
    owner.load_from_serialized(old)
    assert owner.retained_transitions == owner.num_transitions == 0
    equal(owner.historical_archives[0].original_state, frozen_old)
    fresh = api(owner, "readiness")(request(policy, 4, 3, 1000))
    assert not fresh.ready and fresh.reason == "warmup" and fresh.sampleable_units == 0
    new = store(owner, [0, 1], True, False)
    warming = api(owner, "readiness")(request(policy, 1, 3, 1000))
    assert not warming.ready and warming.reason == "warmup" and warming.retained_transitions == 2
    batch = api(owner, "sample_batch")(request(policy, 8, 3, 0))
    check_batch(batch, {(0,), (0, 1)}, catalog(new), "anchor_transition")
    current = owner.serialize()
    target = qualified(10, policy, "captured")
    store(target, [80, 81], False, False)
    load_mode(target, current, "recorded_full_resume")
    equal(target.serialize(), current)
    second = qualified(10, policy, "captured")
    second.load_from_serialized(target.serialize())
    equal(second.serialize(), current)
    assert second.retained_transitions == 2 and len(second.historical_archives) == 1
    with pytest.raises(ValueError):
        load_mode(target, current, "archived_history_fresh_episode")
    equal(target.serialize(), current)
    current["historical_archives"][0]["original_state"]["episodes"][0]["rewards"].fill_(-99)
    equal(target.serialize(), second.serialize())
    next_id = target.serialize()["next_transition_id"]
    target.clear()
    assert target.retained_transitions == 0 and len(target.historical_archives) == 1
    equal(target.historical_archives[0].original_state, frozen_old)
    store(target, [10], False, False)
    assert target.serialize()["episodes"][0]["transition_ids"].min() >= next_id


@pytest.mark.parametrize("defect", ["unknown", "version", "kind", "capacity", "count", "width", "dtype", "nan"])
def test_old5_pure_validation_remains_strict(defect):
    owner, good = old_state(True)
    damaged = copy.deepcopy(good)
    if defect == "unknown":
        damaged["extra"] = 1
    elif defect == "version":
        damaged["format_version"] = 4
    elif defect == "kind":
        damaged["replay_kind"] = "standard"
    elif defect == "capacity":
        damaged["capacity"] = 11
    elif defect == "count":
        damaged["num_transitions"] = 2
    elif defect == "width":
        damaged["episodes"][0]["next_observations"] = torch.zeros((3, 3))
    elif defect == "dtype":
        damaged["episodes"][0]["actions"] = damaged["episodes"][0]["actions"].float()
    else:
        damaged["episodes"][0]["rewards"][0] = float("nan")
    with pytest.raises(ValueError):
        owner.validate_serialized(damaged, expected_obs_dim=2)
    equal(owner.serialize(), good)


@pytest.mark.parametrize("defect", ["unknown", "short", "width", "mask", "recorded", "id", "counter", "fragment", "component", "options"])
def test_current6_restore_refuses_atomically(defect):
    policy = options(
        "adaptive_prefix", "transition_tail", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    store(owner, [0, 1], True, False)
    before = owner.serialize()
    damaged = copy.deepcopy(before)
    row = damaged["episodes"][0]
    if defect == "unknown":
        damaged["extra"] = True
    elif defect == "short":
        row["observations"] = row["observations"][:-1]
    elif defect == "width":
        damaged["action_dim"] = 4
    elif defect == "mask":
        row["next_action_masks"] = row["next_action_masks"].float()
    elif defect == "recorded":
        row["legality_recorded"][0] = False
    elif defect == "id":
        row["transition_ids"][1] = row["transition_ids"][0]
    elif defect == "counter":
        damaged["next_transition_id"] = int(row["transition_ids"].max())
    elif defect == "fragment":
        row["start_offset"] = row["original_length"]
    elif defect == "component":
        row["rewards_extrinsic"] = row["rewards_extrinsic"][:-1]
    else:
        damaged["replay_options"] = {**policy.model_dump(), "sequence_mode": None}
    frozen = copy.deepcopy(damaged)
    with pytest.raises(ValueError):
        owner.load_from_serialized(damaged)
    equal(owner.serialize(), before)
    equal(damaged, frozen)


def test_archive_preparation_dedup_corruption_and_late_failure_are_atomic(monkeypatch):
    policy = options(
        "adaptive_prefix", "transition_tail", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    store(owner, [0, 1], True, False)
    before = owner.serialize()
    _, old = old_state(False)
    standalone = history.archive_standalone_replay(old)
    other_legacy = SequentialReplayBuffer(10, DEVICE)
    other_legacy.store_episode(episode([80, 81], False, False)[0])
    other = history.archive_standalone_replay(other_legacy.serialize())
    candidate = api(owner, "prepare_archived_import")((standalone, other, standalone), expected_obs_dim=2)
    equal(owner.serialize(), before)
    owner.load_prepared(candidate)
    assert owner.retained_transitions == 0 and len(owner.historical_archives) == 2
    assert {archive.source_digest for archive in owner.historical_archives} == {standalone.source_digest, other.source_digest}
    store(owner, [10], False, False)
    current = owner.serialize()
    damaged = copy.deepcopy(current)
    damaged["historical_archives"][0]["original_state"]["episodes"][0]["rewards"][0] += 1
    with pytest.raises(ValueError):
        owner.load_from_serialized(damaged)
    equal(owner.serialize(), current)
    real_materialize = owner._materialize_serialized

    def fail_after_real_preparation(validated):
        real_materialize(validated)
        raise OSError("late sequence materialization failure")

    monkeypatch.setattr(owner, "_materialize_serialized", fail_after_real_preparation)
    with pytest.raises(OSError, match="late sequence materialization"):
        owner.load_from_serialized(current)
    equal(owner.serialize(), current)


def test_empty_current6_and_conflicting_requests_preserve_configured_identity():
    policy = options(
        "adaptive_prefix", "transition_tail", "anchor_transition", "uniform_windows_with_replacement", "successive_without_replacement"
    )
    owner = qualified(10, policy, "captured")
    empty = owner.serialize()
    assert set(empty) == CURRENT_KEYS and empty["format_version"] == 6
    assert empty["action_dim"] == 3 and empty["legality_mode"] == "captured"
    assert empty["num_transitions"] == 0 and empty["episodes"] == [] and empty["historical_archives"] == []
    store(owner, [0], False, False)
    load_mode(owner, empty, "recorded_full_resume")
    equal(owner.serialize(), empty)
    ready = api(owner, "readiness")(request(policy, 1, 3, 0))
    assert not ready.ready and ready.reason == "window_unavailable" and ready.sampleable_units == 0
    for conflict in (
        ReplayRequest(1, 3, 0, "independent_with_replacement", "adaptive_prefix", "anchor_transition"),
        ReplayRequest(1, 3, 0, "successive_without_replacement", "fixed_full", "anchor_transition"),
        ReplayRequest(1, 3, 0, "successive_without_replacement", "adaptive_prefix", "window_mean"),
    ):
        with pytest.raises(ValueError):
            api(owner, "readiness")(conflict)
    with pytest.raises(ValueError):
        api(SequentialReplayBuffer, "for_replay")(10, DEVICE, options=ReplayOptions(), action_dim=3, legality_mode="captured")
    equal(owner.serialize(), empty)


def test_captured_outputs_detach_autograd_inputs():
    policy = options("fixed_full", "whole_episode", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement")
    owner = qualified(10, policy, "captured")
    data, masks = episode([0, 1], True, False)
    for name in ("observations", "next_observations", "rewards", "rewards_extrinsic"):
        data[name].requires_grad_()
    api(owner, "store_captured_episode")(data, next_action_masks=masks, legality_recorded=torch.ones(2, dtype=torch.bool))
    batch = api(owner, "sample_batch")(request(policy, 1, 2, 0))
    for name in ("observations", "next_observations", "rewards", "rewards_extrinsic"):
        assert not getattr(batch, name).requires_grad
        assert not owner.serialize()["episodes"][0][name].requires_grad
        assert data[name].requires_grad


@pytest.mark.parametrize("new_legacy_rows", [False, True])
def test_legacy_import_second_save_relocation_preserves_archives_and_new_transport(tmp_path, monkeypatch, new_legacy_rows):
    _, first = old_state(True)
    second_producer = SequentialReplayBuffer(10, DEVICE)
    second_producer.store_episode(episode([40, 41], False, False)[0])
    second = second_producer.serialize()
    assert set(second) == OLD_KEYS and second["format_version"] == 5
    owner = SequentialReplayBuffer(10, DEVICE)
    owner.load_from_serialized(first)
    owner.load_from_serialized(second)
    initial = {archive.source_digest: history._record(archive) for archive in owner.historical_archives}
    assert len(initial) == 2
    assert {record["archived_row_count"] for record in initial.values()} == {2, 3}
    original_states = [record["original_state"] for record in initial.values()]
    assert any(torch.equal(state["episodes"][0]["observations"], first["episodes"][0]["observations"]) for state in original_states)
    assert any(torch.equal(state["episodes"][0]["observations"], second["episodes"][0]["observations"]) for state in original_states)
    if new_legacy_rows:
        owner.store_episode(episode([80, 81], True, False)[0])
    assert owner.retained_transitions == 0 and owner.action_dim is None and owner.replay_options is None
    portable = owner.serialize()
    assert portable.get("format_version") != 6, "unconfigured inspection must not invent qualified6 legality/options"
    destination = tmp_path / "relocated"
    destination.mkdir()
    artifact = destination / "sequential-inspection.pt"
    torch.save(portable, artifact)
    artifact_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    supplied = torch.load(artifact, weights_only=False)
    before_supplied = copy.deepcopy(supplied)
    restored = SequentialReplayBuffer(10, DEVICE)
    restored.load_from_serialized(supplied)
    equal(supplied, before_supplied)
    actual = {archive.source_digest: history._record(archive) for archive in restored.historical_archives}
    assert set(actual) == set(initial), "second public save/load lost or relabeled original historical archive identities"
    equal(actual, initial)

    def overwrite_tensors(value):
        if isinstance(value, torch.Tensor):
            value.fill_(-99)
        elif isinstance(value, dict):
            for child in value.values():
                overwrite_tensors(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                overwrite_tensors(child)

    overwrite_tensors(supplied)
    assert restored.retained_transitions == 0 and restored.action_dim is None and restored.replay_options is None
    monkeypatch.setattr(random, "choices", lambda population, weights, k: [population[0]])
    monkeypatch.setattr(random, "randint", lambda lower, upper: 0)
    if new_legacy_rows:
        assert restored.num_transitions == 2 and len(restored) == 1
        sampled = restored.sample_sequences(4, 2)
        assert sampled["observations"][:, :, 0].tolist() == [[80, 81]] * 4
        assert sampled["next_observations"][:, :, 0].tolist() == [[1080, 1081]] * 4
        assert sampled["mask"].all()
    else:
        assert restored.num_transitions == 0 and len(restored) == 0
        with pytest.raises(ValueError):
            restored.sample_sequences(1, 1)
    for index, archive in enumerate(restored.historical_archives):
        record = initial[archive.source_digest]
        expected = record["original_state"]["episodes"][0]
        queried = archive.query_rows(offset=0, limit=archive.archived_row_count)
        for name in ("observations", "actions", "rewards", "next_observations", "dones"):
            equal(queried[name], expected[name])
        for name in COMPONENTS:
            if expected[name] is None:
                assert not queried[f"{name}_present"].any()
            else:
                equal(queried[name], expected[name])
        receipt = archive.export(destination / f"archive-{index}.pt")
        equal(torch.load(receipt.destination, weights_only=False), record["original_state"])
        assert receipt.source_digest == archive.source_digest and receipt.row_count == archive.archived_row_count
        queried["observations"].fill_(-99)
    equal({archive.source_digest: history._record(archive) for archive in restored.historical_archives}, initial)
    another = SequentialReplayBuffer(10, DEVICE)
    another.load_from_serialized(restored.serialize())
    equal({archive.source_digest: history._record(archive) for archive in another.historical_archives}, initial)
    assert another.retained_transitions == 0 and another.num_transitions == restored.num_transitions
    if new_legacy_rows:
        assert another.sample_sequences(1, 2)["observations"][0, :, 0].tolist() == [80, 81]
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == artifact_digest


def inspection_state():
    _, old = old_state(False)
    owner = SequentialReplayBuffer(10, DEVICE)
    owner.load_from_serialized(old)
    owner.store_episode(episode([80, 81], True, False)[0])
    state = owner.serialize()
    assert set(state) == {"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"}
    assert state["inspection_kind"] == "sequential_replay_inspection" and type(state["inspection_version"]) is int
    assert state["inspection_version"] == 1 and set(state["legacy_transport"]) == OLD_KEYS
    return state


@pytest.mark.parametrize(
    "path,value",
    [
        (("extra",), 1),
        (("inspection_kind",), "wrong"),
        (("inspection_kind",), "__remove__"),
        (("inspection_version",), True),
        (("inspection_version",), 1.0),
        (("inspection_version",), 2),
        (("legacy_transport", "extra"), 1),
        (("legacy_transport", "num_transitions"), 1),
        (("legacy_transport", "format_version"), 6),
        (("legacy_transport", "episodes", 0, "actions"), None),
        (("historical_archives", 0, "source_digest"), "corrupt"),
        (("historical_archives", 0, "archived_row_count"), 99),
        (("historical_archives", 0, "extra"), 1),
    ],
)
def test_inspection_corruption_refuses_before_populated_target_or_rng_mutation(path, value):
    damaged = inspection_state()
    cursor = damaged
    for part in path[:-1]:
        cursor = cursor[part]
    if value == "__remove__":
        del cursor[path[-1]]
    else:
        cursor[path[-1]] = value
    target, old = old_state(True)
    target.load_from_serialized(old)
    target.store_episode(episode([90, 91], False, False)[0])
    before, source = target.serialize(), copy.deepcopy(damaged)
    rng = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone())
    with pytest.raises(ValueError):
        target.load_from_serialized(damaged)
    equal(target.serialize(), before)
    equal(damaged, source)
    equal((random.getstate(), np.random.get_state(), torch.get_rng_state()), rng)


@pytest.mark.parametrize("mode", ["auto", "inference", "archived_history_fresh_episode"])
def test_inspection_modes_preserve_new_rows_and_union_target_history(mode):
    state = inspection_state()
    target, old = old_state(True)
    target.load_from_serialized(old)
    target.store_episode(episode([90, 91], False, False)[0])
    before = target.serialize()
    validated = target.validate_serialized(state, expected_obs_dim=2)
    equal(target.serialize(), before)
    target.load_prepared(target.materialize_validated(validated))
    load_mode(target, state, mode)
    assert len(target.historical_archives) == 2 and target.retained_transitions == 0 and target.num_transitions == 2
    assert target.action_dim is None and target.replay_options is None
    assert target.sample_sequences(1, 2)["observations"][0, :, 0].tolist() == [80, 81]
    empty = copy.deepcopy(state)
    empty["historical_archives"] = []
    plain = SequentialReplayBuffer(10, DEVICE)
    plain.load_from_serialized(empty)
    assert not plain.historical_archives and set(plain.serialize()) == OLD_KEYS and plain.num_transitions == 2


def test_inspection_full_resume_configured_downgrade_and_late_failure_refuse_atomically(monkeypatch):
    state = inspection_state()
    target = SequentialReplayBuffer(10, DEVICE)
    target.store_episode(episode([90, 91], False, False)[0])
    before, source = target.serialize(), copy.deepcopy(state)
    with pytest.raises(HistoricalLegalityUnavailable):
        load_mode(target, state, "recorded_full_resume")
    equal(target.serialize(), before)
    policy = options("fixed_full", "whole_episode", "window_mean", "uniform_windows_with_replacement", "successive_without_replacement")
    captured = qualified(10, policy, "captured")
    store(captured, [10], True, False)
    captured_before = captured.serialize()
    with pytest.raises(ValueError):
        captured.load_from_serialized(state)
    equal(captured.serialize(), captured_before)
    materialize = target._materialize_serialized

    def fail_after_preparation(validated):
        materialize(validated)
        raise OSError("late inspection preparation")

    monkeypatch.setattr(target, "_materialize_serialized", fail_after_preparation)
    with pytest.raises(OSError, match="late inspection preparation"):
        target.load_from_serialized(state)
    equal(target.serialize(), before)
    equal(state, source)
