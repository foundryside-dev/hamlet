# VFS Uplift Gap Analysis Report

**Date:** [DATE]
**Analyzer:** [NAME]
**Baseline Commit:** [SHA]
**Branch:** [BRANCH]

---

## Executive Summary

- **Total Requirements:** 157
- **Complete (✅):** [COUNT] ([PERCENT]%)
- **Partial (⚠️):** [COUNT] ([PERCENT]%)
- **Missing (❌):** [COUNT] ([PERCENT]%)
- **Unclear (🔍):** [COUNT] ([PERCENT]%)

**Overall Status:** [READY FOR MERGE | NEEDS WORK | BLOCKED]

**Critical Gaps:** [COUNT] (must fix before merge)
**Important Gaps:** [COUNT] (should fix)
**Minor Gaps:** [COUNT] (nice to have)

---

## Critical Gaps (Must Fix Before Merge)

These gaps block production readiness or violate architectural requirements.

| Req ID | Category | Requirement | Impact | Evidence | Priority |
|--------|----------|-------------|--------|----------|----------|
| RUN-1 | Runtime | Mark-and-sweep VFS evaluation | Core feature missing | No evaluator found at src/townlet/vfs/evaluator.py | P0 |
| RUN-2 | Runtime | Item VFS observations | Returns zero stubs | observation_builder.py:XXX hardcoded zeros | P0 |
| RUN-3 | Runtime | Compiled catalog usage | Runtime YAML rebuild found | vectorized_env.py:XXX loads effects.yaml | P0 |
| COMP-2 | Compiler | VFS profiles compilation | Not in CompiledUniverse | universe/compiled.py missing vfs_profiles field | P0 |
| COMP-3 | Compiler | Effects catalog compilation | Not in CompiledUniverse | universe/compiled.py missing effect_catalog field | P0 |
| ... | ... | ... | ... | ... | ... |

**Summary:** [X] critical gaps block merge. Focus on [THEME] (e.g., "runtime integration").

---

## Important Gaps (Should Fix)

These gaps don't block merge but should be addressed soon for completeness.

| Req ID | Category | Requirement | Impact | Evidence | Priority |
|--------|----------|-------------|--------|----------|----------|
| TEST-20 | Testing | Performance validation | No benchmark data | No profiling scripts found | P1 |
| DOC-1 | Documentation | Expression language reference | Missing docs | docs/config-schemas/expressions.md not found | P1 |
| VFS-13 | VFS | Dependency graph construction | Unclear if cycles detected | Need to verify networkx usage | P1 |
| ... | ... | ... | ... | ... | ... |

**Summary:** [X] important gaps should be closed in follow-up PRs.

---

## Minor Gaps (Nice to Have)

These gaps don't significantly impact functionality but improve polish.

| Req ID | Category | Requirement | Impact | Evidence | Priority |
|--------|----------|-------------|--------|----------|----------|
| DOC-9 | Documentation | Edge case policies doc | Reference doc missing | docs/plans/vfs_uplift/edge-case-policies.md not found | P2 |
| EFF-17 | Effects | Nesting depth limit | Safety feature | No depth tracking in executor.py | P2 |
| ... | ... | ... | ... | ... | ... |

**Summary:** [X] minor gaps can be deferred to future work.

---

## Detailed Verification Evidence

