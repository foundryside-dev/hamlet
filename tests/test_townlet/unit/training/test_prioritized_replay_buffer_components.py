"""Tests for PrioritizedReplayBuffer reward component storage (format_version 3).

Task 5 from docs/plans/2025-11-28-reward-tensor-wiring-implementation.md:
- Component storage and retrieval
- Serialization format_version 3
- Rejection of format_version < 3
"""

import numpy as np
import pytest
import torch

from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.state import RewardTensor

CPU = torch.device("cpu")


class TestRewardComponentStorage:
    """Test storing and retrieving reward components in PER."""

    @pytest.fixture
    def buffer(self):
        """Create small PER buffer for testing."""
        return PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

    def test_push_with_components_stores_all_fields(self, buffer):
        """PER buffer should store all reward components when provided."""
        obs = torch.randn(1, 5)
        actions = torch.tensor([2])
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0]),
            extrinsic=torch.tensor([0.5]),
            intrinsic=torch.tensor([0.3]),
            shaping=torch.tensor([0.2]),
        )
        next_obs = torch.randn(1, 5)
        dones = torch.tensor([False])

        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        assert buffer.rewards is not None
        assert buffer.rewards_extrinsic is not None
        assert buffer.rewards_intrinsic is not None
        assert buffer.rewards_shaping is not None

        # Check values
        assert buffer.rewards[0].item() == pytest.approx(1.0)
        assert buffer.rewards_extrinsic[0].item() == pytest.approx(0.5)
        assert buffer.rewards_intrinsic[0].item() == pytest.approx(0.3)
        assert buffer.rewards_shaping[0].item() == pytest.approx(0.2)

    def test_push_batch_with_components(self, buffer):
        """PER buffer should handle batch push with components."""
        batch_size = 4
        obs = torch.randn(batch_size, 5)
        actions = torch.randint(0, 6, (batch_size,))
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0, 2.0, 3.0, 4.0]),
            extrinsic=torch.tensor([0.5, 1.0, 1.5, 2.0]),
            intrinsic=torch.tensor([0.3, 0.6, 0.9, 1.2]),
            shaping=torch.tensor([0.2, 0.4, 0.6, 0.8]),
        )
        next_obs = torch.randn(batch_size, 5)
        dones = torch.rand(batch_size) > 0.5

        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        assert len(buffer) == 4
        # Verify components match input
        for i in range(batch_size):
            assert buffer.rewards_extrinsic[i].item() == pytest.approx((i + 1) * 0.5)
            assert buffer.rewards_intrinsic[i].item() == pytest.approx((i + 1) * 0.3)
            assert buffer.rewards_shaping[i].item() == pytest.approx((i + 1) * 0.2)

    def test_push_without_components_stores_zeros(self, buffer):
        """PER buffer should store zeros for missing components."""
        obs = torch.randn(1, 5)
        actions = torch.tensor([2])
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0]),
            # No components provided
        )
        next_obs = torch.randn(1, 5)
        dones = torch.tensor([False])

        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        # Tensors should be allocated but contain zeros (not updated)
        assert buffer.rewards_extrinsic is not None
        assert buffer.rewards_intrinsic is not None
        assert buffer.rewards_shaping is not None
        assert buffer.rewards_extrinsic[0].item() == 0.0
        assert buffer.rewards_intrinsic[0].item() == 0.0
        assert buffer.rewards_shaping[0].item() == 0.0

    def test_wraparound_preserves_components(self):
        """Component storage should work correctly with PER wraparound."""
        buffer = PrioritizedReplayBuffer(
            capacity=5,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Fill buffer and wrap around
        for i in range(8):
            obs = torch.tensor([[float(i)]])
            actions = torch.tensor([i % 4])
            reward_tensor = RewardTensor.from_dac(
                total=torch.tensor([float(i)]),
                extrinsic=torch.tensor([float(i) * 0.5]),
                intrinsic=torch.tensor([float(i) * 0.3]),
                shaping=torch.tensor([float(i) * 0.2]),
            )
            next_obs = torch.tensor([[float(i + 1)]])
            dones = torch.tensor([False])
            buffer.push(obs, actions, reward_tensor, next_obs, dones)

        # Buffer should contain last 5 transitions (3, 4, 5, 6, 7)
        # At position 3 after 8 pushes to capacity 5
        assert buffer.size_current == 5
        assert buffer.position == 3

        # Check that components wrapped correctly
        # Position 3 should have values from i=3
        assert buffer.rewards_extrinsic[3].item() == pytest.approx(3.0 * 0.5)
        assert buffer.rewards_intrinsic[3].item() == pytest.approx(3.0 * 0.3)
        assert buffer.rewards_shaping[3].item() == pytest.approx(3.0 * 0.2)


class TestSerializationFormatVersion3:
    """Test PER serialization with format_version 3."""

    def test_serialize_empty_buffer_has_version_3(self):
        """Empty PER buffer should serialize with format_version 3."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )
        state = buffer.serialize()

        assert state["format_version"] == 3
        assert state["size_current"] == 0
        assert state["rewards_extrinsic"] is None
        assert state["rewards_intrinsic"] is None
        assert state["rewards_shaping"] is None

    def test_serialize_with_components(self):
        """PER serialization should include all component tensors."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Add transitions with components
        for i in range(5):
            obs = torch.tensor([[float(i)]])
            actions = torch.tensor([i])
            reward_tensor = RewardTensor.from_dac(
                total=torch.tensor([float(i)]),
                extrinsic=torch.tensor([float(i) * 0.5]),
                intrinsic=torch.tensor([float(i) * 0.3]),
                shaping=torch.tensor([float(i) * 0.2]),
            )
            next_obs = torch.tensor([[float(i + 1)]])
            dones = torch.tensor([i == 4])
            buffer.push(obs, actions, reward_tensor, next_obs, dones)

        state = buffer.serialize()

        assert state["format_version"] == 3
        assert state["size_current"] == 5
        assert state["rewards_extrinsic"] is not None
        assert state["rewards_intrinsic"] is not None
        assert state["rewards_shaping"] is not None
        assert state["rewards_extrinsic"].shape == (5,)
        assert state["rewards_intrinsic"].shape == (5,)
        assert state["rewards_shaping"].shape == (5,)

        # Verify component values
        for i in range(5):
            assert state["rewards_extrinsic"][i].item() == pytest.approx(i * 0.5)
            assert state["rewards_intrinsic"][i].item() == pytest.approx(i * 0.3)
            assert state["rewards_shaping"][i].item() == pytest.approx(i * 0.2)

    def test_roundtrip_preserves_components(self):
        """PER serialize/deserialize should preserve component data."""
        buffer1 = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Add transitions
        for i in range(5):
            obs = torch.tensor([[float(i), float(i * 2)]])
            actions = torch.tensor([i % 4])
            reward_tensor = RewardTensor.from_dac(
                total=torch.tensor([float(i)]),
                extrinsic=torch.tensor([float(i) * 0.5]),
                intrinsic=torch.tensor([float(i) * 0.3]),
                shaping=torch.tensor([float(i) * 0.2]),
            )
            next_obs = torch.tensor([[float(i + 1), float((i + 1) * 2)]])
            dones = torch.tensor([i == 4])
            buffer1.push(obs, actions, reward_tensor, next_obs, dones)

        state = buffer1.serialize()

        # Create new buffer and restore
        buffer2 = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )
        buffer2.load_from_serialized(state)

        assert buffer2.size_current == 5
        # Verify components match
        for i in range(5):
            assert buffer2.rewards_extrinsic[i].item() == pytest.approx(i * 0.5)
            assert buffer2.rewards_intrinsic[i].item() == pytest.approx(i * 0.3)
            assert buffer2.rewards_shaping[i].item() == pytest.approx(i * 0.2)


