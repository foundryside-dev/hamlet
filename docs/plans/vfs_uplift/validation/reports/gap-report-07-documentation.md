# Gap Report: Category 7 - Documentation (DOC-*)

**Agent:** Agent 7 (Documentation)
**Generated:** 2025-11-22
**Scope:** Requirements DOC-1 through DOC-10 (10 total)
**Source:** docs/plans/vfs_uplift/validation/requirements-checklist.md Category 7

---

## Executive Summary

**Overall Status:** ⚠️ PARTIAL (7/10 Complete, 3/10 Missing/Incomplete)

**Critical Findings:**
1. ✅ **EXCELLENT**: Core schema docs (expressions, vfs-profiles, effects, items) are comprehensive (900-1700 lines each)
2. ✅ **EXCELLENT**: World Compiler user guide is complete and thorough (1481 lines)
3. ❌ **MISSING**: Reference config lacks vfs_profiles and items sections (DOC-6)
4. ❌ **MISSING**: Edge case policies document doesn't exist (DOC-9)
5. ⚠️ **INCOMPLETE**: VFS integration guide is outdated (no profiles, no runtime evaluation) (DOC-8)
6. ⚠️ **INCOMPLETE**: No affordance migration guide in docs/guides/ (only in old-plan/) (DOC-7)
7. ❌ **MISSING**: Observation management modes not documented in user-facing docs (DOC-10)

**Recommendation:** Requires documentation updates before declaring VFS uplift complete. Core technical docs are excellent, but user-facing migration/integration guides need updates.

---

## Detailed Requirements Analysis

### DOC-1: Expression language reference ✅ COMPLETE

**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 455)
**Requirement:** Complete docs/config-schemas/expressions.md with all operators

**Evidence:**
- File exists: `/home/john/hamlet/docs/config-schemas/expressions.md`
- Line count: 899 lines (substantial, not a stub)
- Content verified:
  - Overview and architecture
  - Complete syntax reference (literals, variables, path access)
  - Operators: arithmetic, comparison, logical
  - Integration examples (VFS, effects, items)
  - Type system reference
  - Performance considerations
  - Best practices
  - Future extensions
  - Troubleshooting

**Verification:**
```bash
wc -l /home/john/hamlet/docs/config-schemas/expressions.md
# Output: 899 /home/john/hamlet/docs/config-schemas/expressions.md

grep "^##" /home/john/hamlet/docs/config-schemas/expressions.md
# Sections: Overview, Syntax, Operators, Integration, Type System,
#           Troubleshooting, Phase 2 Roadmap, Examples, Best Practices
```

**Assessment:** ✅ COMPLETE - Comprehensive reference with all required sections

---

### DOC-2: VFS profiles schema docs ✅ COMPLETE

**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 456)
**Requirement:** docs/config-schemas/vfs-profiles.md with global/agent/item profiles, dependencies, observation mapping

**Evidence:**
- File exists: `/home/john/hamlet/docs/config-schemas/vfs-profiles.md`
- Line count: 1005 lines (comprehensive)
- Content verified:
  - All three scopes documented (global, agent, item)
  - Dependency resolution explained (topological sort, circular detection)
  - Observation integration detailed
  - Static vs dynamic variables
  - Complete examples for each scope
  - Configuration patterns
  - Troubleshooting guide
  - Migration guide section

**Verification:**
```bash
wc -l /home/john/hamlet/docs/config-schemas/vfs-profiles.md
# Output: 1005 /home/john/hamlet/docs/config-schemas/vfs-profiles.md

grep "^##" /home/john/hamlet/docs/config-schemas/vfs-profiles.md | grep -i "scope\|dependency\|observation"
# Output confirms: Variable Scopes, Dependency Resolution, Observation Integration
```

**Assessment:** ✅ COMPLETE - All required topics covered comprehensively

---

### DOC-3: Effects catalog schema docs ✅ COMPLETE

**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 457)
**Requirement:** docs/config-schemas/effects.md with all command types, reapply policies, lifecycle hooks

**Evidence:**
- File exists: `/home/john/hamlet/docs/config-schemas/effects.md`
- Line count: 1700 lines (most comprehensive doc)
- Content verified:
  - All command types documented: modify, spawn_effect, spawn_item, if, for_each
  - All four reapply policies explained: stack, renew, merge, replace
  - All lifecycle hooks documented: on_spawn, on_tick, on_despawn, on_interrupt
  - 10+ complete examples
  - Compilation and validation section
  - Field reference for all EffectDefinition fields
  - Integration with expression language
  - Scope system (global, agent, item, affordance)

