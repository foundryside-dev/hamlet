# T16 bounded preparation; implementation not yet cleared

### T16: Propagate effective warmup/options through the real runner

**Interfaces:** RR passes resolved min_size/replay modes to POP. Existing constructor call sites can deterministically derive the same resolved training policy from their compiled environment, with provenance; no undocumented local warmup default.

- [ ] Add `test_real_runner_warmup1000`, `test_real_runner_recurrent_per`: after2 retained transitions with min_size1000, `assert optimizer_updates == 0`; at1000 plus scheduled/sampleable opportunity the first update occurs. Authored recurrent-PER compiles, constructs, rolls out and performs a real finite update.
- [ ] Run `test_runner_readiness.py` red; use frequency3/target2 with a smaller independent warmup to assert updates only on eligible vector ticks, LR/target on successful update counts.
- [ ] Wire the shared resolved policy, including beta's explicitly named vector-tick horizon; preserve zero-gamma myopic behavior.
- [ ] Run green across all four authored fixture families; a fixed-full no-window diagnostic is not a crash or fabricated update.
- [ ] Review and commit `fix(runner): apply declared replay warmup and modes`.

## Binding constraints

No new branch, worktree, project checkout/source copy or deletion. Use /workspace/hamlet. No subdelegation or index/commit/push. Root owns integration and clears all source writes/runtimes. Current T15 fullR2 source barrier remains active. Additions permitted; removal/degradation/consolidation requires explicit owner approval. Preserve approved historical A, strict per-world B and shared alternative, option leaves/provenance and existing owner rulings.

## Exact projected complete source inventory

[
  {
    "alias": "RR",
    "access": "modify",
    "path": "src/townlet/demo/runner.py",
    "projected_lines": 1500
  },
  {
    "alias": "POP",
    "access": "modify",
    "path": "src/townlet/population/vectorized.py",
    "projected_lines": 3000
  },
  {
    "alias": "test",
    "path": "tests/test_townlet/regressions/bac/test_runner_readiness.py",
    "access": "create_test",
    "projected_lines": 350
  }
]

Worker and fresh reviewer each at most5wholefiles/5000physicalsource lines, including tests/helpers/probes. No hidden sixth source. Omitted constructor/config/sampler APIs must come from existing source-verified prose or explicit supplier request.

## Effective interfaces

### P1. Authored, effective and transport identities

T02 adds `config/bac_options.py` with immutable validated `BaCOptions` and nested policies. T03 adds `config/effective_run.py`:

`resolve_effective_run(base: BrainConfig, training: TrainingV2Config, *, primary_level: str, origins: Mapping[str, str], drive_intrinsic: IntrinsicStrategyConfig) -> EffectiveRunConfig`.

`EffectiveRunConfig` contains `base_brain`, `effective_brain`, `training`, `options`, `exploration: ResolvedExplorationPolicy`, `primary_level`, `field_roles: Mapping[str, FieldRole]`, `authored_brain_hash`, `execution_hash`, `training_hash`, and `derivations: Mapping[str,str]`. `FieldRole` has `status: Literal['active','inactive_preset','derived','unqualified']`, `origin` and `reason`. Continue existing `brain_hash`/`pack_brain_hash` meanings and `compute_brain_hash` API; **add** `execution_hash`, do not silently redefine an existing hash. Effective brain still applies exactly gamma, target interval, Double DQN, learning rate and replay capacity after complete level replacement. Valid nonselected blocks remain validated authored content. Their edit changes authored identity and can retain identical execution identity/weights. Cache fingerprints remain separate transport/source/runtime freshness identities.

