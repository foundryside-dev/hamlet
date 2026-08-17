"""Observation specification DTOs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Literal

from townlet.universe.dto.observation_feature import (
    METER_FEATURE,
    ObservationFeature,
    require_observation_feature,
)
from townlet.vfs.semantic_type import SemanticType, require_semantic_type


def compute_observation_field_uuid(
    *,
    name: str,
    scope: str,
    description: str | None,
    dims: int,
    semantic_type: str,
) -> str:
    """Return a deterministic UUID for an observation field.

    `semantic_type` is part of the payload, so it is REQUIRED and vocabulary-checked at the
    field boundary (PDR-0047): a field cannot be identified without knowing its group.
    """

    payload = "|".join(
        (
            scope,
            name,
            description or "",
            str(dims),
            require_semantic_type(semantic_type, where=f"observation field '{name}'"),
        )
    )
    return sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class ObservationField:
    """Single field in the flattened observation vector.

    `semantic_type` is required and drawn from the ONE closed vocabulary in
    `townlet.vfs.semantic_type` — this DTO is where the compiler is held to the same set an
    author is (PDR-0047 rule 3). It used to be `str | None`, which is how `"effects"` was
    emitted for months without any schema permitting it (DIV-005).

    `feature` is required and drawn from the ONE closed vocabulary in
    `townlet.universe.dto.observation_feature`: it says who fills the field's source variable
    (the registry, or which engine encoder), and it is what the runtime dispatches on. The
    field's NAME is a label the compiler chose — nothing may branch on it (PDR-0045). A
    `meter` field carries the meter's name in `feature_ref`; every other feature carries none.
    """

    uuid: str | None
    name: str
    type: Literal["scalar", "vector", "categorical", "spatial_grid"]
    dims: int
    start_index: int
    end_index: int
    scope: Literal["global", "agent", "agent_private"]
    description: str
    semantic_type: SemanticType
    feature: ObservationFeature
    feature_ref: str | None = None
    categorical_labels: tuple[str, ...] | None = None
    curriculum_active: bool = True

    def __post_init__(self) -> None:
        require_semantic_type(self.semantic_type, where=f"observation field '{self.name}'")
        require_observation_feature(self.feature, where=f"observation field '{self.name}'")
        if self.feature == METER_FEATURE:
            if not self.feature_ref:
                raise ValueError(
                    f"Observation field '{self.name}' is a meter feature but names no meter.\n"
                    "  Rule: a `meter` field carries the meter's name in `feature_ref`, so the "
                    "runtime maps it to a state column without parsing the field's name."
                )
        elif self.feature_ref is not None:
            raise ValueError(
                f"Observation field '{self.name}' carries feature_ref {self.feature_ref!r} but its "
                f"feature {self.feature!r} names no referent.\n"
                "  Rule: only `meter` fields carry a feature_ref."
            )
        if not self.uuid:
            generated = compute_observation_field_uuid(
                name=self.name,
                scope=self.scope,
                description=self.description,
                dims=self.dims,
                semantic_type=self.semantic_type,
            )
            object.__setattr__(self, "uuid", generated)
        if self.dims <= 0:
            raise ValueError(f"Observation field '{self.name}' must have dims > 0")
        if self.end_index <= self.start_index:
            raise ValueError(f"Observation field '{self.name}' has invalid indices: {self.start_index}..{self.end_index}")
        if self.categorical_labels is not None:
            if not self.categorical_labels:
                raise ValueError(f"Observation field '{self.name}' categorical labels cannot be empty")
            object.__setattr__(self, "categorical_labels", tuple(self.categorical_labels))


@dataclass(frozen=True)
class ObservationSpec:
    """Complete observation specification emitted by the compiler."""

    total_dims: int
    fields: tuple[ObservationField, ...] = field(default_factory=tuple)
    encoding_version: str = "1.0"

    def __post_init__(self) -> None:
        object.__setattr__(self, "fields", tuple(self.fields))
        if self.total_dims < 0:
            raise ValueError("ObservationSpec total_dims must be >= 0")
        uuids = [field.uuid for field in self.fields]
        if len(set(uuids)) != len(uuids):
            raise ValueError("ObservationSpec contains duplicate observation field UUIDs")

    def get_field_by_name(self, name: str) -> ObservationField:
        """Lookup field by name."""
        for obs_field in self.fields:
            if obs_field.name == name:
                return obs_field
        raise KeyError(f"Field '{name}' not found in observation spec")

    def get_fields_by_semantic_type(self, semantic: str) -> list[ObservationField]:
        """Return fields that share a semantic type (e.g., 'bars')."""
        return [obs_field for obs_field in self.fields if obs_field.semantic_type == semantic]

    def get_fields_by_feature(self, feature: str) -> list[ObservationField]:
        """Return the fields a given engine feature fills, in layout order.

        This is how the runtime, the structured encoders and the demo find a block: by what
        fills it, never by what it is called. Vocabulary-checked so that a typo asks for a
        member that cannot exist and fails here rather than quietly returning nothing.
        """
        require_observation_feature(feature, where="ObservationSpec.get_fields_by_feature")
        return [obs_field for obs_field in self.fields if obs_field.feature == feature]

    def get_single_field_by_feature(self, feature: str) -> ObservationField | None:
        """The one field a feature fills, or None if the spec has none.

        For the features the compiler emits at most once (grid, window, position, velocity,
        affordance, effects, temporal, item slots). Two fields for such a feature is a
        compiler defect and raises; the caller never has to guess which one it meant.
        """
        matches = self.get_fields_by_feature(feature)
        if len(matches) > 1:
            names = ", ".join(f.name for f in matches)
            raise ValueError(f"Observation spec has {len(matches)} fields for single-instance feature {feature!r}: {names}")
        return matches[0] if matches else None

    @classmethod
    def from_fields(cls, fields: Sequence[ObservationField], encoding_version: str = "1.0") -> ObservationSpec:
        """Helper for building from a sequence while auto-computing dims."""
        total_dims = sum(field.dims for field in fields)
        return cls(total_dims=total_dims, fields=tuple(fields), encoding_version=encoding_version)
