# BaC Remediation and Upgrades Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the 21 reviewed defect groups and coordinator-validated exploration finding X01, deliver the nine adopted design upgrades, and qualify the four BaC families through authored training, restart, transfer, serving and durable output.

**Architecture:** Keep the compiled world/token boundary and shared learner. Add explicit effective-run, historical-transition, replay-sampling, completion/clock, load-mode and output-receipt contracts, then connect their producers and consumers in independently reviewed packages. Preserve the existing authoring and runtime choices alongside stronger, explicitly selected options.

**Tech Stack:** Python, Pydantic, PyTorch, NumPy, YAML declarations, pytest, SQLite, TensorBoard; use the repository's existing `uv` environment. No dependency installation is part of this planning task.

**Spec:** [BAC-2026-11-01-r2](../../remediation/bac/2026-11-01-design-baseline.md), [findings](../../remediation/bac/2026-11-01-findings.json), [review manifest](../../remediation/bac/2026-11-01-review-manifest.json). Detailed evidence is `/workspace/bac-review-2026-11-01/B01.md` through `B12.md`, `CONSOLIDATED.md` and `APPROVAL-ITEMS.md`.

## Global Constraints

- Reviewed base: `4aa5363b5de54d9a112977c32c2975f37627197f`; immutable evidence checkout: `/tmp/hamlet-bac-4aa5363b`. The latest user authorizes autonomous design, implementation and independent verification/repair after this plan receives technical approval. Continue in `/workspace/hamlet` under one coordinator-owned candidate; do not restart in an isolated implementation checkout. Fresh verifiers still use fixed-SHA detached checkouts. This planner has made no implementation changes.
- Binding user rule: “the design isn't fixed, as a rule you can always extend or add new features, complexity or options. If you want to remove, degrade or consolidate, please surface to me for approval”. This supersedes conflicting blanket deletion guidance in root `AGENTS.md`.
- Preserve four network families, complete level-brain replacement, the five training overrides, accepted presets, working zero-width constant policies, mean and attention, sampling and pacing choices, public loaders, partial transfer and stochastic serving capability. Fixing negative dimensions, invalid Nesterov and nonfinite corruption is validation of invalid inputs, not permission to narrow working inputs.
- Do not erase authored keys before validation; every admitted field has an active, inactive/preset, derived or explicitly unqualified role with provenance. A successful parse alone is not operational support.
- Keep compact observations, target-owned nonpersistent static context, eligible-on-entry admission, terminal successors, canonical precomposed reward and once-only frozen lane outcomes.
- Every future implementation worker **and its fresh reviewer** may inspect at most five implementation/test files and 5000 source lines, counting existing files, new modules, fixtures and tests. Specs, reports, YAML and generated interface documents are reference material. Execute existing tests without opening additional test files. Never disguise a larger read inventory as a smaller modification list.
- Implementers alternate between two models; every package receives a fresh adversarial reviewer using the other model, following `docs/remediation/STATUS.md` §§4–5 and `docs/remediation/rereview-2026-10-31/BRIEF.md` methodology. The newer additive/approval instruction supersedes the older brief's deletion rulings. Repair and re-review blocking findings before a dependent package starts. Package technical review does not authorize capability reductions.
- Python formatting remains Black, 140-character lines, Ruff and type hints; preserve ≥70% coverage. No secret-bearing outputs, unrelated tracker claims, commits or production edits during planning.

## Review Focus

1. A terminal successor with an all-false mask must yield a finite reward-only target, including large/poisoned unused action outputs; no `0 * -inf`. T08/T15 own this test.
2. A short retained recurrent fragment and its real final successor must not acquire fictitious length, padded loss, crossed episode history or a hidden-state advance through padding. T12/T15 own this test.
3. A valid sidecar supplied in two supported placements must survive without silent precedence; differing duplicates must identify both origins. T04 owns this test.
4. An exception between recording-file publication and SQL indexing, or a concurrent enqueue during shutdown, must produce an explicit receipt/failure rather than success. T33/T34 own this test.
5. A serving reset/load/play interleaving, including recurrent display and MC dropout, must not alter the training stream or advance memory twice. T27/T31 own this test.

---

## Authority, evidence and approval status

This plan adopts C01–C13 and explicitly labels additional design decisions below as **P** proposals selected for implementation planning. It does not rewrite the design or findings files. D01–D21 remain 21 defect groups, G01–G09 remain nine design gaps/qualifications, and candidate `C01` below means **B04-C01**, not contract BAC-C01. Historical focused test counts overlap; `670 passed, 5 skipped` is the reviewed-base unit baseline, not evidence that future repairs pass.

Evidence qualifications remain binding: D11 observed positive illegal sampler mass, not a native illegal-action incident; D15 executed curriculum/environment forwarding plus source proof, not a full-population witness; D17 used malformed utility input, not normal-producer corruption. G01 strengthens a faithfully implemented old recipe. G04 strengthens the weaker fresh-episode continuation inventory. G08 is an identity-semantics gap, not proof that retained presets are defective. G09 is boundary qualification, not a proved stale-cache/security regression.

**Approved narrow reduction:** John selected Option A, “preserve artifacts, start fresh qualified replay”, approval `BAC-HISTORY-A-2026-11-01` in [HISTORICAL-REPLAY-DECISION.md](../../remediation/bac/HISTORICAL-REPLAY-DECISION.md), question `call_e5fbd34979324b9f9574e38b6e61fbef`. Only supported pre-capture maskless replay stops driving optimizer updates; its artifacts/tensors stay readable/queryable/exportable. Current captured-history full resume is preserved. Option B (known wrong-target training exception) is not selected. No other reduction is selected. Rejecting zero widths/presets, removing mean, forcing a single sampler or RND mode, closing recurrent-PER authoring, deleting loaders/criteria/evaluators, or discarding live learner state without a selected transfer policy would require concrete user approval. An implementation worker must stop that alternative and present affected capability, retained alternative and tradeoff; proceed with the additive path in this plan where possible. The separate Astra MEDIUM review approves technical executability only. **The authoritative technical verdict is external: `docs/remediation/bac/plan-reviews/round-NN.md` must identify this file's exact SHA256 and verdict. The planner never self-approves. Approval or later execution does not require editing these reviewed bytes.**

### Planner inspection receipt

Only these five pinned implementation files were opened/searched; charge full file sizes even where inspection was selective: `src/townlet/population/vectorized.py` 1847, `src/townlet/config/brain_config.py` 561, `src/townlet/training/prioritized_replay_buffer.py` 758, `src/townlet/agent/networks.py` 474, `src/townlet/demo/runner.py` 998: **five files / 4638 charged lines**. No other implementation/test contents were inspected. Other source citations and interface facts are attributed to B01–B12. No code/tests were executed by this planner for this plan. Coordinator-owned later exploration probes are attributed below, not counted as planner execution or extra source inspection.

## Selected additive decisions and interfaces

These signatures and fields are interface commitments, not instructions to transcribe function bodies. Shape abbreviations: `N` lanes, `B` sampled units, `L` requested sequence maximum, `D` compact observation width, `A` compiled action count. Stored observations/reward components are float32, actions/indices int64, masks bool; sampling probabilities and estimator arithmetic use float64. Every tensor crossing an ownership boundary is cloned or immutable by construction.

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

### P4. Representation without losing mean

Add `TokenEncoderOptions(mode: Literal['linear','interaction_mlp'], hidden_width: int|None)` in OP and `TokenSetConfig.token_encoder` / `RecurrentConfig.token_encoder` in BC, independent of mean/attention selection. Linear requires no hidden width; interaction MLP requires a positive explicit hidden width. Omitted new field resolves to recorded linear semantics. Preserve `linear` and its exact old state/behavior. `interaction_mlp` applies a per-type nonlinear row encoder **before** pooling, taking the assembled descriptor and live payload jointly (Linear→ReLU→Linear, explicit hidden width in YAML; use an `nn.Sequential` whose Linear modules are indices0 and2 so transfer omission keys are unambiguous). Existence proof: for two descriptors c in {0,1}, live v in {.25,.75}, the row feature `ReLU(v+c-1)` pooled across the pair is .375 versus .125 after reassignment. The semantic-row permutation, carrying context with rows, preserves the result. T17 implements this witness before claiming expressivity, plus absence/empty exact-zero gradients. Mean remains a full selectable family with either encoder; attention is preserved; historical linear-mean studies are not invalidated.

### P5. Predictor service and completion clocks

**Additional validated finding X01 (C02/C08):** the coordinator's real ordinary-runner four-pack probe at the reviewed pin varied drive none/rnd/adaptive_rnd and training initial weights0/1 with drive base1 and no modifiers. All four returned canonical intrinsic `1.3138583898544312`, while current-scale telemetry was0/0/0/1. Thus selected none and zero runtime scale are actually ignored in canonical reward, despite the existing bound RND route working. Evidence: `/workspace/bac-review-2026-11-01/qualification/exploration-current-contract.json`; its authored executable is `qualification/probe_exploration_current.py`. This post-review finding is **X01**, not silently folded into the original21 defects or nine gaps. T18a–T18f own repair and final fresh probes; none/zero scale must yield canonical0, and each nonzero factor applies exactly once.

#### P5a. One authored exploration resolver and actual reward owner — R1/C08

Pinned coordinator evidence in `PLAN-BOUNDARY-FACTS.md` establishes that drive `IntrinsicStrategyConfig.strategy` accepts exactly `rnd`, `icm`, `count_based`, `adaptive_rnd`, `none`, with `base_weight`, `apply_modifiers` and retained optional raw provider dictionaries. Runner currently always constructs Adaptive. Population **already binds** that provider into ENV; `environment/reward_calculator.py` calls it on eligible **post-physics/successor-phase** observations before canonical DAC composition. Population's later predecessor novelty is diagnostic/predictor input, not the reward route. Do not falsely repair a missing provider binding or compose rewards twice. Adaptive currently returns unweighted RND novelty; DAC's existing named modifiers only map authored bar/variable ranges to multipliers, and do not consume adaptive current weight. The plan explicitly adds that missing single runtime-scale consumer and proves it through actual rewards.

T18a adds `config/exploration_policy.py` (RP), defining immutable `ResolvedExplorationPolicy` with `strategy` (the five drive literals), `epsilon_start`, `epsilon_end`, `epsilon_decay`, `rnd_feature_dim`, `rnd_learning_rate`, `predictor_batch_size`, `initial_intrinsic_weight`, `min_intrinsic_weight`, `variance_threshold`, `min_survival_fraction`, `max_episode_length`, `survival_window`, `decay_rate`, `drive_base_weight`, `modifier_names`, `provider_parameters`, `reward_observation_phase='successor_postphysics'`, `predictor_observation_phase='eligible_predecessor'`, `field_roles` and service policies. `resolve_exploration_policy(drive_intrinsic: IntrinsicStrategyConfig, training: TrainingV2Config, options: BaCOptions) -> ResolvedExplorationPolicy` is the sole resolver; `EffectiveRunConfig.exploration` stores it and execution identity includes active choices.

Precedence/roles are selected now: drive selects provider kind and owns DAC base weight/modifier names; training owns epsilon start/end/decay and the initial runtime intrinsic scale. Training intrinsic annealing/survival parameters operate only for `adaptive_rnd` and are retained inactive presets for other providers. Training RND feature dimension/learning rate and replay batch size supply the existing RND/adaptive predictor parameters. Add typed `options.providers.count_based` and `options.providers.icm`; explicit typed provider values override the same recognized key in the selected raw drive dictionary, which overrides recorded derived values. Recognized RND/adaptive dictionary values are preserved presets unless the explicit new `provider_parameter_source='drive'` is selected; default `'training'` preserves the existing training-owned knobs. New typed overrides and source choice are recorded per field, with a located conflict diagnostic for contradictory values at the same precedence. Nonselected/unknown raw dictionary keys remain losslessly retained validated authoring/preset data with a located inactive-key role, never erased or silently claimed active. No new required field invalidates existing documents.

The selected additive scope **delivers all five already accepted drive choices**, rather than classifying ICM/count-based away. `none` uses the existing EpsilonGreedy exploration/action selection with zero raw novelty; `rnd` uses RND with fixed training initial scale; `adaptive_rnd` uses existing adaptive RND with its changing current scale; count/ICM are the finite provider upgrades in T18b/T18c. Zero initial scale is valid and gives zero contribution while provider computation/service may still occur. Epsilon is one training-owned scalar plus synchronized per-lane selection tensors; decay once per committed batch episode. Adaptive completion consumes the owned lane event once. No nonexistent enabled boolean is inferred.

T18d implements `build_exploration(policy: ResolvedExplorationPolicy, *, obs_dim: int, action_dim: int, device: torch.device) -> ExplorationRuntime` in RP. This facade preserves the existing exploration protocol and exposes `provider`, `policy`, `epsilon`, `current_intrinsic_scale`, `decay_epsilon`, `commit_lane_outcome(event: LaneOutcome)`, `service_predictor(context: IntrinsicTransitionContext)`, `checkpoint_state`, `validate_state`, `load_state`. RP also defines `ExplorationServiceReceipt(provider: str, admitted_rows: int, consumed_rows: int, dropped_rows: int, pending_rows: int, optimizer_updates: int, mandatory_service_updates: int, last_loss: float)`; RND receipts adapt to it, count/none report zero predictor minibatches. Explicit policy state records each field's unit/phase. It dispatches to existing explicitly parameterized EpsilonGreedy/RND/Adaptive constructors and new count/ICM constructors; no class-local behavioral default decides the selected run. `IntrinsicTransitionContext` in RP owns predecessor/action/successor tensors `[N,D]/[N]/[N,D]`, `active_on_entry[N]` and vector tick; reward uses eligible successor phase for the old observation-based providers, and the complete transition for ICM. The environment captures predecessor before mutation and supplies the real committed successor to the existing reward facade. Predictor/service admission remains eligible predecessor rows for RND and eligible whole transitions for ICM. Logging reuses the recorded raw reward novelty or a clearly labeled no-stat diagnostic; it cannot update normalization twice.

The canonical formula in DAC is `effective_intrinsic = raw_novelty * runtime_intrinsic_scale * drive.base_weight * product(authored_modifiers)` exactly once, followed by the existing completion mask and `total=extrinsic+effective_intrinsic+shaping` plus existing one-shot retirement handling. `runtime_intrinsic_scale` is an explicit argument with provenance, not a second copy of a named modifier. The current authored modifiers do not contain an adaptive-scale consumer. RewardCalculator still owns the provider invocation and calls DAC once. Canonical total/components returned by ENV go unchanged to replay/sinks; population does not recompose them.

