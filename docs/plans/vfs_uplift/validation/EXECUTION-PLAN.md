# VFS Uplift Gap Analysis - Execution Plan (EXPANDED)

**Status:** Ready to Execute
**Updated:** 2025-11-23 (Expanded from 5 source documents)
**Total Requirements:** 246 (157 original + 89 new)
**Baseline Commit:** ac67272
**Agents:** 10 (9 parallel + 1 synthesis)
**Sources:** unified-world-compiler-plan.md, items-and-vfs-profiles.md, effects-system-design.md, runtime-vfs-effects-integration.md, command_reference.md

---

## Objective

Execute systematic gap analysis of VFS uplift implementation by dispatching **10 parallel agents**, each verifying their assigned requirements with file:line evidence, then synthesizing results into a final gap report.

---

## Agent Division (No Overlap)

| Agent | Scope | Original | New | Total |
|-------|-------|----------|-----|-------|
| 1 | Compiler & Schema | COMP (20) | COMP-EXT (8) | **28** |
| 2 | VFS System | VFS (15) | VFS-EXT (8) | **23** |
| 3 | Effects System | EFF (20) | EFF-EXT (8) | **28** |
| 4 | **Commands** | — | CMD (22) | **22** |
| 5 | Items System | ITEM (16) | ITEM-EXT (16) | **32** |
| 6 | Runtime Integration | RUN (12) | RUN-EXT (7), LIMITS (7) | **26** |
| 7 | Testing | TEST (22) | TEST-EXT (8) | **30** |
| 8 | Documentation | DOC (10) | DOC-EXT (7) | **17** |
| 9 | Breaking Changes | BREAK (9), Derived (33) | — | **42** |
| 10 | Synthesis | Aggregate all 9 reports | — | **—** |

**Total:** 246 requirements (157 original + 89 new)

**New Categories:**
- **CMD**: Command-specific implementations (switch, for_each, parallel, reduce, delay, while, emit)
- **LIMITS**: Runtime limits and safeguards (collection size, effect depth, delay caps, queue limits)
- ***-EXT**: Extensions to existing categories with detailed implementation requirements

---

## Prerequisites

**Before starting:**

- [ ] Baseline commit recorded: `git rev-parse HEAD > validation/baseline-commit.txt`
- [ ] All 1945+ existing tests pass
- [ ] Working directory clean (no uncommitted changes that would interfere)
- [ ] Read `requirements-summary-expanded.md` to understand scope (246 requirements)
- [ ] Read `additional-requirements.md` for new categories (CMD, LIMITS, *-EXT)
- [ ] Read original `requirements-checklist.md` (157 baseline requirements)

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

## Phase 1: Parallel Agent Dispatch

### Execution Command

**Dispatch all 9 analysis agents in a single message using multiple Task tool calls:**

```markdown
I need you to dispatch 9 gap analysis agents in parallel to verify VFS uplift requirements. Use the Task tool with 9 separate invocations in a single message.

Base your work on:
- Requirements: docs/plans/vfs_uplift/validation/requirements-checklist.md
- Evidence standards: docs/plans/vfs_uplift/validation/evidence-standards.md
- Agent assignments: See EXECUTION-PLAN-CORRECTED.md

Each agent should output their gap report to docs/plans/vfs_uplift/validation/reports/ directory.
```

---

## Agent 1: Compiler & Schema (COMP-1 to COMP-20, COMP-EXT-1 to COMP-EXT-8)

**Scope:** 28 requirements (20 original + 8 extensions)

**Primary files to examine:**

- `src/townlet/universe/compiler.py` (UniverseCompiler class, seven-stage pipeline)
- `src/townlet/universe/compiled.py` (CompiledUniverse class)
- `src/townlet/config/vfs_profiles_config.py` (VFS profile DTOs)
- `src/townlet/config/effects_config.py` (Effects catalog DTOs)
- `src/townlet/config/items_config.py` (Items catalog DTOs)
- `src/townlet/world/expression/parser.py` (expression parser)
- `src/townlet/world/expression/type_checker.py` (type checker)
- `src/townlet/world/expression/evaluator.py` (evaluator)

**Test files:**

