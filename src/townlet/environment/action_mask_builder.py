"""ActionMaskBuilder — per-tick valid-action computation.

Extracted from ``VectorizedHamletEnv.get_action_masks`` to keep the env
shell focused on tick choreography. The builder is constructed once and
called every tick with the per-step state (positions, dones, item state,
affordance state). It carries no mutable state of its own; instances are
safe to share across ticks but not across env resets that change action
space or substrate.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.environment.action_builder import ComposedActionSpace
    from townlet.items import InventoryState, ItemActionHandler, ItemManager
    from townlet.substrate.base import SpatialSubstrate


class ActionMaskBuilder:
    """Compute per-agent action masks from current env state.

    The builder holds references to env-immutable structure (action space,
    substrate, action-id lookups, movement deltas) that does not change
    across ticks. Per-tick state is passed to :meth:`build`.
    """

    def __init__(
        self,
        *,
        action_space: ComposedActionSpace,
        device: torch.device,
        substrate: SpatialSubstrate,
        movement_deltas: torch.Tensor,
        action_ids: dict[str, int],
        enable_temporal_mechanics: bool,
    ) -> None:
        self.action_space = action_space
        self.device = device
        self.substrate = substrate
        self.movement_deltas = movement_deltas
        self.action_ids = action_ids
        self.enable_temporal_mechanics = enable_temporal_mechanics

    def build(
        self,
        *,
        num_agents: int,
        positions: torch.Tensor,
        dones: torch.Tensor | None,
        item_inventory: InventoryState | None,
        item_manager: ItemManager | None,
        item_handler: ItemActionHandler | None,
        affordances: dict[str, Any],
        is_affordance_open: Callable[[str], bool],
    ) -> torch.Tensor:
        """Compute action masks for the current tick.

        Args:
            num_agents: Population size for this tick.
            positions: ``[num_agents, position_dim]`` agent positions.
            dones: ``[num_agents]`` bool mask of terminated agents, or
                ``None`` if the env has not yet populated it.
            item_inventory: Current inventory state, or ``None`` when items
                are disabled.
            item_manager: Item registry, or ``None`` when items are disabled.
            item_handler: Custom action handler, or ``None``.
            affordances: Mapping of affordance name to position.
            is_affordance_open: Predicate that returns ``True`` when the
                given affordance is currently open (for temporal mechanics).

        Returns:
            ``[num_agents, action_dim]`` bool tensor; ``True`` is valid.
        """
        action_masks = self.action_space.get_base_action_mask(
            num_agents=num_agents,
            device=self.device,
        )

        if item_inventory is not None:
            try:
                get_action = self.action_space.get_action_by_name("GET")
            except ValueError:
                get_action = None

            if get_action is not None:
                get_action_id = get_action.id

                inventory_full = ~(item_inventory.slots == -1).any(dim=1)
                if inventory_full.any():
                    action_masks[inventory_full, get_action_id] = False

                if item_manager is not None:
                    for agent_idx in range(num_agents):
                        if not action_masks[agent_idx, get_action_id]:
                            continue

                        agent_pos_tuple = tuple(positions[agent_idx].tolist())
                        item_at_position = False
                        for item in item_manager.active_items.values():
                            if item.position == agent_pos_tuple:
                                item_at_position = True
                                break

                        if not item_at_position:
                            action_masks[agent_idx, get_action_id] = False

            for slot_idx in range(item_inventory.max_items_per_agent):
                try:
                    use_id = self.action_space.get_action_by_name(f"USE_SLOT_{slot_idx}").id
                except ValueError:
                    use_id = None
                try:
                    drop_id = self.action_space.get_action_by_name(f"DROP_SLOT_{slot_idx}").id
                except ValueError:
                    drop_id = None

                if use_id is None and drop_id is None:
                    continue

                slot_items = item_inventory.slots[:, slot_idx]
                slot_empty = slot_items == -1
                if slot_empty.any():
                    if use_id is not None:
                        action_masks[slot_empty, use_id] = False
                    if drop_id is not None:
                        action_masks[slot_empty, drop_id] = False

        if item_handler is not None:
            item_handler.compute_custom_action_masks(self.action_space, action_masks, positions)

        # Boundary constraints — only for discrete rectangular grid
        # substrates, per axis from the substrate's own extents (the old
        # single grid_size masked the y axis with the x extent, which was
        # only correct on square grids — WS-7 first knockdown).
        width = getattr(self.substrate, "width", None)
        height = getattr(self.substrate, "height", None)
        if width is not None and height is not None and self.substrate.position_dim >= 2:
            at_top = positions[:, 1] == 0
            at_bottom = positions[:, 1] == height - 1
            at_left = positions[:, 0] == 0
            at_right = positions[:, 0] == width - 1

            deltas = self.movement_deltas
            up_action_ids = torch.nonzero(deltas[:, 1] < 0, as_tuple=False).squeeze(1)
            down_action_ids = torch.nonzero(deltas[:, 1] > 0, as_tuple=False).squeeze(1)
            left_action_ids = torch.nonzero(deltas[:, 0] < 0, as_tuple=False).squeeze(1)
            right_action_ids = torch.nonzero(deltas[:, 0] > 0, as_tuple=False).squeeze(1)

            if up_action_ids.numel() > 0:
                rows = at_top.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), up_action_ids] = False
            if down_action_ids.numel() > 0:
                rows = at_bottom.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), down_action_ids] = False
            if left_action_ids.numel() > 0:
                rows = at_left.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), left_action_ids] = False
            if right_action_ids.numel() > 0:
                rows = at_right.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), right_action_ids] = False

        if width is not None and height is not None and self.substrate.position_dim == 3:
            at_floor = positions[:, 2] == 0
            if hasattr(self.substrate, "depth"):
                at_ceiling = positions[:, 2] == self.substrate.depth - 1
            else:
                at_ceiling = torch.zeros(num_agents, dtype=torch.bool, device=self.device)

            deltas = self.movement_deltas
            up_z_action_ids = torch.nonzero(deltas[:, 2] > 0, as_tuple=False).squeeze(1)
            down_z_action_ids = torch.nonzero(deltas[:, 2] < 0, as_tuple=False).squeeze(1)
            if up_z_action_ids.numel() > 0:
                rows = at_ceiling.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), up_z_action_ids] = False
            if down_z_action_ids.numel() > 0:
                rows = at_floor.nonzero(as_tuple=True)[0]
                if rows.numel() > 0:
                    action_masks[rows.unsqueeze(1), down_z_action_ids] = False

        # INTERACT — only valid when standing on an open affordance.
        interact_action_idx = self.action_ids.get("INTERACT")
        on_valid_affordance = torch.zeros(num_agents, dtype=torch.bool, device=self.device)

        for affordance_name, affordance_pos in affordances.items():
            if self.enable_temporal_mechanics and not is_affordance_open(affordance_name):
                continue

            on_this_affordance = self.substrate.is_on_position(positions, affordance_pos)
            on_valid_affordance |= on_this_affordance

        if interact_action_idx is not None:
            base_interact_mask = action_masks[:, interact_action_idx].clone()
            action_masks[:, interact_action_idx] = base_interact_mask & on_valid_affordance

        # Terminal agents lose all actions; this must run last so it overrides
        # everything above. Terminal conditions live in bars.yaml; the env's
        # `dones` flag is the single source of truth.
        if dones is not None:
            action_masks[dones] = False

        return action_masks
