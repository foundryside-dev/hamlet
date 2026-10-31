"""Position and vector functions reach VFS state (re-review `authoring` A3).

The profile shape proof derives a call's row shape from the registry
(`FunctionSpec.shape`), not from a hand list: a position function is one row per agent,
a vector function joins its arguments' axes and the type checker proves the payload. So
"distance to the nearest food" is an observed feature, live from the first observation
(`reset()` lays out affordances and positions before the instant-0 evaluation), and a
declared `vec2f` is consumed by `distance`, `within_radius`, `gather`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch
import yaml

from townlet.determinism import seed_all
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

REPO = Path(__file__).resolve().parents[4]
WITNESS = REPO / "configs" / "static_epistemic_access"
LEVEL = "L0_simple"
N = 3
DIST = {"kind": "minmax", "min": 0.0, "max": 16.0, "clip": True}


def _decl(var_id: str, *, scope: str = "agent", type_: str = "scalar", **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": type_,
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": False if type_ == "bool" else 0.0,
    }
    declaration.update(extra)
    return declaration


def _rule(rule_id: str, variable_id: str, expression: str) -> dict:
    return {
        "id": rule_id,
        "phase": "apply_transition_rules",
        "condition": None,
        "writes": [
            {
                "variable_id": variable_id,
                "expression": expression,
                "composition": "overwrite",
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


def _manhattan(env, name: str) -> torch.Tensor:
    target = env.affordances[name].to(dtype=torch.float32)
    return (env.positions.to(dtype=torch.float32) - target.unsqueeze(0)).abs().sum(dim=-1)


def _variable_rows(env, observation: torch.Tensor) -> tuple[torch.Tensor, int, list[str]]:
    """The `variable_element` token rows of `observation`, the value lane, and the slot order."""
    layout = env.token_spec.compact_layout().get_type("variable_element")
    assert layout is not None
    rows = observation[:, layout.start : layout.start + layout.capacity * layout.compact_row_width].reshape(
        env.num_agents, layout.capacity, layout.compact_row_width
    )
    slots = [binding.filler_ref for binding in env.token_spec.get_type("variable_element").slot_bindings]
    return rows, layout.dynamic_features.index("value_0"), slots


# --- distance to an affordance is an observed feature, from the first observation -------------


@pytest.fixture(scope="module")
def spatial_universe(tmp_path_factory: pytest.TempPathFactory):
    declarations = [
        _decl("food_dist", expression='distance_to_affordance("SLEEP")', exposed_to=["agent"], normalization=DIST),
        _decl("near_food", type_="bool", expression='in_range("SLEEP", 2.0)'),
        _decl("nearest_care", expression='min(distance_to_affordance("SLEEP"), distance_to_affordance("DOCTOR"))'),
        _decl("euclid", expression='distance_to_affordance("SLEEP", "euclidean")'),
    ]
    return _compile(_pack(tmp_path_factory.mktemp("spatial"), declarations))


def test_the_first_observation_after_reset_carries_the_distance_to_food(spatial_universe) -> None:
    seed_all(3)
    env = spatial_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    observation = env.reset()
    expected = _manhattan(env, "SLEEP")
    assert torch.equal(_reg(env, "food_dist"), expected)
    assert torch.equal(_reg(env, "near_food"), expected <= 2.0)
    assert torch.equal(_reg(env, "nearest_care"), torch.minimum(expected, _manhattan(env, "DOCTOR")))
    diff = env.positions.to(dtype=torch.float32) - env.affordances["SLEEP"].to(dtype=torch.float32).unsqueeze(0)
    assert torch.allclose(_reg(env, "euclid"), diff.pow(2).sum(dim=-1).sqrt())
    rows, value_lane, slots = _variable_rows(env, observation)
    slot = slots.index("food_dist")
    assert torch.all(rows[:, slot, 0] == 1)
    assert torch.allclose(rows[:, slot, value_lane], expected / 16.0)


def test_moving_the_agent_changes_the_observed_distance(spatial_universe) -> None:
    seed_all(3)
    env = spatial_universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    movement = [index for index, action in enumerate(env.action_space.actions) if action.name not in {"WAIT", "ADVANCE", "INTERACT"}]
    moved = False
    for step in range(6):
        before = env.positions.clone()
        observation, _, _, _ = env.step(torch.full((N,), movement[step % len(movement)], dtype=torch.long))
        expected = _manhattan(env, "SLEEP")
        assert torch.equal(_reg(env, "food_dist"), expected), step
        rows, value_lane, slots = _variable_rows(env, observation)
        assert torch.allclose(rows[:, slots.index("food_dist"), value_lane], expected / 16.0), step
        moved = moved or not torch.equal(before, env.positions)
    assert moved


# --- vector variables are consumed by vector functions ---------------------------------------


def test_vector_functions_read_declared_vectors_in_expressions_rules_and_writes(tmp_path: Path) -> None:
    declarations = [
        _decl("a", type_="vec2f", initial_value=[1.0, 2.0]),
        _decl("b", type_="vec2f", initial_value=[4.0, 6.0]),
        _decl("apart", expression="distance(a, b)"),
        _decl("close", type_="bool", expression="within_radius(a, b, 10.0)"),
        _decl("second", expression="gather(a, 1)"),
        _decl("far_global", scope="global"),
        _decl("far_agent"),
    ]
    advance = [
        {
            "variable_id": "far_agent",
            "expression": 'distance(a, b, "manhattan")',
            "condition": None,
            "composition": "overwrite",
            "phase": "apply_completion_bonuses",
            "priority": 0,
            "clamp": None,
            "telemetry_label": "advance_far",
        }
    ]
    universe = _compile(_pack(tmp_path, declarations, advance_writes=advance))
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    assert torch.equal(_reg(env, "apart"), torch.full((N,), 5.0))  # euclidean by default
    assert torch.equal(_reg(env, "close"), torch.ones(N, dtype=torch.bool))
    assert torch.equal(_reg(env, "second"), torch.full((N,), 2.0))
    env.step(torch.full((N,), _action(env, "ADVANCE"), dtype=torch.long))
    assert torch.equal(_reg(env, "far_agent"), torch.full((N,), 7.0))


def test_a_vector_valued_expression_on_a_scalar_variable_names_the_vector_route(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, [_decl("a", type_="vec2f", initial_value=[1.0, 2.0]), _decl("unit", expression="normalize(a)")]))
    assert "declared as scalar but expression returns vec2f" in message


def test_a_vector_variable_may_not_carry_an_expression(tmp_path: Path) -> None:
    message = _refusal(
        _pack(
            tmp_path,
            [
                _decl("a", type_="vec2f", initial_value=[1.0, 2.0]),
                _decl("twice", type_="vec2f", initial_value=[0.0, 0.0], expression="normalize(a)"),
            ],
        )
    )
    assert "an expression variable is scalar or bool" in message
    assert "distance, within_radius, gather" in message


# --- the shape rule: what each scope admits, said with the fix ----------------------------------


def test_a_position_function_in_a_global_expression_refuses_and_names_scope_agent(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, [_decl("food", scope="global", expression='distance_to_affordance("SLEEP")')]))
    assert "Variable 'food' is global-scope but its expression" in message
    assert "agent-shaped" in message
    assert "scope: agent" in message


def test_an_agent_expression_over_world_state_only_refuses_and_names_scope_global(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, [_decl("night", type_="bool", expression="time_in_window(tick, 2, 6)")]))
    assert "Variable 'night' is agent-scope but its expression" in message
    assert "scope: global" in message


def test_a_stacked_function_joins_a_literal_with_a_per_agent_argument(tmp_path: Path) -> None:
    """`mean(bar.energy, 0.5)` is each agent's mean; the runtime broadcasts, so the proof joins."""
    universe = _compile(_pack(tmp_path, [_decl("half", expression="mean(bar.energy, 0.5)")]))
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    assert torch.allclose(_reg(env, "half"), (env.meters[:, env.meter_name_to_index["energy"]] + 0.5) / 2.0)


