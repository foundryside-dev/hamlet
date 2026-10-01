"""Scope and copy contracts on the single checked VariableRegistry implementation."""

import pytest
import torch

from townlet.vfs.registry import VariableRegistry
from townlet.vfs.schema import VariableDef


def _registry() -> VariableRegistry:
    variables = [
        VariableDef(
            id="world",
            scope="global",
            type="scalar",
            lifetime="episode",
            default=1.0,
            readable_by=["engine", "agent"],
            writable_by=["engine"],
        ),
        VariableDef(
            id="local",
            scope="agent",
            type="scalar",
            lifetime="episode",
            default=2.0,
            readable_by=["engine", "agent"],
            writable_by=["engine"],
        ),
    ]
    return VariableRegistry(variables, 3, torch.device("cpu"))


def test_scope_inventory_and_batch_shapes() -> None:
    registry = _registry()
    assert registry.list_global() == ["world"]
    assert registry.list_agent() == ["local"]
    assert registry.get_global("world", reader="engine").shape == ()
    assert registry.get_agent("local", reader="agent").shape == (3,)
    with pytest.raises(KeyError, match="not global"):
        registry.get_global("local", reader="engine")
    with pytest.raises(KeyError, match="not agent"):
        registry.get_agent("world", reader="engine")


@pytest.mark.parametrize("name,getter", [("world", "get_global"), ("local", "get_agent")])
def test_scoped_values_are_copies_and_checked_writes_reset(name: str, getter: str) -> None:
    registry = _registry()
    value = getattr(registry, getter)(name, reader="engine")
    value.fill_(8.0)
    assert not torch.equal(value, registry.get(name, reader="engine"))
    registry.set(name, value, writer="engine")
    value.zero_()
    assert torch.all(registry.get(name, reader="agent") == 8.0)
    registry.reset_episode_scoped()
    assert torch.all(registry.get(name, reader="engine") == (1.0 if name == "world" else 2.0))


def test_registry_has_one_canonical_namespace() -> None:
    variables = list(_registry().variables.values())
    variables.append(variables[0].model_copy(update={"scope": "agent"}))
    with pytest.raises(ValueError, match="Duplicate variable id"):
        VariableRegistry(variables, 3, torch.device("cpu"))
