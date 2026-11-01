"""PER storage history: actual row identity, strict old access and owned legality."""

import copy
import hashlib
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from townlet.training import historical_checkpoint as history
from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayRequest


def buffer():
    return PrioritizedReplayBuffer(3, 0.6, 0.4, True, torch.device("cpu"))


def request(batch, minimum):
    return ReplayRequest(batch, 1, minimum, "successive_without_replacement", "feedforward", "transition")


def api(owner, name):
    method = getattr(owner, name, None)
    assert callable(method), f"T11 missing qualified PER API: {name}"
    return method


def rows(numbers, components):
    values = torch.tensor(numbers, dtype=torch.float32)
    observations = torch.stack((values, values + 100), dim=1)
    rewards = SimpleNamespace(total=values.clone(), extrinsic=values.clone() if components else None, intrinsic=None, shaping=None)
    actions = torch.tensor([int(number) % 3 for number in numbers], dtype=torch.int64)
    dones = torch.tensor([int(number) % 3 == 2 for number in numbers], dtype=torch.bool)
    masks = torch.zeros((len(numbers), 3), dtype=torch.bool)
    for index, number in enumerate(numbers):
        if not dones[index]:
            masks[index, (int(number) + 1) % 3] = True
    return observations, actions, rewards, observations + 1000, dones, masks


def push(owner, numbers, components):
    api(owner, "push_recorded")(*rows(numbers, components))


def equal(left, right):
    if isinstance(left, torch.Tensor):
        assert isinstance(right, torch.Tensor) and left.dtype == right.dtype and torch.equal(left, right)
    elif isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray) and left.dtype == right.dtype and np.array_equal(left, right)
    elif isinstance(left, dict):
        assert set(left) == set(right)
        for key in left:
            equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert type(left) is type(right) and len(left) == len(right)
        for one, two in zip(left, right, strict=True):
            equal(one, two)
    else:
        assert left == right


def old_state():
    """Exact native PER4 wire schema, independent of the current serializer."""
    obs, actions, rewards, successor, dones, _ = rows([3, 1, 2], True)
    return {
        "replay_kind": "prioritized",
        "format_version": 4,
        "capacity": 3,
        "alpha": 0.6,
        "beta": 1.0,
        "beta_initial": 0.4,
        "beta_annealing": True,
        "observations": obs,
        "actions": actions,
        "rewards": rewards.total,
        "rewards_extrinsic": rewards.extrinsic,
        "rewards_intrinsic": torch.zeros(3),
        "rewards_shaping": torch.zeros(3),
        "next_observations": successor,
        "dones": dones,
        "priorities": np.array([7.0, 11.0, 13.0], dtype=np.float32),
        "max_priority": 13.0,
        "position": 1,
        "size_current": 3,
    }


def assert_batch(batch, expected):
    assert batch.legality_recorded.all() and batch.loss_mask.all()
    assert batch.lengths.tolist() == [1] * len(expected)
    for index, number in enumerate(expected):
        obs, action, reward, successor, done, mask = rows([number], True)
        equal(batch.observations[index], obs[0])
        equal(batch.next_observations[index], successor[0])
        equal(batch.actions[index], action[0])
        equal(batch.rewards[index], reward.total[0])
        equal(batch.dones[index], done[0])
        equal(batch.next_action_masks[index], mask[0])
    equal(batch.weights.cpu().numpy(), batch.sampling.weights)


def test_per_old_strict_validator_beta_and_legacy_sample_positive(monkeypatch):
    owner = buffer()
    before = owner.serialize()
    rng = torch.get_rng_state().clone()
    source = old_state()
    owner.validate_serialized(source, expected_obs_dim=2)
    equal(owner.serialize(), before)
    equal(torch.get_rng_state(), rng)
    assert owner.beta_initial == 0.4 and source["beta"] == 1.0
    args = rows([0, 1, 2], True)
    owner.push(*args[:5])
    monkeypatch.setattr(np.random, "choice", lambda *args, **kwargs: np.array([2, 0], dtype=np.int64))
    sample = owner.sample(2)
    assert {"observations", "actions", "rewards", "next_observations", "dones", "indices", "weights"} <= set(sample)
    assert sample["indices"].tolist() == [2, 0]
    assert sample["observations"][:, 0].tolist() == [2.0, 0.0]
    assert sample["weights"].dtype == torch.float32
    owner.anneal_beta(10, 10)
    assert owner.beta == 1.0 and owner.beta_initial == 0.4


