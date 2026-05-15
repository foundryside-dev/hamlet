"""Tensor-driven terminal checks used by the runtime environment."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict, cast

import torch


class _TerminalCondition(TypedDict):
    meter_idx: int
    operator: str
    value: float


class MeterDynamics:
    """Evaluate terminal checks from compiler-provided tensors."""

    def __init__(
        self,
        *,
        terminal_conditions: Sequence[Mapping[str, Any]],
        meter_name_to_index: Mapping[str, int],
        device: torch.device,
    ) -> None:
        """Initialize meter dynamics with compiler-provided tensors."""

        self.device = device
        self.meter_name_to_index = dict(meter_name_to_index)

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
