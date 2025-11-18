"""Test substrate configuration schema."""

from pathlib import Path

import pytest
import torch

from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.config import (
    AspatialSubstrateConfig,
    Grid2DSubstrateConfig,
    SubstrateConfig,
    load_substrate_config,
)
from townlet.substrate.factory import SubstrateFactory
from townlet.substrate.grid2d import Grid2DSubstrate


def test_grid2d_config_valid():
    """Valid Grid2D config should parse successfully."""
    config_data = {
        "topology": "square",
        "width": 8,
        "height": 8,
        "boundary": "clamp",
        "distance_metric": "manhattan",
        "observation_encoding": "relative",
        "diagonals": True,
    }

    config = Grid2DSubstrateConfig(**config_data)

    assert config.width == 8
    assert config.height == 8
    assert config.boundary == "clamp"


def test_grid2d_config_invalid_dimensions():
    """Grid2D config with invalid dimensions should fail."""
    config_data = {
        "topology": "square",
        "width": 0,  # Invalid!
        "height": 8,
        "boundary": "clamp",
        "distance_metric": "manhattan",
        "observation_encoding": "relative",
        "diagonals": True,
    }

    with pytest.raises(ValueError, match="greater than 0"):
        Grid2DSubstrateConfig(**config_data)


def test_aspatial_config_valid():
    """Valid aspatial config should parse successfully."""
    config_data = {}  # No fields needed for aspatial

    config = AspatialSubstrateConfig(**config_data)

    # Just verify it parses successfully (no fields to check)
    assert config is not None


def test_substrate_config_grid2d():
    """SubstrateConfig with type='grid' should require grid config."""
    config_data = {
        "version": "1.0",
        "description": "Test grid substrate",
        "type": "grid",
        "grid": {
            "topology": "square",
            "width": 8,
            "height": 8,
            "boundary": "clamp",
            "distance_metric": "manhattan",
            "observation_encoding": "relative",
            "diagonals": True,
        },
    }

    config = SubstrateConfig(**config_data)

    assert config.type == "grid"
    assert config.grid is not None
    assert config.grid.width == 8


def test_substrate_config_missing_grid():
    """SubstrateConfig with type='grid' but missing grid config should fail."""
    config_data = {
        "version": "1.0",
        "description": "Test",
        "type": "grid",
        # Missing grid config!
    }

    with pytest.raises(ValueError, match="grid configuration"):
        SubstrateConfig(**config_data)


def test_factory_build_grid2d():
    """Factory should build Grid2DSubstrate from config."""
    config_data = {
        "version": "1.0",
        "description": "Test grid",
        "type": "grid",
        "grid": {
            "topology": "square",
            "width": 8,
            "height": 8,
            "boundary": "clamp",
            "distance_metric": "manhattan",
            "observation_encoding": "relative",
            "diagonals": True,
        },
    }

    config = SubstrateConfig(**config_data)
    substrate = SubstrateFactory.build(config, device=torch.device("cpu"))

    assert isinstance(substrate, Grid2DSubstrate)
    assert substrate.width == 8
    assert substrate.height == 8


def test_factory_build_aspatial():
    """Factory should build AspatialSubstrate from config."""
    config_data = {
        "version": "1.0",
        "description": "Test aspatial",
        "type": "aspatial",
        "aspatial": {},  # Empty dict (no fields needed)
    }

    config = SubstrateConfig(**config_data)
    substrate = SubstrateFactory.build(config, device=torch.device("cpu"))

    assert isinstance(substrate, AspatialSubstrate)
    assert substrate.position_dim == 0


# Phase 5C: observation_encoding tests
def test_grid_config_observation_encoding_valid():
    """Test Grid config accepts valid observation_encoding values."""
    from townlet.substrate.config import GridConfig

    for encoding in ["relative", "scaled", "absolute"]:
        config = GridConfig(
            topology="square",
            width=8,
            height=8,
            boundary="clamp",
            distance_metric="manhattan",
            observation_encoding=encoding,
            diagonals=True,
        )
        assert config.observation_encoding == encoding


def test_grid_config_observation_encoding_default():
    """Test Grid config requires observation_encoding (no defaults)."""
    import pydantic_core

    from townlet.substrate.config import GridConfig

    with pytest.raises((ValueError, pydantic_core._pydantic_core.ValidationError)):
        GridConfig(
            topology="square",
            width=8,
            height=8,
            boundary="clamp",
            distance_metric="manhattan",
            diagonals=True,
            # observation_encoding NOT provided - should fail!
        )