### Category: Compiler (COMP-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| COMP-1 | ✅ COMPLETE | compiler.py:50-150 (7 stages), tests/test_townlet/unit/universe/test_compiler.py:20-80 | All stages present |
| COMP-2 | ❌ MISSING | No VFS profile loading in compiler.py | Needs implementation |
| COMP-3 | ❌ MISSING | No effect catalog in compiler.py | Needs implementation |
| COMP-4 | ✅ COMPLETE | config/vfs_profiles_config.py:10-50, tests/test_townlet/unit/config/test_vfs_profiles_config.py:15-45 | DTOs exist, 12 tests |
| COMP-5 | ⚠️ PARTIAL | config/items_config.py:10-80, missing tests for spawn limits | DTOs exist, tests incomplete |
| COMP-6 | ✅ COMPLETE | config/effects_config.py:10-60, tests/test_townlet/unit/config/test_effects_config.py:20-70 | DTOs + 18 tests |
| COMP-7 | ✅ COMPLETE | world/expression/parser.py:20-200, tests/test_townlet/unit/world/expression/test_parser.py:10-180 | Parser + 22 tests |
| COMP-8 | ✅ COMPLETE | world/expression/ast_nodes.py:10-100, tests/test_townlet/unit/world/expression/test_ast.py:10-80 | AST nodes + 15 tests |
| COMP-9 | ✅ COMPLETE | world/expression/type_checker.py:10-150, tests/test_townlet/unit/world/expression/test_type_checker.py:10-200 | Type checker + 28 tests |
| COMP-10 | ✅ COMPLETE | world/expression/evaluator.py:10-180, tests/test_townlet/unit/world/expression/test_evaluator.py:10-160 | Evaluator + 19 tests |
| COMP-11 | ✅ COMPLETE | effects/compiler.py:20-120, tests/test_townlet/unit/effects/test_command_compiler.py:10-200 | Command parser + 24 tests |
| COMP-12 | ⚠️ PARTIAL | universe/compiler.py:200-250, missing item reference validation | Path validation exists, reference checks incomplete |
| COMP-13 | ✅ COMPLETE | universe/compiler.py:30-45 (format_validation_error), good error messages | Error formatting present |
| COMP-14 | ❌ MISSING | universe/compiled.py missing vfs_profiles and effect_catalog fields | Needs implementation |
| COMP-15 | ✅ COMPLETE | vfs/profiles.py:50-100 (networkx topo sort), tests/test_townlet/unit/vfs/test_profiles.py:80-120 | Topo sort + cycle detection |
| COMP-16 | 🔍 UNCLEAR | observation_builder.py:XXX may have marking, need to verify | Code exists but unclear if marks emitted to CompiledUniverse |
| COMP-17 | ⚠️ PARTIAL | compiler validates vfs_profiles references, item type_id validation missing | Partial validation |
| COMP-18 | ✅ COMPLETE | All DTO fields use Field(...) with no defaults for behavioral params | Verified via grep |
| COMP-19 | ✅ COMPLETE | version: "1.0" in all DTO roots, schema validation present | Verified |
| COMP-20 | ✅ COMPLETE | Compiler enforces experiment vs level split for items/vfs_profiles | Verified in compiler.py:XXX |

### Category: VFS System (VFS-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| VFS-1 | ✅ COMPLETE | All operators in evaluator.py:XXX, 60+ tests | Complete operator library |
| VFS-2 | ✅ COMPLETE | schema.py:20-60 (GlobalVFS/AgentVFS/ItemVFS), registry.py:30-80 | Scoped storage + 18 tests |
| VFS-3 | ⚠️ PARTIAL | Expression field exists in schema, runtime evaluation missing | Compile-time only |
| VFS-4 | ✅ COMPLETE | types/reference.py:10-40, tests for path traversal | Reference types + 10 tests |
| VFS-5 | ⚠️ PARTIAL | observation_builder.py:XXX includes VFS fields, item VFS returns zeros | Agent VFS works, item VFS stubbed |
| VFS-6 | ❌ MISSING | No evaluator.py module, no mark-and-sweep implementation | Needs implementation |
| VFS-7 | ✅ COMPLETE | registry.py:40-60 (access control), tests verify enforcement | Access control + 8 tests |
| VFS-8 | ❌ MISSING | Item storage still uses variables_reference.yaml, not profiles | Needs migration |
| VFS-9 | ❌ MISSING | ItemManager doesn't use vfs_profile field | Needs implementation |
| VFS-10 | ❌ MISSING | Item VFS obs are zero stubs | Needs implementation |
| VFS-11 | ✅ COMPLETE | obs_dim regression tests in test_vectorized_env.py:XXX | Dimension stability verified |
| VFS-12 | ✅ COMPLETE | types/tensor.py:10-50, shape validation present | Tensor types + 6 tests |
| VFS-13 | ✅ COMPLETE | profiles.py:60-80 (networkx DiGraph), cycle detection | Dependency graph + tests |
| VFS-14 | ✅ COMPLETE | types/primitive.py:10-40, all types defined | Primitive types + tests |
| VFS-15 | ✅ COMPLETE | world/expression/context.py:10-80, VFS dicts present | ExecutionContext complete |

