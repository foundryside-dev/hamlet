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


def test_scope_batch_shapes() -> None:
    registry = _registry()
    assert registry.get("world", reader="engine").shape == ()
    assert registry.get("local", reader="agent").shape == (3,)


@pytest.mark.parametrize("name", ["world", "local"])
def test_scoped_values_are_copies_and_checked_writes_reset(name: str) -> None:
    registry = _registry()
    value = registry.get(name, reader="engine")
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
