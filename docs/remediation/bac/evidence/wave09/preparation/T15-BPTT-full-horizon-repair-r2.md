# T15 BPTT full-horizon repair r2 — test-only, runtime pending

Root confirmed all R1 runtimes closed and authorized only the bounded BPTT test repair. Read receiving-code-review and the complete independent integration review R1. Its P2 is confirmed: a maximum derivative over all returned hidden tensors and all updates could accept a merely connected final two-step suffix of an L8 window.

Only test_recurrent_bptt_runtime.py changed. For every actual sampled full configured-L row (L2 and L8), the test now requires a selected final real prediction and a nonzero finite derivative to the FIRST real prefix hidden of that same update. A temporary initial_hidden wrapper forwards the real factory unchanged and marks its returned tensor identity. The real network hook records only the first grad-enabled output consuming that actual initial object, once per group; it never substitutes a value-zero heuristic or a late prefix. Captured first observations bind the candidate first hidden to the actual full-length group. If another group has byte-identical first observations, its independent hidden contributes no nonzero derivative to this row; exactly one candidate must contribute. Every full-length row is asserted immediately. No maximum over timesteps or updates can excuse a disconnected earlier window. Inserting a detach after any early prefix of an L8 row leaves its first hidden derivative absent/zero and fails at that exact update, even if the final two steps remain connected.

Actual ReplayRequest.sequence_length, sampled real-length bounds and full-L nonvacuity remain. Every BPTT runner still requires real optimizer steps matching successful-update counters and changed online parameters. The separate real L8 weight_hh_l0 backward test still requires nonzero gradients on every observed backward. Rollout-memory/completed-lane checks are unchanged. No full-L single-network-call topology is assumed.

No production, bootstrap, lane-learning or helper edit occurred. No sixth source, source copy/worktree/branch, project import, runtime/pytest/collection, index/commit or delegation occurred. Root must run the exact two BPTT lengths and the existing recurrent-weight/rollout tests before broad qualification; this is not GREEN.

## Exact report-time inventory

| Source | Whole lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 2146 | 9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a |
| tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py | 360 | 06ee4ca2e9dff88539ed8cb3120048fc058772d009fa5962ee28f127db7d8f77 |
| tests/test_townlet/integration/test_recurrent_bptt_runtime.py | 222 | 2701678bcb442360eb2a860ea4e74bc7d5b8d4b9b2f639b78c21cd7db9f2494a |
| tests/test_townlet/regressions/test_episode_lane_learning.py | 476 | e328726c20e82dfc6754fb4623211aae24f8a7bd70530864ef49e913b804ad2c |
| tests/test_townlet/regressions/fixtures/episode_lanes.py | 157 | 9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f |

Exactly five complete sources/3361 lines, below five/5000.

Owned static checks PASS:

```text
.venv/bin/black --check tests/test_townlet/integration/test_recurrent_bptt_runtime.py
.venv/bin/ruff check tests/test_townlet/integration/test_recurrent_bptt_runtime.py
```

Root owns runtime and final identity qualification. Return stationary.
