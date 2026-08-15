"""Tests for VTC passive depletion rules."""

import pytest
import torch

from townlet.vfs import vtc


def test_compile_vtc_passive_depletions_emits_rule_metadata() -> None:
    """Meter passive depletion should compile into explicit VTC overwrite rules."""
    assert hasattr(vtc, "compile_vtc_passive_depletions"), "VTC passive depletion compiler is required"

    program = vtc.compile_vtc_passive_depletions(
        [
            {
                "name": "energy",
                "depletion": {"passive": 0.1},
                "bounds": {"min": 0.0, "max": 1.0},
            }
        ]
    )

    assert len(program.rules) == 1
    rule = program.rules[0]
    assert rule.rule_id == "passive:energy"
    assert rule.kind == "passive_depletion"
    assert rule.source_variable_id == "energy"
    assert rule.variable_id == "energy"
    assert rule.expression == "bar.energy - (0.1 * temporal.depletion_multiplier)"
    assert rule.condition is None
    assert rule.composition == "overwrite"
    assert rule.phase == "apply_passive_depletion"
    assert rule.clamp == (0.0, 1.0)
    assert rule.telemetry_label == "passive_depletion:energy"
    assert rule.passive_rate == 0.1
    assert program.passive_rate_for("energy") == 0.1


def test_vtc_passive_depletions_apply_scaled_decay_clamp_and_masking() -> None:
    """Passive depletion should scale by curriculum difficulty, clamp, and preserve inactive agents."""
    assert hasattr(vtc, "compile_vtc_passive_depletions"), "VTC passive depletion compiler is required"

    program = vtc.compile_vtc_passive_depletions(
        [
            {"name": "energy", "depletion": {"passive": 0.1}, "bounds": {"min": 0.0, "max": 1.0}},
            {"name": "health", "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 1.0}},
        ]
    )
    bars_state = {
        "energy": torch.tensor([0.5, 0.05, 0.9], dtype=torch.float32),
        "health": torch.tensor([1.0, 0.5, 0.2], dtype=torch.float32),
    }
    active_mask = torch.tensor([True, True, False])

    updated = program.apply(
        bars_state=bars_state,
        active_mask=active_mask,
        device=torch.device("cpu"),
        depletion_multiplier=2.0,
    )

    assert updated["energy"].tolist() == pytest.approx([0.3, 0.0, 0.9])
    assert updated["health"].tolist() == pytest.approx([1.0, 0.5, 0.2])
