"""Canonical VFS schema hash helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope

__all__ = [
    "canonical_variable_schema",
    "compute_variable_schema_hash",
]


def canonical_variable_schema(variables: Iterable[VariableDef]) -> list[dict[str, Any]]:
    """Return the canonical variable-schema payload used for provenance."""
    return [_canonical_variable_entry(variable) for variable in sorted(variables, key=lambda item: item.id)]


def compute_variable_schema_hash(variables: Iterable[VariableDef]) -> str:
    """Return the SHA-256 digest of the canonical variable-schema payload."""
    payload = json.dumps(
        canonical_variable_schema(variables),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _canonical_variable_entry(variable: VariableDef) -> dict[str, Any]:
    return {
        "id": variable.id,
        "type": variable.type,
        "scope": _scope_value(variable.scope),
        "dims": variable.dims,
        "lifetime": variable.lifetime,
        "readable_by": sorted(variable.readable_by),
        "writable_by": sorted(variable.writable_by),
        "range": _normalization_range(variable.normalization),
    }


def _scope_value(scope: VariableScope | str) -> str:
    if isinstance(scope, VariableScope):
        return scope.value
    return scope


def _normalization_range(normalization: NormalizationSpec | None) -> list[Any] | None:
    if normalization is None:
        return None
    if normalization.min is None or normalization.max is None:
        return None
    return [normalization.min, normalization.max]
