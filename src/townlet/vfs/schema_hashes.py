"""Canonical VFS schema hash helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any

from townlet.vfs.profiles import CompiledItemProfile
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope
from townlet.vfs.transition_graph import TransitionPhaseGraph

__all__ = [
    "canonical_action_schema",
    "canonical_transition_graph_schema",
    "canonical_variable_schema",
    "compute_action_schema_hash",
    "compute_transition_graph_hash",
    "compute_variable_schema_hash",
    "compute_vfs_hash",
]


def canonical_variable_schema(variables: Iterable[VariableDef], item_profiles: Mapping[str, CompiledItemProfile]) -> list[dict[str, Any]]:
    """Bind ordinary and qualified item declarations to one collision-free identity.

    Permissions contribute even for hidden item state. Namespace tags keep a legal
    registry id such as ``food.energy`` distinct from item profile ``food``'s
    ``energy``. Supplying the complete item roster is required, including empty {}.
    """
    entries = [{"identity": ("registry", variable.id), "definition": _canonical_variable_entry(variable)} for variable in variables]
    for name, profile in item_profiles.items():
        if name != profile.profile_name:
            raise ValueError(f"Item profile mapping key {name!r} disagrees with profile identity {profile.profile_name!r}")
        names = [variable.name for variable in profile.variables]
        if len(names) != len(set(names)):
            raise ValueError(f"Item profile {name!r} has duplicate variable identity")
        for variable in profile.variables:
            entries.append(
                {
                    "identity": ("item", name, variable.name),
                    "definition": {
                        "id": variable.name,
                        "type": variable.type,
                        "scope": "item",
                        "dims": variable.dims,
                        "lifetime": variable.lifetime,
                        "initial_value": _plain_payload(variable.initial_value),
                        "readable_by": sorted(variable.readable_by),
                        "writable_by": sorted(variable.writable_by),
                        "range": _normalization_range(variable.normalization),
                    },
                }
            )
    return sorted(entries, key=lambda entry: entry["identity"])


def compute_variable_schema_hash(variables: Iterable[VariableDef], item_profiles: Mapping[str, CompiledItemProfile]) -> str:
    """Hash the complete registry and qualified item state identity."""
    return _hash_payload(canonical_variable_schema(variables, item_profiles))


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
    bounds_clamp_program: Any | None = None,
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
    if bounds_clamp_program is not None:
        rules.extend(_canonical_transition_rule(rule) for rule in bounds_clamp_program.rules)
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
    bounds_clamp_program: Any | None = None,
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
            bounds_clamp_program=bounds_clamp_program,
        )
    )


def compute_vfs_hash(
    variable_schema_hash: str,
    observation_schema_hash: str,
    action_schema_hash: str,
    transition_graph_hash: str,
) -> str:
    """Return the combined VFS identity hash over state, observation, action, and transition schemas.

    The four-term composition is structurally FROZEN across the unit-3 token cut: slot 2
    simply receives the TokenSpec-derived ``observation_schema_hash``
    (townlet.universe.token_hashes), which is why ``vfs_hash`` moved on every pack at the
    cut — DIV-008's registered movement, never a restructuring of this function.
    """
    combined = variable_schema_hash + observation_schema_hash + action_schema_hash + transition_graph_hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _canonical_variable_entry(variable: VariableDef) -> dict[str, Any]:
    """Every declared fact that fixes a variable's storage and reset identity.

    ``shape`` fixes the tensor extent; ``initial_value`` (the DTO's ``default``),
    ``initial_value_mode`` and ``initial_value_params`` fix what a reset restores or
    redraws. Two declarations differing in any of them are different state.
    """
    return {
        "id": variable.id,
        "type": variable.type,
        "scope": _scope_value(variable.scope),
        "dims": variable.dims,
        "shape": list(variable.shape) if variable.shape is not None else None,
        "lifetime": variable.lifetime,
        "initial_value": _plain_payload(variable.default),
        "initial_value_mode": variable.initial_value_mode,
        "initial_value_params": _plain_payload(variable.initial_value_params),
        "readable_by": sorted(variable.readable_by),
        "writable_by": sorted(variable.writable_by),
        "range": _normalization_range(variable.normalization),
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


def _canonical_transition_rule(rule: Any) -> dict[str, Any]:
    """Project a compiled VTC rule onto every declared field except parsed ASTs.

    Every rule family is a frozen dataclass; its fields are the identity. Parsed
    ASTs are derived from the hashed source text and are not serialisable.
    """
    if not dataclasses.is_dataclass(rule) or isinstance(rule, type):
        raise TypeError(f"Transition rule {rule!r} is not a compiled VTC rule dataclass")
    return {field.name: _plain_payload(getattr(rule, field.name)) for field in dataclasses.fields(rule) if not field.name.endswith("_ast")}


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
