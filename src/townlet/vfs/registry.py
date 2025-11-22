"""Variable registry for VFS runtime storage.

The VariableRegistry manages runtime storage of VFS variables with access control
and scope semantics. It handles three scope patterns:

- global: Single value shared by all agents (shape [] or [dims])
- agent: Per-agent values, observable by all (shape [num_agents] or [num_agents, dims])
- agent_private: Per-agent values, observable only by owner (shape [num_agents] or [num_agents, dims])
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import torch

from townlet.vfs.schema import VariableDef, VariableScope

if TYPE_CHECKING:
    pass  # CompiledItemProfile not needed for type checking

__all__ = [
    "VariableRegistry",
    "ScopedVariableRegistry",
    "AccessDeniedError",
]


class AccessDeniedError(Exception):
    """Raised when access control check fails."""

    pass


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
    ):
        """Initialize variable registry.

        Args:
            variables: List of variable definitions
            num_agents: Number of agents in the environment
            device: PyTorch device (cpu or cuda)
            max_items: Maximum items (for item-scoped variables)
            item_profiles: Compiled item profiles (profile_name → CompiledItemProfile)
        """
        self.num_agents = num_agents
        self.max_items = max_items
        self.device = device
        self.item_profiles: dict[str, Any] = item_profiles or {}  # Store compiled profiles

        # Store variable definitions by ID, guarding against duplicate IDs
        self._definitions: dict[str, VariableDef] = {}
        for var in variables:
            if var.id in self._definitions:
                raise ValueError(f"Duplicate variable id '{var.id}' in registry initialization")
            self._definitions[var.id] = var

        # Initialize storage tensors
        self._storage: dict[str, torch.Tensor] = {}
        self._expected_shapes: dict[str, torch.Size] = {}
        self._expected_dtypes: dict[str, torch.dtype] = {}
        self._initialize_storage()

        # Initialize item-scoped storage
        self.item_vfs: torch.Tensor | None = None
        self.item_var_to_index: dict[str, int] = {}
        self.item_profile_map: dict[str, dict[str, int]] = {}  # {profile_name → {var_name → index}}
        self.item_vfs_index_to_profile: dict[int, str] = {}  # {vfs_index → profile_name}
        self._legacy_item_profile_name = "__legacy__"
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

    def _initialize_storage(self) -> None:
        """Initialize storage tensors with default values for all variables."""
        for var_id, var_def in self._definitions.items():
            # Determine tensor shape based on scope and type
            self._compute_shape(var_def)

            # Initialize tensor with default value
            if var_def.type == "scalar":
                # Scalar: default is a single float
                if var_def.scope == "global":
                    # Global scalar: shape []
                    tensor = torch.tensor(var_def.default, device=self.device, dtype=torch.float32)
                else:
                    # Agent/agent_private scalar: shape [num_agents]
                    tensor = torch.full(
                        (self.num_agents,),
                        var_def.default,
                        device=self.device,
                        dtype=torch.float32,
                    )
            elif var_def.type in ("vecNi", "vecNf", "vec2i", "vec3i"):
                base_default = self._build_vector_default(var_def)

                if var_def.scope == "global":
                    tensor = base_default.clone()
                else:
                    tensor = base_default.unsqueeze(0).expand(self.num_agents, -1).clone()
            elif var_def.type == "bool":
                # Bool: default is a boolean
                if var_def.scope == "global":
                    # Global bool: shape []
                    tensor = torch.tensor(var_def.default, device=self.device, dtype=torch.bool)
                else:
                    # Agent/agent_private bool: shape [num_agents]
                    tensor = torch.full(
                        (self.num_agents,),
                        var_def.default,
                        device=self.device,
                        dtype=torch.bool,
                    )
            else:
                raise ValueError(f"Unsupported variable type: {var_def.type}")

            self._storage[var_id] = tensor
            self._expected_shapes[var_id] = tensor.shape
            self._expected_dtypes[var_id] = tensor.dtype

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
        if var_def.type == "scalar" or var_def.type == "bool":
            if var_def.scope == "global":
                return ()  # Shape []
            else:
                return (self.num_agents,)  # Shape [num_agents]

        elif var_def.type == "vec2i":
            dims = 2
        elif var_def.type == "vec3i":
            dims = 3
        elif var_def.type in ("vecNi", "vecNf"):
            if var_def.dims is None:
                raise ValueError(f"vecNi/vecNf variable '{var_def.id}' must have dims field defined")
            dims = var_def.dims
        else:
            raise ValueError(f"Unsupported variable type: {var_def.type}")

        # Vector variable
        if var_def.scope == "global":
            return (dims,)  # Shape [dims]
        else:
            return (self.num_agents, dims)  # Shape [num_agents, dims]

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

        # Update storage (defensive copy to avoid aliasing)
        self._storage[variable_id] = value.to(self.device).clone()

    def _get_vector_dims(self, var_def: VariableDef) -> int:
        """Return expected dimensionality for vector variables."""
        if var_def.type == "vec2i":
            return 2
        if var_def.type == "vec3i":
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

    def _initialize_item_storage_from_profiles(self) -> None:
        """Initialize item VFS storage from compiled profiles.

        Creates:
        - item_vfs: [max_items, max_profile_vars] tensor
        - item_profile_map: {profile_name → {var_name → tensor_index}}

        Item storage is profile-agnostic: all profiles share the same tensor layout
        using max_profile_vars across all profiles. Unused slots are masked.
        """
        item_vars = [v for v in self._definitions.values() if v.scope == VariableScope.ITEM]

        # Profile-driven path
        if self.item_profiles:
            if self.max_items == 0:
                self.item_vfs = None
                self.item_profile_map = {}
                return

            # Calculate max variables across all profiles
            max_vars = 0
            for profile in self.item_profiles.values():
                max_vars = max(max_vars, len(profile.variables))

            # Allocate storage: [max_items, max_vars]
            self.item_vfs = torch.zeros(
                (self.max_items, max_vars),
                dtype=torch.float32,
                device=self.device,
            )

            # Build profile map: {profile_name → {var_name → index}}
            for profile_name, profile in self.item_profiles.items():
                var_map = {}
                for idx, var in enumerate(profile.variables):
                    var_map[var.name] = idx
                self.item_profile_map[profile_name] = var_map
            return

        # Legacy path: allow item-scoped variables without compiled profiles
        if item_vars:
            if self.max_items == 0:
                self.item_vfs = None
                self.item_profile_map = {}
                return

            max_vars = len(item_vars)
            self.item_vfs = torch.zeros(
                (self.max_items, max_vars),
                dtype=torch.float32,
                device=self.device,
            )

            # Single legacy layout shared across all profiles
            legacy_map = {var.id: idx for idx, var in enumerate(item_vars)}
            self.item_profile_map[self._legacy_item_profile_name] = legacy_map

            # Seed default profile definitions so ItemManager can initialize defaults
            legacy_profile = SimpleNamespace(
                profile_name=self._legacy_item_profile_name,
                variables=[SimpleNamespace(name=var.id, initial_value=var.default) for var in item_vars],
            )
            self.item_profiles[self._legacy_item_profile_name] = legacy_profile
            return

        # No items or no profiles
        self.item_vfs = None
        self.item_profile_map = {}

    def _ensure_item_profile(self, profile_name: str) -> None:
        """Ensure a profile map exists, falling back to legacy layout if present."""
        if profile_name in self.item_profile_map:
            return
        legacy_map = self.item_profile_map.get(self._legacy_item_profile_name)
        if legacy_map is not None:
            self.item_profile_map[profile_name] = legacy_map
            legacy_profile = self.item_profiles.get(self._legacy_item_profile_name)
            if legacy_profile is not None:
                self.item_profiles[profile_name] = legacy_profile

    def ensure_item_profile(self, profile_name: str) -> None:
        """Public wrapper to ensure profile map exists (for ItemManager)."""
        self._ensure_item_profile(profile_name)

    def read(
        self,
        variable_id: str,
        context_index: int,
        scope: VariableScope,
    ) -> float | torch.Tensor:
        """Read variable value from registry.

        Args:
            variable_id: Variable ID
            context_index: Index (agent index for agent scope, item vfs_index for item scope)
            scope: Variable scope

        Returns:
            Variable value
        """
        # Handle ITEM scope first (may not be in _definitions if from VFS profiles)
        if scope == VariableScope.ITEM:
            if self.item_vfs is None:
                raise RuntimeError("Item VFS storage not allocated")
            # Get profile for this vfs_index
            if context_index not in self.item_vfs_index_to_profile:
                raise KeyError(f"No item registered at vfs_index {context_index}")
            profile_name = self.item_vfs_index_to_profile[context_index]
            return self.read_item(profile_name, variable_id, context_index)

        # For other scopes, check _definitions
        var = self._definitions.get(variable_id)
        if var is None:
            raise KeyError(f"Variable {variable_id} not found")

        # For other scopes, use existing get() method with reader="engine"
        # This is a simplified implementation for testing
        raise NotImplementedError(f"read() not yet implemented for scope {scope}")

    def write(
        self,
        variable_id: str,
        value: float | torch.Tensor,
        context_index: int,
        scope: VariableScope,
    ) -> None:
        """Write variable value to registry.

        Args:
            variable_id: Variable ID
            value: New value
            context_index: Index (agent index for agent scope, item vfs_index for item scope)
            scope: Variable scope
        """
        # Handle ITEM scope first (may not be in _definitions if from VFS profiles)
        if scope == VariableScope.ITEM:
            if self.item_vfs is None:
                raise RuntimeError("Item VFS storage not allocated")
            # Get profile for this vfs_index
            if context_index not in self.item_vfs_index_to_profile:
                raise KeyError(f"No item registered at vfs_index {context_index}")
            profile_name = self.item_vfs_index_to_profile[context_index]
            self.write_item(profile_name, variable_id, value, context_index)
            return

        # For other scopes, check _definitions
        var = self._definitions.get(variable_id)
        if var is None:
            raise KeyError(f"Variable {variable_id} not found")

        # For other scopes, use existing set() method with writer="engine"
        # This is a simplified implementation for testing
        raise NotImplementedError(f"write() not yet implemented for scope {scope}")

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
        self._ensure_item_profile(profile_name)
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
        self._ensure_item_profile(profile_name)
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
        self._ensure_item_profile(profile_name)
        if profile_name not in self.item_profile_map:
            raise ValueError(f"Profile '{profile_name}' not found. Available: {list(self.item_profile_map.keys())}")
        self.item_vfs_index_to_profile[vfs_index] = profile_name

    def unregister_item_instance(self, vfs_index: int) -> None:
        """Unregister item instance when despawned.

        Args:
            vfs_index: Item VFS index
        """
        self.item_vfs_index_to_profile.pop(vfs_index, None)


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
