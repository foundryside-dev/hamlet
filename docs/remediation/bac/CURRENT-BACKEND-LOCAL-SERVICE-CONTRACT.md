# Current backend-local service contract

Implemented and qualified bounded producer contract for actual RND, ICM and adaptive RND. This is not integrated PW04/BAC release. Actual external caller, bank/context, POP and ordinary-runner/native qualification remains required below. Source basis is the frozen four-file candidate; no new source inspection or runtime accompanied this contract publication.

## Qualified source and evidence

| File | Whole lines | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/rnd.py | 834 | 0848cfe8f08635fac6843d90bdf38ca7c08f92ef8220d7859e2ce65dae4ecf0d |
| src/townlet/exploration/icm.py | 481 | eb7003c15404fea5e3ce8d5779f88235b96b622b853a1c11731a300d3059c90f |
| src/townlet/exploration/adaptive_intrinsic.py | 315 | cb64d78d01c0bb8422dc664206e65588eba373a0a7ed8408634a7fa0a4b80df4 |
| tests/test_townlet/regressions/bac/test_pw_local_service.py | 1412 | 3dcc780c36c15b553272246ac605f9ca6a89cbd732f0142552fd1ee0df4f9dc7 |

Actual4/3042; named ceilings1000/750/500/1800 total4050, hard5/5000. No fifth helper/source is implicit.

Root reports fixed R3 full262 PASS/0 warnings in28.4517s; covering57 PASS in10.641s; separately verified ICM prerequisite4 PASS in4.8203s. Root custody passed193 source/573 config/13 artifacts/3 processes. Same-Sol actual-source fix review reports specification/quality PASS and independently executed full262 PASS in20.9136s with custody PASS. These overlapping selections are separate evidence, not an additive synthetic count.

Root also reports CLI PASS in174.9711s; Ruff, Black (98.022s), defaults601 and expression guards PASS. Global mypy retains9 external oracle/POP errors and zero owned diagnostics: global mypy is not PASS. Root/reviewer jobs are closed. The source material findings—over-capacity admission, raw Adam coercion, state-ID aliases—and ICM copy prerequisite are closed by the fixed-source tests/review. No CUDA or integrated runner result is inferred.

## Required construction and real RNG hooks

Each constructor requires keyword-only `rng: WorldRNGState | None` and `service_clock_unit: Literal['vector_tick', 'world_eligible_admission']`. Neither has a default. Shared callers explicitly supply `rng=None, service_clock_unit='vector_tick'`. Private factory supplies its actual candidate RNG and `service_clock_unit='world_eligible_admission'`. Adaptive forwards both inputs to its actual nested RND. `service_clock_unit` is read-only and cannot change through a call or native import. RNG ownership and clock selection are distinct explicit inputs.

The actual network allocations retain their algorithms and order:

| Provider | Allocation domains | Used provider-draw streams | Unused provider-draw streams |
| --- | --- | --- | --- |
| RND | fixed network under target, then predictor under predictor | target, predictor | model_init, service |
| Adaptive | delegates identical RNG/unit to real RND; outer setup draws nothing | target, predictor | model_init, service |
| ICM | encoder then inverse under model_init, forward under predictor | model_init, predictor | target, service |

Explicit shared None preserves ambient constructor draw order through null contexts. No reinitialization, copied learning engine or global Torch monkeypatch is used. Providers do not retain RNG owners or duplicate RNG state in their native payloads. OwnedWorldBackend.construct supplies its cloned candidate RNG under model_init; same-owner nested component activation is supported. OwnedWorldBackend.call still uses its service domain even though these present provider operations have no stochastic draws. Late live failures remain subject to that owner's quarantine semantics.

Factory callback: `lambda candidate_rng: Provider(..., rng=candidate_rng, service_clock_unit='world_eligible_admission')`, with selected resolved configuration and RND service configuration before publication. Mandatory complete validation callback: `lambda candidate, payload: candidate.validate_state(payload)`. ICM deepcopy transports frozen policy through `type(policy).from_dict(policy.to_dict())` and a shared deepcopy memo, preserving model/Adam pairing without random reconstruction; native preparation supplies its already validated policy through that memo.

