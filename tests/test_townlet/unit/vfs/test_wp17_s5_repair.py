"""WP17 S5 repair pass (verify_B4): reserved names, per-profile item state, read-only tick,
reference compositions, delay on a timeless substrate, and command-level refusal lines.

Each test reproduces one verifier probe (`verify_B4/probes/c_runtime.py`, `add_ref.py`,
`f_follow.py`, `r_refusals.py`) and pins the compile-time refusal or the corrected runtime.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError
from townlet.vfs.namespace import (
    ANY_ITEM,
    EFFECT_LOCALS,
    EFFECT_PIPELINE,
    ENGINE_AGENT_ID,
    ENGINE_TICK,
    INTERACTION_PIPELINE,
    RESERVED_NAMES,
    TRANSITION_WRITE,
    ItemBinding,
    Namespace,
    SpellingError,
    SymbolKind,
)
from townlet.world.expression.references import ENTITY_NAMES

CONFIGS = Path(__file__).resolve().parents[4] / "configs"
WITNESS = CONFIGS / "static_epistemic_access"
LEVEL = "L0_simple"
ITEMS = CONFIGS / "test" / "items_smoke"
ITEMS_LEVEL = "L0_smoke"


def _yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _dump(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _decl(var_id: str, *, scope: str = "agent", type: str = "scalar", **extra: object) -> dict:
    declaration: dict[str, object] = {
        "id": var_id,
        "scope": scope,
        "type": type,
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": [],
        "initial_value": -1 if type.endswith("_ref") else 0.0,
    }
    declaration.update(extra)
    return declaration


def _write(variable_id: str, expression: str, *, composition: str = "overwrite") -> dict:
    return {
        "variable_id": variable_id,
        "expression": expression,
        "condition": None,
        "composition": composition,
        "phase": "apply_completion_bonuses",
        "priority": 0,
        "clamp": None,
        "telemetry_label": "w",
    }


def _rule(variable_id: str, expression: str, *, composition: str = "overwrite") -> dict:
    write = {"variable_id": variable_id, "expression": expression, "composition": composition}
    write.update({"condition": None, "clamp": None, "effect": None})
    return {"id": "r", "phase": "apply_transition_rules", "condition": None, "writes": [write]}


def _effect(on_tick: list[dict], *, scope: str = "agent") -> dict:
    return {
        "id": "e1",
        "scope": scope,
        "duration": 5,
        "reapply_policy": "renew",
        "observable": False,
        "on_spawn": [],
        "on_tick": on_tick,
        "on_despawn": [],
        "on_interrupt": [],
    }


def _pack(
    tmp_path: Path,
    *,
    declarations: list[dict] | None = None,
    writes: list[dict] | None = None,
    rules: list[dict] | None = None,
    effects: list[dict] | None = None,
    sleep_on_start: list[dict] | None = None,
    name: str = "pack",
) -> Path:
    pack = tmp_path / name
    shutil.copytree(WITNESS, pack, ignore=shutil.ignore_patterns(".compiled"))
    if declarations:
        variables = _yaml(pack / "variables.yaml")
        variables["variables"]["declarations"] += declarations
        _dump(pack / "variables.yaml", variables)
    if writes is not None:
        actions = _yaml(pack / "actions.yaml")
        advance = next(action for action in actions["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"] = writes
        _dump(pack / "actions.yaml", actions)
    if rules is not None:
        _dump(pack / "transition_rules.yaml", {"version": "1.0", "transition_rules": rules})
    if effects is not None:
        budget = {"global": 1, "agent": 1, "item": 1, "affordance": 0}
        _dump(pack / "effects.yaml", {"version": "1.0", "max_active_effects": budget, "effect_definitions": effects})
    if sleep_on_start is not None:
        path = pack / "levels" / LEVEL / "affordances.yaml"
        affordances = _yaml(path)
        sleep = next(a for a in affordances["affordances"]["affordances"] if a["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = sleep_on_start
        _dump(path, affordances)
    return pack


def _compile(pack: Path, level: str = LEVEL) -> CompiledUniverse:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _refusal(pack: Path, level: str = LEVEL) -> CompilationError:
    with pytest.raises(CompilationError) as caught:
        _compile(pack, level)
    return caught.value


def _line_of(path: Path, needle: str, *, occurrence: int = 1) -> int:
    seen = 0
    for number, text in enumerate(path.read_text().splitlines(), 1):
        if needle in text:
            seen += 1
            if seen == occurrence:
                return number
    raise AssertionError(f"{needle!r} not in {path}")


# -- P1-a: reserved names --------------------------------------------------------------


def test_the_reserved_set_is_derived_from_the_engine_names_and_effect_locals() -> None:
    assert RESERVED_NAMES == {ENGINE_TICK, *TRANSITION_WRITE.engine, *EFFECT_LOCALS, *ENTITY_NAMES}
    assert ENGINE_AGENT_ID in RESERVED_NAMES


@pytest.mark.parametrize("reserved", sorted(RESERVED_NAMES))
def test_a_variable_taking_a_reserved_name_refuses_at_its_declaration_line(tmp_path: Path, reserved: str) -> None:
    pack = _pack(tmp_path, declarations=[_decl(reserved, scope="global")])
    refusal = _refusal(pack)
    assert f"Variable id '{reserved}' is reserved" in str(refusal)
    (issue,) = refusal.issues
    assert issue.location == f"{pack / 'variables.yaml'}:{_line_of(pack / 'variables.yaml', f'id: {reserved}')}"


def test_item_state_may_reuse_a_reserved_name(tmp_path: Path) -> None:
    """`item.intensity` is a qualified reference: an item variable never collides with a bare name."""
    pack = tmp_path / "items"
    shutil.copytree(ITEMS, pack, ignore=shutil.ignore_patterns(".compiled"))
    variables = _yaml(pack / "variables.yaml")
    variables["variables"]["declarations"].append(_decl("intensity", scope="item", profile="food"))
    _dump(pack / "variables.yaml", variables)
    _compile(pack, ITEMS_LEVEL)


def test_the_namespace_refuses_a_reserved_variable_id() -> None:
    with pytest.raises(ValueError, match="reserved"):
        Namespace(variables=[("intensity", "agent", "scalar")], meters=[], item_profiles={})


@pytest.mark.parametrize("entity", sorted(ENTITY_NAMES))
def test_an_agent_ref_named_after_an_entity_refuses_at_its_declaration_line(tmp_path: Path, entity: str) -> None:
    """`self` / `target` name the context's entities (`spawn_effect: e1, target: target`); a variable may not take them."""
    pack = _pack(tmp_path, declarations=[_decl(entity, scope="agent", type="agent_ref")])
    refusal = _refusal(pack)
    (issue,) = refusal.issues
    assert f"Variable id '{entity}' is reserved" in issue.message
    assert issue.location == f"{pack / 'variables.yaml'}:{_line_of(pack / 'variables.yaml', f'id: {entity}')}"


