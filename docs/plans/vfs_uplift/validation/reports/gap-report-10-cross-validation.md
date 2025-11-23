# Gap Report 10: Cross-Validation (Requirements Checklist Extras)

**Agent:** Agent 10 - Cross-Validation & Synthesis
**Date:** 2025-11-23
**Baseline Commit:** b085877dd45ffb9647a2bc3295ee6ce8c94ad845

## Executive Summary

**Status:** IN PROGRESS - Awaiting primary agent reports (Agents 1-9)

This report performs cross-validation between:
- **requirements-checklist.md**: 124 granular requirements (COMP-1..20, VFS-1..15, EFF-1..20, etc.)
- **master_requirements.md**: 98 consolidated requirements (COMP-REQ-001..013, VFS-REQ-001..009, etc.)

The checklist provides ~26 "extra" requirements through:
1. **Granular test breakdowns**: TEST-1 through TEST-22 (specific test counts per phase)
2. **Implementation details**: Specific file locations, AST node types, error formatting
3. **Edge cases**: Additional validation, debugging, limits
4. **Inferred requirements**: Runtime assertions, debug instrumentation

**Analysis approach:**
- Map checklist requirements to master requirements conceptually
- Identify requirements in checklist NOT covered by master
- Classify each extra as: ✅ DONE, 🟡 PARTIAL, ❌ MISSING, 🔄 REDUNDANT, ⭐ VALUABLE

## Mapping Analysis

### Requirements-Checklist.md vs Master_Requirements.md ID Mapping

The two documents use different ID schemes:
- **Checklist**: `COMP-1`, `VFS-1`, `EFF-1`, etc. (124 total)
- **Master**: `COMP-REQ-001`, `VFS-REQ-001`, `EFF-REQ-001`, etc. (98 total)

**Conceptual mapping:**

| Checklist Category | Checklist Count | Master Category | Master Count | Coverage Analysis |
|-------------------|-----------------|-----------------|--------------|-------------------|
| COMP-1..20 | 20 | COMP-REQ-001..013 | 13 | Checklist more granular |
| VFS-1..15 | 15 | VFS-REQ-001..009 | 9 | Checklist more granular |
| EFF-1..20 | 20 | EFF-REQ-001..011 | 11 | Checklist more granular |
| ITEM-1..16 | 16 | ITEM-REQ-001..017 | 17 | Near parity |
| RUN-1..12 | 12 | RUN-REQ-001..002 | 2 | Checklist much more granular |
| TEST-1..22 | 22 | QA-REQ-002..011 | 10 | Checklist has explicit test counts |
| DOC-1..10 | 10 | DOC-REQ-001..008 | 8 | Near parity |
| BREAK-1..9 | 9 | BREAK-REQ-001..002 | 2 | Checklist more granular |

**Total:** 124 (checklist) vs 98 (master)

## Extra Requirements Analysis

### Category: Compiler (COMP-*)

**Checklist extras not in master:**

#### COMP-1: Seven-stage pipeline implementation detail
**Requirement:** UniverseCompiler must implement 7 compilation stages (parse → symbol table → resolve → cross-validate → metadata → optimization → emit/cache)

**Master coverage:** COMP-REQ-002, COMP-REQ-004 cover compilation but don't specify 7 stages
**Classification:** 🔄 **REDUNDANT** - Implementation detail of compiler architecture
**Rationale:** Master requirements cover compiler functionality; exact stage count is implementation detail

#### COMP-7: Expression parser implementation
**Requirement:** Parse expressions like "target.bar.energy + (0.05 * intensity)" to AST

**Master coverage:** EXP-REQ-001 covers expression language foundation
**Classification:** 🔄 **REDUNDANT** - Covered by EXP-REQ-001
**Rationale:** Expression parsing is fundamental requirement in master

#### COMP-8: AST node types specification
**Requirement:** Define AST nodes (Constant, Variable, PathAccess, BinaryOp, UnaryOp, FunctionCall, IfThenElse)

