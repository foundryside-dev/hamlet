"""Effects-layer tests for global-scope resolution (hamlet-cf16cdb6c4, S1 per-world globals).

A global-scoped VFS tensor leads with the world axis (S1: one world per agent), then its
declared payload. An effects context bound to an agent reads and writes that agent's
world's value as a whole payload; it never gathers the payload's first axis by agent
rows, and never touches another world's row.
"""

import pytest
import torch

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _make_registry(num_agents: int = 2) -> VariableRegistry:
    variables = [
        VariableDef(
            id="grid",
            scope="global",
            type="tensor2d",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=0.0,
            shape=[3, 3],
        ),
        VariableDef(
            id="mood",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=["engine"],
            default=0.0,
        ),
    ]
    return VariableRegistry(variables=variables, num_agents=num_agents, device=torch.device("cpu"))


def _make_context(registry: VariableRegistry, target_index: int | None = 1) -> ExecutionContext:
    return ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs_registry=registry,
        self_index=None,
        target_index=target_index,
    )


def test_effect_expression_reads_and_writes_global_tensor_whole():
    """modify vfs.<global> with a value expression reading the container back works whole-container.

    This is the exact route Trial B's blind run recorded as rejected:
    value expression 'grid' gathered to (batch, ...) and registry.set refused the shape.
    """
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="grid", value_expr="grid + 1.0")
    compiler = command_compiler({"grid": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert result.shape == (2, 3, 3)  # [worlds, 3, 3]
    assert torch.equal(result[1], torch.ones(3, 3))  # the interacting agent's world, whole
    assert torch.equal(result[0], torch.zeros(3, 3))  # the other world is untouched


def test_effect_expression_global_root_reads_global_tensor():
    """The explicit <name> root works end-to-end through compile and execute."""
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="grid", value_expr="grid + 2.0")
    compiler = command_compiler({"grid": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert torch.equal(result[1], torch.full((3, 3), 2.0))
    assert torch.equal(result[0], torch.zeros(3, 3))


def test_global_vfs_write_path_lands_in_the_contexts_world():
    """`<id>` is a write spelling too: the effects schema admits it, so the runtime serves it."""
    registry = _make_registry()
    context = _make_context(registry, target_index=0)

    command = CommandNode(type=CommandType.MODIFY, path="grid", value_expr="grid + 3.0")
    command_compiler({"grid": "float"}).compile_command(command)
    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert torch.equal(result[0], torch.full((3, 3), 3.0))
    assert torch.equal(result[1], torch.zeros(3, 3))


def test_a_row_write_to_a_global_writes_the_whole_payload_of_one_world():
    """A row write never slab-writes container[agent_index] of the payload (hamlet-57a5126baa):
    the row a global has is its world's, and the payload is written whole.

    The effects schema never admits `<global>`; this simulates a stale artifact.
    """
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="grid", value_expr="0.5")
    compiler = command_compiler({"grid": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert torch.equal(result[1], torch.full((3, 3), 0.5))
    assert torch.equal(result[0], torch.zeros(3, 3))


def test_target_vfs_write_to_agent_var_still_works():
    """The per-agent target write path is untouched for agent-scoped variables."""
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="mood", value_expr="0.7")
    compiler = command_compiler({"mood": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    mood = registry.get("mood", reader="engine")
    assert mood[1].item() == pytest.approx(0.7)
    assert mood[0].item() == pytest.approx(0.0)


@pytest.mark.parametrize("path", ["sealed"])
def test_effect_writes_enforce_writable_by(path: str):
    """Every effects write route commits through registry.set: writable_by is
    enforced and a refused write leaves storage untouched (hamlet-57a5126baa).

    The route mutates a clone from registry.get, never registry storage, so an
    authorization refusal cannot leave a partial write behind.
    """
    variables = [
        VariableDef(
            id="sealed",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "engine"],
            writable_by=[],  # engine is not an authorized writer
            default=0.0,
        ),
    ]
    registry = VariableRegistry(variables=variables, num_agents=2, device=torch.device("cpu"))
    context = ExecutionContext(
        bars={"energy": torch.tensor([0.5, 0.8])},
        vfs_registry=registry,
        self_index=0,
        target_index=1,
    )

    command = CommandNode(type=CommandType.MODIFY, path=path, value_expr="0.7")
    command_compiler({path: "float"}).compile_command(command)

    with pytest.raises(PermissionError, match="not allowed to write"):
        CommandExecutor().execute(command, context)

    assert torch.equal(registry.get("sealed", reader="engine"), torch.zeros(2))
