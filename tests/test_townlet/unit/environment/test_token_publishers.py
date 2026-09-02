"""Token publishers + TokenObservationEncoder (token-obs unit 3, Task 8 — ALONGSIDE).

Everything here drives the new machinery directly with SYNTHETIC declarations (the
Task-7 pattern): no shipped pack gives `agent`/`effect`/`variable_element` capacity
today, so their wiring is pinned against constructed TokenTypeSchemas. The pins:

- per-type wiring: declare -> exactly that token's row moves;
- presence legitimately-zero != absent (a zero VALUE keeps presence 1; an absent
  dynamic slot is presence 0 with zeroed payload);
- overflow at capacity+1 raises naming type, capacity, source;
- `agent_private` never lands in any agent's rows — the registry publisher is the
  enforcement point (hamlet-83a043a9b9 by mechanism), refusing BEFORE slot binding;
- visibility filter + egocentric wrap ride the substrate contract;
- replay aliasing: two consecutive encoded ticks never share storage.
"""

import inspect
from types import SimpleNamespace

import pytest
import torch

import townlet.environment.token_publishers as token_publishers
from townlet.agent.token_input import TokenInputAssembler
from townlet.config.affordances_v2_config import AffordanceParamConfig, DeploymentConfig, OpeningHoursConfig
from townlet.effects.affordance_identity import AffordanceMeterWrite
from townlet.environment.observation_encoder import TokenObservationEncoder, build_token_observation_encoder
from townlet.environment.token_publishers import (
    AffordanceTokenPublisher,
    AgentSlotBatch,
    AgentTokenPublisher,
    CompiledValueNormalizer,
    EffectSlotBatch,
    EffectTokenPublisher,
    ItemArenaVariableElementPublisher,
    ItemSlotBatch,
    ItemStateSlotDeclaration,
    ItemTokenPublisher,
    MeterTokenPublisher,
    RegistryVariableElementPublisher,
    SelfTokenPublisher,
    TokenCapacityError,
    TokenPublishContext,
    bind_dynamic_slots,
    parse_filler_ref,
)
from townlet.substrate.aspatial import AspatialSubstrate
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.universe.dto.token_spec import (
    AFFORDANCE_DURATION_FEATURES,
    DESCRIPTOR_BLOCK_WIDTH,
    EFFECT_STATIC_FEATURES,
    INTERACTION_TYPE_VOCABULARY,
    MAX_POSITION_RANK,
    OPENING_HOURS_FEATURES,
    PAYLOAD_SCHEMAS,
    TOKEN_TRANSPORT_VERSION,
    TOKEN_TYPE_ROSTER,
    VALUE_BLOCK_WIDTH,
    EffectDeclaration,
    MeterDeclaration,
    SlotBinding,
    TokenContext,
    TokenSpec,
    affordance_signature,
    build_token_type,
    effect_static_payload,
    element_coordinate_block,
    meter_signature,
    value_block_width_used,
)
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import NormalizationSpec, VariableDef

DEVICE = torch.device("cpu")


def _substrate(boundary: str = "clamp") -> Grid2DSubstrate:
    return Grid2DSubstrate(width=8, height=8, boundary=boundary, distance_metric="manhattan")


def _payload(type_name: str, values: dict[str, float] | None = None) -> tuple[float, ...]:
    payload = [0.0] * len(PAYLOAD_SCHEMAS[type_name])
    for feature, value in (values or {}).items():
        payload[PAYLOAD_SCHEMAS[type_name].index(feature)] = value
    return tuple(payload)


def _static_type(type_name: str, refs: list[str], contexts: list[tuple[float, ...]] | None = None):
    if contexts is None:
        contexts = [_payload(type_name) for _ in refs]
    assert len(contexts) == len(refs)
    return build_token_type(
        type_name,
        tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=ref) for i, ref in enumerate(refs)),
        slot_context_payloads=contexts,
        effect_catalog_contexts=(),
    )


def _dynamic_type(type_name: str, capacity: int):
    bindings = tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{type_name}:{i}") for i in range(capacity))
    return build_token_type(
        type_name,
        bindings,
        slot_context_payloads=() if type_name == "effect" else tuple(_payload(type_name) for _ in bindings),
        effect_catalog_contexts=(),
    )


def _rows(capacity: int, type_name: str, batch: int = 2) -> torch.Tensor:
    if type_name in {"self", "meter", "affordance", "variable_element"}:
        schema = _static_type(type_name, [f"{type_name}:{index}" for index in range(capacity)])
    else:
        schema = _dynamic_type(type_name, capacity)
    width = _layout(schema).compact_row_width
    return torch.zeros((batch, capacity, width), dtype=torch.float32)


def _lane(type_name: str, feature: str) -> int:
    if type_name in {"self", "meter", "affordance", "variable_element"}:
        schema = _static_type(type_name, [f"{type_name}:0"])
    else:
        schema = _dynamic_type(type_name, 1)
    return _layout(schema).dynamic_features.index(feature)


def _spec(schema) -> TokenSpec:
    return TokenSpec(types=(schema,), position_rank=2, transport_version=TOKEN_TRANSPORT_VERSION)


def _layout(schema):
    layout = _spec(schema).compact_layout().get_type(schema.type_name)
    assert layout is not None
    return layout


def _expand(schema, rows: torch.Tensor) -> torch.Tensor:
    return TokenInputAssembler(_spec(schema)).expand_type(schema.type_name, rows)


_METERS = [
    MeterDeclaration(
        name="energy",
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True),
        initial=0.8,
        min=0.0,
        max=1.0,
        lethal_min=True,
        lethal_max=False,
        passive_depletion=0.005,
        move_depletion=0.006,
        interact_depletion=0.0,
        natural_recovery=0.0,
    ),
    MeterDeclaration(
        name="money",
        normalization=NormalizationSpec(kind="minmax", min=0.0, max=100.0, clip=True),
        initial=50.0,
        min=0.0,
        max=100.0,
        lethal_min=False,
        lethal_max=False,
        passive_depletion=0.0,
        move_depletion=0.0,
        interact_depletion=0.0,
        natural_recovery=0.0,
    ),
]
_METER_COLUMNS = {"energy": 0, "money": 1}
_BOUNDED = NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True)


def _meter_type(meters: list[MeterDeclaration]):
    contexts = [_meter_context(meter) for meter in meters]
    return _static_type("meter", [meter.name for meter in meters], contexts)


def _meter_context(meter: MeterDeclaration) -> tuple[float, ...]:
    signature_start = PAYLOAD_SCHEMAS["meter"].index("initial")
    payload = list(_payload("meter"))
    signature = meter_signature(meter)
    payload[signature_start : signature_start + len(signature)] = signature
    payload[PAYLOAD_SCHEMAS["meter"].index("value_width_used")] = value_block_width_used(meter.normalization) / VALUE_BLOCK_WIDTH
    return tuple(payload)


def _sig(seed: float) -> tuple[float, ...]:
    return tuple((seed + i) / 100.0 for i in range(DESCRIPTOR_BLOCK_WIDTH))


def _var(name: str, *, scope: str = "global", normalization=_BOUNDED, dims: int | None = None, default=0.0) -> VariableDef:
    is_vector = dims is not None and dims > 1
    return VariableDef(
        id=name,
        scope=scope,
        type="vecNf" if is_vector else "scalar",
        dims=dims if is_vector else None,
        lifetime="episode",
        readable_by=["agent", "engine"],
        writable_by=["engine"],
        default=[0.0] * dims if is_vector else default,
        description=f"test {name}",
        normalization=normalization,
    )


