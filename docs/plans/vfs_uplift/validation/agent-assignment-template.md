# Gap Analysis Agent Assignment Template

**Purpose:** Organize parallel agent work with clear boundaries

---

## Agent 1: Compiler & Schema (COMP-*)

**Scope:** UniverseCompiler, compiled DTOs, schema/versioning
- Requirements: COMP-1 through COMP-20
- Files: `src/townlet/universe/compiler.py`, `src/townlet/universe/compiled.py`, `src/townlet/vfs/schema.py`
- Dependencies: References VFS/effects compilation but reports only on compiler/schema integration

**Deliverable:** `gap-report-compiler.md`

---

## Agent 2: VFS System (VFS-*)

**Scope:** Variable & Feature System (profiles, registry, expressions)
- Requirements: VFS-1 through VFS-15
- Files: `src/townlet/vfs/*.py`, `src/townlet/config/vfs_profiles_config.py`
- Dependencies: Expression language, observation builder

**Deliverable:** `gap-report-vfs.md`

---

## Agent 3: Effects & Runtime Expressions (EFF-*)

**Scope:** Effects catalog, commands, execution, expression/type checking
- Requirements: EFF-1 through EFF-20
- Files: `src/townlet/effects/*.py`, `src/townlet/world/expression/*.py`, `src/townlet/config/effects_config.py`

**Deliverable:** `gap-report-effects.md`

---

## Agent 4: Item VFS & Inventory (ITEM-*)

**Scope:** Items catalog, inventory, spawning, VFS profile binding
- Requirements: ITEM-1 through ITEM-16
- Files: `src/townlet/items/*.py`, `src/townlet/config/items_config.py`, `src/townlet/vfs/registry.py`

**Deliverable:** `gap-report-items.md`

---

## Agent 5: Runtime Integration (RUN-*)

**Scope:** Environment integration, observation building, evaluation
- Requirements: RUN-1 through RUN-12
- Files: `src/townlet/environment/vectorized_env.py`, `src/townlet/vfs/observation_builder.py`

**Deliverable:** `gap-report-runtime.md`

---

## Agent 6: Observations & Training (OBS-*, RUN overlap)

**Scope:** Observation shapes/dims, delivery to training loops
- Requirements: OBS-related RUN/TEST items
- Files: `src/townlet/vfs/observation_builder.py`, `src/townlet/environment/vectorized_env.py`

**Deliverable:** `gap-report-observations.md`

---

## Agent 7: Testing (TEST-*)

**Scope:** Test coverage and execution
- Requirements: TEST-1 through TEST-22
- Files: `tests/`

**Deliverable:** `gap-report-testing.md`

---

## Agent 8: Documentation (DOC-*)

**Scope:** Documentation completeness and quality
- Requirements: DOC-1 through DOC-10
- Files: `docs/config-schemas/`, `docs/guides/`

**Deliverable:** `gap-report-docs.md`

---

## Agent 9: Performance & Benchmarks (PERF-*)

**Scope:** Performance/benchmark scenarios (if defined)
- Requirements: PERF-* (as applicable)
- Files: `tests/test_townlet/performance/`, profiling/benchmark docs

**Deliverable:** `gap-report-performance.md`

---

## Agent 10: Synthesis (Final)

**Scope:** Merge all gap reports, resolve cross-cutting issues, produce final summary.

**Deliverable:** `gap-report-final.md`

---

## Coordination Protocol

**Before starting:**
1. Read your assigned requirements from `requirements-checklist.md`
2. Understand your scope boundaries
3. Note adjacent systems you'll reference

**During analysis:**
1. Verify YOUR requirements only
2. Reference adjacent systems to understand integration
3. Mark adjacent requirements as "not examined" with note

**After completion:**
1. Submit your gap report with evidence
2. Note any blocking dependencies on other agents
3. Flag cross-cutting concerns for synthesis agent

**Example coordination:**
```markdown
## ITEM-8: Item VFS Observations

Evidence:
- ItemManager provides inventory slots: src/townlet/items/manager.py:234
- ⚠️ BLOCKED: Observation builder integration (RUN-2) not examined
- Can't verify end-to-end without Runtime agent's findings

Status: ✅ COMPLETE (for Items scope)
Blocker: Awaiting RUN-2 verification from Runtime agent
```

---

## Synthesis Agent (Final)

**After all 6 agents complete:**
- Merge all gap reports
- Resolve cross-cutting concerns
- Identify integration gaps
- Produce final `gap-report-final.md`

**Timeline:** 6 agents run in parallel (1-2 days), synthesis takes 2-4 hours
