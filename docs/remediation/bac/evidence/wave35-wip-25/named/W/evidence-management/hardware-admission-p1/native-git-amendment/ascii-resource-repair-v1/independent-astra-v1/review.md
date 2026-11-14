# Independent P1 ASCII resource amendment verification

**Disposition: no blocking defect found in this finite amendment; eligible for root adoption of the new P1 digest.** This is source and synthetic parsing verification, not actual hardware, native capture, or full P1 qualification. Consumers remain pending root adoption and their own integration/requalification.

The reviewed actual source is `/workspace/bac-review-2026-11-01/qualification/capture_bac_hardware_v1.py`, SHA256 `08c89f253231eaf67d2675e6e00b0ae137925456f8918651dbc4d0eab96526e7`. The exact frozen test is `test_capture_bac_hardware_v1.py`, SHA256 `bd605e3626e4fc169943d54a19857f7a92989a7bbd9092c47bbd9805d65c7907`. P0 remains `e4f31eacb0e4499655a19ec91a4f5618a7b2ad3f4090e7ed068816b311e00860`. The freeze and grammar-delta hashes match the assignment (`7d711c52…60e9`, `c3944b7d…ab4c`). All eight cited evidence reference hashes and byte lengths in the freeze were independently verified.

## Defect disposition and source contract

The prior independent P2 review and its `probe-results.json` document five actual P1 assessment acceptances of Arabic-Indic replacements, with empty refusal reasons, under original P1 `d91d9a4eac393d1283de0fa2a894a6f7a837aa9e28aa854c4795462f5229a1bb`. Those are retained failure witnesses, not newly rerun obsolete code. The owner red attempt additionally records ten expected-refusal failures across assessment/preflight and two passing preservation controls, with unchanged original P1 and the same frozen test hash. The red log shows assertion failures or failure to raise, rather than collection/import failure. Its metadata/log digests are verified against the freeze.

Static comparison of the hash-verified original `.py.txt` snapshot to the actual fixed source finds exactly eleven changed lines. AST comparison confines changes to `cpuset`, `assess_resources`, and `discovery_preflight`; every other top-level AST node is identical. No source copy was executed. `source-delta.diff.txt` retains the exact comparison.

- Cgroup resource parsing now requires ASCII before splitting/stripping. This covers the quota and period (including `max` quotas), cpuset endpoints, finite memory limits, and memory current. The shared cpuset parser retains range, duplicate, and malformed-token checks.
- Assessment numeric matching and both consumed meminfo regexes use `re.ASCII`. Non-ASCII digits and non-ASCII numeric separators therefore cannot satisfy those expressions. Assessment continues to consume MemTotal and MemAvailable; the deliberately cheaper preflight continues to consume MemAvailable only. This amendment does not add a new full meminfo validator or change which fields each boundary consumes.
- The source delta leaves all numeric arithmetic, unlimited states, canonical path handling, P0 interface, native Git custody, timestamp/PID/CUDA/driver grammar and bootstrap behavior unchanged. It does not broadly normalize text or filesystem paths.

The original finite Linux-token acceptance defect is repaired in the tested scope. No additional regression or blocking implementation defect was found. This is not a claim that every malformed `/proc/meminfo` document, every unconsumed field, or every pre-existing protocol language is now exhaustively validated.

## Fresh independent evidence

A single actual-source run used the 117-line `probe.py` and imported the frozen modules directly from the qualification directory. It produced 78 passing independent rows: three decimal alphabets across all five fields and both boundaries; mixed ASCII/non-ASCII quota/period tokens; non-ASCII outer/separator whitespace; existing invalid cpuset cases; and ASCII baseline, ASCII meminfo whitespace, unlimited values and Unicode filesystem-path controls. Successful assessment controls assert exact capacity 3.5 and budget `{cpu_slots:3, ram_bytes:600, scratch_bytes:950, scratch_inodes:18}`, rather than only asserting no exception. Refusals retain their actual reasons in the results.

The same bounded process freshly reran the exact frozen owner regression selection with `--tb=line`: **12 passed, 124 deselected**, exit 0. These twelve overlap the retained owner suite and are not added to its 136 total. The owner's full 136-pass record is hash-verified historical evidence; this reviewer did not rerun that full suite.

Actual process metadata: PID 246510, PPID 246509; UTC start `2026-11-14T13:41:10.134660+00:00`, end `2026-11-14T13:41:10.924675+00:00`; affinity `[3]`; soft/hard RLIMIT_AS both 4294967296. Exact `/proc/self/cmdline`, pytest arguments, source references before/after, and exit status 0 are retained in `probe-results.json`. All four before/after source/probe references are equal; all are AST-parseable. No subprocess, actual capture, native Git, APP, CUDA, or hardware workload was invoked by this probe.

Artifacts:

| Artifact | SHA256 |
| --- | --- |
| `probe.py` | `f8afe1e9f19bc07193519d95c50af8cc4ea9236ae4f7282e0cadf19b26dea280` |
| `probe-results.json` | `0852b47e2e8862cd642340125abb70764ac0fae042eda5d5a929dd8a2ca58fed` |
| `focused.log` | `9163614b4d7c5866008b295f6d233fbeb04d131d44be2f351b6c137d8d6de9be` |
| `source-delta.diff.txt` | `da823b3e525ac0647c474e3f06308dabf05edd7c8581991298213c20b3cd097a` |

Current body scope is P1 992 + frozen test 979 + P0 526 + own probe 117 = 2614 lines, four bodies. Conservatively counting the original P1 static snapshot as a distinct body version adds 992 lines, giving five bodies/3606 lines, within the five-body/5000-line ceiling. Only the old/new diff was displayed for the old source; no P2/P4/bootstrap implementation body was read. The old P2 review/results were metadata only. No Git operation, branch, worktree, checkout, source edit, consumer pin edit, or execution source copy occurred.

Root must explicitly adopt the new P1 digest and coordinate P2/P4/bootstrap pins. These findings grant no independent authority to repin them and no actual full-chain/hardware acceptance.
