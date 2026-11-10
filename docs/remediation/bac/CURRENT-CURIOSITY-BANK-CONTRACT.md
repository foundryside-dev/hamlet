# Current curiosity bank producer contract

Current actual BANK1122 plus CP901 checkpoint producer handoff at bounded PW06 candidate `e52234ed9e775355ef3fbc2704ce46b13c78c6bb`, base `41e5742307ad170bc9871e0b5354b00599084da6`. This retains the actual W25 runtime/completion API and explicit shared/private families, adding current same-scope checkpoint preparation. It is not full parent/runner integration or integrated BAC release. No runtime accompanies this document; execution below is attributed to root/Astra.

## Current inspected source inventory

| Whole source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| src/townlet/exploration/scoped_curiosity.py |1122/1350|5ad7ca86549c886f3dc587535ba321df5a1a6737097af38a803cea41051938cc|
| src/townlet/exploration/curiosity_checkpoint.py |901/1200|d0e63d86e154866656db0047194048420c2a7220a2b5958de59d524cafeb8e4c|
| src/townlet/exploration/world_curiosity_state.py |871/900|a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c|
| tests/test_townlet/regressions/bac/test_pw_scope_restore.py |1498/1550|d1036d44536bafb2f8fa85b6226cb76cc6be655dd44c4c91346287ee343a776c|

Actual four-source context4392; ceilings total5000. Provider/factory/policy/ENV/VFS/outcome/HC dependency facts come from the named current source-verified capsules and published contracts. This context did not freshly inspect their implementation, old test helpers or a fifth source. W25 BANK901 evidence is historical source qualification, described separately below; it is not mislabeled as current1122 execution.

## Actual construction and operations

Module `townlet.exploration.scoped_curiosity`. All listed constructor/method inputs are required and keyword-only; checkpoint_state takes none.

`CuriosityBank(policy, descriptor, device, validate_accepted_episode, issuer_factory, report_allocation)` requires actual `ResolvedExplorationPolicy` and `WorldCuriosityDescriptor`. It roundtrips their portable validated forms, verifies complete from_policy descriptor identity, exact unique nonempty world IDs, selected provider geometry, float32 default model profile and CPU/explicitly indexed CUDA device before eager allocation. None allows observation width0; Count/RND/adaptive/ICM require positive width. Action width is positive.

The actual parent supplies the required keyword-call `validate_accepted_episode(accepted=token)`, normally the bound public ENV method. `issuer_factory(owner)` supplies an issuer belonging to this actual BANK; BANK checks issuer.owner and real ENV validates actual issued receipt identity/kind/registered owner. A duck issuer's owner property is not proof. Parent must register this same BANK as curiosity role owner. BANK imports no ENV implementation.

The report callback receives `AllocationEstimate` before constructor/completion/restore allocation admission; raising refuses that path. Instance operations hold an RLock. Parent/runtime owns quiescence relative to other owners, unrelated global RNG users and CUDA initialization.

| Method | Actual result / purpose |
| --- | --- |
| begin_episode(accepted) | genuine activation receipt |
| prepare_step_stamp(accepted, world_ids, active_on_entry, vector_tick) | owned CuriosityStepStamp |
| reward(context, stamp, accepted, update_stats) | owned CuriosityReward |
| admit_and_service(context, stamp, accepted) | tuple of WorldServiceReceipt |
| prepare_completion(accepted, boundary_key, completion_content, outcomes, participated_world_ids) | PreparedBankCompletion |
| commit_completion(prepared) | genuine dispositions receipt; exact last retry returns original receipt |
| prepare_empty_episode_evidence(accepted) | genuine empty_episode receipt |
| quarantine_episode(accepted, reason) | conservative BANK quarantine notification |
| snapshot_world(world_id) | owned diagnostic mapping and observer revision |
| checkpoint_state() | complete owned current same-scope BANK transport |
| prepare_restore(state, mode, accepted, parent_restore, validate_parent_restore) | opaque prepared restore handle |
| install_restore(prepared) | one prepared runtime publication; None |

Module `allocation_estimate(*, policy, descriptor, device)` remains a pure known-tensor constructor estimate, not a provider allocation or full input validator. Actual constructor performs selected-profile validation. Full restore schema/correlation/ownership/publication and resource rules are in the [current checkpoint contract](CURRENT-CURIOSITY-CHECKPOINT-CONTRACT.md); snapshot_world remains diagnostic rather than an alternative restore decoder.

