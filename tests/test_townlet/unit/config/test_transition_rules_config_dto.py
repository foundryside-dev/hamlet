"""Tests for the transition_rules.yaml DTO layer (social-residue authoring surface).

The VTC social-residue compiler (townlet.vfs.vtc) validates rule *semantics*; this
DTO is the parse-time gate in front of it: extra="forbid" so a typo'd key fails
loudly instead of silently changing behaviour, and required-nullable behavioural
fields per the No-Defaults Principle.
"""

import pytest
from pydantic import ValidationError

from townlet.config.transition_rules_config import (
    SocialResidueRuleConfig,
    SocialResidueWriteConfig,
    TransitionRulesConfig,
)
from townlet.vfs import compile_vtc_social_residue_rules
from townlet.vfs.vtc import _SOCIAL_RESIDUE_RULE_KINDS


def _write_payload(**overrides) -> dict:
    payload = {
        "variable_id": "trust",
        "expression": "-0.15",
        "composition": "additive_delta",
        "condition": None,
        "clamp": (0.0, 1.0),
        "effect": "trust_delta",
        "scope": "pair",
    }
    payload.update(overrides)
    return payload


def _rule_payload(**overrides) -> dict:
    payload = {
        "id": "seen_stealing_damages_trust",
        "kind": "visibility_effect",
        "phase": "apply_social_residue_effects",
        "reads": ["chosen_action", "observer_mask", "trust"],
        "condition": "observer_mask and chosen_action == 7",
        "writes": [_write_payload()],
    }
    payload.update(overrides)
    return payload


def _config_payload(**overrides) -> dict:
    payload = {
        "version": "1.0",
        "social_residue": [_rule_payload()],
    }
    payload.update(overrides)
    return payload


class TestSocialResidueWriteConfig:
    def test_valid_write_parses(self):
        write = SocialResidueWriteConfig(**_write_payload())
        assert write.variable_id == "trust"
        assert write.composition == "additive_delta"
        assert write.clamp == (0.0, 1.0)
        assert write.scope == "pair"
        # Computed-at-compile fields may be omitted and default to None.
        assert write.phase is None
        assert write.priority is None
        assert write.telemetry_label is None

    def test_removed_target_field_is_rejected_at_parse_time(self):
        with pytest.raises(ValidationError, match="target"):
            SocialResidueWriteConfig(**_write_payload(target="observer -> actor"))

    def test_typo_key_is_rejected_not_silently_dropped(self):
        with pytest.raises(ValidationError, match="condtion"):
            SocialResidueWriteConfig(**{**_write_payload(), "condtion": "was_observed"})

    @pytest.mark.parametrize("field", ["condition", "clamp", "effect", "scope"])
    def test_nullable_behavioural_fields_must_be_explicit(self, field):
        payload = _write_payload()
        del payload[field]
        with pytest.raises(ValidationError, match=field):
            SocialResidueWriteConfig(**payload)

    def test_unknown_composition_rejected(self):
        with pytest.raises(ValidationError, match="composition"):
            SocialResidueWriteConfig(**_write_payload(composition="frobnicate"))

    def test_unknown_scope_rejected(self):
        # A stray scope would silently fall back to agent-shaped masking at
        # runtime; the DTO closes that hole.
        with pytest.raises(ValidationError, match="scope"):
            SocialResidueWriteConfig(**_write_payload(scope="group"))

    def test_clamp_bounds_must_be_ordered(self):
        with pytest.raises(ValidationError, match="clamp"):
            SocialResidueWriteConfig(**_write_payload(clamp=(1.0, 0.0)))

    def test_empty_condition_string_rejected(self):
        with pytest.raises(ValidationError, match="condition"):
            SocialResidueWriteConfig(**_write_payload(condition="   "))


class TestSocialResidueRuleConfig:
    def test_valid_rule_parses(self):
        rule = SocialResidueRuleConfig(**_rule_payload())
        assert rule.id == "seen_stealing_damages_trust"
        assert rule.kind == "visibility_effect"
        assert rule.reads == ("chosen_action", "observer_mask", "trust")
        assert rule.priority is None

    def test_kind_literal_matches_compiler_vocabulary(self):
        for kind in _SOCIAL_RESIDUE_RULE_KINDS:
            SocialResidueRuleConfig(**_rule_payload(kind=kind))
        with pytest.raises(ValidationError, match="kind"):
            SocialResidueRuleConfig(**_rule_payload(kind="threshold_delta"))

    def test_unknown_rule_key_rejected(self):
        with pytest.raises(ValidationError):
            SocialResidueRuleConfig(**_rule_payload(target="observer"))

    def test_rule_condition_must_be_explicit(self):
        payload = _rule_payload()
        del payload["condition"]
        with pytest.raises(ValidationError, match="condition"):
            SocialResidueRuleConfig(**payload)

    def test_empty_writes_rejected(self):
        with pytest.raises(ValidationError, match="writes"):
            SocialResidueRuleConfig(**_rule_payload(writes=[]))

    def test_empty_reads_rejected(self):
        with pytest.raises(ValidationError, match="reads"):
            SocialResidueRuleConfig(**_rule_payload(reads=[]))

    def test_negative_priority_rejected(self):
        with pytest.raises(ValidationError, match="priority"):
            SocialResidueRuleConfig(**_rule_payload(priority=-1))


class TestTransitionRulesConfig:
    def test_valid_config_parses(self):
        config = TransitionRulesConfig(**_config_payload())
        assert config.version == "1.0"
        assert len(config.social_residue) == 1

    def test_version_is_required(self):
        payload = _config_payload()
        del payload["version"]
        with pytest.raises(ValidationError, match="version"):
            TransitionRulesConfig(**payload)

    def test_social_residue_key_is_required(self):
        with pytest.raises(ValidationError, match="social_residue"):
            TransitionRulesConfig(version="1.0")

    def test_unknown_top_level_key_rejected(self):
        with pytest.raises(ValidationError):
            TransitionRulesConfig(**_config_payload(social_rules=[]))

    def test_duplicate_rule_ids_rejected(self):
        payload = _config_payload(social_residue=[_rule_payload(), _rule_payload()])
        with pytest.raises(ValidationError, match="seen_stealing_damages_trust"):
            TransitionRulesConfig(**payload)

    def test_sources_compile_through_vtc_social_residue_compiler(self):
        """The DTO's compiler-facing dump must be accepted verbatim by the
        existing VTC social-residue compiler."""
        config = TransitionRulesConfig(**_config_payload())
        program = compile_vtc_social_residue_rules(config.social_residue_sources())
        assert len(program.rules) == 1
        assert program.rules[0].rule_id == "seen_stealing_damages_trust"
        assert program.rules[0].scope == "pair"
        assert program.rules[0].clamp == (0.0, 1.0)

    def test_sources_omit_computed_fields_rather_than_passing_none(self):
        """A literal None phase would reach the compiler as the string 'None';
        computed fields must be absent from the dump instead."""
        config = TransitionRulesConfig(**_config_payload())
        (rule_source,) = config.social_residue_sources()
        (write_source,) = rule_source["writes"]
        assert "phase" not in write_source
        assert "priority" not in write_source
        assert "telemetry_label" not in write_source
        assert "priority" not in rule_source
