# Current world identity producer contract

The current constructor route is qualified at transport R1 tree6f46f449:193 joint cases and independent Astra88 pass, with source/fixture/process custody. Six constructor type errors are closed; seven oracle/POP reset-caller errors remain. The earlier R3 lifecycle repair passed54 owned and independent Sol27. These overlapping results describe bounded source handoffs, not integrated BAC release. See CURRENT-WORLD-CONSTRUCTOR-TRANSPORT.md for current call signatures, source hashes and evidence.

Historical R3 producer review scope was exactly ENV2342/WS734/RP768/test830/roster299=5/4973, ceilings2350/734/768/838/310=5000. ENV SHA256 ca739f517b7bb64833b2814c14a99a29d229b1f184c10236faaa52cbe4cfa4f1; roster e2627284a192920211429c77f5a806c0032e17071eedbd0877f95f4d7df4c461; test ff460397f1a9968750e461511b08c71b1de39d6824a9a76045282a9219e0ef3f. WS/RP unchanged. No extra implementation source, runtime, Git/index or source/test edit was used for this document. This ignored prose is the only write.

## Declaration and construction

`townlet.config.world_roster.WorldRosterDeclaration.from_dict(payload)` accepts exactly `{"schema":"world-roster-v1","world_ids":[...exact nonempty unique strings...]}`. It owns an immutable ID tuple; to_dict returns fresh dict/list storage. Semantic membership hashes sorted exact IDs; authored order and manifest digest remain separate provenance. Manifest digest hashes canonical sorted-key compact ensure_ascii JSON UTF-8 plus newline. No row/name/config-label allocation or no-ID fallback exists.

Actual constructor:

```python
VectorizedHamletEnv(
    *, universe, level_name, num_agents, device,
    world_roster, training_seed, lane_world_ids,
)
VectorizedHamletEnv.from_universe(
    universe, *, level_name, num_agents, device,
    world_roster, training_seed, lane_world_ids,
)
```

Every argument is required. Exact roster/binding/cardinality/seed validation precedes construction randomness. lane_world_ids must be a permutation of declared membership. Semantic execution identity includes actual compiled.execution_hash, membership and seed. Constructor accepts string/torch device and normalizes strings. The classmethod rejects absent level and delegates its actual cls/universe through standalone env_factory.from_universe. That factory normalizes string devices and forwards the same required declaration, seed and requested lanes to env_cls. CompiledUniverse.create_environment requires and forwards the same three world arguments. Existing affordance/meter helpers remain.

The accepted CURRENT-COMPILED-POLICY-CONTRACT supplies actual current1.42 compilation: UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False). Actual tests use that compiled artifact and direct ENV construction. No compiler source was reopened.

Readonly/owned views: world_ids tuple, accepted_episode_seqs exact-ID mapping, world_phase string, semantic_execution_identity string. New instances start with accepted cursors0. Private state/data records live in world_roster; ENV remains the only live world/cursor authority.

## Owner receipts and episode entry

`WorldReceiptIssuer(owner=actual_owner).issue(kind=..., payload=...)` returns sealed immutable WorldOwnerReceipt with owned payload access. Only actually issued instances validate; dataclasses.replace copies and duck-typed objects refuse. Registries are weak and do not retain every old event payload. This is cooperative in-process custody, not protection against arbitrary Python introspection.

`env.bind_boundary_authority(owner=t26_owner, role_owners=...)` requires exactly population, curiosity, curriculum, exploration, network, optimizer, scheduler, replay, selection. The mapping is copied/frozen; role objects may explicitly coincide. Rebinding must preserve owner identities. Returned WorldBoundaryAuthority is bound to that ENV.

Fresh entry:

1. `authority.bootstrap(first_batch_episode=integer)` then `env.install_boundary_release(release)` creates unconsumed bootstrap permission. The batch number never supplies world sequence.
2. `env.prepare_episode(batch_episode=..., release=...)` returns a pure immutable WorldEpisodeReservation; `validate_episode_reservation(reservation)` is pure. POP/bank perform their own pure provisional preflight on the same identity.
3. `env.reset(reservation=...)` performs the actual reset once and returns WorldRecord with `.accepted` and owned `.observation`. `.accepted` carries lane-ordered world_ids/world_episode_seqs and batch_episode. First successful reset consumes sequence1 for every world; later reset uses each cursor+1. Equal accepted retry returns the original receipt/observation without resampling, even after rollout.
4. `env.activate_episode(accepted=..., population_receipt=..., curiosity_receipt=...)` requires sealed activation receipts with exact payload `{accepted: token}` from registered population/curiosity owners. Only then may step run. Consumers must use the identical accepted token and cannot increment independent sequence authorities.

