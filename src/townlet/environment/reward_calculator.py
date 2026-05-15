"""Reward calculation facade for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv


class RewardCalculator:
    """Calculate shaped rewards through DACEngine."""

    def __init__(self, env: VectorizedHamletEnv) -> None:
        self._env = env

    def _calculate_shaped_rewards(self) -> torch.Tensor:
        """Calculate total rewards using DACEngine."""
        env = self._env
        if env.exploration_module is not None:
            observations = env._get_observations()
            intrinsic_raw = env.exploration_module.compute_intrinsic_rewards(observations, update_stats=True)
        else:
            intrinsic_raw = torch.zeros(env.num_agents, device=env.device)

        agent_positions = env.positions.to(device=env.device, dtype=torch.float32)

        kwargs = {
            "agent_positions": agent_positions,
            "affordance_positions": env._get_affordance_positions(),
            "last_action_affordance": env._get_last_action_affordances(),
            "affordance_streak": env._get_affordance_streaks(),
            "unique_affordances_used": env._get_unique_affordances_used(),
        }

        if env.enable_temporal_mechanics:
            kwargs["current_hour"] = env.time_of_day

        total_rewards, intrinsic_weights, components = env.vtc_reward_program.apply(
            reward_backend=env.dac_engine,
            step_counts=env.step_counts,
            dones=env.dones,
            meters=env.meters,
            intrinsic_raw=intrinsic_raw,
            reward_context=kwargs,
        )

        env.intrinsic_weights = intrinsic_weights
        env._last_reward_components = components

        return total_rewards
