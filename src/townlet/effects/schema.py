"""Effect system schema and AST node types."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any

from townlet.config.effects_config import EffectScope

__all__ = [
    "CommandType",
    "CommandNode",
    "EffectDefinition",
    "EffectScope",
]


class CommandType(enum.Enum):
    """Type of command in effect pipeline."""

    MODIFY = "modify"
    SPAWN_EFFECT = "spawn_effect"
    SPAWN_ITEM = "spawn_item"
    SAMPLE = "sample"
    TRIGGER_CASCADE = "trigger_cascade"
    IF = "if"
    FOR_EACH = "for_each"
    SWITCH = "switch"
    REDUCE = "reduce"
    PARALLEL = "parallel"
    DELAY = "delay"


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
    target: str | int | None = None  # Simple target ("self", "target", or explicit index)
    target_expr: str | None = None  # Expression string (for complex expressions)
    target_ast: Any | None = None  # ✅ Pre-compiled AST
    duration: int | None = None  # Duration override (if not using effect default)
    intensity: float | None = None  # Intensity multiplier

    # spawn_item command fields
    item_type: str | None = None  # Item type ID (canonical)
    position: Any | None = None  # Simple position ("self", "target", or coordinates)
    position_expr: str | None = None  # Expression string (for complex expressions)
    position_ast: Any | None = None  # ✅ Pre-compiled AST
    quantity: int | None = None  # Number of items to spawn (NEW)
    initial_state: dict | None = None  # Initial VFS state (NEW)

    # sample command fields
    sample_distribution: str | None = None
    sample_params: dict[str, Any] | None = None  # Raw params (may contain expr strings)
    sample_param_asts: dict[str, Any] | None = None  # Pre-compiled param ASTs
    sample_store_path: str | None = None

    # if command fields
    condition_expr: str | None = None  # Boolean expression string
    condition_ast: Any | None = None  # ✅ Pre-compiled AST
    then_commands: list[CommandNode] | None = None
    else_commands: list[CommandNode] | None = None

    # for_each command fields
    collection: str | None = None  # Simple collection type ("nearby_agents", "all_agents")
    collection_expr: str | None = None  # Expression string (for complex expressions)
    collection_ast: Any | None = None  # ✅ Pre-compiled AST
    iterator: str | None = None  # Iterator variable name
    body: list[CommandNode] | None = None  # Body commands
    radius: float | None = None  # Radius for spatial collections (NEW)

    # switch command fields
    switch_expr: str | None = None
    switch_ast: Any | None = None
    cases: list[tuple[str, list[CommandNode]]] | None = None
    case_asts: list[tuple[Any, list[CommandNode]]] | None = None
    default_commands: list[CommandNode] | None = None

    # reduce command fields
    reduce_expr: str | None = None  # collection expression
    reduce_iterator: str | None = None
    reduce_init_expr: str | None = None
    reduce_init_ast: Any | None = None
    reduce_body_expr: str | None = None  # accumulator update expr (uses acc + iterator)
    reduce_body_ast: Any | None = None
    reduce_target: str | None = None

    # parallel command fields
    parallel_commands: list[CommandNode] | None = None

    # delay command fields
    delay_ticks_expr: str | None = None
    delay_ticks_ast: Any | None = None
    delay_commands: list[CommandNode] | None = None

    # trigger_cascade command fields
    cascade_id: str | None = None
    cascade_strength: float | None = None

    def __post_init__(self) -> None:
        """Initialize empty lists for nested commands."""
        if self.then_commands is None:
            self.then_commands = []
        if self.else_commands is None:
            self.else_commands = []
        if self.body is None:
            self.body = []
        if self.cases is None:
            self.cases = []
        if self.default_commands is None:
            self.default_commands = []
        if self.parallel_commands is None:
            self.parallel_commands = []


@dataclass
class EffectDefinition:
    """Lightweight effect definition for tests/benchmarks.

    Mirrors the compiled effect fields accessed by EffectManager.
    """

    id: str
    scope: EffectScope
    duration: int
    reapply_policy: str
    observable: bool = True
    intensity: float = 1.0
    on_spawn: list[CommandNode] | None = None
    on_tick: list[CommandNode] | None = None
    on_despawn: list[CommandNode] | None = None
    on_interrupt: list[CommandNode] | None = None

    def __post_init__(self) -> None:
        self.on_spawn = self.on_spawn or []
        self.on_tick = self.on_tick or []
        self.on_despawn = self.on_despawn or []
        self.on_interrupt = self.on_interrupt or []
