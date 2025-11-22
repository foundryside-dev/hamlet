# Implementation Plan: P2-COMP-24 - Fix Continuous Substrate Observation Spec Gap

**Date:** 2025-11-22
**Issue:** P2-COMP-24-continuous-observation-spec.md
**Effort:** 2-3 hours
**Goal:** Add position/velocity observation fields to observation spec for continuous substrates

---

## Executive Summary

**Problem:** Compiler omits position/velocity fields from observation spec for continuous substrates, causing spec to be incomplete even though runtime still works (via fallback logic).

**Solution:** Modify `compiler.py:_build_observation_spec()` to instantiate continuous substrates and query their actual observation dimensions, accounting for observation_encoding modes (relative, scaled, absolute).

**Strategy:** Use Option 2 (accurate fix) - build temporary substrate instance to get precise observation dimensions rather than hardcoding assumptions.

---

## Problem Analysis

### Current Behavior

**File:** `src/townlet/universe/compiler.py:1537-1576`

```python
# Position / velocity (discrete spatial substrates only)
position_dim = 0
if substrate.type in {"grid", "grid3d"} and substrate.grid is not None:
    if substrate.grid.topology == "cubic":
        position_dim = 3
    else:
        position_dim = 2
elif substrate.type == "gridnd" and substrate.gridnd is not None:
    position_dim = len(substrate.gridnd.dimension_sizes)
# ❌ MISSING: No handling for continuous/continuousnd

if position_dim:
    fields.append(ObservationField(name="obs_position", dims=position_dim, ...))
    offset += position_dim
    fields.append(ObservationField(name="obs_velocity", dims=position_dim, ...))
    offset += position_dim
```

### Why Simple Fix Is Insufficient

**Simple approach** (just add dimension count):
```python
elif substrate.type == "continuous" and substrate.continuous is not None:
    position_dim = substrate.continuous.dimensions
elif substrate.type == "continuousnd" and substrate.continuous is not None:
    position_dim = len(substrate.continuous.bounds)
```

**Problem:** This assumes position observations are always N-dimensional, but **observation_encoding changes dimensionality**:

| Encoding   | Dims | Example (2D) | Description                          |
|------------|------|--------------|--------------------------------------|
| relative   | N    | 2            | Normalized [0, 1] coordinates        |
| scaled     | 2N   | 4            | Normalized + range sizes metadata    |
| absolute   | N    | 2            | Raw unnormalized coordinates         |

**For a 2D continuous substrate with scaled encoding:**
- Simple fix: position_dim = 2 ❌ WRONG
- Correct: position_dim = 4 (2 normalized + 2 range sizes) ✅

---

## Solution Design

### Approach: Query Substrate Instance

**Strategy:** Build temporary substrate instance and call `get_observation_dim()` to get accurate dimensions.

**Rationale:**
1. ✅ Accounts for observation_encoding automatically
2. ✅ Future-proof (new substrates auto-supported)
3. ✅ Consistent with how substrates report their dimensions
4. ✅ No hardcoded assumptions

**Trade-off:**
- ⚠️ Requires building substrate instance during compilation (minimal overhead)
- ⚠️ Adds dependency on SubstrateFactory in observation spec generation

**Verdict:** Trade-off acceptable - compilation is already building substrate instance for action space assembly (line 1803), so this adds consistency.

---

## Implementation Plan

### Phase 1: Code Changes (1 hour)

#### Step 1.1: Modify Observation Spec Generation

**File:** `src/townlet/universe/compiler.py`
**Method:** `_build_observation_spec()` (around line 1400)
**Lines to modify:** 1537-1576

**Change:**