New options are portable typed authoring, carried through compiled serialization/checkpoints and telemetry. The old-document resolution table is fixed here: successive-without-replacement PER sampling, preserved legacy episode-length-with-replacement nonprioritized recurrent sampling, fixed-full windows, whole-episode retention, window-mean objective, max-absolute priority reduction, paced FIFO with one ordinary update per vector tick, max pending rows `max(2*N, predictor_batch_size)`, lossless service-before-admit overflow, completion commitment, stage-band difficulty, greedy-eval network mode, no initial save and final save enabled. Derived values are recorded, including the bounded-service upgrade; explicit options override only their named field. The preserved legacy-step, linear mean, stochastic serving and alternative modes remain explicitly selectable. Existing documents without the new options block retain a published, versioned semantic-resolution table; the resolver records each derived choice and origin. Constructors consume the resolved object, never invent local defaults. T02's explicit YAML fixtures exercise every new mode. Required existing fields remain required; omitted new additive options do not retroactively invalidate working packs.

`BaCOptions` exposes: `replay.sampling_mode` (`successive_without_replacement`, `independent_with_replacement`), `replay.uniform_sequence_adapter` (`legacy_episode_length_with_replacement`, `uniform_windows_with_replacement`); `replay.sequence_mode` (`fixed_full`, `adaptive_prefix`); `replay.retention_mode` (`whole_episode`, `transition_tail`); `replay.sequence_objective` (`window_mean`, `anchor_transition`); `replay.priority_reduction` (`max_abs`, `mean_abs`); `rnd.service_mode` (`occupancy_fifo`, `paced_fifo`), `rnd.max_updates_per_tick`, `rnd.max_pending_rows`, `rnd.overflow_policy` (`service_before_admit`, `drop_oldest`, `drop_newest`); `curriculum.commit_mode` (`completion`, `legacy_step`), `curriculum.difficulty_mode` (`stage_band`, `rate_limited`); `serving.policy_mode` (`greedy_eval`, `mc_dropout`); `checkpoint.save_initial`, `checkpoint.save_final`; the typed provider/source settings in P5a (all five drive choices), and the evaluation/viewer settings in P7. Old accepted stage/recording fields remain present with truthful roles; unqualified does not mean forbidden.

### P2. Historical transition, storage and readiness

T08 adds `training/replay_contract.py`: `ReplayRequest(batch_size: int, sequence_length: int, min_transitions: int, sampling_mode: str, sequence_mode: str, sequence_objective: str)`; `ReplayReadiness(ready: bool, retained_transitions: int, sampleable_units: int, reason: Literal['ready','warmup','batch_unavailable','window_unavailable','capacity_window_impossible'])`; and `ReplayBatch` with fields `legality_recorded`, `observations`, `actions`, `rewards`, `rewards_extrinsic`, `rewards_intrinsic`, `rewards_shaping`, `next_observations`, `dones`, `next_action_masks`, `loss_mask`, `lengths`, `unit_ids`, `weights`, `sampling: SamplingReceipt`. Flat shapes are `[B,D]`, `[B]`, `[B,A]`; recurrent shapes are `[B,L,D]`, `[B,L]`, `[B,L,A]`, with `lengths[B]`, `unit_ids[B]`, `weights[B]`. Reward-component fields retain the existing supported optionality. `legality_recorded` is bool[B] or bool[B,L] and is true for every active sampled row. Qualified production `next_action_masks` is always present. Existing explicitly unconstrained public-buffer inputs can supply a declared all-actions-legal invariant; imported constrained maskless rows are archived under approved A and never get all-true or zero-placeholder learner masks. `SamplingReceipt` is also defined in RC by T08, before any storage consumer: `indices: ndarray[int64,B]`, `weights: ndarray[float64,B]`, `population_size: int`, `conditional_draw_probabilities: ndarray[float64,B]`, `mode: str`, `objective_unit: str`, `weight_rule: str`. T13 implements the sampler that produces this schema; uniform buffers produce the corresponding uniform receipt. RC imports no later sampling implementation.

