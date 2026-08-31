"""Live compact token publishers, one per compiled token type.

Each publisher writes only its type's dynamic compact lanes into the per-tick token
observation allocated by :class:`TokenObservationEncoder`. Immutable slot and catalog
context stays in the compiled schema and is attached one type at a time at the network
boundary. The live ``variable_element`` path currently publishes registry-backed
slots from ``VariableRegistry.scope_arenas``. The item-arena publisher is available,
but the live encoder does not wire it until the compiler emits item-profile slots and
a pack declares them.

Implementation constraints carried verbatim (spec §6):

- publisher write targets use ``.view()`` (raises on copy), never ``.reshape()``;
- output observations are per-tick allocated (see `TokenObservationEncoder.encode`);
- masks are bool;
- registry publisher fills are batched per scope via the arena — never per-variable
  Python loops;
- item-arena reads never hold cross-tick views (gathers copy).

Presence ownership (spec §3): compile-time-static filler kinds publish presence 1
(subject to the visibility filter for spatial types); runtime-dynamic filler kinds
toggle presence through unique-slot writes (`bind_dynamic_slots`). Overflow raises at
publish time naming type, capacity, and source — silent truncation is a lying
observation (spec §2).
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

import torch

from townlet.substrate.base import SpatialSubstrate
from townlet.universe.dto.token_spec import (
    DESCRIPTOR_BLOCK_WIDTH,
    MAX_POSITION_RANK,
    METER_SIGNATURE_WIDTH,
    SCOPE_VOCABULARY,
    VALUE_BLOCK_WIDTH,
    CompactTokenTypeLayout,
    MeterDeclaration,
    TokenTypeSchema,
    meter_signature,
    require_exposure_normalization,
    value_block_width_used,
)
from townlet.universe.dto.token_spec import (
    element_coordinate_block as _element_coordinate_block,
)
from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope

__all__ = [
    "AffordanceTokenPublisher",
    "AgentSlotBatch",
    "AgentTokenPublisher",
    "EffectSlotBatch",
    "EffectTokenPublisher",
    "ItemArenaVariableElementPublisher",
    "ItemSlotBatch",
    "ItemStateSlotDeclaration",
    "ItemTokenPublisher",
    "MeterTokenPublisher",
    "RegistryVariableElementPublisher",
    "SelfTokenPublisher",
    "TokenCapacityError",
    "TokenPublishContext",
    "TokenTypePublisher",
    "bind_dynamic_slots",
]


class TokenCapacityError(ValueError):
    """A publisher was asked to place more live instances than compiled capacity.

    Raised AT PUBLISH TIME, naming type, capacity, and source (spec §2 "overflow is
    loud"): silent truncation is a lying observation.
    """

    def __init__(self, type_name: str, capacity: int, requested: int, source: str) -> None:
        super().__init__(
            f"Token type '{type_name}' overflow at publish time: {requested} live instance(s) "
            f"but compiled capacity is {capacity} (source: {source}).\n"
            "  Rule: overflow raises, naming type, capacity, and source — silent truncation is a "
            "lying observation (spec §2)."
        )
        self.type_name = type_name
        self.capacity = capacity
        self.requested = requested
        self.source = source


def bind_dynamic_slots(type_name: str, capacity: int, slot_indices: torch.Tensor, *, source: str) -> torch.Tensor:
    """Validate a dynamic type's live-instance slot assignment (unique-slot writes).

    Overflow raises `TokenCapacityError`; duplicate or out-of-range slots are refusals —
    dynamic slot assignment is unique-slot writes only (spec §3 presence ownership).
    """
    if slot_indices.dim() != 1:
        raise ValueError(f"Token type '{type_name}': slot_indices must be 1-D, got shape {tuple(slot_indices.shape)}")
    requested = int(slot_indices.shape[0])
    if requested > capacity:
        raise TokenCapacityError(type_name, capacity, requested, source)
    slots = slot_indices.to(dtype=torch.long)
    if requested:
        # ONE device sync per dynamic type per publish: the
        # range test and the duplicate test are both computed device-side and folded
        # into a single scalar before the only `bool()`. The previous form paid two-to
        # -three syncs (`min().item()`, `max().item()`, `torch.unique`) on every tick a
        # live batch flowed. The `.tolist()` diagnostics are on the failure path only,
        # where a sync no longer costs anything.
        in_range = (slots >= 0) & (slots < capacity)
        safe = slots.clamp(0, capacity - 1)
        occupancy = torch.zeros(capacity, dtype=torch.long, device=slots.device)
        occupancy.scatter_add_(0, safe, torch.ones_like(safe))
        bad = (~in_range).any() | (occupancy > 1).any()
        if bool(bad):
            if not bool(in_range.all()):
                raise ValueError(
                    f"Token type '{type_name}': slot index out of range [0, {capacity}) in {slots.tolist()} (source: {source})"
                )
            raise ValueError(
                f"Token type '{type_name}': duplicate slot assignment in {slots.tolist()} (source: {source}).\n"
                "  Rule: dynamic slot assignment is unique-slot writes only (spec §3)."
            )
    return slots


# --------------------------------------------------------------------------- shared blocks

_FILLER_REF_PATTERN = re.compile(r"^(?P<base>.+?)(?:\[(?P<element>\d+)\])?$")


def parse_filler_ref(filler_ref: str) -> tuple[str, int]:
    """Split a `variable_element` filler ref into (variable id, element index).

    The compiler's convention (Task 7): `id` for scalars, `id[i]` for element i of a
    tensor-shaped variable.
    """
    match = _FILLER_REF_PATTERN.match(filler_ref)
    if match is None:  # pragma: no cover - the pattern matches any non-empty string
        raise ValueError(f"Unparseable variable_element filler ref {filler_ref!r}")
    element = match.group("element")
    return match.group("base"), int(element) if element is not None else 0


def _slot_context_slice(
    schema: TokenTypeSchema,
    slot_index: int,
    first_feature: str,
    width: int,
) -> tuple[float, ...]:
    """Read one static fixed-row block from the schema-owned positional context."""
    start = schema.payload_features.index(first_feature)
    return schema.slot_context_payloads[slot_index][start : start + width]


def _element_param(value: float | list[float] | None, element_index: int, *, element_count: int, where: str) -> float | None:
    """One element's normalization parameter: scalars broadcast; a list must carry one
    entry per element (row-major) — same rule as token_spec's descriptor derivation."""
    if value is None:
        return None
    if isinstance(value, list):
        if len(value) == 1:
            return float(value[0])
        if len(value) != element_count:
            raise ValueError(
                f"{where} lists {len(value)} values but the variable has {element_count} elements; "
                "declare one value per element (row-major over the shape) or a single scalar"
            )
        return float(value[element_index])
    return float(value)


class CompiledValueNormalizer:
    """Batched application of the exposure-admitted normalization kinds to a slab of
    element values — the per-variable Python loop's replacement.

    Compiled once at publisher construction into per-element parameter tensors and
    per-kind masks (four masks over the element axis — constant count, independent of
    variable count), then applied to `[..., n_elements]` values in whole-tensor ops.
    Kinds mirror `vfs/observation_builder.apply_normalization`'s live ABI exactly:
    minmax / log_scaled clamp (clip is required at exposure), cyclical_sin_cos lands
    sin in lane 0 and cos in lane 1 of ONE token (spec §1 width rule), binary uses the
    strict `value > threshold` comparison.
    """

    def __init__(self, specs: Sequence[tuple[str, NormalizationSpec, int, int]], device: torch.device) -> None:
        """specs: per element (variable id for errors, spec, element_index, element_count)."""
        n = len(specs)
        self._value_ids = tuple(var_id for var_id, _spec, _element_index, _element_count in specs)
        self._kinds = tuple(spec.kind for _var_id, spec, _element_index, _element_count in specs)
        lo = torch.zeros(n, dtype=torch.float32, device=device)
        hi = torch.ones(n, dtype=torch.float32, device=device)
        scale = torch.ones(n, dtype=torch.float32, device=device)
        kind_ids = torch.zeros(n, dtype=torch.long, device=device)
        width_used = torch.ones(n, dtype=torch.float32, device=device)
        kind_to_id = {"minmax": 0, "log_scaled": 1, "cyclical_sin_cos": 2, "binary": 3}
        for i, (var_id, spec, element_index, element_count) in enumerate(specs):
            require_exposure_normalization(var_id, spec)
            kind_ids[i] = kind_to_id[spec.kind]
            width_used[i] = float(value_block_width_used(spec))
            if spec.kind in ("minmax", "log_scaled"):
                lo_value = _element_param(spec.min, element_index, element_count=element_count, where="normalization.min")
                hi_value = _element_param(spec.max, element_index, element_count=element_count, where="normalization.max")
                assert lo_value is not None and hi_value is not None  # bounded kinds declare both
                lo[i] = lo_value
                hi[i] = hi_value
            elif spec.kind == "cyclical_sin_cos":
                assert spec.period is not None
                scale[i] = spec.period
            elif spec.kind == "binary":
                assert spec.threshold is not None
                scale[i] = spec.threshold
        self._lo = lo
        self._hi = hi
        self._scale = scale
        self._width_used = width_used
        self._masks = {name: kind_ids == kind_id for name, kind_id in kind_to_id.items()}

    @property
    def width_used(self) -> torch.Tensor:
        """[n_elements] float — lanes each element fills (1, or 2 for cyclical_sin_cos)."""
        return self._width_used

    def apply(self, values: torch.Tensor) -> torch.Tensor:
        """[..., n] raw values -> [..., n, VALUE_BLOCK_WIDTH] value lanes, batched."""
        finite_inputs = torch.isfinite(values)
        if not bool(finite_inputs.all()):
            bad_columns = torch.nonzero(~finite_inputs, as_tuple=False)[:, -1].unique().tolist()
            offenders = ", ".join(f"{self._value_ids[index]} ({self._kinds[index]})" for index in bad_columns)
            raise ValueError(f"CompiledValueNormalizer received non-finite live values for: {offenders}")
        span = self._hi - self._lo
        clamped = values.clamp(min=self._lo, max=self._hi)
        lane0 = torch.zeros_like(values)
        lane1 = torch.zeros_like(values)
        minmax = self._masks["minmax"]
        if bool(minmax.any()):
            lane0 = torch.where(minmax, (clamped - self._lo) / span, lane0)
        log_scaled = self._masks["log_scaled"]
        if bool(log_scaled.any()):
            lane0 = torch.where(log_scaled, torch.log1p((clamped - self._lo).clamp(min=0.0)) / torch.log1p(span), lane0)
        cyclical = self._masks["cyclical_sin_cos"]
        if bool(cyclical.any()):
            angle = values * (2.0 * math.pi / self._scale)
            lane0 = torch.where(cyclical, torch.sin(angle), lane0)
            lane1 = torch.where(cyclical, torch.cos(angle), lane1)
        binary = self._masks["binary"]
        if bool(binary.any()):
            lane0 = torch.where(binary, (values > self._scale).to(dtype=values.dtype), lane0)
        normalized = torch.stack((lane0, lane1), dim=-1)
        finite_outputs = torch.isfinite(normalized)
        if not bool(finite_outputs.all()):
            bad_columns = torch.nonzero(~finite_outputs, as_tuple=False)[:, -2].unique().tolist()
            offenders = ", ".join(f"{self._value_ids[index]} ({self._kinds[index]})" for index in bad_columns)
            raise ValueError(f"CompiledValueNormalizer produced non-finite normalized values for: {offenders}")
        return normalized


def _lane(layout: CompactTokenTypeLayout, feature: str) -> int:
    """Compact row column of one dynamic feature."""
    try:
        return layout.dynamic_features.index(feature)
    except ValueError as exc:
        raise ValueError(f"Token type {layout.type_name!r} compact layout has no dynamic feature {feature!r}") from exc


def _require_type(schema: TokenTypeSchema, expected: str) -> TokenTypeSchema:
    if schema.type_name != expected:
        raise ValueError(f"Publisher for token type '{expected}' constructed with schema for '{schema.type_name}'")
    return schema


def _require_layout(
    schema: TokenTypeSchema,
    layout: CompactTokenTypeLayout,
    expected: str,
) -> CompactTokenTypeLayout:
    if layout.type_name != expected:
        raise ValueError(f"Publisher for token type {expected!r} constructed with compact layout for {layout.type_name!r}")
    if layout.capacity != schema.capacity or layout.fixed_row_width != schema.fixed_row_width:
        raise ValueError(f"Token type {expected!r} compact layout disagrees with its compiled schema")
    return layout


# --------------------------------------------------------------------------- publish inputs


@dataclass(frozen=True)
class AgentSlotBatch:
    """Live co-world agents (shared-world packs only — capacity 0 everywhere today).

    Positions are world-shared `[K, D]`, the affordance/item convention; per-world
    batching semantics arrive with the shared-world declaration surface (admitted
    authoring surface #4), which is also what first gives this type capacity.
    """

    slot_indices: torch.Tensor  # [K] long
    positions: torch.Tensor  # [K, D]
    source: str = "shared-world runtime"


@dataclass(frozen=True)
class ItemSlotBatch:
    """Live item instances keyed by compiled item token slot."""

    slot_indices: torch.Tensor  # [K] long — live compiled slots
    positions: torch.Tensor  # [K, D] item positions (world-shared layout state)
    vfs_indices: torch.Tensor  # [K] long — item_vfs row per live slot
    carried: torch.Tensor  # [N, K] bool — carried by this world's agent
    owner_slot: torch.Tensor  # [K] long — inventory slot of the owner; -1 = not applicable
    source: str = "item_manager"


@dataclass(frozen=True)
class EffectSlotBatch:
    """Active effect instances keyed by compiled effect token slot.

    Effect content is PER WORLD, unlike items: `num_agents` is a batch of independent
    worlds and the agent-scope effect store is keyed by world, so which declared effect
    occupies a given slot differs per world. `effect_indices` and `active` are therefore
    `[N, K]`; a slot inactive in a world publishes presence 0 with a zeroed payload,
    exactly as an out-of-range item does.
    """

    slot_indices: torch.Tensor  # [K] long — compiled slots this batch writes
    effect_indices: torch.Tensor  # [N, K] long — index into compiled effect-catalog context order
    remaining_fraction: torch.Tensor  # [N, K] float in [0, 1]
    intensity: torch.Tensor  # [N, K] finite live spawn intensity
    active: torch.Tensor  # [N, K] bool — is this slot occupied in this world
    owner_slot: torch.Tensor  # [K] long; -1 = not applicable
    source: str = "effect_manager"


@dataclass(frozen=True)
class TokenPublishContext:
    """Per-tick inputs the publishers read. Every field is optional so each publisher
    can state exactly what it requires (a missing required input is a loud refusal, not
    a silent zero)."""

    positions: torch.Tensor | None = None  # [N, D] observer positions (substrate dtype)
    velocities: torch.Tensor | None = None  # [N, D] velocity features (bounded, caller's contract)
    meters: torch.Tensor | None = None  # [N, num_meters] meter state
    # `[C, D]` in COMPILED SLOT ORDER, precomputed by the caller whenever the affordance
    # layout changes — never per tick (affordance layouts are
    # static between resets, and the per-tick Python loop + `torch.stack` this replaced
    # was the measured cost). `D == 0` is legal and is the aspatial case (review Minor-8):
    # the publisher then requires no observer positions at all.
    affordance_positions: torch.Tensor | None = None
    # `[C]` bool in compiled slot order: which declared affordances are DEPLOYED in this
    # level. Capacity is the declared affordance count; an undeployed instance is padding
    # and publishes presence 0 (the compiler's own ruling — `deployment.positions` are
    # per-instance payload inputs, not extra capacity).
    affordance_deployed: torch.Tensor | None = None
    vision_range: float | None = None  # None = full observability (pass-all)
    agent_slots: AgentSlotBatch | None = None
    item_slots: ItemSlotBatch | None = None
    effect_slots: EffectSlotBatch | None = None


class TokenTypePublisher(Protocol):
    """The dispatch contract: one publisher per token type, keyed by `type_name`."""

    @property
    def type_name(self) -> str: ...

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        """Fill this type's `[num_worlds, capacity, compact_row_width]` rows for one tick."""
        ...


def _require_input(value: object, publisher: str, field: str) -> None:
    if value is None:
        raise ValueError(f"{publisher} requires TokenPublishContext.{field}; got None")


# --------------------------------------------------------------------------- publishers


class SelfTokenPublisher:
    """`self` (static, capacity 1): own position + velocity. Always present — the
    visibility filter applies to OTHER spatial entities, never to the observer."""

    type_name = "self"

    def __init__(self, schema: TokenTypeSchema, layout: CompactTokenTypeLayout, substrate: SpatialSubstrate) -> None:
        self._schema = _require_type(schema, "self")
        self._layout = _require_layout(schema, layout, "self")
        self._substrate = substrate
        self._pos0: int | None
        self._vel0: int | None
        if substrate.position_dim > 0:
            self._pos0 = _lane(layout, "position_0")
            self._vel0 = _lane(layout, "velocity_0")
        else:
            self._pos0 = None
            self._vel0 = None

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0:
            return
        dim = self._substrate.position_dim
        rows[:, 0, 0] = 1.0
        if dim > 0:
            assert self._pos0 is not None and self._vel0 is not None
            _require_input(ctx.positions, "SelfTokenPublisher", "positions")
            assert ctx.positions is not None
            rows[:, 0, self._pos0 : self._pos0 + dim] = self._substrate.normalize_positions(ctx.positions)
            if ctx.velocities is not None:
                rows[:, 0, self._vel0 : self._vel0 + dim] = ctx.velocities.to(dtype=rows.dtype)


class MeterTokenPublisher:
    """`meter` (static, one slot per declared meter): compact live value block.

    `environment.yaml` range_type is the sole value-transform authority (PDR-0134).
    Its same-kind NormalizationSpec drives the shared compiled normalizer, while the
    compiled positional context carries the kind and parameters attached by the network.
    """

    type_name = "meter"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        meters: Sequence[MeterDeclaration],
        meter_columns: Mapping[str, int],
        device: torch.device,
    ) -> None:
        self._schema = _require_type(schema, "meter")
        self._layout = _require_layout(schema, layout, "meter")
        names = [meter.name for meter in meters]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(f"Meter token input has duplicate meter declaration(s): {duplicates}")
        if len(meters) != schema.capacity:
            raise ValueError(f"Meter declaration count {len(meters)} does not match compiled meter token capacity {schema.capacity}")
        by_name = {meter.name: meter for meter in meters}
        columns: list[int] = []
        normalizations: list[tuple[str, NormalizationSpec, int, int]] = []
        for binding in schema.slot_bindings:
            meter = by_name.get(binding.filler_ref)
            if meter is None:
                raise ValueError(f"Meter token slot {binding.slot_index} is bound to undeclared meter {binding.filler_ref!r}")
            if binding.filler_ref not in meter_columns:
                raise ValueError(f"Meter {binding.filler_ref!r} has no column in the runtime meter state tensor")
            columns.append(meter_columns[binding.filler_ref])
            normalizations.append((f"meter:{meter.name}", meter.normalization, 0, 1))
            computed_signature = meter_signature(meter)
            signature = _slot_context_slice(schema, binding.slot_index, "initial", METER_SIGNATURE_WIDTH)
            if signature != computed_signature:
                raise ValueError(
                    f"Meter token slot {binding.slot_index} compiled identity disagrees with runtime declaration "
                    f"for {meter.name!r}; recompile the config pack"
                )
            compiled_width = _slot_context_slice(schema, binding.slot_index, "value_width_used", 1)[0]
            expected_width = value_block_width_used(meter.normalization) / VALUE_BLOCK_WIDTH
            if compiled_width != expected_width:
                raise ValueError(
                    f"Meter token slot {binding.slot_index} compiled value width disagrees with runtime declaration "
                    f"for {meter.name!r}; recompile the config pack"
                )
        self._columns = torch.tensor(columns, dtype=torch.long, device=device)
        self._normalizer = CompiledValueNormalizer(normalizations, device)
        self._value0 = _lane(layout, "value_0")

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0:
            return
        _require_input(ctx.meters, "MeterTokenPublisher", "meters")
        assert ctx.meters is not None
        values = ctx.meters.to(dtype=torch.float32).index_select(1, self._columns)  # [N, C]
        normalized = self._normalizer.apply(values)
        rows[:, :, 0] = 1.0
        rows[:, :, self._value0 : self._value0 + VALUE_BLOCK_WIDTH] = normalized


