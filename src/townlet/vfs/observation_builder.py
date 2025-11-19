"""VFS observation builder for agent observations."""

from __future__ import annotations

from dataclasses import dataclass

import torch

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    GlobalVFSProfileConfig,
    ItemVFSProfileConfig,
)
from townlet.vfs.registry import ScopedVariableRegistry

__all__ = [
    "VFSObservationSpec",
    "build_vfs_observation",
]


@dataclass
class VFSObservationSpec:
    """Observation dimension specification for VFS variables.

    Defines how many dimensions VFS contributes to agent observations.
    """

    global_vfs_dim: int  # Number of global variables
    agent_vfs_dim: int  # Number of agent variables
    item_vfs_dim: int  # Number of item VFS dimensions (slots × profiles × vars)

    max_items_per_agent: int = 3  # Fixed inventory size
    max_item_profiles: int = 5  # Fixed profile count for transfer learning

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
        # Global VFS dimensions
        global_dim = 0
        if global_profile is not None:
            global_dim = len(global_profile.variables)

        # Agent VFS dimensions
        agent_dim = 0
        if agent_profile is not None:
            agent_dim = len(agent_profile.variables)

        # Item VFS dimensions: max_items × max_profiles × vars_per_profile
        # For now, assume all profiles have same number of variables
        # (will refactor in Phase 4 with actual item system)
        item_dim = 0
        if item_profiles:
            # Fixed slots: 3 items × 5 profiles × vars_per_profile
            max_vars_per_profile = max(len(p.variables) for p in item_profiles)
            item_dim = 3 * max_vars_per_profile  # Simplified for Phase 2

        return cls(
            global_vfs_dim=global_dim,
            agent_vfs_dim=agent_dim,
            item_vfs_dim=item_dim,
        )


def build_vfs_observation(
    registry: ScopedVariableRegistry,
    spec: VFSObservationSpec,
    batch_size: int,
) -> torch.Tensor:
    """Build VFS observation vector for agents.

    Args:
        registry: Variable registry with global/agent/item state
        spec: Observation specification (dims)
        batch_size: Number of agents

    Returns:
        Observation tensor with shape [batch, total_vfs_dim]
    """
    components = []

    # Global VFS: broadcast singleton values to batch
    if spec.global_vfs_dim > 0:
        global_vars = []
        for var_name in registry.list_global():
            value = registry.get_global(var_name)
            # Convert bool to float, broadcast to batch
            if value.dtype == torch.bool:
                value = value.float()
            # Broadcast singleton to batch
            value = value.expand(batch_size)
            global_vars.append(value.unsqueeze(1))  # [batch, 1]

        if global_vars:
            global_obs = torch.cat(global_vars, dim=1)  # [batch, global_dim]
            components.append(global_obs)

    # Agent VFS: per-agent values
    if spec.agent_vfs_dim > 0:
        agent_vars = []
        for var_name in registry.list_agent():
            value = registry.get_agent(var_name)
            # Convert bool to float
            if value.dtype == torch.bool:
                value = value.float()
            agent_vars.append(value.unsqueeze(1))  # [batch, 1]

        if agent_vars:
            agent_obs = torch.cat(agent_vars, dim=1)  # [batch, agent_dim]
            components.append(agent_obs)

    # Item VFS: stubbed for Phase 2 (zero-filled)
    if spec.item_vfs_dim > 0:
        item_obs = torch.zeros(batch_size, spec.item_vfs_dim, device=registry.device)
        components.append(item_obs)

    # Concatenate all components
    if components:
        return torch.cat(components, dim=1)  # [batch, total_vfs_dim]
    else:
        return torch.zeros(batch_size, 0, device=registry.device)