- `tests/test_townlet/unit/universe/test_compiler_pipeline.py`
- `tests/test_townlet/unit/universe/test_compiler_comprehensive.py`
- `tests/test_townlet/unit/universe/test_compiled_universe.py`
- `tests/test_townlet/unit/universe/test_compiler_cli.py`
- `tests/test_townlet/unit/config/test_vfs_profiles_dto.py`
- `tests/test_townlet/unit/config/test_effects_config_dto.py`
- `tests/test_townlet/unit/config/test_items_config_dto.py`
- `tests/test_townlet/unit/world/expression/test_parser.py`
- `tests/test_townlet/unit/world/expression/test_type_checker.py`
- `tests/test_townlet/unit/world/expression/test_evaluator.py`

**Critical requirements:**

- COMP-1: Seven-stage pipeline exists and works
- COMP-2: VFS profiles loaded at compile time
- COMP-3: Effects catalog compiled (not runtime)
- COMP-7: Expression parser with precedence
- COMP-9: Type checker with error reporting
- COMP-13: Error reporting with file context
- COMP-18: No-defaults enforcement

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-01-compiler.md`

---

## Agent 2: VFS System (VFS-1 to VFS-15, VFS-EXT-1 to VFS-EXT-8)

**Scope:** 23 requirements (15 original + 8 extensions)

**Priority Extensions:**
- **VFS-EXT-1 (P0)**: Expression XOR initial_value enforcement - CRITICAL for correctness
- **VFS-EXT-7 (P1)**: Evaluation ordering (global → agent → item) - core feature
- **VFS-EXT-8 (P1)**: Item profile defaults - core feature

**Primary files to examine:**

- `src/townlet/vfs/registry.py` (VariableRegistry - scoped storage)
- `src/townlet/vfs/profiles.py` (VFSProfileCompiler - THE MAIN VFS COMPILER)
- `src/townlet/vfs/schema.py` (VariableDef, scopes)
- `src/townlet/vfs/evaluator.py` (VFSEvaluator - mark-and-sweep evaluation)
- `src/townlet/vfs/observation_builder.py` (observation specs, item VFS)

**Test files:**

- `tests/test_townlet/unit/vfs/test_registry.py`
- `tests/test_townlet/unit/vfs/test_observation_builder.py`
- `tests/test_townlet/unit/vfs/test_variable_registry_tensor.py`
- `tests/test_townlet/unit/universe/test_vfs_profile_compilation.py`
- `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

**Critical requirements:**

- VFS-1: Expression language support (evaluator exists and works)
- VFS-2: Three scopes (global/agent/item all functional)
- VFS-6: Mark-and-sweep evaluation (not eager-only)
- VFS-8: Profile-driven item storage (not variables_reference.yaml)
- VFS-10: Item VFS observations (not zero stubs)
- VFS-15: VFS in ExecutionContext (accessible to effects)

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-02-vfs.md`

---

## Agent 3: Effects System (EFF-1 to EFF-20, EFF-EXT-1 to EFF-EXT-8)

**Scope:** 28 requirements (20 original + 8 extensions)

**Primary files to examine:**

- `src/townlet/effects/catalog.py` (EffectCatalog compilation)
- `src/townlet/effects/executor.py` (CommandExecutor)
- `src/townlet/effects/manager.py` (EffectManager, NullItemManager)
- `src/townlet/effects/schema.py` (CommandNode, CommandType)
- `src/townlet/effects/context.py` (ExecutionContext)
- `src/townlet/config/effects_config.py` (EffectDefinitionConfig)

**Test files:**

- `tests/test_townlet/unit/effects/test_catalog_compilation.py`
- `tests/test_townlet/unit/effects/test_command_executor.py`
- `tests/test_townlet/unit/effects/test_command_compiler.py`
- `tests/test_townlet/unit/effects/test_command_parser.py`
- `tests/test_townlet/unit/effects/test_effect_manager.py`
- `tests/test_townlet/unit/effects/test_lifecycle_interrupt.py`
- `tests/test_townlet/unit/effects/test_reference_types_runtime.py`
- `tests/test_townlet/integration/test_effects_compiled_catalog.py`

**Critical requirements:**

- EFF-1: Effects catalog as compiled artifact (in CompiledUniverse)
- EFF-2: Command pipeline execution (all stages work)
- EFF-6: Reapply policies (stack/renew/merge/replace)
- EFF-8 to EFF-12: All command types work
- EFF-13: Path notation (self.vfs.*, target.vfs.*, target.bar.*)
- EFF-14: Expression language integration
- EFF-15: Type safety in commands

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-03-effects.md`

