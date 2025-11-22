# VFS Uplift Gap Analysis - Execution Plan (Master Requirements)

**Status:** Ready to Execute
**Updated:** 2025-11-23 (Based on master_requirements.md)
**Total Requirements:** 98
**Baseline Commit:** TBD (run git rev-parse HEAD)
**Agents:** 10 (9 parallel + 1 synthesis)
**Source:** docs/plans/vfs_uplift/master_requirements.md

---

## Objective

Execute systematic gap analysis of VFS uplift implementation by dispatching **9 parallel agents**, each verifying their assigned requirements with file:line evidence from the codebase, then synthesizing results into a final gap report.

---

## Agent Division (By Requirement Prefix)

| Agent | Scope | Requirements | Count |
|-------|-------|--------------|-------|
| 1 | Config & DTOs | CFG-REQ-001..002, DTO-REQ-001 | **3** |
| 2 | Compiler | COMP-REQ-001..013 | **13** |
| 3 | VFS System | VFS-REQ-001..009 | **9** |
| 4 | Items System | ITEM-REQ-001..017 | **17** |
| 5 | Effects System | EFF-REQ-001..011 | **11** |
| 6 | Commands | CMD-REQ-001..011 | **11** |
| 7 | Observations & Runtime | OBS-REQ-001..006, RUN-REQ-001..002, MIG-REQ-001 | **10** |
| 8 | QA & Testing | QA-REQ-001..011, PERF-REQ-001 | **12** |
| 9 | Policy & Docs | BREAK-REQ-001..002, POLICY-REQ-001..002, LIMIT-REQ-001, DOC-REQ-001..008 | **12** |
| 10 | Synthesis | Aggregate all 9 reports | **—** |

**Total:** 98 requirements

---

## Prerequisites

**Before starting:**

- [ ] Baseline commit recorded: `git rev-parse HEAD > validation/baseline-commit.txt`
- [ ] All 1945+ existing tests pass
- [ ] Working directory clean (no uncommitted changes that would interfere)
- [ ] Read `master_requirements.md` to understand all 98 requirements

**Verify prerequisites:**

```bash
cd /home/john/hamlet

# Record baseline
git rev-parse HEAD > docs/plans/vfs_uplift/validation/baseline-commit.txt

# Verify tests pass
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --tb=short -q | tail -20

# Check working directory
git status --short  # Should be clean or only docs/plans/vfs_uplift/ changes
```

---

## Agent Instructions Template

Each agent will:

1. **Read assigned requirements** from `master_requirements.md`
2. **Search codebase** for implementation evidence
3. **Classify each requirement**:
   - ✅ **DONE**: Full evidence found (file:line citations)
   - 🟡 **PARTIAL**: Partial implementation (list gaps)
   - ❌ **MISSING**: Not implemented (recommend next steps)
   - 📝 **N/A**: Documentation-only or policy requirement
4. **Generate gap report** in `validation/reports/gap-report-{agent-number}-{scope}.md`

**Evidence Standards:**
- Code citations: `src/townlet/path/file.py:123-145`
- Config citations: `configs/reference/file.yaml:45-67`
- Test citations: `tests/test_townlet/path/test_file.py:test_name`
- Documentation citations: `docs/path/file.md:Section Name`

---

## Agent 1: Config & DTOs

**Scope:** CFG-REQ-001..002, DTO-REQ-001 (3 requirements)

**Requirements:**
- CFG-REQ-001: Items config split (experiment vs level)
- CFG-REQ-002: VFS profiles file (experiment-level)
- DTO-REQ-001: DTOs with no defaults (Pydantic extra="forbid")

**Primary files to examine:**
- `src/townlet/config/items_config.py`
- `src/townlet/config/vfs_profiles_config.py`
- `configs/reference/items.yaml`
- `configs/reference/vfs_profiles.yaml`
- Tests: `tests/test_townlet/unit/config/`

**Output:** `validation/reports/gap-report-01-config-dtos.md`

---

## Agent 2: Compiler

**Scope:** COMP-REQ-001..013 (13 requirements)