```python
# Position / velocity (all spatial substrates)
position_dim = 0
velocity_dim = 0  # May differ from position_dim for some substrates

if substrate.type == "aspatial":
    # Aspatial substrates have no position
    position_dim = 0
    velocity_dim = 0

elif substrate.type in {"grid", "grid3d"}:
    # Discrete grid substrates: position_dim = spatial dimensions
    if substrate.grid is not None:
        if substrate.grid.topology == "cubic":
            position_dim = 3
        else:
            position_dim = 2
    velocity_dim = position_dim  # Velocity matches position dims

elif substrate.type == "gridnd":
    # High-dimensional discrete grids
    if substrate.gridnd is not None:
        position_dim = len(substrate.gridnd.dimension_sizes)
    velocity_dim = position_dim

elif substrate.type in {"continuous", "continuousnd"}:
    # Continuous substrates: observation dims depend on encoding mode
    # Build temporary instance to query actual observation dimensions
    try:
        substrate_instance = SubstrateFactory.build(substrate, torch.device("cpu"))
        position_dim = substrate_instance.get_observation_dim()

        # Velocity always matches substrate's native dimensionality (not encoding)
        # e.g., 2D continuous with scaled encoding: position=4, velocity=2
        velocity_dim = substrate_instance.position_dim

    except Exception as exc:
        # Fallback: use position_dim from config (may be inaccurate for scaled)
        if substrate.type == "continuous" and substrate.continuous is not None:
            position_dim = substrate.continuous.dimensions
            velocity_dim = substrate.continuous.dimensions
        elif substrate.type == "continuousnd" and substrate.continuous is not None:
            position_dim = len(substrate.continuous.bounds)
            velocity_dim = len(substrate.continuous.bounds)

        # Log warning about fallback
        import warnings
        warnings.warn(
            f"Failed to build substrate instance for observation dim calculation: {exc}. "
            f"Using fallback dims (may be inaccurate for scaled encoding).",
            UserWarning,
        )

else:
    # Unknown substrate type - leave position_dim=0
    position_dim = 0
    velocity_dim = 0

# Add position observation field
if position_dim:
    fields.append(
        ObservationField(
            uuid=None,
            name="obs_position",
            type="vector",
            dims=position_dim,
            start_index=offset,
            end_index=offset + position_dim,
            scope="agent",
            description=f"Agent position ({position_dim}D, encoding: {substrate.get('observation_encoding', 'relative')})",
            semantic_type="spatial",
        )
    )
    offset += position_dim

# Add velocity observation field
if velocity_dim:
    fields.append(
        ObservationField(
            uuid=None,
            name="obs_velocity",
            type="vector",
            dims=velocity_dim,
            start_index=offset,
            end_index=offset + velocity_dim,
            scope="agent",
            description=f"Agent velocity ({velocity_dim}D)",
            semantic_type="spatial",
        )
    )
    offset += velocity_dim
```

**Key Changes:**
1. Added `elif` branch for continuous substrates
2. Build substrate instance using `SubstrateFactory.build()`
3. Query `substrate_instance.get_observation_dim()` for accurate position dims
4. Use `substrate_instance.position_dim` for velocity dims (native dimensionality)
5. Added try/except fallback for robustness
6. Enhanced description to include observation_encoding

#### Step 1.2: Add Import if Missing

**File:** `src/townlet/universe/compiler.py`
**Line:** ~40 (with other imports)

**Verify import exists:**
```python
from townlet.substrate.factory import SubstrateFactory
```

**Already present:** Line 41 shows `from townlet.substrate.factory import SubstrateFactory` ✅

---

### Phase 2: Testing (1 hour)

#### Step 2.1: Unit Test - Continuous1D

**Test:** Verify observation spec for continuous1d config

```bash
# Clean cache
rm -rf /home/john/hamlet/configs/test/action_space/continuous1d/.compiled

# Recompile with fix
export PYTHONPATH=/home/john/hamlet/src
python -m townlet.compiler compile /home/john/hamlet/configs/test/action_space/continuous1d/

# Verify observation dim
python << 'EOF'
from townlet.universe.compiled import CompiledUniverse
from pathlib import Path

compiled = CompiledUniverse.load_from_cache(
    Path("/home/john/hamlet/configs/test/action_space/continuous1d/.compiled/universe.msgpack")
)

print("Observation Spec Fields:")
print("-" * 80)
for field in compiled.observation_spec.fields:
    print(f"  {field.name:30s} dims={field.dims:2d} [{field.start_index:3d}:{field.end_index:3d}] type={field.semantic_type}")

print(f"\nTotal dims: {compiled.observation_spec.total_dims}")

# Verify position/velocity fields exist
field_names = {f.name for f in compiled.observation_spec.fields}
assert "obs_position" in field_names, "Missing obs_position field"
assert "obs_velocity" in field_names, "Missing obs_velocity field"

# Verify dims
pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

# Continuous1D with relative encoding: position=1, velocity=1
assert pos_field.dims == 1, f"Expected position dims=1, got {pos_field.dims}"
assert vel_field.dims == 1, f"Expected velocity dims=1, got {vel_field.dims}"

# Total dims: 1 position + 1 velocity + 3 meters + 2 affordances = 7
assert compiled.observation_spec.total_dims == 7, f"Expected total_dims=7, got {compiled.observation_spec.total_dims}"

print("\n✅ All assertions passed!")
EOF
```

