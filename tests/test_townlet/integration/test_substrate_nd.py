"""Integration tests for GridND and ContinuousND with full system.

Tests verify that N-dimensional substrates work end-to-end with:
- Configuration loading and factory
- VectorizedHamletEnv
- Affordance interactions
- Action space handling

Note: ObservationBuilder was removed in VFS integration.
"""

import torch

from townlet.config.stratum_config import SubstrateConfig
from townlet.substrate.continuousnd import ContinuousNDSubstrate
from townlet.substrate.factory import SubstrateFactory
from townlet.substrate.gridnd import GridNDSubstrate

BASE_ACTION_DISC = {"num_directions": 8, "num_magnitudes": 3}


class TestNDSubstrateInteroperability:
    """Test that N-D substrates interoperate with existing system components."""

    def test_gridnd_with_multiple_affordances(self):
        """Test GridND with multiple affordances at different positions."""
        substrate = GridNDSubstrate(
            dimension_sizes=[6, 6, 6, 6],
            boundary="clamp",
            distance_metric="manhattan",
            observation_encoding="relative",
        )

        affordances = {
            "Bed": torch.tensor([1, 1, 1, 1], dtype=torch.long),
            "Hospital": torch.tensor([3, 3, 3, 3], dtype=torch.long),
            "Job": torch.tensor([5, 5, 5, 5], dtype=torch.long),
            "Store": torch.tensor([2, 2, 2, 2], dtype=torch.long),
        }

        agents = torch.tensor(
            [[1, 1, 1, 1], [3, 3, 3, 3], [5, 5, 5, 5], [0, 0, 0, 0]],
            dtype=torch.long,
        )

        # Check each agent's affordance
        for idx, agent_pos in enumerate(agents):
            for aff_name, aff_pos in affordances.items():
                on_affordance = substrate.is_on_position(agent_pos.unsqueeze(0), aff_pos)
                if idx == 0:
                    assert on_affordance[0] == (aff_name == "Bed")
                elif idx == 1:
                    assert on_affordance[0] == (aff_name == "Hospital")
                elif idx == 2:
                    assert on_affordance[0] == (aff_name == "Job")
                else:
                    assert not on_affordance[0]

    def test_continuousnd_with_multiple_affordances(self):
        """Test ContinuousND with multiple affordances at different positions."""
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=0.5,
            distance_metric="euclidean",
            observation_encoding="relative",
        )

        affordances = {
            "Bed": torch.tensor([1.0, 1.0, 1.0, 1.0], dtype=torch.float32),
            "Hospital": torch.tensor([5.0, 5.0, 5.0, 5.0], dtype=torch.float32),
            "Job": torch.tensor([9.0, 9.0, 9.0, 9.0], dtype=torch.float32),
            "Store": torch.tensor([5.0, 1.0, 5.0, 1.0], dtype=torch.float32),
        }

        agents = torch.tensor(
            [
                [1.0, 1.0, 1.0, 1.0],  # On Bed
                [5.0, 5.0, 5.0, 5.0],  # On Hospital
                [9.0, 9.0, 9.0, 9.0],  # On Job
                [0.0, 0.0, 0.0, 0.0],  # On none
            ],
            dtype=torch.float32,
        )

        # Check each agent's affordances
        for idx, agent_pos in enumerate(agents):
            for aff_name, aff_pos in affordances.items():
                on_affordance = substrate.is_on_position(agent_pos.unsqueeze(0), aff_pos)
                if idx == 0:
                    assert on_affordance[0] == (aff_name == "Bed")
                elif idx == 1:
                    # Agent at [5, 5, 5, 5] is only on Hospital
                    # Distance to Hospital: 0
                    # Distance to Store [5, 1, 5, 1]: sqrt((5-5)^2 + (5-1)^2 + (5-5)^2 + (5-1)^2) = sqrt(32) > 0.5
                    assert on_affordance[0] == (aff_name == "Hospital")
                elif idx == 2:
                    assert on_affordance[0] == (aff_name == "Job")
                else:
                    assert not on_affordance[0]

    def test_gridnd_batch_operations(self):
        """Test GridND handles batch operations correctly."""
        substrate = GridNDSubstrate(
            dimension_sizes=[5, 5, 5, 5],
            boundary="clamp",
            distance_metric="manhattan",
            observation_encoding="relative",
        )

        # Batch of 10 agent positions
        positions = substrate.initialize_positions(num_agents=10, device=torch.device("cpu"))

        assert positions.shape == (10, 4)
        assert positions.dtype == torch.long
        assert torch.all(positions >= 0) and torch.all(positions < 5)

        # Apply movement to batch
        deltas = torch.randn((10, 4), dtype=torch.float32)
        new_positions = substrate.apply_movement(positions, deltas)

        assert new_positions.shape == (10, 4)
        assert torch.all(new_positions >= 0) and torch.all(new_positions < 5)

    def test_continuousnd_batch_operations(self):
        """Test ContinuousND handles batch operations correctly."""
        substrate = ContinuousNDSubstrate(
            bounds=[(0.0, 10.0), (0.0, 10.0), (0.0, 10.0), (0.0, 10.0)],
            boundary="clamp",
            movement_delta=0.5,
            interaction_radius=1.0,
            distance_metric="euclidean",
            observation_encoding="relative",
        )

        # Batch of 10 agent positions
        positions = substrate.initialize_positions(num_agents=10, device=torch.device("cpu"))

        assert positions.shape == (10, 4)
        assert positions.dtype == torch.float32

        # Apply movement to batch
        deltas = torch.randn((10, 4), dtype=torch.float32) * 0.5
        new_positions = substrate.apply_movement(positions, deltas)

        assert new_positions.shape == (10, 4)
        assert torch.all(new_positions >= 0.0) and torch.all(new_positions <= 10.0)

    def test_gridnd_distance_metrics_consistency(self):
        """Test that different distance metrics work consistently."""
        dimension_sizes = [8, 8, 8, 8]

        substrates = {
            "manhattan": GridNDSubstrate(
                dimension_sizes=dimension_sizes,
                boundary="clamp",
                distance_metric="manhattan",
                observation_encoding="relative",
            ),
            "euclidean": GridNDSubstrate(
                dimension_sizes=dimension_sizes,
                boundary="clamp",
                distance_metric="euclidean",
                observation_encoding="relative",
            ),
            "chebyshev": GridNDSubstrate(
                dimension_sizes=dimension_sizes,
                boundary="clamp",
                distance_metric="chebyshev",
                observation_encoding="relative",
            ),
        }

        pos1 = torch.tensor([[0, 0, 0, 0]], dtype=torch.long)
        pos2 = torch.tensor([[2, 3, 4, 5]], dtype=torch.long)

        distances = {name: substrate.compute_distance(pos1, pos2) for name, substrate in substrates.items()}

        # Manhattan: |2| + |3| + |4| + |5| = 14
        assert distances["manhattan"][0] == 14

        # Euclidean: sqrt(4 + 9 + 16 + 25) = sqrt(54) ≈ 7.35
        assert torch.allclose(distances["euclidean"], torch.tensor([7.35], dtype=torch.float32), atol=0.1)

        # Chebyshev: max(2, 3, 4, 5) = 5
        assert distances["chebyshev"][0] == 5

    def test_continuousnd_distance_metrics_consistency(self):
        """Test that different distance metrics work consistently in continuous space."""
        bounds = [(0.0, 10.0)] * 4

        substrates = {
            "manhattan": ContinuousNDSubstrate(
                bounds=bounds,
                boundary="clamp",
                movement_delta=0.5,
                interaction_radius=1.0,
                distance_metric="manhattan",
                observation_encoding="relative",
            ),
            "euclidean": ContinuousNDSubstrate(
                bounds=bounds,
                boundary="clamp",
                movement_delta=0.5,
                interaction_radius=1.0,
                distance_metric="euclidean",
                observation_encoding="relative",
            ),
            "chebyshev": ContinuousNDSubstrate(
                bounds=bounds,
                boundary="clamp",
                movement_delta=0.5,
                interaction_radius=1.0,
                distance_metric="chebyshev",
                observation_encoding="relative",
            ),
        }

        pos1 = torch.tensor([[0.0, 0.0, 0.0, 0.0]], dtype=torch.float32)
        pos2 = torch.tensor([[2.0, 3.0, 4.0, 5.0]], dtype=torch.float32)

        distances = {name: substrate.compute_distance(pos1, pos2) for name, substrate in substrates.items()}

        # Manhattan: |2| + |3| + |4| + |5| = 14.0
        assert torch.allclose(distances["manhattan"], torch.tensor([14.0]))

        # Euclidean: sqrt(4 + 9 + 16 + 25) = sqrt(54) ≈ 7.35
        assert torch.allclose(distances["euclidean"], torch.tensor([7.35], dtype=torch.float32), atol=0.1)

        # Chebyshev: max(2, 3, 4, 5) = 5.0
        assert torch.allclose(distances["chebyshev"], torch.tensor([5.0]))


