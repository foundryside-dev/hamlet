"""Item expressions refuse at authoring because they have no runtime evaluator."""

import pytest
from pydantic import ValidationError

from townlet.config.variables_config import VariableDeclaration


def test_item_expression_refuses_before_emission():
    with pytest.raises(ValidationError, match="expression execution supports global and agent"):
        VariableDeclaration(
            readable_by=["engine", "agent"],
            writable_by=["engine"],
            id="rot",
            scope="item",
            profile="p",
            type="scalar",
            lifetime="episode",
            semantic_type="custom",
            exposed_to=[],
            initial_value=0.0,
            expression="1.0",
        )
