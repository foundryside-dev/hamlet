# T20 execution brief — resume from qualified T19

Read this first. This is your complete task and binding execution boundary.

### T20: Completion-driven curriculum and meaningful adaptation — D12/D13/D14/G05

**Interfaces:** CB defines `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None`; CA/CS implement it with P6's event deduplication, completed metrics, dwell and named commitment/difficulty modes. Retain public legacy step methods as their documented step interface, without using them for completion snapshots.

- [ ] Add `test_full_survival_survives_reset`, `test_dwell_counts_ten_transitions`, `test_singleton_band`, `test_rate_has_declared_effect`: survival10/horizon10 gives1.0 after reset; dwell adds10; .6 singleton always.6; rates.01/.1 over10 eligible steps move toward target by.1/at most1.0, clamped to band, while stage-band output preserves its old mapping.
- [ ] Run `test_curriculum_events.py` red; same event twice causes no metric/dwell/stage change, distinct-lane completions remain independent, cap ending is retained.
- [ ] Implement completed fraction baseline/progress in equal units, commit once after thresholds/dwell/entropy, rate-limited mode and truthful inactive adaptation in stage-band mode.
- [ ] Run green plus B06 curriculum/stage-info/signal-purity controls; no second death/completion call is added.
- [ ] Review and commit `fix(curriculum): use owned completion metrics and clocks`.

## Adopted contract

## BAC-C09 — Curriculum event ownership and per-world application [E/C/R]

**Expected behavior:** curriculum receives completed-lane outcomes through one completion interface. It retains completed survival statistics for later decisions instead of reading reset episode accumulators. Survival fraction uses the declared planned episode horizon, not fixed100; supplied ending reason identifies truncation. Stage dwell advances by the lane's eligible transitions, not the number of completion calls. Compare performance with a baseline in the same declared units. Bounds include singleton bands: `[0.6,0.6]` yields0.6.

Per-lane decisions must reach the corresponding independent world's dynamics. A shared scalar may be used only when all lanes intentionally share that decision; lane0 is not a broadcast authority for differing stages. A difficulty label is not evidence of calibrated task difficulty. Preserve accepted adaptation-rate controls and add a defined unit/consumer or explicit inactive role under C02; removing/refusing those controls is **APPROVAL REQUIRED**.

**Design scope:** completion-driven stage commitment is a proposed explicit mode [C/R]; per-step execution uses its committed decision. Other commitment schedules may be retained or added with named clocks. Shared-learner policies can remain shared, but world interventions and their identities are per world. Generic authored stage graphs, active-meter rosters and reward-mode switching are not yet qualified and may be implemented additively. Preserve their accepted knobs/outputs while making current inactivity truthful; removing, degrading or consolidating them is **APPROVAL REQUIRED**. Adding a stage topology does not itself repair the demonstrated survival/depletion bugs; both need evidence.

**Owners:** B06 curriculum; B03 forwarding; B11 dynamics; B09 completion routing; B10 reporting. **Prior authority:** PRD-0005 once-only truthful inputs; CurriculumManager per-agent contract; STATUS S1; known curriculum-authoring gap. Clarifies completion metrics and commitment; does not claim generic-stage capabilities are already delivered. **Acceptance:** full-survival completion followed by meaningful decisions, actual10-step dwell, singleton bounds, and heterogeneous valid stages `[1,5]` applied through the real population/environment to multipliers `[.2,1]`. B06's existing factory/environment replay is evidence, not yet that full-population witness.



## Approved plan interfaces

RND `admit_and_service(observations: Tensor[K,D], *, vector_tick: int) -> PredictorServiceReceipt` accepts only eligible predecessor rows; receipt fields are `admitted_rows`, `consumed_rows`, `dropped_rows`, `pending_rows`, `optimizer_updates`, `last_loss`. Occupancy FIFO drains every complete minibatch in order and keeps only the incomplete tail. Paced FIFO consumes at most its authored update budget per tick and has finite `max_pending_rows`. Default lossless backpressure `service_before_admit` drains enough old complete minibatches before accepting the remainder; the receipt distinguishes mandatory overflow service from paced service. Explicit drop-oldest/newest are optional authored policies with counts, never silent replacements. Tail capacity must accommodate one minibatch; larger ingestion is processed in bounded chunks. Pending rows, order, counters, service configuration, normalization, target/predictor and optimizer are checkpointed and validated before mutation.

T19 adds `training/clock_ledger.py::ClockLedger` with `vector_ticks`, `eligible_transitions`, `optimizer_updates`, `completed_batch_episodes`, `predictor_admitted_rows`, `predictor_consumed_minibatches`, `predictor_dropped_rows`; lane survival remains per-lane. Keep existing `total_steps` as its recorded vector-tick field rather than blanket renaming. Train frequency uses vector ticks; target/LR use successful optimizer updates; warmup/capacity use retained transitions; epsilon/checkpoint cadence use committed batch episodes; stage dwell uses lane eligible transitions; PER beta uses declared vector ticks.

Extend `training/episode.py` additively with `LaneOutcome(outcome: EpisodeCompletion, batch_episode: int, planned_horizon: int, reward_total: float, reward_extrinsic: float, reward_intrinsic: float, reward_shaping: float, policy_entropy: float)`. Population owns canonical episode reward accumulators and publishes these envelopes once, retaining existing `episode_completions` and its existing DTO API. Event identity is `(batch_episode, outcome.agent_idx)`; all sinks consume the same outcome/envelope. Completion never repeats after later ticks/reset. New `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None` is idempotent by event identity, and does not add another death route.

