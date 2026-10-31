"""Compiler re-review (lens `compiler`, 2026-10-31): every refusal the compile used to leave to the runtime.

Each case is one literal edit to a scratch copy of a shipped pack, compiled with the public
compiler. A refusal must carry its registry code and a `file:line` location inside the pack;
the positive controls compile AND step an environment, which is what the original finding
could not do.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import torch

from townlet.universe import __main__ as compiler_cli
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.error_codes import ErrorCode
from townlet.universe.errors import CompilationError

CONFIGS = Path(__file__).parents[4] / "configs"
SEA = ("static_epistemic_access", "L0_simple")
EFFECTS_SMOKE = ("test/effects_smoke", "L0_effects")
GRIDND = ("test/gridnd_4d_pack", "L0_test")
CONTINUOUS = ("test/action_space/continuous1d", "L0")
ASPATIAL = ("test/action_space/aspatial", "L0")
ITEMS_SMOKE = ("test/items_smoke", "L0_smoke")
ACTION_MASKING = ("test/action_masking", "L0_masking")


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


def _step(universe, level: str, steps: int = 4) -> None:
    env = universe.create_environment(num_agents=2, level_name=level, device="cpu")
    env.reset()
    generator = torch.Generator().manual_seed(0)
    for _ in range(steps):
        env.step(torch.randint(0, env.action_dim, (2,), generator=generator))


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


# --- N1: shapes the compile accepted and env construction refused ---------------------


def test_n1a_empty_custom_action_name_refuses_at_parse(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    _edit(pack, "actions.yaml", "  - name: ADVANCE", "  - name: ''")
    error = _refused(pack, SEA[1], ErrorCode.LOAD_ERROR, "actions.yaml")
    assert "custom_actions[" in str(error)


def test_n1b_item_arena_without_item_profile_refuses_at_the_arena_size(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    _edit(pack, "items.yaml", "max_items_in_world: 0", "max_items_in_world: 1")
    error = _refused(pack, SEA[1], ErrorCode.ITEM_ARENA_PROFILE_MISSING, "items.yaml")
    assert "item_profiles is empty" in str(error)


def test_n1c_fixed_position_rank_mismatch_refuses_at_the_positions_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, EFFECTS_SMOKE[0])
    _edit(pack, "levels/L0_effects/affordances.yaml", "      - - 2\n        - 2", "      - - 2\n        - 2\n        - 2")
    error = _refused(pack, EFFECTS_SMOKE[1], ErrorCode.AFFORDANCE_POSITION_SUBSTRATE, "affordances.yaml")
    assert "has 3 coordinate(s), but the grid substrate has rank 2" in str(error)


def test_n1d_random_deployment_under_randomize_false_refuses_at_the_type_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    _edit(pack, "levels/L0_simple/training.yaml", "randomize_affordances: true", "randomize_affordances: false")
    error = _refused(pack, SEA[1], ErrorCode.AFFORDANCE_POSITION_REQUIRED, "affordances.yaml")
    assert "randomize_affordances: false" in str(error)


def test_n1e_fixed_position_outside_the_grid_refuses(tmp_path: Path) -> None:
    pack = _pack(tmp_path, EFFECTS_SMOKE[0])
    _edit(pack, "levels/L0_effects/affordances.yaml", "      - - 2\n        - 2", "      - - 99\n        - 2")
    error = _refused(pack, EFFECTS_SMOKE[1], ErrorCode.AFFORDANCE_POSITION_SUBSTRATE, "affordances.yaml")
    assert "[99, 2] lies outside" in str(error)


def test_n1_fixed_position_on_aspatial_substrate_refuses(tmp_path: Path) -> None:
    pack = _pack(tmp_path, ASPATIAL[0])
    _edit(pack, "levels/L0/affordances.yaml", "      type: random\n      positions: []", "      type: fixed\n      positions: [[0, 0]]")
    _refused(pack, ASPATIAL[1], ErrorCode.AFFORDANCE_POSITION_SUBSTRATE, "affordances.yaml")


def test_n1_continuous_fixed_position_is_checked_against_bounds(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    affordances = pack / "levels/L0/affordances.yaml"
    text = affordances.read_text()
    assert "positions:" in text
    # The shipped pack compiles and steps with its in-bounds positions (positive control) ...
    _step(_compile(pack, CONTINUOUS[1]), CONTINUOUS[1])
    # ... and a coordinate beyond the declared bound refuses.
    import yaml

    document = yaml.safe_load(text)
    first = document["affordances"]["affordances"][0]
    assert first["deployment"]["type"] == "fixed"
    first["deployment"]["positions"] = [[10_000]]
    affordances.write_text(yaml.safe_dump(document, sort_keys=False))
    _refused(pack, CONTINUOUS[1], ErrorCode.AFFORDANCE_POSITION_SUBSTRATE, "affordances.yaml")


def test_n1_positive_control_fixed_positions_inside_the_grid_compile_and_step(tmp_path: Path) -> None:
    pack = _pack(tmp_path, EFFECTS_SMOKE[0])
    _step(_compile(pack, EFFECTS_SMOKE[1]), EFFECTS_SMOKE[1])


# --- N2: substrate rank rules refuse at parse, located; nothing escapes stage 7 bare -----


@pytest.mark.parametrize("sizes", ["[5]", "[5, 5, 5]"])
def test_n2_gridnd_rank_below_four_refuses_at_the_declaration(tmp_path: Path, sizes: str) -> None:
    pack = _pack(tmp_path, GRIDND[0])
    _edit(pack, "stratum.yaml", "dimension_sizes: [5, 5, 5, 5]", f"dimension_sizes: {sizes}")
    error = _refused(pack, GRIDND[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert "a gridnd substrate has 4 to 100" in str(error)


def test_n2_continuousnd_rank_below_four_refuses_at_the_declaration(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "type: continuous\n", "type: continuousnd\n")
    error = _refused(pack, CONTINUOUS[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert "type='continuousnd' serves 4 to 100 dimensions" in str(error)


def test_n2_continuous_rank_above_three_refuses_at_the_declaration(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "dimensions: 1", "dimensions: 4")
    _edit(pack, "stratum.yaml", "- [0.0, 10.0]", "- [0.0, 10.0]\n        - [0.0, 10.0]\n        - [0.0, 10.0]\n        - [0.0, 10.0]")
    error = _refused(pack, CONTINUOUS[1], ErrorCode.LOAD_ERROR, "stratum.yaml")
    assert "type='continuous' serves 1 to 3 dimensions" in str(error)


def test_n2_stage_seven_wraps_a_bare_value_error_with_the_level_location(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A ValueError raised below the compiler inside the level stage is reported, coded, at the level."""
    from townlet.universe.compilers import actions as actions_module

    class ExplodingFactory:
        @staticmethod
        def build(*args, **kwargs):
            raise ValueError("substrate constructor refused")

    # Only the level stage's own reference: stage 3 keeps the real factory.
    monkeypatch.setattr(actions_module, "SubstrateFactory", ExplodingFactory)
    pack = _pack(tmp_path, SEA[0])
    with pytest.raises(CompilationError) as caught:
        _compile(pack, SEA[1])
    (issue,) = [issue for issue in caught.value.issues if issue.code == ErrorCode.LEVEL_COMPILE_REFUSED]
    assert "ValueError: substrate constructor refused" in issue.message
    assert issue.location == f"{pack / 'levels' / SEA[1]}:1"


