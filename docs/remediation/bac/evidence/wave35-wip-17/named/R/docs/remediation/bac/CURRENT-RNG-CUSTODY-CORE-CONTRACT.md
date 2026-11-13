# RNG custody core contract

Current native wire is strict RND/adaptive/ICM v4 with embedded named Adam recipes; see the [native restore configuration contract](CURRENT-NATIVE-RESTORE-CONFIGURATION-CONTRACT.md). The [pure bootstrap contract](CURRENT-PURE-BOOTSTRAP-CONTRACT.md) describes empty shared reservation, held pure bootstrap and explicit-lineage activation. The historical owner/bootstrap/capture/BANK records below retain their own source bindings and evidence scopes.

The current process core adds scoped CUDA admission, idle enrollment expansion, exact per-invocation device operations and source-classified local CUDA completion. These are process-custody capabilities. They do not supply parent boundary/role authority, same-owner revision tracking, truthful producer device inventory or all-child publication. The production local-contract manifest is empty; no real local GPU leaf is enabled by this core-only change.

## Current source and qualification scope

Current [rng_custody.py](../../../src/townlet/exploration/rng_custody.py) is821 lines, SHA256 `0a0f19d37ac85b1584ea028e7e7268a04d18e9f39db0e41b9780181913aae477`. Focused [CUDA admission regression](../../../tests/test_townlet/regressions/bac/test_rng_cuda_admission.py) is1409 lines, SHA256 `b044538dfe656976c0171d81fae4c3d44bba9b47f8b5072d846cfe2d9acf962e`.

R89 qualifies this bounded core CPU/protocol component. Root records1515 unique PASS:67 new core,1290 coherent existing,109 replay and49 owner regression cases. Two CUDA-hardware controls remain SKIP, and one previously required ordinary-runner case remains deselected and owed. The focused67 include ten actual qualified spawn children and two real inherited-gate fork trials, with strict source/import/manifest/PID/PPID ancestry checks. Independent Astra executed the same67 with complete custody verification and PASS; those overlap root's67 and add no unique cases. All application execution is closed.

An initial ten-case pytest batch passed but was rejected by the strong verifier because it actually used two workers. That rejected evidence is retained. Corrected separate one-worker runs supply the accepted child qualification; repeated attempts are not extra unique cases. Immutable R89 component receipt `wave35/r89-cuda-core-component-receipt.json`, SHA256 `dda5f267a4db95acf62b5ec885e28e2a7911845824b15c63b5a30a537abc8332`, and independent verification `P/T18e-R0-CUDA-CORE-INDEPENDENT-VERIFICATION.md`, SHA256 `306d71862be4b66688bcb8aef2160a77202c6180d090b34cc7dff1f2d1d37b7f`, bind these final results.

Owned-core and public-consumer typing, global Ruff/Black and the unchanged defaults600 gate pass. Global mypy still fails with15 required errors: six oracle and nine POP lineage errors. This component qualification leaves programme accounting unchanged at28 qualified/38 remaining/66 total; it does not accept those failures or close remaining programme work.

Instrumented CUDA seams qualify protocol behavior, phase/currentness effects, exact inventory/completion calls and failure identity. They do not qualify actual CUDA initialization/query RNG effects, real asynchronous GPU completion or one-/two-device replay behavior. The actual fork witness establishes inherited-process guard behavior in its measured Linux single-thread profile. No real CUDA work occurs in the guard grandchildren. Skipped hardware controls remain unexecuted.

## Sole domain and required public APIs

`process_rng_domain()` returns the sole process domain; independently constructed domains are refused. Registration binds an actual weak-referenceable lifetime owner, exact initialized sorted/unique CUDA indices and a nonempty immutable entrypoint set. Empty `()` registration is CUDA-query-free and does not enroll a device. Registration/retirement and ownership adoption require idle custody. Active operations pin their admitted owners; idle weak retirement drains under the actual domain lock.

All parameters below are required. Domain entrypoints and gate methods use the exact keyword/positional forms shown. Context-manager APIs yield the listed capability/value; generator `Iterator` annotations do not change the typed public context-manager call.

