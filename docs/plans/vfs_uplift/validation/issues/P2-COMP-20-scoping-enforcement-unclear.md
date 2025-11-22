# P2-COMP-20: Experiment vs Level Scoping Enforcement Unclear

**Priority:** P2 (Minor - Verification Needed)
**Category:** Compiler System
**Estimated Effort:** 1-2 hours
**Status:** Open (Unclear)
**Created:** 2025-11-22

---

## Problem Description

The compiler enforces experiment-level scoping for VFS/effects/items, but it's unclear if this enforcement is complete and tested for all edge cases.

**Current Understanding:**
- Experiment-level: `vfs_profiles.yaml`, `effects.yaml`, `items.yaml`
- Level-specific: `substrate.yaml`, `bars.yaml`, `affordances.yaml`, `training.yaml`
- Enforcement likely exists but not fully verified

**Status:** 🔍 UNCLEAR
- Directory structure suggests correct scoping
- Compiler may enforce but verification needed
- Edge cases may not be tested

**Evidence:**
- Agent 1 (Compiler) report, section COMP-20
- Breaking changes (BREAK-1, BREAK-2) enforce scoping
- Unclear if all paths validated

---

## What Needs Verification

### 1. Experiment-Level Enforcement

**Check:** Does compiler reject level-scoped VFS/effects/items files?

```yaml
# configs/my_experiment/levels/L1/vfs_profiles.yaml  ❌ Should be rejected
# configs/my_experiment/vfs_profiles.yaml  ✅ Should be required
```

**Test:**
```bash
# Try to compile with misplaced files
mkdir -p /tmp/bad_scoping/levels/L1/
cp vfs_profiles.yaml /tmp/bad_scoping/levels/L1/  # Wrong location

python -m townlet.compiler compile /tmp/bad_scoping/

# Expected: CompilationError with clear message
# Actual: ???
```

### 2. Missing Experiment Files

**Check:** Does compiler require experiment-level files?

```yaml
# configs/my_experiment/
#   levels/L1/... ✓ Level files present
#   # Missing: vfs_profiles.yaml ❌

# Expected: CompilationError "Missing vfs_profiles.yaml at experiment level"
```

### 3. Duplicate Files

**Check:** What if both experiment and level have same file?

```yaml
# configs/my_experiment/vfs_profiles.yaml  ✓ Experiment level
# configs/my_experiment/levels/L1/vfs_profiles.yaml  ❌ Duplicate

# Expected: Error or warning?
```

---

## How to Fix (Verification)

### Step 1: Test Enforcement (30 minutes)

**Create test configs with scoping violations:**

```bash
# Test 1: Level-scoped VFS
mkdir -p /tmp/test_scoping/L1/
echo "version: 2.1\nglobal_profile: {}" > /tmp/test_scoping/L1/vfs_profiles.yaml

python -m townlet.compiler compile /tmp/test_scoping/
# Should fail with clear error

# Test 2: Missing experiment VFS
mkdir -p /tmp/test_scoping2/L1/
# Create only level files, no experiment vfs_profiles.yaml

python -m townlet.compiler compile /tmp/test_scoping2/
# Should fail with "Missing vfs_profiles.yaml"

# Test 3: Duplicate files
mkdir -p /tmp/test_scoping3/L1/
echo "..." > /tmp/test_scoping3/vfs_profiles.yaml
echo "..." > /tmp/test_scoping3/L1/vfs_profiles.yaml

python -m townlet.compiler compile /tmp/test_scoping3/
# Should fail or warn about duplicate
```

### Step 2: Check Compiler Logic (30 minutes)

**File:** `src/townlet/universe/compiler.py`

Find scoping validation:

```python
def _validate_file_scoping(self, config_dir):
    """Validate experiment vs level file scoping."""
    experiment_required = ['vfs_profiles.yaml', 'effects.yaml', 'items.yaml']
    level_required = ['substrate.yaml', 'bars.yaml', 'training.yaml']

    # Check experiment-level files exist
    for filename in experiment_required:
        path = config_dir / filename
        if not path.exists():
            raise CompilationError(f"Missing {filename} at experiment level: {config_dir}")

    # Check no level-scoped VFS/effects/items
    for level_dir in (config_dir / 'levels').iterdir():
        for forbidden in experiment_required:
            if (level_dir / forbidden).exists():
                raise CompilationError(
                    f"Found {forbidden} at level scope: {level_dir}\n"
                    f"This file must be at experiment level only: {config_dir}"
                )
```

**Check:** Does this logic exist? Is it comprehensive?

### Step 3: Add Tests (30 minutes, if missing)

**File:** `tests/test_townlet/unit/universe/test_scoping_enforcement.py` (NEW?)

```python
def test_rejects_level_scoped_vfs():
    """Verify compiler rejects vfs_profiles.yaml at level scope."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid config with level-scoped VFS
        bad_config = Path(tmpdir) / "bad_config"
        (bad_config / "levels" / "L1").mkdir(parents=True)
        (bad_config / "levels" / "L1" / "vfs_profiles.yaml").write_text("version: 2.1")

        # Should raise CompilationError
        with pytest.raises(CompilationError, match="vfs_profiles.yaml.*level scope"):
            UniverseCompiler().compile(bad_config)

def test_requires_experiment_vfs():
    """Verify compiler requires vfs_profiles.yaml at experiment level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config missing experiment VFS
        config = Path(tmpdir) / "config"
        (config / "levels" / "L1").mkdir(parents=True)
        # ... create level files but not vfs_profiles.yaml ...

        with pytest.raises(CompilationError, match="Missing vfs_profiles.yaml"):
            UniverseCompiler().compile(config)
```

---

## Acceptance Criteria

- [ ] Compiler rejects level-scoped VFS/effects/items files
- [ ] Compiler requires experiment-level VFS/effects/items files
- [ ] Clear error messages for scoping violations
- [ ] Tests verify all scoping rules
- [ ] If gaps found, promote to P1 with fix plan
- [ ] Update gap-report-01-compiler.md with findings

---

## Files to Check/Modify

1. `src/townlet/universe/compiler.py` - Scoping validation logic
2. `tests/test_townlet/unit/universe/test_scoping_enforcement.py` (NEW?) - Tests
3. `src/townlet/universe/errors.py` - Error messages

---

## Related Issues

- Related: P2-BREAK-1, BREAK-2 (already verified working)
- Blocks: None (edge case verification)

---

## Notes

- **Status: Unclear** - Likely working but needs verification
- Scoping is critical for clean architecture (experiment reusability)
- Tests may exist but weren't found by Agent 1
- After verification, likely mark ✅ COMPLETE or promote to P1 if gaps found
- Low priority because breaking changes agent verified enforcement works
