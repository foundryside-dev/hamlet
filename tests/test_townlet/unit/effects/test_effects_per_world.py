"""Effects are per world (owner ruling S1: the batch is N independent single-agent worlds).

The differential method: two runs that differ only in world 0's actions must leave worlds
1..N-1 byte-identical, for every effect scope (global, affordance, agent, item) and every
command that can reach another world (bare `bar.X`, globals, `for_each: all_agents`,
affordance availability, `spawn_item`, sampling functions). Plus the dead-agent freeze, the
item leftovers of the per-world-items cut, `nearest` candidates and the deleted velocity
name branch.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from tests.test_townlet._fixtures.command_namespace import command_compiler
from townlet.determinism import seed_all
from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor
from townlet.effects.schema import CommandNode, CommandType
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef

REPO = Path(__file__).resolve().parents[4]
EPISTEMIC = REPO / "configs" / "static_epistemic_access"
ITEMS_SMOKE = REPO / "configs" / "test" / "items_smoke"
LEVEL = "L0_simple"
ITEMS_LEVEL = "L0_smoke"
N = 4


def _yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _write(path: Path, payload: Any) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _declaration(var_id: str, *, scope: str = "global", lifetime: str = "episode") -> dict:
    return {
        "id": var_id,
        "scope": scope,
        "type": "scalar",
        "lifetime": lifetime,
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": 0.0,
    }


def _effect(effect_id: str, scope: str, on_tick: list[dict], *, on_spawn: list[dict] | None = None, duration: int = 50) -> dict:
    return {
        "id": effect_id,
        "scope": scope,
        "duration": duration,
        "reapply_policy": "renew",
        "observable": True,
        "on_spawn": on_spawn or [],
        "on_tick": on_tick,
        "on_despawn": [],
        "on_interrupt": [],
    }


def _epistemic_pack(tmp_path: Path, *, declarations: list[dict], effects: list[dict], spawns: list[str], budget: dict) -> Path:
    pack = tmp_path / "pack"
    shutil.copytree(EPISTEMIC, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"] += declarations
    _write(pack / "variables.yaml", variables)
    effects_payload: dict[str, Any] = {"version": "1.0", "effect_definitions": effects}
    if effects:
        effects_payload["max_active_effects"] = budget
    _write(pack / "effects.yaml", effects_payload)
    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    affordances = _yaml(affordances_path)
    sleep = next(a for a in affordances["affordances"]["affordances"] if a["name"] == "SLEEP")
    sleep["interactions"]["on_start"] += [{"spawn_effect": effect_id, "target": "target", "intensity": 1.0} for effect_id in spawns]
    _write(affordances_path, affordances)
    return pack


def _action(env, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


def _place_world0_on_sleep(env) -> None:
    sleep = env.affordances["SLEEP"]
    occupied = {tuple((p[0] if p.dim() > 1 else p).tolist()) for p in env.affordances.values()}
    free = [(x, y) for x in range(7, -1, -1) for y in range(7, -1, -1) if (x, y) not in occupied]
    env.positions[0] = (sleep[0] if sleep.dim() > 1 else sleep).to(env.positions.dtype)
    for agent in range(1, env.num_agents):
        env.positions[agent] = torch.tensor(free[agent], dtype=env.positions.dtype)


def _world_snapshot(env, world: int, obs: torch.Tensor, rewards: torch.Tensor) -> dict:
    snapshot: dict[str, Any] = {
        "obs": obs[world].clone(),
        "reward": float(rewards[world]),
        "meters": env.meters[world].clone(),
        "done": bool(env.dones[world]),
        "position": env.positions[world].clone(),
        "registry": {
            var_id: env.vfs_registry.get(var_id, reader="engine")[world].clone()
            for var_id in env.vfs_registry.variables
            if env.vfs_registry.get(var_id, reader="engine").dim() > 0
        },
    }
    if env.effect_manager is not None:
        snapshot["effects"] = sorted(
            (e.effect_id, e.scope.value, e.duration_remaining, e.elapsed_ticks, float(e.intensity))
            for e in env.effect_manager.effects_in_world(world)
        )
    if env.item_manager is not None:
        state = env.item_manager.worlds[world]
        snapshot["items"] = [
            (
                item.item_type,
                tuple(item.position),
                item.instance_id in state.held,
                item.duration_remaining,
                item.vfs_index - world * env.items_per_world,
            )
            for item in env.item_manager.items_in_world(world)
        ]
        snapshot["timers"] = dict(state.respawn_timers)
        if env.vfs_registry.item_vfs is not None:
            per_world = env.items_per_world
            snapshot["arena"] = env.vfs_registry.item_vfs[world * per_world : (world + 1) * per_world].clone()
    return snapshot


def _run(universe, level: str, actions: list[torch.Tensor], *, setup, seed: int = 7) -> list[list[dict]]:
    """One run: per step, every world's snapshot."""
    seed_all(seed)
    env = universe.create_environment(num_agents=N, level_name=level, device="cpu")
    seed_all(seed)
    env.reset()
    setup(env)
    trace = []
    for step_actions in actions:
        obs, rewards, _, _ = env.step(step_actions)
        trace.append([_world_snapshot(env, world, obs, rewards) for world in range(N)])
    return trace


