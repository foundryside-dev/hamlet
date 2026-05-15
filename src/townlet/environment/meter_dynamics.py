"""Tensor-driven meter dynamics used by the runtime environment."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict, cast

import torch


class _ModulationEntry(TypedDict):
    source_idx: int
    target_idx: int
    base_multiplier: float
    range: float
    baseline_depletion: float


class _TerminalCondition(TypedDict):
    meter_idx: int
    operator: str
    value: float


class MeterDynamics:
    """Apply depletion, modulations, and terminal checks from tensors."""

    def __init__(
        self,
        *,
        base_depletions: torch.Tensor,
        modulation_data: Sequence[Mapping[str, Any]],
        terminal_conditions: Sequence[Mapping[str, Any]],
        meter_name_to_index: Mapping[str, int],
        device: torch.device,
    ) -> None:
        """Initialize meter dynamics with compiler-provided tensors."""

        self.device = device
        self.base_depletions = base_depletions.to(device=device, dtype=torch.float32).clone()
        self.meter_name_to_index = dict(meter_name_to_index)

        self._modulations: list[_ModulationEntry] = []
        for entry in modulation_data:
            self._modulations.append(
                cast(
                    _ModulationEntry,
                    {
                        "source_idx": int(entry["source_idx"]),
                        "target_idx": int(entry["target_idx"]),
                        "base_multiplier": float(entry["base_multiplier"]),
                        "range": float(entry["range"]),
                        "baseline_depletion": float(entry["baseline_depletion"]),
                    },
                )
            )

        self._terminal_conditions: list[_TerminalCondition] = []
        for entry in terminal_conditions:
            self._terminal_conditions.append(
                cast(
                    _TerminalCondition,
                    {
                        "meter_idx": int(entry["meter_idx"]),
                        "operator": entry["operator"],
                        "value": float(entry["value"]),
                    },
                )
            )

    def deplete_meters(self, meters: torch.Tensor, depletion_multiplier: float = 1.0) -> torch.Tensor:
        """Apply base depletion and modulations using precomputed tensors."""

        scaled_depletions = self.base_depletions * depletion_multiplier
        meters = torch.clamp(meters - scaled_depletions, 0.0, 1.0)

        for modulation in self._modulations:
            source_values = meters[:, modulation["source_idx"]]
            target_idx = modulation["target_idx"]
            penalty_strength = 1.0 - source_values
            multiplier = modulation["base_multiplier"] + (modulation["range"] * penalty_strength)
            depletion = modulation["baseline_depletion"] * multiplier
            meters[:, target_idx] = torch.clamp(meters[:, target_idx] - depletion, 0.0, 1.0)

        return meters

    def check_terminal_conditions(self, meters: torch.Tensor, dones: torch.Tensor) -> torch.Tensor:
        """Evaluate terminal conditions using compiler-provided thresholds.

        Preserves monotonic property: once done, stays done until reset.
        """

        terminal_mask = torch.zeros_like(dones, dtype=torch.bool)

        for condition in self._terminal_conditions:
            meter_values = meters[:, condition["meter_idx"]]
            threshold = condition["value"]
            operator = condition["operator"]

            if operator == "<=":
                current = meter_values <= threshold
            elif operator == ">=":
                current = meter_values >= threshold
            elif operator == "<":
                current = meter_values < threshold
            elif operator == ">":
                current = meter_values > threshold
            elif operator == "==":
                current = torch.isclose(meter_values, torch.tensor(threshold, device=meter_values.device))
            else:  # pragma: no cover - defensive
                raise ValueError(f"Unknown terminal condition operator: {operator}")

            terminal_mask |= current

        # Preserve previous done states (monotonic property)
        return terminal_mask | dones

    def get_base_depletion(self, meter_name: str) -> float:
        """Expose base depletion for configuration tests."""

        idx = self.meter_name_to_index.get(meter_name)
        if idx is None:
            raise KeyError(f"Meter '{meter_name}' not found in lookup.")
        return float(self.base_depletions[idx].item())
