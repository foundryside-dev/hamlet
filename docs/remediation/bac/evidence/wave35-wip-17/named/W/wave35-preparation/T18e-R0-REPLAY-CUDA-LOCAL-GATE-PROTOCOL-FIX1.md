# CUDA local gate protocol — binding fix round 1/5

2026-11-13. Prose-only narrow delta to `T18e-R0-REPLAY-CUDA-LOCAL-GATE-PROTOCOL.md`, immutable SHA256 `9990b731aec576d32d527d24f9cc9cfd18bd29fb4b7207dde4e9db3a0a77033f`. Read the complete independent finding at `P/T18e-R0-REPLAY-CUDA-LOCAL-GATE-INDEPENDENT-REVIEW.md`, verified SHA256 `68520bd49151ebec193f576d1ea1fd1bccc9b8b8426c3f4d837692d948a186b7`. No source reread/new body, implementation edit, runtime/import, Git/index action, checkout/copy or delegation. All execution remains UNRUN.

## Required core-enforced owner/route binding

Keep the exact public signature:

`AmbientRNGDomain.local_cuda_access(*, participant: RNGParticipant, contract: LocalCUDAContract) -> AbstractContextManager[LocalCUDAGate]`

Each core-issued contract identity maps to an immutable core-owned record containing **one exact authorized owner class identity and one exact producer route identity**, in addition to the previously specified input/effect, healthy-use and READY post-poison qualification. A source route identifier is internal policy metadata, not a public caller parameter. Separate concrete classes/routes receive separate contract identities; a caller cannot choose or amend the record.

At gate entry, while holding the sole actual domain lock and before `resolve_cuda`, owner-lock work or completion entry:

1. Authenticate the exact contract object in the core-issued manifest and authenticate the participant against the actual membership registry.
2. Resolve and strongly pin that member's live lifetime owner.
3. Fetch the manifest record for this exact contract and require `type(owner) is record.owner_type`. Identity comparison is required. Do not substitute class-name/module-name equality, duck typing, `isinstance` accepting arbitrary subclasses, matching caller-supplied entrypoint strings or merely two independently valid capabilities.
4. Bind the resulting gate to that same participant, pinned owner and exact contract/route record for its whole scope. Then apply the contract's healthy/post-poison/READY checks. All later gate methods authenticate this unchanged binding along with scope/thread/PID. Any mismatch refuses before yielding a gate or touching CUDA.

The manifest thereby authorizes this concrete membership owner to use this exact classified route. A genuine participant owned by a BANK, unrelated producer, another replay family or unlisted subclass cannot use an exported replay contract even though both participant and constant are independently genuine. Different instances of the same explicitly authorized concrete producer class may use its contract through their own authentic participant; authority and completion remain bound to the instance pinned for that invocation.

The source-qualified producer wrapper remains responsible for actually executing the recorded route with its admitted ordinary inputs and truthful device inventory. This cooperative obligation does not weaken the core's enforced class/route association and does not require stack inspection or arbitrary-code purity detection. A contract constant for one allowed route is not a general grant to run another route on that class. Source review verifies dispatch; core verifies the concrete owner identity belongs to the contract's authorized producer class. Existing RNG `entrypoints` do not automatically confer this separate local authority.

## Where identities are issued and later enabled

The existing core domain module owns issuance and the immutable manifest. Its source-controlled initialization creates opaque contract identities only for concrete records present in that reviewed production manifest and exports them as specifically named constants in its public API capsule. There is **no public issuer, registration/update method, caller predicate, caller-supplied owner class, purity flag, evidence string or route string** that can create or broaden a record.

A later bounded replay/supplier integration packet enables a production route by a reviewed source change to this core-owned manifest and its corresponding producer dispatch. That change names the actual concrete producer class, exact local entrypoint/path, admitted input class and qualification states, and publishes the precise constant name/API fact. The core resolves the canonical class from its fixed source-owned dependency, rather than trusting an owner object's claimed module/class name. To avoid the existing replay-imports-core cycle, a fixed source-owned lazy resolver may resolve that class only after the producer module has initialized; it must resolve to the canonical class object and cache that identity in the immutable record before admitting the route. Resolver inputs cannot come from the caller. If canonical resolution is unavailable or fails, refuse; do not fall back to strings, subclasses or generic contracts. Class resolution is not CUDA initialization or qualification.

The current core-only packet may retain an empty production manifest. Its internal CPU-test fixture may install a finite test-only record tied to one exact fixture class and route in controlled test setup; no test contract is exported or made available through a production issuer. This fixture demonstrates authentic relation checking without pretending to qualify a real GPU leaf. Later production activation still requires the already specified source/supplier/qualification gates. In particular, no healthy direct GPU route may be migrated to an empty/disabled manifest and declared complete. Any previously supported concrete subclass route discovered during integration must receive its own justified record before that migration is accepted; silently excluding it is not authorized by this exact-class design.

## Minimal additional causal controls

Using the existing bounded core/test packet and real registered weak owners:

- A genuine contract with the matching exact owner class admits its qualified fixture route; the same genuine contract with a genuine participant owned by an unrelated class or another producer family refuses before gate yield, CUDA query, owner work or completion.
- An unlisted subclass, and an unrelated class spoofing the authorized class/module name, refuse. Another instance of the exact authorized class succeeds only with its own authentic membership and pinned lifetime owner.
- Fabricated contract, unknown participant, unavailable canonical class resolution and expired gate refuse. No caller-supplied class/route/predicate/boolean API can enable a record. A test-only fixture contract is absent from production exports/manifest.
- Once yielded, the gate retains its exact participant/owner/route record and owner pin through completion and quarantine; later methods cannot substitute a different participant or contract.

All previously accepted completion signatures, under-owner synchronization, error identity/aggregation, quarantine, READY/poison, CPU/disposable-scratch boundaries and currentness remain unchanged. No source/hardware purity is inferred from this relation check. This single binding clarification requires no new owner decision, scope waiver or capability-removal approval. Return to the same reviewer for scoped verification, then hand off the approved public API to the waiting core writer.
