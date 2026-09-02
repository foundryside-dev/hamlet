"""Milestone-3 RED contract for compact dynamic replay (PDR-0131/PDR-0132).

The fixed per-type payload remains the network-facing transfer schema.  ``TokenSpec``
serialization itself is the sole compact env/replay ABI; the fixed dimensions and row
layout exist only for boundary assembly.  These tests pin that split without
preserving the full-payload transition ABI as a callable path.
"""

from __future__ import annotations

from dataclasses import MISSING
from pathlib import Path
from typing import Any

import pytest
import torch

from townlet.universe.compiler import UniverseCompiler
from townlet.universe.dto import token_spec as token_spec_module
from townlet.universe.dto.token_spec import (
    AFFORDANCE_SIGNATURE_WIDTH,
    EFFECT_STATIC_FEATURES,
    MAX_POSITION_RANK,
    PAYLOAD_SCHEMAS,
    TOKEN_TYPE_FILLER_KIND,
    EffectDeclaration,
    SlotBinding,
    TokenSpec,
    TokenTypeSchema,
    build_token_type,
    effect_static_payload,
    element_coordinate_block,
)


@pytest.fixture(scope="module")
def l1_token_spec() -> TokenSpec:
    universe = UniverseCompiler().compile(
        Path("configs/default_curriculum"),
        primary_level="L1_full_observability",
        use_cache=False,
    )
    return universe.get_level("L1_full_observability").token_spec


def _token_spec(
    *,
    types: tuple[Any, ...],
    position_rank: int,
) -> TokenSpec:
    fields = TokenSpec.__dataclass_fields__
    assert "position_rank" in fields, "TokenSpec.position_rank must be required compiled universe authority"
    assert (
        fields["position_rank"].default is MISSING and fields["position_rank"].default_factory is MISSING
    ), "TokenSpec.position_rank must be required; the compiler may not hide universe rank behind a default"
    assert "transport_version" in fields, "TokenSpec.transport_version must make the sole compact transport ABI explicit"
    assert (
        fields["transport_version"].default is MISSING and fields["transport_version"].default_factory is MISSING
    ), "TokenSpec.transport_version must be required; old full-payload artifacts may not inherit the compact ABI"
    kwargs: dict[str, Any] = {
        "types": types,
        "position_rank": position_rank,
        "transport_version": "compact-1",
    }
    return TokenSpec(
        **kwargs,
    )


def _fixed_payload(type_name: str, values: dict[str, float] | None = None) -> tuple[float, ...]:
    payload = [0.0] * len(PAYLOAD_SCHEMAS[type_name])
    for feature, value in (values or {}).items():
        payload[PAYLOAD_SCHEMAS[type_name].index(feature)] = value
    return tuple(payload)


def _context(*, context_ref: str, fixed_payload: tuple[float, ...]) -> Any:
    context_type = getattr(token_spec_module, "TokenContext", None)
    assert context_type is not None, (
        "TokenContext(context_ref, fixed_payload) must identify effect-catalog rows " "without putting immutable identity in replay"
    )
    return context_type(context_ref=context_ref, fixed_payload=fixed_payload)


def _build_token_type(
    type_name: str,
    slot_bindings: tuple[SlotBinding, ...],
    *,
    slot_context_payloads: tuple[tuple[float, ...], ...] = (),
    effect_catalog_contexts: tuple[Any, ...] = (),
) -> TokenTypeSchema:
    return build_token_type(
        type_name,
        slot_bindings,
        slot_context_payloads=slot_context_payloads,
        effect_catalog_contexts=effect_catalog_contexts,
    )


def _compact_layout(spec: TokenSpec) -> Any:
    assert hasattr(spec, "position_rank"), "TokenSpec.position_rank must be stored in the compiled artifact"
    assert hasattr(spec, "compact_layout"), (
        "PDR-0131 requires TokenSpec.compact_layout() so replay has one "
        "compact dynamic ABI and the old full-payload transition ABI can be deleted"
    )
    return spec.compact_layout()


