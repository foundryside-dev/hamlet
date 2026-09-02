"""Live compact token observation assembly for :class:`VectorizedHamletEnv`.

The environment exposes only the compiled compact ``TokenSpec`` serialization. Each
tick is assembled from dynamic publisher lanes; immutable contexts are attached later
at the network boundary.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import torch

from townlet.environment.token_publishers import (
    AffordanceTokenPublisher,
    AgentTokenPublisher,
    EffectTokenPublisher,
    ItemArenaVariableElementPublisher,
    ItemStateSlotDeclaration,
    ItemTokenPublisher,
    MeterTokenPublisher,
    RegistryVariableElementPublisher,
    SelfTokenPublisher,
    TokenPublishContext,
    TokenTypePublisher,
    parse_filler_ref,
)
from townlet.universe.dto.token_spec import CompactTokenTypeLayout, TokenSpec, TokenTypeSchema
from townlet.vfs.schema import NormalizationSpec

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


def build_token_observation_encoder(env: VectorizedHamletEnv) -> TokenObservationEncoder:
    """Assemble the live compact token encoder for one environment.

    One publisher per token type with capacity > 0 (PDR-0076: dispatch on the compiled
    type, never on a name); a type with slots and no publisher is a refusal inside
    :class:`TokenObservationEncoder`, not a skip. Everything here is derived from the
    COMPILED artifact — capacities, slot bindings and their order — never from runtime
    counts.
    """
    spec = env.token_spec
    compact_layout = spec.compact_layout()
    device = env.device
    publishers: list[TokenTypePublisher] = []

    def layout_for(type_name: str) -> CompactTokenTypeLayout:
        layout = compact_layout.get_type(type_name)
        assert layout is not None
        return layout

    self_type = spec.get_type("self")
    if self_type is not None and self_type.capacity > 0:
        publishers.append(SelfTokenPublisher(self_type, layout_for("self"), env.substrate))

    meter_type = spec.get_type("meter")
    if meter_type is not None and meter_type.capacity > 0:
        publishers.append(
            MeterTokenPublisher(meter_type, layout_for("meter"), env.level.meter_declarations, env.meter_name_to_index, device)
        )

    affordance_type = spec.get_type("affordance")
    if affordance_type is not None and affordance_type.capacity > 0:
        publishers.append(AffordanceTokenPublisher(affordance_type, layout_for("affordance"), env.substrate))

    agent_type = spec.get_type("agent")
    if agent_type is not None and agent_type.capacity > 0:
        # Capacity is 0 on every shipped pack: `agent` capacity derives from a DECLARED
        # shared-world count, and no pack declares one (`num_agents` is a batch of
        # independent worlds and must never size this).
        publishers.append(AgentTokenPublisher(agent_type, layout_for("agent"), env.substrate))

    item_type = spec.get_type("item")
    if item_type is not None and item_type.capacity > 0:
        publishers.append(ItemTokenPublisher(item_type, layout_for("item"), env.substrate, _owner_slot_capacity(env)))

    effect_type = spec.get_type("effect")
    if effect_type is not None and effect_type.capacity > 0:
        publishers.append(EffectTokenPublisher(effect_type, layout_for("effect"), _owner_slot_capacity(env)))

    element_type = spec.get_type("variable_element")
    if element_type is not None and element_type.capacity > 0:
        # `variable_element` slots are filled by two publishers (token-obs spec §3):
        # the registry half (global/agent-scope exposed variables) and the item-arena
        # half (item-profile state, one slot per compiled `item` token slot — token
        # unit 5 / hamlet-55b2826a02). The compiler's own convention distinguishes
        # them: an item-arena slot's filler_ref is `<profile>.<variable>[<owner_slot>]`
        # where `<profile>` names a compiled item profile
        # (token_spec.py::_variable_element_artifacts); every other slot is
        # registry-backed.
        item_profiles = env.universe.compiled_vfs_profiles.item_profiles if env.universe.compiled_vfs_profiles else None
        registry_slots, item_declarations = _split_variable_element_slots(element_type, item_profiles)
        if registry_slots:
            publishers.append(
                RegistryVariableElementPublisher(
                    element_type,
                    layout_for("variable_element"),
                    env.vfs_registry,
                    registry_slots,
                    device,
                )
            )
        if item_declarations:
            publishers.append(
                ItemArenaVariableElementPublisher(
                    element_type,
                    layout_for("variable_element"),
                    env.vfs_registry,
                    item_declarations,
                    owner_capacity=item_type.capacity if item_type is not None else 0,
                    device=device,
                )
            )

    return TokenObservationEncoder(spec, publishers, device)


def _split_variable_element_slots(
    element_type: TokenTypeSchema,
    item_profiles: dict[str, Any] | None,
) -> tuple[tuple[int, ...], tuple[ItemStateSlotDeclaration, ...]]:
    """Partition a compiled `variable_element` type's slots into (registry-backed slot
    indices, item-arena slot declarations) by their filler_ref shape.

    `item_profiles` is `CompiledVFSProfiles.item_profiles` (`dict[str, CompiledItemProfile]`
    at runtime; typed `dict[str, Any]` upstream — see `universe/compiled.py`).
    """
    profile_normalizations: dict[str, dict[str, NormalizationSpec]] = {}
    if item_profiles:
        for profile_name, profile in item_profiles.items():
            profile_normalizations[profile_name] = {var.name: var.normalization for var in profile.variables if var.exposed_to}

    registry_slots: list[int] = []
    item_declarations: list[ItemStateSlotDeclaration] = []
    for binding in element_type.slot_bindings:
        base_ref, owner_slot = parse_filler_ref(binding.filler_ref)
        profile_name, separator, var_name = base_ref.partition(".")
        var_normalizations = profile_normalizations.get(profile_name) if separator else None
        if var_normalizations is not None and var_name in var_normalizations:
            item_declarations.append(
                ItemStateSlotDeclaration(
                    slot_index=binding.slot_index,
                    owner_slot=owner_slot,
                    normalization=var_normalizations[var_name],
                )
            )
        else:
            registry_slots.append(binding.slot_index)
    return tuple(registry_slots), tuple(item_declarations)


def _owner_slot_capacity(env: VectorizedHamletEnv) -> int:
    """Denominator for normalized owner/slot coordinates.

    The declared per-agent inventory size; 1 when no items catalog is declared (the
    publishers refuse a capacity below 1 rather than dividing by zero).
    """
    catalog = env.universe.items_catalog
    if catalog is None:
        return 1
    return max(1, int(catalog.max_items_per_agent))


class TokenObservationEncoder:
    """The environment's live compact observation encoder.

    Dispatches one publisher per token type (PDR-0076: dispatch on type, never a name
    to match) over the compiled TokenSpec's serialization layout. ``variable_element``
    slots are filled by up to two publishers: the registry half (global/agent-scope
    exposed variables) and the item-arena half (item-profile state), split by
    :func:`_split_variable_element_slots`.

    :meth:`encode` is called at the environment's single end-of-step observation point,
    after all VTC / effects / evaluator writes of the tick.
    """

    def __init__(self, spec: TokenSpec, publishers: Sequence[TokenTypePublisher], device: torch.device) -> None:
        self._spec = spec
        self._device = device
        self._publishers: dict[str, list[TokenTypePublisher]] = {}
        for publisher in publishers:
            if spec.get_type(publisher.type_name) is None:
                raise ValueError(
                    f"Publisher for token type {publisher.type_name!r} has no type in the compiled TokenSpec "
                    f"(types: {[t.type_name for t in spec.types]})"
                )
            self._publishers.setdefault(publisher.type_name, []).append(publisher)
        for token_type in spec.types:
            if token_type.capacity > 0 and token_type.type_name not in self._publishers:
                raise ValueError(
                    f"Token type {token_type.type_name!r} has capacity {token_type.capacity} but no publisher.\n"
                    "  Rule: one publisher per token type (PDR-0076) — a type with slots and no filler is a "
                    "lying observation, not a skip."
                )
        # Cross-publisher slot disjointness (review Minor-6): where one type carries
        # several publishers (variable_element), their slot sets must be disjoint —
        # an overlapping compiled artifact is a bug that must refuse loudly, never
        # resolve as silent last-writer-wins.
        for type_name, type_publishers in self._publishers.items():
            if len(type_publishers) < 2:
                continue
            claimed_by: dict[int, str] = {}
            overlaps: dict[int, tuple[str, str]] = {}
            for publisher in type_publishers:
                claimed = getattr(publisher, "claimed_slots", None)
                if claimed is None:
                    continue
                name = type(publisher).__name__
                for slot in claimed:
                    if slot in claimed_by:
                        overlaps[slot] = (claimed_by[slot], name)
                    else:
                        claimed_by[slot] = name
            if overlaps:
                detail = "; ".join(f"slot {slot}: {a} and {b}" for slot, (a, b) in sorted(overlaps.items()))
                raise ValueError(
                    f"Token type {type_name!r}: overlapping slot claims across publishers — {detail}.\n"
                    "  Rule: cross-publisher slot sets must be disjoint; an overlapping compiled binding is "
                    "an artifact bug and must be loud, never last-writer-wins."
                )

    def encode(self, batch_size: int, ctx: TokenPublishContext) -> torch.Tensor:
        """Build one tick's token observation, `[batch_size, total_dims]` float32.

        The output tensor is allocated PER TICK (spec §6: stored observations are
        cloned or per-tick allocated — nothing here can alias a previous tick, pinned
        by the replay-aliasing test). Each type's rows are addressed through a
        `.view()` of the flat slice — raises on copy, never `.reshape()`.
        """
        observation = torch.zeros((batch_size, self._spec.total_dims), dtype=torch.float32, device=self._device)
        for type_layout in self._spec.compact_layout().types:
            if type_layout.capacity > 0:
                rows = observation[:, type_layout.start : type_layout.end].view(
                    batch_size,
                    type_layout.capacity,
                    type_layout.compact_row_width,
                )
                for publisher in self._publishers.get(type_layout.type_name, []):
                    publisher.publish(rows, ctx)
        return observation
