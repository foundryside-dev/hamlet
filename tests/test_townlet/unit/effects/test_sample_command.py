"""Tests for SAMPLE command compilation and execution."""

from __future__ import annotations

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def _compile(cmd: CommandNode, schema: dict[str, str]) -> CommandNode:
    return CommandCompiler(schema=schema).compile_command(cmd)


def test_sample_uniform_compiles_and_executes_deterministically(cpu_device):
    cmd = CommandNode(
        type=CommandType.SAMPLE,
        sample_distribution="uniform",
        sample_params={"min": 0.0, "max": 1.0},
        sample_store_path="bar.energy",
    )
    compiled = _compile(cmd, schema={"bar.energy": "float"})

    bars_a = {"energy": torch.zeros(3, device=cpu_device)}
    bars_b = {"energy": torch.zeros(3, device=cpu_device)}

    ctx_a = ExecutionContext(bars=bars_a, seed=123, current_tick=5)
    ctx_b = ExecutionContext(bars=bars_b, seed=123, current_tick=5)

    executor = CommandExecutor()
    executor.execute(compiled, ctx_a)
    executor.execute(compiled, ctx_b)

    assert torch.all((bars_a["energy"] >= 0.0) & (bars_a["energy"] <= 1.0))
    # Same seed/current_tick should yield identical samples
    assert torch.allclose(bars_a["energy"], bars_b["energy"])


def test_sample_bernoulli_respects_probability(cpu_device):
    cmd = CommandNode(
        type=CommandType.SAMPLE,
        sample_distribution="bernoulli",
        sample_params={"p": 1.0},
        sample_store_path="bar.flag",
    )
    compiled = _compile(cmd, schema={"bar.flag": "float"})

    bars = {"flag": torch.zeros(2, device=cpu_device)}
    ctx = ExecutionContext(bars=bars, seed=1)
    CommandExecutor().execute(compiled, ctx)

    assert torch.allclose(bars["flag"], torch.ones_like(bars["flag"]))


def test_sample_categorical_returns_int_indices(cpu_device):
    cmd = CommandNode(
        type=CommandType.SAMPLE,
        sample_distribution="categorical",
        sample_params={"probs": [0.1, 0.9]},
        sample_store_path="bar.class_id",
    )
    compiled = _compile(cmd, schema={"bar.class_id": "int"})

    bars = {"class_id": torch.zeros(1, device=cpu_device, dtype=torch.long)}
    ctx = ExecutionContext(bars=bars, seed=7)
    CommandExecutor().execute(compiled, ctx)

    assert bars["class_id"].dtype == torch.long
    assert bars["class_id"].item() in (0, 1)


def test_sample_missing_param_rejected():
    cmd = CommandNode(
        type=CommandType.SAMPLE,
        sample_distribution="uniform",
        sample_params={"min": 0.0},  # missing max
        sample_store_path="bar.energy",
    )
    compiler = CommandCompiler(schema={"bar.energy": "float"})
    with pytest.raises(TypeCheckError):
        compiler.compile_command(cmd)