Count-based design: `CountExploration(policy, *, quantization_width: float, max_entries: int, device)` maintains a shared-learner deterministic LRU table keyed by finite compact eligible successor rows with bins `floor(value/quantization_width)`, computed from exact finite numeric ratios into signed arbitrary-precision integers before a canonical tuple digest, so negative boundaries and finite values cannot overflow a fixed-width key. A no-stat query returns `1/sqrt(existing_count+1)`, with unseen key yielding1, and never mutates counts/LRU. Raw novelty on the nth admitted occurrence is `1/sqrt(n)`; `update_stats=False` queries without advancing counts/LRU. Duplicate rows process in stable lane order. Explicit width/max-entry settings change behavior; defaults for old previously unimplemented selection are width1/16 and max_entries=effective replay capacity, recorded as derived. Eviction is an explicit finite-memory policy and its count is reported. Save/restore exact counts/LRU/config/epsilon with atomic validation; predictor updates are zero.

ICM design: `ICMExploration(policy, *, obs_dim: int, action_dim: int, feature_dim: int, hidden_dim: int, learning_rate: float, inverse_weight: float, forward_weight: float, training_batch_size: int, max_pending_transitions: int, device)` encodes actual `(s,a,s')`; inverse logits predict action from concatenated encoded predecessor/successor, forward predicts successor feature from predecessor feature plus one-hot action. Raw novelty is `.5 * mean((forward - stop_gradient(successor_feature))**2)` per transition. Optimizer loss is `inverse_weight*cross_entropy + forward_weight*mean_squared_error`; forward target is detached, inverse has a real encoder gradient. Explicit typed settings control feature/hidden sizes, learning rate, loss weights and service. Recorded derived old-selection values are feature_dim=training RND feature_dim, hidden_dim=2*feature_dim, learning_rate=training RND learning_rate, inverse_weight=.8, forward_weight=.2, batch size=training replay batch size, max pending=max(2*N,batch size). FIFO complete-transition minibatches use the bounded service policies; all pending s/a/s' rows, encoder/inverse/forward/optimizer state and clocks restore atomically. This is a delivered curiosity option, not a claim of learned competence or an expansion into cognitive topology.

Continuation is tagged by resolved provider kind/schema and exact policy identity. Current qualified state restores all provider networks/optimizer/normalization/counts/LRU/pending context/scale/annealing/epsilon and completed-event identities before one fresh episode reset. Inference and transfer retain their distinct P7 state policies. HC restores matching available old epsilon/RND/adaptive state under the repaired selector and preserves incompatible provider state archivally under approved A; it does not re-execute a wrong historical always-Adaptive selector or reinterpret old recorded rewards. Missing old tails/RNG are reported as unavailable, while every new current reward/selection follows the repaired contract.

RND `admit_and_service(observations: Tensor[K,D], *, vector_tick: int) -> PredictorServiceReceipt` accepts only eligible predecessor rows; receipt fields are `admitted_rows`, `consumed_rows`, `dropped_rows`, `pending_rows`, `optimizer_updates`, `last_loss`. Occupancy FIFO drains every complete minibatch in order and keeps only the incomplete tail. Paced FIFO consumes at most its authored update budget per tick and has finite `max_pending_rows`. Default lossless backpressure `service_before_admit` drains enough old complete minibatches before accepting the remainder; the receipt distinguishes mandatory overflow service from paced service. Explicit drop-oldest/newest are optional authored policies with counts, never silent replacements. Tail capacity must accommodate one minibatch; larger ingestion is processed in bounded chunks. Pending rows, order, counters, service configuration, normalization, target/predictor and optimizer are checkpointed and validated before mutation.

T19 adds `training/clock_ledger.py::ClockLedger` with `vector_ticks`, `eligible_transitions`, `optimizer_updates`, `completed_batch_episodes`, `predictor_admitted_rows`, `predictor_consumed_minibatches`, `predictor_dropped_rows`; lane survival remains per-lane. Keep existing `total_steps` as its recorded vector-tick field rather than blanket renaming. Train frequency uses vector ticks; target/LR use successful optimizer updates; warmup/capacity use retained transitions; epsilon/checkpoint cadence use committed batch episodes; stage dwell uses lane eligible transitions; PER beta uses declared vector ticks.

Extend `training/episode.py` additively with `LaneOutcome(outcome: EpisodeCompletion, batch_episode: int, planned_horizon: int, reward_total: float, reward_extrinsic: float, reward_intrinsic: float, reward_shaping: float, policy_entropy: float)`. Population owns canonical episode reward accumulators and publishes these envelopes once, retaining existing `episode_completions` and its existing DTO API. Event identity is `(batch_episode, outcome.agent_idx)`; all sinks consume the same outcome/envelope. Completion never repeats after later ticks/reset. New `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None` is idempotent by event identity, and does not add another death route.

### P6. Curriculum meanings and per-world application

Completion mode retains the last completed survival fraction `survival_time/planned_horizon`, ending reason, reward and entropy; learning progress compares that fraction to a baseline in the same units before updating it. Dwell adds the lane's actual eligible transitions once. Stage commitment occurs once per completion after evaluating the declared advance/retreat/entropy/dwell rules; per-step decisions execute the committed stage. Preserve `legacy_step` as a named, unit-documented alternative for existing APIs, without routing completion-length-as-reward into it.

`stage_band` preserves direct stage-to-band mapping. Add `rate_limited`: adaptation_rate means maximum difficulty change per eligible lane transition; at completion move current difficulty toward that committed stage's band value by at most `adaptation_rate * eligible_steps`, clamped to [min,max]. Singleton [.6,.6] always returns .6. This control does not claim difficulty calibration or modify independent depletion values. Old stage-band configurations report adaptation rate as retained inactive content; the new mode proves its active effect. Factory/config routes both modes explicitly.

Environment keeps scalar `depletion_multiplier: float` support and adds finite `Tensor[N]` support with rowwise broadcasts in every passive/transition depletion path. Population forwards all decisions in lane order. Existing active-meter/reward-mode labels remain preserved and accurately marked unqualified until their roadmap extension is implemented; do not relabel them as applied dynamics. K02's stage graph/mechanics is separate from repairing D12–D15.

### P7. Checkpoints, transfer and serving

T24 adds `training/load_modes.py`: `LoadMode = Literal['learned_fresh_episode','archived_history_fresh_episode','inference','cross_universe_transfer']`; `CheckpointBoundary(last_completed_episode: int|None, next_episode: int, completed_batch_episodes: int, checkpoint_sequence: int, save_reason: str, mode: LoadMode)` and `CheckpointRef(path: Path, run_id: str, sequence: int, next_episode: int)`. `select_latest_checkpoint(directory: Path, *, run_id: str) -> CheckpointRef|None` validates numeric identity within the selected run; filename padding is cosmetic. Preserve public runner/live load entry points. Validate all identities and prepared owned states before install. Payload records mode/guarantees; exact RNG or mid-episode execution is not claimed.

Runner boundary order is: close participated lanes with explicit reasons → publish/commit owned outcomes and curriculum/adaptive episode effects → decay epsilon once and synchronize selection state → increment next-episode identity/completed-batch count → create boundary → optional periodic/final save. Initial/final policy is explicit. Periodic interval counts completed batch episodes; interval5000 saves at completed count5000, never every100. Periodic/final artifacts at the same boundary agree on next episode and learned state; `load_checkpoint` internally consumes `next_episode` without another unconditional +1. The historical public returned episode value is documented/adapted rather than silently changing its meaning. A zero-episode run or failure before an initialized/committed boundary cannot masquerade as a completed checkpoint.

T28 preserves the low-level by-type helper and adds `partial` and `strict_complete` policies. `TokenRosterReport` adds exact loaded/missing/cold-started parameter names and partial types; `is_clean` is false if any shared parameter remains target-initialized. Strict refusal happens before mutation. `training/transfer.py::transfer_artifact(target: VectorizedPopulation, source: TransferArtifact, *, parameter_policy: str, state_policy: Literal['fresh_target','retain_compatible']) -> TransferReport` validates source schema semantics and geometry first. `TransferArtifact` contains source state, type-schema hash/schema version, architecture/encoder identity, action/reward semantic identities and provenance. Fresh-target starts empty replay, optimizer/scheduler, clocks, rollout memory and RND/annealing, then copies target from transferred online weights. Existing weights-only/live-state-retaining utility behavior remains available with explicit ownership/compatibility report; it does not inherit the fresh-target guarantee. Target static buffers never load from source. Same-shape semantic mismatch refuses in the high-level boundary; head shape alone claims no action/reward competence.

T27 adds `demo/evaluation_view.py::EvaluationRunView(policy_identity: str, seed: int, world_identity: str, episode_cap: int, epsilon: float, policy_mode: str, curriculum_state_policy: str, reward_metric: str, overrides: Mapping[str,object])`. `resolve_evaluation_view(effective: EffectiveRunConfig, *, overrides: Mapping[str,object]) -> EvaluationRunView` derives visible defaults from selected compiled training, and records viewer overrides including historical cap500 when explicitly selected. Greedy serving calls eval; MC-dropout explicitly enables dropout under its isolated stream, with other modules in the intended evaluation state. Successful training updates explicitly set online train/target eval. One episode calls population reset once; display reuses recorded Q/hidden output. T31 provides process-owned inference sessions behind the supported shared-training server boundary; request/load/reset/play and MC dropout cannot consume the training RNG. Existing public live APIs remain callable through adapters, and standalone/historical behavior is honestly qualified rather than removed.

### P8. Durable recording acceptance

T33 adds `recording/receipts.py`: `RecordingTicket(sequence:int, episode:int, lane:int)`; `RecordingReceipt(ticket, status: Literal['persisted','not_selected','failed'], path: Path|None, index_id: int|None, error: str|None)`. Successful enqueue returns a ticket. A lock closes admission before an ordered sentinel; no item accepted after the fence. Writer consumes until sentinel, marks queue tasks completed only after ownership is resolved, and records the first failure for enqueue/drain/shutdown callers. Shutdown joins/drains the closed accepted set, returns receipts or raises the concrete writer/incomplete-episode failure, and is idempotent. A live frame set without its required end marker cannot receive a successful complete-episode receipt.

Selected output uses a temporary file, flush/fsync, atomic publication and committed SQL index under a unique run/episode/lane identity. A success receipt requires a readable matching file/index and reward/ending/frame count agreement. Index failure after file publication is an explicit failure with orphan/reconciliation identity; it is never hidden by thread exit. Runner closes the database only after drain resolves, and records failed/interrupted status truthfully. Periodic selection stays operational; other accepted selection dictionaries remain preserved with truthful active/inactive roles under K04.

## File map and worker/reviewer budgets

All paths below are repository-relative and exact. The task table is the complete allowed **read** inventory for both implementer and its fresh reviewer, not just edited files. `W` modifies, `N` creates, `R` reads only, `T` creates the named test. A created test may import/execute public APIs without opening their implementation. Interface sections above and accepted predecessor receipts provide other boundary facts. Every test path `tests/test_townlet/regressions/bac/test_<slug>.py` is a new independent file; no implicit shared `conftest.py` reading. T02 owns YAML fixtures; later tests build from those YAML packs without reading another Python fixture file. No package may casually open an extra source/test file.

Projected full-file ceilings include cumulative changes, and are deliberately larger than pinned sizes. Recount before dispatch and after implementation. If actual context would exceed a listed ceiling or 5/5000, stop and have the coordinator split that task/read contract before further inspection. Do not drop required coverage to fit. Metadata/path inspection is allowed; source contents remain bounded.

| Alias | Exact path | Projected lines |
|---|---|---:|
| BC | `src/townlet/config/brain_config.py` | 750 |
| TC | `src/townlet/config/training_v2_config.py` | 650 |
| OP | `src/townlet/config/bac_options.py` | 500 |
| EF | `src/townlet/config/effective_run.py` | 300 |
| RP / DRIVE | `src/townlet/config/exploration_policy.py` / `src/townlet/config/drive_as_code.py` | 450 /750 |
| COUNT / ICM / EPS | `src/townlet/exploration/count_based.py` / `icm.py` / `epsilon_greedy.py` in that directory | 300 /500 /150 |
| RWC / DAC | `src/townlet/environment/reward_calculator.py` / `dac_engine.py` in that directory | 150 /1100 |
| UC | `src/townlet/universe/compiler.py` | 1100 |
| CU | `src/townlet/universe/compiled.py` | 1750 |
| DS | `src/townlet/universe/declarations.py` | 750 |
| LR | `src/townlet/config/resolved_launch.py` | 250 |
| RR | `src/townlet/demo/runner.py` | 1500 |
| CLI | `scripts/run_demo.py` | 300 |
| EXL / CUL | `src/townlet/config/exploration.py` / `src/townlet/config/curriculum.py` | 80 / 80 |
| RC | `src/townlet/training/replay_contract.py` | 250 |
| ENV | `src/townlet/environment/vectorized_env.py` | 2000 |
| AM | `src/townlet/environment/action_mask_builder.py` | 250 |
| RB / PB / SB | `src/townlet/training/replay_buffer.py` / `prioritized_replay_buffer.py` / `sequential_replay_buffer.py` in that directory | 850 / 1000 / 1100 |
| PS | `src/townlet/training/per_sampling.py` | 300 |
| QT | `src/townlet/training/q_targets.py` | 180 |
| POP | `src/townlet/population/vectorized.py` | 3000 |
| NET / NF | `src/townlet/agent/networks.py` / `src/townlet/agent/network_factory.py` | 750 / 250 |
| RND / AI | `src/townlet/exploration/rnd.py` / `adaptive_intrinsic.py` in that directory | 500 / 300 |
| AS | `src/townlet/exploration/action_selection.py` | 160 |
| EP / CL | `src/townlet/training/episode.py` / `clock_ledger.py` in that directory | 180 / 180 |
| CB / CA / CS / CF | `src/townlet/curriculum/base.py` / `adversarial.py` / `static.py` / `factory.py` in that directory | 150 / 800 / 220 / 150 |
| CC / ST | `src/townlet/config/curriculum_config.py` / `src/townlet/training/state.py` | 150 / 350 |
| CK / LM | `src/townlet/training/checkpoint_utils.py` / `load_modes.py` in that directory | 1000 / 220 |
| HC | `src/townlet/training/historical_checkpoint.py` | 450 |
| EV / LIVE | `src/townlet/demo/evaluation_view.py` / `src/townlet/demo/live_inference.py` | 300 / 1500 |
| TR | `src/townlet/training/transfer.py` | 300 |
| SERVER / IW | `src/townlet/demo/unified_server.py` / `inference_worker.py` in that directory | 700 / 300 |
| HE / GE | `scripts/l2_baseline.py` / `scripts/evaluate_policy.py` | 320 / 300 |
| REC / RT | `src/townlet/recording/recorder.py` / `receipts.py` in that directory | 550 / 150 |
| DB / TB / REG | `src/townlet/demo/database.py` / `src/townlet/training/tensorboard_logger.py` / `src/townlet/population/runtime_registry.py` | 800 / 650 / 200 |

