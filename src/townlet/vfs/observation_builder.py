"""VFS observation builder for agent observations."""

from __future__ import annotations

from dataclasses import dataclass, field

import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    GlobalVFSProfileConfig,
    ItemVFSProfileConfig,
)
from townlet.vfs.registry import VFSRegistryProtocol

__all__ = [
    "VFSObservationSpec",
    "build_vfs_observation",
]


def _variable_observation_dim(
    var_type: str,
    shape: list[int] | None,
    scope: str | None = None,
    *,
    dims: int | None = None,
    max_elements: int | None = None,
) -> int:
    """Return flattened observation dimensions for a VFS variable type."""
    if var_type in {"int", "float", "bool", "agent_ref", "item_ref", "affordance_ref", "effect_ref"}:
        return 1
    if var_type == "vec2i" or var_type == "vec2f":
        return 2
    if var_type == "vec3i" or var_type == "vec3f":
        return 3
    if var_type in {"vecNi", "vecNf"}:
        if dims is None:
            raise ValueError(f"Vector variable requires dims to compute observation dim (type={var_type}).")
        return dims
    if var_type in {"tensor1d", "tensor2d", "tensor3d", "tensorNd"}:
        if not shape:
            raise ValueError(f"Tensor variable requires shape to compute observation dim (type={var_type}).")
        prod = 1
        for dim in shape:
            prod *= dim
        if max_elements is not None and prod > max_elements:
            raise ValueError(f"Tensor observation dim too large ({prod} > {max_elements}) for type={var_type}, shape={shape}.")
        return prod
    raise ValueError(f"Unsupported VFS variable type for observation dimension calculation: {var_type!r}.")


def _agent_can_observe(var) -> bool:
    return "agent" in var.exposed_to


@dataclass
class VFSObservationSpec:
    """Observation dimension specification for VFS variables.

    Defines how many dimensions VFS contributes to agent observations.
    """

    global_vfs_dim: int  # Number of global variables
    agent_vfs_dim: int  # Number of agent variables
    item_vfs_dim: int  # Number of item VFS dimensions (slots × profiles × vars)

    # Variable ordering metadata for observation construction
    global_vars: tuple[str, ...] = ()
    agent_vars: tuple[str, ...] = ()
    item_profile_vars: dict[str, tuple[str, ...]] = field(default_factory=dict)  # profile_name → exposed var names
    item_vars_per_slot: int | None = None  # Exposed vars per slot (max across profiles)

    max_items_per_agent: int = 3  # Fixed inventory size
    max_item_profiles: int = 5  # Fixed profile count for transfer learning
    max_tensor_elements: int = 1_000_000  # Guardrail for tensor flattening

    @property
    def total_vfs_dim(self) -> int:
        """Total VFS contribution to obs_dim."""
        return self.global_vfs_dim + self.agent_vfs_dim + self.item_vfs_dim

    @classmethod
    def from_profiles(
        cls,
        global_profile: GlobalVFSProfileConfig | None,
        agent_profile: AgentVFSProfileConfig | None,
        item_profiles: list[ItemVFSProfileConfig],
    ) -> VFSObservationSpec:
        """Create observation spec from VFS profiles.

        Args:
            global_profile: Global VFS profile config (or None)
            agent_profile: Agent VFS profile config (or None)
            item_profiles: List of item VFS profile configs

        Returns:
            Observation spec with dimension counts
        """
        return cls._from_variable_iterables(
            global_variables=global_profile.variables if global_profile is not None else (),
            agent_variables=agent_profile.variables if agent_profile is not None else (),
            item_profile_variables=((profile.profile_name, profile.variables) for profile in item_profiles),
        )

    @classmethod
    def _from_variable_iterables(
        cls,
        *,
        global_variables,
        agent_variables,
        item_profile_variables,
        max_items_per_agent: int | None = None,
    ) -> VFSObservationSpec:
        """Create an observation spec from normalized variable iterables."""
        item_slots = cls.max_items_per_agent if max_items_per_agent is None else max_items_per_agent

        global_dim = 0
        global_vars: list[str] = []
        for var in global_variables:
            if not _agent_can_observe(var):
                continue
            global_vars.append(var.name)
            global_dim += _variable_observation_dim(
                var.type,
                getattr(var, "shape", None),
                dims=getattr(var, "dims", None),
                max_elements=cls.max_tensor_elements,
            )

        agent_dim = 0
        agent_vars: list[str] = []
        for agent_var in agent_variables:
            if not _agent_can_observe(agent_var):
                continue
            agent_vars.append(agent_var.name)
            agent_dim += _variable_observation_dim(
                agent_var.type,
                getattr(agent_var, "shape", None),
                dims=getattr(agent_var, "dims", None),
                max_elements=cls.max_tensor_elements,
            )

        item_dim = 0
        item_profile_vars: dict[str, tuple[str, ...]] = {}
        max_profile_dim = 0
        for profile_name, variables in item_profile_variables:
            exposed_vars = []
            profile_dim = 0
            for var in variables:
                if not _agent_can_observe(var):
                    continue
                exposed_vars.append(var.name)
                profile_dim += _variable_observation_dim(
                    var.type,
                    getattr(var, "shape", None),
                    scope="item",
                    dims=getattr(var, "dims", None),
                    max_elements=cls.max_tensor_elements,
                )

            item_profile_vars[profile_name] = tuple(exposed_vars)
            max_profile_dim = max(max_profile_dim, profile_dim)
        if max_profile_dim > 0:
            item_dim = item_slots * max_profile_dim

        return cls(
            global_vfs_dim=global_dim,
            agent_vfs_dim=agent_dim,
            item_vfs_dim=item_dim,
            global_vars=tuple(global_vars),
            agent_vars=tuple(agent_vars),
            item_profile_vars=item_profile_vars,
            item_vars_per_slot=max_profile_dim if max_profile_dim > 0 else None,
            max_items_per_agent=item_slots,
        )

    @classmethod
    def from_compiled_profiles(
        cls,
        compiled_profiles,
        *,
        max_items_per_agent: int,
    ) -> VFSObservationSpec | None:
        """Create an observation spec directly from compiled VFS profiles."""
        if compiled_profiles is None:
            return None

        global_profile = getattr(compiled_profiles, "global_profile", None)
        agent_profile = getattr(compiled_profiles, "agent_profile", None)
        item_profiles = getattr(compiled_profiles, "item_profiles", {}) or {}
        return cls._from_variable_iterables(
            global_variables=getattr(global_profile, "variables", []) if global_profile is not None else (),
            agent_variables=getattr(agent_profile, "variables", []) if agent_profile is not None else (),
            item_profile_variables=((name, getattr(profile, "variables", [])) for name, profile in item_profiles.items()),
            max_items_per_agent=max_items_per_agent,
        )


