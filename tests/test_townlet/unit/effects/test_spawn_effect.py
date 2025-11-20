import pytest
import torch

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType


def test_spawn_effect_with_self_target():
    """Test spawn_effect command spawns effect on self."""
    # Create effect catalog with simple effect
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
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        }
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    # Create spawn_effect command
    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="poison",
        target="self",
        duration=10,
        intensity=1.0,
    )

    # Create context with effect_manager
    bars = {"health": torch.tensor([1.0, 0.8])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
    )

    # Execute command
    executor.execute(command, context)

    # Verify effect spawned on agent 0
    assert 0 in manager.agent_effects
    assert len(manager.agent_effects[0]) == 1
    assert manager.agent_effects[0][0].effect_id == "poison"
    assert manager.agent_effects[0][0].duration_remaining == 10


def test_spawn_effect_with_target():
    """Test spawn_effect command spawns effect on target."""
    catalog = EffectCatalog(
        effects={
            "stun": CompiledEffect(
                id="stun",
                scope="agent",
                duration=5,
                intensity=1.0,
                reapply_policy="replace",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        }
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="stun",
        target="target",  # Target agent, not self
        duration=5,
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0, 0.8])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=1,  # Target agent 1
        effect_manager=manager,
    )

    executor.execute(command, context)

    # Verify effect spawned on agent 1 (target), not agent 0 (self)
    assert 1 in manager.agent_effects
    assert len(manager.agent_effects[1]) == 1
    assert manager.agent_effects[1][0].effect_id == "stun"


def test_spawn_effect_cascade_depth_limit():
    """Test spawn_effect enforces max cascade depth."""
    catalog = EffectCatalog(
        effects={
            "recursive": CompiledEffect(
                id="recursive",
                scope="agent",
                duration=1,
                intensity=1.0,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        }
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="recursive",
        target="self",
        duration=1,
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        spawn_depth=10,  # At limit
    )

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="cascade depth limit exceeded"):
        executor.execute(command, context)
