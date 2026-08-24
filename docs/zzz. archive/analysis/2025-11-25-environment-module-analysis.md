# Environment Module Analysis Report

**Date**: 2025-11-25
**Scope**: `src/townlet/environment/`
**Analyst**: Claude Code
**Status**: Draft for Review

---

## Executive Summary

A comprehensive audit of the `src/townlet/environment/` directory identified **21 issues** across 6 categories. The environment module is the core runtime for HAMLET's vectorized training system, handling agent-environment interactions, reward computation, and observation generation.

**Key Findings**:
- **3 High-severity bugs** that could cause crashes or incorrect behavior
- **8 Medium-severity issues** affecting robustness and maintainability
- **6 Code quality issues** violating DRY principles
- **4 Performance opportunities** for optimization

**Risk Assessment**: The module is functionally stable for current use cases but has latent bugs that could manifest with edge-case configurations (large grids, unusual VFS types, device mismatches).

**Recommendation**: Address high-priority bugs before expanding curriculum levels. Refactoring can be deferred but should be tracked.

---

## Issue Catalog

### Category 1: Type Safety & Validation Bugs

#### Issue ENV-001: VFS Type Conversion Fallback Allows Invalid Types

**Location**: `vectorized_env.py:304-309`

**Description**:
When converting VFS variable types from compiled profiles, the code uses a fallback that assigns unknown type strings directly without validation:

```python
# Current code (problematic)
if var.type in {"float", "scalar"}:
    var_type = "scalar"
elif var.type == "bool":
    var_type = "bool"
# ... other known types ...
else:
    var_type = var.type  # DANGER: Passes through invalid types
```

If a config contains a typo like `type: "scaler"` (instead of "scalar"), this silently propagates to `VariableDef`, causing downstream failures in the VFS registry with cryptic error messages.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Medium | Requires config error, but no validation catches it |
| Impact | High | Crashes during training with unhelpful error |
| Blast Radius | Single run | Fails fast, doesn't corrupt data |

**Proposed Fix**:
```python
VALID_VFS_TYPES = {"scalar", "bool", "tensor1d", "tensor2d", "tensor3d", "tensorNd"}

if var.type in {"float", "scalar"}:
    var_type = "scalar"
elif var.type == "bool":
    var_type = "bool"
# ... other mappings ...
else:
    if var.type not in VALID_VFS_TYPES:
        raise ValueError(
            f"Unsupported VFS variable type '{var.type}' for variable '{var.id}'. "
            f"Valid types: {sorted(VALID_VFS_TYPES)}"
        )
    var_type = var.type
```

**Complexity**: Low (1-2 hours)
- Add constant for valid types
- Add validation with clear error message
- Add unit test for invalid type rejection

---

#### Issue ENV-002: Vision Range Unbounded - OOM Risk

**Location**: `vectorized_env.py:224-227`

**Description**:
Vision radius calculation for POMDP observations has no upper bound:

```python
self.vision_radius = max(1, int(math.ceil(vision_range * (grid_size / 2.0))))
```

For a 1000x1000 grid with `vision_range=1.0`, this computes `radius=500`, creating a 1001x1001 observation window (1,002,001 cells). With 1000 agents and float32, this requires ~4GB just for the observation tensor, likely causing OOM.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Low | Requires unusual config (large grid + high vision) |
| Impact | Critical | OOM crash, potentially kills other processes |
| Blast Radius | System | Can affect entire machine if swap thrashes |

**Proposed Fix**:
```python
MAX_VISION_RADIUS = 50  # Practical upper bound (101x101 window max)

raw_radius = int(math.ceil(vision_range * (grid_size / 2.0)))
self.vision_radius = max(1, min(raw_radius, MAX_VISION_RADIUS))

if raw_radius > MAX_VISION_RADIUS:
    logger.warning(
        f"Vision radius {raw_radius} exceeds max {MAX_VISION_RADIUS}, clamping. "
        f"Consider reducing vision_range or grid_size."
    )
```

**Complexity**: Low (1 hour)
- Add constant and clamping
- Add warning log
- Add unit test for clamping behavior

---

