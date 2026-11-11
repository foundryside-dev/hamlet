# R0 core current candidate API

2026-11-11, Round2 equivalent-branch seal of the Round1 Stage B producer. **Actual-source candidate contract; final-source qualification remains pending.** Root's R44 bounded SPEC approval/full53 result applies to the prior equivalent source; root owns R45 final-source qualification. This is not R0/B1/BANK/bootstrap/fullD/T26 closure. Main programme remains28 qualified/38 remaining/66 total.

Source seals: WS1253 SHA256 `8aaa59e919e82ca49431620f25a77ddd5b08f2c9a845e7c4f5593f1eed6072b0`; domain371 `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`; test1412 `53fad08df44e8e02c198c8d1f71254b5de8ad018067aa7a5bca1ff0afc91ee15`; unchanged RND910 `30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78`; unchanged factory153 `dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8`. Exactly five bodies4099 lines, within registered4963/hard5000. No sixth BANK/CP/old-test/Torch/helper body was opened by this producer author.

Round2 changes only the five ASG002 ternaries to explicit equivalent branches: domain342 (issuing-operation revision identity), WS599/613 (current fork/saved restore lifetime-owner provenance), WS755/781 (typed lineage selection for binding/activation). Conditions, short-circuiting, object identities, RNG continuation and inherited authority are unchanged; all public signatures and this contract's semantics remain the reviewed R44 API. Final guard600/static/runtime results remain root evidence to obtain, not an author claim.

## Domain and capabilities

Import from `townlet.exploration.rng_custody`:

```python
process_rng_domain() -> AmbientRNGDomain

domain.register(*, owner: object, cuda_devices: tuple[int, ...],
                entrypoints: frozenset[str]) -> RNGParticipant
domain.unregister(*, participant: RNGParticipant) -> None
domain.operation(*, participant: RNGParticipant, operation_kind: str,
                 lineage: RNGOperation | None) -> ContextManager[RNGOperation]
domain.current_token(*, participant: RNGParticipant,
                     operation: RNGOperation) -> RNGCurrentToken
domain.validate_current(*, token: RNGCurrentToken,
                        operation: RNGOperation) -> None
domain.poison(*, operation: RNGOperation, error: BaseException) -> None
domain.status() -> tuple[int, int, bool]  # generation, revision, poisoned
```

Use the sole process domain. Independent construction has no public authority argument. Participant, operation and current-token identities are issuer-authenticated, nonportable, not deepcopy/pickle authority and not interchangeable with copied fields. Membership belongs to an actual **weak-referenceable lifetime owner**; an unweakrefable object fails registration. The actual project RNG/backend classes satisfy this directly. Custom parent owners must support normal Python weak references. Duplicate owner identity, invalid entrypoint inventory or noncanonical device inventory refuses. Devices are explicit sorted unique nonnegative indices, already initialized and available when nonempty. CPU inventory() performs no CUDA query.

Register/unregister/new-owner adoption require exclusive idle custody. They may block behind another thread's real operation; same-thread membership mutation inside an active lease refuses. Declared entrypoint strings must match actual producer use. Core owners register `rng`, `call`, `snapshot`, `prepare`, `install`, `validate`; a parent's held candidate/publication lease uses registered `prepare`. These are producer operation kinds, not permission for arbitrary caller work to masquerade as candidate preparation. Other kind names are ordinary work by default.

Top-level admission supplies required `lineage=None`. Nested supported producer work supplies the **exact active operation** on the issuing process/thread. Another thread waits on the actual common lock. Unrelated same-thread entry without that lineage refuses; forged, expired or cross-thread lineage refuses. Same-owner backend lifecycle mutation is separately nonreentrant even with correct lineage. Named same-RNG activation nesting remains legal. Do not hold synchronous leases across await/yield.

## Currency and released preparations

The domain retains an ordinary-work currency counter across operation boundaries. Ordinary scopes conservatively advance it on entry and exit; admitted failed scopes also invalidate currency. No byte comparison or native service counter substitutes for this evidence. Top-level operation exit additionally advances domain revision, including prepare/validate/install and failures. Membership creation, explicit retirement and idle weak retirement advance generation.

