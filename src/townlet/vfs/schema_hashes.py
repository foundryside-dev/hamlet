"""Canonical VFS schema hash helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any

from townlet.config.variables_config import VariablesConfig
from townlet.vfs.profiles import CompiledGlobalProfile, CompiledItemProfile
from townlet.vfs.schema import NormalizationSpec, VariableDef, VariableScope
from townlet.vfs.transition_graph import TransitionPhaseGraph
from townlet.world.expression import ExpressionParser
from townlet.world.expression.ast_nodes import (
    ASTNode,
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    PathAccess,
    Reduce,
    Switch,
    UnaryOp,
    Variable,
)

if TYPE_CHECKING:
    # `townlet.config.actions_config` imports `townlet.vfs.schema`, whose package imports this
    # module; the type is annotation-only here, so the import stays out of the runtime cycle.
    from townlet.config.actions_config import ActionsConfig

__all__ = [
    "canonical_action_schema",
    "canonical_actions_declaration",
    "canonical_expression_ast",
    "canonical_expression_schema",
    "canonical_transition_graph_schema",
    "canonical_variable_schema",
    "canonical_variables_declaration",
    "compute_action_schema_hash",
    "compute_actions_hash",
    "compute_expression_schema_hash",
    "compute_transition_graph_hash",
    "compute_variable_schema_hash",
    "compute_variables_hash",
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
                        "semantic_type": variable.semantic_type,
                        "initial_value": _plain_payload(variable.initial_value),
                        "readable_by": sorted(variable.readable_by),
                        "writable_by": sorted(variable.writable_by),
                        "exposed_to": sorted(variable.exposed_to),
                        "normalization": _normalization_payload(variable.normalization),
                    },
                }
            )
    return sorted(entries, key=lambda entry: entry["identity"])


def compute_variable_schema_hash(variables: Iterable[VariableDef], item_profiles: Mapping[str, CompiledItemProfile]) -> str:
    """Hash the complete registry and qualified item state identity."""
    return _hash_payload(canonical_variable_schema(variables, item_profiles))


def canonical_expression_schema(
    *,
    global_profile: CompiledGlobalProfile | None,
    agent_profile: CompiledGlobalProfile | None,
) -> list[dict[str, Any]]:
    """The compiled global and agent expression programs as identity.

    Expression text lives only on the compiled profiles — never on ``VariableDef``, by
    design — so this is the one place a rewarded ``x * 1`` becoming ``x * 3`` can enter a
    checkpoint-gated hash. Each profile variable contributes its expression as a
    canonical AST (source positions stripped: two spellings that parse identically hash
    identically), its declared and inferred types, lifetime, ``semantic_type`` and its
    in-profile dependency set. Variables without an expression contribute ``None``, so an
    expression appearing or vanishing is a move the registry entry alone cannot see.

    The dependency SET is the identity, not the variable's position in
    ``profile.variables``: that list is one linear extension of the dependency DAG, and
    two declaration orders of independent variables yield different extensions of the
    same program. Any linear extension evaluates to the same values.
    """
    entries: list[dict[str, Any]] = []
    for scope, profile in (("global", global_profile), ("agent", agent_profile)):
        if profile is None:
            continue
        names = [variable.name for variable in profile.variables]
        if len(names) != len(set(names)):
            raise ValueError(f"Compiled {scope} profile has duplicate variable identity")
        for variable in profile.variables:
            if variable.name not in profile.dependencies:
                raise ValueError(f"Compiled {scope} profile variable {variable.name!r} has no dependency record")
            entries.append(
                {
                    "identity": ("expression", scope, variable.name),
                    "definition": {
                        "id": variable.name,
                        "type": variable.type,
                        "result_type": variable.result_type,
                        "lifetime": variable.lifetime,
                        "semantic_type": variable.semantic_type,
                        "expression": None if variable.ast is None else canonical_expression_ast(variable.ast),
                        "dependencies": sorted(profile.dependencies[variable.name]),
                    },
                }
            )
    return sorted(entries, key=lambda entry: entry["identity"])


def compute_expression_schema_hash(
    *,
    global_profile: CompiledGlobalProfile | None,
    agent_profile: CompiledGlobalProfile | None,
) -> str:
    """Return the SHA-256 digest of the canonical global/agent expression programs."""
    return _hash_payload(canonical_expression_schema(global_profile=global_profile, agent_profile=agent_profile))


def canonical_expression_ast(node: ASTNode) -> dict[str, Any]:
    """Project a parsed expression onto its semantic structure only.

    ``line``, ``column`` and ``type_annotation`` are where the author wrote the node and
    what the checker later inferred, not what it computes; both are dropped. Operators
    hash by their surface symbol, constants by value and Python type (``1``, ``1.0`` and
    ``True`` are three different constants).
    """
    if isinstance(node, Constant):
        return {"node": "constant", "value": node.value, "value_type": type(node.value).__name__}
    if isinstance(node, Variable):
        return {"node": "variable", "name": node.name}
    if isinstance(node, PathAccess):
        return {"node": "path", "segments": list(node.segments)}
    if isinstance(node, BinaryOp):
        return {
            "node": "binary",
            "op": node.op.value,
            "left": canonical_expression_ast(node.left),
            "right": canonical_expression_ast(node.right),
        }
    if isinstance(node, UnaryOp):
        return {"node": "unary", "op": node.op.value, "operand": canonical_expression_ast(node.operand)}
    if isinstance(node, FunctionCall):
        return {
            "node": "call",
            "function": node.function_name,
            "arguments": [canonical_expression_ast(argument) for argument in node.arguments],
        }
    if isinstance(node, IfThenElse):
        return {
            "node": "if",
            "condition": canonical_expression_ast(node.condition),
            "then": canonical_expression_ast(node.true_branch),
            "else": canonical_expression_ast(node.false_branch),
        }
    if isinstance(node, IndexAccess):
        return {"node": "index", "base": canonical_expression_ast(node.base), "index": canonical_expression_ast(node.index)}
    if isinstance(node, Switch):
        return {
            "node": "switch",
            "subject": canonical_expression_ast(node.switch_expr),
            "cases": [[canonical_expression_ast(when), _canonical_body(body)] for when, body in node.cases],
            "default": None if node.default is None else _canonical_body(node.default),
        }
    if isinstance(node, Reduce):
        return {
            "node": "reduce",
            "collection": canonical_expression_ast(node.collection),
            "iterator": node.iterator,
            "init": canonical_expression_ast(node.init),
            "body": canonical_expression_ast(node.body),
            "target": node.target,
        }
    raise TypeError(f"Expression node {type(node).__name__} has no canonical hash form")


def _canonical_body(body: list[Any]) -> list[Any]:
    return [canonical_expression_ast(item) if isinstance(item, ASTNode) else _plain_payload(item) for item in body]


def canonical_variables_declaration(config: VariablesConfig) -> dict[str, Any]:
    """The discovered ``variables`` declaration as content, independent of transport.

    ``variables`` is a collection family: discovery merges its fragments in sorted
    pack-relative path order, so moving one declaration between files reorders
    ``declarations`` while changing no fact about any variable. Order is therefore not
    identity here. Declarations sort by the roster identity ``validate_roster`` refuses
    duplicates on, item profile names sort, the role lists (sets spelled as lists) sort,
    and an expression enters as its canonical AST, so two spellings that parse identically
    are one declaration. Where declaration order IS semantic — variable-element slot
    binding for a flat reader — ``layout_hash`` carries it. Everything else the author
    wrote, ``description`` included, is content, exactly as the sibling pack hashes treat it.
    """
    parser = ExpressionParser()
    payload: dict[str, Any] = config.model_dump(mode="json")
    declarations: list[dict[str, Any]] = []
    for declaration in payload["declarations"]:
        entry = dict(declaration)
        for role_field in ("readable_by", "writable_by", "exposed_to"):
            entry[role_field] = sorted(entry[role_field])
        if entry["expression"] is not None:
            entry["expression"] = canonical_expression_ast(parser.parse(entry["expression"]))
        declarations.append(entry)
    payload["declarations"] = sorted(declarations, key=lambda entry: (entry["profile"] or "", entry["id"]))
    payload["item_profiles"] = sorted(payload["item_profiles"])
    return payload


def compute_variables_hash(config: VariablesConfig) -> str:
    """Return the SHA-256 digest of the canonical ``variables`` declaration."""
    return _hash_payload(canonical_variables_declaration(config))


def canonical_actions_declaration(config: ActionsConfig) -> dict[str, Any]:
    """The ``actions`` declaration as content: write expressions and conditions as canonical ASTs.

    A pydantic dump hashes the expression TEXT, so ``'1.0 + 1.0'`` and ``'1.0+1.0'`` were
    two actions and refused resume. Every other field is content as dumped.
    """
    payload: dict[str, Any] = config.model_dump(mode="json")
    for action in payload["actions"]["custom_actions"]:
        action["writes"] = [_canonical_write(write) for write in action["writes"]]
    return payload


def compute_actions_hash(config: ActionsConfig) -> str:
    """Return the SHA-256 digest of the canonical ``actions`` declaration."""
    return _hash_payload(canonical_actions_declaration(config))


_EXPRESSION_PARSER = ExpressionParser()


def _canonical_expression_text(text: str | None) -> dict[str, Any] | None:
    """Expression source text as its canonical AST (``None`` stays ``None``)."""
    if text is None:
        return None
    return canonical_expression_ast(_EXPRESSION_PARSER.parse(text))


def _canonical_write(write: Mapping[str, Any]) -> dict[str, Any]:
    """One action write with its ``expression`` and ``condition`` text canonicalized."""
    entry: dict[str, Any] = _plain_payload(write)
    entry["expression"] = _canonical_expression_text(entry["expression"])
    entry["condition"] = _canonical_expression_text(entry["condition"])
    return entry


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
    expression_schema_hash: str,
) -> str:
    """Return the combined VFS identity hash over state, observation, action, transition and expression schemas.

    Slots 1–4 are the composition the unit-3 token cut left in place (slot 2 receives
    the TokenSpec-derived ``observation_schema_hash``; DIV-008). Slot 5 is the compiled
    global/agent expression programs (``compute_expression_schema_hash``): an expression
    is per-tick passive dynamics, the same kind of fact as a transition rule in slot 4,
    and before it entered here a rewarded expression could change under a checkpoint
    with no hash moving (VFS round-2 F5).
    """
    combined = variable_schema_hash + observation_schema_hash + action_schema_hash + transition_graph_hash + expression_schema_hash
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def _canonical_variable_entry(variable: VariableDef) -> dict[str, Any]:
    """Every declared fact that fixes a variable's storage, reset and exposure identity.

    ``shape`` fixes the tensor extent; ``initial_value`` (the DTO's ``default``),
    ``initial_value_mode`` and ``initial_value_params`` fix what a reset restores or
    redraws; ``semantic_type``, ``exposed_to`` and the complete ``normalization`` fix how
    the variable is grouped and read. Two declarations differing in any of them are
    different state. The expression, if any, is identity too, but it lives on the
    compiled profile, not here — see ``canonical_expression_schema``.
    """
    return {
        "id": variable.id,
        "type": variable.type,
        "scope": _scope_value(variable.scope),
        "dims": variable.dims,
        "shape": list(variable.shape) if variable.shape is not None else None,
        "lifetime": variable.lifetime,
        "semantic_type": variable.semantic_type,
        "initial_value": _plain_payload(variable.default),
        "initial_value_mode": variable.initial_value_mode,
        "initial_value_params": _plain_payload(variable.initial_value_params),
        "readable_by": sorted(variable.readable_by),
        "writable_by": sorted(variable.writable_by),
        "exposed_to": sorted(variable.exposed_to),
        "normalization": _normalization_payload(variable.normalization),
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
        "writes": [_canonical_write(write) for write in action.writes],
    }


_RULE_EXPRESSION_FIELDS = frozenset({"expression", "condition"})


def _canonical_transition_rule(rule: Any) -> dict[str, Any]:
    """Project a compiled VTC rule onto every declared field, expressions as canonical ASTs.

    Every rule family is a frozen dataclass; its fields are the identity. The
    ``expression`` and ``condition`` source text enters as its canonical AST (so a
    respelling that parses identically is the same rule); the parsed ``*_ast`` fields
    are that same parse and are skipped, as is a field marked ``derived`` (computed from
    declarations that are identity elsewhere).
    """
    if not dataclasses.is_dataclass(rule) or isinstance(rule, type):
        raise TypeError(f"Transition rule {rule!r} is not a compiled VTC rule dataclass")
    payload: dict[str, Any] = {}
    for field in dataclasses.fields(rule):
        if field.name.endswith("_ast") or field.metadata.get("derived"):
            continue
        value = getattr(rule, field.name)
        payload[field.name] = _canonical_expression_text(value) if field.name in _RULE_EXPRESSION_FIELDS else _plain_payload(value)
    return payload


def _scope_value(scope: VariableScope | str) -> str:
    if isinstance(scope, VariableScope):
        return scope.value
    return scope


def _normalization_payload(normalization: NormalizationSpec | None) -> dict[str, Any] | None:
    """The complete declared normalization: kind and every parameter, not just the range."""
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
