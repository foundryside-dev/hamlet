# Training Subsystem Audit - 2025-11-26

**Scope**: `src/townlet/training/` (7 files, 1,547 LOC)
**Auditors**: 7 parallel code review agents
**Status**: ✅ ALL ISSUES FIXED (2025-11-27)

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 7 | ✅ Fixed |
| HIGH | 9 | ✅ Fixed |
| MEDIUM | 19 | ✅ Fixed |
| LOW | 16 | ✅ Fixed |
| **TOTAL** | **51** | ✅ Complete |

---

## CRITICAL Issues (Fix Immediately)

### CRIT-01: replay_buffer.py - batch_size > capacity creates scrambled buffer
- **Location**: Lines 78-90 (push method)
- **Confidence**: 100%
- **Description**: When `batch_size > capacity`, circular buffer wraps mid-batch, creating non-contiguous scrambled state. Buffer becomes semantically invalid.
- **Example**: capacity=5, batch_size=7 → writes to indices [0,1,2,3,4,0,1] → final buffer is [item5, item6, item2, item3, item4]
- **Impact**: Silent data corruption, training instability
- **Fix**: Add validation `if batch_size > self.capacity: raise ValueError(...)`

### CRIT-02: replay_buffer.py - Serialization doesn't handle wrap-around
- **Location**: Lines 225-230 (serialize method)
- **Confidence**: 95%
- **Description**: Uses `self.observations[:self.size]` which assumes contiguous data from index 0. After wrap-around, data is not temporally ordered.
- **Impact**: Restored buffer has wrong temporal order, breaks reproducibility
- **Fix**: Reorder data during serialization to maintain temporal sequence

### CRIT-03: prioritized_replay_buffer.py - Zero division in anneal_beta
- **Location**: Line 187
- **Confidence**: 100%
- **Description**: `progress = min(current_step / total_steps, 1.0)` crashes if `total_steps=0`
- **Impact**: Runtime crash during training
- **Fix**: Add guard `if total_steps > 0`

### CRIT-04: prioritized_replay_buffer.py - Beta annealing ignores user config
- **Location**: Line 188
- **Confidence**: 95%
- **Description**: Hardcodes `self.beta = 0.4 + (1.0 - 0.4) * progress`, ignoring constructor's `beta` parameter
- **Impact**: User configuration silently ignored
- **Fix**: Store `self.beta_initial = beta` and use it in annealing formula

### CRIT-05: state.py - BatchedAgentState.to() loses info dict
- **Location**: Lines 108-124
- **Confidence**: 95%
- **Description**: `.to(device)` method transfers tensor fields but omits `info=self.info`
- **Impact**: Silent data loss when moving between devices (latent bug - currently no callers)
- **Fix**: Add `info=self.info` to the return statement

### CRIT-06: checkpoint_utils.py - Missing drive_hash validation
- **Location**: Lines 48-64 (assert_checkpoint_dimensions)
- **Confidence**: 95%
- **Description**: `attach_universe_metadata` saves `drive_hash` but validation function doesn't check it
- **Impact**: Checkpoints can load with mismatched reward functions, breaking reproducibility
- **Fix**: Add drive_hash validation similar to observation_field_uuids

### CRIT-07: Cross-cutting - DAC rewards stored as "extrinsic"
- **Location**: `population/vectorized.py:655-669`
- **Confidence**: 95%
- **Description**: DAC-composed totals stored as `rewards_extrinsic` with zeros for `rewards_intrinsic`. Semantic contract violation.
- **Impact**: Misleading field names, fragile workaround, broken checkpoint semantics
- **Fix**: Create `RewardTensor` DTO with explicit composition state (REC-01)

---

## HIGH Issues

### HIGH-01: sequential_replay_buffer.py - BUG-01 serialize/load mismatch
- **Location**: Lines 257-258, 113-117
- **Description**: `serialize()` expects split rewards but `store_episode()` accepts combined
- **Impact**: KeyError on serialize if episode used combined rewards

