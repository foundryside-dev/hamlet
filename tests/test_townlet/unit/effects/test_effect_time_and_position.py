"""Effects read time and position (remediation effects WP3; hamlet-a737e444c0; findings F5, F9).

`probe_a.py` C: `tick` refused at compile in an effect (`Reference traversal requires schema
entry`) because the effects schema was built from authored declarations only and the engine
publishes `tick` as an ambient global. It is now in the schema by bare name, as in VFS profiles.

`probe_a.py` D: `distance_to_affordance("FOOD")` compiled and then raised `Spatial operators
require agent_positions` at the first tick: the env never handed positions to
`EffectManager.tick`. It now hands agent positions, affordance positions and the substrate,
and every lifecycle context carries them.

`probe_d.py` Z: `lag(...)` compiled inside an effect and raised `Temporal operators require a
TemporalHistory` at runtime. Command pipelines keep no history, so history functions refuse at
compile and name the VFS-profile surface where they work.

`probe_a.py` B3 (`nearby_agents` by the declared metric) is gone with the collection: under
owner ruling S1 no other agent shares an agent's world, so it was always empty and was deleted.

The original probes build on a scratch copy of `effects_smoke` that the branch has since moved
past, so these tests rebuild each assertion on the current pack.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.world.expression.type_checker import TypeCheckError

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "test" / "effects_smoke"
LEVEL = "L0_effects"
BUDGET = {"global": 1, "agent": 1, "item": 0, "affordance": 0}


def _effect(effect_id: str, *, scope: str, on_tick: list[dict]) -> dict:
    return {
        "id": effect_id,
        "scope": scope,
        "duration": 50,
        "reapply_policy": "renew",
        "observable": False,
        "on_spawn": [],
        "on_tick": on_tick,
        "on_despawn": [],
        "on_interrupt": [],
    }


def _pack(tmp_path: Path, effect: dict, *, metric: str | None = None) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    effects = {"version": "1.0", "effect_definitions": [effect], "max_active_effects": BUDGET}
    (pack / "effects.yaml").write_text(yaml.safe_dump(effects, sort_keys=False))
    if metric is not None:
        stratum = yaml.safe_load((pack / "stratum.yaml").read_text())
        stratum["stratum"]["substrate"]["grid"]["distance_metric"] = metric
        (pack / "stratum.yaml").write_text(yaml.safe_dump(stratum, sort_keys=False))
    return pack


def _env(pack: Path, num_agents: int):
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    env.reset()
    return env


def _spawn(env, effect_id: str, target: int = 0, *, world: int | None = None) -> None:
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    env.effect_manager.spawn_effect(
        effect_id,
        target_entity_id=target,
        intensity=1.0,
        current_step=env.global_tick,
        bars=bars,
        vfs_registry=env.vfs_registry,
        world=world,
    )


def _spawn_in_every_world(env, effect_id: str) -> None:
    """S1: an agent-scoped effect per agent, each in its own world."""
    for agent in range(env.num_agents):
        _spawn(env, effect_id, agent)


def _wait(env) -> None:
    env.step(torch.full((env.num_agents,), env.action_dim - 1, dtype=torch.long))


def _place(env, positions: list[list[int]]) -> None:
    env.positions.copy_(torch.tensor(positions, dtype=env.positions.dtype, device=env.positions.device))


# -- probe_a.py C: time -------------------------------------------------------------------


def test_tick_compiles_in_an_effect_and_reads_the_engine_tick(tmp_path: Path) -> None:
    """A global effect copies the engine tick into a global variable every tick."""
    pack = _pack(tmp_path, _effect("clock", scope="global", on_tick=[{"modify": "day_count", "value": "tick"}]))
    env = _env(pack, num_agents=2)
    _spawn(env, "clock", world=0)

    for _ in range(3):
        ticks_at_effect = env.global_tick
        _wait(env)

    # A global-scope effect lives in the world that spawned it (S1): world 1 is untouched.
    assert env.vfs_registry.get("day_count", reader="engine").tolist() == pytest.approx([float(ticks_at_effect), 0.0])
    assert ticks_at_effect > 0


# -- probe_a.py D: position ---------------------------------------------------------------


def test_distance_to_affordance_evaluates_per_agent_in_an_effect(tmp_path: Path) -> None:
    """FOOD is at (3, 3) on a manhattan grid: agents at distance 6, 0 and 2 lose 0.01 per cell."""
    effect = _effect(
        "pull", scope="agent", on_tick=[{"modify": "bar.health", "value": 'bar.health - 0.01 * distance_to_affordance("FOOD")'}]
    )
    env = _env(_pack(tmp_path, effect), num_agents=3)
    _place(env, [[0, 0], [3, 3], [1, 3]])
    health = env.meter_name_to_index["health"]
    _spawn_in_every_world(env, "pull")

    before = env.meters[:, health].clone()
    _wait(env)
    loss = before - env.meters[:, health]

    assert (loss[0] - loss[1]).item() == pytest.approx(0.06, abs=1e-5)
    assert (loss[2] - loss[1]).item() == pytest.approx(0.02, abs=1e-5)


def test_in_range_evaluates_in_an_effect(tmp_path: Path) -> None:
    effect = _effect(
        "near_food",
        scope="agent",
        on_tick=[{"modify": "bar.health", "value": 'bar.health - (if in_range("FOOD", 2.0) then 0.1 else 0.0)'}],
    )
    env = _env(_pack(tmp_path, effect), num_agents=2)
    _place(env, [[0, 0], [3, 2]])
    health = env.meter_name_to_index["health"]
    _spawn_in_every_world(env, "near_food")

    before = env.meters[:, health].clone()
    _wait(env)
    loss = before - env.meters[:, health]

    assert (loss[1] - loss[0]).item() == pytest.approx(0.1, abs=1e-5)


# -- probe_d.py Z: temporal history refuses at compile ------------------------------------


@pytest.mark.parametrize("expression", ["bar.health - 0.1 * lag(bar.energy, 1)", "bar.health - 0.001 * elapsed_ticks()"])
def test_history_functions_refuse_at_compile_in_an_effect(tmp_path: Path, expression: str) -> None:
    pack = _pack(tmp_path, _effect("hist", scope="agent", on_tick=[{"modify": "bar.health", "value": expression}]))

    with pytest.raises(CompilationError, match="which an effect pipeline does not carry"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_history_refusal_reaches_nested_expressions_and_bodies() -> None:
    schema = {"bar.health": "float", "bar.energy": "float"}
    nested = CommandNode(
        type=CommandType.MODIFY,
        path="bar.health",
        value_expr="if bar.health > 0.5 then clamp(ema(bar.energy, 0.5), 0.0, 1.0) else 0.0",
    )
    in_body = CommandNode(
        type=CommandType.FOR_EACH,
        collection="all_agents",
        body=[CommandNode(type=CommandType.MODIFY, path="bar.health", value_expr="bar.health - delta(bar.energy)")],
    )

    for node in (nested, in_body):
        with pytest.raises(TypeCheckError, match="does not carry"):
            command_compiler(schema).compile_command(node)
