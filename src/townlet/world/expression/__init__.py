"""HAMLET Expression Language - Abstract Syntax Tree Node Types.

This module provides the core AST node types for the HAMLET Expression Language,
used throughout the VFS (Variable & Feature System), Effects system, and Items system.

The AST uses the Visitor pattern to separate traversal logic (type checking,
evaluation, pretty printing) from node structure.

Public API:
    - OperatorType: Enum of supported operators (arithmetic, logical, comparison)
    - ASTNode: Base class for all AST nodes
    - ASTVisitor: Visitor pattern interface
    - Constant: Literal values (numbers, booleans, strings)
    - Variable: Simple identifier references
    - PathAccess: Dot-notation nested state access
    - BinaryOp: Binary operations (infix)
    - UnaryOp: Unary operations (prefix)
    - FunctionCall: Function invocation
    - IfThenElse: Conditional expressions (ternary)
    - IndexAccess: Array/list element access
"""

from townlet.world.expression.ast_nodes import (
    ASTNode,
    ASTVisitor,
    BinaryOp,
    Constant,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
    PathAccess,
    UnaryOp,
    Variable,
)

__all__ = [
    "ASTNode",
    "ASTVisitor",
    "BinaryOp",
    "Constant",
    "FunctionCall",
    "IfThenElse",
    "IndexAccess",
    "OperatorType",
    "PathAccess",
    "UnaryOp",
    "Variable",
]
