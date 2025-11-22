# [VFS-1] Advanced Expression Operators (Phase 2)

**Priority:** P2 (Deferred)
**Category:** VFS / Expression Language
**Status:** DEFERRED TO PHASE 2
**Effort:** 12-16 hours (Phase 2 work)

## Description

Core expression language operators (arithmetic, logical, comparison, conditional) are implemented and working. Advanced operators (trigonometric, spatial, statistical, stochastic) are intentionally deferred to Phase 2 per the phased implementation plan.

## Current State

**Phase 1 (COMPLETE):**
- ✅ Arithmetic: +, -, *, /, %, abs(), min(), max()
- ✅ Logical: and, or, not
- ✅ Comparison: ==, !=, <, <=, >, >=
- ✅ Conditional: if-then-else (ternary)
- ✅ Function calls: Built-in functions
- ✅ Path access: bar.*, vfs.*, temporal.*
- ✅ Literals: int, float, bool, list

**Phase 2 (DEFERRED):**
- ⏸️ Trigonometric: sin(), cos(), tan(), asin(), acos(), atan()
- ⏸️ Spatial: distance(), within_radius(), angle_to()
- ⏸️ Statistical: mean(), sum(), count(), min_list(), max_list()
- ⏸️ Stochastic: random(), bernoulli(), normal(), uniform()

**Test Coverage:**
- 116 expression tests passing
- All Phase 1 operators systematically tested
- Phase 2 operators not yet implemented (as planned)

## Rationale for Deferral

**Phase 1 Scope:** Core functionality for VFS variables, effects, and spawn conditions
- Basic arithmetic and logic sufficient for MVP
- Complex operators add implementation complexity
- Can be added incrementally without breaking changes

**Phase 2 Scope:** Advanced behaviors and simulations
- Trigonometric functions for physics simulations
- Spatial functions for proximity-based mechanics
- Statistical functions for aggregate calculations
- Stochastic functions for procedural generation

**No Blocker:** Current expression language sufficient for:
- VFS variable definitions
- Effect conditions and value calculations
- Spawn condition evaluation
- All Phase 1-3 curriculum levels

## Phase 2 Implementation Plan

### Trigonometric Operators (3-4 hours)

**Functions:**
- `sin(angle)` - Sine (angle in radians)
- `cos(angle)` - Cosine
- `tan(angle)` - Tangent
- `asin(value)` - Arcsine (returns radians)
- `acos(value)` - Arccosine
- `atan(value)` - Arctangent
- `atan2(y, x)` - Two-argument arctangent

**Use Cases:**
- Physics simulations (projectile motion)
- Circular motion patterns
- Oscillating behaviors (day/night intensity)

**Implementation:**
```python
# src/townlet/world/expression/evaluator.py

def _eval_function_call(self, node: FunctionCall) -> Value:
    if node.name == "sin":
        return math.sin(args[0])
    # ... etc
```

**Tests:** 10-12 tests for trig functions

### Spatial Operators (4-5 hours)

**Functions:**
- `distance(pos1, pos2)` - Euclidean distance between positions
- `within_radius(pos, center, radius)` - Boolean proximity check
- `angle_to(from_pos, to_pos)` - Angle in radians
- `manhattan_distance(pos1, pos2)` - L1 distance

**Use Cases:**
- Proximity-based spawning ("spawn if agent within 5 units")
- Directional effects ("push away from center")
- Area-of-effect mechanics

**Implementation:**
Requires position type in expression language:
```python
# New type: position (x, y) or (x, y, z)
# Path access: agent.position, item.position
```

**Tests:** 8-10 tests for spatial functions

### Statistical Operators (3-4 hours)

**Functions:**
- `mean(list)` - Arithmetic mean
- `sum(list)` - Sum of elements
- `count(list)` - Number of elements
- `min_list(list)` - Minimum value (different from binary min())
- `max_list(list)` - Maximum value
- `median(list)` - Median value
- `std_dev(list)` - Standard deviation

**Use Cases:**
- Aggregate calculations over multiple agents/items
- "Average health of nearby agents"
- "Total gold in inventory"

**Implementation:**
Requires list iteration in evaluator:
```python
def _eval_function_call(self, node: FunctionCall) -> Value:
    if node.name == "mean":
        values = self._eval(args[0])  # Evaluate list
        return sum(values) / len(values)
```

**Tests:** 10-12 tests for statistical functions

### Stochastic Operators (2-3 hours)

**Functions:**
- `random()` - Uniform random [0, 1)
- `random_int(min, max)` - Random integer
- `bernoulli(p)` - Random boolean with probability p
- `normal(mean, std)` - Gaussian distribution
- `uniform(min, max)` - Uniform distribution

**Use Cases:**
- Procedural generation ("random spawn location")
- Probabilistic effects ("20% chance to apply")
- Noise in simulations

**Implementation:**
Requires random number generation in evaluator:
```python
import random

def _eval_function_call(self, node: FunctionCall) -> Value:
    if node.name == "random":
        return random.random()
```

**Determinism Note:** Need to manage random seed for reproducibility

**Tests:** 8-10 tests for stochastic functions (with seed control)

## Acceptance Criteria (Phase 2)

- [ ] All trigonometric functions implemented and tested
- [ ] All spatial functions implemented and tested
- [ ] All statistical functions implemented and tested
- [ ] All stochastic functions implemented and tested
- [ ] Documentation updated with new operators
- [ ] Integration tests show usage in VFS/effects/items
- [ ] No regression in existing expression tests
- [ ] Random seed management for reproducibility

## Evidence

**Source Report:** gap-report-vfs.md (VFS-1 section)
**Phase 1 Status:** Complete (116 tests passing)
**Phase 2 Status:** Deferred as planned
**Documentation:** docs/config-schemas/expressions.md (has Phase 2 roadmap section)

## Implementation Notes

**Design Principles:**
- Add operators incrementally without breaking existing code
- Each operator category can be implemented independently
- Maintain backward compatibility with Phase 1 expressions
- Follow existing parser/evaluator patterns

**Testing Strategy:**
- Unit tests for each operator
- Integration tests showing real-world usage
- Edge case tests (NaN, infinity, empty lists, etc.)
- Performance tests (if operators used in hot paths)

**Documentation Updates:**
- Update expressions.md with new operators
- Add examples to schema docs
- Update Phase 2 roadmap section
- Cross-reference from VFS/effects/items docs

**Backward Compatibility:**
- Phase 1 configs continue to work
- New operators are additive (no breaking changes)
- Existing ASTs remain valid

## References

- Expression parser: `src/townlet/world/expression/parser.py`
- Expression evaluator: `src/townlet/world/expression/evaluator.py`
- AST nodes: `src/townlet/world/expression/ast_nodes.py`
- Documentation: `docs/config-schemas/expressions.md` (Phase 2 roadmap)
- Phase plan: `docs/plans/2025-11-06-variables-and-features-system.md`
