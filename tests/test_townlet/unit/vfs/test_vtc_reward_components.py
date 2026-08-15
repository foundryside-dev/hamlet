"""Tests for reward components compiled as VTC transition rules."""

from __future__ import annotations

import pytest
import torch

from townlet.config.drive_as_code import (
    BarBonusConfig,
    DriveAsCodeConfig,
    ExtrinsicStrategyConfig,
    IntrinsicStrategyConfig,
    ModifierConfig,
    RangeConfig,
    VariableBonusConfig,
    VFSVariableBonusConfig,
)
from townlet.vfs import vtc


def _reward_config(*, variable_weight: float = 0.5) -> DriveAsCodeConfig:
    return DriveAsCodeConfig(
        version="1.0",
        modifiers={
            "energy_crisis": ModifierConfig(
                bar="energy",
                ranges=[
                    RangeConfig(name="crisis", min=0.0, max=0.3, multiplier=0.0),
                    RangeConfig(name="normal", min=0.3, max=1.0, multiplier=1.0),
                ],
            )
        },
        extrinsic=ExtrinsicStrategyConfig(
            type="constant_base_with_shaped_bonus",
            base_reward=1.0,
            bar_bonuses=[BarBonusConfig(bar="energy", center=0.5, scale=0.25)],
            variable_bonuses=[VariableBonusConfig(variable="energy_deficit", weight=variable_weight)],
            apply_modifiers=["energy_crisis"],
        ),
        intrinsic=IntrinsicStrategyConfig(strategy="rnd", base_weight=0.2, apply_modifiers=["energy_crisis"]),
        shaping=[VFSVariableBonusConfig(type="vfs_variable", variable="vtc_completion_signal", weight=2.0)],
    )


def test_compile_vtc_reward_components_declares_dac_vtc_boundary() -> None:
    """DAC reward sources should compile into explicit VTC compute-reward rules."""
    assert hasattr(vtc, "compile_vtc_reward_components"), "VTC reward-component compiler is required"

    program = vtc.compile_vtc_reward_components(_reward_config())

    assert [rule.rule_id for rule in program.rules] == [
        "reward:modifier:energy_crisis",
        "reward:extrinsic:constant_base_with_shaped_bonus",
        "reward:intrinsic:rnd",
        "reward:shaping:0:vfs_variable",
        "reward:total",
    ]

    modifier_rule = program.rules[0]
    assert modifier_rule.kind == "reward_modifier"
    assert modifier_rule.phase == "compute_rewards"
    assert modifier_rule.variable_id == "reward.modifier.energy_crisis"
    assert modifier_rule.reads == ("bar.energy",)
    assert modifier_rule.component == "modifier"
    assert modifier_rule.source_kind == "bar"
    assert modifier_rule.parameters["ranges"][0]["multiplier"] == 0.0

    extrinsic_rule = program.rules[1]
    assert extrinsic_rule.kind == "reward_component"
    assert extrinsic_rule.component == "extrinsic"
    assert extrinsic_rule.variable_id == "reward.extrinsic"
    assert extrinsic_rule.reads == ("bar.energy", "vfs.energy_deficit", "reward.modifier.energy_crisis")
    assert extrinsic_rule.parameters["variable_bonuses"][0]["weight"] == 0.5

    intrinsic_rule = program.rules[2]
    assert intrinsic_rule.component == "intrinsic"
    assert intrinsic_rule.reads == ("intrinsic_raw", "reward.modifier.energy_crisis")

    shaping_rule = program.rules[3]
    assert shaping_rule.component == "shaping"
    assert shaping_rule.reads == ("vfs.vtc_completion_signal",)
    assert shaping_rule.parameters["weight"] == 2.0

    total_rule = program.rules[4]
    assert total_rule.component == "total"
    assert total_rule.reads == ("reward.extrinsic", "reward.intrinsic", "reward.shaping")
    assert program.expected_components == ("extrinsic", "intrinsic", "intrinsic_raw", "shaping")


def test_vtc_reward_program_applies_dac_backend_and_validates_component_contract() -> None:
    """The VTC reward program should own reward-phase invocation and component shape validation."""
    program = vtc.compile_vtc_reward_components(_reward_config())
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
    program = vtc.compile_vtc_reward_components(_reward_config())
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