## Service, batching and preflight

RND/adaptive provide `admit_and_service_at(observations, *, clock: ServiceClock) -> PredictorServiceReceipt`; ICM provides `admit_and_service_at(context: IntrinsicTransitionContext, *, clock: ServiceClock) -> ExplorationServiceReceipt`. Adaptive also exposes `configure_service(options)` and `predictor_service_counters()` delegation. Exact ServiceClock type/unit/nonnegative integer position and whole-call input validity are checked before service mutation or callbacks.

Private position starts at0 and denotes cumulative own eligible admissions. Require requested position = previous position + actual eligible row count, including explicitly dropped admissions. RND receives caller-selected eligible predecessor rows; ICM selects active actual predecessor/action/successor rows in original order. Global/context vector ticks confer no private opportunities. Episode reset does not rebase the cumulative position.

A private n-row call executes n consecutive single-row events with one ordinary budget opportunity at each new position. Unused budget expires rather than accumulating. Grouping/splitting the same ordered admissions yields the same consumed batches/losses, model/Adam state, tail, counters and final clock/budget. RND preserves drain-before-append order; ICM preserves pre-append overflow handling then append/drain. A same-position empty/all-inactive call returns zero deltas without service or state change. Nonempty same-position input, empty advance, gap, regression and unit mismatch refuse. Provider position checking does not authenticate events or implement bank retry/dedup.

Shared methods remain current substantive operations: RND/adaptive `admit_and_service(observations, *, vector_tick)` and ICM `admit_and_service(context)`. They require vector_tick selection; ICM explicit clock position must match context.vector_tick. Grouped batching is preserved. Equal ticks share ordinary budget; a newer tick resets it and can service complete queued work even on an empty call. Mandatory service_before_admit overflow is separately counted; drop_oldest/newest explicitly count discarded rows.

All service modes preserve admitted = consumed + dropped + pending and consumed = successful service optimizer updates × training_batch_size when operating from valid provider state. RND/adaptive bounded admission explicitly refuses an existing public obs_buffer above the selected capacity before service, counter or clock mutation; public direct update_predictor and lawful unconfigured tails retain their separate direct-training behavior. ICM’s empty initial queue and complete native pending-state validation establish occupancy<=max_pending_transitions, and its per-row handling at full capacity preserves that bound during supported shared/private admission. Oversized ICM native pending payloads refuse before live installation; ICM does not separately preflight an already over-capacity internal _pending queue for arbitrary direct internal mutation. The B2/capacity4/cap1 private RND/adaptive geometry has zero overflow by its per-admission drain order; real shared same-tick overflow and imported-full-tail private ICM overflow are separately qualified, not conflated.

RND/adaptive shared direct update and RND public update_predictor retain genuine one-minibatch learning and leftover tails; private unclocked/direct calls refuse. Full external-buffer row validation precedes admission reconciliation, including incomplete buffers and late rows beyond the next minibatch. Configured shared update assigns its prospective step_counter only after successful service. Public direct update_predictor and unconfigured tails are not removed or newly subjected to bounded-admission capacity. Reward input validation precedes model/RMS effects; empty RND reward does not change RMS. ICM context construction already rejects nonfinite observations; its separate context-boundary evidence is not misreported as provider validation.

## Exact current native formats

All three providers expose `checkpoint_state()`, `validate_state(state)`, `prepare_state(state)`, `install_state(prepared)` and `load_state(state)`. Exact current key sets/versions are required; unknown, missing and obsolete fields refuse without adaptation.

RND schema `rnd-state-v2`, exact top keys:

`schema, fixed_network, predictor_network, optimizer, epsilon, epsilon_min, epsilon_decay, obs_dim, embed_dim, reward_rms_mean, reward_rms_var, reward_rms_count, predictor_service`

RND predictor_service exact keys:

