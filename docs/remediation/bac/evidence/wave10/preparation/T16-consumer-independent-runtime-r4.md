# T16 consumer repair R4 — independent runtime receipt

2026-11-02, existing `/workspace/hamlet`. Root explicitly cleared this run after accepting the bounded static review and closing owner runtimes. Executed exactly the supplied command:

```sh
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave10-r4-independent-consumers-spec.json
```

**Independent result: 4 passed, exit0; 29.92 pytest seconds / 35.62947058677673 harness wall seconds.** This is an actual independent execution, not a restatement of root's earlier result. No new defect appeared in these four cases. The static review's existing lifecycle and coverage limits remain unchanged.

## Exact execution and result custody

Read the supplied execution spec, completed result JSON, full final log, and all three process-identity receipts. The harness ran the repository virtualenv Python, pytest with two xdist workers, worksteal, no coverage, no cacheprovider, and bac_source_identity. Spec `workers:1` is the harness job concurrency; pytest itself used `-n 2`, confirmed by `created: 2/2 workers` and `2 workers [4 items]` in the log.

The exact selected nodes were:

- `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks0]`
- `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_keeps_authored_terminal_and_live_bootstrap[end_ticks1]`
- `tests/test_townlet/regressions/test_episode_lane_sinks.py::test_caller_cap_completes_lanes_before_curriculum_publication`
- `tests/test_townlet/integration/test_runner_hyperparams_v21.py::test_demorunner_threads_training_loop_hyperparameters`

Result: `/workspace/bac-review-2026-11-01/qualification/wave10-r4-independent-consumers/independent-consumers-result.json`.

Log: `/workspace/bac-review-2026-11-01/qualification/wave10-r4-independent-consumers/independent-consumers.log`.

Independently computed final log SHA256: `b201e999002be79a02afdf0407bb32855fbe20cde182dfa10b09bb3cd89685d9`, exactly matching result metadata. Result identifies candidate tree `51c6d53eb2a815257b7eab4bffa800fb54d8a2a2`, base `f575ecefda7844fbd5b7b6138ad0c6bf7b1bafd8`, manifest SHA256 `46ad49bad88b619829c560986549dfab203a984186346a4aea1576afdcae7afb`, and harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. The latter two are harness-reported metadata, not independent source reads.

Every emitted process identity was checked: `identity-controller.json`, `identity-gw0.json`, `identity-gw1.json`. All three report the exact candidate/base above, module `/workspace/hamlet/src/townlet/__init__.py`, Torch `2.11.0+cu130`, and one Torch thread. No conflicting/stale checkout identity appeared. Only the expected benchmark-disabled warnings appeared because xdist is active; no failed or skipped case appears.

## Five-source continuity

Hashed the same five sources before completion and again after the run; all hashes match the prior independent static review and R4 candidate. No extra source/helper was opened or created by this reviewer. Physical line counts remain those established by the static review (five whole sources / 3758 lines).

| Source | Lines | SHA256 before and after |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` |312|`e6631eb7e2375165a1e1131eaf88999e8debb024d37ef736bf9eadcdacd3fbde`|
| `tests/test_townlet/integration/test_runner_hyperparams_v21.py` |126|`237ca50b9deb1e585c7d37d1134896b4fe1a29dde12b4de7a401210e317c4db0`|
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` |157|`9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f`|

## Verdict and limits

The four previously failing consumers now pass independently with their preserved assertions: both cap lane orders, cap completion before curriculum publication, and three authored hyperparameters reaching the explicit population factory. Together with the accepted static review, this supports the narrow repair. It does not add real factory-initializer coverage to HP or a numerical bootstrap-target assertion to SINKS.

Root separately reports all21 direct consumers PASS, full collection6873/6874 selected and guard progress. Those results were not independently rerun here and are not promoted into full-suite evidence. This receipt does not close G2, T16 release, overall acceptance, any of54 final requirements, or any of22 lenses.

Only this ignored report was manually written; the authorized harness produced its normal test outputs in the supplied qualification/scratch locations. `git check-ignore -v` verifies `.git/info/exclude:7` `/.superpowers/`. No source/test/index/tracked-doc edits, additional helper/source reads, branches/worktrees/project checkouts or source copies/deletion, subdelegation, commit or push occurred. Existing14 checkouts remain untouched. Runtime exited; stationary now.
