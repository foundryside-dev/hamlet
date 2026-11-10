# Independent current curriculum consumer review

Verdict: **REPAIR REQUIRED — one P2 test-coverage finding**. This is a source/spec review, not runtime qualification. Root collection/affected-test evidence is still owed to this reviewer. No test, import, runtime probe, git/index/branch/worktree, source copy, implementation edit, or subagent operation was performed. Only this ignored review report was written.

## Exact inspected source inventory

Line metadata and SHA256 were checked before source reading. Exactly five whole current sources were inspected, totaling 1409 lines against the 3100 aggregate ceiling; no sixth implementation/test/helper or historical source was opened.

| Source | Lines | SHA256 |
| --- | ---: | --- |
| tests/test_townlet/unit/curriculum/test_curriculums.py | 684 | c9502d0136fe3491dc2e80e5566774ae9bb0f4302b8ff164c04c661c4d68ace5 |
| src/townlet/curriculum/adversarial.py | 537 | 2194cc4075096670181a50cf1be2158cd68334a07111818ad75382cd73890f4f |
| src/townlet/curriculum/base.py | 66 | d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268 |
| src/townlet/curriculum/static.py | 64 | 22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59 |
| src/townlet/curriculum/factory.py | 58 | 10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71 |

Public/spec data read: the exhaustive original42 mapping in CURRICULUM-COLLECTION-REPAIR-REPORT.md; accepted public DTO capsule at docs/remediation/bac/evidence/wave15-wip-01/wave15-preparation/ACCEPTED-CURRICULUM-PRODUCER-RECEIPT.md; current-only T20 task brief and implementation prose under docs/remediation/bac/evidence/wave13-wip-02/wave13-preparation/. Historical source inventory hashes embedded in prose were not used to open historical source.

## P2 — low-survival retreat no longer has an independent causal assertion

Location: TestAdversarialCurriculumStageRetreat.test_should_retreat_with_low_survival (current unit source around line307), with related configured-threshold witness around line399.

Accepted current design requires retreat after eligible dwell when either survival is below its threshold OR progress is negative. The migrated low-survival test first reaches stage3 at fraction .8, then supplies fraction .2. Its progress is -.6. Consequently its stage3→2 result and retreat reason are fully explained by the separately tested negative-progress branch. Other above-floor low-survival calls in this file also lower the previous fraction; none establishes low survival with nonnegative progress at eligible dwell above stage1.

Concrete source-level counterexample (not executed): replacing the retreat condition in _advance_lane from `(fraction < survival_retreat_threshold or progress < 0)` with `progress < 0` leaves all asserted stage outcomes in this migrated file unchanged. It removes a substantive accepted capability while retaining all52 expected parameter-expanded passes. This is a causal gap in the migrated consumer tests, not a demonstrated production defect.

Required repair within the existing low-survival identity: reach stage4 with genuine improving completions, then commit 100/1000 survival with entropy1 to retreat to stage3 and establish fraction .1. Next commit 200/1000 survival with entropy1, using increasing batch/world sequence identities. Assert fraction .2, positive progress approximately .1, dwell eligibility, resulting stage2, reason retreat, and reset counters. This isolates low survival from negative learning without injected history or compatibility APIs. Alternatively use the same causal structure at another nonboundary stage.

## P3 — configured-threshold behavior is not independently discriminated

The configured-threshold test persists all authored fields correctly, but its first .75 completion has dwell150 below authored200, so it cannot distinguish a hardcoded advance threshold or a dwell comparison mistake. Its final .25 completion has negative progress, so it cannot establish use of the authored retreat threshold .25. The entropy boundary is discriminated. This is a strengthening opportunity beyond the mandatory P2 repair; the report should not overstate independent behavioral coverage for all configured thresholds.

Useful controls: with sufficient dwell and low entropy, a first fraction between default .7 and authored .75 must stay; independently, high survival/low entropy with eligible steps between100 and200 must stay under dwell200; low-survival positive-progress events on opposite sides of the authored retreat threshold distinguish use of that threshold. Keep all setup through genuine completions.

## Positive assessment and bounded limits

The remaining migration is substantive current-contract testing. All42 mapping identities are present, with six additional method identities and static expected52 expanded cases. Current constructors and DTOs are genuine; policies and identities are explicit. No tracker substitute, compatibility alias, skip, xfail, deselection or swallowed exception appears. Stage histories are reached through actual commits. Surviving tests genuinely assert fixed decisions, per-lane isolation, survival fractions and equal-unit progress, supplied entropy gating, complete stage metadata, counter resets, stage-band mappings, selected rate effects, singleton bands, snapshot/load ownership, same-policy refusal, typed current-schema refusal, duplicate idempotency, atomic whole-batch refusal and reward-signal independence. Literal stages, difficulties, reward components, transition identities and tensor content prevent broad vacuous pass-by-weakening.

