# [DOC-9] Dedicated Edge Case Policies Documentation

**Priority:** P2 (Minor)
**Category:** Documentation
**Status:** PARTIAL
**Effort:** 2 hours

## Description

Edge case handling policies are documented in plan files but not consolidated into a dedicated, discoverable documentation file. Need single source of truth for "what happens when..." edge cases (empty VFS profiles, missing affordances, zero items, etc.). Currently policies are scattered across implementation plans and code comments.

## Current State

**Existing documentation (scattered):**
- Edge case policies mentioned in VFS uplift plans
- Implementation notes in code comments
- Some edge cases documented in schema docs
- No centralized edge case reference

**Examples of documented edge cases:**
- Empty VFS profiles (valid, no variables initialized)
- Missing affordances (config valid, no affordances spawn)
- Zero items in catalog (valid, no item spawning)
- Agent with no VFS profile (falls back to default profile)
- Expression evaluation errors (fail gracefully or raise?)

**Problem:**
- Developers must search multiple files to understand edge case behavior
- Inconsistent handling across similar edge cases
- No single policy document to consult
- Undocumented edge cases discovered during development

## Required Implementation

### Create Edge Case Policies Document (2 hours)

**File:** `docs/guides/edge-case-policies.md`

**Structure:**
```markdown
# Edge Case Policies

This document defines HAMLET's behavior for edge cases, boundary conditions, and error scenarios. These policies ensure consistent, predictable behavior across the system.

## Philosophy

**Fail Explicit, Not Implicit:**
- Invalid configurations should fail at compile time with clear errors
- Runtime errors should be exceptional, not normal flow
- Ambiguous cases should require explicit configuration

**Graceful Degradation:**
- Missing optional features degrade gracefully (no crash)
- Empty collections are valid (e.g., empty VFS profiles, zero affordances)
- Defaults should be sensible, not arbitrary

**Zero Is Valid:**
- Zero affordances, zero items, zero cascades are all valid configurations
- Minimal configs (1 bar, 0 affordances) should compile and run

---

## VFS System Edge Cases

### Empty VFS Profiles

**Scenario:** `vfs_profiles.yaml` with no variables defined

**Policy:** ✅ **Valid** - Environment runs without VFS observations

**Behavior:**
- VFS registry initializes but stores no variables
- Observations exclude VFS components (obs_dim unaffected by empty VFS)
- No VFS evaluation overhead

**Example:**
\```yaml
# vfs_profiles.yaml
version: "1.0"
global_profile:
  variables: {}  # Empty - valid
agent_profiles: {}
item_profiles: {}
\```

### Missing VFS Profiles File

**Scenario:** No `vfs_profiles.yaml` in config pack

**Policy:** ❌ **Invalid** - Compile-time error

**Rationale:** Post-VFS uplift, all configs must explicitly declare VFS structure (even if empty)

**Error message:**
\```
ValidationError: Missing required file: vfs_profiles.yaml
All config packs must include VFS profiles declaration (use empty profiles if no VFS needed)
\```

### Agent Without Profile

**Scenario:** Agent spawned but has no VFS profile defined

**Policy:** ✅ **Valid** - Agent uses empty profile (no VFS variables)

**Behavior:**
- Agent exists in registry with scope="agent"
- Agent has no VFS variables (empty variable dict)
- Agent observations exclude VFS component

### Expression Evaluation Errors

**Scenario:** VFS expression fails at runtime (division by zero, undefined variable)

**Policy:** ❌ **Raises RuntimeError** - Expression errors are bugs, not normal flow

**Rationale:**
- Expressions should be validated at compile time (type checker)
- Runtime expression errors indicate invalid config or implementation bug
- Better to fail loudly than silently propagate NaN/Inf

**Mitigation:**
- Type checker (COMP-9) validates expressions at compile time
- Expression evaluator includes safeguards (clamp, handle edge cases)

**Example:**
\```python
# Division by zero in expression
expression: "vfs:numerator / vfs:denominator"  # If denominator=0, raises RuntimeError

# Fixed with safeguard
expression: "vfs:numerator / max(vfs:denominator, 0.001)"  # Clamp denominator
\```

---

## Items System Edge Cases

### Zero Items in Catalog

**Scenario:** `items_catalog.yaml` with no items defined

**Policy:** ✅ **Valid** - Environment runs without items

**Behavior:**
- ItemManager initializes but manages no items
- No items spawn
- GET/DROP/USE actions become no-ops
- Observations exclude item VFS component

### Item Spawn with No Space

**Scenario:** Spawn rule triggers but all grid cells occupied

**Policy:** ✅ **Skip spawn** - Item spawn fails silently, retry next tick

**Behavior:**
- Spawn rule remains active (will retry next tick)
- No error raised (normal flow, not exceptional)
- Logging: Debug message "Spawn failed: No available positions"

### Item With No VFS Profile

**Scenario:** Item definition has no `vfs_profile` field

**Policy:** ❌ **Invalid** - Compile-time error

**Rationale:** Post-VFS uplift, all items must have VFS profile (use empty profile if no variables)

**Error message:**
\```
ValidationError: Item 'apple' missing required field 'vfs_profile'
All items must declare VFS profile (use empty profile if no variables needed)
\```

---

## Effects System Edge Cases

### Empty Effects Catalog

**Scenario:** `effects_catalog.yaml` with no effects defined

**Policy:** ✅ **Valid** - Environment runs without effects

**Behavior:**
- EffectManager initializes but manages no effects
- Spawn effect commands become no-ops
- No runtime overhead from empty effects

### Effect Cascade Exceeds Depth Limit

**Scenario:** Effect chain exceeds MAX_CASCADE_DEPTH (10 levels)

**Policy:** ❌ **Raises RuntimeError** - Infinite cascade prevention

**Behavior:**
- Cascade execution stops at depth 10
- RuntimeError raised with clear message
- Prevents runaway effect chains (infinite loops)

**Error message:**
\```
RuntimeError: Effect cascade exceeded maximum depth 10
Check for circular effect references or infinite spawn chains
\```

### Observable Effect Slots Exceeded

**Scenario:** Agent has 15 active effects but only 5 observation slots

**Policy:** ✅ **Show first 5 effects** - Overflow effects not visible to agent

**Behavior:**
- Take first 5 observable effects (by activation order)
- Remaining effects still active (just not in observations)
- Logging: Debug message "Agent has 15 effects, showing 5 in observations"

---

## Bars and Cascades Edge Cases

### Bar Value Clamped to [min, max]

**Scenario:** Bar modification would push value outside [min_value, max_value]

**Policy:** ✅ **Clamp to bounds** - Values never exceed limits

**Behavior:**
- `energy = 1.2` → clamped to `1.0` (max_value)
- `health = -0.3` → clamped to `0.0` (min_value)
- Clamping logged at debug level

### Zero Decay Rate

**Scenario:** Bar with `decay_rate: 0.0`

**Policy:** ✅ **Valid** - Bar never decays naturally

**Behavior:**
- Bar value constant unless explicitly modified
- Use case: Money bar (doesn't decay, only changes via actions)

### Cascade Target Bar Missing

**Scenario:** Cascade references bar that doesn't exist

**Policy:** ❌ **Invalid** - Compile-time error

**Behavior:**
- Validation error during compilation
- Error message lists available bars and suggests typo fix (if COMP-13 implemented)

---

## Substrate Edge Cases

### Agent Out of Bounds (Boundary Modes)

**Scenario:** Agent action would move outside substrate bounds

**Policy:** **Depends on boundary_mode:**
- `clamp`: Agent stays at boundary (movement fails)
- `wrap`: Agent wraps to opposite edge (toroidal topology)
- `bounce`: Agent bounces back (elastic collision)
- `sticky`: Agent moves slowly at boundary (friction)

**Behavior documented in:** `docs/config-schemas/substrate.md`

### Zero Grid Size

**Scenario:** `grid_size: [0, 0]`

**Policy:** ❌ **Invalid** - Compile-time error

**Behavior:**
- Validation error: Grid size must be positive integers
- Minimum grid size: [1, 1]

---

## Training Edge Cases

### Replay Buffer Not Full

**Scenario:** Training starts but buffer < min_replay_size

**Policy:** ✅ **Skip training** - Wait until buffer fills

**Behavior:**
- Agent continues exploring (epsilon-greedy)
- No gradients computed
- Training starts once buffer reaches min_replay_size

### Episode Length Exceeded

**Scenario:** Episode reaches max_episode_length without done

**Policy:** ✅ **Force episode termination** - Return done=True

**Behavior:**
- Episode truncated at max_episode_length
- Final observation marked as terminal
- Prevents infinite episodes

---

## Observation Edge Cases

### NaN or Inf in Observations

**Scenario:** Observation tensor contains NaN or Inf values

**Policy:** ❌ **Raises RuntimeError** - Invalid observations are bugs

**Rationale:**
- NaN/Inf breaks gradient computation
- Indicates bug in observation building or VFS evaluation
- Better to fail loudly than propagate corruption

**Mitigation:**
- Observation builder validates output (no NaN/Inf)
- VFS normalization clamps values
- Expression evaluator handles edge cases (div by zero)

### Observation Dimension Mismatch

**Scenario:** Compiled obs_dim doesn't match actual observation shape

**Policy:** ❌ **Raises RuntimeError** - Dimension mismatch indicates implementation bug

**Behavior:**
- Environment initialization validates obs_dim
- Runtime check on every observation
- Clear error message with expected vs actual dims

---

## Compilation Edge Cases

### Circular Dependencies

**Scenario:** VFS variable A depends on B, B depends on A

**Policy:** ❌ **Invalid** - Compile-time error (when dependency checker implemented)

**Behavior:**
- Dependency graph validation detects cycles
- Error message shows circular dependency chain

**Future:** Topological sort for evaluation order

### Missing Required Config File

**Scenario:** Config pack missing `substrate.yaml` or `bars.yaml`

**Policy:** ❌ **Invalid** - Compile-time error

**Behavior:**
- Clear error message listing missing required files
- Required files: substrate, bars, training, vfs_profiles

### Unknown Schema Version

**Scenario:** Config file has `version: "2.0"` but only "1.0" supported

**Policy:** ❌ **Invalid** - Compile-time error

**Behavior:**
- Version validation error
- Message lists supported versions
- Prompts user to upgrade or downgrade config

---

## Summary Table

| Edge Case | Policy | Phase |
|-----------|--------|-------|
| Empty VFS profiles | ✅ Valid | Compile |
| Missing VFS profiles file | ❌ Invalid | Compile |
| Zero items in catalog | ✅ Valid | Compile |
| Item spawn no space | ✅ Skip spawn | Runtime |
| Effect cascade depth exceeded | ❌ Error | Runtime |
| Bar value out of bounds | ✅ Clamp | Runtime |
| NaN in observations | ❌ Error | Runtime |
| Circular dependencies | ❌ Error | Compile |
| Unknown schema version | ❌ Error | Compile |

**Legend:**
- ✅ Valid: Handled gracefully, no error
- ❌ Invalid: Raises error with clear message
- Phase: When policy is enforced (Compile = static validation, Runtime = dynamic behavior)

---

## Contributing

When implementing new features:

1. **Document edge cases** in this file
2. **Add validation** at compile time when possible
3. **Handle gracefully** at runtime when compile-time validation not feasible
4. **Test edge cases** explicitly (add tests for boundary conditions)

**Questions?** Check this document first, then consult implementation plans or ask in design discussions.
```