def test_grid_config_observation_encoding_invalid():
    """Test Grid config rejects invalid observation_encoding."""
    from townlet.substrate.config import GridConfig

    with pytest.raises(ValueError, match="observation_encoding"):
        GridConfig(
            topology="square",
            width=8,
            height=8,
            boundary="clamp",
            distance_metric="manhattan",
            observation_encoding="invalid",  # Not in Literal
            diagonals=True,
        )


def test_continuous_config_observation_encoding_valid():
    """Test Continuous config accepts valid observation_encoding values."""
    from townlet.substrate.config import ContinuousConfig

    for encoding in ["relative", "scaled", "absolute"]:
        config = ContinuousConfig(
            dimensions=2,
            bounds=[(0.0, 10.0), (0.0, 10.0)],
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding=encoding,
            action_discretization={"num_directions": 8, "num_magnitudes": 3},
        )
        assert config.observation_encoding == encoding


def test_continuous_config_observation_encoding_default():
    """Test Continuous config requires observation_encoding (no defaults)."""
    import pydantic_core

    from townlet.substrate.config import ContinuousConfig

    with pytest.raises((ValueError, pydantic_core._pydantic_core.ValidationError)):
        ContinuousConfig(
            dimensions=2,
            bounds=[(0.0, 10.0), (0.0, 10.0)],
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            # observation_encoding NOT provided - should fail!
            action_discretization={"num_directions": 8, "num_magnitudes": 3},
        )


def test_gridnd_config_includes_topology_field():
    """GridNDConfig should require topology field (no defaults)."""
    from townlet.substrate.config import GridNDConfig

    config = GridNDConfig(
        dimension_sizes=[5, 5, 5, 5],
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
        topology="hypercube",
    )
    assert hasattr(config, "topology")
    assert config.topology == "hypercube"


def test_gridnd_config_topology_can_be_overridden():
    """GridNDConfig should allow explicit topology specification."""
    from townlet.substrate.config import GridNDConfig

    config = GridNDConfig(
        dimension_sizes=[5, 5, 5, 5],
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
        topology="hypercube",
    )
    assert config.topology == "hypercube"


def test_gridnd_config_validates_yaml_with_topology():
    """GridNDConfig should parse YAML with topology field."""
    from townlet.substrate.config import GridNDConfig

    yaml_data = {
        "dimension_sizes": [5, 5, 5, 5],
        "boundary": "clamp",
        "distance_metric": "manhattan",
        "observation_encoding": "relative",
        "topology": "hypercube",
    }
    config = GridNDConfig(**yaml_data)
    assert config.topology == "hypercube"


# =============================================================================
# CONFIG FILE TESTS (from TASK-002A)
# =============================================================================


@pytest.mark.parametrize(
    "config_path,expected_width,expected_height,expected_obs_grid_dim",
    [
        (Path("configs/default_curriculum/stratum.yaml"), 8, 8, 64),
        (Path("configs/test/model_config/stratum.yaml"), 8, 8, 64),
    ],
)
def test_substrate_config_schema_valid(config_path, expected_width, expected_height, expected_obs_grid_dim):
    """Stratum config should load and expose substrate schema."""
    from townlet.config.stratum_config import StratumConfig

    cfg = StratumConfig.from_yaml(config_path)
    grid = cfg.stratum.substrate.grid
    assert grid is not None
    assert grid.topology == "square"
    assert grid.width == expected_width
    assert grid.height == expected_height
    assert grid.boundary == "clamp"
    assert grid.distance_metric == "manhattan"

    obs_grid_dim = grid.width * grid.height
    assert obs_grid_dim == expected_obs_grid_dim


@pytest.mark.parametrize(
    "config_path",
    [
        Path("configs/default_curriculum/stratum.yaml"),
        Path("configs/test/model_config/stratum.yaml"),
    ],
)
def test_substrate_config_behavioral_equivalence(config_path):
    """Stratum substrate config should produce a standard Grid2D substrate."""
    from townlet.config.stratum_config import StratumConfig

    cfg = StratumConfig.from_yaml(config_path)
    grid = cfg.stratum.substrate.grid
    assert grid is not None
    assert grid.topology == "square"  # Standard 2D grid
    assert grid.boundary == "clamp"
    assert grid.distance_metric == "manhattan"
    assert grid.width == grid.height


