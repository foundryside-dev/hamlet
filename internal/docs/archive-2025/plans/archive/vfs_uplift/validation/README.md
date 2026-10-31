# VFS Uplift Validation Suite – Final Run (Run 3)

**Status:** Ready for Final Validation Run
**Expected Completion:** 90-95%
**Created:** 2025-11-22
**Updated:** 2025-11-23 (Cleaned for Run 3)

---

## Overview

This is the **third and final validation run** for VFS uplift implementation. After two previous runs that identified and resolved critical gaps, we expect 90-95% completion.

**Dual-Source Validation:**
- **Primary:** `docs/plans/vfs_uplift/master_requirements.md` (98 requirements - what was built to)
- **Cross-validation:** `requirements-checklist.md` (~124 requirements - Claude-inferred from docs)

**Strategy:** Validate against both sources to catch everything - the master requirements plus valuable extras Claude inferred that might have been missed.

**Goal:** Generate final burn-down list of remaining work before merge (expected 5-10 items).

---

## Quick Start

### 1. Review Requirements
```bash
# Read the master requirements (98 atomic requirements)
cat docs/plans/vfs_uplift/master_requirements.md
```

### 2. Execute Validation
```bash
# See EXECUTION-GUIDE.md for detailed agent dispatch instructions
cat docs/plans/vfs_uplift/validation/EXECUTION-GUIDE.md
```

### 3. Review Progress from Runs 1-2
```bash
# See what's been fixed since the first two runs
cat docs/plans/vfs_uplift/validation/issues/INDEX.md
ls docs/plans/vfs_uplift/validation/issues/done/
```

---

## Documentation Structure

### Core Documents

**EXECUTION-GUIDE.md**
Agent dispatch plan for Run 3. Defines 10 agents:
- Agents 1-9: Validate 98 primary requirements from master_requirements.md
- Agent 10: Cross-validate ~26 extras from requirements-checklist.md + synthesize final report

**requirements-checklist.md**
Claude-inferred requirements (~124 total) extracted from plan documents. Used for cross-validation to catch valuable requirements not in master.

**evidence-standards.md**
What counts as valid evidence for each requirement type. Agents use this to classify requirements as DONE/PARTIAL/MISSING.

**quick-reference.md**
Common grep patterns and verification commands for quick validation.

### Reference Guides

**observation_modes_guide.md**
Reference for OBS-REQ-002 (observation modes: full_auto, max_compact, full_manual).

**interaction_radius_guide.md**
Reference for COMP-REQ-008 (continuous substrate interaction radius requirements).

**additional-requirements.md**
Supplementary requirements referenced by master_requirements.md (extensions, edge cases, policies).

### Progress Tracking

**issues/**
Issue tracking from Runs 1-2. See `issues/INDEX.md` for summary of completed work.

**issues/done/**
23 resolved issues demonstrating progress toward 90-95% completion target.

**reports/**
Output directory for Run 3 gap analysis reports (will be generated fresh).

---

## Validation Workflow

### Step 1: Prerequisites
```bash
# Record baseline commit
git rev-parse HEAD > docs/plans/vfs_uplift/validation/baseline-commit.txt

# Verify tests pass
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --tb=short -q | tail -20
```

### Step 2: Dispatch Agents
Follow EXECUTION-GUIDE.md to dispatch 9 parallel agents validating their assigned requirements.

### Step 3: Generate Reports
Agents output gap reports to `reports/` directory:
- **Primary validation** (Agents 1-9):
  - `gap-report-01-config-dtos.md` (CFG-REQ, DTO-REQ)
  - `gap-report-02-compiler.md` (COMP-REQ)
  - `gap-report-03-vfs.md` (VFS-REQ)
  - `gap-report-04-items.md` (ITEM-REQ)
  - `gap-report-05-effects.md` (EFF-REQ)
  - `gap-report-06-commands.md` (CMD-REQ)
  - `gap-report-07-obs-runtime.md` (OBS-REQ, RUN-REQ, MIG-REQ)
  - `gap-report-08-qa-testing.md` (QA-REQ, PERF-REQ)
  - `gap-report-09-policy-docs.md` (BREAK-REQ, POLICY-REQ, LIMIT-REQ, DOC-REQ)
- **Cross-validation** (Agent 10):
  - `gap-report-10-cross-validation.md` (extras from requirements-checklist.md)

### Step 4: Synthesize
Agent 10 aggregates all 10 reports into `gap-report-FINAL.md` with:
- Primary requirements status (98 reqs)
- Cross-validation findings (~26 extras)
- Valuable catches (important reqs not in master)
- Final burn-down list (5-10 items)

---

## Evidence Standards

Agents classify each requirement as:

- ✅ **DONE**: Full implementation + tests + integration + docs (where required)
- 🟡 **PARTIAL**: Implementation exists but incomplete (missing tests/docs/error handling)
- ❌ **MISSING**: Not implemented
- 📝 **N/A**: Documentation-only or policy requirement (no code needed)

See `evidence-standards.md` for detailed criteria.

---

## Expected Outcomes for Run 3

Based on progress from Runs 1-2 (23 completed issues), we expect:

**High Confidence (Should be DONE):**
- Compiler: Seven-stage pipeline, profile loading, effects compilation
- VFS: Scoped engine, profiles, observation integration
- Effects: Catalog schema, reapply policies, runtime manager
- Items: Manager runtime, inventory, profile-driven VFS
- Commands: Core DSL (modify, spawn_effect, if, for_each)
- Expression: Parser, AST, type checker, evaluator

**Likely Remaining (PARTIAL/MISSING):**
- Advanced spawn rules (grid/scripted placement, complex schedules)
- Mark-and-sweep VFS evaluation (may still be in eager mode)
- Advanced commands (switch, parallel, reduce, delay)
- Performance benchmarks validation
- Documentation polish (reference configs, guides)

**Final Burn-Down List:**
Run 3 will produce definitive list of remaining work before merge, likely 5-10 items.

---

## Progress Context (Runs 1-2)

**Run 1:** Identified ~40 gaps across all systems
**Run 2:** Resolved 23 critical issues, refined requirements
**Run 3:** Expected to find ~5-10 remaining gaps (5-10% of 98 requirements)

See `issues/INDEX.md` for detailed progress tracking.

---

## Related Documentation

**Master Requirements:**
- `docs/plans/vfs_uplift/master_requirements.md` (98 requirements)

**Plan Documents:**
- `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- `docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md`
- `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- `docs/plans/vfs_uplift/2025-11-23-runtime-vfs-effects-integration.md`

**VFS System Docs:**
- `docs/vfs-integration-guide.md`
- `configs/reference_config/VARIABLE_SUBSYSTEM.md`

---

## Questions?

For questions about:
- **Execution:** See EXECUTION-GUIDE.md
- **Evidence standards:** See evidence-standards.md
- **Requirement interpretation:** Check master_requirements.md Source column
- **Verification patterns:** See quick-reference.md

---

**Ready for Run 3.** Expected status: 90-95% complete. Goal: Final burn-down list for merge.