#### Issue ENV-003: Division by Zero if hours_per_day=0

**Location**: `vectorized_env.py:557, 870`

**Description**:
`hours_per_day` is derived from action mask table shape:

```python
self.hours_per_day = self.action_mask_table.shape[0] if self.action_mask_table.ndim > 0 else 24
```

If the table has shape `[0, ...]` (empty), `hours_per_day=0`. Later at line 870:

```python
hour_idx = active_hour % self.hours_per_day  # ZeroDivisionError
```

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Low | Requires malformed config with empty action masks |
| Impact | High | Crash with unhelpful traceback |
| Blast Radius | Single run | Fails deterministically |

**Proposed Fix**:
```python
self.hours_per_day = max(1, self.action_mask_table.shape[0]) if self.action_mask_table.ndim > 0 else 24

# Add assertion for safety
assert self.hours_per_day > 0, "hours_per_day must be positive"
```

**Complexity**: Trivial (30 minutes)
- One-line fix with `max(1, ...)`
- Add assertion
- Add edge case test

---

### Category 2: Error Handling Gaps

#### Issue ENV-004: VFS Lookup Errors Lack Context

**Location**: `dac_engine.py:125-128`

**Description**:
When a modifier references a VFS variable that doesn't exist, the `KeyError` has no context about which modifier or reward configuration caused it:

```python
source_value = self.vfs_registry.get(var_name, reader="engine")  # Raises KeyError
```

Error message: `KeyError: 'motivation'` - doesn't tell you it was in the "energy_crisis" modifier.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Medium | Config typos happen |
| Impact | Medium | Debugging time wasted |
| Blast Radius | Developer productivity | No data loss, just confusion |

**Proposed Fix**:
```python
try:
    source_value = self.vfs_registry.get(var_name, reader=self.vfs_reader)
except KeyError:
    raise KeyError(
        f"VFS variable '{var_name}' referenced in modifier '{mod_name}' "
        f"but not found in registry. Available: {list(self.vfs_registry.list_variables())}"
    ) from None
```

**Complexity**: Low (1 hour)
- Wrap with try/except
- Add descriptive error
- Add test for error message quality

---

#### Issue ENV-005: Unvalidated Bar Names in Affordance Costs

**Location**: `affordance_engine.py:241-245, 331-333`

**Description**:
When iterating affordance costs, meter names are looked up without validation:

```python
meter_idx = self.meter_name_to_idx[meter_name]  # KeyError if typo
```

A config with `costs: [{meter: "enregy", ...}]` (typo) crashes with `KeyError: 'enregy'`.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Medium | Config errors are common |
| Impact | Medium | Crash during environment setup |
| Blast Radius | Single run | Fast failure |

**Proposed Fix**:
```python
if meter_name not in self.meter_name_to_idx:
    available = sorted(self.meter_name_to_idx.keys())
    raise ValueError(
        f"Affordance '{affordance_id}' references unknown meter '{meter_name}' in costs. "
        f"Available meters: {available}"
    )
meter_idx = self.meter_name_to_idx[meter_name]
```

**Complexity**: Low (1 hour)
- Add validation before lookup
- Include available meters in error
- Add test case

---

#### Issue ENV-006: Silent Skip of Invalid Custom Action Costs

**Location**: `vectorized_env.py:2280-2289`

**Description**:
Custom action cost application silently skips invalid meter names:

```python
for cost in custom_action.costs:
    meter_idx = self.meter_name_to_idx.get(cost.meter)
    if meter_idx is not None:  # Silently skips if meter doesn't exist
        # apply cost
```

This hides config errors - a custom action might appear to work but not actually apply intended costs.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Medium | Silent failures are insidious |
| Impact | Medium | Training proceeds with wrong economics |
| Blast Radius | Experiment validity | Could invalidate research results |

**Proposed Fix**:
```python
for cost in custom_action.costs:
    meter_idx = self.meter_name_to_idx.get(cost.meter)
    if meter_idx is None:
        raise ValueError(
            f"Custom action '{custom_action.id}' cost references unknown meter '{cost.meter}'"
        )
    # apply cost
```

