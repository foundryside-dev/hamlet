# T15 training independent runtime r5

2026-11-02. Root explicitly cleared the prepared exact-four execution after reporting collection of all eight module cases and six R5 guards successful. Execution used existing `/workspace/hamlet`, frozen HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, candidate tree `f71c52fad680a74da1b90cc7470455fc90f4fa3f`.

## Actual result

**Four PASS, actual job exit code 0.** Pytest reports `4 passed in 37.63s`; job-result wall duration is46.406864643096924 seconds. I inspected the actual result JSON, complete log and all three controller/worker identity records rather than relying on outer-wrapper exit. No test failed, errored, skipped or xfailed. The log includes pytest-benchmark's expected warning that benchmarks are disabled under xdist; these four functional tests still executed.

Approved invocation, executed once without broadening or repetition:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave09-r5-independent-training-spec.json
```

The prepared specification ran one job with pytest `-n 2 --dist worksteal`, `--no-cov`, no cacheprovider, and `bac_source_identity`, against these exact nodes in `tests/test_townlet/integration/test_training_loop.py`:

- `TestMultiEpisodeTraining::test_train_10_episodes_with_learning_progression`
- `TestMaskedLossIntegration::test_masked_loss_during_training`
- `TestMultiEpisodeTraining::test_target_network_updates_at_frequency`
- `TestMultiEpisodeTraining::test_q_values_improve_over_time`

The passing unchanged assertions establish actual optimizer progress in all four cases, original ten-episode weight change, at least ten optimizer updates and target-weight change in the target case, original Q-statistic change threshold, and finite metrics after actual recurrent learning. Compiled private-pack minimum/batch assertions passed. Recurrent readiness therefore supplied enough real sampleable experience for this run; no missing sampler support was concealed. Exact optimizer counts are not printed by the harness, so only the asserted lower bounds are claimed.

## Evidence and identity

Evidence directory: `/workspace/bac-review-2026-11-01/qualification/wave09-r5-independent-training`.

`independent-training-result.json` records actual exit0, all four exact nodes and the HEAD/tree above. Its manifest SHA256 is `781a9338ab724924fcfbb744699bf477877a112b0ed632c332ca58004eeabe79`; harness SHA256 is `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`. Independently measured `independent-training.log` SHA256 matches the result: `4e6bae3ac94fd7fbe8ce3c4f4035bac1c17f840bd8e03e6010febc91c82c7a60`.

`independent-training/identity-controller.json`, `identity-gw0.json` and `identity-gw1.json` all report the same exact HEAD/tree, imported module `/workspace/hamlet/src/townlet/__init__.py`, Torch `2.11.0+cu130`, and one Torch thread per process. Their worker labels are respectively `controller`, `gw0` and `gw1`.

All five reviewed source SHA256 values were independently rechecked after execution and match the frozen static review/manifest. Source scope remains five whole sources,3672 lines; no additional implementation source was opened.

| Source | Reviewed lines | Post-run SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |
| `tests/test_townlet/integration/test_training_loop.py` | 641 | `207500289444d904f33d1961164fec493433a3f1514562ff541ce5fced11c722` |

## Findings, remaining qualification and custody

No material runtime defect in this exact-four execution. The limits identified by the static review remain: this is no new exact per-update target-cadence trace, policy-improvement proof or exhaustive masked-gradient proof. It verifies the existing preserved consumer assertions with real learning under explicitly authored private test warmup.

All-eight module execution and replacement full qualification remain root-owned and are not claimed here. The prior fullreplacementR1 failure (root-attributed1FAIL6222PASS14SKIP) remains preserved as a distinct failed run. These four passing cases do not rewrite that result or constitute a full-suite PASS.

The original static review was preserved. No source/test/index/tracked-document edit, new helper/probe, checkout/branch/worktree/source copy/deletion, subdelegation or runtime cancellation occurred. The existing generic harness was invoked without reading its implementation. Only this requested ignored report was written beyond ordinary approved test artifacts. Root was promptly notified of actual four-PASS and matching post-run identities. Return stationary.
