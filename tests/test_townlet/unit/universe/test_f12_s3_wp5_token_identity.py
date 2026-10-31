"""Token-spec refusals are located, coded compile diagnostics; identity is gated on the brain.

VFS round-2 F12 (`r10_indistinguishable.py`): token-spec refusals used to leave the compiler
as bare ``ValueError``s with no code, stage or ``file:line``. S3: the indistinguishability
rule refused two parameter-identical exposed variables for every brain, although only a
permutation-invariant token encoder (``token_set``, ``recurrent`` — both pool through
``TokenSetEncoder``) cannot tell such tokens apart; a flat brain reads slots by position.
Compiler WP5 (C8, effects F15): the same check now covers affordances and catalogued effects.
"""

from __future__ import annotations

import copy
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml

from townlet.config.brain_config import BrainConfig
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.compilers.observation import reads_tokens_as_a_set
from townlet.universe.errors import CompilationError

WITNESS_PACK = Path("configs/static_epistemic_access")  # dueling brain, 8x8 grid: the r10 witness
ASPATIAL_PACK = Path("configs/aspatial_test")  # feedforward brain, no position lanes
TOKEN_BRAIN = Path("configs/test/token_set_smoke/brain.yaml")  # token_set, mean aggregator
LEVEL = "L0_simple"
ASPATIAL_LEVEL = "L0"

