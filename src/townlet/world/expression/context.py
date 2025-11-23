"""Execution context for expression evaluation."""

from dataclasses import dataclass
from typing import Any

import torch

from townlet.world.expression.history import TemporalHistory


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
    affordance_positions: dict[str, torch.Tensor] | None = None
    agent_positions: torch.Tensor | None = None
    device: torch.device = torch.device("cpu")
    history: TemporalHistory | None = None
    step: int | None = None

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
        if parts[0] == "temporal" and len(parts) == 2:
            return self.temporal[parts[1]]
        if parts[0] == "vfs":
            tail = parts[1:]
            # Normalize ref hops: drop explicit ref tokens
            tail = [p for p in tail if p != "ref"]
            # If tail looks like <ref>.bar.<name> or <ref>.vfs.<name>, drop the ref name
            if len(tail) >= 2 and tail[1] in {"bar", "vfs"}:
                tail = tail[1:]
            if not tail:
                raise KeyError(f"Path '{path}' not found in execution context")
            if tail[0] == "bar":
                if len(tail) < 2:
                    raise KeyError(f"Path '{path}' not found in execution context")
                return self.bars[tail[1]]
            key = ".".join(tail if tail[0] != "vfs" else tail[1:])
            if key in self.vfs:
                return self.vfs[key]
        if parts[0] in {"target", "self"}:
            # Normalize target/self.vfs.* or target/self.bar.*
            tail = parts[1:]
            if not tail:
                raise KeyError(f"Path '{path}' not found in execution context")
            if tail[0] == "bar":
                if len(tail) < 2:
                    raise KeyError(f"Path '{path}' not found in execution context")
                return self.bars[tail[1]]
            key = ".".join(tail[1:] if tail[0] == "vfs" else tail)
            if key in self.vfs:
                return self.vfs[key]
        if len(parts) == 1 and path in self.vfs:
            return self.vfs[path]
        raise KeyError(f"Path '{path}' not found in execution context")
