# Per-World Curiosity Design and Execution Addendum

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans for the approved packets. Checkboxes are tracked externally; frozen review artifacts are not progress files.

**Goal:** Resolve X02 by delivering genuinely private, trainable curiosity per stable world while preserving the shared alternative, existing defaults and all 48 base work-package goals.

**Architecture:** Reuse the five existing/planned curiosity backends as private instances in a world-ID registry. Keep the Q learner/action policy shared, and route actual reward, local predictor service, completion, state load and diagnostics through explicit scope contracts. Scope metadata and strong current-source proofs distinguish conditional simulator/private-reward isolation from permitted shared-Q/controller feedback.

**Tech Stack:** Existing Python/Pydantic/PyTorch/NumPy runtime and pytest; no dependency addition or new training architecture is required.

**Authority:** John explicitly chose B in question `call_b2b0e27039af4602b5a1c19bb3a3fc5c`; approval `BAC-S1-PER-WORLD-B-2026-11-01`, for reviewed decision `docs/remediation/bac/SHARED-NOVELTY-ISOLATION-DECISION.md` SHA256 `cb23ae28696259123b2b16b27e0f29b8d6740900b51bad56f387765c6877e701`. The earlier clarification request selected no option; this later explicit answer does. The decision's old pending status does not erase this separately recorded owner answer. Owner chose the isolation direction, not the specific implementation layout; instance banking below is the planner's technical proposal.

**Frozen references:** v3 SHA256 `2dde2d80d3d14c510878c26af1f99c42217be12d3cb3a554647bc68646feedc1`; cadence/PF-06 addendum SHA256 `2b73403fcd9d139e46009c2f49add6dbe6f99310ce37018ffcf839230845d370`. Those bytes remain unchanged. `per-world-curiosity-packets.json` contains the exact proposed DAG/context overlays. This addendum is PROPOSED until same-Astra MEDIUM exact-hash technical approval; it is no implementation or X02 closure receipt.

## Binding boundaries and approach

- Existing documents with omitted curiosity scope retain **shared** behavior. Add explicit `bac_options.curiosity.scope: shared | per_world`; required strict fixtures choose `per_world` explicitly. Neither the old default nor shared capability is replaced. Shared mode truthfully declares coupled intrinsic/total reward; it is not advertised as passing strict S1 reward isolation. Root has clarified that there is no new universal all-supported-runs/default-strict claim. Any contrary universal product wording must be surfaced and reconciled with that owner ruling, not silently interpreted as permission to switch defaults or select A.
- Strict mode means: with the same local initialization, same device/execution profile and unchanged world's complete explicit action/mechanics/local-experience/reset traces, another world's activity cannot change its raw novelty, normalization, effective intrinsic or canonical total reward, including across real curiosity optimizer updates. Shared Q/target/optimizer and action policy remain allowed. This is not independence of fully closed-loop learned policies.
- Every mutable curiosity dependency is private: RND/ICM learned parameters, encoder/inverse/forward weights, gradients, optimizer moments/steps, any scheduler, RMS statistics, counts/LRU, adaptive history/weight, pending data, RNG, phase deduplication and admission/service/update/drop clocks. Per-world normalizers alone do not satisfy this. First implementation copies even fixed targets; identical immutable constants may only be physically shared later with a proved mutation/load barrier.
- Loss means, clipping and minibatches cover only that world's rows/parameters. There is no global active-count denominator, shared optimizer, shared FIFO, shared service/drop quota, or idle-vector-tick pacing of private work. All backends actually train where applicable; frozen models are not an isolation proof.
- Backend algorithms remain RND/adaptive RND/count/ICM/none as specified by v3. This work adds ownership/adapters, not duplicate algorithm implementations. The alternative of a leading-world tensor parameter bank is viable but requires more optimizer/RNG/gradient-reduction machinery; private instances give clearer ownership and reuse at finite cost.
- Memory is O(number of worlds) for private learned models/optimizer/history. Estimate before allocation and report scope/bytes; do not silently fall back to shared, cap population, drop state or skip updates to fit. Preserve shared-mode resource behavior. Use eager declared-world construction at a quiescent runtime boundary for the first implementation; dynamic world addition is not required by existing synchronous fixed-population support.
- Both worker and fresh other-model reviewer have at most5 implementation/test SOURCE files/5000 projected lines, including helpers/probes. Counts below are complete read context, not modification-only lists. Native data/YAML/reports are reference material; executable helpers count. No sixth implementation file was opened by this planner: cumulative five/4638 charged lines remain.

## X02 evidence and finite closure

Coordinator artifact `qualification/isolation/shared-novelty-differential.json` records original source4aa5363b: equal initial Q/RND/observations, actions[0,0] versus[1,0], no Q or predictor optimizer updates, active normalization. World1 observation/done/extrinsic/shaping match, but intrinsic is1.7587649822235107 versus1.7606741189956665, so canonical total differs. This proves current coupling before predictor training. It does not prove all hidden simulator state, future timesteps or complete RNG isolation. X02 is additional to D01–D21/G01–G09/X01 and remains OPEN until the required real-update/lifecycle/controller evidence and final review pass.

## 1. Scope, identity and seeds

PW01 adds `CuriosityScopeOptions(scope, seed_policy)` under BaCOptions. Omission resolves to `shared` plus recorded legacy shared-seed semantics. Explicit `per_world` resolves to `world_id_derived_v1`; every choice/origin/unit/guarantee is serialized and included in effective curiosity identity. Existing shared numerics/defaults remain unchanged. Compiler/cache roundtrip must retain the whole typed policy; if an existing serializer drops it, repair that original bounded owner before releasing this producer.

`WorldId` uses the existing exact population agent_id string (one agent per S1 world), unique/nonempty in strict mode. It is not lane position, population size, global tick or a global process cache key. Preserve case/Unicode and accepted shared APIs. A bank instance owns its own mapping; equal IDs in another run/bank never alias mutable state. `world_binding_hash` records ID-to-world/row binding separately from static compiled policy identity.

