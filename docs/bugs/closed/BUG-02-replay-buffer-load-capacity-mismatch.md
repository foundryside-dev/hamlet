Title: ReplayBuffer.load_from_serialized ignores saved capacity

Severity: high
Status: fixed

Subsystem: training/replay-buffer (standard)
Affected Version/Branch: main

Affected Files:
- `src/townlet/training/replay_buffer.py:167`
- `src/townlet/training/replay_buffer.py:176`

Description:
- `serialize()` records `capacity`, but `load_from_serialized()` neither validates nor adopts it.
- Restoring into a buffer with different `capacity` can silently truncate/overflow later operations or mislead tests.

Reproduction:
1) Create buffer with capacity=100; push 100 transitions; serialize.
2) Create buffer with capacity=50; load from serialized state.
3) No error raised; internal tensors sized for 50, but metadata indicates 100 items → inconsistent state.

Expected Behavior:
- Validate `capacity` equality and raise a clear error, or adopt the serialized capacity and reinitialize storage.

Actual Behavior:
- No validation; potential silent misconfiguration.

Root Cause:
- `load_from_serialized` never checks `state["capacity"]`.

Proposed Fix (Breaking OK):
- Strict mode: if `state["capacity"] != self.capacity`, raise `ValueError` with remediation hint.
- Optional alternative: accept a `strict: bool = True` flag or always adopt serialized capacity by reinitializing storages.

Migration Impact:
- Callers restoring checkpoints must construct buffers with matching capacity (or update to new constructor behavior if we adopt capacity).

Alternatives Considered:
- Silent adoption of capacity; less surprising but hides configuration drift.

Tests:
- Roundtrip test with matching capacity (should pass).
- Negative test with mismatched capacity (should raise).

Owner: training
Links:
- N/A

## Fix Implementation

**Date Fixed**: 2025-11-29
**Commit**: RC-Prep branch

**Changes Made**:

1. **Added capacity validation** in `ReplayBuffer.load_from_serialized()` (line 390-398):
   - Checks if `state["capacity"]` matches `self.capacity`
   - Raises clear `ValueError` with actionable remediation message if mismatch detected
   - Error message explains both options: recreate buffer with matching capacity OR regenerate checkpoint

2. **Added comprehensive tests** in `tests/test_townlet/unit/training/test_replay_buffers.py`:
   - `test_load_capacity_mismatch_raises_error`: Verifies that mismatched capacity raises ValueError
   - `test_load_matching_capacity_succeeds`: Verifies that matching capacity loads successfully

**Error Message**:
```
Cannot load replay buffer: saved capacity (100) does not match current buffer capacity (50).
Either recreate the buffer with capacity=100 or regenerate the checkpoint with the current capacity setting.
```

**Philosophy**: Following CLAUDE.md principle of "fail loudly" for pre-release project - no backwards compatibility, no silent fallbacks. Configuration drift must be detected immediately.