Every reset uses a fail-closed resetting phase; unexpected failure quarantines. No simulator rollback is claimed. `abandon_episode(accepted=..., reason="empty_participation"|"runtime_failure")` quarantines an accepted attempt. Empty abandonment requires actual zero ENV participation and sealed empty_episode evidence from both activated owners via prepare_empty_episode_evidence(accepted=...). No fake outcome, closure, ledger or INITIAL save follows. Recovery reconstructs from a validated boundary or an explicitly fresh run.

## Completion preflight, freeze and release

Bank owns the real prepared/committed disposition work; ENV consumes its evidence. Both bank receipt kinds use exact fields accepted, boundary_key, completion_content, participated_world_ids, dispositions. Dispositions cover every accepted world in lane order as `(world_id,"completed"|"retired_nonparticipating")`; actual ENV participated worlds must match. There must be at least one participant. No empty lane receives a manufactured completion.

1. `env.prepare_episode_close(accepted=..., boundary_key=..., completion_content=..., participated_world_ids=..., dispositions=prepared_bank_receipt)` requires kind prepared_dispositions from registered curiosity owner. It checks the full content and pins rollout revision without freezing or committing.
2. After **all** sinks prepare successfully, retain the complete prepared boundary and call `env.freeze_episode_close(prepared)`. It checks the revision and enters boundary-pending. Every step advances the revision before mutation, so intervening rollout invalidates old preparation. Frozen state blocks step/reset/save.
3. Commit each actual prepared sink/bank idempotently. `env.close_episode(prepared, dispositions=committed_bank_receipt)` requires kind dispositions, same registered owner and exact prepared payload. It records closure without advancing episode cursors. Equal freeze and close retries remain no-ops after installation; freeze retry does not downgrade closed/released phase.
4. `authority.completed(closure=..., effects=...)` requires sealed boundary_effects from bound T26 owner. Fields are batch_episode, accepted_identity, completion_content, retirement_receipt and five effect children. retirement_receipt is the committed bank receipt. Child fields are exactly accepted, boundary_key, completion_content. Expected issuers: curriculum_receipt->curriculum; exploration_receipt/epsilon_install_receipt->exploration; population_commit_receipt->population; selection_sync_receipt->selection. All correlation/content must agree.
5. `env.install_boundary_release(release)` permits next batch/reset and completed serialization independently of saving. Close alone cannot authorize either. Next batch is current+1; next world sequences derive only from ENV cursors.

Real sink preparation/commit/native validation remains each actual owner's obligation. Generic issuer evidence does not implement those sinks or authenticate absent historical payloads.

## INITIAL, COMPLETED and fresh restore

`env.checkpoint_world_state(kind=..., release=..., retained_binding_batches=tuple, initial=...)` requires all explicit arguments. Current exact schema is world-lifecycle-v3 with keys:

schema, kind, next_batch_episode, world_roster, manifest_digest, roster_semantic_identity, training_seed, execution_identity, saved_lane_binding, destination_lane_binding, accepted_episode_seqs, last_closed_episode, completed_boundary_key, accepted_bindings.

INITIAL is a genuine supported bootstrap snapshot: zero cursors, empty accepted_bindings, null saved binding/closure/completed key, actual destination binding/seed/config/roster and unconsumed next-batch permission. `authority.prepare_initial_snapshot(release=..., owners=...)` requires a sealed initial_owners receipt from bound T26. Its identity fields are semantic_execution_identity/bootstrap_first_batch/world_binding, plus eight initial owner children (all roles except curiosity). Each child kind initial_owner comes from that registered role and contains exactly role/state/semantic_execution_identity/bootstrap_first_batch/world_binding. Actual T25/T26 must prepare/validate genuine initialized NN/provider/replay/etc. states and absence of accepted effects before certifying these receipts. ENV does not reinterpret model internals. Repeated INITIAL saves are pure and do not consume bootstrap. Active, closed-pending, frozen or quarantined state cannot masquerade as INITIAL.

