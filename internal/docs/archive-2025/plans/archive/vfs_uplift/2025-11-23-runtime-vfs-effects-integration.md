# Runtime VFS + Effects Integration Plan

> **For Claude:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task with code review between tasks.

**Status:** Ready for execution (validated against current codebase)
**Date:** 2025-11-23
**Owner:** World Compiler (T0 Pillar 3)
**Timeline:** 10-15 days (2-3 weeks)
**Test Target:** 20-30 new tests
**Tech Stack:** PyTorch, Pydantic, networkx (topo sort), pyparsing (expressions)

## Goal

Finish the unified World Compiler deliverables that are still missing at runtime: execute VFS profile expressions in production, surface item VFS state, and ship compiled Effects as a compiler artifact (not rebuilt in the environment). This document consolidates the relevant pieces from:

- `2025-11-19-unified-world-compiler-plan.md` (D2 mark-and-sweep, VFS profiles, compiled effects)
- `2025-11-19-task-2-3-expression-integration.md` (VFS expression evaluation + topo ordering)
- `2025-11-20-task-4.5-item-vfs-integration.md` (item VFS state + observations)
- `2025-11-19-effects-system-design.md` (effect catalog as compiled artifact)
- `2025-11-21-phase-7-completion-plan.md` (effects command gaps – already closed in code)

## Prerequisites

Before starting this plan:

- ✅ Review and address spawn depth increment (executor.py:208) if needed based on code review
- ✅ Ensure Phase 7.1 changes (effects commands) are committed
- ✅ Verify all 435+ existing tests pass (baseline)

## Current State (verified against repo)

- VFS profiles: DTOs + compiler exist (`src/townlet/config/vfs_profiles_config.py`, `src/townlet/vfs/profiles.py`) and are unit-tested, but runtime ignores them. The env loads `variables_reference.yaml` and forbids `expression` there (`src/townlet/vfs/schema.py`, `vectorized_env.py`).
- VFS evaluation: No mark-and-sweep or eager expression execution in the live env; item VFS obs are zero stubs (`src/townlet/vfs/observation_builder.py`).
- Items: `vfs_profile` on items is unused; item VFS storage is allocated from `variables_reference.yaml` (not profiles). Effects can do `self.vfs.*` for items, but profile-driven layout and obs exposure are absent.
- Effects: Catalog is rebuilt at runtime from `effects.yaml` in `vectorized_env.py`; `CompiledUniverse` does not carry a compiled catalog.

## Implementation Plan

### Task 1: Compile-time wiring (VFS profiles + Effects) - 2-3 days

**Goal:** Move VFS profiles and Effects catalog compilation into UniverseCompiler

**Deliverables:**

- **Load profiles:** Extend `UniverseCompiler` to read `vfs_profiles.yaml` (experiment-level) and compile via `VFSProfileCompiler`. Store compiled profiles and evaluated variable metadata in `CompiledUniverse` (per-level as needed).
- **Compiled effects artifact:** Move EffectCatalog build into the compiler; include in `CompiledUniverse` (experiment-scope artifact). Remove runtime rebuild from `vectorized_env.py` once present.
- **Schema surface:** Expand `CompiledUniverse` to expose:
  - `compiled_vfs_profiles` (global, agent, item) with dependency ordering
  - `vfs_expression_schema` (type info for expression checking in runtime writes)
  - `compiled_effect_catalog`
- **Config gating:** If `vfs_profiles.yaml` present, load and validate. If items reference `vfs_profile` but no profiles exist, fail fast. Otherwise, continue with empty profiles (minimal configs without VFS features are allowed).

**Tests:** 5-8 compiler tests (profile loading, catalog compilation, schema validation)

---

### Task 2: Runtime VFS evaluation (mark-and-sweep) - 3-4 days

**Goal:** Execute VFS expressions at runtime using compiled profiles
**Deliverables:**