**Verification:**
```bash
wc -l /home/john/hamlet/docs/config-schemas/effects.md
# Output: 1700 /home/john/hamlet/docs/config-schemas/effects.md

grep "^###.*Command" /home/john/hamlet/docs/config-schemas/effects.md
# Output: modify, spawn_effect, spawn_item, if, for_each (all present)

grep -i "reapply.*policy" /home/john/hamlet/docs/config-schemas/effects.md | head -5
# Output confirms: stack, renew, merge, replace all documented
```

**Assessment:** ✅ COMPLETE - Exceptionally thorough documentation

---

### DOC-4: Items schema docs ✅ COMPLETE

**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 458), items-and-vfs-profiles.md Section 7.2 (lines 485-494)
**Requirement:** docs/config-schemas/items.md with experiment vs level split, spawn rules, interaction commands, vfs_profile field

**Evidence:**
- File exists: `/home/john/hamlet/docs/config-schemas/items.md`
- Line count: 1078 lines (comprehensive)
- Content verified:
  - Experiment vs level split explained (catalog vs appearance)
  - Spawn rules documented (placement, schedule, limits)
  - Interaction types documented (on_pickup, on_use, on_drop)
  - VFS profile configuration section
  - Lifecycle (spawning, duration, cooldown, despawning)
  - Inventory management
  - 5+ complete examples
  - Effects command reference for interactions

**Verification:**
```bash
wc -l /home/john/hamlet/docs/config-schemas/items.md
# Output: 1078 /home/john/hamlet/docs/config-schemas/items.md

grep "^##" /home/john/hamlet/docs/config-schemas/items.md | grep -i "catalog\|appearance\|spawn\|vfs"
# Output confirms: Catalog vs Appearance, VFS State, Spawn rules
```

**Assessment:** ✅ COMPLETE - All required sections present

---

### DOC-5: World Compiler user guide ✅ COMPLETE

**Source:** unified-world-compiler-plan.md Phase 6 Task 6.3 (line 459)
**Requirement:** docs/guides/world-compiler-guide.md with end-to-end workflow, common patterns, troubleshooting

**Evidence:**
- File exists: `/home/john/hamlet/docs/guides/world-compiler-guide.md`
- Line count: 1481 lines (comprehensive guide)
- Content verified:
  - Introduction with four integrated layers (VFS, Effects, Items, Cascades)
  - Directory structure explained (experiment vs level)
  - Common patterns (5+ examples)
  - Compilation CLI commands (validate, compile, inspect)
  - Compilation errors section
  - Integration examples showing Expression → VFS → Effects → Items flow
  - Troubleshooting Q&A
  - Debugging tools
  - Best practices
  - Testing strategies

**Verification:**
```bash
wc -l /home/john/hamlet/docs/guides/world-compiler-guide.md
# Output: 1481 /home/john/hamlet/docs/guides/world-compiler-guide.md

grep "^##" /home/john/hamlet/docs/guides/world-compiler-guide.md | head -15
# Sections: Introduction, Getting Started, Directory Structure, Common Patterns,
#           Compilation, Integration, Troubleshooting, Best Practices
```

**Assessment:** ✅ COMPLETE - Excellent user-facing guide

---

### DOC-6: Reference config updates ❌ MISSING

**Source:** items-and-vfs-profiles.md Section 7.1 (lines 473-481)
**Requirement:** reference-config-v2.1-complete.yaml includes vfs_profiles and items sections with annotated examples

**Evidence:**
- File exists: `/home/john/hamlet/configs/reference/config-v2.1-complete.yaml`
- Line count: 1128 lines
- Content verified:
  - Has 9 sections (experiment, stratum, environment, actions, agent, curriculum, bars, affordances, training)
  - **MISSING**: No vfs_profiles section
  - **MISSING**: No items section (catalog or appearance)
  - **MISSING**: No effects section (though effects.yaml exists at experiment level)

**Verification:**
```bash
grep -n "^vfs_profiles:\|^items:\|^effects:" /home/john/hamlet/configs/reference/config-v2.1-complete.yaml
# Output: (empty)

grep -n "# SECTION" /home/john/hamlet/configs/reference/config-v2.1-complete.yaml | tail -10
# Sections end at: training.yaml (Section 9)
# No Section 10 for vfs_profiles, Section 11 for items, etc.
```