def _assert_equal(a: Any, b: Any, where: str) -> None:
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b), where
    elif isinstance(a, dict):
        assert a.keys() == b.keys(), where
        for key in a:
            _assert_equal(a[key], b[key], f"{where}.{key}")
    else:
        assert a == b, where


def _assert_worlds_identical(trace_a: list[list[dict]], trace_b: list[list[dict]], worlds: range) -> None:
    for step, (snap_a, snap_b) in enumerate(zip(trace_a, trace_b, strict=True)):
        for world in worlds:
            _assert_equal(snap_a[world], snap_b[world], f"step {step} world {world}")


# -- 1/2: every effect scope and for_each, by differential ---------------------------------

WORLD_PROC = _effect(
    "world_proc",
    "global",
    [
        {"modify": "g", "value": "g + 1.0"},
        {"modify": "g_rand", "value": "uniform(0.0, 1.0)"},
        {"modify": "bar.money", "value": "bar.money + 0.01"},
        {
            "for_each": "all_agents",
            "do": [
                {"modify": "bar.health", "value": "bar.health - 0.002"},
                {"modify": "mood", "value": "mood + 1.0"},
            ],
        },
    ],
)
# SLEEP's reachable meter writes are capped (EFFECT_SUMMARY_K), so the other two scopes
# write meters sparingly; every scope still writes a global and the world's agent.
AFFORDANCE_PROC = _effect("aff_proc", "affordance", [{"modify": "g_aff", "value": "g_aff + 1.0"}])
AGENT_PROC = _effect(
    "agent_proc",
    "agent",
    [
        {"modify": "g_agent", "value": "g_agent + 1.0"},
        {"modify": "bar.money", "value": "bar.money - 0.001"},
        {"for_each": "all_agents", "do": [{"modify": "mood", "value": "mood + 10.0"}]},
    ],
)


@pytest.fixture(scope="module")
def effects_universe(tmp_path_factory: pytest.TempPathFactory):
    declarations = [_declaration(v) for v in ("g", "g_rand", "g_aff", "g_agent")] + [_declaration("mood", scope="agent")]
    pack = _epistemic_pack(
        tmp_path_factory.mktemp("effects"),
        declarations=declarations,
        effects=[WORLD_PROC, AFFORDANCE_PROC, AGENT_PROC],
        spawns=["world_proc", "aff_proc", "agent_proc"],
        budget={"global": 1, "agent": 1, "item": 0, "affordance": 1},
    )
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _world0_interacts(env, steps: int) -> list[torch.Tensor]:
    interact, wait = _action(env, "INTERACT"), _action(env, "WAIT")
    actions = [torch.full((N,), wait, dtype=torch.long) for _ in range(steps)]
    actions[0] = actions[0].clone()
    actions[0][0] = interact
    return actions


