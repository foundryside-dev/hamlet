# Current direct world-identity VFS contract

This is the implemented, source-verified direct VFS identity consumer, not a whole-simulator or integrated BAC release. Root reports R2 covering4 PASS in10.5107s wall and full40 PASS /4 CUDA SKIP /0 warnings in17.5133s wall. Same Sol actual-source specification and quality review APPROVE; independent40 PASS /4 CUDA SKIP in10.1766s wall. Root/reviewer custody PASS. These overlapping selections are not summed. Root reports four non-CLI static guards PASS; global mypy still has seven existing oracle/POP caller errors. R2 compiler CLI subsequently PASS in232.18226885795593s wall. These are attributed root/reviewer results, not executions by this contract author.

Root's R3 candidate59afaaa2ca3164e29573569dbdf5907ca8e77a94 keeps these four files byte-identical and its src/config/scripts subtrees identical to R2. Root reports joint285 PASS /4 CUDA SKIP in134.9665s wall, covering3 PASS in31.4431s wall, and190-source/573-config/13-artifact/4-process custody PASS. Independent fixture-maintenance qualification is still pending. **R2 CLI input-equivalence reuse:** the R2 CLI PASS is reused for R3 based on root's identical src/config/scripts input receipt; it is not an R3 CLI rerun. No fresh CLI execution is claimed for R3.

## Source custody and corrected historical statements

Current exact four-file implementation/test inventory totals3551 lines, ceiling4900:

| File | Lines | SHA256 |
|---|---:|---|
| src/townlet/environment/vectorized_env.py | 2399 | 5508110716c38d89497c6d3c0443d6eba15f7bd546b9f2231dd86a41f5b6c166 |
| src/townlet/vfs/random_draws.py | 254 | 751e5766b5efd99a79ccc86c410d76534c397ed9ece59ca67cf2ae4fd83ef676 |
| src/townlet/config/world_roster.py | 312 | 1c3f4ad0f29e663a3f7976b10593e08223bba2b46420b2d4472451a78c667f33 |
| tests/test_townlet/regressions/bac/test_world_vfs_identity.py | 586 | 3a7ae1dd63d56b2f81b7a3a2d8a8b7302355747d7c61431bbcc6fb8dec4ab675 |

Source/tests/index remain frozen during qualification. Only this ignored prose was written in this handoff phase; no fifth source/helper/runtime/import/test/Git/index operation. Public constructor/identity contracts are received interfaces; actual runner/provider implementation was not reopened.

Explicit discrepancy with the current published CURRENT-WORLD-IDENTITY-CONTRACT: it still describes world-lifecycle-v3, calls v4 only design intent, and says VFS increments a scalar reset counter and keys by rows. Those statements describe the preceding constructor checkpoint and are superseded by this implemented consumer. Its earlier fourteen-field v3 key enumeration is preserved in full below, with vfs_random_context added as the fifteenth field. None of the preexisting fields was removed. In particular manifest_digest, roster_semantic_identity, destination_lane_binding, completed_boundary_key and accepted_bindings remain required, even if an abbreviated proposal/summary omits them. Source hashes in historical producer/constructor sections remain historical receipts, not current VFS-source hashes.

## Required context and callable interfaces

VR owns immutable data and draw computation; ENV remains the only live identity/cursor authority. The actual data type is a frozen keyword-only dataclass:

```python
VFSWorldContext(
    *, training_seed: int,
    world_ids: tuple[str, ...],
    world_episode_seqs: tuple[int, ...],
)
```

Seed and each sequence are exact nonnegative ints, rejecting bool/float aliases. IDs are a nonempty exact tuple of unique exact nonempty strings; sequences are an exact tuple of matching length. Exact whitespace/Unicode ID contents survive. Seed is not truncated to64 bits. Unequal per-world sequence tuples are valid for the pure projection; current ENV full-roster reachable-history validation still requires equal cursors. No first-element collapse is used in deriving draws.

```python
VFSRandomness(*, context: VFSWorldContext)
producer.instant(*, tick: int, device: torch.device) -> DrawInstant
producer.state() -> dict[str, Any]
VFSRandomness.validate_state(
    state: Mapping[str, Any], *, expected: VFSWorldContext,
) -> VFSWorldContext
reference_uniform(
    *, training_seed: int, world_id: str, world_episode_seq: int,
    tick: int, site: str, ordinal: int, element: int,
) -> float
```

