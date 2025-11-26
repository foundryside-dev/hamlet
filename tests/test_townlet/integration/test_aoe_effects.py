"""Integration tests for AoE (Area of Effect) healing effects."""

import pytest
import torch

from townlet.config.effects_config import EffectScope
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.parser import ExpressionParser


def test_aoe_heal_nearby_agents():
    """Test AoE healing effect using for_each."""
    executor = CommandExecutor()
    parser = ExpressionParser()

    # Create modify command with compiled AST
    modify_command = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.health",
        value_expr="target.bar.health + 0.3",
        value_ast=parser.parse("target.bar.health + 0.3"),
    )

    # Create effect catalog with group_heal effect
    catalog = EffectCatalog(
        effects={
            "group_heal": CompiledEffect(
                id="group_heal",
                scope="agent",
                duration=1,
                intensity=1.0,
                reapply_policy="replace",
                observable=True,
                on_spawn=[
                    CommandNode(
                        type=CommandType.FOR_EACH,
                        collection="nearby_agents",
                        radius=5.0,
                        iterator="ally",
                        body=[modify_command],
                    )
                ],
                on_tick=[],
                on_despawn=[],
                on_interrupt=[],
            ),
        }
    )

    manager = EffectManager(catalog=catalog, device="cpu", command_executor=executor)

    # Setup: 3 agents, agent 0 casts group_heal
    bars = {"health": torch.tensor([0.5, 0.4, 0.6])}
    agent_positions = torch.tensor([[0.0, 0.0], [3.0, 0.0], [10.0, 0.0]])
    # Agent 1 within radius 5.0, Agent 2 too far

    # Spawn group_heal effect on agent 0
    manager.spawn_effect(
        effect_id="group_heal",
        target_entity_id=0,
        scope=EffectScope.AGENT,
        duration=1,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
        agent_positions=agent_positions,
    )

    # Verify agent 1 healed, agent 2 not
    assert bars["health"][0].item() == pytest.approx(0.5)  # Self unchanged
    assert bars["health"][1].item() == pytest.approx(0.7)  # Agent 1 healed (+0.3)
    assert bars["health"][2].item() == pytest.approx(0.6)  # Agent 2 unchanged (too far)
