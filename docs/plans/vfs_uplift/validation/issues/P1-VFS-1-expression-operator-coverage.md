# P1-VFS-1: Expression Operator Coverage Only 40% Complete

**Priority:** P1 (Important - Should Fix)
**Category:** VFS System
**Estimated Effort:** 3-5 days (incremental)
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

The expression evaluator only implements ~40% of the operators specified in the VFS design document (`VARIABLE_SUBSYSTEM.md`).

**Implemented (Working):**
- ✅ Basic math: `+`, `-`, `*`, `/`, `%`, `**`
- ✅ Comparison: `==`, `!=`, `<`, `>`, `<=`, `>=`
- ✅ Logical: `and`, `or`, `not`
- ✅ Parentheses and operator precedence
- ✅ Variable references: `self.bar.energy`, `target.vfs.health`

**Missing (~60%):**
- ❌ Advanced trig: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`
- ❌ Temporal: `day_of_week`, `time_of_day`, `season`
- ❌ Spatial: `distance`, `manhattan_distance`, `in_range`
- ❌ Statistical: `mean`, `median`, `std`, `percentile`
- ❌ Stochastic: `random`, `normal`, `uniform`, `bernoulli`
- ❌ Vector ops: `dot`, `cross`, `magnitude`, `normalize`
- ❌ Conditional: `if_then_else`, `clamp`, `lerp`

**Impact:**
- Cannot express complex VFS variables that require advanced operators
- Pedagogical limitation: Students can't explore advanced RL reward engineering
- **Not a blocker:** Current operators sufficient for core use cases

**Evidence:**
- Agent 2 (VFS System) report, section VFS-1
- File: `src/townlet/world/expression/evaluator.py` (operator coverage ~40%)
- Design doc: `docs/VARIABLE_SUBSYSTEM.md` lists full operator set

---

## Why This is P1 (Not P0)

**This is NOT a blocker because:**
- Core VFS functionality works with current operators
- All existing test configs use only implemented operators
- Architecture supports easy addition of new operators
- No runtime errors - expressions using missing operators fail at compile time with clear error

**This IS important because:**
- Limits pedagogical value of the framework
- Prevents advanced curriculum levels (spatial reasoning, stochastic rewards)
- Missing operators documented in design spec creates expectation gap

---

## How to Fix (Incremental Approach)

### Phase 1: Mathematical Functions (1 day)

**File:** `src/townlet/world/expression/evaluator.py`

Add math operators:

```python
class ExpressionEvaluator:
    def visit_FunctionCall(self, node: FunctionCallNode) -> torch.Tensor:
        if node.func_name == 'sin':
            return torch.sin(self.visit(node.args[0]))
        elif node.func_name == 'cos':
            return torch.cos(self.visit(node.args[0]))
        elif node.func_name == 'sqrt':
            return torch.sqrt(self.visit(node.args[0]))
        elif node.func_name == 'abs':
            return torch.abs(self.visit(node.args[0]))
        elif node.func_name == 'min':
            return torch.min(self.visit(node.args[0]), self.visit(node.args[1]))
        elif node.func_name == 'max':
            return torch.max(self.visit(node.args[0]), self.visit(node.args[1]))
        elif node.func_name == 'clamp':
            val = self.visit(node.args[0])
            min_val = self.visit(node.args[1])
            max_val = self.visit(node.args[2])
            return torch.clamp(val, min_val, max_val)
        else:
            raise NotImplementedError(f"Function '{node.func_name}' not implemented")
