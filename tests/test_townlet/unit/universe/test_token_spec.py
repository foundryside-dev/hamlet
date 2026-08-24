"""TokenSpec — the compiled token artifact and its pure derivations (unit 3, Task 6).

Spec: docs/superpowers/specs/2026-08-22-token-observation-representation-design.md §§1–2.
Nothing here is wired into the compiler yet (Task 7); every input is a synthetic declaration.
"""

from __future__ import annotations

import math
from typing import get_args

import pytest

from townlet.config.effects_config import EffectScope
from townlet.config.interaction_type import InteractionType
from townlet.universe.dto.token_spec import (
    DESCRIPTOR_BLOCK_WIDTH,
    DTYPE_FLAG_WIDTH,
    EFFECT_SUMMARY_K,
    LIFETIME_ONE_HOT_WIDTH,
    MAX_POSITION_RANK,
    MEAN_CENSUS_ADVISORY,
    METER_SIGNATURE_WIDTH,
    NORMALIZATION_KIND_ONE_HOT_WIDTH,
    NORMALIZATION_PARAM_VECTOR_WIDTH,
    OWNER_SLOT_COORDINATE_WIDTH,
    PAYLOAD_SCHEMAS,
    RESERVED_TOKEN_TYPE_NAMES,
    SCOPE_ONE_HOT_WIDTH,
    SEMANTIC_TYPE_ONE_HOT_WIDTH,
    TOKEN_TYPE_ROSTER,
    VALUE_BLOCK_WIDTH,
    ExposedVariable,
    MeterDeclaration,
    SlotBinding,
    TokenSpec,
    TokenTypeSchema,
    affordance_capacity,
    agent_capacity,
    build_token_type,
    check_indistinguishability,
    describe_variable,
    effect_capacity,
    item_capacity,
    mean_census_advisory,
    meter_capacity,
    meter_signature,
    require_exposure_normalization,
    require_position_rank,
    self_capacity,
    static_payload_signature,
    value_block_width_used,
    variable_element_capacity,
)
from townlet.vfs.schema import NormalizationSpec, VariableScope
from townlet.vfs.semantic_type import SEMANTIC_TYPES

# --------------------------------------------------------------------------- fixtures


def _minmax(lo: float = 0.0, hi: float = 1.0, clip: bool = True) -> NormalizationSpec:
    return NormalizationSpec(kind="minmax", min=lo, max=hi, clip=clip)


def _var(
    var_id: str = "world_temp",
    *,
    scope: str = "global",
    semantic_type: str = "custom",
    normalization: NormalizationSpec | None = None,
    var_type: str = "scalar",
    lifetime: str = "episode",
    default: object = 0.0,
    shape: tuple[int, ...] = (),
    owner_slot: int | None = None,
) -> ExposedVariable:
    return ExposedVariable(
        id=var_id,
        scope=scope,
        semantic_type=semantic_type,
        type=var_type,
        lifetime=lifetime,
        default=default,
        shape=shape,
        normalization=normalization if normalization is not None else _minmax(),
        owner_slot=owner_slot,
    )


def _meter(name: str = "energy", initial: float = 1.0, lo: float = 0.0, hi: float = 1.0) -> MeterDeclaration:
    return MeterDeclaration(
        name=name,
        initial=initial,
        min=lo,
        max=hi,
        lethal_min=True,
        lethal_max=False,
        passive_depletion=0.01,
        move_depletion=0.02,
        interact_depletion=0.05,
        natural_recovery=0.0,
    )


def _static_bindings(n: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=f"{prefix}:{i}") for i in range(n))


def _dynamic_bindings(n: int, prefix: str) -> tuple[SlotBinding, ...]:
    return tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{prefix}:{i}") for i in range(n))


# --------------------------------------------------------------------------- roster


