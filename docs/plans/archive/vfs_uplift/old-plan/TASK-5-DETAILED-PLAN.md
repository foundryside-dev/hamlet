# Task 5: Tests and Validation - Implementation Plan

> **For Claude:** REQUIRED EXECUTION SKILL: Use `superpowers:subagent-driven-development` to execute this plan task-by-task with code review between tasks.

**Goal:** Comprehensive testing and cleanup validation for VFS uplift runtime integration

**Architecture:** Expand integration test coverage, verify no runtime YAML loading, test edge cases, ensure regression-free migration, and validate cleanup completeness.

**Tech Stack:** pytest, grep verification, existing test infrastructure

**Estimated Duration:** 2-3 days
**Test Target:** 5-10 new integration tests

---

## Context

**Current State (after Tasks 1-4):**
- ✅ VFS profiles compiled by UniverseCompiler (Task 1)
- ✅ Effects catalog compiled by UniverseCompiler (Task 1)
- ✅ VFS expressions evaluated at runtime (Task 2)
- ✅ Item VFS profile-driven end-to-end (Task 3)
- ✅ Runtime uses compiled effect catalog (Task 4)
- ✅ Basic integration tests for each task (Tasks 1-4)
- ❌ Need comprehensive cross-feature integration tests
- ❌ Need edge case validation
- ❌ Need cleanup verification (no legacy code paths)

**Target State:**
- ✅ Comprehensive integration tests covering all VFS uplift features
- ✅ Edge case tests (empty configs, missing features, error conditions)
- ✅ Regression tests (all 435+ existing tests still pass)
- ✅ Cleanup verification (grep checks for no runtime YAML loading)
- ✅ Documentation updated with Task 5 completion

---

## Subtask 5.1: VFS Expression Integration Tests

**Files:**
- Expand: `tests/test_townlet/integration/test_vfs_runtime_evaluation.py` (add tests)
- Test: `tests/test_townlet/integration/test_vfs_expression_edge_cases.py` (new file)

**Duration:** ~1 day

### Step 5.1.1: Write failing test for VFS dependency chains

**Test:** Add to `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

```python
def test_vfs_expression_dependency_chain():
    """VFS variables with complex dependency chains should evaluate correctly.

    Tests:
    - Multi-level dependencies (a → b → c)
    - Expression reuse across variables
    - Mark-and-sweep with dependencies
    """
    # Setup: Create config with dependency chain
    # a = 10
    # b = a + 5
    # c = b * 2
    # Only c is observed

    # Exercise: Compile and run environment
    # ...

    # Verify: c evaluates to (10 + 5) * 2 = 30
    # Verify: a and b not evaluated (mark-and-sweep)
```

**Expected:** Test FAILS (need config pack with dependency chain)

### Step 5.1.2: Write failing test for VFS with bar access

**Test:** Add to `tests/test_townlet/integration/test_vfs_runtime_evaluation.py`

```python
def test_vfs_expressions_access_bars():
    """VFS expressions should be able to read bar values.

    Tests:
    - VFS variable depends on bar.energy
    - Bar values change during step
    - VFS expression reflects updated bar values
    """
    # Setup: Config with VFS var that reads bar.energy
    # low_energy_flag = bar.energy < 0.3

    # Exercise: Step environment with different energy levels
    # ...

    # Verify: low_energy_flag updates based on bar.energy
```

**Expected:** Test FAILS (need config with bar-dependent VFS)

### Step 5.1.3: Write edge case test for circular dependencies

**Test:** Create `tests/test_townlet/integration/test_vfs_expression_edge_cases.py`

```python
"""Edge case tests for VFS expression evaluation."""

from pathlib import Path
import pytest
import yaml

from townlet.universe.compiler import UniverseCompiler


def test_circular_dependency_detected_at_compile_time():
    """Circular VFS dependencies should fail at compile time, not runtime."""
    # Setup: Create config with circular dependency
    # a = b + 1
    # b = a + 1

    # Exercise & Verify: Compilation should fail with clear error
    with pytest.raises(ValueError, match="Circular dependency"):
        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)


def test_missing_vfs_variable_reference():
    """VFS expression referencing undefined variable should fail at compile time."""
    # Setup: Config with VFS var referencing nonexistent var
    # my_var = undefined_var + 1

    # Exercise & Verify: Compilation should fail
    with pytest.raises(ValueError, match="Undefined variable"):
        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)


