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
            path: Dotted path like "bar.energy" or "vfs.is_night", or bare variable name like "intensity"

        Returns:
            Tensor value from context

        Raises:
            KeyError: If path not found
        """
        parts = path.split(".")
        if parts[0] == "bar" and len(parts) == 2:
            return self.bars[parts[1]]
        elif parts[0] == "vfs" and len(parts) >= 2:
            # Support reference paths like vfs.ref.foo or nested vfs.ref.ref.bar
            if parts[1] == "ref":
                target_parts = parts[2:]
                while target_parts and target_parts[0] == "ref":
                    target_parts = target_parts[1:]
                key = ".".join(target_parts)
                return self.vfs[key]
            return self.vfs[".".join(parts[1:])]
        elif parts[0] == "temporal" and len(parts) == 2:
            return self.temporal[parts[1]]
        elif len(parts) == 1:
            # Plain variable name - check vfs first
            if path in self.vfs:
                return self.vfs[path]
            raise KeyError(f"Variable '{path}' not found in VFS context")
        else:
            raise KeyError(f"Path '{path}' not found in execution context")
