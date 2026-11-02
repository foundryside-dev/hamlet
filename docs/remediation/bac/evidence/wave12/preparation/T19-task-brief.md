# T19 bounded readiness brief

Read this first: requirements are the extracted approved task and effective interfaces below. Historical frozen-plan gate prose is overlaid by the approved cadence exception; root owns actual gate selection. This is readiness only, not an implementation clearance.

## title

### T19: Owned completion envelopes and clock ledger — C07

## task_text

### T19: Owned completion envelopes and clock ledger — C07

**Interfaces:** Produce P5's `LaneOutcome`/`ClockLedger`; POP owns canonical per-lane reward accumulators/envelopes while retaining existing completion DTO/API. `completed_outcomes: tuple[LaneOutcome,...]` exposes frozen events; `begin_batch_episode(index:int, planned_horizon:int) -> None` establishes event identity before reset/rollout.

- [ ] Add `test_lengths2_5_owned_events_and_clock_units`: assert7 eligible transitions,5 vector ticks,2 lane events, frozen earlier outcome/reward after later ticks and reset; reverse lanes and repeat two resets; cap/budget/shutdown/checkpoint cuts retain explicit reason and nonterminal successor.
- [ ] Run `test_outcome_clocks.py` red for the new ledger/envelopes, keeping B11's already-passing completion controls unchanged.
- [ ] Implement event snapshots and clock increments at their owned advancing events; successful learner updates advance optimizer ledger once, skipped updates zero. Preserve current adaptive once-only completion calls.
- [ ] Run green plus B03/B11 lane gates and an independent train-frequency/target/LR schedule witness with unequal clock counts.
- [ ] Review and commit `feat(training): expose owned outcomes and clock units`.

## extracted_requirements

[
  "Add `test_lengths2_5_owned_events_and_clock_units`: assert7 eligible transitions,5 vector ticks,2 lane events, frozen earlier outcome/reward after later ticks and reset; reverse lanes and repeat two resets; cap/budget/shutdown/checkpoint cuts retain explicit reason and nonterminal successor.",
  "Run `test_outcome_clocks.py` red for the new ledger/envelopes, keeping B11's already-passing completion controls unchanged.",
  "Implement event snapshots and clock increments at their owned advancing events; successful learner updates advance optimizer ledger once, skipped updates zero. Preserve current adaptive once-only completion calls.",
  "Run green plus B03/B11 lane gates and an independent train-frequency/target/LR schedule witness with unequal clock counts.",
  "Review and commit `feat(training): expose owned outcomes and clock units`."
]

## test_nodes

[
  "tests/test_townlet/regressions/bac/test_outcome_clocks.py::test_lengths2_5_owned_events_and_clock_units"
]

## findings

[
  "D12",
  "D13"
]

## contracts

[
  "BAC-C07",
  "BAC-C08",
  "BAC-C09",
  "BAC-C13"
]

## known_items

[]

## relevant_interface_excerpts

