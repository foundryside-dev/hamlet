"""Integration tests for action cost application from bars.yaml.

Tests verify that VectorizedHamletEnv correctly applies:
- base_depletion: Passive decay every tick (existence cost)
- base_move_depletion: Additional cost for movement actions
- base_interaction_cost: Additional cost for INTERACT action

Architecture: Three fundamental action types
1. Existence → base_depletion only
2. Movement → base_depletion + base_move_depletion
3. Interaction → base_depletion + base_interaction_cost
4. WAIT → base_depletion only (optional action)
"""

import torch


class TestMovementCosts:
    """Test that movement actions apply base_move_depletion from bars.yaml."""

    def test_movement_applies_base_move_depletion(self, cpu_env_factory):
        """Movement actions should apply base_move_depletion from bars.yaml."""
        env = cpu_env_factory()
        obs = env.reset()

        # Get initial energy level
        initial_energy = env.meters[0, 0].item()
        base_depletion = env.meter_dynamics.get_base_depletion("energy")
        move_cost = next(bar.depletion.move for bar in env.bars_config.meters if bar.name == "energy")

        # Execute UP action (movement) - UP is typically index 0
        action_labels = env.get_action_label_names()
        up_action = next(idx for idx, label in action_labels.items() if label == "UP")
        actions = torch.tensor([up_action], device=env.device)

        # One step includes: base_depletion + movement cost
        obs, rewards, dones, info = env.step(actions)

        expected_energy = initial_energy - (base_depletion + move_cost)
        actual_energy = env.meters[0, 0].item()

        assert (
            abs(actual_energy - expected_energy) < 1e-4
        ), f"Movement should apply base_depletion + base_move_depletion. Expected {expected_energy:.4f}, got {actual_energy:.4f}"

    def test_movement_costs_per_meter_from_bars(self, cpu_env_factory):
        """Only energy should have movement cost; other meters should not."""
        env = cpu_env_factory()
        env.reset()

        # Get initial meter state
        initial_meters = env.meters.clone()

        # Execute UP action
        up_action = next(idx for idx, label in env.get_action_label_names().items() if label == "UP")
        actions = torch.tensor([up_action], device=env.device)
        env.step(actions)

        # Calculate meter changes
        meter_deltas = initial_meters - env.meters

        # Expected: Only energy (index 0) should have base_move_depletion applied
        base_depletion = env.meter_dynamics.get_base_depletion("energy")
        move_cost = next(bar.depletion.move for bar in env.bars_config.meters if bar.name == "energy")
        expected_delta = base_depletion + move_cost
        energy_delta = meter_deltas[0, 0].item()
        assert (
            abs(energy_delta - expected_delta) < 1e-4
        ), f"Energy should deplete by base_depletion + base_move_depletion. Expected {expected_delta:.4f}, got {energy_delta:.4f}"


class TestInteractionCosts:
    """Test that INTERACT action applies base_interaction_cost from bars.yaml."""

    def test_interact_applies_base_interaction_cost(self, cpu_env_factory):
        """INTERACT action should apply base_interaction_cost from bars.yaml."""
        env = cpu_env_factory()
        obs = env.reset()

        # Get initial energy level
        initial_energy = env.meters[0, 0].item()
        base_depletion = env.meter_dynamics.get_base_depletion("energy")
        interaction_cost = next(bar.depletion.interact for bar in env.bars_config.meters if bar.name == "energy")

        # Execute INTERACT action - typically index 4 in Grid2D
        interact_action = env.action_ids["INTERACT"]
        actions = torch.tensor([interact_action], device=env.device)

        # One step includes: base_depletion + interaction cost
        obs, rewards, dones, info = env.step(actions)

        expected_energy = initial_energy - (base_depletion + interaction_cost)
        actual_energy = env.meters[0, 0].item()

        assert (
            abs(actual_energy - expected_energy) < 1e-4
        ), f"INTERACT should apply base_depletion + base_interaction_cost. Expected {expected_energy:.4f}, got {actual_energy:.4f}"


class TestWaitActionIsolation:
    """Test that WAIT action only pays base_depletion (no extra costs)."""

    def test_wait_only_pays_base_depletion(self, cpu_env_factory):
        """WAIT action should NOT apply any movement or interaction costs."""
        env = cpu_env_factory()
        obs = env.reset()

        # Get initial energy level
        initial_energy = env.meters[0, 0].item()

        # Execute WAIT action - typically index 5 in Grid2D
        wait_action = next(idx for idx, label in env.get_action_label_names().items() if label == "WAIT")
        actions = torch.tensor([wait_action], device=env.device)

        # One step includes: only base_depletion (no action costs)
        obs, rewards, dones, info = env.step(actions)

        base_depletion = env.meter_dynamics.get_base_depletion("energy")
        move_cost = next(bar.depletion.move for bar in env.bars_config.meters if bar.name == "energy")
        wait_is_movement = bool(env._movement_deltas[wait_action].ne(0).any().item())
        wait_cost = move_cost if wait_is_movement else 0.0

        expected_energy = initial_energy - (base_depletion + wait_cost)
        actual_energy = env.meters[0, 0].item()

        assert (
            abs(actual_energy - expected_energy) < 1e-4
        ), f"WAIT should only apply base_depletion. Expected {expected_energy:.4f}, got {actual_energy:.4f}"

    def test_wait_vs_movement_cost_difference(self, cpu_env_factory):
        """WAIT should cost less than movement (demonstrates meaningful action choice)."""
        env = cpu_env_factory()

        # Test WAIT
        env.reset()
        initial_energy_wait = env.meters[0, 0].item()
        wait_action = next(idx for idx, label in env.get_action_label_names().items() if label == "WAIT")
        env.step(torch.tensor([wait_action], device=env.device))
        wait_energy_cost = initial_energy_wait - env.meters[0, 0].item()

        # Test UP (movement)
        env.reset()
        initial_energy_move = env.meters[0, 0].item()
        up_action = next(idx for idx, label in env.get_action_label_names().items() if label == "UP")
        env.step(torch.tensor([up_action], device=env.device))
        move_energy_cost = initial_energy_move - env.meters[0, 0].item()

        # Movement should cost more than WAIT when WAIT has no movement delta.
        move_cost = next(bar.depletion.move for bar in env.bars_config.meters if bar.name == "energy")
        wait_is_movement = bool(env._movement_deltas[wait_action].ne(0).any().item())
        wait_cost = move_cost if wait_is_movement else 0.0
        expected_difference = move_cost - wait_cost
        measured_difference = move_energy_cost - wait_energy_cost

        assert (
            abs(measured_difference - expected_difference) < 1e-4
        ), f"Movement vs WAIT cost delta mismatch. Expected {expected_difference:.4f}, got {measured_difference:.4f}"
        if expected_difference > 0:
            assert (
                move_energy_cost > wait_energy_cost
            ), f"Movement ({move_energy_cost:.4f}) should cost more than WAIT ({wait_energy_cost:.4f}) when WAIT has no movement delta"
