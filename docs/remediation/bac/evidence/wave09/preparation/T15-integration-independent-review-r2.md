# T15 integration independent review R2 — scoped BPTT repair

Reviewed statically on 2026-11-02 in existing `/workspace/hamlet`. Measured HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`; global frozen tree `929bc8952a2e797871d15376e2ef61a8aec73ca5` is attributed to root and `wave09/r2-candidate.json`. Read the complete repaired BPTT source, the BPTT section of `wave09/r2-integration-review.diff`, and `T15-BPTT-full-horizon-repair-r2.md`. This is the requested scoped continuation of R1, with no new source or final lens.

## Verdict

**Spec: PASS by static inspection for the exact R1 P2 repair. Quality: PASS for this bounded change; runtime qualification remains OPEN.** The test now binds every observed full-length row's final selected prediction to the first real prefix hidden state in the same actual update. The former acceptance by any late hidden derivative or any successful update is gone. No new blocking defect was found. The R1 P2 is closed at the source-review level; executable closure still requires root's L2/L8 results on this exact candidate.

This does not assert a production BPTT defect ever existed. The separate main-production review/approval is root-attributed and unchanged; no production source was opened here. R1's other four source assessments and their stated scope limits carry forward because their bytes are unchanged. The constant-three lane target and run-wide successor membership controls remain lifecycle/learning evidence, with independent legality and exact-successor evidence supplied by the separately reviewed main-owned suite; no new lane-test repair is requested.

## Why the repair closes the gap

Within each `_recurrent_predictions` observation, `initial_hidden` forwards the actual network factory and records the returned hidden tensor's identity. The forward hook accepts only a grad-enabled call consuming that initial object and removes the identity after its first use. It retains the first post-observation hidden tensor without detaching it, alongside a detached copy of that first observation group. It does not infer initialization from zero-valued tensors or choose a later hidden state. No network output, hidden state, loss, request or replay receipt is substituted.

After the genuine predictions return, the test selects exactly the rows whose actual sampled length equals the authored L, and matches their first observation group to recorded first prefixes. This is coherent with the supplied producer contract of same-real-length groups and ascending row selection. Each final coordinate must actually be selected by the loss mask. For each such row immediately, autograd evaluates its scalar final prediction against the candidate first-prefix hidden tensors, retaining the real graph for subsequent optimizer backward. Exactly one candidate must supply a nonzero derivative and that entire derivative must be finite. Independent groups with identical first-observation bytes cannot rescue a disconnected row merely by matching their values: without a graph path their derivative is unused or zero.

A complete hidden-state detach in an early part of an L8 window, while retaining a connected final two-step suffix, no longer passes: the tested final prediction has no path to the identified first-prefix hidden. Every full-length row in every observed update is checked before returning, rather than collecting a best derivative across rows, times or updates. Nonempty requests, sampled length bounds, actual full-L support and nonempty successful full-horizon observations prevent vacuous acceptance. The first-to-final derivative proves connectivity across the horizon under the supplied recurrent producer contract; it does not purport to inspect every internal LSTM edge individually.

The common runner still requires positive real optimizer calls, equality with successful-update counters and changed online parameters. The independent recurrent `weight_hh_l0` backward witness and its every-observed-gradient positivity assertion remain intact. The actual rollout-memory and completed-lane hidden-state checks remain intact. YAML-authored L2/L8, batch/minimum settings and real training entry point remain unchanged. Hooks and temporary method patches are restored through `finally`/context exits, and `autograd.grad` uses `retain_graph=True` so the witness does not consume the normal training graph.

## Exact unchanged inventory boundary

Same five complete test sources, now **1537 lines**. Hashes and counts independently remeasured. Only BPTT changed from R1, growing from 203 to 222 lines. No sixth implementation/helper/conftest/probe source was read.

| Source | Lines | SHA256 |
|---|---:|---|
| `tests/test_townlet/integration/test_authored_episode_lanes.py` | 66 | `1aa95fc7764c9e85dfdc16d8f1d43f4014d86fedc18c7bcfdc627bf8779c56ac` |
| `tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py` | 360 | `06ee4ca2e9dff88539ed8cb3120048fc058772d009fa5962ee28f127db7d8f77` |
| `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 222 | `2701678bcb442360eb2a860ea4e74bc7d5b8d4b9b2f639b78c21cd7db9f2494a` |
| `tests/test_townlet/regressions/test_episode_lane_learning.py` | 476 | `e328726c20e82dfc6754fb4623211aae24f8a7bd70530864ef49e913b804ad2c` |
| `tests/test_townlet/regressions/test_episode_lane_population.py` | 413 | `5c306090ecdf7ec50c699ffb48913376a40fd12e58feb682bfc1ceb514ecd4f8` |

## Executable obligations and custody

Root must finish candidate-bound collection and execute both exact `test_training_keeps_the_configured_sequence_graph_connected[2]` and `[8]` cases. Require actual full-L witnesses, finite nonzero first-prefix derivatives for every observed full-L selected final prediction, successful optimizer counters and real parameter changes. Then execute the retained recurrent-weight and rollout-memory cases and the broader existing owner suite. Any first-prefix matching, graph, numerical or runtime failure requires causal diagnosis without weakening the full-horizon condition. Static reasoning about rejection of an early detach is not a claimed executed mutation result; this reviewer ran no mutation or negative-control runtime.

All existing bootstrap, authored/population-lane and lane-learning runtime obligations from R1 remain, as do root's broader affected-owner/full qualification gates. No collection or earlier candidate pass is promoted to final R2 behavioral GREEN. The owner-reported formatting/lint passes are attributed, not independently executed here.

Only this ignored report was written. No source edit, runtime/project import/test/collection/linter/probe, new helper, index/tracker/commit, source copy, branch/worktree/deletion or delegation operation occurred. Existing worktrees were untouched. Return stationary.
