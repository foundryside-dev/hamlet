# [COMP-17] Items-VFS Profile Binding Validation

**Priority:** P1 (Important)
**Category:** Compiler
**Status:** PARTIAL
**Effort:** 2 hours

## Description

Items catalog requires `vfs_profile` field in item definitions, but compiler does not validate that referenced profile names actually exist in compiled VFS profiles. Profile references are required but not cross-validated, leading to potential runtime errors if profile name is mistyped.

## Current State

**Schema validation (working):**
- `vfs_profile` field is required in `ItemDefinition` schema
- Schema validation ensures field is present and non-empty string
- Located in `src/townlet/items/schema.py`

**Cross-reference validation (missing):**
- Compiler does not check if profile name exists in `compiled_vfs_profiles`
- Misspelled profile names pass validation: `vfs_profile: "appl"` instead of `"apple"`
- Runtime error only discovered when item spawns

**Example issue:**
```yaml
# vfs_profiles.yaml
item_profiles:
  apple:
    energy_value: {type: int, default: 10}

# items_catalog.yaml
items:
  red_apple:
    vfs_profile: "appl"  # ❌ Typo - should be "apple"
    # Passes compilation but fails at runtime
```

## Required Implementation

Add cross-reference validation in `UniverseCompiler._stage_4_cross_validate()`:

1. **Collect all VFS profile names:**
   - Extract profile names from `compiled_vfs_profiles.item_profiles`
   - Store in set for O(1) lookup

2. **Validate all item profile references:**
   - Iterate through all items in items catalog
   - Check each `vfs_profile` reference exists in profile set
   - Raise clear validation error if profile not found

3. **Error message template:**
```
ValidationError: Item 'red_apple' references undefined VFS profile 'appl'
  Available profiles: apple, banana, sword, potion
  Did you mean: 'apple'?
```

Estimated: 2 hours (30 lines of validation code + 5 tests)

## Acceptance Criteria

- [ ] Compiler validates all `vfs_profile` references in items catalog
- [ ] Validation occurs in stage 4 (cross-validate)
- [ ] Clear error message when profile not found
- [ ] Error message suggests similar profile names (Levenshtein distance)
- [ ] Test: Valid profile references pass validation
- [ ] Test: Invalid profile reference raises ValidationError
- [ ] Test: Typo suggestions work correctly
- [ ] Test: Empty items catalog passes validation
- [ ] Test: Profile name with special characters handled correctly

## Evidence

**Source Report:** gap-report-final.md (lines 55-68), gap-report-compiler.md
**Related Requirements:** COMP-13 (typo suggestions), VFS profile system
**Current Schema:** `src/townlet/items/schema.py` (ItemDefinition.vfs_profile)

## Implementation Notes

**Implementation Location:**
```python
# src/townlet/universe/compiler.py

def _stage_4_cross_validate(self):
    """Cross-system validation."""

    # Existing validations...

    # NEW: Validate item-VFS profile bindings
    self._validate_item_profile_references()

def _validate_item_profile_references(self):
    """Validate all items reference existing VFS profiles."""
    if not self.compiled_vfs_profiles or not self.items_catalog:
        return  # Nothing to validate

    available_profiles = set(self.compiled_vfs_profiles.item_profiles.keys())

    for item_name, item_def in self.items_catalog.items.items():
        profile_name = item_def.vfs_profile
        if profile_name not in available_profiles:
            suggestions = self._suggest_typo_fixes(profile_name, available_profiles)
            raise ValidationError(
                f"Item '{item_name}' references undefined VFS profile '{profile_name}'\n"
                f"  Available profiles: {', '.join(sorted(available_profiles))}\n"
                f"  Did you mean: {suggestions}?"
            )
```

**Typo Suggestions (optional enhancement from COMP-13):**
- Use Levenshtein distance to find close matches
- Suggest profiles within edit distance 2
- Fallback to "no suggestions" if no close matches

**Edge Cases:**
- Empty items catalog (no items to validate)
- Empty VFS profiles (valid for minimal configs)
- Profile name with underscores/hyphens (exact match required)
- Case sensitivity (profile names are case-sensitive)

## References

- Source file: `src/townlet/universe/compiler.py:_stage_4_cross_validate()` (add validation)
- Schema file: `src/townlet/items/schema.py:ItemDefinition` (vfs_profile field)
- Test file: `tests/test_townlet/unit/universe/test_items_vfs_validation.py` (to be created)
- Related: VFS profiles compilation in `src/townlet/vfs/profiles.py`
