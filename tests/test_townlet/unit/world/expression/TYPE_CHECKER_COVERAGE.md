# Type Checker Test Coverage Map

This maps `TypeChecker` rules (`src/townlet/world/expression/type_checker.py`) to existing tests. Unimplemented features (function calls, index access) are skipped in the codebase and tests.

## Type Inference (Constants)
- `int`/`float`/`bool`/`str` literals → `tests/test_townlet/unit/world/expression/test_type_checker.py::TestConstantInference`

## Path & Variable Resolution
- Variables in schema, unknown variable error → `test_type_checker.py::TestVariable`
- Path access success/error → `test_type_checker.py::TestPathAccess`

## Binary Operators
- Arithmetic (numeric only, float promotion) → `test_type_checker.py::TestBinaryOperators::test_type_check_arithmetic_operators`
- Comparison returns bool, numeric-only enforcement → `test_type_checker.py::TestBinaryOperators::test_type_check_comparison_operators`
- Logical bool-only → `test_type_checker.py::TestBinaryOperators::test_type_check_logical_operators`
- Incompatible operands error → `test_type_checker.py::TestBinaryOperators::test_type_check_incompatible_operands`

## Unary Operators
- Negation numeric-only, NOT bool-only, error cases → `test_type_checker.py::TestUnaryOperators`

## Conditionals
- If/then/else: condition must be bool, branches must match → `test_type_checker.py::TestIntegration::test_type_check_if_then_else`, `test_type_checker.py::test_type_check_if_non_bool_condition`, `test_type_checker.py::test_type_check_if_mismatched_branches`

## Integration (Parse → Type Check → Evaluate)
- Happy paths for arithmetic/comparison/logical/unary → `tests/test_townlet/unit/world/expression/test_integration.py` (multiple tests)
- Schema miss error surfaced from type checker → `test_integration.py::test_pipeline_type_error_detection`

## Not Implemented (by design)
- FunctionCall type checking is `NotImplementedError` (Phase 2) → no tests
- IndexAccess type checking is `NotImplementedError` (Phase 4) → no tests

## Coverage Status
- Implemented rules have direct tests (see above).
- Unimplemented rules are explicitly skipped; no gaps in implemented surface.
