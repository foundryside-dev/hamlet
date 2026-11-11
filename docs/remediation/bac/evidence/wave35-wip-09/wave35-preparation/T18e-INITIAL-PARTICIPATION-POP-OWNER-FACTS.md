# Initial participation: actual POP owner facts

READONLY finite readiness capsule after durable WIP4d442680317e71a3d34f312a360ded1e7737375fc/tree81a6db2a3464c0ffc71ab5cbdea15084ba7aa626. Read approved design SHA901342a6b27ae5bacdff535c337352061fa6c55b7e1d31373be40bbcdad47234 and supplied mask-owner prose; proposed interfaces below are not implemented APIs. No source/test edits, runtime/import/probe/reflection/git/index/branch/worktree/source-copy/subagent action. Only this ignored file written. Metadata preceded rereads; existing exact-five source hashes unchanged:

| Source | Whole lines | SHA256 |
|---|---:|---|
|population/vectorized.py|2612|fcbd0b0ca5b81abcdb624276b09cbb6a8dbbb39359b0ff00b6e275847895a5a3|
|config/exploration_policy.py|1299|fbda6a2178e794747ef1e9b7771d450463051aeba53a598dd40fc334c2754e67|
|training/clock_ledger.py|48|e7b40260b027bc63fd2cb751a4fb55840564c36a38d78fca30f876d9e41473e0|
|training/state.py,readonly|263|a6f22b0b26ca6422e6a0710f9268386e8d2b7162e1a5e9a43a2decdea4c9d3e3|
|parent regression|777|6a4ab0be9cb9ef5d3bb0f977ab468ddfdf4e5e5e59f1e08ee660ffd00bd49780|

Total4999: this context has no implementation-growth capacity. ENV/mask/BANK/native facts are attributed capsules, not sixth-body reads. Original programme66/28qualified/38remaining unchanged.

## Actual reset and activation split

Public `POP.reset(*,reservation) -> (WorldRecord,WorldOwnerReceipt)` is currently one synchronous method. It authenticates the actual caller binding pinned by bind_episode_worlds/begin_batch_episode, refuses unfinished positive lanes, and holds `_step_active=True` with `_reset_stage='preparing'` around actual ENV reset and POP preparation. `_reset_record` retains the real ENV result. It owns the genuine reset observation, zeroes lane/accumulator/completion state, initializes recurrent hidden/containers when selected, updates real survival/epsilon/curriculum telemetry, **then** issues population activation through the retained actual POP issuer. Only then are `_accepted`, `_activation` and completed reset stage published to the caller.

There is no existing public reset-prepared/no-activation return, participation intent/ready receipt, decision handle or seal. By the time a caller receives successful reset, activation has already been issued. Calling new participation preparation *after* that unchanged return cannot honestly claim to precede activation issuance. Equal accepted reset requires prior completed preparation and returns the retained activation/reset record; it does not rerun POP initialization. A post-ENV preparation failure sets failed custody, clears reusable activation and requests actual ENV runtime_failure quarantine; no physical rollback is claimed.

**Minimal proposed insertion:** split the internal completed local reset preparation from final activation issuance. A direct current API can retain `(record,activation)` return while requiring explicit `retired_world_ids` on reset: after actual ENV acceptance and all ordinary local preparation, orchestrate intent/ENV prepare/ready/ENV commit/POP staged assignments, then issue activation and return. Ordinary callers explicitly pass `()` to seal all-active; no omission fallback/unsealed old route. This required keyword is a proposal for coordinated caller update, not a current signature. Alternatively expose an explicit prepared-reset public phase, but its actual reset record and POP custody must replace any fabricated accepted token.

Clarify the design's transaction boundary: `issuer.issue` and result/observation/mask allocations are fallible. No such call may sit in the allocation-free ENV-commit→POP-publication suffix. Activation issuance can be a separate guarded finalization *after* both owners agree, with existing honest quarantine on failure; it must not be described as part of an infallible two-owner assignment suffix. If a single infallible suffix including activation is required instead, its preallocation/unreleased-capability gating needs explicit coordinated review. Do not simply issue a usable activation before the pending decision.

## Actual owner state and representability