**Master coverage:** EXP-REQ-001 covers AST parsing
**Classification:** 🔄 **REDUNDANT** - Implementation detail
**Rationale:** Specific AST node types are implementation choices

#### COMP-9: Type checker implementation
**Requirement:** Type inference, path resolution validation, type compatibility checks

**Master coverage:** COMP-REQ-004 covers path/type validation
**Classification:** 🔄 **REDUNDANT** - Covered by COMP-REQ-004
**Rationale:** Type checking is explicitly in master

#### COMP-10: Expression evaluator implementation
**Requirement:** Execute AST on GPU tensors with execution context

**Master coverage:** EXP-REQ-001 covers evaluation on torch device
**Classification:** 🔄 **REDUNDANT** - Covered by EXP-REQ-001
**Rationale:** Evaluator is part of expression language foundation

#### COMP-13: Error reporting with context
**Requirement:** Clear error messages with file/line, suggestions for typos

**Master coverage:** COMP-REQ-007 covers error UX with context
**Classification:** 🔄 **REDUNDANT** - Covered by COMP-REQ-007
**Rationale:** Exact same requirement in master

#### COMP-19: Config version tracking
**Requirement:** All config files include version field (e.g., "1.0")

**Master coverage:** Not explicitly in master
**Classification:** ⭐ **VALUABLE** - Important for config evolution
**Rationale:** Version tracking enables future migrations and compatibility checks
**Evidence needed:** Check if DTOs enforce version field, validation tests exist

#### COMP-20: Experiment vs level scoping enforcement
**Requirement:** Observation-shape changes at experiment-level; masking/spawn at level-level

**Master coverage:** CFG-REQ-001, COMP-REQ-011 cover file layout
**Classification:** 🔄 **REDUNDANT** - Covered by file layout requirements
**Rationale:** Scoping is enforced by file layout requirements

### Category: VFS System (VFS-*)

#### VFS-1: Expression language operator coverage
**Requirement:** Full expression DSL with all operators from VARIABLE_SUBSYSTEM.md (60+ tests)

**Master coverage:** EXP-REQ-001 covers expression language
**Classification:** 🔄 **REDUNDANT** - Covered by EXP-REQ-001
**Rationale:** Operator coverage is part of expression foundation

#### VFS-11: Observation dimension stability
**Requirement:** obs_dim stable across all levels (enables checkpoint transfer)

**Master coverage:** OBS-REQ-003 covers obs dim stability
**Classification:** 🔄 **REDUNDANT** - Covered by OBS-REQ-003
**Rationale:** Exact same requirement in master

#### VFS-13: Dependency graph construction
**Requirement:** Build dependency graph from expression references, detect cycles

**Master coverage:** VFS-REQ-002 covers mark-and-sweep with topo order
**Classification:** 🔄 **REDUNDANT** - Covered by VFS-REQ-002
**Rationale:** Dependency graph is part of mark-and-sweep evaluation

#### VFS-14: Type system integration
**Requirement:** scalar, bool, vec2i, vec3i, vecNi, vecNf primitive types

**Master coverage:** DOC-REQ-006 documents type system
**Classification:** 🔄 **REDUNDANT** - Covered by type system docs
**Rationale:** Type system is documented in master

#### VFS-15: VFS in ExecutionContext
**Requirement:** ExecutionContext provides vfs_global, vfs_agent, vfs_item dictionaries

**Master coverage:** VFS-REQ-005 covers ExecutionContext VFS access
**Classification:** 🔄 **REDUNDANT** - Covered by VFS-REQ-005
**Rationale:** Exact same requirement in master

### Category: Effects System (EFF-*)

#### EFF-1: Effects catalog as compiled artifact
**Requirement:** Effects compiled first in World Compiler, stored in CompiledWorld

