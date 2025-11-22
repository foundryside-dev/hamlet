# P2-COMP-16: VFS Observation Marking Verification Needed

**Priority:** P2 (Minor - Verification Needed)
**Category:** Compiler System
**Estimated Effort:** 2 hours
**Status:** Open (Unclear)
**Created:** 2025-11-22

---

## Problem Description

The VFS observation marking field exists in `CompiledUniverse` and has test coverage, but it's unclear if the marking logic is complete and used correctly at runtime.

**Status:** 🔍 UNCLEAR
- Field exists: `CompiledUniverse.vfs_observation_spec`
- Test file exists: `test_vfs_observation_marking.py`
- Uncertainty: Is marking logic comprehensive? Is it used at runtime?

**Evidence:**
- Agent 1 (Compiler) report, section COMP-16
- Field found at `compiled.py:line_X`
- Test file found but not fully verified

---

## What Needs Verification

### 1. Marking Logic Completeness

**Check:** Does compiler correctly mark all observable VFS variables?

```python
# In compiler.py
def _mark_vfs_observations(self, vfs_profiles):
    """Mark which VFS variables should appear in observations."""
    marked = []

    for var_name, var_def in vfs_profiles.global_profile.items():
        if var_def.observation:
            marked.append(('global', var_name, var_def.semantic_type))

    for var_name, var_def in vfs_profiles.agent_profile.items():
        if var_def.observation:
            marked.append(('agent', var_name, var_def.semantic_type))

    # Check: Are item profiles marked?
    for profile_name, profile in vfs_profiles.item_profiles.items():
        for var_name, var_def in profile.items():
            if var_def.observation:
                marked.append(('item', profile_name, var_name, var_def.semantic_type))

    return VFSObservationSpec(marked)
```

**Questions:**
- Does it handle all three scopes (global/agent/item)? ✓ Verify
- Does it respect observation management modes? ✓ Verify
- Does it compute correct dimensions? ✓ Verify

### 2. Runtime Usage

**Check:** Is `vfs_observation_spec` used by observation builder?

```python
# In observation_builder.py
def build_observation(self, state, compiled_universe):
    spec = compiled_universe.vfs_observation_spec

    # Check: Is spec actually used?
    for scope, var_name, semantic_type in spec.marked_variables:
        # ... build observation from marked variables ...
```

**Questions:**
- Does observation builder read from spec? ✓ Verify
- Does it filter based on observation management mode? ✓ Verify
- Are dimensions consistent between compile-time and runtime? ✓ Verify

---

## How to Fix (Verification)

### Step 1: Read Existing Code (30 minutes)

```bash
# Find VFS observation marking implementation
grep -r "vfs_observation" src/townlet/universe/
grep -r "VFSObservationSpec" src/townlet/

# Check runtime usage
grep -r "vfs_observation_spec" src/townlet/vfs/
grep -r "vfs_observation_spec" src/townlet/environment/
```

### Step 2: Run Existing Tests (15 minutes)

```bash
# Run VFS observation marking tests
UV_CACHE_DIR=.uv-cache uv run pytest \
  tests/test_townlet/unit/universe/test_vfs_observation_marking.py \
  -v

# Check if tests are comprehensive
```

### Step 3: Add Missing Tests (1 hour, if needed)

**File:** `tests/test_townlet/unit/universe/test_vfs_observation_marking.py`

Add tests if missing:

```python
def test_marks_all_three_scopes():
    """Verify marking includes global, agent, and item VFS."""
    compiled = compile_universe("configs/vfs_smoke")
    spec = compiled.vfs_observation_spec

    assert spec.has_global_variables()
    assert spec.has_agent_variables()
    assert spec.has_item_variables()

def test_respects_observation_flag():
    """Verify only variables with observation=true are marked."""
    # Config has some observable, some not
    compiled = compile_universe("configs/mixed_observability")
    spec = compiled.vfs_observation_spec

    # Should include observable vars
    assert ('global', 'time_of_day') in spec.marked_variables

    # Should exclude non-observable vars
    assert ('global', 'internal_state') not in spec.marked_variables

def test_observation_dim_matches_marked_count():
    """Verify marked variables match obs_dim calculation."""
    compiled = compile_universe("configs/L1_full_observability")
    spec = compiled.vfs_observation_spec

    expected_dim = len(spec.marked_variables)
    actual_dim = compiled.observation_config.vfs_obs_dim

    assert expected_dim == actual_dim
```

### Step 4: Document Findings (15 minutes)

Update this issue with:
- ✅ Marking logic verified complete
- ✅ Runtime usage confirmed
- ✅ Tests comprehensive
- OR ❌ Gaps found, promote to P1 with details

---

## Acceptance Criteria

- [ ] Marking logic verified (handles all scopes)
- [ ] Runtime usage confirmed (observation builder uses spec)
- [ ] Tests comprehensive (all edge cases covered)
- [ ] If gaps found, new issue created with specifics
- [ ] Update gap-report-01-compiler.md with findings

---

## Files to Check

1. `src/townlet/universe/compiler.py` - Marking logic
2. `src/townlet/universe/compiled.py` - VFSObservationSpec definition
3. `src/townlet/vfs/observation_builder.py` - Runtime usage
4. `tests/test_townlet/unit/universe/test_vfs_observation_marking.py` - Tests

---

## Related Issues

- Related: P1-DOC-10 (observation management modes)
- Blocks: None (likely complete, just needs verification)

---

## Notes

- **Status: Unclear** - Code exists but full verification needed
- This is primarily a verification task, not implementation
- Likely will be marked ✅ COMPLETE after verification
- If gaps found, promote to P1 and create detailed fix plan