class TestHelpers:
    def test_element_coordinate_block_is_not_reexported_by_publishers(self):
        assert not hasattr(token_publishers, "element_coordinate_block")

    def test_parse_filler_ref(self):
        assert parse_filler_ref("temp") == ("temp", 0)
        assert parse_filler_ref("wind[2]") == ("wind", 2)

    def test_element_coordinate_block_scalar_is_rank_zero(self):
        block = element_coordinate_block((), 0)
        assert block == (0.0,) * MAX_POSITION_RANK + (0.0,)

    def test_element_coordinate_block_matrix(self):
        # shape (2, 3), element 5 = (row 1, col 2): coords 1/1 and 2/2, rank 2/8.
        block = element_coordinate_block((2, 3), 5)
        assert block[0] == 1.0
        assert block[1] == 1.0
        assert block[MAX_POSITION_RANK] == 2 / MAX_POSITION_RANK

    def test_bind_dynamic_slots_overflow_names_type_capacity_source(self):
        with pytest.raises(TokenCapacityError) as excinfo:
            bind_dynamic_slots("item", 2, torch.tensor([0, 1, 2]), source="item_manager")
        message = str(excinfo.value)
        assert "'item'" in message
        assert "capacity is 2" in message
        assert "3 live instance(s)" in message
        assert "item_manager" in message

    def test_bind_dynamic_slots_duplicate_refuses(self):
        with pytest.raises(ValueError, match="duplicate slot"):
            bind_dynamic_slots("item", 3, torch.tensor([1, 1]), source="test")

    def test_bind_dynamic_slots_out_of_range_refuses(self):
        with pytest.raises(ValueError, match="out of range"):
            bind_dynamic_slots("item", 2, torch.tensor([2]), source="test")


class TestCompiledValueNormalizer:
    def test_minmax_and_binary_and_cyclical_batched(self):
        normalizer = CompiledValueNormalizer(
            [
                ("a", NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True), 0, 1),
                ("b", NormalizationSpec(kind="binary", threshold=0.5), 0, 1),
                ("c", NormalizationSpec(kind="cyclical_sin_cos", period=24.0), 0, 1),
                ("d", NormalizationSpec(kind="log_scaled", min=0.0, max=100.0, clip=True), 0, 1),
            ],
            DEVICE,
        )
        values = torch.tensor([[5.0, 0.5, 6.0, 100.0]])
        lanes = normalizer.apply(values)
        assert lanes.shape == (1, 4, VALUE_BLOCK_WIDTH)
        assert lanes[0, 0, 0].item() == pytest.approx(0.5)
        assert lanes[0, 0, 1].item() == 0.0
        # binary mirrors the live ABI's STRICT comparison (value > threshold).
        assert lanes[0, 1, 0].item() == 0.0
        assert lanes[0, 2, 0].item() == pytest.approx(1.0)  # sin(pi/2), 6/24 of a period
        assert lanes[0, 2, 1].item() == pytest.approx(0.0, abs=1e-6)  # cos(pi/2)
        assert lanes[0, 3, 0].item() == pytest.approx(1.0)
        assert normalizer.width_used.tolist() == [1.0, 1.0, 2.0, 1.0]

    def test_clamps_out_of_range(self):
        normalizer = CompiledValueNormalizer([("a", NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=True), 0, 1)], DEVICE)
        lanes = normalizer.apply(torch.tensor([[7.0]]))
        assert lanes[0, 0, 0].item() == 1.0

    def test_refused_kind_refuses_at_construction(self):
        with pytest.raises(ValueError, match="bounded normalization kind"):
            CompiledValueNormalizer([("a", NormalizationSpec(kind="zscore", mean=0.0, std=1.0), 0, 1)], DEVICE)


class TestSelfTokenPublisher:
    def test_position_and_velocity_wiring(self):
        context = _payload("self", {"position_rank": 2 / MAX_POSITION_RANK})
        schema = _static_type("self", ["self"], [context])
        publisher = SelfTokenPublisher(schema, _layout(schema), _substrate())
        rows = _rows(1, "self")
        ctx = TokenPublishContext(positions=torch.tensor([[0, 0], [7, 7]]), velocities=torch.tensor([[0.1, 0.2], [0.3, 0.4]]))
        publisher.publish(rows, ctx)
        assert rows[:, 0, 0].tolist() == [1.0, 1.0]
        pos0 = _lane("self", "position_0")
        assert rows[0, 0, pos0 : pos0 + 2].tolist() == [0.0, 0.0]
        assert rows[1, 0, pos0 : pos0 + 2].tolist() == [1.0, 1.0]
        expanded = _expand(schema, rows)
        position_rank = 1 + PAYLOAD_SCHEMAS["self"].index("position_rank")
        assert expanded[0, 0, position_rank].item() == pytest.approx(2 / MAX_POSITION_RANK)
        vel0 = _lane("self", "velocity_0")
        assert rows[1, 0, vel0 : vel0 + 2].tolist() == pytest.approx([0.3, 0.4])

    def test_missing_positions_refuses(self):
        schema = _static_type("self", ["self"])
        publisher = SelfTokenPublisher(schema, _layout(schema), _substrate())
        with pytest.raises(ValueError, match="positions"):
            publisher.publish(_rows(1, "self"), TokenPublishContext())


def test_rank_zero_publishers_have_no_position_lane_or_context_requirement():
    substrate = AspatialSubstrate()

    def rank_zero_layout(schema):
        spec = TokenSpec(types=(schema,), position_rank=0, transport_version=TOKEN_TRANSPORT_VERSION)
        layout = spec.compact_layout().get_type(schema.type_name)
        assert layout is not None
        return layout

    self_schema = _static_type("self", ["self"])
    self_layout = rank_zero_layout(self_schema)
    self_rows = torch.zeros((2, 1, self_layout.compact_row_width), dtype=torch.float32)
    SelfTokenPublisher(self_schema, self_layout, substrate).publish(self_rows, TokenPublishContext())
    assert self_layout.dynamic_features == ("presence",)
    assert self_rows.tolist() == [[[1.0]], [[1.0]]]

    affordance_schema = _static_type("affordance", ["affordance:0"])
    affordance_layout = rank_zero_layout(affordance_schema)
    affordance_rows = torch.zeros((2, 1, affordance_layout.compact_row_width), dtype=torch.float32)
    AffordanceTokenPublisher(affordance_schema, affordance_layout, substrate).publish(
        affordance_rows,
        TokenPublishContext(affordance_deployed=torch.tensor([True])),
    )
    assert affordance_layout.dynamic_features == ("presence",)
    assert affordance_rows.tolist() == [[[1.0]], [[1.0]]]

    agent_schema = _dynamic_type("agent", 1)
    agent_layout = rank_zero_layout(agent_schema)
    agent_rows = torch.zeros((2, 1, agent_layout.compact_row_width), dtype=torch.float32)
    AgentTokenPublisher(agent_schema, agent_layout, substrate).publish(
        agent_rows,
        TokenPublishContext(
            agent_slots=AgentSlotBatch(
                slot_indices=torch.tensor([0]),
                positions=torch.empty((1, 0), dtype=torch.long),
            )
        ),
    )
    assert agent_layout.dynamic_features == ("presence",)
    assert agent_rows.tolist() == [[[1.0]], [[1.0]]]

    item_schema = _dynamic_type("item", 1)
    item_layout = rank_zero_layout(item_schema)
    item_rows = torch.zeros((2, 1, item_layout.compact_row_width), dtype=torch.float32)
    ItemTokenPublisher(item_schema, item_layout, substrate, owner_slot_capacity=2).publish(
        item_rows,
        TokenPublishContext(
            item_slots=ItemSlotBatch(
                slot_indices=torch.tensor([0]),
                positions=torch.empty((1, 0), dtype=torch.long),
                vfs_indices=torch.tensor([0]),
                carried=torch.tensor([[False], [False]]),
                owner_slot=torch.tensor([-1]),
            )
        ),
    )
    assert item_layout.dynamic_features == (
        "presence",
        "carried",
        "owner_slot",
        "owner_slot_applicable",
    )
    assert item_rows[:, :, 0].tolist() == [[1.0], [1.0]]
    assert torch.count_nonzero(item_rows[:, :, 1:]) == 0


