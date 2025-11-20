"""Runtime effect lifecycle management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import torch

    from townlet.effects.catalog import EffectCatalog
    from townlet.effects.context import ExecutionContext
    from townlet.effects.executor import CommandExecutor

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

    def __init__(self, catalog: EffectCatalog, device: str = "cpu", command_executor: CommandExecutor | None = None) -> None:
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
        bars: dict[str, torch.Tensor] | None = None,
        vfs_registry: Any | None = None,
        spawn_depth: int = 0,
    ) -> ActiveEffect:
        """Spawn new effect instance, handling reapply policies.

        Args:
            effect_id: Effect definition ID from catalog
            target_entity_id: Entity to attach effect to (agent/item/affordance index)
            scope: Effect scope (global/agent/item/affordance)
            duration: Effect duration in ticks
            intensity: Effect intensity multiplier
            current_step: Current environment step
            bars: Current meter values (for on_spawn command execution)
            vfs_registry: VFS registry (for on_spawn command execution)
            spawn_depth: Current cascade depth (for on_spawn command execution)

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

        # Execute on_spawn commands
        if effect_def.on_spawn and self.command_executor and bars is not None:
            from townlet.effects.context import ExecutionContext

            context = ExecutionContext(
                bars=bars,
                vfs_registry=vfs_registry,
                self_index=target_entity_id,
                target_index=None,
                effect=active,
                effect_manager=self,
                spawn_depth=spawn_depth + 1,  # Increment depth for cascade tracking
            )

            for command in effect_def.on_spawn:
                self.command_executor.execute(command, context)

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

    def tick(
        self,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        current_step: int,
        env_state: Any | None = None,  # Keep for backward compatibility
    ) -> None:
        """Execute all active effects for one timestep.

        Updates lifecycle counters (elapsed_ticks, duration_remaining) and
        removes expired effects. Executes on_tick and on_despawn commands
        if command_executor is configured.

        Args:
            bars: Current meter values
            vfs_registry: VFS registry
            current_step: Current environment step
            env_state: Environment state for command execution (deprecated, use bars/vfs_registry)
        """

        self.current_step = current_step

        # Tick global effects
        for i in range(len(self.global_effects) - 1, -1, -1):
            effect = self.global_effects[i]
            self._tick_effect(effect, None, EffectScope.GLOBAL, bars, vfs_registry)
            if effect.duration_remaining <= 0:
                self.global_effects.pop(i)

        # Tick agent effects
        for agent_id, effects in list(self.agent_effects.items()):
            # Process in reverse to safely remove during iteration
            for i in range(len(effects) - 1, -1, -1):
                effect = effects[i]
                self._tick_effect(effect, agent_id, EffectScope.AGENT, bars, vfs_registry)
                if effect.duration_remaining <= 0:
                    self._despawn_effect(effect, agent_id, EffectScope.AGENT, bars, vfs_registry)

    def _tick_effect(
        self,
        effect: ActiveEffect,
        entity_id: int | None,
        scope: EffectScope,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
    ) -> None:
        """Tick a single effect (execute on_tick and update counters)."""
        # Execute on_tick commands
        if effect.effect_id in self.catalog.effects:
            compiled = self.catalog.effects[effect.effect_id]

            if compiled.on_tick and self.command_executor:
                from townlet.effects.context import ExecutionContext

                context = ExecutionContext(
                    bars=bars,
                    vfs_registry=vfs_registry,
                    self_index=entity_id,
                    target_index=None,
                    effect=effect,
                    effect_manager=self,  # Pass self for spawn_effect
                    spawn_depth=0,  # Reset depth for top-level tick
                )

                for command in compiled.on_tick:
                    self.command_executor.execute(command, context)

        # Decrement duration
        effect.duration_remaining -= 1
        effect.elapsed_ticks += 1

    def _despawn_effect(
        self,
        effect: ActiveEffect,
        entity_id: int,
        scope: EffectScope,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
    ) -> None:
        """Despawn effect and execute on_despawn commands."""
        if effect.effect_id in self.catalog.effects:
            compiled = self.catalog.effects[effect.effect_id]

            if compiled.on_despawn and self.command_executor:
                from townlet.effects.context import ExecutionContext

                context = ExecutionContext(
                    bars=bars,
                    vfs_registry=vfs_registry,
                    self_index=entity_id,
                    target_index=None,
                    effect=effect,
                    effect_manager=self,
                    spawn_depth=0,
                )

                for command in compiled.on_despawn:
                    self.command_executor.execute(command, context)

        # Remove from storage
        if scope == EffectScope.AGENT and entity_id in self.agent_effects:
            self.agent_effects[entity_id].remove(effect)

    def _build_context(self, effect: ActiveEffect, env_state: Any) -> ExecutionContext:
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
            effect=effect,  # Pass effect for effect-specific variables
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
