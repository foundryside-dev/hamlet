"""Integration tests for effects system with VectorizedHamletEnv."""

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv


@pytest.fixture
def effects_smoke_config_path():
    """Path to effects_smoke config pack."""
    return Path("/home/john/hamlet/configs/test/effects_smoke")


def test_environment_initializes_effect_manager(compile_universe, effects_smoke_config_path, cpu_device):
    """VectorizedHamletEnv initializes EffectManager from compiled world."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=4,
        device=cpu_device,
    )

    # Verify EffectManager initialized
    assert hasattr(env, "effect_manager")
    assert env.effect_manager is not None
    assert env.effect_manager.catalog is not None

    # Verify catalog loaded from effects.yaml
    assert "energy_regen" in env.effect_manager.catalog.effects
    assert "health_boost" in env.effect_manager.catalog.effects


def test_environment_ticks_effects_each_step(compile_universe, effects_smoke_config_path, cpu_device):
    """env.step() calls effect_manager.tick()."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=2,
        device=cpu_device,
    )

    env.reset()

    # Spawn effect manually (before affordance interactions work)
    from townlet.config.effects_config import EffectScope

    effect = env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=10,
        intensity=1.0,
        current_step=0,
    )

    assert effect.elapsed_ticks == 0

    # Step environment
    wait_action = env.action_space.get_action_by_name("WAIT")
    actions = torch.full((2,), wait_action.id, dtype=torch.long, device=cpu_device)
    obs, reward, done, info = env.step(actions)

    # Verify effect ticked
    assert effect.elapsed_ticks == 1
    assert effect.duration_remaining == 9


def test_effects_auto_despawn_after_duration(compile_universe, effects_smoke_config_path, cpu_device):
    """Effects automatically despawn when duration_remaining reaches 0."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=1,
        device=cpu_device,
    )

    env.reset()

    from townlet.config.effects_config import EffectScope

    effect = env.effect_manager.spawn_effect(
        effect_id="health_boost",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=3,
        intensity=1.0,
        current_step=0,
    )

    # Step 3 times
    wait_action = env.action_space.get_action_by_name("WAIT")
    actions = torch.full((1,), wait_action.id, dtype=torch.long, device=cpu_device)
    for _ in range(3):
        env.step(actions)

    # Effect should be despawned
    active_effects = env.effect_manager.get_all_active_effects()
    assert effect not in active_effects
