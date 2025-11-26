"""Tests for custom action meter validation (ENV-006) in VectorizedHamletEnv."""

import pytest
import torch

from townlet.environment.action_config import ActionConfig


def _make_custom_action(name: str, costs: dict, effects: dict) -> ActionConfig:
    """Create a custom action config for testing.

    Args:
        name: Action name (used as id context)
        costs: Cost dict {meter_name: amount}
        effects: Effect dict {meter_name: amount}

    Returns:
        ActionConfig with all required fields set
    """
    return ActionConfig(
        id=99,  # High ID to avoid collision with substrate actions
        name=name,
        type="passive",  # Passive type doesn't require delta
        costs=costs,
        effects=effects,
        delta=None,
        teleport_to=None,
        enabled=True,
        description=f"Test action {name}",
        icon=None,
        source="custom",
        source_affordance=None,
    )


class TestCustomActionMeterValidation:
    """Test that custom action costs/effects validate meter names."""

    def test_get_meter_index_raises_on_unknown_meter(self, config_pack_factory):
        """_get_meter_index should raise KeyError with helpful message for unknown meters (ENV-006).

        This prevents silent failures when custom actions reference typos in meter names.
        """
        from tests.test_townlet.utils.builders import make_vectorized_env_from_pack

        config_dir = config_pack_factory(name="meter_validation")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Direct test of _get_meter_index with invalid meter
        with pytest.raises(KeyError) as exc_info:
            env._get_meter_index("invalid_meter", context="test action")

        error_msg = str(exc_info.value)
        # Error should include the invalid meter name
        assert "invalid_meter" in error_msg
        # Error should include context
        assert "test action" in error_msg
        # Error should list available meters
        assert "energy" in error_msg.lower()

    def test_apply_custom_action_raises_on_invalid_cost_meter(self, config_pack_factory):
        """_apply_custom_action should raise KeyError for invalid cost meters (ENV-006).

        Previously this would silently skip, hiding config errors.
        """
        from tests.test_townlet.utils.builders import make_vectorized_env_from_pack

        config_dir = config_pack_factory(name="action_cost_validation")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Create action with invalid meter name (typo)
        invalid_action = _make_custom_action(
            name="test_invalid",
            costs={"enregy": 0.1},  # Typo: "enregy" instead of "energy"
            effects={},
        )

        # Should raise KeyError with helpful message
        with pytest.raises(KeyError) as exc_info:
            env._apply_custom_action(0, invalid_action)

        error_msg = str(exc_info.value)
        # Error should include the invalid meter name
        assert "enregy" in error_msg
        # Error should include action context
        assert "test_invalid" in error_msg
        assert "costs" in error_msg
        # Error should list available meters
        assert "energy" in error_msg.lower()

    def test_apply_custom_action_raises_on_invalid_effect_meter(self, config_pack_factory):
        """_apply_custom_action should raise KeyError for invalid effect meters (ENV-006)."""
        from tests.test_townlet.utils.builders import make_vectorized_env_from_pack

        config_dir = config_pack_factory(name="action_effect_validation")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Create action with invalid effect meter name
        invalid_action = _make_custom_action(
            name="test_invalid_effect",
            costs={},
            effects={"moud": 0.2},  # Typo: "moud" instead of "mood"
        )

        # Should raise KeyError with helpful message
        with pytest.raises(KeyError) as exc_info:
            env._apply_custom_action(0, invalid_action)

        error_msg = str(exc_info.value)
        # Error should include the invalid meter name
        assert "moud" in error_msg
        # Error should include action context
        assert "test_invalid_effect" in error_msg
        assert "effects" in error_msg

    def test_apply_custom_action_succeeds_with_valid_meters(self, config_pack_factory):
        """_apply_custom_action should work normally with valid meter names."""
        from tests.test_townlet.utils.builders import make_vectorized_env_from_pack

        config_dir = config_pack_factory(name="valid_action_meters")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # Get energy index and set initial value so we can test decrease
        energy_idx = env._get_meter_index("energy")
        env.meters[0, energy_idx] = 0.5  # Set to 50% so we can observe decrease
        initial_energy = env.meters[0, energy_idx].item()

        # Create valid action with restoration (negative cost = add energy)
        valid_action = _make_custom_action(
            name="test_valid",
            costs={"energy": -0.2},  # Negative cost = restoration
            effects={},
        )

        # Should succeed without error
        env._apply_custom_action(0, valid_action)

        # Verify meter was updated (negative cost means energy increases)
        new_energy = env.meters[0, energy_idx].item()
        assert new_energy > initial_energy, "Energy should have increased from negative cost (restoration)"
        assert abs(new_energy - 0.7) < 0.01, f"Expected 0.7, got {new_energy}"