**Master coverage:** COMP-REQ-002 covers effects compiled first
**Classification:** 🔄 **REDUNDANT** - Covered by COMP-REQ-002
**Rationale:** Exact same requirement in master

#### EFF-17: Effect nesting depth limit
**Requirement:** Runtime limit (max_depth=10) to prevent infinite recursion

**Master coverage:** CMD-REQ-003 covers effect spawn depth cap
**Classification:** 🔄 **REDUNDANT** - Covered by CMD-REQ-003
**Rationale:** Depth cap is explicitly in master

#### EFF-18: Execution context state access
**Requirement:** Context provides bars, vfs, position, temporal state

**Master coverage:** EFF-REQ-003 covers scope-aware context
**Classification:** 🔄 **REDUNDANT** - Covered by EFF-REQ-003
**Rationale:** Context state is part of scope-aware context requirement

#### EFF-19: Effect duration management
**Requirement:** Auto-despawn when duration_remaining <= 0, execute on_despawn commands

**Master coverage:** EFF-REQ-004 covers EffectManager lifecycle
**Classification:** 🔄 **REDUNDANT** - Covered by EFF-REQ-004
**Rationale:** Duration management is part of lifecycle requirement

#### EFF-20: Effect intensity parameter
**Requirement:** intensity parameter with default, overridable at spawn, available in expressions

**Master coverage:** EFF-REQ-001 includes intensity in schema
**Classification:** 🔄 **REDUNDANT** - Covered by EFF-REQ-001
**Rationale:** Intensity is part of effect catalog schema

### Category: Items System (ITEM-*)

Most ITEM requirements in checklist map 1:1 to master (ITEM-REQ-001..017). No significant extras identified.

### Category: Runtime Integration (RUN-*)

#### RUN-12: Zero regressions
**Requirement:** All 435+ existing tests still pass

**Master coverage:** Not explicitly in master
**Classification:** ⭐ **VALUABLE** - Critical success criterion
**Rationale:** Regression prevention is fundamental but not explicit in master
**Evidence needed:** CI status, test count verification

### Category: Testing (TEST-*)

**Checklist TEST-1 through TEST-22 provide granular test count targets per phase.**

**Master coverage:** QA-REQ-002 covers test coverage targets but less granular

**Classification:** 🟡 **PARTIAL** - Master has coverage targets but not phase-by-phase breakdown

**Analysis:**
- Checklist: 60+ expression tests, 50+ VFS tests, 75+ effects tests, 70+ items tests, 15+ integration
- Master: 20-30 new tests for runtime uplift plus existing 270+ goal

**Valuable catches:**
- TEST-20: Performance validation (benchmark scripts, profiling data, <5% regression)
- TEST-21: Runtime integration tests (5-10 tests for runtime wiring)
- TEST-22: Test config packs (items_smoke, effects_smoke, vfs_smoke)

**Recommendation:** These granular test targets should inform Agent 7's validation

### Category: Documentation (DOC-*)

#### DOC-9: Edge case policies document
**Requirement:** docs/plans/vfs_uplift/edge-case-policies.md

**Master coverage:** DOC-REQ-004 covers edge case policies
**Classification:** 🔄 **REDUNDANT** - Covered by DOC-REQ-004
**Rationale:** Same requirement, different doc path

#### DOC-10: Observation management modes
**Requirement:** Document full_auto, max_compact, full_manual modes

**Master coverage:** DOC-REQ-003 covers observation modes guide
**Classification:** 🔄 **REDUNDANT** - Covered by DOC-REQ-003
**Rationale:** Exact same requirement in master

### Category: Breaking Changes (BREAK-*)

**Checklist BREAK-1 through BREAK-9 provide granular breaking change specifications.**

**Master coverage:** BREAK-REQ-001 and BREAK-REQ-002 consolidate breaking changes

**Classification:** 🟡 **PARTIAL** - Master consolidates, checklist more granular

