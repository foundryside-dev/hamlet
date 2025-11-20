"""ItemManager for spawning/despawning items and managing lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from townlet.config.items_config import ItemsCatalogConfig

from townlet.items.instance import ItemInstance

__all__ = ["ItemManager"]


class ItemManager:
    """Manages all items in the world."""

    def __init__(
        self,
        catalog: ItemsCatalogConfig,
        max_items: int,
        device: str = "cpu",
    ) -> None:
        """Initialize ItemManager.

        Args:
            catalog: Items catalog from items.yaml
            max_items: Maximum items that can exist simultaneously
            device: PyTorch device
        """
        self.catalog = catalog
        self.max_items = max_items
        self.device = device

        self.next_instance_id = 0
        self.active_items: dict[int, ItemInstance] = {}  # instance_id -> ItemInstance

        # VFS slot allocation (fixed-size pool)
        self.vfs_free_slots: set[int] = set(range(max_items))  # Available VFS indices

        # Cooldown tracking (item_type -> tick when can spawn again)
        self.cooldown_until: dict[str, int] = {}

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

    def despawn_item(self, instance_id: int, current_tick: int) -> None:
        """Despawn item and free VFS slot.

        Args:
            instance_id: Item instance ID to despawn
            current_tick: Current tick (for cooldown tracking)
        """
        if instance_id not in self.active_items:
            return

        item = self.active_items[instance_id]

        # Free VFS slot
        self.vfs_free_slots.add(item.vfs_index)

        # Set cooldown if configured
        item_def = next(t for t in self.catalog.item_types if t.id == item.item_type)
        if item_def.cooldown is not None:
            self.cooldown_until[item.item_type] = current_tick + item_def.cooldown

        # Remove from active items
        del self.active_items[instance_id]

    def tick(self, current_tick: int) -> None:
        """Advance all item lifecycles by one tick.

        Args:
            current_tick: Current environment tick
        """
        # Collect expired items (BEFORE ticking - expired items don't tick)
        expired = [instance_id for instance_id, item in self.active_items.items() if item.is_expired()]

        # Despawn expired items
        for instance_id in expired:
            self.despawn_item(instance_id, current_tick)

        # Tick all remaining items (AFTER despawning)
        for item in self.active_items.values():
            item.tick()

    def get_all_items(self) -> list[ItemInstance]:
        """Get all active items (for testing/debugging)."""
        return list(self.active_items.values())
