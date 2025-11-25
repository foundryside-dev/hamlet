"""Tests for hours_per_day division guard (ENV-003) in VectorizedHamletEnv."""

import torch

from tests.test_townlet.utils.builders import make_vectorized_env_from_pack


class TestHoursPerDayGuard:
    """Test hours_per_day is always positive to prevent division by zero."""

    def test_hours_per_day_is_positive(self, config_pack_factory):
        """hours_per_day should always be positive to prevent division by zero.

        This is a safety guard - we should never get division by zero errors
        when computing hour_idx = active_hour % hours_per_day.
        """
        config_dir = config_pack_factory(name="minimal")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # hours_per_day should be positive
        assert env.hours_per_day > 0, f"hours_per_day must be > 0, got {env.hours_per_day}"

    def test_hours_per_day_at_least_one(self, config_pack_factory):
        """hours_per_day should be at least 1 to allow safe modulo.

        The calculation `active_hour % hours_per_day` requires hours_per_day >= 1.
        """
        config_dir = config_pack_factory(name="guard_test")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # hours_per_day should be at least 1
        assert env.hours_per_day >= 1, f"hours_per_day must be >= 1, got {env.hours_per_day}"

        # Verify no division by zero in hour_idx calculation
        # Simulates what happens in _get_action_mask_for_hour
        for active_hour in [0, 1, 10, 100, 1000]:
            hour_idx = active_hour % env.hours_per_day
            assert 0 <= hour_idx < env.hours_per_day, f"Invalid hour_idx={hour_idx} for active_hour={active_hour}"

    def test_hour_idx_modulo_never_raises(self, config_pack_factory):
        """Verify hour_idx calculation using modulo never causes errors.

        This test ensures the fix (max(1, ...)) prevents division by zero.
        """
        config_dir = config_pack_factory(name="modulo_test")

        env = make_vectorized_env_from_pack(
            config_dir,
            level_name="L0_test",
            num_agents=1,
            device=torch.device("cpu"),
        )

        # This should not raise ZeroDivisionError
        active_hour = 0
        hour_idx = active_hour % env.hours_per_day
        assert isinstance(hour_idx, int)
