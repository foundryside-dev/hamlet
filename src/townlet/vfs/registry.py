"""Variable registry for VFS runtime storage.

The VariableRegistry manages runtime storage of VFS variables with access control
and scope semantics. It handles these scope patterns:

- global: World state, one row per world (shape [num_worlds] or [num_worlds, dims])
- agent: Per-agent values (shape [num_agents] or [num_agents, dims])

The batch is N independent single-agent worlds (owner ruling S1, 2026-10-25), so
``num_worlds == num_agents`` and world ``i`` is agent ``i``'s world. The world axis is
engine-internal: an author declares ``scope: global`` and reads it as one value in
their world. No reader or writer reduces across worlds.
- affordance: Per-affordance-instance values (shape [num_affordances, ...])

Item-scope state lives in the item arena (``item_vfs``), not in ordinary storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import torch

from townlet.vfs.access_policy import validate_static_access
from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.schema_hashes import compute_variable_schema_hash
from townlet.vfs.storage_dtype import storage_dtype

__all__ = [
    "VariableRegistry",
    "ScopeArena",
]


@dataclass(frozen=True)
class StaticAccessPolicy:
    """The immutable role authority for one runtime variable."""

    readable_by: tuple[str, ...]
    writable_by: tuple[str, ...]
    exposed_to: tuple[str, ...]


def _snapshot_access_policy(identifier: str, declaration: Any) -> StaticAccessPolicy:
    validate_static_access(identifier, declaration.readable_by, declaration.writable_by, declaration.exposed_to)
    return StaticAccessPolicy(tuple(declaration.readable_by), tuple(declaration.writable_by), tuple(declaration.exposed_to))


@dataclass(frozen=True)
class ScopeArena:
    """One per-scope storage arena (token-obs unit 3, Task 8 — the item_vfs shape).

    ``tensor`` is ``[rows, elements]`` float32 — ``num_worlds`` rows for the global
    scope, ``num_agents`` for the agent scope (equal under S1: one agent per world); ``index`` maps each backed variable id to its
    ``(offset, element_count)`` column span. Backed variables' registry storage tensors
    are VIEWS into this arena, so every write path (set / set_engine_value / lifetime
    reset) lands here with no sync step, and the token registry publisher reads one slab
    per scope — batched fills, never per-variable Python loops (hamlet-c7084169f7).
    """

    tensor: torch.Tensor
    index: dict[str, tuple[int, int]]


class VariableRegistry:
    """Runtime storage for VFS variables with access control.

    Examples:
        # Create registry with variables
        registry = VariableRegistry(
            variables=[
                VariableDef(id="energy", scope="agent", type="scalar", ...),
                VariableDef(id="position", scope="agent", type="vecNf", dims=2, ...),
            ],
            num_agents=4,
            device=torch.device("cpu"),
        )

        # Read variable (with access control)
        energy = registry.get("energy", reader="agent")

        # Write variable (with access control)
        registry.set("energy", new_values, writer="engine")
    """

    def __init__(
        self,
        variables: list[VariableDef],
        num_agents: int,
        device: torch.device,
        max_items: int = 0,
        item_profiles: dict[str, Any] | None = None,
        num_affordances: int = 0,
    ):
        """Initialize variable registry.

        Args:
            variables: List of variable definitions
            num_agents: Number of agents in the environment
            device: PyTorch device (cpu or cuda)
            max_items: Maximum items (for item-scoped variables)
            item_profiles: Compiled item profiles (profile_name → CompiledItemProfile)
            num_affordances: Number of affordance-scope rows
        """
        self.num_agents = num_agents
        # S1 (2026-10-25): the batch is independent single-agent worlds, so the global
        # scope's world axis has one row per agent. Agents-per-world > 1 is a future
        # declared parameter, not a reinterpretation of this axis.
        self.num_worlds = num_agents
        self.max_items = max_items
        self.num_affordances = num_affordances
        self.device = device
        self.item_profiles: dict[str, Any] = item_profiles or {}  # Store compiled profiles
        # Guardrail for tensor allocations
        self._max_tensor_elements = 1_000_000

        # Store variable definitions by ID, guarding against duplicate IDs
        self._definitions: dict[str, VariableDef] = {}
        self._access_policies: dict[str, StaticAccessPolicy] = {}
        self._item_access_policies: dict[tuple[str, str], StaticAccessPolicy] = {}
        for var in variables:
            if var.id in self._definitions:
                raise ValueError(f"Duplicate variable id '{var.id}' in registry initialization")
            self._access_policies[var.id] = _snapshot_access_policy(var.id, var)
            self._definitions[var.id] = var

        for profile_name, profile in self.item_profiles.items():
            for variable in profile.variables:
                key = (profile_name, variable.name)
                if key in self._item_access_policies:
                    raise ValueError(f"Duplicate item variable {key!r}")
                self._item_access_policies[key] = _snapshot_access_policy(f"{profile_name}.{variable.name}", variable)

        # Hash the same sealed policies used by checked access and publishers.
        self._identity_item_profiles = deepcopy(self.item_profiles)
        for profile_name, profile in self._identity_item_profiles.items():
            for variable in profile.variables:
                policy = self._item_access_policies[(profile_name, variable.name)]
                variable.readable_by = policy.readable_by
                variable.writable_by = policy.writable_by
                variable.exposed_to = policy.exposed_to

        # Initialize storage tensors. Per-scope arenas are allocated FIRST so that
        # float32-typed global/agent variables can be stored as views into them
        # (token-obs unit 3, Task 8 — see ScopeArena).
        self._storage: dict[str, torch.Tensor] = {}
        self._expected_shapes: dict[str, torch.Size] = {}
        self._expected_dtypes: dict[str, torch.dtype] = {}
        self._scope_arenas: dict[str, ScopeArena] = {}
        self._arena_backed: dict[str, str] = {}  # variable id -> arena scope key
        self._initialize_scope_arenas()
        self._initialize_storage()

        # Initialize item-scoped storage
        self.item_vfs: torch.Tensor | None = None
        self.item_profile_map: dict[str, dict[str, int]] = {}  # {profile_name → {var_name → index}}
        self.item_profile_type_map: dict[str, dict[str, str]] = {}  # {profile_name → {var_name → type}}
        self.item_vfs_index_to_profile: dict[int, str] = {}  # {vfs_index → profile_name}
        self._initialize_item_storage_from_profiles()

    @property
    def variables(self) -> dict[str, VariableDef]:
        """Get variable definitions dictionary.

        Returns:
            Dictionary mapping variable IDs to their definitions.

        Examples:
            # Check if variable exists
            if "energy" in registry.variables:
                var_def = registry.variables["energy"]
                print(f"Energy type: {var_def.type}")

            # Iterate over all variables
            for var_id, var_def in registry.variables.items():
                print(f"{var_id}: {var_def.scope}")
        """
        return self._definitions

    @property
    def variable_schema_hash(self) -> str:
        """Return the current variable schema hash for this registry."""
        definitions = [
            definition.model_copy(
                update={
                    "readable_by": list(self._access_policies[name].readable_by),
                    "writable_by": list(self._access_policies[name].writable_by),
                    "exposed_to": list(self._access_policies[name].exposed_to),
                }
            )
            for name, definition in self._definitions.items()
        ]
        return compute_variable_schema_hash(definitions, self._identity_item_profiles)

    @property
    def scope_arenas(self) -> dict[str, ScopeArena]:
        """The per-scope storage arenas (always both keys, `global` and `agent`).

        Consumed by the token registry publisher for batched per-scope fills.
        """
        return self._scope_arenas

    def _arena_scope_key(self, var_def: VariableDef) -> str | None:
        """Arena membership rule: float32-typed `global`/`agent` variables, nothing else.

        Integer/bool-typed variables keep standalone storage (the arena is float32, the value-token dtype);
        no shipped pack exposes one, and a compiled binding against one is refused by the
        publisher at construction.
        """
        scope = VariableScope(var_def.scope)
        if scope == VariableScope.GLOBAL:
            key = "global"
        elif scope == VariableScope.AGENT:
            key = "agent"
        else:
            return None
        return key if self._storage_dtype(var_def) == torch.float32 else None

    @staticmethod
    def _storage_dtype(var_def: VariableDef) -> torch.dtype:
        """The dtype _build_storage_tensor will allocate, decided without building it."""
        return storage_dtype(var_def.type)

    def _arena_element_count(self, var_def: VariableDef) -> int:
        """Per-row element count: the declared shape with the scope prefix stripped."""
        full_shape = self._compute_shape(var_def)
        prefix_len = len(self._scope_prefix_shape(var_def))
        count = 1
        for dim in full_shape[prefix_len:]:
            count *= dim
        return count

    def _initialize_scope_arenas(self) -> None:
        """Allocate the global/agent arenas from the declarations."""
        layouts: dict[str, dict[str, tuple[int, int]]] = {"global": {}, "agent": {}}
        offsets = {"global": 0, "agent": 0}
        for var_id, var_def in self._definitions.items():
            scope_key = self._arena_scope_key(var_def)
            if scope_key is None:
                continue
            count = self._arena_element_count(var_def)
            layouts[scope_key][var_id] = (offsets[scope_key], count)
            offsets[scope_key] += count
            self._arena_backed[var_id] = scope_key
        rows = {"global": self.num_worlds, "agent": self.num_agents}
        for scope_key in ("global", "agent"):
            self._scope_arenas[scope_key] = ScopeArena(
                tensor=torch.zeros((rows[scope_key], offsets[scope_key]), dtype=torch.float32, device=self.device),
                index=layouts[scope_key],
            )

    def _arena_storage_view(self, var_id: str, shape: torch.Size) -> torch.Tensor:
        """The arena-backed storage tensor for one variable: a VIEW, never a copy.

        `.view()` raises on copy by contract (spec §6 implementation constraint) — a
        silent `.reshape()` here would detach storage from the arena.
        """
        scope_key = self._arena_backed[var_id]
        arena = self._scope_arenas[scope_key]
        offset, count = arena.index[var_id]
        sliced = arena.tensor[:, offset : offset + count]
        if len(shape) == 1:
            return sliced.squeeze(1)
        return sliced.view(tuple(shape))

    def _write_storage(self, variable_id: str, value: torch.Tensor) -> None:
        """Commit a validated write: in place for arena-backed variables (the storage IS
        the arena view), defensive rebind-with-clone for everything else."""
        if variable_id in self._arena_backed:
            self._storage[variable_id].copy_(value)
        else:
            self._storage[variable_id] = value.clone()

    def _initialize_storage(self) -> None:
        """Initialize storage tensors with default values for all variables."""
        for var_id, var_def in self._definitions.items():
            tensor = self._build_storage_tensor(var_def)
            if var_id in self._arena_backed:
                view = self._arena_storage_view(var_id, tensor.shape)
                view.copy_(tensor)
                tensor = view
            self._storage[var_id] = tensor
            self._expected_shapes[var_id] = tensor.shape
            self._expected_dtypes[var_id] = tensor.dtype

    def _build_storage_tensor(self, var_def: VariableDef) -> torch.Tensor:
        """Build the initialized storage tensor for one variable definition."""
        shape = self._compute_shape(var_def)

        if var_def.type == "scalar":
            return torch.full(shape, var_def.default, device=self.device, dtype=torch.float32)
        if var_def.type in ("agent_ref", "item_ref", "affordance_ref", "effect_ref"):
            default_value = -1 if var_def.default is None else var_def.default
            return torch.full(shape, default_value, device=self.device, dtype=torch.long)
        if var_def.type in ("tensor1d", "tensor2d", "tensor3d", "tensorNd"):
            return self._initialize_tensor(var_def)
        if var_def.type in ("vecNi", "vecNf", "vec2i", "vec3i", "vec2f", "vec3f"):
            base_default = self._build_vector_default(var_def)
            if len(shape) == 1:
                return base_default.clone()
            prefix_shape = shape[:-1]
            return base_default.reshape((1,) * len(prefix_shape) + (base_default.shape[0],)).expand(shape).clone()
        if var_def.type == "bool":
            return torch.full(shape, var_def.default, device=self.device, dtype=torch.bool)
        raise ValueError(f"Unsupported variable type: {var_def.type}")

    def _compute_shape(self, var_def: VariableDef) -> tuple[int, ...]:
        """Compute tensor shape for a variable definition.

        Args:
            var_def: Variable definition

        Returns:
            Tuple representing tensor shape

        Examples:
            global scalar: (num_worlds,)
            global vector (dims=2): (num_worlds, 2)
            agent scalar: (num_agents,)
            agent vector (dims=2): (num_agents, 2)
        """
        prefix_shape = self._scope_prefix_shape(var_def)
        if var_def.type in ("scalar", "bool", "agent_ref", "item_ref", "affordance_ref", "effect_ref"):
            return prefix_shape
        if var_def.type in ("tensor1d", "tensor2d", "tensor3d", "tensorNd"):
            if not var_def.shape:
                raise ValueError(f"Tensor variable '{var_def.id}' requires a shape")
            return (*prefix_shape, *tuple(var_def.shape))

        elif var_def.type in {"vec2i", "vec2f"}:
            dims = 2
        elif var_def.type in {"vec3i", "vec3f"}:
            dims = 3
        elif var_def.type in ("vecNi", "vecNf"):
            if var_def.dims is None:
                raise ValueError(f"{var_def.type} variable '{var_def.id}' must have dims field defined")
            dims = var_def.dims
        else:
            raise ValueError(f"Unsupported variable type: {var_def.type}")

        return (*prefix_shape, dims)

    def _scope_prefix_shape(self, var_def: VariableDef) -> tuple[int, ...]:
        """Return the leading tensor dimensions implied by a variable scope."""
        scope = VariableScope(var_def.scope)
        if scope == VariableScope.GLOBAL:
            return (self.num_worlds,)
        if scope == VariableScope.AGENT:
            return (self.num_agents,)
        if scope == VariableScope.AFFORDANCE:
            if self.num_affordances <= 0:
                raise ValueError(f"Variable '{var_def.id}' uses affordance scope but num_affordances must be positive")
            return (self.num_affordances,)
        if scope == VariableScope.ITEM:
            raise ValueError(
                "Item-scoped state requires an item arena and a declared item profile; it cannot enter ordinary registry storage."
            )
        raise ValueError(f"Unsupported variable scope: {var_def.scope}")

    def get(self, variable_id: str, reader: str) -> torch.Tensor:
        """Get variable value with access control.

        Args:
            variable_id: ID of the variable to read
            reader: Explicit engine or agent role

        Returns:
            Tensor containing the variable value

        Raises:
            KeyError: If variable_id doesn't exist
            PermissionError: If reader not allowed to read this variable

        Examples:
            # Read energy (agent scope)
            energy = registry.get("energy", reader="agent")
            # Returns: tensor([1.0, 1.0, 1.0, 1.0])  # shape [num_agents]

            # Read global time_sin: one value per world
            time_sin = registry.get("time_sin", reader="agent")
            # Returns: tensor([0.0, 0.0, 0.0, 0.0])  # shape [num_worlds]
        """
        self._validate_actor(reader, "read", variable_id)
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        self.authorize_read(variable_id, reader=reader)
        value = self._storage[variable_id]

        return value.clone()

    def set(self, variable_id: str, value: torch.Tensor, writer: str) -> None:
        """Set variable value with access control.

        Args:
            variable_id: ID of the variable to write
            value: New tensor value
            writer: Explicit role; only engine writes may be declared

        Raises:
            KeyError: If variable_id doesn't exist
            PermissionError: If writer not allowed to write this variable

        Examples:
            # Update energy for all agents
            new_energy = torch.tensor([0.9, 0.8, 0.7, 0.6])
            registry.set("energy", new_energy, writer="engine")

            # Update global time_sin in every world
            registry.set("time_sin", torch.full((registry.num_worlds,), 0.707), writer="engine")
        """
        self._validate_actor(writer, "write", variable_id)
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        self.authorize_write(variable_id, writer=writer)
        self._validate_write(variable_id, value)
        self._write_storage(variable_id, value.to(self.device))

    def set_engine_value(self, variable_id: str, value: torch.Tensor) -> None:
        """Write evaluator/VTC output as the engine under the same checks as ``set``.

        Public, permission-checked write-back path for VTC commits and profile
        expression write-backs. It validates the declared shape and dtype exactly as
        ``set`` does — it neither bypasses the declared shape (a global scalar holds
        exactly one value per world, ``[num_worlds]``) nor coerces dtype (hamlet-2ca2cb373f: a float into a bool target is refused,
        not truncated). Callers produce storage-typed values; the one admitted
        conversion, integer widening into float32, lives in ``to_storage_dtype``.
        """
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        self.authorize_write(variable_id, writer="engine")
        self._validate_write(variable_id, value)
        self._write_storage(variable_id, value.to(self.device))

    def _validate_write(self, variable_id: str, value: torch.Tensor) -> None:
        """The one shape-and-dtype check every registry write passes through."""
        expected_shape = self._expected_shapes[variable_id]
        expected_dtype = self._expected_dtypes[variable_id]
        if value.shape != expected_shape:
            raise ValueError(f"Value for '{variable_id}' has shape {tuple(value.shape)}, expected {tuple(expected_shape)}")
        if value.dtype != expected_dtype:
            raise ValueError(f"Value for '{variable_id}' has dtype {value.dtype}, expected {expected_dtype}")

    def reset_tick_scoped(self) -> None:
        """Re-initialize tick-lifetime variables."""
        self._reset_lifetimes({"tick"})

    def reset_episode_scoped(self) -> None:
        """Re-initialize tick- and episode-lifetime variables; persistent state is kept."""
        self._reset_lifetimes({"tick", "episode"})

    def _reset_lifetimes(self, lifetimes: AbstractSet[str]) -> None:
        """A reset IS re-initialization: the declared initializer runs again.

        A literal or deterministic mode (zeros/ones/eye) therefore restores the same
        value; a random mode (random_normal/random_uniform) draws afresh from torch's
        global RNG, the stream ``seed_all`` seeds and that agent placement also samples,
        so each reset is reproducible per seed rather than a frozen first draw.
        """
        for var_id, var_def in self._definitions.items():
            if str(var_def.lifetime) in lifetimes:
                self._write_storage(var_id, self._build_storage_tensor(var_def))

    def _persistent_ids(self) -> tuple[str, ...]:
        return tuple(var_id for var_id, var_def in self._definitions.items() if str(var_def.lifetime) == "persistent")

    def persistent_state(self) -> dict[str, torch.Tensor]:
        """Capture exactly the persistent-lifetime storage, for checkpoint resume.

        Tick and episode lifetimes are re-initialized by every reset, so a resume never
        needs them and they are not captured. Item variables are episode lifetime by
        declaration, so the item arena is never persistent. Values are detached CPU
        copies: the snapshot never aliases live storage and loads on any device.
        """
        return {var_id: self._storage[var_id].detach().to("cpu").clone() for var_id in self._persistent_ids()}

    def validate_persistent_state(self, state: Mapping[str, torch.Tensor]) -> None:
        """Refuse a snapshot whose ids, shapes or dtypes differ from this registry.

        The checkpoint identity gate compares ``vfs_hash`` and ``variables_hash`` before
        any restore, so a mismatch here is unreachable for a checkpoint of this universe:
        reaching it is an engine defect, and it raises rather than restoring a subset.
        """
        expected = set(self._persistent_ids())
        actual = set(state)
        if actual != expected:
            raise RuntimeError(
                "Engine defect: persistent VFS state does not match the compiled registry "
                f"(missing={sorted(expected - actual)}, unknown={sorted(actual - expected)}); "
                "the checkpoint identity gate should have refused it."
            )
        for var_id in sorted(expected):
            value = state[var_id]
            if not isinstance(value, torch.Tensor):
                raise RuntimeError(f"Engine defect: persistent VFS state '{var_id}' is {type(value).__name__}, not a tensor.")
            if value.shape != self._expected_shapes[var_id] or value.dtype != self._expected_dtypes[var_id]:
                raise RuntimeError(
                    f"Engine defect: persistent VFS state '{var_id}' has shape {tuple(value.shape)} dtype {value.dtype}, "
                    f"expected {tuple(self._expected_shapes[var_id])} dtype {self._expected_dtypes[var_id]}; "
                    "the checkpoint identity gate should have refused it."
                )

    def restore_persistent_state(self, state: Mapping[str, torch.Tensor]) -> None:
        """Restore a ``persistent_state`` snapshot onto this registry's device.

        Every entry is validated before any is written, so a refusal applies nothing.
        Writes go through the arena-aware storage commit, never a rebind.
        """
        self.validate_persistent_state(state)
        for var_id in self._persistent_ids():
            self._write_storage(var_id, state[var_id].to(self.device))

    def _get_vector_dims(self, var_def: VariableDef) -> int:
        """Return expected dimensionality for vector variables."""
        if var_def.type in {"vec2i", "vec2f"}:
            return 2
        if var_def.type in {"vec3i", "vec3f"}:
            return 3
        if var_def.type in ("vecNi", "vecNf"):
            if var_def.dims is None:
                raise ValueError(f"Variable '{var_def.id}' missing 'dims' for type '{var_def.type}'")
            return var_def.dims
        default_list = var_def.default
        if isinstance(default_list, list):
            return len(default_list)
        raise ValueError(f"Variable '{var_def.id}' must provide default list for type '{var_def.type}'")

    def _build_vector_default(self, var_def: VariableDef) -> torch.Tensor:
        """Build default tensor for vector variables, padding if necessary."""
        dims = self._get_vector_dims(var_def)
        dtype = torch.long if var_def.type in ("vecNi", "vec2i", "vec3i") else torch.float32
        tensor = torch.zeros(dims, device=self.device, dtype=dtype)

        default_values = var_def.default
        if isinstance(default_values, list) and default_values:
            copy_len = min(len(default_values), dims)
            default_tensor = torch.tensor(default_values[:copy_len], device=self.device, dtype=dtype)
            tensor[:copy_len] = default_tensor
        return tensor

    def _initialize_tensor(self, var_def: VariableDef) -> torch.Tensor:
        """Initialize tensor variables (tensor1d/2d/3d/Nd) with optional modes."""
        if not var_def.shape:
            raise ValueError(f"Tensor variable '{var_def.id}' is missing required shape")

        payload_shape = tuple(var_def.shape)
        full_shape = self._compute_shape(var_def)
        prefix_shape = full_shape[: len(full_shape) - len(payload_shape)]
        total_elements = 1
        for dim in full_shape:
            total_elements *= dim
        if total_elements > self._max_tensor_elements:
            raise ValueError(
                f"Tensor variable '{var_def.id}' shape {list(full_shape)} exceeds max supported elements ({self._max_tensor_elements})."
            )
        mode = var_def.initial_value_mode or "zeros"
        params = var_def.initial_value_params or {}

        if mode == "zeros":
            base = torch.zeros(full_shape, device=self.device, dtype=torch.float32)
        elif mode == "ones":
            base = torch.ones(full_shape, device=self.device, dtype=torch.float32)
        elif mode == "eye":
            if len(payload_shape) != 2 or payload_shape[0] != payload_shape[1]:
                raise ValueError(f"initial_value_mode 'eye' requires square 2D shape; got {list(payload_shape)}")
            base = torch.eye(payload_shape[0], device=self.device, dtype=torch.float32)
            if prefix_shape:
                base = base.reshape((1,) * len(prefix_shape) + payload_shape).expand(full_shape).clone()
        elif mode == "random_normal":
            mean = float(params.get("mean", 0.0))
            std = float(params.get("std", 1.0))
            base = torch.normal(mean, std, size=full_shape, device=self.device)
        elif mode == "random_uniform":
            low = float(params.get("low", 0.0))
            high = float(params.get("high", 1.0))
            base = torch.rand(full_shape, device=self.device) * (high - low) + low
        else:
            raise ValueError(f"Unknown initial_value_mode '{mode}' for tensor variable '{var_def.id}'")

        if var_def.default is not None:
            # Allow explicit default override if provided; broadcast if necessary.
            explicit = torch.tensor(var_def.default, device=self.device, dtype=torch.float32)
            if prefix_shape:
                if explicit.dim() == len(payload_shape):
                    explicit = explicit.reshape((1,) * len(prefix_shape) + tuple(explicit.shape))
                elif explicit.dim() == len(payload_shape) + len(prefix_shape):
                    leading_shape = explicit.shape[: len(prefix_shape)]
                    invalid_dims = [
                        (actual, expected)
                        for actual, expected in zip(leading_shape, prefix_shape, strict=True)
                        if actual not in {1, expected}
                    ]
                    if invalid_dims:
                        raise ValueError(
                            f"Default for tensor variable '{var_def.id}' must have leading scope dims "
                            f"broadcastable to {tuple(prefix_shape)}, got {tuple(leading_shape)}"
                        )

            if explicit.shape == torch.Size(full_shape):
                pass
            else:
                try:
                    explicit = explicit.expand(full_shape)
                except RuntimeError as exc:
                    raise ValueError(
                        f"Cannot broadcast default for tensor variable '{var_def.id}' from shape {tuple(explicit.shape)} "
                        f"to {tuple(full_shape)}"
                    ) from exc
            base = explicit.clone()

        return base

    def _initialize_item_storage_from_profiles(self) -> None:
        """Initialize item VFS storage from compiled profiles.

        Creates:
        - item_vfs: [max_items, max_profile_vars] tensor
        - item_profile_map: {profile_name → {var_name → tensor_index}}

        Item storage is profile-agnostic: all profiles share the same tensor layout
        using max_profile_vars across all profiles. Unused slots are masked.
        """
        item_vars = [v for v in self._definitions.values() if v.scope == VariableScope.ITEM]
        if item_vars:
            raise ValueError(
                "Item-scoped state requires an item arena and a declared item profile; it cannot enter ordinary registry storage."
            )

        if self.max_items > 0 and not self.item_profiles:
            raise ValueError("Item VFS requested (max_items>0) but no item_profiles were provided.")

        if not self.item_profiles or self.max_items == 0:
            self.item_vfs = None
            self.item_profile_map = {}
            return

        max_vars = 0
        for profile in self.item_profiles.values():
            max_vars = max(max_vars, len(profile.variables))

        self.item_vfs = torch.zeros(
            (self.max_items, max_vars),
            dtype=torch.float32,
            device=self.device,
        )

        for profile_name, profile in self.item_profiles.items():
            var_map = {}
            type_map = {}
            for idx, var in enumerate(profile.variables):
                var_map[var.name] = idx
                type_map[var.name] = getattr(var, "type", "scalar")
            self.item_profile_map[profile_name] = var_map
            self.item_profile_type_map[profile_name] = type_map

    def get_access_policy(self, variable_id: str) -> StaticAccessPolicy:
        """Return the validated runtime policy, independent of mutable DTO lists."""
        return self._access_policies[variable_id]

    def get_item_access_policy(self, profile_name: str, variable_id: str) -> StaticAccessPolicy:
        """Return the qualified policy; shared arena columns are not variable identity."""
        return self._item_access_policies[(profile_name, variable_id)]

    @staticmethod
    def _validate_actor(actor: str, operation: str, identifier: str) -> None:
        if not isinstance(actor, str) or actor not in ("engine", "agent"):
            raise PermissionError(
                f"Unknown actor '{actor}' for {operation} of variable '{identifier}'; supported roles are engine and agent"
            )

    def authorize_read(self, variable_id: str, *, reader: str) -> None:
        """Authorize an ordinary read without touching storage."""
        self._validate_actor(reader, "read", variable_id)
        policy = self.get_access_policy(variable_id)
        if reader not in policy.readable_by:
            raise PermissionError(
                f"Actor '{reader}' is not allowed to read {self._definitions[variable_id].scope} variable '{variable_id}'"
            )

    def authorize_write(self, variable_id: str, *, writer: str) -> None:
        """Authorize an attempted ordinary write, even if its value is unchanged."""
        self._validate_actor(writer, "write", variable_id)
        if writer not in self.get_access_policy(variable_id).writable_by:
            raise PermissionError(f"Actor '{writer}' is not allowed to write variable '{variable_id}'")

    def authorize_item_read(self, profile_name: str, variable_id: str, *, reader: str) -> None:
        """Authorize a qualified item read without accessing the arena."""
        self._validate_actor(reader, "read", f"{profile_name}.{variable_id}")
        if reader not in self.get_item_access_policy(profile_name, variable_id).readable_by:
            raise PermissionError(f"Actor '{reader}' is not allowed to read item variable '{profile_name}.{variable_id}'")

    def authorize_item_write(self, profile_name: str, variable_id: str, *, writer: str) -> None:
        """Authorize a qualified item write before arena mutation."""
        self._validate_actor(writer, "write", f"{profile_name}.{variable_id}")
        if writer not in self.get_item_access_policy(profile_name, variable_id).writable_by:
            raise PermissionError(f"Actor '{writer}' is not allowed to write item variable '{profile_name}.{variable_id}'")

    def _validate_item_row(self, profile_name: str, vfs_index: int) -> None:
        if not 0 <= vfs_index < self.max_items:
            raise IndexError(f"Item row {vfs_index} is outside the declared arena")
        actual = self.item_vfs_index_to_profile.get(vfs_index)
        if actual != profile_name:
            raise PermissionError(f"Item row {vfs_index} has profile '{actual}', not '{profile_name}'")

    def _initialize_item_row(self, profile_name: str, vfs_index: int) -> None:
        """Trusted allocation lifecycle; authored overrides use checked write_item."""
        if self.item_vfs is None:
            raise RuntimeError("Item VFS storage not allocated")
        self.item_vfs[vfs_index].zero_()
        profile = self.item_profiles[profile_name]
        for variable in profile.variables:
            if variable.initial_value is not None:
                self.item_vfs[vfs_index, self.item_profile_map[profile_name][variable.name]] = float(variable.initial_value)

    def write_item(self, profile_name: str, var_name: str, value: float | torch.Tensor, vfs_index: int, *, writer: str) -> None:
        """Write item variable value.

        Args:
            profile_name: Item profile name (e.g., "medical", "food")
            var_name: Variable name
            value: New value
            vfs_index: Item VFS index (row in item_vfs tensor)

        Raises:
            RuntimeError: If item storage not allocated
            KeyError: If profile or variable not found
        """
        self.authorize_item_write(profile_name, var_name, writer=writer)
        self._validate_item_row(profile_name, vfs_index)
        if self.item_vfs is None:
            raise RuntimeError("Item VFS storage not allocated")
        if profile_name not in self.item_profile_map:
            raise KeyError(f"Item profile '{profile_name}' not found. Available: {list(self.item_profile_map.keys())}")
        profile_vars = self.item_profile_map[profile_name]
        if var_name not in profile_vars:
            raise KeyError(f"Variable '{var_name}' not found in profile '{profile_name}'. Available: {list(profile_vars.keys())}")
        var_idx = profile_vars[var_name]
        self.item_vfs[vfs_index, var_idx] = value

    def read_item(self, profile_name: str, var_name: str, vfs_index: int, *, reader: str) -> float:
        """Read item variable value.

        Args:
            profile_name: Item profile name (e.g., "medical", "food")
            var_name: Variable name
            vfs_index: Item VFS index (row in item_vfs tensor)

        Returns:
            Variable value as Python float

        Raises:
            RuntimeError: If item storage not allocated
            KeyError: If profile or variable not found
        """
        self.authorize_item_read(profile_name, var_name, reader=reader)
        self._validate_item_row(profile_name, vfs_index)
        if self.item_vfs is None:
            raise RuntimeError("Item VFS storage not allocated")
        if profile_name not in self.item_profile_map:
            raise KeyError(f"Item profile '{profile_name}' not found. Available: {list(self.item_profile_map.keys())}")
        profile_vars = self.item_profile_map[profile_name]
        if var_name not in profile_vars:
            raise KeyError(f"Variable '{var_name}' not found in profile '{profile_name}'. Available: {list(profile_vars.keys())}")
        var_idx = profile_vars[var_name]
        return self.item_vfs[vfs_index, var_idx].item()

    def register_item_instance(self, vfs_index: int, profile_name: str) -> None:
        """Register mapping from vfs_index to profile for an item instance.

        Args:
            vfs_index: Item VFS index
            profile_name: Item profile name

        Raises:
            ValueError: If profile not found
        """
        if profile_name not in self.item_profile_map:
            raise ValueError(f"Profile '{profile_name}' not found. Available: {list(self.item_profile_map.keys())}")
        self.item_vfs_index_to_profile[vfs_index] = profile_name

    def unregister_item_instance(self, vfs_index: int) -> None:
        """Unregister item instance when despawned.

        Args:
            vfs_index: Item VFS index
        """
        self.item_vfs_index_to_profile.pop(vfs_index, None)

    def get_variable_type(self, variable_id: str) -> str | None:
        """Return declared type for a variable (agent/global scopes)."""
        var = self._definitions.get(variable_id)
        return getattr(var, "type", None) if var else None

    def get_item_variable_type(self, profile_name: str, variable_id: str) -> str | None:
        """Return declared type for an item-scoped variable."""
        return self.item_profile_type_map.get(profile_name, {}).get(variable_id)

    def get_item_profile_for_index(self, vfs_index: int) -> str | None:
        """Return profile name for a given item VFS index (if registered)."""
        return self.item_vfs_index_to_profile.get(vfs_index)