VFSRandomness is frozen; it stores its context and derived per-world base-key tuple. It exposes no reset operation, scalar episode authority, arbitrary restore or old-state decoder. `validate_state` is pure, validates the complete exact child schema/types and compares the exact ordered context to expected; it returns owned immutable data. Reference tick/ordinal/element and instant tick require exact nonnegative ints.

DrawInstant stores a lane-ordered tuple of instant world keys and device; `.worlds` derives from that tuple length. Existing consumer stream signatures remain:

```python
instant.stream(site: str, shape: tuple[int, ...]) -> DrawStream
instant.stream_with_shared_prefix(
    site: str, shape: tuple[int, ...], *, shared_site: str, shared_draws: int,
) -> DrawStream
stream.uniform(name: str, like: torch.Tensor) -> torch.Tensor
stream.normal(name: str, like: torch.Tensor) -> torch.Tensor
```

The existing leading-world shape check and argument/context broadcast proof remain. Scalars draw the full context shape; shaped arguments broadcast with that context, preserving its world axis. This covers per-world global, agent and world/affordance-like contexts without changing their mechanics. Uniforms and normals return float32 on the instant device. Mixing is tensor-vectorized across worlds/elements; Python handles O(N) world-key projection, not each output element. Numeric row indices do not supply world identity. Element indices remain flattened within each world's trailing shape.

## Exact versioned domain and numerical recipe

Domain literal: `townlet.simulator.vfs.world-draw.v1`.

For each world encode `[domain, training_seed, world_id, world_episode_seq]` using stdlib JSON with ensure_ascii=True and separators=(",", ":"), UTF-8, no newline. BLAKE2b with digest_size=8, interpreted unsigned little-endian, is the base world key. Array framing and exact strings/integers are significant. Inputs exclude batch number, row, N, roster membership/order, compiled/authored hash and every other world's action/context. This simulator/VFS namespace is separate from curiosity, Q and provider RNG; it does not attest their implementations.

Let M be the existing SplitMix64 step: add0x9E3779B97F4A7C15 modulo2**64; XOR logical shift30 and multiply0xBF58476D1CE4E5B9 modulo2**64; XOR logical shift27 and multiply0x94D049BB133111EB modulo2**64; XOR logical shift31. The implementation retains signed-int64 tensor wrap and logical-shift helpers.

- instant key = M(base key XOR tick).
- label hash = unsigned little-endian BLAKE2b8 of UTF-8 site.
- site key = M(M(instant key XOR label hash) XOR call ordinal).
- element bits24 = M(site key XOR element lane) >>40.
- Uniform uses element lane=element and returns bits24/2**24.
- Normal uses element lanes2*element and2*element+1, u1=1-bits24a/2**24, u2=bits24b/2**24, then sqrt(-2*log(u1))*cos(2*pi*u2). Float64 intermediates convert to float32. u1 is in(0,1], keeping log finite.

Ordinals remain stream-local evaluation order. A shared condition prefix uses shared_site with the original prefix ordinal; following write draws use the write site with ordinal reduced by shared_draws. Thus the rule's shared condition remains shared across its writes and unrelated write tails remain independently addressed. This is deterministic 64-bit domain derivation, not collision freedom or a cryptographic security assertion.

The test file embeds four root-generated pre-implementation normative rows (28 elements): zero-sequence/zero-seed, ordinary accepted identity, large seed2**80+91, and exact whitespace/Unicode IDs including ordinal2. It compares the independent scalar oracle, public reference and actual tensor stream to literal bits24 values divided by2**24. Root established all literal oracle values before production changed; the pre-implementation public reference then failed on the required training_seed argument. Current CPU tests pass those numerical/domain checks, shape/broadcast and normal checks; four CUDA cases are skipped, so CUDA correctness/performance is unqualified here. Normal comparisons use tolerances rather than asserting bit-identical transcendental outputs across devices.

## ENV reset, projection and phase contract

Construction creates sequence-zero VFS context from ENV's explicit training seed, actual world IDs and zero accepted cursor map. Prepare/validate reservation remains pure. A new reset first validates the reservation and constructs its whole VFS context/producer before entering resetting. Inside the guarded reset it sets a transient `_world_vfs_pending` context and installs that producer before `_reset_world_state`, so instant-zero evaluation already uses the candidate IDs/sequences. The previous VFS scalar increment is removed. Accepted tokens and cursor updates still occur only after actual reset succeeds and use that identical reservation. The pending marker clears in finally; any late failure quarantines. No simulator rollback is claimed.

