# C3 restore composition v3 — concrete additive producer contracts

2026-11-14. **Proposed design; independent review required before APP implementation.** This finite revision addresses the exact v2 review requests. It preserves the conditional segmented idle choreography, actual parent/cadence comparisons and original18 G3/G4 obligations. It does not reopen BAC design, change C2's separate qualification, grant blanket reentry, or claim an implemented outcome/attempt API.

Inputs: `env-independent-design-review-v2.md` SHA256 `3b348e8d60732309fc22077ff91b8765bb9bd6448b53fc61ca32772dadbb7280`; `core-currency-supplier-v1.md` SHA256 `b24eab4821f3b5bf73d663acd8dc5e8733838e93b9bb2327cf727f3b72a7395b`; historical `producer-facts-v2.md` SHA256 `8593de9209fe8eea39bcae036704d1aa0a749f82fd55ab3a976d562e5400cd23`; accompanying `ownership-capsule-v1.md`. The owned source packet is exactly RP1343/BANK1492/parent_custody239/world_roster312/VFS254 = **3640 lines / five whole bodies**. ENV/helper/core/CP facts below are explicitly attributed suppliers, not additional source inspection. No runtime, APP edit, branch/worktree/copy/Git operation or new agent.

## 1. Design selection and scope

Select an explicit, opt-in, source-owned **ENV restore attempt with two explicit child profiles: direct BANK, or runtime plus its BANK**. Its additions are: (a) a pure ENV preparation-currentness method; (b) source-issued installation outcome observation for BANK/runtime; (c) exact attempt methods, mandatory correlation adapters and terminal ENV fencing. This follows the already-selected segmented direction; it is not a choice to replace standalone restore. Root explicitly confirms both paths are required integration, including approved manual/direct-BANK INITIAL/COMPLETED receiving composition. No fabricated runtime or fallback dispatch is permitted.

A bound parent invocation cannot span idle replacement-cohort registration: parent_custody18,115–135,183–239 and BANK1348–1436 establish that conflict. Ordinary `authority.restored` cannot run under unbound ENV retention. Reusing effectful `_bound_env` is therefore not a repair. Early release before genuine child preparation is also not selected: authentic saved bytes alone have not earned the actual candidate/ledger/cadence comparisons. The proposed additions let the real comparisons run, then genuinely issue the release at an ordinary ENV cut.

The new attempt is finite: one prepared world, one selected actual child profile, one child preparation, one native/(when present)runtime installation and one world installation, followed by one fixed component-finalization callback. It is not arbitrary multi-owner rollback or an all-child transaction engine. The original owner remains responsible for the real journal/ledger and other-child obligations; the callback must be the real owner continuation and is qualified against those obligations. A successful attempt does not substitute for outstanding POP/replay/T26 qualification.

## 2. ENV pure preparation check: selected API and exact predicate

**New public method:** `EnvParentCustody.validate_prepared_restore(*, prepared: WorldRecord) -> None`.

Only the actual live retained **unbound** ENV scope can call it. It authenticates current PID/Thread, its actual issuer registry entry, current retained scope, held ENV exclusion and pinned owner identities. It refuses an operation-bound scope, active ENV method/reverse continuation, expired/reentered scope or publication/cleanup in progress. It neither infers callback origin nor adopts a lower owner's active RNG lineage.

At genuine `prepare_world_restore` issuance, add an issuer-owned seal linking the exact record, original private `_payload` identity and prevalidated receiving metadata. Authenticate the scope and original seal/weak registry BEFORE inspecting the supplied record. Then check the exact concrete issuer-created record, original kind, `_owner is ENV`, current generation and registry identity, original private payload identity and no failed-attempt invalidation. Record identity, not equal payloads, is authority. Seal storage must not strongly retain dead records through weak-key value cycles.

The predicate's receiving metadata is the following **supplied current ENV mapping**, checked through source-owned builtins/identities rather than public property access or arbitrary equality:

