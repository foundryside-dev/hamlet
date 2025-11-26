"""Tests for trigger_cascade command execution and validation."""

from __future__ import annotations

import pytest
import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.environment.meter_dynamics import MeterDynamics
from townlet.world.expression.parser import ExpressionParser


def _make_meter_dynamics() -> MeterDynamics:
    base = torch.tensor([0.0, 0.0], dtype=torch.float32)
    cascade_data = {
        "health_drop": [
            {"source_idx": 0, "target_idx": 1, "threshold": 0.5, "strength": 0.2},
        ]
    }
    modulation_data: list[dict] = []
    terminal_conditions: list[dict] = []
    return MeterDynamics(
        base_depletions=base,
        cascade_data=cascade_data,
        modulation_data=modulation_data,
        terminal_conditions=terminal_conditions,
        meter_name_to_index={"energy": 0, "health": 1},
        device=torch.device("cpu"),
    )


def test_trigger_cascade_applies_penalty():
    meters = {"energy": torch.tensor([[0.25], [0.75]]), "health": torch.tensor([[1.0], [1.0]])}
    ctx = ExecutionContext(bars=meters, meter_dynamics=_make_meter_dynamics())
    parser = ExpressionParser()
    cmd = CommandNode(
        type=CommandType.TRIGGER_CASCADE,
        cascade_id="health_drop",
        cascade_strength=1.0,
        # use dummy ASTs to satisfy executor path
        value_ast=parser.parse("0"),
    )

    executor = CommandExecutor()
    executor.execute(cmd, ctx)

    # First agent below threshold: health should drop
    assert torch.isclose(ctx.bars["health"][0, 0], torch.tensor(1.0 - 0.2 * ((0.5 - 0.25) / 0.5)))
    # Second agent above threshold: unchanged
    assert torch.isclose(ctx.bars["health"][1, 0], torch.tensor(1.0))


def test_trigger_cascade_rejects_unknown_id():
    ctx = ExecutionContext(bars={"energy": torch.ones(1), "health": torch.ones(1)}, meter_dynamics=_make_meter_dynamics())
    cmd = CommandNode(type=CommandType.TRIGGER_CASCADE, cascade_id="missing", cascade_strength=1.0)
    executor = CommandExecutor()
    with pytest.raises(ValueError, match="Unknown cascade_id"):
        executor.execute(cmd, ctx)


def test_trigger_cascade_rejects_nonpositive_strength():
    ctx = ExecutionContext(bars={"energy": torch.ones(1), "health": torch.ones(1)}, meter_dynamics=_make_meter_dynamics())
    cmd = CommandNode(type=CommandType.TRIGGER_CASCADE, cascade_id="health_drop", cascade_strength=0.0)
    executor = CommandExecutor()
    with pytest.raises(ValueError, match="must be positive"):
        executor.execute(cmd, ctx)
