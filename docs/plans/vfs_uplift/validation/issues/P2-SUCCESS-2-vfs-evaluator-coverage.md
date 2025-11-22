# P2-SUCCESS-2: VFS Evaluator Test Coverage at 22%

**Priority:** P2 (Minor - Test Coverage Gap)
**Category:** Success Criteria (Testing)
**Estimated Effort:** 4-6 hours
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The VFS evaluator module (`src/townlet/world/expression/evaluator.py`) has only 22% test coverage, below the 80% target for core modules.

**Current Coverage:**
```
src/townlet/world/expression/evaluator.py    22%    (low)
```

**Gap Analysis:**
- Expression parsing: Well tested (113 tests)
- Type checking: Well tested (27 tests)
- **Evaluator execution:** Under-tested (integration tests exist, unit coverage gaps)

**Impact:**
- Edge cases in evaluation logic may not be caught
- Runtime evaluation bugs harder to debug
- **Low priority:** Integration tests validate end-to-end behavior

**Evidence:**
- Agent 9 (Success Criteria) report, section SUCCESS-2
- Coverage report from `uv run pytest --cov`

---

## How to Fix

### Step 1: Identify Uncovered Code Paths (1 hour)

Run coverage with detailed output:

```bash
# Generate coverage report with missing lines
UV_CACHE_DIR=.uv-cache uv run pytest \
  --cov=townlet.world.expression.evaluator \
  --cov-report=term-missing \
  tests/test_townlet/unit/world/expression/

# Expected output:
# evaluator.py   22%   Lines 45-67, 89-103, 120-135 not covered
```

**Analyze missing coverage:**
- Which operators lack evaluation tests?
- Which edge cases not tested (empty batches, NaN handling)?
- Which error paths not exercised?

### Step 2: Add Unit Tests for Uncovered Operators (2 hours)

**File:** `tests/test_townlet/unit/world/expression/test_evaluator.py` (extend existing)

Add tests for uncovered operators:

```python
"""Extended tests for ExpressionEvaluator coverage."""

import pytest
import torch
from townlet.world.expression.evaluator import ExpressionEvaluator
from townlet.world.expression.parser import ExpressionParser
from townlet.world.expression.nodes import *


class TestArithmeticOperators:
    """Test all arithmetic operators."""

    def test_addition(self):
        """Verify + operator."""
        expr = parse("2.0 + 3.0")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([5.0]))

    def test_subtraction(self):
        """Verify - operator."""
        expr = parse("10.0 - 3.0")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([7.0]))

    def test_multiplication(self):
        """Verify * operator."""
        expr = parse("4.0 * 5.0")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([20.0]))

    def test_division(self):
        """Verify / operator."""
        expr = parse("20.0 / 4.0")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([5.0]))

    def test_division_by_zero_returns_nan(self):
        """Verify division by zero returns NaN, not error."""
        expr = parse("1.0 / 0.0")
        result = evaluator.evaluate(expr, context)
        assert torch.isnan(result).all()


class TestComparisonOperators:
    """Test all comparison operators."""

    def test_greater_than(self):
        """Verify > operator."""
        expr = parse("5.0 > 3.0")
        result = evaluator.evaluate(expr, context)
        assert result.dtype == torch.bool
        assert result.all()

    def test_less_than(self):
        """Verify < operator."""
        expr = parse("3.0 < 5.0")
        result = evaluator.evaluate(expr, context)
        assert result.all()

    def test_equality(self):
        """Verify == operator."""
        expr = parse("5.0 == 5.0")
        result = evaluator.evaluate(expr, context)
        assert result.all()

    def test_inequality(self):
        """Verify != operator."""
        expr = parse("5.0 != 3.0")
        result = evaluator.evaluate(expr, context)
        assert result.all()


class TestLogicalOperators:
    """Test boolean logic operators."""

    def test_logical_and(self):
        """Verify AND operator."""
        expr = parse("true AND true")
        result = evaluator.evaluate(expr, context)
        assert result.all()

    def test_logical_or(self):
        """Verify OR operator."""
        expr = parse("false OR true")
        result = evaluator.evaluate(expr, context)
        assert result.all()

    def test_logical_not(self):
        """Verify NOT operator."""
        expr = parse("NOT false")
        result = evaluator.evaluate(expr, context)
        assert result.all()


class TestBuiltinFunctions:
    """Test all builtin functions."""

    def test_min_function(self):
        """Verify min() function."""
        expr = parse("min(5.0, 3.0)")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([3.0]))

    def test_max_function(self):
        """Verify max() function."""
        expr = parse("max(5.0, 3.0)")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([5.0]))

    def test_abs_function(self):
        """Verify abs() function."""
        expr = parse("abs(-5.0)")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([5.0]))

    def test_clamp_function(self):
        """Verify clamp() function."""
        expr = parse("clamp(15.0, 0.0, 10.0)")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([10.0]))

    def test_random_function_range(self):
        """Verify random() returns values in [0, 1]."""
        expr = parse("random()")
        result = evaluator.evaluate(expr, context)
        assert (result >= 0.0).all() and (result <= 1.0).all()


class TestPathResolution:
    """Test VFS/bar path resolution."""

    def test_global_vfs_path(self):
        """Verify global.vfs.X resolves correctly."""
        context.vfs_registry.global_vfs[0, time_idx] = 0.75
        expr = parse("global.vfs.time_of_day")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([0.75]))

    def test_agent_vfs_path(self):
        """Verify agent.vfs.X resolves correctly."""
        context.vfs_registry.agent_vfs[0, agent_id, gold_idx] = 100.0
        expr = parse("agent.vfs.gold")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([100.0]))

    def test_agent_bar_path(self):
        """Verify agent.bar.X resolves correctly."""
        context.bars[0, agent_id, energy_idx] = 0.5
        expr = parse("agent.bar.energy")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([0.5]))

    def test_item_reference_path(self):
        """Verify item reference traversal (target.vfs.X)."""
        # Set up item VFS state
        context.vfs_registry.item_vfs[0, item_id, damage_idx] = 25.0
        expr = parse("target.vfs.damage")
        result = evaluator.evaluate(expr, context)
        assert torch.allclose(result, torch.tensor([25.0]))


class TestBatchedEvaluation:
    """Test vectorized evaluation across batches."""

    def test_batched_arithmetic(self):
        """Verify operations work across batch dimension."""
        # Set different values per env
        context.bars[:, agent_id, energy_idx] = torch.tensor([0.5, 0.7, 0.9])
        expr = parse("agent.bar.energy * 2.0")
        result = evaluator.evaluate(expr, context)

        expected = torch.tensor([1.0, 1.4, 1.8])
        assert torch.allclose(result, expected)

    def test_batched_comparison(self):
        """Verify comparisons work across batch dimension."""
        context.bars[:, agent_id, energy_idx] = torch.tensor([0.3, 0.5, 0.7])
        expr = parse("agent.bar.energy > 0.5")
        result = evaluator.evaluate(expr, context)

        expected = torch.tensor([False, False, True])
        assert (result == expected).all()
```

