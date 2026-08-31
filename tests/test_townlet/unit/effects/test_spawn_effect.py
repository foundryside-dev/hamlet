import pytest
import torch

from townlet.config.effects_config import CommandConfig, EffectScope
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.parser import CommandParser
from townlet.effects.schema import CommandNode, CommandType


class DummyItemManager:
    def spawn_item(self, *args, **kwargs):
        raise RuntimeError("spawn_item not supported in DummyItemManager")


@pytest.mark.parametrize(
    ("scope", "store_name", "store_key"),
    (
        (EffectScope.GLOBAL, "global_effects", None),
        (EffectScope.AGENT, "agent_effects", 0),
        (EffectScope.ITEM, "item_effects", 0),
        (EffectScope.AFFORDANCE, "affordance_effects", "0"),
    ),
)
def test_spawn_effect_definition_scope_is_runtime_authority(scope, store_name, store_key):
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "scoped": CompiledEffect(
                id="scoped",
                scope=scope.value,
                duration=10,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )
    manager = EffectManager(catalog=catalog, device="cpu")
    command = CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="scoped", target="self", intensity=1.0)
    context = ExecutionContext(
        bars={},
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
    )

    CommandExecutor().execute(command, context)

    store = getattr(manager, store_name)
    active = store[0] if store_key is None else store[store_key][0]
    assert active.scope == scope


def test_spawn_effect_with_self_target():
    """Test spawn_effect command spawns effect on self."""
    # Create effect catalog with simple effect
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "poison": CompiledEffect(
                id="poison",
                scope="agent",
                duration=10,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    # Create spawn_effect command
    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="poison",
        target="self",
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
        item_manager=DummyItemManager(),
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
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "stun": CompiledEffect(
                id="stun",
                scope="agent",
                duration=5,
                reapply_policy="replace",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="stun",
        target="target",  # Target agent, not self
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0, 0.8])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=1,  # Target agent 1
        effect_manager=manager,
        item_manager=DummyItemManager(),
    )

    executor.execute(command, context)

    # Verify effect spawned on agent 1 (target), not agent 0 (self)
    assert 1 in manager.agent_effects
    assert len(manager.agent_effects[1]) == 1
    assert manager.agent_effects[1][0].effect_id == "stun"


def test_spawn_effect_cascade_depth_limit():
    """Test spawn_effect enforces max cascade depth."""
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "recursive": CompiledEffect(
                id="recursive",
                scope="agent",
                duration=1,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="recursive",
        target="self",
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
        spawn_depth=10,  # At limit
    )

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="cascade depth limit exceeded"):
        executor.execute(command, context)


def test_spawn_effect_passes_spawn_depth_unchanged():
    """Executor should forward spawn_depth without incrementing."""
    from types import SimpleNamespace

    class RecordingManager:
        def __init__(self) -> None:
            self.last_spawn_depth: int | None = None
            self.current_step = 0
            self.catalog = SimpleNamespace(get=lambda effect_id: SimpleNamespace(duration=1, scope="agent"))

        def spawn_effect(self, **kwargs):
            self.last_spawn_depth = kwargs.get("spawn_depth")
            return SimpleNamespace(instance_id=1)

    manager = RecordingManager()
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="any",
        target="self",
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
        spawn_depth=3,
    )

    executor.execute(command, context)

    assert manager.last_spawn_depth == 3


def test_spawn_effect_uses_catalog_duration():
    """spawn_effect duration has exactly one authority: the catalog definition."""
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "slow": CompiledEffect(
                id="slow",
                scope="agent",
                duration=50,  # catalog duration
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="slow",
        target="self",
        intensity=1.0,
    )

    bars = {"health": torch.tensor([1.0, 0.8])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
    )

    executor.execute(command, context)

    assert 0 in manager.agent_effects
    assert manager.agent_effects[0][0].duration_remaining == 50


def test_spawn_effect_pipeline_requires_explicit_target_and_intensity():
    """Parser+compiler should execute only explicitly targeted spawn commands."""
    config = CommandConfig(spawn_effect="poison", target="self", intensity=1.0)
    parser = CommandParser()
    compiler = CommandCompiler(schema={})

    node = compiler.compile_command(parser.parse_command(config))

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "poison": CompiledEffect(
                id="poison",
                scope="agent",
                duration=3,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    bars = {"health": torch.tensor([1.0, 0.8])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=1,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
    )

    executor.execute(node, context)

    assert 1 in manager.agent_effects
    assert manager.agent_effects[1][0].effect_id == "poison"


def test_spawn_effect_evaluates_target_expression_when_not_literal():
    """Non-literal targets should be evaluated via target_ast at runtime."""
    config = CommandConfig(spawn_effect="stun", target="1 + 1", intensity=1.0)
    parser = CommandParser()
    compiler = CommandCompiler(schema={})
    node = compiler.compile_command(parser.parse_command(config))

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "stun": CompiledEffect(
                id="stun",
                scope="agent",
                duration=5,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu")
    executor = CommandExecutor()

    bars = {"health": torch.tensor([1.0, 0.9, 0.7])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        effect_manager=manager,
        item_manager=DummyItemManager(),
    )

    executor.execute(node, context)

    assert 2 in manager.agent_effects
    assert manager.agent_effects[2][0].effect_id == "stun"
