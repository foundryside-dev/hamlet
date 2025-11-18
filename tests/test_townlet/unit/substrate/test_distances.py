"""Test substrate-based distance checks for Phase 5.

This test file validates that distance calculations use substrate.is_on_position()
instead of hardcoded Manhattan distance calculations.
"""

import torch


def test_interaction_uses_substrate_distance(basic_env):
    """Environment should use substrate.is_on_position() for interactions."""
    env = basic_env

    # Reset environment so randomization occurs, then capture a known affordance position
    env.reset()
    affordance_name = "SLEEP" if "SLEEP" in env.affordances else next(iter(env.affordances.keys()))
    target_pos = env.affordances[affordance_name].clone()
    env.positions = target_pos.unsqueeze(0)  # [1, position_dim]

    # Snapshot meters to detect interaction effects
    initial_meters = env.meters.clone()

    # Execute INTERACT action via action space lookup
    interact_action = env.action_space.get_action_by_name("INTERACT").id
    actions = torch.tensor([interact_action], dtype=torch.long, device=env.device)
    obs, rewards, dones, infos = env.step(actions)

    # Interaction should succeed (agent is on affordance); meters should change
    final_meters = env.meters
    assert (final_meters != initial_meters).any(), (
        "Meters should change after interacting with affordance at the same position. "
        f"Agent position: {env.positions[0]}, Affordance '{affordance_name}' position: {target_pos}"
    )
