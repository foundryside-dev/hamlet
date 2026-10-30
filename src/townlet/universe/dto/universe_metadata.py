"""Universe metadata DTO."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, field, fields
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class UniverseMetadata:
    """High-level metadata describing a compiled universe."""

    # Identification
    universe_name: str
    schema_version: str
    # The level this projection was compiled FOR. Required, no default: it is the
    # only field that distinguishes two levels which collide on every content hash
    # (measured: L0_5_dual_resource and L1_full_observability share vfs_hash,
    # transition_graph_hash and action_schema_hash in the shipped pack).
    primary_level: str

    # Substrate + topology
    substrate_type: str
    position_dim: int

    # Meter metadata (required)
    meter_count: int
    ticks_per_day: int

    # Optional meter metadata
    meter_names: tuple[str, ...] = field(default_factory=tuple)
    meter_name_to_index: Mapping[str, int] = field(default_factory=dict)
    # Affordance metadata
    affordance_count: int = 0
    affordance_ids: tuple[str, ...] = field(default_factory=tuple)
    affordance_id_to_index: Mapping[str, int] = field(default_factory=dict)

    # Action/observation space
    action_count: int = 0
    observation_dim: int = 0

    # VFS scope extents (canonical variables `extents:` block). Zero means
    # the pack declares no variables of that scope — the loader rejects a
    # scoped variable whose extent is undeclared, so 0 never reaches a registry
    # that needs it.
    num_message_slots: int = 0

    # Spatial metadata for finite substrates. Axis dimensions remain owned by
    # the substrate; collapsing them to one square-only number loses identity.
    grid_cells: int | None = None

    # Versioning + provenance
    config_version: str = "1.0"
    compiler_version: str = "0.0.0"
    compiled_at: str = ""
    config_hash: str = ""
    config_mtime: float = 0.0  # Maximum modification time of all config files (for cache invalidation)
    provenance_id: str = ""
    compiler_git_sha: str = ""
    python_version: str = ""
    torch_version: str = ""
    pydantic_version: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "meter_names", tuple(self.meter_names))
        object.__setattr__(
            self,
            "meter_name_to_index",
            MappingProxyType(dict(self.meter_name_to_index)),
        )
        object.__setattr__(self, "affordance_ids", tuple(self.affordance_ids))
        object.__setattr__(
            self,
            "affordance_id_to_index",
            MappingProxyType(dict(self.affordance_id_to_index)),
        )

    def __deepcopy__(self, memo: dict[int, Any]) -> UniverseMetadata:
        """Rebuild through the constructor: `copy.deepcopy` cannot pickle a mappingproxy.

        The two index maps are read-only views installed by ``__post_init__``; copying
        their plain-dict contents and re-constructing re-installs the views, so a clone
        is as immutable as the original and ``CompiledUniverse.clone()`` works on a
        freshly compiled universe, not only on one rebuilt from an artifact.
        """
        values: dict[str, Any] = {}
        for member in fields(self):
            value = getattr(self, member.name)
            values[member.name] = deepcopy(dict(value) if isinstance(value, MappingProxyType) else value, memo)
        return UniverseMetadata(**values)
