# P2-COMP-24: Continuous Substrates Missing Position/Velocity in Observation Spec

**Priority:** P2 (MINOR)
**Category:** COMP (Compiler)
**Status:** OPEN
**Effort:** 2-3 hours

---

## Problem Description

The compiler's observation spec generation (`compiler.py:1537-1576`) **omits position/velocity observation fields for continuous substrates** (type="continuous" or "continuousnd"). Only discrete substrates (grid, grid3d, gridnd) get position/velocity fields added to the observation spec.

**Impact:**
- Observation spec is incomplete for continuous substrates
- Missing fields: `obs_position`, `obs_velocity`
- Runtime uses fallback logic (calls `substrate.encode_observation()` directly), so functionality still works
- Tests pass despite incomplete spec

**Severity:** MINOR - No functionality broken, but spec should be complete for consistency

---

## Evidence

### Code Analysis

**compiler.py:1537-1576**
```python
# Position / velocity (discrete spatial substrates only)  ← ⚠️ Comment says "discrete only"
position_dim = 0
if substrate.type in {"grid", "grid3d"} and substrate.grid is not None:
    if substrate.grid.topology == "cubic":
        position_dim = 3
    else:
        position_dim = 2
elif substrate.type == "gridnd" and substrate.gridnd is not None:
    position_dim = len(substrate.gridnd.dimension_sizes)
# ⚠️ MISSING: No handling for substrate.type in {"continuous", "continuousnd"}

if position_dim:  # ← This is 0 for continuous substrates
    fields.append(ObservationField(name="obs_position", dims=position_dim, ...))
    offset += position_dim
    fields.append(ObservationField(name="obs_velocity", dims=position_dim, ...))
    offset += position_dim
```

### Test Evidence

**Config:** `configs/test/action_space/continuous1d/stratum.yaml`
- Substrate type: `continuous`
- Dimensions: 1
- Observation encoding: `relative` (should produce 1-dimensional position encoding)

**Compilation Result:**
```
Observation Dim : 5

Observation Spec Fields:
  obs_meters                     dims= 3 [  0:  3] type=bars
  obs_affordance_at_position     dims= 2 [  3:  5] type=affordance

⚠️ MISSING: obs_position (expected 1 dim [5:6])
⚠️ MISSING: obs_velocity (expected 1 dim [6:7])
```

**Expected Total Dims:** 7 (3 meters + 2 affordances + 1 position + 1 velocity)
**Actual Total Dims:** 5 (3 meters + 2 affordances)

---

## Root Cause

The observation spec generation code assumes only discrete substrates have position/velocity observations. Continuous substrates were either overlooked or intentionally omitted during implementation.

However, continuous substrates **do** implement position encoding via `encode_observation()`:
- `continuous.py:294-314` - `encode_observation()` returns N-dimensional positions
- `continuousnd.py:288-308` - `encode_observation()` returns N-dimensional positions

The runtime has fallback logic that calls `substrate.encode_observation()` even when the observation spec doesn't include position fields:
- `vectorized_env.py:1348-1364` - `_encode_position_observation()` calls `substrate.encode_observation()`

**Hypothesis:** The observation spec gap was introduced during early development when continuous substrates were less commonly used, and the runtime fallback logic prevented the gap from causing test failures.

---

## Fix Required

### Option 1: Simple Fix (Account for Position Dimensions Only)

**Location:** `compiler.py:1537-1576`

**Change:**
```python
# Position / velocity (all spatial substrates)
position_dim = 0
if substrate.type in {"grid", "grid3d"} and substrate.grid is not None:
    if substrate.grid.topology == "cubic":
        position_dim = 3
    else:
        position_dim = 2
elif substrate.type == "gridnd" and substrate.gridnd is not None:
    position_dim = len(substrate.gridnd.dimension_sizes)
# ✅ ADD THIS:
elif substrate.type == "continuous" and substrate.continuous is not None:
    position_dim = substrate.continuous.dimensions
elif substrate.type == "continuousnd" and substrate.continuous is not None:
    position_dim = len(substrate.continuous.bounds)
```

**Limitation:** This assumes position observations are always N-dimensional, which is **incorrect for scaled encoding** (2N dims).

### Option 2: Accurate Fix (Build Substrate and Query Observation Dim)

**Location:** `compiler.py:1537-1576`