## Actual families, ownership and shared behavior

Private scope eagerly constructs one actual `OwnedWorldBackend` per exact ID, canonical sorted allocation order, using actual `WorldRNGState.create` and BANK's actual `make_backend` callback. The callback receives the real candidate RNG, with no quiescent snapshot inside its activation or replacement validation clone used for production draws. Actual fixed/learned models, Adam/moments, residual gradients, RMS, Count/LRU, tails, adaptive history/weight and named streams remain world-owned. Independent banks/IDs do not share those mutable stores.

Shared scope explicitly constructs one actual provider with world_id/rng/descriptor=None and vector_tick policy. All five families remain substantive supported selections; grouped Count/RMS effects and actual vector-tick service budgets remain coupled shared state. The current shared seed-policy label `legacy_shared_v1` describes this selected stream ownership; no obsolete artifact loader or fallback is introduced. None/Count have no invented optimizer or at-clock method. Global Q/action selection and epsilon cadence remain external, with `make_policy_selector` a separate current selector API.

Actual `IntrinsicTransitionContext` carries predecessor/actions/successor/active_on_entry/vector_tick; BANK receives stamp and real accepted token separately. Whole-row geometry, finiteness/action bounds, selected float32/device/width, episode/eligibility binding and actual token authentication precede new work and replay. Active-on-entry terminal transitions get one eligible event; inactive rows make no provider calls.

RND/adaptive/Count/none reward eligible successor rows; adaptive returns unweighted raw novelty with actual current get_intrinsic_weight scale. Other eligible scales use resolved initial_intrinsic_weight; none raw is0. ICM receives actual predecessor/action/successor context. Inactive raw/scale are0. CuriosityReward owns raw/scales/eligibility and its properties return clones. Authored DAC base/modifiers and canonical composition remain external and must apply runtime scale once.

Private RND/adaptive service ingests own eligible predecessor rows; private ICM uses actual one-row transitions. Typed clock is world_eligible_admission at cumulative+1, independent of vector tick. Successful eligible settlement advances each world's cumulative BANK position even for none/Count. Actual provider budgets/overflow/queues are retained, without cross-world denominator/quota. RND overflow_optimizer_updates maps to mandatory_service_updates and absent last_loss to0; ICM uses its actual receipt fields. Count reward admission is not repeated during service.

Private receipts are one per presented row, exact own event/world, with inactive zero effects. Shared nonempty eligibility produces one aggregate receipt with world_id=None and original eligible event order; trainable shared receipts use actual vector clocks/deltas, none/Count no clock/zero predictor counters. Shared all-inactive input returns an empty tuple without service, including when a native tail exists. Separate provider empty-call opportunities are not invoked by this inactive BANK path.

## Episode, phase and retry semantics

BANK owns current accepted-token reference, episode-local eligible cursors, cumulative positions, per-world bounded reward/service/completion caches and one current batch reservation. Epoch starts0. ENV alone authenticates accepted identity. Real batch0 is permitted with first world sequence1; later begin requires each exact sequence n+1 after prior dispositions. Same actual-token begin retry returns the same activation receipt without mutation. Genuine next begin clears episode-local caches/dispositions/current reservation and retained historical completion/step, keeping learned models/gradients/Adam/RMS/LRU/tails/private RNG/cumulative positions.

prepare_step_stamp reserves next eligible sequence, retains inactive sequence, and records vector_tick in BANK metadata; the WS stamp itself has no tick field. Equal current preparation replays its stamp. Reward precedes service; completion requires settled work. CuriosityEventId is value identity, not an ENV capability.

Private retry uses full exact own source/content/tick and latest own phase event. Inactive finite row values are excluded from local equality, while full presented geometry/finiteness/action bounds/eligibility/episode checks still apply. An unchanged eligible own event can retry at its original tick after another world's later work; cached reward/scale/service return without provider/RNG/cursor/cache/revision mutation or overwriting the newer reservation. Changed own content/update_stats/original tick or expired own event refuses. An inactive replay returns zero-effect row metadata. Shared replay requires exact complete current ordered batch/stamp/tick/content. These caches retain actual source tensors, not just hashes.

## Completion and failure custody