class TestMeterTokenPublisher:
    def _publisher(self):
        schema = _meter_type(_METERS)
        return MeterTokenPublisher(schema, _layout(schema), _METERS, _METER_COLUMNS, DEVICE)

    def test_declare_then_that_row_moves(self):
        publisher = self._publisher()
        rows = _rows(2, "meter")
        v0 = _lane("meter", "value_0")
        publisher.publish(rows, TokenPublishContext(meters=torch.tensor([[0.8, 25.0], [0.2, 100.0]])))
        assert rows[0, 0, v0].item() == pytest.approx(0.8)
        assert rows[0, 1, v0].item() == pytest.approx(0.25)  # money's DECLARED range position
        assert rows[1, 1, v0].item() == pytest.approx(1.0)

    def test_zero_value_is_present_not_absent(self):
        # Presence legitimately-zero != absent: a meter AT its min still publishes.
        publisher = self._publisher()
        rows = _rows(2, "meter")
        publisher.publish(rows, TokenPublishContext(meters=torch.zeros((2, 2))))
        assert rows[:, :, 0].tolist() == [[1.0, 1.0], [1.0, 1.0]]
        assert rows[0, 0, _lane("meter", "value_0")].item() == 0.0
        # ... and the static signature block still distinguishes the two meters.
        schema = _meter_type(_METERS)
        expanded = _expand(schema, rows)
        sig0 = 1 + PAYLOAD_SCHEMAS["meter"].index("initial")
        assert expanded[0, 0, sig0:].tolist() != expanded[0, 1, sig0:].tolist()

    def test_identity_uses_binding_refs_and_fixed_payload_uses_slot_contexts(self):
        schema = _meter_type([_METERS[1], _METERS[0]])
        rows = _rows(2, "meter", batch=1)

        MeterTokenPublisher(schema, _layout(schema), _METERS, _METER_COLUMNS, DEVICE).publish(
            rows,
            TokenPublishContext(meters=torch.tensor([[0.8, 25.0]])),
        )

        expanded = _expand(schema, rows)
        signature_start = 1 + PAYLOAD_SCHEMAS["meter"].index("initial")
        context_signature_start = PAYLOAD_SCHEMAS["meter"].index("initial")
        assert expanded[0, 0, signature_start:].tolist() == pytest.approx(schema.slot_context_payloads[0][context_signature_start:])
        assert expanded[0, 1, signature_start:].tolist() == pytest.approx(schema.slot_context_payloads[1][context_signature_start:])
        assert rows[0, 0, _lane("meter", "value_0")].item() == pytest.approx(0.25)
        assert rows[0, 1, _lane("meter", "value_0")].item() == pytest.approx(0.8)

    def test_unbound_meter_refuses_at_construction(self):
        schema = _static_type("meter", ["energy", "ghost"], [_meter_context(_METERS[0]), _meter_context(_METERS[1])])
        with pytest.raises(ValueError, match="undeclared meter 'ghost'"):
            MeterTokenPublisher(schema, _layout(schema), _METERS, _METER_COLUMNS, DEVICE)

    def test_duplicate_meter_declaration_refuses_before_dictionary_collapse(self):
        duplicate = [_METERS[0], _METERS[0]]
        with pytest.raises(ValueError, match="duplicate meter declaration.*energy"):
            schema = _meter_type(duplicate)
            MeterTokenPublisher(schema, _layout(schema), duplicate, {"energy": 0}, DEVICE)

    def test_meter_declaration_count_must_equal_compiled_capacity(self):
        with pytest.raises(ValueError, match="declaration count.*capacity"):
            schema = _meter_type([_METERS[0]])
            MeterTokenPublisher(schema, _layout(schema), _METERS, _METER_COLUMNS, DEVICE)

    def test_declared_range_type_drives_both_value_lanes_and_identity(self):
        common = {
            "initial": 0.0,
            "min": 0.0,
            "max": 99.0,
            "lethal_min": False,
            "lethal_max": False,
            "passive_depletion": 0.0,
            "move_depletion": 0.0,
            "interact_depletion": 0.0,
            "natural_recovery": 0.0,
        }
        meters = [
            MeterDeclaration(name="linear", normalization=NormalizationSpec(kind="minmax", min=0.0, max=99.0, clip=True), **common),
            MeterDeclaration(name="log", normalization=NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=True), **common),
            MeterDeclaration(name="clock", normalization=NormalizationSpec(kind="cyclical_sin_cos", period=24.0), **common),
            MeterDeclaration(name="switch", normalization=NormalizationSpec(kind="binary", threshold=0.5), **common),
        ]
        schema = _meter_type(meters)
        columns = {meter.name: index for index, meter in enumerate(meters)}
        rows = _rows(4, "meter", batch=1)

        MeterTokenPublisher(schema, _layout(schema), meters, columns, DEVICE).publish(
            rows,
            TokenPublishContext(meters=torch.tensor([[49.5, 9.0, 6.0, 0.5]])),
        )

        value0 = _lane("meter", "value_0")
        value1 = _lane("meter", "value_1")
        assert rows[0, 0, value0 : value1 + 1].tolist() == pytest.approx([0.5, 0.0])
        assert rows[0, 1, value0 : value1 + 1].tolist() == pytest.approx([0.5, 0.0])
        assert rows[0, 2, value0 : value1 + 1].tolist() == pytest.approx([1.0, 0.0], abs=1e-6)
        assert rows[0, 3, value0 : value1 + 1].tolist() == [0.0, 0.0]
        expanded = _expand(schema, rows)
        width = 1 + PAYLOAD_SCHEMAS["meter"].index("value_width_used")
        assert expanded[0, :, width].tolist() == [0.5, 0.5, 1.0, 0.5]

        signature = 1 + PAYLOAD_SCHEMAS["meter"].index("initial")
        assert len({tuple(expanded[0, index, signature:].tolist()) for index in range(4)}) == 4

    @pytest.mark.parametrize(
        ("meter_index", "kind"),
        (
            (0, "minmax"),
            (1, "log_scaled"),
            (2, "cyclical_sin_cos"),
            (3, "binary"),
        ),
    )
    @pytest.mark.parametrize(
        "bad_value",
        (
            pytest.param(float("nan"), id="nan"),
            pytest.param(float("inf"), id="positive_inf"),
            pytest.param(float("-inf"), id="negative_inf"),
        ),
    )
    def test_non_finite_live_meter_value_refuses_before_mutating_rows(self, meter_index: int, kind: str, bad_value: float):
        common = {
            "initial": 0.0,
            "min": 0.0,
            "max": 99.0,
            "lethal_min": False,
            "lethal_max": False,
            "passive_depletion": 0.0,
            "move_depletion": 0.0,
            "interact_depletion": 0.0,
            "natural_recovery": 0.0,
        }
        meters = [
            MeterDeclaration(name="linear", normalization=NormalizationSpec(kind="minmax", min=0.0, max=99.0, clip=True), **common),
            MeterDeclaration(name="log", normalization=NormalizationSpec(kind="log_scaled", min=0.0, max=99.0, clip=True), **common),
            MeterDeclaration(name="clock", normalization=NormalizationSpec(kind="cyclical_sin_cos", period=24.0), **common),
            MeterDeclaration(name="switch", normalization=NormalizationSpec(kind="binary", threshold=0.5), **common),
        ]
        rows = _rows(4, "meter", batch=1)
        before = rows.clone()
        values = [49.5, 9.0, 6.0, 1.0]
        values[meter_index] = bad_value

        with pytest.raises(ValueError, match=rf"non-finite live values.*{kind}"):
            MeterTokenPublisher(
                (schema := _meter_type(meters)),
                _layout(schema),
                meters,
                {meter.name: index for index, meter in enumerate(meters)},
                DEVICE,
            ).publish(rows, TokenPublishContext(meters=torch.tensor([values])))

        assert torch.equal(rows, before)

    def test_cyclical_factor_that_would_be_non_finite_refuses_at_declaration(self):
        with pytest.raises(ValueError, match="cyclical.*float32"):
            MeterDeclaration(
                name="clock",
                normalization=NormalizationSpec(kind="cyclical_sin_cos", period=1e-320),
                initial=0.0,
                min=0.0,
                max=1.0,
                lethal_min=False,
                lethal_max=False,
                passive_depletion=0.0,
                move_depletion=0.0,
                interact_depletion=0.0,
                natural_recovery=0.0,
            )

    def test_encoder_builds_meter_publisher_from_compiled_level_declarations(self):
        meter = MeterDeclaration(
            name="clock",
            initial=6.0,
            normalization=NormalizationSpec(kind="cyclical_sin_cos", period=24.0),
            min=0.0,
            max=24.0,
            lethal_min=False,
            lethal_max=False,
            passive_depletion=0.0,
            move_depletion=0.0,
            interact_depletion=0.0,
            natural_recovery=0.0,
        )
        env = SimpleNamespace(
            token_spec=TokenSpec(types=(_meter_type([meter]),), position_rank=2, transport_version=TOKEN_TRANSPORT_VERSION),
            level=SimpleNamespace(meter_declarations=(meter,)),
            meter_name_to_index={"clock": 0},
            device=DEVICE,
        )

        encoder = build_token_observation_encoder(env)
        observation = encoder.encode(1, TokenPublishContext(meters=torch.tensor([[6.0]])))

        value0 = _lane("meter", "value_0")
        value1 = _lane("meter", "value_1")
        assert observation[0, value0 : value1 + 1].tolist() == pytest.approx([1.0, 0.0], abs=1e-6)