def _assembler(spec: TokenSpec) -> Any:
    from townlet.agent.token_input import TokenInputAssembler

    return TokenInputAssembler(token_spec=spec)


def _single_type_spec(type_name: str, *, capacity: int = 2, effect_catalog_size: int = 2) -> TokenSpec:
    filler_kind = TOKEN_TYPE_FILLER_KIND[type_name]
    bindings = tuple(SlotBinding(slot_index=slot, filler_kind=filler_kind, filler_ref=f"{type_name}:{slot}") for slot in range(capacity))
    if type_name == "effect":
        slot_context_payloads: tuple[tuple[float, ...], ...] = ()
        effect_catalog_contexts = tuple(
            _context(
                context_ref=f"effect:catalog:{index}",
                fixed_payload=tuple((index + 1) * 0.125 for _ in PAYLOAD_SCHEMAS[type_name]),
            )
            for index in range(effect_catalog_size)
        )
    else:
        slot_context_payloads = tuple(tuple((slot + 1) * 0.125 for _ in PAYLOAD_SCHEMAS[type_name]) for slot in range(capacity))
        effect_catalog_contexts = ()
    return _token_spec(
        position_rank=2,
        types=(
            _build_token_type(
                type_name,
                bindings,
                slot_context_payloads=slot_context_payloads,
                effect_catalog_contexts=effect_catalog_contexts,
            ),
        ),
    )


def test_immutable_context_is_schema_owned_without_duplicating_non_effect_identity(l1_token_spec: TokenSpec) -> None:
    assert (
        "static_signature" not in SlotBinding.__dataclass_fields__
    ), "SlotBinding is slot assignment only; immutable fixed payloads belong to TokenTypeSchema"
    assert "slot_context_payloads" in TokenTypeSchema.__dataclass_fields__
    assert "effect_catalog_contexts" in TokenTypeSchema.__dataclass_fields__
    assert "context_rows" not in TokenTypeSchema.__dataclass_fields__
    assert "effect_catalog_signatures" not in TokenSpec.__dataclass_fields__

    context_type = getattr(token_spec_module, "TokenContext", None)
    assert context_type is not None
    assert context_type.__dataclass_params__.frozen
    assert tuple(context_type.__dataclass_fields__) == ("context_ref", "fixed_payload")

    for type_schema in l1_token_spec.types:
        assert isinstance(type_schema.slot_context_payloads, tuple)
        assert isinstance(type_schema.effect_catalog_contexts, tuple)
        if type_schema.type_name == "effect":
            assert type_schema.slot_context_payloads == ()
        else:
            assert type_schema.effect_catalog_contexts == ()
            assert len(type_schema.slot_context_payloads) == type_schema.capacity
        for payload in type_schema.slot_context_payloads:
            assert isinstance(payload, tuple)
            assert len(payload) == len(PAYLOAD_SCHEMAS[type_schema.type_name])
        for row in type_schema.effect_catalog_contexts:
            assert isinstance(row, context_type)
            assert isinstance(row.fixed_payload, tuple)
            assert len(row.fixed_payload) == len(PAYLOAD_SCHEMAS[type_schema.type_name])


def test_current_l1_dynamic_census_is_exactly_118_and_below_the_120_cap(l1_token_spec: TokenSpec) -> None:
    """Current L1 exposes ONE variable_element — the authored day_phase clock (PDR-0143) —
    so its authoritative width is 118 (measured 2026-09-02), still below the 120 cap.

    This is the same shape the PDR's 118-float target described as a hypothetical 115 base
    plus one rank-0 variable token; day_phase makes that shape the real, current census, not
    a synthetic addition (see the rank-0 row-width test below).
    """
    layout = _compact_layout(l1_token_spec)

    assert not hasattr(layout, "reconstruct")
    assert not hasattr(layout, "static_context")
    assert getattr(token_spec_module, "TOKEN_TRANSPORT_VERSION", None) == "compact-1"
    assert l1_token_spec.transport_version == "compact-1"
    assert l1_token_spec.position_rank == 2
    assert l1_token_spec.census == {
        "self": 1,
        "meter": 8,
        "affordance": 14,
        "agent": 0,
        "item": 2,
        "effect": 0,
        "variable_element": 1,
    }
    assert l1_token_spec.total_dims == layout.dynamic_total_dims == 5 + 24 + 70 + 16 + 3 == 118
    assert l1_token_spec.fixed_total_dims == 4142
    assert l1_token_spec.row_layout()[-1][3] == l1_token_spec.total_dims
    assert l1_token_spec.fixed_row_layout()[-1][3] == l1_token_spec.fixed_total_dims
    assert l1_token_spec.total_dims <= 120
    assert l1_token_spec.total_dims * 2 * 100_000 * torch.float32.itemsize == 94_400_000


