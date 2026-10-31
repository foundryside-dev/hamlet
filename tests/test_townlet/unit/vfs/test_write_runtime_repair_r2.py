"""Re-review repair R2 (VFS writes and runtime): every write an authored pack can compile, the runtime serves.

Each test reproduces one re-review probe (`rereview/authoring` A1, `rereview/vfs_runtime` N1, N2,
N3, N8) on a real pack, compiles it, and steps it: a compile that accepts what the runtime cannot
serve is the defect class these pin.

- A1: a transition rule on a meter (`variable_id: bar.<m>`) commits through the meter bars, masked
  per world, clamped, and bounded at `clamp_and_validate`; a meter rule after that phase refuses.
- N1: bool and reference item state reach pipelines in their declared dtype.
- N2: a per-row value into a vector/tensor target refuses in action writes and rules alike.
- N3: `clamp` on a bool or reference target refuses at compile.
- N8: an `item_ref` with `lifetime: persistent` refuses at its declaration line.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from townlet.environment.vectorized_env import VectorizedHamletEnv
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.vtc import compile_vtc_interaction_progress, compile_vtc_modulations

CONFIGS = Path(__file__).resolve().parents[4] / "configs"
CURRICULUM = CONFIGS / "default_curriculum"
CURRICULUM_LEVEL = "L1_full_observability"
WITNESS = CONFIGS / "static_epistemic_access"
WITNESS_LEVEL = "L0_simple"
ITEMS = CONFIGS / "test" / "items_smoke"
ITEMS_LEVEL = "L0_smoke"


# -- pack helpers ----------------------------------------------------------------------


def _yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text())


def _dump(path: Path, payload: Any) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _decl(var_id: str, *, scope: str = "agent", type: str = "scalar", lifetime: str = "episode", **extra: Any) -> dict[str, Any]:
    declaration: dict[str, Any] = {
        "id": var_id,
        "scope": scope,
        "type": type,
        "lifetime": lifetime,
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": None if type.endswith("_ref") else 0.0,
    }
    declaration.update(extra)
    return declaration


def _rule(variable_id: str, expression: str, *, composition: str = "additive_delta", **fields: Any) -> dict[str, Any]:
    write = {"variable_id": variable_id, "expression": expression, "composition": composition, "condition": None}
    write.update({"clamp": fields.pop("clamp", None), "effect": None})
    rule = {"id": "r", "phase": fields.pop("phase", "apply_transition_rules"), "condition": fields.pop("condition", None)}
    assert not fields, fields
    rule["writes"] = [write]
    return rule


def _write(variable_id: str, expression: str, *, composition: str = "overwrite", clamp: list[float] | None = None) -> dict[str, Any]:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": None,
        "composition": composition,
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": clamp,
        "telemetry_label": "w",
    }


def _pack(
    tmp_path: Path,
    base: Path,
    *,
    declarations: list[dict[str, Any]] | None = None,
    rules: list[dict[str, Any]] | None = None,
    writes: list[dict[str, Any]] | None = None,
    name: str = "pack",
) -> Path:
    pack = tmp_path / name
    shutil.copytree(base, pack, ignore=shutil.ignore_patterns(".compiled"))
    if declarations:
        variables = _yaml(pack / "variables.yaml")
        variables["variables"]["declarations"] += declarations
        _dump(pack / "variables.yaml", variables)
    if rules is not None:
        _dump(pack / "transition_rules.yaml", {"version": "1.0", "transition_rules": rules})
    if writes is not None:
        actions = _yaml(pack / "actions.yaml")
        advance = next(action for action in actions["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"] = writes
        _dump(pack / "actions.yaml", actions)
    return pack


def _compile(pack: Path, level: str) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _env(universe: CompiledUniverse, level: str, num_agents: int = 2) -> VectorizedHamletEnv:
    env = VectorizedHamletEnv.from_universe(universe, level_name=level, num_agents=num_agents, device="cpu")
    env.reset()
    return env


def _action(env: VectorizedHamletEnv, name: str) -> int:
    return next(index for index, action in enumerate(env.action_space.actions) if action.name == name)


def _step(env: VectorizedHamletEnv, name: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, dict]:
    return env.step(torch.full((env.num_agents,), _action(env, name), dtype=torch.long))


def _meter(env: VectorizedHamletEnv, name: str) -> torch.Tensor:
    return env.meters[:, env.meter_name_to_index[name]].clone()


def _refusal(pack: Path, level: str) -> CompilationError:
    with pytest.raises(CompilationError) as caught:
        _compile(pack, level)
    return caught.value


def _line_of(path: Path, needle: str) -> int:
    for number, text in enumerate(path.read_text().splitlines(), 1):
        if needle in text:
            return number
    raise AssertionError(f"{needle!r} not in {path}")


def _energy_after_one_wait(tmp_path: Path, rules: list[dict[str, Any]] | None, name: str) -> torch.Tensor:
    env = _env(_compile(_pack(tmp_path, CURRICULUM, rules=rules, name=name), CURRICULUM_LEVEL), CURRICULUM_LEVEL)
    _step(env, "WAIT")
    return _meter(env, "energy")


# -- A1: transition rules on meters ------------------------------------------------------


def test_a_rule_on_a_meter_compiles_and_steps_writing_the_meter(tmp_path: Path) -> None:
    baseline = _energy_after_one_wait(tmp_path, None, "baseline")
    drained = _energy_after_one_wait(tmp_path, [_rule("bar.energy", "-0.1")], "drain")
    assert torch.allclose(drained, baseline - 0.1)


def test_a_meter_rule_is_masked_per_world(tmp_path: Path) -> None:
    baseline = _energy_after_one_wait(tmp_path, None, "baseline")
    drained = _energy_after_one_wait(tmp_path, [_rule("bar.energy", "-0.1", condition="agent_id == 0")], "world0")
    assert torch.allclose(drained[0], baseline[0] - 0.1)
    assert torch.equal(drained[1], baseline[1])


def test_a_meter_rule_applies_its_clamp_and_the_meter_bounds(tmp_path: Path) -> None:
    clamped = _energy_after_one_wait(tmp_path, [_rule("bar.energy", "5.0", composition="overwrite", clamp=[0.0, 0.7])], "clamp")
    assert torch.allclose(clamped, torch.full_like(clamped, 0.7))
    # No rule clamp: clamp_and_validate still holds the meter to its declared bounds.
    bounded = _energy_after_one_wait(tmp_path, [_rule("bar.energy", "5.0", composition="overwrite")], "bounds")
    assert torch.equal(bounded, torch.ones_like(bounded))


def test_a_meter_rule_reads_the_meter_it_writes_at_phase_entry(tmp_path: Path) -> None:
    baseline = _energy_after_one_wait(tmp_path, None, "baseline")
    halved = _energy_after_one_wait(tmp_path, [_rule("bar.energy", "0.5", composition="multiplicative_modifier")], "halve")
    assert torch.allclose(halved, baseline * 0.5)


def test_a_rule_zeroing_a_lethal_meter_ends_the_episode_that_tick(tmp_path: Path) -> None:
    """The variable-driven death the review's m13 workaround reached for: a rule, then the terminal check."""
    rules = [_rule("bar.health", "0.0", composition="overwrite", condition="agent_id == 1")]
    env = _env(_compile(_pack(tmp_path, CURRICULUM, rules=rules), CURRICULUM_LEVEL), CURRICULUM_LEVEL)
    _, _, dones, _ = _step(env, "WAIT")
    assert dones.tolist() == [False, True]


