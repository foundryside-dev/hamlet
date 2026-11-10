# Direct world-identity VFS consumer: finite ABI proposal

Status: readonly preparation for root's bounded ABI check; no implementation or execution result. This continues the approved BAC consumer dependency. Root remains integration owner and clears tests-only work. Current constructor R1 stays frozen. No new programme, source fanout, compatibility mode, family restriction, or whole-simulator claim is proposed.

## Custody and finite inventory

Observed whole-file SHA256 and line counts:

| File | Lines | SHA256 | Ceiling |
|---|---:|---|---:|
| src/townlet/environment/vectorized_env.py | 2343 | f2b50300ae9d51fa9d6e4b069091ddd1064ce09f3f5e24df1c5917453237c784 | 2600 |
| src/townlet/vfs/random_draws.py | 218 | e9cb4a885c70ef72282841d26c95c3a11e5208657e814faf4ea16b1821f9e490 | 700 |
| src/townlet/config/world_roster.py | 299 | e2627284a192920211429c77f5a806c0032e17071eedbd0877f95f4d7df4c461 | 400 |
| tests/test_townlet/regressions/bac/test_world_vfs_identity.py | reserved, not created | no hash | 1200 |

Exactly 3 existing source files (2860 lines) plus 1 reserved test; maximum 4/4900. Helpers needed below remain definitions inside these files. No fifth source, fixture, probe, provider or substrate read/edit is authorized. This proposal is the only write. Public CURRENT-WORLD-IDENTITY-CONTRACT and ignored wave17-preparation/CURRENT-WORLD-CONSTRUCTOR-TRANSPORT are received interfaces; their test results are attributed receipts, not runs performed here. AGENTS.md was read. No Git/index/runtime/import/test/copy/branch/worktree/deletion operation was performed.

## Current source facts and call-site handoff

ENV validates the explicit nonnegative integer training seed, exact IDs, full roster/cardinality before constructor randomness (289, 1917 onward). Its execution identity includes membership and compiled execution hash; that whole identity must not seed VFS because spectator membership would alter it.

ENV creates VFSRandomness(self._world_seed) at 780. `_reset_world_state` increments VFS's private scalar through `.reset()` at 1020, after resetting effects/history and before evaluating expressions at instant zero. Public reset validates reservation at 2086, enters resetting, calls the world reset, then constructs the accepted token and updates authoritative cursors at 2090–2103. Equal accepted reset retry returns early at 2083–2085. Therefore the candidate reservation must supply the draw context before the first reset-time expression; installing only after acceptance is too late.

`_vfs_draws` (1487–1489) currently supplies tick, numeric world count and device. Direct call sites visible in ENV: global profile at 1449; agent profile at 1477; VTC transition context at 1547. Other consumers may call the same ENV method through their received interface; no claim about unopened implementation bodies is made. `_execute_actions` delegates at 1499. Preserve DrawInstant.stream / stream_with_shared_prefix and DrawStream.uniform / normal signatures for these consumers. Clock order is unchanged: actions at k and expression evaluation after ENV's single advance to k+1 (1269–1272, 1342).

ENV's existing VFS native methods (1491–1497) export/restore unconstrained scalar seed/episode. World checkpoint/restore (2241–2343) does not cross-validate VFS state. ROSTER.validate_world_snapshot validates world-lifecycle-v3, including real INITIAL zero history versus COMPLETED last-binding/cursor correlation. Current full-roster reachable histories require equal cursors; VFS must still represent the full per-world tuple, not take its first element.

VR currently masks seed to 64 bits, owns an incrementing episode, and `_bits` XORs numeric torch.arange world rows into a common site key. Its valid broadcast/context shape rules, float32 24-bit uniforms, two-lane Box–Muller normals, stream-local call ordinals, shared transition-condition prefix and device-local vectorized mixing are retained.

## Chosen concrete ABI