**Expected Output:**
```
Observation Spec Fields:
--------------------------------------------------------------------------------
  obs_position                   dims= 1 [  0:  1] type=spatial
  obs_velocity                   dims= 1 [  1:  2] type=spatial
  obs_meters                     dims= 3 [  2:  5] type=bars
  obs_affordance_at_position     dims= 2 [  5:  7] type=affordance

Total dims: 7

✅ All assertions passed!
```

#### Step 2.2: Test Observation Encoding Modes

**Create test configs for each encoding mode:**

```bash
# Test relative encoding (default)
python -m townlet.compiler compile configs/test/action_space/continuous1d/
# Expected: position=1, total=7

# Create scaled encoding variant
mkdir -p /tmp/continuous1d_scaled
cp -r configs/test/action_space/continuous1d/* /tmp/continuous1d_scaled/
sed -i 's/observation_encoding: relative/observation_encoding: scaled/' /tmp/continuous1d_scaled/stratum.yaml

# Test scaled encoding
python -m townlet.compiler compile /tmp/continuous1d_scaled/
# Expected: position=2 (1 normalized + 1 range size), total=8

# Verify scaled encoding dims
python << 'EOF'
from townlet.universe.compiled import CompiledUniverse
from pathlib import Path

compiled = CompiledUniverse.load_from_cache(
    Path("/tmp/continuous1d_scaled/.compiled/universe.msgpack")
)

pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

# Scaled encoding: position=2 (normalized + range), velocity=1 (native dim)
assert pos_field.dims == 2, f"Expected position dims=2 for scaled, got {pos_field.dims}"
assert vel_field.dims == 1, f"Expected velocity dims=1, got {vel_field.dims}"

# Total: 2 position + 1 velocity + 3 meters + 2 affordances = 8
assert compiled.observation_spec.total_dims == 8, f"Expected total_dims=8, got {compiled.observation_spec.total_dims}"

print("✅ Scaled encoding test passed!")
EOF
```

#### Step 2.3: Test ContinuousND (4D+ substrates)

**Create 4D continuous test config:**

```bash
mkdir -p /tmp/continuous4d_test
cat > /tmp/continuous4d_test/stratum.yaml << 'EOF'
stratum:
  version: "1.0"
  substrate:
    type: continuousnd
    continuous:
      dimensions: 4
      bounds:
        - [0.0, 10.0]
        - [0.0, 10.0]
        - [0.0, 10.0]
        - [0.0, 10.0]
      boundary: clamp
      movement_delta: 0.5
      interaction_radius: 1.0
      distance_metric: euclidean
      observation_encoding: relative
      action_discretization:
        num_directions: 8
        num_magnitudes: 3
  vision_support: global
  temporal_support: disabled
EOF

# Copy other required files from continuous1d
cp configs/test/action_space/continuous1d/environment.yaml /tmp/continuous4d_test/
cp configs/test/action_space/continuous1d/experiment.yaml /tmp/continuous4d_test/
cp configs/test/action_space/continuous1d/agent.yaml /tmp/continuous4d_test/
cp configs/test/action_space/continuous1d/actions.yaml /tmp/continuous4d_test/
cp configs/test/action_space/continuous1d/effects.yaml /tmp/continuous4d_test/

# Compile
python -m townlet.compiler compile /tmp/continuous4d_test/

# Verify 4D observations
python << 'EOF'
from townlet.universe.compiled import CompiledUniverse
from pathlib import Path

compiled = CompiledUniverse.load_from_cache(
    Path("/tmp/continuous4d_test/.compiled/universe.msgpack")
)

pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

# 4D continuous with relative encoding: position=4, velocity=4
assert pos_field.dims == 4, f"Expected position dims=4, got {pos_field.dims}"
assert vel_field.dims == 4, f"Expected velocity dims=4, got {vel_field.dims}"

# Total: 4 position + 4 velocity + 3 meters + 2 affordances = 13
assert compiled.observation_spec.total_dims == 13, f"Expected total_dims=13, got {compiled.observation_spec.total_dims}"

print("✅ ContinuousND 4D test passed!")
EOF
```

#### Step 2.4: Regression Test - Discrete Substrates

**Verify discrete substrates still work correctly:**

