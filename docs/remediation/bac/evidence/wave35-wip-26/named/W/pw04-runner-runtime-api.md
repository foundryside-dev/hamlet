# PW04 actual runtime API capsule

Read-only source inspection for the observed R152 runner constructor failure. No test execution or implementation claim. Source budget: three implementation/test files, 3,735 lines total. Source identities:

- `src/townlet/config/exploration_policy.py` (1,343): SHA256 `5c5410d8bf6213f42cab3b18925efb164eec4670dd7f8c10b31af305f8a32363`.
- `src/townlet/exploration/scoped_curiosity.py` (1,492): SHA256 `110d640bdb607fd58d6e991dba49da2cc5236f169cc4c1db45627db6b8082f7c`.
- `tests/test_townlet/regressions/bac/test_parent_intrinsic_handoff.py` (900): SHA256 `bbfdc1e8d60a609de6dacf7b68c0d6cb7e014df308dddddde5698ad2bf7fd673`.

## Construction

`build_exploration` at exploration_policy.py:1322 is the current factory; all eight keyword inputs are required:

1. `policy: ResolvedExplorationPolicy` (actual instance, cloned through complete to_dict/from_dict).
2. `descriptor`: actual `WorldCuriosityDescriptor` in BANK's constructor; runtime annotation itself is Any.
3. `device: torch.device | str`.
4. `validate_accepted_episode`: actual `env.validate_accepted_episode`.
5. `issuer_factory(bank)`: returns an issuer whose `owner is bank`.
6. `report_allocation(AllocationEstimate)`: real reporting sink.
7. `validate_committed_batch(*, batch_episode, outcomes) -> None`.
8. `validate_parent_cadence(*, cadence, mode, accepted, parent_restore) -> None`.

The positive test construction at test_parent_intrinsic_handoff.py:180–241 uses:

`WorldCuriosityDescriptor.from_policy(selected_policy, world_ids=declared_ids, observation_dim=selected.token_spec.total_dims, action_dim=selected.action_metadata.total_actions, training_seed=selected.training.seed)`.

The descriptor class definition is outside this supplier's inspected files; this exact factory call is source-verified at its real callsite, not a claim about all accepted constructor variants. Import paths are `townlet.exploration.world_curiosity_state.WorldCuriosityDescriptor`, `townlet.environment.vectorized_env.WorldReceiptIssuer`, and `townlet.config.exploration_policy.build_exploration`.

The factory captures the actual BANK argument in controller-owned state and returns `WorldReceiptIssuer(owner=bank)`. Then build the actual POP with `exploration=runtime`, and complete the closure's POP binding. The two parent callbacks forward all keyword arguments to `population.validate_committed_batch` and `population.validate_parent_cadence`. These are calls to genuine POP methods, not test implementations of validation. POP method bodies were not inspected by this supplier; the runner writer owns that source slice. The closure must not be used until its real POP binding exists, and must never become a permissive/no-op fallback.

BANK validates exact declared IDs, policy/descriptor equality, CPU or explicitly indexed CUDA, float32 profile, and positive observation width for non-none providers (scoped_curiosity.py:281–309). BANK creates its own RNG-domain participant and per-world or shared backends (348–359); its `_factory` delegates selected policy/geometry/device/owned RNG/descriptor to `make_backend` (393–405). Runner must not replace this with a hardcoded Adaptive provider or invent its rng/service-clock arguments.

## Owner registration and episode entry

The source test's local controller binds ENV boundary authority to these actual owners (test_parent_intrinsic_handoff.py:50–69): population=POP; curiosity=BANK; curriculum=POP.curriculum; exploration=runtime; network=POP.q_network; optimizer=POP.optimizer; scheduler=POP when the schedule has no separate live owner, otherwise POP.scheduler; replay=POP.replay_buffer; selection=runtime. Controller itself owns the boundary authority. BANK is the curiosity owner, not the facade.

