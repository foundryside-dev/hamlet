"""Affordance metadata DTOs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AffordanceInfo:
    """Metadata for a single affordance."""

    id: str
    name: str
    enabled: bool
    cost: float
    category: str | None = None
    description: str = ""
    position: tuple[float, ...] | dict[str, float] | float | None = None

    def __post_init__(self) -> None:
        if isinstance(self.position, Sequence) and not isinstance(self.position, str | bytes | tuple):
            object.__setattr__(self, "position", tuple(self.position))


@dataclass(frozen=True)
class AffordanceMetadata:
    """Collection of affordance metadata."""

    affordances: tuple[AffordanceInfo, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "affordances", tuple(self.affordances))

    def get_affordance_by_name(self, name: str) -> AffordanceInfo:
        """Lookup affordance by display name."""
        for affordance in self.affordances:
            if affordance.name == name:
                return affordance
        raise KeyError(f"Affordance '{name}' not found")