| Live POP state | Existing meaning / consequence |
|---|---|
|`current_obs`|Mutable public float32[N,D], initially zero then actual owned reset/returned observation; main previous-observation equality uses this field.|
|`episode_step_counts`|Mutable public long[N], counts actual eligible returned transitions.|
|`episode_completed`|Mutable public bool[N]; can represent inactive/completed with no event, but no current public initial-retirement method sets that state.|
|`episode_completions`|List[N] of actual completion or None; a zero-count retired B must remain None.|
|`_episode_participants`|Private set of row indices accumulated from genuine successful claim masks; failed attempts are quarantined, not healthy completion.|
|`_completed_outcomes`,`_published_events`|Actual positive-survival events and retained canonical publication data; no event is made for survival0.|
|`_batch_participants`|Retained positive participant roster after actual count/claim-history agreement, finalized participants and ENV-done nonparticipants; drives partial/delayed batch commit.|
|`_episode_reward_totals`|CPU float64[N,4], actual canonical total/extrinsic/intrinsic/shaping accumulation.|
|`_episode_entropies`,`_episode_entropy_present`|CPU float64[N]/bool[N]; real eligible Q-policy snapshot only.|
|`current_episodes`,`rollout_hidden`|Recurrent real transition lists and h/c; empty retired lane has no list rows and must not fabricate training or hidden reset events.|
|`_accepted`,`_reset_record`,`_activation`,`_population_issuer`|Actual live token/reset/issued owner capability custody, not portable reconstruction.|
|`_owned_episode`|Actual caller batch/horizon/ordered IDs/sequences pinned before reset.|
|`_vector_steps`,`_vector_stage`|One actual identity-only step handle registry with owned candidate; participation must refuse a prepared or executing step.|

Partial retirement can be represented by ENV-done B plus `episode_completed[B]=True`, count0, completionNone, zero accumulators/entropy-presentFalse and no B event/claim. `_finalize_episode` already returns None for completed or zero-count lanes. Subsequent real A-only claims/steps can populate A; genuine positive A completion then matches `_retain_participant_roster` with B actually retired in ENV. No EpisodeCompletion/LaneOutcome0 is needed. Whole-retired completed mask allTrue makes existing ordinary POP step refuse before physics; do not manufacture an empty tick to help closure. These are storage facts, **not** permission for callers/tests to write dones/completed directly as genuine lifecycle authority.

There is **no persistent POP current action-mask cache**. The pipeline queries real ENV.get_action_masks after Q/curriculum work; predecessor masks are temporary. `_returned_step` owns last returned observations/rewards/dones/components/successor_action_masks, but has no accepted/tick key and is not cleared by ordinary reset. It therefore cannot be treated as authenticated current-reset mask/previous-observation authority. New participation staging needs an owned current-accepted snapshot, not an assumed existing cache. Supplied mask-owner capsule confirms ENV also has no mask cache; its builder clears done rows last and can stage candidate_dones or derive a masked candidate from one genuine fixed-reset full mask. All callbacks/clone/validation must finish before ENV publication.

## Actual guards, locks and mutation entrypoints

POP has **no Lock/RLock or established cross-thread lock order**. Its booleans/retained-operation fields provide synchronous cooperative reentry checks, not atomic multi-thread check-and-set. `_step_active` spans actual reset, step and native installation; `_preparing_checkpoint`, `_pending_batch_commit`, `_batch_commit_active`, `_failed_step`, `_owned_reset_pending` and pending step registry add operation-specific fences. These checks do not observe arbitrary external live tensor writes. RP has its own RLock plus `_operation_active` guard around runtime calls; that lock does not protect POP/ENV fields or create a two-owner transaction lock. Supported single-owner quiescence is required; a concurrent-thread guarantee would need its actual owners' explicit lock/order protocol, not an inference from current phase checks.

Pending initial-decision guards must cover reset/equal-reset, bind_episode_worlds, begin_batch_episode, prepare_vector_step, claim_vector_step, step_population, public greedy/epsilon selectors, flush_episode, commit_episode_outcomes, all checkpoint prepare/validate/install/load/export paths and recursive participation/activation orchestration. Current `get_checkpoint()` is another exporter and calls child snapshots; do not leave it as a pending-decision escape. `update_curriculum_tracker` and telemetry synchronization mutate state and need an external-call fence or a deliberately internal staged path. Simple immutable clock/owned progress reads may remain diagnostic, but never native authority. Existing reset legitimately calls sync_exploration_metrics while `_step_active` is set; public wrappers and internal staged helpers must distinguish legitimate owner orchestration from callback reentry instead of blindly rejecting their own internal calls.

`_checkpoint_revision` changes for binding/begin/reset preparation, population steps, public rollout selection, flush, committed-batch publication and restore installation. It does not automatically change for public tensor mutation or pure prepare_vector_step; claim changes registry stage/participant history. Equality of revision is therefore insufficient to prove observation/status/mask bytes unchanged. Retain exact actual reset/token/preparation identity and independent owned before/candidate snapshots as the design requires. The scalar revision itself authenticates nothing.

## Required preselection seal check and action flow

Actual step checks completed-all/reset/activity, binds real replay, evaluates Q, computes entropy/curriculum, queries masks and selects eligible actions **before** preparing/claiming its step handle. Public greedy/epsilon selectors also run Q before any step claim. Current preparation compares predecessor to mutable `current_obs` and entry mask to mutable ENV.dones; it has no independent sealed retired-ID/activity record. Only checking a new seal inside claim would be too late to prevent selector RNG/network/replay-preparation effects after live-state tampering.

