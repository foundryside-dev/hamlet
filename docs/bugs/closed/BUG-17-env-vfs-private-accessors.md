Title: Vectorized env uses VFS private attributes for presence checks

Severity: low
Status: FIXED

Subsystem: environment/vectorized + VFS
Affected Version/Branch: main

Affected Files:
- `src/townlet/environment/vectorized_env.py:1269` (observation field check)
- `src/townlet/environment/vectorized_env.py:1781` (velocity_x check)
- `src/townlet/environment/vectorized_env.py:1784` (velocity_y check)
- `src/townlet/environment/vectorized_env.py:1787` (velocity_z check)
- `src/townlet/environment/vectorized_env.py:1791` (velocity_magnitude check)

Description:
- The environment probed `self.vfs_registry._definitions` (private attribute) to check if variables exist before write.
- This coupled the env to internal VFS structures and bypassed any future invariants the registry might impose.

Reproduction:
- Read code; private member access is brittle by design.

Expected Behavior:
- Use the public `.variables` property exposed by the registry to check variable presence.

Actual Behavior:
- Access to `._definitions` directly (FIXED: now uses `.variables`).

Root Cause:
- Used private attribute instead of existing public API (`.variables` property was already available).

Fix Applied:
- Replaced all 5 instances of `._definitions` with `.variables` property
- Added tests to verify public API usage in `tests/test_townlet/unit/environment/test_vectorized_env.py`
- Tests confirm that variable presence checks work correctly using public API

Migration Impact:
- None for users; internal refactor only. No breaking changes.

Alternatives Considered:
- Add `contains(name: str) -> bool` method (unnecessary - `.variables` dict already supports `in` operator)
- Try/except around `set`; heavier and less clear.

Tests:
- `TestVFSVariableAccess::test_vfs_variable_presence_check_uses_public_api`
- `TestVFSVariableAccess::test_velocity_variables_check_uses_public_api`

Owner: env+vfs
Fixed: 2025-11-29