class TestRoster:
    def test_roster_order_is_stable_and_seven_live(self):
        assert TOKEN_TYPE_ROSTER == ("self", "meter", "affordance", "agent", "item", "effect", "variable_element")
        assert set(PAYLOAD_SCHEMAS) == set(TOKEN_TYPE_ROSTER)

    def test_reserved_names_are_three_and_disjoint(self):
        assert RESERVED_TOKEN_TYPE_NAMES == frozenset({"relation", "message", "group"})
        assert not RESERVED_TOKEN_TYPE_NAMES & set(TOKEN_TYPE_ROSTER)

    @pytest.mark.parametrize("name", sorted(RESERVED_TOKEN_TYPE_NAMES))
    def test_reserved_name_refuses_instantiation(self, name: str):
        with pytest.raises(ValueError, match="reserved"):
            TokenTypeSchema(type_name=name, payload_features=("x",), capacity=0, slot_bindings=())

    def test_unknown_name_refuses(self):
        with pytest.raises(ValueError, match="closed roster"):
            TokenTypeSchema(type_name="raster", payload_features=("x",), capacity=0, slot_bindings=())

    def test_engine_constants(self):
        assert MAX_POSITION_RANK == 8
        assert VALUE_BLOCK_WIDTH == 2
        assert EFFECT_SUMMARY_K == 4
        assert MEAN_CENSUS_ADVISORY == 64


# --------------------------------------------------------------------------- descriptor block


class TestDescriptorBlock:
    def test_widths_derive_from_enums(self):
        assert SCOPE_ONE_HOT_WIDTH == len(VariableScope) == 9
        assert SEMANTIC_TYPE_ONE_HOT_WIDTH == len(SEMANTIC_TYPES) == 6
        assert NORMALIZATION_KIND_ONE_HOT_WIDTH == len(get_args(NormalizationSpec.model_fields["kind"].annotation)) == 9
        assert NORMALIZATION_PARAM_VECTOR_WIDTH == 5  # min, max, clip, scale + params-absent flag
        assert DTYPE_FLAG_WIDTH == 3
        assert LIFETIME_ONE_HOT_WIDTH == 3
        assert OWNER_SLOT_COORDINATE_WIDTH == 2

    def test_descriptor_block_width_is_pinned(self):
        # Single pin so drift is loud: 9 + 6 + 9 + 5 + 3 + 3 + 1 (initial) + 1 (log count) + 2.
        assert DESCRIPTOR_BLOCK_WIDTH == 39
        assert len(PAYLOAD_SCHEMAS["variable_element"]) == (MAX_POSITION_RANK + 1) + (VALUE_BLOCK_WIDTH + 1) + DESCRIPTOR_BLOCK_WIDTH

    def test_describe_variable_has_descriptor_width_and_marks_declaration(self):
        var = _var(normalization=_minmax(0.0, 10.0), default=5.0)
        block = describe_variable(var, element_index=0)
        assert len(block) == DESCRIPTOR_BLOCK_WIDTH
        scope_hot = block[:SCOPE_ONE_HOT_WIDTH]
        assert scope_hot[list(VariableScope).index(VariableScope.GLOBAL)] == 1.0 and sum(scope_hot) == 1.0
        # normalized declared initial = (5 - 0) / (10 - 0)
        assert block[-4] == pytest.approx(0.5)
        # element count log-scaled: log1p(1)
        assert block[-3] == pytest.approx(math.log1p(1))
        # no owner slot -> (0, applicable 0)
        assert block[-2:] == (0.0, 0.0)

    def test_owner_slot_coordinate_applies_to_item_profile_state(self):
        var = _var("durability", scope="item", owner_slot=3)
        block = describe_variable(var, element_index=0, owner_capacity=4)
        assert block[-2:] == (pytest.approx(3 / 4), 1.0)

    def test_tensor_elements_get_per_element_initial(self):
        var = _var(
            "temps",
            var_type="tensor1d",
            shape=(3,),
            default=[0.0, 5.0, 10.0],
            normalization=NormalizationSpec(kind="minmax", min=[0.0, 0.0, 0.0], max=[10.0, 10.0, 10.0], clip=True),
        )
        initials = [describe_variable(var, element_index=i)[-4] for i in range(3)]
        assert initials == pytest.approx([0.0, 0.5, 1.0])


# --------------------------------------------------------------------------- width rules