_METERS_BY_NAME = {meter.name: meter for meter in _METERS}


def _affordance(name: str, interaction_type: str, duration_ticks: int | None = None) -> AffordanceParamConfig:
    return AffordanceParamConfig(
        name=name,
        interaction_type=interaction_type,  # type: ignore[arg-type]
        duration_ticks=duration_ticks,
        costs={},
        costs_per_tick={},
        interactions={"on_start": [], "per_tick": [], "on_completion": [], "on_early_exit": [], "on_failure": []},
        opening_hours=OpeningHoursConfig(enabled=False),
        deployment=DeploymentConfig(type="fixed", positions=[[0, 0]]),
    )


def _write(meter_name: str, delta: float) -> AffordanceMeterWrite:
    return AffordanceMeterWrite(meter_name, 1, delta, "on_start", "interaction", "target", None)


_AFFORDANCE_SIGNATURES = [
    affordance_signature(
        affordance=_affordance("EAT", "instant"),
        effect_deltas=(_write("energy", 0.3),),
        meters=_METERS_BY_NAME,
    ),
    affordance_signature(
        affordance=_affordance("SLEEP", "multi_tick", 3),
        effect_deltas=(
            _write("energy", 0.5),
            _write("money", -10.0),
        ),
        meters=_METERS_BY_NAME,
    ),
]


def _affordance_type():
    contexts: list[tuple[float, ...]] = []
    n_interactions = len(INTERACTION_TYPE_VOCABULARY)
    duration_start = n_interactions
    opening_start = duration_start + len(AFFORDANCE_DURATION_FEATURES)
    summary_start = opening_start + len(OPENING_HOURS_FEATURES)
    for signature in _AFFORDANCE_SIGNATURES:
        payload = list(_payload("affordance"))
        payload[:n_interactions] = signature[:n_interactions]
        payload[n_interactions : n_interactions + len(AFFORDANCE_DURATION_FEATURES)] = signature[duration_start:opening_start]
        payload[opening_start : opening_start + len(OPENING_HOURS_FEATURES)] = signature[opening_start:summary_start]
        effect_start = PAYLOAD_SCHEMAS["affordance"].index("effect_0_form")
        payload[effect_start : effect_start + len(signature[summary_start:-1])] = signature[summary_start:-1]
        payload[PAYLOAD_SCHEMAS["affordance"].index("effect_count")] = signature[-1]
        contexts.append(tuple(payload))
    return _static_type("affordance", ["EAT", "SLEEP"], contexts)


class TestAffordanceTokenPublisher:
    def _publisher(self, boundary: str = "clamp"):
        schema = _affordance_type()
        return AffordanceTokenPublisher(schema, _layout(schema), _substrate(boundary))

    def _ctx(self, positions, vision_range=None):
        return TokenPublishContext(
            positions=positions,
            affordance_positions=torch.tensor([[2, 3], [7, 7]]),
            affordance_deployed=torch.tensor([True, True]),
            vision_range=vision_range,
        )

    def test_full_observability_publishes_both_with_identity(self):
        publisher = self._publisher()
        schema = _affordance_type()
        rows = _rows(2, "affordance")
        publisher.publish(rows, self._ctx(torch.tensor([[0, 0], [4, 4]])))
        assert rows[:, :, 0].tolist() == [[1.0, 1.0], [1.0, 1.0]]
        expanded = _expand(schema, rows)
        it_instant = 1 + PAYLOAD_SCHEMAS["affordance"].index("interaction_type_instant")
        it_multi = 1 + PAYLOAD_SCHEMAS["affordance"].index("interaction_type_multi_tick")
        assert expanded[0, 0, it_instant].item() == 1.0 and expanded[0, 0, it_multi].item() == 0.0
        assert expanded[0, 1, it_multi].item() == 1.0
        # effect summary forms: +1 is an unconditional direct literal delta; 0 is absent.
        p0 = 1 + PAYLOAD_SCHEMAS["affordance"].index("effect_0_form")
        p1 = 1 + PAYLOAD_SCHEMAS["affordance"].index("effect_1_form")
        assert expanded[0, 0, p0].item() == 1.0 and expanded[0, 0, p1].item() == 0.0
        assert expanded[0, 1, p0].item() == 1.0 and expanded[0, 1, p1].item() == 1.0

    def test_egocentric_moves_with_the_agent(self):
        publisher = self._publisher()
        ego0 = _lane("affordance", "egocentric_0")
        rows_a = _rows(2, "affordance", batch=1)
        publisher.publish(rows_a, self._ctx(torch.tensor([[0, 0]])))
        rows_b = _rows(2, "affordance", batch=1)
        publisher.publish(rows_b, self._ctx(torch.tensor([[2, 3]])))
        assert rows_a[0, 0, ego0 : ego0 + 2].tolist() == pytest.approx([2 / 7, 3 / 7])
        assert rows_b[0, 0, ego0 : ego0 + 2].tolist() == [0.0, 0.0]  # standing on it = relative zero

    def test_visibility_zeroes_presence_and_payload(self):
        publisher = self._publisher()
        rows = _rows(2, "affordance", batch=1)
        # vision_range 0.5 on 8-wide grid -> radius 2. Agent at (0,0): EAT at (2,3) is
        # manhattan 5 (out), SLEEP at (7,7) is 14 (out).
        publisher.publish(rows, self._ctx(torch.tensor([[0, 0]]), vision_range=0.5))
        assert rows[0, :, 0].tolist() == [0.0, 0.0]
        assert rows.abs().sum().item() == 0.0  # payload zeroed, not just presence

    def test_visibility_is_per_agent(self):
        publisher = self._publisher()
        rows = _rows(2, "affordance")
        publisher.publish(rows, self._ctx(torch.tensor([[2, 2], [7, 6]]), vision_range=0.5))
        assert rows[:, :, 0].tolist() == [[1.0, 0.0], [0.0, 1.0]]

    def test_wrap_egocentric_shortest_path(self):
        publisher = self._publisher(boundary="wrap")
        rows = _rows(2, "affordance", batch=1)
        publisher.publish(rows, self._ctx(torch.tensor([[0, 0]])))
        ego0 = _lane("affordance", "egocentric_0")
        # SLEEP at (7,7) from (0,0) on a wrap 8x8: shortest path is (-1,-1)/7.
        assert rows[0, 1, ego0 : ego0 + 2].tolist() == pytest.approx([-1 / 7, -1 / 7])

    def test_wrong_shaped_position_matrix_refuses(self):
        # The matrix is COMPILED SLOT ORDER at the compiled capacity; a short one is an
        # engine bug and must be loud, never silently padded.
        publisher = self._publisher()
        ctx = TokenPublishContext(
            positions=torch.tensor([[0, 0]]),
            affordance_positions=torch.tensor([[2, 3]]),
            affordance_deployed=torch.tensor([True, True]),
        )
        with pytest.raises(ValueError, match=r"affordance_positions must be \[2, 2\]"):
            publisher.publish(_rows(2, "affordance", batch=1), ctx)

    def test_an_undeployed_declaration_is_absent_for_every_observer(self):
        # Capacity is the DECLARED affordance count; an undeployed instance is padding.
        publisher = self._publisher()
        rows = _rows(2, "affordance", batch=1)
        ctx = TokenPublishContext(
            positions=torch.tensor([[2, 3]]),
            affordance_positions=torch.tensor([[2, 3], [7, 7]]),
            affordance_deployed=torch.tensor([True, False]),
        )
        publisher.publish(rows, ctx)
        assert rows[0, 0, 0] == 1.0
        assert rows[0, 1, 0] == 0.0
        assert torch.all(rows[0, 1] == 0.0)


