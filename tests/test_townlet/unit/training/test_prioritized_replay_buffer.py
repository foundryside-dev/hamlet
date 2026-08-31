"""Tests for prioritized experience replay buffer.

CRIT-07: Updated to use RewardTensor DTO.
"""

import numpy as np
import pytest
import torch

from townlet.training.prioritized_replay_buffer import PrioritizedReplayBuffer
from townlet.training.state import RewardTensor


def _make_reward_tensor(rewards: torch.Tensor) -> RewardTensor:
    """Helper to create RewardTensor from reward values."""
    return RewardTensor.from_dac(total=rewards)


def test_prioritized_replay_buffer_push():
    """PrioritizedReplayBuffer accepts transitions."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Push batch of 1 transition
    obs = torch.randn(1, 10)  # [batch=1, obs_dim=10]
    action = torch.tensor([2])  # [batch=1]
    rewards = _make_reward_tensor(torch.tensor([1.0]))  # [batch=1]
    next_obs = torch.randn(1, 10)  # [batch=1, obs_dim=10]
    done = torch.tensor([False])  # [batch=1]

    buffer.push(obs, action, rewards, next_obs, done)

    assert buffer.size() == 1


def test_prioritized_replay_buffer_sample():
    """PrioritizedReplayBuffer samples with priorities."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Add 50 transitions (batch of 50)
    obs = torch.randn(50, 10)  # [batch=50, obs_dim=10]
    actions = torch.tensor([i % 5 for i in range(50)])  # [batch=50]
    rewards = _make_reward_tensor(torch.tensor([float(i) for i in range(50)]))  # [batch=50]
    next_obs = torch.randn(50, 10)  # [batch=50, obs_dim=10]
    dones = torch.tensor([i == 49 for i in range(50)])  # [batch=50]
    buffer.push(obs, actions, rewards, next_obs, dones)

    # Sample batch
    batch = buffer.sample(batch_size=16)

    assert batch["observations"].shape == (16, 10)
    assert batch["actions"].shape == (16,)
    assert batch["rewards"].shape == (16,)
    assert batch["next_observations"].shape == (16, 10)
    assert batch["dones"].shape == (16,)
    assert "weights" in batch  # Importance sampling weights
    assert "indices" in batch  # For priority updates


def test_prioritized_replay_buffer_update_priorities():
    """PrioritizedReplayBuffer updates priorities from TD errors."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Add transitions (batch of 20)
    obs = torch.randn(20, 10)  # [batch=20, obs_dim=10]
    actions = torch.zeros(20, dtype=torch.long)  # [batch=20]
    rewards = _make_reward_tensor(torch.zeros(20))  # [batch=20]
    next_obs = torch.randn(20, 10)  # [batch=20, obs_dim=10]
    dones = torch.zeros(20, dtype=torch.bool)  # [batch=20]
    buffer.push(obs, actions, rewards, next_obs, dones)

    # Sample batch
    batch = buffer.sample(batch_size=10)

    # Update priorities with TD errors
    td_errors = torch.randn(10).abs()  # Absolute TD errors
    buffer.update_priorities(batch["indices"], td_errors)

    # Priorities should be updated (no exception raised)
    assert buffer.size() == 20


def test_prioritized_replay_buffer_beta_annealing():
    """PrioritizedReplayBuffer anneals beta toward 1.0."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=True,
        device=torch.device("cpu"),
    )

    initial_beta = buffer.beta
    assert initial_beta == 0.4

    # Anneal beta (would be called during training)
    buffer.anneal_beta(total_steps=10000, current_step=5000)

    # Beta should increase toward 1.0
    assert buffer.beta > initial_beta
    assert buffer.beta <= 1.0