### Category: Effects System (EFF-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| EFF-1 | ❌ MISSING | Effects catalog not in CompiledUniverse | Needs compiler integration |
| EFF-2 | ✅ COMPLETE | effects/executor.py:20-200, all commands implemented | Command pipeline + 28 tests |
| EFF-3 | ✅ COMPLETE | effects/manager.py:20-150, lifecycle methods present | EffectManager + 22 tests |
| EFF-4 | ✅ COMPLETE | effects/schema.py:10-40 (ActiveEffect dataclass) | ActiveEffect + tests |
| EFF-5 | ✅ COMPLETE | manager.py:30-50 (scoped collections) | Scoped storage + 10 tests |
| EFF-6 | ✅ COMPLETE | manager.py:80-120 (reapply policy in spawn_effect) | All 4 policies + 12 tests |
| EFF-7 | ⚠️ PARTIAL | observable field exists, obs integration missing | Field present, not in obs |
| EFF-8 | ✅ COMPLETE | executor.py:40-60 (modify/set/increment/decrement) | State commands + 8 tests |
| EFF-9 | ✅ COMPLETE | executor.py:70-100 (spawn_item/spawn_effect/delete/despawn) | Lifecycle commands + 10 tests |
| EFF-10 | ✅ COMPLETE | executor.py:110-140 (if/for_each) | Control flow + 8 tests |
| EFF-11 | ⚠️ PARTIAL | emit_event exists, trigger_cascade missing | Events partial |
| EFF-12 | ✅ COMPLETE | evaluator.py:XXX (random() function), executor.py:XXX (sample) | Randomness + 6 tests |
| EFF-13 | ✅ COMPLETE | context.py:20-60 (special variables) | Path notation + 12 tests |
| EFF-14 | ✅ COMPLETE | executor.py uses expression evaluator for all values | Expression integration complete |
| EFF-15 | ✅ COMPLETE | Type checking in command compilation, compiler errors on mismatches | Type safety + 8 tests |
| EFF-16 | ✅ COMPLETE | vectorized_env.py:XXX initializes EffectManager, calls tick() in step | Environment integration + 6 tests |
| EFF-17 | 🔍 UNCLEAR | executor.py:208 has spawn_depth, but unclear if limit enforced | Depth tracking exists, need to verify limit |
| EFF-18 | ✅ COMPLETE | context.py has all required fields | Context state complete |
| EFF-19 | ✅ COMPLETE | manager.py:XXX decrements duration, despawns on expiry | Duration management + 6 tests |
| EFF-20 | ✅ COMPLETE | intensity in EffectDef, overridable at spawn, in expressions | Intensity + 8 tests |

### Category: Items System (ITEM-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| ITEM-1 | ⚠️ PARTIAL | vfs_profiles field in ItemTypeConfig, not used at runtime | Compile-time only |
| ITEM-2 | ✅ COMPLETE | max_items_per_agent enforced, GET/DROP auto-generated | Inventory + 12 tests |
| ITEM-3 | ✅ COMPLETE | items/manager.py:20-180, ItemInstance dataclass | ItemManager + 24 tests |
| ITEM-4 | ✅ COMPLETE | inventory.py:10-80, pickup/drop, DENY_PICKUP | Inventory + 16 tests |
| ITEM-5 | ✅ COMPLETE | Action handlers in vectorized_env.py:XXX | GET/USE/DROP + 18 tests |
| ITEM-6 | ✅ COMPLETE | manager.py:80-120 (placement/schedule/limits) | Spawn rules + 14 tests |
| ITEM-7 | ✅ COMPLETE | Required fields in DTOs, enforcement in ItemManager | Lifecycle + tests |
| ITEM-8 | ⚠️ PARTIAL | Condition parsing exists, VFS predicate evaluation missing | Partial implementation |
| ITEM-9 | ✅ COMPLETE | Interactions use effects commands, no opaque dicts | Clean implementation verified |
| ITEM-10 | ✅ COMPLETE | Catalog at experiment level, compiler loads correctly | Scoping correct |
| ITEM-11 | ✅ COMPLETE | Spawn rules at level level, references catalog | Scoping correct |
| ITEM-12 | ⚠️ PARTIAL | DTOs have local_commands/inventory_commands, runtime masking missing | Compile-time only |
| ITEM-13 | ✅ COMPLETE | ItemInstance.position field, spatial/aspatial support | Position tracking + 6 tests |
| ITEM-14 | ✅ COMPLETE | Fixed pool allocation in registry.py:XXX | Pre-allocated pool + tests |
| ITEM-15 | ✅ COMPLETE | Scheduler in manager.py:XXX | Spawn scheduler + 8 tests |
| ITEM-16 | ✅ COMPLETE | INTERACT auto-generated, interaction_radius from substrate | INTERACT + 6 tests |

