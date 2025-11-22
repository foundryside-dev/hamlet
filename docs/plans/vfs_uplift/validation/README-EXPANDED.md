# VFS Uplift Validation - EXPANDED (246 Requirements)

**Status:** Ready for Execution
**Updated:** 2025-11-23
**Total Requirements:** 246 (157 original + 89 new)

---

## What Changed

### Original Scope (157 Requirements)

The original validation framework covered 4 VFS uplift plan documents:
- `2025-11-19-unified-world-compiler-plan.md`
- `2025-11-18-items-and-vfs-profiles.md`
- `2025-11-19-effects-system-design.md`
- `2025-11-23-runtime-vfs-effects-integration.md`

### Expanded Scope (+89 Requirements)

The framework has been expanded by deeply analyzing **all 5 source documents**, including the highly detailed command reference:
- All 4 original plan documents (re-analyzed for missed details)
- `command_reference.md` (NEW - highly detailed command specs)

**Result:** 89 additional testable requirements across 9 new categories.

---

## New Categories (89 Requirements)

### 1. CMD (Command-Specific): 22 requirements

Detailed implementation specs for each command type:

**Implemented Commands:**
- **switch**: Equality-based matching, type validation, tensor broadcasting (3 requirements)
- **for_each**: Iteration cap (256), nested prohibition, iterator scope, resolvers, no break/continue (5 requirements)
- **parallel**: Disjoint-write validation, sequential execution, empty rejection (3 requirements)
- **reduce**: Fixed-size collections, type consistency, required fields (3 requirements)
- **delay**: time_enabled requirement, delay limits (1000), queue cap (10000), zero-delay semantics, scheduler persistence (5 requirements)

**Future Commands (Not Implemented):**
- **while**: Guarded loops with max_iters cap (1 requirement - marked P3)
- **emit**: Event emission for observability (1 requirement - marked P3)

### 2. LIMITS (Runtime Limits): 7 requirements

Safety-critical caps consolidated from scattered references:
- `MAX_COLLECTION_SIZE = 256` (for_each, reduce)
- `max_depth = 10` (effect spawn recursion)
- `MAX_DELAY_TICKS = 1,000` (delay command)
- `MAX_SCHEDULED_ITEMS = 10,000` (scheduler queue)
- Item pool allocation caps
- VFS profile count limits
- Spawn rule count limits

**Priority:** P0 (all safety-critical)

### 3. VFS-EXT (VFS Extensions): 8 requirements

Detailed VFS requirements not in original checklist:
- **VFS-EXT-1 (P0)**: Expression XOR initial_value enforcement (CRITICAL)
- **VFS-EXT-7 (P1)**: Evaluation ordering (global → agent → item)
- **VFS-EXT-8 (P1)**: Item profile defaults
- Observation exposure control, semantic types, profile ID stability, dependency tracking

### 4. ITEM-EXT (Items Extensions): 16 requirements

Detailed item spawn and lifecycle requirements:
- **ITEM-EXT-5 (P1)**: Conditional spawn with VFS predicates
- **ITEM-EXT-1 to ITEM-EXT-4 (P2)**: Placement modes, schedule types, limits, priority
- Item tags, visual metadata, holder tracking, durability/decay
- Local/inventory commands, exclusivity, instance ID tracking

### 5. COMP-EXT (Compiler Extensions): 8 requirements

Compiler wiring and validation details:
- Config gating, feature flags, file layout enforcement
- Hashing for provenance, per-level metadata
- Expression rejection in variables_reference.yaml (P0)
- Levenshtein distance for typo suggestions
- File/line tracking for error reporting

### 6. EFF-EXT (Effects Extensions): 8 requirements

Additional effects system details:
- on_interrupt lifecycle hook
- Observable effects (deferred to VFS integration)
- Affordance availability masking
- Cascade triggering, event emission
- Sample command with weights, random() function

### 7. RUN-EXT (Runtime Extensions): 7 requirements

Runtime execution details:
- **RUN-EXT-5 (P0)**: Zero-stub removal (correctness)
- **RUN-EXT-1 (P1)**: Eager fallback mode (debug escape hatch)
- VFS evaluation context, item VFS masking
- Profile-driven obs dimensions, instrumentation, assertions