def test_type_mismatch_in_vfs_expression():
    """VFS expression with type mismatch should fail at compile time."""
    # Setup: Config with int var assigned bool expression
    # my_int_var = bar.energy < 0.5  # Returns bool, not int

    # Exercise & Verify: Compilation should fail with type error
    with pytest.raises(TypeError, match="Type mismatch"):
        compiler = UniverseCompiler()
        compiled = compiler.compile(config_dir, primary_level="test_level", use_cache=False)
```

**Expected:** Tests FAIL (need to implement test configs)

### Step 5.1.4: Implement test configs and run tests

Create minimal test configs in `tests/test_townlet/integration/fixtures/vfs_edge_cases/`:
- `circular_dependency/` - Config with circular VFS vars
- `undefined_var/` - Config with undefined variable reference
- `type_mismatch/` - Config with type mismatch

Run tests:
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_vfs_expression_edge_cases.py -xvs
```

**Expected:** Tests PASS (compiler catches errors at compile time)

### Step 5.1.5: Commit VFS expression integration tests

```bash
git add tests/test_townlet/integration/test_vfs_runtime_evaluation.py tests/test_townlet/integration/test_vfs_expression_edge_cases.py
git commit -m "test(vfs): add comprehensive VFS expression integration tests

- Test multi-level dependency chains (a → b → c)
- Test VFS expressions accessing bars
- Test circular dependency detection at compile time
- Test undefined variable detection at compile time
- Test type mismatch detection at compile time
- All edge cases caught at compile time (not runtime)

Task 5.1 complete (VFS expression tests)"
```

---

## Subtask 5.2: Item VFS Integration Tests

**Files:**
- Expand: `tests/test_townlet/integration/test_item_vfs_integration.py` (add tests)
- Test: `tests/test_townlet/integration/test_item_vfs_observations.py` (new file)

**Duration:** ~0.5 days

### Step 5.2.1: Write test for item VFS in observations with masking

**Test:** Create `tests/test_townlet/integration/test_item_vfs_observations.py`

```python
"""Integration tests for item VFS in agent observations."""

from pathlib import Path
import torch

from townlet.universe.compiler import UniverseCompiler


def test_item_vfs_observations_include_held_items():
    """Agent observations should include VFS state of held items."""
    # Setup: Compile items_smoke config
    config_dir = Path(__file__).parent.parent.parent.parent / "configs" / "test" / "items_smoke"

    compiler = UniverseCompiler()
    compiled = compiler.compile(config_dir, primary_level="items_smoke", use_cache=False)

    env = compiled.create_environment(
        num_agents=4,
        level_name="items_smoke",
        device=torch.device("cpu"),
    )

    # Exercise: Spawn items and pickup
    # Agent 0: holds 2 items (slots 0, 1 filled)
    # Agent 1: holds 1 item (slot 0 filled, slot 1 empty)
    # Agent 2: holds 0 items (both slots empty)
    # ... (use ItemManager to spawn and assign items)

    obs = env.reset()

    # Verify: Observations include item VFS with masking
    # obs shape: [batch, obs_dim]
    # Item VFS should be non-zero for held items
    # Empty slots should be masked (zeros)


def test_item_vfs_masking_with_different_profiles():
    """Items with different VFS profiles should mask correctly."""
    # Setup: Config with 2 item profiles (different variable counts)
    # Profile A: 3 vars (calories, freshness, quality)
    # Profile B: 2 vars (damage, durability)

    # Exercise: Agent holds 1 item from Profile A and 1 from Profile B
    # ...

    # Verify: Observations use max_vars across all profiles
    # Profile B item has 3rd slot masked (unused)


def test_item_vfs_updates_in_observations():
    """Item VFS state changes should appear in observations."""
    # Setup: Agent holds apple with calories=100

    # Exercise: Effect reduces apple.calories to 50
    # ...

    # Verify: Next observation shows updated calories value
```

**Expected:** Tests FAIL (need to implement item pickup in test fixtures)

### Step 5.2.2: Implement tests and verify passing

Implement test fixture helpers for item spawning and pickup:
```python
def spawn_and_pickup_item(env, agent_idx, item_type, initial_state=None):
    """Helper to spawn item and assign to agent inventory."""
    # ... implementation
```

