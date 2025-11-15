# Phase 5 Status: Minimal CompiledUniverse Return

**Date**: 2025-11-15
**Status**: BLOCKED - Task scoping issue
**Branch**: `config-refactor`

## Summary

Phase 5 task ("Implement Minimal CompiledUniverse Return") encountered a **fundamental scoping problem**: creating even a "minimal" CompiledUniverse from v2.1 hierarchical configs requires substantial type conversion between v2.1 and legacy config schemas.

## What Was Attempted

### Goal
Implement `_compile_v21_hierarchical` to return a minimal `CompiledUniverse` using data from Stages 1-2 (hierarchical loading + vocabulary validation).

### Approach 1: Full Type Conversion
Attempted to convert v2.1 hierarchical structures to legacy flat structures:

**V2.1 Structure** → **Legacy Structure**
- `MeterConfig` (nested: depletion/recovery/bounds) → `BarConfig` (flat: base_depletion, etc.)
- `CascadeParamConfig` (source/target/threshold/strength) → `CascadeConfig` (adds name/description)
- `SubstrateConfig` (no version/description) → `SubstrateConfig` (requires version/description)
- `TrainingV2Config` (nested sections) → `TrainingConfig` (flat, ~15 required fields)
- Plus: `CurriculumConfig`, `ExplorationConfig`, `PopulationConfig`, `CuesConfig`

**Result**: Hit validation errors due to **No-Defaults Principle** - every config requires ALL fields explicitly specified, making manual construction extremely tedious.

### Approach 2: Load Legacy Template
Attempted to load `configs/L0_0_minimal` as a `HamletConfig` template to avoid type conversions.

**Result**: Recursive loading context issue - `HamletConfig.load()` expects to be called from root context, fails when called during another compilation.

### Approach 3: Stub hamlet_config
Attempted to pass `None` for `hamlet_config` field.

**Result**: Won't work - `CompiledUniverse` requires valid `HamletConfig` (field is not Optional).

## Root Cause Analysis

**The "minimal" task is not actually minimal.** Here's why:

1. **CompiledUniverse is legacy-first**: Designed around flat `HamletConfig` structure
2. **V2.1 is fundamentally different**: Hierarchical with separate experiment/stratum/environment/levels
3. **Type conversion is non-trivial**: Requires mapping between incompatible schemas
4. **No-Defaults Principle amplifies complexity**: Can't construct configs with partial data

## What IS Implemented (Stages 1-2)

✅ **Stage 1**: Hierarchical config loading (`_load_experiment_structure`)
- Loads `experiment.yaml`, `stratum.yaml`, `environment.yaml`, `actions.yaml`, `agent.yaml`
- Loads all curriculum levels from `levels/` directory
- Returns structured tuple of configs

✅ **Stage 2**: Cross-curriculum vocabulary validation (`_validate_vocabulary_consistency`)
- Enforces WHAT vs HOW split (vocabulary in environment.yaml, parameters in levels/)
- Validates all levels use same meters/affordances as environment.yaml
- Provides clear error messages for vocabulary mismatches

## What Is NOT Implemented

❌ **Stages 3-7**: Full compiler pipeline
- Symbol table building
- Reference resolution
- Observation spec generation
- Optimization data computation
- CompiledUniverse emission

❌ **V2.1 → Legacy Conversion**: Type mapping between config versions

❌ **Minimal CompiledUniverse**: Even stub version requires substantial scaffolding

## Recommended Path Forward

### Option A: Defer Phase 5 (RECOMMENDED)
Accept that "minimal CompiledUniverse" is a misnomer. Instead:

1. **Document Stages 1-2 as complete** (they work and are tested)
2. **Mark Stages 3-7 as TODO** (clear NotImplementedError with explanation)
3. **Focus on v2.1 config migration** first (get all levels into hierarchical structure)
4. **Then implement full compiler** (Stages 3-7) once config migration complete

**Rationale**: Trying to bridge v2.1 ↔ legacy creates technical debt. Better to fully commit to v2.1, then implement compiler properly.

### Option B: Create Parallel V2.1 CompiledUniverse
Define a new `CompiledUniverseV21` class that:
- Stores v2.1 hierarchical configs directly (no conversion)
- Has minimal metadata (name, counts, hashes)
- Can be extended incrementally as Stages 3-7 implemented

**Rationale**: Avoids type conversion, allows independent v2.1 development.

### Option C: Implement Full Type Conversion (NOT RECOMMENDED)
Complete all v2.1 → legacy conversions to create valid `HamletConfig`.

**Rationale**: High effort, creates maintenance burden, delays v2.1 adoption.

## Files Modified (To Be Reverted)

```
src/townlet/universe/compiler.py
```

**Changes**: Multiple attempts at type conversion in `_compile_v21_hierarchical`
**Status**: Experimental/incomplete, should be reverted to clean NotImplementedError

## Testing Status

✅ **Stages 1-2 Work**: Can load and validate v2.1 hierarchical configs
```bash
# This works:
from townlet.universe.compiler import UniverseCompiler
compiler = UniverseCompiler()
experiment, stratum, environment, actions, agent, levels = compiler._load_experiment_structure(Path("configs/default_curriculum"))
compiler._validate_vocabulary_consistency(environment, levels)
# Output: Validation passes, no errors
```

❌ **Full Compilation Blocked**: Cannot create CompiledUniverse without type conversion
```bash
# This raises NotImplementedError:
compiled = compiler.compile(Path("configs/default_curriculum"))
```

## Conclusion

**Phase 5 task as specified is blocked** by insufficient scoping. The task assumed "minimal" meant "stub some fields", but reality is "convert between incompatible type systems".

**Recommendation**: Accept Stages 1-2 as Phase 5 deliverable, defer full compilation to Phase 6+.

## Next Steps

1. Revert experimental compiler changes
2. Restore clean NotImplementedError in `_compile_v21_hierarchical`
3. Update BUNDLE-01 roadmap to reflect revised phase breakdown
4. Proceed with config migration (get all levels into v2.1 structure)
5. Implement Stages 3-7 once migration complete

---

**Lessons Learned**:
- "Minimal" is context-dependent - in strongly-typed systems with no-defaults, there's no such thing as "minimal stub"
- Type conversion between incompatible schemas is a first-class engineering task, not a "quick bridge"
- Stages 1-2 (loading + validation) are valuable standalone deliverables - don't gate on full pipeline
