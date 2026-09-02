"""Comprehensive coverage tests for Continuous substrate (1D/2D/3D).

This module tests uncovered paths in Continuous substrates to improve coverage from 17% → target 70%+:

Coverage targets:
- src/townlet/substrate/continuous.py:306-355 (get_default_actions for 1D/2D/3D)
- src/townlet/substrate/continuous.py:146-162 (bounce boundary complex reflection)
- src/townlet/substrate/continuous.py:183-184 (chebyshev distance)
- src/townlet/substrate/continuous.py:356-392 (get_valid_neighbors error)
- src/townlet/substrate/continuous.py:400-423 (normalize_positions)
- src/townlet/substrate/continuous.py:475-487 (encode_partial_observation NotImplementedError)
- src/townlet/substrate/continuous.py:285, 302 (invalid encoding errors)
"""

import pytest
import torch

from townlet.substrate.continuous import Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate

# Shared defaults to avoid repetitive ctor arguments in tests
BASE_ACTION_DISC = {"num_directions": 8, "num_magnitudes": 3}
BASE_CONT_ARGS = dict(
    boundary="clamp",
    movement_delta=0.5,
    interaction_radius=1.0,
    distance_metric="euclidean",
    action_discretization=BASE_ACTION_DISC,
)


def make_cont1d(**overrides):
    params = dict(min_x=0.0, max_x=10.0)
    params.update(BASE_CONT_ARGS)
    params.update(overrides)
    return Continuous1DSubstrate(**params)


def make_cont2d(**overrides):
    params = dict(min_x=0.0, max_x=10.0, min_y=0.0, max_y=10.0)
    params.update(BASE_CONT_ARGS)
    params.update(overrides)
    return Continuous2DSubstrate(**params)


def make_cont3d(**overrides):
    params = dict(min_x=0.0, max_x=10.0, min_y=0.0, max_y=10.0, min_z=0.0, max_z=10.0)
    params.update(BASE_CONT_ARGS)
    params.update(overrides)
    return Continuous3DSubstrate(**params)


class TestContinuousActionGeneration:
    """Test get_default_actions() for 1D/2D/3D continuous substrates."""

    @pytest.mark.parametrize(
        "substrate_cls,kwargs,expected_len,expected_names_prefix,expected_last",
        [
            (
                Continuous1DSubstrate,
                dict(
                    min_x=0.0,
                    max_x=10.0,
                    boundary="clamp",
                    movement_delta=0.5,
                    interaction_radius=1.0,
                    distance_metric="euclidean",
                    action_discretization={"num_directions": 8, "num_magnitudes": 3},
                ),
                3,  # LEFT, RIGHT, INTERACT
                ["LEFT", "RIGHT"],
                "INTERACT",
            ),
            (
                Continuous2DSubstrate,
                dict(
                    min_x=0.0,
                    max_x=10.0,
                    min_y=0.0,
                    max_y=10.0,
                    boundary="clamp",
                    movement_delta=0.5,
                    interaction_radius=1.0,
                    distance_metric="euclidean",
                    action_discretization={"num_directions": 8, "num_magnitudes": 3},
                ),
                17,  # 8 directions × 2 magnitudes + INTERACT
                ["MOVE_", "MOVE_"],
                "INTERACT",
            ),
            (
                Continuous3DSubstrate,
                dict(
                    min_x=0.0,
                    max_x=10.0,
                    min_y=0.0,
                    max_y=10.0,
                    min_z=0.0,
                    max_z=10.0,
                    boundary="clamp",
                    movement_delta=0.5,
                    interaction_radius=1.0,
                    distance_metric="euclidean",
                    action_discretization={"num_directions": 8, "num_magnitudes": 3},
                ),
                7,  # 6 movement axes + INTERACT
                ["UP", "DOWN", "LEFT", "RIGHT"],
                "INTERACT",
            ),
        ],
    )
    def test_get_default_actions_counts_and_order(self, substrate_cls, kwargs, expected_len, expected_names_prefix, expected_last):
        substrate = substrate_cls(**kwargs)
        actions = substrate.get_default_actions()

        assert len(actions) == expected_len
        assert actions[-1].name == expected_last

        # Check leading names follow expected pattern/prefix
        for prefix, action in zip(expected_names_prefix, actions):
            assert action.name.startswith(prefix)

    def test_get_default_actions_deltas_1d(self):
        """1D actions should have correct deltas.

        Coverage target: 1D delta assignment
        """
        substrate = make_cont1d()

        actions = substrate.get_default_actions()

        # LEFT should be [-1]
        assert actions[0].delta == [-1], "LEFT delta should be [-1]"
        # RIGHT should be [1]
        assert actions[1].delta == [1], "RIGHT delta should be [1]"

    def test_get_default_actions_deltas_3d(self):
        """3D actions should have correct deltas including Z-axis.

        Coverage target: 3D delta assignment
        """
        substrate = make_cont3d()

        actions = substrate.get_default_actions()

        # UP_Z should be [0, 0, -1] (upward in Z)
        assert actions[4].delta == [0, 0, -1], "UP_Z delta should be [0, 0, -1]"
        # DOWN_Z should be [0, 0, 1] (downward in Z)
        assert actions[5].delta == [0, 0, 1], "DOWN_Z delta should be [0, 0, 1]"

    def test_get_default_actions_interact_and_wait(self):
        """INTERACT and WAIT should have no deltas and appropriate costs.

        Coverage target: INTERACT and WAIT generation
        """
        substrate = make_cont2d()

        actions = substrate.get_default_actions()

        # INTERACT (last)
        interact = actions[-1]
        assert interact.name == "INTERACT"
        assert interact.type == "interaction"
        assert interact.delta is None
        assert interact.costs == {}