def test_a_meter_rule_after_clamp_and_validate_refuses_at_its_line(tmp_path: Path) -> None:
    rules = [_rule("bar.energy", "5.0", composition="overwrite", phase="evaluate_terminal_conditions")]
    pack = _pack(tmp_path, CURRICULUM, rules=rules)
    refusal = _refusal(pack, CURRICULUM_LEVEL)
    (issue,) = refusal.issues
    assert "after 'clamp_and_validate'" in issue.message
    assert issue.location == f"{pack / 'transition_rules.yaml'}:{_line_of(pack / 'transition_rules.yaml', 'id: r')}"


def test_a_variable_rule_at_evaluate_terminal_conditions_still_compiles(tmp_path: Path) -> None:
    """Only meters are bounded at clamp_and_validate; a variable rule may run at any phase."""
    rules = [_rule("g", "1.0", phase="evaluate_terminal_conditions")]
    universe = _compile(_pack(tmp_path, WITNESS, declarations=[_decl("g", scope="global")], rules=rules), WITNESS_LEVEL)
    env = _env(universe, WITNESS_LEVEL)
    _step(env, "WAIT")
    assert env.vfs_registry.get("g", reader="engine").tolist() == [1.0, 1.0]


# -- N1: bool and reference item state ---------------------------------------------------


