# T20 current-only fix2 independent review R9

## Remaining material defect

**P2 — One-target-ULP validation rejects genuine saturated native output because production cancels a larger predecessor.** The latest-rate interval and zero-rate invariant are correct in real arithmetic, but the one-representable-target-step allowance does not cover the current producer's `D + (T - D)` arithmetic over the whole predecessor band. This is a same-source native round-trip defect, not an obsolete-format compatibility issue.

Precise genuine-source witness for the existing fifth file (not executed as an extra probe):

1. Construct `curriculum(dwell=1, mode='rate_limited', rate=0.01, low=0.0, high=0.4)`.
2. Use existing `advance_to_stages(manager, [5])`: the four real improving long completions reach stage5/difficulty0.4, with batch IDs1–4.
3. Commit `outcome(batch=5, steps=1, horizon=2)`: retreat to stage4, difficulty0.39.
4. Commit `outcome(batch=6, steps=1, horizon=4)`: retreat to stage3, difficulty0.38.
5. Commit `outcome(batch=7, steps=40, horizon=400)`: retreat to stage2; new target0.1 and budget0.4. The producer computes `0.38 + (0.1 - 0.38)`, whose binary64 result is `0.09999999999999998`.
6. Load the manager's own checkpoint into an identically configured fresh manager. `_validate_effects` computes the collapsed mathematical interval at0.1 and expands its lower endpoint by only one step to `0.09999999999999999`. The genuine saved difficulty is another float below that bound, so load raises `ValueError('Difficulty is unreachable under the latest completion rate budget')`.

All other new constraints permit this genuine history: seven unique monotonic events; current stage2 with reset clocks; previous fraction0.25/current0.1 permits retreat; band membership holds. No snapshot mutation, made-up earlier history or invalid DTO is required. The exact integer durations and configured rate/band are supported current inputs.

The eight R8 malformed-state witnesses are repaired, but the producer/validator still disagree on this valid current state. Do not solve it by an arbitrary two-target-ULP allowance: cancellation error depends on the predecessor's scale, and the floating saturated expression need not be monotone across all interior predecessors. Evaluating only the production formula at band endpoints is also not a universal rounding proof.

### Recommended bounded repair and witness

Align production movement with the validator using cancellation-free directional movement. For predecessor D, target T and nonnegative budget B, use `min(T, D+B)` while approaching upward, and `max(T, D-B)` while approaching downward, with the existing band clamp. Saturated movement then selects T directly; unsaturated movement has only the same addition/subtraction used in the interval endpoints. These operations are monotone over the allowed finite band, so `[min(T,L+B), max(T,H-B)]` is justified for floating production too, rather than merely for the ideal real-valued equation. Alternatively provide an equally sound rounding envelope for the existing producer, covering all predecessors, not just tested endpoints.

Keep the explicit immutable zero-rate invariant and new-stage target semantics. No schema/version/legacy adapter or prior-event reconstruction is necessary. Current legitimate behavior need not preserve the old expression's cancellation bit pattern; the repaired current producer must emit snapshots its own validator accepts.

Add the exact seven-event native round-trip/future-equivalence test to the existing fifth file before production repair. Retain all eight malformed-rate refusals and seven genuine controls. A symmetric nonzero-band/saturation case is useful if it fits the approved allowance, but the causal seven-event witness is the required reproduction. Current test size967/1000 leaves33 lines; obtain a finite budget ruling before exceeding that named ceiling.

## Dispositions and verdicts

R7 latest-rate corruption finding: intended domain constraints implemented correctly, including target computed from the new committed stage and rate0 remaining at the authored lower bound. R8 actual malformed controls substantiate their need. R4 first-event effects/static counts/available-history checks and future-generation receipt repairs remain intact. No new P1 or separate blocking P3 found in this delta.

Spec compliance: **CHANGES REQUESTED** for the genuine native false rejection above. Code quality: **CHANGES REQUESTED** for producer/validator floating arithmetic alignment plus causal regression. No bounded producer acceptance yet despite existing tests passing. This is not a T21 caller issue; it is wholly within the current owned T20 implementation.