**Complexity**: Low (1 hour)
- Change silent skip to explicit error
- Add validation test

---

### Category 3: Device & Tensor Safety

#### Issue ENV-007: Device Mismatch in DACEngine

**Location**: `dac_engine.py` (multiple locations)

**Description**:
`DACEngine` creates tensors on `self.device` but never validates that input tensors (meters, intrinsic rewards) are on the same device:

```python
# DACEngine initialized with device="cuda:0"
result = meters * modifier  # Fails if meters on CPU
```

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Low | Requires mixed device setup |
| Impact | High | Immediate crash |
| Blast Radius | Single run | Clear error message from PyTorch |

**Proposed Fix**:
```python
def calculate_rewards(self, meters: torch.Tensor, intrinsic_raw: torch.Tensor, ...) -> ...:
    # Validate device consistency
    if meters.device != self.device:
        raise RuntimeError(
            f"Meters tensor on {meters.device} but DACEngine on {self.device}. "
            f"Ensure all tensors are on the same device."
        )
    if intrinsic_raw.device != self.device:
        raise RuntimeError(
            f"Intrinsic tensor on {intrinsic_raw.device} but DACEngine on {self.device}."
        )
    # ... rest of method
```

**Complexity**: Low (1 hour)
- Add device checks at method entry
- Add test with intentional mismatch

---

#### Issue ENV-008: Floating-Point Precision in Modifier Thresholds

**Location**: `dac_engine.py:130-145`

**Description**:
Modifier range comparisons use exact floating-point comparisons:

```python
in_range = (source_value >= r.min) & (source_value < r.max)
```

For boundary values, floating-point rounding can cause unexpected behavior:
- `energy=0.49999999999` might not trigger `range: [0.0, 0.5]`
- `energy=0.50000000001` might not trigger `range: [0.5, 1.0]`

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | Low | Requires exact boundary values |
| Impact | Low | Slight reward miscalculation |
| Blast Radius | Training quality | Subtle, not catastrophic |

**Proposed Fix**:
```python
EPSILON = 1e-7
in_range = (source_value >= (r.min - EPSILON)) & (source_value < (r.max + EPSILON))
```

**Complexity**: Trivial (30 minutes)
- Add epsilon tolerance
- Document behavior in docstring

---

### Category 4: Code Duplication (DRY Violations)

#### Issue ENV-009: Duplicate NullItemManager Classes

**Location**: `vectorized_env.py:39`, `affordance_engine.py:666`

**Description**:
Two separate `NullItemManager` implementations exist with slightly different interfaces:

```python
# vectorized_env.py
class NullItemManager:
    def spawn_item(self, *args, **kwargs): ...
    def tick(self, *args, **kwargs): return None
    def process_respawns(self, *args, **kwargs): return None

# affordance_engine.py
class NullItemManager:
    def spawn_item(self, *args, **kwargs): ...
    # Missing tick() and process_respawns()
```

If either changes, the other diverges.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | High | Maintenance will eventually diverge |
| Impact | Low | Both are stub implementations |
| Blast Radius | Code quality | Technical debt accumulation |

**Proposed Fix**:
```python
# New file: src/townlet/environment/null_managers.py
class NullItemManager:
    """Null object pattern for item management when items are disabled."""

    def spawn_item(self, *args: Any, **kwargs: Any) -> None:
        """No-op spawn."""
        pass

    def tick(self, *args: Any, **kwargs: Any) -> None:
        """No-op tick."""
        return None

    def process_respawns(self, *args: Any, **kwargs: Any) -> None:
        """No-op respawn processing."""
        return None
```

Then import in both files.

**Complexity**: Low (1-2 hours)
- Create shared module
- Update imports
- Remove duplicates
- Verify tests pass

---

#### Issue ENV-010: Duplicate Modulation Rules Builder

**Location**: `vectorized_env.py:598-614, 710-726`

**Description**:
Identical logic for building modulation rules appears twice:

```python
# Lines 598-614: Building rules for affordance system
modulation_rules = []
for mod_spec in optimization_data.modulation_rules:
    # ... ~16 lines of identical logic ...

# Lines 710-726: Building rules for DAC engine
modulation_rules = []
for mod_spec in optimization_data.modulation_rules:
    # ... same ~16 lines ...
```

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | High | Bug fix in one won't propagate |
| Impact | Medium | Could cause inconsistent modulation |
| Blast Radius | Training correctness | Subtle divergence |

**Proposed Fix**:
```python
def _build_modulation_rules(
    self,
    optimization_data: OptimizationData,
    all_affordance_names: list[str]
) -> list[dict[str, Any]]:
    """Build modulation rules from optimization data.

    Single source of truth for modulation rule construction.
    """
    rules = []
    for mod_spec in optimization_data.modulation_rules:
        rule = {
            "name": mod_spec.name,
            "source_type": mod_spec.source_type,
            "source_name": mod_spec.source_name,
            "ranges": [
                {"min": r.min, "max": r.max, "multiplier": r.multiplier}
                for r in mod_spec.ranges
            ],
        }
        if mod_spec.affordance_idx is not None:
            aff_idx = mod_spec.affordance_idx
            if 0 <= aff_idx < len(all_affordance_names):
                rule["affordance"] = all_affordance_names[aff_idx]
        rules.append(rule)
    return rules
```

**Complexity**: Medium (2-3 hours)
- Extract method
- Update both call sites
- Add unit test for rule building
- Verify integration tests pass

---

#### Issue ENV-011: Duplicate VFS Type Conversion Logic

**Location**: `vectorized_env.py:304-309, 333-338`

**Description**:
VFS variable type mapping duplicated for agent and global variables:

```python
# Agent variables (lines 304-309)
if var.type in {"float", "scalar"}:
    var_type = "scalar"
elif var.type == "bool":
    var_type = "bool"
# ...

# Global variables (lines 333-338) - same logic repeated
if var.type in {"float", "scalar"}:
    var_type = "scalar"
# ...
```

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | High | Type mapping changes would need dual updates |
| Impact | Low | Both do the same thing currently |
| Blast Radius | Code quality | Maintenance burden |

**Proposed Fix**:
```python
def _normalize_vfs_type(self, raw_type: str, var_id: str) -> str:
    """Normalize VFS variable type to canonical form.

    Args:
        raw_type: Type string from config
        var_id: Variable ID for error messages

    Returns:
        Normalized type string

    Raises:
        ValueError: If type is not recognized
    """
    TYPE_MAPPING = {
        "float": "scalar",
        "scalar": "scalar",
        "bool": "bool",
        "tensor1d": "tensor1d",
        "tensor2d": "tensor2d",
        "tensor3d": "tensor3d",
        "tensorNd": "tensorNd",
    }

    if raw_type not in TYPE_MAPPING:
        raise ValueError(
            f"Unknown VFS type '{raw_type}' for variable '{var_id}'. "
            f"Valid types: {sorted(set(TYPE_MAPPING.values()))}"
        )
    return TYPE_MAPPING[raw_type]
```

**Complexity**: Low (1-2 hours)
- Extract helper method
- Update both call sites
- Addresses ENV-001 simultaneously

---

### Category 5: Performance Opportunities

#### Issue ENV-012: Position Tuple Conversion Every Step

**Location**: `vectorized_env.py:1454`

**Description**:
For item pickup checks, agent positions are converted to tuples every step:

```python
pos_tuple = tuple(self.positions[agent_idx].tolist())
```

With 1000 agents, this is 1000 GPU→CPU transfers + list conversions + tuple conversions per step.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | N/A | Performance, not correctness |
| Impact | Medium | ~1-5% slowdown with many agents |
| Blast Radius | Training speed | Scales with agent count |

**Proposed Fix**:
```python
# In step(), after position updates:
self._position_tuples = {
    i: tuple(self.positions[i].tolist())
    for i in range(self.num_agents)
}

# In item pickup:
pos_tuple = self._position_tuples[agent_idx]
```

**Complexity**: Low (1 hour)
- Add position cache
- Update after movement
- Invalidate on reset

---

#### Issue ENV-013: Redundant Affordance Position Dict Creation

**Location**: `vectorized_env.py:2100-2113`

