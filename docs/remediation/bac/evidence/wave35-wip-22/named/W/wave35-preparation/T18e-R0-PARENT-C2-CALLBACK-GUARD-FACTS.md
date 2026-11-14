# C2 current POP callback and nested ENV facts

2026-11-14. Finite read-only supplier for `bac_parent_env_c2_prepare` and root.
Only already-charged `src/townlet/population/vectorized.py`3163 reread, current
SHA256 `6c4f7ca085f0a7db34f42bebe22f0240ed12825627c13bcffb3c0d3be3f99022`.
No new implementation body, runtime/import/test, APP edit, Git write or worktree
operation. C1 implementation is not inspected or characterized by this capsule;
C2 must consume its separately accepted API. Line references below are POP.

## Actual exclusion and callback binding

POP has NO Lock/RLock, RNG participant, lineage parameter, domain admission or
retained owner-custody scope in this source. `_step_active`, `_step_inspection`,
selection/reset/checkpoint/batch flags and revision fields are ordinary instance
state, not cross-thread exclusion. No current total POP/ENV lock order exists.

Construction367 attaches actual AgentRuntimeRegistry to ENV, then370 calls
`env.set_exploration_runtime(exploration=exploration,
claim_vector_step=self.claim_vector_step)` with the real bound POP method.
This happens before later Q/target construction and before most POP flags are
initialized. It does not grant partial-construction callback execution or
authenticate arbitrary callbacks as parent methods. The externally supplied
runtime is retained; POP does not construct/register its commit/cadence callback
closures here. Their actual fixture binding is a separate supplied contract.

`_require_operation_idle`855 rejects any `_step_active`, `_selection_frame`,
`_initial_reset`, `_step_inspection`, `_preparing_checkpoint` or
`_batch_commit_active`. It acquires no lock and verifies no thread identity.
It must NOT be indiscriminately inserted into the callbacks below: legitimate
claim/commit/cadence callbacks run while their corresponding outer POP phase
is active.

## Exact incoming callback entries

**Claim:** `claim_vector_step(*, prepared, accepted, world_ids, predecessor,
actions, active_on_entry) -> int`1384 only rejects existing `_step_inspection`,
sets a fresh inspection object, calls private claim, and clears only its own
inspection in finally. It intentionally does not require `_step_active=False`.
Private claim1412 requires exact PreparedVectorStep type, membership in POP's
own `_vector_steps` registry and `_vector_stage=='prepared'`; rebuilds a record
via `_step_record`; compares all saved identity/content; then publishes the union
of actual active participant rows and stage `executing`, returning the owned
next vector tick. It does not run physics, advance POP total_steps, service,
or turn the handle into completed progress.

`_step_record`1286 rejects restoring/selecting/initial-reset/failed/owned-reset
pending work, absent/foreign accepted identity, pending batch commit, incomplete
or mismatched clock ledger, wrong roster, tensor layout/shape/dtype/device,
nonfinite or changed predecessor, out-of-range actions and activity disagreement.
Crucially, its real nested calls are ENV.validate_accepted_episode1297 and
`_validate_owned_training`1298, which itself calls ENV.validate_initial_participation.
Thus real ENV.step -> POP.claim -> ENV accepted/participation validation must
remain legal under C2 while arbitrary peer ENV mutation from a callback refuses.
The guard does tensor reductions/equality/clones before completion; it is not a
pure CPU metadata callback. A fabricated handle cannot satisfy its registry.

**Empty proof:** `prepare_empty_episode_evidence(*, accepted) -> Any`1250 DOES
require POP operation-idle, checks owned state, then calls actual
ENV.validate_accepted_episode1254. It requires exact current `_accepted`, real
issuer, no pending batch/step/restore/failure/vector/owned-reset, zero POP and ENV
counts, no outcomes/recurrent transitions, and no vector attempt for this accepted
identity. It issues/retains actual empty receipt only once. ENV empty abandonment
may call this method, yielding ENV -> POP empty -> ENV accepted validation;
it is not permission to call empty proof during an active POP step or to turn a
zero-participation proof into positive closure/normal release.

**Committed batch validator:** `validate_committed_batch(*, batch_episode,
outcomes) -> None`1613 canonicalizes actual outcomes with freeze_lane_outcome,
then requires `_batch_commit_active`, a retained `_pending_batch_commit`, and
exact batch/content equality. No idle guard and no ENV/runtime call appears
inside this validator. Actual POP.commit_episode_outcomes1533 establishes this
state only after checking its own published event fingerprints/canonical bytes,
participant roster and matching retry request; sets active immediately before
calling runtime.commit_batch_episode1594 and clears it in finally. Healthy
publication of POP ledger/cadence follows the runtime return. A direct arbitrary
runtime call cannot manufacture pending POP authority by supplying equal-looking
events. View canonicalization can touch outcome tensor data.

