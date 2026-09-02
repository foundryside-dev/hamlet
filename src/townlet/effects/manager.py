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
from townlet.numeric import require_float32

__all__ = [
    "ActiveEffect",
    "EffectManager",
]


class NullItemManager:
    """Fallback ItemManager to satisfy ExecutionContext when items are disabled."""

    def spawn_item(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("ItemManager is not configured; spawn_item is unavailable")

    def tick(self, *args: Any, **kwargs: Any) -> None:
        return None

    def process_respawns(self, *args: Any, **kwargs: Any) -> None:
        return None


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
    observable: bool  # Whether the effect is exposed in observations
    effect_index: int = -1  # Stable integer ID for observation encoding

    def __post_init__(self) -> None:
        self.intensity = require_float32(self.intensity, field=f"active effect {self.effect_id!r} intensity")


class EffectManager:
    """Manages all active effects across all entities."""

    def __init__(
        self,
        catalog: EffectCatalog,
        device: str = "cpu",
        command_executor: CommandExecutor | None = None,
        scheduler: Any | None = None,
        time_enabled: bool = True,
        affordance_overrides: dict[str, bool] | None = None,
    ) -> None:
        """Initialize effect manager with compiled catalog.

        Args:
            catalog: Compiled EffectCatalog from world compiler
            device: PyTorch device for tensor operations
            command_executor: CommandExecutor for running effect commands (optional)
        """
        self.catalog = catalog
        self.device = device
        self.command_executor = command_executor
        from townlet.effects.scheduler import Scheduler

        self.scheduler = scheduler or Scheduler(time_enabled=time_enabled)
        self.affordance_overrides = affordance_overrides
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
        intensity: float,
        current_step: int,
        bars: dict[str, torch.Tensor] | None = None,
        vfs_registry: Any | None = None,
        spawn_depth: int = 0,
        agent_positions: Any | None = None,  # NEW: for for_each spatial queries
        item_manager: Any | None = None,  # NEW: ItemManager for spawn_item commands
    ) -> ActiveEffect:
        """Spawn new effect instance, handling reapply policies.

        Args:
            effect_id: Effect definition ID from catalog
            target_entity_id: Entity to attach effect to (agent/item/affordance index)
            intensity: Effect intensity multiplier
            current_step: Current environment step
            bars: Current meter values (for on_spawn command execution)
            vfs_registry: VFS registry (for on_spawn command execution)
            spawn_depth: Current cascade depth (for on_spawn command execution)
            agent_positions: Agent positions tensor [batch, 2] (for for_each spatial queries)

        Returns:
            ActiveEffect instance
        """
        # Get compiled effect definition (validates effect_id exists)
        effect_def = self.catalog.effects[effect_id]
        scope = EffectScope(effect_def.scope)
        duration = effect_def.duration
        intensity = require_float32(intensity, field=f"effect {effect_id!r} intensity")
        effect_index = self.catalog.get_effect_index(effect_id)
        observable = effect_def.observable

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
                merged_intensity = require_float32(
                    existing.intensity + intensity,
                    field=f"merged effect intensity for {effect_id!r}",
                )
                existing.intensity = merged_intensity
                if effect_def.on_interrupt and self.command_executor and bars is not None:
                    context = self._lifecycle_context(
                        existing,
                        bars=bars,
                        vfs_registry=vfs_registry,
                        item_manager=item_manager or NullItemManager(),
                        spawn_depth=spawn_depth,
                        agent_positions=agent_positions,
                        interrupt_reason="merged_by_effect",
                        current_tick=current_step,
                    )

                    for command in effect_def.on_interrupt:
                        self.command_executor.execute(command, context)
                return existing

            elif effect_def.reapply_policy == "replace":
                # Cancel any pending delayed work from the existing effect before replacing
                self._cancel_scheduled_for_effect(existing)

                # NEW: Execute on_interrupt before removing old effect
                if effect_def.on_interrupt and self.command_executor and bars is not None:
                    context = self._lifecycle_context(
                        existing,
                        bars=bars,
                        vfs_registry=vfs_registry,
                        item_manager=item_manager or NullItemManager(),
                        spawn_depth=spawn_depth,
                        agent_positions=agent_positions,
                        interrupt_reason="replaced_by_effect",  # NEW
                        current_tick=current_step,  # NEW
                    )

                    for command in effect_def.on_interrupt:
                        self.command_executor.execute(command, context)

                # Remove old instance (skip on_despawn - already interrupted)
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
            observable=observable,
            effect_index=effect_index,
        )
        self.next_instance_id += 1

        # Store in scoped collection
        self._add_to_scope(active)

        # Execute on_spawn commands
        if effect_def.on_spawn and self.command_executor and bars is not None:
            context = self._lifecycle_context(
                active,
                bars=bars,
                vfs_registry=vfs_registry,
                item_manager=item_manager or NullItemManager(),
                spawn_depth=spawn_depth + 1,  # Increment depth for cascade tracking
                agent_positions=agent_positions,  # NEW: for for_each spatial queries
                current_tick=current_step,  # NEW
            )

            for command in effect_def.on_spawn:
                self.command_executor.execute(command, context)

        return active

    def _lifecycle_context(
        self,
        effect: ActiveEffect,
        *,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None,
        spawn_depth: int,
        current_tick: int,
        agent_positions: Any | None = None,
        interrupt_reason: str | None = None,
    ) -> ExecutionContext:
        """Build one scope-authoritative context for every effect lifecycle hook."""
        from townlet.effects.context import ExecutionContext

        scope = EffectScope(effect.scope)
        entity_id = effect.target_entity_id
        entity_is_indexed_self = scope in {EffectScope.AGENT, EffectScope.ITEM}
        is_item = scope == EffectScope.ITEM
        return ExecutionContext(
            bars=bars,
            vfs_registry=vfs_registry,
            self_index=entity_id if entity_is_indexed_self else None,
            target_index=entity_id,
            effect=effect,
            self_is_item=is_item,
            target_is_item=is_item,
            effect_manager=self,
            item_manager=item_manager or NullItemManager(),
            spawn_depth=spawn_depth,
            agent_positions=agent_positions,
            interrupt_reason=interrupt_reason,
            current_tick=current_tick,
            scheduler=self.scheduler,
            affordance_overrides=self.affordance_overrides,
        )

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

    def get_observable_agent_effects(self, agent_id: int) -> list[ActiveEffect]:
        """Return observable effects attached to a specific agent."""
        effects = self.agent_effects.get(agent_id, [])
        return [eff for eff in effects if eff.observable]

    def _cancel_scheduled_for_effect(self, effect: ActiveEffect) -> None:
        """Cancel any scheduled commands tied to the effect's scope/entity."""
        if not self.scheduler:
            return

        scope_value = effect.scope.value if hasattr(effect.scope, "value") else str(effect.scope)

        if effect.scope == EffectScope.AGENT:
            self.scheduler.cancel(scope=scope_value, entity_id=effect.target_entity_id)
        elif effect.scope == EffectScope.ITEM:
            self.scheduler.cancel(scope=scope_value, entity_id=effect.target_entity_id)
        elif effect.scope == EffectScope.AFFORDANCE:
            self.scheduler.cancel(scope=scope_value, entity_id=str(effect.target_entity_id))
        elif effect.scope == EffectScope.GLOBAL:
            self.scheduler.cancel(scope=scope_value, entity_id=None)

    def cancel_scheduled_for_entity(self, scope: str, entity_id: int | str | None) -> None:
        """Cancel scheduled commands for a given scope/entity (external callers)."""
        if not self.scheduler:
            return
        self.scheduler.cancel(scope=scope, entity_id=entity_id)

    def reset_scheduler(self, current_tick: int = 0) -> None:
        """Reset scheduler and clear all pending delayed work."""
        if self.scheduler:
            self.scheduler.reset(current_tick=current_tick)

    def tick(
        self,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        current_step: int,
        item_manager: Any | None = None,  # NEW: ItemManager for spawn_item commands
        agent_positions: Any | None = None,
    ) -> None:
        """Execute all active effects for one timestep.

        Updates lifecycle counters (elapsed_ticks, duration_remaining) and
        removes expired effects. Executes on_tick and on_despawn commands
        if command_executor is configured.

        Args:
            bars: Current meter values
            vfs_registry: VFS registry
            current_step: Current environment step
            item_manager: ItemManager for spawn_item commands (optional)
        """

        item_manager = item_manager or NullItemManager()
        self.current_step = current_step

        # Execute any scheduled commands due at this tick before on_tick handlers
        if self.scheduler:
            due_items = self.scheduler.advance(current_step)
            self._execute_scheduled_items(due_items, bars, vfs_registry, item_manager, agent_positions)

        self._tick_scope_collection(self.global_effects, bars, vfs_registry, item_manager)
        for effects in list(self.agent_effects.values()):
            self._tick_scope_collection(effects, bars, vfs_registry, item_manager)
        for effects in list(self.item_effects.values()):
            self._tick_scope_collection(effects, bars, vfs_registry, item_manager)
        for effects in list(self.affordance_effects.values()):
            self._tick_scope_collection(effects, bars, vfs_registry, item_manager)

        # Drain any zero-delay commands scheduled during this tick
        if self.scheduler:
            while True:
                pending_now = self.scheduler.drain_due()
                if not pending_now:
                    break
                self._execute_scheduled_items(pending_now, bars, vfs_registry, item_manager, agent_positions)

    def _tick_scope_collection(
        self,
        effects: list[ActiveEffect],
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None,
    ) -> None:
        """Tick and naturally despawn one scope collection in reverse removal order."""
        for effect in reversed(effects.copy()):
            self._tick_effect(effect, bars, vfs_registry, item_manager)
            if effect.duration_remaining <= 0:
                self._despawn_effect(effect, bars, vfs_registry, item_manager, interrupt_reason=None)

    def _execute_scheduled_items(
        self,
        scheduled_items: list[Any],
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None,
        agent_positions: Any | None,
    ) -> None:
        """Execute scheduled commands using the current tick context."""

        if not scheduled_items or self.command_executor is None:
            return

        from townlet.effects.context import ExecutionContext

        queue = list(scheduled_items)
        while queue:
            item = queue.pop(0)

            overrides = dict(getattr(item, "context_overrides", {}) or {})
            self_index = overrides.pop("self_index", None)
            target_index = overrides.pop("target_index", None)
            self_is_item = overrides.pop("self_is_item", False)
            target_is_item = overrides.pop("target_is_item", False)
            spawn_depth = overrides.pop("spawn_depth", 0)
            effect_override = overrides.pop("effect", None)

            # Derive defaults from scope/entity when not explicitly provided
            if item.scope == "agent" and self_index is None and item.entity_id is not None:
                try:
                    self_index = int(item.entity_id)
                except Exception:
                    self_index = item.entity_id
                if target_index is None:
                    target_index = self_index
            if item.scope == "item" and self_index is None and item.entity_id is not None:
                try:
                    self_index = int(item.entity_id)
                except Exception:
                    self_index = item.entity_id
                self_is_item = True

            ctx = ExecutionContext(
                bars=bars,
                vfs_registry=vfs_registry,
                self_index=self_index,
                target_index=target_index,
                effect=effect_override,
                self_is_item=self_is_item,
                target_is_item=target_is_item,
                effect_manager=self,
                item_manager=item_manager or NullItemManager(),
                spawn_depth=spawn_depth,
                agent_positions=agent_positions,
                current_tick=self.current_step,
                scheduler=self.scheduler,
                affordance_overrides=self.affordance_overrides,
            )

            for cmd in item.commands:
                self.command_executor.execute(cmd, ctx)

            if self.scheduler:
                pending_now = self.scheduler.drain_due()
                if pending_now:
                    queue.extend(pending_now)

    def _tick_effect(
        self,
        effect: ActiveEffect,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None = None,  # NEW
    ) -> None:
        """Tick a single effect (execute on_tick and update counters)."""
        # Execute on_tick commands
        if effect.effect_id in self.catalog.effects:
            compiled = self.catalog.effects[effect.effect_id]

            if compiled.on_tick and self.command_executor:
                context = self._lifecycle_context(
                    effect,
                    bars=bars,
                    vfs_registry=vfs_registry,
                    item_manager=item_manager,
                    spawn_depth=0,  # Reset depth for top-level tick
                    current_tick=self.current_step,  # NEW
                )

                for command in compiled.on_tick:
                    self.command_executor.execute(command, context)

        # Decrement duration
        effect.duration_remaining -= 1
        effect.elapsed_ticks += 1

    def _despawn_effect(
        self,
        effect: ActiveEffect,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None = None,  # NEW
        interrupt_reason: str | None = None,
    ) -> None:
        """Despawn effect and execute on_despawn commands."""
        if effect.effect_id in self.catalog.effects:
            compiled = self.catalog.effects[effect.effect_id]

            # Cancel any scheduled work before running on_despawn to avoid orphaned commands
            self._cancel_scheduled_for_effect(effect)

            if compiled.on_despawn and self.command_executor:
                context = self._lifecycle_context(
                    effect,
                    bars=bars,
                    vfs_registry=vfs_registry,
                    item_manager=item_manager,
                    spawn_depth=0,
                    interrupt_reason=interrupt_reason,
                    current_tick=self.current_step,  # NEW
                )

                for command in compiled.on_despawn:
                    self.command_executor.execute(command, context)

        self._remove_from_scope(effect)

    def _build_context(
        self, effect: ActiveEffect, env_state: Any, current_tick: int = 0, item_manager: Any | None = None
    ) -> ExecutionContext:
        """Build ExecutionContext for effect.

        Args:
            effect: Active effect instance
            env_state: Environment state (bars, VFS, etc.)
            current_tick: Current simulation tick (for time-based conditions)

        Returns:
            ExecutionContext with effect and target references
        """
        bars = getattr(env_state, "bars", None)
        vfs_registry = getattr(env_state, "vfs_registry", None)
        return self._lifecycle_context(
            effect,
            bars=bars or {},
            vfs_registry=vfs_registry,
            item_manager=item_manager or NullItemManager(),
            spawn_depth=0,
            current_tick=current_tick,
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

    def cancel_effect(
        self,
        instance_id: int,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        current_step: int,
        item_manager: Any | None = None,
    ) -> None:
        """Manually cancel an effect instance (fail-forward: on_interrupt then remove)."""
        target_effect = next(
            (effect for effect in self.get_all_active_effects() if effect.instance_id == instance_id),
            None,
        )

        if target_effect is None:
            raise ValueError(f"Effect instance {instance_id} not found for cancel_effect")

        compiled = self.catalog.effects.get(target_effect.effect_id)
        if compiled and compiled.on_interrupt and self.command_executor:
            # Cancel pending delayed work tied to this effect before interrupt commands run
            self._cancel_scheduled_for_effect(target_effect)

            context = self._lifecycle_context(
                target_effect,
                bars=bars,
                vfs_registry=vfs_registry,
                item_manager=item_manager or NullItemManager(),
                spawn_depth=0,
                interrupt_reason="manually_cancelled",
                current_tick=current_step,
            )

            for command in compiled.on_interrupt:
                self.command_executor.execute(command, context)

        # Remove effect (no on_despawn when manually cancelled).
        self._remove_from_scope(target_effect)