[
  {
    "id": "P5core",
    "text": "RND `admit_and_service(observations: Tensor[K,D], *, vector_tick: int) -> PredictorServiceReceipt` accepts only eligible predecessor rows; receipt fields are `admitted_rows`, `consumed_rows`, `dropped_rows`, `pending_rows`, `optimizer_updates`, `last_loss`. Occupancy FIFO drains every complete minibatch in order and keeps only the incomplete tail. Paced FIFO consumes at most its authored update budget per tick and has finite `max_pending_rows`. Default lossless backpressure `service_before_admit` drains enough old complete minibatches before accepting the remainder; the receipt distinguishes mandatory overflow service from paced service. Explicit drop-oldest/newest are optional authored policies with counts, never silent replacements. Tail capacity must accommodate one minibatch; larger ingestion is processed in bounded chunks. Pending rows, order, counters, service configuration, normalization, target/predictor and optimizer are checkpointed and validated before mutation.\n\nT19 adds `training/clock_ledger.py::ClockLedger` with `vector_ticks`, `eligible_transitions`, `optimizer_updates`, `completed_batch_episodes`, `predictor_admitted_rows`, `predictor_consumed_minibatches`, `predictor_dropped_rows`; lane survival remains per-lane. Keep existing `total_steps` as its recorded vector-tick field rather than blanket renaming. Train frequency uses vector ticks; target/LR use successful optimizer updates; warmup/capacity use retained transitions; epsilon/checkpoint cadence use committed batch episodes; stage dwell uses lane eligible transitions; PER beta uses declared vector ticks.\n\nExtend `training/episode.py` additively with `LaneOutcome(outcome: EpisodeCompletion, batch_episode: int, planned_horizon: int, reward_total: float, reward_extrinsic: float, reward_intrinsic: float, reward_shaping: float, policy_entropy: float)`. Population owns canonical episode reward accumulators and publishes these envelopes once, retaining existing `episode_completions` and its existing DTO API. Event identity is `(batch_episode, outcome.agent_idx)`; all sinks consume the same outcome/envelope. Completion never repeats after later ticks/reset. New `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None` is idempotent by event identity, and does not add another death route."
  },
  {
    "id": "P6",
    "text": "### P6. Curriculum meanings and per-world application\n\nCompletion mode retains the last completed survival fraction `survival_time/planned_horizon`, ending reason, reward and entropy; learning progress compares that fraction to a baseline in the same units before updating it. Dwell adds the lane's actual eligible transitions once. Stage commitment occurs once per completion after evaluating the declared advance/retreat/entropy/dwell rules; per-step decisions execute the committed stage. Preserve `legacy_step` as a named, unit-documented alternative for existing APIs, without routing completion-length-as-reward into it.\n\n`stage_band` preserves direct stage-to-band mapping. Add `rate_limited`: adaptation_rate means maximum difficulty change per eligible lane transition; at completion move current difficulty toward that committed stage's band value by at most `adaptation_rate * eligible_steps`, clamped to [min,max]. Singleton [.6,.6] always returns .6. This control does not claim difficulty calibration or modify independent depletion values. Old stage-band configurations report adaptation rate as retained inactive content; the new mode proves its active effect. Factory/config routes both modes explicitly.\n\nEnvironment keeps scalar `depletion_multiplier: float` support and adds finite `Tensor[N]` support with rowwise broadcasts in every passive/transition depletion path. Population forwards all decisions in lane order. Existing active-meter/reward-mode labels remain preserved and accurately marked unqualified until their roadmap extension is implemented; do not relabel them as applied dynamics. K02's stage graph/mechanics is separate from repairing D12\u2013D15."
  },
  {
    "id": "B-section-2",
    "path": "/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/per-world-curiosity-addendum.md",
    "sha256": "3b82ecc340b936cd5672f248b85508f75136ab76cb994ac54723673989906871",
    "text": "## 2. Private state, RNG and service contract\n\n`world_curiosity_state.py` defines:\n\n- `ServiceClock(unit: Literal['vector_tick','world_eligible_admission'], position: int)`.\n- `CuriosityEventId(curiosity_epoch: int, world_id: str, world_episode_seq: int, eligible_seq: int)` and an immutable `CuriosityStepStamp` for all rows in one accepted transition context. The stamp has immutable IDs/world IDs of length N, episode and eligible-sequence integer tensors[N], and actual eligible bool[N]; raw/scales are finite tensors[N], with transition observations[N,D] and actions[N]. All shape/ID/order/content validation precedes mutation. Each phase accepts only its next event, replays its bounded last equal-content receipt without mutation, and refuses expired, changed-content or out-of-order IDs. Fresh construction uses epoch0; explicit conversion/evaluation cloning uses source epoch+1, clears active last-event caches and starts local eligible/service counts at0 while retaining the actual restored world episode identity. Inherited learned/history counters remain labeled template data, never active inherited dedup IDs. Ordinary reset advances only the episode identity/local episode cursor, not curiosity epoch or learned state; ordinary full resume restores all cursors/epoch unchanged. PW01/PW02 receipts publish these exact stamp/cursor initialization rules.\n- `WorldCursor` with last reward/service/completion IDs, local eligible admissions, consumed minibatches, successful updates and drops; bounded last-phase receipt caches/checksums prevent an immediate duplicate event advancing state twice. Expired older IDs and an ID with changed content diagnose before mutation; no unbounded event-history cache is required.\n- `WorldRNGState`: private torch CPU/CUDA states for used devices, private NumPy Generator/Python Random state, and versioned seeds. Model initialization and provider calls execute in the private RNG domain; global streams are restored on normal/error exit. Private operations use one serialized runtime owner, with a scoped RNG lock and no concurrent shared-policy operation inside the RNG domain. Serving uses the already required process boundary. This preserves actual learning, not frozen updates. Future parallelization must prove the same ownership contract.\n\n`provider_factory.py::make_backend(policy, *, world_id: str|None, obs_dim: int, action_dim: int, device) -> CuriosityBackend` constructs the existing five classes, no algorithm copies. It also constructs the existing epsilon policy selector. Shared scope keeps current mixed batching/cadence; private scope creates disjoint mutable instances under local seeds. Global action-policy epsilon still advances once per committed batch episode as v3 requires; its policy RNG/clock is separate from curiosity state. Legacy epsilon fields inside private backend objects cannot become a reward-coupling channel.\n\n`scoped_curiosity.py::CuriosityBank` provides `prepare_step_stamp(...)`, `reward(context, *, update_stats: bool) -> CuriosityReward`, `admit_and_service(context) -> tuple[WorldServiceReceipt,...]`, `begin_episode(world_id, episode_seq)`, `complete(outcome)`, `snapshot_world(world_id)` and prepared-state installation. `CuriosityReward` has `raw[N]`, `scales[N]`, active membership and immutable event IDs. Shared mode returns its declared shared result; per_world routes each actual row by ID and scatters back. Full-batch identity/shape/finite/clock validation happens before any backend mutation. No row-position or lane0 authority is substituted.\n\nAdd `admit_and_service_at(..., clock: ServiceClock)` adapters to RND/ICM and adaptive delegation; the old vector_tick method remains the shared-compatible adapter. Private service uses its own admitted-transition cursor. Backend FIFO, paced budget and overflow policy are applied per world; loss normalization and any clipping are per-world only. Complete minibatches actually call the backend optimizer, incomplete tails remain local, and extra idle/global ticks create no service opportunities. Aggregate metrics never feed back into these budgets. None has no predictor, count-based updates its own counts/LRU, and trainable providers must demonstrate nonzero parameter changes.\n\nReward phase remains eligible post-physics/successor observations for existing observation providers, actual(s,a,s') for ICM; RND predictor ingestion remains eligible predecessor rows. ENV prepares/stamps context before physics and carries that same stamp through its committed successor/reward and info to POP service, rather than regenerating IDs at logging time. `IntrinsicTransitionContext` gains world IDs, per-world episode/admission IDs and explicit global_vector_tick provenance; global tick is never the private service clock. `LaneOutcome` adds world_id/world_episode_seq without removing existing completion APIs.\n\nThe single DAC formula is unchanged: raw * runtime scale[N] * authored drive base * authored modifiers, then existing ending/retirement composition. Private scales remain vectors all the way to their own row. No population mean is used for canonical rewards. A preserved scalar summary may be clearly labeled mean-of-private-scales for telemetry only; per-world values remain present and no controller/composer consumes that summary."
  },
  {
    "id": "B-section-3",
    "path": "/workspace/hamlet/.superpowers/sdd/2026-11-01-bac-remediation-upgrades/per-world-curiosity-addendum.md",
    "sha256": "3b82ecc340b936cd5672f248b85508f75136ab76cb994ac54723673989906871",
    "text": "## 3. Lifecycle and shared Q/C09 boundary\n\n- Eligible-on-entry admission includes the terminal transition once. Completed/retired/inactive rows cannot update normalizers, queues, RNG or service clocks later. Same last event may return its cached receipt; changed or invalid duplicates refuse. Completion uses its own WorldId/episode identity and affects only that adaptive backend, not a batch mean or every lane's history.\n- Accepted reset closes/refuses unfinished nonempty episodes as v3 specifies. Reset clears episode-local cursor/cache state once, while learned curiosity, RMS/counts/LRU/history, pending tails and RNG persist across that world's episodes. No reseeding/reinitialization on ordinary reset or idle ticks. Stable IDs survive reset/resume; no state is reused merely because a row index is reused.\n- Core differential first runs with no Q updates but real curiosity updates. It then runs with real shared Q updates while each unchanged world's explicit actions and actual mechanics-input trace are controlled and recorded. Current active mechanics input is per-world depletion_multiplier in ENV.step; actions and any later genuinely applied controller intervention must be named at the real interface. Curiosity scale/reward/internal state are outputs, not controls one may pin to hide a leak.\n- Separate C09 proof supplies lane-distinct Q/entropy/completion inputs and verifies each lane's decision/application, no lane0 broadcast and the declared shared-Q feedback. A shared Q update may alter later policy/controller inputs; strict B is not a claim that those closed-loop decisions are independent. Do not use a conditional simulator trace as proof of controller independence."
  }
]