## Actual independent execution

After root's explicit1CPU clearance and closure of its runtime/Git/custody processes, executed exactly the supplied `run_bac_packet_checks_locked.py` command using `wave13-r9-astra-independent-spec.json`, then executed the unchanged `verify_wave09_run.py` custody command. No helper source was read.

Selection in the existing fifth file:

`-k 'latest_rate or logically_impossible or genuine_first_event or static_multi_event or future_generation or codec or shared_fingerprint or malformed_later or changed_content_duplicate or prepare or checkpoint or rate_limited_resume or preflight'`

Actual result: **129 passed,45 deselected,0 warnings**, pytest0.50s; wrapper wall4.843864679336548s, exit0. This includes all15 newly authored latest-rate cases plus the prior adversarial/preparation/native/codec controls selected by the expression. The new cancellation witness above is not among those tests and is a precise static proof pending the authorized tests-first follow-up.

Custody verifier exit0: exact base/tree confirmed;172 source guards,573 config digests,13 protected artifacts,1 process identity,14 registered worktrees; source/index/import/thread/fixture custody PASS. Both execution sessions are closed; runtime barrier released to root. Unlike R7's preserved prerequisite failure, R9 independent tests actually ran and passed.

Log: `/workspace/bac-review-2026-11-01/qualification/wave13-r9-astra-independent/astra-independent.log`, SHA256 `909211f080fb81e6f858c15324d7945e706d83d8b455ec004d4b833e8b8a3e4b`. Manifest SHA256 `714e3ee4fa9bfd11141a30eb361989c52fa39707ec3c4145409178edd6f82896`. Harness SHA256 supplied by execution receipt: `180558c22da088a57326aa9251fbb64761e2788f18cb982532525b84b571f791`.

Root separately supplied R9 full owned174 PASS/0 warnings/16.5691s, local mypy/Ruff/Black/no-defaults601 PASS, and global six old factory-call errors still open. Root's R8 causal RED was8 FAIL166 PASS with all eight intended call-phase DID NOT RAISE. Those are attributed observations, not substituted for the independent result above.

## Candidate/source inventory

Base `af6b91f7166be8ac799cb97a08accaabf1022cb0`; staged tree `16a68ff4301c393dd75bf8b0c5b6ad88997c8749`. Read complete R7→R9 CA/test diff, updated fix2 implementation handoff and complete fix2 tests-first report, against the prior full five-file review. Actual hashes checked:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/curriculum/base.py |66|d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268|
| src/townlet/curriculum/adversarial.py |531|af3180a57d5c2d0e7f55fa1dc4f9e3757941f92f13ec58bbda531c8e7f8a1196|
| src/townlet/curriculum/static.py |64|22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59|
| src/townlet/training/episode.py |176|53b52a8a56d5fc2714604198fc4516c5c4d48258537a9dcbe4ccd00dae743cbf|
| tests/test_townlet/regressions/bac/test_curriculum_events.py |967|e6d3b7ad72c102175d4ed4cc1541e6fa4edbce6a164012936dc5059d2e194e0e|

Total5/1804 actual; projection2520; hard5/5000. CB/CS/EP unchanged from prior complete inspection. No sixth source/helper/probe/fixture, no inline execution of new source, no source/test/index/tracked-doc edit, no branch/worktree/copy/cleanup/commit/push. Only this ignored report authored.

## Handoff versus release

Once the owned producer's P2 is fixed with causal RED/GREEN, fresh review and independent verification, root can record bounded T20 producer handoff status and durably publish the current work under the approved WIP policy, then gracefully halt as requested. This does not authorize starting T21 here or claim integrated release. Six old factory-call type errors, current-caller maintenance, identity/provider/POP/runner/native-boundary integration, earlier-full tests/guards and final strict-curiosity/learning/native/E2E/restart/substantive BAC gates remain owed. No compatibility protocol is restored and no final criterion is waived by this review.