Its semantically real entry calls (71–91) are: bind roles while fresh; `boundary.bootstrap(first_batch_episode=batch)`; `env.install_boundary_release(release)`; `env.prepare_episode(batch_episode=batch, release=release)`; validate reservation; `pop.bind_episode_worlds(world_ids=declared_ids, world_episode_seqs=reservation.world_episode_seqs)`; `pop.begin_batch_episode(batch, planned_horizon=authored_horizon)`; `record, activation = pop.reset(reservation=reservation, retired_world_ids=...)`; `curiosity = runtime.begin_episode(accepted=record.accepted)`; `env.activate_episode(accepted=record.accepted, population_receipt=activation, curiosity_receipt=curiosity)`.

This is a source-verified local test recipe, NOT an existing production runner controller. Do not copy test IDs, test horizon, `retired_world_ids=()` regardless of actual lifecycle, or fixture effect-issuer logic into production as attestation. The test file expressly states its local boundary driver does not certify T26/native restore. No production controller implementation was inspected here; whether one exists remains for integration-owner inspection.

## Subsequent operations and completion

Actual POP stepping is `pop.step_population(env)` in positive tests (e.g.409). Runtime current surface (exploration_policy.py:962–1011) is `prepare_step_stamp(accepted, world_ids, active_on_entry, vector_tick)`, `reward(context, stamp, accepted, update_stats)`, `admit_and_service(context, stamp, accepted)` with keyword arguments. Do not bypass POP's authenticated claim/clock/learning choreography by calling providers directly. Selection uses runtime-owned epsilon tensors; telemetry synchronizes via `pop.sync_exploration_metrics()`.

BANK completion is separately prepared with accepted identity, boundary key, canonical completion content, actual outcomes and actual participating IDs, then `commit_completion(prepared=...)` returns retirement authority. Global epsilon cadence is separately committed via `runtime.commit_batch_episode(batch_episode=..., outcomes=...)` (1039–1085). It authenticates the real POP callback, rejects mutated callback views, performs exact-content retry deduplication, and applies one global recurrence. The positive POP retry test (test_parent_intrinsic_handoff.py:764–798) proves `pop.commit_episode_outcomes(events)` delegates that runtime commitment and preserves pending custody after injected child failure. Do not also manually decay epsilon in runner.

Fixture completion (94–136) performs real curriculum/BANK/POP effects but then locally creates effect issuers and a controller release. That is explicitly LOCAL TEST CONTROLLER behavior, not proof that the production HC/runner effect witness exists. Production completion must own and authenticate the actual effects, ledger/model/optimizer/scheduler/replay owners, ENV close and successor release; fake/no-op callbacks or fabricated success receipts cannot satisfy runner acceptance.

## Restore constraints and remaining production obligations

Runtime transport is exactly schema/policy/bank/selector/cadence with schema `exploration-runtime-state-v1`; diagnostics are refused, complete receiving policy must match ordinary restore, and BANK policy must agree (exploration_policy.py:1135–1174). `prepare_restore(*, state, mode, accepted, parent_restore, validate_parent_restore)` returns an owned prepared token; `install_restore(*, prepared)` checks authentic handle, runtime/BANK freshness and genuine parent cadence again before BANK publication (1247–1320). The constructor callback validates parent cadence during preparation and install, not merely at build time.

BANK rejects preparation while completion is pending; delegates mode validation to the checkpoint module; re-authenticates live accepted identity or correlates actual parent restore; validates full native records off-side before publication (scoped_curiosity.py:1350–1435). The imported checkpoint mode checker was NOT opened. The current written contract, CURRENT-EXPLORATION-RUNTIME-CONTRACT.md:81–84, specifies initial permits None/None parent pair or genuine initial preparation; live_episode requires actual receiving accepted identity and None/None parent pair; completed_boundary requires genuine retained completed parent preparation/validator; private_initialized requires genuine correlated parent preparation. These exact mode table details are document-supported, not independently reverified inside the imported checker by this bounded supplier.

The inspected positive test at lines877–900 establishes a material production ordering constraint: prepare an initial POP restore while fresh, then bind roles before installation, and install must refuse before runtime publication. Restore cannot replace registered owner identities behind an existing ENV authority. Runtime exposes `retain_parent_custody()` (exploration_policy.py:872); parent must honor its real custody/quiescence contract, not fake a lease.

