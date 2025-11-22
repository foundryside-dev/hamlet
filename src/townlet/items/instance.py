"""ItemInstance dataclass for runtime item state."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ItemInstance"]


@dataclass
class ItemInstance:
    """Runtime instance of an item in the world.

    Tracks position, VFS state index, lifecycle timers.
    """

    name: str | None
    icon: str | None
    tags: tuple[str, ...]

    item_type: str  # Reference to ItemTypeConfig.id
    instance_id: int  # Unique instance ID (incrementing counter)
    position: tuple[int, ...] | tuple[float, ...]  # Spatial position (grid or continuous)
    vfs_index: int  # Index into item_vfs tensor ([max_items, num_profiles])
    vfs_profile: str  # VFS profile name (e.g., "food_stats", "weapon_stats")

    spawn_tick: int  # When item was spawned
    duration_total: int | None  # Total lifetime (None = permanent)
    duration_remaining: int | None  # Ticks until despawn (None = permanent)
    holder_agent_id: int | None = None  # Agent holding the item (None when on ground)

    def tick(self) -> None:
        """Advance lifecycle by one tick."""
        if self.duration_remaining is not None:
            self.duration_remaining -= 1

    def is_expired(self) -> bool:
        """Check if item should despawn."""
        return self.duration_remaining is not None and self.duration_remaining <= 0
