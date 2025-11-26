# Task 2.3: Expression Evaluation Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Wire expression evaluator into VFS for dynamic variable computation with dependency ordering and circular dependency detection.

**Architecture:** Topological sort for evaluation order. Expression execution context with bars, vfs, self, target paths. Circular dependency detection via graph traversal.

**Tech Stack:** PyTorch tensors, networkx (for topological sort), Python 3.11+

**Dependencies:** Task 1.4 (Expression Evaluator), Task 2.1 (VFS Profiles DTOs), Task 2.2 (Scoped Registry)

---

## Background

Phase 1 VFS had static initial values. Phase 2 VFS variables can have `expression:` fields that compute values dynamically.

**Challenge:** Variables can depend on other variables:
```yaml
- name: energy_fraction
  expression: "bar.energy / bar.max_energy"  # Depends on bars

- name: is_crisis
  expression: "energy_fraction < 0.2"  # Depends on energy_fraction
```

**Solution:** Topological sort ensures dependencies are evaluated before dependents. Circular dependencies raise compile-time error.

---

## Task Breakdown

### Step 1: Write failing test for dependency graph construction

**File:** `tests/test_townlet/unit/vfs/test_expression_integration.py`

```python
"""Tests for VFS expression evaluation integration."""
import pytest
import torch
from townlet.vfs.profiles import VFSProfileCompiler
from townlet.config.vfs_profiles_config import (
    GlobalVFSProfileConfig,
    GlobalVFSVariableConfig,
)


def test_build_dependency_graph_no_deps():
    """Variables with no dependencies have no edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="day_count", type="int", initial_value=0),
            GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # No dependencies = no edges
    assert len(graph.edges) == 0
    assert set(graph.nodes) == {"day_count", "tick"}


def test_build_dependency_graph_with_deps():
    """Variables with expression dependencies have edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="tick", type="int", initial_value=0),
            GlobalVFSVariableConfig(
                name="is_night",
                type="bool",
                expression="tick % 24 >= 18"
            ),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # is_night depends on tick
    assert ("tick", "is_night") in graph.edges


def test_build_dependency_graph_nested_deps():
    """Nested dependencies create transitive edges."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    graph = compiler.build_dependency_graph(profile.variables)

    # a -> b -> c
    assert ("a", "b") in graph.edges
    assert ("b", "c") in graph.edges
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py::test_build_dependency_graph_no_deps -v
```

**Expected:** FAIL - VFSProfileCompiler not defined

---

### Step 2: Implement dependency graph construction

**File:** `src/townlet/vfs/profiles.py`

```python
"""VFS profile compilation with expression evaluation."""
import networkx as nx
from typing import Any
from townlet.config.vfs_profiles_config import (
    GlobalVFSVariableConfig,
    AgentVFSVariableConfig,
    ItemVFSVariableConfig,
)
from townlet.world.expression import ExpressionParser, Variable, ASTNode


class VFSProfileCompiler:
    """Compiles VFS profiles with expression dependency resolution."""

    def __init__(self):
        self.parser = ExpressionParser()

    def build_dependency_graph(
        self,
        variables: list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> nx.DiGraph:
        """Build dependency graph for variables.

        Args:
            variables: List of variable configs

        Returns:
            Directed graph with edges from dependency -> dependent
        """
        graph = nx.DiGraph()

        # Add all variables as nodes
        for var in variables:
            graph.add_node(var.name)

        # Add edges for expression dependencies
        for var in variables:
            if var.expression is not None:
                # Extract variable references from expression
                deps = self._extract_variable_refs(var.expression)
                for dep in deps:
                    # Only add edge if dependency is in same profile
                    if dep in [v.name for v in variables]:
                        graph.add_edge(dep, var.name)

        return graph

    def _extract_variable_refs(self, expression: str) -> set[str]:
        """Extract variable references by parsing AST (robust, not regex).

        Uses Phase 1 parser to build AST, then traverses to find Variable nodes.
        This is 100% accurate - no false matches from string literals or partial matches.

        Args:
            expression: Expression string (e.g., "a + b * c")

        Returns:
            Set of variable names referenced
        """
        # Parse expression to AST (reuse Phase 1 parser!)
        ast = self.parser.parse(expression)

        # Traverse AST to collect Variable nodes
        refs = set()

        def visit(node: ASTNode) -> None:
            """Recursively visit AST nodes to find Variables."""
            if isinstance(node, Variable):
                refs.add(node.name)

            # Visit children (handles BinaryOp, UnaryOp, FunctionCall, etc.)
            if hasattr(node, 'left'):
                visit(node.left)
            if hasattr(node, 'right'):
                visit(node.right)
            if hasattr(node, 'operand'):
                visit(node.operand)
            if hasattr(node, 'arguments'):
                for arg in node.arguments:
                    visit(arg)
            if hasattr(node, 'condition'):
                visit(node.condition)
            if hasattr(node, 'true_branch'):
                visit(node.true_branch)
            if hasattr(node, 'false_branch'):
                visit(node.false_branch)
            if hasattr(node, 'base'):
                visit(node.base)
            if hasattr(node, 'index'):
                visit(node.index)

        visit(ast)
        return refs
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -k "dependency_graph" -v
```

