# T17 consumer R2 independent runtime receipt

2026-11-02 UTC. Root separately authorized this independent runtime after reporting its joint38 and six guard wrappers CLOSED. Existing `/workspace/hamlet` only. The previously proposed four existing consumer nodes ran against unchanged R2. No source, new probe/helper/test, index, tracked documentation, branch/worktree, project-source copy/deletion, or delegation changes. This ignored receipt is the only authored file in this phase. No wrapper/plugin implementation or fourth source was inspected. All14 worktrees left untouched; root separately owns comprehensive custody verification.

## Actual result

**4 passed, 0 failed, 0 skipped**. Actual pytest log: `4 workers [4 items]`, four pass dots, `4 passed in 94.16s (0:01:34)`. Wrapper result records exit0 and **99.86783361434937 seconds** wall time. The launched wrapper session exited normally with exit0; no process termination was used. Result JSON and actual log were both read and checked; outer exit alone was not treated as proof.

Result DATA: `/workspace/bac-review-2026-11-01/qualification/wave11-r2-independent-consumers/independent-consumers-result.json`.

Log: `/workspace/bac-review-2026-11-01/qualification/wave11-r2-independent-consumers/independent-consumers.log`.

Log SHA256 independently matched result: `0a891aff727253c0bb56f4ef9701a15b655a78d21eac75509c6c588e9603ab87`.

The log's benchmark warnings say benchmarks are disabled under xdist; all four selected functional tests executed and passed.

## Exact authorized invocation and selected nodes

Working directory `/workspace/hamlet`:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave11-r2-independent-consumers-spec.json
```

The actual result command used `/workspace/hamlet/.venv/bin/python -m pytest`, the following four nodes, and `--no-cov -p no:cacheprovider -p bac_source_identity -q -n 4 --dist worksteal --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave11-r2-independent-consumers`:

1. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_recurrent_brain_yaml_trains_the_recurrent_weight_matrix`
2. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_keeps_the_configured_sequence_graph_connected[2]`
3. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_keeps_the_configured_sequence_graph_connected[8]`
4. `tests/test_townlet/integration/test_recurrent_bptt_runtime.py::test_training_does_not_clobber_mid_episode_rollout_memory`

The DATA spec's `workers: 1` denotes the one wrapper job; the pytest command and actual log confirm four xdist workers.

## Candidate and runtime identity verification

Result, manifest, and all five identity DATA records agree on:

- Base commit: `a0802a442bc7ea529de650b8705629923a0e6c72`.
- Candidate tree: `f0410f6b8185cf2c87f4f6d5ddbd0a730e886dc9`.
- Loaded module identity: `/workspace/hamlet/src/townlet/__init__.py`.
- PyTorch: `2.11.0+cu130`.
- Threads: **1** each.

Exactly five records were found and validated: `identity-controller.json`, `identity-gw0.json`, `identity-gw1.json`, `identity-gw2.json`, `identity-gw3.json`, under the output directory's `independent-consumers/` subdirectory. Their worker fields are exactly `controller`, `gw0`, `gw1`, `gw2`, `gw3`.

Manifest SHA256 independently matched result: `f0ff070cce442c0c60035c5e6dab7fd3d245900423d61873a9534791cba23bb6`.

Harness SHA256 recorded by sanctioned wrapper metadata: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. Its implementation was not read.

All three current source hashes were independently recomputed after closure and match the R2 manifest and earlier static review (1056 total lines):

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/agent/networks.py` | 655 | `24d4a8627255dab42b3b9b64995c62235f71f25ea04cdbaace6616f1b6e899ed` |
| `src/townlet/agent/network_factory.py` | 179 | `31b1340b6a125754ae15dbcc981223a4a6f4056ebf9db38ffbe63ba0ff9dd75c` |
| `tests/test_townlet/integration/test_recurrent_bptt_runtime.py` | 222 | `105656e944001f44213e8c721bc98d7c99e8d8512aa1172eeabc93ea0f3df0a7` |

## Invariant interpretation and disposition

The earlier static review independently established exact preservation of all23 original assertions and scenario/control-flow text, apart from the two observer method/name substitutions. Their passing execution now establishes, for these configured runs:

- Actual optimizer-step calls were positive, agreed with the population training counter, and at least one actual Q-network parameter changed. The recurrent flag and network type held. Actual autograd hook observations on initialized LSTM `weight_hh_l0` were nonempty, and every recorded maximum absolute recurrent gradient was strictly positive. No fabricated gradient or standalone training was substituted. Numeric gradient magnitudes were not emitted by these tests, so no unrecorded numeric values are claimed.
- Both configured sequence lengths2 and8 had actual sampled full-length training rows. Replay requests and sampled length bounds held. The actual selected final-Q prediction had exactly one nonzero connected derivative to an observed first real prefix, and that derivative was finite. Full-horizon evidence was nonempty in each case.
- Training occurred during the rollout-memory scenario; actual mid-episode forwards were observed. Active lanes with positive episode counts did not have exactly-zero hidden state. Completed lanes were observed alongside rollout activity and had exactly-zero hidden state as asserted. The repaired observer therefore measured real calls rather than passing by empty observation.

**Static review P2 runtime-evidence gap: addressed for these four scenarios by this independent run.** No new failure was revealed by restored observation. The broader upstream implementation-audit boundary remains: only the approved three sources were independently reviewed; this receipt does not claim a complete audit of imported runner/population implementations.

The repair remains **observation restoration only**, not a new runtime capability. This run supplies the previously missing consumer evidence for unchanged production behavior under the retained configuration. It does not broaden claims to other architectures, seeds, platforms, or the entire BAC suite.

Root supplied separate R2 joint38 PASS/no skips in135.0191s and six guards PASS; those are attributed to root and are not counted as this worker's execution. This receipt claims only the independent four selected passes. The original actual R1 affected22-module **2 FAIL / 407 PASS** remains intact. No whole-BAC, full409, or replacement all-green R1 claim is made.

Worker returns stationary after normal wrapper closure and this receipt.
