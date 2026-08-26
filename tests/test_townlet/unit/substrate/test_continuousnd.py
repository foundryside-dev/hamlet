"""Test ContinuousND substrate for N-dimensional continuous spaces (N≥4)."""

import pytest
import torch

from townlet.substrate.continuousnd import ContinuousNDSubstrate


def test_continuousnd_requires_minimum_4_dimensions():
    """ContinuousND should reject dimensions < 4."""
    with pytest.raises(ValueError, match="ContinuousND requires at least 4 dimensions"):
        ContinuousNDSubstrate(
            bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],  # Only 3D
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )


def test_continuousnd_validates_positive_bounds():
    """ContinuousND should reject invalid bounds (min >= max)."""
    with pytest.raises(ValueError, match="min.*must be < max"):
        ContinuousNDSubstrate(
            bounds=[(0.0, 10.0), (0.0, 10.0), (5.0, 5.0), (0.0, 10.0)],  # Equal bounds
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )


def test_continuousnd_asymmetric_bounds():
    """ContinuousND should support different bounds per dimension."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 100.0), (-50.0, 50.0), (10.0, 20.0), (-10.0, 30.0)],  # Different ranges
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    assert substrate.position_dim == 4
    assert substrate.bounds == [(0.0, 100.0), (-50.0, 50.0), (10.0, 20.0), (-10.0, 30.0)]


def test_continuousnd_warns_at_10_dimensions():
    """ContinuousND should emit warning at N≥10."""
    with pytest.warns(UserWarning, match="10 dimensions"):
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0)] * 10,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )

    assert substrate.action_space_size == 22  # 2*10 + 2


def test_continuousnd_exceeds_100_dimensions():
    """ContinuousND should reject dimension count > 100."""
    with pytest.raises(ValueError, match="dimension count.*exceeds limit"):
        ContinuousNDSubstrate(
            bounds=[(0.0, 10.0)] * 101,  # Too many dimensions
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )


def test_continuousnd_movement_with_clamp_boundary():
    """Test movement with clamp boundary (hard walls)."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 5.0), (0.0, 5.0), (0.0, 5.0), (0.0, 5.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    # Agent at corner [0.0, 0.0, 0.0, 0.0]
    positions = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)

    # Try to move negative (should be clamped)
    deltas = torch.tensor([[-1.0, -1.0, -1.0, -1.0]], dtype=torch.float32)
    new_positions = substrate.apply_movement(positions, deltas)

    # Should stay at [0.0, 0.0, 0.0, 0.0]
    assert torch.allclose(new_positions, torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32))


def test_continuousnd_movement_with_wrap_boundary():
    """Test movement with wrap boundary (toroidal)."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 5.0), (0.0, 5.0), (0.0, 5.0), (0.0, 5.0)],
        boundary="wrap",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    # Agent at [0.0, 0.0, 0.0, 0.0]
    positions = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)

    # Move negative (should wrap to [4.5, 4.5, 4.5, 4.5])
    deltas = torch.tensor([[-1.0, -1.0, -1.0, -1.0]], dtype=torch.float32)
    new_positions = substrate.apply_movement(positions, deltas)

    expected = torch.tensor([[4.5, 4.5, 4.5, 4.5]], dtype=torch.float32)
    assert torch.allclose(new_positions, expected)


def test_continuousnd_distance_manhattan():
    """Test Manhattan distance in 4D continuous space."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="manhattan",
        observation_encoding="relative",
    )

    pos1 = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    pos2 = torch.tensor([[3.0, 4.0, 5.0, 6.0]], dtype=torch.float32)

    distance = substrate.compute_distance(pos1, pos2)

    # Manhattan: |3-0| + |4-0| + |5-0| + |6-0| = 18.0
    assert torch.allclose(distance, torch.tensor([18.0]))


def test_continuousnd_distance_euclidean():
    """Test Euclidean distance in 4D continuous space."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    pos1 = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    pos2 = torch.tensor([[3.0, 4.0, 0.0, 0.0]], dtype=torch.float32)

    distance = substrate.compute_distance(pos1, pos2)

    # Euclidean: sqrt(3^2 + 4^2 + 0^2 + 0^2) = sqrt(25) = 5.0
    assert torch.allclose(distance, torch.tensor([5.0]))


def test_continuousnd_distance_chebyshev():
    """Test Chebyshev distance in 4D continuous space."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="chebyshev",
        observation_encoding="relative",
    )

    pos1 = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
    pos2 = torch.tensor([[3.0, 4.0, 5.0, 6.0]], dtype=torch.float32)

    distance = substrate.compute_distance(pos1, pos2)

    # Chebyshev: max(|3-0|, |4-0|, |5-0|, |6-0|) = 6.0
    assert torch.allclose(distance, torch.tensor([6.0]))








def test_continuousnd_is_on_position_within_radius():
    """Test proximity-based position matching (within interaction_radius)."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    agent_positions = torch.tensor(
        [
            [5.0, 5.0, 5.0, 5.0],  # Exactly on target
            [5.0, 5.0, 5.0, 5.8],  # Within radius (0.8 units away)
            [5.0, 5.0, 5.0, 6.2],  # Outside radius (1.2 units away)
        ],
        dtype=torch.float32,
    )

    target_position = torch.tensor([5.0, 5.0, 5.0, 5.0], dtype=torch.float32)

    on_position = substrate.is_on_position(agent_positions, target_position)

    assert on_position[0]  # Exact match
    assert on_position[1]  # Within radius
    assert not on_position[2]  # Outside radius


def test_continuousnd_initialize_positions():
    """Test random position initialization in bounds."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (-5.0, 5.0), (100.0, 200.0), (-50.0, 50.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    positions = substrate.initialize_positions(num_agents=10, device=torch.device("cpu"))

    assert positions.shape == (10, 4)
    assert positions.dtype == torch.float32

    # Check all positions are within bounds
    for i in range(10):
        assert 0.0 <= positions[i, 0] <= 10.0
        assert -5.0 <= positions[i, 1] <= 5.0
        assert 100.0 <= positions[i, 2] <= 200.0
        assert -50.0 <= positions[i, 3] <= 50.0


def test_continuousnd_get_valid_neighbors_raises():
    """ContinuousND should raise NotImplementedError for get_valid_neighbors."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    position = torch.tensor([5.0, 5.0, 5.0, 5.0], dtype=torch.float32)

    with pytest.raises(NotImplementedError, match="continuous positions"):
        substrate.get_valid_neighbors(position)


def test_continuousnd_get_all_positions_raises():
    """ContinuousND should raise NotImplementedError for get_all_positions."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    with pytest.raises(NotImplementedError, match="infinite positions"):
        substrate.get_all_positions()




def test_continuousnd_supports_enumerable_positions():
    """ContinuousND should return False for supports_enumerable_positions."""
    substrate = ContinuousNDSubstrate(
        bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    assert not substrate.supports_enumerable_positions()
