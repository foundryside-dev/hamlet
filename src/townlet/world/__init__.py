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
        FunctionCall, IfThenElse, IndexAccess, Switch, Reduce - Complex expressions

    Runtime:
        ExecutionContext - Evaluation context with state access

    Types:
        ScalarType, BoolType - Primitive type validators
        Vec2Type, Vec3Type, Vec4Type - Vector type validators

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
    TypeChecker,
    TypeCheckError,
    UnaryOp,
    Variable,
)

# Type system
from townlet.world.types import (
    BoolType,
    ScalarType,
    Type,
    Vec2Type,
    Vec3Type,
    Vec4Type,
)

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
    "Type",
    "ScalarType",
    "BoolType",
    "Vec2Type",
    "Vec3Type",
    "Vec4Type",
]
