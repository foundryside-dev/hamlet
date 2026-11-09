# T20 independent actual-source review R1

## Findings first

### P2 — Completion restore accepts contradictory completed baselines and impossible progress

Contract: completed survival and baseline use the same fraction units; restore must preserve those meanings and reject invalid state before mutation. The new envelope duplicates the last fraction in `metrics[lane].survival_baseline`, `last_survival_rate`, and `prev_avg_reward`, but validates these independently. `adversarial.py:683-686` checks tensor finiteness then passes only the envelope to `_validate_completed_state`. Lines 743-750 accept any finite progress and any baseline in [0,1], with no comparison to the tensors. Load installs all these values at 639-649. Future commitment reads the envelope baseline at 303, while reported survival reads the tensor at 778.

Precise static witness, using only the existing regression helpers: create `curriculum(dwell=10)`, commit `outcome()` (stage 2, baseline 1), take its checkpoint, change only `state['completion']['metrics'][0]['survival_baseline']` to 0.0, and load into an identically configured manager. Every validation predicate passes. Commit `outcome(batch=2)`. Line 303 computes +1 rather than 0; lines 320-324 advance to stage 3 instead of remaining at stage 2. Immediately after load, stage info also reports survival_rate=1 and survival_baseline=0. No valid producer state has that disagreement. This is a malformed-checkpoint refusal gap, not a claim that untouched native snapshots spontaneously corrupt.

Related same-boundary witness: change `learning_progress` to 2.0 (or 1e300). Validation accepts a value impossible for the difference of two fractions in [0,1]; load reconstructs it into the progress tensor (the latter value exceeds float32 range). Require the mathematical range and compare redundant fractions using the checkpoint tensor dtype's representation, so normal fractions such as 0.8 are not rejected merely for float32 rounding. Validate before installing any live state.

### P3 — New refusal and resumed-future-behavior contracts lack owned regression coverage

The 252-line regression file exercises 22 parametrized happy-path cases, including a single untouched stage_band restore with duplicate replay. It does not assert any invalid-input/load refusal or unchanged state after refusal; it does not compare rate_limited future decisions before/after restore. The new validation code is substantial and the P2 witness above passes through precisely that uncovered path. Add the concrete cases below inside this owned file, without another probe file. This is a qualification gap, not a claim that the existing 22 tests fail.

## Verdicts

Spec compliance: changes requested for completion checkpoint consistency. The main T20 consumer, equal-unit progress, completion-owned dwell, once-only decisions, singleton bands and explicit rate semantics are statically consistent with the task brief. T21 config/factory and T23 population/runner integration remain mandatory deferred work; their absence here is not a T20 defect.

Code quality: request changes on the new restore boundary and add adversarial refusal/resume tests. No P1 found within the five-file inventory. Legacy constructor signatures and the seven-key legacy checkpoint schema remain intact. The new base method is concrete, so it does not add an abstract requirement to existing subclasses. Static completion consumption is an idempotent no-op, preserving its checkpoint schema.

## Inspected candidate and evidence

Base: `506674b538b01dbfb97a1e45df1bf22060bcab5c`. Immutable candidate tree: `d5717c96be86b505b35b42936bc944a589aae769`. Read task brief first, then budget ruling, implementation handoff, complete R1 diff package and relevant manifest metadata; reviewed actual source, not just handoff claims. Actual shell SHA256 outputs match the R1 manifest for every allowed file:

| File | Lines | SHA256 |
| --- | ---: | --- |
| src/townlet/curriculum/base.py | 92 | 2605ebcbb413e3db990081fa481a1517a647bfb276dc2898e3a17526c5411c92 |
| src/townlet/curriculum/adversarial.py | 803 | 086439b0d3e20e4e543bd24493f69c3eeaa99bc52005ddceef013a249a46eb59 |
| src/townlet/curriculum/static.py | 149 | 128faa2cc1732cd841817a9d1471c6014960012e34eb74d28a22d22ef51942a6 |
| src/townlet/training/episode.py | 66 | 5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9 |
| tests/test_townlet/regressions/bac/test_curriculum_events.py | 252 | 8e3578fb8be251e84269a48449c2b2cbcc091ffdc238f85429b44bd9ad545883 |

Five whole files / 1362 lines, approved projection 1870, hard cap 5 / 5000. No sixth helper, fixture, test or inline probe read/written. No source, tests, index or tracked documents changed. Only this ignored report written; ignored status checked. No runtime/import/pytest commands executed: runtime clearance was not supplied before this report. Root-observed R0 22 FAIL / 0 ERROR is received evidence only. Owner GREEN/static checks remain pending from this review's perspective; no passing execution inferred. Canonical commit_mode spelling adjustment is documented in the handoff and matches the inspected source/tests.

## Contract checks and refuted hypotheses