| Actual metadata | Required check |
| --- | --- |
| `_world_phase`, `_world_generation`, `_world_revision` | `fresh-bound`, exact integer0, exact integer0 |
| `_world_authority`, its `_env` and `_owner`; `_world_role_owners` | Exact current bound authority, receiver and boundary owner; original actual nine-role mapping and each pinned owner identity |
| `_world_accepted`, `_world_reset`, `_world_reservation`, `_world_release`, `_world_closure`, `_world_frozen`, `_world_consumers`, `_world_restored`, `_world_vfs_pending`, `_world_last_closed`, `_world_saved_binding` | All None |
| `_participation_pending`, `_participation_committed`, `_participation_reset_state` | All None |
| `_participation_busy`, `_participation_failed` | Both False |
| `_world_cursors` | Actual receiving world-ID keys, exact integer0 values |
| `_world_bindings`, `_world_equal` | Empty |
| `_world_roster`, `_world_seed`, `_world_ids`, `_world_identity` | Original receiving roster identity, actual seed, exact ID tuple and semantic identity sealed at preparation |
| `_exploration_runtime`, `_claim_vector_step`, `_exploration_bound` | Actual binding/absence remains as sealed/pinned; ordinary preparation does not acquire a new runtime-binding prerequisite |
| Approved Packet M manual ownership, when present | Authenticate and pin the actual receiving session/population binding and its source-owned healthy quiescence predicate; preserve its supported fresh-bound restore path. Do not infer absence/quiescence from phase or fabricate a runtime. The M supplier must map its proposed exact fields before implementation; no such fields are asserted already implemented |
| `_world_bootstrap`, `_world_records` | Preserve legitimate issued uninstalled bootstrap and multiple preparations/releases; neither must be empty |
| New attempt association/failure metadata | The selected record may be in this live attempt's escrow; a failed/revoked association or terminal composition fence refuses |

The WorldRecord supplier establishes owned frozen containers, accessor copies and potentially mutable cloned Tensor leaves/opaque capability identities. Therefore the seal does **not** claim deep primitive immutability. Store an independent immutable metadata projection at issuance; authenticate its link to the original payload identity without traversing contents. Never call `payload`, `__getattr__`, `same_value`, `_bound_env`, `_check_committed_participation`, `_require_phase`, encoding, Tensor equality or VFS reconstruction inside this pure path. Full portable validation remains at original preparation; real content/ledger comparisons remain separate.

Both success and refusal cause no mutation, sticky failure, allocation of a capability, callback, device/RNG operation, admission, lock acquisition, quarantine or registry change. No new device/profile restriction or simulator physical-state immutability predicate is introduced. Healthy fresh-bound affordance helpers remain supported outside the explicitly exclusive attempt. Private/raw mutation detection is not promised.

## 3. BANK/runtime installation outcomes: concrete creation, reads and lifetime

The following are **new additive methods**, with the same meaning on each real producer:

- `bank.restore_installation_outcome(*, prepared) -> RestoreInstallationOutcome`
- `runtime.restore_installation_outcome(*, prepared) -> RestoreInstallationOutcome`
- `outcome.read() -> RestoreInstallationResult`

The actual preparation producer allocates its observation cell and opaque outcome object BEFORE the final token issuance/publication-sensitive region. Each genuine prepared handle owns exactly one such observation; the getter only authenticates the exact currently registered handle/issuer and returns that existing object. It is an observation lookup, not an operation-decorated validation/export and not a core status call. It cannot enter admission, take a new RNG invocation, allocate native state, refresh currency or call user code. The getter may use only the actual producer's existing local lock for its registry lookup; it acquires no domain/ENV lock afterward and authorizes no mutation. In the attempt it runs under the already-held outer gate/ENV exclusion (and runtime lock for that profile), so lock order remains domain -> ENV -> runtime when present -> BANK. It refuses active incompatible public-call/reverse state and foreign creating PID/Thread before registry work. A copied/unregistered/foreign handle refuses. Existing standalone signatures and return values remain unchanged; ordinary callers need not request or inspect an outcome.

`read()` authenticates its actual issued outcome and creating PID/Thread, then returns the current immutable, preallocated result. Reads are permitted before entry (`pending`) and after sealing, including after owner failure/domain poison. A pending or in-progress result is NOT success or certified no-publication. The result is observation only: no install permit, lineage, currentness token or retry authority. A sealed result never changes. It remains readable for the outcome object's lifetime; it does not require the prepared handle to remain registered or reusable. No exception traceback or user callback is retained.

### 3.1 Exact result fields and producer cuts

`RestoreInstallationResult` contains these immutable values, rather than one caller-set success bit:

