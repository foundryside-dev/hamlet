# [COMP-11] Command Parser Integration Clarity

**Priority:** P1 (Important)
**Category:** Testing/Documentation
**Status:** PARTIAL
**Effort:** 2-3 hours

## Description

Command parser exists and functions correctly, but integration details with compiler pipeline are unclear. Gap analysis couldn't verify how command compilation flows from YAML → AST → compiled effects catalog. Need documentation or tests showing end-to-end compilation flow.

## Current State

**Implementation:** ✅ COMPLETE
- Parser: `src/townlet/effects/parser.py`
- Compiler: `src/townlet/effects/compiler.py`
- Integration point: Effects catalog compilation in UniverseCompiler

**Test Coverage:** ⚠️ INTEGRATION UNCLEAR
- Unit tests exist: `test_command_parser.py`, `test_command_compiler.py`
- Integration unclear: How does YAML flow through pipeline?
- Missing: End-to-end compilation trace

**Questions:**
1. Where does command parsing happen in compiler pipeline?
2. How are expressions extracted and compiled to ASTs?
3. How are compiled commands stored in EffectCatalog?
4. How does runtime access pre-compiled ASTs?

## Required Implementation

### Option A: Integration Test (Recommended - 2 hours)

Create test showing complete compilation flow:

**File:** `tests/test_townlet/integration/test_effects_compilation_pipeline.py`

```python
"""End-to-end tests for effects compilation pipeline."""

import pytest
from pathlib import Path

from townlet.universe.compiler import UniverseCompiler
from townlet.effects.catalog import EffectCatalog


class TestEffectsCompilationPipeline:
    """Tests for YAML → Catalog compilation flow."""

    def test_effect_compilation_end_to_end(self, tmp_path):
        """Effect YAML compiles to catalog with pre-compiled ASTs."""

        # Step 1: Create minimal config with effect
        config_dir = tmp_path / "test_config"
        config_dir.mkdir()

        effects_yaml = config_dir / "effects.yaml"
        effects_yaml.write_text("""
version: "1.0"

effects:
  damage_over_time:
    duration: 10
    reapply_policy: stack
    commands:
      - type: modify
        path: target.bar.health
        operation: subtract
        value: "0.1 * vfs:intensity"
""")

        # Step 2: Compile with UniverseCompiler
        compiler = UniverseCompiler()
        catalog = compiler._compile_effects_catalog(config_dir)

        # Step 3: Verify catalog structure
        assert "damage_over_time" in catalog.effects
        effect = catalog.effects["damage_over_time"]

        # Step 4: Verify command compiled with AST
        assert len(effect.commands) == 1
        cmd = effect.commands[0]
        assert cmd.type == CommandType.MODIFY
        assert cmd.path == "target.bar.health"
        assert cmd.value_expr == "0.1 * vfs:intensity"
        assert cmd.value_ast is not None  # ✅ Pre-compiled AST exists

        # Step 5: Verify AST is executable
        # (would need ExecutionContext to fully test)

    def test_nested_commands_compilation(self, tmp_path):
        """Nested commands (if/for_each) compile with ASTs."""

        config_dir = tmp_path / "test_config"
        config_dir.mkdir()

        effects_yaml = config_dir / "effects.yaml"
        effects_yaml.write_text("""
version: "1.0"

effects:
  conditional_heal:
    duration: 1
    commands:
      - type: if
        condition: "target.bar.health < 0.5"
        then:
          - type: modify
            path: target.bar.health
            operation: add
            value: "0.2"
        else:
          - type: modify
            path: target.bar.health
            operation: add
            value: "0.1"
""")

        compiler = UniverseCompiler()
        catalog = compiler._compile_effects_catalog(config_dir)

        effect = catalog.effects["conditional_heal"]
        cmd = effect.commands[0]

        # Verify condition compiled to AST
        assert cmd.type == CommandType.IF
        assert cmd.condition_expr == "target.bar.health < 0.5"
        assert cmd.condition_ast is not None  # ✅ Condition is AST

        # Verify nested commands exist
        assert len(cmd.then_commands) == 1
        assert len(cmd.else_commands) == 1

        # Verify nested command expressions compiled
        then_cmd = cmd.then_commands[0]
        assert then_cmd.value_ast is not None

    def test_command_parser_error_reporting(self, tmp_path):
        """Parser errors include file location and suggestions."""

        config_dir = tmp_path / "test_config"
        config_dir.mkdir()

        effects_yaml = config_dir / "effects.yaml"
        effects_yaml.write_text("""
version: "1.0"

effects:
  broken_effect:
    commands:
      - type: modify
        path: target.bar.health
        operation: invalid_op
        value: "0.1"
""")

        compiler = UniverseCompiler()

        with pytest.raises(ValueError) as exc_info:
            compiler._compile_effects_catalog(config_dir)

        error_msg = str(exc_info.value)
        assert "invalid_op" in error_msg
        assert "broken_effect" in error_msg  # Effect name in error
        # Optionally: check for suggestions like "Did you mean 'add'?"

    def test_expression_syntax_error_reporting(self, tmp_path):
        """Expression syntax errors reported with context."""

        config_dir = tmp_path / "test_config"
        config_dir.mkdir()

        effects_yaml = config_dir / "effects.yaml"
        effects_yaml.write_text("""
version: "1.0"

effects:
  syntax_error_effect:
    commands:
      - type: modify
        path: target.bar.health
        operation: add
        value: "0.1 +"  # Syntax error: incomplete expression
""")

        compiler = UniverseCompiler()

        with pytest.raises(Exception) as exc_info:  # Could be ParseError or ValueError
            compiler._compile_effects_catalog(config_dir)

        error_msg = str(exc_info.value)
        assert "syntax_error_effect" in error_msg or "0.1 +" in error_msg


class TestCommandASTCaching:
    """Verify ASTs are pre-compiled (not parsed at runtime)."""

    def test_ast_created_at_compile_time(self, tmp_path):
        """AST nodes exist in catalog, not expression strings."""

        # Create and compile effect
        # ...

        # Verify value_ast is not None
        # Verify condition_ast is not None (for if commands)
        # Verify ASTs are actual ASTNode instances, not strings
```