**Granular checklist requirements:**
- BREAK-1: vfs_profiles.yaml required
- BREAK-2: variables_reference.yaml no item scope
- BREAK-3: Effect catalog compiled
- BREAK-4: Item instances require vfs_profile
- BREAK-5: EffectPipeline deleted
- BREAK-6: max_items_per_agent required
- BREAK-7: No behavioral defaults
- BREAK-8: reapply_policy required
- BREAK-9: Observation dimension changes

**All covered by:**
- Master BREAK-REQ-001: Ban level-scoped VFS/effects
- Master BREAK-REQ-002: No backward-compat paths
- Master POLICY-REQ-001: No implicit defaults
- Master COMP-REQ-006: Strict variables_reference scope

**Classification:** 🔄 **REDUNDANT** - All checklist breaking changes covered by master

## Summary of Extras

### Total Extras Identified: ~26

**Classification breakdown:**

| Status | Count | Notes |
|--------|-------|-------|
| ✅ DONE | TBD | Awaiting primary agent reports |
| 🟡 PARTIAL | 2 | TEST-* granularity, BREAK-* granularity |
| ❌ MISSING | TBD | Awaiting primary agent reports |
| 🔄 REDUNDANT | ~20 | Implementation details, covered by master |
| ⭐ VALUABLE | 2 | COMP-19 (version tracking), RUN-12 (zero regressions) |

### Valuable Catches (Important Requirements Not Explicit in Master)

1. **COMP-19: Config version tracking** ⭐
   - **What:** All config files include version field for future migrations
   - **Why valuable:** Enables config evolution, compatibility checks, migration paths
   - **Master gap:** No explicit version field requirement
   - **Evidence needed:** Check DTOs for version field enforcement

2. **RUN-12: Zero regressions** ⭐
   - **What:** All 435+ existing tests must still pass
   - **Why valuable:** Fundamental success criterion for integration
   - **Master gap:** Not explicit in master requirements
   - **Evidence needed:** CI status, test count verification

### Recommendations

1. **Add to master_requirements.md:**
   - Version tracking requirement (COMP-19 equivalent)
   - Zero regression requirement (RUN-12 equivalent)

2. **Use checklist granularity for validation:**
   - TEST-* breakdown informs Agent 7 testing validation
   - BREAK-* breakdown helps verify all breaking changes handled

3. **Focus on valuable catches:**
   - Verify version field in all DTO roots
   - Verify CI passing with no new skips/xfails

## Next Steps

**Blocked on:** Primary agent reports (Agents 1-9)

**Once unblocked:**
1. Read all 9 gap reports
2. Update classifications (DONE/PARTIAL/MISSING) based on evidence
3. Aggregate status counts
4. Compile final burn-down list (Phase 2)

**Expected completion:** After all primary agent reports available

---

## Detailed Requirement-by-Requirement Analysis

### COMP Requirements (Checklist)

| Checklist ID | Title | Master Coverage | Classification | Notes |
|--------------|-------|-----------------|----------------|-------|
| COMP-1 | Seven-stage pipeline | COMP-REQ-002 | 🔄 REDUNDANT | Implementation detail |
| COMP-2 | Load VFS profiles at compile time | COMP-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-3 | Load effects catalog at compile time | COMP-REQ-002 | 🔄 REDUNDANT | Covered |
| COMP-4 | VFS profile DTOs | DTO-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-5 | Items catalog DTOs | CFG-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-6 | Effects catalog DTOs | EFF-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-7 | Expression parser | EXP-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-8 | AST node types | EXP-REQ-001 | 🔄 REDUNDANT | Implementation detail |
| COMP-9 | Type checker | COMP-REQ-004 | 🔄 REDUNDANT | Covered |
| COMP-10 | Expression evaluator | EXP-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-11 | Command pipeline parser | COMP-REQ-002 | 🔄 REDUNDANT | Covered |
| COMP-12 | Cross-validation | COMP-REQ-002 | 🔄 REDUNDANT | Covered |
| COMP-13 | Error reporting with context | COMP-REQ-007 | 🔄 REDUNDANT | Covered |
| COMP-14 | CompiledUniverse schema extensions | COMP-REQ-003 | 🔄 REDUNDANT | Covered |
| COMP-15 | VFS profile compilation | VFS-REQ-002 | 🔄 REDUNDANT | Covered |
| COMP-16 | VFS observation marking | OBS-REQ-006 | 🔄 REDUNDANT | Covered |
| COMP-17 | Items-VFS profile binding validation | COMP-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-18 | No-defaults enforcement | POLICY-REQ-001 | 🔄 REDUNDANT | Covered |
| COMP-19 | Config version tracking | **NONE** | ⭐ VALUABLE | **Add to master** |
| COMP-20 | Experiment vs level scoping | COMP-REQ-011 | 🔄 REDUNDANT | Covered |

