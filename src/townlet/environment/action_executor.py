"""Action execution for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


class ActionExecutor:
    """Execute movement, custom, item, and affordance interaction actions."""

    def __init__(self, env: VectorizedHamletEnv) -> None:
        self._env = env

    def _execute_actions(self, actions: torch.Tensor) -> dict:
        """Execute movement, interaction, and wait actions."""
        env = self._env
        custom_action_start_id = env.action_space.substrate_action_count
        custom_mask = actions >= custom_action_start_id

        if custom_mask.any():
            custom_agent_indices = torch.where(custom_mask)[0]
            for agent_idx in custom_agent_indices:
                action_id = int(actions[agent_idx].item())
                action = env.action_space.get_action_by_id(action_id)
                env._apply_custom_action(agent_idx, action)

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

        if env.enable_temporal_mechanics:
            for agent_idx in range(env.num_agents):
                if not torch.equal(old_positions[agent_idx], env.positions[agent_idx]):
                    env.interaction_progress[agent_idx] = 0
                    env.last_interaction_affordance[agent_idx] = None

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

        return successful_interactions

    def _handle_interactions(self, interact_mask: torch.Tensor) -> dict:
        """Handle INTERACT actions with multi-tick accumulation."""
        env = self._env
        if not env.enable_temporal_mechanics:
            return env._handle_instant_interactions(interact_mask)

        if not any(getattr(aff, "interaction_type", "instant") in {"multi_tick", "dual"} for aff in env.affordance_engine.affordances):
            return env._handle_instant_interactions(interact_mask)

        successful_interactions: dict[int, str] = {}

        for affordance_name, affordance_pos in env.affordances.items():
            if not env._is_affordance_open(affordance_name):
                continue

            at_affordance = env.substrate.is_on_position(env.positions, affordance_pos) & interact_mask

            if not at_affordance.any():
                continue

            cost_per_tick = env.affordance_engine.get_affordance_cost(affordance_name, cost_mode="per_tick")
            if env.money_idx is not None:
                can_afford = env.meters[:, env.money_idx] >= cost_per_tick
                at_affordance = at_affordance & can_afford

            if not at_affordance.any():
                continue

            duration_ticks = env.affordance_engine.get_duration_ticks(affordance_name)

            agent_indices = torch.where(at_affordance)[0]

            for agent_idx in agent_indices:
                agent_idx_int = agent_idx.item()
                current_pos = env.positions[agent_idx]

                if env.last_interaction_affordance[agent_idx_int] == affordance_name and torch.equal(
                    current_pos, env.last_interaction_position[agent_idx_int]
                ):
                    env.interaction_progress[agent_idx] += 1
                else:
                    env.interaction_progress[agent_idx] = 1
                    env.last_interaction_affordance[agent_idx_int] = affordance_name
                    env.last_interaction_position[agent_idx_int] = current_pos.clone()

                ticks_done = int(env.interaction_progress[agent_idx].item())

                single_agent_mask = torch.zeros(env.num_agents, dtype=torch.bool, device=env.device)
                single_agent_mask[agent_idx] = True

                env.meters = env.affordance_engine.apply_multi_tick_interaction(
                    meters=env.meters,
                    affordance_name=affordance_name,
                    current_tick=ticks_done - 1,
                    agent_mask=single_agent_mask,
                    check_affordability=False,
                )

                if ticks_done == duration_ticks:
                    env.interaction_progress[agent_idx] = 0
                    env.last_interaction_affordance[agent_idx_int] = None

                successful_interactions[agent_idx_int] = affordance_name

        env._update_affordance_tracking(successful_interactions)

        return successful_interactions

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

            cost_normalized = env.affordance_engine.get_affordance_cost(affordance_name, cost_mode="instant")
            if cost_normalized > 0:
                if env.money_idx is not None:
                    can_afford = env.meters[:, env.money_idx] >= cost_normalized
                    at_affordance = at_affordance & can_afford

                if not at_affordance.any():
                    continue

            agent_indices = torch.where(at_affordance)[0]
            for agent_idx in agent_indices:
                successful_interactions[agent_idx.item()] = affordance_name

            env.meters = env.affordance_engine.apply_interaction(
                meters=env.meters,
                affordance_name=affordance_name,
                agent_mask=at_affordance,
                current_tick=env.global_tick,
            )

        env._update_affordance_tracking(successful_interactions)

        return successful_interactions
