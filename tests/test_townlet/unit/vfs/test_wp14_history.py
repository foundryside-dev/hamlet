"""WP14 (review-2026-10-24 VFS F9, S9): the temporal-history operators are live.

Reproduction `r9_history_operators.py`: every profile expression using `lag`, `delta`,
`moving_average`, `ema`, `rate_of_change`, `rising_edge` or `falling_edge` was refused by
the shape proof, so `vfs_history_spec` was always None and the history pipeline was dead.
They are now pointwise in shape, collected from the global and the agent profile, and a
`lag` read is not a dependency edge, so `t: where(<event>, 0.0, lag(t, 1) + 1.0)` is one
declaration. The runtime contract (world/expression/history.py, variables.md "History
operators"):

- one committed sample per instant, after every expression of the instant evaluates;
- before `n` instants exist, `lag(x, n)` is the value `x` held when the episode began
  (declared initial for tick/episode lifetime, carried value for persistent);
- history is episode-scoped for every lifetime; a dead world's history does not advance.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.config.variables_config import VariableDeclaration
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.evaluator import VFSEvaluator
from townlet.vfs.history import collect_history_requirements
from townlet.vfs.profiles import VFSProfileCompiler
from townlet.vfs.schema_hashes import compute_expression_schema_hash

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
L5 = REPO / "configs" / "L5_multi_agent"
L5_LEVEL = "L5_multi_agent"


# --- pack helpers ---------------------------------------------------------------------------


def _decl(var_id: str, *, scope: str = "agent", type_: str = "scalar", lifetime: str = "episode", **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": type_,
        "lifetime": lifetime,
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": False if type_ == "bool" else 0.0,
    }
    declaration.update(extra)
    return declaration


def _pack(tmp_path: Path, declarations: list[dict], name: str = "pack") -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"] += declarations
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return pack


def _compile(pack: Path, level: str = LEVEL):
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _env(universe, num_agents: int = 2, level: str = LEVEL):
    env = universe.create_environment(num_agents=num_agents, level_name=level, device="cpu")
    env.reset()
    return env


def _action(env, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


def _reg(env, var_id: str) -> list:
    return env.vfs_registry.get(var_id, reader="engine").tolist()


def _all(env, name: str) -> torch.Tensor:
    return torch.full((env.num_agents,), _action(env, name), dtype=torch.long)


# --- r9: every operator compiles, is collected, and tracks ------------------------------------


R9_CASES = {
    # ADVANCE adds 1.0 to public_state each step; energy loses 0.01 passively; tick counts instants.
    "agent_lag_bar": (
        [_decl("prev_energy", expression="lag(bar.energy, 1)")],
        {"bar.energy": 1},
        {"prev_energy": [1.0, 1.0, 0.99, 0.98]},
    ),
    "agent_delta_var": (
        [_decl("d_public", expression="delta(public_state)")],
        {"vfs.public_state": 1},
        {"d_public": [0.0, 1.0, 1.0, 1.0]},
    ),
    "global_lag_tick": (
        [_decl("prev_tick", scope="global", expression="lag(tick, 1)")],
        {"vfs.tick": 1},
        {"prev_tick": [0.0, 0.0, 1.0, 2.0]},
    ),
    "global_ema_tick": (
        [_decl("ema_tick", scope="global", expression="ema(tick, 0.5)")],
        {"vfs.tick": 1},
        {"ema_tick": [0.0, 0.5, 1.25, 2.125]},
    ),
    # r9's `rising_edge(tick > 1.0)` names no value; the predicate is declared and named instead.
    "global_rising_edge": (
        [
            _decl("late", scope="global", type_="bool", expression="tick > 1.0"),
            _decl("edge", scope="global", type_="bool", expression="rising_edge(late)"),
        ],
        {"vfs.late": 1},
        {"edge": [False, False, True, False]},
    ),
}


@pytest.mark.parametrize("case", sorted(R9_CASES))
def test_r9_operator_compiles_is_collected_and_tracks(tmp_path: Path, case: str) -> None:
    declarations, spec, expected = R9_CASES[case]
    universe = _compile(_pack(tmp_path, declarations))
    assert universe.vfs_history_spec == spec
    env = _env(universe)
    seen: dict[str, list] = {var_id: [_reg(env, var_id)[0]] for var_id in expected}
    for _ in range(3):
        env.step(_all(env, "ADVANCE"))
        for var_id in expected:
            seen[var_id].append(_reg(env, var_id)[0])
    for var_id, values in expected.items():
        assert seen[var_id] == pytest.approx(values), var_id


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        ("rising_edge(tick > 1.0)", "first argument is a computed expression"),
        ("lag(public_state + 1.0, 1)", "first argument is a computed expression"),
        ("lag(public_state, 0)", r"depth n must be in 1\.\.256; got 0"),
        ("lag(public_state, 300)", r"depth n must be in 1\.\.256; got 300"),
        ("lag(public_state, hidden_score)", "integer"),
        ("ema(public_state, 1.5)", r"alpha must be in \(0, 1\]"),
        ("moving_average(public_state, 0)", r"window must be in 1\.\.256"),
    ],
)
def test_a_temporal_call_the_runtime_cannot_serve_refuses_at_compile(tmp_path: Path, expression: str, message: str) -> None:
    pack = _pack(tmp_path, [_decl("bad", type_="bool" if "edge" in expression else "scalar", expression=expression)])
    with pytest.raises(CompilationError, match=message) as refusal:
        _compile(pack)
    assert "VFS-PROFILE-COMPILE" in str(refusal.value)
    assert "variables.yaml" in str(refusal.value)


def test_a_temporal_operator_in_an_action_write_refuses_it_keeps_no_history(tmp_path: Path) -> None:
    pack = _pack(tmp_path, [])
    actions_path = pack / "actions.yaml"
    actions = yaml.safe_load(actions_path.read_text())
    advance = next(a for a in actions["actions"]["custom_actions"] if a["name"] == "ADVANCE")
    advance["writes"][0]["expression"] = "lag(public_state, 1)"
    actions_path.write_text(yaml.safe_dump(actions, sort_keys=False))
    with pytest.raises(CompilationError, match="temporal history"):
        _compile(pack)


# --- each operator's value over a scripted sequence -------------------------------------------


def _declaration(var_id: str, expression: str | None, *, type_: str = "scalar", initial: object = 0.0) -> VariableDeclaration:
    return VariableDeclaration(
        id=var_id,
        scope="agent",
        type=type_,
        lifetime="episode",
        semantic_type="custom",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        exposed_to=[],
        initial_value=initial,
        expression=expression,
    )


def _run_scripted(declarations: list[VariableDeclaration], xs: list[list[float]], flags: list[list[bool]], lives: list[list[bool]]):
    """Drive begin_instant → evaluate → write back → commit_instant over a scripted bar `x` and static `flag`."""
    profile = VFSProfileCompiler().compile_profile(declarations, {"x": "float"}, cross_scope=[])
    evaluator = VFSEvaluator(history_spec=collect_history_requirements(None, profile))
    expressions = {d.id for d in declarations if d.expression is not None}
    state = {d.id: torch.full((2,), d.initial_value, dtype=torch.bool if d.type == "bool" else torch.float32) for d in declarations}
    trace: dict[str, list[list]] = {name: [] for name in expressions}
    for x, flag, live in zip(xs, flags, lives, strict=True):
        bars = {"x": torch.tensor(x)}
        state["flag"] = torch.tensor(flag)
        evaluator.begin_instant(bars, state, torch.device("cpu"))
        result = evaluator.evaluate_global_profile(profile, bars, dict(state), marks=expressions, num_agents=2)
        state.update({name: result[name] for name in expressions})
        evaluator.commit_instant(bars, state, live=torch.tensor(live))
        for name in expressions:
            trace[name].append(result[name].tolist())
    return trace, evaluator


SCRIPT_X = [[1.0, 5.0], [3.0, 5.0], [2.0, 5.0], [6.0, 5.0], [4.0, 5.0]]
SCRIPT_FLAG = [[False, True], [True, True], [True, True], [False, True], [True, True]]
ALL_LIVE = [[True, True]] * 5


def test_each_operator_over_a_scripted_sequence() -> None:
    declarations = [
        _declaration("flag", None, type_="bool", initial=False),
        _declaration("lag2", "lag(bar.x, 2)"),
        _declaration("d", "delta(bar.x)"),
        _declaration("ma3", "moving_average(bar.x, 3)"),
        _declaration("e", "ema(bar.x, 0.5)"),
        _declaration("roc2", "rate_of_change(bar.x, 2)"),
        _declaration("up", "rising_edge(flag)", type_="bool", initial=False),
        _declaration("down", "falling_edge(flag)", type_="bool", initial=False),
    ]
    trace, _ = _run_scripted(declarations, SCRIPT_X, SCRIPT_FLAG, ALL_LIVE)
    world0 = {name: [row[0] for row in rows] for name, rows in trace.items()}
    # x = 1, 3, 2, 6, 4; the pre-history (seed) is the episode-start value 1.
    assert world0["lag2"] == pytest.approx([1.0, 1.0, 1.0, 3.0, 2.0])
    assert world0["d"] == pytest.approx([0.0, 2.0, -1.0, 4.0, -2.0])
    assert world0["ma3"] == pytest.approx([1.0, 5 / 3, 2.0, 11 / 3, 4.0])
    assert world0["e"] == pytest.approx([1.0, 2.0, 2.0, 4.0, 4.0])
    assert world0["roc2"] == pytest.approx([0.0, 1.0, 0.5, 1.5, 1.0])
    # flag = F, T, T, F, T; its seed is its own episode-start value F.
    assert world0["up"] == [False, True, False, False, True]
    assert world0["down"] == [False, False, False, True, False]
    # World 1 holds x = 5 and flag = T throughout: no change, no edge.
    world1 = {name: [row[1] for row in rows] for name, rows in trace.items()}
    assert world1["d"] == pytest.approx([0.0] * 5)
    assert world1["ma3"] == pytest.approx([5.0] * 5)
    assert world1["up"] == [False] * 5 and world1["down"] == [False] * 5


def test_lag_before_history_exists_is_the_declared_initial_value_of_an_expression_variable() -> None:
    """`doubled`'s history seed is its declared initial value (7.0), not its first evaluation."""
    declarations = [
        _declaration("flag", None, type_="bool", initial=False),
        _declaration("doubled", "bar.x * 2.0", initial=7.0),
        _declaration("prev_doubled", "lag(doubled, 2)"),
    ]
    trace, _ = _run_scripted(declarations, SCRIPT_X, SCRIPT_FLAG, ALL_LIVE)
    assert [row[0] for row in trace["prev_doubled"]] == pytest.approx([7.0, 7.0, 2.0, 6.0, 4.0])


