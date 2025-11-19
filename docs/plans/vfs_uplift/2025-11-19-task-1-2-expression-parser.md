# Task 1.2: Expression Parser - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a parser using pyparsing that converts expression strings into AST nodes.

**Architecture:** Recursive descent parser using pyparsing library. Handles operator precedence, both infix and functional syntax. Produces AST nodes from Task 1.1.

**Tech Stack:** pyparsing 3.1+, Python 3.11+

**Dependencies:** Task 1.1 (AST Nodes) must be complete

**References:**
- pyparsing docs: https://pyparsing-docs.readthedocs.io/
- Operator precedence: Standard mathematical precedence
- VARIABLE_SUBSYSTEM.md: Function library specification

---

## Task Breakdown

### Step 1: Add pyparsing dependency

**File:** `pyproject.toml` (modify)

Find the `[project.dependencies]` section and add:
```toml
[project.dependencies]
# ... existing dependencies ...
pyparsing = "^3.1.0"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv sync
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "import pyparsing; print(pyparsing.__version__)"
```

**Expected:** Prints version >= 3.1.0

**Commit:**
```bash
git add pyproject.toml
git commit -m "deps: add pyparsing for expression parsing"
```

---

### Step 2: Write failing test for parsing constants

**File:** `tests/test_townlet/unit/world/expression/test_parser.py`

```python
"""Tests for expression parser."""
import pytest
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression import Constant


def test_parse_float_constant():
    """Parser converts float strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse("0.05")

    assert isinstance(result, Constant)
    assert result.value == 0.05
    assert isinstance(result.value, float)


def test_parse_integer_constant():
    """Parser converts integer strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse("42")

    assert isinstance(result, Constant)
    assert result.value == 42
    assert isinstance(result.value, int)


def test_parse_boolean_true():
    """Parser converts 'true' to Constant(True)."""
    parser = ExpressionParser()
    result = parser.parse("true")

    assert isinstance(result, Constant)
    assert result.value is True


def test_parse_boolean_false():
    """Parser converts 'false' to Constant(False)."""
    parser = ExpressionParser()
    result = parser.parse("false")

    assert isinstance(result, Constant)
    assert result.value is False


def test_parse_string_constant():
    """Parser converts quoted strings to Constant nodes."""
    parser = ExpressionParser()
    result = parser.parse('"energy"')

    assert isinstance(result, Constant)
    assert result.value == "energy"
    assert isinstance(result.value, str)


def test_parse_string_with_single_quotes():
    """Parser supports single-quoted strings."""
    parser = ExpressionParser()
    result = parser.parse("'Fridge'")

    assert isinstance(result, Constant)
    assert result.value == "Fridge"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_float_constant -v
```

**Expected:** FAIL - Module 'townlet.world.expression.parser' not found

---

### Step 3: Implement parser skeleton and constant parsing

**File:** `src/townlet/world/expression/parser.py`

```python
"""Expression parser using pyparsing."""
from pyparsing import (
    Literal,
    Word,
    alphas,
    alphanums,
    nums,
    QuotedString,
    pyparsing_common,
    ParserElement,
)
from townlet.world.expression import (
    ASTNode,
    Constant,
    Variable,
    PathAccess,
    BinaryOp,
    UnaryOp,
    FunctionCall,
    IfThenElse,
    IndexAccess,
    OperatorType,
)


# Enable packrat parsing for performance
ParserElement.enablePackrat()


class ExpressionParser:
    """Parser for HAMLET Expression Language.

    Converts expression strings into AST nodes using pyparsing.

    Examples:
        >>> parser = ExpressionParser()
        >>> parser.parse("0.05")
        Constant(value=0.05)
        >>> parser.parse("a + b")
        BinaryOp(left=Variable("a"), op=ADD, right=Variable("b"))
    """

    def __init__(self):
        """Initialize parser with grammar rules."""
        self._build_grammar()

    def _build_grammar(self):
        """Build pyparsing grammar for expression language."""

        # Literals
        # Boolean literals (must come before identifiers)
        true_literal = Literal("true").setParseAction(lambda: Constant(value=True))
        false_literal = Literal("false").setParseAction(lambda: Constant(value=False))
        bool_literal = true_literal | false_literal

        # Numeric literals
        float_literal = pyparsing_common.fnumber().setParseAction(
            lambda tokens: Constant(value=float(tokens[0]))
        )
        int_literal = pyparsing_common.signed_integer().setParseAction(
            lambda tokens: Constant(value=int(tokens[0]))
        )
        # Try float first (includes integers like "42.0")
        numeric_literal = float_literal | int_literal

        # String literals (double or single quotes)
        string_literal = (
            QuotedString('"', escChar="\\")
            | QuotedString("'", escChar="\\")
        ).setParseAction(lambda tokens: Constant(value=str(tokens[0])))

        # Combine all constants
        constant = bool_literal | numeric_literal | string_literal

        # For now, expression is just constants
        # We'll add more in subsequent steps
        self.expression = constant

    def parse(self, text: str) -> ASTNode:
        """Parse expression string into AST.

        Args:
            text: Expression string to parse

        Returns:
            AST node representing the expression

        Raises:
            ParseException: If text is not a valid expression
        """
        result = self.expression.parseString(text, parseAll=True)
        return result[0]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse" -v
```