**Expected:** All 3 dependency graph tests PASS

**Commit:**
```bash
git add src/townlet/vfs/profiles.py tests/test_townlet/unit/vfs/test_expression_integration.py
git commit -m "feat(vfs): add dependency graph construction for VFS variables"
```

---

### Step 3: Write failing test for circular dependency detection

**File:** `tests/test_townlet/unit/vfs/test_expression_integration.py` (append)

```python
from townlet.vfs.profiles import CircularDependencyError


def test_detect_circular_dependency_simple():
    """Detect simple circular dependency (a -> b -> a)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_detect_circular_dependency_complex():
    """Detect complex circular dependency (a -> b -> c -> a)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", expression="c + 1"),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
        ]
    )

    compiler = VFSProfileCompiler()

    with pytest.raises(CircularDependencyError, match="cycle"):
        compiler.topological_sort(profile.variables)


def test_topological_sort_no_deps():
    """Topological sort with no dependencies."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", initial_value=2),
        ]
    )

    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile.variables)

    # Both have no deps, order doesn't matter (but should be deterministic)
    assert len(sorted_vars) == 2


def test_topological_sort_linear_deps():
    """Topological sort with linear dependencies (a -> b -> c)."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    sorted_vars = compiler.topological_sort(profile.variables)

    # Should be ordered: a, b, c
    names = [v.name for v in sorted_vars]
    assert names == ["a", "b", "c"]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py::test_detect_circular_dependency_simple -v
```

**Expected:** FAIL - topological_sort() not implemented

---

### Step 4: Implement topological sort with cycle detection

**File:** `src/townlet/vfs/profiles.py` (add exception and method)

```python
class CircularDependencyError(Exception):
    """Raised when circular dependency detected in VFS variables."""
    pass


class VFSProfileCompiler:
    # ... existing code ...

    def topological_sort(
        self,
        variables: list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]
    ) -> list[GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig]:
        """Sort variables in dependency order (dependencies first).

        Args:
            variables: List of variable configs

        Returns:
            Variables sorted in topological order

        Raises:
            CircularDependencyError: If circular dependency detected
        """
        graph = self.build_dependency_graph(variables)

        # Check for cycles
        try:
            # networkx raises NetworkXError if cycles exist
            sorted_names = list(nx.topological_sort(graph))
        except nx.NetworkXError:
            # Find a cycle for error message
            cycles = list(nx.simple_cycles(graph))
            cycle_str = " -> ".join(cycles[0] + [cycles[0][0]])
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle_str}"
            )

        # Map names back to variable configs
        name_to_var = {v.name: v for v in variables}
        sorted_vars = [name_to_var[name] for name in sorted_names]

        return sorted_vars
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -k "circular or topological" -v
```

**Expected:** All 4 tests PASS

**Commit:**
```bash
git add src/townlet/vfs/profiles.py tests/test_townlet/unit/vfs/test_expression_integration.py
git commit -m "feat(vfs): add topological sort with circular dependency detection"
```

---

### Step 5: Write failing test for expression compilation

**File:** `tests/test_townlet/unit/vfs/test_expression_integration.py` (append)

