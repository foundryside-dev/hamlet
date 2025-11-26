"""Tests for dynamic affordance availability toggles via Effects."""

from __future__ import annotations

import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.world.expression.parser import ExpressionParser


def test_modify_affordance_availability_updates_overrides():
    overrides: dict[str, bool] = {}
    bars = {"energy": torch.ones(2)}
    ctx = ExecutionContext(bars=bars, affordance_overrides=overrides)
    parser = ExpressionParser()
    cmd = CommandNode(
        type=CommandType.MODIFY,
        path="affordance.bank.available",
        value_ast=parser.parse("false"),
    )
    executor = CommandExecutor()

    executor.execute(cmd, ctx)

    assert overrides["bank"] is False
    # Subsequent reads should return a tensor bool
    value = ctx.get_path("affordance.bank.available")
    assert isinstance(value, torch.Tensor)
    assert value.item() is False

    cmd_enable = CommandNode(
        type=CommandType.MODIFY,
        path="affordance.bank.available",
        value_ast=parser.parse("true"),
    )
    executor.execute(cmd_enable, ctx)
    assert overrides["bank"] is True


def test_is_affordance_open_respects_overrides_first():
    class DummyEnv:
        def __init__(self) -> None:
            self.affordance_overrides = {"cafe": False, "library": True}
            self.enable_temporal_mechanics = False
            self.action_mask_table = torch.ones(1, 1)  # required fields for helper
            self.affordance_name_to_mask_idx = {"cafe": 0, "library": 0}
            self.hours_per_day = 1
            self.time_of_day = 0

    dummy = DummyEnv()

    assert VectorizedHamletEnv._is_affordance_open(dummy, "cafe") is False
    assert VectorizedHamletEnv._is_affordance_open(dummy, "library") is True
