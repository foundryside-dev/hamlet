"""Agent inventory state management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.items.instance import ItemInstance

__all__ = ["InventoryState"]


class InventoryState:
    """Agent inventory state ([batch, max_items_per_agent] slots).

    Stores item instance_ids in fixed-size tensor.
    -1 indicates empty slot.
    """

    def __init__(
        self,
        batch_size: int,
        max_items_per_agent: int,
        device: str = "cpu",
    ) -> None:
        """Initialize inventory state.

        Args:
            batch_size: Number of agents
            max_items_per_agent: Max items per agent
            device: PyTorch device
        """
        self.batch_size = batch_size
        self.max_items_per_agent = max_items_per_agent
        self.device = device

        # Inventory slots: [batch, max_items_per_agent]
        # -1 = empty slot, >=0 = item instance_id
        self.slots = torch.full(
            (batch_size, max_items_per_agent),
            fill_value=-1,
            dtype=torch.long,
            device=device,
        )

    def add_item(self, agent_idx: int, item: ItemInstance) -> bool:
        """Add item to agent's inventory (DENY_PICKUP policy).

        Args:
            agent_idx: Agent index
            item: Item instance to add

        Returns:
            True if added, False if inventory full (DENY_PICKUP)
        """
        # Find first empty slot (-1)
        empty_slots = self.slots[agent_idx] == -1
        if not empty_slots.any():
            return False  # Inventory full (DENY_PICKUP policy)

        # Get first empty slot index
        slot_idx = empty_slots.nonzero(as_tuple=True)[0][0].item()

        # Store item instance_id
        self.slots[agent_idx, slot_idx] = item.instance_id

        return True

    def remove_item(self, agent_idx: int, slot_idx: int) -> int | None:
        """Remove item from inventory slot.

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0 to max_items_per_agent-1)

        Returns:
            Item instance_id if removed, None if slot empty
        """
        if slot_idx < 0 or slot_idx >= self.max_items_per_agent:
            raise ValueError(f"Invalid slot_idx: {slot_idx}")

        instance_id = self.slots[agent_idx, slot_idx].item()
        if instance_id == -1:
            return None  # Slot already empty

        # Clear slot
        self.slots[agent_idx, slot_idx] = -1

        return instance_id

    def get_item(self, agent_idx: int, slot_idx: int) -> int | None:
        """Get item instance_id from slot (without removing).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index

        Returns:
            Item instance_id or None if empty
        """
        if slot_idx < 0 or slot_idx >= self.max_items_per_agent:
            raise ValueError(f"Invalid slot_idx: {slot_idx}")

        instance_id = self.slots[agent_idx, slot_idx].item()
        return instance_id if instance_id != -1 else None

    def is_full(self, agent_idx: int) -> bool:
        """Check if agent's inventory is full."""
        return not (self.slots[agent_idx] == -1).any()

    def count_items(self, agent_idx: int) -> int:
        """Count non-empty slots in agent's inventory."""
        return (self.slots[agent_idx] != -1).sum().item()