Use a frozen data-only `VFSWorldContext` defined in VR (no live ENV/receipt references). Required keyword fields: `training_seed: int`, `world_ids: tuple[str, ...]`, `world_episode_seqs: tuple[int, ...]`. Construction validates exact nonnegative integers (reject bool/float), immutable nonempty unique exact string IDs, equal tuple lengths, and every sequence independently. Zero is valid for fresh INITIAL context; ENV controls whether draws can occur. Preserve exact unbounded seed rather than silently reducing it modulo 2**64. No inferred IDs, scalar episode, batch-to-sequence arithmetic, row fallback, or live capability serialization.

Replacement callable contract:

```
VFSRandomness(*, context: VFSWorldContext)
VFSRandomness.instant(*, tick: int, device: torch.device) -> DrawInstant
VFSRandomness.state() -> dict[str, Any]
VFSRandomness.validate_state(state: Mapping[str, Any], *, expected: VFSWorldContext) -> VFSWorldContext  # pure
reference_uniform(*, training_seed: int, world_id: str, world_episode_seq: int,
                  tick: int, site: str, ordinal: int, element: int) -> float
```

VFSRandomness is an immutable-context draw producer, with no `.reset()`, scalar `.episode`, mutable private cursor, or arbitrary `.restore()`. `DrawInstant` carries lane-ordered world keys and device; `worlds` derives from their length. Its stream interfaces and `.worlds` contract survive unchanged. `_bits` broadcasts the world-key tensor `[N,1]` against element lanes `[1,E]`; torch.arange remains only for within-world elements. Tensor mixing remains on the requested device with int64 wrap, float64 intermediate and float32 outputs. Host work is O(N) context derivation, never one Python call per output element. Unequal sequence tuples are valid at the pure context/kernel level and projected independently.

ENV has one small pure context builder from explicit IDs/sequences and its `_world_seed`. Constructor builds sequence-zero context from its actual lanes. `_vfs_draws` refuses fresh/pre-bootstrap, quarantine and restoring states; resetting is permitted only with the already validated candidate projection; accepted rollout uses the installed accepted projection. This does not add an activation bypass: public step retains its current gate.

Reset keeps its existing duplicate early return. For a new attempt: validate reservation; build and validate complete candidate context with no mutation; enter resetting; install the candidate VFS producer; execute existing `_reset_world_state` without scalar increment; accept the exact same IDs/sequences if successful. If any reset work fails, existing quarantine applies. A provisional projection is not an accepted token; it cannot be checkpointed/exported as accepted native context. On success the producer already represents the accepted identity; no increment or second installation is necessary. Reserving twice changes nothing; accepted retry does not touch VFS, RNG, layout, effects or tick. ENV remains the sole lifecycle authority.

## Frozen versioned derivation

Domain literal: `townlet.simulator.vfs.world-draw.v1`. This is a simulator/VFS-only namespace, not curiosity/Q/provider RNG. For each world, encode the JSON array `[domain, training_seed, world_id, world_episode_seq]` using `json.dumps(..., ensure_ascii=True, separators=(",", ":"))`, UTF-8, without newline; use BLAKE2b digest_size=8, interpreted unsigned little-endian, as the world base key. Exact string contents (including whitespace/Unicode distinctions) are preserved. This framing prevents concatenation ambiguity, preserves large integer seeds, and excludes batch number, row, N, roster membership/order, authored hash and other worlds' cursors/actions.

Let M be the existing splitmix64 operation. Instant world key = `M(base_key XOR tick)` with tick an exact nonnegative int. Existing site function is retained per world: `M(M(instant_key XOR blake2b(site_utf8, digest_size=8)_little) XOR ordinal)`. Stream ordinal is the existing nonnegative call ordinal, reset only by creating a stream at an instant. Element output bits = `M(site_key XOR element_lane) >> 40`. Uniform element_lane = flattened within-world element index. Normal lanes are `2*element` and `2*element+1`; keep u1=1-bits/2**24, u2=bits/2**24 and existing Box–Muller expression. Shared-prefix calls use shared_site and original prefix ordinal; remaining write calls use write site and ordinal minus prefix length, exactly as now.

