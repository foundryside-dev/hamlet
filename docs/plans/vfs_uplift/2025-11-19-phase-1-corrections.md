# Phase 1 Implementation Plans - Critical Corrections

**Date:** 2025-11-19
**Status:** MUST READ BEFORE EXECUTING

---

## Overview

Three critical technical issues discovered in Task 1.2 and Task 1.3 plans. These corrections MUST be applied during execution.

---

## Correction 1: Task 1.2 - Add IfThenElse Grammar

**Issue:** AST node defined but no parser grammar for `if/then/else` syntax.

**Location:** Task 1.2, Step 13 (reorganized `_build_grammar`)

**Fix:** Add IfThenElse grammar BEFORE `primary` definition:

```python
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
```

**Update primary to include if_expression:**

```python
        # Primary expressions
        # Order: constant, function_call, if_expression, path_or_variable
        primary = constant | function_call | if_expression | path_or_variable
```

**Add tests in Step 12 (after function_call tests):**

```python
from townlet.world.expression import IfThenElse


def test_parse_if_then_else():
    """Parser handles if/then/else ternary syntax."""
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
    parser = ExpressionParser()
    result = parser.parse("if a then (if b then 1 else 2) else 3")

    assert isinstance(result, IfThenElse)
    assert isinstance(result.true_branch, IfThenElse)
```

---

## Correction 2: Task 1.2 - Fix Right-Associativity for Exponentiation

**Issue:** `make_binop` iterates left-to-right, making `2**3**4` parse as `(2**3)**4` instead of `2**(3**4)`.

**Location:** Task 1.2, Step 9 (`_build_grammar`)

**Fix:** Add separate handler for right-associative operators:

```python
        # Binary operator helpers (LEFT associative)
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

        # Binary operator helpers (RIGHT associative)
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
```

**Update infixNotation to use make_right_binop for exponentiation:**

```python
        expression_with_ops = infixNotation(
            primary,
            [
                # Level 7: Unary operators (prefix, right-associative)
                (Literal("-") | Literal("not"), 1, opAssoc.RIGHT, make_unaryop),

                # Level 6: Exponentiation (right-associative) - FIXED
                (Literal("**"), 2, opAssoc.RIGHT, make_right_binop),

                # Level 5: Multiplication, Division, Modulo (left-associative)
                (Literal("*") | Literal("/") | Literal("%"), 2, opAssoc.LEFT, make_binop),

                # ... rest unchanged ...
            ],
        )
```

**Add test to verify right-associativity:**

```python
def test_parse_exponentiation_right_associative():
    """Parser respects right-associativity for exponentiation."""
    parser = ExpressionParser()
    result = parser.parse("2 ** 3 ** 4")

    # Should parse as: 2 ** (3 ** 4) = 2 ** 81 = ...
    # NOT: (2 ** 3) ** 4 = 8 ** 4 = 4096
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

---

## Correction 3: Task 1.3 - Implement IfThenElse Type Checking (Don't Defer)

**Issue:** IfThenElse type checking is trivial, no reason to defer to Phase 2.

**Location:** Task 1.3, Step 14 (visitor method stubs)

**Fix:** Replace the NotImplementedError stub with full implementation:

```python
    def visit_if_then_else(self, node: IfThenElse) -> PrimitiveType:
        """Check conditional expression.

        Rules:
        - Condition must be bool
        - True and false branches must have same type
        - Result type is branch type
        """
        # Check condition is bool
        cond_type = node.condition.accept(self)
        if cond_type != BoolType():
            raise TypeCheckError(
                f"If condition must be bool, got {cond_type}"
            )

        # Check both branches
        true_type = node.true_branch.accept(self)
        false_type = node.false_branch.accept(self)

        # Branches must match
        if true_type != false_type:
            raise TypeCheckError(
                f"If branches must have same type. "
                f"Got {true_type} (true) and {false_type} (false)"
            )

        # Result type is branch type
        return true_type
```

**Add tests in Step 13 (after integration tests):**

```python
def test_type_check_if_then_else():
    """Type checker validates if/then/else conditionals."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if true then 1 else 2
    node = IfThenElse(
        condition=Constant(value=True),
        true_branch=Constant(value=1),
        false_branch=Constant(value=2),
    )
    result_type = checker.check(node)

    assert result_type == ScalarType()


def test_type_check_if_non_bool_condition():
    """Type error when condition is not bool."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if 5 then 1 else 2  (condition is scalar, not bool)
    node = IfThenElse(
        condition=Constant(value=5),
        true_branch=Constant(value=1),
        false_branch=Constant(value=2),
    )

    with pytest.raises(TypeCheckError, match="must be bool"):
        checker.check(node)


def test_type_check_if_mismatched_branches():
    """Type error when branches have different types."""
    schema = {}
    checker = TypeChecker(schema=schema)

    # if true then 1 else true  (scalar vs bool)
    node = IfThenElse(
        condition=Constant(value=True),
        true_branch=Constant(value=1),
        false_branch=Constant(value=True),
    )

    with pytest.raises(TypeCheckError, match="must have same type"):
        checker.check(node)
