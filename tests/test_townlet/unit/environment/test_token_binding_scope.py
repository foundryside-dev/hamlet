"""Typed binding scope owns publisher dispatch independently of reference spelling."""

from types import SimpleNamespace

import pytest

from townlet.environment.observation_encoder import _split_variable_element_slots
from townlet.universe.compiled import _serialize_token_spec, _token_spec_from_plain
from townlet.universe.dto.token_spec import PAYLOAD_SCHEMAS, TOKEN_TRANSPORT_VERSION, SlotBinding, TokenSpec, build_token_type
from townlet.universe.token_hashes import compute_observation_schema_hash, compute_token_layout_hash
from townlet.vfs.schema import NormalizationSpec, VariableScope


def _schema(scope: VariableScope | None, ref: str = "food.energy"):
    return build_token_type(
        "variable_element",
        (SlotBinding(slot_index=0, filler_kind="static", filler_ref=ref, scope=scope),),
        slot_context_payloads=((0.0,) * len(PAYLOAD_SCHEMAS["variable_element"]),),
        effect_catalog_contexts=(),
    )


def _profiles():
    normalization = NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True)
    return {"food": SimpleNamespace(variables=[SimpleNamespace(name="energy", exposed_to=("agent",), normalization=normalization)])}


def test_global_dotted_reference_does_not_become_item_state():
    schema = _schema(VariableScope.GLOBAL)
    assert _split_variable_element_slots(schema, _profiles()) == ((0,), ())


def test_item_scope_requires_a_known_profile_instead_of_falling_into_registry():
    schema = _schema(VariableScope.ITEM, "missing.energy[0]")
    with pytest.raises(ValueError, match="item profile"):
        _split_variable_element_slots(schema, _profiles())


def test_item_scope_emits_owner_slot_and_declared_normalization():
    registry, items = _split_variable_element_slots(_schema(VariableScope.ITEM, "food.energy[2]"), _profiles())
    assert registry == ()
    assert len(items) == 1
    assert items[0].owner_slot == 2
    assert items[0].normalization == _profiles()["food"].variables[0].normalization


def test_variable_binding_requires_non_null_scope():
    with pytest.raises(ValueError, match="scope"):
        _schema(None)


def test_binding_refuses_unknown_scope():
    with pytest.raises(ValueError, match="scope"):
        SlotBinding(slot_index=0, filler_kind="static", filler_ref="state", scope="unknown")


def test_non_variable_binding_requires_null_scope():
    with pytest.raises(ValueError, match="scope"):
        build_token_type(
            "self",
            (SlotBinding(slot_index=0, filler_kind="static", filler_ref="self", scope=VariableScope.AGENT),),
            slot_context_payloads=((0.0,) * len(PAYLOAD_SCHEMAS["self"]),),
            effect_catalog_contexts=(),
        )


def test_scope_is_semantic_identity_without_changing_layout():
    global_spec = TokenSpec(types=(_schema(VariableScope.GLOBAL),), position_rank=0, transport_version=TOKEN_TRANSPORT_VERSION)
    agent_spec = TokenSpec(types=(_schema(VariableScope.AGENT),), position_rank=0, transport_version=TOKEN_TRANSPORT_VERSION)
    assert compute_token_layout_hash(global_spec) == compute_token_layout_hash(agent_spec)
    assert compute_observation_schema_hash(global_spec) != compute_observation_schema_hash(agent_spec)


def test_scope_roundtrip_and_missing_scope_refusal():
    spec = TokenSpec(types=(_schema(VariableScope.ITEM, "food.energy[2]"),), position_rank=0, transport_version=TOKEN_TRANSPORT_VERSION)
    payload = _serialize_token_spec(spec)
    restored = _token_spec_from_plain(payload)
    assert restored == spec
    assert _split_variable_element_slots(restored.types[0], _profiles())[1][0].owner_slot == 2
    del payload["types"][0]["slot_bindings"][0]["scope"]
    with pytest.raises(ValueError, match="scope"):
        _token_spec_from_plain(payload)