### VFS Requirements (Checklist)

| Checklist ID | Title | Master Coverage | Classification | Notes |
|--------------|-------|-----------------|----------------|-------|
| VFS-1 | Expression language support | EXP-REQ-001 | 🔄 REDUNDANT | Covered |
| VFS-2 | Three scopes (global/agent/item) | VFS-REQ-001 | 🔄 REDUNDANT | Covered |
| VFS-3 | Dynamic variables via expressions | VFS-REQ-002 | 🔄 REDUNDANT | Covered |
| VFS-4 | Reference types | COMP-REQ-009 | 🔄 REDUNDANT | Covered |
| VFS-5 | Observation builder integration | OBS-REQ-001 | 🔄 REDUNDANT | Covered |
| VFS-6 | Mark-and-sweep evaluation | VFS-REQ-002 | 🔄 REDUNDANT | Covered |
| VFS-7 | Registry with access control | VFS-REQ-001 | 🔄 REDUNDANT | Covered |
| VFS-8 | Profile-driven item storage | ITEM-REQ-003 | 🔄 REDUNDANT | Covered |
| VFS-9 | Item instance profiles | ITEM-REQ-003 | 🔄 REDUNDANT | Covered |
| VFS-10 | Item VFS observations | OBS-REQ-001 | 🔄 REDUNDANT | Covered |
| VFS-11 | Observation dimension stability | OBS-REQ-003 | 🔄 REDUNDANT | Covered |
| VFS-12 | Tensor types support | VFS-REQ-007 | 🔄 REDUNDANT | Covered |
| VFS-13 | Dependency graph construction | VFS-REQ-002 | 🔄 REDUNDANT | Covered |
| VFS-14 | Type system integration | DOC-REQ-006 | 🔄 REDUNDANT | Covered |
| VFS-15 | VFS in ExecutionContext | VFS-REQ-005 | 🔄 REDUNDANT | Covered |

### EFF Requirements (Checklist)

| Checklist ID | Title | Master Coverage | Classification | Notes |
|--------------|-------|-----------------|----------------|-------|
| EFF-1 | Effects catalog as compiled artifact | COMP-REQ-002 | 🔄 REDUNDANT | Covered |
| EFF-2 | Command pipeline execution | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-3 | EffectManager lifecycle | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-4 | ActiveEffect runtime structure | EFF-REQ-004 | 🔄 REDUNDANT | Implementation detail |
| EFF-5 | Scoped effect storage | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-6 | Reapply policies | EFF-REQ-002 | 🔄 REDUNDANT | Covered |
| EFF-7 | Observable effects | EFF-REQ-005 | 🔄 REDUNDANT | Covered |
| EFF-8 | Command types - State modification | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-9 | Command types - Entity lifecycle | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-10 | Command types - Control flow | CMD-REQ-001 | 🔄 REDUNDANT | Covered |
| EFF-11 | Command types - Messaging/Events | CMD-REQ-009 | 🔄 REDUNDANT | Covered |
| EFF-12 | Command types - Randomness | EFF-REQ-010 | 🔄 REDUNDANT | Covered |
| EFF-13 | Path notation support | EFF-REQ-003 | 🔄 REDUNDANT | Covered |
| EFF-14 | Expression language integration | EXP-REQ-001 | 🔄 REDUNDANT | Covered |
| EFF-15 | Type safety in commands | COMP-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-16 | Environment integration | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-17 | Effect nesting depth limit | CMD-REQ-003 | 🔄 REDUNDANT | Covered |
| EFF-18 | Execution context state access | EFF-REQ-003 | 🔄 REDUNDANT | Covered |
| EFF-19 | Effect duration management | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| EFF-20 | Effect intensity parameter | EFF-REQ-001 | 🔄 REDUNDANT | Covered |

