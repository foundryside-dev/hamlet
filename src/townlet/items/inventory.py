"""Agent inventory state management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.items.instance import ItemInstance

__all__ = ["InventoryState"]


class InventoryState:
    """Fixed-size inventory for agents using GPU tensors.

    Storage:
    - slots: [batch, max_items_per_agent] tensor of instance IDs (-1 = empty)
    - items: dict[instance_id -> ItemInstance] for metadata lookup
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

        # Slot storage: -1 = empty, ≥0 = instance_id
        self.slots = torch.full(
            (batch_size, max_items_per_agent),
            fill_value=-1,
            dtype=torch.long,
            device=device,
        )

        # Item metadata lookup
        self.items: dict[int, ItemInstance] = {}

    def add_item(self, agent_idx: int, item: ItemInstance) -> bool:
        """Add item to first empty slot (DENY_PICKUP if full).

        Args:
            agent_idx: Agent index
            item: ItemInstance to add

        Returns:
            True if added, False if inventory full
        """
        # Find first empty slot
        agent_slots = self.slots[agent_idx]
        empty_mask = agent_slots == -1

        if not empty_mask.any():
            return False  # DENY_PICKUP policy

        # Get first empty slot index
        slot_idx = int(torch.where(empty_mask)[0][0].item())

        # Store instance ID
        self.slots[agent_idx, slot_idx] = item.instance_id

        # Store item metadata
        self.items[item.instance_id] = item

        return True

    def remove_item(self, agent_idx: int, slot_idx: int) -> int | None:
        """Remove item from slot.

        Args:
            agent_idx: Agent index
            slot_idx: Slot index

        Returns:
            Instance ID if removed, None if slot empty
        """
        instance_id = int(self.slots[agent_idx, slot_idx].item())

        if instance_id == -1:
            return None

        # Clear slot
        self.slots[agent_idx, slot_idx] = -1

        # Remove from metadata (keep for respawn tracking)
        # Actually DON'T remove - need it for DROP action
        # self.items.pop(instance_id, None)

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

    def reset(self) -> None:
        """Clear all inventory slots and metadata."""
        self.slots.fill_(-1)
        self.items.clear()
