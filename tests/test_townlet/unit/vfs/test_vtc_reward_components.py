"""The DAC reward-output contract: ``VTCRewardProgram`` validates what the backend returns.

Rewards are DAC's. There is no reward transition phase and no compiled reward rule;
the program only calls the backend and refuses mis-shaped outputs.
"""

from __future__ import annotations

import pytest
import torch

from townlet.vfs import vtc


def test_vtc_reward_program_carries_no_compiled_rules() -> None:
    program = vtc.VTCRewardProgram()
    assert not hasattr(program, "rules")
    assert program.expected_components == ("extrinsic", "intrinsic", "intrinsic_raw", "shaping")


def test_vtc_reward_program_applies_dac_backend_and_validates_component_contract() -> None:
    """The VTC reward program should own reward-phase invocation and component shape validation."""
    program = vtc.VTCRewardProgram()
    device = torch.device("cpu")
    step_counts = torch.tensor([1, 2], device=device)
    dones = torch.tensor([False, True], device=device)
    meters = torch.tensor([[0.8], [0.2]], device=device)
    intrinsic_raw = torch.tensor([0.3, 0.4], device=device)

    class Backend:
        def __init__(self) -> None:
            self.kwargs: dict[str, object] | None = None

        def calculate_rewards(self, **kwargs: object) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
            self.kwargs = kwargs
            return (
                torch.tensor([1.5, 0.0], device=device),
                torch.tensor([1.0, 0.0], device=device),
                {
                    "extrinsic": torch.tensor([1.0, 0.0], device=device),
                    "intrinsic": torch.tensor([0.3, 0.0], device=device),
                    "intrinsic_raw": torch.tensor([0.3, 0.4], device=device),
                    "shaping": torch.tensor([0.2, 0.0], device=device),
                },
            )

    backend = Backend()

    total, intrinsic_weight, components = program.apply(
        reward_backend=backend,
        step_counts=step_counts,
        dones=dones,
        meters=meters,
        intrinsic_raw=intrinsic_raw,
        reward_context={"current_hour": torch.tensor([12, 12], device=device)},
    )

    assert backend.kwargs is not None
    assert backend.kwargs["step_counts"] is step_counts
    assert backend.kwargs["dones"] is dones
    assert backend.kwargs["meters"] is meters
    assert backend.kwargs["intrinsic_raw"] is intrinsic_raw
    assert torch.equal(total, torch.tensor([1.5, 0.0], device=device))
    assert torch.equal(intrinsic_weight, torch.tensor([1.0, 0.0], device=device))
    assert set(components) == {"extrinsic", "intrinsic", "intrinsic_raw", "shaping"}


def test_vtc_reward_program_rejects_missing_declared_component() -> None:
    """Reward backends must return every component declared by the VTC reward contract."""
    program = vtc.VTCRewardProgram()
    device = torch.device("cpu")

    class Backend:
        def calculate_rewards(self, **kwargs: object) -> tuple[torch.Tensor, torch.Tensor, dict[str, torch.Tensor]]:
            return (
                torch.ones(2, device=device),
                torch.ones(2, device=device),
                {
                    "extrinsic": torch.ones(2, device=device),
                    "intrinsic": torch.ones(2, device=device),
                    "shaping": torch.ones(2, device=device),
                },
            )

    with pytest.raises(KeyError, match="missing declared reward components"):
        program.apply(
            reward_backend=Backend(),
            step_counts=torch.ones(2, dtype=torch.long, device=device),
            dones=torch.zeros(2, dtype=torch.bool, device=device),
            meters=torch.ones((2, 1), device=device),
            intrinsic_raw=torch.ones(2, device=device),
            reward_context={},
        )