def test_a_dead_worlds_history_does_not_advance() -> None:
    """World 0 is done from instant 2: its ring and its ema freeze; world 1's advance."""
    declarations = [
        _declaration("flag", None, type_="bool", initial=False),
        _declaration("prev", "lag(bar.x, 1)"),
        _declaration("e", "ema(bar.x, 0.5)"),
    ]
    xs = [[1.0, 1.0], [3.0, 3.0], [2.0, 2.0], [6.0, 6.0], [4.0, 4.0]]
    lives = [[True, True], [True, True], [False, True], [False, True], [False, True]]
    trace, _ = _run_scripted(declarations, xs, SCRIPT_FLAG, lives)
    prev = trace["prev"]
    assert [row[1] for row in prev] == pytest.approx([1.0, 1.0, 3.0, 2.0, 6.0])
    # Instant 2's sample (2.0) is never committed for world 0: the last committed is 3.0.
    assert [row[0] for row in prev] == pytest.approx([1.0, 1.0, 3.0, 3.0, 3.0])
    # ema's running state froze at instant 1's 2.0 for world 0.
    assert [row[0] for row in trace["e"]][3:] == pytest.approx([0.5 * 6.0 + 0.5 * 2.0, 0.5 * 4.0 + 0.5 * 2.0])


# --- lag-only self-edges ------------------------------------------------------------------------


