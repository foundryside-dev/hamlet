# CUDA / 16-worker tooling readiness — bounded static handoff

Status: CUDA remains unqualified. John's promised server has not been supplied;
access, actual resources and CUDA execution are unverified. This note changes no
acceptance gate. Read-only inspection covered exactly five helper bodies (278
lines), AGENTS.md, EVIDENCE-PROCESS.md and CUDA-RUNNER-HANDOFF.md. No helper,
application, Git/index, environment or runtime/test operation was executed.

## Existing facts and finite additive follow-up

1. **Capture is tied to the historical CPU host.** `capture_wave14_round.py`
   asserts cpu.max is exactly `400000 100000`, affinity >=4, numeric memory.max
   >=16 GiB and >=4 GiB free. It assumes Linux cgroup-v2 paths; `max` memory
   limits fail integer conversion. Resource output says CUDA unavailable and
   records a fixed old TMPDIR and threads=1 without establishing those settings.
   Add a separately named capture version with measured quota/affinity/RAM/disk,
   effective scratch path and explicit admitted concurrency; retain one-thread
   custody unless a newly reviewed contract changes it.
2. **Sixteen jobs and sixteen pytest workers are different controls.** Capture
   emits outer spec workers=1 and owned pytest `-n 2 --dist worksteal`; the runner
   uses spec workers for concurrent subprocess jobs. Add explicit independent
   job and xdist limits, unique attempt/job paths and a total CPU/GPU budget.
   Choose limits after admission, not from the server's advertised worker count.
   Isolate process-global poison selections and preserve exact named selections.
3. **CUDA is forcibly hidden.** `run_bac_packet_checks_locked.py` overwrites
   CUDA_VISIBLE_DEVICES with an empty string. It sets OMP/MKL/OpenBLAS threads=1;
   the plugin sets Torch threads=1. Add explicit CPU/CUDA job profiles with
   validated device assignment and bounded per-device concurrency. Record GPU
   UUID/model/count/VRAM, driver, Torch/build CUDA capability, visible-to-physical
   mapping, effective environment and competing workload. Capture currently
   records only CPU/memory/disk/process snapshots; no GPU facts are witnessed.
4. **Identity is pytest-only and startup-only.** `bac_source_identity.py` checks
   HEAD/tree, source hashes and townlet import under root/src, then writes one
   controller/gwN record with Torch version and thread count. No PID/PPID,
   interpreter, child identity, GPU assignment or end-of-process source witness
   is recorded. Both verifiers demand controller plus exactly gw0..gw(N-1) from
   integer `-n`; this already represents `-n 16`, but cannot attest arbitrary
   child processes, worker replacements or GPU execution. Add actual process
   and child custody, unique process records and explicit expected/observed
   worker accounting; reject missing identities and verify imports/device use.
5. **Index locking is partial.** Runner, plugin and success verifier serialize
   `git write-tree` via `.superpowers/bac-qualification-index.lock`. Failed-run
   verifier calls write-tree without this lock. The lock protects cooperative
   metadata calls only, not source/index mutation throughout execution. Capture
   itself stages files and writes a tree: it is not a read-only admission tool.
   New helper versions must coordinate every metadata operation and maintain
   the authorized candidate freeze; no new checkout or branch is required.
6. **Attempts are not exclusively created.** Runner accepts existing output
   directories and overwrites logs/results; plugin identities/failures and both
   custody reports also overwrite fixed paths. Only capture's candidate path
   has a pre-existence assertion; its specs/resource file can be overwritten.
   Add exclusive immutable attempt creation and unique names; seal start/end
   times, command/selection, seed, environment/hardware and actual exit status.
   Preserve interrupted attempts even when no result file is produced. Runner
   prints failing child results but does not propagate their nonzero codes as
   its own exit status; qualification must require explicit per-job verification.
7. **Receipt checks need a CUDA execution gate.** Success verifier authenticates
   manifest/log, current source/config/artifact bytes, registry, pytest identities
   and absence of failure files, but counts come from log regexes and skipped or
   xfailed hardware cases do not fail it. Neither verifier compares the recorded
   command with the spec or authenticates result.harness_sha256 against a pinned
   version; only the failed verifier checks optional auxiliary_harness hashes.
   Add common pinned dependency/spec/result verification, structured outcomes,
   required-case collection/execution and actual CUDA assertions. Distinguish
   successful, completed-failed and interrupted outcomes without relabeling any.

## Execution and publication boundary

First prepare and independently review the finite new capture, runner, identity
and verifier versions above, including focused concurrency/custody checks when
execution is authorized. Preserve all old hashed helper bytes and attempts;
new names/hashes are new evidence objects, not compatibility adapters. Root owns
application changes and candidate sealing. Hardware/access is an external block;
CPU-only assumptions and custody gaps are fixable tooling blocks.

After server admission, use the existing authorized checkout and exact candidate;
verify causal fixtures/imports before costly runs. Execute the current ledger's
open CUDA/slow/end-to-end and learning/provider/checkpoint obligations. Independently
verify each attempt, retain failures/skips, name terminal attempts, and seal a new
checkpoint receipt linked to its predecessor. Publish new exact bytes plus verified
immutable references under EVIDENCE-PROCESS.md; do not sum overlapping selections
or infer package acceptance from hardware availability or a custody PASS.

## Inspected source identities (SHA-256)

All paths are under `/workspace/bac-review-2026-11-01/qualification/`.

| Helper | Lines | SHA-256 |
|---|---:|---|
| capture_wave14_round.py | 103 | f4c8a6db1df092c6ef37a552d989f4107feef7f92e94578f5cb60f0d78868d02 |
| run_bac_packet_checks_locked.py | 20 | 180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791 |
| bac_source_identity.py | 60 | 0a376a6454e317104adc4bce2cdc0d268c216de8c67e91e60623e6df7d31719d |
| verify_bac_run.py | 33 | b00f16ec8666f475805399e80e7f4c2e335f8c6170c18cb705c22f8d6725c91d |
| verify_bac_failed_run.py | 62 | aa23117fc684edf13e70743d5eb4ee2f652a751f218f45d88316ee1859e8bc56 |
