"""Held-out surface-label harnesses for VFS generalisation experiments."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from pyparsing import ParseException

from townlet.world.expression import (
    ASTNode,
    BinaryOp,
    Constant,
    ExpressionParser,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    PathAccess,
    Reduce,
    Switch,
    UnaryOp,
    Variable,
)

__all__ = [
    "VFSGeneralisationPack",
    "VFSGeneralisationReport",
    "VFSGeneralisationSignature",
    "assert_held_out_generalisation_split",
    "build_vfs_generalisation_signature",
    "operator_grammar_signature",
]

_IGNORED_PROFILE_KEYS = frozenset(
    {
        "description",
        "expression_ast",
        "condition_ast",
        "id",
        "label",
        "line",
        "name",
        "rule_id",
        "source_metadata",
        "telemetry_label",
        "uuid",
    }
)
_SURFACE_VALUE_KEYS = frozenset(
    {
        "action_name",
        "affordance",
        "affordance_id",
        "bar",
        "source",
        "source_affordance",
        "source_variable_id",
        "target",
        "target_affordance_id",
        "target_variable_id",
        "variable_id",
    }
)
_DYNAMIC_KEY_FIELDS = frozenset({"costs", "costs_per_tick", "effects", "modifiers"})
_EXPRESSION_FIELDS = frozenset({"condition", "expression", "modify", "value", "when"})
_OPERATOR_FIELD_KEYS = frozenset({"composition", "interaction_type", "kind", "phase"})
_STABLE_IDENTIFIERS = frozenset(
    {
        "affordance_is_open",
        "chosen_interact",
        "done",
        "interaction_progress",
        "same_affordance",
        "time_of_day",
    }
)
_STABLE_PATH_SEGMENTS = frozenset(
    {
        "agent",
        "affordance",
        "available",
        "bar",
        "completed",
        "components",
        "dac",
        "extrinsic",
        "global",
        "intrinsic",
        "modifier",
        "multiplier",
        "reward",
        "self",
        "shaping",
        "target",
        "temporal",
        "total",
        "vfs",
    }
)
_EXPRESSION_PARSER: ExpressionParser | None = None


@dataclass(frozen=True)
class VFSGeneralisationPack:
    """One train or test pack for a held-out VFS generalisation experiment."""

    variables: tuple[Any, ...] = ()
    affordances: tuple[Any, ...] = ()
    rules: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "affordances", tuple(self.affordances))
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True)
class VFSGeneralisationSignature:
    """Surface-insensitive causal and operator signature for a VFS pack."""

    variable_profiles: tuple[str, ...]
    affordance_profiles: tuple[str, ...]
    rule_profiles: tuple[str, ...]
    operator_grammar: tuple[str, ...]


@dataclass(frozen=True)
class VFSGeneralisationReport:
    """Validation proof for a held-out train/test split."""

    held_out_variable_names: tuple[str, ...]
    held_out_affordance_labels: tuple[str, ...]
    shared_operator_grammar: tuple[str, ...]
    variable_profile_count: int
    affordance_profile_count: int
    rule_profile_count: int


class _SurfaceSymbols:
    """Per-profile symbol table that erases labels while preserving equality relationships."""

    def __init__(self) -> None:
        self._by_value: dict[str, str] = {}

    def placeholder(self, value: str) -> str:
        token = self._by_value.get(value)
        if token is None:
            token = f"<surface_{len(self._by_value)}>"
            self._by_value[value] = token
        return token


def assert_held_out_generalisation_split(
    train: VFSGeneralisationPack,
    test: VFSGeneralisationPack,
    *,
    require_variables: bool = True,
    require_affordances: bool = True,
) -> VFSGeneralisationReport:
    """Validate a train/test VFS split with held-out names and shared causal structure."""

    train_variables = _surface_names(train.variables, "variable")
    test_variables = _surface_names(test.variables, "variable")
    train_affordances = _surface_names(train.affordances, "affordance")
    test_affordances = _surface_names(test.affordances, "affordance")

    if require_variables and (not train_variables or not test_variables):
        raise ValueError("held-out variable split requires both train and test variable names")
    if require_affordances and (not train_affordances or not test_affordances):
        raise ValueError("held-out affordance split requires both train and test affordance labels")

    _reject_duplicates(train_variables, "train variable names")
    _reject_duplicates(test_variables, "test variable names")
    _reject_duplicates(train_affordances, "train affordance labels")
    _reject_duplicates(test_affordances, "test affordance labels")

    variable_overlap = sorted(set(train_variables) & set(test_variables))
    if variable_overlap:
        raise ValueError(f"held-out variable names overlap between train and test packs: {variable_overlap}")

    affordance_overlap = sorted(set(train_affordances) & set(test_affordances))
    if affordance_overlap:
        raise ValueError(f"held-out affordance labels overlap between train and test packs: {affordance_overlap}")

    train_signature = build_vfs_generalisation_signature(train)
    test_signature = build_vfs_generalisation_signature(test)

    _assert_same_counter(
        _causal_profiles(train_signature),
        _causal_profiles(test_signature),
        "causal profiles",
    )
    _assert_same_counter(
        train_signature.operator_grammar,
        test_signature.operator_grammar,
        "operator grammar",
    )

    return VFSGeneralisationReport(
        held_out_variable_names=test_variables,
        held_out_affordance_labels=test_affordances,
        shared_operator_grammar=train_signature.operator_grammar,
        variable_profile_count=len(train_signature.variable_profiles),
        affordance_profile_count=len(train_signature.affordance_profiles),
        rule_profile_count=len(train_signature.rule_profiles),
    )


def build_vfs_generalisation_signature(pack: VFSGeneralisationPack) -> VFSGeneralisationSignature:
    """Build a deterministic signature that ignores surface labels but keeps causal fields."""

    variable_profiles = tuple(sorted(_profile_signature(item) for item in pack.variables))
    affordance_profiles = tuple(sorted(_profile_signature(item) for item in pack.affordances))
    rule_profiles = tuple(sorted(_profile_signature(item) for item in pack.rules))
    operator_grammar = tuple(
        sorted(
            grammar
            for item in (*pack.variables, *pack.affordances, *pack.rules)
            for grammar in _operator_grammar_entries(_to_plain_value(item))
        )
    )
    return VFSGeneralisationSignature(
        variable_profiles=variable_profiles,
        affordance_profiles=affordance_profiles,
        rule_profiles=rule_profiles,
        operator_grammar=operator_grammar,
    )


def operator_grammar_signature(expression: str) -> str:
    """Return the surface-insensitive operator grammar for one expression string."""

    return _stable_json(_expression_payload(expression, _SurfaceSymbols(), keep_constants=False))


def _profile_signature(item: Any) -> str:
    symbols = _SurfaceSymbols()
    return _stable_json(_canonical_value(_to_plain_value(item), symbols, parent_key=None, current_key=None))


def _canonical_value(value: Any, symbols: _SurfaceSymbols, *, parent_key: str | None, current_key: str | None) -> Any:
    if isinstance(value, Mapping):
        canonical_items: list[tuple[str, Any]] = []
        for raw_key, raw_child in value.items():
            key = str(raw_key)
            if key in _IGNORED_PROFILE_KEYS:
                continue
            if parent_key in _DYNAMIC_KEY_FIELDS:
                canonical_key = _surface_string(key, symbols)
            else:
                canonical_key = key
            canonical_child = _canonical_value(raw_child, symbols, parent_key=key, current_key=key)
            canonical_items.append((canonical_key, canonical_child))
        return {key: child for key, child in sorted(canonical_items, key=lambda item: item[0])}

    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_canonical_value(child, symbols, parent_key=current_key, current_key=None) for child in value]

    if isinstance(value, str):
        if current_key in _EXPRESSION_FIELDS:
            return _expression_payload(value, symbols, keep_constants=True)
        if current_key in _SURFACE_VALUE_KEYS:
            return _surface_string(value, symbols)
        return value

    return value


def _operator_grammar_entries(value: Any) -> tuple[str, ...]:
    entries: list[str] = []

    def visit(node: Any, *, current_key: str | None) -> None:
        if isinstance(node, Mapping):
            for key_raw, child in node.items():
                key = str(key_raw)
                if key in _IGNORED_PROFILE_KEYS:
                    continue
                if key in _EXPRESSION_FIELDS and isinstance(child, str):
                    entries.append(_stable_json(("expression", key, _expression_payload(child, _SurfaceSymbols(), keep_constants=False))))
                    continue
                if key in _OPERATOR_FIELD_KEYS and isinstance(child, str):
                    entries.append(_stable_json(("field", key, child)))
                visit(child, current_key=key)
            return

        if isinstance(node, Sequence) and not isinstance(node, str | bytes | bytearray):
            for child in node:
                visit(child, current_key=current_key)

    visit(value, current_key=None)
    return tuple(entries)


def _expression_payload(expression: str, symbols: _SurfaceSymbols, *, keep_constants: bool) -> Any:
    try:
        ast = _expression_parser().parse(expression)
    except ParseException as exc:
        raise ValueError(f"VFS generalisation expression could not be parsed: {expression!r}") from exc
    return _ast_payload(ast, symbols, keep_constants=keep_constants)


def _expression_parser() -> ExpressionParser:
    global _EXPRESSION_PARSER
    if _EXPRESSION_PARSER is None:
        _EXPRESSION_PARSER = ExpressionParser()
    return _EXPRESSION_PARSER


def _ast_payload(node: ASTNode, symbols: _SurfaceSymbols, *, keep_constants: bool) -> Any:
    if isinstance(node, Constant):
        if keep_constants:
            return ("const", type(node.value).__name__, node.value)
        return ("const", type(node.value).__name__)
    if isinstance(node, Variable):
        return ("var", _identifier_payload(node.name, symbols))
    if isinstance(node, PathAccess):
        return ("path", tuple(_path_segment_payload(segment, symbols) for segment in node.segments))
    if isinstance(node, BinaryOp):
        return (
            "binary",
            node.op.value,
            _ast_payload(node.left, symbols, keep_constants=keep_constants),
            _ast_payload(node.right, symbols, keep_constants=keep_constants),
        )
    if isinstance(node, UnaryOp):
        return ("unary", node.op.value, _ast_payload(node.operand, symbols, keep_constants=keep_constants))
    if isinstance(node, FunctionCall):
        return (
            "call",
            node.function_name,
            tuple(_ast_payload(arg, symbols, keep_constants=keep_constants) for arg in node.arguments),
        )
    if isinstance(node, IfThenElse):
        return (
            "if",
            _ast_payload(node.condition, symbols, keep_constants=keep_constants),
            _ast_payload(node.true_branch, symbols, keep_constants=keep_constants),
            _ast_payload(node.false_branch, symbols, keep_constants=keep_constants),
        )
    if isinstance(node, IndexAccess):
        return (
            "index",
            _ast_payload(node.base, symbols, keep_constants=keep_constants),
            _ast_payload(node.index, symbols, keep_constants=keep_constants),
        )
    if isinstance(node, Switch):
        return (
            "switch",
            _ast_payload(node.switch_expr, symbols, keep_constants=keep_constants),
            tuple(
                (
                    _ast_payload(case_expr, symbols, keep_constants=keep_constants),
                    tuple(_to_plain_value(statement) for statement in body),
                )
                for case_expr, body in node.cases
            ),
            None if node.default is None else tuple(_to_plain_value(statement) for statement in node.default),
        )
    if isinstance(node, Reduce):
        return (
            "reduce",
            _ast_payload(node.collection, symbols, keep_constants=keep_constants),
            symbols.placeholder(node.iterator),
            _ast_payload(node.init, symbols, keep_constants=keep_constants),
            _ast_payload(node.body, symbols, keep_constants=keep_constants),
            None if node.target is None else _surface_string(node.target, symbols),
        )
    raise TypeError(f"Unsupported expression AST node for VFS generalisation signature: {type(node).__name__}")


def _identifier_payload(identifier: str, symbols: _SurfaceSymbols) -> str:
    if identifier in _STABLE_IDENTIFIERS:
        return identifier
    return symbols.placeholder(identifier)


def _path_segment_payload(segment: str, symbols: _SurfaceSymbols) -> str:
    if segment in _STABLE_PATH_SEGMENTS:
        return segment
    return symbols.placeholder(segment)


def _surface_string(value: str, symbols: _SurfaceSymbols) -> str:
    if "." not in value:
        return _identifier_payload(value, symbols)
    return ".".join(_path_segment_payload(segment, symbols) for segment in value.split("."))


def _surface_names(items: Sequence[Any], item_kind: str) -> tuple[str, ...]:
    names: list[str] = []
    for item in items:
        payload = _to_plain_value(item)
        if not isinstance(payload, Mapping):
            raise TypeError(f"VFS generalisation {item_kind} entries must be mappings or DTO/dataclass objects")
        raw_name = payload.get("name") or payload.get("id") or payload.get("label")
        if raw_name is None:
            raise ValueError(f"VFS generalisation {item_kind} entry must expose name, id, or label")
        name = str(raw_name).strip()
        if not name:
            raise ValueError(f"VFS generalisation {item_kind} entry has an empty surface label")
        names.append(name)
    return tuple(names)


def _reject_duplicates(values: tuple[str, ...], label: str) -> None:
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise ValueError(f"{label} contain duplicates: {duplicates}")


def _causal_profiles(signature: VFSGeneralisationSignature) -> tuple[str, ...]:
    return (
        *(f"variable:{profile}" for profile in signature.variable_profiles),
        *(f"affordance:{profile}" for profile in signature.affordance_profiles),
        *(f"rule:{profile}" for profile in signature.rule_profiles),
    )


def _assert_same_counter(train_values: tuple[str, ...], test_values: tuple[str, ...], label: str) -> None:
    train_counter = Counter(train_values)
    test_counter = Counter(test_values)
    if train_counter == test_counter:
        return
    missing = _counter_sample(train_counter - test_counter)
    unexpected = _counter_sample(test_counter - train_counter)
    raise ValueError(f"train/test {label} differ: missing_in_test={missing}; unexpected_in_test={unexpected}")


def _counter_sample(counter: Counter[str]) -> list[str]:
    return list(counter.elements())[:3]


def _to_plain_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="python", exclude_none=True)
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)  # type: ignore[arg-type]
    if hasattr(value, "__dict__"):
        return {key: child for key, child in vars(value).items() if not key.startswith("_")}
    return value


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