## effective_gate_selection

{
  "policy_reference": "BAC-CADENCE-A-2026-11-01",
  "addendum_sha256": "2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370",
  "next_mandatory_checkpoint": "G3",
  "earlier_full_trigger_assessment_required": true,
  "full_suite_required_before_release": null,
  "selection_instruction": "**T19 selection:** next mandatory checkpoint G3. Coordinator must assess the actual patch for approved earlier-full triggers before any deferral and record the decision; uncertainty triggers a full gate. No package or slice is declared repository green from focused-only evidence.",
  "required_receipt_fields": [
    "candidate_sha",
    "scope",
    "focused_commands",
    "owner_suite_commands",
    "static_commands",
    "review_record",
    "full_suite_status",
    "full_suite_reason",
    "unrun_checks",
    "next_full_gate",
    "source_inventory",
    "curiosity_scope",
    "curiosity_origin",
    "world_binding",
    "guarantee",
    "local_clock_units",
    "mode_limitations"
  ],
  "per_world_overlay_reference": "BAC-S1-PER-WORLD-B-2026-11-01",
  "X03_growth_activation": "X03-GROWTH-EXECUTION-R2-2026-11-01",
  "current_joint_release_wave": null
}

## reviewer_read_inventory

[
  {
    "alias": "POP",
    "access": "modify",
    "path": "src/townlet/population/vectorized.py",
    "projected_lines": 3000
  },
  {
    "alias": "EP",
    "access": "modify",
    "path": "src/townlet/training/episode.py",
    "projected_lines": 200
  },
  {
    "alias": "CL",
    "access": "create",
    "path": "src/townlet/training/clock_ledger.py",
    "projected_lines": 180
  },
  {
    "alias": "RC",
    "access": "read_only",
    "path": "src/townlet/training/replay_contract.py",
    "projected_lines": 250
  },
  {
    "alias": "test",
    "path": "tests/test_townlet/regressions/bac/test_outcome_clocks.py",
    "access": "create_test",
    "projected_lines": 350
  }
]

