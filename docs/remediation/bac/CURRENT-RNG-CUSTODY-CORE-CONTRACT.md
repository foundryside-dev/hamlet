# RNG custody core contract

The implemented standalone core coordinates participating shared ambient work and private RNG swapping through one process domain. Backend owners also hold a separate mutation lock. It provides current-token authentication, opaque prepared state, pure current private reset, exact private stream restore and shared continuation dependency checks. Fixed-source R45 qualifies the bounded RND/CPU profile below; actual R0/B1/BANK/bootstrap/fullD/T26 integration, package acceptance and whole-program RNG enrollment remain required.

## Source and public interfaces

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

## Qualified evidence and boundaries

Root's fixed-source R45 execution passed53 cases in39.201999187s; independent Astra executed the **same53** in31.908644199s, with zero errors/skips/warnings. These are overlapping executions of53 unique cases, not106 cases. Both runs passed808source/573config/13artifact/index/import/thread/14registry MAIN1 controller custody. Genuine spawned poison children PID191342 and191339 were independently companion-verified for actual source/import/manifest/debug, Torch2.11.0+cu130, intra1/interop5, Process/queue PID agreement and exit0.

The cases use genuine compiled token-set-smoke D/A, actual selected RND/provider factory, real backward/Adam/FIFO history and complete independent native/stream/ambient/next-draw observations. They qualify both cross-lease currency schedules including no-draw and validation, two-real-shared sequential continuation, real reclamation/active pins, independent nonnested nesting oracle, actual constructor admission, partial setter/post-constructor capture/verification cuts, preexisting private owner after child poison and same-owner service/manual/replacement exclusion. This is the executed RND/CPU core profile. It does not qualify all five providers, full training, CUDA or native gradient transport.

The [pinned dense CPU Adam profile](CURRENT-CPU-ADAM-RNG-PROFILE.md) remains the narrow independent-owner RNG-free exemption. No blanket optimizer wrapper/hook/gate or manual-step/replacement/signed-offset restriction was added. Stochastic forward/backward/hooks/selection/sampling/construction still require actual admission. Managed callbacks receive actual native objects; copied return values do not prevent aliases retained through side effects. Raw aliases and standalone native prepare/install retain caller-owned same-object quiescence, without an automatic mutation detector.

The runnable functional witness is `uv run pytest tests/test_townlet/regressions/bac/test_world_rng_custody.py --no-cov -p no:cacheprovider -q`. Root qualification additionally uses the external identity plugin/harness to record exact source/runtime/import/thread manifests and actual child identity. Final Astra source/runtime review309 lines, SHA256 `938f9e89d42f55c5c923e7130243c56cc356ab00d77b160623a30863554b7411`, approves this bounded CPU core with no material finding and retains the GPU/global integration limits.

Root's closed R45 CLI fleet passed34 packs in210.216794729s wall, with35 actual process identities and808 source/573 config/13 artifact guards for each, plus exact20ce0b57 source/index/import/thread custody. CLI log SHA256 is `edad11c3fe94f96286522586db83b06c5a741639cfd24c30a74a7a63aaa0fad1`. This verifies that fleet/profile; BANK runtime adoption and full training remain required below.

Global Ruff/Black/expression and unchanged defaults600 pass. Mypy has zero core errors but14 mandatory BANK missing-lineage caller errors plus6 prior oracle errors,20/198; global static all_passed remains false. Actual BANK domain-before-lock/required-lineage adoption, pure shared replacement/archived bootstrap, supported direct factory/native/Q/replay/selector/ENV/curriculum enrollment, real stable-role/all-child publication/fullD/T26 and older84 fixture migration remain required and unqualified. The shared constructor's real consumption cannot be called pure replacement preparation. Exact process-cohort resume remains optional P3, with no new checkpoint requirement.

Package accounting stays28 qualified/38 remaining/66 total; the54 requirements,22 final reviews and all final programme gates remain unchanged. Package/global acceptance still requires the integration and final gates above.