### Category: Runtime Integration (RUN-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| RUN-1 | ❌ MISSING | No vfs/evaluator.py module | Needs implementation |
| RUN-2 | ❌ MISSING | observation_builder.py:XXX returns zeros for item VFS | Needs implementation |
| RUN-3 | ❌ MISSING | vectorized_env.py:XXX loads effects.yaml at runtime | Needs migration to compiled catalog |
| RUN-4 | ✅ COMPLETE | context.py:10-80, constructed in manager.tick() | ExecutionContext + tests |
| RUN-5 | ⚠️ PARTIAL | Registry has read/write, profile map missing | Needs profile support |
| RUN-6 | ❌ MISSING | spawn_item doesn't accept vfs_profile/initial_state | Needs implementation |
| RUN-7 | 🔍 UNCLEAR | Schema built from compiled metadata, need to verify VFS paths included | Partial evidence |
| RUN-8 | 🔍 UNCLEAR | No profiling benchmarks found | Needs benchmarking |
| RUN-9 | ⚠️ PARTIAL | Item state in checkpoints, VFS state unclear | Partial serialization |
| RUN-10 | ✅ COMPLETE | vectorized_env.py:XXX calls effect_manager.tick() | Integration complete |
| RUN-11 | ❌ MISSING | No VFS evaluation loop in env.step | Needs implementation |
| RUN-12 | ✅ COMPLETE | CI passing, 435+ tests green | Zero regressions verified |

### Category: Testing (TEST-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| TEST-1 | ⚠️ PARTIAL | Current: ~435 tests, Target: 270+ (met), but new runtime tests missing | Test count OK, coverage gaps |
| TEST-2 | ✅ COMPLETE | test_parser.py:10-180 (22 tests) | Parser tests complete |
| TEST-3 | ✅ COMPLETE | test_type_checker.py:10-200 (28 tests) | Type checker tests complete |
| TEST-4 | ✅ COMPLETE | test_evaluator.py:10-160 (19 tests) | Evaluator tests complete |
| TEST-5 | ✅ COMPLETE | test_vfs_profiles_config.py:15-45 (12 tests) | VFS DTO tests complete |
| TEST-6 | ✅ COMPLETE | test_vfs_registry.py:20-120 (18 tests) | Registry tests complete |
| TEST-7 | ✅ COMPLETE | test_vfs_profiles.py:30-150 (20 tests) | VFS evaluation tests complete |
| TEST-8 | ⚠️ PARTIAL | test_observation_builder.py:XXX (10 tests), item VFS tests missing | Partial coverage |
| TEST-9 | ✅ COMPLETE | test_effects_config.py:20-70 (18 tests) | Effects DTO tests complete |
| TEST-10 | ✅ COMPLETE | test_command_compiler.py:10-200 (24 tests) | Command compilation tests complete |
| TEST-11 | ✅ COMPLETE | test_executor.py:20-220 (28 tests) | Execution tests complete |
| TEST-12 | ✅ COMPLETE | test_effect_manager.py:30-180 (22 tests) | Manager tests complete |
| TEST-13 | ✅ COMPLETE | test_effects_integration.py:10-80 (6 tests) | Effects integration complete |
| TEST-14 | ⚠️ PARTIAL | test_items_config.py:XXX (12 tests), spawn limit tests missing | Partial coverage |
| TEST-15 | ✅ COMPLETE | test_item_manager.py:20-200 (24 tests) | Manager tests complete |
| TEST-16 | ✅ COMPLETE | test_inventory.py:15-120 (16 tests) | Inventory tests complete |
| TEST-17 | ✅ COMPLETE | test_item_actions.py:20-180 (18 tests) | Action handler tests complete |
| TEST-18 | ⚠️ PARTIAL | test_items_integration.py:10-80 (6 tests), items_smoke incomplete | Partial integration |
| TEST-19 | ⚠️ PARTIAL | Some integration tests exist, full pipeline test missing | Partial coverage |
| TEST-20 | ❌ MISSING | No profiling/benchmark scripts found | Needs implementation |
| TEST-21 | ❌ MISSING | No runtime integration tests for VFS/effects compiled catalogs | Needs implementation |
| TEST-22 | ⚠️ PARTIAL | items_smoke exists, effects_smoke exists, vfs_smoke missing | 2/3 test packs |