```python
from townlet.world.expression import ExpressionParser
from townlet.world.types import ScalarType, BoolType


def test_compile_variable_with_expression():
    """Compiler parses and type-checks expressions."""
    var = GlobalVFSVariableConfig(
        name="is_night",
        type="bool",
        expression="tick % 24 >= 18"
    )

    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}  # Available variables

    compiled = compiler.compile_variable(var, schema)

    assert compiled.name == "is_night"
    assert compiled.ast is not None  # Parsed AST
    assert compiled.result_type == "bool"


def test_compile_variable_with_initial_value():
    """Compiler handles static initial values (no expression)."""
    var = GlobalVFSVariableConfig(
        name="day_count",
        type="int",
        initial_value=0
    )

    compiler = VFSProfileCompiler()
    schema = {}

    compiled = compiler.compile_variable(var, schema)

    assert compiled.name == "day_count"
    assert compiled.ast is None  # No expression
    assert compiled.initial_value == 0


def test_compile_variable_type_mismatch():
    """Compiler catches type mismatches."""
    from townlet.world.expression.type_checker import TypeCheckError

    var = GlobalVFSVariableConfig(
        name="invalid",
        type="bool",
        expression="tick + 1"  # Returns int, not bool
    )

    compiler = VFSProfileCompiler()
    schema = {"tick": "int"}

    with pytest.raises(TypeCheckError, match="bool"):
        compiler.compile_variable(var, schema)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py::test_compile_variable_with_expression -v
```

**Expected:** FAIL - compile_variable() not implemented

---

### Step 6: Implement expression compilation

**File:** `src/townlet/vfs/profiles.py` (add dataclass and method)

```python
from dataclasses import dataclass
from typing import Optional
from townlet.world.expression import ExpressionParser, ASTNode
from townlet.world.expression.type_checker import TypeChecker


@dataclass
class CompiledVariable:
    """Compiled VFS variable with parsed expression."""

    name: str
    type: str
    ast: Optional[ASTNode]  # None if initial_value
    initial_value: Optional[int | float | bool | list]
    result_type: Optional[str]  # Inferred type from type checker


class VFSProfileCompiler:
    def __init__(self):
        self.parser = ExpressionParser()

    # ... existing code ...

    def compile_variable(
        self,
        var: GlobalVFSVariableConfig | AgentVFSVariableConfig | ItemVFSVariableConfig,
        schema: dict[str, str]
    ) -> CompiledVariable:
        """Compile a VFS variable (parse expression, type check).

        Args:
            var: Variable config
            schema: Type schema for available variables

        Returns:
            Compiled variable with parsed AST

        Raises:
            TypeCheckError: If expression has type error
        """
        # Variable with static initial value
        if var.initial_value is not None:
            return CompiledVariable(
                name=var.name,
                type=var.type,
                ast=None,
                initial_value=var.initial_value,
                result_type=var.type,
            )

        # Variable with expression
        # Parse expression to AST
        ast = self.parser.parse(var.expression)

        # Type check expression
        type_checker = TypeChecker(schema=schema)
        result_type = type_checker.check(ast)

        # Verify result type matches declared type
        if result_type != var.type:
            raise TypeError(
                f"Variable '{var.name}' declared as {var.type} but "
                f"expression returns {result_type}"
            )

        return CompiledVariable(
            name=var.name,
            type=var.type,
            ast=ast,
            initial_value=None,
            result_type=result_type,
        )
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -k "compile_variable" -v
```

**Expected:** All 3 compile_variable tests PASS

**Commit:**
```bash
git add src/townlet/vfs/profiles.py tests/test_townlet/unit/vfs/test_expression_integration.py
git commit -m "feat(vfs): add expression compilation with type checking"
```

---

### Step 7: Write failing test for profile compilation

**File:** `tests/test_townlet/unit/vfs/test_expression_integration.py` (append)

```python
def test_compile_global_profile():
    """Compiler compiles global profile with dependency ordering."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(name="c", type="int", expression="b + 1"),
            GlobalVFSVariableConfig(name="a", type="int", initial_value=1),
            GlobalVFSVariableConfig(name="b", type="int", expression="a + 1"),
        ]
    )

    compiler = VFSProfileCompiler()
    compiled = compiler.compile_global_profile(profile)

    # Variables sorted in dependency order
    assert [v.name for v in compiled.variables] == ["a", "b", "c"]

    # All variables compiled
    assert all(v.ast is not None or v.initial_value is not None for v in compiled.variables)


def test_compile_global_profile_with_bars():
    """Compiler includes bars in schema for expressions."""
    profile = GlobalVFSProfileConfig(
        variables=[
            GlobalVFSVariableConfig(
                name="avg_energy",
                type="float",
                expression="bar.energy"  # Reference to bar
            ),
        ]
    )

    compiler = VFSProfileCompiler()
    # Should not raise (bar.energy is valid path)
    compiled = compiler.compile_global_profile(profile, bar_schema={"energy": "float"})

    assert compiled.variables[0].name == "avg_energy"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py::test_compile_global_profile -v
```