- Reset-loss hypothesis refuted for resetting episode accumulators: completed fraction, Python baseline and progress are separate retained fields; tracker update_step/update_baseline return early in completion mode. initialize_population intentionally starts a new population and clears identities, snapshots and transitions; it is not the same operation as episode accumulator reset.
- Double-step commitment hypothesis refuted: decision-path advance/retreat is explicitly gated to legacy_step at 447/456. Completion commits at most one retreat or advance per unseen event and adds actual survival_time to dwell before gating. Dwell/episode counters reset on transition.
- Float32 equal-fraction false retreat hypothesis refuted for normal commits: progress uses the Python completed baseline rather than round-tripped prev_avg_reward. This benefit is why checkpoint validation must compare representations carefully.
- Duplicate/lane collision hypothesis refuted for declared identity: key is (batch_episode, agent_idx), independent of lane ordering; repeated keys skip mutation. All events are prevalidated for lane/steps/reason before the mutation loop. Real LaneOutcome construction already validates batch/horizon/world identity and finite rewards/entropy. A generator is outside the declared Sequence API and is not used as a defect witness.
- Rate ignored hypothesis refuted in rate_limited: difficulty budget is rate times eligible transitions, target uses the newly committed stage, and movement is clamped to the configured band. Default stage_band preserves mapping and marks rate inactive. Both modes handle singleton bands.
- Legacy behavior is retained behind legacy_step: original step accumulation, advance/retreat priority and baseline updates remain. The new completion API explicitly rejects legacy mode to avoid a second clock. Constructor/from_yaml remain legacy defaults; transport of new modes is T21, not silently claimed complete here.
- Valid native checkpoint snapshot aliasing is improved: save/load clone tensors and deep-copy completed metrics. Cross-mode envelope/key mismatch and configuration mismatch are rejected before tensor assignment. Seen identities and rate state are included. The P2 finding concerns semantic contradictions that the new validation still accepts.
- Stage range/nonnegative dwell validation remains absent in the shared pre-existing tensor validator: stage 6 can be loaded and later index STAGE_CONFIGS out of range. This is inherited rather than introduced by this patch, so it is not promoted to a separate new-change finding; completion restore coverage should nevertheless exercise these invariants.
- No evidence establishes calibrated difficulty or applied active-meter/reward-mode mechanics. Status metadata truthfully says unqualified/uncalibrated; existing labels/depletion values remain preserved. Nullable legacy agent_id in completion transition events requires T23 sink qualification; no sink source was read and no downstream failure is asserted.

## Substantive tests for root to add in the existing owned file

1. P2 contradictory baseline/tensor checkpoint rejection, unchanged full state after refusal, and bounded learning_progress validation; include a valid fractional 0.8 native round-trip to protect against overstrict float equality.
2. Parameterized malformed completion sequence: valid first event followed by invalid lane, zero/excess steps or unknown reason; assert no metric, dwell, stage, rate, dedup or transition change anywhere.
3. Parameterized missing/unknown completion envelope keys, version/config mismatch, duplicate/out-of-range seen identities, missing per-lane metrics and invalid rate state; assert atomic refusal. Verify cross-mode restore refuses in both directions.
4. Rate-limited resume equivalence: save mid-ramp, restore, replay duplicate (no movement), then apply fresh advance/retreat/no-transition outcomes and compare difficulty, stages, progress/dwell and canonical transition identity with an uninterrupted control.
5. Checkpoint isolation: mutate saved tensors and metric dictionaries without affecting live state; mutate the loaded input after load without affecting restored state.
6. Completion-mode legacy baseline hook inactivity and explicit no-consumer legacy refusal; constructor-only legacy seven-key round-trip. Existing unrelated owner suites may supply some compatibility coverage but were not read.
7. Assert completion transition agent_idx/world_id/world_episode_seq/batch_episode and boundary stages 1/5. These IDs are implemented but absent from current assertions.

## Early-full trigger and limits

Early-full trigger: YES. The base completion interface and new checkpoint producer/consumer envelope change shared semantics, even though legacy schema remains intact. Before acceptance, root should run owned curriculum events plus its existing curriculum, stage-info, signal-purity, config/compatibility and checkpoint/resume qualification under its runtime guard. Root controls the selection and clearance. Fresh full routing/world-dynamics evidence remains required in T21/T23, including heterogeneous per-world stages; it must not be inferred from these direct consumer tests.

This is a static adversarial review with precise source proofs. It makes no claim about unseen factory, population, runner, sink, serializer or helper implementations and no claim about runtime results. No additional branch/worktree/copy, cleanup, capability reduction, subagents or index operations were performed.

## Root evidence update received before handoff

Root subsequently supplied actual R1 GREEN: 22 PASS in 17.5925 seconds at the exact `d5717c96be86b505b35b42936bc944a589aae769` tree, with source/import/thread/index/config/artifact/registry checks passing. Root's existing nine-module owner suite (152 cases, two workers) and static guards (two workers) are running, not yet reported complete. This supersedes the earlier pending status for the owned 22 tests only. These passes do not exercise the new negative witnesses above. Root requested finishing the static report without rerunning those known-passing tests and will add negative controls to the same fifth file; no independent runtime was executed here.
