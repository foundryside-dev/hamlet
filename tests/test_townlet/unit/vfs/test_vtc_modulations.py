"""Tests for VTC affordance modulation rules."""

import pytest
import torch

from townlet.config.affordances_v2_config import ModulationParamConfig
from townlet.vfs import vtc


def test_compile_vtc_modulations_emits_modulation_rule_metadata() -> None:
    """Affordance modulation parameters should compile into VTC rule records."""
    assert hasattr(vtc, "compile_vtc_modulations"), "VTC modulation compiler is required"

    program = vtc.compile_vtc_modulations(
        [
            ModulationParamConfig(
                bar="energy",
                affordances=["WORK"],
                type="linear_multiplier",
                threshold=0.3,
                min_multiplier=0.5,
            )
        ]
    )

    assert len(program.rules) == 1
    rule = program.rules[0]
    assert rule.rule_id == "energy->WORK"
    assert rule.kind == "modulation"
    assert rule.source_variable_id == "energy"
    assert rule.target_affordance_id == "WORK"
    assert rule.variable_id == "affordance.WORK.multiplier"
    assert rule.expression == "where(bar.energy < 0.3, 0.5 + (1.0 - 0.5) * (bar.energy / 0.3), 1.0)"
    assert rule.condition is None
    assert rule.composition == "multiplicative_modifier"
    assert rule.phase == "apply_modulations"
    assert rule.clamp == (0.0, 1.0)
    assert rule.telemetry_label == "modulation:energy->WORK"


def test_vtc_modulations_multiply_matching_affordance_factors_and_mask_inactive() -> None:
    """Matching modulation rules should multiply and inactive agents should receive zero multiplier."""
    assert hasattr(vtc, "compile_vtc_modulations"), "VTC modulation compiler is required"

    program = vtc.compile_vtc_modulations(
        [
            ModulationParamConfig(
                bar="energy",
                affordances=["WORK"],
                type="linear_multiplier",
                threshold=0.3,
                min_multiplier=0.5,
            ),
            ModulationParamConfig(
                bar="mood",
                affordances=["WORK", "SOCIALIZE"],
                type="linear_multiplier",
                threshold=0.4,
                min_multiplier=0.7,
            ),
        ]
    )
    bars_state = {
        "energy": torch.tensor([0.15, 0.6, 0.15], dtype=torch.float32),
        "mood": torch.tensor([0.2, 0.2, 0.2], dtype=torch.float32),
    }
    active_mask = torch.tensor([True, True, False])

    work_multiplier = program.compute_affordance_multiplier(
        "WORK",
        bars_state,
        active_mask=active_mask,
        device=torch.device("cpu"),
    )
    socialize_multiplier = program.compute_affordance_multiplier(
        "SOCIALIZE",
        bars_state,
        active_mask=active_mask,
        device=torch.device("cpu"),
    )

    assert work_multiplier.tolist() == pytest.approx([0.75 * 0.85, 0.85, 0.0])
    assert socialize_multiplier.tolist() == pytest.approx([0.85, 0.85, 0.0])
