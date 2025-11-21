# VFS Uplift Gap Analysis - Execution Plan

**Status:** Ready to Execute
**Created:** 2025-11-22
**Estimated Duration:** 6-12 hours (parallel execution)
**Baseline Commit:** da4adcf

---

## Objective

Execute systematic gap analysis of VFS uplift implementation by dispatching 6 parallel agents, each verifying their assigned requirements with file:line evidence, then synthesizing results into a final gap report.

---

## Prerequisites

**Before starting:**
- [ ] Baseline commit recorded: `git rev-parse HEAD > validation/baseline-commit.txt`
- [ ] All 435+ existing tests pass
- [ ] Working directory clean (no uncommitted changes that would interfere)
- [ ] Read `requirements-checklist.md` to understand scope (157 requirements)

**Verify prerequisites:**
```bash
cd /home/john/hamlet

# Record baseline
git rev-parse HEAD > docs/plans/vfs_uplift/validation/baseline-commit.txt

# Verify tests pass
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --co -q | wc -l  # Should be 435+

# Check working directory
git status --short  # Should be clean or only docs/plans/vfs_uplift/validation/ changes
```

---

## Phase 1: Parallel Agent Dispatch (4-8 hours)

### Execution Command

**Dispatch all 6 agents in a single message using multiple Task tool calls:**

```markdown
I need you to dispatch 6 gap analysis agents in parallel to verify VFS uplift requirements. Use the Task tool with 6 separate invocations in a single message.

Base your work on:
- Requirements: docs/plans/vfs_uplift/validation/requirements-checklist.md
- Evidence standards: docs/plans/vfs_uplift/validation/evidence-standards.md
- Agent assignments: docs/plans/vfs_uplift/validation/agent-assignment-template.md

Each agent should output their gap report to docs/plans/vfs_uplift/validation/reports/ directory.
```

---

### Agent 1: Compiler System (COMP-*)

**Prompt:**

```
You are analyzing the **Compiler System** for VFS uplift gap analysis.

**Your scope:** Requirements COMP-1 through COMP-20 (20 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Category 1)

**Primary files to examine:**
- src/townlet/universe/compiler.py (compilation pipeline)
- src/townlet/universe/compiled.py (CompiledUniverse schema)
- src/townlet/config/vfs_profiles_config.py (VFS profile DTOs)
- src/townlet/config/effects_config.py (Effects catalog DTOs)
- src/townlet/config/items_config.py (Items catalog DTOs)

**Test files:**
- tests/test_townlet/unit/universe/test_compiler.py
- tests/test_townlet/unit/universe/test_compiled.py

**Adjacent systems (reference but don't report):**
- src/townlet/vfs/profiles.py (VFS compilation - verify integration only)
- src/townlet/effects/catalog.py (Effects compilation - verify integration only)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Category 1 (COMP-*)
2. Read docs/plans/vfs_uplift/validation/evidence-standards.md for verification standards
3. For each COMP-* requirement:
   - Find implementation (file:line)
   - Find tests (test file:name)
   - Verify error handling exists
   - Assign status: ✅ COMPLETE, ⚠️ PARTIAL, ❌ MISSING, 🔍 UNCLEAR
4. For adjacent systems, note "not examined - [AGENT]'s scope"
5. Document evidence in table format

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-compiler.md

**Use this exact template:**

```markdown
# Gap Report: Compiler System (COMP-*)

**Agent:** Compiler Agent
**Date:** 2025-11-22
**Baseline:** [commit SHA]
**Requirements:** COMP-1 to COMP-20 (20 total)

## Summary

- ✅ COMPLETE: X requirements
- ⚠️ PARTIAL: X requirements
- ❌ MISSING: X requirements
- 🔍 UNCLEAR: X requirements

## Critical Gaps (P0)

[Table of ❌ MISSING requirements that are critical]

## Evidence Table