class AffordanceTokenPublisher:
    """`affordance` (static, one slot per placed instance): interaction-type one-hot,
    position, egocentric delta, and the declared effect summary — all under the
    substrate visibility filter (out of range => presence 0, payload zeroed)."""

    type_name = "affordance"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        substrate: SpatialSubstrate,
    ) -> None:
        self._schema = _require_type(schema, "affordance")
        self._layout = _require_layout(schema, layout, "affordance")
        self._substrate = substrate
        self._pos0: int | None
        self._ego0: int | None
        if substrate.position_dim > 0:
            self._pos0 = _lane(layout, "position_0")
            self._ego0 = _lane(layout, "egocentric_0")
        else:
            self._pos0 = None
            self._ego0 = None

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0:
            return
        dim = self._substrate.position_dim
        capacity = self._schema.capacity
        _require_input(ctx.affordance_deployed, "AffordanceTokenPublisher", "affordance_deployed")
        assert ctx.affordance_deployed is not None
        if tuple(ctx.affordance_deployed.shape) != (capacity,):
            raise ValueError(
                f"AffordanceTokenPublisher: affordance_deployed must be [{capacity}] in compiled slot order, "
                f"got {tuple(ctx.affordance_deployed.shape)}"
            )
        if dim > 0:
            # `position_dim == 0` is aspatial: no observer positions and no entity
            # positions exist, and requiring them would be a lie (review Minor-8).
            _require_input(ctx.positions, "AffordanceTokenPublisher", "positions")
            _require_input(ctx.affordance_positions, "AffordanceTokenPublisher", "affordance_positions")
            assert ctx.affordance_positions is not None
            if tuple(ctx.affordance_positions.shape) != (capacity, dim):
                raise ValueError(
                    f"AffordanceTokenPublisher: affordance_positions must be [{capacity}, {dim}] in compiled slot "
                    f"order, got {tuple(ctx.affordance_positions.shape)}"
                )
        if dim > 0:
            assert self._pos0 is not None and self._ego0 is not None
            assert ctx.positions is not None
            assert ctx.affordance_positions is not None
            entity_pos = ctx.affordance_positions
            rows[:, :, self._pos0 : self._pos0 + dim] = self._substrate.normalize_positions(entity_pos)
            rows[:, :, self._ego0 : self._ego0 + dim] = self._substrate.egocentric_delta(ctx.positions, entity_pos)
            visible = self._substrate.visible(ctx.positions, entity_pos, ctx.vision_range)  # [N, C] bool
        else:
            visible = torch.ones((rows.shape[0], capacity), dtype=torch.bool, device=rows.device)
        # An undeployed declaration is padding, not a hidden entity: it is absent for
        # every observer, in every world.
        visible = visible & ctx.affordance_deployed.to(device=rows.device, dtype=torch.bool).unsqueeze(0)
        # Out of range => presence 0 AND payload zeroed (spec §3): an invisible token
        # must not leak its static identity.
        rows *= visible.to(dtype=rows.dtype).unsqueeze(-1)
        rows[:, :, 0] = visible.to(dtype=rows.dtype)


