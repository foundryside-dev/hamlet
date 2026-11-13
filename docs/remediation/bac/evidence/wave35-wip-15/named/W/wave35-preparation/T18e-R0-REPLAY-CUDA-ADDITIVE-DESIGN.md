# T18e-R0 replay CUDA: finite additive protocol for B6

2026-11-13. Design only; no implementation or runtime qualification. CPU B1/B2/B4/B5 work proceeds independently. Recommendation: add a public same-domain admission gate, idle device-enrollment expansion, and explicit per-operation completion sets; preserve dynamic unindexed replay devices. Do not enroll every available device.

## Evidence and scope

Measured before source reads: rng_custody371 + replay_contract352 + replay_buffer715 + prioritized_replay_buffer1142 + sequential_replay_buffer1884 = **4464 lines / five production bodies**. Read only those bodies (targeted replay sections/searches), plus the requested source-qualified prose capsules and official-document excerpts. No sixth test/helper body, imports, runtime, Git/index actions, source edit, branch, worktree, copy or delegation.

SHA256, in that order:

- `9d6cd6fcfe62d8e53bda1e6ce7b34a89454ccc88373b5ec4cd072fe004ad66fb`
- `eb40cf7a78d0ddec538a05649b34ddb2c5521dc1ac8f68de3319344b0fd73b7a`
- `85a30028b21a2400fbbe43f82ac7422a20320c7173535a4e3bfcb342a81e29b3`
- `6d0fd54102363bb89b27590fef3e97ccdca3de6dbdce214c0c4b1219759b2bc0`
- `b29a5be9b48c99180ef64730802f041cf4536b30b8771d2ad945ceca7569bad6`

Inputs: T18e-R0-REPLAY-STAGEB-ADDENDUM B6; REPLAY-STAGEB-FIX1-PROPOSAL; PYTORCH-CUDA-DOC-FACTS; CUDA-BOOTSTRAP-SUPPLIER-FACTS; P/T18e-R0-CUDA-ENROLLMENT-CORE-FACTS; DOMAIN-NESTED-TOKEN-API; DOMAIN-REPLAY-API (all filenames have the T18e-R0 prefix).

Current core registration is idle-only, requires initialized explicit indices, and cannot update an existing participant. Operations complete declared member devices at nested exit and their union at outer exit. Replay currently releases owner exclusion before that completion. Current constructors impose indexed/initialized CUDA even though empty storage is metadata-only. Flat and PER retain tensors allocated earlier; recurrent retains entire episodes and can therefore retain several actual device identities. Constructors' `self.device`, later `.to(self.device)`/allocation calls, retained tensor `.device`, and prepared candidate storage must not be conflated.

The supplied PyTorch 2.11 contract establishes `cuda` dynamically means `current_device()`, including after `set_device`; `cuda.init()` is explicit on-demand initialization and a no-op once initialized. It does not establish CUDA execution correctness, initialization RNG side effects, or this project's custody protocol.

## Preserved behavior

1. Empty CPU, `cuda`, and `cuda:N` constructors remain metadata-only. Register one lifetime participant with `()`; this is **empty membership, not CUDA enrollment**. Do not query any CUDA attribute, initialize, allocate, guess index zero, or replace the public device with a canonical device.
2. A direct operation that actually needs CUDA automatically initializes/resolves/enrolls under the sole domain, with no caller initialization/preflight prerequisite. Resolve unindexed selection anew for each operation. Keep public `self.device` unchanged. Use a private per-call effective device for actual allocations; it expires at call exit. Do not migrate retained storage merely because selection changed.
3. Preserve existing tensor/device errors and actual old supported routes. This proposal does not promise to repair pre-existing mixed-device tensor-operation incompatibilities. Dynamic selection must not be rejected just because storage is on another index; enrollment/completion covers both, and the original algorithm determines whether that combination is valid.
4. Healthy owner-local data work remains distinct from RNG admission, including the accepted disposable scratch-generator category and permitted local continuation after common poison. No implicit lineage is introduced for sampling/preparation/publication.

## Proposed public core additions

Names below are proposed API contracts, not existing symbols. Implement inside the current domain owner; replay never reaches `_lock`, `_members`, `_active`, `_finish`, or `_poison`.

`domain.admission(*, lineage: RNGOperation | None) -> context manager[RNGAdmission]`

