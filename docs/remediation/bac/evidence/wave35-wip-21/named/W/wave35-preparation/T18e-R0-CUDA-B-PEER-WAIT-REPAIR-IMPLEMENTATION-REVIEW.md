# R114 peer-wait implementation: independent exact review

Date: 2026-11-14. Reviewer: `/root/bac_astra_peer_wait_plan`; writer: `/root/bac_peer_wait_diagnosis`. The reviewer did not implement this patch or execute its tests.

**SPEC: PASS. QUALITY: PASS for the exact bounded test-only patch.** No concrete defect or assertion weakening found. This approves progression to root's frozen qualification, not a repaired runtime PASS, full B/BAC acceptance, or programme closure.

## Exact review subject

Paths below are relative to `/workspace/hamlet`; W is `.superpowers/sdd/2026-11-01-bac-remediation-upgrades`, P is W/wave35-preparation.

| Input | SHA256 verified |
| --- | --- |
| tests/test_townlet/regressions/bac/test_replay_rng_custody.py (1158 lines) | `0bf62bb8d0a411b12f55ad05459e7d5d7bbbbf1a0f879b3b592b405f9acab80d` |
| src/townlet/exploration/rng_custody.py (1195 lines, unchanged) | `6cb01ca77b58db5f4c4784dc36da566c06cf68c2a7c2ce227bb780549f3344f8` |
| src/townlet/training/replay_contract.py (881 lines, unchanged) | `8c0251c3c46e9c296e7b3bb5afcf2f6cdce8083fa22666c5a662be454a9a12f4` |
| P/T18e-R0-CUDA-B-PEER-WAIT-REPAIR-IMPLEMENTATION.md | `b4f70bb5695255003fd61620d49018c372cab9cd3ca85b67923394c692c8023d` |
| P/T18e-R0-CUDA-B-PEER-WAIT-REPAIR.patch | `ad211f6db426be0b73cf979d957e5d9ddf52dad8aae708b28c01092e6b736277` |
| W/wave35/r114-peer-wait-tests-only-grant.json | `83d19c85d20a132b53b1795801cb7bb41f2178916ef2285c500a5f25a4b81d87` |

The accepted plan is P/T18e-R0-CUDA-B-PEER-WAIT-REPAIR-PLAN-REVIEW.md, SHA256 `ad226cbd95ddb0e36a19631e79fef25512f633989da4cff92714b50d2bc94d42`, authored by this reviewer earlier in the same task. The grant binds that exact plan. Root supplies the patch's HEAD baseline `fe9cc615b1a0e3e94fb5dcf7e7e3fdea0be306eb` and baseline test SHA256 `5870d5315dd6f975f6e9513a492ba08f84671576f18e70f62795b122e13eabd7`. The root-produced exact patch was read in full and compared with the revised function. This reviewer performed no Git operation.

Inspection remains within the same three source/test bodies, now3234 total lines. Their line counts and hashes were checked directly. No additional implementation body or imported source was inspected. The previous plan's accepted contracts and source-path reasoning remain applicable because both admitted production bodies are unchanged.

## Specification and quality findings

The exact diff changes only the existing peer-wait test and the necessary RNGDeviceInvocation import. No shared helper, fixture, other test, production, timeout, entrypoint, signature or policy changes appear. Its source comment describes the bounded route distinction and retains historical RED provenance without a programme acceptance claim.

- The instance-level helper wrapper captures the original bound owner helper before patching. Its signature correctly matches lookup from the patched instance: no injected self is expected. It forwards kind, required explicit lineage, route, args, kwargs and mutation unchanged. It selects the actual worker Thread object, signals reached immediately before original context entry, and records/acquires only after that original context yields. It yields that exact lease and delegates original context exit through the enclosing `with`, including exceptional exits.
- The class-level factory wrapper correctly accepts the bound domain argument and calls the captured original bound factory. It forwards all actual participant/kind/lineage/device arguments, records the original returned invocation object, and returns that exact object without proxying entry, exit or completion. Its selected-worker filter does not exclude a wrong participant. A factory refusal becomes the worker's exception outcome, not a false successful wait.
- Recurrent keeps the original public-operation observer and original actual-dispatch tuple assertion. It now also retains its genuine yielded lease. The migrated route is chosen explicitly by fixture kind; there is no compatibility fallback or restoration of an obsolete public dispatch path. The unused helper capture for recurrent is valid because the supplied owner inherits the admitted ReplayCustody helper.
- The real registered peer and actual samplers remain. Worker launch stays within the genuine peer hold, all standalone domain-entering calls supply explicit None lineage, and the strong peer reference remains live to the final assertion. The worker is assigned before any observer can be called during the trial.
- Held-phase assertions preserve reached3 seconds, negative done0.5 seconds, live-row preservation and the selected ambient-state equality. The added acquired recheck after the negative wait, empty token list and empty migrated issuance list strengthen the observation. No owner/domain diagnostic acquisition was added to those held-state checks.
- Finally-based release and join5 seconds remain, with a surviving-worker failure and patches still installed during cleanup. Worker BaseException capture remains a failed outcome; original context failures are not suppressed. Released-phase checks require acquired, done, exactly one recorded genuine operation, exactly one actual migrated issuance with participant identity/sample/None/empty CPU inventory, or recurrent's original actual-operation tuple. Full serialized replay equality, a single nonexception real result and actual selected stream advancement remain unchanged.
- Exact type assertions supplement identity-preserving source delegation. They are not treated as independent authenticity proof. No token is fabricated, no admission-only result is mistaken for operation authority, and no invocation method is called from the main thread.

The factory observer records successful issuance, rather than attempted factory entry; that is the approved property. On the inspected source, admission precedes the factory. Any unsuccessful call propagates to an exception outcome and cannot satisfy released success. The pre-entry reached event remains a route-entry witness, not a scheduler stack proof. These limits do not create a defect in the approved bounded regression.

## Qualification still required

No application/import/test/lint/type/runtime execution was performed by this reviewer, and no runtime PASS is inferred. Root must bind collection and changed-test style to these exact bytes and run the focused flat/per/recurrent peer-wait3, then the exact affected54 inventory (healthy53 plus the isolated poison1) with genuine source/process/thread and child custody verification. Focused3 overlap affected54 and add no unique coverage. Unexpected failures must remain immutable attempts, with diagnosis rather than weakened assertions.

R113 affected54=52 PASS/2 FAIL and healthy53=51 PASS/2 FAIL remain historical authoritative failures. Root reports that the first new capture attempt stopped because a document-line metadata projection was stale (232 versus240); that is root-supplied attempt status, not this reviewer's execution observation. Retain that failed capture and bind a corrected attempt separately. The reviewed test/source hashes are unaffected by that reported metadata repair.

This verdict is confined to the observer implementation. Actual CUDA/B6, parent outcome/lock handoff, import-order proof, recurrent/runner integration, global typing, full/default suites, coverage>=70%, slow/learning checks, fresh final review and exact remote CI remain open; package accounting stays28/38/66. Any source change invalidates this exact-patch approval until reviewed again.

Only this review artifact was written. No code/doc/tool edits, application execution, new source bodies, Git mutations, branches/worktrees/checkouts/execution copies, deletion, cancellation or delegation were performed.