**Requirements:**
- COMP-REQ-001: Compiler loads profiles/items
- COMP-REQ-002: Effects compiled first
- COMP-REQ-003: Runtime consumes compiled artifacts
- COMP-REQ-004: Path/type validation + errors
- COMP-REQ-005: Profile load gating
- COMP-REQ-006: Strict variables_reference scope
- COMP-REQ-007: Error UX with context
- COMP-REQ-008: Continuous interaction guard
- COMP-REQ-009: Reference type resolution
- COMP-REQ-010: Feature flag gating
- COMP-REQ-011: File layout enforcement
- COMP-REQ-012: Hashing for provenance
- COMP-REQ-013: Per-level spawn metadata

**Primary files to examine:**
- `src/townlet/universe/compiler.py` (UniverseCompiler)
- `src/townlet/universe/compiled.py` (CompiledUniverse)
- `src/townlet/world/expression/type_checker.py`
- `src/townlet/effects/compiler.py`
- Tests: `tests/test_townlet/unit/universe/test_compiler*.py`

**Output:** `validation/reports/gap-report-02-compiler.md`

---

## Agent 3: VFS System

**Scope:** VFS-REQ-001..009 (9 requirements)

**Requirements:**
- VFS-REQ-001: Scoped VFS engine
- VFS-REQ-002: Mark-and-sweep evaluation
- VFS-REQ-003: Expression XOR initial_value
- VFS-REQ-004: Evaluation order (global → agent → item)
- VFS-REQ-005: ExecutionContext VFS access
- VFS-REQ-006: Profile metadata & exposure
- VFS-REQ-007: Advanced tensor types
- VFS-REQ-008: Update rule DSL (future)
- VFS-REQ-009: Eager evaluation fallback

**Primary files to examine:**
- `src/townlet/vfs/registry.py`
- `src/townlet/vfs/schema.py`
- `src/townlet/vfs/observation_builder.py`
- `src/townlet/world/expression/evaluator.py`
- Tests: `tests/test_townlet/unit/vfs/`

**Output:** `validation/reports/gap-report-03-vfs.md`

---

## Agent 4: Items System

**Scope:** ITEM-REQ-001..017 (17 requirements)

**Requirements:**
- ITEM-REQ-001: Item manager runtime
- ITEM-REQ-002: Inventory + core actions
- ITEM-REQ-003: Profile-driven item VFS
- ITEM-REQ-004: Fixed item VFS pool
- ITEM-REQ-005: Spawn rules coverage
- ITEM-REQ-006: Conditional spawn predicates
- ITEM-REQ-007: Use action handling
- ITEM-REQ-008: Item VFS defaults
- ITEM-REQ-009: Item-scoped custom verbs
- ITEM-REQ-010: Item tags
- ITEM-REQ-011: Item visual metadata
- ITEM-REQ-012: Holder agent tracking
- ITEM-REQ-013: Item durability/charges
- ITEM-REQ-014: Item spoilage/decay
- ITEM-REQ-015: Exclusive vs shared items
- ITEM-REQ-016: Item instance ID tracking
- ITEM-REQ-017: Item spawn timing

**Primary files to examine:**
- `src/townlet/environment/items/` (if exists)
- `src/townlet/environment/vectorized_env.py` (item handling)
- `src/townlet/config/items_config.py`
- Tests: `tests/test_townlet/integration/test_items*.py`

**Output:** `validation/reports/gap-report-04-items.md`

---

## Agent 5: Effects System

**Scope:** EFF-REQ-001..011 (11 requirements)

**Requirements:**
- EFF-REQ-001: Effects catalog schema
- EFF-REQ-002: Reapply policy semantics
- EFF-REQ-003: Scope-aware context
- EFF-REQ-004: EffectManager runtime
- EFF-REQ-005: Effects observable via VFS
- EFF-REQ-006: on_interrupt hook
- EFF-REQ-007: Affordance availability commands
- EFF-REQ-008: Cascade trigger command
- EFF-REQ-009: Sample command with weights
- EFF-REQ-010: Random chance conditionals
- EFF-REQ-011: Effect metadata catalog