def test_no_shipped_pack_declares_a_reserved_variable_id() -> None:
    declared: list[tuple[Path, str]] = []
    for path in sorted(CONFIGS.rglob("*.y*ml")):
        if ".compiled" in path.parts:
            continue
        for document in yaml.safe_load_all(path.read_text()):
            variables = document.get("variables") if isinstance(document, dict) else None
            if not isinstance(variables, dict):
                continue
            for declaration in variables.get("declarations", []) or []:
                if isinstance(declaration, dict) and declaration.get("scope") != "item" and declaration.get("id") in RESERVED_NAMES:
                    declared.append((path, declaration["id"]))
    assert declared == []


# -- P1-b: item state is the bound item's profile ----------------------------------------


def _items_pack(tmp_path: Path, apple_on_pickup: list[dict], *, effects: list[dict] | None = None) -> Path:
    pack = tmp_path / "items"
    shutil.copytree(ITEMS, pack, ignore=shutil.ignore_patterns(".compiled"))
    items = _yaml(pack / "items.yaml")
    apple = next(item for item in items["items"]["item_types"] if item["id"] == "apple")
    apple["interactions"]["on_pickup"] = apple_on_pickup
    _dump(pack / "items.yaml", items)
    if effects is not None:
        payload = _yaml(pack / "effects.yaml")
        payload["effect_definitions"] = effects
        _dump(pack / "effects.yaml", payload)
    return pack


