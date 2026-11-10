# Exact outcome ID independent source/spec/quality review

Static verdict: PASS for the finite C09/C13 producer alignment; no material source, specification, or test-quality defect found. Runtime qualification is pending explicit root authorization and is not claimed by this static verdict.

Reviewed candidate 2558d794476a4e7a1878b3c334b62d1733d62bb9 against the supplied base cfef2979e70f0cc9a850c9928386e2e243a0b21b and review-package diff. Read the brief, proposal, implementation report, AGENTS.md, review package, and exactly the three complete authorized source/test files. No fourth source/helper/fixture or excluded BANK test was opened.

The changed LaneOutcome predicate accepts precisely the same nonempty string domain as exact_world_ids. The old strip predicate excluded valid space/tab/CR world identities. Keeping isinstance and replacing only the emptiness expression repairs that domain mismatch without admitting empty strings or nonstrings. There is no normalization, case folding, Unicode conversion, roster narrowing, serializer or schema change, fingerprint recipe change, or compatibility adapter. Both current-state construction and frozen decoding converge on the repaired validator. Existing JSON encoding preserves embedded controls, whitespace, and composed/decomposed Unicode distinctly.

The 27-case test matrix exercises actual WorldRosterDeclaration, LaneOutcome, current state, and frozen public behavior. The explicit finite dense CPU tensors, positive survival of 1, planned horizon 2, valid completion reason, integer counters, and finite numeric fields prevent unrelated DTO failures from masquerading as identity regressions. Ordinary-ID and declaration controls establish the preconditions. Space/tab/CR cases test construction and both round trips; empty/None/integer/bool/bytes cases retain construction and current-decoder refusals. Existing exact identities test leading/trailing spaces, case, Unicode composition, and embedded CR/tab/space. Fingerprint comparisons hold other fields constant and distinguish all twelve exact identities. These assertions measure observable contracts rather than reproduce the validator. Full envelope comparisons also check tensor values, dtype, shape, layout, and CPU placement.

The reported old-code 10 failures / 17 passes and formatting checks are root/implementer-attributed evidence, not independently executed observations. This finite DTO change does not establish actual parent/runner/BANK integration, global mypy completion, or full acceptance; those remain open with root. No material in-scope finding is deferred.

Observed custody:

| File | Whole lines / cap | SHA-256 |
| --- | --- | --- |
| src/townlet/config/world_roster.py | 312 / 350 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| src/townlet/training/episode.py | 176 / 250 | 1616ba8c526051a4f3b8593a5c86daf5d405d311aacf9f0c375bce1756ceae4f |
| tests/test_townlet/regressions/bac/test_lane_outcome_exact_world_ids.py | 171 / 450 | 82124334b10aec6e8d978b078224da2dc49240629635c48d74156f5617fb3088 |

Total 659 lines within the reserved 1,050-line ceiling. This ignored review report is the only file written. No source/test/index changes, standalone imports/runtime, commits, pushes, branches, worktrees, copies, installations, deletions, or subagents.

## Authorized independent execution and final verdict

After root explicitly authorized the already-collected 27-case independent run, executed only:

`python /workspace/bac-review-2026-11-01/qualification/run_bac_packet_checks_locked.py /workspace/bac-review-2026-11-01/qualification/wave27-r1-independent-spec.json`

The child exited 0 in 3.3872482776641846 seconds against candidate 2558d794476a4e7a1878b3c334b62d1733d62bb9 and base cfef2979e70f0cc9a850c9928386e2e243a0b21b. Then executed the authorized positive verifier:

`python /workspace/bac-review-2026-11-01/qualification/verify_bac_run.py /workspace/bac-review-2026-11-01/qualification/wave27-r1-independent-spec.json`

Verifier exited 0: 27 passed, zero skipped/xfailed/xpassed/warnings; 349 source guards, 573 config digests, 13 protected artifacts, one process identity, 14 worktree registry records, one available worktree; source/index/import/thread/fixture custody PASS. The run log is `/workspace/bac-review-2026-11-01/qualification/wave27-r1-independent/independent.log`, SHA-256 `e46afbabb7bbc53b48c5ff404a93101ea06f0159f1be3ef0df1d9468b865f325`. All authorized child/verifier processes are closed.

Final finite source/spec/quality and independent-execution verdict: PASS, no material in-scope finding or gap. This closes this reviewer’s pending runtime qualification only. Parent/runner/BANK integration, global mypy, and whole-BAC/full acceptance remain open and are not inferred from this evidence. No additional source was inspected or changed.

## Final contract verification

Reviewed `CURRENT-EXACT-OUTCOME-ID-CONTRACT.md`; observed SHA-256 `794c4494e230d49713a80291ecb24892e3451cde0e131ea2c40f43551276590b` matches the supplied final contract identity. Verdict: PASS, no material contradiction or overclaim found against the previously inspected three whole files and this reviewer's actual independent receipt.

The prose accurately states exact nonempty raw-string identity, whitespace acceptance without normalization, unchanged native/frozen shape and fingerprint recipes, existing identity preservation, the three whitespace regression families, retained empty/nonstring rejection, and the 659-line three-slot inventory. Its independent timing of 3.387248 seconds agrees with this reviewer's actual 3.3872482776641846-second custody receipt. Root's 3.10259-second result and other root-only checks remain explicitly attributed, not independently re-executed here.

The old owner-fixture failure at episode_lanes.py:48 is explicitly root-reported and precedes DTO assertions because three current ENV inputs are missing; the contract correctly leaves coherent parent-fixture integration open and does not claim a broad suite rerun. BANK remains a draft awaiting test-gap correction and implementation, not implemented or qualified by this DTO proof. The excluded 901-line BANK draft was not inspected. This verification read only the final prose and its hash, appended only this ignored report, and performed no additional source reads, runtime, code edits, or index operations.