class TestAgentTokenPublisher:
    def test_capacity_zero_is_a_noop_and_never_keys_on_batch_size(self):
        # num_agents is a batch of independent worlds (Global Constraints): a 7-world
        # batch against capacity 0 publishes NOTHING and raises nothing.
        schema = _dynamic_type("agent", 0)
        publisher = AgentTokenPublisher(schema, _layout(schema), _substrate())
        rows = torch.zeros((7, 0, 1 + len(PAYLOAD_SCHEMAS["agent"])))
        publisher.publish(rows, TokenPublishContext(positions=torch.zeros((7, 2), dtype=torch.long)))
        assert rows.numel() == 0

    def test_synthetic_shared_world_slots_fill(self):
        schema = _dynamic_type("agent", 2)
        publisher = AgentTokenPublisher(schema, _layout(schema), _substrate())
        rows = _rows(2, "agent", batch=1)
        batch = AgentSlotBatch(slot_indices=torch.tensor([1]), positions=torch.tensor([[3, 4]]))
        publisher.publish(rows, TokenPublishContext(positions=torch.tensor([[0, 0]]), agent_slots=batch))
        assert rows[0, 0, 0].item() == 0.0  # unassigned slot: absent
        assert rows[0, 1, 0].item() == 1.0
        pos0 = _lane("agent", "position_0")
        assert rows[0, 1, pos0 : pos0 + 2].tolist() == pytest.approx([3 / 7, 4 / 7])

    def test_overflow_raises(self):
        schema = _dynamic_type("agent", 1)
        publisher = AgentTokenPublisher(schema, _layout(schema), _substrate())
        batch = AgentSlotBatch(slot_indices=torch.tensor([0, 1]), positions=torch.zeros((2, 2), dtype=torch.long))
        ctx = TokenPublishContext(positions=torch.zeros((1, 2), dtype=torch.long), agent_slots=batch)
        with pytest.raises(TokenCapacityError, match="'agent'"):
            publisher.publish(_rows(1, "agent", batch=1), ctx)


def _item_batch(slot_indices, positions, vfs_indices, carried, owner_slot):
    return ItemSlotBatch(
        slot_indices=torch.tensor(slot_indices),
        positions=torch.tensor(positions),
        vfs_indices=torch.tensor(vfs_indices),
        carried=torch.tensor(carried),
        owner_slot=torch.tensor(owner_slot),
    )


class TestItemTokenPublisher:
    def _publisher(self, capacity: int = 2):
        schema = _dynamic_type("item", capacity)
        return ItemTokenPublisher(schema, _layout(schema), _substrate(), owner_slot_capacity=2)

    def test_dynamic_presence_toggles_and_payload_fills(self):
        publisher = self._publisher()
        rows = _rows(2, "item", batch=1)
        batch = _item_batch([0], [[5, 5]], [0], [[False]], [-1])
        publisher.publish(rows, TokenPublishContext(positions=torch.tensor([[5, 5]]), item_slots=batch))
        assert rows[0, 0, 0].item() == 1.0
        assert rows[0, 1, 0].item() == 0.0  # absent slot stays absent with zero payload
        assert rows[0, 1].abs().sum().item() == 0.0
        assert rows[0, 0, _lane("item", "owner_slot_applicable")].item() == 0.0

    def test_carried_item_is_on_self_with_owner_coordinates(self):
        publisher = self._publisher()
        rows = _rows(2, "item", batch=1)
        batch = _item_batch([1], [[7, 7]], [3], [[True]], [1])
        publisher.publish(rows, TokenPublishContext(positions=torch.tensor([[0, 0]]), item_slots=batch, vision_range=0.5))
        # Out of range by position, but carried => visible to the carrying world.
        assert rows[0, 1, 0].item() == 1.0
        assert rows[0, 1, _lane("item", "carried")].item() == 1.0
        ego0 = _lane("item", "egocentric_0")
        assert rows[0, 1, ego0 : ego0 + 2].tolist() == [0.0, 0.0]  # carried = relative zero
        assert rows[0, 1, _lane("item", "owner_slot")].item() == pytest.approx(0.5)
        assert rows[0, 1, _lane("item", "owner_slot_applicable")].item() == 1.0

    def test_overflow_at_capacity_plus_one(self):
        publisher = self._publisher(capacity=2)
        batch = _item_batch([0, 1, 2], [[0, 0], [1, 1], [2, 2]], [0, 1, 2], [[False, False, False]], [-1, -1, -1])
        ctx = TokenPublishContext(positions=torch.zeros((1, 2), dtype=torch.long), item_slots=batch)
        with pytest.raises(TokenCapacityError) as excinfo:
            publisher.publish(_rows(2, "item", batch=1), ctx)
        assert excinfo.value.capacity == 2
        assert excinfo.value.requested == 3
        assert excinfo.value.source == "item_manager"


class TestEffectTokenPublisher:
    _DECLARATIONS = [
        EffectDeclaration(id="regen", scope="agent", duration=10, reapply_policy="renew"),
        EffectDeclaration(id="poison", scope="agent", duration=5, reapply_policy="stack"),
    ]

    @staticmethod
    def _schema(capacity: int, declarations: list[EffectDeclaration]):
        bindings = tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"effect:{i}") for i in range(capacity))
        contexts = []
        for declaration in declarations:
            payload = list(_payload("effect"))
            payload[: len(EFFECT_STATIC_FEATURES)] = effect_static_payload(declaration)
            contexts.append(TokenContext(context_ref=f"effect:{declaration.id}", fixed_payload=tuple(payload)))
        return build_token_type(
            "effect",
            bindings,
            slot_context_payloads=(),
            effect_catalog_contexts=tuple(contexts),
        )

    def test_constructor_has_no_declarations_authority(self):
        schema = self._schema(1, self._DECLARATIONS)
        assert "declarations" not in inspect.signature(EffectTokenPublisher).parameters
        with pytest.raises(TypeError, match="declarations"):
            EffectTokenPublisher(
                schema,
                _layout(schema),
                declarations=list(reversed(self._DECLARATIONS)),
                owner_slot_capacity=4,
            )

    def test_exact_static_payload_comes_from_compiled_catalog_context(self):
        schema = self._schema(1, self._DECLARATIONS)
        publisher = EffectTokenPublisher(schema, _layout(schema), owner_slot_capacity=4)
        rows = _rows(1, "effect", batch=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[1]]),
            remaining_fraction=torch.tensor([[0.6]]),
            intensity=torch.tensor([[2.0]]),
            active=torch.tensor([[True]]),
            owner_slot=torch.tensor([2]),
        )

        publisher.publish(rows, TokenPublishContext(effect_slots=batch))

        expected = schema.effect_catalog_contexts[1].fixed_payload[: len(EFFECT_STATIC_FEATURES)]
        expanded = _expand(schema, rows)
        assert expanded[0, 0, 1 : 1 + len(EFFECT_STATIC_FEATURES)].tolist() == pytest.approx(expected)

    def _publisher(self, capacity: int = 2):
        schema = self._schema(capacity, self._DECLARATIONS)
        return EffectTokenPublisher(schema, _layout(schema), owner_slot_capacity=4)

    def test_declared_identity_and_remaining_fraction(self):
        publisher = self._publisher()
        rows = _rows(2, "effect", batch=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[1]]),
            remaining_fraction=torch.tensor([[0.6]]),
            intensity=torch.tensor([[2.0]]),
            active=torch.tensor([[True]]),
            owner_slot=torch.tensor([2]),
        )
        publisher.publish(rows, TokenPublishContext(effect_slots=batch))
        assert rows[0, 0, 0].item() == 1.0
        assert rows[0, 0, _lane("effect", "remaining_fraction")].item() == pytest.approx(0.6)
        assert rows[0, 0, _lane("effect", "live_intensity")].item() == pytest.approx(2.0 / 3.0)
        expanded = _expand(self._schema(2, self._DECLARATIONS), rows)
        assert expanded[0, 0, 1 + PAYLOAD_SCHEMAS["effect"].index("reapply_stack")].item() == 1.0
        assert rows[0, 0, _lane("effect", "owner_slot")].item() == pytest.approx(0.5)
        assert rows[0, 1, 0].item() == 0.0

    def test_remaining_fraction_refuses_one_dimensional_broadcast_across_worlds(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[0], [1]]),
            remaining_fraction=torch.tensor([0.25]),
            intensity=torch.ones((2, 1)),
            active=torch.ones((2, 1), dtype=torch.bool),
            owner_slot=torch.tensor([-1]),
        )

        with pytest.raises(ValueError, match=r"remaining_fraction must be \[2, 1\], got \(1,\)"):
            publisher.publish(_rows(1, "effect", batch=2), TokenPublishContext(effect_slots=batch))

    def test_active_refuses_one_dimensional_broadcast_across_worlds(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[0], [1]]),
            remaining_fraction=torch.tensor([[0.25], [0.75]]),
            intensity=torch.ones((2, 1)),
            active=torch.tensor([True]),
            owner_slot=torch.tensor([-1]),
        )

        with pytest.raises(ValueError, match=r"active must be \[2, 1\], got \(1,\)"):
            publisher.publish(_rows(1, "effect", batch=2), TokenPublishContext(effect_slots=batch))

    @pytest.mark.parametrize("value", (float("nan"), float("inf"), float("-inf")), ids=("nan", "positive-infinity", "negative-infinity"))
    def test_remaining_fraction_refuses_nonfinite_values(self, value: float):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[0]]),
            remaining_fraction=torch.tensor([[value]]),
            intensity=torch.ones((1, 1)),
            active=torch.ones((1, 1), dtype=torch.bool),
            owner_slot=torch.tensor([-1]),
        )

        with pytest.raises(ValueError, match="remaining_fraction must be finite"):
            publisher.publish(_rows(1, "effect", batch=1), TokenPublishContext(effect_slots=batch))

    def test_remaining_fraction_requires_a_floating_tensor(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[0]]),
            remaining_fraction=torch.tensor([[1]], dtype=torch.int64),
            intensity=torch.ones((1, 1)),
            active=torch.ones((1, 1), dtype=torch.bool),
            owner_slot=torch.tensor([-1]),
        )

        with pytest.raises(ValueError, match="remaining_fraction must use a floating dtype"):
            publisher.publish(_rows(1, "effect", batch=1), TokenPublishContext(effect_slots=batch))

    def test_remaining_fraction_preserves_distinct_per_world_values(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([[0], [1]]),
            remaining_fraction=torch.tensor([[0.25], [0.75]]),
            intensity=torch.ones((2, 1)),
            active=torch.ones((2, 1), dtype=torch.bool),
            owner_slot=torch.tensor([-1]),
        )
        rows = _rows(1, "effect", batch=2)

        publisher.publish(rows, TokenPublishContext(effect_slots=batch))

        assert rows[:, 0, _lane("effect", "remaining_fraction")].tolist() == pytest.approx([0.25, 0.75])

    def test_overflow_names_source(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0, 1]),
            effect_indices=torch.tensor([[0, 1]]),
            remaining_fraction=torch.ones((1, 2)),
            intensity=torch.ones((1, 2)),
            active=torch.ones((1, 2), dtype=torch.bool),
            owner_slot=torch.tensor([-1, -1]),
        )
        with pytest.raises(TokenCapacityError, match="effect_manager"):
            publisher.publish(_rows(1, "effect", batch=1), TokenPublishContext(effect_slots=batch))

    def test_command_intensity_changes_dynamic_effect_observation(self):
        publisher = self._publisher(capacity=1)
        rows = []
        for intensity in (0.5, 2.0):
            output = _rows(1, "effect", batch=1)
            batch = EffectSlotBatch(
                slot_indices=torch.tensor([0]),
                effect_indices=torch.tensor([[0]]),
                remaining_fraction=torch.tensor([[1.0]]),
                intensity=torch.tensor([[intensity]]),
                active=torch.tensor([[True]]),
                owner_slot=torch.tensor([-1]),
            )
            publisher.publish(output, TokenPublishContext(effect_slots=batch))
            rows.append(output)
        assert not torch.equal(rows[0], rows[1])