**Expected:** All 6 constant tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add parser skeleton with constant parsing"
```

---

### Step 4: Write failing tests for variable parsing

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
from townlet.world.expression import Variable


def test_parse_simple_variable():
    """Parser converts identifiers to Variable nodes."""
    parser = ExpressionParser()
    result = parser.parse("intensity")

    assert isinstance(result, Variable)
    assert result.name == "intensity"


def test_parse_variable_with_underscore():
    """Parser supports underscores in variable names."""
    parser = ExpressionParser()
    result = parser.parse("slot_index")

    assert isinstance(result, Variable)
    assert result.name == "slot_index"


def test_parse_variable_with_numbers():
    """Parser supports numbers in variable names (not at start)."""
    parser = ExpressionParser()
    result = parser.parse("var123")

    assert isinstance(result, Variable)
    assert result.name == "var123"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_simple_variable -v
```

**Expected:** FAIL - Parses as Constant instead of Variable (or parse error)

---

### Step 5: Implement variable parsing

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Replace the line `self.expression = constant` with:

```python
        # Variables (identifiers)
        # Must not match keywords (true, false, and, or, not, if, then, else)
        keywords = {"true", "false", "and", "or", "not", "if", "then", "else"}
        identifier = Word(alphas + "_", alphanums + "_")

        def make_variable(tokens):
            name = tokens[0]
            if name in keywords:
                # This shouldn't happen due to grammar ordering,
                # but guard against it
                raise ValueError(f"Cannot use keyword '{name}' as variable")
            return Variable(name=name)

        variable = identifier.copy().setParseAction(make_variable)

        # Primary expressions (atoms)
        primary = constant | variable

        # For now, expression is primary
        # We'll add operators in subsequent steps
        self.expression = primary
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_variable" -v
```

**Expected:** All 3 variable tests PASS

**Also verify constants still work:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_float_constant" -v
```

**Expected:** PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add variable parsing with keyword exclusion"
```

---

### Step 6: Write failing tests for path access

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
from townlet.world.expression import PathAccess


def test_parse_path_access_two_segments():
    """Parser converts dotted paths to PathAccess nodes."""
    parser = ExpressionParser()
    result = parser.parse("self.position")

    assert isinstance(result, PathAccess)
    assert result.segments == ["self", "position"]


def test_parse_path_access_three_segments():
    """Parser handles multi-segment paths."""
    parser = ExpressionParser()
    result = parser.parse("target.bar.energy")

    assert isinstance(result, PathAccess)
    assert result.segments == ["target", "bar", "energy"]


def test_parse_path_access_deep():
    """Parser handles deeply nested paths."""
    parser = ExpressionParser()
    result = parser.parse("global.vfs.agent.is_night")

    assert isinstance(result, PathAccess)
    assert result.segments == ["global", "vfs", "agent", "is_night"]
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_path_access_two_segments -v
```

**Expected:** FAIL - Parses as Variable("self") only

---

### Step 7: Implement path access parsing

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Replace the `primary` definition with:

```python
        # Path access (dotted notation)
        # target.bar.energy → ["target", "bar", "energy"]
        def make_path_access(tokens):
            segments = [str(t) for t in tokens]
            if len(segments) == 1:
                # Single identifier is a Variable, not PathAccess
                return Variable(name=segments[0])
            return PathAccess(segments=segments)

        path_or_variable = identifier + (Literal(".").suppress() + identifier)[...].setParseAction(
            lambda tokens: tokens.asList()
        )
        path_or_variable.setParseAction(make_path_access)

        # Primary expressions (atoms)
        primary = constant | path_or_variable
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_path" -v
```

**Expected:** All 3 path tests PASS

**Also verify variables still work:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_simple_variable -v
```