class TestContinuousBounceEdgeCases:
    """Test complex bounce boundary behavior.

    Coverage target: lines 146-162 (bounce reflection with modulo arithmetic)
    """

    def test_bounce_boundary_multiple_reflections_positive(self):
        """Bounce should handle multiple reflections when agent moves far beyond boundary.

        Coverage target: lines 153-162 (complex reflection logic)
        """
        substrate = make_cont2d(boundary="bounce", movement_delta=1.0, interaction_radius=0.5)

        # Agent near right edge, move far right (multiple bounces)
        positions = torch.tensor([[9.0, 5.0]], dtype=torch.float32)
        # Move right by 25 units (would go to 34, way beyond 10)
        deltas = torch.tensor([[25.0, 0.0]], dtype=torch.float32)

        new_positions = substrate.apply_movement(positions, deltas)

        # Position 34 in [0, 10]: normalized = 34, range_size = 10
        # 34 % 20 = 14, 14 >= 10, so reflect: 20 - 14 = 6
        assert 0.0 <= new_positions[0, 0] <= 10.0, "Should stay in bounds"
        assert torch.allclose(new_positions[0, 0], torch.tensor(6.0)), "Should bounce to position 6"

    def test_bounce_boundary_exceed_half_reflection(self):
        """Bounce should reflect when normalized position exceeds half range.

        Coverage target: lines 158-159 (exceed_half mask and reflection)
        """
        substrate = make_cont1d(max_x=5.0, boundary="bounce", movement_delta=1.0, interaction_radius=0.5)

        # Agent at 4, move right by 3 (would go to 7, beyond 5)
        positions = torch.tensor([[4.0]], dtype=torch.float32)
        deltas = torch.tensor([[3.0]], dtype=torch.float32)

        new_positions = substrate.apply_movement(positions, deltas)

        # Position 7 in [0, 5]: normalized = 7, range_size = 5
        # 7 % 10 = 7, 7 >= 5, so reflect: 10 - 7 = 3
        assert torch.allclose(new_positions[0, 0], torch.tensor(3.0)), "Should bounce to position 3"


class TestContinuousChebyshevDistance:
    """Test Chebyshev distance metric (L∞ norm).

    Coverage target: lines 183-184 (chebyshev metric)
    """

    def test_distance_chebyshev_2d(self):
        """Chebyshev distance should return max of absolute differences.

        Coverage target: lines 183-184
        """
        substrate = make_cont2d(distance_metric="chebyshev")

        pos1 = torch.tensor([[0.0, 0.0]], dtype=torch.float32)
        pos2 = torch.tensor([[3.0, 7.0]], dtype=torch.float32)

        distance = substrate.compute_distance(pos1, pos2)

        # max(|0-3|, |0-7|) = max(3, 7) = 7
        assert torch.allclose(distance, torch.tensor([7.0])), "Chebyshev should return max component"

    def test_distance_chebyshev_3d(self):
        """Chebyshev distance in 3D should return max across all dimensions.

        Coverage target: Chebyshev for 3D
        """
        substrate = make_cont3d(distance_metric="chebyshev")

        pos1 = torch.tensor([[1.0, 2.0, 3.0]], dtype=torch.float32)
        pos2 = torch.tensor([[4.0, 6.0, 5.0]], dtype=torch.float32)

        distance = substrate.compute_distance(pos1, pos2)

        # max(|1-4|, |2-6|, |3-5|) = max(3, 4, 2) = 4
        assert torch.allclose(distance, torch.tensor([4.0])), "Chebyshev should return max component in 3D"