Current-token validation authenticates membership, issuing identity, the exact persistent ordinary-work currency and the top revision/held-operation relationship. It checks currency both within the issuing lease and in a later lease. A peer call after token issuance but before issuing-lease release, and a peer call in the next lease before install/validation, both stale the token even if the peer draws nothing. Successful candidate-only prepare/validate/install bookkeeping under one held `prepare` lineage composes; nested ordinary calls/snapshots/direct private work invalidate prior candidates. Internal candidate work occurs under the producer's prepare scope.

A released preparation is conservatively stale after another admitted top-level operation, including no-draw calls, snapshots, another preparation, or validation of another handle. A valid owner's admitted foreign/fabricated/consumed-handle attempt also advances the operation revision on failure; failed nested work invalidates currency. A foreign/unregistered participant, unpermitted entrypoint or invalid lineage rejected **before admission** invokes no callback and does not manufacture an ordinary operation. Healthy owner revision changes independently on managed live callbacks/snapshots and publication.

Producer-issued tokens from a successfully closing preparation/validation operation are finalized after that operation's own idle weak-retirement bookkeeping, without rewriting their ordinary-work currency or laundering an intervening registration/ordinary operation. Subsequent membership changes still stale released work. Ended peer lifetimes can therefore invalidate released preparations: callers must retain relevant owners and hold the actual common lease continuously for atomic multi-owner publication rather than presume quietness.

## Public RNG owner

Import RNG/backend APIs from `townlet.exploration.world_curiosity_state`:

```python
WorldRNGState.create(*, descriptor: WorldCuriosityDescriptor,
                     world_id: str, cuda_devices: tuple[int, ...]) -> WorldRNGState
WorldRNGState.from_snapshot(payload: Any, *, descriptor: WorldCuriosityDescriptor,
                            world_id: str, cuda_devices: tuple[int, ...]) -> WorldRNGState
rng.snapshot() -> dict[str, Any]
rng.validate_binding(*, descriptor: WorldCuriosityDescriptor,
                     world_id: str, cuda_devices: tuple[int, ...]) -> None
rng.activate(component: str) -> ContextManager[WorldRandomSources]
rng.rng_participant -> RNGParticipant
```

Create/from_snapshot register actual standalone owners while idle. Create is initial KDF construction, not reset. From_snapshot validates the complete current stream transport and restores its continuation. Snapshot and ordinary lifecycle calls require quiescent private activation. Binding validation and actual same-RNG named activation inherit the authenticated active frame; they do not adopt an unrelated ambient operation just because it runs on the same thread. Components remain model_init,target,predictor,service, with Torch CPU/Python/PCG64/legacy NumPy and declared CUDA continuations. Seed/snapshot schemas and sampling ownership are unchanged. No process-cohort checkpoint field is added.

The existing low-level `WorldRNGState(descriptor,world_id,cuda_devices,components)` copies supplied components and registers an owner; complete canonical snapshot validation belongs to the public builders above. It is not a caller-supplied portable currentness capability. Python sources retain their activation-bound check; retained NumPy generator/RNG aliases still require caller quiescence.

## Private and shared backend signatures

All lifecycle `lineage` keywords below are **required**. Pass explicit None for standalone execution; there is no default or unguarded compatibility route.