**Expected:** PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add path access parsing (dotted notation)"
```

---

### Step 8: Write failing tests for binary operators

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
from townlet.world.expression import BinaryOp, OperatorType


def test_parse_addition():
    """Parser handles infix addition."""
    parser = ExpressionParser()
    result = parser.parse("a + b")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.ADD
    assert isinstance(result.left, Variable)
    assert result.left.name == "a"
    assert isinstance(result.right, Variable)
    assert result.right.name == "b"


def test_parse_multiplication():
    """Parser handles infix multiplication."""
    parser = ExpressionParser()
    result = parser.parse("x * y")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.MUL


def test_parse_comparison():
    """Parser handles comparison operators."""
    parser = ExpressionParser()
    result = parser.parse("x > 10")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.GT
    assert isinstance(result.left, Variable)
    assert isinstance(result.right, Constant)
    assert result.right.value == 10


def test_parse_logical_and():
    """Parser handles logical operators."""
    parser = ExpressionParser()
    result = parser.parse("a and b")

    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.AND


def test_parse_operator_precedence():
    """Parser respects operator precedence (PEMDAS)."""
    parser = ExpressionParser()
    result = parser.parse("a + b * c")

    # Should parse as: a + (b * c)
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.ADD
    assert isinstance(result.left, Variable)
    assert result.left.name == "a"

    # Right side should be multiplication
    assert isinstance(result.right, BinaryOp)
    assert result.right.op == OperatorType.MUL
    assert result.right.left.name == "b"
    assert result.right.right.name == "c"


def test_parse_parentheses_override_precedence():
    """Parser respects parentheses for precedence override."""
    parser = ExpressionParser()
    result = parser.parse("(a + b) * c")

    # Should parse as: (a + b) * c
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.MUL

    # Left side should be addition
    assert isinstance(result.left, BinaryOp)
    assert result.left.op == OperatorType.ADD
    assert result.left.left.name == "a"
    assert result.left.right.name == "b"

    assert isinstance(result.right, Variable)
    assert result.right.name == "c"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_addition -v
```

**Expected:** FAIL - Binary operators not recognized

---

### Step 9: Implement binary operator parsing with precedence

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Add after `primary` definition and before `self.expression`:

```python
        # Import for precedence helpers
        from pyparsing import infixNotation, opAssoc, Suppress

        # Parentheses for grouping
        lparen = Suppress("(")
        rparen = Suppress(")")

        # Operator precedence (lowest to highest)
        # Level 1: Logical OR
        # Level 2: Logical AND
        # Level 3: Comparisons
        # Level 4: Addition, Subtraction
        # Level 5: Multiplication, Division, Modulo
        # Level 6: Exponentiation (right-associative)

        def make_binary_op(op_type):
            """Factory for creating binary op parse actions."""
            def action(tokens):
                result = tokens[0][0]
                for i in range(1, len(tokens[0]), 2):
                    op = tokens[0][i]
                    right = tokens[0][i + 1]
                    result = BinaryOp(left=result, op=op_type, right=right)
                return result
            return action

        # Define operator symbols
        add_op = Literal("+")
        sub_op = Literal("-")
        mul_op = Literal("*")
        div_op = Literal("/")
        mod_op = Literal("%")
        pow_op = Literal("**")

        eq_op = Literal("==")
        neq_op = Literal("!=")
        lte_op = Literal("<=")
        gte_op = Literal(">=")
        lt_op = Literal("<")
        gt_op = Literal(">")

        and_op = Literal("and")
        or_op = Literal("or")

        # Build expression with operator precedence using infixNotation
        expression_with_ops = infixNotation(
            primary,
            [
                # Level 6: Exponentiation (right-associative)
                (pow_op, 2, opAssoc.RIGHT, make_binary_op(OperatorType.POW)),

                # Level 5: Multiplication, Division, Modulo
                (
                    mul_op | div_op | mod_op,
                    2,
                    opAssoc.LEFT,
                    lambda tokens: make_binary_op(
                        {
                            "*": OperatorType.MUL,
                            "/": OperatorType.DIV,
                            "%": OperatorType.MOD,
                        }[tokens[0][1]]
                    )(tokens),
                ),

                # Level 4: Addition, Subtraction
                (
                    add_op | sub_op,
                    2,
                    opAssoc.LEFT,
                    lambda tokens: make_binary_op(
                        {"+"  : OperatorType.ADD, "-": OperatorType.SUB}[
                            tokens[0][1]
                        ]
                    )(tokens),
                ),

                # Level 3: Comparisons
                (
                    eq_op | neq_op | lte_op | gte_op | lt_op | gt_op,
                    2,
                    opAssoc.LEFT,
                    lambda tokens: make_binary_op(
                        {
                            "==": OperatorType.EQ,
                            "!=": OperatorType.NEQ,
                            "<=": OperatorType.LTE,
                            ">=": OperatorType.GTE,
                            "<": OperatorType.LT,
                            ">": OperatorType.GT,
                        }[tokens[0][1]]
                    )(tokens),
                ),

                # Level 2: Logical AND
                (and_op, 2, opAssoc.LEFT, make_binary_op(OperatorType.AND)),

                # Level 1: Logical OR
                (or_op, 2, opAssoc.LEFT, make_binary_op(OperatorType.OR)),
            ],
        )

        self.expression = expression_with_ops
```

