"""Unit tests for SequentialReplayBuffer edge cases.

CRIT-07: Updated to use single 'rewards' field (DAC-composed totals).
"""

from __future__ import annotations

import copy

import pytest
import torch

from townlet.config.bac_options import ReplayOptions
from townlet.training.replay_contract import HistoricalLegalityUnavailable
from townlet.training.sequential_replay_buffer import SequentialReplayBuffer


def qualified_buffer(capacity: int) -> SequentialReplayBuffer:
    # Newly authored synthetic rows explicitly declare an unconstrained vocabulary.
    return SequentialReplayBuffer.for_replay(
        capacity,
        torch.device("cpu"),
        options=ReplayOptions(
            sampling_mode="successive_without_replacement",
            uniform_sequence_adapter="legacy_episode_length_with_replacement",
            sequence_mode="fixed_full",
            retention_mode="whole_episode",
            sequence_objective="window_mean",
            priority_reduction="max_abs",
        ),
        action_dim=8,
        legality_mode="unconstrained",
    )


def assert_exact_state(expected, actual):
    assert type(actual) is type(expected)
    if isinstance(expected, torch.Tensor):
        assert expected.dtype == actual.dtype and expected.shape == actual.shape and expected.device == actual.device
        assert torch.equal(expected, actual)
    elif isinstance(expected, dict):
        assert expected.keys() == actual.keys()
        for key in expected:
            assert_exact_state(expected[key], actual[key])
    elif isinstance(expected, (list, tuple)):
        assert len(expected) == len(actual)
        for left, right in zip(expected, actual, strict=True):
            assert_exact_state(left, right)
    else:
        assert expected == actual


def make_episode(length: int, *, reward_value: float = 1.0) -> dict[str, torch.Tensor]:
    """Create test episode with single rewards field (CRIT-07).

    Args:
        length: Number of timesteps in episode
        reward_value: Value for all rewards (default 1.0)

    Returns:
        Episode dict with observations, actions, rewards (DAC-composed), dones,
        and next_observations (WS-1(c): required successor observations)
    """
    obs = torch.arange(length * 2, dtype=torch.float32).view(length, 2)
    actions = torch.arange(length, dtype=torch.long)
    dones = torch.zeros(length, dtype=torch.bool)
    dones[-1] = True

    episode: dict[str, torch.Tensor] = {
        "observations": obs,
        "actions": actions,
        "rewards": torch.full((length,), reward_value),  # CRIT-07: Single rewards field
        "dones": dones,
        "next_observations": obs + 2.0,  # successor of obs[t] is obs[t+1] in this layout
    }

    return episode


class TestSequentialReplayBuffer:
    def test_store_episode_eviction(self):
        buffer = SequentialReplayBuffer(capacity=5, device=torch.device("cpu"))

        buffer.store_episode(make_episode(3))
        buffer.store_episode(make_episode(4))

        # Capacity 5 → first episode evicted (3 transitions) when second (4) inserted
        assert len(buffer) == 1
        assert buffer.num_transitions == 4

    def test_sample_sequences_masks_post_terminal(self, monkeypatch):
        """CRIT-07: Test masking with DAC-composed rewards."""
        buffer = SequentialReplayBuffer(capacity=20, device=torch.device("cpu"))
        buffer.store_episode(make_episode(6, reward_value=2.0))  # CRIT-07: Pre-composed reward

        # Force deterministic choice
        monkeypatch.setattr("random.choice", lambda seq: seq[0])
        monkeypatch.setattr("random.randint", lambda a, b: 0)

        # MED-13: intrinsic_weight parameter removed
        batch = buffer.sample_sequences(batch_size=1, seq_len=4)
        mask = batch["mask"][0]

        # Terminal at final timestep (index 3) → mask all True
        assert mask[-1]
        assert torch.equal(mask, torch.ones_like(mask))

        rewards = batch["rewards"][0]
        # CRIT-07/MED-13: Rewards are DAC-composed totals stored directly in buffer
        assert torch.allclose(rewards, torch.full((4,), 2.0))

    def test_sample_sequences_requires_long_enough_episode(self):
        buffer = SequentialReplayBuffer(capacity=20, device=torch.device("cpu"))
        buffer.store_episode(make_episode(3))

        with pytest.raises(ValueError):  # type: ignore[name-defined]
            buffer.sample_sequences(batch_size=1, seq_len=5)

    def test_serialize_and_restore(self):
        """Current qualified replay retains active rows and single rewards."""
        buffer = qualified_buffer(10)
        buffer.store_episode(make_episode(4))

        state = buffer.serialize()

        restored = qualified_buffer(10)
        restored.load_from_serialized(state)

        assert state["format_version"] == 6
        assert_exact_state(state, restored.serialize())
        assert len(restored) == 1
        batch = restored.sample_sequences(batch_size=1, seq_len=2)
        assert batch["observations"].shape == (1, 2, 2)