| API | Result or yielded value |
| --- | --- |
| `domain.operation(*, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation \| None)` | yields `RNGOperation`; full-member completion |
| `domain.device_operation(*, participant: RNGParticipant, operation_kind: str, lineage: RNGOperation \| None, cuda_devices: tuple[int, ...])` | yields `RNGOperation`; exact invocation subset |
| `domain.admission(*, lineage: RNGOperation \| None)` | yields `RNGAdmission` |
| `admission.resolve_cuda(device: torch.device)` | `int`; positional or keyword selector |
| `admission.enroll(*, participant: RNGParticipant, cuda_devices: tuple[int, ...])` | `None` |
| `admission.report_failure(*, error: BaseException)` | `None` |
| `domain.local_cuda_access(*, participant: RNGParticipant, contract: LocalCUDAContract)` | yields `LocalCUDAGate` |
| `local_gate.resolve_cuda(*, device: torch.device)` | `int`; keyword selector |
| `local_gate.complete(*, cuda_devices: tuple[int, ...])` | yields `None` around actual local work |
| `local_gate.completion_failed()` | `bool` while gate remains open |
| `local_gate.report_failure(*, error: BaseException)` | `None` |

The full-member and explicit-subset operations are distinct capabilities. Both authenticate the actual participant, registered entrypoint, issuing thread and exact active lineage, and share ordinary-work currency, revision, token and failure rules. A subset must be sorted/unique, initialized and within enrolled membership before its body begins; it cannot add membership. Each nested operation completes its selected scope inventory and contributes that inventory to the sorted outer completion union. A full-member scope selects the member's declared tuple. An explicit empty subset is truthful only for work that uses no CUDA. Both empty routes access no CUDA attributes.

`lineage=None` obtains standalone admission only while the same thread is idle. An active operation requires its exact authentic lineage; missing, foreign, expired and cross-thread lineage refuse. No local scope, diagnostic value or gate can fabricate lineage. Other threads wait at the actual domain RLock. The new admission gate holds that same lock throughout its lifetime and creates no operation, token or draw authority. A gate opened under a parent requires its authentic lineage and cannot initialize or enroll while that parent remains active.

## Lazy resolution, READY and enrollment

CUDA resolution requires an actual `torch.device` CUDA selector. Structural refusal precedes CUDA queries. For unindexed `torch.device("cuda")`, resolution reads the actual current device anew; the public selector is not permanently canonicalized to its first index. A returned effective index is per invocation. Producer inventory must separately include actual retained/source/input/staged/output/temporary devices; selection alone is insufficient, and historical enrollment is not an instruction to synchronize every device on every call.

Healthy idle resolution verifies an already initialized runtime or calls explicit `torch.cuda.init()` when necessary. Immediately before an actual initialization attempt, the core advances ordinary-work currency once, invalidating prior preparations without inventing an operation exit/revision. Successful initialization records READY before normal index validation. Thus successful first init followed by an out-of-range refusal retains READY and its currency invalidation, without owner-data publication or enrollment. A no-op already-initialized resolution preserves otherwise current preparations. No seed, draw, RNG capture or all-device enrollment is performed merely to resolve an index.

READY is a process-local healthy-runtime fact. It is established by successful healthy initialization or initialized-runtime verification and cleared when uninitialized/uncertain runtime state is observed. It is not membership, current-token authority or proof of an arbitrary leaf's effects. Active-parent initialization refuses before an attempt and requires idle preflight. Uncertain query/init failure clears readiness, preserves the original exception and records common first-cause poison; normal device/index refusal does not itself poison. Initialization has no claimed rollback to a CUDA state that did not exist.

Under an idle admission gate, `enroll` authenticates the existing participant/live owner and validates exact initialized indices, then atomically replaces the immutable member record with its exact union. Participant identity, weak owner reference and entrypoints remain. Only a real expansion increments membership generation; an unchanged union is a no-op. The gate pins an enrolled owner through exit. No unregister/re-register, token refresh or compensating generation reset is used. Active enrollment refuses even with genuine parent lineage.

## Source-bound local CUDA work and completion

`LocalCUDAContract` is an opaque source-issued classification identity. The immutable core manifest associates each enabled identity with one exact concrete owner class and route/input/effect policy, including separate healthy and READY post-poison permissions. Local entry authenticates both membership and contract, requires `type(owner) is policy.owner_type`, pins that same lifetime instance and retains the exact participant/owner/contract/route binding. Unrelated producers, unlisted subclasses, name spoofing, fabricated contracts and caller purity declarations do not qualify. There is no public issuer or policy-registration API.