Completion outcomes are actual `LaneOutcome` records in participating accepted-world order, with exact world/sequence/batch/agent-index identity and public codec validation. `boundary_key` is an exact nonnegative int equal to accepted.batch_episode, not tick or private admission count. Full canonical completion is tuple((freeze_lane_outcome(event).payload.hex(), fingerprint)...). Hex preserves complete evidence because receipt transport does not carry bytes; fingerprint alone is insufficient.

After first-preparation allocation admission and complete canonical validation, BANK owns outcome tensors/scalars independently. Equal pending retry checks every retained scalar/tensor/type/shape/device/content field against complete admitted evidence before any codec allocation, report or owner call. Caller tensor mutation, changed outcome or completion content refuses; reference identity is insufficient. Equal retry returns the actual same prepared object.

Adaptive completion shallow-copies the actual provider and independently copies survival_history, invoking real update_on_episode_end on raw survived steps. Only candidate history/weight return; no model/Adam/gradient/RMS/tail reconstruct/load occurs. Shared adaptive applies participant outcomes in original accepted order. Expected numerical candidate ValueError is a distinct off-side refusal, not quarantine; observed preparation still advances revision. Nonadaptive completion changes dispositions only.

PreparedBankCompletion is destination/revision/pending-identity-bound, with BANK-held publication data separate from token fields. Pending completion blocks steps/begin/snapshot/export. Prepare issues genuine prepared_dispositions; commit issues dispositions with exact accepted/boundary_key/completion_content/participated_world_ids/dispositions correlation. Every accepted world gets completed or retired_nonparticipating disposition; nonparticipants get no fabricated outcome/history. Commit validates custody/content, publishes only prepared adaptive history/weight plus disposition/cache, consumes the token and clears pending. Exact last source-instance retry returns its original receipt. Ordinary completion preserves live model/optimizer/gradient/tail identities and values.

`mutation_revision` tracks successful lifecycle/publication and source owner observations. Snapshot/export increments it, so observation between prepare_restore and intended install makes the restore handle stale. Existing WS observations have their own revisions. Unexpected live provider/result/receipt/cache/return-copy failures after observation/publication quarantine, including WS callback failure; no rollback of already begun Count/RMS/optimizer effects is promised. Off-side expected restore refusal does not touch active owners or quarantine them. Actual full native restore can recover a quarantined BANK from healthy saved state; exporting the quarantined partial source remains forbidden.

## Diagnostic, empty and checkpoint boundaries

snapshot_world returns schema curiosity-bank-world-v1, scope/world/policy/descriptor, actual private native+RNG owner envelope or coupled shared native provider, epoch, accepted value identity, own cursor/cache and pending metadata. PW06 adds explicit `bank_phase` and `historical_identity`. INITIAL has no accepted/history identity, zero BANK cursors, false participation, no disposition/cache/pending. Imported completed history also has accepted_identity=None, but phase completed_boundary and a separate original historical identity; it cannot be classified INITIAL merely because `_accepted` is absent. All diagnostic data are owned; issued capabilities are not serialized.

Empty evidence requires actual current token, no participation/admissions/disposition and no unfinished phase/completion, then issues empty_episode with exact accepted/empty participated_world_ids/empty events. It does not change learned/RNG/cursors/revision. Actual ENV abandonment calls registered owners and authenticates real issued evidence; issuing it alone is not ENV success.

quarantine_episode authenticates the current token and exact empty_participation/runtime_failure reason. Equal retry is idempotent; changed reason refuses. It conservatively fails BANK even during pending work. No ENV acknowledgement, fabricated close/reset/retirement or empty-as-INITIAL grant is invented. Parent/T26 notification/recovery wiring remains required.

The new checkpoint format covers all five actual families in current same scope, including complete native state, explicit residual gradients, private RNG, source/cache/cursors and current/historical phase evidence. Live mode requires actual receiving ENV token; completed mode requires retained real fresh ENV preparation plus genuine parent correlation and imports no close authority. Original completion/step binding survives receiving-order changes; callback views are independently owned, including after return. Exact OrderedDict/module metadata and finite NumPy RMS floating values are current producer data, preserved without precision/type conversion. See the checkpoint contract for exact fields and validators.

The three BANK checkpoint methods do not install network/Q/replay/scheduler/ENV/effects owners, issue a parent restored release, promise shared global-RNG serialization, or implement clone/conversion. Existing real parent authority remains ENV's public prepared-restore/restored-boundary/release protocol. Parent must prepare all children and enforce its actual joint freshness/publication boundary; no new production parent helper API is claimed here.