def test_a_rank_zero_variable_element_row_is_exactly_three_floats() -> None:
    """A single variable_element slot is presence plus two value lanes — three floats,
    regardless of position_rank. This is the shape day_phase's real row in L1 shares
    (verified above), pinned here independently of any one universe's census."""
    scalar_spec = _token_spec(
        position_rank=0,
        types=(
            _build_token_type(
                "variable_element",
                (
                    SlotBinding(
                        slot_index=0,
                        filler_kind="static",
                        filler_ref="variable:clock[0]",
                    ),
                ),
                slot_context_payloads=(_fixed_payload("variable_element"),),
            ),
        ),
    )
    scalar_layout = _compact_layout(scalar_spec)

    variable_layout = scalar_layout.get_type("variable_element")
    assert variable_layout is not None
    assert variable_layout.dynamic_features == ("presence", "value_0", "value_1")
    assert scalar_spec.total_dims == scalar_layout.dynamic_total_dims == 3


def test_compact_l1_rows_exclude_descriptors_and_fixed_rank_padding(l1_token_spec: TokenSpec) -> None:
    layout = _compact_layout(l1_token_spec)

    dynamic_features_by_type = {token_type.type_name: token_type.dynamic_features for token_type in layout.types}
    assert dynamic_features_by_type == {
        "self": ("presence", "position_0", "position_1", "velocity_0", "velocity_1"),
        "meter": ("presence", "value_0", "value_1"),
        "affordance": ("presence", "position_0", "position_1", "egocentric_0", "egocentric_1"),
        "agent": ("presence", "position_0", "position_1", "egocentric_0", "egocentric_1"),
        "item": (
            "presence",
            "position_0",
            "position_1",
            "egocentric_0",
            "egocentric_1",
            "carried",
            "owner_slot",
            "owner_slot_applicable",
        ),
        "effect": (
            "presence",
            "context_index",
            "remaining_fraction",
            "live_intensity",
            "owner_slot",
            "owner_slot_applicable",
        ),
        "variable_element": ("presence", "value_0", "value_1"),
    }
    serialized_features = {feature for features in dynamic_features_by_type.values() for feature in features}
    assert "position_rank" not in serialized_features
    assert "value_width_used" not in serialized_features
    assert not any(f"position_{index}" in serialized_features for index in range(2, MAX_POSITION_RANK))
    assert not serialized_features.intersection(
        {
            "initial",
            "lethal_min",
            "normalization_kind_minmax",
            "interaction_type_instant",
            "duration_ticks",
            "open_hour_0",
            "effect_count",
            "scope_global",
            "semantic_temporal",
            "declared_initial",
        }
    )


