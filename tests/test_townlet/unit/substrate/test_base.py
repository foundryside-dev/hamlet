"""Tests for SpatialSubstrate base class contracts."""

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.continuous import Continuous1DSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate


class TestActionSpaceSizeProperty:
    """Test that all substrates implement action_space_size property."""

    def test_grid2d_action_space_size(self, grid2d_diagonals):
        """Grid2D has 9 actions when diagonals are enabled (no WAIT)."""
        # 4 cardinal + 4 diagonals + INTERACT
        assert grid2d_diagonals.action_space_size == 9

    def test_grid3d_action_space_size(self, grid3d_diagonals):
        """Grid3D has 11 actions when diagonals are enabled (no WAIT)."""
        # 4 cardinal (XY) + 4 diagonals (XY) + 2 vertical (±Z) + INTERACT
        assert grid3d_diagonals.action_space_size == 11

    def test_continuous1d_action_space_size(self, cont1d):
        """Continuous1D has 3 actions (±X/INTERACT)."""
        s = cont1d
        assert s.action_space_size == 3
        assert s.action_space_size == 2 * s.position_dim + 1

    def test_continuous2d_action_space_size(self, cont2d):
        """Continuous2D uses discretized moves (2*num_directions) + INTERACT."""
        s = cont2d
        # With num_directions=8 and magnitudes=3 → 16 movement actions + INTERACT
        assert s.action_space_size == 17
        assert s.action_space_size == (2 * s.action_discretization["num_directions"]) + 1

    def test_continuous3d_action_space_size(self, cont3d):
        """Continuous3D has 6 moves (±X/±Y/±Z) + INTERACT."""
        s = cont3d
        assert s.action_space_size == 7
        assert s.action_space_size == 2 * s.position_dim + 1

    def test_aspatial_action_space_size(self):
        """Aspatial has a single action (INTERACT only)."""
        substrate = AspatialSubstrate()
        assert substrate.action_space_size == 1

    def test_action_space_formula_consistency(self):
        """Verify action counts match configured movement schemas."""
        test_cases = [
            # Grid substrates with diagonals disabled fall back to 2N+1 actions (no WAIT)
            (Grid2DSubstrate(8, 8, "clamp", "manhattan", enable_diagonals=False), 2, 5),
            (Grid3DSubstrate(8, 8, 3, "clamp", "manhattan", enable_diagonals=False), 3, 7),
            # Continuous substrates use discretized actions; minimal expectations remain 2N+1 (no WAIT)
            (
                Continuous1DSubstrate(
                    min_x=0.0,
                    max_x=10.0,
                    boundary="clamp",
                    movement_delta=0.5,
                    interaction_radius=1.0,
                    action_discretization={"num_directions": 8, "num_magnitudes": 3},
                    distance_metric="manhattan",
                ),
                1,
                3,
            ),
        ]

        for substrate, expected_dim, expected_actions in test_cases:
            assert substrate.position_dim == expected_dim
            assert substrate.action_space_size == expected_actions
            assert substrate.action_space_size == (2 * substrate.position_dim) + 1