The Python reference implements this specification independently of tensor mixing. Lock known-vector expectations for ID/seed/sequence/tick/site/ordinal in the owned test. Domain hashing is a deterministic 64-bit PRF-style namespace separation, not a promise of mathematical collision freedom or cryptographic RNG security. No compiled hash salt is needed: stable existing sites distinguish mechanics. Changing another world's action or context leaves a target's keys unchanged; changing target context changes its domain input.

## Native schema and pure preflight

Exact portable VFS schema:

```
{"schema": "vfs-world-random-v1", "domain": "townlet.simulator.vfs.world-draw.v1",
 "training_seed": <exact int>, "world_ids": [<exact IDs in saved lane order>],
 "world_episode_seqs": [<exact integers paired with those IDs>]}
```

Reject missing/extra fields, old seed/episode dictionaries, wrong version/domain, mutable aliases, malformed later IDs/sequences, duplicate IDs, bool/float integers and contradictory seed/ID-to-sequence mappings before any install. `validate_state` fully validates the supplied payload before comparing to expected context and returns an owned immutable value. Lane order is exact for a producer state; remapping occurs explicitly after validating saved context, never by guessing rows.

Proposed finite native integration decision: bump world lifecycle to `world-lifecycle-v4` and add required `vfs_random_context` to the exact world snapshot fields. ROSTER's pure validator validates this child against the parent seed, `destination_lane_binding.world_ids` and each parent's accepted cursor mapped by ID. This destination binding is the actual producer's lanes at snapshot time; `saved_lane_binding` remains historical last-accepted provenance and may differ after a restore permutation. Do not rewrite retained accepted bindings to the destination order. INITIAL requires all-zero context and existing pristine bootstrap checks. COMPLETED requires context matched to accepted cursors plus existing closure provenance checks. A standalone VFS-shaped object cannot attest a completed boundary.

ROSTER may import the data/pure validator from VR; VR must not import ROSTER (avoid a cycle). Keep the validator in the three-file inventory. Root should confirm this exact schema bump in the finite ABI check; no legacy decoder is proposed.

`checkpoint_world_state` includes the validated current VFS context only after its existing boundary authorization. `prepare_world_restore` validates the entire v4 snapshot, including the last malformed VFS child, before producing prepared_restore; it also preconstructs the destination VFS context from the validated cursor map and actual destination IDs. `install_world_restore` installs that context within its existing guarded install, without reset, completion, tick advancement or RNG consumption. INITIAL thus retains seq0 until first accepted reset; COMPLETED carries prior sequences and the next reservation derives cursor+1. Equal install retries return without reinstallation. Ordinary unexpected install failure retains quarantine behavior, not rollback claims.

Keep `env.vfs_random_state() -> dict[str, Any]` as an owned export of the current context, explicitly refusing resetting/restoring/quarantined phases. Keep `env.restore_vfs_random_state(state: Mapping[str, Any]) -> None` only as strict expected-current-context validation/reinstallation: validate against ENV's current authoritative lanes and cursors before mutation; it cannot load different seed/cursors or create a release. Reject operation in resetting/restoring/quarantined or active phases. Joint lifecycle restoration must use prepare/install_world_restore; after that, a separately restored VFS owner payload must equal the already installed expected destination context. No probing or scalar compatibility adapter. Parent consumers expecting an older world schema need their planned explicit current-native update; this packet does not edit them or claim they pass.

## Finite tests-first acceptance in the reserved file

