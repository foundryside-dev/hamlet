"""Test configurable observation encoding for Continuous substrates.

This tests the retrofit of Continuous1D/2D/3D substrates to support
three observation encoding modes:
- relative: Normalized [0, 1] positions
- scaled: Normalized + range metadata
- absolute: Raw unnormalized positions
"""

import pytest
import torch

from townlet.substrate.continuous import (
    Continuous1DSubstrate,
    Continuous2DSubstrate,
    Continuous3DSubstrate,
)


@pytest.fixture
def device():
    """Test device (CPU for unit tests)."""
    return torch.device("cpu")


# ==================== Continuous1D Tests ====================


@pytest.fixture
def continuous_1d_relative():
    """1D continuous substrate with relative encoding."""
    return Continuous1DSubstrate(
        min_x=0.0,
        max_x=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_1d_scaled():
    """1D continuous substrate with scaled encoding."""
    return Continuous1DSubstrate(
        min_x=0.0,
        max_x=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="scaled",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_1d_absolute():
    """1D continuous substrate with absolute encoding."""
    return Continuous1DSubstrate(
        min_x=0.0,
        max_x=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="absolute",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


# ==================== Continuous2D Tests ====================


@pytest.fixture
def continuous_2d_relative():
    """2D continuous substrate with relative encoding."""
    return Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_2d_scaled():
    """2D continuous substrate with scaled encoding."""
    return Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="scaled",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_2d_absolute():
    """2D continuous substrate with absolute encoding."""
    return Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="absolute",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


# ==================== Continuous3D Tests ====================


@pytest.fixture
def continuous_3d_relative():
    """3D continuous substrate with relative encoding."""
    return Continuous3DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        min_z=0.0,
        max_z=30.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_3d_scaled():
    """3D continuous substrate with scaled encoding."""
    return Continuous3DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        min_z=0.0,
        max_z=30.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="scaled",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


@pytest.fixture
def continuous_3d_absolute():
    """3D continuous substrate with absolute encoding."""
    return Continuous3DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=20.0,
        min_z=0.0,
        max_z=30.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="euclidean",
        observation_encoding="absolute",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )


# ==================== Edge Case Tests ====================


# ==================== Chebyshev Distance Tests ====================


def test_continuous_1d_chebyshev_distance():
    """Test Continuous1D chebyshev distance metric."""
    substrate = Continuous1DSubstrate(
        min_x=0.0,
        max_x=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="chebyshev",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )

    # Test distance calculation
    pos1 = torch.tensor([[2.0], [5.0]])
    pos2 = torch.tensor([[6.0], [8.0]])

    dist = substrate.compute_distance(pos1, pos2)

    # Chebyshev in 1D is same as euclidean/manhattan (only one dimension)
    expected = torch.tensor([4.0, 3.0])
    assert torch.allclose(dist, expected)


def test_continuous_2d_chebyshev_distance():
    """Test Continuous2D chebyshev distance metric."""
    substrate = Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="chebyshev",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )

    # Test distance calculation
    pos1 = torch.tensor([[0.0, 0.0], [2.0, 3.0]])
    pos2 = torch.tensor([[4.0, 3.0], [5.0, 8.0]])

    dist = substrate.compute_distance(pos1, pos2)

    # Chebyshev distance = max(|x1-x2|, |y1-y2|)
    # pos1[0] to pos2[0]: max(|0-4|, |0-3|) = max(4, 3) = 4
    # pos1[1] to pos2[1]: max(|2-5|, |3-8|) = max(3, 5) = 5
    expected = torch.tensor([4.0, 5.0])
    assert torch.allclose(dist, expected)


def test_continuous_3d_chebyshev_distance():
    """Test Continuous3D chebyshev distance metric."""
    substrate = Continuous3DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        min_z=0.0,
        max_z=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=1.0,
        distance_metric="chebyshev",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )

    # Test distance calculation
    pos1 = torch.tensor([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]])
    pos2 = torch.tensor([[4.0, 3.0, 2.0], [5.0, 8.0, 4.0]])

    dist = substrate.compute_distance(pos1, pos2)

    # Chebyshev distance = max(|x1-x2|, |y1-y2|, |z1-z2|)
    # pos1[0] to pos2[0]: max(|0-4|, |0-3|, |0-2|) = max(4, 3, 2) = 4
    # pos1[1] to pos2[1]: max(|1-5|, |2-8|, |3-4|) = max(4, 6, 1) = 6
    expected = torch.tensor([4.0, 6.0])
    assert torch.allclose(dist, expected)


def test_continuous_chebyshev_interaction_radius():
    """Test that chebyshev distance affects interaction detection."""
    substrate = Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=3.0,  # Chebyshev radius
        distance_metric="chebyshev",
        observation_encoding="relative",
        action_discretization={"num_directions": 8, "num_magnitudes": 3},
    )

    # Agent positions
    agent_positions = torch.tensor(
        [
            [0.0, 0.0],  # Distance to target: max(2, 2) = 2 (within radius)
            [0.0, 5.0],  # Distance to target: max(2, 3) = 3 (at radius boundary)
            [5.0, 0.0],  # Distance to target: max(3, 2) = 3 (at radius boundary)
            [5.0, 5.0],  # Distance to target: max(3, 3) = 3 (at radius boundary)
            [6.0, 6.0],  # Distance to target: max(4, 4) = 4 (outside radius)
        ]
    )

    # Target position
    target_position = torch.tensor([2.0, 2.0])

    # Check interaction
    can_interact = substrate.is_on_position(agent_positions, target_position)

    expected = torch.tensor([True, True, True, True, False])
    assert torch.equal(can_interact, expected)
