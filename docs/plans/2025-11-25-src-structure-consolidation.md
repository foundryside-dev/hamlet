# src/townlet Structure Consolidation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate the redundant `compiler/` module, improve module exports, and clarify naming confusion between parse-time DTOs and runtime configs.

**Architecture:** The `compiler/` module (171 LOC) is just a CLI wrapper around `universe/compiler.py` (4,415 LOC). Moving CLI to `universe/__main__.py` eliminates confusion. World module needs root `__init__.py` for cleaner imports. Config naming needs clarifying docstrings.

**Tech Stack:** Python 3.13, Pydantic v2, pytest, ruff/black

---

## Overview

| Priority | Task | Impact | Risk |
|----------|------|--------|------|
| P1 | Delete `compiler/` module, move CLI to `universe/` | High - removes confusion | Low - just moving code |
| P2 | Add clarifying docstrings for parse/runtime config split | Medium - DX improvement | None |
| P3 | Add `world/__init__.py` with common exports | Medium - cleaner imports | None |
| P4 | Consolidate tiny config loaders (Optional) | Low - fewer files | Low |

---

## Task 1: Delete `compiler/` Module - Move CLI to `universe/`

**Files:**
- Delete: `src/townlet/compiler/__init__.py`
- Delete: `src/townlet/compiler/__main__.py`
- Create: `src/townlet/universe/__main__.py`
- Modify: `tests/test_townlet/unit/universe/test_compiler_cli.py:9`

### Step 1: Create `universe/__main__.py`

Copy the CLI code from `compiler/__main__.py` to `universe/__main__.py`, updating the module path references.

```python
"""CLI entry point for the Universe compiler (python -m townlet.universe)."""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from collections.abc import Iterable, Mapping
from pathlib import Path

from townlet.universe.compiled import CompiledUniverse
from townlet.universe.compiler import UniverseCompiler
from townlet.universe.errors import CompilationError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m townlet.universe",
        description="Utility commands for the UniverseCompiler (UAC CLI).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_parser = subparsers.add_parser("compile", help="Compile a config pack and optionally cache the artifact.")
    compile_parser.add_argument("config_dir", help="Path to config directory (contains training.yaml, bars.yaml, etc.)")
    compile_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip cache reads/writes (always rebuild).",
    )

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect a compiled universe artifact (MessagePack file).",
    )
    inspect_parser.add_argument("artifact", help="Path to config directory or .compiled/universe.msgpack artifact")
    inspect_parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for inspection (default: table)",
    )

    validate_parser = subparsers.add_parser("validate", help="Run compilation without touching the cache (lint-style check).")
    validate_parser.add_argument("config_dir", help="Path to config directory to validate")

    return parser


def _format_metadata_lines(metadata) -> list[str]:
    rows: list[tuple[str, str]] = [
        ("Universe", metadata.universe_name),
        ("Substrate", metadata.substrate_type),
        ("Meters", f"{metadata.meter_count}"),
        ("Affordances", f"{metadata.affordance_count}"),
        ("Actions", f"{metadata.action_count}"),
        ("Observation Dim", f"{metadata.observation_dim}"),
        ("Grid Cells", metadata.grid_cells if metadata.grid_cells is not None else "N/A"),
        ("Config Hash", metadata.config_hash[:16] if metadata.config_hash else ""),
        ("Compiled At", metadata.compiled_at),
    ]
    width = max(len(label) for label, _ in rows)
    return [f"  {label.ljust(width)} : {value}" for label, value in rows]


def _print_summary(metadata) -> None:
    print("Summary:")
    for line in _format_metadata_lines(metadata):
        print(line)


def _cmd_compile(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir).resolve()
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    compiler = UniverseCompiler()
    start = time.perf_counter()
    compiled = compiler.compile(config_dir, use_cache=not args.no_cache)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    _print_summary(compiled.metadata)
    print(f"Compilation succeeded in {elapsed_ms:.1f} ms")

    if not args.no_cache:
        cache_path = config_dir / ".compiled" / "universe.msgpack"
        if cache_path.exists():
            print(f"Cache artifact written to: {cache_path}")

    return 0


def _convert_for_json(value):
    if isinstance(value, Mapping):
        return {k: _convert_for_json(v) for k, v in dict(value).items()}
    if isinstance(value, list | tuple):
        return [_convert_for_json(v) for v in value]
    return value


def _metadata_to_dict(metadata) -> dict:
    payload = {}
    for field in dataclasses.fields(metadata):
        payload[field.name] = _convert_for_json(getattr(metadata, field.name))
    return payload


def _cmd_inspect(args: argparse.Namespace) -> int:
    artifact_path = Path(args.artifact).resolve()

    # Auto-resolve config directory to artifact path for better UX
    if artifact_path.is_dir():
        artifact_path = artifact_path / ".compiled" / "universe.msgpack"

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    compiled = CompiledUniverse.load_from_cache(artifact_path)
    if args.format == "json":
        payload = {
            "artifact": str(artifact_path),
            "metadata": _metadata_to_dict(compiled.metadata),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_summary(compiled.metadata)
        print(f"Artifact path: {artifact_path}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    config_dir = Path(args.config_dir).resolve()
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    compiler = UniverseCompiler()
    start = time.perf_counter()
    compiler.compile(config_dir, use_cache=False)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    print(f"Validation succeeded in {elapsed_ms:.1f} ms (no cache artifacts written)")
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.command == "compile":
            return _cmd_compile(args)
        if args.command == "inspect":
            return _cmd_inspect(args)
        if args.command == "validate":
            return _cmd_validate(args)
    except CompilationError as exc:  # pragma: no cover - exercised via tests indirectly
        print(f"Compilation failed: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
```

