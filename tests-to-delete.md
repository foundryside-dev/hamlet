# Tests to Delete (v2.1 Migration)

## Executive Summary

**Total Test Files Affected**: 19 files
**Estimated Lines to Delete**: ~313 lines (CORRECTED - see test-audit-corrections.md for details)
**Reason**: Testing deleted v1.0 flat config functionality that doesn't exist in v2.1

### Breakdown (CORRECTED):
- **DELETE Entirely**: 1 test file (313 lines) - HamletConfig.load() tests only
- **DELETE Tests Within Files**: 0 tests - ALL moved to UPDATE after false positive review
- **UPDATE**: Tests using valid v2.1 functionality but with wrong paths or deleted config data

### Correction Note:
Original audit incorrectly categorized tests that use deleted config files as test data as "tests to delete".
After review, these tests are actually testing valid functionality (continuous substrates, Grid3D, training pipelines)
and should be UPDATED to create substrates programmatically or use v2.1 config paths.
See `/home/john/hamlet/test-audit-corrections.md` for detailed analysis of false positives.

---

## Category 1: Deleted Entire Test File (MUST DELETE)

### 1.1 HamletConfig.load() Tests (Already Marked Skip)
- [ ] **tests/test_townlet/integration/config/test_hamlet_config_dto.py** (313 lines)
  - **Reason**: Tests `HamletConfig.load()` method which was deleted in v2.1
  - **Status**: Already marked `pytestmark = pytest.mark.skip`
  - **Action**: DELETE entire file
  - **Evidence**: File header says "TODO: Rewrite tests to verify compiler output instead of HamletConfig.load()."
  - **Classes**:
    - `TestHamletConfigComposition` (13 tests)
    - `TestHamletConfigCrossValidation` (2 tests)
    - `TestHamletConfigProductionPacks` (4 tests)
    - `TestHamletConfigErrorMessages` (2 tests)
    - `TestRawConfigsIntegration` (1 test)

---

## Category 2: Tests Using Deleted Config Packs (UPDATE to Create Programmatically)

### 2.1 L1_3D_house (Config deleted, but Grid3D substrate functionality is VALID)
- [ ] **tests/test_townlet/integration/test_substrate_migration.py::test_training_with_grid3d_substrate**
  - Line 11-33: Tests Grid3D substrate training (VALID FUNCTIONALITY)
  - Uses `configs/L1_3D_house` as test data (deleted)
  - Action: UPDATE to create Grid3DSubstrate programmatically (pattern exists at line 133-163)
  - **WHY UPDATE**: Testing substrate migration mechanics, not the config itself

- [ ] **tests/test_townlet/unit/environment/test_pomdp_validation.py** (multiple tests)
  - Lines referencing `configs/L1_3D_house`:
    - Uses as source for creating temp Grid3D configs
  - Action: UPDATE to use `configs/default_curriculum/levels/L1_full_observability` and modify substrate

- [ ] **tests/test_townlet/unit/environment/test_gridnd_action_support.py::test_gridnd_substrate_action_vocabulary**
  - Uses `configs/L1_3D_house` as source
  - Action: UPDATE to create Grid4D from scratch or use L1 as base

