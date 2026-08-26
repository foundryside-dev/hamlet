"""Test GridND scaling behavior for 7D, 10D substrates."""

import pytest
import torch

from townlet.substrate.gridnd import GridNDSubstrate


def test_gridnd_7d_initialization():
    """Test 7D grid substrate."""
    substrate = GridNDSubstrate(
        dimension_sizes=[3] * 7,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
    )

    assert substrate.position_dim == 7
    assert substrate.action_space_size == 16  # 2*7 + 2

    # Test position initialization
    positions = substrate.initialize_positions(100, torch.device("cpu"))
    assert positions.shape == (100, 7)
    assert (positions >= 0).all()
    assert (positions < 3).all()


def test_gridnd_10d_initialization_with_warning():
    """Test 10D grid substrate (warning threshold)."""
    with pytest.warns(UserWarning, match="10 dimensions"):
        substrate = GridNDSubstrate(
            dimension_sizes=[2] * 10,  # Small sizes to keep fast
            boundary="clamp",
            distance_metric="manhattan",
            observation_encoding="relative",
        )

    assert substrate.position_dim == 10
    assert substrate.action_space_size == 22  # 2*10 + 2

    # Test position initialization
    positions = substrate.initialize_positions(100, torch.device("cpu"))
    assert positions.shape == (100, 10)


def test_gridnd_7d_movement_all_boundaries():
    """Test 7D movement with all boundary modes."""
    for boundary_mode in ["clamp", "wrap", "bounce", "sticky"]:
        substrate = GridNDSubstrate(
            dimension_sizes=[5] * 7,
            boundary=boundary_mode,
            distance_metric="manhattan",
            observation_encoding="relative",
        )

        # Agent at center
        positions = torch.full((1, 7), 2, dtype=torch.long)

        # Move in all directions
        deltas = torch.ones((1, 7), dtype=torch.float32)

        new_positions = substrate.apply_movement(positions, deltas)

        # Verify movement applied
        assert new_positions.shape == (1, 7)
        assert (new_positions >= 0).all()
        assert (new_positions < 5).all()






def test_gridnd_7d_distance_metrics():
    """Test all distance metrics in 7D."""
    for metric in ["manhattan", "euclidean", "chebyshev"]:
        substrate = GridNDSubstrate(
            dimension_sizes=[10] * 7,
            boundary="clamp",
            distance_metric=metric,
            observation_encoding="relative",
        )

        pos1 = torch.zeros((1, 7), dtype=torch.long)
        pos2 = torch.ones((1, 7), dtype=torch.long)

        distance = substrate.compute_distance(pos1, pos2)

        # Verify distance is positive
        assert distance[0] > 0

        if metric == "manhattan":
            assert distance[0] == 7  # sum of 1's
        elif metric == "euclidean":
            assert torch.allclose(distance, torch.tensor([torch.sqrt(torch.tensor(7.0))]))
        elif metric == "chebyshev":
            assert distance[0] == 1  # max of 1's