Each `test_<slug>.py` has a **350-line ceiling** except the final learning comparison's 300-line harness. Source aliases always mean the exact path above; `T(slug)` means the exact regression path above.

| Task | Complete worker AND reviewer read inventory | Files / projected lines | Dependencies |
|---|---|---:|---|
| T01 | W BC, W TC, T(numerics) | 3 / 1750 | none |
| T02 | W BC, W TC, N OP, T(options) | 4 / 2250 | T01 |
| T03 | N EF, W UC, W CU, R RP, T(effective_run) | 5 /3950 | T02,T18a |
| T03a | N HC, R CK, R BC, R RC, T(historical_dispatch) | 5 /2800 | T03,T08 |
| T04 | W DS, R UC, T(sidecars) | 3 / 2200 | T03 |
| T05 | N LR, R UC, R CU, T(discovery) | 4 / 3450 | T04 |
| T06 | W CLI, W RR, R LR, T(launch_transport) | 4 / 2400 | T05 |
| T07 | W EXL, W CUL, R LR, T(public_loaders) | 4 / 760 | T05 |
| T08 | N RC, N QT, T(transition_contract) | 3 / 780 | T02 |
| T08a | W AS, R QT, T(action_probabilities) | 3 / 690 | T08 |
| T09 | W ENV, R AM, R RC, T(successor_producer) | 4 / 2850 | T08 |
| T10 | W RB, R RC, R HC, T(uniform_history) | 4 /1900 | T03a,T08 |
| T11 | W PB, R RC, R HC, T(per_history) | 4 /2050 | T10 |
| T12 | W SB, R RC, R OP, R HC, T(sequence_history) | 5 /2650 | T11 |
| T13 | N PS, W PB, R OP, T(per_estimator) | 4 / 2150 | T12 |
| T14 | W SB, R PS, R RC, R OP, T(recurrent_per) | 5 / 2500 | T13 |
| T15 | W POP, R RC, R QT, R SB, T(learner_legality) | 5 / 4880 | T08a,T09,T10–T14 |
| T16 | W RR, W POP, T(runner_readiness) | 3 / 4850 | T06,T15 |
| T17 | W NET, W NF, R BC, R OP, T(token_binding) | 5 / 2600 | T02,T16 |
| T18 | W RND, R OP, T(rnd_service) | 3 /1350 | T02 |
| T18a | N RP, R DRIVE, R TC, R OP, T(exploration_policy) | 5 /2700 | T02 |
| T18b | N COUNT, R RP, R EPS, R OP, T(count_provider) | 5 /1750 | T18a |
| T18c | N ICM, R RP, R EPS, R OP, T(icm_provider) | 5 /1950 | T18a |
| T18d | W RP, R RND, R AI, R EPS, T(exploration_factory) | 5 /1750 | T18,T18b,T18c,T19 |
| T18e | W ENV, W RWC, W DAC, R RP, T(intrinsic_composition) | 5 /4050 | T09,T18d |
| T18f | W POP, W RR, T(exploration_routing) | 3 /4850 | T16,T18e,T19 |
| T19 | W POP, W EP, N CL, R RC, T(outcome_clocks) | 5 / 3960 | T17 |
| T20 | W CB, W CA, W CS, R EP, T(curriculum_events) | 5 / 1700 | T19 |
| T21 | W CF, W CC, R TC, R OP, T(curriculum_factory) | 5 / 1800 | T20 |
| T22 | W ENV, R ST, T(per_world_dynamics) | 3 / 2700 | T09,T18e,T21 |
| T23 | W POP, W RR, T(curriculum_routing) | 3 / 4850 | T16,T18f,T19–T22 |
| T24 | W CK, N LM, R EF, T(checkpoint_contract) | 4 / 1870 | T03,T23 |
| T25 | W POP, R RND, R CL, R RC, T(population_restore) | 5 / 4280 | T18,T19,T23,T24 |
| T26 | W RR, R CK, R LM, R EP, T(checkpoint_boundary) | 5 / 3250 | T24,T25 |
| T27 | W LIVE, N EV, R CK, R LM, T(serving_modes) | 5 / 3370 | T17,T26 |
| T28 | W CK, R NET, T(partial_transfer) | 3 / 2100 | T17,T27 |
| T29 | W CU, R EF, R BC, T(artifact_coherence) | 4 / 3150 | T03,T28 |
| T30 | N TR, W POP, R CK, T(artifact_transfer) | 4 / 4650 | T25,T28,T29 |
| T31 | W SERVER, N IW, W LIVE, R EV, T(serving_isolation) | 5 / 3150 | T27,T30 |
| T32 | N GE, R HE, R EV, T(evaluation_entry) | 4 / 1270 | T07,T31 |
| T33 | W REC, W DB, N RT, T(recording_drain) | 4 / 1850 | T04 |
| T34 | W RR, R REC, R RT, R DB, T(recording_cleanup) | 5 / 3350 | T26,T33 |
| T35 | W DB, W TB, W REG, R CL, T(sink_units) | 5 / 2180 | T19,T34 |
| T36 | W RR, R EF, R CL, T(effective_telemetry) | 4 / 2330 | T26,T35 |
| T37 | R POP, R RC, R PS, T(joint_learning) | 4 / 3900 | T15–T18,T18a–T18f,T25,T30,T36 |
| T38 | R RR, R LIVE, R TR, T(joint_restart_serving) | 4 / 3650 | T26–T32,T36 |
| T39 | R REC, R DB, R TB, T(joint_outputs) | 4 / 2350 | T34–T36 |
| T40 | R GE, T(learning_comparison:300) | 2 / 600 | T37–T39 and final repository gate |

Serial mutable-file ownership is the task order above: BC/TC T01→T02; CU T03→T29; RR T06→T16→T18f→T23→T26→T34→T36; ENV T09→T18e→T22; RP T18a→T18d; PB T11→T13; SB T12→T14; POP T15→T16→T19→T18f→T23→T25→T30; CK T24→T28; LIVE T27→T31; DB T33→T35. No parallel worker may edit any of these while its owner runs. Independent branches T07, T18, T18b/T18c, T33 can run after dependencies, with immutable interface receipts. T18a runs immediately after T02 and feeds T03; T19 precedes T18d/T18f so owned completion types exist before facade wiring. The table is the dependency DAG; ranges include every task in that range, and a dependency means its review and repairs have completed.

## Execution and verification convention

Track execution checkboxes and completion in the external acceptance ledger/task receipts, not by editing this byte-frozen approved plan. Any plan amendment requires a new content hash and re-review. For implementation tasks below, set `CHECKOUT=/workspace/hamlet`; for a verifier set `CHECKOUT` to its detached exact-SHA candidate, run from that directory with its existing environment and `PYTHONPATH="$CHECKOUT/src"`; assert the imported `townlet.__file__` resolves there. Do not import the mutable main checkout by accident. The exact focused command is `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_<slug>.py -q`. In each task:

1. Add the named regression/proof and run that exact command **red**. For existing defects, it must fail on the specified assertion in the reviewed base; for new interfaces/modes, it fails because that interface or guarantee is absent. A syntax/import mistake unrelated to the intended missing interface is not useful red evidence.
2. Implement only that task's deliverable; rerun the same command **green**, then the relevant existing named suites from the owning B report without opening more source. An expected diagnostic is asserted, not silently skipped.
3. Record SHA, imports, command, assertions, limits, inventory and results in the implementation receipt. Fresh other-model review uses the same bounded inventory and attacks the stated negative controls. Repair before dependency release.
4. Commit exactly the task-owned files with the specified Conventional Commit subject, after green verification and review. Do not combine several independently reviewable packages into an unreviewed commit.

The steps below are checkboxes for those concrete actions; completion requires the whole convention, not merely checking a box. New test directories/modules must be absent before creation or explicitly reconciled with their existing owner; never overwrite an unrelated file.

### T01: Finite and constructible authored numerics — D06/D07/D08/G06

**Interfaces:** Preserve `BrainConfig`, `TrainingV2Config`, `apply_training_overrides` and selected optimizer factories. Add per-width `>=0` validation for flat/dueling lists, selected SGD Nesterov→momentum>0, finite-only behavioral floats, and gamma `[0,1]` consistently. Preset numerics are validated without selecting their inactive behavior.

- [ ] Add `test_negative_width_is_located`, `test_nesterov_requires_positive_momentum`, `test_infinite_override_refused`, `test_zero_gamma_and_constant_policy_work`: `assert gamma == 0`, `assert isfinite(q).all()`, zero-width Q is observation-independent with its existing bias parameters; negative widths and `.inf/.nan` fail before allocation/update.
- [ ] Run `test_numerics.py` red; retain the full-pack compile controls and finite optimizer update witness, not only isolated DTO construction.
- [ ] Implement the stated BC/TC validators; preserve active optimizer/loss families and finite positive controls.
- [ ] Run green plus B01 focused factory/DTO suites; confirm complete level replacement/five override behavior remains.
- [ ] Review and commit `fix(config): validate constructible finite brain parameters`.

### T02: Portable option schema and preserved presets

**Interfaces:** Produce `BaCOptions` and P1's versioned semantic-resolution table. Add a recognized optional `bac_options` block to the existing training DTO and token-encoder options to the brain DTO without refusing accepted old documents. Each option's selected/derived value is serialized. Geometry fields stay compiler-owned.

- [ ] Add `test_all_modes_round_trip`, `test_old_options_remain_accepted`, `test_unqualified_options_are_retained`: assert mean/attention, linear/interaction encoders, both PER modes, fixed/adaptive windows, whole/tail retention, both RND modes and both serving modes remain selectable; unknown keys/invalid nonfinite values refuse.
- [ ] Run `test_options.py` red; create explicit YAML fixture packs under `configs/test/bac_remediation/{feedforward,dueling,token_set,recurrent}/` plus `options/` documents covering every added mode. YAML ownership belongs solely to this task, outside source limits; use the real declaration compiler, not invented abbreviated pack syntax.
- [ ] Implement typed options and publish `docs/remediation/bac/options.md` with units, old-document resolution and active/inactive roles, including K02/K04 surfaces. Preserve new options in cache serialization inputs.
- [ ] Run green; compile each explicit fixture, then transport-only rename it and assert resolved options equal.
- [ ] Review and commit `feat(config): declare additive BaC runtime options`.

### T03: One effective run view and distinct identities — G08

**Interfaces:** Produce P1's `EffectiveRunConfig`/`FieldRole`/resolver; compiled universe gains `effective_run` and the new identities while retaining its selected base `brain` and existing hashes.

- [ ] Add `test_preset_edit_changes_authored_not_execution`, `test_five_overrides_have_one_runtime_view`, `test_effective_cache_roundtrip`: `assert original_base == before`, `assert effective.gamma == .73`, target13/Doubletrue/LR.0007/capacity2048; inactive preset edit changes authored hash, preserves execution hash and seeded selected weights.
- [ ] Run `test_effective_run.py` red against compile→resolved object→cache; preserve the B07 inherited/full-level-replacement controls.
- [ ] Wire compiler and compiled roundtrip to the resolver; expose provenance and option roles without relabeling existing hashes or deleting presets.
- [ ] Run green and B07/B08 serialization/override controls; assert cache transport fingerprint may differ while execution identity stays equal.
- [ ] Review and commit `feat(config): expose effective run identity and provenance`.

### T03a: Approved archive/fresh-buffer import before storage schemas

**Interfaces:** Produce HC's P2 policy/immutable archive/export types and format9 canonicalizers, with approval `BAC-HISTORY-A-2026-11-01`. `HistoricalPreparedEnvelope(policy: HistoricalAccessPolicy, archives: tuple[HistoricalReplayArchive,...], available_learned_state: Mapping[str,object])` is prepared by `prepare_historical_envelope(payload, *, requested_mode, validate_legacy: Callable[[Mapping[str,object]],None]) -> HistoricalPreparedEnvelope`. It runs actual existing old validation, clones/preserves archival state and prepares the available non-replay state without installing runtime components. T10–T12 own fresh-buffer construction/actual adapter bodies. No generic unsupported-version migration is introduced.

- [ ] Add `test_approved_import_preserves_archive_and_seeds_empty_replay`, `test_old_identity_recipe_ignores_only_new_absent_fields`, `test_archive_failure_is_atomic`: genuine9/6 artifacts with uniform4/PER4/sequential5 auto-select approved archival import; archive query/export returns exact original values/priorities/episode boundaries/rewards, archived count is exact, and prepared active retained count is0. The explicit recorded_full_resume request diagnoses missing masks before mutation; already-unsupported/malformed states keep located refusal.
- [ ] Run `test_historical_dispatch.py` red against genuine pinned producer artifacts with recorded digests/key/version inventories. Query/export is exercised on actual old data, not invented abbreviated payloads.
- [ ] Implement approval-linked dispatch, immutable archives, separate available learned-state packet and standalone embedded archival serialization. Original files/digests remain unchanged; export is an additional exact native artifact. No unrecorded row gets a learner mask, priority index or sampling route. Preserve old recorded rewards verbatim as archival evidence.
- [ ] Run green on envelope encode/decode, archive query/export/digest equality, exact row counts, duplicate-source identity, old hash recipe and deep malformed/archive-publication failures with zero runtime mutation. Actual active-empty import, restored clocks, new warmup and later full current resume are required again in T10–T12/T25–T27/T38.
- [ ] Review and commit `feat(checkpoint): archive pre-capture replay under approved policy` before strict replay schema commits.



### T04: Lossless sidecar lowering — D16

**Interfaces:** Canonical declaration lowering accepts valid top-level and nested training sidecars additively. Equal duplicates retain both origins; conflicting duplicates refuse at both locations. Every supplied mapping is validated before lowering, including one shadowed by a duplicate.

- [ ] Add `test_nested_sidecars_survive`, `test_malformed_shadowed_sidecar_refuses`, `test_conflict_names_both_origins`: assert recording.enabled true/output_subdir survive, malformed extra refuses, unequal values do not silently win; top-level controls remain valid.
- [ ] Run `test_sidecars.py` red using full authored compile, including recording/run_metadata separately and together.
- [ ] Implement located normalization in DS; valid nested request changes resulting DTO/training identity and reaches the same canonical consumer fields.
- [ ] Run green plus B07 declaration-origin/store tests.
- [ ] Review and commit `fix(config): validate sidecars before declaration lowering`.

### T05: Canonical launch resolution

**Interfaces:** `resolved_launch.py` defines `ResolvedLaunch(root: Path, level_name: str, compiled: CompiledUniverse, effective: EffectiveRunConfig, declaration_origins: Mapping[str,str])`; `resolve_launch(path: Path, *, level_name: str|None) -> ResolvedLaunch`. Use compiler content discovery for pack/direct-level inputs and located missing/duplicate diagnostics. Do not introduce a filename heuristic.

