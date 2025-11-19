"""
Type system for Townlet World Model.

Provides type validators for GPU tensors with batch dimensions.
"""

from townlet.world.types.primitive import (
    BoolType,
    ScalarType,
    Type,
    Vec2Type,
    Vec3Type,
    Vec4Type,
)

__all__ = [
    "Type",
    "ScalarType",
    "BoolType",
    "Vec2Type",
    "Vec3Type",
    "Vec4Type",
]