def _item_decl(var_id: str, type: str, initial_value: Any) -> dict[str, Any]:
    return _decl(var_id, scope="item", type=type, profile="food", initial_value=initial_value)


def _items_pack(tmp_path: Path, on_use: list[dict[str, Any]]) -> Path:
    pack = tmp_path / "items"
    shutil.copytree(ITEMS, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"] += [
        _item_decl("flag", "bool", False),
        _item_decl("owner", "agent_ref", None),
        _decl("nullref", type="agent_ref"),
    ]
    _dump(pack / "variables.yaml", variables)
    items = _yaml(pack / "items.yaml")
    apple = next(item for item in items["items"]["item_types"] if item["id"] == "apple")
    apple["interactions"]["on_use"] = on_use
    _dump(pack / "items.yaml", items)
    return pack


def _pick_up_and_use_apple(universe: CompiledUniverse, uses: int) -> list[float]:
    env = _env(universe, ITEMS_LEVEL)
    apple = next(item for item in env.item_manager.items_in_world(0) if item.item_type == "apple")
    env.positions[0] = torch.as_tensor(apple.position, dtype=env.positions.dtype)
    names = [action.name for action in env.action_space.actions]
    get = next(name for name in names if name.startswith("GET"))
    use = next(name for name in names if name.startswith("USE"))
    actions = torch.full((env.num_agents,), _action(env, "WAIT"), dtype=torch.long)
    actions[0] = _action(env, get)
    env.step(actions)
    flags = []
    for _ in range(uses):
        actions = torch.full((env.num_agents,), _action(env, "WAIT"), dtype=torch.long)
        actions[0] = _action(env, use)
        env.step(actions)
        flags.append(env.vfs_registry.read_item("food", "flag", apple.vfs_index, reader="engine"))
    return flags


@pytest.mark.parametrize(
    "condition",
    ["not item.flag", "not item.flag and item.owner == nullref"],
    ids=["not", "and-with-ref"],
)
def test_bool_and_reference_item_state_are_read_in_their_declared_dtype(tmp_path: Path, condition: str) -> None:
    on_use = [{"if": condition, "then": [{"modify": "item.flag", "value": "not item.flag"}], "else": []}]
    universe = _compile(_items_pack(tmp_path, on_use), ITEMS_LEVEL)
    # First use: the flag is false, so the toggle sets it; second use: the guard is false.
    assert _pick_up_and_use_apple(universe, 2) == [1.0, 1.0]


# -- N2: one shape policy for vector/tensor targets --------------------------------------


_VECTORS = [
    _decl("vec", type="vecNf", dims=3, initial_value=[0.0, 0.0, 0.0]),
    _decl("av", initial_value=2.0),
    _decl("g", scope="global", initial_value=3.0),
    _decl("two", scope="global", initial_value=0.0, expression="2.0"),
]


@pytest.mark.parametrize("expression", ["av", "bar.energy", "g", "agent_id * 1.0"])
@pytest.mark.parametrize("program", ["action", "rule"])
def test_a_per_row_value_into_a_vector_target_refuses_in_both_programs(tmp_path: Path, program: str, expression: str) -> None:
    if program == "action":
        pack = _pack(tmp_path, WITNESS, declarations=_VECTORS, writes=[_write("vec", expression)])
        # An action write is located at its action's entry.
        path, needle = pack / "actions.yaml", "name: ADVANCE"
    else:
        pack = _pack(tmp_path, WITNESS, declarations=_VECTORS, rules=[_rule("vec", expression, composition="overwrite")])
        path, needle = pack / "transition_rules.yaml", "id: r"
    refusal = _refusal(pack, WITNESS_LEVEL)
    (issue,) = refusal.issues
    assert issue.code == "VTC-WRITE-TYPE"
    assert "into vecNf 'vec'" in issue.message and "takes a constant" in issue.message
    assert issue.location == f"{path}:{_line_of(path, needle)}"


@pytest.mark.parametrize(("expression", "value"), [("1.0", 1.0), ("two", 2.0)], ids=["literal", "constant-expression"])
@pytest.mark.parametrize("program", ["action", "rule"])
def test_a_constant_fills_a_vector_target_in_both_programs(tmp_path: Path, program: str, expression: str, value: float) -> None:
    if program == "action":
        pack, action = _pack(tmp_path, WITNESS, declarations=_VECTORS, writes=[_write("vec", expression)]), "ADVANCE"
    else:
        pack, action = _pack(tmp_path, WITNESS, declarations=_VECTORS, rules=[_rule("vec", expression, composition="overwrite")]), "WAIT"
    env = _env(_compile(pack, WITNESS_LEVEL), WITNESS_LEVEL, num_agents=3)
    _step(env, action)
    assert env.vfs_registry.get("vec", reader="engine").tolist() == [[value] * 3] * 3