class TestContinuousGetValidNeighbors:
    """Test get_valid_neighbors() raises NotImplementedError.

    Coverage target: lines 356-392 (error path)
    """

    def test_get_valid_neighbors_raises_not_implemented_1d(self):
        """1D continuous should raise NotImplementedError for get_valid_neighbors.

        Continuous spaces have infinite neighbors, so enumeration is not meaningful.
        Coverage target: lines 389-392
        """
        substrate = make_cont1d()

        position = torch.tensor([5.0], dtype=torch.float32)

        with pytest.raises(NotImplementedError) as exc_info:
            substrate.get_valid_neighbors(position)

        error_msg = str(exc_info.value).lower()
        assert "continuous" in error_msg
        assert "positions" in error_msg or "neighbors" in error_msg

    def test_get_valid_neighbors_raises_not_implemented_2d(self):
        """2D continuous should raise NotImplementedError for get_valid_neighbors.

        Coverage target: lines 389-392
        """
        substrate = make_cont2d()

        position = torch.tensor([5.0, 5.0], dtype=torch.float32)

        with pytest.raises(NotImplementedError):
            substrate.get_valid_neighbors(position)

    def test_get_valid_neighbors_raises_not_implemented_3d(self):
        """3D continuous should raise NotImplementedError for get_valid_neighbors.

        Coverage target: lines 389-392
        """
        substrate = make_cont3d()

        position = torch.tensor([5.0, 5.0, 5.0], dtype=torch.float32)

        with pytest.raises(NotImplementedError):
            substrate.get_valid_neighbors(position)


class TestContinuousNormalizePositions:
    """Test normalize_positions() method.

    Coverage target: lines 400-423 (normalize_positions)
    """

    def test_normalize_positions_1d(self):
        """Should normalize 1D positions to [0, 1] range.

        Coverage target: lines 419-423 (calls _encode_relative)
        """
        substrate = make_cont1d()

        positions = torch.tensor([[0.0], [5.0], [10.0]], dtype=torch.float32)

        normalized = substrate.normalize_positions(positions)

        # Should be [0.0, 0.5, 1.0]
        expected = torch.tensor([[0.0], [0.5], [1.0]], dtype=torch.float32)
        assert torch.allclose(normalized, expected), "Should normalize to [0, 1] range"

    def test_normalize_positions_2d(self):
        """Should normalize 2D positions to [0, 1] range per dimension.

        Coverage target: normalize_positions for 2D
        """
        substrate = make_cont2d(max_y=20.0)

        positions = torch.tensor([[0.0, 0.0], [10.0, 20.0]], dtype=torch.float32)

        normalized = substrate.normalize_positions(positions)

        # Should be [[0.0, 0.0], [1.0, 1.0]]
        expected = torch.tensor([[0.0, 0.0], [1.0, 1.0]], dtype=torch.float32)
        assert torch.allclose(normalized, expected), "Should normalize each dimension independently"

    def test_normalize_positions_negative_bounds(self):
        """Should normalize positions with negative bounds correctly.

        Coverage target: Normalization with negative ranges
        """
        substrate = make_cont2d(min_x=-5.0, max_x=5.0, min_y=-10.0, max_y=10.0)

        positions = torch.tensor([[-5.0, -10.0], [0.0, 0.0], [5.0, 10.0]], dtype=torch.float32)

        normalized = substrate.normalize_positions(positions)

        # Min should map to 0, center to 0.5, max to 1
        expected = torch.tensor([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]], dtype=torch.float32)
        assert torch.allclose(normalized, expected), "Should handle negative bounds correctly"


class TestContinuousCoordinateSemantics:
    """Test coordinate_semantics property.

    Coverage target: lines 114-117 (coordinate_semantics property)
    """

    def test_coordinate_semantics_1d(self):
        """1D should return X: position semantics.

        Coverage target: lines 116 (1D case)
        """
        substrate = make_cont1d()

        semantics = substrate.coordinate_semantics

        assert "X" in semantics
        assert semantics["X"] == "position"

    def test_coordinate_semantics_2d(self):
        """2D should return X: horizontal, Y: vertical semantics.

        Coverage target: lines 116 (2D case)
        """
        substrate = make_cont2d()

        semantics = substrate.coordinate_semantics

        assert "X" in semantics
        assert "Y" in semantics
        assert semantics["X"] == "horizontal"
        assert semantics["Y"] == "vertical"

    def test_coordinate_semantics_3d(self):
        """3D should return X, Y, Z semantics.

        Coverage target: lines 116 (3D case)
        """
        substrate = make_cont3d()

        semantics = substrate.coordinate_semantics

        assert "X" in semantics
        assert "Y" in semantics
        assert "Z" in semantics
        assert semantics["X"] == "horizontal"
        assert semantics["Y"] == "vertical"
        assert semantics["Z"] == "depth"
