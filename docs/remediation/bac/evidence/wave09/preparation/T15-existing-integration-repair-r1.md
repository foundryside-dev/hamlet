# T15 existing integration repair r1 — authored, runtime pending

Root closed all R0 runtimes and authorized only three owned test edits. Exactly five complete sources remain charged; no sixth runner, supplier, network, buffer, conftest or executable probe was opened. Initial read inventory and causal findings are in T15-existing-integration-audit.md.

## Source identity

| Source | Whole lines | SHA256 |
|---|---:|---|
| src/townlet/population/vectorized.py | 2146 | 6548abfe25bc58e8ff0dad00638387898f9a6504357a07e2c42c646915b9ef52 |
| tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py | 360 | 06ee4ca2e9dff88539ed8cb3120048fc058772d009fa5962ee28f127db7d8f77 |
| tests/test_townlet/integration/test_recurrent_bptt_runtime.py | 203 | 4d593039f7ab31eb3a54ab04b51d9134a003dbc2b7723c05abe975e3ccf1cf1e |
| tests/test_townlet/regressions/test_episode_lane_learning.py | 476 | e328726c20e82dfc6754fb4623211aae24f8a7bd70530864ef49e913b804ad2c |
| tests/test_townlet/regressions/fixtures/episode_lanes.py | 157 | 9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f |

Total 5 sources/3342 lines, below five/5000. POP/common fixture may move independently under their authorized owners; these are the observed report-time pins.

## Corrections and retained behavioral controls

Bootstrap observes the real SequentialReplayBuffer.sample_batch class method, returns its unchanged receipt, copies actual fields, and aligns configured functional huber/smooth_l1/mse selected-loss targets through loss_mask. The independent oracle unrolls only each row’s real prefix, evaluates its exact stored successor with captured successor legality, and uses its own online/target hidden trajectories. Final-real indexing replaces padded final-column assumptions. Gamma and vanilla/Double assertions, lost-bootstrap equality check, nonterminal support, zero-hidden negative and new crossed-hidden negative remain mandatory. Optimizer.step is wrapped only after the real common initializer completes; sampled batches must correspond to successful optimizer counters and actual parameter change. No sample or target is substituted.

BPTT observes the actual public ReplayRequest.sequence_length (root-relayed field) and actual sampled real lengths, requiring full authored-length support. A record-only Q-network hook retains returned online hidden tensors. torch.autograd.grad of real final predictions with respect to earlier returned hidden requires a nonzero cross-timestep derivative; a detached prefix fails this control even though every one-step forward still occurs. The existing nonzero recurrent weight backward assertion remains. Every BPTT runner test also requires real optimizer steps/counters and parameter change. The rollout-memory preservation/completed-lane checks remain. Root verified runner.population is None until run; observation is therefore installed on the common initializer before entering run, not on context entry.

Lane learner tests explicitly pass replay_min_size=2 to the root-owned public supplier relay, which authors the copied YAML before compile. No production minimum changes. Actual sample_batch class observation follows any lazy sequential replacement and checks readiness/retained minimum; the real receipt/law is unchanged. The actual configured _loss_values call is wrapped and forwarded unchanged, supporting all three functional loss choices and aligning recurrent selected targets. Test-local torch/Python/NumPy seeds98 make existing sampling laws reproducible without fabricated receipts or RNG draw replacement.

All63 predecessor/successor/admission/predictor/normalization ledger coordinates, independent RND RMS/reward recomputation, RND and Q optimizer steps and parameter changes remain required. Real selected ordinary/terminal/cap targets remain independently checked against reward+gamma*3, actual successor forwards remain observed, and padding is excluded from objective/row arithmetic. Existing three membership/completion corruptions and actual truncation-done corruption remain assertions that must fail for the intended reason. The shared helper owner retains full-N ENV transport while adapting K-selector schedule rows; this worker never edited that fixture or its supplier.

## Verification and limits

Owned target Black formatting and Ruff passed. Final check commands:

```text
.venv/bin/black --check tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py tests/test_townlet/integration/test_recurrent_bptt_runtime.py tests/test_townlet/regressions/test_episode_lane_learning.py
.venv/bin/ruff check tests/test_townlet/integration/test_recurrent_bootstrap_runtime.py tests/test_townlet/integration/test_recurrent_bptt_runtime.py tests/test_townlet/regressions/test_episode_lane_learning.py
```

No project import, runtime, pytest/collection, index/commit, branch/worktree/source copy or subdelegation occurred. Root must execute the exact affected nodes in its identity/import/fixture harness, verify sampled coverage and all negative controls, and diagnose genuine failures without dropping assertions. These changes are not GREEN or production qualification. No production optimizer defect was claimed or repaired here; full ICM reward remains REQUIRED OPEN under T18e/f.
