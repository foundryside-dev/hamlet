"""Test configurable observation encoding for Grid2D substrate."""

import pytest
import torch

from townlet.substrate.grid2d import Grid2DSubstrate


@pytest.fixture
def device():
    return torch.device("cpu")


@pytest.fixture
def grid2d_relative(device):
    """Grid2D with relative encoding (normalized coordinates)."""
    return Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        observation_encoding="relative",
    )


@pytest.fixture
def grid2d_scaled(device):
    """Grid2D with scaled encoding (normalized + ranges)."""
    return Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        observation_encoding="scaled",
    )


@pytest.fixture
def grid2d_absolute(device):
    """Grid2D with absolute encoding (raw coordinates)."""
    return Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        observation_encoding="absolute",
    )




















def test_grid2d_default_encoding_is_relative():
    """Grid2D should default to relative encoding for backward compatibility."""
    substrate = Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        # observation_encoding NOT provided
    )
    assert substrate.observation_encoding == "relative"


# =============================================================================
# POSITION AND MOVEMENT TESTS
# =============================================================================


def test_substrate_initialize_positions_correctness():
    """Grid2D.initialize_positions() should return valid grid positions."""
    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")

    positions = substrate.initialize_positions(num_agents=10, device=torch.device("cpu"))

    # Correct shape and type
    assert positions.shape == (10, 2)
    assert positions.dtype == torch.long

    # Within bounds
    assert (positions >= 0).all()
    assert (positions < 8).all()


def test_substrate_movement_matches_legacy():
    """Substrate movement should produce identical results to legacy torch.clamp."""
    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan")
    positions = torch.tensor([[3, 3]], dtype=torch.long)

    # Move up (delta [0, -1])
    deltas = torch.tensor([[0, -1]], dtype=torch.long)
    new_positions = substrate.apply_movement(positions, deltas)

    # Should move to [3, 2]
    assert (new_positions == torch.tensor([[3, 2]], dtype=torch.long)).all()

    # Test boundary clamping at edge
    edge_positions = torch.tensor([[0, 0]], dtype=torch.long)
    up_left_delta = torch.tensor([[-1, -1]], dtype=torch.long)
    clamped = substrate.apply_movement(edge_positions, up_left_delta)

    # Should clamp to [0, 0] (not go negative)
    assert (clamped == torch.tensor([[0, 0]], dtype=torch.long)).all()


# =============================================================================
# TOPOLOGY ATTRIBUTE TESTS
# =============================================================================


def test_grid2d_stores_topology_when_provided():
    """Grid2D should store topology attribute when explicitly provided."""
    substrate = Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        observation_encoding="relative",
        topology="square",
    )
    assert substrate.topology == "square"


def test_grid2d_topology_defaults_to_square():
    """Grid2D topology should default to 'square' if not provided."""
    substrate = Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        enable_diagonals=True,
        observation_encoding="relative",
    )
    assert substrate.topology == "square"


def test_grid2d_topology_attribute_exists():
    """Grid2D should have topology attribute (not inherited from base)."""
    substrate = Grid2DSubstrate(
        width=8,
        height=8,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
    )
    assert hasattr(substrate, "topology")