- [ ] Add `test_pack_level_and_multidoc_resolution`: assert renamed experiment/training/brain, nested declarations and combined multidocument transport produce equal effective execution identities and correct selected level; ambiguous level remains a located explicit error.
- [ ] Run `test_discovery.py` red.
- [ ] Implement canonical root/level resolution around compiler discovery; public consumers receive the resolved object, not reread YAML.
- [ ] Run green with cached/uncached and absent/duplicate declaration controls.
- [ ] Review and commit `feat(config): resolve launch inputs through declarations`.

### T06: CLI and runner content transport — D20

**Interfaces:** CLI and `DemoRunner.__init__` consume `resolve_launch`; preserve flags and public constructor arguments. Omitted episodes reads `effective.training.training_loop.max_episodes`; explicit overrides are recorded.

- [ ] Add `test_real_cli_and_runner_accept_transport_changes`: real CLI subprocess/runner construction for B12's three variants returns success with bounded episodes3, and omitted episodes resolves100000 at dispatch; checkpoint-dir/port/level/force-new-VFS still propagate.
- [ ] Run `test_launch_transport.py` red, proving failures after successful compile before the fix.
- [ ] Remove filename preflights/direct single-document rereads in these consumers; keep located compiler diagnostics for genuinely missing content.
- [ ] Run green plus B12's conventional transport and parser controls; no long-lived server in focused verification.
- [ ] Review and commit `fix(cli): honor discovered declarations end to end`.

### T07: Preserve public loaders with canonical discovery — K03

**Interfaces:** Keep `load_exploration_config` and `load_curriculum_config` names/signatures/return DTOs. Resolve their pack/direct-level arguments through LR; document level ambiguity and resolved temporal references.

- [ ] Add `test_public_loaders_accept_relocation_and_period_of`: conventional and renamed inputs return equal DTOs; shipped L3 `{period_of: day_phase}` resolves before DTO construction; bare invalid training wrapper still refuses.
- [ ] Run `test_public_loaders.py` red.
- [ ] Implement adapters without deleting exports or forcing callers onto a new API.
- [ ] Run green and B12 direct-loader DTO controls.
- [ ] Review and commit `feat(config): extend public loaders with content discovery`.

### T08: Transition and finite masked-target primitives — D01/D11 seam

**Interfaces:** Produce P2's contract types/validation, `HistoricalLegalityUnavailable(ValueError)` and `q_targets.py::legal_bootstrap(q_online: Tensor|None, q_target: Tensor, legal: Tensor, bootstrap: Tensor, *, double_dqn: bool) -> Tensor`, preserving arbitrary leading flat/recurrent dimensions; `bootstrap=False` returns exact0 before masked max/argmax. `validate_successor_masks(masks: Tensor, dones: Tensor, *, action_dim: int) -> None` accepts empty terminals, diagnoses empty nonterminals.

- [ ] Add `test_terminal_empty_mask_is_finite`, `test_nonterminal_empty_mask_refuses`, `test_double_uses_online_legal_choice`: `assert terminal_value == 0`, `assert target == 3` for reward1/gamma.5/legalQ4/illegalQ100; online/target differing legal rankings prove Double selects online and evaluates target.
- [ ] Run `test_transition_contract.py` red; include batch1 shapes and poisoned unused terminal Q values.
- [ ] Implement the typed DTOs and target helper with no live-environment dependency, no multiply-zero-times-infinity path, and detached target results. Unknown-legality records cannot reach this helper or an alternative optimizer path: approved A archives them outside active replay. No legacy unmasked-bootstrap helper is created.
- [ ] Run green; assert invalid dimensions/dtypes/masks refuse without mutating inputs.
- [ ] Review and commit `feat(training): define historical successor legality contract`.

### T09: Commit successor legality at the environment producer

**Interfaces:** ENV produces P2's `successor_action_masks` after the same committed successor as returned observation. Existing `get_action_masks()` API remains.

- [ ] Add `test_mask_belongs_to_returned_successor`: a real state-dependent GET legality change is captured, terminal all-false masks are valid, cap successor remains selectable, returned masks cannot be changed by the next live step.
- [ ] Run `test_successor_producer.py` red through an authored pack; global disabled control remains zero.
- [ ] Add cloned step-info mask and explicit live-empty diagnosis using the canonical mask builder; preserve entry-active/terminal ordering.
- [ ] Run green plus B11's authored lane/reset controls.
- [ ] Review and commit `feat(env): publish owned successor action masks`.

### T10: Uniform replay historical-mask lifecycle

**Interfaces:** RB implements P2's new methods and extends push with optional explicit successor masks without removing unconstrained public buffer use. New qualified state carries masks and action dimension in every candidate/materialization path.

- [ ] Add `test_uniform_mask_wrap_sample_restore_atomic`: wrap capacity4 across six identifiable rows; assert each sampled observation's original successor mask survives wrap/restore; approved uniform4 import archives every old row unchanged, exposes query/export with exact archived count, and initializes active retained count0; no archive row can be sampled; recorded_full_resume requests refuse atomically; a malformed mask width/empty nonterminal refuses and leaves serialized state bitwise unchanged.
- [ ] Run `test_uniform_history.py` red; finite empty and terminal controls included.
- [ ] Implement allocation/push/sample/clear/stats/serialize/validate/prepare/install fields together; clones prevent caller or serialized-payload aliasing.
- [ ] Run green plus B04 uniform replay roundtrip/refusal suites.
- [ ] Review and commit `feat(replay): retain uniform successor legality`.

### T11: Prioritized replay historical-mask lifecycle

**Interfaces:** PB implements the same P2 contract, preserving indices, priorities, reward components and legacy sample API. This task changes storage, not the estimator law.

- [ ] Add `test_per_mask_priority_alignment_and_restore`: priorities select identifiable rows whose mask/reward/successor identities match before/after wrap/restore; invalid mask state refuses atomically. Approved PER4 import preserves all priorities/successors/rewards in queryable/exportable archive while active replay/priorities start empty; recorded_full_resume refuses before mutation and no archived priority can address a new active row.
- [ ] Run `test_per_history.py` red.
- [ ] Extend every PB tensor field, strict schema and restore candidate with masks/action geometry; preserve finite priority contents for T13.
- [ ] Run green plus B04 PER artifact tests; do not claim D10 fixed yet.
- [ ] Review and commit `feat(replay): retain prioritized successor legality`.

### T12: Real short windows and capacity/readiness — D02/G02

**Interfaces:** SB implements P2 retention/window/readiness modes, historical masks, stable endpoint IDs and exact real lengths. Legacy `store_episode`/`sample_sequences` remain supported. Episodes and serialized tensors are owned clones.

- [ ] Add `test_sixteen_short_episodes_do_not_crash`, `test_capacity15_has_viable_two_step_windows`, `test_capacity1_adaptive_retains_one_real_row`: lengths2/L3 fixed reports unavailable, adaptive gives real length2 with false padding; cap15 no hidden16 gate; cap1/L8 tail+adaptive gives length1, fixed-full gives named impossible readiness, no invented rows.
- [ ] Run `test_sequence_history.py` red; masks/successors match every real row and final boundary after eviction and restore; no cross-episode splice; approved sequential5 import archives every exact original episode/successor/reward field, starts0 active transitions/windows, and never splices archive data into a new window; recorded_full_resume refuses atomically.
- [ ] Implement modes/counts/readiness and serialization, including `loss_mask`/`lengths`, terminal versus truncation, and explicit partial-fragment identity.
- [ ] Run green plus B04 sequence buffer controls; mutating source/serialized data must not alter live retained tensors.
- [ ] Review and commit `feat(replay): support bounded recurrent fragments and readiness`.

### T13: Matching PER estimators and finite priorities — D10/candidate C01

**Interfaces:** Produce P3's `sample_units` using T08's `SamplingReceipt`; PB uses it without changing the existing successive draw law. Priority updates validate the entire request before mutation and combine repeated with-replacement IDs deterministically.

- [ ] Add `test_full_buffer_huber_gradient_zero`, `test_ordered_estimator_exact_expectation`, `test_actual_sampler_ordered_law`, `test_independent_estimator_exact_expectation`, `test_large_finite_priorities`: assert old `[+1,-9]` Huber gradient becomes0 at B=N; exhaustively enumerate N2..4/B1..N and compare expected each-row coefficient to1/N at absolute tolerance1e-12; instrument the actual sampler to assert every returned conditional q and ordered tuple probability agrees with that law, plus deterministic seeded frequency bounds against exact ordered probabilities; equal `[3e38,3e38]` gives probabilities.5/.5 and finite weights. Alpha0/beta0/beta1 and unequal priorities are separate controls.
- [ ] Run `test_per_estimator.py` red; prove negative control using old initial-P/sample-max formula fails the exact expectation, not a rare statistical draw.
- [ ] Implement scaled float64 scores, ordered conditional receipt, detached residual-total/independent weights and atomic finite priority updates; persist the chosen rule/mode.
- [ ] Run green. Include a bounded authored reward/Q→real learner qualification for C01: report reachable or still API-only with exact parameter bounds; do not force extreme corrupted network values or upgrade the historical finding. Fix finite API robustness regardless.
- [ ] Review and commit `fix(replay): match PER estimators to each sampling law`.

### T14: Add recurrent PER — D21

**Interfaces:** SB uses PS over P2/P3's explicit window units and objective; supplies `weights[B]`, stable `unit_ids[B]`, `update_priorities(unit_ids: Tensor, td_errors: Tensor, *, loss_mask: Tensor) -> None`, with real-row aggregation and eviction-safe identity.

- [ ] Add `test_recurrent_per_window_objective`, `test_recurrent_priority_restore_and_eviction`: exact expectation of weighted window means/anchor losses equals each declared uniform unit objective; a deterministic toy with two different zero-start histories for the same row and a real nonconstant LSTM control prove context-dependent losses are counted as declared, not equated by row ID; priority ignores padding, repeated IDs merge deterministically, evicted IDs cannot update a different window.
- [ ] Run `test_recurrent_per.py` red; test both sampling laws, short/full windows and both priority reductions.
- [ ] Implement recurrent priority/index lifecycle and serialization using PS, preserving uniform fixed-window and all-valid loss choices; no compile refusal substitutes for this capability.
- [ ] Run green, including strict malformed-ID/probability restore no-mutation and new-window initialization controls.
- [ ] Review and commit `feat(replay): implement recurrent prioritized sampling`.

### T15: Production collection, masked targets and learner readiness — D01/D02/D09/D21

**Interfaces:** POP uses `ReplayRequest`, `readiness` and `sample_batch`; appends stored successor masks to exact recurrent prefixes and flat pushes. Learner uses QT for legal choices; recurrent unroll groups real lengths, uses each network's own hidden state and real boundary successor, and weights the declared per-window objective once. Online enters train mode for updates; target stays eval. Buffer sample APIs supply all required state; no current-env legality query occurs while learning.

- [ ] Add `test_authored_target_matrix_and_direction`, `test_terminal_and_truncation_controls`, `test_ready_skip_preserves_update_clocks`, `test_archived_rows_cannot_drive_learning`: importing old maskless rows leaves them queryable/exportable with original rewards but active retained count0, zero sampled archive IDs and no optimizer update during new-row warmup; every subsequently sampled captured witness has target3. No test accepts target51 as a live optimizer behavior. Feedforward/dueling/token_set/recurrent × vanilla/Double × global/state-dependent illegal actions produce target3 rather than51 and WAIT bias decreases from4; true terminal target0, cap/bootstrap target3. Recurrent interior/final-real boundary and uniform/PER both execute real updates.
- [ ] Run `test_learner_legality.py` red; retain sixteen length2/L3 and capacity15 controls, plus identifiable padded junk that cannot change loss/gradient/hidden. A history-dependent recurrent control must distinguish crossed online/target hidden states.
- [ ] Replace the hardcoded16/batch-only gate with retained-transition warmup plus true sampleability/scheduled tick; remove recurrent-PER runtime refusal only after wiring its working learner; use shape-safe `squeeze(-1)` for batch1.
- [ ] Run green plus B03 recurrent bootstrap/BPTT/lane-learning gates; skipped samples do not advance optimizer, LR or target synchronization and do not clear rollout memory.
- [ ] Review and commit `fix(training): use historical legal targets and real readiness`.

### T16: Propagate effective warmup/options through the real runner

**Interfaces:** RR passes resolved min_size/replay modes to POP. Existing constructor call sites can deterministically derive the same resolved training policy from their compiled environment, with provenance; no undocumented local warmup default.

- [ ] Add `test_real_runner_warmup1000`, `test_real_runner_recurrent_per`: after2 retained transitions with min_size1000, `assert optimizer_updates == 0`; at1000 plus scheduled/sampleable opportunity the first update occurs. Authored recurrent-PER compiles, constructs, rolls out and performs a real finite update.
- [ ] Run `test_runner_readiness.py` red; use frequency3/target2 with a smaller independent warmup to assert updates only on eligible vector ticks, LR/target on successful update counts.
- [ ] Wire the shared resolved policy, including beta's explicitly named vector-tick horizon; preserve zero-gamma myopic behavior.
- [ ] Run green across all four authored fixture families; a fixed-full no-window diagnostic is not a crash or fabricated update.
- [ ] Review and commit `fix(runner): apply declared replay warmup and modes`.

### T17: Descriptor/value interactions while retaining mean — G01

**Interfaces:** NF passes P4's explicit encoder mode/hidden width into token-set/recurrent constructors; NET keeps linear state/forward behavior and adds per-type prepool interaction MLPs. Static context is target-owned/nonpersistent for both modes.

- [ ] Add `test_mean_can_bind_descriptor_value`, `test_linear_mean_is_preserved`, `test_semantic_permutation_absence_and_memory`: constructive row feature witness gives .375 versus.125; authored B02 complementary-variable pack has a selected nonzero Q distinction, semantic row+context permutation is equal within1e-6, absent/empty pooled values and encoder gradients equal exact0.
- [ ] Run `test_token_binding.py` red for the new mode; retain exact linear-mean alias as a truthful historical control rather than asserting random weights must distinguish.
- [ ] Implement P4 and mode-aware state identity/factory routing, preserving mean/attention, token/recurrent and zero-start sequence semantics.
- [ ] Run green plus B02 compact/context/empty/permutation/network suites and frame-vs-history separation.
- [ ] Review and commit `feat(agent): add interaction encoders to mean token policies`.

### T18: Bounded RND service and tail state — G03/G04

**Interfaces:** RND produces P5's service receipt and validates/restores pending observations, service settings and counters. Existing direct `update_predictor` remains a supported explicit one-minibatch operation; population will use the new service API at T25.

