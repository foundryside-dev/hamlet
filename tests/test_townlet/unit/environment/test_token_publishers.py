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

import pytest
import torch

from townlet.environment.observation_encoder import TokenObservationEncoder
from townlet.environment.token_publishers import (
    AffordanceTokenDeclaration,
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
    element_coordinate_block,
    parse_filler_ref,
)
from townlet.substrate.grid2d import Grid2DSubstrate
from townlet.universe.dto.token_spec import (
    DESCRIPTOR_BLOCK_WIDTH,
    MAX_POSITION_RANK,
    PAYLOAD_SCHEMAS,
    TOKEN_TYPE_ROSTER,
    VALUE_BLOCK_WIDTH,
    EffectDeclaration,
    MeterDeclaration,
    SlotBinding,
    TokenSpec,
    build_token_type,
)
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import NormalizationSpec, VariableDef

DEVICE = torch.device("cpu")


def _substrate(boundary: str = "clamp") -> Grid2DSubstrate:
    return Grid2DSubstrate(width=8, height=8, boundary=boundary, distance_metric="manhattan", observation_encoding="relative")


def _static_type(type_name: str, refs: list[str]):
    return build_token_type(
        type_name, tuple(SlotBinding(slot_index=i, filler_kind="static", filler_ref=ref) for i, ref in enumerate(refs))
    )


def _dynamic_type(type_name: str, capacity: int):
    return build_token_type(
        type_name,
        tuple(SlotBinding(slot_index=i, filler_kind="dynamic", filler_ref=f"{type_name}:{i}") for i in range(capacity)),
    )


def _rows(capacity: int, type_name: str, batch: int = 2) -> torch.Tensor:
    width = 1 + len(PAYLOAD_SCHEMAS[type_name])
    return torch.zeros((batch, capacity, width), dtype=torch.float32)


def _lane(type_name: str, feature: str) -> int:
    return 1 + PAYLOAD_SCHEMAS[type_name].index(feature)


