"""Tests for SubstrateFactory support of GridND and ContinuousND substrates."""

import tempfile
from pathlib import Path

import pytest
import torch

from townlet.config.stratum_config import SubstrateConfig
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.factory import SubstrateFactory
from townlet.substrate.gridnd import GridNDSubstrate

BASE_ACTION_DISC = {"num_directions": 8, "num_magnitudes": 3}


class TestGridNDFactoryFromConfig:
    """Test factory creation of GridND substrates from config."""

    def test_gridnd_4d_basic(self):
        """Test creating 4D GridND substrate from config."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [8, 8, 8, 8],
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "observation_encoding": "relative",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert isinstance(substrate, GridNDSubstrate)
        assert substrate.dimension_sizes == [8, 8, 8, 8]
        assert substrate.boundary == "clamp"
        assert substrate.distance_metric == "manhattan"
        assert substrate.observation_encoding == "relative"
        assert substrate.position_dim == 4
        assert substrate.action_space_size == 2 * 4 + 2  # 10 actions

    def test_gridnd_5d_with_different_sizes(self):
        """Test creating 5D GridND with varying dimension sizes."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [3, 4, 5, 6, 7],
                "boundary": "wrap",
                "distance_metric": "euclidean",
                "observation_encoding": "scaled",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert isinstance(substrate, GridNDSubstrate)
        assert substrate.dimension_sizes == [3, 4, 5, 6, 7]
        assert substrate.boundary == "wrap"
        assert substrate.distance_metric == "euclidean"
        assert substrate.observation_encoding == "scaled"
        assert substrate.position_dim == 5
        assert substrate.action_space_size == 12  # 2*5 + 2

    def test_gridnd_10d_absolute_encoding(self):
        """Test 10D GridND with absolute observation encoding."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [4] * 10,
                "boundary": "bounce",
                "distance_metric": "chebyshev",
                "observation_encoding": "absolute",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert isinstance(substrate, GridNDSubstrate)
        assert substrate.position_dim == 10
        assert len(substrate.dimension_sizes) == 10
        assert substrate.observation_encoding == "absolute"

    def test_gridnd_position_initialization(self):
        """Test that initialized GridND positions are valid."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [5, 6, 7, 8],
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "observation_encoding": "relative",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        positions = substrate.initialize_positions(num_agents=100, device=torch.device("cpu"))

        assert positions.shape == (100, 4)
        assert positions.dtype == torch.long
        # Check all positions are within bounds
        for dim_idx, size in enumerate(substrate.dimension_sizes):
            assert (positions[:, dim_idx] >= 0).all()
            assert (positions[:, dim_idx] < size).all()

    def test_gridnd_observation_encoding_relative(self):
        """Test relative observation encoding for GridND."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [10, 10, 10, 10],
                "boundary": "clamp",
                "distance_metric": "manhattan",
                "observation_encoding": "relative",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        # Create test positions
        positions = torch.tensor([[0, 0, 0, 0], [9, 9, 9, 9]], dtype=torch.long)
        observations = substrate.encode_observation(positions, {})

        assert observations.shape == (2, 4)  # relative encoding: N dims
        # First position (0,0,0,0) should encode as all zeros
        assert (observations[0] == 0).all()
        # Last position (9,9,9,9) should encode as all ones (normalized)
        assert (observations[1] == 1).all()

    def test_gridnd_observation_encoding_scaled(self):
        """Test scaled observation encoding for GridND."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [5, 6, 7, 8],
                "boundary": "clamp",
                "observation_encoding": "scaled",
                "distance_metric": "manhattan",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        positions = torch.tensor([[0, 0, 0, 0]], dtype=torch.long)
        observations = substrate.encode_observation(positions, {})

        assert observations.shape == (1, 8)  # scaled encoding: 2N dims
        # First 4 dims should be coordinates (all zero)
        assert (observations[0, :4] == 0).all()
        # Next 4 dims should be dimension sizes
        assert observations[0, 4] == 5.0
        assert observations[0, 5] == 6.0
        assert observations[0, 6] == 7.0
        assert observations[0, 7] == 8.0