All three buffer classes gain `retained_transitions: int`, `readiness(request: ReplayRequest) -> ReplayReadiness`, `sample_batch(request: ReplayRequest) -> ReplayBatch`, preserving their public sample/push/store interfaces through explicit adapters, with pre-capture learning-history behavior changed only by approved A. Existing uniform replay remains without replacement. Sequence `__len__` need not be renamed/redefined; readiness uses the new retained-transition count. Public maskless buffer inputs continue to support the explicitly unconstrained/all-actions-legal buffer use case; production compiled-world admission always supplies actual masks. A constrained caller cannot assert that missing historical information was reconstructed; archived old history has no active sampler/optimizer interface.

Environment `step` returns cloned `info['successor_action_masks']: bool[N,A]` after committing that step's successor and completion status. Population stores the eligible row with the exact same successor observation. Buffers preserve mask width, values, wrap/eviction alignment, clones, serialization, strict key/version validation, prepare/materialize/install and no-mutation refusal. Recurrent masks are successor masks at **each real t**, including final real t, never a shifted current live mask. Terminals can have all-false masks; live nonterminal empty masks diagnose before selection/bootstrap. External cap/budget keeps `done=False` and a real successor/mask.

`adaptive_prefix` adds real fragment support: one window ending at each retained transition, with up to L preceding rows inside that same retained episode fragment. Pad transport only; `lengths` and `loss_mask` describe real rows. Group unrolls by real length, zero-start each local window, bootstrap its real last successor under that network's real final hidden, and never advance hidden through padding. `anchor_transition` applies loss only to the final real row, giving a uniform objective over retained eligible anchors. `window_mean` retains the all-real-row training choice: first compute each window's mean valid loss, then average/importance-weight **windows**; its declared objective is uniform over sampleable windows, not a falsely claimed uniform-transition objective. Preserve the historical length-weighted episode/start draw law as the explicit `legacy_episode_length_with_replacement` adapter. With fixed-full windows, let valid episodes e have length `n_e>=L`, `S=sum_valid n_e`, `M=sum_valid(n_e-L+1)`. Each draw independently selects e with `n_e/S`, then a uniform start among its `n_e-L+1` positions, so `p(e,start)=n_e/[S*(n_e-L+1)]`. To estimate the uniform-window objective its batch-mean weight is `1/(M*p(e,start))` (or the beta power in an explicitly annealed mode), never a successive-PER conditional weight. Selection rule: nonprioritized existing recurrent documents resolve to this preserved adapter; the added uniform-window adapter selects each valid window with1/M. Prioritized recurrent documents use the explicitly selected P3 PER draw law. For adaptive-prefix legacy draws, each retained episode fragment has `n_e` endpoints, so length-proportional episode then uniform endpoint yields1/sum n_e; no fixed-full denominator is reused. Declare each adapter in `SamplingReceipt` and test its actual ordered/independent proposal, not just a separately enumerated formula.

`whole_episode` preserves current retention. `transition_tail` is additive: evict oldest eligible rows, retain explicit fragment/episode identity, never splice episodes or invent evicted context. Capacity1/L8 can retain and learn from one **real** row in adaptive-prefix/anchor mode; readiness reports actual length1. Fixed-full mode remains selectable and reports `capacity_window_impossible` (or temporary `window_unavailable`) with counts and the additive mode that can serve it, without crashing, silently starving, rejecting the accepted pack, or claiming an eight-row sample exists. Diagnostics repeat on state change, not every tick.

#### Approved historical format and access policy — established before storage changes

**Selected Option A:** John explicitly approved `BAC-HISTORY-A-2026-11-01`, recorded in `docs/remediation/bac/HISTORICAL-REPLAY-DECISION.md`, question `call_e5fbd34979324b9f9574e38b6e61fbef`: “A — preserve artifacts, start fresh qualified replay (Recommended)”. This precise approval permits ordinary resume to stop sampling supported pre-capture maskless history while preserving every original artifact/replay tensor for inspection/query/export. It does not permit deletion, arbitrary scope reduction, or loss of current captured-mask full resume. Option B's retained wrong-target optimizer exception is **not selected**.

