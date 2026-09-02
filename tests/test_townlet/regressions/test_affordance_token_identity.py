"""Regressions for compiler-owned affordance token identity."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from townlet.effects.affordance_identity import (
    extract_affordance_meter_writes,
)
from townlet.numeric import require_float32
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto.token_spec import (
    AFFORDANCE_DURATION_FEATURES,
    AFFORDANCE_EFFECT_ENTRY_WIDTH,
    AFFORDANCE_EFFECT_MAGNITUDE_OFFSET,
    AFFORDANCE_EFFECT_METER_OFFSET,
    EFFECT_SUMMARY_K,
    INTERACTION_TYPE_VOCABULARY,
    OPENING_HOURS_FEATURES,
    affordance_signature,
    meter_signature,
)

REFERENCE_PACK = Path("configs/reference/model_pack")
LEVEL = "L0_demo"


def _copy_reference_pack(tmp_path: Path, name: str = "pack") -> Path:
    pack = tmp_path / name
    shutil.copytree(REFERENCE_PACK, pack)
    return pack


def _affordance_payload(pack: Path, name: str) -> tuple[Path, dict, dict]:
    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    payload = yaml.safe_load(affordances_path.read_text())
    affordance = next(entry for entry in payload["affordances"]["affordances"] if entry["name"] == name)
    return affordances_path, payload, affordance


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False))


def _compiled_affordance_signature(pack: Path, name: str) -> tuple[tuple[float, ...], str]:
    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    level = compiled.get_level(LEVEL)
    return _affordance_context_signature(level, name), level.observation_schema_hash


def _affordance_context_signature(level, name: str) -> tuple[float, ...]:
    schema = level.token_spec.get_type("affordance")
    assert schema is not None
    binding = next(binding for binding in schema.slot_bindings if binding.filler_ref == name)
    payload = schema.slot_context_payloads[binding.slot_index]
    position_start = schema.payload_features.index("position_0")
    effect_start = schema.payload_features.index("effect_0_form")
    return payload[:position_start] + payload[effect_start:]


def _effect_blocks(signature: tuple[float, ...]) -> tuple[tuple[float, ...], ...]:
    start = len(INTERACTION_TYPE_VOCABULARY) + len(AFFORDANCE_DURATION_FEATURES) + len(OPENING_HOURS_FEATURES)
    return tuple(
        signature[start + index * AFFORDANCE_EFFECT_ENTRY_WIDTH : start + (index + 1) * AFFORDANCE_EFFECT_ENTRY_WIDTH]
        for index in range(EFFECT_SUMMARY_K)
    )


def _effect_value_indices() -> tuple[int, int, int]:
    return AFFORDANCE_EFFECT_MAGNITUDE_OFFSET, AFFORDANCE_EFFECT_MAGNITUDE_OFFSET + 1, AFFORDANCE_EFFECT_METER_OFFSET


@pytest.fixture(scope="module")
def reference_universe():
    return UniverseCompiler().compile(REFERENCE_PACK, primary_level=LEVEL, use_cache=False)


@pytest.mark.parametrize(
    ("affordance_name", "expected_deltas"),
    (
        pytest.param(
            "EAT",
            (
                ("cost", "on_start", "energy", require_float32(-0.05, field="expected delta")),
                ("interaction", "on_start", "mood", require_float32(0.05, field="expected delta")),
                ("interaction", "on_start", "energy", require_float32(0.2, field="expected delta")),
            ),
            id="on-start",
        ),
        pytest.param(
            "SLEEP",
            (
                ("cost_per_tick", "per_tick", "energy", require_float32(-0.005, field="expected delta")),
                ("interaction", "per_tick", "energy", require_float32(0.1, field="expected delta")),
            ),
            id="per-tick",
        ),
        pytest.param(
            "WORK",
            (
                ("cost_per_tick", "per_tick", "energy", require_float32(-0.05, field="expected delta")),
                ("interaction", "per_tick", "energy", require_float32(-0.01, field="expected delta")),
                ("interaction", "per_tick", "mood", require_float32(0.05, field="expected delta")),
            ),
            id="negative-per-tick",
        ),
    ),
)
def test_compiled_affordance_identity_uses_all_executable_lifecycle_deltas(
    reference_universe,
    affordance_name: str,
    expected_deltas: tuple[tuple[str, str, str, float], ...],
) -> None:
    level = reference_universe.get_level(LEVEL)
    metadata = next(affordance for affordance in level.affordance_metadata.affordances if affordance.id == affordance_name)
    declarations = level.meter_declarations
    meters = {meter.name: meter for meter in declarations}
    affordance = next(affordance for affordance in level.affordances.affordances if affordance.name == affordance_name)
    writes = extract_affordance_meter_writes(affordance, effect_catalog=reference_universe.compiled_effect_catalog)

    assert not hasattr(metadata, "effects")
    assert tuple((write.source, write.stage, write.meter_name, write.delta) for write in writes) == expected_deltas
    expected_signature = affordance_signature(affordance=affordance, effect_deltas=writes, meters=meters)
    assert _affordance_context_signature(level, affordance_name) == tuple(
        require_float32(value, field="expected affordance signature") for value in expected_signature
    )


def test_non_affine_meter_interaction_keeps_dynamic_target_identity(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    shutil.copytree(REFERENCE_PACK, pack)
    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    payload = yaml.safe_load(affordances_path.read_text())
    eat = next(affordance for affordance in payload["affordances"]["affordances"] if affordance["name"] == "EAT")
    eat["interactions"]["on_start"][1]["value"] = "target.bar.energy * 2.0"
    affordances_path.write_text(yaml.safe_dump(payload, sort_keys=False))

    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    level = compiled.get_level(LEVEL)
    declarations = level.meter_declarations
    energy = next(meter for meter in declarations if meter.name == "energy")
    first_effect = _effect_blocks(_affordance_context_signature(level, "EAT"))[0]
    magnitude, sign, meter_start = _effect_value_indices()

    assert first_effect[0] == -1.0
    assert first_effect[magnitude : sign + 1] == (0.0, 0.0)
    assert first_effect[meter_start:] == pytest.approx(meter_signature(energy))


def test_repeated_opposite_deltas_remain_distinct_identity_declarations(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    shutil.copytree(REFERENCE_PACK, pack)
    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    payload = yaml.safe_load(affordances_path.read_text())
    eat = next(affordance for affordance in payload["affordances"]["affordances"] if affordance["name"] == "EAT")
    eat["interactions"]["on_start"] = [
        {"modify": "target.bar.energy", "value": "target.bar.energy + 0.1"},
        {"modify": "target.bar.energy", "value": "target.bar.energy - 0.1"},
    ]
    eat["interactions"]["on_completion"] = []
    affordances_path.write_text(yaml.safe_dump(payload, sort_keys=False))

    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    level = compiled.get_level(LEVEL)
    declarations = level.meter_declarations
    energy = next(meter for meter in declarations if meter.name == "energy")
    signature = _affordance_context_signature(level, "EAT")
    first_effect, second_effect, *_ = _effect_blocks(signature)
    magnitude, sign, meter_start = _effect_value_indices()

    assert (first_effect[0], first_effect[magnitude], first_effect[sign]) == (1.0, pytest.approx(0.1), 1.0)
    assert first_effect[meter_start:] == pytest.approx(meter_signature(energy))
    assert (second_effect[0], second_effect[magnitude], second_effect[sign]) == (1.0, pytest.approx(0.1), -1.0)
    assert second_effect[meter_start:] == pytest.approx(meter_signature(energy))
    assert signature[-1] == pytest.approx(3.0 / 4.0)


def test_mutually_exclusive_meter_writes_are_marked_dynamic_without_cancelling(tmp_path: Path) -> None:
    pack = tmp_path / "pack"
    shutil.copytree(REFERENCE_PACK, pack)
    affordances_path = pack / "levels" / LEVEL / "affordances.yaml"
    payload = yaml.safe_load(affordances_path.read_text())
    eat = next(affordance for affordance in payload["affordances"]["affordances"] if affordance["name"] == "EAT")
    eat["interactions"]["on_start"] = [
        {
            "if": "target.bar.energy > 0.5",
            "then": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.1"}],
            "else": [{"modify": "target.bar.energy", "value": "target.bar.energy - 0.1"}],
        }
    ]
    eat["interactions"]["on_completion"] = []
    affordances_path.write_text(yaml.safe_dump(payload, sort_keys=False))

    compiled = UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)
    level = compiled.get_level(LEVEL)
    writes = extract_affordance_meter_writes(
        next(affordance for affordance in level.affordances.affordances if affordance.name == "EAT"),
        effect_catalog=compiled.compiled_effect_catalog,
    )

    assert [(write.form, write.delta) for write in writes] == [
        (1, require_float32(-0.05, field="expected delta")),
        (-1, require_float32(0.1, field="expected delta")),
        (-1, require_float32(-0.1, field="expected delta")),
    ]
    assert _affordance_context_signature(level, "EAT")[-1] == pytest.approx(3.0 / 4.0)


def test_same_meter_delta_in_different_lifecycle_stage_changes_signature_and_hash(tmp_path: Path) -> None:
    signatures: list[tuple[tuple[float, ...], str]] = []
    for stage in ("per_tick", "on_completion"):
        pack = _copy_reference_pack(tmp_path, stage)
        path, payload, work = _affordance_payload(pack, "WORK")
        work["costs"] = {}
        work["costs_per_tick"] = {}
        for lifecycle_stage in work["interactions"]:
            work["interactions"][lifecycle_stage] = []
        work["interactions"][stage] = [
            {"modify": "target.bar.energy", "value": "target.bar.energy + 0.1"},
        ]
        _write_yaml(path, payload)
        signatures.append(_compiled_affordance_signature(pack, "WORK"))

    assert signatures[0][0] != signatures[1][0]
    assert signatures[0][1] != signatures[1][1]


def test_spawned_effect_meter_writes_are_included_from_compiled_catalog() -> None:
    compiled = UniverseCompiler().compile("configs/trial_k_cold", primary_level="L0_cold", use_cache=False)
    level = compiled.get_level("L0_cold")
    signature = _affordance_context_signature(level, "WINTER_ONSET")

    # winter has four recursively reachable target-bar writes (three cold_bite,
    # one comfort); none may disappear merely because the affordance uses spawn_effect.
    assert signature[-1] == pytest.approx(4.0 / 5.0)
    cold_bite = next(meter for meter in level.meter_declarations if meter.name == "cold_bite")
    comfort = next(meter for meter in level.meter_declarations if meter.name == "comfort")
    assert _contains_subsequence(signature, meter_signature(cold_bite))
    assert _contains_subsequence(signature, meter_signature(comfort))


@pytest.mark.parametrize("effect_ref", ("missing_effect", "ate_food"), ids=("missing", "cycle"))
def test_spawned_effect_missing_reference_or_cycle_refuses(tmp_path: Path, effect_ref: str) -> None:
    pack = _copy_reference_pack(tmp_path)
    path, payload, eat = _affordance_payload(pack, "EAT")
    eat["interactions"]["on_start"] = [{"spawn_effect": effect_ref, "target": "target", "intensity": 1.0}]
    eat["interactions"]["on_completion"] = []
    _write_yaml(path, payload)
    if effect_ref == "ate_food":
        effects_path = pack / "effects.yaml"
        effects_payload = yaml.safe_load(effects_path.read_text())
        effects_payload["effect_definitions"][0]["on_spawn"] = [{"spawn_effect": "ate_food", "target": "target", "intensity": 1.0}]
        _write_yaml(effects_path, effects_payload)

    with pytest.raises(ValueError, match="spawn_effect.*(missing|cycle)|cycle.*spawn_effect"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_non_finite_affine_literal_refuses_instead_of_becoming_dynamic(tmp_path: Path) -> None:
    pack = _copy_reference_pack(tmp_path)
    path, payload, eat = _affordance_payload(pack, "EAT")
    eat["interactions"]["on_start"] = [
        {"modify": "target.bar.energy", "value": "target.bar.energy + 1e309"},
    ]
    eat["interactions"]["on_completion"] = []
    _write_yaml(path, payload)

    with pytest.raises(ValueError, match="finite"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_costs_and_costs_per_tick_have_distinct_identity_and_hash(tmp_path: Path) -> None:
    for affordance_name, cost_kind in (("EAT", "costs"), ("WORK", "costs_per_tick")):
        signatures: list[tuple[tuple[float, ...], str]] = []
        for amount in (0.0, 0.1):
            pack = _copy_reference_pack(tmp_path, f"{cost_kind}_{amount}")
            path, payload, affordance = _affordance_payload(pack, affordance_name)
            affordance["costs"] = {}
            affordance["costs_per_tick"] = {}
            if amount:
                affordance[cost_kind] = {"energy": amount}
            for lifecycle_stage in affordance["interactions"]:
                affordance["interactions"][lifecycle_stage] = []
            _write_yaml(path, payload)
            signatures.append(_compiled_affordance_signature(pack, affordance_name))

        assert signatures[0][0] != signatures[1][0]
        assert signatures[0][1] != signatures[1][1]


def test_opening_hours_behavior_changes_identity_and_hash(tmp_path: Path) -> None:
    signatures: list[tuple[tuple[float, ...], str]] = []
    for name, opening_hours in (
        ("always", {"enabled": False, "schedule": []}),
        ("business_hours", {"enabled": True, "schedule": [{"start": 8, "end": 18}]}),
    ):
        pack = _copy_reference_pack(tmp_path, name)
        path, payload, eat = _affordance_payload(pack, "EAT")
        eat["opening_hours"] = opening_hours
        _write_yaml(path, payload)
        signatures.append(_compiled_affordance_signature(pack, "EAT"))

    assert signatures[0][0] != signatures[1][0]
    assert signatures[0][1] != signatures[1][1]


def test_declared_duration_changes_identity_and_hash(tmp_path: Path) -> None:
    signatures: list[tuple[tuple[float, ...], str]] = []
    for duration in (2, 3):
        pack = _copy_reference_pack(tmp_path, f"duration_{duration}")
        path, payload, work = _affordance_payload(pack, "WORK")
        work["duration_ticks"] = duration
        _write_yaml(path, payload)
        signatures.append(_compiled_affordance_signature(pack, "WORK"))

    assert signatures[0][0] != signatures[1][0]
    assert signatures[0][1] != signatures[1][1]


def _set_work_per_tick_writes(pack: Path, deltas: tuple[float, ...]) -> None:
    path, payload, work = _affordance_payload(pack, "WORK")
    work["costs"] = {}
    work["costs_per_tick"] = {}
    work["interactions"]["per_tick"] = [{"modify": "target.bar.energy", "value": f"target.bar.energy + {delta}"} for delta in deltas]
    work["interactions"]["on_completion"] = []
    _write_yaml(path, payload)


def test_fixed_k_admits_five_reachable_meter_writes(tmp_path: Path) -> None:
    pack = _copy_reference_pack(tmp_path)
    _set_work_per_tick_writes(pack, (0.1, 0.2, 0.3, 0.4, 0.5))

    UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_more_than_fixed_k_reachable_meter_writes_refuses(tmp_path: Path) -> None:
    pack = _copy_reference_pack(tmp_path)
    _set_work_per_tick_writes(pack, (0.1, 0.2, 0.3, 0.4, 0.5, 0.6))

    with pytest.raises(ValueError, match=rf"EFFECT_SUMMARY_K|at most {EFFECT_SUMMARY_K}|{EFFECT_SUMMARY_K}.*writes"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


@pytest.mark.parametrize(
    ("field", "left", "right"),
    (
        pytest.param("spawn_intensity", 0.5, 2.0, id="command-intensity"),
        pytest.param("duration", 2, 20, id="effect-duration"),
        pytest.param("reapply_policy", "renew", "stack", id="effect-reapply"),
        pytest.param("observable", False, True, id="effect-observable"),
        pytest.param("spawn_target", "target", "0", id="spawn-target"),
    ),
)
def test_spawned_effect_behavior_parameters_change_identity_and_hash(
    tmp_path: Path,
    field: str,
    left: object,
    right: object,
) -> None:
    signatures: list[tuple[tuple[float, ...], str]] = []
    for side, value in (("left", left), ("right", right)):
        pack = _copy_reference_pack(tmp_path, side)
        path, payload, eat = _affordance_payload(pack, "EAT")
        eat["costs"] = {}
        eat["interactions"]["on_start"] = [
            {
                "spawn_effect": "ate_food",
                "target": value if field == "spawn_target" else "target",
                "intensity": value if field == "spawn_intensity" else 1.0,
            }
        ]
        _write_yaml(path, payload)
        if field not in {"spawn_target", "spawn_intensity"}:
            effects_path = pack / "effects.yaml"
            effects_payload = yaml.safe_load(effects_path.read_text())
            effects_payload["effect_definitions"][0][field] = value
            _write_yaml(effects_path, effects_payload)
        signatures.append(_compiled_affordance_signature(pack, "EAT"))

    assert signatures[0][0] != signatures[1][0]
    assert signatures[0][1] != signatures[1][1]


@pytest.mark.parametrize("target", ("self", "1"))
def test_unrepresentable_affordance_spawn_target_refuses(tmp_path: Path, target: str) -> None:
    pack = _copy_reference_pack(tmp_path)
    path, payload, eat = _affordance_payload(pack, "EAT")
    eat["interactions"]["on_start"] = [{"spawn_effect": "ate_food", "target": target, "intensity": 1.0}]
    _write_yaml(path, payload)

    with pytest.raises(ValueError, match="spawn_effect.*target|target.*represent"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def test_non_cyclic_nested_spawn_effect_refuses_instead_of_flattening_chain(tmp_path: Path) -> None:
    pack = _copy_reference_pack(tmp_path)
    path, payload, eat = _affordance_payload(pack, "EAT")
    eat["interactions"]["on_start"] = [{"spawn_effect": "ate_food", "target": "target", "intensity": 1.0}]
    _write_yaml(path, payload)
    effects_path = pack / "effects.yaml"
    effects_payload = yaml.safe_load(effects_path.read_text())
    effects_payload["effect_definitions"].append(
        {
            "id": "leaf",
            "scope": "agent",
            "duration": 2,
            "reapply_policy": "renew",
            "observable": True,
            "on_spawn": [],
            "on_tick": [{"modify": "target.bar.energy", "value": "target.bar.energy + 0.1"}],
            "on_despawn": [],
            "on_interrupt": [],
        }
    )
    effects_payload["effect_definitions"][0]["on_spawn"] = [{"spawn_effect": "leaf", "target": "target", "intensity": 1.0}]
    _write_yaml(effects_path, effects_payload)

    with pytest.raises(ValueError, match="nested spawn_effect.*fixed|fixed.*nested spawn_effect"):
        UniverseCompiler().compile(pack, primary_level=LEVEL, use_cache=False)


def _contains_subsequence(haystack: tuple[float, ...], needle: tuple[float, ...]) -> bool:
    return any(haystack[index : index + len(needle)] == pytest.approx(needle) for index in range(len(haystack) - len(needle) + 1))
