# VFS Uplift Gap Analysis - Issue Index

**Generated:** 2025-11-22 (Updated with COMP-7/8/9 corrections)
**Source Report:** `docs/plans/vfs_uplift/validation/reports/gap-report-final.md`
**Total Issues:** 15 (0 P0 + 7 P1 + 8 P2)

---

## Overview

This directory contains individual issue files for each gap identified in the VFS uplift validation gap analysis. Each issue file provides:
- Detailed description of what's missing or incomplete
- Current state and required implementation
- Acceptance criteria
- Effort estimates
- Implementation notes and references

**Status Summary:**
- **P0 (Critical):** 0 issues - All critical requirements complete ✅
- **P1 (Important):** 8 issues - Runtime integration, spawn rules, benchmarks, DSL operators (10-12 days total effort)
- **P2 (Minor):** 8 issues - Polish, nice-to-have features (18-22 days total effort)

**Note:** COMP-7, COMP-8, COMP-9 (expression language foundation) previously listed as P0 gaps have been confirmed as fully implemented and removed from issue tracking.

---

## Priority 0 (Critical)

**None** - All P0 requirements complete ✅

**Expression Language Foundation (COMP-7, COMP-8, COMP-9):**
Previously identified as P0 gaps, these have been confirmed as **fully implemented**:

- **COMP-7: Expression parser** ✅ COMPLETE
  - Implementation: src/townlet/world/expression/parser.py (251 lines)
  - pyparsing-based parser with packrat optimization

- **COMP-8: AST node types** ✅ COMPLETE
  - Implementation: src/townlet/world/expression/ast_nodes.py (259 lines)
  - All required nodes (Constant, Variable, PathAccess, BinaryOp, UnaryOp, FunctionCall, IfThenElse)

- **COMP-9: Type checker** ✅ COMPLETE
  - Implementation: src/townlet/world/expression/type_checker.py (313 lines)
  - Bottom-up type inference with complete type system

**Total:** 1,099 lines in expression module, fully integrated into effects compiler, executor, VFS evaluator, and profiles.

**Test Coverage:** 4 test files (performance benchmarks, integration, edge cases, schema validation)

**Issue Files:** Deleted (requirements confirmed complete)

---

## Priority 1 (Important) - Runtime Integration & Advanced Features

**Total Effort:** 8-10 days
**Recommendation:** Complete in next sprint after merge

### Compiler (2 issues - 6 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P1-COMP-1](./P1-COMP-1-seven-stage-pipeline.md) | Seven-stage pipeline explicit structure | 4 hours | PARTIAL |
| [P1-COMP-17](./P1-COMP-17-profile-binding-validation.md) | Items-VFS profile binding validation | 2 hours | PARTIAL |

### VFS (1 issue - 1-2 days)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P1-VFS-6](./P1-VFS-6-mark-and-sweep-integration.md) | Mark-and-sweep runtime integration | 1-2 days | PARTIAL |

**Impact:** Optimization feature. Evaluator runs in EAGER mode (evaluates all variables) until mark-and-sweep fully wired. Functional correctness maintained.

### Items (2 issues - 3-4 days)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P1-ITEM-6](./P1-ITEM-6-advanced-spawn-rules.md) | Advanced spawn rules (fixed/grid/scripted placement, diverse schedules) | 2-3 days | PARTIAL |
| [P1-ITEM-8](./P1-ITEM-8-spawn-conditions.md) | Spawn conditions (VFS predicates) | 1 day | MISSING |

**Impact:** Advanced item spawning for Phase 4+ scenarios. Current random + periodic spawning sufficient for Phase 1-3.

### Runtime (1 issue - 1 day)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P1-RUN-8](./P1-RUN-8-performance-benchmarks.md) | Performance benchmarks (<5% overhead validation) | 1 day | PARTIAL |

**Impact:** Infrastructure exists, no formal validation that <5% overhead target is met. Based on efficient patterns, overhead likely <1%.

### Documentation (1 issue - 4 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P1-DOC-6](./P1-DOC-6-reference-config-v21.md) | Reference config v2.1 (locate or create) | 4 hours | UNCLEAR |

**Impact:** Discoverability issue. Users can piece together complete config from templates and schema docs.

---

## Priority 2 (Minor) - Polish & Nice-to-Have

**Total Effort:** 20-25 days (not urgent)
**Recommendation:** Address as time permits, defer most to Phase 4+

### Compiler (2 issues - 4.5 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-COMP-13](./P2-COMP-13-typo-suggestions.md) | Typo suggestions in error messages (Levenshtein distance) | 4 hours | MISSING |
| [P2-COMP-19](./P2-COMP-19-vfs-profiles-version.md) | VFSProfilesConfig missing version field | 30 minutes | MISSING |

### VFS (2 issues - 5-7 days)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-VFS-4](./P2-VFS-4-reference-types-runtime.md) | Reference types runtime support (agent_ref, item_ref traversal) | 3-4 days | PARTIAL |
| [P2-VFS-12](./P2-VFS-12-tensor-types.md) | Tensor types (tensor1d/2d/Nd with shape specification) | 2-3 days | PARTIAL |

**Impact:** Advanced VFS features for Phase 4+ (complex state representations, inter-agent references).

### Effects (2 issues - 5 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-EFF-7](./P2-EFF-7-observable-effects.md) | Observable effects in observations | 4 hours | PARTIAL |
| [P2-EFF-17](./P2-EFF-17-cascade-depth-limit-test.md) | Cascade depth limit test | 1 hour | PARTIAL |

**Impact:** Visualization and safety validation. Effects work correctly, just need observation integration and test coverage.

### Items (1 issue - Phase 4+ feature)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-ITEM-12](./P2-ITEM-12-custom-item-commands.md) | Custom item commands (REPAIR, COMBINE, etc.) | 2-3 days | MISSING |