Coordinator pinned evidence establishes currently callable demo9/population6/uniform4/PER4/sequential5. These payloads lack successor masks and sufficient hidden-world state for exact reconstruction. Other versions already refused by the pinned strict loaders acquire no invented support promise. T03a creates `training/historical_checkpoint.py` (HC) and its approved dispatch/archive tests **before** T10–T12 change storage schemas. New captured formats are demo10/population7/uniform5/PER5/sequential6. All active current learner rows have actual masks and `legality_recorded=True`; archives live in a separate container with no sampler/optimizer interface.

`HistoricalAccessPolicy` records `source_formats`, `requested_mode`, `effective_mode`, `approval_reference`, `archived_row_count`, `active_retained_transitions`, `restored_clocks`, `guarantees` and `legacy_identity_recipe`. `resolve_historical_access(payload: Mapping[str,object], *, requested_mode: Literal['auto','recorded_full_resume','archived_history_fresh_episode','inference']) -> HistoricalAccessPolicy` dispatches as follows:

| Input / request | Selected behavior before runtime mutation | Guarantee/disposition |
|---|---|---|
| Current captured10/7 with replay5/5/6; auto or recorded_full_resume | Validate/prepare all owned state, restore active replay/priorities/masks/tails/clocks unchanged | Full current learned-fresh-episode resume; no archive-induced replay clearing or warmup reset |
| Exact pre-capture9/6 with uniform4/PER4/sequential5; auto or archived_history_fresh_episode | Validate exact old identity/schema; preserve its complete replay state in a separate archive, prepare a fresh empty captured-format active buffer, restore available learned/world/other state, reset episode-local state once | Approved Option A; record mode, source versions, `BAC-HISTORY-A-2026-11-01`, exact archived eligible-row count and active retained count0 |
| Same pre-capture input; explicit recorded_full_resume | `HistoricalLegalityUnavailable` before mutation, naming missing masks and the approved archive/fresh-buffer mode | No invented masks or pretended full-history continuation; ordinary auto access remains available under approved A |
| Supported old/new input; inference | Validate policy identity/geometry and preserve existing policy inspection/inference access | No training-history or stochastic-continuation claim; source artifact unchanged |
| Current captured artifact produced after an approved archival import | Restore all active captured replay exactly and retain its separate historical archives/approval metadata | Full current resume; historical archive rows never rejoin replay or count toward readiness |
| Malformed/unsupported state, current active rows with unknown legality, archive corruption, or incompatible identity | Located atomic refusal with every active runtime component unchanged | No deletion, state laundering, partial install or legacy optimizer path |

HC defines `HistoricalReplayArchive(source_formats, original_state, source_digest, archived_row_count, reward_semantics, approval_reference)` with `query_rows(*, offset: int, limit: int) -> Mapping[str,Tensor]` and `export(destination: Path) -> ArchiveExportReceipt`. `original_state` preserves original tensor values/dtypes, successor/actions/dones, priorities/episode boundaries and recorded reward/components bitwise; `reward_semantics='historical_recorded_pre_fix'` prevents reinterpreting them using repaired X01 scaling. The original source file and digest remain unchanged. The archive is an owned immutable copy when importing a state mapping; current checkpoints embed its complete archival payload/metadata, so standalone checkpoint relocation does not introduce a missing external-history dependency. Optional separate export is durable/atomic and never replaces the original file. `ArchiveExportReceipt` records destination, source digest, row count and output digest. Archive publication/preparation failure aborts before any runtime install.

