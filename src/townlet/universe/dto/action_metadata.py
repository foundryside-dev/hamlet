"""Action metadata DTOs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

import torch


@dataclass(frozen=True)
class ActionMetadata:
    """Metadata for a single action in the compiled universe."""

    id: int
    name: str
    type: Literal["movement", "interaction", "passive", "transaction"]
    enabled: bool
    source: Literal["substrate", "custom", "affordance", "item"]
    costs: Mapping[str, float] = field(default_factory=dict)
    description: str = ""
    movement_delta: tuple[float, ...] | None = None
    source_affordance: str | None = None
    writes: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "costs", MappingProxyType(dict(self.costs)))
        if self.movement_delta is not None:
            object.__setattr__(self, "movement_delta", tuple(self.movement_delta))
        object.__setattr__(self, "writes", tuple(dict(write) for write in self.writes))


@dataclass(frozen=True)
class ActionSpaceMetadata:
    """Rich metadata describing the action space."""

    total_actions: int
    actions: tuple[ActionMetadata, ...] = field(default_factory=tuple)
    labels: Mapping[int, str] = field(default_factory=dict)
    label_description: str | None = None
    label_domain: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "actions", tuple(self.actions))
        object.__setattr__(self, "labels", MappingProxyType(dict(self.labels)))
        if self.total_actions < 0:
            raise ValueError("total_actions must be >= 0")

    def get_enabled_actions(self) -> list[ActionMetadata]:
        """Return the subset of enabled actions."""
        return [action for action in self.actions if action.enabled]

    def get_action_mask(self, num_agents: int, device: torch.device) -> torch.Tensor:
        """Return a [num_agents, total_actions] bool mask with disabled actions masked out."""
        if num_agents <= 0:
            raise ValueError("num_agents must be positive")

        mask = torch.ones(num_agents, self.total_actions, dtype=torch.bool, device=device)
        for action in self.actions:
            if action.id >= self.total_actions:
                raise ValueError(f"Action '{action.name}' has id {action.id} which exceeds total_actions={self.total_actions}")
            if not action.enabled:
                mask[:, action.id] = False
        return mask


@dataclass(frozen=True)
class RuntimeAction:
    """Runtime-ready action definition emitted by the compiler."""

    id: int
    name: str
    type: Literal["movement", "interaction", "passive", "transaction"]
    enabled: bool
    source: Literal["substrate", "custom", "affordance", "item"]
    costs: Mapping[str, float] = field(default_factory=dict)
    effects: Mapping[str, float] = field(default_factory=dict)
    delta: tuple[int | float, ...] | None = None
    teleport_to: tuple[int, ...] | None = None
    description: str | None = None
    icon: str | None = None
    source_affordance: str | None = None
    reads: tuple[str, ...] = field(default_factory=tuple)
    writes: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "costs", MappingProxyType(dict(self.costs)))
        object.__setattr__(self, "effects", MappingProxyType(dict(self.effects)))
        object.__setattr__(self, "reads", tuple(self.reads))
        object.__setattr__(self, "writes", tuple(dict(write) for write in self.writes))
        if self.delta is not None:
            object.__setattr__(self, "delta", tuple(self.delta))
        if self.teleport_to is not None:
            object.__setattr__(self, "teleport_to", tuple(self.teleport_to))


@dataclass(frozen=True)
class RuntimeActionSpace:
    """Runtime-ready action-space definition emitted by the compiler."""

    actions: tuple[RuntimeAction, ...]
    substrate_action_count: int
    custom_action_count: int
    affordance_action_count: int
    enabled_action_names: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "actions", tuple(self.actions))
        if self.enabled_action_names is not None:
            object.__setattr__(self, "enabled_action_names", tuple(self.enabled_action_names))
        if self.substrate_action_count < 0:
            raise ValueError("substrate_action_count must be >= 0")
        if self.custom_action_count < 0:
            raise ValueError("custom_action_count must be >= 0")
        if self.affordance_action_count < 0:
            raise ValueError("affordance_action_count must be >= 0")

    @property
    def action_dim(self) -> int:
        """Total number of action slots."""
        return len(self.actions)

    @property
    def action_ids(self) -> dict[str, int]:
        """Map action names to action IDs."""
        return {action.name: action.id for action in self.actions}
