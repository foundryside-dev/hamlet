"""
Tests for primitive type system.

RED phase: These tests define the interface before implementation.
"""

import torch

from townlet.world.types.primitive import (
    BoolType,
    ScalarType,
    Vec2Type,
    Vec3Type,
    Vec4Type,
)


class TestScalarType:
    """Test scalar (float) type."""

    def test_validate_valid(self):
        """Scalar accepts float tensors."""
        scalar = ScalarType()
        tensor = torch.tensor([1.0, 2.5, -3.14])
        assert scalar.validate(tensor) is True

    def test_validate_invalid_dtype(self):
        """Scalar rejects non-float tensors."""
        scalar = ScalarType()
        tensor = torch.tensor([1, 2, 3], dtype=torch.int64)
        assert scalar.validate(tensor) is False

    def test_validate_invalid_shape(self):
        """Scalar rejects multi-dimensional tensors."""
        scalar = ScalarType()
        tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        assert scalar.validate(tensor) is False


class TestBoolType:
    """Test boolean type."""

    def test_validate_valid(self):
        """Bool accepts bool tensors."""
        bool_type = BoolType()
        tensor = torch.tensor([True, False, True], dtype=torch.bool)
        assert bool_type.validate(tensor) is True

    def test_validate_invalid_dtype(self):
        """Bool rejects non-bool tensors."""
        bool_type = BoolType()
        tensor = torch.tensor([1.0, 0.0, 1.0])
        assert bool_type.validate(tensor) is False


class TestVec2Type:
    """Test 2D vector type."""

    def test_validate_valid(self):
        """Vec2 accepts shape (batch_size, 2) float tensors."""
        vec2 = Vec2Type()
        tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        assert vec2.validate(tensor) is True

    def test_validate_invalid_shape(self):
        """Vec2 rejects tensors with wrong second dimension."""
        vec2 = Vec2Type()
        tensor = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        assert vec2.validate(tensor) is False

    def test_validate_invalid_dtype(self):
        """Vec2 rejects non-float tensors."""
        vec2 = Vec2Type()
        tensor = torch.tensor([[1, 2], [3, 4]], dtype=torch.int64)
        assert vec2.validate(tensor) is False


class TestVec3Type:
    """Test 3D vector type."""

    def test_validate_valid(self):
        """Vec3 accepts shape (batch_size, 3) float tensors."""
        vec3 = Vec3Type()
        tensor = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        assert vec3.validate(tensor) is True

    def test_validate_invalid_shape(self):
        """Vec3 rejects tensors with wrong second dimension."""
        vec3 = Vec3Type()
        tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        assert vec3.validate(tensor) is False


class TestVec4Type:
    """Test 4D vector type."""

    def test_validate_valid(self):
        """Vec4 accepts shape (batch_size, 4) float tensors."""
        vec4 = Vec4Type()
        tensor = torch.tensor([[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]])
        assert vec4.validate(tensor) is True

    def test_validate_invalid_shape(self):
        """Vec4 rejects tensors with wrong second dimension."""
        vec4 = Vec4Type()
        tensor = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        assert vec4.validate(tensor) is False