def test_world0s_effects_of_every_scope_leave_every_other_world_identical(effects_universe) -> None:
    env = effects_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    wait = _action(env, "WAIT")
    quiet = [torch.full((N,), wait, dtype=torch.long) for _ in range(6)]
    active = _world0_interacts(env, 6)

    trace_a = _run(effects_universe, LEVEL, quiet, setup=_place_world0_on_sleep)
    trace_b = _run(effects_universe, LEVEL, active, setup=_place_world0_on_sleep)

    _assert_worlds_identical(trace_a, trace_b, range(1, N))
    # World 0 did change: every scope's effect lives and writes there.
    last = trace_b[-1][0]
    assert {e[0] for e in last["effects"]} == {"world_proc", "aff_proc", "agent_proc"}
    assert float(last["registry"]["g"]) > 0 and float(last["registry"]["g_aff"]) > 0 and float(last["registry"]["g_agent"]) > 0
    assert float(last["registry"]["mood"]) > 0  # for_each all_agents reached world 0's agent
    assert not torch.equal(trace_a[-1][0]["meters"], last["meters"])


def test_each_world_gets_its_own_instance_and_its_own_random_stream(effects_universe) -> None:
    """Two worlds that both interact each own one global instance; their sampled values differ."""
    seed_all(7)
    env = effects_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    seed_all(7)
    env.reset()
    sleep = env.affordances["SLEEP"]
    env.positions[:] = (sleep[0] if sleep.dim() > 1 else sleep).to(env.positions.dtype)
    interact, wait = _action(env, "INTERACT"), _action(env, "WAIT")
    env.step(torch.tensor([interact, interact, wait, wait]))
    env.step(torch.full((N,), wait, dtype=torch.long))
    manager = env.effect_manager
    assert sorted(manager.global_effects) == [0, 1]
    assert [len(manager.global_effects[w]) for w in (0, 1)] == [1, 1]
    g = env.vfs_registry.get("g", reader="engine").tolist()
    assert g[0] == g[1] > 0 and g[2] == g[3] == 0.0
    rand = env.vfs_registry.get("g_rand", reader="engine").tolist()
    assert rand[0] != rand[1]


def test_a_spawner_bound_to_no_world_spawns_one_global_instance_per_live_world(effects_universe) -> None:
    env = effects_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    command = CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="world_proc", target=0, intensity=1.0)
    context = ExecutionContext(
        bars=bars,
        vfs_registry=env.vfs_registry,
        effect_manager=env.effect_manager,
        write_mask=torch.tensor([True, False, True, True]),
    )
    CommandExecutor().execute(command, context)
    assert sorted(env.effect_manager.global_effects) == [0, 2, 3]
    assert {e.world for e in env.effect_manager.get_all_active_effects()} == {0, 2, 3}


def test_an_agent_scoped_spawn_into_another_world_is_refused(effects_universe) -> None:
    env = effects_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    bars = {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}
    command = CommandNode(type=CommandType.SPAWN_EFFECT, effect_id="agent_proc", target=2, intensity=1.0)
    context = ExecutionContext(bars=bars, vfs_registry=env.vfs_registry, effect_manager=env.effect_manager, target_index=0)
    with pytest.raises(ValueError, match="worlds are independent"):
        CommandExecutor().execute(command, context)


def test_a_for_each_element_outside_the_pipelines_world_is_refused() -> None:
    from townlet.world.expression.parser import ExpressionParser

    body = command_compiler({"bar.energy": "float"}).compile_command(
        CommandNode(type=CommandType.MODIFY, path="bar.energy", value_expr="0.0")
    )
    command = CommandNode(
        type=CommandType.FOR_EACH, collection_expr="1", collection_ast=ExpressionParser().parse("1"), iterator="x", body=[body]
    )
    bars = {"energy": torch.ones(2)}
    with pytest.raises(ValueError, match="worlds are independent"):
        CommandExecutor().execute(command, ExecutionContext(bars=bars, target_index=0))
    assert bars["energy"].tolist() == [1.0, 1.0]


