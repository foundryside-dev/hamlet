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
    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    effect = manager.spawn_effect("regen", 1, EffectScope.AGENT, 100, 1.0, 500)

    # Initial state
    assert effect.elapsed_ticks == 0
    assert effect.duration_remaining == 100

    # Tick once
    manager.tick(current_step=501)

    assert effect.elapsed_ticks == 1
    assert effect.duration_remaining == 99


def test_tick_despawns_expired_effects(catalog_fixture):
    """tick() removes effects when duration_remaining reaches 0."""
    manager = EffectManager(catalog=catalog_fixture, device="cpu")
    _ = manager.spawn_effect("regen", 2, EffectScope.AGENT, 3, 1.0, 100)

    manager.tick(current_step=101)  # remaining=2
    manager.tick(current_step=102)  # remaining=1
    assert len(manager.agent_effects[2]) == 1

    manager.tick(current_step=103)  # remaining=0, despawn

    assert 2 not in manager.agent_effects or len(manager.agent_effects[2]) == 0


def test_tick_handles_multiple_scopes(catalog_fixture):
    """tick() processes effects from all scopes."""
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

    manager.tick(current_step=11)

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
    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor  # Inject mock

    _ = manager.spawn_effect("regen", 3, EffectScope.AGENT, 50, 1.0, 100)

    # Create minimal env_state mock
    class EnvState:
        pass

    env_state = EnvState()

    manager.tick(current_step=101, env_state=env_state)

    # Verify command executor called
    assert mock_executor.execute_commands_called
    assert mock_executor.on_tick_call_count > 0


def test_tick_executes_on_despawn_before_removal(catalog_with_commands, mock_executor):
    """on_despawn commands execute before effect removed."""
    manager = EffectManager(catalog=catalog_with_commands, device="cpu")
    manager.command_executor = mock_executor

    _ = manager.spawn_effect("buff", 5, EffectScope.AGENT, 2, 1.0, 200)

    class EnvState:
        pass

    env_state = EnvState()

    manager.tick(current_step=201, env_state=env_state)  # remaining=1
    initial_call_count = mock_executor.on_tick_call_count

    manager.tick(current_step=202, env_state=env_state)  # remaining=0, despawn

    # Verify on_despawn executed (call count increased again)
    assert mock_executor.on_tick_call_count > initial_call_count
    # Verify effect removed
    assert 5 not in manager.agent_effects or len(manager.agent_effects[5]) == 0
