"""Configuration DTOs for transition_rules.yaml (experiment-level VTC rule families).

This is the parse-time gate in front of the VTC social-residue compiler
(townlet.vfs.vtc.compile_vtc_social_residue_rules). The compiler validates rule
semantics; this layer enforces the authoring contract: extra="forbid" so a stray
or typo'd key fails at parse instead of silently changing behaviour, and
nullable behavioural fields (condition, clamp, effect, scope) that must be set
explicitly per the No-Defaults Principle. Fields the compiler derives when
absent (write-level phase/priority/telemetry_label, rule-level priority) are
computed values and may be omitted.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = [
    "SocialResidueRuleConfig",
    "SocialResidueWriteConfig",
    "TransitionRulesConfig",
]


class SocialResidueWriteConfig(BaseModel):
    """One variable write carried by a social-residue rule.

    Mirrors townlet.vfs.schema.WriteSpec's grammar, with two differences the
    social-residue compiler defines: phase/priority/telemetry_label are derived
    from the owning rule when omitted, and effect/scope annotate relationship
    semantics (scope "pair" masks by the symmetric active-agent mask).
    """

    model_config = ConfigDict(extra="forbid")

    variable_id: str = Field(
        min_length=1,
        description="ID of the VFS variable to write to",
    )

    expression: str = Field(
        min_length=1,
        description="Expression evaluated through the VTC expression runtime",
    )

    composition: Literal[
        "overwrite",
        "additive_delta",
        "multiplicative_modifier",
        "min",
        "max",
        "clamp",
        "priority_write",
        "last_write_wins",
        "claim_if_free",
        "capacity_claim",
        "append_event",
    ] = Field(
        description="How to compose this write with other writes targeting the same variable in the same phase",
    )

    condition: str | None = Field(
        description="Optional predicate gating this write, combined with the rule-level condition. Pass null for unconditional writes.",
    )

    clamp: tuple[float, float] | None = Field(
        description="Optional inclusive post-write bounds. Pass null when no clamp applies.",
    )

    effect: str | None = Field(
        description="Relationship-effect label (e.g. trust_delta), used in derived telemetry labels. Pass null when unlabelled.",
    )

    scope: Literal["pair", "agent"] | None = Field(
        description="Write masking scope. 'pair' masks by the symmetric active-agent mask; null infers from the target shape.",
    )

    phase: str | None = Field(
        default=None,
        description="Transition phase override; inherits the rule's phase when omitted (computed)",
    )

    priority: int | None = Field(
        default=None,
        ge=0,
        description="Ordering key override within the phase; derived from the rule when omitted (computed)",
    )

    telemetry_label: str | None = Field(
        default=None,
        min_length=1,
        description="Audit label override; derived as kind:rule_id:effect when omitted (computed)",
    )

    @model_validator(mode="after")
    def validate_write(self) -> SocialResidueWriteConfig:
        if self.condition is not None and not self.condition.strip():
            raise ValueError("condition must be null or a non-empty expression")
        if self.clamp is not None:
            low, high = self.clamp
            if low > high:
                raise ValueError("clamp lower bound must be <= upper bound")
        return self


class SocialResidueRuleConfig(BaseModel):
    """One declarative relationship/social-state rule."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        min_length=1,
        description="Unique rule identifier, carried into telemetry labels",
    )

    kind: Literal["visibility_effect", "social_residue", "institutional_rule"] = Field(
        description="Rule family (must match the VTC social-residue compiler's vocabulary)",
    )

    phase: str = Field(
        min_length=1,
        description="Transition phase the rule's writes default to (canonically apply_social_residue_effects)",
    )

    reads: tuple[str, ...] = Field(
        min_length=1,
        description="Variables the rule's condition/expressions read; direction lives in this declared data",
    )

    condition: str | None = Field(
        description="Optional rule-level predicate combined with each write's condition. Pass null for unconditional rules.",
    )

    writes: tuple[SocialResidueWriteConfig, ...] = Field(
        min_length=1,
        description="Variable writes this rule performs",
    )

    priority: int | None = Field(
        default=None,
        ge=0,
        description="Ordering key within the phase; derived from declaration order when omitted (computed)",
    )

    @model_validator(mode="after")
    def validate_rule(self) -> SocialResidueRuleConfig:
        if self.condition is not None and not self.condition.strip():
            raise ValueError("condition must be null or a non-empty expression")
        return self


class TransitionRulesConfig(BaseModel):
    """Top-level schema for an experiment-level transition_rules.yaml."""

    model_config = ConfigDict(extra="forbid")

    version: Literal["1.0"] = Field(description="Config schema version")

    social_residue: tuple[SocialResidueRuleConfig, ...] = Field(
        description="Declarative social-residue rules compiled into the transition schedule",
    )

    @model_validator(mode="after")
    def validate_unique_rule_ids(self) -> TransitionRulesConfig:
        seen: set[str] = set()
        for rule in self.social_residue:
            if rule.id in seen:
                raise ValueError(f"Duplicate social_residue rule id '{rule.id}'")
            seen.add(rule.id)
        return self

    def social_residue_sources(self) -> tuple[dict[str, Any], ...]:
        """Compiler-facing dump for compile_vtc_social_residue_rules.

        Computed fields are omitted rather than passed as None: the compiler
        stringifies a present-but-None phase, so absence is the only correct
        encoding for "derive this".
        """
        return tuple(rule.model_dump(exclude_none=True) for rule in self.social_residue)
