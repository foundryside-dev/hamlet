"""A bare write to an agent-scoped variable is one agent's row, never the batch.

Reproduction of review-2026-10-24 V8 (findings_vfs hamlet-b9a3bcbde2, `probe2.py` C): both
agents interacting at SLEEP with `modify: public_state value: public_state + 5.0`
landed `[10.0, 10.0]` because the whole batch was written once per interactor.

Under one spelling (VFS round-2 S5) a bare agent variable is this world's agent's row
in every pipeline: S1 gives a world one agent, so a global-, affordance- or item-scoped
effect addresses that agent exactly as an agent-scoped effect or an interaction does.
"""

from __future__ import annotations

import shutil
from pathlib import Path

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
from townlet.world.expression.type_checker import TypeCheckError

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"

SCHEMA = {"bar.energy": "float", "mood": "float", "gcount": "float", "item.freshness": "float"}
SCOPES = {"gcount": "global"}


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _pack(tmp_path: Path, *, sleep_on_start: list[dict] | None = None, effects: list[dict] | None = None) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    if sleep_on_start is not None:
        path = pack / "levels" / LEVEL / "affordances.yaml"
        payload = yaml.safe_load(path.read_text())
        sleep = next(a for a in payload["affordances"]["affordances"] if a["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = sleep_on_start
        _write_yaml(path, payload)
    if effects is not None:
        _write_yaml(
            pack / "effects.yaml",
            {
                "version": "1.0",
                "max_active_effects": {"global": 1, "agent": 1, "item": 1, "affordance": 1},
                "effect_definitions": effects,
            },
        )
    return pack


def _effect(scope: str, on_tick: list[dict]) -> dict:
    return {
        "id": f"{scope}_probe",
        "scope": scope,
        "duration": 3,
        "reapply_policy": "renew",
        "observable": False,
        "on_spawn": [],
        "on_tick": on_tick,
        "on_despawn": [],
        "on_interrupt": [],
    }


def _env(pack: Path, num_agents: int):
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    env.reset()
    env.positions[:] = env.affordances["SLEEP"].to(env.positions.dtype)
    return env


def _public_state(env) -> list[float]:
    return env.vfs_registry.get("public_state", reader="engine").tolist()


BARE_INCREMENT = [{"modify": "public_state", "value": "public_state + 5.0"}]


def test_bare_write_lands_on_the_interacting_agent_only(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=BARE_INCREMENT), num_agents=2)
    env.step(torch.tensor([env.action_ids["INTERACT"], env.action_ids["WAIT"]]))
    assert _public_state(env) == [5.0, 0.0]


def test_two_interactors_each_get_their_own_row(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=BARE_INCREMENT), num_agents=2)
    env.step(torch.full((2,), env.action_ids["INTERACT"]))
    assert _public_state(env) == [5.0, 5.0]


def test_the_second_interactor_alone_writes_only_its_row(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=BARE_INCREMENT), num_agents=2)
    env.step(torch.tensor([env.action_ids["WAIT"], env.action_ids["INTERACT"]]))
    assert _public_state(env) == [0.0, 5.0]


def test_global_bare_write_lands_in_each_interactors_own_world(tmp_path: Path) -> None:
    pack = _pack(tmp_path, sleep_on_start=[{"modify": "gcount", "value": "gcount + 1.0"}])
    variables = pack / "variables.yaml"
    payload = yaml.safe_load(variables.read_text())
    payload["variables"]["declarations"].append(
        {
            "id": "gcount",
            "scope": "global",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": 0.0,
        }
    )
    _write_yaml(variables, payload)
    env = _env(pack, num_agents=2)
    env.step(torch.full((2,), env.action_ids["INTERACT"]))
    # One row per world (S1): each interactor counts in its own world, never in the other's.
    assert env.vfs_registry.get("gcount", reader="engine").tolist() == [1.0, 1.0]
    env.step(torch.tensor([env.action_ids["WAIT"], env.action_ids["INTERACT"]]))
    assert env.vfs_registry.get("gcount", reader="engine").tolist() == [1.0, 2.0]