## Acceptance Criteria

- [ ] `docs/guides/edge-case-policies.md` created
- [ ] Edge case policies for all major systems documented (VFS, items, effects, bars, substrate, training)
- [ ] Each edge case includes: scenario, policy, behavior, rationale, examples
- [ ] Clear distinction between compile-time (invalid) vs runtime (handled) errors
- [ ] Summary table of common edge cases
- [ ] Contributing guidelines for new edge cases
- [ ] Linked from main documentation index
- [ ] Policies consistent with actual implementation

## Evidence

**Source Report:** gap-report-final.md (lines 71-94), gap-report-testing-docs.md
**Current state:** Policies scattered across plan files and code comments

## Implementation Notes

**Why P2 (not P1/P0):** Edge cases are handled correctly in implementation (via unit tests and code). This is about documentation consolidation for developer reference, not fixing bugs. Useful but not critical.

**Documentation Purpose:**
1. **Developer reference:** Quick lookup for "what happens when..."
2. **Design consistency:** Ensure similar edge cases handled similarly
3. **Onboarding:** Help new contributors understand system behavior
4. **Testing guide:** List of edge cases to test

**Organization:**
- Group by system (VFS, items, effects, bars, substrate, training)
- Each edge case: Scenario → Policy → Behavior → Rationale
- Summary table for quick reference
- Examples where helpful

**Policy Types:**
- **✅ Valid (graceful):** Edge case is normal, handle gracefully (no error)
- **❌ Invalid (error):** Edge case is error, fail with clear message
- **⚠️ Warning:** Edge case is suspicious, log warning but continue

**Consolidation Sources:**
1. VFS uplift plan files (edge case sections)
2. Code comments (edge case handling)
3. Unit tests (edge case test descriptions)
4. Implementation experience (discovered edge cases)

**Maintenance:**
- Update when new edge cases discovered
- Update when policies change
- Keep synchronized with implementation

## References

- Documentation file: `docs/guides/edge-case-policies.md` (to be created)
- Source material: VFS uplift plans, code comments, unit tests
- Related: Schema documentation (references edge case policies)