COMPLETED requires installed completed release, null initial argument and exact retained binding references including latest closed batch. Snapshotting never issues the release or repeats completion/decay.

Restore API:

```python
prepared = env.prepare_world_restore(
    kind=..., state=..., world_roster=..., destination_world_ids=...,
    semantic_execution_identity=...,
)
release = authority.restored(restore=prepared, boundary=joint_restore_receipt)
env.install_world_restore(prepared=prepared, release=release)
```

Destination must be fresh authority-bound with no installed release/live history. Joint receipt kind restored_boundary is T26-issued, with exact payload kind/state/prepared matching the preparation. All nested parent validation must precede this attestation/installation. INITIAL installs fresh bootstrap capabilities; first real reset accepts sequence1. COMPLETED restores cursors unchanged and allows next fresh episode. Neither branch runs reset/completion/epsilon effects during load; unexpected installation failure quarantines. No exact stochastic or mid-episode continuation is promised.

## Retained binding provenance and integration limits

accepted_bindings contains sorted exact records `{batch_episode, world_ids, world_episode_seqs}`. Each is the original accepted lane binding for that batch. Latest closure must match its own record/saved binding/cursors; native duplicated integers are independently type-checked, so bool/float aliases refuse. Current full-roster histories have equal accepted cursors and validated sequence progression. Requested fresh destination permutation does not rewrite older bindings/events/fingerprints.

T25 must derive the exact retained-reference union from actual prepared owner snapshots; ENV requires requested records to exist but cannot infer missing external references. Each retained historical event validates against its own batch binding, not the latest order. Fingerprint-only records do not permit reconstructing/authenticating absent payloads. Actual POP/PW05 owner validators retain those evidence limits explicitly.

Current compiled/classmethod/factory constructor transport is source-reviewed and independently tested. Seven remaining mypy errors are in oracle constructor/reset and POP reset callers; they must consume real reservations/reset observations/activation. No compatibility fallback is authorized, and global mypy remains failing. VFS and the actual runtime/native owner integrations below remain required.

Actual runner/T23 owns explicit run declaration and immutable run-world-roster.json custody; it is not implemented by the declaration hash. PW05 owns genuine accepted/settled/completed/retired cursors, private learned/RNG state and bank preflight/commit. T18d/T26 own actual effect receipts, epsilon/selection and pending-boundary reentry. T24/T25 own outer/native parent schemas, initialized NN/provider restore and atomic expected-refusal preparation. The54 tests exercise real ENV construction/reset/steps and producer gates using explicitly local sink doubles; they do not qualify those actual consumers.

Existing VFS still independently increments its scalar reset counter and uses row-based draw keys. Its direct accepted-world identity consumer remains required. Ambient spawn/layout RNG independence is also unqualified; prior learner/reset interference was an unrun hypothesis. None of private-state, simulator-order/spectator, actual learning, full-family/native/E2E or final BAC acceptance follows from the bounded producer results.

## Historical producer postflight (R3)
All R3 sessions are closed. Exact R3tree05b01ad1d548ad76bda8d0ef9a6ef4b685acb29a passes54owned/9covering and239joint; same Sol independent27PASS0warnings11.5209wall with custodyPASS. These selections overlap and are not summed. CompilerCLI alsoPASS190.4529wall; Ruff/Black/defaults601/expressionPASS. Globalmypy remainsFAIL13actualcallererrors4files, noowned/helpererrors. Root postflight verifies183source/573config/13artifact/index/registry/custody; boundedsourcehandoffonly, no integratedrelease. This updates the earlier at-writing pending-runtime statement without claiming missingrealconsumer/finalgates.

## Current constructor source update
Current ENV2343 SHA256 f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784 differs from the historical R3 source only in classmethod forwarding. Lifecycle/data schemas remain world-lifecycle-v3 here. The separately reviewed planned v4 VFS child is design intent until its consumer is implemented and tested. Current four-file constructor context totals4305;193joint/independent88 and all five non-mypy guards pass, while seven reset-caller errors and final integration remain open.
