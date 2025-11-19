"""Execution context for effect command evaluation."""

from __future__ import annotations

import torch

from townlet.vfs.registry import ScopedVariableRegistry

__all__ = ["ExecutionContext"]


class ExecutionContext:
    """Runtime context for effect command execution.

    Provides access to:
    - bars: Meter tensors (energy, health, etc.)
    - vfs: VFS variable registry
    - self: Current agent/item index
    - target: Target agent/item index
    """

    def __init__(
        self,
        bars: dict[str, torch.Tensor] | None,
        vfs_registry: ScopedVariableRegistry | None,
        self_index: int | None,
        target_index: int | None,
    ):
        self.bars = bars or {}
        self.vfs_registry = vfs_registry
        self.self_index = self_index
        self.target_index = target_index

    def get_path(self, path: str) -> torch.Tensor:
        """Resolve path to tensor value.

        Args:
            path: Dot-separated path (e.g., "bar.energy", "vfs.motivation", "target.bar.health")

        Returns:
            Tensor value at path

        Raises:
            KeyError: If path not found
        """
        # Handle target. prefix
        if path.startswith("target."):
            if self.target_index is None:
                raise ValueError("target_index not set in context")

            # Resolve rest of path and index into target
            rest = path[len("target.") :]
            tensor = self.get_path(rest)

            # If batched tensor, index into it
            if tensor.dim() > 0:
                return tensor[self.target_index]
            return tensor

        # Handle self. prefix
        if path.startswith("self."):
            if self.self_index is None:
                raise ValueError("self_index not set in context")

            rest = path[len("self.") :]
            tensor = self.get_path(rest)

            if tensor.dim() > 0:
                return tensor[self.self_index]
            return tensor

        # Handle bar.* paths
        if path.startswith("bar."):
            bar_name = path[len("bar.") :]
            if bar_name not in self.bars:
                raise KeyError(f"Bar '{bar_name}' not found. Available: {list(self.bars.keys())}")
            return self.bars[bar_name]

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path[len("vfs.") :]

            # Try global scope first
            if var_name in self.vfs_registry.list_global():
                return self.vfs_registry.get_global(var_name)

            # Try agent scope
            if var_name in self.vfs_registry.list_agent():
                return self.vfs_registry.get_agent(var_name)

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")

    def set_path(self, path: str, value: torch.Tensor):
        """Set path to new tensor value (mutation).

        Args:
            path: Dot-separated path
            value: New tensor value
        """
        # Handle target. prefix
        if path.startswith("target."):
            if self.target_index is None:
                raise ValueError("target_index not set in context")

            rest = path[len("target.") :]
            # Get original tensor and mutate in-place
            original = self.get_path(rest)
            if original.dim() > 0:
                original[self.target_index] = value
            else:
                # Scalar case - need to replace
                self.set_path(rest, value)
            return

        # Handle bar.* paths
        if path.startswith("bar."):
            bar_name = path[len("bar.") :]
            if bar_name not in self.bars:
                raise KeyError(f"Bar '{bar_name}' not found")
            self.bars[bar_name] = value
            return

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path[len("vfs.") :]

            # Try global scope
            if var_name in self.vfs_registry.list_global():
                self.vfs_registry.set_global(var_name, value)
                return

            # Try agent scope
            if var_name in self.vfs_registry.list_agent():
                self.vfs_registry.set_agent(var_name, value)
                return

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")
