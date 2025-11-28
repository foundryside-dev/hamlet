# Exploration Module Audit - Bug Fixes

**Date**: 2025-11-28
**Status**: Complete
**Tests**: 2591 passing

## Overview

Systematic audit of the exploration module (`src/townlet/exploration/`) identified and fixed 9 bugs affecting RND (Random Network Distillation) intrinsic motivation and adaptive exploration annealing.

## Critical Bug: Variance Collapse (EXP-01)

### Problem

The `RunningMeanStd` class used for normalizing intrinsic rewards was initialized with `count=epsilon=1e-4`. When early prediction errors (MSE) were small (0.001-0.01 range), the variance collapsed rapidly, causing normalized intrinsic rewards to explode by 10-100x.

**Reproduction scenario**:
```python
rms = RunningMeanStd(epsilon=1e-4)  # count = 0.0001
rms.update(np.array([0.001]))        # First batch with small MSE
# Variance collapses to ~0.0001

# Normalization: mse / sqrt(var) = 0.5 / 0.01 = 50.0
# Expected: ~0.5, Actual: 50.0 (100x inflation!)
```

**Impact on training**:
- Intrinsic rewards dominate extrinsic rewards in early training
- Agent explores excessively instead of learning task
- Reward signal becomes non-stationary, destabilizing Q-learning

### Solution

```python
class RunningMeanStd:
    MIN_VAR = 0.01  # Variance floor

    def __init__(self, initial_count: int = 100):  # Was: epsilon=1e-4
        self.count = float(initial_count)  # 100 pseudo-samples for stability
```

Plus variance floor in normalization:
```python
effective_var = max(self.reward_rms.var, RunningMeanStd.MIN_VAR)
normalized = mse / (np.sqrt(effective_var) + 1e-8)
```

**Files**: `rnd.py:17-44`, `rnd.py:231-233`

---

## Medium Bugs

### EXP-02: Missing Gradient Clipping in RND Training

**Problem**: RND predictor training had no gradient clipping, while Q-network uses `max_grad_norm=10.0`. Novel states can produce large prediction errors → exploding gradients.

**Solution**: Added gradient clipping before optimizer step:
```python
torch.nn.utils.clip_grad_norm_(self.predictor_network.parameters(), max_norm=10.0)
```

**File**: `rnd.py:279-282`

---

### EXP-03: Incomplete Checkpoint State

**Problem**: `obs_buffer` (up to 127 pending observations) was not saved in checkpoints, causing non-deterministic restoration.

**Solution**: Save and restore obs_buffer:
```python
# checkpoint_state()
"obs_buffer": [obs.cpu() for obs in self.obs_buffer]

# load_state()
self.obs_buffer = [obs.to(self.device) for obs in state.get("obs_buffer", [])]
```

**File**: `rnd.py:343-344`, `rnd.py:379-381`

---

### EXP-04: Missing obs_dim Validation on Checkpoint Load

**Problem**: Loading a checkpoint from a different curriculum level (e.g., L0 obs_dim=29 into L2 obs_dim=54) produced cryptic PyTorch errors.

**Solution**: Validate obs_dim before loading:
```python
if checkpoint_obs_dim != self.obs_dim:
    raise ValueError(
        f"Checkpoint obs_dim mismatch: checkpoint has {checkpoint_obs_dim}, "
        f"current environment has {self.obs_dim}."
    )
```

**File**: `rnd.py:358-365`

---

### EXP-05: Missing Parameter Validation in AdaptiveIntrinsicExploration

**Problem**: No validation of configuration parameters. `decay_rate > 1.0` would **increase** exploration weight over time (opposite of intended behavior).

**Solution**: Added validation in `__init__`:
```python
if not 0.0 < decay_rate < 1.0:
    raise ValueError(
        f"decay_rate must be in (0, 1), got {decay_rate}. "
        f"Values >= 1 would increase exploration weight over time."
    )
if variance_threshold <= 0:
    raise ValueError(...)
if survival_window < 10:
    raise ValueError(...)  # Minimum for variance calculation
```