| Field | Values / source meaning |
| --- | --- |
| `status` | `pending`, `in_progress`, `sealed` |
| `call_entered` | Actual source install entry reached; no inference from caller intent |
| `operation_entered` | Real BANK invocation body admitted; runtime result incorporates BANK's actual value |
| `handle_consumed` | BANK's actual registry removal at1480; runtime result additionally records its own handle disposition separately as `runtime_handle_consumed` |
| `bank_publication` | `none`, `complete`, `uncertain`; complete only after actual dictionary publication at1489 returned |
| `runtime_publication` | `not_applicable` for BANK; otherwise `none`, `complete`, `uncertain`; complete only after the actual runtime suffix1317–1319 returned |
| `completion` | `not_entered`, `succeeded`, `failed`, `uncertified`; based on the actual own invocation's exit/completion observation, never exception text |
| `returned_normally` | Whether the whole represented install returned normally after its real required suffix and completion |

Before reaching a potentially publishing assignment, source bookkeeping conservatively moves that dimension to `uncertain`; only returning past the actual assignment moves it to `complete`. This distinguishes injected preassignment failure, partial/uncertified publication and a completed assignment. Hook locations and preallocated references must not insert a user callback or a new fallible serializer/native read after publication. Source exceptions remain primary.

BANK anchors: `_admission`364–390 owns the actual invocation/completion and detects publication changes; `_restore_publication`1438–1473 prebuilds the replacement dictionary with `_publications+1`; install1475–1492 removes the token before correlation/currentness, publishes at1489 and can fail later. Instrument the existing public guard/admission chain as well as its body so refusal before invocation is distinguishable from a consumed no-publication body refusal. Observe actual invocation completion even on exception. Do not infer completion success from no thrown CUDA error or count equality.

Runtime anchors: the existing install1302–1319 has its own early freshness/cadence checks, forwards the actual BANK install, then publishes its own selector/cadence/revision/handle suffix. Its result incorporates the actual BANK result; if runtime refuses before forwarding, BANK remains pending and runtime certifies that it never forwarded. If BANK publishes then raises at completion, runtime suffix is absent and completion is failed/uncertified. A runtime suffix fault after successful BANK completion is partial joint publication even though BANK is healthy. No new post-BANK comparison callback is added.

### 3.2 Storage and release requirements

Use an owner-controlled nonserialized outcome registry whose identity is preserved across BANK dictionary replacement; never store a new observation only in the displaced dictionary. Allocate result variants/recording slots before token sealing. The preparation entry retains the observation through installation; the active install wrapper retains the cell locally across registry removal and dictionary publication. The runtime publication retains its actual BANK observation, so a consumed BANK handle does not destroy evidence.

The outcome object may strongly retain its actual issuer and original handle for its advertised lifetime. The issuer registry must use weak outcome keys; its value/cell must not retain the outcome or its handle, so it cannot keep an externally abandoned observation alive through a value cycle. Active preparation/install already supplies the necessary strong execution references. After sealing, remove transient invocation/candidate/scope/callback references from the observation cell; the immutable historical result remains. Dropping an observation is ordinary lifetime release, not a core unregister/refresh operation. Avoid introducing owner-lifetime changes between token seal and install by retaining all actually needed producer roots through that cut.

The exact source implementation of these recording cuts needs an independent BANK/runtime review. This design specifies a new supplier API; it does not report it as already implemented or treat a wrapper-created fake receipt as evidence.

## 4. Exact ENV attempt API and source-owned correlation integration

**Two new explicit public factories on the genuine boundary authority:**

`authority.restore_bank_attempt(*, prepared: WorldRecord, bank, validate_parent_restore, finalize_component) -> context manager yielding WorldRestoreAttempt`

`authority.restore_runtime_attempt(*, prepared: WorldRecord, runtime, validate_parent_restore, finalize_component) -> context manager yielding WorldRestoreAttempt`

Each factory enters and owns the continuous **idle** domain admission for its lexical lifetime. It authenticates the actual boundary authority, exact prepared ENV record/seal and selected genuine child association. Direct BANK authenticates the actual receiving curiosity owner and preserves an actual bound manual population/session, where present. The runtime profile authenticates the actual receiving runtime and its BANK association with the receiving curiosity owner. It pins those genuine owners and registers one attempt for this receiver. It refuses nesting/concurrent attempts on that receiver. It does not make ordinary world preparation or direct-BANK composition depend on runtime binding. It must check actual owner association, not role-name/type guessing or fabricated replacement roles. A new pure `runtime.validate_restore_receiver(*, curiosity_owner) -> None` supplies the exact runtime-to-BANK owner check under already-held exclusion; it must check its actual child identity and real owner binding, not enter a native invocation.