### Step 3: Add Edge Case Tests (1 hour)

Test error handling and edge cases:

```python
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_batch(self):
        """Verify evaluation with empty batch."""
        context = ExecutionContext(batch_size=0)
        expr = parse("1.0 + 2.0")
        result = evaluator.evaluate(expr, context)
        assert result.shape == (0,)

    def test_nan_propagation(self):
        """Verify NaN propagates through expressions."""
        context.bars[0, agent_id, energy_idx] = float('nan')
        expr = parse("agent.bar.energy + 1.0")
        result = evaluator.evaluate(expr, context)
        assert torch.isnan(result).all()

    def test_inf_handling(self):
        """Verify infinity handled gracefully."""
        expr = parse("1.0 / 0.0")  # Division by zero
        result = evaluator.evaluate(expr, context)
        # Should be inf or nan, not crash
        assert torch.isinf(result).all() or torch.isnan(result).all()

    def test_invalid_path_raises_error(self):
        """Verify invalid paths raise errors."""
        expr = parse("agent.bar.nonexistent")
        with pytest.raises(KeyError, match="nonexistent"):
            evaluator.evaluate(expr, context)

    def test_type_coercion_float_to_bool(self):
        """Verify type coercion in boolean contexts."""
        expr = parse("agent.bar.energy AND true")  # Float AND bool
        # Should coerce float to bool (> 0.5)
        result = evaluator.evaluate(expr, context)
        assert result.dtype == torch.bool
```

### Step 4: Verify Coverage Improvement (30 minutes)

Re-run coverage after adding tests:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest \
  --cov=townlet.world.expression.evaluator \
  --cov-report=term-missing \
  tests/test_townlet/unit/world/expression/

# Target: 80%+ coverage
```

---

## Acceptance Criteria

- [ ] VFS evaluator coverage increases from 22% to ≥80%
- [ ] All arithmetic operators tested (+, -, *, /, %, **)
- [ ] All comparison operators tested (>, <, ==, !=, >=, <=)
- [ ] All logical operators tested (AND, OR, NOT)
- [ ] All builtin functions tested (min, max, abs, clamp, random)
- [ ] Path resolution tested (global.vfs, agent.vfs, agent.bar, target.vfs)
- [ ] Batched evaluation tested
- [ ] Edge cases tested (NaN, inf, division by zero, empty batch)

---

## Files to Modify

1. `tests/test_townlet/unit/world/expression/test_evaluator.py` - Add unit tests

---

## Related Issues

- Related: P1-VFS-1 (expression operator coverage - only 40% operators implemented)
- Related: P2-SUCCESS-3 (environment integration coverage)
- Blocks: None (test coverage gap)

---

## Notes

- **Low priority:** Integration tests validate end-to-end behavior
- **Code quality:** Higher unit test coverage helps catch regressions
- **Strategy:** Focus on uncovered lines from coverage report
- **Quick win:** Most operators already implemented, just need tests
- Consider using property-based testing (hypothesis) for arithmetic edge cases