**File**: `adaptive_intrinsic.py:65-84`

---

### EXP-08: Missing Epsilon Shape Validation

**Problem**: `epsilon_greedy_action_selection()` didn't validate epsilon tensor shape. A 2D tensor `[1, batch]` would silently broadcast incorrectly.

**Solution**: Added shape validation:
```python
if epsilons.ndim != 1:
    raise ValueError(f"epsilons must be 1D tensor, got shape {epsilons.shape}")
if epsilons.shape[0] != batch_size:
    raise ValueError(f"epsilons batch size {epsilons.shape[0]} != q_values batch {batch_size}")
```

**File**: `action_selection.py:44-54`

---

## Low Priority Fixes

### EXP-06: Remove Unused Device Field

**Problem**: `AdaptiveIntrinsicExploration.device` was stored but never used (RND handles device internally).

**Solution**: Removed the field to prevent future confusion.

**File**: `adaptive_intrinsic.py:108`

---

### EXP-07: Type Annotation Mismatch

**Problem**: `update_on_episode_end(survival_time: float)` but survival times are always integers (step counts).

**Solution**: Changed type to `int`:
```python
def update_on_episode_end(self, survival_time: int) -> None:
    ...
self.survival_history: list[int] = []
```

**File**: `adaptive_intrinsic.py:112`, `adaptive_intrinsic.py:161-171`

---

## DRL Considerations

### Why Variance Collapse Matters

In RND-based intrinsic motivation:
1. **Novelty signal** = MSE between fixed (random) network and predictor network
2. **Normalization** divides by running std to keep intrinsic rewards comparable to extrinsic
3. **If variance collapses**: normalization inflates small MSE values → intrinsic >> extrinsic

This is particularly problematic because:
- Early in training, predictor learns quickly → MSE drops
- With `count=1e-4`, a few batches dominate variance calculation
- Result: variance tracks MSE closely, then normalizing by sqrt(var) ≈ normalizing by MSE itself → always ~1.0

The fix ensures variance stays stable longer, allowing the agent to balance exploration and exploitation properly.

### Impact on Training Dynamics

| Phase | Before Fix | After Fix |
|-------|-----------|-----------|
| Episode 1-10 | Intrinsic rewards 10-100x extrinsic | Intrinsic ~ extrinsic |
| Episode 10-100 | Erratic reward signal | Stable normalization |
| Convergence | Delayed/unstable | Normal learning curve |

### Gradient Clipping Rationale

RND prediction error can spike when agent visits truly novel states (e.g., first time reaching a new affordance). Without gradient clipping:
- Large MSE → large gradients → unstable predictor
- Unstable predictor → noisy intrinsic rewards → noisy Q-targets

The `max_norm=10.0` matches the Q-network clipping for consistency.

---

## Test Coverage

Updated tests in `tests/test_townlet/unit/exploration/test_rnd_normalization.py`:
- `test_intrinsic_rewards_are_stable_order_of_magnitude` - verifies no reward explosion
- `test_normalized_rewards_are_stable_after_warmup` - verifies stability after predictor learning
- `test_normalization_is_persistent_across_checkpoints` - verifies checkpoint consistency
- `test_adaptive_applies_weight_only_once` - verifies no double-weighting

---

## Files Modified

- `src/townlet/exploration/rnd.py` (EXP-01, EXP-02, EXP-03, EXP-04)
- `src/townlet/exploration/adaptive_intrinsic.py` (EXP-05, EXP-06, EXP-07)
- `src/townlet/exploration/action_selection.py` (EXP-08)
- `tests/test_townlet/unit/exploration/test_rnd_normalization.py` (test updates)

---

## DRL Expert Review (2025-11-28)

**Grade: B+** - Solid bug fixes, but missing configurability and curriculum considerations.

