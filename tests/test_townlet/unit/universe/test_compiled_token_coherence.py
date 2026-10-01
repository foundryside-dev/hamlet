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


def _append_non_effect_slot(token_type: dict[str, Any], *, filler_kind: str, filler_ref: str) -> None:
    """Keep a tampered non-effect type structurally valid for coherence testing."""
    slot_index = token_type["capacity"]
    token_type["slot_bindings"].append(
        {
            "slot_index": slot_index,
            "filler_kind": filler_kind,
            "filler_ref": filler_ref,
            "scope": "global" if token_type["type_name"] == "variable_element" else None,
        }
    )
    token_type["slot_context_payloads"].append([0.0] * len(token_type["payload_features"]))
    token_type["capacity"] += 1


def _remove_last_non_effect_slot(token_type: dict[str, Any]) -> None:
    """Keep a reduced non-effect type structurally valid for coherence testing."""
    token_type["slot_bindings"].pop()
    token_type["slot_context_payloads"].pop()
    token_type["capacity"] -= 1


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


def test_load_rejects_token_rank_tampering_against_persisted_grid2d_substrate(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    assert payload["metadata"]["position_dim"] == 2
    assert payload["stratum"]["stratum"]["substrate"]["grid"]["topology"] == "square"
    token_spec = _level(payload)["token_spec"]
    token_spec["position_rank"] = 3
    for type_name in ("self", "affordance", "agent", "item"):
        token_type = _token_type(token_spec, type_name)
        rank_index = token_type["payload_features"].index("position_rank")
        for context in token_type["slot_context_payloads"]:
            context[rank_index] = 3 / 8
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match=r"position_rank.*substrate"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "context", "capacity"])
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
    elif mutation == "context":
        contexts = _token_type(_level(payload)["token_spec"], "meter")["slot_context_payloads"]
        current = contexts[0][0]
        contexts[0][0] = 0.25 if current != 0.25 else 0.5
    else:
        _remove_last_non_effect_slot(_token_type(_level(payload)["token_spec"], "meter"))
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match=r"meter.*slot (?:bindings|context)"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "context", "capacity"])
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
    elif mutation == "context":
        contexts = _token_type(_level(payload)["token_spec"], "affordance")["slot_context_payloads"]
        current = contexts[0][0]
        contexts[0][0] = 0.25 if current != 0.25 else 0.5
    else:
        _remove_last_non_effect_slot(_token_type(_level(payload)["token_spec"], "affordance"))
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match=r"affordance.*slot (?:bindings|context)"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_effect_catalog_tampering_used_by_affordance(compiled_token_payload: dict[str, Any]) -> None:
    payload = deepcopy(compiled_token_payload)
    payload["compiled_effect_catalog"]["effects"]["business_cycle"]["on_tick"][0]["path"] = "bar.energy"

    with pytest.raises(ValueError, match=r"affordance.*slot (?:bindings|context)"):
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
        _append_non_effect_slot(self_type, filler_kind="static", filler_ref="ghost-self")
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="self.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_agent_capacity_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    agent_type = _token_type(_level(payload)["token_spec"], "agent")
    _append_non_effect_slot(agent_type, filler_kind="dynamic", filler_ref="agent:0")
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="agent.*slot bindings"):
        CompiledUniverse.from_dict(payload)


def test_load_rejects_item_capacity_tampering_even_with_recomputed_hashes(
    compiled_token_payload: dict[str, Any],
) -> None:
    payload = deepcopy(compiled_token_payload)
    item_type = _token_type(_level(payload)["token_spec"], "item")
    _append_non_effect_slot(item_type, filler_kind="dynamic", filler_ref="item:0")
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
        _remove_last_non_effect_slot(item_type)
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
            "scope": None,
        },
    )
    effect_type["slot_bindings"][1]["slot_index"] = 1
    effect_type["capacity"] = 2
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match="effect.*slot bindings"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("mutation", ["reference", "order", "context", "capacity", "scope"])
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
    elif mutation == "context":
        contexts = variable_type["slot_context_payloads"]
        current = contexts[0][0]
        contexts[0][0] = 0.25 if current != 0.25 else 0.5
    elif mutation == "scope":
        bindings[0]["scope"] = "agent" if bindings[0]["scope"] == "global" else "global"
    else:
        _remove_last_non_effect_slot(variable_type)
    _rehash_primary_token_artifact(payload)

    with pytest.raises(ValueError, match=r"variable_element.*slot (?:bindings|context)"):
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


