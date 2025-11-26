"""
Primitive type system for Townlet World Model.

Provides basic type validators for scalar, bool, and vector types.
All types validate GPU tensors with batch dimensions.
"""

from typing import Protocol

import torch


class Type(Protocol):
    """Protocol for type validators.

    All type validators must implement validate() method.
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate tensor against type constraints.

        Args:
            tensor: GPU tensor to validate

        Returns:
            True if tensor matches type constraints, False otherwise
        """
        ...


class ScalarType:
    """Scalar (float) type.

    Validates:
    - dtype: torch.float32
    - shape: (batch_size,) - 1D tensor
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate scalar tensor.

        Args:
            tensor: Tensor to validate

        Returns:
            True if tensor is 1D float tensor
        """
        return tensor.dtype == torch.float32 and tensor.ndim == 1


class BoolType:
    """Boolean type.

    Validates:
    - dtype: torch.bool
    - shape: (batch_size,) - 1D tensor
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate bool tensor.

        Args:
            tensor: Tensor to validate

        Returns:
            True if tensor is 1D bool tensor
        """
        return tensor.dtype == torch.bool and tensor.ndim == 1


class Vec2Type:
    """2D vector type.

    Validates:
    - dtype: torch.float32
    - shape: (batch_size, 2)
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate 2D vector tensor.

        Args:
            tensor: Tensor to validate

        Returns:
            True if tensor is (batch_size, 2) float tensor
        """
        return tensor.dtype == torch.float32 and tensor.ndim == 2 and tensor.shape[1] == 2


class Vec3Type:
    """3D vector type.

    Validates:
    - dtype: torch.float32
    - shape: (batch_size, 3)
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate 3D vector tensor.

        Args:
            tensor: Tensor to validate

        Returns:
            True if tensor is (batch_size, 3) float tensor
        """
        return tensor.dtype == torch.float32 and tensor.ndim == 2 and tensor.shape[1] == 3


class Vec4Type:
    """4D vector type.

    Validates:
    - dtype: torch.float32
    - shape: (batch_size, 4)
    """

    def validate(self, tensor: torch.Tensor) -> bool:
        """Validate 4D vector tensor.

        Args:
            tensor: Tensor to validate

        Returns:
            True if tensor is (batch_size, 4) float tensor
        """
        return tensor.dtype == torch.float32 and tensor.ndim == 2 and tensor.shape[1] == 4