```python
OwnedWorldBackend.construct(*, rng: WorldRNGState,
                            factory: Callable[[WorldRNGState], Any]) -> OwnedWorldBackend
owner.call(operation: Callable[[Any, WorldRandomSources], Any], *, lineage: RNGOperation | None) -> Any
owner.snapshot(*, lineage: RNGOperation | None) -> dict[str, Any]
owner.prepare_restore(payload: Any, *, factory: Callable[[WorldRNGState], Any],
                      validate_backend: Callable[[Any, Any], object],
                      lineage: RNGOperation | None) -> PreparedWorldBackend
owner.prepare_learning_reset(*, factory: Callable[[WorldRNGState], Any],
                             prepare_native: Callable[[Any, Any], object],
                             lineage: RNGOperation | None) -> PreparedWorldBackend
owner.validate_prepared(prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None
owner.install(prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None
owner.rng_participant -> RNGParticipant

SharedWorldBackend.construct(*, factory: Callable[[], Any],
                             cuda_devices: tuple[int, ...]) -> SharedWorldBackend
shared.call(operation: Callable[[Any], Any], *, lineage: RNGOperation | None) -> Any
shared.snapshot(*, lineage: RNGOperation | None) -> dict[str, Any]
shared.prepare_restore(payload: Any, *, factory: Callable[[], Any],
                       validate_backend: Callable[[Any, Any], object],
                       lineage: RNGOperation | None) -> PreparedWorldBackend
shared.prepare_learning_reset(*, factory: Callable[[], Any],
                              prepare_native: Callable[[Any, Any], object],
                              lineage: RNGOperation | None) -> PreparedWorldBackend
shared.validate_prepared(prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None
shared.install(prepared: PreparedWorldBackend, *, lineage: RNGOperation | None) -> None
shared.rng_participant -> RNGParticipant
```

Constructors create registered lifecycle owners, so they are idle bootstrap operations, not nested construction APIs for an already-held parent lease. Private construct forks the supplied current RNG and retains real candidate factory consumption while leaving the original input continuation/binding usable. Its adopted candidate gets its own actual backend-owner registration; an independent original RNG's registration is not retired. The low-level `OwnedWorldBackend(backend,rng)` aliases/transfers supplied objects, retires the earlier registration only if that registration belongs to that same supplied RNG, and binds the RNG to the backend owner. An externally retained owned RNG alias pins its owning lifecycle object; when all actual aliases disappear, ordinary GC can reclaim the owner/native/RNG cycle. Do not wrap the same mutable RNG as independent simultaneous raw owners.

The low-level `SharedWorldBackend(backend,cuda_devices)` retains a caller-supplied concrete native backend and registers; it does not itself manufacture a fresh native model. Raw constructor callers own quiescence and alias correctness. Managed Shared.construct runs the real selected ambient factory under actual admission and retains constructor consumption. It is **not RNG-free preparation** that can run outside a joint lease and later rewind peer draws.

Callbacks get actual native references; returned values are owned copies. Managed callbacks and snapshots hold a separate owner mutation lock after domain admission, advance owner revision on success/failure as specified by their live paths, and quarantine on live callback/capture failure. A callback may perform the real bare optimizer step or genuine replacement. Side-effect-retained references are not made immutable, and raw mutation outside the protocol is not automatically freshness-detected.

## Candidate work, restore timing and publication

PreparedWorldBackend exposes no material fields/getter or public constructor. Destination-owned weak issuance records carry candidate state, owner revision and domain evidence. Foreign/fabricated/consumed handles, owner revision change, membership/domain/currency change and a shared predecessor change refuse before native publication or ambient setters. `validate_prepared` authenticates the same preflight and refreshes only that valid handle's domain token; it does not consume the prepared handle. Install consumes it once. Snapshot envelopes remain owned-world-backend-v1 with healthy/backend/rng, and shared-world-backend-v1 with healthy/backend only.

Private reset clones current native state directly and all current named continuations without live owner.call/snapshot/native checkpoint/create/reseed. Factory receives the actual candidate RNG. `prepare_native(current_candidate,fresh_candidate)` must complete the actual family reset on the offside receiver and return None; the object return annotation permits strict runtime rejection of bad return values. Disposable native validation runs on a separate work fork. Fresh constructor advancement is retained; exact private restore instead installs saved streams and discards disposable reconstruction advancement. Ordinary successful/refused preparation with successful cleanup does not advance live owner revision or alter live native/RNG/health/ambient state.

For both restore methods, **validate_backend is pre-load and pure**, not a post-load mutable hook: construct real candidate; capture its checkpoint; validate owned transported native data with required None result; reject candidate/transport mutation; load native state; require exact checkpoint roundtrip; clone before sealing. No new post-load hook or candidate field accessor was added. Native family semantic/pairing qualification belongs to that producer adapter. Non-native extra data such as separately transported gradients is not invented inside the native envelope.

