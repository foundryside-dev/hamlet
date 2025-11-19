"""Runtime effect lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectScope

__all__ = [
    "ActiveEffect",
    "EffectManager",
]


@dataclass
class ActiveEffect:
    """Runtime instance of an effect attached to an entity.

    Tracks lifecycle state (duration, intensity, elapsed time) and
    references the compiled effect definition from the catalog.
    """

    effect_id: str  # Reference to catalog definition
    instance_id: int  # Unique instance ID
    target_entity_id: int  # What it's attached to (agent/item/affordance index)
    scope: EffectScope  # Where it lives (global/agent/item/affordance)

    # Lifecycle state
    intensity: float  # Current intensity multiplier
    duration_total: int  # Total ticks when spawned
    duration_remaining: int  # Ticks until despawn
    elapsed_ticks: int  # How long active
    spawn_step: int  # When it was created


class EffectManager:
    """Manages all active effects across all entities."""

    def __init__(self, device: str = "cpu"):
        """Initialize empty effect manager.

        Args:
            device: PyTorch device for tensor operations
        """
        self.device = device
        self.next_instance_id = 0

        # Scoped storage
        self.global_effects: list[ActiveEffect] = []
        self.agent_effects: dict[int, list[ActiveEffect]] = {}  # agent_id -> effects
        self.item_effects: dict[int, list[ActiveEffect]] = {}  # item_id -> effects
        self.affordance_effects: dict[str, list[ActiveEffect]] = {}  # affordance_id -> effects
