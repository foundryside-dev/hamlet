"""WP13 (review-2026-10-24 VFS F4, owner ruling S1): `global` state is per world.

The env batch is N independent single-agent worlds. A `global` variable therefore has
one row per world, engine-internal: the author still declares `scope: global` and reads
it as one value in their world. Reproduction `r12_global_cross_world.py`: agent 0 using
SLEEP in world 0 raised the shared `visits` global, so agent 1 in world 1 observed it and
was rewarded for it. Every reader and writer now addresses its own world's row.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.effects.context import ExecutionContext
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs import compile_vtc_social_residue_rules
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.vtc import VTCWriteRefusalError, VTCWriteTarget

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
MINMAX = {"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True}


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _write(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _declaration(var_id: str, *, scope: str = "global", exposed: bool = False, **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": ["agent"] if exposed else [],
        "initial_value": 0.0,
    }
    if exposed:
        declaration["normalization"] = MINMAX
    declaration.update(extra)
    return declaration


def _pack(tmp_path: Path, *, declarations: list[dict] = (), rules: list[dict] | None = None) -> Path:
    """r12: a global `visits`, exposed and rewarded at weight 1, raised by SLEEP's `on_start`."""
    pack = tmp_path / "pack"
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))

    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"] += [_declaration("visits", exposed=True), *declarations]
    _write(pack / "variables.yaml", variables)

    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    affordances = _yaml(affordances_path)
    sleep = next(a for a in affordances["affordances"]["affordances"] if a["name"] == "SLEEP")
    sleep["interactions"]["on_start"].append({"modify": "vfs.visits", "value": "vfs.visits + 1.0"})
    _write(affordances_path, affordances)

    drive_path = pack / "levels" / LEVEL / "drive.yaml"
    drive = _yaml(drive_path)
    drive["drive"]["extrinsic"]["variable_bonuses"] = [{"variable": "visits", "weight": 1.0}]
    _write(drive_path, drive)

    if rules is not None:
        _write(pack / "transition_rules.yaml", {"version": "1.0", "social_residue": rules})
    return pack


def _env(pack: Path, num_agents: int = 2):
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    env.reset()
    return env


def _place_agent0_on_sleep(env) -> None:
    """Agent 0 stands on SLEEP; agent 1 stands on a cell no affordance occupies."""
    sleep = env.affordances["SLEEP"]
    env.positions[0] = (sleep[0] if sleep.dim() > 1 else sleep).to(env.positions.dtype)
    occupied = {tuple((p[0] if p.dim() > 1 else p).tolist()) for p in env.affordances.values()}
    free = next((x, y) for x in range(7, -1, -1) for y in range(7, -1, -1) if (x, y) not in occupied)
    env.positions[1] = torch.tensor(free, dtype=env.positions.dtype)


