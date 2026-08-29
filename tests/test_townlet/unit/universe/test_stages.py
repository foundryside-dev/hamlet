"""Tests for the authoritative compile-pipeline stage enum."""

from __future__ import annotations

import pytest

from townlet.universe.errors import CompilationError
from townlet.universe.stages import CompilationStage
from townlet.universe.symbol_table import UniverseSymbolTable


def test_stage_numbers_are_contiguous_and_ordered() -> None:
    numbers = [stage.number for stage in CompilationStage]
    assert numbers == list(range(len(numbers)))


def test_stage_labels_cite_number_and_description() -> None:
    for stage in CompilationStage:
        assert stage.label == f"Stage {stage.number}: {stage.description}"


def test_pipeline_order_is_the_documented_sequence() -> None:
    assert [stage.name for stage in CompilationStage] == [
        "PREFLIGHT",
        "PARSE",
        "LIMITS",
        "SEMANTICS",
        "SYMBOLS",
        "RESOLVE",
        "SHARED",
        "LEVELS",
        "EMIT",
    ]


def test_symbol_table_errors_cite_the_enum_label() -> None:
    table = UniverseSymbolTable()

    class _Meter:
        name = "energy"

    table.register_meter(_Meter())
    with pytest.raises(CompilationError) as excinfo:
        table.register_meter(_Meter())

    assert CompilationStage.SYMBOLS.label in str(excinfo.value)
