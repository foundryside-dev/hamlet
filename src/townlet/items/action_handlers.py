"""Item action handlers (GET, USE_SLOT_N, DROP_SLOT_N)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import torch

if TYPE_CHECKING:
    from townlet.items.inventory import InventoryState
    from townlet.items.manager import ItemManager
    from townlet.vfs.registry import VariableRegistry

from townlet.effects.context import ExecutionContext
from townlet.effects.executor import CommandExecutor

__all__ = ["ItemActionHandler", "NullEffectManager"]


class NullEffectManager:
    """Fallback EffectManager to satisfy fail-forward context; raises on spawn_effect."""

    def spawn_effect(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("EffectManager is not configured; spawn_effect is unavailable")


class ItemActionHandler:
    """Handles item-related actions (pickup, use, drop)."""

    def __init__(
        self,
        manager: ItemManager,
        inventory: InventoryState,
        command_executor: CommandExecutor,
        vfs_registry: VariableRegistry,
        meter_name_to_index: dict[str, int],
        effect_manager: Any | None = None,
        affordance_overrides: dict[str, bool] | None = None,
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
        self.effect_manager = effect_manager or NullEffectManager()
        self.affordance_overrides = affordance_overrides
        # Cache custom verb specs for masking/dispatch
        self.custom_action_specs = {
            name: (item_type, scope, command_name) for name, item_type, scope, command_name in manager.get_custom_action_specs()
        }

    def _execute_interaction(
        self,
        item_type: str,
        agent_idx: int,
        interaction: Literal["on_pickup", "on_use", "on_drop"],
        meters: torch.Tensor,  # [batch, num_meters] - passed from environment
        item_vfs_index: int | None = None,  # NEW: Item's VFS index for self-modification
        current_tick: int | None = None,
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
            effect_manager=self.effect_manager,
            item_manager=self.manager,
            scheduler=getattr(self.effect_manager, "scheduler", None),
            current_tick=current_tick or 0,
            affordance_overrides=self.affordance_overrides,
        )

        # Execute all commands
        for command in commands:
            self.command_executor.execute(command, context)

    @staticmethod
    def _positions_match(agent_pos: torch.Tensor, item_pos: tuple[int, ...] | tuple[float, ...]) -> bool:
        """Match agent/item positions without forcing integer rounding.

        Continuous substrates keep fractional coordinates; rounding them to ints
        breaks equality checks for local custom verbs. Compare in float space
        with a small tolerance so both discrete and continuous positions work.
        """

        if agent_pos.numel() != len(item_pos):
            return False

        # Always compare in float space; rtol=0 keeps comparisons strict.
        agent_f = agent_pos.to(dtype=torch.float32)
        item_f = torch.as_tensor(item_pos, device=agent_f.device, dtype=agent_f.dtype)
        return torch.allclose(agent_f, item_f, atol=1e-4, rtol=0.0)

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
            # Exclusive items leave the world when picked up; shared items remain in place.
            if item.exclusive:
                self.manager.lift_item(item.instance_id)

            # Execute on_pickup Effects commands
            self._execute_interaction(
                item_type=item.item_type,
                agent_idx=agent_idx,
                interaction="on_pickup",
                meters=meters,
                item_vfs_index=item.vfs_index,  # NEW: Pass vfs_index
                current_tick=current_tick,
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
            current_tick=current_tick,
        )

        return True

    def _execute_commands(
        self,
        commands: list,
        *,
        agent_idx: int,
        item: Any,
        meters: torch.Tensor,
        current_tick: int,
    ) -> None:
        """Execute a list of compiled commands for a custom verb."""
        if not commands:
            return

        bars_dict = {name: meters[:, idx] for name, idx in self.meter_name_to_index.items()}
        context = ExecutionContext(
            bars=bars_dict,
            vfs_registry=self.vfs_registry,
            self_index=item.vfs_index,
            target_index=agent_idx,
            self_is_item=True,
            effect_manager=self.effect_manager,
            item_manager=self.manager,
            scheduler=getattr(self.effect_manager, "scheduler", None),
            current_tick=current_tick,
            affordance_overrides=self.affordance_overrides,
        )

        for command in commands:
            self.command_executor.execute(command, context)

    def compute_custom_action_masks(self, action_space, action_masks: torch.Tensor, agent_positions: torch.Tensor) -> None:
        """Mask custom item actions based on availability."""
        if not self.custom_action_specs:
            return

        # Build a quick lookup of held items per agent for inventory verbs
        for action_name, (item_type, scope, command_name) in self.custom_action_specs.items():
            try:
                action_id = action_space.get_action_by_name(action_name).id
            except ValueError:
                continue

            available = torch.zeros(action_masks.shape[0], dtype=torch.bool, device=action_masks.device)

            if scope == "inventory":
                for agent_idx in range(self.inventory.slots.shape[0]):
                    slot_items = self.inventory.slots[agent_idx]
                    for instance_id in slot_items.tolist():
                        if instance_id == -1:
                            continue
                        item = self.inventory.items.get(int(instance_id))
                        if item is not None and item.item_type == item_type:
                            available[agent_idx] = True
                            break
            else:  # local
                for agent_idx, agent_pos in enumerate(agent_positions):
                    for item in self.manager.active_items.values():
                        if item.item_type == item_type and self._positions_match(agent_pos, item.position):
                            available[agent_idx] = True
                            break

            action_masks[~available, action_id] = False

    def handle_custom_action(
        self,
        action_name: str,
        agent_idx: int,
        agent_position: torch.Tensor,
        current_tick: int,
        meters: torch.Tensor,
    ) -> bool:
        """Execute a custom item verb if available."""
        spec = self.custom_action_specs.get(action_name)
        if spec is None:
            return False
        item_type, scope, command_name = spec

        # Resolve compiled commands
        compiled = next((t for t in self.manager.compiled_item_types if t.id == item_type), None)
        if compiled is None:
            return False

        if scope == "inventory":
            # Pick first matching held item
            item_obj = None
            for idx in range(self.inventory.max_items_per_agent):
                candidate = self.inventory.get_item(agent_idx, idx)
                if candidate is None:
                    continue
                candidate_item = self.inventory.items.get(candidate)
                if candidate_item and candidate_item.item_type == item_type:
                    item_obj = candidate_item
                    break
            if item_obj is None:
                return False
            commands = compiled.compiled_inventory_commands.get(command_name, [])
            self._execute_commands(commands, agent_idx=agent_idx, item=item_obj, meters=meters, current_tick=current_tick)
            return True

        # local scope: find matching item at agent position (support continuous coords)
        item_obj = None
        for item in self.manager.active_items.values():
            if item.item_type == item_type and self._positions_match(agent_position, item.position):
                item_obj = item
                break
        if item_obj is None:
            return False
        commands = compiled.compiled_local_commands.get(command_name, [])
        self._execute_commands(commands, agent_idx=agent_idx, item=item_obj, meters=meters, current_tick=current_tick)
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

        # Shared items remain in the world; exclusive items return to the grid.
        if item.exclusive:
            agent_pos_tuple = tuple(agent_position.tolist())
            self.manager.place_item(
                instance_id=instance_id,  # Use existing instance (NOT spawn_item)
                position=agent_pos_tuple,
            )

        return True