class TestWidthRules:
    def test_cyclical_sin_cos_is_one_token_both_lanes(self):
        spec = NormalizationSpec(kind="cyclical_sin_cos", period=24.0)
        require_exposure_normalization("day_phase", spec)
        assert value_block_width_used(spec) == 2 == VALUE_BLOCK_WIDTH
        var = _var("day_phase", normalization=spec, default=6.0)
        assert variable_element_capacity([var]) == 1

    def test_scalar_kinds_use_lane_zero_only(self):
        assert value_block_width_used(_minmax()) == 1
        assert value_block_width_used(NormalizationSpec(kind="binary", threshold=0.5)) == 1

    def test_one_hot_exposure_refuses(self):
        spec = NormalizationSpec(kind="one_hot", categories=4)
        with pytest.raises(ValueError, match="one_hot"):
            require_exposure_normalization("weather", spec)

    @pytest.mark.parametrize(
        "spec",
        [
            NormalizationSpec(kind="none"),
            NormalizationSpec(kind="zscore", mean=0.0, std=1.0),
            NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False),
            NormalizationSpec(kind="log_scaled", min=0.0, max=100.0, clip=False),
            NormalizationSpec(kind="masked_value", mask_value=-1.0, fill_value=0.0),
        ],
        ids=["none", "zscore", "unclipped_minmax", "unclipped_log", "masked_value"],
    )
    def test_unbounded_exposure_refuses(self, spec: NormalizationSpec):
        with pytest.raises(ValueError, match="bounded"):
            require_exposure_normalization("odometer", spec)

    def test_rank_scaled_exposure_refuses_naming_the_ruling(self):
        with pytest.raises(ValueError, match="rank_scaled.*hamlet-6a6e104523"):
            require_exposure_normalization("rank", NormalizationSpec(kind="rank_scaled"))

    def test_missing_normalization_at_exposure_refuses(self):
        with pytest.raises(ValueError, match="required at exposure"):
            require_exposure_normalization("raw", None)

    def test_bounded_kinds_pass(self):
        require_exposure_normalization("a", NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True))
        require_exposure_normalization("b", NormalizationSpec(kind="log_scaled", min=0.0, max=100.0, clip=True))
        require_exposure_normalization("c", NormalizationSpec(kind="binary", threshold=0.5))


# --------------------------------------------------------------------------- indistinguishability


class TestIndistinguishability:
    def test_identical_signatures_refuse_naming_both(self):
        a = _var("world_temp", default=0.3)
        b = _var("season_clock", default=0.3)
        with pytest.raises(ValueError, match="world_temp.*season_clock|season_clock.*world_temp"):
            check_indistinguishability([a, b])

    def test_one_distinguishing_parameter_compiles(self):
        a = _var("world_temp", default=0.3)
        b = _var("season_clock", default=0.3, lifetime="tick")
        check_indistinguishability([a, b])
        c = _var("season_clock", default=0.3, semantic_type="temporal")
        check_indistinguishability([a, c])
        d = _var("season_clock", default=0.3, normalization=_minmax(0.0, 24.0))
        check_indistinguishability([a, d])

    def test_different_declared_initial_distinguishes(self):
        a = _var("world_temp", default=0.3)
        b = _var("season_clock", default=0.7)
        check_indistinguishability([a, b])
        assert static_payload_signature(a) != static_payload_signature(b)

    def test_scope_is_part_of_coordinate_space(self):
        a = _var("x", scope="global")
        b = _var("y", scope="agent")
        check_indistinguishability([a, b])


# --------------------------------------------------------------------------- capacity


