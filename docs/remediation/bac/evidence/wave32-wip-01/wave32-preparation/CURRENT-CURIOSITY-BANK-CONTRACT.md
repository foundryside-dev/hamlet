# Current curiosity BANK producer contract

Source-verified PW07 successor contract for actual CP1135/BANK1282/RP768/test1456, exactly4641 whole lines within named ceilings5000. The [checkpoint contract](CURRENT-CURIOSITY-CHECKPOINT-CONTRACT.md) records exact source links/hashes, schemas, initialization/restore custody and attributed evidence. Current coherent candidate is `4f755ce9756fcde76cba50e96673b67aa54b1571`, base a7c4cd0b; production/main153/metadata16 bytes remain identical to qualified `3c0052b80d24fc6387a1e186e485b808dd3bf3de`, as root records in `W/wave32/r1-production-equivalence.json`. No runtime accompanied this document. Component fixture correction and final bounded gates are closed; integrated parent qualification remains open. Root owns publication after scoped prose re-review.

## Actual construction and operations

Module `townlet.exploration.scoped_curiosity`. `CuriosityBank(*, policy, descriptor, device, validate_accepted_episode, issuer_factory, report_allocation)` requires every keyword. It requires actual `ResolvedExplorationPolicy`, roundtrips owned policy/descriptor, verifies complete policy-derived descriptor, exact unique nonempty world IDs, selected geometry, float32 and CPU or explicitly indexed CUDA. None allows observation width0; other families require positive width. Constructor allocation reporting occurs before eager provider construction.

The actual parent supplies `validate_accepted_episode(accepted=token)` and an issuer bound to this BANK. The issuer's owner property alone cannot establish ENV authority: the actual parent registers this same BANK as curiosity role owner and ENV authenticates issued receipt identity/kind/owner. BANK imports no ENV implementation. Instance methods serialize with RLock; parent/runtime coordinates other owners, unrelated RNG users and CUDA initialization.

All listed inputs are required keywords except the argument-free checkpoint export:

| Method | Result / purpose |
| --- | --- |
| `begin_episode(*, accepted)` | genuine activation receipt |
| `prepare_step_stamp(*, accepted, world_ids, active_on_entry, vector_tick)` | CuriosityStepStamp |
| `reward(*, context, stamp, accepted, update_stats)` | owned CuriosityReward |
| `admit_and_service(*, context, stamp, accepted)` | tuple of WorldServiceReceipt |
| `prepare_completion(*, accepted, boundary_key, completion_content, outcomes, participated_world_ids)` | PreparedBankCompletion |
| `commit_completion(*, prepared)` | genuine dispositions receipt |
| `prepare_empty_episode_evidence(*, accepted)` | genuine empty_episode receipt |
| `quarantine_episode(*, accepted, reason)` | conservative quarantine notification |
| `snapshot_world(*, world_id)` | owned diagnostic mapping; advances observer revision |
| `checkpoint_state()` | complete owned current BANK v2 transport |
| `prepare_restore(*, state, mode, accepted, parent_restore, validate_parent_restore)` | destination/revision-bound opaque restore handle |
| `prepare_private_initialization(*, state, initialization, parent_restore, validate_parent_restore)` | explicit fresh/clone initialization handle |
| `install_restore(*, prepared)` | one prepared publication; None |

Module `allocation_estimate(*, policy, descriptor, device)` is a pure known-tensor constructor estimate. It neither allocates a provider nor replaces constructor validation. Snapshot is diagnostic, not a restore decoder. There is no new CLI, parent coordinator or legacy adapter API.

## Families, ownership and reward/service clocks

Private scope eagerly constructs actual WorldRNGState/OwnedWorldBackend per exact ID in canonical sorted allocation order through actual BANK factory callbacks. Learning models, fixed targets, Adam/moments, gradients, RMS, Count/LRU, active tails, adaptive history/weight and named RNG streams remain independently owned. Shared scope explicitly constructs one coupled provider with world_id/rng/descriptor=None and vector_tick policy. All five families remain substantive: none, count_based, rnd, adaptive_rnd, icm. Shared selected seed label `legacy_shared_v1` is its current ownership label; it does not authorize obsolete artifact fallback. Global Q/action selection and epsilon cadence remain separate.

Actual `IntrinsicTransitionContext` owns predecessor/actions/successor/active_on_entry/vector_tick. BANK receives its separate stamp and actual accepted token. Whole-row geometry, finiteness, action bounds, selected float32/device/width and token/episode/eligibility bindings validate before work or retry. Active-on-entry terminal transitions receive one eligible event; inactive rows call no provider.

RND/adaptive/Count/none reward eligible successor rows; ICM uses actual predecessor/action/successor context. Adaptive raw novelty is unweighted and scale comes from current provider get_intrinsic_weight. Other eligible scales use resolved initial_intrinsic_weight. Inactive raw and scale are0. CuriosityReward owns raw/scales/eligibility and returns tensor clones. DAC base/modifiers and final composition remain external and must apply runtime scale once.

**Current none behavior:** eligible raw0 and contribution0, but scale equals initial_intrinsic_weight. CP validates that same cached scale. T18d's zero-scale requirement is pending producer/consumer work; this contract does not claim it is implemented.

