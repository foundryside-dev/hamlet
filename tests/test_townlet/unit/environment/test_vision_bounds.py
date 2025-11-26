"""Tests for vision radius bounds (ENV-002) in VectorizedHamletEnv."""

import pytest
import torch

from tests.test_townlet.helpers.config_builder import mutate_curriculum_yaml, mutate_stratum_yaml
from tests.test_townlet.utils.builders import make_vectorized_env_from_pack


def _set_partial_with_vision(vision_range: float):
    """Create curriculum mutator for partial observability with specific vision range."""

    def mutate(curriculum):
        curriculum["curriculum"]["active_vision"] = "partial"
        curriculum["curriculum"]["vision_range"] = vision_range

    return mutate


class TestVisionRadiusBounds:
    """Test vision radius calculation for partial observability."""

    @pytest.fixture
    def grid_100x100_config_pack(self, config_pack_factory):
        """Create config pack with 100x100 grid (at max limit of 10000 cells)."""
        config_dir = config_pack_factory(name="grid100")

        def mutate_stratum(data: dict) -> None:
            grid = data["stratum"]["substrate"]["grid"]
            grid["width"] = 100
            grid["height"] = 100

        mutate_stratum_yaml(config_dir, mutate_stratum)
        return config_dir

    @pytest.fixture
    def grid_50x50_config_pack(self, config_pack_factory):
        """Create config pack with 50x50 grid."""
        config_dir = config_pack_factory(name="grid50")

        def mutate_stratum(data: dict) -> None:
            grid = data["stratum"]["substrate"]["grid"]
            grid["width"] = 50
            grid["height"] = 50

        mutate_stratum_yaml(config_dir, mutate_stratum)
        return config_dir

    def test_vision_radius_at_max_on_large_grid(self, grid_100x100_config_pack, caplog):
        """Vision radius should be at MAX_VISION_RADIUS=50 on 100x100 grid with full vision.

        With a 100x100 grid and vision_range=1.0, raw_radius would be:
        ceil(1.0 * (100 / 2)) = ceil(50) = 50
        This is exactly at the max, so no clamping warning.
        """
        import logging

        mutate_curriculum_yaml(grid_100x100_config_pack, _set_partial_with_vision(1.0))

        with caplog.at_level(logging.WARNING, logger="townlet.environment.vectorized_env"):
            env = make_vectorized_env_from_pack(
                grid_100x100_config_pack,
                level_name="L0_test",
                num_agents=1,
                device=torch.device("cpu"),
            )

        # Vision radius should be exactly 50 (at limit)
        assert env.vision_radius == 50, f"Expected radius=50, got {env.vision_radius}"

        # No clamping warning should be logged since we're exactly at limit
        vision_warnings = [r for r in caplog.records if "exceeds max" in r.message]
        assert len(vision_warnings) == 0, "No warning expected when exactly at limit"

    def test_vision_radius_within_bounds_on_medium_grid(self, grid_50x50_config_pack, caplog):
        """Vision radius should be computed correctly within bounds.

        With a 50x50 grid and vision_range=0.5, raw_radius would be:
        ceil(0.5 * (50 / 2)) = ceil(12.5) = 13
        This is within bounds and should not trigger a warning.
        """
        import logging

        mutate_curriculum_yaml(grid_50x50_config_pack, _set_partial_with_vision(0.5))

        with caplog.at_level(logging.WARNING, logger="townlet.environment.vectorized_env"):
            env = make_vectorized_env_from_pack(
                grid_50x50_config_pack,
                level_name="L0_test",
                num_agents=1,
                device=torch.device("cpu"),
            )

        # Vision radius should be computed normally
        expected_radius = 13  # ceil(0.5 * 25)
        assert env.vision_radius == expected_radius, f"Expected radius={expected_radius}, got {env.vision_radius}"

        # No warning should be logged
        vision_warnings = [r for r in caplog.records if "Vision radius" in r.message]
        assert len(vision_warnings) == 0, "No warning expected for in-bounds vision radius"

    def test_vision_radius_at_least_one(self, grid_50x50_config_pack):
        """Vision radius should be at least 1 even with tiny vision_range.

        With a very small vision_range that would compute to 0, the result
        should still be 1 to ensure a valid local window.
        """
        mutate_curriculum_yaml(grid_50x50_config_pack, _set_partial_with_vision(0.001))

        env = make_vectorized_env_from_pack(
            grid_50x50_config_pack,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Vision radius should be at least 1
        assert env.vision_radius >= 1, f"Vision radius should be >= 1, got {env.vision_radius}"

    def test_local_window_size_correct(self, grid_50x50_config_pack):
        """Local window size should be 2 * radius + 1, clamped to grid size.

        With radius=13 on a 50x50 grid, window_size = min(2*13+1, 50) = 27.
        """
        mutate_curriculum_yaml(grid_50x50_config_pack, _set_partial_with_vision(0.5))

        env = make_vectorized_env_from_pack(
            grid_50x50_config_pack,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Window size should be based on radius
        expected_window_size = 2 * 13 + 1  # 27
        assert env.local_window_size == expected_window_size, f"Expected window_size={expected_window_size}, got {env.local_window_size}"

    def test_local_window_clamped_to_grid_size(self, grid_50x50_config_pack):
        """Local window size should not exceed grid size.

        With vision_range=1.0 on a 50x50 grid:
        - raw_radius = ceil(1.0 * 25) = 25
        - window = 2*25+1 = 51, but clamped to grid_size = 50
        """
        mutate_curriculum_yaml(grid_50x50_config_pack, _set_partial_with_vision(1.0))

        env = make_vectorized_env_from_pack(
            grid_50x50_config_pack,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Window size should be clamped to grid size
        assert env.local_window_size <= 50, f"Window size should be <= grid size 50, got {env.local_window_size}"

    # Note: test_vision_radius_exceeds_max_raises_error was removed because:
    # - vision_range is validated to be <= 1.0 by CurriculumConfig
    # - grid size is validated to be <= 10000 cells (100x100)
    # - With these constraints, max radius = ceil(1.0 * 50) = 50, which is exactly
    #   at MAX_VISION_RADIUS, so we can never exceed it through valid configs.
    # The validation in vectorized_env.py exists as a safety net for future changes
    # to upstream validation, but cannot be tested through normal config paths.