The current production manifest contains no entries. A later bounded producer/supplier change must enable each concrete audited route and its actual input restrictions before migrating that route. The finite private CPU fixture supplies no production permission. Producer dispatch remains responsible for executing exactly the classified leaf with its supported ordinary inputs and truthful device inventory; the core is not an arbitrary-code purity detector.

A local gate holds the sole domain lock before producer owner exclusion. Healthy idle local resolution may initialize before acquiring the owner lock. Under an active parent it cannot initialize or enroll. Under common poison, it requires a previously READY runtime and an individually qualified post-poison route; it cannot bootstrap or verify unknown readiness. Already READY unindexed selection remains dynamic under the route's qualified query contract. CPU owner-local leaves and accepted disposable cloned-generator scratch work remain on their existing owner-only path without new CUDA prerequisites.

The producer acquires its owner lock, validates health and inventories actual initialized source/destination/temporary devices, then enters exactly one `local_gate.complete(cuda_devices=...)` scope around the actual work. Tuple validation precedes the body. Mid-work resolution, overlapping/repeated completion and escaping an active unfinished scope refuse. Internal helpers reuse the producer's existing scope and effective device. They cannot retroactively add an unlisted device after work starts.

Local completion attempts every declared index in stable order on success or body failure, without sweeping undeclared available/historical devices. It runs while the producer still holds owner exclusion. In an owner-held `finally`, the producer inspects `completion_failed()` and quarantines an affected owner before releasing its lock; then it releases the gate/pin. The core cannot inspect a producer's private lock or prove its inventory. Actual producer dispatch, exclusion and quarantine placement require their own bounded implementation/review.

## Failure, currentness and process boundaries

Body failure with successful completion is raised unchanged. Local completion uncertainty sets the authentic failure marker and first common poison cause; every declared local index is still attempted. Body and distinct completion failures retain original identity/order, with the body first. Repeated exception identities are not duplicated through nested/parent cleanup. Gate `report_failure` can report pre-operation uncertainty without fabricating an operation; under a genuine active operation its errors also participate in that operation's exit aggregation. Reporting and successful local work never heal common poison, mint/refresh tokens or authorize publication. No public poison reset exists.

Core tokens are issuer-owned evidence for their participant, operation, generation, revision and currency; producers validate the original token. The core finalizes still-current issued tokens through its own operation-exit weak-retirement bookkeeping; this grants no producer permission to refresh stale material. In the same held operation, validation uses its original revision; across release it permits only the immediately following operation revision with matching generation/currency. Actual membership changes and ordinary admitted work can stale preparations. Ordinary nested sibling work changes currency; ordinary work inside an open preparation follows the existing nesting rule and need not independently stale its core token. Producer owner-revision/material checks are therefore independently required after staging and immediately before publication. Successful local work alone does not advance core operation revision/currency/generation. Owner mutations must advance the producer's own revision before their mutation body, including failed attempts, when that producer is integrated.

Correct lock order is sole domain admission/gate before producer-owner exclusion, with parent/BANK lifecycle locks placed inside the declared order. CUDA completion must finish before owner exclusion is released. The core's `_cuda_busy` transaction guard rejects unrelated same-thread reentry during runtime/bootstrap/inventory/local-completion transactions; other threads wait at the actual domain lock. `status()` remains blocking diagnostics and supplies no owner-lock-safe admission authority.

New gate entries and every gate method check the actual process PID before lock acquisition, scope/thread/policy checks or CUDA effects. Real inherited use raises built-in `RuntimeError` with exact text `RNG custody cannot be inherited by another process`. Open issuing-thread scope, real RLock ownership and unchanged local binding are also authenticated. Gate/contract/operation/participant/token capabilities are process identities, noncopyable and nonportable; synchronous scopes cannot cross await/task ownership or be used after exit. Genuine domain custody does not intercept arbitrary raw library calls or detect raw mutable aliases.

## Remaining integration and hardware obligations

