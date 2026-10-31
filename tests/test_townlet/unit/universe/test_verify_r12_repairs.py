"""Repairs for the adversarial verification of 39825727 (`verify_R12/RESULTS.md`).

Each case edits a scratch copy of a shipped pack and compiles it with the public compiler.
A refusal carries its registry code and a `file:line` inside the pack; a positive case
compiles AND steps an environment, and reads the value the authoring promised.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError

CONFIGS = Path(__file__).parents[4] / "configs"
SEA = ("static_epistemic_access", "L0_simple")


def _pack(tmp_path: Path, source: str) -> Path:
    dest = tmp_path / Path(source).name
    shutil.copytree(CONFIGS / source, dest, ignore=shutil.ignore_patterns(".compiled"))
    return dest


def _edit(pack: Path, file: str, old: str, new: str) -> None:
    path = pack / file
    text = path.read_text()
    assert old in text, f"{file} no longer contains {old!r}; re-derive the edit"
    path.write_text(text.replace(old, new, 1))


def _compile(pack: Path, level: str):
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _env(universe, level: str, num_agents: int = 2):
    env = universe.create_environment(num_agents=num_agents, level_name=level, device="cpu")
    env.reset()
    return env


def _step(env, steps: int = 4) -> None:
    generator = torch.Generator().manual_seed(0)
    for _ in range(steps):
        env.step(torch.randint(0, env.action_dim, (env.num_agents,), generator=generator))


def _refused(pack: Path, level: str, code: ErrorCode, located_in: str) -> CompilationError:
    with pytest.raises(CompilationError) as caught:
        _compile(pack, level)
    issues = [issue for issue in caught.value.issues if issue.code == code]
    assert issues, f"expected {code}; got {caught.value}"
    location = issues[0].location
    assert location is not None and located_in in location, f"{code} located at {location!r}, not in {located_in!r}"
    path, _, line = location.rpartition(":")
    assert Path(path).is_relative_to(pack) and int(line) > 0, location
    return caught.value


def _located_line(pack: Path, error: CompilationError, code: ErrorCode) -> str:
    location = next(issue.location for issue in error.issues if issue.code == code)
    assert location is not None
    path, _, line = location.rpartition(":")
    return Path(path).read_text().splitlines()[int(line) - 1].strip()


def _agent_variable(identifier: str, kind: str, initial: object, expression: str | None = None) -> str:
    text = (
        f"  - id: {identifier}\n    scope: agent\n    type: {kind}\n    lifetime: episode\n    semantic_type: custom\n"
        f"    readable_by: [engine]\n    writable_by: [engine]\n    exposed_to: []\n    initial_value: {initial}\n"
    )
    if expression is not None:
        text += f"    expression: {expression}\n"
    return text


def _declare(pack: Path, *declarations: str) -> None:
    _edit(pack, "variables.yaml", "  - id: hidden_score", "".join(declarations) + "  - id: hidden_score")


# --- D1: keyword prefixes are identifiers, never a keyword plus a remainder ------------


KEYWORD_PREFIXED = ["notable", "nothing", "true_count", "falsey", "iffy", "orbit", "order", "android", "thenx", "elsewhere"]


def test_d1_keyword_prefixed_ids_declare_and_read_their_own_value(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    declarations = [_agent_variable(name, "scalar", float(index + 1)) for index, name in enumerate(KEYWORD_PREFIXED)]
    # Each reader adds 100 to one keyword-prefixed id: the value proves which variable was read.
    readers = [_agent_variable(f"read_{name}", "scalar", 0.0, f"{name} + 100.0") for name in KEYWORD_PREFIXED]
    # `nothing` beside `hing`: once read as `not hing`.
    _declare(pack, *declarations, *readers, _agent_variable("hing", "scalar", -5.0))
    universe = _compile(pack, SEA[1])
    env = _env(universe, SEA[1])
    _step(env)
    registry = env.vfs_registry
    for index, name in enumerate(KEYWORD_PREFIXED):
        expected = float(index + 1) + 100.0
        assert registry.get(f"read_{name}", reader="engine").tolist() == [expected, expected], name


def test_d1_notable_beside_able_reads_notable_not_not_able(tmp_path: Path) -> None:
    """The silent misread: with both declared, `notable` once parsed as `not able`."""
    pack = _pack(tmp_path, SEA[0])
    _declare(
        pack,
        _agent_variable("able", "bool", "true"),
        _agent_variable("notable", "bool", "true"),
        _agent_variable("pick", "scalar", 0.0, "if notable then 7.0 else 3.0"),
        _agent_variable("mix", "bool", "true", "notable and not able"),
        _agent_variable("mix_or", "bool", "false", "able or not notable"),
    )
    universe = _compile(pack, SEA[1])
    env = _env(universe, SEA[1])
    _step(env)
    registry = env.vfs_registry
    assert registry.get("pick", reader="engine").tolist() == [7.0, 7.0]
    assert registry.get("mix", reader="engine").tolist() == [False, False]
    assert registry.get("mix_or", reader="engine").tolist() == [True, True]


def test_d1_every_keyword_token_is_whole_word() -> None:
    from townlet.world.expression import ExpressionParser
    from townlet.world.expression.ast_nodes import BinaryOp, IfThenElse, UnaryOp, Variable

    parser = ExpressionParser()
    for name in KEYWORD_PREFIXED + ["not_x", "and_x", "if_open", "false_alarm", "truex"]:
        assert parser.parse(name) == Variable(name=name), name
    assert isinstance(parser.parse("not able"), UnaryOp)
    assert isinstance(parser.parse("notable and not able"), BinaryOp)
    assert isinstance(parser.parse("if iffy then thenx else elsewhere"), IfThenElse)
    # A keyword glued to an operand is not an infix operator either.
    for text in ("a orbit", "a android", "x notable"):
        with pytest.raises(Exception):
            parser.parse(text)


# --- D2: random placement is per world and never reads a declared position --------------


def test_d2_static_epistemic_access_runs_at_61_worlds(tmp_path: Path) -> None:
    """61 worlds used to exceed the one-grid head count and crash on a missing declared position."""
    pack = _pack(tmp_path, SEA[0])
    universe = _compile(pack, SEA[1])
    env = _env(universe, SEA[1], num_agents=61)
    assert env.randomize_affordances
    _step(env)
    env.reset()
    affordance_cells = {tuple(position.tolist()) for position in env.affordances.values()}
    assert len(affordance_cells) == len(env.affordances)
    assert not affordance_cells & {tuple(row) for row in env.positions.tolist()}


def test_d2_off_grid_declared_position_is_never_used_under_randomize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from townlet.environment.vectorized_env import VectorizedHamletEnv

    level = "L1_full_observability"
    pack = _pack(tmp_path, "default_curriculum")
    _edit(pack, f"levels/{level}/affordances.yaml", "      - - 2\n        - 2", "      - - 99\n        - 2")
    universe = _compile(pack, level)

    def _refuse_declared(self: VectorizedHamletEnv) -> None:
        raise AssertionError("randomize_affordances: true read a declared position")

    monkeypatch.setattr(VectorizedHamletEnv, "_apply_configured_affordance_positions", _refuse_declared)
    # 51 worlds tripped the old fallback onto declared positions; under S1 placement is per world.
    env = _env(universe, level, num_agents=51)
    for _ in range(3):
        _step(env, steps=2)
        env.reset()
        for name, position in env.affordances.items():
            assert 0 <= int(position[0]) < 8 and 0 <= int(position[1]) < 8, (name, position.tolist())


def test_d2_substrate_too_small_for_one_world_refuses_at_compile(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    stratum = (pack / "stratum.yaml").read_text()
    width = next(line for line in stratum.splitlines() if line.strip().startswith("width:"))
    height = next(line for line in stratum.splitlines() if line.strip().startswith("height:"))
    _edit(pack, "stratum.yaml", width, width.split(":")[0] + ": 1")
    _edit(pack, "stratum.yaml", height, height.split(":")[0] + ": 1")
    error = _refused(pack, SEA[1], ErrorCode.GRID_CAPACITY_EXCEEDED, "training.yaml")
    assert "plus one agent per world" in str(error)
    assert _located_line(pack, error, ErrorCode.GRID_CAPACITY_EXCEEDED).startswith("randomize_affordances:")


def test_d2_capacity_is_per_world_not_per_population(tmp_path: Path) -> None:
    """A population far larger than the grid compiles: worlds do not share cells."""
    pack = _pack(tmp_path, SEA[0])
    _edit(pack, f"levels/{SEA[1]}/training.yaml", "    size: 1\n", "    size: 4096\n")
    _compile(pack, SEA[1])


# --- D3: a write to a meter is held to the meter's bounds when its phase commits --------


L1 = "L1_full_observability"


def _write(variable_id: str, expression: str, composition: str = "additive_delta", clamp: list[float] | None = None) -> dict:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "composition": composition,
        "condition": None,
        "clamp": clamp,
        "effect": None,
    }


def _rules_pack(tmp_path: Path, rules: list[dict], name: str) -> Path:
    import yaml

    pack = tmp_path / name
    shutil.copytree(CONFIGS / "default_curriculum", pack, ignore=shutil.ignore_patterns(".compiled"))
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": rules}, sort_keys=False))
    return pack


def _meters_after_one_wait(pack: Path) -> dict[str, float]:
    universe = _compile(pack, L1)
    env = _env(universe, L1, num_agents=1)
    wait = next(index for index, action in enumerate(env.action_space.actions) if action.name == "WAIT")
    before = {name: float(env.meters[0, index]) for name, index in env.meter_name_to_index.items()}
    env.step(torch.tensor([wait]))
    return {name: float(env.meters[0, index]) - before[name] for name, index in env.meter_name_to_index.items()}


@pytest.mark.parametrize("phase", ["apply_passive_depletion", "apply_threshold_cascades", "ingest_actions"])
def test_d3_meter_rule_overshoot_does_not_drive_the_cascades(tmp_path: Path, phase: str) -> None:
    """`bar.satiation += -5` before the cascades: the cascades read the clamped 0.0, not -4.x."""
    unclamped = [{"id": "drain", "phase": phase, "condition": None, "writes": [_write("bar.satiation", "-5.0")]}]
    clamped = [{"id": "drain", "phase": phase, "condition": None, "writes": [_write("bar.satiation", "-5.0", clamp=[0.0, 1.0])]}]
    delta_unclamped = _meters_after_one_wait(_rules_pack(tmp_path, unclamped, "unclamped"))
    delta_clamped = _meters_after_one_wait(_rules_pack(tmp_path, clamped, "clamped"))
    assert delta_unclamped == pytest.approx(delta_clamped, abs=1e-7)
    assert delta_clamped["health"] < 0.0  # the starving cascade still fires, at its in-bounds magnitude


def test_d3_a_later_rule_reads_the_clamped_meter(tmp_path: Path) -> None:
    """m_oob2: a rule at the cascade phase overshoots; a later rule reading the meter sees 0.0."""

    def rules(clamp: list[float] | None) -> list[dict]:
        return [
            {
                "id": "drain",
                "phase": "apply_threshold_cascades",
                "condition": None,
                "writes": [_write("bar.satiation", "-5.0", clamp=clamp)],
            },
            {
                "id": "mood_from_satiation",
                "phase": "apply_transition_rules",
                "condition": None,
                "writes": [_write("bar.mood", "bar.satiation * 0.01")],
            },
        ]

    delta_unclamped = _meters_after_one_wait(_rules_pack(tmp_path, rules(None), "unclamped"))
    delta_clamped = _meters_after_one_wait(_rules_pack(tmp_path, rules([0.0, 1.0]), "clamped"))
    assert delta_unclamped["mood"] == pytest.approx(delta_clamped["mood"], abs=1e-7)


def test_d3_action_write_on_a_meter_is_clamped_before_a_same_phase_rule_reads_it(tmp_path: Path) -> None:
    import yaml

    rules = [
        {
            "id": "observe",
            "phase": "apply_action_effects",
            "condition": None,
            "writes": [_write("seen_satiation", "bar.satiation", composition="overwrite")],
        }
    ]
    pack = _rules_pack(tmp_path, rules, "action_write")
    variables = yaml.safe_load((pack / "variables.yaml").read_text())
    variables["variables"]["declarations"].append(
        {
            "id": "seen_satiation",
            "scope": "agent",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": 9.0,
        }
    )
    (pack / "variables.yaml").write_text(yaml.safe_dump(variables, sort_keys=False))
    actions = yaml.safe_load((pack / "actions.yaml").read_text())
    actions["actions"]["custom_actions"].append(
        {
            "name": "DRAIN",
            "description": "overshoot satiation",
            "enabled_by_default": True,
            "writes": [
                {
                    "variable_id": "bar.satiation",
                    "expression": "-5.0",
                    "condition": None,
                    "composition": "additive_delta",
                    "phase": "apply_action_effects",
                    "priority": 0,
                    "clamp": None,
                    "telemetry_label": "drain",
                }
            ],
        }
    )
    (pack / "actions.yaml").write_text(yaml.safe_dump(actions, sort_keys=False))
    universe = _compile(pack, L1)
    env = _env(universe, L1, num_agents=2)
    drain = next(index for index, action in enumerate(env.action_space.actions) if action.name == "DRAIN")
    env.step(torch.tensor([drain, drain]))
    # Within one phase action writes commit before rules, so the rule reads the action's
    # result, and that result is already held to satiation's declared bounds [0, 1].
    assert env.vfs_registry.get("seen_satiation", reader="engine").tolist() == [0.0, 0.0]
    assert env.meters[:, env.meter_name_to_index["satiation"]].tolist() == [0.0, 0.0]


# --- D4 + P3(a): substrate constructor rules refuse at parse, located ------------------


CONTINUOUS = ("test/action_space/continuous1d", "L0")
GRIDND = ("test/gridnd_4d_pack", "L0_test")


def test_d4_interaction_radius_wider_than_the_bounds_refuses_at_its_key(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "interaction_radius: 1.0", "interaction_radius: 20.0")
    error = _refused(pack, CONTINUOUS[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert "too small for affordance interaction" in str(error)
    assert _located_line(pack, error, ErrorCode.LOAD_ERROR).startswith("interaction_radius:")


def test_d4_continuousnd_interaction_radius_refuses_at_parse(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "type: continuous\n", "type: continuousnd\n")
    _edit(pack, "stratum.yaml", "dimensions: 1", "dimensions: 4")
    _edit(pack, "stratum.yaml", "- [0.0, 10.0]", "- [0.0, 10.0]\n        - [0.0, 10.0]\n        - [0.0, 0.5]\n        - [0.0, 10.0]")
    error = _refused(pack, CONTINUOUS[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert "span of bounds[2]" in str(error)


def test_d4_positive_control_radius_equal_to_the_span_compiles_and_steps(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "interaction_radius: 1.0", "interaction_radius: 10.0")
    env = _env(_compile(pack, CONTINUOUS[1]), CONTINUOUS[1])
    _step(env)


@pytest.mark.parametrize("rank", [9, 13, 100])
def test_p3a_gridnd_rank_above_max_position_rank_refuses_at_the_declaration(tmp_path: Path, rank: int) -> None:
    from townlet.config.stratum_config import MAX_POSITION_RANK

    pack = _pack(tmp_path, GRIDND[0])
    _edit(pack, "stratum.yaml", "dimension_sizes: [5, 5, 5, 5]", f"dimension_sizes: {[2] * rank}")
    error = _refused(pack, GRIDND[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert f"a gridnd substrate has 4 to {MAX_POSITION_RANK}" in str(error)
    assert not any(issue.code == ErrorCode.TOKEN_SPEC for issue in error.issues)


def test_p3a_the_dto_bound_is_the_token_specs_constant() -> None:
    from townlet.config import stratum_config
    from townlet.universe.dto import token_spec

    assert token_spec.MAX_POSITION_RANK is stratum_config.MAX_POSITION_RANK
    assert stratum_config.ContinuousConfig.model_fields["dimensions"].metadata[-1].le == stratum_config.MAX_POSITION_RANK


def test_p3a_gridnd_at_max_position_rank_compiles(tmp_path: Path) -> None:
    pack = _pack(tmp_path, GRIDND[0])
    import yaml

    _edit(pack, "stratum.yaml", "dimension_sizes: [5, 5, 5, 5]", "dimension_sizes: [2, 2, 2, 2, 2, 2, 2, 2]")
    affordances = pack / f"levels/{GRIDND[1]}/affordances.yaml"
    document = yaml.safe_load(affordances.read_text())
    for affordance in document["affordances"]["affordances"]:
        affordance["deployment"]["positions"] = [list(position) + [0, 0, 0, 0] for position in affordance["deployment"]["positions"]]
    affordances.write_text(yaml.safe_dump(document, sort_keys=False))
    universe = _compile(pack, GRIDND[1])
    assert universe.get_level(GRIDND[1]).token_type_schema_hash.startswith("de093a6e9f59924e")


# --- R3 follow-up: a position function on an aspatial substrate refuses at compile ------


ASPATIAL = ("test/action_space/aspatial", "L0")
_ASPATIAL_VARIABLE = (
    "  - id: near_bed\n    scope: agent\n    type: {kind}\n    lifetime: episode\n    semantic_type: custom\n"
    "    readable_by: [engine]\n    writable_by: [engine]\n    exposed_to: []\n    initial_value: {initial}\n"
    "    expression: '{expression}'\n"
)


@pytest.mark.parametrize(
    ("kind", "initial", "expression"),
    [
        ("scalar", 0.0, 'distance_to_affordance("Bed")'),
        ("bool", "false", 'in_range("Bed", 1.0)'),
        ("scalar", 0.0, 'bar.energy + distance_to_affordance("Bed", "euclidean")'),
    ],
)
def test_aspatial_position_function_in_a_variable_refuses_at_its_expression(
    tmp_path: Path, kind: str, initial: object, expression: str
) -> None:
    pack = _pack(tmp_path, ASPATIAL[0])
    declaration = _ASPATIAL_VARIABLE.format(kind=kind, initial=initial, expression=expression.replace("'", "''"))
    _edit(pack, "variables.yaml", "  declarations: []", "  declarations:\n" + declaration)
    error = _refused(pack, ASPATIAL[1], ErrorCode.EXPRESSION_POSITION_ASPATIAL, "variables.yaml")
    assert "the substrate is aspatial" in str(error)
    assert _located_line(pack, error, ErrorCode.EXPRESSION_POSITION_ASPATIAL).startswith("expression:")


def test_aspatial_position_function_in_an_interaction_refuses_at_its_command(tmp_path: Path) -> None:
    pack = _pack(tmp_path, ASPATIAL[0])
    _edit(pack, "levels/L0/affordances.yaml", "value: bar.energy + 0.1", "value: 'bar.energy + distance_to_affordance(\"Bed\")'")
    error = _refused(pack, ASPATIAL[1], ErrorCode.EXPRESSION_POSITION_ASPATIAL, "affordances.yaml")
    assert "distance_to_affordance" in str(error)
    assert _located_line(pack, error, ErrorCode.EXPRESSION_POSITION_ASPATIAL).startswith("value:")


def test_aspatial_positive_control_non_positional_expressions_compile_and_step(tmp_path: Path) -> None:
    pack = _pack(tmp_path, ASPATIAL[0])
    declaration = _ASPATIAL_VARIABLE.format(kind="scalar", initial=0.0, expression="bar.energy * 2.0")
    _edit(pack, "variables.yaml", "  declarations: []", "  declarations:\n" + declaration)
    _step(_env(_compile(pack, ASPATIAL[1]), ASPATIAL[1]))


def test_spatial_substrate_still_admits_position_functions(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    _declare(pack, _agent_variable("to_sleep", "scalar", 0.0, "'distance_to_affordance(\"SLEEP\")'"))
    env = _env(_compile(pack, SEA[1]), SEA[1])
    _step(env)
    assert bool((env.vfs_registry.get("to_sleep", reader="engine") >= 0.0).all())


# --- P3(b): reference refusals locate the exact child key, not the parent mapping -------


def test_p3b_dac_modifier_bar_refusal_points_at_the_bar_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "default_curriculum")
    _edit(pack, f"levels/{L1}/drive.yaml", "    energy_crisis:\n      bar: energy", "    energy_crisis:\n      bar: nosuch")
    error = _refused(pack, L1, ErrorCode.DAC_REF_UNDEFINED_MODIFIER_BAR, "drive.yaml")
    assert _located_line(pack, error, ErrorCode.DAC_REF_UNDEFINED_MODIFIER_BAR) == "bar: nosuch"


def test_p3b_dac_shaping_refusal_is_exact_when_the_reference_is_not_the_first_child(tmp_path: Path) -> None:
    """`target_affordance` is the third key of its shaping entry; the parent lookup was two lines up."""
    pack = _pack(tmp_path, "default_curriculum")
    _edit(pack, f"levels/{L1}/drive.yaml", "target_affordance: EAT", "target_affordance: NOPE")
    error = _refused(pack, L1, ErrorCode.DAC_REF_UNDEFINED_APPROACH_AFFORDANCE, "drive.yaml")
    assert _located_line(pack, error, ErrorCode.DAC_REF_UNDEFINED_APPROACH_AFFORDANCE) == "target_affordance: NOPE"


def test_p3b_clock_reference_refusal_points_at_the_period_of_line(tmp_path: Path) -> None:
    level = "L3_temporal_mechanics"
    pack = _pack(tmp_path, "default_curriculum")
    _edit(pack, f"levels/{level}/curriculum.yaml", "period_of: day_phase", "period_of: nosuch")
    error = _refused(pack, level, ErrorCode.CLOCK_REFERENCE, "curriculum.yaml")
    assert _located_line(pack, error, ErrorCode.CLOCK_REFERENCE).startswith("period_of: nosuch")


# --- P3(c): effects_hash is content, not transport order --------------------------------


ITEMS_SMOKE = ("test/items_smoke", "L0_smoke")


def _split_food_decay(pack: Path, fragment: str) -> None:
    effects = pack / "effects.yaml"
    text = effects.read_text()
    start = text.index('  - id: "food_decay"')
    food = text[start:]
    effects.write_text(text[:start])
    (pack / fragment).write_text('version: "1.0"\neffect_definitions:\n' + food)


@pytest.mark.parametrize("fragment", ["aa_more_effects.yaml", "zz_more_effects.yaml"])
def test_p3c_moving_an_effect_to_another_fragment_keeps_effects_hash(tmp_path: Path, fragment: str) -> None:
    base = _compile(_pack(tmp_path / "base", ITEMS_SMOKE[0]), ITEMS_SMOKE[1])
    moved_pack = _pack(tmp_path / "moved", ITEMS_SMOKE[0])
    _split_food_decay(moved_pack, fragment)
    moved = _compile(moved_pack, ITEMS_SMOKE[1])
    assert base.effects_hash is not None
    assert moved.effects_hash == base.effects_hash


def test_p3c_swapping_effect_definitions_keeps_effects_hash_and_a_body_edit_moves_it(tmp_path: Path) -> None:
    base = _compile(_pack(tmp_path / "base", ITEMS_SMOKE[0]), ITEMS_SMOKE[1])
    swapped_pack = _pack(tmp_path / "swapped", ITEMS_SMOKE[0])
    effects = swapped_pack / "effects.yaml"
    text = effects.read_text()
    first, second, third = (text.index(f'  - id: "{name}"') for name in ("wear_and_tear", "item_degradation", "item_break"))
    effects.write_text(text[:first] + text[second:third] + text[first:second] + text[third:])
    assert _compile(swapped_pack, ITEMS_SMOKE[1]).effects_hash == base.effects_hash

    edited_pack = _pack(tmp_path / "edited", ITEMS_SMOKE[0])
    _edit(edited_pack, "effects.yaml", "(1.0 * intensity)", "(1.5 * intensity)")
    assert _compile(edited_pack, ITEMS_SMOKE[1]).effects_hash != base.effects_hash


def test_p3c_int_and_float_literals_hash_as_every_sibling_canonical_ast_hash_does(tmp_path: Path) -> None:
    """`1` and `1.0` are distinct DSL constants (by value and type) in every canonical-AST pack hash."""
    from townlet.vfs.schema_hashes import canonical_expression_ast
    from townlet.world.expression import ExpressionParser

    parser = ExpressionParser()
    assert canonical_expression_ast(parser.parse("x * 1.0")) != canonical_expression_ast(parser.parse("x * 1"))
    base = _compile(_pack(tmp_path / "base", ITEMS_SMOKE[0]), ITEMS_SMOKE[1])
    edited_pack = _pack(tmp_path / "edited", ITEMS_SMOKE[0])
    _edit(edited_pack, "effects.yaml", "(1.0 * intensity)", "(1 * intensity)")
    assert _compile(edited_pack, ITEMS_SMOKE[1]).effects_hash != base.effects_hash


# --- P3(g): a persistent reference to an episode row refuses at its declaration ---------


def _ref_variable(identifier: str, kind: str, scope: str, lifetime: str) -> str:
    return (
        f"  - id: {identifier}\n    scope: {scope}\n    type: {kind}\n    lifetime: {lifetime}\n    semantic_type: custom\n"
        "    readable_by: [engine]\n    writable_by: [engine]\n    exposed_to: []\n    initial_value: null\n"
    )


@pytest.mark.parametrize("kind", ["effect_ref", "affordance_ref", "item_ref"])
@pytest.mark.parametrize("scope", ["agent", "global"])
def test_p3g_persistent_episode_row_reference_refuses_at_the_declaration_line(tmp_path: Path, kind: str, scope: str) -> None:
    pack = _pack(tmp_path, SEA[0])
    _declare(pack, _ref_variable("held", kind, scope, "persistent"))
    error = _refused(pack, SEA[1], ErrorCode.LOAD_ERROR, "variables.yaml")
    assert f"is an {kind} with lifetime persistent" in str(error) and "lifetime: episode" in str(error)
    assert _located_line(pack, error, ErrorCode.LOAD_ERROR) == "- id: held"


@pytest.mark.parametrize("kind", ["effect_ref", "affordance_ref"])
def test_p3g_episode_lifetime_references_compile_and_step(tmp_path: Path, kind: str) -> None:
    pack = _pack(tmp_path, SEA[0])
    _declare(pack, _ref_variable("held", kind, "agent", "episode"))
    _step(_env(_compile(pack, SEA[1]), SEA[1]))


# --- P3(d): the identity gate's docstring names every compared hash ----------------------


def test_p3d_checkpoint_identity_docstring_names_every_hash_key() -> None:
    from townlet.training.checkpoint_utils import LEVEL_HASH_KEYS, PACK_HASH_KEYS, assert_checkpoint_identity

    doc = assert_checkpoint_identity.__doc__ or ""
    for key in PACK_HASH_KEYS:
        assert f"``{key.removesuffix('_hash')}``" in doc, key
    for _, name in LEVEL_HASH_KEYS:
        assert f"``{name}``" in doc, name
    for stale in ("four per-level", "six pack-scope"):
        assert stale not in doc


def test_d3_writes_in_one_phase_compose_before_the_meter_is_clamped(tmp_path: Path) -> None:
    """+0.8 and -0.8 on one meter in one phase cancel: the clamp applies once, at the phase commit.

    Satiation starts at its upper bound 1.0, so a per-write clamp would end at 0.2.
    """
    baseline_pack = _rules_pack(tmp_path, [], "baseline")
    (baseline_pack / "transition_rules.yaml").unlink()
    cancelling = [
        {"id": "up", "phase": "apply_transition_rules", "condition": None, "writes": [_write("bar.satiation", "0.8")]},
        {"id": "down", "phase": "apply_transition_rules", "condition": None, "writes": [_write("bar.satiation", "-0.8")]},
    ]
    pack = _rules_pack(tmp_path, cancelling, "cancelling")
    baseline = _meters_after_one_wait(baseline_pack)
    cancelled = _meters_after_one_wait(pack)
    assert cancelled["satiation"] == pytest.approx(baseline["satiation"], abs=1e-6)


# --- P3(f): the schema docs' examples are what they claim to be -------------------------


DOCS = Path(__file__).parents[4] / "docs"


def _yaml_blocks(path: Path) -> list[tuple[int, str]]:
    import re

    text = path.read_text()
    return [(text[: match.start()].count("\n") + 1, match.group(1)) for match in re.finditer(r"```yaml\n(.*?)```", text, flags=re.DOTALL)]


@pytest.mark.parametrize("doc", ["config-schemas/expressions.md", "config-schemas/variables.md", "config-schemas/transition_rules.md"])
def test_p3f_every_yaml_block_in_the_schema_docs_parses(doc: str) -> None:
    import yaml

    for line, body in _yaml_blocks(DOCS / doc):
        try:
            yaml.safe_load(body)
        except yaml.YAMLError as exc:  # pragma: no cover - the failure message is the point
            pytest.fail(f"{doc}:{line} is not valid YAML: {exc}")


def test_p3f_variables_md_time_since_declaration_is_complete(tmp_path: Path) -> None:
    import yaml

    from townlet.config.variables_config import VariableDeclaration

    (body,) = [body for _, body in _yaml_blocks(DOCS / "config-schemas/variables.md") if "id: time_since_last_sleep" in body]
    (declaration,) = yaml.safe_load(body)
    VariableDeclaration.model_validate(declaration)


def test_p3f_expressions_md_names_only_the_real_effect_locals() -> None:
    from townlet.world.expression.references import EFFECT_LOCALS

    text = (DOCS / "config-schemas/expressions.md").read_text()
    assert '"duration"' not in text and "'duration'" not in text
    assert "(future)" not in text
    for local in EFFECT_LOCALS:
        assert local in text


def test_p3f_vfs_md_marks_every_undeclared_rule_name_as_illustrative() -> None:
    import re

    text = (DOCS / "architecture/VFS.md").read_text()
    for match in re.finditer(r"```yaml\n(.*?)```", text, flags=re.DOTALL):
        if "transition_rules:" not in match.group(1) or "public_reputation" not in match.group(1):
            continue
        preceding = text[: match.start()].rstrip().splitlines()[-1]
        assert preceding.startswith("*Illustrative names:"), text[: match.start()].count("\n") + 1
