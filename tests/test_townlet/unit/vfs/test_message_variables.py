"""Tests for message-scope VFS variables."""

import pytest
import torch

from townlet.vfs import VariableRegistry
from townlet.vfs.schema import VariableDef, VariableScope


def _message_variable(dims: int) -> VariableDef:
    return VariableDef(
        id="recent_message_tokens",
        scope="message",
        type="message_token",
        dims=dims,
        lifetime="episode",
        readable_by=["engine", "agent"],
        writable_by=["engine"],
        default=[0.0 for _ in range(dims)],
    )


def test_message_scope_and_token_type_are_first_class_schema_values() -> None:
    assert VariableScope.MESSAGE == "message"

    variable = _message_variable(4)

    assert variable.scope == "message"
    assert variable.type == "message_token"
    assert variable.dims == 4


def test_message_variables_initialize_expected_registry_shape() -> None:
    registry = VariableRegistry(
        variables=[_message_variable(5)],
        num_agents=3,
        num_message_slots=2,
        device=torch.device("cpu"),
    )

    messages = registry.get("recent_message_tokens", reader="engine")

    assert messages.shape == torch.Size([3, 2, 5])
    assert torch.all(messages == 0.0)


def test_message_scope_requires_explicit_message_slot_extent() -> None:
    with pytest.raises(ValueError, match="num_message_slots.*positive"):
        VariableRegistry(
            variables=[_message_variable(5)],
            num_agents=3,
            device=torch.device("cpu"),
        )
