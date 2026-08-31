"""Numeric representation boundary for the compiled token artifact.

The observation tensor is float32 and every compiler-owned static feature is a bounded
model input.  Finite Python floats are therefore not sufficient: declarations must
survive float32 tensorization without overflow, underflow, or semantic collapse.
"""

from __future__ import annotations

import math

import pytest

from townlet.universe.dto.token_spec import (
    DESCRIPTOR_BLOCK_WIDTH,
    ENCODING_VERSION,
    METER_SIGNATURE_FEATURES,
    METER_SIGNATURE_WIDTH,
    ExposedVariable,
    MeterDeclaration,
    SlotBinding,
    TokenSpec,
    build_token_type,
    describe_variable,
    meter_signature,
)
from townlet.vfs.schema import NormalizationSpec


def _meter(
    *,
    normalization: NormalizationSpec | None = None,
    initial: float | None = None,
    minimum: float = 0.0,
    maximum: float = 100.0,
    passive_depletion: float = 1.0,
    move_depletion: float = 0.0,
    interact_depletion: float = 0.0,
    natural_recovery: float = 0.0,
) -> MeterDeclaration:
    return MeterDeclaration(
        name="energy",
        normalization=normalization or NormalizationSpec(kind="minmax", min=minimum, max=maximum, clip=True),
        initial=minimum if initial is None else initial,
        min=minimum,
        max=maximum,
        lethal_min=True,
        lethal_max=False,
        passive_depletion=passive_depletion,
        move_depletion=move_depletion,
        interact_depletion=interact_depletion,
        natural_recovery=natural_recovery,
    )


def _variable(normalization: NormalizationSpec, *, shape: tuple[int, ...] = ()) -> ExposedVariable:
    return ExposedVariable(
        id="world.signal",
        scope="global",
        semantic_type="custom",
        type="scalar" if not shape else "tensor1d",
        lifetime="episode",
        default=0.0,
        shape=shape,
        normalization=normalization,
    )


def test_token_spec_refuses_noncanonical_encoding_version() -> None:
    with pytest.raises(ValueError, match=rf"encoding_version.*{ENCODING_VERSION}"):
        TokenSpec(types=(), encoding_version="token-arbitrary")


def test_static_signatures_are_bounded_model_inputs() -> None:
    binding = SlotBinding(
        slot_index=0,
        filler_kind="static",
        filler_ref="meter:energy",
        static_signature=(1.000001,) + (0.0,) * (METER_SIGNATURE_WIDTH - 1),
    )

    with pytest.raises(ValueError, match=r"static_signature.*\[-1, 1\]"):
        build_token_type("meter", (binding,))


def test_static_signatures_are_canonical_float32_values() -> None:
    binding = SlotBinding(
        slot_index=0,
        filler_kind="static",
        filler_ref="meter:energy",
        static_signature=(0.1,) + (0.0,) * (METER_SIGNATURE_WIDTH - 1),
    )

    schema = build_token_type("meter", (binding,))

    assert schema.slot_bindings[0].static_signature is not None
    assert schema.slot_bindings[0].static_signature[0] == pytest.approx(0.1)
    assert schema.slot_bindings[0].static_signature[0] != 0.1


def test_variable_descriptor_saturates_authored_magnitudes_and_element_count() -> None:
    variable = _variable(
        NormalizationSpec(kind="minmax", min=-1.0e20, max=1.0e20, clip=True),
        shape=(1_000_000_000,),
    )

    descriptor = describe_variable(variable, element_index=0, owner_capacity=None)

    assert len(descriptor) == DESCRIPTOR_BLOCK_WIDTH
    assert all(-1.0 <= feature <= 1.0 for feature in descriptor)


def test_meter_rate_signature_preserves_direction() -> None:
    depletion = meter_signature(_meter(passive_depletion=-2.0))
    recovery = meter_signature(_meter(passive_depletion=2.0))
    rate_index = METER_SIGNATURE_FEATURES.index("passive_depletion")

    assert depletion[rate_index] < 0.0 < recovery[rate_index]
    assert depletion[rate_index] == -recovery[rate_index]


@pytest.mark.parametrize(
    "rate_name",
    ("passive_depletion", "move_depletion", "interact_depletion", "natural_recovery"),
)
@pytest.mark.parametrize("bad_rate", (1.0e39, -1.0e39, 1.0e-50, -1.0e-50))
def test_meter_refuses_rates_that_change_meaning_in_float32(rate_name: str, bad_rate: float) -> None:
    with pytest.raises(ValueError, match=rf"{rate_name}.*float32"):
        _meter(**{rate_name: bad_rate})


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    (
        pytest.param(1.0, 1.00000001, id="ordered-bounds-collapse"),
        pytest.param(-3.0e38, 3.0e38, id="span-overflows"),
    ),
)
def test_meter_refuses_ranges_whose_float32_arithmetic_is_not_finite_and_ordered(
    minimum: float,
    maximum: float,
) -> None:
    normalization = NormalizationSpec(kind="minmax", min=minimum, max=maximum, clip=True)

    with pytest.raises(ValueError, match=r"float32"):
        _meter(normalization=normalization, minimum=minimum, maximum=maximum)


def test_meter_refuses_an_authored_interior_initial_that_collapses_to_a_bound() -> None:
    with pytest.raises(ValueError, match=r"initial.*float32"):
        _meter(initial=1.00000001, minimum=1.0, maximum=2.0)


@pytest.mark.parametrize(
    "normalization",
    (
        pytest.param(NormalizationSpec(kind="binary", threshold=1.0e300), id="binary-overflow"),
        pytest.param(NormalizationSpec(kind="cyclical_sin_cos", period=1.0e-50), id="period-underflow"),
        pytest.param(NormalizationSpec(kind="cyclical_sin_cos", period=1.0e-38), id="period-factor-overflow"),
    ),
)
def test_meter_normalization_refuses_values_not_representable_as_float32(
    normalization: NormalizationSpec,
) -> None:
    with pytest.raises(ValueError, match=r"float32"):
        _meter(normalization=normalization)


def test_meter_range_refuses_bounds_that_collapse_in_float32() -> None:
    normalization = NormalizationSpec(kind="minmax", min=1.0e-50, max=2.0e-50, clip=True)

    with pytest.raises(ValueError, match=r"float32"):
        _meter(normalization=normalization, minimum=1.0e-50, maximum=2.0e-50)


def test_variable_normalization_refuses_values_not_representable_as_float32() -> None:
    variable = _variable(NormalizationSpec(kind="binary", threshold=1.0e300))

    with pytest.raises(ValueError, match=r"float32"):
        describe_variable(variable, element_index=0, owner_capacity=None)


@pytest.mark.parametrize("bad_default", (1.0e39, -1.0e39, 1.0e-50, -1.0e-50))
def test_exposed_variable_refuses_defaults_that_change_meaning_in_float32(bad_default: float) -> None:
    variable = ExposedVariable(
        id="world.signal",
        scope="global",
        semantic_type="custom",
        type="scalar",
        lifetime="episode",
        default=bad_default,
        shape=(),
        normalization=NormalizationSpec(kind="minmax", min=-1.0, max=1.0, clip=True),
    )

    with pytest.raises(ValueError, match=r"default.*float32"):
        describe_variable(variable, element_index=0, owner_capacity=None)


def test_meter_signature_is_finite_and_bounded_float32() -> None:
    signature = meter_signature(_meter(passive_depletion=-2.0, natural_recovery=3.0))

    assert all(math.isfinite(feature) and -1.0 <= feature <= 1.0 for feature in signature)