class TestCapacity:
    def test_self_and_meter(self):
        assert self_capacity() == 1
        assert meter_capacity([_meter("energy"), _meter("health")]) == 2

    def test_affordance_from_metadata_count(self):
        assert affordance_capacity(affordance_count=14) == 14

    def test_agent_capacity_zero_without_shared_world_declaration(self):
        assert agent_capacity(declared_agents_per_world=None) == 0
        assert agent_capacity(declared_agents_per_world=1) == 0
        assert agent_capacity(declared_agents_per_world=4) == 3

    def test_item_capacity_arithmetic(self):
        assert item_capacity(max_items_in_world=1, max_items_per_agent=1, declared_agents_per_world=None) == 2
        assert item_capacity(max_items_in_world=10, max_items_per_agent=3, declared_agents_per_world=4) == 22

    def test_effect_capacity_per_scope_budget_times_denominator(self):
        budgets = {"global": 2, "agent": 3, "item": 1, "affordance": 1}
        total = effect_capacity(
            max_active_effects=budgets,
            declared_effect_count=5,
            declared_agents_per_world=None,
            item_capacity_value=2,
            affordance_capacity_value=14,
        )
        assert total == 2 * 1 + 3 * 1 + 1 * 2 + 1 * 14

    def test_effect_capacity_budget_required_when_effects_declared(self):
        with pytest.raises(ValueError, match="max_active_effects"):
            effect_capacity(
                max_active_effects=None,
                declared_effect_count=1,
                declared_agents_per_world=None,
                item_capacity_value=0,
                affordance_capacity_value=0,
            )

    def test_effect_capacity_zero_when_no_effects_declared(self):
        assert (
            effect_capacity(
                max_active_effects=None,
                declared_effect_count=0,
                declared_agents_per_world=None,
                item_capacity_value=0,
                affordance_capacity_value=0,
            )
            == 0
        )

    def test_effect_budget_must_cover_every_scope(self):
        with pytest.raises(ValueError, match="item"):
            effect_capacity(
                max_active_effects={"global": 1, "agent": 1, "affordance": 1},
                declared_effect_count=1,
                declared_agents_per_world=None,
                item_capacity_value=0,
                affordance_capacity_value=0,
            )

    def test_variable_element_capacity_sums_elements(self):
        scalar = _var("a")
        tensor = _var(
            "b",
            var_type="tensor2d",
            shape=(2, 3),
            default=[[0.0] * 3] * 2,
            normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True),
        )
        assert variable_element_capacity([scalar, tensor]) == 1 + 6


# --------------------------------------------------------------------------- rank


class TestPositionRank:
    def test_rank_eight_accepted(self):
        require_position_rank(8, substrate_type="gridnd")

    def test_rank_nine_refuses_loudly(self):
        with pytest.raises(ValueError, match="MAX_POSITION_RANK"):
            require_position_rank(9, substrate_type="gridnd")

    def test_aspatial_rank_zero_accepted(self):
        require_position_rank(0, substrate_type="aspatial")


# --------------------------------------------------------------------------- payload schemas


class TestPayloadSchemas:
    def test_affordance_payload_layout(self):
        features = PAYLOAD_SCHEMAS["affordance"]
        n_interaction = len(get_args(InteractionType))
        assert n_interaction == 3
        assert [f for f in features if f.startswith("interaction_type_")] == [f"interaction_type_{t}" for t in get_args(InteractionType)]
        assert sum(f.startswith("position_") for f in features) == MAX_POSITION_RANK + 1
        assert sum(f.startswith("egocentric_") for f in features) == MAX_POSITION_RANK
        # K entries of (present, magnitude, sign, target signature) + the count feature.
        assert sum(f.startswith("effect_") for f in features) == EFFECT_SUMMARY_K * (3 + METER_SIGNATURE_WIDTH) + 1
        assert features[-1] == "effect_count"
        assert (
            len(features)
            == n_interaction + (MAX_POSITION_RANK + 1) + MAX_POSITION_RANK + EFFECT_SUMMARY_K * (3 + METER_SIGNATURE_WIDTH) + 1
        )

    def test_meter_payload_carries_value_block_and_signature(self):
        features = PAYLOAD_SCHEMAS["meter"]
        assert len(features) == (VALUE_BLOCK_WIDTH + 1) + METER_SIGNATURE_WIDTH
        sig = meter_signature(_meter("energy", initial=0.5, lo=0.0, hi=1.0))
        assert len(sig) == METER_SIGNATURE_WIDTH
        assert sig[0] == pytest.approx(0.5)

    def test_variable_element_payload_is_position_value_descriptor(self):
        features = PAYLOAD_SCHEMAS["variable_element"]
        assert features[: MAX_POSITION_RANK + 1] == tuple(f"position_{i}" for i in range(MAX_POSITION_RANK)) + ("position_rank",)
        assert features[MAX_POSITION_RANK + 1 : MAX_POSITION_RANK + 1 + VALUE_BLOCK_WIDTH + 1] == ("value_0", "value_1", "value_width_used")
        assert "presence" not in features

    def test_effect_payload_scope_one_hot_from_enum(self):
        features = PAYLOAD_SCHEMAS["effect"]
        assert [f for f in features if f.startswith("scope_")] == [f"scope_{s.value}" for s in EffectScope]

    def test_every_payload_is_unique_and_nonempty(self):
        for name, features in PAYLOAD_SCHEMAS.items():
            assert features, name
            assert len(set(features)) == len(features), name