---

## Agent 4: Commands (CMD-SWITCH-1 to CMD-EMIT-1) - NEW AGENT

**Scope:** 22 requirements (all new from command_reference.md)

**Primary files to examine:**

- `src/townlet/effects/executor.py` (CommandExecutor - all command implementations)
- `src/townlet/effects/compiler.py` (CommandCompiler - command AST compilation)
- `src/townlet/effects/parser.py` (CommandParser - YAML to AST)
- `src/townlet/effects/schema.py` (CommandNode, CommandType)
- `src/townlet/effects/scheduler.py` (Scheduler for delay commands)
- `src/townlet/effects/collections.py` (Collection resolvers: all_agents, nearby_agents, etc.)

**Test files:**

- `tests/test_townlet/unit/effects/test_command_executor.py`
- `tests/test_townlet/unit/effects/test_command_compiler.py`
- `tests/test_townlet/unit/effects/test_for_each.py`
- `tests/test_townlet/unit/effects/test_switch_executor.py`
- `tests/test_townlet/unit/effects/test_parallel_compiler.py`
- `tests/test_townlet/unit/effects/test_reduce_executor.py`
- `tests/test_townlet/unit/effects/test_delay_executor.py`
- `tests/test_townlet/unit/effects/test_delay_alignment.py`
- `tests/test_townlet/unit/effects/test_scheduler.py`

**Critical requirements:**

- **CMD-FOREACH-1 (P0)**: MAX_COLLECTION_SIZE = 256 enforcement (safety)
- **CMD-FOREACH-2 (P0)**: Nested for_each prohibition (safety)
- **CMD-SWITCH-1, CMD-SWITCH-2, CMD-SWITCH-3 (P1)**: Switch implementation (equality matching, type validation, tensor broadcasting)
- **CMD-PARALLEL-1, CMD-PARALLEL-2 (P1)**: Parallel semantics (disjoint writes, sequential execution)
- **CMD-REDUCE-1, CMD-REDUCE-2, CMD-REDUCE-3 (P1)**: Reduce implementation (fixed-size, type consistency, required fields)
- **CMD-DELAY-1 through CMD-DELAY-5 (P1)**: Delay implementation (time_enabled, limits, queue cap, zero-delay, persistence)
- **CMD-WHILE-1 (P3)**: While loop NOT IMPLEMENTED (future work)
- **CMD-EMIT-1 (P3)**: Emit event NOT IMPLEMENTED (future work)

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-04-commands.md`

---

## Agent 5: Items System (ITEM-1 to ITEM-16, ITEM-EXT-1 to ITEM-EXT-16)

**Scope:** 32 requirements (16 original + 16 extensions)

**Priority Extensions:**
- **ITEM-EXT-5 (P1)**: Conditional spawn with VFS predicates - core feature
- **ITEM-EXT-1 through ITEM-EXT-4 (P2)**: Item spawn features (placement, schedule, limits, priority)

**Primary files to examine:**

- `src/townlet/items/manager.py` (ItemManager - spawn/despawn/lifecycle)
- `src/townlet/items/inventory.py` (InventoryState - per-agent inventory)
- `src/townlet/items/instance.py` (ItemInstance dataclass)
- `src/townlet/items/action_handlers.py` (GET/DROP/USE actions)
- `src/townlet/config/items_config.py` (ItemTypeConfig with vfs_profile field)

**Test files:**

- `tests/test_townlet/unit/items/test_item_manager.py`
- `tests/test_townlet/unit/items/test_inventory.py`
- `tests/test_townlet/integration/test_items_integration.py`
- `tests/test_townlet/integration/test_item_vfs_observations.py`

**Critical requirements:**

- ITEM-1: Item VFS profiles binding (vfs_profile field exists)
- ITEM-2: Inventory management (max_items_per_agent enforced)
- ITEM-5: Action handlers (GET/DROP/USE all work)
- ITEM-9: Item interactions via Effects (spawn_item command)
- ITEM-13: Item position tracking
- ITEM-14: Item VFS state allocation (profile-driven)
- ITEM-16: INTERACT action for affordances

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-04-items.md`

