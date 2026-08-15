"""Tests for fixed-slot dynamic-need VFS variables."""

import pytest
import torch

from townlet.vfs import VariableRegistry, canonical_fixed_slot_dynamic_need_variables


def test_canonical_fixed_slot_dynamic_need_variables_match_spec_fields() -> None:
    variables = canonical_fixed_slot_dynamic_need_variables(max_slots=4)

    assert [variable.id for variable in variables] == [
        "dynamic_need_intensity",
        "dynamic_need_growth_rate",
        "dynamic_need_urgency",
        "dynamic_need_recurrence",
        "dynamic_need_substitutability",
        "dynamic_need_visibility",
        "dynamic_need_status_value",
        "dynamic_need_social_mediation",
        "dynamic_need_contagion",
        "dynamic_need_catastrophe_curve",
    ]

    for variable in variables:
        assert variable.scope == "agent"
        assert variable.type == "vecNf"
        assert variable.dims == 4
        assert variable.lifetime == "episode"
        assert variable.readable_by == ["agent", "engine", "social_model"]
        assert variable.writable_by == ["engine", "vtc"]
        assert variable.default == [0.0, 0.0, 0.0, 0.0]
        assert variable.observable is True
        assert variable.normalization is not None
        assert variable.normalization.kind == "minmax"
        assert variable.normalization.min == 0.0
        assert variable.normalization.max == 1.0


def test_canonical_fixed_slot_dynamic_need_variables_initialize_expected_registry_shape() -> None:
    registry = VariableRegistry(
        variables=list(canonical_fixed_slot_dynamic_need_variables(max_slots=3)),
        num_agents=2,
        device=torch.device("cpu"),
    )

    intensity = registry.get("dynamic_need_intensity", reader="agent")
    catastrophe_curve = registry.get("dynamic_need_catastrophe_curve", reader="social_model")

    assert intensity.shape == torch.Size([2, 3])
    assert catastrophe_curve.shape == torch.Size([2, 3])
    assert torch.all(intensity == 0.0)
    assert torch.all(catastrophe_curve == 0.0)


def test_canonical_fixed_slot_dynamic_need_variables_require_positive_max_slots() -> None:
    with pytest.raises(ValueError, match="max_slots must be positive"):
        canonical_fixed_slot_dynamic_need_variables(max_slots=0)