- **Evaluator:** Add a VFS evaluator module that takes compiled profiles + registry and evaluates expressions in topo order, respecting dependencies. Support two modes (from D2): `mark_and_sweep` (only variables marked for obs) and `eager` (all vars). Default to `mark_and_sweep`; keep `eager` as debug flag.
- **Marking:** At compile time, mark which VFS variables are consumed by observation fields; emit this in `CompiledUniverse` (e.g., `vfs_observation_marks`). Runtime uses marks to decide which vars to evaluate.
- **Registry integration:** Replace the ad hoc `variables_reference.yaml` load in `vectorized_env.py` with `CompiledUniverse` VFS metadata + compiled profiles. Reject `variables_reference.yaml` expressions entirely (already enforced) and remove the fallback load for item-scoped vars.
- **Execution context:** Ensure expression evaluation context used by VFS evaluator has bars + VFS dictionaries, with self/target support consistent with `townlet.world.expression.context.ExecutionContext`.
- **Observation builder:** Update `src/townlet/vfs/observation_builder.py` to consume compiled item profiles: fixed slots = `max_items_per_agent × max_item_profiles × vars_per_profile`, with masking for empty slots. Remove zero-stub behavior.

**Tests:** 8-10 tests (evaluator topo order, mark-and-sweep vs eager, observation builder dimensions)

---

### Task 3: Item VFS integration - 2-3 days

**Goal:** Make item VFS profile-driven end-to-end
**Deliverables:**

- **Profile-driven storage:** When initializing `VariableRegistry`, shape item storage using compiled item profiles (not `variables_reference.yaml`). Map `{profile_name → variable → tensor index}` so items can share layouts by profile.
- **Spawn/init:** ItemManager should assign `vfs_profile` to instances and use the profile map to initialize item VFS defaults; accept `initial_state` keyed by variable name within the selected profile.
- **ExecutionContext:** Keep `self_is_item` path resolution (already present) and ensure `vfs_registry.read/write` understands profile-scoped item variables using the new map.
- **Observations:** Include item VFS slices per carried item slot; mask unused slots. Align dimensions with `VFSObservationSpec` derived from compiled profiles.

**Tests:** 5-7 tests (profile application, initial_state, observations with masking)

---

### Task 4: Effects runtime usage - 1-2 days

**Goal:** Use compiled effect catalog from UniverseCompiler
**Deliverables:**

- **Use compiled catalog:** Replace runtime construction in `vectorized_env.py` with the compiled catalog from `CompiledUniverse`. Keep schema/type checking consistent with the compiler schema generation.
- **Schema sync:** When building the effects command schema, include bars + VFS paths from compiled profiles (self/target), including item-scoped paths (`self.vfs.*`, `target.vfs.*`). Remove the secondary YAML pass over `variables_reference.yaml` for schema inference.

**Tests:** 2-3 tests (compiled catalog usage, schema consistency)

---

### Task 5: Tests and validation - 2-3 days

**Goal:** Comprehensive testing and cleanup
**Deliverables:**

- **Unit tests:** (covered in Tasks 1-4 above, total 20-30 new tests)
  - VFS evaluator topo order, circular detection (reuse existing tests) + new tests for mark-and-sweep vs eager
  - Item VFS profile application (defaults, initial_state, profile switch)
  - Observation builder outputs correct dims/masks for item VFS

- **Integration tests:**
  - `test_expression_vfs_effects` updated to run through compiled profile execution
  - Items smoke: pickup/use/drop modifies item VFS and shows in observations
  - Effects smoke: effect spawn uses compiled catalog (no runtime YAML rebuild)

- **Cleanup validation:**
  - Ensure no runtime references remain to `variables_reference.yaml` for item vars (grep verification)
  - Ensure no ad hoc effect catalog creation at runtime (grep verification)
  - Remove zero-stub behavior from observation builder

- **Regression check:**
  - All 435+ existing tests still pass

**Tests:** Integration suite (5-10 tests)

---

## Success Criteria

### Functional Requirements

- ✅ VFS expressions execute at runtime using compiled profiles
- ✅ Mark-and-sweep evaluation mode is default with eager override available
- ✅ Item VFS is profile-driven end-to-end (allocation, mutation, observations)
- ✅ Item instances honor `vfs_profile` field
- ✅ CompiledUniverse carries effect catalog and VFS profile metadata
- ✅ `vectorized_env.py` consumes compiled artifacts (not raw YAML)

### Test Requirements

- ✅ 20-30 new tests passing (unit + integration)
- ✅ All 435+ existing tests still pass (zero regressions)
- ✅ Items smoke test shows non-zero item VFS observations
- ✅ Effects smoke test uses compiled catalog

### Code Quality

