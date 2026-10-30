"""ItemManager for spawning/despawning items and managing lifecycle."""

from __future__ import annotations

import hashlib
import logging
import math
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from typing import TYPE_CHECKING, Any, Literal

import torch

if TYPE_CHECKING:
    from townlet.config.items_config import ItemsAppearanceConfig, ItemsCatalogConfig
    from townlet.substrate.base import SpatialSubstrate
    from townlet.vfs.registry import VariableRegistry

from townlet.config.items_config import (
    SpawnPlacementConfig,
    SpawnScheduleConfig,
    build_item_command_action_name,
)
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode
from townlet.items.instance import ItemInstance
from townlet.vfs.registry import item_row_world
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.world.expression.ast_nodes import PathAccess, Variable
from townlet.world.expression.context import ExecutionContext as ExprExecutionContext
from townlet.world.expression.evaluator import Evaluator

__all__ = ["ItemManager", "CompiledItemType", "SpawnPredicateReads", "WorldItemState"]


class SpawnPredicateReads:
    """What an item spawn predicate (`when:`) may read, and the runtime values behind it.

    One declaration owns both sides, so the compiler can never admit a name the runtime
    does not serve: `schema()` is what the compiler type-checks a predicate against, and
    `context()` is what `ItemManager` evaluates it in. Both are derived from the same
    registry roster (`VFSCompiler.build_runtime_variables` at compile time, the live
    `VariableRegistry` at run time) through the same scope rule:

    - a registry variable is readable iff its declared scope is in `VARIABLE_SCOPES`,
      spelled `vfs.<id>`. That includes the engine-published `tick` (a global variable),
      which is the one temporal primitive a predicate reads; there is no `temporal.*`
      namespace here.
    - a meter is readable as `bar.<name>`.

    Every other spelling (bare names, `env.*`, `agent.vfs.*`, `temporal.*`) is refused at
    compile time. Global and agent reads both yield one value per world (S1: one agent
    per world), and items are per world too, so the predicate is evaluated per world
    (`ItemManager._should_spawn_rule` gives one bool per world): each world decides its
    own spawn. There is no reduction across worlds.
    """

    VARIABLE_ROOT = "vfs"
    BAR_ROOT = "bar"
    VARIABLE_SCOPES: frozenset[VariableScope] = frozenset({VariableScope.GLOBAL, VariableScope.AGENT})

    @classmethod
    def admits(cls, scope: VariableScope | str) -> bool:
        return VariableScope(scope) in cls.VARIABLE_SCOPES

    @classmethod
    def variable_path(cls, variable_id: str) -> str:
        return f"{cls.VARIABLE_ROOT}.{variable_id}"

    @classmethod
    def bar_path(cls, meter_name: str) -> str:
        return f"{cls.BAR_ROOT}.{meter_name}"

    @staticmethod
    def _expression_type(variable_type: str) -> str:
        return "float" if variable_type == "scalar" else variable_type

    @classmethod
    def schema(cls, *, meter_names: Iterable[str], variables: Iterable[VariableDef]) -> dict[str, str]:
        """The compile-time type schema: every readable path and its expression type."""
        schema = {cls.bar_path(name): "float" for name in meter_names}
        for variable in variables:
            if cls.admits(variable.scope):
                schema[cls.variable_path(variable.id)] = cls._expression_type(variable.type)
        return schema

    @classmethod
    def reads(cls, ast: Any) -> list[str]:
        """Every name a parsed predicate reads, in source order (paths joined by '.')."""
        if isinstance(ast, PathAccess):
            return [".".join(ast.segments)]
        if isinstance(ast, Variable):
            return [ast.name]
        if is_dataclass(ast) and not isinstance(ast, type):
            return [name for field in fields(ast) for name in cls.reads(getattr(ast, field.name))]
        if isinstance(ast, list | tuple):
            return [name for child in ast for name in cls.reads(child)]
        return []

    @classmethod
    def context(
        cls,
        *,
        bars: Mapping[str, torch.Tensor],
        registry: VariableRegistry | None,
        device: torch.device,
    ) -> ExprExecutionContext:
        """The runtime evaluation context, resolved variable id -> scope -> value."""
        values: dict[str, torch.Tensor] = {}
        types: dict[str, str] = {}
        num_agents: int | None = None
        if registry is not None:
            num_agents = registry.num_agents
            for variable_id, variable in registry.variables.items():
                if not cls.admits(variable.scope):
                    continue
                values[variable_id] = registry.get(variable_id, reader="engine")
                types[variable_id] = variable.type
        return ExprExecutionContext(
            bars=dict(bars),
            vfs=values,
            affordances={},
            temporal={},
            device=device,
            vfs_types=types,
            num_agents=num_agents,
        )


@dataclass
class CompiledItemType:
    """Item type with pre-compiled Effects commands.

    This is the runtime representation after CommandCompiler processes
    the raw ItemTypeConfig from YAML.
    """

    id: str
    vfs_profile: str
    duration: int | None
    cooldown: int | None
    name: str | None
    icon: str | None
    tags: tuple[str, ...]
    exclusive: bool

    # Pre-compiled Effects commands (ready for CommandExecutor)
    compiled_on_pickup: list[CommandNode]
    compiled_on_use: list[CommandNode]
    compiled_on_drop: list[CommandNode]
    compiled_local_commands: dict[str, list[CommandNode]]
    compiled_inventory_commands: dict[str, list[CommandNode]]


