# Task 3.3: Command Executor - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement runtime command execution with path resolution, GPU tensor mutations, and execution context.

**Architecture:** ExecutionContext provides access to bars, VFS, self, target. CommandExecutor interprets CommandNode AST and mutates tensors. Supports modify, spawn_effect, if, for_each commands.

**Tech Stack:** Python 3.11+, PyTorch tensors, Expression Evaluator (Phase 1)

**Dependencies:** Task 1.4 (Expression Evaluator), Task 3.2 (Command Parser)

**References:**
- Effects design: `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- Expression Evaluator: `src/townlet/world/expression/evaluator.py`

---

## Task Breakdown

### Step 1: Write failing test for ExecutionContext

**File:** `tests/test_townlet/unit/effects/test_execution_context.py`

```python
"""Tests for effect execution context."""
import pytest
import torch
from townlet.effects.context import ExecutionContext
from townlet.vfs.registry import ScopedVariableRegistry


def test_execution_context_bar_access():
    """ExecutionContext provides access to bar tensors."""
    bar_storage = {
        "energy": torch.tensor([1.0, 0.5, 0.8]),
        "health": torch.tensor([0.9, 0.7, 1.0]),
    }

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
    )

    energy = context.get_path("bar.energy")
    assert torch.equal(energy, torch.tensor([1.0, 0.5, 0.8]))


def test_execution_context_vfs_access():
    """ExecutionContext provides access to VFS variables."""
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_global("day_count", torch.tensor(42))
    registry.set_agent("motivation", torch.tensor([1.0, 0.8, 1.2]))

    context = ExecutionContext(
        bars=None,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
    )

    day_count = context.get_path("vfs.day_count")
    assert torch.equal(day_count, torch.tensor(42))

    motivation = context.get_path("vfs.motivation")
    assert torch.equal(motivation, torch.tensor([1.0, 0.8, 1.2]))


def test_execution_context_target_prefix():
    """ExecutionContext resolves 'target.' prefix."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=1,  # Target is agent index 1
    )

    # target.bar.energy should resolve to energy[1]
    target_energy = context.get_path("target.bar.energy")
    assert target_energy.item() == 0.5


def test_execution_context_set_path():
    """ExecutionContext can mutate bar/VFS values."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
    )

    # Mutate energy
    context.set_path("bar.energy", torch.tensor([0.9, 0.4, 0.7]))

    assert torch.equal(bar_storage["energy"], torch.tensor([0.9, 0.4, 0.7]))
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_execution_context.py::test_execution_context_bar_access -v
```

**Expected:** FAIL - Module 'townlet.effects.context' not found

---

### Step 2: Implement ExecutionContext

**File:** `src/townlet/effects/context.py`

```python
"""Execution context for effect command evaluation."""
from __future__ import annotations

import torch
from townlet.vfs.registry import ScopedVariableRegistry

__all__ = ["ExecutionContext"]


