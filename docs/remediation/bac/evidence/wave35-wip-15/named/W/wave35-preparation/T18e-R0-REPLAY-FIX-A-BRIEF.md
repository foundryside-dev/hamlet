# Replay repair slice A — tests first, then separately granted implementation

Read this first. This is the continuation of the finite BAC R0 replay repair, not a new programme. Base HEAD678513c7540a61114d59a17d1b1e0eb8a06ce0a2; initial R76 tree ea50156c62b594cb1343f4d2561120b77164707b. Root is integration/execution owner.

## Source boundary and immediate authority
Fresh context: exactly these five whole bodies, including future growth, never >5000 lines:
- src/townlet/training/replay_contract.py current352, cap550 (production READ ONLY until root RED grant)
- src/townlet/training/replay_buffer.py current715, cap850 (same)
- src/townlet/training/prioritized_replay_buffer.py current1142, cap1300 (same)
- tests/test_townlet/regressions/bac/test_replay_rng_custody.py current684, cap1400 (sole permitted source WRITE now)
- src/townlet/exploration/rng_custody.py current371, cap371 READ ONLY
Projected4471. Measure before reading. Do not read recurrent, bootstrap helper, archive helper, caller or sixth implementation body, including via excerpts. Public supplier prose is allowed. No source copies, new branches/worktrees/checkouts, delegation, Git/index, imports/runtime/compiler/static/formatter actions. Root executes exact-source tests after freeze; author may use wc/sha and inspect/edit owned text. No backward compatibility adapters/default lineage; no capability reduction. Preserve all existing controls/source not yours. No tooling writes.

## Requirements and review facts
Read P/T18e-R0-REPLAY-STAGEB-REVIEW.md and ADDENDUM.md (verbatim findings), STAGEB-FIX1-PROPOSAL.md (sealed SHA2a404c22...), StageB brief/report and REPLAY-CUSTODY-API.md. P is this directory. Original source author context reached4777/5000; fresh split avoids discarding necessary tests. Existing tests: distinct healthy11, causal9, poison1 all PASS on R76 with815 source/process/import custody. Passing them does not discharge defects. Original28qualified/38remaining/66 unchanged.
A owns B1 flat/PER stale DTO/current-target revalidation and mutable DTO rejection; B2 shared issuer-held prepared material/identity-only handle; B5 genuine typed guard signatures including required lineage and PreparedReplay return; B4 shared/flat/PER controls below. B3 recurrent scratch classification and recurrent-specific B4 are next separate slice. B6 remains required additive CUDA design; DO NOT modify CUDA semantics in A.

Tests now:
1. Genuine flat/PER validate width1 -> same owner clear/push width2 -> materialize old DTO must refuse with full unchanged live state; direct fresh prepare mismatch healthy comparator. Mutated returned validation material cannot become authority.
2. Fabricated/copied/reinitialized handle/material substitution refused, unchanged full live state; identity-only capability has no material-taking public constructor or payload field. Important: failed admitted install legitimately stales prior domain currency; prepare FRESH for subsequent positive one-use proof, do not assume earlier authentic handle remains current.
3. Same held outer authentic lineage prepare/install succeeds; sibling ordinary sample and owner mutation invalidate correctly. Actual staging-copy/archive fault before publication preserves state/healthy usability; actual assignment fault after >=1 published field quarantines, including clear/sample/install refusal. Flat/PER distinct staging paths covered. Installed data independent of retained input/candidate bytes. Shared guard once is sufficient where genuinely shared; preserve family distinctions.
4. Extend existing isolated replay_poison child to preissue prepared handle, then poison via genuine lease, require sample/new prepare/old install refusal and local clear cannot heal domain. Preserve exact role/message/import/PID/PPID fields; parent registry uses current CPU profile, not CUDA claim.
Existing correct branches may already PASS; do not manufacture RED for already-correct behavior. Defects B1/B2 require genuine causal RED before production fix. B5 initial source erasure is confirmed; root will check actual missing callers after fix without suppression.

Supplier prose: DOMAIN-REPLAY-API, DOMAIN-NESTED-TOKEN-API, DOMAIN-STATUS-LOCK-FACT, REPLAY-POISON-BOUNDARY, REPLAY-HELPER-RNG-FACTS, QUALIFIED-CHILD-CUSTODY-API. Scratch generator calls are ambient-free/persistent-preserving, not literally RNG-free. No status under owner lock or claim status diagnostic is atomic admission. Domain before owner; token/owner revision fences and completion lifetime retained.
Static existing failures: Ruff test import, Black five source, one new default raised ratchet601>600; fix owned text during appropriate production stage, never increase ratchet or hide typed callers. Root runs formatter only when authorized writer frozen, with budget remeasurement.

## Report and freeze
Write P/T18e-R0-REPLAY-FIX-A-REPORT.md with exact initial/final lines+hashes, new test node IDs, intended causal assertion, honest UNRUN status, source-qualified API questions. Return short summary and freeze. Root captures/tests -> genuine RED evidence -> separately grants three production file fix. This is fix round1/5 of original material findings, resliced for source budget, not a reset of review accounting. Independent review afterward; no self-approval or package completion claim.

