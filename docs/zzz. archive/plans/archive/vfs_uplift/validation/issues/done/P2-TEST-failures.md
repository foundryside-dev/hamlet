# [TEST] Fix 4 Failing Tests

**Priority:** P2 (Minor)
**Category:** Testing
**Status:** PARTIAL
**Effort:** 2-3 hours

## Description

4 tests are currently failing (99.1% pass rate). While the failures are minor and don't block release, they should be fixed for clean test suite before production.

## Current State

**Test Status:**
- Total tests: 2,330
- Passing: 2,309 (99.1%)
- Failing: 4 (0.4%)
- Skipped: 17 (0.7%)

**Overall Impact:** LOW - All failures are edge cases or legacy API tests

## Failing Tests

### 1. **test_use_slot_action_executes_effects**
**File:** `tests/test_townlet/integration/test_items_effects_cascade.py`
**Issue:** Item effect application edge case
**Impact:** Low - Specific interaction between USE action and effect execution
**Root Cause:** TBD (needs investigation)
**Expected Fix Time:** 1-2 hours

**Investigation Steps:**
1. Read test to understand expected behavior
2. Check if USE action properly triggers effect pipeline
3. Verify effect executor receives correct context
4. Check for timing/ordering issues in effect application

### 2-4. **Custom Action Tests** (3 tests)
**Files:** Legacy custom action test files
**Issue:** Tests reference removed/renamed methods
**Impact:** Low - Tests for deprecated API
**Root Cause:** Custom actions refactored, tests not updated

**Failing Tests:**
- Test A: Legacy API method call
- Test B: Old parameter names
- Test C: Deprecated helper function

**Expected Fix Time:** 30-60 minutes

**Fix Options:**
1. **Update tests** to use new API (recommended if API still exists)
2. **Remove tests** if functionality deprecated and covered elsewhere
3. **Mark as skipped** with TODO if fix deferred to later

## Required Implementation

### Investigation Phase (30 minutes)

1. **Run failing tests individually:**
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/integration/test_items_effects_cascade.py::test_use_slot_action_executes_effects -v
UV_CACHE_DIR=.uv-cache uv run pytest tests/path/to/custom_action_test.py -v
```

2. **Analyze failure output:**
- Exception type and message
- Stack trace
- Expected vs actual values

3. **Categorize each failure:**
- Bug in implementation (needs code fix)
- Bug in test (needs test update)
- Deprecated test (safe to remove/skip)

### Fix Phase (1.5-2 hours)

#### For test_use_slot_action_executes_effects:

**If implementation bug:**
1. Fix bug in `src/townlet/items/action_handlers.py` or `src/townlet/effects/executor.py`
2. Verify test passes
3. Add regression test if needed

**If test bug:**
1. Update test expectations
2. Verify test logic matches current behavior
3. Add comments explaining edge case

#### For custom action tests:

**If API still exists:**
1. Update test imports
2. Update method calls to new API
3. Update assertions

**If API deprecated:**
1. Remove test
2. Verify functionality covered by other tests
3. Document removal in commit message

### Verification Phase (30 minutes)

```bash
# Run all tests to ensure no regressions
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -v --tb=short

# Verify 100% pass rate
UV_CACHE_DIR=.uv-cache uv run pytest tests/ -q | grep "passed"
```

## Acceptance Criteria

- [ ] All 4 failing tests resolved
- [ ] Test pass rate: 100% (or documented skips)
- [ ] No new test failures introduced
- [ ] Each fix documented in commit message
- [ ] If tests removed, verify coverage not reduced

## Evidence

**Source Report:** gap-report-testing-docs.md (TEST-1 section)
**Current Status:** 2,309 passing / 2,330 total (99.1% pass rate)
**Target:** 100% pass rate (2,330/2,330)

## Implementation Notes

**Test Priority:**
1. **test_use_slot_action_executes_effects** - Most important, integration test
2. **Custom action tests** - Lower priority, likely safe to remove

**When to Skip vs Fix:**
- Skip: If test covers functionality removed from Phase 1-3 scope
- Fix: If test covers active functionality but API changed
- Remove: If test duplicates coverage elsewhere

**Regression Prevention:**
After fixing, add test to CI to prevent future breakage:
```yaml
# .github/workflows/tests.yml
- name: Run previously failing tests
  run: |
    uv run pytest tests/test_townlet/integration/test_items_effects_cascade.py::test_use_slot_action_executes_effects -v
```

## References

- Test files: Various (identify during investigation)
- Related code: `src/townlet/items/action_handlers.py`, `src/townlet/effects/executor.py`
- Test infrastructure: `tests/conftest.py` (fixtures)
- CI: `.github/workflows/tests.yml` (add regression checks)
