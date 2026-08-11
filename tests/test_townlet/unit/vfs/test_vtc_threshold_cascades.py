"""Tests for threshold cascades compiled as VTC transition rules."""

from __future__ import annotations

import torch

from townlet.config.bars_v2_config import CascadeParamConfig
from townlet.vfs.vtc import compile_vtc_threshold_cascades

# A cascade writes its TARGET meter, so the compiler needs the target's declared
# bounds to emit the rule's clamp (WS-1(e)). These fixtures are unit-interval.
_METERS = [
    {"name": name, "depletion": {"passive": 0.0}, "bounds": {"min": 0.0, "max": 1.0}} for name in ("energy", "mood", "satiation", "hygiene")
]


def _cascade(*, source: str, target: str, threshold: float, strength: float) -> CascadeParamConfig:
    return CascadeParamConfig(source=source, target=target, threshold=threshold, strength=strength)


def test_compile_vtc_threshold_cascades_emits_threshold_delta_rule_metadata() -> None:
    program = compile_vtc_threshold_cascades(
        [
            _cascade(source="satiation", target="energy", threshold=0.3, strength=0.006),
        ],
        _METERS,
    )

    assert len(program.rules) == 1
    rule = program.rules[0]
    assert rule.rule_id == "satiation->energy"
    assert rule.kind == "threshold_delta"
    assert rule.variable_id == "energy"
    assert rule.condition == "bar.satiation < 0.3"
    assert rule.expression == "-0.006 * ((0.3 - bar.satiation) / 0.3)"
    assert rule.composition == "additive_delta"
    assert rule.phase == "apply_threshold_cascades"
    assert rule.clamp == (0.0, 1.0)


def test_vtc_threshold_cascades_sum_target_penalties_from_phase_snapshot() -> None:
    program = compile_vtc_threshold_cascades(
        [
            _cascade(source="satiation", target="energy", threshold=0.3, strength=0.006),
            _cascade(source="mood", target="energy", threshold=0.2, strength=0.001),
            _cascade(source="hygiene", target="mood", threshold=0.4, strength=0.003),
        ],
        _METERS,
    )

    updated = program.apply(
        bars_state={
            "energy": torch.tensor([1.0, 1.0, 1.0]),
            "satiation": torch.tensor([0.15, 0.5, 0.15]),
            "mood": torch.tensor([0.1, 0.1, 0.1]),
            "hygiene": torch.tensor([0.0, 0.0, 0.0]),
        },
        active_mask=torch.tensor([True, True, False]),
        device=torch.device("cpu"),
    )

    expected_energy = torch.tensor(
        [
            1.0 - (0.006 * ((0.3 - 0.15) / 0.3)) - (0.001 * ((0.2 - 0.1) / 0.2)),
            1.0 - (0.001 * ((0.2 - 0.1) / 0.2)),
            1.0,
        ]
    )
    expected_mood = torch.tensor([1.0e-1 - (0.003 * ((0.4 - 0.0) / 0.4)), 1.0e-1 - 0.003, 0.1])

    assert torch.allclose(updated["energy"], expected_energy, atol=1e-7)
    assert torch.allclose(updated["mood"], expected_mood, atol=1e-7)
