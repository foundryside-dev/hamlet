"""Effects-layer tests for global-scope resolution (hamlet-cf16cdb6c4 / A-G1, A-G2 scope guard).

A global-scoped VFS tensor's first axis is spatial, not an agent axis. Every route
here previously treated it as agent-scoped: the eval context gathered it by
arange(batch), the target/self view builder sliced its first axis by agent index,
and target.vfs writes slab-wrote container[agent_index].
"""

import pytest
import torch

from townlet.effects.compiler import CommandCompiler
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
    value expression 'vfs.grid' gathered to (batch, ...) and registry.set refused the shape.
    """
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="vfs.grid", value_expr="vfs.grid + 1.0")
    compiler = CommandCompiler(schema={"vfs.grid": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert result.shape == (3, 3)
    assert torch.equal(result, torch.ones(3, 3))


def test_effect_expression_global_root_reads_global_tensor():
    """The explicit global.vfs.<name> root works end-to-end through compile and execute."""
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="vfs.grid", value_expr="global.vfs.grid + 2.0")
    compiler = CommandCompiler(schema={"vfs.grid": "float", "global.vfs.grid": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    result = registry.get("grid", reader="engine")
    assert result.shape == (3, 3)
    assert torch.equal(result, torch.full((3, 3), 2.0))


def test_target_vfs_write_to_global_raises():
    """modify target.vfs.<global> must refuse loudly, not slab-write container[agent_index].

    The slab write is A-G2's accidental route (hamlet-57a5126baa): it indexes the
    container's first SPATIAL axis by agent index.
    """
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    # Schema deliberately includes the stale target path, simulating a pre-fix artifact:
    # the runtime must still refuse.
    command = CommandNode(type=CommandType.MODIFY, path="target.vfs.grid", value_expr="0.5")
    compiler = CommandCompiler(schema={"target.vfs.grid": "float"})
    compiler.compile_command(command)

    with pytest.raises(ValueError, match="global"):
        CommandExecutor().execute(command, context)

    # And the container is untouched — the refusal happened before any mutation.
    assert torch.equal(registry.get("grid", reader="engine"), torch.zeros(3, 3))


def test_target_vfs_read_of_global_not_available():
    """target.vfs.<global> is not a readable view: globals are excluded from per-entity views."""
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="vfs.mood", value_expr="target.vfs.grid + 1.0")
    compiler = CommandCompiler(schema={"vfs.mood": "float", "target.vfs.grid": "float"})
    compiler.compile_command(command)

    with pytest.raises(KeyError):
        CommandExecutor().execute(command, context)


def test_target_vfs_write_to_agent_var_still_works():
    """The per-agent target write path is untouched for agent-scoped variables."""
    registry = _make_registry()
    context = _make_context(registry, target_index=1)

    command = CommandNode(type=CommandType.MODIFY, path="target.vfs.mood", value_expr="0.7")
    compiler = CommandCompiler(schema={"target.vfs.mood": "float"})
    compiler.compile_command(command)

    CommandExecutor().execute(command, context)

    mood = registry.get("mood", reader="engine")
    assert mood[1].item() == pytest.approx(0.7)
    assert mood[0].item() == pytest.approx(0.0)