def test_prioritized_replay_buffer_anneal_beta_zero_total_steps():
    """CRIT-03: anneal_beta should not crash when total_steps=0."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.5,
        beta_annealing=True,
        device=torch.device("cpu"),
    )

    initial_beta = buffer.beta

    # Should not raise ZeroDivisionError
    buffer.anneal_beta(total_steps=0, current_step=0)

    # Beta should remain unchanged
    assert buffer.beta == initial_beta


def test_prioritized_replay_buffer_anneal_beta_respects_initial_value():
    """CRIT-04: anneal_beta should use user-provided initial beta, not hardcoded 0.4."""
    # Use non-default initial beta
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.6,  # Custom initial beta (not the default 0.4)
        beta_annealing=True,
        device=torch.device("cpu"),
    )

    assert buffer.beta_initial == 0.6

    # At step 0, beta should be initial value
    buffer.anneal_beta(total_steps=1000, current_step=0)
    assert buffer.beta == 0.6

    # At halfway, beta should be between initial and 1.0
    buffer.anneal_beta(total_steps=1000, current_step=500)
    expected_beta = 0.6 + (1.0 - 0.6) * 0.5  # 0.8
    assert abs(buffer.beta - expected_beta) < 0.001

    # At end, beta should be 1.0
    buffer.anneal_beta(total_steps=1000, current_step=1000)
    assert buffer.beta == 1.0


def test_prioritized_replay_buffer_anneal_beta_disabled():
    """Beta annealing should not change beta when beta_annealing=False."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.5,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    initial_beta = buffer.beta

    buffer.anneal_beta(total_steps=1000, current_step=500)

    # Beta should remain unchanged when annealing is disabled
    assert buffer.beta == initial_beta