class TestSequentialReplayBufferClearAPI:
    """Test clear() method for sequential buffer."""

    def test_clear_resets_episodes(self):
        """clear() should remove all episodes."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        buffer.store_episode(make_episode(5))  # CRIT-07: Use single rewards field
        buffer.store_episode(make_episode(7))

        assert len(buffer) == 2
        assert buffer.num_transitions == 12

        buffer.clear()

        assert len(buffer) == 0
        assert buffer.num_transitions == 0
        assert len(buffer.episodes) == 0

    def test_clear_idempotence(self):
        """Calling clear() multiple times should be safe."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Clear empty buffer
        buffer.clear()
        assert len(buffer) == 0

        # Add episodes and clear
        buffer.store_episode(make_episode(5))  # CRIT-07: Use single rewards field
        buffer.clear()

        # Clear again
        buffer.clear()
        assert len(buffer) == 0
        assert buffer.num_transitions == 0

    def test_buffer_works_after_clear(self):
        """Buffer should work normally after clear()."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Fill buffer
        buffer.store_episode(make_episode(10))  # CRIT-07: Use single rewards field
        buffer.clear()

        # Should be able to store episodes again
        buffer.store_episode(make_episode(5))  # CRIT-07: Use single rewards field
        assert len(buffer) == 1
        assert buffer.num_transitions == 5

        # Should be able to sample
        batch = buffer.sample_sequences(batch_size=1, seq_len=3)
        assert batch["observations"].shape == (1, 3, 2)


class TestSequentialReplayBufferRewardComponents:
    """Test optional reward component storage."""

    def test_episode_with_components_stores_correctly(self):
        """Episode with reward components should store all fields."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Create episode with components
        episode = make_episode(5, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((5,), 0.5)
        episode["rewards_intrinsic"] = torch.full((5,), 0.3)
        episode["rewards_shaping"] = torch.full((5,), 0.2)

        buffer.store_episode(episode)

        assert len(buffer) == 1
        stored_episode = buffer.episodes[0]
        assert "rewards_extrinsic" in stored_episode
        assert "rewards_intrinsic" in stored_episode
        assert "rewards_shaping" in stored_episode
        assert torch.allclose(stored_episode["rewards_extrinsic"], torch.full((5,), 0.5))
        assert torch.allclose(stored_episode["rewards_intrinsic"], torch.full((5,), 0.3))
        assert torch.allclose(stored_episode["rewards_shaping"], torch.full((5,), 0.2))

    def test_episode_without_components_still_works(self):
        """Episode reward components remain optional in the current format."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Create episode without components
        episode = make_episode(5, reward_value=1.0)

        buffer.store_episode(episode)

        assert len(buffer) == 1
        stored_episode = buffer.episodes[0]
        assert "rewards_extrinsic" not in stored_episode
        assert "rewards_intrinsic" not in stored_episode
        assert "rewards_shaping" not in stored_episode

    def test_serialization_format_version_5(self):
        """Serialized buffer has format_version 5 and carries next_observations."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Add episode with components
        episode = make_episode(4, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((4,), 0.6)
        episode["rewards_intrinsic"] = torch.full((4,), 0.2)
        episode["rewards_shaping"] = torch.full((4,), 0.2)
        buffer.store_episode(episode)

        serialized = buffer.serialize()

        assert serialized["format_version"] == 5
        assert len(serialized["episodes"]) == 1
        assert "next_observations" in serialized["episodes"][0]
        assert "rewards_extrinsic" in serialized["episodes"][0]
        assert "rewards_intrinsic" in serialized["episodes"][0]
        assert "rewards_shaping" in serialized["episodes"][0]

    def test_serialization_without_components(self):
        """Serialization works for episodes without components."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Add episode without components
        episode = make_episode(4, reward_value=1.0)
        buffer.store_episode(episode)

        serialized = buffer.serialize()

        assert serialized["format_version"] == 5
        assert len(serialized["episodes"]) == 1
        # Components should not be present
        assert serialized["episodes"][0]["rewards_extrinsic"] is None
        assert serialized["episodes"][0]["rewards_intrinsic"] is None
        assert serialized["episodes"][0]["rewards_shaping"] is None

    def test_empty_buffer_serialization_version_5(self):
        """Empty buffer serialization should have format_version 5."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        serialized = buffer.serialize()

        assert serialized["format_version"] == 5
        assert serialized["num_transitions"] == 0
        assert len(serialized["episodes"]) == 0

    def test_non_current_format_rejection(self):
        """Unsupported4/8 and incomplete supported6/7 remain distinct refusals."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        previous_format = {
            "format_version": 4,
            "num_transitions": 0,
            "episodes": [],
            "capacity": 100,
        }

        with pytest.raises(ValueError, match="supported format_version values are 5, 6 and 7"):
            buffer.load_from_serialized(previous_format)

        with pytest.raises(ValueError, match="replay_kind"):
            buffer.load_from_serialized({"format_version": 6})

        with pytest.raises(ValueError, match="replay_kind"):
            buffer.load_from_serialized({"format_version": 7})

        with pytest.raises(ValueError, match="supported format_version values are 5, 6 and 7"):
            buffer.load_from_serialized({"format_version": 8})

    def test_round_trip_with_components(self):
        """Serialize and restore preserves component data."""
        buffer = qualified_buffer(100)

        # Add episode with components
        episode = make_episode(5, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((5,), 0.5)
        episode["rewards_intrinsic"] = torch.full((5,), 0.3)
        episode["rewards_shaping"] = torch.full((5,), 0.2)
        buffer.store_episode(episode)

        serialized = buffer.serialize()

        # Restore to new buffer
        restored = qualified_buffer(100)
        restored.load_from_serialized(serialized)

        assert serialized["format_version"] == 6
        assert_exact_state(serialized, restored.serialize())
        assert len(restored) == 1
        restored_episode = restored.episodes[0]
        assert torch.allclose(restored_episode["rewards_extrinsic"], torch.full((5,), 0.5))
        assert torch.allclose(restored_episode["rewards_intrinsic"], torch.full((5,), 0.3))
        assert torch.allclose(restored_episode["rewards_shaping"], torch.full((5,), 0.2))

    def test_component_validation_wrong_shape(self):
        """Component with wrong shape raises ValueError."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        episode = make_episode(5, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((5, 2), 0.5)  # Wrong shape: 2D instead of 1D

        with pytest.raises(ValueError, match="rewards_extrinsic must be 1D"):  # type: ignore[name-defined]
            buffer.store_episode(episode)

    def test_component_validation_wrong_length(self):
        """Component with wrong length raises ValueError."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        episode = make_episode(5, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((3,), 0.5)  # Wrong length: 3 instead of 5

        with pytest.raises(ValueError, match="Episode tensor length mismatch"):  # type: ignore[name-defined]
            buffer.store_episode(episode)


class TestCompactSequentialReplayCheckpointABI:
    def test_l1_episode_observations_use_compact_width_and_float32(self):
        buffer = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        episode = make_episode(3)
        episode["observations"] = torch.zeros((3, 115), dtype=torch.float32)
        episode["next_observations"] = torch.ones((3, 115), dtype=torch.float32)

        buffer.store_episode(episode)

        assert buffer.episodes[0]["observations"].shape == (3, 115)
        assert buffer.episodes[0]["next_observations"].shape == (3, 115)
        assert buffer.episodes[0]["observations"].dtype is torch.float32
        assert buffer.episodes[0]["next_observations"].dtype is torch.float32

    def test_serialized_legacy_transport_has_exact_version_kind_and_keys(self):
        state = SequentialReplayBuffer(capacity=10, device=torch.device("cpu")).serialize()

        assert state["format_version"] == 5
        assert state["replay_kind"] == "sequential"
        assert set(state) == {"replay_kind", "format_version", "capacity", "num_transitions", "episodes"}

    def test_serialized_current_state_has_exact_version_kind_and_keys(self):
        state = qualified_buffer(10).serialize()
        assert state["format_version"] == 6
        assert state["replay_kind"] == "sequential"
        assert set(state) == {
            "replay_kind",
            "format_version",
            "capacity",
            "num_transitions",
            "episodes",
            "action_dim",
            "legality_mode",
            "replay_options",
            "next_episode_id",
            "next_transition_id",
            "historical_archives",
        }
        assert state["action_dim"] == 8 and state["legality_mode"] == "unconstrained"
        assert state["num_transitions"] == state["next_episode_id"] == state["next_transition_id"] == 0

    def test_legacy_post_terminal_archive_and_inspection_roundtrip(self):
        source = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        episode = make_episode(3)
        episode["dones"] = torch.tensor([False, True, False])
        episode["rewards_extrinsic"] = torch.tensor([0.25, 0.5, 0.75])
        source.store_episode(episode)
        sample = source.sample_sequences(batch_size=1, seq_len=3)
        assert torch.equal(sample["mask"], torch.tensor([[True, True, False]]))
        assert torch.equal(sample["next_observations"][0], episode["next_observations"])
        legacy = source.serialize()
        before = copy.deepcopy(legacy)
        source.validate_serialized(legacy, expected_obs_dim=2)
        assert_exact_state(before, legacy)
        assert_exact_state(before, source.serialize())
        with pytest.raises(HistoricalLegalityUnavailable, match="missing historical successor masks"):
            source.load_for_mode(legacy, requested_mode="recorded_full_resume")
        assert_exact_state(before, source.serialize())

        inspected = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        inspected.load_from_serialized(legacy)
        assert inspected.num_transitions == inspected.retained_transitions == len(inspected) == 0
        archive = inspected.historical_archives[0]
        assert archive.archived_row_count == 3
        assert_exact_state(before, archive.original_state)
        rows = archive.query_rows(offset=0, limit=3)
        for name, value in episode.items():
            assert_exact_state(value, rows[name])
        assert rows["rewards_extrinsic_present"].all()
        assert not rows["rewards_intrinsic_present"].any()
        with pytest.raises(ValueError, match="buffer is empty"):
            inspected.sample_sequences(batch_size=1, seq_len=1)

        # New legacy transport remains distinct from the imported archive after resave.
        new_episode = make_episode(3, reward_value=7.0)
        inspected.store_episode(new_episode)
        envelope = inspected.serialize()
        assert set(envelope) == {"inspection_kind", "inspection_version", "legacy_transport", "historical_archives"}
        assert envelope["inspection_kind"] == "sequential_replay_inspection"
        assert type(envelope["inspection_version"]) is int and envelope["inspection_version"] == 1
        assert envelope["legacy_transport"]["format_version"] == 5
        restored = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        restored.load_from_serialized(envelope)
        assert_exact_state(envelope, restored.serialize())
        assert restored.retained_transitions == 0 and restored.legacy_transport_transitions == 3
        assert restored.historical_archives[0].source_digest == archive.source_digest
        assert_exact_state(before, restored.historical_archives[0].original_state)
        assert torch.equal(restored.sample_sequences(1, 3)["rewards"][0], new_episode["rewards"])
        assert_exact_state(before, legacy)

    @pytest.mark.parametrize("invalid_version", (5.0, 6.0, 7.0, True))
    def test_format_version_requires_an_exact_integer(self, invalid_version: object):
        buffer = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        state = buffer.serialize()
        state["format_version"] = invalid_version

        with pytest.raises(ValueError, match="supported format_version values are 5, 6 and 7"):
            buffer.load_from_serialized(state)

    def test_structural_validation_does_not_materialize_episode_tensors(self, monkeypatch):
        buffer = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        buffer.store_episode(make_episode(3))
        state = buffer.serialize()
        prepare_calls = 0
        original_prepare = buffer._prepare_serialized

        def counted_prepare(*args, **kwargs):
            nonlocal prepare_calls
            prepare_calls += 1
            return original_prepare(*args, **kwargs)

        monkeypatch.setattr(buffer, "_prepare_serialized", counted_prepare)
        buffer.validate_serialized(state, expected_obs_dim=2)

        assert prepare_calls == 0

    def test_loader_refuses_non_mapping_payload(self):
        replay = SequentialReplayBuffer(capacity=4, device=torch.device("cpu"))

        with pytest.raises(ValueError, match="payload must be a mapping"):
            replay.load_from_serialized(None)

    def test_unsupported_version4_refuses_without_mutation(self):
        buffer = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        buffer.store_episode(make_episode(3))
        before = buffer.serialize()
        previous = dict(before)
        previous["format_version"] = 4

        previous_input = copy.deepcopy(previous)
        with pytest.raises(ValueError, match=r"format_version 4.*supported format_version values are 5, 6 and 7"):
            buffer.load_from_serialized(previous)

        assert_exact_state(previous_input, previous)
        after = buffer.serialize()
        assert before.keys() == after.keys()
        assert before["num_transitions"] == after["num_transitions"]
        assert len(before["episodes"]) == len(after["episodes"])
        for field in before["episodes"][0]:
            expected = before["episodes"][0][field]
            actual = after["episodes"][0][field]
            if expected is None:
                assert actual is None
            else:
                assert torch.equal(expected, actual)

    @pytest.mark.parametrize(
        ("mutation", "message"),
        (
            pytest.param(lambda state: state.__setitem__("replay_kind", "standard"), "replay_kind", id="wrong-kind"),
            pytest.param(lambda state: state.__setitem__("unknown", 1), "key set", id="unknown-key"),
            pytest.param(lambda state: state.pop("episodes"), "key set", id="missing-key"),
            pytest.param(lambda state: state.__setitem__("capacity", 11), "capacity", id="capacity"),
            pytest.param(lambda state: state.__setitem__("format_version", 7), "key set", id="mixed-prioritized7"),
        ),
    )
    @pytest.mark.parametrize("qualified", [False, True], ids=["legacy5", "current6"])
    def test_current_state_refuses_wrong_kind_keys_or_capacity(self, mutation, message, qualified):
        target = qualified_buffer(10) if qualified else SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        target.store_episode(make_episode(3))
        before = target.serialize()
        state = copy.deepcopy(before)
        mutation(state)
        input_before = copy.deepcopy(state)

        with pytest.raises(ValueError, match=message):
            target.load_from_serialized(state)
        assert_exact_state(input_before, state)
        assert_exact_state(before, target.serialize())

    @pytest.mark.parametrize(
        ("field", "replacement", "message"),
        (
            pytest.param("observations", lambda tensor: tensor.to(torch.float64), "observations.*dtype", id="observation-dtype"),
            pytest.param("actions", lambda tensor: tensor.to(torch.int32), "actions.*dtype", id="action-dtype"),
            pytest.param("dones", lambda tensor: tensor.to(torch.float32), "dones.*dtype", id="done-dtype"),
            pytest.param("next_observations", lambda tensor: tensor[:, :-1], "next_observations.*shape", id="next-shape"),
        ),
    )
    @pytest.mark.parametrize("qualified", [False, True], ids=["legacy5", "current6"])
    def test_current_state_refuses_invalid_episode_tensor_contract(self, field, replacement, message, qualified):
        source = qualified_buffer(10) if qualified else SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        source.store_episode(make_episode(3))
        before = source.serialize()
        state = source.serialize()
        state["episodes"][0][field] = replacement(state["episodes"][0][field])
        input_before = copy.deepcopy(state)

        with pytest.raises(ValueError, match=message):
            source.load_from_serialized(state)
        assert_exact_state(input_before, state)
        assert_exact_state(before, source.serialize())


class TestSequentialReplayBufferStatsAPI:
    """Test stats() method for sequential buffer."""

    def test_stats_empty_buffer(self):
        """stats() should work on empty buffer."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        stats = buffer.stats()

        assert stats["size"] == 0  # num_transitions
        assert stats["capacity"] == 100
        assert stats["occupancy_ratio"] == 0.0
        assert stats["memory_bytes"] == 0
        assert stats["device"] == "cpu"
        assert stats["num_episodes"] == 0
        assert stats["num_transitions"] == 0

    def test_stats_with_episodes(self):
        """stats() should report episode and transition counts."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        buffer.store_episode(make_episode(5))  # CRIT-07: Use single rewards field
        buffer.store_episode(make_episode(7))
        buffer.store_episode(make_episode(3))

        stats = buffer.stats()

        assert stats["size"] == 15  # total transitions
        assert stats["capacity"] == 100
        assert stats["occupancy_ratio"] == 0.15
        assert stats["num_episodes"] == 3
        assert stats["num_transitions"] == 15
        assert stats["memory_bytes"] > 0

    def test_stats_memory_calculation(self):
        """stats() should calculate memory across all episodes."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Empty buffer
        assert buffer.stats()["memory_bytes"] == 0

        # Add one episode (length 5, obs_dim=2)
        buffer.store_episode(make_episode(5))  # CRIT-07: Use single rewards field

        stats = buffer.stats()

        # CRIT-07: Each episode has: observations [5,2], actions [5], rewards [5], dones [5]
        # (single rewards field instead of split extrinsic/intrinsic)
        # WS-1(c): plus next_observations [5,2]
        expected_bytes = (
            5 * 2 * 4  # observations (float32)
            + 5 * 8  # actions (int64)
            + 5 * 4  # rewards (float32) - CRIT-07: Single field
            + 5 * 1  # dones (bool)
            + 5 * 2 * 4  # next_observations (float32) - WS-1(c)
        )

        assert stats["memory_bytes"] == expected_bytes

    def test_stats_after_clear(self):
        """stats() should show empty buffer after clear()."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        buffer.store_episode(make_episode(10))  # CRIT-07: Use single rewards field
        buffer.clear()

        stats = buffer.stats()

        assert stats["size"] == 0
        assert stats["num_episodes"] == 0
        assert stats["num_transitions"] == 0
        assert stats["occupancy_ratio"] == 0.0
        assert stats["memory_bytes"] == 0