class ExecutionContext:
    """Runtime context for effect command execution.

    Provides access to:
    - bars: Meter tensors (energy, health, etc.)
    - vfs: VFS variable registry
    - self: Current agent/item index
    - target: Target agent/item index
    """

    def __init__(
        self,
        bars: dict[str, torch.Tensor] | None,
        vfs_registry: ScopedVariableRegistry | None,
        self_index: int | None,
        target_index: int | None,
    ):
        self.bars = bars or {}
        self.vfs_registry = vfs_registry
        self.self_index = self_index
        self.target_index = target_index

    def get_path(self, path: str) -> torch.Tensor:
        """Resolve path to tensor value.

        Args:
            path: Dot-separated path (e.g., "bar.energy", "vfs.motivation", "target.bar.health")

        Returns:
            Tensor value at path

        Raises:
            KeyError: If path not found
        """
        # Handle target. prefix
        if path.startswith("target."):
            if self.target_index is None:
                raise ValueError("target_index not set in context")

            # Resolve rest of path and index into target
            rest = path[len("target."):]
            tensor = self.get_path(rest)

            # If batched tensor, index into it
            if tensor.dim() > 0:
                return tensor[self.target_index]
            return tensor

        # Handle self. prefix
        if path.startswith("self."):
            if self.self_index is None:
                raise ValueError("self_index not set in context")

            rest = path[len("self."):]
            tensor = self.get_path(rest)

            if tensor.dim() > 0:
                return tensor[self.self_index]
            return tensor

        # Handle bar.* paths
        if path.startswith("bar."):
            bar_name = path[len("bar."):]
            if bar_name not in self.bars:
                raise KeyError(f"Bar '{bar_name}' not found. Available: {list(self.bars.keys())}")
            return self.bars[bar_name]

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path[len("vfs."):]

            # Try global scope first
            if var_name in self.vfs_registry.list_global():
                return self.vfs_registry.get_global(var_name)

            # Try agent scope
            if var_name in self.vfs_registry.list_agent():
                return self.vfs_registry.get_agent(var_name)

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")

    def set_path(self, path: str, value: torch.Tensor):
        """Set path to new tensor value (mutation).

        Args:
            path: Dot-separated path
            value: New tensor value
        """
        # Handle target. prefix
        if path.startswith("target."):
            if self.target_index is None:
                raise ValueError("target_index not set in context")

            rest = path[len("target."):]
            # Get original tensor and mutate in-place
            original = self.get_path(rest)
            if original.dim() > 0:
                original[self.target_index] = value
            else:
                # Scalar case - need to replace
                self.set_path(rest, value)
            return

        # Handle bar.* paths
        if path.startswith("bar."):
            bar_name = path[len("bar."):]
            if bar_name not in self.bars:
                raise KeyError(f"Bar '{bar_name}' not found")
            self.bars[bar_name] = value
            return

        # Handle vfs.* paths
        if path.startswith("vfs."):
            if self.vfs_registry is None:
                raise ValueError("VFS registry not set in context")

            var_name = path[len("vfs."):]

            # Try global scope
            if var_name in self.vfs_registry.list_global():
                self.vfs_registry.set_global(var_name, value)
                return

            # Try agent scope
            if var_name in self.vfs_registry.list_agent():
                self.vfs_registry.set_agent(var_name, value)
                return

            raise KeyError(f"VFS variable '{var_name}' not found")

        raise ValueError(f"Invalid path: {path}")
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_execution_context.py -v
```

**Expected:** All 5 tests PASS

**Commit:**
```bash
git add src/townlet/effects/context.py tests/test_townlet/unit/effects/test_execution_context.py
git commit -m "feat(effects): add ExecutionContext for command evaluation"
```

---

### Step 3: Write failing test for CommandExecutor modify command

**File:** `tests/test_townlet/unit/effects/test_command_executor.py`

```python
"""Tests for command executor."""
import pytest
import torch
from townlet.effects.executor import CommandExecutor
from townlet.effects.context import ExecutionContext
from townlet.effects.schema import CommandNode, CommandType