class TestNDSubstrateConfigRoundtrip:
    """Test that N-D substrate configs can be saved and loaded."""

    def test_gridnd_yaml_config_roundtrip(self):
        """Test creating GridND from config dict simulates YAML loading."""
        config_dict = {
            "type": "gridnd",
            "gridnd": {
                "dimension_sizes": [6, 7, 8, 9],
                "boundary": "wrap",
                "distance_metric": "euclidean",
                "observation_encoding": "scaled",
                "topology": "hypercube",
            },
        }

        # Create substrate from config
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        # Verify all properties preserved
        assert substrate.dimension_sizes == [6, 7, 8, 9]
        assert substrate.boundary == "wrap"
        assert substrate.distance_metric == "euclidean"
        assert substrate.observation_encoding == "scaled"

    def test_continuousnd_yaml_config_roundtrip(self):
        """Test creating ContinuousND from config dict simulates YAML loading."""
        config_dict = {
            "type": "continuousnd",
            "continuous": {
                "dimensions": 4,
                "bounds": [(0.0, 100.0), (-50.0, 50.0), (10.0, 20.0), (-10.0, 30.0)],
                "boundary": "bounce",
                "movement_delta": 2.0,
                "interaction_radius": 3.5,
                "distance_metric": "chebyshev",
                "observation_encoding": "absolute",
                "action_discretization": BASE_ACTION_DISC,
            },
        }

        # Create substrate from config
        config = SubstrateConfig(**config_dict)
        substrate = SubstrateFactory.build(config, torch.device("cpu"))

        # Verify all properties preserved
        assert substrate.bounds == [(0.0, 100.0), (-50.0, 50.0), (10.0, 20.0), (-10.0, 30.0)]
        assert substrate.boundary == "bounce"
        assert substrate.movement_delta == 2.0
        assert substrate.interaction_radius == 3.5
        assert substrate.distance_metric == "chebyshev"
        assert substrate.observation_encoding == "absolute"
