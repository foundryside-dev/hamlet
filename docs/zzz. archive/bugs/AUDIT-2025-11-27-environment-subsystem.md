# Environment Subsystem Audit - 2025-11-27

**Scope**: `src/townlet/environment/` (5,559 LOC across 13 files)
**Auditors**: 4 parallel code review agents
**Status**: VERIFICATION COMPLETE (2025-11-27)

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 3 | 1 Fixed, 2 Low Risk/False Positive |
| HIGH | 18 | 3 Fixed, 1 Real (delete dead code), 2 Low Risk, 12 False Positive |
| MEDIUM | 16 | Pending |
| LOW | 10 | Pending |
| **TOTAL** | **47** | 4 Fixed, 2 Low Risk, 14 False Positives |

---

## File Breakdown

| File | LOC | CRITICAL | HIGH | MEDIUM | LOW |
|------|-----|----------|------|--------|-----|
| vectorized_env.py | 2,426 | 0 | 8 | 7 | 5 |
| dac_engine.py | 1,005 | 3 | 5 | 5 | 0 |
| affordance_engine.py | 682 | 0 | 3 | 2 | 3 |
| Remaining files | ~1,446 | 0 | 2 | 2 | 2 |

---

## CRITICAL Issues (Fix Immediately)

### CRIT-01: dac_engine.py - Polynomial strategy NaN with negative bars ✅ FIXED
- **Location**: `_compute_polynomial()` method, line 343
- **Confidence**: 95%
- **Description**: Polynomial strategy raises bars to fractional exponents. If a bar becomes negative (e.g., due to cascade overflow), `(-0.1)^0.5` produces NaN, silently corrupting reward signals.
- **Impact**: Training instability, silent reward corruption
- **Fix**: Added `bar_value_safe = torch.clamp(bar_value, min=0.0)` before `torch.pow()`

### CRIT-02: dac_engine.py - Exponential transform overflow to Inf (LOW RISK)
- **Location**: `_apply_transform()` method with `type: exponential`
- **Confidence**: 90%
- **Description**: `torch.exp(scale * value)` can overflow to `Inf` for large values (e.g., scale=2.0, value=400 → exp(800) = Inf).
- **Impact**: Gradient explosion, training crash
- **Status**: LOW RISK - Bars are normalized to [0,1], would need bar > 88 to overflow. Deferred.

### CRIT-03: dac_engine.py - Division by zero in approach reward (FALSE POSITIVE)
- **Location**: `_compute_approach_reward()` method
- **Confidence**: 85% (may be protected by Pydantic validation)
- **Description**: Original audit reported `bonus / distance` but actual code divides by `max_distance` (config param), not `distances`.
- **Impact**: None - was a false positive
- **Status**: FALSE POSITIVE - Division is by `max_distance` (config), not `distances`

---

## HIGH Issues

### vectorized_env.py

#### HIGH-01: Per-agent step count used as global tick ✅ FIXED
- **Location**: Lines 1631, 1661, 1685, 2058
- **Description**: Global tick derived from agent 0's step count. If agent 0 dies/resets early, global tick drifts from actual simulation time.
- **Impact**: Time-based mechanics (L3) become desynchronized
- **Fix**: Added `self.global_tick` counter, initialized in `__init__`, incremented in `step()`, reset in `reset()`. Replaced all 4 usages.

#### HIGH-02: Direct VFS registry storage access bypasses access control ✅ FIXED
- **Location**: Lines 1647, 1648, 1674
- **Description**: Code bypasses `read()`/`write()` methods that enforce access control, defeating VFS security model.
- **Impact**: Access control violations go undetected
- **Fix**: Replaced `_storage` access with `vfs_registry.get()`/`set()` API. Added dtype casting for compatibility.

#### HIGH-03: VFS agent profile evaluation missing (FALSE POSITIVE)
- **Location**: Agent initialization and step logic
- **Description**: VFS agent profiles should modify observation building but evaluation path appears incomplete.
- **Impact**: None
- **Status**: FALSE POSITIVE - By design, only global profiles have expression evaluation. Agent profiles define storage variables, not computed expressions.

#### HIGH-04: Terminal conditions checked before effects applied (FALSE POSITIVE)
- **Location**: `_check_terminal_conditions()` call ordering
- **Description**: Terminal check runs before meter effects are fully applied.
- **Impact**: None
- **Status**: FALSE POSITIVE - Code correctly executes: deplete meters → cascades → effects → VFS → terminal check. Order is correct.

#### HIGH-05: Missing validation for action mask shape (FALSE POSITIVE)
- **Location**: Action masking logic
- **Description**: Action mask shape not validated against action space dimension.
- **Impact**: None
- **Status**: FALSE POSITIVE - Mask is created by `ActionBuilder.get_base_action_mask()` with shape `[num_agents, action_dim]`. Shape is guaranteed correct by construction.

