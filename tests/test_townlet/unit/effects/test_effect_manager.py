"""Unit tests for EffectManager runtime."""

import pytest

from townlet.config.effects_config import EffectDefinitionConfig, EffectsConfig, EffectScope, ReapplyPolicy
from townlet.effects.catalog import EffectCatalog
from townlet.effects.manager import ActiveEffect, EffectManager


def test_active_effect_initialization():
    """ActiveEffect stores lifecycle state."""
    effect = ActiveEffect(
        effect_id="regen",
        instance_id=42,
        target_entity_id=3,
        scope=EffectScope.AGENT,
        intensity=1.5,
        duration_total=100,
        duration_remaining=100,
        elapsed_ticks=0,
        spawn_step=1000,
    )

    assert effect.effect_id == "regen"
    assert effect.instance_id == 42
    assert effect.target_entity_id == 3
    assert effect.intensity == 1.5
    assert effect.duration_remaining == 100
    assert effect.elapsed_ticks == 0


def test_active_effect_tracks_multiple_targets():
    """Multiple agents can have same effect type."""
    effect1 = ActiveEffect(
        effect_id="regen",
        instance_id=1,
        target_entity_id=0,
        scope=EffectScope.AGENT,
        intensity=1.0,
        duration_total=50,
        duration_remaining=50,
        elapsed_ticks=0,
        spawn_step=100,
    )

    effect2 = ActiveEffect(
        effect_id="regen",
        instance_id=2,
        target_entity_id=5,
        scope=EffectScope.AGENT,
        intensity=2.0,
        duration_total=50,
        duration_remaining=30,
        elapsed_ticks=20,
        spawn_step=100,
    )

    assert effect1.target_entity_id != effect2.target_entity_id
    assert effect1.instance_id != effect2.instance_id
    assert effect1.intensity != effect2.intensity


@pytest.fixture
def catalog_fixture():
    """Create a catalog with 'regen' effect."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            EffectDefinitionConfig(
                id="regen",
                scope=EffectScope.AGENT,
                duration=100,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.STACK,
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        ],
    )
    return EffectCatalog.from_config(config)


def test_spawn_effect_creates_active_instance(catalog_fixture):
    """EffectManager.spawn_effect() creates ActiveEffect."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    effect = manager.spawn_effect(
        effect_id="regen",
        target_entity_id=5,
        scope=EffectScope.AGENT,
        duration=100,
        intensity=1.0,
        current_step=1000,
    )

    assert effect.effect_id == "regen"
    assert effect.target_entity_id == 5
    assert effect.duration_total == 100
    assert effect.intensity == 1.0
    assert effect.spawn_step == 1000
    assert effect.instance_id == 0  # First instance

    # Check stored in scoped collection
    assert 5 in manager.agent_effects
    assert effect in manager.agent_effects[5]


def test_spawn_effect_stack_policy_allows_multiple(catalog_fixture):
    """Stack policy allows multiple instances of same effect."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    effect1 = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.0, 100)
    effect2 = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.5, 110)

    assert len(manager.agent_effects[3]) == 2
    assert effect1.instance_id != effect2.instance_id
    assert effect1.intensity == 1.0
    assert effect2.intensity == 1.5
