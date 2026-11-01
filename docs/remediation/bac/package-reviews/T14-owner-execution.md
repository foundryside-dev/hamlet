# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-owner-maintenance-independent-execution-r1.md`, SHA256 `07756a35bcd559a43249f06ae4501f84dce85124881caf50885e1a7a14472fa8`, retained unchanged. Portable rendering normalizes execution paths.

# T14 owner maintenance independent execution R1

Verdict: **SCOPED CLEAR, independently executed owner suites PASS**. The actual owners job exited 0 and its log reports **63 passed in 31.84s**, with no failures or skips. Harness elapsed time was 39.39579916000366 seconds. No new material defect or gap was observed. This corroborates the prior static preservation/expectation review; it does not establish full BAC or native C07 acceptance.

## Exact execution and identities

Root explicitly opened a one-CPU independent runtime window for these two owner files. The output directory and external spec path were checked absent before creation. Existing `/workspace/hamlet` only; exact base HEAD `01f2f64f42c2932177729607b337419355cb2720`, candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`.

Invocation:

```text
.venv/bin/python qualification/run_bac_packet_checks_locked.py qualification/wave08-astra-owners-r1-spec.json
```

Exact executed job, from `/workspace/hamlet`:

```text
.venv/bin/python -m pytest tests/test_townlet/unit/training/test_sequential_replay_buffer.py tests/test_townlet/integration/test_compact_token_acceptance.py -q --no-cov -p no:cacheprovider -p bac_source_identity
```

The external spec selects `workers: 1`, the frozen wave08 `green-r1-candidate.json` manifest, and output `qualification/wave08-astra-owners-r1`. The supplied qualification API sets one thread and empty CUDA visibility and checks 112 guarded hashes/HEAD/tree before and after, with each pytest process's import/source/Torch identity. Per-job result JSON and the complete actual log were inspected, not merely the outer driver exit. The identity receipt reports the expected HEAD/tree, imported module `src/townlet/__init__.py`, Torch `2.11.0+cu130`, controller, threads1.

| Evidence | SHA256 |
| --- | --- |
| `owners.log` | `86777ea6cc686b2a8a8a2350003fbe99389e536ceba9548055c827039e55c1cd` |
| candidate manifest | `2c60cc34fe84cccefb7041aa9ad67928c8a7184a69bb01935b59b4fba6ccb6e5` |
| supplied harness, independently hashed without reading source | `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791` |
| identity plugin (root-supplied identity, not source-inspected) | `0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d` |
| unchanged static review | `a1ecbc53f7250b14c473ecace8ae9b9c3a45c1513b131e73bc76dd497193429b` |

Actual log: `qualification/wave08-astra-owners-r1/owners.log`; job record: same directory `owners-result.json`; runtime identity: `owners/identity-controller.json`.

## Preserved source inventory and limits

No new application/helper implementation was opened. Complete source inventory remains exactly three files / 3294 lines:

| Source | Lines | Rechecked SHA256 |
| --- | ---: | --- |
| `src/townlet/training/sequential_replay_buffer.py` | 1815 | `f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c` |
| `tests/test_townlet/unit/training/test_sequential_replay_buffer.py` | 611 | `18cff4fa681e5c08ec759301b3ebbed69568bc8ab80b7ccea3e6c260294f373a` |
| `tests/test_townlet/integration/test_compact_token_acceptance.py` | 868 | `a9a911a37679ffb850583fefaa7b73907a3f350d86959238d718c5ffb85867dc` |

All three hashes and the unchanged static-review hash were rechecked after execution. No source/test/index content edits, staging, commits, worktree/branch changes, project-source copies, deletion, new probes or subdelegation. Only external spec/execution artifacts and this ignored execution receipt were written. The expressly authorized harness owns its metadata-lock-scoped git write-tree checks; no separate reviewer git write-tree was invoked. All 14 worktrees remain preserved. Returned stationary.

Root reports core69/native65/sequence owners136/native consumers118/all six guards PASS; those separate results are attributed to root and were not rerun here. Full-suite status is still pending in this receipt: this run covers only the two owner files. Mandatory full serialization/public-contract qualification, X04 finite unweighted TD telemetry in T15 before G2, full native C07/T24/T25 and final whole-BAC acceptance remain OPEN. User preservation/History A and actual instructions/approvals continue to govern; no durable rule or user-only fallback was created.
