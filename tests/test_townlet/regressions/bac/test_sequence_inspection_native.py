"""Actual population inspection transport; not complete native or learner qualification."""

from __future__ import annotations

import copy
from collections.abc import Mapping

import pytest
import torch

from townlet.curriculum.static import StaticCurriculum
from townlet.exploration.epsilon_greedy import EpsilonGreedyExploration
from townlet.population.vectorized import VectorizedPopulation
from townlet.training.replay_contract import HistoricalLegalityUnavailable, ReplayRequest
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer


def _equal(expected, actual):
    assert type(actual) is type(expected)
    if isinstance(expected, torch.Tensor):
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.device == expected.device
        assert torch.equal(actual, expected)
    elif isinstance(expected, Mapping):
        assert actual.keys() == expected.keys()
        for key in expected:
            _equal(expected[key], actual[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for left, right in zip(expected, actual, strict=True):
            _equal(left, right)
    else:
        assert actual == expected


def _population(env_factory, device, brain):
    env = env_factory(num_agents=1, device_override=device)
    population = VectorizedPopulation(
        env=env,
        curriculum=StaticCurriculum(difficulty_level=0.5),
        exploration=EpsilonGreedyExploration(epsilon=0.8, epsilon_min=0.1, epsilon_decay=0.999),
        agent_ids=["inspection-agent"],
        device=device,
        brain_config=brain,
        obs_dim=env.observation_dim,
        action_dim=env.action_dim,
        train_frequency=10000,
        batch_size=2,
        sequence_length=3,
        max_grad_norm=10.0,
    )
    assert population.is_recurrent and not population.use_per
    assert isinstance(population.replay_buffer, SequentialReplayBuffer)
    # Exercise the native constructor as shipped, without replacing its buffer.
    assert population.replay_buffer.action_dim is None
    assert population.replay_buffer.replay_options is None
    assert population.replay_buffer.serialize()["format_version"] == 5
    return population


def _episode(width, reward, *, interior_terminal):
    observations = torch.arange(3 * width, dtype=torch.float32).reshape(3, width) / 100
    return {
        "observations": observations,
        "actions": torch.zeros(3, dtype=torch.int64),
        "rewards": torch.tensor([reward, reward + 1, reward + 2], dtype=torch.float32),
        "rewards_extrinsic": torch.tensor([0.25, 0.5, 0.75], dtype=torch.float32),
        "rewards_shaping": torch.tensor([-0.25, 0.0, 0.25], dtype=torch.float32),
        "next_observations": observations + 0.125,
        "dones": torch.tensor([False, True, False] if interior_terminal else [False, False, True]),
    }


def _native_state(population):
    # Native state_dict tensors can alias their producer; own every comparison oracle.
    return copy.deepcopy(population.get_checkpoint_state())


def _assert_learned_fields(expected, actual):
    assert expected.keys() == actual.keys()
    for key in expected:
        if key != "replay_buffer":
            _equal(expected[key], actual[key])


def _relocated_checkpoint(state, root, name):
    original = root / f"{name}.pt"
    relocated_dir = root / f"{name}-relocated"
    relocated_dir.mkdir()
    torch.save(state, original)
    relocated = original.rename(relocated_dir / "population.pt")
    result = torch.load(relocated, map_location="cpu", weights_only=False)
    _equal(state, result)
    return result


def _assert_inspection(population, old_state, digest, new_episode):
    buffer = population.replay_buffer
    assert isinstance(buffer, SequentialReplayBuffer)
    assert buffer.retained_transitions == 0
    assert buffer.action_dim is None and buffer.replay_options is None and buffer.legality_mode == "legacy"
    archives = buffer.historical_archives
    assert len(archives) == 1
    archive = archives[0]
    assert archive.source_formats == {"scope": "standalone_replay", "replay": 5, "replay_kind": "sequential"}
    assert archive.source_digest == digest and archive.archived_row_count == 3
    assert archive.reward_semantics == "historical_recorded_pre_fix"
    assert archive.approval_reference == "BAC-HISTORY-A-2026-11-01"
    _equal(old_state, archive.original_state)
    rows = archive.query_rows(offset=0, limit=3)
    for name, values in old_state["episodes"][0].items():
        if values is None:
            assert name not in rows
        else:
            _equal(values, rows[name])
    for name in ("rewards_extrinsic", "rewards_intrinsic", "rewards_shaping"):
        expected = old_state["episodes"][0][name] is not None
        _equal(torch.full((3,), expected, dtype=torch.bool), rows[f"{name}_present"])
    _equal(torch.zeros(3, dtype=torch.int64), rows["episode_ids"])
    if new_episode is None:
        assert buffer.num_transitions == buffer.legacy_transport_transitions == len(buffer) == 0
        with pytest.raises(ValueError, match="buffer is empty"):
            buffer.sample_sequences(batch_size=1, seq_len=3)
    else:
        assert buffer.num_transitions == buffer.legacy_transport_transitions == 3 and len(buffer) == 1
        sample = buffer.sample_sequences(batch_size=1, seq_len=3)
        for name in ("observations", "actions", "rewards", "dones", "next_observations"):
            _equal(new_episode[name], sample[name][0])
        _equal(torch.ones((1, 3), dtype=torch.bool), sample["mask"])
        assert not torch.isin(sample["rewards"], old_state["episodes"][0]["rewards"]).any()
    request = ReplayRequest(
        batch_size=1,
        sequence_length=3,
        min_transitions=1,
        sampling_mode="successive_without_replacement",
        sequence_mode="fixed_full",
        sequence_objective="window_mean",
    )
    with pytest.raises(HistoricalLegalityUnavailable, match="for_replay"):
        buffer.readiness(request)
    with pytest.raises(HistoricalLegalityUnavailable, match="for_replay"):
        buffer.sample_batch(request)
    envelope = buffer.serialize()
    assert set(envelope) == {"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"}
    assert envelope["inspection_kind"] == "sequential_replay_inspection"
    assert type(envelope["inspection_version"]) is int and envelope["inspection_version"] == 1
    transport = envelope["legacy_transport"]
    assert set(transport) == {"replay_kind", "format_version", "capacity", "num_transitions", "episodes"}
    assert transport["format_version"] == 5 and transport["replay_kind"] == "sequential"
    assert transport["num_transitions"] == (0 if new_episode is None else 3)
    if new_episode is None:
        assert transport["episodes"] == []
    else:
        assert len(transport["episodes"]) == 1
        for name, values in new_episode.items():
            _equal(values, transport["episodes"][0][name])
        assert transport["episodes"][0]["rewards_intrinsic"] is None
    assert len(envelope["historical_archives"]) == 1
    assert set(envelope["historical_archives"][0]) == {
        "source_formats",
        "original_state",
        "source_digest",
        "archived_row_count",
        "reward_semantics",
        "approval_reference",
    }
    return envelope


@pytest.mark.parametrize("new_legacy_rows", [False, True], ids=["archive-only", "separate-new-legacy"])
def test_native_recurrent_inspection_archive_relocation(env_factory, cpu_device, recurrent_brain_config, tmp_path, new_legacy_rows):
    source = _population(env_factory, cpu_device, recurrent_brain_config)
    old_episode = _episode(source.env.observation_dim, 101.0, interior_terminal=True)
    source.replay_buffer.store_episode(old_episode)
    old_replay = copy.deepcopy(source.replay_buffer.serialize())
    assert old_replay["format_version"] == 5 and old_replay["num_transitions"] == 3
    legacy_sample = source.replay_buffer.sample_sequences(batch_size=1, seq_len=3)
    _equal(torch.tensor([[True, True, False]]), legacy_sample["mask"])
    _equal(old_episode["next_observations"], legacy_sample["next_observations"][0])
    source.replay_buffer.validate_serialized(old_replay, expected_obs_dim=source.env.observation_dim)
    # Distinct transport clock witness, not a claim of optimizer learning.
    source.total_steps = 17
    original_native = _native_state(source)
    original_file = tmp_path / "original-population.pt"
    torch.save(original_native, original_file)

    imported = _population(env_factory, cpu_device, recurrent_brain_config)
    assert imported.total_steps != original_native["total_steps"]
    pristine = _native_state(imported)
    imported.validate_checkpoint_state(original_native)
    _equal(pristine, _native_state(imported))
    imported.load_checkpoint_state(original_native)
    _assert_learned_fields(original_native, _native_state(imported))
    assert imported.replay_buffer.retained_transitions == imported.replay_buffer.num_transitions == 0
    archive = imported.replay_buffer.historical_archives[0]
    _equal(old_replay, archive.original_state)
    digest = archive.source_digest
    new_episode = _episode(source.env.observation_dim, 7.0, interior_terminal=False) if new_legacy_rows else None
    if new_episode is not None:
        imported.replay_buffer.store_episode(new_episode)
    envelope = _assert_inspection(imported, old_replay, digest, new_episode)
    first_native = _native_state(imported)
    _equal(envelope, first_native["replay_buffer"])

    for generation in (1, 2):
        loaded = _relocated_checkpoint(first_native, tmp_path, f"inspection-{generation}")
        restored = _population(env_factory, cpu_device, recurrent_brain_config)
        before_restore = _native_state(restored)
        restored.validate_checkpoint_state(loaded)
        _equal(before_restore, _native_state(restored))
        restored.load_checkpoint_state(loaded)
        _equal(first_native, _native_state(restored))
        _assert_learned_fields(original_native, _native_state(restored))
        _equal(envelope, _assert_inspection(restored, old_replay, digest, new_episode))
        export = restored.replay_buffer.historical_archives[0].export(tmp_path / f"history-{generation}.pt")
        assert export.source_digest == digest and export.row_count == 3
        _equal(old_replay, torch.load(export.destination, map_location="cpu", weights_only=False))
        _equal(first_native, loaded)
        first_native = _native_state(restored)  # Second pass uses an actual native resave.

    _equal(original_native, torch.load(original_file, map_location="cpu", weights_only=False))
    _equal(original_native, _native_state(source))
    _equal(old_replay, source.replay_buffer.serialize())