**Primary files to examine:**
- `src/townlet/effects/executor.py` (EffectManager)
- `src/townlet/effects/compiler.py`
- `src/townlet/effects/schema.py`
- `src/townlet/config/effects_config.py`
- Tests: `tests/test_townlet/unit/effects/`

**Output:** `validation/reports/gap-report-05-effects.md`

---

## Agent 6: Commands

**Scope:** CMD-REQ-001..011 (11 requirements)

**Requirements:**
- CMD-REQ-001: Command DSL support + guards
- CMD-REQ-002: Command runtime caps
- CMD-REQ-003: Effect spawn depth cap
- CMD-REQ-004: Switch semantics
- CMD-REQ-005: for_each semantics
- CMD-REQ-006: Parallel semantics
- CMD-REQ-007: Reduce constraints
- CMD-REQ-008: Delay scheduler semantics
- CMD-REQ-009: Emit event command
- CMD-REQ-010: Advanced control flow implementation
- CMD-REQ-011: While loop - not implemented

**Primary files to examine:**
- `src/townlet/effects/executor.py` (command implementations)
- `src/townlet/effects/compiler.py` (command compilation)
- `src/townlet/effects/schema.py` (CommandType enum)
- `src/townlet/effects/scheduler.py` (delay command)
- Tests: `tests/test_townlet/unit/effects/test_command*.py`

**Output:** `validation/reports/gap-report-06-commands.md`

---

## Agent 7: Observations & Runtime

**Scope:** OBS-REQ-001..006, RUN-REQ-001..002, MIG-REQ-001 (10 requirements)

**Requirements:**
- OBS-REQ-001: VFS in observations
- OBS-REQ-002: Observation modes
- OBS-REQ-003: Obs dim stability
- OBS-REQ-004: No zero-stub item VFS
- OBS-REQ-005: Mask unused item slots
- OBS-REQ-006: Profile-driven obs dimensions
- RUN-REQ-001: Debug instrumentation
- RUN-REQ-002: Runtime assertions
- MIG-REQ-001: Affordances/items use Effects

**Primary files to examine:**
- `src/townlet/vfs/observation_builder.py`
- `src/townlet/environment/vectorized_env.py`
- `src/townlet/universe/affordances.py`
- Tests: `tests/test_townlet/unit/environment/test_observations.py`

**Output:** `validation/reports/gap-report-07-obs-runtime.md`

---

## Agent 8: QA & Testing

**Scope:** QA-REQ-001..011, PERF-REQ-001 (12 requirements)

**Requirements:**
- QA-REQ-001: (Not defined in master - placeholder)
- QA-REQ-002: Test coverage targets
- QA-REQ-003: Metadata-mask parity
- QA-REQ-004: Static usage verification
- QA-REQ-005: Checkpoint roundtrip tests
- QA-REQ-006: Circular dependency tests
- QA-REQ-007: Expression operator coverage
- QA-REQ-008: Type safety negative tests
- QA-REQ-009: Reapply policy tests
- QA-REQ-010: Access control violation tests
- QA-REQ-011: Action masking tests
- PERF-REQ-001: Step-loop performance

**Primary files to examine:**
- `tests/test_townlet/` (all test files)
- `.github/workflows/` (CI validation)
- `scripts/` (validation scripts)
- Performance benchmarks

**Output:** `validation/reports/gap-report-08-qa-testing.md`

---

## Agent 9: Policy & Documentation

**Scope:** BREAK-REQ-001..002, POLICY-REQ-001..002, LIMIT-REQ-001, DOC-REQ-001..008 (12 requirements)

**Requirements:**
- BREAK-REQ-001: Ban level-scoped VFS/effects
- BREAK-REQ-002: No backward-compat paths
- POLICY-REQ-001: No implicit defaults
- POLICY-REQ-002: Breaking changes only
- LIMIT-REQ-001: Resource count limits
- DOC-REQ-001: Reference docs update
- DOC-REQ-002: Command DSL reference
- DOC-REQ-003: Observation modes guide
- DOC-REQ-004: Edge case policies
- DOC-REQ-005: Interaction radius guide
- DOC-REQ-006: Type system reference
- DOC-REQ-007: Reapply policy examples
- DOC-REQ-008: Expression context reference