**Impact:** Advanced item interaction for Phase 4+ gameplay (crafting, progression, inventory management).

### Testing (1 issue - 2 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-TEST-22](./P2-TEST-22-vfs-smoke-config.md) | VFS smoke test config pack | 2 hours | MISSING |

**Impact:** Convenience feature for faster VFS validation. VFS already tested extensively via L0-L3 configs and 298 unit tests.

### Documentation (2 issues - 4 hours)

| Issue | Requirement | Effort | Status |
|-------|-------------|--------|--------|
| [P2-DOC-9](./P2-DOC-9-edge-case-policies.md) | Dedicated edge-case-policies.md | 2 hours | PARTIAL |
| [P2-DOC-10](./P2-DOC-10-observation-management-modes.md) | Observation management modes documentation | 2 hours | PARTIAL |

**Impact:** Documentation consolidation and discoverability. Policies and modes documented in plans, need schema docs.

---

## Issue Categories

### By System

- **Compiler (COMP):** 2 issues (2 P1, 2 P2) - removed 3 P0 issues (confirmed complete)
- **VFS System (VFS):** 3 issues (1 P1, 2 P2)
- **Effects (EFF):** 2 issues (2 P2)
- **Items (ITEM):** 3 issues (2 P1, 1 P2)
- **Runtime (RUN):** 1 issue (1 P1)
- **Testing (TEST):** 1 issue (1 P2)
- **Documentation (DOC):** 3 issues (1 P1, 2 P2)

### By Status

- **MISSING:** 5 issues (2 P1, 3 P2) - removed 3 P0 issues (confirmed complete)
- **PARTIAL:** 9 issues (4 P1, 5 P2) - removed 2 issues now complete
- **UNCLEAR:** 1 issue (1 P1)

---

## Recommended Action Plan

### Immediate (Post-Merge)

**None required** - All P0 requirements complete ✅

**Note:** COMP-7, COMP-8, COMP-9 (expression language foundation) confirmed as fully implemented with 1,099 lines of code across parser.py, ast_nodes.py, and type_checker.py. Zero P0 blockers for merge.

### Short-Term (Next Sprint)

**Week 1-2: Complete P1 Items (4-5 days)**
1. VFS-6: Mark-and-sweep runtime integration (1-2 days)
2. COMP-1: Seven-stage pipeline (4 hours)
3. COMP-17: Profile binding validation (2 hours)
4. RUN-8: Performance benchmarks (1 day)
5. DOC-6: Locate/create reference config (4 hours)
6. ITEM-6: Advanced spawn rules (2-3 days) - Optional, Phase 4+
7. ITEM-8: Spawn conditions (1 day) - Optional, Phase 4+

**Rationale:** Address runtime integration gaps, validation improvements, and documentation polish.

### Long-Term (Future Sprints)

**P2 Items - As Time Permits:**
- Compiler polish: Typo suggestions (4 hours), version field (30 min)
- VFS advanced features: Reference types (3-4 days), tensor types (2-3 days)
- Effects polish: Observable effects (4 hours), depth limit test (1 hour)
- Documentation: Edge case policies (2 hours), observation modes (2 hours)
- Testing: VFS smoke config (2 hours)

**Defer to Phase 4+:**
- ITEM-12: Custom item commands (crafting system)
- VFS-4: Reference types (inter-agent interactions)
- VFS-12: Tensor types (complex state representations)

---

## Issue File Format

Each issue file contains:

### Header
- **Priority:** P0/P1/P2 with category (Critical/Important/Minor)
- **Category:** System (Compiler/VFS/Effects/Items/Runtime/Testing/Documentation)
- **Status:** MISSING/PARTIAL/UNCLEAR
- **Effort:** Estimated implementation time

### Sections
1. **Description:** Brief summary of gap
2. **Current State:** What exists now, what's missing
3. **Required Implementation:** Detailed implementation steps
4. **Acceptance Criteria:** Checklist of completion requirements
5. **Evidence:** Source reports, related requirements, file references
6. **Implementation Notes:** Design decisions, dependencies, priority justification
7. **References:** Source files, test files, documentation

---

## Navigation

**Browse by priority:**
- [P0 Issues](#priority-0-critical) (0 issues - all complete ✅)
- [P1 Issues](#priority-1-important---runtime-integration--advanced-features) (7 issues)
- [P2 Issues](#priority-2-minor---polish--nice-to-have) (8 issues)

**Browse by system:**
- Compiler: COMP-1, COMP-13, COMP-17, COMP-19 (removed COMP-7, COMP-8, COMP-9 - confirmed complete)
- VFS: VFS-4, VFS-6, VFS-12
- VFS DSL: VFS-operators (new)
- Effects: EFF-7, EFF-17
- Items: ITEM-6, ITEM-8, ITEM-12
- Runtime: RUN-8
- Testing: TEST-22
- Documentation: DOC-6, DOC-9, DOC-10

**Source Reports:**
- [Final Report](../reports/gap-report-final.md)
- [Compiler Report](../reports/gap-report-compiler.md)
- [VFS Report](../reports/gap-report-vfs.md)
- [Effects Report](../reports/gap-report-effects.md)
- [Items Report](../reports/gap-report-items.md)
- [Runtime Report](../reports/gap-report-runtime.md)
- [Testing & Docs Report](../reports/gap-report-testing-docs.md)

---

**Last Updated:** 2025-11-22 (Corrected with COMP-7/8/9 completions)
**Issue Count:** 15 (0 P0, 7 P1, 8 P2)
**Total Estimated Effort:** 26-32 days (P0: 0d, P1: 8-10d, P2: 18-22d)
