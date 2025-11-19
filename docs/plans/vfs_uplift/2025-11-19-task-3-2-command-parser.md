# Task 3.2: Command Parser & Compiler - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Parse effect commands to AST and compile expressions within commands with type checking.

**Architecture:** CommandNode AST with compilation phase that validates paths, type-checks expressions, and resolves references. Reuses Expression Language parser from Phase 1.

**Tech Stack:** Python 3.11+, dataclasses, Expression Language (Phase 1)

**Dependencies:** Task 1.1-1.4 (Expression Language), Task 3.1 (Effects DTOs)

**References:**
- Effects design: `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- Expression Language: `src/townlet/world/expression/`

---

## Task Breakdown

### Step 1: Write failing test for CommandNode AST

**File:** `tests/test_townlet/unit/effects/test_command_parser.py`

```python
"""Tests for command parser and AST."""
import pytest
from townlet.effects.schema import CommandNode, CommandType


def test_command_node_modify():
    """CommandNode for modify command."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",
        value_expr="target.bar.energy + 0.05"
    )

    assert node.type == CommandType.MODIFY
    assert node.path == "target.bar.energy"
    assert node.value_expr == "target.bar.energy + 0.05"


def test_command_node_spawn_effect():
    """CommandNode for spawn_effect command."""
    node = CommandNode(
        type=CommandType.SPAWN_EFFECT,
        effect_id="poisoned",
        target_expr="self",
        intensity=2.0
    )

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.effect_id == "poisoned"
    assert node.target_expr == "self"
    assert node.intensity == 2.0


def test_command_node_if():
    """CommandNode for if command with nested then/else."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy < 0.2",
        then_commands=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.vfs.is_crisis",
                value_expr="true"
            )
        ],
        else_commands=[
            CommandNode(
                type=CommandType.MODIFY,
                path="target.vfs.is_crisis",
                value_expr="false"
            )
        ]
    )

    assert node.type == CommandType.IF
    assert node.condition_expr == "target.bar.energy < 0.2"
    assert len(node.then_commands) == 1
    assert len(node.else_commands) == 1
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_parser.py::test_command_node_modify -v
```

**Expected:** FAIL - Module 'townlet.effects.schema' not found

---

### Step 2: Implement CommandNode and CommandType

**File:** `src/townlet/effects/schema.py`

```python
"""Effect system schema and AST node types."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any

__all__ = [
    "CommandType",
    "CommandNode",
    "ActiveEffect",
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

    def __post_init__(self):
        """Initialize empty lists for nested commands."""
        if self.then_commands is None:
            self.then_commands = []
        if self.else_commands is None:
            self.else_commands = []
        if self.do_commands is None:
            self.do_commands = []
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_parser.py -k "command_node" -v
```

**Expected:** All 3 command_node tests PASS

**Commit:**
```bash
git add src/townlet/effects/schema.py tests/test_townlet/unit/effects/test_command_parser.py
git commit -m "feat(effects): add CommandNode AST and CommandType enum"
```

---

### Step 3: Write failing test for command parsing

**File:** `tests/test_townlet/unit/effects/test_command_parser.py` (append)

```python
from townlet.effects.parser import CommandParser
from townlet.config.effects_config import CommandConfig


def test_parser_modify_command():
    """Parser converts modify CommandConfig to CommandNode."""
    config = CommandConfig(
        modify="target.bar.energy",
        value="target.bar.energy + 0.05"
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.MODIFY
    assert node.path == "target.bar.energy"
    assert node.value_expr == "target.bar.energy + 0.05"


def test_parser_spawn_effect_command():
    """Parser converts spawn_effect CommandConfig to CommandNode."""
    config = CommandConfig(
        spawn_effect="poisoned",
        target="self",
        intensity=2.0
    )

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.SPAWN_EFFECT
    assert node.effect_id == "poisoned"
    assert node.target_expr == "self"
    assert node.intensity == 2.0


def test_parser_if_command():
    """Parser converts if CommandConfig to CommandNode with nesting."""
    from townlet.config.effects_config import CommandConfig

    config = CommandConfig.model_validate({
        "if": "target.bar.energy < 0.2",
        "then": [
            {"modify": "target.vfs.is_crisis", "value": "true"}
        ],
        "else": [
            {"modify": "target.vfs.is_crisis", "value": "false"}
        ]
    })

    parser = CommandParser()
    node = parser.parse_command(config)

    assert node.type == CommandType.IF
    assert node.condition_expr == "target.bar.energy < 0.2"
    assert len(node.then_commands) == 1
    assert node.then_commands[0].type == CommandType.MODIFY
    assert len(node.else_commands) == 1
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_parser.py::test_parser_modify_command -v
```

**Expected:** FAIL - Module 'townlet.effects.parser' not found

---

### Step 4: Implement CommandParser

**File:** `src/townlet/effects/parser.py`

```python
"""Command parser from config to AST."""
from __future__ import annotations

from townlet.config.effects_config import CommandConfig
from townlet.effects.schema import CommandNode, CommandType

__all__ = ["CommandParser"]


class CommandParser:
    """Parse effect commands from config DTOs to CommandNode AST."""

    def parse_command(self, config: CommandConfig) -> CommandNode:
        """Parse single command config to AST node.

        Args:
            config: Command configuration DTO

        Returns:
            Compiled CommandNode AST
        """
        # Determine command type
        if config.modify is not None:
            return CommandNode(
                type=CommandType.MODIFY,
                path=config.modify,
                value_expr=config.value,
            )

        elif config.spawn_effect is not None:
            return CommandNode(
                type=CommandType.SPAWN_EFFECT,
                effect_id=config.spawn_effect,
                target_expr=config.target or "self",
                intensity=config.intensity or 1.0,
            )

        elif config.spawn_item is not None:
            return CommandNode(
                type=CommandType.SPAWN_ITEM,
                item_type=config.spawn_item,
                position_expr=config.position,
            )

        elif config.if_condition is not None:
            return CommandNode(
                type=CommandType.IF,
                condition_expr=config.if_condition,
                then_commands=[self.parse_command(cmd) for cmd in config.then],
                else_commands=[self.parse_command(cmd) for cmd in config.else_],
            )

        elif config.for_each is not None:
            return CommandNode(
                type=CommandType.FOR_EACH,
                collection_expr=config.for_each,
                iterator_var=config.as_,
                do_commands=[self.parse_command(cmd) for cmd in config.do],
            )

        else:
            raise ValueError("Invalid command config: no command type set")

    def parse_commands(self, configs: list[CommandConfig]) -> list[CommandNode]:
        """Parse list of command configs.

        Args:
            configs: List of command configurations

        Returns:
            List of CommandNode AST nodes
        """
        return [self.parse_command(config) for config in configs]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_parser.py -k "parser" -v
```

**Expected:** All 3 parser tests PASS

**Commit:**
```bash
git add src/townlet/effects/parser.py tests/test_townlet/unit/effects/test_command_parser.py
git commit -m "feat(effects): add CommandParser from config to AST"
```

---

### Step 5: Write failing test for command compilation

**File:** `tests/test_townlet/unit/effects/test_command_compiler.py`

```python
"""Tests for command compiler with expression validation."""
import pytest
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.type_checker import TypeCheckError


def test_compiler_modify_validates_path():
    """Compiler validates modify command path exists."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",
        value_expr="5.0"
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.path == "target.bar.energy"


