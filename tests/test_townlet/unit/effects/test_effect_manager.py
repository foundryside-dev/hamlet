"""Unit tests for EffectManager runtime."""

import pytest

from townlet.config.effects_config import CommandConfig, EffectDefinitionConfig, EffectsConfig, EffectScope, ReapplyPolicy
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


def test_tick_updates_elapsed_and_remaining(catalog_fixture):
    """tick() advances lifecycle counters."""
    import torch

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("regen", 1, EffectScope.AGENT, 100, 1.0, 500)

    # Initial state
    assert effect.elapsed_ticks == 0
    assert effect.duration_remaining == 100

    # Tick once
    bars = {"health": torch.tensor([1.0, 0.8])}
    manager.tick(bars=bars, vfs_registry=None, current_step=501)

    assert effect.elapsed_ticks == 1
    assert effect.duration_remaining == 99


def test_tick_despawns_expired_effects(catalog_fixture):
    """tick() removes effects when duration_remaining reaches 0."""
    import torch

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    _ = manager.spawn_effect("regen", 2, EffectScope.AGENT, 3, 1.0, 100)

    bars = {"health": torch.tensor([1.0, 0.8, 0.9])}
    manager.tick(bars=bars, vfs_registry=None, current_step=101)  # remaining=2
    manager.tick(bars=bars, vfs_registry=None, current_step=102)  # remaining=1
    assert len(manager.agent_effects[2]) == 1

    manager.tick(bars=bars, vfs_registry=None, current_step=103)  # remaining=0, despawn

    assert 2 not in manager.agent_effects or len(manager.agent_effects[2]) == 0


def test_tick_handles_multiple_scopes(catalog_fixture):
    """tick() processes effects from all scopes."""
    import torch

    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    # Add a global effect to the catalog
    catalog_fixture.effects["day_cycle"] = catalog_fixture.effects["regen"].__class__(
        id="day_cycle",
        scope=EffectScope.GLOBAL,
        duration=200,
        intensity=1.0,
        reapply_policy=ReapplyPolicy.STACK,
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    global_effect = manager.spawn_effect("day_cycle", 0, EffectScope.GLOBAL, 200, 1.0, 10)
    agent_effect = manager.spawn_effect("regen", 5, EffectScope.AGENT, 50, 1.0, 10)

    bars = {"health": torch.tensor([1.0] * 6)}
    manager.tick(bars=bars, vfs_registry=None, current_step=11)

    assert global_effect.elapsed_ticks == 1
    assert agent_effect.elapsed_ticks == 1


# Step 5: Command Execution Integration Tests


class MockCommandExecutor:
    """Mock CommandExecutor for testing command execution integration."""

    def __init__(self):
        self.execute_commands_called = False
        self.on_tick_call_count = 0
        self.on_despawn_called = False
        self.last_commands = None
        self.last_context = None

    def execute(self, command, context):
        """Mock execute method (single command)."""
        self.execute_commands_called = True
        self.last_context = context
        self.on_tick_call_count += 1

    def execute_commands(self, commands, context):
        """Mock execute_commands method."""
        self.execute_commands_called = True
        self.last_commands = commands
        self.last_context = context

        # Track on_tick vs on_despawn by checking command list content
        if commands:  # If there are commands
            self.on_tick_call_count += 1


@pytest.fixture
def catalog_with_commands():
    """Create a catalog with effects that have on_tick and on_despawn commands."""
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            EffectDefinitionConfig(
                id="regen",
                scope=EffectScope.AGENT,
                duration=50,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.STACK,
                observable=True,
                on_spawn=[],
                on_tick=[CommandConfig(modify="target.bar.energy", value="target.bar.energy + 0.1")],
                on_despawn=[CommandConfig(modify="target.bar.energy", value="target.bar.energy + 5.0")],
                on_interrupt=[],
            ),
            EffectDefinitionConfig(
                id="buff",
                scope=EffectScope.AGENT,
                duration=2,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.STACK,
                observable=True,
                on_spawn=[],
                on_tick=[CommandConfig(modify="target.bar.health", value="target.bar.health + 0.5")],
                on_despawn=[CommandConfig(modify="target.bar.health", value="target.bar.health + 10.0")],
                on_interrupt=[],
            ),
        ],
    )
    return EffectCatalog.from_config(config)


@pytest.fixture
def mock_executor():
    """Create a mock command executor."""
    return MockCommandExecutor()


def test_tick_executes_on_tick_commands(catalog_with_commands, mock_executor):
    """tick() executes on_tick commands for each active effect."""
    import torch

    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor  # Inject mock

    _ = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.0, 100)

    bars = {"energy": torch.tensor([1.0] * 4)}
    manager.tick(bars=bars, vfs_registry=None, current_step=101)

    # Verify command executor called
    assert mock_executor.execute_commands_called
    assert mock_executor.on_tick_call_count > 0