def _registry(extra_vars: list[VariableDef] | None = None, num_agents: int = 2) -> VariableRegistry:
    variables = [
        _var("temp", default=0.25),
        _var("phase", normalization=NormalizationSpec(kind="cyclical_sin_cos", period=24.0)),
        _var("mood", scope="agent", normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
        _var("wind", dims=3, normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
    ]
    return VariableRegistry(variables=variables + (extra_vars or []), num_agents=num_agents, device=DEVICE)


def _registry_bindings(refs: list[str]) -> list[SlotBinding]:
    return [SlotBinding(slot_index=i, filler_kind="static", filler_ref=ref) for i, ref in enumerate(refs)]


def _variable_context(ref: str, slot_index: int) -> tuple[float, ...]:
    payload = list(_payload("variable_element"))
    base_ref, element_index = parse_filler_ref(ref)
    if "." in base_ref:
        element_index = 0
    shape = (3,) if base_ref == "wind" else ()
    position_start = PAYLOAD_SCHEMAS["variable_element"].index("position_0")
    coordinates = element_coordinate_block(shape, element_index)
    payload[position_start : position_start + len(coordinates)] = coordinates
    payload[PAYLOAD_SCHEMAS["variable_element"].index("value_width_used")] = 1.0 if base_ref == "phase" else 0.5
    descriptor_start = PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
    payload[descriptor_start : descriptor_start + DESCRIPTOR_BLOCK_WIDTH] = _sig(slot_index)
    return tuple(payload)


def _variable_type(bindings: list[SlotBinding]):
    return build_token_type(
        "variable_element",
        bindings,
        slot_context_payloads=tuple(_variable_context(binding.filler_ref, binding.slot_index) for binding in bindings),
        effect_catalog_contexts=(),
    )


class TestRegistryVariableElementPublisher:
    def test_constructor_identity_authority_is_schema_slot_indices(self):
        signature = inspect.signature(RegistryVariableElementPublisher)
        assert "slot_bindings" not in signature.parameters
        assert "slot_indices" in signature.parameters

    def test_subset_resolves_filler_identity_from_schema_binding(self):
        registry = _registry()
        bindings = _registry_bindings(["temp", "mood"])
        schema = _variable_type(bindings)
        publisher = RegistryVariableElementPublisher(schema, _layout(schema), registry, slot_indices=(1,), device=DEVICE)
        rows = _rows(schema.capacity, "variable_element")

        publisher.publish(rows, TokenPublishContext())

        assert publisher.claimed_slots == (1,)
        assert rows[:, 0].abs().sum().item() == 0.0
        assert rows[0, 1, _lane("variable_element", "value_0")].item() == pytest.approx(0.0)
        registry.set("mood", torch.tensor([2.0, 8.0]), writer="engine")
        publisher.publish(rows, TokenPublishContext())
        assert rows[:, 1, _lane("variable_element", "value_0")].tolist() == pytest.approx([0.2, 0.8])

    @pytest.mark.parametrize(
        ("slot_indices", "message"),
        [
            ((True,), "integer"),
            ((2,), "out of range"),
            ((1, 1), "duplicate"),
            ((1, 0), "compiled order"),
        ],
    )
    def test_slot_indices_are_strictly_validated(self, slot_indices, message):
        registry = _registry()
        schema = _variable_type(_registry_bindings(["temp", "mood"]))
        with pytest.raises(ValueError, match=message):
            RegistryVariableElementPublisher(schema, _layout(schema), registry, slot_indices=slot_indices, device=DEVICE)

    def _publisher(self, registry, refs):
        bindings = _registry_bindings(refs)
        schema = _variable_type(bindings)
        return RegistryVariableElementPublisher(schema, _layout(schema), registry, tuple(range(schema.capacity)), DEVICE), schema

    def test_declare_then_that_row_moves_batched_from_the_arena(self):
        registry = _registry()
        publisher, schema = self._publisher(registry, ["temp", "mood", "wind[1]"])
        v0 = _lane("variable_element", "value_0")
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext())
        assert rows[0, 0, v0].item() == pytest.approx(0.25)
        registry.set("temp", torch.tensor(0.75), writer="engine")
        registry.set("mood", torch.tensor([2.0, 8.0]), writer="engine")
        registry.set("wind", torch.tensor([[0.0, 5.0, 0.0], [0.0, 5.0, 0.0]])[0], writer="engine")
        rows2 = _rows(schema.capacity, "variable_element")
        publisher.publish(rows2, TokenPublishContext())
        assert rows2[0, 0, v0].item() == pytest.approx(0.75)  # global broadcasts to every world
        assert rows2[1, 0, v0].item() == pytest.approx(0.75)
        assert rows2[0, 1, v0].item() == pytest.approx(0.2)  # agent scope: per-world row
        assert rows2[1, 1, v0].item() == pytest.approx(0.8)
        assert rows2[0, 2, v0].item() == pytest.approx(0.5)  # wind[1] element

    def test_presence_and_descriptor_and_coords(self):
        registry = _registry()
        publisher, schema = self._publisher(registry, ["temp", "wind[2]"])
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext())
        assert rows[:, :, 0].tolist() == [[1.0, 1.0], [1.0, 1.0]]
        expanded = _expand(schema, rows)
        d0 = 1 + PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        assert expanded[0, 0, d0 : d0 + DESCRIPTOR_BLOCK_WIDTH].tolist() == pytest.approx(list(_sig(0)))
        pos0 = 1 + PAYLOAD_SCHEMAS["variable_element"].index("position_0")
        assert expanded[0, 1, pos0].item() == 1.0  # wind[2] of shape (3,): coord 2/2
        assert expanded[0, 1, pos0 + MAX_POSITION_RANK].item() == pytest.approx(1 / MAX_POSITION_RANK)
        vw = 1 + PAYLOAD_SCHEMAS["variable_element"].index("value_width_used")
        assert expanded[0, 0, vw].item() == pytest.approx(1 / VALUE_BLOCK_WIDTH)

    def test_fixed_coordinates_and_descriptor_come_from_positional_slot_context(self):
        registry = _registry()
        bindings = _registry_bindings(["temp"])
        context = list(_variable_context("temp", 0))
        descriptor_start = PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        expected_descriptor = _sig(25.0)
        context[descriptor_start : descriptor_start + DESCRIPTOR_BLOCK_WIDTH] = expected_descriptor
        schema = build_token_type(
            "variable_element",
            bindings,
            slot_context_payloads=(tuple(context),),
            effect_catalog_contexts=(),
        )
        rows = _rows(1, "variable_element")

        RegistryVariableElementPublisher(schema, _layout(schema), registry, (0,), DEVICE).publish(rows, TokenPublishContext())

        expanded = _expand(schema, rows)
        descriptor = 1 + PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        assert expanded[0, 0, descriptor : descriptor + DESCRIPTOR_BLOCK_WIDTH].tolist() == pytest.approx(expected_descriptor)

    def test_cyclical_fills_both_lanes_of_one_token(self):
        registry = _registry()
        publisher, schema = self._publisher(registry, ["phase"])
        registry.set("phase", torch.tensor(6.0), writer="engine")
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext())
        v0 = _lane("variable_element", "value_0")
        assert rows[0, 0, v0].item() == pytest.approx(1.0)  # sin(2pi*6/24)
        assert rows[0, 0, v0 + 1].item() == pytest.approx(0.0, abs=1e-6)
        expanded = _expand(schema, rows)
        vw = 1 + PAYLOAD_SCHEMAS["variable_element"].index("value_width_used")
        assert expanded[0, 0, vw].item() == pytest.approx(2 / VALUE_BLOCK_WIDTH)

    def test_agent_private_binding_refused_before_slot_binding(self):
        registry = _registry(extra_vars=[_var("secret", scope="agent_private")])
        bindings = _registry_bindings(["secret"])
        schema = _variable_type(bindings)
        with pytest.raises(ValueError) as excinfo:
            RegistryVariableElementPublisher(schema, _layout(schema), registry, tuple(range(schema.capacity)), DEVICE)
        message = str(excinfo.value)
        assert "agent_private" in message
        assert "hamlet-83a043a9b9" in message
        assert "enforcement point" in message

    def test_agent_private_never_lands_in_any_agents_rows(self):
        # The end-to-end pin: a registry CONTAINING an exposed-looking agent_private
        # variable publishes identically to one without it, and its sentinel value
        # appears nowhere in the token tensor.
        sentinel = 0.937
        with_private = _registry(extra_vars=[_var("secret", scope="agent_private", default=sentinel)])
        without_private = _registry()
        with_private.set("secret", torch.tensor([sentinel, sentinel]), writer="engine")
        refs = ["temp", "mood", "wind[0]", "wind[1]", "wind[2]", "phase"]
        publisher_a, schema = self._publisher(with_private, refs)
        publisher_b, _ = self._publisher(without_private, refs)
        rows_a = _rows(schema.capacity, "variable_element")
        rows_b = _rows(schema.capacity, "variable_element")
        publisher_a.publish(rows_a, TokenPublishContext())
        publisher_b.publish(rows_b, TokenPublishContext())
        assert torch.equal(rows_a, rows_b)
        assert not bool(torch.isclose(rows_a, torch.tensor(sentinel)).any())
        # ... and the arena itself never held it (excluded by construction).
        for arena in with_private.scope_arenas.values():
            assert "secret" not in arena.index

    def test_item_scope_ref_routed_away_loudly(self):
        registry = _registry()
        bindings = _registry_bindings(["not_a_registry_var"])
        schema = _variable_type(bindings)
        with pytest.raises(ValueError, match="ItemArenaVariableElementPublisher"):
            RegistryVariableElementPublisher(schema, _layout(schema), registry, tuple(range(schema.capacity)), DEVICE)

    def test_missing_slot_context_refuses(self):
        bindings = [SlotBinding(slot_index=0, filler_kind="static", filler_ref="temp")]
        with pytest.raises(ValueError, match="slot context payloads"):
            build_token_type("variable_element", bindings, slot_context_payloads=(), effect_catalog_contexts=())


