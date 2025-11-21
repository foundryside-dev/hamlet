# VFS Uplift Validation Suite

**Purpose:** Systematic gap analysis for VFS uplift implementation readiness

**Created:** 2025-11-22
**Status:** Ready for use

---

## Overview

This validation suite provides tools for comprehensive gap analysis of the VFS uplift implementation against the master requirements extracted from four foundational plan documents.

**Source Plans:**
1. `2025-11-19-unified-world-compiler-plan.md` - Overall architecture and phasing
2. `2025-11-18-items-and-vfs-profiles.md` - Items system and VFS profiles design
3. `2025-11-19-effects-system-design.md` - Effects system architecture
4. `2025-11-23-runtime-vfs-effects-integration.md` - Runtime integration plan

---

## Documents in This Suite

### 1. requirements-checklist.md
**Purpose:** Master list of all 157 requirements extracted from plans

**Structure:**
- 8 categories (Compiler, VFS, Effects, Items, Runtime, Testing, Documentation, Breaking Changes)
- Each requirement has:
  - Unique ID (e.g., COMP-1, VFS-5, EFF-10)
  - Source reference (plan file and line number)
  - Detailed requirement text
  - Evidence checklist (what to verify)
- Summary statistics and cross-cutting concerns

**Use this to:**
- Get comprehensive view of all requirements
- Understand requirement dependencies
- Identify which requirements belong together

---

### 2. gap-report-template.md
**Purpose:** Template for generating gap analysis reports

**Structure:**
- Executive summary (status counts, critical gaps)
- Critical gaps table (P0 - must fix before merge)
- Important gaps table (P1 - should fix soon)
- Minor gaps table (P2 - nice to have)
- Detailed verification evidence (all 157 requirements)
- Summary by category
- Priority breakdown with effort estimates
- Recommendations (immediate actions, follow-up work, future work)
- Risk assessment
- Conclusion and next steps
- Verification commands (grep patterns, test counts)

**Use this to:**
- Generate gap analysis reports
- Track implementation progress
- Communicate status to stakeholders
- Plan sprints based on priority breakdown

---

### 3. evidence-standards.md
**Purpose:** Define what counts as valid evidence for each status level

**Structure:**
- Evidence quality levels (✅ COMPLETE, ⚠️ PARTIAL, ❌ MISSING, 🔍 UNCLEAR)
- Evidence requirements by requirement type (Config/Schema, Compiler, Runtime, Expression/AST, VFS, Effects, Items, Testing, Documentation, Breaking Changes)
- Common pitfalls (false positives/negatives)
- Verification workflow (7-step process)
- Evidence template
- Quality checklist

**Use this to:**
- Understand what evidence is needed for each requirement
- Avoid common mistakes in gap analysis
- Ensure consistent evidence quality across analysts
- Know when to mark something as COMPLETE vs PARTIAL

---

## How to Perform Gap Analysis

### Step 1: Review Requirements
```bash
# Read the master checklist
cat docs/plans/vfs_uplift/validation/requirements-checklist.md

# Focus on a specific category (e.g., Runtime Integration)
grep -A 5 "Category 5: Runtime Integration" docs/plans/vfs_uplift/validation/requirements-checklist.md
```

### Step 2: Set Up Evidence Standards
```bash
# Read evidence standards to understand what counts as "complete"
cat docs/plans/vfs_uplift/validation/evidence-standards.md

# Focus on relevant requirement types (e.g., Runtime Requirements)
grep -A 20 "### Runtime Requirements" docs/plans/vfs_uplift/validation/evidence-standards.md
```

### Step 3: Verify Each Requirement
For each requirement in the checklist:

1. **Search for implementation**
   ```bash
   # Example: VFS evaluation (RUN-1)
   grep -r "mark_and_sweep" src/townlet/vfs/
   grep -r "VFSEvaluator" src/townlet/
   find src/townlet/vfs/ -name "*evaluator*"
   ```

2. **Search for tests**
   ```bash
   # Example: VFS evaluation tests
   find tests/test_townlet/unit/vfs/ -name "*evaluator*"
   grep -r "mark_and_sweep" tests/test_townlet/
   pytest --collect-only tests/test_townlet/unit/vfs/
   ```

3. **Read implementation** (verify semantics match requirement)

4. **Read tests** (verify coverage of happy path + error cases)

5. **Check integration** (verify wired into environment/compiler)

6. **Check documentation** (verify schema docs/guides exist)

7. **Assign status** using evidence-standards.md criteria

### Step 4: Fill Out Gap Report
```bash
# Copy template
cp docs/plans/vfs_uplift/validation/gap-report-template.md \
   docs/plans/vfs_uplift/validation/gap-report-2025-11-22.md

# Fill in:
# - Date, analyzer, baseline commit
# - Status for each requirement (using evidence from Step 3)
# - Summary statistics
# - Critical/important/minor gaps tables
# - Recommendations with effort estimates
# - Risk assessment
```

### Step 5: Review and Iterate
1. **Sanity check:** Do summary statistics match detailed evidence?
2. **Completeness check:** All 157 requirements have status?
3. **Priority check:** Are P0 gaps truly blocking merge?
4. **Effort check:** Do estimates seem reasonable?
5. **Recommendation check:** Are next steps actionable?

---

## Quick Start: Focus on High-Risk Areas

If short on time, focus gap analysis on these high-risk categories first:

### Priority 1: Runtime Integration (RUN-*)
**Why critical:** Core functionality, determines if system works end-to-end

