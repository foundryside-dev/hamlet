# Astra plan revision evidence — 2026-10-02

Revision parent: `fix/episode-lane-accounting@86857eb0e0730c113cbf27f21bd97a308095079b`.
Runtime/tests/config/scripts remain identical to source `ec463fdaaa632e4e1f778b938ace94f53a73a745`.
This receipt demonstrates the proposed S1 preflight only; no runtime code was modified.
The original independent Astra review remains beside the plan unchanged.

## Executed controls

Primary `.venv`: Python 3.13.15, SQLite 3.53.1. Agent and coordinator independently
executed the complete function against disposable artifacts using trusted prospective
DDL extracted from the current `_create_schema`, amended with the plan's required
batch/context/reason/shaping columns. Expected column declarations come from that
trusted DDL, never from the input artifact. SQLite-connect spies assert every
inspection connection targets a private `/tmp/demo-schema-preflight-*` directory.
The proposal text in the revised plan is byte-identical to `preflight.py.txt` here.

**22 controls passed: 20 original families unchanged; two external-change controls refused.**
Snapshots include existence, size and SHA256 for main, WAL, SHM and journal. Two
negative controls deliberately change the source or introduce WAL after the copy
read; refusal leaves exactly the injected writer state and performs no additional
original-family mutation. Do not call those two inputs unchanged.

| Category | Demonstrated outcome |
| --- | --- |
| Normally closed old WAL DB without companions | Version-0 refusal, no original SQLite connection or new companions |
| Current-stamp malformed closed WAL DB | Private validation refuses; original family unchanged |
| Valid normally closed current WAL-mode or DELETE-mode file | Supported private-copy validation; original family unchanged |
| Valid committed WAL; malformed current-stamp committed WAL | Explicit unsupported-family refusal; committed content preserved |
| Pending journal, empty WAL, orphan WAL | Refusal, complete original family preserved |
| Truncated/corrupt/non-SQLite/unsupported stamp | Refusal, complete original family preserved |
| Wrong types, nullability, primary key or hidden generated column | Strict declared-column refusal |
| No exclusive custody | Refusal before inspection/opening |
| Absent or zero-byte companion-free new path | Permitted fresh-creation preflight; no original creation by inspection |
| Source changed or companion appeared during validation | Detected and refused; only the external injection changes original bytes |

A private committed-WAL witness reads no `committed_wal_witness` row from a main-only
copy, and reads `present` from a complete main+WAL copy. This proves why the bounded
preflight explicitly refuses pending families rather than silently ignoring WAL.
No original family is opened with SQLite even for that witness.

## Commands and custody

Run from the primary worktree, using its existing valid environment; disposable
SQLite fixtures are created under `/tmp` and removed by their own scoped temporary
contexts. The retained raw output is a byte copy, including temporary path names.

```bash
.venv/bin/python -P runs/episode-lanes/2026-10-02/planning/astra-revision/probe.py \
  --proposal runs/episode-lanes/2026-10-02/planning/astra-revision/preflight.py \
  --source /home/john/hamlet/src/townlet/demo/database.py
```

The archived `.py.txt` paths also execute through the probe's SourceFileLoader;
provide those exact paths through `--proposal` and the executable probe path.
Raw agent/coordinator stdout and stderr remain in ignored
`runs/episode-lanes/2026-10-02/planning/astra-revision/`; the coordinator stdout is
also archived here as `root-probe.stdout.txt`. Files are retained, not cleaned away.

| Artifact | SHA256 |
| --- | --- |
| preflight.py.txt | `0640b8073ac9b9c60c5d6fa43a370b56db830ac84ff9f9def8955824a1d54406` |
| probe.py.txt | `8585884478697a532febcaf01a0fbc3937997717f5cacf417a0368bcb8126d54` |
| root-probe.stdout.txt | `d928cec8a193d71ab04b6c77cbaacc456c7aed0356e01a6edf9774a7df3aa14c` |
| agent-probe.stdout (ignored bank) | `c500fc15f943ba1cb11823639ec1df7ee845e55da745748a3c056759d7596f20` |
| src/townlet/demo/database.py | `945ea042fdacc9b265ce6a2e4b4d62fd9b876c816c6a00dd29df94d99d2bb082` |

## Limits and execution handoff

The custody boolean asserts a caller obligation; it is not a lock. Maintaining
exclusive ownership through actual reopening is a runtime prerequisite, not
established by these disposable controls. Fingerprints detect changes but do not
prove atomic snapshots with active owners. Any WAL/SHM/journal presence, even
valid committed content, is explicitly unsupported and preserved. Concurrent
owners and interrupted-run recovery require a PDR scope amendment if needed.

W1's four-of-five recorder losses remain the original independent review's bounded
thread evidence without indexing. No fresh ordinary runner/index acceptance was
executed in this plan revision: E0a now requires it early. W2's canonical frame and
observer prefix contracts are implementation instructions, not a corrected reward
reading. No fresh full suite, learning convergence, push or main merge occurred.

## Proposed reward-fragment and document checks

The coordinator extracted and executed the complete `S1 format-2 reward payload`
Python block from the revised plan using the primary `.venv/bin/python -P` via
stdin. The earlier positive total and zero terminal frame both retain prefix 1.0
through indices `[0,1,1,0]`. Seven controls refuse negative/out-of-range/bool
indices, component mismatch, NaN, bool reward and metadata-total mismatch. Fragment
SHA256: `60654e3ae1661e32742c412b85309c81181e74e7ce6101b526ad2877ecbb13fc`.
The DB block compiles and equals `preflight.py.txt` byte-for-byte. Modified Markdown
fences balance and 35 local links resolve across seven documents: the plan and its checkpoint/
evidence documents. `git diff --check` passes. These are proposal/document checks,
not actual DAC, TensorBoard, persisted observer or full-suite acceptance.

Astra re-review identified a concrete overlapping-owner video caller: the batch
query database remains open while each individual export opens the same path.
The revised S1 now owns query-owner close before child export and child-owner
close after load on success/failure, with real sequential DB/reader and exception
cleanup controls. This is a required implementation caller update, not an executed
runtime repair or permission to ignore pending WAL companions.

## Independent final review

Astra independently reran all 22 archived database controls and the exact numeric
fragment with eleven additional refusal controls. Final verdict:
**APPROVED_WITH_WARNINGS**, no blockers, for the 1,576-line plan hash
`159ab22fc58bb43a5c2e9756c5bfbc9546f10ecb1d5a42145a357b104acb1b6c`.
[Final re-review](../../../../../plans/2026-10-02-truthful-episode-lanes.astra-revision-review.md)
and its separate JSON receipt preserve stopped-owner/ordinary-shutdown/candidate
acceptance gates. Original reviews and prior evidence remain unchanged. The
report is archived byte-for-byte, SHA256
`a0dc3d9d78a08880152f6520286ac5167f11d15927758b83e9cec009a5517b81`.