### Category: Documentation (DOC-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| DOC-1 | ❌ MISSING | docs/config-schemas/expressions.md not found | Needs creation |
| DOC-2 | ❌ MISSING | docs/config-schemas/vfs-profiles.md not found | Needs creation |
| DOC-3 | ❌ MISSING | docs/config-schemas/effects.md not found | Needs creation |
| DOC-4 | ❌ MISSING | docs/config-schemas/items.md not found | Needs creation |
| DOC-5 | ❌ MISSING | docs/guides/world-compiler-guide.md not found | Needs creation |
| DOC-6 | ⚠️ PARTIAL | reference-config has some sections, vfs_profiles/items incomplete | Partial updates |
| DOC-7 | ❌ MISSING | No migration guide for affordances | Needs creation |
| DOC-8 | ⚠️ PARTIAL | vfs-integration-guide.md exists, profiles section incomplete | Needs update |
| DOC-9 | ❌ MISSING | edge-case-policies.md not found | Needs creation |
| DOC-10 | ❌ MISSING | Observation management modes not documented | Needs documentation |

### Category: Breaking Changes (BREAK-*)

| Req ID | Status | Evidence | Notes |
|--------|--------|----------|-------|
| BREAK-1 | ⚠️ PARTIAL | Compiler error exists, migration guide missing | Partial implementation |
| BREAK-2 | ✅ COMPLETE | schema.py forbids item scope in variables_reference.yaml | Enforcement present |
| BREAK-3 | ❌ MISSING | Effect catalog not compiled, still runtime rebuild | Needs migration |
| BREAK-4 | ❌ MISSING | spawn_item doesn't validate vfs_profile | Needs validation |
| BREAK-5 | ✅ COMPLETE | effect_pipeline.py deleted, all affordances migrated | Verified via grep |
| BREAK-6 | ✅ COMPLETE | max_items_per_agent required in InventoryConfig | Enforcement verified |
| BREAK-7 | ✅ COMPLETE | All behavioral params required in DTOs | Verified via grep |
| BREAK-8 | ✅ COMPLETE | reapply_policy required in EffectDefinitionConfig | Enforcement verified |
| BREAK-9 | 🔍 UNCLEAR | Observation dimensions changed, impact unclear | Needs documentation |

---

## Summary by Category

| Category | Complete | Partial | Missing | Unclear | Total |
|----------|----------|---------|---------|---------|-------|
| Compiler (COMP-*) | [X] | [X] | [X] | [X] | 20 |
| VFS System (VFS-*) | [X] | [X] | [X] | [X] | 15 |
| Effects System (EFF-*) | [X] | [X] | [X] | [X] | 20 |
| Items System (ITEM-*) | [X] | [X] | [X] | [X] | 16 |
| Runtime Integration (RUN-*) | [X] | [X] | [X] | [X] | 12 |
| Testing (TEST-*) | [X] | [X] | [X] | [X] | 22 |
| Documentation (DOC-*) | [X] | [X] | [X] | [X] | 10 |
| Breaking Changes (BREAK-*) | [X] | [X] | [X] | [X] | 9 |
| **TOTALS** | **[X]** | **[X]** | **[X]** | **[X]** | **124** |

---

## Priority Breakdown

### P0 (Must Fix - Blocks Merge)
- [COUNT] requirements
- **Themes:** Runtime integration (VFS evaluation, item VFS obs), compiled catalogs
- **Estimated Effort:** [X] days

### P1 (Should Fix - Important for Completeness)
- [COUNT] requirements
- **Themes:** Testing (performance, integration), documentation (schema docs)
- **Estimated Effort:** [X] days

### P2 (Nice to Have - Can Defer)
- [COUNT] requirements
- **Themes:** Edge case docs, polish features
- **Estimated Effort:** [X] days

---

## Recommendations