_METERS = [
    MeterDeclaration(
        name="energy",
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
        schema = _static_type("self", ["self"])
        publisher = SelfTokenPublisher(schema, _substrate())
        rows = _rows(1, "self")
        ctx = TokenPublishContext(positions=torch.tensor([[0, 0], [7, 7]]), velocities=torch.tensor([[0.1, 0.2], [0.3, 0.4]]))
        publisher.publish(rows, ctx)
        assert rows[:, 0, 0].tolist() == [1.0, 1.0]
        pos0 = _lane("self", "position_0")
        assert rows[0, 0, pos0 : pos0 + 2].tolist() == [0.0, 0.0]
        assert rows[1, 0, pos0 : pos0 + 2].tolist() == [1.0, 1.0]
        assert rows[0, 0, _lane("self", "position_rank")].item() == pytest.approx(2 / MAX_POSITION_RANK)
        vel0 = _lane("self", "velocity_0")
        assert rows[1, 0, vel0 : vel0 + 2].tolist() == pytest.approx([0.3, 0.4])

    def test_missing_positions_refuses(self):
        publisher = SelfTokenPublisher(_static_type("self", ["self"]), _substrate())
        with pytest.raises(ValueError, match="positions"):
            publisher.publish(_rows(1, "self"), TokenPublishContext())


class TestMeterTokenPublisher:
    def _publisher(self):
        schema = _static_type("meter", ["energy", "money"])
        return MeterTokenPublisher(schema, _METERS, _METER_COLUMNS, DEVICE)

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
        sig0 = _lane("meter", "initial")
        assert rows[0, 0, sig0:].tolist() != rows[0, 1, sig0:].tolist()

    def test_unbound_meter_refuses_at_construction(self):
        schema = _static_type("meter", ["energy", "ghost"])
        with pytest.raises(ValueError, match="undeclared meter 'ghost'"):
            MeterTokenPublisher(schema, _METERS, _METER_COLUMNS, DEVICE)


_AFFORDANCES = [
    AffordanceTokenDeclaration(id="EAT", interaction_type="instant", effect_deltas={"energy": 0.3}),
    AffordanceTokenDeclaration(id="SLEEP", interaction_type="multi_tick", effect_deltas={"energy": 0.5, "money": -10.0}),
]
_METERS_BY_NAME = {meter.name: meter for meter in _METERS}


class TestAffordanceTokenPublisher:
    def _publisher(self, boundary: str = "clamp"):
        schema = _static_type("affordance", ["EAT", "SLEEP"])
        return AffordanceTokenPublisher(schema, _substrate(boundary), _AFFORDANCES, _METERS_BY_NAME, DEVICE)

    def _ctx(self, positions, vision_range=None):
        return TokenPublishContext(
            positions=positions,
            affordance_positions={"EAT": torch.tensor([2, 3]), "SLEEP": torch.tensor([7, 7])},
            vision_range=vision_range,
        )

    def test_full_observability_publishes_both_with_identity(self):
        publisher = self._publisher()
        rows = _rows(2, "affordance")
        publisher.publish(rows, self._ctx(torch.tensor([[0, 0], [4, 4]])))
        assert rows[:, :, 0].tolist() == [[1.0, 1.0], [1.0, 1.0]]
        it_instant = _lane("affordance", "interaction_type_instant")
        it_multi = _lane("affordance", "interaction_type_multi_tick")
        assert rows[0, 0, it_instant].item() == 1.0 and rows[0, 0, it_multi].item() == 0.0
        assert rows[0, 1, it_multi].item() == 1.0
        # effect summary present-flags: EAT has one delta, SLEEP two.
        p0 = _lane("affordance", "effect_0_present")
        p1 = _lane("affordance", "effect_1_present")
        assert rows[0, 0, p0].item() == 1.0 and rows[0, 0, p1].item() == 0.0
        assert rows[0, 1, p0].item() == 1.0 and rows[0, 1, p1].item() == 1.0

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

    def test_missing_runtime_position_refuses(self):
        publisher = self._publisher()
        ctx = TokenPublishContext(positions=torch.tensor([[0, 0]]), affordance_positions={"EAT": torch.tensor([2, 3])})
        with pytest.raises(ValueError, match="SLEEP"):
            publisher.publish(_rows(2, "affordance", batch=1), ctx)


class TestAgentTokenPublisher:
    def test_capacity_zero_is_a_noop_and_never_keys_on_batch_size(self):
        # num_agents is a batch of independent worlds (Global Constraints): a 7-world
        # batch against capacity 0 publishes NOTHING and raises nothing.
        publisher = AgentTokenPublisher(_dynamic_type("agent", 0), _substrate())
        rows = torch.zeros((7, 0, 1 + len(PAYLOAD_SCHEMAS["agent"])))
        publisher.publish(rows, TokenPublishContext(positions=torch.zeros((7, 2), dtype=torch.long)))
        assert rows.numel() == 0

    def test_synthetic_shared_world_slots_fill(self):
        publisher = AgentTokenPublisher(_dynamic_type("agent", 2), _substrate())
        rows = _rows(2, "agent", batch=1)
        batch = AgentSlotBatch(slot_indices=torch.tensor([1]), positions=torch.tensor([[3, 4]]))
        publisher.publish(rows, TokenPublishContext(positions=torch.tensor([[0, 0]]), agent_slots=batch))
        assert rows[0, 0, 0].item() == 0.0  # unassigned slot: absent
        assert rows[0, 1, 0].item() == 1.0
        pos0 = _lane("agent", "position_0")
        assert rows[0, 1, pos0 : pos0 + 2].tolist() == pytest.approx([3 / 7, 4 / 7])

    def test_overflow_raises(self):
        publisher = AgentTokenPublisher(_dynamic_type("agent", 1), _substrate())
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
        return ItemTokenPublisher(_dynamic_type("item", capacity), _substrate(), owner_slot_capacity=2)

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
        EffectDeclaration(id="regen", scope="agent", duration=10, intensity=0.4, reapply_policy="renew"),
        EffectDeclaration(id="poison", scope="agent", duration=5, intensity=-0.2, reapply_policy="stack"),
    ]

    def _publisher(self, capacity: int = 2):
        return EffectTokenPublisher(_dynamic_type("effect", capacity), self._DECLARATIONS, owner_slot_capacity=4, device=DEVICE)

    def test_declared_identity_and_remaining_fraction(self):
        publisher = self._publisher()
        rows = _rows(2, "effect", batch=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0]),
            effect_indices=torch.tensor([1]),
            remaining_fraction=torch.tensor([[0.6]]),
            owner_slot=torch.tensor([2]),
        )
        publisher.publish(rows, TokenPublishContext(effect_slots=batch))
        assert rows[0, 0, 0].item() == 1.0
        assert rows[0, 0, _lane("effect", "remaining_fraction")].item() == pytest.approx(0.6)
        assert rows[0, 0, _lane("effect", "intensity")].item() < 0.0  # poison's signed intensity
        assert rows[0, 0, _lane("effect", "reapply_stack")].item() == 1.0
        assert rows[0, 0, _lane("effect", "owner_slot")].item() == pytest.approx(0.5)
        assert rows[0, 1, 0].item() == 0.0

    def test_overflow_names_source(self):
        publisher = self._publisher(capacity=1)
        batch = EffectSlotBatch(
            slot_indices=torch.tensor([0, 1]),
            effect_indices=torch.tensor([0, 1]),
            remaining_fraction=torch.ones((1, 2)),
            owner_slot=torch.tensor([-1, -1]),
        )
        with pytest.raises(TokenCapacityError, match="effect_manager"):
            publisher.publish(_rows(1, "effect", batch=1), TokenPublishContext(effect_slots=batch))