def _item_profile_registry() -> VariableRegistry:
    class _ProfileVar:
        def __init__(self, name: str):
            self.name = name
            self.type = "scalar"

    class _Profile:
        def __init__(self, names: list[str]):
            self.variables = [_ProfileVar(name) for name in names]

    return VariableRegistry(
        variables=[],
        num_agents=2,
        device=DEVICE,
        max_items=3,
        item_profiles={"food": _Profile(["nutrition", "freshness"])},
    )


class TestItemArenaVariableElementPublisher:
    def _publisher(self, registry, n_slots: int = 2):
        declarations = [
            ItemStateSlotDeclaration(
                slot_index=i,
                owner_slot=i,
                normalization=_BOUNDED,
            )
            for i in range(n_slots)
        ]
        bindings = [
            SlotBinding(
                slot_index=i,
                filler_kind="static",
                filler_ref=f"food.{('nutrition' if i == 0 else 'freshness')}[{i}]",
            )
            for i in range(n_slots)
        ]
        schema = _variable_type(bindings)
        return ItemArenaVariableElementPublisher(schema, _layout(schema), registry, declarations, owner_capacity=2, device=DEVICE), schema

    def test_live_owner_slot_publishes_normalized_state(self):
        registry = _item_profile_registry()
        registry.write_item("food", "nutrition", 0.75, vfs_index=2)
        # Mirrors production (`ItemManager.spawn_item` -> `register_item_instance`,
        # manager.py:396): the publisher's live-slot mask checks the occupant's
        # REGISTERED profile against the declared slot's own profile, not mere
        # liveness (a compiled item token slot can be occupied by any profile).
        registry.register_item_instance(2, "food")
        publisher, schema = self._publisher(registry)
        rows = _rows(schema.capacity, "variable_element")
        batch = _item_batch([0], [[1, 1]], [2], [[False], [False]], [-1])
        publisher.publish(rows, TokenPublishContext(item_slots=batch))
        v0 = _lane("variable_element", "value_0")
        assert rows[0, 0, 0].item() == 1.0
        assert rows[0, 0, v0].item() == pytest.approx(0.75)
        assert rows[1, 0, v0].item() == pytest.approx(0.75)  # world-shared item arena
        # dead owner slot 1: presence 0, payload zeroed.
        assert rows[0, 1, 0].item() == 0.0
        assert rows[0, 1].abs().sum().item() == 0.0

    def test_no_live_items_means_all_absent(self):
        registry = _item_profile_registry()
        publisher, schema = self._publisher(registry)
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext())
        assert rows.abs().sum().item() == 0.0

    def test_descriptor_comes_from_positional_slot_context(self):
        registry = _item_profile_registry()
        publisher, schema = self._publisher(registry, n_slots=1)
        registry.write_item("food", "nutrition", 0.5, vfs_index=0)
        registry.register_item_instance(0, "food")
        rows = _rows(schema.capacity, "variable_element")
        batch = _item_batch([0], [[1, 1]], [0], [[False], [False]], [-1])

        publisher.publish(rows, TokenPublishContext(item_slots=batch))

        expanded = _expand(schema, rows)
        descriptor_start = 1 + PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        context_start = PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        assert expanded[0, 0, descriptor_start:].tolist() == pytest.approx(schema.slot_context_payloads[0][context_start:])

    def test_reads_gather_never_hold_views(self):
        registry = _item_profile_registry()
        registry.write_item("food", "nutrition", 0.5, vfs_index=0)
        registry.register_item_instance(0, "food")
        publisher, schema = self._publisher(registry, n_slots=1)
        batch = _item_batch([0], [[1, 1]], [0], [[False], [False]], [-1])
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext(item_slots=batch))
        before = rows.clone()
        registry.write_item("food", "nutrition", 0.9, vfs_index=0)  # mutate the arena AFTER publish
        assert torch.equal(rows, before)  # published tick unchanged: the read copied

    def test_unknown_profile_refuses(self):
        registry = _item_profile_registry()
        declaration = ItemStateSlotDeclaration(
            slot_index=0,
            owner_slot=0,
            normalization=_BOUNDED,
        )
        bindings = [SlotBinding(slot_index=0, filler_kind="static", filler_ref="ghost.x")]
        schema = _variable_type(bindings)
        with pytest.raises(ValueError, match="'ghost'"):
            ItemArenaVariableElementPublisher(schema, _layout(schema), registry, [declaration], owner_capacity=2, device=DEVICE)


