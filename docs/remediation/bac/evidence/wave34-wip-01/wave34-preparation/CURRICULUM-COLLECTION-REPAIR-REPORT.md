# Curriculum collection prerequisite repair — authored, awaiting root qualification

Only `tests/test_townlet/unit/curriculum/test_curriculums.py` changed. No production, RP/runtime source, existing new runtime test, config, episode implementation or helper implementation was changed/read outside the five whole source slots. No runtime/import/probe/compile/pytest/uv/index/git/branch/worktree/source-copy/subagent operations were performed. Root owns collection, affected tests, independent Astra review and the subsequent full797-source gate. This report claims no test PASS or complete BAC qualification.

## Cause and authority

Root's supplied full collection result selected8495 and stopped at the old unit file line27 importing removed `PerformanceTracker`; no broad runtime gate had begun. Inspection established that the remaining old file also assumed removed tracker tensors, Q-value calculation/decision-time mutation, configure bridges, default construction, flat checkpoint fields and load-time policy replacement. Merely deleting the failing import would conceal those obsolete consumer calls.

`AGENTS.md` owner zero-BC clarification requires direct caller replacement and forbids aliases/adapters. `CURRICULUM-COLLECTION-original-T20.md` is historical: current authority is the accepted T20 current-only task/implementation prose in `docs/remediation/bac/evidence/wave13-wip-02/wave13-preparation/`. It explicitly removes PerformanceTracker, Q-derived entropy calculation, decision-time commitment, configure_from_training and seven-array checkpoint interpretation. Current performance is completed survival fraction and its equal-unit delta; rewards remain genuine retained components. Current load validates an exact same-policy native schema rather than reconfiguring the manager. No substantive accepted current consumer capability was found missing.

The public DTO capsule `docs/remediation/bac/evidence/wave15-wip-01/wave15-preparation/ACCEPTED-CURRICULUM-PRODUCER-RECEIPT.md` supplied source-verified EpisodeCompletion/LaneOutcome signatures, valid cap reason, finite readings and explicit identity constraints without reading episode.py. Existing current-only T20 prose and the scoped sources supplied the current checkpoint/metric meanings and supported lane_outcome_state operation. Test world labels `world-N` are declared consumer-test identities only, with no runtime world-roster qualification claim. No factory case existed in this old unit file; its static/adversarial choices remain covered by genuine direct constructors. No fake tracker, fake outcome, compatibility alias, skip, xfail, deselection or test deletion was added.

## Exact source inventory

| Whole source | Access | Final lines / ceiling | SHA256 |
|---|---|---:|---|
| tests/test_townlet/unit/curriculum/test_curriculums.py | modified |684 /2200| c9502d0136fe3491dc2e80e5566774ae9bb0f4302b8ff164c04c661c4d68ace5 |
| src/townlet/curriculum/adversarial.py | read only |537 /600| 2194cc4075096670181a50cf1be2158cd68334a07111818ad75382cd73890f4f |
| src/townlet/curriculum/base.py | read only |66 /100| d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268 |
| src/townlet/curriculum/static.py | read only |64 /100| 22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59 |
| src/townlet/curriculum/factory.py | read only |58 /100| 10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71 |

Five sources1409 lines /3100 ceiling. Original old unit1131 lines SHA256 `702d78e904bfa1ae9ab4ce8281a9e518de719a5e41adf33ae78e9431ae73fb36`; other four hashes unchanged. The only additional artifact is this ignored report under the established .superpowers ignored handoff destination; ignore status was not probed with git.

## Complete original-case mapping

All42 original class/method identities remain; historical names mentioning tracker/tensor/entropy calculation are retained for review continuity and have explicit current-contract docstrings. No expectation is implemented by a fake replacement class. All stage fixtures reach their stages through actual improving completions, never stage/checkpoint injection. All policy fields and event identities are explicit.