def _action(env, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


def _visits_rows(env, obs: torch.Tensor) -> torch.Tensor:
    """The `visits` variable_element token row of every world, from the flat observation."""
    spec = env.token_spec
    bindings = spec.get_type("variable_element").slot_bindings
    start, end = next(
        (s, e) for (ttype, slot, s, e) in spec.row_layout() if ttype == "variable_element" and bindings[slot].filler_ref == "visits"
    )
    return obs[:, start:end]


def _registry(env, var_id: str) -> list[float]:
    return env.vfs_registry.get(var_id, reader="engine").tolist()


# --- r12: one world's interaction never reaches another world ---------------------------


def test_agent0s_interaction_leaves_agent1s_world_unchanged_in_registry_observation_and_reward(tmp_path: Path) -> None:
    pack = _pack(tmp_path)
    torch.manual_seed(0)
    interacting = _env(pack)
    torch.manual_seed(0)
    control = _env(pack)  # the same layout, where nobody interacts
    for env in (interacting, control):
        _place_agent0_on_sleep(env)
    wait = _action(interacting, "WAIT")

    obs, reward, _, info = interacting.step(torch.tensor([_action(interacting, "INTERACT"), wait]))
    control_obs, control_reward, _, _ = control.step(torch.tensor([wait, wait]))

    assert info["successful_interactions"] == {0: "SLEEP"}
    # Registry: world 0 counted the visit; world 1 did not.
    assert _registry(interacting, "visits") == [1.0, 0.0]
    # Observation: each world publishes its own row; world 1's equals the no-interaction run.
    rows = _visits_rows(interacting, obs)
    assert not torch.equal(rows[0], rows[1])
    assert torch.equal(rows[1], _visits_rows(control, control_obs)[1])
    assert torch.equal(obs[1], control_obs[1])
    # Reward: world 1's agent is not rewarded for world 0's event.
    assert reward[0].item() == pytest.approx(1.0)
    assert reward[1].item() == pytest.approx(control_reward[1].item())
    assert reward[1].item() == pytest.approx(0.0)


def test_the_engine_tick_is_the_same_instant_in_every_world(tmp_path: Path) -> None:
    env = _env(_pack(tmp_path), num_agents=3)
    assert _registry(env, "tick") == [0.0, 0.0, 0.0]
    for expected in (1.0, 2.0, 3.0):
        env.step(torch.full((3,), _action(env, "WAIT"), dtype=torch.long))
        assert _registry(env, "tick") == [expected] * 3
    env.reset()
    assert _registry(env, "tick") == [0.0, 0.0, 0.0]


# --- transition rules advance each world's global on that world's own state ---------------


def test_a_global_rule_advances_each_world_independently(tmp_path: Path) -> None:
    rule = {
        "id": "afterglow",
        "phase": "apply_social_residue_effects",
        "kind": "social_residue",
        "reads": ["visits", "afterglow"],
        "condition": "visits > 0.0",
        "writes": [
            {
                "variable_id": "afterglow",
                "effect": "advance",
                "expression": "1.0",
                "composition": "additive_delta",
                "condition": None,
                "clamp": [0.0, 1000.0],
            }
        ],
    }
    env = _env(_pack(tmp_path, declarations=[_declaration("afterglow")], rules=[rule]))
    _place_agent0_on_sleep(env)
    wait = _action(env, "WAIT")
    env.step(torch.tensor([_action(env, "INTERACT"), wait]))
    after_visit = _registry(env, "afterglow")
    for _ in range(2):
        env.step(torch.tensor([wait, wait]))
    # Only world 0 ever visited, so only world 0's rule fires, once per tick.
    assert after_visit[1] == 0.0
    assert _registry(env, "afterglow") == [after_visit[0] + 2.0, 0.0]


# --- expressions evaluate per world -------------------------------------------------------


def test_global_and_agent_expressions_read_their_own_worlds_global(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        declarations=[
            _declaration("visits_doubled", expression="visits * 2.0"),
            _declaration("seen", scope="agent", expression="visits + bar.energy * 0.0"),
            _declaration("constant", expression="3.0"),
        ],
    )
    env = _env(pack)
    _place_agent0_on_sleep(env)
    env.step(torch.tensor([_action(env, "INTERACT"), _action(env, "WAIT")]))
    assert _registry(env, "visits_doubled") == [2.0, 0.0]
    assert _registry(env, "seen") == [1.0, 0.0]
    # A literal-only global expression is world-invariant: the same value in every row.
    assert _registry(env, "constant") == [3.0, 3.0]


def test_a_global_expression_still_cannot_read_agent_state(tmp_path: Path) -> None:
    """The authoring contract is unchanged: a global is a scalar in its world, and an
    agent value is not. The world axis coincides with the agent axis only while a world
    holds one agent (S1); agents-per-world is a future declared parameter."""
    pack = _pack(tmp_path, declarations=[_declaration("energy_echo", expression="bar.energy * 1.0")])
    with pytest.raises(CompilationError, match="energy_echo"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


# --- persistent state round-trips per-world rows -----------------------------------------


def _persistent_registry() -> VariableRegistry:
    season = VariableDef(
        id="season",
        scope="global",
        type="vecNf",
        dims=2,
        lifetime="persistent",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=[0.0, 0.0],
    )
    return VariableRegistry(variables=[season], num_agents=3, device=torch.device("cpu"))


def test_persistent_save_and_restore_round_trips_every_worlds_row() -> None:
    source = _persistent_registry()
    rows = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    source.set_engine_value("season", rows)
    state = source.persistent_state()
    assert torch.equal(state["season"], rows)  # the snapshot carries the world axis

    target = _persistent_registry()
    target.restore_persistent_state(state)
    assert torch.equal(target.get("season", reader="engine"), rows)
    offset, count = target.scope_arenas["global"].index["season"]
    assert torch.equal(target.scope_arenas["global"].tensor[:, offset : offset + count], rows)

    # A snapshot without the world axis is not this registry's state.
    with pytest.raises(RuntimeError, match="shape"):
        target.validate_persistent_state({"season": rows[0]})


# --- batch-shared state cannot read a per-world global ------------------------------------

_RULE_TARGETS = {
    "pressure": VTCWriteTarget(VariableScope.GLOBAL, "scalar", meter=False),
    "wear": VTCWriteTarget(VariableScope.AFFORDANCE, "scalar", meter=False),
}


def _wear_rule(expression: str, condition: str | None = None) -> dict:
    return {
        "id": "wear_from_pressure",
        "phase": "apply_social_residue_effects",
        "kind": "social_residue",
        "reads": ["wear", "pressure"],
        "condition": condition,
        "writes": [{"variable_id": "wear", "expression": expression, "composition": "additive_delta"}],
    }


@pytest.mark.parametrize(("expression", "condition"), [("wear + pressure", None), ("pressure", None), ("1.0", "pressure > 0.5")])
def test_an_affordance_rule_reading_a_global_refuses_at_compile(expression: str, condition: str | None) -> None:
    """Affordance state is shared by every world; a global has one value per world, so the
    read has no single world. Refused at compile, never broadcast by a coincidence of extents."""
    with pytest.raises(VTCWriteRefusalError, match="no single world"):
        compile_vtc_social_residue_rules([_wear_rule(expression, condition)], _RULE_TARGETS)


def test_an_affordance_rule_reading_affordance_state_still_runs() -> None:
    program = compile_vtc_social_residue_rules([_wear_rule("wear * 0.0 + 1.0")], _RULE_TARGETS)
    updated = program.apply(
        vfs_state={"wear": torch.zeros(3), "pressure": torch.zeros(2)}, active_mask=torch.tensor([True, True]), device=torch.device("cpu")
    ).values
    assert updated["wear"].tolist() == [1.0, 1.0, 1.0]


def test_an_availability_override_is_per_world() -> None:
    """`affordance.X.available` has one value per world: a world-bound write lands in its world only."""
    registry = VariableRegistry(
        [
            VariableDef(
                id="open_flag",
                scope="global",
                type="bool",
                lifetime="episode",
                readable_by=["engine"],
                writable_by=["engine"],
                default=True,
            )
        ],
        2,
        torch.device("cpu"),
    )
    overrides: list[dict[str, bool]] = [{}, {}]
    context = ExecutionContext(bars={"energy": torch.ones(2)}, vfs_registry=registry, affordance_overrides=overrides)
    # Bound to no world, the per-world read writes each world's own value.
    context.set_path("affordance.SLEEP.available", context.get_path("vfs.open_flag"))
    assert overrides == [{"SLEEP": True}, {"SLEEP": True}]
    # Bound to agent 1's world, the write lands in world 1 only.
    bound = context.copy(target_index=1)
    bound.set_path("affordance.SLEEP.available", torch.tensor(False))
    assert overrides == [{"SLEEP": True}, {"SLEEP": False}]
