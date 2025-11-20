"""Item action handlers (GET, USE_SLOT_N, DROP_SLOT_N)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.items.inventory import InventoryState
    from townlet.items.manager import ItemManager

__all__ = ["ItemActionHandler"]


class ItemActionHandler:
    """Handles item-related actions (pickup, use, drop)."""

    def __init__(
        self,
        manager: ItemManager,
        inventory: InventoryState,
    ) -> None:
        """Initialize action handler.

        Args:
            manager: ItemManager instance
            inventory: InventoryState instance
        """
        self.manager = manager
        self.inventory = inventory

    def handle_get_action(
        self,
        agent_idx: int,
        agent_position: torch.Tensor,  # [position_dim]
        current_tick: int,
    ) -> bool:
        """Handle GET action (pickup item at agent position).

        Args:
            agent_idx: Agent index
            agent_position: Agent position tensor
            current_tick: Current tick

        Returns:
            True if item picked up, False otherwise
        """
        # Find item at agent's position
        agent_pos_tuple = tuple(agent_position.tolist())

        item = None
        for active_item in self.manager.active_items.values():
            if active_item.position == agent_pos_tuple:
                item = active_item
                break

        if item is None:
            return False  # No item at position

        # Try to add to inventory (DENY_PICKUP if full)
        success = self.inventory.add_item(agent_idx, item)

        if success:
            # Remove item from world
            self.manager.despawn_item(item.instance_id, current_tick)

            # TODO: Execute on_pickup Effects commands
            # (deferred to Task 4.5 Environment Integration)

        return success

    def handle_use_slot_action(
        self,
        agent_idx: int,
        slot_idx: int,
        current_tick: int,
    ) -> bool:
        """Handle USE_SLOT_N action (use item in inventory slot).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0-based)
            current_tick: Current tick

        Returns:
            True if item used, False if slot empty
        """
        # Get item from slot (without removing)
        instance_id = self.inventory.get_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot empty

        # TODO: Execute on_use Effects commands
        # (deferred to Task 4.5 Environment Integration)

        # For now, just return success
        return True

    def handle_drop_slot_action(
        self,
        agent_idx: int,
        slot_idx: int,
        agent_position: torch.Tensor,  # [position_dim]
        current_tick: int,
    ) -> bool:
        """Handle DROP_SLOT_N action (drop item from inventory).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0-based)
            agent_position: Agent position (where to drop item)
            current_tick: Current tick

        Returns:
            True if item dropped, False if slot empty
        """
        # Remove item from inventory
        instance_id = self.inventory.remove_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot already empty

        # Get item from manager's despawned tracking
        # (We need to restore it to the world)

        # TODO: Spawn item at agent's position
        # (Need to track item_type from instance_id)
        # This requires extending ItemInstance or tracking in ItemManager

        # For now, just return success
        # (Full implementation in Task 4.5)

        return True
