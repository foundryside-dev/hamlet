"""Exact-coordinate episode attribution must reject misleading controls."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts.check_episode_lanes import (
    canonical,
    compare_exact,
    digest,
    expected_inventory,
    load_expected,
    reading_index,
    semantic_errors,
    validate_capture,
)


def key(field: str, tick: int, agent: int) -> tuple[str, str, int, int, str]:
    return ("authored-two-five", field, tick, agent, "value")


def ledger() -> dict:
    return {
        key("step_counts", tick, agent): value
        for tick, values in enumerate(([1, 1], [2, 2], [3, 3], [4, 4], [5, 5]), 1)
        for agent, value in enumerate(values)
    } | {key("actions", 2, 0): 7, key("rewards", 5, 1): 0.0, key("global_tick", 5, -1): 5, key("reset_counts", 0, 0): 0}


def repaired() -> dict:
    result = ledger()
    for tick in (3, 4, 5):
        result[key("step_counts", tick, 0)] = 2
    return result


def declarations() -> list:
    return [(key("step_counts", tick, 0), tick, 2) for tick in (3, 4, 5)]


def test_complete_exact_changes_qualify() -> None:
    compare_exact(ledger(), repaired(), declarations())


@pytest.mark.parametrize(
    "field,tick,agent,value", [("actions", 2, 0, 8), ("rewards", 5, 1, 1.0), ("global_tick", 5, -1, 4), ("reset_counts", 0, 0, 1)]
)
def test_unauthorized_live_action_reward_clock_reset_refuses(field: str, tick: int, agent: int, value: object) -> None:
    after = repaired()
    after[key(field, tick, agent)] = value
    with pytest.raises(ValueError, match="declaration set"):
        compare_exact(ledger(), after, declarations())


def test_terminal_transition_dropped_refuses() -> None:
    after = repaired()
    del after[key("step_counts", 2, 0)]
    with pytest.raises(ValueError):
        compare_exact(ledger(), after, declarations())


def test_correct_aggregate_wrong_lanes_refuses() -> None:
    after = repaired()
    after[key("step_counts", 5, 0)] = 5
    after[key("step_counts", 5, 1)] = 2
    with pytest.raises(ValueError):
        compare_exact(ledger(), after, declarations())


def test_unused_allowance_refuses() -> None:
    with pytest.raises(ValueError, match="declaration set"):
        compare_exact(ledger(), repaired(), declarations() + [(key("rewards", 5, 1), 0.0, 1.0)])


def test_duplicate_allowance_refuses() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        compare_exact(ledger(), repaired(), declarations() * 2)


def test_exact_old_and_new_values_required() -> None:
    with pytest.raises(ValueError, match="exact values"):
        compare_exact(ledger(), repaired(), [(key("step_counts", tick, 0), 99, 2) for tick in (3, 4, 5)])


def test_type_preserved_even_when_python_values_compare_equal() -> None:
    with pytest.raises(ValueError, match="type"):
        compare_exact({key("step_counts", 1, 0): 1}, {key("step_counts", 1, 0): True}, [(key("step_counts", 1, 0), 1, 1)])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_readings_refuse(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        reading_index([{"key": list(key("rewards", 1, 0)), "value": value}])


def test_duplicate_readings_refuse() -> None:
    reading = {"key": list(key("step_counts", 1, 0)), "value": 1}
    with pytest.raises(ValueError, match="Duplicate"):
        reading_index([reading, reading])


@pytest.mark.parametrize("payload", ["", "```json\n{}\n```\n```json\n{}\n```", '```json\n{"schema":"unknown"}\n```'])
def test_manifest_missing_extra_or_unknown_json_refuses(tmp_path: Path, payload: str) -> None:
    path = tmp_path / "expected.md"
    path.write_text(payload)
    with pytest.raises(ValueError):
        load_expected(path)


def test_preregistered_unknown_after_revision_does_not_relax_values(tmp_path: Path) -> None:
    value = {"schema": "episode-lanes.expected.v1", "before_revision": "a" * 40, "after_revision": None, "changes": []}
    path = tmp_path / "expected.md"
    path.write_text("```json\n" + json.dumps(value) + "\n```\n")
    assert load_expected(path) == value


def capture() -> dict:
    value = {
        "schema": "episode-lanes.capture.v1",
        "manifest": {
            "source_root": "/parent",
            "revision": "a" * 40,
            "source_sha256": "b" * 64,
            "imported_modules": {"townlet": "/parent/src/townlet/__init__.py"},
            "source_stamp": {"revision": "a" * 40, "source_sha256": "b" * 64},
            "config_sha256": "c" * 64,
            "config_inventory": {"experiment.yaml": "d" * 64},
            "instrument_sha256": "e" * 64,
            "recipe": "authored-two-five",
            "recipe_version": 1,
            "seed": 42,
            "device": "cpu",
            "actions": [[0, 0], [7, 0], [0, 0], [0, 0], [0, 7]],
            "action_sha256": "f" * 64,
            "measured_fields": ["step_counts"],
        },
        "readings": [],
        "contract": {"qualified": False, "errors": ["parent counts"]},
    }
    for identity in sorted(expected_inventory("authored-two-five")):
        _, field, _, agent, coordinate = identity
        default: object = 0
        if coordinate == "present":
            default = False
        elif coordinate in {"dtype", "shape"}:
            default = None
        elif coordinate == "sha256":
            default = "0" * 64
        elif field in {"dones", "reset_dones", "ledger_active", "ledger_terminal"}:
            default = False
        elif field in {"rewards", "extrinsic", "intrinsic", "shaping", "intrinsic_weight"}:
            default = 0.0
        elif field in {"active_on_entry", "newly_terminal", "newly_retired", "population_completed", "reset_population_completed"}:
            default = None
        elif field.startswith("completion_") or field.startswith("reset_completion_"):
            default = None
        elif agent >= 0 and field in {"observations", "meters", "actions", "selected_q_values", "reset_observations", "reset_meters"}:
            default = []
        value["readings"].append({"key": list(identity), "value": default})
    manifest = value["manifest"]
    manifest["config_sha256"] = digest(canonical(manifest["config_inventory"]))
    manifest["action_sha256"] = digest(canonical(manifest["actions"]))
    manifest["measured_fields"] = sorted({row["key"][1] for row in value["readings"]})
    errors = semantic_errors(reading_index(value["readings"]), manifest["recipe"])
    value["contract"] = {"qualified": not errors, "errors": errors}
    return value


def test_complete_parent_defects_are_retained_without_fabricating_candidate_qualification() -> None:
    value = capture()
    assert not value["contract"]["qualified"]
    assert validate_capture(value)


@pytest.mark.parametrize("field", ["config_inventory", "actions"])
def test_modified_config_or_recorded_actions_cannot_keep_old_digest(field: str) -> None:
    value = capture()
    value["manifest"][field] = {} if field == "config_inventory" else [[999, 999]]
    with pytest.raises(ValueError, match="digest"):
        validate_capture(value)


def test_coordinate_dropped_on_both_sides_cannot_narrow_recipe_inventory() -> None:
    value = capture()
    value["readings"].pop()
    with pytest.raises(ValueError, match="inventory"):
        validate_capture(value)


def test_forged_qualified_flag_cannot_override_independently_enumerated_contract() -> None:
    value = capture()
    value["contract"] = {"qualified": True, "errors": []}
    with pytest.raises(ValueError, match="Forged"):
        validate_capture(value)


def test_stale_verdict_after_reading_mutation_refuses() -> None:
    value = capture()
    next(row for row in value["readings"] if row["key"] == list(key("step_counts", 1, 0)))["value"] = 1
    with pytest.raises(ValueError, match="stale"):
        validate_capture(value)


def test_duplicate_json_properties_cannot_hide_allowance(tmp_path: Path) -> None:
    path = tmp_path / "expected.md"
    path.write_text('```json\n{"schema":"episode-lanes.expected.v1","schema":"hidden"}\n```\n')
    with pytest.raises(ValueError, match="Duplicate JSON"):
        load_expected(path)


@pytest.mark.parametrize("mutation", ["wrong_import", "stale_revision", "stale_source_hash", "unknown_field", "unknown_recipe"])
def test_invalid_source_stamp_import_or_coordinate_refuses(mutation: str) -> None:
    value = copy.deepcopy(capture())
    if mutation == "wrong_import":
        value["manifest"]["imported_modules"]["townlet"] = "/candidate/src/townlet/__init__.py"
    elif mutation == "stale_revision":
        value["manifest"]["source_stamp"]["revision"] = "f" * 40
    elif mutation == "stale_source_hash":
        value["manifest"]["source_stamp"]["source_sha256"] = "f" * 64
    elif mutation == "unknown_recipe":
        value["manifest"]["recipe"] = "other"
    else:
        value["readings"][0]["key"][1] = "unknown"
    with pytest.raises(ValueError):
        validate_capture(value)