`WorldCuriosityDescriptor` records scope, schema version1, provider kind/active-parameter hash, observation/action geometry, ordered runtime world IDs plus canonical ID-keyed storage, seed policy, clock units, origin and guarantee. Shared old payloads missing scope are explicitly inferred shared; no missing tag means private. Existing identity recipes for supported historical formats remain; ordinary same-scope resume checks them, and explicit scope conversion permits only its declared ownership-derived differences. New selected scope changes behavioral identity. No wall-clock/output-directory/run UUID or whole-population hash enters private seed derivation.

KDF: hash a versioned canonical record of training base seed, exact WorldId, provider kind and stream/component name into each local seed. Do not use row index, N, active count, admission order, current Q parameters or global step. Separate model-init/target/predictor/service streams are named and persisted. Adding/reordering a spectator ID cannot change another world's seed or effective local defaults. Strict derived queue capacity uses local world cardinality1 (for example max(2,predictor_batch_size)), not global N; authored capacities remain explicit per-world quantities in this scope.

## 2. Private state, RNG and service contract

`world_curiosity_state.py` defines:

- `ServiceClock(unit: Literal['vector_tick','world_eligible_admission'], position: int)`.
- `CuriosityEventId(curiosity_epoch: int, world_id: str, world_episode_seq: int, eligible_seq: int)` and an immutable `CuriosityStepStamp` for all rows in one accepted transition context. The stamp has immutable IDs/world IDs of length N, episode and eligible-sequence integer tensors[N], and actual eligible bool[N]; raw/scales are finite tensors[N], with transition observations[N,D] and actions[N]. All shape/ID/order/content validation precedes mutation. Each phase accepts only its next event, replays its bounded last equal-content receipt without mutation, and refuses expired, changed-content or out-of-order IDs. Fresh construction uses epoch0; explicit conversion/evaluation cloning uses source epoch+1, clears active last-event caches and starts local eligible/service counts at0 while retaining the actual restored world episode identity. Inherited learned/history counters remain labeled template data, never active inherited dedup IDs. Ordinary reset advances only the episode identity/local episode cursor, not curiosity epoch or learned state; ordinary full resume restores all cursors/epoch unchanged. PW01/PW02 receipts publish these exact stamp/cursor initialization rules.
- `WorldCursor` with last reward/service/completion IDs, local eligible admissions, consumed minibatches, successful updates and drops; bounded last-phase receipt caches/checksums prevent an immediate duplicate event advancing state twice. Expired older IDs and an ID with changed content diagnose before mutation; no unbounded event-history cache is required.
- `WorldRNGState`: private torch CPU/CUDA states for used devices, private NumPy Generator/Python Random state, and versioned seeds. Model initialization and provider calls execute in the private RNG domain; global streams are restored on normal/error exit. Private operations use one serialized runtime owner, with a scoped RNG lock and no concurrent shared-policy operation inside the RNG domain. Serving uses the already required process boundary. This preserves actual learning, not frozen updates. Future parallelization must prove the same ownership contract.

`provider_factory.py::make_backend(policy, *, world_id: str|None, obs_dim: int, action_dim: int, device) -> CuriosityBackend` constructs the existing five classes, no algorithm copies. It also constructs the existing epsilon policy selector. Shared scope keeps current mixed batching/cadence; private scope creates disjoint mutable instances under local seeds. Global action-policy epsilon still advances once per committed batch episode as v3 requires; its policy RNG/clock is separate from curiosity state. Legacy epsilon fields inside private backend objects cannot become a reward-coupling channel.

`scoped_curiosity.py::CuriosityBank` provides `prepare_step_stamp(...)`, `reward(context, *, update_stats: bool) -> CuriosityReward`, `admit_and_service(context) -> tuple[WorldServiceReceipt,...]`, `begin_episode(world_id, episode_seq)`, `complete(outcome)`, `snapshot_world(world_id)` and prepared-state installation. `CuriosityReward` has `raw[N]`, `scales[N]`, active membership and immutable event IDs. Shared mode returns its declared shared result; per_world routes each actual row by ID and scatters back. Full-batch identity/shape/finite/clock validation happens before any backend mutation. No row-position or lane0 authority is substituted.

Add `admit_and_service_at(..., clock: ServiceClock)` adapters to RND/ICM and adaptive delegation; the old vector_tick method remains the shared-compatible adapter. Private service uses its own admitted-transition cursor. Backend FIFO, paced budget and overflow policy are applied per world; loss normalization and any clipping are per-world only. Complete minibatches actually call the backend optimizer, incomplete tails remain local, and extra idle/global ticks create no service opportunities. Aggregate metrics never feed back into these budgets. None has no predictor, count-based updates its own counts/LRU, and trainable providers must demonstrate nonzero parameter changes.

