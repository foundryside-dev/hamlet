"""Canonical relational VFS variable definitions."""

from __future__ import annotations

from townlet.vfs.schema import NormalizationSpec, VariableDef

__all__ = ["canonical_l5_relational_variables"]


def canonical_l5_relational_variables() -> tuple[VariableDef, ...]:
    """Return the canonical L5 relationship and institutional state variables."""
    return (
        VariableDef(
            id="trust",
            scope="pair",
            type="scalar",
            lifetime="episode",
            readable_by=["engine", "social_model"],
            writable_by=["vtc"],
            default=0.5,
            normalization=_unit_interval_normalization(),
            description="Directed trust from one agent toward another.",
        ),
        VariableDef(
            id="obligation",
            scope="pair",
            type="scalar",
            lifetime="episode",
            readable_by=["engine", "social_model"],
            writable_by=["vtc"],
            default=0.0,
            normalization=_unit_interval_normalization(),
            description="Directed outstanding social obligation from one agent toward another.",
        ),
        VariableDef(
            id="public_reputation",
            scope="agent",
            type="scalar",
            lifetime="episode",
            readable_by=["agent", "other_agents", "social_model", "engine"],
            writable_by=["vtc"],
            default=0.5,
            normalization=_unit_interval_normalization(),
            description="Publicly visible reputation score for each agent.",
        ),
        VariableDef(
            id="norm_legitimacy",
            scope="group",
            type="scalar",
            lifetime="episode",
            readable_by=["engine", "social_model"],
            writable_by=["vtc"],
            default=0.5,
            normalization=_unit_interval_normalization(),
            description="Group-level legitimacy of an institutional norm.",
        ),
    )


def _unit_interval_normalization() -> NormalizationSpec:
    return NormalizationSpec(kind="minmax", min=0.0, max=1.0, clip=False)