- Holds the sole actual domain RLock for its whole lifetime; checks PID, poison and authentic lineage before yielding. None requires idle same-thread custody; a supplied lineage requires that exact active operation. Other threads wait. The gate itself is not an RNGOperation and grants no draw/token authority.
- A gate is opaque, issuing-thread/scope-bound, noncopyable and nonserializable. Nested gates must not launder missing/wrong lineage. Initialization/update helpers reject unrelated same-thread reentry while their transaction is in progress.
- Under an **idle** gate, `gate.resolve_cuda(device)` calls explicit `torch.cuda.init()` only when needed, validates initialized count, and returns the supplied explicit index or actual `current_device()` index. Under an authenticated active gate it may resolve an already initialized device, but cannot initialize or alter membership. There is no count-to-inventory expansion.
- `gate.enroll(participant=..., cuda_devices=...)` is idle-only, authenticates the existing lifetime participant, validates exact initialized indices, and atomically replaces its immutable member record with the union of old and requested indices. Same participant/weak owner/entrypoints remain. Increment generation exactly when the set changes; unchanged union is a true no-op. Existing tokens become stale by existing generation rules. Do not unregister/re-register or refresh tokens.
- First real initialization is an ambient lifecycle event: invalidate existing preparations by advancing currency (and the appropriate core lifecycle accounting) once, before the attempt. A no-op already-initialized resolve must not invalidate an otherwise current prepare/install pair. Do not seed, draw, capture CUDA RNG merely to resolve an index, or claim restoration to a pre-initialization CUDA state that did not exist.

Extend `domain.operation` with an optional explicit `cuda_devices` argument. Omission preserves today's full-member behavior for existing consumers. An explicit tuple must be exact/sorted/unique and a subset of enrolled membership. Use that tuple for nested completion and for accumulation into the outer operation's completion union. It cannot add membership or authorize an unavailable/uninitialized device. An empty tuple is valid only when the producer really performs no CUDA work. The replay producer, not the domain, owns truthful device inventory, as with current registration.

This distinction avoids synchronizing every historically enrolled device on every call. Membership may remember devices actually used earlier; completion follows the current operation's selected, retained, input and staged devices. A newly selected already-enrolled device may join an already-held operation through this argument without changing membership or generation. The operation still authenticates and pins the replay participant in the normal way.

One additional narrow gate is needed for existing owner-local CUDA work: `domain.local_cuda_access()` holds the same lock and checks PID, but may run while commonly poisoned. It grants **no RNGOperation, token, register/update or publication authority**. It supports initialization/resolution for local deterministic tensor work and an authenticated failure-report method. When nested in an active operation it cannot initialize CUDA; already initialized deterministic local work remains permissible. It does not call `operation` under an owner lock. This is synchronization for producer-classified ambient-free work, not a replacement admission path for samples. CPU local paths keep their existing owner-only path and access no CUDA attribute.

The gate's failure-report method records common poison without requiring a fabricated operation, using the same first-cause/grouped-failure rules. Only an authentic live gate may report. This is necessary for an initialization or CUDA-completion failure occurring before an RNGOperation can lawfully exist. It does not expose a reset or healing API.

## Replay integration and lock lifetime

The shared ReplayCustody owns the gate and device bookkeeping. Its producer-specific inventory collectors inspect metadata of known supported tensors/DTOs only; never traverse arbitrary user properties or run callbacks to discover devices.

For a direct sample/prepare/install:

1. Enter `domain.admission(lineage=None)` before acquiring the replay lock. Initialize/resolve only if the planned path needs CUDA; CPU-only empty/archive paths remain lazy.
2. Acquire the owner lock and check local health. Inspect retained storage, issuer-held staged material, and supported call input tensor devices; add the actual per-call selected device when used. Canonicalize exact CUDA indices from actual tensor metadata. Include source devices for transfers, destination devices, and temporary-device work; no all-device guess.
3. Idle-enroll the required union. Enter the real domain operation with the exact completion tuple **while still within the gate and owner lock**. This is lawful domain-before-owner exclusion because the public gate acquired the actual domain first; it is not the existing unsafe owner-first admission pattern.
4. Perform the existing operation using the per-call effective device. Currentness validation occurs after enrollment and after staging, immediately before publication. Issue prepared handles only after successful staging/currentness; retain B1/B2 ownership fixes.
5. Exit the real operation, including actual CUDA completion, while the owner lock remains held; only then release owner and gate. Body failure follows the same completion path. This closes the sample-versus-clear/store gap, including nested completion.

For an already nested call, authenticate its explicit lineage at gate entry, then acquire owner lock, resolve current selection and collect actual devices. Verify the complete required tuple is enrolled before any tensor work/draw/staging. Enter the nested real operation with that tuple and complete before releasing owner. No membership changes while active.

