# T20 tests-first handoff

Status: authored the named regression file only; production remains unchanged. No test, import, runtime, formatter, index, commit, push, branch/worktree, copy, cleanup, deletion, or subagent operation was performed. Root must execute and inspect meaningful RED before clearing production implementation. There are no execution results to report.

## Exact read/write inventory

Read the task brief and the four allowed existing implementation files; authored the fifth allowed test file and this prose report. Skill instructions for test-driven development and its test-quality reference were consulted; no additional repository code/test/helper/fixture was inspected.

| Path | Actual lines | SHA256 | Authorized projection |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` | 86 | `04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26` | 150 |
| `src/townlet/curriculum/adversarial.py` | 565 | `8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b` | 800 |
| `src/townlet/curriculum/static.py` | 143 | `4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be` | 220 |
| `src/townlet/training/episode.py` | 66 | `5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9` | 200 |
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` | 243 | `bbb3ab360e67efd5ff4a6e1003d5226478ed2a10cba4f414a24e286b6040bdb9` | 350 |

Total actual source/test inventory: 5 files, 1103 lines; authorized projection 1720. No expansion requested at this stage.

## Proposed explicit API for T21

Preserve the existing constructor and `configure_from_training(config)` route. Add config attributes `commitment_mode` with values `legacy_step` / `completion`, and `difficulty_mode` with values `stage_band` / `rate_limited`. Tests explicitly select `completion` and `stage_band` unless testing another mode. Preserve existing unsupplied defaults (`legacy_step`, `stage_band`) so T21 must explicitly route completion mode; do not silently switch existing callers. Existing `adaptation_rate`, `min_difficulty`, and `max_difficulty` names remain accepted.

Add `CurriculumManager.commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None`, implemented by adversarial and static consumers. Event identity remains `(batch_episode, outcome.agent_idx)`. No completion is synthesized from step calls. Static accepts completions without changing its fixed decisions. Actual T19 `LaneOutcome` includes `world_id` and `world_episode_seq`; every fixture supplies concrete `town-world-N` and batch sequence values, real final tensors, reward components, entropy, horizon, and ending reason.

Completion mode records survival fraction using each envelope's horizon, prior fraction baseline, progress before baseline update, ending reason, reward components, and entropy. Proposed additive `get_stage_info` keys: `completion_reason`, `learning_progress`, `survival_baseline`, `reward_total`, `reward_extrinsic`, `reward_intrinsic`, `reward_shaping`, `policy_entropy`, `commitment_mode`, `difficulty_mode`, `adaptation_rate`, `adaptation_rate_active`, and `adaptation_rate_units`. Existing `survival_rate` means retained completed fraction in this mode. Baseline starts at zero, so first full completion has positive progress. Store updated baseline only after computing progress and making the stage commitment.

`rate_limited` starts at the lower configured bound and moves toward the newly committed stage target by at most rate times this completion's survival_time (eligible lane transitions), clamped to the configured band. Units string: `difficulty_per_eligible_transition`. `stage_band` preserves direct stage mapping and reports retained adaptation rate inactive. Singleton bounds always return the singleton. Difficulty movement does not alter existing stage depletion values, active-meter labels, or reward-mode labels. Those labels remain preserved; their broader qualification remains outside T20.

## Tests and intended RED

The helper explicitly asserts that the owned completion consumer exists before invoking it. Current production has no such method, giving an intentional assertion failure instead of an accidental AttributeError. Tests that first exercise existing outputs can also expose meaningful value mismatches: singleton currently falls back to stage mapping; stage-info lacks explicit mode/activity metadata. Root must distinguish actual assertion failures from environment/collection errors.

| Test | Bug or missing behavior caught |
| --- | --- |
| `test_full_survival_survives_reset` | Completed 10/10 fraction and cap reason survive clearing next-episode accumulators; constructor horizon 500 cannot become the denominator. |
| `test_dwell_counts_ten_transitions` | Ten lane transitions count as ten dwell units and one completion. |
| `test_duplicate_completion_does_not_mutate_metrics_dwell_or_stage` | Replay cannot add dwell, metrics, episodes, events, or another stage commitment. |
| `test_distinct_lanes_and_reordered_duplicates_are_independent` | Same-batch lanes remain independent; duplicate order cannot affect them; later batches are new identities and ending reasons remain per lane. |
| `test_learning_progress_compares_completed_fractions_before_baseline_update` | Fractions .4 then .6 give progress .2 despite unrelated reward magnitudes; retain component rewards and entropy. |
| `test_equal_fraction_is_not_positive_learning_despite_more_steps_and_reward` | Equal .8 fractions do not advance despite increased duration/reward. |
| `test_advance_requires_completion_entropy_and_eligible_dwell` | Entropy and dwell gates apply before committing, transition resets dwell, repeated decisions do not recommit. |
| `test_retreat_uses_negative_fraction_progress_and_ignores_entropy_gate` | A .5 decline retreats at high entropy even above the low-survival threshold. |
| `test_low_survival_retreats_even_with_positive_learning_progress` | Low survival independently triggers retreat despite positive progress. |
| `test_checkpoint_resume_preserves_completion_identity_and_completed_metrics` | Restore cannot lose event deduplication, retained fraction, or dwell. |
| `test_completion_mode_step_interface_does_not_commit_stage_or_dwell` | Existing step entry point cannot mutate completion-owned dwell/stage/info; repeated decisions remain pure. |
| `test_singleton_band` | Both difficulty modes return .6 for [.6,.6], before and after completion. |
| `test_rate_has_declared_effect` | Rates .01/.1 over ten eligible steps produce .1/.25 toward stage-2 .25 target, with explicit active units. |
| `test_rate_limited_moves_back_toward_retreat_target_and_clamps_to_band` | Movement works in both directions and respects [.2,.6]. |
| `test_stage_band_preserves_mapping_and_truthfully_reports_inactive_rate` | Stages 1–5 retain [.2,.3,.4,.5,.6] mapping regardless of rate; depletion/reward/meter outputs survive. |
| `test_legacy_step_remains_an_explicit_working_interface` | Explicit legacy step calls still update one step/dwell unit. |
| `test_static_curriculum_accepts_completion_without_changing_decisions` | Static implements the shared interface without introducing adaptation. |

## Risks and implementation boundary

- Proposed API names and first-completion baseline semantics above are explicit implementation choices for root/T21 review, not claims of existing interfaces.
- Reset witness clears only current accumulator tensors; it intentionally avoids calling any second death/completion route. It is a bounded curriculum test, not a population reset integration witness.
- `get_batch_decisions(None, ids)` uses real managers whose permitted source ignores state; no helper/state file was read or mocked. IDs are explicit and ordered.
- Completion-mode legacy `update_step` may retain episode-local accumulators, but cannot mutate completed stage/dwell/metrics. Explicit `legacy_step` retains existing behavior.
- Checkpoint deduplication adds state beyond the present exact seven-tensor schema. Implement additive compatibility carefully, with validation before mutation, and surface budget concerns before exceeding 800 adversarial lines. Tests do not authorize dropping old checkpoint fields or capabilities.
- T21 owns config/factory propagation; T23 owns runner/population routing. These tests do not claim either integration or the full-population heterogeneous-world witness is delivered. No new death/completion call is requested.
- Root alone owns RED/GREEN, B06/stage-info/signal-purity controls, further runtime qualification, index, commits, and push.
