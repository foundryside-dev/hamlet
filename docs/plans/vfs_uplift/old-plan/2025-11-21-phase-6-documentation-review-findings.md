# Phase 6: Documentation Review Findings

**Date:** 2025-11-21
**Branch:** `vfs,effects,items`
**Review Status:** ✅ COMPLETE

## Overview

Five specialized code-reviewer agents audited the Phase 6 documentation suite (~4,500 lines) against actual implementation. This report compiles their findings and proposes fixes.

## Summary of Findings

| Document | Severity | Status | Key Issues |
|----------|----------|--------|------------|
| expressions.md | 🔴 Critical | Needs fixes | Division type inference, precedence table, API mismatch |
| vfs-profiles.md | 🟡 Moderate | Needs clarification | Schema format confusion, missing vector types |
| effects.md | 🔴 Critical | Needs fixes | Unimplemented features presented as complete |
| items.md | 🔴 Critical | Needs fixes | Item actions NOT automatic (major integration issue) |
| world-compiler-guide.md | 🟢 Minor | Excellent | 95% accurate, minor clarity improvements |

## Detailed Findings

### 1. expressions.md (826 lines) - CRITICAL ISSUES

**Issue 1.1: Division Type Inference Incorrect**
- **Documentation states**: `int / int → float`
- **Actual behavior**: `int / int → int` (integer division)
- **Impact**: Users will write incorrect expressions expecting float results
- **Fix**: Update type inference table in "Type System" section
- **Line reference**: Type inference rules section

**Issue 1.2: Operator Precedence Table Wrong**
- **Documentation states**: Unary operators (-, not) at level 2
- **Actual behavior**: pyparsing infixNotation puts first item (unary) at HIGHEST precedence (level 1)
- **Impact**: Users will write expressions with wrong operator grouping
- **Fix**: Correct precedence table:
  ```
  Level 1 (Highest): Unary (-, not)
  Level 2: Multiplicative (*, /, %)
  Level 3: Additive (+, -)
  Level 4: Relational (<, <=, >, >=)
  Level 5: Equality (==, !=)
  Level 6: Logical AND (and)
  Level 7: Logical OR (or)
  Level 8 (Lowest): Ternary (if/else)
  ```
- **Line reference**: Operator precedence table section

**Issue 1.3: ExecutionContext API Mismatch**
- **Documentation shows**: `context.get("bar.energy")` → scalar float
- **Actual behavior**: `context.get("bar.energy")` → batched tensor [N]
- **Two ExecutionContext classes exist**:
  - `townlet.world.expression.context.ExecutionContext` (expression evaluation)
  - `townlet.effects.context.ExecutionContext` (effects execution)
- **Impact**: Example code won't work as shown
- **Fix**: Add note about batched tensors, clarify which ExecutionContext is documented
- **Line reference**: Examples throughout document

### 2. vfs-profiles.md (999 lines) - MODERATE ISSUES

**Issue 2.1: Schema Format Confusion**
- **Two formats exist in codebase**:
  1. `vfs_profiles.yaml` (static: initial_value, dynamic: expression)
  2. `variables_reference.yaml` (legacy VFS format)
- **Documentation focuses on vfs_profiles.yaml only**
- **Impact**: Users unaware of two-file configuration requirement
- **Fix**: Add section explaining relationship between files
- **Line reference**: Schema section

**Issue 2.2: Missing Vector Types**
- **Documentation lists**: int, float, bool, str
- **Actual implementation includes**: vec2f, vec3f, vecNi, vecNf (in code comments/tests)
- **Impact**: Users can't use vector types properly
- **Fix**: Add vector types to type system section with examples
- **Line reference**: Type system section

**Issue 2.3: Runtime vs Compile-Time Confusion**
- **Documentation mixes**: Compile-time spec generation and runtime value updates
- **Unclear**: When expressions are evaluated (compile-time vs every tick)
- **Impact**: Performance expectations unclear
- **Fix**: Add "When Expressions Evaluate" section explaining:
  - Static variables: initial_value at spawn time only
  - Dynamic variables: expression evaluated every tick
  - Observation specs: computed at compile time
- **Line reference**: Throughout document

### 3. effects.md (~650 lines) - CRITICAL ISSUES

**Issue 3.1: on_interrupt Lifecycle Hook Not Executed**
- **Documentation states**: "on_interrupt: Runs when effect is interrupted by another effect"
- **Actual implementation**: EffectManager has no code path that calls on_interrupt
- **Impact**: Users will write on_interrupt handlers that never execute
- **Fix**: Add "Implementation Status" section:
  - ✅ Implemented: on_spawn, on_tick, on_despawn
  - ⚠️ Planned: on_interrupt (schema exists, not executed)
- **Line reference**: Lifecycle hooks section
- **Source**: `src/townlet/effects/manager.py:137-200` (no on_interrupt calls)

**Issue 3.2: spawn_effect Command Stubbed**
- **Documentation shows**: Full spawn_effect examples with effect parameters
- **Actual implementation**: Returns dummy effect ID, doesn't actually spawn
- **Source**: `src/townlet/effects/executor.py:90-96` (placeholder implementation)
- **Impact**: Cascade effects (effect spawning effect) won't work
- **Fix**: Mark as "Not Yet Implemented" in command reference

