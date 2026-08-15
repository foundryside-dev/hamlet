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


def test_item_scoped_variables_rejected_from_variables_reference_yaml():
    """variables_reference.yaml must reject item scope; item vars live in profiles."""
    from townlet.config.vfs_config import VariablesReferenceConfig

    yaml_content = """
version: "1.0"
variables:
  - id: durability
    scope: item
    type: scalar
    default: 100.0
    lifetime: persistent
    readable_by: [agent, engine]
    writable_by: [actions, engine]
    description: Item durability
"""

    from io import StringIO

    import yaml

    data = yaml.safe_load(StringIO(yaml_content))

    with pytest.raises(ValidationError, match="item-scoped variables"):
        VariablesReferenceConfig(**data)
