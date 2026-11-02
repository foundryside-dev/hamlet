# T15 artifact independent runtime r4

2026-11-02. Root explicitly cleared this existing-harness execution on frozen HEAD `75bc8e438caaf4eadf8f4e0f6b522f84c680c1e7`, candidate tree `f4032499a9800e8a8398b812a8dcc7ebfe9c4974`, after reporting collection and custody checks passed. This reviewer independently executed the exact previously failing artifact case in `/workspace/hamlet`.

## Actual result

**PASS: one test, actual job exit code 0.** Pytest reports `1 passed in 5.60s`; the job-result JSON records 14.335936784744263 seconds. The wrapper exit alone was not used to establish success. I inspected the actual job-result JSON, complete pytest log and identity-controller JSON.

Invocation:

```text
env TMPDIR=/workspace/bac-review-2026-11-01/qualification/scratch/tmp-wave08-r3 python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave09-r4-independent-artifact-spec.json
```

The existing harness ran only:

```text
/workspace/hamlet/.venv/bin/python -m pytest tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py::test_ordinary_two_episode_files_index_sql_and_tb_match_actual_eligible_ledger -q --no-cov -p no:cacheprovider -p bac_source_identity --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave09-astra-artifact-r4
```

Evidence directory: `/workspace/bac-review-2026-11-01/qualification/wave09-r4-independent-artifact`.

- `independent-artifact-result.json`: actual exit0, exact node and frozen candidate/HEAD above; manifest SHA256 `7127f3f1855212118fd688a5d7b1024714bac43dab0d0267aa25bc45f4a7df3c`; harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.
- `independent-artifact.log`: collected one item and one PASS. Independently measured log SHA256 matches result: `4544ace84e425bf91d65b7f200d5148420a8d83ea888a1e47b713b8dc89fa999`.
- `independent-artifact/identity-controller.json`: exact HEAD and candidate above, module `/workspace/hamlet/src/townlet/__init__.py`, worker `controller`, Torch `2.11.0+cu130`, threads `1`.

The generated DATA at `/workspace/bac-review-2026-11-01/qualification/scratch/wave09-astra-artifact-r4/episode-lane-artifacts0/ordinary-cleanup.json` reports `ordinary_cleanup_passed`, writer not alive, empty outstanding queue and writer buffer, six accepted/six dequeued entries, two episodes/two recording rows, fourteen realized live-agent transitions, and two existing compressed files. Their measured fixture digests are `446694b6641309c4c5c2dcc792140d5415f7c90aca776a8d4cf5d6807ca2ddde` and `6e8b8e1f4037221873c75fd46d9ae885fbe3125115dc496667c53f8a79226238`; compressed sizes 872/881 bytes, serialized sizes 1402/1402 bytes. The passing test also executes queued/persisted payload equality, independent eligible ledger, file sizes/index/SQL and TensorBoard agreement assertions previously inspected in the static review.

## Post-execution source custody

All four hashes and counts independently rechecked after actual execution; they match the frozen r4 static review and manifest (3031 lines total).

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/population/vectorized.py` | 2146 | `9569eab3d766ed5467ecf78736cd170c7aa0d0b77d90efe28239f3bab64ff12a` |
| `tests/test_townlet/regressions/test_episode_lane_sinks.py` | 304 | `29b8fd697fd11e55c6d0a28de2ecba119f933d3cb8276d36f6502e35bbf0e79b` |
| `tests/test_townlet/regressions/test_episode_lane_artifact_pipeline.py` | 424 | `1bd025f4fd8c1a18f25235ed94718e68826a8c301386906d8a09ccd85710cc1f` |
| `tests/test_townlet/regressions/fixtures/episode_lanes.py` | 157 | `9de34aa9764fe2cef766aace4e6ebd391543621fa90def16b5614292e476ec7f` |

No material finding in this execution. The causal fixture repair now has independent executable evidence that the exact previously failing artifact reaches and passes its real sink assertions. This is not full qualification: remaining nine-sink/eleven-artifact focused coverage, including playback/export/eight corruption controls, and the replacement full gate remain root-owned. No success is inferred for unexecuted cases.

The original failed full run (root-attributed one setup ERROR, 3536 PASS, 11 SKIP) remains a distinct historical failure; this isolated PASS neither replaces nor removes that proof. No source/index edits, new checkout/worktree, source copy/deletion, runtime cancellation, additional probe/helper or fifth source inspection occurred. The generic existing harness was invoked without opening its implementation. Only this ignored report was written by the reviewer beyond ordinary approved test artifacts. Root was notified of actual exit0 and matching identity immediately so focused20 can proceed.
