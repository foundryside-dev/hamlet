import torch

from townlet.config.effects_config import EffectScope
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType


def test_poison_spawns_nausea_cascade():
    """Test effect spawning another effect (poison → nausea)."""
    executor = CommandExecutor()

    # Create catalog with poison (spawns nausea) and nausea effects
    catalog = EffectCatalog(
        effects={
            "poison": CompiledEffect(
                id="poison",
                scope="agent",
                duration=10,
                intensity=1.0,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[
                    CommandNode(
                        type=CommandType.SPAWN_EFFECT,
                        effect_id="nausea",
                        target="self",
                        duration=5,
                        intensity=0.5,
                    )
                ],
                on_despawn=[],
                on_interrupt=[],
            ),
            "nausea": CompiledEffect(
                id="nausea",
                scope="agent",
                duration=5,
                intensity=0.5,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            ),
        }
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)

    # Spawn poison effect manually
    bars = {"health": torch.tensor([1.0])}
    manager.spawn_effect(
        effect_id="poison",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=10,
        intensity=1.0,
        current_step=0,
    )

    # Verify only poison effect exists initially
    assert 0 in manager.agent_effects
    assert len(manager.agent_effects[0]) == 1
    assert manager.agent_effects[0][0].effect_id == "poison"

    # Tick manager (should execute poison's on_tick, spawning nausea)
    manager.tick(bars=bars, vfs_registry=None, current_step=1)

    # Verify nausea was spawned
    assert 0 in manager.agent_effects
    effects = manager.agent_effects[0]
    effect_ids = [e.effect_id for e in effects]
    assert "poison" in effect_ids
    assert "nausea" in effect_ids
    assert len(effects) == 2  # Both poison and nausea active
