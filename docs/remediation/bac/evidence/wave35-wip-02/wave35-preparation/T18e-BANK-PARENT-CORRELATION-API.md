# T18e BANK/parent clock and ledger correlation capsule

Read-only dependency capsule for the parent author. Uses only the same four whole sources and unchanged inventory recorded in `T18e-TRANSFER-CURIOSITY-RESET-CONTRACT.md` (4,554 lines). No additional source, provider/helper/test body, runtime, import, probe, compile, or git action. Only this ignored note written. The parent owns POP/RP/clock/runtime wrapper edits; this capsule does not claim to have inspected them.

Decision: keep native validation and BANK/native ledger arithmetic in BANK/curiosity_checkpoint (CP). Add one narrow producer-owned pure parent-correlation interface rather than duplicate their nested-key walking in POP. Suggested names below are new interface proposals, not existing APIs. Parent-supplied native ordinary-v2/current-runtime-v1 profiles must be authenticated by their actual producers; their outer wrapper path/schema strings are not established by these four sources. The exact BANK transport observed here is `curiosity-bank-state-v2`.

## Exact paths already established by the producers

Let `B` mean the actual BANK checkpoint dictionary, not an invented runtime wrapper path. `checkpoint_state()` constructs B (scoped_curiosity.py:954); `worlds` is a list of exact-ID records, not an ID-keyed dictionary. Select record W by `W['world_id']`. Do not infer that lane/list index authenticates identity.

| Meaning | Actual serialized path |
| --- | --- |
| BANK phase, epoch, scope | B.bank_phase; B.curiosity_epoch; B.descriptor.scope (also B.policy.curiosity_scope) |
| Ordinary/private origin | B.initialization_origin; ordinary origin is None |
| Shared native | B.shared_backend.native; shared gradients are B.shared_backend.gradients |
| Private native | W.backend.backend; W.backend is the `owned-world-backend-v1` envelope with schema/healthy/backend/rng |
| Private gradients | W.gradients, separate from native envelope |
| World cursors | W.cursor.accepted_episode_seq / eligible_seq / cumulative_service_position / participated / disposition |
| Current/historical retained step | B.step.tick; B.step.context.vector_tick when context exists; B.step.original_binding; B.step.stamp; B.step.serviced; B.step.receipts |
| Local retained original ticks | W.phase_cache.reward.content.vector_tick; W.phase_cache.service.content.vector_tick when those entries exist |
| Receipt clock | B.step.receipts[*].clock.unit / position when clock exists; W.phase_cache.service.receipt.clock likewise |
| Actual completion evidence | B.completion.original_accepted_identity / boundary_key / completion_content / participated_world_ids / dispositions / outcomes |
| Private initialization baseline | B.initialization_origin.inherited_baseline; episode_baseline; initialization; source_checkpoint |

Native selector N is shared native or the private native above. CP's exact `native_ledger` (curiosity_checkpoint.py:338) establishes these paths, without exposing arbitrary provider internals:

| Selected family | Counters | Native clock fields | Pending payload |
| --- | --- | --- | --- |
| rnd | N.predictor_service | N.predictor_service.service_clock_unit / service_position / ordinary_updates_at_position; step_counter is also referenced by clone_native | N.predictor_service.pending_observations |
| adaptive_rnd | N.rnd_state.predictor_service | N.rnd_state.predictor_service.service_clock_unit / service_position / ordinary_updates_at_position; step_counter likewise | N.rnd_state.predictor_service.pending_observations |
| icm | N.counters | N.service_clock_unit / service_position / ordinary_updates_at_position | N.pending |
| none, count_based | No predictor ledger exposed by native_ledger | No predictor service clock claimed | No predictor pending payload claimed |

Referenced counter names are admitted_rows, consumed_rows, dropped_rows, optimizer_updates; mandatory_service_updates is additionally read from ICM counters. CP deliberately represents RND/adaptive inherited mandatory baseline as None. Do not guess a native RND cumulative overflow/mandatory key: the inspected BANK maps each live receipt's `overflow_optimizer_updates` attribute to receipt.mandatory_service_updates, but this does not establish a serialized cumulative field. Likewise, no native Adam tensor `step` is a parent clock.

## Existing validation division

