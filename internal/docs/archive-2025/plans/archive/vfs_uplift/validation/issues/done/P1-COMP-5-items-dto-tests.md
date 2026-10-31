# [COMP-5] Items DTO Tests Coverage

**Priority:** P1 (Important)
**Category:** Compiler/Testing
**Status:** PARTIAL
**Effort:** 4-6 hours

## Description

Items DTO configuration exists and works correctly, but test coverage is significantly below target. Only 2 dedicated tests exist versus target of 15-20 tests for comprehensive DTO validation.

## Current State

**Implementation:** ✅ COMPLETE
- File: `src/townlet/config/items_config.py`
- DTOs exist: ItemTypeConfig (line 58), ItemsCatalogConfig (line 101), SpawnScheduleConfig, SpawnPlacementConfig
- All fields functional and validated

**Test Coverage:** ⚠️ INSUFFICIENT
- Current: 2 explicit items DTO tests
- Target: 15-20 tests
- Gap: 13-18 tests needed

**Existing Tests:**
- `tests/test_townlet/unit/config/test_items_dto.py` - exists but minimal coverage
- Items functionality tested indirectly through integration tests
- Missing: Edge case validation, error handling, field constraints

## Required Implementation

### Test Categories Needed

#### 1. **ItemTypeConfig Validation** (5-6 tests)
- Valid item with all fields
- Valid item with minimal fields (only required)
- Invalid: missing required fields (id, vfs_profile)
- Invalid: empty id string
- Invalid: vfs_profile null/empty
- Valid: special characters in item names
- Valid: initial_state with various VFS types

#### 2. **SpawnScheduleConfig Validation** (4-5 tests)
- Valid: periodic schedule
- Valid: time_window schedule
- Valid: poisson schedule
- Valid: normal distribution schedule
- Invalid: missing required fields
- Invalid: negative period/intervals

#### 3. **SpawnPlacementConfig Validation** (3-4 tests)
- Valid: random placement
- Valid: fixed placement with coordinates
- Valid: grid placement
- Valid: scripted placement
- Invalid: missing mode
- Invalid: invalid coordinates

#### 4. **ItemsCatalogConfig Validation** (2-3 tests)
- Valid catalog with multiple items
- Valid empty catalog
- Invalid: duplicate item IDs
- Invalid: null item definitions

#### 5. **Integration Validation** (1-2 tests)
- Complete items config with spawn rules
- Config with appearance rules
- Config with interactions

### Test File Structure

**File:** `tests/test_townlet/unit/config/test_items_dto.py`

```python
"""Comprehensive DTO validation tests for items configuration."""

import pytest
from pydantic import ValidationError

from townlet.config.items_config import (
    ItemTypeConfig,
    ItemsCatalogConfig,
    SpawnScheduleConfig,
    SpawnPlacementConfig,
)


class TestItemTypeConfig:
    """Tests for ItemTypeConfig DTO."""

    def test_valid_item_all_fields(self):
        """Valid item with all optional fields populated."""
        # ...

    def test_valid_item_minimal_fields(self):
        """Valid item with only required fields."""
        # ...

    def test_invalid_missing_id(self):
        """Reject item with missing id field."""
        # ...

    def test_invalid_empty_id(self):
        """Reject item with empty string id."""
        # ...

    def test_invalid_missing_vfs_profile(self):
        """Reject item without vfs_profile."""
        # ...

    def test_valid_initial_state_various_types(self):
        """initial_state accepts int/float/bool/list values."""
        # ...


class TestSpawnScheduleConfig:
    """Tests for spawn schedule validation."""

    def test_valid_periodic_schedule(self):
        """Periodic schedule with valid period."""
        # ...

    def test_valid_time_window_schedule(self):
        """Time window schedule with start/end."""
        # ...

    def test_invalid_negative_period(self):
        """Reject negative period values."""
        # ...

    # ... more tests


class TestSpawnPlacementConfig:
    """Tests for spawn placement modes."""

    def test_valid_random_placement(self):
        """Random placement mode."""
        # ...

    def test_valid_fixed_placement_with_coordinates(self):
        """Fixed placement with explicit coordinates."""
        # ...

    # ... more tests


class TestItemsCatalogConfig:
    """Tests for complete items catalog."""

    def test_valid_catalog_multiple_items(self):
        """Catalog with multiple item definitions."""
        # ...

    def test_valid_empty_catalog(self):
        """Empty catalog (no items) is valid."""
        # ...

    def test_invalid_duplicate_item_ids(self):
        """Reject catalog with duplicate item IDs."""
        # ...

    # ... more tests
```

## Acceptance Criteria

- [ ] 15-20 tests for items DTO validation
- [ ] All ItemTypeConfig fields tested (required and optional)
- [ ] All spawn schedule types validated
- [ ] All spawn placement modes validated
- [ ] Edge cases covered (empty strings, nulls, negative values)
- [ ] Error messages validated (Pydantic ValidationError)
- [ ] Tests follow existing DTO test patterns
- [ ] Tests run successfully with UV_CACHE_DIR

## Evidence

**Source Report:** gap-report-compiler.md (COMP-5 section)
**Baseline:** 2 existing tests in test_items_dto.py
**Target:** 15-20 tests (aligned with other DTO test files)
**Current Files:** src/townlet/config/items_config.py (7 config classes)

## Implementation Notes

**Follow Existing Patterns:**
Look at similar DTO test files for structure:
- `tests/test_townlet/unit/config/test_vfs_profiles_dto.py` (VFS DTOs)
- `tests/test_townlet/unit/config/test_effects_dto.py` (Effects DTOs)

**Pydantic Validation:**
- Use `pytest.raises(ValidationError)` for invalid cases
- Check error messages contain expected field names
- Test both missing fields and invalid values

**Test Organization:**
- One class per DTO type
- Descriptive test names (test_valid_*, test_invalid_*)
- Use fixtures for common config patterns

## References

- Implementation: `src/townlet/config/items_config.py`
- Test file: `tests/test_townlet/unit/config/test_items_dto.py` (expand this)
- Pattern examples: Other DTO test files in `tests/test_townlet/unit/config/`
- Related: Items functionality tests in `tests/test_townlet/unit/items/`