| Original class | Original method | Current assertions |
|---|---|---|
| TestStaticCurriculum | test_returns_same_decision_for_all_agents | Three initialized lanes retain exact authored difficulty/reward/meters/depletion/reason. |
| TestStaticCurriculum | test_respects_different_difficulty_levels | Genuine explicit easy.2/hard.9 policies produce their different fixed decisions. |
| TestStaticCurriculum | test_checkpoint_state_returns_all_config | Exact native top schema, version2/static identity, full authored config and initial lane. |
| TestStaticCurriculum | test_load_state_restores_configuration | Same-policy completed state roundtrips exactly; incompatible policy refuses atomically. Supersedes old load-time reconfiguration. |
| TestStaticCurriculum | test_checkpoint_restore_roundtrip | Heterogeneous completed lanes preserve complete native state, decisions and metrics. |
| TestPerformanceTracker | test_update_step_accumulates_rewards_and_steps | Real completion windows retain all four supplied reward readings and per-lane eligible dwell/count. Producer accumulation is no longer curriculum-owned. |
| TestPerformanceTracker | test_update_step_resets_on_done | New completed window replaces lane0 metrics, retains cumulative stage dwell, leaves lane1 unchanged; equal retry leaves native state unchanged. Producer step-reset behavior is superseded here. |
| TestPerformanceTracker | test_get_survival_rate_calculation | Actual50/100/250 durations with horizon500 produce.1/.2/.5. |
| TestPerformanceTracker | test_get_learning_progress_positive | Fractions.2→.5 yield+.3 despite strongly decreasing reward; baseline.5. |
| TestPerformanceTracker | test_get_learning_progress_negative | Fractions.5→.2 yield−.3 despite strongly increasing reward. |
| TestPerformanceTracker | test_update_baseline_stores_current_average | Completed fraction baseline.3→.6 and progress+.3 replace old average-reward units. |
| TestAdversarialCurriculumStageAdvancement | test_should_not_advance_without_minimum_steps | Perfect completion500 cannot satisfy dwell1000; no telemetry. |
| TestAdversarialCurriculumStageAdvancement | test_should_not_advance_from_stage_5 | Real stage5 followed by further improving full survival stays5; no extra transition. |
| TestAdversarialCurriculumStageAdvancement | test_should_advance_with_all_conditions_met | Actual stage2→3 at fraction.8/progress.05/entropy.3; stage counters reset. |
| TestAdversarialCurriculumStageAdvancement | test_should_not_advance_with_low_survival | Positive progress.2/low entropy cannot advance with low fraction.2. |
| TestAdversarialCurriculumStageAdvancement | test_should_not_advance_with_negative_learning | High survival.72 but negative fraction progress.03 retreats despite large rewards. |
| TestAdversarialCurriculumStageAdvancement | test_should_not_advance_with_high_entropy | Fraction.8/positive progress/dwell400 blocked by entropy.8. |
| TestAdversarialCurriculumStageAdvancement | test_stage_transition_logs_reason | Entire exact canonical transition identity/stages/reason/fraction/progress/entropy/dwell; equal retry does not re-emit. Supersedes nullable old agent_id. |
| TestAdversarialCurriculumStageRetreat | test_should_not_retreat_from_stage_1 | Low-survival completion cannot cross lower stage bound; no telemetry. |
| TestAdversarialCurriculumStageRetreat | test_should_not_retreat_without_minimum_steps | Actual stage2 then low-survival/negative-progress duration100 cannot meet newly reset dwell500. |
| TestAdversarialCurriculumStageRetreat | test_should_retreat_with_low_survival | Actual stage3→2 on fraction.2, retaining reason and counter reset. |
| TestAdversarialCurriculumStageRetreat | test_should_retreat_with_negative_learning | Actual stage3→2 on high fraction.78 but negative progress.02 despite high reward. |
| TestAdversarialCurriculumEntropyCalculation | test_entropy_zero_for_deterministic_policy | Producer-supplied exact entropy0 retained, gates advance and appears in canonical telemetry. Q-derived calculation explicitly removed by accepted ownership. |
| TestAdversarialCurriculumEntropyCalculation | test_entropy_high_for_uniform_policy | Supplied exact entropy1 retained and blocks advance with no telemetry. |
| TestAdversarialCurriculumEntropyCalculation | test_entropy_batch_processing | Equal-survival lanes with supplied entropies0/1 independently advance/stay at stages2/1. |
| TestAdversarialCurriculumBatchDecisions | test_get_batch_decisions_advances_stage | Completion commits stage3; three repeated decision reads retain exact shaped/reason/difficulty outputs without state mutation. Supersedes old decision-time learning. |
| TestAdversarialCurriculumBatchDecisions | test_get_batch_decisions_retreats_stage | Completion commits retreat stage2; decision reports exact stage/difficulty and remains pure. |
| TestAdversarialCurriculumBatchDecisions | test_get_batch_decisions_maps_stage_to_difficulty | Real heterogeneous stages1–5 retain all five difficulty/depletion/meter-roster/reward-mode outputs. |
| TestAdversarialCurriculumBatchDecisions | test_stage_5_is_sparse_rewards | Real stage5 retains sparse/SPARSE output and truthful unqualified meter/reward/uncalibrated difficulty status. |
| TestAdversarialCurriculumBatchDecisions | test_adversarial_curriculum_thresholds_from_config | Explicit resolved constructor policy matches full persisted meaning; genuine completions exercise authored dwell/entropy/advance/retreat. No configure bridge or uninspected config DTO. |
| TestAdversarialCurriculumBatchDecisions | test_adversarial_curriculum_difficulty_mapping_from_config | Real stages1–5 map into [.2,.6] at all five expected values; stage-band rate correctly inactive. |
| TestAdversarialCurriculumStatePersistence | test_checkpoint_state_includes_all_tracker_state | Exact completion schema; three real stages, dwell400/400/450, counts1/1/1, rewards12/3.5/0, baselines.8/.75/.85, nine receipts; snapshot mutation cannot affect live state. |
| TestAdversarialCurriculumStatePersistence | test_load_state_restores_all_state | Full current native state and all lane info restored; caller snapshot mutation cannot affect restored state. |
| TestCurriculumSignalPurity | test_curriculum_has_canonical_checkpoint_methods | Native validation plus full10/10 fraction1/progress1 despite reward1000; later repeated decision reads preserve snapshot and completed fraction. |
| TestCurriculumSignalPurity | test_curriculum_state_preserves_agent_stages | Fresh1 restores real saved3/dwell400 and exact stage metadata. |
| TestAdversarialCurriculumFullStateRoundtrip | test_checkpoint_state_includes_all_tracker_tensors | Exact current lane/metric fields and entire source-backed canonical event mapping including both actual typed readings; valid native schema. Seven-array representation removed by owner design. |
| TestAdversarialCurriculumFullStateRoundtrip | test_load_state_restores_every_tensor_exactly | Whole current snapshot recursively exact, including tensor dtype/shape/content; all caller event tensors can mutate after load without affecting restored state. |
| TestAdversarialCurriculumFullStateRoundtrip | test_resume_continues_episode_counter | Real next lane0 completion resumes saved count1→2/dwell400→800, other lanes untouched; duplicate retry cannot increment. |
| TestAdversarialCurriculumLoadStateStrictness | test_load_state_raises_on_missing_key | Each exact top-level required key missing refuses ValueError before mutation; expanded into three parameter values. |
| TestAdversarialCurriculumLoadStateStrictness | test_load_state_raises_on_num_agents_mismatch | Genuine three-lane current checkpoint refuses two-lane load atomically. |
| TestCurriculumCheckpointValidators | test_static_validator_requires_exact_typed_schema_without_mutation | Unknown top key, malformed meter config and boolean dwell refuse without mutation. |
| TestCurriculumCheckpointValidators | test_adversarial_validator_requires_exact_tensor_contract_without_mutation | Unknown top key, float stage and impossible previous fraction2 refuse without mutation. Exact current typed schema replaces removed tracker-tensor dtype contract. |