def test_a_lag_self_edge_accumulator_is_one_declaration(tmp_path: Path) -> None:
    """`streak` counts the ticks since public_state last passed 1.5; -1.0 seeds the first tick to 0."""
    pack = _pack(tmp_path, [_decl("streak", initial_value=-1.0, expression="where(public_state > 1.5, 0.0, lag(streak, 1) + 1.0)")])
    universe = _compile(pack)
    assert universe.vfs_history_spec == {"vfs.streak": 1}
    env = _env(universe)
    values = [_reg(env, "streak")]
    for name in ("WAIT", "WAIT", "ADVANCE", "ADVANCE", "WAIT", "WAIT"):
        env.step(torch.tensor([_action(env, name), _action(env, "WAIT")]))
        values.append(_reg(env, "streak"))
    # World 0: public_state 0,0,0,1,2,2,2 -> passes 1.5 at the 4th step and stays there.
    assert [v[0] for v in values] == [0.0, 1.0, 2.0, 3.0, 0.0, 0.0, 0.0]
    assert [v[1] for v in values] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]


def test_a_cycle_closed_only_by_lag_sorts_and_evaluates(tmp_path: Path) -> None:
    pack = _pack(tmp_path, [_decl("a", expression="lag(b, 1) + 1.0"), _decl("b", expression="a * 2.0")])
    env = _env(_compile(pack))
    seen = [(_reg(env, "a")[0], _reg(env, "b")[0])]
    for _ in range(2):
        env.step(_all(env, "WAIT"))
        seen.append((_reg(env, "a")[0], _reg(env, "b")[0]))
    assert seen == [(1.0, 2.0), (3.0, 6.0), (7.0, 14.0)]