An equal accepted reset retry returns the original reset record/observation before context construction, producer replacement or any reset/RNG/tick/effect work. Reservation projection is not acceptance and confers no checkpoint capability. Public step still requires activation by the registered population/curiosity owners.

`env._vfs_draws()` uses ENV global_tick and device. During resetting it requires the pending context and equality with the installed producer. Otherwise it requires active-awaiting-activation, active, boundary-pending, closed-awaiting-release or released-completed, derives expected context from current exact IDs/cursors, and rejects producer disagreement. Fresh/bootstrap, restoring and quarantined phases cannot obtain draws through this method. Actual owned call sites remain global/agent VFS profile evaluation and VTC transition contexts; action execution retains its existing delegation and timing. Actions run at tick k, followed by the existing single ENV advance and later expression evaluation at k+1.

`env.vfs_random_state() -> dict[str, Any]` exports fresh owned data and checks its context against ENV. It explicitly refuses resetting, restoring and quarantined phases. It may export context in other current phases, including fresh/bootstrap/active/frozen phases; this data export alone is not authorization for a world checkpoint. `checkpoint_world_state` retains its stricter INITIAL/COMPLETED release gates.

`env.restore_vfs_random_state(state: Mapping[str, Any]) -> None` is strict expected-current-context validation/reinstallation. Only fresh-unbound, fresh-bound, bootstrap-ready and released-completed phases allow it. Active/awaiting-activation/frozen/closed-pending/resetting/restoring/quarantined phases refuse. It validates the entire payload against ENV seed, actual lane order and authoritative cursors before replacing the producer; it cannot change those values, issue a release or load a scalar legacy state.

## Exact native child and parent schemas

The VFS child has exactly five fields:

```text
schema = "vfs-world-random-v1"
domain = "townlet.simulator.vfs.world-draw.v1"
training_seed = exact nonnegative int
world_ids = list of unique exact nonempty strings, in producer lane order
world_episode_seqs = list of exact nonnegative ints paired with world_ids
```

Missing/extra fields, wrong schema/domain, malformed later entries, bool/float aliases, duplicate IDs, shape mismatch or any contradiction with expected seed/ordered IDs/sequences refuse. Only portable identity data is serialized, never an ENV capability or live producer. The old `{seed, episode}` payload is not supported.

The enclosing world state has **exactly these fifteen fields**, checked by ROSTER.validate_world_snapshot and emitted by ENV.checkpoint_world_state:

| Exact field | Current meaning |
|---|---|
| schema | "world-lifecycle-v4" |
| kind | explicit "INITIAL" or "COMPLETED" |
| next_batch_episode | exact nonnegative next released batch integer |
| world_roster | original authored world-roster-v1 declaration |
| manifest_digest | declaration manifest digest |
| roster_semantic_identity | declaration membership identity |
| training_seed | ENV's exact explicit seed |
| execution_identity | ENV semantic execution identity |
| saved_lane_binding | null for INITIAL; original latest accepted binding for COMPLETED |
| destination_lane_binding | actual snapshot producer's current lane binding |
| accepted_episode_seqs | exact world-ID-to-accepted-cursor mapping |
| last_closed_episode | null for INITIAL; exact last closure record for COMPLETED |
| completed_boundary_key | null for INITIAL; exact latest completed batch integer |
| accepted_bindings | retained sorted original accepted batch bindings |
| vfs_random_context | required current five-field VFS child above |

A binding has exactly schema/world_ids/hash with schema world-binding-v1. An accepted_bindings entry has exactly batch_episode/world_ids/world_episode_seqs. The last_closed_episode record has exactly batch_episode/world_ids/world_episode_seqs/completion_content/participated_world_ids. Completion content is owned data, not reconstructed external sink evidence.

Parent validation checks declaration/seed/execution identity, validates destination_lane_binding as the snapshot producer's full declared binding, validates every accepted cursor, then validates the full VFS child against that ordered binding and cursor-by-ID projection. **This child check occurs before INITIAL's early return.** INITIAL additionally requires zero cursors, empty accepted history and null saved binding/closure/completed key. COMPLETED additionally retains existing nonzero cursor, next-batch, last-closure, saved-binding and retained-history provenance checks. Pure unequal VFS contexts do not relax current full-roster history validation.

