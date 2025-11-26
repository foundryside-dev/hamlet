"""Tests for effect cascade depth limiting."""

import pytest
import torch

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import MAX_CASCADE_DEPTH, CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


class _StubEffectManager:
    def __init__(self, catalog: EffectCatalog):
        self.catalog = catalog
        self.spawn_calls: list[tuple] = []
        self.current_step = 0

    def spawn_effect(self, **kwargs):
        self.spawn_calls.append(kwargs)


def _make_context(spawn_depth: int, manager: _StubEffectManager) -> ExecutionContext:
    return ExecutionContext(
        bars={"energy": torch.tensor([1.0])},
        effect_manager=manager,
        self_index=0,
        target_index=0,
        spawn_depth=spawn_depth,
    )


def _make_catalog(effect_id: str = "shield") -> EffectCatalog:
    compiled = CompiledEffect(
        id=effect_id,
        scope="agent",
        duration=5,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )
    return EffectCatalog(effects={effect_id: compiled})


def _spawn_command(effect_id: str = "shield") -> CommandNode:
    return CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id=effect_id,
        target=0,  # explicit index to avoid self/target resolution
        duration=None,
        intensity=1.0,
    )


def test_cascade_depth_limit_triggers_error():
    """spawn_effect should hard-fail once cascade depth limit is reached."""
    catalog = _make_catalog()
    manager = _StubEffectManager(catalog)
    executor = CommandExecutor()
    context = _make_context(spawn_depth=MAX_CASCADE_DEPTH, manager=manager)
    cmd = _spawn_command()

    with pytest.raises(RuntimeError, match="depth limit exceeded"):
        executor.execute(cmd, context)

    # Ensure no spawn was attempted once limit tripped
    assert not manager.spawn_calls


def test_cascade_depth_within_limit_spawns():
    """spawn_effect should succeed when under the cascade depth cap."""
    catalog = _make_catalog()
    manager = _StubEffectManager(catalog)
    executor = CommandExecutor()
    context = _make_context(spawn_depth=MAX_CASCADE_DEPTH - 1, manager=manager)
    cmd = _spawn_command()

    executor.execute(cmd, context)

    assert len(manager.spawn_calls) == 1
    call_kwargs = manager.spawn_calls[0]
    assert call_kwargs["effect_id"] == "shield"
    assert call_kwargs["target_entity_id"] == 0
