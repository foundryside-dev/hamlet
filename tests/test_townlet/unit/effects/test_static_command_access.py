"""Compound dynamic commands authorize all targets before their own mutation."""

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def test_constructed_parallel_denial_preserves_earlier_target() -> None:
    registry = VariableRegistry(
        [
            VariableDef(
                id=name, scope="global", type="scalar", lifetime="episode", default=2.0, readable_by=["engine"], writable_by=writers
            )
            for name, writers in [("allowed", ["engine"]), ("constant", [])]
        ],
        2,
        torch.device("cpu"),
    )
    command = CommandCompiler({"vfs.allowed": "float", "vfs.constant": "float"}).compile_command(
        CommandNode(
            type=CommandType.PARALLEL,
            parallel_commands=[
                CommandNode(type=CommandType.MODIFY, path="vfs.allowed", value_expr="9.0"),
                CommandNode(type=CommandType.MODIFY, path="vfs.constant", value_expr="2.0"),
            ],
        )
    )
    ctx = ExecutionContext(vfs_registry=registry)
    before = {name: registry.get(name, reader="engine") for name in ["allowed", "constant"]}
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, ctx)
    for name, value in before.items():
        assert torch.equal(registry.get(name, reader="engine"), value)


def test_constructed_for_each_denial_precedes_first_bar_mutation() -> None:
    registry = VariableRegistry(
        [VariableDef(id="constant", scope="agent", type="scalar", lifetime="episode", default=2.0, readable_by=["engine"], writable_by=[])],
        2,
        torch.device("cpu"),
    )
    command = CommandCompiler({"target.bar.energy": "float", "target.vfs.constant": "float"}).compile_command(
        CommandNode(
            type=CommandType.FOR_EACH,
            collection="all_agents",
            iterator="agent",
            body=[
                CommandNode(type=CommandType.MODIFY, path="target.bar.energy", value_expr="9.0"),
                CommandNode(type=CommandType.MODIFY, path="target.vfs.constant", value_expr="2.0"),
            ],
        )
    )
    ctx = ExecutionContext(vfs_registry=registry, bars={"energy": torch.full((2,), 3.0)})
    before = ctx.bars["energy"].clone()
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, ctx)
    assert torch.equal(ctx.bars["energy"], before)


def test_denied_sample_does_not_advance_random_generator() -> None:
    registry = VariableRegistry(
        [
            VariableDef(
                id="constant", scope="global", type="scalar", lifetime="episode", default=2.0, readable_by=["engine"], writable_by=[]
            )
        ],
        2,
        torch.device("cpu"),
    )
    command = CommandCompiler({"vfs.constant": "float"}).compile_command(
        CommandNode(
            type=CommandType.SAMPLE, sample_store_path="vfs.constant", sample_distribution="uniform", sample_params={"min": 0.0, "max": 1.0}
        )
    )
    generator = torch.Generator().manual_seed(123)
    ctx = ExecutionContext(vfs_registry=registry, rng=generator)
    before = generator.get_state().clone()
    with pytest.raises(PermissionError, match="constant"):
        CommandExecutor().execute(command, ctx)
    assert torch.equal(generator.get_state(), before)