`version, training_batch_size, options, pending_observations, admitted_rows, consumed_rows, dropped_rows, optimizer_updates, optimizer_step_offset, service_clock_unit, service_position, ordinary_updates_at_position, step_counter`

Version is exact int2. Options match selected resolved configuration; None is lawful only for unconfigured shared direct training. Ordered pending rows obey native geometry/dtype/finiteness/capacity. Adam step equals optimizer_updates+signed optimizer_step_offset with nonnegative resulting step. Epsilon lies within its validated bounds/floor; RMS mean is finite, variance>=0 and count>0. RND `available_state()` is an owned diagnostic subset only; native validate/load do not accept it. Historical load_available_state/missing-service restore dispatch is removed.

ICM schema `icm-state-v2`, exact top keys:

`schema, policy, policy_identity, config, encoder, inverse_model, forward_model, optimizer, epsilon, epsilon_decay, epsilon_min, pending, counters, last_loss, service_clock_unit, service_position, ordinary_updates_at_position`

ICM config keys:

`obs_dim, action_dim, feature_dim, hidden_dim, learning_rate, inverse_weight, forward_weight, training_batch_size, max_pending_transitions, device`

ICM counter keys:

`admitted_rows, consumed_rows, dropped_rows, optimizer_updates, mandatory_service_updates`

Current complete policy/identity and selected configuration match destination. Pending is an ordered owned list of predecessor/action/successor rows, including action bounds and finite float32 observations. Source device provenance is CPU/CUDA; tensors prepare for the receiving device. Mandatory updates<=total; ordinary budget<=total-minus-mandatory and the selected paced cap. Loss is finite nonnegative and zero before any update. Epsilon matches the selected schedule. No old service_tick/ordinary_updates_this_tick native aliases remain.

Adaptive schema `adaptive-intrinsic-state-v2`, exact keys:

`schema, rnd_state, initial_intrinsic_weight, current_intrinsic_weight, min_intrinsic_weight, variance_threshold, min_survival_fraction, max_episode_length, min_survival_for_annealing, survival_window, decay_rate, survival_history`

rnd_state is complete current rnd-state-v2. Outer selected configuration, bounded finite weight, exact derived threshold and finite nonnegative bounded-window history validate before nested preparation. History must be representable for float32 variance/mean computation; nonfinite derived values refuse before completion mutation. The original variance estimator, strict thresholds and minimum ten observations are preserved. Weight is not reconstructed from truncated history. History snapshots/restores do not alias live lists.

Saved unit must equal the explicitly selected destination unit. Private service_position equals admitted_rows for ordinary origin0 continuation; unstarted private state has no recorded work/tail/used budget. Private RND requires configured options and step_counter0. Shared position is None before bounded service or an exact nonnegative int; None requires ordinary budget0 while valid shared direct-training counters/tails may exist. Ordinary resume preserves these values. Explicit clone/evaluation-origin rebasing remains a separate owner transaction; this producer adds no converter or false-origin import.

## Validation, installation and algorithm preservation

Snapshots and prepared inputs own tensor/container storage. Model geometry/dtype, complete dense Adam coverage, exact integer state IDs, common scalar steps, groups, counters, clocks and normalization/history semantics are checked off-side. Raw Adam moment dtype/geometry/finiteness/nonnegative squared moments validate before any loader can cast them; bool/integral-float state-ID aliases refuse. RND also checks loaded optimizer state and a disposable execution probe's state/parameters for finiteness. Supported actual RND LR/settings/offset are retained; ICM retains its selected-policy optimizer settings.

validate_state prepares/discards without live mutation or RNG draws. prepare_state creates a fully owned candidate with correct model/Adam references. Adaptive outer validation precedes loading only an off-side nested RND. install_state checks destination identity and nonconsumption before a prepared attribute-dictionary swap; no fallible provider load or remaining validation follows the first destination assignment. Candidates are single-install and require quiescent custody. This is not rollback against asynchronous interruption or late numerical failure during live learning.

OwnedWorldBackend additionally binds prepared restore tokens to live revision: snapshot/call after preparation invalidates the token. The qualified fixture observes purity, verifies stale-token refusal, then prepares again and installs without intervening owner observation. It retains positive full-state/RNG/next-real-update comparisons. No WS guard was weakened.

