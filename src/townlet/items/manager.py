"""ItemManager for spawning/despawning items and managing lifecycle."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
    from townlet.vfs.registry import VariableRegistry

from townlet.config.items_config import SpawnPlacementConfig, SpawnScheduleConfig
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode
from townlet.items.instance import ItemInstance
from townlet.world.expression.context import ExecutionContext as ExprExecutionContext
from townlet.world.expression.evaluator import Evaluator

__all__ = ["ItemManager", "CompiledItemType"]


@dataclass
class CompiledItemType:
    """Item type with pre-compiled Effects commands.

    This is the runtime representation after CommandCompiler processes
    the raw ItemTypeConfig from YAML.
    """

    id: str
    vfs_profile: str
    duration: int | None
    cooldown: int | None

    # Pre-compiled Effects commands (ready for CommandExecutor)
    compiled_on_pickup: list[CommandNode]
    compiled_on_use: list[CommandNode]
    compiled_on_drop: list[CommandNode]


class ItemManager:
    """Manages all items in the world."""

    def __init__(
        self,
        catalog: ItemsCatalogConfig,
        max_items: int,
        device: torch.device | str,
        schema: dict[str, str] | None = None,  # NEW: Schema for Effects compilation
        vfs_registry: VariableRegistry | None = None,  # NEW: VFS registry for item state storage
        effect_manager: Any | None = None,  # NEW: EffectManager for scheduler cancellation
    ) -> None:
        """Initialize ItemManager.

        Args:
            catalog: Items catalog from items.yaml
            max_items: Maximum items that can exist simultaneously
            device: PyTorch device
            schema: Variable type schema for Effects compilation
            vfs_registry: VFS registry for item state storage
        """
        self.catalog = catalog
        self.max_items = max_items
        self.device = torch.device(device) if isinstance(device, str) else device
        self.vfs_registry = vfs_registry  # Store VFS registry
        self.effect_manager = effect_manager

        # Compile item interactions if schema provided
        self.compiled_item_types: list[CompiledItemType] = []

        if schema is not None:
            from townlet.config.effects_config import CommandConfig
            from townlet.effects.parser import CommandParser

            compiler = CommandCompiler(schema=schema)
            parser = CommandParser()

            for item_type in catalog.item_types:
                # Convert raw dicts to CommandConfig objects
                on_pickup_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_pickup]
                on_use_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_use]
                on_drop_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_drop]

                # Parse CommandConfig objects to CommandNode AST
                on_pickup_nodes = parser.parse_commands(on_pickup_configs)
                on_use_nodes = parser.parse_commands(on_use_configs)
                on_drop_nodes = parser.parse_commands(on_drop_configs)

                # Compile with type checking and AST storage
                compiled_on_pickup = compiler.compile_commands(on_pickup_nodes)
                compiled_on_use = compiler.compile_commands(on_use_nodes)
                compiled_on_drop = compiler.compile_commands(on_drop_nodes)

                self.compiled_item_types.append(
                    CompiledItemType(
                        id=item_type.id,
                        vfs_profile=item_type.vfs_profile,
                        duration=item_type.duration,
                        cooldown=item_type.cooldown,
                        compiled_on_pickup=compiled_on_pickup,
                        compiled_on_use=compiled_on_use,
                        compiled_on_drop=compiled_on_drop,
                    )
                )
        else:
            # No schema - store raw types without compilation
            # (Used in unit tests that don't need Effects)
            for item_type in catalog.item_types:
                self.compiled_item_types.append(
                    CompiledItemType(
                        id=item_type.id,
                        vfs_profile=item_type.vfs_profile,
                        duration=item_type.duration,
                        cooldown=item_type.cooldown,
                        compiled_on_pickup=[],
                        compiled_on_use=[],
                        compiled_on_drop=[],
                    )
                )

        self.next_instance_id = 0

        # Active items in the world (visible on grid)
        self.active_items: dict[int, ItemInstance] = {}  # instance_id -> ItemInstance

        # Held items (in agent inventories, not on grid)
        # These items continue to tick (age/spoil) but are not spatially positioned
        self.held_items: dict[int, ItemInstance] = {}

        # VFS slot allocation (fixed-size pool)
        self.vfs_free_slots: set[int] = set(range(max_items))  # Available VFS indices

        # Cooldown tracking (item_type -> tick when can spawn again)
        self.cooldown_until: dict[str, int] = {}

        # Appearance config for periodic respawning
        self.appearance_config: ItemsAppearanceConfig | None = None
        self.grid_size: tuple[int, ...] | None = None

        # Respawn timers (item_type -> tick when should respawn)
        self.respawn_timers: dict[str, int] = {}

        # Track cumulative spawns per appearance rule for max_total enforcement
        self.rule_spawn_counts: dict[str, int] = {}

        # Track next scheduled spawn tick for normal/poisson schedules per item_type
        self.next_scheduled_tick: dict[str, int] = {}

        # Track per-item scripted pointer (next event index) to avoid reusing past events
        self.script_indices: dict[str, int] = {}

    def reset_state(self) -> None:
        """Clear all item runtime state for a fresh episode."""

        self.active_items.clear()
        self.held_items.clear()
        self.vfs_free_slots = set(range(self.max_items))
        self.cooldown_until.clear()
        self.appearance_config = None
        self.grid_size = None
        self.respawn_timers.clear()
        self.next_instance_id = 0
        self.rule_spawn_counts.clear()
        self.next_scheduled_tick.clear()
        self.script_indices.clear()

        if self.vfs_registry is not None and self.vfs_registry.item_vfs is not None:
            from townlet.vfs.schema import VariableScope

            self.vfs_registry.item_vfs.zero_()
            for var_id, var_def in self.vfs_registry.variables.items():
                if var_def.scope != VariableScope.ITEM:
                    continue
                default_value = var_def.default
                if default_value is None:
                    continue
                var_idx = self.vfs_registry.item_var_to_index.get(var_id)
                if var_idx is None:
                    continue
                target_tensor = self.vfs_registry.item_vfs[:, var_idx]
                if isinstance(default_value, list):
                    target_tensor.fill_(default_value[0])
                else:
                    target_tensor.fill_(default_value)

    def find_spawn_location(
        self,
        strategy: str,
        origin: tuple[int, ...] | tuple[float, ...] | None = None,
        explicit: tuple[int, ...] | tuple[float, ...] | None = None,
        retries: int = 3,
    ) -> tuple[int, ...]:
        """Resolve spawn position with collision avoidance and fail-fast on unsupported inputs."""
        if strategy in {"self", "target"}:
            if origin is None:
                raise RuntimeError(f"Origin required for strategy '{strategy}'")
            return tuple(int(round(float(x))) for x in origin)

        if strategy == "explicit":
            if explicit is None:
                raise RuntimeError("Explicit coordinates required for strategy 'explicit'")
            return tuple(int(round(float(x))) for x in explicit)

        if strategy == "random":
            if origin is None:
                raise RuntimeError("Origin required for strategy 'random'")
            base = tuple(int(round(float(x))) for x in origin)
            occupied = {item.position for item in self.active_items.values()}
            for _ in range(retries):
                dx = int(torch.randint(-1, 2, ()).item())
                dy = int(torch.randint(-1, 2, ()).item())
                candidate = (base[0] + dx, base[1] + dy)
                if candidate not in occupied:
                    return candidate
            raise RuntimeError("Failed to find free position for random spawn_item after retries")

        raise RuntimeError(f"Unsupported spawn strategy '{strategy}'")

    def _valid_position(self, position: tuple[int, ...]) -> bool:
        """Check position within grid bounds if grid_size known."""

        if self.grid_size is None:
            return True
        if len(position) != len(self.grid_size):
            return False
        return all(0 <= coord < dim for coord, dim in zip(position, self.grid_size))

    def _position_occupied(self, position: tuple[int, ...]) -> bool:
        """Check whether a position is occupied by an active item."""

        return any(item.position == position for item in self.active_items.values())

    def spawn_item(
        self,
        item_type: str,
        position: tuple[int, ...] | tuple[float, ...],
        current_tick: int,
        initial_state: dict[str, float] | None = None,
    ) -> ItemInstance | None:
        """Spawn new item instance.

        Args:
            item_type: Item type ID from catalog
            position: Spawn position (grid or continuous coords)
            current_tick: Current environment tick
            initial_state: Optional VFS state overrides (e.g., {"durability": 50.0})

        Returns:
            ItemInstance if spawned, None if at capacity or on cooldown
        """
        # Check max_items capacity
        if len(self.active_items) >= self.max_items:
            return None

        # Check cooldown
        if item_type in self.cooldown_until:
            if current_tick < self.cooldown_until[item_type]:
                return None  # Still on cooldown

        # Get item type definition
        item_def = next((t for t in self.catalog.item_types if t.id == item_type), None)
        if item_def is None:
            raise KeyError(f"Unknown item type: {item_type}")

        # Allocate VFS slot
        if not self.vfs_free_slots:
            return None  # No VFS slots available
        vfs_index = self.vfs_free_slots.pop()

        # Initialize item VFS state from profile defaults + initial_state overrides
        if self.vfs_registry is not None and item_def.vfs_profile:
            profile_name = item_def.vfs_profile

            # Get profile from registry
            if profile_name not in self.vfs_registry.item_profile_map:
                raise ValueError(f"VFS profile '{profile_name}' not found in registry")

            profile_map = self.vfs_registry.item_profile_map[profile_name]

            item_vfs = getattr(self.vfs_registry, "item_vfs", None)
            if item_vfs is None:
                raise ValueError("Item VFS storage not allocated in registry")

            # Get compiled profile to access initial_value defaults
            if hasattr(self.vfs_registry, "item_profiles") and self.vfs_registry.item_profiles:
                compiled_profile = self.vfs_registry.item_profiles.get(profile_name)
                if compiled_profile:
                    # Initialize with defaults from compiled profile
                    for compiled_var in compiled_profile.variables:
                        if compiled_var.initial_value is not None:
                            var_idx = profile_map[compiled_var.name]
                            item_vfs[vfs_index, var_idx] = float(compiled_var.initial_value)

            # Apply initial_state overrides if provided
            if initial_state is not None:
                for var_name, value in initial_state.items():
                    if var_name not in profile_map:
                        raise ValueError(f"Variable '{var_name}' not in profile '{profile_name}'")
                    var_idx = profile_map[var_name]
                    item_vfs[vfs_index, var_idx] = float(value)

        # Create instance
        instance = ItemInstance(
            item_type=item_type,
            instance_id=self.next_instance_id,
            position=position,
            vfs_index=vfs_index,
            vfs_profile=item_def.vfs_profile,  # Assign VFS profile from item type
            spawn_tick=current_tick,
            duration_total=item_def.duration,
            duration_remaining=item_def.duration,
        )
        self.next_instance_id += 1

        # Store in active items
        self.active_items[instance.instance_id] = instance

        # Register item instance in VFS registry
        if self.vfs_registry is not None and instance.vfs_profile:
            self.vfs_registry.register_item_instance(instance.vfs_index, instance.vfs_profile)

        return instance

    def lift_item(self, instance_id: int) -> ItemInstance | None:
        """Move item from world to held state (pickup).

        Preserves item identity and VFS state. Item continues to tick.

        Args:
            instance_id: Item instance ID

        Returns:
            ItemInstance if lifted, None if not found
        """
        if instance_id not in self.active_items:
            return None

        # Move from active to held (do NOT free VFS slot - item still exists)
        item = self.active_items.pop(instance_id)
        self.held_items[instance_id] = item

        return item

    def place_item(
        self,
        instance_id: int,
        position: tuple[int, ...],
    ) -> ItemInstance | None:
        """Move item from held state to world (drop).

        Preserves item identity and VFS state.

        Args:
            instance_id: Item instance ID
            position: Position to place item

        Returns:
            ItemInstance if placed, None if not found
        """
        if instance_id not in self.held_items:
            return None

        # Move from held to active
        item = self.held_items.pop(instance_id)
        item.position = position
        self.active_items[instance_id] = item

        return item

    def despawn_item(self, instance_id: int, current_tick: int) -> None:
        """Despawn item from world or held state.

        Args:
            instance_id: Item instance ID to despawn
            current_tick: Current tick (for cooldown tracking)
        """
        # Check active items first
        if instance_id in self.active_items:
            item = self.active_items.pop(instance_id)
        # Then check held items
        elif instance_id in self.held_items:
            item = self.held_items.pop(instance_id)
        else:
            return  # Item not found

        # Unregister item instance from VFS registry
        if self.vfs_registry is not None:
            self.vfs_registry.unregister_item_instance(item.vfs_index)

        # Cancel any scheduled delayed commands targeting this item
        if self.effect_manager is not None:
            self.effect_manager.cancel_scheduled_for_entity(scope="item", entity_id=item.vfs_index)

        # Free VFS slot
        self.vfs_free_slots.add(item.vfs_index)

        # Set cooldown if configured
        item_def = next(t for t in self.catalog.item_types if t.id == item.item_type)
        if item_def.cooldown is not None:
            self.cooldown_until[item.item_type] = current_tick + item_def.cooldown

        # Set respawn timer if configured in appearance config
        # Note: Timer is per item_type, not per instance. If multiple items
        # of the same type despawn, only the most recent despawn triggers respawn.
        if self.appearance_config is not None:
            # Find appearance rule for this item type
            rule = next(
                (r for r in self.appearance_config.items if r.item_type == item.item_type),
                None,
            )

            if rule is not None:
                schedule = getattr(rule, "schedule", None)

                if schedule is not None and isinstance(schedule, SpawnScheduleConfig):
                    if schedule.type == "periodic" and schedule.period is not None:
                        self.respawn_timers[item.item_type] = current_tick + schedule.period
                    elif schedule.type == "normal" and schedule.mean is not None and schedule.std_dev is not None:
                        next_tick = int(
                            max(
                                0.0,
                                torch.normal(
                                    mean=torch.tensor(schedule.mean),
                                    std=torch.tensor(schedule.std_dev),
                                ).item(),
                            )
                        )
                        self.respawn_timers[item.item_type] = next_tick
                    elif schedule.type == "poisson" and schedule.rate is not None and schedule.rate > 0:
                        self.respawn_timers[item.item_type] = current_tick + 1
                    elif schedule.type == "time_window":
                        if schedule.start_tick is not None and current_tick < schedule.start_tick:
                            self.respawn_timers[item.item_type] = schedule.start_tick
                        else:
                            self.respawn_timers[item.item_type] = current_tick + 1
                else:
                    # No schedule: do not queue respawns automatically
                    pass

    def tick(self, current_tick: int) -> None:
        """Advance all item lifecycles by one tick.

        Args:
            current_tick: Current environment tick
        """
        # Collect expired items from BOTH registries (BEFORE ticking)
        expired = []

        # Check active items (on grid)
        for instance_id, item in self.active_items.items():
            if item.is_expired():
                expired.append(instance_id)

        # Check held items (in inventories) - they also expire!
        for instance_id, item in self.held_items.items():
            if item.is_expired():
                expired.append(instance_id)

        # Despawn expired items
        for instance_id in expired:
            self.despawn_item(instance_id, current_tick)

        # Tick all remaining items in BOTH registries (AFTER despawning)
        for item in self.active_items.values():
            item.tick()

        for item in self.held_items.values():
            item.tick()

    def get_all_items(self) -> list[ItemInstance]:
        """Get all active items (for testing/debugging)."""
        return list(self.active_items.values())

    def _should_spawn_rule(
        self,
        rule: Any,
        *,
        bars: dict[str, torch.Tensor] | None,
        temporal: dict[str, torch.Tensor] | None,
        current_tick: int,
    ) -> bool:
        """Evaluate spawn predicate if provided."""

        if rule.when is None:
            return True

        if rule.when_ast is None:
            raise RuntimeError("Spawn condition provided without compiled AST. Run UniverseCompiler before using spawn conditions.")

        if bars is None:
            raise RuntimeError("Spawn conditions require bar context; pass bars when invoking spawn routines")

        vfs_state: dict[str, torch.Tensor] = {}
        if self.vfs_registry is not None:
            for var_id, _ in self.vfs_registry.variables.items():
                vfs_state[var_id] = self.vfs_registry._storage[var_id]

        temporal_context = temporal or {"tick": torch.tensor(current_tick, device=self.device)}

        context = ExprExecutionContext(
            bars=bars,
            vfs=vfs_state,
            affordances={},
            temporal=temporal_context,
            device=self.device,
        )

        evaluator = Evaluator(context)
        result = evaluator.evaluate(rule.when_ast)

        if isinstance(result, torch.Tensor):
            if result.numel() == 1:
                return bool(result.item())
            # Vectorized contexts emit per-agent tensors; require all agents to satisfy.
            return bool(torch.all(result).item())

        return bool(result)

    def _iter_positions(
        self,
        rule: Any,
        grid_size: tuple[int, ...],
        *,
        current_tick: int,
        count: int,
    ) -> list[tuple[int, ...]]:
        """Generate up to `count` positions for a spawn event based on placement config."""

        positions: list[tuple[int, ...]] = []
        placement = getattr(rule, "placement", None)
        placement_mode = placement.mode if isinstance(placement, SpawnPlacementConfig) else None

        if placement_mode is None or placement_mode == "random":
            for _ in range(count):
                positions.append(tuple(random.randint(0, size - 1) for size in grid_size))
            return positions

        if placement_mode == "fixed":
            for pos in placement.fixed_positions or []:
                if len(positions) >= count:
                    break
                if not self._valid_position(pos) or self._position_occupied(pos):
                    continue
                positions.append(pos)
            return positions

        if placement_mode == "grid":
            spacing = placement.grid_spacing or 1
            for x in range(0, grid_size[0], spacing):
                for y in range(0, grid_size[1], spacing):
                    if len(positions) >= count:
                        return positions
                    pos = (x, y)
                    if self._position_occupied(pos):
                        continue
                    positions.append(pos)
            return positions

        if placement_mode == "scripted":
            script = placement.script or []
            start_idx = self.script_indices.get(rule.item_type, 0)
            # Advance past events before current_tick
            while start_idx < len(script) and script[start_idx].get("tick") < current_tick:
                start_idx += 1
            for idx in range(start_idx, len(script)):
                if len(positions) >= count:
                    break
                event = script[idx]
                tick = event.get("tick")
                if tick is None or tick != current_tick:
                    break
                pos = tuple(event.get("position", ()))
                if not self._valid_position(pos) or self._position_occupied(pos):
                    continue
                positions.append(pos)
                start_idx = idx + 1
            self.script_indices[rule.item_type] = start_idx
            return positions

        return positions

    def _next_script_tick(self, rule: Any, current_tick: int) -> int | None:
        placement = getattr(rule, "placement", None)
        placement_mode = placement.mode if isinstance(placement, SpawnPlacementConfig) else None
        if placement_mode != "scripted":
            return None
        script = placement.script or []
        for event in script:
            tick = event.get("tick")
            if tick is not None and tick > current_tick:
                return int(tick)
        return None

    def _resolve_respawn_positions(self, rule: Any, *, current_tick: int, count: int) -> list[tuple[int, ...]]:
        """Resolve placement for respawns; honor count and scripted tick alignment."""

        placement = getattr(rule, "placement", None)
        placement_mode = placement.mode if isinstance(placement, SpawnPlacementConfig) else None

        positions: list[tuple[int, ...]] = []

        if placement_mode is None or placement_mode == "random":
            return [tuple(random.randint(0, size - 1) for size in self.grid_size or (1,)) for _ in range(count)]

        if placement_mode == "fixed":
            for pos in placement.fixed_positions or []:
                if len(positions) >= count:
                    break
                if self._valid_position(pos) and not self._position_occupied(pos):
                    positions.append(pos)
            return positions

        if placement_mode == "grid":
            spacing = placement.grid_spacing or 1
            grid_size = self.grid_size or (0,)
            for x in range(0, grid_size[0], spacing):
                for y in range(0, grid_size[1], spacing):
                    if len(positions) >= count:
                        return positions
                    pos = (x, y)
                    if self._position_occupied(pos):
                        continue
                    positions.append(pos)
            return positions

        if placement_mode == "scripted":
            script = placement.script or []
            start_idx = self.script_indices.get(rule.item_type, 0)
            # Advance past events before current_tick
            while start_idx < len(script) and script[start_idx].get("tick") < current_tick:
                start_idx += 1
            for idx in range(start_idx, len(script)):
                if len(positions) >= count:
                    break
                event = script[idx]
                tick = event.get("tick")
                if tick is None or tick != current_tick:
                    break
                pos = tuple(event.get("position", ()))
                if not self._valid_position(pos) or self._position_occupied(pos):
                    continue
                positions.append(pos)
                start_idx = idx + 1
            self.script_indices[rule.item_type] = start_idx
            return positions

        return positions

    def _schedule_allows_spawn(self, rule: Any, current_tick: int) -> bool:
        """Check advanced schedule gating (time_window, poisson, normal)."""

        schedule = getattr(rule, "schedule", None)
        if schedule is None or not isinstance(schedule, SpawnScheduleConfig):
            return True

        if schedule.type == "time_window":
            if schedule.start_tick is not None and current_tick < schedule.start_tick:
                return False
            if schedule.end_tick is not None and current_tick > schedule.end_tick:
                return False
            return True

        if schedule.type == "poisson":
            rate = schedule.rate or 0.0
            if rate <= 0.0:
                return False
            prob = 1.0 - torch.exp(torch.tensor(-rate))
            if prob >= 0.9999:
                return True
            return bool(torch.rand((), device=self.device) < prob)

        if schedule.type == "normal":
            next_tick = self.next_scheduled_tick.get(rule.item_type)
            if next_tick is None:
                next_tick = current_tick + 1
                self.next_scheduled_tick[rule.item_type] = next_tick
            if current_tick < next_tick:
                return False
            # Schedule next window based on mean (deterministic cadence)
            mean_tick = schedule.mean or 1.0
            self.next_scheduled_tick[rule.item_type] = int(max(current_tick + 1, math.ceil(mean_tick)))
            return True

        # periodic handled via timers, default allow here
        return True

    def spawn_initial_items(
        self,
        appearance_config: ItemsAppearanceConfig,
        grid_size: tuple[int, ...],
        current_tick: int,
        *,
        bars: dict[str, torch.Tensor] | None = None,
        temporal: dict[str, torch.Tensor] | None = None,
    ) -> None:
        """Spawn items at level start based on ItemsAppearanceConfig.

        Args:
            appearance_config: Level-specific item spawn rules
            grid_size: Grid dimensions (e.g., (7, 7) for 7x7 grid)
            current_tick: Current environment tick
        """
        # Store config for periodic respawning
        self.set_appearance_config(appearance_config, grid_size)

        for rule in appearance_config.items:
            # Validate item type exists in catalog
            if not any(t.id == rule.item_type for t in self.catalog.item_types):
                # Skip unknown item types (e.g., energy_drink in test config)
                continue
            rule_key = getattr(rule, "_rule_key", f"rule_{id(rule)}")

            if not self._schedule_allows_spawn(rule, current_tick=current_tick):
                continue

            if not self._should_spawn_rule(rule, bars=bars, temporal=temporal, current_tick=current_tick):
                continue

            count = rule.spawn_count if rule.spawn_count is not None else 1
            if count <= 0:
                continue
            positions = self._iter_positions(rule, grid_size, current_tick=current_tick, count=count)
            current_total = self.rule_spawn_counts.get(rule_key, 0)
            for position in positions:
                max_total = getattr(rule, "max_total", None)
                if max_total is not None and current_total >= max_total:
                    continue
                self.spawn_item(rule.item_type, position, current_tick)
                current_total += 1
                self.rule_spawn_counts[rule_key] = current_total

    def set_appearance_config(
        self,
        appearance_config: ItemsAppearanceConfig,
        grid_size: tuple[int, ...],
    ) -> None:
        """Store appearance config for periodic respawning.

        Args:
            appearance_config: Level-specific item spawn rules
            grid_size: Grid dimensions for random position generation
        """
        self.appearance_config = appearance_config
        self.grid_size = grid_size
        # Reset spawn counts when a new appearance config is applied
        self.rule_spawn_counts.clear()
        self.next_scheduled_tick.clear()
        self.script_indices.clear()
        for idx, rule in enumerate(appearance_config.items):
            rule_key = f"rule_{idx}_{rule.item_type}"
            setattr(rule, "_rule_key", rule_key)
            self.rule_spawn_counts[rule_key] = 0

    def process_respawns(
        self,
        current_tick: int,
        *,
        bars: dict[str, torch.Tensor] | None = None,
        temporal: dict[str, torch.Tensor] | None = None,
    ) -> None:
        """Process periodic item respawning based on timers.

        Args:
            current_tick: Current environment tick
        """
        if self.appearance_config is None or self.grid_size is None:
            return  # No appearance config, no respawning

        expired_types = [item_type for item_type, respawn_tick in self.respawn_timers.items() if current_tick >= respawn_tick]

        # Attempt to spawn each expired type
        for item_type in expired_types:
            # Find appearance rule for this item type
            rule = next(
                (r for r in self.appearance_config.items if r.item_type == item_type),
                None,
            )

            if rule is None:
                # Rule removed from config, clear timer
                del self.respawn_timers[item_type]
                continue
            rule_key = getattr(rule, "_rule_key", f"rule_{id(rule)}")

            if not self._schedule_allows_spawn(rule, current_tick=current_tick):
                # Reschedule according to schedule type
                schedule = getattr(rule, "schedule", None)
                if schedule and isinstance(schedule, SpawnScheduleConfig):
                    if schedule.type == "poisson" and schedule.rate and schedule.rate > 0:
                        self.respawn_timers[item_type] = current_tick + 1
                    elif schedule.type == "time_window":
                        if schedule.end_tick is not None and current_tick > schedule.end_tick:
                            del self.respawn_timers[item_type]
                        else:
                            next_tick = max(current_tick + 1, schedule.start_tick or current_tick + 1)
                            self.respawn_timers[item_type] = next_tick
                    elif schedule.type == "normal" and schedule.mean is not None and schedule.std_dev is not None:
                        sampled = torch.normal(
                            mean=torch.tensor(schedule.mean),
                            std=torch.tensor(schedule.std_dev),
                        ).item()
                        next_tick_int = int(max(current_tick + 1, math.ceil(sampled)))
                        self.respawn_timers[item_type] = next_tick_int
                continue

            if not self._should_spawn_rule(rule, bars=bars, temporal=temporal, current_tick=current_tick):
                continue

            max_total = getattr(rule, "max_total", None)
            current_total = self.rule_spawn_counts.get(rule_key, 0)
            if max_total is not None and current_total >= max_total:
                continue

            count = getattr(rule, "spawn_count", 1)
            if count is None:
                count = 1
            if count <= 0:
                del self.respawn_timers[item_type]
                continue
            positions = self._resolve_respawn_positions(rule, current_tick=current_tick, count=count)
            spawned_any = False
            for position in positions:
                spawned = self.spawn_item(item_type, position, current_tick)
                if spawned is not None:
                    spawned_any = True
                    self.rule_spawn_counts[rule_key] = current_total + 1
                    break  # respawn one per timer

            schedule = getattr(rule, "schedule", None)
            if spawned_any:
                placement = getattr(rule, "placement", None)
                placement_mode = placement.mode if isinstance(placement, SpawnPlacementConfig) else None
                if placement_mode == "scripted":
                    next_script_tick = self._next_script_tick(rule, current_tick)
                    if next_script_tick is not None:
                        self.respawn_timers[item_type] = next_script_tick
                    else:
                        del self.respawn_timers[item_type]
                else:
                    del self.respawn_timers[item_type]
            else:
                # Reschedule retry
                if schedule and isinstance(schedule, SpawnScheduleConfig):
                    if schedule.type == "poisson" and schedule.rate and schedule.rate > 0:
                        self.respawn_timers[item_type] = current_tick + 1
                    elif schedule.type == "time_window":
                        next_tick = max(current_tick + 1, schedule.start_tick or current_tick + 1)
                        self.respawn_timers[item_type] = next_tick
                    elif schedule.type == "normal" and schedule.mean is not None:
                        next_tick_int = self.next_scheduled_tick.get(item_type, current_tick + 1)
                        self.respawn_timers[item_type] = next_tick_int