### Option B: Documentation (Faster - 1 hour)

**File:** `docs/architecture/EFFECTS_COMPILATION_FLOW.md`

```markdown
# Effects Compilation Flow

## Pipeline Stages

### Stage 1: YAML Parse
**Location:** `UniverseCompiler._stage_1_load_configs()`
**Input:** `effects.yaml` file
**Output:** `EffectsConfig` DTO (Pydantic validation)

### Stage 2: Command Parsing
**Location:** `EffectCompiler.compile_effect()`
**Input:** `EffectDefinitionConfig` from DTO
**Output:** `CommandNode` AST with pre-compiled expressions

**Key Operations:**
1. Parse command structure (type, path, value, etc.)
2. Extract expression strings (value, condition, etc.)
3. **Call ExpressionParser** to convert strings → AST
4. Store AST in `CommandNode.value_ast`, `CommandNode.condition_ast`, etc.

### Stage 3: Type Checking
**Location:** `TypeChecker.check()`
**Input:** AST from parser
**Output:** Type-annotated AST

**Validates:**
- Path references exist (bar.*, vfs.*)
- Types match (e.g., condition must be bool)
- No undefined variables

### Stage 4: Catalog Assembly
**Location:** `EffectCatalog.from_config()`
**Input:** Compiled `CommandNode` trees
**Output:** `EffectCatalog` artifact

**Stores:**
- Effect definitions with compiled commands
- Pre-compiled ASTs (not expression strings!)
- Reapply policies, durations, metadata

### Stage 5: Runtime Execution
**Location:** `CommandExecutor.execute()`
**Input:** `CommandNode` from catalog
**Runtime:** Evaluates pre-compiled ASTs (no parsing!)

**Flow:**
```
YAML → DTO → CommandNode (AST) → Catalog → Runtime (Evaluate AST)
```

## Code References

- Entry point: `src/townlet/universe/compiler.py:_compile_effects_catalog()`
- Command compiler: `src/townlet/effects/compiler.py`
- Expression parser: `src/townlet/world/expression/parser.py`
- Type checker: `src/townlet/world/expression/type_checker.py`
- Catalog: `src/townlet/effects/catalog.py`
- Runtime: `src/townlet/effects/executor.py`
```

## Acceptance Criteria

**Option A (Integration Test):**
- [ ] Test file created with end-to-end compilation tests
- [ ] Tests verify YAML → Catalog → AST flow
- [ ] Tests verify ASTs pre-compiled (not runtime parsing)
- [ ] Tests verify error reporting includes context
- [ ] All tests pass

**Option B (Documentation):**
- [ ] Flow document created showing pipeline stages
- [ ] Each stage documented (input, output, operations)
- [ ] Code references provided for each stage
- [ ] Diagram showing YAML → DTO → AST → Catalog → Runtime

**Both Options:**
- [ ] Can verify how command compilation works
- [ ] Integration between parser and compiler clear
- [ ] Pre-compilation verified (ASTs not strings in catalog)

## Evidence

**Source Report:** gap-report-compiler.md (COMP-11 section)
**Implementation Files:**
- `src/townlet/effects/parser.py` (exists)
- `src/townlet/effects/compiler.py` (exists)
- `src/townlet/universe/compiler.py` (calls effects compilation)

**Current Tests:**
- `tests/test_townlet/unit/effects/test_command_parser.py` (unit)
- `tests/test_townlet/unit/effects/test_command_compiler.py` (unit)
- **Missing:** Integration test showing full flow

## Implementation Notes

**Recommendation:** Option A (integration test)
- Tests serve as executable documentation
- Verifies integration actually works
- Catches integration bugs
- Can be run in CI

**Key Integration Points to Test:**
1. YAML string → DTO (Pydantic)
2. DTO → CommandNode (parser)
3. Expression string → AST (ExpressionParser)
4. AST → Type-checked AST (TypeChecker)
5. CommandNode → Catalog (assembly)
6. Catalog → Runtime (execution uses AST, not string)

## References

- Implementation: `src/townlet/effects/` (parser, compiler, catalog, executor)
- Compiler integration: `src/townlet/universe/compiler.py:_compile_effects_catalog()`
- Example integration test: `tests/test_townlet/integration/test_effects_compiled_catalog.py`
- Pattern: Similar to VFS profile compilation integration tests
