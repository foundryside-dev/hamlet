"""Test that compiler respects explicit vision_range values without hidden defaults.

BUG-18: Compiler should not inject hidden default vision_range=3 for POMDP local_window.

The no-defaults principle requires:
- vision_range must be explicitly specified in config (Pydantic enforces this)
- Compiler must respect ALL valid values, including vision_range=0
- No silent fallbacks that override operator's explicit choices

This test verifies that vision_range=0 (valid per schema: ge=0) keeps the local window derived
from the explicit config value instead of inflating to a larger default.
"""

import math
import shutil
from pathlib import Path

import pytest

from townlet.universe.compiler import UniverseCompiler


class TestVisionRangeNoDefaults:
    """Test that compiler respects explicit vision_range without hidden defaults."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary config directory with a complete config pack."""
        config_dir = tmp_path / "test_vision_range_0"
        config_dir.mkdir()

        # Copy experiment-level files required by the compiler
        default_pack = Path("configs/default_curriculum")
        for shared_file in [
            "experiment.yaml",
            "stratum.yaml",
            "environment.yaml",
            "actions.yaml",
            "agent.yaml",
            "vfs_profiles.yaml",
            "items.yaml",
            "effects.yaml",
        ]:
            shutil.copy(default_pack / shared_file, config_dir / shared_file)

        # Copy the L2 level so we can modify its vision_range
        levels_dir = config_dir / "levels"
        levels_dir.mkdir()
        l2_source = default_pack / "levels" / "L2_partial_observability"
        l2_dest = levels_dir / l2_source.name
        shutil.copytree(l2_source, l2_dest)

        # Modify curriculum.yaml to set vision_range: 0 (POMDP local window disabled)
        curriculum_yaml = l2_dest / "curriculum.yaml"
        curriculum_content = curriculum_yaml.read_text()
        curriculum_modified = curriculum_content.replace("vision_range: 0.5", "vision_range: 0")
        curriculum_yaml.write_text(curriculum_modified)

        return config_dir

    def test_compiler_respects_vision_range_zero(self, temp_config_dir):
        """Compiler should respect vision_range=0 (minimal window), not default to a larger radius.

        BUG-18: The compiler had `vision_range = raw_configs.environment.vision_range or 3`
        which silently changed explicit 0 → 3, violating no-defaults principle.

        Expected behavior:
        - vision_range=0 → local_window size derived directly from config (no hidden defaults)
        - NOT vision_range=3 → local_window size should not jump to a 7×7 window from a default radius of 3
        """
        compiler = UniverseCompiler()
        compiled = compiler.compile(temp_config_dir, primary_level="L2_partial_observability", use_cache=False)

        # Find local_window field in compiled observation spec
        local_window_field = next(
            (field for field in compiled.observation_spec.fields if field.name == "obs_local_window"),
            None,
        )

        assert local_window_field is not None, "local_window field not found in compiled observation spec"

        grid_width = compiled.stratum.stratum.substrate.grid.width
        # Mirror compiler formula: radius = ceil(range * grid/2), clamped to at least 1
        radius = max(1, int(math.ceil(0 * (grid_width / 2.0))))
        expected_window_size = min((2 * radius) + 1, grid_width) ** 2

        assert local_window_field.dims == expected_window_size, (
            f"Compiler should respect vision_range=0; expected {expected_window_size} dims from formula, " f"got {local_window_field.dims}."
        )

    def test_compiler_respects_default_level_vision_range(self):
        """Baseline test: level-defined vision_range should drive local window size."""
        compiler = UniverseCompiler()
        config_dir = Path("configs/default_curriculum")
        compiled = compiler.compile(config_dir, primary_level="L2_partial_observability", use_cache=False)

        # Find local_window field
        local_window_field = next(
            (field for field in compiled.observation_spec.fields if field.name == "obs_local_window"),
            None,
        )

        assert local_window_field is not None, "local_window field not found"

        # Use the same formula as the compiler to derive expected size from curriculum value
        level_curriculum = compiled.get_level("L2_partial_observability").curriculum.curriculum
        grid_width = compiled.stratum.stratum.substrate.grid.width
        radius = max(1, int(math.ceil(level_curriculum.vision_range * (grid_width / 2.0))))
        expected_window_size = min((2 * radius) + 1, grid_width) ** 2

        assert local_window_field.dims == expected_window_size, (
            f"Expected local window derived from vision_range={level_curriculum.vision_range}, "
            f"got {local_window_field.dims} dims (expected {expected_window_size})."
        )
