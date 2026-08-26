"""Token observation assembly for :class:`VectorizedHamletEnv`.

Unit-3 Task-10 cut: the fixed-width superset+mask `ObservationEncoder` — raster grid
encoding, local window, position/velocity/meter/affordance/effect/temporal blocks, the
per-field VFS mirror read and the activity mask — is DELETED. The environment's
observation is the compiled `TokenSpec` serialization, assembled by
:class:`TokenObservationEncoder` from one publisher per token type.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import torch

from townlet.environment.token_publishers import (
    AffordanceTokenDeclaration,
    AffordanceTokenPublisher,
    AgentTokenPublisher,
    EffectTokenPublisher,
    ItemTokenPublisher,
    MeterTokenPublisher,
    RegistryVariableElementPublisher,
    SelfTokenPublisher,
    TokenPublishContext,
    TokenTypePublisher,
)
from townlet.universe.dto.token_spec import (
    EffectDeclaration,
    MeterDeclaration,
    TokenSpec,
)

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


def build_token_observation_encoder(env: VectorizedHamletEnv) -> TokenObservationEncoder:
    """Assemble the live token encoder for one environment (unit-3 Task-10 swap).

    One publisher per token type with capacity > 0 (PDR-0076: dispatch on the compiled
    type, never on a name); a type with slots and no publisher is a refusal inside
    :class:`TokenObservationEncoder`, not a skip. Everything here is derived from the
    COMPILED artifact — capacities, slot bindings and their order — never from runtime
    counts.
    """
    spec = env.universe.token_spec
    device = env.device
    publishers: list[TokenTypePublisher] = []

    self_type = spec.get_type("self")
    if self_type is not None and self_type.capacity > 0:
        publishers.append(SelfTokenPublisher(self_type, env.substrate))

    meter_type = spec.get_type("meter")
    if meter_type is not None and meter_type.capacity > 0:
        publishers.append(
            MeterTokenPublisher(meter_type, _meter_declarations(env), env.meter_name_to_index, device)
        )

    affordance_type = spec.get_type("affordance")
    if affordance_type is not None and affordance_type.capacity > 0:
        publishers.append(
            AffordanceTokenPublisher(
                affordance_type,
                env.substrate,
                _affordance_declarations(env),
                {meter.name: meter for meter in _meter_declarations(env)},
                device,
            )
        )

    agent_type = spec.get_type("agent")
    if agent_type is not None and agent_type.capacity > 0:
        # Capacity is 0 on every shipped pack: `agent` capacity derives from a DECLARED
        # shared-world count, and no pack declares one (`num_agents` is a batch of
        # independent worlds and must never size this).
        publishers.append(AgentTokenPublisher(agent_type, env.substrate))

    item_type = spec.get_type("item")
    if item_type is not None and item_type.capacity > 0:
        publishers.append(ItemTokenPublisher(item_type, env.substrate, _owner_slot_capacity(env)))

    effect_type = spec.get_type("effect")
    if effect_type is not None and effect_type.capacity > 0:
        publishers.append(
            EffectTokenPublisher(effect_type, _effect_declarations(env), _owner_slot_capacity(env), device)
        )

    element_type = spec.get_type("variable_element")
    if element_type is not None and element_type.capacity > 0:
        # Item-profile exposure has no compile emission yet (the compiler refuses an
        # `exposed_to` on an item-profile variable and names the landing), so every
        # compiled `variable_element` slot is registry-backed today. The item-arena half
        # wires in with the unit-5 pack migration that authors the first one.
        publishers.append(
            RegistryVariableElementPublisher(element_type, env.vfs_registry, list(element_type.slot_bindings), device)
        )

    return TokenObservationEncoder(spec, publishers, device)


def _meter_declarations(env: VectorizedHamletEnv) -> list[MeterDeclaration]:
    """The level's bars.yaml declarations, in declaration order."""
    return [
        MeterDeclaration(
            name=meter.name,
            initial=meter.initial,
            min=meter.bounds.min,
            max=meter.bounds.max,
            lethal_min=meter.bounds.lethal_min,
            lethal_max=meter.bounds.lethal_max,
            passive_depletion=meter.depletion.passive,
            move_depletion=meter.depletion.move,
            interact_depletion=meter.depletion.interact,
            natural_recovery=meter.recovery.natural,
        )
        for meter in env.level.bars.meters
    ]


def _affordance_declarations(env: VectorizedHamletEnv) -> list[AffordanceTokenDeclaration]:
    """Declared identity per compiled affordance slot (spec §1, applied recursively)."""
    interaction_types = {affordance.name: affordance.interaction_type for affordance in env.level.affordances.affordances}
    declarations: list[AffordanceTokenDeclaration] = []
    for info in env.level.affordance_metadata.affordances:
        interaction_type = interaction_types.get(info.id)
        if interaction_type is None:
            raise ValueError(
                f"Affordance {info.id!r} is in the compiled affordance metadata but not in the level's "
                "affordances.yaml; recompile the config pack."
            )
        declarations.append(
            AffordanceTokenDeclaration(
                id=info.id,
                interaction_type=str(interaction_type),
                effect_deltas=dict(info.effects),
            )
        )
    return declarations


def _effect_declarations(env: VectorizedHamletEnv) -> list[EffectDeclaration]:
    """Declared effect identity in CATALOG ORDER — `EffectSlotBatch.effect_indices`
    indexes this list, so the order is the compiled catalog's, not a runtime one."""
    catalog = env.universe.compiled_effect_catalog
    if catalog is None:
        return []
    return [
        EffectDeclaration(
            id=effect.id,
            scope=effect.scope,
            duration=effect.duration,
            intensity=effect.intensity,
            reapply_policy=effect.reapply_policy,
        )
        for effect in catalog.effects.values()
    ]


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
    """The environment's observation (unit-3 Task-10 swap).

    Dispatches one publisher per token type (PDR-0076: dispatch on type, never a name
    to match) over the compiled TokenSpec's serialization layout. `variable_element`
    carries TWO publishers — registry-arena and item-arena (spec §3).

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
        offset = 0
        for token_type in self._spec.types:
            width = token_type.capacity * token_type.row_width
            if token_type.capacity > 0:
                rows = observation[:, offset : offset + width].view(batch_size, token_type.capacity, token_type.row_width)
                for publisher in self._publishers.get(token_type.type_name, []):
                    publisher.publish(rows, ctx)
            offset += width
        return observation