## Current status and restrictions

T16 is qualified and remotely durable at a0802a442bc7ea529de650b8705629923a0e6c72; 26/66 scoped packages qualified. T17 tests authoring is active; T19 depends on its completion. Only read stable declared five-source inventory; missing CL and test count as future owned files. No sixth implementation/helper/probe source. Prose reports/YAML data can be consumed with attribution. No source edits, runtime/imports/compiler/pytest/lint/collection, index/staging/commits/push, new branches/worktrees/project checkouts/source copies, deletion or subdelegation. Use existing /workspace/hamlet. Preserve all14 worktrees, all current capabilities/options/history. Additions permitted; removal/degradation/consolidation needs owner approval. No durable user-only rule was adopted; failed rule neither grants nor restricts. Existing project instructions and actual tool approvals govern. Root alone owns integration.

Write only T19-interface-readiness.md here: actual public signatures, ownership/snapshot timing, global/local clock units and exact existing/new files hashes/line counts; distinguish confirmed C07 gap, already working behavior, required producer/consumer DATA/API handoffs and specific implementation seam within the accepted plan. Do not reopen architecture or expand scope. Return concise readiness and missing prerequisites, then stationary.


## Effective tests-first clearance and adopted additive seam

T17 source995ce97b02a7ab57fad8da9c3c0ccd0b94a284f6 is scoped-qualified and checkpointbc47e44662f7bea953156a668610a20e6bced9f2 is pushed/exact-remote verified. Previousa080 all three CI workflows/jobs succeeded; bc47 lint/config succeed and tests run. Historical readiness prohibitions are superseded only by explicit root phase clearances.

