"""Tests for Effects configuration DTOs."""

from townlet.config.effects_config import EffectScope, ReapplyPolicy


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


def test_effect_scope_enum():
    """EffectScope has exactly 4 values."""
    assert EffectScope.GLOBAL.value == "global"
    assert EffectScope.AGENT.value == "agent"
    assert EffectScope.ITEM.value == "item"
    assert EffectScope.AFFORDANCE.value == "affordance"


def test_effect_scope_case_insensitive():
    """EffectScope accepts mixed case strings."""
    assert EffectScope("global") == EffectScope.GLOBAL
    assert EffectScope("Global") == EffectScope.GLOBAL
    assert EffectScope("GLOBAL") == EffectScope.GLOBAL