Reward phase remains eligible post-physics/successor observations for existing observation providers, actual(s,a,s') for ICM; RND predictor ingestion remains eligible predecessor rows. ENV prepares/stamps context before physics and carries that same stamp through its committed successor/reward and info to POP service, rather than regenerating IDs at logging time. `IntrinsicTransitionContext` gains world IDs, per-world episode/admission IDs and explicit global_vector_tick provenance; global tick is never the private service clock. `LaneOutcome` adds world_id/world_episode_seq without removing existing completion APIs.

The single DAC formula is unchanged: raw * runtime scale[N] * authored drive base * authored modifiers, then existing ending/retirement composition. Private scales remain vectors all the way to their own row. No population mean is used for canonical rewards. A preserved scalar summary may be clearly labeled mean-of-private-scales for telemetry only; per-world values remain present and no controller/composer consumes that summary.

## 3. Lifecycle and shared Q/C09 boundary

- Eligible-on-entry admission includes the terminal transition once. Completed/retired/inactive rows cannot update normalizers, queues, RNG or service clocks later. Same last event may return its cached receipt; changed or invalid duplicates refuse. Completion uses its own WorldId/episode identity and affects only that adaptive backend, not a batch mean or every lane's history.
- Accepted reset closes/refuses unfinished nonempty episodes as v3 specifies. Reset clears episode-local cursor/cache state once, while learned curiosity, RMS/counts/LRU/history, pending tails and RNG persist across that world's episodes. No reseeding/reinitialization on ordinary reset or idle ticks. Stable IDs survive reset/resume; no state is reused merely because a row index is reused.
- Core differential first runs with no Q updates but real curiosity updates. It then runs with real shared Q updates while each unchanged world's explicit actions and actual mechanics-input trace are controlled and recorded. Current active mechanics input is per-world depletion_multiplier in ENV.step; actions and any later genuinely applied controller intervention must be named at the real interface. Curiosity scale/reward/internal state are outputs, not controls one may pin to hide a leak.
- Separate C09 proof supplies lane-distinct Q/entropy/completion inputs and verifies each lane's decision/application, no lane0 broadcast and the declared shared-Q feedback. A shared Q update may alter later policy/controller inputs; strict B is not a claim that those closed-loop decisions are independent. Do not use a conditional simulator trace as proof of controller independence.

## 4. Restore, conversion, transfer and serving

`curiosity_checkpoint.py` defines `describe_curiosity_state`, `prepare_curiosity_restore`, `prepare_scope_conversion` and `CuriosityRestoreCandidate`. Preparation validates/allocates/loads all private candidates off-side, including every RNG/queue/optimizer/config/identity, and restores global RNG even on failure. Installation swaps only fully prepared owned state; invalid last-world payload cannot partly mutate first-world/Q/replay/world state.

Ordinary private resume requires matching scope/provider/active parameters/geometry/seed policy and exact declared world identity binding. Curiosity data itself is ID-keyed, and row permutations with corresponding context dispatch correctly; whole-run simulator row remapping is not silently invented by its loader. Missing/duplicate/extra IDs or mismatched binding refuse before mutation, with the preserved shared-resume or explicit conversion alternatives. A current private captured checkpoint restores every active replay row, local tail/clock, dedup identity and model state unchanged. There is no implicit shared/private conversion.

Two explicit shared→private operations are selected:

1. `fresh_private`: archive source curiosity unchanged; initialize each declared private backend from its seed. Preserve compatible Q/target/optimizer/scheduler, world/curriculum state and existing learning clocks. Curiosity starts a new declared isolation origin, not a fabricated private past.
2. `clone_learned_archive_pending`: deep-copy compatible learned network/optimizer/RMS/count/LRU/adaptive snapshot into each private slot, with independent mutable objects. Mark the prefix `shared_snapshot_template`; it is initial state, not that world's historical trajectory. Preserve inherited optimizer counters as inherited counters and start new local admission/service counters at0. Source mixed pending data is archived unchanged, never assigned to fictitious world trajectories or trained into every clone. Private RNG starts from declared world-derived streams, with its origin explicit; no exact old shared stochastic continuation is claimed. Unknown/incompatible mandatory shapes refuse before mutation; nonselected provider components stay archival under v3's compatible-state policy.

Both are new explicit operations; neither changes ordinary shared full resume or deletes source artifacts. There is no automatic merge of private learned curiosity into a shared instance. Existing fresh-target transfer may initialize the target's declared scope; retain-compatible transfer preserves target curiosity only under its explicit compatible policy. Target weights still recopy online, replay/optimizer resets follow the existing chosen transfer mode, and source history is never silently reinterpreted.

Approved historical A remains exact: pre-capture maskless replay is archived/readable/queryable/exportable and active replay starts empty; available other state/clocks restore. Captured shared/private replay is retained as recorded, including its original reward/provenance, and never recomposed under new scope. Private ICM/RND service consumes only new actual own-world admissions, never a global Q-replay sample. Loader dispatch inspects actual owned component formats/tags: an outer old version alone does not authorize clearing a newly captured buffer. A producer and its parent exact validators must evolve coherently in the same packet; ordinary-runner checkpoint smoke is required immediately. Supported producer-format inventory is recorded; arbitrary unsupported combinations acquire no invented migration promise.

Evaluation/serving records scope, source-world selection and state/update policy. Old omitted scope remains shared. Private fresh evaluation binds explicit evaluation IDs and creates fresh local state; `source_snapshot` requires explicit source world IDs and clones them independently without mutating training. No selecting lane0 and broadcasting it, pooling private states or pretending a shared prefix is private. Preserve existing reward-statistics-only viewer behavior as a named option; explicit read_only and local_learning policies are separately truthful. Required B proofs use actual local learning, not read_only. BaseT27 first delivers its working fresh-evaluation path; PW10 introduces source_snapshot enum/runtime together, never an accepted-but-unimplemented selector. T31's process-isolated sessions remain mandatory.

## 5. Simulator-state evidence without invented APIs

The prior VFS probe covered obs/reward/done/meters/positions, registry variables via `get(id,reader='engine')[w]`, effects tuples through `effects_in_world(w)`, global torch RNG digests and reset cycles. `vfs_random_state()` exposes runseed/episode only. Neither is a complete hidden-state snapshot API; no such API is assumed here.

PW12 owns a counted executable helper with `capture_world_snapshot(env, *, row, step_result, world_ids, inventory) -> WorldSnapshot`. Its finite inventory must name actual interfaces/adapters/source receipts for observations, done/survival, meters/positions, all VFS variables, effects, item state/inventories, affordance state, history, and every present world-owned RNG/draw cursor, plus reset/lifecycle state. Absent components are recorded explicitly for that authored profile. Shared immutable layout and shared policy/learner state are separately identified with contract/source rationale, not hidden by arbitrary exclusions. Capture real tensors/values into immutable CPU clones/canonical values; a later mutation cannot rewrite the snapshot.

The inventory/helper is inspected within ENV/REG/WS/helper/test context below and uses actual APIs plus runtime interface/data inspection, no sixth implementation source. A missing present owner is a failing inventory/probe requirement, not permission to claim full hidden-state equivalence from observations alone. Coordinator must supply its named owner receipt or bounded reslice/repair before X02 can close. This is a finite prerequisite for the known owner set, not an open-ended world-engine redesign. YAML profiles include unequal[2,5] lifecycles and present item/effect/history/affordance owners; existing compilable shipped profiles provide additional ownership controls.

## 6. Work packages, context and serialization

Only proposed packet metadata is written now. All source paths below are complete context for implementer AND fresh other-model reviewer. Every new test/probe/helper is charged. Recount before dispatch; exceedance requires a bounded reslice, not hidden reads or dropped tests. T01/T02/T08 completed evidence/context and the current frozen T18 execution packet are preserved, not retroactively altered.

| New packet | Complete source read inventory (W modify/N create/R read-only) | Files / lines | Dependencies |
|---|---|---:|---|
| PW01 Scope, stable identity, seeds and effective contract | modify `src/townlet/config/bac_options.py` 600; modify `src/townlet/config/effective_run.py` 300; modify `src/townlet/config/exploration_policy.py` 600; create `src/townlet/exploration/world_curiosity_state.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_scope_contract.py` 350 | 5 /2200 | T03,T18a,T08,T18 |
| PW02 Private RNG domains and quiescent lifecycle | modify `src/townlet/exploration/world_curiosity_state.py` 350; read_only `src/townlet/exploration/rnd.py` 700; read_only `src/townlet/exploration/icm.py` 500; read_only `src/townlet/exploration/adaptive_intrinsic.py` 300; create_test `tests/test_townlet/regressions/bac/test_pw_rng_domains.py` 350 | 5 /2200 | PW01,T18,T18b,T18c |
| PW03 Reusable backend and policy-selector factory | create `src/townlet/exploration/provider_factory.py` 250; read_only `src/townlet/exploration/rnd.py` 700; read_only `src/townlet/exploration/adaptive_intrinsic.py` 300; read_only `src/townlet/exploration/epsilon_greedy.py` 150; create_test `tests/test_townlet/regressions/bac/test_pw_backend_factory.py` 350 | 5 /1750 | PW04,T18b,T18c |
| PW04 Backend-local clocks and future native-consumer coherence | modify `src/townlet/exploration/rnd.py` 700; modify `src/townlet/exploration/icm.py` 500; modify `src/townlet/exploration/adaptive_intrinsic.py` 300; modify `src/townlet/population/vectorized.py` 3000; create_test `tests/test_townlet/regressions/bac/test_pw_local_service.py` 350 | 5 /4850 | PW02,T18,T18c,T19 |
| PW05 Scoped private-instance registry | create `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/exploration/world_curiosity_state.py` 350; read_only `src/townlet/exploration/provider_factory.py` 250; read_only `src/townlet/config/exploration_policy.py` 600; create_test `tests/test_townlet/regressions/bac/test_pw_private_bank.py` 400 | 5 /2250 | PW02,PW03,PW04 |
| PW06 Strict scope checkpoint preparation | create `src/townlet/exploration/curiosity_checkpoint.py` 450; read_only `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/exploration/world_curiosity_state.py` 350; read_only `src/townlet/training/historical_checkpoint.py` 450; create_test `tests/test_townlet/regressions/bac/test_pw_scope_restore.py` 400 | 5 /2300 | PW05,T03a |
| PW07 Explicit shared-to-private initialization | modify `src/townlet/exploration/curiosity_checkpoint.py` 450; read_only `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/training/historical_checkpoint.py` 450; read_only `src/townlet/exploration/world_curiosity_state.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_scope_conversion.py` 400 | 5 /2300 | PW06 |
| PW08 Population scope wiring and existing-validator coherence | modify `src/townlet/population/vectorized.py` 3000; modify `src/townlet/training/checkpoint_utils.py` 1000; read_only `src/townlet/config/exploration_policy.py` 600; create_test `tests/test_townlet/regressions/bac/test_pw_population_scope.py` 400 | 4 /5000 | T18e,T19,PW07 |
| PW09 Top-level load scope and identity dispatch | modify `src/townlet/training/checkpoint_utils.py` 1000; modify `src/townlet/training/load_modes.py` 220; read_only `src/townlet/exploration/curiosity_checkpoint.py` 450; read_only `src/townlet/exploration/world_curiosity_state.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_load_scope.py` 400 | 5 /2420 | T24,PW07 |
| PW10 Transfer and serving scope policies | modify `src/townlet/training/transfer.py` 400; modify `src/townlet/demo/live_inference.py` 1500; modify `src/townlet/demo/evaluation_view.py` 350; modify `src/townlet/exploration/curiosity_checkpoint.py` 450; create_test `tests/test_townlet/regressions/bac/test_pw_scope_serving.py` 400 | 5 /3100 | T27,T30,PW09 |
| PW11 Truthful per-world diagnostics and preserved summaries | modify `src/townlet/config/exploration_policy.py` 600; modify `src/townlet/population/runtime_registry.py` 250; modify `src/townlet/training/tensorboard_logger.py` 700; modify `src/townlet/demo/database.py` 850; create_test `tests/test_townlet/regressions/bac/test_pw_scope_telemetry.py` 350 | 5 /2750 | T35,T36,PW10,PW13,PW14 |
| PW12 Complete named simulator-state probe inventory | create `tests/test_townlet/fixtures/bac_curiosity/world_snapshot.py` 350; read_only `src/townlet/environment/vectorized_env.py` 2000; read_only `src/townlet/population/runtime_registry.py` 250; read_only `src/townlet/exploration/world_curiosity_state.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_world_snapshot_inventory.py` 400 | 5 /3350 | PW01,T22 |
| PW13 Actual-update private curiosity differential | read_only `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/config/exploration_policy.py` 600; read_only `src/townlet/exploration/world_curiosity_state.py` 350; read_only `tests/test_townlet/fixtures/bac_curiosity/world_snapshot.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_private_isolation.py` 400 | 5 /2350 | T18f,T23,PW12 |
| PW14 Reset, resume, conversion and old-history acceptance | read_only `src/townlet/exploration/curiosity_checkpoint.py` 450; read_only `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/config/exploration_policy.py` 600; read_only `tests/test_townlet/fixtures/bac_curiosity/world_snapshot.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_private_lifecycle.py` 400 | 5 /2450 | T26,PW10,PW12 |
| PW15 C09 ownership and shared-Q feedback differential | read_only `src/townlet/population/vectorized.py` 3000; read_only `src/townlet/curriculum/adversarial.py` 800; read_only `src/townlet/training/episode.py` 200; read_only `src/townlet/exploration/scoped_curiosity.py` 650; create_test `tests/test_townlet/regressions/bac/test_pw_private_controller.py` 300 | 5 /4950 | T30,T23,PW12 |
| PW16 Strict/shared matrix, source-verified claims and finite cohort | read_only `src/townlet/config/exploration_policy.py` 600; read_only `src/townlet/exploration/scoped_curiosity.py` 650; read_only `src/townlet/demo/evaluation_view.py` 350; read_only `src/townlet/exploration/world_curiosity_state.py` 350; create_test `tests/test_townlet/regressions/bac/test_pw_private_support_matrix.py` 350 | 5 /2300 | PW11,PW13,PW14,PW15,T37,T38,T39 |

### Existing-packet coherent reslices

- Preserve **current frozen T18 exactly as an execution boundary**: dependency T02; four actual source files/RND604 + POP1854 + OP243 + its counted test334 =3035 lines. Its actual native-runner smoke has passed, while package/full review and the native POP optimizer-payload P2 repair remain in T18; a smoke pass is not package approval. This addendum adds no HC read, T16/PW01 prerequisite, requirement replacement or retroactive source/receipt change to T18. Root retains its current packet and recounts the real final repair inventory there before release. Completed T01/T02/T08 packets are likewise untouched. Future ceilings below never replace these attributed historical/current counts.
- PW04 owns the genuinely future B clock adapters and their native POP validator/producer coherence: RND700 + ICM500 + Adaptive300 + POP3000 + its test350 =5 files/4850 projected lines, after T19 and before bank/facade consumers. It consumes PW02's declared ServiceClock/event-state public contract from the approved interface/receipt without opening WS implementation; all five actual implementation/test sources are listed. Its own real ordinary-runner save/load smoke must pass at its changed-source SHA. Earlier T18 native evidence is a control, not a substitute. Native optimizer/tail/clock rejection must leave live state unchanged; no broken current consumer may be deferred to T25.
- PW01 waits frozen T18, so later OP scope changes cannot rewrite T18's dependency receipt. Future POP writer order is T18→T15→T16→T19→PW04→PW08; T19 continues to wait T18.
- T18d consumes PW03's backend factory and PW05/PW06/PW07 bank/state policy: RP/PF/BANK/WS/test,5files2200. Same five-provider construction, epsilon, scale and continuation goal; implementation is reused rather than duplicated.
- T18e has ENV/RWC/DAC/RP/test,5files4300. It delivers scoped stamped contexts and real vector scale composition in both modes, with no additional hidden helper read.
- PW08 owns POP/CK/RP/test,4files5000, before T18f; it pairs actual population wiring with any required existing exact-validator compatibility. T18f then modifies RR and reads POP plus its test,3files4850; original runner end-to-end goal is unchanged.
- T24 follows PW08's CK ownership; PW09 followsT24 and precedesT25. PW10 followsT27/T30 and precedesT31; it owns CP/LIVE/TR/EV together for its source-snapshot/transfer feature. CP mutations serialize PW06→PW07→PW10. RP mutations serialize T18a→PW01→T18d→PW11.
- Future ceilings are RND700 (current attributed604 plus adapter/repair growth), OP600, RP600, EP200, RWC250, REG250, TB700, DB850, EV350, TR400; no POP/ENV ceiling inflation is used to hide a >5000 task. `per-world-curiosity-packets.json` explicitly recounts every affected future base packet, dependencies and ownership. BaseT40's counted test ceiling becomes400 for its additive cohort cases (GE300+test400=2files700). All old goals and existing tested alternatives remain.
- T35 also waits PW12 so its runtime-registry mutation cannot race the named simulator-state inventory reader. All shared-file writer/reader pairs are ordered in the proposed combined DAG.
- PW12's counted snapshot helper350 is explicitly included in PW13/PW14 context. PW15 deliberately reads controller/population sources rather than silently adding that helper as a sixth file; its controller probe makes no standalone full-hidden-state claim.

### Required proof and commit steps for each new packet

Each packet has exact test nodes in the JSON and below. For each: add the named real regression/control red; run its exact `uv run pytest --no-cov -p no:cacheprovider <test_path> -q`; implement only owned paths/interfaces; rerun green plus owning existing suites and relevant actual consumers; obtain fresh other-model review, repair, run the effective cadence/static/full gates, and commit exactly that packet with its specified subject. Before costly work validate collection/import/fixture/exact SHA. Receipt includes exact inventory, evidence, limitations, scope/origin and next full gate. No fake mock-composer pass or looped flaky rerun is acceptance.

#### PW01: Scope, stable identity, seeds and effective contract

**Interfaces/acceptance:** Omission remains shared; explicit per_world roundtrips compile/cache/effective identity and preserved old shared hash recipe. IDs a.b/a/b/Unicode remain distinct; duplicate IDs refuse. Same WorldId seed/state survives row order and spectator-N changes; new scope changes guarantee identity. Create explicit shared/per_world YAML profiles without changing old defaults.

**Exact tests:** `test_scope_defaults_and_identity_roundtrip`, `test_world_seed_is_stable_under_lane_reorder`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_contract.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): declare explicit world ownership and seed contracts` and record immutable source/evidence SHA, inventory and limits externally.

#### PW02: Private RNG domains and quiescent lifecycle

**Interfaces/acceptance:** For each trainable backend and real optimizer update, private world1/global RNG states are unchanged by added world0 calls except world0's own state. Global RNG restores on constructor/load/compute failure; private streams resume from saved state. Prove no mutable object/state aliases across worlds/banks, and serialize owner calls rather than introducing concurrent global-RNG overlap.

**Exact tests:** `test_private_rng_restores_global_streams`, `test_world1_rng_independent_of_world0_calls`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_rng_domains.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): isolate per-world random streams` and record immutable source/evidence SHA, inventory and limits externally.