## Additional controls and validation limits

Six added method identities strengthen the accepted current coverage: rate.01/.1 gives difficulty.1/.25 after ten eligible transitions (two parameter values, true active units and duplicate purity); singleton.6 is preserved across real advance/retreat in both difficulty modes (two values); preparation has no effects, owns both actual tensor readings against caller mutation, installs once and refuses changed duplicate content atomically; a later invalid lane refuses the entire batch before effects; ten-transition dwell and full fraction survive repeated decision reads with cap reason; paired reward-component changes cannot change stage/progress/decisions. There are48 authored method definitions and an expected52 parameter-expanded cases by static inventory, not a collection result.

The historical class/method names do not claim that curriculum still accumulates live rewards, computes entropy from Q-values, accepts old tensor checkpoints or reconfigures on load. The actual episode producer and environment reset are outside this five-source consumer repair. Existing new runtime tests and their evidence remain frozen for root qualification.

Authorized scoped formatter/lint only: `.venv/bin/black tests/test_townlet/unit/curriculum/test_curriculums.py` reformatted one owned file. Final `.venv/bin/black --check tests/test_townlet/unit/curriculum/test_curriculums.py` reported one file unchanged, exit0; `.venv/bin/ruff check tests/test_townlet/unit/curriculum/test_curriculums.py` reported All checks passed, exit0. No test/import/collection/compile command was run. Root must pin actual collection and affected-test outcomes, then obtain fresh independent Astra review before the full gate.