### 8. TEST-EXT (Testing Extensions): 8 requirements

Additional testing requirements:
- **TEST-EXT-1, TEST-EXT-2 (P1)**: Dimension regression, checkpoint roundtrip
- **TEST-EXT-5, TEST-EXT-6 (P1)**: Type safety negative tests, reapply policy tests
- Circular dependency tests, operator coverage, access control violations

### 9. DOC-EXT (Documentation Extensions): 7 requirements

Documentation gaps identified:
- **DOC-EXT-1 (P2)**: Command reference (comprehensive DSL guide)
- **DOC-EXT-5 (P2)**: Type system reference
- Observation modes, edge case policies, interaction radius
- Reapply policy examples, expression context variables

---

## Files

### Core Documents

1. **requirements-checklist.md** (157 original requirements)
   - Original comprehensive checklist from 4 plan documents
   - Keep as baseline for comparison

2. **additional-requirements.md** (89 new requirements)
   - All new requirements from expanded analysis
   - Organized into 9 new categories (CMD, LIMITS, *-EXT)

3. **requirements-summary-expanded.md** (THIS IS THE KEY DOCUMENT)
   - Executive summary of all 246 requirements
   - Priority breakdown (P0, P1, P2, P3)
   - Recommended validation strategy
   - Gap analysis roadmap

### Execution Planning

4. **EXECUTION-PLAN.md** (UPDATED)
   - Updated for 246 total requirements
   - Agent 4 now handles Commands (CMD-*)
   - Agent assignments updated with new categories
   - Priority requirements highlighted

5. **requirements-checklist-expanded.md** (PARTIAL - for reference)
   - Attempted full merge (too large to complete in one file)
   - Use `requirements-summary-expanded.md` + `additional-requirements.md` instead

---

## Priority Breakdown

### P0 (Critical): 12 requirements - VALIDATE IMMEDIATELY

**Safety & Correctness - Must fix before merge:**

1. Runtime caps enforcement (safety):
   - CMD-FOREACH-1: MAX_COLLECTION_SIZE = 256
   - CMD-FOREACH-2: Nested for_each prohibition
   - LIMITS-1 through LIMITS-4: All caps (collection, depth, delay, queue)

2. Correctness requirements:
   - VFS-EXT-1: Expression XOR initial_value
   - COMP-EXT-6: Expression rejection in variables_reference.yaml
   - RUN-EXT-5: Zero-stub removal

**Validation Priority:** Start here! These are blockers.

### P1 (High): 35 requirements - VALIDATE THIS WEEK

**Core functionality:**

1. Command implementations (CMD-SWITCH-*, CMD-PARALLEL-*, CMD-REDUCE-*, CMD-DELAY-*)
2. VFS evaluation (VFS-EXT-7, VFS-EXT-8)
3. Item spawn (ITEM-EXT-5)
4. Runtime (RUN-EXT-1)
5. Testing (TEST-EXT-1, TEST-EXT-2, TEST-EXT-5, TEST-EXT-6)

**Validation Priority:** Core features that should work.

### P2 (Medium): 31 requirements - VALIDATE NEXT WEEK

**Important features:**

1. Command details (for_each specifics, parallel rejection)
2. Item spawn features (placement, schedule, limits, priority)
3. VFS metadata (exposure, semantic types, profile IDs, dependencies)
4. Effect commands (affordance masking, cascades, sample, random)
5. Compiler wiring (gating, feature flags, file layout)

**Validation Priority:** Features that enhance functionality.

### P3 (Low): 23 requirements - BACKLOG

**Polish & future work:**

1. Future commands (while, emit) - marked as not implemented
2. Item details (placement modes, metadata, durability)
3. Effects hooks (on_interrupt, observable via VFS, events)
4. Runtime debug (instrumentation)
5. Documentation (all DOC-EXT-*)

**Validation Priority:** Can defer to post-merge.

---

## How to Use This

### For Immediate Validation

