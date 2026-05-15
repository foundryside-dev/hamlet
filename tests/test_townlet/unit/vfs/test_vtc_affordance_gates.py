"""Tests for operating-hour gates compiled as VTC transition rules."""

from __future__ import annotations

import torch

from townlet.vfs import vtc


def _affordance(name: str, *, enabled: bool, windows: list[tuple[int, int]]) -> dict[str, object]:
    return {
        "name": name,
        "opening_hours": {
            "enabled": enabled,
            "schedule": [{"start": start, "end": end} for start, end in windows],
        },
    }


def test_compile_vtc_affordance_gates_emits_action_legality_rule_metadata() -> None:
    program = vtc.compile_vtc_affordance_gates([_affordance("Job", enabled=True, windows=[(9, 18)])])

    assert len(program.rules) == 1
    rule = program.rules[0]
    assert rule.rule_id == "job_open_window"
    assert rule.kind == "affordance_gate"
    assert rule.source_variable_id == "time_of_day"
    assert rule.target_affordance_id == "Job"
    assert rule.variable_id == "affordance.Job.available"
    assert rule.expression == "time_in_window(temporal.time_of_day, 9.0, 18.0)"
    assert rule.condition is None
    assert rule.composition == "overwrite"
    assert rule.phase == "compute_action_legality_masks"
    assert rule.clamp is None
    assert rule.telemetry_label == "affordance_gate:Job"


def test_vtc_affordance_gates_evaluate_normal_wraparound_and_24_hour_windows() -> None:
    program = vtc.compile_vtc_affordance_gates(
        [
            _affordance("Job", enabled=True, windows=[(9, 18)]),
            _affordance("Bar", enabled=True, windows=[(18, 28)]),
            _affordance("Bed", enabled=False, windows=[]),
        ]
    )

    assert program.is_affordance_open("Job", time_of_day=10, device=torch.device("cpu")) is True
    assert program.is_affordance_open("Job", time_of_day=19, device=torch.device("cpu")) is False
    assert program.is_affordance_open("Bar", time_of_day=20, device=torch.device("cpu")) is True
    assert program.is_affordance_open("Bar", time_of_day=2, device=torch.device("cpu")) is True
    assert program.is_affordance_open("Bar", time_of_day=5, device=torch.device("cpu")) is False
    assert program.is_affordance_open("Bed", time_of_day=0, device=torch.device("cpu")) is True
    assert program.is_affordance_open("Bed", time_of_day=23, device=torch.device("cpu")) is True