def test_ranked_variable_coordinates_are_static_context_not_replay_lanes() -> None:
    universe = UniverseCompiler().compile(
        Path("configs/test/token_set_smoke"),
        primary_level="L0_test",
        use_cache=False,
    )
    spec = universe.get_level("L0_test").token_spec
    layout = _compact_layout(spec)
    assembler = _assembler(spec)
    variable_type = spec.get_type("variable_element")
    assert variable_type is not None
    assert any(binding.filler_ref.startswith("need_tokens[") for binding in variable_type.slot_bindings)
    variable_layout = layout.get_type("variable_element")
    assert variable_layout is not None
    assert variable_layout.dynamic_features == ("presence", "value_0", "value_1")

    dynamic_rows = torch.zeros((1, variable_type.capacity, 3), dtype=torch.float32)
    for binding in variable_type.slot_bindings:
        dynamic_rows[0, binding.slot_index] = torch.tensor([1.0, 0.25, 0.75])

    expanded_rows = assembler.expand_type("variable_element", dynamic_rows)
    assert expanded_rows.shape == (1, variable_type.capacity, 1 + len(PAYLOAD_SCHEMAS["variable_element"]))
    for binding in variable_type.slot_bindings:
        if not binding.filler_ref.startswith("need_tokens["):
            continue
        element_index = int(binding.filler_ref.removeprefix("need_tokens[").removesuffix("]"))
        position_start = 1 + PAYLOAD_SCHEMAS["variable_element"].index("position_0")
        expected_coordinates = torch.tensor(element_coordinate_block((4, 3), element_index), dtype=torch.float32)
        assert torch.equal(
            expanded_rows[0, binding.slot_index, position_start : position_start + MAX_POSITION_RANK + 1],
            expected_coordinates,
        )


def test_static_context_and_dynamic_state_assemble_the_fixed_input_exactly() -> None:
    static_feature_names = tuple(
        feature
        for feature in PAYLOAD_SCHEMAS["affordance"]
        if not feature.startswith("position_") and not feature.startswith("egocentric_")
    )
    assert len(static_feature_names) == AFFORDANCE_SIGNATURE_WIDTH
    signature = tuple((index + 1) / (AFFORDANCE_SIGNATURE_WIDTH + 1) for index in range(AFFORDANCE_SIGNATURE_WIDTH))
    fixed_payload = _fixed_payload(
        "affordance",
        dict(zip(static_feature_names, signature, strict=True)) | {"position_rank": 2 / MAX_POSITION_RANK},
    )
    spec = _token_spec(
        position_rank=2,
        types=(
            _build_token_type(
                "affordance",
                (
                    SlotBinding(
                        slot_index=0,
                        filler_kind="static",
                        filler_ref="affordance:cafe[0]",
                    ),
                ),
                slot_context_payloads=(fixed_payload,),
            ),
        ),
    )
    _compact_layout(spec)
    assembler = _assembler(spec)
    dynamic = torch.tensor([[1.0, 0.125, 0.75, -0.25, 0.5]], dtype=torch.float32)

    assert spec.total_dims == 5
    assert spec.fixed_total_dims == 277
    expected = torch.zeros((1, spec.fixed_total_dims), dtype=torch.float32)
    expected[0, 0] = 1.0
    expected[0, 1:] = torch.tensor(fixed_payload)
    for feature, value in zip(
        ("position_0", "position_1", "egocentric_0", "egocentric_1"),
        dynamic[0, 1:],
        strict=True,
    ):
        expected[0, 1 + PAYLOAD_SCHEMAS["affordance"].index(feature)] = value
    expanded = assembler.expand_type("affordance", dynamic.view(1, 1, 5))
    assert expanded.shape == (1, 1, 277)
    assert torch.equal(expanded[:, 0, :], expected)


def test_presence_gates_compiled_static_context() -> None:
    signature = (0.5,) * AFFORDANCE_SIGNATURE_WIDTH
    static_feature_names = tuple(
        feature
        for feature in PAYLOAD_SCHEMAS["affordance"]
        if not feature.startswith("position_") and not feature.startswith("egocentric_")
    )
    fixed_payload = _fixed_payload(
        "affordance",
        dict(zip(static_feature_names, signature, strict=True)) | {"position_rank": 2 / MAX_POSITION_RANK},
    )
    spec = _token_spec(
        position_rank=2,
        types=(
            _build_token_type(
                "affordance",
                (
                    SlotBinding(
                        slot_index=0,
                        filler_kind="static",
                        filler_ref="affordance:cafe[0]",
                    ),
                ),
                slot_context_payloads=(fixed_payload,),
            ),
        ),
    )
    _compact_layout(spec)
    assembler = _assembler(spec)
    present = torch.tensor([[1.0, 0.1, 0.2, -0.3, 0.4]], dtype=torch.float32)
    absent_with_garbage = present.clone()
    absent_with_garbage[0, 0] = 0.0

    assembled_present = assembler.expand_type("affordance", present.view(1, 1, 5))
    assembled_absent = assembler.expand_type("affordance", absent_with_garbage.view(1, 1, 5))

    assert assembled_present.abs().sum() > 0
    assert torch.equal(assembled_absent, torch.zeros_like(assembled_absent))