def build_vfs_observation(
    registry: VFSRegistryProtocol,
    spec: VFSObservationSpec,
    batch_size: int,
    agent_item_inventory: torch.Tensor | None = None,
) -> torch.Tensor:
    """Build VFS observation vector for agents.

    Args:
        registry: Variable registry with global/agent/item state
        spec: Observation specification (dims)
        batch_size: Number of agents
        agent_item_inventory: Item indices for each agent slot [batch, max_items_per_agent]
                              or None for zero stubs. -1 indicates empty slot.

    Returns:
        Observation tensor with shape [batch, total_vfs_dim]
    """
    components = []

    # Global VFS: broadcast singleton values to batch
    if spec.global_vfs_dim > 0:
        global_vars = []
        target_vars = spec.global_vars or tuple(registry.list_global())
        for var_name in target_vars:
            value = registry.get_global(var_name)
            if not torch.is_floating_point(value):
                value = value.float()
            global_vars.append(_flatten_to_batch(value, batch_size))

        if global_vars:
            global_obs = torch.cat(global_vars, dim=1)  # [batch, global_dim]
            components.append(global_obs)

    # Agent VFS: per-agent values
    if spec.agent_vfs_dim > 0:
        agent_vars = []
        target_vars = spec.agent_vars or tuple(registry.list_agent())
        for var_name in target_vars:
            value = registry.get_agent(var_name)
            if not torch.is_floating_point(value):
                value = value.float()
            agent_vars.append(_flatten_to_batch(value, batch_size, expect_batch=True))

        if agent_vars:
            agent_obs = torch.cat(agent_vars, dim=1)  # [batch, agent_dim]
            components.append(agent_obs)

    # Item VFS: Include item state with masking
    if spec.item_vfs_dim > 0:
        item_vfs_storage = registry.item_vfs
        if item_vfs_storage is None:
            raise RuntimeError("Item VFS storage is missing; cannot build item observations.")
        if agent_item_inventory is None:
            # No item inventory provided, return zeros for item slots
            item_obs = torch.zeros(
                (batch_size, spec.item_vfs_dim),
                dtype=torch.float32,
                device=registry.device,
            )
        else:
            if spec.item_vfs_dim % spec.max_items_per_agent != 0:
                raise ValueError("item_vfs_dim must be divisible by max_items_per_agent for item observations.")

            if agent_item_inventory.dim() != 2 or agent_item_inventory.size(1) != spec.max_items_per_agent:
                raise ValueError("agent_item_inventory must have shape [batch, max_items_per_agent] when item_vfs_dim is non-zero.")
            if agent_item_inventory.size(0) != batch_size:
                raise ValueError("agent_item_inventory batch dimension must match batch_size.")

            vars_per_slot = spec.item_vars_per_slot or (spec.item_vfs_dim // spec.max_items_per_agent)

            if vars_per_slot == 0:
                item_obs = torch.zeros(
                    (batch_size, spec.item_vfs_dim),
                    dtype=torch.float32,
                    device=registry.device,
                )
            else:
                inventory_indices = agent_item_inventory.to(device=registry.device, dtype=torch.long)
                max_index = item_vfs_storage.size(0)
                invalid_positive = (inventory_indices >= max_index) & (inventory_indices != -1)
                if invalid_positive.any().item():
                    raise IndexError(f"agent_item_inventory references out-of-range item_vfs indices (max valid index: {max_index - 1}).")

                item_obs = torch.zeros(
                    (batch_size, spec.item_vfs_dim),
                    dtype=item_vfs_storage.dtype,
                    device=registry.device,
                )

                # Precompute exposed indices per profile. Missing profiles or variables
                # are configuration errors, not "no exposed values" cases.
                profile_indices: dict[str, list[int]] = {}
                registry_profile_map = registry.item_profile_map
                source_profiles = (
                    spec.item_profile_vars.items()
                    if spec.item_profile_vars
                    else ((name, tuple(var_map.keys())) for name, var_map in registry_profile_map.items())
                )
                for profile_name, var_names in source_profiles:
                    if profile_name not in registry_profile_map:
                        raise RuntimeError(
                            f"Item VFS observation references profile {profile_name!r}, "
                            f"but registry only has profiles {sorted(registry_profile_map)}."
                        )
                    idx_map = registry_profile_map[profile_name]
                    missing_vars = [name for name in var_names if name not in idx_map]
                    if missing_vars:
                        raise RuntimeError(
                            f"Item VFS observation references variables {missing_vars} for profile {profile_name!r}, "
                            f"but registry only has variables {sorted(idx_map)}."
                        )
                    exposed_indices = [idx_map[name] for name in var_names]
                    profile_indices[profile_name] = exposed_indices

                profile_lookup = registry.item_vfs_index_to_profile
                profile_id_by_name = {name: idx for idx, name in enumerate(profile_indices)}
                row_profile_ids = torch.full((max_index,), -1, dtype=torch.long, device=registry.device)
                for vfs_idx, profile_name in profile_lookup.items():
                    if vfs_idx < 0 or vfs_idx >= max_index:
                        raise IndexError(f"Item profile metadata references out-of-range item_vfs index {vfs_idx}.")
                    if profile_name in profile_id_by_name:
                        row_profile_ids[vfs_idx] = profile_id_by_name[profile_name]

                valid_mask = inventory_indices != -1
                safe_indices = inventory_indices.clamp(min=0)
                selected_profile_ids = row_profile_ids[safe_indices]
                unresolved_mask = valid_mask & (selected_profile_ids == -1)
                if unresolved_mask.any().item():
                    first_agent, first_slot = unresolved_mask.nonzero(as_tuple=False)[0].tolist()
                    unresolved_index = int(inventory_indices[first_agent, first_slot].item())
                    unresolved_profile = profile_lookup.get(unresolved_index)
                    raise RuntimeError(
                        f"Item VFS observation cannot resolve exposed variables for VFS row index {unresolved_index} "
                        f"(profile={unresolved_profile!r})."
                    )

                for profile_name, selected_indices in profile_indices.items():
                    if not selected_indices:
                        continue
                    profile_id = profile_id_by_name[profile_name]
                    profile_mask = valid_mask & (selected_profile_ids == profile_id)
                    if not profile_mask.any().item():
                        continue
                    rows, slots = profile_mask.nonzero(as_tuple=True)
                    vfs_rows = safe_indices[rows, slots]
                    source_cols = torch.tensor(selected_indices, dtype=torch.long, device=registry.device)
                    values = item_vfs_storage[vfs_rows.unsqueeze(1), source_cols.unsqueeze(0)]
                    dest_cols = slots.unsqueeze(1) * vars_per_slot + torch.arange(len(selected_indices), device=registry.device)
                    item_obs[rows.unsqueeze(1), dest_cols] = values

        components.append(item_obs)

    # Concatenate all components
    if components:
        return torch.cat(components, dim=1)  # [batch, total_vfs_dim]
    else:
        return torch.zeros(batch_size, 0, device=registry.device)


def _flatten_to_batch(value: torch.Tensor, batch_size: int, expect_batch: bool = False) -> torch.Tensor:
    """Ensure value is [batch, flat_dim] and float."""
    if not torch.is_floating_point(value):
        value = value.float()

    if expect_batch:
        if value.dim() == 1:
            value = value.unsqueeze(1)
        if value.shape[0] != batch_size:
            raise ValueError(f"Expected batch size {batch_size}, got {value.shape[0]}")
        flat = value.reshape(batch_size, -1)
        return flat

    # Global values: broadcast to batch if missing leading dim
    if value.dim() >= 1 and value.shape[0] == batch_size:
        # Already batched; don't double-broadcast
        pass
    elif value.dim() == 0:
        value = value.expand(batch_size)
    elif value.dim() >= 1:
        value = value.unsqueeze(0).expand(batch_size, *value.shape)
    flat = value.reshape(batch_size, -1)
    return flat