The constructor fix alone does not establish a runnable production lifecycle. Runner needs genuine fresh/boundary/restore controller orchestration and the authored checkpoint/restore/continued-learning witness, with actual artifacts and learner updates. This supplier neither implements nor certifies those missing responsibilities. Older contract prose at line67 says tests use cooperative callbacks rather than actual POP cadence implementation; the inspected newer test construction forwards to actual POP validators. Use current source callsites for that distinction, while retaining the explicit limitation on the local test controller.

### Policy projection and allocation callback clarification

The actual resolver signature is `resolve_exploration_policy(drive_intrinsic: IntrinsicStrategyConfig, training: TrainingV2Config, options: BaCOptions) -> ResolvedExplorationPolicy` (exploration_policy.py:432), not a single effective-run argument. The selected test call at line177 uses selected level drive/training/options; it deliberately changes strategy/scope for parameterized tests. Production must retain actual selected authoring. This supplier has not inspected EffectiveRun's definition and makes no claim that an `effective_run.exploration_policy` field exists.

The allocation callback receives one positional `AllocationEstimate` and returns None. Positive tests retain estimates with `reports.append`; a genuine production logging/recording sink can satisfy this contract. BANK reports its construction allocation before backend creation (340–341), and snapshot/restore/initialization reports include owned input, candidate workspace and retained parent callback views (1136–1165). Runtime additionally reports parent commitment/preparation allocations (1020–1032). These are estimates with stated assumptions and unknowns, not measured allocator peaks. Do not drop unknown-components metadata or call back into runtime from the reporting sink.

## Production curriculum completion supplement

Authorized additional source inventory: `src/townlet/curriculum/static.py`, 64 lines, SHA256 `22ff977b07fa494a1f6b403b312af2c5f6e22780af472e6c132832213782cc59`; `src/townlet/curriculum/adversarial.py`, 537 lines, SHA256 `2194cc4075096670181a50cf1be2158cd68334a07111818ad75382cd73890f4f`. Total supplier inventory now five files / 4,336 lines; no further source bodies opened. Everything in this supplement is verified directly in those files unless expressly limited.

Both StaticCurriculum and AdversarialCurriculum inherit CompletionCurriculum's actual production protocol:

- `initialize_population(num_agents: int) -> None` (adversarial.py:106) is separate from construction and requires a positive exact integer. Constructor leaves `num_agents=0`; completion, decisions and checkpoint methods require initialization. Initialization creates current version2 state, generation0, fresh lanes, empty event history/metrics, a new owner token and empty telemetry. It is valid once for a fresh constructed receiver before loading saved state. It is NOT harmless repeated setup: repeating it discards current learning/history and invalidates all prior prepared tokens.
- `prepare_episode_outcomes(outcomes: Sequence[LaneOutcome]) -> PreparedCurriculumOutcomes` (131) freezes each outcome, validates lane range, rejects changed-content reuse of `(batch_episode, agent_idx)`, and checks new lane completions preserve world_id and strictly advance world_episode_seq and batch_episode. It returns owner_token/current generation/frozen outcomes. Inspection shows no assignment to live curriculum state or telemetry; local known/latest dictionaries and frozen readings hold preflight work. The imported freezing implementation was not opened in this inventory.
- `commit_prepared_episode_outcomes(prepared) -> None` (158) checks actual preparation type, identical owner token, nonnegative generation/not future, converts and re-prepares canonical content. If ALL supplied identities/fingerprints are already present it returns without mutation, including an empty batch or an equal retry from an older generation. Otherwise stale generation is refused. It deep-copies state and telemetry, applies only previously unseen events to the candidate, increments generation once, then publishes `_state, transition_events = candidate, transitions` (209). Thus repeated equal outcomes do not duplicate lane clocks or curriculum transitions. A partially new stale preparation must be freshly prepared; do not force through a mismatch.