- [ ] Add `test_occupancy512_consumes_four_batches`, `test_paced_retention_is_bounded`, `test_two_of_three_tail_resume`: occupancy batch128 admits512/consumes512/updates4/pending0; repeated paced512 inputs respect bound and report overflow service/drop counts; saving after2 of3 then admitting row3 matches uninterrupted predictor tensors and optimizer count.
- [ ] Run `test_rnd_service.py` red; seven identifiable rows prove FIFO admission/consumption, frozen target unchanged, normalization count and zero intrinsic-weight contribution remain distinct.
- [ ] Implement bounded chunked ingestion, both pacing/overflow policies, receipts and pre-mutation tail validation. Explicit drop modes do not masquerade as lossless backpressure.
- [ ] Run green plus B05 normalization/update-timing/exploration tests; malformed tail/config/count state leaves target runtime unchanged.
- [ ] Review and commit `feat(exploration): bound predictor service and persist pending rows`.

### T18a: Resolve every authored exploration field at one boundary — R1

**Interfaces:** Produce P5a's RP policy/context/receipt types and `resolve_exploration_policy`. T03 consumes the resolved policy; this task runs immediately after T02, before T03 despite its domain-based identifier. It implements resolution, not a placeholder provider factory.

- [ ] Add `test_drive_selects_five_strategies`, `test_training_drive_override_roles`: full authored drive+training contrasts select exactly none/rnd/adaptive_rnd/count_based/icm, epsilon/RND/initial/annealing sources match P5a, explicit typed provider overrides beat recognized raw entries, inactive/unknown preset keys remain lossless with provenance. None/zero weights are distinct from nonexistent enabled toggles.
- [ ] Run `test_exploration_policy.py` red with actual DTOs and portable authored fixtures, including nonselected dictionaries, nonfinite active parameters and located equal-precedence conflicts.
- [ ] Implement P5a's exact precedence/roles, selected defaults and policy execution identity. Define all five provider parameter sets and context/receipt schemas now; no selected strategy is deferred out of the delivery scope.
- [ ] Run green and compiler/effective identity contrasts; each active knob changes policy identity and each preset remains authored identity without a false execution claim.
- [ ] Review and commit `feat(exploration): resolve authored provider and parameter ownership`.

### T18b: Add finite count-based novelty for the accepted selector

**Interfaces:** Produce COUNT's `CountExploration` with P5a quantization/LRU/count semantics, current exploration/action-selection protocol, RP service receipts and complete owned checkpoint state.

- [ ] Add `test_count_novelty_and_no_stat_query`, `test_count_capacity_and_restore`: same eligible row gives1 then1/sqrt(2); an unseen no-stat query gives1 and changes neither counts nor LRU; width.25 maps[-.01,0,.249,.25] to bins[-1,0,0,1] and extreme finite values remain well-defined; chosen quantization can merge/separate two authored states; overflow evicts exactly the declared oldest key and reports it. Restore yields identical next novelty/count order; malformed counts/duplicate LRU/config refuse atomically.
- [ ] Run `test_count_provider.py` red, including multiple same-tick rows, inactive lanes and finite/zero scale controls.
- [ ] Implement the shared-learner finite table, stable quantization/keying, epsilon protocol and serialized config/state. Preserve accepted raw config as resolved/preset data rather than silently deleting keys.
- [ ] Run green; legal action selection remains shared and predictor update count is explicitly0, not a fake trained model.
- [ ] Review and commit `feat(exploration): implement bounded count-based novelty`.

### T18c: Add transition-based ICM for the accepted selector

**Interfaces:** Produce ICM's P5a constructor, `compute_transition_novelty(context: IntrinsicTransitionContext, *, update_stats: bool) -> Tensor`, bounded complete-transition service and full state validation/restore. The existing observation-only API on old providers is preserved; the new ICM path requires actual transition context.

- [ ] Add `test_icm_uses_action_and_successor`, `test_icm_objective_gradients_and_tail`: same s with differing real a/s' changes inverse/forward objective as specified; controlled tensors prove `.5*mean(error**2)`, weighted CE/MSE loss and detached forward target, with nonzero inverse encoder gradient. One optimizer minibatch changes trainable weights; two-of-three pending transitions restored then third admitted produce identical update count/tensors without a global-RNG claim.
- [ ] Run `test_icm_provider.py` red; padding/completed-lane rows are excluded, absent/wrong action or successor context diagnoses rather than inventing s', and nonfinite/deep malformed state leaves the target unchanged.
- [ ] Implement encoder/inverse/forward models, explicit parameters and FIFO bounded-service policies; preserve actual predecessor/action/successor identity and serialize pending context/counters/optimizer/epsilon.
- [ ] Run green with loss-weight/feature/rate authored contrasts, zero contribution control and lossless versus declared-drop occupancy accounting.
- [ ] Review and commit `feat(exploration): implement bounded transition curiosity`.

### T18d: Construct all five selected providers and own continuation

**Interfaces:** Implement RP `build_exploration`/`ExplorationRuntime` using the existing explicitly parameterized epsilon/RND/adaptive classes and T18b/T18c constructors. Current provider-tagged state validates complete selected policy before installation; HC receipts retain actual old provider as archival provenance; live execution always uses the repaired authored selector and restores only its matching available subtree.

- [ ] Add `test_factory_constructs_selected_provider`, `test_provider_state_kind_and_scale`: all five real provider classes are selected by the authored drive; rnd fixed scale and adaptive current scale differ as declared; none scale/raw contribution0; epsilon tensors use training epsilon exactly; wrong provider state refuses without mutation. Repeated owned adaptive completion identity advances survival/annealing only once.
- [ ] Run `test_exploration_factory.py` red, including every current strategy save/load and old epsilon/RND/adaptive adapter signatures.
- [ ] Implement the facade/delegation, common reward/service/epsilon/state access and once-only completion ownership; keep old provider APIs callable. Old state records its actual historical provider as archival provenance; approved A restores matching available substate under the repaired authored selector and archives incompatible provider substate without executing the wrong selector or changing recorded old rewards.
- [ ] Run green, asserting all provider defaults/derived values are explicit and scale never hides in a duplicate modifier/replay multiplication.
- [ ] Review and commit `feat(exploration): construct declared providers with owned state`.

### T18e: Bind selected raw novelty and runtime scale into the existing composer

**Interfaces:** ENV captures an owned `IntrinsicTransitionContext` before/after the accepted physics step; RWC preserves `_calculate_shaped_rewards(*, active_on_entry, intrinsic_context=...)` and its current successor-phase provider invocation, now via ExplorationRuntime for all five choices. DAC accepts explicit `runtime_intrinsic_scale` and applies P5a's formula once. Old direct callers lacking new context retain their documented observation-only path for old providers; ICM requires its new complete context API.

- [ ] Add `test_real_composer_applies_runtime_scale_once`, `test_provider_phase_and_transition_identity`: with captured raw2/runtime.5/drive base.25/authored modifier2, effective intrinsic is.5; with extrinsic1/shaping.1 total is1.6 before any separate retirement bonus. Runtime scale0 yields intrinsic0 for real RND/adaptive/count/ICM; terminal mask follows existing semantics. Record the actual bound provider invocation and reward components through the real ENV→RWC→DAC path, using model/config controls rather than replacing the composer.
- [ ] Run `test_intrinsic_composition.py` red against the pinned always-Adaptive/unused runtime-scale path. Distinguishable predecessor/successor observations prove observation providers preserve post-physics reward phase; ICM gets the true s,a,s' while RND predictor admission remains predecessor-phase. Each eligible reward row updates stats once.
- [ ] Implement context/phase delivery and single scaling at DAC; keep drive base/modifier execution and existing retirement handling. Population's diagnostic novelty cannot replace/recompose canonical returned rewards or update normalization again.
- [ ] Run green; captured replay/sink total and components equal ENV's actual canonical outputs; changing initial/adaptive scale or drive base independently changes only its own factor.
- [ ] Review and commit `fix(exploration): apply resolved intrinsic scale in canonical rewards`.

### T18f: Real runner/population exploration routing and authored contrast

**Interfaces:** RR constructs only `build_exploration(effective.exploration, ...)`; POP binds its ExplorationRuntime into ENV, synchronizes per-lane epsilon/current scale, forwards owned completion events once and routes provider-specific service. T19's owned event API exists before this wiring task; T25 completes strict provider-state checkpoint integration.

- [ ] Add `test_authored_runner_strategy_reward_contrasts`, `test_epsilon_and_adaptive_completion_once`: five full authored packs reach real runner construction and their selected class/provider receipt, actual ENV→replay rewards reflect each provider/base/runtime/annealing contrast, none and initial0 yield exact zero intrinsic contribution, nonzero RND/count/ICM controls are positive. Scalar epsilon and per-lane action-selection tensors match before/after one committed episode decay; duplicate adaptive event changes no scale/history.
- [ ] Run `test_exploration_routing.py` red; changing only a drive selector cannot leave an undeclared always-Adaptive provider. Test same predecessor/successor phase identity and no double provider normalization/admission/composition.
- [ ] Wire the resolved policy/factory/facade into the real runner and population, replace class-only telemetry/service assumptions, and update POP get/validate/load provider-state dispatch together so this actual-runner package remains save/load-capable before T25 adds the joint replay/ledger atomicity gate; and retain all accepted selectors and old direct APIs. No missing selector is merely labeled unqualified to close C08.
- [ ] Run green across all five strategies and four family smoke paths, with canonical reward components, eligible seven-row accounting and later T25/T38 continuation obligations recorded.
- [ ] Review and commit `fix(runner): execute authored exploration policy end to end`.

### T19: Owned completion envelopes and clock ledger — C07

**Interfaces:** Produce P5's `LaneOutcome`/`ClockLedger`; POP owns canonical per-lane reward accumulators/envelopes while retaining existing completion DTO/API. `completed_outcomes: tuple[LaneOutcome,...]` exposes frozen events; `begin_batch_episode(index:int, planned_horizon:int) -> None` establishes event identity before reset/rollout.

- [ ] Add `test_lengths2_5_owned_events_and_clock_units`: assert7 eligible transitions,5 vector ticks,2 lane events, frozen earlier outcome/reward after later ticks and reset; reverse lanes and repeat two resets; cap/budget/shutdown/checkpoint cuts retain explicit reason and nonterminal successor.
- [ ] Run `test_outcome_clocks.py` red for the new ledger/envelopes, keeping B11's already-passing completion controls unchanged.
- [ ] Implement event snapshots and clock increments at their owned advancing events; successful learner updates advance optimizer ledger once, skipped updates zero. Preserve current adaptive once-only completion calls.
- [ ] Run green plus B03/B11 lane gates and an independent train-frequency/target/LR schedule witness with unequal clock counts.
- [ ] Review and commit `feat(training): expose owned outcomes and clock units`.

### T20: Completion-driven curriculum and meaningful adaptation — D12/D13/D14/G05

**Interfaces:** CB defines `commit_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> None`; CA/CS implement it with P6's event deduplication, completed metrics, dwell and named commitment/difficulty modes. Retain public legacy step methods as their documented step interface, without using them for completion snapshots.

- [ ] Add `test_full_survival_survives_reset`, `test_dwell_counts_ten_transitions`, `test_singleton_band`, `test_rate_has_declared_effect`: survival10/horizon10 gives1.0 after reset; dwell adds10; .6 singleton always.6; rates.01/.1 over10 eligible steps move toward target by.1/at most1.0, clamped to band, while stage-band output preserves its old mapping.
- [ ] Run `test_curriculum_events.py` red; same event twice causes no metric/dwell/stage change, distinct-lane completions remain independent, cap ending is retained.
- [ ] Implement completed fraction baseline/progress in equal units, commit once after thresholds/dwell/entropy, rate-limited mode and truthful inactive adaptation in stage-band mode.
- [ ] Run green plus B06 curriculum/stage-info/signal-purity controls; no second death/completion call is added.
- [ ] Review and commit `fix(curriculum): use owned completion metrics and clocks`.

### T21: Curriculum factory and option provenance

**Interfaces:** CF constructs existing static/adversarial choices with resolved commitment/difficulty modes and adaptation-rate units; CC/TC validation remains additive. Decisions report stage, difficulty, depletion and active/inactive mechanics separately.

- [ ] Add `test_factory_routes_curriculum_modes`: direct factory and compiled authored configuration select the same mode/units; accepted active-meter/reward-mode fields survive roundtrip with unqualified role rather than silent execution claims or removal.
- [ ] Run `test_curriculum_factory.py` red.
- [ ] Wire all P6 parameters, preserving existing strategy choices and old validated singleton ranges; do not bake generic stage topology into this defect fix.
- [ ] Run green with static/adversarial factory tests and full-pack option identity checks.
- [ ] Review and commit `feat(curriculum): resolve commitment and adaptation policies`.

### T22: Per-world dynamics capability — D15 producer boundary

**Interfaces:** ENV adds vector `depletion_multiplier` alongside existing scalar API. Validate bool/shape/nonfinite/negative-invalid inputs before mutation; explicitly broadcast `[N,1]` across every applicable per-world meter/transition depletion path.

- [ ] Add `test_vector_depletion_matches_independent_scalars`: energy1/depletion.1/multipliers[.2,1] gives[.98,.9]; scalar.5 still gives[.95,.95]. Reverse lane order, inactive lanes and substrate controls prove rowwise independence.
- [ ] Run `test_per_world_dynamics.py` red; malformed tensor leaves tick/meters/observation unchanged.
- [ ] Implement finite scalar-or-vector application without ambiguity or implicit lane0 broadcasts, preserving authored mechanics/reward ownership.
- [ ] Run green plus B11 environment/action-mask/lane controls.
- [ ] Review and commit `feat(env): apply depletion decisions per world`.

### T23: Joint curriculum routing through population and runner — D12/D15

**Interfaces:** POP forwards all decisions in lane order; RR supplies `begin_batch_episode`, obtains owned outcomes and calls curriculum's completion API exactly once, replacing the survival-as-reward legacy routing. Other sinks receive the same outcomes.

- [ ] Add `test_full_population_stages1_5`, `test_runner_completion_advances_curriculum`: real compiled population restoring stages[1,5] yields energies[.98,.9] with multipliers[.2,1]; completed10-step events retain fraction1/dwell10 and can satisfy declared advancement thresholds. Reverse lane order and duplicate flush negative controls.
- [ ] Run `test_curriculum_routing.py` red; this is the new full-population proof, not a relabel of B06's component witness.
- [ ] Wire vector decisions and owned completion routing, preserving once-only adaptive exploration updates and all current ending reasons.
- [ ] Run green through two consecutive authored episodes and B06/B11 compatibility controls; no lane0 authority or extra completion route remains.
- [ ] Review and commit `fix(curriculum): route per-world decisions and completed outcomes`.

### T24: Checkpoint boundary/schema and numeric selection — D04/G09 seam