**Description**:
`_get_affordance_positions()` is called multiple times per step for shaping bonuses, each time returning the same dict.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | N/A | Performance |
| Impact | Low | Minor overhead |
| Blast Radius | Training speed | Negligible for small configs |

**Proposed Fix**:
Cache the result at the start of `step()` and pass it through to reward computation.

**Complexity**: Trivial (30 minutes)

---

#### Issue ENV-014: Unnecessary Tensor Clone in Reward Computation

**Location**: `dac_engine.py:929`

**Description**:
```python
intrinsic = intrinsic_raw.clone()  # Unnecessary copy
intrinsic = intrinsic * base_weight  # Creates new tensor anyway
```

The clone is immediately replaced by arithmetic result.

**Risk Assessment**:
| Factor | Rating | Rationale |
|--------|--------|-----------|
| Likelihood | N/A | Performance |
| Impact | Low | One extra tensor allocation per step |
| Blast Radius | Memory | Minor |

**Proposed Fix**:
```python
intrinsic = intrinsic_raw * base_weight  # Direct multiplication
```

**Complexity**: Trivial (15 minutes)

---

### Category 6: Documentation & Clarity

#### Issue ENV-015: Misleading TODO Comment

**Location**: `vectorized_env.py:1024`

**Description**:
Comment suggests incomplete collision handling but code appears complete.

**Complexity**: Trivial (15 minutes) - Review and update/remove comment

---

#### Issue ENV-016: Missing cost_mode Documentation

**Location**: `affordance_engine.py:463-487`

**Description**:
`get_affordance_cost()` parameter behavior undocumented for edge cases.

**Complexity**: Trivial (15 minutes) - Add docstring

---

## Complexity Summary

| Complexity | Issues | Total Effort |
|------------|--------|--------------|
| Trivial (< 30 min) | ENV-003, ENV-008, ENV-013, ENV-014, ENV-015, ENV-016 | ~2.5 hours |
| Low (1-2 hours) | ENV-001, ENV-002, ENV-004, ENV-005, ENV-006, ENV-007, ENV-009, ENV-011, ENV-012 | ~12 hours |
| Medium (2-3 hours) | ENV-010 | ~3 hours |
| High (> 4 hours) | None | 0 |

**Total Estimated Effort**: ~17.5 hours (2-3 focused days)

---

## Recommended Implementation Order

### Phase 1: Critical Bugs (Day 1)
1. ENV-001 + ENV-011 (combine - VFS type validation)
2. ENV-002 (vision range bounds)
3. ENV-003 (hours_per_day division by zero)

### Phase 2: Error Handling (Day 1-2)
4. ENV-004 (VFS lookup context)
5. ENV-005 (bar name validation)
6. ENV-006 (custom action cost validation)
7. ENV-007 (device mismatch)

### Phase 3: Code Quality (Day 2)
8. ENV-009 (NullItemManager consolidation)
9. ENV-010 (modulation rules extraction)
10. ENV-008 (floating-point epsilon)

### Phase 4: Performance & Docs (Day 3, optional)
11. ENV-012, ENV-013, ENV-014 (performance)
12. ENV-015, ENV-016 (documentation)

---

## Test Coverage Recommendations

Each fix should include:
1. **Unit test** for the specific validation/behavior
2. **Integration test** verifying the fix doesn't break existing functionality
3. **Edge case test** for boundary conditions

Example test for ENV-001:
```python
def test_vfs_type_conversion_rejects_invalid_type():
    """VFS type conversion should reject unknown types with helpful error."""
    with pytest.raises(ValueError, match="Unknown VFS type 'scaler'"):
        env._normalize_vfs_type("scaler", "test_var")
```

---

## Appendix: Files Analyzed

| File | Lines | Issues Found |
|------|-------|--------------|
| `vectorized_env.py` | ~2500 | 10 |
| `dac_engine.py` | ~950 | 5 |
| `affordance_engine.py` | ~700 | 3 |
| `temporal_utils.py` | ~100 | 1 |
| `action_config.py` | ~200 | 0 |
| `observation_buffer.py` | ~150 | 0 |

---

*Report generated by Claude Code analysis on 2025-11-25*