No completion method returns a `WorldOwnerReceipt`, nor is the prepared object an ENV effect receipt. Source evidence after successful commit is `checkpoint_state()` (211), an independent deepcopy with exact outer keys version/strategy/completion; completion contains config/generation/lanes/events/metrics. Events retain identity+fingerprint; metrics retain the latest canonical actual event and previous survival fraction. `transition_events` is separate telemetry; static has no transition event but still records dwell, episodes and completion identity/history. A production controller must tie its effect witness to a successful authentic curriculum commit and the actual completion content; it must not mistake a test issuer or nonempty telemetry for proof.

`validate_checkpoint_state(state) -> None` (216–351) is genuine non-mutating preflight of exact schema/config/population, monotone identity history/fingerprints, latest metrics and reachable lane effects. Its first-completion check advances a freshly created local lane dictionary, not live state. `load_state(state) -> None` (353) deep-copies caller state, invokes validation, then publishes owned state/new owner token/empty transition telemetry. It therefore invalidates prior prepared receipts and must be called within the production parent restore transaction. The standalone API supplies no separate prepared curriculum-restore handle; do not claim its validation call alone proves an atomic multi-owner runner restore.

Relation to existing runtime sequence: prepare real curriculum outcomes before mutation; actual BANK preparation/freeze and ENV boundary rules remain independent. Successful curriculum commit does not commit BANK retirement, POP outcomes or global epsilon cadence. Conversely runtime commit_completion does not commit curriculum. POP's actual commit_episode_outcomes delegates the authenticated global epsilon recurrence, as documented above. Runner's controller must retain/retry each actual effect and authenticate its boundary release. The fixture's ordering (prepare curriculum/BANK/ENV, freeze ENV, commit curriculum, commit BANK, commit POP, sync epsilon telemetry, close/release) is source-verified as a local component test only; it does not prove the production runner controller or native checkpoint attestation exists.

## Snapshot, telemetry and completion callsite clarification

BANK's shared provider native payload is exactly `runtime.checkpoint_state()['bank']['shared_backend']['native']` (scoped_curiosity.py:1074–1080). Private native payload is the matching world record's `['backend']['backend']` under `['bank']['worlds']` (1083–1098,1218–1223). Provider-native RND/config schema definitions are outside this inventory and are not certified here. Public `runtime.snapshot_world(world_id=exact_id)` returns shared native under `['backend']`, private native under `['backend']['backend']` (942–1001). These observations copy owned state and advance mutation revision; they are not cheap harmless telemetry and must not be interposed into prepared restore/completion custody.

There is no public current-weight getter on the inspected Runtime/BANK surface. Actual transition reward exposes a cloned per-row `CuriosityReward.scales` tensor: none=0, adaptive=current backend intrinsic weight, other selected providers=policy initial weight (630–641). Preserve actual world/lane identity when reporting scales; no implied per-world mean is defined. A new cheap current-weight observation would require an explicit API change, rather than access to private provider fields or pretending a checkpoint snapshot is inert.

Current static/adversarial curriculum has no `tracker` attribute. `get_stage_info(agent_idx)` provides committed `current_stage`, `steps_at_stage`, `episodes_at_stage` and metrics; `get_batch_decisions(None, ids)` gives actual decisions. Old tracker updates cannot substitute for real completion, and additional old updates must not duplicate effects already committed by current completion.

BANK completion requires nonempty actual participants in accepted-world order. `tuple(event.world_id for event in outcomes)` must equal that ordered participant tuple, and every outcome's sequence/batch/lane index must match accepted identity (760–786). Same pending exact preparation returns its token; same committed token returns its same actual retirement receipt (869–875). No separate public cheap closure assertion exists. Snapshot `bank_phase='completed_boundary'` and saved completion metadata are observations, not transported authority. Empty episodes use their separate authenticated evidence/quarantine protocol. Curriculum completion event entries are exactly `{'identity': (batch_episode, agent_idx), 'fingerprint': frozen.fingerprint}` (207); neither these retained records nor its None commit return are ENV owner receipts.

## Complete INITIAL real-owner construction recipe