- `preflight` (CP:169) validates exact current envelope/policy/descriptor/device/scope/phase; `validate_origin` (446) qualifies shared-to-private source, baseline, epoch and episode relations; `validate_records` (874) validates cursors/caches/step/completion and private native/BANK ledger correlation.
- `validate_native` (946) owns the bridge to actual native validation. None gets exact epsilon fields/bounds; count gets bank geometry plus disposable load; selected RND/adaptive/ICM use their producer validator, with additional RND epsilon schedule/bounds. `capture_gradients`/`attach_gradients` own module inventory and actual Adam/Parameter pairing. Parent must not reproduce those checks.
- `match_live` (CP:244) requires actual receiving accepted values/order. `match_parent` (256) checks an actual `WorldRecord(kind='prepared_restore')`, parent world snapshot, accepted cursors, VFS context, and INITIAL/COMPLETED closure evidence. `_correlate_parent` (scoped_curiosity.py:1056) gives the actual parent validator an owned B view, requires None return and no view mutation. Preparation calls it twice; final installation authenticates actual accepted authority when live.
- These existing parent correlation checks do NOT compare parent total_steps/predictor counters with retained native clock or context ticks. A new pure producer correlation helper is needed for that missing relation. `future_counters` exists but is an internal arithmetic helper, not a public whole-runtime parent-correlator. `snapshot_world()` exposes diagnostic future_service_counters but observes native owners and changes revision; it is not a pure validation substitute.

## Exact private arithmetic already owned by CP

For trainable family, take native counters C, pending row count P, and baseline H. With ordinary origin, H is zero for admitted/consumed/dropped/optimizer; ICM mandatory is zero, RND/adaptive mandatory is None. With an initialization origin, H is exactly origin.inherited_baseline as independently derived/validated against its shared source.

CP `future_counters` (365) computes F[name] = C[name] - H[name] for non-None baseline entries and requires nonnegative values. It proves:

- F.admitted_rows = F.consumed_rows + F.dropped_rows + P.
- F.consumed_rows = F.optimizer_updates * selected predictor_batch_size.
- For ICM, F.mandatory_service_updates <= F.optimizer_updates.
- If native position is None, C.admitted_rows = 0; otherwise native service_position = C.admitted_rows.
- `validate_records` then requires F.admitted_rows = W.cursor.cumulative_service_position.

At a real private admission, public receipt clock position is old cumulative_service_position + 1. Native receives that public position plus H.admitted_rows when initialization origin exists (scoped_curiosity.py:645). Do not compare this private native position with parent vector tick; the units and inherited basis differ.

`inherited_baseline` (CP:347) uses source consumed/dropped/optimizer counts only for clone_learned_archive_pending, with H.admitted = H.consumed + H.dropped. Fresh_private has zero H. The archived shared pending rows are not cloned into private work. Each clone has inherited settled learning, but a new parent run's predictor-update count must not count that inherited learning once per world. For a parent counter explicitly defined as new-run native optimizer operations, CP should supply/check sum over private F.optimizer_updates, rather than sum raw C.optimizer_updates. A parent counter with a different start epoch requires its own authenticated baseline: no guessed subtraction.

Shared current-native totals can be compared only to parent counters declared in that same run/baseline basis. Do not sum shared totals once per W; there is one grouped provider. Never count origin.source_checkpoint again as current service. The parent must say whether its predictor counter counts all native optimizer operations, only ordinary updates, or calls; CP must not silently equate these. Overflow/mandatory work means calls and optimizer operations are not generally 1:1.

## Vector domain and retained phases

Parent provides its authenticated current vector domain, including the actual `total_steps + 1` candidate bound used by the parent step protocol. CP does not derive parent total_steps from epsilon, completion count, accepted episode count, provider step_counter, or service_position. The caller supplies a bound representing the specific snapshot/prepared phase; CP must not silently reinterpret an uncommitted candidate tick as an executed step.

Correlate nonnegative original ticks of B.step.tick, non-None B.step.context.vector_tick, and every present current-run reward/service content.vector_tick against that supplied domain. CP already requires context.vector_tick = step.tick, cached event content equality, original world/episode binding, and serviced-step receipt correspondence. Preserve original ticks under private lane permutation: `project_step` changes row order, not vector_tick (CP:1058). A local cache may be older than the current step due to inactivity; no equality to latest parent tick is justified.

Shared active trainable receipt clock position is its original content vector_tick (CP:714). Reached current shared native vector service_position may be behind parent maximum because inactive ticks do not call the provider; own retries may retain the same reached position. Thus validate the actual native vector unit and an upper bound for a non-None reached position, not equality to parent current tick. Native ordinary budget at that reached position remains producer-validated; a parent's later tick is not evidence to reset that budget. ICM shared service is invoked without an explicit vector_tick argument in the observed BANK (scoped_curiosity.py:659); the native producer must confirm its serialized unit/position semantics before CP applies a shared vector bound to it. No invented ICM per-call/vector identity.

