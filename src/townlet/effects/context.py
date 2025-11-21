"""Execution context for effect command evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import torch

from townlet.vfs.registry import VariableRegistry

__all__ = ["ExecutionContext"]


class _NullEffectManager:
    def spawn_effect(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise RuntimeError("EffectManager is not configured; spawn_effect unavailable")


class _NullItemManager:
    def spawn_item(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise RuntimeError("ItemManager is not configured; spawn_item unavailable")


@dataclass
class ExecutionContext:
    """Runtime context for effect command execution."""

    bars: dict[str, torch.Tensor] = field(default_factory=dict)
    vfs_registry: VariableRegistry | None = None
    self_index: int | None = None
    target_index: int | None = None
    effect: Any | None = None
    self_is_item: bool = False
    effect_manager: Any | None = None
    item_manager: Any | None = None
    spawn_depth: int = 0
    agent_positions: torch.Tensor | None = None
    interrupt_reason: str | None = None
    current_tick: int = 0
    target_is_item: bool = False
    iterator_value: Any | None = None
    inventory: Any | None = None
    scheduler: Any | None = None  # Scheduler for delay commands

    def __post_init__(self) -> None:
        if self.effect_manager is None:
            self.effect_manager = _NullEffectManager()
        if self.item_manager is None:
            self.item_manager = _NullItemManager()
        if self.bars is None:
            self.bars = {}

    def copy(self, **overrides: Any) -> ExecutionContext:
        """Shallow copy with field overrides for child contexts."""

        return replace(self, **overrides)

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
            # Special handling when target refers to an item VFS
            if rest.startswith("vfs.") and self.target_is_item:
                from townlet.vfs.schema import VariableScope

                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                value = self.vfs_registry.read(
                    var_name,
                    context_index=self.target_index,
                    scope=VariableScope.ITEM,
                )
                if not isinstance(value, torch.Tensor):
                    value = torch.tensor(value, dtype=torch.float32)
                return value

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

            # NEW: Special handling for self.vfs.* when self is an item
            if rest.startswith("vfs.") and self.self_is_item:
                from townlet.vfs.schema import VariableScope

                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                value = self.vfs_registry.read(
                    var_name,
                    context_index=self.self_index,
                    scope=VariableScope.ITEM,
                )
                # Convert to tensor if needed
                if not isinstance(value, torch.Tensor):
                    value = torch.tensor(value, dtype=torch.float32)
                return value

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

            # VariableRegistry API compatibility
            if var_name in self.vfs_registry.variables:
                return self.vfs_registry.get(var_name, reader="engine")

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")

    def set_path(self, path: str, value: torch.Tensor) -> None:
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
            # Item target VFS handling
            if rest.startswith("vfs.") and self.target_is_item:
                from townlet.vfs.schema import VariableScope

                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                write_value = value.item() if isinstance(value, torch.Tensor) and value.numel() == 1 else value
                self.vfs_registry.write(
                    var_name,
                    write_value,
                    context_index=self.target_index,
                    scope=VariableScope.ITEM,
                )
                return

            original = self.get_path(rest)
            if original.dim() > 0:
                original[self.target_index] = value
            else:
                # Scalar case - need to replace
                self.set_path(rest, value)
            return

        # NEW: Handle self. prefix with special logic for items
        if path.startswith("self."):
            if self.self_index is None:
                raise ValueError("self_index not set in context")

            rest = path[len("self.") :]

            # NEW: Special handling for self.vfs.* when self is an item
            if rest.startswith("vfs.") and self.self_is_item:
                from townlet.vfs.schema import VariableScope

                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                # Convert value to Python float if it's a tensor (VFS registry.write() accepts both)
                write_value = value.item() if isinstance(value, torch.Tensor) and value.numel() == 1 else value
                self.vfs_registry.write(
                    var_name,
                    write_value,
                    context_index=self.self_index,
                    scope=VariableScope.ITEM,
                )
                return

            # Default: Get original tensor and mutate in-place
            original = self.get_path(rest)
            if original.dim() > 0:
                original[self.self_index] = value
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

            # VariableRegistry API compatibility
            if var_name in self.vfs_registry.variables:
                self.vfs_registry.set(var_name, value, writer="engine")
                return

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")
