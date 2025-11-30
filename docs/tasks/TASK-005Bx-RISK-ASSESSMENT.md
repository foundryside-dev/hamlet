# TASK-005Bx Risk Assessment Summary

**Date**: 2025-11-30
**Assessed By**: Research/Review Agent
**Task**: TASK-005Bx-VFS2-RESIDUAL.md
**Status**: CONDITIONAL GO (with revisions)

---

## Executive Summary

**VERDICT**: Proceed with **18-26 hour implementation** (not 10-14) using **release-quality architecture**.

**Key Finding**: Expression engine is 90% complete (verified), but integration has 3 hidden architectural gaps not in original task estimate.

---

## Critical Discoveries

### 1. VariableRegistry Lacks Batched Update API ⛔
**Impact**: +3-4 hours
**Resolution**: Add `set_partial(variable_id, values, agent_indices)` method

**Evidence**: Line 270 of `registry.py` - current `set()` requires full tensor replacement

### 2. ActionMetadata DTO Extension Required ⚠️
**Impact**: +2-3 hours
**Resolution**: Add `writes: tuple[CompiledWriteSpec, ...]` field, handle serialization

**Evidence**: Line 14-30 of `action_metadata.py` - no field for compiled writes

### 3. AST Serialization Strategy Needed ⚠️
**Impact**: +2 hours
**Resolution**: Store expression string (not AST), re-parse on checkpoint load

**Evidence**: Line 509 of `compiled.py` - checkpoint serialization requires JSON-safe data

---

## Validated Claims

✅ **Expression engine is production-ready**
- 2,428 lines across 8 files (verified)
- 120 unit tests (verified)
- Used in effects, items, universe compiler (verified)
- GPU-native, fully functional

✅ **Only integration work remains**
- Parser, evaluator, type checker all exist
- No new expression features needed
- Can copy patterns from effects system

❌ **"10-14 hours" estimate**
- Underestimated by 60-80%
- Actual: 18-26 hours for RC-1 quality

---

## Architectural Decisions for RC-1

### Decision 1: Proper API (No Hacks)
**Question**: Batched variable updates?
**Answer**: Add `VariableRegistry.set_partial()` method
- ✅ Clean API for release
- ✅ Proper access control
- ✅ Shape validation
- ❌ +3-4 hours (acceptable for RC-1)

**Rejected**: Direct `_storage` access (pre-release hack, not RC-1 quality)

### Decision 2: Expression Storage
**Question**: Store AST or string?
**Answer**: Store expression string, parse on-demand
- ✅ Checkpoint serialization (JSON-safe)
- ✅ Small overhead (parser fast ~0.1ms)
- ✅ Clean architecture

**Rejected**: Custom AST serialization (+6 hours, unnecessary complexity)

### Decision 3: Permission Validation
**Question**: When to check writable_by?
**Answer**: Compile time (with runtime defensive check)
- ✅ Fail fast with clear errors
- ✅ Config authors get immediate feedback
- ✅ Runtime is defensive (shouldn't happen)

---

## Risk Mitigation

### HIGH RISKS (Addressed)

1. **VariableRegistry API** - RESOLVED: Add set_partial() method
2. **Shape Mismatches** - MITIGATED: Runtime validation with clear errors
3. **Checkpoint Serialization** - RESOLVED: Store strings, re-parse on load

### MEDIUM RISKS (Handled)

1. **Permission Enforcement** - Add compile-time check
2. **Device Placement** - set_partial() handles internally

### LOW RISKS (Monitored)

1. **Performance Overhead** - Benchmark, expect <1%
2. **Scope Creep** - Task explicitly excludes new features

---

## Effort Breakdown (Revised)

| Component | Original | Revised | Reason |
|-----------|----------|---------|--------|
| VariableRegistry API | 0h | **3-4h** | Missing batched update API |
| Compile-time parsing | 2-3h | **4-6h** | DTO changes, serialization, permissions |
| Runtime execution | 3-4h | **6-8h** | AST caching, shape validation, device handling |
| Unit tests | 3-4h | **5-7h** | Registry API, permissions, checkpoints |
| Integration tests | 1-2h | **2-3h** | Regression + checkpoint compatibility |
| Documentation | 1h | **1-2h** | Config examples, migration notes |
| **TOTAL** | **10-14h** | **18-26h** | **+60-80%** |

**Confidence**: High (75%) - Expression engine stable, patterns exist in effects

---

## RC-1 Release Checklist

### Must Complete

- [ ] VariableRegistry.set_partial() with permission validation
- [ ] ActionMetadata DTO extension with checkpoint compatibility
- [ ] Compile-time permission checks (writable_by)
- [ ] Runtime shape validation with clear errors
- [ ] Device handling (GPU/CPU transfers)
- [ ] Comprehensive unit tests (registry, permissions, shapes)
- [ ] Integration tests (end-to-end + regression)
- [ ] L0-L3 configs still work (no breakage)
- [ ] BUG-36 closed with working demonstration
- [ ] TASK-005B marked complete

### Documentation

- [ ] Config example showing writes syntax
- [ ] Permission requirements documented
- [ ] Migration guide for enabling writes
- [ ] CLAUDE.md updated (VFS2 complete)

---

## Go/No-Go Decision

### ✅ GO IF:

1. Accept 18-26 hours (not 10-14)
2. Accept proper API additions (no storage hacks)
3. Accept expression string storage (small re-parse overhead)
4. Commit to comprehensive testing (RC-1 quality)

### ❌ NO-GO IF:

1. Cannot accept 60-80% effort increase
2. Require quick-and-dirty implementation
3. Cannot add new VariableRegistry API

---

## Recommendation

**PROCEED** with TASK-005Bx for RC-1 completion.

**Rationale**:
- VFS2 is 90% done - cannot ship incomplete
- WriteSpec API exists but dormant - misleading
- Expression engine is production-ready
- Integration patterns exist (effects system)
- 18-26 hours is acceptable for RC-1 blocker

**Next Steps**:
1. Update TASK-005Bx.md with revised estimates
2. Mark as RC-1 blocker
3. Schedule 18-26 hours for completion
4. No shortcuts - do it properly

---

## Evidence Files Examined

**Total**: 25+ files reviewed

**Expression Engine** (verified production-ready):
- `/src/townlet/world/expression/` - 8 files, 2,428 lines
- 120 unit tests in `/tests/test_townlet/unit/world/expression/`
- 56 commits to expression module

**Integration Points** (verified usage):
- `effects/compiler.py:8` - uses ExpressionParser
- `effects/executor.py` - evaluates AST at runtime
- `vfs/evaluator.py` - VFSEvaluator with mark-and-sweep
- `universe/compiler.py` - validation integration

**API Gaps** (verified missing):
- Line 270: `registry.py` - set() requires full replacement
- Line 14-30: `action_metadata.py` - no writes field
- Line 1686: `vectorized_env.py` - direct storage access (hack)

**Patterns to Copy** (verified working):
- Line 55: `effects/compiler.py` - expression parsing
- Line 87: `vfs/evaluator.py` - evaluation pattern
- Line 1823: `vectorized_env.py` - batched meter updates