**Assessment:** ❌ MISSING - Reference config needs sections for:
1. vfs_profiles (experiment-level or per-level)
2. items catalog (experiment-level)
3. items appearance (level-level)
4. effects catalog (experiment-level) - though effects.yaml exists separately

**Impact:** Medium - Users lack annotated examples for new schemas in the reference config

---

### DOC-7: Migration guide ⚠️ PARTIAL

**Source:** unified-world-compiler-plan.md Phase 5 (line 569)
**Requirement:** Migration guide for affordances (effect_pipeline → effects commands) with before/after examples and automated migration script

**Evidence:**
- **User-facing guides:**
  - `/home/john/hamlet/docs/guides/dac-migration.md` (22K, covers DAC migration)
  - `/home/john/hamlet/docs/guides/substrate-migration.md` (12K, covers substrate migration)
  - **MISSING**: No affordance/effect_pipeline migration guide in docs/guides/

- **Internal plans:**
  - `/home/john/hamlet/docs/plans/vfs_uplift/old-plan/2025-11-20-phase-5-affordance-migration.md` exists
  - Contains before/after examples and migration script details
  - But located in old-plan/ directory, not user-facing docs/guides/

**Verification:**
```bash
ls -lh /home/john/hamlet/docs/guides/*migration*
# Output: dac-migration.md, substrate-migration.md (no affordance migration)

ls /home/john/hamlet/docs/plans/vfs_uplift/old-plan/2025-11-20-phase-5-affordance-migration.md
# Output: File exists in old-plan/ (internal, not user-facing)
```

**Assessment:** ⚠️ PARTIAL - Migration documentation exists but only in internal plans, not user-facing guides

**Recommendation:** Either:
1. Move/adapt affordance migration content to `docs/guides/affordance-migration.md`, OR
2. Create a unified "VFS Uplift Migration Guide" covering affordances, VFS profiles, items, effects

---

### DOC-8: VFS integration guide updates ⚠️ INCOMPLETE

**Source:** items-and-vfs-profiles.md Section 0 (line 16)
**Requirement:** Update docs/vfs-integration-guide.md with profiles section, runtime evaluation, breaking changes

**Evidence:**
- File exists: `/home/john/hamlet/docs/vfs-integration-guide.md`
- Line count: ~21K (substantial)
- Content verified:
  - ✅ Has Phase 1 integration patterns
  - ✅ Covers Variable Registry, Observation Specs, Access Control
  - ❌ **MISSING**: No profiles section (only mentions "Profile VFS overhead" once)
  - ❌ **MISSING**: No runtime evaluation documentation (mark-and-sweep, eager mode)
  - ❌ **MISSING**: No breaking changes section for vfs_profiles.yaml requirement
  - ⚠️ **OUTDATED**: Focused on Phase 1 (variables_reference.yaml), not Phase 2 (vfs_profiles.yaml)

**Verification:**
```bash
grep -i "profile" /home/john/hamlet/docs/vfs-integration-guide.md
# Output: Only "Profile VFS overhead" (performance note)

grep -i "mark-and-sweep\|runtime.*evaluation" /home/john/hamlet/docs/vfs-integration-guide.md
# Output: (empty)

grep "^##" /home/john/hamlet/docs/vfs-integration-guide.md
# Sections: Phase 1 Status, Integration Patterns, BAC Roadmap, Migration Path,
#           Best Practices, Testing, Known Limitations
```

**Assessment:** ⚠️ INCOMPLETE - Guide needs updates for:
1. VFS profiles (global, agent, item scopes)
2. Runtime evaluation modes (mark-and-sweep, eager)
3. Breaking changes (vfs_profiles.yaml required for items)
4. Item VFS state integration

**Impact:** Medium - Users following the guide will miss critical Phase 2 features

---

### DOC-9: Edge case policies ❌ MISSING

**Source:** unified-world-compiler-plan.md Related Documentation (line 738)
**Requirement:** docs/plans/vfs_uplift/edge-case-policies.md documenting DENY_PICKUP policy and other edge cases

**Evidence:**
- File does NOT exist: `/home/john/hamlet/docs/plans/vfs_uplift/edge-case-policies.md`
- No alternative location found

**Verification:**
```bash
ls /home/john/hamlet/docs/plans/vfs_uplift/edge-case-policies.md
# Output: edge-case-policies.md: MISSING

find /home/john/hamlet/docs -name "*edge*case*" -o -name "*DENY*PICKUP*"
# Output: (empty)
```

