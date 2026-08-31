"""Integration test for RewardTensor component wiring.

Verifies the complete data flow:
1. DACEngine returns components
2. Components flow through env info dict
3. Components stored in replay buffer
4. Checkpoint format_version is 3
5. Legacy format rejection
"""

from __future__ import annotations

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.training.replay_buffer import ReplayBuffer
from townlet.training.state import RewardTensor

# Use the same test level as test_dac_integration.py
LEVEL_NAME = "L0_test"


class TestRewardComponentFlow:
    """Verify components flow from DAC to buffer."""

    def test_dac_returns_components(self, compile_universe, test_config_pack_path, cpu_device):
        """DACEngine.calculate_rewards returns component dict via info."""
        universe = compile_universe(test_config_pack_path)
        env = VectorizedHamletEnv.from_universe(
            universe,
            level_name=LEVEL_NAME,
            num_agents=2,
            device=cpu_device,
        )

        env.reset()
        actions = torch.zeros(2, dtype=torch.long, device=cpu_device)
        obs, rewards, dones, info = env.step(actions)

        # Verify components in info dict
        assert "reward_components" in info, "info dict should contain reward_components"
        components = info["reward_components"]
        assert "extrinsic" in components, "Components should include extrinsic"
        assert "intrinsic" in components, "Components should include intrinsic"
        assert "shaping" in components, "Components should include shaping"

        # Verify all components are tensors with correct shape
        assert components["extrinsic"].shape == (2,), "Extrinsic should match num_agents"
        assert components["intrinsic"].shape == (2,), "Intrinsic should match num_agents"
        assert components["shaping"].shape == (2,), "Shaping should match num_agents"

    def test_components_in_info_dict(self, compile_universe, test_config_pack_path, cpu_device):
        """step() returns components and intrinsic_weight in info dict."""
        universe = compile_universe(test_config_pack_path)
        env = VectorizedHamletEnv.from_universe(
            universe,
            level_name=LEVEL_NAME,
            num_agents=2,
            device=cpu_device,
        )

        env.reset()
        obs, rewards, dones, info = env.step(torch.zeros(2, dtype=torch.long, device=cpu_device))

        assert "reward_components" in info, "info should have reward_components"
        assert "intrinsic_weight" in info, "info should have intrinsic_weight"

        # Verify intrinsic_weight is a tensor
        assert isinstance(info["intrinsic_weight"], torch.Tensor), "intrinsic_weight should be tensor"
        assert info["intrinsic_weight"].shape == (2,), "intrinsic_weight should match num_agents"

    def test_replay_buffer_stores_components(self, cpu_device):
        """Replay buffer stores component tensors when RewardTensor has components."""
        buffer = ReplayBuffer(capacity=100, device=cpu_device)

        # Create RewardTensor with components
        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0], device=cpu_device),
            extrinsic=torch.tensor([0.5], device=cpu_device),
            intrinsic=torch.tensor([0.3], device=cpu_device),
            shaping=torch.tensor([0.2], device=cpu_device),
        )

        buffer.push(
            observations=torch.randn(1, 29, device=cpu_device),
            actions=torch.zeros(1, dtype=torch.long, device=cpu_device),
            rewards=reward_tensor,
            next_observations=torch.randn(1, 29, device=cpu_device),
            dones=torch.zeros(1, dtype=torch.bool, device=cpu_device),
        )

        # Verify component tensors were initialized and stored
        assert buffer.rewards_extrinsic is not None, "Buffer should have rewards_extrinsic"
        assert buffer.rewards_intrinsic is not None, "Buffer should have rewards_intrinsic"
        assert buffer.rewards_shaping is not None, "Buffer should have rewards_shaping"

        # Verify values
        assert buffer.rewards_extrinsic[0].item() == pytest.approx(0.5), "Extrinsic value mismatch"
        assert buffer.rewards_intrinsic[0].item() == pytest.approx(0.3), "Intrinsic value mismatch"
        assert buffer.rewards_shaping[0].item() == pytest.approx(0.2), "Shaping value mismatch"
        assert buffer.rewards[0].item() == pytest.approx(1.0), "Total reward mismatch"

    def test_checkpoint_format_version_3(self, cpu_device):
        """Serialized buffer has format_version 3 with component fields."""
        buffer = ReplayBuffer(capacity=100, device=cpu_device)

        reward_tensor = RewardTensor.from_dac(
            total=torch.tensor([1.0], device=cpu_device),
            extrinsic=torch.tensor([0.5], device=cpu_device),
            intrinsic=torch.tensor([0.3], device=cpu_device),
            shaping=torch.tensor([0.2], device=cpu_device),
        )

        buffer.push(
            observations=torch.randn(1, 29, device=cpu_device),
            actions=torch.zeros(1, dtype=torch.long, device=cpu_device),
            rewards=reward_tensor,
            next_observations=torch.randn(1, 29, device=cpu_device),
            dones=torch.zeros(1, dtype=torch.bool, device=cpu_device),
        )

        serialized = buffer.serialize()

        # Verify format_version
        assert "format_version" in serialized, "Serialized buffer should have format_version"
        assert serialized["format_version"] == 3, "format_version should be 3"

        # Verify component fields exist
        assert "rewards_extrinsic" in serialized, "Serialized buffer should have rewards_extrinsic"
        assert "rewards_intrinsic" in serialized, "Serialized buffer should have rewards_intrinsic"
        assert "rewards_shaping" in serialized, "Serialized buffer should have rewards_shaping"

        # Verify component values are preserved
        assert serialized["rewards_extrinsic"] is not None
        assert serialized["rewards_intrinsic"] is not None
        assert serialized["rewards_shaping"] is not None

    def test_load_rejects_old_format(self, cpu_device):
        """Loading format_version < 3 raises ValueError."""
        buffer = ReplayBuffer(capacity=100, device=cpu_device)

        # Create old format checkpoint (version 2)
        old_format = {
            "format_version": 2,
            "size": 0,
            "position": 0,
            "capacity": 100,
            "observations": None,
            "actions": None,
            "rewards": None,
            "next_observations": None,
            "dones": None,
        }

        # Should raise ValueError for old format
        with pytest.raises(ValueError, match="exact current format_version is 3"):
            buffer.load_from_serialized(old_format)

    def test_buffer_handles_missing_components(self, cpu_device):
        """Buffer handles RewardTensor without components gracefully."""
        buffer = ReplayBuffer(capacity=100, device=cpu_device)

        # Create RewardTensor without components
        reward_tensor = RewardTensor.from_dac(total=torch.tensor([1.0], device=cpu_device))

        buffer.push(
            observations=torch.randn(1, 29, device=cpu_device),
            actions=torch.zeros(1, dtype=torch.long, device=cpu_device),
            rewards=reward_tensor,
            next_observations=torch.randn(1, 29, device=cpu_device),
            dones=torch.zeros(1, dtype=torch.bool, device=cpu_device),
        )

        # Buffer should initialize component tensors even if first push has no components
        assert buffer.rewards_extrinsic is not None, "Buffer should initialize extrinsic tensor"
        assert buffer.rewards_intrinsic is not None, "Buffer should initialize intrinsic tensor"
        assert buffer.rewards_shaping is not None, "Buffer should initialize shaping tensor"

        # Components should be zero when not provided
        assert buffer.rewards_extrinsic[0].item() == 0.0, "Missing extrinsic should be zero"
        assert buffer.rewards_intrinsic[0].item() == 0.0, "Missing intrinsic should be zero"
        assert buffer.rewards_shaping[0].item() == 0.0, "Missing shaping should be zero"

    def test_intrinsic_raw_in_components(self, compile_universe, test_config_pack_path, cpu_device):
        """DACEngine returns intrinsic_raw in components for TensorBoard logging."""
        universe = compile_universe(test_config_pack_path)
        env = VectorizedHamletEnv.from_universe(
            universe,
            level_name=LEVEL_NAME,
            num_agents=2,
            device=cpu_device,
        )

        # Set up RND exploration to generate non-zero intrinsic rewards
        from townlet.exploration.rnd import RNDExploration

        obs = env.reset()
        exploration = RNDExploration(
            obs_dim=obs.shape[1],
            embed_dim=64,
            learning_rate=1e-4,
            training_batch_size=32,
            epsilon_start=1.0,
            epsilon_min=0.01,
            epsilon_decay=0.995,
            device=cpu_device,
        )
        env.set_exploration_module(exploration)

        actions = torch.zeros(2, dtype=torch.long, device=cpu_device)
        obs, rewards, dones, info = env.step(actions)

        # Verify intrinsic_raw is present
        components = info["reward_components"]
        assert "intrinsic_raw" in components, "Components should include intrinsic_raw"
        assert components["intrinsic_raw"].shape == (2,), "intrinsic_raw should match num_agents"

    def test_end_to_end_component_flow(self, compile_universe, test_config_pack_path, cpu_device):
        """Verify complete flow from environment through buffer to serialization."""
        universe = compile_universe(test_config_pack_path)
        env = VectorizedHamletEnv.from_universe(
            universe,
            level_name=LEVEL_NAME,
            num_agents=2,
            device=cpu_device,
        )

        buffer = ReplayBuffer(capacity=100, device=cpu_device)

        # Step environment
        obs = env.reset()
        actions = torch.zeros(2, dtype=torch.long, device=cpu_device)
        next_obs, rewards, dones, info = env.step(actions)

        # Extract components from info
        components = info.get("reward_components", {})

        # Create RewardTensor with components
        reward_tensor = RewardTensor.from_dac(
            total=rewards,
            extrinsic=components.get("extrinsic"),
            intrinsic=components.get("intrinsic"),
            shaping=components.get("shaping"),
        )

        # Store in buffer
        buffer.push(
            observations=obs,
            actions=actions,
            rewards=reward_tensor,
            next_observations=next_obs,
            dones=dones,
        )

        # Verify buffer storage
        assert buffer.size == 2, "Buffer should have 2 transitions"
        assert buffer.rewards_extrinsic is not None
        assert buffer.rewards_intrinsic is not None
        assert buffer.rewards_shaping is not None

        # Serialize and verify format
        serialized = buffer.serialize()
        assert serialized["format_version"] == 3
        assert "rewards_extrinsic" in serialized
        assert "rewards_intrinsic" in serialized
        assert "rewards_shaping" in serialized

        # Load into new buffer
        new_buffer = ReplayBuffer(capacity=100, device=cpu_device)
        new_buffer.load_from_serialized(serialized)

        # Verify components were preserved
        assert new_buffer.size == 2
        assert torch.allclose(new_buffer.rewards_extrinsic[:2], buffer.rewards_extrinsic[:2])
        assert torch.allclose(new_buffer.rewards_intrinsic[:2], buffer.rewards_intrinsic[:2])
        assert torch.allclose(new_buffer.rewards_shaping[:2], buffer.rewards_shaping[:2])
