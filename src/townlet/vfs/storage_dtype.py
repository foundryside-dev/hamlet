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

__all__ = ["admitted_write_result_types", "storage_dtype", "to_storage_dtype"]

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
    numeric types, a bool admits only bool, integer storage admits only int.
    """
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
