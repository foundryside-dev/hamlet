# R0 replay Stage A fix1 independent re-review

2026-11-13. Reviewed the supplied fix1 diff, current test and updated author report against the original Stage A review. Original review is preserved unchanged. Root supplies R74 candidate `6fe4a41e45e35af808e98164b6015a34503cf97b` at HEAD `678513c7`. No runtime, imports, probes, Git/index actions, source edits, additional source bodies or delegation occurred.

## Exact scope

Measured and hashed before reading this revision. The four unchanged production bodies retain original hashes and lengths677/1092/1815/222. Current test is578 lines, SHA256 `3c93193a3028c5979768ce474da2a7f54be55c4ebd888f14c40a57dc1cfe389d`; whole five **4384/5000**, leaving616 lines for growth. Test remains within750. Production inspection for the new issue below is the already-authorized PER body, not a sixth body.

## Original findings

| Original P2 | Disposition | Evidence and boundary |
|---|---|---|
| Reached-admission witness | ADDRESSED in test design | Test-local wrapper filters actual worker and participant, observes entry to the public domain operation, delegates the original bound operation, and records yield/acquisition. Held-state/stream and eventual real draw checks accompany it. Same-owner subclass delegates the prospective actual `_owner_operation(*, mutation)` guard. This is an actual future helper observation, not a test-only production API. R74 does not yet execute successful waiting. |
| Guaranteed cleanup verification | ADDRESSED | Both finally blocks join only started threads and check survivors within finally, chaining the primary error on cleanup failure. Release precedes joins. No inference that daemon threads themselves provide cleanup. |
| Refusal state discrimination | ADDRESSED | Foreign PER owners have different rows, priorities, IDs and generator state; stale candidates differ from live rows at the same count. Full recursive serialized destination equality now accompanies foreign/stale/one-use refusal. |
| Exact local continuation | ADDRESSED | Complete generator payload equality before and after paired real next draws, selected output/receipt equality and all three CPU ambient states replace single-index coincidence. A new configured-PER direct control proves global NumPy advancement with unchanged owned generator, Python and Torch. |

These dispositions assess the corrections themselves. One newly introduced assertion defect prevents unconditional readiness, below.

## New P2: PER held-state comparison uses incompatible row extents

`test_replay_rng_custody.py:83` compares `owner.observations` in full to `saved["observations"]` in `_assert_live_rows_unchanged`. The actual PER owner allocates capacity8 for the three-row fixture, whereas `prioritized_replay_buffer.py:761` serializes `value[:self.size_current]`, a three-row active prefix. Consequently the prospective PER admission test reaches a deterministic unequal `[8,1]` versus `[3,1]` comparison after correct admission is implemented. R74 cannot expose it because that node currently stops at missing `rng_participant`.

Required bounded repair: compare `owner.observations[:owner.size_current]` to the serialized observations, retaining the full priority-array comparison (PER intentionally serializes capacity-length priorities). Do not change production transport or fixture capacity to evade the mismatch. Root should run a separately selectable healthy invocation of this test-local live-state comparison for the genuine PER fixture before interpreting later custody failures; this is a fixture prerequisite, not evidence of admission. This change fits in the existing test body.

The module introductory prose still describes the two concurrency nodes as current-signature behavioral REDs; update that summary to match the already-correct per-node/report distinction when repairing. This is editorial, not an additional material finding.

## Evidence and verdict

Root's exact R74 execution is recorded in the author report and receipt `wave35/r74-replay-stagea-fix1-receipt.json`:19 collected;10 healthy PASS with zero warnings/skips/errors;4 prepared FAIL at `DID NOT RAISE`;5 prerequisite/API FAIL (three missing participant, one lineage TypeError, one unreached owner guard). Root reports815source/573config/13artifact, index/import/thread and14MAIN1 custody verified, all sessions closed. These are attributed root results, not reviewer execution. Collection is not additional execution. The earlier R73 actual admission3/owner1 bypass results remain separately bound to their original source and are not relabeled as current waiting evidence.

**SPEC: accepted bounded tests-first direction. QUALITY: CHANGES REQUIRED for the single new P2 before declaring these exact bytes ready to drive producer GREEN qualification.** All four original P2 corrections are addressed. After the active-prefix repair and fixture prerequisite, no further blocking issue was found in this scoped diff; the packet can then drive actual producer implementation, with explicit caller-signature migration and real GREEN waiting still owed. No production approval is inferred. Poison child, CUDA, wider caller/outer publication and final R0 acceptance remain open; programme accounting stays28/38/66.
