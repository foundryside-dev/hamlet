# B activation — exact private supplier interface

2026-11-13. Implementation concretization of adopted B plan SHA256
`a1c6b789046d60089fe4f852f7935ca6d8a48c8e808ab193ac062d315ca6f719`,
adoption `c01a6bad9e9f5a742465a7b01516c9d2cf03449e2ef83bec19d8092c7f523aae`.
These private symbols are INTENDED, not yet implemented. No production edits
or execution occurred. Core948/shared881/flat816/PER1310 remain the four
read-only bodies, total3955, with hashes unchanged from that plan. No core test,
producer test or helper body was read. Root has granted one new activation
test <=650; core growth to1250 reserves combined4907/five, hard5000/five.

## Exact symbols and representation

All new implementation stays in `townlet.exploration.rng_custody`.
Keep existing frozen `_LocalCUDARecord` fields unchanged: `owner_type:
type[object]`, `route: str`, `input_type: type[object]`, `rationale: str`,
`healthy: bool`, `post_poison: bool`. It is the concrete resolved live policy.

Add frozen `_LocalCUDADescriptor` with required fields (no defaults):

- `owner_kind: Literal["flat", "per"]`
- `route: str`
- `input_kind: Literal["tensor", "request", "mapping", "archive", "none", "integer", "indices"]`
- `rationale: str`
- `healthy: bool`
- `post_poison: bool`

`_LOCAL_CUDA_CONTRACTS: Mapping[LocalCUDAContract, _LocalCUDADescriptor]`
is a `MappingProxyType` over the exact fixed18 source-issued constants/map in
the adopted plan's “Exact18 manifest and dispatch map”. No additional identity,
alias, public issuer or production test descriptor. Flat has8, PER10;
flat load_for_mode's route is exactly `load_for_mode`; PER has no separate
load_for_mode identity. Every descriptor has healthy=True/post_poison=False.

Input tags: both push/push_recorded -> tensor; both readiness -> request;
both validate_serialized and flat load_for_mode -> mapping; both
install_historical_archive -> archive; both serialize/historical_archives ->
none; PER declare_unconstrained_action_dim -> integer; both PER priority update
routes -> indices. Resolve respectively to `torch.Tensor`, canonical
`ReplayRequest`, `collections.abc.Mapping`, canonical `HistoricalReplayArchive`,
`type(None)`, `int`, `numpy.ndarray`. This describes the primary formal input
(or absent argument), not all effects. The descriptor's rationale records the
complete adopted ordinary-data/retained-state profile. It imposes no new input
rejection and is not an arbitrary-code purity check.

Add `AmbientRNGDomain._local_cuda_policies:
dict[LocalCUDAContract, tuple[_LocalCUDADescriptor, _LocalCUDARecord]]`, initially
empty. The tuple binds exact descriptor identity to exact frozen resolved
policy identity. Keep `_Gate.policy: _LocalCUDARecord | None` unchanged.

Add these private methods, with every argument required:

- `_resolve_local_cuda_record(self, *, descriptor: _LocalCUDADescriptor) -> _LocalCUDARecord`
- `_local_cuda_policy(self, *, contract: LocalCUDAContract) -> _LocalCUDARecord`

The resolver uses fixed imports for the canonical flat/PER classes and the
input classes above, selected only by those closed source tags. No owner,
module path, class name, predicate or route is supplied by a public caller.
Unknown tags, unavailable/partial canonical classes and failed imports refuse;
no record is cached on failure. Canonical lookup is deferred until real gate
entry after module initialization; creating/exporting constants does not
import replay producers or touch CUDA. No eager cyclic import is added.

## Lock, PID, identity and lifetime

Both private methods check real PID first, then require the actual domain
RLock to be held (existing `_OwnedRLock._is_owned` contract), and reject CUDA
transaction reentry before resolution. They never acquire an owner lock.
`_local_cuda_policy` authenticates exact contract/type and descriptor type from
the immutable manifest before cache use. For a cache hit, its descriptor must
be `is` the current manifest descriptor; a mismatch refuses instead of silently
rebinding. For a miss, resolve once and publish the descriptor/record tuple
only after success under that same exclusion. Return its exact record.

`local_cuda_access` retains PID/reentry/lock/`_has_local_gate` checks and actual
participant authentication, obtains this policy, then enforces exact canonical
owner identity and existing permission checks before yielding. A second public
local gate while the first is open MUST still refuse. No test opens nested
public local gates to exercise cache population.

`_gate_record` performs NO resolution. It checks the current manifest descriptor
against the cached tuple's descriptor identity, its policy against the cached
record identity, and the existing exact participant/owner/class/thread/lock
binding. Removing/replacing a manifest descriptor or cached record invalidates
the live gate. Resolving a different route leaves its record unchanged.
Pins retain the particular owner through completion/close; descriptor/cache
entries retain only finite metadata and canonical classes, never owners,
participants, gates, invocation results or errors. No currentness revision or
CUDA READY/poison mutation comes from successful pure policy resolution.

## Separate core-test owner adaptation

Replace old fake-policy manifest entries with `_LocalCUDADescriptor` entries;
there is NO production union accepting old `_LocalCUDARecord` manifest values
and NO compatibility branch. The finite private fixture may patch the resolver
method in test setup: for its exact test descriptor identity return its known
frozen `_LocalCUDARecord` bound to the exact fixture class; reject unexpected
fixture descriptors (or explicitly delegate production descriptors to the real
resolver). Install the descriptor in a test-only immutable manifest and use a
scoped fresh `_local_cuda_policies` dictionary. This continues the accepted
private finite fixture: no fixture contract/export/issuer enters production.
Run genuine `_local_cuda_policy`, gate and completion logic after that seam.
Restore fixture bindings only after all fixture gates have exited; do not heal
poison, reset the domain, or claim this fixture qualifies canonical resolution.

The core-test owner separately exercises real production canonical resolution
and exact18 permissions. For active cache stability, hold one real local gate
and invoke private `_local_cuda_policy` for another reviewed constant under
that already-held actual domain lock, then confirm the first record/gate stays
authentic. This direct private test is confined to the separate core-test
packet; public nested-gate refusal remains a distinct negative control.

Extend plain-state/fork observations for the actual immutable manifest fields,
resolved/unresolved keys, descriptor-policy identity relations and cached class
identities. Read state without invoking either resolver, importing producers,
draining queues or touching CUDA in a guard child. Parent establishes/seals any
needed resolved state first. Both public entry and private resolver PID guards
must precede inherited lock/cache/import work. Root owns schema/verifier/source
coupling and child admission. Earlier empty-manifest receipts remain historical.

This capsule adds no test execution or acceptance. Root reports core R109
88 unique PASS including16 isolated cases and the phase pair, with final
bounded review/adoption complete. B source writes still require their own
baton; the current grant is activation-tests only. Final actual names/fields,
hashes and behavior must be verified against the implemented core before the
separate core-test packet claims qualification.