---

## Agent 6: Runtime Integration (RUN-1 to RUN-12, RUN-EXT-1 to RUN-EXT-7, LIMITS-1 to LIMITS-7)

**Scope:** 26 requirements (12 original + 7 runtime extensions + 7 limits)

**Priority Requirements:**
- **LIMITS-1 through LIMITS-7 (P0)**: All runtime caps (safety-critical)
  - MAX_COLLECTION_SIZE = 256
  - Effect spawn depth = 10
  - MAX_DELAY_TICKS = 1,000
  - MAX_SCHEDULED_ITEMS = 10,000
  - Item pool caps, profile counts, spawn rules
- **RUN-EXT-5 (P0)**: Zero-stub removal - correctness critical
- **RUN-EXT-1 (P1)**: Eager fallback mode - debug essential

**Primary files to examine:**

- `src/townlet/environment/vectorized_env.py` (main environment - VFS/effects integration)
- `src/townlet/vfs/observation_builder.py` (build_vfs_observation function)
- `src/townlet/effects/manager.py` (effect step integration)
- `src/townlet/items/manager.py` (item spawn with profiles)

**Test files:**

- `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`
- `tests/test_townlet/integration/test_item_vfs_observations.py`
- `tests/test_townlet/integration/test_effects_compiled_catalog.py`

**Critical requirements:**

- RUN-1: Mark-and-sweep VFS evaluation (env.step() calls evaluator)
- RUN-2: Item VFS observations (actual values, not zero stubs)
- RUN-3: Compiled catalog usage (NO EffectCatalog.from_yaml() at runtime)
- RUN-4: ExecutionContext construction (correct state access)
- RUN-8: Performance target (<5% overhead)
- RUN-11: VFS evaluation at runtime (verify happens every step)
- RUN-12: Zero regressions (all 435+ tests pass)

**Verification commands:**

```bash
# Verify NO runtime YAML loading
grep -n "variables_reference.yaml" src/townlet/environment/vectorized_env.py  # Should be empty
grep -n "effects.yaml" src/townlet/environment/vectorized_env.py  # Should be empty
grep -n "EffectCatalog.from_yaml" src/townlet/environment/vectorized_env.py  # Should be empty

# Verify compiled artifacts are used
grep -n "compiled_universe" src/townlet/environment/vectorized_env.py  # Should exist
```

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-05-runtime.md`

---

## Agent 7: Testing (TEST-1 to TEST-22, TEST-EXT-1 to TEST-EXT-8)

**Scope:** 30 requirements (22 original + 8 extensions)

**Priority Extensions:**
- **TEST-EXT-1 (P1)**: Dimension regression tests (obs_dim stability)
- **TEST-EXT-2 (P1)**: Checkpoint roundtrip tests (item VFS state)
- **TEST-EXT-5 (P1)**: Type safety negative tests (compile errors)
- **TEST-EXT-6 (P1)**: Reapply policy tests (one per policy)

**Primary files to examine:**

- All test files under `tests/test_townlet/`
- Test configuration fixtures

**Critical requirements:**

- TEST-1: 270+ tests total (count via pytest --co)
- TEST-2 to TEST-18: Category-specific test coverage
- TEST-19: Complete pipeline tests (E2E)
- TEST-20: Performance validation benchmarks
- TEST-21: Runtime integration tests
- TEST-22: Test config packs

**Verification commands:**

```bash
# Total test count
UV_CACHE_DIR=.uv-cache uv run pytest tests/ --co -q | wc -l

# Tests by category
find tests/test_townlet/unit/universe -name "test_*.py" | wc -l
find tests/test_townlet/unit/vfs -name "test_*.py" | wc -l
find tests/test_townlet/unit/effects -name "test_*.py" | wc -l
find tests/test_townlet/unit/items -name "test_*.py" | wc -l
find tests/test_townlet/integration -name "test_*.py" | wc -l
find tests/test_townlet/performance -name "test_*.py" | wc -l

