"""ItemManager for spawning/despawning items and managing lifecycle."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig

from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode
from townlet.items.instance import ItemInstance

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
    ) -> None:
        """Initialize ItemManager.

        Args:
            catalog: Items catalog from items.yaml
            max_items: Maximum items that can exist simultaneously
            device: PyTorch device
            schema: Variable type schema for Effects compilation
        """
        self.catalog = catalog
        self.max_items = max_items
        self.device = torch.device(device) if isinstance(device, str) else device

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

    def spawn_item(
        self,
        item_type: str,
        position: tuple[int, ...] | tuple[float, ...],
        current_tick: int,
    ) -> ItemInstance | None:
        """Spawn new item instance.

        Args:
            item_type: Item type ID from catalog
            position: Spawn position (grid or continuous coords)
            current_tick: Current environment tick

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

        # Create instance
        instance = ItemInstance(
            item_type=item_type,
            instance_id=self.next_instance_id,
            position=position,
            vfs_index=vfs_index,
            spawn_tick=current_tick,
            duration_total=item_def.duration,
            duration_remaining=item_def.duration,
        )
        self.next_instance_id += 1

        # Store in active items
        self.active_items[instance.instance_id] = instance

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

            if rule is not None and rule.spawn_interval is not None:
                # Schedule respawn
                self.respawn_timers[item.item_type] = current_tick + rule.spawn_interval

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

    def spawn_initial_items(
        self,
        appearance_config: ItemsAppearanceConfig,
        grid_size: tuple[int, ...],
        current_tick: int,
    ) -> None:
        """Spawn items at level start based on ItemsAppearanceConfig.

        Args:
            appearance_config: Level-specific item spawn rules
            grid_size: Grid dimensions (e.g., (7, 7) for 7x7 grid)
            current_tick: Current environment tick
        """
        for rule in appearance_config.items:
            # Validate item type exists in catalog
            if not any(t.id == rule.item_type for t in self.catalog.item_types):
                # Skip unknown item types (e.g., energy_drink in test config)
                continue

            # Spawn count items
            for _ in range(rule.spawn_count):
                # Generate random position within grid bounds
                if rule.spawn_position == "random":
                    position = tuple(random.randint(0, size - 1) for size in grid_size)
                else:
                    # TODO: Support fixed positions when needed
                    position = tuple(random.randint(0, size - 1) for size in grid_size)

                # Attempt spawn (may fail if at capacity)
                self.spawn_item(rule.item_type, position, current_tick)

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