#### HIGH-06: Affordance position iteration order non-deterministic (FALSE POSITIVE)
- **Location**: Affordance processing loops
- **Description**: Dict iteration order may vary across runs.
- **Impact**: None
- **Status**: FALSE POSITIVE - Python 3.7+ guarantees dict insertion order. Affordances populated from ordered list in config.

#### HIGH-07: Velocity written to VFS without shape validation (FALSE POSITIVE)
- **Location**: Velocity update in continuous substrates
- **Description**: Velocity tensor written to VFS without validating shape.
- **Impact**: None
- **Status**: FALSE POSITIVE - VFS registry.set() enforces expected shapes on write. Velocity components correctly extracted as `[num_agents]` tensors.

#### HIGH-08: Missing retirement check for dead agents (LOW RISK)
- **Location**: Agent state management
- **Description**: Dead agents may not be properly retired from VFS registry, leaving stale state.
- **Impact**: Minimal - vectorized design resets entire population together
- **Status**: LOW RISK - VFS registry has no `retire_agent()` method. Vectorized architecture handles this via population reset. Dead agents are masked and cannot act. Agent-scoped VFS state persists until episode reset but doesn't cause issues.

### dac_engine.py

#### HIGH-04: Hybrid strategy bar indexing without bounds check (FALSE POSITIVE)
- **Location**: `_compute_hybrid()` method
- **Description**: Bar indices accessed without validating they exist in current environment config.
- **Impact**: None
- **Status**: FALSE POSITIVE - `_get_bar_index()` method explicitly validates bar existence with KeyError. Same validation used by all strategies. Test coverage confirms.

#### HIGH-05: Modifier range evaluation order-dependent (FALSE POSITIVE)
- **Location**: Modifier application logic
- **Description**: Multiple modifiers applied in dict iteration order which isn't guaranteed.
- **Impact**: None
- **Status**: FALSE POSITIVE - `apply_modifiers` is a LIST, not a dict. Order is explicitly controlled via config YAML. Dict is only used for lookups.

#### HIGH-06: Missing NaN check on final reward (LOW RISK)
- **Location**: End of `compute_rewards()` method
- **Description**: No validation that final reward tensor is finite before returning.
- **Impact**: Theoretical - mitigated by existing safeguards
- **Status**: LOW RISK - Polynomial NaN prevention via clamping, bars normalized [0,1], no division by zero, dead agents zeroed out. Never observed in practice.

#### HIGH-07: Shaping bonus accumulation without overflow check (FALSE POSITIVE)
- **Location**: Shaping bonus loop
- **Description**: Multiple shaping bonuses added without checking for overflow.
- **Impact**: None
- **Status**: FALSE POSITIVE - Float32 range is [-3.4e38, +3.4e38]. All shaping bonuses bounded by design. Even 11 types with typical weights cannot approach float32 limits.

#### HIGH-08: VFS variable access in shaping without existence check (FALSE POSITIVE)
- **Location**: `vfs_variable` shaping bonus type
- **Description**: Accesses VFS variable without checking it exists in registry.
- **Impact**: None
- **Status**: FALSE POSITIVE - VFS `registry.get()` validates existence and raises KeyError. This is intentional fail-fast design, not a bug.

### affordance_engine.py

#### HIGH-09: Hardcoded action space dimensions in dead code ✅ DELETE
- **Location**: `get_action_masks()` method, lines 387-445
- **Description**: Unused method with hardcoded `num_affordances = 15`. Violates config-driven design.
- **Impact**: Code quality, potential confusion
- **Status**: REAL - Dead code should be deleted per CLAUDE.md anti-pattern. Action masking handled by `vectorized_env.py`.
- **Fix**: Delete `get_action_masks()` method from AffordanceEngine

#### HIGH-10: Tensor aliasing bug in effects execution (FALSE POSITIVE)
- **Location**: Effects application loop
- **Description**: Tensor views may alias underlying storage.
- **Impact**: None
- **Status**: FALSE POSITIVE - Code uses dictionary entry replacement (`self.bars[name] = value`), not in-place modification. Original views unchanged. `.clone()` already used at lines 634-635.

#### HIGH-11: Missing validation for empty dict cost format (FALSE POSITIVE)
- **Location**: Cost parsing logic
- **Description**: Empty dict `{}` accepted as valid cost.
- **Impact**: None
- **Status**: FALSE POSITIVE - Empty dicts intentionally supported for free affordances. `_iter_costs({})` returns empty iterator, loop doesn't execute. Configs use `costs: {}` by design.

### Remaining Files

#### HIGH-12: No validation for empty custom actions list (FALSE POSITIVE)
- **Location**: `ActionBuilder.__init__()` or `build()` method
- **Description**: Empty custom actions list accepted but may cause issues with action space construction.
- **Impact**: None
- **Status**: FALSE POSITIVE - `substrate.get_default_actions()` ALWAYS provides base actions (4-16 depending on substrate type). Custom actions are additive. Test `test_action_space_builder_substrate_only()` explicitly validates this scenario.