### HIGH-02: replay_buffer.py - BUG-02 load ignores capacity
- **Location**: Lines 233-272
- **Description**: `load_from_serialized` doesn't validate capacity match
- **Impact**: Size > capacity causes cryptic errors

### HIGH-03: Cross-cutting - BUG-08 inconsistent serialization
- **Location**: All three buffer types
- **Description**: ReplayBuffer stores split, SequentialBuffer stores split, PER stores combined
- **Impact**: Cannot switch buffer types mid-training

### HIGH-04: replay_buffer.py - Position counter unbounded
- **Location**: Line 89
- **Description**: `self.position += 1` grows forever, serialized to checkpoints
- **Impact**: Memory growth, checkpoint bloat (minor in practice)

### HIGH-05: checkpoint_utils.py - Missing brain_hash validation
- **Location**: Lines 21-30, 48-64
- **Description**: No validation for network architecture hash
- **Impact**: Can load incompatible network architectures

### HIGH-06: tensorboard_logger.py - Global step collision
- **Location**: Line 214
- **Description**: `episode * 1000 + step` collides when episodes > 1000 steps (L3 has 1440)
- **Impact**: Non-monotonic x-axis, unusable meter graphs

### HIGH-07: checkpoint_utils.py - safe_torch_load only catches RuntimeError
- **Location**: Lines 157-164
- **Description**: Other exceptions (pickle, ModuleNotFound) not handled gracefully
- **Impact**: Unhelpful error messages

### HIGH-08: checkpoint_utils.py - Silent failure in verify_checkpoint_digest
- **Location**: Lines 92-98
- **Description**: Returns False when digest missing but callers don't check
- **Impact**: Data corruption indicators silently ignored

### HIGH-09: state.py - curriculum_difficulties never populated (BUG-40)
- **Location**: Lines 68, 82, 99
- **Description**: Field always zeros, never wired to actual curriculum decisions
- **Impact**: Dead field, violates no-dead-code principle

---

## MEDIUM Issues

### Replay Buffer Performance
- **MED-01**: `replay_buffer.py:79-90` - Push uses Python loop, not vectorized (BUG-05)
- **MED-02**: `sequential_replay_buffer.py:134` - O(n) eviction via `pop(0)` (BUG-04)
- **MED-03**: `prioritized_replay_buffer.py:130-136` - O(n) sampling, needs segment tree (ENH-01)

### Validation Gaps
- **MED-04**: `replay_buffer.py` - No validation of input tensor shapes (NEW-07)
- **MED-05**: `replay_buffer.py` - No obs_dim validation on load (BUG-11)
- **MED-06**: `sequential_replay_buffer.py:112-117` - Accepts ambiguous dual reward formats (ISSUE-01)
- **MED-07**: `sequential_replay_buffer.py:114` - Partial split rewards accepted (ISSUE-02)
- **MED-08**: `prioritized_replay_buffer.py:175` - Redundant abs() on TD errors (contract unclear)

### State/Logging Gaps
- **MED-09**: `tensorboard_logger.py` - No shaping reward logging (DAC has 3 components)
- **MED-10**: `tensorboard_logger.py` - No modifier effect logging
- **MED-11**: `state.py:28` - reward_mode field may be obsolete post-DAC
- **MED-12**: `state.py:25-28` - Hardcoded max_length=6 for active_meters

### Contract Issues
- **MED-13**: Cross-cutting - `intrinsic_weight` parameter is dead (always 1.0)
- **MED-14**: `prioritized_replay_buffer.py:99-100` - PER pre-combines at push, loses flexibility
- **MED-15**: `replay_buffer.py:111` - sample() uses replacement (reduces diversity)
- **MED-16**: `replay_buffer.py:129` - Always returns mask=True, ignores post-terminal
- **MED-17**: `sequential_replay_buffer.py:269-289` - load_from_serialized ignores capacity mismatch
- **MED-18**: `checkpoint_utils.py:63` - UUID comparison is order-sensitive (undocumented)
- **MED-19**: `tensorboard_logger.py:124-138` - Multi-agent flush increments per-agent not per-episode

