"""Cancelling an effect cancels exactly its own delayed work (verify_B2c side finding).

Delayed work was keyed by the effect's (scope, entity) only, and every global effect in a
world shares the key ('global', w): cancelling one dropped the other's delayed work. And
`cancel_effect` cancelled delayed work only when the effect had an `on_interrupt`
pipeline, so a cancelled effect without one still ran its delayed commands later. Delayed
work now also carries its effect instance, and cancelling always cancels it.
"""

from __future__ import annotations

import torch

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.executor import CommandExecutor
from townlet.effects.manager import EffectManager
from townlet.effects.scheduler import Scheduler
from townlet.effects.schema import CommandNode, CommandType

SCHEMA = {"bar.a": "float", "bar.b": "float"}


def _delayed_set(bar: str) -> CommandNode:
    return command_compiler(SCHEMA).compile_command(
        CommandNode(
            type=CommandType.DELAY,
            delay_ticks_expr="2",
            delay_commands=[CommandNode(type=CommandType.MODIFY, path=f"bar.{bar}", value_expr="5.0")],
        )
    )


def _global(effect_id: str, bar: str, *, on_interrupt: list[CommandNode]) -> CompiledEffect:
    return CompiledEffect(
        id=effect_id,
        scope="global",
        duration=50,
        reapply_policy="stack",
        observable=False,
        on_spawn=[_delayed_set(bar)],
        on_tick=[],
        on_despawn=[],
        on_interrupt=on_interrupt,
    )


def _manager(*, interrupt: bool) -> tuple[EffectManager, dict[str, torch.Tensor]]:
    noop = [command_compiler(SCHEMA).compile_command(CommandNode(type=CommandType.MODIFY, path="bar.b", value_expr="bar.b"))]
    on_interrupt = noop if interrupt else []
    catalog = EffectCatalog(
        effects={"first": _global("first", "a", on_interrupt=on_interrupt), "second": _global("second", "b", on_interrupt=on_interrupt)},
        max_active_effects={"global": 4, "agent": 0, "item": 0, "affordance": 0},
    )
    manager = EffectManager(catalog=catalog, command_executor=CommandExecutor(), scheduler=Scheduler(time_enabled=True))
    bars = {"a": torch.zeros(2), "b": torch.zeros(2)}
    return manager, bars


def _run(interrupt: bool) -> dict[str, torch.Tensor]:
    manager, bars = _manager(interrupt=interrupt)
    first = manager.spawn_effect("first", 0, 1.0, 0, bars=bars, vfs_registry=None, world=0)
    manager.spawn_effect("second", 0, 1.0, 0, bars=bars, vfs_registry=None, world=0)
    manager.cancel_effect(first.instance_id, bars=bars, vfs_registry=None, current_step=0)
    for step in range(4):
        manager.tick(bars=bars, vfs_registry=None, current_step=step)
    return bars


def test_cancelling_one_global_effect_keeps_the_other_ones_delayed_work() -> None:
    bars = _run(interrupt=True)
    assert bars["a"].tolist() == [0.0, 0.0]  # the cancelled effect's delayed write never ran
    assert bars["b"].tolist() == [5.0, 0.0]  # the other effect in the same world still ran its own


def test_cancelling_an_effect_without_on_interrupt_still_cancels_its_delayed_work() -> None:
    bars = _run(interrupt=False)
    assert bars["a"].tolist() == [0.0, 0.0]
    assert bars["b"].tolist() == [5.0, 0.0]
