"""Integration tests for DACEngine in the current v2.1 config pack."""

import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv

LEVEL_NAME = "L0_test"


def _wait_action_id(env: VectorizedHamletEnv) -> int:
    return env.action_space.get_action_by_name("WAIT").id


def _interact_action_id(env: VectorizedHamletEnv) -> int:
    return env.action_space.get_action_by_name("INTERACT").id


def test_dac_engine_reward_calculation(compile_universe, test_config_pack_path, cpu_device):
    """Environment should wire DACEngine rewards using the v2.1 pack."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=4, device=cpu_device)

    env.reset()
    wait_id = _wait_action_id(env)
    actions = torch.full((4,), wait_id, dtype=torch.long, device=cpu_device)
    _, rewards, _, _ = env.step(actions)

    assert rewards.shape == (4,)
    assert hasattr(env, "dac_engine") and env.dac_engine is not None
    assert not hasattr(env, "reward_strategy")


def test_dac_engine_compiles_all_levels(compile_universe, test_config_pack_path, cpu_device):
    """All available curriculum levels in the test pack should compile and run."""
    universe = compile_universe(test_config_pack_path)
    for level in universe.available_levels:
        env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=2, device=cpu_device)
        env.reset()
        wait_id = _wait_action_id(env)
        actions = torch.full((2,), wait_id, dtype=torch.long, device=cpu_device)
        _, rewards, _, _ = env.step(actions)
        assert rewards.shape == (2,)
        assert hasattr(env, "dac_engine")


def test_intrinsic_rewards_integration(compile_universe, test_config_pack_path, cpu_device):
    """Intrinsic rewards from exploration module should flow into reward components."""
    from townlet.exploration.rnd import RNDExploration

    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=4, device=cpu_device)

    obs = env.reset()
    obs_dim = obs.shape[1]

    exploration = RNDExploration(
        obs_dim=obs_dim,
        embed_dim=128,
        learning_rate=1e-4,
        training_batch_size=128,
        epsilon_start=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.995,
        device=cpu_device,
    )
    env.set_exploration_module(exploration)

    wait_id = _wait_action_id(env)
    actions = torch.full((4,), wait_id, dtype=torch.long, device=cpu_device)
    obs, rewards, _, _ = env.step(actions)

    expected_intrinsic = exploration.compute_intrinsic_rewards(obs, update_stats=False)
    assert torch.any(expected_intrinsic != 0.0), "RND should emit non-zero intrinsic rewards for novel states"

    assert hasattr(env, "_last_reward_components"), "Reward components should be recorded for debugging"
    components = env._last_reward_components
    assert "intrinsic" in components
    intrinsic_component = components["intrinsic"]
    assert torch.any(intrinsic_component != 0.0), "Intrinsic component should propagate into reward calculation"


def test_affordance_history_tracking_last_action(compile_universe, test_config_pack_path, cpu_device):
    """_get_last_action_affordances should reflect last interact per agent."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=2, device=cpu_device)

    env.reset()
    interact_id = _interact_action_id(env)
    wait_id = _wait_action_id(env)

    sleep_pos = env.affordances.get("SLEEP")
    assert sleep_pos is not None, "SLEEP affordance must exist in L0_test"
    env.positions[0] = sleep_pos.clone()

    actions = torch.tensor([interact_id, wait_id], device=cpu_device)
    env.step(actions)

    last_affordances = env._get_last_action_affordances()
    assert last_affordances[0] == "SLEEP"
    assert last_affordances[1] is None


def test_affordance_history_tracking_streaks(compile_universe, test_config_pack_path, cpu_device):
    """Streak counters should increment on consecutive interactions with the same affordance."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=1, device=cpu_device)

    env.reset()
    interact_id = _interact_action_id(env)
    sleep_pos = env.affordances.get("SLEEP")
    assert sleep_pos is not None
    env.positions[0] = sleep_pos.clone()

    actions = torch.tensor([interact_id], device=cpu_device)
    env.step(actions)
    streaks = env._get_affordance_streaks()
    assert "SLEEP" in streaks
    assert streaks["SLEEP"][0] == 1

    env.step(actions)
    streaks = env._get_affordance_streaks()
    assert streaks["SLEEP"][0] == 2


def test_affordance_history_tracking_unique_count(compile_universe, test_config_pack_path, cpu_device):
    """Unique affordance counts should reflect distinct affordances used per agent."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=2, device=cpu_device)

    env.reset()
    interact_id = _interact_action_id(env)
    affordance_positions = list(env.affordances.values())
    assert len(affordance_positions) >= 2, "Need at least two affordances for this test"

    env.positions[0] = affordance_positions[0].clone()
    env.positions[1] = affordance_positions[1].clone()

    actions = torch.tensor([interact_id, interact_id], device=cpu_device)
    env.step(actions)

    unique_counts = env._get_unique_affordances_used()
    assert unique_counts.shape[0] == 2
    assert torch.all(unique_counts >= 0)


def test_affordance_history_tracking_reset(compile_universe, test_config_pack_path, cpu_device):
    """Tracking state should reset with environment reset."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=1, device=cpu_device)

    env.reset()
    interact_id = _interact_action_id(env)
    sleep_pos = env.affordances.get("SLEEP")
    assert sleep_pos is not None
    env.positions[0] = sleep_pos.clone()

    env.step(torch.tensor([interact_id], device=cpu_device))
    env.reset()

    assert all(a is None for a in env._get_last_action_affordances())
    assert env._get_affordance_streaks() == {}
    assert torch.all(env._get_unique_affordances_used() == 0)


def test_timing_bonus_receives_time_of_day(compile_universe, test_config_pack_path, cpu_device):
    """DACEngine should receive time_of_day even when stepping with WAIT."""
    universe = compile_universe(test_config_pack_path)
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL_NAME, num_agents=2, device=cpu_device)

    wait_id = _wait_action_id(env)
    env.step(torch.tensor([wait_id, wait_id], device=cpu_device))

    assert env.time_of_day is not None
