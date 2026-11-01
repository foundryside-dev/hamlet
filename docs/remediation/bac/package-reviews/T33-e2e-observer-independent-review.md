# Independent static review: real recording shutdown observer

Verdict: PASS for the bounded test-instrument maintenance only. No actionable regression or weakened assertion found in the test diff against HEAD. This is not a runtime pass or a whole-T33/BAC pass. Legacy overwrite/generation preservation remains OPEN and outside this review.

## Reviewed inventory and provenance

HEAD verified: `214408b107730b4511b8a690541569aeca4b7b67`.
Candidate manifest declares tree `bd51b793cf9d41fd1dd8a2592183cda89da0da60` and 24 source guards; no index write or tree construction was performed.
Exactly four whole source files were inspected, totaling 962 lines:

| File | Lines | SHA-256 |
| --- | ---: | --- |
| `tests/test_townlet/regressions/test_episode_recording_shutdown.py` | 184 | `9874eed75d1b7491a5a8ef5fca1af7430b61aaff52037b8948b84e2636b67fa2` |
| `src/townlet/recording/recorder.py` | 470 | `6d42b8a43d38d1aae456c832001df7f71cf40834441e31962f7c62996c18ab0e` |
| `src/townlet/recording/data_structures.py` | 243 | `b8b2a5b2c202e8fc28ee907b645391cfb32f7d1a5530f528fa8ae6e076171158` |
| `src/townlet/recording/receipts.py` | 65 | `5b4f249a0771bf99565c32336068a8ec927ac91d65f750edab912e7ded9104a5` |

The three supplied hashes match, including their manifest entries. The data-structures hash was independently computed above. Administrative reads were repository AGENTS.md and the candidate manifest. The test-only diff against HEAD was inspected. Runner/config-builder implementation and other source files were not opened.

## Static assessment

The recorder really enqueues `_Capture(frame, sequence, ticket)` and `_Boundary(marker, ticket)`. The observer now projects these actual entries onto their frame/marker DTOs. It continues to recognize bare DTOs, which the inspected writer itself still accepts on its legacy path. This is observation of the existing transport, with no synthetic accepted frames, boundary insertion, or substitution of production queue entries.

Both wrappers call the saved real queue primitive exactly once. `_put` observes only after insertion; `_get` observes the removed entry and returns that original entry unchanged. Normal queue operations execute these primitives while holding their queue mutex, preserving the existing acceptance/dequeue ordering observation. Normalization omits envelope ticket/sequence details from the data comparison, appropriately retaining the pre-existing test's DTO persistence contract; this test does not establish ticket correctness.

The diff changes only imports, envelope recognition, and outstanding-entry diagnostics. It preserves all ten parametrized fresh attempts, the real `DemoRunner.run()` call and context-manager cleanup, exact two live steps/two accepted frames/one marker, stopped writer, empty queue, empty episode buffer, and accepted/dequeued equality. It adds no sleep, polling, manual finish, extra join, alternate producer, or cleanup repair.

The test still independently reads the actual path from the one SQL recording row, reads compressed artifact bytes, decompresses LZ4 and decodes MessagePack. Full decoded metadata and full decoded step lists are compared against the accepted DTO ledger (MessagePack normalization only), followed by version, frame index, survival, episode identity, reward contributors and other canonical SQL metadata, reason, and byte-size assertions. The patch does not replace this with a writer helper or expected-only artifact.

Outstanding entries now retain the raw transport kind while describing recognized DTO data. Unknown entries, including the plain-object shutdown sentinel, are described with kind/repr rather than passed to `asdict`. They remain in `outstanding`, so the unchanged emptiness assertion still fails; diagnostic tolerance does not permit queue residue.

Existing observational limits are unchanged: hooks target the Queue class globally, and accepted/dequeued DTOs are held by reference rather than serialized snapshots. The inspected writer does not mutate these DTOs on the exercised envelope path, and the patch introduces no mutation. Neither point is a new blocker for this bounded maintenance.

## Validation limits

Static reads and hash checks only; no imports, tests, runtime probes, source edits, index edits, branch/worktree operations, copying, or delegation were performed. No actual root runtime result was supplied during this review. The reported old observer failure (zero accepted entries despite actual runner output) is task context, not independent runtime evidence. Root's ten-attempt run remains the source of runtime verification.