def test_compiler_modify_rejects_invalid_path():
    """Compiler rejects invalid path in modify command."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.invalid",
        value_expr="5.0"
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="invalid"):
        compiler.compile_command(node)


def test_compiler_modify_validates_expression():
    """Compiler type-checks value expression."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",
        value_expr="target.bar.energy + 0.05"
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.value_expr == "target.bar.energy + 0.05"


def test_compiler_modify_rejects_type_mismatch():
    """Compiler rejects type mismatch in modify command."""
    node = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",  # float
        value_expr="true"  # bool - type mismatch!
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="type"):
        compiler.compile_command(node)


def test_compiler_if_validates_bool_condition():
    """Compiler validates if condition is boolean."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy < 0.2",  # Should be bool
        then_commands=[],
        else_commands=[]
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    compiled = compiler.compile_command(node)
    assert compiled.condition_expr == "target.bar.energy < 0.2"


def test_compiler_if_rejects_non_bool_condition():
    """Compiler rejects non-boolean if condition."""
    node = CommandNode(
        type=CommandType.IF,
        condition_expr="target.bar.energy",  # float, not bool!
        then_commands=[],
        else_commands=[]
    )

    schema = {"target.bar.energy": "float"}
    compiler = CommandCompiler(schema)

    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_command(node)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_compiler.py::test_compiler_modify_validates_path -v
```

**Expected:** FAIL - Module 'townlet.effects.compiler' not found

---

### Step 6: Implement CommandCompiler

**File:** `src/townlet/effects/compiler.py`

```python
"""Command compiler with expression validation."""
from __future__ import annotations

from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression import ExpressionParser
from townlet.world.expression.type_checker import TypeChecker

__all__ = ["CommandCompiler"]


class CommandCompiler:
    """Compile commands with expression type checking."""

    def __init__(self, schema: dict[str, str]):
        """Initialize compiler with type schema.

        Args:
            schema: Type schema for paths (e.g., {"target.bar.energy": "float"})
        """
        self.schema = schema
        self.parser = ExpressionParser()
        self.type_checker = TypeChecker(schema=schema)

    def compile_command(self, node: CommandNode) -> CommandNode:
        """Compile and validate command.

        Args:
            node: CommandNode AST

        Returns:
            Validated CommandNode (same instance, after validation and AST compilation)

        Raises:
            TypeCheckError: If path invalid or type mismatch
        """
        if node.type == CommandType.MODIFY:
            # Validate path exists
            if node.path not in self.schema:
                raise KeyError(f"Path '{node.path}' not found in schema. Available: {list(self.schema.keys())}")

            # Parse and type-check value expression
            value_ast = self.parser.parse(node.value_expr)
            value_type = self.type_checker.check(value_ast)

            # Verify type matches target path
            target_type = self.schema[node.path]
            if value_type != target_type:
                from townlet.world.expression.type_checker import TypeCheckError
                raise TypeCheckError(
                    f"Type mismatch for path '{node.path}': expected {target_type}, got {value_type}"
                )

            # ✅ PERF FIX: Store compiled AST for runtime use
            node.value_ast = value_ast

        elif node.type == CommandType.SPAWN_EFFECT:
            # Validate and compile target expression
            if node.target_expr:
                target_ast = self.parser.parse(node.target_expr)
                self.type_checker.check(target_ast)
                # ✅ Store compiled AST
                node.target_ast = target_ast

        elif node.type == CommandType.IF:
            # Validate condition is boolean
            cond_ast = self.parser.parse(node.condition_expr)
            cond_type = self.type_checker.check(cond_ast)

            if cond_type != "bool":
                from townlet.world.expression.type_checker import TypeCheckError
                raise TypeCheckError(
                    f"If condition must be bool, got {cond_type}"
                )

            # ✅ Store compiled AST
            node.condition_ast = cond_ast

            # Recursively compile nested commands
            for cmd in node.then_commands:
                self.compile_command(cmd)
            for cmd in node.else_commands:
                self.compile_command(cmd)

        elif node.type == CommandType.FOR_EACH:
            # Validate collection expression
            coll_ast = self.parser.parse(node.collection_expr)
            self.type_checker.check(coll_ast)

            # ✅ Store compiled AST
            node.collection_ast = coll_ast

            # Recursively compile nested commands
            for cmd in node.do_commands:
                self.compile_command(cmd)

        return node

    def compile_commands(self, nodes: list[CommandNode]) -> list[CommandNode]:
        """Compile list of commands.

        Args:
            nodes: List of CommandNode AST nodes

        Returns:
            Validated list of CommandNode (same instances, after validation)
        """
        for node in nodes:
            self.compile_command(node)
        return nodes
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_compiler.py -v
```

**Expected:** All 6 compiler tests PASS

**Commit:**
```bash
git add src/townlet/effects/compiler.py tests/test_townlet/unit/effects/test_command_compiler.py
git commit -m "feat(effects): add CommandCompiler with expression type checking"
```

---

### Step 7: Update EffectCatalog to compile commands

**File:** `src/townlet/effects/catalog.py` (modify)

```python
"""Effects catalog compilation and loading."""
from __future__ import annotations

from dataclasses import dataclass

from townlet.config.effects_config import EffectDefinitionConfig, EffectsConfig
from townlet.effects.parser import CommandParser
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode

__all__ = ["CompiledEffect", "EffectCatalog"]


@dataclass
class CompiledEffect:
    """Compiled effect with parsed and validated command pipelines."""

    id: str
    scope: str
    duration: int
    intensity: float
    reapply_policy: str
    observable: bool

    # Compiled command pipelines
    on_spawn: list[CommandNode]
    on_tick: list[CommandNode]
    on_despawn: list[CommandNode]
    on_interrupt: list[CommandNode]


@dataclass
class EffectCatalog:
    """Compiled effect catalog.

    Maps effect IDs to compiled effect definitions.
    """

    effects: dict[str, CompiledEffect]

    @classmethod
    def from_config(cls, config: EffectsConfig, schema: dict[str, str] | None = None) -> EffectCatalog:
        """Compile effects catalog from config.

        Args:
            config: Effects configuration from YAML
            schema: Type schema for command validation (optional for Phase 3.1)

        Returns:
            Compiled catalog with validated command pipelines
        """
        parser = CommandParser()
        compiler = CommandCompiler(schema) if schema else None

        effects = {}
        for defn in config.effect_definitions:
            # Parse commands to AST
            on_spawn = parser.parse_commands(defn.on_spawn)
            on_tick = parser.parse_commands(defn.on_tick)
            on_despawn = parser.parse_commands(defn.on_despawn)
            on_interrupt = parser.parse_commands(defn.on_interrupt)

            # Compile (validate) if schema provided
            if compiler:
                compiler.compile_commands(on_spawn)
                compiler.compile_commands(on_tick)
                compiler.compile_commands(on_despawn)
                compiler.compile_commands(on_interrupt)

            compiled = CompiledEffect(
                id=defn.id,
                scope=defn.scope.value,
                duration=defn.duration,
                intensity=defn.intensity,
                reapply_policy=defn.reapply_policy.value,
                observable=defn.observable,
                on_spawn=on_spawn,
                on_tick=on_tick,
                on_despawn=on_despawn,
                on_interrupt=on_interrupt,
            )

            effects[defn.id] = compiled

        return cls(effects=effects)

    def get(self, effect_id: str) -> CompiledEffect:
        """Get compiled effect by ID.

        Args:
            effect_id: Effect identifier

        Returns:
            Compiled effect

        Raises:
            KeyError: If effect ID not found
        """
        if effect_id not in self.effects:
            raise KeyError(
                f"Effect '{effect_id}' not found in catalog. "
                f"Available effects: {list(self.effects.keys())}"
            )
        return self.effects[effect_id]

    def __contains__(self, effect_id: str) -> bool:
        """Check if effect exists in catalog."""
        return effect_id in self.effects

    def __len__(self) -> int:
        """Number of effects in catalog."""
        return len(self.effects)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_catalog_compilation.py -v
```

**Expected:** All catalog tests still PASS (backward compatible)

**Commit:**
```bash
git add src/townlet/effects/catalog.py
git commit -m "feat(effects): extend EffectCatalog to compile command pipelines"
```

---

### Step 8: Add module exports

**File:** `src/townlet/effects/__init__.py` (update)

```python
"""Effects system for HAMLET World Compiler."""
from __future__ import annotations

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.parser import CommandParser
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType

__all__ = [
    "EffectCatalog",
    "CompiledEffect",
    "CommandParser",
    "CommandCompiler",
    "CommandNode",
    "CommandType",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.effects import CommandParser, CommandCompiler; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/effects/__init__.py
git commit -m "feat(effects): export command parser and compiler in module API"
```

---

### Step 9: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/effects/
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/effects/ tests/test_townlet/unit/effects/
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/effects/
```

**Expected:** No changes needed

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/ -v
```

**Expected:** All ~27 tests PASS (18 from Task 3.1 + 9 new)

**Commit if any changes:**
```bash
git add -u
git commit -m "test(effects): verify all parser and compiler tests pass"
```

---

## Success Criteria

✅ **27+ tests passing** (DTOs + catalog + parser + compiler)
✅ **CommandParser converts config to AST** (all command types)
✅ **CommandCompiler validates expressions** (type checking)
✅ **Path validation** (rejects invalid paths)
✅ **Type mismatch detection** (compile-time errors)
✅ **Nested command compilation** (if/for_each)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Task 3.3: Command Executor**

Implement runtime command execution with path resolution and GPU tensor mutations.

See: `docs/plans/vfs_uplift/2025-11-19-task-3-3-command-executor.md`