**Change:**
```python
# Position / velocity (all spatial substrates)
position_dim = 0
substrate_instance = None

if substrate.type in {"grid", "grid3d", "gridnd"}:
    # Discrete substrates: position_dim = number of spatial dimensions
    if substrate.type in {"grid", "grid3d"} and substrate.grid is not None:
        if substrate.grid.topology == "cubic":
            position_dim = 3
        else:
            position_dim = 2
    elif substrate.type == "gridnd" and substrate.gridnd is not None:
        position_dim = len(substrate.gridnd.dimension_sizes)

elif substrate.type in {"continuous", "continuousnd"}:
    # Continuous substrates: position_dim depends on observation_encoding
    # Build temporary instance to get accurate observation dimension
    substrate_instance = SubstrateFactory.build(substrate, torch.device("cpu"))
    position_dim = substrate_instance.get_observation_dim()
```

**Pros:**
- Accounts for observation_encoding (relative, scaled, absolute)
- Accurate for all substrate types
- Future-proof (new substrates automatically supported)

**Cons:**
- Requires building temporary substrate instance (slight overhead)
- Adds dependency on SubstrateFactory in observation spec generation

**Recommendation:** Use Option 2 (accurate fix) for consistency and future-proofing.

---

## Verification Steps

1. **Compile continuous1d config:**
   ```bash
   rm -rf /home/john/hamlet/configs/test/action_space/continuous1d/.compiled
   python -m townlet.compiler compile /home/john/hamlet/configs/test/action_space/continuous1d/
   ```

   **Expected Output:**
   ```
   Observation Dim : 7  # ← Was 5, should be 7
   ```

2. **Inspect observation spec:**
   ```python
   from townlet.universe.compiled import CompiledUniverse
   compiled = CompiledUniverse.load_from_cache(Path("configs/test/action_space/continuous1d/.compiled/universe.msgpack"))
   for field in compiled.observation_spec.fields:
       print(f"{field.name:30s} dims={field.dims:2d} [{field.start_index:3d}:{field.end_index:3d}]")
   ```

   **Expected Fields:**
   ```
   obs_position                   dims= 1 [  0:  1]  # ← NEW
   obs_velocity                   dims= 1 [  1:  2]  # ← NEW
   obs_meters                     dims= 3 [  2:  5]  # ← Offset shifted
   obs_affordance_at_position     dims= 2 [  5:  7]  # ← Offset shifted
   ```

3. **Test scaled encoding (2N dims):**
   - Change `observation_encoding: relative` → `observation_encoding: scaled`
   - Recompile
   - Expected: `obs_position` dims=2 (1 normalized + 1 range size)

4. **Run existing tests:**
   ```bash
   pytest tests/test_townlet/integration/test_substrate_migration.py::test_continuous_proximity_interaction -xvs
   ```

   **Expected:** ✅ PASS (no regressions)

---

## Acceptance Criteria

1. ✅ Continuous substrates get `obs_position` and `obs_velocity` fields in observation spec
2. ✅ Position dims correctly account for observation_encoding:
   - relative: N dims
   - scaled: 2N dims (normalized + range sizes)
   - absolute: N dims
3. ✅ Total observation dims match runtime observations
4. ✅ All existing tests pass (no regressions)
5. ✅ Continuous1d config compiles with Observation Dim=7 (not 5)

---

## Related Files

- `src/townlet/universe/compiler.py:1537-1576` - Observation spec generation (fix location)
- `src/townlet/substrate/continuous.py:294-332` - Continuous substrate observation encoding
- `src/townlet/substrate/continuousnd.py:288-325` - ContinuousND substrate observation encoding
- `src/townlet/environment/vectorized_env.py:1348-1364` - Runtime fallback logic
- `configs/test/action_space/continuous1d/` - Test config for verification

---

## Notes

- This is a **pre-existing gap**, not introduced by VFS uplift
- Runtime still works due to fallback logic in `vectorized_env.py`
- No users affected (pre-release with zero users)
- Fix improves consistency between compiler spec and runtime behavior

---

## Estimated Effort

**2-3 hours:**
- 1 hour: Implement Option 2 fix (build substrate instance, query observation dim)
- 30 min: Update tests to verify observation dims
- 30 min: Test with all observation encodings (relative, scaled, absolute)
- 30 min: Run full test suite, verify no regressions
