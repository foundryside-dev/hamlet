# P1 Issues - Prioritized Execution Order

**Generated:** 2025-11-22
**Total P1 Issues:** 9
**Total Estimated Effort:** ~3-4 days
**Recommendation:** Execute in order listed below for optimal risk reduction

---

## Priority Tier 1: Critical Path (Must Fix First)

### 🔴 Priority 1A: P1-RUN-12 - Integration Test Failures
**File:** `issues/P1-RUN-12-integration-test-failures.md`
**Effort:** 4-8 hours
**Impact:** BLOCKS validation of runtime correctness

**Why First:**
- 4/5 VFS runtime tests failing means core functionality may be broken
- Fixes import error that blocks P1-RUN-8 performance benchmarks
- Must verify system works before fixing anything else
- High risk if left unfixed (unknown runtime bugs)

**Blockers:** None
**Blocks:** P1-RUN-8 (performance benchmarks)

**Quick Wins:**
1. Fix EffectDefinition import error (5 minutes)
2. Add 'effects' to ObservationField.semantic_type enum (10 minutes)
3. Debug 4 VFS runtime evaluation tests (2-4 hours)

---

### 🟠 Priority 1B: P1-RUN-8 - Performance Benchmark Import Error
**File:** `issues/P1-RUN-8-performance-benchmark-import.md`
**Effort:** 1 hour (15 min fix + 45 min run benchmarks)
**Impact:** Cannot verify <5% overhead target

**Why Second:**
- Trivial import fix (same as RUN-12)
- Unblocks performance verification
- Must confirm VFS doesn't add excessive overhead before merge
- Risk: System may be slower than expected (unlikely but critical to know)

**Blocked By:** P1-RUN-12 (same import error)
**Blocks:** Performance validation for merge confidence

**Action:**
1. Fix import in test_component_benchmarks.py
2. Run benchmarks to verify <5% overhead
3. Document results in validation report

---

### 🟡 Priority 1C: P1-RUN-9 - Checkpoint Serialization
**File:** `issues/P1-RUN-9-checkpoint-serialization.md`
**Effort:** 4-6 hours
**Impact:** Cannot resume training with item VFS state

**Why Third:**
- Data loss risk: Item state not persisted across training sessions
- Affects reproducibility (core value proposition)
- Relatively simple fix (add field to checkpoint payload)
- Users will hit this quickly in long training runs

**Blockers:** None
**Blocks:** Long-term training reproducibility

**Action:**
1. Add registry.item_vfs to checkpoint_utils.py (2 hours)
2. Add restore logic (1 hour)
3. Add integration test (1-2 hours)
4. Verify checkpoint save/load roundtrip (1 hour)

---

## Priority Tier 2: User Experience (Fix Before Public Release)

### 🟢 Priority 2A: P1-DOC-8 - VFS Integration Guide Update
**File:** `issues/P1-DOC-8-vfs-integration-guide-outdated.md`
**Effort:** 4-6 hours
**Impact:** Documentation doesn't reflect current implementation

**Why Fourth:**
- **Pre-release context:** No migration needed, just "how it works" documentation
- Guide describes old Phase 1 patterns instead of current Phase 2 implementation
- Should show current best practices (experiment-level scoping, item_profiles)
- Do while implementation is fresh in mind

**Blockers:** None
**Blocks:** User adoption, external contributions

**Action:**
1. Update vfs-integration-guide.md to show current patterns (3 hours)
   - Remove "migration" framing, focus on "how to configure"
   - Show experiment-level vfs_profiles.yaml structure
   - Document item_profiles pattern
   - Add complete working examples
2. Update/remove any outdated Phase 1 references (1 hour)

---

### 🟢 Priority 2B: P1-DOC-6 - Reference Config Complete Example
**File:** `issues/P1-DOC-6-reference-config-missing-sections.md`
**Effort:** 2-3 hours
**Impact:** Users lack comprehensive config reference showing all systems