## Owned preparation and explicit destination remapping

Existing public world restore callable remains:

```python
prepared = env.prepare_world_restore(
    kind=..., state=..., world_roster=..., destination_world_ids=...,
    semantic_execution_identity=...,
)
release = authority.restored(restore=prepared, boundary=joint_restore_receipt)
env.install_world_restore(prepared=prepared, release=release)
```

Preparation requires a fresh-bound ENV with matching authored roster/seed/execution identity and the exact actual requested destination lane tuple. It first validates the complete saved parent/VFS context in the saved producer's order. It then explicitly derives the requested destination context by world ID from accepted_episode_seqs; it does not infer identity from numeric rows.

The prepared_restore record's exact payload fields are `state`, `destination_world_ids`, `destination_vfs_context`. State remains the validated saved parent, including its original child order. The additional destination_vfs_context is a portable five-field VFS-state dict for the new order. Receipt storage uses the existing frozen/owned codec; access returns owned list/dict data. No raw VFSWorldContext dataclass, live VFSRandomness producer or new capability is embedded. The existing joint restored_boundary receipt payload remains exactly kind/state/prepared and must match that same preparation; actual parent validators must complete their own preparation before issuing it.

Install checks preparation/release custody and validates the prepared destination child against this ENV's IDs/seed and the prepared cursor map before mutation. It constructs the producer before entering restoring, then installs it with the existing world fields. INITIAL retains sequence0 and bootstrap permission; first accepted reset consumes1. COMPLETED preserves accepted cursors and permits the next reservation to derive cursor+1. Neither install resets, advances tick/RNG or repeats completion. Unexpected installation failure quarantines. Equal install retry returns the original installed release without reinstalling.

Historical saved_lane_binding and accepted_bindings are unchanged by destination remapping. After a restore permutation, a later snapshot's destination_lane_binding and VFS child use the new producer order, while saved_lane_binding/retained accepted history can still use the old accepted order. The tested second-generation completed snapshot validates this distinction and restores again without rewriting history. No exact stochastic or mid-episode simulator continuation is promised.

## Proven scope and remaining actual consumers

CPU evidence covers actual current authored compilation, actual ENV constructor/reservation/reset/activation/step, same-ID direct VFS draws under fresh lane reversal/leading-spectator insertion, differing other-world actions, pure unequal sequence projection, reset retry/no resampling, quarantine, native contradiction refusal and INITIAL/COMPLETED producer roundtrips with local sealed owner receipts. Local owner helpers are explicitly producer-test evidence; they do not implement real bank/learner/NN/provider preparation or certify absent historical payloads.

Root identifies the actual runner format9 scalar VFS validator as still OPEN. That runner/native-parent consumer has not been migrated or qualified by this source packet; its old scalar expectations do not become valid because the direct ENV child now passes. The runner source was not opened here, so this is an attributed integration obligation, not a fresh source audit. Older world/VFS-owner fixture updates are the separately planned bounded test-maintenance packet; no fallback/dual decoder is authorized.

Ambient Torch spawn/layout independence and real learner-reset interference remain required separate qualification. Owned ENV still uses substrate.initialize_positions(..., generator=None), shared layout sampling and torch.randperm/torch.randint fallbacks. This packet preserves those supported mechanics and does not claim they are independent of lane order, N or learner RNG. It does not refactor uninspected substrates/providers, restrict world operation to lockstep to avoid per-world work, or claim whole-simulator S1.

Actual oracle/POP reset callers, T23 run declaration/manifest custody, PW05 bank/private learned/RNG state, T18d/T26 real effects and boundary receipts, T24/T25 native-parent preparation/restore, full-family/learning/restart/E2E gates and final BAC acceptance remain their existing obligations. Global mypy remains failing with seven oracle/POP errors. R2 CLI passed and is reused for R3 only on the input-equivalence basis stated above; independent fixture qualification remains pending. Bounded VFS CPU/domain/native-producer approval does not close those gates.

Root final R3 receipt: fresh Astra owner-fixture independent execution passed106 with zero skips/failures/warnings in34.679s wall; custodyPASS190source/573configs/13artifacts/exacttree59afaaa2ca3164e29573569dbdf5907ca8e77a94. All source/reviewer sessions closed. Required real runner/native-parent and broader integration obligations remain OPEN.