The callbacks are fixed at creation: `validate_parent_restore(*, prepared, curiosity_state) -> None` is the existing real content/ledger comparison; `finalize_component(*, restored: WorldRecord) -> None` is the actual receiving controller's final journal/ledger continuation. Neither is interchangeable with a no-op fixture that claims authority. These remain explicit cooperative callback boundaries: source adapters prove that the required check and real supplied callback were called at the required cuts, not that arbitrary Python comparison code internally did honest work. Consumer qualification must use and test the genuine owner functions.

The concrete attempt methods are:

| Method | Enforced action and valid predecessor |
| --- | --- |
| `prepare_child(*, state, mode) -> None` | From acquired world preparation only; forwards exactly one genuine selected BANK or runtime `prepare_restore` with this exact parent, accepted=None, requested supported mode and its source-owned parent adapter; retains real handle and outcome internally. Factory selection fixes the exact producer; no method probing or fallback |
| `prepare_private_initialization(*, state, initialization) -> None` | Alternative to the preceding method, not an extra preparation; forwards the existing private-initialization API and actual selected supported initialization mode with the same enforced parent/adapters |
| `issue_release(*, boundary) -> None` | After real selected child preparation; outside ENV retention calls genuine `authority.restored` with this actual prepared record and the actual supplied earned boundary; escrows its exact returned release |
| `install_child() -> None` | After release issuance; reinstates unbound ENV retention and mandatory correlation integration, forwards exactly the selected retained BANK/runtime handle once and reads its real outcome |
| `install_world() -> None` | Only after successful sealed selected child result; outside ENV retention invokes ordinary ENV installation using the exact escrowed pair and one-use internal attempt authorization |
| `finish() -> WorldRecord` | Only after actual world installation; calls the fixed genuine `finalize_component` once, requires None, marks COMPLETE and returns the actual installed release |
| `abort() -> None` | Idempotent terminal failure disposition selected from source-owned observations; accepts no caller classification, success bit, replacement handle or rollback state |

Actual argument names for forwarding to existing producers must remain their current signatures; these proposed attempt method names are NEW, not a backward-compatibility dispatcher. No unsupported mode is invented. This fresh-bound parent profile does not take over live accepted-parent or no-parent standalone routes; those remain supported and separately tested.

The attempt object is issuer-registered, nonserializable, Thread/PID-bound and usable only in its live lexical context. Its methods own all transitions and catch their own stage errors before returning to arbitrary caller code. A caught method exception cannot enable a later stage. Exiting normally before COMPLETE invokes abort; exceptional exit invokes abort and preserves the primary exception. Exit after COMPLETE releases execution authority without revoking the already-installed legitimate result. A later ordinary exact-pair idempotent world-install retry retains its current semantics.

### 4.1 Mandatory adapters; exactly the original callback cuts

Add the finite runtime method `runtime.correlate_world_restore(*, attempt) -> context manager`. It authenticates this actual source-issued live attempt, exact runtime/parent, current retained unbound ENV scope, Thread/PID and operation-idle runtime entry. It holds the actual runtime lock for exactly ONE selected prepare or install call and records a source-owned correlation overlay. It does **not** create a C1 runtime retention/operation binding, adopt RNG lineage or span an active RNG invocation through cohort registration. Its entry/exit does no new RNG operation. The overlay is outside restorable state and expires on every path. An attempt-created handle can only be installed with its matching live overlay; ordinary handles retain their existing install route.

At the runtime's actual `_correlate_cadence` cut, source code invokes the attempt's mandatory pure ENV check, then the already-bound genuine cadence comparator, then the mandatory pure check on normal return. Preserve original argument ownership, None-return, unchanged-view and revision checks. Do not replace the constructor-bound cadence owner with a user-supplied surrogate. At each BANK parent callback the exact adapter supplied by the attempt similarly checks, calls the fixed original `validate_parent_restore`, checks again on normal return, then returns None. A failure from an outer pure check cannot be swallowed by the inner comparison callback. A comparison exception propagates immediately without pretending the trailing check ran.

