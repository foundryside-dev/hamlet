"""Action execution for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    from townlet.vfs import VTCInteractionProgressResult


class ActionExecutor:
    """Execute movement, custom, item, and affordance interaction actions."""

    def __init__(self, env: VectorizedHamletEnv) -> None:
        self._env = env

    def _execute_actions(self, actions: torch.Tensor) -> dict:
        """Execute movement, interaction, and wait actions."""
        env = self._env
        custom_action_start_id = env.action_space.substrate_action_count

        old_positions = env.positions.clone()

        substrate_mask = actions < custom_action_start_id
        if substrate_mask.any():
            movement_deltas = env._movement_deltas[actions[substrate_mask]]
            env.positions[substrate_mask] = env.substrate.apply_movement(env.positions[substrate_mask], movement_deltas)

        velocity = (env.positions - old_positions).float()
        env._velocity = velocity

        if "velocity_x" in env.vfs_registry._definitions:
            env.vfs_registry.set("velocity_x", velocity[:, 0], writer="engine")

        if "velocity_y" in env.vfs_registry._definitions and velocity.shape[1] >= 2:
            env.vfs_registry.set("velocity_y", velocity[:, 1], writer="engine")

        if "velocity_z" in env.vfs_registry._definitions and velocity.shape[1] >= 3:
            env.vfs_registry.set("velocity_z", velocity[:, 2], writer="engine")

        if "velocity_magnitude" in env.vfs_registry._definitions:
            magnitude = torch.norm(velocity, dim=1)
            env.vfs_registry.set("velocity_magnitude", magnitude, writer="engine")

        movement_actions = env._movement_deltas.ne(0).any(dim=1)
        movement_mask = torch.zeros(env.num_agents, dtype=torch.bool, device=env.device)
        if substrate_mask.any():
            movement_mask[substrate_mask] = movement_actions[actions[substrate_mask]]
        if movement_mask.any():
            movement_costs = torch.zeros(env.meter_count, device=env.device)
            for bar in env.bars_config.meters:
                idx = env.meter_name_to_index.get(bar.name)
                if idx is not None:
                    movement_costs[idx] = float(bar.depletion.move)

            env.meters[movement_mask] -= movement_costs.unsqueeze(0)
            env.meters = torch.clamp(env.meters, 0.0, 1.0)

        if env.item_handler is not None:
            current_ticks = env.step_counts.clone()
            try:
                get_action = env.action_space.get_action_by_name("GET")
            except ValueError:
                get_action = None

            if get_action is not None:
                get_action_id = get_action.id
                get_mask = actions == get_action_id
                if get_mask.any():
                    for agent_idx in torch.where(get_mask)[0]:
                        env.item_handler.handle_get_action(
                            agent_idx=int(agent_idx.item()),
                            agent_position=env.positions[agent_idx],
                            current_tick=int(current_ticks[agent_idx].item()),
                            meters=env.meters,
                        )

            if env.item_inventory is not None:
                for slot_idx in range(env.item_inventory.max_items_per_agent):
                    use_action_name = f"USE_SLOT_{slot_idx}"
                    try:
                        use_action = env.action_space.get_action_by_name(use_action_name)
                    except ValueError:
                        use_action = None

                    if use_action is not None:
                        use_action_id = use_action.id
                        use_mask = actions == use_action_id
                        if use_mask.any():
                            for agent_idx in torch.where(use_mask)[0]:
                                env.item_handler.handle_use_slot_action(
                                    agent_idx=int(agent_idx.item()),
                                    slot_idx=slot_idx,
                                    current_tick=int(current_ticks[agent_idx].item()),
                                    meters=env.meters,
                                )

                for slot_idx in range(env.item_inventory.max_items_per_agent):
                    drop_action_name = f"DROP_SLOT_{slot_idx}"
                    try:
                        drop_action = env.action_space.get_action_by_name(drop_action_name)
                    except ValueError:
                        drop_action = None

                    if drop_action is not None:
                        drop_action_id = drop_action.id
                        drop_mask = actions == drop_action_id
                        if drop_mask.any():
                            for agent_idx in torch.where(drop_mask)[0]:
                                env.item_handler.handle_drop_slot_action(
                                    agent_idx=int(agent_idx.item()),
                                    slot_idx=slot_idx,
                                    agent_position=env.positions[agent_idx],
                                    current_tick=int(current_ticks[agent_idx].item()),
                                )

            for action_name in env.item_handler.custom_action_specs.keys():
                try:
                    action_id = env.action_space.get_action_by_name(action_name).id
                except ValueError:
                    continue
                action_mask = actions == action_id
                if action_mask.any():
                    for agent_idx in torch.where(action_mask)[0]:
                        env.item_handler.handle_custom_action(
                            action_name=action_name,
                            agent_idx=int(agent_idx.item()),
                            agent_position=env.positions[agent_idx],
                            current_tick=int(current_ticks[agent_idx].item()),
                            meters=env.meters,
                        )

        interact_action_idx = env.action_ids.get("INTERACT")

        successful_interactions = {}
        progress_advanced = False
        if interact_action_idx is not None:
            interact_mask = (actions == interact_action_idx) & substrate_mask
            if interact_mask.any():
                interaction_costs = torch.zeros(env.meter_count, device=env.device)
                for bar in env.bars_config.meters:
                    idx = env.meter_name_to_index.get(bar.name)
                    if idx is not None:
                        interaction_costs[idx] = float(bar.depletion.interact)

                env.meters[interact_mask] -= interaction_costs.unsqueeze(0)
                env.meters = torch.clamp(env.meters, 0.0, 1.0)

                successful_interactions = env._handle_interactions(interact_mask)
                progress_advanced = env.enable_temporal_mechanics and env.vtc_interaction_progress_program.has_multi_tick_affordances()

        if env.enable_temporal_mechanics and env.vtc_interaction_progress_program.has_multi_tick_affordances() and not progress_advanced:
            self._advance_vtc_interaction_progress({})

        return successful_interactions

    def _handle_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT actions with multi-tick accumulation."""
        env = self._env
        if not env.enable_temporal_mechanics:
            return env._handle_instant_interactions(interact_mask)

        if not env.vtc_interaction_progress_program.has_multi_tick_affordances():
            return env._handle_instant_interactions(interact_mask)

        successful_interactions: dict[int, str] = {}
        multi_tick_interactions: dict[int, str] = {}
        interaction_agents_by_affordance: dict[str, list[int]] = {}

        for affordance_name, affordance_pos in env.affordances.items():
            if not env._is_affordance_open(affordance_name):
                continue

            at_affordance = env.substrate.is_on_position(env.positions, affordance_pos) & interact_mask

            if not at_affordance.any():
                continue

            is_multi_tick = env.vtc_interaction_progress_program.contains_affordance(affordance_name)
            cost_mode = "per_tick" if is_multi_tick else "instant"
            # Gate on EVERY declared cost, not just money. The previous form read a
            # single hardcoded money meter, so an affordance declaring energy or mood
            # costs was affordable to an agent who could not pay them.
            at_affordance = at_affordance & env.affordance_engine.can_afford(affordance_name, env.meters, cost_mode=cost_mode)

            if not at_affordance.any():
                continue

            if not is_multi_tick:
                agent_indices = torch.where(at_affordance)[0]
                for agent_idx in agent_indices:
                    successful_interactions[int(agent_idx.item())] = affordance_name
                env.meters = env.affordance_engine.apply_instant_interaction(
                    meters=env.meters,
                    affordance_name=affordance_name,
                    agent_mask=at_affordance,
                    current_tick=env.global_tick,
                )
                continue

            agent_indices = torch.where(at_affordance)[0]

            for agent_idx in agent_indices:
                agent_idx_int = int(agent_idx.item())
                successful_interactions[agent_idx_int] = affordance_name
                multi_tick_interactions[agent_idx_int] = affordance_name
                interaction_agents_by_affordance.setdefault(affordance_name, []).append(agent_idx_int)

        progress_result = self._advance_vtc_interaction_progress(multi_tick_interactions)

        for affordance_name, grouped_agent_indices in interaction_agents_by_affordance.items():
            agent_mask = torch.zeros(env.num_agents, dtype=torch.bool, device=env.device)
            agent_mask[torch.tensor(grouped_agent_indices, device=env.device, dtype=torch.long)] = True

            for ticks_done in torch.unique(progress_result.ticks_done[agent_mask]):
                if int(ticks_done.item()) <= 0:
                    continue
                tick_mask = agent_mask & (progress_result.ticks_done == ticks_done)
                completion_mask = tick_mask & progress_result.completion_mask
                env.meters = env.affordance_engine.apply_vtc_multi_tick_effects(
                    meters=env.meters,
                    affordance_name=affordance_name,
                    current_tick=int(ticks_done.item()) - 1,
                    agent_mask=tick_mask,
                    completion_mask=completion_mask,
                )

        env._update_affordance_tracking(successful_interactions)

        return successful_interactions

    def _advance_vtc_interaction_progress(self, successful_interactions: dict[int, str]) -> VTCInteractionProgressResult:
        """Advance VTC-owned multi-tick progress and sync the environment state."""
        env = self._env
        result = env.vtc_interaction_progress_program.apply(
            interaction_affordances=successful_interactions,
            positions=env.positions,
            interaction_progress=env.interaction_progress,
            last_affordances=env.last_interaction_affordance,
            last_positions=env.last_interaction_position,
            active_mask=torch.logical_not(env.dones),
            device=env.device,
        )
        env.interaction_progress = result.interaction_progress
        env.last_interaction_affordance = result.last_affordances
        env.last_interaction_position = result.last_positions
        return result

    def _handle_instant_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT action at affordances in instant mode."""
        env = self._env
        successful_interactions = {}

        for affordance_name, affordance_pos in env.affordances.items():
            if env.enable_temporal_mechanics and not env._is_affordance_open(affordance_name):
                continue

            at_affordance = env.substrate.is_on_position(env.positions, affordance_pos) & interact_mask

            if not at_affordance.any():
                continue

            # Gate on EVERY declared cost. get_affordance_cost() returned only the
            # money component — and, despite its docstring promising a normalized
            # [0,1] value, returned the raw declared amount.
            at_affordance = at_affordance & env.affordance_engine.can_afford(affordance_name, env.meters, cost_mode="instant")

            if not at_affordance.any():
                continue

            agent_indices = torch.where(at_affordance)[0]
            for agent_idx in agent_indices:
                successful_interactions[agent_idx.item()] = affordance_name

            env.meters = env.affordance_engine.apply_instant_interaction(
                meters=env.meters,
                affordance_name=affordance_name,
                agent_mask=at_affordance,
                current_tick=env.global_tick,
            )

        env._update_affordance_tracking(successful_interactions)

        return successful_interactions