Root adopts the final readiness additive binding seam: bind_episode_worlds(*, world_ids: Sequence[str], world_episode_seqs: Sequence[int]) before begin_batch_episode(index:int, planned_horizon:int), pin actual caller-owned identities to that begun episode, require fresh explicit binding next episode and concrete mandatory identity fields in qualified LaneOutcome. No row/batch/tick-derived guessed IDs/seqs or None identity. Existing unbegun completion/reset/step/flush APIs remain supported, without pretending they produce qualified new envelopes. Full runner/bank/checkpoint integration remains mandatory in its finite later owners. The new setup is additive and grants no scope reduction.

Use supplied real2/5 fixture API, both orders/two measured resets, explicit external-stop reasons/nonterminal successors and owned snapshots. Exact handoffs: T19-public-api-handoff.md, T19-entropy-api-handoff.md and T19-lane-fixture-api-handoff.md. Consume only prose/DATA, no sixth implementation links. Entropy uses supplied actual pre-physics Q signal and last eligible snapshot; no second mutating curriculum call or fabricated static zero. Preserve declared semantics and diagnose invalid inputs rather than conceal them.

Authoritative predictor accounting clarification: receipt.optimizer_updates counts actual successful complete predictor minibatches and is the direct ClockLedger predictor_consumed_minibatches delta; do not infer it from loss, Q-training batch size or guessed consumed-row division. consumed_rows may validate against the actual predictor minibatch size. Include all receipt admissions/drops including mandatory overflow work, preserving supported shared backlog service and legacy one-minibatch behavior. Provider/runner/private-clock scopes remain explicit.

Tests-first source clearance covers ONLY the new owned test; no POP/EP/CL production edits or runtime until root meaningful RED. Existing complete five-file projection remains POP3000/EP200/newCL180/read-onlyRC250/test350=3980. Report any genuinely necessary within-five-file reallocation before exceeding per-file projection; never add an uncounted helper/probe. Root sole index and runtime owner. No new branch/worktree/project copy/deletion/subdelegation.


## Formatting headroom ruling

After actual meaningful R0, root reallocates the same five paths to POP3000/EP200/CL180/read-onlyRC250/test500=4130, below5000. The new test is323 lines before Black; extra headroom preserves every assertion/scenario through formatting. No sixth source or capability/task/plan change is authorized.


## Current repair witness headroom and non-degrading lifecycle ruling

Fresh actual R2 Astra core review found two P2 defects and unrestricted delayed-commit/reset gap. Root requires preserving accepted reset and later commitment, retaining immutable publication fingerprints across reset; do not forbid/reset-degrade to close the gap. Add focused witnesses inside same owned test. Five-file projection is now POP3000/EP200/CL180/RC250/test650=4280, below5000. Full gate is required before T19 release because configured predictor service wiring changes existing work/clock semantics. User requires graceful halt after T19; no next packet.
