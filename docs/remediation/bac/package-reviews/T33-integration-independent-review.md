# Recording integration maintenance — independent static review r9

Verdict: PASS for this bounded integration-test maintenance review. No P1/P2 findings. This is not runtime qualification, whole-BAC acceptance, GPU qualification, or release approval.

Reviewed the complete current contents of exactly five source/test files, 1951 lines total, and the full `git diff HEAD` for the two owned integration tests. No sixth source/helper/builder was read; no application imports, tests, runtime probes, source edits/copies, index changes, branch/worktree operations or delegation were performed. This report is the only authored artifact.

Candidate metadata: base HEAD `214408b107730b4511b8a690541569aeca4b7b67`; manifest candidate tree `b34cf49af0bd041fffb197d2096a4a52d6179dc7`, from `generation-green-r9-candidate.json` (28 source guards). Candidate tree identity is attributed to that manifest; file counts and the following hashes were directly checked during review.

| Whole file | Lines | SHA256 |
|---|---:|---|
| tests/test_townlet/integration/test_recording_recorder.py | 757 | 517341fb44d5edb7cdc85dc4bb6b4f8840de7ce741695d594b766038f8d6e962 |
| tests/test_townlet/integration/test_recording_substrate.py | 138 | 806f4f11e1a00b8dc058b643531ff78cdcea5b84c9e027fbac5993d655fcea9c |
| src/townlet/recording/recorder.py | 699 | 8fca0b033bdc74f9e8146006c029b8bce6228b067f89b72109e1a886f4a32825 |
| src/townlet/recording/data_structures.py | 243 | b8b2a5b2c202e8fc28ee907b645391cfb32f7d1a5530f528fa8ae6e076171158 |
| src/townlet/recording/receipts.py | 114 | f4f90c3ae1584965cbfc7ad84170fb3b0413ba5599a9eeb3d0d447f48b6fd647 |

Design basis: read `LEGACY-GENERATIONS-PROPOSAL.md` and `LEGACY-GENERATIONS-REVIEW-r1.md`. Proposal hash directly confirmed as `b28387782a8e3f9b09d5644fd59461fa9ca4f3389d64d44cd090a934260bb18c`. Applied its additive preservation requirements and parent-attributed original P8/T33/user preservation contract. The failed durable rule supplies neither authority nor restriction; no user-only fallback is adopted.

## Findings and preservation checks

P1: none. P2: none within this maintenance scope.

The private queue adaptation observes `_Capture.frame` and `_Boundary.marker`, while retaining actual scalar values, tensor-derived positions/meters, optional Q-values, action masks and temporal fields. Additional mutations test snapshot independence. The boundary fixture checks exact metadata equality plus a distinct metadata object and actual sequence/episode/lane ticket. No arbitrary accepted-set weakening or numeric expectation replacement appears in the diff.

Stopped-consumer fixtures stop and join the real writer before capture, assert the sentinel was consumed, then acknowledge exactly the entries they remove. These are transport-only observations. Their empty shutdown tuple is cleanup after test-owned removal, not evidence that frames persisted or normal production drain resolved their provisional groups. The standalone metadata fixture likewise does not claim a complete 200-frame episode persisted. These limitations are consistent with the assigned fixture purpose, not an invalid persistence assertion.

The overflow test retains the established legacy warning/drop/None behavior, increments the read-only drop counter twice, checks unchanged queued frames and consecutive accepted sequences, and confirms a later accepted capture uses sequence 2. Its deliberately incomplete dropped group must raise RecordingDrainError despite manual queue consumption, expose errors, produce no persisted receipt, close admission and leave no live consumer or unfinished queue tasks. This is a substantive failure control, not successful drain evidence. Qualified routes remain strict in reviewed production source; these two integration files alone do not establish their runtime coverage.

The separate ordinary-recorder incomplete-work test actually runs the consumer and requires the real missing-end error, exact unbound sequence `(0,)`, no receipts and completed thread/queue shutdown. The raw writer buffering test actually starts writer_loop, waits for queue acknowledgements, verifies the buffered frame and then checks explicit incomplete-stop errors. The raw successful writer test now starts a consumer before asserting buffer clearing, so the old initially-empty-buffer shortcut cannot satisfy the complete test. Both raw items must be acknowledged; actual artifact/alias existence, receipt status/identity, index invocation and metadata assertions make false persistence non-vacuous.

The writer persistence fixture uses a coherent one-publication indexed database seam: its context yields generation 1, insertion records kwargs and returns index 1. It requires exact indexed metadata, boundary sequence, frame count, final_done False, legacy True and generation 1. The single frame has index 0, rewards 1/1/0/0 and done False, matched by cap metadata with one survival step and identical reward totals; this meets the inspected DTO/episode validator. Artifact and canonical alias bytes match, their inodes differ, the receipt is absolute and below the temporary output root but outside its root directory, the legacy locator uses the correct relative base, and the indexed hash equals actual artifact bytes. This mock qualifies the writer-to-index seam, not real SQLite commit durability or generation allocation.

The stop test correctly distinguishes enqueueing the sentinel from consuming it, requiring the actual loop to exit and clear unfinished tasks. No genuine legacy capability loss has been dismissed as a stale fixture.

## Refuted concerns

- Queue inspection does not race the consumer: the helper verifies the writer has exited before admission begins.
- Bare raw RecordedStep/EpisodeEndMarker transport was not removed: the writer adapter handles these legacy inputs, and the changed successful test exercises the real loop.
- Buffer-empty alone is no longer enough to pass the publication test: real files, one index call and one persisted receipt are required.
- Empty receipt checks in transport fixtures do not authorize lost production frames: the distinct real-consumer incomplete test requires loss reporting; transport fixtures cannot be cited as normal drain proof.
- Legacy capacity logging is not replaced by arbitrary exception tolerance: the two drops must return None and log, while shutdown of the incomplete group must specifically fail and fence admission.
- Immutable artifact and mutable canonical alias are not conflated: path, byte equality, distinct inode, index locator and legacy locator assertions distinguish them.

## P3 observations and bounded gaps

Inherited low-priority assertion gaps remain: the live-environment temporal test's comment says non-decreasing interaction progress, but its repeated `>= 0.0` assertion does not compare consecutive values. The variable-dimension affordance test only converts local lists with tuple(), so it does not qualify recording serialization/validation. Neither weakness was introduced or used to replace stronger coverage by this patch.

The new real-consumer synchronization uses unbounded queue.join(). It establishes actual acknowledgements under the reviewed source, but a future consumer regression can hang until an outer runner timeout rather than yield the former local timeout assertion. This is a P3 failure-diagnosis limitation, not false success or a demonstrated current failure.

Publication assertions check actual artifact bytes/hash against the alias and index seam; they do not independently decode and compare the persisted payload against every original field. Production verification validates its own serialized payload. Real SQLite publication, repeat generation custody, cross-process locking, ordinary Runner end-to-end behavior and full qualification remain separately owned evidence outside these five files. No additional test programme is proposed here.

No runtime pass is claimed by this reviewer. Root reported that current tests were executing and separately owns ordinary Runner ten-run evidence and full qualification; outcomes may be attributed only from root's completed exact-candidate evidence, not inferred from this static PASS.
