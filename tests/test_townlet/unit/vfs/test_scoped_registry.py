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


def test_set_agent_variable():
    """Registry stores agent variables as batch tensors."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_agent("motivation", torch.tensor([1.0, 0.8, 1.2]))

    value = registry.get_agent("motivation")
    assert torch.equal(value, torch.tensor([1.0, 0.8, 1.2]))


def test_get_agent_variable_not_found():
    """Registry raises KeyError for missing agent variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="motivation"):
        registry.get_agent("motivation")


def test_agent_batch_dimension():
    """Agent variables have batch dimension."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    batch_size = 64
    registry.set_agent("is_crisis", torch.zeros(batch_size, dtype=torch.bool))

    value = registry.get_agent("is_crisis")
    assert value.shape == (batch_size,)


def test_list_agent_variables():
    """Registry lists all agent variable names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_agent("motivation", torch.tensor([1.0]))
    registry.set_agent("is_crisis", torch.tensor([False]))

    names = registry.list_agent()
    assert set(names) == {"motivation", "is_crisis"}


def test_set_item_variable():
    """Registry stores item variables per profile."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    # food_stats profile has 2 instances with nutrition values
    registry.set_item("food_stats", "nutrition", torch.tensor([0.5, 0.3]))

    value = registry.get_item("food_stats", "nutrition")
    assert torch.equal(value, torch.tensor([0.5, 0.3]))


def test_get_item_variable_not_found():
    """Registry raises KeyError for missing item variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    with pytest.raises(KeyError, match="food_stats"):
        registry.get_item("food_stats", "nutrition")


def test_item_profiles_separate_namespaces():
    """Item profiles are separate namespaces."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("weapon_stats", "damage", torch.tensor([10.0]))

    # Same variable name in different profiles
    registry.set_item("food_stats", "value", torch.tensor([1.0]))
    registry.set_item("weapon_stats", "value", torch.tensor([50.0]))

    assert torch.equal(registry.get_item("food_stats", "value"), torch.tensor([1.0]))
    assert torch.equal(registry.get_item("weapon_stats", "value"), torch.tensor([50.0]))


def test_list_item_profiles():
    """Registry lists all item profile names."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("weapon_stats", "damage", torch.tensor([10.0]))

    profiles = registry.list_item_profiles()
    assert set(profiles) == {"food_stats", "weapon_stats"}


def test_list_item_variables_in_profile():
    """Registry lists all variables in a profile."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))

    registry.set_item("food_stats", "nutrition", torch.tensor([0.5]))
    registry.set_item("food_stats", "is_spoiled", torch.tensor([False]))

    variables = registry.list_item_variables("food_stats")
    assert set(variables) == {"nutrition", "is_spoiled"}


def test_global_variable_defensive_copy():
    """Retrieved tensors don't alias internal storage (global scope)."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(42))

    day_count = registry.get_global("day_count")
    day_count.fill_(999)  # Mutate returned tensor

    # Internal storage should be unchanged
    assert registry.get_global("day_count") == 42


def test_agent_variable_defensive_copy():
    """Retrieved tensors don't alias internal storage (agent scope)."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_agent("motivation", torch.tensor([1.0, 0.8, 1.2]))

    motivation = registry.get_agent("motivation")
    motivation[0] = 999.0  # Mutate returned tensor

    # Internal storage should be unchanged
    assert torch.equal(registry.get_agent("motivation"), torch.tensor([1.0, 0.8, 1.2]))


def test_item_variable_defensive_copy():
    """Retrieved tensors don't alias internal storage (item scope)."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_item("food", "nutrition", torch.tensor([0.5]))

    nutrition = registry.get_item("food", "nutrition")
    nutrition[0] = 999.0  # Mutate returned tensor

    # Internal storage should be unchanged
    assert registry.get_item("food", "nutrition")[0] == 0.5