**Interfaces:** Produce P7's LM types/selector and extend CK validation/metadata with explicit modes, identities and guarantees. Keep strict trusted-local/digest assumptions; this is no new security audit. Consume T03a's already-selected supported-version/auto-access policy; do not reopen it after storage changes.

- [ ] Add `test_numeric_latest_within_run`, `test_mode_and_boundary_validate_before_mutation`: actual valid checkpoint99999/100000 with different weights selects100000; unrelated run/temp/malformed filenames cannot silently win. Invalid next-index/mode/hash and malformed nested state refuse before runtime mutation.
- [ ] Run `test_checkpoint_contract.py` red; preserve force-new-VFS identity branch semantics.
- [ ] Implement common numeric selector and explicit boundary validators, retained existing identity hashes plus execution identity, and T03a's exact old/new mode dispatch, approved archival separation/active-empty import, source row-count metadata and format9 identity recipe. Never silently drop replay on format mismatch.
- [ ] Run green plus B08 checkpoint identity/lineage controls; verify the exact Option A approval and its scope; record any other proposed narrowing for approval and leave that other alternative unselected.
- [ ] Review and commit `feat(checkpoint): define load boundaries and numeric selection`.

### T25: Population predictor/replay/clock restore seam — G03/G04/C10

**Interfaces:** POP routes the selected ExplorationRuntime service (RND eligible predecessors, ICM eligible complete transitions, count/none explicit no-predictor result), updates CL from receipt, and validates/prepares replay masks/window priorities/tails and clocks before install. Provider-tagged validators recognize the complete new RND/adaptive/count/ICM/none state and tail key sets rather than rejecting or dropping added state. Old supported payloads dispatch through approved A: immutable archives separated from fresh active replay, available compatible provider/learned/world state restored, and source/mode/approval/row-count/clock metadata explicit. Current captured states retain complete active replay on full resume.

- [ ] Add `test_population_restores_tail_and_historical_masks`, `test_seven_eligible_rows_once`: [2,5] population admits exactly7 predictor rows, no post-completion rows; new tail replay/priority/ledger state roundtrips; approved pre-capture import with saved optimizer count17/vector ticks50 and two archived rows preserves those cumulative clocks, active count0 and exact archive rewards. With frequency1/min_size1000, two new captured rows leave update count17, row1000 permits update18 and LR/target follow that restored count; archives never satisfy warmup. Malformed deepest archive/tail or mask rejects with networks/optimizer/replay/curriculum-compatible owned population state unchanged.
- [ ] Run `test_population_restore.py` red; compare deterministic third-row predictor continuation without asserting global stochastic equivalence.
- [ ] Replace direct `obs_buffer.extend`/single-update bypass and isinstance-only RND/Adaptive dispatch; implement complete validation/materialization/install inventory and version metadata with explicit guarantees.
- [ ] Run green plus B03/B05/B08 focused checkpoint, eligibility and normalization controls; retain exactly one normalization/reward composition owner.
- [ ] Review and commit `fix(training): restore complete predictor and replay state`.

### T26: One episode-end checkpoint transaction — D03/D19/K05

**Interfaces:** RR creates/consumes `CheckpointBoundary`, commits outcomes/epsilon before periodic/final serialization and uses CK's numeric latest. Public `save_checkpoint`/`load_checkpoint` stay available with documented adapter semantics; no accidental extra +1.

- [ ] Add `test_periodic_epsilon_matches_uninterrupted`, `test_periodic_final_next_episode_agree`, `test_authored_interval_and_empty_run`: restart epsilon is.4, including selection tensor, after start.8/decay.5; completed indices100/101 restore next102 from either final/periodic boundary; interval5000 does not save at100, does save after5000 completed batches; explicit final policy is independent.
- [ ] Run `test_checkpoint_boundary.py` red using actual save/digest/load and distinct saved weights.
- [ ] Implement P7 order, numeric selected-run load, committed count cadence, exception/zero-episode guards and validation-before-install; avoid double decay/curriculum commit on load.
- [ ] Run green plus B09 periodic/final/identity controls; final checkpoint carries predictor tail, active captured replay, embedded immutable archives, approval/import mode, archived-row count and distinct clock units through T25; reloading that new artifact preserves active replay/warmup rather than repeating the archive reset.
- [ ] Review and commit `fix(runner): checkpoint committed episode-end state`.

### T27: Explicit serving modes, run view and one reset — D04/D18/G07

**Interfaces:** EV resolves P7's run view; LIVE uses CK numeric selection and applies deterministic eval or explicit MC dropout. Preserve public live load methods and recorded checkpoint identity/age. One population reset owns one world/random-episode advancement.

- [ ] Add `test_greedy_dropout_is_deterministic`, `test_mc_dropout_is_explicit`, `test_live_numeric_latest_and_single_reset`: repeated same-observation epsilon0 eval Q/actions equal exactly, configured MC mode varies under its recorded stream; newest100000 weights load; VFS0→1 exactly once; cap defaults to compiled value2 in the tiny pack and explicit viewer500 is recorded.
- [ ] Run `test_serving_modes.py` red; all four families, stacked recurrent dropout, train-mode control and display-without-second-hidden-advance included.
- [ ] Implement named evaluation/viewer override resolution, eval mode on construct/load, correct curriculum state policy/epsilon/cap, one reset and Q reuse.
- [ ] Run green plus B09 live identity/mode tests; do not claim training-stream isolation until T31.
- [ ] Review and commit `fix(serving): declare policy modes and evaluation run view`.

### T28: Truthful partial transfer and atomic strict mode — D17

**Interfaces:** Extend CK helper/report per P7 with explicit parameter policy; keep existing helper callable and preserve partial loading with a non-clean detailed report.

- [ ] Add `test_missing_meter_bias_is_partial_not_clean`, `test_strict_partial_refuses_atomically`: remove only `encoder.encoders.meter.bias` for the linear token/recurrent encoder; the interaction MLP declares its Sequential keys exactly as `encoder.encoders.meter.0.weight`, `.0.bias`, `.2.weight`, `.2.bias`, and its omission test first asserts `.0.bias` exists then removes that actual shared parameter; partial loads weight, retains target bias with exact missing/cold-start report and `assert not report.is_clean`; strict refuses before any earlier matching key mutates.
- [ ] Run `test_partial_transfer.py` red; complete current dictionaries remain clean, new/source-only types and non-type modules report every disposition.
- [ ] Implement per-parameter completeness/reporting and preflight shape checks; target context buffers stay bitwise unchanged.
- [ ] Run green plus B08 transfer controls; do not allege normal producers emit this malformed input.
- [ ] Review and commit `fix(transfer): report incomplete shared types truthfully`.

### T29: Artifact effective-identity coherence — G09 qualification

**Interfaces:** CU import recomputes resolved effective identity using the selected base+training, preserves authored/preset identity semantics and checks stamped identities before returning a qualified object.

- [ ] Add `test_modified_payload_identity_is_diagnosed`, `test_legitimate_preset_identity_roundtrip`: modified activation with old stamp fails coherent import; a valid preset edit with correctly updated authored identity and unchanged execution identity succeeds; plain/clone/cache/full-level-replacement roundtrips still equal.
- [ ] Run `test_artifact_coherence.py` red for the new coherence guarantee, without calling it an ordinary-cache defect.
- [ ] Implement strict semantic identity reconciliation under P1, preserving target token coherence and public import access policy; diagnostics distinguish modified input from cache freshness.
- [ ] Run green plus B07/B08 artifact/lineage/transport controls.
- [ ] Review and commit `feat(artifacts): qualify effective identity on import`.

### T30: Schema-aware transfer and explicit target-state policy — G09

**Interfaces:** Produce P7's `TransferArtifact`, `TransferReport` and `transfer_artifact`. POP keeps its current low-level weights-only seam and adds high-level source-provenance/schema/state policy validation before mutation.

- [ ] Add `test_fresh_target_transfer_has_no_history`, `test_same_shape_schema_mismatch_refuses`, `test_live_state_policy_is_explicit`: after fresh transfer replay0/optimizer state empty/clocks0/hidden0/RND pending0 and target equals online; incompatible same-shape schema leaves every target state unchanged; retained-compatible mode preserves/report its chosen replay/clock policy rather than silently clearing it.
- [ ] Run `test_artifact_transfer.py` red; include target-only/source-only types, head action/reward semantic mismatch reporting, partial/strict parameter policies and immutable target buffers.
- [ ] Implement validated prepare/install transfer and explicit source/target provenance; no zero-shot competence claim or hidden fresh-target precondition.
- [ ] Run green plus B08 complete-transfer/atomicity/context controls.
- [ ] Review and commit `feat(transfer): add schema-aware target state policies`.

### T31: Serving/evaluation isolation in shared training — G07/C12

**Interfaces:** IW defines `InferenceSession.start(view: EvaluationRunView)`, `load(ref: CheckpointRef)`, `reset()`, `step()`, `close()` across a process-owned model/env/RNG boundary. SERVER routes its existing public viewer/control requests to that session; LIVE keeps public adapters and standalone usage. No usable endpoint or stochastic mode is deleted.

- [ ] Add `test_training_serving_interleaving_isolated`: same seeded training prefix/continuation with versus without serving construction/load/reset/play/display/MC requests has identical training sampled row IDs, action draws, Q/optimizer tensors and clocks; child stream outputs may differ by declared mode without consuming parent RNG.
- [ ] Run `test_serving_isolation.py` red through actual server/session boundaries, not an unused isolated utility; include reload and two episode resets, failed child cleanup and recurrent display controls.
- [ ] Implement process-owned session and declared request/response identity/mode/age; do not call global `seed_all` in the parent while constructing a shared-training viewer. Standalone direct execution remains documented with its actual guarantee.
- [ ] Run green plus B09 unified/live tests and bounded interleaving differential across four families.
- [ ] Review and commit `feat(serving): isolate inference sessions from training state`.

### T32: Add a current all-family evaluator, preserve historical instrument — K03

**Interfaces:** New `scripts/evaluate_policy.py --config PATH --level NAME --checkpoint PATH --episodes N [named overrides]` resolves LR/EV and uses the qualified inference session, emitting JSON policy/run identity, seeds, cap, curriculum, reward components and survival. Historical `l2_baseline.py` remains available with its frozen FF protocol.

- [ ] Add `test_current_evaluator_all_families`, `test_historical_ff_evaluator_retained`: current CLI handles recurrent hidden/reset/display once, returns declared cap and comparable reward units; historical FF still executes its existing bounded test. It is not relabeled a generic evaluator.
- [ ] Run `test_evaluation_entry.py` red for the new CLI and preserve existing historical controls.
- [ ] Implement the explicit evaluator and documentation linking the two instruments' actual scopes, using canonical discovery for current evaluation.
- [ ] Run green plus B12 baseline/parser controls; no learning-quality claim from two-step smoke episodes.
- [ ] Review and commit `feat(eval): add declared all-family policy evaluation`.

### T33: Accepted recording work survives shutdown — D05

**Interfaces:** REC/DB/RT implement P8's acceptance fence, tickets, durable receipt, failure propagation and idempotent shutdown. DB indexing has unique run/episode/lane identity and a commit receipt; no success from thread exit alone.

- [ ] Add `test_immediate_shutdown_drains_selected_episode`, `test_shutdown_fences_concurrent_acceptance`, `test_writer_failure_propagates`: two real frames+end followed immediately by shutdown yields1 readable complete file/1 matching committed index/0 pending accepted items/stopped writer; deterministic barriers exercise enqueue/sentinel ordering without sleeps. Inject file/SQL failure, full queue and missing end separately; each yields explicit failed receipt/exception, never false success.
- [ ] Run `test_recording_drain.py` red through real recorder/database; retain B10 naturally timed success as a control, not a repair involving waiting.
- [ ] Implement P8 ordered drain, task ownership, atomic publication/receipt and failure channel; preserve existing periodic selector and accepted other criteria with truthful roles.
- [ ] Run green plus B10 shutdown/sink/artifact tests, including repeated shutdown and file/index disagreement checks.
- [ ] Review and commit `fix(recording): drain accepted output before writer shutdown`.

### T34: Runner cleanup owns recorder failure — C13

**Interfaces:** RR stops admission/flushes participated outcomes, waits for recorder drain resolution before DB close, records failed/interrupted/completed status from actual termination and persistence result; existing context-manager cleanup remains callable/idempotent.

- [ ] Add `test_runner_cleanup_persists_or_reports_failure`: ordinary authored runner immediate cleanup persists its selected file/index; injected writer failure cannot return completed/success; DB stays open through drain, then closes once. Keyboard shutdown and learner failure retain their explicit status/ending reasons.
- [ ] Run `test_recording_cleanup.py` red; no sleeps, fake writer success or swallowed exception acceptance.
- [ ] Wire P8 receipts/failures into cleanup/final-save ordering, preserving the original training exception when persistence also fails with a chained recorded cause.
- [ ] Run green with B10 two-episode runner/sink controls and bounded concurrent cleanup.
- [ ] Review and commit `fix(runner): propagate recording durability failures`.

### T35: Sink units and owned outcomes — C07/C13

**Interfaces:** DB/TB/REG consume the same owned outcomes and CL unit names. Existing useful counters/API remain, with explicit unit metadata; no generic-label-only allegation or blanket `total_steps` rename.

- [ ] Add `test_owned_sink_reconciliation`: lane[2,5] yields slot0 survival2/batch ticks5/live transitions7/two completions with exact canonical total/components and ending reasons across SQL, TensorBoard and registry; altered scratch sink survival3 causes disagreement refusal. Distinct optimizer count proves tick/update labels are meaningful.
- [ ] Run `test_sink_units.py` red only for added explicit units/outcome wiring; retain already-passing B10 numerical controls.
- [ ] Implement ledger/output fields and committed checkpoint sequence/loaded-model age where owned, preserving reward/end-reason checks and fail-closed export input.
- [ ] Run green plus B10 accounting/database/sink suites.
- [ ] Review and commit `feat(telemetry): report owned outcomes and clock units`.

### T36: Effective hyperparameters and honest intervention reporting

**Interfaces:** RR emits EF values/roles/identities plus CL units and declared checkpoint/intervention policy. Keep existing useful fields with unit annotations; replace hardcoded reported intrinsic weight1.0 with actual effective value.

- [ ] Add `test_effective_hparams_and_interventions`: reported LR/gamma/min_size/intrinsic weight match resolved values; selected checkpoint interval and predictor modes are explicit; fixed `randomize_affordances:false` retains every position at episode5000 and logs an actual no-op rather than a claimed layout change.
- [ ] Run `test_effective_telemetry.py` red for reporting, preserving B09's fixed-layout refutation.
- [ ] Wire EF/CL metadata, explicit initial/final/periodic policies and actual intervention effect/status. Do not remove a working intervention; name and record it.
- [ ] Run green and B09/B10 telemetry/lifecycle controls; no fabricated toggle named intrinsic.enabled is introduced as a repair requirement.
- [ ] Review and commit `fix(telemetry): report effective settings and interventions`.

