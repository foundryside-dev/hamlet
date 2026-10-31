"""The post-green P3 sweep (2026-11-01): each cheap, contained fix with the behaviour it changes.

STATUS.md §7.5: scope-aware undeployed-affordance checks, expression-field-only static facts,
literal draw bounds, located effect budgets, unquoted affordance names, strict artifact keys,
an exact command round trip, and content-canonical affordance/item hashes.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

import msgpack
import pytest
import yaml

from townlet.config.drive_as_code import DriveAsCodeConfig, VFSVariableBonusConfig
from townlet.config.effects_config import CommandConfig
from townlet.config.training_v2_config import EnabledActionsConfig
from townlet.effects.parser import CommandParser
from townlet.universe.compiled import COMPILED_LEVEL_FIELDS, REQUIRED_COMPILED_UNIVERSE_FIELDS, CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError

CONFIGS = Path(__file__).resolve().parents[4] / "configs"
SEA, SEA_LEVEL = CONFIGS / "static_epistemic_access", "L0_simple"


def _pack(tmp_path: Path, source: Path, name: str = "pack") -> Path:
    dest = tmp_path / name
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns(".compiled"))
    return dest


def _compile(pack: Path, level: str) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _refusal(pack: Path, level: str) -> CompilationError:
    with pytest.raises(CompilationError) as caught:
        _compile(pack, level)
    return caught.value


def _located_line(pack: Path, refusal: CompilationError, code: str) -> str:
    """The source line a refusal with ``code`` points at."""
    match = re.search(rf"\[{re.escape(code)}\] (\S+):(\d+)", str(refusal))
    assert match is not None, str(refusal)
    path, line = Path(match.group(1)), int(match.group(2))
    assert path.is_relative_to(pack)
    return path.read_text().splitlines()[line - 1].strip()


def _add_variable(pack: Path, expression: str, **extra: Any) -> None:
    path = pack / "variables.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["variables"]["declarations"].append(
        {
            "id": "probe",
            "scope": "agent",
            "type": "scalar",
            "lifetime": "episode",
            "semantic_type": "custom",
            "readable_by": ["engine", "agent"],
            "writable_by": ["engine"],
            "exposed_to": [],
            "initial_value": 0.0,
            "expression": expression,
            **extra,
        }
    )
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, (path, old)
    path.write_text(text.replace(old, new, 1))


def _undeploy(pack: Path, level: str, affordance: str) -> None:
    _edit(pack / "levels" / level / "training.yaml", f"    - {affordance}\n", "")


def _two_level_sea(tmp_path: Path) -> Path:
    """The witness pack with a second level, `L1_other`, that does not deploy COOK."""
    pack = _pack(tmp_path, SEA)
    shutil.copytree(pack / "levels" / SEA_LEVEL, pack / "levels" / "L1_other")
    _undeploy(pack, "L1_other", "COOK")
    return pack


# --- 1. The undeployed-affordance check follows declaration scope ----------------------------


def test_a_level_scoped_interaction_is_checked_against_its_own_level_only(tmp_path: Path) -> None:
    pack = _two_level_sea(tmp_path)
    _edit(pack / "levels" / SEA_LEVEL / "affordances.yaml", "value: bar.energy + 0.8", 'value: bar.energy + distance_to_affordance("COOK")')
    assert _compile(pack, SEA_LEVEL).get_level(SEA_LEVEL).level_name == SEA_LEVEL


def test_a_level_scoped_interaction_refuses_when_its_own_level_does_not_deploy(tmp_path: Path) -> None:
    pack = _two_level_sea(tmp_path)
    _edit(pack / "levels" / SEA_LEVEL / "affordances.yaml", "value: bar.energy + 0.8", 'value: bar.energy + distance_to_affordance("COOK")')
    _undeploy(pack, SEA_LEVEL, "COOK")
    refusal = _refusal(pack, SEA_LEVEL)
    message = str(refusal)
    assert f"level '{SEA_LEVEL}' does not deploy 'COOK'" in message
    assert "level 'L1_other'" not in message
    assert _located_line(pack, refusal, "EXPRESSION-AFFORDANCE-UNDEPLOYED").startswith("value:")


def test_a_pack_scoped_expression_is_checked_against_every_level(tmp_path: Path) -> None:
    pack = _two_level_sea(tmp_path)
    _add_variable(pack, 'distance_to_affordance("COOK")')
    assert "level 'L1_other' does not deploy 'COOK'" in str(_refusal(pack, SEA_LEVEL))


# --- 2. Only expression-bearing fields are parsed ---------------------------------------------


def test_a_description_is_prose_and_never_parsed_as_an_expression(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA)
    _add_variable(pack, "bar.energy", description='distance_to_affordance("NOPE") and uniform(5.0, 2.0)')
    assert "probe" in {variable.id for variable in _compile(pack, SEA_LEVEL).get_level(SEA_LEVEL).vfs_variables}


# --- 3. Literal draw arguments that cannot be right -------------------------------------------


@pytest.mark.parametrize(
    ("expression", "fragment"),
    [
        ("uniform(5.0, 2.0)", "uniform(5, 2)"),
        ("uniform(1, -1)", "uniform(1, -1)"),
        ("normal_dist(0.0, -2.0)", "normal_dist(..., -2)"),
    ],
)
def test_a_literal_draw_range_that_cannot_be_right_refuses_at_the_expression(tmp_path: Path, expression: str, fragment: str) -> None:
    pack = _pack(tmp_path, SEA)
    _add_variable(pack, expression)
    refusal = _refusal(pack, SEA_LEVEL)
    assert fragment in str(refusal)
    assert _located_line(pack, refusal, "EXPRESSION-DRAW-RANGE").startswith("expression:")


@pytest.mark.parametrize("expression", ["uniform(-1.0, 2.0)", "uniform(3.0, 3.0)", "normal_dist(0.0, 0.0)", "uniform(bar.energy, 2.0)"])
def test_an_admissible_or_computed_draw_range_compiles(tmp_path: Path, expression: str) -> None:
    pack = _pack(tmp_path, SEA)
    _add_variable(pack, expression)
    _compile(pack, SEA_LEVEL)


def _action_write_site(pack: Path) -> tuple[Path, str]:
    _edit(
        pack / "actions.yaml",
        "      expression: '1.0'\n      condition: null\n      composition: additive_delta",
        "      expression: uniform(5.0, 2.0)\n      condition: null\n      composition: additive_delta",
    )
    return pack, SEA_LEVEL


def _transition_rule_site(pack: Path) -> tuple[Path, str]:
    rule = {
        "id": "probe_rule",
        "phase": "apply_transition_rules",
        "condition": None,
        "writes": [
            {
                "variable_id": "public_state",
                "expression": "uniform(5.0, 2.0)",
                "composition": "overwrite",
                "condition": None,
                "clamp": None,
                "effect": None,
            }
        ],
    }
    (pack / "transition_rules.yaml").write_text(yaml.safe_dump({"version": "1.0", "transition_rules": [rule]}, sort_keys=False))
    return pack, SEA_LEVEL


def _effect_pipeline_site(pack: Path) -> tuple[Path, str]:
    _edit(pack / "effects.yaml", 'value: "bar.energy + (0.05 * intensity)"', 'value: "bar.energy + uniform(5.0, 2.0)"')
    return pack, "L0_effects"


def _item_hook_site(pack: Path) -> tuple[Path, str]:
    _edit(pack / "items.yaml", "value: bar.energy + 0.3", "value: bar.energy + uniform(5.0, 2.0)")
    return pack, "L0_smoke"


def _nested_effect_site(wrapper: str) -> Any:
    """A draw inside a nested command body: ``delay``/``for_each`` (``do``), ``if`` (``then``), ``switch`` (``cases[].do``)."""
    inner = {"modify": "bar.energy", "value": "bar.energy + uniform(5.0, 2.0)"}
    wrappers = {
        "delay": {"delay": "1", "do": [inner]},
        "if": {"if": "true", "then": [inner], "else": []},
        "for_each": {"for_each": "all_agents", "as": "a", "do": [inner]},
        "switch": {"switch": "1", "cases": [{"when": "1", "do": [inner]}], "default": []},
        "parallel": {"parallel": [inner]},
    }

    def place(pack: Path) -> tuple[Path, str]:
        path = pack / "effects.yaml"
        payload = yaml.safe_load(path.read_text())
        definition = payload["effect_definitions"][0]
        stage = next(stage for stage in ("on_spawn", "on_tick") if definition.get(stage))
        definition[stage] = [wrappers[wrapper]]
        path.write_text(yaml.safe_dump(payload, sort_keys=False))
        return pack, "L0_effects"

    return place


@pytest.mark.parametrize(
    ("source", "place", "expected_line"),
    [
        (SEA, _action_write_site, "expression: uniform(5.0, 2.0)"),
        (SEA, _transition_rule_site, "- id: probe_rule"),
        (CONFIGS / "test" / "effects_smoke", _effect_pipeline_site, 'value: "bar.energy + uniform(5.0, 2.0)"'),
        (CONFIGS / "test" / "items_smoke", _item_hook_site, "value: bar.energy + uniform(5.0, 2.0)"),
        *(
            (CONFIGS / "test" / "effects_smoke", _nested_effect_site(wrapper), "value: bar.energy + uniform(5.0, 2.0)")
            for wrapper in ("delay", "if", "for_each", "switch", "parallel")
        ),
    ],
    ids=[
        "action-write",
        "transition-rule-write",
        "effect-pipeline",
        "item-hook",
        "effect-delay-do",
        "effect-if-then",
        "effect-for-each-do",
        "effect-switch-case",
        "effect-parallel",
    ],
)
def test_every_expression_site_kind_is_visited(tmp_path: Path, source: Path, place: Any, expected_line: str) -> None:
    pack, level = place(_pack(tmp_path, source))
    refusal = _refusal(pack, level)
    assert _located_line(pack, refusal, "EXPRESSION-DRAW-RANGE") == expected_line


# --- 4. A negative effect budget is located at the budget's own line --------------------------


def test_a_negative_effect_budget_refuses_at_the_budget_line(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONFIGS / "test" / "effects_smoke")
    _edit(pack / "effects.yaml", "  agent: 4", "  agent: -1")
    refusal = _refusal(pack, "L0_effects")
    assert "max_active_effects.agent" in str(refusal)
    assert _located_line(pack, refusal, "LOAD_ERROR") == "agent: -1"


# --- 6. enabled_actions.custom has no default -------------------------------------------------


def test_enabled_actions_custom_is_required() -> None:
    with pytest.raises(ValueError, match="custom"):
        EnabledActionsConfig()  # type: ignore[call-arg]


# --- 8. One shaping class answers to type: vfs_variable ---------------------------------------


def test_vfs_variable_shaping_resolves_to_the_one_remaining_class() -> None:
    drive = yaml.safe_load((CONFIGS / "default_curriculum" / "levels" / "L1_full_observability" / "drive.yaml").read_text())["drive"]
    drive["shaping"] = [{"type": "vfs_variable", "variable": "signal", "weight": 2.0}]
    (bonus,) = DriveAsCodeConfig.model_validate(drive).shaping
    assert isinstance(bonus, VFSVariableBonusConfig)
    assert (bonus.variable, bonus.weight) == ("signal", 2.0)


# --- 9. Messages that name the fix ------------------------------------------------------------


def test_an_unquoted_affordance_name_is_told_to_quote_it(tmp_path: Path) -> None:
    pack = _pack(tmp_path, SEA)
    _add_variable(pack, "distance_to_affordance(SLEEP)")
    refusal = _refusal(pack, SEA_LEVEL)
    assert 'Quote it: distance_to_affordance("SLEEP")' in str(refusal)
    assert _located_line(pack, refusal, "EXPRESSION-AFFORDANCE-UNQUOTED").startswith("expression:")


# --- 11. A stale or foreign artifact fails loudly ---------------------------------------------


@pytest.fixture(scope="module")
def model_pack_payload() -> dict[str, Any]:
    return _compile(CONFIGS / "reference" / "model_pack", "L0_demo").to_dict()


def test_the_serialized_key_sets_are_the_declared_ones(model_pack_payload: dict[str, Any]) -> None:
    assert set(model_pack_payload) == set(REQUIRED_COMPILED_UNIVERSE_FIELDS)
    assert set(model_pack_payload["all_levels"]["L0_demo"]) == set(COMPILED_LEVEL_FIELDS)


def test_an_unknown_top_level_key_refuses(model_pack_payload: dict[str, Any]) -> None:
    payload = {**model_pack_payload, "stray": 1}
    with pytest.raises(ValueError, match=r"carries unknown field\(s\) \['stray'\]"):
        CompiledUniverse.from_dict(payload)


def test_an_unknown_level_key_refuses(model_pack_payload: dict[str, Any]) -> None:
    payload = json.loads(json.dumps(model_pack_payload))
    payload["all_levels"]["L0_demo"]["stray"] = 1
    with pytest.raises(ValueError, match=r"'all_levels.L0_demo' carries unknown field\(s\) \['stray'\]"):
        CompiledUniverse.from_dict(payload)


def test_the_cache_fast_path_recompiles_an_artifact_with_an_unknown_key(tmp_path: Path) -> None:
    pack = _pack(tmp_path, CONFIGS / "test" / "model_config")
    compiler = UniverseCompiler()
    compiled = compiler.compile(pack, primary_level="L0_test", use_cache=True)
    payload = compiled.to_dict()
    payload["stray"] = 1
    compiler._cache_artifact_path(pack, "L0_test").write_bytes(msgpack.packb(payload, use_bin_type=True))

    recompiled = UniverseCompiler().compile(pack, primary_level="L0_test", use_cache=True)

    assert recompiled.metadata.universe_name == compiled.metadata.universe_name
    assert "stray" not in recompiled.to_dict()


# --- 12. delay_commands round-trips exactly ---------------------------------------------------


def test_a_fresh_command_and_its_round_trip_agree_on_delay_commands() -> None:
    node = CommandParser().parse_command(CommandConfig.model_validate({"modify": "bar.energy", "value": "1.0"}))
    assert node.delay_commands == []
    universe = _compile(CONFIGS / "test" / "effects_smoke", "L0_effects")
    restored = CompiledUniverse.from_dict(json.loads(json.dumps(universe.to_dict())))
    assert restored.compiled_effect_catalog == universe.compiled_effect_catalog


# --- 14. affordances_hash and items_hash are content, not text --------------------------------


def _level_hash(pack: Path, level: str) -> str:
    return _compile(pack, level).get_level(level).affordances_hash


def test_respacing_an_interaction_expression_does_not_move_affordances_hash(tmp_path: Path) -> None:
    base = _level_hash(_pack(tmp_path, SEA, "base"), SEA_LEVEL)
    respelled = _pack(tmp_path, SEA, "respelled")
    _edit(respelled / "levels" / SEA_LEVEL / "affordances.yaml", "value: bar.energy + 0.8", "value: bar.energy+0.8")
    assert _level_hash(respelled, SEA_LEVEL) == base
    changed = _pack(tmp_path, SEA, "changed")
    _edit(changed / "levels" / SEA_LEVEL / "affordances.yaml", "value: bar.energy + 0.8", "value: bar.energy + 0.9")
    assert _level_hash(changed, SEA_LEVEL) != base


def test_reordering_a_costs_mapping_does_not_move_affordances_hash(tmp_path: Path) -> None:
    level = "L1_full_observability"
    base_pack = _pack(tmp_path, CONFIGS / "default_curriculum", "base")
    path = base_pack / "levels" / level / "affordances.yaml"
    payload = yaml.safe_load(path.read_text())
    affordance = next(entry for entry in payload["affordances"]["affordances"] if len(entry["costs"]) >= 2)
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    base = _level_hash(base_pack, level)

    reordered_pack = _pack(tmp_path, base_pack, "reordered")
    affordance["costs"] = dict(reversed(list(affordance["costs"].items())))
    (reordered_pack / "levels" / level / "affordances.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))
    assert _level_hash(reordered_pack, level) == base


def test_respacing_an_item_hook_expression_does_not_move_items_hash(tmp_path: Path) -> None:
    source, level = CONFIGS / "test" / "items_smoke", "L0_smoke"
    base = _compile(_pack(tmp_path, source, "base"), level).items_hash
    assert base is not None
    respelled = _pack(tmp_path, source, "respelled")
    _edit(respelled / "items.yaml", "value: bar.energy + 0.3", "value: bar.energy+0.3")
    assert _compile(respelled, level).items_hash == base
    changed = _pack(tmp_path, source, "changed")
    _edit(changed / "items.yaml", "value: bar.energy + 0.3", "value: bar.energy + 0.4")
    assert _compile(changed, level).items_hash != base
