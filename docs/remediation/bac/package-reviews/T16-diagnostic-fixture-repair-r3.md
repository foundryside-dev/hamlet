# T16 changed-readiness diagnostic fixture repair r3

Root reports the R2 exact-two selection GREEN in28.9363 wall seconds and all six guards PASS. Its complete owned12 run reached **11PASS/1FAIL**,92.7278 harness wall seconds (pytest86.99s). The sole failure is the fixed_full fixture's log-count assertion at the former line522. These are root-owned results, retained with their actual identity; this repair has not been executed and does not relabel that run as12PASS.

Read the actual failure log and verified SHA256: `/workspace/bac-review-2026-11-01/qualification/wave10-r2-owned/owned.log`, `fa0b5358dcd35383c6f75bf392a7a71e6c92e835f663d2bc4252ccae12ed763a`. It contains exactly two distinct, correctly changed backend signatures:

```text
Replay not ready: capacity_window_impossible (retained=0, sampleable=0)
Replay not ready: capacity_window_impossible (retained=1, sampleable=0)
```

The existing no-repeat assertion succeeded. The next assertion incorrectly required the entire reason to appear only once, ignoring the actual retained-count state change0→1. This is a **fixture expectation fault**, not repeated production logging or a readiness/learning defect. Root reports160 source paths/five process identities/14 checkouts custody PASS and explicitly cleared only this assertion repair with all local runtimes closed.

## Exact change

Only the one count assertion inside `test_real_runner_window_diagnostic` changed. The repaired assertion requires the exact two expected signature messages in their actual order, once each. The existing `len(messages) == len(set(messages))` rejection of repeats remains unchanged. Thus initial retained0 diagnosis remains required, retained1 diagnosis remains required, and repeated or unexpected messages still fail.

The exact test diff is **4 additions/1 deletion**,526→529 lines. Every other function/helper is byte-identical to root's staged R2 test; the complete diff contains only this one hunk inside the fixed_full branch. Zero optimizer/sample/scheduler/target work, zero learner updates, exact initial online/target weights, empty optimizer state, unchanged scheduler, actual retained1/sampleable0 reason, vector beta pacing and the adaptive real-length1/actual-learning branch all remain unchanged. No production edit or initial logging suppression was made; all99 assertions/five test functions/12 expected parameterizations remain present.

Before test SHA256: `4b9fdcc73192b91db199111b4c2a07186e50fa1afc5bd6a77aa1e2909660939a`.

After test SHA256: **`2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`**.

## Five-source custody and verification limit

Same complete inventory, now **5 files/4422 physical lines**, under the unchanged RR1200/POP2200/BC600/OF200/test700 =5/4900 projection:

| Complete source | Lines | SHA256 |
|---|---:|---|
| `src/townlet/demo/runner.py` |1017|`e1c4b6c00923416f6fdf9e70976ea57a4a706e38a2ea228b4b10273906d6aacf`|
| `src/townlet/population/vectorized.py` |2146|`9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a`|
| `src/townlet/config/brain_config.py` |568|`6c041ed40de507dfed81dc4b3a58cbb728d446228f6fd831ee115348aa559079`|
| `src/townlet/agent/optimizer_factory.py` |162|`56af1a9c8edb70a25b43a6e10aa3080d9a7b8becff112924e21a9429d994717d`|
| `tests/test_townlet/regressions/bac/test_runner_readiness.py` |529|`2352066710ef7d97de02efb498021f26f7ffc50e2ce2afe96ea6ba4bbee04ce4`|

All production hashes remain unchanged. Standard-library AST parsing succeeds; assertion count99 and maximum line length133 are unchanged. No project import/runtime, pytest, collection, compiler, linter/formatter or probe ran. Syntax and diff checks are not an observed test remediation PASS. No sixth implementation/helper/source, index/commit/push/tracker action, branch/worktree/checkout/source copy/deletion or subdelegation occurred. Only the owned test and this ignored receipt were written; all14 existing checkouts remain preserved.

Return stationary. Root owns the exact failed-node rerun and unchanged11-control evidence binding; mandatory full G2 must cover all12 on the final source. No source-only/earlier partial run constitutes final T16/repository qualification.
