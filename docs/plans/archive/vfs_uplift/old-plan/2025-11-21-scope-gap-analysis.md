# World Compiler: Scope Gap Analysis

**Date:** 2025-11-21
**Branch:** `vfs,effects,items`
**Purpose:** Cross-check documentation review findings against unified plan deliverables

## Executive Summary

The unified plan (`2025-11-19-unified-world-compiler-plan.md`) promised **full implementation** of all World Compiler components. The documentation review reveals **significant scope gaps** - multiple features documented but not fully implemented, or implemented partially without clear "Not Yet Implemented" markers.

**Gap Severity:**
- 🔴 **Critical**: Features promised in plan, documented as complete, but stubbed/not implemented
- 🟡 **Moderate**: Features promised in plan, partially implemented, unclear status
- 🟢 **Minor**: Documentation accuracy issues not affecting functionality

## Scope Gaps by Phase

### Phase 1: Expression Language Foundation ✅ (Mostly Complete)

**Plan Promise** (lines 78-144):
- "Parse expressions to AST"
- "Type checking & validation"
- "Runtime evaluation context"
- 60+ tests passing

**Actual Delivery:**
- ✅ Parser works (pyparsing with infixNotation)
- ✅ Type checker works (type inference implemented)
- ✅ Evaluator works (GPU tensor operations)
- ✅ Tests exist and pass

**Gaps Identified:**

#### 🟢 Minor: Division Type Inference Unclear
- **Plan statement**: No explicit type rules documented
- **Review finding**: Documentation states `int / int → float`, actual behavior unclear
- **Impact**: Users may write incorrect expressions
- **Root cause**: Plan didn't specify division type semantics
- **Severity**: Minor (likely documentation error, not implementation gap)

#### 🟢 Minor: Operator Precedence Table Wrong
- **Plan statement**: "Handle operator precedence" (line 124)
- **Review finding**: Documentation shows unary ops at level 2, should be level 1
- **Impact**: Users write expressions with wrong grouping expectations
- **Root cause**: Documentation error, implementation likely correct (pyparsing defines precedence)
- **Severity**: Minor (documentation fix only)

**Phase 1 Verdict:** ✅ **95% Complete** - Minor documentation fixes needed, core functionality delivered

---

### Phase 2: VFS Profiles (Dynamic) ⚠️ (Partially Complete)

**Plan Promise** (lines 147-206):
- "Expression-based, dynamic variables"
- "Reference types" (`agent_ref`, `item_ref`, `affordance_ref`, `effect_ref`)
- "Scoped registry (global/agent/item)"
- Vector types: `vec2i`, `vec3i`, `vecNi`, `vecNf` (line 98)
- 50+ tests passing

**Actual Delivery:**
- ✅ Expression-based variables work
- ✅ Scoped registry implemented (global/agent/item)
- ✅ Tests pass (50+)

**Gaps Identified:**