For local CUDA reads/mutations, enter `local_cuda_access` before owner exclusion, resolve lazily when the path actually uses the requested CUDA target, then run the existing ambient-free algorithm and complete its actual device tuple before owner release. Such calls do not issue tokens or heal poison. Existing nested local helper calls reuse the producer's active local scope/effective device; they must not reacquire domain custody from inside an independently acquired owner lock. Metadata-only leaves can retain owner-only exclusion. Include GPU inputs even for a CPU destination; an actually CPU-only operation never queries CUDA. This requires explicit method classification, not a blanket change making every read an RNG operation.

## Parent preflight: scoped, exact and coherent

Add `replay.cuda_preflight(*, anticipated_devices: tuple[torch.device, ...])` as a context manager for NEW nested-parent integrations. This method is not a prerequisite for ordinary direct replay calls. A shared helper may acquire multiple replay owners in deterministic order under one gate; do not independently hold one owner while obtaining another domain.

Preflight enters an idle domain gate, resolves the current replay selector and any explicitly anticipated targets, acquires and retains the owner lock, inventories actual retained and issuer-held storage, and idle-enrolls their exact union. The caller enters its parent operation **inside** that still-open preflight scope and passes the real parent lineage to replay. Exit the parent lease, including its completion, before releasing preflight's owner/gate scopes. No gap is allowed between preflight and parent admission. Retaining owner exclusion prevents another thread from replacing storage with an unenrolled device between those steps. Supported call-input devices that the parent will later supply must also be declared in its preflight plan.

Within that parent, a `set_device` switch to a pre-enrolled target is supported: resolve again at actual replay entry and include that concrete device in the operation tuple. Do not pin to preflight's first selected device. If an active parent first requests an unenrolled device or requires CUDA initialization, refuse before effects with a specific preflight-required error. This follows idle-only membership invariants. It is a condition on the **new explicit nested protocol**, not evidence that an old supported parent path was removed. Close the parent and preflight the intended device before retrying; never silently retry after a draw/publication.

Same-thread local mutation under the parent can introduce a declared target; retained inventory is recollected at each nested replay call. A new undeclared target cannot be added to membership under that lease. New parent integrations must declare such targets before entry. This design does not pretend to predict arbitrary future `set_device` calls. No historical supported nested path requiring unrestricted mid-lease new-device enrollment has been established here, so no user approval for an alleged removal is requested on that speculation.

## Currentness, cleanup and poison

Enrollment/initialization before a prepare legitimately invalidates older candidates; a no-op gate does not. Prepare and install with unchanged membership can compose inside one held parent using existing same-operation token rules. Switching to a newly enrolled device between released prepare and install stales the old handle; prepare again under the intended inventory. Preflight all intended indices before preparing when a parent plans a later switch. Never mint a replacement token to bless stale material.

Normal argument/device-index rejection before initialization/work leaves live replay unchanged and need not poison. Initialization failure after an attempt begins must not be guessed clean: retain the error, invalidate preparations and poison unless the supplier can establish a specific clean no-effect failure class. Successful first initialization establishes new CUDA runtime state; it is not a sampling draw and must not reset any already initialized RNG state. Qualify Python/NumPy/CPU Torch state preservation and existing-device CUDA state preservation explicitly. If initialization cannot meet that contract on supported Torch, return that concrete supplier result for owner decision; do not silently reset or broaden devices.

Staging/body exceptions with successful completion retain existing clean-failure semantics; uncertain publication quarantines the owner. CUDA completion failure while owner exclusion is held poisons the common domain, quarantines the affected replay owner, and retains both body and completion exceptions. Do not return a successful batch or prepared handle after completion failure. Local CUDA completion failure uses the authenticated local gate's report mechanism; healthy CPU-only local data work on other owners remains permitted after common poison. No gate may clear common poison or owner quarantine.

## Finite implementation slices

A. Core owner: rng_custody plus a new small focused regression body and supplied replay API capsule. Implement/test gate authentication, idle union enrollment, initialization accounting, local-gate failure reporting and optional operation completion subsets. Preserve existing consumers' default behavior. Do not read all replay implementations in this slice.

B. Shared replay + flat/PER: replay_contract, replay_buffer, prioritized_replay_buffer and one focused test body. Add lazy constructor, precise route/device classification, effective-device scopes, gate-before-owner ordering, completion under owner, preflight and currentness integration. Carry forward separately fixed B1/B2/B4/B5; do not overwrite concurrent fixes.

C. Recurrent: replay_contract, sequential_replay_buffer and one focused test body. Inventory every retained episode and issuer-held candidate; preserve current-device allocation and retained-source semantics; apply identical nested/direct completion ordering.