RND retains the fixed frozen target, trainable predictor, real Adam and RMS-normalized unweighted novelty. ICM retains actual encoder/inverse/forward models, weighted inverse/forward objective and detached successor target for forward loss. Adaptive retains RND composition and survival-based weight annealing. Shared and private learning use positive learning rates in qualification. No scheduler, clipping controller or new loss-scaling algorithm is claimed. CPU/static results do not establish CUDA or cross-device bitwise equivalence.

## Required external integration

Known gaps here are attributed to root/producer prose, not new external source inspection. External old owner fixtures and callers still require explicit rng/unit transport; obsolete signatures are not supported by a hidden default. Global mypy has9 external oracle/POP errors with owned code clean. Current parent dispatch and strict native key sets must consume the exact formats above, including actual ICM rather than epsilon-only inheritance recognition.

Actual POP/parent must validate and prepare all provider/bank/RNG/identity and Q/replay/counter/lifecycle candidates before any installation, then commit the prepared provider without a second late live load. Actual bank/context stamp routing, ENV accepted identity, cumulative/episode-local cursors, phase/dedup/retry and adaptive completion custody remain separate required integrations. The existing owned-world-backend-v1 envelope continues to own backend plus RNG; provider native state does not replace it.

Required test_shared_runner_checkpoint_still_roundtrips belongs to the actual integration owner: current ordinary runner.run, actual native artifact/digest, receiving load, saved tail/order/Adam/LR/clock continuation and a next genuine optimizer update; deep malformed provider plus changed candidate parent Q/counters must refuse with full live parent equality. No backend fixture, stub/skip, prior-source result or bounded producer PASS closes this gate. Required current shared-owner fixtures/callers, coherent full gates and final BAC acceptance remain open. Original66 packets/28 releases are unchanged.


Root existing-owner integration receipt: five frozen existing test files collected151 cases successfully (3.2346s); one representative from each then failed at the old constructor call, missing new required rng/service_clock_unit (fivecall-phase TypeErrors in4.0824s).196-source/573-config/13-artifact/process custody PASS; no old assertions were reached or relabeled passing. Bounded five-file current API/native-fixture migration is next. Backend source qualification and these required owner/whole-system obligations remain distinct. No constructor defaults or compatibility adapter were restored.


Current owner-fixture follow-up at tested tree 4c0cec9a4cd8893910a0abb64c396eb7011f5787: all151 original cases remain in source.76 shared constructor sites now pass explicit None/vector_tick; current native corruption keys and complete matching adaptive snapshots replace superseded partial-import expectations, preserving real next-update/LR/FIFO/RMS/gradient evidence. One greedy fixture explicitly supplies epsilon_min0 with epsilon_start0. The real basic_env fixture declares a stable test-owned world ID and forwards the actual selected level training.seed and identical lane tuple;18 checkpoint consumers only read observation_dim, so no activation/role permission was invented. Root19 prerequisitesPASS10.8583 and freshSol19PASS8.1718; source/spec/qualityAPPROVE.

Focused component execution:412PASS26.2254s with exactly the unchanged required real runner node test_native_runner_checkpoint_retains_tail_and_rejects_corruption explicitly deselected; independentAstra150PASS69.9772s with the same one required deselection, no skips/xfails. The runner case is still REQUIRED OPEN and prevented full151/413 qualification. It was neither removed nor marked skip; it must run after actual runtime/bank/native-parent prerequisites are repaired. These overlapping selections are not summed. All196source/573config/13artifact/process/import/thread/index custodyPASS. Four W21global guardsPASS(Black53.7073/defaults601 unchanged); globalmypy9requirederrors remainsFAIL. BackendR3CLI174.9711 is reused only because src/config/scripts are byte-identical; no W21CLIrerun is claimed. Other global environment fixture constructor/lifecycle sites remain their existing required caller work. No wholePW04/BAC release follows from this fixture handoff.
