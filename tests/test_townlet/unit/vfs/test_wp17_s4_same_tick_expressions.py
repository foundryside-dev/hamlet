"""WP17 S4 + F10 (review-2026-10-24 VFS round 2): expression variables are same-tick inputs to writes.

A designer names a derived quantity (`rich: cash > 0.5`) and gates a write on it
(`condition: rich`). Before this change the write read the value the last profile
evaluation stored: one tick behind when an earlier phase of the same tick moved the
input, and for a `tick`-lifetime variable always its declared literal, because tick
state resets before the action phases and profiles evaluate only at the end of a step
(F10, reproduction `r11_lifetime_expression.py` case (a)).

Now the compiler substitutes each expression variable's expression (recursively) into
the write and rule ASTs that read it, so a write reads the expression evaluated on the
state the write sees. An expression calling a function that needs evaluation-time
context (a history operator, the engine step, positions) is not inlined: a write reads
its stored value, and a `tick`-lifetime one refuses at compile.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledVariable
from townlet.vfs.schema import VariableDef, WriteSpec
from townlet.vfs.vtc import VTCWriteRefusalError, compile_vtc_action_writes, compile_vtc_transition_rules, vtc_write_targets
from townlet.world.expression import ExpressionParser, read_paths

WITNESS = Path(__file__).resolve().parents[4] / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
EARLY_PHASE = "apply_action_effects"
LATE_PHASE = "apply_completion_bonuses"
RULE_PHASE = "apply_social_residue_effects"


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _dump(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _decl(var_id: str, *, scope: str = "agent", type: str = "scalar", lifetime: str = "episode", **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": type,
        "lifetime": lifetime,
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": False if type == "bool" else 0.0,
    }
    declaration.update(extra)
    return declaration


def _write(variable_id: str, expression: str, *, phase: str = LATE_PHASE, condition: str | None = None) -> dict:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": condition,
        "composition": "additive_delta",
        "phase": phase,
        "priority": 0,
        "clamp": None,
        "telemetry_label": f"w_{variable_id}",
    }


def _pack(tmp_path: Path, *, declarations: list[dict], writes: list[dict], rules: list[dict] | None = None, name: str = "pack") -> Path:
    """The witness pack with extra variables, ADVANCE's writes replaced, and optional transition rules."""
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"] += declarations
    _dump(pack / "variables.yaml", variables)
    actions = _yaml(pack / "actions.yaml")
    advance = next(action for action in actions["actions"]["custom_actions"] if action["name"] == "ADVANCE")
    advance["writes"] = writes
    _dump(pack / "actions.yaml", actions)
    if rules is not None:
        _dump(pack / "transition_rules.yaml", {"version": "1.0", "transition_rules": rules})
    return pack