@pytest.mark.parametrize(
    "declarations",
    [
        [_decl("bad", expression="bad + 1.0")],
        [_decl("bad", expression="delta(bad) + 1.0")],
        [_decl("bad", expression="ema(bad, 0.5)")],
        [_decl("a", expression="b + 1.0"), _decl("b", expression="lag(a, 1) + a")],
    ],
    ids=["plain_self", "delta_self", "ema_self", "two_cycle_not_broken_by_lag"],
)
def test_a_cycle_not_closed_by_lag_still_refuses(tmp_path: Path, declarations: list[dict]) -> None:
    with pytest.raises(CompilationError, match="Circular dependency detected"):
        _compile(_pack(tmp_path, declarations))


def test_lag_of_an_agent_variable_in_a_global_expression_is_still_scope_widening(tmp_path: Path) -> None:
    with pytest.raises(CompilationError, match="cannot widen to per-agent state"):
        _compile(_pack(tmp_path, [_decl("g", scope="global", expression="lag(public_state, 1)")]))


# --- reset and persistent lifetime --------------------------------------------------------------


def test_episode_history_restarts_at_reset_from_the_declared_initial_value(tmp_path: Path) -> None:
    env = _env(_compile(_pack(tmp_path, [_decl("prev_public", expression="lag(public_state, 1)")])))
    for _ in range(3):
        env.step(_all(env, "ADVANCE"))
    assert _reg(env, "prev_public") == [2.0, 2.0]
    env.reset()
    # public_state is back at 0.0, and so is its history: not last episode's 3.0.
    assert _reg(env, "prev_public") == [0.0, 0.0]
    env.step(_all(env, "WAIT"))
    assert _reg(env, "prev_public") == [0.0, 0.0]


def _persistent_pack(tmp_path: Path, name: str = "pack") -> Path:
    return _pack(
        tmp_path,
        [
            _decl("p_count", scope="global", lifetime="persistent", expression="lag(p_count, 1) + 1.0"),
            _decl("p_lag3", scope="global", expression="lag(p_count, 3)"),
        ],
        name=name,
    )


def test_a_persistent_variables_history_is_seeded_with_its_carried_value_at_reset(tmp_path: Path) -> None:
    """History is episode-scoped for every lifetime. A persistent value carries across the
    reset, so `lag(p, 1)` continues the accumulation exactly, and every deeper lag collapses
    to the carried value until the ring refills."""
    env = _env(_compile(_persistent_pack(tmp_path)))
    for _ in range(4):
        env.step(_all(env, "WAIT"))
    assert _reg(env, "p_count") == [5.0, 5.0]  # instants 0..4
    assert _reg(env, "p_lag3") == [2.0, 2.0]
    env.reset()
    assert _reg(env, "p_count") == [6.0, 6.0]  # lag(p_count, 1) = the carried 5.0
    assert _reg(env, "p_lag3") == [5.0, 5.0]  # not 3.0: the previous episode is not history
    trace = []
    for _ in range(3):
        env.step(_all(env, "WAIT"))
        trace.append((_reg(env, "p_count")[0], _reg(env, "p_lag3")[0]))
    assert trace == [(7.0, 5.0), (8.0, 5.0), (9.0, 6.0)]


def test_resume_from_the_persistent_snapshot_reproduces_history_exactly(tmp_path: Path) -> None:
    """Checkpoints are taken between episodes and resume begins with reset(), which seeds
    every ring from the restored registry: history needs no checkpoint of its own."""
    universe = _compile(_persistent_pack(tmp_path))
    continuing = _env(universe)
    for _ in range(4):
        continuing.step(_all(continuing, "WAIT"))
    snapshot = continuing.vfs_registry.persistent_state()

    resumed = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    resumed.vfs_registry.restore_persistent_state(snapshot)
    for env in (continuing, resumed):
        env.reset()
    for _ in range(4):
        assert _reg(resumed, "p_count") == _reg(continuing, "p_count")
        assert _reg(resumed, "p_lag3") == _reg(continuing, "p_lag3")
        for env in (continuing, resumed):
            env.step(_all(env, "WAIT"))


