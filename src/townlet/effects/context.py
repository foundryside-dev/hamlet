"""Execution context for effect command evaluation."""

from __future__ import annotations

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


class ExecutionContext:
    """Runtime context for effect command execution.

    Provides access to:
    - bars: Meter tensors (energy, health, etc.)
    - vfs: VFS variable registry
    - self: Current agent/item index
    - target: Target agent/item index
    - effect_manager: EffectManager for spawning effects (NEW)
    - item_manager: ItemManager for spawning items (NEW)
    - current_tick: Current environment tick (NEW)
    """

    def __init__(
        self,
        bars: dict[str, torch.Tensor],
        vfs_registry: VariableRegistry,
        self_index: int | None,
        target_index: int | None,
        effect: Any | None = None,
        self_is_item: bool = False,  # NEW: Track if self refers to item
        effect_manager: Any | None = None,  # REQUIRED
        item_manager: Any | None = None,  # REQUIRED
        spawn_depth: int = 0,  # NEW (cascade depth tracking)
        agent_positions: torch.Tensor | None = None,  # NEW: [batch, 2] spatial positions
        interrupt_reason: str | None = None,  # NEW: Why effect was interrupted
        current_tick: int = 0,  # NEW
        target_is_item: bool = False,  # NEW: mark target as item for vfs routing
    ):
        if effect_manager is None:
            effect_manager = _NullEffectManager()
        if item_manager is None:
            item_manager = _NullItemManager()

        self.bars = bars or {}
        self.vfs_registry = vfs_registry
        self.self_index = self_index
        self.target_index = target_index
        self.effect = effect  # ActiveEffect instance for effect-specific variables
        self.self_is_item = self_is_item  # NEW
        self.effect_manager = effect_manager  # NEW
        self.item_manager = item_manager  # NEW
        self.spawn_depth = spawn_depth  # NEW
        self.agent_positions = agent_positions  # NEW
        self.interrupt_reason = interrupt_reason  # NEW
        self.current_tick = current_tick  # NEW
        self.target_is_item = target_is_item  # NEW

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