Replacing old Q-derived entropy, reward-average progress, step-reset ownership and load-time reconfiguration is consistent with the accepted current-only contract. These are legitimate ownership/schema changes rather than missing compatibility. Factory source is current-only and unchanged; no original mapped factory case needs restoration in this repair.

This review does not claim full production test exhaustiveness or validate the external episode implementation. The DTO capsule supplies that public contract within the finite source scope. Root must repair the P2 witness, send final source metadata plus actual affected-test/collection evidence, obtain repair review, and only then proceed to the broader gate. No runtime PASS is claimed here.

## Root evidence received after initial review

Root reports actual52 collection PASS with source797 hash/index custody bound to tree8362228e. Owning current consumer plus regression runtime was still active/source-frozen when reported; compiler CLI qualification was running separately. These are received root observations, not reviewer execution. No affected runtime outcome has yet been supplied. The source-level P2 finding and repair-required verdict remain unchanged by successful collection.

Root subsequently reports affected runtime completed: **227 PASS, 0 skips, 0 warnings**, 10.35648 seconds wall, comprising52 migrated cases plus175 accepted-event regressions. Root custody verification PASS covers797 sources,573 configs,13 artifacts,3 exact process identities, tree8362228e. This is explicitly root-executed evidence; this reviewer ran no runtime/import/test commands. Successful current implementation execution does not establish sensitivity to the missing independent low-survival cause. **REPAIR REQUIRED remains the verdict** until the finite test strengthening and fresh source review/qualification complete.

## Fix1 scoped re-review — APPROVED

This section supersedes the initial repair-required verdict for the exact fix1 candidate only. **P2 ADDRESSED; P3 ADDRESSED. No remaining defect or new breakage found in the finite fix diff.** No unrelated optional observation was added to the ledger.

Reviewed CURRICULUM-COLLECTION-fix1.patch, the updated original repair report including actual root execution attribution, and both changed method bodies in current source. Rechecked metadata for the same five whole-source inventory: test753 SHA256 `c414386e87ab43d11bfbae86cb5264102b9cb8985f2fcf618157cf0519e278da`; adversarial537/base66/static64/factory58 retain exactly the four hashes listed in the initial inventory. Aggregate1478/3100. No sixth source, historical full source, runtime/import/probe, git/index/branch/worktree/source-copy or delegation operation occurred; only this ignored report was appended.

**P2:** The existing low-survival identity now genuinely reaches stage4, establishes fraction.1 while retreating to3, then supplies fraction.2 with positive progress.1, high entropy1 and eligible dwell200. Exact state and transition assertions require3→2 with counter reset. Removing the low-survival OR arm now leaves stage3 and fails the test; negative-progress behavior cannot satisfy the asserted event. Genuine monotonic event identities, full valid reward components and native DTO readings remain intact.

**P3:** The existing configured-policy identity preserves its original assertions and adds three independent managers. Advance.75 is discriminated from default.7 by fraction.72/progress.72/dwell720/entropy.3 staying at1, followed by genuine.8 advance. Dwell200 is discriminated from default100 by fraction.9375/progress.9375/entropy.3 with150 eligible transitions staying at1, then a genuinely improving event advancing at cumulative310. Retreat.25 is discriminated from default.3 by increasing fraction.1→.27 at high entropy and dwell540 retaining stage3; a later genuine.1 reset followed by increasing.24 at dwell480 must retreat2→1. Both retreat sides have positive progress, so they isolate survival threshold use. The added setups satisfy the declared current rules and introduce no fabricated history or compatibility API.

The patch changes only those two existing method bodies: all42 original identities plus six controls and52 expanded cases remain. It neither removes existing current coverage nor changes production. Initial positive assessment therefore carries forward, with its identified causal gaps closed.

Received root evidence for candidate tree `9644cd5f4da362357d6ae4f448325efa91335f34` / base47d82: collection52 PASS; exact command recorded in the repair report runs the current consumer and accepted-event regression files with `-q --no-cov -p no:cacheprovider -p bac_source_identity -n 2 --dist worksteal` and designated wave34-r9-curriculum basetemp. Result **227 PASS, 0 skips, 0 warnings**,9.3245878 seconds wall, child exit0. Root output log SHA256 `0fc5ee55e2a96d30e142f418f2a16585f0344de515517ec8bf1964a5efd5f283`; root custody PASS797 guarded sources/573 configs/13 artifacts/3 exact pytest identities/index, with report registry14/MAIN1. These are root-executed observations, not reviewer execution.

**Clean scoped approval:** the finite consumer repair and both review findings are closed at the above hashes. This permits root to proceed to the separately required broader gates; it does not claim those gates, compiler CLI completion, or overall BAC release have passed.