**Why Fifth:**
- Quick win (copy/paste from existing L1/L2 configs)
- Single-file reference showing how everything works together
- Complements DOC-8 (users can see complete working example)
- Low effort, high value for onboarding

**Blockers:** None (can do in parallel with DOC-8)
**Blocks:** User onboarding, discoverability

**Action:**
1. Add vfs_profiles.yaml section showing all 3 scopes (1 hour)
2. Add items.yaml section showing VFS binding (1 hour)
3. Add effects.yaml section if missing (30 min)
4. Update TOC (15 min)

---

### 🟢 Priority 2C: P1-DOC-10 - Observation Modes Not Documented
**File:** `issues/P1-DOC-10-observation-modes-not-documented.md`
**Effort:** 4 hours
**Impact:** Users don't know about observation management modes

**Why Sixth:**
- Advanced feature documentation
- Less critical than migration guide (DOC-8)
- Can be done alongside other doc updates
- Useful for power users

**Blockers:** None
**Blocks:** Advanced configuration understanding

**Action:**
1. Document full_auto, max_compact, full_manual modes (2 hours)
2. Add examples for each mode (1 hour)
3. Update vfs-profiles.md schema (1 hour)

---

## Priority Tier 3: Features (Can Defer to Post-Merge)

### 🔵 Priority 3A: P1-EFF-11 - Event Command
**File:** `issues/P1-EFF-11-event-command.md`
**Effort:** 2-3 hours
**Impact:** Syntactic sugar for effect cascading

**Why Seventh:**
- Workaround exists (spawn_effect cascades)
- Nice-to-have, not required for functionality
- Low risk to defer
- Can add when users request it

**Blockers:** None
**Blocks:** None (optional syntactic sugar)

**Action:** Defer to post-merge sprint unless time permits

---

### 🔵 Priority 3B: P1-EFF-12 - Sample Command
**File:** `issues/P1-EFF-12-sample-command.md`
**Effort:** 1 day
**Impact:** Stochastic sampling syntactic sugar

**Why Eighth:**
- Workaround exists (random() in expressions)
- Advanced distributions not needed for current curriculum
- Can add when needed for complex stochastic behaviors
- Low priority compared to runtime/doc issues

**Blockers:** None
**Blocks:** None (optional feature)

**Action:** Defer to post-merge sprint unless time permits

---

### 🔵 Priority 3C: P1-VFS-1 - Expression Operator Coverage
**File:** `issues/P1-VFS-1-expression-operator-coverage.md`
**Effort:** 3-5 days (can be phased)
**Impact:** Only 40% of advanced operators implemented

**Why Last:**
- **Largest effort** (3-5 days)
- Basic operators (40%) sufficient for current needs
- Missing: trig, temporal, spatial, statistical, stochastic
- Can add incrementally as curriculum levels require
- No immediate use cases for missing operators

**Blockers:** None
**Blocks:** Advanced curriculum levels (L4+)

**Action:**
- Defer to backlog
- Add operators incrementally as needed
- Prioritize based on curriculum requirements

**Phased Approach:**
1. Phase 1: Temporal operators (for L3) - 1 day
2. Phase 2: Statistical operators (for L5) - 1 day
3. Phase 3: Spatial operators (for L4 multi-zone) - 1 day
4. Phase 4: Trig/stochastic (as needed) - 2 days

---

## Execution Strategy

### Week 1 (3 days) - CRITICAL PATH + UX

**Day 1: Runtime Validation**
- Morning: P1-RUN-12 - Fix integration test failures (4-8 hours)
- Afternoon: P1-RUN-8 - Fix benchmark import, run verification (1 hour)

**Day 2: Runtime Persistence + Doc Start**
- Morning: P1-RUN-9 - Checkpoint serialization (4-6 hours)
- Afternoon: Start P1-DOC-8 - VFS integration guide (2 hours)

**Day 3: Documentation Completion**
- Morning: P1-DOC-8 - Update VFS guide to show current patterns (4 hours)
- Afternoon: P1-DOC-6 - Add complete config example (2-3 hours)

**DELIVERABLES:** All runtime issues fixed, documentation shows "how it works now"
**CONFIDENCE:** High (merge-ready)

