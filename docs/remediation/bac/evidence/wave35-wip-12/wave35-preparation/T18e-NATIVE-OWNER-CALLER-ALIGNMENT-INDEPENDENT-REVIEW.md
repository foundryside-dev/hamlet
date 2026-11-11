# Native owner caller alignment — independent finite review

2026-11-11. SPEC: APPROVE within this caller-alignment scope. QUALITY: APPROVE within this scope. No material defect found in the two-test unstaged delta against the staged R53 baseline. Runtime qualification remains root-owned and pending this review.

Requirements were read before implementation: AGENTS.md and the21-line finite brief, followed by the33-line author report SHA256 `134cccba0389943c286764f8b3ff94258a8bed307c37913899d02b90fce7feb8`. The native restore configuration contract was read as prose/API facts. No other CURRENT document was read or edited.

Exact implementation read inventory: five complete bodies,4262 lines; no sixth source/helper/probe body. Read-only production seals and reviewed test seals independently match the supplied packet:

| Path | Lines | SHA256 |
|---|---:|---|
| `src/townlet/exploration/world_curiosity_state.py` |1253|`8aaa59e919e82ca49431620f25a77ddd5b08f2c9a845e7c4f5593f1eed6072b0`|
| `src/townlet/exploration/rnd.py` |1128|`53cccad55acad4018518bd498206129feddc5f54113560103cab60c94659ac46`|
| `src/townlet/exploration/provider_factory.py` |153|`dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8`|
| `tests/test_townlet/regressions/bac/test_owned_native_metadata.py` |314|`eab1491f577ab57b19d997ca848d1eada2a2df68569553957510b2aa190045e8`|
| `tests/test_townlet/regressions/bac/test_pw_local_service.py` |1414|`2fed03f1e10f39cbcd34b54aaa2fb938b36c5da3aa288bdb4d485149fc96f11f`|

All56 changed owner lifecycle sites supply explicit root `lineage=None` (27 metadata,29 service). Inspection shows these calls execute outside a held owner operation; provider work stays inside the real callback. Raw provider and WorldRNGState APIs remain distinct. No compatibility wrapper, fabricated context, private prepared-handle inspection or production change was introduced.

Actual `_BackendOwner._validate_prepared` first rejects a missing/consumed handle, then checks destination revision. `OwnedWorldBackend.call` and `snapshot` advance that revision. The consumed-handle assertion now matches `already consumed`, and the observation-stale assertion matches `destination changed`; both remain specific ValueError refusals grounded in the actual source.

PW continuation now prepares and installs immediately, checks exact saved state, and compares actual source/destination next-work draws, receipts, traced learning and native/RNG snapshots before preparing a separate negative-control handle. Its later snapshot establishes destination observation staleness while checking unchanged backend/RNG values; failed installation again checks unchanged values and ambient streams. The reorder preserves the original no-mutation control on a learned destination and prevents a negative control from blocking the genuine positive continuation.

Native metadata tests retain the independent direct-provider reference, exact recursive type/order/metadata comparator, actual OrderedDict metadata witness, tensor/NumPy alias mutations, real Adam/FIFO/RMS continuation, next-update gradients and pure-validator mutation controls. The mutation witness still records that substantive native validation was reached before the deliberately impure action.

Private-stream comparisons retain Torch, Python, legacy NumPy and owned NumPy draws plus world-b pressure against the independent world-a replay. These are actual executed callbacks and independently compared exported data, not owner self-comparisons. Native exact-v4 schemas and predictor_service.version3 are unchanged; no loader validation was relaxed.

Independent static AST parsing passed for all five bodies. Counts confirm42 test functions,125 assert statements,15 pytest refusal calls and56 explicit lineage=None keywords. The scoped diff preserves original function/parameter identities and substantive assertion/oracle expressions apart from the two documented regex corrections and intentional PW statement reorder. No test/helper was added or removed.

Review operations were source/prose reads, the read-only two-test unstaged diff, and standard-library AST/hash inventory. Only this report was written. No pytest, application import/runtime, compiler probe, source copy, Git/index mutation, branch/worktree/checkout, dependency installation or subagent occurred.

Root still must qualify the23 exact previously failing native nodes and bounded coherent affected suites. The supplied R53 result (946 collected;920 PASS,24 FAIL,2 CUDA-unavailable SKIP) is historical context, not evidence that this fixed tree passes. The separately owned DemoRunner ENV world_roster/training_seed/lane_world_ids prerequisite remains required and outside this fix; this approval neither waives it nor claims parent/programme closure.

Independent runtime addendum,2026-11-11: root subsequently authorized the exact existing locked harness/spec for the23 causal owner nodes. PTY41746 was polled to CLOSED, exit0; one serial pytest process, no additional runtime or source-body expansion.

Complete named log/result:23 collected,23 PASS,0 FAIL/SKIP/ERROR/warnings; pytest9.53s, harness15.216585636138916s. This independently repeats the23 causal cases and adds no unique cases to root's overlapping coherent998 selection.

Candidate tree `51173768987b6bd451291ca59d90f75cf4bf0b7e`; manifest SHA256 `8097951b7cdd4adb1352cc544374220493c92b1be1a1dab5e2a08799efba1579`; harness SHA256 `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`, as recorded in the result.

Log `/workspace/bac-review-2026-11-01/qualification/wave35-r54-independent-owner23/independent-owner23.log`, independently hashed SHA256 `f0fad1033b25cfb066b8c53a3585765093384110ca4d245b20b2bf048fce1dc8`; adjacent `independent-owner23-result.json` was read completely. Final full source/config/artifact/process/index custody verification remains owed by root; no Git/index or harness/spec/source modification was performed here. Scoped SPEC/QUALITY approval stands.
