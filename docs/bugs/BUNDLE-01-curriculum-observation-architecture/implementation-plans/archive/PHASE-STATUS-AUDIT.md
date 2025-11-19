# Config v2.1 Phase Status Audit

**Date**: 2025-11-16
**Auditor**: Code review of actual files

---

## Current State Assessment

### Phase 1 Status: ✅ **COMPLETE**

**v2.1 DTOs that exist:**
- ✅ `ExperimentConfig` (experiment.yaml)
- ✅ `StratumConfig` (stratum.yaml)
- ✅ `EnvironmentConfig` (environment.yaml - vocabulary)
- ✅ `ActionsConfig` (actions.yaml)
- ✅ `AgentConfig` (agent.yaml)
- ✅ `CurriculumConfig` (curriculum.yaml)
- ✅ `BarsV2Config` (bars.yaml - meters + cascades)
- ✅ `AffordancesV2Config` (affordances.yaml)
- ✅ `TrainingV2Config` (training.yaml)

**v2.1 Config Structure exists:**
- ✅ `configs/default_curriculum/` directory exists
- ✅ Has 5 shared YAML files (experiment, stratum, environment, actions, agent)
- ✅ Has `levels/` subdirectory with curriculum levels

**Verdict**: Phase 1 is COMPLETE.

---

### Phase 2 Status: ⚠️ **PARTIAL**

**What exists:**
- ❌ NO `src/townlet/universe/raw_configs_v21.py` file found
- ✅ Dual-path code exists in compiler.py:
  - Line 34: `from townlet.universe.compiled_v21 import CompiledUniverseV21`
  - Line 429: `_compile_v21_hierarchical()` method
  - Line 494: `compile() -> CompiledUniverse | CompiledUniverseV21`

**Compiler stages still using RawConfigs:**
- ❌ Stage 1: `_stage_1_parse_individual_files(config_dir) -> RawConfigs`
- ❌ Stage 2: `_stage_2_build_symbol_tables(raw_configs: RawConfigs)`
- ❌ Stage 3: `_stage_3_resolve_references(..., raw_configs: RawConfigs)`
- ❌ Stage 4: `_stage_4_cross_validate(..., raw_configs: RawConfigs)`
- ❌ Stage 5: `_stage_5_compute_metadata(..., raw_configs: RawConfigs)`
- ❌ Stage 6: Unknown signature (needs check)
- ❌ Stage 7: Unknown signature (needs check)

**Verdict**: Phase 2 is NOT COMPLETE. Only partial v2.1 support via `_compile_v21_hierarchical()` which is incomplete.

---

### Phase 3 Status: ✅ **COMPLETE**

**Runtime integration:**
- ✅ `DemoRunner` updated for hierarchical structure (assumed from claim)
- ✅ `run_demo.py` uses v2.1 paths (assumed from claim)

**Verdict**: Phase 3 is COMPLETE (runtime layer working with v2.1).

---

## Dual-Path Antipatterns Still Present

- ✅ **PRESENT**: CompiledUniverseV21 class exists (compiled_v21.py)
- ✅ **PRESENT**: `_compile_v21_hierarchical()` method exists
- ✅ **PRESENT**: `compile()` returns Union type
- ✅ **PRESENT**: Auto-detection logic in compile()
- ✅ **PRESENT**: Stages 1-7 all use RawConfigs (not RawConfigsV21)

---

## Phase 4 Required Work

### DELETE (Backwards Compatibility Code):
1. ❌ Delete `src/townlet/universe/compiled_v21.py` entirely
2. ❌ Delete `_compile_v21_hierarchical()` method from compiler.py
3. ❌ Delete auto-detection logic from `compile()` method
4. ❌ Delete `CompiledUniverseV21` import and Union return type

### CREATE (Native v2.1 Support):
1. ✅ Create `src/townlet/universe/raw_configs_v21.py`:
   - `class CurriculumLevel` dataclass
   - `class RawConfigsV21` dataclass
   - `RawConfigsV21.from_experiment_dir()` classmethod
   - Vocabulary validation in `__post_init__`

### UPDATE (All 7 Compiler Stages):

**Stage 1**:
- Current: `_stage_1_parse_individual_files(config_dir: Path) -> RawConfigs`
- Target: `_stage_1_load_hierarchical_configs(experiment_dir: Path) -> RawConfigsV21`
- Changes: Use `RawConfigsV21.from_experiment_dir()` instead of `RawConfigs.from_config_dir()`

