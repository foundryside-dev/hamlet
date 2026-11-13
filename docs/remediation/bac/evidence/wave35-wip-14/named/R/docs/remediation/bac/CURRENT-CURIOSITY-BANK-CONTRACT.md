# Current curiosity BANK producer contract

Current source candidate is **R72 tree prefix `c4b3765`**. The implementation below adopts managed process RNG custody, atomic native/gradient capture and payload-configured restoration. Root reports coherent1290 PASS/two unavailable-CUDA SKIP in183.0770s, independent Astra155 PASS in141.4772s and compiler CLI34 packs/35 actual processes PASS in165.8924s. The independent selection overlaps the coherent run and is not added to it. These results qualify the bounded CPU BANK/owner component; full-parent/runner/programme acceptance remains open. Historical qualification remains identified separately below. Publication of the prospective [WIP14 receipt](evidence/wave35-wip-14.json) is **PENDING** until root commits the evidence.

| Current source | Lines | SHA256 |
| --- | ---: | --- |
| `src/townlet/exploration/scoped_curiosity.py` |1414|`3b9b5476530317fc48991ba096545e3e2bad3593deb92d9caeb3a3bbab6e1027`|
| `src/townlet/exploration/curiosity_checkpoint.py` |1158|`b45ba7627b50c123de36862a678a8db98d4ab074db23d296b6cd81a05d74b6c1`|
| `src/townlet/exploration/rng_custody.py` |371|`9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`|
| `src/townlet/training/clock_ledger.py` |48|`e7b40260b027bc63fd2cb751a4fb55840564c36a38d78fca30f876d9e41473e0`|
| `tests/test_townlet/regressions/bac/test_bank_rng_custody.py` |1468|`faa687a8d5aad44799d21d992c2bb602e704dc883fd7d7d6cd55e6e8f937d664`|

This bounded five-body source inventory totals4459 lines. The qualified atomic-owner implementation is supplied through its public contract, not an additional implementation inspection. Earlier BANK1284/CP1138 and runtime tree157f141a evidence remains historical; it is not claimed byte-identical to these sources.

## Actual construction and operations

Module `townlet.exploration.scoped_curiosity`. `CuriosityBank(*, policy, descriptor, device, validate_accepted_episode, issuer_factory, report_allocation)` requires every keyword. It requires actual `ResolvedExplorationPolicy`, roundtrips owned policy/descriptor, verifies complete policy-derived descriptor, exact unique nonempty world IDs, selected geometry, float32 and CPU or explicitly indexed CUDA. None allows observation width0; other families require positive width. Constructor allocation reporting occurs before eager provider construction.

The actual parent supplies `validate_accepted_episode(accepted=token)` and an issuer bound to this BANK. The issuer's owner property alone cannot establish ENV authority: the actual parent registers this same BANK as curiosity role owner and ENV authenticates issued receipt identity/kind/owner. BANK imports no ENV implementation. BANK registers an actual lifetime participant in the sole cooperating process RNG domain. Public operations admit before its RLock, reject unrelated same-thread reentry and pass the exact held lineage to all managed private/shared owner work. Declared CUDA initialization and quiescence over raw aliases remain caller responsibilities (`scoped_curiosity.py:333`, `:346`, `:394`).

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
| `prepare_restore(*, state, mode, accepted, parent_restore, validate_parent_restore)` | destination/revision/domain-currentness-bound opaque restore handle |
| `prepare_private_initialization(*, state, initialization, parent_restore, validate_parent_restore)` | explicit fresh/clone initialization handle |
| `install_restore(*, prepared)` | one prepared publication; None |

Module `allocation_estimate(*, policy, descriptor, device)` is a pure known-tensor constructor estimate. It neither allocates a provider nor replaces constructor validation. Snapshot is diagnostic, not a restore decoder. There is no new CLI, parent coordinator or legacy adapter API.

## Families, ownership and reward/service clocks