# --- N3: a custom action may not shadow a substrate or engine action -------------------


def test_n3_custom_action_named_after_a_substrate_action_refuses_at_its_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    _edit(pack, "actions.yaml", "  - name: ADVANCE", "  - name: UP")
    error = _refused(pack, SEA[1], ErrorCode.ACTION_NAME_RESERVED, "actions.yaml")
    assert "Custom action 'UP'" in str(error) and "substrate" in str(error)
    line = int(next(issue.location for issue in error.issues if issue.code == ErrorCode.ACTION_NAME_RESERVED).rpartition(":")[2])
    assert (pack / "actions.yaml").read_text().splitlines()[line - 1].strip() == "- name: UP"


@pytest.mark.parametrize("name", ["INTERACT", "GET", "USE_SLOT_0", "DROP_SLOT_0"])
def test_n3_engine_action_names_refuse_with_a_code_and_a_location(tmp_path: Path, name: str) -> None:
    pack = _pack(tmp_path, ITEMS_SMOKE[0])
    _edit(
        pack,
        "actions.yaml",
        "  custom_actions:\n",
        f"  custom_actions:\n    - name: {name}\n      description: shadow\n      enabled_by_default: true\n",
    )
    error = _refused(pack, ITEMS_SMOKE[1], ErrorCode.ACTION_NAME_RESERVED, "actions.yaml")
    assert f"Custom action '{name}'" in str(error)


