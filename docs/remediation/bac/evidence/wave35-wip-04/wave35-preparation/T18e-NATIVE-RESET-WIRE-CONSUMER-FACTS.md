# T18e native reset wire consumer facts

Finite static fact check from the already reviewed exact four sources (4,554 whole lines): curiosity_checkpoint.py (CP), scoped_curiosity.py (BANK), world_curiosity_state.py (WS), live_inference.py. No new source/provider/test body read, runtime/probe/import/compile/test/git action, or source/index write. Only this ignored note written. N1's proposed native checkpoint v3 and required learning-origin O are parent-supplied proposed contracts, not APIs inspected in native implementation.

Conclusion: **no known CP/BANK/WS prerequisite patch is required merely to accept ordinary RND/adaptive/ICM v3 native snapshots with O=0**, provided N1 updates actual family checkpoint/validate/load/factory together and preserves the existing named service ledger/epsilon fields consumed below. Those consumers neither hardcode those families' native checkpoint version/exact key set nor compare native Adam step to lifetime optimizer updates. This is static compatibility evidence, not a passed pipeline/type/test claim. B1 remains required for genuine reset provenance/epochs/origins; native O>0 alone does not supply that ownership contract.

## Actual fixed schemas and exact keys

| Consumer | What is fixed | Native v3/O implication |
| --- | --- | --- |
| CP.preflight (169) | Exact `curiosity-bank-state-v2` outer ENVELOPE, complete selected policy/descriptor/device, world record fields, shared native/gradients container | Native v3 remains inside existing native payload; no native family schema string or full native key set checked here. Do not bump BANK schema merely because the native payload changes. |
| CP.validate_records (874) | Private `owned-world-backend-v1` envelope exact schema/healthy/backend/rng keys and healthy=True | Required native O lives inside backend, not as an extra owned-envelope key. No full native key enumeration here. |
| WS.prepare_restore (830) | Exact owned-envelope schema/healthy/backend/rng; exact current RNG snapshot via WorldRNGState.from_snapshot | Native backend payload passes to supplied validator/load and exact roundtrip; O is not an unexpected outer key. |
| CP.validate_native, family none (946) | Exact native epsilon/epsilon_decay/epsilon_min fields | This exact native-key check applies only to none, not RND/adaptive/ICM. Adding O to none would need explicit coordination and is not the proposed N1 change. |
| CP.validate_native, count | counts/lru geometry plus disposable native load | No new count-origin claim. Count is outside proposed native v3 change here. |
| CP.validate_native, RND/adaptive/ICM | Reads established RND epsilon fields where relevant, then calls actual family validate_state(payload), requiring None return | Native producer owns v3 exact keys/schema/O/Adam semantics. No hardcoded old native version/Adam update-step equation here. |

CP.owned recursively retains portable dict fields and scalar ints; no key stripping or scalar-origin exclusion. WS._owned likewise copies native payload data. Tensor inventory/allocation paths do not interpret O. `PreparedCuriosityRestore`, PreparedWorldBackend and BANK world envelope versions are independent of native model version.

## Existing delegation and publication paths

- BANK.prepare_restore (1160) first outer-preflights/correlates, then CP.validate_records, then qualifies actual candidate native state. Thus calling CP.preflight alone is NOT full native validation; schema/O qualification happens later.
- Private restoration constructs actual selected-family provider from the current factory. WS.prepare_restore calls the BANK-supplied CP.validate_native callback, requires callback None and no mutation of candidate checkpoint or transported payload, loads native payload, requires exact checkpoint_state equality, and returns destination/revision-bound prepared state. A newly required O must be emitted by checkpoint_state, accepted by validate/load, and reproduced exactly.
- Shared restoration clones current selected-family provider with CP.clone_provider, invokes CP.validate_native, loads payload, checks exact checkpoint_state equality, and attaches gradients. It does not manually parse Adam counters.
- CP.validate_archived_native (502) constructs an actual current-factory shared provider in disposable custody, delegates native validate/load, requires exact roundtrip, and attaches gradients. Ordinary v3 archived shared origins therefore use the same native producer rules, without a CP native version gate.
- CP.validate_boundary_template (416) compares fresh_private unstarted state to actual current factory checkpoint/gradient state. A current factory emitting v3/O=0 supplies the new expected template automatically. Clone initialization compares against CP.clone_native's transformation of actual source transport; its details below still require N1 preservation.
- CP.gradient_modules/check_pairing/capture_gradients/attach_gradients (980–1038) check actual trainable module inventory, no fixed-target gradient, actual optimizer Parameter identity/group membership and gradient shape/type/device. They do not compare Adam state `step` to optimizer_updates, inspect a learning origin O, or derive manual update delta. N1's fresh/reset native optimizer must still own exactly the installed modules' Parameters.
- WS._backend_contract only requires checkpoint_state/load_state callability; WS cloning reconstructs selected policy and deep-copies the provider. No native version dispatch occurs there.

