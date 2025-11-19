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

    def __init__(self, catalog, device: str = "cpu"):
        """Initialize effect manager with compiled catalog.

        Args:
            catalog: Compiled EffectCatalog from world compiler
            device: PyTorch device for tensor operations
        """
        self.catalog = catalog
        self.device = device
        self.current_step = 0  # Track environment step
        self.next_instance_id = 0

        # Scoped storage
        self.global_effects: list[ActiveEffect] = []
        self.agent_effects: dict[int, list[ActiveEffect]] = {}  # agent_id -> effects
        self.item_effects: dict[int, list[ActiveEffect]] = {}  # item_id -> effects
        self.affordance_effects: dict[str, list[ActiveEffect]] = {}  # affordance_id -> effects

    def spawn_effect(
        self,
        effect_id: str,
        target_entity_id: int,
        scope: EffectScope,
        duration: int,
        intensity: float,
        current_step: int,
    ) -> ActiveEffect:
        """Spawn new effect instance.

        Args:
            effect_id: Effect definition ID from catalog
            target_entity_id: Entity to attach effect to (agent/item/affordance index)
            scope: Effect scope (global/agent/item/affordance)
            duration: Effect duration in ticks
            intensity: Effect intensity multiplier
            current_step: Current environment step

        Returns:
            ActiveEffect instance
        """
        # Get compiled effect definition (validates effect_id exists)
        _ = self.catalog.effects[effect_id]

        # For now: STACK policy only (create new instance)
        # TODO: Handle other reapply policies in Step 3

        # Create new instance
        active = ActiveEffect(
            effect_id=effect_id,
            instance_id=self.next_instance_id,
            target_entity_id=target_entity_id,
            scope=scope,
            intensity=intensity,
            duration_total=duration,
            duration_remaining=duration,
            elapsed_ticks=0,
            spawn_step=current_step,
        )
        self.next_instance_id += 1

        # Store in scoped collection
        self._add_to_scope(active)

        return active

    def _add_to_scope(self, effect: ActiveEffect) -> None:
        """Add effect to appropriate scoped collection."""
        if effect.scope == EffectScope.GLOBAL:
            self.global_effects.append(effect)
        elif effect.scope == EffectScope.AGENT:
            if effect.target_entity_id not in self.agent_effects:
                self.agent_effects[effect.target_entity_id] = []
            self.agent_effects[effect.target_entity_id].append(effect)
        elif effect.scope == EffectScope.ITEM:
            if effect.target_entity_id not in self.item_effects:
                self.item_effects[effect.target_entity_id] = []
            self.item_effects[effect.target_entity_id].append(effect)
        elif effect.scope == EffectScope.AFFORDANCE:
            # Note: affordance_effects keyed by affordance_id (string), not entity_id
            # For now, store by string representation of target_entity_id
            key = str(effect.target_entity_id)
            if key not in self.affordance_effects:
                self.affordance_effects[key] = []
            self.affordance_effects[key].append(effect)
