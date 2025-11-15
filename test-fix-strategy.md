# Test Fix Strategy - Config v2.1 Migration

**Baseline**: 367 failed, 1564 passed, 46 skipped, 391 errors (Total: 2368 tests)

## Failure Categories

### Category 1: Config Path References (HIGHEST PRIORITY)
**Error Pattern**: `Config file not found: configs/L0_0_minimal/training.yaml`
**Root Cause**: Tests trying to load individual YAML files instead of using compiler
**Estimated Count**: ~200-250 failures
**Fix Pattern**:
```python
# OLD (broken)
config = HamletConfig.from_directory("configs/L0_0_minimal")

# NEW (correct)
from townlet.universe.compiler import compile
universe = compile(Path("configs/default_curriculum"))
config = universe.config
```

**Files to Update**:
- `tests/test_townlet/integration/config/test_hamlet_config_dto.py`
- `tests/test_townlet/integration/test_*.py` (all integration tests)
- `tests/test_townlet/unit/universe/*.py`

### Category 2: Deleted Config Pack References
**Error Pattern**: Tests referencing L1_3D_house, L1_continuous_*, etc.
**Root Cause**: Tests parameterized over deleted config packs
**Estimated Count**: ~50-75 failures
**Fix Pattern**:
```python
# OLD
@pytest.mark.parametrize("pack", [
    "L0_0_minimal", "L1_3D_house", "L1_continuous_1D"  # DELETED
])

# NEW
@pytest.mark.parametrize("pack", [
    "L0_0_minimal", "L0_5_dual_resource", "L1_full_observability"
])
```

**Valid Config Packs** (v2.1):
- L0_0_minimal
- L0_5_dual_resource
- L1_full_observability
- L2_partial_observability
- L3_temporal_mechanics

### Category 3: Fixture Updates
**Error Pattern**: Fixtures creating temp configs without v2.1 structure
**Root Cause**: Fixtures still creating flat config directories
**Estimated Count**: ~30-50 failures
**Fix Pattern**:
```python
# OLD
temp_dir / "training.yaml"
temp_dir / "bars.yaml"

# NEW
temp_dir / "training" / "default.yaml"
temp_dir / "bars" / "default.yaml"
```

**Files to Update**:
- `tests/test_townlet/unit/config/fixtures.py`
- All test files using `temp_config_*` fixtures

### Category 4: HamletConfig vs CompiledUniverseV21
**Error Pattern**: Tests expecting `HamletConfig` object
**Root Cause**: Compiler returns `CompiledUniverseV21`, not `HamletConfig`
**Estimated Count**: ~40-60 failures
**Fix Pattern**:
```python
# OLD
assert isinstance(result, HamletConfig)

# NEW
assert isinstance(result, CompiledUniverseV21)
config = result.config  # Get HamletConfig
```

### Category 5: Observation Spec Changes
**Error Pattern**: Tests checking observation_dim directly
**Root Cause**: observation_dim now in observation_spec
**Estimated Count**: ~20-30 failures
**Fix Pattern**:
```python
# OLD
assert config.environment.observation_dim == 29

# NEW
assert universe.observation_spec.total_dims == 29
```

### Category 6: Temporary Test Config Creation
**Error Pattern**: `FileNotFoundError: /tmp/.../training.yaml`
**Root Cause**: Tests creating incomplete config packs
**Estimated Count**: ~10-20 failures
**Fix Pattern**: Create full v2.1 directory structure in temp dirs

## Fix Order (By Task)

### Task 5.2: Fix config path references
1. Update `tests/test_townlet/unit/config/fixtures.py` first
2. Remove deleted pack references from all `@pytest.mark.parametrize`
3. Update pack lists to v2.1 valid packs

### Task 5.3: Fix compiler tests
1. Update `tests/test_townlet/unit/universe/test_compiler.py`
2. Update stage tests (test_stage1_parse.py through test_stage7_emit.py)
3. Fix observation spec tests

### Task 5.4: Fix integration tests
1. Update `test_hamlet_config_dto.py` (highest impact)
2. Update environment integration tests
3. Update checkpoint/runner tests

### Task 5.5: Fix remaining failures
1. Batch by category (path refs, fixtures, etc.)
2. Commit after each category
3. Document any tests that need deeper refactoring

## Expected Outcomes

- **After Task 5.2**: ~75% of errors resolved (path/pack issues)
- **After Task 5.3**: ~85% of errors resolved (compiler tests)
- **After Task 5.4**: ~95% of errors resolved (integration tests)
- **After Task 5.5**: >98% pass rate

## Tests That May Need Skip/Rewrite

Some tests may be testing v2.0 internals that no longer exist:
- Tests for individual YAML validation (now compiler's job)
- Tests for HamletConfig.from_directory() (deleted method)
- Tests for config composition logic (now in compiler)

**Strategy**: Skip with clear comment linking to this document, mark as "TODO: rewrite for v2.1"
