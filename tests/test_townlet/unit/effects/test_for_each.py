"""Tests for for_each command."""

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType


def test_for_each_nearby_agents_with_modify():
    """Test for_each iterates over nearby agents and modifies bars."""
    executor = CommandExecutor()

    # Create for_each command: heal all agents within radius 3.0
    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="nearby_agents",
        radius=3.0,
        iterator="ally",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.health",
                value_expr="target.bar.health + 0.2",
            )
        ],
    )

    # Compile nested modify command
    schema = {"target.bar.health": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    # Create context with 3 agents (self at index 0, others at 1, 2)
    bars = {
        "health": torch.tensor([0.5, 0.6, 0.7]),  # All agents need healing
    }

    # Mock agent positions (needed for radius check)
    # Agent 0 at (0, 0), Agent 1 at (2, 0), Agent 2 at (10, 0)
    # Only Agent 1 is within radius 3.0
    agent_positions = torch.tensor([[0.0, 0.0], [2.0, 0.0], [10.0, 0.0]])

    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        agent_positions=agent_positions,  # NEW field needed
    )

    # Execute for_each
    executor.execute(command, context)

    # Verify only agent 1 was healed (within radius)
    assert bars["health"][0].item() == pytest.approx(0.5)  # Self unchanged
    assert bars["health"][1].item() == pytest.approx(0.8)  # Agent 1 healed (+0.2)
    assert bars["health"][2].item() == pytest.approx(0.7)  # Agent 2 unchanged (too far)


def test_for_each_all_agents():
    """Test for_each with all_agents collection."""
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        iterator="agent",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.energy",
                value_expr="target.bar.energy + 0.1",
            )
        ],
    )

    # Compile nested modify command
    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"energy": torch.tensor([0.2, 0.3, 0.4])}
    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
    )

    executor.execute(command, context)

    # All agents should be boosted (+0.1 energy)
    assert bars["energy"][0].item() == pytest.approx(0.3)
    assert bars["energy"][1].item() == pytest.approx(0.4)
    assert bars["energy"][2].item() == pytest.approx(0.5)


def test_for_each_empty_collection_noop():
    """Test for_each with empty collection is no-op."""
    executor = CommandExecutor()

    command = CommandNode(
        type=CommandType.FOR_EACH,
        collection="nearby_agents",
        radius=1.0,  # Very small radius - no one nearby
        iterator="ally",
        body=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.bar.health",
                value_expr="0.0",  # Would zero health
            )
        ],
    )

    # Compile nested modify command (with literal value this time)
    schema = {"target.bar.health": "float"}
    compiler = CommandCompiler(schema=schema)
    for body_cmd in command.body:
        compiler.compile_command(body_cmd)

    bars = {"health": torch.tensor([0.5, 0.6])}
    agent_positions = torch.tensor([[0.0, 0.0], [10.0, 10.0]])  # Far apart

    context = ExecutionContext(
        bars=bars,
        vfs_registry=None,
        self_index=0,
        target_index=None,
        agent_positions=agent_positions,
    )

    executor.execute(command, context)

    # Health unchanged (no nearby agents)
    assert bars["health"][0].item() == pytest.approx(0.5)
    assert bars["health"][1].item() == pytest.approx(0.6)