def test_tick_executes_on_despawn_before_removal(catalog_with_commands, mock_executor):
    """on_despawn commands execute before effect removed."""
    import torch

    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor

    _ = manager.spawn_effect("buff", 5, EffectScope.AGENT, 2, 1.0, 200)

    bars = {"health": torch.tensor([1.0] * 6)}
    manager.tick(bars=bars, vfs_registry=None, current_step=201)  # remaining=1
    initial_call_count = mock_executor.on_tick_call_count

    manager.tick(bars=bars, vfs_registry=None, current_step=202)  # remaining=0, despawn

    # Verify on_despawn executed (call count increased again)
    assert mock_executor.on_tick_call_count > initial_call_count
    # Verify effect removed
    assert 5 not in manager.agent_effects or len(manager.agent_effects[5]) == 0


def test_spawn_effect_executes_on_spawn():
    """spawn_effect() executes on_spawn commands when spawning effects."""
    import torch

    # Create catalog with effect that has on_spawn commands
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            EffectDefinitionConfig(
                id="poisoned",
                scope=EffectScope.AGENT,
                duration=30,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.STACK,
                observable=True,
                on_spawn=[CommandConfig(modify="target.bar.health", value="target.bar.health - 5.0")],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        ],
    )
    catalog = EffectCatalog.from_config(config)

    # Create mock executor to track command execution
    mock_executor = MockCommandExecutor()
    manager = EffectManager(catalog=catalog, device="cpu", command_executor=mock_executor)

    # Spawn effect with bars and vfs_registry
    bars = {"health": torch.tensor([100.0, 95.0, 80.0])}
    effect = manager.spawn_effect(
        effect_id="poisoned",
        target_entity_id=1,
        scope=EffectScope.AGENT,
        duration=30,
        intensity=1.0,
        current_step=100,
        bars=bars,
        vfs_registry=None,
        spawn_depth=0,
    )

    # Verify effect created
    assert effect.effect_id == "poisoned"
    assert effect.target_entity_id == 1

    # Verify on_spawn commands executed
    assert mock_executor.execute_commands_called
    assert mock_executor.last_context is not None
    assert mock_executor.last_context.self_index == 1
    assert mock_executor.last_context.effect == effect
    assert mock_executor.last_context.spawn_depth == 1  # Incremented from 0


def test_spawn_effect_skips_on_spawn_without_bars():
    """spawn_effect() skips on_spawn commands when bars not provided."""

    # Create catalog with effect that has on_spawn commands
    config = EffectsConfig(
        version="1.0",
        effect_definitions=[
            EffectDefinitionConfig(
                id="poisoned",
                scope=EffectScope.AGENT,
                duration=30,
                intensity=1.0,
                reapply_policy=ReapplyPolicy.STACK,
                observable=True,
                on_spawn=[CommandConfig(modify="target.bar.health", value="target.bar.health - 5.0")],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            )
        ],
    )
    catalog = EffectCatalog.from_config(config)

    # Create mock executor
    mock_executor = MockCommandExecutor()
    manager = EffectManager(catalog=catalog, device="cpu", command_executor=mock_executor)

    # Spawn effect without bars (commands require bars to execute)
    effect = manager.spawn_effect(
        effect_id="poisoned",
        target_entity_id=2,
        scope=EffectScope.AGENT,
        duration=30,
        intensity=1.0,
        current_step=100,
    )

    # Verify effect created but on_spawn NOT executed
    assert effect.effect_id == "poisoned"
    assert not mock_executor.execute_commands_called


# --- NullItemManager tests ---


def test_null_item_manager_spawn_item_raises():
    """NullItemManager.spawn_item() raises RuntimeError."""
    from townlet.effects.manager import NullItemManager

    manager = NullItemManager()

    with pytest.raises(RuntimeError, match="ItemManager is not configured"):
        manager.spawn_item("item_type")


def test_null_item_manager_tick_returns_none():
    """NullItemManager.tick() returns None."""
    from townlet.effects.manager import NullItemManager

    manager = NullItemManager()
    result = manager.tick()

    assert result is None


def test_null_item_manager_process_respawns_returns_none():
    """NullItemManager.process_respawns() returns None."""
    from townlet.effects.manager import NullItemManager

    manager = NullItemManager()
    result = manager.process_respawns()

    assert result is None


# --- Item and affordance scope tests ---


