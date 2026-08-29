# Items & VFS Profiles - Implementation Plans

**Status:** Ready for Execution (pending Phase 0 team review)

**Goal:** Add Items and VFS Profiles to HAMLET with full configurability, no runtime magic, and Phase 1 limits for safe rollout.

**Total Estimated Time:** 23-29 days (4-6 weeks) for full implementation, 18-22 days (3.5-4.5 weeks) for MVP (Phase 1-3 only)

---

## Plan Structure

This implementation is broken into 5 phases:

### Phase 0: Design Resolution (2-3 days) - **BLOCKER**

**File:** `2025-11-19-phase-0-design-resolution.md`

**Status:** READY FOR TEAM REVIEW

**Blocking:** Phase 1 cannot start until all 5 design decisions are approved by team.

**Deliverables:**
- 5 design decision documents resolving critical blockers
- File layout decision (separate vfs_profiles.yaml)
- Expression language scope (Phase 1 = static only)
- Observation budget (3 slots × 5 profiles)
- Interaction granularity (fixed vocab + slot actions)
- Performance limits (conservative Phase 1 bounds)

**Success Criteria:**
- All decision documents written and reviewed
- Team approval on all 5 decisions
- Phase 1 readiness checklist complete

---

### Phase 1: DTOs + Compiler (4-5 days)

**File:** `2025-11-19-phase-1-dtos-compiler.md`

**Prerequisites:** Phase 0 decisions approved

**Deliverables:**
- VFS Profiles DTOs (global/agent/item scopes, static variables)
- Items DTOs (catalog + appearance configs)
- CompiledUniverse catalog fields
- UniverseCompiler load stages with cross-validation
- Reference config examples
- Schema documentation

**Success Criteria:**
- 30+ unit tests passing (DTOs, compiler, validation)
- Integration test: Load configs → compile → verify catalogs
- No runtime changes (metadata-only phase)

---

### Phase 2: VFS Engine + DynObs (6-7 days)

**File:** `2025-11-19-phase-2-vfs-engine-dynobs.md`

**Prerequisites:** Phase 1 complete and passing all tests

**Deliverables:**
- Scoped VFS registry (global/agent/item storage)
- VFS Observation spec builder with fixed item slot layout
- Observation assembly with inventory masking
- Dimension regression tests (obs_dim stability)

**Success Criteria:**
- 40-50 unit tests passing (registry, obs builder, assembly)
- obs_dim matches compiled metadata for all curriculum levels
- Checkpoint compatibility verified

---

### Phase 3: Items Runtime + Inventory (8-10 days)

**File:** `2025-11-19-phase-3-items-runtime.md`

**Prerequisites:** Phase 2 complete with VFS observations working

**Deliverables:**
- ItemManager with spawn/despawn lifecycle
- Agent inventory state integration
- Action handlers (GET, USE_SLOT_N, DROP_SLOT_N)
- Item effects (bar deltas, VFS updates)
- Checkpoint serialization for items

**Success Criteria:**
- 50+ unit tests passing (item manager, actions, effects)
- Integration test: Full training loop with items
- Smoke test with `configs/test/items_smoke` pack

---

### Phase 4: Advanced Scheduling (3-4 days) - **OPTIONAL**

**File:** `2025-11-19-phase-4-advanced-scheduling.md`

**Prerequisites:** Phase 3 complete and deployed to production

**Status:** OPTIONAL - NOT MVP-CRITICAL

**Deliverables:**
- Scheduled spawning (time_window, Poisson, normal)
- Spawn conditions (VFS/bar predicates)
- Spawn priority ordering

**Success Criteria:**
- 15+ unit tests passing (schedules, conditions, priority)
- Integration test with complex spawn rules

**Recommendation:** Defer to post-MVP if schedule pressure. Phase 1-3 deliver functional items without advanced scheduling.

---

## Execution Strategies

### Strategy 1: Subagent-Driven Development (Recommended)

**Use when:** Working in current session, want fast iteration with code review between tasks

**How:**
1. Use `superpowers:subagent-driven-development` skill
2. Dispatch fresh subagent per task from plan
3. Review code between tasks
4. Fast iteration with quality gates

**Command:**
```
I want to use subagent-driven development to execute Phase 1
```

### Strategy 2: Parallel Session Execution

**Use when:** Want to batch-execute full phase in separate session

**How:**
1. Open new Claude Code session in dedicated worktree
2. Use `superpowers:executing-plans` skill
3. Point to plan file (e.g., `2025-11-19-phase-1-dtos-compiler.md`)
4. Execute with checkpoints

**Command:**
```
Use executing-plans skill to execute docs/plans/vfs_uplift/2025-11-19-phase-1-dtos-compiler.md
```

---

## Phase Dependencies

```
Phase 0 (Design Resolution)
    │
    ├─ REQUIRED: Team review and approval
    │
    └─▶ Phase 1 (DTOs + Compiler)
           │
           ├─ All tests passing
           │
           └─▶ Phase 2 (VFS Engine + DynObs)
                  │
                  ├─ obs_dim regression tests passing
                  │
                  └─▶ Phase 3 (Items Runtime + Inventory)
                         │
                         ├─ OPTIONAL ─▶ Phase 4 (Advanced Scheduling)
                         │
                         └─ MVP COMPLETE (Phases 1-3)
```

