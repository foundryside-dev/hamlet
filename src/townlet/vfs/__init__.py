"""Variable & Feature System (VFS) module.

The VFS provides a declarative way to define variables, observations, and
action effects for the Townlet environment.

Phase 1: Schema definitions, registry, observation specs
Phase 2: Derivation graphs, complex types, expression evaluation
"""

from townlet.vfs.observation_builder import VFSObservationSpec, apply_normalization
from townlet.vfs.registry import VariableRegistry, VFSRegistryProtocol
from townlet.vfs.schema import (
    NormalizationSpec,
    ObservationField,
    VariableDef,
    WriteSpec,
)
from townlet.vfs.schema_hashes import (
    EMPTY_TRANSITION_GRAPH_HASH,
    canonical_action_schema,
    canonical_observation_schema,
    canonical_variable_schema,
    compute_action_schema_hash,
    compute_observation_schema_hash,
    compute_variable_schema_hash,
    compute_vfs_hash,
)

__all__ = [
    "EMPTY_TRANSITION_GRAPH_HASH",
    "NormalizationSpec",
    "ObservationField",
    "VariableDef",
    "VariableRegistry",
    "VFSRegistryProtocol",
    "VFSObservationSpec",
    "WriteSpec",
    "apply_normalization",
    "canonical_action_schema",
    "canonical_observation_schema",
    "canonical_variable_schema",
    "compute_action_schema_hash",
    "compute_observation_schema_hash",
    "compute_variable_schema_hash",
    "compute_vfs_hash",
]