### Step 2: Update test import

Modify `tests/test_townlet/unit/universe/test_compiler_cli.py` line 9:

```python
# Before:
from townlet.compiler import __main__ as compiler_cli

# After:
from townlet.universe import __main__ as compiler_cli
```

### Step 3: Run tests to verify CLI still works

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/universe/test_compiler_cli.py -v`

Expected: All 4 tests pass

### Step 4: Delete the old `compiler/` directory

```bash
rm -rf src/townlet/compiler/
```

### Step 5: Verify no imports reference old module

Run: `grep -r "from townlet.compiler" src/ tests/`

Expected: No matches (only docs will have references)

### Step 6: Run full test suite

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -x -q`

Expected: All tests pass

### Step 7: Commit

```bash
git add src/townlet/universe/__main__.py tests/test_townlet/unit/universe/test_compiler_cli.py
git rm -rf src/townlet/compiler/
git commit -m "$(cat <<'EOF'
refactor: move compiler CLI from townlet.compiler to townlet.universe

The compiler/ module was a thin 171 LOC wrapper around universe/compiler.py
(4,415 LOC). This consolidation:

- Moves CLI to universe/__main__.py (python -m townlet.universe)
- Deletes redundant compiler/ directory
- Updates test imports

Note: Documentation still references `python -m townlet.universe` - a follow-up
task will update those references via search/replace.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Update Documentation References

**Files to modify (search/replace):**
- `CLAUDE.md`
- `docs/UNIVERSE-COMPILER.md`
- `docs/guides/world-compiler-guide.md`
- `docs/guides/dac-migration.md`
- `.github/workflows/lint.yml`
- `scripts/validate_compiler_cli.py`
- Multiple other docs (see grep output)

### Step 1: Mass search/replace in documentation

Pattern: `python -m townlet.universe` → `python -m townlet.universe`

Run the following commands:

```bash
# Update all markdown files
find docs/ -name "*.md" -exec sed -i 's/python -m townlet\.compiler/python -m townlet.universe/g' {} \;

# Update CLAUDE.md
sed -i 's/python -m townlet\.compiler/python -m townlet.universe/g' CLAUDE.md

# Update workflows
sed -i 's/python -m townlet\.compiler/python -m townlet.universe/g' .github/workflows/lint.yml

