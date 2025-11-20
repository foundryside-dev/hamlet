"""Collection resolution for for_each commands."""

from __future__ import annotations

from typing import Any

import torch


def resolve_collection(
    collection_type: str,
    context: Any,  # ExecutionContext
    radius: float | None = None,
) -> list[int]:
    """Resolve collection to list of indices.

    Args:
        collection_type: Type of collection ("nearby_agents", "all_agents", etc.)
        context: Execution context with agent_positions, etc.
        radius: Radius for spatial queries (required for nearby_agents)

    Returns:
        List of entity indices in collection
    """
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
        nearby = torch.where((distances <= radius) & (torch.arange(len(distances)) != context.self_index))[0]

        return nearby.tolist()

    elif collection_type == "inventory_items":
        # Not implemented yet (requires inventory reference)
        raise NotImplementedError("inventory_items collection not yet supported")

    elif collection_type == "active_effects":
        # Not implemented yet (requires effect_manager reference)
        raise NotImplementedError("active_effects collection not yet supported")

    else:
        raise ValueError(f"Unknown collection type: {collection_type}")
