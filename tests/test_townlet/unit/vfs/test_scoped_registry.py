"""Tests for scoped variable registry."""

import pytest
import torch

from townlet.vfs.registry import ScopedVariableRegistry


def test_set_global_variable():
    """Registry stores global variables as singleton tensors."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("day_count", torch.tensor(42))

    value = registry.get_global("day_count")
    assert torch.equal(value, torch.tensor(42))


def test_get_global_variable_not_found():
    """Registry raises KeyError for missing global variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="day_count"):
        registry.get_global("day_count")


def test_global_variables_separate_from_agent():
    """Global and agent scopes are separate namespaces."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("x", torch.tensor(1))
    registry.set_agent("x", torch.tensor([2, 3]))

    assert torch.equal(registry.get_global("x"), torch.tensor(1))
    assert torch.equal(registry.get_agent("x"), torch.tensor([2, 3]))


def test_list_global_variables():
    """Registry lists all global variable names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_global("day_count", torch.tensor(0))
    registry.set_global("is_night", torch.tensor(False))

    names = registry.list_global()
    assert set(names) == {"day_count", "is_night"}