**Expected:** FAIL - compile_global_profile() not implemented

---

### Step 8: Implement profile compilation

**File:** `src/townlet/vfs/profiles.py` (add dataclass and method)

```python
@dataclass
class CompiledGlobalProfile:
    """Compiled global VFS profile."""

    variables: list[CompiledVariable]


class VFSProfileCompiler:
    # ... existing code ...

    def compile_global_profile(
        self,
        profile: GlobalVFSProfileConfig,
        bar_schema: Optional[dict[str, str]] = None
    ) -> CompiledGlobalProfile:
        """Compile global VFS profile.

        Args:
            profile: Global profile config
            bar_schema: Type schema for bars (e.g., {"energy": "float"})

        Returns:
            Compiled profile with variables in dependency order
        """
        # Sort variables in dependency order
        sorted_vars = self.topological_sort(profile.variables)

        # Build type schema for expression type checking
        schema: dict[str, str] = {}

        # Add bar paths to schema
        if bar_schema:
            for bar_name, bar_type in bar_schema.items():
                schema[f"bar.{bar_name}"] = bar_type

        # Compile each variable
        compiled_vars = []
        for var in sorted_vars:
            compiled = self.compile_variable(var, schema)
            compiled_vars.append(compiled)

            # Add this variable to schema for subsequent variables
            schema[var.name] = var.type

        return CompiledGlobalProfile(variables=compiled_vars)
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -k "compile_global_profile" -v
```

**Expected:** Both profile compilation tests PASS

**Commit:**
```bash
git add src/townlet/vfs/profiles.py tests/test_townlet/unit/vfs/test_expression_integration.py
git commit -m "feat(vfs): add global profile compilation with dependency ordering"
```

---

### Step 9: Add module exports

**File:** `src/townlet/vfs/profiles.py` (add at top)

```python
"""VFS profile compilation with expression evaluation."""
from __future__ import annotations
import networkx as nx
from dataclasses import dataclass
from typing import Optional, Any
from townlet.config.vfs_profiles_config import (
    GlobalVFSVariableConfig,
    AgentVFSVariableConfig,
    ItemVFSVariableConfig,
    GlobalVFSProfileConfig,
)
from townlet.world.expression import ExpressionParser, ASTNode, Variable
from townlet.world.expression.type_checker import TypeChecker

__all__ = [
    "VFSProfileCompiler",
    "CircularDependencyError",
    "CompiledVariable",
    "CompiledGlobalProfile",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.vfs.profiles import VFSProfileCompiler; print('OK')"
```

**Expected:** Prints "OK"

**Commit:**
```bash
git add src/townlet/vfs/profiles.py
git commit -m "feat(vfs): export VFS profile compiler in module API"
```

---

### Step 10: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/vfs/profiles.py
```

**Expected:** Success

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/vfs/profiles.py tests/test_townlet/unit/vfs/test_expression_integration.py
UV_CACHE_DIR=.uv-cache uv run ruff check src/townlet/vfs/profiles.py
```

**Expected:** No changes needed

**Run full test suite:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/vfs/test_expression_integration.py -v
```

**Expected:** All ~13 tests PASS

**Commit:**
```bash
git add -u
git commit -m "test(vfs): verify all expression integration tests pass"
```

---

## Success Criteria

✅ **13+ tests passing** (dependency graph, topological sort, compilation)
✅ **Dependency graph construction** (AST traversal for variable refs - 100% accurate, no regex)
✅ **Circular dependency detection** (raises compile-time error)
✅ **Topological sort** (evaluates dependencies before dependents)
✅ **Expression compilation** (parse + type check)
✅ **Profile compilation** (full pipeline with dependency ordering)
✅ **Reuses Phase 1 infrastructure** (ExpressionParser, AST nodes)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Task 2.4: Observation Builder**

Include VFS fields in observations:
- Fixed slot allocation for item VFS (3 slots × 5 profiles)
- Masking for empty slots
- obs_dim calculation with VFS variables

See: `docs/plans/vfs_uplift/2025-11-19-task-2-4-observation-builder.md` (to be created)