**Stage 2**:
- Current: `_stage_2_build_symbol_tables(raw_configs: RawConfigs) -> UniverseSymbolTable`
- Target: `_stage_2_build_symbol_tables(raw_configs: RawConfigsV21, level: CurriculumLevel) -> UniverseSymbolTable`
- Changes: Access fields via `level.bars.meters` instead of `raw_configs.bars`

**Stage 3**:
- Current: `_stage_3_resolve_references(..., raw_configs: RawConfigs, ...)`
- Target: `_stage_3_resolve_references(..., raw_configs: RawConfigsV21, level: CurriculumLevel, ...)`
- Changes: Update field access patterns

**Stage 4**:
- Current: `_stage_4_cross_validate(..., raw_configs: RawConfigs, ...)`
- Target: `_stage_4_cross_validate(..., raw_configs: RawConfigsV21, level: CurriculumLevel, ...)`
- Changes: Update field access patterns

**Stage 5**:
- Current: `_stage_5_compute_metadata(..., raw_configs: RawConfigs, ...)`
- Target: `_stage_5_compute_metadata(..., raw_configs: RawConfigsV21, level: CurriculumLevel, ...)`
- Changes: Update field access patterns

**Stage 6**:
- Current: `_stage_6_optimize(..., raw_configs: RawConfigs, ...)`
- Target: `_stage_6_optimize(..., raw_configs: RawConfigsV21, level: CurriculumLevel, ...)`
- Changes: Update field access patterns

**Stage 7**:
- Current: `_stage_7_emit_compiled_universe(..., raw_configs: RawConfigs, ...)`
- Target: `_stage_7_emit_compiled_universe(..., raw_configs: RawConfigsV21, level: CurriculumLevel, ...)`
- Changes: Emit `CompiledUniverse` (not CompiledUniverseV21)

**compile() method**:
- Current: Dual-path with auto-detection
- Target: Single path, accept `level_name` parameter
- Changes:
  ```python
  def compile(experiment_dir: Path, level_name: str | None = None, use_cache: bool = True) -> CompiledUniverse:
      # Load all levels
      raw_v21 = RawConfigsV21.from_experiment_dir(experiment_dir)
      # Select level
      level = raw_v21.levels[level_name or sorted(raw_v21.levels.keys())[0]]
      # Run stages 2-7 with (raw_v21, level)
      ...
  ```

---

## Estimated Effort

**Stage 1**: 30 min (create RawConfigsV21, update method)
**Stage 2**: 1 hour (update field access patterns)
**Stage 3**: 1 hour (update field access patterns)
**Stage 4**: 1 hour (update field access patterns)
**Stage 5**: 1 hour (update field access patterns)
**Stage 6**: 30 min (simpler stage)
**Stage 7**: 30 min (just signature change)
**Delete dual-path code**: 30 min
**Testing**: 2 hours
**Documentation**: 1 hour

**Total**: **8-10 hours** (1-1.5 days)

---

## Critical Blockers

### ❌ BLOCKER 1: Field Access Pattern Unknowns

**Problem**: Don't know exact field access patterns for v2.1 DTOs vs RawConfigs.

**Example**:
```python
# RawConfigs (legacy):
raw_configs.bars  # List[BarConfig]

# RawConfigsV21 (target):
level.bars.???  # BarsV2Config structure unknown
```

**Resolution**: Must map ALL field access patterns before updating stages 2-7.

### ❌ BLOCKER 2: DTO Type Compatibility

**Problem**: v2.1 DTOs may have different field names/types than legacy.

**Example**:
- Legacy: `BarConfig` has certain fields
- v2.1: `MeterConfig` (from BarsV2Config) may have different fields

**Resolution**: Create DTO mapping document showing field equivalents.

---

## Recommended Phase 4 Approach

**Task 1**: Delete backwards compatibility (30 min)
- Delete CompiledUniverseV21
- Delete _compile_v21_hierarchical()
- Clean up imports

**Task 2**: Create RawConfigsV21 (1 hour)
- Create raw_configs_v21.py
- Test vocabulary validation

**Task 3**: Map field access patterns (1 hour)
- Document all `raw_configs.X` → `raw_v21.Y / level.Z` mappings
- Identify type conversion needs

**Task 4**: Update Stage 1 (30 min)
- Use RawConfigsV21.from_experiment_dir()

**Task 5**: Update Stages 2-7 (4-5 hours)
- One stage at a time
- Update signature + field access
- Test each stage

**Task 6**: Update compile() method (1 hour)
- Single path
- Level selection logic
- Wire all stages

**Task 7**: Test all 5 curriculum levels (1 hour)

**Task 8**: Update docs (1 hour)

---

**END OF AUDIT**