- ✅ No runtime `variables_reference.yaml` reads for item-scoped variables (grep verification)
- ✅ No runtime effect catalog rebuild (grep verification)
- ✅ Performance: <5% overhead from VFS expression evaluation

---

## Breaking Changes (Pre-release)

As a pre-release project with zero users, these breaking changes are acceptable:

1. **`vfs_profiles.yaml` now required** for items with VFS state
   - Items that reference `vfs_profile` must have corresponding profiles defined
   - Minimal configs without VFS features continue to work

2. **`variables_reference.yaml`** no longer supports item-scoped variables
   - Item variables must be defined in `vfs_profiles.yaml` instead
   - Agent/global variables in `variables_reference.yaml` still supported

3. **Effect catalog** must be compiled at universe compilation time
   - No runtime YAML rebuild from `effects.yaml`
   - Effects integrated into `CompiledUniverse` artifact

4. **Item instances** must specify `vfs_profile` if using VFS state
   - Profile name must match an entry in `vfs_profiles.yaml`

**Migration Guide:**

- Update all config packs with items to include `vfs_profiles.yaml`
- Move item-scoped variables from `variables_reference.yaml` to profiles
- Verify effect catalog compiles with `python -m townlet.universe compile <config>`

---

## Timeline Summary

| Task | Duration | Tests | Dependencies |
|------|----------|-------|--------------|
| Task 1: Compile-time wiring | 2-3 days | 5-8 | Prerequisites complete |
| Task 2: Runtime VFS evaluation | 3-4 days | 8-10 | Task 1 |
| Task 3: Item VFS integration | 2-3 days | 5-7 | Task 2 |
| Task 4: Effects runtime usage | 1-2 days | 2-3 | Task 1, Task 2 |
| Task 5: Tests and validation | 2-3 days | 5-10 integration | Tasks 1-4 |
| **TOTAL** | **10-15 days** | **20-30** | |

**Critical Path:** Task 1 → Task 2 → Task 3 → Task 5

**Parallelization Opportunity:** Task 4 can run in parallel with Task 3 after Task 2 completes (reduces timeline by 1-2 days with two developers).

---

## Risk Assessment

### Medium Risk Areas

**1. VFS Expression Performance**
- **Risk:** Mark-and-sweep evaluation adds overhead to step loop
- **Mitigation:** Profile early, implement eager fallback, cache compiled ASTs
- **Target:** <5% performance regression

**2. Item VFS Observation Dimensions**
- **Risk:** Adding item VFS breaks observation dimension stability
- **Mitigation:** Fixed slot allocation, dimension regression tests
- **Checkpoint Impact:** Acceptable (pre-release, zero users)

**3. Config Migration Effort**
- **Risk:** All config packs need `vfs_profiles.yaml`
- **Mitigation:** Start with items_smoke, validate pattern, then migrate curriculum
- **Scope:** 5 curriculum levels + test configs (~10 config packs)

### Low Risk Areas

**4. Compiled Catalog Integration**
- **Risk:** Breaking effects catalog at runtime
- **Mitigation:** Existing effects tests verify functionality
- **Status:** Effects system already production-ready (Phase 3 complete)

---

## Execution Strategy

**Recommended:** Subagent-driven development with code review between tasks

**Commands:**

```bash
# Task 1
"Use subagent-driven development to execute Task 1: Compile-time wiring from docs/plans/vfs_uplift/2025-11-23-runtime-vfs-effects-integration.md"

# Task 2
"Use subagent-driven development to execute Task 2: Runtime VFS evaluation from docs/plans/vfs_uplift/2025-11-23-runtime-vfs-effects-integration.md"

# ... etc
```

**Advantages:**

- Clear task boundaries (each task is self-contained)
- Can catch integration issues early
- Easier to debug (smaller changes per task)
- Code review after each task ensures quality

---

## Related Documentation

- **Unified Plan:** `docs/plans/vfs_uplift/2025-11-19-unified-world-compiler-plan.md`
- **Implementation Status:** `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`
- **VFS Profiles Design:** `docs/plans/vfs_uplift/2025-11-19-task-2-3-expression-integration.md`
- **Item VFS Integration:** `docs/plans/vfs_uplift/2025-11-20-task-4.5-item-vfs-integration.md`
- **Effects System:** `docs/plans/vfs_uplift/2025-11-19-effects-system-design.md`