**Note:** Pre-release = no migration docs needed, just clear "current usage" docs

---

### Week 2 (Optional) - FEATURES

**Day 4: Advanced Documentation**
- P1-DOC-10 - Observation modes (4 hours)

**Day 5: Syntactic Sugar (if time permits)**
- P1-EFF-11 - Event command (2-3 hours)
- P1-EFF-12 - Sample command (1 day)

**DEFER TO BACKLOG:**
- P1-VFS-1 - Expression operators (3-5 days, add incrementally)

---

## Priority Matrix

```
           HIGH IMPACT                LOW IMPACT
         ┌─────────────────┬─────────────────────┐
HIGH     │ P1-RUN-12 🔴    │ P1-DOC-8 🟢        │
RISK     │ P1-RUN-8  🟠    │ P1-DOC-6 🟢        │
         │ P1-RUN-9  🟡    │ P1-DOC-10 🟢       │
         ├─────────────────┼─────────────────────┤
LOW      │                 │ P1-EFF-11 🔵       │
RISK     │                 │ P1-EFF-12 🔵       │
         │                 │ P1-VFS-1  🔵       │
         └─────────────────┴─────────────────────┘
```

---

## Quick Reference

### Must Fix Before Merge (Tier 1)
1. ✅ P1-RUN-12 - Integration tests (4-8 hours) - CRITICAL
2. ✅ P1-RUN-8 - Performance benchmarks (1 hour) - CRITICAL
3. ✅ P1-RUN-9 - Checkpoint serialization (4-6 hours) - HIGH RISK

**Total Tier 1 Effort:** 9-15 hours (~2 days)

### Fix Before Public Release (Tier 2)
4. ✅ P1-DOC-8 - Update VFS guide to current patterns (4-6 hours)
5. ✅ P1-DOC-6 - Complete reference config example (2-3 hours)
6. ✅ P1-DOC-10 - Document observation modes (4 hours)

**Total Tier 2 Effort:** ~1.5 days

**Pre-release philosophy:** No "migration" docs - just clear "how to configure it now" documentation

### Can Defer to Post-Merge (Tier 3)
7. 🔵 P1-EFF-11 - Event command (2-3 hours) - DEFER
8. 🔵 P1-EFF-12 - Sample command (1 day) - DEFER
9. 🔵 P1-VFS-1 - Expression operators (3-5 days) - DEFER, add incrementally

**Total Tier 3 Effort:** 4-6 days (optional)

---

## Risk-Based Decision Tree

```
START: Ready to merge?
│
├─ Are integration tests passing? (RUN-12)
│  ├─ NO → FIX IMMEDIATELY (4-8 hours) 🔴
│  └─ YES → Continue
│
├─ Can we verify <5% overhead? (RUN-8)
│  ├─ NO → FIX IMMEDIATELY (1 hour) 🟠
│  └─ YES → Continue
│
├─ Is checkpoint serialization working? (RUN-9)
│  ├─ NO → FIX BEFORE MERGE (4-6 hours) 🟡
│  └─ YES → Continue
│
├─ Going public soon?
│  ├─ YES → Fix all Tier 2 docs (2 days) 🟢
│  └─ NO → Can defer docs to post-merge
│
└─ Need advanced features?
   ├─ YES → Evaluate Tier 3 case-by-case 🔵
   └─ NO → MERGE NOW, defer Tier 3
```

---

## Summary

**Minimum for Merge (Tier 1):** 2 days
- Runtime validation (RUN-12, RUN-8)
- Data persistence (RUN-9)

**Ideal for Merge (Tier 1 + 2):** 4 days
- + User documentation (DOC-8, DOC-6, DOC-10)

**Complete P1 Backlog (All tiers):** 8-10 days
- + Syntactic sugar features (EFF-11, EFF-12)
- + Advanced operators (VFS-1)

**Recommendation:** Execute Tier 1 (2 days) → Merge → Execute Tier 2 (2 days) → Defer Tier 3 to backlog
