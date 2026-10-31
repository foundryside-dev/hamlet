"""Per-agent command semantics (review-2026-10-24 effects F1, F2; remediation WP2).

F1: a scalar `modify: bar.X` rebound the bar to a stride-0 broadcast view, so the next
per-agent write to the same bar landed on every agent (`probe_d.py` I3 printed
`[0.4, 0.4, 0.4]`). A bar write now copies into the existing tensor, and the executor
checks after every command that no bar was rebound or left as a broadcast view.

F2: the `if` and `switch` commands collapsed a per-agent condition with `.any()` and ran
the branch for every agent (`probe_b.py` F penalised all three agents when one was low).
They are now masked execution: the condition is evaluated per agent and the branch runs
with it as a write mask. A scalar condition is the degenerate mask.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
import yaml

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiler import UniverseCompiler
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "test" / "effects_smoke"
LEVEL = "L0_effects"

SCHEMA = {
    "bar.health": "float",
    "bar.energy": "float",
    "bar.level": "float",
    "counter": "float",
}


def _modify(path: str, value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)


def _if(condition: str, then: list[CommandNode], otherwise: list[CommandNode] | None = None) -> CommandNode:
    return CommandNode(type=CommandType.IF, condition_expr=condition, then_commands=then, else_commands=otherwise or [])


def _compile(node: CommandNode, schema: dict[str, str] = SCHEMA) -> CommandNode:
    return command_compiler(schema).compile_command(node)


def _scalar(var_id: str, *, scope: str) -> VariableDef:
    return VariableDef(
        id=var_id, scope=scope, type="scalar", lifetime="episode", default=0.0, readable_by=["engine"], writable_by=["engine"]
    )


def _bars() -> dict[str, torch.Tensor]:
    return {"health": torch.tensor([1.0, 0.1, 1.0]), "energy": torch.tensor([1.0, 1.0, 1.0])}


def _no_broadcast_stride(tensor: torch.Tensor) -> bool:
    return all(stride != 0 for stride, size in zip(tensor.stride(), tensor.shape, strict=True) if size > 1)


# -- F1: a bar write copies into the existing tensor --------------------------------------


def test_scalar_modify_then_per_agent_modify_hits_one_agent() -> None:
    """probe_d.py I3, under S1: a bare bar write from agent 1's pipeline is world 1's row only."""
    scalar = _compile(_modify("bar.health", "0.3"))
    indexed = _compile(_modify("bar.health", "bar.health + 0.1"))
    bars = {"health": torch.tensor([1.0, 1.0, 1.0])}
    original = bars["health"]
    context = ExecutionContext(bars=bars, target_index=1)
    executor = CommandExecutor()

    executor.execute(scalar, context)
    assert bars["health"] is original
    assert _no_broadcast_stride(bars["health"])
    assert torch.allclose(bars["health"], torch.tensor([1.0, 0.3, 1.0]))

    executor.execute(indexed, context)
    assert torch.allclose(bars["health"], torch.tensor([1.0, 0.4, 1.0]))


def test_scalar_modify_writes_through_a_column_view_of_the_meter_matrix() -> None:
    """The env hands effects `meters[:, i]` column views; the write must land in the matrix."""
    meters = torch.ones(3, 2)
    bars = {"health": meters[:, 0], "energy": meters[:, 1]}
    CommandExecutor().execute(_compile(_modify("bar.health", "0.3")), ExecutionContext(bars=bars))
    assert torch.allclose(meters[:, 0], torch.tensor([0.3, 0.3, 0.3]))
    assert meters[:, 1].tolist() == [1.0, 1.0, 1.0]
    assert bars["health"].data_ptr() == meters.data_ptr()


def test_executor_refuses_a_bar_that_is_a_broadcast_view() -> None:
    bars = {"health": torch.tensor(1.0).expand(3)}
    with pytest.raises(RuntimeError, match="broadcast view"):
        CommandExecutor().execute(_compile(_modify("bar.health", "bar.health")), ExecutionContext(bars=bars))


def test_executor_refuses_a_command_that_rebinds_a_bar() -> None:
    class RebindingContext(ExecutionContext):
        def set_path(self, path: str, value: torch.Tensor) -> None:
            self.bars[path.removeprefix("bar.")] = value.clone()

    context = RebindingContext(bars={"health": torch.tensor([1.0, 1.0, 1.0])})
    with pytest.raises(RuntimeError, match="rebound"):
        CommandExecutor().execute(_compile(_modify("bar.health", "0.3")), context)


# -- F2: if/switch are masked execution ---------------------------------------------------


def test_if_runs_then_and_else_per_agent() -> None:
    command = _compile(
        _if(
            "bar.health < 0.5",
            then=[_modify("bar.energy", "bar.energy - 0.5")],
            otherwise=[_modify("bar.energy", "bar.energy + 0.1")],
        )
    )
    bars = _bars()
    CommandExecutor().execute(command, ExecutionContext(bars=bars))
    assert torch.allclose(bars["energy"], torch.tensor([1.1, 0.5, 1.1]))


def test_if_masks_an_indexed_write_by_the_targets_row() -> None:
    """An agent-scoped effect attached to a healthy agent does not penalise it because another agent is low."""
    command = _compile(_if("bar.health < 0.5", then=[_modify("bar.energy", "bar.energy - 0.5")]))
    bars = _bars()
    executor = CommandExecutor()
    executor.execute(command, ExecutionContext(bars=bars, self_index=0, target_index=0))
    assert bars["energy"].tolist() == [1.0, 1.0, 1.0]
    executor.execute(command, ExecutionContext(bars=bars, self_index=1, target_index=1))
    assert bars["energy"].tolist() == [1.0, 0.5, 1.0]


def test_if_masks_a_bare_agent_vfs_write_by_row() -> None:
    mood = _scalar("mood", scope="agent")
    registry = VariableRegistry([mood], 3, torch.device("cpu"))
    command = _compile(_if("bar.health < 0.5", then=[_modify("mood", "1.0")]), {"bar.health": "float", "mood": "float"})
    bars = _bars()
    executor = CommandExecutor()
    executor.execute(command, ExecutionContext(bars=bars, vfs_registry=registry, target_index=0))
    executor.execute(command, ExecutionContext(bars=bars, vfs_registry=registry, target_index=1))
    assert registry.get("mood", reader="engine").tolist() == [0.0, 1.0, 0.0]


def test_nested_if_intersects_masks() -> None:
    inner = _if("bar.energy > 0.5", then=[_modify("bar.energy", "0.0")])
    command = _compile(_if("bar.health < 0.5", then=[inner]))
    bars = {"health": torch.tensor([0.1, 0.1, 1.0]), "energy": torch.tensor([1.0, 0.2, 1.0])}
    CommandExecutor().execute(command, ExecutionContext(bars=bars))
    assert torch.allclose(bars["energy"], torch.tensor([0.0, 0.2, 1.0]))


def test_scalar_condition_is_the_degenerate_mask() -> None:
    command = _compile(
        _if("bar.health < 0.5", then=[_modify("bar.energy", "0.0")], otherwise=[_modify("bar.energy", "0.5")]),
    )
    bars = _bars()
    executor = CommandExecutor()
    # Each pipeline is bound to its agent's world: its bare bar write is that row only.
    executor.execute(command, ExecutionContext(bars=bars, target_index=1))
    assert bars["energy"].tolist() == [1.0, 0.0, 1.0]
    executor.execute(command, ExecutionContext(bars=bars, target_index=0))
    assert bars["energy"].tolist() == [0.5, 0.0, 1.0]


def test_partial_mask_writes_a_global_in_the_live_worlds_only() -> None:
    """A global has one row per world (S1), so a per-agent mask is a per-world mask on it."""
    counter = _scalar("counter", scope="global")
    registry = VariableRegistry([counter], 3, torch.device("cpu"))
    command = _compile(_if("bar.health < 0.5", then=[_modify("counter", "1.0")]))
    CommandExecutor().execute(command, ExecutionContext(bars=_bars(), vfs_registry=registry))
    assert registry.get("counter", reader="engine").tolist() == [0.0, 1.0, 0.0]


def test_whole_batch_mask_writes_a_global_target() -> None:
    counter = _scalar("counter", scope="global")
    registry = VariableRegistry([counter], 3, torch.device("cpu"))
    command = _compile(_if("bar.health < 2.0", then=[_modify("counter", "1.0")]))
    CommandExecutor().execute(command, ExecutionContext(bars=_bars(), vfs_registry=registry))
    assert registry.get("counter", reader="engine").tolist() == [1.0, 1.0, 1.0]


def test_switch_selects_a_case_per_agent_first_match_wins() -> None:
    command = _compile(
        CommandNode(
            type=CommandType.SWITCH,
            switch_expr="bar.level",
            cases=[
                ("1.0", [_modify("bar.energy", "0.1")]),
                ("2.0", [_modify("bar.energy", "0.2")]),
                ("bar.level", [_modify("bar.energy", "0.3")]),  # matches everyone; only agents no earlier case took
            ],
            default_commands=[_modify("bar.energy", "0.9")],
        )
    )
    bars = {"level": torch.tensor([1.0, 2.0, 3.0, 2.0]), "energy": torch.zeros(4)}
    CommandExecutor().execute(command, ExecutionContext(bars=bars))
    assert torch.allclose(bars["energy"], torch.tensor([0.1, 0.2, 0.3, 0.2]))


def test_switch_default_runs_for_the_agents_no_case_took() -> None:
    command = _compile(
        CommandNode(
            type=CommandType.SWITCH,
            switch_expr="bar.level",
            cases=[("1.0", [_modify("bar.energy", "0.1")])],
            default_commands=[_modify("bar.energy", "0.9")],
        )
    )
    bars = {"level": torch.tensor([1.0, 2.0, 3.0]), "energy": torch.zeros(3)}
    CommandExecutor().execute(command, ExecutionContext(bars=bars))
    assert torch.allclose(bars["energy"], torch.tensor([0.1, 0.9, 0.9]))


def test_spawn_effect_under_a_mask_is_the_target_agents_decision() -> None:
    spawned: list[int] = []

    class Manager:
        current_step = 0
        catalog = SimpleNamespace(get=lambda effect_id: SimpleNamespace(scope="agent"))

        def spawn_effect(self, **kwargs: object) -> None:
            spawned.append(int(kwargs["target_entity_id"]))  # type: ignore[call-overload]

    spawn = CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="weak", target="target", intensity=1.0)
    command = _compile(_if("bar.health < 0.5", then=[spawn]))
    executor = CommandExecutor()
    for agent in range(3):
        executor.execute(command, ExecutionContext(bars=_bars(), effect_manager=Manager(), self_index=agent, target_index=agent))
    assert spawned == [1]


def test_delay_under_a_partial_mask_carries_the_mask_to_the_delayed_block() -> None:
    delay = CommandNode(type=CommandType.DELAY, delay_ticks_expr="1", delay_commands=[_modify("bar.energy", "0.0")])
    command = _compile(_if("bar.health < 0.5", then=[delay]))
    scheduled: list[dict] = []
    scheduler = SimpleNamespace(schedule=lambda **kw: scheduled.append(kw))
    bars = _bars()
    CommandExecutor().execute(command, ExecutionContext(bars=bars, scheduler=scheduler))
    assert len(scheduled) == 1
    mask = scheduled[0]["context_overrides"]["write_mask"]
    assert mask.tolist() == [False, True, False]
    # The scheduler rebuilds the delayed context from these overrides (manager
    # _execute_scheduled_items pops write_mask); the delayed block then writes only the
    # agents that satisfied the condition when it was scheduled.
    executor = CommandExecutor()
    for cmd in scheduled[0]["commands"]:
        executor.execute(cmd, ExecutionContext(bars=bars, write_mask=mask))
    assert bars["energy"].tolist() == [1.0, 0.0, 1.0]


# -- probe_b.py F, end to end through the compiled pack ------------------------------------


def _pack(tmp_path: Path, on_tick: list[dict]) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    (pack / "effects.yaml").write_text(
        yaml.safe_dump(
            {
                "version": "1.0",
                "max_active_effects": {"global": 0, "agent": 1, "item": 0, "affordance": 0},
                "effect_definitions": [
                    {
                        "id": "crisis",
                        "scope": "agent",
                        "duration": 5,
                        "reapply_policy": "renew",
                        "observable": False,
                        "on_spawn": [],
                        "on_tick": on_tick,
                        "on_despawn": [],
                        "on_interrupt": [],
                    }
                ],
            },
            sort_keys=False,
        )
    )
    return pack


def test_if_on_a_per_agent_condition_penalises_only_the_low_agent(tmp_path: Path) -> None:
    """probe_b.py F: health [1.0, 0.1, 1.0]; only agent 1 loses 0.5 energy."""
    pack = _pack(tmp_path, [{"if": "bar.health < 0.5", "then": [{"modify": "bar.energy", "value": "bar.energy - 0.5"}], "else": []}])
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=3, level_name=LEVEL, device="cpu")
    env.reset()
    health, energy = env.meter_name_to_index["health"], env.meter_name_to_index["energy"]
    env.meters[1, health] = 0.1
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    # S1: each world gets its own crisis; the condition holds in world 1 only.
    for agent in range(3):
        env.effect_manager.spawn_effect(
            "crisis",
            target_entity_id=agent,
            intensity=1.0,
            current_step=env.global_tick,
            bars=bars,
            vfs_registry=env.vfs_registry,
            agent_positions=env.positions,
            item_manager=env.item_manager,
        )
    env.step(torch.full((3,), env.action_dim - 1, dtype=torch.long))  # WAIT

    after = env.meters[:, energy]
    assert after[0].item() == pytest.approx(after[2].item())
    assert after[1].item() == pytest.approx(after[0].item() - 0.5)
