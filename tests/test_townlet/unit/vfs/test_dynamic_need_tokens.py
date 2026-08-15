"""Tests for set-encoder dynamic-need VFS variables."""

import pytest
import torch

from townlet.vfs import (
    VariableRegistry,
    canonical_set_encoder_dynamic_need_variables,
    dynamic_need_token_layout,
)


def _slice_tuple(value: slice) -> tuple[int | None, int | None, int | None]:
    return (value.start, value.stop, value.step)


def test_dynamic_need_token_layout_matches_spec_fields() -> None:
    layout = dynamic_need_token_layout(
        max_slots=3,
        id_embedding_dims=4,
        tag_embedding_dims=2,
        satisfaction_embedding_dims=5,
    )

    assert layout.max_slots == 3
    assert layout.token_width == 14
    assert layout.shape == (3, 14)
    assert _slice_tuple(layout.field_slice("id_embedding")) == (0, 4, None)
    assert _slice_tuple(layout.field_slice("intensity")) == (4, 5, None)
    assert _slice_tuple(layout.field_slice("growth_rate")) == (5, 6, None)
    assert _slice_tuple(layout.field_slice("urgency")) == (6, 7, None)
    assert _slice_tuple(layout.field_slice("tag_embedding")) == (7, 9, None)
    assert _slice_tuple(layout.field_slice("satisfaction_embedding")) == (9, 14, None)


def test_canonical_set_encoder_dynamic_need_variables_create_tensor_tokens() -> None:
    variables = canonical_set_encoder_dynamic_need_variables(
        max_slots=3,
        id_embedding_dims=4,
        tag_embedding_dims=2,
        satisfaction_embedding_dims=5,
    )

    assert [variable.id for variable in variables] == ["dynamic_need_tokens"]

    dynamic_need_tokens = variables[0]
    assert dynamic_need_tokens.scope == "agent"
    assert dynamic_need_tokens.type == "tensor2d"
    assert dynamic_need_tokens.shape == [3, 14]
    assert dynamic_need_tokens.lifetime == "episode"
    assert dynamic_need_tokens.readable_by == ["agent", "engine", "social_model"]
    assert dynamic_need_tokens.writable_by == ["engine", "vtc"]
    assert dynamic_need_tokens.default is None
    assert dynamic_need_tokens.initial_value_mode == "zeros"
    assert dynamic_need_tokens.observable is True


def test_set_encoder_dynamic_need_variables_initialize_registry_shape() -> None:
    registry = VariableRegistry(
        variables=list(
            canonical_set_encoder_dynamic_need_variables(
                max_slots=3,
                id_embedding_dims=4,
                tag_embedding_dims=2,
                satisfaction_embedding_dims=5,
            )
        ),
        num_agents=2,
        device=torch.device("cpu"),
    )

    tokens = registry.get("dynamic_need_tokens", reader="agent")

    assert tokens.shape == torch.Size([2, 3, 14])
    assert torch.all(tokens == 0.0)


def test_dynamic_need_token_layout_requires_positive_extents() -> None:
    with pytest.raises(ValueError, match="max_slots must be positive"):
        dynamic_need_token_layout(
            max_slots=0,
            id_embedding_dims=4,
            tag_embedding_dims=2,
            satisfaction_embedding_dims=5,
        )

    with pytest.raises(ValueError, match="id_embedding_dims must be positive"):
        dynamic_need_token_layout(
            max_slots=3,
            id_embedding_dims=0,
            tag_embedding_dims=2,
            satisfaction_embedding_dims=5,
        )