D. Separate bounded integration/review contexts for parent-call migration and CUDA controls. Measure current whole-body counts before each read and reserve growth below five bodies/5000 lines; split further if growth requires it. No context acquires hidden test/helper implementations through extraction. Publish source-qualified API capsules between slices. One source-writer baton at a time.

## Finite causal tests and qualification

CPU/protocol controls (small focused groups; test seams are supplementary, never GPU qualification):

- All three empty constructors with `cpu`, `cuda`, `cuda:N` perform zero CUDA attribute access; invalid explicit index fails only at actual CUDA use, not empty construction. CPU-only methods, registration and completion also remain CUDA-query-free.
- Real domain gates reject foreign/expired/cross-thread lineage, active enrollment, fabricated/escaped gate capabilities and same-thread bootstrap reentry; another thread blocks at the actual gate. Same owner/participant survives expansion. A no-op enrollment preserves a genuine token; actual expansion stales it. Explicit operation tuple outside membership refuses before body.
- With finite instrumented CUDA seams, change simulated selected index between two direct calls and confirm two resolutions, correct exact membership expansion and operation subsets; no device-count-wide enrollment. Cover retained/candidate/source devices differing from selected device.
- Actual owner method plus a controlled completion barrier: competing clear/store cannot acquire owner until completion is released, including a raised body and nested call. Verify clean body failure remains usable, completion failure poisons/quarantines and aggregates errors, and partial publication remains quarantined.
- Real nested prepare/install under scoped preflight succeeds; declared later selection works; undeclared nested selection refuses before draw/tensor work. A sibling ordinary call or local mutation still stales the candidate by existing currency/revision rules. Post-poison healthy local CPU work stays permitted and does not heal poison.

Real CUDA qualification, owed on the upcoming 16-worker server (at least two visible GPUs needed for the two-device cases):

1. Fresh isolated process for each family/device form: construct while CUDA uninitialized, assert it stays uninitialized, then first real store/prepare/sample succeeds without manual initialization. Separate CPU-only process proves no CUDA initialization. Use genuine rows and sampler outputs.
2. Explicit `cuda:N` on a nondefault available index: actual storage/output identity, finite ambient RNG snapshots and actual completion. Check initialization preserves existing CPU/Python/NumPy state; already initialized resolution preserves each existing CUDA RNG state until the genuine sampler draws.
3. Unindexed switch 0 -> 1 between direct calls: use clear/repopulate for a guaranteed supported allocation path and inspect actual storage/output devices. Also retain old storage while selecting a new target and test source-compatible paths (e.g. recurrent materialization/restore) with both device identities included. Do not relabel a pre-existing mixed-device algorithm error as proof of pinning being acceptable.
4. Prepare material on one device, retain it, then exercise currentness/installation and both source/destination completion as designed. Pre-enroll a two-device parent plan; nested selection change works and same-parent prepare/install stays current. An undeclared device case refuses before effects, with unchanged serialized owner/RNG state.
5. Real asynchronous CUDA work on selected and retained-storage devices plus a competing same-owner thread: prove no clear/store/publication overlaps incomplete work using real events/streams and completion evidence. Check both nested and standalone paths. Instrument synchronization calls only to prove no unrelated available or historical-only device is completed; actual GPU events establish completion correctness.
6. Isolated fault-injection children exercise bootstrap/completion reporting and poison refusal through public gates while delegating real work before the seam raises. Do not induce a destructive GPU fault or report injected failures as native driver-failure qualification. Run typed API and existing currentness/poison regression controls at final bytes.

No CUDA test has been run in this design task. CPU passes cannot discharge B6, asynchronous owner exclusion, multi-device completion, or initialized-runtime side-effect qualification. One-GPU execution cannot discharge two-device switching/retention controls.

## Decisions and disposition

This is one concrete additive protocol, not an endorsement of all-device enrollment, permanent pinning, eager constructors, new caller initialization requirements, private-lock access or status-based admission. The core/replay owners must review and implement the new APIs and route classifications; existing source has none of this authority today. No demonstrated old supported capability must be removed by the proposed direct-call path. If supplier execution discovers unavoidable initialization side effects, or parent migration reveals a genuinely previously supported path lost by the declared-inventory protocol, surface that exact evidence for an owner decision before accepting degradation. Do not invent such a historical contract or seek speculative user permission now.

B6 remains OPEN pending implementation, independent bounded review and applicable real-CUDA qualification. No final acceptance, accounting change or release is granted.
