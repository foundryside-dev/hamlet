"""Negative controls for Cut B's independent before/after evidence comparator."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

_SCRIPT = Path(__file__).resolve().parents[4] / "scripts/check_declaration_cut_b.py"
_SPEC = importlib.util.spec_from_file_location("cut_b_comparator", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
comparator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(comparator)


def test_missing_null_and_numeric_type_changes_are_visible():
    changes = comparator.differences({"removed": None, "typed": True}, {"added": None, "typed": 1})
    assert changes == [
        {"path": "/added", "before_present": False, "after_present": True, "after": None},
        {"path": "/removed", "before_present": True, "after_present": False, "before": None},
        {"path": "/typed", "before_present": True, "after_present": True, "before": True, "after": 1},
    ]


def test_exact_attribution_and_stale_missing_or_wrong_value_controls():
    change = {
        "kind": "hash",
        "pack": "pack",
        "level": "level",
        "path": "/variable_schema_hash",
        "before_present": True,
        "after_present": True,
        "before": "a",
        "after": "b",
    }
    approval = {**change, "cause": "canonical variable lifetime", "causing_commit": "1234567", "register_ref": "DIV-014"}
    unexplained, stale = comparator.classify_changes([dict(change)], [approval])
    assert unexplained == stale == []
    assert comparator.classify_changes([dict(change)], [])[0] == [change]
    assert comparator.classify_changes([], [approval])[1] == [approval]
    assert comparator.classify_changes([dict(change)], [{**approval, "after": "c"}])[0] == [change]
    with pytest.raises(ValueError, match="Duplicate attribution"):
        comparator.classify_changes([dict(change)], [approval, approval])
    with pytest.raises(ValueError, match="lacks explicit cause"):
        comparator.classify_changes([dict(change)], [{**approval, "cause": ""}])


def test_numeric_coercion_does_not_authorize_a_different_reset_value():
    change = {
        "kind": "reset",
        "pack": "pack",
        "level": "level",
        "path": "/initial/foo/values",
        "before_present": True,
        "after_present": True,
        "before": [0],
        "after": [True],
    }
    approval = {**change, "after": [1], "cause": "declared reset", "causing_commit": "1234567", "register_ref": "DIV-014"}
    assert comparator.classify_changes([change], [approval])[0] == [change]


def test_stream_bytes_keep_signed_zero_distinct_and_identical_nan_equal():
    before = np.array([[0.0, np.nan]], dtype=np.float32)
    after = before.copy()
    assert comparator.compare_stream(before, after)["equal"] is True
    after[0, 0] = -0.0
    difference = comparator.compare_stream(before, after)
    assert difference["equal"] is False
    assert difference["first_indices"] == [[0, 0]]
    assert difference["differing_element_count"] == 1
    assert comparator.compare_stream(before, before.astype(np.float64))["equal"] is False
    assert comparator.compare_stream(before, before.reshape(2, 1))["equal"] is False