def test_per_mask_priority_alignment_and_restore(monkeypatch):
    owner = buffer()
    owner.validate_serialized(old_state(), expected_obs_dim=2)
    push(owner, [0, 1, 2], True)
    owner.update_priorities(np.array([0, 1, 2]), torch.tensor([2.0, 4.0, 8.0]))
    push(owner, [3, 4], True)
    state = owner.serialize()
    assert state["format_version"] == 6 and state["position"] == 2
    assert state["observations"][:, 0].tolist() == [3.0, 4.0, 2.0]
    restored = buffer()
    restored.load_from_serialized(state)
    equal(restored.serialize(), state)
    monkeypatch.setattr(np.random, "choice", lambda *args, **kwargs: np.array([2, 0, 1], dtype=np.int64))
    for current in (owner, restored):
        batch = api(current, "sample_batch")(request(3, 3))
        assert batch.sampling.indices.tolist() == [2, 0, 1]
        assert batch.unit_ids.tolist() == [2, 3, 4]
        assert_batch(batch, [2, 3, 4])
        equal(batch.rewards_extrinsic, batch.rewards)
    batch.next_action_masks.fill_(True)
    equal(restored.serialize(), state)
    state["observations"].fill_(-10)
    assert restored.serialize()["observations"][:, 0].tolist() == [3.0, 4.0, 2.0]


@pytest.mark.parametrize("defect", ["mask_dtype", "mask_width", "mask_count", "empty_live", "action", "recorded", "unknown", "presence"])
def test_per_current_restore_refuses_atomically(defect):
    owner = buffer()
    push(owner, [0, 1, 2], True)
    owner.anneal_beta(10, 10)
    before = owner.serialize()
    damaged = copy.deepcopy(before)
    if defect == "mask_dtype":
        damaged["next_action_masks"] = damaged["next_action_masks"].float()
    elif defect == "mask_width":
        damaged["action_dim"] = 4
    elif defect == "mask_count":
        damaged["next_action_masks"] = damaged["next_action_masks"][:-1]
    elif defect == "empty_live":
        damaged["next_action_masks"][0].fill_(False)
    elif defect == "action":
        damaged["actions"][0] = 3
    elif defect == "recorded":
        damaged["legality_recorded"][0] = False
    elif defect == "presence":
        damaged["rewards_extrinsic_present"][0] = False
        damaged["rewards_extrinsic"][0] = 99
    else:
        damaged["unknown"] = True
    frozen = copy.deepcopy(damaged)
    with pytest.raises(ValueError):
        owner.load_from_serialized(damaged)
    equal(owner.serialize(), before)
    equal(damaged, frozen)


def test_per_optional_presence_overwrite_and_readiness():
    owner = buffer()
    push(owner, [0, 1, 2], True)
    push(owner, [3], False)
    batch = api(owner, "sample_batch")(request(3, 0))
    indices = batch.sampling.indices.tolist()
    assert_batch(batch, [[3, 1, 2][index] for index in indices])
    assert batch.rewards_extrinsic_present.tolist() == [index != 0 for index in indices]
    assert batch.rewards_extrinsic[indices.index(0)].item() == 0
    assert batch.rewards_intrinsic is None and not batch.rewards_intrinsic_present.any()
    assert batch.rewards_shaping is None and not batch.rewards_shaping_present.any()
    assert owner.retained_transitions == 3
    ready = api(owner, "readiness")(request(2, 1000))
    assert not ready.ready and ready.reason == "warmup" and ready.retained_transitions == 3
    assert api(owner, "readiness")(request(3, 3)).ready
    with pytest.raises(ValueError):
        api(owner, "readiness")(ReplayRequest(1, 2, 0, "successive_without_replacement", "fixed_full", "window_mean"))


