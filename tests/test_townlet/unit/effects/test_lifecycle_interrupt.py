import pytest
import torch

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.parser import ExpressionParser


def test_on_interrupt_executes_when_replaced():
    """Test on_interrupt hook executes when effect replaced."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    # Create effect with on_interrupt hook
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "concentration": CompiledEffect(
                id="concentration",
                scope="agent",
                duration=10,
                reapply_policy="replace",  # Reapplying replaces old effect
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.2"),  # Penalty for lost concentration
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)

    bars = {"mood": torch.tensor([1.0])}

    # Spawn first concentration effect on agent 0
    manager.spawn_effect(
        effect_id="concentration",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Verify mood unchanged
    assert bars["mood"][0].item() == pytest.approx(1.0)

    # Spawn second concentration effect (replaces first)
    manager.spawn_effect(
        effect_id="concentration",
        target_entity_id=0,
        intensity=1.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    # Verify on_interrupt executed (mood penalty applied)
    assert bars["mood"][0].item() == pytest.approx(0.8)  # -0.2 mood penalty


def test_on_interrupt_executes_on_merge():
    """on_interrupt should run when merge consumes effect."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "merge_buff": CompiledEffect(
                id="merge_buff",
                scope="agent",
                duration=10,
                reapply_policy="merge",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.1"),
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)
    bars = {"mood": torch.tensor([1.0])}

    # Spawn first instance
    manager.spawn_effect(
        effect_id="merge_buff",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Merge second instance
    manager.spawn_effect(
        effect_id="merge_buff",
        target_entity_id=0,
        intensity=2.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    assert bars["mood"][0].item() == pytest.approx(0.9)


def test_on_interrupt_executes_on_manual_cancel():
    """on_interrupt should run when effect is manually cancelled."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "cancel_me": CompiledEffect(
                id="cancel_me",
                scope="agent",
                duration=10,
                reapply_policy="stack",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.25"),
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)
    bars = {"mood": torch.tensor([1.0])}

    # Spawn effect
    active = manager.spawn_effect(
        effect_id="cancel_me",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Cancel manually
    manager.cancel_effect(
        instance_id=active.instance_id,
        bars=bars,
        vfs_registry=None,
        current_step=5,
    )

    assert bars["mood"][0].item() == pytest.approx(0.75)


def test_on_interrupt_not_called_for_other_policies():
    """Test on_interrupt only executes for replace policy, not renew/merge/stack."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    # Test renew policy - should NOT call on_interrupt
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "buff": CompiledEffect(
                id="buff",
                scope="agent",
                duration=10,
                reapply_policy="renew",  # Renew doesn't interrupt
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.5"),
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)
    bars = {"mood": torch.tensor([1.0])}

    # Spawn first buff
    manager.spawn_effect(
        effect_id="buff",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Renew buff (should NOT execute on_interrupt)
    manager.spawn_effect(
        effect_id="buff",
        target_entity_id=0,
        intensity=1.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    # Verify on_interrupt NOT executed (mood still 1.0)
    assert bars["mood"][0].item() == pytest.approx(1.0)


def test_on_interrupt_skips_on_despawn():
    """Test on_interrupt replaces on_despawn when effect is interrupted."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    # Create effect with both on_interrupt and on_despawn
    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "focus": CompiledEffect(
                id="focus",
                scope="agent",
                duration=10,
                reapply_policy="replace",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.health",
                        value_ast=parser.parse("bar.health - 0.5"),  # Despawn penalty
                    )
                ],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.3"),  # Interrupt penalty
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)
    bars = {"mood": torch.tensor([1.0]), "health": torch.tensor([1.0])}

    # Spawn first focus effect
    manager.spawn_effect(
        effect_id="focus",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Replace with second focus effect
    manager.spawn_effect(
        effect_id="focus",
        target_entity_id=0,
        intensity=1.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    # Verify on_interrupt executed (mood penalty)
    assert bars["mood"][0].item() == pytest.approx(0.7)

    # Verify on_despawn NOT executed (health unchanged)
    assert bars["health"][0].item() == pytest.approx(1.0)


def test_interrupt_reason_set_in_context():
    """Test interrupt_reason is set in ExecutionContext during on_interrupt."""
    parser = ExpressionParser()

    # Track interrupt_reason by capturing context in executor
    captured_context = {}

    # Create a custom executor that captures context
    class CapturingExecutor(CommandExecutor):
        def execute(self, command, context):
            captured_context["interrupt_reason"] = context.interrupt_reason
            super().execute(command, context)

    capturing_executor = CapturingExecutor()

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "shield": CompiledEffect(
                id="shield",
                scope="agent",
                duration=10,
                reapply_policy="replace",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.1"),
                    )
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=capturing_executor)
    bars = {"mood": torch.tensor([1.0])}

    # Spawn first effect
    manager.spawn_effect(
        effect_id="shield",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Replace (should capture interrupt_reason)
    manager.spawn_effect(
        effect_id="shield",
        target_entity_id=0,
        intensity=1.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    # Verify interrupt_reason was set
    assert captured_context["interrupt_reason"] == "replaced_by_effect"


def test_on_interrupt_with_multiple_commands():
    """Test on_interrupt can execute multiple commands."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    catalog = EffectCatalog(
        max_active_effects={"global": 8, "agent": 8, "item": 8, "affordance": 8},
        effects={
            "multi": CompiledEffect(
                id="multi",
                scope="agent",
                duration=10,
                reapply_policy="replace",
                observable=True,
                on_spawn=[],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.mood",
                        value_ast=parser.parse("bar.mood - 0.2"),
                    ),
                    CommandNode(
                        type=CommandType.MODIFY,
                        path="bar.health",
                        value_ast=parser.parse("bar.health - 0.1"),
                    ),
                ],
            ),
        },
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)
    bars = {"mood": torch.tensor([1.0]), "health": torch.tensor([1.0])}

    # Spawn first effect
    manager.spawn_effect(
        effect_id="multi",
        target_entity_id=0,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    # Replace (should execute all on_interrupt commands)
    manager.spawn_effect(
        effect_id="multi",
        target_entity_id=0,
        intensity=1.0,
        current_step=1,
        bars=bars,
        vfs_registry=None,
    )

    # Verify both commands executed
    assert bars["mood"][0].item() == pytest.approx(0.8)
    assert bars["health"][0].item() == pytest.approx(0.9)