MINMAX = {"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True}


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def _dump(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _edit(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    payload = _load(path)
    mutate(payload)
    _dump(path, payload)


def _pack(tmp_path: Path, *, token_brain: bool, base: Path = WITNESS_PACK) -> Path:
    dest = tmp_path / ("token_brain" if token_brain else "flat_brain")
    shutil.copytree(base, dest, ignore=shutil.ignore_patterns(".compiled"))
    if token_brain:
        shutil.copyfile(TOKEN_BRAIN, dest / "brain.yaml")
    return dest


def _declaration(var_id: str) -> dict[str, Any]:
    return {
        "id": var_id,
        "scope": "agent",
        "type": "scalar",
        "lifetime": "episode",
        "semantic_type": "custom",
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "exposed_to": ["agent"],
        "initial_value": 0.0,
        "normalization": dict(MINMAX),
    }


def _twin_variables(pack: Path) -> None:
    """r10: hunger and thirst, equal in every declared parameter, driven by different writes."""

    def add(payload: dict[str, Any]) -> None:
        payload["variables"]["declarations"].extend([_declaration("hunger"), _declaration("thirst")])

    _edit(pack / "variables.yaml", add)

    def writes(payload: dict[str, Any]) -> None:
        advance = next(action for action in payload["actions"]["custom_actions"] if action["name"] == "ADVANCE")
        advance["writes"] = [
            {
                "variable_id": var_id,
                "expression": expr,
                "condition": None,
                "composition": "additive_delta",
                "phase": "apply_completion_bonuses",
                "priority": 0,
                "clamp": None,
                "telemetry_label": f"w_{var_id}",
            }
            for var_id, expr in (("hunger", "0.1"), ("thirst", "0.3"))
        ]

    _edit(pack / "actions.yaml", writes)


def _twin_affordances(pack: Path, *, level: str = LEVEL, original: str = "SLEEP", twin_name: str = "NAP", enable: bool = True) -> None:
    """A second affordance identical to ``original`` in interaction type, duration, hours and meter writes."""

    def add(payload: dict[str, Any]) -> None:
        affordances = payload["affordances"]["affordances"]
        source = next(entry for entry in affordances if entry["name"] == original)
        twin = copy.deepcopy(source)
        twin["name"] = twin_name
        if twin["deployment"]["positions"]:
            twin["deployment"]["positions"] = [[6, 6]]
        affordances.append(twin)

    _edit(pack / "levels" / level / "affordances.yaml", add)

    def declare(payload: dict[str, Any]) -> None:
        payload["environment"]["affordances"].append({"name": twin_name})

    _edit(pack / "environment.yaml", declare)

    if enable:

        def deploy(payload: dict[str, Any]) -> None:
            payload["training"]["enabled_affordances"].append(twin_name)

        _edit(pack / "levels" / level / "training.yaml", deploy)


def _effect(effect_id: str, *, observable: bool = True) -> dict[str, Any]:
    return {
        "id": effect_id,
        "scope": "agent",
        "duration": 20,
        "reapply_policy": "renew",
        "observable": observable,
        "on_spawn": [],
        "on_tick": [{"modify": "bar.energy", "value": "bar.energy + (0.05 * intensity)"}],
        "on_despawn": [],
        "on_interrupt": [],
    }


def _twin_effects(pack: Path, *, observable: bool = True) -> None:
    """Two catalogued effects identical in scope, duration and reapply policy."""

    def add(payload: dict[str, Any]) -> None:
        payload["effect_definitions"] = [_effect("regen", observable=observable), _effect("second_wind", observable=observable)]
        payload["max_active_effects"] = {"global": 0, "agent": 2, "item": 0, "affordance": 0}

    _edit(pack / "effects.yaml", add)


def _compile(pack: Path, *, level: str = LEVEL) -> Any:
    return UniverseCompiler().compile(pack, primary_level=level, use_cache=False)


def _refusal(pack: Path, *, level: str = LEVEL) -> str:
    with pytest.raises(CompilationError) as excinfo:
        _compile(pack, level=level)
    assert excinfo.value.stage.startswith("Stage 7"), excinfo.value.stage
    return str(excinfo.value)


def _line_of(path: Path, needle: str) -> int:
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if needle in line:
            return number
    raise AssertionError(f"{needle!r} not in {path}")


# --------------------------------------------------------------------------- S3 + F12: variables


def test_r10_twin_variables_refuse_under_a_token_brain_with_code_and_both_locations(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=True)
    _twin_variables(pack)
    message = _refusal(pack)
    variables_yaml = pack / "variables.yaml"
    thirst_line = _line_of(variables_yaml, "id: thirst")
    hunger_line = _line_of(variables_yaml, "id: hunger")

    assert "[TOKEN-IDENTITY]" in message
    assert f"variables.yaml:{thirst_line} - Variable 'hunger' and Variable 'thirst'" in message
    assert f"Variable 'hunger' is declared at {variables_yaml}:{hunger_line}" in message
    # The message says what the encoder sees and why only a set-pooling brain cares; it
    # never tells the author to change a behavioural parameter to satisfy the compiler.
    assert "permutation-invariant" in message
    assert "scope, semantic type, normalization kind and bounds" in message
    assert "feedforward, dueling" in message
    assert "Add a distinguishing" not in message


def test_r10_twin_variables_compile_under_a_flat_brain(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=False)
    assert BrainConfig.model_validate(_load(pack / "brain.yaml")).architecture.type == "dueling"
    _twin_variables(pack)
    universe = _compile(pack)
    level = universe.get_level(LEVEL)
    refs = [binding.filler_ref for binding in level.token_spec.get_type("variable_element").slot_bindings]
    assert "hunger" in refs and "thirst" in refs


def test_r10_twin_variables_compile_under_a_token_brain_once_one_parameter_differs(tmp_path: Path) -> None:
    # Not an escape hatch the message recommends — a check that the refusal is about the
    # declared identity, not about the pair of names.
    pack = _pack(tmp_path, token_brain=True)
    _twin_variables(pack)

    def retype(payload: dict[str, Any]) -> None:
        thirst = next(entry for entry in payload["variables"]["declarations"] if entry["id"] == "thirst")
        thirst["lifetime"] = "tick"

    _edit(pack / "variables.yaml", retype)
    _compile(pack)


@pytest.mark.parametrize(
    ("architecture", "expected"),
    [("feedforward", False), ("dueling", False), ("token_set", True), ("recurrent", True)],
)
def test_permutation_invariant_gate_follows_the_architecture_type(architecture: str, expected: bool) -> None:
    payload = _load(TOKEN_BRAIN)
    stream = {"hidden_layers": [32], "activation": "relu"}
    architectures: dict[str, dict[str, Any]] = {
        "feedforward": {"hidden_layers": [32], "activation": "relu", "dropout": 0.0, "layer_norm": False},
        "dueling": {
            "shared_layers": [32],
            "value_stream": stream,
            "advantage_stream": stream,
            "activation": "relu",
            "dropout": 0.0,
            "layer_norm": False,
        },
        "token_set": {"token_embed_dim": 16, "q_head_hidden_dim": 32, "aggregator": {"type": "mean"}},
        "recurrent": {
            "token_embed_dim": 16,
            "aggregator": {"type": "mean"},
            "lstm": {"hidden_size": 32, "num_layers": 1, "dropout": 0.0},
            "q_head_hidden_dim": 32,
        },
    }
    payload["architecture"] = {"type": architecture, architecture: architectures[architecture]}
    brain = BrainConfig.model_validate(payload)
    assert reads_tokens_as_a_set(brain) is expected


# --------------------------------------------------------------------------- WP5: affordances and effects


def test_twin_affordances_on_a_grid_compile_under_a_token_brain(tmp_path: Path) -> None:
    # Two beds at different positions differ in the affordance token's position and
    # egocentric lanes every episode, under fixed and random deployment alike: the set
    # encoder can tell them apart, so the identity check does not apply on a spatial substrate.
    pack = _pack(tmp_path, token_brain=True)
    _twin_affordances(pack)
    universe = _compile(pack)
    level = universe.get_level(LEVEL)
    assert level.token_spec.position_rank > 0
    refs = [binding.filler_ref for binding in level.token_spec.get_type("affordance").slot_bindings]
    assert "SLEEP" in refs and "NAP" in refs


def test_twin_affordances_on_an_aspatial_substrate_refuse_under_a_token_brain(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=True, base=ASPATIAL_PACK)
    _twin_affordances(pack, level=ASPATIAL_LEVEL, original="Bed", twin_name="Cot")
    message = _refusal(pack, level=ASPATIAL_LEVEL)
    affordances_yaml = pack / "levels" / ASPATIAL_LEVEL / "affordances.yaml"

    assert "[TOKEN-IDENTITY]" in message
    assert f"affordances.yaml:{_line_of(affordances_yaml, 'name: Cot')} - Affordance 'Bed' and Affordance 'Cot'" in message
    assert f"Affordance 'Bed' is declared at {affordances_yaml}:{_line_of(affordances_yaml, 'name: Bed')}" in message
    assert "interaction type, duration, opening hours and the reachable meter writes" in message
    assert "no position lanes" in message


def test_twin_affordances_on_an_aspatial_substrate_compile_when_the_twin_is_not_deployed(tmp_path: Path) -> None:
    # An affordance outside enabled_affordances publishes presence 0 forever: padding, not a twin.
    pack = _pack(tmp_path, token_brain=True, base=ASPATIAL_PACK)
    _twin_affordances(pack, level=ASPATIAL_LEVEL, original="Bed", twin_name="Cot", enable=False)
    universe = _compile(pack, level=ASPATIAL_LEVEL)
    assert "Cot" not in universe.get_level(ASPATIAL_LEVEL).training.enabled_affordances


def test_twin_affordances_on_an_aspatial_substrate_compile_under_a_flat_brain(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=False, base=ASPATIAL_PACK)
    _twin_affordances(pack, level=ASPATIAL_LEVEL, original="Bed", twin_name="Cot")
    universe = _compile(pack, level=ASPATIAL_LEVEL)
    refs = [binding.filler_ref for binding in universe.get_level(ASPATIAL_LEVEL).token_spec.get_type("affordance").slot_bindings]
    assert refs == ["Bed", "Cot"]


def test_twin_effects_refuse_under_a_token_brain_located_in_the_effects_declaration(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=True)
    _twin_effects(pack)
    message = _refusal(pack)
    effects_yaml = pack / "effects.yaml"

    assert "[TOKEN-IDENTITY]" in message
    assert f"effects.yaml:{_line_of(effects_yaml, 'id: second_wind')} - Effect 'regen' and Effect 'second_wind'" in message
    assert f"Effect 'regen' is declared at {effects_yaml}:{_line_of(effects_yaml, 'id: regen')}" in message
    assert "scope, duration and reapply policy, not what the effect writes" in message
    # Effect slots are bound dynamically: the message must not claim a flat brain reads them apart by position.
    assert "by position" not in message


def test_unobservable_twin_effects_compile_under_a_token_brain(tmp_path: Path) -> None:
    # observable: false effects are never published, so no token exists to alias.
    pack = _pack(tmp_path, token_brain=True)
    _twin_effects(pack, observable=False)
    _compile(pack)


def test_twin_effects_compile_under_a_flat_brain(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=False)
    _twin_effects(pack)
    universe = _compile(pack)
    contexts = universe.get_level(LEVEL).token_spec.get_type("effect").effect_catalog_contexts
    assert [context.context_ref for context in contexts] == ["effect:regen", "effect:second_wind"]


# --------------------------------------------------------------------------- F12: every token-spec refusal is located


@pytest.mark.parametrize(
    ("label", "normalization", "fragment"),
    [
        ("unclipped_range", {"kind": "minmax", "min": 0.0, "max": 4.0, "clip": False}, "bounded normalization kind"),
        ("one_hot", {"kind": "one_hot", "categories": 4}, "one_hot is refused on tokenized variables"),
        ("rank_scaled", {"kind": "rank_scaled"}, "rank_scaled is refused"),
    ],
)
def test_exposure_refusals_carry_code_and_the_variable_line(
    tmp_path: Path, label: str, normalization: dict[str, Any], fragment: str
) -> None:
    pack = _pack(tmp_path, token_brain=False)

    def mutate(payload: dict[str, Any]) -> None:
        payload["variables"]["declarations"][0]["normalization"] = normalization

    _edit(pack / "variables.yaml", mutate)
    message = _refusal(pack)
    variables_yaml = pack / "variables.yaml"
    assert "[TOKEN-EXPOSURE]" in message, label
    assert f"{variables_yaml}:{_line_of(variables_yaml, 'id: public_state')} - Variable 'public_state'" in message
    assert fragment in message


def test_exposed_item_variable_without_item_capacity_is_a_located_capacity_refusal(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=False)

    def mutate(payload: dict[str, Any]) -> None:
        payload["variables"]["item_profiles"] = ["food"]
        payload["variables"]["declarations"].append(
            {
                "id": "freshness",
                "scope": "item",
                "profile": "food",
                "type": "scalar",
                "lifetime": "episode",
                "semantic_type": "custom",
                "readable_by": ["engine", "agent"],
                "writable_by": ["engine"],
                "exposed_to": ["agent"],
                "initial_value": 1.0,
                "normalization": dict(MINMAX),
            }
        )

    _edit(pack / "variables.yaml", mutate)
    message = _refusal(pack)
    variables_yaml = pack / "variables.yaml"
    assert "[TOKEN-CAPACITY]" in message
    assert f"{variables_yaml}:{_line_of(variables_yaml, 'id: freshness')} - Item-profile variable(s) food.freshness" in message
    assert re.search(r"`item` token capacity is 0", message)


def test_affordance_identity_extraction_refusal_is_located_at_the_affordance(tmp_path: Path) -> None:
    pack = _pack(tmp_path, token_brain=False)
    _twin_effects(pack)

    def mutate(payload: dict[str, Any]) -> None:
        sleep = next(entry for entry in payload["affordances"]["affordances"] if entry["name"] == "SLEEP")
        sleep["interactions"]["on_start"] = [{"spawn_effect": "regen", "target": "self", "intensity": 1.0}]

    affordances_yaml = pack / "levels" / LEVEL / "affordances.yaml"
    _edit(affordances_yaml, mutate)
    message = _refusal(pack)
    assert "[TOKEN-SPEC]" in message
    assert f"{affordances_yaml}:{_line_of(affordances_yaml, 'name: SLEEP')} - Affordance 'SLEEP'" in message
    assert "spawn_effect target" in message