Minimal paired consumer work: retain an immutable per-accepted initial decision plus owned initial activity/observation/mask evidence; validate it at public step/selection entry before Q/replay binding/curriculum/RNG, and again at prepare/claim. Keep B irrevocably excluded for that accepted identity even if both public ENV.dones and POP.completed are tampered. Retain correlated owned previous-return observation authority for later steps; do not accept simultaneous tampering of ENV physical encoding and public current_obs just because they agree. The genuine reset record can supply initial physical observation, but not complete mutable hidden-state freshness; ENV owner must qualify the additional preservation comparisons.

Actual `_select_eligible` presents only eligible rows to runtime.select_actions, validates returned int64 geometry and scatters into full in-range filler actions. Feedforward `_rollout_q` currently evaluates the full N-row Q batch; recurrent rollout preserves inactive hidden columns. Therefore do not promise that later A-only steps perform no B Q forward; the required zero B participation/replay/curiosity work is distinct from shared Q computation. No reward/stamp/service/model/RNG call is needed for the retirement operation itself. Existing canonical real ENV handoff→actual replay→one service→vector cut remains unchanged after the new decision seals.

## Native fields and zero-tick restore

Current population format7 has exactly version,q_network,optimizer,scheduler,total_steps,exploration_state,universe_metadata,target_network,training_step_counter,replay_buffer,clock_ledger,vector_step_progress. It serializes **none** of current_obs/ENV dones/episode_completed/counts/current mask/reset stage/initial decision/pending intent or actual token authority. Replay masks are stored transition data, not live activity authority. vector_step_progress is None at fresh zero-ledger INITIAL or a portable terminal actual-step record; it cannot distinguish unsealed versus sealed before-first-tick decisions. The smaller training.state.PopulationCheckpoint DTO also contains no such fields.

Thus the current POP payload cannot encode/reconstruct a zero-count completed B or infer a participation seal from total_steps0/counts0/progressNone. Existing runtime/BANK live component restore does not supply those missing POP/ENV facts. Current POP boundary restore requires a fresh receiver and refuses bound ENV roles; full D/live simulator/native restore remains separately open. Do not advertise an unsupported live POP restore as an existing capability, but any newly supported before-first-tick continuation must preserve sealed inactivity rather than reopening a decision window.

The native owner must add/correlate explicit current decision data where that state is supported (actual portable accepted identity, retired IDs and sealed status, with exact current parser validation), or prove a real outer lifecycle inference that distinguishes these states. Live pending receipts/handles/issuer identities are never serialized or re-created as authority. Unsealed pending transaction cannot masquerade as a healthy boundary. This is a required native interface decision, not an invented existing field or a reason to reset ledger/history. Current zero-counter fields alone provide no such inference.

## Empty ruling and real evidence

Root resolved the accepted requirement directly from actual independent P2-C: **“All-empty remains separate and must not become a completion.”** Required C is mixed positive participation plus honest retired_nonparticipating. Preserve genuine all-empty abandonment/quarantine; no new normal-empty completion/release is required or proposed.

Actual POP.prepare_empty_episode_evidence authenticates current actual token/issuer, refuses pending/failed/running/reset/step/commit/restore work, requires actual POP and ENV counts0, no outcomes/recurrent rows and no vector attempt for this accepted identity, then caches real owner-issued kind empty_episode with exact accepted/participated_world_ids()/events(). It does not require episode_completedFalse, so a correctly sealed whole-retired completed mask with zero events can remain compatible. Public ENV/BANK capsules supply their matching actual activated-owner proofs and abandon_episode(reason='empty_participation') quarantine behavior. No stamp, reward, admission, decay, batch commit or fake completed release is produced.

## Finite owner handoff / blockers

Ready facts: existing fields can represent completed-zero-without-event, actual positive claim/count/roster logic can consume it, real empty proof/abandon is available, masks can stage via the separately qualified owner boundary. Concrete new work is the actual reset-before-activation split, issued intent/preparation/ready exact custody, guarded paired publication, immutable sealed participation/previous-observation authority with preselection checks, and explicit native seal correlation. Clarify final activation issuance outside the allocation-free paired suffix and supported thread/quiescence contract. Mask callback/hidden-state read purity remains its separately identified owner question, not proved by POP.

No implementation is authorized in this4999-line context. Root must reslice complete actual owning sources/tests for code/review and supply ENV/native contracts through capsules, preserving genuine C A-learning/replay/B-nonparticipation/next episode tests and all full D/E/F/B1/current-caller/final gates. No requirement/28-of66 accounting change or source qualification follows from this prose.
