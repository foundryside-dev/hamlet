# [VFS-6] Mark-and-Sweep Runtime Integration

**Priority:** P1 (Important)
**Category:** VFS / Runtime
**Status:** PARTIAL
**Effort:** 1-2 days

## Description

VFS evaluator implements mark-and-sweep optimization but it's not fully wired into the runtime observation pipeline. Evaluator has EAGER/LAZY modes but ObservationBuilder doesn't mark which variables are actually used, forcing EAGER mode (evaluate all variables even if not observed). This creates a performance optimization gap.

## Current State

**What works:**
- ✅ VFSEvaluator has `evaluate_global_profile()` with mark-and-sweep logic
- ✅ VFSEvaluator supports EAGER and LAZY evaluation modes
- ✅ VectorizedHamletEnv.step() calls VFSEvaluator.evaluate_global_profile() (lines 1461-1487)
- ✅ Runtime VFS evaluation is functional and correct

**What's missing:**
- ❌ ObservationBuilder doesn't mark which VFS variables are consumed
- ❌ No `vfs_observation_marks` in CompiledUniverse
- ❌ Evaluator always runs in EAGER mode (evaluates all variables, not just marked ones)
- ❌ No integration tests for mark-and-sweep optimization

**Current behavior:** All VFS variables evaluate on every step, even if not observed. Functionally correct but less efficient than mark-and-sweep optimization.

**Performance impact:** Likely <1% overhead (efficient patterns already used), but formal benchmark needed (RUN-8).

## Required Implementation

### 1. Add Marking to ObservationBuilder (4-6 hours)

**File:** `src/townlet/vfs/observation_builder.py`

**Changes:**
```python
class ObservationBuilder:
    def build_vfs_observation(self, ...):
        """Build VFS observations and mark consumed variables."""

        # Existing: Build observation tensor
        obs_tensor = self._build_obs_tensor(...)

        # NEW: Track which variables were actually read
        consumed_vars = set()
        for slot in global_slots:
            consumed_vars.add(slot.var_name)
        for slot in agent_slots:
            consumed_vars.add(slot.var_name)
        for profile in item_profiles:
            for slot in profile.slots:
                consumed_vars.add(slot.var_name)

        # Return both observation and marks
        return obs_tensor, consumed_vars
```

### 2. Store Marks in CompiledUniverse (1 hour)

**File:** `src/townlet/universe/compiled.py`

**Changes:**
```python
@dataclass
class CompiledUniverse:
    # Existing fields...

    # NEW: VFS observation marks
    vfs_observation_marks: Optional[Set[str]] = None  # Variable names consumed by observations
```

**Compiler integration:**
```python
# src/townlet/universe/compiler.py
def compile(self):
    # After building observation spec
    obs_spec = ObservationBuilder.build_spec(...)
    vfs_marks = obs_spec.consumed_variables  # Extract from spec

    return CompiledUniverse(
        # Existing fields...
        vfs_observation_marks=vfs_marks
    )
```

### 3. Wire into VFSEvaluator (2-3 hours)

**File:** `src/townlet/environment/vectorized_env.py`

**Changes:**
```python
# In VectorizedHamletEnv.__init__():
self.vfs_observation_marks = compiled_universe.vfs_observation_marks

# In VectorizedHamletEnv.step():
if self.vfs_registry and self.compiled_universe.compiled_vfs_profiles:
    global_profile = self.compiled_universe.compiled_vfs_profiles.global_profile
    if global_profile:
        VFSEvaluator.evaluate_global_profile(
            profile=global_profile,
            registry=self.vfs_registry,
            context={...},
            mode=EvaluationMode.LAZY,  # Use LAZY instead of EAGER
            marks=self.vfs_observation_marks  # Pass marks for mark-and-sweep
        )
```

### 4. Integration Tests (3-4 hours)

**File:** `tests/test_townlet/integration/test_vfs_mark_and_sweep.py` (new)

**Test cases:**
- Test LAZY mode evaluates only marked variables
- Test EAGER mode evaluates all variables
- Test mark set correctly populated from observation spec
- Test performance comparison (EAGER vs LAZY)
- Test correctness: observations identical in both modes

## Acceptance Criteria

- [ ] ObservationBuilder.build_vfs_observation() returns consumed variable set
- [ ] CompiledUniverse.vfs_observation_marks field stores marks
- [ ] UniverseCompiler populates vfs_observation_marks during compilation
- [ ] VectorizedHamletEnv.step() passes marks to VFSEvaluator
- [ ] VFSEvaluator uses LAZY mode when marks provided
- [ ] Only marked variables are evaluated in LAZY mode
- [ ] All variables evaluated in EAGER mode (backward compatibility)
- [ ] Integration test validates mark-and-sweep optimization
- [ ] Performance test shows LAZY mode is faster than EAGER (when subset marked)
- [ ] No regression in observation correctness

## Evidence

**Source Report:** gap-report-final.md (lines 55-68, 256-265), gap-report-vfs.md
**Current Implementation:**
- VFSEvaluator: `src/townlet/vfs/evaluator.py`
- ObservationBuilder: `src/townlet/vfs/observation_builder.py`
- Runtime integration: `src/townlet/environment/vectorized_env.py:1461-1487`

## Implementation Notes

**Why P1 (not P0):** Functional correctness is maintained. This is an optimization, not a bug. EAGER mode works correctly, just evaluates more variables than necessary.

**Performance Context:**
- Efficient patterns already used (GPU tensors, cached ASTs, vectorized ops)
- Estimated overhead <1% in EAGER mode
- Mark-and-sweep optimization most valuable when:
  - Many VFS variables defined (>50)
  - Few variables observed (<20)
  - Complex expressions (nested paths, functions)

**Testing Strategy:**
1. Unit tests: VFSEvaluator mark-and-sweep logic in isolation
2. Integration tests: End-to-end with real environment
3. Performance tests: Benchmark EAGER vs LAZY on large VFS schemas

**Rollout Plan:**
1. Implement marking in ObservationBuilder (low risk)
2. Add marks to CompiledUniverse (no runtime impact)
3. Wire into VFSEvaluator (feature flag for safety)
4. Validate performance improvement with benchmarks
5. Enable LAZY mode by default once validated

## References

- Evaluator: `src/townlet/vfs/evaluator.py:evaluate_global_profile()`
- ObservationBuilder: `src/townlet/vfs/observation_builder.py:build_vfs_observation()`
- Runtime integration: `src/townlet/environment/vectorized_env.py:1461-1487`
- Test file: `tests/test_townlet/integration/test_vfs_mark_and_sweep.py` (to be created)
- Related: RUN-8 (performance benchmarks), VFS evaluation design in uplift plans
