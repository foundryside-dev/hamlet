# Gap Analysis Agent Assignment Template

**Purpose:** Organize parallel agent work with clear boundaries

---

## Agent 1: Compiler System (COMP-*)

**Scope:** UniverseCompiler and compilation pipeline
- Requirements: COMP-1 through COMP-20 (20 total)
- Files: `src/townlet/universe/compiler.py`, `src/townlet/universe/compiled.py`
- Dependencies: May reference VFS/Effects compilation but only report on compiler integration

**Adjacent Systems (reference but don't report):**
- VFS compilation (VFS agent's scope)
- Effects catalog building (Effects agent's scope)
- Items catalog loading (Items agent's scope)

**Deliverable:** `gap-report-compiler.md` with COMP-* requirements verified

---

## Agent 2: VFS System (VFS-*)

**Scope:** Variable & Feature System (profiles, registry, expressions)
- Requirements: VFS-1 through VFS-15 (15 total)
- Files: `src/townlet/vfs/*.py`, `src/townlet/config/vfs_profiles_config.py`
- Dependencies: May reference expression language, observation builder

**Adjacent Systems (reference but don't report):**
- Expression parser (shared with Effects)
- Compiler integration (Compiler agent's scope)
- Item VFS allocation (report integration only)

**Deliverable:** `gap-report-vfs.md` with VFS-* requirements verified

---

## Agent 3: Effects System (EFF-*)

**Scope:** Effects catalog, commands, execution, lifecycle
- Requirements: EFF-1 through EFF-20 (20 total)
- Files: `src/townlet/effects/*.py`, `src/townlet/config/effects_config.py`
- Dependencies: May reference command execution, VFS mutations

**Adjacent Systems (reference but don't report):**
- VFS registry writes (verify API usage only)
- Item spawning (verify command exists only)
- Compiler catalog building (Compiler agent's scope)

**Deliverable:** `gap-report-effects.md` with EFF-* requirements verified

---

## Agent 4: Items System (ITEM-*)

**Scope:** Items catalog, inventory, spawning, interactions
- Requirements: ITEM-1 through ITEM-16 (16 total)
- Files: `src/townlet/items/*.py`, `src/townlet/config/items_config.py`
- Dependencies: May reference VFS profiles, effects integration

**Adjacent Systems (reference but don't report):**
- VFS profile application (verify API usage only)
- Effects spawning (verify command calls only)
- Compiler catalog building (Compiler agent's scope)

**Deliverable:** `gap-report-items.md` with ITEM-* requirements verified

---

## Agent 5: Runtime Integration (RUN-*)

**Scope:** Environment integration, observation building, evaluation
- Requirements: RUN-1 through RUN-12 (12 total)
- Files: `src/townlet/environment/vectorized_env.py`, `src/townlet/vfs/observation_builder.py`
- Dependencies: Integrates ALL other systems

**Adjacent Systems (reference but don't report):**
- All compile-time artifacts (verify API contracts only)
- VFS evaluator (VFS agent's scope)
- Effects manager (Effects agent's scope)
- Items manager (Items agent's scope)

**Deliverable:** `gap-report-runtime.md` with RUN-* requirements verified

---

## Agent 6: Testing & Documentation (TEST-*, DOC-*)

**Scope:** Test coverage, documentation completeness
- Requirements: TEST-1 through TEST-22, DOC-1 through DOC-10 (32 total)
- Files: `tests/`, `docs/config-schemas/`, `docs/guides/`
- Dependencies: Verifies ALL systems have tests and docs

**Adjacent Systems (reference but don't report):**
- Feature implementation (other agents' scope)
- Only verify: tests exist, docs exist, coverage ≥ target

**Deliverable:** `gap-report-testing-docs.md` with TEST-*/DOC-* requirements verified

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
