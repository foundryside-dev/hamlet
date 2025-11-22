# VFS Uplift Requirements Summary - EXPANDED

**Date:** 2025-11-23
**Status:** Ready for Validation
**Total Requirements:** 246 (157 original + 89 new)

---

## Summary

The requirements checklist has been expanded by analyzing all 5 VFS uplift plan documents comprehensively, including the detailed command reference. The expansion adds **89 new requirements** across **9 new categories**.

---

## Original Requirements (157 total)

From `requirements-checklist.md`:

| Category | Count | Agent |
|----------|-------|-------|
| COMP (Compiler) | 20 | Agent 1 |
| VFS (VFS System) | 15 | Agent 2 |
| EFF (Effects) | 20 | Agent 3 |
| ITEM (Items) | 16 | Agent 4 |
| RUN (Runtime) | 12 | Agent 5 |
| TEST (Testing) | 22 | Agent 6 |
| DOC (Documentation) | 10 | Agent 7 |
| BREAK (Breaking Changes) | 9 | Agent 8 |
| **Derived** | 33 | Agent 9 |
| **TOTAL** | **157** | |

---

## New Requirements (89 total)

From `additional-requirements.md`:

| Category | Count | Description | Priority |
|----------|-------|-------------|----------|
| **CMD** (Command-Specific) | 22 | Detailed command implementation specs (switch, for_each, parallel, reduce, delay, while, emit) | P0-P3 |
| **LIMITS** (Runtime Limits) | 7 | Safety caps and constraints (MAX_COLLECTION_SIZE=256, effect depth=10, delay ticks=1000, scheduled items=10000) | P0 |
| **VFS-EXT** (VFS Extensions) | 8 | Expression XOR initial_value, observation exposure, semantic types, evaluation ordering | P0-P2 |
| **ITEM-EXT** (Items Extensions) | 16 | Placement modes, schedule types, spawn priorities, conditional spawn, tags, metadata, durability | P1-P3 |
| **COMP-EXT** (Compiler Extensions) | 8 | Config gating, feature flags, file layout, hashing, Levenshtein suggestions, file/line tracking | P1-P2 |
| **EFF-EXT** (Effects Extensions) | 8 | on_interrupt hook, observable effects, cascade triggering, sample command, random chance | P2-P3 |
| **RUN-EXT** (Runtime Extensions) | 7 | Eager fallback mode, VFS context, item VFS masking, profile-driven dimensions, zero-stub removal | P0-P1 |
| **TEST-EXT** (Testing Extensions) | 8 | Dimension regression, checkpoint roundtrip, type safety negative tests, reapply policy tests | P1-P2 |
| **DOC-EXT** (Documentation Extensions) | 7 | Command reference, type system, observation modes, reapply policies, expression context | P2-P3 |
| **TOTAL** | **89** | | |

---

## Combined Total: 246 Requirements

**Breakdown by Agent Assignment:**

| Agent | Scope | Original | New | Total |
|-------|-------|----------|-----|-------|
| 1 | Compiler & Schema | COMP (20) | COMP-EXT (8) | **28** |
| 2 | VFS System | VFS (15) | VFS-EXT (8) | **23** |
| 3 | Effects | EFF (20) | EFF-EXT (8) | **28** |
| 4 | **Commands (NEW)** | — | CMD (22) | **22** |
| 5 | Items | ITEM (16) | ITEM-EXT (16) | **32** |
| 6 | Runtime | RUN (12) | RUN-EXT (7), LIMITS (7) | **26** |
| 7 | Testing | TEST (22) | TEST-EXT (8) | **30** |
| 8 | Documentation | DOC (10) | DOC-EXT (7) | **17** |
| 9 | Breaking Changes | BREAK (9), Derived (33) | — | **42** |
| 10 | Synthesis | — | — | **—** |
| **TOTAL** | | **157** | **89** | **246** |

---

## Priority Breakdown

### P0 (Critical - Must Fix Before Merge): 12 requirements

**Safety & Correctness:**
- CMD-FOREACH-1: Iteration cap (MAX_COLLECTION_SIZE=256)
- CMD-FOREACH-2: Nested for_each prohibition
- LIMITS-1 through LIMITS-4: All runtime caps (collection, effect depth, delay, queue)
- VFS-EXT-1: Expression XOR initial_value enforcement
- COMP-EXT-6: Expression rejection in variables_reference.yaml
- RUN-EXT-5: Zero-stub removal

### P1 (High - Core Functionality): 35 requirements

**Command Implementations:**
- CMD-SWITCH-* (3): Switch equality matching, type validation, tensor broadcasting
- CMD-PARALLEL-* (2): Disjoint-write validation, sequential execution
- CMD-REDUCE-* (3): Fixed-size collections, type consistency, required fields
- CMD-DELAY-* (5): time_enabled requirement, delay limits, queue cap, zero-delay semantics, scheduler persistence

**VFS & Items:**
- VFS-EXT-7: Evaluation ordering (global → agent → item)
- VFS-EXT-8: Item profile defaults
- ITEM-EXT-5: Conditional spawn with VFS predicates
- RUN-EXT-1: Eager fallback mode (debug escape hatch)

### P2 (Medium - Important Features): 31 requirements

**Command Details:**
- CMD-FOREACH-* (3): Iterator scope, resolver signatures, no break/continue
- CMD-PARALLEL-3: Empty branch rejection
- ITEM-EXT-1 through ITEM-EXT-4: Item spawn features (placement, schedule, limits, priority)

**VFS & Effects:**
- VFS-EXT-3 through VFS-EXT-6: VFS metadata (exposure, semantic types, profile IDs, dependencies)
- EFF-EXT-3, EFF-EXT-4, EFF-EXT-6, EFF-EXT-7: Effect commands (affordance masking, cascades, sample, random)