def test_n3_positive_control_a_custom_action_with_writes_keeps_them(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    universe = _compile(pack, SEA[1])
    advance = next(action for action in universe.get_level(SEA[1]).runtime_action_space.actions if action.name == "ADVANCE")
    assert len(advance.writes) == 2
    _step(universe, SEA[1])


# --- N4: continuous bounds must be finite --------------------------------------------


@pytest.mark.parametrize("bounds", ["[-.inf, .inf]", "[0.0, .inf]", "[.nan, 1.0]"])
def test_n4_nonfinite_continuous_bounds_refuse_at_the_declaration(tmp_path: Path, bounds: str) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    _edit(pack, "stratum.yaml", "- [0.0, 10.0]", f"- {bounds}")
    _refused(pack, CONTINUOUS[1], ErrorCode.LOAD_ERROR, "stratum.yaml")


def test_n4_positive_control_finite_bounds_produce_finite_observations(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONTINUOUS[0])
    universe = _compile(pack, CONTINUOUS[1])
    env = universe.create_environment(num_agents=2, level_name=CONTINUOUS[1], device="cpu")
    observation = env.reset()
    assert torch.isfinite(env.positions).all()
    assert torch.isfinite(observation).all()


# --- N6: a variable id is an expression identifier ----------------------------------


@pytest.mark.parametrize("identifier", ["true", "false", "and", "if", "a b", "1x", "x-y", "énergie", "bar.energy", "x[0]"])
def test_n6_unreferenceable_variable_ids_refuse_at_the_declaration_line(tmp_path: Path, identifier: str) -> None:
    pack = _pack(tmp_path, SEA[0])
    declaration = (
        f"  - id: '{identifier}'\n    scope: agent\n    type: scalar\n    lifetime: episode\n    semantic_type: custom\n"
        "    readable_by: [engine]\n    writable_by: [engine]\n    exposed_to: []\n    initial_value: 0.0\n  - id: hidden_score"
    )
    _edit(pack, "variables.yaml", "  - id: hidden_score", declaration)
    error = _refused(pack, SEA[1], ErrorCode.LOAD_ERROR, "variables.yaml")
    assert "is not an expression identifier" in str(error)
    assert "[A-Za-z_][A-Za-z0-9_]*" in str(error)


def test_n6_the_grammar_is_the_parsers_own() -> None:
    from townlet.world.expression import ExpressionParser
    from townlet.world.expression.ast_nodes import Constant, Variable
    from townlet.world.expression.references import EXPRESSION_KEYWORDS, is_identifier

    parser = ExpressionParser()
    assert is_identifier("hidden_score") and isinstance(parser.parse("hidden_score"), Variable)
    for keyword in EXPRESSION_KEYWORDS:
        assert not is_identifier(keyword)
    assert isinstance(parser.parse("true"), Constant)
    assert not is_identifier("énergie")
    with pytest.raises(Exception):
        parser.parse("énergie")


def test_n6_shipped_packs_declare_only_identifiers() -> None:
    import yaml

    from townlet.world.expression.references import is_identifier

    offenders = []
    for path in sorted(CONFIGS.rglob("variables.yaml")):
        if ".compiled" in path.parts:
            continue
        document = yaml.safe_load(path.read_text())
        for declaration in document["variables"]["declarations"]:
            if not is_identifier(str(declaration["id"])):
                offenders.append(f"{path}:{declaration['id']}")
    assert not offenders


# --- A4-minimal: opening hours need a 24-tick day --------------------------------------


def test_a4_opening_hours_on_a_non_24_tick_day_refuse_at_the_opening_hours_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, ACTION_MASKING[0])
    _edit(pack, "levels/L0_masking/curriculum.yaml", "day_length: 24", "day_length: 48")
    _edit(
        pack,
        "levels/L0_masking/affordances.yaml",
        "    opening_hours:\n      enabled: false",
        "    opening_hours:\n      enabled: true\n      schedule:\n        - start: 6\n          end: 20",
    )
    error = _refused(pack, ACTION_MASKING[1], ErrorCode.AFFORDANCE_OPENING_HOURS_DAY_PERIOD, "affordances.yaml")
    assert "opening hours currently require a 24-tick day period" in str(error)
    line = int(
        next(issue.location for issue in error.issues if issue.code == ErrorCode.AFFORDANCE_OPENING_HOURS_DAY_PERIOD).rpartition(":")[2]
    )
    assert (pack / "levels/L0_masking/affordances.yaml").read_text().splitlines()[line - 1].strip() == "opening_hours:"