@pytest.fixture
def static_access_payload(tmp_path: Path) -> dict[str, Any]:
    from tests.test_townlet.integration.test_canonical_variable_runtime import _compile, _pack, _variable

    public = _variable("public", scope="global")
    public.update(exposed_to=["agent"], normalization={"kind": "minmax", "min": 0.0, "max": 10.0, "clip": True})
    hidden = _variable("hidden", scope="agent")
    hidden.update(readable_by=["engine"], writable_by=[])
    item = _variable("charge", scope="item")
    item.update(profile="default_item", readable_by=["engine"], writable_by=[])
    return _compile(_pack(tmp_path, [public, hidden, item])).to_dict()


@pytest.mark.parametrize("side", ["registry", "profile"])
@pytest.mark.parametrize("field", ["readable_by", "writable_by"])
def test_load_refuses_bidirectional_ordinary_policy_disagreement(static_access_payload: dict[str, Any], side: str, field: str) -> None:
    payload = deepcopy(static_access_payload)
    variable = (
        next(v for v in _level(payload)["vfs_variables"] if v["id"] == "hidden")
        if side == "registry"
        else payload["compiled_vfs_profiles"]["agent_profile"]["variables"][0]
    )
    variable[field] = ["engine", "agent"] if field == "readable_by" else ["engine"]
    with pytest.raises(ValueError, match="policy coherence"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("side", ["registry", "profile"])
def test_load_refuses_ordinary_profile_roster_loss(static_access_payload: dict[str, Any], side: str) -> None:
    payload = deepcopy(static_access_payload)
    if side == "registry":
        _level(payload)["vfs_variables"] = [v for v in _level(payload)["vfs_variables"] if v["id"] != "hidden"]
    else:
        payload["compiled_vfs_profiles"]["agent_profile"]["variables"].clear()
    with pytest.raises(ValueError, match="policy coherence"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("field", ["readable_by", "writable_by"])
def test_load_refuses_hidden_item_policy_with_stale_hash(static_access_payload: dict[str, Any], field: str) -> None:
    payload = deepcopy(static_access_payload)
    item = payload["compiled_vfs_profiles"]["item_profiles"]["default_item"]["variables"][0]
    item[field] = ["engine", "agent"] if field == "readable_by" else ["engine"]
    with pytest.raises(ValueError, match="variable_schema_hash"):
        CompiledUniverse.from_dict(payload)


def test_load_refuses_item_profile_key_identity_disagreement(static_access_payload: dict[str, Any]) -> None:
    payload = deepcopy(static_access_payload)
    payload["compiled_vfs_profiles"]["item_profiles"]["default_item"]["profile_name"] = "wrong"
    with pytest.raises(ValueError, match="profile.*identity"):
        CompiledUniverse.from_dict(payload)


def test_load_refuses_hidden_item_policy_even_if_variable_hash_is_refreshed(static_access_payload: dict[str, Any]) -> None:
    from townlet.vfs.schema_hashes import compute_variable_schema_hash

    payload = deepcopy(static_access_payload)
    item = payload["compiled_vfs_profiles"]["item_profiles"]["default_item"]["variables"][0]
    item["writable_by"] = ["engine"]
    profiles = compiled_module._deserialize_vfs_profiles(payload["compiled_vfs_profiles"])
    definitions = tuple(compiled_module.VariableDef(**v) for v in _level(payload)["vfs_variables"])
    _level(payload)["variable_schema_hash"] = compute_variable_schema_hash(definitions, profiles.item_profiles)
    with pytest.raises(ValueError, match="vfs_hash"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("scope", ["agent_profile", "global_profile", "item_profiles"])
@pytest.mark.parametrize("field", ["readable_by", "writable_by"])
def test_load_requires_profile_policy_fields(static_access_payload: dict[str, Any], scope: str, field: str) -> None:
    payload = deepcopy(static_access_payload)
    profile = payload["compiled_vfs_profiles"][scope]
    if scope == "item_profiles":
        profile = profile["default_item"]
    profile["variables"][0].pop(field)
    with pytest.raises(ValueError, match=field):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("scope", ["agent_profile", "item_profiles"])
def test_load_refuses_duplicate_profile_variable_identity(static_access_payload: dict[str, Any], scope: str) -> None:
    payload = deepcopy(static_access_payload)
    profile = payload["compiled_vfs_profiles"][scope]
    if scope == "item_profiles":
        profile = profile["default_item"]
    profile["variables"].append(deepcopy(profile["variables"][0]))
    with pytest.raises(ValueError, match="(?:policy coherence|duplicate variable identity)"):
        CompiledUniverse.from_dict(payload)


def test_load_does_not_accept_deleted_whole_item_profile_with_stale_identity(static_access_payload: dict[str, Any]) -> None:
    payload = deepcopy(static_access_payload)
    payload["compiled_vfs_profiles"]["item_profiles"].clear()
    with pytest.raises(ValueError, match="variable_schema_hash"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("side", ["registry", "profile"])
@pytest.mark.parametrize("field", ["type", "lifetime", "normalization"])
def test_load_refuses_same_entity_profile_metadata_disagreement(static_access_payload: dict[str, Any], side: str, field: str) -> None:
    payload = deepcopy(static_access_payload)
    variable = (
        next(v for v in _level(payload)["vfs_variables"] if v["id"] == "public")
        if side == "registry"
        else payload["compiled_vfs_profiles"]["global_profile"]["variables"][0]
    )
    if field == "type":
        variable["type"] = "bool"
        variable["default" if side == "registry" else "initial_value"] = True
    elif field == "lifetime":
        variable["lifetime"] = "persistent"
    else:
        variable["normalization"]["max"] = 20.0
    with pytest.raises(ValueError, match=f"policy coherence.*{field}"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("side", ["registry", "profile"])
def test_load_refuses_same_entity_profile_dimension_disagreement(tmp_path: Path, side: str) -> None:
    from tests.test_townlet.integration.test_canonical_variable_runtime import _compile, _pack, _variable

    vector = _variable("vector", scope="agent")
    vector.update(type="vecNf", dims=2, initial_value=[1.0, 2.0])
    payload = _compile(_pack(tmp_path, [vector])).to_dict()
    variable = (
        next(v for v in _level(payload)["vfs_variables"] if v["id"] == "vector")
        if side == "registry"
        else payload["compiled_vfs_profiles"]["agent_profile"]["variables"][0]
    )
    variable["dims"] = 3
    variable["default" if side == "registry" else "initial_value"] = [1.0, 2.0, 3.0]
    with pytest.raises(ValueError, match="policy coherence.*dims"):
        CompiledUniverse.from_dict(payload)


@pytest.mark.parametrize("side", ["registry", "profile"])
def test_load_refuses_same_entity_profile_tensor_shape_disagreement(tmp_path: Path, side: str) -> None:
    from tests.test_townlet.integration.test_canonical_variable_runtime import _compile, _pack, _variable

    tensor = _variable("matrix", scope="agent")
    tensor.pop("initial_value")
    tensor.update(type="tensor2d", shape=[2, 2], initial_value_mode="zeros")
    payload = _compile(_pack(tmp_path, [tensor])).to_dict()
    variable = (
        next(v for v in _level(payload)["vfs_variables"] if v["id"] == "matrix")
        if side == "registry"
        else payload["compiled_vfs_profiles"]["agent_profile"]["variables"][0]
    )
    variable["shape"] = [2, 3]
    with pytest.raises(ValueError, match="policy coherence.*shape"):
        CompiledUniverse.from_dict(payload)


def test_load_accepts_scalar_expression_spelling_and_lowered_tensor_initializer(tmp_path: Path) -> None:
    from tests.test_townlet.integration.test_canonical_variable_runtime import _compile, _pack, _variable

    scalar = _variable("number", scope="global")
    tensor = _variable("matrix", scope="agent")
    tensor.pop("initial_value")
    tensor.update(
        type="tensor2d",
        shape=[2, 2],
        initial_value_mode="zeros",
        exposed_to=["agent"],
        normalization={"kind": "minmax", "min": 0.0, "max": 1.0, "clip": True},
    )
    payload = _compile(_pack(tmp_path, [scalar, tensor])).to_dict()
    assert next(v for v in _level(payload)["vfs_variables"] if v["id"] == "number")["type"] == "scalar"
    assert payload["compiled_vfs_profiles"]["global_profile"]["variables"][0]["type"] == "float"
    assert next(v for v in _level(payload)["vfs_variables"] if v["id"] == "matrix")["initial_value_mode"] is None
    assert payload["compiled_vfs_profiles"]["agent_profile"]["variables"][0]["initial_value_mode"] == "zeros"
    CompiledUniverse.from_dict(payload)