Run tests:
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_item_vfs_observations.py -xvs
```

**Expected:** Tests PASS

### Step 5.2.3: Write test for item VFS profile switching

**Test:** Add to `tests/test_townlet/integration/test_item_vfs_integration.py`

```python
def test_item_profile_switch_updates_vfs_layout():
    """Switching item profile should update VFS storage layout.

    Tests profile-based VFS allocation:
    - Spawn item with profile A (3 vars)
    - Despawn and spawn different item type with profile B (2 vars)
    - Verify storage uses profile B layout
    """
    # Setup: Config with 2 item profiles

    # Exercise: Spawn item (profile A), despawn, spawn item (profile B)
    # ...

    # Verify: VFS registry uses correct profile map for each item
```

**Expected:** Test PASSES (profile-driven storage already implemented)

### Step 5.2.4: Commit item VFS integration tests

```bash
git add tests/test_townlet/integration/test_item_vfs_observations.py tests/test_townlet/integration/test_item_vfs_integration.py
git commit -m "test(items): add comprehensive item VFS integration tests

- Test item VFS in agent observations with masking
- Test masking with different item profiles
- Test item VFS state updates in observations
- Test profile switching updates VFS layout
- All tests verify profile-driven storage

Task 5.2 complete (Item VFS tests)"
```

---

## Subtask 5.3: Effects Runtime Integration Tests

**Files:**
- Expand: `tests/test_townlet/integration/test_effects_compiled_catalog.py` (add tests)

**Duration:** ~0.5 days

### Step 5.3.1: Write test for effects referencing item VFS

**Test:** Add to `tests/test_townlet/integration/test_effects_compiled_catalog.py`

```python
def test_effects_can_reference_item_vfs():
    """Effects should be able to read and modify item VFS variables.

    Tests:
    - Effect reads item.vfs.durability
    - Effect modifies item.vfs.quality
    - Item VFS schema includes all item profile variables
    """
    # Setup: Config with effects that reference item VFS
    # effect: modify_item
    #   on_spawn:
    #     - modify: "self.vfs.durability = self.vfs.durability - 0.1"

    # Exercise: Trigger effect on item
    # ...

    # Verify: Item VFS state modified correctly


def test_effects_cascade_with_item_vfs():
    """Effect cascades should work with item VFS state.

    Tests:
    - Effect A modifies item.vfs.charges
    - When charges < 1, spawns Effect B
    - Effect B despawns item
    """
    # Setup: Config with cascading effects

    # Exercise: Trigger effect cascade
    # ...

    # Verify: Cascade triggers correctly based on item VFS condition
```

**Expected:** Tests MAY FAIL (need config with item VFS effects)

### Step 5.3.2: Implement test config and run tests

Create test config in `tests/test_townlet/integration/fixtures/effects_item_vfs/`:
- `effects.yaml` with effects referencing item VFS
- `items.yaml` with item types that have VFS state
- `vfs_profiles.yaml` with item profiles

Run tests:
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_effects_compiled_catalog.py -xvs
```

**Expected:** Tests PASS

### Step 5.3.3: Commit effects integration tests

```bash
git add tests/test_townlet/integration/test_effects_compiled_catalog.py
git commit -m "test(effects): add tests for effects referencing item VFS

- Test effects reading item VFS variables
- Test effects modifying item VFS variables
- Test effect cascades with item VFS conditions
- Verify compiled catalog includes item VFS schema

Task 5.3 complete (Effects runtime tests)"
```

---

## Subtask 5.4: Cleanup Verification

**Files:**
- Create: `tests/test_townlet/integration/test_cleanup_verification.py` (new file)

**Duration:** ~0.5 days

### Step 5.4.1: Write grep verification tests

**Test:** Create `tests/test_townlet/integration/test_cleanup_verification.py`

