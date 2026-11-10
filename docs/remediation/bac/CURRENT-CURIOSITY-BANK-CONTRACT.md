# Current curiosity bank producer contract

Bounded PW05 BANK source handoff, not integrated release or full BAC acceptance. Actual BANK901 lines SHA2563e0e4fd17d8f9588e5975769d3639a75ff6f53b43a4a4d716743b100f8200f2b; owned test1348 SHA25645cc06aa000158c4b1c26f3000bca7a2fcc87477e961e64b87039f6383ec9b73. This document describes inspected actual source and attributes execution to root/reviewer; no runtime accompanies publication.

## Actual construction and public operations

Module: townlet.exploration.scoped_curiosity. All listed constructor/method inputs are required and keyword-only.

CuriosityBank(policy, descriptor, device, validate_accepted_episode, issuer_factory, report_allocation) accepts actual ResolvedExplorationPolicy and WorldCuriosityDescriptor. It reconstructs current portable policy/descriptor, verifies complete from_policy identity, exact nonempty unique declared IDs, positive selected-provider width (none allows0), CPU or explicitly indexed CUDA device and float32 default model dtype before provider allocation. Required validator is a keyword-call callable validate_accepted_episode(accepted=token). Actual parent supplies the bound ENV public method; BANK imports no ENV implementation. Required issuer_factory(owner) creates actual WorldReceiptIssuer(owner=bank); BANK checks issuer.owner is self, and actual ENV authenticates issued receipt identity/kind/registered owner. A duck issuer's owner property alone is not authentication proof. Actual parent must register this same bank as curiosity owner.

The allocation callback receives actual AllocationEstimate before eager construction and before first completion candidate preparation; raising refuses that allocation path. Instance calls are serialized by an RLock. External runtime still owns quiescence relative to unrelated shared-policy/global RNG users and CUDA initialization.

Public operations:

- begin_episode(accepted) -> actual activation receipt.
- prepare_step_stamp(accepted, world_ids, active_on_entry, vector_tick) -> CuriosityStepStamp.
- reward(context, stamp, accepted, update_stats) -> CuriosityReward.
- admit_and_service(context, stamp, accepted) -> tuple[WorldServiceReceipt,...].
- prepare_completion(accepted, boundary_key, completion_content, outcomes, participated_world_ids) -> PreparedBankCompletion.
- commit_completion(prepared) -> actual dispositions receipt.
- prepare_empty_episode_evidence(accepted) -> actual empty_episode receipt.
- quarantine_episode(accepted, reason) -> None.
- snapshot_world(world_id) -> owned diagnostic mapping.

Module allocation_estimate(policy, descriptor, device) is a keyword-only pure known-tensor estimator; it describes the float32 profile, not a constructor or full input validator. It does not allocate a provider. BANK constructor performs the actual selected-profile validation.

## Real providers and private ownership

Private scope eagerly constructs one actual OwnedWorldBackend per exact ID, in canonical sorted order, with WorldRNGState.create from the declared descriptor/seed/device inventory. OwnedWorldBackend.construct supplies the actual candidate RNG to make_backend. No snapshots occur inside factory callbacks and no validation clone substitutes for production draws. Actual RND/adaptive/ICM algorithms, gradients, optimizer state, target/learned model storage, RMS, counts/LRU, tails/history and service state remain instance-owned. Fixed targets are private too. Same exact IDs in different banks do not share mutable objects.

Shared scope constructs one real provider with explicit world_id/rng/descriptor=None and vector_tick policy. It preserves actual grouped reward/service behavior and coupled Count/RMS effects. None/count invent no optimizer or at-clock method. Global Q/action selection and epsilon cadence remain external; BANK does not construct or advance a global selector. Required caller uses make_policy_selector separately.

## Raw reward, scale and service geometry

