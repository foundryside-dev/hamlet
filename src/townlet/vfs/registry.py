"""Variable registry for VFS runtime storage.

The VariableRegistry manages runtime storage of VFS variables with access control
and scope semantics. It handles these scope patterns:

- global: Single value shared by all agents (shape [] or [dims])
- agent: Per-agent values, observable by all (shape [num_agents] or [num_agents, dims])
- agent_private: Per-agent values, observable only by owner (shape [num_agents] or [num_agents, dims])
- pair: Directed agent-agent values (dense shape [num_agents, num_agents, ...] or sparse shape [num_pair_edges, ...])
- group: Group/faction/team values (shape [num_groups, ...])
- affordance: Per-affordance-instance values (shape [num_affordances, ...])
- zone: Per-zone values (shape [num_zones, ...])
- message: Recent message buffer values (shape [num_agents, num_message_slots, ...])
"""

from __future__ import annotations

from collections.abc import Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

import torch

from townlet.vfs.schema import VariableDef, VariableScope
from townlet.vfs.schema_hashes import compute_variable_schema_hash

if TYPE_CHECKING:
    pass  # CompiledItemProfile not needed for type checking

__all__ = [
    "VariableRegistry",
    "ScopeArena",
    "ScopedVariableRegistry",
    "VFSRegistryProtocol",
    "AccessDeniedError",
    "DynamicVariableMutation",
]


@dataclass(frozen=True)
class ScopeArena:
    """One per-scope storage arena (token-obs unit 3, Task 8 — the item_vfs shape).

    ``tensor`` is ``[rows, elements]`` float32 — rows 1 for the global scope,
    ``num_agents`` for the agent scope; ``index`` maps each backed variable id to its
    ``(offset, element_count)`` column span. Backed variables' registry storage tensors
    are VIEWS into this arena, so every write path (set / set_engine_value / lifetime
    reset) lands here with no sync step, and the token registry publisher reads one slab
    per scope — batched fills, never per-variable Python loops (hamlet-c7084169f7).

    `agent_private` is excluded by construction: the arenas exist to feed observation,
    and the publisher (`environment/token_publishers.py`) is the enforcement point for
    the hamlet-83a043a9b9 boundary.
    """

    tensor: torch.Tensor
    index: dict[str, tuple[int, int]]


NetworkShapeEffect = Literal["shape_stable_internal", "observation_schema_changed"]
_NETWORK_SHAPE_EFFECTS = {"shape_stable_internal", "observation_schema_changed"}


@dataclass(frozen=True)
class DynamicVariableMutation:
    """Audit record for an explicitly gated runtime variable mutation."""

    operation: Literal["add", "remove"]
    variable_id: str
    network_shape_effect: NetworkShapeEffect
    shape: tuple[int, ...]
    dtype: str
    variable_schema_hash: str


class AccessDeniedError(Exception):
    """Raised when access control check fails."""

    pass


