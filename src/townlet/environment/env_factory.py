"""Factory helpers for constructing vectorized Hamlet environments."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from townlet.universe.dto import MeterMetadata

if TYPE_CHECKING:
    from townlet.environment.vectorized_env import VectorizedHamletEnv
    from townlet.universe.compiled import CompiledUniverse


# Valid VFS variable types for VariableDef.
_VALID_VFS_TYPES = frozenset({"scalar", "bool", "tensor1d", "tensor2d", "tensor3d", "tensorNd", "agent_ref", "item_ref"})


def _normalize_vfs_type(raw_type: str, var_id: str) -> str:
    """Normalize VFS variable type to canonical form."""
    if raw_type in ("int", "float"):
        return "scalar"
    if raw_type in _VALID_VFS_TYPES:
        return raw_type

    raise ValueError(f"Unsupported VFS variable type '{raw_type}' for variable '{var_id}'. " f"Valid types: {sorted(_VALID_VFS_TYPES)}")


def _build_bar_index_map(meter_metadata: MeterMetadata) -> dict[str, int]:
    """Build mapping from bar IDs to meter tensor indices."""
    return {meter.name: meter.index for meter in meter_metadata.meters}


def _resolve_deployable_affordances(
    all_affordance_names: list[str],
    enabled_affordances: list[str] | None,
    name_to_id: dict[str, str],
) -> list[str]:
    """Return affordances that should be deployed, respecting IDs and names in config."""
    if enabled_affordances is None:
        raise ValueError("enabled_affordances must be an explicit list (empty to deploy none); null is not allowed.")

    enabled_lookup = {str(entry) for entry in enabled_affordances}
    deployable: list[str] = []
    for name in all_affordance_names:
        if name in enabled_lookup:
            deployable.append(name)
            continue
        aff_id = name_to_id.get(name)
        if aff_id is not None and aff_id in enabled_lookup:
            deployable.append(name)
    return deployable


def from_universe(
    env_cls: type[VectorizedHamletEnv],
    universe: CompiledUniverse,
    *,
    level_name: str,
    num_agents: int,
    device: torch.device | str,
) -> VectorizedHamletEnv:
    """Instantiate an environment using metadata from a compiled universe."""
    if level_name is None:
        raise ValueError(
            "VectorizedHamletEnv.from_universe requires an explicit level_name; "
            "implicit default level selection is not allowed in v2.1 runtime."
        )

    if isinstance(device, str):
        torch_device = torch.device(device)
    else:
        torch_device = device

    return env_cls(
        universe=universe,
        level_name=level_name,
        num_agents=num_agents,
        device=torch_device,
    )