**Cadence validator:** `validate_parent_cadence(*, cadence, mode, accepted,
parent_restore) -> None`1619 checks exact retained `_preparing_checkpoint`
correlation (mode, parent object identity, recursive cadence equality) when that
phase exists; otherwise compares to actual `_parent_cadence`. If accepted is not
None it calls ENV.validate_accepted_episode1627 and requires identity with POP's
current accepted token. It does NOT require general idle or reject the enclosing
restore flags. POP.prepare_checkpoint_state sets correlation3073 around actual
runtime prepare/private-init and clears it in finally. POP.install_checkpoint_state
sets correlation and `_step_active=True`3129 around runtime.install_restore,
publishes only after that return, then clears both flags. Those are genuine
runtime -> POP cadence -> ENV validation edges, not fresh parent/ENV entry
authority. The recursive equality helper can execute tensor equality.

## Participation and close: distinguish outbound calls from callbacks

There is no public POP `validate_initial_participation`, `prepare_episode_close`
or `close_episode` callback in this body. Do not invent one for C2. POP's genuine
initial-participation pairing is driven OUTWARD during reset:

* reset1108 requires idle/healthy/no pending work, genuine begun binding and
  retired subset. It sets `_reset_stage='preparing'`, `_step_active=True`, calls
  ENV.reset1147, then builds retained `_InitialReset` with exact before readings.
* `_prepare_initial_participation`1030 checks work identity/revision, issues real
  intent with accepted/world/retired/revision, calls ENV.prepare_initial_participation1044,
  validates returned observation/masks against actual geometry and old readings,
  creates clones/retired decision, and issues actual ready receipt.
* `_publish_initial_participation`1078 rechecks work/revision/physical and logical
  emptiness, calls ENV.commit_initial_participation1097, then makes assignment-only
  paired POP publication1099–1106. Activation finalization calls ENV's reading
  validator1218 and rechecks retained identity/revision/flags afterward. No
  general callback exemption follows from possession of intent/ready data.

POP._validate_owned_training943 and _validate_owned_reading957 both check owned
state BEFORE and AFTER the respective ENV validator, passing actual accepted,
participation and predecessor. If ENV became quarantined, POP latches failed
and clears activation. `_check_owned_state` itself may detect inconsistency and
call `_quarantine_participation`, which sets failed/clears activation then calls
ENV.abandon_episode(reason='runtime_failure')870, preserving cleanup error as
a note on the original Exception. Hence claim/empty/selection validation can
legitimately trigger fail-closed ENV cleanup on the reverse callback stack.
That exact cleanup path must be distinguished from arbitrary reentrant mutation;
it is not an ambient permission to reset/step/restore or reopen uncertainty.

Actual step2079 sets `_step_active=True`, calls internal vector preparation
(not public idle-guarded prepare), then ENV.step2243; claim consequently occurs
under the active POP phase. After ENV return, real service/replay/learning and
state publication run; ENV initial-participation validators2369/2382 bracket
successor/finalization checks. The method clears vector handles only on genuine
success and finally clears `_step_active`. Its error path may call runtime
quarantine then ENV.abandon_episode2116. Reset failure likewise calls abandonment1242.

Selectors2013/2044 hold `_selection_frame`, call ENV.get_action_masks, revalidate
the frame and owned reading, and clear it in finally. `flush_episode`1981 holds
`_step_active`, validates owned training, finalizes real positive-survival lane
data and calls ENV participation validation1999; failures quarantine. No source
lock is held by those flags. Reads of ENV dones/counts/meters and action-mask
tensors require the future concrete exclusion/device inventory, not a comment
describing them as observations.

Positive normal ENV close is orchestrated by the real external controller/
fixture, not by a POP.close callback. POP exposes actual completed_outcomes,
flush_episode, commit_episode_outcomes and sync_exploration_metrics; its
participant roster1521 requires positive counts matching claimed participation,
completed participants and retired nonparticipants. A close adapter cannot
substitute a direct ENV step or empty receipt for completed POP accounting.
Current first-A-only-step supplier remains the concrete nonlearning positive
fixture route; it does not migrate parent locking or runner publication.

## Finite lock-order consequences for C2

The existing legitimate cycle is CALL nesting, not a safely established mutex
cycle: POP step -> ENV step -> POP claim -> ENV validation; ENV empty abandon ->
POP empty -> ENV validation; runtime/BANK -> POP cadence -> ENV validation;
and failure detection -> ENV runtime_failure abandonment. C2 must explicitly
authenticate these finite source-controlled validation/cleanup continuations
under already-held ENV custody while preserving all current POP identity/phase/
content checks. A blanket ENV busy check would reject real claim validation;
a blanket callback exemption would admit arbitrary peer ENV mutation.

POP currently has no lock to retain or reacquire, so C2 cannot advertise a
completed total POP/ENV/runtime/BANK lock order or call private POP flags lock
ownership. Future POP producer must acquire its own real exclusion in agreed
order before these callbacks and authenticate nested reuse without acquiring a
fresh POP lock while ENV/runtime/BANK is held. Likewise C2 must not obtain fresh
domain admission under independently held ENV exclusion contrary to accepted
C1 order. Actual C1 APIs and ENV's own source determine the concrete retained
scope; this facts capsule adds no invented public scope API or lineage bypass.