## Fix round1/5 — causal coverage repair authored

Read the complete independent review and applicable `superpowers:subagent-driven-development` fix-loop resource (`skill://plugins~Plugin_60aea7460bd4819199fd97a9553a5e12/subagent-driven-development/references/fix-loop.md`). Root's execution split controls this round: original author modifies/formats/reports only; root captures and executes covering tests, supplies actual command/output, and dispatches the same Astra reviewer after that evidence is in this report. No runtime/import/probe/git/index or additional source read was performed here. Production and existing accepted-event regressions remain frozen.

Received root evidence for the INITIAL c9502d0 test candidate, tree8362228e: actual collection52 PASS; owning consumer plus accepted-event regression227 PASS,0 skips,0 warnings,10.35648 seconds; source797/config573/artifact13/three pytest process custody verified. Compiler CLI subsequently completed exit0 with custody PASS before root lifted the old-unit-only write freeze. These are root observations, not author execution and not qualification of this fix. The independent causal finding remained valid despite those results.

Only two existing test method bodies changed. All42 original identities and six added current-control identities remain. The following exact finding-to-assertion mapping supersedes the corresponding initial coverage rows; initial history is preserved above.

| Finding | Existing identity | Causal assertions added |
|---|---|---|
| P2 low-survival OR branch confounded by negative progress | TestAdversarialCurriculumStageRetreat.test_should_retreat_with_low_survival | Genuine improving completions reach literal stage4. Event4 at100/1000 and entropy1 establishes fraction.1 and retreats to3/reset counters. Event5 at200/1000 has fraction.2 and positive progress.1, entropy1, and actual eligible dwell200; must retreat3→2 with reason retreat and both counters0. Transition fraction/progress/dwell are also literal. Removing the low-survival branch while retaining negative-progress retreat leaves the event5 lane at3 and fails these assertions. |
| P3 configured advance threshold not behaviorally isolated | TestAdversarialCurriculumBatchDecisions.test_adversarial_curriculum_thresholds_from_config | A separate same-policy manager receives720/1000 with low entropy.3: fraction/progress.72 and sufficient dwell720 must retain stage1/no telemetry under configured advance.75. A hardcoded default.7 would advance and fail. Next800/1000 with positive progress crosses the configured threshold and advances to2. |
| P3 configured dwell not behaviorally isolated | Same existing configured-policy identity | A separate same-policy manager receives150/160, fraction/progress.9375 and low entropy.3: dwell150 is above default100 but below configured200 and must retain stage1/no telemetry. Next160/160 raises cumulative dwell to310 and positively improves fraction, advancing to2 with recorded dwell310. |
| P3 configured retreat threshold not behaviorally isolated | Same existing configured-policy identity | A separate same-policy manager reaches4 through real fractions.8/.85/.9 with eligible dwell. Then200/2000 establishes fraction.1 and retreats to3. Next540/2000 gives fraction.27/progress+.17 and eligible dwell540: above configured retreat.25 but below default.3, it must retain stage3/counters540 and1/no telemetry. A hardcoded default.3 fails. Another real.1 completion retreats to2 and resets dwell; next480/2000 gives fraction.24/progress+.14 and eligible dwell480, forcing2→1/reset counters with reason retreat. Ignoring the low-survival branch or a threshold too low fails. High entropy1 prevents advancing in these positive-progress witnesses. |

