"""A bare `vfs.X` write to an agent-scoped variable is one agent's row, never the batch.

Reproduction of review-2026-10-24 V8 (findings_vfs hamlet-b9a3bcbde2, `probe2.py` C): both
agents interacting at SLEEP with `modify: vfs.public_state value: vfs.public_state + 5.0`
landed `[10.0, 10.0]` because the whole batch was written once per interactor. The command
compiler now resolves a bare agent-scoped `vfs.X` to `target.vfs.X` wherever the pipeline
runs with an interacting agent, and refuses the write where it does not.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.effects.compiler import CommandCompiler
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef
from townlet.world.expression.type_checker import TypeCheckError

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"

# Schema shape produced by EffectsCompiler.build_schema: agent variables carry a
# `target.` twin, globals a `global.` twin, item-profile variables a `self.` form only.
SCHEMA = {
    "bar.energy": "float",
    "target.bar.energy": "float",
    "vfs.mood": "float",
    "target.vfs.mood": "float",
    "vfs.gcount": "float",
    "global.vfs.gcount": "float",
    "self.vfs.freshness": "float",
}


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


BARE_INCREMENT = [{"modify": "vfs.public_state", "value": "vfs.public_state + 5.0"}]


def test_bare_write_lands_on_the_interacting_agent_only(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=BARE_INCREMENT), num_agents=2)
    env.step(torch.tensor([env.action_ids["INTERACT"], env.action_ids["WAIT"]]))
    assert _public_state(env) == [5.0, 0.0]


def test_two_interactors_each_get_their_own_row(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path, sleep_on_start=BARE_INCREMENT), num_agents=2)
    env.step(torch.full((2,), env.action_ids["INTERACT"]))
    assert _public_state(env) == [5.0, 5.0]


def test_target_spelling_is_unchanged(tmp_path: Path) -> None:
    explicit = [{"modify": "target.vfs.public_state", "value": "target.vfs.public_state + 5.0"}]
    env = _env(_pack(tmp_path, sleep_on_start=explicit), num_agents=2)
    env.step(torch.tensor([env.action_ids["WAIT"], env.action_ids["INTERACT"]]))
    assert _public_state(env) == [0.0, 5.0]


def test_global_bare_write_lands_in_each_interactors_own_world(tmp_path: Path) -> None:
    pack = _pack(tmp_path, sleep_on_start=[{"modify": "vfs.gcount", "value": "vfs.gcount + 1.0"}])
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
def test_bare_agent_write_without_an_agent_target_refuses_at_compile(tmp_path: Path, scope: str) -> None:
    pack = _pack(tmp_path, effects=[_effect(scope, BARE_INCREMENT)])
    with pytest.raises(CompilationError, match=rf"Effect '{scope}_probe' failed to compile.*no interacting agent"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_agent_scoped_effect_compiles_bare_agent_write(tmp_path: Path) -> None:
    pack = _pack(tmp_path, effects=[_effect("agent", BARE_INCREMENT)])
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    assert universe.compiled_effect_catalog is not None
    (command,) = universe.compiled_effect_catalog.get("agent_probe").on_tick
    assert command.path == "target.vfs.public_state"


# -- compiler-level contract ------------------------------------------------------------


def _modify(path: str, value: str) -> CommandNode:
    return CommandNode(type=CommandType.MODIFY, path=path, value_expr=value)


def test_compiler_resolves_bare_agent_path_and_expression_under_agent_target() -> None:
    node = CommandCompiler(SCHEMA, agent_target=True).compile_command(_modify("vfs.mood", "vfs.mood + vfs.gcount"))
    assert node.path == "target.vfs.mood"
    left, right = node.value_ast.left, node.value_ast.right
    assert left.segments == ["target", "vfs", "mood"]
    assert right.segments == ["vfs", "gcount"]


def test_agent_target_is_a_required_declaration() -> None:
    """No default: every construction site states whether `target` is bound to an agent row."""
    with pytest.raises(TypeError, match="agent_target"):
        CommandCompiler(SCHEMA)  # type: ignore[call-arg]


def test_compiler_refuses_bare_agent_write_without_agent_target() -> None:
    with pytest.raises(TypeCheckError, match="no interacting agent"):
        CommandCompiler(SCHEMA, agent_target=False).compile_command(_modify("vfs.mood", "1.0"))


@pytest.mark.parametrize("path", ["vfs.gcount", "self.vfs.freshness"])
def test_compiler_leaves_global_and_item_paths_alone(path: str) -> None:
    node = CommandCompiler(SCHEMA, agent_target=False).compile_command(_modify(path, "1.0"))
    assert node.path == path


def test_for_each_over_agents_binds_an_agent_target_inside_a_global_pipeline() -> None:
    loop = CommandNode(type=CommandType.FOR_EACH, collection="all_agents", iterator="agent", body=[_modify("vfs.mood", "2.0")])
    CommandCompiler(SCHEMA, agent_target=False).compile_command(loop)
    assert loop.body is not None and loop.body[0].path == "target.vfs.mood"


def test_for_each_over_inventory_items_has_no_agent_target() -> None:
    loop = CommandNode(type=CommandType.FOR_EACH, collection="inventory_items", iterator="item", body=[_modify("vfs.mood", "2.0")])
    with pytest.raises(TypeCheckError, match="no interacting agent"):
        CommandCompiler(SCHEMA, agent_target=True).compile_command(loop)


def test_parallel_conflict_sees_bare_and_target_spellings_as_one_write() -> None:
    node = CommandNode(type=CommandType.PARALLEL, parallel_commands=[_modify("vfs.mood", "1.0"), _modify("target.vfs.mood", "2.0")])
    with pytest.raises(TypeCheckError, match="same targets"):
        CommandCompiler(SCHEMA, agent_target=True).compile_command(node)


def test_sample_store_target_resolves_too() -> None:
    sample = CommandNode(
        type=CommandType.SAMPLE, sample_store_path="vfs.mood", sample_distribution="uniform", sample_params={"min": 0.0, "max": 1.0}
    )
    compiler = CommandCompiler(SCHEMA, agent_target=True)
    assert compiler.compile_command(sample).sample_store_path == "target.vfs.mood"


# -- runtime backstop: a bare agent write reaching the context unresolved -----------------


def _registry() -> VariableRegistry:
    mood = VariableDef(
        id="mood", scope="agent", type="scalar", lifetime="episode", default=0.0, readable_by=["engine"], writable_by=["engine"]
    )
    return VariableRegistry([mood], 3, torch.device("cpu"))


def test_runtime_bare_agent_write_with_target_writes_that_row() -> None:
    registry = _registry()
    node = _modify("vfs.mood", "vfs.mood + 1.5")
    CommandCompiler({"vfs.mood": "float"}, agent_target=True).compile_command(node)  # no target twin: the compiler cannot resolve it
    CommandExecutor().execute(node, ExecutionContext(vfs_registry=registry, target_index=2))
    assert registry.get("mood", reader="engine").tolist() == [0.0, 0.0, 1.5]


def test_runtime_bare_agent_write_without_target_refuses_untouched() -> None:
    registry = _registry()
    node = _modify("vfs.mood", "1.0")
    CommandCompiler({"vfs.mood": "float"}, agent_target=True).compile_command(node)
    with pytest.raises(ValueError, match="never a batch write"):
        CommandExecutor().execute(node, ExecutionContext(vfs_registry=registry, target_index=None))
    assert registry.get("mood", reader="engine").tolist() == [0.0, 0.0, 0.0]