@pytest.mark.parametrize(
    "command",
    [
        {"modify": "bar.energy", "value": "bar.energy + item.durability * 0.001"},
        {"modify": "item.durability", "value": "1.0"},
    ],
    ids=["read", "write"],
)
def test_a_hook_naming_another_profiles_state_refuses_at_the_command_line(tmp_path: Path, command: dict) -> None:
    """r c6: an apple (profile food) hook naming medical-only `durability` compiled and crashed with KeyError."""
    pack = _items_pack(tmp_path, [command])
    refusal = _refusal(pack, ITEMS_LEVEL)
    (issue,) = refusal.issues
    assert "the bound item's profile (food) does not declare (declared by item profile(s) medical)" in issue.message
    on_pickup = _line_of(pack / "items.yaml", "on_pickup:")
    assert issue.location is not None and int(issue.location.rsplit(":", 1)[1]) > on_pickup


def test_a_hook_reads_its_own_profiles_state(tmp_path: Path) -> None:
    _compile(_items_pack(tmp_path, [{"modify": "item.freshness", "value": "item.freshness - 1.0"}]), ITEMS_LEVEL)


def test_an_item_scoped_effect_reads_only_state_every_profile_declares(tmp_path: Path) -> None:
    """An item-scoped effect's item is chosen at run time: the intersection of the profiles is readable."""
    shared = _items_pack(tmp_path, [], effects=[_effect([{"modify": "item.condition", "value": "item.condition - 1.0"}], scope="item")])
    _compile(shared, ITEMS_LEVEL)
    shutil.rmtree(tmp_path / "items")
    partial = _items_pack(tmp_path, [], effects=[_effect([{"modify": "item.durability", "value": "1.0"}], scope="item")])
    assert "every item profile declares" in str(_refusal(partial, ITEMS_LEVEL))


def test_the_item_binding_is_the_intersection_with_one_type() -> None:
    namespace = Namespace(
        variables=[],
        meters=[],
        item_profiles={"a": {"x": "scalar", "y": "scalar", "z": "scalar"}, "b": {"x": "scalar", "y": "bool"}},
    )
    assert set(namespace.item_state(ANY_ITEM)) == {"x"}
    assert set(namespace.item_state(ItemBinding.of_profile("a"))) == {"x", "y", "z"}
    assert "item.z" not in namespace.schema(EFFECT_PIPELINE.with_item(ANY_ITEM))


# -- P2-a: tick is a read-only engine name -----------------------------------------------


def test_tick_resolves_as_the_engine_name_in_every_context() -> None:
    namespace = Namespace(variables=[("tick", "global", "scalar")], meters=[], item_profiles={})
    for context in (TRANSITION_WRITE, INTERACTION_PIPELINE, EFFECT_PIPELINE):
        assert namespace.resolve("tick", context).kind == SymbolKind.ENGINE
        with pytest.raises(SpellingError, match="'tick', the engine name, which is no state a write can change"):
            namespace.resolve_write("tick", context)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"effects": [_effect([{"modify": "tick", "value": "999.0"}])]},
        {"effects": [_effect([{"modify": "tick", "value": "999.0"}], scope="global")]},
        {"rules": [_rule("tick", "1.0")]},
        {"sleep_on_start": [{"modify": "tick", "value": "1.0"}]},
    ],
    ids=["agent_effect", "global_effect", "rule", "interaction"],
)
def test_writing_tick_refuses_in_every_consumer_with_the_engine_name_message(tmp_path: Path, kwargs: dict) -> None:
    assert "'tick', the engine name, which is no state a write can change" in str(_refusal(_pack(tmp_path, **kwargs)))


