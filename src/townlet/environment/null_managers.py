"""Null object pattern implementations for optional subsystems.

These classes provide fail-forward behavior when optional subsystems
(like items) are not configured. They raise explicit errors on operations
that shouldn't be called when the subsystem is disabled, preventing
silent failures.
"""

import logging
from typing import Any

_logger = logging.getLogger(__name__)


class NullItemManager:
    """Null object pattern for item management when items are disabled.

    This class is used when the item system is explicitly not configured.
    It provides no-op implementations for lifecycle methods (tick, process_respawns)
    and raises explicit errors for operations that require items to be configured
    (spawn_item).

    Usage:
        If items are not configured:
            item_manager = NullItemManager()
        else:
            item_manager = RealItemManager(...)

        # Safe to call - returns None
        item_manager.tick(meters)
        item_manager.process_respawns(positions)

        # Raises RuntimeError if items not configured
        item_manager.spawn_item(...)  # Only call if items are configured

    Note:
        This consolidates duplicate implementations from vectorized_env.py and
        affordance_engine.py (ENV-009).
    """

    def spawn_item(self, *args: Any, **kwargs: Any) -> None:
        """Attempt to spawn an item - raises when items are disabled.

        Raises:
            RuntimeError: Always, since items are not configured
        """
        raise RuntimeError(
            "ItemManager is not configured; spawn_item is unavailable. " "Configure items in the universe config to enable item spawning."
        )

    def tick(self, *args: Any, **kwargs: Any) -> None:
        """Lifecycle tick - no-op when items are disabled.

        Returns:
            None - items are disabled, nothing to tick
        """
        _logger.debug("NullItemManager.tick() called - items disabled, skipping")
        return None

    def process_respawns(self, *args: Any, **kwargs: Any) -> None:
        """Process item respawns - no-op when items are disabled.

        Returns:
            None - items are disabled, nothing to respawn
        """
        _logger.debug("NullItemManager.process_respawns() called - items disabled, skipping")
        return None