def test_substrate_config_no_defaults():
    """Substrate config should require all fields (no-defaults principle)."""

    # Attempt to load incomplete config (missing required fields)
    incomplete_yaml = """
version: "1.0"
type: "grid"
# Missing: description, grid section
"""
    incomplete_path = Path("/tmp/incomplete_substrate.yaml")
    incomplete_path.write_text(incomplete_yaml)

    # Should raise ValidationError (not fall back to defaults)
    with pytest.raises(Exception) as exc_info:
        load_substrate_config(incomplete_path)

    # Error message should mention missing field
    assert "description" in str(exc_info.value).lower()

    # Cleanup
    incomplete_path.unlink()


def test_substrate_config_file_exists():
    """Production packs expose substrate via stratum.yaml (v2.1 hierarchy)."""
    production_configs = [
        Path("configs/default_curriculum/stratum.yaml"),
        Path("configs/test/model_config/stratum.yaml"),
    ]

    for stratum_path in production_configs:
        assert stratum_path.exists(), f"Missing stratum.yaml at {stratum_path}"


# Edge Case Tests (Priority 2 from code review)


def test_substrate_config_invalid_boundary():
    """Invalid boundary mode should raise ValidationError."""
    invalid_yaml = """
version: "1.0"
description: "Test invalid boundary"
type: "grid"
grid:
  topology: "square"
  width: 8
  height: 8
  boundary: "invalid_mode"
  distance_metric: "manhattan"
"""
    invalid_path = Path("/tmp/invalid_boundary_substrate.yaml")
    invalid_path.write_text(invalid_yaml)

    # Should raise Pydantic ValidationError for invalid literal value
    with pytest.raises(ValueError) as exc_info:
        load_substrate_config(invalid_path)

    # Error message should indicate invalid boundary value
    error_msg = str(exc_info.value).lower()
    assert "boundary" in error_msg or "invalid" in error_msg

    # Cleanup
    invalid_path.unlink()


def test_substrate_config_invalid_distance_metric():
    """Invalid distance metric should raise ValidationError."""
    invalid_yaml = """
version: "1.0"
description: "Test invalid distance metric"
type: "grid"
grid:
  topology: "square"
  width: 8
  height: 8
  boundary: "clamp"
  distance_metric: "invalid_metric"
"""
    invalid_path = Path("/tmp/invalid_distance_substrate.yaml")
    invalid_path.write_text(invalid_yaml)

    # Should raise Pydantic ValidationError for invalid literal value
    with pytest.raises(ValueError) as exc_info:
        load_substrate_config(invalid_path)

    # Error message should indicate invalid distance_metric value
    error_msg = str(exc_info.value).lower()
    assert "distance_metric" in error_msg or "invalid" in error_msg

    # Cleanup
    invalid_path.unlink()


def test_substrate_config_non_square_grid():
    """Non-square grids (width ≠ height) should be valid."""
    non_square_yaml = """
version: "1.0"
description: "Non-square grid test"
type: "grid"
grid:
  topology: "square"
  width: 10
  height: 5
  boundary: "clamp"
  distance_metric: "manhattan"
  observation_encoding: "relative"
  diagonals: false
"""
    non_square_path = Path("/tmp/non_square_substrate.yaml")
    non_square_path.write_text(non_square_yaml)

    # Should load successfully (non-square grids are valid)
    config = load_substrate_config(non_square_path)

    assert config.grid.width == 10
    assert config.grid.height == 5
    assert config.grid.width != config.grid.height  # Verify non-square

    # Cleanup
    non_square_path.unlink()


def test_substrate_config_aspatial_loading():
    """Aspatial config should load correctly end-to-end."""
    import torch

    from townlet.substrate.factory import SubstrateFactory

    # Load example aspatial config
    aspatial_path = Path("docs/examples/substrate-aspatial.yaml")
    config = load_substrate_config(aspatial_path)

    # Verify config structure
    assert config.type == "aspatial"
    assert config.aspatial is not None
    assert config.grid is None

    # Verify factory can build substrate
    substrate = SubstrateFactory.build(config, device=torch.device("cpu"))

    # Verify substrate behavior
    assert substrate.position_dim == 0
    assert substrate.get_observation_dim() == 0


@pytest.mark.parametrize(
    "example_name",
    [
        "substrate-aspatial.yaml",
        "substrate-euclidean-distance.yaml",
        "substrate-toroidal-grid.yaml",
    ],
)
def test_example_configs_valid(example_name):
    """Example configs should load and validate correctly."""
    example_path = Path("docs/examples") / example_name

    # Should load without errors
    config = load_substrate_config(example_path)

    # All examples should have valid version and description
    assert config.version == "1.0"
    assert config.description

    # Verify config type matches filename
    if "aspatial" in example_name:
        assert config.type == "aspatial"
        assert config.aspatial is not None
    else:
        assert config.type == "grid"
        assert config.grid is not None