The normal runtime fresh-bound parent path retains BANK's three preparation correlations (1389,1394,1238) plus installation1484, and runtime's two preparation cadence correlations (1251/1240 or the actual private-init equivalents) plus installation1309. Thus seven actual comparisons remain; a healthy runtime path has fourteen surrounding pure checks. The direct-BANK profile has its real three-plus-one comparisons/eight surrounding pure checks; it does not invent runtime cadence work. It calls the existing direct BANK APIs under ENV retention, without a runtime overlay or fake delegated C1 scope. The attempt's source-owned parent adapter is still mandatory. No extra core operation is inserted. Adapters replace neither CP parent matching nor live accepted checks. Standalone initial None/None and live-parent modes keep their actual different callback behavior.

The pure validator itself never sets a sticky failure bit. The source-owned attempt/overlay catches an escaping refusal and terminates the attempt. Arbitrary user code calling a pure method and swallowing its own error is not claimed detectable; it cannot bypass the mandatory outer checks or substitute the attempt's actual handle/parent.

## 5. Escrow, terminal ingress and poison-safe failure entrypoints

Escrow both the exact prepared world record and its actual release in ENV-owned nonserialized metadata. While active, direct ordinary release issuance or installation using that preparation refuses unless it is the attempt's exact source call. Source-controlled `issue_release` and `install_world` create distinct one-use internal call identities and consume/expire them on all paths; no public permit issuer or generic reverse right exists. Multiple unrelated legitimate preparations and an already-issued uninstalled bootstrap remain valid. A failed attempt revokes only its own preparation/release associations; it does not erase unrelated registry entries.

**New enforcing ENV entrypoint:** private `_finish_restore_attempt_failure(attempt)` called only by the registered source-owned attempt. It derives disposition from the actual stage and issuer-sealed child results; no public caller can supply a safe/unsafe boolean. It authenticates the actual live lexical gate owner, current Thread/PID and attempt registration. At a runtime failure it runs under already-held ENV exclusion. At an ordinary ENV call/finalizer failure it reacquires the ENV lock after lower-owner unwind under the attempt's still-held outer domain gate, **without entering another admission or healthy guard**. It performs only preallocated assignment/invalidation operations. Its exact helper implementation and source lock order require ENV review; it must not call a normal guarded cleanup method after domain poison.

| Actual observation | Required result |
| --- | --- |
| Refusal before child preparation/installation starts, no world publication | Revoke this attempt's escrow; preserve healthy unchanged receiver where actual metadata still permits it |
| Child preparation entered then failed, without a source-certified completion observation | Fail conservatively as uncertain; do not invent a successful preparation completion or enlarge this design with a generic prepare-result framework |
| Install sealed with no BANK/runtime publication, and completion succeeded or invocation genuinely never entered | FAILED_NO_PUBLICATION; revoke escrow, preserve truthful ENV metadata and the child's actual existing health/failure flags. A consumed native handle stays consumed. This does NOT guarantee BANK is reusable: its existing failure flags still apply |
| Any BANK/runtime publication, uncertain publication, failed/uncertified completion; runtime suffix error; world error after successful runtime publication; finalizer error | FAILED_PARTIAL_OR_UNCERTAIN; revoke attempt authority and enforce terminal failed-composition fence on the receiving ENV |
| Both installations and actual fixed finalizer return successfully | COMPLETE; seal attempt result, expire execution permits; ordinary exact installed-pair idempotence remains |

Install pending/in-progress is never certified no-publication merely because no success returned. Original exceptions and real child flags survive. No rollback, silent reprepare, token replacement, automatic retry, fabricated receipt, all-child success inference or blanket poisoning of an otherwise valid native child is allowed. New optional composed attempts conservatively fence uncertain failures; existing standalone behavior is unchanged. A separately requested attempt after a proven no-publication failure must earn every currentness/health check anew and use a new genuine preparation; it is not recovery of the consumed handle.

The terminal fence is new owner state, not just `_quarantine_participation`. It needs no accepted token and cannot call `abandon_episode` to invent one. Source ingress must deny on the terminal receiver:

1. Healthy lifecycle/participation action: preparation, reservation validation, activation/reset/step, commit/validate/freeze/close and boundary installation; public action-mask and physical affordance reads/mutations/randomization that otherwise present healthy simulator outputs.
2. Healthy snapshot/export/restore: world checkpoint, new preparation, release issuance, world/VFS installation, and every old prepared/release association's attempt to become healthy authority.
3. Rebinding that could bypass the fence: boundary authority, exploration/runtime binding, runtime-registry attachment and new `bind_manual_execution`; no old dictionary, new manual session or new role mapping silently clears terminal failure.
4. Any new composed attempt or pure prepared-parent validation claiming the failed receiver is fresh-bound/current.

