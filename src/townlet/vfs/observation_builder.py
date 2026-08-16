"""VFS observation builder for agent observations."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    GlobalVFSProfileConfig,
    ItemVFSProfileConfig,
)
from townlet.vfs.registry import VFSRegistryProtocol
from townlet.vfs.schema import NormalizationSpec

__all__ = [
    "VFSObservationSpec",
    "apply_normalization",
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


def agent_can_observe(var) -> bool:
    """True when a profile variable is exposed to the agent (public twin of the predicate the
    spec builder uses, so the compiler emits fields for exactly the variables the runtime
    would have flattened — one rule, two callers, PDR-0075)."""
    return _agent_can_observe(var)


def profile_variable_observation_dim(var, *, scope: str | None = None) -> int:
    """Flattened observation width of one profile variable, by its declared type/shape/dims.

    The same rule `VFSObservationSpec` sums per scope, exposed so the compiler can emit ONE
    observation field per global/agent profile variable at exactly the width the runtime
    reads (PDR-0075).
    """
    return _variable_observation_dim(
        var.type,
        getattr(var, "shape", None),
        scope=scope,
        dims=getattr(var, "dims", None),
        max_elements=VFSObservationSpec.max_tensor_elements,
    )


def _normalization_parameter(
    value: float | list[float] | None,
    target: torch.Tensor,
    name: str,
) -> torch.Tensor:
    if value is None:
        raise ValueError(f"Normalization parameter {name!r} is required")
    return torch.as_tensor(value, dtype=target.dtype, device=target.device)


def _rank_scale(value: torch.Tensor) -> torch.Tensor:
    if value.ndim == 0 or value.shape[0] <= 1:
        return torch.zeros_like(value)

    order = torch.argsort(value, dim=0, stable=True)
    ranks = torch.empty_like(value)
    rank_values = torch.arange(value.shape[0], dtype=value.dtype, device=value.device)
    while rank_values.ndim < value.ndim:
        rank_values = rank_values.unsqueeze(-1)
    ranks.scatter_(0, order, rank_values.expand_as(value))
    return ranks / float(value.shape[0] - 1)


def apply_normalization(value: torch.Tensor, normalization: NormalizationSpec) -> torch.Tensor:
    """Apply a VFS normalization spec to a tensor."""
    value_float = value if torch.is_floating_point(value) else value.float()

    if normalization.kind == "none":
        return value_float

    if normalization.kind == "minmax":
        min_value = _normalization_parameter(normalization.min, value_float, "min")
        max_value = _normalization_parameter(normalization.max, value_float, "max")
        scaled = torch.clamp(value_float, min=min_value, max=max_value) if normalization.clip else value_float
        return (scaled - min_value) / (max_value - min_value)

    if normalization.kind == "zscore":
        mean = _normalization_parameter(normalization.mean, value_float, "mean")
        std = _normalization_parameter(normalization.std, value_float, "std")
        return (value_float - mean) / std

    if normalization.kind == "cyclical_sin_cos":
        if normalization.period is None:
            raise ValueError("cyclical_sin_cos normalization requires period")
        angle = value_float * (2.0 * math.pi / normalization.period)
        if angle.ndim == 1:
            angle = angle.unsqueeze(-1)
        return torch.cat((torch.sin(angle), torch.cos(angle)), dim=-1)

    if normalization.kind == "binary":
        if normalization.threshold is None:
            raise ValueError("binary normalization requires threshold")
        return (value_float > normalization.threshold).to(dtype=value_float.dtype)

    if normalization.kind == "one_hot":
        if normalization.categories is None:
            raise ValueError("one_hot normalization requires categories")
        indices = value.long()
        if indices.ndim > 0 and indices.shape[-1] == 1:
            indices = indices.squeeze(-1)
        if bool(((indices < 0) | (indices >= normalization.categories)).any().item()):
            raise ValueError("one_hot normalization received category index outside configured range")
        return torch.nn.functional.one_hot(indices, num_classes=normalization.categories).to(dtype=torch.float32)

    if normalization.kind == "log_scaled":
        min_value = _normalization_parameter(normalization.min, value_float, "min")
        max_value = _normalization_parameter(normalization.max, value_float, "max")
        shifted = (torch.clamp(value_float, min=min_value, max=max_value) if normalization.clip else value_float) - min_value
        if bool((shifted < 0).any().item()):
            raise ValueError("log_scaled normalization received value below configured min")
        return torch.log1p(shifted) / torch.log1p(max_value - min_value)

    if normalization.kind == "rank_scaled":
        return _rank_scale(value_float)

    if normalization.kind == "masked_value":
        if normalization.mask_value is None or normalization.fill_value is None:
            raise ValueError("masked_value normalization requires mask_value and fill_value")
        mask = value_float == normalization.mask_value
        return torch.where(mask, torch.full_like(value_float, normalization.fill_value), value_float)

    raise ValueError(f"Unsupported normalization kind: {normalization.kind!r}")


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
    global_active_mask: tuple[bool, ...] = ()
    agent_active_mask: tuple[bool, ...] = ()
    item_active_mask: tuple[bool, ...] = ()

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
        global_active_mask: list[bool] = []
        for var in global_variables:
            if not _agent_can_observe(var):
                continue
            dim = _variable_observation_dim(
                var.type,
                getattr(var, "shape", None),
                dims=getattr(var, "dims", None),
                max_elements=cls.max_tensor_elements,
            )
            global_vars.append(var.name)
            global_dim += dim
            global_active_mask.extend([bool(getattr(var, "curriculum_active", True))] * dim)

        agent_dim = 0
        agent_vars: list[str] = []
        agent_active_mask: list[bool] = []
        for agent_var in agent_variables:
            if not _agent_can_observe(agent_var):
                continue
            dim = _variable_observation_dim(
                agent_var.type,
                getattr(agent_var, "shape", None),
                dims=getattr(agent_var, "dims", None),
                max_elements=cls.max_tensor_elements,
            )
            agent_vars.append(agent_var.name)
            agent_dim += dim
            agent_active_mask.extend([bool(getattr(agent_var, "curriculum_active", True))] * dim)

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
            global_active_mask=tuple(global_active_mask),
            agent_active_mask=tuple(agent_active_mask),
            item_active_mask=tuple(True for _ in range(item_dim)),
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


def _apply_active_mask(component: torch.Tensor, active_mask: tuple[bool, ...], section_name: str) -> torch.Tensor:
    if not active_mask:
        return component
    if component.dim() != 2:
        raise ValueError(f"{section_name} VFS observation component must be rank-2.")
    if len(active_mask) != component.shape[1]:
        expected_dim = component.shape[1]
        raise ValueError(f"{section_name}_active_mask length {len(active_mask)} does not match {section_name}_vfs_dim {expected_dim}.")
    mask = torch.tensor(active_mask, dtype=component.dtype, device=component.device).unsqueeze(0)
    return component * mask


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
            global_obs = _apply_active_mask(global_obs, spec.global_active_mask, "global")
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
            agent_obs = _apply_active_mask(agent_obs, spec.agent_active_mask, "agent")
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

        item_obs = _apply_active_mask(item_obs, spec.item_active_mask, "item")
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