def _full_spec(registry: VariableRegistry, element_refs: list[str]) -> TokenSpec:
    element_bindings = _registry_bindings(element_refs)
    types = []
    for type_name in TOKEN_TYPE_ROSTER:
        if type_name == "self":
            types.append(_static_type("self", ["self"]))
        elif type_name == "meter":
            types.append(_meter_type(_METERS))
        elif type_name == "affordance":
            types.append(_affordance_type())
        elif type_name == "item":
            types.append(_dynamic_type("item", 2))
        elif type_name == "variable_element":
            types.append(_variable_type(element_bindings))
        else:
            types.append(_dynamic_type(type_name, 0))
    return TokenSpec(types=tuple(types), position_rank=2, transport_version=TOKEN_TRANSPORT_VERSION)


def _encoder(registry: VariableRegistry, spec: TokenSpec) -> TokenObservationEncoder:
    substrate = _substrate()
    self_type = spec.get_type("self")
    meter_type = spec.get_type("meter")
    affordance_type = spec.get_type("affordance")
    agent_type = spec.get_type("agent")
    item_type = spec.get_type("item")
    effect_type = spec.get_type("effect")
    element_type = spec.get_type("variable_element")
    assert all(
        token_type is not None for token_type in (self_type, meter_type, affordance_type, agent_type, item_type, effect_type, element_type)
    )
    assert self_type is not None
    assert meter_type is not None
    assert affordance_type is not None
    assert agent_type is not None
    assert item_type is not None
    assert effect_type is not None
    assert element_type is not None
    compact_layout = spec.compact_layout()

    def layout_for(type_name: str):
        layout = compact_layout.get_type(type_name)
        assert layout is not None
        return layout

    publishers = [
        SelfTokenPublisher(self_type, layout_for("self"), substrate),
        MeterTokenPublisher(meter_type, layout_for("meter"), _METERS, _METER_COLUMNS, DEVICE),
        AffordanceTokenPublisher(affordance_type, layout_for("affordance"), substrate),
        AgentTokenPublisher(agent_type, layout_for("agent"), substrate),
        ItemTokenPublisher(item_type, layout_for("item"), substrate, owner_slot_capacity=2),
        EffectTokenPublisher(effect_type, layout_for("effect"), owner_slot_capacity=1),
        RegistryVariableElementPublisher(
            element_type, layout_for("variable_element"), registry, tuple(range(element_type.capacity)), DEVICE
        ),
        ItemArenaVariableElementPublisher(element_type, layout_for("variable_element"), registry, [], owner_capacity=1, device=DEVICE),
    ]
    return TokenObservationEncoder(spec, publishers, DEVICE)


def _full_ctx(registry_positions=None) -> TokenPublishContext:
    return TokenPublishContext(
        positions=registry_positions if registry_positions is not None else torch.tensor([[0, 0], [4, 4]]),
        velocities=torch.zeros((2, 2)),
        meters=torch.tensor([[0.8, 25.0], [0.2, 100.0]]),
        affordance_positions=torch.tensor([[2, 3], [7, 7]]),
        affordance_deployed=torch.tensor([True, True]),
    )


class TestTokenObservationEncoder:
    def test_layout_matches_spec_serialization(self):
        registry = _registry()
        spec = _full_spec(registry, ["temp", "mood"])
        encoder = _encoder(registry, spec)
        observation = encoder.encode(2, _full_ctx())
        assert observation.shape == (2, spec.total_dims)
        # Row layout agreement: presence flags sit exactly where row_layout says.
        for type_name, _slot, start, _end in spec.row_layout():
            if type_name in ("self", "meter", "affordance", "variable_element"):
                assert observation[0, start].item() in (0.0, 1.0)
        # meter block: first meter row's presence is 1 at its layout offset.
        meter_rows = [row for row in spec.row_layout() if row[0] == "meter"]
        assert observation[0, meter_rows[0][2]].item() == 1.0

    def test_capacity_without_publisher_refuses(self):
        registry = _registry()
        spec = _full_spec(registry, ["temp"])
        substrate = _substrate()
        self_type = spec.get_type("self")
        assert self_type is not None
        with pytest.raises(ValueError, match="no publisher"):
            TokenObservationEncoder(spec, [SelfTokenPublisher(self_type, _layout(self_type), substrate)], DEVICE)

    def test_unknown_publisher_type_refuses(self):
        spec = TokenSpec(
            types=(_static_type("self", ["self"]),),
            position_rank=2,
            transport_version=TOKEN_TRANSPORT_VERSION,
        )

        class FakePublisher:
            type_name = "meter"

            def publish(self, rows, ctx):  # pragma: no cover
                pass

        with pytest.raises(ValueError, match="no type in the compiled TokenSpec"):
            TokenObservationEncoder(spec, [FakePublisher()], DEVICE)

    def test_overlapping_variable_element_slot_claims_refuse(self):
        # Minor-6: the two variable_element publishers must claim DISJOINT slot sets;
        # an overlapping compiled artifact refuses loudly at encoder construction,
        # naming the slot and both claimants — never silent last-writer-wins.
        registry = _registry()
        bindings = _registry_bindings(["temp", "mood"])
        schema = _variable_type(bindings)
        spec = TokenSpec(types=(schema,), position_rank=2, transport_version=TOKEN_TRANSPORT_VERSION)
        publisher_a = RegistryVariableElementPublisher(schema, _layout(schema), registry, (0, 1), DEVICE)
        publisher_b = RegistryVariableElementPublisher(schema, _layout(schema), registry, (0,), DEVICE)
        with pytest.raises(ValueError, match="overlapping slot claims") as excinfo:
            TokenObservationEncoder(spec, [publisher_a, publisher_b], DEVICE)
        message = str(excinfo.value)
        assert "slot 0" in message
        assert message.count("RegistryVariableElementPublisher") == 2  # both claimants named

    def test_replay_aliasing_two_ticks_never_share_storage(self):
        registry = _registry()
        spec = _full_spec(registry, ["temp", "mood"])
        encoder = _encoder(registry, spec)
        tick_one = encoder.encode(2, _full_ctx())
        stored = tick_one.clone()
        registry.set("temp", torch.tensor(0.9), writer="engine")
        tick_two = encoder.encode(2, _full_ctx())
        assert tick_one.data_ptr() != tick_two.data_ptr()
        assert torch.equal(tick_one, stored)  # tick one is immutable history
        assert not torch.equal(tick_one, tick_two)  # the declared change moved tick two

    def test_end_to_end_agent_private_never_lands(self):
        sentinel = 0.937
        registry = _registry(extra_vars=[_var("secret", scope="agent_private", default=sentinel)])
        registry.set("secret", torch.tensor([sentinel, sentinel]), writer="engine")
        spec = _full_spec(registry, ["temp", "mood"])
        encoder = _encoder(registry, spec)
        observation = encoder.encode(2, _full_ctx())
        assert not bool(torch.isclose(observation, torch.tensor(sentinel)).any())