## Allocation reporting

AllocationEstimate keeps schema/operation/scope/device/dtypes/world/participant/instance counts, known numeric bytes/components, assumptions and unknown components. Construction distinguishes eager clone peak and trained model/gradient/Adam/queue reserve. Completion accounts for complete outcome transport and sequential adaptive history workspace without model copies. Restore adds old/new candidate/resident/native/gradient/tail/input/workspace and actual metadata/numeric storage, with explicit allowance for both possibly retained parent callback views. Python integer/Count/container cost, allocators/library workspace and external/prior callback copies remain unknown; these are estimates, not total bounds. Report refusal occurs before admitted work; no scope/population/capacity fallback or skipped update follows.

Actual late CP cache/receipt/outcome allocations run after real off-side owner/native preparation and feed the installed values. All validation, provider load, gradient attachment, container allocation and parent callback work finish before one preallocated BANK dictionary publication, preserving receiving issuer/callback/lock identity. Install rechecks its own handle/revision/live token; unexpected install failure quarantines rather than claiming fake rollback. External quiescence and parent composition remain requirements.

## Evidence provenance and limits

Historical W25 BANK901 SHA3e0e4fd17d8f9588e5975769d3639a75ff6f53b43a4a4d716743b100f8200f2b with original private-bank test1348 SHA45cc06aa000158c4b1c26f3000bca7a2fcc87477e961e64b87039f6383ec9b73 had root84PASS28.4573s, fresh Sol84PASS45.3494s wrapper, covering551PASS/3conditional CUDA skips36.7296s and bounded source SPEC/QUALITY approval after five findings were addressed. Its receipt does not claim checkpoint support at901. The provider/factory/policy/WS dependency inventories in that old five-source context are historical; they were not all re-read here.

PW06 prerequisite development preserved all five families/scopes and real learning. The original shared even10-row test trace incorrectly demanded a nonempty B2 tail; it was corrected to nine actual admissions while retaining positive LR/nonzero learned Parameters/Adam moments/>=2 updates and real tails. Root focused shared3PASS31.6338s and all17 controlsPASS22.0313s preceded genuine missing-method17PASS126FAIL27.4958s at143 collection. R2 root/Astra each75PASS68FAIL (63.8657s/72.0758s) exposed current OrderedDict/NumPy native transport before intended later assertions. R3's four real Count regressions separately proved batch0 rejection and retained first/final callback history aliases before source correction.

Exact current R4 root147PASS65.5674s and fresh Astra147PASS80.4319s; actual-source SPEC/QUALITY APPROVED, all three native-copy/batch0/callback findings ADDRESSED, report SHA862908d7b581a896532bfb4a882ad30590fb77d4b694afb755074646841ff65e. Root covering635PASS/3conditional CUDA skips101.5953s includes old BANK84 plus prior551 covering cases. These overlapping selections are separate evidence and are not summed. Root reports352source/573config/13artifact custody PASS for root3/independent1/cover2pytest identities and the actual non-pytest child352hash/48imports/intra-op1/inter-op5. All runtime closed before publication. Four cheap guards PASS, including Black48.3649s and unchanged defaults601; global mypy remains FAIL with the same9 old oracle/POP errors across197 files.

Current CPU units use synthetic3D/2action transitions with genuine ENV acceptance/issuer/activation/close/restore calls and explicit cooperative other-role interfaces. Restored actual Parameters, None/zero/nonzero gradients, Adam references/moments and source/destination storage are independently witnessed, with next real updates and final-world/refusal/allocation evidence. The actual HC/ReplayBuffer/RewardTensor cases exercise recorded rows/masks/components/clocks in minimal test-owned containers, not full DQN parent schema, actual sampler behavior or real runner/native artifact admission.

Required next work remains actual RP/ENV/POP/parent runtime routing, fresh completed full-parent captured REPLAY/private-counter preservation and next optimizer update, whole-parent final-child refusal, actual ordinary runner/native save/load, T26 durable boundary reentry, PW07 explicit clone/conversion and subsequent consumers. CLI/default repository/full coverage/slow/hardware/remote gates and final BAC acceptance remain open where not independently completed. K01's preexisting qualified/deferred exact-stochastic or mid-episode simulator scope is preserved; active captured training REPLAY is not a new simulator continuation promise. No shared universal isolation, current full-parent success, original release-count increment or integrated BAC closure follows from this component handoff.