class TestLegacyFormatRejection:
    """Test that format_version < 3 is rejected by PER."""

    def test_load_format_version_2_raises_error(self):
        """Loading format_version 2 should raise ValueError."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        old_format = {
            "format_version": 2,
            "capacity": 10,
            "alpha": 0.6,
            "beta": 0.4,
            "beta_initial": 0.4,
            "beta_annealing": False,
            "observations": torch.randn(5, 3),
            "actions": torch.randint(0, 4, (5,)),
            "rewards": torch.randn(5),
            "next_observations": torch.randn(5, 3),
            "dones": torch.rand(5) > 0.5,
            "priorities": np.zeros(10, dtype=np.float32),
            "max_priority": 1.0,
            "position": 5,
            "size_current": 5,
        }

        with pytest.raises(ValueError, match="exact current format_version is 3"):
            buffer.load_from_serialized(old_format)

    def test_load_format_version_1_raises_error(self):
        """Loading format_version 1 should raise ValueError."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        legacy_format = {
            "format_version": 1,
            "capacity": 10,
            "alpha": 0.6,
            "beta": 0.4,
            "beta_initial": 0.4,
            "beta_annealing": False,
            "observations": torch.randn(5, 3),
            "actions": torch.randint(0, 4, (5,)),
            "rewards_extrinsic": torch.randn(5),
            "rewards_intrinsic": torch.randn(5),
            "next_observations": torch.randn(5, 3),
            "dones": torch.rand(5) > 0.5,
            "priorities": np.zeros(10, dtype=np.float32),
            "max_priority": 1.0,
            "position": 5,
            "size_current": 5,
        }

        with pytest.raises(ValueError, match="exact current format_version is 3"):
            buffer.load_from_serialized(legacy_format)

    def test_load_missing_format_version_raises_error(self):
        """Loading state without format_version should raise ValueError."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        old_format = {
            # No format_version field (defaults to 1)
            "capacity": 10,
            "alpha": 0.6,
            "beta": 0.4,
            "beta_initial": 0.4,
            "beta_annealing": False,
            "observations": torch.randn(5, 3),
            "actions": torch.randint(0, 4, (5,)),
            "rewards": torch.randn(5),
            "next_observations": torch.randn(5, 3),
            "dones": torch.rand(5) > 0.5,
            "priorities": np.zeros(10, dtype=np.float32),
            "max_priority": 1.0,
            "position": 5,
            "size_current": 5,
        }

        with pytest.raises(ValueError, match="exact current format_version is 3"):
            buffer.load_from_serialized(old_format)


class TestClearAndStatsWithComponents:
    """Test clear() and stats() handle component tensors in PER."""

    def test_clear_deallocates_component_tensors(self):
        """clear() should set component tensors to None."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Add data with components
        obs = torch.randn(2, 5)
        actions = torch.tensor([0, 1])
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0, 2.0]),
            extrinsic=torch.tensor([0.5, 1.0]),
            intrinsic=torch.tensor([0.3, 0.6]),
            shaping=torch.tensor([0.2, 0.4]),
        )
        next_obs = torch.randn(2, 5)
        dones = torch.tensor([False, True])
        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        assert buffer.rewards_extrinsic is not None
        assert buffer.rewards_intrinsic is not None
        assert buffer.rewards_shaping is not None

        buffer.clear()

        assert buffer.rewards_extrinsic is None
        assert buffer.rewards_intrinsic is None
        assert buffer.rewards_shaping is None

    def test_stats_includes_component_memory(self):
        """stats() should include memory for component tensors."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Empty buffer should report 0 bytes
        assert buffer.stats()["memory_bytes"] == 0

        # Add data (obs_dim=5)
        obs = torch.randn(5, 5)
        actions = torch.randint(0, 6, (5,))
        reward_tensor = RewardTensor.from_dac(
            total=torch.randn(5),
            extrinsic=torch.randn(5),
            intrinsic=torch.randn(5),
            shaping=torch.randn(5),
        )
        next_obs = torch.randn(5, 5)
        dones = torch.rand(5) > 0.5
        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        stats = buffer.stats()

        # Calculate expected memory (all tensors preallocated to capacity)
        expected_bytes = (
            10 * 5 * 4  # observations (float32)
            + 10 * 8  # actions (int64)
            + 10 * 4  # rewards (float32)
            + 10 * 4  # rewards_extrinsic (float32)
            + 10 * 4  # rewards_intrinsic (float32)
            + 10 * 4  # rewards_shaping (float32)
            + 10 * 5 * 4  # next_observations (float32)
            + 10 * 1  # dones (bool)
            + 10 * 4  # priorities (numpy float32)
        )

        assert stats["memory_bytes"] == expected_bytes

    def test_stats_after_clear_shows_zero_memory(self):
        """stats() should show 0 memory after clear()."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=CPU,
        )

        # Fill buffer
        obs = torch.randn(5, 3)
        actions = torch.randint(0, 6, (5,))
        reward_tensor = RewardTensor.from_dac(
            total=torch.randn(5),
            extrinsic=torch.randn(5),
            intrinsic=torch.randn(5),
            shaping=torch.randn(5),
        )
        next_obs = torch.randn(5, 3)
        dones = torch.rand(5) > 0.5
        buffer.push(obs, actions, reward_tensor, next_obs, dones)

        buffer.clear()
        stats = buffer.stats()

        assert stats["size"] == 0
        assert stats["occupancy_ratio"] == 0.0
        assert stats["memory_bytes"] == 0