#### PW03: Reusable backend and policy-selector factory

**Interfaces/acceptance:** Construct all five existing classes, same shared configuration effect, real per-world fresh mutable instances, and matching model geometry. Factory/selector APIs are complete before facade consumption; no absent ICM/count source helper or duplicate model implementation.

**Exact tests:** `test_factory_reuses_all_five_backends`, `test_private_factory_returns_disjoint_mutable_instances`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_backend_factory.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `refactor(curiosity): separate backend construction from scope routing` and record immutable source/evidence SHA, inventory and limits externally.

#### PW04: Backend-local clocks and future native-consumer coherence

**Interfaces/acceptance:** Vary idle vector ticks and world0 budget pressure while world1 has the same local admissions: its consumed batches, updates, queue/order, drops, LR/optimizer counters, loss scale and clipping match exactly. After frozen T18/T19, introduce future adapters and update actual POP validators coherently in PW04. Restore old/shared backend tail/clock/optimizer state and perform a new real ordinary-runner save/load at PW04's changed-source SHA; malformed deep optimizer/tail/clock payload refuses before live mutation. Any caused consumer failure is repaired inside PW04 before release, never by rewriting T18's packet or waiting for T25. Use PW02's documented public ServiceClock/stamp interface without reading WS as a sixth source.