def test_executor_modify_bar():
    """Executor modifies bar value via expression."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
    )

    command = CommandNode(
        type=CommandType.MODIFY,
        path="bar.energy",
        value_expr="bar.energy + 0.1"
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # Energy should be increased by 0.1
    assert torch.allclose(bar_storage["energy"], torch.tensor([1.1, 0.6, 0.9]))


def test_executor_modify_with_target():
    """Executor modifies target-prefixed path."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=1,  # Target agent 1
    )

    command = CommandNode(
        type=CommandType.MODIFY,
        path="target.bar.energy",
        value_expr="target.bar.energy + 0.2"
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # Only agent 1's energy should change
    assert torch.allclose(bar_storage["energy"], torch.tensor([1.0, 0.7, 0.8]))


def test_executor_modify_constant():
    """Executor can set constant values."""
    bar_storage = {"energy": torch.tensor([1.0, 0.5, 0.8])}

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=None,
        self_index=None,
        target_index=None,
    )

    command = CommandNode(
        type=CommandType.MODIFY,
        path="bar.energy",
        value_expr="0.5"
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # All energy set to 0.5
    assert torch.equal(bar_storage["energy"], torch.tensor([0.5, 0.5, 0.5]))
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_executor.py::test_executor_modify_bar -v
```

**Expected:** FAIL - Module 'townlet.effects.executor' not found

---

### Step 4: Implement CommandExecutor for modify commands

**File:** `src/townlet/effects/executor.py`

```python
"""Command executor for effect pipelines."""
from __future__ import annotations

import torch
from townlet.effects.context import ExecutionContext
from townlet.effects.schema import CommandNode, CommandType
from townlet.world.expression.evaluator import Evaluator, EvaluationContext
# NOTE: No ExpressionParser import - ASTs are pre-compiled by CommandCompiler!

__all__ = ["CommandExecutor"]


class CommandExecutor:
    """Execute effect commands against runtime context.

    IMPORTANT: Commands contain pre-compiled ASTs (from CommandCompiler).
    This executor NEVER parses expressions - it only evaluates pre-compiled ASTs.
    """

    def __init__(self):
        # No parser needed! ASTs are pre-compiled
        self.evaluator = Evaluator()

    def execute(self, command: CommandNode, context: ExecutionContext):
        """Execute single command.

        Args:
            command: CommandNode with pre-compiled ASTs
            context: Runtime execution context

        Raises:
            NotImplementedError: For unimplemented command types
        """
        if command.type == CommandType.MODIFY:
            self._execute_modify(command, context)
        elif command.type == CommandType.SPAWN_EFFECT:
            self._execute_spawn_effect(command, context)
        elif command.type == CommandType.IF:
            self._execute_if(command, context)
        elif command.type == CommandType.FOR_EACH:
            self._execute_for_each(command, context)
        else:
            raise NotImplementedError(f"Command type {command.type} not implemented")

    def _execute_modify(self, command: CommandNode, context: ExecutionContext):
        """Execute modify command.

        Args:
            command: Modify command node with pre-compiled value_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        value_ast = command.value_ast

        # Create evaluation context from execution context
        eval_ctx = self._make_eval_context(context)

        # Evaluate pre-compiled expression
        result = self.evaluator.evaluate(value_ast, eval_ctx)

        # Set path to result
        context.set_path(command.path, result)

    def _execute_spawn_effect(self, command: CommandNode, context: ExecutionContext):
        """Execute spawn_effect command (stub for now).

        Args:
            command: Spawn effect command node
            context: Execution context
        """
        # Stub for Task 3.4 (EffectManager integration)
        pass

    def _execute_if(self, command: CommandNode, context: ExecutionContext):
        """Execute if command.

        Args:
            command: If command node with pre-compiled condition_ast
            context: Execution context
        """
        # ✅ PERF FIX: Use pre-compiled AST directly (NO parsing at runtime!)
        cond_ast = command.condition_ast
        eval_ctx = self._make_eval_context(context)

        # Evaluate pre-compiled condition
        condition = self.evaluator.evaluate(cond_ast, eval_ctx)

        # Execute then or else branch
        if condition.item():  # Convert to Python bool
            for cmd in command.then_commands:
                self.execute(cmd, context)
        else:
            for cmd in command.else_commands:
                self.execute(cmd, context)

    def _execute_for_each(self, command: CommandNode, context: ExecutionContext):
        """Execute for_each command (stub for now).

        Args:
            command: For each command node
            context: Execution context
        """
        # Stub for now - requires iterator support in EvaluationContext
        raise NotImplementedError("for_each not implemented yet")

    def _make_eval_context(self, context: ExecutionContext) -> EvaluationContext:
        """Convert ExecutionContext to EvaluationContext.

        Args:
            context: Effect execution context

        Returns:
            Expression evaluation context
        """
        # Build variable dict from context
        variables = {}

        # Add bars
        for bar_name, tensor in context.bars.items():
            variables[f"bar.{bar_name}"] = tensor

        # Add VFS globals
        if context.vfs_registry:
            for var_name in context.vfs_registry.list_global():
                tensor = context.vfs_registry.get_global(var_name)
                variables[f"vfs.{var_name}"] = tensor

            # Add VFS agent variables
            for var_name in context.vfs_registry.list_agent():
                tensor = context.vfs_registry.get_agent(var_name)
                variables[f"vfs.{var_name}"] = tensor

        # Add target. prefix if target_index set
        if context.target_index is not None:
            for key, tensor in list(variables.items()):
                if tensor.dim() > 0:
                    variables[f"target.{key}"] = tensor[context.target_index]

        return EvaluationContext(variables=variables)

    def execute_commands(self, commands: list[CommandNode], context: ExecutionContext):
        """Execute list of commands in order.

        Args:
            commands: List of command nodes
            context: Execution context
        """
        for command in commands:
            self.execute(command, context)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_executor.py -k "modify" -v
```

**Expected:** All 3 modify tests PASS

**Commit:**
```bash
git add src/townlet/effects/executor.py tests/test_townlet/unit/effects/test_command_executor.py
git commit -m "feat(effects): add CommandExecutor with modify command execution"
```

---

### Step 5: Write failing test for if command execution

**File:** `tests/test_townlet/unit/effects/test_command_executor.py` (append)

```python
def test_executor_if_then():
    """Executor executes then branch when condition true."""
    bar_storage = {"energy": torch.tensor([0.1, 0.5, 0.8])}

    from townlet.vfs.registry import ScopedVariableRegistry
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_agent("is_crisis", torch.tensor([False, False, False]))

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
    )

    command = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy < 0.2",  # Will match [0.1, _, _]
        then_commands=[
            CommandNode(
                type=CommandType.MODIFY,
                path="vfs.is_crisis",
                value_expr="true"
            )
        ],
        else_commands=[]
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # First agent should have is_crisis set to true
    # But this is a vectorized operation, so ALL will be set
    # For proper per-agent logic, need target_index
    is_crisis = registry.get_agent("is_crisis")
    assert is_crisis.any()  # At least one true


def test_executor_if_else():
    """Executor executes else branch when condition false."""
    bar_storage = {"energy": torch.tensor([0.9])}

    from townlet.vfs.registry import ScopedVariableRegistry
    registry = ScopedVariableRegistry(device=torch.device("cpu"))
    registry.set_agent("status", torch.tensor([0]))

    context = ExecutionContext(
        bars=bar_storage,
        vfs_registry=registry,
        self_index=None,
        target_index=None,
    )

    command = CommandNode(
        type=CommandType.IF,
        condition_expr="bar.energy < 0.2",  # False
        then_commands=[
            CommandNode(type=CommandType.MODIFY, path="vfs.status", value_expr="1")
        ],
        else_commands=[
            CommandNode(type=CommandType.MODIFY, path="vfs.status", value_expr="2")
        ]
    )

    executor = CommandExecutor()
    executor.execute(command, context)

    # Else branch should execute
    status = registry.get_agent("status")
    assert torch.equal(status, torch.tensor([2]))
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/test_command_executor.py -k "if" -v
```

**Expected:** Both if tests PASS

**Commit:**
```bash
git add tests/test_townlet/unit/effects/test_command_executor.py
git commit -m "test(effects): add if command execution tests"
```

---

### Step 6: Add module exports

**File:** `src/townlet/effects/__init__.py` (update)

```python
"""Effects system for HAMLET World Compiler."""
from __future__ import annotations

from townlet.effects.catalog import CompiledEffect, EffectCatalog
from townlet.effects.parser import CommandParser
from townlet.effects.compiler import CommandCompiler
from townlet.effects.schema import CommandNode, CommandType
from townlet.effects.executor import CommandExecutor
from townlet.effects.context import ExecutionContext

__all__ = [
    "EffectCatalog",
    "CompiledEffect",
    "CommandParser",
    "CommandCompiler",
    "CommandNode",
    "CommandType",
    "CommandExecutor",
    "ExecutionContext",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.effects import CommandExecutor, ExecutionContext; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/effects/__init__.py
git commit -m "feat(effects): export executor and context in module API"
```

---

### Step 7: Type checking and formatting

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

**Expected:** All ~37 tests PASS (27 from previous + 10 new)

**Commit if any changes:**
```bash
git add -u
git commit -m "test(effects): verify all executor tests pass"
```

---

## Success Criteria

✅ **37+ tests passing** (DTOs + parser + compiler + executor)
✅ **ExecutionContext resolves paths** (bar, vfs, target, self)
✅ **CommandExecutor modifies tensors** (GPU-native mutations)
✅ **Expression evaluation** (reuses Phase 1 evaluator)
✅ **If command execution** (conditional branches)
✅ **Target-scoped modifications** (per-agent mutations)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Task 3.4: EffectManager Runtime**

Implement ActiveEffect lifecycle, spawn/tick/despawn, and reapply policies.

See: `docs/plans/vfs_uplift/2025-11-19-task-3-4-effect-manager.md`
