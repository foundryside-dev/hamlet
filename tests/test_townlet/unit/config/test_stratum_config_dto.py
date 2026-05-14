"""Tests for StratumConfig DTO (v2.1 stratum.yaml)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from townlet.config.stratum_config import (
    ActionDiscretizationConfig,
    ContinuousConfig,
    StratumConfig,
    SubstrateConfig,
)


class TestStratumConfigLoading:
    """Test loading StratumConfig from real v2.1 YAML."""

    def test_load_from_model_config_stratum_yaml(self):
        """Load stratum.yaml from the canonical model_config pack."""
        path = Path("configs/test/model_config/stratum.yaml")
        assert path.exists(), f"stratum.yaml not found at {path}"

        config = StratumConfig.from_yaml(path)
        root = config.stratum

        # Basic shape and enums
        assert root.version == "1.0"
        assert root.vision_support in {"global", "partial", "both", "none"}
        assert root.temporal_support in {"enabled", "disabled"}

        # Substrate is a 2D grid with expected parameters
        substrate = root.substrate
        assert substrate.type == "grid"
        assert substrate.grid is not None
        assert substrate.grid.topology == "square"
        assert substrate.grid.width == 8
        assert substrate.grid.height == 8
        assert substrate.grid.boundary == "clamp"
        assert substrate.grid.distance_metric == "manhattan"
        assert substrate.grid.observation_encoding == "relative"
        assert substrate.grid.diagonals is False

        # Only one substrate block should be populated
        assert substrate.gridnd is None
        assert substrate.continuous is None
        assert substrate.aspatial is None

    def test_stratum_config_rejects_extra_fields(self, tmp_path: Path):
        """Extra top-level fields should be rejected (extra=forbid)."""
        stratum_yaml = tmp_path / "stratum.yaml"
        stratum_yaml.write_text("""
stratum:
  version: "1.0"
  substrate:
    type: grid
    grid:
      topology: square
      width: 4
      height: 4
      boundary: clamp
      distance_metric: manhattan
      observation_encoding: relative
      diagonals: true
  vision_support: global
  temporal_support: disabled
  unexpected_field: true
""")

        with pytest.raises(ValidationError):
            StratumConfig.from_yaml(stratum_yaml)


class TestSubstrateConfigValidation:
    """Direct substrate-level validation tests."""

    def test_grid_type_requires_grid_block(self):
        """type='grid' without grid block should fail."""
        with pytest.raises(ValidationError):
            SubstrateConfig(type="grid", grid=None, gridnd=None, continuous=None, aspatial=None)  # type: ignore[call-arg]

    def test_only_one_substrate_block_allowed(self):
        """Providing multiple substrate blocks should fail."""
        # Minimal continuous config for this test
        continuous = ContinuousConfig(
            dimensions=1,
            bounds=[(0.0, 1.0)],
            boundary="clamp",
            movement_delta=0.1,
            interaction_radius=0.5,
            distance_metric="euclidean",
            observation_encoding="relative",
            action_discretization=ActionDiscretizationConfig(num_directions=8, num_magnitudes=3),
        )

        with pytest.raises(ValidationError):
            SubstrateConfig(  # type: ignore[call-arg]
                type="continuous",
                grid=None,
                gridnd=None,
                continuous=continuous,
                aspatial={},
            )