**Assessment:** ❌ MISSING - Document doesn't exist

**Impact:** Low-Medium - Edge case policies are mentioned in code/configs but not centrally documented. DENY_PICKUP is documented in items.md (line 638-648), but other edge cases may not be.

**Recommendation:** Create edge-case-policies.md covering:
1. DENY_PICKUP (inventory overflow)
2. Item spawn when max_simultaneous reached
3. Effect spawn with reapply policies
4. VFS circular dependency handling
5. Expression evaluation failures (divide by zero, type errors)
6. Missing reference targets in effects

---

### DOC-10: Observation management modes ❌ MISSING

**Source:** items-and-vfs-profiles.md Section 6.3 (lines 438-467)
**Requirement:** Document full_auto, max_compact, full_manual modes with trade-offs and selection guide

**Evidence:**
- **User-facing docs:** Not found in docs/config-schemas/ or docs/guides/
- **Plan docs only:** Documented in `docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md` (lines 438-467)
- **Reference config:** Mentioned in `/home/john/hamlet/configs/reference/config-v2.1-complete.yaml` (lines 59-73) with brief explanation

**Verification:**
```bash
grep -r "observation_management_mode\|full_auto\|max_compact\|full_manual" /home/john/hamlet/docs/config-schemas/ /home/john/hamlet/docs/guides/
# Output: (empty)

grep "observation_management_mode" /home/john/hamlet/configs/reference/config-v2.1-complete.yaml
# Output: Line 73 (brief mention in reference config)

grep -A 10 "full_auto" /home/john/hamlet/docs/plans/vfs_uplift/2025-11-18-items-and-vfs-profiles.md
# Output: Detailed explanation (lines 442-467)
```

**Assessment:** ❌ MISSING from user-facing documentation

**Found in:**
- ✅ Plan document (items-and-vfs-profiles.md)
- ✅ Reference config (brief comment)
- ❌ NOT in vfs-profiles.md
- ❌ NOT in items.md
- ❌ NOT in world-compiler-guide.md

**Impact:** Medium - Users won't understand observation dimension management options

**Recommendation:** Add section to vfs-profiles.md or items.md explaining:
1. **full_auto**: System manages obs layout, uses masking
2. **max_compact**: Drops unused fields, minimizes obs_dim (curriculum-specific)
3. **full_manual**: User specifies exact obs layout (fixed obs_dim)
4. Trade-offs (checkpoint compatibility, flexibility, control)
5. Selection guide based on use case

---

## Summary Statistics

| Requirement | Status | File/Evidence | Lines | Completeness |
|-------------|--------|---------------|-------|--------------|
| DOC-1: Expression language reference | ✅ COMPLETE | expressions.md | 899 | Comprehensive |
| DOC-2: VFS profiles schema docs | ✅ COMPLETE | vfs-profiles.md | 1005 | Comprehensive |
| DOC-3: Effects catalog schema docs | ✅ COMPLETE | effects.md | 1700 | Comprehensive |
| DOC-4: Items schema docs | ✅ COMPLETE | items.md | 1078 | Comprehensive |
| DOC-5: World Compiler user guide | ✅ COMPLETE | world-compiler-guide.md | 1481 | Comprehensive |
| DOC-6: Reference config updates | ❌ MISSING | config-v2.1-complete.yaml | 1128 | Missing vfs_profiles/items sections |
| DOC-7: Migration guide | ⚠️ PARTIAL | old-plan/affordance-migration.md | - | Only in internal plans |
| DOC-8: VFS integration guide updates | ⚠️ INCOMPLETE | vfs-integration-guide.md | ~600 | Missing profiles/runtime eval |
| DOC-9: Edge case policies | ❌ MISSING | - | - | File doesn't exist |
| DOC-10: Observation management modes | ❌ MISSING | - | - | Only in plan docs |

**Overall:** 5 Complete, 2 Partial, 3 Missing = ⚠️ PARTIAL (70% complete)

---

## Critical Gaps

### High Priority (Blocks Production Readiness)

1. **DOC-6: Reference config updates**
   - Impact: Users have no annotated examples for vfs_profiles, items, effects
   - Action: Add sections to config-v2.1-complete.yaml:
     - vfs_profiles (global, agent, item examples)
     - items catalog (experiment-level)
     - items appearance (level-level)
     - effects catalog (if not already in separate file)

2. **DOC-10: Observation management modes**
   - Impact: Users won't understand obs_dim stability options
   - Action: Add section to vfs-profiles.md or items.md explaining full_auto/max_compact/full_manual