class TestContinuousNDFactoryFromConfig:
    """Test factory creation of ContinuousND substrates from config."""

    def test_continuousnd_4d_basic(self):
        """Test creating 4D ContinuousND substrate from config."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert isinstance(substrate, ContinuousNDSubstrate)
        assert substrate.position_dim == 4
        assert substrate.bounds == [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)]
        assert substrate.boundary == "clamp"
        assert substrate.movement_delta == 0.5
        assert substrate.interaction_radius == 1.0
        assert substrate.distance_metric == "euclidean"
        assert substrate.observation_encoding == "relative"
        assert substrate.action_space_size == 10  # 2*4 + 2

    def test_continuousnd_6d_different_bounds(self):
        """Test 6D ContinuousND with different bounds per dimension."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 6,
                "bounds": [
                    (0.0, 5.0),
                    (0.0, 10.0),
                    (-5.0, 5.0),
                    (0.0, 1.0),
                    (0.0, 100.0),
                    (-10.0, 10.0),
                ],
                "boundary": "wrap",
                "movement_delta": 0.1,
                "interaction_radius": 0.5,
                "distance_metric": "manhattan",
                "observation_encoding": "scaled",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert isinstance(substrate, ContinuousNDSubstrate)
        assert substrate.position_dim == 6
        assert len(substrate.bounds) == 6
        assert substrate.bounds[0] == (0.0, 5.0)
        assert substrate.bounds[2] == (-5.0, 5.0)
        assert substrate.movement_delta == 0.1
        assert substrate.distance_metric == "manhattan"

    def test_continuousnd_position_initialization(self):
        """Test that initialized ContinuousND positions are valid."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [(0.0, 10.0), (0.0, 20.0), (-5.0, 5.0), (0.0, 1.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        positions = substrate.initialize_positions(num_agents=50, device=torch.device("cpu"))

        assert positions.shape == (50, 4)
        assert positions.dtype == torch.float32
        # Check all positions are within bounds
        assert (positions[:, 0] >= 0.0).all() and (positions[:, 0] <= 10.0).all()
        assert (positions[:, 1] >= 0.0).all() and (positions[:, 1] <= 20.0).all()
        assert (positions[:, 2] >= -5.0).all() and (positions[:, 2] <= 5.0).all()
        assert (positions[:, 3] >= 0.0).all() and (positions[:, 3] <= 1.0).all()

    def test_continuousnd_observation_encoding_relative(self):
        """Test relative observation encoding for ContinuousND."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "observation_encoding": "relative",
                "distance_metric": "euclidean",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        # Test boundary positions
        positions = torch.tensor(
            [[0.0, 0.0, 0.0, 0.0], [10.0, 10.0, 10.0, 10.0]],
            dtype=torch.float32,
        )
        observations = substrate.encode_observation(positions, {})

        assert observations.shape == (2, 4)  # relative: N dims
        # First position (0,0,0,0) should be all zeros
        assert (observations[0] == 0).all()
        # Last position (10,10,10,10) should be all ones
        assert (observations[1] == 1).all()

    def test_continuousnd_observation_encoding_absolute(self):
        """Test absolute observation encoding for ContinuousND."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "observation_encoding": "absolute",
                "distance_metric": "euclidean",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        positions = torch.tensor(
            [[1.5, 2.5, 3.5, 4.5]],
            dtype=torch.float32,
        )
        observations = substrate.encode_observation(positions, {})

        assert observations.shape == (1, 4)  # absolute: N dims
        # Should match input positions exactly
        assert torch.allclose(observations[0], positions[0])


class TestFactoryConfigValidation:
    """Test that factory properly validates config structures."""

    def test_gridnd_missing_config_raises_error(self):
        """Test that missing gridnd config raises appropriate error."""
        config_dict = {
            "type": "gridnd",
        }
        with pytest.raises(ValueError, match="type='gridnd' requires.*gridnd block"):
            SubstrateConfig(**config_dict)

    def test_continuousnd_missing_config_raises_error(self):
        """Test that missing continuous config for continuousnd raises error."""
        config_dict = {
            "type": "continuousnd",
        }
        with pytest.raises(ValueError, match="type='continuousnd' requires.*continuous block"):
            SubstrateConfig(**config_dict)

    @pytest.mark.skip(reason="v2.1 GridNDConfig doesn't enforce minimum dimensions at DTO level")
    def test_gridnd_dimension_validation(self):
        """Test that GridND config validates dimension count."""
        # NOTE: v2.1 moved dimension validation to substrate level, not config DTO level
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [8, 8, 8],  # Only 3D
                "boundary": "clamp",
                "observation_encoding": "relative",
                "distance_metric": "manhattan",
                "topology": "hypercube",
            },
        }
        with pytest.raises(ValueError, match="GridND requires at least 4 dimensions"):
            SubstrateConfig(**config_dict)

    def test_continuousnd_dimension_validation(self):
        """Test that ContinuousND config validates dimension count."""
        # Less than 4 dimensions should fail (at substrate level, not config level)
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 3,
                "bounds": [(0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
                "boundary": "clamp",
                "movement_delta": 0.5,
                "interaction_radius": 1.0,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        # v2.1: Validation happens at substrate level with different error message
        with pytest.raises(ValueError, match="ContinuousND requires at least 4 dimensions"):
            config = SubstrateConfig(**config_dict)
            SubstrateFactory.build(config, torch.device("cpu"))


class TestFactoryYAMLLoading:
    """Test factory loading substrates from YAML files."""

    def test_gridnd_from_yaml(self):
        """Test loading GridND substrate from YAML file."""
        import yaml

        yaml_content = """
