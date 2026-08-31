"""Adversarial cache-load pins for the compiler-owned token artifact."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

import townlet.universe.compiled as compiled_module
from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.token_hashes import (
    compute_observation_schema_hash,
    compute_token_layout_hash,
    compute_token_type_schema_hash,
)
from townlet.vfs.schema_hashes import compute_vfs_hash


@pytest.fixture(scope="module")
def compiled_token_payload() -> dict[str, Any]:
    compiled = UniverseCompiler().compile(
        Path("configs/trial002_money_log_gdp"),
        primary_level="L0_simple",
        use_cache=False,
    )
    return compiled.to_dict()


@pytest.fixture(scope="module")
def compiled_items_payload() -> dict[str, Any]:
    compiled = UniverseCompiler().compile(
        Path("configs/default_curriculum"),
        primary_level="L1_full_observability",
        use_cache=False,
    )
    return compiled.to_dict()


def _level(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["all_levels"][payload["metadata"]["primary_level"]]


def _token_type(token_spec: dict[str, Any], type_name: str) -> dict[str, Any]:
    return next(token_type for token_type in token_spec["types"] if token_type["type_name"] == type_name)


def _rehash_primary_token_artifact(payload: dict[str, Any]) -> None:
    """Model an attacker who updates every stored hash after changing TokenSpec."""
    level = _level(payload)
    spec = compiled_module._token_spec_from_plain(level["token_spec"])
    level["token_type_schema_hash"] = compute_token_type_schema_hash(spec)
    level["layout_hash"] = compute_token_layout_hash(spec)
    level["observation_schema_hash"] = compute_observation_schema_hash(spec)
    level["vfs_hash"] = compute_vfs_hash(
        level["variable_schema_hash"],
        level["observation_schema_hash"],
        level["action_schema_hash"],
        level["transition_graph_hash"],
    )
    payload["token_spec"] = deepcopy(level["token_spec"])
    for field_name in ("token_type_schema_hash", "layout_hash", "observation_schema_hash", "vfs_hash"):
        payload[field_name] = level[field_name]


@pytest.mark.parametrize("mutation", ["reference", "order", "signature", "capacity"])
def test_load_rejects_meter_binding_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    bindings = _token_type(_level(payload)["token_spec"], "meter")["slot_bindings"]
    if mutation == "reference":
        bindings[0]["filler_ref"] = "ghost-meter"
    elif mutation == "order":
        bindings[0]["filler_ref"], bindings[1]["filler_ref"] = bindings[1]["filler_ref"], bindings[0]["filler_ref"]
        bindings[0]["static_signature"], bindings[1]["static_signature"] = (
            bindings[1]["static_signature"],
            bindings[0]["static_signature"],
        )
    elif mutation == "signature":
        current = bindings[0]["static_signature"][0]
        bindings[0]["static_signature"][0] = 0.25 if current != 0.25 else 0.5
    else:
        bindings.pop()
        _token_type(_level(payload)["token_spec"], "meter")["capacity"] -= 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="meter slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "signature", "capacity"])
def test_load_rejects_affordance_binding_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    bindings = _token_type(_level(payload)["token_spec"], "affordance")["slot_bindings"]
    if mutation == "reference":
        bindings[0]["filler_ref"] = "ghost-affordance"
    elif mutation == "order":
        bindings[0]["filler_ref"], bindings[1]["filler_ref"] = bindings[1]["filler_ref"], bindings[0]["filler_ref"]
        bindings[0]["static_signature"], bindings[1]["static_signature"] = (
            bindings[1]["static_signature"],
            bindings[0]["static_signature"],
        )
    elif mutation == "signature":
        current = bindings[0]["static_signature"][0]
        bindings[0]["static_signature"][0] = 0.25 if current != 0.25 else 0.5
    else:
        bindings.pop()
        _token_type(_level(payload)["token_spec"], "affordance")["capacity"] -= 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="affordance slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_effect_catalog_tampering_used_by_affordance(compiled_token_payload: dict[str, Any]) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["effects"]["business_cycle"]["on_tick"][0]["path"] = "bar.energy"

    with pytest.raises(ValueError, match="affordance slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "capacity"])
def test_load_rejects_self_binding_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    self_type = _token_type(_level(payload)["token_spec"], "self")
    if mutation == "reference":
        self_type["slot_bindings"][0]["filler_ref"] = "ghost-self"
    else:
        self_type["slot_bindings"].append(
            {
                "slot_index": 1,
                "filler_kind": "static",
                "filler_ref": "ghost-self",
                "static_signature": None,
            }
        )
        self_type["capacity"] += 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="self.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_agent_capacity_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    agent_type = _token_type(_level(payload)["token_spec"], "agent")
    agent_type["slot_bindings"].append(
        {
            "slot_index": 0,
            "filler_kind": "dynamic",
            "filler_ref": "agent:0",
            "static_signature": None,
        }
    )
    agent_type["capacity"] = 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="agent.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_item_capacity_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    item_type = _token_type(_level(payload)["token_spec"], "item")
    item_type["slot_bindings"].append(
        {
            "slot_index": 0,
            "filler_kind": "dynamic",
            "filler_ref": "item:0",
            "static_signature": None,
        }
    )
    item_type["capacity"] = 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="item.*slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "capacity"])
def test_load_rejects_nonzero_item_binding_tampering_even_with_recomputed_hashes(
    compiled_items_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_items_payload)
    item_type = _token_type(_level(payload)["token_spec"], "item")
    bindings = item_type["slot_bindings"]
    if mutation == "reference":
        bindings[0]["filler_ref"] = "item:ghost"
    elif mutation == "order":
        bindings[0]["filler_ref"], bindings[1]["filler_ref"] = bindings[1]["filler_ref"], bindings[0]["filler_ref"]
    else:
        bindings.pop()
        item_type["capacity"] -= 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="item.*slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "capacity"])
def test_load_rejects_effect_binding_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    effect_type = _token_type(_level(payload)["token_spec"], "effect")
    if mutation == "reference":
        effect_type["slot_bindings"][0]["filler_ref"] = "effect:global:ghost"
    else:
        effect_type["slot_bindings"].pop()
        effect_type["capacity"] = 0
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="effect.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_effect_budget_change_against_stale_bindings(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["max_active_effects"]["global"] = 2

    with pytest.raises(ValueError, match="effect.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_effect_scope_block_order_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["max_active_effects"]["agent"] = 1
    effect_type = _token_type(_level(payload)["token_spec"], "effect")
    effect_type["slot_bindings"].insert(
        0,
        {
            "slot_index": 0,
            "filler_kind": "dynamic",
            "filler_ref": "effect:agent:0",
            "static_signature": None,
        },
    )
    effect_type["slot_bindings"][1]["slot_index"] = 1
    effect_type["capacity"] = 2
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="effect.*slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "signature", "capacity"])
def test_load_rejects_variable_element_binding_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
    mutation: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    variable_type = _token_type(_level(payload)["token_spec"], "variable_element")
    bindings = variable_type["slot_bindings"]
    if mutation == "reference":
        bindings[0]["filler_ref"] = "ghost-variable"
    elif mutation == "order":
        bindings[0]["filler_ref"], bindings[1]["filler_ref"] = bindings[1]["filler_ref"], bindings[0]["filler_ref"]
        bindings[0]["static_signature"], bindings[1]["static_signature"] = (
            bindings[1]["static_signature"],
            bindings[0]["static_signature"],
        )
    elif mutation == "signature":
        current = bindings[0]["static_signature"][0]
        bindings[0]["static_signature"][0] = 0.25 if current != 0.25 else 0.5
    else:
        bindings.pop()
        variable_type["capacity"] -= 1
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="variable_element.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_effect_catalog_budget_round_trips_exactly(compiled_token_payload: dict[str, Any]) -> None:
    payload = deepcopy(compiled_token_payload)
    expected_budget = {"global": 1, "agent": 0, "item": 0, "affordance": 0}

    assert payload["compiled_effect_catalog"].get("max_active_effects") == expected_budget
    restored = CompiledUniverse.from_dict(payload)

    assert restored.compiled_effect_catalog is not None
    assert restored.compiled_effect_catalog.max_active_effects == expected_budget


def test_load_rejects_effect_catalog_missing_required_budget(compiled_token_payload: dict[str, Any]) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"].pop("max_active_effects", None)

    with pytest.raises(ValueError, match="compiled_effect_catalog.max_active_effects"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize(
    ("budget", "error_match"),
    [
        (None, "must be a mapping when effects are present"),
        ([1, 0, 0, 0], "must be a mapping"),
        ({"global": 1, "agent": 0, "item": 0}, "must contain exactly"),
        ({"global": 1, "agent": 0, "item": 0, "affordance": 0, "ghost": 0}, "must contain exactly"),
        ({"global": -1, "agent": 0, "item": 0, "affordance": 0}, r"max_active_effects\.global.*non-negative integer"),
        ({"global": True, "agent": 0, "item": 0, "affordance": 0}, r"max_active_effects\.global.*non-negative integer"),
    ],
)
def test_load_rejects_malformed_effect_catalog_budget(
    compiled_token_payload: dict[str, Any],
    budget: object,
    error_match: str,
) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["max_active_effects"] = budget

    with pytest.raises(ValueError, match=error_match):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_effect_budget_when_catalog_is_empty(compiled_token_payload: dict[str, Any]) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["effects"] = {}
    payload["compiled_effect_catalog"]["max_active_effects"] = {
        "global": 0,
        "agent": 0,
        "item": 0,
        "affordance": 0,
    }

    with pytest.raises(ValueError, match="must be null when no effects are present"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_incomplete_token_type_roster_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    level_token_types = _level(payload)["token_spec"]["types"]
    level_token_types[:] = [token_type for token_type in level_token_types if token_type["type_name"] != "agent"]
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="exact engine roster"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize(
    "field_name",
    ["token_type_schema_hash", "layout_hash", "observation_schema_hash", "vfs_hash"],
)
def test_load_rejects_stale_per_level_derived_hash(compiled_token_payload: dict[str, Any], field_name: str) -> None:
    payload = deepcopy(compiled_token_payload)
    _level(payload)[field_name] = "0" * 64

    with pytest.raises(ValueError, match=field_name):
        CompiledUniverse.from_dict(payload)


def test_valid_compiled_token_artifact_still_round_trips(compiled_token_payload: dict[str, Any]) -> None:
    restored = CompiledUniverse.from_dict(deepcopy(compiled_token_payload))

    assert restored.metadata.primary_level == "L0_simple"