### P6. Curriculum meanings and per-world application

Completion mode retains the last completed survival fraction `survival_time/planned_horizon`, ending reason, reward and entropy; learning progress compares that fraction to a baseline in the same units before updating it. Dwell adds the lane's actual eligible transitions once. Stage commitment occurs once per completion after evaluating the declared advance/retreat/entropy/dwell rules; per-step decisions execute the committed stage. Preserve `legacy_step` as a named, unit-documented alternative for existing APIs, without routing completion-length-as-reward into it.

`stage_band` preserves direct stage-to-band mapping. Add `rate_limited`: adaptation_rate means maximum difficulty change per eligible lane transition; at completion move current difficulty toward that committed stage's band value by at most `adaptation_rate * eligible_steps`, clamped to [min,max]. Singleton [.6,.6] always returns .6. This control does not claim difficulty calibration or modify independent depletion values. Old stage-band configurations report adaptation rate as retained inactive content; the new mode proves its active effect. Factory/config routes both modes explicitly.

Environment keeps scalar `depletion_multiplier: float` support and adds finite `Tensor[N]` support with rowwise broadcasts in every passive/transition depletion path. Population forwards all decisions in lane order. Existing active-meter/reward-mode labels remain preserved and accurately marked unqualified until their roadmap extension is implemented; do not relabel them as applied dynamics. K02's stage graph/mechanics is separate from repairing D12–D15.

## Actual inventory

{
  "src/townlet/curriculum/base.py": {
    "sha256": "04bfb42f3b5d4faa3728be82d6c476448011fdb0c63788a24296839375b1ae26",
    "lines": 86,
    "projected_lines": 150
  },
  "src/townlet/curriculum/adversarial.py": {
    "sha256": "8ce48905b6163d25ff98f692af7986447245cc29eba47bcc248f10e4f4b8cf8b",
    "lines": 565,
    "projected_lines": 800
  },
  "src/townlet/curriculum/static.py": {
    "sha256": "4bce47073d50962defe1c405ca4a5fbda480e8321e2e38ff8e3558d7fafbf1be",
    "lines": 143,
    "projected_lines": 220
  },
  "src/townlet/training/episode.py": {
    "sha256": "5db951b4e76f88a2339ee5f77fe6515a726b5e2d1a006dbe283ea07d022f7fa9",
    "lines": 66,
    "projected_lines": 200
  },
  "tests/test_townlet/regressions/bac/test_curriculum_events.py": {
    "absent": true,
    "projected_lines": 350
  }
}

## Working rules and current stage

Work ONLY in /workspace/hamlet, existing branch project-recovery-bac-2026-11-01, base506674b538b01dbfb97a1e45df1bf22060bcab5c. No new branch/worktree, repository/source copy, removal/pruning or cleanup. No subagents. Root alone owns index, runtime/qualification and commits/push. Do not run tests, imports, formatters or broad commands until root clearance. Reading the five exact listed implementation/test files plus prose/YAML/reference reports is permitted; do not inspect an additional code/test/helper/fixture file. No hidden read inventory. Keep every whole file within the named projections or report a concrete budget issue BEFORE exceeding; hard cap5files/5000lines. Existing owner tests can be executed later without reading their source.

INITIAL ASSIGNMENT: author ONLY the named new regression test file and write tests-first report. Do NOT modify production before root observes meaningful RED. Use real EpisodeCompletion/LaneOutcome instances, reward components/entropy and explicit real declared IDs. T19 LaneOutcome also requires world_id and world_episode_seq; inspect EP for actual signatures. Preserve cap/ending reasons, per-lane event identity and duplicate handling. Existing step APIs and existing stage_band mapping stay supported. No capability removal/degradation/consolidation without user approval. Additive designs are authorized. Do not infer a user-only standing policy or authority from a failed durable rule; follow session/project instructions and actual approvals. Public remote pushing is already user-authorized; workers never push.

The reviewed immutable plan remains unchanged; T21 owns config/factory integration and T23 owns POP/runner routing. T20 must implement the completion consumer API, not silently claim later consumers are wired. Publish an explicit proposed mode-selection API in the tests-first report for T21; no hidden behavior defaults contrary to project guard. No per-step mutation of completed mode stage/dwell; retain legacy_step as a documented explicit alternative. Existing stage_band adaptation_rate is retained but reported inactive; new rate_limited has real per-transition units. P3 cleanup is separate.

Testing outline: full survival10/horizon10 retained after reset; equal-unit baseline/progress; dwell10 once; repeat identical event no mutation; independent lanes, reordered duplicates, cap reason; singleton.6; rates.01/.1 for10steps; stage_band old mapping; entropy/dwell/advance/retreat ordering, no repeated completion/death or per-step stage change. Add substantive edge tests within350line test budget. If budget requires expansion, report actual inventory and proposed finite projection; do not add files or weaken assertions.

Write report to /workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/wave13-preparation/T20-test-authoring.md. Include actual five-file lines/hashes, proposed API, test case names and intended meaningful RED conditions, risks/clarifications, and no fabricated test results. Reply concisely with status/report path.
