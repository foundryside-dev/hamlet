"""Items system for HAMLET.

Provides world objects with VFS state, inventory mechanics, and Effects-based interactions.
"""

from townlet.items.instance import ItemInstance
from townlet.items.manager import ItemManager

__all__ = [
    "ItemInstance",
    "ItemManager",
]
