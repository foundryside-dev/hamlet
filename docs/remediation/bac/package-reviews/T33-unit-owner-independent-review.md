# Recording owner alignment — independent r9 static refresh

Verdict: **PASS for owner-test maintenance and its scoped static alignment.** No new blocking finding in this five-file review. Prior raw-public-queue and missing-debug defects are repaired in the inspected REC source, with their meaningful controls retained. This is not runtime PASS, complete C13 proof, whole-BAC qualification or dependent-release approval. The original review is preserved unchanged.

Existing checkout `/workspace/hamlet`; verified HEAD `214408b107730b4511b8a690541569aeca4b7b67`. Candidate tree `b34cf49af0bd041fffb197d2096a4a52d6179dc7` is attributed to coordinator/`generation-green-r9-candidate.json` (28 guarded paths), not regenerated. Exact locally hashed whole-source inventory is **five files / 2327 lines**:

| Source | Lines | SHA256 |
|---|---:|---|
| tests/test_townlet/unit/recording/test_recorder.py | 680 | 11d2391ec0bd7c7e105f8e8d45ce81d5771c4d87961dfee696e432ac3b15576b |
| src/townlet/recording/recorder.py | 699 | 8fca0b033bdc74f9e8146006c029b8bce6228b067f89b72109e1a886f4a32825 |
| src/townlet/recording/data_structures.py | 243 | b8b2a5b2c202e8fc28ee907b645391cfb32f7d1a5530f528fa8ae6e076171158 |
| src/townlet/recording/receipts.py | 114 | f4f90c3ae1584965cbfc7ad84170fb3b0413ba5599a9eeb3d0d447f48b6fd647 |
| tests/test_townlet/utils/builders.py | 591 | 01394a093464632c3df756451e2e91c7b3a398b9ebddc80bb04d41e266a82f3a |

All five whole sources were reassessed; DTO/builders retain the prior hashes. Reference contract: exact locally verified `LEGACY-GENERATIONS-PROPOSAL.md` SHA256 `b28387782a8e3f9b09d5644fd59461fa9ca4f3389d64d44cd090a934260bb18c` and its `LEGACY-GENERATIONS-REVIEW-r1.md` design PASS, together with prior accepted P8/T33/interface context. No sixth implementation/test/helper, imports, runtime, probes, code changes, index writes, branch/worktree/copy operations or delegation. Only this ignored report was written. Root owns current unit execution; no duplicate execution requested.

## Meaningful assertions retained

- Mock writer outcome lists are actual empty lists, avoiding a truthy generic Mock incorrectly triggering sticky writer failure. The production failure check remains active. Q-value/mask assertions retain exact authored values through `.frame`.
- Legacy Full handling now correctly asserts baseline no-throw/None behavior for both frame and finish rejection, cumulative readonly counters, exact warning/error call counts, unchanged sequence/binding/open-frame/task state and unchanged accepted queue contents. This supersedes the earlier candidate's blanket raising expectation under the adopted preservation contract; it is not a waiver of admission accountability.
- Four strict contrasts cover scoped frame, scoped bound frame, legacy bound frame and scoped finish. Each requires queue.Full, no accepted state changes and no legacy-counter increments. Actual finite DTO construction and the real bounded queue remain involved despite the mocked consumer.
- Direct `_process_episode_end` calls supply actual matching terminal metadata/frame/ticket plus dropped_frames=0 and the real buffer length. They exercise processing, receipts, clearing, selection and diagnostics. They do not reproduce the dispatch algorithm. These valid supplied ledgers are fixture setup, not evidence that real producer ledgers cannot drift.
- Raw legacy transport still queues bare RecordedStep/EpisodeEndMarker, runs a real thread/loop, orders stop after queued inputs, bounds join, asserts zero unfinished tasks/no errors and checks an explicitly authored complete independently decoded payload. The REC adapter now assigns provisional raw sequence0 and actual boundary identity, then enters the ordinary processing path. Incomplete raw input still requires the specific missing-marker ValueError/unbound sequence0; unsupported object still requires TypeError. Neither negative was changed to accept a generic error.
- Selected info and unselected debug assertions remain; REC restores debug in the actual nonselected branch. Periodic enabled/disabled/no-criteria controls remain.
- Receipt paths now assert real absolute immutable artifacts distinct from the canonical alias, with separate inode identity and identical published bytes. Replacing old receipt.path==alias expectations is required by the adopted generation design. Canonical alias existence/data remain asserted; the old visible artifact capability is not dropped.
- DB seam uses a real nullcontext yielding generation1 around the mocked DB method, with exact context call identity. It asserts generation1, immutable absolute file_path, separate canonical relative legacy_file_path, legacy=True, actual metadata/lane/sequence/reason, independently computed compressed hash and both sizes, payload reward/ending and receipt index7. No fictitious SQL execution is inferred from this setup.

## Static implementation alignment and evidence limits

REC preserves the narrowed legacy Full catches while strict routes rethrow; counters update under the admission lock, accepted state advances only after successful enqueue, successful boundaries snapshot/reset per-group ledgers, and incomplete/dropped groups fail before selection/publication. Sticky errors and the closed fence still raise. Raw dispatch and debug are present. Generation publication retains nonce artifact paths, no-overwrite artifact publication, separately staged atomic alias replacement, root guard before DB publication context, exact byte readback and immutable receipt paths; exceptions retain publication observations through the receipt error slot. These observations explain why the updated unit assumptions fit the inspected code; they do not prove DB internals or all concurrent schedules.

Remaining evidence boundaries are material and unchanged by this scoped PASS:

1. Mock shutdown on an empty queue proves orchestration, idempotent tuple return and admission closure, not concurrent accepted-set drain. Full queue unit controls stop at refused admission; per-group dropped-ledger failure, rejected-finish retry and actual shutdown accounting require the separate primary T33 real-consumer tests/review.
2. nullcontext(1) proves a valid producer seam invocation, not generation allocation, canonical 15-field reconciliation, companion commits, durable binding, close/lock lifecycle or independent-process exclusion. Those are explicitly delegated to the separate bounded primary review/evidence; DB and regression source were not opened here.
3. The two raw negative tests' nonrecursive `glob('*.msgpack.lz4')` proves absence of a canonical top-level artifact, not absence of hidden `.recording-generations` artifacts. No actual leak is apparent: inspected unsupported/missing-end branches never call publication. Treat this as a limited negative assertion, not full no-artifact proof; generation-aware failure custody belongs to the primary tests.
4. Compression-none unit coverage remains alias existence only, as before; it does not independently decode the uncompressed artifact. A single-publication samefile/bytes check establishes copied alias identity, not preservation across subsequent aliases/instances. Repeat-generation and later-failure preservation remain primary-suite obligations.

No meaningful prior assertion was deleted to manufacture green. No new specific runtime concern was found that warrants duplicating root's unit run. All broader runtime/static/full and final common-source qualification gates remain open until coordinator evidence resolves them.