def _registry(extra_vars: list[VariableDef] | None = None, num_agents: int = 2) -> VariableRegistry:
    variables = [
        _var("temp", default=0.25),
        _var("phase", normalization=NormalizationSpec(kind="cyclical_sin_cos", period=24.0)),
        _var("mood", scope="agent", normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
        _var("wind", dims=3, normalization=NormalizationSpec(kind="minmax", min=0.0, max=10.0, clip=True)),
    ]
    return VariableRegistry(variables=variables + (extra_vars or []), num_agents=num_agents, device=DEVICE)


def _registry_bindings(refs: list[str]) -> list[SlotBinding]:
    return [SlotBinding(slot_index=i, filler_kind="static", filler_ref=ref, static_signature=_sig(i)) for i, ref in enumerate(refs)]


class TestRegistryVariableElementPublisher:
    def _publisher(self, registry, refs):
        bindings = _registry_bindings(refs)
        schema = build_token_type("variable_element", bindings)
        return RegistryVariableElementPublisher(schema, registry, bindings, DEVICE), schema

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
        d0 = 1 + PAYLOAD_SCHEMAS["variable_element"].index("scope_global")
        assert rows[0, 0, d0 : d0 + DESCRIPTOR_BLOCK_WIDTH].tolist() == pytest.approx(list(_sig(0)))
        pos0 = _lane("variable_element", "position_0")
        assert rows[0, 1, pos0].item() == 1.0  # wind[2] of shape (3,): coord 2/2
        assert rows[0, 1, pos0 + MAX_POSITION_RANK].item() == pytest.approx(1 / MAX_POSITION_RANK)
        vw = _lane("variable_element", "value_width_used")
        assert rows[0, 0, vw].item() == pytest.approx(1 / VALUE_BLOCK_WIDTH)

    def test_cyclical_fills_both_lanes_of_one_token(self):
        registry = _registry()
        publisher, schema = self._publisher(registry, ["phase"])
        registry.set("phase", torch.tensor(6.0), writer="engine")
        rows = _rows(schema.capacity, "variable_element")
        publisher.publish(rows, TokenPublishContext())
        v0 = _lane("variable_element", "value_0")
        assert rows[0, 0, v0].item() == pytest.approx(1.0)  # sin(2pi*6/24)
        assert rows[0, 0, v0 + 1].item() == pytest.approx(0.0, abs=1e-6)
        vw = _lane("variable_element", "value_width_used")
        assert rows[0, 0, vw].item() == pytest.approx(2 / VALUE_BLOCK_WIDTH)

    def test_agent_private_binding_refused_before_slot_binding(self):
        registry = _registry(extra_vars=[_var("secret", scope="agent_private")])
        bindings = _registry_bindings(["secret"])
        schema = build_token_type("variable_element", bindings)
        with pytest.raises(ValueError) as excinfo:
            RegistryVariableElementPublisher(schema, registry, bindings, DEVICE)
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
        schema = build_token_type("variable_element", bindings)
        with pytest.raises(ValueError, match="ItemArenaVariableElementPublisher"):
            RegistryVariableElementPublisher(schema, registry, bindings, DEVICE)

    def test_missing_static_signature_refuses(self):
        registry = _registry()
        bindings = [SlotBinding(slot_index=0, filler_kind="static", filler_ref="temp")]
        schema = build_token_type("variable_element", bindings)
        with pytest.raises(ValueError, match="static_signature"):
            RegistryVariableElementPublisher(schema, registry, bindings, DEVICE)


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
                profile_name="food",
                var_name=("nutrition" if i == 0 else "freshness"),
                owner_slot=i,
                normalization=_BOUNDED,
                descriptor=_sig(10.0 + i),
            )
            for i in range(n_slots)
        ]
        bindings = [
            SlotBinding(slot_index=i, filler_kind="static", filler_ref=f"food.{d.var_name}[{i}]", static_signature=d.descriptor)
            for i, d in enumerate(declarations)
        ]
        schema = build_token_type("variable_element", bindings)
        return ItemArenaVariableElementPublisher(schema, registry, declarations, owner_capacity=2, device=DEVICE), schema

    def test_live_owner_slot_publishes_normalized_state(self):
        registry = _item_profile_registry()
        registry.write_item("food", "nutrition", 0.75, vfs_index=2)
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

    def test_reads_gather_never_hold_views(self):
        registry = _item_profile_registry()
        registry.write_item("food", "nutrition", 0.5, vfs_index=0)
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
            slot_index=0, profile_name="ghost", var_name="x", owner_slot=0, normalization=_BOUNDED, descriptor=_sig(0)
        )
        bindings = [SlotBinding(slot_index=0, filler_kind="static", filler_ref="ghost.x", static_signature=_sig(0))]
        schema = build_token_type("variable_element", bindings)
        with pytest.raises(ValueError, match="'ghost'"):
            ItemArenaVariableElementPublisher(schema, registry, [declaration], owner_capacity=2, device=DEVICE)


