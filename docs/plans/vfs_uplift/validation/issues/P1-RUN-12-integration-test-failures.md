# P1-RUN-12: Integration Test Failures (4/5 VFS Runtime Tests)

**Priority:** P1 (Important - Should Fix)
**Category:** Runtime Integration
**Estimated Effort:** 1 day
**Status:** Open
**Created:** 2025-11-22

---

## Problem Description

4 out of 5 integration tests in `test_vfs_runtime_evaluation.py` are failing due to schema evolution mismatches between test fixtures and current VFS implementation.

**Failing Tests:**
1. `test_global_vfs_evaluation_at_runtime`
2. `test_agent_vfs_evaluation_with_expressions`
3. `test_vfs_dependency_ordering`
4. `test_item_vfs_runtime_updates`

**Passing Test:**
- `test_vfs_expression_evaluation_basic` ✅

**Impact:**
- Reduced confidence in VFS runtime evaluation
- CI may be failing (if these tests are run)
- Cannot verify VFS evaluation works correctly at runtime

**Evidence:**
- Agent 5 (Runtime Integration) report, section RUN-12
- Test file: `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

---

## Root Cause

Schema evolution since tests were written:

1. **VFS profile structure changed:** Tests use old YAML schema without `vfs_profiles.yaml`
2. **Expression syntax updated:** Some tests use deprecated expression format
3. **Observation field semantic types:** Missing `effects` in enum (separate issue)
4. **Dependency resolution:** Tests assume eager evaluation, but mark-and-sweep is now default

---

## How to Fix

### Step 1: Update Test Fixtures (4 hours)

**Create new test fixtures that match current schema:**

```bash
# Create test fixture directory
mkdir -p tests/fixtures/vfs_runtime_tests/

# Files needed:
tests/fixtures/vfs_runtime_tests/
├── vfs_profiles.yaml          # Experiment-level VFS profiles
├── substrate.yaml
├── bars.yaml
└── training.yaml
```

**Example `vfs_profiles.yaml`:**

```yaml
version: "2.1"

global_profile:
  time_of_day:
    expression: "(step % 24) / 24.0"
    observation: true

agent_profile:
  energy_efficiency:
    expression: "self.bar.energy / self.bar.max_energy"
    observation: true

item_profiles:
  sword:
    durability:
      initial_value: 1.0
      observation: true
```

### Step 2: Fix Test Logic (3 hours)

**File:** `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

Update each failing test:

```python
def test_global_vfs_evaluation_at_runtime():
    """Verify global VFS variables are evaluated every step."""
    config = HamletConfig.from_directory("tests/fixtures/vfs_runtime_tests")
    env = VectorizedHamletEnv(config, n_envs=1)

    # Step 1: Verify initial state
    obs, info = env.reset()
    initial_time = env.registry.global_vfs[0, 0]  # time_of_day
    assert initial_time == 0.0

    # Step 24: Verify time advanced
    for _ in range(24):
        obs, reward, done, truncated, info = env.step([0])  # WAIT action

    # time_of_day should cycle back to ~1.0
    time_after_24 = env.registry.global_vfs[0, 0]
    assert abs(time_after_24 - 1.0) < 0.05  # Allow small floating point error
```

### Step 3: Run and Verify (1 hour)

```bash
# Run just the VFS runtime tests
UV_CACHE_DIR=.uv-cache uv run pytest \
  tests/test_townlet/integration/test_vfs_runtime_evaluation.py \
  -v --tb=short

# Expected: 5/5 passing
```

### Step 4: Update Related Tests (2 hours)

Check if other integration tests have similar issues:

```bash
# Find tests using old VFS schema
grep -r "variables_reference.yaml" tests/test_townlet/integration/
```

Update any other tests found to use `vfs_profiles.yaml`.

---

## Detailed Fix for Each Test

### Test 1: `test_global_vfs_evaluation_at_runtime`
- **Issue:** Uses old `variables_reference.yaml` at level scope
- **Fix:** Create experiment-level `vfs_profiles.yaml` with `global_profile`

### Test 2: `test_agent_vfs_evaluation_with_expressions`
- **Issue:** Expression syntax changed (old: `bar.energy`, new: `self.bar.energy`)
- **Fix:** Update expression paths to include `self.` prefix

### Test 3: `test_vfs_dependency_ordering`
- **Issue:** Assumes eager evaluation, but topological sort changed
- **Fix:** Use mark-and-sweep mode or verify topological order is correct

### Test 4: `test_item_vfs_runtime_updates`
- **Issue:** Item VFS uses `vfs_profile` field, not inline variables
- **Fix:** Create item profile in `vfs_profiles.yaml`, reference by name

---

## Acceptance Criteria

- [ ] All 5 tests in `test_vfs_runtime_evaluation.py` pass
- [ ] Test fixtures use current schema (vfs_profiles.yaml at experiment level)
- [ ] Expression syntax matches current parser (self.*, target.*, etc.)
- [ ] Tests verify mark-and-sweep evaluation (not just eager)
- [ ] CI passing with these tests enabled

---

## Files to Modify

1. `tests/test_townlet/integration/test_vfs_runtime_evaluation.py` - Update test logic
2. `tests/fixtures/vfs_runtime_tests/vfs_profiles.yaml` (NEW) - Test fixture
3. `tests/fixtures/vfs_runtime_tests/substrate.yaml` (NEW) - Test fixture
4. `tests/fixtures/vfs_runtime_tests/bars.yaml` (NEW) - Test fixture

---

## Related Issues

- Related: P1-RUN-9 (checkpoint serialization)
- Blocking: None (tests are isolated)

---

## Notes

- These tests were written for Phase 1 VFS (variables_reference.yaml per level)
- Phase 2 VFS moved to experiment-level vfs_profiles.yaml with profiles
- Tests need migration to new schema, not a bug in the implementation
- Consider adding test for backward compatibility if needed
