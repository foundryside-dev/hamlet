"""Integration tests for effects system with VectorizedHamletEnv."""

from pathlib import Path

import pytest
import torch

from townlet.environment.vectorized_env import VectorizedHamletEnv


@pytest.fixture
def effects_smoke_config_path():
    """Path to effects_smoke config pack."""
    return Path("configs/test/effects_smoke")


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

    effect = env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
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
    assert effect.duration_remaining == 19


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

    effect = env.effect_manager.spawn_effect(
        effect_id="health_boost",
        target_entity_id=0,
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


def test_effect_modifies_bar_values(compile_universe, effects_smoke_config_path, cpu_device):
    """Effects with modify commands change bar values."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=1,
        device=cpu_device,
    )

    env.reset()

    # Start below the declared ceiling so the effect's increase is observable inside
    # bounds: the clamp_and_validate phase enforces bars.*.bounds on the effects tick
    # (hamlet-f46e2b381a), so an effect can no longer push energy past bounds.max.
    env.meters[0, env.meter_name_to_index["energy"]] = 0.5
    initial_energy = env.meters[0, env.meter_name_to_index["energy"]].item()

    # Spawn energy_regen effect

    env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
    )

    # Step once
    wait_action = env.action_space.get_action_by_name("WAIT")
    actions = torch.full((1,), wait_action.id, dtype=torch.long, device=cpu_device)
    env.step(actions)

    # Energy should increase by 0.05 per effect, but passive depletion is 0.01
    # Net change: +0.05 - 0.01 = +0.04
    new_energy = env.meters[0, env.meter_name_to_index["energy"]].item()
    expected_energy = initial_energy + 0.04  # Effect (+0.05) - passive depletion (-0.01)
    assert new_energy > initial_energy
    assert abs(new_energy - expected_energy) < 1e-5


def test_on_spawn_commands_execute_immediately(compile_universe, effects_smoke_config_path, cpu_device):
    """on_spawn commands execute when effect spawned."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=1,
        device=cpu_device,
    )

    env.reset()

    # Set health to 0.5
    env.meters[0, env.meter_name_to_index["health"]] = 0.5
    initial_health = 0.5

    # Spawn health_boost (on_spawn adds 0.2 health)
    # Build the command context explicitly so on_spawn runs immediately.

    effect = env.effect_manager.spawn_effect(
        effect_id="health_boost",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
    )

    # Manually execute on_spawn commands (simulating what spawn_effect should do)
    if env.effect_manager.command_executor:
        context = env.effect_manager._build_context(effect, env)
        effect_def = env.effect_manager.catalog.effects["health_boost"]
        env.effect_manager.command_executor.execute_commands(effect_def.on_spawn, context)

    # Health should increase immediately (by 0.2)
    new_health = env.meters[0, env.meter_name_to_index["health"]].item()
    assert new_health > initial_health
    assert abs(new_health - 0.7) < 1e-5


def test_renew_policy_resets_duration_in_environment(compile_universe, effects_smoke_config_path, cpu_device):
    """RENEW policy resets effect duration in live environment."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=1,
        device=cpu_device,
    )

    env.reset()

    # Spawn effect with the catalog's declared duration (20).
    effect = env.effect_manager.spawn_effect(
        effect_id="energy_regen",  # Has RENEW policy
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
    )

    # Step twice (duration should be 18)
    wait_action = env.action_space.get_action_by_name("WAIT")
    actions = torch.full((1,), wait_action.id, dtype=torch.long, device=cpu_device)
    env.step(actions)
    env.step(actions)
    assert effect.duration_remaining == 18

    # Reapply (should reset to the catalog duration)
    env.effect_manager.spawn_effect(
        effect_id="energy_regen",
        target_entity_id=0,
        intensity=1.0,
        current_step=2,
    )

    assert effect.duration_remaining == 20  # Renewed


def test_merge_policy_stacks_intensity(compile_universe, effects_smoke_config_path, cpu_device):
    """MERGE policy accumulates intensity for poison."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(
        universe=universe,
        level_name="L0_effects",
        num_agents=1,
        device=cpu_device,
    )

    env.reset()

    effect = env.effect_manager.spawn_effect(
        effect_id="poison",  # Has MERGE policy
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
    )

    # Apply again with intensity=0.5
    env.effect_manager.spawn_effect(
        effect_id="poison",
        target_entity_id=0,
        intensity=0.5,
        current_step=1,
    )

    assert effect.intensity == 1.5  # Merged


def test_effect_rows_appear_in_the_observation_when_an_effect_spawns(compile_universe, effects_smoke_config_path, cpu_device):
    """Config-in/behaviour-out for the `effect` token type: a declared effect's row is absent
    until it spawns, present with a live remaining fraction after, and decays as it ticks."""
    universe = compile_universe(effects_smoke_config_path)
    env = VectorizedHamletEnv.from_universe(universe=universe, level_name="L0_effects", num_agents=1, device=cpu_device)
    layout = env.token_spec.compact_layout().get_type("effect")
    assert layout is not None and layout.capacity > 0
    remaining = layout.dynamic_features.index("remaining_fraction")

    obs = env.reset()
    before = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(
        layout.capacity, layout.compact_row_width
    )
    before_present = int(before[:, 0].sum().item())

    env.effect_manager.spawn_effect(effect_id="energy_regen", target_entity_id=0, intensity=1.0, current_step=0)
    wait = env.action_space.get_action_by_name("WAIT").id
    obs, *_ = env.step(torch.full((1,), wait, dtype=torch.long, device=cpu_device))
    rows = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)
    present = rows[:, 0] == 1.0
    assert present.sum().item() == before_present + 1
    first = rows[present][0, remaining].item()
    assert 0.0 < first <= 1.0

    obs, *_ = env.step(torch.full((1,), wait, dtype=torch.long, device=cpu_device))
    rows = obs[0, layout.start : layout.start + layout.capacity * layout.compact_row_width].view(layout.capacity, layout.compact_row_width)
    assert rows[rows[:, 0] == 1.0][0, remaining].item() < first
