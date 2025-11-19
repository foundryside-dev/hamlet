"""VFS observation builder for agent observations."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.config.vfs_profiles_config import (
    AgentVFSProfileConfig,
    GlobalVFSProfileConfig,
    ItemVFSProfileConfig,
)

__all__ = [
    "VFSObservationSpec",
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