**Exact tests:** `test_local_clock_ignores_idle_vector_ticks`, `test_backend_losses_and_quotas_are_world_local`, `test_shared_runner_checkpoint_still_roundtrips`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_local_service.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): service private backends on local admissions` and record immutable source/evidence SHA, inventory and limits externally.

#### PW05: Scoped private-instance registry

**Interfaces/acceptance:** Run RND/adaptive/count/ICM/none in two scoped banks. World1 parameters/moments/RMS/queues/history/weights/RNG/counters match across different world0 activity, with at least two real world1 predictor/ICM updates and nonzero parameter change. Assert optimizer/parameter/container identity separation, not just matching logged counters. Shared scope retains a positive coupled-reward/count-collision control.

**Exact tests:** `test_private_models_moments_and_queues_do_not_alias`, `test_world1_updates_match_when_world0_activity_changes`, `test_shared_mode_retains_coupled_control`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_bank.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): add per-world provider state banks` and record immutable source/evidence SHA, inventory and limits externally.

#### PW06: Strict scope checkpoint preparation

**Interfaces/acceptance:** Same-scope private state roundtrips all IDs, models/moments/RMS/LRU/tails/RNG/dedup. Missing/extra/duplicate/mismatched IDs, wrong scope/provider/config/geometry, malformed last-world tensor/RNG/queue or allocation failure leave all active state unchanged. Current full resume preserves active captured replay and private counters.