# -- N3: clamp on a bool or reference target ---------------------------------------------

_FLAGS = [_decl("flag", type="bool", initial_value=False), _decl("aref", type="agent_ref")]


@pytest.mark.parametrize(
    ("target", "expression", "type_word"),
    [("flag", "true", "bool"), ("aref", "-1", "agent_ref"), ("aref", "agent_id", "agent_ref")],
)
@pytest.mark.parametrize("program", ["action", "rule"])
def test_clamp_on_a_bool_or_reference_target_refuses_at_compile(
    tmp_path: Path, program: str, target: str, expression: str, type_word: str
) -> None:
    if program == "action":
        pack = _pack(tmp_path, WITNESS, declarations=_FLAGS, writes=[_write(target, expression, clamp=[0.0, 10.0])])
        path, needle = pack / "actions.yaml", "name: ADVANCE"
    else:
        rule = _rule(target, expression, composition="overwrite", clamp=[0.0, 0.5])
        pack = _pack(tmp_path, WITNESS, declarations=_FLAGS, rules=[rule])
        path, needle = pack / "transition_rules.yaml", "id: r"
    refusal = _refusal(pack, WITNESS_LEVEL)
    (issue,) = refusal.issues
    assert issue.code == "VTC-WRITE-TYPE"
    assert f"clamps {type_word} '{target}'" in issue.message and "clamp: null" in issue.message
    assert issue.location == f"{path}:{_line_of(path, needle)}"


def test_the_same_writes_without_clamp_compile_and_step(tmp_path: Path) -> None:
    writes = [_write("flag", "true"), _write("aref", "agent_id")]
    env = _env(_compile(_pack(tmp_path, WITNESS, declarations=_FLAGS, writes=writes), WITNESS_LEVEL), WITNESS_LEVEL, num_agents=3)
    _step(env, "ADVANCE")
    assert env.vfs_registry.get("flag", reader="engine").tolist() == [True, True, True]
    assert env.vfs_registry.get("aref", reader="engine").tolist() == [0, 1, 2]


# -- N8: a persistent item_ref -----------------------------------------------------------


def test_a_persistent_item_ref_refuses_at_its_declaration_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, WITNESS, declarations=[_decl("held", type="item_ref", lifetime="persistent")])
    refusal = _refusal(pack, WITNESS_LEVEL)
    (issue,) = refusal.issues
    assert "item_ref with lifetime persistent" in issue.message and "lifetime: episode" in issue.message
    assert issue.location == f"{pack / 'variables.yaml'}:{_line_of(pack / 'variables.yaml', 'id: held')}"


def test_a_persistent_agent_ref_compiles_and_survives_reset(tmp_path: Path) -> None:
    """An agent row is its world under S1 and is never repopulated, so a persistent agent_ref stays valid."""
    declarations = [_decl("who", type="agent_ref", lifetime="persistent")]
    pack = _pack(tmp_path, WITNESS, declarations=declarations, writes=[_write("who", "agent_id")])
    env = _env(_compile(pack, WITNESS_LEVEL), WITNESS_LEVEL)
    _step(env, "ADVANCE")
    env.reset()
    assert env.vfs_registry.get("who", reader="engine").tolist() == [0, 1]


# -- A6: vocabulary refusals name the vocabulary -----------------------------------------


def test_an_unknown_modulation_type_names_the_admitted_one() -> None:
    modulation = {"bar": "energy", "affordances": ["SLEEP"], "type": "quadratic", "threshold": 0.5, "min_multiplier": 0.2}
    with pytest.raises(ValueError, match="Declare type: linear_multiplier"):
        compile_vtc_modulations([modulation])


@pytest.mark.parametrize(("duration", "needle"), [(None, "Declare duration_ticks"), (0, "must be a positive integer")])
def test_a_progress_interaction_without_a_duration_names_the_fix(duration: int | None, needle: str) -> None:
    affordance = {"name": "SLEEP", "interaction_type": "multi_tick", "duration_ticks": duration}
    with pytest.raises(ValueError, match=needle) as caught:
        compile_vtc_interaction_progress([affordance])
    assert "instant" in str(caught.value)
