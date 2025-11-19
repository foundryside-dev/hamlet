"""Execution context for expression evaluation."""

from dataclasses import dataclass
from typing import Any

import torch


@dataclass
class ExecutionContext:
    """Runtime context for expression evaluation.

    Provides access to simulation state:
    - bars: Meter values (energy, health, etc.)
    - vfs: Variable & Feature System state
    - affordances: Affordance positions/states
    - temporal: Time-based values (tick count, day/night)
    """

    bars: dict[str, torch.Tensor]  # e.g., {"energy": tensor([batch])}
    vfs: dict[str, torch.Tensor]
    affordances: dict[str, Any]  # Affordance state
    temporal: dict[str, torch.Tensor]  # Time values
    device: torch.device = torch.device("cpu")

    def get(self, path: str) -> torch.Tensor:
        """Resolve dotted path to tensor value.

        Args:
            path: Dotted path like "bar.energy" or "vfs.is_night"

        Returns:
            Tensor value from context

        Raises:
            KeyError: If path not found
        """
        parts = path.split(".")
        if parts[0] == "bar" and len(parts) == 2:
            return self.bars[parts[1]]
        elif parts[0] == "vfs" and len(parts) >= 2:
            return self.vfs[".".join(parts[1:])]
        elif parts[0] == "temporal" and len(parts) == 2:
            return self.temporal[parts[1]]
        else:
            raise KeyError(f"Path '{path}' not found in execution context")