Private scope eagerly constructs actual WorldRNGState/OwnedWorldBackend per exact ID in canonical sorted allocation order through actual BANK factory callbacks. Learning models, fixed targets, Adam/moments, gradients, RMS, Count/LRU, active tails, adaptive history/weight and named RNG streams remain independently owned. Shared scope constructs one coupled managed provider through genuine consuming `SharedWorldBackend.construct`, with world_id/rng/descriptor=None and vector_tick policy. Its constructor retains real ambient consumption; pure restore bootstrap is a separate operation (`scoped_curiosity.py:343`). All five families remain substantive: none, count_based, rnd, adaptive_rnd, icm. Shared selected seed label `legacy_shared_v1` is its current ownership label; it does not authorize obsolete artifact fallback. Global Q/action selection and epsilon cadence remain separate.

Actual `IntrinsicTransitionContext` owns predecessor/actions/successor/active_on_entry/vector_tick. BANK receives its separate stamp and actual accepted token. Whole-row geometry, finiteness, action bounds, selected float32/device/width and token/episode/eligibility bindings validate before work or retry. Active-on-entry terminal transitions receive one eligible event; inactive rows call no provider.

RND/adaptive/Count/none reward eligible successor rows; ICM uses actual predecessor/action/successor context. Adaptive raw novelty is unweighted and scale comes from current provider get_intrinsic_weight. None selects0.0; Count/RND/ICM eligible scales use resolved initial_intrinsic_weight. Inactive raw and scale are0. CuriosityReward owns raw/scales/eligibility and returns tensor clones. DAC base/modifiers and final composition remain external and must apply runtime scale once.

**Current none behavior:** eligible raw0, selected scale0 and contribution0; inactive raw/scale remain0. BANK selects zero inside its actual provider callback, and the same value reaches returned reward, pending reward, local cache and retries in both scopes. CP requires exact selected-device float32 cached zero alongside raw zero; coherent nonzero scale refuses without normalization, old-schema fallback or archive migration. The narrow T18d none-scale prerequisite was historically qualified; its zero-scale semantics are retained. The runtime/facade/global-selector component is documented separately in the [runtime contract](CURRENT-EXPLORATION-RUNTIME-CONTRACT.md); actual parent/native/learning integration and whole T18d remain owed.

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

Unexpected provider/result/receipt/cache/return-copy failures after observation/publication quarantine, including owner callback failure. Already begun Count/RMS/optimizer effects have no rollback promise. Expected off-side restore refusal leaves live destination state intact; explicit healthy checkpoint restore can recover a quarantined BANK. A quarantined partial source cannot export. Recovery reconstructs offside from healthy SAVED payload; it neither clones/services the quarantined current graph nor heals process-domain poison. Snapshot/export are observations that advance revision and stale previously prepared handles.

Empty evidence requires actual token, no participation/admissions/disposition and no unfinished phase/completion. It issues empty_episode with exact accepted token and empty participant/events tuples without changing learned/RNG/cursors/revision. Actual ENV abandonment independently authenticates registered owner evidence; evidence alone is not ENV success. quarantine_episode accepts only empty_participation/runtime_failure, authenticates current token, and is idempotent only for the same token/reason. It does not invent closure, reset, retirement or an INITIAL exemption. Parent/T26 recovery wiring remains owed.

## Initialization, diagnostics and continuation

Only explicit `fresh_private` or `clone_learned_archive_pending` prepares shared-to-private initialization into an untouched healthy INITIAL receiver. Source must be ordinary current shared INITIAL or committed COMPLETED with compatible selected behavior/geometry/seed/membership/device. Ordinary restore does not invoke conversion. Both choices preserve a complete independently owned inactive source archive, including pending rows and original gradients/history. Fresh uses actual initial native state; clone preserves learned state and inherited settled native baseline while emptying the active local tail. Full equations and compatibility rules are in the checkpoint contract.

Native baseline is a shared template, never work attributed to each world's past. Future-local counters and BANK cumulative positions start0. Clone preserves Adam/native consistency and signed RND offset. Real future service translates native clock by the baseline and emits local public clocks. None/Count have no invented predictor ledger. Both choices retain independent same-ID factory RNG continuation; no shared historical RNG becomes a private stream.