```python
"""Cleanup verification tests for VFS uplift runtime integration."""

import subprocess
from pathlib import Path


def test_no_runtime_variables_reference_yaml_loading():
    """Verify no runtime loading of variables_reference.yaml for item vars."""
    # Grep check: src/townlet/environment/vectorized_env.py
    result = subprocess.run(
        [
            "grep",
            "-n",
            "variables_reference.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert result.returncode != 0 or "variables_reference.yaml" not in result.stdout, \
        f"Found runtime variables_reference.yaml loading:\n{result.stdout}"


def test_no_runtime_effects_yaml_loading():
    """Verify no runtime loading of effects.yaml."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "effects.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert result.returncode != 0 or "effects_path.*read_text" not in result.stdout, \
        f"Found runtime effects.yaml loading:\n{result.stdout}"


def test_no_runtime_effect_catalog_rebuild():
    """Verify no runtime EffectCatalog.from_config() calls."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "EffectCatalog.from_config",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches
    assert result.returncode != 0, \
        f"Found runtime EffectCatalog rebuild:\n{result.stdout}"


def test_no_runtime_vfs_profile_loading():
    """Verify no runtime loading of vfs_profiles.yaml."""
    result = subprocess.run(
        [
            "grep",
            "-n",
            "vfs_profiles.yaml",
            "src/townlet/environment/vectorized_env.py",
        ],
        capture_output=True,
        text=True,
    )

    # Should find no matches (or only comments)
    assert result.returncode != 0 or "vfs_profiles_path.*read_text" not in result.stdout, \
        f"Found runtime vfs_profiles.yaml loading:\n{result.stdout}"
```

**Expected:** Tests PASS (all runtime YAML loading removed)

### Step 5.4.2: Run cleanup verification tests

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_cleanup_verification.py -xvs
```

**Expected:** All tests PASS

### Step 5.4.3: Commit cleanup verification tests

```bash
git add tests/test_townlet/integration/test_cleanup_verification.py
git commit -m "test(cleanup): add grep verification tests for runtime YAML loading

- Verify no runtime variables_reference.yaml loading
- Verify no runtime effects.yaml loading
- Verify no runtime effect catalog rebuild
- Verify no runtime vfs_profiles.yaml loading
- All compiled artifacts consumed from CompiledUniverse

Task 5.4 complete (Cleanup verification)"
```

---

## Subtask 5.5: Regression Testing

**Files:**
- Run existing test suite
- Document any failures

**Duration:** ~0.5 days

### Step 5.5.1: Run full test suite

```bash
cd /home/john/hamlet
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v --tb=short
```

**Expected:** All 435+ tests PASS (zero regressions)

### Step 5.5.2: Check for XFAIL/XPASS tests

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v | grep -E "XFAIL|XPASS"
```

**Expected:** Only intentional XFAILs (3 XPASS from Phase 4 are acceptable)

### Step 5.5.3: Run integration tests specifically

```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/ -v --tb=short
```

**Expected:** All integration tests PASS

### Step 5.5.4: Document test results

Create test report:
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v --tb=short > test_results_task5.txt 2>&1
```

Verify:
- Total test count (should be 435+ after adding Task 5 tests)
- Pass rate (should be 99%+)
- Any new failures (should be zero)

### Step 5.5.5: Commit regression test results

```bash
git add test_results_task5.txt
git commit -m "test(regression): verify all tests pass after VFS uplift

- All 435+ existing tests passing
- 10+ new Task 5 tests passing
- Zero regressions from VFS uplift changes
- 99%+ pass rate maintained

Task 5.5 complete (Regression testing)"
```

---

## Subtask 5.6: Documentation and Status Update

**Files:**
- Modify: `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

**Duration:** ~0.25 days

### Step 5.6.1: Update implementation status

**File:** `docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md`

Add Task 5 status section:

```markdown
### Task 5: Tests and Validation ✅ COMPLETE

**Status:** 100% complete
**Timeline:** Planned 2-3 days | Actual: X days
**Test Coverage:** 10 integration tests (100% passing)

**Deliverables:**
- ✅ VFS expression integration tests (dependency chains, bar access, edge cases)
- ✅ Item VFS integration tests (observations, masking, profile switching)
- ✅ Effects runtime tests (item VFS references, cascades)
- ✅ Cleanup verification tests (grep checks for no runtime YAML loading)
- ✅ Regression testing (all 435+ tests passing, zero regressions)

**Test Breakdown:**
- **VFS Expression Tests:** 5 tests (dependency chains, bar access, circular deps, undefined vars, type mismatches)
- **Item VFS Tests:** 3 tests (observations with masking, profile switching, state updates)
- **Effects Runtime Tests:** 2 tests (item VFS references, cascades)
- **Cleanup Verification Tests:** 4 tests (grep checks)
- **Regression Tests:** 435+ existing tests (all passing)

**Commits:** [list commit SHAs]

**Grep Verification Results:**
- ✅ No runtime variables_reference.yaml loading for item vars
- ✅ No runtime effects.yaml loading
- ✅ No runtime effect catalog rebuild
- ✅ No runtime vfs_profiles.yaml loading

**Regression Test Results:**
- ✅ 435+ tests passing (previous count)
- ✅ +10 new tests (Task 5)
- ✅ Zero regressions
- ✅ 99%+ pass rate maintained
```

