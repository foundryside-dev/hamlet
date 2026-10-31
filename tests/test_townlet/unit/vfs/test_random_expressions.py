"""Random draws reach VFS state (re-review `authoring` A2).

`uniform` and `normal_dist` are admitted in global and agent variable expressions,
transition rules and action writes. A draw is one per row of its context, from that
world's own stream (`townlet.vfs.random_streams.WorldRandomStreams`, S1): world w's
draws depend on the run seed, the episode and w alone, never on the batch size or on
another world's actions. The item spawn predicate carries no stream and refuses.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.determinism import seed_all
from townlet.items.manager import SpawnPredicateReads
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.evaluator import VFSEvaluator
from townlet.vfs.namespace import SPAWN_PREDICATE
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.vtc import VTCTransitionRuleProgram, VTCWriteTarget, compile_vtc_transition_rules
from townlet.world.expression import ExpressionParser

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
N = 4
STEPS = 64
MINMAX = {"kind": "minmax", "min": 0.0, "max": 3.0, "clip": True}


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


def _rule(rule_id: str, variable_id: str, expression: str, *, condition: str | None = None, composition: str = "overwrite") -> dict:
    return {
        "id": rule_id,
        "phase": "apply_transition_rules",
        "condition": condition,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": expression,
                "composition": composition,
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }


def _pack(
    tmp_path: Path,
    declarations: list[dict],
    *,
    rules: list[dict] | None = None,
    advance_writes: list[dict] | None = None,
    name: str = "pack",
) -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"] += declarations
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    if rules is not None:
        (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": rules}, sort_keys=False))
    if advance_writes is not None:
        actions_path = pack / "actions.yaml"
        actions = yaml.safe_load(actions_path.read_text())
        advance = next(action for action in actions["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"] += advance_writes
        actions_path.write_text(yaml.safe_dump(actions, sort_keys=False))
    return pack


def _compile(pack: Path):
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _refusal(pack: Path) -> str:
    with pytest.raises(CompilationError) as excinfo:
        _compile(pack)
    return str(excinfo.value)


def _action(env, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


def _reg(env, var_id: str) -> torch.Tensor:
    return env.vfs_registry.get(var_id, reader="engine")


# The authored mechanics under test: per-world weather that re-rolls every 4 ticks (a
# global expression closed through `lag`), a per-agent literal-argument draw, a draw around
# a per-agent value, a rule rolling a global, and an action write rolling an agent value.
RANDOM_DECLARATIONS = [
    _decl(
        "weather",
        scope="global",
        expression="where(tick % 4 == 0, uniform(0.0, 3.0), lag(weather, 1))",
        exposed_to=["agent"],
        normalization=MINMAX,
    ),
    _decl("noise", expression="uniform(0.0, 1.0)"),
    _decl("jitter", expression="normal_dist(public_state, 0.1)"),
    _decl("yesterday", scope="global", expression="lag(weather, 1)"),
    _decl("roll", scope="global"),
    _decl("luck"),
]
RANDOM_RULES = [_rule("roll_rule", "roll", "uniform(0.0, 1.0)")]
ADVANCE_LUCK = [
    {
        "variable_id": "luck",
        "expression": "uniform(0.0, 1.0)",
        "condition": None,
        "composition": "overwrite",
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": None,
        "telemetry_label": "advance_luck",
    }
]
RANDOM_VARIABLES = ("weather", "noise", "jitter", "yesterday", "roll", "luck")


@pytest.fixture(scope="module")
def random_universe(tmp_path_factory: pytest.TempPathFactory):
    return _compile(_pack(tmp_path_factory.mktemp("random"), RANDOM_DECLARATIONS, rules=RANDOM_RULES, advance_writes=ADVANCE_LUCK))


def _snapshot(env, world: int, obs: torch.Tensor) -> dict[str, Any]:
    return {
        "obs": obs[world].clone(),
        "meters": env.meters[world].clone(),
        "position": env.positions[world].clone(),
        "registry": {var_id: _reg(env, var_id)[world].clone() for var_id in env.vfs_registry.variables},
    }


def _run(universe, actions: list[torch.Tensor], *, num_agents: int = N, seed: int = 7) -> list[list[dict[str, Any]]]:
    """Per step (reset first), every world's snapshot."""
    seed_all(seed)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    seed_all(seed)
    obs = env.reset()
    trace = [[_snapshot(env, world, obs) for world in range(num_agents)]]
    for step_actions in actions:
        obs, _, _, _ = env.step(step_actions)
        trace.append([_snapshot(env, world, obs) for world in range(num_agents)])
    return trace


def _assert_equal(a: Any, b: Any, where: str) -> None:
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b), where
    elif isinstance(a, dict):
        assert a.keys() == b.keys(), where
        for key in a:
            _assert_equal(a[key], b[key], f"{where}.{key}")
    elif isinstance(a, list):
        assert len(a) == len(b), where
        for index, (left, right) in enumerate(zip(a, b, strict=True)):
            _assert_equal(left, right, f"{where}[{index}]")
    else:
        assert a == b, where