def test_spawn_effect_item_scope(catalog_fixture):
    """EffectManager handles ITEM scope effects."""
    # Add item-scoped effect to catalog
    catalog_fixture.effects["item_decay"] = catalog_fixture.effects["regen"].__class__(
        id="item_decay",
        scope=EffectScope.ITEM,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    effect = manager.spawn_effect(
        effect_id="item_decay",
        target_entity_id=42,  # Item ID
        scope=EffectScope.ITEM,
        duration=100,
        intensity=1.0,
        current_step=0,
    )

    assert effect.scope == EffectScope.ITEM
    assert 42 in manager.item_effects
    assert effect in manager.item_effects[42]


def test_spawn_effect_affordance_scope(catalog_fixture):
    """EffectManager handles AFFORDANCE scope effects."""
    # Add affordance-scoped effect to catalog
    catalog_fixture.effects["depleted"] = catalog_fixture.effects["regen"].__class__(
        id="depleted",
        scope=EffectScope.AFFORDANCE,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    effect = manager.spawn_effect(
        effect_id="depleted",
        target_entity_id=7,  # Affordance index
        scope=EffectScope.AFFORDANCE,
        duration=100,
        intensity=1.0,
        current_step=0,
    )

    assert effect.scope == EffectScope.AFFORDANCE
    assert "7" in manager.affordance_effects  # Keyed by string
    assert effect in manager.affordance_effects["7"]


def test_get_all_active_effects_includes_all_scopes(catalog_fixture):
    """get_all_active_effects() returns effects from all scopes."""
    # Add effects for different scopes
    catalog_fixture.effects["item_decay"] = catalog_fixture.effects["regen"].__class__(
        id="item_decay",
        scope=EffectScope.ITEM,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )
    catalog_fixture.effects["depleted"] = catalog_fixture.effects["regen"].__class__(
        id="depleted",
        scope=EffectScope.AFFORDANCE,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )
    catalog_fixture.effects["global_buff"] = catalog_fixture.effects["regen"].__class__(
        id="global_buff",
        scope=EffectScope.GLOBAL,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    # Spawn effects in different scopes
    global_eff = manager.spawn_effect("global_buff", 0, EffectScope.GLOBAL, 100, 1.0, 0)
    agent_eff = manager.spawn_effect("regen", 1, EffectScope.AGENT, 100, 1.0, 0)
    item_eff = manager.spawn_effect("item_decay", 42, EffectScope.ITEM, 100, 1.0, 0)
    aff_eff = manager.spawn_effect("depleted", 7, EffectScope.AFFORDANCE, 100, 1.0, 0)

    all_effects = manager.get_all_active_effects()

    assert len(all_effects) == 4
    assert global_eff in all_effects
    assert agent_eff in all_effects
    assert item_eff in all_effects
    assert aff_eff in all_effects


# --- cancel_effect tests ---


def test_cancel_effect_agent_scope(catalog_fixture):
    """cancel_effect() removes agent-scoped effect."""
    import torch

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("regen", 3, EffectScope.AGENT, 100, 1.0, 0)

    bars = {"health": torch.tensor([1.0] * 4)}
    manager.cancel_effect(effect.instance_id, bars, None, current_step=10)

    assert 3 not in manager.agent_effects or effect not in manager.agent_effects.get(3, [])


def test_cancel_effect_global_scope(catalog_fixture):
    """cancel_effect() removes global-scoped effect."""
    import torch

    # Add global effect to catalog
    catalog_fixture.effects["global_buff"] = catalog_fixture.effects["regen"].__class__(
        id="global_buff",
        scope=EffectScope.GLOBAL,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("global_buff", 0, EffectScope.GLOBAL, 100, 1.0, 0)

    bars = {"health": torch.tensor([1.0])}
    manager.cancel_effect(effect.instance_id, bars, None, current_step=10)

    assert effect not in manager.global_effects


def test_cancel_effect_item_scope(catalog_fixture):
    """cancel_effect() removes item-scoped effect."""
    import torch

    # Add item effect to catalog
    catalog_fixture.effects["item_decay"] = catalog_fixture.effects["regen"].__class__(
        id="item_decay",
        scope=EffectScope.ITEM,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("item_decay", 42, EffectScope.ITEM, 100, 1.0, 0)

    bars = {"health": torch.tensor([1.0])}
    manager.cancel_effect(effect.instance_id, bars, None, current_step=10)

    assert 42 not in manager.item_effects or effect not in manager.item_effects.get(42, [])


def test_cancel_effect_affordance_scope(catalog_fixture):
    """cancel_effect() removes affordance-scoped effect."""
    import torch

    # Add affordance effect to catalog
    catalog_fixture.effects["depleted"] = catalog_fixture.effects["regen"].__class__(
        id="depleted",
        scope=EffectScope.AFFORDANCE,
        duration=100,
        intensity=1.0,
        reapply_policy="stack",
        observable=True,
        on_spawn=[],
        on_tick=[],
        on_despawn=[],
        on_interrupt=[],
    )

    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("depleted", 7, EffectScope.AFFORDANCE, 100, 1.0, 0)

    bars = {"health": torch.tensor([1.0])}
    manager.cancel_effect(effect.instance_id, bars, None, current_step=10)

    assert "7" not in manager.affordance_effects or effect not in manager.affordance_effects.get("7", [])


def test_cancel_effect_not_found_raises(catalog_fixture):
    """cancel_effect() raises when effect not found."""
    import torch

    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    bars = {"health": torch.tensor([1.0])}
    with pytest.raises(ValueError, match="not found"):
        manager.cancel_effect(instance_id=99999, bars=bars, vfs_registry=None, current_step=10)


# --- Scheduler tests ---


def test_reset_scheduler(catalog_fixture):
    """reset_scheduler() clears pending work."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    # Reset should not raise
    manager.reset_scheduler(current_tick=100)

    # Scheduler should be reset
    assert manager.scheduler.current_tick == 100


def test_cancel_scheduled_for_entity(catalog_fixture):
    """cancel_scheduled_for_entity() delegates to scheduler."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")

    # Should not raise
    manager.cancel_scheduled_for_entity(scope="agent", entity_id=5)
