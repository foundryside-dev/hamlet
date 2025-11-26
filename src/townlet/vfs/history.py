"""History requirement analysis for VFS expressions."""

from __future__ import annotations

from townlet.vfs.profiles import CompiledGlobalProfile
from townlet.world.expression import ASTVisitor, Constant, FunctionCall, PathAccess, Variable

TEMPORAL_FUNCTIONS = {"lag", "delta", "moving_average", "ema", "rate_of_change", "rising_edge", "falling_edge"}


def _key_from_node(node) -> str:
    if isinstance(node, PathAccess):
        return ".".join(node.segments)
    if isinstance(node, Variable):
        return f"vfs.{node.name}"
    raise ValueError("Temporal operators require first argument to be a variable or path")


def _extract_int(node, name: str) -> int:
    if not isinstance(node, Constant) or not isinstance(node.value, int):
        raise ValueError(f"Function '{name}' requires integer literal argument for window/offset")
    return int(node.value)


class HistoryCollector(ASTVisitor):
    """Collects history window requirements from an expression AST."""

    def __init__(self) -> None:
        self.requirements: dict[str, int] = {}

    def visit_constant(self, node: Constant):  # noqa: D401
        return None

    def visit_variable(self, node: Variable):  # noqa: D401
        return None

    def visit_path_access(self, node: PathAccess):  # noqa: D401
        return None

    def visit_binary_op(self, node):  # noqa: D401
        node.left.accept(self)
        node.right.accept(self)

    def visit_unary_op(self, node):  # noqa: D401
        node.operand.accept(self)

    def visit_if_then_else(self, node):  # noqa: D401
        node.condition.accept(self)
        node.true_branch.accept(self)
        node.false_branch.accept(self)

    def visit_index_access(self, node):  # noqa: D401
        node.base.accept(self)
        node.index.accept(self)

    def visit_switch(self, node):  # pragma: no cover - not used here
        for case in getattr(node, "cases", []):
            case.accept(self)
        getattr(node, "default", None) and node.default.accept(self)

    def visit_reduce(self, node):  # pragma: no cover - not used here
        node.source.accept(self)
        node.initial.accept(self)

    def visit_function_call(self, node: FunctionCall):  # noqa: D401
        func = node.function_name
        for arg in node.arguments:
            arg.accept(self)

        if func not in TEMPORAL_FUNCTIONS:
            return

        key = _key_from_node(node.arguments[0])
        required_window = 1
        if func == "lag":
            required_window = _extract_int(node.arguments[1], func) + 1
        elif func == "moving_average":
            required_window = _extract_int(node.arguments[1], func)
        elif func == "delta":
            required_window = 2
        elif func == "rate_of_change":
            required_window = _extract_int(node.arguments[1], func) + 1

        # Minimum 1
        required_window = max(required_window, 1)
        self.requirements[key] = max(self.requirements.get(key, 0), required_window)


def collect_history_requirements(profile: CompiledGlobalProfile | None) -> dict[str, int]:
    """Collect per-key window requirements from compiled global profile.

    Returns a mapping of key -> max window required for temporal operators.
    """

    if profile is None:
        return {}

    requirements: dict[str, int] = {}

    for var in profile.variables:
        if var.ast is None:
            continue
        collector = HistoryCollector()
        var.ast.accept(collector)
        for key, window in collector.requirements.items():
            requirements[key] = max(requirements.get(key, 0), window)

    return requirements