### Strengths Identified
- Variance collapse fix is critical and correctly implemented
- Gradient clipping prevents exploding gradients
- Checkpoint improvements enhance reproducibility
- Parameter validation catches catastrophic misconfigurations

### Issues Raised for Future Work

#### HIGH PRIORITY

**1. Hardcoded hyperparameters violate no-defaults principle**

`initial_count=100` and `MIN_VAR=0.01` should be configurable in `training.yaml`:
```yaml
intrinsic:
  rnd:
    normalization:
      initial_count: 100
      min_variance: 0.01
```

**2. Absolute variance threshold doesn't scale across curriculum levels**

L0 (500 max steps) has different survival variance than L3 (1000 max steps). Use coefficient of variation instead:
```python
cv = std_survival / (mean_survival + 1e-8)
return cv < self.cv_threshold and mean_survival > self.min_survival_for_annealing
```

**3. Missing reward clipping per Burda et al. (2018)**

Paper clips rewards to [-5, 5] after normalization:
```python
clipped = torch.clamp(normalized, min=0.0, max=5.0)
```

**4. Potential annealing feedback loop**

When intrinsic weight drops → less exploration → lower variance → faster annealing → feedback loop. Add hysteresis:
```python
self.annealing_cooldown = 100  # Episodes between annealing triggers
```

#### MEDIUM PRIORITY

**5. RND training_batch_size should match Q-network**

Currently hardcoded to 128, Q-network uses 256. Make configurable.

**6. Active mask may break transfer learning**

Masking >50% of observations could destroy spatial information needed for curriculum progression.

#### LOW PRIORITY (Future Work)

- Consider EMA normalization for non-stationary distributions
- Add batch normalization to RND networks (per Burda et al.)
- Log RND predictor loss to TensorBoard

### Literature Alignment

**Burda et al. (2018) "Exploration by Random Network Distillation"**:
- ✅ Normalizing by running std of prediction errors
- ✅ Training predictor with gradient descent
- ⚠️ Missing: Batch normalization in networks
- ⚠️ Missing: Reward clipping to [-5, 5]

---

## Action Items

| Priority | Item | Status |
|----------|------|--------|
| HIGH | Make `initial_count` configurable | ✅ DONE (RNDNormalizationConfig.initial_count) |
| HIGH | Make `MIN_VAR` configurable | ✅ DONE (RNDNormalizationConfig.min_variance) |
| HIGH | Use CV for annealing threshold | ✅ DONE (AnnealingConfig.use_coefficient_of_variation) |
| HIGH | Add reward clipping (0-5) | ✅ DONE (RNDNormalizationConfig.reward_clip_max) |
| MEDIUM | Add annealing hysteresis | ✅ DONE (AnnealingConfig.hysteresis_cooldown) |
| MEDIUM | Match RND batch size to Q-network | ✅ DONE (RNDConfig.batch_size) |
| LOW | Add active_mask validation | ✅ DONE (EXP-09: length check + >50% warning) |

### Implementation Notes (2025-11-28)

All action items completed. Changes:

**Config DTOs** (`training_v2_config.py`):
- Added `RNDNormalizationConfig` with `initial_count`, `min_variance`, `reward_clip_max`
- Added `batch_size` to `RNDConfig`
- Added `use_coefficient_of_variation`, `hysteresis_cooldown` to `AnnealingConfig`

**Runtime** (`rnd.py`, `adaptive_intrinsic.py`):
- `RunningMeanStd` accepts configurable `initial_count`, `min_variance`
- Reward clipping added to `compute_intrinsic_rewards()`
- CV mode and hysteresis in `should_anneal()`
- EXP-09: `active_mask` validation - length check (error) + >50% masked warning

**Configs**: All 23 `training.yaml` files updated with new fields.

**Tests**: Added `TestActiveMaskValidation` class in `test_rnd_normalization.py`.