1. **Read:** `requirements-summary-expanded.md` (executive summary)
2. **Start with P0:** Validate 12 critical requirements immediately
3. **Check:** Use `EXECUTION-PLAN.md` for agent assignments
4. **Reference:** Use `additional-requirements.md` for detailed requirement specs

### For Comprehensive Validation

1. **Baseline:** Review original `requirements-checklist.md` (157 requirements)
2. **Extensions:** Review `additional-requirements.md` (89 new requirements)
3. **Execute:** Follow `EXECUTION-PLAN.md` (dispatch 9 agents in parallel)
4. **Track:** Use priority breakdown to focus efforts

### For Documentation

- **Command Reference:** See `command_reference.md` (source document)
- **Gap Reports:** Will be generated in `validation/reports/` directory
- **Summary:** Use `requirements-summary-expanded.md` for stakeholder communication

---

## Validation Workflow

### Phase 1: P0 Requirements (2-3 days)

**Focus:** Safety-critical caps and correctness

**Agents:** Agent 4 (Commands), Agent 6 (Runtime)

**Deliverables:**
- Verify all runtime caps enforced
- Verify expression XOR validation
- Verify zero-stub removal

### Phase 2: P1 Requirements (4-6 days)

**Focus:** Core command implementations and features

**Agents:** Agent 2 (VFS), Agent 4 (Commands), Agent 5 (Items), Agent 6 (Runtime), Agent 7 (Testing)

**Deliverables:**
- Command implementation status (switch, parallel, reduce, delay)
- VFS evaluation ordering
- Item conditional spawn
- Eager fallback mode

### Phase 3: P2 Requirements (3-5 days)

**Focus:** Important features and metadata

**Agents:** Agent 1 (Compiler), Agent 2 (VFS), Agent 3 (Effects), Agent 5 (Items)

**Deliverables:**
- Command details verification
- Item spawn features
- VFS metadata
- Compiler wiring

### Phase 4: P3 Requirements (2-3 days)

**Focus:** Future work and documentation

**Agents:** Agent 8 (Documentation)

**Deliverables:**
- Future commands marked as not implemented
- Documentation gaps identified
- Recommendations for post-merge work

**Total Estimated Time:** 11-17 days (with parallel execution)

---

## Success Criteria

**Phase 1 (P0) Success:**
- [ ] All 12 critical requirements verified
- [ ] No safety gaps (all caps enforced)
- [ ] No correctness gaps (XOR validation, zero-stub removal)

**Phase 2 (P1) Success:**
- [ ] All 35 core functionality requirements verified
- [ ] Command implementations complete or documented as in-progress
- [ ] VFS/Items core features working

**Phase 3 (P2) Success:**
- [ ] All 31 important feature requirements verified
- [ ] Gaps documented with effort estimates
- [ ] Recommendations for addressing gaps

**Phase 4 (P3) Success:**
- [ ] All 23 polish/future requirements classified
- [ ] Future work properly marked (while, emit)
- [ ] Documentation roadmap created

**Overall Success:**
- [ ] 246 requirements accounted for
- [ ] P0 gaps = 0 (critical issues fixed)
- [ ] P1/P2 gaps documented with plan
- [ ] P3 deferred to backlog
- [ ] Final report synthesized

---

## Next Actions

**Immediate (Today):**
1. Review `requirements-summary-expanded.md`
2. Understand priority breakdown (P0, P1, P2, P3)
3. Review `EXECUTION-PLAN.md` updates

**This Week:**
1. Execute Phase 1 validation (P0 requirements)
2. Execute Phase 2 validation (P1 requirements)
3. Document any gaps found

**Next Week:**
1. Execute Phase 3 validation (P2 requirements)
2. Execute Phase 4 validation (P3 requirements)
3. Synthesize final gap report

**After Validation:**
1. Address P0 gaps (if any)
2. Create issues for P1/P2 gaps
3. Update documentation
4. Run final verification

---

## Questions?

Refer to:
- **Summary:** `requirements-summary-expanded.md`
- **Details:** `additional-requirements.md`
- **Execution:** `EXECUTION-PLAN.md`
- **Original:** `requirements-checklist.md`

**Status:** Framework ready for execution 🚀