**Note:** The operator parse action logic above is complex. Let me simplify it:

**Replace the infixNotation section with:**

```python
        # Helper to make binary ops
        def make_binop(tokens):
            """Convert infix tokens to BinaryOp AST nodes."""
            result = tokens[0][0]
            i = 1
            while i < len(tokens[0]):
                op_str = tokens[0][i]
                right = tokens[0][i + 1]

                # Map operator string to OperatorType
                op_map = {
                    "+": OperatorType.ADD,
                    "-": OperatorType.SUB,
                    "*": OperatorType.MUL,
                    "/": OperatorType.DIV,
                    "%": OperatorType.MOD,
                    "**": OperatorType.POW,
                    "==": OperatorType.EQ,
                    "!=": OperatorType.NEQ,
                    "<": OperatorType.LT,
                    ">": OperatorType.GT,
                    "<=": OperatorType.LTE,
                    ">=": OperatorType.GTE,
                    "and": OperatorType.AND,
                    "or": OperatorType.OR,
                }

                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown operator: {op_str}")

                result = BinaryOp(left=result, op=op_type, right=right)
                i += 2

            return result

        # Build expression with operator precedence
        from pyparsing import infixNotation, opAssoc

        expression_with_ops = infixNotation(
            primary,
            [
                # Level 6: Exponentiation (right-associative)
                (Literal("**"), 2, opAssoc.RIGHT, make_binop),

                # Level 5: Multiplication, Division, Modulo (left-associative)
                (Literal("*") | Literal("/") | Literal("%"), 2, opAssoc.LEFT, make_binop),

                # Level 4: Addition, Subtraction (left-associative)
                (Literal("+") | Literal("-"), 2, opAssoc.LEFT, make_binop),

                # Level 3: Comparisons (left-associative)
                (
                    Literal("==")
                    | Literal("!=")
                    | Literal("<=")
                    | Literal(">=")
                    | Literal("<")
                    | Literal(">"),
                    2,
                    opAssoc.LEFT,
                    make_binop,
                ),

                # Level 2: Logical AND (left-associative)
                (Literal("and"), 2, opAssoc.LEFT, make_binop),

                # Level 1: Logical OR (left-associative)
                (Literal("or"), 2, opAssoc.LEFT, make_binop),
            ],
        )

        self.expression = expression_with_ops
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_addition or test_parse_operator_precedence" -v
```

**Expected:** Both tests PASS

**Run all binary operator tests:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "binary or operator or precedence or parentheses" -v
```

**Expected:** All 6 tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add binary operator parsing with precedence"
```

---

### Step 10: Write failing tests for unary operators

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
from townlet.world.expression import UnaryOp


def test_parse_unary_minus():
    """Parser handles unary negation."""
    parser = ExpressionParser()
    result = parser.parse("-x")

    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.SUB
    assert isinstance(result.operand, Variable)
    assert result.operand.name == "x"


def test_parse_unary_not():
    """Parser handles logical not."""
    parser = ExpressionParser()
    result = parser.parse("not active")

    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.NOT
    assert isinstance(result.operand, Variable)
    assert result.operand.name == "active"


