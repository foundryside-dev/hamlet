# Plan Fixes for v2.1 Implementation - 2025-11-16

**Purpose**: Document all corrections needed to fix the 13 blocking issues in phase plans

**Status**: FIXING IN PROGRESS

---

## Fix Summary

### Files to Update:
1. `2025-11-16-v2.1-phase1-create-dtos.md` - Issues #2, #3
2. `2025-11-16-v2.1-phase4-native-compiler.md` - Issues #1, #4, #5, #6, #13
3. `2025-11-16-v2.1-phase6-test-migration.md` - Issues #2, #4, #11
4. `2025-11-16-v2.1-phase7-documentation.md` - Issue #4

---

## Issue #1: Field Access Pattern - Phase 4 Field Mapping Doc

**File**: `2025-11-16-v2.1-phase4-native-compiler.md`
**Location**: Task 3, field mapping document (around line 405-440)

**WRONG**:
```markdown
### Meters/Bars:
- `raw_configs.bars` (List[BarConfig]) → `level.bars.meters` (List[MeterConfig])

### Affordances:
- `raw_configs.affordances` → `level.affordances.affordances`
```

**CORRECT**:
```markdown
### Meters/Bars:
- `raw_configs.bars` (List[BarConfig]) → `level.bars.bars.meters` (List[MeterConfig])

### Cascades:
- `raw_configs.cascades` → `level.bars.bars.cascades`

### Affordances:
- `raw_configs.affordances` → `level.affordances.affordances.affordances`
```

---

## Issue #2: Wrong Module Names - Phase 1, Task 11

**File**: `2025-11-16-v2.1-phase1-create-dtos.md`
**Location**: Task 11, line 366-374 (imports section)

**WRONG**:
```python
from townlet.config.bars_config import BarsConfig
from townlet.config.affordances_config import AffordancesConfig
from townlet.config.training_config import TrainingConfig
```

**CORRECT**:
```python
from townlet.config.bars_v2_config import BarsV2Config
from townlet.config.affordances_v2_config import AffordancesV2Config
from townlet.config.training_v2_config import TrainingV2Config
```

---

## Issue #3: Wrong File Names - Phase 1, Tasks 8-10

**File**: `2025-11-16-v2.1-phase1-create-dtos.md`
**Location**: Task descriptions around line 317-327

**WRONG**:
```markdown
- **Task 8**: `BarsConfig` (bars.yaml) - File: `bars_config.py`
- **Task 9**: `AffordancesConfig` (affordances.yaml) - File: `affordances_config.py`
- **Task 10**: `TrainingConfig` (training.yaml) - File: `training_config.py`
```

**CORRECT**:
```markdown
- **Task 8**: `BarsV2Config` (bars.yaml) - File: `bars_v2_config.py`
- **Task 9**: `AffordancesV2Config` (affordances.yaml) - File: `affordances_v2_config.py`
- **Task 10**: `TrainingV2Config` (training.yaml) - File: `training_v2_config.py`
```

---

## Issue #4: Wrong Argument Name - Multiple Phases

### Phase 4, Task 6

**File**: `2025-11-16-v2.1-phase4-native-compiler.md`
**Location**: Line 736 and throughout compile() method

**WRONG**:
```python
def compile(
    self,
    experiment_dir: Path,
    level_name: str | None = None,  # ❌
    use_cache: bool = True
) -> CompiledUniverse:
```

**CORRECT**:
```python
def compile(
    self,
    experiment_dir: Path,
    primary_level: str | None = None,  # ✅
    use_cache: bool = True
) -> CompiledUniverse:
```

**All references to `level_name` parameter in compile() signature must be changed to `primary_level`**

### Phase 6, Task 1

**File**: `2025-11-16-v2.1-phase6-test-migration.md`
**Location**: Test examples throughout

**Pattern to find and replace**:
- `primary_level="L1_full_observability"` ✅ (keep)
- `level_name="L1_full_observability"` ❌ (fix)

### Phase 7, Documentation

**File**: `2025-11-16-v2.1-phase7-documentation.md`
**Location**: All compile() examples

---

## Issue #5: Single-Level Compile - Phase 4, Task 6

**File**: `2025-11-16-v2.1-phase4-native-compiler.md`
**Location**: compile() method implementation (line 732-860)

