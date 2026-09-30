"""Tests for item-scoped VFS variables."""

import pytest
from pydantic import ValidationError

from townlet.vfs.schema import VariableDef, VariableScope


def test_item_scope_is_valid():
    """Item scope should be recognized as valid scope."""
    var = VariableDef(
        id="durability",
        scope=VariableScope.ITEM,
        type="scalar",
        default=100.0,
        lifetime="persistent",
        readable_by=["agent", "engine"],
        writable_by=["actions", "engine"],
        description="Item durability (0-100)",
    )

    assert var.scope == VariableScope.ITEM
    assert var.id == "durability"


def test_item_variable_uses_the_canonical_declaration_contract():
    """Item state uses the same explicit fields and a qualified profile group."""
    from townlet.config.variables_config import VariableDeclaration

    payload = {
        "id": "durability",
        "scope": "item",
        "profile": "equipment",
        "type": "scalar",
        "initial_value": 100.0,
        "lifetime": "episode",
        "semantic_type": "custom",
        "exposed_to": [],
    }
    variable = VariableDeclaration.model_validate(payload)
    assert variable.id == "durability"
    assert variable.profile == "equipment"
    for unsupported in ({"profile": None}, {"lifetime": "persistent"}):
        with pytest.raises(ValidationError):
            VariableDeclaration.model_validate({**payload, **unsupported})