def _quiet(env_like_num_agents: int, wait: int, steps: int) -> list[torch.Tensor]:
    return [torch.full((env_like_num_agents,), wait, dtype=torch.long) for _ in range(steps)]


# --- admission -------------------------------------------------------------------------------


def test_random_draws_compile_in_expressions_rules_and_action_writes(random_universe) -> None:
    schedule = random_universe.get_level(LEVEL).transition_schedule
    assert {rule.variable_id for rule in schedule.transition_rule_program.rules} == {"roll"}
    assert "luck" in {write.variable_id for write in schedule.action_write_program.writes}


def test_a_literal_argument_draw_in_an_agent_expression_is_one_draw_per_row(random_universe) -> None:
    seed_all(3)
    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    noise = _reg(env, "noise")
    assert noise.shape == (N,)
    assert len(set(noise.tolist())) == N
    assert torch.all((noise >= 0.0) & (noise < 1.0))


def test_a_global_draw_differs_across_worlds_and_a_rule_rolls_per_world(random_universe) -> None:
    seed_all(3)
    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    wait = _action(env, "WAIT")
    env.step(torch.full((N,), wait, dtype=torch.long))
    assert len(set(_reg(env, "weather").tolist())) == N
    assert len(set(_reg(env, "roll").tolist())) == N
    assert torch.all((_reg(env, "weather") >= 0.0) & (_reg(env, "weather") < 3.0))


def test_weather_holds_for_k_ticks_and_lag_of_a_random_variable_reads_its_history(random_universe) -> None:
    seed_all(5)
    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    wait = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
    weather = [_reg(env, "weather").clone()]
    yesterday = [_reg(env, "yesterday").clone()]
    for _ in range(9):
        env.step(wait)
        weather.append(_reg(env, "weather").clone())
        yesterday.append(_reg(env, "yesterday").clone())
    # Ticks 0..3 hold the tick-0 roll, 4..7 the tick-4 roll, 8.. the tick-8 roll.
    for tick in range(1, 4):
        assert torch.equal(weather[tick], weather[0]), tick
    for tick in range(5, 8):
        assert torch.equal(weather[tick], weather[4]), tick
    assert not torch.equal(weather[4], weather[0])
    assert not torch.equal(weather[8], weather[4])
    # `yesterday` is the committed weather of the previous instant (the declared 0.0 at tick 0).
    assert torch.equal(yesterday[0], torch.zeros(N))
    for tick in range(1, 10):
        assert torch.equal(yesterday[tick], weather[tick - 1]), tick


def test_an_action_write_draw_lands_on_the_acting_agents_row_only(random_universe) -> None:
    seed_all(5)
    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    actions = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
    actions[1] = _action(env, "ADVANCE")
    env.step(actions)
    luck = _reg(env, "luck")
    assert luck[1] != 0.0
    assert torch.equal(luck[[0, 2, 3]], torch.zeros(3))


# --- S1: isolation, reproducibility, batch-size independence --------------------------------


def test_same_seed_runs_are_bitwise_identical(random_universe) -> None:
    seed_all(7)
    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    wait, advance = _action(probe, "WAIT"), _action(probe, "ADVANCE")
    actions = _quiet(N, wait, STEPS)
    for step in range(0, STEPS, 3):
        actions[step] = actions[step].clone()
        actions[step][step % N] = advance
    _assert_equal(_run(random_universe, actions), _run(random_universe, actions), "A/A")


def test_world0s_actions_leave_every_other_worlds_draws_identical(random_universe) -> None:
    seed_all(7)
    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    wait, advance = _action(probe, "WAIT"), _action(probe, "ADVANCE")
    movement = [index for index, action in enumerate(probe.action_space.actions) if action.name not in {"WAIT", "ADVANCE", "INTERACT"}]
    quiet = _quiet(N, wait, STEPS)
    busy = [row.clone() for row in quiet]
    for step in range(STEPS):
        busy[step][0] = advance if step % 2 else movement[step % len(movement)]

    trace_a = _run(random_universe, quiet)
    trace_b = _run(random_universe, busy)

    for step, (snap_a, snap_b) in enumerate(zip(trace_a, trace_b, strict=True)):
        for world in range(1, N):
            _assert_equal(snap_a[world], snap_b[world], f"step {step} world {world}")
    # World 0 did act: its action-write draw and its public state moved.
    assert trace_b[-1][0]["registry"]["luck"] != 0.0
    assert trace_b[-1][0]["registry"]["public_state"] > 0.0


def test_a_worlds_draws_do_not_depend_on_the_batch_size(random_universe) -> None:
    seed_all(7)
    probe = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    wait = _action(probe, "WAIT")
    small = _run(random_universe, _quiet(N, wait, 16), num_agents=N)
    large = _run(random_universe, _quiet(2 * N, wait, 16), num_agents=2 * N)
    for step, (snap_small, snap_large) in enumerate(zip(small, large, strict=True)):
        for world in range(N):
            for var_id in ("weather", "noise", "roll", "yesterday"):
                assert torch.equal(snap_small[world]["registry"][var_id], snap_large[world]["registry"][var_id]), (step, world, var_id)


