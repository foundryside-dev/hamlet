"""Unit tests for effect reapply policies."""

import pytest

from townlet.config.effects_config import EffectDefinitionConfig, EffectsConfig, EffectScope, ReapplyPolicy
from townlet.effects.catalog import EffectCatalog
from townlet.effects.manager import EffectManager


@pytest.fixture
def catalog_with_policies():
    """Create a catalog with effects having different reapply policies."""
    config = EffectsConfig(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        version="1.0",
        effect_definitions=[
            EffectDefinitionConfig(
                id="shield",
                scope=EffectScope.AGENT,
                duration=100,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.RENEW,
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            ),
            EffectDefinitionConfig(
                id="poison",
                scope=EffectScope.AGENT,
                duration=50,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.MERGE,
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            ),
            EffectDefinitionConfig(
                id="buff",
                scope=EffectScope.AGENT,
                duration=80,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.REPLACE,
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            ),
        ],
    )
    return EffectCatalog.from_config(config)


def test_renew_policy_resets_duration(catalog_with_policies):
    """Renew policy resets duration_remaining to full."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")

    # Spawn initial effect
    effect1 = manager.spawn_effect("shield", 2, EffectScope.AGENT, 100, 1.0, 1000)
    effect1.duration_remaining = 20  # Simulate decay

    # Reapply same effect
    effect2 = manager.spawn_effect("shield", 2, EffectScope.AGENT, 100, 1.0, 1050)

    # Should be same instance with renewed duration
    assert len(manager.agent_effects[2]) == 1
    assert effect2.instance_id == effect1.instance_id
    assert effect2.duration_remaining == 100  # Reset to full


def test_merge_policy_adds_intensity(catalog_with_policies):
    """Merge policy accumulates intensity."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")

    effect1 = manager.spawn_effect("poison", 4, EffectScope.AGENT, 50, 1.0, 500)
    effect2 = manager.spawn_effect("poison", 4, EffectScope.AGENT, 50, 0.5, 510)

    assert len(manager.agent_effects[4]) == 1
    assert effect2.instance_id == effect1.instance_id
    assert effect2.intensity == 1.5  # 1.0 + 0.5


def test_replace_policy_despawns_old(catalog_with_policies):
    """Replace policy removes old instance and creates new."""
    manager = EffectManager(catalog=catalog_with_policies, device="cpu")

    effect1 = manager.spawn_effect("buff", 7, EffectScope.AGENT, 80, 2.0, 200)
    effect2 = manager.spawn_effect("buff", 7, EffectScope.AGENT, 80, 3.0, 210)

    assert len(manager.agent_effects[7]) == 1
    assert effect2.instance_id != effect1.instance_id  # New instance
    assert effect2.intensity == 3.0  # New intensity
