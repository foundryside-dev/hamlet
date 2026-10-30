"""Runtime effect lifecycle management."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.effects.catalog import EffectCatalog
    from townlet.effects.context import ExecutionContext
    from townlet.effects.executor import CommandExecutor
    from townlet.substrate.base import SpatialSubstrate

from townlet.config.effects_config import EffectScope
from townlet.effects.admission import EffectAdmissionSnapshot
from townlet.effects.schema import CommandNode, CommandType
from townlet.numeric import require_float32

__all__ = [
    "ActiveEffect",
    "EffectManager",
]


class NullItemManager:
    """Fallback ItemManager to satisfy ExecutionContext when items are disabled."""

    def spawn_item(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("ItemManager is not configured; spawn_item is unavailable")

    find_spawn_location = spawn_item

    @property
    def num_worlds(self) -> int:
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
    # The one world it lives in (S1: the batch is independent single-agent worlds). It
    # reads and writes only this world; see EffectManager.spawn_effect for the rule.
    world: int

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


@dataclass(frozen=True)
class _Spatial:
    """The spatial state one spawn or tick hands every lifecycle context it builds."""

    agent_positions: torch.Tensor | None
    affordance_positions: dict[str, torch.Tensor] | None
    substrate: SpatialSubstrate | None


class EffectManager:
    """Manages all active effects across all entities."""

    def __init__(
        self,
        catalog: EffectCatalog,
        device: str = "cpu",
        command_executor: CommandExecutor | None = None,
        scheduler: Any | None = None,
        time_enabled: bool = True,
        affordance_overrides: list[dict[str, bool]] | None = None,
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
        self._admission_transaction_active = False
        # One random stream per world for effect sampling (`sample`, `uniform()`,
        # `normal_dist()`), so one world's draws never shift another's (S1). Seeded from
        # the run seed (`torch.initial_seed()`), the world and the episode; made on first use.
        self._episode = 0
        self.world_rngs: dict[int, torch.Generator] = {}

        # Scoped storage. Every effect lives in one world (S1); a store's key carries it:
        # an agent row and an item-arena row each belong to exactly one world, and the
        # global and affordance stores are keyed by world explicitly.
        self.global_effects: dict[int, list[ActiveEffect]] = {}  # world -> effects
        self.agent_effects: dict[int, list[ActiveEffect]] = {}  # agent row -> effects
        self.item_effects: dict[int, list[ActiveEffect]] = {}  # item-arena row -> effects
        self.affordance_effects: dict[tuple[int, int], list[ActiveEffect]] = {}  # (world, entity) -> effects

    def spawn_effect(
        self,
        effect_id: str,
        target_entity_id: int,
        intensity: float,
        current_step: int,
        bars: dict[str, torch.Tensor] | None = None,
        vfs_registry: Any | None = None,
        spawn_depth: int = 0,
        agent_positions: torch.Tensor | None = None,
        item_manager: Any | None = None,
        affordance_positions: dict[str, torch.Tensor] | None = None,
        substrate: SpatialSubstrate | None = None,
        world: int | None = None,
    ) -> ActiveEffect:
        """Spawn new effect instance, handling reapply policies.

        Every effect lives in exactly one world (S1: the batch is independent
        single-agent worlds). An agent-scoped effect lives in its agent's world and an
        item-scoped one in its item's world; `world`, when given, must agree. A global- or
        affordance-scoped effect has no entity that names a world, so `world` (the world
        whose event spawned it) is required. A spawner bound to no world spawns one
        instance per world: `CommandExecutor` loops; this method never broadcasts.

        Args:
            effect_id: Effect definition ID from catalog
            target_entity_id: Entity to attach effect to (agent/item/affordance index)
            intensity: Effect intensity multiplier
            current_step: Current environment step
            bars: Current meter values (for on_spawn command execution)
            vfs_registry: VFS registry (for on_spawn command execution)
            spawn_depth: Current cascade depth (for on_spawn command execution)
            agent_positions: Agent positions [num_agents, position_dim] (spatial reads, spawn_item origins)
            item_manager: ItemManager for spawn_item commands
            affordance_positions: Affordance positions by name (affordance-spatial functions)
            substrate: Substrate whose declared metric measures distance
            world: The world the spawning event happened in

        Returns:
            ActiveEffect instance
        """
        effect_def = self.catalog.effects[effect_id]
        scope = EffectScope(effect_def.scope)
        world = self.effect_world(scope, target_entity_id, world=world, vfs_registry=vfs_registry)
        existing = self._find_existing(effect_id, self._scope_key(scope, target_entity_id, world), scope)
        pipelines = []
        if existing is None or effect_def.reapply_policy == "stack":
            pipelines.append(effect_def.on_spawn)
        elif effect_def.reapply_policy in {"merge", "replace"}:
            pipelines.append(effect_def.on_interrupt)
            if effect_def.reapply_policy == "replace":
                pipelines.append(effect_def.on_spawn)
        owns_transaction = (
            not self._admission_transaction_active
            and self.command_executor is not None
            and bars is not None
            and any(self._has_immediate_spawn(pipeline) for pipeline in pipelines)
        )
        snapshot = None
        if owns_transaction:
            from townlet.effects.context import _NullItemManager as ContextNullItemManager
            from townlet.environment.null_managers import NullItemManager as EnvironmentNullItemManager

            snapshot_item_manager = item_manager
            if isinstance(item_manager, (NullItemManager, ContextNullItemManager, EnvironmentNullItemManager)):
                snapshot_item_manager = None
            snapshot = EffectAdmissionSnapshot.capture(
                manager=self,
                bars=bars,
                registry=vfs_registry,
                item_manager=snapshot_item_manager,
            )
            self._admission_transaction_active = True
        try:
            return self._spawn_effect(
                effect_id,
                target_entity_id,
                world,
                intensity,
                current_step,
                bars,
                vfs_registry,
                spawn_depth,
                item_manager,
                _Spatial(agent_positions, affordance_positions, substrate),
            )
        except PermissionError:
            if snapshot is not None:
                snapshot.restore()
            raise
        finally:
            if owns_transaction:
                self._admission_transaction_active = False

    @classmethod
    def _has_immediate_spawn(cls, commands: list[CommandNode]) -> bool:
        """Detect cascades without evaluating targets or entering delayed work."""
        for command in commands:
            if command.type == CommandType.SPAWN_EFFECT:
                return True
            branches = [command.then_commands, command.else_commands, command.body, command.parallel_commands, command.default_commands]
            branches.extend(commands for _, commands in command.case_asts or [])
            if any(cls._has_immediate_spawn(branch) for branch in branches if branch):
                return True
        return False

    @staticmethod
    def effect_world(scope: EffectScope, target_entity_id: int, *, world: int | None, vfs_registry: Any | None) -> int:
        """The one world an effect of `scope` attached to `target_entity_id` lives in.

        An agent's world is its row (S1: world i is agent i's); an item's world is its
        arena row's; a global or affordance effect's is the spawning world. A spawn
        that names an entity outside the spawning world would write another world's
        state, so it is refused.
        """
        if scope is EffectScope.AGENT:
            entity_world = int(target_entity_id)
        elif scope is EffectScope.ITEM:
            if vfs_registry is None:
                if world is None:
                    raise ValueError("An item-scoped effect needs the VFS registry (or world=) to find its item's world")
                return int(world)
            entity_world = vfs_registry.item_world(int(target_entity_id))
        else:
            if world is None:
                raise ValueError(
                    f"A {scope.value}-scoped effect lives in the world whose event spawned it; spawn it with world= "
                    "(a spawner bound to no world spawns one instance per world)"
                )
            return int(world)
        if world is not None and int(world) != entity_world:
            raise ValueError(
                f"Cannot spawn a {scope.value}-scoped effect on {scope.value} {target_entity_id} (world {entity_world}) "
                f"from world {world}: worlds are independent, an event writes only its own world"
            )
        return entity_world

    @staticmethod
    def _scope_key(scope: EffectScope, target_entity_id: int, world: int) -> Any:
        """The key of an effect in its scope's store (agent row, item row, world, or (world, entity))."""
        if scope is EffectScope.GLOBAL:
            return world
        if scope is EffectScope.AFFORDANCE:
            return (world, int(target_entity_id))
        return int(target_entity_id)

    def world_rng(self, world: int, device: torch.device) -> torch.Generator:
        """World `world`'s effect random stream for this episode."""
        generator = self.world_rngs.get(world)
        if generator is None:
            digest = hashlib.blake2b(f"effects:{torch.initial_seed()}:{self._episode}:{world}".encode(), digest_size=8).digest()
            generator = torch.Generator(device=device)
            generator.manual_seed(int.from_bytes(digest, "little") & ((1 << 63) - 1))
            self.world_rngs[world] = generator
        return generator

    def _store(self, scope: EffectScope) -> dict[Any, list[ActiveEffect]]:
        if scope is EffectScope.GLOBAL:
            return self.global_effects
        if scope is EffectScope.AGENT:
            return self.agent_effects
        if scope is EffectScope.ITEM:
            return self.item_effects
        return self.affordance_effects

    def _spawn_effect(
        self,
        effect_id: str,
        target_entity_id: int,
        world: int,
        intensity: float,
        current_step: int,
        bars: dict[str, torch.Tensor] | None,
        vfs_registry: Any | None,
        spawn_depth: int,
        item_manager: Any | None,
        spatial: _Spatial,
    ) -> ActiveEffect:
        # Get compiled effect definition (validates effect_id exists)
        effect_def = self.catalog.effects[effect_id]
        scope = EffectScope(effect_def.scope)
        duration = effect_def.duration
        intensity = require_float32(intensity, field=f"effect {effect_id!r} intensity")
        effect_index = self.catalog.get_effect_index(effect_id)
        observable = effect_def.observable

        # Check for existing effect on same target (in the same world)
        existing = self._find_existing(effect_id, self._scope_key(scope, target_entity_id, world), scope)

        if existing and effect_def.reapply_policy == "renew":
            # Renew invokes no lifecycle commands.
            existing.duration_remaining = duration
            return existing

        merging = existing is not None and effect_def.reapply_policy == "merge"
        replacing = existing is not None and effect_def.reapply_policy == "replace"
        merged_intensity = (
            require_float32(existing.intensity + intensity, field=f"merged effect intensity for {effect_id!r}")
            if merging and existing is not None
            else intensity
        )
        active = (
            existing
            if merging
            else ActiveEffect(
                effect_id=effect_id,
                instance_id=self.next_instance_id,
                target_entity_id=target_entity_id,
                scope=scope,
                world=world,
                intensity=intensity,
                duration_total=duration,
                duration_remaining=duration,
                elapsed_ticks=0,
                spawn_step=current_step,
                observable=observable,
                effect_index=effect_index,
            )
        )
        assert active is not None

        # Resolve every immediate lifecycle context before changing manager state.
        # In particular, replacement must authorize BOTH hooks before interrupting
        # the existing effect, and item writes must use the attached row's profile.
        interrupt_context = None
        spawn_context = None
        if self.command_executor is not None and bars is not None:
            if (merging or replacing) and existing is not None and effect_def.on_interrupt:
                interrupt_context = self._lifecycle_context(
                    existing,
                    bars=bars,
                    vfs_registry=vfs_registry,
                    item_manager=item_manager,
                    spawn_depth=spawn_depth,
                    spatial=spatial,
                    interrupt_reason="merged_by_effect" if merging else "replaced_by_effect",
                    current_tick=current_step,
                )
                self.command_executor.preflight_commands(effect_def.on_interrupt, interrupt_context)
            if not merging and effect_def.on_spawn:
                spawn_context = self._lifecycle_context(
                    active,
                    bars=bars,
                    vfs_registry=vfs_registry,
                    item_manager=item_manager,
                    spawn_depth=spawn_depth + 1,
                    spatial=spatial,
                    current_tick=current_step,
                )
                self.command_executor.preflight_commands(effect_def.on_spawn, spawn_context)

        if merging:
            active.intensity = merged_intensity
        elif replacing and existing is not None:
            self._cancel_scheduled_for_effect(existing)

        if interrupt_context is not None and self.command_executor is not None:
            for command in effect_def.on_interrupt:
                self.command_executor.execute(command, interrupt_context)
        if merging:
            return active
        if replacing and existing is not None:
            self._remove_from_scope(existing)

        # Interrupt hooks can themselves spawn effects. Allocate the final ID only
        # after they execute, preserving the successful path's allocation order.
        active.instance_id = self.next_instance_id
        self.next_instance_id += 1
        self._add_to_scope(active)
        if spawn_context is not None and self.command_executor is not None:
            for command in effect_def.on_spawn:
                self.command_executor.execute(command, spawn_context)

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
        spatial: _Spatial,
        interrupt_reason: str | None = None,
        write_mask: torch.Tensor | None = None,
    ) -> ExecutionContext:
        """Build one scope-authoritative context for every effect lifecycle hook.

        An agent- or item-scoped effect's `self` and `target` are its entity. A global-
        or affordance-scoped effect has no agent: it addresses its world's agents with
        `for_each: all_agents`, never through a vestigial entity index.
        """
        from townlet.effects.context import ExecutionContext

        scope = EffectScope(effect.scope)
        entity_id: int | None = None
        if scope in {EffectScope.AGENT, EffectScope.ITEM}:
            entity_id = effect.target_entity_id
        is_item = scope == EffectScope.ITEM
        return ExecutionContext(
            bars=bars,
            vfs_registry=vfs_registry,
            self_index=entity_id,
            target_index=entity_id,
            effect=effect,
            write_mask=write_mask,
            self_is_item=is_item,
            target_is_item=is_item,
            effect_manager=self,
            item_manager=item_manager or NullItemManager(),
            spawn_depth=spawn_depth,
            agent_positions=spatial.agent_positions,
            affordance_positions=spatial.affordance_positions,
            substrate=spatial.substrate,
            interrupt_reason=interrupt_reason,
            current_tick=current_tick,
            scheduler=self.scheduler,
            affordance_overrides=self.affordance_overrides,
        )

    def _add_to_scope(self, effect: ActiveEffect) -> None:
        """Add effect to its scope's store, under its world-carrying key."""
        key = self._scope_key(effect.scope, effect.target_entity_id, effect.world)
        store = self._store(effect.scope)
        if key not in store:
            store[key] = []
        store[key].append(effect)

    def _find_existing(self, effect_id: str, key: Any, scope: EffectScope) -> ActiveEffect | None:
        """The live instance of `effect_id` under scope-store `key`, if any."""
        store = self._store(scope)
        if key not in store:
            return None
        for effect in store[key]:
            if effect.effect_id == effect_id:
                return effect
        return None

    def _remove_from_scope(self, effect: ActiveEffect) -> None:
        """Remove effect from its scope's store."""
        key = self._scope_key(effect.scope, effect.target_entity_id, effect.world)
        collection = self._store(effect.scope).get(key)
        if collection is not None and effect in collection:
            collection.remove(effect)

    def get_observable_agent_effects(self, agent_id: int) -> list[ActiveEffect]:
        """Return observable effects attached to a specific agent."""
        effects = self.agent_effects.get(agent_id, [])
        return [eff for eff in effects if eff.observable]

    @classmethod
    def schedule_key(cls, effect: ActiveEffect) -> tuple[str, Any]:
        """The scheduler (scope, entity) key of delayed work an effect schedules.

        One key per effect entity in its world, so cancelling one world's global effect
        never cancels another world's delayed work.
        """
        scope = EffectScope(effect.scope)
        return scope.value, cls._scope_key(scope, effect.target_entity_id, effect.world)

    def _cancel_scheduled_for_effect(self, effect: ActiveEffect) -> None:
        """Cancel any scheduled commands tied to the effect's scope/entity."""
        if not self.scheduler:
            return
        scope_value, entity = self.schedule_key(effect)
        self.scheduler.cancel(scope=scope_value, entity_id=entity)

    def discard_item_effects(self, item_row: int) -> None:
        """Drop every effect on item row `item_row`, and their delayed work, as the item leaves.

        A hard clear (no on_interrupt / on_despawn): the item's state row is being
        unregistered, so a hook would read a row that no longer has a profile. The
        same hard-clear rule as an episode reset, scoped to one item.
        """
        for effect in self.item_effects.pop(item_row, []):
            self._cancel_scheduled_for_effect(effect)
        self.cancel_scheduled_for_entity(scope=EffectScope.ITEM.value, entity_id=item_row)

    def cancel_scheduled_for_entity(self, scope: str, entity_id: Any) -> None:
        """Cancel scheduled commands for a given scope/entity (external callers)."""
        if not self.scheduler:
            return
        self.scheduler.cancel(scope=scope, entity_id=entity_id)

    def reset(self) -> None:
        """Discard every effect and all delayed work at an episode boundary.

        Effects are episode-scoped. ``reset()`` empties the global, agent, item and
        affordance stores, clears the scheduler and rewinds its clock to tick 0, and
        restarts ``next_instance_id`` and ``current_step`` at 0, so per-instance
        counters (``elapsed_ticks``, ``duration_remaining``, ``intensity``) cannot
        survive into the next episode.

        It is a hard clear: no ``on_despawn`` or ``on_interrupt`` hook runs. The
        environment has already re-initialised meters and episode-scoped VFS state
        when it calls this, so a hook write would land in the new episode, which is
        the carry-over this method exists to prevent.

        A legitimately re-spawned effect is one that a spawn path re-creates after
        ``reset()`` returns: an interaction, a cascade, or a delayed command
        scheduled in the new episode. Such an instance starts fresh
        (new instance id, full duration, zero elapsed ticks). There is no
        ``on_reset`` hook; an effect that should be live at tick 0 would need one
        declared, never a surviving instance.
        """
        self.global_effects.clear()
        self.agent_effects.clear()
        self.item_effects.clear()
        self.affordance_effects.clear()
        self.scheduler.reset(current_tick=0)
        self.next_instance_id = 0
        self.current_step = 0
        self._admission_transaction_active = False
        self._episode += 1
        self.world_rngs.clear()

    def tick(
        self,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        current_step: int,
        item_manager: Any | None = None,
        agent_positions: torch.Tensor | None = None,
        affordance_positions: dict[str, torch.Tensor] | None = None,
        substrate: SpatialSubstrate | None = None,
        live: torch.Tensor | None = None,
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
            agent_positions: Agent positions [num_agents, position_dim] this tick
            affordance_positions: Affordance positions by name this tick
            substrate: Substrate whose declared metric measures distance
            live: `[num_worlds]` bool, the worlds whose agent is live this tick (None: all).
                Every hook and delayed block runs under it as a write mask, so an effect in
                a world whose agent is done writes nothing (dead agents freeze, as VTC
                rules do), and a persistent global carries no posthumous advance.

        Every lifecycle hook and delayed block run by this tick sees the same spatial
        state, so position reads (`distance_to_affordance`, `in_range`, `nearby_agents`)
        evaluate inside effects. Without it those reads refuse at runtime.
        """

        item_manager = item_manager or NullItemManager()
        spatial = _Spatial(agent_positions, affordance_positions, substrate)
        self.current_step = current_step

        # Execute any scheduled commands due at this tick before on_tick handlers
        if self.scheduler:
            due_items = self.scheduler.advance(current_step)
            self._execute_scheduled_items(due_items, bars, vfs_registry, item_manager, spatial, live)

        for store in (self.global_effects, self.agent_effects, self.item_effects, self.affordance_effects):
            for effects in list(store.values()):
                self._tick_scope_collection(effects, bars, vfs_registry, item_manager, spatial, live)

        # Drain any zero-delay commands scheduled during this tick
        if self.scheduler:
            while True:
                pending_now = self.scheduler.drain_due()
                if not pending_now:
                    break
                self._execute_scheduled_items(pending_now, bars, vfs_registry, item_manager, spatial, live)

    def _tick_scope_collection(
        self,
        effects: list[ActiveEffect],
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None,
        spatial: _Spatial,
        live: torch.Tensor | None,
    ) -> None:
        """Tick and naturally despawn one scope collection in reverse removal order."""
        for effect in reversed(effects.copy()):
            self._tick_effect(effect, bars, vfs_registry, item_manager, spatial, live)
            if effect.duration_remaining <= 0:
                self._despawn_effect(effect, bars, vfs_registry, item_manager, spatial, interrupt_reason=None, write_mask=live)

    def _execute_scheduled_items(
        self,
        scheduled_items: list[Any],
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        item_manager: Any | None,
        spatial: _Spatial,
        live: torch.Tensor | None,
    ) -> None:
        """Execute scheduled commands using the current tick context.

        A delayed block keeps the mask that was live when it was scheduled, narrowed by
        this tick's live worlds.
        """

        if not scheduled_items or self.command_executor is None:
            return

        from townlet.effects.context import ExecutionContext

        queue = list(scheduled_items)
        while queue:
            item = queue.pop(0)

            overrides = dict(item.context_overrides)
            self_index = overrides.pop("self_index", None)
            target_index = overrides.pop("target_index", None)
            self_is_item = overrides.pop("self_is_item", False)
            target_is_item = overrides.pop("target_is_item", False)
            spawn_depth = overrides.pop("spawn_depth", 0)
            effect_override = overrides.pop("effect", None)
            write_mask = overrides.pop("write_mask", None)
            if live is not None and write_mask is None:
                write_mask = live
            elif live is not None:
                write_mask = write_mask & live

            # Derive defaults from scope/entity when not explicitly provided
            if item.scope == "agent" and self_index is None and item.entity_id is not None:
                self_index = int(item.entity_id)
                if target_index is None:
                    target_index = self_index
            if item.scope == "item" and self_index is None and item.entity_id is not None:
                self_index = int(item.entity_id)
                self_is_item = True

            ctx = ExecutionContext(
                bars=bars,
                vfs_registry=vfs_registry,
                self_index=self_index,
                target_index=target_index,
                effect=effect_override,
                write_mask=write_mask,
                self_is_item=self_is_item,
                target_is_item=target_is_item,
                effect_manager=self,
                item_manager=item_manager or NullItemManager(),
                spawn_depth=spawn_depth,
                agent_positions=spatial.agent_positions,
                affordance_positions=spatial.affordance_positions,
                substrate=spatial.substrate,
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
        item_manager: Any | None,
        spatial: _Spatial,
        live: torch.Tensor | None,
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
                    current_tick=self.current_step,
                    spatial=spatial,
                    write_mask=live,
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
        item_manager: Any | None,
        spatial: _Spatial,
        interrupt_reason: str | None = None,
        write_mask: torch.Tensor | None = None,
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
                    current_tick=self.current_step,
                    spatial=spatial,
                    write_mask=write_mask,
                )

                for command in compiled.on_despawn:
                    self.command_executor.execute(command, context)

        self._remove_from_scope(effect)

    def get_all_active_effects(self) -> list[ActiveEffect]:
        """Get all active effects across all scopes (for testing).

        Returns:
            List of all active effects
        """
        result: list[ActiveEffect] = []
        for store in (self.global_effects, self.agent_effects, self.item_effects, self.affordance_effects):
            for effects in store.values():
                result.extend(effects)
        return result

    def effects_in_world(self, world: int) -> list[ActiveEffect]:
        """Every active effect living in `world`, any scope."""
        return [effect for effect in self.get_all_active_effects() if effect.world == world]

    def cancel_effect(
        self,
        instance_id: int,
        bars: dict[str, torch.Tensor],
        vfs_registry: Any | None,
        current_step: int,
        item_manager: Any | None = None,
        agent_positions: torch.Tensor | None = None,
        affordance_positions: dict[str, torch.Tensor] | None = None,
        substrate: SpatialSubstrate | None = None,
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
                spatial=_Spatial(agent_positions, affordance_positions, substrate),
            )

            for command in compiled.on_interrupt:
                self.command_executor.execute(command, context)

        # Remove effect (no on_despawn when manually cancelled).
        self._remove_from_scope(target_effect)