### RUN Requirements (Checklist)

| Checklist ID | Title | Master Coverage | Classification | Notes |
|--------------|-------|-----------------|----------------|-------|
| RUN-1 | Mark-and-sweep VFS evaluation | VFS-REQ-002 | 🔄 REDUNDANT | Covered |
| RUN-2 | Item VFS observations | OBS-REQ-001 | 🔄 REDUNDANT | Covered |
| RUN-3 | Compiled catalog usage | COMP-REQ-003 | 🔄 REDUNDANT | Covered |
| RUN-4 | ExecutionContext construction | VFS-REQ-005 | 🔄 REDUNDANT | Covered |
| RUN-5 | VFS registry reads/writes | VFS-REQ-001 | 🔄 REDUNDANT | Covered |
| RUN-6 | ItemManager spawn with profiles | ITEM-REQ-003 | 🔄 REDUNDANT | Covered |
| RUN-7 | Effects schema from compiled profiles | COMP-REQ-003 | 🔄 REDUNDANT | Covered |
| RUN-8 | Performance target (<5% overhead) | PERF-REQ-001 | 🔄 REDUNDANT | Covered |
| RUN-9 | Checkpoint serialization | QA-REQ-005 | 🔄 REDUNDANT | Covered |
| RUN-10 | Effect step integration | EFF-REQ-004 | 🔄 REDUNDANT | Covered |
| RUN-11 | VFS evaluation at runtime | VFS-REQ-004 | 🔄 REDUNDANT | Covered |
| RUN-12 | Zero regressions | **NONE** | ⭐ VALUABLE | **Add to master** |

### TEST Requirements (Checklist)

All TEST-1 through TEST-22 are covered by QA-REQ-002 (test coverage targets), but checklist provides more granular phase-by-phase breakdown.

**Classification:** 🟡 **PARTIAL** - Master has overall targets, checklist has granular breakdowns

### DOC Requirements (Checklist)

All DOC-1 through DOC-10 are covered by DOC-REQ-001 through DOC-REQ-008 in master.

**Classification:** 🔄 **REDUNDANT** - All covered by master

### BREAK Requirements (Checklist)

All BREAK-1 through BREAK-9 are covered by BREAK-REQ-001, BREAK-REQ-002, POLICY-REQ-001, and COMP-REQ-006 in master.

**Classification:** 🔄 **REDUNDANT** - All covered by master (consolidated)

---

## Conclusion

**Key findings:**

1. **Checklist provides granular implementation details** - Most "extras" are implementation details or test breakdowns covered by consolidated master requirements

2. **Two valuable catches identified:**
   - COMP-19: Config version tracking (should be added to master)
   - RUN-12: Zero regressions (should be explicit success criterion)

3. **Checklist granularity useful for validation:**
   - TEST-* breakdown helps Agent 7 verify test coverage
   - BREAK-* breakdown helps verify all breaking changes handled
   - Implementation details (COMP-7/8/9/10) help verify architecture

4. **No major gaps found:**
   - Master requirements comprehensively cover functionality
   - Checklist adds detail and test targets
   - Both documents align well

**Next phase:** Awaiting primary agent reports to update DONE/PARTIAL/MISSING classifications and compile final burn-down list.
