# [COMP-9] Type Checker Test Breakdown Clarity

**Priority:** P1 (Important)
**Category:** Testing/Documentation
**Status:** PARTIAL
**Effort:** 2-3 hours

## Description

Type checker implementation is complete and functional, but test breakdown is unclear. Gap analysis couldn't verify systematic coverage of all type checking rules due to test organization. Need to reorganize or document tests to clearly show coverage of type system features.

## Current State

**Implementation:** ✅ COMPLETE
- File: `src/townlet/world/expression/type_checker.py`
- Features: Type inference, unification, error reporting
- All type checking functionality working

**Test Coverage:** ⚠️ UNCLEAR
- Tests exist in expression test suite (116 total)
- Type checking tested but not clearly organized
- Can't easily verify coverage of specific type rules
- Test breakdown by feature unclear

**Issues:**
- Which tests cover type inference?
- Which tests cover type errors?
- Which tests cover implicit conversions?
- Are all type rules systematically tested?

## Required Implementation

### Option A: Reorganize Tests (Recommended - 2-3 hours)

Create dedicated type checker test file with clear organization:

**File:** `tests/test_townlet/unit/world/expression/test_type_checker.py`

**Structure:**
```python
"""Dedicated tests for expression type checker."""

import pytest
from townlet.world.expression.type_checker import TypeChecker, TypeCheckError


class TestTypeInference:
    """Tests for type inference rules."""

    def test_infer_int_literal(self):
        """Literal integers infer to int type."""
        # ...

    def test_infer_float_literal(self):
        """Literal floats infer to float type."""
        # ...

    def test_infer_bool_literal(self):
        """Literal booleans infer to bool type."""
        # ...

    def test_infer_arithmetic_expression(self):
        """Arithmetic expressions infer based on operand types."""
        # int + int → int
        # float + float → float
        # int + float → float
        # ...

    def test_infer_comparison_expression(self):
        """Comparison expressions always infer to bool."""
        # ...

    def test_infer_logical_expression(self):
        """Logical expressions always infer to bool."""
        # ...


class TestTypeUnification:
    """Tests for type unification (implicit conversions)."""

    def test_int_to_float_conversion(self):
        """int can unify with float (implicit conversion)."""
        # bar.energy * 10 (where energy is float, 10 is int)
        # ...

    def test_bool_does_not_unify_with_numeric(self):
        """bool cannot unify with int or float."""
        # bar.energy and bar.health → TYPE ERROR
        # ...

    def test_list_element_type_unification(self):
        """List elements must have compatible types."""
        # ...


class TestTypeErrors:
    """Tests for type error detection and reporting."""

    def test_type_mismatch_arithmetic(self):
        """Detect type mismatch in arithmetic."""
        # bar.energy + true → TYPE ERROR
        # ...

    def test_type_mismatch_comparison(self):
        """Detect invalid comparison operands."""
        # "string" < 5 → TYPE ERROR (if strings supported)
        # ...

    def test_type_mismatch_function_argument(self):
        """Detect argument type mismatch."""
        # abs("not a number") → TYPE ERROR
        # ...

    def test_undefined_variable_error(self):
        """Detect references to undefined variables."""
        # vfs:nonexistent → ERROR
        # ...


class TestPathTypeResolution:
    """Tests for path access type resolution."""

    def test_bar_path_resolves_to_float(self):
        """bar.* paths resolve to float type."""
        # ...

    def test_vfs_path_resolves_to_declared_type(self):
        """vfs.* paths resolve based on variable definition."""
        # ...

    def test_temporal_path_types(self):
        """temporal.* paths resolve to correct types."""
        # temporal.hour → int
        # temporal.day_progress → float
        # ...


class TestErrorMessages:
    """Tests for type error message quality."""

    def test_error_message_includes_types(self):
        """Error messages show expected and actual types."""
        # ...

    def test_error_message_includes_location(self):
        """Error messages show expression location."""
        # ...

    def test_error_suggests_fix_for_common_mistakes(self):
        """Error messages suggest fixes."""
        # "Did you mean to compare? Use bar.energy > 0 instead of bar.energy"
        # ...
```

**Coverage Target:**
- 20-25 dedicated type checker tests
- Clear organization by feature
- Systematic coverage of type rules

### Option B: Document Existing Tests (Faster - 1 hour)

If tests already exist but are scattered, create documentation:

**File:** `tests/test_townlet/unit/world/expression/TYPE_CHECKER_COVERAGE.md`

**Contents:**
```markdown
# Type Checker Test Coverage Map

This document maps type checker features to existing tests.

## Type Inference

| Feature | Test File | Test Name |
|---------|-----------|-----------|
| Int literal inference | test_expression_integration.py | test_parse_int_literal |
| Float literal inference | test_expression_integration.py | test_parse_float_literal |
| [... etc ...]

## Type Unification

| Feature | Test File | Test Name |
|---------|-----------|-----------|
| int → float | test_expression_integration.py | test_mixed_arithmetic |
| [... etc ...]

## Type Errors

| Error Type | Test File | Test Name |
|-----------|-----------|-----------|
| Type mismatch | test_vfs_expression_edge_cases.py | test_type_error_detection |
| [... etc ...]

## Coverage Gaps

- [ ] Explicit test for list type unification
- [ ] Explicit test for function argument type checking
- [ ] Error message quality tests
```

## Acceptance Criteria

**Option A (Reorganize):**
- [ ] New test file created: test_type_checker.py
- [ ] 20-25 tests organized by feature
- [ ] All type checking rules covered
- [ ] Tests pass and integrate with existing suite
- [ ] Clear docstrings explaining each test

**Option B (Document):**
- [ ] Coverage map document created
- [ ] All existing type checker tests mapped
- [ ] Coverage gaps identified
- [ ] Gaps filled with new tests (if any)

**Both Options:**
- [ ] Can verify type system coverage from tests
- [ ] Type inference systematically tested
- [ ] Type errors systematically tested
- [ ] Implicit conversions tested

## Evidence

**Source Report:** gap-report-compiler.md (COMP-9 section)
**Implementation:** src/townlet/world/expression/type_checker.py (complete)
**Current Tests:** Scattered across 116 expression tests
**Need:** Clear breakdown showing systematic coverage

## Implementation Notes

**Recommendation:** Option A (reorganize)
- Better long-term maintainability
- Makes type system rules explicit
- Easier to verify coverage
- Serves as documentation

**Test Organization Philosophy:**
- One test file per major component
- One test class per feature
- Clear descriptive test names
- Tests serve as specification

**Type System Rules to Test:**
1. Type inference for literals
2. Type inference for operators
3. Type inference for function calls
4. Type inference for path access
5. Implicit conversions (int → float)
6. Forbidden conversions (bool ↔ numeric)
7. Type error detection
8. Error message quality

## References

- Implementation: `src/townlet/world/expression/type_checker.py`
- Existing tests: `tests/test_townlet/unit/universe/test_vfs_expression_schema.py`
- Integration tests: `tests/test_townlet/integration/test_vfs_expression_edge_cases.py`
- Pattern: `tests/test_townlet/unit/effects/test_command_executor.py` (clear test organization)
