"""Test ContinuousND scaling to higher dimensions (7D, 10D)."""

import pytest
import torch

from townlet.substrate.continuousnd import ContinuousNDSubstrate


def test_continuousnd_7d_movement():
    """Test movement in 7D space."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0)] * 7,
        boundary="clamp",
        movement_delta=1.0,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    # Agent at origin
    positions = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)

    # Move positive in all dimensions
    deltas = torch.tensor([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], dtype=torch.float32)
    new_positions = substrate.apply_movement(positions, deltas)

    expected = torch.tensor([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], dtype=torch.float32)
    assert torch.allclose(new_positions, expected)


def test_continuousnd_7d_distance_euclidean():
    """Test Euclidean distance in 7D."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0)] * 7,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    pos1 = torch.tensor([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    pos2 = torch.tensor([[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]], dtype=torch.float32)

    distance = substrate.compute_distance(pos1, pos2)

    # Euclidean: sqrt(7 * 1^2) = sqrt(7) ≈ 2.646
    expected = torch.sqrt(torch.tensor(7.0))
    assert torch.allclose(distance, expected)


def test_continuousnd_10d_initialization_with_warning():
    """Test 10D continuous space emits warning."""
    with pytest.warns(UserWarning, match="10 dimensions"):
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0)] * 10,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )

    assert substrate.position_dim == 10
    assert substrate.action_space_size == 22  # 2*10 + 2


def test_continuousnd_10d_movement():
    """Test movement in 10D space."""
    with pytest.warns(UserWarning):
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0)] * 10,
            boundary="wrap",
            movement_delta=1.0,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )

    # Agent at boundary
    positions = torch.tensor([[10.0] * 10], dtype=torch.float32)

    # Move positive (should wrap to 0)
    deltas = torch.tensor([[1.0] * 10], dtype=torch.float32)
    new_positions = substrate.apply_movement(positions, deltas)

    # Should wrap to [1.0, 1.0, ...]
    expected = torch.tensor([[1.0] * 10], dtype=torch.float32)
    assert torch.allclose(new_positions, expected, atol=1e-5)


def test_continuousnd_10d_distance_manhattan():
    """Test Manhattan distance in 10D."""
    with pytest.warns(UserWarning):
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0)] * 10,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="manhattan",
            observation_encoding="relative",
        )

    pos1 = torch.tensor([[0.0] * 10], dtype=torch.float32)
    pos2 = torch.tensor([[1.0] * 10], dtype=torch.float32)

    distance = substrate.compute_distance(pos1, pos2)

    # Manhattan: sum of absolute differences = 10 * 1.0 = 10.0
    assert torch.allclose(distance, torch.tensor([10.0]))


def test_continuousnd_batch_movement_7d():
    """Test batched movement for multiple agents in 7D."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0)] * 7,
        boundary="clamp",
        movement_delta=1.0,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    # 5 agents
    positions = torch.tensor(
        [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
            [9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0],
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
            [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
        ],
        dtype=torch.float32,
    )

    # Different deltas for each agent
    deltas = torch.tensor(
        [
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Should clamp to max
            [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
            [-1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0],
        ],
        dtype=torch.float32,
    )

    new_positions = substrate.apply_movement(positions, deltas)

    assert new_positions.shape == (5, 7)
    assert torch.allclose(new_positions[0], torch.tensor([1.0] * 7))  # Moved forward
    assert torch.allclose(new_positions[1], torch.tensor([5.0] * 7))  # Didn't move
    assert torch.allclose(new_positions[2], torch.tensor([10.0] * 7))  # Clamped to max
    assert torch.allclose(new_positions[3], torch.tensor([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]))  # Moved back
    assert torch.allclose(new_positions[4], torch.tensor([9.0] * 7))  # Moved back from boundary


def test_continuousnd_exceeds_max_dimensions():
    """Test that >100D raises error."""
    with pytest.raises(ValueError, match="dimension count.*exceeds limit"):
        ContinuousNDSubstrate(
            bounds=[(0.0, 1.0)] * 101,
            boundary="clamp",
            movement_delta=0.01,
            interaction_radius=0.1,
            distance_metric="euclidean",
            observation_encoding="relative",
        )
