"""Items system for HAMLET.

Provides world objects with VFS state, inventory mechanics, and Effects-based interactions.
"""

from townlet.items.action_handlers import ItemActionHandler
from townlet.items.instance import ItemInstance
from townlet.items.inventory import InventoryState
from townlet.items.manager import ItemManager

__all__ = [
    "ItemActionHandler",
    "ItemInstance",
    "ItemManager",
    "InventoryState",
]
