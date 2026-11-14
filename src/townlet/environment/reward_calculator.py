"""Reward calculation facade for :class:`VectorizedHamletEnv`."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.config.exploration_policy import IntrinsicTransitionContext
    from townlet.config.world_roster import WorldAcceptedEpisode
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    from townlet.exploration.world_curiosity_state import CuriosityStepStamp


class RewardCalculator:
    """Calculate shaped rewards through DACEngine."""

    def __init__(self, env: VectorizedHamletEnv) -> None:
        self._env = env

    def _calculate_shaped_rewards(
        self,
        *,
        active_on_entry: torch.Tensor,
        intrinsic_context: IntrinsicTransitionContext,
        intrinsic_stamp: CuriosityStepStamp,
        accepted: WorldAcceptedEpisode,
    ) -> torch.Tensor:
        """Calculate total rewards using DACEngine."""
        env = self._env
        intrinsic_reward = env._exploration_runtime.reward(
            context=intrinsic_context,
            stamp=intrinsic_stamp,
            accepted=accepted,
            update_stats=True,
        )
        return self._apply_shaped_rewards(intrinsic_raw=intrinsic_reward.raw, runtime_intrinsic_scale=intrinsic_reward.scales)

    def _calculate_manual_rewards(self) -> torch.Tensor:
        env = self._env
        zero = torch.zeros(env.num_agents, dtype=env.meters.dtype, device=env.device)
        return self._apply_shaped_rewards(intrinsic_raw=zero, runtime_intrinsic_scale=zero.clone())

    def _apply_shaped_rewards(self, *, intrinsic_raw: torch.Tensor, runtime_intrinsic_scale: torch.Tensor) -> torch.Tensor:
        env = self._env
        agent_positions = env.positions.to(device=env.device, dtype=torch.float32)

        kwargs = {
            "agent_positions": agent_positions,
            "affordance_positions": env._get_affordance_positions(),
            "last_action_affordance": env._get_last_action_affordances(),
            "affordance_streak": env._get_affordance_streaks(),
            "unique_affordances_used": env._get_unique_affordances_used(),
        }

        if env.enable_temporal_mechanics:
            # The hour the step's action was taken at (instant k): step() flips
            # time_of_day to the next action's hour only after rewards. DAC terms
            # are tensor programs, so the hour crosses this boundary as a tensor.
            kwargs["current_hour"] = torch.tensor(env.time_of_day, device=env.device)

        total_rewards, intrinsic_weights, components = env.vtc_reward_program.apply(
            reward_backend=env.dac_engine,
            step_counts=env.step_counts,
            dones=env.dones,
            meters=env.meters,
            intrinsic_raw=intrinsic_raw,
            runtime_intrinsic_scale=runtime_intrinsic_scale,
            reward_context=kwargs,
        )

        env.intrinsic_weights = intrinsic_weights
        env._last_reward_components = components

        return total_rewards