Actual IntrinsicTransitionContext still supplies predecessor/actions/successor/active_on_entry/vector_tick; explicit stamp and accepted token are separate BANK arguments. BANK checks actual types, full row binding and episode/eligibility correlation, provider width, float32 observations on selected device, and action bounds before provider calls. Context construction supplies finite tensors and int64 actions/bool eligibility. Eligible-on-entry terminal transitions have the same one-event path; inactive rows make no provider/RNG calls.

RND/adaptive/count/none receive eligible successor observations; adaptive raw novelty is unweighted and scale comes from actual get_intrinsic_weight. Other eligible scales use resolved initial_intrinsic_weight, including none whose raw is zero. ICM receives actual predecessor/action/successor context. Inactive raw and scale are zero. CuriosityReward owns detached raw/scales/eligible tensors and immutable event IDs; properties return clones. DAC authored base/modifiers and canonical total composition remain external and must apply the runtime vector scale once.

Private RND/adaptive ingest actual eligible predecessor rows; private ICM ingests actual one-row transitions. ServiceClock('world_eligible_admission', cumulative+1) is independent of vector ticks; successful eligible settlement increments each world's cumulative position even for nonpredictor families. Actual provider budgets/overflow/queues execute without cross-world denominator or quota. RND PredictorServiceReceipt overflow_optimizer_updates maps to mandatory_service_updates; last_loss=None maps0. ICM uses its actual ExplorationServiceReceipt fields. None/count settle phases with zero predictor counters and no clock, without repeating Count reward admission.

Private receipts are one per presented row, with exact ID/event and inactive zero metadata. Shared nonempty input produces one aggregate receipt with world_id=None and eligible event IDs. Shared trainable RND/adaptive/ICM receipts contain the actual vector clock/deltas; shared none/count receipts have clock=None and zero predictor counters. Shared all-inactive input returns an empty tuple and performs no provider call, even if queued work exists. Shared empty-call opportunities permitted by providers are deliberately not invoked by this inactive BANK path.

## Local phase and replay authority

BANK owns episode-local eligible cursor, cumulative service position, per-world bounded reward/service/completion caches, and one current batch reservation. Fresh curiosity epoch is0; ENV alone supplies accepted episode identity. First begin requires sequence1 and later begin exactly next accepted sequence after prior dispositions, retaining learned/RNG/tails/cumulative clocks. Equal same-token begin returns its issued activation receipt. No fabricated episode-zero EventId exists.

prepare_step_stamp reserves the next eligible sequence, retains inactive sequence, records actual vector_tick in BANK metadata and replays equal current preparation. WS stamps themselves have no tick field. Reward precedes service; completion requires settled phases. Whole-row validation precedes private replay as well as new work.

Private replay uses the actual per-world last event/source/tick cache. Inactive finite predecessor/action/successor content is excluded from private equality, but geometry/finiteness/action bounds/eligibility/accepted episode checks still apply. An unchanged eligible world can replay its original immutable stamp/context at its original reserved tick after another world's later activity. Cached own raw/scale/service receipt returns without provider/RNG/cursor/cache/revision changes or overwriting the newer current batch reservation. Historical inactive rows return zero-effect metadata rather than another active receipt. Changed own content, reward update_stats, original tick provenance or expired own event refuses. Private own phase-cache content remains fully retained; it is not a hash-only dedup record. Shared replay instead requires the complete current ordered batch/stamp/tick/source content to match.

Local snapshots expose own source/cache/event/receipt and own full canonical completion pair. Full bank completion correlation stays in actual prepared/committed receipt payloads. Descriptor roster/seeds/binding and accepted lane binding are separately labeled provenance; global completion data never controls private learning.

## Completion, preparation and revision

outcomes are actual LaneOutcome records in participating accepted-world order. BANK validates exact world/episode/batch/agent-row identity, actual participation and public lane_outcome_state semantics. boundary_key must be an exact int equal to accepted.batch_episode. Canonical completion_content is tuple((freeze_lane_outcome(event).payload.hex(), fingerprint)...) in that order. Hex preserves the full payload because actual receipt transport rejects bytes; fingerprint alone is insufficient.

