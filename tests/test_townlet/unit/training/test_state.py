"""Tests for training state DTOs."""

import torch

from townlet.training.state import BatchedAgentState


class TestBatchedAgentState:
    """Test BatchedAgentState hot-path state container."""

    def test_batched_agent_state_creation(self):
        """BatchedAgentState should accept all required tensors."""
        batch_size = 4
        obs_dim = 10
        device = torch.device("cpu")

        # HIGH-09: curriculum_difficulties field removed
        state = BatchedAgentState(
            observations=torch.randn(batch_size, obs_dim),
            actions=torch.randint(0, 6, (batch_size,)),
            rewards=torch.randn(batch_size),
            dones=torch.rand(batch_size) > 0.5,
            epsilons=torch.ones(batch_size) * 0.1,
            intrinsic_rewards=torch.randn(batch_size),
            survival_times=torch.randint(0, 100, (batch_size,)),
            device=device,
        )

        assert state.batch_size == batch_size
        assert state.observations.shape == (batch_size, obs_dim)
        assert state.device == device

    def test_batched_agent_state_info_dict(self):
        """BatchedAgentState should store info dict."""
        batch_size = 4
        device = torch.device("cpu")

        info = {"custom_key": "custom_value", "nested": {"data": 123}}

        # HIGH-09: curriculum_difficulties field removed
        state = BatchedAgentState(
            observations=torch.randn(batch_size, 10),
            actions=torch.randint(0, 6, (batch_size,)),
            rewards=torch.randn(batch_size),
            dones=torch.rand(batch_size) > 0.5,
            epsilons=torch.ones(batch_size) * 0.1,
            intrinsic_rewards=torch.randn(batch_size),
            survival_times=torch.randint(0, 100, (batch_size,)),
            device=device,
            info=info,
        )

        assert state.info == info
        assert state.info["custom_key"] == "custom_value"
        assert state.info["nested"]["data"] == 123

    def test_batched_agent_state_default_info_is_empty_dict(self):
        """BatchedAgentState should default info to empty dict."""
        batch_size = 4
        device = torch.device("cpu")

        # HIGH-09: curriculum_difficulties field removed
        state = BatchedAgentState(
            observations=torch.randn(batch_size, 10),
            actions=torch.randint(0, 6, (batch_size,)),
            rewards=torch.randn(batch_size),
            dones=torch.rand(batch_size) > 0.5,
            epsilons=torch.ones(batch_size) * 0.1,
            intrinsic_rewards=torch.randn(batch_size),
            survival_times=torch.randint(0, 100, (batch_size,)),
            device=device,
        )

        assert state.info == {}

    def test_batched_agent_state_to_preserves_info(self):
        """CRIT-05: BatchedAgentState.to() should preserve info dict."""
        batch_size = 4
        cpu = torch.device("cpu")

        info = {"custom_key": "custom_value", "data": [1, 2, 3]}

        # HIGH-09: curriculum_difficulties field removed
        state = BatchedAgentState(
            observations=torch.randn(batch_size, 10),
            actions=torch.randint(0, 6, (batch_size,)),
            rewards=torch.randn(batch_size),
            dones=torch.rand(batch_size) > 0.5,
            epsilons=torch.ones(batch_size) * 0.1,
            intrinsic_rewards=torch.randn(batch_size),
            survival_times=torch.randint(0, 100, (batch_size,)),
            device=cpu,
            info=info,
        )

        # Move to same device (cpu to cpu)
        new_state = state.to(cpu)

        # Info should be preserved
        assert new_state.info == info
        assert new_state.info["custom_key"] == "custom_value"
        assert new_state.info["data"] == [1, 2, 3]

    def test_batched_agent_state_to_moves_tensors(self):
        """BatchedAgentState.to() should move all tensors to new device."""
        batch_size = 4
        cpu = torch.device("cpu")

        # HIGH-09: curriculum_difficulties field removed
        state = BatchedAgentState(
            observations=torch.randn(batch_size, 10),
            actions=torch.randint(0, 6, (batch_size,)),
            rewards=torch.randn(batch_size),
            dones=torch.rand(batch_size) > 0.5,
            epsilons=torch.ones(batch_size) * 0.1,
            intrinsic_rewards=torch.randn(batch_size),
            survival_times=torch.randint(0, 100, (batch_size,)),
            device=cpu,
        )

        new_state = state.to(cpu)

        assert new_state.device == cpu
        assert new_state.observations.device == cpu
        assert new_state.actions.device == cpu
        assert new_state.rewards.device == cpu
        assert new_state.dones.device == cpu
        assert new_state.epsilons.device == cpu
        assert new_state.intrinsic_rewards.device == cpu
        assert new_state.survival_times.device == cpu

    # LOW-09: test_detach_cpu_summary deleted - method was dead code