The core change supplies no replay CUDA preflight wrapper, per-producer selected/retained/input/staged inventory, local route activation, owner mutation revision/publication implementation or parent call-site migration. Those require their own bounded source and causal evidence. Existing same-object/raw-alias quiescence and real parent/role/all-child publication responsibilities remain. Real CUDA initialization and initialized-query RNG preservation, actual asynchronous completion under owner exclusion and applicable one-/two-device tests remain required. B6 actual producer/hardware work, the deselected required ordinary-runner case,15 global type errors and the remaining38 programme packages stay open despite this core component qualification.

## Historical source-qualified contracts and evidence

The following records retain their original source hashes, runtime selections and checkpoint-specific limits. Their historical pending lists and package counts do not rebind current source or assert current package accounting. In particular, old371-line core hashes below describe those checkpoints; the current core binding is stated above. Native v3 history creates no compatibility path through the strict current v4 wire.

## Historical R45 source binding and public interfaces

The fixed five-body source is4099 lines: world_curiosity_state.py1253, rng_custody.py371, regression1412, unchanged rnd.py910 and provider_factory.py153. Core/test SHA256s are `8aaa59e919e82ca49431620f25a77ddd5b08f2c9a845e7c4f5593f1eed6072b0`, `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb` and `53fad08df44e8e02c198c8d1f71254b5de8ad018067aa7a5bca1ff0afc91ee15` respectively. Unchanged RND/factory seals are `30d3e9fba6ae6f90ffdda425c986bd6abecaf70e3728bdf104ca21ca832adc78` and `dc69a831e045bed5c71b5bd448b1e9ff0163e6bce9d816b41d10af0f580708c8`.