class AgentTokenPublisher:
    """`agent` (dynamic): other agents sharing the world.

    Capacity is 0 on every shipped pack — no shared-world declaration surface exists,
    and capacity NEVER derives from `num_agents` (a batch of independent worlds, plan
    Global Constraints) — so this publisher is a no-op by construction today. It is
    still built fully: given a synthetic shared-world slot batch it fills position and
    egocentric features under the visibility filter.
    """

    type_name = "agent"

    def __init__(self, schema: TokenTypeSchema, layout: CompactTokenTypeLayout, substrate: SpatialSubstrate) -> None:
        self._schema = _require_type(schema, "agent")
        self._layout = _require_layout(schema, layout, "agent")
        self._substrate = substrate
        self._pos0: int | None
        self._ego0: int | None
        if substrate.position_dim > 0:
            self._pos0 = _lane(layout, "position_0")
            self._ego0 = _lane(layout, "egocentric_0")
        else:
            self._pos0 = None
            self._ego0 = None

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0 or ctx.agent_slots is None:
            return
        batch = ctx.agent_slots
        slots = bind_dynamic_slots(self.type_name, self._schema.capacity, batch.slot_indices, source=batch.source)
        if slots.shape[0] == 0:
            return
        dim = self._substrate.position_dim
        payload = torch.zeros((rows.shape[0], slots.shape[0], rows.shape[2]), dtype=rows.dtype, device=rows.device)
        if dim > 0:
            assert self._pos0 is not None and self._ego0 is not None
            _require_input(ctx.positions, "AgentTokenPublisher", "positions")
            assert ctx.positions is not None
            visible = self._substrate.visible(ctx.positions, batch.positions, ctx.vision_range)  # [N, K] bool
            payload[:, :, self._pos0 : self._pos0 + dim] = self._substrate.normalize_positions(batch.positions)
            payload[:, :, self._ego0 : self._ego0 + dim] = self._substrate.egocentric_delta(ctx.positions, batch.positions)
        else:
            visible = torch.ones((rows.shape[0], slots.shape[0]), dtype=torch.bool, device=rows.device)
        payload *= visible.to(dtype=rows.dtype).unsqueeze(-1)
        payload[:, :, 0] = visible.to(dtype=rows.dtype)
        rows[:, slots, :] = payload