def _compile(pack: Path) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _env(universe: CompiledUniverse, num_agents: int = 1) -> VectorizedHamletEnv:
    env = VectorizedHamletEnv.from_universe(universe, level_name=LEVEL, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def _advance(env: VectorizedHamletEnv) -> None:
    index = next(i for i, action in enumerate(env.action_space.actions) if action.name == "ADVANCE")
    env.step(torch.full((env.num_agents,), index, dtype=torch.long))


def _read(env: VectorizedHamletEnv, name: str) -> list:
    return env.vfs_registry.get(name, reader="engine").tolist()


def _cash_pack(tmp_path: Path, *, rich: str = "cash > 0.5", rules: list[dict] | None = None, name: str = "pack") -> Path:
    """`cash` rises in an early action phase; later writes are gated on expressions over it.

    At reset `cash` is 0, so every stored expression is false: a write that read the
    stored value would miss on the first tick. Only a write that reads the expression
    evaluated on the state it sees (cash = 1 after the early phase) hits.
    """
    return _pack(
        tmp_path,
        name=name,
        declarations=[
            _decl("cash"),
            _decl("rich_t", type="bool", lifetime="tick", expression=rich),
            _decl("rich_e", type="bool", lifetime="episode", expression=rich),
            _decl("cash_x2", lifetime="tick", expression="cash * 2.0"),
            _decl("very_rich", type="bool", expression="cash_x2 > 1.5"),
            _decl("hits_t"),
            _decl("hits_e"),
            _decl("hits_nested"),
            _decl("rule_hits"),
        ],
        writes=[
            _write("cash", "1.0", phase=EARLY_PHASE),
            _write("hits_t", "1.0", condition="rich_t"),
            _write("hits_e", "1.0", condition="vfs.rich_e"),
            _write("hits_nested", "1.0", condition="very_rich"),
        ],
        rules=rules,
    )


def test_r11a_bar_money_condition_sees_rich_on_the_same_tick_for_both_lifetimes(tmp_path: Path) -> None:
    """r11(a) verbatim: `rich: bar.money > 0.1`, money 0.5 throughout; the tick-lifetime write never hit (F10)."""
    pack = _pack(
        tmp_path,
        declarations=[
            _decl("rich", type="bool", lifetime="tick", expression="bar.money > 0.1"),
            _decl("rich_ep", type="bool", lifetime="episode", expression="bar.money > 0.1"),
            _decl("hits_tick_lifetime"),
            _decl("hits_episode_lifetime"),
        ],
        writes=[
            _write("hits_tick_lifetime", "1.0", condition="rich"),
            _write("hits_episode_lifetime", "1.0", condition="rich_ep"),
        ],
    )
    env = _env(_compile(pack))
    for tick in range(1, 4):
        _advance(env)
        assert _read(env, "hits_tick_lifetime") == [float(tick)]
        assert _read(env, "hits_episode_lifetime") == [float(tick)]


def test_condition_reads_the_expression_on_the_state_the_write_sees(tmp_path: Path) -> None:
    """An earlier action phase moves the input; a later write gated on the expression sees it that tick."""
    env = _env(_compile(_cash_pack(tmp_path)))
    assert _read(env, "rich_e") == [False]  # what a stored read would see on tick 1
    _advance(env)
    assert _read(env, "cash") == [1.0]
    assert _read(env, "hits_t") == [1.0]
    assert _read(env, "hits_e") == [1.0]


def test_nested_expression_variables_inline_recursively(tmp_path: Path) -> None:
    """`very_rich` reads `cash_x2` (tick lifetime) reads `cash`: the compiled condition reads only `cash`."""
    universe = _compile(_cash_pack(tmp_path))
    nested = next(w for w in universe.get_level(LEVEL).transition_schedule.action_write_program.writes if w.variable_id == "hits_nested")
    assert nested.condition == "very_rich"  # the authored text is the declaration's identity
    assert nested.condition_ast is not None
    assert read_paths(nested.condition_ast) == frozenset({"cash"})
    env = _env(universe)
    _advance(env)
    assert _read(env, "hits_nested") == [1.0]


def test_transition_rule_reads_an_expression_variable_on_the_same_tick(tmp_path: Path) -> None:
    """A rule after the action phases sees `rich_t` evaluated on the post-action state, not its reset literal."""
    rule = {
        "id": "reward_rich",
        "phase": RULE_PHASE,
        "condition": "rich_t",
        "writes": [
            {
                "variable_id": "rule_hits",
                "expression": "rule_hits + 1.0",
                "composition": "overwrite",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    env = _env(_compile(_cash_pack(tmp_path, rules=[rule])))
    _advance(env)
    assert _read(env, "rule_hits") == [1.0]
    _advance(env)
    assert _read(env, "rule_hits") == [2.0]


def test_inlining_survives_the_cache_round_trip(tmp_path: Path) -> None:
    """The load path rebuilds the schedule from the serialized profiles and inlines the same way."""
    universe = _compile(_cash_pack(tmp_path))
    cache = tmp_path / "universe.msgpack"
    universe.save_to_cache(cache)
    loaded = CompiledUniverse.load_from_cache(cache)
    env = _env(loaded)
    _advance(env)
    assert _read(env, "hits_t") == [1.0]
    assert _read(env, "hits_nested") == [1.0]


def test_changing_the_expression_moves_the_compared_hash(tmp_path: Path) -> None:
    """The write's text is unchanged, so the transition graph hash holds; the expression moves `vfs_hash`.

    The canonical write hashes its authored (pre-substitution) AST, and the expression
    enters `vfs_hash` — the hash checkpoints compare — through the expression schema
    hash (WP10). Together they cover the substituted program.
    """
    before = _compile(_cash_pack(tmp_path, rich="cash > 0.5", name="before")).get_level(LEVEL)
    after = _compile(_cash_pack(tmp_path, rich="cash > 0.7", name="after")).get_level(LEVEL)
    assert before.transition_graph_hash == after.transition_graph_hash
    assert before.vfs_hash != after.vfs_hash


def test_per_world_differential(tmp_path: Path) -> None:
    """Each world's write reads its own world's expression: agent state and a per-world global alike."""
    pack = _pack(
        tmp_path,
        declarations=[
            _decl("cash"),
            _decl("rich", type="bool", lifetime="tick", expression="cash > 0.5"),
            _decl("heat", scope="global"),
            _decl("warm", scope="global", type="bool", lifetime="tick", expression="heat > 0.5"),
            _decl("hits_rich"),
            _decl("hits_warm"),
        ],
        writes=[
            _write("cash", "1.0", phase=EARLY_PHASE),
            _write("hits_rich", "1.0", condition="rich"),
            _write("hits_warm", "1.0", condition="warm"),
        ],
    )
    env = _env(_compile(pack), num_agents=2)
    env.vfs_registry.set("cash", torch.tensor([0.0, -5.0]), writer="engine")
    env.vfs_registry.set("heat", torch.tensor([1.0, 0.0]), writer="engine")
    _advance(env)
    assert _read(env, "hits_rich") == [1.0, 0.0]
    assert _read(env, "hits_warm") == [1.0, 0.0]


# --- Context-bound expressions (history operators, step, positions) are never inlined ---------------

_PARSER = ExpressionParser()


def _variable_def(var_id: str, *, var_type: str = "scalar", lifetime: str = "episode") -> VariableDef:
    return VariableDef(
        id=var_id,
        scope="agent",
        type=var_type,
        lifetime=lifetime,
        readable_by=["engine"],
        writable_by=["engine"],
        default=False if var_type == "bool" else 0.0,
    )


def _compiled(var_id: str, expression: str | None, *, var_type: str = "scalar", lifetime: str = "episode") -> CompiledVariable:
    return CompiledVariable(
        name=var_id,
        type="float" if var_type == "scalar" else var_type,
        exposed_to=(),
        lifetime=lifetime,
        readable_by=("engine",),
        writable_by=("engine",),
        expression=expression,
        ast=None if expression is None else _PARSER.parse(expression),
    )


def _history_targets(lagged_lifetime: str) -> dict:
    """`lagged: lag(bar.energy, 1)` (context-bound) and `dropping: lagged > bar.energy` (pure, reads it)."""
    variables = [
        _variable_def("lagged", lifetime=lagged_lifetime),
        _variable_def("dropping", var_type="bool"),
        _variable_def("state"),
    ]
    profile = CompiledGlobalProfile(
        variables=[
            _compiled("state", None),
            _compiled("lagged", "lag(bar.energy, 1)", lifetime=lagged_lifetime),
            _compiled("dropping", "lagged > bar.energy", var_type="bool"),
        ],
        dependencies={"state": (), "lagged": (), "dropping": ("lagged",)},
    )
    return vtc_write_targets(variables, ["energy"], (None, profile))


class _Action:
    def __init__(self, write: WriteSpec) -> None:
        self.id = 0
        self.name = "ACT"
        self.source_affordance = None
        self.writes = (write,)


def _action_write(condition: str) -> _Action:
    return _Action(WriteSpec(**_write("state", "1.0", condition=condition)))


def test_episode_history_expression_is_read_stored_not_inlined() -> None:
    targets = _history_targets("episode")
    (direct,) = compile_vtc_action_writes([_action_write("lagged > 0.5")], targets).writes
    assert direct.condition_ast is not None
    assert read_paths(direct.condition_ast) == frozenset({"lagged"})
    # A pure expression over it inlines, and keeps the stored read of the history operand.
    (nested,) = compile_vtc_action_writes([_action_write("dropping")], targets).writes
    assert nested.condition_ast is not None
    assert read_paths(nested.condition_ast) == frozenset({"lagged", "bar.energy"})


@pytest.mark.parametrize("condition", ["lagged > 0.5", "dropping"])
def test_tick_history_expression_read_by_a_write_refuses(condition: str) -> None:
    """Tick state resets before the action phases, so a stored read would only see the literal."""
    with pytest.raises(VTCWriteRefusalError) as excinfo:
        compile_vtc_action_writes([_action_write(condition)], _history_targets("tick"))
    (refusal,) = excinfo.value.refusals
    assert refusal.kind == "type"
    assert "tick-lifetime expression variable 'lagged'" in refusal.message
    assert "'lag'" in refusal.message


def test_tick_history_expression_read_by_a_rule_refuses() -> None:
    rule = {
        "id": "r",
        "phase": RULE_PHASE,
        "condition": "dropping",
        "writes": [{"variable_id": "state", "expression": "1.0", "composition": "overwrite", "condition": None}],
    }
    with pytest.raises(VTCWriteRefusalError, match="tick-lifetime expression variable 'lagged'"):
        compile_vtc_transition_rules([rule], _history_targets("tick"))


def test_write_calling_a_history_operator_directly_refuses() -> None:
    """A transition write evaluates without temporal history; it names the quantity as a variable instead."""
    with pytest.raises(VTCWriteRefusalError, match="calls 'lag'"):
        compile_vtc_action_writes([_action_write("lag(bar.energy, 1) > 0.5")], _history_targets("episode"))


def test_tick_lifetime_history_read_refuses_at_compile_with_file_line(tmp_path: Path) -> None:
    """End to end: the profile compiler admits `lag` (WP14); a write reading a tick-lifetime one is located."""
    pack = _pack(
        tmp_path,
        declarations=[_decl("lagged", lifetime="tick", expression="lag(bar.money, 1)"), _decl("hits")],
        writes=[_write("hits", "1.0", condition="lagged > 0.1")],
    )
    with pytest.raises(CompilationError) as excinfo:
        _compile(pack)
    message = str(excinfo.value)
    assert "VTC-WRITE-TYPE" in message and "actions.yaml:" in message
    assert "tick-lifetime expression variable 'lagged'" in message and "'lag'" in message


def test_episode_lifetime_history_read_compiles_and_reads_storage(tmp_path: Path) -> None:
    """The episode-lifetime twin compiles; the write keeps a stored read of `lagged` and runs."""
    pack = _pack(
        tmp_path,
        declarations=[_decl("lagged", lifetime="episode", expression="lag(bar.money, 1)"), _decl("hits")],
        writes=[_write("hits", "1.0", condition="lagged > 0.1")],
    )
    universe = _compile(pack)
    (write,) = universe.get_level(LEVEL).transition_schedule.action_write_program.writes
    assert write.condition_ast is not None
    assert read_paths(write.condition_ast) == frozenset({"lagged"})
    env = _env(universe)
    for _ in range(3):
        _advance(env)
    assert _read(env, "hits")[0] <= 3.0


# --- Reference writes are provably world-local (coordinator item, S1) ------------------------------
#
# `aref <- agent_id * 0` reads state, so the constant check passed it, and it killed the batch
# at runtime ("Engine defect: agent_ref ... names agent 0") in every world but world 0.


def _ref_targets() -> dict:
    variables = [
        _variable_def("buddy", var_type="agent_ref"),
        _variable_def("partner", var_type="agent_ref"),
        _variable_def("held", var_type="item_ref"),
        _variable_def("state"),
    ]
    return vtc_write_targets(variables, ["energy"], ())


def _ref_action(variable_id: str, expression: str) -> _Action:
    return _Action(WriteSpec(**{**_write(variable_id, expression), "composition": "overwrite"}))


@pytest.mark.parametrize(
    "expression",
    ["agent_id * 0", "agent_id + 1", "agent_id - agent_id", "max(agent_id, 0)", "where(state > 0.5, agent_id, 0)"],
)
def test_an_agent_ref_write_that_can_name_another_world_refuses(expression: str) -> None:
    with pytest.raises(VTCWriteRefusalError, match="not provably an entity of the writing world") as excinfo:
        compile_vtc_action_writes([_ref_action("buddy", expression)], _ref_targets())
    assert excinfo.value.refusals[0].kind == "type"


@pytest.mark.parametrize("expression", ["agent_id", "-1", "where(state > 0.5, agent_id, -1)", "if state > 0.5 then -1 else agent_id"])
def test_self_null_and_choices_between_them_are_the_agent_ref_writes(expression: str) -> None:
    compile_vtc_action_writes([_ref_action("buddy", expression)], _ref_targets())


def test_agent_id_is_not_an_item_ref() -> None:
    with pytest.raises(VTCWriteRefusalError, match="item_ref 'held'"):
        compile_vtc_action_writes([_ref_action("held", "agent_id")], _ref_targets())


def test_a_reference_write_refuses_at_compile_with_file_line(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        declarations=[_decl("aref", type="agent_ref", initial_value=-1)],
        writes=[{**_write("aref", "agent_id * 0"), "composition": "overwrite"}],
    )
    with pytest.raises(CompilationError) as excinfo:
        _compile(pack)
    message = str(excinfo.value)
    assert "VTC-WRITE-TYPE" in message and "actions.yaml" in message
    assert "not provably an entity of the writing world" in message
