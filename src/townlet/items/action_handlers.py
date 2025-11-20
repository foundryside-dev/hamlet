"""Item action handlers (GET, USE_SLOT_N, DROP_SLOT_N)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import torch

if TYPE_CHECKING:
    from townlet.items.inventory import InventoryState
    from townlet.items.manager import ItemManager
    from townlet.vfs.registry import VariableRegistry

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor

__all__ = ["ItemActionHandler"]


class ItemActionHandler:
    """Handles item-related actions (pickup, use, drop)."""

    def __init__(
        self,
        manager: ItemManager,
        inventory: InventoryState,
        command_executor: CommandExecutor,
        vfs_registry: VariableRegistry,
        meter_name_to_index: dict[str, int],
    ) -> None:
        """Initialize action handler.

        Args:
            manager: ItemManager instance
            inventory: InventoryState instance
            command_executor: CommandExecutor for Effects
            vfs_registry: VFS registry for Effects context
            meter_name_to_index: Bar name to index mapping
        """
        self.manager = manager
        self.inventory = inventory
        self.command_executor = command_executor
        self.vfs_registry = vfs_registry
        self.meter_name_to_index = meter_name_to_index

    def _execute_interaction(
        self,
        item_type: str,
        agent_idx: int,
        interaction: Literal["on_pickup", "on_use", "on_drop"],
        meters: torch.Tensor,  # [batch, num_meters] - passed from environment
        item_vfs_index: int | None = None,  # NEW: Item's VFS index for self-modification
    ) -> None:
        """Execute Effects commands for item interaction.

        Args:
            item_type: Item type ID (e.g., "apple")
            agent_idx: Agent performing interaction
            interaction: Which interaction type to execute
            meters: Current meters tensor from environment
            item_vfs_index: Item's VFS index for self-modification (NEW)
        """
        # Find compiled item type
        compiled_type = next(
            (t for t in self.manager.compiled_item_types if t.id == item_type),
            None,
        )

        if compiled_type is None:
            return  # Item type not found

        # Get compiled commands for this interaction
        if interaction == "on_pickup":
            commands = compiled_type.compiled_on_pickup
        elif interaction == "on_use":
            commands = compiled_type.compiled_on_use
        elif interaction == "on_drop":
            commands = compiled_type.compiled_on_drop
        else:
            return

        if not commands:
            return  # No commands to execute

        # Build ExecutionContext targeting the agent
        # Pattern: Same as affordance Effects execution
        bars_dict = {name: meters[:, idx] for name, idx in self.meter_name_to_index.items()}

        # Context mapping for item interactions:
        # - target = Agent performing the action (can access target.bar.*, target.vfs.*)
        # - self = The Item itself (can access self.vfs.durability, etc.)
        context = ExecutionContext(
            bars=bars_dict,
            vfs_registry=self.vfs_registry,
            self_index=item_vfs_index,  # NEW: Pass item's vfs_index
            target_index=agent_idx,  # Agent is the target
            self_is_item=True,  # NEW: Mark self as item for VFS routing
        )

        # Execute all commands
        for command in commands:
            self.command_executor.execute(command, context)

    def handle_get_action(
        self,
        agent_idx: int,
        agent_position: torch.Tensor,  # [position_dim]
        current_tick: int,
        meters: torch.Tensor,  # [batch, num_meters]
    ) -> bool:
        """Handle GET action (pickup item at agent position).

        Args:
            agent_idx: Agent index
            agent_position: Agent position tensor
            current_tick: Current tick
            meters: Current meters tensor from environment

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
            # Move item from world to held state (preserves VFS state)
            self.manager.lift_item(item.instance_id)

            # Execute on_pickup Effects commands
            self._execute_interaction(
                item_type=item.item_type,
                agent_idx=agent_idx,
                interaction="on_pickup",
                meters=meters,
                item_vfs_index=item.vfs_index,  # NEW: Pass vfs_index
            )

        return success

    def handle_use_slot_action(
        self,
        agent_idx: int,
        slot_idx: int,
        current_tick: int,
        meters: torch.Tensor,  # [batch, num_meters]
    ) -> bool:
        """Handle USE_SLOT_N action (use item in inventory slot).

        Args:
            agent_idx: Agent index
            slot_idx: Inventory slot index (0-based)
            current_tick: Current tick
            meters: Current meters tensor from environment

        Returns:
            True if item used, False if slot empty
        """
        # Get item from slot (without removing)
        instance_id = self.inventory.get_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot empty

        # Get item metadata from inventory
        # (ItemInstance tracks item_type at line 17 of instance.py)
        item = self.inventory.items.get(instance_id)

        if item is None:
            return False  # Item metadata missing (shouldn't happen)

        # Execute on_use Effects commands
        self._execute_interaction(
            item_type=item.item_type,
            agent_idx=agent_idx,
            interaction="on_use",
            meters=meters,
            item_vfs_index=item.vfs_index,  # NEW: Pass vfs_index
        )

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
        # Remove item from inventory slot
        instance_id = self.inventory.remove_item(agent_idx, slot_idx)

        if instance_id is None:
            return False  # Slot already empty

        # Get item metadata from inventory
        item = self.inventory.items.get(instance_id)

        if item is None:
            return False  # Item metadata missing (shouldn't happen)

        # Execute on_drop Effects commands (if any exist and need meters)
        # Note: Current items have empty on_drop arrays, so this is a no-op
        # Future: If on_drop Effects require meters, we'd need to pass them here

        # Place item back in world at agent's position (preserves VFS state)
        agent_pos_tuple = tuple(agent_position.tolist())
        self.manager.place_item(
            instance_id=instance_id,  # Use existing instance (NOT spawn_item)
            position=agent_pos_tuple,
        )

        return True
