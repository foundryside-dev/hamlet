"""Execution context for effect command evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableScope

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
    rng: torch.Generator | None = None
    seed: int | None = None  # Optional deterministic seed for sampling
    affordance_overrides: dict[str, bool] | None = None  # Runtime affordance availability overrides
    meter_dynamics: Any | None = None  # Optional MeterDynamics for trigger_cascade

    def __post_init__(self) -> None:
        if self.effect_manager is None:
            self.effect_manager = _NullEffectManager()
        if self.item_manager is None:
            self.item_manager = _NullItemManager()
        if self.bars is None:
            self.bars = {}
        if self.affordance_overrides is None:
            self.affordance_overrides = {}

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

            rest = path[len("target.") :]
            if rest.startswith("vfs."):
                segments = rest.split(".")[1:]
                if self.target_is_item:
                    return self._resolve_vfs_path(scope="item", index=self.target_index, segments=segments)
                tensor = self._resolve_vfs_path(
                    scope="agent",
                    index=None,  # keep batch for non-reference paths
                    segments=segments,
                    default_index=self.target_index,
                )
                if tensor.dim() > 0:
                    return tensor[self.target_index]
                return tensor
            if rest.startswith("bar."):
                bar_name = rest[len("bar.") :]
                if bar_name not in self.bars:
                    raise KeyError(f"Bar '{bar_name}' not found. Available: {list(self.bars.keys())}")
                bar_tensor = self.bars[bar_name]
                if bar_tensor.dim() == 0:
                    return bar_tensor
                return bar_tensor[self.target_index]

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

        # Handle affordance availability
        if path.startswith("affordance.") and path.endswith(".available"):
            parts = path.split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid affordance path: {path}")
            aff_name = parts[1]
            available = True if self.affordance_overrides is None else self.affordance_overrides.get(aff_name, True)
            return torch.tensor(bool(available), device=self.bars[next(iter(self.bars))].device if self.bars else torch.device("cpu"))

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")
            segments = path.split(".")[1:]  # drop leading "vfs"
            # Keep batched tensors for bare vfs.* paths; callers (target./self.) index as needed.
            return self._resolve_vfs_path(scope="agent", index=None, segments=segments)

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

            if rest.startswith("vfs."):
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                segments = rest.split(".")[1:]
                var_name = segments[0]
                if len(segments) > 1:
                    raise ValueError(f"Setting target reference traversal '{rest}' is not supported.")
                self._write_agent_vfs_value(var_name, self.target_index, value)
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

            if rest.startswith("vfs."):
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                segments = rest.split(".")[1:]
                var_name = segments[0]
                if len(segments) > 1:
                    raise ValueError(f"Setting reference traversal '{rest}' is not supported.")
                self._write_agent_vfs_value(var_name, self.self_index, value)
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

        # Handle affordance availability overrides
        if path.startswith("affordance.") and path.endswith(".available"):
            parts = path.split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid affordance path: {path}")
            aff_name = parts[1]
            if self.affordance_overrides is None:
                self.affordance_overrides = {}
            scalar_value: bool
            if isinstance(value, torch.Tensor):
                scalar_value = bool(value.item())
            else:
                scalar_value = bool(value)
            self.affordance_overrides[aff_name] = scalar_value
            return

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path[len("vfs.") :]

            if var_name in self.vfs_registry.variables:
                self.vfs_registry.set(var_name, value, writer="engine")
                return

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")

    def _resolve_vfs_path(self, scope: str, index: int | None, segments: list[str], *, default_index: int | None = None) -> torch.Tensor:
        """Traverse VFS paths, including reference types."""
        if not segments:
            raise ValueError("VFS path must include a variable name")

        var_name = segments[0]
        var_type = self._lookup_variable_type(scope, index, var_name)
        ref_traversal = var_type in ("agent_ref", "item_ref")
        read_index = index
        if ref_traversal and read_index is None and scope != "global":
            # Use the supplied default index (target/self) as the starting point for reference traversal.
            read_index = default_index if default_index is not None else self.self_index
            if read_index is None:
                raise ValueError("VFS reference traversal requires an index (self_index missing).")
        allow_batch = not ref_traversal and index is None
        value = self._read_vfs_value(scope, read_index, var_name, allow_batch=allow_batch)

        # No further traversal
        if len(segments) == 1:
            if isinstance(value, torch.Tensor):
                return value
            return torch.tensor(value, device=self.bars[next(iter(self.bars))].device if self.bars else torch.device("cpu"))

        # Expect traversal of reference types only
        if var_type not in ("agent_ref", "item_ref"):
            raise ValueError(f"Cannot traverse non-reference VFS variable '{var_name}'")
        if len(segments) < 3:
            raise ValueError(f"Reference '{var_name}' must be followed by '.vfs.<name>' or '.bar.<name>'")

        ref_kind = segments[1]
        tail = segments[2:]
        ref_idx = int(value.item() if isinstance(value, torch.Tensor) else value)

        if var_type == "agent_ref":
            if ref_idx < 0 or ref_idx >= getattr(self.vfs_registry, "num_agents", 0):
                raise ValueError(f"Invalid agent reference index {ref_idx}")
            if ref_kind == "bar":
                if not tail:
                    raise ValueError("Reference traversal missing bar name")
                bar_name = tail[0]
                if bar_name not in self.bars:
                    raise KeyError(f"Bar '{bar_name}' not found while traversing reference")
                bar_tensor = self.bars[bar_name]
                result = bar_tensor[ref_idx]
                if len(tail) > 1:
                    raise ValueError("Cannot traverse beyond bar values")
                return result
            if ref_kind != "vfs":
                raise ValueError(f"Unsupported reference traversal segment '{ref_kind}' (expected 'vfs' or 'bar')")
            return self._resolve_vfs_path(scope="agent", index=ref_idx, segments=tail)

        # item_ref
        if ref_kind != "vfs":
            raise ValueError("Item references only support '.vfs.<name>' traversal")
        if ref_idx < 0 or ref_idx >= getattr(self.vfs_registry, "max_items", 0):
            raise ValueError(f"Invalid item reference index {ref_idx}")
        return self._resolve_vfs_path(scope="item", index=ref_idx, segments=tail)

    def _read_vfs_value(self, scope: str, index: int | None, var_name: str, *, allow_batch: bool) -> torch.Tensor:
        """Read a VFS variable for the given scope/index."""
        if self.vfs_registry is None:
            raise ValueError("VFS registry not set in context")

        if scope == "global":
            return self.vfs_registry.get(var_name, reader="engine")

        if scope in ("agent", "agent_private"):
            tensor = self.vfs_registry.get(var_name, reader="engine")
            if tensor.dim() == 0 or allow_batch:
                return tensor
            if index is None:
                raise ValueError(f"{scope} scope VFS access requires an index")
            return tensor[index]

        if scope == "item":
            if index is None:
                raise ValueError("Item scope VFS access requires an index")
            profile_name = self.vfs_registry.get_item_profile_for_index(index)
            if profile_name is None:
                raise KeyError(f"No item profile registered for vfs_index {index}")
            val = self.vfs_registry.read(var_name, context_index=index, scope=VariableScope.ITEM)
            if isinstance(val, torch.Tensor):
                return val
            return torch.tensor(val, device=self.bars[next(iter(self.bars))].device if self.bars else torch.device("cpu"))

        raise ValueError(f"Unsupported VFS scope '{scope}'")

    def _lookup_variable_type(self, scope: str, index: int | None, var_name: str) -> str | None:
        """Return declared type for a VFS variable."""
        if self.vfs_registry is None:
            return None
        if scope == "item":
            if index is None:
                return None
            profile_name = self.vfs_registry.get_item_profile_for_index(index)
            if profile_name:
                return self.vfs_registry.get_item_variable_type(profile_name, var_name)
        return self.vfs_registry.get_variable_type(var_name)

    def _write_agent_vfs_value(self, var_name: str, index: int, value: torch.Tensor) -> None:
        """Write an agent-scoped VFS variable for a specific agent."""
        if self.vfs_registry is None:
            raise RuntimeError("VFS registry is not configured; cannot write VFS variable")
        batch = self.vfs_registry.get(var_name, reader="engine")
        if batch.dim() == 0:
            raise ValueError(f"VFS variable '{var_name}' is not agent-scoped; cannot index by agent.")
        batch[index] = value
        self.vfs_registry.set(var_name, batch, writer="engine")
