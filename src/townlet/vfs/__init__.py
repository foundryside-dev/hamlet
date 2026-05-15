"""Variable & Feature System (VFS) module.

The VFS provides a declarative way to define variables, observations, and
action effects for the Townlet environment.

Phase 1: Schema definitions, registry, observation specs
Phase 2: Derivation graphs, complex types, expression evaluation
"""

from townlet.vfs.observation_builder import VFSObservationSpec
from townlet.vfs.registry import VariableRegistry, VFSRegistryProtocol
from townlet.vfs.schema import (
    NormalizationSpec,
    ObservationField,
    VariableDef,
    WriteSpec,
)

__all__ = [
    "NormalizationSpec",
    "ObservationField",
    "VariableDef",
    "VariableRegistry",
    "VFSRegistryProtocol",
    "VFSObservationSpec",
    "WriteSpec",
]