class ItemTokenPublisher:
    """`item` (dynamic): world/carried item instances with owner/slot coordinates.

    A carried item is on its owner: its egocentric delta is zeroed for the carrying
    world and it is visible there regardless of stored position.
    """

    type_name = "item"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        substrate: SpatialSubstrate,
        owner_slot_capacity: int,
    ) -> None:
        self._schema = _require_type(schema, "item")
        self._layout = _require_layout(schema, layout, "item")
        self._substrate = substrate
        if owner_slot_capacity < 1:
            raise ValueError("ItemTokenPublisher requires owner_slot_capacity >= 1 to normalize owner slots")
        self._owner_slot_capacity = owner_slot_capacity
        self._pos0: int | None
        self._ego0: int | None
        if substrate.position_dim > 0:
            self._pos0 = _lane(layout, "position_0")
            self._ego0 = _lane(layout, "egocentric_0")
        else:
            self._pos0 = None
            self._ego0 = None
        self._carried = _lane(layout, "carried")
        self._owner_slot = _lane(layout, "owner_slot")
        self._owner_applicable = _lane(layout, "owner_slot_applicable")

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0 or ctx.item_slots is None:
            return
        batch = ctx.item_slots
        slots = bind_dynamic_slots(self.type_name, self._schema.capacity, batch.slot_indices, source=batch.source)
        if slots.shape[0] == 0:
            return
        dim = self._substrate.position_dim
        carried = batch.carried.to(dtype=torch.bool)
        payload = torch.zeros((rows.shape[0], slots.shape[0], rows.shape[2]), dtype=rows.dtype, device=rows.device)
        if dim > 0:
            assert self._pos0 is not None and self._ego0 is not None
            _require_input(ctx.positions, "ItemTokenPublisher", "positions")
            assert ctx.positions is not None
            visible = self._substrate.visible(ctx.positions, batch.positions, ctx.vision_range)
            payload[:, :, self._pos0 : self._pos0 + dim] = self._substrate.normalize_positions(batch.positions)
            ego = self._substrate.egocentric_delta(ctx.positions, batch.positions)
            ego = ego * (~carried).to(dtype=ego.dtype).unsqueeze(-1)  # carried = on self = relative zero
            payload[:, :, self._ego0 : self._ego0 + dim] = ego
        else:
            visible = torch.ones((rows.shape[0], slots.shape[0]), dtype=torch.bool, device=rows.device)
        visible = visible | carried
        applicable = batch.owner_slot >= 0
        payload[:, :, self._carried] = carried.to(dtype=rows.dtype)
        payload[:, :, self._owner_slot] = (batch.owner_slot.clamp(min=0).to(dtype=rows.dtype) / self._owner_slot_capacity) * applicable.to(
            dtype=rows.dtype
        )
        payload[:, :, self._owner_applicable] = applicable.to(dtype=rows.dtype)
        payload *= visible.to(dtype=rows.dtype).unsqueeze(-1)
        payload[:, :, 0] = visible.to(dtype=rows.dtype)
        rows[:, slots, :] = payload