**Exact tests:** `test_private_restore_matches_by_world_id`, `test_invalid_last_world_leaves_all_runtime_state_unchanged`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_restore.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): prepare strict world-owned checkpoint state` and record immutable source/evidence SHA, inventory and limits externally.

#### PW07: Explicit shared-to-private initialization

**Interfaces/acceptance:** fresh_private has declared fresh origin; clone_learned_archive_pending retains compatible learned tensors/moments/RMS/counts/history as independent copies, inherited counters labeled, future local counters0, mixed pending unchanged archivally. Both preserve source/shared resume and captured replay; old maskless data still follows approvedA. No initial private history is fabricated.

**Exact tests:** `test_fresh_private_and_clone_learned_origins`, `test_shared_pending_is_archived_not_falsely_attributed`, `test_current_captured_replay_is_preserved`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_conversion.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(curiosity): add explicit private initialization policies` and record immutable source/evidence SHA, inventory and limits externally.

#### PW08: Population scope wiring and existing-validator coherence

**Interfaces/acceptance:** Two real ordinary populations bind exact stable IDs. Actual eligibility governs every reward/service/completion, inactive rows get no calls, different private scales reach different rows. Save/load through the actual runner/existing validators succeeds immediately, with complete provider state and no stale exact-key rejection; no fix is deferred toT25.

**Exact tests:** `test_real_population_uses_stable_world_ids`, `test_private_ordinary_runner_checkpoint_smoke`, `test_inactive_world_gets_no_curiosity_call`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_population_scope.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(population): bind world-owned curiosity through runtime state` and record immutable source/evidence SHA, inventory and limits externally.

#### PW09: Top-level load scope and identity dispatch

**Interfaces/acceptance:** Normal private resume strictly matches binding; mismatches refuse atomically. Explicit conversion has its allowlisted scope-derived identity differences and no automatic fallback. Header/parent/owned state versions are coherent and supported producer forms recorded; newly captured rows are never archived merely because an outer version is old.

**Exact tests:** `test_same_scope_resume_and_explicit_scope_mismatch`, `test_scope_import_failure_is_atomic`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_load_scope.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(checkpoint): validate curiosity scope and world binding` and record immutable source/evidence SHA, inventory and limits externally.

#### PW10: Transfer and serving scope policies

**Interfaces/acceptance:** Fresh-target transfer initializes every target-world curiosity in its declared scope; retained-compatible state preserves the target's own validated state. Private viewer snapshot requires source IDs, copies independently and never broadcasts lane0 or mutates training. Fresh/reward-stats-only/read-only/local-learning views identify actual semantics, with true local updates in the required B serving path and unchanged Q eval/memory rules.