def test_parse_double_negation():
    """Parser handles nested unary operators."""
    parser = ExpressionParser()
    result = parser.parse("--x")

    # Should parse as: -(-(x))
    assert isinstance(result, UnaryOp)
    assert result.op == OperatorType.SUB
    assert isinstance(result.operand, UnaryOp)
    assert result.operand.op == OperatorType.SUB
    assert result.operand.operand.name == "x"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_unary_minus -v
```

**Expected:** FAIL - Unary operators not recognized

---

### Step 11: Implement unary operator parsing

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Modify the `infixNotation` call to add unary operators. Insert BEFORE the exponentiation level:

```python
        # Helper to make unary ops
        def make_unaryop(tokens):
            """Convert prefix tokens to UnaryOp AST nodes."""
            result = tokens[0][-1]  # Start with the innermost operand
            # Process operators right-to-left
            for i in range(len(tokens[0]) - 2, -1, -1):
                op_str = tokens[0][i]
                op_map = {
                    "-": OperatorType.SUB,
                    "not": OperatorType.NOT,
                }
                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown unary operator: {op_str}")
                result = UnaryOp(op=op_type, operand=result)
            return result

        expression_with_ops = infixNotation(
            primary,
            [
                # Level 7: Unary operators (prefix, right-associative)
                (Literal("-") | Literal("not"), 1, opAssoc.RIGHT, make_unaryop),

                # Level 6: Exponentiation (right-associative)
                (Literal("**"), 2, opAssoc.RIGHT, make_binop),

                # ... rest of operators unchanged ...
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_unary" -v
```

**Expected:** All 3 unary tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add unary operator parsing (negation, not)"
```

---

### Step 12: Write failing tests for function calls

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
def test_parse_function_call_no_args():
    """Parser handles zero-argument function calls."""
    parser = ExpressionParser()
    result = parser.parse("get_time()")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "get_time"
    assert result.arguments == []


def test_parse_function_call_single_arg():
    """Parser handles single-argument function calls."""
    parser = ExpressionParser()
    result = parser.parse("abs(x)")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "abs"
    assert len(result.arguments) == 1
    assert isinstance(result.arguments[0], Variable)
    assert result.arguments[0].name == "x"


def test_parse_function_call_multiple_args():
    """Parser handles multi-argument function calls."""
    parser = ExpressionParser()
    result = parser.parse("clamp(val, 0, 1)")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "clamp"
    assert len(result.arguments) == 3
    assert isinstance(result.arguments[0], Variable)
    assert isinstance(result.arguments[1], Constant)
    assert isinstance(result.arguments[2], Constant)


def test_parse_function_call_string_arg():
    """Parser handles string arguments."""
    parser = ExpressionParser()
    result = parser.parse('distance_to_affordance("Fridge")')

    assert isinstance(result, FunctionCall)
    assert result.function_name == "distance_to_affordance"
    assert len(result.arguments) == 1
    assert result.arguments[0].value == "Fridge"


def test_parse_nested_function_calls():
    """Parser handles nested function calls."""
    parser = ExpressionParser()
    result = parser.parse("max(abs(x), abs(y))")

    assert isinstance(result, FunctionCall)
    assert result.function_name == "max"
    assert len(result.arguments) == 2
    assert isinstance(result.arguments[0], FunctionCall)
    assert result.arguments[0].function_name == "abs"
    assert isinstance(result.arguments[1], FunctionCall)
    assert result.arguments[1].function_name == "abs"


def test_parse_if_then_else():
    """Parser handles if/then/else ternary syntax."""
    from townlet.world.expression import IfThenElse

    parser = ExpressionParser()
    result = parser.parse("if x > 0 then 1 else -1")

    assert isinstance(result, IfThenElse)
    assert isinstance(result.condition, BinaryOp)
    assert result.condition.op == OperatorType.GT
    assert isinstance(result.true_branch, Constant)
    assert result.true_branch.value == 1
    assert isinstance(result.false_branch, UnaryOp)
    assert result.false_branch.op == OperatorType.SUB


def test_parse_nested_if_then_else():
    """Parser handles nested if/then/else."""
    from townlet.world.expression import IfThenElse

    parser = ExpressionParser()
    result = parser.parse("if a then (if b then 1 else 2) else 3")

    assert isinstance(result, IfThenElse)
    assert isinstance(result.true_branch, IfThenElse)


def test_parse_exponentiation_right_associative():
    """Parser respects right-associativity for exponentiation."""
    parser = ExpressionParser()
    result = parser.parse("2 ** 3 ** 4")

    # Should parse as: 2 ** (3 ** 4), NOT (2 ** 3) ** 4
    assert isinstance(result, BinaryOp)
    assert result.op == OperatorType.POW
    assert isinstance(result.left, Constant)
    assert result.left.value == 2

    # Right side should be 3 ** 4
    assert isinstance(result.right, BinaryOp)
    assert result.right.op == OperatorType.POW
    assert result.right.left.value == 3
    assert result.right.right.value == 4
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_function_call_no_args -v
```

**Expected:** FAIL - Function calls not recognized

---

### Step 13: Implement function call parsing

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Add BEFORE the `primary` definition:

```python
        # Forward declaration for recursive grammar
        expression_ref = Forward()

        # Function calls
        # max(a, b) → FunctionCall("max", [Variable("a"), Variable("b")])
        lparen = Suppress("(")
        rparen = Suppress(")")
        comma = Suppress(",")

        def make_function_call(tokens):
            func_name = tokens[0]
            # arguments might be empty list or list of expressions
            args = list(tokens[1:]) if len(tokens) > 1 else []
            return FunctionCall(function_name=func_name, arguments=args)

        function_call = (
            identifier
            + lparen
            + Optional(expression_ref + (comma + expression_ref)[...])
            + rparen
        ).setParseAction(make_function_call)
```

Then update `primary` to include function calls:

```python
        # Primary expressions (atoms)
        # Order matters: try function_call before path_or_variable
        # (both start with identifier)
        primary = constant | function_call | path_or_variable

        # Bind the forward reference to the full expression
        # (needed for recursive function call arguments)
        expression_with_ops = infixNotation(...)  # existing code
        expression_ref <<= expression_with_ops
```

**Wait - we need to reorganize.** The forward reference needs to point to the FINAL expression including operators. Let me fix this:

**Replace the entire `_build_grammar` method with this reorganized version:**

```python
    def _build_grammar(self):
        """Build pyparsing grammar for expression language."""
        from pyparsing import Forward, Optional, Suppress, infixNotation, opAssoc

        # Forward declaration for recursive grammar
        expression_ref = Forward()

        # Literals
        true_literal = Literal("true").setParseAction(lambda: Constant(value=True))
        false_literal = Literal("false").setParseAction(lambda: Constant(value=False))
        bool_literal = true_literal | false_literal

        float_literal = pyparsing_common.fnumber().setParseAction(
            lambda tokens: Constant(value=float(tokens[0]))
        )
        int_literal = pyparsing_common.signed_integer().setParseAction(
            lambda tokens: Constant(value=int(tokens[0]))
        )
        numeric_literal = float_literal | int_literal

        string_literal = (
            QuotedString('"', escChar="\\") | QuotedString("'", escChar="\\")
        ).setParseAction(lambda tokens: Constant(value=str(tokens[0])))

        constant = bool_literal | numeric_literal | string_literal

        # Identifiers and keywords
        keywords = {"true", "false", "and", "or", "not", "if", "then", "else"}
        identifier = Word(alphas + "_", alphanums + "_")

        # Function calls (must come before variables to parse correctly)
        lparen = Suppress("(")
        rparen = Suppress(")")
        comma = Suppress(",")

        def make_function_call(tokens):
            func_name = tokens[0]
            args = list(tokens[1:]) if len(tokens) > 1 else []
            return FunctionCall(function_name=func_name, arguments=args)

        function_call = (
            identifier
            + lparen
            + Optional(expression_ref + (comma + expression_ref)[...])
            + rparen
        ).setParseAction(make_function_call)

        # Path access or variable
        def make_path_access(tokens):
            segments = [str(t) for t in tokens]
            if len(segments) == 1:
                name = segments[0]
                if name in keywords:
                    raise ValueError(f"Cannot use keyword '{name}' as variable")
                return Variable(name=name)
            return PathAccess(segments=segments)

        path_or_variable = (
            identifier + (Literal(".").suppress() + identifier)[...]
        ).setParseAction(make_path_access)

        # If-Then-Else (ternary conditional)
        # if x > 0 then 1 else -1
        if_kw = Literal("if")
        then_kw = Literal("then")
        else_kw = Literal("else")

        def make_if_then_else(tokens):
            # tokens: [condition, true_branch, false_branch]
            return IfThenElse(
                condition=tokens[0],
                true_branch=tokens[1],
                false_branch=tokens[2]
            )

        if_expression = (
            if_kw.suppress()
            + expression_ref
            + then_kw.suppress()
            + expression_ref
            + else_kw.suppress()
            + expression_ref
        ).setParseAction(make_if_then_else)

        # Primary expressions (order matters: try function_call before path)
        primary = constant | function_call | if_expression | path_or_variable

        # Unary operator helpers
        def make_unaryop(tokens):
            result = tokens[0][-1]
            for i in range(len(tokens[0]) - 2, -1, -1):
                op_str = tokens[0][i]
                op_map = {"-": OperatorType.SUB, "not": OperatorType.NOT}
                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown unary operator: {op_str}")
                result = UnaryOp(op=op_type, operand=result)
            return result

        # Binary operator helpers (LEFT-associative)
        def make_binop(tokens):
            """Convert infix tokens to BinaryOp (left-associative)."""
            result = tokens[0][0]
            i = 1
            while i < len(tokens[0]):
                op_str = tokens[0][i]
                right = tokens[0][i + 1]
                op_map = {
                    "+": OperatorType.ADD,
                    "-": OperatorType.SUB,
                    "*": OperatorType.MUL,
                    "/": OperatorType.DIV,
                    "%": OperatorType.MOD,
                    "==": OperatorType.EQ,
                    "!=": OperatorType.NEQ,
                    "<": OperatorType.LT,
                    ">": OperatorType.GT,
                    "<=": OperatorType.LTE,
                    ">=": OperatorType.GTE,
                    "and": OperatorType.AND,
                    "or": OperatorType.OR,
                }
                op_type = op_map.get(op_str)
                if op_type is None:
                    raise ValueError(f"Unknown operator: {op_str}")
                result = BinaryOp(left=result, op=op_type, right=right)
                i += 2
            return result

        # Binary operator helpers (RIGHT-associative)
        def make_right_binop(tokens):
            """Convert infix tokens to BinaryOp (right-associative).

            For a ** b ** c, parse as a ** (b ** c), not (a ** b) ** c.
            """
            items = tokens[0]
            # Build from right to left
            result = items[-1]  # Rightmost operand
            for i in range(len(items) - 2, -1, -2):
                op_str = items[i]
                left = items[i - 1]

                if op_str == "**":
                    op_type = OperatorType.POW
                else:
                    raise ValueError(f"Unknown right-assoc operator: {op_str}")

                result = BinaryOp(left=left, op=op_type, right=result)
            return result

        # Build expression with operator precedence
        expression_with_ops = infixNotation(
            primary,
            [
                (Literal("-") | Literal("not"), 1, opAssoc.RIGHT, make_unaryop),
                (Literal("**"), 2, opAssoc.RIGHT, make_right_binop),
                (Literal("*") | Literal("/") | Literal("%"), 2, opAssoc.LEFT, make_binop),
                (Literal("+") | Literal("-"), 2, opAssoc.LEFT, make_binop),
                (
                    Literal("==")
                    | Literal("!=")
                    | Literal("<=")
                    | Literal(">=")
                    | Literal("<")
                    | Literal(">"),
                    2,
                    opAssoc.LEFT,
                    make_binop,
                ),
                (Literal("and"), 2, opAssoc.LEFT, make_binop),
                (Literal("or"), 2, opAssoc.LEFT, make_binop),
            ],
        )

        # Bind forward reference
        expression_ref <<= expression_with_ops
        self.expression = expression_with_ops
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_function_call" -v
```

**Expected:** All 5 function_call tests PASS

**Verify existing tests still pass:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -v
```

**Expected:** All tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add function call parsing with recursion"
```

---

### Step 14: Write failing tests for index access

**File:** `tests/test_townlet/unit/world/expression/test_parser.py` (append)

```python
def test_parse_index_access_constant():
    """Parser handles array indexing with constant index."""
    parser = ExpressionParser()
    result = parser.parse("inventory[0]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, Variable)
    assert result.base.name == "inventory"
    assert isinstance(result.index, Constant)
    assert result.index.value == 0


def test_parse_index_access_variable():
    """Parser handles array indexing with variable index."""
    parser = ExpressionParser()
    result = parser.parse("items[slot_index]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, Variable)
    assert result.base.name == "items"
    assert isinstance(result.index, Variable)
    assert result.index.name == "slot_index"


def test_parse_index_access_expression():
    """Parser handles array indexing with expression index."""
    parser = ExpressionParser()
    result = parser.parse("bars[i + 1]")

    assert isinstance(result, IndexAccess)
    assert isinstance(result.index, BinaryOp)
    assert result.index.op == OperatorType.ADD


def test_parse_nested_index_access():
    """Parser handles multi-dimensional indexing."""
    parser = ExpressionParser()
    result = parser.parse("grid[x][y]")

    # Should parse as: (grid[x])[y]
    assert isinstance(result, IndexAccess)
    assert isinstance(result.base, IndexAccess)
    assert result.base.base.name == "grid"
    assert result.base.index.name == "x"
    assert result.index.name == "y"
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py::test_parse_index_access_constant -v
```

**Expected:** FAIL - Index access not recognized

---

### Step 15: Implement index access parsing

**File:** `src/townlet/world/expression/parser.py` (modify `_build_grammar`)

Add after function_call definition and before primary:

```python
        # Index access (array subscripting)
        # inventory[0] → IndexAccess(Variable("inventory"), Constant(0))
        lbracket = Suppress("[")
        rbracket = Suppress("]")

        # Index access is a postfix operator on primary expressions
        # We'll handle this after defining primary

        # Primary expressions (before index access)
        primary_base = constant | function_call | path_or_variable

        # Index access wraps primary (postfix operator)
        def make_index_access(tokens):
            result = tokens[0]
            # Each [expr] creates a new IndexAccess wrapping the previous result
            for i in range(1, len(tokens)):
                index_expr = tokens[i]
                result = IndexAccess(base=result, index=index_expr)
            return result

        primary_with_index = (
            primary_base + (lbracket + expression_ref + rbracket)[...]
        ).setParseAction(make_index_access)

        # Update primary to include index access
        primary = primary_with_index
```

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -k "test_parse_index_access" -v
```

**Expected:** All 4 index_access tests PASS

**Verify all tests:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -v
```

**Expected:** All tests PASS

**Commit:**
```bash
git add src/townlet/world/expression/parser.py tests/test_townlet/unit/world/expression/test_parser.py
git commit -m "feat(expression): add index access parsing (array subscripting)"
```

---

### Step 16: Add parser to module __init__

**File:** `src/townlet/world/expression/__init__.py` (modify)

Add to imports and __all__:

```python
from .ast_nodes import (...)  # existing
from .parser import ExpressionParser

__all__ = [
    # ... existing ...
    "ExpressionParser",
]
```

**Verify:**
```bash
UV_CACHE_DIR=.uv-cache uv run python -c "from townlet.world.expression import ExpressionParser; p = ExpressionParser(); print(p.parse('a + b'))"
```

**Expected:** Prints BinaryOp object

**Commit:**
```bash
git add src/townlet/world/expression/__init__.py
git commit -m "feat(expression): export ExpressionParser in module API"
```

---

### Step 17: Run full test suite

**Run:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py -v --tb=short
```

**Expected:** All tests PASS

**Count tests:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/unit/world/expression/test_parser.py --co -q
```

**Expected:** ~35-40 tests

---

### Step 18: Type checking and formatting

**Run mypy:**
```bash
UV_CACHE_DIR=.uv-cache uv run mypy src/townlet/world/expression/parser.py
```

**Expected:** Success (or fix type errors)

**Run ruff:**
```bash
UV_CACHE_DIR=.uv-cache uv run ruff format src/townlet/world/expression/
UV_CACHE_DIR=.uv-cache uv run ruff format tests/test_townlet/unit/world/expression/
```

**Expected:** Code formatted

**Commit:**
```bash
git add -u
git commit -m "style(expression): format parser code"
```

---

## Success Criteria

✅ **35-40 tests passing** (exceeds 15-20 requirement)
✅ **All expression types parseable** (constants, variables, paths, operators, functions, index access)
✅ **Operator precedence correct** (PEMDAS + logical ops)
✅ **Recursive grammar working** (nested function calls, nested index access)
✅ **Type checking passes** (mypy clean)
✅ **Code formatted** (ruff)

---

## Next Steps

**Phase 1 - Task 1.3: Type Checker**

Implement type checking visitor that:
- Validates path resolution (`target.bar.energy` exists in schema)
- Checks type compatibility (can't assign vec2i to scalar)
- Infers expression result types
- Catches errors at compile-time

See: `docs/plans/2025-11-19-task-1-3-type-checker.md` (to be created)
