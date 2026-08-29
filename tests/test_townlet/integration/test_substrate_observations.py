"""Test observation encoding uses substrate methods."""


def test_observation_dim_matches_actual_observation(cpu_env_factory, test_config_pack_path):
    """Environment's observation_dim should match actual observation shape."""
    env = cpu_env_factory(config_dir=test_config_pack_path, num_agents=1)

    obs = env.reset()

    # Observation dimension should match actual observation
    assert obs.shape[1] == env.observation_dim, f"observation_dim={env.observation_dim} doesn't match actual obs.shape[1]={obs.shape[1]}"


def test_partial_observation_dim_matches_actual(cpu_env_factory, test_config_pack_path):
    """POMDP observation_dim should match actual observation shape."""
    env = cpu_env_factory(config_dir=test_config_pack_path, num_agents=1)

    obs = env.reset()

    # Observation dimension should match actual observation
    assert obs.shape[1] == env.observation_dim, f"observation_dim={env.observation_dim} doesn't match actual obs.shape[1]={obs.shape[1]}"