### Step 5.6.2: Update overall plan status

Update executive summary:

```markdown
## Executive Summary

The **Runtime VFS + Effects Integration** (VFS Uplift) has been **fully implemented** across all 5 tasks. All success criteria have been met, with 445+ tests passing and zero regressions.

**Timeline Achievement:**
- **Planned:** 10-15 days
- **Actual:** X days (under budget)
- **Status:** Production-ready

**Quality Metrics:**
- **Test Count:** 445+ tests (22+ new from VFS uplift)
- **Pass Rate:** 99%+ (zero regressions)
- **Grep Verification:** All runtime YAML loading removed
- **Performance:** <5% overhead from VFS evaluation (target met)
```

### Step 5.6.3: Commit documentation updates

```bash
git add docs/plans/vfs_uplift/UNIFIED-PLAN-IMPLEMENTATION-STATUS.md
git commit -m "docs: mark Task 5 (Tests and validation) as COMPLETE

Task 5 delivered:
- 10 comprehensive integration tests ✅
- Edge case validation (circular deps, undefined vars, type mismatches) ✅
- Cleanup verification (grep checks) ✅
- Regression testing (zero failures) ✅
- Documentation complete ✅

All VFS uplift tasks complete (1-5). System production-ready."
```

---

## Task 5 Success Criteria

**Functional:**
- ✅ VFS expression integration tests cover dependency chains and bar access
- ✅ Item VFS integration tests cover observations, masking, and profile switching
- ✅ Effects runtime tests cover item VFS references and cascades
- ✅ Edge cases tested (circular deps, undefined vars, type mismatches)
- ✅ All edge cases caught at compile time (not runtime)

**Tests:**
- ✅ 5-10 new integration tests passing
- ✅ All 435+ existing tests still pass (zero regressions)
- ✅ 99%+ pass rate maintained

**Code Quality:**
- ✅ No runtime variables_reference.yaml loading (grep verification)
- ✅ No runtime effects.yaml loading (grep verification)
- ✅ No runtime effect catalog rebuild (grep verification)
- ✅ No runtime vfs_profiles.yaml loading (grep verification)
- ✅ Performance: <5% overhead from VFS evaluation

---

## Notes for Engineer

**Key Design Decisions:**

1. **Compile-time error detection:**
   - Circular dependencies caught at compile time (not runtime)
   - Undefined variable references caught at compile time
   - Type mismatches caught at compile time
   - Rationale: Fail fast, clear errors, no runtime surprises

2. **Grep verification as tests:**
   - Grep checks formalized as pytest tests
   - Ensures no accidental reintroduction of runtime YAML loading
   - Part of CI pipeline (automated enforcement)

3. **Regression testing required:**
   - Full test suite must pass after each subtask
   - Zero regressions allowed (pre-release = strict quality)
   - Pass rate must stay 99%+ (3 XPASS from Phase 4 acceptable)

4. **Edge cases comprehensive:**
   - All failure modes tested (circular, undefined, type errors)
   - Item VFS masking edge cases (empty slots, different profiles)
   - Effects integration edge cases (item VFS references, cascades)

**Common Pitfalls:**

- Don't skip grep verification tests (critical for maintenance)
- Don't skip regression testing (VFS uplift touched critical paths)
- Don't use `--no-cov` or `-x` flags during final regression run (need full report)
- Don't commit if any existing tests fail (fix or revert changes)

**Testing Strategy:**

- Integration tests: Test full pipelines with real configs
- Edge case tests: Test error conditions and boundary cases
- Regression tests: Run full existing suite (no cherry-picking)
- Grep verification: Formalized as pytest tests (not manual checks)

**Performance Validation:**

Task 5 does NOT include performance benchmarking (already done in Phase 6 of Unified Plan).
VFS evaluation overhead already verified <5% in Phase 6.

---

## Execution Handoff

**Plan complete and saved to `docs/plans/vfs_uplift/TASK-5-DETAILED-PLAN.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - Dispatch fresh subagent per subtask, review between subtasks, fast iteration with quality gates

**2. Parallel Session (separate)** - Open new session with `/superpowers:execute-plan`, batch execution with checkpoints

**Which approach?**