# --------------------------------------------------------------------------- artifact + serialization


class TestTokenSpecArtifact:
    def _spec(self) -> TokenSpec:
        return TokenSpec(
            types=(
                build_token_type("self", _static_bindings(1, "self")),
                build_token_type("meter", _static_bindings(8, "meter")),
                build_token_type("affordance", _static_bindings(14, "aff")),
                build_token_type("agent", ()),
                build_token_type("item", _dynamic_bindings(2, "item")),
                build_token_type("effect", ()),
                build_token_type("variable_element", ()),
            )
        )

    def test_total_dims_equals_sum_formula(self):
        spec = self._spec()
        expected = sum(t.capacity * (1 + t.payload_width) for t in spec.types)
        assert spec.total_dims == expected
        assert spec.total_dims == 1 * (1 + len(PAYLOAD_SCHEMAS["self"])) + 8 * (1 + len(PAYLOAD_SCHEMAS["meter"])) + 14 * (
            1 + len(PAYLOAD_SCHEMAS["affordance"])
        ) + 2 * (1 + len(PAYLOAD_SCHEMAS["item"]))

    def test_census_counts(self):
        spec = self._spec()
        assert spec.census == {"self": 1, "meter": 8, "affordance": 14, "agent": 0, "item": 2, "effect": 0, "variable_element": 0}

    def test_row_layout_presence_leads_each_row(self):
        spec = self._spec()
        layout = spec.row_layout()
        offset = 0
        for type_name, slot, start, end in layout:
            assert start == offset
            assert end - start == 1 + len(PAYLOAD_SCHEMAS[type_name])
            offset = end
            assert slot >= 0
        assert offset == spec.total_dims

    def test_types_must_follow_roster_order(self):
        with pytest.raises(ValueError, match="roster order"):
            TokenSpec(types=(build_token_type("meter", ()), build_token_type("self", _static_bindings(1, "s"))))

    def test_duplicate_type_refuses(self):
        with pytest.raises(ValueError, match="duplicate"):
            TokenSpec(types=(build_token_type("self", ()), build_token_type("self", ())))

    def test_capacity_must_equal_bindings(self):
        with pytest.raises(ValueError, match="capacity"):
            TokenTypeSchema(
                type_name="meter", payload_features=PAYLOAD_SCHEMAS["meter"], capacity=3, slot_bindings=_static_bindings(2, "m")
            )

    def test_payload_features_must_match_engine_schema(self):
        with pytest.raises(ValueError, match="payload schema"):
            TokenTypeSchema(type_name="meter", payload_features=("wrong",), capacity=0, slot_bindings=())

    def test_slot_binding_indices_are_dense_from_zero(self):
        bad = (SlotBinding(slot_index=1, filler_kind="static", filler_ref="m:1"),)
        with pytest.raises(ValueError, match="slot_index"):
            build_token_type("meter", bad)

    def test_encoding_version(self):
        assert self._spec().encoding_version == "token-1.0"


# --------------------------------------------------------------------------- census advisory


class TestCensusAdvisory:
    def test_no_advisory_at_or_below_threshold(self):
        spec = TokenSpec(types=(build_token_type("affordance", _static_bindings(MEAN_CENSUS_ADVISORY, "a")),))
        assert mean_census_advisory(spec, aggregator="mean") is None

    def test_advisory_names_counts_when_any_type_exceeds(self):
        spec = TokenSpec(types=(build_token_type("affordance", _static_bindings(MEAN_CENSUS_ADVISORY + 1, "a")),))
        text = mean_census_advisory(spec, aggregator="mean")
        assert text is not None
        assert "affordance" in text and str(MEAN_CENSUS_ADVISORY + 1) in text and "64" in text

    def test_no_advisory_for_attention(self):
        spec = TokenSpec(types=(build_token_type("affordance", _static_bindings(MEAN_CENSUS_ADVISORY + 1, "a")),))
        assert mean_census_advisory(spec, aggregator="attention") is None