```

**Tests:** Add to `tests/test_townlet/unit/world/expression/test_evaluator.py`

### Phase 2: Temporal Functions (1 day)

```python
def visit_FunctionCall(self, node: FunctionCallNode) -> torch.Tensor:
    # ... existing math functions ...

    elif node.func_name == 'time_of_day':
        # Expects global VFS variable 'step'
        step = self.context.vfs_registry.global_vfs[:, self.context.step_index]
        return (step % 24) / 24.0  # Normalize to [0, 1]

    elif node.func_name == 'day_of_week':
        step = self.context.vfs_registry.global_vfs[:, self.context.step_index]
        return ((step // 24) % 7) / 7.0  # Day of week [0, 1]
```

### Phase 3: Spatial Functions (1 day)

```python
elif node.func_name == 'distance':
    # Euclidean distance between two positions
    pos1 = self.visit(node.args[0])  # vec2i
    pos2 = self.visit(node.args[1])  # vec2i
    diff = pos1 - pos2
    return torch.sqrt((diff ** 2).sum(dim=-1))

elif node.func_name == 'manhattan_distance':
    pos1 = self.visit(node.args[0])
    pos2 = self.visit(node.args[1])
    diff = torch.abs(pos1 - pos2)
    return diff.sum(dim=-1)

elif node.func_name == 'in_range':
    dist = self.visit(node.args[0])  # Can call distance()
    max_range = self.visit(node.args[1])
    return (dist <= max_range).float()
```

### Phase 4: Stochastic Functions (1-2 days)

**Note:** Requires careful handling for reproducibility

```python
elif node.func_name == 'random':
    # Uniform random [0, 1]
    # IMPORTANT: Use seeded RNG for reproducibility
    if not hasattr(self.context, 'rng'):
        self.context.rng = torch.Generator()
        self.context.rng.manual_seed(self.context.seed)

    shape = self.context.batch_size
    return torch.rand(shape, generator=self.context.rng)

elif node.func_name == 'normal':
    mean = self.visit(node.args[0])
    std = self.visit(node.args[1])
    noise = torch.randn_like(mean, generator=self.context.rng)
    return mean + std * noise
```

### Phase 5: Statistical Functions (1 day)

```python
elif node.func_name == 'mean':
    # Mean over agent dimension
    values = self.visit(node.args[0])
    return torch.mean(values, dim=0, keepdim=True).expand_as(values)

elif node.func_name == 'std':
    values = self.visit(node.args[0])
    return torch.std(values, dim=0, keepdim=True).expand_as(values)
```

---

## Testing Strategy

For each phase, add tests to `test_evaluator.py`:

```python
def test_math_functions():
    expr = "sin(3.14159 / 2)"
    result = evaluator.evaluate(expr)
    assert torch.allclose(result, torch.tensor(1.0), atol=1e-4)

def test_temporal_functions():
    # Set global step to 12 (noon)
    context.vfs_registry.global_vfs[0, step_idx] = 12.0
    expr = "time_of_day()"
    result = evaluator.evaluate(expr)
    assert torch.allclose(result, torch.tensor(0.5))  # 12/24 = 0.5

def test_stochastic_reproducibility():
    # Verify seeded random is deterministic
    context.seed = 42
    expr = "random()"
    result1 = evaluator.evaluate(expr)

    context.seed = 42  # Reset
    result2 = evaluator.evaluate(expr)

    assert torch.allclose(result1, result2)
```

---

## Documentation Updates

**File:** `docs/config-schemas/expressions.md`

Add operator reference table for each phase:

```markdown
### Mathematical Functions

| Operator | Signature | Example | Description |
|----------|-----------|---------|-------------|
| `sin(x)` | `float → float` | `sin(angle)` | Sine (radians) |
| `cos(x)` | `float → float` | `cos(angle)` | Cosine (radians) |
| `clamp(x, min, max)` | `float, float, float → float` | `clamp(value, 0.0, 1.0)` | Clamp to range |
...
```

---

## Acceptance Criteria

**Per Phase:**
- [ ] Operators implemented in `evaluator.py`
- [ ] Type checker updated in `type_checker.py` (if needed)
- [ ] Unit tests added with 100% coverage for new operators
- [ ] Documentation updated in `expressions.md`
- [ ] Integration test using new operators in VFS profile

**Overall:**
- [ ] All operators from `VARIABLE_SUBSYSTEM.md` implemented
- [ ] 100% operator coverage (not 40%)
- [ ] No breaking changes to existing expressions

---

## Files to Modify

1. `src/townlet/world/expression/evaluator.py` - Add operator implementations
2. `src/townlet/world/expression/type_checker.py` - Add type signatures
3. `tests/test_townlet/unit/world/expression/test_evaluator.py` - Add tests
4. `docs/config-schemas/expressions.md` - Document new operators

---

## Related Issues

- Blocking: None (optional feature expansion)
- Blocked by: None
- Related: Future curriculum levels (L4+ spatial reasoning)

---

## Notes

- **Incremental delivery:** Ship each phase independently
- **Backward compatible:** Adding operators doesn't break existing expressions
- **Seeded RNG crucial:** Stochastic operators must be reproducible for RL training
- **Performance:** Most operators are GPU-native (torch ops), minimal overhead
- **Non-blocking:** Can defer to post-merge and add as needed for new curriculum levels
