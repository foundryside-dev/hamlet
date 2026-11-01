# Source provenance

Original scoped review/execution retains its recorded actual identity. The final source binding verifies the reviewed files are identical in qualified source `b3003550b7c1dad76a52e596b2af01658fa2b92d`, tree `aecfaaa84cd58fafd8ac1f6ca67052639d570ed4`; no execution is relabeled as occurring at a later HEAD.

Original `T14-owner-maintenance-independent-review-r1.md`, SHA256 `a1ecbc53f7250b14c473ecace8ae9b9c3a45c1513b131e73bc76dd497193429b`, retained unchanged. Portable rendering normalizes execution paths.

# T14 existing-owner maintenance independent review R1

Verdict: **SCOPED CLEAR**. No material P1/P2 defect or preservation gap found in the two owner-test changes against the actual sequential producer. This is a static review of expectation maintenance, not T14 release, whole-BAC approval, runtime success, or review of the separate PER mathematical implementation. Optional P3: none.

## Identity and complete source inventory

Existing `/workspace/hamlet` only. Observed HEAD `01f2f64f42c2932177729607b337419355cb2720`. Root manifest `.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave08/green-r1-candidate.json` identifies candidate tree `324438ad58d9d5a85bba54e18be1ee225ada5969`, 112 guarded paths and 14 preserved worktrees. Candidate tree identity is manifest-attributed; this reviewer did not generate a tree or claim whole-index equality.

Exactly three complete implementation/test sources were read, 3294 lines total, below hard 5/5000:

| Source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/training/sequential_replay_buffer.py` | 1815 | `f958b1ed79bab5a37422353a04a9d78c05969950dfbf994436b4e1ce0e73392c` |
| `tests/test_townlet/unit/training/test_sequential_replay_buffer.py` | 611 | `18cff4fa681e5c08ec759301b3ebbed69568bc8ab80b7ccea3e6c260294f373a` |
| `tests/test_townlet/integration/test_compact_token_acceptance.py` | 868 | `a9a911a37679ffb850583fefaa7b73907a3f350d86959238d718c5ffb85867dc` |

Read applicable root AGENTS.md and the dispatched-subagent exemption in `superpowers:using-superpowers`. Read task-T14, the inspection-transport handoff and its exact T12 proposal as prose. Effective R1 interface proposal hash was verified as `d6708084cb8bb63ba3febf8860b24a5f8b7a846da609c18ac2988aca35e77239`; its Astra review as `37d9bda30b9a7b00f2a084f1c70fb754d16cf293082b43e2892823346a50d2a8`; the owner-maintenance receipt as `e413de7484ac48484fb002ed31d6877f338b8bc6f516be579051860dd4351079`. These are public prose receipts, not additional source reads. No RC, OP, PS, HC, POP, helper, network, conftest or fourth test implementation was opened.

## Independent semantic assessment

The complete two-file diff against HEAD was read using `GIT_OPTIONAL_LOCKS=0 git diff HEAD -- <owned test paths>`: unit +10/-6 lines; compact +19/-5. Review followed actual branches, producer construction, snapshots and raises contexts rather than relying on the author's AST counts.

- Uniform remains format6: the producer constant is 6 (SB line41), `for_replay` leaves priority absent, and `_serialize_current` (line1590) adds format7/priority_state only when actual priority state exists. Unit exact current keys/version and compact current6 sample/receipt/mask/component assertions remain intact.
- Legacy bare5 remains genuine producer output. Unit tests still construct it via the public two-argument buffer, exercise post-terminal dictionary sampling, then import it as an archive with zero active retention. The four-key inspection resave/restore remains callable and checks complete archive custody, retained0, separate newly authored legacy rows and sample values. SB `serialize`, legacy materialization (line685), inspection validation (line1777) and mode guards preserve these distinctions. Compact old5 is an independently authored exact old schema, not captured6 relabeled as historical evidence.
- Strict version checks agree with SB `_validate_serialized` (line1681): exact integer membership precedes captured schema validation. Existing 5.0/6.0/True refusals remain; 7.0 is additive. Unsupported4 and true future8 receive the actual supported-list diagnostic `5, 6 and 7`. Bare integer7 passes version selection, then fails the missing `replay_kind` check before key-set validation; the changed expectation is correct and does not skip capability.
- Both legacy5 and current6 corruption producers remain under the unit parametrization. Each added retag7 mutation lacks the required closed7 key set, is refused before priority reconstruction, and retains exact input/live snapshots. Existing wrong-kind, unknown/missing keys, wrong capacity and tensor-contract refusals are unchanged.
- Compact captured6 retag5 remains a negative case. The new loop tests retag5 and retag7 separately, snapshots each mutated input, and checks both source and the same populated live target immediately after each refusal. The surrounding final equality checks remain. The earlier original full-current roundtrip is still reached and asserted.
- The old5 retag7 input formerly covered by the unsupported-version loop is separately retained as `mixed_legacy`, with the correct key-set failure and independent input/live equality checks. Unsupported4 remains and unsupported8 is added. Thus changing 7 from unsupported to malformed-supported does not drop that old negative payload. No positive7 or historical5 is manufactured through tag rewriting, and no priority state is guessed.
- Compact standard and flat-prioritized branches, their producer versions and their historical/retag/purity assertions are unchanged. All existing test functions remain, with no new skip, xfail, early return or weakened branch condition. Current6 full resume, historical archive/fresh0/readiness, component/mask checks and inspection preservation are still operative in the reviewed control flow.

The owner's reported 36 existing functions and 214 assert ASTs are supporting custody evidence only; the clear verdict rests on the full source/diff and producer-path assessment above. HC archive internals and other replay-family internals were not independently re-reviewed here.

## Execution limits and remaining gates

Static reads, hashes, line counts, manifest data queries and read-only Git inspection only. No project imports, runtime, pytest, collection, new probes, source/test edits, index/staging/commits, git write-tree, branch/worktree creation, project-source copies, deletion, tracker writes or subdelegation. Only this ignored review prose was written. Source identities were checked before review and rechecked after writing; returned source-stationary.

Root's reported R0 outcomes (core69 pass; native64 pass/one codec diagnostic failure; sequence/history128 pass/five stale diagnostics; native consumers117 pass/one stale compact expectation) are attributed evidence, not execution by this reviewer. Root R1 collection, actual runtime, six standing guards and mandatory full serialization/public-contract gate remain pending in this verdict; no passing claims are inferred. Separate core/native reviews remain necessary. T15 must provide X04 finite unweighted TD telemetry before G2. Full native C07, T24/T25 and final acceptance remain OPEN.

User preservation and approved History A override blanket deletion guidance. No durable rule was saved and no user-only fallback adopted; the failed rule neither grants nor restricts authority. Existing instructions and actual approvals govern. All 14 worktrees remain untouched by this reviewer.