class EffectTokenPublisher:
    """`effect` (dynamic): active observable effects — compact catalog selector plus
    remaining-fraction and owner coordinates. Effects are not spatial, so they have no
    visibility filter."""

    type_name = "effect"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        owner_slot_capacity: int,
    ) -> None:
        self._schema = _require_type(schema, "effect")
        self._layout = _require_layout(schema, layout, "effect")
        if owner_slot_capacity < 1:
            raise ValueError("EffectTokenPublisher requires owner_slot_capacity >= 1 to normalize owner slots")
        self._owner_slot_capacity = owner_slot_capacity
        self._context_index = _lane(layout, "context_index")
        self._remaining = _lane(layout, "remaining_fraction")
        self._intensity = _lane(layout, "live_intensity")
        self._owner_slot = _lane(layout, "owner_slot")
        self._owner_applicable = _lane(layout, "owner_slot_applicable")

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        if self._schema.capacity == 0 or ctx.effect_slots is None:
            return
        batch = ctx.effect_slots
        slots = bind_dynamic_slots(self.type_name, self._schema.capacity, batch.slot_indices, source=batch.source)
        if slots.shape[0] == 0:
            return
        num_worlds, n_slots = rows.shape[0], slots.shape[0]
        indices = batch.effect_indices
        if tuple(indices.shape) != (num_worlds, n_slots):
            raise ValueError(f"EffectTokenPublisher: effect_indices must be [{num_worlds}, {n_slots}], got {tuple(indices.shape)}")
        remaining = batch.remaining_fraction
        if not isinstance(remaining, torch.Tensor):
            raise ValueError("EffectTokenPublisher: remaining_fraction must be a torch.Tensor")
        if tuple(remaining.shape) != (num_worlds, n_slots):
            raise ValueError(f"EffectTokenPublisher: remaining_fraction must be [{num_worlds}, {n_slots}], got {tuple(remaining.shape)}")
        if not remaining.is_floating_point():
            raise ValueError("EffectTokenPublisher: remaining_fraction must use a floating dtype")
        if not torch.isfinite(remaining).all():
            raise ValueError("EffectTokenPublisher: remaining_fraction must be finite")
        intensity = batch.intensity
        if tuple(intensity.shape) != (num_worlds, n_slots):
            raise ValueError(f"EffectTokenPublisher: intensity must be [{num_worlds}, {n_slots}], got {tuple(intensity.shape)}")
        if not torch.isfinite(intensity).all():
            raise ValueError("EffectTokenPublisher: live intensity must be finite")
        active = batch.active
        if not isinstance(active, torch.Tensor):
            raise ValueError("EffectTokenPublisher: active must be a torch.Tensor")
        if tuple(active.shape) != (num_worlds, n_slots):
            raise ValueError(f"EffectTokenPublisher: active must be [{num_worlds}, {n_slots}], got {tuple(active.shape)}")

        payload = torch.zeros((num_worlds, n_slots, rows.shape[2]), dtype=rows.dtype, device=rows.device)
        payload[:, :, self._context_index] = indices.to(device=rows.device, dtype=rows.dtype)
        payload[:, :, self._remaining] = remaining.to(device=rows.device).clamp(0.0, 1.0).to(dtype=rows.dtype)
        intensity = intensity.to(device=rows.device, dtype=rows.dtype)
        payload[:, :, self._intensity] = intensity / (1.0 + intensity.abs())
        applicable = batch.owner_slot >= 0
        payload[:, :, self._owner_slot] = (batch.owner_slot.clamp(min=0).to(dtype=rows.dtype) / self._owner_slot_capacity) * applicable.to(
            dtype=rows.dtype
        )
        payload[:, :, self._owner_applicable] = applicable.to(dtype=rows.dtype)
        # A slot inactive in this world must not leak the static identity of whatever
        # effect last occupied it (spec §3 presence ownership).
        active = active.to(device=rows.device, dtype=torch.bool)
        payload *= active.to(dtype=rows.dtype).unsqueeze(-1)
        payload[:, :, 0] = active.to(dtype=rows.dtype)
        rows[:, slots, :] = payload


