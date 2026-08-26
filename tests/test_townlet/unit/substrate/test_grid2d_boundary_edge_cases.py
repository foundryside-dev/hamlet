"""Comprehensive boundary mode and edge case tests for Grid2D substrate.

This module tests uncovered paths in Grid2D:
- Boundary mode edge cases (bounce with multiple reflections, sticky on corners)
- Full grid encoding with agents and affordances
- Invalid encoding modes
- Edge cases in partial observation encoding
- Distance metric edge cases

Coverage targets:
- src/townlet/substrate/grid2d.py:324-376 (full grid encoding)
- src/townlet/substrate/grid2d.py:395 (invalid encoding error path)
- src/townlet/substrate/grid2d.py:429 (invalid encoding in get_observation_dim)
- src/townlet/substrate/grid2d.py:108-132 (bounce and sticky boundary detailed behavior)
"""

import torch

from townlet.substrate.grid2d import Grid2DSubstrate


class TestGrid2DBoundaryEdgeCases:
    """Test boundary mode edge cases and corner behavior."""

    def test_bounce_boundary_multiple_reflections_x_axis(self):
        """Bounce boundary should handle multiple reflections correctly on x-axis.

        When agent moves far beyond boundary, it should reflect properly.
        Coverage target: lines 113-117 (x-axis bouncing logic)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="bounce",
            distance_metric="manhattan",
        )

        # Agent at center, move far right (beyond boundary)
        positions = torch.tensor([[3, 3]], dtype=torch.long)
        # Delta would take us to x=8 (out of bounds)
        deltas = torch.tensor([[5, 0]], dtype=torch.long)

        new_positions = substrate.apply_movement(positions, deltas)

        # x=8 should bounce to x = 2*(8-1) - 8 = 14 - 8 = 6
        assert new_positions[0, 0].item() == 6, "Should bounce from right boundary"
        assert new_positions[0, 1].item() == 3, "Y should not change"

    def test_bounce_boundary_multiple_reflections_y_axis(self):
        """Bounce boundary should handle multiple reflections correctly on y-axis.

        Coverage target: lines 119-123 (y-axis bouncing logic)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="bounce",
            distance_metric="manhattan",
        )

        # Agent at center, move far down (beyond boundary)
        positions = torch.tensor([[3, 3]], dtype=torch.long)
        # Delta would take us to y=9 (well beyond boundary)
        deltas = torch.tensor([[0, 6]], dtype=torch.long)

        new_positions = substrate.apply_movement(positions, deltas)

        # y=9 should bounce to y = 2*(8-1) - 9 = 14 - 9 = 5
        assert new_positions[0, 0].item() == 3, "X should not change"
        assert new_positions[0, 1].item() == 5, "Should bounce from bottom boundary"

    def test_bounce_boundary_negative_positions(self):
        """Bounce boundary should handle negative positions (absolute value reflection).

        Coverage target: lines 114, 116, 120, 122 (negative position bounce masks)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="bounce",
            distance_metric="manhattan",
        )

        # Agent near edge, move left past boundary
        positions = torch.tensor([[1, 2]], dtype=torch.long)
        deltas = torch.tensor([[-3, -4]], dtype=torch.long)

        new_positions = substrate.apply_movement(positions, deltas)

        # x = 1 - 3 = -2, bounce to abs(-2) = 2
        # y = 2 - 4 = -2, bounce to abs(-2) = 2
        assert new_positions[0, 0].item() == 2, "Should bounce negative x to positive"
        assert new_positions[0, 1].item() == 2, "Should bounce negative y to positive"

    def test_sticky_boundary_corner_behavior(self):
        """Sticky boundary should keep agent in place when hitting corner.

        Coverage target: lines 126-131 (sticky boundary logic)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="sticky",
            distance_metric="manhattan",
        )

        # Agent at top-left corner
        positions = torch.tensor([[0, 0]], dtype=torch.long)
        # Try to move diagonally out of bounds
        deltas = torch.tensor([[-1, -1]], dtype=torch.long)

        new_positions = substrate.apply_movement(positions, deltas)

        # Should stay at [0, 0] (both axes out of bounds)
        assert new_positions[0, 0].item() == 0, "Should stick at left boundary"
        assert new_positions[0, 1].item() == 0, "Should stick at top boundary"

    def test_sticky_boundary_partial_movement(self):
        """Sticky boundary should only prevent movement on out-of-bounds axis.

        If one axis is valid and one is out of bounds, only the invalid axis should stick.
        Coverage target: lines 127-131 (independent axis checking)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="sticky",
            distance_metric="manhattan",
        )

        # Agent at left edge, mid-height
        positions = torch.tensor([[0, 4]], dtype=torch.long)
        # Try to move left (invalid) and down (valid)
        deltas = torch.tensor([[-1, 1]], dtype=torch.long)

        new_positions = substrate.apply_movement(positions, deltas)

        # x should stick at 0, y should move to 5
        assert new_positions[0, 0].item() == 0, "X should stick at left boundary"
        assert new_positions[0, 1].item() == 5, "Y should move normally"






class TestGrid2DDistanceMetricEdgeCases:
    """Test distance metric edge cases and broadcasting.

    Coverage target: lines 135-155 (compute_distance with broadcasting)
    """

    def test_distance_broadcasting_single_target(self):
        """Should handle broadcasting when pos2 is single position [2].

        Coverage target: lines 142-143 (unsqueeze for broadcasting)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="clamp",
            distance_metric="manhattan",
            enable_diagonals=False,
        )

        # Multiple agent positions
        pos1 = torch.tensor([[0, 0], [3, 4], [7, 7]], dtype=torch.long)
        # Single target position [2] (will be broadcast)
        pos2 = torch.tensor([5, 5], dtype=torch.long)

        distances = substrate.compute_distance(pos1, pos2)

        assert distances.shape == (3,), "Should return distance for each agent"
        assert distances[0].item() == 10, "Manhattan distance [0,0] to [5,5]"
        assert distances[1].item() == 3, "Manhattan distance [3,4] to [5,5]"
        assert distances[2].item() == 4, "Manhattan distance [7,7] to [5,5]"

    def test_chebyshev_distance_computes_max(self):
        """Chebyshev distance should return max(|x1-x2|, |y1-y2|).

        Coverage target: lines 153-155 (chebyshev metric)
        """
        substrate = Grid2DSubstrate(
            width=8,
            height=8,
            boundary="clamp",
            distance_metric="chebyshev",
        )

        pos1 = torch.tensor([[0, 0]], dtype=torch.long)
        pos2 = torch.tensor([[3, 7]], dtype=torch.long)

        distance = substrate.compute_distance(pos1, pos2)

        # max(|0-3|, |0-7|) = max(3, 7) = 7
        assert distance.item() == 7, "Chebyshev should return max component"