**PROBLEM**: Current plan shows compile() only processing ONE level

**REQUIRED FIX**: Implement multi-level compilation loop

**ADD THIS SECTION** (around line 803-835):

```python
    # Compile ALL levels
    all_levels_metadata = {}
    for level_name, level in raw_configs.levels.items():
        logger.info(f"=== Compiling level: {level_name} ===")

        # Run stages 2-6 for this level
        logger.info("=== Stage 2: Building symbol tables ===")
        symbol_table = self._stage_2_build_symbol_tables(raw_configs, level)

        logger.info("=== Stage 3: Resolving references ===")
        resolved = self._stage_3_resolve_references(symbol_table, raw_configs, level)

        logger.info("=== Stage 4: Cross-validating configs ===")
        validated = self._stage_4_cross_validate(resolved, raw_configs, level)

        logger.info("=== Stage 5: Building rich metadata ===")
        metadata = self._stage_5_build_rich_metadata(validated, raw_configs, level)

        logger.info("=== Stage 6: Optimizing ===")
        optimized = self._stage_6_optimize(metadata, raw_configs, level)

        # Create level metadata
        level_metadata = CompiledUniverse.LevelMetadata(
            level_name=level_name,
            curriculum=level.curriculum,
            training=level.training,
            observation_spec=optimized.observation_spec,
            action_metadata=optimized.action_metadata
        )
        all_levels_metadata[level_name] = level_metadata
        logger.info(f"✓ Compiled {level_name}")

    # Select primary level metadata
    primary_metadata = all_levels_metadata[primary_level]

    # Stage 7: Emit single CompiledUniverse with all levels
    logger.info("=== Stage 7: Emitting CompiledUniverse ===")
    compiled = CompiledUniverse(
        # Primary level fields (for backwards compat)
        observation_spec=primary_metadata.observation_spec,
        action_metadata=primary_metadata.action_metadata,
        # ... other primary fields from optimized state

        # Multi-level support
        experiment_dir=experiment_dir,
        all_levels=all_levels_metadata
    )
```

---

## Issue #6: Field Mapping Document - Phase 4, Task 3

**File**: `2025-11-16-v2.1-phase4-native-compiler.md`
**Location**: Around line 404-440

**FIX**: Already covered in Issue #1

---

## Issue #11: Test Import Paths - Phase 6, Task 4

**File**: `2025-11-16-v2.1-phase6-test-migration.md`
**Location**: Line 379+ (test imports)

**WRONG**:
```python
from townlet.config.experiment import ExperimentConfig  # ❌
from townlet.config.stratum import StratumConfig        # ❌
```

**CORRECT**:
```python
from townlet.config.experiment_config import ExperimentConfig  # ✅
from townlet.config.stratum_config import StratumConfig        # ✅
```

---

## Issue #13: Vocabulary Validation Field Access - Phase 4, Task 2

**File**: `2025-11-16-v2.1-phase4-native-compiler.md`
**Location**: Vocabulary validation code (if exists in wrong form)

**This appears to be CORRECT in current plan** (lines 202-203 show proper nesting)

**Verify no other instances exist with wrong pattern**

---

## Execution Plan for Fixes

1. **Phase 1 Plan** (5 min):
   - Fix Task 8-10 descriptions (file names)
   - Fix Task 11 imports (module names)

2. **Phase 4 Plan** (20 min):
   - Fix Task 3 field mapping doc
   - Fix Task 6 compile() signature (level_name → primary_level)
   - Add multi-level compilation loop to Task 6
   - Verify all field access patterns

3. **Phase 6 Plan** (5 min):
   - Fix test import paths
   - Fix primary_level references

4. **Phase 7 Plan** (3 min):
   - Fix primary_level in examples

**Total Estimated Time**: 33 minutes

---

## Validation Checklist

After fixes, verify:
- [ ] All field access uses section-root pattern (double/triple nesting)
- [ ] All imports use `_config` suffix (experiment_config not experiment)
- [ ] All curriculum DTOs use V2 suffix (BarsV2Config not BarsConfig)
- [ ] All compile() signatures use `primary_level` not `level_name`
- [ ] Phase 4 compile() populates `all_levels` field
- [ ] All test files import from correct paths

---

**Status**: Document created, fixes to be applied next