**Exact tests:** `test_transfer_fresh_and_retained_private_state`, `test_viewer_world_selection_and_private_snapshot_clone`, `test_serving_curiosity_does_not_mutate_training`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_serving.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(serving): preserve explicit curiosity scope on load and transfer` and record immutable source/evidence SHA, inventory and limits externally.

#### PW11: Truthful per-world diagnostics and preserved summaries

**Interfaces/acceptance:** Different private weights such as[.2,.8] remain actual per-world rewards/sink values; a mean summary may report.5 but cannot scale both rows. Every scope/guarantee/clock/origin/shared prefix is truthful in effective identities/SQL/TB/registry, with no whole-population hidden feedback into service.

**Exact tests:** `test_per_world_scales_and_state_units_reach_sinks`, `test_scalar_summary_is_never_used_for_reward`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_scope_telemetry.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `feat(telemetry): report curiosity ownership and guarantees` and record immutable source/evidence SHA, inventory and limits externally.

#### PW12: Complete named simulator-state probe inventory

**Interfaces/acceptance:** Every present named physical/history/item/effect/affordance/RNG owner is captured or blocked with a concrete missing owner interface. Snapshot immutability and correct row/ID binding are tested. The helper never equates observation-only equality with full-state equality, and excludes shared-policy state only under the actual contract.

**Exact tests:** `test_snapshot_covers_each_present_world_state_owner`, `test_owned_snapshot_is_immutable_and_world_indexed`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_world_snapshot_inventory.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `test(isolation): inventory actual world-state snapshot owners` and record immutable source/evidence SHA, inventory and limits externally.

#### PW13: Actual-update private curiosity differential

**Interfaces/acceptance:** First reproduce the retained shared no-optimizer coupling as an intentional positive control. Strict pair uses equal initial snapshots, active normalization, nonzero weights, full local traces and real RND/ICM optimizer changes. Vary world0 actions/admissions, count-key collisions/LRU eviction, own completion/anneal, inactive/unequal[2,5] lives, row order, spectator worlds and idle service calls. In a simulator differential keep the unchanged world's actual simulator tick/draw-input trace fixed and capture its RNG provenance; do not equate arbitrary global-tick changes with an identical local mechanical trace or overwrite random outputs to force equality. Assert world1 raw/intrinsic/canonical total, full private state and inventoried world state bitwise equal on the fixed device/profile; never force post-admission state equal or disable training.

**Exact tests:** `test_private_reward_and_state_match_across_real_updates`, `test_count_lru_anneal_and_idle_worlds_are_private`, `test_shared_novelty_is_explicitly_coupled`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_isolation.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `test(isolation): prove private curiosity through real updates` and record immutable source/evidence SHA, inventory and limits externally.

#### PW14: Reset, resume, conversion and old-history acceptance

**Interfaces/acceptance:** Two episodes, duplicate completion/reset, pending2-of3, private checkpoint/full resume, explicit scope conversions, historicalA archive integrity and standalone relocation all work. Private same-trace continuation matches while old/shared access remains available. Malformed deep last-world state or bad source-world selection cannot mutate any earlier world/Q/replay/world/curiosity state.

**Exact tests:** `test_private_two_episode_and_tail_resume`, `test_archive_A_and_scope_conversion_preserve_source_data`, `test_malformed_world_state_refuses_without_partial_mutation`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_lifecycle.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `test(isolation): qualify private curiosity state lifecycle` and record immutable source/evidence SHA, inventory and limits externally.

#### PW15: C09 ownership and shared-Q feedback differential

**Interfaces/acceptance:** Use lane-distinct Q/entropy/controller inputs and actual[1,5] stage decisions reaching[.2,1] mechanics. Verify each lane receives its own decision, then allow real shared-Q updates and record their feedback. In the separate conditional pair, hold full actions/mechanics fixed while Q actually updates and curiosity actually trains; private rewards/state still match. Controller outputs themselves are not declared independent.

**Exact tests:** `test_controller_uses_own_lane_inputs_and_applies_own_decision`, `test_private_curiosity_with_real_shared_q_updates_and_fixed_controls`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_controller.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `test(isolation): distinguish private curiosity from shared policy feedback` and record immutable source/evidence SHA, inventory and limits externally.

#### PW16: Strict/shared matrix, source-verified claims and finite cohort

**Interfaces/acceptance:** Require all four Q families ×all five providers ×both scopes to have truthful compile/rollout/update/save/load/serving rows and explicit strict profile. Preserve original T40 cohort and add only the finite strict cohort below. Source-verify docs/claims/units, update X02 acceptance rows and final-lens coverage, never mark X02 closed from a selector flag or frozen-predictor run.

**Exact tests:** `test_all_families_and_providers_have_truthful_scope_rows`, `test_required_strict_cohort_is_explicit_and_finite`.

- [ ] Write those failing authored/unit controls and run `uv run pytest --no-cov -p no:cacheprovider tests/test_townlet/regressions/bac/test_pw_private_support_matrix.py -q` red for the intended missing guarantee.
- [ ] Implement the stated producer/consumer contract only in the owned files; use accepted predecessor interfaces and no unlisted source/helper read.
- [ ] Run the exact command green plus actual owner/consumer suites and capture genuine state/optimizer evidence with the stated negative controls.
- [ ] Complete required static/full checkpoints and fresh other-model adversarial review; repair blockers before any dependent package.
- [ ] Commit `test(bac): publish scoped curiosity qualification evidence` and record immutable source/evidence SHA, inventory and limits externally.

## 7. Finite integration/final acceptance

Retain all original per-package proofs, required owner/static checks, G1–G7 gates and early full triggers. Identity/schema/serialized ownership changes and material cross-slice repairs require earlier full suites before dependent release under the already owner-approved cadence exception; unused isolated helpers may use the documented next coherent checkpoint. Add a core B integration checkpoint after PW01–PW08/PW12/PW13 and T18f/T23, then state/serving/controller/matrix qualification after PW09–PW16. An identical unchanged candidate may satisfy two labels once; no gate is silently waived.

The acceptance ledger gains X02→PW01–PW16→exact tests/evidence→OPEN/CLOSED plus scope/origin/binding/guarantee/source SHA, with BAC-C05/C08/C09 primary and C02/C07/C10/C11/C12/C13 seams. Strict fresh and converted origins are distinguished; shared mode remains the explicitly preserved coupled alternative. X02 closes only after genuine private updates, complete required owner snapshots, lifecycle/load/conversion/serving, C09/shared-Q controls, source-verified truthful mode/default claims and independent final evidence. No unresolved P1/P2 or unapproved in-scope gap is relabeled optional.

Keep the original T40 finite protocol/cohort intact. Add a bounded12-run strict cohort (four families ×seeds[11,29,47],10k eligible transitions/run,20 evaluation episodes/seed), explicit per_world and nonzero adaptive-RND curiosity with real local predictor updates; all other choices/any deviations are recorded in its manifest. Use the same named random-legal/scripted/constant controls and separate extrinsic/raw novelty/effective intrinsic/total/survival/task success metrics. This adds at most120k training transitions, not a provider-algorithm sweep. Original and strict cohorts are distinct; do not claim a causal shared-vs-private learning comparison if provider/evaluation settings differ. All existing thresholds/negative controls/failure reporting remain. No campaign starts before integrity gates pass.

All17 original fresh final source/spec/design lenses and independent synthesis remain. Recount their contexts using the future ceilings above (all remain≤5/5000). Add these four current-source lenses, each fresh other-model and with a counted350-line scratch probe, all at the final common immutable SHA:

| Added final lens | Complete source context | Files/lines | Required current-source claim |
|---|---|---:|---|
| F18 private bank/RNG/factory | BANK650,WS350,PF250,RP600,probe350 |5/2200 | All private mutable ownership, RNG/global restoration, real updates/local budgets, preserved shared mode |
| F19 private state/transfer | POP3000,CP450,WS350,TR400,probe350 |5/4550 | Strict atomic binding/resume/conversion/archives and fresh/retained transfer; shared/current resume not reduced |
| F20 physical/reward comparator | SNAP350,ENV2000,RWC250,DAC1100,probe350 |5/4050 | Full named owner inventory, actual context/phase, vector scale and canonical total; no invented full-snapshot proof |
| F21 C09/shared-policy boundary | POP3000,CA800,CB150,EP200,probe350 |5/4500 | Own-lane controller inputs/application, shared-Q feedback and valid controlled-mechanics differential |

Original final contexts affected by ceilings remain bounded: F01 BC750/TC650/OP600/EF300/probe350=2650; F08 AS160/RND700/AI300/RP600/probe350=2110; F10 RR1500/CL180/CC150/REG250/probe350=2430; F11 CK1000/LM220/TR400/RC250/probe350=2220; F12 LIVE1500/EV350/SERVER700/IW300/probe350=3200; F14 REC550/RT150/DB850/TB700/probe350=2600; F15 GE300/EV350/T40test400/probe350=1400; F16 COUNT300/ICM500/RP600/RND700/probe350=2450; F17 ENV2000/RWC250/DAC1100/DRIVE750/probe350=4450. Others retain their approved contexts. Synthesis now reconciles all 21 lenses, X02 and mode/default/origin declarations; repeated repair→review→same-SHA gates continue until the finite ledger passes. Final repo/coverage/slow/hardware checks and required remote CI are unchanged.

## R1 technical repair disposition

Astra MEDIUM R1's sole activation blocker is resolved by preserving current frozen T18 and moving all future B adapter/native-consumer coherence into existing PW04. No seventeenth additive packet or owner-policy change is needed. RND future ceiling700 replaces every former500 in future packet and final-lens contexts; the only604 count is the attributed frozen T18 actual inventory. All future inventories are floored at supplied current actual sizes plus stated growth; dispatch recount remains mandatory. The regenerated64-node DAG and mutating shared-file preflight explicitly use T18's preserved T02 boundary, PW01 afterT18 and PW04 afterT19. The finite acceptance/cohort/gates and all16 additive packet goals remain. X02 and T18 review status are not closed by this amendment.

## Review focus, open facts and activation

- Repeat actual normalization, private gradient/optimizer, count collision/LRU and adaptive-history contrasts; neither a private RMS-only patch nor frozen/shared predictor passes.
- Keep real unroll/anchor loss masks separate and preserve active-on-entry/terminal/retirement eligibility. No event/control/RNG identity derives from global idle ticks or lane position.
- Scope conversions explicitly identify shared prefix and archive unassigned pending data; current captured replay/old artifacts/shared resume remain intact. No historical rewards or missing private trajectories are fabricated.
- Full item/history/affordance/effect owner accessors are not yet supplied as one complete API; PW12 must name and prove them through actual owned interfaces/receipts. Any genuine missing owner exposure blocks the affected proof and requires a bounded coordinator reslice, not guessed field names or a green claim. There is no additional owner policy choice required to implement B.
- Existing universal/default product wording is reconciled truthfully with the selected explicit modes; omitted scope is still shared, strict fixtures are explicit, and no new universal all-runs promise/default substitution is inferred. Surface a contrary claim rather than silently selecting A.

Owner B is already authorized. Same Astra MEDIUM must technically approve this exact addendum and proposed context/DAG before B-sensitive integration. Independent legal/replay work can continue under existing approved packets/gates. Root activates overlays and owns portable ledger/docs/decision updates after that review; those reference artifacts do not grant packet workers extra source files. This planner writes only these ignored proposal artifacts and makes no source, frozen-plan/cadence, root progress/index or portable-decision edits. X02 remains open until implementation and executable acceptance, not merely review or owner selection.
