"""Tests for trigger_cascade command execution and validation."""

from __future__ import annotations

import pytest
import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs import VTCThresholdCascadeProgram, compile_vtc_threshold_cascades
from townlet.world.expression.parser import ExpressionParser


def _make_threshold_cascade_program() -> VTCThresholdCascadeProgram:
    return compile_vtc_threshold_cascades(
        [
            {"id": "health_drop", "source": "energy", "target": "health", "threshold": 0.5, "strength": 0.2},
        ]
    )


def test_trigger_cascade_applies_penalty():
    meters = {"energy": torch.tensor([0.25, 0.75]), "health": torch.tensor([1.0, 1.0])}
    ctx = ExecutionContext(bars=meters, threshold_cascade_program=_make_threshold_cascade_program())
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
    assert torch.isclose(ctx.bars["health"][0], torch.tensor(1.0 - 0.2 * ((0.5 - 0.25) / 0.5)))
    # Second agent above threshold: unchanged
    assert torch.isclose(ctx.bars["health"][1], torch.tensor(1.0))


def test_trigger_cascade_rejects_unknown_id():
    ctx = ExecutionContext(
        bars={"energy": torch.ones(1), "health": torch.ones(1)},
        threshold_cascade_program=_make_threshold_cascade_program(),
    )
    cmd = CommandNode(type=CommandType.TRIGGER_CASCADE, cascade_id="missing", cascade_strength=1.0)
    executor = CommandExecutor()
    with pytest.raises(ValueError, match="Unknown cascade_id"):
        executor.execute(cmd, ctx)


def test_trigger_cascade_rejects_nonpositive_strength():
    ctx = ExecutionContext(
        bars={"energy": torch.ones(1), "health": torch.ones(1)},
        threshold_cascade_program=_make_threshold_cascade_program(),
    )
    cmd = CommandNode(type=CommandType.TRIGGER_CASCADE, cascade_id="health_drop", cascade_strength=0.0)
    executor = CommandExecutor()
    with pytest.raises(ValueError, match="must be positive"):
        executor.execute(cmd, ctx)
