"""Test ObservationActivity exposure in VectorizedHamletEnv (v2.1 configs)."""


class TestEnvironmentObservationActivity:
    def test_env_exposes_observation_activity(self, env_factory, cpu_device, test_config_pack_path):
        """VectorizedHamletEnv should expose observation_activity from runtime."""
        env = env_factory(
            config_dir=test_config_pack_path,
            level_name="L0_5_dual_resource",
            num_agents=4,
            device_override=cpu_device,
        )

        assert hasattr(env, "observation_activity")
        assert env.observation_activity is not None

    def test_env_observation_activity_matches_runtime(self, env_factory, cpu_device, compile_universe, test_config_pack_path):
        """Environment's observation_activity should match compiled LevelMetadata."""
        compiled = compile_universe(test_config_pack_path)
        level_meta = compiled.get_level("L0_0_minimal")

        env = env_factory(
            config_dir=test_config_pack_path,
            level_name="L0_0_minimal",
            num_agents=4,
            device_override=cpu_device,
        )

        assert env.observation_activity is level_meta.observation_activity

    def test_env_observation_activity_has_valid_mask(self, env_factory, cpu_device, test_config_pack_path):
        """Environment's observation_activity should have valid active_mask."""
        env = env_factory(
            config_dir=test_config_pack_path,
            level_name="L0_5_dual_resource",
            num_agents=4,
            device_override=cpu_device,
        )

        # active_mask length should match observation_dim
        assert len(env.observation_activity.active_mask) == env.observation_dim

    def test_env_observation_activity_has_group_slices(self, env_factory, cpu_device, test_config_pack_path):
        """Environment's observation_activity should have semantic group slices."""
        env = env_factory(
            config_dir=test_config_pack_path,
            level_name="L0_5_dual_resource",
            num_agents=4,
            device_override=cpu_device,
        )

        # Should have at least spatial and bars groups
        assert env.observation_activity.get_group_slice("spatial") is not None
        assert env.observation_activity.get_group_slice("bars") is not None
        assert len(env.observation_activity.group_slices) >= 2