**Issue 3.3: spawn_item Command Not Implemented**
- **Documentation shows**: spawn_item examples
- **Actual implementation**: Stub in schema, not in executor
- **Impact**: Effects can't create items (documented feature doesn't work)
- **Fix**: Mark as "Not Yet Implemented" in command reference

**Issue 3.4: for_each Command Raises NotImplementedError**
- **Documentation shows**: for_each loop examples
- **Actual implementation**: `raise NotImplementedError("for_each iteration")`
- **Source**: `src/townlet/effects/executor.py:120`
- **Impact**: Multi-target effects won't work
- **Fix**: Mark as "Not Yet Implemented" in command reference

### 4. items.md (~650 lines) - CRITICAL INTEGRATION ISSUE

**Issue 4.1: Item Actions NOT Automatically Added**
- **Documentation states**: "GET, USE_SLOT_N, DROP_SLOT_N actions automatically added to action space when Items enabled"
- **Actual implementation**: Actions must be manually configured in `actions.yaml`
- **Source**: No auto-registration code in ItemManager or action composition
- **Impact**: MAJOR INTEGRATION ISSUE - users will enable Items but have no way to interact
- **Fix**: Add CRITICAL section:
  ```yaml
  # REQUIRED: Manual Action Configuration
  # Items do NOT automatically add actions. You must add these to actions.yaml:

  custom_actions:
    - action_id: GET
      source: items
      # ... configuration
    - action_id: USE_SLOT_0
      source: items
    # ... etc
  ```
- **Line reference**: Integration section, quick start guide

**Issue 4.2: Inventory Slot Configuration Unclear**
- **Documentation mentions num_inventory_slots but doesn't explain action generation**
- **Actual pattern**: USE_SLOT_0, USE_SLOT_1, ..., USE_SLOT_{N-1}, DROP_SLOT_0, etc.
- **Fix**: Add explicit table showing action IDs for different slot counts

### 5. world-compiler-guide.md (1,479 lines) - MINOR ISSUES (95% Accurate)

**Issue 5.1: "Not Yet Implemented" Ambiguity**
- **Some features marked "Not Yet Implemented" but actually work** (e.g., expression evaluation)
- **Some features NOT marked but actually incomplete** (e.g., spawn_effect)
- **Impact**: Minor confusion about implementation status
- **Fix**: Add clear "Implementation Status" table at document start

**Issue 5.2: CLI Examples Could Be More Specific**
- **Current examples**: Generic paths
- **Better examples**: Actual curriculum levels from repo
- **Fix**: Use `configs/L0_0_minimal/` as example throughout

## Recommendations

### Priority 1: Critical Fixes (Required for Phase 6 Completion)

1. **Fix expressions.md operator precedence table** (10 min)
2. **Add "Implementation Status" to effects.md** (15 min)
3. **Add CRITICAL manual action config section to items.md** (20 min)

### Priority 2: Moderate Fixes (Important for Usability)

4. **Add vector types to vfs-profiles.md** (15 min)
5. **Add "When Expressions Evaluate" to vfs-profiles.md** (20 min)
6. **Add two-file configuration explanation to vfs-profiles.md** (15 min)

### Priority 3: Minor Improvements (Nice to Have)

7. **Add implementation status table to world-compiler-guide.md** (10 min)
8. **Update examples to use real curriculum levels** (15 min)

**Total estimated time**: ~2 hours for all fixes

## Proposed Fix Plan

### Task 1: Fix Critical Documentation Errors (45 minutes)

**Files to modify**:
- `docs/config-schemas/expressions.md` (precedence table, type inference)
- `docs/config-schemas/effects.md` (implementation status section)
- `docs/config-schemas/items.md` (manual action configuration)

**Approach**: Targeted edits to critical sections only

### Task 2: Clarify VFS Configuration (50 minutes)

**Files to modify**:
- `docs/config-schemas/vfs-profiles.md` (vector types, evaluation timing, two-file setup)

**Approach**: Add new sections without removing existing content

### Task 3: Polish User Guide (25 minutes)

**Files to modify**:
- `docs/guides/world-compiler-guide.md` (status table, better examples)

**Approach**: Minor enhancements for clarity

## Decision Point

**Option A: Fix Now (Complete Phase 6 Properly)**
- Fix all Priority 1 issues (~45 min)
- Phase 6 documentation fully accurate
- Users won't hit critical integration issues

**Option B: Mark Phase 6 Complete, Fix Later**
- Documentation exists (~4,500 lines)
- Known accuracy issues documented
- Fix in separate task/phase

**Recommendation**: **Option A** - The items.md issue is critical enough to warrant immediate fix. Users enabling Items will have no way to interact without manual action configuration, which is a major integration failure not a minor documentation inaccuracy.

## Related Files

- **Review Reports**: (In agent transcripts, not persisted to disk)
- **Phase 6 Plan**: `docs/plans/vfs_uplift/2025-11-20-phase-6-integration-testing.md`
- **Phase 6 Summary**: `docs/plans/vfs_uplift/PHASE-6-COMPLETE.md`

---

**Next Steps**: Await decision on fix approach (Option A vs Option B)