Therefore an ordinary native v3 snapshot with O=0 follows the current delegated paths. There is no identified CP/BANK old-schema compatibility adapter to remove or update for that case. External checkpoint utilities, POP/RP/runtime wrappers and unrelated consumers were not inspected by this worker; this finding does not certify them or broaden N1's source scope.

## Named native fields CP does consume

Let N be `B.shared_backend.native` for shared or `W.backend.backend` for private (world selected by exact world_id). CP.native_ledger uses:

- RND: counters/clock = N.predictor_service; pending = N.predictor_service.pending_observations.
- Adaptive: same fields under N.rnd_state.predictor_service.
- ICM: counters = N.counters; clock = N; pending = N.pending.

Existing consumed fields are admitted_rows, consumed_rows, dropped_rows, optimizer_updates, ICM mandatory_service_updates, service_position, and the clone transformation's service_clock_unit/ordinary_updates_at_position. RND/adaptive native epsilon/epsilon_decay/epsilon_min remain at native root or N.rnd_state respectively. No assumption about where N1 stores O is made here; CP currently does not read O at any path.

Private CP.future_counters (365) checks the following against inherited baseline H, not Adam step:

- F = native counters - H, nonnegative for each defined entry.
- F.admitted = F.consumed + F.dropped + pending length.
- F.consumed = F.optimizer_updates * policy.predictor_batch_size.
- ICM F.mandatory_service_updates <= F.optimizer_updates.
- Native service_position is None only with native admitted=0; otherwise it equals native admitted.
- CP.validate_records requires F.admitted = BANK world cumulative_service_position.

These equations concern predictor work conservation and BANK admission ownership. They do not say Adam S = lifetime U. N1's proposed RND/adaptive S=(U-O)+existing manual delta and ICM S=U-O are native-owned checks and need no CP Adam-equation replacement identified here. Do not zero lifetime U to make fresh Adam pass; that would break existing BANK cumulative evidence.

CP.clone_native (397), used for existing shared→private initialization, makes an owned copy of the entire native payload. For count/ICM it rewrites policy/policy_identity. When baseline exists it sets known counters to the chosen inherited settled baseline, changes clock to world_eligible_admission with baseline admitted position and zero ordinary budget, clears ICM pending or RND/adaptive pending_observations, and resets RND/adaptive predictor_service.step_counter to zero. It retains learning/optimizer payload and any newly introduced O field unless its native producer changes that field's location or meaning. N1 must ensure its v3 validation remains coherent with this existing lawful producer transformation; this capsule does not infer that service step_counter is an Adam/manual-update delta. If the new native implementation couples O or manual delta to a transformed field, that exact coupling is a concrete producer compatibility dependency to report, not a reason to guess native keys in CP.

## What O>0 does not close

Current CP has no direct O==0 restriction and no awareness of native reset origin. Therefore **do not claim every O>0 native snapshot is rejected by CP**. A producer-valid payload that retains old native ledger/cursor-compatible counters may pass existing native delegation and conservation checks even though BANK has no bounded reset provenance. Native transport acceptance is not proof of authorized same-BANK reset publication.

For a genuine learning reset, B1 remains required regardless of whether a particular O>0 payload happens to pass existing wire validation:

1. CP.preflight currently requires curiosity_epoch=0 for ordinary origin; nonzero origin currently denotes per-world shared→private initialization only. It has no current same-scope reset provenance encoding.
2. CP.validate_cache/receipt_value/validate_step decode retained events under one current curiosity_epoch. Advancing learning epoch while preserving original historical bindings requires explicit bounded historical/current epoch handling; silently rewriting old receipt/event epochs is false history.
3. CP.future_counters and BANK.admit_and_service understand only ordinary zero baseline or existing shared→private inherited baseline. O describes optimizer learning origin, not automatically admission-clock origin, pending ownership, new-run parent predictor-count basis or global RtEPS/cadence.
4. BANK needs actual parent quiescence/preparation/install authority, same actual ENV/issuer identity, off-side native/RNG preparation and stale-token handling. Native O cannot authorize any of those.

No broad pipeline/type gate is marked closed by this note. N1 may implement/test ordinary native v3 and family learning reset within its owned scope; genuine BANK/parent reset integration remains an explicit separate dependency. If ordinary native v3 fails a current delegated path, report the exact failing named field or native roundtrip invariant rather than assuming a hardcoded old native version exists in these consumers.