**Key requirements:**
- RUN-1: Mark-and-sweep VFS evaluation
- RUN-2: Item VFS observations
- RUN-3: Compiled catalog usage
- RUN-11: VFS evaluation at runtime

**Verification:**
```bash
# Check if VFS evaluator exists
find src/townlet/vfs/ -name "*evaluator*" -o -name "*eval*"

# Check if item VFS obs are real data (not zeros)
grep -A 5 "item_vfs" src/townlet/vfs/observation_builder.py

# Check if env uses compiled catalogs (not runtime YAML)
grep "EffectCatalog" src/townlet/environment/vectorized_env.py
grep "effects.yaml" src/townlet/environment/vectorized_env.py
```

### Priority 2: Compiler Integration (COMP-2, COMP-3, COMP-14)
**Why critical:** Determines if compiled artifacts are available at runtime

**Key requirements:**
- COMP-2: VFS profiles compiled into CompiledUniverse
- COMP-3: Effects catalog compiled into CompiledUniverse
- COMP-14: CompiledUniverse schema extensions

**Verification:**
```bash
# Check CompiledUniverse fields
grep "compiled_vfs_profiles\|compiled_effect_catalog" src/townlet/universe/compiled.py

# Check compiler loads profiles/effects
grep "vfs_profiles.yaml\|effects.yaml" src/townlet/universe/compiler.py
```

### Priority 3: Test Coverage (TEST-1, TEST-20, TEST-21)
**Why critical:** Prevents regressions, validates functionality

**Key requirements:**
- TEST-1: 270+ tests total (baseline met, new tests needed)
- TEST-20: Performance validation (<5% overhead)
- TEST-21: Runtime integration tests

**Verification:**
```bash
# Count tests by category
pytest --collect-only tests/test_townlet/unit/world/expression/ | grep "test_"
pytest --collect-only tests/test_townlet/unit/vfs/ | grep "test_"
pytest --collect-only tests/test_townlet/unit/effects/ | grep "test_"
pytest --collect-only tests/test_townlet/unit/items/ | grep "test_"

# Check for performance benchmarks
find tests/ -name "*benchmark*" -o -name "*perf*"

# Check for runtime integration tests
grep -r "compiled.*catalog\|mark_and_sweep" tests/test_townlet/integration/
```

---

## Expected Timeline

**Full gap analysis:** 1-2 days
- Requirement verification: 4-6 hours
- Evidence collection: 4-6 hours
- Report writing: 2-3 hours
- Review and iteration: 1-2 hours

**Quick gap analysis (high-risk only):** 4-6 hours
- Focus on RUN-*, COMP-2/3/14, TEST-20/21
- Minimal evidence collection
- Executive summary only

---

## Integration with Development Workflow

### Before Starting Implementation
1. Run gap analysis to establish baseline
2. Identify P0 gaps (blockers)
3. Create task plan based on gap report recommendations

### During Implementation
1. Update gap report after each completed task
2. Track status changes (❌ → ⚠️ → ✅)
3. Verify test counts meet targets

### Before Merge/PR
1. Run final gap analysis
2. Verify all P0 gaps closed
3. Document remaining P1/P2 gaps for follow-up
4. Confirm zero regressions (RUN-12)

---

## Output Format Examples

### Executive Summary Format
```
**Total Requirements:** 157
**Complete (✅):** 105 (67%)
**Partial (⚠️):** 28 (18%)
**Missing (❌):** 18 (11%)
**Unclear (🔍):** 6 (4%)

**Overall Status:** NEEDS WORK
**Critical Gaps:** 3 (runtime VFS evaluation, item VFS obs, compiled catalogs)
```

### Gap Table Format
```
| Req ID | Category | Requirement | Impact | Evidence | Priority |
|--------|----------|-------------|--------|----------|----------|
| RUN-1 | Runtime | Mark-and-sweep VFS eval | Core feature missing | No evaluator at src/townlet/vfs/evaluator.py | P0 |
| RUN-2 | Runtime | Item VFS observations | Returns zero stubs | observation_builder.py:XXX hardcoded zeros | P0 |
```

### Recommendation Format
```
### Immediate Actions (Before Merge)
1. **Implement runtime VFS evaluation** (RUN-1, VFS-6)
   - Create vfs/evaluator.py module
   - Mark-and-sweep + eager modes
   - Wire into env.step()
   - Target: 3-4 days

2. **Fix item VFS observations** (RUN-2, VFS-10)
   - Replace zero stubs with real data
   - Target: 1-2 days
```

---

## Maintenance

### When to Update This Suite

**Update requirements-checklist.md when:**
- New plan documents added
- Requirements change in existing plans
- New cross-cutting concerns identified

**Update gap-report-template.md when:**
- New verification commands needed
- New report sections required
- Priority breakdown structure changes

**Update evidence-standards.md when:**
- New requirement types added (e.g., "Curriculum Requirements")
- Common pitfalls discovered
- Verification workflow improvements

---

## Related Documentation

**Plan Documents:**
- `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- `docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md`
- `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
- `docs/plans/vfs_uplift/2025-11-23-runtime-vfs-effects-integration.md`

**Implementation Status:**
- `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

**VFS System Docs:**
- `docs/vfs-integration-guide.md`
- `configs/reference_config/VARIABLE_SUBSYSTEM.md`

---

## Questions?

For questions about:
- **Requirement interpretation:** Check source plan document (line numbers in requirements-checklist.md)
- **Evidence standards:** See evidence-standards.md
- **Gap report format:** See gap-report-template.md
- **Verification commands:** See gap-report-template.md Appendix A

For issues with this validation suite, contact the VFS uplift team or create an issue.