`snapshot_world` schema is `curiosity-bank-world-v2`, with exact fields `schema, scope, world_id, policy_identity, descriptor, backend, curiosity_epoch, initialization_origin, future_service_counters, accepted_identity, cursor, phase_cache, pending_step, bank_phase, historical_identity`. Private backend is native+RNG owner envelope; shared backend is coupled native provider state. Trainable private future_service_counters contain admitted_rows/consumed_rows/dropped_rows/optimizer_updates/mandatory_service_updates/pending_rows. RND/adaptive mandatory cumulative field is None; none/Count and shared future_service_counters are None. Diagnostic source/archive/counters are independently owned.

INITIAL has zero ENV cursors and no accepted/history/cache/disposition. Completed-source initialization yields private_initialized: real source episode baseline, zero local work and no accepted/closing capability, fake completion or imported disposition. Source completion exists only in origin. Next begin needs real baseline+1 ENV token. Ordinary completed restore instead retains truthful historical_identity and completion data while accepted_identity is None; absence of an accepted token does not imply INITIAL.

Current ordinary INITIAL, private_initialized, live and completed restores retain origin/epoch, full native state, explicit optional gradients, RNG, local caches/cursors and phase provenance. Unstarted initialized states are checked against the selected fresh/clone native and gradient template. Later evolved learning validates under current native/local equations. Private_initialized correlates actual parent against archived source history; later private restore correlates its current runtime. Complete current OrderedDict order/_metadata and NumPy floating RMS values survive through the qualified owner codec. Issued authority capabilities never serialize.

AllocationEstimate retains schema/operation/scope/device/dtypes/world/participant/instance counts, known bytes/components, assumptions and unknowns. Reports cover constructor/completion/restore plus initialization and origin-bearing snapshot/checkpoint archive cost. Unknown Python Count/container/integer cost, allocators/workspace and external copies remain explicit. Report refusal precedes admitted allocation; there is no scope/capacity fallback. Off-side native preparation, gradient attachment, late real runtime allocation and parent callbacks finish before one preallocated publication. Genuine parent all-child freshness/publication and quiescence remain external responsibilities.

## Managed capture, preparation and final currency

`checkpoint_state` captures shared native plus named gradients in one managed callback. Private capture uses qualified `snapshot_with_capture`: one owner scope/activation, one native serializer, gradients from the same actual Parameters, owned results and RNG capture after activation cleanup. Native/RNG envelope and auxiliary gradients remain distinct. There is no split call/snapshot or private RNG access (`scoped_curiosity.py:996`, `:1009`, `:1020`).

Both restore paths examine/report/correlate first, release examination before idle preregistration, then re-enter domain before BANK and reauthenticate exact revision/phase/pending/policy/descriptor/device/authority. A strong cohort retains BANK, every input RNG, every private owner, shared reservation and archive RNG through token outcome. Saved native v4 recipes configure actual selected offside candidates before substantive validation/load; final gradients attach after final owner install and no later model copy/load follows. Private restoration installs saved continuation separately from disposable construction work; shared restoration uses held reservation/bootstrap. See the [checkpoint contract](CURRENT-CURIOSITY-CHECKPOINT-CONTRACT.md) and [native reconstruction](CURRENT-NATIVE-RESTORE-CONFIGURATION-CONTRACT.md) (`scoped_curiosity.py:114`, `:1108`, `:1126`, `:1144`, `:1150`, `:1185`, `:1276`, `:1340`).

All runtime allocation, activation receipt, parent callback views/correlation, cohort/registry retention and destination checks finish before final BANK domain currency. Install consumes authentic destination handle custody, runs final callbacks, rechecks retained identity, validates generation/revision/ordinary-work currency, then assigns one prepared dictionary. Export, idempotent ordinary work, peer work or membership retirement can stale a released preparation even when native bytes and BANK revision are unchanged; diagnostic status/equal bytes never grant publication (`scoped_curiosity.py:1099`, `:1168`, `:1360`, `:1398`; `rng_custody.py:115`, `:320`, `:332`).