### T37: Joint authored learning support matrix — C01/C04–C09

**Interfaces:** Black-box authored fixtures exercise the production compile→environment→population→replay→optimizer path. Write `docs/remediation/bac/support-matrix.json` with exact candidate SHA, supported/qualified/unqualified cells and evidence paths; no parse-only support claims.

- [ ] Add `test_joint_family_replay_matrix`: all four families, all five selected exploration providers, vanilla/Double, uniform/PER, preserved/new encoder/aggregator modes, both PER draw laws and full/short recurrent geometry. Assert legal target3/wrong-direction repair, min_size1000, finite weighted objectives and once-only7/5/2 lifecycle; matrix cells point to real updates rather than B09's collection-only recurrent run.
- [ ] Run `test_joint_learning.py` red before changing production in this package; failures route to owning earlier package, never get patched around in the probe.
- [ ] Add bounded joint probes/negative controls only, including real seven-row RND service and per-world stages[1,5] through production population; preserve zero-width/gamma0/preset positive controls.
- [ ] Run green and the owning fixed-SHA focused suites; require fresh other-model adversarial review of probes and result claims.
- [ ] Commit `test(bac): qualify authored learning support matrix` after all earlier repairs/reviews.

### T38: Joint restart/transfer/serve/discovery matrix — C02/C03/C10–C12

**Interfaces:** Use real current-format artifacts, valid digests and public loaders; compare owned learned state/next-episode and declared evaluation settings, not an unpromised exact global stream.

- [ ] Add `test_joint_restart_transfer_serving`: four families train/update/save/load/serve; periodic/final next102 and epsilon.4; numeric100000 latest weights; all five provider kinds/scales and their owned RND/ICM tails/count tables restore; all active masks/priorities intact; approved pre-capture artifacts remain byte-identical and archive query/export preserves recorded rewards, while no archived row enters sampling and current full resume preserves its active buffer; target-schema/fresh-transfer state policy; renamed/multidocument launch/resume/eval/serve; deterministic/MC modes, one reset and isolation all agree with declared views.
- [ ] Run `test_joint_restart_serving.py` red; malformed deepest payload/identity/schema cases must leave runtime unchanged, and display must not advance recurrent memory.
- [ ] Add joint black-box acceptance and artifacts only; route any production defect to its owner and re-review that package before repeating this gate.
- [ ] Run green at detached candidate SHA; old uniform4/PER4/sequential5 imports auto-dispatch through approved archival/fresh-qualified-buffer access, with exact readable/exportable contents, approval/mode/row-count receipt and restored cumulative clocks; new warmup excludes archives. Later current captured checkpoints restore all active replay without clearing it, and every sampled row satisfies C05. Never accept invented masks or silently empty replay.
- [ ] Review and commit `test(bac): qualify restart transfer and serving seams`.

### T39: Joint persisted-output acceptance — C07/C13

**Interfaces:** Real runner SQL/TensorBoard/selected recordings/export accounting use matching event IDs and receipts at one candidate.

- [ ] Add `test_joint_owned_output_pipeline`: two episodes of [2,5] and reversed lanes reconcile7 live/5 ticks, frozen earlier outcomes, reward components and six ending reasons; immediate shutdown leaves one matching file/index per selected episode or explicit failure; malformed sink control rejects.
- [ ] Run `test_joint_outputs.py` red; writer scheduling is controlled by barriers, not delay-based assertions or universal-loss claims.
- [ ] Add authored output acceptance only and preserve current periodic selection controls plus truthful inactive richer criteria metadata.
- [ ] Run green with real file readability/index commit checks and interruption/failure statuses; no post-terminal row is labeled experience.
- [ ] Review and commit `test(bac): qualify durable owned outputs`.

### Final repository gate, then T40: Finite learning qualification

**Gate owner:** integration coordinator. Measured environment is four CPU quota / five CPU affinity, 16GiB RAM, approximately0.3GiB initially used and no competing tests. Parallelize independent checks with explicit CPU/thread limits and avoid oversubscribing PyTorch; before any costly test verify collection, imports, fixture validity and exact SHA. Verification-only source inventory is the three reviewed joint tests (≤1050 lines) and GE (≤300), **4 files / ≤1350 lines** for that worker/reviewer. Existing suites execute without reading additional source. Before every implementation commit, run the standing repository gate: `CUDA_VISIBLE_DEVICES= uv run pytest tests -q --no-cov -p no:cacheprovider -n auto --dist worksteal`, `uv run ruff check .`, `uv run black --check src tests scripts`, `uv run mypy src/townlet`, `uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet`, `uv run python scripts/validate_compiler_cli.py`, and `uv run python scripts/gen_expression_functions_doc.py --check`. Cap test workers at the available four-CPU quota when auto affinity would oversubscribe, recording the exact invocation. At the final candidate SHA after the source-verified documentation pass, repeat these unfiltered checks in a detached checkout, plus the project coverage invocation `uv run pytest`, `uv run pytest -m slow` and applicable GPU-marked cases on available hardware. Independent lint/type/documentation checks may run concurrently within measured limits. Verify `token_type_schema_hash` retains prefix `de093a6e9f59924e` on every compilable shipped level. If shipped config inputs change, coordinator runs `uv run python scripts/regen_frozen_live_inputs.py` and commits the inventory diff; YAML fixture additions must be included if the inventory tool covers them. Record exact command/selection/skips/failure reasons; unavailable GPU is explicitly unqualified, not passed. Use the project's configured ≥70% coverage gate. Do not replace these commands with the historical670-pass baseline or sum overlapping slices. Any failure returns to its owning package, is repaired/re-reviewed, then the affected gates and final unfiltered gate rerun at the new SHA. Do not start learning qualification before integrity gates pass.

**T40 interfaces:** `test_learning_comparison.py` is an executable comparison harness using the current evaluator and explicit cohort manifest under `docs/remediation/bac/learning/`. Run only when implementation is later authorized; this planning work launches no campaign.

- [ ] Define the exact finite cohort before running: four fixture families × seeds[11,29,47], 10000 admitted eligible training transitions per run (record indivisible-step shortfall), evaluation20 fresh episodes per seed with the same declared cap/world/reward/curriculum view, learned policy versus seeded random-legal and scripted WAIT baselines. Add a paired linear-mean versus interaction-mean descriptor-binding task; retain historical M4 as context, not current evidence.
- [ ] Verify harness negative control with an intentionally observation-independent constant policy: descriptor-conditioned success cannot exceed its declared balanced-task chance bound within the recorded confidence interval; a scripted correct policy supplies the positive task-solvability control. A mock evaluator returning the training reward is not acceptance.
- [ ] Execute the finite cohort after the repository gate, recording run/evaluation identities, checkpoint sequences, seeds, budgets/realized counts, extrinsic reward, raw novelty/effective intrinsic contribution, total reward, survival and task success separately.
- [ ] Report paired seed outcomes and uncertainty, compare against both named baselines, and state whether a preregistered practical threshold is met. Threshold for the balanced two-choice binding task is mean success≥.8 and lower95% Wilson bound>.5 over60 evaluation episodes per family; its constant negative control and scripted positive control must calibrate the task. General survival tasks report results without inventing a convergence threshold. Failure to beat baseline is an unresolved learning qualification, not permission to remove a family/algorithm.
- [ ] Fresh other-model review the protocol/results, retain failures/limits, and commit `test(eval): record finite BaC learning qualification`. Any algorithm/model improvement prompted by results gets its own additive design, bounded tasks and evidence; cognition/graphs/new algorithms remain available future directions.

## Coverage and disposition register

| Finding | Implementing / proving tasks | Disposition |
|---|---|---|
| D01 | T03a,T08–T15,T25–T26,T37–T38 | Legal target/gradient for every optimizer row; approved A archives old maskless history, starts fresh qualified replay and preserves query/export, with no historical P1 exception |
| D02 | T12,T15–T16,T37 | Real sampleability/no-update; additive short-window support |
| D03 | T24–T26,T38 | One committed epsilon/next-episode boundary |
| D04 | T24,T26–T27,T38 | Common numeric selected-run latest; assert actual newer weights |
| D05 | T33–T34,T39 | Accepted-work fence, durable drain and explicit failure |
| D06 | T01–T03 | Located negative-geometry diagnostic; working zero preserved |
| D07 | T01–T03 | Located invalid Nesterov/momentum diagnostic |
| D08 | T01–T03 | Finite authored learning rate and effective optimizer controls |
| D09 | T10–T16,T37 | Authored retained-transition warmup plus sampleability and clocks |
| D10 | T13–T15,T37 | Retained successive sampler with correct conditional estimator; independent option |
| D11 | T08,T37 plus action-selection change below | Exact-zero illegal probability; no native-illegal-draw claim |
| D12 | T19–T23,T35,T37 | Owned completed metrics and eligible-transition dwell |
| D13 | T19–T23,T35,T37 | Actual planned-horizon survival fraction |
| D14 | T20–T23,T37 | Singleton difficulty band remains exactly .6 |
| D15 | T22–T23,T37 | New actual full-population per-world proof |
| D16 | T04,T33,T38 | Validate every sidecar placement, no erasure |
| D17 | T28,T30,T38 | Truthful partial report and atomic strict option |
| D18 | T15,T27,T31–T32,T38 | Explicit train/eval/MC modes with isolated serving |
| D19 | T02,T24–T26,T36,T38 | Authored completed-batch cadence, separate initial/final policy |
| D20 | T05–T07,T32,T38 | Canonical content transport through public consumers |
| D21 | T14–T16,T37–T38 | Additive operational recurrent PER; no authoring closure |
| G01 | T02,T17,T30,T37,T40 | Interaction mean mode/proof, existing linear/attention retained |
| G02 | T12,T14–T16,T37 | Retained-transition capacity/warmup, real prefixes, honest fixed-window impossibility |
| G03 | T18,T25,T37 | Occupancy/paced bounded service and explicit counters |
| G04 | T18,T25–T26,T38 | Pending predictor tail continuation and atomic restore |
| G05 | T20–T23,T36 | Defined adaptation units/effect plus preserved stage-band role |
| G06 | T01–T03,T16,T37 | Gamma0 adopted consistently |
| G07 | T27,T31–T32,T38 | Declared run view, one reset, interleaving qualification |
| G08 | T02–T03,T29,T36 | Preset retention, authored/effective identity and roles |
| G09 | T24,T28–T30,T38 | Schema-aware artifact coherence/transfer/state policy qualification |
| X01 (post-review validated exploration selector/scale finding) | T18a–T18f,T25,T37–T38,F08/F16/F17 | Actual none/zero reward becomes0; all five current providers/scales repaired; approved archived old rewards remain unchanged evidence and are never reinterpreted or sampled |
| Candidate C01 (B04-C01) | T13,T37 | Numerical API repair and separate reachability qualification; not retroactively one of D01–D21 |

### Required small action-selection package T08a — D11

This independently reviewable package follows T08 and precedes T15/T37. Its complete worker/reviewer inventory is **W AS, R QT, T(action_probabilities): 3 files / 690 projected lines**; it is a DAG node, not an unbudgeted addition to T08. Preserve all existing strategy callers and add explicit live-empty diagnosis, with terminal/inactive bypass controlled by the producer's eligibility contract.

- [ ] Add `test_disabled_mass_exact_zero`, `test_live_empty_mask_diagnoses`: capture the real native sampler input for Q[[100,1]], mask[[False,True]], epsilon1 and assert weights[[0,1]] exactly; epsilon0 chooses1, mixed rows/per-lane epsilons preserve legality; a live empty row fails diagnostically rather than selecting unmasked greedy.
- [ ] Run `test_action_probabilities.py` red; no100M-draw rare-event campaign is needed.
- [ ] Replace epsilon dust on false entries with normalization over the true legal set only; preserve random/greedy strategy choices and zero contribution for inactive rows.
- [ ] Run green plus B05 epsilon/exploration suites; adjust existing all-invalid fallback expectation to the declared live-empty policy, without refusing an accepted working live state silently.
- [ ] Review and commit `fix(exploration): assign zero probability to disabled actions`.

| Contract | Complete implementing/acceptance coverage |
|---|---|
| BAC-C01 | T01–T03,T14–T17,T27–T32,T37–T40; operational four-family matrix and honest unqualified cells |
| BAC-C02 | T01–T07,T16–T18,T21,T24,T29,T36,T38; lossless/finite effective configuration and preserved options |
| BAC-C03 | T04–T07,T27,T32,T38; content discovery through launch/load/resume/serve/eval |
| BAC-C04 | T17,T28–T30,T37; compact context, interaction proof, permutation/absence/empty and target ownership |
| BAC-C05 | T08,T08a,T09–T15,T22–T23,T37; historical legality, all-family selection/targets and truncation |
| BAC-C06 | T10–T16,T37; retained warmup/capacity, exact sampling objectives, recurrent PER/short windows |
| BAC-C07 | T15–T16,T19–T26,T35–T39; owned completion and distinct clocks |
| BAC-C08 | T08a,T18,T18a–T18f,T19,T25–T26,T35–T37; eligible predictor, bounded pacing/tail and reward ownership |
| BAC-C09 | T19–T23,T35–T37; completed metrics/adaptation and per-world dynamics, K02 truthful scope |
| BAC-C10 | T24–T30,T38; mode/boundary/next-index/latest/atomic restore and declared historical limits |
| BAC-C11 | T28–T30,T38; partial/strict truth, schema/provenance and fresh/retained target-state policy |
| BAC-C12 | T15,T27,T31–T32,T36,T38,T40; mode/reset/memory/view/stream isolation and evaluation identity |
| BAC-C13 | T04,T19,T24,T27,T33–T36,T39; owned unit/identity telemetry and durable selected output |

