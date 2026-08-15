"""Canonical VFS schema hash helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from townlet.vfs.schema import NormalizationSpec, ObservationField, VariableDef, VariableScope
from townlet.vfs.transition_graph import TransitionPhaseGraph

__all__ = [
    "canonical_action_schema",
    "canonical_observation_schema",
    "canonical_transition_graph_schema",
    "canonical_variable_schema",
    "compute_action_schema_hash",
    "compute_observation_schema_hash",
    "compute_transition_graph_hash",
    "compute_variable_schema_hash",
    "compute_vfs_hash",
]


def canonical_variable_schema(variables: Iterable[VariableDef]) -> list[dict[str, Any]]:
    """Return the canonical variable-schema payload used for provenance."""
    return [_canonical_variable_entry(variable) for variable in sorted(variables, key=lambda item: item.id)]


def compute_variable_schema_hash(variables: Iterable[VariableDef]) -> str:
    """Return the SHA-256 digest of the canonical variable-schema payload."""
    return _hash_payload(canonical_variable_schema(variables))


def canonical_observation_schema(fields: Iterable[ObservationField]) -> list[dict[str, Any]]:
    """Return the ordered observation-schema payload used for provenance."""
    return [_canonical_observation_entry(field) for field in fields]


def compute_observation_schema_hash(fields: Iterable[ObservationField]) -> str:
    """Return the SHA-256 digest of the canonical observation-schema payload."""
    return _hash_payload(canonical_observation_schema(fields))


def canonical_action_schema(actions: Iterable[Any]) -> list[dict[str, Any]]:
    """Return the action-space payload used for policy/action ABI provenance."""
    return [_canonical_action_entry(action) for action in sorted(actions, key=lambda item: item.id)]


def compute_action_schema_hash(actions: Iterable[Any]) -> str:
    """Return the SHA-256 digest of the canonical action-space payload."""
    return _hash_payload(canonical_action_schema(actions))


def canonical_transition_graph_schema(
    phase_graph: TransitionPhaseGraph,
    action_write_program: Any,
    *,
    affordance_gate_program: Any | None = None,
    interaction_progress_program: Any | None = None,
    terminal_condition_program: Any | None = None,
    threshold_cascade_program: Any | None = None,
    modulation_program: Any | None = None,
    passive_depletion_program: Any | None = None,
    social_residue_program: Any | None = None,
    reward_component_program: Any | None = None,
) -> dict[str, Any]:
    """Return the transition-graph payload used for world-physics provenance."""
    rules = [_canonical_transition_rule(write) for write in action_write_program.writes]
    if affordance_gate_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in affordance_gate_program.rules)
    if interaction_progress_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in interaction_progress_program.progress_rules)
        rules.extend(_canonical_transition_rule(rule) for rule in interaction_progress_program.completion_bonus_rules)
    if terminal_condition_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in terminal_condition_program.rules)
    if passive_depletion_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in passive_depletion_program.rules)
    if modulation_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in modulation_program.rules)
    if threshold_cascade_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in threshold_cascade_program.rules)
    if social_residue_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in social_residue_program.rules)
    if reward_component_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in reward_component_program.rules)
    return {
        "phase_graph": phase_graph.to_canonical_payload(),
        "rules": rules,
    }


def compute_transition_graph_hash(
    phase_graph: TransitionPhaseGraph,
    action_write_program: Any,
    *,
    affordance_gate_program: Any | None = None,
    interaction_progress_program: Any | None = None,
    terminal_condition_program: Any | None = None,
    threshold_cascade_program: Any | None = None,
    modulation_program: Any | None = None,
    passive_depletion_program: Any | None = None,
    social_residue_program: Any | None = None,
    reward_component_program: Any | None = None,
) -> str:
    """Return the SHA-256 digest of the compiled transition graph and rules."""
    return _hash_payload(
        canonical_transition_graph_schema(
            phase_graph,
            action_write_program,
            affordance_gate_program=affordance_gate_program,
            interaction_progress_program=interaction_progress_program,
            terminal_condition_program=terminal_condition_program,
            threshold_cascade_program=threshold_cascade_program,
            modulation_program=modulation_program,
            passive_depletion_program=passive_depletion_program,
            social_residue_program=social_residue_program,
            reward_component_program=reward_component_program,
        )
    )


def compute_vfs_hash(
    variable_schema_hash: str,
    observation_schema_hash: str,
    action_schema_hash: str,
    transition_graph_hash: str,
) -> str:
    """Return the combined VFS identity hash over state, observation, action, and transition schemas."""
    combined = variable_schema_hash + observation_schema_hash + action_schema_hash + transition_graph_hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _canonical_variable_entry(variable: VariableDef) -> dict[str, Any]:
    return {
        "id": variable.id,
        "type": variable.type,
        "scope": _scope_value(variable.scope),
        "dims": variable.dims,
        "lifetime": variable.lifetime,
        "readable_by": sorted(variable.readable_by),
        "writable_by": sorted(variable.writable_by),
        "range": _normalization_range(variable.normalization),
    }


def _canonical_observation_entry(field: ObservationField) -> dict[str, Any]:
    return {
        "id": field.id,
        "source_variable": field.source_variable,
        "shape": list(field.shape),
        "normalization": _normalization_payload(field.normalization),
        "exposed_to": sorted(field.exposed_to),
        "curriculum_active": field.curriculum_active,
        "dtype": "float32",
        "semantic_type": field.semantic_type,
    }


def _canonical_action_entry(action: Any) -> dict[str, Any]:
    return {
        "id": action.id,
        "name": action.name,
        "type": action.type,
        "source": action.source,
        "enabled": action.enabled,
        "costs": _plain_payload(action.costs),
        "effects": _plain_payload(action.effects),
        "delta": list(action.delta) if action.delta is not None else None,
        "teleport_to": list(action.teleport_to) if action.teleport_to is not None else None,
        "source_affordance": action.source_affordance,
        "reads": sorted(action.reads),
        "writes": [_plain_payload(write) for write in action.writes],
    }


def _canonical_transition_rule(write: Any) -> dict[str, Any]:
    if hasattr(write, "rule_id"):
        entry = {
            "rule_id": write.rule_id,
            "kind": write.kind,
            "variable_id": write.variable_id,
            "expression": write.expression,
            "condition": write.condition,
            "composition": write.composition,
            "phase": write.phase,
            "priority": write.priority,
            "clamp": list(write.clamp) if write.clamp is not None else None,
            "telemetry_label": write.telemetry_label,
        }
        if hasattr(write, "source_variable_id"):
            entry["source_variable_id"] = write.source_variable_id
        if hasattr(write, "target_affordance_id"):
            entry["target_affordance_id"] = write.target_affordance_id
        if hasattr(write, "effect"):
            entry["effect"] = write.effect
        if hasattr(write, "scope"):
            entry["scope"] = write.scope
        if hasattr(write, "target"):
            entry["target"] = write.target
        if hasattr(write, "duration_ticks"):
            entry["duration_ticks"] = write.duration_ticks
        if hasattr(write, "operator"):
            entry["operator"] = write.operator
        if hasattr(write, "threshold"):
            entry["threshold"] = write.threshold
        if hasattr(write, "reads"):
            entry["reads"] = list(write.reads)
        if hasattr(write, "component"):
            entry["component"] = write.component
        if hasattr(write, "source_kind"):
            entry["source_kind"] = write.source_kind
        if hasattr(write, "strategy"):
            entry["strategy"] = write.strategy
        if hasattr(write, "shaping_type"):
            entry["shaping_type"] = write.shaping_type
        if hasattr(write, "parameters"):
            entry["parameters"] = _plain_payload(write.parameters)
        return entry
    return {
        "action_id": write.action_id,
        "action_name": write.action_name,
        "variable_id": write.variable_id,
        "expression": write.expression,
        "condition": write.condition,
        "composition": write.composition,
        "phase": write.phase,
        "priority": write.priority,
        "clamp": list(write.clamp) if write.clamp is not None else None,
        "telemetry_label": write.telemetry_label,
    }


def _scope_value(scope: VariableScope | str) -> str:
    if isinstance(scope, VariableScope):
        return scope.value
    return scope


def _normalization_range(normalization: NormalizationSpec | None) -> list[Any] | None:
    if normalization is None:
        return None
    if normalization.min is None or normalization.max is None:
        return None
    return [normalization.min, normalization.max]


def _normalization_payload(normalization: NormalizationSpec | None) -> dict[str, Any] | None:
    if normalization is None:
        return None
    return normalization.model_dump(mode="json", exclude_none=True)


def _hash_payload(payload: Any) -> str:
    canonical_json = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def _plain_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain_payload(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_plain_payload(item) for item in value]
    return value
