"""Effect system schema and AST node types."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CommandType",
    "CommandNode",
]


class CommandType(enum.Enum):
    """Type of command in effect pipeline."""

    MODIFY = "modify"
    SPAWN_EFFECT = "spawn_effect"
    SPAWN_ITEM = "spawn_item"
    IF = "if"
    FOR_EACH = "for_each"


@dataclass
class CommandNode:
    """AST node for a single command.

    Compiled representation with pre-compiled expression ASTs for runtime performance.
    """

    type: CommandType

    # modify command fields
    path: str | None = None  # Target path (e.g., "target.bar.energy")
    value_expr: str | None = None  # Expression string (for debugging/serialization)
    value_ast: Any | None = None  # ✅ Pre-compiled AST (from Phase 1 expression language)

    # spawn_effect command fields
    effect_id: str | None = None  # Effect ID to spawn
    target_expr: str | None = "self"  # Expression string
    target_ast: Any | None = None  # ✅ Pre-compiled AST
    intensity: float | None = 1.0  # Intensity multiplier

    # spawn_item command fields
    item_type: str | None = None  # Item type ID
    position_expr: str | None = None  # Expression string
    position_ast: Any | None = None  # ✅ Pre-compiled AST

    # if command fields
    condition_expr: str | None = None  # Boolean expression string
    condition_ast: Any | None = None  # ✅ Pre-compiled AST
    then_commands: list[CommandNode] | None = None
    else_commands: list[CommandNode] | None = None

    # for_each command fields
    collection_expr: str | None = None  # Expression string
    collection_ast: Any | None = None  # ✅ Pre-compiled AST
    iterator_var: str | None = None  # Variable name for iteration
    do_commands: list[CommandNode] | None = None

    def __post_init__(self) -> None:
        """Initialize empty lists for nested commands."""
        if self.then_commands is None:
            self.then_commands = []
        if self.else_commands is None:
            self.else_commands = []
        if self.do_commands is None:
            self.do_commands = []