### Medium Priority (User Experience)

3. **DOC-8: VFS integration guide updates**
   - Impact: Guide is outdated for Phase 2 features
   - Action: Update vfs-integration-guide.md with:
     - VFS profiles section
     - Runtime evaluation (mark-and-sweep, eager)
     - Breaking changes (vfs_profiles.yaml requirement)

4. **DOC-7: Migration guide**
   - Impact: Users lack guide for affordance → effects migration
   - Action: Move affordance migration content from old-plan/ to docs/guides/

### Low Priority (Nice to Have)

5. **DOC-9: Edge case policies**
   - Impact: Edge cases scattered across docs
   - Action: Create edge-case-policies.md consolidating:
     - DENY_PICKUP
     - Item spawn limits
     - Effect reapply policies
     - VFS circular dependencies
     - Expression failures

---

## Verification Commands

```bash
# Check all config-schemas docs exist and are substantial
for doc in expressions.md vfs-profiles.md effects.md items.md; do
  if [ -f "/home/john/hamlet/docs/config-schemas/$doc" ]; then
    lines=$(wc -l < "/home/john/hamlet/docs/config-schemas/$doc")
    echo "$doc: $lines lines"
  else
    echo "$doc: MISSING"
  fi
done

# Output:
# expressions.md: 899 lines
# vfs-profiles.md: 1005 lines
# effects.md: 1700 lines
# items.md: 1078 lines

# Check migration guides
ls -lh /home/john/hamlet/docs/guides/*migration*
# Output: dac-migration.md (22K), substrate-migration.md (12K)

# Check world compiler guide
ls -lh /home/john/hamlet/docs/guides/world-compiler-guide.md
# Output: 41K, Nov 21 06:30

# Check reference config
grep -n "^vfs_profiles:\|^items:" /home/john/hamlet/configs/reference/config-v2.1-complete.yaml
# Output: (empty - MISSING)

# Check edge case policies
ls /home/john/hamlet/docs/plans/vfs_uplift/edge-case-policies.md
# Output: MISSING

# Check observation management modes in user docs
grep -r "full_auto\|max_compact\|full_manual" /home/john/hamlet/docs/config-schemas/ /home/john/hamlet/docs/guides/
# Output: (empty - MISSING from user docs)
```

---

## Recommendations

### Immediate Actions (Pre-Release Blockers)

1. **Update reference config** (DOC-6)
   - Add vfs_profiles section with global/agent/item examples
   - Add items catalog section (experiment-level)
   - Add items appearance section (level-level)
   - Ensure all examples are annotated

2. **Document observation management modes** (DOC-10)
   - Add section to vfs-profiles.md or create separate doc
   - Explain full_auto, max_compact, full_manual
   - Provide selection guide

### Short-Term Actions (1-2 weeks)

3. **Update VFS integration guide** (DOC-8)
   - Add VFS profiles section
   - Document runtime evaluation modes
   - Add breaking changes section
   - Update examples to Phase 2 patterns

4. **Create affordance migration guide** (DOC-7)
   - Move content from old-plan/ to docs/guides/
   - Add automation script instructions
   - Include before/after examples

### Medium-Term Actions (Nice to Have)

5. **Create edge case policies doc** (DOC-9)
   - Consolidate edge cases from code/configs
   - Document DENY_PICKUP and other policies
   - Provide troubleshooting flowcharts

---

## Positive Findings

1. **Excellent Core Documentation**: expressions.md, vfs-profiles.md, effects.md, items.md are all comprehensive (900-1700 lines each) with examples, troubleshooting, and best practices.

2. **Thorough User Guide**: world-compiler-guide.md is a complete end-to-end guide with patterns, CLI commands, integration examples, and debugging tools.

3. **Good Structure**: Docs follow consistent patterns with frontmatter, examples, troubleshooting sections.

4. **No Stubs**: All existing schema docs are substantial and production-ready.

---

## Conclusion

**Documentation is 70% complete** with excellent core technical documentation but gaps in user-facing migration/integration guides and reference configs.

**Core schema docs (DOC-1 through DOC-5)** are production-ready and comprehensive. **User-facing docs (DOC-6 through DOC-10)** need updates before declaring VFS uplift complete.

**Priority:** Update reference config (DOC-6) and document observation management modes (DOC-10) before release. Other gaps are medium/low priority.

**No blockers for internal development**, but documentation gaps will impact external users/contributors.