Preserve explicit identity/failure diagnostics and existing cooperative raw surfaces as such; do not claim to intercept arbitrary retained Tensor/manager aliases. A raw diagnostic view is not a healthy checkpoint or owner receipt. The source reviewer must map this finite ingress set to every actual public ENV method and ensure it fails before side effects. This is a necessary source mapping, not permission to invent method names or waive an existing entrypoint. Ordinary healthy fresh-bound helpers, standalone world restore/idempotence and independent runtime/BANK capabilities remain unchanged. No new general recovery API is selected; an explicitly supported later reconstruction, if any, must earn its own real owner contract.

### 5.1 Approved manual-session interaction

Approved design `../../manual-driver-design/manual-physical-driver-design-v1.md` SHA256 `5d358375b1c506a3a2f240dbbb411c8e003a26b16da2ec43f25bacd9d905b6f2` explicitly permits a fresh receiving manual session to bind at fresh-bound BEFORE genuine INITIAL/COMPLETED world restore. Its source author supplied these proposed predicates on2026-11-14; they are not implemented-source facts in this review:

- One actual ENV-retained session binds the exact population role after genuine nine-role binding, with no runtime/claim execution binding. Binding preserves fresh-bound. It is exclusive execution ownership, not evidence of entered physical work.
- Session lifetime follows that ENV/role binding across normal reset and permitted fresh restore. A fresh session has no issued/pending physical work. No additional caller acknowledgement or synthetic C3 adapter is needed. C3 seals/pins its actual binding and checks genuine quiescence/currentness under ENV exclusion; it must not reject merely because the session exists.
- Each private physical decision/receipt is tied to current generation, accepted identity, activation and revision. Restored generation invalidates old per-episode authority; a restored last-closed accepted token cannot authorize live step/close. The receiving session does not adopt historical physical ticks as current authority.
- Session step/retire must check actual active activation, absence of pending/frozen completion, exact issuer/ENV/population/Thread/PID, and ENV terminal/quarantine plus session failure/uncertainty before physical effects. A C3 terminal failed-composition state must therefore be included in the actual source-owned session ingress predicate; phase checks must not accidentally omit it. New manual binding is also fenced.

These are required M/C3 integration tests for both direct-BANK INITIAL and COMPLETED restore, normal subsequent reservation/reset/activation/physical work and failed-composition denial. M's eventual exact fields/source must be supplied to the implementing ENV owner; this review does not invent their names or require new runtime work. Existing fresh-bound restore is preserved, not made optional. The ordinary runtime profile remains separate and authentic.

## 6. Exact ordering and core currency constraints

1. The caller obtains its genuine ordinary world preparation; entering the explicit BANK or runtime attempt factory owns continuous idle domain admission, authenticates/escrows that exact record and pins the actual participating owners, including the real manual session where present. It starts no parent RNG invocation.
2. Unbound ENV retention -> actual selected child exclusion (runtime lock/correlation overlay only in runtime profile) -> genuine child preparation. BANK executes first invocation, exits to idle, registers its real replacement cohort, then executes second invocation and final token sealing. All original correlations remain.
3. Remove overlay and ENV retention while retaining the outer gate. Genuine ordinary release issuance runs with its exact one-use attempt authorization. No active ENV method or operation crosses into it.
4. Re-retain ENV, enter the exact runtime overlay only when that profile is selected, install the retained genuine child handle; read its source result without a new operation. On failure, finalize under retained exclusion before leaving it.
5. Leave ENV retention and run actual ENV installation via the attempt's one-use permit, then its fixed finalizer. On failure, perform source-owned terminal denial before the outer gate exits. Success seals COMPLETE before releasing custody.

Core supplier: final token issued at r validates inside the immediate separate install at r+1 only with matching generation/currency and a successful issuer exit. Admission ENTER drains weak retirement; EXIT does not. An extra no-draw operation still stales revision; unrelated registered-owner retirement AFTER issuer normalization can stale global generation at the next admission. Strong relevant cohort retention is necessary but not a global pin. Every such real stale refusal must remain a refusal; no refresh, ignored drain, hidden reprepare or promised success under arbitrary GC. ENV's ordinary admission-only release work itself does not advance operation currency, but its entry can drain retirement. No currentness status/export is inserted between token seal and install.

## 7. Finite acceptance and implementation packages

These are executable requirements, not results or APP authorization:

- **Ownership/purity:** use genuine INITIAL/COMPLETED records, multiple preparations, bootstrap-issued fresh-bound, public payload-copy mutation and permitted nested completion content. Show the pure predicate uses no payload access/Tensor/equality/encoding/callback/lock/admission/issuer work on success or refusal. Foreign/copied/expired records and inconsistent exact metadata refuse without mutation. Preserve supported public nested ownership semantics and no new device/profile gate.
- **Real correlations:** all16 original G3 healthy restore/reset/reorder/VFS prerequisites first; original negatives must fail at intended ledger/cadence/currentness checks, not unrelated reentry. Assert actual3+1 BANK and2+1 runtime comparisons/all14 healthy pure checks in the runtime profile, and actual3+1/eight in direct BANK. Retain independent seven-ledger/content semantics. Qualify both actual manual/direct-BANK INITIAL and COMPLETED receiving paths, actual reorder/private-initialization variants, and runtime+BANK paths. Complete the original two G4 POP/replay obligations in their own owned producer packet; this design does not declare them fixed.
- **Outcome truth:** genuine refusal before operation; consumed-handle/no-publication currentness refusal; failure immediately before and after actual BANK publication; actual completion failure; runtime suffix interruption; normal success. Check source-issued fields, no added operation/callback after publication, retained evidence across dictionary replacement/poison and honest handle consumption. A sealed no-publication result must not erase an actual BANK failure flag.
- **Attempt enforcement:** early normal exit, externally caught stage error, failure of mandatory outer pure check, replacement/no-op callback attempts, escaped preparation/release/direct install, wrong handle/attempt/Thread/PID, repeated calls and alternate release issuance. Preserve genuine ordinary idempotent install, standalone initial/no-parent/live routes, multiple ordinary preparations and healthy fresh-bound helpers.
- **Failure cuts:** after real runtime publication, fault ENV prechecks before its existing restoring try, its mutation path and the real finalizer. Check terminal fence and escaped-capability denial at every listed ingress before gate release, without fresh admission or accepted token. Confirm native state is truthful rather than rolled back or falsely poisoned. Exercise preparation completion uncertainty conservatively.
- **Core schedule:** real two-invocation/idle-cohort/immediate-install positive; own issuer-exit retirement normalization versus unrelated retirement queued afterward; actual intervening no-draw operation, membership change and completion failure. Assert real stale refusal and disposition with no replacement token. Test relevant-owner lifetime pinning separately from unrelated global GC.
- **Exclusion/lifetime:** real peer-thread waiting across both ENV-retention gaps; outcome lookup/read does not drain or advance core state; observation garbage collection has no hidden strong-registry retention; primary exception preserved; no healthy result escapes an incomplete attempt. CPU evidence is not native hardware/all-child/global closure.

After independent design review, use fresh measured source packets, each <=5 whole files/5000 lines: (A) ENV/helper seal and pure check with focused tests; (B) BANK/runtime outcome production and runtime correlation overlay with focused tests; (C) finite attempt owner/ENV ingress integration and genuine consumer tests. The exact source files/line ceilings must be measured by root before authorization; this is a dependency order, not a claim that all current grown bodies fit one packet. No extraction/consolidation/copying controllers to fit a budget. Package B must be source-qualified for the actual publication/completion cuts; the ENV reviewer cannot supply that proof. Package C must qualify the exact real finalizer and actual receiver association, not a fabricated fixture owner.

## 8. Review disposition and remaining precise supplier checks

**Technical design recommendation:** adopt the additive APIs above, subject to independent source-owner review. No capability-reducing proposal is selected and no routine user decision is needed for these authorized additions. The v2 ownership gap is closed by the actual supplier; the exact ENV metadata is incorporated without primitive-only, bootstrap-empty, single-preparation, device/profile or physical-state-freeze restrictions.

Remaining finite review questions are implementation feasibility checks, not unspecified policy: can the actual ENV/helper hold the required lock and perform poison-safe terminal bookkeeping at every ordinary-method/finalizer exception cut; does the ingress map cover the full promised fence; do the real BANK/runtime wrappers seal the defined outcomes on every guard/body/completion/suffix path without altering currency; and does the genuine consumer's fixed finalizer satisfy its existing journal/other-child obligations? If any actual implementation would reduce an existing supported capability, surface that concrete change before APP work rather than treating this design as removal approval.

Until those answers and executable controls are independently accepted, C3 remains open. No count/programme change, false C2 urgency or broad framework is introduced.
