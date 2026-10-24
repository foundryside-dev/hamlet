"""``docs/config-schemas/expressions.md`` carries the function table the registry renders.

The generated block is ``FUNCTION_SPECS`` rendered by ``scripts/gen_expression_functions_doc.py``.
A registry change without a regenerated document fails here, and every documented function
is a registered one.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from townlet.world.expression.functions import FUNCTION_SPECS

REPO_ROOT = Path(__file__).parents[5]
SCRIPT = REPO_ROOT / "scripts" / "gen_expression_functions_doc.py"
DOC = REPO_ROOT / "docs" / "config-schemas" / "expressions.md"


@pytest.fixture(scope="module")
def generator():
    spec = importlib.util.spec_from_file_location("gen_expression_functions_doc", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generated_block(generator) -> str:
    document = DOC.read_text(encoding="utf-8")
    begin = document.index(generator.BEGIN_MARKER) + len(generator.BEGIN_MARKER)
    end = document.index(generator.END_MARKER)
    return document[begin:end].lstrip("\n")


def test_document_table_is_the_rendered_registry(generator) -> None:
    assert _generated_block(generator) == generator.render_table(FUNCTION_SPECS), "run scripts/gen_expression_functions_doc.py"


def test_check_mode_reports_the_document_current(generator) -> None:
    assert generator.main(["--check"]) == 0


def test_every_registered_function_has_one_row_and_no_row_is_unregistered(generator) -> None:
    rows = re.findall(r"^\| `([a-z_0-9]+)\(", _generated_block(generator), flags=re.MULTILINE)
    assert sorted(rows) == sorted(FUNCTION_SPECS)


def test_document_carries_no_planned_labels() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    assert "planned" not in text
    assert "not yet implemented" not in text
