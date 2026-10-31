"""`gather` and `scatter` index one world's element axis, never the batch (owner ruling S1).

They indexed dim 0 unconditionally, and dim 0 of every registry or bar read is the batch
of independent worlds: `gather(bar.energy, 2)` in world 0's effect read world 2's energy
(verify_B2c L3). The type checker now proves the index has an element axis to address
(the first argument is a vector or a tensor1d) and the evaluator indexes that axis in every
row, so the value one world computes never depends on another world's state. A `reduce`
over a bare `bar.X` was already refused (a scalar is not a collection).
"""

from __future__ import annotations

import pytest
import torch

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef
from townlet.world.expression.type_checker import TypeCheckError

SCHEMA = {
    "bar.energy": "float",
    "inv": "vecNf",
    "pick": "float",
}


def _modify(path: str, value: str) -> CommandNode:
    return command_compiler(SCHEMA).compile_command(CommandNode(type=CommandType.MODIFY, path=path, value_expr=value))


@pytest.mark.parametrize("expression", ["gather(bar.energy, 2)", "scatter(bar.energy, 0, 9.0)", "gather(bar.energy, 0)"])
def test_indexing_a_scalar_value_is_refused_at_compile(expression: str) -> None:
    with pytest.raises(TypeCheckError, match="only row axis is the batch of independent worlds"):
        _modify("bar.energy", expression)


def _registry(inv: torch.Tensor) -> VariableRegistry:
    variables = [
        VariableDef(
            id="inv",
            scope="agent",
            type="vecNf",
            dims=3,
            lifetime="episode",
            readable_by=["engine"],
            writable_by=["engine"],
            default=[0.0, 0.0, 0.0],
        ),
        VariableDef(
            id="pick", scope="agent", type="scalar", lifetime="episode", readable_by=["engine"], writable_by=["engine"], default=0.0
        ),
    ]
    registry = VariableRegistry(variables=variables, num_agents=3, device=torch.device("cpu"))
    registry.set("inv", inv, writer="engine")
    return registry


def _world2_pipeline(inv: torch.Tensor, command: CommandNode) -> VariableRegistry:
    registry = _registry(inv)
    CommandExecutor().execute(command, ExecutionContext(bars={"energy": torch.ones(3)}, vfs_registry=registry, target_index=2))
    return registry


def test_gather_reads_an_element_of_its_own_worlds_vector_whatever_another_world_holds() -> None:
    command = _modify("pick", "gather(inv, 1)")
    base = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    other = base.clone()
    other[0] = torch.tensor([-1.0, -2.0, -3.0])  # only world 0 differs

    for inv in (base, other):
        pick = _world2_pipeline(inv, command).get("pick", reader="engine")
        assert pick.tolist() == [0.0, 0.0, 8.0]


def test_scatter_writes_an_element_of_its_own_worlds_vector() -> None:
    command = _modify("inv", "scatter(inv, 0, 9.0)")
    inv = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    after = _world2_pipeline(inv, command).get("inv", reader="engine")
    assert torch.equal(after[:2], inv[:2])
    assert after[2].tolist() == [9.0, 8.0, 9.0]


def test_an_index_outside_the_element_axis_refuses() -> None:
    command = _modify("pick", "gather(inv, 3)")
    with pytest.raises(ValueError, match="outside the element axis"):
        _world2_pipeline(torch.zeros(3, 3), command)