1. Actual `UniverseCompiler().compile(Path("configs/test/token_set_smoke"), primary_level="L0_test", use_cache=False)` and received current `compiled.create_environment` interface; actual ENV construction, owner binding, bootstrap/reservation/reset/activation/step. Helpers reside in this test file. Role receipts are explicitly labeled local producer-test owners, not real bank/learner owners. Authored YAML may be inspected/referenced under the brief's exemption; do not fabricate compiled/ENV substitutes. Observe reset-time draw context through an owned test spy around the existing ENV seam while calling the real implementation; assert it equals the eventually accepted token and differs from preceding cursor zero. No production test hook.
2. Fresh environments with exact target IDs under lane permutation and added spectator membership/N: compare direct VFS streams mapped by exact ID at matched tick/site/shape/sequence. Exercise actual reset/step gates, but compare the isolated VFS domain where simulator inputs may differ. Assert exact CPU equality against independent reference vectors; normal/shape/range/finiteness and all broadcast shapes including shared prefix. Run available device cases within existing test infrastructure, with unavailable CUDA clearly skipped, not qualified.
3. At fixed target input/context/tick, change another world's action through actual ENV step and compare the target domain; separately use pure contexts with unequal per-world sequences to change only another world's accepted-context projection. This tests non-collapse without forging unequal reachable ENV history. Preserve global/agent/affordance-shaped streams and the existing shared-prefix alternative. Target seed, ID, sequence, tick, site and ordinal perturbations get meaningful vector expectations, not a one-sample probabilistic inequality claim.
4. Repeated prepare is pure; accepted retry before and after a real step returns original receipt/observation, preserves tick/VFS state and Torch RNG state, and never invokes reset twice. Force a late reset failure after candidate draw observation; assert quarantine and blocked native export/retry, without claiming simulator rollback. No independent VFS reset authority remains.
5. Pure VFS validation rejects malformed later tuple/list entries, bool/float seeds/sequences, duplicates, mismatched lengths, extra fields, stale domain/version and wrong target cursor, with unchanged producer state and ambient RNG. Deep v4 restore refusal checks full destination ENV state/phase/cursors/VFS context before and after refusal; valid earlier children plus invalid last VFS child cannot partially install.
6. Genuine producer INITIAL export/restore under local initial-owner receipts: zero sequence, no accepted history, first real reset sequence1. Genuine producer COMPLETED export/restore under local prepared/committed-disposition and boundary-effect receipts, including fresh lane permutation: child-parent cross-correlation, historical binding preservation, unchanged accepted cursors, next reservation/reset cursor+1. Reject valid-looking child from different seed, world ID, or sequence even when parent itself validates. These are producer-only native tests, not parent checkpoint or real-bank proof.

Expected causal RED against frozen source: current constructor API cannot accept context; current scalar/row streams disagree under identity-preserving lane permutation and spectator insertion; reset-time context is absent; old native schema cannot carry or reject contradictory per-world VFS context. Existing actual ENV gates, ordinary shape semantics and duplicate-reset behavior may already pass and are retained regression controls. Root records collected cases and intended failures after tests-only clearance, before production edits. No runtime was run in this phase.

## Remaining qualification and bounded decisions

The concrete decisions for root's ABI check are the data-only VR context, immutable producer replacement during ENV reset, specified versioned KDF, and v4 embedded native correlation. They fit the 4/4900 ceiling; implementation must report any actual exceedance rather than add a helper or remove mechanics. No additional user design decision is needed to begin the authorized consumer.

Ambient simulator RNG remains a required distinct qualification concern, not an optional omission. Owned evidence: constructor layout randomization at ENV557; reset spawn uses substrate.initialize_positions(..., generator=None) at 975/980; continuous combined layout/spawn at 1871; finite placement fallback uses torch.randperm at 1900 and torch.randint at 1911. These can depend on ambient Torch state and N. Shared affordance layout is an existing supported mechanic and must not be silently replaced/restricted. The VFS draw domain is separable at `_vfs_draws`; no inspected evidence makes substrate/provider edits inseparable from this consumer. Whole-simulator spawn/layout/order/spectator and real learner-reset interference still need their specifically required qualification; no result is inferred, no uninspected substrate is refactored, and no lockstep-only restriction is introduced to avoid per-world projection.

Actual oracle/POP callers, T23 manifest custody, real bank/curiosity/learning/private RNG, outer/native parent restore and full-family E2E remain their existing assigned obligations. This packet supplies the missing direct VFS identity consumer only and must be described that way in subsequent evidence.