def test_prioritized_replay_buffer_len():
    """PrioritizedReplayBuffer implements __len__."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    assert len(buffer) == 0

    # Add transitions
    obs = torch.randn(10, 5)
    actions = torch.zeros(10, dtype=torch.long)
    rewards = _make_reward_tensor(torch.zeros(10))
    next_obs = torch.randn(10, 5)
    dones = torch.zeros(10, dtype=torch.bool)
    buffer.push(obs, actions, rewards, next_obs, dones)

    assert len(buffer) == 10


def test_prioritized_replay_buffer_serialize():
    """PrioritizedReplayBuffer can be serialized and restored."""
    buffer = PrioritizedReplayBuffer(
        capacity=50,
        alpha=0.7,
        beta=0.5,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Add transitions
    obs = torch.randn(10, 5)
    actions = torch.tensor([i % 3 for i in range(10)])
    rewards = _make_reward_tensor(torch.tensor([float(i) for i in range(10)]))
    next_obs = torch.randn(10, 5)
    dones = torch.zeros(10, dtype=torch.bool)
    buffer.push(obs, actions, rewards, next_obs, dones)

    # Serialize
    state = buffer.serialize()

    # Verify beta_initial is in serialized state
    assert "beta_initial" in state
    assert state["beta_initial"] == 0.5
    assert state["format_version"] == 4

    # Create new buffer and restore
    new_buffer = PrioritizedReplayBuffer(
        capacity=50,
        alpha=0.7,
        beta=0.5,
        beta_annealing=False,
        device=torch.device("cpu"),
    )
    new_buffer.load_from_serialized(state)

    # Verify state restored
    assert len(new_buffer) == 10
    assert new_buffer.alpha == 0.7
    assert new_buffer.beta == 0.5
    assert new_buffer.beta_initial == 0.5
    assert new_buffer.capacity == 50
    assert new_buffer.position == buffer.position
    assert new_buffer.max_priority == buffer.max_priority


def test_prioritized_replay_buffer_device_placement():
    """PrioritizedReplayBuffer stores tensors on target device (BUG-06 fix verification)."""
    device = torch.device("cpu")
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=device,
    )

    # Push transitions
    obs = torch.randn(10, 5)
    actions = torch.zeros(10, dtype=torch.long)
    rewards = _make_reward_tensor(torch.ones(10))
    next_obs = torch.randn(10, 5)
    dones = torch.zeros(10, dtype=torch.bool)
    buffer.push(obs, actions, rewards, next_obs, dones)

    # Verify storage tensors are on target device (not lists of CPU tensors)
    assert isinstance(buffer.observations, torch.Tensor), "observations should be tensor, not list"
    assert isinstance(buffer.actions, torch.Tensor), "actions should be tensor, not list"
    assert isinstance(buffer.rewards, torch.Tensor), "rewards should be tensor, not list"
    assert isinstance(buffer.next_observations, torch.Tensor), "next_observations should be tensor, not list"
    assert isinstance(buffer.dones, torch.Tensor), "dones should be tensor, not list"

    assert buffer.observations.device == device
    assert buffer.actions.device == device
    assert buffer.rewards.device == device
    assert buffer.next_observations.device == device
    assert buffer.dones.device == device

    # Verify storage is preallocated with full capacity (contiguous memory)
    assert buffer.observations.shape == (100, 5)
    assert buffer.actions.shape == (100,)
    assert buffer.rewards.shape == (100,)
    assert buffer.next_observations.shape == (100, 5)
    assert buffer.dones.shape == (100,)

    # Verify sampling returns tensors on target device (no device churn)
    batch = buffer.sample(batch_size=5)
    assert batch["observations"].device == device
    assert batch["actions"].device == device
    assert batch["rewards"].device == device
    assert batch["next_observations"].device == device
    assert batch["dones"].device == device


def test_prioritized_replay_buffer_wraparound_indexing():
    """PrioritizedReplayBuffer handles buffer wraparound without IndexError (Issue 1 fix verification)."""
    # Small capacity to trigger wraparound quickly
    buffer = PrioritizedReplayBuffer(
        capacity=10,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Push exactly capacity transitions (fills buffer to position=10, size=10)
    obs = torch.randn(10, 5)
    actions = torch.zeros(10, dtype=torch.long)
    rewards = _make_reward_tensor(torch.ones(10))
    next_obs = torch.randn(10, 5)
    dones = torch.zeros(10, dtype=torch.bool)
    buffer.push(obs, actions, rewards, next_obs, dones)

    assert buffer.size() == 10
    assert buffer.position == 0  # Wrapped to 0

    # Push one more batch (triggers wraparound - was IndexError before fix)
    obs2 = torch.randn(5, 5)
    actions2 = torch.zeros(5, dtype=torch.long)
    rewards2 = _make_reward_tensor(torch.ones(5))
    next_obs2 = torch.randn(5, 5)
    dones2 = torch.zeros(5, dtype=torch.bool)

    # This should NOT raise IndexError (was bug when position >= capacity)
    buffer.push(obs2, actions2, rewards2, next_obs2, dones2)

    assert buffer.size() == 10  # Still at capacity
    assert buffer.position == 5  # Wrapped: (0 + 5) % 10


def test_prioritized_replay_buffer_sample_size_guard():
    """PrioritizedReplayBuffer raises clear error when batch_size > buffer size (Issue 2 fix verification)."""
    buffer = PrioritizedReplayBuffer(
        capacity=100,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    # Add only 5 transitions
    obs = torch.randn(5, 10)
    actions = torch.zeros(5, dtype=torch.long)
    rewards = _make_reward_tensor(torch.ones(5))
    next_obs = torch.randn(5, 10)
    dones = torch.zeros(5, dtype=torch.bool)
    buffer.push(obs, actions, rewards, next_obs, dones)

    # Try to sample more than available (batch_size=10 > size=5)
    with pytest.raises(ValueError, match=r"Buffer size \(5\) < batch_size \(10\)"):
        buffer.sample(batch_size=10)

    # Should work when batch_size <= size
    batch = buffer.sample(batch_size=5)
    assert batch["observations"].shape == (5, 10)


def test_prioritized_replay_buffer_previous_format_rejected():
    """load_from_serialized rejects the immediately previous artifact."""
    buffer = PrioritizedReplayBuffer(
        capacity=50,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    previous_state = {
        "format_version": 3,
        "capacity": 50,
        "alpha": 0.6,
        "beta": 0.4,
        "beta_initial": 0.4,
        "beta_annealing": False,
        "observations": None,
        "actions": None,
        "rewards": None,
        "next_observations": None,
        "dones": None,
        "priorities": np.zeros(50, dtype=np.float32),
        "max_priority": 1.0,
        "position": 0,
        "size_current": 0,
    }

    with pytest.raises(ValueError, match="exact current format_version is 4"):
        buffer.load_from_serialized(previous_state)


def test_prioritized_replay_buffer_future_format_rejected():
    buffer = PrioritizedReplayBuffer(
        capacity=50,
        alpha=0.6,
        beta=0.4,
        beta_annealing=False,
        device=torch.device("cpu"),
    )

    with pytest.raises(ValueError, match="exact current format_version is 4"):
        buffer.load_from_serialized({"format_version": 5})


class TestCompactPrioritizedReplayCheckpointABI:
    def _buffer(self, *, capacity: int = 10) -> PrioritizedReplayBuffer:
        return PrioritizedReplayBuffer(
            capacity=capacity,
            alpha=0.6,
            beta=0.4,
            beta_annealing=True,
            device=torch.device("cpu"),
        )

    def test_l1_observation_pair_uses_exact_float32_shape_and_bytes(self):
        buffer = self._buffer(capacity=100_000)
        observations = torch.zeros((1, 115), dtype=torch.float32)
        buffer.push(
            observations,
            torch.zeros(1, dtype=torch.long),
            _make_reward_tensor(torch.zeros(1, dtype=torch.float32)),
            observations.clone(),
            torch.zeros(1, dtype=torch.bool),
        )

        assert buffer.observations is not None
        assert buffer.next_observations is not None
        assert buffer.observations.dtype is torch.float32
        assert buffer.next_observations.dtype is torch.float32
        assert buffer.observations.shape == (100_000, 115)
        assert buffer.next_observations.shape == (100_000, 115)
        pair = (buffer.observations, buffer.next_observations)
        assert sum(tensor.numel() * tensor.element_size() for tensor in pair) == 92_000_000
        assert sum(tensor.untyped_storage().nbytes() for tensor in pair) == 92_000_000

    def test_serialized_state_has_exact_current_version_kind_and_keys(self):
        state = self._buffer().serialize()

        assert state["format_version"] == 4
        assert state["replay_kind"] == "prioritized"
        assert set(state) == {
            "replay_kind",
            "format_version",
            "capacity",
            "alpha",
            "beta",
            "beta_initial",
            "beta_annealing",
            "observations",
            "actions",
            "rewards",
            "rewards_extrinsic",
            "rewards_intrinsic",
            "rewards_shaping",
            "next_observations",
            "dones",
            "priorities",
            "max_priority",
            "position",
            "size_current",
        }

    @pytest.mark.parametrize("invalid_version", (4.0, True))
    def test_format_version_requires_an_exact_integer(self, invalid_version: object):
        buffer = self._buffer(capacity=10)
        state = buffer.serialize()
        state["format_version"] = invalid_version

        with pytest.raises(ValueError, match="exact current format_version is 4"):
            buffer.load_from_serialized(state)

    def test_structural_validation_does_not_materialize_restore_storage(self, monkeypatch):
        buffer = self._buffer(capacity=10)
        observations = torch.zeros((1, 3), dtype=torch.float32)
        buffer.push(
            observations,
            torch.zeros(1, dtype=torch.long),
            _make_reward_tensor(torch.zeros(1, dtype=torch.float32)),
            observations.clone(),
            torch.zeros(1, dtype=torch.bool),
        )
        state = buffer.serialize()
        prepare_calls = 0
        original_prepare = buffer._prepare_serialized

        def counted_prepare(*args, **kwargs):
            nonlocal prepare_calls
            prepare_calls += 1
            return original_prepare(*args, **kwargs)

        monkeypatch.setattr(buffer, "_prepare_serialized", counted_prepare)
        buffer.validate_serialized(state, expected_obs_dim=3)

        assert prepare_calls == 0

    def test_loader_refuses_non_mapping_payload(self):
        replay = self._buffer(capacity=4)

        with pytest.raises(ValueError, match="payload must be a mapping"):
            replay.load_from_serialized(None)

    def test_immediately_previous_version_refuses_without_mutation(self):
        buffer = self._buffer()
        observations = torch.ones((1, 3), dtype=torch.float32)
        buffer.push(
            observations,
            torch.zeros(1, dtype=torch.long),
            _make_reward_tensor(torch.ones(1, dtype=torch.float32)),
            observations + 1,
            torch.zeros(1, dtype=torch.bool),
        )
        before = buffer.serialize()
        previous = dict(before)
        previous["format_version"] = 3

        with pytest.raises(ValueError, match=r"format_version 3.*format_version is 4"):
            buffer.load_from_serialized(previous)

        after = buffer.serialize()
        assert before.keys() == after.keys()
        for key in before:
            if isinstance(before[key], torch.Tensor):
                assert torch.equal(before[key], after[key])
            elif isinstance(before[key], np.ndarray):
                assert np.array_equal(before[key], after[key])
            else:
                assert before[key] == after[key]

    @pytest.mark.parametrize(
        ("mutation", "message"),
        (
            pytest.param(lambda state: state.__setitem__("replay_kind", "standard"), "replay_kind", id="wrong-kind"),
            pytest.param(lambda state: state.__setitem__("unknown", 1), "key set", id="unknown-key"),
            pytest.param(lambda state: state.pop("priorities"), "key set", id="missing-key"),
            pytest.param(lambda state: state.__setitem__("capacity", 11), "capacity", id="capacity"),
            pytest.param(lambda state: state.__setitem__("alpha", 0.7), "alpha", id="alpha"),
            pytest.param(lambda state: state.__setitem__("beta_initial", 0.3), "beta_initial", id="beta-initial"),
        ),
    )
    def test_current_state_refuses_wrong_kind_keys_or_configuration(self, mutation, message):
        state = self._buffer().serialize()
        mutation(state)

        with pytest.raises(ValueError, match=message):
            self._buffer().load_from_serialized(state)

    @pytest.mark.parametrize(
        ("field", "replacement", "message"),
        (
            pytest.param("observations", lambda tensor: tensor.to(torch.float64), "observations.*dtype", id="observation-dtype"),
            pytest.param("priorities", lambda array: array.astype(np.float64), "priorities.*dtype", id="priority-dtype"),
            pytest.param("priorities", lambda array: np.full_like(array, np.nan), "priorities.*finite", id="priority-finite"),
            pytest.param("max_priority", lambda value: float("inf"), "max_priority.*finite", id="max-priority-finite"),
        ),
    )
    def test_current_state_refuses_invalid_tensor_or_priority_contract(self, field, replacement, message):
        source = self._buffer()
        observations = torch.ones((2, 3), dtype=torch.float32)
        source.push(
            observations,
            torch.zeros(2, dtype=torch.long),
            _make_reward_tensor(torch.ones(2, dtype=torch.float32)),
            observations + 1,
            torch.zeros(2, dtype=torch.bool),
        )
        state = source.serialize()
        state[field] = replacement(state[field])

        with pytest.raises(ValueError, match=message):
            self._buffer().load_from_serialized(state)


class TestPrioritizedReplayBufferClearAPI:
    """Test clear() method for prioritized buffer."""

    def test_clear_resets_counters(self):
        """clear() should reset size and position to zero."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Add transitions
        obs = torch.randn(10, 5)
        actions = torch.zeros(10, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(10))
        next_obs = torch.randn(10, 5)
        dones = torch.zeros(10, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        assert buffer.size_current == 10
        assert buffer.position == 10

        buffer.clear()

        assert buffer.size_current == 0
        assert buffer.position == 0
        assert len(buffer) == 0

    def test_clear_deallocates_storage(self):
        """clear() should set storage tensors to None to free memory."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Initialize storage
        obs = torch.randn(5, 3)
        actions = torch.zeros(5, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(5))
        next_obs = torch.randn(5, 3)
        dones = torch.zeros(5, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        assert buffer.observations is not None
        assert buffer.actions is not None

        buffer.clear()

        assert buffer.observations is None
        assert buffer.actions is None
        assert buffer.rewards is None
        assert buffer.next_observations is None
        assert buffer.dones is None

    def test_clear_resets_priorities(self):
        """clear() should reset priorities array and max_priority."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Add transitions and update priorities
        obs = torch.randn(10, 5)
        actions = torch.zeros(10, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(10))
        next_obs = torch.randn(10, 5)
        dones = torch.zeros(10, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        # Sample and update priorities to change max_priority
        batch = buffer.sample(batch_size=5)
        buffer.update_priorities(batch["indices"], torch.tensor([10.0, 5.0, 8.0, 3.0, 12.0]))

        assert buffer.max_priority > 1.0  # Should have increased

        buffer.clear()

        # Priorities should be reset
        assert buffer.max_priority == 1.0
        # All priorities should be zero
        assert np.allclose(buffer.priorities, np.zeros(50))

    def test_clear_idempotence(self):
        """Calling clear() multiple times should be safe."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Clear empty buffer
        buffer.clear()
        assert len(buffer) == 0

        # Add data and clear
        obs = torch.randn(5, 3)
        actions = torch.zeros(5, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(5))
        next_obs = torch.randn(5, 3)
        dones = torch.zeros(5, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)
        buffer.clear()

        # Clear again
        buffer.clear()
        assert len(buffer) == 0
        assert buffer.observations is None

    def test_buffer_works_after_clear(self):
        """Buffer should work normally after clear()."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Fill buffer
        obs = torch.randn(20, 5)
        actions = torch.zeros(20, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(20))
        next_obs = torch.randn(20, 5)
        dones = torch.zeros(20, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        buffer.clear()

        # Should be able to push again
        obs = torch.randn(5, 3)
        actions = torch.zeros(5, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(5))
        next_obs = torch.randn(5, 3)
        dones = torch.zeros(5, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        assert len(buffer) == 5
        assert buffer.observations is not None
        assert buffer.observations.shape == (50, 3)  # New obs_dim


class TestPrioritizedReplayBufferStatsAPI:
    """Test stats() method for prioritized buffer."""

    def test_stats_empty_buffer(self):
        """stats() should work on empty buffer with unallocated storage."""
        buffer = PrioritizedReplayBuffer(
            capacity=100,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        stats = buffer.stats()

        assert stats["size"] == 0
        assert stats["capacity"] == 100
        assert stats["occupancy_ratio"] == 0.0
        assert stats["memory_bytes"] == 0  # No tensors allocated
        assert stats["device"] == "cpu"

    def test_stats_partially_filled(self):
        """stats() should report correct values for partially filled buffer."""
        buffer = PrioritizedReplayBuffer(
            capacity=100,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Add 10 transitions with obs_dim=5
        obs = torch.randn(10, 5)
        actions = torch.zeros(10, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(10))
        next_obs = torch.randn(10, 5)
        dones = torch.zeros(10, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        stats = buffer.stats()

        assert stats["size"] == 10
        assert stats["capacity"] == 100
        assert stats["occupancy_ratio"] == 0.1
        assert stats["memory_bytes"] > 0  # Should have allocated memory
        assert stats["device"] == "cpu"

    def test_stats_full_buffer(self):
        """stats() should show full occupancy when buffer is full."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Fill to capacity
        obs = torch.randn(10, 5)
        actions = torch.zeros(10, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(10))
        next_obs = torch.randn(10, 5)
        dones = torch.zeros(10, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        stats = buffer.stats()

        assert stats["size"] == 10
        assert stats["capacity"] == 10
        assert stats["occupancy_ratio"] == 1.0

    def test_stats_memory_calculation(self):
        """stats() should calculate approximate memory usage including priorities."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Empty buffer should report 0 bytes (tensors not allocated)
        assert buffer.stats()["memory_bytes"] == 0

        # Add data (obs_dim=5)
        obs = torch.randn(5, 5)
        actions = torch.zeros(5, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(5))
        next_obs = torch.randn(5, 5)
        dones = torch.zeros(5, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        stats = buffer.stats()

        # Calculate expected memory (tensors preallocated + NumPy priorities)
        # observations: 10*5 floats, actions: 10 longs, rewards: 10 floats (total),
        # rewards_extrinsic: 10 floats, rewards_intrinsic: 10 floats, rewards_shaping: 10 floats,
        # next_observations: 10*5 floats, dones: 10 bools, priorities: 10 float32
        expected_bytes = (
            10 * 5 * 4  # observations (float32)
            + 10 * 8  # actions (int64)
            + 10 * 4  # rewards (float32, total)
            + 10 * 4  # rewards_extrinsic (float32)
            + 10 * 4  # rewards_intrinsic (float32)
            + 10 * 4  # rewards_shaping (float32)
            + 10 * 5 * 4  # next_observations (float32)
            + 10 * 1  # dones (bool)
            + 10 * 4  # priorities (numpy float32)
        )

        assert stats["memory_bytes"] == expected_bytes

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_stats_cuda_device(self):
        """stats() should report correct device string for CUDA buffers."""
        buffer = PrioritizedReplayBuffer(
            capacity=10,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cuda"),
        )

        obs = torch.randn(5, 3)
        actions = torch.zeros(5, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(5))
        next_obs = torch.randn(5, 3)
        dones = torch.zeros(5, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        stats = buffer.stats()

        assert "cuda" in stats["device"]

    def test_stats_after_clear(self):
        """stats() should show empty buffer after clear()."""
        buffer = PrioritizedReplayBuffer(
            capacity=50,
            alpha=0.6,
            beta=0.4,
            beta_annealing=False,
            device=torch.device("cpu"),
        )

        # Fill buffer
        obs = torch.randn(20, 3)
        actions = torch.zeros(20, dtype=torch.long)
        rewards = _make_reward_tensor(torch.ones(20))
        next_obs = torch.randn(20, 3)
        dones = torch.zeros(20, dtype=torch.bool)
        buffer.push(obs, actions, rewards, next_obs, dones)

        buffer.clear()
        stats = buffer.stats()

        assert stats["size"] == 0
        assert stats["occupancy_ratio"] == 0.0
        assert stats["memory_bytes"] == 0