# Run all tests to verify pass rate
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v --tb=short 2>&1 | tail -100
```

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-06-testing.md`

---

## Agent 8: Documentation (DOC-1 to DOC-10, DOC-EXT-1 to DOC-EXT-7)

**Scope:** 17 requirements (10 original + 7 extensions)

**Priority Extensions:**
- **DOC-EXT-1 (P2)**: Command reference (comprehensive DSL guide)
- **DOC-EXT-5 (P2)**: Type system reference (all types documented)
- **DOC-EXT-2 (P3)**: Observation modes (full_auto, max_compact, full_manual)

**Files to examine:**

- `docs/config-schemas/expressions.md`
- `docs/config-schemas/vfs-profiles.md`
- `docs/config-schemas/effects.md`
- `docs/config-schemas/items.md`
- `docs/guides/world-compiler-guide.md`
- Reference config packs in `configs/`
- Migration guides

**Critical requirements:**

- DOC-1: Expression language reference (comprehensive syntax guide)
- DOC-2: VFS profiles schema docs (all fields documented)
- DOC-3: Effects catalog schema docs (command types, reapply policies)
- DOC-4: Items schema docs (vfs_profile field, spawn rules)
- DOC-5: World Compiler user guide (how to use compiler CLI)
- DOC-6: Reference config updates (L0-L3 all use new schemas)
- DOC-7: Migration guide (old → new patterns)

**Verification commands:**

```bash
# Check docs exist and are substantial (not stubs)
for doc in expressions.md vfs-profiles.md effects.md items.md; do
  if [ -f "docs/config-schemas/$doc" ]; then
    lines=$(wc -l < "docs/config-schemas/$doc")
    echo "$doc: $lines lines"
    if [ $lines -lt 100 ]; then
      echo "  WARNING: Likely a stub (< 100 lines)"
    fi
  else
    echo "$doc: MISSING"
  fi
done

# Check migration guide
ls -lh docs/guides/*migration* 2>/dev/null || echo "Migration guide: MISSING"
```

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-07-documentation.md`

---

## Agent 9: Breaking Changes & Success Criteria (BREAK-1 to BREAK-9, Derived requirements)

**Scope:** 42 requirements (9 breaking changes + 33 derived)

**Note:** No new extensions for this category, but total includes all derived success criteria from original analysis

**Primary files to examine:**

- All config DTOs (verify no fallbacks for old formats)
- Error messages for breaking changes
- Migration documentation

**Critical requirements:**

- BREAK-1: No variables_reference.yaml at level scope (experiment-only)
- BREAK-2: No effects.yaml at level scope (experiment-only)
- BREAK-3: Items use vfs_profile field (not inline variables)
- BREAK-4: Clear error messages for old configs
- BREAK-5: No fallback mechanisms (fail loudly)
- BREAK-6: No backwards compatibility code
- BREAK-7: Deleted deprecated code paths
- BREAK-8: Updated all reference configs
- BREAK-9: Migration guide exists

**Verification commands:**

```bash
# Verify no level-scoped VFS/effects files
for level in configs/L*/; do
  if [ -f "$level/variables_reference.yaml" ]; then
    echo "VIOLATION: $level has variables_reference.yaml (should be experiment-level only)"
  fi
  if [ -f "$level/effects.yaml" ]; then
    echo "VIOLATION: $level has effects.yaml (should be experiment-level only)"
  fi
done

# Check for backwards compatibility code (antipatterns)
grep -r "for backward.*compatibility" src/townlet/ || echo "✓ No backwards compat comments"
grep -r "hasattr.*old.*field" src/townlet/ || echo "✓ No old field checks"
grep -r "legacy.*support" src/townlet/ || echo "✓ No legacy support code"
```

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-08-breaking-changes.md`

---

## Agent 10: Synthesis & Final Report

**Scope:** Aggregate all 9 agent reports

**Input:** 9 gap reports (246 requirements total)

**Areas to verify:**

