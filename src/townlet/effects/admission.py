"""Rollback state for one immediate effect-admission cascade.

This snapshot covers the finite mutation surface of CommandExecutor lifecycle
commands: bars, ordinary/item VFS writes, affordance availability, effect
admission/reapplication, scheduling/cancellation, item spawning, and torch RNG.
It shares immutable catalog/compiler objects and retains original runtime
objects. It is not a transaction for arbitrary callbacks, environment ticks,
item pickup/despawn, variable declaration changes, or future delayed execution.

The manager captures once at the outer admission boundary, lets nested spawns
execute in their normal order, and restores only on PermissionError. In
particular, dynamic targets see earlier sibling writes and random expressions
are evaluated once. Successful cascades require no commit/copy-back step.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from townlet.effects.manager import ActiveEffect, EffectManager
    from townlet.effects.scheduler import ScheduledItem, Scheduler
    from townlet.items.instance import ItemInstance
    from townlet.items.manager import ItemManager
    from townlet.vfs.registry import VariableRegistry

__all__ = ["EffectAdmissionSnapshot", "permission_denial_rng"]


@contextmanager
def permission_denial_rng() -> Iterator[None]:
    """Undo target-expression sampling if resolving/admitting a spawn is denied."""
    cpu_rng = torch.get_rng_state()
    if torch.cuda.is_initialized():
        cuda_rng = torch.cuda.get_rng_state_all()
    else:
        cuda_rng = None
    try:
        yield
    except PermissionError:
        torch.set_rng_state(cpu_rng)
        if cuda_rng is not None:
            torch.cuda.set_rng_state_all(cuda_rng)
        raise


@dataclass
class _TensorMappingState:
    mapping: dict[str, torch.Tensor]
    entries: dict[str, torch.Tensor]
    values: list[tuple[torch.Tensor, torch.Tensor]]

    @classmethod
    def capture(cls, mapping: dict[str, torch.Tensor]) -> _TensorMappingState:
        return cls(mapping=mapping, entries=mapping.copy(), values=[(tensor, tensor.detach().clone()) for tensor in mapping.values()])

    def restore(self) -> None:
        # Rebind replaced non-arena variables/bars to their original tensors;
        # in-place copy also repairs all arena views and external aliases.
        self.mapping.clear()
        self.mapping.update(self.entries)
        for tensor, value in self.values:
            tensor.copy_(value)


@dataclass
class _ListMappingState[Key, Value]:
    mapping: dict[Key, list[Value]]
    entries: dict[Key, list[Value]]
    values: list[tuple[list[Value], list[Value]]]

    @classmethod
    def capture(cls, mapping: dict[Key, list[Value]]) -> _ListMappingState[Key, Value]:
        return cls(mapping=mapping, entries=mapping.copy(), values=[(items, items.copy()) for items in mapping.values()])

    def restore(self) -> None:
        self.mapping.clear()
        self.mapping.update(self.entries)
        for items, contents in self.values:
            items[:] = contents


@dataclass
class _RegistryState:
    registry: VariableRegistry
    storage: _TensorMappingState
    item_tensor: torch.Tensor | None
    item_values: torch.Tensor | None
    item_profiles: dict[int, str]
    profile_entries: dict[int, str]

    @classmethod
    def capture(cls, registry: VariableRegistry) -> _RegistryState:
        return cls(
            registry=registry,
            storage=_TensorMappingState.capture(registry._storage),
            item_tensor=registry.item_vfs,
            item_values=None if registry.item_vfs is None else registry.item_vfs.detach().clone(),
            item_profiles=registry.item_vfs_index_to_profile,
            profile_entries=registry.item_vfs_index_to_profile.copy(),
        )

    def restore(self) -> None:
        self.registry._storage = self.storage.mapping
        self.storage.restore()
        self.registry.item_vfs = self.item_tensor
        if self.item_tensor is not None and self.item_values is not None:
            self.item_tensor.copy_(self.item_values)
        self.registry.item_vfs_index_to_profile = self.item_profiles
        self.item_profiles.clear()
        self.item_profiles.update(self.profile_entries)


@dataclass
class _ItemSpawnState:
    manager: ItemManager
    active_items: dict[int, ItemInstance]
    active_entries: dict[int, ItemInstance]
    next_instance_id: int
    free_slots: set[int]
    free_values: set[int]
    positions: dict[tuple[int, ...], set[int]]
    position_entries: dict[tuple[int, ...], set[int]]
    position_values: list[tuple[set[int], set[int]]]

    @classmethod
    def capture(cls, manager: ItemManager) -> _ItemSpawnState:
        return cls(
            manager=manager,
            active_items=manager.active_items,
            active_entries=manager.active_items.copy(),
            next_instance_id=manager.next_instance_id,
            free_slots=manager.vfs_free_slots,
            free_values=manager.vfs_free_slots.copy(),
            positions=manager._position_index,
            position_entries=manager._position_index.copy(),
            position_values=[(values, values.copy()) for values in manager._position_index.values()],
        )

    def restore(self) -> None:
        self.manager.active_items = self.active_items
        self.active_items.clear()
        self.active_items.update(self.active_entries)
        self.manager.next_instance_id = self.next_instance_id
        self.manager.vfs_free_slots = self.free_slots
        self.free_slots.clear()
        self.free_slots.update(self.free_values)
        self.manager._position_index = self.positions
        self.positions.clear()
        self.positions.update(self.position_entries)
        for values, contents in self.position_values:
            values.clear()
            values.update(contents)


@dataclass
class EffectAdmissionSnapshot:
    """Original identities plus copied values; capture once, restore on denial.

    Tensor memory and copy cost are linear in the supplied bars, ordinary VFS,
    and item arena. Container cost is linear in active effects/items and pending
    scheduler entries. No compiled command, catalog, or item definition is copied.
    Callers supply actual runtime managers/registries or explicit None for absent
    services; disabled-service placeholders have no state in this domain.
    """

    manager: EffectManager
    global_effects: list[ActiveEffect]
    global_entries: list[ActiveEffect]
    agent_effects: _ListMappingState[int, ActiveEffect]
    item_effects: _ListMappingState[int, ActiveEffect]
    affordance_effects: _ListMappingState[str, ActiveEffect]
    effect_values: list[tuple[ActiveEffect, dict[str, Any]]]
    next_instance_id: int
    current_step: int
    scheduler: Scheduler
    pending: _ListMappingState[int, ScheduledItem]
    scheduler_tick: int
    bars: _TensorMappingState | None
    registry: _RegistryState | None
    item_manager: _ItemSpawnState | None
    affordance_overrides: dict[str, bool] | None
    affordance_entries: dict[str, bool] | None
    cpu_rng: torch.Tensor
    cuda_rng: list[torch.Tensor] | None

    @classmethod
    def capture(
        cls,
        *,
        manager: EffectManager,
        bars: dict[str, torch.Tensor] | None,
        registry: VariableRegistry | None,
        item_manager: ItemManager | None,
    ) -> EffectAdmissionSnapshot:
        effects = manager.get_all_active_effects()
        return cls(
            manager=manager,
            global_effects=manager.global_effects,
            global_entries=manager.global_effects.copy(),
            agent_effects=_ListMappingState.capture(manager.agent_effects),
            item_effects=_ListMappingState.capture(manager.item_effects),
            affordance_effects=_ListMappingState.capture(manager.affordance_effects),
            effect_values=[(effect, {field.name: getattr(effect, field.name) for field in fields(effect)}) for effect in effects],
            next_instance_id=manager.next_instance_id,
            current_step=manager.current_step,
            scheduler=manager.scheduler,
            pending=_ListMappingState.capture(manager.scheduler.pending),
            scheduler_tick=manager.scheduler.current_tick,
            bars=None if bars is None else _TensorMappingState.capture(bars),
            registry=None if registry is None else _RegistryState.capture(registry),
            item_manager=None if item_manager is None else _ItemSpawnState.capture(item_manager),
            affordance_overrides=manager.affordance_overrides,
            affordance_entries=None if manager.affordance_overrides is None else manager.affordance_overrides.copy(),
            cpu_rng=torch.get_rng_state(),
            cuda_rng=torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None,
        )

    def restore(self) -> None:
        """Restore values in place, then recover original mappings/references."""
        with torch.no_grad():
            if self.bars is not None:
                self.bars.restore()
            if self.registry is not None:
                self.registry.restore()
            if self.item_manager is not None:
                self.item_manager.restore()
        for effect, values in self.effect_values:
            for name, value in values.items():
                setattr(effect, name, value)
        self.manager.global_effects = self.global_effects
        self.global_effects[:] = self.global_entries
        self.manager.agent_effects = self.agent_effects.mapping
        self.agent_effects.restore()
        self.manager.item_effects = self.item_effects.mapping
        self.item_effects.restore()
        self.manager.affordance_effects = self.affordance_effects.mapping
        self.affordance_effects.restore()
        self.manager.next_instance_id = self.next_instance_id
        self.manager.current_step = self.current_step
        self.manager.scheduler = self.scheduler
        self.scheduler.pending = self.pending.mapping
        self.pending.restore()
        self.scheduler.current_tick = self.scheduler_tick
        self.manager.affordance_overrides = self.affordance_overrides
        if self.affordance_overrides is not None and self.affordance_entries is not None:
            self.affordance_overrides.clear()
            self.affordance_overrides.update(self.affordance_entries)
        torch.set_rng_state(self.cpu_rng)
        if self.cuda_rng is not None:
            torch.cuda.set_rng_state_all(self.cuda_rng)
