"""Tests for reward calculation delegation."""

from __future__ import annotations

import torch

from townlet.environment.reward_calculator import RewardCalculator


def test_reward_calculator_routes_reward_phase_through_vtc_program() -> None:
    """RewardCalculator should invoke DAC only through the compiled VTC reward program."""
    device = torch.device("cpu")

    class DACBackend:
        def calculate_rewards(self, **kwargs: object) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
            raise AssertionError("DAC must be invoked through VTC reward program")

    class VTCRewardProgram:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        def apply(self, **kwargs: object) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
            self.kwargs = kwargs
            return (
                torch.tensor([2.0, 0.0], device=device),
                torch.tensor([1.0, 0.0], device=device),
                {
                    "extrinsic": torch.tensor([1.5, 0.0], device=device),
                    "intrinsic": torch.tensor([0.3, 0.0], device=device),
                    "intrinsic_raw": torch.tensor([0.3, 0.4], device=device),
                    "shaping": torch.tensor([0.2, 0.0], device=device),
                },
            )

    class Env:
        def __init__(self) -> None:
            self.device = device
            self.num_agents = 2
            self.exploration_module = None
            self.positions = torch.zeros((2, 2), device=device)
            self.step_counts = torch.tensor([1, 2], device=device)
            self.dones = torch.tensor([False, True], device=device)
            self.meters = torch.tensor([[0.8], [0.2]], device=device)
            self.time_of_day = torch.tensor([12, 12], device=device)
            self.enable_temporal_mechanics = True
            self.intrinsic_weights: torch.Tensor | None = None
            self._last_reward_components: dict[str, torch.Tensor] = {}
            self.dac_engine = DACBackend()
            self.vtc_reward_program = VTCRewardProgram()

        def _get_observations(self) -> torch.Tensor:
            raise AssertionError("observations are only needed for exploration rewards")

        def _get_affordance_positions(self) -> dict[str, torch.Tensor]:
            return {}

        def _get_last_action_affordances(self) -> list[str | None]:
            return [None, None]

        def _get_affordance_streaks(self) -> dict[str, torch.Tensor]:
            return {}

        def _get_unique_affordances_used(self) -> torch.Tensor:
            return torch.zeros(2, device=device)

    env = Env()

    rewards = RewardCalculator(env)._calculate_shaped_rewards()  # type: ignore[arg-type]

    assert torch.equal(rewards, torch.tensor([2.0, 0.0], device=device))
    assert env.vtc_reward_program.kwargs is not None
    assert env.vtc_reward_program.kwargs["reward_backend"] is env.dac_engine
    assert env.vtc_reward_program.kwargs["step_counts"] is env.step_counts
    assert env.vtc_reward_program.kwargs["dones"] is env.dones
    assert env.vtc_reward_program.kwargs["meters"] is env.meters
    assert torch.equal(env.vtc_reward_program.kwargs["intrinsic_raw"], torch.zeros(2, device=device))
    reward_context = env.vtc_reward_program.kwargs["reward_context"]
    assert isinstance(reward_context, dict)
    assert reward_context["current_hour"] is env.time_of_day
    assert env.intrinsic_weights is not None
    assert torch.equal(env.intrinsic_weights, torch.tensor([1.0, 0.0], device=device))
    assert set(env._last_reward_components) == {"extrinsic", "intrinsic", "intrinsic_raw", "shaping"}