#### 🟡 Moderate: Vector Types Missing from Documentation
- **Plan statement**: Line 98 explicitly lists `vec2i`, `vec3i`, `vecNi`, `vecNf`
- **Review finding**: Documentation only lists `int`, `float`, `bool`, `str`
- **Impact**: Users cannot use vector types (or don't know they exist)
- **Root cause**: Implementation may exist in code comments/tests but not exposed in schema/docs
- **Severity**: Moderate (unclear if types are fully implemented or just planned)

#### 🟡 Moderate: Reference Types Unclear
- **Plan statement**: Line 98 explicitly lists `agent_ref`, `item_ref`, `affordance_ref`, `effect_ref`
- **Review finding**: Reference types not clearly documented
- **Impact**: Users cannot use reference types for entity relationships
- **Root cause**: Implementation status unclear (may be in code but not documented)
- **Severity**: Moderate (potentially unfinished feature)

#### 🟡 Moderate: Two Schema Formats Exist
- **Plan statement**: No mention of multiple formats
- **Review finding**: `vfs_profiles.yaml` and `variables_reference.yaml` both exist
- **Impact**: Users confused about which format to use
- **Root cause**: Legacy VFS format not fully deprecated
- **Severity**: Moderate (architectural inconsistency)

#### 🟡 Moderate: Evaluation Timing Unclear
- **Plan statement**: Decision D2 (lines 586-628) specifies "Hybrid (mark-and-sweep) with eager fallback"
- **Review finding**: Documentation doesn't explain when expressions evaluate (compile-time vs every tick)
- **Impact**: Performance expectations unclear, users don't understand cost model
- **Root cause**: Documentation doesn't reflect architectural decision D2
- **Severity**: Moderate (affects performance understanding)

**Phase 2 Verdict:** ⚠️ **75% Complete** - Core functionality works, but advanced features (vector types, reference types) unclear or missing

---

### Phase 3: Effects System 🔴 (Incomplete - Major Gaps)

**Plan Promise** (lines 209-280):
- "Implement Effects as the command pipeline foundation"
- **Task 3.3** (lines 256-259): "Implement command execution (**modify, spawn_effect, spawn_item, if, for_each, etc.**)"
- "Effect lifecycle (**spawn, tick, despawn, interrupt**)"
- "All command types execute correctly" (success criteria line 277)
- 75+ tests passing

**Actual Delivery:**
- ✅ Effect catalog loading works
- ✅ Command pipeline parser works
- ✅ `modify` and `if` commands work
- ✅ Lifecycle hooks on_spawn, on_tick, on_despawn work
- ✅ Reapply policies work (stack/renew/merge/replace)
- ✅ 75+ tests pass

**Gaps Identified:**

#### 🔴 CRITICAL: spawn_effect Command Stubbed
- **Plan statement**: Line 256 explicitly requires "Implement command execution (...**spawn_effect**...)"
- **Review finding**: Returns dummy effect ID, doesn't actually spawn effects
- **Source**: `src/townlet/effects/executor.py:90-96` (placeholder implementation)
- **Impact**: Cascade effects (effect spawning effect) don't work
- **Root cause**: Implementation incomplete despite plan requirement
- **Severity**: CRITICAL (core feature promised but not delivered)

#### 🔴 CRITICAL: spawn_item Command Not Implemented
- **Plan statement**: Line 256 explicitly requires "Implement command execution (...**spawn_item**...)"
- **Review finding**: Stub in schema, not in executor
- **Impact**: Effects cannot create items (documented feature doesn't work)
- **Root cause**: Implementation incomplete despite plan requirement
- **Severity**: CRITICAL (core feature promised but not delivered)

#### 🔴 CRITICAL: for_each Command Raises NotImplementedError
- **Plan statement**: Line 256 explicitly requires "Implement command execution (...**for_each**, etc.)"
- **Review finding**: `raise NotImplementedError("for_each iteration")` at `src/townlet/effects/executor.py:120`
- **Impact**: Multi-target effects don't work
- **Root cause**: Implementation incomplete despite plan requirement
- **Severity**: CRITICAL (core feature promised but not delivered)

#### 🟡 Moderate: on_interrupt Lifecycle Hook Not Executed
- **Plan statement**: Line 264 requires "Effect lifecycle (**spawn, tick, despawn, interrupt**)"
- **Review finding**: EffectManager has no code path that calls on_interrupt
- **Source**: `src/townlet/effects/manager.py:137-200` (no on_interrupt calls)
- **Impact**: Users write on_interrupt handlers that never execute
- **Root cause**: Lifecycle implementation incomplete (3/4 hooks work)
- **Severity**: Moderate (documented feature doesn't work, but less critical than commands)

**Phase 3 Verdict:** 🔴 **60% Complete** - Core infrastructure works, but **3 of 5 command types not implemented** despite explicit plan requirement

---

### Phase 4: Items System 🔴 (Incomplete - Critical Integration Gap)

**Plan Promise** (lines 283-362):
- "Implement Items using Effects for all interactions"
- **Task 4.4** (lines 341-346): "Action Handlers (2 days) - GET action, USE_SLOT_N actions, DROP_SLOT_N actions"
- "Action masking (GET masked when inventory full, etc.)"
- **Task 4.5** (lines 348-353): "Wire ItemManager into VectorizedHamletEnv"
- "Agents can pickup/use/drop items" (success criteria line 358)
- 70+ tests passing

**Actual Delivery:**
- ✅ ItemManager implemented (spawn/despawn, lifecycle)
- ✅ Inventory state tracking works
- ✅ Action handlers exist (GET, USE_SLOT_N, DROP_SLOT_N)
- ✅ Tests pass (70+)

**Gaps Identified:**

#### 🔴 CRITICAL: Item Actions NOT Automatically Added
- **Plan statement**: Task 4.4 says "Action Handlers" will be implemented as part of Items system
- **Plan implication**: Line 349 "Wire ItemManager into VectorizedHamletEnv" suggests automatic integration
- **Review finding**: Actions must be MANUALLY configured in `actions.yaml` (not automatic)
- **Impact**: **MAJOR INTEGRATION ISSUE** - Users enable Items but have no way to interact
- **Root cause**: Plan didn't explicitly specify "automatic action registration," but architectural intent was clear
- **Severity**: CRITICAL (breaks user expectations, makes Items nearly unusable without manual config)

#### 🟡 Moderate: Inventory Slot → Action Mapping Unclear
- **Plan statement**: Line 342 mentions "USE_SLOT_N actions" (plural)
- **Review finding**: Documentation doesn't explain how slot count maps to action IDs
- **Impact**: Users don't know how many actions to configure for N inventory slots
- **Root cause**: Documentation doesn't explain generation pattern (USE_SLOT_0, USE_SLOT_1, ..., USE_SLOT_{N-1})
- **Severity**: Moderate (usability issue, not functionality gap)

**Phase 4 Verdict:** 🔴 **70% Complete** - Core Items system works, but **critical integration gap** (manual action config) breaks architectural vision

---

### Phase 5: Affordance Migration ✅ (Complete)

**Plan Promise** (lines 365-406):
- "Migrate existing affordances from EffectPipeline to Effects system"
- "Delete `effect_pipeline.py`"
- "All curriculum levels migrated"
- Zero regressions

**Actual Delivery:**
- ✅ All curriculum levels migrated to Effects syntax
- ✅ EffectPipeline code deleted (confirmed in conversation history)
- ✅ Tests pass

**Gaps Identified:**
- None

**Phase 5 Verdict:** ✅ **100% Complete** - Full migration successful

---

### Phase 6: Integration & Testing ⚠️ (Complete but Inaccurate Documentation)

**Plan Promise** (lines 409-460):
- "End-to-end testing, performance validation, documentation"
- **Task 6.1**: 10-15 integration tests
- **Task 6.2**: <5% performance regression
- **Task 6.3**: Complete documentation suite (expressions.md, vfs-profiles.md, effects.md, items.md, world-compiler-guide.md)

**Actual Delivery:**
- ✅ 16 integration tests created (13 passing, 3 xfailed)
- ✅ Performance: 86% improvement (far exceeded target)
- ✅ Documentation: 5 files created (~4,500 lines)

**Gaps Identified:**

#### 🟡 Moderate: Documentation Describes Unimplemented Features as Complete
- **Plan statement**: Task 6.3 requires "Complete documentation suite"
- **Review finding**: Documentation presents unimplemented commands (spawn_effect, spawn_item, for_each) as complete
- **Impact**: Users write configs that don't work, then file bug reports
- **Root cause**: Documentation agents read schema files (which have stubs) and assumed implementation complete
- **Severity**: Moderate (documentation accuracy, not functionality gap)

**Phase 6 Verdict:** ⚠️ **90% Complete** - Tests and performance excellent, but documentation doesn't reflect incomplete Phase 3 implementation

---

## Summary: What SHOULD Have Been Delivered vs What WAS Delivered

### Promised Scope (from Unified Plan)

| Component | Plan Lines | Promised Features | Status |
|-----------|------------|-------------------|--------|
| **Expression Language** | 78-144 | Parser, type checker, evaluator, 60+ tests | ✅ 95% |
| **VFS Profiles** | 147-206 | Dynamic variables, vector types, reference types, 50+ tests | ⚠️ 75% |
| **Effects System** | 209-280 | **All command types**, full lifecycle, 75+ tests | 🔴 60% |
| **Items System** | 283-362 | Full integration, action handlers, 70+ tests | 🔴 70% |
| **Affordance Migration** | 365-406 | Delete EffectPipeline, migrate all levels | ✅ 100% |
| **Integration & Testing** | 409-460 | E2E tests, performance, accurate docs | ⚠️ 90% |

### Critical Scope Gaps (NOT Delivered Despite Plan Promise)

#### 🔴 Effects System - 3 Commands Not Implemented
**Plan explicit promise** (line 256):
> "Implement command execution (modify, spawn_effect, spawn_item, if, for_each, etc.)"

**Actual state:**
- ❌ `spawn_effect`: Stubbed (returns dummy ID)
- ❌ `spawn_item`: Not implemented
- ❌ `for_each`: Raises NotImplementedError

**Impact:** Effects cannot cascade (spawn other effects) or create items. Multi-target effects impossible.

**Estimated remaining work:** 4-6 days (Task 3.3 was budgeted 2 days, but clearly incomplete)

#### 🔴 Items System - Action Registration Not Automatic
**Plan implicit promise** (line 349):
> "Wire ItemManager into VectorizedHamletEnv"

**Architectural expectation:** Items system should automatically add GET/USE/DROP actions when enabled

**Actual state:**
- ❌ Actions must be manually configured in `actions.yaml`
- ❌ No documentation of manual config requirement
- ❌ Easy to enable Items but have no way to interact

**Impact:** Users enable Items, see no GET/USE/DROP actions, assume Items broken.

**Estimated remaining work:** 2-3 days (automatic action registration + tests)

#### 🟡 VFS Profiles - Vector/Reference Types Unclear
**Plan explicit promise** (line 98):
> `primitive.py         # scalar, bool, vec2i, vec3i, vecNi, vecNf`
> `reference.py         # agent_ref, item_ref, affordance_ref, effect_ref`

**Actual state:**
- ⚠️ Vector types may exist in code but not documented
- ⚠️ Reference types implementation status unclear

**Impact:** Users cannot use advanced types for entity relationships or spatial data.

**Estimated remaining work:** 1-2 days (if types exist, just documentation; if not, 3-4 days implementation)

---

## Root Cause Analysis

### Why Were Features Documented But Not Implemented?

**Hypothesis 1: Schema-First Development**
- Effects schema defines all command types (modify, spawn_effect, spawn_item, if, for_each)
- Documentation agents read schema files and assumed implementation complete
- No validation that schema → implementation → tests pipeline was complete

**Hypothesis 2: Task Completion Without Success Criteria Verification**
- Phase 3 success criteria (line 277): "All command types execute correctly"
- This was marked complete, but clearly spawn_effect/spawn_item/for_each don't execute
- Suggests tests covered happy path (modify, if) but not all commands

**Hypothesis 3: Phase 6 Documentation Created Before Phase 3/4 Completion**
- Phase 6 documentation describes world as it SHOULD be (per schema)
- Phase 3/4 implementation stopped short of full plan scope
- No reconciliation pass to mark unimplemented features

**Hypothesis 4: Pre-Release Freedom Misapplied**
- "NO backwards compatibility" (CLAUDE.md) interpreted as "can leave features half-done"
- Correct interpretation: "can break APIs without deprecation"
- Incorrect interpretation: "can ship incomplete features without marking as incomplete"

---

## Recommendations

### Option A: Complete Original Scope (High Priority Gaps)

**Recommended for:**
- 🔴 Effects commands (spawn_effect, spawn_item, for_each) - 4-6 days
- 🔴 Item action auto-registration - 2-3 days

**Total:** 6-9 days additional work

**Rationale:** These features were explicitly promised in the plan and have cascade effects:
- Without spawn_effect, effects cannot trigger other effects (breaks design)
- Without spawn_item, effects cannot create world objects (breaks design)
- Without item action auto-registration, Items nearly unusable

### Option B: Document "Not Yet Implemented" (Quick Fix)

**Recommended for:**
- 🟡 Vector types (vec2f, vec3f, etc.)
- 🟡 Reference types (agent_ref, item_ref, etc.)
- 🟡 on_interrupt lifecycle hook

**Total:** 2-3 hours documentation updates

**Rationale:** These features are nice-to-have but not blocking core workflows. Document as "Planned" and users can work around.

### Option C: Accept Scope Reduction (Reset Expectations)

**If time-constrained:**
1. Update unified plan to mark spawn_effect/spawn_item/for_each as "Phase 7: Advanced Effects"
2. Update documentation to clearly mark as "Not Yet Implemented"
3. Add items.md CRITICAL note about manual action configuration

**Total:** 1-2 hours plan/doc updates

**Trade-off:** Breaks architectural vision (Effects as complete command pipeline), but honest about scope.

---

## Decision Matrix

| Gap | Severity | User Impact | Implementation Cost | Recommendation |
|-----|----------|-------------|---------------------|----------------|
| spawn_effect/spawn_item/for_each | 🔴 Critical | Cannot cascade effects or create items | 4-6 days | **Option A: Implement** |
| Item action auto-registration | 🔴 Critical | Items nearly unusable | 2-3 days | **Option A: Implement** |
| on_interrupt hook | 🟡 Moderate | Workaround: use on_despawn | 1-2 days | **Option B: Document** |
| Vector/reference types | 🟡 Moderate | Workaround: scalar values | 3-4 days (if missing) | **Option B: Document** |
| Division type inference docs | 🟢 Minor | User confusion (minor) | 15 minutes | **Fix immediately** |
| Operator precedence table | 🟢 Minor | User confusion (minor) | 10 minutes | **Fix immediately** |

---

## Proposed Fix Plan

### Immediate (Today - 1 hour)
1. Fix critical documentation errors (operator precedence, division type)
2. Add "Implementation Status" section to effects.md marking spawn_effect/spawn_item/for_each as "Not Yet Implemented"
3. Add CRITICAL note to items.md about manual action configuration

### Short-Term (This Week - 2-3 days)
4. Implement item action auto-registration (unblock Items usability)
5. Add implementation status table to world-compiler-guide.md

### Medium-Term (Next Sprint - 4-6 days)
6. Implement spawn_effect, spawn_item, for_each commands (complete Phase 3)
7. Add on_interrupt execution to EffectManager

### Long-Term (Phase 7 - Future)
8. Implement vector types (vec2f, vec3f, vecNi, vecNf) if missing
9. Implement reference types (agent_ref, item_ref, affordance_ref, effect_ref)
10. Add user-controlled `expose_to_obs` per VFS variable (Decision D2 future benefit)

---

## Related Files

- **Unified Plan**: `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- **Review Findings**: `docs/plans/vfs_uplift/2025-11-21-phase-6-documentation-review-findings.md`
- **Phase 6 Summary**: `docs/plans/vfs_uplift/PHASE-6-COMPLETE.md`

---

**Conclusion:** The World Compiler is **80% complete** against original unified plan scope. Core infrastructure is solid, but **critical command types** (spawn_effect, spawn_item, for_each) and **Items auto-registration** remain unfinished despite explicit plan promises. Immediate documentation fixes + 1 week implementation would close scope gap.