def test_effect_context_selector_assembles_world_specific_static_identity_without_projection() -> None:
    declarations = (
        EffectDeclaration(id="regen", scope="agent", duration=10, reapply_policy="renew"),
        EffectDeclaration(id="shield", scope="agent", duration=8, reapply_policy="replace"),
        EffectDeclaration(id="poison", scope="agent", duration=5, reapply_policy="stack"),
    )
    signatures = tuple(effect_static_payload(declaration) for declaration in declarations)
    fixed_payloads = tuple(_fixed_payload("effect", dict(zip(EFFECT_STATIC_FEATURES, signature, strict=True))) for signature in signatures)
    spec = _token_spec(
        position_rank=2,
        types=(
            _build_token_type(
                "effect",
                (SlotBinding(slot_index=0, filler_kind="dynamic", filler_ref="effect:0"),),
                effect_catalog_contexts=tuple(
                    _context(context_ref=f"effect:{declaration.id}", fixed_payload=fixed_payload)
                    for declaration, fixed_payload in zip(declarations, fixed_payloads, strict=True)
                ),
            ),
        ),
    )
    layout = _compact_layout(spec)
    assembler = _assembler(spec)
    # Two worlds occupy the same runtime slot with identical live state but different
    # declared effect definitions. The raw exact-integral context index is transport
    # metadata only; using index 2 makes accidental [0, 1] normalization observable.
    selected_context_indices = (0, 2)
    dynamic = torch.tensor(
        [
            [1.0, 0.0, 0.75, 0.5, 0.25, 1.0],
            [1.0, 2.0, 0.75, 0.5, 0.25, 1.0],
        ],
        dtype=torch.float32,
    )

    effect_layout = layout.get_type("effect")
    assert effect_layout is not None
    assert effect_layout.dynamic_features == (
        "presence",
        "context_index",
        "remaining_fraction",
        "live_intensity",
        "owner_slot",
        "owner_slot_applicable",
    )
    assert "context_index" not in PAYLOAD_SCHEMAS["effect"]
    assert dynamic[:, 1].tolist() == [0.0, 2.0]

    assert spec.total_dims == 6
    assert spec.fixed_total_dims == 14
    expected = torch.zeros((2, spec.fixed_total_dims), dtype=torch.float32)
    expected[:, 0] = 1.0
    for world, context_index in enumerate(selected_context_indices):
        expected[world, 1:] = torch.tensor(fixed_payloads[context_index])
        for feature, value in zip(
            ("remaining_fraction", "live_intensity", "owner_slot", "owner_slot_applicable"),
            dynamic[world, 2:],
            strict=True,
        ):
            expected[world, 1 + PAYLOAD_SCHEMAS["effect"].index(feature)] = value

    expanded = assembler.expand_type("effect", dynamic.view(2, 1, 6))
    assert expanded.shape == (2, 1, 14)
    assert torch.equal(expanded[:, 0, :], expected)
    assert not torch.equal(
        expanded[0, 0, 1 : 1 + len(EFFECT_STATIC_FEATURES)],
        expanded[1, 0, 1 : 1 + len(EFFECT_STATIC_FEATURES)],
    )


