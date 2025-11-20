"""Integration tests for curriculum level compatibility.

Ensures all 5 curriculum levels compile and load after World Compiler changes.
"""

from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler

CURRICULUM_LEVELS = [
    "L0_0_minimal",
    "L0_5_dual_resource",
    "L1_full_observability",
    "L2_partial_observability",
    "L3_temporal_mechanics",
]


@pytest.fixture
def compiler():
    """UniverseCompiler instance."""
    return UniverseCompiler()


@pytest.fixture
def curriculum_dir():
    """Path to default curriculum."""
    return Path("/home/john/hamlet/configs/default_curriculum")


class TestCurriculumCompatibility:
    """Test all curriculum levels work with World Compiler."""

    @pytest.mark.parametrize("level_name", CURRICULUM_LEVELS)
    def test_level_compiles(self, compiler, curriculum_dir, level_name):
        """Curriculum level compiles successfully."""
        universe = compiler.compile(curriculum_dir)

        # Verify level exists
        assert level_name in universe.available_levels, f"Level {level_name} not found in compiled universe"

        level = universe.get_level(level_name)
        assert level is not None

        # Verify level has affordances
        assert hasattr(level, "affordances")
        assert len(level.affordances.affordances) > 0

        # Verify all affordances have interactions
        for aff in level.affordances.affordances:
            assert hasattr(aff, "interactions")
            assert isinstance(aff.interactions, dict)

    def test_all_levels_have_stable_obs_dim(self, compiler, curriculum_dir):
        """All levels produce consistent observation dimensions."""
        universe = compiler.compile(curriculum_dir)

        obs_dims = {}
        for level_name in universe.available_levels:
            level = universe.get_level(level_name)
            # Get total_dims from observation_spec if available
            if hasattr(level, "observation_spec"):
                obs_dims[level_name] = level.observation_spec.total_dims

        # Verify Grid2D levels have same obs_dim (for transfer learning)
        # L2 is POMDP so will have different obs_dim
        grid2d_levels = ["L0_0_minimal", "L0_5_dual_resource", "L1_full_observability", "L3_temporal_mechanics"]
        grid2d_dims = {name: obs_dims.get(name) for name in grid2d_levels if name in obs_dims}

        if grid2d_dims:
            # All Grid2D non-POMDP levels should have same obs_dim
            dims_list = list(grid2d_dims.values())
            assert all(d == dims_list[0] for d in dims_list), f"Grid2D obs_dim mismatch: {grid2d_dims}"