Dictionary assignment is irrevocable internal publication; install succeeds only after mandatory lease exit/device completion. No application callback, load/copy, allocation or repair follows final currency/assignment. Exit-completion uncertainty propagates, poisons the process domain and quarantines the assigned BANK. The joint parent must fail closed; no healthy rollback/retry is promised and no poison-healing API exists (`scoped_curiosity.py:346`, `:1393`, `:1409`, `:1411`; `rng_custody.py:207`, `:212`, `:231`, `:354`). Cooperating entrypoint custody does not isolate arbitrary raw library use.

Any newly retired peer membership invalidates a released token, including unrelated old graph cycles collected by GC. Positive lifetime tests collect old setup garbage before preparation, then still collect after preparation and require the entire current cohort to remain alive before real install. This is test-only isolation, not peer pinning, disabled GC or token refresh. R70 attribution preserves the genuine prior refusal; explicit retirement-staleness coverage remains (`test_bank_rng_custody.py:93`, `:331`, `:722`, `:742`, `:759`).

## Continuation and evidence boundaries

C10/K01 support learned-state fresh-episode restart; exact stochastic and mid-episode simulator trajectory remains deferred. Two complementary witnesses cover BANK: real restored ENV/reward/replay/single-service/close/release liveness, and exact reward/receipt/full BANK-native/RNG/gradient/cache continuation under identical authentic component input with receiver-local authority. The latter earns no invented ENV/population/replay work and does not require independent simulator resets to emit equal observations (`test_bank_rng_custody.py:136`, `:150`; [world identity](CURRENT-WORLD-IDENTITY-CONTRACT.md)).

The archive witness uses genuine facade conversion, source selector/cadence and earned ledger, actual parent/ENV installation, sufficient private service, and ordinary learned-origin restoration. Its Q/replay/curriculum are newly constructed, so it is not full-parent restoration. BANK's source archive is distinct from active replay; historical artifact inspection/export and current captured replay remain supported (`test_bank_rng_custody.py:294`; [runtime contract](CURRENT-EXPLORATION-RUNTIME-CONTRACT.md)).

Historical qualification is retained with its original source/scope. These overlapping selections are not added or counted as R72 reruns:

| Historical checkpoint | Qualified scope |
| --- | --- |
| W25 | BANK901: root84 and independent84; covering551 with3 CUDA skips |
| PW06 / PW07 | Historical checkpoint v1 root147/independent147; later v2 main153/independent153; separate codec16/independent16 preserves OrderedDict metadata |
| immutable47 (`b848b95a` prerequisite) | None-scale22/independent22; covering973 with3 CUDA skips; narrow prerequisite, not whole T18d |
| tree `157f141a` | Historical runtime covering1123 with3 CUDA skips and independent150; separate selector/cadence component |

Original receipt details remain in the [evidence index](EVIDENCE-INDEX.md), prior immutable contracts and the runtime contract. Historical remote CI failures/successes do not certify current R72 CI. Root reports814-source custody for each final execution, thirteen coherent and four independent actual child identities verified, all runtimes closed, and sealed Astra source/runtime review SHA256`5e93e98ce16b671125a1f8dabaf532f08a3fba4d387b4f65e4370657196f181d`. R72 manifest prefix is `873bf5e`. Global Ruff/Black734, expression/default600 and owned-two-file mypy pass; global mypy retains six oracle errors. The earlier affected15 result is an overlapping causal selection, not an additional total.

Actual full-parent replay/network/optimizer/scheduler/curriculum restoration, stable all-child publication/quarantine, POP/ordinary runner/T26/full-D, full/default/coverage≥70/slow/learning/current CI and applicable CUDA remain required. One actual-runner case was explicitly deselected from the component selection and remains required. The two unavailable-CUDA skips are not hardware qualification. No final54-requirement/22-lens acceptance is inferred. Programme status remains28 qualified/38 remaining/66 total; no integrated BAC release follows.