| Producer | Actual source binding | Public work |
|---|---|---|
| Process domain | [rng_custody.py](../../../src/townlet/exploration/rng_custody.py#L137), operation231/current validation332 | register/unregister, operation, current_token/validate_current, poison/status; process_rng_domain370 returns the sole instance |
| Named private RNG | [world_curiosity_state.py557](../../../src/townlet/exploration/world_curiosity_state.py#L557) | create/from_snapshot, snapshot, validate_binding, activate, rng_participant |
| Private lifecycle | [OwnedWorldBackend966](../../../src/townlet/exploration/world_curiosity_state.py#L966), reset1058/install1087 | actual private factory/callbacks, prepared restore/reset, validation/publication |
| Shared lifecycle | [SharedWorldBackend1115](../../../src/townlet/exploration/world_curiosity_state.py#L1115), reset1209/install1234 | actual ambient construction/callbacks, prepared restore/reset, validation/publication |

Required call shapes are:

```python
OwnedWorldBackend.construct(*, rng, factory)
SharedWorldBackend.construct(*, factory, cuda_devices)
owner.call(operation, *, lineage)
owner.snapshot(*, lineage)
owner.prepare_restore(payload, *, factory, validate_backend, lineage)
owner.prepare_learning_reset(*, factory, prepare_native, lineage)
owner.validate_prepared(prepared, *, lineage)
owner.install(prepared, *, lineage)
```

All lifecycle lineage keywords are required. Explicit None obtains standalone admission; exact active lineage composes nested owner work. Private factory receives its actual candidate WorldRNGState and private call receives `(backend, sources)`; shared factory receives no arguments and shared call receives `(backend)`. Native reset adapter receives `(current_candidate, fresh_candidate)` and must return None after genuine family reset. Restore validator receives `(candidate, owned_native_payload)` and must return None without changing either.

Registration binds an actual weak-referenceable lifetime owner, explicit canonical initialized CUDA inventory and permitted entrypoints. Constructors/new registrations require idle custody. Backend `rng_participant` exposes only opaque membership. The domain, operations and prepared handles are process-bound issuer identities; copied fields, serialized handles, wrong owner, reuse and stale evidence cannot authorize publication. PreparedWorldBackend has no material getter or public material constructor.

## Admission, currentness and lifetime

Actual exclusion order is domain admission before owner mutation lock. Parent/BANK adoption must additionally place the domain before its lifecycle/BANK locks. Other threads wait on that common domain. Unrelated same-thread reentry, wrong/expired lineage and same-owner lifecycle reentry refuse before effects. Same-RNG named nesting, including A→B→A, retains its genuine active lineage.

Persistent ordinary-work currency survives lease boundaries. Draw/no-draw calls, snapshots and admitted failures invalidate prior preparations; successful standalone bookkeeping also changes domain revision. Membership registration, explicit retirement and idle weak retirement change generation. Rejected invalid membership/lineage before admission causes no callback. Prepared owner revision, domain currency/generation/revision and shared predecessor checks occur before any ambient setter or backend publication. Successful validate_prepared refreshes only its already-authenticated handle and does not consume it.

The registry weakly owns lifecycle objects. GC retirement queues drain while idle; active operations pin every admitted owner through outer exit. Raw supplied-RNG adoption retires its former standalone registration when appropriate, while managed construction preserves an independent original RNG and binds a distinct candidate owner. Retained real RNG/native aliases remain real lifetime roots. No public poison reset exists.

Each admitted nested scope completes its declared devices before return; outer exit completes the sorted participant-device union before releasing admission. Completion/cleanup failure poisons custody and preserves primary errors alongside completion errors. CPU empty inventory accesses no CUDA attribute. Actual GPU execution remains unqualified.

## Reset and restore continuation

Private learning reset clones the current native backend and every current named stream under custody. It invokes neither live owner.call/snapshot/native checkpoint nor create/reseed. The real selected fresh factory advances the candidate's streams; disposable native validation uses separate work continuation. Publication retains genuine constructor advancement, native retained obligations and correct next service. Exact private restore instead installs saved named continuation and discards disposable reconstruction draws.

Shared construction is real ambient-consuming work. Shared reset captures current entry, performs the genuine selected fresh factory, retains its advanced continuation and restores entry until publication. A producer-owned predecessor revision prevents two candidates forked from the same entry from silently both committing. After the first commits, the second must refuse before staging; genuine reprepare/install under the still-held lease continues from that first committed continuation. Ordinary shared restore preserves the **current** ambient stream through disposable native reconstruction, including prior peer draws. Its snapshot contains no historical process RNG field.

For an already bootstrapped private RND owner and its genuine same-family selected factory, the publication portion uses the actual public APIs:

```python
from townlet.exploration.rng_custody import process_rng_domain

def reset_rnd(current, fresh):
    current.install_state(current.prepare_learning_reset(fresh=fresh))

with process_rng_domain().operation(
    participant=owner.rng_participant, operation_kind="prepare", lineage=None
) as lease:
    prepared = owner.prepare_learning_reset(
        factory=factory, prepare_native=reset_rnd, lineage=lease
    )
    owner.install(prepared, lineage=lease)
```

The component lease supplies RNG/owner custody. Genuine outer boundary/role/all-child publication authority remains the enclosing producer's responsibility.

Restore validation is **pre-load and pure**. Actual native load, exact roundtrip and final clone follow it. It is not a mutable post-load hook and does not transport CP's separately owned gradients. Actual offside-owner gradient attachment, pairing and parent-token sealing require the owning BANK/CP integration. No opaque candidate access or automatic deepcopy-gradient guarantee is supplied.

## Historical R45 qualified evidence and boundaries

Root's fixed-source R45 execution passed53 cases in39.201999187s; independent Astra executed the **same53** in31.908644199s, with zero errors/skips/warnings. These are overlapping executions of53 unique cases, not106 cases. Both runs passed808source/573config/13artifact/index/import/thread/14registry MAIN1 controller custody. Genuine spawned poison children PID191342 and191339 were independently companion-verified for actual source/import/manifest/debug, Torch2.11.0+cu130, intra1/interop5, Process/queue PID agreement and exit0.

The cases use genuine compiled token-set-smoke D/A, actual selected RND/provider factory, real backward/Adam/FIFO history and complete independent native/stream/ambient/next-draw observations. They qualify both cross-lease currency schedules including no-draw and validation, two-real-shared sequential continuation, real reclamation/active pins, independent nonnested nesting oracle, actual constructor admission, partial setter/post-constructor capture/verification cuts, preexisting private owner after child poison and same-owner service/manual/replacement exclusion. This is the executed RND/CPU core profile. It does not qualify all five providers, full training, CUDA or native gradient transport.

The [pinned dense CPU Adam profile](CURRENT-CPU-ADAM-RNG-PROFILE.md) remains the narrow independent-owner RNG-free exemption. No blanket optimizer wrapper/hook/gate or manual-step/replacement/signed-offset restriction was added. Stochastic forward/backward/hooks/selection/sampling/construction still require actual admission. Managed callbacks receive actual native objects; copied return values do not prevent aliases retained through side effects. Raw aliases and standalone native prepare/install retain caller-owned same-object quiescence, without an automatic mutation detector.

The runnable functional witness is `uv run pytest tests/test_townlet/regressions/bac/test_world_rng_custody.py --no-cov -p no:cacheprovider -q`. Root qualification additionally uses the external identity plugin/harness to record exact source/runtime/import/thread manifests and actual child identity. Final Astra source/runtime review309 lines, SHA256 `938f9e89d42f55c5c923e7130243c56cc356ab00d77b160623a30863554b7411`, approves this bounded CPU core with no material finding and retains the GPU/global integration limits.

Root's closed R45 CLI fleet passed34 packs in210.216794729s wall, with35 actual process identities and808 source/573 config/13 artifact guards for each, plus exact20ce0b57 source/index/import/thread custody. CLI log SHA256 is `edad11c3fe94f96286522586db83b06c5a741639cfd24c30a74a7a63aaa0fad1`. This verifies that fleet/profile; BANK runtime adoption and full training remain required below.

Global Ruff/Black/expression and unchanged defaults600 pass. Mypy has zero core errors but14 mandatory BANK missing-lineage caller errors plus6 prior oracle errors,20/198; global static all_passed remains false. Actual BANK domain-before-lock/required-lineage adoption, pure shared replacement/archived bootstrap, supported direct factory/native/Q/replay/selector/ENV/curriculum enrollment, real stable-role/all-child publication/fullD/T26 and older84 fixture migration remain required and unqualified. The shared constructor's real consumption cannot be called pure replacement preparation. Exact process-cohort resume remains optional P3, with no new checkpoint requirement.

Package accounting stays28 qualified/38 remaining/66 total; the54 requirements,22 final reviews and all final programme gates remain unchanged. Package/global acceptance still requires the integration and final gates above.

## Historical R47 — existing RNG owner regressions at native v3

At R47, existing binding/domain regressions used the required common-domain API and then-current native v3 records. That historical checkpoint superseded the earlier84 fixture-migration item for its bound source; it does not establish current-v4 owner qualification. Actual R0/B1/BANK/bootstrap/fullD/T26 integration and whole-program enrollment remain required.

Only the two existing test files changed. All original27 functions and84 collected node identities are retained: binding12/52 and domains15/32. Frozen binding is581 lines, SHA256 `225e926896eca8a61512d9b17d059ab2283f11a8ed5056d0ba5e38fc0fb48ae8`; domains is1061 lines, SHA256 `6967b38929f81e7f86406c3e2d2dda0f84210d06ec3b235aaa73f79c2f791f1f`. Production remains unchanged: world_curiosity_state.py1253 SHA256 `8aaa59e919e82ca49431620f25a77ddd5b08f2c9a845e7c4f5593f1eed6072b0` and rng_custody.py371 SHA256 `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`.

Backend call/snapshot/prepare/install sites now pass explicit standalone `lineage=None`; the separate WorldRNGState signatures are unchanged. The foreign-handle control still refuses, then a fresh authentic preparation immediately precedes the positive install, because an admitted foreign attempt invalidates released preparation currency. Consumed-handle refusal and real managed-learning staleness remain separate controls. No prepared material fields, compatibility alias, fallback or private poison reset was restored.

The historical R47 learned-state oracle required exact `rnd-state-v3`, `adaptive-intrinsic-state-v3` with nested RNDv3, and `icm-state-v3`, plus RND `predictor_service.version=3`. Its no-reset fixtures required optimizer_epoch_origin O exact0, nested in RND service and top-level in ICM, and S=(U-O)+delta for RND/adaptive or S=U-O for ICM. Those formulae remain current, but the obsolete schemas are rejected by current natives: owner fixtures must require v4 and the corresponding recipe from the primary current-wire contract. Historical changed-model/Adam/RMS/FIFO/clock/budget/alias/stream assertions and zero-offset controls are not relabeled as new v4 execution; supported signed-offset/manual/replacement capabilities remain intact.

Refusal controls now require the actual typed boundaries and exact messages: RuntimeError `Unrelated same-thread RNG reentry is forbidden` for active standalone snapshots/unrelated cross-owner entry; RuntimeError `RNG membership requires exclusive idle custody` for active registration/from_snapshot; RuntimeError `Private RNG state is unusable after failed capture` for broken private binding; RuntimeError `Ambient RNG domain is poisoned after failed restoration` after poison; ValueError `Prepared backend is foreign, fabricated or already consumed` for foreign/used handles; and ValueError `Prepared backend destination changed` after actual managed learning. Callback nonentry and complete no-effects observations remain part of these controls.

Both poison tests execute genuine restoration failures in fresh children and leave the parent domain healthy. The binding child replaces the removed coordinator-reset fixture; the domains child retains its actual failure/cause, surviving setters and source/import/tree checks. Qualified children bootstrap the trusted identity hook before native/poison work, enrich their own newly issued receipts under distinct binding_poison/domains_poison names, and emit their actual PID after successful assertions. Parents compare that PID with the actual Popen handle and zero exit status before recording observations; owned-child timeout cleanup is bounded. No interop-thread setter or parent-fabricated child identity is used.

Root's fixed-source R47 combined selection collected137 exact nodes and passed135 with2 CUDA-unavailable skips in41.9571042s, zero warnings. Independent Astra executed the same original84 subset:82 passed and the same2 CUDA-unavailable cases skipped in16.4289067s, zero warnings. The independent84 overlap the root137; this is137 selected unique nodes, not217. Root additionally passed all3 healthy native/private prerequisites in5.5797486s and targeted8 in12.8987808s; these also overlap the selection.

Root reports companion verification of every actual child for source/import/manifest/debug identity, Torch2.11, intra1/interop5, actual reported/process PID agreement and exit0: targeted children195273/195300; combined core195700, binding195878 and domains195965; independent children196315/196371. Final independent source/runtime review SHA256 `19f4ad14538d3084b20f3226f231b0af95e1a8f7bd46969ac1f402314fe0cecd` approves SPEC and QUALITY with no material findings. These are attributed root/reviewer executions; this documentation author ran no application or test.

Root's R47 CLI fleet is closed and verified:34 packs and35 actual process profiles passed in154.546749115s, each checking809 source/573 configuration/13 artifact guards plus import/thread/index custody. CLI log SHA256 is `edf63af96673c757c56bd014406fbdfc64e5b1f9c2668a5a4e5a084e7c9c2f5f`. All R47 runtime and verifier work is now closed. This verifies that fleet/profile and does not substitute for remaining integration.

The2 skipped CUDA cases remain unexecuted and hardware-unqualified. Global mypy remains20 required errors,14 BANK lineage callers plus6 oracle errors; global static acceptance remains open. Actual domain-before-BANK locking, pure shared replacement/archived bootstrap, direct stochastic consumer enrollment, native gradient transport, full training, real stable-role/all-child publication/fullD/T26 and final programme gates remain required. Managed owner currentness does not intercept raw mutable aliases; their caller-owned same-object quiescence remains distinct. Package accounting stays28 qualified/38 remaining/66 total, with54 requirements and22 final reviews unchanged.

Current migration status supplied by root at R53:946 owner cases yielded920 PASS,24 FAIL and2 CUDA skips;23 failures are obsolete owner calls missing required lineage, and one known ordinary-runner ENV-role prerequisite remains required. This is reported migration evidence, not a new check by this documentation author or complete current owner qualification. Subsequent causal repairs/execution belong to the sole test owner and root; no compatibility or capability reduction is inferred.

## Historical R58 correction

The shared pure bootstrap and `activate_under` producer APIs are implemented and boundedly qualified; see [current pure bootstrap](CURRENT-PURE-BOOTSTRAP-CONTRACT.md). Earlier R45/R47 statements listing bootstrap as pending and the final R53 paragraph reporting 946 owner cases with 24 failures describe historical source snapshots. Current R58 coherent execution passed 1,052 cases with two unavailable-CUDA skips; the required ordinary-runner ENV integration failure remains OPEN. Actual BANK/CP adoption and parent publication remain open. The 28/38/66 package count and 54 requirements/22 final lenses are unchanged.

## Historical R67 additive atomic private capture

```python
OwnedWorldBackend.snapshot_with_capture(capture, *, lineage) -> (snapshot_envelope, owned_auxiliary_value)
```

The required `lineage` is either explicit `None` for standalone admission or the exact authentic active parent operation. One owner scope and one private service activation invoke native `checkpoint_state()` exactly once, then invoke the read-only capture callback exactly once on the same actual backend/Parameters. Both native and auxiliary ownership copies finish inside activation. Activation restoration and completion finish before the producer's internal quiescent RNG snapshot; owner/domain custody continues through result construction and outer completion. The unchanged envelope fields are `schema="owned-world-backend-v1"`, `healthy`, `backend` and `rng`; auxiliary data is returned separately. Supported returned value data is independently owned, with tensors/Parameters detached and cloned. Existing `snapshot` and `call` semantics are unchanged.

The callback may capture named gradients from the actual live Parameters. It must not perform lifecycle work, configure/load native state, snapshot private RNG or retain live aliases. Exact lineage does not bypass active-frame quiescence or same-owner reentry exclusion. Noncallable capture rejects before native/RNG work without quarantining a healthy owner. Live native/callback/copy failure propagates, quarantines the owner and advances its revision; uncertain restoration/completion retains existing common-domain poison behavior. As with ordinary snapshot, diagnostic capture of a quarantined owner does not clear its `healthy=False` state or permit managed calls. Callback read-only behavior and supported value transport remain cooperative obligations, not an arbitrary-code sandbox or raw-alias mutation detector.

BANK consumers must retain their outer process-domain operation and lock and forward that exact lineage. Do not split native/gradient/RNG capture across owner operations: a second serializer can change private RNG or nonserialized gradients despite equal native bytes. Do not call private RNG internals from BANK or snapshot RNG inside the callback. Shared owners require no additional API: their existing `call` supports native plus gradient capture under actual custody. Producer qualification does not establish consumer adoption or all-child publication.

R67 source is `world_curiosity_state.py`1361, SHA256 `433b3563457fbf68d26d47d73dc375c1382e0cc77d0987a4c9d4f62f3cdfcce3`; unchanged domain371 SHA256 `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`. New capture regression598 SHA256 `ad6f50b0991efc30eb0e960dc5f5c78560ed849e4046240f029139e716fcc180` reuses the existing genuine bootstrap supplier998 SHA256 `452e427b945475e050b35273b6bb44effe3ade6ef96629c4382c2d68591ee727`. These four seals remain unchanged at this R72 documentation handoff. R67 candidate tree is `04af55dcf99559c949b16af6fa92effd30b54f6f`, manifest SHA256 `f256db6b0a8759ef5a15501fe1a637f4f8d62c09dc224e999ec47eb4aa29f102`.

After the genuine R66 missing-method RED, root's R67 new16 passed in32.315819s and existing56 bootstrap controls passed in45.185444s. Independent Astra executed the same new16 once in27.910327196s, all passed with no skips/warnings, and approved SPEC/QUALITY with no blocking findings. The two new16 runs overlap; they are not32 unique cases. Independent log SHA256 is `1afd2d0cc9addca7f2b01381b10aa3ab3228e3c15dd9013a0d013f8527219155`. Root verified814-source/573-config/13-artifact/controller/import/index/14-MAIN1 custody and all three actual independent spawned poison-child identity/observation pairs. Witnesses cover one serializer, identical real Parameters, detached gradients/results, post-copy/post-cleanup RNG continuation, exact lineage, coordinated actual peer admission, revision invalidation, callback failures and isolated setter/cleanup/completion poison. This is bounded CPU producer qualification; actual GPU execution, final R72 BANK integration, full-parent restoration and whole-program acceptance are not established by these R67 results. Separately, root reports bounded R72 CPU BANK/CP qualification at candidate `c4b3765a1b9734a82b1a7eaaccbb1489da23d9bc`: coherent 1290 PASS with two CUDA-unavailable skips, independent Astra 155 PASS (an overlapping subset), all 13 coherent and four independent actual child custody checks, CLI 34 packs/35 process profiles, and final SPEC/QUALITY PASS. Immutable `wave35/r72-bank-component-receipt.json` SHA256 `e2bad20684bfe39082cf8979deac2b340f9585994b7705bea27a75e7efeb35d6` records that distinct component result; it does not rebind the R67 producer evidence above. Full-parent joint restoration/publication, actual ordinary runner integration, six global oracle type errors, applicable hardware and final programme gates remain open; documentation/evidence and remote publication remain pending. Deferred exact stochastic/mid-episode simulator continuation is not added to the producer guarantee.