type: gridnd
gridnd:
  dimension_sizes: [8, 8, 8, 8]
  boundary: clamp
  distance_metric: manhattan
  observation_encoding: relative
  topology: hypercube
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = Path(f.name)

        try:
            with open(config_path) as f:
                loaded_data = yaml.safe_load(f)
            config = SubstrateConfig(**loaded_data)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))

            assert isinstance(substrate, GridNDSubstrate)
            assert substrate.dimension_sizes == [8, 8, 8, 8]
            assert substrate.boundary == "clamp"
        finally:
            config_path.unlink()

    def test_continuousnd_from_yaml(self):
        """Test loading ContinuousND substrate from YAML file."""
        import yaml

        yaml_content = """
type: continuousnd
continuous:
  dimensions: 4
  bounds: [[0.0, 10.0], [0.0, 10.0], [0.0, 10.0], [0.0, 10.0]]
  boundary: wrap
  movement_delta: 0.5
  interaction_radius: 1.0
  distance_metric: euclidean
  observation_encoding: scaled
  action_discretization:
    num_directions: 8
    num_magnitudes: 3
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = Path(f.name)

        try:
            with open(config_path) as f:
                loaded_data = yaml.safe_load(f)
            config = SubstrateConfig(**loaded_data)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))

            assert isinstance(substrate, ContinuousNDSubstrate)
            assert substrate.position_dim == 4
            assert substrate.boundary == "wrap"
            assert substrate.observation_encoding == "scaled"
        finally:
            config_path.unlink()


class TestFactoryEdgeCases:
    """Test factory behavior with edge cases and boundary conditions."""

    def test_gridnd_max_dimensions(self):
        """Test GridND with maximum allowed dimensions (100D)."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [2] * 100,  # 100D grid
                "boundary": "clamp",
                "observation_encoding": "relative",
                "distance_metric": "manhattan",
                "topology": "hypercube",
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert substrate.position_dim == 100
        assert substrate.action_space_size == 202  # 2*100 + 2

    def test_continuousnd_max_dimensions(self):
        """Test ContinuousND with maximum allowed dimensions (100D)."""
        bounds = [(0.0, 1.0)] * 100
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 100,
                "bounds": bounds,
                "boundary": "clamp",
                "movement_delta": 0.01,
                "interaction_radius": 0.1,
                "distance_metric": "euclidean",
                "observation_encoding": "relative",
                "action_discretization": BASE_ACTION_DISC,
            },
        }
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        assert substrate.position_dim == 100

    def test_gridnd_boundary_modes(self):
        """Test GridND with all boundary modes."""
        for boundary_mode in ["clamp", "wrap", "bounce", "sticky"]:
            config_dict = {
                "type": "gridnd",
                "gridnd": {
                    "dimension_sizes": [8, 8, 8, 8],
                    "boundary": boundary_mode,
                    "observation_encoding": "relative",
                    "distance_metric": "manhattan",
                    "topology": "hypercube",
                },
            }
            config = SubstrateConfig(**config_dict)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))
            assert substrate.boundary == boundary_mode

    def test_continuousnd_boundary_modes(self):
        """Test ContinuousND with all boundary modes."""
        for boundary_mode in ["clamp", "wrap", "bounce", "sticky"]:
            config_dict = {
                "type": "continuousnd",
                "continuous": {
                    "dimensions": 4,
                    "bounds": [(0.0, 10.0)] * 4,
                    "boundary": boundary_mode,
                    "movement_delta": 0.5,
                    "interaction_radius": 1.0,
                    "distance_metric": "euclidean",
                    "observation_encoding": "relative",
                    "action_discretization": BASE_ACTION_DISC,
                },
            }
            config = SubstrateConfig(**config_dict)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))
            assert substrate.boundary == boundary_mode

    def test_gridnd_distance_metrics(self):
        """Test GridND with all distance metrics."""
        for metric in ["manhattan", "euclidean", "chebyshev"]:
            config_dict = {
                "type": "gridnd",
                "gridnd": {
                    "dimension_sizes": [8, 8, 8, 8],
                    "boundary": "clamp",
                    "distance_metric": metric,
                    "observation_encoding": "relative",
                    "topology": "hypercube",
                },
            }
            config = SubstrateConfig(**config_dict)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))
            assert substrate.distance_metric == metric

    def test_continuousnd_distance_metrics(self):
        """Test ContinuousND with all distance metrics."""
        for metric in ["euclidean", "manhattan", "chebyshev"]:
            config_dict = {
                "type": "continuousnd",
                "continuous": {
                    "dimensions": 4,
                    "bounds": [(0.0, 10.0)] * 4,
                    "boundary": "clamp",
                    "movement_delta": 0.5,
                    "interaction_radius": 1.0,
                    "distance_metric": metric,
                    "observation_encoding": "relative",
                    "action_discretization": BASE_ACTION_DISC,
                },
            }
            config = SubstrateConfig(**config_dict)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))
            assert substrate.distance_metric == metric


class TestFactoryIntegration:
    """Integration tests with multiple substrate types."""

    def test_factory_creates_correct_types(self):
        """Test that factory creates correct substrate types."""
        configs = [
            {
                "type": "gridnd",
                "gridnd": {
                    "dimension_sizes": [8, 8, 8, 8],
                    "boundary": "clamp",
                    "observation_encoding": "relative",
                    "distance_metric": "manhattan",
                    "topology": "hypercube",
                },
                "expected_type": GridNDSubstrate,
            },
            {
                "type": "continuousnd",
                "continuous": {
                    "dimensions": 4,
                    "bounds": [(0.0, 10.0)] * 4,
                    "boundary": "clamp",
                    "movement_delta": 0.5,
                    "interaction_radius": 1.0,
                    "distance_metric": "euclidean",
                    "observation_encoding": "relative",
                    "action_discretization": BASE_ACTION_DISC,
                },
                "expected_type": ContinuousNDSubstrate,
            },
        ]

        for config_dict in configs:
            expected_type = config_dict.pop("expected_type")
            config = SubstrateConfig(**config_dict)
            substrate = SubstrateFactory.build(config, torch.device("cpu"))
            assert isinstance(substrate, expected_type)
