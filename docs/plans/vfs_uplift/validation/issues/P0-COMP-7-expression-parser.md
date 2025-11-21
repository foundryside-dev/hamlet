# [COMP-7] Expression Parser

**Priority:** P0 (Critical)
**Category:** Compiler
**Status:** DONE
**Effort:** 1 day

## Description

Full expression parser is missing. Currently using string-based workaround that is not scalable for complex expressions. Parser is needed to convert expression strings into Abstract Syntax Trees (AST) for type checking, optimization, and complex expression support.

## Current State

String-based expression evaluation exists in VFS evaluator and works for simple expressions:
- Basic arithmetic (add, subtract, multiply, divide)
- Comparisons (eq, gt, lt, gte, lte)
- Basic functions (clamp, lerp, etc.)
- Current L0-L3 configs use only simple expressions that work with existing evaluator

**Workaround functional:** All Phase 1-3 curriculum levels work correctly with current string-based evaluation.

## Required Implementation

Create `src/townlet/world/expression/` module with:

1. **Lexer/Tokenizer:**
   - Token types: NUMBER, STRING, IDENTIFIER, OPERATOR, LPAREN, RPAREN, etc.
   - Tokenize expression strings for parsing

2. **Recursive Descent Parser:**
   - Parse tokens into AST nodes
   - Support operator precedence
   - Handle function calls, path notation (dot-access)
   - 80-120 lines estimated

3. **AST Construction:**
   - Build tree structure from tokens
   - Link to AST node types (COMP-8)

4. **Error Handling:**
   - Syntax errors with line/column information
   - Clear error messages for invalid expressions

## Acceptance Criteria

- [ ] Lexer tokenizes all expression operators and literals
- [ ] Parser builds valid AST from expression strings
- [ ] Parser handles operator precedence correctly
- [ ] Parser supports function calls with multiple arguments
- [ ] Parser supports path notation (agent.vfs.energy, target.bar.health)
- [ ] Syntax errors provide clear messages with positions
- [ ] All L0-L3 config expressions parse successfully
- [ ] 20+ parser tests (valid expressions, syntax errors, edge cases)

## Evidence

**Source Report:** gap-report-final.md (lines 27-50), gap-report-compiler.md
**Related Requirements:** COMP-8 (AST node types), COMP-9 (type checker)
**Current Workaround:** String-based evaluation in `src/townlet/vfs/evaluator.py`
**Test Coverage:** `tests/test_townlet/unit/world/expression/test_parser.py`

## Implementation Notes

**Dependencies:**
- Must be completed before COMP-8 (AST nodes) and COMP-9 (type checker)
- Parser output becomes input to type checker
- Refactor VFSEvaluator to consume AST instead of strings

**Risk Level:** Low for Phase 1-3 (workaround functional), Medium for Phase 4+ (complex expressions needed)

**Priority Justification:** Marked P0 because it's foundational infrastructure, but merge is not blocked since workaround functions correctly for current curriculum levels. Should be completed immediately post-merge as P0 backlog item.

## References

- Implementation location: `src/townlet/world/expression/parser.py` (to be created)
- Test file: `tests/test_townlet/unit/world/test_expression_parser.py` (to be created)
- Related: Expression language design in VFS uplift plans