```bash
# Test Grid2D (should still be 2D position/velocity)
python -m townlet.compiler compile configs/L0_0_minimal/ --no-cache

python << 'EOF'
from townlet.universe.compiled import CompiledUniverse
from pathlib import Path

compiled = CompiledUniverse.load_from_cache(
    Path("configs/L0_0_minimal/.compiled/universe.msgpack")
)

pos_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_position")
vel_field = next(f for f in compiled.observation_spec.fields if f.name == "obs_velocity")

assert pos_field.dims == 2, f"Grid2D should have position dims=2, got {pos_field.dims}"
assert vel_field.dims == 2, f"Grid2D should have velocity dims=2, got {vel_field.dims}"

print("✅ Grid2D regression test passed!")
EOF

# Test GridND (should still be N-dimensional)
# (Would need GridND test config - skip if not available)
```

#### Step 2.5: Integration Test - Full Environment

**Test that runtime can build observations correctly:**

```bash
export PYTHONPATH=/home/john/hamlet/src
export UV_CACHE_DIR=.uv-cache

# Run continuous substrate integration test
uv run pytest tests/test_townlet/integration/test_substrate_migration.py::test_continuous_proximity_interaction -xvs

# Expected: ✅ PASS
```

---

### Phase 3: Edge Cases & Validation (30 min)

#### Edge Case 1: Aspatial Substrate

**Verify aspatial still has no position/velocity:**

```bash
# Aspatial substrates should have position_dim=0
# No changes expected - verify no regression
```

#### Edge Case 2: Missing Substrate Config

**Test fallback behavior when substrate config is malformed:**

```python
# Create malformed config (e.g., continuous with no bounds)
# Verify compiler raises ValidationError, not crashes
```

#### Edge Case 3: Continuous2D with Discretized Actions

**Test 2D continuous with large action space:**

```bash
# num_directions=32, num_magnitudes=7 = 224 actions
# Verify observation spec still correct (position=2 or 4 depending on encoding)
```

---

### Phase 4: Documentation Updates (30 min)

#### Update 1: Code Comments

**File:** `src/townlet/universe/compiler.py`
**Location:** Lines 1537-1576

**Add docstring explaining logic:**

```python
# Position / velocity observation fields
#
# Position dimensions depend on substrate type and observation encoding:
# - Grid2D/Grid3D: 2D or 3D (fixed)
# - GridND: N dimensions (N=4 to 100)
# - Continuous/ContinuousND: N or 2N dimensions depending on observation_encoding
#   - relative: N dims (normalized [0,1])
#   - scaled: 2N dims (normalized + range sizes)
#   - absolute: N dims (raw coordinates)
# - Aspatial: 0 dims (no position)
#
# For continuous substrates, we build a temporary instance to query
# get_observation_dim() to get accurate dimensions based on encoding mode.
```

#### Update 2: Issue Ticket

**File:** `docs/plans/vfs_uplift/validation/issues/P2-COMP-24-continuous-observation-spec.md`

**Mark as resolved:**

```markdown
**Status:** ✅ RESOLVED (2025-11-22)

**Fix Committed:** [commit hash]
- Modified compiler.py:_build_observation_spec() to build substrate instances
- Added position/velocity fields for continuous substrates
- Accounts for observation_encoding (relative, scaled, absolute)
- All tests passing
```

#### Update 3: Analysis Document

**File:** `docs/plans/vfs_uplift/validation/SUBSTRATE-COMPILER-ANALYSIS.md`

**Update findings section:**

```markdown
### ✅ Continuous Substrates Observation Spec (FIXED)

**Status:** ✅ RESOLVED (was ⚠️ gap)

**Fix Applied:** Compiler now builds substrate instances to query observation dimensions,
accounting for observation_encoding mode.

**Verification:**
- Continuous1D relative: position=1, velocity=1 ✅
- Continuous1D scaled: position=2, velocity=1 ✅
- ContinuousND 4D: position=4, velocity=4 ✅
```

---

## Rollout Plan

### Step-by-Step Execution

