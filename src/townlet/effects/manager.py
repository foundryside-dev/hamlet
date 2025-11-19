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

    def __init__(self, catalog, device: str = "cpu", command_executor=None):
        """Initialize effect manager with compiled catalog.

        Args:
            catalog: Compiled EffectCatalog from world compiler
            device: PyTorch device for tensor operations
            command_executor: CommandExecutor for running effect commands (optional)
        """
        self.catalog = catalog
        self.device = device
        self.command_executor = command_executor
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
        """Spawn new effect instance, handling reapply policies.

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
        effect_def = self.catalog.effects[effect_id]

        # Check for existing effect on same target
        existing = self._find_existing(effect_id, target_entity_id, scope)

        if existing:
            # Handle reapply policy
            if effect_def.reapply_policy == "renew":
                # Reset duration to full
                existing.duration_remaining = duration
                return existing

            elif effect_def.reapply_policy == "merge":
                # Accumulate intensity
                existing.intensity += intensity
                return existing

            elif effect_def.reapply_policy == "replace":
                # Remove old instance
                self._remove_from_scope(existing)
                # Continue to create new instance below

            # STACK: Do nothing, create new instance below

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

    def _find_existing(self, effect_id: str, target_entity_id: int, scope: EffectScope) -> ActiveEffect | None:
        """Find existing effect on target.

        Args:
            effect_id: Effect definition ID
            target_entity_id: Target entity ID
            scope: Effect scope

        Returns:
            ActiveEffect if found, None otherwise
        """
        collection = self._get_scope_collection(target_entity_id, scope)
        if collection is None:
            return None

        for effect in collection:
            if effect.effect_id == effect_id:
                return effect

        return None

    def _get_scope_collection(self, target_entity_id: int, scope: EffectScope) -> list[ActiveEffect] | None:
        """Get scoped collection for target.

        Args:
            target_entity_id: Target entity ID
            scope: Effect scope

        Returns:
            List of effects for this scope/target, or None if not found
        """
        if scope == EffectScope.GLOBAL:
            return self.global_effects
        elif scope == EffectScope.AGENT:
            return self.agent_effects.get(target_entity_id)
        elif scope == EffectScope.ITEM:
            return self.item_effects.get(target_entity_id)
        elif scope == EffectScope.AFFORDANCE:
            return self.affordance_effects.get(str(target_entity_id))
        return None

    def _remove_from_scope(self, effect: ActiveEffect) -> None:
        """Remove effect from scoped collection.

        Args:
            effect: Effect to remove
        """
        collection = self._get_scope_collection(effect.target_entity_id, effect.scope)
        if collection is not None and effect in collection:
            collection.remove(effect)

    def tick(self, current_step: int, env_state=None) -> None:
        """Execute all active effects for one timestep.

        Updates lifecycle counters (elapsed_ticks, duration_remaining) and
        removes expired effects. Executes on_tick and on_despawn commands
        if command_executor is configured.

        Args:
            current_step: Current environment step
            env_state: Environment state for command execution (optional)
        """
        self.current_step = current_step

        # Process all scopes
        all_collections = [
            self.global_effects,
            *self.agent_effects.values(),
            *self.item_effects.values(),
            *self.affordance_effects.values(),
        ]

        for collection in all_collections:
            # Process in reverse to safely remove during iteration
            for i in range(len(collection) - 1, -1, -1):
                effect = collection[i]

                # Execute on_tick commands if executor available
                if self.command_executor and env_state:
                    context = self._build_context(effect, env_state)
                    effect_def = self.catalog.effects[effect.effect_id]
                    self.command_executor.execute_commands(effect_def.on_tick, context)

                # Update lifecycle
                effect.elapsed_ticks += 1
                effect.duration_remaining -= 1

                # Check for expiry
                if effect.duration_remaining <= 0:
                    # Execute on_despawn commands before removal
                    if self.command_executor and env_state:
                        context = self._build_context(effect, env_state)
                        effect_def = self.catalog.effects[effect.effect_id]
                        self.command_executor.execute_commands(effect_def.on_despawn, context)

                    # Despawn (remove from collection)
                    collection.pop(i)

    def _build_context(self, effect: ActiveEffect, env_state):
        """Build ExecutionContext for effect.

        Args:
            effect: Active effect instance
            env_state: Environment state (bars, VFS, etc.)

        Returns:
            ExecutionContext with effect and target references
        """
        from townlet.effects.context import ExecutionContext

        # Extract state from env_state
        bars = getattr(env_state, "bars", None)
        vfs_registry = getattr(env_state, "vfs_registry", None)

        return ExecutionContext(
            bars=bars,
            vfs_registry=vfs_registry,
            self_index=None,  # Not used in effect context
            target_index=effect.target_entity_id,
        )

    def get_all_active_effects(self) -> list[ActiveEffect]:
        """Get all active effects across all scopes (for testing).

        Returns:
            List of all active effects
        """
        result = []
        result.extend(self.global_effects)
        for effects in self.agent_effects.values():
            result.extend(effects)
        for effects in self.item_effects.values():
            result.extend(effects)
        for effects in self.affordance_effects.values():
            result.extend(effects)
        return result