def _full_spec(registry: VariableRegistry, element_refs: list[str]) -> TokenSpec:
    element_bindings = _registry_bindings(element_refs)
    types = []
    for type_name in TOKEN_TYPE_ROSTER:
        if type_name == "self":
            types.append(_static_type("self", ["self"]))
        elif type_name == "meter":
            types.append(_static_type("meter", ["energy", "money"]))
        elif type_name == "affordance":
            types.append(_static_type("affordance", ["EAT", "SLEEP"]))
        elif type_name == "item":
            types.append(_dynamic_type("item", 2))
        elif type_name == "variable_element":
            types.append(build_token_type("variable_element", element_bindings))
        else:
            types.append(_dynamic_type(type_name, 0))
    return TokenSpec(types=tuple(types))


def _encoder(registry: VariableRegistry, spec: TokenSpec) -> TokenObservationEncoder:
    substrate = _substrate()
    element_type = spec.get_type("variable_element")
    assert element_type is not None
    publishers = [
        SelfTokenPublisher(spec.get_type("self"), substrate),
        MeterTokenPublisher(spec.get_type("meter"), _METERS, _METER_COLUMNS, DEVICE),
        AffordanceTokenPublisher(spec.get_type("affordance"), substrate, _AFFORDANCES, _METERS_BY_NAME, DEVICE),
        AgentTokenPublisher(spec.get_type("agent"), substrate),
        ItemTokenPublisher(spec.get_type("item"), substrate, owner_slot_capacity=2),
        EffectTokenPublisher(spec.get_type("effect"), [], owner_slot_capacity=1, device=DEVICE),
        RegistryVariableElementPublisher(element_type, registry, list(element_type.slot_bindings), DEVICE),
        ItemArenaVariableElementPublisher(element_type, registry, [], owner_capacity=1, device=DEVICE),
    ]
    return TokenObservationEncoder(spec, publishers, DEVICE)


def _full_ctx(registry_positions=None) -> TokenPublishContext:
    return TokenPublishContext(
        positions=registry_positions if registry_positions is not None else torch.tensor([[0, 0], [4, 4]]),
        velocities=torch.zeros((2, 2)),
        meters=torch.tensor([[0.8, 25.0], [0.2, 100.0]]),
        affordance_positions={"EAT": torch.tensor([2, 3]), "SLEEP": torch.tensor([7, 7])},
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
        with pytest.raises(ValueError, match="no publisher"):
            TokenObservationEncoder(spec, [SelfTokenPublisher(spec.get_type("self"), substrate)], DEVICE)

    def test_unknown_publisher_type_refuses(self):
        spec = TokenSpec(types=(_static_type("self", ["self"]),))

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
        schema = build_token_type("variable_element", bindings)
        spec = TokenSpec(types=(schema,))
        publisher_a = RegistryVariableElementPublisher(schema, registry, bindings, DEVICE)
        publisher_b = RegistryVariableElementPublisher(schema, registry, bindings[:1], DEVICE)
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