Restore available online/target weights, optimizer/scheduler state, exploration state compatible with the selected repaired provider, curriculum, persistent world/layout state, episode identity and available cumulative clocks. Preserve source vector ticks and successful optimizer-update counts; they are historical cumulative clocks, **not** warmup occupancy. Set active retained-transition count0 and resume warmup against newly retained captured transitions only. Do not reset optimizer/LR/target counters as if this were cross-universe transfer. A min_size1000 import has zero further optimizer updates after two new rows; after1000 retained new rows plus a scheduled sampleable opportunity it may update, starting from the restored update counter. Archive row count never advances replay readiness, RND admission, stage dwell, completed episodes or any learning clock. Current-format full resume restores its actual retained count/warmup state unchanged.

No `legacy_unrecorded_bootstrap` or equivalent unknown-mask training branch is implemented. Old unrecorded rows cannot appear in any active `ReplayBatch`, including recurrent interior/boundary samples or PER indices. A read/query/export operation is not a training sampler. The learner and final acceptance tests enforce target3 instead of51 for every sampled nonterminal legality witness, with no historical P1 exception. The explicit approval is attached to D01/C05/C10 and historical reward provenance/X01/C08 ledger rows; it is a finite access-policy reduction, not a waiver of those defects.

HC retains exact format9 identity canonicalization over its old brain/training schema and five overrides, including presets; absent new option fields do not silently change that old identity recipe. Explicit incompatible new encoders/options refuse before mutation rather than pretending an old hash attests to them. Available old provider state is reused only in a matching repaired selector: epsilon restores commonly; adaptive→rnd reuses its recorded RND subtree; adaptive→adaptive reuses available adaptive/RND state; old state for a different newly selected count/ICM/none provider is preserved as inactive archival provider state while that selected provider starts with its defined compatible state. The old actual always-Adaptive selector is reported as source provenance, never used to override the repaired authored selector. Unrecorded RND tails/RNG are identified as unavailable, not fabricated; original absent state carries no new exact-continuation promise. All newly captured reward uses repaired current selector/scale semantics.

T10–T12 own each archive/import adapter; T25–T27 wire population/public runner/live dispatch. Their tests prove uniform/PER/recurrent original-state readability/export equality, archive row counts, empty qualified active replay, preserved learned clocks/state, no archived sampling, successful new captured learning, malformed/deep/archive-failure atomicity, and later current-format full resume without replay clearing. Public constructors/loaders/inspection APIs remain callable; their changed pre-capture learning behavior cites this exact approval. No further go-ahead is needed for the approved policy.

### P3. PER mathematics, including the existing sampler

T13 adds `training/per_sampling.py`, importing the already-defined RC receipt. `sample_units(priorities: ndarray[float64], *, alpha: float, beta: float, batch_size: int, mode: str, rng: numpy.random.Generator) -> SamplingReceipt`; receipt fields are `indices[int64,B]`, `weights[float64,B]`, `population_size:int`, `conditional_draw_probabilities[float64,B]`, `mode`, `objective_unit` and `weight_rule`. Stored loss weights are detached constants. Retain the existing successive weighted **without-replacement draw law**, including order. Its first-order inclusion probability is explicitly

`pi_i = sum over ordered distinct B-tuples containing i of product_k [u_(i_k)/(sum_j u_j - sum_(r<k) u_(i_r))]`, with `u_i = priority_i**alpha`.

Do **not** substitute the initial draw probability for this inclusion probability. Instead use the exact conditional residual-total estimator, which avoids approximating those marginals: for ordered position k=1..B, `q_k=u_(i_k)/sum_remaining u`; `(sum_(r<k) loss_(i_r) + loss_(i_k)/q_k)/N` is conditionally unbiased for the uniform-population loss. Average these B estimates. Equivalently the learner's batch mean uses `w_k(1)=((B-k)+1/q_k)/N`. At B=N use all-one weights and the exact full-population mean. At beta in [0,1], use `w_k(beta)=w_k(1)**beta`; only beta1 claims unbiased uniform correction. This is a conditional estimator, **not** standard marginal-inclusion IS. T13's exhaustive ordered enumeration proves each row's expected coefficient is 1/N.