def test_a4_positive_control_opening_hours_on_a_24_tick_day_compile_and_step(tmp_path: Path) -> None:
    pack = _pack(tmp_path, ACTION_MASKING[0])
    _edit(
        pack,
        "levels/L0_masking/affordances.yaml",
        "    opening_hours:\n      enabled: false",
        "    opening_hours:\n      enabled: true\n      schedule:\n        - start: 6\n          end: 20",
    )
    universe = _compile(pack, ACTION_MASKING[1])
    assert universe.get_level(ACTION_MASKING[1]).token_type_schema_hash.startswith("de093a6e9f59924e")
    _step(universe, ACTION_MASKING[1])


def test_a4_inactive_temporal_level_with_a_null_day_length_is_not_checked(tmp_path: Path) -> None:
    """The gate only runs with active temporal mechanics; an inactive level declares no period."""
    pack = _pack(tmp_path, "default_curriculum")
    universe = _compile(pack, "L1_full_observability")
    level = universe.get_level("L1_full_observability")
    assert level.curriculum.curriculum.day_length is None
    assert any(affordance.opening_hours.enabled for affordance in level.affordances.affordances)


# --- N8: artifact bytes do not follow PYTHONHASHSEED -----------------------------------


def test_n8_evaluation_marks_serialize_sorted(tmp_path: Path) -> None:
    pack = _pack(tmp_path, "test/vfs_dependency_chain")
    universe = _compile(pack, "L0_deps")
    assert universe.vfs_evaluation_marks
    payload = universe.to_dict()["vfs_evaluation_marks"]
    for key, marks in payload.items():
        assert marks == sorted(marks), key
        assert set(marks) == universe.vfs_evaluation_marks[key]


# --- N10: codes, discovery hygiene, inspect exit status --------------------------------


def test_n10_duplicate_symbol_refusals_carry_a_code() -> None:
    from townlet.config.actions_config import CustomActionConfig
    from townlet.universe.symbol_table import UniverseSymbolTable

    table = UniverseSymbolTable()
    action = CustomActionConfig(name="REST", description="rest", enabled_by_default=True)
    table.register_action(action)
    with pytest.raises(CompilationError) as caught:
        table.register_action(action)
    assert [issue.code for issue in caught.value.issues] == [ErrorCode.SYMBOL_DUPLICATE]


