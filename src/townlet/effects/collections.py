"""Collection resolution for for_each commands."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import torch

MAX_COLLECTION_SIZE = 256

CollectionResolver = Callable[..., list[int]]


def _resolve_all_agents(context: Any, **_: Any) -> list[int]:
    batch_size = next(iter(context.bars.values())).shape[0]
    return list(range(batch_size))


def _resolve_nearby_agents(context: Any, **kwargs: Any) -> list[int]:
    radius = kwargs.get("radius")
    if radius is None:
        raise ValueError("radius required for 'nearby_agents' collection")
    if context.self_index is None:
        raise ValueError("self_index required for 'nearby_agents' collection")
    if not hasattr(context, "agent_positions") or context.agent_positions is None:
        raise ValueError("agent_positions required for 'nearby_agents' collection")

    self_pos = context.agent_positions[context.self_index]
    distances = torch.norm(context.agent_positions - self_pos, dim=1)
    device = distances.device
    nearby = torch.where((distances <= radius) & (torch.arange(len(distances), device=device) != context.self_index))[0]
    return nearby.tolist()


def _resolve_inventory_items(context: Any, **_: Any) -> list[int]:
    inventory = getattr(context, "inventory", None)
    if inventory is None:
        raise ValueError("inventory required for 'inventory_items' collection")
    item_indices: list[int] = []
    for slot in inventory.slots[context.self_index]:
        value = int(slot.item()) if hasattr(slot, "item") else int(slot)
        if value >= 0:
            item_indices.append(value)
    return item_indices


def _resolve_active_effects(context: Any, **_: Any) -> list[int]:
    if not getattr(context, "effect_manager", None):
        raise ValueError("effect_manager required for 'active_effects' collection")
    if context.self_index is None:
        raise ValueError("self_index required for 'active_effects' collection")
    effects = context.effect_manager.agent_effects.get(context.self_index, [])
    return [eff.target_entity_id for eff in effects]


COLLECTION_RESOLVERS: dict[str, CollectionResolver] = {
    "all_agents": _resolve_all_agents,
    "nearby_agents": _resolve_nearby_agents,
    "inventory_items": _resolve_inventory_items,
    "active_effects": _resolve_active_effects,
}


def register_collection_resolver(name: str, resolver: CollectionResolver) -> None:
    """Register a new collection resolver (overwrites existing name)."""

    COLLECTION_RESOLVERS[name] = resolver


def resolve_collection(
    collection_type: str,
    context: Any,
    max_count: int = MAX_COLLECTION_SIZE,
    **kwargs: Any,
) -> list[int]:
    """Resolve collection to list of indices."""

    if max_count <= 0:
        raise ValueError("max_count must be positive")

    resolver = COLLECTION_RESOLVERS.get(collection_type)
    if resolver is None:
        raise ValueError(f"Unknown collection type: {collection_type}")

    indices = resolver(context=context, **kwargs)
    if len(indices) > max_count:
        raise RuntimeError(f"for_each collection size {len(indices)} exceeds cap {max_count}")
    return indices
