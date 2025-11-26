"""Tests for item-scoped VFS variables."""

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


def test_item_scoped_variables_parse_from_yaml():
    """Item-scoped variables should parse from YAML config."""
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
    config = VariablesReferenceConfig(**data)

    durability_var = next(v for v in config.variables if v.id == "durability")
    assert durability_var.scope == "item"