After allocation admission and complete outcome/canonical validation, BANK retains independent complete outcome objects including owned tensor evidence. Pending equal retry compares supplied complete content and every retained scalar/dtype/shape/device/tensor field without either allocating outcome codec, report callback or owner observation. Changed content, scalar outcome or caller-mutated same-object tensor refuses. Equal returns the existing prepared token. No fingerprint-only or object-identity shortcut is used.

Actual adaptive completion prepares off-side by shallow-copying the actual backend and independently copying survival_history; it invokes the real update_on_episode_end with raw survival steps. Only history/weight candidate values return. Nested RND/model/Adam/RMS/gradients/tails are not operated on or reconstructed. Shared adaptive applies actual outcomes to one such candidate in accepted order. Expected candidate numerical ValueError becomes a distinct off-side refusal; prior learned values/cursors/caches stay unchanged and the observation revision advances. Nonadaptive completion changes dispositions only.

Prepared token is destination/revision-bound and opaque cooperative in-process state. BANK retains its own publication data separately. One pending slot blocks steps/begin/snapshot/changed completion. prepare issues kind prepared_dispositions; commit issues kind dispositions with exact fields accepted, boundary_key, completion_content, participated_world_ids, dispositions. Dispositions cover accepted lane order as completed or retired_nonparticipating; nonparticipants receive no fabricated outcome/history.

Commit checks destination/token/pending identity/revision/content before publication, assigns only prepared adaptive history and weight to unchanged real backends, publishes local dispositions/cache, consumes token and clears slot. Identical last commit replay returns the same issued receipt. Ordinary completion preserves model/optimizer/gradient/tail identities and values. No whole-native owner reconstruction is used.

mutation_revision tracks successful bank lifecycle/publication and owner observations. Snapshot advances it because WS snapshot advances owner revision. Failed preparation after actual owner observation advances revision even if no learned/cache state was published. Operation boundaries cover post-provider result/receipt/cache/return-copy work: once an observation or publication begins, unexpected failure quarantines the bank and prevents cached success/retry from continuing. Actual provider callback failure also invokes WS quarantine. Expected off-side candidate refusal avoids false quarantine. No rollback of earlier real Count/RMS/optimizer effects is claimed; all already-started work remains diagnostic evidence of a failed bank.

## INITIAL, empty attempts and snapshot limits

snapshot_world returns schema curiosity-bank-world-v1, scope/world/policy/descriptor, actual private owned backend+RNG envelope (or explicitly shared native backend), epoch, accepted value binding, cursor, phase_cache and local pending metadata. Tensors/containers are owned. INITIAL accepted_identity=None, episode/eligible/cumulative positions0, participatedFalse, dispositionNone, empty cache and no pending step. Capability tokens/issued receipts are not serialized as authenticated objects. Shared snapshots describe one coupled provider, not independently restorable per-world states.

Empty evidence authenticates actual current accepted token, requires zero participation/admissions/disposition and no pending unfinished phase/completion, and issues empty_episode with exact payload {accepted: actual_token, participated_world_ids: (), events: ()}. It does not mutate learned state/RNG/cursors/revision/phase. Actual ENV calls both registered owner evidence methods during empty abandonment and validates genuine issued receipts; receipt creation alone does not claim ENV success.

quarantine_episode is this BANK's conservative parent notification, not an ENV acknowledgement API. It requires actual current accepted identity and exact empty_participation/runtime_failure reason. Same notification retries are idempotent; changed reason refuses. It fails the bank even with pending phases/completion and permanently prevents their use. It may follow real ENV abandonment refusal: no fabricated closure, retirement, reset or INITIAL state is granted. Actual parent/T26 failure wiring and validated recovery remain required. Recovery/full restore is not implemented here.

## Resource reporting

