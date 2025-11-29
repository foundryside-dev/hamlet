Title: RND.get_novelty_map hardcodes observation slices (64:70) and grid flattening

Severity: medium
Status: FIXED

Subsystem: exploration/RND
Affected Version/Branch: main

Affected Files:
- `src/townlet/exploration/rnd.py:281` (meters slice 64:70)

Description:
- `get_novelty_map` constructs a fake observation by setting a one-hot grid cell and meters slice to 0.5 using hardcoded indices.
- This breaks when observation layout/size differs from the assumed 70-dim layout.

Reproduction:
- Use a universe with different obs_dim or meter count; call `get_novelty_map` → out-of-bounds or nonsense placements.

Expected Behavior:
- Build observations based on the compiler’s observation spec (field slices), not hardcoded indices.

Actual Behavior:
- Hardcoded indices; function becomes invalid outside legacy layouts.

Root Cause:
- Legacy assumptions baked into debug visualization helper.

Resolution:
- Method deleted entirely (see CLAUDE.md pre-release policy: delete unused code rather than maintain it)
- Grep search confirmed method was never called in codebase (only defined, never invoked)
- Added comment in rnd.py explaining deletion rationale
- Method had hardcoded assumptions (70-dim obs, meters at 64:70, one-hot grid encoding) incompatible with VFS-based observation layouts

Fix Commit:
- Deleted get_novelty_map() from src/townlet/exploration/rnd.py
- Added explanatory comment at deletion site
- Updated this bug doc to FIXED status

Owner: exploration
