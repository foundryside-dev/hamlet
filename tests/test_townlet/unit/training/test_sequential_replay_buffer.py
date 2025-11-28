"""Unit tests for SequentialReplayBuffer edge cases.

CRIT-07: Updated to use single 'rewards' field (DAC-composed totals).
"""

from __future__ import annotations

import pytest
import torch

from townlet.training.sequential_replay_buffer import SequentialReplayBuffer


def make_episode(length: int, *, reward_value: float = 1.0) -> dict[str, torch.Tensor]:
    """Create test episode with single rewards field (CRIT-07).

    Args:
        length: Number of timesteps in episode
        reward_value: Value for all rewards (default 1.0)

    Returns:
        Episode dict with observations, actions, rewards (DAC-composed), dones
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
        """CRIT-07: Test serialization with single rewards field."""
        buffer = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        buffer.store_episode(make_episode(4))

        state = buffer.serialize()

        restored = SequentialReplayBuffer(capacity=10, device=torch.device("cpu"))
        restored.load_from_serialized(state)

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
        """Episode without reward components should work (backward compatibility)."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Create episode without components
        episode = make_episode(5, reward_value=1.0)

        buffer.store_episode(episode)

        assert len(buffer) == 1
        stored_episode = buffer.episodes[0]
        assert "rewards_extrinsic" not in stored_episode
        assert "rewards_intrinsic" not in stored_episode
        assert "rewards_shaping" not in stored_episode

    def test_serialization_format_version_3(self):
        """Serialized buffer has format_version 3."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Add episode with components
        episode = make_episode(4, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((4,), 0.6)
        episode["rewards_intrinsic"] = torch.full((4,), 0.2)
        episode["rewards_shaping"] = torch.full((4,), 0.2)
        buffer.store_episode(episode)

        serialized = buffer.serialize()

        assert serialized["format_version"] == 3
        assert len(serialized["episodes"]) == 1
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

        assert serialized["format_version"] == 3
        assert len(serialized["episodes"]) == 1
        # Components should not be present
        assert "rewards_extrinsic" not in serialized["episodes"][0]
        assert "rewards_intrinsic" not in serialized["episodes"][0]
        assert "rewards_shaping" not in serialized["episodes"][0]

    def test_empty_buffer_serialization_version_3(self):
        """Empty buffer serialization should have format_version 3."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        serialized = buffer.serialize()

        assert serialized["format_version"] == 3
        assert serialized["num_transitions"] == 0
        assert len(serialized["episodes"]) == 0

    def test_legacy_format_rejection(self):
        """Loading format_version < 3 raises ValueError."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Format version 2
        old_format_v2 = {
            "format_version": 2,
            "num_transitions": 0,
            "episodes": [],
            "capacity": 100,
        }

        with pytest.raises(ValueError, match="format_version < 3"):  # type: ignore[name-defined]
            buffer.load_from_serialized(old_format_v2)

        # Format version 1
        old_format_v1 = {
            "format_version": 1,
            "num_transitions": 0,
            "episodes": [],
            "capacity": 100,
        }

        with pytest.raises(ValueError, match="format_version < 3"):  # type: ignore[name-defined]
            buffer.load_from_serialized(old_format_v1)

    def test_round_trip_with_components(self):
        """Serialize and restore preserves component data."""
        buffer = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))

        # Add episode with components
        episode = make_episode(5, reward_value=1.0)
        episode["rewards_extrinsic"] = torch.full((5,), 0.5)
        episode["rewards_intrinsic"] = torch.full((5,), 0.3)
        episode["rewards_shaping"] = torch.full((5,), 0.2)
        buffer.store_episode(episode)

        serialized = buffer.serialize()

        # Restore to new buffer
        restored = SequentialReplayBuffer(capacity=100, device=torch.device("cpu"))
        restored.load_from_serialized(serialized)

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
        expected_bytes = (
            5 * 2 * 4  # observations (float32)
            + 5 * 8  # actions (int64)
            + 5 * 4  # rewards (float32) - CRIT-07: Single field
            + 5 * 1  # dones (bool)
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