def test_n10_duplicate_custom_action_names_both_origins_at_discovery(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    (pack / "more_actions.yaml").write_text(
        "actions:\n  version: '1.0'\n  substrate_actions:\n    inherit: true\n  custom_actions:\n"
        "  - name: ADVANCE\n    description: again\n    enabled_by_default: true\n  labels:\n    preset: gaming\n"
    )
    error = _refused(pack, SEA[1], ErrorCode.DECLARATION_COLLISION, "more_actions.yaml")
    assert f"{pack / 'actions.yaml'}:" in str(error)


def test_n10_cache_write_failure_is_a_coded_located_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from townlet.universe.compiled import CompiledUniverse

    def refuse(self, path):
        raise OSError("disk full")

    monkeypatch.setattr(CompiledUniverse, "save_to_cache", refuse)
    pack = _pack(tmp_path, SEA[0])
    with pytest.raises(CompilationError) as caught:
        UniverseCompiler().compile(pack, primary_level=SEA[1], use_cache=True)
    (issue,) = caught.value.issues
    assert issue.code == ErrorCode.CACHE_WRITE_FAILED
    assert issue.location == f"{pack / '.compiled' / 'universe-L0_simple.msgpack'}:1"
    assert "disk full" in issue.message


@pytest.mark.parametrize("name", ["extra.YAML", "extra.YML", "levels/L0_simple/Extra.Yaml"])
def test_n10_uppercase_yaml_suffix_is_refused_not_ignored(tmp_path: Path, name: str) -> None:
    pack = _pack(tmp_path, SEA[0])
    (pack / name).write_text("bogus: true\n")
    error = _refused(pack, SEA[1], ErrorCode.DECLARATION_SCOPE, name)
    assert "lowercase .yaml or .yml suffix" in str(error)


def test_n10_dotfiles_and_dot_directories_are_not_transport(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    before = _compile(pack, SEA[1])
    # An editor lock file is a broken symlink; a dot directory is not a level; neither is read.
    (pack / "levels" / SEA[1] / ".#bars.yaml").symlink_to("john@host.1234")
    (pack / ".git").mkdir()
    (pack / ".git" / "config.yaml").write_text("bogus: true\n")
    (pack / "levels" / ".backup").mkdir()
    (pack / ".hidden.yaml").write_text("bogus: true\n")
    after = _compile(pack, SEA[1])
    assert after.metadata.config_hash == before.metadata.config_hash
    assert after.available_levels == before.available_levels


def test_n10_a_file_directly_under_levels_is_refused(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA[0])
    shutil.copyfile(pack / "experiment.yaml", pack / "levels" / "stray.yaml")
    error = _refused(pack, SEA[1], ErrorCode.DECLARATION_SCOPE, "levels/stray.yaml")
    assert "belongs to no level" in str(error)


def test_n10_inspect_with_a_mismatched_primary_level_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    pack = _pack(tmp_path, SEA[0])
    assert compiler_cli.main(["compile", str(pack), "--primary-level", SEA[1]]) == 0
    artifact = pack / ".compiled" / f"universe-{SEA[1]}.msgpack"
    capsys.readouterr()
    assert compiler_cli.main(["inspect", str(artifact), "--primary-level", "OTHER"]) == 1
    captured = capsys.readouterr()
    assert "ARTIFACT_LOAD_REFUSED" in captured.err and "'OTHER'" in captured.err
    assert compiler_cli.main(["inspect", str(artifact), "--primary-level", SEA[1]]) == 0


def test_n3_custom_wait_on_a_grid_is_not_a_shadow() -> None:
    """Grid2D binds no WAIT of its own (`substrate/grid2d.py`), so the shipped custom WAIT stands."""
    universe = _compile(CONFIGS / "default_curriculum", "L1_full_observability")
    actions = universe.get_level("L1_full_observability").runtime_action_space.actions
    waits = [action for action in actions if action.name == "WAIT"]
    assert len(waits) == 1 and waits[0].source == "custom" and waits[0].type == "passive"
    assert actions[-1].name != "WAIT" or waits[0].source == "custom"
