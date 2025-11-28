# [COMP-7] Expression Language Documentation

**Priority:** P1 (Important)
**Category:** Documentation
**Status:** DONE
**Effort:** 3-4 hours

## Description

Expression parser implementation is complete and well-tested (116 tests), but documentation gaps exist. Users need comprehensive reference documentation for the expression language to write VFS variables, effects conditions, and spawn rules.

## Current State

**Implementation:** ✅ COMPLETE
- Parser: `src/townlet/world/expression/parser.py`
- AST nodes: `src/townlet/world/expression/ast_nodes.py`
- Type checker: `src/townlet/world/expression/type_checker.py`
- Evaluator: `src/townlet/world/expression/evaluator.py`

**Test Coverage:** ✅ EXCELLENT
- 116 expression tests passing
- All operators tested
- Edge cases covered

**Documentation:** ✅ COMPLETE
- File: `docs/config-schemas/expressions.md`
- Added integration examples (VFS variables, effect conditions, item spawn conditions)
- Added troubleshooting guide and path namespaces (including item.*)
- Added type system reference and Phase 2 deferred-operators roadmap

## Required Implementation

### Documentation Gaps to Address

#### 1. **Advanced Operators** (Phase 2 deferred)
Document that these operators are planned but not yet implemented:
- Trigonometric: sin(), cos(), tan()
- Spatial: distance(), within_radius()
- Statistical: mean(), sum(), count()
- Stochastic: random(), bernoulli()

Add "Phase 2 Roadmap" section listing deferred operators.

#### 2. **Integration Examples**
Add practical examples showing expression usage in:

**VFS Variables:**
```yaml
vfs_profiles:
  agent_profiles:
    player:
      variables:
        is_critical:
          type: bool
          expression: "bar.energy < 0.2 or bar.health < 0.3"
```

**Effect Conditions:**
```yaml
effects_catalog:
  effects:
    regeneration:
      commands:
        - type: "if"
          condition: "target.bar.health < 0.5"
          then:
            - type: "modify"
              path: "target.bar.health"
              operation: "add"
              value: 0.1
```

**Spawn Conditions:**
```yaml
spawn_rules:
  - item_type: "apple"
    when: "not vfs:is_winter and bar.energy < 0.8"
```

#### 3. **Troubleshooting Guide**
Common errors and solutions:
- "Undefined variable 'vfs:foo'" → Check vfs_profiles.yaml
- "Type mismatch: expected bool, got int" → Use comparison operators
- "Circular dependency detected" → Review variable dependencies
- "Cannot access item.* in global scope" → Scope restrictions

#### 4. **Path Access Reference**
Document all valid path prefixes:
- `bar.*` - Agent bars (energy, health, etc.)
- `vfs.*` - VFS variables (global, agent, item scopes)
- `self.bar.*`, `self.vfs.*` - Current agent in effects
- `target.bar.*`, `target.vfs.*` - Target agent in effects
- `item.vfs.*` - Item variables (in item context)
- `temporal.*` - Time variables (hour, day_progress)

#### 5. **Type System Reference**
Document supported types and conversions:
- Primitive types: int, float, bool
- Container types: list (Phase 1 limited support)
- Reference types: agent_ref, item_ref (opaque in expressions)
- Tensor types: tensor1d, tensor2d (Phase 2)
- Implicit conversions: int → float (allowed)
- Forbidden conversions: bool ↔ numeric (explicit comparison required)

### Documentation Structure

**File:** `docs/config-schemas/expressions.md` (expand existing)

**New Sections to Add:**

```markdown
## Integration Examples

### VFS Variables
[Examples of expressions in vfs_profiles.yaml]

### Effect Conditions
[Examples of expressions in effects_catalog.yaml]

### Spawn Conditions
[Examples of expressions in items spawn rules]

---

## Path Access Reference

### Available Paths

| Path Prefix | Context | Example | Description |
|-------------|---------|---------|-------------|
| `bar.*` | All | `bar.energy` | Agent meter values |
| `vfs.*` | VFS-enabled | `vfs:is_raining` | VFS variable access |
| `self.*` | Effects | `self.bar.health` | Current agent |
| `target.*` | Effects | `target.vfs:gold` | Target agent |
| `item.*` | Item context | `item.vfs:durability` | Item variables |
| `temporal.*` | Time-enabled | `temporal.hour` | Current game time |

---

## Type System

### Supported Types

- **int**: Integer values (1, 42, -10)
- **float**: Floating-point values (0.5, 3.14, -2.7)
- **bool**: Boolean values (true, false)
- **list**: Homogeneous lists (Phase 1 limited support)

### Implicit Conversions

✅ **Allowed:**
- int → float: `bar.energy * 10` (10 converts to 10.0)

❌ **Forbidden:**
- bool ↔ numeric: Use explicit comparison
  - Wrong: `bar.energy and bar.health`
  - Right: `bar.energy > 0 and bar.health > 0`

---

## Troubleshooting

### Common Errors

#### "Undefined variable 'vfs:foo'"
**Cause:** Variable not defined in vfs_profiles.yaml
**Solution:** Add variable to appropriate profile (global/agent/item)

#### "Type mismatch: expected bool, got float"
**Cause:** Using numeric value where boolean required (e.g., if condition)
**Solution:** Use comparison operator: `bar.energy > 0.5` instead of `bar.energy`

[... more error cases ...]

---

## Phase 2 Roadmap

### Deferred Operators

The following operators are planned for Phase 2 but not yet implemented:

**Trigonometric:**
- `sin(angle)`, `cos(angle)`, `tan(angle)`
- `asin(value)`, `acos(value)`, `atan(value)`

**Spatial:**
- `distance(pos1, pos2)` - Euclidean distance
- `within_radius(pos, center, radius)` - Proximity check

**Statistical:**
- `mean(list)`, `sum(list)`, `count(list)`
- `min(list)`, `max(list)`

**Stochastic:**
- `random()` - Uniform [0,1)
- `bernoulli(p)` - Random boolean with probability p
- `normal(mean, std)` - Gaussian distribution

See Phase 2 implementation plan for details.
```

## Acceptance Criteria

- [ ] Advanced operators documented as Phase 2 roadmap
- [ ] Integration examples added (VFS, effects, spawn rules)
- [ ] Path access reference complete with all prefixes
- [ ] Type system documented (types, conversions, restrictions)
- [ ] Troubleshooting guide with 5+ common errors
- [ ] All examples tested and valid
- [ ] Cross-references to other schema docs
- [ ] Updated table of contents

## Evidence

**Source Report:** gap-report-compiler.md (COMP-7 section)
**Existing Docs:** docs/config-schemas/expressions.md (826 lines - good foundation)
**Test Coverage:** 116 expression tests (src/townlet/world/expression/)
**Integration:** VFS profiles, effects, items all use expressions

## Implementation Notes

**Documentation Style:**
- Follow existing schema doc format
- Use tables for reference material
- Include runnable YAML examples
- Link to related schema docs

**Testing Examples:**
Before adding examples to docs, validate they work:
```bash
# Create test config with example expression
# Compile with UniverseCompiler
# Verify expression parses and type-checks
```

**Cross-References:**
- Link expressions.md from vfs-profiles.md
- Link expressions.md from effects.md
- Link expressions.md from items.md
- Add "See also" sections

## References

- Documentation file: `docs/config-schemas/expressions.md` (expand)
- Implementation: `src/townlet/world/expression/` (parser, AST, type checker, evaluator)
- Test examples: `tests/test_townlet/unit/universe/test_vfs_expression_schema.py`
- Integration: VFS profiles, effects catalog, items spawn rules