Private public receipt positions instead equal W.cursor.cumulative_service_position at their retained local service cache, and may lag other worlds. Native private position includes H; compare through the existing CP equations above. Historical source archive ticks/budgets belong to the source's original domain, not automatically the new parent's domain. A fresh private run initialized from a late shared source must not reject that archived source because its old tick exceeds the new parent's total_steps + 1. Its source is separately native/parent-qualified; current local clocks and F counters use the receiving run's basis.

Phase conditions actually enforced:

- INITIAL: no dispatch/step/completion; each world has empty cache and zero accepted/eligible/cumulative cursors. An initialized-from-shared-INITIAL origin may exist; clone inherited native state is not evidence of local work.
- private_initialized: explicit private origin only, source was shared COMPLETED; no local dispatch/step/completion/cache, local eligible/cumulative = 0, accepted cursors equal source episode baseline. Native inherited state need not be zero. Actual parent preparation correlates the archived source closure, not a fabricated new local completion.
- live_episode: actual token, exact dispatch identity; disposition None and no completion cache. B.step may be absent, reserved, rewarded/unserviced, or serviced. Reward-only reservations are not admitted yet: event eligible_seq can be cursor + 1 while native/BANK admissions have not advanced. Do not demand a native service receipt or position equal to such a reservation tick.
- completed_boundary: committed real completion, no live dispatch; retained step if present is serviced and bound to original completion identity. Participants/dispositions/outcomes and cache content remain real historical evidence. A completed episode need not consume all pending predictor rows.

Nonpredictor none/count and inactive rows have no trainable service-clock effect. Receipt absence/null clock is valid in those cases; do not invent a zero native service position as evidence. `receipt_value` (CP:550) validates active trainable receipt admission count against its actual grouped event count; this is not a 1:1 optimizer update promise.

## Minimal additive public correlation interface

Proposed BANK entry point, name illustrative:

`validate_parent_snapshot_correlation(*, state, parent_domain) -> None`

The receiver supplies its known policy/descriptor/device internally. Parent supplies an immutable, strictly validated domain containing (1) actual vector tick bound and phase semantics, (2) parent predictor-count value and explicit metric/basis/start epoch, and (3) any real run-baseline evidence required by that basis. The outer current-runtime-v1 owner extracts its own actual fields, authenticates them, and calls this helper; it never walks provider internals. Neither EPS nor diagnostics authenticate this domain.

CP owns all exact BANK paths, origin selection, local/inherited arithmetic, current-versus-archived tick selection, scope aggregation and comparison. Native producer owns any additional normalized shared clock/counter projection if CP cannot establish it from the current native schema without duplicating native logic. The helper must be pure with respect to receiver, supplied state and ambient RNG: no owner snapshot/call/revision change, restore/install, factory allocation, or source mutation. Return None or raise; no new authority token. Existing prepare_restore/native validators remain responsible for complete semantic native validation; this correlation helper cannot bless an otherwise invalid native state. It can run as part of the existing parent callback, with full preparation still doing native validation before publication.

Avoid expanding its API into a generic reset or arbitrary native introspection service. If the actual native ordinary-v2 producer already exposes a pure validated normalized service-accounting projection, reuse it; none is demonstrated in these four source bodies. If not, add the smallest family-owned projection needed for the shared clock/optimizer metric. Do not add guessed serialized keys or equate service step_counter with parent total_steps.

Required finite correlation tests (unrun): current shared position behind current parent; inactive-only ticks; same-position retry budget; private clone inherited counts excluded from new-run parent count; fresh private late-source archive outside receiving domain; reserved reward-only step; completed underfull pending tail; count/none zero predictor effects; forged future original context/cache tick; mismatched private baseline/native admission; parent counter with wrong metric/basis; actual current-runtime-v1/native ordinary-v2 integration through producer entry points. Keep native internal malformed-state tests with their producer, not duplicated in POP.

## Reset handoff to ROOT/Astra

Use additive same-BANK native-qualified prepare/install reset, preserving actual ENV/issuer identity, global RtEPS/cadence, accepted cursors/real receipts, private learning epoch and honest native clock/ledger origins. Preserve pending obligations losslessly or identify the exact native/geometry semantic conflict for the owner; no fallback adapter, scope conversion, forced new BANK, hidden service, or new 1:1 gate. Global RtEPS is authoritative runtime state; provider epsilon is native diagnostic transport, not a second schedule owner. A fail-before-Q-mutation intermediate transfer WIP is safe but does not close the reset-capability dependency. No scope-removal proposal is selected. ROOT will obtain Astra review of the additive native contract before producer implementation; this note performs neither review nor implementation.
