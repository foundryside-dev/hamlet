"""Tests for dynamic affordance availability toggles via Effects (per world, S1)."""

from __future__ import annotations

import torch

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.world.expression.parser import ExpressionParser


def _toggle(value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path="affordance.bank.available", value_ast=ExpressionParser().parse(value))


def test_modify_affordance_availability_updates_only_the_pipelines_world():
    overrides: list[dict[str, bool]] = [{}, {}]
    bars = {"energy": torch.ones(2)}
    ctx = ExecutionContext(bars=bars, affordance_overrides=overrides, target_index=1)
    executor = CommandExecutor()

    executor.execute(_toggle("false"), ctx)

    assert overrides == [{}, {"bank": False}]
    value = ctx.get_path("affordance.bank.available")
    assert isinstance(value, torch.Tensor)
    assert value.item() is False
    # World 0 still sees the declared availability.
    assert ctx.copy(target_index=0).get_path("affordance.bank.available").item() is True

    executor.execute(_toggle("true"), ctx)
    assert overrides == [{}, {"bank": True}]


def test_a_context_bound_to_no_world_toggles_every_live_world():
    overrides: list[dict[str, bool]] = [{}, {}, {}]
    ctx = ExecutionContext(bars={"energy": torch.ones(3)}, affordance_overrides=overrides, write_mask=torch.tensor([True, False, True]))

    CommandExecutor().execute(_toggle("false"), ctx)

    assert overrides == [{"bank": False}, {}, {"bank": False}]


def test_affordance_open_mask_applies_each_worlds_override_first():
    class DummyEnv:
        def __init__(self) -> None:
            self.affordance_overrides = [{"cafe": False}, {"library": False}]
            self.enable_temporal_mechanics = False
            self.time_of_day = 0
            self.device = torch.device("cpu")

        def _is_affordance_open(self, name: str, hour: int | None = None) -> bool:
            return VectorizedHamletEnv._is_affordance_open(self, name, hour)  # type: ignore[arg-type]

    dummy = DummyEnv()

    assert VectorizedHamletEnv._affordance_open_mask(dummy, "cafe").tolist() == [False, True]  # type: ignore[arg-type]
    assert VectorizedHamletEnv._affordance_open_mask(dummy, "library").tolist() == [True, False]  # type: ignore[arg-type]