def test_a_position_function_in_a_rule_refuses_at_the_rule_and_names_the_expression_variable_route(tmp_path: Path) -> None:
    message = _refusal(_pack(tmp_path, [_decl("food")], rules=[_rule("food_rule", "food", 'distance_to_affordance("SLEEP")')]))
    assert "transition_rules.yaml" in message
    assert "'distance_to_affordance', which needs agent and affordance positions on the context" in message
    assert "a transition write or rule does not carry" in message
    assert "Declare the quantity as a global or agent expression variable and read it by name" in message


def test_a_rule_reads_a_position_expression_variable_by_its_stored_value(tmp_path: Path) -> None:
    """A position expression is stored (its context is the evaluator's), so the rule sees the distance the observation showed."""
    universe = _compile(
        _pack(
            tmp_path,
            [_decl("food_dist", expression='distance_to_affordance("SLEEP")'), _decl("seen")],
            rules=[_rule("copy", "seen", "food_dist")],
        )
    )
    seed_all(3)
    env = universe.create_environment(num_agents=N, level_name=LEVEL, device="cpu")
    env.reset()
    shown = _reg(env, "food_dist").clone()
    env.step(torch.full((N,), _action(env, "WAIT"), dtype=torch.long))
    assert torch.equal(_reg(env, "seen"), shown)