def test_nearby_agents_is_refused_at_compile(tmp_path: Path) -> None:
    effect = _effect("aura", "agent", [{"for_each": "nearby_agents", "radius": 1.5, "do": []}])
    pack = _epistemic_pack(
        tmp_path, declarations=[], effects=[effect], spawns=[], budget={"global": 0, "agent": 1, "item": 0, "affordance": 0}
    )
    with pytest.raises(CompilationError, match="radius"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


# -- trial_k_cold: each world gets its own winter -------------------------------------------


def test_trial_k_cold_winter_is_per_world() -> None:
    universe = UniverseCompiler().compile(REPO / "configs" / "trial_k_cold", primary_level="L0_cold", use_cache=False)
    env = universe.create_environment(num_agents=3, level_name="L0_cold", device="cpu")
    env.reset()
    onset = env.affordances["WINTER_ONSET"]
    env.positions[1] = (onset[0] if onset.dim() > 1 else onset).to(env.positions.dtype)
    env.positions[0] = torch.tensor([7, 7], dtype=env.positions.dtype)
    env.positions[2] = torch.tensor([6, 7], dtype=env.positions.dtype)
    interact, wait = _action(env, "INTERACT"), _action(env, "WAIT")
    env.step(torch.tensor([wait, interact, wait]))
    for _ in range(3):
        env.step(torch.full((3,), wait, dtype=torch.long))
    winter_ticks = env.vfs_registry.get("winter_ticks", reader="engine").tolist()
    assert winter_ticks[1] > 0 and winter_ticks[0] == winter_ticks[2] == 0.0
    assert [e.world for e in env.effect_manager.get_all_active_effects()] == [1]


# -- 4: dead agents freeze their world ------------------------------------------------------


def test_a_dead_agents_world_is_frozen_and_its_persistent_global_carries_no_posthumous_advance(tmp_path: Path) -> None:
    ticker = _effect(
        "ticker",
        "agent",
        [{"modify": "g_eff", "value": "g_eff + 1.0"}, {"modify": "g_persist", "value": "g_persist + 1.0"}],
        duration=100,
    )
    pack = _epistemic_pack(
        tmp_path,
        declarations=[_declaration("g_eff"), _declaration("g_persist", lifetime="persistent")],
        effects=[ticker],
        spawns=["ticker"],
        budget={"global": 0, "agent": 1, "item": 0, "affordance": 0},
    )
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    sleep = env.affordances["SLEEP"]
    env.positions[:] = (sleep[0] if sleep.dim() > 1 else sleep).to(env.positions.dtype)
    interact, wait = _action(env, "INTERACT"), _action(env, "WAIT")
    env.step(torch.tensor([interact, interact]))
    env.meters[0, env.meter_name_to_index["energy"]] = 0.001  # world 0's agent dies this tick
    _, _, dones, _ = env.step(torch.tensor([wait, wait]))
    assert dones.tolist() == [True, False]
    frozen = env.vfs_registry.get("g_persist", reader="engine")[0].item()
    for _ in range(3):
        env.step(torch.tensor([wait, wait]))
    g_eff = env.vfs_registry.get("g_eff", reader="engine").tolist()
    g_persist = env.vfs_registry.get("g_persist", reader="engine").tolist()
    assert g_persist[0] == frozen
    assert g_eff[1] > g_eff[0]
    env.reset()
    assert env.vfs_registry.get("g_persist", reader="engine")[0].item() == frozen


# -- 3: nearest takes per-world candidates only ---------------------------------------------


def test_nearest_over_vector_candidates_is_refused_at_compile(tmp_path: Path) -> None:
    pick = _effect("pick", "agent", [{"modify": "g", "value": "nearest(spot, spot)"}])
    spot = {**_declaration("spot", scope="agent"), "type": "vec2f", "initial_value": [0.0, 0.0]}
    pack = _epistemic_pack(
        tmp_path,
        declarations=[_declaration("g"), spot],
        effects=[pick],
        spawns=[],
        budget={"global": 0, "agent": 1, "item": 0, "affordance": 0},
    )
    with pytest.raises(CompilationError, match="tensor2d of candidate rows"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


# -- 6: no engine write by variable name ----------------------------------------------------


def test_a_variable_named_velocity_x_is_never_written_by_the_engine(tmp_path: Path) -> None:
    """PDR-0045: the engine used to write movement deltas into any variable NAMED velocity_*."""
    declarations = [_declaration(name, scope="agent") for name in ("velocity_x", "velocity_y", "velocity_magnitude")]
    pack = _epistemic_pack(
        tmp_path, declarations=declarations, effects=[], spawns=[], budget={"global": 0, "agent": 0, "item": 0, "affordance": 0}
    )
    universe = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    env = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    env.reset()
    env.positions[:] = torch.tensor([[2, 2], [5, 5]], dtype=env.positions.dtype)
    move = next(a.id for a in env.action_space.actions if a.name in ("RIGHT", "UP", "DOWN", "LEFT"))
    env.step(torch.full((2,), move, dtype=torch.long))
    for name in ("velocity_x", "velocity_y", "velocity_magnitude"):
        assert env.vfs_registry.get(name, reader="engine").tolist() == [0.0, 0.0]


# -- 5 and 7-9: items ----------------------------------------------------------------------


def _items_pack(tmp_path: Path) -> Path:
    """items_smoke plus the leak probe's edits: item-scoped `drain` (bare bar write) and
    `drop_coin` (spawn at self) effects, apple on_use spawning a coin, short-lived coins
    on a short random respawn period, so world 0's actions change its own random draws."""
    pack = tmp_path / "items"
    shutil.copytree(ITEMS_SMOKE, pack, ignore=shutil.ignore_patterns(".compiled"))
    effects = _yaml(pack / "effects.yaml")
    effects["effect_definitions"] += [
        _effect("drain", "item", [{"modify": "bar.energy", "value": "bar.energy - 0.2"}], duration=3),
        _effect("drop_coin", "item", [], on_spawn=[{"spawn_item": "coin", "position": "self", "quantity": 1}], duration=1),
    ]
    effects["max_active_effects"]["item"] = 4
    _write(pack / "effects.yaml", effects)
    items = _yaml(pack / "items.yaml")
    types = {t["id"]: t for t in items["items"]["item_types"]}
    types["apple"]["interactions"]["on_use"].append({"spawn_item": "coin", "position": "self", "quantity": 1})
    types["coin"]["duration"] = 8
    _write(pack / "items.yaml", items)
    appearance = _yaml(pack / "levels" / ITEMS_LEVEL / "items.yaml")
    coin = next(rule for rule in appearance["items"] if rule["item_type"] == "coin")
    coin["spawn_count"] = 1
    coin["schedule"]["period"] = 12
    _write(pack / "levels" / ITEMS_LEVEL / "items.yaml", appearance)
    return pack


@pytest.fixture(scope="module")
def items_universe(tmp_path_factory: pytest.TempPathFactory):
    return UniverseCompiler().compile(_items_pack(tmp_path_factory.mktemp("items")), primary_level=ITEMS_LEVEL, use_cache=False)


def _bars(env) -> dict[str, torch.Tensor]:
    return {name: env.meters[:, idx] for name, idx in env.meter_name_to_index.items()}


def _items_env(universe, num_agents: int = N, seed: int = 7):
    seed_all(seed)
    env = universe.create_environment(num_agents=num_agents, level_name=ITEMS_LEVEL, device="cpu")
    seed_all(seed)
    env.reset()
    return env


def test_world0s_item_activity_and_random_draws_leave_every_other_world_identical(items_universe) -> None:
    """The verifier's items_leak: world 0's extra spawns used to shift every later world's placement."""
    env = _items_env(items_universe)
    names = {a.name: a.id for a in env.action_space.actions}
    cycle = [names["GET"], names["USE_SLOT_0"], names["RIGHT"], names["WAIT"], names["GET"], names["DOWN"], names["DROP_SLOT_0"]]
    wait = names["WAIT"]
    steps = 60
    quiet = [torch.full((N,), wait, dtype=torch.long) for _ in range(steps)]
    active = []
    for step in range(steps):
        actions = torch.full((N,), wait, dtype=torch.long)
        actions[0] = cycle[step % len(cycle)]
        active.append(actions)

    def setup(env) -> None:
        apple = next(i for i in env.item_manager.worlds[0].active.values() if i.item_type == "apple")
        env.positions[0] = torch.tensor(apple.position, dtype=env.positions.dtype)

    trace_a = _run(items_universe, ITEMS_LEVEL, quiet, setup=setup)
    trace_b = _run(items_universe, ITEMS_LEVEL, active, setup=setup)
    _assert_worlds_identical(trace_a, trace_b, range(1, N))
    assert any(a[0]["items"] != b[0]["items"] for a, b in zip(trace_a, trace_b, strict=True))


def test_same_seed_is_the_same_run(items_universe) -> None:
    env = _items_env(items_universe)
    wait = _action(env, "WAIT")
    actions = [torch.full((N,), wait, dtype=torch.long) for _ in range(30)]
    trace_a = _run(items_universe, ITEMS_LEVEL, actions, setup=lambda env: None)
    trace_b = _run(items_universe, ITEMS_LEVEL, actions, setup=lambda env: None)
    _assert_worlds_identical(trace_a, trace_b, range(N))


def test_a_bare_bar_write_from_an_item_effect_is_its_items_world_only(items_universe) -> None:
    env = _items_env(items_universe, num_agents=3)
    apple = next(iter(env.item_manager.worlds[0].active.values()))
    energy = env.meter_name_to_index["energy"]
    before = env.meters[:, energy].clone()
    env.effect_manager.spawn_effect(
        "drain", apple.vfs_index, 1.0, env.global_tick, bars=_bars(env), vfs_registry=env.vfs_registry, item_manager=env.item_manager
    )
    env.step(torch.full((3,), _action(env, "WAIT"), dtype=torch.long))
    loss = (before - env.meters[:, energy]).tolist()
    assert loss[0] == pytest.approx(loss[1] + 0.2, abs=1e-5)
    assert loss[1] == pytest.approx(loss[2], abs=1e-6)


def test_spawn_at_self_from_a_carried_item_is_at_its_holder(items_universe) -> None:
    env = _items_env(items_universe, num_agents=3)
    manager = env.item_manager
    apple = next(i for i in manager.worlds[1].active.values() if i.item_type == "apple")
    env.positions[1] = torch.tensor(apple.position, dtype=env.positions.dtype)
    get, wait = _action(env, "GET"), _action(env, "WAIT")
    env.step(torch.tensor([wait, get, wait]))
    assert apple.instance_id in manager.worlds[1].held
    ground = tuple(apple.position)
    holder_at = ((ground[0] + 2) % 5, (ground[1] + 2) % 5)
    env.positions[1] = torch.tensor(holder_at, dtype=env.positions.dtype)
    coins = {i.instance_id for i in manager.worlds[1].active.values()}
    env.effect_manager.spawn_effect(
        "drop_coin",
        apple.vfs_index,
        1.0,
        env.global_tick,
        bars=_bars(env),
        vfs_registry=env.vfs_registry,
        item_manager=manager,
        agent_positions=env.positions,
    )
    spawned = [i for i in manager.worlds[1].active.values() if i.instance_id not in coins]
    assert [tuple(i.position) for i in spawned] == [holder_at]


def test_an_item_effect_outliving_its_item_is_discarded_with_it(items_universe) -> None:
    """Verifier: wear_and_tear renewed on a medkit about to expire crashed the batch (KeyError)."""
    env = _items_env(items_universe, num_agents=2)
    manager = env.item_manager
    medkit = next(i for i in manager.worlds[0].active.values() if i.item_type == "medkit")
    medkit.duration_remaining = 2
    env.effect_manager.spawn_effect(
        "wear_and_tear", medkit.vfs_index, 1.0, env.global_tick, bars=_bars(env), vfs_registry=env.vfs_registry, item_manager=manager
    )
    wait = torch.full((2,), _action(env, "WAIT"), dtype=torch.long)
    for _ in range(5):
        env.step(wait)
    assert medkit.instance_id not in manager.live_items
    assert medkit.vfs_index not in env.effect_manager.item_effects


def test_ground_capacity_is_max_items_in_world(items_universe) -> None:
    env = _items_env(items_universe, num_agents=2)
    manager = env.item_manager
    manager.reset_state()
    limit = items_universe.items_catalog.max_items_in_world
    assert env.items_per_world > limit  # the arena also holds carried items
    cells = [(x, y) for x in range(5) for y in range(5)]
    spawned = [manager.spawn_item(0, "apple", cell, 0) for cell in cells[: env.items_per_world]]
    assert sum(item is not None for item in spawned) == limit
    assert manager.spawn_item(1, "apple", (0, 0), 0) is not None  # world 1 is unaffected


def test_an_item_ref_must_name_a_row_of_its_own_world() -> None:
    from townlet.vfs.profiles import CompiledItemProfile, CompiledVariable

    other = CompiledVariable(
        name="other", type="item_ref", exposed_to=(), lifetime="episode", readable_by=("engine",), writable_by=("engine",), initial_value=-1
    )
    profile = CompiledItemProfile(profile_name="p", variables=[other])
    registry = VariableRegistry(
        [
            VariableDef(
                id="ref", scope="agent", type="item_ref", lifetime="episode", default=-1, readable_by=["engine"], writable_by=["engine"]
            )
        ],
        3,
        torch.device("cpu"),
        items_per_world=4,
        item_profiles={"p": profile},
    )
    registry.set("ref", torch.tensor([-1, 5, 11]), writer="engine")  # world 1 -> row 5, world 2 -> row 11
    with pytest.raises(RuntimeError, match="Engine defect: item_ref 'ref' in world 0 names item row 9"):
        registry.set("ref", torch.tensor([9, -1, -1]), writer="engine")
    registry.register_item_instance(5, "p")
    registry.write_item("p", "other", 6.0, 5, writer="engine")
    with pytest.raises(RuntimeError, match="Engine defect: item_ref 'p.other' on item row 5"):
        registry.write_item("p", "other", 1.0, 5, writer="engine")


def test_the_item_arena_is_guarded_like_every_other_tensor(items_universe) -> None:
    profiles = items_universe.compiled_vfs_profiles.item_profiles
    with pytest.raises(ValueError, match="Item arena .* exceeds max supported elements"):
        VariableRegistry(variables=[], num_agents=4096, items_per_world=1000, device=torch.device("cpu"), item_profiles=profiles)


def test_each_worlds_item_stream_is_its_own() -> None:
    """Extra random placements in world 0 never move world 1's (the cross-world RNG leak)."""
    from townlet.config.items_config import ItemAppearanceRuleConfig, ItemsCatalogConfig, SpawnPlacementConfig
    from townlet.items.manager import ItemManager
    from townlet.substrate.grid2d import Grid2DSubstrate

    catalog = ItemsCatalogConfig.from_yaml(path=ITEMS_SMOKE / "items.yaml")
    rule = ItemAppearanceRuleConfig(item_type="apple", spawn_count=3, placement=SpawnPlacementConfig(mode="random"))
    substrate = Grid2DSubstrate(width=8, height=8, boundary="clamp", distance_metric="manhattan", enable_diagonals=False)

    def placements(extra_world0_draws: int) -> list[Any]:
        torch.manual_seed(5)
        manager = ItemManager(catalog=catalog, num_worlds=2, substrate=substrate, items_per_world=13, device="cpu")
        for _ in range(extra_world0_draws):
            manager._placement_positions(0, rule, current_tick=0, count=3)
        return manager._placement_positions(1, rule, current_tick=0, count=3)

    assert placements(0) == placements(4)
