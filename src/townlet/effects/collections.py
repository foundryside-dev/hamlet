"""Collection resolution for for_each commands."""

from __future__ import annotations

from typing import Any

import torch

MAX_COLLECTION_SIZE = 64


def resolve_collection(
    collection_type: str,
    context: Any,  # ExecutionContext
    radius: float | None = None,
    max_count: int = MAX_COLLECTION_SIZE,
) -> list[int]:
    """Resolve collection to list of indices.

    Args:
        collection_type: Type of collection ("nearby_agents", "all_agents", etc.)
        context: Execution context with agent_positions, etc.
        radius: Radius for spatial queries (required for nearby_agents)

    Returns:
        List of entity indices in collection
    """
    if max_count <= 0:
        raise ValueError("max_count must be positive")

    if collection_type == "all_agents":
        # Return all agent indices
        batch_size = next(iter(context.bars.values())).shape[0]
        return list(range(batch_size))

    elif collection_type == "nearby_agents":
        if radius is None:
            raise ValueError("radius required for 'nearby_agents' collection")
        if context.self_index is None:
            raise ValueError("self_index required for 'nearby_agents' collection")
        if not hasattr(context, "agent_positions") or context.agent_positions is None:
            raise ValueError("agent_positions required for 'nearby_agents' collection")

        # Get self position
        self_pos = context.agent_positions[context.self_index]

        # Compute distances to all agents
        distances = torch.norm(context.agent_positions - self_pos, dim=1)

        # Filter by radius (exclude self)
        device = distances.device
        nearby = torch.where((distances <= radius) & (torch.arange(len(distances), device=device) != context.self_index))[0]

        indices = nearby.tolist()
        if len(indices) > max_count:
            raise RuntimeError(f"for_each collection size {len(indices)} exceeds cap {max_count}")
        return indices

    elif collection_type == "inventory_items":
        inventory = getattr(context, "inventory", None)
        if inventory is None:
            raise ValueError("inventory required for 'inventory_items' collection")
        item_indices: list[int] = []
        for slot in inventory.slots[context.self_index]:
            # slots store instance_id integers; -1 means empty
            value = int(slot.item()) if hasattr(slot, "item") else int(slot)
            if value >= 0:
                item_indices.append(value)
        if len(item_indices) > max_count:
            raise RuntimeError(f"for_each collection size {len(item_indices)} exceeds cap {max_count}")
        return item_indices

    elif collection_type == "active_effects":
        if not getattr(context, "effect_manager", None):
            raise ValueError("effect_manager required for 'active_effects' collection")
        if context.self_index is None:
            raise ValueError("self_index required for 'active_effects' collection")
        effects = context.effect_manager.agent_effects.get(context.self_index, [])
        if len(effects) > max_count:
            raise RuntimeError(f"for_each collection size {len(effects)} exceeds cap {max_count}")
        return [eff.target_entity_id for eff in effects]

    else:
        raise ValueError(f"Unknown collection type: {collection_type}")
