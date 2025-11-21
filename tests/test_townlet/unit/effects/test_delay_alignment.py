"""Ensure delay commands scheduled with current_tick anchor to the right tick."""

import torch

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.scheduler import Scheduler
from townlet.effects.schema import CommandNode, CommandType


def _delay_cmd(ticks: str, path: str, value: str) -> CommandNode:
    return CommandNode(
        type=CommandType.DELAY,
        delay_ticks_expr=ticks,
        delay_commands=[CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)],
    )


def test_delay_respects_current_tick_anchor():
    # Build delay command: zero-delay should fire at current_tick anchor
    delay_cmd = _delay_cmd("0", "bar.energy", "5")
    schema = {"bar.energy": "int"}
    compiler = CommandCompiler(schema)
    compiled = compiler.compile_command(delay_cmd)

    scheduler = Scheduler(time_enabled=True)
    executor = CommandExecutor()

    bars = {"energy": torch.tensor([0], dtype=torch.int)}
    ctx = ExecutionContext(bars=bars, scheduler=scheduler, current_tick=10)

    # Execute delay -> should enqueue for due_tick=10
    executor.execute(compiled, ctx)
    due = scheduler.advance(10)
    assert due and due[0].due_tick == 10

    # Run due commands
    for item in due:
        for cmd in item.commands:
            executor.execute(cmd, ctx)

    assert torch.equal(bars["energy"], torch.tensor([5]))