1. **Error Handling** (compile-time validation, clear error messages)
2. **Type Safety** (expression type checking, command type validation)
3. **Performance** (<5% overhead, benchmarks exist and pass)
4. **Pedagogical** (clean abstractions, no opaque dicts)
5. **Integration** (cross-system dependencies verified)

**Primary files:**

- Performance benchmarks: `tests/test_townlet/performance/test_component_benchmarks.py`
- Integration tests: `tests/test_townlet/integration/`
- Error handling: Check error messages in all DTOs and compiler stages

**Critical verifications:**

- Performance benchmarks exist and show <5% overhead
- All cross-system integrations have tests
- Type checker prevents invalid configs at compile time
- Error messages include file context and suggestions
- No opaque dictionaries in item VFS storage

**Verification commands:**

```bash
# Run performance benchmarks
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/performance/ -v

# Check for opaque dict usage
grep -r "Dict\[str, Any\]" src/townlet/items/ | grep -v "# type: ignore" || echo "✓ No opaque dicts"

# Verify type safety in DTOs
grep -r "Optional\[" src/townlet/config/*_config.py | wc -l  # Should be minimal
```

**Output:** `docs/plans/vfs_uplift/validation/reports/gap-report-09-success-criteria.md`

---

## Phase 2: Report Collection

**After all 9 agents complete:**

1. Verify all reports exist:

```bash
ls -lh docs/plans/vfs_uplift/validation/reports/gap-report-*.md
```

Expected files:
- `gap-report-01-compiler.md`
- `gap-report-02-vfs.md`
- `gap-report-03-effects.md`
- `gap-report-04-items.md`
- `gap-report-05-runtime.md`
- `gap-report-06-testing.md`
- `gap-report-07-documentation.md`
- `gap-report-08-breaking-changes.md`
- `gap-report-09-success-criteria.md`

2. Quick scan for critical gaps:

```bash
grep -h "❌ MISSING" docs/plans/vfs_uplift/validation/reports/*.md | wc -l
grep -h "## Critical Gaps" -A 10 docs/plans/vfs_uplift/validation/reports/*.md
```

---

## Phase 3: Synthesis

#**Process:**