| Req ID | Requirement | Status | Evidence | Notes |
|--------|-------------|--------|----------|-------|
| COMP-1 | Seven-stage pipeline | ✅ COMPLETE | src/townlet/universe/compiler.py:145-892 | All 7 stages present |
| COMP-2 | Load VFS profiles | ❌ MISSING | Not found | No vfs_profiles.yaml loading in compiler |
[... continue for all COMP-* ...]

## Adjacent Systems Referenced

- VFS compilation (VFS agent's scope): Verified compiler calls VFSProfileCompiler.compile()
- Effects compilation (Effects agent's scope): Verified compiler calls EffectCatalog.from_config()
```

**Important:**
- Every claim MUST have file:line evidence
- Use grep/glob to find implementation
- Run tests to verify they pass
- Mark adjacent work as "not examined"
```

---

### Agent 2: VFS System (VFS-*)

**Prompt:**

```
You are analyzing the **VFS System** for VFS uplift gap analysis.

**Your scope:** Requirements VFS-1 through VFS-15 (15 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Category 2)

**Primary files to examine:**
- src/townlet/vfs/registry.py (VariableRegistry, scoped storage)
- src/townlet/vfs/profiles.py (VFS profile compilation)
- src/townlet/vfs/schema.py (VariableDef, scopes)
- src/townlet/vfs/evaluator.py (VFS expression evaluation)
- src/townlet/vfs/observation_builder.py (obs_vfs field)

**Test files:**
- tests/test_townlet/unit/vfs/test_registry.py
- tests/test_townlet/unit/vfs/test_profiles_dto.py
- tests/test_townlet/unit/vfs/test_observation_builder.py
- tests/test_townlet/integration/test_vfs_runtime_evaluation.py

**Adjacent systems (reference but don't report):**
- src/townlet/world/expression/ (expression parser - shared with Effects)
- src/townlet/universe/compiler.py (compiler integration)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Category 2 (VFS-*)
2. Read docs/plans/vfs_uplift/validation/evidence-standards.md
3. For each VFS-* requirement:
   - Find implementation (file:line)
   - Find tests (test file:name)
   - Verify expression evaluation works (run tests)
   - Assign status with evidence
4. Check for VFS-1 (expression language) - does evaluator.py execute expressions?
5. Check for VFS-8 (mark-and-sweep) - does it exist and work?
6. Check for VFS-12 (item VFS) - is storage profile-driven?

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-vfs.md

**Template:** Same structure as Agent 1, adapted for VFS-* requirements

**Critical requirements to verify:**
- VFS-1: Expression language support (evaluator module exists and works)
- VFS-2: Three scopes (global/agent/item all functional)
- VFS-8: Mark-and-sweep evaluation (not just eager mode)
- VFS-12: Item VFS profile-driven storage (not variables_reference.yaml)
```

---

### Agent 3: Effects System (EFF-*)

**Prompt:**

```
You are analyzing the **Effects System** for VFS uplift gap analysis.

**Your scope:** Requirements EFF-1 through EFF-20 (20 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Category 3)

**Primary files to examine:**
- src/townlet/effects/catalog.py (EffectCatalog compilation)
- src/townlet/effects/executor.py (Command execution)
- src/townlet/effects/manager.py (ActiveEffect lifecycle)
- src/townlet/effects/schema.py (EffectDef, CommandNode)
- src/townlet/effects/context.py (ExecutionContext)
- src/townlet/config/effects_config.py (DTOs)

**Test files:**
- tests/test_townlet/unit/effects/test_catalog_compilation.py
- tests/test_townlet/unit/effects/test_command_pipeline.py
- tests/test_townlet/unit/effects/test_effect_lifecycle.py
- tests/test_townlet/integration/test_effects_compiled_catalog.py

**Adjacent systems (reference but don't report):**
- src/townlet/vfs/registry.py (VFS writes - verify API usage only)
- src/townlet/universe/compiler.py (catalog compilation)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Category 3 (EFF-*)
2. For each EFF-* requirement:
   - Find implementation (file:line)
   - Find tests (test file:name)
   - Verify command types work (modify, spawn_effect, if, for_each, etc.)
   - Assign status with evidence

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-effects.md

**Critical requirements to verify:**
- EFF-1: Effects catalog as compiled artifact (in CompiledUniverse)
- EFF-5: Command pipeline execution (all command types work)
- EFF-10: Reapply policies (stack/renew/merge/replace all implemented)
- EFF-15: VFS path resolution (self.vfs.*, target.vfs.* work)
```

---

### Agent 4: Items System (ITEM-*)

**Prompt:**

```
You are analyzing the **Items System** for VFS uplift gap analysis.

**Your scope:** Requirements ITEM-1 through ITEM-16 (16 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Category 4)

**Primary files to examine:**
- src/townlet/items/manager.py (ItemManager, spawn/despawn)
- src/townlet/items/inventory.py (Agent inventory state)
- src/townlet/items/instance.py (ItemInstance dataclass)
- src/townlet/config/items_config.py (DTOs)

**Test files:**
- tests/test_townlet/unit/items/test_item_manager.py
- tests/test_townlet/unit/items/test_inventory.py
- tests/test_townlet/integration/test_items_integration.py
- tests/test_townlet/integration/test_item_vfs_observations.py

**Adjacent systems (reference but don't report):**
- src/townlet/vfs/registry.py (item VFS allocation - verify API calls only)
- src/townlet/effects/executor.py (spawn_item command)
- src/townlet/universe/compiler.py (catalog compilation)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Category 4 (ITEM-*)
2. For each ITEM-* requirement:
   - Find implementation (file:line)
   - Find tests (test file:name)
   - Verify vfs_profile field is honored
   - Assign status with evidence

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-items.md

**Critical requirements to verify:**
- ITEM-1: Item VFS profiles (vfs_profile field exists and functional)
- ITEM-5: vfs_profile field honored (items use correct profile on spawn)
- ITEM-8: Item VFS in observations (agents see held item VFS state)
- ITEM-12: GET/DROP/USE actions (all three work with inventory)
```

---

### Agent 5: Runtime Integration (RUN-*)

**Prompt:**

```
You are analyzing **Runtime Integration** for VFS uplift gap analysis.

**Your scope:** Requirements RUN-1 through RUN-12 (12 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Category 5)

**Primary files to examine:**
- src/townlet/environment/vectorized_env.py (main environment)
- src/townlet/vfs/observation_builder.py (obs construction)

**Test files:**
- tests/test_townlet/integration/test_vfs_runtime_evaluation.py
- tests/test_townlet/integration/test_item_vfs_observations.py
- tests/test_townlet/integration/test_effects_compiled_catalog.py

**Adjacent systems (reference ALL - this agent verifies integration):**
- src/townlet/vfs/evaluator.py (VFS evaluation)
- src/townlet/effects/manager.py (effects execution)
- src/townlet/items/manager.py (item spawning)
- src/townlet/universe/compiler.py (compiled artifacts usage)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Category 5 (RUN-*)
2. For each RUN-* requirement:
   - Find where vectorized_env.py integrates the feature
   - Verify it uses compiled artifacts (not runtime YAML)
   - Find integration tests
   - Assign status with evidence
3. Use grep to verify NO runtime YAML loading:
   ```bash
   grep -n "variables_reference.yaml" src/townlet/environment/vectorized_env.py
   grep -n "effects.yaml" src/townlet/environment/vectorized_env.py
   ```

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-runtime.md

**Critical requirements to verify:**
- RUN-1: Mark-and-sweep VFS evaluation (env.step() calls evaluator)
- RUN-2: Item VFS observations (not zero stubs - actual values)
- RUN-3: Use compiled catalog (no EffectCatalog.from_yaml() at runtime)
- RUN-7: No runtime variables_reference.yaml for item vars (grep verification)
```

---

### Agent 6: Testing & Documentation (TEST-*, DOC-*)

**Prompt:**

```
You are analyzing **Testing & Documentation** for VFS uplift gap analysis.

**Your scope:** Requirements TEST-1 through TEST-22, DOC-1 through DOC-10 (32 total)

**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md (Categories 6 & 7)

**Files to examine:**
- tests/ (all test files - count and verify pass)
- docs/config-schemas/ (schema documentation)
- docs/guides/ (user guides)

**Your task:**

1. Read docs/plans/vfs_uplift/validation/requirements-checklist.md Categories 6 & 7
2. For TEST-* requirements:
   - Count total tests: `pytest --co -q | wc -l`
   - Verify test pass rate: `pytest tests/ --tb=short`
   - Check coverage by system (grep for test files per module)
3. For DOC-* requirements:
   - Check if doc file exists
   - Verify it's not a stub (>100 lines with actual content)
   - Assign status with evidence

**Test counting commands:**
```bash
# Total tests
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --co -q | wc -l

# Tests by category
find tests/test_townlet/unit/vfs -name "test_*.py" -exec wc -l {} + | tail -1
find tests/test_townlet/unit/effects -name "test_*.py" -exec wc -l {} + | tail -1
find tests/test_townlet/unit/items -name "test_*.py" -exec wc -l {} + | tail -1
find tests/test_townlet/integration -name "test_*.py" -exec wc -l {} + | tail -1

# Run tests
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v --tb=short 2>&1 | tail -50
```

**Documentation verification:**
```bash
ls -lh docs/config-schemas/expressions.md 2>/dev/null || echo "MISSING"
ls -lh docs/config-schemas/vfs-profiles.md 2>/dev/null || echo "MISSING"
ls -lh docs/config-schemas/effects.md 2>/dev/null || echo "MISSING"
ls -lh docs/config-schemas/items.md 2>/dev/null || echo "MISSING"
ls -lh docs/guides/world-compiler-guide.md 2>/dev/null || echo "MISSING"
```

**Output:** docs/plans/vfs_uplift/validation/reports/gap-report-testing-docs.md

**Critical requirements to verify:**
- TEST-1: 270+ tests passing (from unified plan)
- TEST-20: Performance benchmarks (<5% regression target)
- DOC-1: Expression language reference (docs/config-schemas/expressions.md)
- DOC-2: VFS profiles schema (docs/config-schemas/vfs-profiles.md)
- DOC-5: World Compiler guide (docs/guides/world-compiler-guide.md)
```

---

## Phase 2: Report Collection (immediate)

**After all 6 agents complete:**

1. Verify all reports exist:
```bash
ls -lh docs/plans/vfs_uplift/validation/reports/gap-report-*.md
```

Expected:
- gap-report-compiler.md
- gap-report-vfs.md
- gap-report-effects.md
- gap-report-items.md
- gap-report-runtime.md
- gap-report-testing-docs.md

2. Quick scan for critical gaps:
```bash
grep -h "❌ MISSING" docs/plans/vfs_uplift/validation/reports/*.md | wc -l
grep -h "## Critical Gaps" -A 10 docs/plans/vfs_uplift/validation/reports/*.md
```

---

## Phase 3: Synthesis (2-4 hours)

### Synthesis Agent Task

**Prompt:**

```
You are synthesizing the gap analysis results from 6 parallel agents.

**Your task:**

1. Read all 6 gap reports from docs/plans/vfs_uplift/validation/reports/

2. Create a merged gap report at docs/plans/vfs_uplift/validation/reports/gap-report-final.md

3. For each requirement (157 total):
   - Collect status from appropriate agent
   - Verify ADJACENT markers match (if Agent A says "VFS-12 not examined", verify Agent 2 examined VFS-12)
   - Resolve conflicts (if two agents claim same requirement)

4. Identify integration gaps:
   - Agent A calls Agent B's API but Agent B didn't verify the API works
   - Cross-system dependencies with no tests

5. Prioritize all gaps:
   - P0 (Critical): Breaks core functionality, must fix before merge
   - P1 (Important): Missing feature or incomplete implementation, should fix
   - P2 (Minor): Polish or nice-to-have, can defer

6. Calculate statistics:
   - Total requirements: 157
   - Complete: X (Y%)
   - Partial: X
   - Missing: X
   - Unclear: X

7. Create action plan:
   - For each P0 gap: What needs to be done, estimated effort
   - For each P1 gap: What's missing, priority ranking
   - For P2 gaps: List for backlog

**Template:**

```markdown
# VFS Uplift Gap Analysis - Final Report

**Date:** 2025-11-22
**Baseline Commit:** [SHA]
**Analysts:** 6 parallel agents + synthesis
**Total Requirements:** 157

---

## Executive Summary

**Overall Status:**
- ✅ COMPLETE: X requirements (Y%)
- ⚠️ PARTIAL: X requirements (Y%)
- ❌ MISSING: X requirements (Y%)
- 🔍 UNCLEAR: X requirements (Y%)

**Recommendation:** [READY FOR MERGE / NEEDS WORK / BLOCKED]

**Critical Gaps:** X (must fix before merge)
**Important Gaps:** X (should fix soon)
**Minor Gaps:** X (backlog)

---

## Critical Gaps (P0 - Must Fix Before Merge)

| Req ID | Category | Requirement | Impact | Estimated Effort | Owner |
|--------|----------|-------------|--------|------------------|-------|
| RUN-1 | Runtime | Mark-and-sweep evaluation | No VFS evaluation at runtime | 3-4 days | VFS team |
| RUN-2 | Runtime | Item VFS observations | Observations are zero stubs | 2-3 days | Items team |
[... list all P0 gaps ...]

**Total P0 Effort:** X days

---

## Important Gaps (P1 - Should Fix)

[Table of P1 gaps with effort estimates]

**Total P1 Effort:** X days

---

## Minor Gaps (P2 - Can Defer)

[Table of P2 gaps]

---

## Detailed Requirements Status

### Category 1: Compiler (20 requirements)
[Status table for COMP-1 to COMP-20]

### Category 2: VFS System (15 requirements)
[Status table for VFS-1 to VFS-15]

[... continue for all 8 categories ...]

---

## Integration Analysis

**Cross-System Dependencies Verified:**
- ✅ Compiler → VFS: VFSProfileCompiler integration works
- ✅ Compiler → Effects: EffectCatalog compilation works
- ❌ Runtime → VFS: Evaluator not called in env.step()
- ⚠️ Items → VFS: API integration works but no E2E test

**Integration Gaps:**
[List any missing integration points]

---

## Action Plan

### Immediate (Before Merge - P0 Gaps)

1. **RUN-1: Implement mark-and-sweep VFS evaluation**
   - File: src/townlet/vfs/evaluator.py
   - What: Create VFSEvaluator class with mark-and-sweep mode
   - Effort: 3-4 days
   - Blocker: Critical

2. **RUN-2: Wire item VFS observations**
   - File: src/townlet/vfs/observation_builder.py
   - What: Replace zero stub with actual item VFS values
   - Effort: 2-3 days
   - Blocker: Critical

[... list all P0 action items ...]

### Short-Term (P1 Gaps - Next Sprint)

[List P1 action items with effort]

### Backlog (P2 Gaps)

[List P2 items for future work]

---

## Risk Assessment

**High Risk (Merge Blockers):**
- X critical gaps (P0)
- Estimated X days to resolve
- [Any specific technical risks]

**Medium Risk:**
- X important gaps (P1)
- May cause issues in production
- Can be addressed post-merge with hotfix

**Low Risk:**
- X minor gaps (P2)
- Polish and documentation
- Safe to defer

---

## Recommendations

**Merge Decision:** [READY / NOT READY / CONDITIONAL]

**If NOT READY:**
- Must complete P0 gaps: [list]
- Estimated time: X days
- Re-run gap analysis after fixes

**If CONDITIONAL:**
- Can merge if: [conditions]
- Must track: [P1 gaps as issues]
- Timeline: [when to address]

**If READY:**
- All critical functionality present
- P1/P2 gaps documented for backlog
- Zero regressions verified

---

## Appendix: Agent Reports

- [gap-report-compiler.md](./gap-report-compiler.md)
- [gap-report-vfs.md](./gap-report-vfs.md)
- [gap-report-effects.md](./gap-report-effects.md)
- [gap-report-items.md](./gap-report-items.md)
- [gap-report-runtime.md](./gap-report-runtime.md)
- [gap-report-testing-docs.md](./gap-report-testing-docs.md)
```
```

---

## Success Criteria

**Phase 1 Success:**
- [ ] All 6 agents complete without errors
- [ ] All 6 gap reports generated
- [ ] Every requirement has status assigned
- [ ] All claims have file:line evidence

**Phase 2 Success:**
- [ ] All reports collected and readable
- [ ] Critical gaps identified (grep verification)

**Phase 3 Success:**
- [ ] Final report synthesized
- [ ] All 157 requirements accounted for
- [ ] ADJACENT markers resolved
- [ ] Integration gaps identified
- [ ] Action plan created with effort estimates
- [ ] Merge recommendation provided

---

## Failure Recovery

**If agent fails:**
1. Check error message
2. Fix issue (missing file, syntax error)
3. Re-dispatch only failed agent
4. Continue with others

**If synthesis fails:**
1. Verify all 6 reports exist and are readable
2. Check for conflicting status (two agents claim same req)
3. Manually resolve conflicts
4. Re-run synthesis

---

## Post-Execution

**After final report complete:**

1. Commit all reports:
```bash
git add docs/plans/vfs_uplift/validation/reports/
git add docs/plans/vfs_uplift/validation/baseline-commit.txt
git commit -m "docs(validation): gap analysis results - [DATE]

6 parallel agents verified 157 requirements:
- ✅ Complete: X (Y%)
- ⚠️ Partial: X (Y%)
- ❌ Missing: X (Y%)

Critical gaps (P0): X
Important gaps (P1): X
Minor gaps (P2): X

Recommendation: [READY/NOT READY/CONDITIONAL]

See gap-report-final.md for details."
```

2. Review with team:
   - Share gap-report-final.md
   - Discuss P0 gaps and timeline
   - Assign action items

3. Track gaps as issues:
```bash
# Create issues for P0 gaps
gh issue create --title "P0: [REQ-ID] [Requirement]" --body "See gap-report-final.md"
```

---

## Timeline Estimate

**Optimistic (6 hours):**
- Phase 1: 4 hours (all agents fast)
- Phase 2: 30 minutes (quick scan)
- Phase 3: 2 hours (synthesis)

**Realistic (8-10 hours):**
- Phase 1: 6-8 hours (some agents slow)
- Phase 2: 30 minutes
- Phase 3: 3-4 hours (complex synthesis)

**Pessimistic (12+ hours):**
- Phase 1: 8-10 hours (agents encounter issues)
- Phase 2: 1 hour (report issues)
- Phase 3: 4-6 hours (conflicts to resolve)

---

## Ready to Execute

This plan is ready for immediate execution. To start:

1. Verify prerequisites
2. Dispatch all 6 agents in parallel (single message, 6 Task tool calls)
3. Wait for completion (4-8 hours)
4. Run synthesis agent
5. Review final report
6. Create action plan

**Command to execute:** See "Phase 1: Parallel Agent Dispatch" above
