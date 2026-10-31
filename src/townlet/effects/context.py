"""Execution context for effect command evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any

import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableScope
from townlet.world.expression.references import Reference, ReferenceKind, parse_reference

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
        Every write such a context makes (variables, ``bar.X``, item state,
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

    # -- reference resolution (VFS round-2 S5) ------------------------------------------

    def agent_read_row(self) -> int | None:
        """The agent row a bare agent variable or a meter names here: this world's agent.

        The batch is independent single-agent worlds (S1), so the agent is the one the
        context addresses or, when it addresses none (a global-, affordance- or
        item-scoped effect), its world's agent (world ``w`` holds agent ``w``). None for a
        context bound to no world (direct engine or test callers), which spans the batch.
        """
        agent = self.agent_row()
        if agent is not None:
            return agent
        return self.world_row()

    def bound_item(self) -> int | None:
        """The item-arena row ``item.<x>`` names: the innermost bound item (a loop's element first)."""
        if self.target_index is not None and self.target_is_item:
            return self.target_index
        if self.self_index is not None and self.self_is_item:
            return self.self_index
        return None

    def _device(self) -> torch.device:
        return self.bars[next(iter(self.bars))].device if self.bars else torch.device("cpu")

    def _reference(self, path: str) -> Reference:
        reference = parse_reference(path)
        if reference is None:
            raise ValueError(f"'{path}' is not a reference spelling (a bare name, 'bar.<meter>' or 'item.<name>')")
        return reference

    def _registry(self) -> VariableRegistry:
        if self.vfs_registry is None:
            raise ValueError("VFS registry not set in context")
        return self.vfs_registry

    def _required_item(self, path: str) -> int:
        item = self.bound_item()
        if item is None:
            raise ValueError(f"'{path}' reads item state, but this pipeline is bound to no item")
        return item

    def read_item_state(self, item_row: int) -> dict[str, torch.Tensor]:
        """Every state variable of the item at ``item_row``, by name."""
        registry = self._registry()
        profile_name = registry.get_item_profile_for_index(item_row)
        if profile_name is None:
            raise KeyError(f"No item profile registered for vfs_index {item_row}")
        return {
            name: torch.as_tensor(registry.read_item(profile_name, name, item_row, reader="engine"), device=self._device())
            for name in registry.item_profile_map[profile_name]
        }

    def get_path(self, path: str) -> torch.Tensor:
        """The value ``path`` names in this pipeline's world, resolved through the one reference grammar.

        A bare global or affordance variable is this world's row; a bare agent variable
        and ``bar.<m>`` are this world's agent's row; ``item.<x>`` is the bound item's
        state. A context bound to no world reads the whole batch.
        """
        reference = self._reference(path)
        if reference.kind == ReferenceKind.METER:
            if reference.name not in self.bars:
                raise KeyError(f"Bar '{reference.name}' not found. Available: {list(self.bars.keys())}")
            return self._row(self.bars[reference.name], self.agent_read_row())
        if reference.kind == ReferenceKind.ITEM:
            return self.read_item_state(self._required_item(path))[reference.name]
        registry = self._registry()
        var_def = registry.variables.get(reference.name)
        if var_def is None:
            raise KeyError(f"VFS variable '{reference.name}' not found")
        tensor = registry.get(reference.name, reader="engine")
        if var_def.scope == VariableScope.AGENT:
            return self._row(tensor, self.agent_read_row())
        return self._row(tensor, self.world_row())

    @staticmethod
    def _row(tensor: torch.Tensor, row: int | None) -> torch.Tensor:
        if row is None or tensor.dim() == 0:
            return tensor
        return tensor[row]

    def authorize_write_path(self, path: str) -> None:
        """Preflight one resolved command target without reading or mutating storage."""
        reference = self._reference(path)
        if reference.kind == ReferenceKind.METER:
            return
        registry = self._registry()
        if reference.kind == ReferenceKind.ITEM:
            item = self._required_item(path)
            profile = registry.get_item_profile_for_index(item)
            if profile is None:
                raise KeyError(f"No item profile registered for vfs_index {item}")
            registry.authorize_item_write(profile, reference.name, writer="engine")
            return
        registry.authorize_write(reference.name, writer="engine")

    def set_path(self, path: str, value: torch.Tensor) -> None:
        """Write ``path`` in this pipeline's world (the same resolution as ``get_path``), under the write mask."""
        self.authorize_write_path(path)
        reference = self._reference(path)
        if reference.kind == ReferenceKind.METER:
            if reference.name not in self.bars:
                raise KeyError(f"Bar '{reference.name}' not found")
            destination = self.bars[reference.name]
            row = self.agent_read_row()
            if row is None or destination.dim() == 0:
                self._write_batch(path, destination, value)
            elif self.row_is_live(row):
                destination[row] = value
            return
        registry = self._registry()
        if reference.kind == ReferenceKind.ITEM:
            item = self._required_item(path)
            if not self.item_row_is_live(item):
                return
            write_value = value.item() if isinstance(value, torch.Tensor) and value.numel() == 1 else value
            profile_name = registry.get_item_profile_for_index(item)
            if profile_name is None:
                raise KeyError(f"No item profile registered for vfs_index {item}")
            registry.write_item(profile_name, reference.name, write_value, item, writer="engine")
            return
        var_def = registry.variables.get(reference.name)
        if var_def is None:
            raise KeyError(f"VFS variable '{reference.name}' not found")
        row = self.agent_read_row() if var_def.scope == VariableScope.AGENT else self.world_row()
        if row is None:
            self._write_batch_vfs_value(reference.name, value)
        elif self.row_is_live(row):
            self._write_agent_vfs_value(reference.name, row, value)

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

    def _write_batch_vfs_value(self, var_name: str, value: torch.Tensor) -> None:
        """Write every row of a batched VFS variable the write mask leaves live.

        Only a context bound to no world (direct engine or test callers) writes this
        way; a world-bound context writes its own row (S1, review-2026-10-24 VFS F4).
        """
        assert self.vfs_registry is not None
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