def test_agent_id_as_a_target_refuses_with_the_same_message(tmp_path: Path) -> None:
    refusal = _refusal(_pack(tmp_path, writes=[_write("agent_id", "1")]))
    assert "'agent_id', the engine name, which is no state a write can change" in str(refusal)


# -- P2-b: a reference composes by replacement only --------------------------------------


@pytest.mark.parametrize("composition", ["additive_delta", "multiplicative_modifier", "min", "max"])
@pytest.mark.parametrize("consumer", ["write", "rule"])
def test_a_reference_target_refuses_arithmetic_compositions(tmp_path: Path, composition: str, consumer: str) -> None:
    declarations = [_decl("aref", type="agent_ref")]
    if consumer == "write":
        pack = _pack(tmp_path, declarations=declarations, writes=[_write("aref", "agent_id", composition=composition)])
    else:
        pack = _pack(tmp_path, declarations=declarations, rules=[_rule("aref", "-1", composition=composition)])
    assert f"composes '{composition}' into agent_ref 'aref'" in str(_refusal(pack))


def test_a_reference_target_overwrites(tmp_path: Path) -> None:
    _compile(_pack(tmp_path, declarations=[_decl("aref", type="agent_ref")], writes=[_write("aref", "agent_id")]))


# -- P2-c: delay needs a substrate that keeps time ---------------------------------------


def test_delay_in_an_interaction_refuses_on_a_timeless_substrate(tmp_path: Path) -> None:
    pack = _pack(tmp_path, sleep_on_start=[{"delay": "2", "do": [{"modify": "public_state", "value": "public_state + 5.0"}]}])
    refusal = _refusal(pack)
    assert "delay command not allowed when time is disabled" in str(refusal)
    (issue,) = refusal.issues
    assert issue.location.endswith(f"affordances.yaml:{_line_of(pack / 'levels' / LEVEL / 'affordances.yaml', 'delay:')}")


def test_delay_in_an_item_hook_refuses_on_a_timeless_substrate(tmp_path: Path) -> None:
    stratum = _yaml(ITEMS / "stratum.yaml")
    assert stratum["stratum"]["temporal_support"] != "enabled"
    pack = _items_pack(tmp_path, [{"delay": "1", "do": [{"modify": "bar.energy", "value": "bar.energy + 0.1"}]}])
    assert "delay command not allowed when time is disabled" in str(_refusal(pack, ITEMS_LEVEL))


# -- P3: refusal lines and the bare meter target -------------------------------------------


def test_a_nested_interaction_refusal_cites_the_nested_command(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path,
        sleep_on_start=[
            {"modify": "bar.energy", "value": "bar.energy + 0.1"},
            {"if": "bar.energy > 0.5", "then": [{"modify": "public_state", "value": "vfs.public_state + 1.0"}], "else": []},
        ],
    )
    (issue,) = _refusal(pack).issues
    assert "write 'public_state'" in issue.message and "on_start[1].then[0]" in issue.message
    affordances = pack / "levels" / LEVEL / "affordances.yaml"
    assert issue.location == f"{affordances}:{_line_of(affordances, 'modify: public_state')}"


def test_an_effect_refusal_cites_the_command(tmp_path: Path) -> None:
    pack = _pack(
        tmp_path, effects=[_effect([{"modify": "bar.energy", "value": "0.5"}, {"modify": "public_state", "value": "vfs.public_state"}])]
    )
    (issue,) = _refusal(pack).issues
    assert "on_tick[1]" in issue.message
    assert issue.location == f"{pack / 'effects.yaml'}:{_line_of(pack / 'effects.yaml', 'modify: public_state')}"


def test_a_bare_meter_interaction_target_names_the_meter_spelling(tmp_path: Path) -> None:
    pack = _pack(tmp_path, sleep_on_start=[{"modify": "energy", "value": "1.0"}])
    assert "write 'bar.energy'" in str(_refusal(pack))
