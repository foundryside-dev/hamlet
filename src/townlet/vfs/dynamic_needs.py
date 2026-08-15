"""Canonical fixed-slot dynamic-need VFS variable definitions."""

from __future__ import annotations

from dataclasses import dataclass

from townlet.vfs.schema import NormalizationSpec, VariableDef

__all__ = [
    "FIXED_SLOT_DYNAMIC_NEED_FIELDS",
    "DynamicNeedTokenLayout",
    "canonical_fixed_slot_dynamic_need_variables",
    "canonical_set_encoder_dynamic_need_variables",
    "dynamic_need_token_layout",
]

FIXED_SLOT_DYNAMIC_NEED_FIELDS: tuple[str, ...] = (
    "intensity",
    "growth_rate",
    "urgency",
    "recurrence",
    "substitutability",
    "visibility",
    "status_value",
    "social_mediation",
    "contagion",
    "catastrophe_curve",
)

_SET_ENCODER_SCALAR_FIELDS: tuple[str, ...] = ("intensity", "growth_rate", "urgency")


@dataclass(frozen=True)
class DynamicNeedTokenLayout:
    """Stable shape metadata for flattened dynamic-need token observations."""

    max_slots: int
    id_embedding_dims: int
    tag_embedding_dims: int
    satisfaction_embedding_dims: int

    @property
    def token_width(self) -> int:
        """Number of features carried by each dynamic-need token."""
        return self.id_embedding_dims + len(_SET_ENCODER_SCALAR_FIELDS) + self.tag_embedding_dims + self.satisfaction_embedding_dims

    @property
    def shape(self) -> tuple[int, int]:
        """Tensor payload shape for the dynamic-need token set."""
        return (self.max_slots, self.token_width)

    def field_slice(self, field_name: str) -> slice:
        """Return the per-token feature slice for a named token field."""
        offset = 0
        if field_name == "id_embedding":
            return slice(offset, offset + self.id_embedding_dims)
        offset += self.id_embedding_dims

        for scalar_field in _SET_ENCODER_SCALAR_FIELDS:
            if field_name == scalar_field:
                return slice(offset, offset + 1)
            offset += 1

        if field_name == "tag_embedding":
            return slice(offset, offset + self.tag_embedding_dims)
        offset += self.tag_embedding_dims

        if field_name == "satisfaction_embedding":
            return slice(offset, offset + self.satisfaction_embedding_dims)

        raise KeyError(f"Unknown dynamic-need token field: {field_name}")


def dynamic_need_token_layout(
    *,
    max_slots: int,
    id_embedding_dims: int,
    tag_embedding_dims: int,
    satisfaction_embedding_dims: int,
) -> DynamicNeedTokenLayout:
    """Return shape metadata for the set-encoder dynamic-need token representation."""
    _require_positive("max_slots", max_slots)
    _require_positive("id_embedding_dims", id_embedding_dims)
    _require_positive("tag_embedding_dims", tag_embedding_dims)
    _require_positive("satisfaction_embedding_dims", satisfaction_embedding_dims)

    return DynamicNeedTokenLayout(
        max_slots=max_slots,
        id_embedding_dims=id_embedding_dims,
        tag_embedding_dims=tag_embedding_dims,
        satisfaction_embedding_dims=satisfaction_embedding_dims,
    )


def canonical_fixed_slot_dynamic_need_variables(max_slots: int) -> tuple[VariableDef, ...]:
    """Return fixed-slot dynamic-need variables with one vector field per causal dimension."""
    if max_slots <= 0:
        raise ValueError("max_slots must be positive")

    return tuple(_dynamic_need_variable(field_name, max_slots) for field_name in FIXED_SLOT_DYNAMIC_NEED_FIELDS)


def canonical_set_encoder_dynamic_need_variables(
    *,
    max_slots: int,
    id_embedding_dims: int,
    tag_embedding_dims: int,
    satisfaction_embedding_dims: int,
) -> tuple[VariableDef, ...]:
    """Return the canonical variable-token dynamic-need tensor for set encoders."""
    layout = dynamic_need_token_layout(
        max_slots=max_slots,
        id_embedding_dims=id_embedding_dims,
        tag_embedding_dims=tag_embedding_dims,
        satisfaction_embedding_dims=satisfaction_embedding_dims,
    )
    return (
        VariableDef(
            id="dynamic_need_tokens",
            scope="agent",
            type="tensor2d",
            shape=list(layout.shape),
            lifetime="episode",
            readable_by=["agent", "engine", "social_model"],
            writable_by=["engine", "vtc"],
            default=None,
            initial_value_mode="zeros",
            observable=True,
            description=(
                "Fixed-capacity variable-token dynamic-need set. Each row contains id_embedding, "
                "intensity, growth_rate, urgency, tag_embedding, and satisfaction_embedding fields."
            ),
        ),
    )


def _dynamic_need_variable(field_name: str, max_slots: int) -> VariableDef:
    return VariableDef(
        id=f"dynamic_need_{field_name}",
        scope="agent",
        type="vecNf",
        dims=max_slots,
        lifetime="episode",
        readable_by=["agent", "engine", "social_model"],
        writable_by=["engine", "vtc"],
        default=[0.0 for _ in range(max_slots)],
        observable=True,
        normalization=_unit_interval_normalization(),
        description=f"Fixed-slot dynamic-need {field_name} values for each agent.",
    )


def _unit_interval_normalization() -> NormalizationSpec:
    return NormalizationSpec(kind="minmax", min=0.0, max=1.0)


def _require_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