```

**Update Step 14 commit message:**

```bash
git commit -m "feat(expression): implement if/then/else type checking"
```

---

## Execution Checklist

When executing plans, apply these corrections:

- [ ] **Task 1.2, Step 13:** Add IfThenElse grammar before primary
- [ ] **Task 1.2, Step 13:** Add if_expression tests (2 tests)
- [ ] **Task 1.2, Step 9:** Add make_right_binop function
- [ ] **Task 1.2, Step 9:** Use make_right_binop for exponentiation
- [ ] **Task 1.2, Step 9:** Add right-associativity test
- [ ] **Task 1.3, Step 14:** Implement visit_if_then_else (don't stub)
- [ ] **Task 1.3, Step 13:** Add if/then/else type checking tests (3 tests)
- [ ] **Task 1.4, Step 7:** Implement visit_if_then_else with torch.where()
- [ ] **Task 1.4, Step 7:** Add vectorized if/then/else tests (2 tests)

---

## Impact on Test Counts

**Task 1.2 (Parser):** +3 tests (2 if/then/else, 1 right-assoc) = **38-43 tests** (was 35-40)
**Task 1.3 (Type Checker):** +3 tests (if/then/else checking) = **28-33 tests** (was 25-30)
**Task 1.4 (Evaluator):** +2 tests (vectorized conditionals) = **22-25 tests** (was 20+)
**Total Phase 1:** **~120 tests** (was ~110)

---

## Validation

After applying corrections, verify:

1. **IfThenElse parsing works:**
   ```python
   parser.parse("if x > 0 then 1 else -1")  # Should return IfThenElse node
   ```

2. **Right-associativity correct:**
   ```python
   parser.parse("2 ** 3 ** 4")  # Should be 2 ** (3 ** 4), not (2 ** 3) ** 4
   ```

3. **IfThenElse type checking works:**
   ```python
   checker.check(if_node)  # Should validate condition is bool, branches match
   ```

---

## Correction 4: Task 1.4 - Vectorized IfThenElse Evaluation

**Issue:** IfThenElse cannot use Python `if/else` on batched tensors (4096 agents). Must use `torch.where()` for element-wise selection.

**Location:** Task 1.4, Step 7 (add after visit_unary_op)

**Critical:** Without this, `if bar.energy < 0.3 then 1.0 else 0.0` would fail on tensor[4096] conditions.

**Fix:** Add vectorized conditional evaluation:

```python
    def visit_if_then_else(self, node: IfThenElse) -> torch.Tensor:
        """Execute vectorized conditional logic using torch.where().

        Critical: Uses torch.where() because condition is a batch tensor.
        Cannot use Python's 'if' statement on Tensor[bool, batch_size].

        Logic: result[i] = true_branch[i] if condition[i] else false_branch[i]

        Example:
            condition = tensor([True, False, True])  # 3 agents
            true_val = tensor([10, 10, 10])
            false_val = tensor([20, 20, 20])
            result = tensor([10, 20, 10])  # Element-wise selection
        """
        condition = node.condition.accept(self)
        true_val = node.true_branch.accept(self)
        false_val = node.false_branch.accept(self)

        # Ensure inputs are tensors (handle scalar constants)
        if not isinstance(condition, torch.Tensor):
            condition = torch.tensor(condition, device=self.context.device)
        if not isinstance(true_val, torch.Tensor):
            true_val = torch.tensor(true_val, device=self.context.device)
        if not isinstance(false_val, torch.Tensor):
            false_val = torch.tensor(false_val, device=self.context.device)

        # Vectorized selection (PyTorch handles broadcasting)
        return torch.where(condition, true_val, false_val)
```

**Add tests:**

```python
def test_evaluate_if_then_else_vectorized():
    """Evaluator handles vectorized conditional (batch processing)."""
    from townlet.world.expression import PathAccess

    ctx = ExecutionContext(
        bars={"energy": torch.tensor([0.2, 0.8, 0.1])},  # 3 agents
    )
    evaluator = Evaluator(context=ctx)

    # if bar.energy < 0.3 then 1.0 else 0.0
    node = IfThenElse(
        condition=BinaryOp(
            left=PathAccess(segments=["bar", "energy"]),
            op=OperatorType.LT,
            right=Constant(value=0.3)
        ),
        true_branch=Constant(value=1.0),
        false_branch=Constant(value=0.0)
    )

    result = evaluator.evaluate(node)

    # [0.2 < 0.3 (T), 0.8 < 0.3 (F), 0.1 < 0.3 (T)]
    expected = torch.tensor([1.0, 0.0, 1.0])
    assert torch.allclose(result, expected)


def test_full_integration_if_then_else():
    """Parse + evaluate if/then/else on batched data."""
    parser = ExpressionParser()
    ctx = ExecutionContext(
        bars={"health": torch.tensor([0.5, 1.0])}
    )
    evaluator = Evaluator(context=ctx)

    ast = parser.parse("if bar.health > 0.8 then 10 else 20")
    result = evaluator.evaluate(ast)

    # [0.5 > 0.8 (F) -> 20, 1.0 > 0.8 (T) -> 10]
    expected = torch.tensor([20.0, 10.0])
    assert torch.allclose(result, expected)
```

---

## Ready to Execute

With these corrections applied, the plans are ready for execution via:

```
Use subagent-driven development to execute Task 1.1 from docs/plans/2025-11-19-task-1-1-ast-nodes.md
```

Then continue with Task 1.2 (with corrections), Task 1.3 (with corrections), and Task 1.4 (with corrections).
