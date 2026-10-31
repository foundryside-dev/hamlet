"""The one place a declared VFS type meets a torch storage dtype.

Three facts live here so that the registry, the VTC programs and the profile
evaluator cannot disagree about them:

- which dtype a declared type is stored as (``storage_dtype``);
- which expression-DSL result types a write may produce for a declared type
  (``admitted_write_result_types``), the compile-time half of write validation;
- the single runtime conversion a storage write admits (``to_storage_dtype``):
  an integer-typed DSL result widening into float32 storage. The DSL's ``int`` is a
  type-level distinction (``7``, ``where(c, 1, 0)``); scalar storage is float32 and
  the authoring contract says scalar expressions "do not promise integer registry
  storage". Everything else — float into bool, float into a reference, bool into a
  number — is refused, never cast.
"""

from __future__ import annotations

import torch

__all__ = [
    "BATCH_ROW_REFERENCE_TYPES",
    "ELEMENT_PAYLOAD_TYPES",
    "NON_NUMERIC_TYPES",
    "admitted_write_result_types",
    "storage_dtype",
    "to_storage_dtype",
]

#: References whose stored value is a batch row: an agent row is its world (S1), an item
#: row belongs to one world. A constant one is another world's entity everywhere but one
#: world, so authored constants are refused (declaration and write) and the registry
#: refuses any stored value outside the row's own world.
BATCH_ROW_REFERENCE_TYPES = frozenset({"agent_ref", "item_ref"})

#: Declared types whose value is no quantity a clamp can bound: a truth value, or a row index
#: (a reference names a row; bounding it rewrites which row it names). A write ``clamp`` on one
#: is refused at compile (``vfs.vtc._write_type_refusal``).
NON_NUMERIC_TYPES = frozenset({"bool", "agent_ref", "item_ref", "affordance_ref", "effect_ref"})

#: Declared types whose row carries elements: a vector's components, a tensor's cells. A write
#: expression is a number (``admitted_write_result_types``), so writing one spreads it over every
#: element; the compiler admits that only for a constant, never for a per-row value
#: (``vfs.vtc._element_payload_refusal``).
ELEMENT_PAYLOAD_TYPES = frozenset({"vec2i", "vec3i", "vec2f", "vec3f", "vecNi", "vecNf", "tensor1d", "tensor2d", "tensor3d", "tensorNd"})

_LONG_TYPES = frozenset({"agent_ref", "item_ref", "affordance_ref", "effect_ref", "vecNi", "vec2i", "vec3i"})
_INTEGER_DTYPES = frozenset({torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8})


def storage_dtype(var_type: str) -> torch.dtype:
    """The dtype the registry allocates for a declared VFS type."""
    if var_type in _LONG_TYPES:
        return torch.long
    if var_type == "bool":
        return torch.bool
    return torch.float32


def admitted_write_result_types(var_type: str) -> frozenset[str]:
    """Expression-DSL result types a write expression may produce for ``var_type``.

    Mirrors ``VFSProfileCompiler.compile_variable``: a scalar admits the DSL's two
    numeric types, a bool admits only bool, integer storage admits only int, and a
    batch-row reference also admits a read of its own type (``aref <- aref2``,
    ``where(c, aref2, -1)``). A cross-typed reference (``item_ref <- agent_ref``) is
    refused; whether an int is the null or ``agent_id`` is the write's world-locality
    proof (``vfs.vtc._world_local_reference``).
    """
    if var_type in BATCH_ROW_REFERENCE_TYPES:
        return frozenset({"int", var_type})
    dtype = storage_dtype(var_type)
    if dtype == torch.bool:
        return frozenset({"bool"})
    if dtype == torch.long:
        return frozenset({"int"})
    return frozenset({"int", "float"})


def to_storage_dtype(value: torch.Tensor, dtype: torch.dtype, label: str) -> torch.Tensor:
    """Return ``value`` in storage ``dtype``: identity, or integer widening into float32.

    Raises ValueError for any other conversion; the compile-time type check makes
    that unreachable for authored writes, so reaching it is an engine defect.
    """
    if value.dtype == dtype:
        return value
    if dtype == torch.float32 and value.dtype in _INTEGER_DTYPES:
        return value.to(dtype=torch.float32)
    raise ValueError(f"{label} has dtype {value.dtype}, expected {dtype}; storage writes never coerce dtype")
