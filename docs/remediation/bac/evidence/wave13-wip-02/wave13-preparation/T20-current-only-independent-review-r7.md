# T20 current-only fix review R7

## Remaining finding

**P2 — Multi-event native rate state can violate the latest transition's reachable interval.** The R4 one-event rate witness is fixed by exact first-event replay, but `_validate_effects` does not validate rate movement when completion_count>1. `_validate_lane` accepts any finite difficulty in the authored band for rate_limited. The latest event and configured rate alone impose a narrower interval, independent of unavailable earlier event payloads.

Precise static witness using existing fifth-file helpers: construct `curriculum(dwell=10, mode='rate_limited', rate=1.0)`; commit `outcome()` then `outcome(batch=2)`. The first completion advances to stage2; the second retains stage2 because progress is0, with dwell10/count1. Both end at difficulty0.25. Change only saved `completion.lanes[0].difficulty` to0.9. The current validator accepts it: band membership passes, completion_count2 avoids exact first-event replay, stage2 meets reachability bound1+2-1, and latest zero progress requires no transition. Restored decisions immediately report0.9. Ten eligible transitions at rate1 must have reached stage2 target0.25 exactly from every possible predecessor in [0,1]. This is impossible producer state, not arbitrary plausible corruption requiring hidden history.

For general bounds L/H, latest eligible steps S, rate r and target T computed from the **new committed stage**, let B=r*S. The update is monotone in predecessor difficulty D∈[L,H], so its reachable output interval is:

`[min(T, L+B), max(T, H-B)]`.

Reject values outside this interval before installation (using an appropriate representation-aware boundary comparison, without admitting a material extra rate move). If B spans the band, the interval collapses to T. This rule applies whether or not the latest completion changed stage because production `_advance_lane` computes target after stage mutation. Do not accidentally use the pre-transition stage target.

The constructor also explicitly accepts rate0. With immutable rate0 and initial difficultyL, every reachable state must remain exactlyL even after multiple events. After two completions at rate0, changing difficulty alone to0.1 is currently accepted when the band is [0,1]. This is another available-policy invariant; it does not require reconstructing older events. The generic interval with B0 alone is [L,H], so rate0 needs its invariant separately.

Requested existing-file negative controls: multi-event saturated target mismatch; multi-event unsaturated values below/above the latest reachable interval; multi-event zero-rate movement. Include genuine endpoint/interior values and latest-stage-transition target controls, unchanged whole snapshot/owner-token usability on refusal, and future native continuation. The owned test file is896/900 lines; root must approve finite extra test budget before expansion. No sixth probe is needed or authorized.

## R4 repair dispositions

The reported R4 first-event dwell/stage/rate corruption cases now reject through pure exact replay from the authored initial lane. Static count equality, count/dwell simultaneous reset, latest-step minimum dwell and stage reachability from available transition count close the associated retained-history gaps. First-event replay mutates only a temporary dictionary; validation still precedes state/token/telemetry installation. The latest-signal checks correctly account for stage boundaries: a reset to stage1 can be a retreat from2; a reset to5 can be an advance from4. Unreset boundary-stage counters do not incorrectly demand an impossible retreat below1 or advancement above5. No valid-producer false rejection identified in these added conditions.

Future-generation receipts now refuse before the all-installed shortcut; actual older equal retries remain no-ops. Expanded tests cover all12 declared codec dtypes, nonzero complex/scalar/noncontiguous readings and malformed byte/dtype/shape/fingerprint/content cases. Static multi-event native continuation is now directly exercised. R4's P3 future-generation issue and stated codec/static coverage gaps are repaired in source/tests, subject to recorded runtime evidence below.

The `any((low_survival, negative_progress))` expression is equivalent to the former OR here: both operands are pure finite-number comparisons. No schema/default/waiver/compatibility bridge was introduced to satisfy the guard. The canonical event/previous_fraction model still resolves the older duplicated-baseline issue.

## Verdicts and scope

Spec compliance: **CHANGES REQUESTED**, limited to the remaining current-native multi-event rate-state P2 above. Code quality: **CHANGES REQUESTED** for that bounded validation repair and causal tests. No new P1. No additional blocking P3 identified. The P2 is in the current owned producer, not a deferred caller integration issue.

This is the same ongoing current-only T20 review, based on the full R4 five-file review plus complete R4→R7 source/test diff and current implementation handoff. Current-only removals remain authorized. T21 factory/constructor/current-caller work, T23 routing/identity and later native/provider/runner boundaries remain outstanding; no obsolete API should be restored to hide those seams. Final full/default/static/native/learning/E2E/restart/strict-private-curiosity gates remain owed. Bounded producer acceptance, once this P2 is repaired and checked, would not be integrated release. Root's authorized durable WIP commit/push and graceful halt can accurately record outstanding integration; this reviewer neither starts T21 nor owns index/commit/push.

## Candidate custody

Base `af6b91f7166be8ac799cb97a08accaabf1022cb0`; staged R7 tree `30dec57702114084aafcafa901c47db65531afc8`; manifest `wave13/r7-candidate.json`.

| Source | Lines | Actual SHA256 matching manifest |
| --- | ---: | --- |
| curriculum/base.py |66|d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268|
| curriculum/adversarial.py |516|ba79f1e650ac33180088475c7e3b94d92dbff083fdd6410308ef40ccbc4174cf|
| curriculum/static.py |64|22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59|
| training/episode.py |176|53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf|
| tests/test_townlet/regressions/bac/test_curriculum_events.py |896|0897c9b93c5421f9bc7defa87f3705bb5d9c1eec73354225135071c071f4aea7|

Production paths above are relative to src/townlet. Actual5/1718; approved projection2420; hard5/5000. CB/CS/EP hashes are unchanged from fully inspected R4. Only CA/test changed. No sixth implementation/helper/probe/fixture source was opened; no source/tests/index/tracked-docs edited, branches/worktrees/copies created, cleanup or commit/push performed. This ignored report is the only authored file.

## Execution record

Root supplied R5 intended RED159 collected/10 FAIL149 PASS, R6 semantic159 PASS, and R7 final159 PASS/0 warnings/20.8576wall. Root also supplied R7 custody172 source/573 config/13 artifacts/3 process PASS, registry14 with only MAIN available, and owned mypy/Ruff/Black/no-defaults PASS601. Global mypy remains six old factory-call errors explicitly assigned T21; it is not green. These are attributed root observations.

Reviewer selected existing fifth-file tests with:

`-k 'logically_impossible or genuine_first_event or static_multi_event or future_generation or codec or shared_fingerprint or malformed_later or changed_content_duplicate or prepare or checkpoint or rate_limited_resume or preflight'`

After explicit1CPU clearance, executed exactly the root-supplied identity wrapper and JSON spec. The attempt exited1 at its git write-tree custody check because `/workspace/hamlet/.git/index.lock` already existed (git exit128). No output directory/test result was produced. Execution session is closed. No lock was removed or index action attempted by this reviewer. This is an infrastructure/custody blockage, not a test failure or pass. Root was notified and a rerun awaits renewed clearance. The new multi-event rate P2 remains a precise static proof; no unapproved inline probe was run.

Root subsequently confirmed the lock is absent and no live Git/test/helper process remains, with no deletion/change performed. Root directed **no R7 rerun** because the same-source P2 is already established. Final R7 independent-test status is **UNRUN — CUSTODY PREREQUISITE FAILURE**, not a failing assertion or a pass. Root will reserve independent execution for the repaired candidate and avoid concurrent Git/custody operations. This reviewer's runtime is closed and the runtime barrier is released to root for its next tests-first repair packet.
