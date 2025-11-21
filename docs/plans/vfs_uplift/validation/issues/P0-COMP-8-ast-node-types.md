# [COMP-8] AST Node Types

**Priority:** P0 (Critical)
**Category:** Compiler
**Status:** MISSING
**Effort:** 0.5 day

## Description

AST (Abstract Syntax Tree) node type definitions are missing. Need dataclass definitions for all expression AST nodes to represent parsed expressions in tree structure. These node types are the foundation for type checking and optimization.

## Current State

No AST node types exist. Parser (COMP-7) and type checker (COMP-9) cannot be implemented without these foundational types.

String-based evaluation workaround bypasses need for AST, but blocks advanced features:
- Type checking at compile time
- Expression optimization
- Complex nested expressions
- Reference type traversal

## Required Implementation

Create `src/townlet/world/expression/ast_nodes.py` with dataclass definitions:

1. **Base Node:**
   - `ASTNode` (abstract base class)
   - Fields: line, column, type annotation

2. **Literal Nodes:**
   - `LiteralNode` (numbers, strings, booleans)
   - `VarRefNode` (variable references)
   - `PathNode` (dot-notation paths like agent.vfs.energy)

3. **Operator Nodes:**
   - `BinaryOpNode` (add, sub, mul, div, comparisons)
   - `UnaryOpNode` (neg, not)
   - `FunctionCallNode` (clamp, lerp, max, min, etc.)

4. **Control Flow Nodes (future):**
   - `IfNode` (conditional expressions)
   - `ForEachNode` (iteration expressions)

Estimated: 40-60 lines of dataclass definitions

## Acceptance Criteria

- [ ] Base `ASTNode` class with common fields (line, column, type)
- [ ] `LiteralNode` for number/string/boolean literals
- [ ] `VarRefNode` for variable references
- [ ] `PathNode` for dot-notation path expressions
- [ ] `BinaryOpNode` for binary operators with precedence
- [ ] `UnaryOpNode` for unary operators
- [ ] `FunctionCallNode` for function calls with args
- [ ] All nodes are immutable dataclasses
- [ ] Type hints on all fields
- [ ] 10+ unit tests for node construction and validation

## Evidence

**Source Report:** gap-report-final.md (lines 27-50), gap-report-compiler.md
**Related Requirements:** COMP-7 (parser), COMP-9 (type checker)

## Implementation Notes

**Design Pattern:** Immutable dataclasses for functional-style AST manipulation

**Dependencies:**
- Required by COMP-7 (parser returns AST nodes)
- Required by COMP-9 (type checker walks AST nodes)
- Should be implemented second (after parser skeleton, before full type checker)

**Node Structure Example:**
```python
@dataclass(frozen=True)
class BinaryOpNode(ASTNode):
    operator: str  # "+", "-", "*", "/", "==", etc.
    left: ASTNode
    right: ASTNode
    line: int
    column: int
    type_annotation: Optional[str] = None
```

**Priority Justification:** Foundational type system for expression language. Blocks COMP-9 (type checker) and advanced expression features. Part of P0 expression language foundation that should be completed immediately post-merge.

## References

- Implementation location: `src/townlet/world/expression/ast_nodes.py` (to be created)
- Test file: `tests/test_townlet/unit/world/test_ast_nodes.py` (to be created)
- Related: Expression language design in VFS uplift plans