### Immediate Actions (Before Merge)
1. **Implement runtime VFS evaluation** (RUN-1, VFS-6)
   - Create vfs/evaluator.py module
   - Mark-and-sweep + eager modes
   - Wire into env.step()
   - Target: 3-4 days

2. **Fix item VFS observations** (RUN-2, VFS-10)
   - Replace zero stubs with real data
   - Profile-driven obs builder
   - Target: 1-2 days

3. **Migrate to compiled catalogs** (RUN-3, COMP-2, COMP-3, EFF-1)
   - VFS profiles in CompiledUniverse
   - Effects catalog in CompiledUniverse
   - Remove runtime YAML reads
   - Target: 2-3 days

4. **Critical tests** (TEST-21)
   - Runtime integration tests
   - Compiled catalog usage tests
   - Target: 1 day

**Total Estimated Effort:** 7-10 days

### Follow-Up Work (Next Sprint)
1. **Documentation suite** (DOC-1 through DOC-5)
   - Expression language reference
   - Schema docs (vfs-profiles, effects, items)
   - World Compiler user guide
   - Target: 3-4 days

2. **Performance validation** (TEST-20, RUN-8)
   - Benchmark scripts
   - Profiling analysis
   - <5% regression verification
   - Target: 1-2 days

3. **Test coverage gaps** (TEST-18, TEST-19, TEST-22)
   - Integration test suite
   - vfs_smoke config pack
   - Target: 2-3 days

**Total Estimated Effort:** 6-9 days

### Future Work (Backlog)
1. **Observable effects in obs** (EFF-7)
2. **Item custom commands runtime** (ITEM-12)
3. **Edge case documentation** (DOC-9, DOC-10)

---

## Risk Assessment

### High Risk Items
- **Runtime performance** (RUN-8): No baseline benchmarks, unknown if <5% target achievable
  - **Mitigation:** Profile early, implement eager fallback

- **Observation dimension stability** (VFS-11, BREAK-9): Item VFS changes may break checkpoints
  - **Mitigation:** Acceptable (pre-release), document breaking change

### Medium Risk Items
- **Migration effort** (BREAK-1 through BREAK-4): All configs need updates
  - **Mitigation:** Start with test packs, validate pattern

- **Cross-validation completeness** (COMP-12, COMP-17): Some reference checks missing
  - **Mitigation:** Add validation incrementally, test thoroughly

### Low Risk Items
- **Documentation** (DOC-* category): Doesn't block functionality
  - **Mitigation:** Follow-up sprint work acceptable

---

## Conclusion

**Merge Readiness:** [READY | NOT READY | BLOCKED]

**Key Blockers:**
1. [Primary blocker with mitigation plan]
2. [Secondary blocker with mitigation plan]

**Next Steps:**
1. [Immediate action 1]
2. [Immediate action 2]
3. [Immediate action 3]

**Timeline Estimate:** [X] days to merge-ready state

---

## Appendix A: Verification Commands

```bash
# Grep verification patterns
grep -r "variables_reference.yaml" src/townlet/  # Should only find agent/global scope
grep -r "EffectCatalog(" src/townlet/environment/  # Should not find runtime construction
grep -r "def spawn_item" src/townlet/items/  # Check vfs_profile parameter

# Test count verification
pytest --collect-only tests/test_townlet/unit/world/expression/ | grep "test session starts"
pytest --collect-only tests/test_townlet/unit/vfs/ | grep "test session starts"
pytest --collect-only tests/test_townlet/unit/effects/ | grep "test session starts"
pytest --collect-only tests/test_townlet/unit/items/ | grep "test session starts"

# Schema validation
python -m townlet.compiler compile configs/test/items_smoke/  # Should succeed
python -m townlet.compiler validate configs/test/effects_smoke/  # Should succeed

# Performance baseline
pytest tests/test_townlet/integration/test_vectorized_env.py --benchmark-only
```

## Appendix B: Evidence Standards Reference

See `docs/plans/vfs_uplift/validation/evidence-standards.md` for detailed criteria.

**Quick Reference:**
- ✅ COMPLETE: Implementation + Tests + Docs + No obvious gaps
- ⚠️ PARTIAL: Implementation exists but missing tests/docs/error handling
- ❌ MISSING: No implementation found (grep/search came up empty)
- 🔍 UNCLEAR: Found code but can't confirm it matches requirement (need deeper investigation)
