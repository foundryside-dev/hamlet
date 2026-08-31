"""Canonical fixed-slot dynamic-need VFS variable definitions."""

from __future__ import annotations

from townlet.vfs.schema import NormalizationSpec, VariableDef

__all__ = [
    "FIXED_SLOT_DYNAMIC_NEED_FIELDS",
    "canonical_fixed_slot_dynamic_need_variables",
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


def canonical_fixed_slot_dynamic_need_variables(max_slots: int) -> tuple[VariableDef, ...]:
    """Return fixed-slot dynamic-need variables with one vector field per causal dimension."""
    if max_slots <= 0:
        raise ValueError("max_slots must be positive")

    return tuple(_dynamic_need_variable(field_name, max_slots) for field_name in FIXED_SLOT_DYNAMIC_NEED_FIELDS)


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
    return NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False)