@runtime_checkable
class VFSRegistryProtocol(Protocol):
    """Observation-facing registry contract shared by runtime registry variants."""

    device: torch.device
    item_vfs: torch.Tensor | None
    item_profile_map: dict[str, dict[str, int]]
    item_vfs_index_to_profile: dict[int, str]

    def list_global(self) -> list[str]: ...

    def get_global(self, name: str) -> torch.Tensor: ...

    def list_agent(self) -> list[str]: ...

    def get_agent(self, name: str) -> torch.Tensor: ...


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
        num_groups: int = 0,
        num_affordances: int = 0,
        num_zones: int = 0,
        num_message_slots: int = 0,
        dynamic_variable_mode: bool = False,
        pair_storage_mode: Literal["dense", "sparse"] = "dense",
        pair_edges: torch.Tensor | Sequence[Sequence[int]] | None = None,
    ):
        """Initialize variable registry.

        Args:
            variables: List of variable definitions
            num_agents: Number of agents in the environment
            device: PyTorch device (cpu or cuda)
            max_items: Maximum items (for item-scoped variables)
            item_profiles: Compiled item profiles (profile_name → CompiledItemProfile)
            num_groups: Number of group-scope rows
            num_affordances: Number of affordance-scope rows
            num_zones: Number of zone-scope rows
            num_message_slots: Number of recent-message buffer slots per agent
            dynamic_variable_mode: Allow explicit add/remove of variable definitions during a run
            pair_storage_mode: Pair-scope allocation strategy, either dense all-pairs or sparse edge rows
            pair_edges: Directed pair edges as [num_pair_edges, 2], required for sparse pair variables
        """
        self.num_agents = num_agents
        self.max_items = max_items
        self.num_groups = num_groups
        self.num_affordances = num_affordances
        self.num_zones = num_zones
        self.num_message_slots = num_message_slots
        self.dynamic_variable_mode = dynamic_variable_mode
        self.pair_storage_mode = pair_storage_mode
        self.device = device
        self.item_profiles: dict[str, Any] = item_profiles or {}  # Store compiled profiles
        self._dynamic_variable_mutations: list[DynamicVariableMutation] = []
        self.variable_schema_generation = 0
        # Guardrail for tensor allocations
        self._max_tensor_elements = 1_000_000

        # Store variable definitions by ID, guarding against duplicate IDs
        self._definitions: dict[str, VariableDef] = {}
        for var in variables:
            if var.id in self._definitions:
                raise ValueError(f"Duplicate variable id '{var.id}' in registry initialization")
            self._definitions[var.id] = var

        self._pair_edges: torch.Tensor | None = None
        self._pair_edge_to_index: dict[tuple[int, int], int] = {}
        self._initialize_pair_storage_index(pair_edges)

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
        self._initial_storage: dict[str, torch.Tensor] = {name: value.clone() for name, value in self._storage.items()}

        # Initialize item-scoped storage
        self.item_vfs: torch.Tensor | None = None
        self.item_var_to_index: dict[str, int] = {}
        self.item_profile_map: dict[str, dict[str, int]] = {}  # {profile_name → {var_name → index}}
        self.item_profile_type_map: dict[str, dict[str, str]] = {}  # {profile_name → {var_name → type}}
        self.item_vfs_index_to_profile: dict[int, str] = {}  # {vfs_index → profile_name}
        self._initialize_item_storage_from_profiles()

        # Guardrail for tensor allocations
        self._max_tensor_elements = 1_000_000

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
    def dynamic_variable_mutations(self) -> tuple[DynamicVariableMutation, ...]:
        """Return runtime variable mutation audit records."""
        return tuple(self._dynamic_variable_mutations)

    @property
    def variable_schema_hash(self) -> str:
        """Return the current variable schema hash for this registry."""
        return compute_variable_schema_hash(self._definitions.values())

    def _initialize_pair_storage_index(self, pair_edges: torch.Tensor | Sequence[Sequence[int]] | None) -> None:
        """Validate and store sparse pair topology metadata."""
        if self.pair_storage_mode not in {"dense", "sparse"}:
            raise ValueError("pair_storage_mode must be either 'dense' or 'sparse'")

        has_pair_variables = any(VariableScope(var.scope) == VariableScope.PAIR for var in self._definitions.values())

        if self.pair_storage_mode == "dense":
            if pair_edges is not None:
                raise ValueError("pair_edges may only be provided when pair_storage_mode='sparse'")
            return

        if pair_edges is None:
            if has_pair_variables:
                raise ValueError("pair_edges must be provided when pair_storage_mode='sparse' and pair variables are declared")
            self._pair_edges = torch.empty((0, 2), dtype=torch.long, device=self.device)
            return

        self._pair_edges = self._coerce_pair_edges(pair_edges)
        self._pair_edge_to_index = {
            (int(source_agent), int(target_agent)): edge_index
            for edge_index, (source_agent, target_agent) in enumerate(self._pair_edges.detach().cpu().tolist())
        }

    def _coerce_pair_edges(self, pair_edges: torch.Tensor | Sequence[Sequence[int]]) -> torch.Tensor:
        """Return validated directed pair edges as a long tensor on the registry device."""
        if isinstance(pair_edges, torch.Tensor):
            raw_edges = pair_edges.to(device=self.device)
        elif len(pair_edges) == 0:
            raw_edges = torch.empty((0, 2), dtype=torch.long, device=self.device)
        else:
            raw_edges = torch.as_tensor(pair_edges, device=self.device)

        if raw_edges.dtype.is_floating_point or raw_edges.dtype.is_complex or raw_edges.dtype == torch.bool:
            raise ValueError("pair_edges must contain integer agent indices")
        if raw_edges.ndim != 2 or raw_edges.shape[1] != 2:
            raise ValueError(f"pair_edges must have shape [num_pair_edges, 2], got {tuple(raw_edges.shape)}")

        edges = raw_edges.to(dtype=torch.long).contiguous()
        if edges.numel() > 0 and ((edges < 0).any() or (edges >= self.num_agents).any()):
            raise ValueError(f"pair_edges contain agent indices out of range for num_agents={self.num_agents}")

        seen_edges: set[tuple[int, int]] = set()
        for source_agent, target_agent in edges.detach().cpu().tolist():
            edge = (int(source_agent), int(target_agent))
            if edge in seen_edges:
                raise ValueError(f"pair_edges contain duplicate directed edge {edge}")
            seen_edges.add(edge)

        return edges

    def _require_sparse_pair_edges(self) -> torch.Tensor:
        """Return sparse pair edges or fail loudly when pair storage is dense."""
        if self.pair_storage_mode != "sparse" or self._pair_edges is None:
            raise ValueError("Sparse pair edge metadata requires pair_storage_mode='sparse'")
        return self._pair_edges

    def get_pair_edges(self) -> torch.Tensor:
        """Return directed sparse pair edges as [num_pair_edges, 2]."""
        return self._require_sparse_pair_edges().clone()

    def get_pair_mask(self) -> torch.Tensor:
        """Return a dense boolean neighbourhood mask for sparse pair edges."""
        pair_edges = self._require_sparse_pair_edges()
        mask = torch.zeros((self.num_agents, self.num_agents), dtype=torch.bool, device=self.device)
        if pair_edges.numel() > 0:
            mask[pair_edges[:, 0], pair_edges[:, 1]] = True
        return mask

    def get_pair_edge_index(self, source_agent: int, target_agent: int) -> int:
        """Return the sparse row index for a directed active pair relationship."""
        self._require_sparse_pair_edges()
        edge = (int(source_agent), int(target_agent))
        if edge not in self._pair_edge_to_index:
            raise KeyError(f"Pair edge {edge} is not active in sparse pair storage")
        return self._pair_edge_to_index[edge]

    def materialize_pair_dense(self, variable_id: str, reader: str, fill_value: float | int | bool | None = None) -> torch.Tensor:
        """Materialize a sparse pair variable into a dense diagnostic view."""
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        var_def = self._definitions[variable_id]
        if VariableScope(var_def.scope) != VariableScope.PAIR:
            raise ValueError(f"Variable '{variable_id}' is not pair-scoped (scope: {var_def.scope})")

        pair_edges = self._require_sparse_pair_edges()
        sparse_values = self.get(variable_id, reader=reader)
        dense_shape = (self.num_agents, self.num_agents, *tuple(sparse_values.shape[1:]))
        dense = torch.full(
            dense_shape,
            self._pair_dense_fill_value(var_def) if fill_value is None else fill_value,
            dtype=sparse_values.dtype,
            device=self.device,
        )
        if pair_edges.numel() > 0:
            dense[pair_edges[:, 0], pair_edges[:, 1]] = sparse_values
        return dense

    def _pair_dense_fill_value(self, var_def: VariableDef) -> float | int | bool:
        """Return a scalar fill value for sparse-pair dense diagnostic views."""
        if var_def.type in ("agent_ref", "item_ref", "affordance_ref", "effect_ref"):
            return -1 if var_def.default is None else int(var_def.default)
        if var_def.type == "bool":
            return bool(var_def.default)
        if isinstance(var_def.default, bool):
            return bool(var_def.default)
        if isinstance(var_def.default, int):
            return int(var_def.default)
        if isinstance(var_def.default, float):
            return float(var_def.default)
        return 0

    def add_variable(self, var_def: VariableDef, *, network_shape_effect: NetworkShapeEffect) -> None:
        """Add a variable definition and storage tensor during a dynamic-variable run."""
        self._require_dynamic_variable_mode()
        self._validate_network_shape_effect(var_def, network_shape_effect)
        if var_def.id in self._definitions:
            raise ValueError(f"Variable '{var_def.id}' already exists in registry")

        tensor = self._build_storage_tensor(var_def)
        self._definitions[var_def.id] = var_def
        self._storage[var_def.id] = tensor
        self._expected_shapes[var_def.id] = tensor.shape
        self._expected_dtypes[var_def.id] = tensor.dtype
        self._initial_storage[var_def.id] = tensor.clone()
        self._record_dynamic_variable_mutation("add", var_def, network_shape_effect, tensor)

    def remove_variable(self, variable_id: str, *, network_shape_effect: NetworkShapeEffect) -> None:
        """Remove a variable definition and its storage during a dynamic-variable run."""
        self._require_dynamic_variable_mode()
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        var_def = self._definitions[variable_id]
        self._validate_network_shape_effect(var_def, network_shape_effect)
        tensor = self._storage[variable_id]
        del self._definitions[variable_id]
        del self._storage[variable_id]
        del self._expected_shapes[variable_id]
        del self._expected_dtypes[variable_id]
        del self._initial_storage[variable_id]
        scope_key = self._arena_backed.pop(variable_id, None)
        if scope_key is not None:
            # The arena column is orphaned, not reallocated. It stays readable through
            # already-compiled publisher bindings (their column indices are frozen at
            # construction and would serve the stale value) — which is exactly what the
            # observation_schema_changed acknowledgment on this removal covers.
            del self._scope_arenas[scope_key].index[variable_id]
        self._record_dynamic_variable_mutation("remove", var_def, network_shape_effect, tensor)

    def _require_dynamic_variable_mode(self) -> None:
        if not self.dynamic_variable_mode:
            raise ValueError("Runtime variable mutations require VariableRegistry(dynamic_variable_mode=True)")

    def _validate_network_shape_effect(self, var_def: VariableDef, network_shape_effect: NetworkShapeEffect) -> None:
        if network_shape_effect not in _NETWORK_SHAPE_EFFECTS:
            raise ValueError(f"network_shape_effect must be one of {sorted(_NETWORK_SHAPE_EFFECTS)}")
        if self._can_change_observation_schema(var_def) and network_shape_effect != "observation_schema_changed":
            raise ValueError(
                f"Variable '{var_def.id}' is agent-observable; dynamic add/remove must use "
                "network_shape_effect='observation_schema_changed'"
            )

    def _can_change_observation_schema(self, var_def: VariableDef) -> bool:
        return bool(var_def.observable or "agent" in var_def.exposed_to)

    def _record_dynamic_variable_mutation(
        self,
        operation: Literal["add", "remove"],
        var_def: VariableDef,
        network_shape_effect: NetworkShapeEffect,
        tensor: torch.Tensor,
    ) -> None:
        self.variable_schema_generation += 1
        self._dynamic_variable_mutations.append(
            DynamicVariableMutation(
                operation=operation,
                variable_id=var_def.id,
                network_shape_effect=network_shape_effect,
                shape=tuple(tensor.shape),
                dtype=str(tensor.dtype),
                variable_schema_hash=self.variable_schema_hash,
            )
        )

    @property
    def scope_arenas(self) -> dict[str, ScopeArena]:
        """The per-scope storage arenas (always both keys, `global` and `agent`).

        Consumed by the token registry publisher for batched per-scope fills. The agent
        arena never contains `agent_private` variables — excluded by construction, with
        the publisher as the loud enforcement point (hamlet-83a043a9b9).
        """
        return self._scope_arenas

    def _arena_scope_key(self, var_def: VariableDef) -> str | None:
        """Arena membership rule: float32-typed `global`/`agent` variables, nothing else.

        `agent_private` deliberately returns None — see ScopeArena. Integer/bool-typed
        variables keep standalone storage (the arena is float32, the value-token dtype);
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
        if var_def.type in ("agent_ref", "item_ref", "affordance_ref", "effect_ref", "vecNi", "vec2i", "vec3i"):
            return torch.long
        if var_def.type == "bool":
            return torch.bool
        return torch.float32

    def _arena_element_count(self, var_def: VariableDef) -> int:
        """Per-row element count: the declared shape with the scope prefix stripped."""
        full_shape = self._compute_shape(var_def)
        prefix_len = len(self._scope_prefix_shape(var_def))
        count = 1
        for dim in full_shape[prefix_len:]:
            count *= dim
        return count

    def _initialize_scope_arenas(self) -> None:
        """Allocate the global/agent arenas from construction-time declarations.

        Variables added later through dynamic_variable_mode are never arena-backed —
        compiled token slot bindings are static, so nothing can observe them through the
        arena path.
        """
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
        rows = {"global": 1, "agent": self.num_agents}
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
        if scope_key == "global":
            return arena.tensor[0, offset : offset + count].view(tuple(shape))
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
        if var_def.type in ("vecNi", "vecNf", "vec2i", "vec3i", "vec2f", "vec3f", "message_token"):
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
            global scalar: ()
            global vector (dims=2): (2,)
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
        elif var_def.type in ("vecNi", "vecNf", "message_token"):
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
            return ()
        if scope in (VariableScope.AGENT, VariableScope.AGENT_PRIVATE):
            return (self.num_agents,)
        if scope == VariableScope.PAIR:
            if self.pair_storage_mode == "sparse":
                return (self._require_sparse_pair_edges().shape[0],)
            return (self.num_agents, self.num_agents)
        if scope == VariableScope.GROUP:
            return (self._positive_extent(var_def, "num_groups"),)
        if scope == VariableScope.AFFORDANCE:
            return (self._positive_extent(var_def, "num_affordances"),)
        if scope == VariableScope.ZONE:
            return (self._positive_extent(var_def, "num_zones"),)
        if scope == VariableScope.MESSAGE:
            return (self.num_agents, self._positive_extent(var_def, "num_message_slots"))
        if scope == VariableScope.ITEM:
            raise ValueError(
                "Item-scoped variables in variables_reference.yaml are not supported. Use vfs_profiles.yaml item_profiles instead."
            )
        raise ValueError(f"Unsupported variable scope: {var_def.scope}")

    def _positive_extent(self, var_def: VariableDef, attr_name: str) -> int:
        """Return a positive configured extent for a non-agent scope."""
        value = int(getattr(self, attr_name))
        if value <= 0:
            raise ValueError(f"Variable '{var_def.id}' uses {var_def.scope} scope but {attr_name} must be positive")
        return value

    def get(self, variable_id: str, reader: str) -> torch.Tensor:
        """Get variable value with access control.

        Args:
            variable_id: ID of the variable to read
            reader: Who is reading (e.g., "agent", "engine", "acs")

        Returns:
            Tensor containing the variable value

        Raises:
            KeyError: If variable_id doesn't exist
            PermissionError: If reader not allowed to read this variable

        Examples:
            # Read energy (agent scope)
            energy = registry.get("energy", reader="agent")
            # Returns: tensor([1.0, 1.0, 1.0, 1.0])  # shape [num_agents]

            # Read global time_sin
            time_sin = registry.get("time_sin", reader="agent")
            # Returns: tensor(0.0)  # shape []
        """
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        var_def = self._definitions[variable_id]

        # Check read permission
        if reader not in var_def.readable_by:
            raise PermissionError(f"'{reader}' is not allowed to read variable '{variable_id}'. Readable by: {var_def.readable_by}")

        value = self._storage[variable_id]

        if var_def.scope == "agent_private" and reader == "agent":
            raise PermissionError(
                f"'{reader}' is not allowed to read agent_private variable '{variable_id}'. "
                "Only privileged readers (engine, acs, etc.) may access raw values."
            )

        return value.clone()

    def set(self, variable_id: str, value: torch.Tensor, writer: str) -> None:
        """Set variable value with access control.

        Args:
            variable_id: ID of the variable to write
            value: New tensor value
            writer: Who is writing (e.g., "engine", "actions")

        Raises:
            KeyError: If variable_id doesn't exist
            PermissionError: If writer not allowed to write this variable

        Examples:
            # Update energy for all agents
            new_energy = torch.tensor([0.9, 0.8, 0.7, 0.6])
            registry.set("energy", new_energy, writer="engine")

            # Update global time_sin
            registry.set("time_sin", torch.tensor(0.707), writer="engine")
        """
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        var_def = self._definitions[variable_id]

        # Check write permission
        if writer not in var_def.writable_by:
            raise PermissionError(f"'{writer}' is not allowed to write variable '{variable_id}'. Writable by: {var_def.writable_by}")

        expected_shape = self._expected_shapes[variable_id]
        expected_dtype = self._expected_dtypes[variable_id]

        if value.shape != expected_shape:
            raise ValueError(f"Value for '{variable_id}' has shape {tuple(value.shape)}, expected {tuple(expected_shape)}")

        if value.dtype != expected_dtype:
            raise ValueError(f"Value for '{variable_id}' has dtype {value.dtype}, expected {expected_dtype}")

        # Update storage (in place for arena-backed variables; defensive copy otherwise)
        self._write_storage(variable_id, value.to(self.device))

    def set_engine_value(self, variable_id: str, value: torch.Tensor) -> None:
        """Write evaluator output as the engine, enforcing the declared element shape.

        Public, permission-checked writeback path for VTC/evaluator write-backs, kept
        separate from the environment hot path's direct storage mutation. Prior to
        hamlet-d970ef83f0 this bypassed the declared-shape check for non-sparse-pair
        variables (docstring used to bless "per-agent batches for variables declared as
        global scalars"); that bypass let storage drift permanently from
        `_expected_shapes`, corrupting state whose shape then depended on writer identity.
        A variable whose expression is genuinely per-agent must be declared agent-scoped,
        not written through a global declaration.
        """
        if variable_id not in self._definitions:
            raise KeyError(f"Variable '{variable_id}' not found in registry")

        var_def = self._definitions[variable_id]
        if "engine" not in var_def.writable_by:
            raise PermissionError(f"'engine' is not allowed to write variable '{variable_id}'. Writable by: {var_def.writable_by}")

        expected_dtype = self._expected_dtypes[variable_id]
        expected_shape = self._expected_shapes[variable_id]
        if value.shape != expected_shape:
            raise ValueError(
                f"Engine write for '{variable_id}' has shape {tuple(value.shape)}, expected {tuple(expected_shape)}.\n"
                "  Rule: set_engine_value no longer bypasses the declared element shape "
                "(hamlet-d970ef83f0) — a global scalar can no longer legally hold a per-agent "
                "batch. If the expression is genuinely per-agent, declare the variable "
                "agent-scoped instead of global."
            )
        self._write_storage(variable_id, value.to(device=self.device, dtype=expected_dtype))

    def reset_tick_scoped(self) -> None:
        """Restore tick-lifetime variables to their configured defaults."""
        self._reset_lifetimes({"tick"})

    def reset_episode_scoped(self) -> None:
        """Restore episode-start variables while preserving persistent state."""
        self._reset_lifetimes({"tick", "episode"})

    def _reset_lifetimes(self, lifetimes: AbstractSet[str]) -> None:
        for var_id, var_def in self._definitions.items():
            if str(var_def.lifetime) in lifetimes:
                self._write_storage(var_id, self._initial_storage[var_id])

    def _get_vector_dims(self, var_def: VariableDef) -> int:
        """Return expected dimensionality for vector variables."""
        if var_def.type in {"vec2i", "vec2f"}:
            return 2
        if var_def.type in {"vec3i", "vec3f"}:
            return 3
        if var_def.type in ("vecNi", "vecNf", "message_token"):
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
                "Item-scoped variables in variables_reference.yaml are not supported. Use vfs_profiles.yaml item_profiles instead."
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

    def list_global(self) -> list[str]:
        """List all global variable names."""
        return [var_id for var_id, var_def in self._definitions.items() if var_def.scope == VariableScope.GLOBAL]

    def get_global(self, name: str) -> torch.Tensor:
        """Get global variable value.

        Args:
            name: Variable name

        Returns:
            Global variable value tensor

        Raises:
            KeyError: If variable not found or not global
        """
        if name not in self._definitions:
            raise KeyError(f"Variable '{name}' not found")
        var_def = self._definitions[name]
        if var_def.scope != VariableScope.GLOBAL:
            raise KeyError(f"Variable '{name}' is not global (scope: {var_def.scope})")
        return self._storage[name].clone()

    def list_agent(self) -> list[str]:
        """List all agent variable names (including agent_private)."""
        return [
            var_id for var_id, var_def in self._definitions.items() if var_def.scope in (VariableScope.AGENT, VariableScope.AGENT_PRIVATE)
        ]

    def get_agent(self, name: str) -> torch.Tensor:
        """Get agent variable value.

        Args:
            name: Variable name

        Returns:
            Agent variable value tensor (batch)

        Raises:
            KeyError: If variable not found or not agent-scoped
        """
        if name not in self._definitions:
            raise KeyError(f"Variable '{name}' not found")
        var_def = self._definitions[name]
        if var_def.scope not in (VariableScope.AGENT, VariableScope.AGENT_PRIVATE):
            raise KeyError(f"Variable '{name}' is not agent-scoped (scope: {var_def.scope})")
        return self._storage[name].clone()

    def write_item(self, profile_name: str, var_name: str, value: float | torch.Tensor, vfs_index: int) -> None:
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
        if self.item_vfs is None:
            raise RuntimeError("Item VFS storage not allocated")
        if profile_name not in self.item_profile_map:
            raise KeyError(f"Item profile '{profile_name}' not found. Available: {list(self.item_profile_map.keys())}")
        profile_vars = self.item_profile_map[profile_name]
        if var_name not in profile_vars:
            raise KeyError(f"Variable '{var_name}' not found in profile '{profile_name}'. Available: {list(profile_vars.keys())}")
        var_idx = profile_vars[var_name]
        self.item_vfs[vfs_index, var_idx] = value

    def read_item(self, profile_name: str, var_name: str, vfs_index: int) -> float:
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


class ScopedVariableRegistry:
    """Variable storage with three scopes: global, agent, item.

    Global scope: Singleton values shared across all agents
        - Storage: dict[str, torch.Tensor] (scalar tensors)
        - Example: {"day_count": tensor(42), "is_night": tensor(True)}

    Agent scope: Per-agent values (batch tensors)
        - Storage: dict[str, torch.Tensor] (batch_size tensors)
        - Example: {"motivation": tensor([1.0, 0.8, 1.2])}

    Item scope: Per-item-instance values (profile-based)
        - Storage: dict[profile_name, dict[var_name, torch.Tensor]]
        - Example: {"food_stats": {"nutrition": tensor([0.5, 0.3])}}
    """

    def __init__(self, device: torch.device = torch.device("cpu")):
        self.device = device

        # Global scope: singleton tensors
        self._global_storage: dict[str, torch.Tensor] = {}

        # Agent scope: batch tensors (populated later)
        self._agent_storage: dict[str, torch.Tensor] = {}

        # Item scope: profile -> {var -> tensor} (populated later)
        self._item_storage: dict[str, dict[str, torch.Tensor]] = {}
        self.item_vfs: torch.Tensor | None = None
        self.item_profile_map: dict[str, dict[str, int]] = {}
        self.item_vfs_index_to_profile: dict[int, str] = {}

    # Global scope methods

    def set_global(self, name: str, value: torch.Tensor) -> None:
        """Set global variable value.

        Args:
            name: Variable name
            value: Singleton tensor (no batch dimension)
        """
        self._global_storage[name] = value.to(self.device)

    def get_global(self, name: str) -> torch.Tensor:
        """Get global variable value.

        Args:
            name: Variable name

        Returns:
            Singleton tensor

        Raises:
            KeyError: If variable not found
        """
        if name not in self._global_storage:
            raise KeyError(f"Global variable '{name}' not found. Available: {list(self._global_storage.keys())}")
        return self._global_storage[name].clone()

    def list_global(self) -> list[str]:
        """List all global variable names."""
        return list(self._global_storage.keys())

    # Agent scope methods (stubs for now)

    def set_agent(self, name: str, value: torch.Tensor) -> None:
        """Set agent variable value (batch tensor)."""
        self._agent_storage[name] = value.to(self.device)

    def get_agent(self, name: str) -> torch.Tensor:
        """Get agent variable value (batch tensor)."""
        if name not in self._agent_storage:
            raise KeyError(f"Agent variable '{name}' not found. Available: {list(self._agent_storage.keys())}")
        return self._agent_storage[name].clone()

    def list_agent(self) -> list[str]:
        """List all agent variable names."""
        return list(self._agent_storage.keys())

    # Item scope methods

    def set_item(self, profile_name: str, var_name: str, value: torch.Tensor) -> None:
        """Set item variable value for a profile.

        Args:
            profile_name: Item profile name (e.g., "food_stats")
            var_name: Variable name within profile
            value: Tensor with shape [num_instances] or [num_instances, ...]
        """
        if profile_name not in self._item_storage:
            self._item_storage[profile_name] = {}

        self._item_storage[profile_name][var_name] = value.to(self.device)

    def get_item(self, profile_name: str, var_name: str) -> torch.Tensor:
        """Get item variable value for a profile.

        Args:
            profile_name: Item profile name
            var_name: Variable name within profile

        Returns:
            Tensor with shape [num_instances] or [num_instances, ...]

        Raises:
            KeyError: If profile or variable not found
        """
        if profile_name not in self._item_storage:
            raise KeyError(f"Item profile '{profile_name}' not found. Available: {list(self._item_storage.keys())}")

        profile_vars = self._item_storage[profile_name]
        if var_name not in profile_vars:
            raise KeyError(f"Variable '{var_name}' not found in profile '{profile_name}'. Available: {list(profile_vars.keys())}")

        return profile_vars[var_name].clone()

    def list_item_profiles(self) -> list[str]:
        """List all item profile names."""
        return list(self._item_storage.keys())

    def list_item_variables(self, profile_name: str) -> list[str]:
        """List all variables in an item profile.

        Args:
            profile_name: Item profile name

        Returns:
            List of variable names in profile

        Raises:
            KeyError: If profile not found
        """
        if profile_name not in self._item_storage:
            raise KeyError(f"Item profile '{profile_name}' not found. Available: {list(self._item_storage.keys())}")

        return list(self._item_storage[profile_name].keys())

    def check_access(self, scope: str, path: str, operation: str) -> None:
        """Check if access is allowed per VFS access control rules.

        Access control rules:
        - Global variables: read-only for all scopes
        - Agent variables: read/write for agent scope only
        - Item variables: read/write for item scope only

        Args:
            scope: Requesting scope ("global", "agent", "item")
            path: Variable path (e.g., "day_count", "food_stats.nutrition")
            operation: Access type ("read", "write")

        Raises:
            AccessDeniedError: If access denied
        """
        # Agent variables (check first, before global)
        if path in self._agent_storage:
            if scope != "agent" and operation == "write":
                raise AccessDeniedError(f"Agent variable '{path}' can only be written by agent scope. Scope '{scope}' denied.")
            return  # Read allowed, write allowed for agent scope

        # Global variables are read-only
        if path in self._global_storage:
            if operation == "write":
                raise AccessDeniedError(f"Global variable '{path}' is read-only. Cannot write from scope '{scope}'.")
            return  # Read allowed

        # Item variables (profile.var format)
        if "." in path:
            profile, var = path.split(".", 1)
            if profile in self._item_storage:
                if scope != "item" and operation == "write":
                    raise AccessDeniedError(f"Item variable '{path}' can only be written by item scope. Scope '{scope}' denied.")
                return  # Read allowed, write allowed for item scope

        # Variable not found in any scope - allow for now (will fail at get/set)