1. Read all 9 gap reports
2. Aggregate status for all 246 requirements
3. Identify integration gaps (where Agent A calls Agent B's API)
4. Prioritize gaps:
   - **P0 (Critical):** Breaks core functionality, must fix before merge
   - **P1 (Important):** Missing feature, should fix soon
   - **P2 (Minor):** Polish/nice-to-have, can defer
5. Calculate statistics (% complete/partial/missing)
6. Create action plan with effort estimates
7. Provide merge recommendation

**Template:**

```markdown
# VFS Uplift Gap Analysis - Final Report

**Date:** 2025-11-23 (Expanded)
**Baseline Commit:** ac67272
**Analysts:** 9 parallel agents + synthesis
**Total Requirements:** 246 (157 original + 89 new)

---

## Executive Summary

**Overall Status:**
- ✅ COMPLETE: X requirements (Y%)
- ⚠️ PARTIAL: X requirements (Y%)
- ❌ MISSING: X requirements (Y%)
- 🔍 UNCLEAR: X requirements (Y%)

**Recommendation:** [READY FOR MERGE / NEEDS WORK / BLOCKED]

**Critical Gaps (P0):** X (must fix before merge)
**Important Gaps (P1):** X (should fix soon)
**Minor Gaps (P2):** X (backlog)

---

## Critical Gaps (P0 - Must Fix Before Merge)

| Req ID | Category | Requirement | Impact | Estimated Effort | Owner |
|--------|----------|-------------|--------|------------------|-------|
| ... | ... | ... | ... | ... | ... |

**Total P0 Effort:** X days

---

## Important Gaps (P1 - Should Fix)

[Table of P1 gaps]

---

## Minor Gaps (P2 - Can Defer)

[Table of P2 gaps]

---

## Detailed Requirements Status by Category

### Category 1: Compiler (20/20)
[Status table]

### Category 2: VFS System (15/15)
[Status table]

[... continue for all 8 categories ...]

---

## Integration Analysis

**Cross-System Dependencies Verified:**
- ✅ Compiler → VFS: Integration works
- ✅ Compiler → Effects: Compilation works
- ❌ Runtime → VFS: Evaluator not called
- ⚠️ Items → VFS: API works but no E2E test

**Integration Gaps:**
[List any missing integration points]

---

## Action Plan

### Immediate (Before Merge - P0 Gaps)

1. **[REQ-ID]: [Requirement]**
   - File: [file path]
   - What: [description]
   - Effort: [time estimate]
   - Blocker: [yes/no]

[... list all P0 action items ...]

### Short-Term (P1 Gaps - Next Sprint)

[List P1 action items]

### Backlog (P2 Gaps)

[List P2 items]

---

## Risk Assessment

**High Risk (Merge Blockers):**
- X critical gaps (P0)
- Estimated X days to resolve
- [Specific technical risks]

**Medium Risk:**
- X important gaps (P1)
- Can be addressed post-merge

**Low Risk:**
- X minor gaps (P2)
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
- Must track P1 gaps as issues
- Timeline: [when to address]

**If READY:**
- All critical functionality present
- P1/P2 gaps documented for backlog
- Zero regressions verified

---

## Appendix: Agent Reports

- [gap-report-01-compiler.md](./gap-report-01-compiler.md)
- [gap-report-02-vfs.md](./gap-report-02-vfs.md)
- [gap-report-03-effects.md](./gap-report-03-effects.md)
- [gap-report-04-items.md](./gap-report-04-items.md)
- [gap-report-05-runtime.md](./gap-report-05-runtime.md)
- [gap-report-06-testing.md](./gap-report-06-testing.md)
- [gap-report-07-documentation.md](./gap-report-07-documentation.md)
- [gap-report-08-breaking-changes.md](./gap-report-08-breaking-changes.md)
- [gap-report-09-success-criteria.md](./gap-report-09-success-criteria.md)
```

---

## Success Criteria

**Phase 1 Success:**
- [ ] All 9 analysis agents complete without errors
- [ ] All 9 gap reports generated
- [ ] Every requirement (157 total) has status assigned
- [ ] All claims have file:line evidence

**Phase 2 Success:**
- [ ] All 9 reports collected and readable
- [ ] Critical gaps identified (grep verification)

**Phase 3 Success:**
- [ ] Final report synthesized by Agent 10
- [ ] All 157 requirements accounted for
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
1. Verify all 9 reports exist and are readable
2. Check for conflicting status
3. Manually resolve conflicts
4. Re-run synthesis agent

---

## Timeline Estimate

**Optimistic (6 hours):**
- Phase 1: 4 hours (all 9 agents fast)
- Phase 2: 30 minutes (quick scan)
- Phase 3: 1.5 hours (synthesis)

**Realistic (8-10 hours):**
- Phase 1: 6-8 hours (some agents slow)
- Phase 2: 30 minutes
- Phase 3: 2-3 hours (synthesis with conflict resolution)

**Pessimistic (12+ hours):**
- Phase 1: 8-10 hours (agents encounter issues)
- Phase 2: 1 hour (report issues)
- Phase 3: 4-6 hours (complex conflicts)

---

## Notes

**Line Number References:**
All line numbers in this plan are approximate and based on baseline commit ac67272. Code may have shifted slightly. Use grep/glob to find exact locations.

**Evidence Standards:**
Every claim MUST have file:line evidence. "I think it exists" or "probably implemented" is not acceptable. Use grep, read files, run tests to verify.

**No Overlap:**
Each agent has a distinct scope. If you find a requirement outside your scope, note it as "not examined - [AGENT]'s scope" and continue.

**Cross-System Integration:**
Note where you call APIs from other agents' modules. The synthesis agent will verify these integration points.

---

## Ready to Execute

This plan is ready for immediate execution. To start:

1. Verify prerequisites (baseline commit, tests pass, clean directory)
2. Dispatch all 9 agents in parallel (single message, 9 Task tool calls)
3. Wait for completion (6-10 hours estimated)
4. Run synthesis agent (Agent 10)
5. Review final report and create action plan

**Next Step:** Copy the "Execution Command" from Phase 1 and paste it to Claude to begin.