# Update scripts
sed -i 's/python -m townlet\.compiler/python -m townlet.universe/g' scripts/validate_compiler_cli.py
```

### Step 2: Verify replacements

Run: `grep -r "python -m townlet.universe" . --include="*.md" --include="*.yml" --include="*.py" | grep -v ".git"`

Expected: Only `src/townlet/universe/compiled.py:398` (error message referencing old path - update manually)

### Step 3: Update error message in compiled.py

Modify `src/townlet/universe/compiled.py:398`:

```python
# Before:
"Recompile the config pack with `python -m townlet.universe compile <config_dir>`."

# After:
"Recompile the config pack with `python -m townlet.universe compile <config_dir>`."
```

### Step 4: Commit documentation updates

```bash
git add -A
git commit -m "$(cat <<'EOF'
docs: update CLI references from townlet.compiler to townlet.universe

Mass search/replace across all documentation, CI configs, and scripts
to reflect the consolidated CLI entry point.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Add Clarifying Docstrings for Parse-Time vs Runtime Configs

**Files:**
- Modify: `src/townlet/config/affordances_v2_config.py:1-14`
- Modify: `src/townlet/config/actions_config.py:1` (add docstring)
- Modify: `src/townlet/environment/affordance_config.py:1-7`
- Modify: `src/townlet/environment/action_config.py:1` (add docstring)

### Step 1: Update `config/affordances_v2_config.py` docstring

The existing docstring is good. Add a clear "PARSE-TIME" marker:

```python
"""Affordances configuration DTO for Config v2.1 (curriculum-level).

PARSE-TIME DTO: This module validates affordances.yaml structure during compilation.
For runtime affordance objects used by the environment, see:
    townlet.environment.affordance_config

Philosophy: All behavioral parameters must be explicitly specified.
No implicit defaults. Operator accountability.

Design: Validates affordances.yaml structure from v2.1 hierarchical configs.
Includes affordance parameters AND modulation parameters in same file.

Structure:
    affordances:
      version: "1.0"
      affordances: [...]    # How affordances behave in this curriculum level
      modulations: [...]    # How bars affect affordance effectiveness
"""
```

### Step 2: Update `environment/affordance_config.py` docstring

```python
"""Affordance configuration models for runtime.

RUNTIME DTO: This module defines runtime affordance objects used by the environment
stack during simulation. For parse-time YAML validation DTOs, see:
    townlet.config.affordances_v2_config

Config v2.1 compiles affordance metadata from hierarchical YAML packs;
this module does not perform any YAML loading.
"""
```

### Step 3: Add docstring to `config/actions_config.py`

```python
"""Actions configuration DTO for Config v2.1.

PARSE-TIME DTO: This module validates actions from training.yaml during compilation.
For runtime action configuration used by the environment, see:
    townlet.environment.action_config

Defines which actions are enabled for a curriculum level.
"""
```

### Step 4: Update `environment/action_config.py` docstring

Read the file first to see current state, then add:

```python
"""Action configuration models for runtime.

RUNTIME DTO: This module defines runtime action configuration used by the environment
stack during simulation. For parse-time YAML validation DTOs, see:
    townlet.config.actions_config

Action configs are compiled from the parse-time DTOs by the UniverseCompiler.
"""
```

### Step 5: Commit

```bash
git add src/townlet/config/affordances_v2_config.py \
        src/townlet/config/actions_config.py \
        src/townlet/environment/affordance_config.py \
        src/townlet/environment/action_config.py
git commit -m "$(cat <<'EOF'
docs: clarify parse-time vs runtime config distinction

Added PARSE-TIME and RUNTIME markers to docstrings to help developers
understand the relationship between:
- config/*.py (YAML validation during compilation)
- environment/*.py (runtime objects during simulation)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Add `world/__init__.py` for Cleaner Imports

**Files:**
- Create: `src/townlet/world/__init__.py`

### Step 1: Create `world/__init__.py`

```python
"""HAMLET World module - Expression language and type system.

This module provides the expression language used throughout HAMLET for:
- VFS (Variable & Feature System) computed fields
- Effects system commands
- Items system actions
- Dynamic state computations

Public API (re-exported from submodules):
    Expression Language:
        ExpressionParser - Parse expression strings to AST
        Evaluator - Evaluate AST against execution context
        TypeChecker - Validate expression types
        TypeCheckError - Type checking exception

    AST Nodes:
        ASTNode, ASTVisitor - Base classes
        Constant, Variable, PathAccess - Value access
        BinaryOp, UnaryOp - Operations
        FunctionCall, IfThenElse, IndexAccess - Complex expressions

    Runtime:
        ExecutionContext - Evaluation context with state access

    Types:
        PrimitiveType - Core type enum (int, float, bool, string, etc.)

Usage:
    >>> from townlet.world import ExpressionParser, Evaluator, ExecutionContext
    >>> parser = ExpressionParser()
    >>> ast = parser.parse("self.bar.energy + 0.1")
    >>> result = Evaluator().evaluate(ast, context)
"""

