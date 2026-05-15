"""Canonical VFS schema hash helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from townlet.vfs.schema import NormalizationSpec, ObservationField, VariableDef, VariableScope

__all__ = [
    "canonical_observation_schema",
    "canonical_variable_schema",
    "compute_observation_schema_hash",
    "compute_variable_schema_hash",
]


def canonical_variable_schema(variables: Iterable[VariableDef]) -> list[dict[str, Any]]:
    """Return the canonical variable-schema payload used for provenance."""
    return [_canonical_variable_entry(variable) for variable in sorted(variables, key=lambda item: item.id)]


def compute_variable_schema_hash(variables: Iterable[VariableDef]) -> str:
    """Return the SHA-256 digest of the canonical variable-schema payload."""
    return _hash_payload(canonical_variable_schema(variables))


def canonical_observation_schema(fields: Iterable[ObservationField]) -> list[dict[str, Any]]:
    """Return the ordered observation-schema payload used for provenance."""
    return [_canonical_observation_entry(field) for field in fields]


def compute_observation_schema_hash(fields: Iterable[ObservationField]) -> str:
    """Return the SHA-256 digest of the canonical observation-schema payload."""
    return _hash_payload(canonical_observation_schema(fields))


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


def _canonical_observation_entry(field: ObservationField) -> dict[str, Any]:
    return {
        "id": field.id,
        "source_variable": field.source_variable,
        "shape": list(field.shape),
        "normalization": _normalization_payload(field.normalization),
        "exposed_to": sorted(field.exposed_to),
        "curriculum_active": field.curriculum_active,
        "dtype": "float32",
        "semantic_type": field.semantic_type,
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


def _normalization_payload(normalization: NormalizationSpec | None) -> dict[str, Any] | None:
    if normalization is None:
        return None
    return normalization.model_dump(mode="json", exclude_none=True)


def _hash_payload(payload: Any) -> str:
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