# --- per-world independence ---------------------------------------------------------------------


def test_history_is_per_world_a_world0_difference_never_reaches_world1(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        [
            _decl("prev2", expression="lag(public_state, 2)"),
            _decl("smooth", expression="ema(public_state, 0.3)"),
            _decl("climb", expression="rate_of_change(public_state, 2)"),
        ],
    )
    universe = _compile(pack)
    run_a, run_b = _env(universe), _env(universe)
    wait, advance = _action(run_a, "WAIT"), _action(run_a, "ADVANCE")
    for k in range(5):
        run_a.step(torch.tensor([advance, wait]))
        run_b.step(torch.tensor([wait if k % 2 else advance, wait]))
        for var_id in ("prev2", "smooth", "climb"):
            assert _reg(run_a, var_id)[1] == _reg(run_b, var_id)[1], (k, var_id)
    assert _reg(run_a, "smooth")[0] != _reg(run_b, "smooth")[0]


def test_a_done_worlds_history_freezes_in_the_environment(tmp_path: Path) -> None:
    env = _env(_compile(_pack(tmp_path, [_decl("prev_tick", scope="global", expression="lag(tick, 1)")])))
    for _ in range(3):
        env.step(_all(env, "WAIT"))
    assert _reg(env, "prev_tick") == [2.0, 2.0]
    env.dones[0] = True  # world 0's agent is done: its world is frozen
    for _ in range(2):
        env.step(_all(env, "WAIT"))
    # World 0's last committed tick is 3 (the step it was last live); world 1 reads tick 4.
    assert _reg(env, "prev_tick") == [3.0, 4.0]


# --- history in the hash ------------------------------------------------------------------------


def test_the_hash_moves_with_the_lag_depth(tmp_path: Path) -> None:
    shallow = _compile(_pack(tmp_path, [_decl("prev", expression="lag(public_state, 1)")], name="shallow"))
    deep = _compile(_pack(tmp_path, [_decl("prev", expression="lag(public_state, 2)")], name="deep"))
    assert shallow.vfs_history_spec == {"vfs.public_state": 1}
    assert deep.vfs_history_spec == {"vfs.public_state": 2}
    assert shallow.get_level(LEVEL).vfs_hash != deep.get_level(LEVEL).vfs_hash
    profiles = [(u.compiled_vfs_profiles.global_profile, u.compiled_vfs_profiles.agent_profile) for u in (shallow, deep)]
    assert compute_expression_schema_hash(global_profile=profiles[0][0], agent_profile=profiles[0][1]) != compute_expression_schema_hash(
        global_profile=profiles[1][0], agent_profile=profiles[1][1]
    )


def test_a_lag_read_is_not_a_dependency_but_a_same_instant_read_is(tmp_path: Path) -> None:
    universe = _compile(
        _pack(tmp_path, [_decl("a", expression="lag(b, 1) + public_state"), _decl("b", expression="a * 2.0")]),
    )
    dependencies = universe.compiled_vfs_profiles.agent_profile.dependencies
    assert dependencies["a"] == ("public_state",)  # b is read through lag: no edge
    assert dependencies["b"] == ("a",)


# --- the worked example: L5 time_since_last_sleep -----------------------------------------------


def test_l5_time_since_last_sleep_counts_ticks_since_energy_last_rose() -> None:
    universe = _compile(L5, level=L5_LEVEL)
    assert universe.vfs_history_spec == {"bar.energy": 1, "vfs.time_since_last_sleep": 1}
    env = _env(universe, level=L5_LEVEL)
    sleep = env.affordances["SLEEP"]
    env.positions[0] = (sleep[0] if sleep.dim() > 1 else sleep).to(env.positions.dtype)
    occupied = {tuple((p[0] if p.dim() > 1 else p).tolist()) for p in env.affordances.values()}
    env.positions[1] = torch.tensor(next((x, y) for x in range(7, -1, -1) for y in range(7, -1, -1) if (x, y) not in occupied))
    wait, interact = _action(env, "WAIT"), _action(env, "INTERACT")
    values = [_reg(env, "time_since_last_sleep")]
    for k in range(6):
        env.step(torch.tensor([interact if k == 3 else wait, wait]))
        values.append(_reg(env, "time_since_last_sleep"))
    assert [v[0] for v in values] == [0.0, 1.0, 2.0, 3.0, 0.0, 1.0, 2.0]
    assert [v[1] for v in values] == [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