```bash
# 1. Create feature branch (optional, or work directly on vfs,effects,items)
cd /home/john/hamlet

# 2. Make code changes
# Edit src/townlet/universe/compiler.py as described in Phase 1

# 3. Test continuous1d (relative encoding)
rm -rf configs/test/action_space/continuous1d/.compiled
python -m townlet.compiler compile configs/test/action_space/continuous1d/
# Run verification script from Step 2.1

# 4. Test scaled encoding
# Create scaled variant and test as in Step 2.2

# 5. Test ContinuousND 4D
# Create 4D config and test as in Step 2.3

# 6. Run regression tests
pytest tests/test_townlet/integration/test_substrate_migration.py -xvs

# 7. Run full compiler test suite
pytest tests/test_townlet/unit/universe/ -k compiler -xvs

# 8. Update documentation
# Edit issue ticket, analysis document as in Phase 4

# 9. Commit changes
git add src/townlet/universe/compiler.py
git add docs/plans/vfs_uplift/validation/issues/P2-COMP-24-continuous-observation-spec.md
git add docs/plans/vfs_uplift/validation/SUBSTRATE-COMPILER-ANALYSIS.md
git commit -m "fix(compiler): add position/velocity observations for continuous substrates

- Modified _build_observation_spec() to build substrate instances for continuous types
- Query get_observation_dim() to account for observation_encoding (relative/scaled/absolute)
- Fixes P2-COMP-24: observation spec was incomplete for continuous substrates
- Tested with continuous1d (relative and scaled) and continuousnd 4D
- All regression tests passing

Closes #P2-COMP-24"
```

---

## Verification Checklist

### Pre-Commit

- [ ] Code compiles without errors
- [ ] Continuous1D relative encoding: position=1, velocity=1, total=7
- [ ] Continuous1D scaled encoding: position=2, velocity=1, total=8
- [ ] ContinuousND 4D: position=4, velocity=4, total=13
- [ ] Grid2D regression: position=2, velocity=2 (no change)
- [ ] Aspatial regression: no position/velocity fields (no change)
- [ ] Integration test `test_continuous_proximity_interaction` passes
- [ ] No new compiler warnings

### Post-Commit

- [ ] All curriculum configs recompile successfully
- [ ] Full test suite passes: `pytest tests/test_townlet/ -x`
- [ ] Documentation updated
- [ ] Issue ticket marked resolved

---

## Risk Assessment

### Low Risk

**Why:**
1. ✅ Only affects observation spec generation (well-isolated code)
2. ✅ Continuous substrates already work (runtime has fallback logic)
3. ✅ No API changes (internal compiler implementation detail)
4. ✅ Pre-release with zero users (no backwards compatibility concerns)

### Potential Issues

1. **Substrate instantiation failure:**
   - **Mitigation:** Try/except with fallback to dimension count
   - **Impact:** Minimal - fallback dims are better than nothing

2. **Performance overhead:**
   - **Mitigation:** Compilation already builds substrates for action space (line 1803)
   - **Impact:** Negligible - one extra substrate build per compilation

3. **Observation dim mismatch:**
   - **Mitigation:** Comprehensive testing of all encoding modes
   - **Impact:** Would be caught by integration tests

---

## Success Criteria

### Must Have (P0)

1. ✅ Continuous substrates get position/velocity fields in observation spec
2. ✅ Position dims correctly account for observation_encoding
3. ✅ All existing tests pass (no regressions)
4. ✅ Continuous1D config compiles with correct observation dims

### Should Have (P1)

1. ✅ ContinuousND (4D+) tested and verified
2. ✅ All observation encodings tested (relative, scaled, absolute)
3. ✅ Documentation updated

### Nice to Have (P2)

1. ⚪ Add unit test specifically for observation spec generation
2. ⚪ Add config schema validation test for continuous substrates

---

## Timeline

**Total Effort:** 2-3 hours

| Phase                      | Time    | Cumulative |
|----------------------------|---------|------------|
| Phase 1: Code Changes      | 1 hour  | 1 hour     |
| Phase 2: Testing           | 1 hour  | 2 hours    |
| Phase 3: Edge Cases        | 30 min  | 2.5 hours  |
| Phase 4: Documentation     | 30 min  | 3 hours    |

**Recommended Schedule:**
- Start: After current substrate analysis complete
- End: Within same work session (3 hours max)
- Blocker: None (no dependencies on other issues)

---

## Next Steps

1. **Read this plan** - Review and confirm approach
2. **Execute Phase 1** - Make code changes to compiler.py
3. **Execute Phase 2** - Run all test cases
4. **Execute Phase 3** - Verify edge cases
5. **Execute Phase 4** - Update documentation
6. **Commit** - Create clean commit with descriptive message

**Ready to proceed?** Say "yes" to start Phase 1, or ask questions if anything needs clarification.
