# T20 implementation handoff

Status: scoped implementation authored after root supplied actual R0 evidence: fixed tree `e9b0a91ecc800f65169ef082731a8df90ffc9ad3`, 22 collected, 22 FAIL, 0 ERROR, 17.6653 seconds. Root reported 17 missing-consumer failures, two singleton output mismatches, and three missing mode/rate metadata failures, all call-phase. This worker did not execute RED or any runtime qualification. GREEN and independent Astra medium review remain root-owned and pending.

## API and compatibility

Canonical authored spelling is `commit_mode`, supplied by root from existing CurriculumOptions/preset evidence. Implementation and the regression fixture/assertions now use that spelling. This supersedes the proposed spelling `commitment_mode` in the earlier tests-first report. That test change is root-authorized spelling only; all 22 cases/assertions/values remain.

Existing constructor signatures remain unchanged. `configure_from_training` accepts explicit `commit_mode='legacy_step'|'completion'` and `difficulty_mode='stage_band'|'rate_limited'`. Defaults retain legacy_step/stage_band. Modes must be chosen before population initialization; existing legacy same-mode configuration remains available. Completion configuration is frozen after population initialization to preserve checkpoint meaning. The new rate_limited mode requires a finite nonnegative rate and the completion clock. Existing adaptation-rate content remains accepted in stage_band and is reported inactive.

CB adds a concrete completion entry point that raises NotImplementedError by default, preserving construction of existing subclasses. CA implements the owned completion consumer; CS explicitly accepts completions as a no-op without changing decisions or checkpoint schema. T21 transports config/factory modes; T23 routes real population/runner outcomes. Neither later integration is claimed here.

## Runtime meanings

- Completion identity is `(batch_episode, outcome.agent_idx)`; duplicates cannot change metrics, dwell, rate state, or stage. A whole input sequence is validated for real LaneOutcome instances, valid lane indices, positive eligible transitions within horizon, and declared completion reasons before event mutation starts.
- Survival uses each supplied planned_horizon. Retained completed metrics survive reset of episode accumulators. The initial fraction baseline is zero; progress compares current and previous completed fractions before baseline update, independent of reward magnitude. The baseline calculation uses Python fraction snapshots to avoid float32 roundoff turning equal fractions into negative progress.
- Dwell adds survival_time once; retreat has priority, then advance, applying entropy/dwell gates before one commitment. Transition resets stage dwell/episode counters. Decisions read the committed stage and do not recommit.
- Tracker step and baseline hooks are inactive in completion mode; their legacy behavior remains available through the explicit legacy mode. Public tracker survival/progress getters return retained completed metrics in completion mode.
- Rate-limited difficulty starts at the configured lower bound, moves toward the committed stage target by at most adaptation_rate times eligible lane transitions, and clamps to the configured band. Stage-band mapping is preserved, including singleton correction. Existing depletion values, meter rosters and reward labels remain intact; the implementation does not claim new mechanics or calibration.
- Stage info adds mode/activity/unit metadata and completed reward components, entropy, ending reason, progress, baseline and explicit world identity. Meter/reward labels are explicitly marked unqualified, and difficulty is reported uncalibrated. Completion transition events carry agent_idx/world_id/world_episode_seq/batch_episode; their legacy agent_id slot is None because LaneOutcome supplies no canonical string agent ID. Legacy decision-driven transitions retain their existing supplied string agent IDs. Existing downstream event sinks were not inspected under this five-file budget; T23 must verify their handling of the canonical identity fields and nullable legacy slot when routing completion mode.

## Checkpoint meanings and earlier-full trigger

Legacy mode retains its established exact seven native tensor keys and legacy metric units; no completion history is synthesized. Snapshot/load tensor cloning prevents alias mutation without changing the schema. Static retains its established four-key configuration schema.

Completion mode retains those seven tensor fields and adds a required version-1 `completion` envelope. The envelope contains exact meaning-bearing configuration (including commit_mode/difficulty_mode, band/rate, thresholds, entropy gate, and dwell), seen event identities, last per-lane completed metric snapshots, and per-lane rate state. In completion mode prev_avg_reward stores the completed fraction baseline, last_survival_rate stores the completed fraction, and completed progress is reconstructed from the retained snapshots. Legacy field meanings remain unchanged in legacy mode.

Validation occurs before any load mutation, checking tensor schema/shape/dtype/finiteness, envelope version/configuration, event identity uniqueness/range, per-lane metric presence, world identity/reason and finite numeric metrics, and rate state within the band. A missing envelope, unknown/mismatched config, or cross-mode checkpoint is rejected, never upgraded by inventing history. Existing transition event history is telemetry and is not added to checkpoint history; restored deduplication prevents re-emitting past transitions.

Earlier-full assessment: YES, completion-mode checkpoint producer/consumer meaning changes and the shared CB/CA interface justify root's broader owner qualification before acceptance. Root-provided existing curriculum, stage-info, config DTO, signal-purity, transfer and compatibility suites are relevant; broader checkpoint/resume qualification should also be considered under root's runtime inventory. No such execution is claimed by this worker.

## Boundaries and pending qualification

Only CB/CA/CS production files changed. EP remains unchanged. The owned regression file received the root-authorized canonical spelling adjustment and formatting during implementation; no scenarios or assertion values were removed/weakened. No additional implementation/test/helper source was read. No tests, imports, runtime commands, index/commit/push, subagents, branches/worktrees/copies, or cleanup were performed by this worker.

## Final stationary inventory

Root approved a finite CA projection increase from 800 to 950 before formatting, recorded in `T20-budget-ruling.json`; five-file projection is now 1870, hard cap remains 5 files/5000 lines, and the frozen plan is unchanged. Actual total is 1362 lines.

| Whole file | Lines | SHA256 | Projection |
| --- | ---: | --- | ---: |
| `src/townlet/curriculum/base.py` | 92 | `2605ebcbb413e3db990081fa481a1517a647bfb276dc2898e3a17526c5411c92` | 150 |
| `src/townlet/curriculum/adversarial.py` | 803 | `086439b0d3e20e4e543bd24493f69c3eeaa99bc52005ddceef013a249a46eb59` | 950 |
| `src/townlet/curriculum/static.py` | 149 | `128faa2cc1732cd841817a9d1471c6014960012e34eb74d28a22d22ef51942a6` | 220 |
| `src/townlet/training/episode.py` | 66 | `5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9` | 200 |
| `tests/test_townlet/regressions/bac/test_curriculum_events.py` | 252 | `8e3578fb8be251e84269a48449c2b2cbcc091ffdc238f85429b44bd9ad545883` | 350 |

Authorized formatter command targeted only the four owned changed paths: `.venv/bin/ruff format src/townlet/curriculum/base.py src/townlet/curriculum/adversarial.py src/townlet/curriculum/static.py tests/test_townlet/regressions/bac/test_curriculum_events.py`. Initial output: `2 files reformatted, 2 files left unchanged`; final invocation after documentation/status additions: `4 files left unchanged`, exit 0. This is formatter evidence only, not test/runtime evidence. Worker is stationary pending root GREEN and independent Astra medium review.