def test_per_old_archive_query_export_fresh_active_and_current_roundtrip(tmp_path):
    state = old_state()
    source = tmp_path / "native-per4.pt"
    torch.save(state, source)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    loaded = torch.load(source, weights_only=False)
    owner = buffer()
    owner.validate_serialized(loaded, expected_obs_dim=2)
    owner.load_from_serialized(loaded)
    assert len(owner) == 0, "T11 approved PER4 import must archive, never activate unknown legality"
    assert owner.beta == 1.0 and owner.beta_initial == 0.4
    assert owner.position == 0 and owner.max_priority == 1.0 and not owner.priorities.any()
    archives = owner.historical_archives
    assert len(archives) == 1 and archives[0].archived_row_count == 3
    archive = archives[0]
    assert archive.source_formats == {"scope": "standalone_replay", "replay": 4, "replay_kind": "prioritized"}
    assert archive.approval_reference == history.APPROVAL_REFERENCE
    assert archive.reward_semantics == "historical_recorded_pre_fix"
    equal(archive.original_state, state)
    queried = archive.query_rows(offset=1, limit=2)
    for name in ("observations", "next_observations", "actions", "rewards", "dones"):
        equal(queried[name], state[name][1:])
    equal(queried["priorities"].numpy(), state["priorities"][1:])
    receipt = archive.export(tmp_path / "export.pt")
    equal(torch.load(receipt.destination, weights_only=False), state)
    assert receipt.row_count == 3 and receipt.source_digest == archive.source_digest
    queried["priorities"].fill_(-1)
    loaded["priorities"].fill(999)
    equal(owner.historical_archives[0].original_state, state)
    push(owner, [0, 1], True)
    assert not api(owner, "readiness")(request(1, 1000)).ready
    batch = api(owner, "sample_batch")(request(2, 0))
    assert set(batch.observations[:, 0].tolist()) == {0.0, 1.0}
    owner.update_priorities(batch.sampling.indices, torch.tensor([2.0, 3.0]))
    equal(owner.historical_archives[0].original_state, state)
    current = owner.serialize()
    second = buffer()
    api(second, "load_for_mode")(current, requested_mode="recorded_full_resume")
    equal(second.serialize(), current)
    third = buffer()
    third.load_from_serialized(second.serialize())
    equal(third.serialize(), current)
    assert third.retained_transitions == 2 and len(third.historical_archives) == 1
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("defect", ["beta", "initial", "position", "maximum", "extra"])
def test_per_old_validator_remains_strict_and_pure(defect):
    owner = buffer()
    good = old_state()
    owner.validate_serialized(good, expected_obs_dim=2)
    damaged = copy.deepcopy(good)
    if defect == "beta":
        damaged["beta"] = 0.2
    elif defect == "initial":
        damaged["beta_initial"] = 1.0
    elif defect == "position":
        damaged["position"] = 3
    elif defect == "maximum":
        damaged["max_priority"] = 1.0
    else:
        damaged["extra"] = None
    before = owner.serialize()
    with pytest.raises(ValueError):
        owner.validate_serialized(damaged, expected_obs_dim=2)
    equal(owner.serialize(), before)


def test_per_modes_and_archive_failure_leave_populated_target_unchanged(monkeypatch):
    owner = buffer()
    push(owner, [0, 1], True)
    before = owner.serialize()
    load = api(owner, "load_for_mode")
    with pytest.raises(HistoricalLegalityUnavailable):
        load(old_state(), requested_mode="recorded_full_resume")
    equal(owner.serialize(), before)
    with pytest.raises(ValueError):
        load(before, requested_mode="archived_history_fresh_episode")
    equal(owner.serialize(), before)

    def fail_archive(state):
        raise OSError("archive preparation failed")

    monkeypatch.setattr(history, "archive_standalone_replay", fail_archive)
    with pytest.raises(OSError, match="archive preparation"):
        load(old_state(), requested_mode="auto")
    equal(owner.serialize(), before)


def test_per_current_archive_corruption_and_empty_restore():
    owner = buffer()
    owner.load_from_serialized(old_state())
    assert len(owner) == 0, "old unknown-mask rows must be archived before current restore"
    empty = owner.serialize()
    target = buffer()
    push(target, [0, 1], True)
    api(target, "load_for_mode")(empty, requested_mode="recorded_full_resume")
    equal(target.serialize(), empty)
    push(target, [0], True)
    before = target.serialize()
    damaged = copy.deepcopy(before)
    damaged["historical_archives"][0]["original_state"]["priorities"][0] += 1
    with pytest.raises(ValueError):
        target.load_from_serialized(damaged)
    equal(target.serialize(), before)


def test_per_unconstrained_adapter_requires_declared_geometry_before_qualified_sampling():
    owner = buffer()
    owner.push(*rows([0], True)[:5])
    assert owner.sample(1)["actions"].tolist() == [0]
    ready = api(owner, "readiness")(request(1, 0))
    assert not ready.ready and ready.sampleable_units == 0
    push(owner, [1], True)
    batch = api(owner, "sample_batch")(request(2, 0))
    zero = batch.observations[:, 0].tolist().index(0.0)
    assert batch.next_action_masks[zero].tolist() == [True, True, True]
    assert batch.legality_recorded.all()
    before = owner.serialize()
    arguments = list(rows([0], True))
    arguments[-1] = torch.ones((1, 4), dtype=torch.bool)
    with pytest.raises(ValueError):
        api(owner, "push_recorded")(*arguments)
    equal(owner.serialize(), before)


def test_per_clear_retains_owned_archive_and_rejects_changed_domain():
    owner = buffer()
    archive = history.archive_standalone_replay(old_state())
    install = api(owner, "install_historical_archive")
    install(archive)
    install(archive)
    assert len(owner.historical_archives) == 1
    push(owner, [0, 1], True)
    owner.clear()
    assert len(owner) == 0 and owner.retained_transitions == 0
    equal(owner.historical_archives[0].original_state, old_state())
    state = owner.serialize()
    corrupted = copy.deepcopy(state)
    corrupted["historical_archives"][0]["source_formats"]["replay_kind"] = "standard"
    with pytest.raises(ValueError):
        owner.load_from_serialized(corrupted)
    equal(owner.serialize(), state)
