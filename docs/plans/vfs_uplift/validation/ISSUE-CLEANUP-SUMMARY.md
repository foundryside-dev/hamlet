# Issue Cleanup Summary

**Date:** 2025-11-22
**Action:** Removed unnecessary issues (pre-release context)

---

## Issues Deleted (4 files)

### 1. P2-DOC-7: Migration Guide Not User-Facing ❌ DELETED
**Reason:** Migration guides not needed for pre-release with zero users
- Pre-release philosophy: No "how to migrate" docs, just "how it works now" docs
- Instead: Update existing guides to show current patterns (P1-DOC-8)

### 2. P2-DOC-6: Reference Config Missing Sections ❌ DELETED
**Reason:** Duplicate of P1-DOC-6
- Same issue described at different priority levels
- Kept P1-DOC-6 (4 hours) as the canonical issue

### 3. P2-TEST-20: Performance Benchmark Import Error ❌ DELETED
**Reason:** Duplicate of P1-RUN-8
- Both describe same EffectDefinition import error
- Kept P1-RUN-8 as it correctly identifies this as blocking performance verification

### 4. P2-ITEM-12: Custom Item Commands ❌ DELETED
**Reason:** Intentionally out of scope, not a requirement
- Marked as "Intentionally Deferred to Future" in own description
- Phase 4+ feature, workaround exists (effects on standard actions)
- Not a gap or bug, just a future enhancement idea

---

## Remaining Issues

**Total:** 16 issues (down from 20)

### P1 Issues (9 files)
1. P1-VFS-1 - Expression operator coverage (40% → 100%)
2. P1-EFF-11 - Event command (syntactic sugar)
3. P1-EFF-12 - Sample command (stochastic sampling)
4. P1-RUN-8 - Performance benchmark import error
5. P1-RUN-9 - Checkpoint serialization
6. P1-RUN-12 - Integration test failures
7. P1-DOC-6 - Reference config missing sections
8. P1-DOC-8 - VFS integration guide (update to current patterns)
9. P1-DOC-10 - Observation modes documentation

### P2 Issues (7 files)
1. P2-COMP-16 - VFS observation marking (verification needed)
2. P2-COMP-20 - Scoping enforcement (verification needed)
3. P2-DOC-9 - Edge case policies document
4. P2-ITEM-8 - Spawn conditions VFS predicates
5. P2-SUCCESS-1 - Typo suggestions (fuzzy matching)
6. P2-SUCCESS-2 - VFS evaluator test coverage (22% → 80%)
7. P2-SUCCESS-3 - Environment integration coverage (4% → 60%)

---

## Files Already in done/ (from previous work)

**17 completed issues** (not moved, already there):
- P1-COMP-1, P1-COMP-5, P1-COMP-7, P1-COMP-9, P1-COMP-11, P1-COMP-17
- P1-DOC-6 (older version), P1-ITEM-6, P1-ITEM-8, P1-RUN-8 (older version), P1-VFS-6
- P2-COMP-19, P2-EFF-7, P2-EFF-17, P2-TEST-failures, P2-VFS-4
- P1-COMP-1-seven-stage-pipeline-test-plan

**Note:** These were completed in earlier validation phases and remain in done/ for historical reference.

---

## Summary

**Before cleanup:** 20 issue files
**After cleanup:** 16 issue files
**Deleted:** 4 files (2 duplicates, 1 not-needed-for-pre-release, 1 intentionally-out-of-scope)

**Pre-release principle applied:**
- No migration documentation (users to migrate don't exist)
- Focus on "how to configure it now" instead of "how to upgrade from old version"
- Only track actual gaps/bugs, not future enhancement ideas

**Issue quality improved:**
- No duplicates
- No out-of-scope features masquerading as issues
- Clear distinction between P1 (must fix) and P2 (nice to have)
