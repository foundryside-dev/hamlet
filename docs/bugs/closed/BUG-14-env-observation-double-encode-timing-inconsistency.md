Title: step() recomputes observations twice per step; time-of-day inconsistency

Severity: medium
Status: FIXED

Subsystem: environment/vectorized
Affected Version/Branch: main

Affected Files:
- `src/townlet/environment/vectorized_env.py:1710-1730` (FIXED)

Description:
- `_calculate_shaped_rewards` calls `_get_observations()` to compute intrinsic rewards, then `step()` recomputes observations for return.
- `time_of_day` increments after rewards; observations used for intrinsic are computed with previous time, while returned observations use the incremented time.

Reproduction:
- Step environment with temporal features enabled and an exploration module that uses observations for intrinsic reward; log `time_sin/cos` differences.

Expected Behavior:
- Single observation per step or at least consistent temporal encoding between intrinsic computation and returned observation.

Actual Behavior:
- Two encodes; intrinsic sees t, returned obs sees t+1.

Root Cause:
- `_calculate_shaped_rewards` calls `_get_observations()` before `time_of_day` increments; `step()` increments time and calls `_get_observations()` again.

Fix Applied:
- Moved `time_of_day` increment to occur BEFORE `_calculate_shaped_rewards()` call (line 1710-1716).
- Both `_get_observations()` calls (inside rewards calculation and final return) now see the same `time_of_day` value.
- Added comprehensive test `test_temporal_consistency_in_step` to verify temporal features are consistent.

Migration Impact:
- Intrinsic computation semantics change slightly; intrinsic rewards now computed with observations from step T+1 instead of step T.
- This is the correct behavior: rewards should reflect the state AFTER the action.

Alternatives Considered:
- Cache obs pre-step and post-step separately; increases complexity and still duplicates work.
- Compute observation once and pass to both functions; would require larger refactor.

Tests:
- Added `tests/test_townlet/unit/environment/test_vectorized_env.py::TestVectorizedHamletEnvStep::test_temporal_consistency_in_step`
- Test verifies `time_sin` and `time_cos` values match expected values based on current `time_of_day`.

Owner: environment
Fixed: 2025-11-29