AllocationEstimate reports scope/device/dtype/counts/components/known tensor bytes/assumptions/unknown components. Constructor report distinguishes eager model cloning peak and trained model/gradient/Adam/queue reserve. Completion report accounts for outcome transport and sequential adaptive history workspace, with no model copies. Python histories/count integer-key overhead, RNG tensors, allocators/activation/library workspace remain explicitly unknown. These are estimates, not total resident-memory bounds. Report failure refuses work; no scope fallback, population cap, capacity reduction or skipped updates is used. CPU float32 evidence does not qualify different dtype/device numerics.

## Qualified inventory and attributed evidence

| Whole source | Lines / ceiling | SHA256 |
| --- | ---: | --- |
| world_curiosity_state.py |871/1000|a639d6f927492cf0334a49f330f514b6472be75f624f24a2f1b5e8381af93b2c|
| provider_factory.py |153/400|7ca30733720017eea4a8063be0261dfd365c9547f501649bd71d937eecd5efb0|
| config/exploration_policy.py |768/1100|af8843ec1a270cfa49ec44b7ac5615d33db0d4d16b2d169d161bb4a1cd402c8c|
| scoped_curiosity.py |901/1000|3e0e4fd17d8f9588e5975769d3639a75ff6f53b43a4a4d716743b100f8200f2b|
| test_pw_private_bank.py |1348/1500|45cc06aa000158c4b1c26f3000bca7a2fcc87477e961e64b87039f6383ec9b73|

Actual5/4041; ceilings5/5000. No sixth source/helper was read by this owner.

Evidence/provenance is recorded in adjacent PW05-report.md and PW05-IMPLEMENTATION-REVIEW.md; root qualification receipts live under /workspace/bac-review-2026-11-01/qualification/ using wave25-rN artifacts. Specific received sequence: r1-negative-custody.json documents72collected/6 actual prerequisite controls PASS/66 genuine missing-BANK call failures. R2 root and independent each71PASS1FAIL exposed the tensor-bool prerequisite; independent log is wave25-r2-independent/independent.log. R3 had84collected/72PASS12FAIL: eleven new intended behavioral failures and one causal service-cadence prerequisite. R4 corrected service node proved actual optimizer/parameter/Adam change before intended retry-quarantine failure (12.4008s). These are prior-source RED/control receipts, not combined current pass counts.

For repaired901 source root reports84PASS28.4573s and fresh Sol84PASS with wrapper wall45.3494s (pytest41.24s) and custody350PASS; these overlapping runs are separate evidence. Completed R5 review in PW05-IMPLEMENTATION-REVIEW.md reports SPECIFICATION APPROVED, QUALITY APPROVED, all five findings addressed and no material fix-induced breakage (root review receipt1ece6f3c…, report with subsequent document-review appendix59b29870…). Root covering551PASS/3conditional CUDA skips36.7296s with actual child350-source/48-import/intra1-inter5 custodyPASS. Root reports Ruff/Black(56.7901s)/no-defaults601/expression PASS. Global mypy still has9 unchanged oracle/POP errors: global mypy is NOT PASS. All runtime sessions were reported closed before this document was written.

Required acceptance demonstrates all five real families in private/shared scopes; trainable private RND/adaptive/ICM have >=2 actual world1 optimizer updates/nonzero learned parameters and Adam moments across changed other-world activity/idle schedules, plus real storage/gradient/container ownership and shared Count coupling. Synthetic3D/2action learning traces and cooperative other-role fixtures are bounded unit evidence. Actual ENV token/issuer/activation/lifecycle calls are real, but this does not prove compiled matching-policy dimensions, actual RP/ENV/POP transition authorship, production nine-role effects or full ordinary runner routing.

No checkpoint import, clone, conversion or atomic full-parent restore is implemented by this diagnostic snapshot API. EPS/Count complete restore validators and PW06/PW07/PW08 remain required. Actual parent/runner native save/load/next optimizer update, RP/ENV/POP/T26 integration, shared-Q/C09, CLI/full coverage/default CI, CUDA/hardware and final54-requirement/22-lens acceptance remain owed. No original release-count increment, universal shared isolation or overall BAC closure follows from this bounded handoff.