Root's separate BANK/CP source owner reports its existing path attaches gradients **after installing each offside replacement owner**, then publishes the BANK dictionary. With properly bootstrapped offside owners, actual owner.call can perform that attachment/validation under held lineage before the parent's final current token is issued. It advances owner/domain mutation evidence, so seal the parent's token after all such work. This is an attributed consumer route to qualify in its own slice, not a claim of current integrated BANK code or automatic gradient preservation by deepcopy.

Shared reset stores a producer-owned ambient continuation predecessor revision. Successful Shared.construct/reset publication advances it only after candidate RNG staging verifies. Two shared candidates prepared from the same entry cannot silently both publish: after the first commits, the second install **or validate_prepared** refuses with `Shared reset continuation predecessor changed; prepare again from current continuation`, before capture/setters/publication. Under the still-held lease, reprepare the second from the first's committed current continuation, then install; genuine multi-owner reset remains usable and yields two sequential real constructions. Private sibling preparation/publication introduces no competing ambient continuation.

Ordinary shared restore has no earlier process RNG payload and preserves the **current** ambient state through disposable reconstruction. It cannot rewind a peer. Stage/verify failure attempts entry cleanup before any backend publication; cleanup failure poisons. Publication failure after staging quarantines rather than promising rollback of an already-published joint operation. Actual outer all-child authority/quarantine remains the parent's obligation.

## Lifetime, device completion and limits

The process registry holds weak owners, not native/model/Adam roots. Weak callbacks enqueue inert retirement notices without taking application/domain locks. Notices drain under exclusive idle custody and advance generation; a retained opaque participant alone does not keep its owner alive. Every participant admitted to an active operation is strongly pinned through the outer operation. Active unregister refuses. Healthy dropped owners and native state reclaim normally; source diagnostics/exception references and explicitly retained aliases are still real Python roots.

The domain synchronizes declared devices before **each admitted nested scope** returns and before the outer lease releases, including callbacks returning None and exceptional exits. Outer completion covers the union of participating devices in sorted order. Completion failure poisons the common domain; primary callback errors are preserved alongside completion errors in BaseExceptionGroup rather than silently discarded. Affected backend scopes quarantine when common poison propagates. Capture/install restoration failure likewise poisons. There is no public poison reset. Empty CPU inventory reaches no CUDA attribute/query; actual initialized-device/hardware execution remains separately unqualified.

The pinned exact independent ordinary dense CPU Adam region remains exempt from global admission. It may finish during another owner's private activation while mutating only its own real model. Same-owner copying/publication still requires actual mutation exclusion. Constructors, stochastic forward/backward/hooks/selection/sampling/service and supported direct routes still need real producer admission; no blanket optimizer wrapper/hook/manual-step/replacement/signed-offset ban is added. Raw aliases retain caller-owned same-object quiescence, and native handles do not acquire an invented mutation detector.

## Required next consumer work

Actual BANK/CP must migrate all backend call/snapshot/prepare/validate/install sites to required lineage, acquire the domain **before** BANK's lock, and qualify real boundary/all-child publication. Passing lineage inside the old BANK-first decorator does not repair lock order. Existing old owner tests need current signatures/refusal expectations; none were opened or modified here. RND/factory's already-owned direct source uses unchanged RNG activate/validate_binding calls, but their unwrapped direct stochastic entrypoints remain required enrollment work.

Stable existing-owner candidate preparation/restoration registers nothing and can run under a held lease. Newly replacement lifecycle owners still require idle pre-registration. A **qualified pure shared replacement/bootstrap/reservation route remains a concrete mandatory dependency**: this repair adds no speculative reservation or post-load API, and does not authorize actual ambient shared construction outside joint custody as a pure workaround. Root's next bounded BANK/bootstrap producer slice must reconcile that capability and the reported real offside gradient path before integration qualification. No unread caller is claimed migrated and no global mypy/defaults/runtime GREEN is claimed here.

This capsule adds no cohort checkpoint manifest, exact process stochastic resume, active-zero-tick continuation or new general scheduling framework. Source/API truth is candidate evidence only until root's fixed-source execution and independent review.