Private RND/adaptive service admits own eligible predecessor rows; private ICM admits complete one-row transitions. Public service clock is world_eligible_admission at cumulative+1, independently of vector tick. For initialized trainable owners, native clock adds inherited admitted baseline; public receipt and BANK position count only future local admissions. None/Count advance genuine eligible BANK positions without predictor counters/clocks. Count reward admission is not repeated during service. RND overflow updates map to mandatory_service_updates and absent last_loss to0; ICM retains actual receipt fields. Provider service budgets/overflow/queues remain selected behavior, without cross-world quotas.

Private returns one receipt per presented row, with exact own event/world and zero inactive effects. Shared nonempty eligibility returns one aggregate receipt with world_id=None and original eligible event order; trainable service uses actual vector clock/deltas. Shared none/Count have no predictor clock/counters. All-inactive shared input returns an empty tuple without servicing an existing tail; this BANK path does not invoke separate native empty-call opportunities.

## Episode and retry semantics

ENV authenticates actual accepted identity. Initial accepted sequence is1 even for legal batch0; next begin requires each exact sequence n+1 after dispositions or a truthful private_initialized boundary. Same actual-token begin retry returns the existing activation receipt. New begin clears episode-local caches/dispositions/reservation/history while retaining learned state, gradients, tails, cumulative positions, origin and epoch.

prepare_step_stamp reserves next eligible sequence, retains inactive sequence and records vector tick in BANK metadata; CuriosityStepStamp itself has no tick field. Equal current preparation returns its stamp. Reward precedes service; completion requires settled work. CuriosityEventId is value identity, not an ENV capability. Ordinary epoch0 or initialized source+1 epoch is retained and checked throughout runtime/cache transport.

Private retry requires full exact own content/original tick/update_stats and latest own phase event. Finite inactive row values are excluded from local equality, while whole-row validation still applies. An unchanged eligible own event may retry at its original tick after another world's later work; cached reward/scale/service returns without provider/RNG/cursor/cache/revision mutation or replacing the newer reservation. Changed or expired own provenance refuses. Shared retry requires complete current ordered batch/stamp/tick/content. Caches retain source tensors, not only hashes.

## Completion, failure and empty custody

Completion uses actual LaneOutcome records in participating accepted-world order with exact world/sequence/batch/agent-index identity. Boundary key is exact nonnegative accepted.batch_episode. Canonical content is the full tuple of `(freeze_lane_outcome(event).payload.hex(), fingerprint)` values, not fingerprint-only evidence.

First preparation reports allocation before owning outcome data and candidate work. Equal pending retry checks complete retained scalar/tensor/type/shape/device/content evidence before codec allocation/report/owner calls, then returns the same prepared object. Caller mutation or changed content refuses. Actual adaptive completion shallow-copies the provider and independently copies survival_history, invokes real update_on_episode_end on raw survival steps, and retains only candidate history/weight. Shared outcomes apply in original accepted order. No model/Adam/gradient/RMS/tail restore occurs. Expected candidate ValueError refuses off-side without quarantine; observed preparation still advances revision. Nonadaptive completion changes dispositions only.

PreparedBankCompletion is destination/revision/pending-identity-bound; BANK owns publication values separately from returned token fields. Pending completion blocks steps/begin/snapshot/export/restore. Preparation issues prepared_dispositions; commit validates custody/content and publishes only candidate adaptive history/weight and dispositions/cache, then issues dispositions. Every accepted world receives completed or retired_nonparticipating; nonparticipants gain no invented outcome/history. Exact last source-instance commit retry returns the original receipt. Ordinary completion preserves model/optimizer/gradient/tail identities and values.

Unexpected provider/result/receipt/cache/return-copy failures after observation/publication quarantine, including owner callback failure. Already begun Count/RMS/optimizer effects have no rollback promise. Expected off-side restore refusal leaves live destination state intact; explicit healthy checkpoint restore can recover a quarantined BANK. A quarantined partial source cannot export. Snapshot/export are observations that advance revision and stale previously prepared handles.

Empty evidence requires actual token, no participation/admissions/disposition and no unfinished phase/completion. It issues empty_episode with exact accepted token and empty participant/events tuples without changing learned/RNG/cursors/revision. Actual ENV abandonment independently authenticates registered owner evidence; evidence alone is not ENV success. quarantine_episode accepts only empty_participation/runtime_failure, authenticates current token, and is idempotent only for the same token/reason. It does not invent closure, reset, retirement or an INITIAL exemption. Parent/T26 recovery wiring remains owed.

## Initialization, diagnostics and continuation

Only explicit `fresh_private` or `clone_learned_archive_pending` prepares shared-to-private initialization into an untouched healthy INITIAL receiver. Source must be ordinary current shared INITIAL or committed COMPLETED with compatible selected behavior/geometry/seed/membership/device. Ordinary restore does not invoke conversion. Both choices preserve a complete independently owned inactive source archive, including pending rows and original gradients/history. Fresh uses actual initial native state; clone preserves learned state and inherited settled native baseline while emptying the active local tail. Full equations and compatibility rules are in the checkpoint contract.