def test_a_new_episode_re_derives_every_worlds_stream(random_universe) -> None:
    seed_all(11)
    env = random_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    first = _reg(env, "noise").clone()
    env.reset()
    assert not torch.equal(_reg(env, "noise"), first)


# --- lifetimes and consumers -----------------------------------------------------------------


def test_a_random_expression_is_stored_not_inlined_so_a_rule_reads_the_observed_draw(tmp_path: Path) -> None:
    """Inlining `coin` into the rule would draw again; the rule must see the value the observation showed."""
    pack = _pack(
        tmp_path,
        [_decl("coin", scope="global", expression="uniform(0.0, 1.0)"), _decl("copy", scope="global")],
        rules=[_rule("copy_rule", "copy", "coin")],
    )
    universe = _compile(pack)
    seed_all(2)
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    wait = torch.full((N,), _action(env, "WAIT"), dtype=torch.long)
    for _ in range(3):
        shown = _reg(env, "coin").clone()
        env.step(wait)
        # The rule ran at instant k on the draw the instant-k observation carried; `coin`
        # then re-rolled for instant k+1.
        assert torch.equal(_reg(env, "copy"), shown)
        assert not torch.equal(_reg(env, "coin"), shown)


def test_a_tick_lifetime_random_expression_compiles_but_a_rule_reading_it_refuses(tmp_path: Path) -> None:
    _compile(_pack(tmp_path, [_decl("flash", scope="global", lifetime="tick", expression="uniform(0.0, 1.0)")], name="alone"))
    message = _refusal(
        _pack(
            tmp_path,
            [_decl("flash", scope="global", lifetime="tick", expression="uniform(0.0, 1.0)"), _decl("copy", scope="global")],
            rules=[_rule("copy_rule", "copy", "flash")],
            name="read",
        )
    )
    assert "tick-lifetime expression variable 'flash'" in message
    assert "a random stream on the context" in message
    assert "lifetime episode" in message


def test_an_item_spawn_predicate_refuses_a_draw_and_names_the_expression_variable_route() -> None:
    namespace = SpawnPredicateReads.namespace(
        meter_names=["energy"],
        variables=[
            VariableDef(
                id="g", scope="global", type="scalar", lifetime="episode", default=0.0, readable_by=["engine"], writable_by=["engine"]
            )
        ],
    )
    (refusal,) = namespace.refusals(ExpressionParser().parse("uniform(0.0, 1.0) < g"), SPAWN_PREDICATE)
    assert "'uniform', which needs a random stream on the context, which an item spawn predicate does not carry" in refusal
    assert "Declare the quantity as a global or agent expression variable and read it by name" in refusal


# --- the engine never falls through to torch's global stream --------------------------------


def _profile(expression: str) -> CompiledGlobalProfile:
    variable = CompiledVariable(
        readable_by=("engine", "agent"),
        writable_by=("engine",),
        name="x",
        lifetime="episode",
        type="float",
        exposed_to=(),
        expression=expression,
        ast=ExpressionParser().parse(expression),
    )
    return CompiledGlobalProfile(variables=[variable], dependencies={"x": ()})


def test_the_profile_evaluator_refuses_to_sample_without_the_world_streams() -> None:
    evaluator = VFSEvaluator(history_spec=None)
    with pytest.raises(RuntimeError, match="Engine defect: expression variable 'x' samples"):
        evaluator.evaluate_global_profile(_profile("uniform(0.0, 1.0)"), bars={}, vfs_state={}, marks={"x"}, device=torch.device("cpu"))
    generators = tuple(torch.Generator().manual_seed(seed) for seed in (1, 2, 3))
    drawn = evaluator.evaluate_global_profile(
        _profile("uniform(0.0, 1.0)"), bars={}, vfs_state={}, marks={"x"}, device=torch.device("cpu"), world_rngs=generators
    )["x"]
    assert drawn.shape == (3,)
    assert torch.equal(drawn, torch.stack([torch.rand((), generator=torch.Generator().manual_seed(seed)) for seed in (1, 2, 3)]))


def test_a_rule_program_refuses_to_sample_without_the_world_streams() -> None:
    targets = {"g": VTCWriteTarget(VariableScope.GLOBAL, "scalar", meter=False, expression=None)}
    program = compile_vtc_transition_rules([_rule("r", "g", "uniform(0.0, 1.0)")], targets)
    with pytest.raises(RuntimeError, match="Engine defect: VTC transition rules ran without the world random streams"):
        VTCTransitionRuleProgram(program.rules).apply(
            vfs_state={"g": torch.zeros(2)}, active_mask=torch.tensor([True, True]), device=torch.device("cpu"), world_rngs=None
        )
    with pytest.raises(RuntimeError, match="3 world streams for 2 worlds"):
        VTCTransitionRuleProgram(program.rules).apply(
            vfs_state={"g": torch.zeros(2)},
            active_mask=torch.tensor([True, True]),
            device=torch.device("cpu"),
            world_rngs=tuple(torch.Generator() for _ in range(3)),
        )
