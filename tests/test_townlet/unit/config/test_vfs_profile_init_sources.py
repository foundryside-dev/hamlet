"""An expression variable may declare its reset value; a tensor initializer may not coexist with an expression."""

import pytest
from pydantic import ValidationError

from townlet.config.vfs_profiles_config import GlobalVFSVariableConfig


def _base(**extra):
    return {"name": "day_phase", "type": "float", "semantic_type": "temporal", **extra}


def test_expression_with_declared_initial_value_is_accepted():
    var = GlobalVFSVariableConfig(**_base(expression="tick", initial_value=0.0))
    assert var.expression == "tick" and var.initial_value == 0.0


def test_expression_with_tensor_initializer_refuses():
    with pytest.raises(ValidationError, match="initial_value_mode"):
        GlobalVFSVariableConfig(**_base(expression="tick", initial_value_mode="zeros", shape=[2]))


def test_no_init_source_refuses():
    with pytest.raises(ValidationError, match="exactly one"):
        GlobalVFSVariableConfig(**_base())
