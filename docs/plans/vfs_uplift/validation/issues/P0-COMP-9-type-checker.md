# [COMP-9] Type Checker

**Priority:** P0 (Critical)
**Category:** Compiler
**Status:** MISSING
**Effort:** 1 day

## Description

Expression type checker is missing. Need compile-time type validation to catch type errors (adding string to number, invalid function arguments, undefined variables) before runtime. Without type checker, invalid expressions fail at runtime rather than at config load time.

## Current State

No type checking exists. String-based evaluator discovers type errors at runtime when expressions are evaluated. This causes:
- Runtime type errors that could be caught at compile time
- Poor error messages (stack traces instead of clear validation messages)
- No validation of variable references (undefined variables fail at runtime)
- No validation of function signatures (wrong argument types/counts fail at runtime)

**Current risk:** Low for Phase 1-3 (simple expressions, well-tested configs), Medium for Phase 4+ (complex expressions with more opportunities for errors)

## Required Implementation

Create `src/townlet/world/expression/type_checker.py` with:

1. **Type Inference:**
   - Walk AST and infer types for all nodes
   - Support basic types: int, float, bool, string
   - Support VFS types: vector3, agent_ref, item_ref (future)

2. **Type Validation:**
   - Binary operators: validate operand types (number + number, not number + string)
   - Function calls: validate argument types match signatures
   - Variable references: validate variables exist in VFS schema
   - Path expressions: validate paths are valid (agent.vfs.energy exists)

3. **Error Reporting:**
   - Clear type mismatch errors with expression context
   - Undefined variable errors with suggestions
   - Invalid function signature errors with expected types

4. **Integration:**
   - Called during Universe Compiler stage 4 (cross-validation)
   - Type check all VFS variable expressions
   - Type check all effect command expressions

Estimated: 100-150 lines

## Acceptance Criteria

- [ ] Type checker walks AST and infers types for all nodes
- [ ] Binary operator type validation (e.g., reject "hello" + 5)
- [ ] Function call signature validation (arg types and count)
- [ ] Variable reference validation (undefined variables caught)
- [ ] Path expression validation (invalid paths caught)
- [ ] Clear error messages with expression context
- [ ] Integration point in UniverseCompiler stage 4
- [ ] Type check all VFS variable expressions during compilation
- [ ] 30+ type checker tests (valid expressions, type mismatches, edge cases)
- [ ] All L0-L3 configs pass type checking

## Evidence

**Source Report:** gap-report-final.md (lines 27-50), gap-report-compiler.md
**Related Requirements:** COMP-7 (parser), COMP-8 (AST nodes), COMP-17 (profile validation)

## Implementation Notes

**Algorithm:** Single-pass recursive AST visitor with symbol table lookup

**Type Rules:**
- Arithmetic ops (+, -, *, /): require number operands, return number
- Comparison ops (==, <, >): require same types, return bool
- Boolean ops (and, or): require bool operands, return bool
- Functions: each function has explicit signature (see expression language spec)

**Symbol Table Integration:**
- Type checker needs access to VFS schema (variable types)
- Need reference to compiled_vfs_profiles for type lookups
- Path expressions resolve against profile schemas

**Error Quality Examples:**
```
TypeError at line 3, column 12: Cannot add 'string' and 'int'
  Expression: "vfs:player_name + 5"
              ~~~~~~~~~~~~~~~~~~~~^

ReferenceError at line 5: Undefined variable 'player_energyy'
  Did you mean: 'player_energy'?
```

**Priority Justification:** Part of P0 expression language foundation. Prevents entire class of runtime errors by catching them at compile time. Should be completed immediately post-merge as P0 backlog item.

## References

- Implementation location: `src/townlet/world/expression/type_checker.py` (to be created)
- Test file: `tests/test_townlet/unit/world/test_type_checker.py` (to be created)
- Integration point: `src/townlet/universe/compiler.py` stage 4 (cross-validation)
- Related: Expression language type system in VFS uplift plans
