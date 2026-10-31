"""Tests for the pack-scope ``transition_rules`` DTO layer.

The VTC transition-rule compiler (townlet.vfs.vtc) validates rule *semantics*; this
DTO is the parse-time gate in front of it: extra="forbid" so a typo'd key fails
loudly instead of silently changing behaviour, and required-nullable behavioural
fields per the No-Defaults Principle. A rule declares no ``reads`` (derived from
its ASTs) and no ``kind`` (VFS round-2 S8).
"""

import pytest
from pydantic import ValidationError

from townlet.config.transition_rules_config import (
    TransitionRuleConfig,
    TransitionRulesConfig,
    TransitionRuleWriteConfig,
)
from townlet.vfs import VTCWriteTarget, compile_vtc_transition_rules
from townlet.vfs.schema import VariableScope


def _write_payload(**overrides) -> dict:
    payload = {
        "variable_id": "reputation",
        "expression": "-0.15",
        "composition": "additive_delta",
        "condition": None,
        "clamp": (0.0, 1.0),
        "effect": "reputation_delta",
    }
    payload.update(overrides)
    return payload


def _rule_payload(**overrides) -> dict:
    payload = {
        "id": "seen_stealing_damages_reputation",
        "phase": "apply_transition_rules",
        "condition": "was_observed and chosen_action == 7",
        "writes": [_write_payload()],
    }
    payload.update(overrides)
    return payload


def _config_payload(**overrides) -> dict:
    payload = {
        "version": "1.0",
        "transition_rules": [_rule_payload()],
    }
    payload.update(overrides)
    return payload


class TestTransitionRuleWriteConfig:
    def test_valid_write_parses(self):
        write = TransitionRuleWriteConfig(**_write_payload())
        assert write.variable_id == "reputation"
        assert write.composition == "additive_delta"
        assert write.clamp == (0.0, 1.0)
        # Computed-at-compile fields may be omitted and default to None.
        assert write.phase is None
        assert write.priority is None
        assert write.telemetry_label is None

    def test_removed_target_field_is_rejected_at_parse_time(self):
        with pytest.raises(ValidationError, match="target"):
            TransitionRuleWriteConfig(**_write_payload(target="observer -> actor"))

    def test_typo_key_is_rejected_not_silently_dropped(self):
        with pytest.raises(ValidationError, match="condtion"):
            TransitionRuleWriteConfig(**{**_write_payload(), "condtion": "was_observed"})

    @pytest.mark.parametrize("field", ["condition", "clamp", "effect"])
    def test_nullable_behavioural_fields_must_be_explicit(self, field):
        payload = _write_payload()
        del payload[field]
        with pytest.raises(ValidationError, match=field):
            TransitionRuleWriteConfig(**payload)

    def test_unknown_composition_rejected(self):
        with pytest.raises(ValidationError, match="composition"):
            TransitionRuleWriteConfig(**_write_payload(composition="frobnicate"))

    @pytest.mark.parametrize("scope", ["pair", "agent", None])
    def test_removed_scope_field_is_rejected_at_parse_time(self, scope):
        # Masking follows the target's declared scope; an authored annotation was a
        # second authority and is an unknown key.
        with pytest.raises(ValidationError, match="scope"):
            TransitionRuleWriteConfig(**_write_payload(scope=scope))

    def test_clamp_bounds_must_be_ordered(self):
        with pytest.raises(ValidationError, match="clamp"):
            TransitionRuleWriteConfig(**_write_payload(clamp=(1.0, 0.0)))

    def test_empty_condition_string_rejected(self):
        with pytest.raises(ValidationError, match="condition"):
            TransitionRuleWriteConfig(**_write_payload(condition="   "))


class TestTransitionRuleConfig:
    def test_valid_rule_parses(self):
        rule = TransitionRuleConfig(**_rule_payload())
        assert rule.id == "seen_stealing_damages_reputation"
        assert rule.priority is None

    @pytest.mark.parametrize("field,value", [("reads", ["chosen_action"]), ("kind", "visibility_effect")])
    def test_deleted_rule_fields_are_unknown_keys(self, field, value):
        """``reads`` is derived from the ASTs and ``kind`` had no behaviour; both fail as extra keys."""
        with pytest.raises(ValidationError, match=field):
            TransitionRuleConfig(**_rule_payload(**{field: value}))

    def test_unknown_rule_key_rejected(self):
        with pytest.raises(ValidationError):
            TransitionRuleConfig(**_rule_payload(target="observer"))

    def test_rule_condition_must_be_explicit(self):
        payload = _rule_payload()
        del payload["condition"]
        with pytest.raises(ValidationError, match="condition"):
            TransitionRuleConfig(**payload)

    def test_empty_writes_rejected(self):
        with pytest.raises(ValidationError, match="writes"):
            TransitionRuleConfig(**_rule_payload(writes=[]))

    def test_negative_priority_rejected(self):
        with pytest.raises(ValidationError, match="priority"):
            TransitionRuleConfig(**_rule_payload(priority=-1))


class TestTransitionRulesConfig:
    def test_valid_config_parses(self):
        config = TransitionRulesConfig(**_config_payload())
        assert config.version == "1.0"
        assert len(config.transition_rules) == 1

    def test_version_is_required(self):
        payload = _config_payload()
        del payload["version"]
        with pytest.raises(ValidationError, match="version"):
            TransitionRulesConfig(**payload)

    def test_transition_rules_key_is_required(self):
        with pytest.raises(ValidationError, match="transition_rules"):
            TransitionRulesConfig(version="1.0")

    def test_old_family_key_is_rejected(self):
        """The ``social_residue`` list is the deleted family name: an unknown key, not an alias."""
        with pytest.raises(ValidationError, match="social_residue"):
            TransitionRulesConfig(version="1.0", social_residue=[_rule_payload()], transition_rules=[])

    def test_unknown_top_level_key_rejected(self):
        with pytest.raises(ValidationError):
            TransitionRulesConfig(**_config_payload(social_rules=[]))

    def test_duplicate_rule_ids_rejected(self):
        payload = _config_payload(transition_rules=[_rule_payload(), _rule_payload()])
        with pytest.raises(ValidationError, match="seen_stealing_damages_reputation"):
            TransitionRulesConfig(**payload)

    def test_sources_compile_through_vtc_transition_rule_compiler(self):
        """The DTO's compiler-facing dump must be accepted verbatim by the VTC compiler."""
        config = TransitionRulesConfig(**_config_payload())
        targets = {
            "reputation": VTCWriteTarget(VariableScope.AGENT, "scalar", meter=False, expression=None),
            "chosen_action": VTCWriteTarget(VariableScope.AGENT, "scalar", meter=False, expression=None),
            "was_observed": VTCWriteTarget(VariableScope.AGENT, "bool", meter=False, expression=None),
        }
        program = compile_vtc_transition_rules(config.rule_sources(), targets)
        assert len(program.rules) == 1
        assert program.rules[0].rule_id == "seen_stealing_damages_reputation"
        assert program.rules[0].target_scope == VariableScope.AGENT
        assert program.rules[0].clamp == (0.0, 1.0)
        assert program.rules[0].reads == ("chosen_action", "was_observed")

    def test_sources_omit_computed_fields_rather_than_passing_none(self):
        """A literal None phase would reach the compiler as the string 'None';
        computed fields must be absent from the dump instead."""
        config = TransitionRulesConfig(**_config_payload())
        (rule_source,) = config.rule_sources()
        (write_source,) = rule_source["writes"]
        assert "phase" not in write_source
        assert "priority" not in write_source
        assert "telemetry_label" not in write_source
        assert "priority" not in rule_source