The added independent-with-replacement mode draws `P_i=u_i/sum u`, uses `(N*P_i)**(-beta)`, allows repeated units, and reduces repeated priority updates deterministically by maximum absolute TD error for each sampled stable unit ID. No sample/batch-maximum normalization. Use no normalization initially (factor1); any later deterministic whole-population factor is explicit in the receipt. Alpha0 returns the correct uniform estimator for each draw law; beta pacing remains vector ticks against a recorded authored/derived vector-tick horizon.

Numerics: validate finite positive priorities before state mutation, compute normalized scores by float64 scaling/log arithmetic, and validate finite positive conditional probabilities/weights. `[3e38,3e38]` produces `[.5,.5]`. Overflow/nonfinite updates fail atomically with located/unit diagnostics. B04-C01 remains an API-level candidate until T13's bounded authored-learner reachability qualification; robustness can be repaired without promoting its historical evidence.

T14 uses the same unit sampler for recurrent PER. Stable unit IDs identify an episode-fragment/window endpoint and window mode; eviction removes its priority/index entry. In anchor mode priority is the anchor absolute TD error +1e-6. In window-mean mode choose explicitly `max_abs` or `mean_abs` over real loss rows, then +1e-6. The zero-start context is part of each window unit: the same underlying transition in two different windows may have different recurrent loss. No coverage-count shortcut claims those losses are identical. Anchor mode selects one deterministic admissible zero-start context per retained endpoint; window-mean mode averages its explicit context-dependent window losses. Importance weights apply once to per-window objective, never again per timestep or divided by a random global padded-row count. New windows inherit the recorded maximum positive priority. Save/restore priorities, stable-ID mapping, modes, beta and receipt configuration together; no promise of exact stochastic continuation follows.

## Current T15 handoff

VectorizedPopulation.for_training is explicit resolved learner seam; ordinary construction/inspection/serving preserved, lazy compiled policy adapter activates on actual learning entry and adopts loaded/empty-owned state rather than resetting it. All six replay leaves are explicit, including uniform sampling_mode. Beta horizon/current tick explicit in vector ticks. Current T15 source at f71c52fa is frozen during fullR2; no package-qualified claim until native captures. See wave09-preparation/T15-interface-proposal-r1.md, T15-interface-astra-review-r1.md, T15-actual-independent-review-r1.md, T15-actual-independent-runtime-r2.md, T15-documentation-draft.md for source-verified prose. Read your actual RR/POP sources independently within the bounded inventory.

## Current clearance

READ ONLY readiness audit may inspect3declared sources/prose and write an ignored report. No projectruntime/import/test/linter/collection or source edit until root explicit clearance after T15 qualification. Identify concrete API choices, compile/config fixture supplies needed, source budgets and any capability decision; do not start a new architecture/planning loop.

## Gate policy

{
  "policy_reference": "BAC-CADENCE-A-2026-11-01",
  "addendum_sha256": "2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370",
  "next_mandatory_checkpoint": "G2",
  "earlier_full_trigger_assessment_required": true,
  "full_suite_required_before_release": null,
  "selection_instruction": "**T16 selection:** next mandatory checkpoint G2. Coordinator must assess the actual patch for approved earlier-full triggers before any deferral and record the decision; uncertainty triggers a full gate. No package or slice is declared repository green from focused-only evidence.",
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


## Effective routine bounded context adjustment

Root adopts T16-bounded-context-adjustment.json: RR1200/POP2200/read-only BC600/read-only optimizer_factory200/test700, exactly5sources/projected4900. This supersedes the earlier3source4850 projection; actual four existing files3877 leaves ample test margin. Read-only BC/OF may verify scheduler/PER fixture schema and actual scheduler construction. No sixth helper. Source/test authoring still NOT CLEARED before T15 qualification. No task/lens/scope reduction or frozenplan edit.