**Primary files to examine:**
- `docs/config-schemas/`
- `docs/guides/`
- `configs/reference/`
- Code patterns for backwards compatibility
- Validation scripts for policy enforcement

**Output:** `validation/reports/gap-report-09-policy-docs.md`

---

## Agent 10: Synthesis

**Scope:** Aggregate all 9 agent reports into final gap report

**Wait for:** All 9 agent reports completed

**Tasks:**
1. Read all 9 gap reports
2. Count requirements by status (DONE, PARTIAL, MISSING, N/A)
3. Identify P0 blockers (requirements marked MISSING with high priority)
4. Summarize implementation status by category
5. Recommend next steps

**Output:** `validation/reports/gap-report-FINAL.md`

**Template:**
```markdown
# VFS Uplift Gap Analysis - Final Report

## Executive Summary

Total Requirements: 98
- ✅ DONE: X (Y%)
- 🟡 PARTIAL: X (Y%)
- ❌ MISSING: X (Y%)
- 📝 N/A: X (Y%)

## P0 Blockers (Critical Missing Requirements)

[List of MISSING requirements with Priority P0 or critical impact]

## Category Status

### Config & DTOs (3 requirements)
[Summary from Agent 1]

### Compiler (13 requirements)
[Summary from Agent 2]

### VFS System (9 requirements)
[Summary from Agent 3]

[...continue for all categories...]

## Recommendations

1. [Immediate actions for P0 blockers]
2. [Next steps for PARTIAL requirements]
3. [Documentation needs]
4. [Testing gaps]

## Detailed Reports

See individual agent reports in validation/reports/
```

---

## Execution Instructions

### Step 1: Verify Prerequisites

```bash
cd /home/john/hamlet
git rev-parse HEAD > docs/plans/vfs_uplift/validation/baseline-commit.txt
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --tb=short -q | tail -20
```

### Step 2: Dispatch Agents

Use the Task tool to dispatch 9 agents in parallel in a single message:

```markdown
I need you to dispatch 9 gap analysis agents in parallel to verify VFS uplift requirements from master_requirements.md.

Use the Task tool with 9 separate invocations in a single message, following the agent assignments in EXECUTION-PLAN-MASTER.md.

Each agent should:
1. Read their assigned requirements from docs/plans/vfs_uplift/master_requirements.md
2. Search the codebase for implementation evidence
3. Classify each requirement as DONE/PARTIAL/MISSING/N/A
4. Output gap report to docs/plans/vfs_uplift/validation/reports/

Agent assignments:
- Agent 1: CFG-REQ-001..002, DTO-REQ-001 (3 reqs)
- Agent 2: COMP-REQ-001..013 (13 reqs)
- Agent 3: VFS-REQ-001..009 (9 reqs)
- Agent 4: ITEM-REQ-001..017 (17 reqs)
- Agent 5: EFF-REQ-001..011 (11 reqs)
- Agent 6: CMD-REQ-001..011 (11 reqs)
- Agent 7: OBS-REQ-001..006, RUN-REQ-001..002, MIG-REQ-001 (10 reqs)
- Agent 8: QA-REQ-001..011, PERF-REQ-001 (12 reqs)
- Agent 9: BREAK-REQ-001..002, POLICY-REQ-001..002, LIMIT-REQ-001, DOC-REQ-001..008 (12 reqs)
```

### Step 3: Wait for Completion

All agents will complete and generate their reports in `validation/reports/`.

### Step 4: Synthesize

Dispatch Agent 10 to synthesize all reports into final gap report.

---

## Success Criteria

- [ ] All 98 requirements accounted for
- [ ] Evidence citations provided for DONE/PARTIAL status
- [ ] P0 blockers identified
- [ ] Next steps recommended
- [ ] Final report generated

---

## Notes

**Master Requirements File:** `docs/plans/vfs_uplift/master_requirements.md`
**Reports Directory:** `docs/plans/vfs_uplift/validation/reports/`
**Baseline Commit:** Stored in `validation/baseline-commit.txt`