Native baseline is a shared template, never work attributed to each world's past. Future-local counters and BANK cumulative positions start0. Clone preserves Adam/native consistency and signed RND offset. Real future service translates native clock by the baseline and emits local public clocks. None/Count have no invented predictor ledger. Both choices retain independent same-ID factory RNG continuation; no shared historical RNG becomes a private stream.

`snapshot_world` schema is `curiosity-bank-world-v2`, with exact fields `schema, scope, world_id, policy_identity, descriptor, backend, curiosity_epoch, initialization_origin, future_service_counters, accepted_identity, cursor, phase_cache, pending_step, bank_phase, historical_identity`. Private backend is native+RNG owner envelope; shared backend is coupled native provider state. Trainable private future_service_counters contain admitted_rows/consumed_rows/dropped_rows/optimizer_updates/mandatory_service_updates/pending_rows. RND/adaptive mandatory cumulative field is None; none/Count and shared future_service_counters are None. Diagnostic source/archive/counters are independently owned.

INITIAL has zero ENV cursors and no accepted/history/cache/disposition. Completed-source initialization yields private_initialized: real source episode baseline, zero local work and no accepted/closing capability, fake completion or imported disposition. Source completion exists only in origin. Next begin needs real baseline+1 ENV token. Ordinary completed restore instead retains truthful historical_identity and completion data while accepted_identity is None; absence of an accepted token does not imply INITIAL.

Current ordinary INITIAL, private_initialized, live and completed restores retain origin/epoch, full native state, explicit optional gradients, RNG, local caches/cursors and phase provenance. Unstarted initialized states are checked against the selected fresh/clone native and gradient template. Later evolved learning validates under current native/local equations. Private_initialized correlates actual parent against archived source history; later private restore correlates its current runtime. Complete current OrderedDict order/_metadata and NumPy floating RMS values survive through the qualified owner codec. Issued authority capabilities never serialize.

AllocationEstimate retains schema/operation/scope/device/dtypes/world/participant/instance counts, known bytes/components, assumptions and unknowns. Reports cover constructor/completion/restore plus initialization and origin-bearing snapshot/checkpoint archive cost. Unknown Python Count/container/integer cost, allocators/workspace and external copies remain explicit. Report refusal precedes admitted allocation; there is no scope/capacity fallback. Off-side native preparation, gradient attachment, late real runtime allocation and parent callbacks finish before one preallocated publication. Genuine parent all-child freshness/publication and quiescence remain external responsibilities.

## Evidence boundaries

Historical W25 BANK901 runtime evidence was root84PASS28.4573s, independent Sol84PASS45.3494s and covering551PASS/3 CUDA skips36.7296s. PW06 v1 checkpoint evidence was root147PASS65.5674s, independent Astra147PASS80.4319s and covering635PASS/3 CUDA skips101.5953s. These historical overlapping selections are not current-source reruns or additive totals.

Current PW07 main root153PASS84.7200s and independent Sol153PASS137.7268s plus whole bounded source/design/runtime approval qualify the tested component. Separate codec root16PASS14.3636s/independent Astra16PASS13.9113s qualify OrderedDict/_metadata preservation. Root all10 paced positive conversions PASS26.6487s. Production and these suites are byte-identical at current4f755ce9. Its final combined selection954 completed951PASS/3 conditional CUDA skips121.8010s, with custody354source/573config/13protected artifacts/4pytest identities PASS. The earlier780PASS/2 stale reference-helper FAIL/3 CUDA skips204.6491s is historical: pure fixture correction now has root31PASS/1skip18.1072s and independent Astra31PASS/1skip18.9909s. Actual poison children verified354 source hashes/48 imports/intra-op1/inter-op5. Root supplies final test-reference prefix9457bc3f942 and APPROVED reviewer prefixbfd9324f. All runtime is closed; bounded component gates are complete. These overlapping selections are not additive totals.

Final four cheap guards PASS/default601, including Black45.4959s; global mypy still has nine oracle/POP caller errors across197 sources. Previous public a7c CI is Config PASS/Lint FAIL/Tests FAIL. Tests-job logs failed retrieval twice with Transport closed; cause remains untriaged and cannot be inferred to be only the nine mypy errors. No remote CI success for current4f755ce9 is claimed.

Actual learning/storage/gradient/optimizer/fixed-target/RNG/next-update and source/archive independence are exercised with synthetic3D/2action CPU inputs, genuine ENV authority and cooperative local role interfaces. Minimal HC/replay preservation is an actual component unit, not DQN sampling or full-parent qualification. Historical A inspection/export and current captured active replay remain supported; source curiosity-tail archive is distinct from active replay. K01's existing exact-stochastic/mid-episode simulator qualification limits remain unchanged, alongside supported ordinary live BANK restore.

Actual parent/population/runner/native replay/sampler/T26, completed full-parent resume/private counters/next update, final-child refusal, CLI/full/default/coverage≥70/slow/hardware/learning/CI and final54requirements/22lenses remain owed. Original28/66 release counts are unchanged. No integrated BAC release or universal shared isolation follows from this handoff.