@pytest.mark.parametrize(
    "type_name",
    ("self", "meter", "affordance", "agent", "item", "effect", "variable_element"),
)
def test_each_compact_token_type_expands_one_type_at_a_time(type_name: str) -> None:
    spec = _single_type_spec(type_name)
    schema = spec.get_type(type_name)
    type_layout = spec.compact_layout().get_type(type_name)
    assert schema is not None and type_layout is not None
    dynamic_rows = torch.zeros((1, schema.capacity, type_layout.compact_row_width), dtype=torch.float32)
    for slot in range(schema.capacity):
        dynamic_rows[0, slot, 0] = 1.0
        for lane, feature in enumerate(type_layout.dynamic_features[1:], start=1):
            dynamic_rows[0, slot, lane] = float(slot) if feature == "context_index" else (lane + slot) / 16.0

    expected = torch.zeros((1, schema.capacity, schema.fixed_row_width), dtype=torch.float32)
    for slot in range(schema.capacity):
        context = schema.effect_catalog_contexts[slot].fixed_payload if type_name == "effect" else schema.slot_context_payloads[slot]
        expected[0, slot, 1:] = torch.tensor(context, dtype=torch.float32)
        for lane, fixed_index in enumerate(type_layout.fixed_scatter_indices):
            if fixed_index is not None:
                expected[0, slot, fixed_index] = dynamic_rows[0, slot, lane]

    expanded = _assembler(spec).expand_type(type_name, dynamic_rows)

    assert expanded.shape == expected.shape
    assert torch.equal(expanded, expected)


@pytest.mark.parametrize(
    ("selector", "error"),
    (
        pytest.param(0.5, "integral", id="fractional"),
        pytest.param(-1.0, "range", id="negative"),
        pytest.param(2.0, "range", id="out-of-range"),
        pytest.param(float("nan"), "finite", id="nan"),
        pytest.param(float("inf"), "finite", id="positive-infinity"),
        pytest.param(float("-inf"), "finite", id="negative-infinity"),
        pytest.param(16_777_217.0, "exactly representable.*float32", id="float32-inexact"),
    ),
)
def test_present_effect_selector_refuses_before_catalog_gather(selector: float, error: str) -> None:
    spec = _single_type_spec("effect", capacity=1)
    dynamic_rows = torch.zeros((1, 1, 6), dtype=torch.float64)
    dynamic_rows[0, 0, 0] = 1.0
    dynamic_rows[0, 0, 1] = selector

    with pytest.raises(ValueError, match=error):
        _assembler(spec).expand_type("effect", dynamic_rows)


@pytest.mark.parametrize(
    "selector",
    (0.5, -1.0, 2.0, float("nan"), float("inf"), float("-inf"), 16_777_217.0),
    ids=("fractional", "negative", "out-of-range", "nan", "positive-infinity", "negative-infinity", "float32-inexact"),
)
def test_absent_effect_selector_is_ignored_and_returns_exact_zero(selector: float) -> None:
    spec = _single_type_spec("effect", capacity=1)
    dynamic_rows = torch.zeros((1, 1, 6), dtype=torch.float64)
    dynamic_rows[0, 0, 1] = selector

    expanded = _assembler(spec).expand_type("effect", dynamic_rows)

    assert torch.equal(expanded, torch.zeros_like(expanded))


def test_effect_selector_validation_handles_mixed_present_and_absent_batch() -> None:
    spec = _single_type_spec("effect", capacity=1)
    dynamic_rows = torch.tensor(
        [
            [[1.0, 0.0, 0.75, 0.5, 0.25, 1.0]],
            [[0.0, float("nan"), 0.75, 0.5, 0.25, 1.0]],
            [[1.0, 1.0, 0.75, 0.5, 0.25, 1.0]],
        ],
        dtype=torch.float32,
    )

    expanded = _assembler(spec).expand_type("effect", dynamic_rows)

    assert torch.equal(expanded[1], torch.zeros_like(expanded[1]))
    assert not torch.equal(expanded[0, 0, 1:], expanded[2, 0, 1:])


def test_present_effect_against_empty_catalog_refuses_before_gather() -> None:
    spec = _single_type_spec("effect", capacity=1, effect_catalog_size=0)
    dynamic_rows = torch.tensor([[[1.0, 0.0, 0.75, 0.5, 0.25, 1.0]]], dtype=torch.float32)

    with pytest.raises(ValueError, match="empty effect catalog"):
        _assembler(spec).expand_type("effect", dynamic_rows)
