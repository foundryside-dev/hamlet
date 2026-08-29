# Test Suite Dead Code Cleanup Plan

**Created**: 2025-11-25
**Status**: In Progress

## Overview

Deep dive analysis of the test suite revealed backwards compatibility patterns and dead code that violate CLAUDE.md's "ZERO backwards compatibility" rule.

## High Priority: CLAUDE.md Violations

### Issue 1: TestBackwardCompatibility class in test_observation_field_schema.py
- **Location**: `tests/test_townlet/unit/vfs/test_observation_field_schema.py:90-103`
- **Problem**: Tests that optional fields have defaults for "old configs that don't have the new fields"
- **Fix**: Delete the entire `TestBackwardCompatibility` class

### Issue 2: Checkpoint backwards compat test
- **Location**: `tests/test_townlet/unit/population/test_vectorized_population.py:1036-1095`
- **Problem**: `test_checkpoint_without_scheduler_state_is_backward_compatible` simulates loading "old checkpoints"
- **Fix**: Delete the test function

### Issue 3: TestActionConfigBackwardCompatibility class
- **Location**: `tests/test_townlet/unit/environment/test_action_config_extension.py:150-172`
- **Problem**: Tests that `reads`/`writes` fields are optional with defaults
- **Fix**: Delete the entire `TestActionConfigBackwardCompatibility` class

### Issue 4: hasattr() fallback in test_checkpointing.py
- **Location**: `tests/test_townlet/integration/test_checkpointing.py:54-56`
- **Problem**: `if hasattr(curriculum, "initialize_population")` tolerates missing method
- **Fix**: Remove hasattr check, call method directly

### Issue 5: hasattr() fallback in test_vectorized_population.py
- **Location**: `tests/test_townlet/unit/population/test_vectorized_population.py:528`
- **Problem**: `sequence_length if hasattr(...) else 1` fallback
- **Fix**: Remove hasattr, access attribute directly

## Medium Priority: Unused Code

### Issue 6: Unused fixtures
- **Location**: `tests/test_townlet/_fixtures/environment.py:54-94` - `instant_env`
- **Location**: `tests/test_townlet/_fixtures/variable_meters.py:784-807` - `task001_env_4meter_pomdp`
- **Location**: `tests/test_townlet/_fixtures/variable_meters.py:835-848` - `task001_env_12meter_pomdp`
- **Fix**: Delete all three fixtures

### Issue 7: Unused constants
- **Location**: `tests/test_townlet/unit/config/fixtures.py:118-144`
- **Problem**: 16 constants defined but never used
- **Fix**: Delete lines 118-144

## Verification

After all changes, run:
```bash
UV_CACHE_DIR=.uv-cache uv run pytest tests/test_townlet/ -x -q
```