---

## Progress Tracking

| Phase | Status | Tests | Completion |
|-------|--------|-------|------------|
| Phase 0 | 🟡 Pending Review | N/A | 100% (docs written) |
| Phase 1 | ⚪ Not Started | 0/30 | 0% |
| Phase 2 | ⚪ Not Started | 0/50 | 0% |
| Phase 3 | ⚪ Not Started | 0/50 | 0% |
| Phase 4 | ⚪ Not Started | 0/15 | 0% (optional) |

Legend:
- ⚪ Not Started
- 🟡 In Progress
- 🟢 Complete
- 🔴 Blocked

---

## Quick Start

### For Team Reviewer (Phase 0)

```bash
# Read all design decisions
cat docs/plans/vfs_uplift/decisions/001-file-layout.md
cat docs/plans/vfs_uplift/decisions/002-expression-language-phase1.md
cat docs/plans/vfs_uplift/decisions/003-observation-budget.md
cat docs/plans/vfs_uplift/decisions/004-interaction-granularity.md
cat docs/plans/vfs_uplift/decisions/005-performance-limits.md

# Review summary
cat docs/plans/vfs_uplift/decisions/README.md

# Approve or request changes
```

### For Engineer (Phase 1+)

```bash
# Create feature branch
git checkout -b feature/items-vfs-phase1

# Read plan
cat docs/plans/vfs_uplift/2025-11-19-phase-1-dtos-compiler.md

# Option A: Subagent-driven (recommended)
# → Ask Claude: "Use subagent-driven development to execute Phase 1"

# Option B: Parallel session
# → Open new session
# → Ask Claude: "Use executing-plans to execute docs/plans/vfs_uplift/2025-11-19-phase-1-dtos-compiler.md"
```

---

## Key Decisions Reference

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **File Layout** | Separate `vfs_profiles.yaml` | Cleaner separation, easier review |
| **Expression Language** | Phase 1 = static only | Avoid scope creep, defer DSL to Phase 2+ |
| **Observation Budget** | 3 slots × 5 profiles (15 dims) | Bounded obs growth, checkpoint compat |
| **Interaction Granularity** | Fixed vocab + slot actions | No architecture redesign, aligns with current action_config |
| **Performance Limits** | Conservative (10 types, 3/agent) | Prove architecture, increase in Phase 3+ |

---

## Risk Mitigation

| Risk | Mitigation | Status |
|------|------------|--------|
| Expression DSL scope creep | Phase 1 rejects expressions, defer to Phase 2+ | ✅ Resolved |
| obs_dim mismatches | Dimension regression tests in Phase 2 | ✅ Planned |
| Action space explosion | Fixed vocab with masking (7 actions) | ✅ Resolved |
| Inventory overflow bugs | Hard limit + assertions, deny policy | ✅ Planned |
| Phase 4 schedule pressure | Mark Phase 4 optional, MVP = Phase 1-3 | ✅ Documented |

---

## Success Metrics

### Phase 1 (DTOs + Compiler)
- ✅ 30+ tests passing
- ✅ Compiler loads vfs_profiles.yaml and items.yaml
- ✅ Cross-validation catches broken refs
- ✅ No runtime changes

### Phase 2 (VFS Engine + DynObs)
- ✅ 50+ tests passing
- ✅ obs_dim stable across all levels
- ✅ VFS fields appear in observations
- ✅ Empty item slots masked correctly

### Phase 3 (Items Runtime + Inventory)
- ✅ 50+ tests passing
- ✅ Items spawn/despawn with lifecycle
- ✅ Agents pickup/use/drop items
- ✅ Effects modify bars and VFS
- ✅ Checkpoint roundtrip preserves item state

### Phase 4 (Advanced Scheduling - Optional)
- ✅ 15+ tests passing
- ✅ time_window spawning works
- ✅ VFS spawn conditions evaluated
- ✅ Priority ordering enforced

---

## Related Documentation

- **Original Plan:** `docs/plans/2025-11-18-items-and-vfs-profiles.md`
- **Deep Dive Analysis:** (Provided by deep-dive analysis above)
- **Schema Docs:** `docs/config-schemas/vfs-profiles.md`, `docs/config-schemas/items.md`
- **VFS Integration Guide:** `docs/vfs-integration-guide.md`
- **Reference Config:** `configs/reference_config/VARIABLE_SUBSYSTEM.md`

---

## Questions?

- **Stuck on Phase 0?** Review decision documents, propose alternatives
- **Stuck on implementation?** Use `superpowers:systematic-debugging` skill
- **Tests failing?** Use `superpowers:test-driven-development` skill
- **Need code review?** Use `superpowers:requesting-code-review` skill

---

**Next Action:** Present Phase 0 decision documents to team for approval. Phase 1 cannot start until all 5 decisions are accepted.