Original entropy-boundary/config transport assertions remain intact. There is no history injection, backend emulation, compatibility path or test removal. No method or parameter was added: static expected52 expanded cases remain, pending root recapture.

Final source inventory for round1 supersedes only the initial old-unit row: `tests/test_townlet/unit/curriculum/test_curriculums.py` **753 lines**, SHA256 **c414386e87ab43d11bfbae86cb5264102b9cb8985f2fcf618157cf0519e278da**. The other four sources were hash-checked and exactly match the initial inventory: adversarial537/2194cc4075096670181a50cf1be2158cd68334a07111818ad75382cd73890f4f; base66/d961844d5738ac85d26d5dd57520d1954718ee93e482e5133d4323d14c149268; static64/22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59; factory58/10be467c8ca72853bd8c6cceac60e6e13fcb4f202f1511fc7a9040539dbd9c71. Total five sources1478/3100 ceiling; every individual ceiling holds.

Authorized scoped commands run by author, both exit0:

- `.venv/bin/black tests/test_townlet/unit/curriculum/test_curriculums.py` — `1 file left unchanged`.
- `.venv/bin/ruff check tests/test_townlet/unit/curriculum/test_curriculums.py` — `All checks passed!`.

Covering test files for root execution: `tests/test_townlet/unit/curriculum/test_curriculums.py` and `tests/test_townlet/regressions/bac/test_curriculum_events.py` (the latter's source was not read or modified). Final candidate actual command/output and collection/affected outcomes are **pending root execution** and must be appended before scoped re-review. No final-fix runtime PASS is claimed.


## Root execution of fix1 candidate

Exact current test753/c414386e, candidate tree9644cd5f4da362357d6ae4f448325efa91335f34/base47d82. Root collection52 PASS. Root command: `/workspace/hamlet/.venv/bin/python -m pytest tests/test_townlet/unit/curriculum/test_curriculums.py tests/test_townlet/regressions/bac/test_curriculum_events.py -q --no-cov -p no:cacheprovider -p bac_source_identity -n 2 --dist worksteal --basetemp=/workspace/bac-review-2026-11-01/qualification/scratch/wave34-r9-curriculum`. Output:227 passed,0skips,0warnings;9.3245878s wall, child exit0. LogSHA256 0fc5ee55e2a96d30e142f418f2a16585f0344de515517ec8bf1964a5efd5f283. Custody PASS797guarded sources/573configs/13artifacts/3exactpytest identities/14registry MAIN1. This is root execution, not author/reviewer execution. Both finite causal controls now pass on actual current production source; independent scoped repair review remains required.