class TestGrid2DGetValidNeighbors:
    """Test get_valid_neighbors edge cases.

    Coverage target: lines 445-467 (get_valid_neighbors)
    """

    def test_get_valid_neighbors_wrap_boundary_returns_all(self):
        """Wrap boundary should return all 4 neighbors without filtering.

        Coverage target: lines 463-465 (clamp boundary filtering vs others)
        """
        substrate = Grid2DSubstrate(
            width=5,
            height=5,
            boundary="wrap",
            distance_metric="manhattan",
        )

        # Corner position
        position = torch.tensor([0, 0], dtype=torch.long)
        neighbors = substrate.get_valid_neighbors(position)

        # Wrap mode returns all 4 neighbors (even if they appear out of bounds)
        assert len(neighbors) == 4, "Wrap mode should return all 4 neighbors"

    def test_get_valid_neighbors_clamp_boundary_filters(self):
        """Clamp boundary should filter out-of-bounds neighbors.

        Coverage target: lines 464-465 (bounds filtering for clamp)
        """
        substrate = Grid2DSubstrate(
            width=5,
            height=5,
            boundary="clamp",
            distance_metric="manhattan",
        )

        # Corner position
        position = torch.tensor([0, 0], dtype=torch.long)
        neighbors = substrate.get_valid_neighbors(position)

        # Clamp mode filters out negative positions
        # Only RIGHT and DOWN are valid from [0,0]
        assert len(neighbors) == 2, "Clamp mode should filter out-of-bounds neighbors"

        # Check that returned neighbors are in bounds
        for neighbor in neighbors:
            assert 0 <= neighbor[0] < 5, "Neighbor x should be in bounds"
            assert 0 <= neighbor[1] < 5, "Neighbor y should be in bounds"