**Compiler:**
- COMP-EXT-1, COMP-EXT-2, COMP-EXT-3: Compiler wiring (gating, feature flags, file layout)

### P3 (Low - Polish & Future Work): 23 requirements

**Future Commands:**
- CMD-WHILE-1: While loop (not implemented)
- CMD-EMIT-1: Event emission (not implemented)

**Item Details:**
- ITEM-EXT-12 through ITEM-EXT-14: Item placement details
- ITEM-EXT-6 through ITEM-EXT-11: Item metadata, durability, decay, commands

**Effects & Runtime:**
- EFF-EXT-1, EFF-EXT-2, EFF-EXT-5: Future hooks (on_interrupt, observable effects, events)
- RUN-EXT-6: Debug instrumentation

**Documentation:**
- All DOC-EXT-* (7): Documentation polish

---

## Key Findings

### 1. Command Reference Was Highly Detailed

The `command_reference.md` document contained **22 new command-specific requirements** that weren't captured in the original checklist. These include:

- Precise implementation semantics for each command type
- Runtime limits and caps (MAX_COLLECTION_SIZE, MAX_DELAY_TICKS, etc.)
- Validation rules (nested for_each prohibition, disjoint-write enforcement)
- Future commands explicitly marked as not implemented (while, emit)

### 2. Runtime Limits Were Scattered

Safety-critical limits were mentioned across multiple documents but not consolidated:

- MAX_COLLECTION_SIZE = 256 (for_each, reduce)
- Effect spawn depth = 10 (prevents infinite recursion)
- MAX_DELAY_TICKS = 1,000
- MAX_SCHEDULED_ITEMS = 10,000
- Item pool allocation caps

These are now consolidated in the **LIMITS** category.

### 3. Testing Gaps Identified

Many implementation requirements lacked corresponding test requirements:

- Command-specific tests (22 CMD requirements need dedicated tests)
- Limit enforcement tests (boundary conditions)
- Type safety negative tests (compile errors on type mismatches)
- Reapply policy tests (one per policy: stack, renew, merge, replace)

### 4. Documentation Needs Expansion

Several areas need comprehensive documentation:

- Command reference DSL guide (all commands, syntax, semantics)
- Type system reference (primitives, references, tensors)
- Observation management modes (full_auto, max_compact, full_manual)
- Reapply policy examples
- Expression context variables

---

## Recommended Validation Strategy

### Phase 1: Priority Validation (P0 Requirements)

**Focus:** Safety-critical requirements that could cause runtime failures

1. **Verify runtime caps are enforced:**
   - LIMITS-1 through LIMITS-4 (MAX_COLLECTION_SIZE, effect depth, delay ticks, queue cap)
   - CMD-FOREACH-1, CMD-FOREACH-2 (iteration cap, nested prohibition)

2. **Verify correctness requirements:**
   - VFS-EXT-1 (expression XOR initial_value)
   - COMP-EXT-6 (expression rejection in variables_reference.yaml)
   - RUN-EXT-5 (zero-stub removal)

**Estimated Time:** 2-3 days (Agent 4, Agent 6)

### Phase 2: Core Functionality (P1 Requirements)

**Focus:** Command implementations and core features

1. **Command implementations:**
   - CMD-SWITCH-* (Agent 4)
   - CMD-PARALLEL-* (Agent 4)
   - CMD-REDUCE-* (Agent 4)
   - CMD-DELAY-* (Agent 4)

2. **VFS & Items:**
   - VFS-EXT-7, VFS-EXT-8 (Agent 2)
   - ITEM-EXT-5 (Agent 5)
   - RUN-EXT-1 (Agent 6)

**Estimated Time:** 4-6 days (multiple agents in parallel)

### Phase 3: Feature Completeness (P2 Requirements)

**Focus:** Important features and metadata

1. **for_each details:** CMD-FOREACH-3 through CMD-FOREACH-5
2. **Item spawn features:** ITEM-EXT-1 through ITEM-EXT-4
3. **VFS metadata:** VFS-EXT-3 through VFS-EXT-6
4. **Compiler wiring:** COMP-EXT-1 through COMP-EXT-3

**Estimated Time:** 3-5 days

### Phase 4: Documentation & Polish (P3 Requirements)

**Focus:** Future work and documentation

1. **Future commands:** Document as not implemented (CMD-WHILE-1, CMD-EMIT-1)
2. **Documentation:** All DOC-EXT-* requirements
3. **Debug features:** RUN-EXT-6, RUN-EXT-7

**Estimated Time:** 2-3 days

---

## Next Steps

1. **Update EXECUTION-PLAN.md:**
   - Increase total requirements from 157 → 246
   - Add Agent 4 for Commands (CMD-*)
   - Redistribute requirements across agents

2. **Merge additional-requirements.md into requirements-checklist.md:**
   - Append new categories (CMD, LIMITS, *-EXT)
   - Update summary statistics
   - Add priority markings

3. **Run validation in phases:**
   - Phase 1 (P0): Immediate
   - Phase 2 (P1): This week
   - Phase 3 (P2): Next week
   - Phase 4 (P3): Following week

4. **Track progress:**
   - Create issues for P0 gaps (if any)
   - Document P1/P2 findings
   - Defer P3 to backlog

---

## Files

- **Original Checklist:** `requirements-checklist.md` (157 requirements)
- **Additional Requirements:** `additional-requirements.md` (89 requirements)
- **Execution Plan:** `EXECUTION-PLAN.md` (needs update for 246 total)
- **This Summary:** `requirements-summary-expanded.md`

---

**Status:** Ready for validation execution
**Recommended Start:** Begin Phase 1 (P0 validation) immediately