class RegistryVariableElementPublisher:
    """`variable_element`, registry half: global/agent-scope exposed variables, read as
    two batched slabs from the per-scope arenas (`VariableRegistry.scope_arenas`) —
    never a per-variable Python loop, never a clone per read (hamlet-c7084169f7).

    **This publisher is the `agent_private` enforcement point** (spec §2 scope table;
    the hamlet-83a043a9b9 boundary by mechanism, not assumption). The registry's raw
    accessors `get_global` / `get_agent` check NOTHING — `get_agent` serves
    `agent_private` variables to any caller, and `list_agent` includes them — so
    nothing upstream protects the observation. The filter is here, structurally and
    before slot binding: slot bindings resolve ONLY against the global/agent scope
    arenas (which exclude `agent_private` by construction), and a compiled binding
    whose variable is `agent_private` is refused loudly at construction. Pinned by
    test: an agent_private value never lands in any agent's rows.
    """

    type_name = "variable_element"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        registry: VariableRegistry,
        slot_indices: Sequence[int],
        device: torch.device,
    ) -> None:
        self._schema = _require_type(schema, "variable_element")
        self._layout = _require_layout(schema, layout, "variable_element")
        self._registry = registry
        slot_positions: list[int] = []
        global_local: list[int] = []
        global_columns: list[int] = []
        agent_local: list[int] = []
        agent_columns: list[int] = []
        normalizer_specs: list[tuple[str, NormalizationSpec, int, int]] = []
        validated_slot_indices: list[int] = []
        seen_slot_indices: set[int] = set()
        for position, slot_index in enumerate(slot_indices):
            if isinstance(slot_index, bool) or not isinstance(slot_index, int):
                raise ValueError(f"RegistryVariableElementPublisher slot_indices[{position}] must be an integer, got {slot_index!r}")
            if slot_index < 0 or slot_index >= schema.capacity:
                raise ValueError(
                    f"RegistryVariableElementPublisher slot_indices[{position}]={slot_index} is out of range "
                    f"for capacity {schema.capacity}"
                )
            if slot_index in seen_slot_indices:
                raise ValueError(f"RegistryVariableElementPublisher slot_indices contains duplicate slot {slot_index}")
            if validated_slot_indices and slot_index < validated_slot_indices[-1]:
                raise ValueError("RegistryVariableElementPublisher slot_indices must follow compiled order")
            seen_slot_indices.add(slot_index)
            validated_slot_indices.append(slot_index)

        for slot_index in validated_slot_indices:
            binding = schema.slot_bindings[slot_index]
            if binding.slot_index != slot_index:
                raise ValueError(
                    f"variable_element schema binding at position {slot_index} declares slot {binding.slot_index}; "
                    "compiled slot bindings must be position-aligned"
                )
            filler_ref = binding.filler_ref
            base_id, element_index = parse_filler_ref(filler_ref)
            var_def = registry.variables.get(base_id)
            if var_def is None:
                raise ValueError(
                    f"variable_element slot {slot_index} is bound to {filler_ref!r}, which is not a registry variable; "
                    "item-profile state slots belong to ItemArenaVariableElementPublisher"
                )
            scope = VariableScope(var_def.scope)
            if scope == VariableScope.AGENT_PRIVATE:
                raise ValueError(
                    f"variable_element slot {slot_index} is bound to agent_private variable {base_id!r}.\n"
                    "  Rule: agent_private is excluded from observation by the publisher, filtered BEFORE slot "
                    "binding (token-obs spec §2 scope table; hamlet-83a043a9b9). The raw registry accessors "
                    "check nothing — this refusal is the enforcement point."
                )
            if scope == VariableScope.GLOBAL:
                scope_key = "global"
            elif scope == VariableScope.AGENT:
                scope_key = "agent"
            else:
                raise ValueError(
                    f"variable_element slot {slot_index} is bound to {base_id!r} of scope {scope.value!r}; only "
                    "global/agent registry scopes publish through the registry arena (spec §2 scope table)"
                )
            arena = registry.scope_arenas[scope_key]
            if base_id not in arena.index:
                raise ValueError(
                    f"variable_element slot {slot_index}: variable {base_id!r} is not arena-backed (non-float32 "
                    "storage). Integer/bool token exposure has no shipped user; it lands when a pack needs it."
                )
            offset, count = arena.index[base_id]
            if element_index >= count:
                raise ValueError(f"variable_element slot {slot_index}: {filler_ref!r} indexes past {count} element(s)")
            local = len(slot_positions)
            slot_positions.append(int(slot_index))
            if scope_key == "global":
                global_local.append(local)
                global_columns.append(offset + element_index)
            else:
                agent_local.append(local)
                agent_columns.append(offset + element_index)
            spec = require_exposure_normalization(base_id, var_def.normalization)
            normalizer_specs.append((base_id, spec, element_index, count))
            context_coordinates = _slot_context_slice(schema, slot_index, "position_0", MAX_POSITION_RANK + 1)
            shape = self._element_shape(var_def)
            expected_coordinates = _element_coordinate_block(shape, element_index)
            if context_coordinates != expected_coordinates:
                raise ValueError(
                    f"variable_element slot {slot_index} ({filler_ref!r}) compiled coordinates disagree with "
                    "the runtime variable declaration; recompile the config pack"
                )
            compiled_width = _slot_context_slice(schema, slot_index, "value_width_used", 1)[0]
            expected_width = value_block_width_used(spec) / VALUE_BLOCK_WIDTH
            if compiled_width != expected_width:
                raise ValueError(
                    f"variable_element slot {slot_index} ({filler_ref!r}) compiled value width disagrees with "
                    "the runtime variable declaration; recompile the config pack"
                )
            _slot_context_slice(schema, slot_index, f"scope_{SCOPE_VOCABULARY[0]}", DESCRIPTOR_BLOCK_WIDTH)
        self._slots = torch.tensor(slot_positions, dtype=torch.long, device=device)
        self._global_local = torch.tensor(global_local, dtype=torch.long, device=device)
        self._global_columns = torch.tensor(global_columns, dtype=torch.long, device=device)
        self._agent_local = torch.tensor(agent_local, dtype=torch.long, device=device)
        self._agent_columns = torch.tensor(agent_columns, dtype=torch.long, device=device)
        self._normalizer = CompiledValueNormalizer(normalizer_specs, device)
        self._value0 = _lane(layout, "value_0")

    @property
    def claimed_slots(self) -> tuple[int, ...]:
        """Token slots this publisher fills; the encoder refuses cross-publisher overlap."""
        return tuple(int(slot) for slot in self._slots.tolist())

    @staticmethod
    def _element_shape(var_def: VariableDef) -> tuple[int, ...]:
        if var_def.shape:
            return tuple(var_def.shape)
        if var_def.dims is not None and var_def.dims > 1:
            return (int(var_def.dims),)
        return ()

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        n = self._slots.shape[0]
        if n == 0:
            return
        num_worlds = rows.shape[0]
        arenas = self._registry.scope_arenas
        # Batched slab reads: one gather per scope, straight off the arena — the values
        # arrive float32 already. Cast policy (hamlet-0268336cd1): float32 is
        # integer-exact to 2^24, which covers tick-lifetime counters (the engine `tick`
        # rides this path once exposed); PERSISTENT-lifetime counters that could exceed
        # 2^24 remain that ticket's open question — the publisher adds no cast of its
        # own, it publishes the storage dtype.
        values = torch.zeros((num_worlds, n), dtype=torch.float32, device=rows.device)
        if self._global_columns.shape[0]:
            values[:, self._global_local] = arenas["global"].tensor[0].index_select(0, self._global_columns)
        if self._agent_columns.shape[0]:
            values[:, self._agent_local] = arenas["agent"].tensor.index_select(1, self._agent_columns)
        lanes = self._normalizer.apply(values)  # [N, n, VALUE_BLOCK_WIDTH]
        slots = self._slots
        rows[:, slots, 0] = 1.0
        rows[:, slots, self._value0 : self._value0 + VALUE_BLOCK_WIDTH] = lanes


