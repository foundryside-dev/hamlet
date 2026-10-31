"""Repairs for the adversarial verification of 636192e0 (R3 verifier, V1-V7).

VFS draws are counter-based (`townlet.vfs.random_draws`): every value is a pure function of
(seed, episode, tick, site, world, element). Each case compiles a scratch pack and steps it.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.determinism import seed_all
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
MINMAX = {"kind": "minmax", "min": 0.0, "max": 3.0, "clip": True}


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


def _write(variable_id: str, expression: str, *, condition: str | None = None) -> dict:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "composition": "overwrite",
        "condition": condition,
        "clamp": None,
        "effect": None,
    }


def _rule(rule_id: str, writes: list[dict], *, condition: str | None = None) -> dict:
    return {"id": rule_id, "phase": "apply_transition_rules", "condition": condition, "writes": writes}


def _pack(tmp_path: Path, declarations: list[dict], *, rules: list[dict] | None = None, name: str = "pack") -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"] += declarations
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    if rules is not None:
        (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": rules}, sort_keys=False))
    return pack


def _compile(pack: Path):
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _refusal(pack: Path) -> str:
    with pytest.raises(CompilationError) as caught:
        _compile(pack)
    return str(caught.value)


def _env(universe, num_agents: int, seed: int = 7):
    seed_all(seed)
    env = universe.create_environment(num_agents=num_agents, level_name=LEVEL, device="cpu")
    env.reset()
    return env


def _wait(env) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == "WAIT")


def _reg(env, var_id: str) -> torch.Tensor:
    return env.vfs_registry.get(var_id, reader="engine").clone()


def _trajectory(universe, variables: tuple[str, ...], *, num_agents: int, steps: int, seed: int = 7) -> list[dict[str, torch.Tensor]]:
    env = _env(universe, num_agents, seed)
    wait = _wait(env)
    trace = [{name: _reg(env, name) for name in variables}]
    for _ in range(steps):
        env.step(torch.full((num_agents,), wait, dtype=torch.long))
        trace.append({name: _reg(env, name) for name in variables})
    return trace


# --- V1: a draw fills its context's full joined shape, every element its own world's -----

AFFORDANCE_DECLS = [_decl("aff_v", scope="affordance"), _decl("aff_w", scope="affordance", initial_value=1.0)]


@pytest.mark.parametrize(
    "expression",
    ["uniform() * aff_w", "uniform(0.0, aff_w)", "where(aff_w > 0.5, uniform(), 0.0)", "normal_dist(0.0, aff_w)", "uniform()"],
)
def test_v1_an_affordance_rule_draw_is_one_value_per_world_affordance_row(tmp_path: Path, expression: str) -> None:
    universe = _compile(_pack(tmp_path, AFFORDANCE_DECLS, rules=[_rule("roll", [_write("aff_v", expression)])]))
    by_n: dict[int, torch.Tensor] = {}
    for num_agents in (1, 3, 4, 7):
        env = _env(universe, num_agents)
        env.step(torch.full((num_agents,), _wait(env), dtype=torch.long))
        value = _reg(env, "aff_v")
        affordances = value.shape[1]
        assert value.shape == (num_agents, affordances)
        # Every element of a world's row is its own draw, and no two worlds share a row.
        assert all(len(set(value[world].tolist())) == affordances for world in range(num_agents))
        assert len({tuple(value[world].tolist()) for world in range(num_agents)}) == num_agents
        by_n[num_agents] = value
    for num_agents in (3, 4, 7):  # N-independence: world w's row is the same whatever the batch size
        assert torch.equal(by_n[num_agents][:1], by_n[1])
        assert torch.equal(by_n[num_agents][:3], by_n[7][:3])


def test_v1_a_rule_condition_draw_on_an_affordance_target_is_per_row(tmp_path: Path) -> None:
    rules = [_rule("gate", [_write("aff_v", "1.0", condition="uniform() < aff_w * 0.5")])]
    universe = _compile(_pack(tmp_path, AFFORDANCE_DECLS, rules=rules))
    seven = _env(universe, 7)
    seven.step(torch.full((7,), _wait(seven), dtype=torch.long))
    one = _env(universe, 1)
    one.step(torch.full((1,), _wait(one), dtype=torch.long))
    fired = _reg(seven, "aff_v")
    assert torch.equal(fired[:1], _reg(one, "aff_v"))
    assert len({tuple(fired[world].tolist()) for world in range(7)}) > 1


def test_v1_a_rule_conditions_draw_is_shared_by_all_its_writes(tmp_path: Path) -> None:
    """The rule-level condition is one draw per row for the whole rule: its writes fire together."""
    declarations = [_decl("first"), _decl("second")]
    rules = [_rule("coin", [_write("first", "1.0"), _write("second", "1.0")], condition="uniform() < 0.5")]
    universe = _compile(_pack(tmp_path, declarations, rules=rules))
    env = _env(universe, 64)
    env.step(torch.full((64,), _wait(env), dtype=torch.long))
    first, second = _reg(env, "first"), _reg(env, "second")
    assert torch.equal(first, second)
    assert 0 < int(first.sum()) < 64


# --- V2: a draw is never a compile-time constant ------------------------------------------


def test_v2_compiling_a_draw_into_a_reference_write_consumes_no_global_randomness(tmp_path: Path) -> None:
    declarations = [_decl("aref", type_="agent_ref", initial_value=None)]
    rules = [_rule("pick", [_write("aref", "where(uniform() < 0.5, -1, 0)")])]
    pack = _pack(tmp_path, declarations, rules=rules)
    outcomes = set()
    for seed in range(12):
        torch.manual_seed(seed)
        before = torch.get_rng_state()
        message = _refusal(pack)
        assert torch.equal(before, torch.get_rng_state()), "the compile drew from torch's global generator"
        outcomes.add("not provably an entity of the writing world" in message)
    assert outcomes == {True}, "admission must not depend on the global seed"


def test_v2_the_constant_folder_refuses_a_draw() -> None:
    from townlet.vfs.vtc import _is_constant
    from townlet.world.expression import ExpressionParser

    parser = ExpressionParser()
    assert _is_constant(parser.parse("max(-1, 0) - 1"))
    assert not _is_constant(parser.parse("where(uniform() < 0.5, -1, 0)"))
    assert not _is_constant(parser.parse("normal_dist()"))


def test_v2_a_draw_into_a_vector_target_is_not_a_constant(tmp_path: Path) -> None:
    declarations = [_decl("vec", type_="vec2f", initial_value=[0.0, 0.0])]
    message = _refusal(_pack(tmp_path, declarations, rules=[_rule("spread", [_write("vec", "uniform()")])]))
    assert "it draws a random value per row" in message


# --- V3: draws are keyed on stable sites, not on evaluation order -------------------------

V3_DECLS = [
    _decl("a_one", expression="normal_dist(0.0, 1.0)"),
    _decl("g_rand", scope="global", expression="uniform(0.0, 1.0)"),
    _decl("a_two", expression="uniform(0.0, 1.0) + normal_dist(0.0, 1.0)"),
    _decl("a_target"),
    _decl("g_target", scope="global"),
]
V3_RULES = [_rule("roll_a", [_write("a_target", "uniform()")]), _rule("roll_g", [_write("g_target", "normal_dist()")])]
V3_VARS = ("a_one", "g_rand", "a_two", "a_target", "g_target")


def _same(left: list[dict[str, torch.Tensor]], right: list[dict[str, torch.Tensor]], names: tuple[str, ...] = V3_VARS) -> bool:
    return all(torch.equal(a[name], b[name]) for a, b in zip(left, right, strict=True) for name in names)


def test_v3_moving_or_reordering_declarations_rerolls_nothing(tmp_path: Path) -> None:
    base = _trajectory(_compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES, name="base")), V3_VARS, num_agents=3, steps=6)

    moved_pack = _pack(tmp_path, [d for d in V3_DECLS if d["id"] != "a_two"], rules=V3_RULES, name="moved")
    (moved_pack / "aaa").mkdir()
    early = {"variables": {"version": "1.0", "declarations": [d for d in V3_DECLS if d["id"] == "a_two"]}}
    (moved_pack / "aaa" / "early.yaml").write_text(yaml.safe_dump(early, sort_keys=False))
    assert _same(base, _trajectory(_compile(moved_pack), V3_VARS, num_agents=3, steps=6))

    reversed_pack = _pack(tmp_path, list(reversed(V3_DECLS)), rules=list(reversed(V3_RULES)), name="reversed")
    assert _same(base, _trajectory(_compile(reversed_pack), V3_VARS, num_agents=3, steps=6))


@pytest.mark.parametrize(
    ("extra_declarations", "extra_rules"),
    [
        ([_decl("unrelated_a", expression="uniform(0.0, 1.0)")], []),
        ([_decl("unrelated_g", scope="global", expression="normal_dist()")], []),
        ([_decl("unrelated_t")], [_rule("unrelated_rule", [_write("unrelated_t", "uniform()")])]),
    ],
)
def test_v3_an_unrelated_random_mechanic_rerolls_nothing_else(tmp_path: Path, extra_declarations: list, extra_rules: list) -> None:
    base = _trajectory(_compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES, name="base")), V3_VARS, num_agents=3, steps=6)
    extended = _pack(tmp_path, extra_declarations + V3_DECLS, rules=extra_rules + V3_RULES, name="extended")
    assert _same(base, _trajectory(_compile(extended), V3_VARS, num_agents=3, steps=6))


def test_v3_same_seed_is_bitwise_identical_and_another_seed_differs(tmp_path: Path) -> None:
    universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))
    first = _trajectory(universe, V3_VARS, num_agents=4, steps=8, seed=7)
    assert _same(first, _trajectory(universe, V3_VARS, num_agents=4, steps=8, seed=7))
    assert not _same(first, _trajectory(universe, V3_VARS, num_agents=4, steps=8, seed=8))


@pytest.mark.parametrize("num_agents", [2, 4, 7])
def test_v3_world0_differential(tmp_path: Path, num_agents: int) -> None:
    """World 0 acts differently (ADVANCE, then dies by its action stream); worlds 1..N-1 are untouched."""
    universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))

    def run(perturb: bool) -> list[dict[str, Any]]:
        env = _env(universe, num_agents)
        wait = _wait(env)
        advance = next(index for index, action in enumerate(env.action_space.actions) if action.name == "ADVANCE")
        trace = []
        for step in range(24):
            actions = torch.full((num_agents,), wait, dtype=torch.long)
            if perturb:
                actions[0] = advance if step % 2 == 0 else (step % env.action_dim)
            obs, rewards, dones, _ = env.step(actions)
            trace.append(
                {
                    "obs": obs[1:].clone(),
                    "rewards": rewards[1:].clone(),
                    "dones": dones[1:].clone(),
                    "meters": env.meters[1:].clone(),
                    **{name: _reg(env, name)[1:] for name in env.vfs_registry.variables if _reg(env, name).dim() >= 1},
                }
            )
        return trace

    quiet, perturbed = run(False), run(True)
    for left, right in zip(quiet, perturbed, strict=True):
        for key in left:
            assert torch.equal(left[key], right[key]), key


def test_v3_resume_from_a_checkpoint_reproduces_the_draws(tmp_path: Path) -> None:
    """The draw state is (seed, episode). Checkpointed between episodes (as the runner does) and
    restored into a fresh env in a differently seeded process, every later draw is the original's,
    tick for tick: a value is a pure function of seed, episode, tick, site, world and element."""
    universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))
    original = _env(universe, 3, seed=11)
    wait = _wait(original)
    for _ in range(2):
        for _ in range(3):
            original.step(torch.full((3,), wait, dtype=torch.long))
        original.reset()
    checkpoint = original.vfs_random_state()
    original.reset()
    original_ticks = [{name: _reg(original, name) for name in V3_VARS}]
    for _ in range(5):
        original.step(torch.full((3,), wait, dtype=torch.long))
        original_ticks.append({name: _reg(original, name) for name in V3_VARS})

    seed_all(999)
    resumed = universe.create_environment(num_agents=3, level_name=LEVEL, device="cpu")
    resumed.restore_vfs_random_state(checkpoint)
    resumed.reset()
    for tick, expected in enumerate(original_ticks):
        if tick:
            resumed.step(torch.full((3,), wait, dtype=torch.long))
        for name in V3_VARS:
            assert torch.equal(_reg(resumed, name), expected[name]), (tick, name)


def test_v3_the_runner_checkpoint_carries_the_draw_state() -> None:
    from townlet.training.checkpoint_utils import CHECKPOINT_FORMAT_VERSION, DEMO_CHECKPOINT_KEYS

    assert "vfs_random_state" in DEMO_CHECKPOINT_KEYS and CHECKPOINT_FORMAT_VERSION == 9


def test_v7_the_seed_is_captured_at_construction(tmp_path: Path) -> None:
    """Another environment's seed_all after construction never shifts this environment's draws."""
    universe = _compile(_pack(tmp_path, V3_DECLS, rules=V3_RULES))
    seed_all(1)
    solo = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    solo.reset()
    solo.reset()
    expected = _reg(solo, "g_rand")

    seed_all(1)
    shared = universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu")
    shared.reset()
    seed_all(2)
    universe.create_environment(num_agents=2, level_name=LEVEL, device="cpu").reset()
    shared.reset()
    assert torch.equal(_reg(shared, "g_rand"), expected)


def test_draw_kernel_matches_the_reference_specification() -> None:
    from townlet.vfs.random_draws import VFSRandomness, reference_uniform

    randomness = VFSRandomness(2**63 + 12345)
    randomness.reset()
    randomness.reset()
    stream = randomness.instant(tick=9, worlds=3, device=torch.device("cpu")).stream("var:x", (3, 5))
    stream.uniform("uniform", torch.zeros(()))
    second = stream.uniform("uniform", torch.zeros(()))
    expected = [
        [reference_uniform(seed=2**63 + 12345, episode=2, tick=9, site="var:x", ordinal=1, world=w, element=e) for e in range(5)]
        for w in range(3)
    ]
    assert torch.equal(second, torch.tensor(expected, dtype=torch.float32))
    normal = randomness.instant(tick=0, worlds=8192, device=torch.device("cpu")).stream("var:n", (8192,)).normal("n", torch.zeros(()))
    assert abs(float(normal.mean())) < 0.05 and abs(float(normal.std()) - 1.0) < 0.05


# --- V4: a static initialised by initial_value_mode is read at its runtime value ---------


def test_v4_an_expression_over_a_mode_initialised_tensor_compiles_resets_and_steps(tmp_path: Path) -> None:
    tensor = _decl("t1", type_="tensor1d", shape=[3], initial_value_mode="ones")
    del tensor["initial_value"]
    declarations = [tensor, _decl("first_element", expression="gather(t1, 0) + bar.energy * 0.0")]
    env = _env(_compile(_pack(tmp_path, declarations)), 2)
    assert _reg(env, "first_element").tolist() == [1.0, 1.0]
    env.step(torch.full((2,), _wait(env), dtype=torch.long))
    assert _reg(env, "first_element").tolist() == [1.0, 1.0]


# --- V5: vector equality is refused where one bool per row is declared --------------------


@pytest.mark.parametrize("operator", ["==", "!="])
def test_v5_vector_equality_refuses_at_compile(tmp_path: Path, operator: str) -> None:
    declarations = [_decl("vecv", type_="vec2f", initial_value=[0.0, 1.0]), _decl("same", type_="bool", expression=f"vecv {operator} vecv")]
    pack = _pack(tmp_path, declarations)
    message = _refusal(pack)
    assert "'vec2f' has elements" in message
    assert _located(pack, message, "VFS-PROFILE-COMPILE").startswith("- id: same")


def test_v5_element_equality_compiles_and_steps(tmp_path: Path) -> None:
    declarations = [
        _decl("vecv", type_="vec2f", initial_value=[0.0, 1.0]),
        _decl("same", type_="bool", expression="gather(vecv, 1) == 1.0"),
    ]
    env = _env(_compile(_pack(tmp_path, declarations)), 2)
    env.step(torch.full((2,), _wait(env), dtype=torch.long))
    assert _reg(env, "same").tolist() == [True, True]


# --- V6: a position function names a deployed affordance, refused at compile otherwise -----


def _located(pack: Path, message: str, code: str) -> str:
    import re

    match = re.search(rf"\[{re.escape(code)}\] (\S+):(\d+)", message)
    assert match is not None, message
    path, line = Path(match.group(1)), int(match.group(2))
    assert path.is_relative_to(pack)
    return path.read_text().splitlines()[line - 1].strip()


def test_v6_an_unknown_affordance_name_refuses_at_the_expression(tmp_path: Path) -> None:
    pack = _pack(tmp_path, [_decl("to_nope", expression='distance_to_affordance("NOPE")')])
    message = _refusal(pack)
    assert "no affordance is named 'NOPE'" in message
    assert _located(pack, message, "EXPRESSION-AFFORDANCE-UNKNOWN").startswith("expression:")


@pytest.mark.parametrize("call", ['distance_to_affordance("COOK")', 'in_range("COOK", 1.0)'])
def test_v6_an_undeployed_affordance_refuses_naming_the_level(tmp_path: Path, call: str) -> None:
    kind = "bool" if call.startswith("in_range") else "scalar"
    pack = _pack(tmp_path, [_decl("to_cook", type_=kind, expression=call)])
    training = pack / f"levels/{LEVEL}/training.yaml"
    training.write_text(training.read_text().replace("    - COOK\n", ""))
    message = _refusal(pack)
    assert f"level '{LEVEL}' does not deploy 'COOK'" in message


def test_v6_a_deployed_affordance_compiles_exposed_and_reads_a_finite_distance(tmp_path: Path) -> None:
    declaration = _decl(
        "to_cook",
        expression='distance_to_affordance("COOK")',
        exposed_to=["agent"],
        normalization={"kind": "minmax", "min": 0.0, "max": 16.0, "clip": True},
    )
    env = _env(_compile(_pack(tmp_path, [declaration])), 2)
    env.step(torch.full((2,), _wait(env), dtype=torch.long))
    assert bool(torch.isfinite(_reg(env, "to_cook")).all())


# --- P3: declared widths and literal indices are static facts ------------------------------


@pytest.mark.parametrize(
    ("declarations", "expression", "code"),
    [
        (
            [_decl("v2", type_="vec2f", initial_value=[0.0, 0.0]), _decl("v3", type_="vec3f", initial_value=[0.0, 0.0, 0.0])],
            "distance(v2, v3)",
            "EXPRESSION-VECTOR-WIDTH",
        ),
        (
            [_decl("vn", type_="vecNf", dims=4, initial_value=[0.0] * 4), _decl("v2", type_="vec2f", initial_value=[0.0, 0.0])],
            "manhattan_distance(vn, v2)",
            "EXPRESSION-VECTOR-WIDTH",
        ),
        ([_decl("v2", type_="vec2f", initial_value=[0.0, 0.0])], "gather(v2, 5) + bar.energy", "EXPRESSION-INDEX-RANGE"),
        ([_decl("v2", type_="vec2f", initial_value=[0.0, 0.0])], "gather(v2, -1) + bar.energy", "EXPRESSION-INDEX-RANGE"),
    ],
)
def test_p3_static_width_and_index_errors_refuse_at_compile(tmp_path: Path, declarations: list, expression: str, code: str) -> None:
    pack = _pack(tmp_path, [*declarations, _decl("probe", expression=expression)])
    message = _refusal(pack)
    assert _located(pack, message, code).startswith("expression:")


def test_p3_matching_widths_and_in_range_indices_compile_and_step(tmp_path: Path) -> None:
    declarations = [
        _decl("v2", type_="vec2f", initial_value=[3.0, 4.0]),
        _decl("w2", type_="vec2f", initial_value=[0.0, 0.0]),
        _decl("probe", expression="distance(v2, w2) + gather(v2, 1) + bar.energy * 0.0"),
    ]
    env = _env(_compile(_pack(tmp_path, declarations)), 2)
    env.step(torch.full((2,), _wait(env), dtype=torch.long))
    assert _reg(env, "probe").tolist() == pytest.approx([9.0, 9.0])
