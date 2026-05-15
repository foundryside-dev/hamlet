"""Targeted unit tests for MeterDynamics."""

from __future__ import annotations

import torch

from townlet.environment.meter_dynamics import MeterDynamics


def make_meter_dynamics(device: torch.device = torch.device("cpu")) -> MeterDynamics:
    terminal_conditions = [
        {"meter_idx": 1, "operator": "<=", "value": 0.1},
    ]

    meter_lookup = {"energy": 0, "health": 1}
    return MeterDynamics(
        terminal_conditions=terminal_conditions,
        meter_name_to_index=meter_lookup,
        device=device,
    )


class TestMeterDynamics:
    def test_terminal_condition_detects_death(self):
        md = make_meter_dynamics()
        meters = torch.tensor([[0.3, 0.05], [0.3, 0.5]], dtype=torch.float32)
        dones = torch.zeros(2, dtype=torch.bool)

        mask = md.check_terminal_conditions(meters, dones)
        assert torch.equal(mask, torch.tensor([True, False]))
