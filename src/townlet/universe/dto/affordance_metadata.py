"""Affordance metadata DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AffordanceInfo:
    """Metadata for a single affordance: its identity in declaration order."""

    id: str
    name: str


@dataclass(frozen=True)
class AffordanceMetadata:
    """Collection of affordance metadata."""

    affordances: tuple[AffordanceInfo, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "affordances", tuple(self.affordances))

    def get_affordance_by_name(self, name: str) -> AffordanceInfo:
        """Lookup affordance by display name."""
        for affordance in self.affordances:
            if affordance.name == name:
                return affordance
        raise KeyError(f"Affordance '{name}' not found")
