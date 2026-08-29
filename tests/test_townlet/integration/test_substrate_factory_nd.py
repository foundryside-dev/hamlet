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
