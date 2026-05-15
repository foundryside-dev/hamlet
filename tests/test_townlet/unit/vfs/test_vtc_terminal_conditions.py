"""Tests for terminal conditions compiled as VTC transition rules."""

from __future__ import annotations

import torch

from townlet.vfs import vtc


def _meter(
    name: str,
    *,
    min_value: float,
    max_value: float,
    lethal_min: bool,
    lethal_max: bool,
) -> dict[str, object]:
    return {
        "name": name,
        "bounds": {
            "min": min_value,
            "max": max_value,
            "lethal_min": lethal_min,
            "lethal_max": lethal_max,
        },
    }


def test_compile_vtc_terminal_conditions_emits_rule_metadata() -> None:
    """Lethal meter bounds should compile into explicit VTC terminal-condition rules."""
    assert hasattr(vtc, "compile_vtc_terminal_conditions"), "VTC terminal-condition compiler is required"

    program = vtc.compile_vtc_terminal_conditions(
        [
            _meter("energy", min_value=0.0, max_value=1.0, lethal_min=True, lethal_max=False),
            _meter("stress", min_value=0.0, max_value=1.0, lethal_min=False, lethal_max=True),
            _meter("mood", min_value=0.0, max_value=1.0, lethal_min=False, lethal_max=False),
        ]
    )

    assert len(program.rules) == 2

    energy_rule = program.rules[0]
    assert energy_rule.rule_id == "terminal:energy:min"
    assert energy_rule.kind == "terminal_condition"
    assert energy_rule.source_variable_id == "energy"
    assert energy_rule.variable_id == "done"
    assert energy_rule.expression == "bar.energy <= 0.0"
    assert energy_rule.condition is None
    assert energy_rule.composition == "event"
    assert energy_rule.phase == "evaluate_terminal_conditions"
    assert energy_rule.clamp is None
    assert energy_rule.telemetry_label == "terminal_condition:energy:min"
    assert energy_rule.operator == "<="
    assert energy_rule.threshold == 0.0

    stress_rule = program.rules[1]
    assert stress_rule.rule_id == "terminal:stress:max"
    assert stress_rule.source_variable_id == "stress"
    assert stress_rule.expression == "bar.stress >= 1.0"
    assert stress_rule.telemetry_label == "terminal_condition:stress:max"
    assert stress_rule.operator == ">="
    assert stress_rule.threshold == 1.0


def test_vtc_terminal_conditions_preserve_existing_dones_and_mask_inactive_agents() -> None:
    """VTC terminal evaluation should OR new triggers into existing done state for active agents only."""
    program = vtc.compile_vtc_terminal_conditions(
        [
            _meter("energy", min_value=0.0, max_value=1.0, lethal_min=True, lethal_max=False),
            _meter("stress", min_value=0.0, max_value=1.0, lethal_min=False, lethal_max=True),
        ]
    )

    updated = program.apply(
        bars_state={
            "energy": torch.tensor([0.0, 0.5, 0.0, 0.5], dtype=torch.float32),
            "stress": torch.tensor([0.2, 0.4, 0.5, 1.0], dtype=torch.float32),
        },
        dones=torch.tensor([False, True, False, False]),
        active_mask=torch.tensor([True, True, False, True]),
        device=torch.device("cpu"),
    )

    assert torch.equal(updated, torch.tensor([True, True, False, True]))