@dataclass
class WorldItemState:
    """One world's item lifecycle (S1: the batch is independent single-agent worlds).

    Every field is per world: occupancy, the world's arena rows, cooldowns, respawn
    timers, rule spawn counts and schedule cursors. `free_rows` holds FLAT item-arena
    rows of this world (`world * items_per_world + slot`), so an allocated row is
    globally unique and effect/expression row keys stay valid without a world beside them.
    """

    free_rows: set[int]
    active: dict[int, ItemInstance] = field(default_factory=dict)  # on the ground (and held shared items)
    held: dict[int, ItemInstance] = field(default_factory=dict)  # lifted exclusive items, in an inventory
    position_index: dict[tuple[int, ...] | tuple[float, ...], set[int]] = field(default_factory=dict)
    cooldown_until: dict[str, int] = field(default_factory=dict)
    respawn_timers: dict[str, int] = field(default_factory=dict)
    rule_spawn_counts: dict[str, int] = field(default_factory=dict)
    next_scheduled_tick: dict[str, int] = field(default_factory=dict)
    script_indices: dict[str, int] = field(default_factory=dict)


class ItemManager:
    """Manages every world's items: one compiled catalog, per-world lifecycle state.

    Items are per world (S1, 2026-10-25): world `w` owns arena rows
    `[w * items_per_world, (w + 1) * items_per_world)` and its own `WorldItemState`.
    A pickup, spawn, despawn, cooldown or respawn timer in one world never touches
    another. Instance ids stay globally unique (`InventoryState.purge_instance` masks
    every inventory row by id). Under S1 world `w`'s one agent is agent `w`
    (`world_of_agent`); a holder is an agent index, its world is derived.
    """

    def __init__(
        self,
        catalog: ItemsCatalogConfig,
        *,
        items_per_world: int,
        num_worlds: int,
        substrate: SpatialSubstrate,
        device: torch.device | str,
        schema: dict[str, str] | None = None,
        vfs_registry: VariableRegistry | None = None,
        effect_manager: Any | None = None,
        inventory: Any | None = None,
    ) -> None:
        """Initialize ItemManager.

        Args:
            catalog: Items catalog from items.yaml
            items_per_world: Arena rows per world (`token_spec.item_capacity`)
            num_worlds: Worlds in the batch (S1: one per agent)
            substrate: The world's substrate; placement and co-location ask it
            device: PyTorch device
            schema: Variable type schema for Effects compilation
            vfs_registry: VFS registry for item state storage
            inventory: InventoryState reference for cleanup on despawn
        """
        if items_per_world < 0:
            raise ValueError(f"items_per_world must be >= 0, got {items_per_world}")
        if num_worlds < 1:
            raise ValueError(f"num_worlds must be >= 1, got {num_worlds}")
        if vfs_registry is not None and (vfs_registry.items_per_world, vfs_registry.num_worlds) != (items_per_world, num_worlds):
            raise ValueError(
                f"ItemManager arena ({num_worlds} worlds x {items_per_world} rows) disagrees with the registry's "
                f"({vfs_registry.num_worlds} x {vfs_registry.items_per_world})"
            )
        self.catalog = catalog
        self.items_per_world = items_per_world
        self.num_worlds = num_worlds
        self.substrate = substrate
        self.device = torch.device(device) if isinstance(device, str) else device
        self.vfs_registry = vfs_registry  # Store VFS registry
        self.effect_manager = effect_manager
        self.inventory = inventory  # Store inventory for despawn cleanup (I2 fix)
        self._debug_items = os.getenv("HAMLET_DEBUG_ITEMS", "").strip().lower() in {"1", "true", "yes", "on"}
        self._logger = logging.getLogger("hamlet.items")

        # Compile item interactions if schema provided
        self.compiled_item_types: list[CompiledItemType] = []
        self.custom_action_specs: list[tuple[str, str, Literal["local", "inventory"], str]] = []

        if schema is not None:
            from townlet.config.effects_config import CommandConfig
            from townlet.effects.parser import CommandParser

            compiler = CommandCompiler(schema=schema, agent_target=True)
            parser = CommandParser()

            for item_type in catalog.item_types:
                # Convert raw dicts to CommandConfig objects
                on_pickup_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_pickup]
                on_use_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_use]
                on_drop_configs = [CommandConfig(**cmd) for cmd in item_type.interactions.on_drop]
                # Custom verbs
                local_custom_cfgs: dict[str, list[CommandConfig]] = {}
                inventory_custom_cfgs: dict[str, list[CommandConfig]] = {}
                for custom in item_type.interactions.local_commands:
                    local_custom_cfgs[custom.name] = [CommandConfig(**cmd) for cmd in custom.effects]
                for custom in item_type.interactions.inventory_commands:
                    inventory_custom_cfgs[custom.name] = [CommandConfig(**cmd) for cmd in custom.effects]

                # Parse CommandConfig objects to CommandNode AST
                on_pickup_nodes = parser.parse_commands(on_pickup_configs)
                on_use_nodes = parser.parse_commands(on_use_configs)
                on_drop_nodes = parser.parse_commands(on_drop_configs)
                local_custom_nodes = {name: parser.parse_commands(cmds) for name, cmds in local_custom_cfgs.items()}
                inventory_custom_nodes = {name: parser.parse_commands(cmds) for name, cmds in inventory_custom_cfgs.items()}

                # Compile with type checking and AST storage
                compiled_on_pickup = compiler.compile_commands(on_pickup_nodes)
                compiled_on_use = compiler.compile_commands(on_use_nodes)
                compiled_on_drop = compiler.compile_commands(on_drop_nodes)
                compiled_local_commands = {name: compiler.compile_commands(cmds) for name, cmds in local_custom_nodes.items()}
                compiled_inventory_commands = {name: compiler.compile_commands(cmds) for name, cmds in inventory_custom_nodes.items()}

                self.compiled_item_types.append(
                    CompiledItemType(
                        id=item_type.id,
                        vfs_profile=item_type.vfs_profile,
                        duration=item_type.duration,
                        cooldown=item_type.cooldown,
                        name=item_type.name,
                        icon=item_type.icon,
                        tags=tuple(item_type.tags),
                        exclusive=item_type.exclusive,
                        compiled_on_pickup=compiled_on_pickup,
                        compiled_on_use=compiled_on_use,
                        compiled_on_drop=compiled_on_drop,
                        compiled_local_commands=compiled_local_commands,
                        compiled_inventory_commands=compiled_inventory_commands,
                    )
                )
                for name in local_custom_cfgs:
                    action_name = build_item_command_action_name(item_type.id, name, "local")
                    self.custom_action_specs.append((action_name, item_type.id, "local", name))
                for name in inventory_custom_cfgs:
                    action_name = build_item_command_action_name(item_type.id, name, "inventory")
                    self.custom_action_specs.append((action_name, item_type.id, "inventory", name))
        else:
            # No schema - store raw types without compilation
            # (Used in unit tests that don't need Effects)
            for item_type in catalog.item_types:
                self.compiled_item_types.append(
                    CompiledItemType(
                        id=item_type.id,
                        vfs_profile=item_type.vfs_profile,
                        duration=item_type.duration,
                        cooldown=item_type.cooldown,
                        name=item_type.name,
                        icon=item_type.icon,
                        tags=tuple(item_type.tags),
                        exclusive=item_type.exclusive,
                        compiled_on_pickup=[],
                        compiled_on_use=[],
                        compiled_on_drop=[],
                        compiled_local_commands={},
                        compiled_inventory_commands={},
                    )
                )
                for custom in item_type.interactions.local_commands:
                    action_name = build_item_command_action_name(item_type.id, custom.name, "local")
                    self.custom_action_specs.append((action_name, item_type.id, "local", custom.name))
                for custom in item_type.interactions.inventory_commands:
                    action_name = build_item_command_action_name(item_type.id, custom.name, "inventory")
                    self.custom_action_specs.append((action_name, item_type.id, "inventory", custom.name))

        self.next_instance_id = 0
        # Every live instance (any world, ground or held), by globally unique id.
        self.live_items: dict[int, ItemInstance] = {}
        self.worlds: list[WorldItemState] = [self._fresh_world(world) for world in range(num_worlds)]
        # One random stream per world for item placement and spawn schedules, so one
        # world's draws never shift another's (S1). Seeded from the run seed
        # (`torch.initial_seed()`, set by `seed_all`), the world index and the episode,
        # without consuming the global stream: the same seed is the same run.
        self._episode = 0
        self.world_rngs: list[torch.Generator] = []
        self._reseed_world_rngs()

        # Appearance config for periodic respawning (shared rules; state is per world).
        self.appearance_config: ItemsAppearanceConfig | None = None
        self._rule_keys: dict[int, str] = {}
        # Enumerated grid cells, built on first use by `grid` placement.
        self._cells: list[tuple[int, ...]] | None = None

    def _reseed_world_rngs(self) -> None:
        run_seed = torch.initial_seed()
        self.world_rngs = []
        for world in range(self.num_worlds):
            digest = hashlib.blake2b(f"items:{run_seed}:{self._episode}:{world}".encode(), digest_size=8).digest()
            generator = torch.Generator(device=self.device)
            generator.manual_seed(int.from_bytes(digest, "little") & ((1 << 63) - 1))
            self.world_rngs.append(generator)

    def _fresh_world(self, world: int) -> WorldItemState:
        base = world * self.items_per_world
        return WorldItemState(free_rows=set(range(base, base + self.items_per_world)))

    def _log_items(self, message: str, **kwargs: Any) -> None:
        """Emit debug logs when HAMLET_DEBUG_ITEMS is enabled."""
        if not self._debug_items:
            return
        self._logger.debug(message, extra=kwargs)

    # -- worlds -----------------------------------------------------------------------

    @staticmethod
    def world_of_agent(agent_idx: int) -> int:
        """The world agent `agent_idx` lives in. S1: one agent per world, world i = agent i."""
        return agent_idx

    def world_of(self, item: ItemInstance) -> int:
        """The world an item instance lives in, from its flat arena row."""
        return item_row_world(item.vfs_index, self.items_per_world)

    def world_state(self, world: int) -> WorldItemState:
        if not 0 <= world < self.num_worlds:
            raise IndexError(f"World {world} is outside the batch [0, {self.num_worlds})")
        return self.worlds[world]

    def items_in_world(self, world: int) -> list[ItemInstance]:
        """Every live item of `world` (ground and held), in arena-row order."""
        state = self.world_state(world)
        return sorted([*state.active.values(), *state.held.values()], key=lambda item: item.vfs_index)

    def item_at_row(self, vfs_index: int) -> ItemInstance | None:
        """The live instance holding arena row `vfs_index`, if any."""
        state = self.world_state(item_row_world(vfs_index, self.items_per_world))
        for items in (state.active, state.held):
            for item in items.values():
                if item.vfs_index == vfs_index:
                    return item
        return None

    def holder_of(self, item: ItemInstance) -> int | None:
        """The agent carrying `item` in its own world (lowest index), or None on the ground."""
        world = self.world_of(item)
        holders = sorted(h for h in item.holder_agent_ids if self.world_of_agent(h) == world)
        return holders[0] if holders else None

    def items_at(self, world: int, position: torch.Tensor) -> list[ItemInstance]:
        """Active items of `world` co-located with `position`, in spawn order.

        Co-location is the substrate's own predicate (`is_on_position`): exact on a grid,
        within the interaction radius on a continuous space, always on aspatial.
        """
        active = list(self.world_state(world).active.values())
        if not active:
            return []
        dtype = self.substrate.position_dtype
        item_positions = torch.tensor([list(item.position) for item in active], dtype=dtype, device=position.device)
        item_positions = item_positions.reshape(len(active), self.substrate.position_dim)
        here = self.substrate.is_on_position(item_positions, position.to(dtype=dtype))
        return [item for item, on in zip(active, here.tolist(), strict=True) if on]

    def reset_state(self) -> None:
        """Clear all item runtime state for a fresh episode."""
        self.live_items.clear()
        self.worlds = [self._fresh_world(world) for world in range(self.num_worlds)]
        self.appearance_config = None
        self._rule_keys.clear()
        self.next_instance_id = 0
        self._episode += 1
        self._reseed_world_rngs()

        if self.vfs_registry is not None:
            self.vfs_registry.item_vfs_index_to_profile.clear()
            if self.vfs_registry.item_vfs is not None:
                self.vfs_registry.item_vfs.zero_()

    # -- positions --------------------------------------------------------------------

    def _position_key(self, position: Iterable[Any] | torch.Tensor) -> tuple[int, ...] | tuple[float, ...]:
        """A position in the substrate's own dtype: integer cells, or float coordinates."""
        values = position.tolist() if isinstance(position, torch.Tensor) else list(position)
        if self.substrate.position_dtype.is_floating_point:
            return tuple(float(x) for x in values)
        return tuple(int(round(float(x))) for x in values)

    def _grid_cells(self) -> list[tuple[int, ...]]:
        """Every cell of a discrete grid substrate, in the substrate's enumeration order.

        `grid` placement is refused at compile on any other substrate.
        """
        if self._cells is None:
            if self.substrate.position_dtype.is_floating_point or self.substrate.position_dim == 0:
                raise RuntimeError("grid item placement needs a discrete grid substrate; the compiler refuses it here")
            self._cells = [tuple(int(c) for c in cell) for cell in self.substrate.get_all_positions()]
        return self._cells

    def _position_occupied(self, world: int, position: tuple[int, ...] | tuple[float, ...]) -> bool:
        """Check whether a position is occupied by an active item of `world` (O(1) lookup)."""
        return bool(self.world_state(world).position_index.get(position))

    def _index_position(self, state: WorldItemState, item: ItemInstance) -> None:
        state.position_index.setdefault(self._position_key(item.position), set()).add(item.instance_id)

    def _unindex_position(self, state: WorldItemState, item: ItemInstance) -> None:
        key = self._position_key(item.position)
        ids = state.position_index.get(key)
        if ids is not None:
            ids.discard(item.instance_id)
            if not ids:
                del state.position_index[key]

    def find_spawn_location(
        self,
        world: int,
        strategy: str,
        origin: tuple[int, ...] | tuple[float, ...] | None = None,
        explicit: tuple[int, ...] | tuple[float, ...] | None = None,
        retries: int = 3,
    ) -> tuple[int, ...] | tuple[float, ...]:
        """Resolve a spawn position in `world`; fail fast on unsupported inputs."""
        if strategy in {"self", "target"}:
            if origin is None:
                raise RuntimeError(f"Origin required for strategy '{strategy}'")
            return self._position_key(origin)

        if strategy == "explicit":
            if explicit is None:
                raise RuntimeError("Explicit coordinates required for strategy 'explicit'")
            return self._position_key(explicit)

        if strategy == "random":
            if origin is None:
                raise RuntimeError("Origin required for strategy 'random'")
            dim = self.substrate.position_dim
            dtype = self.substrate.position_dtype
            base = torch.tensor([list(self._position_key(origin))], dtype=dtype, device=self.device).reshape(1, dim)
            occupied = self.world_state(world).position_index
            for _ in range(retries):
                # A unit step per axis, through the substrate's own boundary rule.
                step = torch.randint(-1, 2, (1, dim), device=self.device, generator=self.world_rngs[world]).to(dtype=dtype)
                candidate = self._position_key(self.substrate.apply_movement(base.clone(), step)[0])
                if not occupied.get(candidate):
                    return candidate
            raise RuntimeError("Failed to find free position for random spawn_item after retries")

        raise RuntimeError(f"Unsupported spawn strategy '{strategy}'")

    # -- lifecycle --------------------------------------------------------------------

    def _authorize_spawn_state(self, item_type: str, initial_state: dict[str, float] | None) -> dict[str, float]:
        """Resolve and authorize complete overrides without allocating an item."""
        item_def = next((item for item in self.catalog.item_types if item.id == item_type), None)
        if item_def is None:
            raise KeyError(f"Unknown item type: {item_type}")
        overrides: dict[str, float] = {}
        if self.vfs_registry is not None and item_def.vfs_profile:
            profile_name = item_def.vfs_profile
            if profile_name not in self.vfs_registry.item_profile_map:
                raise ValueError(f"VFS profile '{profile_name}' not found in registry")
            if self.vfs_registry.item_vfs is None:
                raise ValueError("Item VFS storage not allocated in registry")
            for var_name, value in (initial_state or {}).items():
                self.vfs_registry.authorize_item_write(profile_name, var_name, writer="engine")
                overrides[var_name] = float(value)
        elif initial_state:
            raise ValueError("Item initial_state requires a declared VFS profile and registry")

        return overrides

    def spawn_item(
        self,
        world: int,
        item_type: str,
        position: Iterable[Any] | torch.Tensor,
        current_tick: int,
        initial_state: dict[str, float] | None = None,
    ) -> ItemInstance | None:
        """Spawn a new item instance into `world`.

        Args:
            world: The world the item lives in
            item_type: Item type ID from catalog
            position: Spawn position (grid or continuous coords)
            current_tick: Current environment tick
            initial_state: Optional VFS state overrides (e.g., {"durability": 50.0})

        Returns:
            ItemInstance if spawned, None if the world is at capacity or on cooldown
        """
        state = self.world_state(world)
        # Ground capacity is the declared max_items_in_world; the arena (free_rows,
        # checked below) also holds the world's carried items.
        if len(state.active) >= self.catalog.max_items_in_world:
            return None

        # Check cooldown
        if item_type in state.cooldown_until and current_tick < state.cooldown_until[item_type]:
            return None  # Still on cooldown

        # Get item type definition
        item_def = next((t for t in self.catalog.item_types if t.id == item_type), None)
        if item_def is None:
            raise KeyError(f"Unknown item type: {item_type}")

        overrides = self._authorize_spawn_state(item_type, initial_state)

        # Allocate an arena row of this world
        if not state.free_rows:
            return None  # No VFS slots available
        # Row selection depends only on available membership. set.pop() keeps
        # a hidden cursor which a refused effect cascade cannot restore.
        vfs_index = min(state.free_rows)
        state.free_rows.remove(vfs_index)

        # Initialize item VFS state from profile defaults + initial_state overrides
        if self.vfs_registry is not None and item_def.vfs_profile:
            profile_name = item_def.vfs_profile

            self.vfs_registry._initialize_item_row(profile_name, vfs_index)
            self.vfs_registry.register_item_instance(vfs_index, profile_name)

            # Authored overrides are writes, including overrides equal to a default.
            for var_name, value in overrides.items():
                self.vfs_registry.write_item(profile_name, var_name, value, vfs_index, writer="engine")

        instance = ItemInstance(
            item_type=item_type,
            instance_id=self.next_instance_id,
            position=self._position_key(position),
            vfs_index=vfs_index,
            vfs_profile=item_def.vfs_profile,  # Assign VFS profile from item type
            name=item_def.name,
            icon=item_def.icon,
            tags=tuple(item_def.tags),
            spawn_tick=current_tick,
            duration_total=item_def.duration,
            duration_remaining=item_def.duration,
            exclusive=item_def.exclusive,
        )
        self.next_instance_id += 1

        state.active[instance.instance_id] = instance
        self.live_items[instance.instance_id] = instance
        self._index_position(state, instance)

        self._log_items(
            "spawn_item",
            instance_id=instance.instance_id,
            item_type=item_type,
            world=world,
            position=instance.position,
            vfs_index=vfs_index,
        )
        return instance

    def lift_item(self, instance_id: int) -> ItemInstance | None:
        """Move an item from its world's ground to held state (pickup).

        Preserves item identity and VFS state. Item continues to tick.

        Returns:
            ItemInstance if lifted, None if not on the ground
        """
        item = self.live_items.get(instance_id)
        if item is None:
            return None
        state = self.worlds[self.world_of(item)]
        if instance_id not in state.active:
            return None
        if not item.exclusive:
            # Shared items stay in the world even when held.
            return item

        # Move from active to held (do NOT free the arena row - item still exists)
        state.held[instance_id] = state.active.pop(instance_id)
        self._unindex_position(state, item)
        return item

    def place_item(
        self,
        instance_id: int,
        position: Iterable[Any] | torch.Tensor,
    ) -> ItemInstance | None:
        """Move an item from held state back to its world's ground (drop).

        Preserves item identity and VFS state.

        Returns:
            ItemInstance if placed, None if not held
        """
        item = self.live_items.get(instance_id)
        if item is None:
            return None
        state = self.worlds[self.world_of(item)]
        if instance_id not in state.held:
            return None

        state.active[instance_id] = state.held.pop(instance_id)
        item.position = self._position_key(position)
        item.holder_agent_ids.clear()
        self._index_position(state, item)
        return item

    def despawn_item(self, instance_id: int, current_tick: int) -> None:
        """Despawn an item from its world (ground or held).

        Args:
            instance_id: Item instance ID to despawn
            current_tick: Current tick (for cooldown tracking)
        """
        item = self.live_items.pop(instance_id, None)
        if item is None:
            return  # Item not found
        world = self.world_of(item)
        state = self.worlds[world]
        if instance_id in state.active:
            del state.active[instance_id]
            self._unindex_position(state, item)
        else:
            del state.held[instance_id]

        # Unregister item instance from VFS registry
        if self.vfs_registry is not None:
            self.vfs_registry.unregister_item_instance(item.vfs_index)

        # Clean up inventory references (I2 memory leak fix)
        if self.inventory is not None:
            self.inventory.purge_instance(instance_id)

        # Discard the item's live effects and delayed work before its row is freed: an
        # effect outliving its item would read an unregistered row (and kill the batch).
        if self.effect_manager is not None:
            self.effect_manager.discard_item_effects(item.vfs_index)

        state.free_rows.add(item.vfs_index)

        # Set cooldown if configured
        item_def = next(t for t in self.catalog.item_types if t.id == item.item_type)
        if item_def.cooldown is not None:
            state.cooldown_until[item.item_type] = current_tick + item_def.cooldown

        # Set respawn timer if configured in appearance config
        # Note: Timer is per (world, item_type), not per instance. If multiple items
        # of the same type despawn, only the most recent despawn triggers respawn.
        if self.appearance_config is not None:
            rule = next(
                (r for r in self.appearance_config.items if r.item_type == item.item_type),
                None,
            )
            if rule is not None:
                self._arm_respawn_timer(world, rule, current_tick)

        self._log_items(
            "despawn_item",
            instance_id=instance_id,
            item_type=item.item_type,
            world=world,
            vfs_index=item.vfs_index,
            current_tick=current_tick,
        )

    def _arm_respawn_timer(self, world: int, rule: Any, current_tick: int) -> None:
        """Queue the rule's next spawn attempt in `world` from its declared schedule.

        Called when an item despawns and when a rule's `when:` predicate rejects a spawn
        in this world (initial or respawn), so a rejected rule retries on its declared
        period rather than never (initial) or every tick (respawn). A rule without a
        schedule queues nothing.
        """
        timers = self.worlds[world].respawn_timers
        schedule = rule.schedule
        if not isinstance(schedule, SpawnScheduleConfig):
            return
        if schedule.type == "periodic" and schedule.period is not None:
            timers[rule.item_type] = current_tick + schedule.period
        elif schedule.type == "normal" and schedule.mean is not None and schedule.std_dev is not None:
            next_tick = int(
                max(
                    0.0,
                    torch.normal(
                        mean=torch.tensor([float(schedule.mean)]),
                        std=torch.tensor([float(schedule.std_dev)]),
                        generator=self.world_rngs[world],
                    ).item(),
                )
            )
            timers[rule.item_type] = next_tick
        elif schedule.type == "poisson" and schedule.rate is not None and schedule.rate > 0:
            timers[rule.item_type] = current_tick + 1
        elif schedule.type == "time_window":
            if schedule.start_tick is not None and current_tick < schedule.start_tick:
                timers[rule.item_type] = schedule.start_tick
            else:
                timers[rule.item_type] = current_tick + 1

    def tick(self, current_tick: int) -> None:
        """Advance every world's item lifecycles by one tick.

        Args:
            current_tick: Current environment tick
        """
        # Ground and held items both expire (collected BEFORE ticking).
        expired = [instance_id for instance_id, item in self.live_items.items() if item.is_expired()]
        for instance_id in expired:
            self.despawn_item(instance_id, current_tick)

        # Tick all remaining items (AFTER despawning)
        for item in self.live_items.values():
            item.tick()

    def get_custom_action_specs(self) -> list[tuple[str, str, Literal["local", "inventory"], str]]:
        """Return (action_name, item_type, scope, command_name) tuples for custom item verbs."""
        return list(self.custom_action_specs)

    # -- spawn rules ------------------------------------------------------------------

    def _should_spawn_rule(
        self,
        rule: Any,
        *,
        bars: dict[str, torch.Tensor] | None,
    ) -> list[bool]:
        """The rule's spawn predicate per world, in the `SpawnPredicateReads` context.

        Every readable value has one row per world (S1), so the predicate is a `[N]`
        bool: each world decides its own spawn. There is no cross-world reduction.
        """
        if rule.when is None:
            return [True] * self.num_worlds

        if rule.when_ast is None:
            raise RuntimeError("Spawn condition provided without compiled AST. Run UniverseCompiler before using spawn conditions.")

        if bars is None:
            raise RuntimeError("Spawn conditions require bar context; pass bars when invoking spawn routines")

        context = SpawnPredicateReads.context(bars=bars, registry=self.vfs_registry, device=self.device)
        result = Evaluator(context).evaluate(rule.when_ast)
        values = torch.as_tensor(result, device=self.device).to(dtype=torch.bool)
        if values.numel() == 1:
            return [bool(values.item())] * self.num_worlds
        if tuple(values.shape) != (self.num_worlds,):
            raise RuntimeError(
                f"Spawn predicate {rule.when!r} for {rule.item_type!r} produced shape {tuple(values.shape)}; "
                f"it must give one value per world ({self.num_worlds})"
            )
        return [bool(v) for v in values.tolist()]

    def _placement_mode(self, rule: Any) -> str:
        placement = rule.placement
        return placement.mode if isinstance(placement, SpawnPlacementConfig) else "random"

    def _placement_positions(
        self,
        world: int,
        rule: Any,
        *,
        current_tick: int,
        count: int,
    ) -> list[tuple[int, ...] | tuple[float, ...]]:
        """Up to `count` positions in `world` for one spawn event of `rule`.

        random: the substrate's own position initialization (every substrate, any rank).
        fixed / grid / scripted: cells of a discrete grid. Every authored fixed and
        scripted cell is checked against the grid at compile ([ITEM-PLACEMENT-SUBSTRATE]).
        """
        mode = self._placement_mode(rule)
        placement = rule.placement
        positions: list[tuple[int, ...] | tuple[float, ...]] = []

        if mode == "random":
            if count <= 0:
                return positions
            drawn = self.substrate.initialize_positions(count, self.device, generator=self.world_rngs[world])
            return [self._position_key(row) for row in drawn.reshape(count, self.substrate.position_dim)]

        assert isinstance(placement, SpawnPlacementConfig)  # Type narrowing for mypy
        if mode == "fixed":
            for raw in placement.fixed_positions or []:
                if len(positions) >= count:
                    break
                cell = tuple(int(c) for c in raw)
                if not self._position_occupied(world, cell):
                    positions.append(cell)
            return positions

        if mode == "grid":
            spacing = placement.grid_spacing or 1
            for cell in self._grid_cells():
                if len(positions) >= count:
                    break
                if all(c % spacing == 0 for c in cell) and not self._position_occupied(world, cell):
                    positions.append(cell)
            return positions

        if mode == "scripted":
            script = placement.script or []
            indices = self.worlds[world].script_indices
            start_idx = indices.get(rule.item_type, 0)
            # Advance past events before current_tick
            while start_idx < len(script):
                tick = script[start_idx].get("tick")
                if tick is None or tick >= current_tick:
                    break
                start_idx += 1
            for idx in range(start_idx, len(script)):
                if len(positions) >= count:
                    break
                event = script[idx]
                tick = event.get("tick")
                if tick is None or tick != current_tick:
                    break
                cell = tuple(int(c) for c in event.get("position", ()))
                if not self._position_occupied(world, cell):
                    positions.append(cell)
                start_idx = idx + 1
            indices[rule.item_type] = start_idx
            return positions

        raise RuntimeError(f"Unknown item placement mode {mode!r}")

    def _next_script_tick(self, rule: Any, current_tick: int) -> int | None:
        if self._placement_mode(rule) != "scripted":
            return None
        assert isinstance(rule.placement, SpawnPlacementConfig)  # Type narrowing for mypy
        for event in rule.placement.script or []:
            tick = event.get("tick")
            if tick is not None and tick > current_tick:
                return int(tick)
        return None

    def _schedule_allows_spawn(self, world: int, rule: Any, current_tick: int) -> bool:
        """Check advanced schedule gating (time_window, poisson, normal) in `world`."""

        schedule = rule.schedule
        if not isinstance(schedule, SpawnScheduleConfig):
            return True

        if schedule.type == "time_window":
            if schedule.start_tick is not None and current_tick < schedule.start_tick:
                return False
            if schedule.end_tick is not None and current_tick > schedule.end_tick:
                return False
            return True

        if schedule.type == "poisson":
            rate = schedule.rate or 0.0
            if rate <= 0.0:
                return False
            prob = 1.0 - torch.exp(torch.tensor(-rate))
            if prob >= 0.9999:
                return True
            return bool(torch.rand((), device=self.device, generator=self.world_rngs[world]) < prob)

        if schedule.type == "normal":
            cursor = self.worlds[world].next_scheduled_tick
            next_tick = cursor.get(rule.item_type)
            if next_tick is None:
                next_tick = current_tick + 1
                cursor[rule.item_type] = next_tick
            if current_tick < next_tick:
                return False
            # Schedule next window based on mean (deterministic cadence)
            mean_tick = schedule.mean or 1.0
            cursor[rule.item_type] = int(max(current_tick + 1, math.ceil(mean_tick)))
            return True

        # periodic handled via timers, default allow here
        return True

    def spawn_initial_items(
        self,
        appearance_config: ItemsAppearanceConfig,
        current_tick: int,
        *,
        bars: dict[str, torch.Tensor] | None = None,
    ) -> None:
        """Spawn every world's level-start items from the level's spawn rules.

        Args:
            appearance_config: Level-specific item spawn rules
            current_tick: Current environment tick
        """
        # Store config for periodic respawning
        self.set_appearance_config(appearance_config)

        for rule in appearance_config.items:
            # Validate item type exists in catalog
            if not any(t.id == rule.item_type for t in self.catalog.item_types):
                # Skip unknown item types (e.g., energy_drink in test config)
                continue
            rule_key = self._rule_keys[id(rule)]
            count = rule.spawn_count
            spawn_ok: list[bool] | None = None
            for world in range(self.num_worlds):
                if not self._schedule_allows_spawn(world, rule, current_tick=current_tick):
                    continue
                if spawn_ok is None:
                    spawn_ok = self._should_spawn_rule(rule, bars=bars)
                if not spawn_ok[world]:
                    self._arm_respawn_timer(world, rule, current_tick)
                    continue
                if count <= 0:
                    continue
                counts = self.worlds[world].rule_spawn_counts
                current_total = counts.get(rule_key, 0)
                for position in self._placement_positions(world, rule, current_tick=current_tick, count=count):
                    if rule.max_total is not None and current_total >= rule.max_total:
                        continue
                    self.spawn_item(world, rule.item_type, position, current_tick)
                    current_total += 1
                    counts[rule_key] = current_total

    def set_appearance_config(self, appearance_config: ItemsAppearanceConfig) -> None:
        """Store the level's spawn rules for periodic respawning; reset every world's counters."""
        self.appearance_config = appearance_config
        self._rule_keys = {id(rule): f"rule_{idx}_{rule.item_type}" for idx, rule in enumerate(appearance_config.items)}
        for state in self.worlds:
            state.next_scheduled_tick.clear()
            state.script_indices.clear()
            state.rule_spawn_counts = dict.fromkeys(self._rule_keys.values(), 0)

    def process_respawns(
        self,
        current_tick: int,
        *,
        bars: dict[str, torch.Tensor] | None = None,
    ) -> None:
        """Process every world's item respawns from its own timers.

        Args:
            current_tick: Current environment tick
        """
        if self.appearance_config is None:
            return  # No appearance config, no respawning

        # The predicate is per world; evaluate it at most once per rule this tick.
        predicate: dict[int, list[bool]] = {}
        for world in range(self.num_worlds):
            self._process_world_respawns(world, current_tick, bars=bars, predicate=predicate)

    def _process_world_respawns(
        self,
        world: int,
        current_tick: int,
        *,
        bars: dict[str, torch.Tensor] | None,
        predicate: dict[int, list[bool]],
    ) -> None:
        assert self.appearance_config is not None
        state = self.worlds[world]
        timers = state.respawn_timers
        expired_types = [item_type for item_type, respawn_tick in timers.items() if current_tick >= respawn_tick]

        for item_type in expired_types:
            rule = next((r for r in self.appearance_config.items if r.item_type == item_type), None)
            if rule is None:
                # Rule removed from config, clear timer
                del timers[item_type]
                continue
            rule_key = self._rule_keys[id(rule)]
            schedule = rule.schedule

            if not self._schedule_allows_spawn(world, rule, current_tick=current_tick):
                # Reschedule according to schedule type
                if isinstance(schedule, SpawnScheduleConfig):
                    if schedule.type == "poisson" and schedule.rate and schedule.rate > 0:
                        timers[item_type] = current_tick + 1
                    elif schedule.type == "time_window":
                        if schedule.end_tick is not None and current_tick > schedule.end_tick:
                            del timers[item_type]
                        else:
                            timers[item_type] = max(current_tick + 1, schedule.start_tick or current_tick + 1)
                    elif schedule.type == "normal" and schedule.mean is not None and schedule.std_dev is not None:
                        sampled = torch.normal(
                            mean=torch.tensor([float(schedule.mean)]),
                            std=torch.tensor([float(schedule.std_dev)]),
                            generator=self.world_rngs[world],
                        ).item()
                        timers[item_type] = int(max(current_tick + 1, math.ceil(sampled)))
                continue

            if id(rule) not in predicate:
                predicate[id(rule)] = self._should_spawn_rule(rule, bars=bars)
            if not predicate[id(rule)][world]:
                self._arm_respawn_timer(world, rule, current_tick)
                continue

            current_total = state.rule_spawn_counts.get(rule_key, 0)
            if rule.max_total is not None and current_total >= rule.max_total:
                continue

            count = rule.spawn_count
            if count <= 0:
                del timers[item_type]
                continue
            spawned_any = False
            for position in self._placement_positions(world, rule, current_tick=current_tick, count=count):
                if self.spawn_item(world, item_type, position, current_tick) is not None:
                    spawned_any = True
                    state.rule_spawn_counts[rule_key] = current_total + 1
                    break  # respawn one per timer

            if spawned_any:
                next_script_tick = self._next_script_tick(rule, current_tick)
                if next_script_tick is not None:
                    timers[item_type] = next_script_tick
                else:
                    del timers[item_type]
            elif isinstance(schedule, SpawnScheduleConfig):
                # Reschedule retry
                if schedule.type == "poisson" and schedule.rate and schedule.rate > 0:
                    timers[item_type] = current_tick + 1
                elif schedule.type == "time_window":
                    timers[item_type] = max(current_tick + 1, schedule.start_tick or current_tick + 1)
                elif schedule.type == "normal" and schedule.mean is not None:
                    timers[item_type] = state.next_scheduled_tick.get(item_type, current_tick + 1)
