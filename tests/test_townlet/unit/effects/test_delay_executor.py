"""Integration tests for delay command with scheduler."""

import pytest
import torch

from townlet.effects.catalog import EffectCatalog
from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.scheduler import Scheduler
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def _delay_command(ticks: str, do_cmds: list[CommandNode]) -> CommandNode:
    return CommandNode(type=CommandType.DELAY, delay_ticks_expr=ticks, delay_commands=do_cmds)


def _modify(path: str, value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)


def test_delay_rejects_non_int_ticks():
    node = _delay_command("true", [_modify("bar.energy", "1")])
    compiler = CommandCompiler(schema={"bar.energy": "int"})
    with pytest.raises(TypeCheckError, match="int"):
        compiler.compile_command(node)


def test_delay_enqueues_and_executes_after_ticks():
    # Build delay command: after 2 ticks, set bar.energy to 5
    delay_cmd = _delay_command("2", [_modify("bar.energy", "5")])
    schema = {"bar.energy": "int"}
    compiler = CommandCompiler(schema)
    compiled_delay = compiler.compile_command(delay_cmd)

    scheduler = Scheduler(time_enabled=True)
    manager = EffectManager(catalog=EffectCatalog(effects={}), command_executor=CommandExecutor(), scheduler=scheduler)

    from townlet.effects.context import ExecutionContext

    context = ExecutionContext(bars={"energy": torch.tensor(0)}, scheduler=scheduler)
    executor = manager.command_executor

    # Execute delay at tick 0 -> should enqueue
    executor.execute(compiled_delay, context)
    assert scheduler.pending  # something enqueued

    # Advance to tick 1: nothing due
    scheduler.advance(1)
    assert scheduler.drain_due() == []

    # Advance to tick 2: command should run
    due = scheduler.advance(2)
    for item in due:
        for cmd in item.commands:
            executor.execute(cmd, context)

    assert torch.equal(context.bars["energy"], torch.tensor(5))


def test_delay_runs_through_effect_manager_tick():
    # delay 2 ticks then modify energy via manager tick scheduling
    delay_cmd = _delay_command("2", [_modify("bar.energy", "5")])
    schema = {"bar.energy": "int"}
    compiler = CommandCompiler(schema)
    compiled_delay = compiler.compile_command(delay_cmd)

    scheduler = Scheduler(time_enabled=True)
    manager = EffectManager(catalog=EffectCatalog(effects={}), command_executor=CommandExecutor(), scheduler=scheduler)

    bars = {"energy": torch.tensor(0)}
    context = ExecutionContext(bars=bars, scheduler=scheduler, self_index=0)
    executor = manager.command_executor

    executor.execute(compiled_delay, context)

    manager.tick(bars=bars, vfs_registry=None, current_step=0)
    manager.tick(bars=bars, vfs_registry=None, current_step=1)
    assert torch.equal(bars["energy"], torch.tensor(0))

    manager.tick(bars=bars, vfs_registry=None, current_step=2)
    assert torch.equal(bars["energy"], torch.tensor(5))


def test_delay_cancelled_on_effect_despawn():
    # Effect with duration 1 schedules a delayed modify; despawn should cancel pending
    delay_cmd = _delay_command("5", [_modify("bar.energy", "5")])
    schema = {"bar.energy": "int"}
    compiler = CommandCompiler(schema)
    compiled_delay = compiler.compile_command(delay_cmd)

    # Build a minimal compiled effect with on_tick containing delay
    from townlet.effects.catalog import CompiledEffect

    effect_def = CompiledEffect(
        id="delayer",
        scope="agent",
        duration=1,
        intensity=1.0,
        reapply_policy="stack",
        observable=False,
        on_spawn=[],
        on_tick=[compiled_delay],
        on_despawn=[],
        on_interrupt=[],
    )

    catalog = EffectCatalog(effects={"delayer": effect_def})
    scheduler = Scheduler(time_enabled=True)
    manager = EffectManager(catalog=catalog, command_executor=CommandExecutor(), scheduler=scheduler)

    bars = {"energy": torch.tensor(0)}

    # Spawn effect and tick once -> schedules delay for tick 5, then effect expires
    manager.spawn_effect(
        effect_id="delayer",
        target_entity_id=0,
        scope=manager.catalog.effects["delayer"].scope,  # type: ignore[arg-type]
        duration=1,
        intensity=1.0,
        current_step=0,
        bars=bars,
        vfs_registry=None,
    )

    manager.tick(bars=bars, vfs_registry=None, current_step=0)

    # Effect duration should now be 0 and despawned; scheduler should be cleared
    assert not scheduler.pending