@dataclass(frozen=True)
class ItemStateSlotDeclaration:
    """One compiled item-state `variable_element` slot: an exposed item-profile variable
    bound to one owner item token slot."""

    slot_index: int
    owner_slot: int
    normalization: NormalizationSpec


class ItemArenaVariableElementPublisher:
    """`variable_element`, item-arena half: item-profile state read from the
    consolidated `item_vfs` `[max_items, max_vars]` arena with owner/slot coordinates.

    Reads are GATHERS — advanced indexing copies, so no view of the item arena is ever
    held across ticks (spec §6). Presence toggles with the owner item slot's liveness:
    a dead owner slot publishes presence 0 with zeroed payload.
    """

    type_name = "variable_element"

    def __init__(
        self,
        schema: TokenTypeSchema,
        layout: CompactTokenTypeLayout,
        registry: VariableRegistry,
        declarations: Sequence[ItemStateSlotDeclaration],
        owner_capacity: int,
        device: torch.device,
    ) -> None:
        self._schema = _require_type(schema, "variable_element")
        self._layout = _require_layout(schema, layout, "variable_element")
        self._registry = registry
        if declarations and owner_capacity < 1:
            raise ValueError("ItemArenaVariableElementPublisher requires owner_capacity >= 1 when slots are declared")
        # Stored raw: capacity 0 is a real state, legal only with zero declarations,
        # where publish() no-ops before reading it (review Minor-8 — no silent 0→1).
        self._owner_capacity = owner_capacity
        slot_positions: list[int] = []
        columns: list[int] = []
        owner_slots: list[int] = []
        normalizer_specs: list[tuple[str, NormalizationSpec, int, int]] = []
        for declaration in declarations:
            if not 0 <= declaration.slot_index < schema.capacity:
                raise ValueError(f"variable_element item-state slot {declaration.slot_index} is out of range [0, {schema.capacity})")
            binding = schema.slot_bindings[declaration.slot_index]
            base_ref, _ = parse_filler_ref(binding.filler_ref)
            profile_name, separator, var_name = base_ref.partition(".")
            if not separator or not profile_name or not var_name:
                raise ValueError(
                    f"variable_element slot {declaration.slot_index}: item-state filler_ref "
                    f"{binding.filler_ref!r} must be '<profile>.<variable>'"
                )
            profile_vars = registry.item_profile_map.get(profile_name)
            if profile_vars is None:
                raise ValueError(
                    f"variable_element slot {declaration.slot_index}: item profile {profile_name!r} is not "
                    f"compiled into the registry (available: {sorted(registry.item_profile_map)})"
                )
            if var_name not in profile_vars:
                raise ValueError(
                    f"variable_element slot {declaration.slot_index}: variable {var_name!r} is not in item "
                    f"profile {profile_name!r} (available: {sorted(profile_vars)})"
                )
            if not (0 <= declaration.owner_slot < owner_capacity):
                raise ValueError(
                    f"variable_element slot {declaration.slot_index}: owner item slot {declaration.owner_slot} is out of "
                    f"range [0, {owner_capacity})"
                )
            compiled_coordinates = _slot_context_slice(schema, declaration.slot_index, "position_0", MAX_POSITION_RANK + 1)
            if compiled_coordinates != _element_coordinate_block((), 0):
                raise ValueError(
                    f"variable_element slot {declaration.slot_index} ({binding.filler_ref!r}) compiled coordinates "
                    "disagree with the scalar item-state declaration; recompile the config pack"
                )
            compiled_width = _slot_context_slice(schema, declaration.slot_index, "value_width_used", 1)[0]
            expected_width = value_block_width_used(declaration.normalization) / VALUE_BLOCK_WIDTH
            if compiled_width != expected_width:
                raise ValueError(
                    f"variable_element slot {declaration.slot_index} ({binding.filler_ref!r}) compiled value width "
                    "disagrees with the item-state declaration; recompile the config pack"
                )
            slot_positions.append(declaration.slot_index)
            columns.append(profile_vars[var_name])
            owner_slots.append(declaration.owner_slot)
            _slot_context_slice(
                schema,
                declaration.slot_index,
                f"scope_{SCOPE_VOCABULARY[0]}",
                DESCRIPTOR_BLOCK_WIDTH,
            )
            normalizer_specs.append((binding.filler_ref, declaration.normalization, 0, 1))
        self._slots = torch.tensor(slot_positions, dtype=torch.long, device=device)
        self._columns = torch.tensor(columns, dtype=torch.long, device=device)
        self._owner_slots = torch.tensor(owner_slots, dtype=torch.long, device=device)
        self._normalizer = CompiledValueNormalizer(normalizer_specs, device)
        self._value0 = _lane(layout, "value_0")

    @property
    def claimed_slots(self) -> tuple[int, ...]:
        """Token slots this publisher fills; the encoder refuses cross-publisher overlap."""
        return tuple(int(slot) for slot in self._slots.tolist())

    def publish(self, rows: torch.Tensor, ctx: TokenPublishContext) -> None:
        n = self._slots.shape[0]
        if n == 0:
            return
        item_vfs = self._registry.item_vfs
        if item_vfs is None:
            raise ValueError("ItemArenaVariableElementPublisher declared slots but the registry has no item_vfs arena")
        live = torch.zeros(self._owner_capacity, dtype=torch.bool, device=rows.device)
        vfs_rows = torch.zeros(self._owner_capacity, dtype=torch.long, device=rows.device)
        if ctx.item_slots is not None and ctx.item_slots.slot_indices.shape[0]:
            owner_slots = ctx.item_slots.slot_indices.to(dtype=torch.long)
            live[owner_slots] = True
            vfs_rows[owner_slots] = ctx.item_slots.vfs_indices.to(dtype=torch.long)
        mine_live = live.index_select(0, self._owner_slots)  # [n] bool
        source_rows = vfs_rows.index_select(0, self._owner_slots)  # [n]
        # Gather COPIES: no view of item_vfs survives this call (spec §6).
        values = item_vfs[source_rows, self._columns].to(dtype=torch.float32)  # [n]
        values = values * mine_live.to(dtype=torch.float32)
        lanes = self._normalizer.apply(values)  # [n, VALUE_BLOCK_WIDTH]
        live_f = mine_live.to(dtype=rows.dtype)
        slots = self._slots
        # Item state is world-shared (one item arena, like affordance layout): rows
        # broadcast over the world batch. Presence 0 zeroes the payload of dead slots.
        rows[:, slots, 0] = live_f
        rows[:, slots, self._value0 : self._value0 + VALUE_BLOCK_WIDTH] = lanes * live_f.unsqueeze(-1)
