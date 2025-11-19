"""Integration tests for substrate migration (Grid2D → Grid3D → Continuous)."""

import torch

from tests.test_townlet.utils.builders import make_grid3d_substrate

ACTION_DISC = {"num_directions": 8, "num_magnitudes": 3}


def test_training_with_grid3d_substrate(tmp_path):
    """Training runs with 3D cubic grid."""
    # Create Grid3D substrate programmatically (no config files needed)
    substrate = make_grid3d_substrate(
        width=5,
        height=5,
        depth=3,
        boundary="clamp",
        distance_metric="manhattan",
        observation_encoding="relative",
    )

    # Verify Grid3D substrate properties
    assert substrate.position_dim == 3
    assert substrate.action_space_size == 11  # cardinal + diagonals defined by Grid3D defaults

    # Verify substrate can generate random positions
    num_agents = 10
    device = torch.device("cpu")
    positions = substrate.initialize_positions(num_agents, device)

    # Verify 3D positions
    assert positions.shape == (num_agents, 3)
    assert positions.dtype == torch.long

    # Verify all dimensions in bounds
    assert (positions[:, 0] >= 0).all() and (positions[:, 0] < 5).all()  # X (width)
    assert (positions[:, 1] >= 0).all() and (positions[:, 1] < 5).all()  # Y (height)
    assert (positions[:, 2] >= 0).all() and (positions[:, 2] < 3).all()  # Z (depth)

    # Verify boundary clamping
    edge_positions = torch.tensor([[4, 4, 2]], dtype=torch.long)  # At edge
    # Try to move +X (action 0: EAST) - should clamp at boundary
    movement_deltas = torch.tensor([[1, 0, 0]], dtype=torch.long)
    new_pos = substrate.apply_movement(edge_positions, movement_deltas)
    assert new_pos[0, 0] == 4  # Should stay clamped at width-1

    # Verify UP/DOWN movement (Z axis)
    center_pos = torch.tensor([[2, 2, 1]], dtype=torch.long)
    # Move UP (+Z)
    up_delta = torch.tensor([[0, 0, 1]], dtype=torch.long)
    new_pos = substrate.apply_movement(center_pos, up_delta)
    assert new_pos[0, 2] == 2  # Z should increase

    # Move DOWN (-Z)
    down_delta = torch.tensor([[0, 0, -1]], dtype=torch.long)
    new_pos = substrate.apply_movement(center_pos, down_delta)
    assert new_pos[0, 2] == 0  # Z should decrease


def test_continuous_proximity_interaction(tmp_path):
    """Verify proximity-based interaction works in continuous space."""
    from townlet.substrate.continuous import Continuous2DSubstrate

    # Create continuous substrate directly
    substrate = Continuous2DSubstrate(
        min_x=0.0,
        max_x=10.0,
        min_y=0.0,
        max_y=10.0,
        boundary="clamp",
        movement_delta=0.5,
        interaction_radius=0.8,
        action_discretization=ACTION_DISC,
        distance_metric="euclidean",
        observation_encoding="relative",
    )

    # Place agent and affordance close together
    agent_pos = torch.tensor([[5.0, 5.0]], dtype=torch.float32)
    affordance_pos = torch.tensor([[5.5, 5.5]], dtype=torch.float32)

    # Check proximity interaction
    # Distance = sqrt((5.5-5.0)^2 + (5.5-5.0)^2) = sqrt(0.5) ≈ 0.707 < 0.8
    on_affordance = substrate.is_on_position(agent_pos, affordance_pos)

    assert on_affordance[0], "Agent should be within interaction radius"

    # Now move affordance outside interaction radius
    affordance_pos_far = torch.tensor([[7.0, 7.0]], dtype=torch.float32)
    on_affordance_far = substrate.is_on_position(agent_pos, affordance_pos_far)

    assert not on_affordance_far[0], "Agent should be outside interaction radius"
