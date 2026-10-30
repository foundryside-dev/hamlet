"""Execution context for effect command evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableScope

if TYPE_CHECKING:
    from townlet.substrate.base import SpatialSubstrate

__all__ = ["ExecutionContext"]


class _NullEffectManager:
    def spawn_effect(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise RuntimeError("EffectManager is not configured; spawn_effect unavailable")


class _NullItemManager:
    def spawn_item(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        raise RuntimeError("ItemManager is not configured; spawn_item unavailable")

    find_spawn_location = spawn_item

    @property
    def num_worlds(self) -> int:  # pragma: no cover
        raise RuntimeError("ItemManager is not configured; spawn_item unavailable")


def _available(overrides: dict[str, bool], affordance: str) -> bool:
    """A world's affordance availability: its runtime override, or open when it has none."""
    if affordance in overrides:
        return bool(overrides[affordance])
    return True


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
    # Spatial state of the tick: raw agent positions (spawn_item origins), affordance
    # positions by name, and the substrate whose declared metric measures distance.
    agent_positions: torch.Tensor | None = None
    affordance_positions: dict[str, torch.Tensor] | None = None
    substrate: SpatialSubstrate | None = None
    interrupt_reason: str | None = None
    current_tick: int = 0
    target_is_item: bool = False
    iterator_value: Any | None = None
    inventory: Any | None = None
    scheduler: Any | None = None  # Scheduler for delay commands
    rng: torch.Generator | None = None
    seed: int | None = None  # Optional deterministic seed for sampling
    # Runtime affordance availability overrides, one mapping per world (S1).
    affordance_overrides: list[dict[str, bool]] | None = None
    # Per-agent liveness of this pipeline: a `[num_agents]` bool tensor set by a masked
    # `if`/`switch` branch, None when every row is live. Every write passes through it.
    write_mask: torch.Tensor | None = None

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

    # -- write mask ---------------------------------------------------------------------

    def agent_row(self) -> int | None:
        """The agent row this context addresses, or None when it addresses no agent."""
        if self.target_index is not None and not self.target_is_item:
            return self.target_index
        if self.self_index is not None and not self.self_is_item:
            return self.self_index
        return None

    def item_world(self, item_row: int) -> int:
        """The world an item-arena row belongs to (items are per world, S1)."""
        if self.vfs_registry is None:
            raise ValueError("VFS registry not set in context; an item row has no world without it")
        return self.vfs_registry.item_world(item_row)

    def item_row(self) -> int | None:
        """The item-arena row this context addresses (self first, then target), if any."""
        if self.self_index is not None and self.self_is_item:
            return self.self_index
        if self.target_index is not None and self.target_is_item:
            return self.target_index
        return None

    def world_row(self) -> int | None:
        """The one world this context reads and writes, or None when it is bound to none.

        The batch is independent single-agent worlds (S1), so world ``i`` is agent
        ``i``'s. Every effect lives in one world (``ActiveEffect.world``: its agent's,
        its item's, or for a global- or affordance-scoped effect the world whose event
        spawned it). An affordance or item interaction acts in the world of the agent it
        addresses; a context whose only entity is an item acts in that item's world.
        Every write such a context makes (globals, bare ``bar.X``, item state,
        affordance availability, spawns) lands in that world only.

        A context bound to no world (no effect, agent or item: only direct engine or
        test callers build one) addresses every world under its write mask, and a
        global- or affordance-scoped spawn from it creates one instance per live world.
        """
        if self.effect is not None:
            return int(self.effect.world)
        agent = self.agent_row()
        if agent is not None:
            return agent
        item = self.item_row()
        return None if item is None else self.item_world(item)

    def live_worlds(self, num_worlds: int) -> list[int]:
        """The worlds a write from this context lands in: its own if live, else every live one."""
        world = self.world_row()
        if world is not None:
            return [world] if self.row_is_live(world) else []
        return [w for w in range(num_worlds) if self.row_is_live(w)]

    def require_same_world(self, what: str, entity_world: int) -> None:
        """Refuse an entity reference that leaves this context's world (S1: worlds are independent)."""
        world = self.world_row()
        if world is not None and entity_world != world:
            raise ValueError(
                f"{what} is in world {entity_world}, but this pipeline runs in world {world}: worlds are independent, "
                "so a pipeline reads and writes only its own world"
            )

    def item_row_is_live(self, item_row: int) -> bool:
        """Whether the world of item row `item_row` is live under the write mask.

        An item has one world, so a per-agent condition gates its write by that world's
        row alone (S1: world i is agent i's), never by the whole batch.
        """
        return self.row_is_live(self.item_world(item_row))

    def row_is_live(self, index: int) -> bool:
        """Whether agent row `index` is live under the write mask."""
        if self.write_mask is None:
            return True
        return bool(self.write_mask[index].item())

    def require_whole_batch_live(self, what: str) -> None:
        """A target with no per-agent axis can only be written when no row is masked out.

        Writing it when some rows are live and others are not would collapse a
        per-agent condition into one shared decision; refuse instead.
        """
        if self.write_mask is None or bool(self.write_mask.all().item()):
            return
        raise ValueError(
            f"Cannot write {what} under a per-agent condition: the target has no per-agent row, "
            f"but the enclosing if/switch holds for only some agents "
            f"({int(self.write_mask.sum().item())} of {self.write_mask.numel()}). "
            "Condition on a scalar (target./self.) value, or write a per-agent target."
        )

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
                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                profile_name = self.vfs_registry.get_item_profile_for_index(self.self_index)
                if profile_name is None:
                    raise KeyError(f"No item profile registered for vfs_index {self.self_index}")
                value = self.vfs_registry.read_item(profile_name, var_name, self.self_index, reader="engine")
                return torch.as_tensor(value, dtype=torch.float32)

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
            device = torch.device("cpu")
            if self.bars:
                device = self.bars[next(iter(self.bars))].device
            if self.affordance_overrides is None:
                return torch.tensor(True, device=device)
            world = self.world_row()
            if world is not None:
                return torch.tensor(_available(self.affordance_overrides[world], aff_name), device=device)
            return torch.tensor([_available(overrides, aff_name) for overrides in self.affordance_overrides], device=device)

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")
            segments = path.split(".")[1:]  # drop leading "vfs"
            # Keep batched tensors for bare vfs.* paths; callers (target./self.) index as needed.
            return self._resolve_vfs_path(scope="agent", index=None, segments=segments)

        # Handle global.vfs.* paths: the explicit spelling of a global, its world's value
        if path.startswith("global.vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")
            return self._resolve_vfs_path(scope="global", index=None, segments=path.split(".")[2:])

        raise ValueError(f"Invalid path: {path}")

    def authorize_write_path(self, path: str) -> None:
        """Preflight one resolved command target without reading or mutating storage."""
        parts = path.split(".")
        item_index: int | None = None
        if parts[0] == "global":
            parts.pop(0)
        elif parts[0] in ("self", "target"):
            actor = parts.pop(0)
            is_item = self.self_is_item if actor == "self" else self.target_is_item
            if is_item:
                index = self.self_index if actor == "self" else self.target_index
                if index is None:
                    raise ValueError(f"{actor}_index not set in context")
                item_index = index
        if parts[0] != "vfs":
            return
        if len(parts) < 2:
            raise ValueError(f"VFS write path '{path}' has no variable identity")
        if self.vfs_registry is None:
            raise ValueError("VFS registry not set in context")
        # Bare VFS targets and item-profile IDs may contain dots. Resolve the
        # complete declared identity rather than interpreting it as traversal.
        variable_id = ".".join(parts[1:])
        if item_index is None:
            self.vfs_registry.authorize_write(variable_id, writer="engine")
        else:
            profile = self.vfs_registry.get_item_profile_for_index(item_index)
            if profile is None:
                raise KeyError(f"No item profile registered for vfs_index {item_index}")
            self.vfs_registry.authorize_item_write(profile, variable_id, writer="engine")

    def set_path(self, path: str, value: torch.Tensor) -> None:
        """Set path to new tensor value (mutation).

        Args:
            path: Dot-separated path
            value: New tensor value
        """
        self.authorize_write_path(path)
        # Handle target. prefix
        if path.startswith("target."):
            if self.target_index is None:
                raise ValueError("target_index not set in context")

            rest = path[len("target.") :]
            # Get original tensor and mutate in-place
            # Item target VFS handling
            if rest.startswith("vfs.") and self.target_is_item:
                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                if not self.item_row_is_live(self.target_index):
                    return
                write_value = value.item() if isinstance(value, torch.Tensor) and value.numel() == 1 else value
                profile_name = self.vfs_registry.get_item_profile_for_index(self.target_index)
                if profile_name is None:
                    raise KeyError(f"No item profile registered for vfs_index {self.target_index}")
                self.vfs_registry.write_item(profile_name, var_name, write_value, self.target_index, writer="engine")
                return

            if rest.startswith("vfs."):
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                segments = rest.split(".")[1:]
                var_name = segments[0]
                if len(segments) > 1:
                    raise ValueError(f"Setting target reference traversal '{rest}' is not supported.")
                if self.row_is_live(self.target_index):
                    self._write_agent_vfs_value(var_name, self.target_index, value)
                return

            self._write_indexed(rest, self.target_index, value)
            return

        # NEW: Handle self. prefix with special logic for items
        if path.startswith("self."):
            if self.self_index is None:
                raise ValueError("self_index not set in context")

            rest = path[len("self.") :]

            # NEW: Special handling for self.vfs.* when self is an item
            if rest.startswith("vfs.") and self.self_is_item:
                var_name = rest[len("vfs.") :]
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                if not self.item_row_is_live(self.self_index):
                    return
                # Convert scalar tensors to Python floats for item VFS storage.
                write_value = value.item() if isinstance(value, torch.Tensor) and value.numel() == 1 else value
                profile_name = self.vfs_registry.get_item_profile_for_index(self.self_index)
                if profile_name is None:
                    raise KeyError(f"No item profile registered for vfs_index {self.self_index}")
                self.vfs_registry.write_item(profile_name, var_name, write_value, self.self_index, writer="engine")
                return

            if rest.startswith("vfs."):
                if self.vfs_registry is None:
                    raise ValueError("VFS registry not set in context")
                segments = rest.split(".")[1:]
                var_name = segments[0]
                if len(segments) > 1:
                    raise ValueError(f"Setting reference traversal '{rest}' is not supported.")
                if self.row_is_live(self.self_index):
                    self._write_agent_vfs_value(var_name, self.self_index, value)
                return

            self._write_indexed(rest, self.self_index, value)
            return

        # Handle bar.* paths: a context bound to a world writes that world's row only
        if path.startswith("bar."):
            bar_name = path[len("bar.") :]
            if bar_name not in self.bars:
                raise KeyError(f"Bar '{bar_name}' not found")
            destination = self.bars[bar_name]
            world = self.world_row()
            if world is None or destination.dim() == 0:
                self._write_batch(path, destination, value)
            elif self.row_is_live(world):
                if isinstance(value, torch.Tensor) and value.dim() > 0 and value.shape == destination.shape:
                    value = value[world]
                destination[world] = value
            return

        # Handle affordance availability overrides
        if path.startswith("affordance.") and path.endswith(".available"):
            parts = path.split(".")
            if len(parts) != 3:
                raise ValueError(f"Invalid affordance path: {path}")
            aff_name = parts[1]
            if self.affordance_overrides is None:
                raise ValueError(f"Cannot write '{path}': this pipeline was given no affordance availability store")
            worlds = self.live_worlds(len(self.affordance_overrides))
            per_world = isinstance(value, torch.Tensor) and value.numel() == len(self.affordance_overrides) and value.dim() == 1
            if isinstance(value, torch.Tensor) and value.numel() != 1 and not per_world:
                raise ValueError(f"'{path}' takes one value per world, but the expression produced shape {tuple(value.shape)}")
            for world in worlds:
                if isinstance(value, torch.Tensor):
                    self.affordance_overrides[world][aff_name] = bool((value[world] if per_world else value).item())
                else:
                    self.affordance_overrides[world][aff_name] = bool(value)
            return

        # Handle bare vfs.* paths, and global.vfs.* (the explicit spelling of a global)
        if path.startswith(("vfs.", "global.vfs.")):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path.split("vfs.", 1)[1]
            var_def = self.vfs_registry.variables.get(var_name)
            if var_def is None:
                raise KeyError(f"VFS variable '{var_name}' not found")

            if path.startswith("global.") and var_def.scope != VariableScope.GLOBAL:
                raise ValueError(f"'{path}' names {var_def.scope}-scoped variable '{var_name}'; 'global.vfs.' spells a global only.")
            if var_def.scope == VariableScope.AGENT:
                # An agent-scoped bare write is one agent's row, never the batch. The
                # compiler resolves it to target.vfs.X; a node reaching here unresolved
                # is routed to the agent target or refused.
                if self.target_index is None or self.target_is_item:
                    raise ValueError(
                        f"Bare write '{path}' names agent-scoped variable '{var_name}' but this context has no agent "
                        f"target; an agent-scoped write is never a batch write. Write it as 'target.{path}'."
                    )
                if self.row_is_live(self.target_index):
                    self._write_agent_vfs_value(var_name, self.target_index, value)
                return

            self._write_global_vfs_value(var_name, value)
            return

        raise ValueError(f"Invalid path: {path}")

    def _write_indexed(self, path: str, index: int, value: torch.Tensor) -> None:
        """Write one agent's row of a batched path, or the whole value of a scalar path."""
        original = self.get_path(path)
        if original.dim() == 0:
            self.set_path(path, value)
            return
        if self.row_is_live(index):
            original[index] = value

    def _write_batch(self, path: str, destination: torch.Tensor, value: torch.Tensor) -> None:
        """Copy `value` into `destination` in place, broadcasting a scalar over the batch.

        The stored tensor is never rebound: a rebind to an expanded view made the next
        indexed write land on every agent (review-2026-10-24 effects F1).
        """
        if destination.dim() == 0:
            self.require_whole_batch_live(f"scalar '{path}'")
            destination.copy_(value)
            return
        if self.write_mask is None:
            destination.copy_(value)
            return
        if self.write_mask.shape != destination.shape:
            raise ValueError(f"Write mask shape {tuple(self.write_mask.shape)} does not match '{path}' shape {tuple(destination.shape)}")
        destination.copy_(torch.where(self.write_mask, value.to(destination.dtype), destination))

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

        assert self.vfs_registry is not None  # _read_vfs_value above required it
        if var_type == "agent_ref":
            if ref_idx < 0 or ref_idx >= self.vfs_registry.num_agents:
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
        if ref_idx < 0 or ref_idx >= self.vfs_registry.max_items:
            raise ValueError(f"Invalid item reference index {ref_idx}")
        self.require_same_world(f"Item reference '{var_name}' (row {ref_idx})", self.vfs_registry.item_world(ref_idx))
        return self._resolve_vfs_path(scope="item", index=ref_idx, segments=tail)

    def _read_vfs_value(self, scope: str, index: int | None, var_name: str, *, allow_batch: bool) -> torch.Tensor:
        """Read a VFS variable for the given scope/index."""
        if self.vfs_registry is None:
            raise ValueError("VFS registry not set in context")

        if scope == "global" or self._declared_global(var_name):
            # One row per world (S1): the context's world reads its own row.
            tensor = self.vfs_registry.get(var_name, reader="engine")
            row = self.world_row()
            return tensor if row is None else tensor[row]

        if scope == "agent":
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
            val = self.vfs_registry.read_item(profile_name, var_name, index, reader="engine")
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

    def _declared_global(self, var_name: str) -> bool:
        assert self.vfs_registry is not None
        var_def = self.vfs_registry.variables.get(var_name)
        return var_def is not None and var_def.scope == VariableScope.GLOBAL

    def _write_global_vfs_value(self, var_name: str, value: torch.Tensor) -> None:
        """Write a global into the context's world, or into every world under the write mask.

        A global has one row per world (S1). A context bound to one world writes that
        row only, so one world's interaction never moves another world's state
        (review-2026-10-24 VFS F4). A world-shared context (see `world_row`) writes every
        world's row that the write mask leaves live.
        """
        assert self.vfs_registry is not None
        row = self.world_row()
        if row is not None:
            if self.row_is_live(row):
                self._write_agent_vfs_value(var_name, row, value)
            return
        batch = self.vfs_registry.get(var_name, reader="engine")
        # No dtype cast: the registry refuses a value whose dtype is not the declared one.
        candidate = value.to(device=batch.device).expand_as(batch)
        if self.write_mask is not None:
            mask = self.write_mask.to(device=batch.device, dtype=torch.bool)
            while mask.dim() < batch.dim():
                mask = mask.unsqueeze(-1)
            candidate = torch.where(mask, candidate, batch)
        self.vfs_registry.set(var_name, candidate.clone(), writer="engine")

    def _write_agent_vfs_value(self, var_name: str, index: int, value: torch.Tensor) -> None:
        """Write one row of a batched (agent- or global-scoped) VFS variable.

        A global's row is the world of agent ``index`` (S1: one agent per world).
        """
        if self.vfs_registry is None:
            raise RuntimeError("VFS registry is not configured; cannot write VFS variable")
        batch = self.vfs_registry.get(var_name, reader="engine")
        if batch.dim() == 0:
            raise ValueError(f"VFS variable '{var_name}' is not agent-scoped; cannot index by agent.")
        if isinstance(value, torch.Tensor) and value.dim() > 0 and value.shape == batch.shape:
            # A batch-shaped value is the expression evaluated over every row (a bare
            # read reaching the runtime unresolved); the agent's row is its value.
            value = value[index]
        batch[index] = value
        self.vfs_registry.set(var_name, batch, writer="engine")