#### HIGH-13: Potential division by zero in cascade logic (FALSE POSITIVE)
- **Location**: Cascade computation, meter_dynamics.py lines 141-144, 207-212
- **Description**: Cascade divisor may be zero in edge cases.
- **Impact**: None
- **Status**: FALSE POSITIVE - Guard `if not low_mask.any(): continue` prevents division when mask is empty. When threshold=0.0, `low_mask = (values < 0.0)` is always False (meters clamped to [0,1]), so division is never reached.

---

## MEDIUM Issues

### vectorized_env.py (7 issues)

- **MED-01**: Observation building could be vectorized further
- **MED-02**: Reset logic duplicated between soft and hard reset
- **MED-03**: Magic numbers in reward clipping (should be configurable)
- **MED-04**: Missing docstring on several internal methods
- **MED-05**: Unnecessary tensor copies in observation gathering
- **MED-06**: Debug logging overhead in hot path
- **MED-07**: Episode statistics tracking incomplete

### dac_engine.py (5 issues)

- **MED-08**: Bonus type dispatch uses if-elif chain (could use registry pattern)
- **MED-09**: Modifier logging verbose in normal operation
- **MED-10**: Transform caching opportunity missed
- **MED-11**: Hardcoded epsilon values (should be configurable)
- **MED-12**: Missing type hints on helper methods

### affordance_engine.py (2 issues)

- **MED-13**: Effect application could be batched across agents
- **MED-14**: Cooldown tracking uses Python dict (could use tensor)

### Remaining Files (2 issues)

- **MED-15**: Action label resolution inefficient (rebuilds mapping each call)
- **MED-16**: Cascade graph not validated for cycles

---

## LOW Issues

### vectorized_env.py (5 issues)

- **LOW-01**: Unused import statements
- **LOW-02**: Inconsistent variable naming (snake_case vs camelCase in comments)
- **LOW-03**: TODO comments without tracking
- **LOW-04**: Test-only code paths in production file
- **LOW-05**: Redundant type assertions

### affordance_engine.py (3 issues)

- **LOW-06**: Legacy parameter names in docstrings
- **LOW-07**: Unused local variables
- **LOW-08**: Overly broad exception catch

### Remaining Files (2 issues)

- **LOW-09**: Inconsistent error message formatting
- **LOW-10**: Missing `__all__` exports

---

## Architectural Recommendations

### REC-01: Separate Global Time from Agent Time (HIGH)
Create explicit `SimulationClock` component:
```python
@dataclass
class SimulationClock:
    global_tick: int = 0
    ticks_per_day: int = 24

    def advance(self) -> None:
        self.global_tick += 1

    @property
    def time_of_day(self) -> float:
        return (self.global_tick % self.ticks_per_day) / self.ticks_per_day
```

### REC-02: Add Numerical Stability Guard to DAC (CRITICAL)
```python
def _safe_reward(self, reward: torch.Tensor) -> torch.Tensor:
    """Clamp and validate reward tensor."""
    reward = torch.clamp(reward, min=-1e6, max=1e6)
    if not torch.isfinite(reward).all():
        logger.warning("Non-finite rewards detected, clamping")
        reward = torch.nan_to_num(reward, nan=0.0, posinf=1e6, neginf=-1e6)
    return reward
```

### REC-03: VFS Access Audit (HIGH)
Grep codebase for `._storage` access and replace with proper API:
```bash
grep -r "_storage" src/townlet/environment/
```

### REC-04: Effect Ordering Specification (MEDIUM)
Document and enforce effect application order:
1. Meter deltas (from actions)
2. Cascade effects (meter-to-meter)
3. Time-based decay
4. Terminal condition check

---

## Fix Order (Recommended)

1. **CRIT-01**: Polynomial NaN guard (5 min, prevents silent corruption)
2. **CRIT-02**: Exponential overflow clamp (5 min, prevents crash)
3. **CRIT-03**: Division by zero guard (5 min, prevents crash)
4. **HIGH-01**: Global tick separation (30 min, L3 correctness)
5. **HIGH-02**: VFS access control (1 hour, security)
6. **HIGH-04**: Terminal condition ordering (15 min, correctness)
7. **HIGH-06**: Final reward NaN check (5 min, training stability)
8. Remaining HIGH issues (2-3 hours)
9. MEDIUM issues (batch cleanup)
10. LOW issues (code quality sweep)

---

## Test Coverage Gaps

1. No test for polynomial strategy with negative bar values
2. No test for exponential transform with large inputs
3. No test for approach reward at zero distance
4. No test for global tick vs agent tick drift
5. No test for VFS access control enforcement
6. No test for effect application ordering
7. No test for cascade cycle detection

---

## Related Documentation

- Training subsystem audit: `docs/bugs/AUDIT-2025-11-26-training-subsystem.md` (✅ ALL FIXED)
- VFS integration guide: `docs/vfs-integration-guide.md`
- DAC configuration: `docs/config-schemas/drive_as_code.md`