| Known/deferred item | Explicit disposition and additive roadmap |
|---|---|
| K01 exact stochastic/mid-episode continuation | Retain **deferred guarantee**, not a fresh-episode defect. T03a/T24 implement approved A archival/fresh-buffer import for pre-capture history and unchanged current full resume; T24 records Python/NumPy/torch CPU/CUDA/exploration/environment/effect/item/replay RNG and replay index-to-transition ordering inventory/owners as a reference table. Future exact mode requires a separately planned differential: uninterrupted versus restored draw identities, scheduling and mid-episode world/rollout state match. No exact claim until that passes; no ban on implementing it. |
| K02 generic stages/active meters/reward switching | T02/T03/T21/T36 preserve fields and identify currently applied depletion versus inactive meter/reward labels. Separate additive roadmap: authored stage/edge schema with units and provenance → per-world stage decision → real active-meter and shaped/sparse reward consumers → checkpoint identity and before/after world/reward witnesses. Existing five-stage/static choices remain presets. This unbuilt feature is not a newly confirmed regression; no arbitrary prohibition or silent option removal. |
| K03 historical evaluator/public loaders | T07 extends public loaders; T32 adds current all-family evaluation alongside the preserved frozen FF instrument. Historical records remain historical; no false generic-evaluator guarantee. |
| K04 richer recording selection | T02/T03/T33/T36 retain periodic and accepted performance/stage-transition/stage-boundary settings, publish active/inactive roles, and qualify periodic durability now. Additive follow-on: immutable selection context from owned outcomes/stage transition, reason-set receipt and bounded pre/post boundary buffer, positive/negative criteria tests plus durable-output gate. It needs its own authored criteria specification/bounded packages before claiming delivered support; no deletion/refusal is selected. |
| K05 final next-index discrepancy | Repair in T24/T26/T38, independently of D03; actual indices100/101 yield next102 without another +1. |
| K06 cognition/topology/named modules/execution graphs | Retain unbuilt targets in roadmap, not regressions or current delivery claims. Next design can add schema/registry/graph interfaces with a concrete user task and its own acceptance; this plan imposes no categorical cognition/algorithm/complexity ban. |

Resolved/refuted items stay out of bug work: optimizer-update LR scheduling already matches r2 (documentation/units reconciliation only); fixed-layout episode5000 mutation is refuted (preserve no-op control, truthful log in T36); nonexistent intrinsic.enabled toggles are not ignored accepted fields (preserve strict refusal, zero initial weight); selected base plus five overrides is valid; no ordinary stale-cache failure or checkpoint security finding is established by B08's modified input. Historical phantom-lane/terminal-successor/reset controls remain passing protections, not reopened defect counts.

## Final independent spec, design and source review wave

Package reviews do not substitute for this gate. After integrating T01–T39, source-verified documentation, and any added learning-harness source, the coordinator freezes one candidate commit `FINAL_SHA`. All final reviewers are fresh contexts that implemented none of their assigned files, use the other model from their lens's primary last implementer, and receive the complete r2 design, findings, current acceptance ledger, option/support matrix, package receipts and this plan. They inspect the **current final source**, not earlier package versions. Every lens checks all applicable clauses of C01–C13 and D/G findings, distinguishes existing/revised/legacy guarantees, and attempts authored positive/negative cross-seam probes. No lens may expand its source inventory without reslicing first.

Each lens owns a scratch probe `/tmp/bac-final-<FINAL_SHA>/<lens>/probe.py` capped at350 lines and a report `docs/remediation/bac/final-reviews/<FINAL_SHA>/<lens>.md`. The scratch probe counts in the inventory below even if it imports existing tests. All source reads and execution use a detached checkout at `FINAL_SHA`; record `git rev-parse HEAD`, clean status and imported `townlet.__file__` before and after. Reports quote precise **current** source lines, exact commands/results, D/G/C ledger IDs, closed/open/qualified dispositions and coverage limits; a suite pass alone is not a full-spec verdict. Generated reports are reference material and do not mutate the reviewed source candidate.

| Final lens / primary owner contrast | Complete implementation/test read inventory, including its new probe | Files / projected lines | Principal contract/evidence responsibility |
|---|---|---:|---|
| F01 configuration; other model than last BC/TC owner | BC750, TC650, OP500, EF300, probe350 | 5 /2550 | C01/C02: every accepted active/preset/derived knob, finite validity, effective identity, new exploration selection roles |
| F02 compiler/artifacts; other model than last CU owner | UC1100, CU1750, DS750, HC450, probe350 | 5 /4400 | C02/C03/C10/C11: lossless lowering, full replacement, old/current hash and approved archive dispatch and coherent import |
| F03 entry/evaluation; other model than last CLI/GE owner | LR250, CLI300, GE300, HE320, probe350 | 5 /1520 | C03/C12: all supported transports, current evaluator and preserved historical FF protocol |
| F04 environment/outcomes; other model than last ENV owner | ENV2000, AM250, ST350, EP180, probe350 | 5 /3130 | C05/C07/C09: exact successor-mask timing, eligibility/endings, per-world action/depletion/owned outcomes |
| F05 flat replay/math; other model than last PB owner | RB850, PB1000, RC250, PS300, probe350 | 5 /2750 | C05/C06/C10: storage/restore lifecycle, actual draw law, beta1 objective, finite numerics, approved archive query/export and zero archive sampling |
| F06 recurrent learner; other model than last POP owner | SB1100, POP3000, QT180, probe350 | 4 /4630 | C01/C05/C06/C07/C08/C11: actual targets/direction, real short windows/context/hidden state, readiness/PER, approved archive/current-full dispatch and transfer consumer |
| F07 token representation; other model than last NET owner | NET750, NF250, `src/townlet/agent/token_input.py`150, `src/townlet/universe/token_hashes.py`150, probe350 | 5 /1650 | C04/C11/C12: descriptor binding existence, permutation/absence/empty, schema/context ownership and correct MLP omission key |
| F08 exploration; other model than last RP/RND owner | AS160, RND500, AI300, RP450, probe350 | 5 /1760 | C02/C05/C08/C10: selected strategy construction, reward ownership, exact zero mass, bounded predictor/tail and continuation |
| F09 curriculum; other model than last CA owner | CB150, CA800, CS220, CF150, probe350 | 5 /1670 | C02/C07/C09: completion/step commitment modes, fractions/dwell/rates/bands and per-lane decisions |
| F10 runner/telemetry; other model than last RR owner | RR1500, CL180, CC150, REG200, probe350 | 5 /2380 | C02/C07/C08/C09/C10/C13: real resolved-policy wiring, episode transaction, effective settings/units and cleanup ordering |
| F11 checkpoint/transfer; other model than last CK/TR owner | CK1000, LM220, TR300, RC250, probe350 | 5 /2120 | C05/C10/C11: current-full/approved-archival mode guarantees, approval/row-count/warmup clocks and atomic archive failure, complete/partial/fresh/retained transfer and numeric selection |
| F12 serving; other model than last LIVE owner | LIVE1500, EV300, SERVER700, IW300, probe350 | 5 /3150 | C01/C03/C10/C12/C13: four-family mode/view/reset/memory/isolation, handoff identity and actual public paths |
| F13 public strategy/load APIs; other model than last loader/strategy owner | EXL80, CUL80, `src/townlet/exploration/base.py`150, `src/townlet/exploration/epsilon_greedy.py`150, probe350 | 5 /810 | C03/C08/C10: retained loader/exploration APIs, effective epsilon and strategy-state protocol |
| F14 durability/sinks; other model than last REC/DB owner | REC550, RT150, DB800, TB650, probe350 | 5 /2500 | C07/C13: acceptance fence, scheduling/failure interleavings, matching file/index and owned sink reconciliation |
| F15 learning protocol; other model than T40 harness owner | GE300, EV300, `tests/test_townlet/regressions/bac/test_learning_comparison.py`300, probe350 | 4 /1250 | C01/C12: finite budgets/cohorts, authentic controls, separate reward metrics, qualified claims rather than historical extrapolation |
| F16 additive curiosity; other model than last ICM/COUNT owner | COUNT300, ICM500, RP450, RND500, probe350 | 5 /2100 | C01/C02/C08/C10: all five selected providers, actual count/transition effects, objective/gradient correctness, bounded service and exact owned state |
| F17 canonical composition; other model than last DAC/ENV owner | ENV2000, RWC150, DAC1100, DRIVE750, probe350 | 5 /4350 | C02/C05/C08/C13: actual bound provider, successor/predecessor phases, zero/base/runtime/modifier scaling exactly once, true reward/replay contrast |

HC and RP are the historical-access and exploration-policy modules defined by T03a/T18a. All affected implementation modules, including additive count/ICM and the canonical composition seam, have a current-source owner in this wave, with intentional boundary overlap. Existing unchanged external implementations are executed through authored probes; a new contrary source hypothesis routes to a separately bounded lens rather than silent extra inspection.

- [ ] Coordinator first verifies probe collection/import/fixture validity, resource limits and common `FINAL_SHA`, then dispatches independent lenses; tests share the four-CPU quota while model/source reviews may proceed concurrently. Every lens runs its filed predecessor repros relevant to the contract and independently authored current-source positive/negative probes, including the world0 differential over compilable shipped levels where applicable.
- [ ] F01–F17 each issue `GREEN` or `NOT GREEN` with the finite D/G/C closure table, source citations, commands, known K/candidate/P3 dispositions and limits. A final lens cannot inherit a predecessor's approval without checking changed current source. Contract wording and active/inactive authoring docs are checked against behavior, not used as implementation evidence.
- [ ] A fresh independent synthesis reviewer reads only the17 reports, complete r2 spec/findings/current ledger and source-reference manifests (no additional implementation reads, **0 files/0 lines**); it reconciles every D01–D21/X01/G01–G09/BAC-C01–C13, shared interface and conflicting lens result. It requires all blockers resolved, no unapproved in-scope gaps, exact approved archival policy/roadmap qualifications, and common-SHA unfiltered repository gates. Missing evidence or contradictory claims is `NOT GREEN`, not majority approval.
- [ ] Route each P1/P2, in-scope gap or documentation contradiction to its original bounded implementation owner; repair, run red/green and the standing gate, and independently review the fix. Freeze a new immutable SHA, rerun changed/dependent final lenses and all prior negative controls. Unchanged lenses receive a fresh final-SHA source/diff/behavior check within their same inventories before reissuing verdict; if that check finds a dependency or unexplained difference, rerun the full lens. Repeat the synthesis and final repository gate at the new SHA until the finite exit ledger is satisfied.
- [ ] If T40 adds source or documentation after this wave, it creates a new final candidate and triggers the same final-SHA refresh/gates; no final approval may refer to superseded bytes. Learning outcomes below threshold remain a named qualification requiring the authorized additive repair/design cycle; P3 remains separately logged and finite. Preserve scope/approval decisions explicitly rather than silently reclassifying required gaps as optional.

## Exit and handoff

- [ ] Each package, including T03a/T08a/T18a–T18f, has red/green evidence, exact bounded read inventory, ownership commit, fresh other-model adversarial approval and repaired dependencies.
- [ ] D01–D21/X01/G01–G09 have final candidate assertions in the register; C01 candidate reachability is honestly dispositioned; K01–K06 retain the statuses above; C01–C13 all have joint evidence.
- [ ] Final detached-SHA full repository gate and F01–F17 fresh final spec/design/current-source verdicts plus independent synthesis pass, with exact skip/hardware limits and meaningful family/option support matrix; T37–T39 joint probes pass at that same SHA. Existing green baseline totals or earlier package approvals are not substituted.
- [ ] T40 finite learning report follows integrity acceptance, preserves unsuccessful results and makes only measured learning claims. A failed learning threshold remains an open qualification and starts an additive improvement cycle.
- [ ] Only the precise pre-capture optimizer-history reduction in approved Option A (`BAC-HISTORY-A-2026-11-01`) is selected. Verify immutable archive/query/export preservation, available state/clocks restored, fresh active warmup and unchanged current full resume; no known wrong-target training exception remains. Any other reduction still needs concrete approval and cannot be inferred from pre-release status.
- [ ] Planner self-review checks spec/finding/contract coverage, task-sized decisions, interface/type consistency, Review Focus tests, proportionality, read budgets and serial ownership. The separate Astra MEDIUM reviewer evaluates the exact file SHA256; requested revisions return to the same planner, then the same reviewer until no blockers. Do not edit approved bytes without another review.

### Finite acceptance ledger, documentation and stop rule

The coordinator owns `docs/remediation/bac/acceptance-ledger.json` and generates one row for every D01–D21, X01, G01–G09, BAC-C01–BAC-C13, K01–K06 and candidate C01. Required row fields are `id`, `classification`, `in_scope`, `tasks`, `test_nodes`, `command`, `expected_assertion`, `candidate_sha`, `evidence_paths`, `disposition`, `remaining_severity`, `approval_reference`. The tables above provide task mapping; each named test in its owning task supplies the exact executable node/assertion and the common command supplies its invocation. Initialize rows as PLANNED, never CLOSED merely because the plan mentions them. Final D/G/C rows need current-SHA executable evidence, zero unresolved P1/P2 and zero unapproved in-scope design gaps, with no historical optimizer exception. D01/X01/C05/C08/C10 rows record `BAC-HISTORY-A-2026-11-01`, exact archived formats/row counts/reward provenance, archive query/export and atomicity evidence, preserved available state/clocks, fresh captured warmup and unchanged current full resume. Archived original rewards remain evidence, never reinterpreted or sampled; all current emitted rewards/optimizer targets satisfy the repaired contracts. Optional roadmap items retain their honest scope and cannot absorb required gaps. Candidate C01 has an explicit API repair/reachability result. K05 is repaired; K01/K02/K04/K06 have the specific qualified/deferred limits above, and K03 preserves/extends the stated interfaces.

After T37–T39 and before the final detached gate, perform a source-verified documentation pass on `README.md`, `docs/architecture/BAC.md`, `docs/config-schemas/brain.md`, `docs/config-schemas/training.md`, `docs/config-schemas/declarations.md` and the BaC support/options/acceptance records. The documentation worker/reviewer reads only `test_joint_learning.py`, `test_joint_restart_serving.py`, `test_joint_outputs.py` and GE: **4 files /1350 projected implementation/test lines**; docs/reports are reference material. Package source reviewers supply exact final source citations in their existing bounded receipts; the documentation pass checks every capability claim against those receipts and executable matrix, asks the owning bounded reviewer to recheck changed claims, and never reads the entire implementation to evade the cap. Coordinator serializes shared-document ownership and records exact final source/evidence SHA. This is a finite consistency pass, not permission to invent new capability claims.

Technical approval starts the already-authorized implementation/verification cycle without a routine further go-ahead. Continue review→gap analysis→repair→review fixes→full-spec review as needed; the stopping condition is the finite ledger and repository/learning qualification above, not an arbitrary round count. Keep P3 in a separate finite report/follow-up set, analogous to VFS's green PR57 followed by separate P3 PR58; do not turn P3 into an unlimited improvement program or let it hide a P1/P2. The precise Option A archive/fresh-buffer reduction is already approved; other capability reductions still require concrete approval; Emmy may surface/recall John and approve scope changes on his behalf as the user has authorized. No routine check-in is required for the additive path.

This planner's output is only this document; the planner has made no production implementation changes. The coordinator may execute independently technically approved additive packages (including separately scoped T01) while this final plan revision is reviewed; that does not approve an unreviewed historical policy or change these bytes. Implementation after exact-hash external technical approval is already authorized; authoritative approval and execution status live in the external review records/ledger. Only the explicit historical-replay Option A approval is applied; no other capability-reduction approval is inferred. Any later merge/publication follows the coordinator-verified recovery grant/PDR-0101, exact remote CI and protection requirements; this plan grants no broader merge or publication authority.
