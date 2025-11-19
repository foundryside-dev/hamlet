"""Tests for Effects configuration DTOs."""

from townlet.config.effects_config import ReapplyPolicy


def test_reapply_policy_enum():
    """ReapplyPolicy has exactly 4 values."""
    assert ReapplyPolicy.STACK.value == "stack"
    assert ReapplyPolicy.RENEW.value == "renew"
    assert ReapplyPolicy.MERGE.value == "merge"
    assert ReapplyPolicy.REPLACE.value == "replace"


def test_reapply_policy_case_insensitive():
    """ReapplyPolicy accepts mixed case strings."""
    assert ReapplyPolicy("stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("Stack") == ReapplyPolicy.STACK
    assert ReapplyPolicy("STACK") == ReapplyPolicy.STACK
