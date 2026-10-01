"""An expression variable may declare its reset value; a tensor initializer may not coexist with an expression."""

import pytest
from pydantic import ValidationError

from townlet.config.variables_config import VariableDeclaration


def _base(**extra):
    return {
        "readable_by": ["engine", "agent"],
        "writable_by": ["engine"],
        "id": "day_phase",
        "scope": "global",
        "lifetime": "persistent",
        "exposed_to": [],
        "type": "scalar",
        "semantic_type": "temporal",
        **extra,
    }


def test_expression_with_declared_initial_value_is_accepted():
    var = VariableDeclaration(**_base(expression="tick", initial_value=0.0))
    assert var.expression == "tick" and var.initial_value == 0.0


def test_expression_with_tensor_initializer_refuses():
    with pytest.raises(ValidationError, match="initial_value_mode"):
        VariableDeclaration(**_base(expression="tick", initial_value_mode="zeros", shape=[2]))


def test_no_init_source_refuses():
    with pytest.raises(ValidationError, match="exactly one"):
        VariableDeclaration(**_base())
