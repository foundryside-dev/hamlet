"""Tests for dynamic action space sizing in VectorizedHamletEnv."""

from pathlib import Path

import pytest

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.continuous import Continuous1DSubstrate, Continuous2DSubstrate, Continuous3DSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.substrate.grid3d import Grid3DSubstrate


class TestActionSpaceDynamicSizing:
    """Test that VectorizedHamletEnv uses substrate.action_space_size."""

    @pytest.fixture
    def minimal_config(self):
        """Minimal config for testing (bars, affordances, cascades)."""
        # This would load from a minimal test config directory
        # For now, return None and we'll use fixtures in actual implementation
        return None

    def test_env_respects_grid2d_action_space(self, minimal_config):
        """Environment action_dim matches Grid2D substrate."""
        substrate = Grid2DSubstrate(8, 8, "clamp", "manhattan")

        # Create environment (would need full config in real test)
        # env = <vectorized environment instantiated via fixtures>

        # Verify action dimension matches substrate
        # assert env.action_dim == substrate.action_space_size
        # assert env.action_dim == 10

        # Placeholder for now - actual test will be in integration tests
        # 4 cardinal + 4 diagonals + INTERACT + WAIT
        # 4 cardinal + 4 diagonals + INTERACT (WAIT now comes from custom actions)
        assert substrate.action_space_size == 9

    def test_env_respects_grid3d_action_space(self):
        """Environment action_dim matches Grid3D substrate."""
        substrate = Grid3DSubstrate(8, 8, 3, "clamp")
        # 4 cardinal (XY) + 4 diagonals (XY) + 2 vertical (±Z) + INTERACT (WAIT now custom)
        assert substrate.action_space_size == 11

    def test_env_respects_continuous_action_spaces(self):
        """Environment action_dim matches Continuous substrates."""
        c1d = Continuous1DSubstrate(
            min_x=0.0,
            max_x=10.0,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            action_discretization={"num_directions": 8, "num_magnitudes": 3},
            distance_metric="euclidean",
            observation_encoding="relative",
        )
        c2d = Continuous2DSubstrate(
            min_x=0.0,
            max_x=10.0,
            min_y=0.0,
            max_y=10.0,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            action_discretization={"num_directions": 8, "num_magnitudes": 3},
            distance_metric="euclidean",
            observation_encoding="relative",
        )
        c3d = Continuous3DSubstrate(
            min_x=0.0,
            max_x=10.0,
            min_y=0.0,
            max_y=10.0,
            min_z=0.0,
            max_z=10.0,
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            action_discretization={"num_directions": 8, "num_magnitudes": 3},
            distance_metric="euclidean",
            observation_encoding="relative",
        )

        assert c1d.action_space_size == 3
        # Continuous2D uses discretized actions: movements + INTERACT (STOP is custom-only)
        expected_2d = 8 * (3 - 1) + 1
        assert c2d.action_space_size == expected_2d
        # Continuous3D retains canonical moves + INTERACT
        assert c3d.action_space_size == 7

    def test_env_respects_aspatial_action_space(self):
        """Environment action_dim matches Aspatial substrate."""
        substrate = AspatialSubstrate()
        assert substrate.action_space_size == 1


class TestEnvironmentActionSpace:
    """Ensure compiled universes expose substrate-driven action dimensions."""

    @pytest.mark.parametrize(
        "config_dir",
        [
            Path("configs/test/action_space/grid2d"),
            Path("configs/test/action_space/aspatial"),
            Path("configs/test/action_space/continuous1d"),
        ],
        ids=["grid2d", "aspatial", "continuous1d"],
    )
    def test_env_action_dim_matches_compiled_metadata(self, env_factory, cpu_device, config_dir):
        """VectorizedHamletEnv should honor compiled metadata for action sizing."""

        env = env_factory(config_dir=config_dir, num_agents=1, device_override=cpu_device)

        expected_action_dim = env.metadata.action_count
        assert env.action_dim == expected_action_dim, f"env.action_dim should match compiled metadata for {config_dir}"
        assert env.action_space.action_dim == expected_action_dim, f"Composed action_space must match compiled metadata for {config_dir}"

        # Substrate portion of the action space should align with substrate definition.
        assert (
            env.action_space.substrate_action_count == env.substrate.action_space_size
        ), "Substrate action slice must reflect substrate.action_space_size"