Source: test_parent_intrinsic_handoff.py:145–241. This supplies complete constructor arguments for a standalone INITIAL real-owner test; it does not attest production runner completion. The `compiled` fixture and L0 `policy` helper are imported from `tests.test_townlet.regressions.bac.test_pw_scope_conversion` (lines13–14). Their bodies/compiler invocation were not opened, so compiler arguments are not established by this capsule.

1. Set CPU device. Obtain `selected = compiled.get_level(compiled.metadata.primary_level)` and `effective = compiled.effective_run`. The source uses eight declared IDs `parent-A` through `parent-H` and asserts effective training population size is eight.
2. Call `compiled.create_environment(num_agents=len(IDS), level_name=compiled.metadata.primary_level, device=device, world_roster=WorldRosterDeclaration.from_dict({'schema': 'world-roster-v1', 'world_ids': list(IDS)}), training_seed=selected.training.seed, lane_world_ids=IDS)`.
3. Call `build_curriculum(effective.training, curriculum_options=effective.options.curriculum, static_policy=effective.static_policy, device=device)`, then `curriculum.initialize_population(len(IDS))` once on this fresh owner.
4. Select an actual resolved policy. Source L0 path calls imported `policy(compiled, family, scope, 'paced_fifo')`. Its non-L0 path resolves selected training BAC options into a dict, explicitly authors `curiosity_scope={scope: scope, seed_policy: legacy_shared_v1 for shared or world_id_derived_v1 for per_world}`, sets `rnd.service_mode='paced_fifo'`, copies selected drive intrinsic and sets strategy=family, then calls `resolve_exploration_policy(IntrinsicStrategyConfig.model_validate(drive), selected.training, BaCOptions.model_validate(options))`. These deliberate test variants must not be misrepresented as unchanged authoring. A supplied actual selected_policy bypasses that test selection.
5. Build descriptor and runtime using the exact eight inputs already documented above. Retain actual BANK from issuer_factory. The runtime callbacks close over a holder which is populated with the actual POP immediately after construction; they forward to POP's genuine validation methods, never return unconditional success.
6. Resolve `resolved = resolve_bac_options(selected.training.bac_options, training=selected.training)` and construct the actual POP with ALL these arguments:

```python
VectorizedPopulation.for_training(
    env=env,
    curriculum=curriculum,
    exploration=runtime,
    agent_ids=list(IDS),
    device=device,
    brain_config=apply_training_overrides(compiled.brain, selected.training),
    obs_dim=selected.token_spec.total_dims,
    train_frequency=1,
    batch_size=2,
    sequence_length=8,
    max_grad_norm=10.0,
    action_dim=selected.action_metadata.total_actions,
    tb_logger=None,
    max_episodes=2,
    max_steps_per_episode=20,
    replay_options=resolved.options.replay,
    min_transitions=2,
    replay_rng=np.random.Generator(np.random.PCG64(selected.training.seed)),
    replay_origin='authored',
    beta_vector_tick_horizon=40,
    beta_horizon_origin='explicit test episodes2 * declared test horizon20; vector ticks',
    current_vector_tick=0,
)
```

7. Immediately bind the holder's population to that real POP. The `validate_committed_batch` closure forwards batch_episode/outcomes, and `validate_parent_cadence` forwards cadence/mode/accepted/parent_restore to that POP. ENV callback is its actual validate_accepted_episode; issuer is WorldReceiptIssuer with owner=actual BANK; reports.append retains real allocation estimates.

The numerical replay/training values above are exactly the source fixture's declared test configuration, not universal production defaults. No controller bind/bootstrap/reservation/reset is performed for a fresh INITIAL target; doing so changes lifecycle preconditions. Production imports needed beyond those listed above: `townlet.config.bac_options.resolve_bac_options`, `townlet.config.brain_config.apply_training_overrides`, `townlet.config.drive_as_code.IntrinsicStrategyConfig`, `townlet.config.world_roster.WorldRosterDeclaration`, `townlet.curriculum.factory.build_curriculum`, and `townlet.population.vectorized.VectorizedPopulation`.