@pytest.mark.parametrize("scope", ["global", "item", "affordance"])
def test_every_effect_scope_compiles_a_bare_agent_write_to_its_worlds_agent(tmp_path: Path, scope: str) -> None:
    pack = _pack(tmp_path, effects=[_effect(scope, BARE_INCREMENT)])
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert universe.compiled_effect_catalog is not None
    (command,) = universe.compiled_effect_catalog.get(f"{scope}_probe").on_tick
    assert command.path == "public_state"


def test_agent_scoped_effect_compiles_bare_agent_write(tmp_path: Path) -> None:
    pack = _pack(tmp_path, effects=[_effect("agent", BARE_INCREMENT)])
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert universe.compiled_effect_catalog is not None
    (command,) = universe.compiled_effect_catalog.get("agent_probe").on_tick
    assert command.path == "public_state"


# -- compiler-level contract ------------------------------------------------------------


def _modify(path: str, value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)


def test_compiler_keeps_bare_paths_as_written() -> None:
    node = command_compiler(SCHEMA, scopes=SCOPES).compile_command(_modify("mood", "mood + gcount"))
    assert node.path == "mood"
    assert (node.value_ast.left.name, node.value_ast.right.name) == ("mood", "gcount")


@pytest.mark.parametrize("path", ["gcount", "item.freshness"])
def test_compiler_leaves_global_and_item_paths_alone(path: str) -> None:
    node = command_compiler(SCHEMA, item=True, scopes=SCOPES).compile_command(_modify(path, "1.0"))
    assert node.path == path


def test_for_each_over_agents_binds_an_agent_target_inside_a_global_pipeline() -> None:
    loop = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", iterator="agent", body=[_modify("mood", "2.0")])
    command_compiler(SCHEMA).compile_command(loop)
    assert loop.body is not None and loop.body[0].path == "mood"


def test_for_each_over_inventory_items_binds_the_item_and_keeps_the_agent() -> None:
    loop = CommandNode(
        type=CommandType.FOR_EACH,
        collection="inventory_items",
        iterator="item",
        body=[_modify("mood", "2.0"), _modify("item.freshness", "item.freshness - 1.0")],
    )
    command_compiler(SCHEMA).compile_command(loop)


def test_parallel_conflict_sees_bare_and_target_spellings_as_one_write() -> None:
    node = CommandNode(type=CommandType.PARALLEL, parallel_commands=[_modify("mood", "1.0"), _modify("mood", "2.0")])
    with pytest.raises(TypeCheckError, match="same targets"):
        command_compiler(SCHEMA).compile_command(node)


def test_sample_store_target_resolves_too() -> None:
    sample = CommandNode(
        type=CommandType.SAMPLE, sample_store_path="mood", sample_distribution="uniform", sample_params={"min": 0.0, "max": 1.0}
    )
    compiler = command_compiler(SCHEMA)
    assert compiler.compile_command(sample).sample_store_path == "mood"


# -- runtime: a bare agent write lands on this world's agent ------------------------------


def _registry() -> VariableRegistry:
    mood = VariableDef(
        id="mood", scope="agent", type="scalar", lifetime="episode", default=0.0, readable_by=["engine"], writable_by=["engine"]
    )
    return VariableRegistry([mood], 3, torch.device("cpu"))


def test_runtime_bare_agent_write_with_target_writes_that_row() -> None:
    registry = _registry()
    node = _modify("mood", "mood + 1.5")
    command_compiler({"mood": "float"}).compile_command(node)
    CommandExecutor().execute(node, ExecutionContext(vfs_registry=registry, target_index=2))
    assert registry.get("mood", reader="engine").tolist() == [0.0, 0.0, 1.5]


def test_runtime_bare_agent_write_from_a_world_bound_effect_writes_its_worlds_agent() -> None:
    registry = _registry()
    node = _modify("mood", "mood + 1.0")
    command_compiler({"mood": "float"}).compile_command(node)

    class _Effect:
        world = 1
        intensity = 1.0
        elapsed_ticks = 0
        duration_remaining = 1

    CommandExecutor().execute(node, ExecutionContext(vfs_registry=registry, effect=_Effect()))
    assert registry.get("mood", reader="engine").tolist() == [0.0, 1.0, 0.0]