### 2.2 L1_continuous_1D/2D/3D (Configs deleted, but Continuous substrate functionality is VALID)
- [ ] **tests/test_townlet/integration/test_substrate_migration.py::test_training_with_continuous1d_substrate**
  - Lines 35-60: Tests Continuous1D substrate training (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_1D` as test data (deleted)
  - Action: UPDATE to create Continuous1DSubstrate programmatically (pattern exists at line 133-163)
  - **WHY UPDATE**: Testing continuous substrate integration, not the config itself

- [ ] **tests/test_townlet/integration/test_substrate_migration.py::test_training_with_continuous2d_substrate**
  - Lines 62-95: Tests Continuous2D substrate training (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_2D` as test data (deleted)
  - Action: UPDATE to create Continuous2DSubstrate programmatically
  - **WHY UPDATE**: Testing continuous substrate integration, not the config itself

- [ ] **tests/test_townlet/integration/test_substrate_migration.py::test_training_with_continuous3d_substrate**
  - Lines 97-131: Tests Continuous3D substrate training (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_3D` as test data (deleted)
  - Action: UPDATE to create Continuous3DSubstrate programmatically
  - **WHY UPDATE**: Testing continuous substrate integration, not the config itself

- [ ] **tests/test_townlet/integration/test_substrate_migration.py::test_continuous_proximity_interaction**
  - Lines 133-163: Valid test that creates substrate directly
  - Action: KEEP (already uses programmatic creation - this is the pattern to follow!)

- [ ] **tests/test_townlet/unit/substrate/test_continuous.py::TestContinuousConfiguration::test_config_1d**
  - Lines 523-540: Tests Continuous1DSubstrate mechanics (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_1D/substrate.yaml` as test data (deleted)
  - Action: UPDATE to create substrate programmatically (lines 17-522 already do this!)
  - **WHY UPDATE**: Testing substrate functionality, not config structure

- [ ] **tests/test_townlet/unit/substrate/test_continuous.py::TestContinuousConfiguration::test_config_2d**
  - Lines 541-558: Tests Continuous2DSubstrate mechanics (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_2D/substrate.yaml` as test data (deleted)
  - Action: UPDATE to create substrate programmatically
  - **WHY UPDATE**: Testing substrate functionality, not config structure

- [ ] **tests/test_townlet/unit/substrate/test_continuous.py::TestContinuousConfiguration::test_config_3d**
  - Lines 559-576: Tests Continuous3DSubstrate mechanics (VALID FUNCTIONALITY)
  - Uses `configs/L1_continuous_3D/substrate.yaml` as test data (deleted)
  - Action: UPDATE to create substrate programmatically
  - **WHY UPDATE**: Testing substrate functionality, not config structure

- [ ] **tests/test_townlet/unit/environment/test_vectorized_env.py** (reference to L1_continuous_2D)
  - Search for "L1_continuous_2D" - one reference
  - Action: UPDATE to create continuous substrate from scratch or DELETE test

- [ ] **tests/test_townlet/unit/environment/test_action_space.py** (references to continuous configs)
  - References to `configs/L1_continuous_1D` in test data
  - Action: UPDATE to create continuous substrate from scratch or DELETE tests

- [ ] **tests/test_townlet/_fixtures/environment.py** (fixture definitions)
  - Lines referencing `configs/L1_continuous_1D` and `configs/L1_continuous_3D`
  - Action: UPDATE fixtures to create continuous substrates programmatically or DELETE fixtures

### 2.3 aspatial_test (DELETED - not in v2.1)
- [ ] **tests/test_townlet/integration/test_env_substrate.py::ASPARTIAL_CONFIG**
  - Line 9: `ASPARTIAL_CONFIG = Path("configs/aspatial_test")`
  - Action: DELETE tests using this config or UPDATE to create aspatial programmatically

- [ ] **tests/test_townlet/unit/environment/test_action_space.py** (aspatial_test reference)
  - Reference to `configs/aspatial_test`
  - Action: UPDATE or DELETE

- [ ] **tests/test_townlet/unit/environment/test_checkpoint_validation.py** (aspatial_test reference)
  - Reference to `configs/aspatial_test`
  - Action: UPDATE or DELETE

- [ ] **tests/test_townlet/_fixtures/environment.py::aspatial_env** fixture
  - Uses `configs/aspatial_test`
  - Action: UPDATE to create aspatial substrate programmatically or DELETE fixture

### 2.4 configs/test (DELETED - replaced by default_curriculum structure)
- [ ] **tests/test_townlet/slow/test_training_levels.py** (all tests)
  - All tests reference `configs/test/training_level_*.yaml` (deleted)
  - Tests validate TRAINING PIPELINE MECHANICS (VALID FUNCTIONALITY):
    - Load configuration, Initialize environment/population, Run training, Save/load checkpoints, Verify learning progress
  - Action: UPDATE to use `configs/default_curriculum/levels/L0_0_minimal`, `L1_full_observability`, etc.
  - **WHY UPDATE**: Testing end-to-end training pipeline, not config structure. Function `run_training_pipeline()` is generic and just needs valid config paths.

- [ ] **tests/test_townlet/properties/test_environment_properties.py** (configs/test references)
  - Multiple references to `Path("configs/test")`
  - Action: UPDATE to use `configs/default_curriculum/levels/L0_0_minimal` or similar

- [ ] **tests/test_townlet/integration/test_action_costs.py** (configs/test references)
  - Comments referencing `configs/test/bars.yaml`
  - Action: UPDATE to use actual v2.1 config pack

- [ ] **tests/test_townlet/integration/test_live_inference_metadata.py**
  - Line: `TEST_CONFIG_DIR = Path("configs/test")`
  - Action: UPDATE to use v2.1 config path

- [ ] **tests/test_townlet/integration/test_topology_metadata.py**
  - Line: `TEST_CONFIG_DIR = Path("configs/test")`
  - Action: UPDATE to use v2.1 config path

- [ ] **tests/test_townlet/unit/test_configuration.py** (configs/test references)
  - Multiple references to `configs/test`
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/unit/environment/test_observations.py** (configs/test reference)
  - Comment: "configs/test has 2D position"
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/unit/environment/test_affordance_engine.py** (configs/test reference)
  - Comment: "Default uses configs/test/ directory"
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/unit/environment/test_action_space.py** (configs/test reference)
  - Reference to `Path("configs/test")`
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/unit/environment/test_vectorized_env.py** (configs/test reference)
  - Uses `Path("configs/test")`
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/unit/environment/test_checkpoint_validation.py** (configs/test reference)
  - Uses `Path("configs/test")`
  - Action: UPDATE to use v2.1 config pack

- [ ] **tests/test_townlet/special/test_task002a_migration_errors.py** (configs/test reference)
  - Uses `Path("configs/test")`
  - Action: UPDATE to use v2.1 config pack

---

## Category 3: Tests Using Old Flat Config Paths (UPDATE to v2.1)

These tests are testing VALID functionality but using the old flat path structure.

### 3.1 Update Path References (configs/L* → configs/default_curriculum/levels/L*)

**Pattern**: Tests using `configs/L0_0_minimal`, `configs/L1_full_observability`, etc. should use new paths.

**Files to Update** (46+ references):
- tests/test_townlet/properties/test_environment_properties.py
- tests/test_townlet/integration/test_custom_actions.py
- tests/test_townlet/integration/test_recording_recorder.py
- tests/test_townlet/integration/test_preflight_validation.py
- tests/test_townlet/integration/test_temporal_mechanics.py
- tests/test_townlet/integration/test_recurrent_networks.py
- tests/test_townlet/integration/test_curriculum_transfer.py
- tests/test_townlet/integration/test_data_flows.py
- tests/test_townlet/integration/test_substrate_observations.py
- tests/test_townlet/integration/test_episode_execution.py
- tests/test_townlet/unit/training/test_checkpoint_utils.py
- tests/test_townlet/unit/agent/test_structured_qnetwork.py
- tests/test_townlet/unit/agent/test_network_selection.py
- tests/test_townlet/unit/population/test_double_dqn_algorithm.py
- tests/test_townlet/unit/exploration/test_rnd_masking.py
- tests/test_townlet/unit/substrate/test_grid2d.py
- tests/test_townlet/unit/universe/test_dac_compiler_validation.py (13 tests)
- tests/test_townlet/unit/universe/test_stage4_cross_validate.py
- tests/test_townlet/unit/universe/test_cues_compiler.py
- tests/test_townlet/unit/universe/test_vision_range_no_defaults.py
- tests/test_townlet/unit/universe/test_stage2_symbol_table.py
- tests/test_townlet/unit/universe/test_compiled_universe_activity.py
- tests/test_townlet/unit/universe/test_compiled_universe_comprehensive.py
- tests/test_townlet/unit/universe/test_stage3_resolve.py
- tests/test_townlet/unit/universe/test_raw_configs.py
- tests/test_townlet/unit/universe/test_stage6_optimize.py
- tests/test_townlet/unit/universe/test_partial_obs_curriculum_masking.py
- tests/test_townlet/unit/universe/test_metadata_serialization.py
- tests/test_townlet/unit/universe/test_capability_validation.py (8 tests)
- tests/test_townlet/unit/universe/test_grid_feasibility.py
- tests/test_townlet/unit/universe/test_stage5_metadata.py
- tests/test_townlet/unit/universe/test_compiled_universe.py (9 tests)
- tests/test_townlet/unit/universe/test_raw_configs_properties.py

**Action for ALL above**: Global find/replace:
```
configs/L0_0_minimal → configs/default_curriculum/levels/L0_0_minimal
configs/L0_5_dual_resource → configs/default_curriculum/levels/L0_5_dual_resource
configs/L1_full_observability → configs/default_curriculum/levels/L1_full_observability
configs/L2_partial_observability → configs/default_curriculum/levels/L2_partial_observability
configs/L3_temporal_mechanics → configs/default_curriculum/levels/L3_temporal_mechanics
```

---

## Category 4: Tests Using RawConfigs.from_config_dir (UPDATE)

These tests use the v1.0 loading API but test valid v2.1 functionality.

**Files** (8 references):
- tests/test_townlet/unit/universe/test_stage4_cross_validate.py
- tests/test_townlet/unit/universe/test_cues_compiler.py
- tests/test_townlet/unit/universe/test_stage2_symbol_table.py
- tests/test_townlet/unit/universe/test_grid_feasibility.py
- tests/test_townlet/unit/universe/test_stage3_resolve.py
- tests/test_townlet/unit/universe/test_raw_configs.py
- tests/test_townlet/unit/universe/test_raw_configs_properties.py
- tests/test_townlet/integration/config/test_hamlet_config_dto.py (SKIP - already in DELETE category)

**Action**: These tests are valid - they test RawConfigs which is the v2.1 Stage 1 output. Just update paths.

---

## Category 5: Tests Using Individual YAML Loading (REVIEW)

Tests that load individual `substrate.yaml`, `bars.yaml`, `training.yaml` files directly.

**Status**: Most of these are VALID - they're testing individual DTO loaders, not the old flat config structure.

**Files to Review** (but likely KEEP):
- tests/test_townlet/unit/config/test_bar_config_dto.py (valid - tests BarConfig DTO)
- tests/test_townlet/unit/config/test_training_config_dto.py (valid - tests TrainingConfig DTO)
- tests/test_townlet/unit/substrate/test_config.py (valid - tests substrate config loading)

**Action**: KEEP these - they test individual config file parsing which is still valid in v2.1.

---

## Summary Statistics (CORRECTED)

### Files by Action:

**DELETE Entirely**: 1 file
- test_hamlet_config_dto.py (313 lines) - Tests deleted HamletConfig.load() method

**DELETE Specific Tests**: 0 test methods
- **CORRECTED**: All previous DELETE candidates moved to UPDATE category
- **Reason**: They test valid functionality, just use deleted configs as test data

**UPDATE to Create Substrates Programmatically**: 2 files, 7 test methods (~174 lines)
- test_substrate_migration.py (4 tests: Grid3D + Continuous 1D/2D/3D)
- test_continuous.py (3 tests: test_config_1d/2d/3d)
- **Pattern**: Create substrates directly instead of loading from deleted config files

**UPDATE Config Paths**: 1 file needs special attention
- test_training_levels.py (~200+ lines) - Update to use v2.1 curriculum level paths

**UPDATE Paths Only**: 46+ files
- Simple find/replace: `configs/L*` → `configs/default_curriculum/levels/L*`
- Simple find/replace: `configs/test` → `configs/default_curriculum/levels/L0_0_minimal` (or appropriate level)

**KEEP (No Changes)**: Individual DTO tests are valid

### Estimated Changes (CORRECTED):

- **Lines to DELETE**: 313 lines (test_hamlet_config_dto.py only)
- **Lines to UPDATE (Programmatic Creation)**: ~174 lines (7 test methods in 2 files)
- **Lines to UPDATE (Path Changes)**: ~200+ references to old paths (simple find/replace)
- **Net Reduction**: Original estimate was 700-1000 lines deleted, corrected to 313 lines deleted + ~374 lines updated

---

## Top 5 Files Needing Most Work (CORRECTED)

1. **tests/test_townlet/integration/config/test_hamlet_config_dto.py** - DELETE ENTIRE FILE (313 lines)
2. **tests/test_townlet/slow/test_training_levels.py** - UPDATE config paths (200+ lines affected)
3. **tests/test_townlet/integration/test_substrate_migration.py** - UPDATE 4 tests to create substrates programmatically (~120 lines)
4. **tests/test_townlet/unit/substrate/test_continuous.py** - UPDATE 3 tests to create substrates programmatically (~54 lines)
5. **tests/test_townlet/_fixtures/environment.py** - UPDATE fixtures (continuous/aspatial) (~50 lines affected)

---

## Action Plan (CORRECTED)

### Phase 1: Safe Deletions (Immediate)
1. ✅ Delete `test_hamlet_config_dto.py` (already skipped, 313 lines)
   - Only file that should be fully deleted

### Phase 2: Path Updates (Bulk Operation)
1. Global find/replace for all `configs/L*` → `configs/default_curriculum/levels/L*`
2. Global find/replace for `configs/test` → `configs/default_curriculum/levels/L0_0_minimal` (or appropriate level)
3. Verify all tests pass after path updates

### Phase 3: Programmatic Substrate Creation (Careful)
1. Update `test_substrate_migration.py`:
   - 4 tests: Create Grid3D, Continuous1D, Continuous2D, Continuous3D programmatically
   - Pattern already exists in same file (line 133-163)
2. Update `test_continuous.py`:
   - 3 tests: Create Continuous1D/2D/3DSubstrate programmatically
   - Pattern already exists in same file (lines 17-522)
3. Update fixtures in `_fixtures/environment.py` to create substrates programmatically

### Phase 4: Training Levels Migration
1. Update `test_training_levels.py` to use v2.1 curriculum levels
2. Map old configs to new:
   - `configs/test/training_level_1*.yaml` → `configs/default_curriculum/levels/L1_full_observability`
   - `configs/test/training_level_2*.yaml` → `configs/default_curriculum/levels/L2_partial_observability`
   - `configs/test/training_level_3*.yaml` → `configs/default_curriculum/levels/L3_temporal_mechanics`

### Phase 5: Verification
1. Run full test suite
2. Remove any remaining skip marks for tests that now work
3. Document what was changed in migration notes

---

## Notes (CORRECTED)

**What Actually Needs to Be Deleted**:
- ✅ `test_hamlet_config_dto.py` - Tests the deleted `HamletConfig.load()` API
- **ONLY 313 LINES** of actual test deletion needed

**What Should Be Updated (Not Deleted)**:
- Tests using deleted config packs (L1_3D_house, continuous variants, configs/test) as test data
- These tests validate VALID functionality (substrates, training pipeline, etc.)
- Fix by creating substrates programmatically or using v2.1 config paths

**Key Insight from Corrections**:
- **Config files as test data ≠ config-specific tests**
- A test loading `configs/L1_continuous_3D/substrate.yaml` is NOT testing the config itself
- It's testing substrate mechanics and using the config file for convenience
- Fix: Create the substrate directly instead of loading from deleted config

**Pre-Release Principle Still Applies**:
> "NO backwards compatibility arrangements - Delete old code paths immediately"

The principle applies to **code paths** (HamletConfig.load), not to **test data sources**.
We're not maintaining backwards compatibility - we're fixing tests to use v2.1 patterns.

**Original Audit Error**:
- Conflated "uses deleted config" with "tests deleted config"
- Would have deleted ~400-700 lines of valid test coverage
- Corrected to DELETE 313 lines, UPDATE ~374 lines