# Expression language (primary API)
from townlet.world.expression import (
    ASTNode,
    ASTVisitor,
    BinaryOp,
    Constant,
    Evaluator,
    ExecutionContext,
    ExpressionParser,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
    PathAccess,
    Reduce,
    Switch,
    TypeCheckError,
    TypeChecker,
    UnaryOp,
    Variable,
)

# Type system
from townlet.world.types.primitive import PrimitiveType

__all__ = [
    # Parser
    "ExpressionParser",
    # Evaluator
    "Evaluator",
    "ExecutionContext",
    # Type checker
    "TypeChecker",
    "TypeCheckError",
    # AST nodes
    "ASTNode",
    "ASTVisitor",
    "BinaryOp",
    "Constant",
    "FunctionCall",
    "IfThenElse",
    "IndexAccess",
    "OperatorType",
    "PathAccess",
    "Reduce",
    "Switch",
    "UnaryOp",
    "Variable",
    # Types
    "PrimitiveType",
]
```

### Step 2: Verify imports work

Run: `python -c "from townlet.world import ExpressionParser, Evaluator, TypeChecker; print('OK')"`

Expected: `OK`

### Step 3: Run tests to ensure no regressions

Run: `UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/effects/ -v -q`

Expected: All tests pass

### Step 4: Commit

```bash
git add src/townlet/world/__init__.py
git commit -m "$(cat <<'EOF'
feat: add world/__init__.py for cleaner imports

Enables importing common expression language components directly from
townlet.world instead of nested paths:

    # Before
    from townlet.world.expression.parser import ExpressionParser

    # After
    from townlet.world import ExpressionParser

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 5 (Optional): Consolidate Tiny Config Loaders

**Decision point:** The `config/exploration.py` (24 LOC) and `config/curriculum.py` (14 LOC) files contain loader functions, not just re-exports. They provide convenience wrappers.

**Recommendation:** SKIP this task. These files:
1. Have distinct loader functions (`load_exploration_config`, `load_curriculum_config`)
2. Provide clean import paths for specific use cases
3. Are small but purposeful

Similarly, `config/vfs_config.py` (13 LOC) defines a standalone DTO class that may grow.

**Action:** Mark as "will not implement" - the current organization is acceptable.

---

## Final Verification

### Step 1: Run full test suite

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -q
```

Expected: All tests pass

### Step 2: Run linters

```bash
uv run ruff check src/townlet/
uv run black --check src/townlet/
uv run mypy src/townlet/
```

Expected: No errors

### Step 3: Verify CLI works end-to-end

```bash
python -m townlet.universe validate configs/L0_0_minimal/
python -m townlet.universe compile configs/L0_0_minimal/
python -m townlet.universe inspect configs/L0_0_minimal/
```

Expected: All commands succeed

---

## Summary of Changes

| Change | LOC Removed | LOC Added | Net |
|--------|-------------|-----------|-----|
| Delete `compiler/` module | 171 | 0 | -171 |
| Create `universe/__main__.py` | 0 | 167 | +167 |
| Update test import | 1 | 1 | 0 |
| Documentation updates | ~50 refs | ~50 refs | 0 |
| Clarifying docstrings | 0 | ~40 | +40 |
| `world/__init__.py` | 0 | ~75 | +75 |

**Net result:** +111 LOC, but eliminates module confusion and improves DX.
