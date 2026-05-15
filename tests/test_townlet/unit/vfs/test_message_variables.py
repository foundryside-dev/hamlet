"""Tests for canonical L6 message-scope VFS variables."""

import pytest
import torch

from townlet.vfs import VariableRegistry, canonical_l6_message_variables
from townlet.vfs.schema import VariableDef, VariableScope


def test_message_scope_and_token_type_are_first_class_schema_values() -> None:
    assert VariableScope.MESSAGE == "message"

    variable = VariableDef(
        id="scratch_message",
        scope="message",
        type="message_token",
        dims=4,
        lifetime="episode",
        readable_by=["agent", "social_model"],
        writable_by=["vtc"],
        default=[0.0, 0.0, 0.0, 0.0],
    )

    assert variable.scope == "message"
    assert variable.type == "message_token"
    assert variable.dims == 4


def test_canonical_l6_message_variables_match_spec_metadata() -> None:
    variables = canonical_l6_message_variables(message_token_dims=5)

    assert [variable.id for variable in variables] == ["recent_message_tokens"]

    recent_messages = variables[0]
    assert recent_messages.scope == "message"
    assert recent_messages.type == "message_token"
    assert recent_messages.dims == 5
    assert recent_messages.lifetime == "episode"
    assert recent_messages.readable_by == ["agent", "social_model"]
    assert recent_messages.writable_by == ["vtc"]
    assert recent_messages.default == [0.0, 0.0, 0.0, 0.0, 0.0]


def test_canonical_l6_message_variables_initialize_expected_registry_shape() -> None:
    registry = VariableRegistry(
        variables=list(canonical_l6_message_variables(message_token_dims=5)),
        num_agents=3,
        num_message_slots=2,
        device=torch.device("cpu"),
    )

    messages = registry.get("recent_message_tokens", reader="social_model")

    assert messages.shape == torch.Size([3, 2, 5])
    assert torch.all(messages == 0.0)


def test_message_scope_requires_explicit_message_slot_extent() -> None:
    with pytest.raises(ValueError, match="num_message_slots.*positive"):
        VariableRegistry(
            variables=list(canonical_l6_message_variables(message_token_dims=5)),
            num_agents=3,
            device=torch.device("cpu"),
        )