---

## LOW Issues

### Edge Cases
- **LOW-01**: `sequential_replay_buffer.py:120` - No zero-length episode validation
- **LOW-02**: `sequential_replay_buffer.py:33-41` - No non-positive capacity validation
- **LOW-03**: `sequential_replay_buffer.py:137` - No negative intrinsic_weight validation
- **LOW-04**: `prioritized_replay_buffer.py:104,116` - Position counter modulo inconsistency
- **LOW-05**: `checkpoint_utils.py:21,48` - No None check for universe parameter
- **LOW-06**: `checkpoint_utils.py:100` - Implicit strip() contract for digest files
- **LOW-07**: `checkpoint_utils.py:15` - Magic string for digest suffix
- **LOW-08**: `tensorboard_logger.py:99,144...` - Empty agent_id creates malformed metrics
- **LOW-09**: `state.py:126-137` - detach_cpu_summary() never called (dead code?)
- **LOW-10**: `state.py:84,101` - No type hints for info dict contents

### Code Quality
- **LOW-11**: `replay_buffer.py:71-76` - Redundant .to(device) calls
- **LOW-12**: `tensorboard_logger.py:113-114` - Duplicate condition check
- **LOW-13**: `replay_buffer.py` - ENH-02 preallocation/dtype/pin_memory options
- **LOW-14**: `sequential_replay_buffer.py:184` - Sampling bias toward uniform episodes (BUG-10)
- **LOW-15**: `sequential_replay_buffer.py:119-123` - No tensor shape validation
- **LOW-16**: `prioritized_replay_buffer.py:136` - Sampling without replacement caps at buffer size

---

## Architectural Recommendations

### REC-01: Unified Reward Contract (CRITICAL)
Create explicit `RewardTensor` DTO:
```python
@dataclass
class RewardTensor:
    total: torch.Tensor
    extrinsic: torch.Tensor | None = None
    intrinsic: torch.Tensor | None = None
    is_composed: bool = True
```

### REC-02: Abstract Buffer Interface (HIGH)
```python
class ReplayBufferProtocol(Protocol):
    def push(...) -> None: ...
    def sample(...) -> dict[str, Tensor]: ...
    def serialize() -> dict[str, Any]: ...  # Must include buffer_type, format_version
```

### REC-03: Remove Dead intrinsic_weight Parameter (MEDIUM)
Remove from `ReplayBuffer.sample()` and `SequentialReplayBuffer.sample_sequences()`

### REC-04: Add Buffer Metadata to Checkpoints (MEDIUM)
```python
checkpoint["replay_buffer"] = {
    "buffer_type": "standard" | "sequential" | "prioritized",
    "format_version": 1,
    "reward_format": "dac_composed",
}
```

---

## Fix Order (Recommended)

1. **CRIT-01**: batch_size > capacity guard (5 min, prevents corruption)
2. **CRIT-03**: Zero division guard (2 min, prevents crash)
3. **CRIT-04**: Beta annealing fix (5 min, respects config)
4. **CRIT-05**: BatchedAgentState.to() fix (2 min, prevents data loss)
5. **CRIT-06**: drive_hash validation (10 min, reproducibility)
6. **CRIT-02**: Serialization wrap-around (30 min, complex)
7. **CRIT-07**: RewardTensor DTO (2-4 hours, architectural)

---

## Test Coverage Gaps

1. No test for `batch_size > capacity`
2. No test for serialization after wrap-around
3. No test for `anneal_beta` with `total_steps=0`
4. No test for beta annealing with non-0.4 initial value
5. No test for `BatchedAgentState.to()` with info dict
6. No test for drive_hash/brain_hash validation
7. No test for capacity mismatch during load
